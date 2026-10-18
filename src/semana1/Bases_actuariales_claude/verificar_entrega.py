"""Verifica la entrega de Bases_actuariales_claude sin recalcular nada y sin pandas.

Comprueba: que la corrida vigente existe y su manifiesto coincide con los archivos (hashes), que el script de la carpeta es
el copiado en la corrida, que los 18 controles pasaron sin cambios de datos, índices ni entrenamiento, que la corrida se
calculó sobre la capa que hoy señala current_dataset.json (avisa, sin fallar, si el índice cambió después), que
PLAN_PRUEBAS.md cita la corrida vigente, y que cada cifra de cifras_plan.json coincide con evidencia.json.
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
        node = node[int(key)] if isinstance(node, list) and not filters else node[key]
        if filters:
            conditions = dict(item.split("=", 1) for item in filters.split(";"))
            found = [row for row in node if all(str(row.get(k)) == v for k, v in conditions.items())]
            if len(found) != 1:
                raise KeyError(f"{path}: {len(found)} coincidencias para {conditions}")
            node = found[0]
    return node


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
    check("el script de la carpeta es el copiado en la corrida", digest(HERE / "bases_actuariales.py") == manifest.get("bases_actuariales.py"))
    summary = evidence["checks_summary"]
    check("todos los controles de la corrida pasaron", summary["all_passed"] and summary["checks_total"] == 18, {"passed": summary["checks_passed"], "total": summary["checks_total"]})
    scope = evidence["scope"]
    check("sin cambios de datos, índices ni entrenamiento", scope["data_modified"] is False and scope["indices_modified"] is False and scope["models_trained"] is False)

    index = json.loads((ROOT / "Hackaton/Semana 1/Limpieza/current_dataset.json").read_text(encoding="utf-8"))
    if index["workspace_relative_run"] != evidence["provenance"]["active_run"]:
        report["notes"].append(f"current_dataset.json señala ahora {index['workspace_relative_run']}; la corrida se calculó sobre {evidence['provenance']['active_run']}. Repetir bases_actuariales.py.")
    else:
        catalog_path = ROOT / index["catalog_workspace_relative"]
        check("el catálogo activo es el que usó la corrida", digest(catalog_path) == evidence["provenance"]["catalog_sha256"])
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        mismatched = [name for name, h in evidence["provenance"]["tables_sha256"].items() if catalog[name]["sha256"] != h]
        check("los hashes de las tablas usadas siguen en el catálogo activo", not mismatched, mismatched)

    plan = (HERE / "PLAN_PRUEBAS.md").read_text(encoding="utf-8")
    check("el plan cita la corrida vigente", evidence["run_id"] in plan, evidence["run_id"])
    figures = json.loads((HERE / "cifras_plan.json").read_text(encoding="utf-8"))
    mismatches = []
    for item in figures["checks"]:
        try:
            observed = resolve(evidence, item["path"])
        except (KeyError, IndexError, TypeError) as exc:
            mismatches.append({"name": item["name"], "error": str(exc)})
            continue
        expected = item["expected"]
        if isinstance(expected, bool) or isinstance(expected, str) or expected is None:
            ok = observed == expected
        else:
            tol = float(item.get("tol", 0))
            ok = observed is not None and abs(float(observed) - float(expected)) <= tol * max(abs(float(expected)), 1e-12) + (0 if tol else 1e-9)
        if not ok:
            mismatches.append({"name": item["name"], "path": item["path"], "expected": expected, "observed": observed})
    check(f"{len(figures['checks'])} cifras del plan ligadas a la evidencia", not mismatches, mismatches[:20])
    report["figures_checked"] = len(figures["checks"])
    report["run_id"] = evidence["run_id"]
    (HERE / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for c in report["checks"]:
        print(("OK  " if c["passed"] else "FALLA ") + c["name"] + ("" if c["passed"] else f" -> {c['detail']}"))
    for note in report["notes"]:
        print("NOTA " + note)
    print("Resultado:", "pasa" if report["passed"] else "falla")
    if not report["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
