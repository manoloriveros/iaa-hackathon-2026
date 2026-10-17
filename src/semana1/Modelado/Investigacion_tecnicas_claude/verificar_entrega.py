"""Verifica la entrega de Investigacion_tecnicas_claude sin recalcular los diagnósticos.

Comprueba: hashes del catálogo activo frente a la procedencia de la corrida, manifiesto de la
corrida, enlaces locales del informe, ausencia de marcadores pendientes, y que cada cifra de
cifras_informe.json coincida con evidencia.json dentro de su tolerancia. Escribe verification.json.
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
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def resolve(evidence, path: str):
    """Resuelve rutas como a/b[c=1;d=x]/e sobre dicts y listas de dicts."""
    node = evidence
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

    def check(name: str, ok: bool, detail=None) -> None:
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

    index = json.loads((ROOT / "Hackaton/Semana 1/Limpieza/current_dataset.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / index["catalog_workspace_relative"]).read_text(encoding="utf-8"))
    prov = evidence["provenance"]["files"]
    lineage = {}
    for k in prov:
        active = catalog[k]
        audit_only = (
            (active.get("parent_sha256") == prov[k]["sha256"] and active.get("original_values_changed", 1) == 0)
            or (active.get("audit_parent_sha256") == prov[k]["sha256"]
                and active.get("audit_original_values_changed", 1) == 0)
        )
        if active["sha256"] == prov[k]["sha256"]:
            lineage[k] = "igual"
        elif audit_only:
            lineage[k] = "capa de auditoría sobre la tabla usada (valores previos sin cambios)"
        else:
            lineage[k] = "DISTINTA"
    check("procedencia compatible con el catálogo activo", all(v != "DISTINTA" for v in lineage.values()),
          {"catalogo_activo": index["workspace_relative_run"], "catalogo_corrida": evidence["provenance"]["catalog"], "tablas": lineage})
    mismatch = [k for k, v in prov.items() if digest(ROOT / v["path"]) != v["sha256"]]
    check("hashes de las once tablas", not mismatch, mismatch)
    check("sin entrenamiento", evidence.get("models_trained") is False and evidence.get("labels_materialized_for_training") is False)

    informe = (HERE / "INFORME.md").read_text(encoding="utf-8")
    check("sin marcador RUNID", "RUNID" not in informe)
    links = re.findall(r"\]\(([^)]+)\)", informe)
    missing = []
    for link in links:
        if link.startswith(("http://", "https://", "mailto:")):
            continue
        target = (HERE / link.split("#")[0]).resolve()
        if not target.exists():
            missing.append(link)
    check("enlaces locales del informe", not missing, missing)
    check("figuras y tablas listadas", all((run / "figuras" / f).is_file() for f in evidence["figures"])
          and all((run / "tables" / t).is_file() for t in evidence["tables"]))

    figures = json.loads((HERE / "cifras_informe.json").read_text(encoding="utf-8"))["checks"]
    failures = []
    for item in figures:
        try:
            value = resolve(evidence, item["path"])
        except Exception as error:  # noqa: BLE001
            failures.append({"name": item["name"], "error": str(error)})
            continue
        expected, tol = item["expected"], item["tol"]
        if tol == 0:
            ok = value == expected
        else:
            ok = abs(float(value) - float(expected)) <= tol * max(abs(float(expected)), 1e-12)
        if not ok:
            failures.append({"name": item["name"], "path": item["path"], "expected": expected, "found": value})
    check(f"cifras del informe ({len(figures)})", not failures, failures)

    sources = json.loads((HERE / "fuentes.json").read_text(encoding="utf-8"))["sources"]
    ids = [s["id"] for s in sources]
    cited = set(re.findall(r"\bC\d{2}\b", informe))
    check("fuentes citadas existen", cited <= set(ids), sorted(cited - set(ids)))
    check("fuentes sin citar", not (set(ids) - cited), sorted(set(ids) - cited))

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
