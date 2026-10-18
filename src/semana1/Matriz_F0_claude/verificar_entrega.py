"""Verifica la entrega de Matriz_F0_claude sin recalcular nada.

Comprueba: manifiesto de la corrida vigente (hashes), que el script de la carpeta es el copiado en la corrida, que todos
los controles pasaron sin cambios de datos, índices ni entrenamiento, que la corrida usó la capa y la corrida de bases
que hoy están vigentes (avisa, sin fallar, si cambiaron), que el contrato de disponibilidad no tiene columnas sin
clasificar y excluye por ramo las columnas obligatorias, que los metadatos Parquet de las tres matrices y de las
particiones tienen las filas esperadas, y que las cifras de cifras_f0.json coinciden con evidencia.json.
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
MUST_EXCLUDE = ["customer_service_contacts", "renewal_decision", "audit_ren00", "surname"]
MUST_EXCLUDE_HOME = ["sum_insured_raw", "audit_capital_scale_adjusted", "audit_capital_scale_confirmed", "audit_capital_cap01"]


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
                raise KeyError(f"{path}: {len(found)} coincidencias")
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
    evidence = json.loads((run / "evidencia.json").read_text(encoding="utf-8"))
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    bad = [n for n, h in manifest.items() if not (run / n).is_file() or digest(run / n) != h]
    check("manifiesto de la corrida", not bad, bad[:10])
    check("el script de la carpeta es el copiado en la corrida", digest(HERE / "construir_f0.py") == manifest.get("construir_f0.py"))
    s = evidence["checks_summary"]
    check("todos los controles de la corrida pasaron", s["all_passed"], {"passed": s["checks_passed"], "total": s["checks_total"]})
    sc = evidence["scope"]
    check("sin cambios de datos, índices ni entrenamiento", sc["data_modified"] is False and sc["indices_modified"] is False and sc["models_trained"] is False)

    active = json.loads((ROOT / "Hackaton/Semana 1/Limpieza/current_dataset.json").read_text(encoding="utf-8"))
    bases = json.loads((ROOT / "Hackaton/Semana 1/Bases_actuariales_claude/current_run.json").read_text(encoding="utf-8"))
    if active["workspace_relative_run"] != evidence["provenance"]["active_run"]:
        report["notes"].append("La capa activa cambió después de la corrida; repetir construir_f0.py.")
    if bases["workspace_relative_run"] != evidence["provenance"]["bases_run"]:
        report["notes"].append("La corrida vigente de Bases_actuariales_claude cambió; repetir construir_f0.py.")

    contract = json.loads((run / "contrato_disponibilidad.json").read_text(encoding="utf-8"))["columnas"]
    problems = []
    for line, cols in contract.items():
        problems += [f"{line}:{c} sin clasificar" for c, v in cols.items() if v["bloque"] == "revisar"]
        needed = MUST_EXCLUDE + (MUST_EXCLUDE_HOME if line != "motor" else [])
        problems += [f"{line}:{c} no excluida" for c in needed if c in cols and cols[c]["bloque"] != "excluida"]
        problems += [f"{line}:{c} ausente" for c in needed if c not in cols]
    check("contrato completo y exclusiones obligatorias por ramo", not problems, problems[:10])

    try:
        import pyarrow.parquet as pq
        rows = {line: pq.read_metadata(run / f"tables/f0_{line}.parquet").num_rows for line in ["motor", "buildings", "contents"]}
        expected = {line: evidence["lines"][line]["rows_train"] + evidence["lines"][line]["rows_test"] for line in rows}
        part_rows = pq.read_metadata(run / "tables/particiones.parquet").num_rows
        check("filas de las matrices y de las particiones", rows == expected and part_rows == 3035950, {"matrices": rows, "particiones": part_rows})
    except ImportError:
        report["notes"].append("pyarrow no disponible: no se leyeron los metadatos Parquet (los hashes del manifiesto sí se comprobaron)")

    figures = json.loads((HERE / "cifras_f0.json").read_text(encoding="utf-8"))
    mismatches = []
    for item in figures["checks"]:
        try:
            observed = resolve(evidence, item["path"])
        except (KeyError, IndexError, TypeError) as exc:
            mismatches.append({"name": item["name"], "error": str(exc)})
            continue
        if observed != item["expected"]:
            mismatches.append({"name": item["name"], "expected": item["expected"], "observed": observed})
    check(f"{len(figures['checks'])} cifras ligadas a la evidencia", not mismatches, mismatches[:10])
    report["run_id"] = evidence["run_id"]
    (HERE / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for c in report["checks"]:
        print(("OK  " if c["passed"] else "FALLA ") + c["name"] + ("" if c["passed"] else f" -> {c['detail']}"))
    for n in report["notes"]:
        print("NOTA " + n)
    print("Resultado:", "pasa" if report["passed"] else "falla")
    if not report["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
