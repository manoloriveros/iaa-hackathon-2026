"""Verifica la entrega de Validacion_ajustes_claude sin recalcular nada y sin pandas.

Comprueba: manifiesto de la corrida vigente (hashes), que el dashboard de la raíz es el de esa corrida,
que las 41 comprobaciones pasaron, que las cifras de INFORME.md (cifras_informe.json) coinciden con
evidencia.json, que los originales citados conservan su hash, y que los enlaces locales del informe existen.
Escribe verification.json. Uso: python verificar_entrega.py
"""
from __future__ import annotations

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


def main() -> None:
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "checks": [], "passed": True}

    def check(name, ok, detail=None):
        report["checks"].append({"name": name, "passed": bool(ok), "detail": detail})
        if not ok:
            report["passed"] = False

    current = json.loads((HERE / "current_run.json").read_text(encoding="utf-8"))
    run = ROOT / current["workspace_relative_run"]
    evidence = json.loads((run / "evidencia.json").read_text(encoding="utf-8"))
    check("evidencia existe", (run / "evidencia.json").is_file(), str(run.relative_to(ROOT)))
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    bad = [name for name, h in manifest.items() if not (run / name).is_file() or digest(run / name) != h]
    check("manifiesto de la corrida", not bad, bad[:10])
    check("dashboard de la raíz es el de la corrida", (HERE / "dashboard.html").is_file() and digest(HERE / "dashboard.html") == manifest.get("dashboard.html"))
    html = (HERE / "dashboard.html").read_text(encoding="utf-8")
    check("dashboard incrusta la corrida", evidence["run_id"] in html and "/*__DATA__*/" not in html)
    check("todas las comprobaciones de la corrida pasaron", evidence["summary"]["all_passed"] and evidence["summary"]["checks_total"] == 41,
          {"passed": evidence["summary"]["checks_passed"], "total": evidence["summary"]["checks_total"]})
    check("sin entrenamiento ni cambios de datos", evidence["scope"]["models_trained"] is False and evidence["scope"]["data_modified"] is False)
    raw = ROOT / "Hackaton/Semana 1/Datos"
    orig_bad = [k for k, h in evidence["provenance"]["originals_sha256"].items() if not (raw / f"{k}.parquet").is_file() or digest(raw / f"{k}.parquet") != h]
    check("los once originales conservan el hash citado", not orig_bad, orig_bad)
    informe = (HERE / "INFORME.md").read_text(encoding="utf-8")
    missing = []
    for link in re.findall(r"\]\(([^)]+)\)", informe):
        if link.startswith(("http://", "https://", "mailto:")):
            continue
        if not (HERE / link.split("#")[0]).resolve().exists():
            missing.append(link)
    check("enlaces locales del informe", not missing, missing)
    check("el informe cita la corrida vigente", evidence["run_id"] in informe)
    figures = json.loads((HERE / "cifras_informe.json").read_text(encoding="utf-8"))["checks"]
    failures = []
    for item in figures:
        try:
            value = resolve(evidence, item["path"])
        except Exception as error:  # noqa: BLE001
            failures.append({"name": item["name"], "error": str(error)})
            continue
        expected, tol = item["expected"], item["tol"]
        if tol == 0 or isinstance(expected, bool):
            ok = value == expected
        else:
            ok = abs(float(value) - float(expected)) <= tol * max(abs(float(expected)), 1e-12)
        if not ok:
            failures.append({"name": item["name"], "path": item["path"], "expected": expected, "found": value})
    check(f"cifras del informe ({len(figures)})", not failures, failures)
    report["run"] = str(run.relative_to(ROOT))
    report["checks_passed"] = sum(1 for c in report["checks"] if c["passed"])
    report["checks_total"] = len(report["checks"])
    report["independent_validation"] = False
    report["human_review"] = "pending"
    (HERE / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("passed", "checks_passed", "checks_total", "run")}, ensure_ascii=False))
    if not report["passed"]:
        for c in report["checks"]:
            if not c["passed"]:
                print("FALLA:", c["name"], c["detail"])
        sys.exit(1)


if __name__ == "__main__":
    main()
