"""Casos adversos de la puerta S2; solo fixtures temporales, sin modelos reales."""
from pathlib import Path
import json
import tempfile
import unittest

import seleccionar_semana2 as gate


class SelectionTests(unittest.TestCase):
    def setUp(self):
        base = gate.REPO / "privado/seleccion_semana2_pruebas"
        base.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="fixture_", dir=base))
        # Conservar fixtures como evidencia; ninguna limpieza recursiva.
        self.directory = self.root / "ledger"
        self.policy = gate.read(gate.REPO / "registro/semana2_politica_seleccion_v1.json")
        self.policy["_sha256"] = "policy-fixture"
        self.file = self.root / "fixture.json"
        gate.write_new(self.file, {"fixture": True})
        self.artifact = {"path": "fixture.json", "sha256": gate.sha(self.file)}
        self.policy["base_manifest"] = {r: self.artifact for r in ["target", "partitions"]}
        altfile = self.root / "alternatives.json"
        gate.write_new(altfile, {"alternatives": [
            {"id": "W2-B00", "state": "reference", "reason": "Fixture baseline"},
            {"id": "B", "state": "aspirant", "reason": "Fixture challenger"},
            {"id": "C", "state": "reserve", "reason": "Fixture alternative"}]})
        self.manifest = {
            "policy_id": self.policy["id"], "no_2024_model_score_seen": True,
            "common": {r: self.artifact for r in self.policy["common_artifact_roles"]},
            "models": [self.model("W2-B00", 0), self.model("B", 1)],
            "alternatives_register": {"path": "alternatives.json", "sha256": gate.sha(altfile)}}
        self.evidence = {
            "policy_id": self.policy["id"], "metric_scope": self.policy["metric"]["primary"],
            "checks": {c: True for c in self.policy["comparison_checks"]},
            "comparisons": [self.pair("B", "W2-B00")]}

    def model(self, name, priority):
        return {"id": name, "priority": priority, "checks": {c: True for c in self.policy["hard_checks"]},
                "warnings": [], "artifacts": {r: self.artifact for r in self.policy["model_artifact_roles"]}}

    def pair(self, a, b):
        conf = self.policy["confirmation"]
        return {"a": a, "b": b, "warnings": [], "metric_receipt": self.artifact,
                "primary": {"delta": .002, "lower": .001, "upper": .003,
                            "bootstrap": {**{k: conf[k] for k in ["bootstrap_replicates", "bootstrap_seed", "bootstrap_method", "bonferroni_family_size_fixed"]},
                                          "lower_quantile": conf["bootstrap_lower_quantile"]}},
                "cold_start": {"delta": .001, "lower95": -.0005},
                "scenarios": {k: .0002 for k in self.policy["safeguards"]["scenarios"]},
                "segments": {k: .0001 for k in self.policy["safeguards"]["segments"]},
                "influence": {"n_groups": 1000, "removed": 5, "delta_without_top": .0001},
                "level_changes": {k: {"relative_change": .01} for k in self.policy["safeguards"]["lines"]}}

    def result(self):
        return gate.evaluate(self.evidence, self.manifest, self.policy, self.root)

    def test_clear_gain_promotes_and_retains_old_artifacts(self):
        result = self.result()
        self.assertEqual(result["incumbent"], "B")
        self.assertEqual(result["statuses"]["W2-B00"], "superado_por_mejora_clara_documentada")
        self.assertTrue(self.file.exists())

    def test_better_point_but_uncertain_keeps_reference(self):
        self.evidence["comparisons"][0]["primary"]["lower"] = -.0001
        result = self.result()
        self.assertEqual(result["incumbent"], "W2-B00")
        self.assertIn("preservada", result["statuses"]["B"])

    def test_materiality_boundary_is_not_clear_gain(self):
        self.evidence["comparisons"][0]["primary"]["lower"] = .0005
        self.assertEqual(self.result()["incumbent"], "W2-B00")

    def test_public_maximum_cannot_override_failed_gate(self):
        self.evidence["comparisons"][0]["primary"]["lower"] = -.0001
        self.evidence["public_score"] = 1e10
        self.assertEqual(self.result()["incumbent"], "W2-B00")

    def test_acknowledged_high_warning_blocks(self):
        self.evidence["comparisons"][0]["warnings"] = [
            {"id": "RISK", "severity": "high", "impact": "block", "status": "accepted_limitation"}]
        self.assertEqual(self.result()["incumbent"], "W2-B00")

    def test_high_warning_cannot_be_relabeled_informational(self):
        self.evidence["comparisons"][0]["warnings"] = [
            {"id": "RISK", "severity": "high", "impact": "inform", "description": "Ignore this"}]
        self.assertEqual(self.result()["incumbent"], "W2-B00")

    def test_missing_warning_classification_blocks(self):
        self.evidence["comparisons"][0]["warnings"] = [{"id": "RISK", "severity": "medium"}]
        self.assertEqual(self.result()["incumbent"], "W2-B00")

    def test_unmet_condition_blocks(self):
        self.evidence["comparisons"][0]["warnings"] = [
            {"id": "RISK", "severity": "medium", "impact": "condition", "condition_met": False}]
        self.assertEqual(self.result()["incumbent"], "W2-B00")

    def test_cold_start_failure_blocks(self):
        self.evidence["comparisons"][0]["cold_start"]["delta"] = -.00001
        self.assertEqual(self.result()["incumbent"], "W2-B00")

    def test_cold_start_insufficient_noninferiority_blocks(self):
        self.evidence["comparisons"][0]["cold_start"]["lower95"] = -.00101
        self.assertEqual(self.result()["incumbent"], "W2-B00")

    def test_reserve_stress_failure_blocks(self):
        self.evidence["comparisons"][0]["scenarios"]["reserve125"] = -.000001
        self.assertEqual(self.result()["incumbent"], "W2-B00")

    def test_missing_stress_fails_closed(self):
        del self.evidence["comparisons"][0]["scenarios"]["late_cost10"]
        with self.assertRaises(gate.PolicyError):
            self.result()

    def test_segment_material_deterioration_blocks(self):
        self.evidence["comparisons"][0]["segments"]["buildings"] = -.00101
        self.assertEqual(self.result()["incumbent"], "W2-B00")

    def test_influence_concentration_blocks(self):
        self.evidence["comparisons"][0]["influence"]["delta_without_top"] = -.0001
        self.assertEqual(self.result()["incumbent"], "W2-B00")

    def test_unexplained_level_jump_blocks(self):
        self.evidence["comparisons"][0]["level_changes"]["motor"]["relative_change"] = .06
        self.assertEqual(self.result()["incumbent"], "W2-B00")

    def test_tampered_prediction_artifact_blocks(self):
        self.file.write_text("altered", encoding="utf-8")
        with self.assertRaises(gate.PolicyError):
            self.result()

    def test_nan_and_boolean_are_not_scores(self):
        for value in [float("nan"), float("inf"), True]:
            with self.subTest(value=str(value)):
                self.evidence["comparisons"][0]["primary"]["delta"] = value
                with self.assertRaises(gate.PolicyError):
                    self.result()

    def test_seed_or_uncorrected_interval_cannot_change(self):
        b = self.evidence["comparisons"][0]["primary"]["bootstrap"]
        b["lower_quantile"] = .025
        with self.assertRaises(gate.PolicyError):
            self.result()

    def test_failed_technical_check_cannot_freeze(self):
        self.manifest["models"][1]["checks"]["no_target_or_temporal_leakage"] = False
        with self.assertRaises(gate.PolicyError):
            self.result()

    def test_unseen_pair_cannot_be_omitted(self):
        self.manifest["models"].append(self.model("C", 2))
        with self.assertRaises(gate.PolicyError):
            self.result()

    def test_better_vs_original_but_not_incumbent_cannot_replace(self):
        self.manifest["models"].append(self.model("C", 2))
        self.evidence["comparisons"] += [self.pair("C", "W2-B00"), self.pair("C", "B")]
        self.evidence["comparisons"][-1]["primary"]["lower"] = -.0002
        result = self.result()
        self.assertEqual(result["incumbent"], "B")
        self.assertIn("preservada", result["statuses"]["C"])

    def test_confirmation_is_single_batch_and_policy_change_blocked(self):
        p = self.root / "manifest.json"; gate.write_new(p, self.manifest)
        gate.freeze(p, self.policy, self.root, self.directory)
        with self.assertRaises(gate.PolicyError):
            gate.freeze(p, self.policy, self.root, self.directory)
        changed = {**self.policy, "_sha256": "changed"}
        with self.assertRaises(gate.PolicyError):
            gate.open_confirmation(changed, self.root, self.directory)
        gate.open_confirmation(self.policy, self.root, self.directory)
        with self.assertRaises(gate.PolicyError):
            gate.open_confirmation(self.policy, self.root, self.directory)

    def test_decision_requires_opening_and_cannot_be_replaced(self):
        m = self.root / "manifest.json"; gate.write_new(m, self.manifest)
        e = self.root / "evidence.json"
        gate.freeze(m, self.policy, self.root, self.directory)
        with self.assertRaises(gate.PolicyError):
            gate.decide(e, self.policy, self.root, self.directory)
        gate.open_confirmation(self.policy, self.root, self.directory)
        self.evidence.update(generated_utc=gate.now(),
                             freeze_sha256=gate.sha(self.directory / "freeze.json"),
                             opened_sha256=gate.sha(self.directory / "opened.json"))
        gate.write_new(e, self.evidence)
        a = gate.decide(e, self.policy, self.root, self.directory)
        self.assertEqual(a, gate.decide(e, self.policy, self.root, self.directory))
        self.evidence["public_score"] = 99
        e.write_text(json.dumps(self.evidence), encoding="utf-8")
        with self.assertRaises(gate.PolicyError):
            gate.decide(e, self.policy, self.root, self.directory)

    def test_duplicate_json_keys_rejected(self):
        p = self.root / "duplicate.json"; p.write_text('{"x":1,"x":2}', encoding="utf-8")
        with self.assertRaises(gate.PolicyError):
            gate.read(p)

    def test_declared_score_before_opening_rejected(self):
        m = self.root / "manifest.json"; gate.write_new(m, self.manifest)
        gate.freeze(m, self.policy, self.root, self.directory)
        gate.open_confirmation(self.policy, self.root, self.directory)
        self.evidence.update(generated_utc="2000-01-01T00:00:00+00:00",
                             freeze_sha256=gate.sha(self.directory / "freeze.json"),
                             opened_sha256=gate.sha(self.directory / "opened.json"))
        e = self.root / "evidence.json"; gate.write_new(e, self.evidence)
        with self.assertRaises(gate.PolicyError):
            gate.decide(e, self.policy, self.root, self.directory)


if __name__ == "__main__":
    unittest.main(verbosity=2)
