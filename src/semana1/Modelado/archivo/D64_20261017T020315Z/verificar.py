"""Controles documentales y aritméticos D64, sin ajustar modelos."""
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import numpy as np
from sklearn import __version__ as sklearn_version
from sklearn.metrics import d2_tweedie_score, mean_tweedie_deviance

CLOSE = Path(__file__).resolve().parent
MODEL = CLOSE.parent.parent
ROOT = MODEL.parents[2]
PREP = ROOT / "Preparación"
REF = MODEL / "Referencias_publicas"
checks = {}


def check(name, condition):
    checks[name] = bool(condition)
    if not condition:
        raise AssertionError(name)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


catalog = read(MODEL / "experimentos.json")
previous = read(CLOSE / "before" / (MODEL / "experimentos.json").relative_to(ROOT))
protocol = read(MODEL / "protocolo_metodologico.json")
old_protocol = read(CLOSE / "before" / (MODEL / "protocolo_metodologico.json").relative_to(ROOT))
state = read(PREP / "ESTADO_PROYECTO.json")
old_state = read(CLOSE / "before" / (PREP / "ESTADO_PROYECTO.json").relative_to(ROOT))
check("22_candidates", len(catalog["candidates"]) == 22)
for old, new in zip(previous["candidates"], catalog["candidates"]):
    check("candidate_preserved_" + old["id"], {k: v for k, v in new.items() if k != "calculation_contract"} == old)
    check("calculation_contract_unmeasured_" + old["id"], new["calculation_contract"]["local_D2"] is None and new["calculation_contract"]["public_D2"] is None and new["calculation_contract"]["evaluation_power"] == 1.5)
check("catalog_validation_unchanged", catalog["validation"] == previous["validation"])
check("catalog_policy_unchanged", catalog["submission_policy"] == previous["submission_policy"])
check("no_trained_models", catalog["models_trained"] == previous["models_trained"] == 0)
for key in old_protocol:
    if key not in {"version", "metric"}:
        check("protocol_preserved_" + key, protocol[key] == old_protocol[key])
check("metric_previous_fields_preserved", all(protocol["metric"][k] == v for k, v in old_protocol["metric"].items()))
for key in old_state:
    if key not in {"memory_as_of", "methodological_plan"}:
        check("state_preserved_" + key, state[key] == old_state[key])
check("methodology_state_consistent", protocol["version"] == state["methodological_plan"]["version"] == "1.11")
check("methodology_plan_preserved", all(state["methodological_plan"][k] == v for k, v in old_state["methodological_plan"].items() if k != "version"))
for name in ("MEMORIA_PROYECTO.md", "DECISIONES.md"):
    old = (CLOSE / "before" / (PREP / name).relative_to(ROOT)).read_text(encoding="utf-8")
    check("history_append_only_" + name, (PREP / name).read_text(encoding="utf-8").startswith(old))
check("D64_unique", len(re.findall(r"^### D64,", (PREP / "DECISIONES.md").read_text(encoding="utf-8"), re.M)) == 1)
check("table_candidates_complete", all(f'| {c["id"]} |' in (MODEL / "CATALOGO_MODELOS.md").read_text(encoding="utf-8") for c in catalog["candidates"]))
source = read(REF / "captura.json")
check("image_hash", source["image_sha256"] == hashlib.sha256((REF / "captura.png").read_bytes()).hexdigest())
check("score_transcription", [r["score_displayed"] for r in source["rows"]] == ["0.11416", "0.10563", "0.07169", "0.07169"])
check("rank_reference_not_invented", [r["rank_displayed"] for r in source["rows"]] == [1, None, None, None])
generated = [REF / "calculos.json", REF / "TABLA_Y_CALCULOS.md"]
before = [p.read_bytes() for p in generated]
subprocess.run([sys.executable, str(REF / "calcular.py")], check=True, capture_output=True)
check("regeneration_deterministic", before == [p.read_bytes() for p in generated])
calc = read(REF / "calculos.json")
leader = calc["comparisons_vs_glm"][0]
check("score_gap_decimal", Decimal(leader["delta_D2"]) == Decimal("0.00853"))
check("relative_deviance_reduction_decimal", abs(Decimal(leader["relative_deviance_reduction_pct"]) - Decimal("0.9537439762067153")) < Decimal("1e-15"))

# Identidad contra scikit-learn sobre vectores de comprobación, sin datos del reto.
y = np.array([0., 2.5, 15., 80.])
e = np.array([.1, .25, .5, 1.])
a = np.array([.2, 5., 12.5, 60.])
b = np.array([.4, 4., 20., 50.])
w = np.array([1., 2., .5, 3.])
unit = 4 * (y / np.sqrt(a) - 2 * np.sqrt(y) + np.sqrt(a))
check("unit_deviance_formula", math.isclose(np.average(unit, weights=w), mean_tweedie_deviance(y, a, sample_weight=w, power=1.5), abs_tol=1e-12))
null = np.full(len(y), np.average(y, weights=w))
manual = 1 - np.average(unit, weights=w) / mean_tweedie_deviance(y, null, sample_weight=w, power=1.5)
check("D2_formula", math.isclose(manual, d2_tweedie_score(y, a, sample_weight=w, power=1.5), abs_tol=1e-12))
sa = d2_tweedie_score(y, a, sample_weight=w, power=1.5)
sb = d2_tweedie_score(y, b, sample_weight=w, power=1.5)
reduction = 1 - mean_tweedie_deviance(y, a, sample_weight=w, power=1.5) / mean_tweedie_deviance(y, b, sample_weight=w, power=1.5)
check("score_to_deviance_reduction_identity", math.isclose((sa - sb) / (1 - sb), reduction, abs_tol=1e-12))
for p in [1.5, 1.9]:
    # Sumas, no medias con normalizadores distintos.
    q = a / e
    loss_amount = mean_tweedie_deviance(y, a, power=p) * len(y)
    weights = e ** (2 - p)
    loss_rate = mean_tweedie_deviance(y / e, q, sample_weight=weights, power=p) * weights.sum()
    check("exposure_loss_identity_" + str(p), math.isclose(loss_amount, loss_rate, rel_tol=1e-12))

docs = [MODEL / "CATALOGO_MODELOS.md", REF / "TABLA_Y_CALCULOS.md"]
for doc in docs:
    for target in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
        if not target.startswith("https://"):
            check("link_" + doc.name + "_" + target, (doc.parent / target).exists())
report = {"checked_utc": datetime.now(timezone.utc).isoformat(), "scope": "D64 own documentary and synthetic arithmetic checks; no training, no competition data, no independent review", "sklearn_version": sklearn_version, "checks_passed": len(checks), "all_passed": all(checks.values()), "checks": checks}
(CLOSE / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
files = [MODEL / "experimentos.json", MODEL / "protocolo_metodologico.json", MODEL / "METODOLOGIA_ACTUARIAL.md", MODEL / "README.md", MODEL / "CATALOGO_MODELOS.md", PREP / "MEMORIA_PROYECTO.md", PREP / "ESTADO_PROYECTO.json", PREP / "DECISIONES.md", *REF.iterdir()]
manifest = {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
(CLOSE / "after_sha256.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"all_passed": report["all_passed"], "checks_passed": len(checks), "sklearn_version": sklearn_version, "report": str(CLOSE / "verification.json")}, ensure_ascii=False))
