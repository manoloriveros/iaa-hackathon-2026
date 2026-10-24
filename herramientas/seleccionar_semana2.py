"""Puerta S2: recalcula métricas desde predicciones congeladas; no entrena.

La política y el ejecutable se verifican contra el índice activo. Al decidir,
contrasta los recibos con el recálculo; una respuesta guardada revalida su
contexto y resultado, repitiendo las métricas. No autoriza abrir confirmación ni acredita
procedencia honesta o revisión profesional independiente.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import metric_binding

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
ACTIVE = REPO / "registro/semana2_seleccion_actual.json"


class PolicyError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    def duplicate(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise PolicyError(f"Clave JSON duplicada: {k}")
            result[k] = v
        return result
    return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                      object_pairs_hook=duplicate,
                      parse_constant=lambda x: (_ for _ in ()).throw(PolicyError(f"Número no finito: {x}")))


def write_new(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("x", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def require(ok, message):
    if not ok:
        raise PolicyError(message)


def number(value, name):
    require(type(value) in (int, float) and math.isfinite(value), f"{name}: falta número finito")
    return float(value)


def artifact(spec, root):
    require(isinstance(spec, dict), "Falta artefacto con path/sha256")
    require(isinstance(spec.get("path"), str) and spec["path"], "Falta path")
    path = (root / spec["path"]).resolve()
    require(path.is_relative_to(root.resolve()), "Artefacto fuera del workspace")
    require(path.is_file(), f"No existe artefacto: {spec['path']}")
    require(sha(path) == spec.get("sha256"), f"SHA no coincide: {spec['path']}")
    return path


def true_checks(checks, names):
    require(isinstance(checks, dict), "Faltan controles explícitos")
    for name in names:
        require(checks.get(name) is True, f"Control no aprobado: {name}")


def verify_manifest(manifest, policy, root):
    require(manifest.get("policy_id") == policy["id"], "Política de manifiesto distinta")
    require(manifest.get("no_2024_model_score_seen") is True, "No se declara congelación previa a scores2024")
    common = manifest.get("common", {})
    for role in policy["common_artifact_roles"]:
        artifact(common.get(role), root)
    for role, expected in policy["base_manifest"].items():
        require(common[role] == expected, f"Base/partición distinta para {role}")
    models = manifest.get("models", [])
    require(1 <= len(models) <= policy["confirmation"]["max_models"], "Familia debe tener referencia y hasta3aspirantes")
    ids = [m.get("id") for m in models]
    require(all(isinstance(i, str) and i for i in ids) and len(set(ids)) == len(ids), "IDs inválidos/duplicados")
    require(ids[0] == policy["reference_id"], "La referencia inicial debe ser W2-B00")
    require([m.get("priority") for m in models] == list(range(len(models))), "Prioridad debe quedar fijada como0..n")
    for model in models:
        true_checks(model.get("checks"), policy["hard_checks"])
        blockers = warning_reasons(model.get("warnings"), root)
        require(not blockers, f"Advertencias técnicas sin resolver en {model['id']}: {blockers}")
        for role in policy["model_artifact_roles"]:
            artifact(model.get("artifacts", {}).get(role), root)
    require(isinstance(manifest.get("alternatives_register"), dict), "Falta registro de todas las alternativas")
    alternatives = read(artifact(manifest["alternatives_register"], root)).get("alternatives")
    require(isinstance(alternatives, list), "Registro de alternativas sin lista")
    alternative_ids = [a.get("id") for a in alternatives]
    require(len(set(alternative_ids)) == len(alternative_ids) and set(ids) <= set(alternative_ids),
            "Alternativas duplicadas o modelos congelados ausentes del registro")
    for item in alternatives:
        require(isinstance(item.get("id"), str) and item["id"] and bool(item.get("reason")),
                "Alternativa sin ID/motivo")
        require(item.get("state") in ["reference", "aspirant", "reserve", "blocked_technical", "not_shortlisted_development"],
                "Alternativa descartada sin comparación registrada")
    try:
        metric_binding.bindings(manifest, policy, root)
    except (metric_binding.BindingError, OSError, KeyError, TypeError, ValueError) as exc:
        raise PolicyError("Vínculo de métricas no válido: " + str(exc)) from exc
    for model in models:
        artifact(model.get("artifacts", {}).get("level_predictions"), root)
    try:
        metric_binding.preflight(manifest, policy, root)
    except (metric_binding.BindingError, OSError, KeyError, TypeError, ValueError) as exc:
        raise PolicyError("Preflight de estructura no satisfecho: " + str(exc)) from exc
    return ids


def warning_reasons(warnings, root):
    require(isinstance(warnings, list), "Falta lista explícita de advertencias")
    reasons = []
    ids = set()
    for w in warnings:
        require(isinstance(w, dict) and isinstance(w.get("id"), str) and w["id"], "Advertencia sinID")
        require(w["id"] not in ids, "Advertencia duplicada")
        ids.add(w["id"])
        impact = w.get("impact")
        require(w.get("severity") in ["critical", "high", "medium", "low"], "Advertencia sin gravedad explícita")
        if w["severity"] in ["critical", "high"] and impact != "block":
            reasons.append(f"{w['id']}: gravedad alta/crítica exige bloqueo")
        if impact == "inform":
            require(bool(w.get("description")), "Advertencia informativa sin descripción")
        elif impact == "block":
            if w.get("status") != "resolved":
                reasons.append(f"{w['id']}: bloqueo no resuelto")
            else:
                artifact(w.get("evidence"), root)
        elif impact == "condition":
            if w.get("condition_met") is not True:
                reasons.append(f"{w['id']}: condición no satisfecha")
            else:
                artifact(w.get("evidence"), root)
        else:
            reasons.append(f"{w['id']}: impacto desconocido")
    return reasons


def evaluate_pair(pair, policy, root, manifest=None):
    """Use recomputed values, never the supplied side of a tolerance check."""
    try:
        computed = metric_binding.verify_receipt(pair, manifest, policy, root)
    except (metric_binding.BindingError, OSError, KeyError, TypeError, ValueError) as exc:
        raise PolicyError("Recibo sin correspondencia semántica: " + str(exc)) from exc
    pair = copy.deepcopy(pair)
    explanations = pair.get("level_changes", {})
    for name, value in computed.items():
        if name != "level_changes":
            pair[name] = value
    pair["level_changes"] = {line: {**explanations.get(line, {}), **value}
                             for line, value in computed["level_changes"].items()}
    reasons = warning_reasons(pair.get("warnings"), root)
    artifact(pair.get("metric_receipt"), root)
    p = pair.get("primary", {})
    delta = number(p.get("delta"), "primary.delta")
    lower = number(p.get("lower"), "primary.lower")
    upper = number(p.get("upper"), "primary.upper")
    require(lower <= delta <= upper, "Intervalo primario incompatible con punto")
    b = p.get("bootstrap", {})
    conf = policy["confirmation"]
    for key in ["bootstrap_replicates", "bootstrap_seed", "bootstrap_method", "bonferroni_family_size_fixed"]:
        require(b.get(key) == conf[key], f"Bootstrap distinto: {key}")
    require(abs(number(b.get("lower_quantile"), "bootstrap.lower_quantile") - conf["bootstrap_lower_quantile"]) < 1e-12,
            "Cuantil sin corrección familiar registrada")
    if lower <= policy["metric"]["delta_min"]:
        reasons.append("Mejora clara no acreditada: límite inferior<=0.0005")
    s = policy["safeguards"]
    cold = pair.get("cold_start", {})
    cold_delta = number(cold.get("delta"), "cold.delta")
    cold_lower = number(cold.get("lower95"), "cold.lower95")
    require(cold_lower <= cold_delta, "Límite inferior cold-start incompatible")
    if cold_delta < s["cold_start_nominal_delta_min"] or cold_lower < s["cold_start_lower95_min"]:
        reasons.append("Población nueva no supera salvaguarda")
    scenarios = pair.get("scenarios", {})
    for name in s["scenarios"]:
        if number(scenarios.get(name), f"scenario.{name}") < s["scenario_temporal_delta_min"]:
            reasons.append(f"Escenario adverso: {name}")
    segments = pair.get("segments", {})
    for name in s["segments"]:
        if number(segments.get(name), f"segment.{name}") < s["segment_delta_min"]:
            reasons.append(f"Deterioro material: {name}")
    influence = pair.get("influence", {})
    groups = influence.get("n_groups")
    require(type(groups) is int and groups >= 2, "Grupos de influencia insuficientes")
    removed = min(groups - 1, max(5, math.ceil(0.001 * groups)))
    require(influence.get("removed") == removed, "Supresión de influencia distinta de la fijada")
    if number(influence.get("delta_without_top"), "influence.delta_without_top") < 0:
        reasons.append("Ganancia depende de pocos grupos favorables")
    levels = pair.get("level_changes", {})
    for line in s["lines"]:
        item = levels.get(line, {})
        ratio = number(item.get("relative_change"), f"level.{line}")
        if abs(ratio) > s["unexplained_absolute_level_change_max"]:
            if item.get("explained_and_validated_in_development") is not True:
                reasons.append(f"Cambio de nivel>5% sin justificar: {line}")
            else:
                artifact(item.get("evidence"), root)
    return {"a": pair["a"], "b": pair["b"], "passes": not reasons, "reasons": reasons,
            "delta": delta, "lower": lower, "upper": upper}


def evaluate(evidence, manifest, policy, root):
    ids = verify_manifest(manifest, policy, root)
    require(evidence.get("policy_id") == policy["id"], "Política de evidencia distinta")
    require(evidence.get("metric_scope") == policy["metric"]["primary"], "Estimando distinto")
    true_checks(evidence.get("checks"), policy["comparison_checks"])
    rows = evidence.get("comparisons", [])
    expected = {(ids[i], ids[j]) for i in range(len(ids)) for j in range(i)}
    keys = [(p.get("a"), p.get("b")) for p in rows]
    require(len(set(keys)) == len(keys) and set(keys) == expected, "Faltan/sobran pares congelados o hay duplicados")
    evaluated = {k: evaluate_pair(p, policy, root, manifest) for k, p in zip(keys, rows)}
    incumbent = ids[0]
    status = {i: "alternativa_preservada" for i in ids}
    steps = []
    for candidate in ids[1:]:
        result = evaluated[candidate, incumbent]
        steps.append(result)
        if result["passes"]:
            status[incumbent] = "superado_por_mejora_clara_documentada"
            incumbent = candidate
        else:
            status[candidate] = "no_promovido_alternativa_preservada"
    status[incumbent] = "referencia_vigente"
    return {"policy_id": policy["id"], "utc": now(), "incumbent": incumbent,
            "statuses": status, "promotion_steps": steps, "all_pair_results": list(evaluated.values()),
            "claim": "Decisión condicional a recibos aportados, sin certificación independiente de scores/IC.",
            "public_score_used": False, "models_deleted": False}


@contextmanager
def lock(directory):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "selection.lock"
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise PolicyError("Selección bloqueada por otra operación; no retirar bloqueo ajeno") from exc
    try:
        os.write(fd, f"pid={os.getpid()} utc={now()}".encode())
        os.close(fd)
        yield
    finally:
        path.unlink()


def state(directory):
    events = []
    for name in ["freeze.json", "opened.json", "decision.json"]:
        if (directory / name).exists():
            events.append(name)
    require(events in ([], ["freeze.json"], ["freeze.json", "opened.json"],
                       ["freeze.json", "opened.json", "decision.json"]), "Estado parcial/incoherente")
    return events


def freeze(manifest_path, policy, root, directory):
    review = preopening_review(policy, root)
    with lock(directory):
        require(not state(directory), "La tanda ya está congelada; no se sustituye")
        manifest = read(manifest_path)
        ids = verify_manifest(manifest, policy, root)
        receipt = {"utc": now(), "policy_id": policy["id"], "policy_sha256": policy["_sha256"],
                   "manifest_sha256": sha(manifest_path), "manifest": manifest, "models": ids,
                   "preopening_review": review}
        write_new(directory / "freeze.json", receipt)
        return receipt


def open_confirmation(policy, root, directory):
    review = preopening_review(policy, root)
    with lock(directory):
        require(state(directory) == ["freeze.json"], "La confirmación solo se abre una vez")
        frozen = read(directory / "freeze.json")
        require(frozen["policy_sha256"] == policy["_sha256"], "Política alterada tras congelar")
        require(frozen.get("preopening_review") == review, "Revisión separada distinta de la congelación")
        verify_manifest(frozen["manifest"], policy, root)
        receipt = {"utc": now(), "freeze_sha256": sha(directory / "freeze.json"),
                   "policy_sha256": policy["_sha256"], "confirmation_batch_consumed": True,
                   "preopening_review": review}
        write_new(directory / "opened.json", receipt)
        return receipt


def decide(evidence_path, policy, root, directory):
    review = preopening_review(policy, root)
    with lock(directory):
        current = state(directory)
        require("opened.json" in current, "No se abrió la tanda antes de consultar resultados")
        opened = read(directory / "opened.json")
        freeze_sha256 = sha(directory / "freeze.json")
        opened_sha256 = sha(directory / "opened.json")
        evidence_sha256 = sha(evidence_path)
        require(opened["freeze_sha256"] == freeze_sha256, "Congelación alterada")
        require(opened["policy_sha256"] == policy["_sha256"], "Política alterada después de abrir")
        frozen = read(directory / "freeze.json")
        require(frozen.get("policy_sha256") == policy["_sha256"]
                and frozen.get("policy_id") == policy["id"], "Política congelada distinta")
        require(opened.get("preopening_review") == frozen.get("preopening_review") == review,
                "Revisión separada cambió entre transiciones")
        # A cached result is a current attestation only while its frozen context
        # AND substantive result remain valid. Repeated decide intentionally
        # recomputes metrics from frozen predictions; it never refits models.
        verify_manifest(frozen["manifest"], policy, root)
        old = None
        if "decision.json" in current:
            old = read(directory / "decision.json")
            expected = {"policy_id": policy["id"], "evidence_sha256": evidence_sha256,
                        "freeze_sha256": freeze_sha256, "opened_sha256": opened_sha256,
                        "policy_sha256": policy["_sha256"], "preopening_review": review}
            require(all(old.get(k) == v for k, v in expected.items()),
                    "Decisión histórica no coincide con contexto vigente; no se reemplaza")
        evidence = read(evidence_path)
        require(evidence.get("freeze_sha256") == opened["freeze_sha256"], "Evidencia no vinculada a congelación")
        require(evidence.get("opened_sha256") == sha(directory / "opened.json"), "Evidencia no vinculada a apertura")
        try:
            generated = datetime.fromisoformat(evidence["generated_utc"])
            opened_at = datetime.fromisoformat(opened["utc"])
            require(generated.tzinfo is not None and generated >= opened_at, "Scores anteriores a apertura registrada")
        except (ValueError, KeyError, TypeError) as exc:
            raise PolicyError("Fecha de evidencia inválida o ausente") from exc
        result = evaluate(evidence, frozen["manifest"], policy, root)
        result.update(evidence_sha256=sha(evidence_path), freeze_sha256=opened["freeze_sha256"],
                      opened_sha256=sha(directory / "opened.json"), policy_sha256=policy["_sha256"],
                      preopening_review=review)
        if old is not None:
            # Compare exact typed JSON, not tolerant numeric equality; an altered
            # cached value must not become a valid current result by rounding.
            previous = {k: v for k, v in old.items() if k != "utc"}
            recomputed = {k: v for k, v in result.items() if k != "utc"}
            require(metric_binding.canonical_sha(previous) == metric_binding.canonical_sha(recomputed),
                    "Resultado histórico difiere del recálculo vigente; no se reemplaza")
            return old
        write_new(directory / "evidence.json", evidence)
        write_new(directory / "decision.json", result)
        return result


def active():
    index = read(ACTIVE)
    policy_path = artifact(index["policy"], ROOT)
    require(sha(Path(__file__)) == index["gate_sha256"], "Ejecutable distinto del registrado")
    policy = read(policy_path)
    policy["_sha256"] = sha(policy_path)
    policy["_metric_binding_release"] = index.get("metric_binding_release")
    directory = (ROOT / index["ledger_workspace_relative"]).resolve()
    require(directory.is_relative_to((REPO / "privado").resolve()), "Ledger fuera del área privada")
    return policy, directory


def preopening_review(policy, root):
    try:
        review = metric_binding.verify_release_review(policy, root, Path(__file__))
        return {"review": review, "bindings": copy.deepcopy(policy["_metric_binding_release"]["bindings"])}
    except (metric_binding.BindingError, OSError, KeyError, TypeError, ValueError) as exc:
        raise PolicyError("Revisión separada previa a apertura no satisfecha: " + str(exc)) from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("estado")
    p = subs.add_parser("congelar"); p.add_argument("--manifest", type=Path, required=True)
    subs.add_parser("abrir")
    p = subs.add_parser("decidir"); p.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    try:
        policy, directory = active()
        if args.command == "estado":
            result = {"policy_id": policy["id"], "events": state(directory),
                      "status": "criterios_fijados_sin_comparar" if not state(directory) else "tanda_en_curso_o_cerrada",
                      "delta_min": policy["metric"]["delta_min"]}
        elif args.command == "congelar":
            result = freeze(args.manifest, policy, ROOT, directory)
        elif args.command == "abrir":
            result = open_confirmation(policy, ROOT, directory)
        else:
            result = decide(args.evidence, policy, ROOT, directory)
        print(json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False))
        if args.command == "decidir" and not any(s["passes"] for s in result["promotion_steps"]):
            return 3
        return 0
    except (PolicyError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOQUEADO", "reason": str(exc), "incumbent_replaced": False}, ensure_ascii=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
