"""Construye el dashboard HTML bilingüe (ES/EN) a partir de la evidencia de validar_ajustes.py.

Lee runs/<corrida>/evidencia.json y las tablas CSV de esa corrida, arma un JSON compacto y lo incrusta en
plantilla_dashboard.html. Escribe runs/<corrida>/dashboard.html y una copia en dashboard.html (raíz de la
carpeta) y actualiza el manifiesto de la corrida. Sin dependencias externas: el HTML funciona sin red.

Uso: python construir_dashboard.py [ruta_de_la_corrida]   (por defecto, la corrida de current_run.json
o, si no existe, la más reciente en runs/).
"""
from __future__ import annotations

import csv
import hashlib
import json
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


def read_csv(path: Path, numeric=(), integer=()) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            out = {}
            for k, v in row.items():
                if v == "" or v is None:
                    out[k] = None
                elif k in integer:
                    out[k] = int(float(v))
                elif k in numeric:
                    out[k] = float(v)
                else:
                    out[k] = v
            rows.append(out)
    return rows


DECISIONS = [
    ("D32", "16 oct", "ID01, EXP01", "Limpieza reversible de claves y exposición; cribado CAP00", "Reversible key and exposure cleaning; CAP00 screening"),
    ("D34", "16 oct", "revisión", "Revisión de capitales extremos sin corregirlos", "Review of extreme capitals without correcting them"),
    ("D36", "16 oct", "CAP01", "2.073 capitales /1000 por autorización explícita", "2,073 capitals /1000 by explicit authorization"),
    ("D38", "16 oct", "CAT01, AGE01", "Alias de construcción y edad del tomador recalculada", "Construction aliases and recomputed policyholder age"),
    ("D40", "16 oct", "auditoría", "58 puntos VD01–VD58 y nuevos sondeos", "58 VD01–VD58 items and new probes"),
    ("D41", "16 oct", "revisión", "604 pares de siniestros revisados; DUP01 propuesto", "604 claim pairs reviewed; DUP01 proposed"),
    ("D42", "16 oct", "DUP01", "604 copias excluidas; 162.546 siniestros", "604 copies excluded; 162,546 claims"),
    ("D43", "16 oct", "revisión", "Calendario 2024 y día 31-12 omitido; CAL00 propuesto", "2024 calendar and omitted 31 Dec; CAL00 proposed"),
    ("D44", "16 oct", "revisión", "2.742 rechazos con continuidad; REN00 propuesto", "2,742 declines with continuity; REN00 proposed"),
    ("D45", "16 oct", "REN00", "Marca audit_ren00 y guard de predictores", "audit_ren00 flag and predictor guard"),
    ("D46", "16 oct", "revisión", "413 siniestros anteriores al primer periodo; PRE00 propuesto", "413 claims before the first period; PRE00 proposed"),
    ("D47", "16 oct", "PRE00", "Marca audit_pre00 y coste fuera del objetivo", "audit_pre00 flag and cost outside the target"),
    ("D48", "16 oct", "revisión", "1.454 capitales pendientes revisados", "1,454 pending capitals reviewed"),
    ("D49", "16 oct", "CAP02R", "867 capitales /1000 en rama retrospectiva", "867 capitals /1000 in a retrospective branch"),
    ("D51", "16 oct", "revisión", "Doce discrepancias numéricas", "Twelve numeric discrepancies"),
    ("D52", "16 oct", "CAP03R", "Once capitales /1000 (rama)", "Eleven capitals /1000 (branch)"),
    ("D53", "16 oct", "revisión", "109 capitales con apoyo posterior", "109 capitals with later support"),
    ("D54", "16 oct", "CAP04R", "109 capitales /1000 (rama); 467 pendientes", "109 capitals /1000 (branch); 467 pending"),
    ("D55", "16 oct", "revisión", "108 capitales sin referencia original habitual; se conservan", "108 capitals without a usual original reference; kept"),
    ("D56", "16 oct", "revisión", "202 capitales con contexto incompleto; sin cambios", "202 capitals with incomplete context; no changes"),
    ("D57", "16 oct", "revisión", "48 referencias distantes; DIST01-R propone 46", "48 distant references; DIST01-R proposes 46"),
    ("D58", "16 oct", "CAP05R", "46 capitales /1000 (rama); 421 pendientes", "46 capitals /1000 (branch); 421 pending"),
    ("D59", "16 oct", "validación", "Validación independiente de los ajustes (Claude): 41/41 y este dashboard", "Independent validation of the adjustments (Claude): 41/41 and this dashboard"),
]


