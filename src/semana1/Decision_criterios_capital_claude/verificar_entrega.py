"""Verifica la entrega de Decision_criterios_capital_claude sin recalcular nada y sin pandas.

Comprueba: manifiesto de la corrida vigente (hashes), que el script de la carpeta es el copiado en la corrida, que los
19 controles pasaron sin cambios de datos ni de índices, que los once originales conservan el hash citado, que las
listas decididas no están aplicadas (270 autorizadas por historia y 149 bajo PRM01-R), que DECISION_ACTUARIAL.md cita
la corrida vigente y sus enlaces locales existen, y que las cifras de cifras_decision.json coinciden con evidencia.json.
Informa, sin fallar, si los índices de Limpieza cambiaron desde la decisión (ocurrirá cuando se aplique una capa).
Escribe verification.json. Uso: python verificar_entrega.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "RUTAS_PROYECTO.json").is_file():
            return candidate
    raise FileNotFoundError("No se encontró RUTAS_PROYECTO.json hacia arriba.")


ROOT = find_root(HERE)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def resolve(node, path: str):
    for segment in path.split("/"):
        match = re.match(r"^([^\[]+)(?:\[(.*)\])?$", segment)
        key, filters = match.group(1), match.group(2)
        node = node[key]
        if filters:
            conditions = dict(item.split("=", 1) for item in filters.split(";"))
            found = [row for row in node if all(str(row.get(k)) == v for k, v in conditions.items())]
            if len(found) != 1:
                raise KeyError(f"{path}: {len(found)} coincidencias para {conditions}")
            node = found[0]
    return node


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "checks": [], "passed": True, "notes": []}

    def check(name, ok, detail=None):
        report["checks"].append({"name": name, "passed": bool(ok), "detail": detail})
        if not ok:
            report["passed"] = False

    current = json.loads((HERE / "current_run.json").read_text(encoding="utf-8"))
    run = ROOT / current["workspace_relative_run"]
    check("evidencia existe", (run / "evidencia.json").is_file(), str(run.relative_to(ROOT)).replace("\\", "/"))
    evidence = json.loads((run / "evidencia.json").read_text(encoding="utf-8"))
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    bad = [name for name, h in manifest.items() if not (run / name).is_file() or digest(run / name) != h]
    check("manifiesto de la corrida", not bad, bad[:10])
    check("el script de la carpeta es el copiado en la corrida", digest(HERE / "consolidar_decision.py") == manifest.get("consolidar_decision.py"))
    check("todos los controles de la corrida pasaron", evidence["checks_summary"]["all_passed"] and evidence["checks_summary"]["checks_total"] == 19,
          {"passed": evidence["checks_summary"]["checks_passed"], "total": evidence["checks_summary"]["checks_total"]})
    scope = evidence["scope"]
    check("decisión sin cambios de datos, índices ni entrenamiento", scope["decision_only"] is True and scope["data_modified"] is False and scope["indices_modified"] is False and scope["models_trained"] is False)
    raw = ROOT / "Hackaton/Semana 1/Datos"
    orig_bad = [k for k, h in evidence["provenance"]["originals_sha256"].items() if not (raw / f"{k}.parquet").is_file() or digest(raw / f"{k}.parquet") != h]
    check("los once originales conservan el hash citado", not orig_bad, orig_bad)
    auth = read_rows(run / "tables/autorizadas.csv")
    prm = read_rows(run / "tables/prm01_F0.csv")
    check("las 270 autorizadas por historia no están aplicadas", len(auth) == 270 and all(r["capital_change_applied"] == "False" and r["correction_authorized_by_participant"] == "False" for r in auth), len(auth))
    check("las 149 de PRM01-R no están aplicadas", len(prm) == 149 and all(r["capital_change_applied"] == "False" and r["correction_authorized_by_participant"] == "False" for r in prm), len(prm))
    crit = {}
    for r in auth:
        crit[r["criterio"]] = crit.get(r["criterio"], 0) + 1
    check("criterios y filas de la lista autorizada", crit == {"NUL01-R": 152, "END02-R": 19, "TW01-R": 17, "MOV01-R": 47, "END01-R": 32, "CHAIN01-R": 3}, crit)
    hashes = {}
    for r in auth + prm:
        hashes.setdefault(r["criterio"], []).append(r["row_id"])
    recomputed = {k: hashlib.sha256("\n".join(sorted(v)).encode()).hexdigest() for k, v in hashes.items()}
    expected = {k: evidence["by_criterion"][k]["sha256_sorted_row_ids"] for k in evidence["by_criterion"]}
    check("los hashes por criterio de las tablas coinciden con la evidencia", recomputed == expected, {k: recomputed[k][:12] for k in sorted(recomputed)})
    doc = (HERE / "DECISION_ACTUARIAL.md").read_text(encoding="utf-8")
    check("el documento cita la corrida vigente", evidence["run_id"] in doc)
    missing = []
    for link in re.findall(r"\]\(([^)]+)\)", doc):
        if link.startswith(("http://", "https://", "mailto:")):
            continue
        if not (HERE / link.split("#")[0]).resolve().exists():
            missing.append(link)
    check("enlaces locales del documento", not missing, missing)
    figures = json.loads((HERE / "cifras_decision.json").read_text(encoding="utf-8"))["checks"]
    failures = []
    for item in figures:
        try:
            value = resolve(evidence, item["path"])
        except Exception as error:  # noqa: BLE001
            failures.append({"name": item["name"], "error": str(error)})
            continue
        expected_value, tol = item["expected"], item["tol"]
        if tol == 0 or isinstance(expected_value, (bool, str, list)):
            ok = value == expected_value
        else:
            ok = abs(float(value) - float(expected_value)) <= tol * max(abs(float(expected_value)), 1e-12)
        if not ok:
            failures.append({"name": item["name"], "path": item["path"], "expected": expected_value, "found": value})
    check(f"cifras del documento ({len(figures)})", not failures, failures)
    limp = ROOT / "Hackaton/Semana 1/Limpieza"
    inputs = evidence["provenance"]["inputs_sha256"]
    changed = [name for name in ("current_retrospective_dataset.json", "current_dataset.json") if digest(limp / name) != inputs[name]]
    report["notes"].append("los índices de Limpieza no han cambiado desde la decisión" if not changed else f"índices cambiados desde la decisión (esperable tras aplicar una capa): {changed}; la decisión se tomó sobre {evidence['provenance']['retrospective_run']}")
    report["run"] = str(run.relative_to(ROOT)).replace("\\", "/")
    report["checks_passed"] = sum(1 for c in report["checks"] if c["passed"])
    report["checks_total"] = len(report["checks"])
    report["independent_validation"] = False
    report["human_review"] = "pending"
    report["data_modified"] = False
    (HERE / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("passed", "checks_passed", "checks_total", "run", "notes")}, ensure_ascii=False))
    if not report["passed"]:
        for c in report["checks"]:
            if not c["passed"]:
                print("FALLA:", c["name"], c["detail"])
        sys.exit(1)


if __name__ == "__main__":
    main()