def main() -> None:
    if len(sys.argv) > 1:
        run = Path(sys.argv[1]).resolve()
    else:
        cur = HERE / "current_run.json"
        if cur.is_file():
            run = ROOT / json.loads(cur.read_text(encoding="utf-8"))["workspace_relative_run"]
        else:
            run = sorted((HERE / "runs").glob("val_*"))[-1]
    ev = json.loads((run / "evidencia.json").read_text(encoding="utf-8"))
    t = run / "tables"
    exp01 = read_csv(t / "exp01_cambios.csv", numeric=("old", "new"), integer=("covered_days",))
    cap01 = read_csv(t / "cap01_cohorte_recalculada.csv", numeric=("sum_insured", "prior_sum_insured", "ratio"), integer=("gap_days",))
    age01 = read_csv(t / "age01_discrepancias.csv", integer=("old", "new", "days_quote_to_inception"))
    id01 = read_csv(t / "id01_muestra.csv")
    dup01 = read_csv(t / "dup01_pares.csv", numeric=("paid_to_date", "incurred_to_date", "recoveries"), integer=("duplicate_group",))
    pre00 = read_csv(t / "pre00_siniestros.csv", numeric=("paid_to_date", "incurred_to_date", "recoveries"), integer=("days_before_first",))
    ren00 = read_csv(t / "ren00_cohorte.csv", integer=("renewal_count",))
    retro = read_csv(t / "cap0xr_cambios_acumulados.csv", numeric=("old", "new"))
    for r in cap01:
        r["period_start"] = (r.get("period_start") or "")[:10]
    lines = ["motor", "buildings", "contents"]
    products = {}
    for line in lines:
        prof = ev["profiles"][line]
        tables = {"exp01": [r for r in exp01 if r["table"] in (f"policies_{line}", f"test_{line}")],
                  "ren00": [r for r in ren00 if r["line"] == line]}
        if line == "motor":
            tables["id01"] = id01
        else:
            tables["cap01"] = [r for r in cap01 if r["line"] == line]
            tables["age01"] = [r for r in age01 if r["table"] in (f"policies_{line}", f"test_{line}")]
            tables["retro"] = [r for r in retro if r["line"] == line]
        products[line] = {"profile": prof, "tables": tables}
    data = {
        "meta": {"run_id": ev["run_id"], "created_utc": ev["created_utc"], "environment": ev["environment"], "base_run": ev["lineage"]["active_base"],
                 "retro_run": ev["lineage"]["active_retrospective"], "checks_total": ev["summary"]["checks_total"], "checks_passed": ev["summary"]["checks_passed"],
                 "findings": ev["summary"]["findings"], "built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "runs": ev["runs"]},
        "originals": ev["provenance"]["originals_sha256"], "checks": ev["checks"], "lineage": ev["lineage"], "invariance": ev["invariance_summary"],
        "rules": ev["rules"], "open_issues": ev["open_issues"], "products": products,
        "claims": {"dup01": {"summary": ev["rules"]["DUP01"], "pairs": dup01}, "pre00": {"summary": ev["rules"]["PRE00"], "rows": pre00},
                   "profiles": {line: ev["profiles"][line]["claims"] for line in lines}},
        "retro": {"summary": ev["rules"]["CAP0xR"], "rows": retro},
        "decisions": [{"id": d[0], "date": d[1], "rule": d[2], "es": d[3], "en": d[4]} for d in DECISIONS],
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    template = (HERE / "plantilla_dashboard.html").read_text(encoding="utf-8")
    assert template.count("/*__DATA__*/") == 1
    html = template.replace("/*__DATA__*/", payload)
    (run / "dashboard.html").write_text(html, encoding="utf-8")
    (HERE / "dashboard.html").write_text(html, encoding="utf-8")
    (run / "dashboard_data.json").write_text(payload + "\n", encoding="utf-8")
    manifest_path = run / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    for name in ["dashboard.html", "dashboard_data.json"]:
        manifest[name] = digest(run / name)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run": run.relative_to(ROOT).as_posix(), "dashboard_bytes": len(html.encode("utf-8")), "data_bytes": len(payload.encode("utf-8")),
                      "dashboard_sha256": manifest["dashboard.html"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
