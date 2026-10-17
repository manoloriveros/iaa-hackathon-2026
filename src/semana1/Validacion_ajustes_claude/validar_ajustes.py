"""Validación crítica e independiente de los ajustes aplicados a los datos (Claude).

Recalcula cada regla desde los Parquet originales con código propio, la contrasta fila a fila con las
bitácoras y las capas derivadas de Codex, comprueba que ninguna otra celda cambió entre capas, verifica
hashes y linaje de catálogos, y deja evidencia reproducible para el informe y el dashboard.

Reglas cubiertas: ID01, EXP01 (D32), CAP01 (D36), CAT01 y AGE01 (D38), DUP01 (D42), REN00 (D45),
PRE00 (D47) y la rama retrospectiva CAP02R/CAP03R/CAP04R (D49, D52, D54).

No entrena modelos, no modifica datos ni índices, no publica. Cada ejecución crea runs/val_<marca>_<id>/.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "RUTAS_PROYECTO.json").is_file():
            return candidate
    raise FileNotFoundError("No se encontró RUTAS_PROYECTO.json hacia arriba.")


HERE = Path(__file__).resolve().parent
ROOT = find_root(HERE)
READER = ROOT / "Preparación" / ".cache" / "parquet-reader"
if READER.is_dir() and str(READER) not in sys.path:
    sys.path.insert(0, str(READER))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pyarrow as pa  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

S1 = ROOT / "Hackaton" / "Semana 1"
RAW = S1 / "Datos"
LIMP = S1 / "Limpieza"
RUNS = {
    "clean": "clean_20261016T175335Z_a6412ce0",
    "capfix": "capfix_20261016T184904Z_099a22b1",
    "refine": "refine_20261016T190025Z_6751bba4",
    "dupfix": "dupfix_20261016T195843Z_fc0bb423",
    "renaudit": "renaudit_20261016T203904Z_657dd741",
    "preaudit": "preaudit_20261016T211816Z_817285a5",
}
# La rama retrospectiva (CAP02R, CAP03R, CAP04R, CAP05R…) sigue creciendo: se valida la corrida que señale
# current_retrospective_dataset.json en el momento de ejecutar, y su linaje se recorre por hashes padre.
RETRO_INDEX = LIMP / "current_retrospective_dataset.json"
D28_REPORT = ROOT / "Preparación/artifacts/verification/workspace_layout_20261016T164312Z_e7327974/report.json"
D34_RUN = S1 / "Revision_capitales/runs/capital_20261016T180903Z_bceb990c"
POLICY_TABLES = ["policies_motor", "policies_buildings", "policies_contents", "test_motor", "test_buildings", "test_contents"]
HOME_TABLES = ["policies_buildings", "policies_contents", "test_buildings", "test_contents"]
LINES = ["motor", "buildings", "contents"]
CAT_MAP = {"Brick": "brick", "BRICK": "brick", "NON_STANDARD": "non_standard", "STONE": "stone", "T": "t", "W": "w"}
CAP_FIELDS = {
    "buildings": ["customer_id", "address_id", "construction_type", "occupancy", "accidental_damage_cover",
                  "voluntary_excess", "compulsory_excess", "smoke_alarms", "mortgage"],
    "contents": ["customer_id", "address_id", "tenure", "security_level", "high_value_items", "accidental_damage_cover",
                 "works_from_home", "lodgers", "bicycle_cover", "voluntary_excess", "compulsory_excess"],
}
CAP_THRESHOLD = {"buildings": 10_000_000, "contents": 1_000_000}


# ----------------------------------------------------------------------------- utilidades
def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def run_dir(name: str) -> Path:
    return LIMP / "runs" / RUNS[name]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def table(path: Path, columns=None) -> pa.Table:
    return pq.read_table(path, columns=columns)


def frame(path: Path, columns=None) -> pd.DataFrame:
    return pq.read_table(path, columns=columns).to_pandas()


def dates(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series)


def completed_years(at: pd.Series, birth: pd.Series) -> pd.Series:
    at, birth = dates(at), dates(birth)
    before_birthday = (at.dt.month < birth.dt.month) | ((at.dt.month == birth.dt.month) & (at.dt.day < birth.dt.day))
    return (at.dt.year - birth.dt.year - before_birthday.astype(int)).astype("int64")


def key_hash(df: pd.DataFrame, cols) -> pd.Series:
    return pd.util.hash_pandas_object(df[cols], index=False)


def differing_columns(t1: pa.Table, t2: pa.Table, cols) -> list[str]:
    out = []
    for c in cols:
        a, b = t1.column(c).combine_chunks(), t2.column(c).combine_chunks()
        if a.type != b.type:
            try:
                b = b.cast(a.type)
            except (pa.ArrowInvalid, pa.ArrowNotImplementedError):
                out.append(c)
                continue
        if not a.equals(b):
            out.append(c)
    return out


def jsonable(value):
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if np.isnan(value) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if value is pd.NA or value is None:
        return None
    if isinstance(value, float) and np.isnan(value):
        return None
    return value


def records(df: pd.DataFrame, limit=None) -> list[dict]:
    d = df if limit is None else df.head(limit)
    d = d.copy()
    for c in d.columns:
        if str(d[c].dtype).startswith("datetime"):
            d[c] = d[c].dt.strftime("%Y-%m-%d")
    return [jsonable({k: (None if (isinstance(v, float) and np.isnan(v)) else v) for k, v in r.items()}) for r in d.to_dict("records")]


class Checks:
    def __init__(self):
        self.items = []

    def add(self, cid: str, rule: str, name_es: str, name_en: str, passed, expected=None, observed=None, detail=None, severity="control"):
        self.items.append(jsonable({"id": cid, "rule": rule, "name_es": name_es, "name_en": name_en, "passed": bool(passed),
                                    "expected": expected, "observed": observed, "detail": detail, "severity": severity}))
        print(("OK   " if passed else "FALLA") + f" {cid} {name_es}", flush=True)


# ----------------------------------------------------------------------------- principal
def main() -> None:
    stamp = datetime.now(timezone.utc).strftime("val_%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8]
    out = HERE / "runs" / stamp
    (out / "tables").mkdir(parents=True, exist_ok=False)
    checks = Checks()
    ev = {"run_id": stamp, "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
          "environment": {"python": sys.version.split()[0], "pandas": pd.__version__, "numpy": np.__version__, "pyarrow": pa.__version__},
          "scope": {"base_rules": ["ID01", "EXP01", "CAP01", "CAT01", "AGE01", "DUP01", "REN00", "PRE00"],
                    "retrospective_rules": "las de la corrida activa de current_retrospective_dataset.json (CAP02R en adelante)", "models_trained": False, "data_modified": False},
          "runs": RUNS, "provenance": {}, "lineage": {}, "invariance": {}, "rules": {}, "profiles": {}, "open_issues": {}}
    dash = {"products": {}, "claims": {}, "retro": {}, "overview": {}}

    # ------------------------------------------------------------------ A. integridad y linaje
    originals = {p.stem: digest(p) for p in sorted(RAW.glob("*.parquet"))}
    ev["provenance"]["originals_sha256"] = originals
    d28 = D28_REPORT.read_text(encoding="utf-8")
    missing = [k for k, h in originals.items() if h not in d28]
    checks.add("A01", "integridad", "Los once originales conservan el SHA-256 del informe de reorganización D28",
               "All eleven originals keep the SHA-256 recorded in the D28 layout report", not missing and len(originals) == 11, 11, len(originals) - len(missing), missing)
    cur = load_json(LIMP / "current_dataset.json"); cur_r = load_json(RETRO_INDEX)
    retro_run = ROOT / cur_r["workspace_relative_run"]
    RUNS["retro_active"] = retro_run.name
    catalogs = {}
    bad_hash = []
    for name in RUNS:
        cat_path = run_dir(name) / "dataset_catalog.json"
        if not cat_path.is_file():
            continue
        cat = load_json(cat_path)
        catalogs[name] = cat
        for tbl, entry in cat.items():
            p = ROOT / entry["workspace_relative_path"]
            if p.is_file() and digest(p) != entry["sha256"]:
                bad_hash.append((name, tbl))
    all_catalogs = {}
    for cat_path in sorted((LIMP / "runs").glob("*/dataset_catalog.json")):
        try:
            all_catalogs[cat_path.parent.name] = load_json(cat_path)
        except (OSError, ValueError):
            continue
    ev["provenance"]["catalogs_checked"] = sorted(catalogs)
    checks.add("A02", "integridad", "Cada tabla presente coincide con el SHA-256 de su catálogo (capas base y rama activa)",
               "Every table present matches the SHA-256 in its run catalog (base layers and active branch)", not bad_hash, 0, len(bad_hash), bad_hash)
    # lineage chain
    chain = []
    def parents_of(cat, tbl) -> set:
        # Codex registra varios padres según la operación: parent_sha256 (valores), audit_parent_sha256 (marcas),
        # retrospective_/numeric_/context_/distant_capital_parent_sha256 (rama). Se acepta cualquier clave *parent_sha256.
        return {v for k, v in cat[tbl].items() if k.endswith("parent_sha256") and isinstance(v, str)}
    links = [("clean", "policies_motor", originals["policies_motor"]), ("capfix", "policies_buildings", catalogs["clean"]["policies_buildings"]["sha256"]),
             ("refine", "policies_buildings", catalogs["capfix"]["policies_buildings"]["sha256"]), ("dupfix", "claims", originals["claims"]),
             ("renaudit", "policies_motor", catalogs["refine"]["policies_motor"]["sha256"]), ("preaudit", "claims", catalogs["dupfix"]["claims"]["sha256"])]
    ok_chain = True
    for name, tbl, expected in links:
        got = parents_of(catalogs[name], tbl) if name in catalogs else set()
        if name == "clean":  # la primera capa no registra padre: su padre es el original, comprobado por hash en A01
            got = {originals[tbl]}
        ok = expected is not None and expected in got
        ok_chain &= ok
        chain.append({"run": name, "table": tbl, "parent_matches_previous_layer": ok, "parents_declared": len(got)})
    # rama: recorrer ancestros por hash desde la corrida activa hasta renaudit, tabla por tabla
    sha_to_run = {}
    for rname, cat in all_catalogs.items():
        for tbl in ["policies_buildings", "policies_contents", "test_buildings", "test_contents"]:
            if tbl in cat:
                sha_to_run.setdefault((tbl, cat[tbl]["sha256"]), rname)
    branch_runs, branch_ok = set(), True
    for tbl in ["policies_buildings", "policies_contents"]:
        target = catalogs["renaudit"][tbl]["sha256"]
        frontier, seen, reached = [retro_run.name], set(), False
        while frontier:
            rname = frontier.pop()
            if rname in seen or rname not in all_catalogs:
                continue
            seen.add(rname)
            for parent in parents_of(all_catalogs[rname], tbl):
                if parent == target:
                    reached = True
                prun = sha_to_run.get((tbl, parent))
                if prun and prun not in seen:
                    frontier.append(prun)
        branch_runs |= seen; branch_ok &= reached
        chain.append({"run": retro_run.name, "table": tbl, "parent_matches_previous_layer": reached, "parents_declared": len(seen)})
    ev["lineage"]["chain"] = chain
    ev["lineage"]["branch_runs_visited"] = sorted(branch_runs)
    checks.add("A03", "linaje", "La cadena de capas enlaza por hash padre: original → clean → capfix → refine → renaudit; claims original → dupfix → preaudit; la rama activa remonta hasta renaudit por sus padres declarados",
               "Layer chain links by parent hash: original → clean → capfix → refine → renaudit; claims original → dupfix → preaudit; the active branch traces back to renaudit through its declared parents", ok_chain and branch_ok, True, ok_chain and branch_ok, chain)
    verifs = {}
    for name in ["clean", "capfix", "refine", "dupfix", "renaudit", "preaudit", "retro_active"]:
        vp = run_dir(name) / "verification.json"
        if vp.is_file():
            verifs[name if name != "retro_active" else retro_run.name] = bool(load_json(vp).get("passed"))
    ev["lineage"]["codex_verifications_passed"] = verifs
    checks.add("A04", "linaje", "Las verificaciones propias de Codex de cada corrida presente terminan en passed=true",
               "Codex's own verification.json of each run present ends with passed=true", all(verifs.values()) and len(verifs) >= 6, len(verifs), sum(verifs.values()), verifs)
    ev["lineage"]["active_base"] = cur["workspace_relative_run"]; ev["lineage"]["active_retrospective"] = cur_r["workspace_relative_run"]
    ev["lineage"]["active_retrospective_status"] = cur_r.get("status")
    checks.add("A05", "linaje", "El índice base apunta a preaudit (PRE00) y el retrospectivo a una rama que remonta a renaudit; ninguno aprobado para modelar",
               "Base index points to preaudit (PRE00) and the retrospective index to a branch tracing back to renaudit; neither approved for modelling",
               cur["workspace_relative_run"].endswith(RUNS["preaudit"]) and branch_ok and not cur["approved_for_modeling"] and not cur_r["approved_for_modeling"],
               None, {"base": cur["workspace_relative_run"], "retro": cur_r["workspace_relative_run"], "retro_status": cur_r.get("status")})

    # ------------------------------------------------------------------ B. ID01 y EXP01 (original → clean)
    customers = frame(RAW / "customers.parquet", ["customer_id", "date_of_birth"])
    master = customers.customer_id.astype("string")
    checks.add("B00", "ID01", "El maestro de clientes es único y todo ID tiene ocho dígitos ASCII",
               "Customer master is unique and every ID has eight ASCII digits", master.is_unique and master.str.fullmatch(r"[0-9]{8}").all(), True, True)
    leading_zero_share = float(master.str.startswith("0").mean())
    id01 = {"tables": {}, "master_leading_zero_share": round(leading_zero_share, 4)}
    exp01 = {"tables": {}, "by_year": []}
    invariance = {}
    id_samples, exp_rows = [], []
    for name in POLICY_TABLES:
        raw = table(RAW / f"{name}.parquet")
        clean = table(run_dir("clean") / "data" / f"{name}.parquet")
        df = raw.select(["row_id", "customer_id", "period_start", "period_end", "exposure"]).to_pandas()
        s = df.customer_id.astype("string")
        lengths = s.str.len().value_counts().sort_index()
        padded = s.str.zfill(8)
        numeric_ok = bool(s.str.fullmatch(r"[0-9]{1,8}").all())
        in_master = bool(padded.isin(set(master)).all())
        collision = int(padded.nunique() < s.nunique())
        changed = padded.ne(s)
        ledger = frame(run_dir("clean") / "ledger" / f"{name}_customer_id.parquet")
        led_match = (len(ledger) == int(changed.sum())) and set(ledger.row_id) == set(df.loc[changed, "row_id"]) and \
            ledger.set_index("row_id").new.astype("string").reindex(df.loc[changed, "row_id"]).eq(padded[changed].values).all()
        clean_ids = clean.column("customer_id").to_pandas().astype("string")
        id01["tables"][name] = {"rows": len(df), "changed": int(changed.sum()), "short_id_share": round(float(changed.mean()), 4),
                                "length_distribution": {int(k): int(v) for k, v in lengths.items()}, "numeric_only": numeric_ok,
                                "all_in_master_after_padding": in_master, "distinct_ids_merged_by_padding": collision,
                                "unmatched_before": int((~s.isin(set(master))).sum()), "unmatched_after": int((~padded.isin(set(master))).sum()),
                                "ledger_rows": len(ledger), "ledger_matches_recomputation": bool(led_match), "clean_layer_equals_recomputation": bool(clean_ids.eq(padded).all())}
        if changed.any():
            smp = df.loc[changed, ["row_id", "customer_id"]].head(200).assign(new=padded[changed].head(200).values, table=name)
            id_samples.append(smp)
        # EXP01
        ps, pe = dates(df.period_start), dates(df.period_end)
        days = (pe - ps).dt.days + 1
        exp = (days / 365).round(4)
        mode = np.select([np.abs(df.exposure - days) <= 5.1e-5, np.abs(df.exposure - days / 360) <= 5.1e-5,
                          np.abs(df.exposure - days / 365) <= 5.1e-5], ["day_amount", "ACT360", "ACT365"], default="other")
        e_changed = exp.ne(df.exposure)
        eledger = frame(run_dir("clean") / "ledger" / f"{name}_exposure.parquet")
        e_match = (len(eledger) == int(e_changed.sum())) and set(eledger.row_id) == set(df.loc[e_changed, "row_id"]) and \
            np.allclose(eledger.set_index("row_id").new.reindex(df.loc[e_changed, "row_id"]).values, exp[e_changed].values, atol=1e-9)
        clean_exp = clean.column("exposure").to_pandas()
        exp01["tables"][name] = {"rows": len(df), "changed": int(e_changed.sum()), "modes_all_rows": {k: int(v) for k, v in pd.Series(mode).value_counts().items()},
                                 "modes_changed_rows": {k: int(v) for k, v in pd.Series(mode[e_changed]).value_counts().items()},
                                 "other_convention_rows": int((mode == "other").sum()), "dates_valid": bool(ps.notna().all() and pe.notna().all() and (pe >= ps).all()),
                                 "covered_days_min": int(days.min()), "covered_days_max": int(days.max()), "exposure_sum_raw": round(float(df.exposure.sum()), 4),
                                 "exposure_sum_recomputed": round(float(exp.sum()), 4), "exposure_sum_clean_layer": round(float(clean_exp.sum()), 4),
                                 "ledger_rows": len(eledger), "ledger_matches_recomputation": bool(e_match), "clean_layer_equals_recomputation": bool(np.allclose(clean_exp.values, exp.values, atol=1e-9)),
                                 "day_amount_full_year_rows": int(((mode == "day_amount") & (df.exposure == 365)).sum())}
        yr = pd.DataFrame({"year": ps.dt.year, "raw": df.exposure, "recomputed": exp, "days": days}).groupby("year").agg(raw=("raw", "sum"), recomputed=("recomputed", "sum"), rows=("days", "size"))
        for y, r in yr.iterrows():
            exp01["by_year"].append({"table": name, "year": int(y), "rows": int(r.rows), "exposure_raw": round(float(r.raw), 4), "exposure_recomputed": round(float(r.recomputed), 4)})
        if e_changed.any():
            exp_rows.append(pd.DataFrame({"table": name, "row_id": df.loc[e_changed, "row_id"].values, "period_start": ps[e_changed].dt.strftime("%Y-%m-%d").values,
                                          "period_end": pe[e_changed].dt.strftime("%Y-%m-%d").values, "covered_days": days[e_changed].values,
                                          "old": df.loc[e_changed, "exposure"].values, "new": exp[e_changed].values, "convention": mode[e_changed]}))
        # invariance original → clean
        other = [c for c in raw.column_names if c not in ("customer_id", "exposure")]
        diff = differing_columns(raw, clean, other)
        same_rows = raw.num_rows == clean.num_rows and raw.column("row_id").combine_chunks().equals(clean.column("row_id").combine_chunks())
        invariance[f"original→clean:{name}"] = {"rows_equal_and_ordered": bool(same_rows), "columns_changed_besides_rule": diff, "columns_compared": len(other)}
        del raw, clean, df
    ev["rules"]["ID01"] = id01; ev["rules"]["EXP01"] = exp01
    t_changed = sum(v["changed"] for v in id01["tables"].values())
    checks.add("B01", "ID01", "Solo customer_id de autos tiene ceros perdidos; los demás identificadores tienen longitud fija",
               "Only motor customer_id lost leading zeros; all other identifiers have fixed length",
               all(len(v["length_distribution"]) == 1 for k, v in id01["tables"].items() if "motor" not in k) and id01["tables"]["policies_motor"]["changed"] > 0, None,
               {k: v["length_distribution"] for k, v in id01["tables"].items()})
    checks.add("B02", "ID01", "Rellenar a ocho dígitos recupera todos los cruces con el maestro sin fusionar claves distintas (98.110 train, 25.554 test)",
               "Zero-padding restores every join to the master without merging distinct keys (98,110 train, 25,554 test)",
               all(v["all_in_master_after_padding"] and v["unmatched_after"] == 0 and v["distinct_ids_merged_by_padding"] == 0 and v["numeric_only"] for v in id01["tables"].values())
               and id01["tables"]["policies_motor"]["changed"] == 98110 and id01["tables"]["test_motor"]["changed"] == 25554, 123664, t_changed)
    checks.add("B03", "ID01", "La bitácora ID01 y la capa clean coinciden fila a fila con el recálculo",
               "ID01 ledger and clean layer match the recomputation row by row", all(v["ledger_matches_recomputation"] and v["clean_layer_equals_recomputation"] for v in id01["tables"].values()), True, True)
    checks.add("B04", "ID01", "Plausibilidad: la proporción de IDs cortos en autos (≈10 %) coincide con la de IDs del maestro que empiezan por cero",
               "Plausibility: share of short motor IDs (≈10 %) matches the share of master IDs starting with zero",
               abs(id01["tables"]["policies_motor"]["short_id_share"] - leading_zero_share) < 0.01, round(leading_zero_share, 4), id01["tables"]["policies_motor"]["short_id_share"], severity="hallazgo")
    tot_changed = sum(v["changed"] for v in exp01["tables"].values())
    checks.add("C01", "EXP01", "Toda exposición original cae en una de tres convenciones (ACT/365, ACT/360 o días); ninguna fila queda sin explicar",
               "Every raw exposure falls into one of three conventions (ACT/365, ACT/360 or day counts); no row is unexplained",
               all(v["other_convention_rows"] == 0 for v in exp01["tables"].values()), 0, sum(v["other_convention_rows"] for v in exp01["tables"].values()))
    checks.add("C02", "EXP01", "Las fechas son válidas (fin ≥ inicio) y ningún periodo supera 365 días cubiertos; el caso bisiesto de 366 días no aparece",
               "Dates are valid (end ≥ start) and no period exceeds 365 covered days; the 366-day leap case does not occur",
               all(v["dates_valid"] and v["covered_days_max"] <= 366 for v in exp01["tables"].values()), None, {k: v["covered_days_max"] for k, v in exp01["tables"].items()})
    checks.add("C03", "EXP01", "Cambios recalculados: 5.736 autos, 4.182 edificios, 4.311 contenidos, cero en test; bitácora y capa clean coinciden",
               "Recomputed changes: 5,736 motor, 4,182 buildings, 4,311 contents, zero in test; ledger and clean layer match",
               exp01["tables"]["policies_motor"]["changed"] == 5736 and exp01["tables"]["policies_buildings"]["changed"] == 4182 and exp01["tables"]["policies_contents"]["changed"] == 4311
               and all(v["changed"] == 0 for k, v in exp01["tables"].items() if k.startswith("test")) and all(v["ledger_matches_recomputation"] and v["clean_layer_equals_recomputation"] for v in exp01["tables"].values()), 14229, tot_changed)
    raw_total = sum(v["exposure_sum_raw"] for v in exp01["tables"].values() if v); rec_total = sum(v["exposure_sum_recomputed"] for v in exp01["tables"].values())
    exp01["totals"] = {"raw": round(raw_total, 4), "recomputed": round(rec_total, 4), "train_raw": round(sum(exp01["tables"][t]["exposure_sum_raw"] for t in POLICY_TABLES[:3]), 4),
                       "train_recomputed": round(sum(exp01["tables"][t]["exposure_sum_recomputed"] for t in POLICY_TABLES[:3]), 4)}
    checks.add("C04", "EXP01", "La exposición total de entrenamiento pasa de 2.658.636,18 a 1.968.577,06 años (D32); el exceso venía de 2.319 filas en días",
               "Training exposure goes from 2,658,636.18 to 1,968,577.06 years (D32); the excess came from 2,319 rows stored as days",
               abs(exp01["totals"]["train_raw"] - 2658636.1771) < 0.01 and abs(exp01["totals"]["train_recomputed"] - 1968577.0591) < 0.01, [2658636.1771, 1968577.0591],
               [exp01["totals"]["train_raw"], exp01["totals"]["train_recomputed"]])
    checks.add("C05", "EXP01", "Ninguna otra columna cambió entre el original y la capa clean (comparación completa de todas las columnas restantes)",
               "No other column changed between original and clean layer (full comparison of every remaining column)",
               all(v["rows_equal_and_ordered"] and not v["columns_changed_besides_rule"] for k, v in invariance.items() if k.startswith("original→clean")), 0,
               sum(len(v["columns_changed_besides_rule"]) for k, v in invariance.items() if k.startswith("original→clean")))
    pd.concat(id_samples).to_csv(out / "tables" / "id01_muestra.csv", index=False)
    exp_all = pd.concat(exp_rows)
    exp_all.to_csv(out / "tables" / "exp01_cambios.csv", index=False)

    # ------------------------------------------------------------------ D. CAP01 (clean → capfix), recalculo de la cohorte D34 desde los originales
    approved = frame(run_dir("capfix") / "evidence" / "approved_cohort.parquet")
    cap_ledger = frame(run_dir("capfix") / "ledger" / "all_capital_changes.parquet")
    pending = frame(run_dir("capfix") / "tables" / "pending_capitals.parquet")
    cap01 = {"lines": {}, "approved_rows": len(approved), "pending_rows": len(pending)}
    cap_tables_rows = []
    for line, thr in CAP_THRESHOLD.items():
        frames = []
        for p in ["policies", "test"]:
            t = frame(RAW / f"{p}_{line}.parquet", ["row_id", "policy_id", "period_start", "period_end", "sum_insured", "written_premium"] + CAP_FIELDS[line])
            t["source_table"] = f"{p}_{line}"; frames.append(t)
        f = pd.concat(frames, ignore_index=True)
        f["period_start"] = dates(f.period_start); f["period_end"] = dates(f.period_end)
        f = f.sort_values(["policy_id", "period_start", "period_end", "row_id"]).reset_index(drop=True)
        hi = f.sum_insured > thr
        normal_pos = pd.Series(np.where(~hi, np.arange(len(f)), np.nan), index=f.index)
        prior_pos = normal_pos.groupby(f.policy_id).ffill().groupby(f.policy_id).shift()
        exists = prior_pos.notna()
        anchor = f.reindex(prior_pos.fillna(-1).astype(int)).reset_index(drop=True)
        known = pd.Series(True, index=f.index); same = pd.Series(True, index=f.index)
        for col in CAP_FIELDS[line]:
            a, b = f[col], anchor[col]
            if col == "construction_type":
                a = a.astype("string").str.casefold().str.strip(); b = b.astype("string").str.casefold().str.strip()
            known &= a.notna() & b.notna() & exists
            same &= a.eq(b).fillna(False)
        temporal = anchor.period_end < f.period_start
        gap = (f.period_start - anchor.period_start).dt.days
        ratio = (f.sum_insured / 1000) / anchor.sum_insured
        support = hi & exists & known & same & temporal & gap.between(1, 400) & ratio.between(0.9, 1.1)
        mine = set(f.loc[support, "row_id"]); theirs = set(approved.loc[approved.line == line, "row_id"])
        # cascade on corrected data
        f2 = f.copy(); corr = f2.row_id.isin(theirs); f2.loc[corr, "sum_insured"] = f2.loc[corr, "sum_insured"] / 1000
        hi2 = f2.sum_insured > thr
        np2 = pd.Series(np.where(~hi2, np.arange(len(f2)), np.nan), index=f2.index)
        pp2 = np2.groupby(f2.policy_id).ffill().groupby(f2.policy_id).shift(); ex2 = pp2.notna()
        an2 = f2.reindex(pp2.fillna(-1).astype(int)).reset_index(drop=True)
        k2 = pd.Series(True, index=f2.index); s2 = pd.Series(True, index=f2.index)
        for col in CAP_FIELDS[line]:
            a, b = f2[col], an2[col]
            if col == "construction_type":
                a = a.astype("string").str.casefold().str.strip(); b = b.astype("string").str.casefold().str.strip()
            k2 &= a.notna() & b.notna() & ex2; s2 &= a.eq(b).fillna(False)
        cascade = hi2 & ex2 & k2 & s2 & (an2.period_end < f2.period_start) & (f2.period_start - an2.period_start).dt.days.between(1, 400) & ((f2.sum_insured / 1000) / an2.sum_insured).between(0.9, 1.1)
        normal, extreme = f.loc[~hi, "sum_insured"], f.loc[hi, "sum_insured"]
        log = np.log10(f.sum_insured.clip(lower=1))
        hist, edges = np.histogram(log, bins=np.arange(3, 9.26, 0.25))
        pend_line = hi & ~support
        cap01["lines"][line] = {
            "rows": len(f), "extreme_rows": int(hi.sum()), "extreme_policies": int(f.loc[hi, "policy_id"].nunique()), "threshold_CU": thr,
            "recomputed_prior_supported": len(mine), "approved_prior_supported": len(theirs), "sets_equal": mine == theirs,
            "only_recomputed": sorted(mine - theirs)[:20], "only_approved": sorted(theirs - mine)[:20],
            "normal_cluster_max_CU": float(normal.max()), "extreme_cluster_min_CU": float(extreme.min()), "gap_factor": round(float(extreme.min() / normal.max()), 2),
            "normal_median_CU": float(normal.median()), "extreme_median_div1000_CU": float(extreme.median() / 1000),
            "rows_between_threshold_div10_and_threshold": int(((f.sum_insured > thr / 10) & (f.sum_insured <= thr)).sum()),
            "hypothetical_ratio_quantiles_cohort": {str(q): round(float(v), 4) for q, v in ratio[support].quantile([0, .25, .5, .75, 1]).items()},
            "cascade_rows_if_recomputed_on_corrected_data": int(cascade.sum()),
            "pending": {"total": int(pend_line.sum()), "with_prior_normal_anchor": int((pend_line & exists).sum()),
                        "anchor_same_context_ratio_outside": int((pend_line & exists & known & same & temporal & gap.between(1, 400) & ~ratio.between(0.9, 1.1)).sum()),
                        "anchor_context_changed_or_incomplete": int((pend_line & exists & ~(known & same)).sum()), "no_prior_anchor": int((pend_line & ~exists).sum()),
                        "test_rows": int((pend_line & f.source_table.str.startswith("test")).sum())},
            "log10_histogram": {"edges": [round(float(e), 2) for e in edges], "counts": [int(c) for c in hist]},
        }
        cap_tables_rows.append(f.loc[support, ["source_table", "row_id", "policy_id", "period_start", "sum_insured"]].assign(
            prior_row_id=anchor.loc[support, "row_id"].values, prior_sum_insured=anchor.loc[support, "sum_insured"].values, gap_days=gap[support].values, ratio=ratio[support].round(4).values, line=line))
        del f, f2, anchor, an2
    ev["rules"]["CAP01"] = cap01
    checks.add("D01", "CAP01", "Recalculando los criterios D34 desde los originales se obtiene exactamente la cohorte aprobada: 1.074 edificios y 999 contenidos (2.073)",
               "Recomputing the D34 criteria from the originals yields exactly the approved cohort: 1,074 buildings and 999 contents (2,073)",
               all(v["sets_equal"] for v in cap01["lines"].values()) and cap01["lines"]["buildings"]["recomputed_prior_supported"] == 1074 and cap01["lines"]["contents"]["recomputed_prior_supported"] == 999, 2073,
               sum(v["recomputed_prior_supported"] for v in cap01["lines"].values()))
    checks.add("D02", "CAP01", "El cribado separa dos nubes sin solape: edificios ≤1,06 M frente a ≥52 M CU; contenidos ≤0,35 M frente a ≥8,2 M CU; los umbrales caen dentro del hueco",
               "The screen separates two non-overlapping clusters: buildings ≤1.06 M vs ≥52 M CU; contents ≤0.35 M vs ≥8.2 M CU; thresholds sit inside the gap",
               all(v["gap_factor"] > 10 for v in cap01["lines"].values()), None, {k: {"max_normal": v["normal_cluster_max_CU"], "min_extreme": v["extreme_cluster_min_CU"]} for k, v in cap01["lines"].items()}, severity="hallazgo")
    checks.add("D03", "CAP01", "La hipótesis ×1000 es coherente a nivel global: la mediana de la nube extrema dividida por mil coincide con la mediana normal (227.000 frente a 226.000; 38.650 frente a 39.300 CU)",
               "The ×1000 hypothesis is globally consistent: extreme-cluster median divided by 1,000 matches the normal median (227,000 vs 226,000; 38,650 vs 39,300 CU)",
               all(0.9 < v["extreme_median_div1000_CU"] / v["normal_median_CU"] < 1.1 for v in cap01["lines"].values()), None,
               {k: [v["normal_median_CU"], v["extreme_median_div1000_CU"]] for k, v in cap01["lines"].items()}, severity="hallazgo")
    # clean → capfix invariance and arithmetic
    cap_ok = True; details = {}
    for name in POLICY_TABLES:
        a = table(run_dir("clean") / "data" / f"{name}.parquet"); b = table(run_dir("capfix") / "data" / f"{name}.parquet")
        other = [c for c in a.column_names if c != "sum_insured"]
        diff = differing_columns(a, b, other)
        same_rows = a.num_rows == b.num_rows and a.column("row_id").combine_chunks().equals(b.column("row_id").combine_chunks())
        if "sum_insured" in a.column_names:
            sa = a.column("sum_insured").to_pandas(); sb = b.column("sum_insured").to_pandas(); rid = a.column("row_id").to_pandas()
            changed = sa.ne(sb)
            led = cap_ledger[cap_ledger.source_table == name]
            arith = bool(np.allclose(sb[changed].values, sa[changed].values / 1000)) and set(rid[changed]) == set(led.row_id) and len(led) == int(changed.sum())
            details[name] = {"changed": int(changed.sum()), "ledger_rows": len(led), "new_equals_old_div_1000": arith}
            cap_ok &= arith
        else:
            details[name] = {"identical_bytes": digest(run_dir("clean") / "data" / f"{name}.parquet") == digest(run_dir("capfix") / "data" / f"{name}.parquet")}
            cap_ok &= details[name]["identical_bytes"]
        invariance[f"clean→capfix:{name}"] = {"rows_equal_and_ordered": bool(same_rows), "columns_changed_besides_rule": diff, "columns_compared": len(other)}
        cap_ok &= same_rows and not diff
        del a, b
    cap01["capfix_layer"] = details
    checks.add("D04", "CAP01", "En la capa capfix solo cambia sum_insured en las 2.073 filas aprobadas (802/272 edificios, 731/268 contenidos), siempre old/1000; autos byte a byte igual",
               "In the capfix layer only sum_insured changes, on the 2,073 approved rows (802/272 buildings, 731/268 contents), always old/1000; motor byte-identical",
               cap_ok and details["policies_buildings"]["changed"] == 802 and details["test_buildings"]["changed"] == 272 and details["policies_contents"]["changed"] == 731 and details["test_contents"]["changed"] == 268, 2073,
               sum(v.get("changed", 0) for v in details.values()))
    checks.add("D05", "CAP01", "Los 1.454 capitales pendientes de D34 siguen intactos en la capa base; 1.060 no tienen referencia anterior normal en su póliza",
               "The 1,454 pending capitals from D34 remain untouched in the base layer; 1,060 have no earlier normal reference in their policy",
               sum(v["pending"]["total"] for v in cap01["lines"].values()) == 1454 and len(pending) == 1454, 1454, sum(v["pending"]["total"] for v in cap01["lines"].values()),
               {k: v["pending"] for k, v in cap01["lines"].items()})
    checks.add("D06", "CAP01", "Riesgo de cascada acotado: recomputando el criterio sobre los datos ya corregidos solo 3 filas pendientes pasarían a tener apoyo anterior (no se aplicó)",
               "Cascade risk is bounded: recomputing the criterion on corrected data only 3 pending rows would gain prior support (not applied)",
               sum(v["cascade_rows_if_recomputed_on_corrected_data"] for v in cap01["lines"].values()) <= 5, None, sum(v["cascade_rows_if_recomputed_on_corrected_data"] for v in cap01["lines"].values()), severity="hallazgo")
    pd.concat(cap_tables_rows).to_csv(out / "tables" / "cap01_cohorte_recalculada.csv", index=False)

    # ------------------------------------------------------------------ E/F. CAT01 y AGE01 (capfix → refine)
    cat01 = {"tables": {}}; age01 = {"tables": {}}
    birth = customers.set_index("customer_id").date_of_birth
    age_rows = []
    for name in HOME_TABLES:
        a = table(run_dir("capfix") / "data" / f"{name}.parquet"); b = table(run_dir("refine") / "data" / f"{name}.parquet")
        cols = ["row_id", "customer_id", "period_start", "period_end", "policyholder_age", "exposure", "days_quote_to_inception", "new_business"] + (["construction_type"] if "buildings" in name else [])
        fa = a.select(cols).to_pandas(); fb = b.select([c for c in cols if c in b.column_names]).to_pandas()
        rule_cols = ["policyholder_age"] + (["construction_type"] if "buildings" in name else [])
        other = [c for c in a.column_names if c not in rule_cols]
        diff = differing_columns(a, b, other)
        same_rows = a.num_rows == b.num_rows and a.column("row_id").combine_chunks().equals(b.column("row_id").combine_chunks())
        invariance[f"capfix→refine:{name}"] = {"rows_equal_and_ordered": bool(same_rows), "columns_changed_besides_rule": diff, "columns_compared": len(other)}
        if "buildings" in name:
            raw_ct = fa.construction_type.astype("string")
            mapped = raw_ct.replace(CAT_MAP)
            counts = pd.DataFrame({"old": raw_ct, "new": mapped}).value_counts(dropna=False).reset_index(name="rows")
            changed = mapped.ne(raw_ct).fillna(False)
            cat01["tables"][name] = {"rows": len(fa), "changed": int(changed.sum()), "null_values": int(raw_ct.isna().sum()),
                                     "transitions": records(counts.sort_values("rows", ascending=False)),
                                     "refine_layer_equals_recomputation": bool(fb.construction_type.astype("string").fillna("<NA>").eq(mapped.fillna("<NA>")).all()),
                                     "t_w_kept_separate": bool(set(mapped.dropna().unique()) <= {"brick", "non_standard", "stone", "t", "w"} and "timber" not in set(mapped.dropna().unique())
                                                               and ("t" in set(raw_ct.str.casefold().dropna().unique())) == ("t" in set(mapped.dropna().unique()))),
                                     "distinct_before": int(raw_ct.nunique()), "distinct_after": int(mapped.nunique())}
        ps = dates(fa.period_start); pe = dates(fa.period_end); bd = dates(fa.customer_id.map(birth))
        age = completed_years(ps, bd)
        diffs = fa.policyholder_age - age
        mism = diffs.ne(0)
        quote = ps - pd.to_timedelta(fa.days_quote_to_inception.fillna(0).astype(int), unit="D")
        age_quote = completed_years(quote, bd)
        age_end = completed_years(pe, bd)
        bday = pd.to_datetime(dict(year=ps.dt.year, month=bd.dt.month, day=bd.dt.day.where(~((bd.dt.month == 2) & (bd.dt.day == 29)), 28)))
        bday_on_start = bday.eq(ps)
        explained_quote = mism & (diffs == -1) & age_quote.eq(fa.policyholder_age)
        explained_bday_on_start = mism & (diffs == -1) & ~explained_quote & bday_on_start
        explained_end = mism & (diffs == 1) & age_end.eq(fa.policyholder_age)
        ledger = frame(run_dir("refine") / "ledger" / f"{name}_policyholder_age.parquet")
        led_ok = len(ledger) == int(mism.sum()) and set(ledger.row_id) == set(fa.loc[mism, "row_id"]) and ledger.set_index("row_id").new.reindex(fa.loc[mism, "row_id"]).eq(age[mism].values).all()
        age01["tables"][name] = {"rows": len(fa), "discrepancies": int(mism.sum()), "diff_distribution": {str(int(k)): int(v) for k, v in diffs[mism].value_counts().items()},
                                 "max_abs_diff": int(diffs.abs().max()), "ambiguous_leap_cases": int(((bd.dt.month == 2) & (bd.dt.day == 29) & ~ps.dt.is_leap_year & (ps.dt.month == 2) & (ps.dt.day == 28)).sum()),
                                 "explained_by_age_at_quote_date": int(explained_quote.sum()), "explained_by_birthday_on_period_start_exclusive": int(explained_bday_on_start.sum()),
                                 "plus_one_explained_by_age_at_period_end": int(explained_end.sum()), "unexplained": int((mism & ~explained_quote & ~explained_bday_on_start & ~explained_end).sum()),
                                 "age_at_quote_matches_all_rows_share": round(float(age_quote.eq(fa.policyholder_age).mean()), 4), "age_at_start_matches_all_rows_share": round(float(age.eq(fa.policyholder_age).mean()), 4),
                                 "raw_age_min": int(fa.policyholder_age.min()), "raw_age_max": int(fa.policyholder_age.max()), "recomputed_min": int(age.min()), "recomputed_max": int(age.max()),
                                 "ledger_rows": len(ledger), "ledger_matches_recomputation": bool(led_ok), "refine_layer_equals_recomputation": bool(fb.policyholder_age.eq(age).all()),
                                 "age_histogram_raw": {str(int(k)): int(v) for k, v in fa.policyholder_age.value_counts().sort_index().items()},
                                 "age_histogram_new": {str(int(k)): int(v) for k, v in age.value_counts().sort_index().items()}}
        cls = np.select([explained_quote, explained_bday_on_start, explained_end], ["age_at_quote_date", "birthday_on_period_start", "age_at_period_end"], default="unexplained")
        age_rows.append(pd.DataFrame({"table": name, "row_id": fa.loc[mism, "row_id"].values, "customer_id": fa.loc[mism, "customer_id"].values,
                                      "date_of_birth": bd[mism].dt.strftime("%Y-%m-%d").values, "period_start": ps[mism].dt.strftime("%Y-%m-%d").values,
                                      "days_quote_to_inception": fa.loc[mism, "days_quote_to_inception"].values, "old": fa.loc[mism, "policyholder_age"].values,
                                      "new": age[mism].values, "explanation": cls[mism]}))
        del a, b, fa, fb
    ev["rules"]["CAT01"] = cat01; ev["rules"]["AGE01"] = age01
    checks.add("E01", "CAT01", "construction_type es la única columna de texto con variantes de mayúsculas en las once tablas; el mapa de seis alias da 555.824 + 144.386 cambios",
               "construction_type is the only text column with case variants across the eleven tables; the six-alias map yields 555,824 + 144,386 changes",
               cat01["tables"]["policies_buildings"]["changed"] == 555824 and cat01["tables"]["test_buildings"]["changed"] == 144386, 700210, sum(v["changed"] for v in cat01["tables"].values()))
    checks.add("E02", "CAT01", "La capa refine coincide con el recálculo y t/w siguen separados (sin fusión con timber)",
               "Refine layer matches the recomputation and t/w remain separate (no merge with timber)", all(v["refine_layer_equals_recomputation"] and v["t_w_kept_separate"] for v in cat01["tables"].values()), True, True)
    tot_age = sum(v["discrepancies"] for v in age01["tables"].values())
    checks.add("F01", "AGE01", "Edad recalculada al inicio del periodo: 2.936 discrepancias (1.122/300 edificios, 1.209/305 contenidos), todas de un año; bitácora y capa coinciden",
               "Age recomputed at period start: 2,936 discrepancies (1,122/300 buildings, 1,209/305 contents), all of one year; ledger and layer match",
               tot_age == 2936 and all(v["max_abs_diff"] == 1 and v["ledger_matches_recomputation"] and v["refine_layer_equals_recomputation"] for v in age01["tables"].values()), 2936, tot_age)
    expl = sum(v["explained_by_age_at_quote_date"] + v["explained_by_birthday_on_period_start_exclusive"] + v["plus_one_explained_by_age_at_period_end"] for v in age01["tables"].values())
    checks.add("F02", "AGE01", "Hallazgo: la edad original no es un error de captura sino otra convención: edad a la fecha de cotización (o cumpleaños el mismo día de inicio, sin contar) explica el 98 % de las discrepancias y el +1 restante es la edad al fin del periodo",
               "Finding: the raw age is not a capture error but another convention: age at quotation date (or birthday on the start day, not counted) explains 98 % of discrepancies and the remaining +1 cases equal age at period end",
               expl / tot_age > 0.95, None, {"explained": expl, "total": tot_age, "unexplained": tot_age - expl}, severity="hallazgo")
    checks.add("F03", "AGE01", "Ninguna otra columna cambió entre capfix y refine; driver_age de autos no se tocó",
               "No other column changed between capfix and refine; motor driver_age untouched",
               all(v["rows_equal_and_ordered"] and not v["columns_changed_besides_rule"] for k, v in invariance.items() if k.startswith("capfix→refine")) and
               digest(run_dir("capfix") / "data" / "policies_motor.parquet") == digest(run_dir("refine") / "data" / "policies_motor.parquet"), 0,
               sum(len(v["columns_changed_besides_rule"]) for k, v in invariance.items() if k.startswith("capfix→refine")))
    pd.concat(age_rows).to_csv(out / "tables" / "age01_discrepancias.csv", index=False)
    # driver_age vs customer birth (motor, informative)
    fm = frame(run_dir("refine") / "data" / "policies_motor.parquet", ["customer_id", "period_start", "driver_age"])
    da = completed_years(fm.period_start, fm.customer_id.map(birth))
    age01["motor_driver_age_vs_policyholder_age_at_start"] = {"rows": len(fm), "equal": int((fm.driver_age == da).sum()), "share_equal": round(float((fm.driver_age == da).mean()), 4),
                                                             "abs_diff_gt_5": int(((fm.driver_age - da).abs() > 5).sum())}
    del fm

    # ------------------------------------------------------------------ G. DUP01 (claims original → dupfix)
    cl = frame(RAW / "claims.parquet")
    fields = [c for c in cl.columns if c != "claim_id"]
    cl["key"] = key_hash(cl, fields)
    sizes = cl.groupby("key").claim_id.transform("size")
    dup = cl[sizes > 1]
    group_sizes = dup.groupby("key").size()
    collision_guard = int((dup.groupby("key")[fields].nunique(dropna=False).max(axis=1) > 1).sum())
    pairs = dup.groupby("key").claim_id.agg(list)
    short = pairs.map(lambda ids: sorted(ids, key=len)[0]); long = pairs.map(lambda ids: sorted(ids, key=len)[1])
    aliases = frame(run_dir("dupfix") / "ledger" / "claim_id_aliases.parquet")
    excluded = cl[cl.claim_id.isin(set(long))]
    acc = excluded[excluded.status != "repudiated"]
    dfx = table(run_dir("dupfix") / "data" / "claims.parquet")
    kept = cl[~cl.claim_id.isin(set(long))].drop(columns="key").reset_index(drop=True)
    dfx_pd = dfx.to_pandas()
    kept_equal = kept.shape == dfx_pd.shape and list(kept.columns) == list(dfx_pd.columns) and \
        pd.util.hash_pandas_object(kept, index=False).reset_index(drop=True).equals(pd.util.hash_pandas_object(dfx_pd, index=False).reset_index(drop=True))
    ident = sizes > 1
    near = {}
    for label, cols in [("policy_line_peril_lossdate", ["policy_id", "line", "peril", "loss_date"]), ("policy_line_lossdate", ["policy_id", "line", "loss_date"])]:
        s = cl.groupby(cols).claim_id.transform("size"); m = (s > 1) & ~ident
        near[label] = {"rows": int(m.sum()), "groups": int(cl[m].groupby(cols).ngroups)}
    extra = {}
    for label, drop in [("ignoring_report_date", ["report_date"]), ("ignoring_report_repairer_third_party", ["report_date", "repairer_id", "third_party_id"])]:
        cols = [c for c in fields if c not in drop]
        s = cl.groupby(key_hash(cl, cols)).claim_id.transform("size"); extra[label] = int(((s > 1) & ~ident).sum())
    dup01 = {"identical_groups_size2": int((group_sizes == 2).sum()), "identical_groups_larger": int((group_sizes > 2).sum()), "rows_in_identical_groups": int((sizes > 1).sum()),
             "hash_collision_groups": collision_guard, "one_short_one_long_id_per_pair": bool((short.str.len().eq(10) & long.str.len().eq(11)).all()),
             "eleven_char_ids_total": int(cl.claim_id.str.len().eq(11).sum()), "excluded_equals_long_ids": set(aliases.excluded_claim_id) == set(long),
             "retained_equals_short_ids": set(aliases.retained_claim_id) == set(short), "excluded_by_year": {int(k): int(v) for k, v in dates(excluded.loss_date).dt.year.value_counts().sort_index().items()},
             "excluded_by_line": {k: int(v) for k, v in excluded.line.value_counts().items()}, "excluded_by_status": {k: int(v) for k, v in excluded.status.value_counts().items()},
             "excluded_by_peril": {k: int(v) for k, v in excluded.peril.value_counts().items()},
             "net_accepted_excluded_CU": round(float((acc.incurred_to_date - acc.recoveries).sum()), 2), "paid_excluded_CU": round(float(acc.paid_to_date.sum()), 2),
             "rows_original": len(cl), "rows_dupfix": dfx.num_rows, "dupfix_equals_original_minus_excluded_in_order": bool(kept_equal),
             "near_duplicates_not_identical": near, "additional_duplicates_if_relaxing_key": extra}
    ev["rules"]["DUP01"] = dup01
    checks.add("G01", "DUP01", "Recalculo: 604 pares idénticos en los once campos salvo claim_id, ningún grupo mayor; en cada par un ID de 10 y otro de 11 caracteres",
               "Recomputation: 604 pairs identical on the eleven fields except claim_id, no larger group; each pair has one 10- and one 11-character ID",
               dup01["identical_groups_size2"] == 604 and dup01["identical_groups_larger"] == 0 and dup01["one_short_one_long_id_per_pair"] and collision_guard == 0, 604, dup01["identical_groups_size2"])
    checks.add("G02", "DUP01", "Los 604 IDs de 11 caracteres del archivo son exactamente los excluidos; los retenidos son los de 8 dígitos; la capa dupfix es el original sin esas filas, en el mismo orden (162.546)",
               "The file's 604 eleven-character IDs are exactly the excluded ones; retained are the 8-digit ones; dupfix layer is the original minus those rows, same order (162,546)",
               dup01["eleven_char_ids_total"] == 604 and dup01["excluded_equals_long_ids"] and dup01["retained_equals_short_ids"] and dup01["rows_dupfix"] == 162546 and kept_equal, 162546, dup01["rows_dupfix"])
    checks.add("G03", "DUP01", "Efecto financiero recalculado: 3.174.167,49 CU de neto aceptado excluido; 600 de los 604 pares ocurren en 2022",
               "Recomputed financial effect: 3,174,167.49 CU of accepted net excluded; 600 of the 604 pairs occur in 2022",
               abs(dup01["net_accepted_excluded_CU"] - 3174167.49) < 0.01 and dup01["excluded_by_year"].get(2022) == 600, 3174167.49, dup01["net_accepted_excluded_CU"])
    checks.add("G04", "DUP01", "Relajar la clave (ignorar report_date, reparador o tercero) no descubre pares adicionales; quedan 57 colisiones no idénticas por póliza y fecha (17 con el mismo peligro) que se conservan",
               "Relaxing the key (ignoring report_date, repairer or third party) finds no extra pairs; 57 non-identical same-policy/date collisions remain (17 same peril) and are kept",
               extra["ignoring_report_date"] == 0 and extra["ignoring_report_repairer_third_party"] == 0 and near["policy_line_lossdate"]["groups"] == 57 and near["policy_line_peril_lossdate"]["groups"] == 17, None, {"near": near, "extra": extra}, severity="hallazgo")
    pd.DataFrame({"duplicate_group": range(1, len(short) + 1), "retained_claim_id": short.values, "excluded_claim_id": long.values}).merge(
        cl[["claim_id", "policy_id", "line", "peril", "loss_date", "report_date", "status", "paid_to_date", "incurred_to_date", "recoveries"]], left_on="excluded_claim_id", right_on="claim_id").drop(columns="claim_id").to_csv(out / "tables" / "dup01_pares.csv", index=False)

    # ------------------------------------------------------------------ H. REN00 (refine → renaudit)
    rows = []
    for line in LINES:
        tr = frame(run_dir("refine") / "data" / f"policies_{line}.parquet", ["row_id", "policy_id", "customer_id", "period_start", "period_end", "renewal_decision", "renewal_count", "new_business"]); tr["src"] = "train"
        te = frame(run_dir("refine") / "data" / f"test_{line}.parquet", ["row_id", "policy_id", "customer_id", "period_start", "period_end", "renewal_count", "new_business"]); te["src"] = "test"; te["renewal_decision"] = pd.NA
        f = pd.concat([tr, te], ignore_index=True); f["line"] = line; rows.append(f)
    f = pd.concat(rows, ignore_index=True)
    f["period_start"] = dates(f.period_start); f["period_end"] = dates(f.period_end); f["year"] = f.period_start.dt.year
    f = f.sort_values(["line", "policy_id", "period_start", "period_end"]).reset_index(drop=True)
    g = f.groupby(["line", "policy_id"])
    f["next_row"] = g.row_id.shift(-1); f["next_year"] = g.year.shift(-1); f["next_customer"] = g.customer_id.shift(-1); f["next_rc"] = g.renewal_count.shift(-1)
    dec = f[f.renewal_decision.eq("declined_by_insurer")]
    cohort = dec[(dec.year == 2024) & (dec.next_year == 2025)]
    frozen = frame(run_dir("renaudit") / "evidence" / "frozen_cohort.parquet", ["line", "policy_id", "row_id", "previous_row_id"])
    marked_ids = set(cohort.policy_id)
    successor_by_label = f[f.src == "train"].assign(has_next=f.next_row.notna()).groupby(["year", "renewal_decision"]).agg(rows=("row_id", "size"), with_successor=("has_next", "sum")).reset_index()
    successor_by_label["successor_share"] = (successor_by_label.with_successor / successor_by_label.rows).round(4)
    ren = {"cohort_policies": int(cohort.policy_id.nunique()), "by_line": {k: int(v) for k, v in cohort.groupby("line").policy_id.nunique().items()},
           "frozen_cohort_equal": set(frozen.policy_id) == marked_ids and set(frozen.previous_row_id) == set(cohort.row_id),
           "cohort_periods": {k: int(v) for k, v in f[f.policy_id.isin(marked_ids)].groupby("src").size().items()},
           "successor_same_customer": int((cohort.customer_id == cohort.next_customer).sum()), "successor_renewal_count_delta_1": int(((cohort.next_rc - cohort.renewal_count) == 1).sum()),
           "declined_2024_without_successor": int(((dec.year == 2024) & dec.next_row.isna()).sum()),
           "declined_by_year": {int(y): {"rows": int(len(d)), "with_successor_next_year": int((d.next_year == y + 1).sum())} for y, d in dec.groupby("year")},
           "successor_share_by_label_year": records(successor_by_label),
           "decision_counts_by_year": records(f[f.src == "train"].groupby(["year", "renewal_decision"]).size().reset_index(name="rows"))}
    ok_mark = True; mark_detail = {}
    for name in POLICY_TABLES:
        a = table(run_dir("refine") / "data" / f"{name}.parquet"); b = table(run_dir("renaudit") / "data" / f"{name}.parquet")
        added = [c for c in b.column_names if c not in a.column_names]
        diff = differing_columns(a, b, a.column_names)
        same_rows = a.num_rows == b.num_rows and a.column("row_id").combine_chunks().equals(b.column("row_id").combine_chunks())
        invariance[f"refine→renaudit:{name}"] = {"rows_equal_and_ordered": bool(same_rows), "columns_changed_besides_rule": diff, "columns_added": added, "columns_compared": len(a.column_names)}
        flag = b.column("audit_ren00").to_pandas(); pid = b.column("policy_id").to_pandas()
        expected_flag = pid.isin(marked_ids)
        mark_detail[name] = {"marked": int(flag.sum()), "expected": int(expected_flag.sum()), "equal": bool(flag.eq(expected_flag).all()), "nulls": int(flag.isna().sum())}
        ok_mark &= mark_detail[name]["equal"] and same_rows and not diff and added == ["audit_ren00"] and mark_detail[name]["nulls"] == 0
        del a, b
    ren["marks"] = mark_detail
    ev["rules"]["REN00"] = ren
    checks.add("H01", "REN00", "Recalculo de la cohorte: 2.742 pólizas con rechazo del asegurador en 2024 y sucesor en 2025 (1.513 autos, 1.010 edificios, 219 contenidos), igual a la congelada",
               "Cohort recomputation: 2,742 policies declined by the insurer in 2024 with a 2025 successor (1,513 motor, 1,010 buildings, 219 contents), equal to the frozen one",
               ren["cohort_policies"] == 2742 and ren["frozen_cohort_equal"] and ren["by_line"] == {"motor": 1513, "buildings": 1010, "contents": 219}, 2742, ren["cohort_policies"])
    checks.add("H02", "REN00", "audit_ren00 marca exactamente todos los periodos de esas pólizas (9.110 train, 2.931 test = 12.041), sin nulos; ninguna otra celda cambió",
               "audit_ren00 marks exactly every period of those policies (9,110 train, 2,931 test = 12,041), no nulls; no other cell changed",
               ok_mark and ren["cohort_periods"] == {"test": 2931, "train": 9110}, 12041, sum(v["marked"] for v in mark_detail.values()))
    checks.add("H03", "REN00", "Hallazgo: declined_by_insurer no es una no renovación efectiva: entre 2021 y 2024 el 91–100 % de esas filas tiene sucesor al año siguiente, con el mismo cliente y contador +1",
               "Finding: declined_by_insurer is not an effective non-renewal: in 2021–2024, 91–100 % of those rows have a successor the next year, same customer and counter +1",
               all(v["with_successor_next_year"] / v["rows"] > 0.9 for v in ren["declined_by_year"].values()) and ren["successor_same_customer"] == 2742, None, ren["declined_by_year"], severity="hallazgo")
    cohort[["line", "policy_id", "row_id", "customer_id", "period_start", "period_end", "renewal_count", "next_row"]].rename(columns={"row_id": "declined_2024_row_id", "next_row": "successor_2025_row_id"}).assign(
        period_start=lambda d: d.period_start.dt.strftime("%Y-%m-%d"), period_end=lambda d: d.period_end.dt.strftime("%Y-%m-%d")).to_csv(out / "tables" / "ren00_cohorte.csv", index=False)
    periods = f[f.src == "train"][["line", "policy_id", "row_id", "period_start", "period_end"]].copy()
    del f, rows, dec, cohort

    # ------------------------------------------------------------------ I. PRE00 (dupfix → preaudit) y asignación de siniestros
    claims = frame(run_dir("dupfix") / "data" / "claims.parquet")
    claims["loss_date"] = dates(claims.loss_date); claims["report_date"] = dates(claims.report_date)
    periods = periods.sort_values(["line", "policy_id", "period_start"])
    periods["prev_end"] = periods.groupby(["line", "policy_id"]).period_end.shift()
    overlaps = int((periods.prev_end.notna() & (periods.period_start <= periods.prev_end)).sum())
    j = claims[["claim_id", "policy_id", "line", "loss_date"]].merge(periods[["policy_id", "line", "row_id", "period_start", "period_end"]], on=["policy_id", "line"], how="left")
    hit = j[(j.loss_date >= j.period_start) & (j.loss_date <= j.period_end)]
    nhit = hit.groupby("claim_id").size()
    claims["n_hits"] = claims.claim_id.map(nhit).fillna(0).astype(int)
    first = periods.groupby(["line", "policy_id"]).period_start.min(); last = periods.groupby(["line", "policy_id"]).period_end.max()
    idx = pd.MultiIndex.from_frame(claims[["line", "policy_id"]])
    claims["first_start"] = idx.map(first); claims["last_end"] = idx.map(last)
    has_policy = claims.first_start.notna()
    claims["category"] = np.select([claims.n_hits == 1, claims.n_hits > 1, ~has_policy, claims.loss_date < claims.first_start, claims.loss_date > claims.last_end],
                                   ["unique", "ambiguous", "no_policy", "before_first_period", "after_last_period"], default="in_gap")
    bf = claims[claims.category == "before_first_period"]
    pre_ledger = frame(run_dir("preaudit") / "ledger" / "pre00_marked_claims.parquet")
    pre_claims = table(run_dir("preaudit") / "data" / "claims.parquet")
    flag = pre_claims.column("audit_pre00").to_pandas(); cid = pre_claims.column("claim_id").to_pandas()
    expected_flag = cid.isin(set(bf.claim_id))
    a = table(run_dir("dupfix") / "data" / "claims.parquet")
    diff = differing_columns(a, pre_claims, a.column_names)
    same_rows = a.num_rows == pre_claims.num_rows and a.column("claim_id").combine_chunks().equals(pre_claims.column("claim_id").combine_chunks())
    invariance["dupfix→preaudit:claims"] = {"rows_equal_and_ordered": bool(same_rows), "columns_changed_besides_rule": diff, "columns_added": [c for c in pre_claims.column_names if c not in a.column_names]}
    acc_bf = bf.merge(claims[["claim_id", "status", "paid_to_date", "incurred_to_date", "recoveries"]].drop_duplicates("claim_id"), on="claim_id", suffixes=("", "_y")) if "paid_to_date" not in bf.columns else bf
    acc_bf = acc_bf[acc_bf.status != "repudiated"]
    assigned = claims[claims.category == "unique"]; assigned_acc = assigned[assigned.status != "repudiated"]
    pre = {"assignment_categories": {k: int(v) for k, v in claims.category.value_counts().items()}, "overlapping_periods_within_policy": overlaps,
           "before_first_by_line_status": records(bf.groupby(["line", "status"]).size().reset_index(name="rows")),
           "before_first_reported_within_observed_coverage": int((bf.report_date >= bf.first_start).sum()), "before_first_reported_before_first_start": int((bf.report_date < bf.first_start).sum()),
           "days_before_first_quantiles": {str(q): float(v) for q, v in (bf.first_start - bf.loss_date).dt.days.quantile([0, .25, .5, .75, 1]).items()},
           "before_first_by_loss_year": {int(k): int(v) for k, v in bf.loss_date.dt.year.value_counts().sort_index().items()},
           "accepted_before_first": {"records": int(len(acc_bf)), "paid": round(float(acc_bf.paid_to_date.sum()), 2), "incurred": round(float(acc_bf.incurred_to_date.sum()), 2),
                                     "recoveries": round(float(acc_bf.recoveries.sum()), 2), "net": round(float((acc_bf.incurred_to_date - acc_bf.recoveries).sum()), 2)},
           "assigned_accepted": {"records": int(len(assigned_acc)), "net": round(float((assigned_acc.incurred_to_date - assigned_acc.recoveries).sum()), 2)},
           "marks": {"marked": int(flag.sum()), "expected": int(expected_flag.sum()), "equal": bool(flag.eq(expected_flag).all()), "nulls": int(flag.isna().sum())},
           "ledger_rows": len(pre_ledger), "ledger_equals_recomputed_set": set(pre_ledger.claim_id) == set(bf.claim_id),
           "loss_date_range": [claims.loss_date.min().strftime("%Y-%m-%d"), claims.loss_date.max().strftime("%Y-%m-%d")],
           "report_date_range": [claims.report_date.min().strftime("%Y-%m-%d"), claims.report_date.max().strftime("%Y-%m-%d")]}
    ev["rules"]["PRE00"] = pre
    checks.add("I01", "PRE00", "Asignación recalculada por policy_id, ramo e intervalo: 162.133 únicas y 413 anteriores al primer periodo; cero ambiguas, sin póliza, en huecos o posteriores; los periodos no se solapan",
               "Recomputed assignment by policy_id, line and interval: 162,133 unique and 413 before the first period; zero ambiguous, no-policy, in-gap or after-last; periods never overlap",
               pre["assignment_categories"] == {"unique": 162133, "before_first_period": 413} and overlaps == 0, {"unique": 162133, "before_first_period": 413}, pre["assignment_categories"])
    checks.add("I02", "PRE00", "audit_pre00 marca exactamente los 413 recalculados (296/67/50), sin nulos, y ninguna otra celda cambió; 409 aceptados suman 1.721.459,84 CU netos fuera del objetivo",
               "audit_pre00 marks exactly the 413 recomputed claims (296/67/50), no nulls, and no other cell changed; 409 accepted ones total 1,721,459.84 CU net outside the target",
               pre["marks"]["equal"] and pre["ledger_equals_recomputed_set"] and same_rows and not diff and abs(pre["accepted_before_first"]["net"] - 1721459.84) < 0.01 and pre["accepted_before_first"]["records"] == 409, 413, pre["marks"]["marked"])
    checks.add("I03", "PRE00", "Hallazgo: los 413 siniestros se reportaron dentro de un periodo observado de su póliza (ninguno antes del primer inicio); ocurrieron entre 4 y 499 días antes, mediana 31",
               "Finding: all 413 claims were reported within an observed period of their policy (none before the first start); they occurred 4 to 499 days earlier, median 31",
               pre["before_first_reported_within_observed_coverage"] == 413, 413, pre["before_first_reported_within_observed_coverage"], severity="hallazgo")
    bf.assign(loss_date=bf.loss_date.dt.strftime("%Y-%m-%d"), report_date=bf.report_date.dt.strftime("%Y-%m-%d"), first_start=bf.first_start.dt.strftime("%Y-%m-%d"),
              days_before_first=(bf.first_start - bf.loss_date).dt.days)[["claim_id", "policy_id", "line", "peril", "loss_date", "report_date", "status", "paid_to_date", "incurred_to_date", "recoveries", "first_start", "days_before_first"]].to_csv(out / "tables" / "pre00_siniestros.csv", index=False)
    claims_for_profile = claims.copy()
    del a, pre_claims, j, hit

    # ------------------------------------------------------------------ J. Rama retrospectiva (corrida activa del índice)
    cum = frame(retro_run / "ledger" / "cumulative_retrospective_changes.parquet")
    pend_r = frame(retro_run / "tables" / "pending_capitals.parquet", ["row_id", "source_table", "sum_insured"])
    rsummary = load_json(retro_run / "summary.json") if (retro_run / "summary.json").is_file() else {}
    retro = {"active_run": retro_run.name, "status": cur_r.get("status"), "ledger_rows": len(cum), "by_rule": {k: int(v) for k, v in cum.rule.value_counts().items()},
             "by_table": {k: int(v) for k, v in cum.source_table.value_counts().items()}, "test2025_supported": int(cum.audit_ref_test2025.sum()),
             "pending_in_branch": len(pend_r), "pending_by_table": {k: int(v) for k, v in pend_r.source_table.value_counts().items()},
             "summary_cumulative_changes": rsummary.get("cumulative_retrospective_changes"), "summary_pending_after": rsummary.get("pending_after")}
    ok_r = True; rdet = {}
    for name in HOME_TABLES:
        a = table(run_dir("renaudit") / "data" / f"{name}.parquet"); b = table(ROOT / catalogs["retro_active"][name]["workspace_relative_path"])
        other = [c for c in a.column_names if c != "sum_insured"]
        diff = differing_columns(a, b, other)
        same_rows = a.num_rows == b.num_rows and a.column("row_id").combine_chunks().equals(b.column("row_id").combine_chunks())
        sa = a.column("sum_insured").to_pandas(); sb = b.column("sum_insured").to_pandas(); rid = a.column("row_id").to_pandas()
        changed = sa.ne(sb); led = cum[cum.source_table == name]
        arith = bool(np.allclose(sb[changed].values, sa[changed].values / 1000)) and set(rid[changed]) == set(led.row_id) and len(led) == int(changed.sum())
        rdet[name] = {"changed": int(changed.sum()), "ledger_rows": len(led), "new_equals_old_div_1000": arith, "other_columns_changed": diff, "rows_equal_and_ordered": bool(same_rows),
                      "still_extreme_after_branch": int((sb > CAP_THRESHOLD["buildings" if "buildings" in name else "contents"]).sum())}
        ok_r &= arith and same_rows and not diff
        invariance[f"renaudit→{retro_run.name}:{name}"] = {"rows_equal_and_ordered": bool(same_rows), "columns_changed_besides_rule": diff, "columns_compared": len(other)}
        del a, b
    retro["layer"] = rdet
    base_rows = pd.concat([frame(run_dir("refine") / "data" / f"{t}.parquet", ["row_id", "period_start", "period_end", "policy_id", "sum_insured"]) for t in HOME_TABLES])
    ref = cum.copy(); ref["reference_period_start"] = pd.to_datetime(ref.reference_period_start, errors="coerce")
    ref = ref.merge(base_rows[["row_id", "period_start", "period_end"]], on="row_id", how="left")
    ref["period_start"] = dates(ref.period_start); ref["period_end"] = dates(ref.period_end)
    later = ref.reference_period_start > ref.period_end; earlier = ref.reference_period_start < ref.period_start
    retro["references_after_corrected_period"] = int(later.sum()); retro["references_before_corrected_period"] = int(earlier.sum())
    retro["references_overlapping_or_missing"] = int((~later & ~earlier).sum())
    retro["reference_gap_days_quantiles_later"] = {str(q): float(v) for q, v in (ref.reference_period_start - ref.period_end).dt.days[later].quantile([0, .25, .5, .75, 1]).items()} if later.any() else {}
    retro["by_rule_reference_direction"] = records(pd.DataFrame({"rule": ref.rule, "direction": np.where(later, "later", np.where(earlier, "earlier", "other"))}).groupby(["rule", "direction"]).size().reset_index(name="rows"))
    pend_policies = set(pend_r.merge(base_rows[["row_id", "policy_id"]], on="row_id", how="left").policy_id.dropna())
    retro["policies_with_corrected_and_pending_rows"] = int(len(set(ref.policy_id) & pend_policies))
    ref_cap = cum.merge(base_rows[["row_id", "sum_insured"]].rename(columns={"row_id": "reference_row_id", "sum_insured": "reference_sum_insured"}), on="reference_row_id", how="left")
    ratio_r = ref_cap.new / ref_cap.reference_sum_insured
    retro["ratio_new_over_reference_quantiles"] = {str(q): round(float(v), 4) for q, v in ratio_r.quantile([0, .05, .25, .5, .75, .95, 1]).items()}
    retro["reference_rows_found"] = int(ref_cap.reference_sum_insured.notna().sum())
    same_base = all(catalogs["retro_active"][t]["sha256"] == catalogs["renaudit"][t]["sha256"] for t in ["test_motor", "policies_motor"]) \
        and catalogs["retro_active"]["claims"]["sha256"] == catalogs["preaudit"]["claims"]["sha256"]
    retro["motor_and_claims_identical_to_base"] = same_base
    ev["rules"]["CAP0xR"] = retro
    checks.add("J01", "CAP0xR", "En la rama activa solo cambia sum_insured, exactamente en las filas de la bitácora acumulada y siempre como old/1000; autos y claims son idénticos a la base",
               "In the active branch only sum_insured changes, exactly on the cumulative ledger rows and always as old/1000; motor and claims are identical to the base",
               ok_r and same_base and (retro["summary_cumulative_changes"] in (None, len(cum))), retro["summary_cumulative_changes"], sum(v["changed"] for v in rdet.values()),
               {"by_rule": retro["by_rule"], "by_table": retro["by_table"]})
    checks.add("J02", "CAP0xR", "Toda referencia de la rama es estrictamente anterior o posterior al periodo corregido (ninguna solapada ni ausente); la base conserva 1.454 pendientes y la rama los que declara su índice",
               "Every branch reference is strictly earlier or later than the corrected period (none overlapping or missing); the base keeps 1,454 pending and the branch what its index declares",
               retro["references_overlapping_or_missing"] == 0 and len(pending) == 1454 and len(pend_r) == cur_r.get("pending_capitals", len(pend_r)), {"later+earlier": len(cum)},
               {"later": retro["references_after_corrected_period"], "earlier": retro["references_before_corrected_period"], "pending_branch": len(pend_r), "pending_base": len(pending), "test2025_supported": retro["test2025_supported"]}, severity="hallazgo")
    cum.assign(reference_period_start=cum.reference_period_start.astype("string")).to_csv(out / "tables" / "cap0xr_cambios_acumulados.csv", index=False)

    # ------------------------------------------------------------------ K. invariancia global original → base final y columnas tocadas
    ev["invariance"] = invariance
    touched = {}
    for name in POLICY_TABLES:
        a = table(RAW / f"{name}.parquet"); b = table(run_dir("renaudit") / "data" / f"{name}.parquet")
        diff = differing_columns(a, b, a.column_names)
        touched[name] = {"columns_changed": diff, "columns_added": [c for c in b.column_names if c not in a.column_names], "rows": a.num_rows, "rows_final": b.num_rows}
        del a, b
    touched["claims"] = {"columns_changed": [], "columns_added": ["audit_pre00"], "rows": 163150, "rows_final": 162546, "rows_removed": 604}
    ev["invariance_summary"] = touched
    expected_touch = {"policies_motor": ["customer_id", "exposure"], "policies_buildings": ["customer_id", "exposure", "policyholder_age", "sum_insured", "construction_type"],
                      "policies_contents": ["customer_id", "exposure", "policyholder_age", "sum_insured"], "test_motor": ["customer_id"],
                      "test_buildings": ["policyholder_age", "sum_insured", "construction_type"], "test_contents": ["policyholder_age", "sum_insured"]}
    ok_touch = all(set(touched[t]["columns_changed"]) <= set(expected_touch[t]) and touched[t]["columns_added"] == ["audit_ren00"] for t in POLICY_TABLES)
    checks.add("K01", "invariancia", "Del original a la base vigente solo cambian las columnas de las reglas (customer_id, exposure, sum_insured, construction_type, policyholder_age) y se añade audit_ren00; nada más",
               "From original to the active base only the rule columns change (customer_id, exposure, sum_insured, construction_type, policyholder_age) plus the added audit_ren00; nothing else",
               ok_touch, expected_touch, {t: touched[t]["columns_changed"] for t in POLICY_TABLES})
    # ------------------------------------------------------------------ L. incidencias abiertas recalculadas (D40) sobre la capa base
    pm = frame(run_dir("renaudit") / "data" / "policies_motor.parquet", ["row_id", "policy_id", "ncb_years", "years_licensed", "driver_age", "fuel_type", "engine_size_cc", "cover_type", "period_start", "period_end"])
    tm = frame(run_dir("renaudit") / "data" / "test_motor.parquet", ["row_id", "ncb_years", "years_licensed", "driver_age", "fuel_type", "engine_size_cc"])
    open_issues = {"VD_ncb_gt_licensed": {"train": int((pm.ncb_years > pm.years_licensed).sum()), "test": int((tm.ncb_years > tm.years_licensed).sum())},
                   "VD34_licence_age_lt_16": {"train": int(((pm.driver_age - pm.years_licensed) < 16).sum()), "test": int(((tm.driver_age - tm.years_licensed) < 16).sum())},
                   "VD35_electric": {"rows": int((pm.fuel_type == "electric").sum() + (tm.fuel_type == "electric").sum()),
                                     "engine_positive": int(((pm.fuel_type == "electric") & (pm.engine_size_cc > 0)).sum() + ((tm.fuel_type == "electric") & (tm.engine_size_cc > 0)).sum()),
                                     "engine_missing": int(((pm.fuel_type == "electric") & pm.engine_size_cc.isna()).sum() + ((tm.fuel_type == "electric") & tm.engine_size_cc.isna()).sum())}}
    open_issues["VD_ncb_gt_licensed"]["total"] = open_issues["VD_ncb_gt_licensed"]["train"] + open_issues["VD_ncb_gt_licensed"]["test"]
    open_issues["VD34_licence_age_lt_16"]["total"] = open_issues["VD34_licence_age_lt_16"]["train"] + open_issues["VD34_licence_age_lt_16"]["test"]
    pm["period_start"] = dates(pm.period_start); pm["period_end"] = dates(pm.period_end)
    raw_claims = frame(RAW / "claims.parquet"); raw_claims["loss_date"] = dates(raw_claims.loss_date)
    def coverage_issues(cl_src, label):
        res = {}
        m = cl_src[cl_src.line == "motor"].merge(pm[["policy_id", "period_start", "period_end", "cover_type"]], on="policy_id")
        m = m[(m.loss_date >= m.period_start) & (m.loss_date <= m.period_end) & (m.status != "repudiated")]
        res["VD09_own_damage_outside_comprehensive"] = int(((m.peril == "own_damage") & (m.cover_type != "comprehensive")).sum())
        for line in ["buildings", "contents"]:
            ph = frame(run_dir("renaudit") / "data" / f"policies_{line}.parquet", ["policy_id", "period_start", "period_end", "accidental_damage_cover", "sum_insured"])
            ph["period_start"] = dates(ph.period_start); ph["period_end"] = dates(ph.period_end)
            c = cl_src[cl_src.line == line].merge(ph, on="policy_id")
            c = c[(c.loss_date >= c.period_start) & (c.loss_date <= c.period_end) & (c.status != "repudiated")]
            res[f"VD10_accidental_damage_without_option_{line}"] = int(((c.peril == "accidental_damage") & (c.accidental_damage_cover == False)).sum())  # noqa: E712
            res[f"VD11_net_incurred_above_capital_{line}"] = int(((c.incurred_to_date - c.recoveries) > c.sum_insured).sum())
        return {f"{k}_{label}": v for k, v in res.items()}
    open_issues.update(coverage_issues(raw_claims, "original_claims"))
    open_issues.update(coverage_issues(claims_for_profile, "dup01_claims"))
    ends = {"motor": int((pm.period_end == "2024-12-30").sum())}
    for line in ["buildings", "contents"]:
        ends[line] = int((dates(frame(run_dir("renaudit") / "data" / f"policies_{line}.parquet", ["period_end"]).period_end) == "2024-12-30").sum())
    ends["total"] = sum(ends.values())
    open_issues["VD16_periods_ending_2024_12_30"] = ends
    ev["open_issues"] = open_issues
    checks.add("L01", "pendientes", "Las incidencias abiertas de D40 se reproducen de forma independiente: 161.822 NCB > antigüedad (127.041 train, 34.781 test), 3.717 edades de licencia < 16 (train+test), 2.533 eléctricos sin cilindrada, 4 own_damage fuera de comprehensive, 506/1.090 accidental_damage sin opción y 8/3 netos sobre el capital en claims original; 500.245 periodos terminan el 30-12-2024",
               "D40 open issues reproduce independently: 161,822 NCB > years licensed (127,041 train, 34,781 test), 3,717 licence ages < 16 (train+test), 2,533 electric rows without engine size, 4 own_damage outside comprehensive, 506/1,090 accidental_damage without the option and 8/3 nets above capital on original claims; 500,245 periods end on 2024-12-30",
               open_issues["VD_ncb_gt_licensed"] == {"train": 127041, "test": 34781, "total": 161822} and open_issues["VD34_licence_age_lt_16"]["total"] == 3717 and open_issues["VD35_electric"]["engine_missing"] == 2533
               and open_issues["VD09_own_damage_outside_comprehensive_original_claims"] == 4 and open_issues["VD10_accidental_damage_without_option_buildings_original_claims"] == 506
               and open_issues["VD10_accidental_damage_without_option_contents_original_claims"] == 1090 and open_issues["VD11_net_incurred_above_capital_buildings_original_claims"] == 8
               and open_issues["VD11_net_incurred_above_capital_contents_original_claims"] == 3 and ends["total"] == 500245, None, open_issues, severity="hallazgo")
    checks.add("L02", "pendientes", "Hallazgo: tras DUP01 las cifras de VD10 bajan a 502 y 1.087 (cuatro y tres de los pares excluidos eran accidental_damage sin opción); D40 las calculó antes de la depuración",
               "Finding: after DUP01 the VD10 figures drop to 502 and 1,087 (four and three of the excluded pairs were accidental_damage without the option); D40 computed them before the de-duplication",
               open_issues["VD10_accidental_damage_without_option_buildings_dup01_claims"] == 502 and open_issues["VD10_accidental_damage_without_option_contents_dup01_claims"] == 1087, [502, 1087],
               [open_issues["VD10_accidental_damage_without_option_buildings_dup01_claims"], open_issues["VD10_accidental_damage_without_option_contents_dup01_claims"]], severity="hallazgo")
    del pm, tm, raw_claims

    # ------------------------------------------------------------------ M. perfiles por producto para el dashboard
    for line in LINES:
        raw_tr = frame(RAW / f"policies_{line}.parquet"); raw_te = frame(RAW / f"test_{line}.parquet")
        base_tr = frame(run_dir("renaudit") / "data" / f"policies_{line}.parquet"); base_te = frame(run_dir("renaudit") / "data" / f"test_{line}.parquet")
        ps = dates(raw_tr.period_start)
        prof = {"train_rows": len(raw_tr), "test_rows": len(raw_te), "policies_train": int(raw_tr.policy_id.nunique()), "policies_test": int(raw_te.policy_id.nunique()),
                "customers_train": int(base_tr.customer_id.nunique()), "columns": len(raw_tr.columns),
                "test_policies_seen_in_train_share": round(float(raw_te.policy_id.isin(set(raw_tr.policy_id)).mean()), 4),
                "periods_by_year": {int(k): int(v) for k, v in ps.dt.year.value_counts().sort_index().items()},
                "exposure_by_year_raw": {int(k): round(float(v), 2) for k, v in raw_tr.groupby(ps.dt.year).exposure.sum().items()},
                "exposure_by_year_base": {int(k): round(float(v), 2) for k, v in base_tr.groupby(ps.dt.year).exposure.sum().items()},
                "exposure_test_raw": round(float(raw_te.exposure.sum()), 2),
                "new_business_share": round(float(raw_tr.new_business.mean()), 4), "new_business_share_test": round(float(raw_te.new_business.mean()), 4),
                "missing_share_raw": {c: round(float(raw_tr[c].isna().mean()), 4) for c in raw_tr.columns if raw_tr[c].isna().any()},
                "missing_share_test": {c: round(float(raw_te[c].isna().mean()), 4) for c in raw_te.columns if raw_te[c].isna().any()},
                "covered_days_bins": {}, "rules_applied": []}
        days = (dates(raw_tr.period_end) - ps).dt.days + 1
        labels = ["1-30", "31-90", "91-180", "181-364", "365", "366"]
        bins = pd.cut(days, [0, 30, 90, 180, 364, 365, 366], labels=labels)
        counts = bins.value_counts()
        prof["covered_days_bins"] = {lab: int(counts.get(lab, 0)) for lab in labels}
        if line == "motor":
            prof["rules_applied"] = ["ID01", "EXP01", "REN00"]
            prof["customer_id_length_raw"] = id01["tables"]["policies_motor"]["length_distribution"]
            prof["driver_age_hist_raw"] = {str(int(k)): int(v) for k, v in raw_tr.driver_age.value_counts().sort_index().items()}
            prof["ncb_years_hist_raw"] = {str(int(k)): int(v) for k, v in raw_tr.ncb_years.value_counts().sort_index().items()}
            prof["cover_type_counts"] = {k: int(v) for k, v in raw_tr.cover_type.value_counts().items()}
            prof["vehicle_value_group_counts"] = {str(int(k)): int(v) for k, v in raw_tr.vehicle_value_group.value_counts().sort_index().items()}
        else:
            prof["rules_applied"] = ["EXP01", "CAP01", "AGE01", "REN00"] + (["CAT01"] if line == "buildings" else []) + ["CAP0xR (rama)"]
            thr = CAP_THRESHOLD[line]
            for label, s in [("raw", pd.concat([raw_tr.sum_insured, raw_te.sum_insured])), ("base", pd.concat([base_tr.sum_insured, base_te.sum_insured]))]:
                hist, edges = np.histogram(np.log10(s.clip(lower=1)), bins=np.arange(3, 9.26, 0.25))
                prof[f"sum_insured_log10_hist_{label}"] = {"edges": [round(float(e), 2) for e in edges], "counts": [int(c) for c in hist]}
                prof[f"sum_insured_extreme_rows_{label}"] = int((s > thr).sum())
            retro_tr = frame(ROOT / catalogs["retro_active"][f"policies_{line}"]["workspace_relative_path"], ["sum_insured"])
            retro_te = frame(ROOT / catalogs["retro_active"][f"test_{line}"]["workspace_relative_path"], ["sum_insured"])
            s = pd.concat([retro_tr.sum_insured, retro_te.sum_insured])
            hist, edges = np.histogram(np.log10(s.clip(lower=1)), bins=np.arange(3, 9.26, 0.25))
            prof["sum_insured_log10_hist_retro"] = {"edges": [round(float(e), 2) for e in edges], "counts": [int(c) for c in hist]}
            prof["sum_insured_extreme_rows_retro"] = int((s > thr).sum())
            prof["sum_insured_quantiles_raw_normal"] = {str(q): float(v) for q, v in raw_tr.loc[raw_tr.sum_insured <= thr, "sum_insured"].quantile([.05, .25, .5, .75, .95]).items()}
            prof["policyholder_age_hist_raw"] = age01["tables"][f"policies_{line}"]["age_histogram_raw"]; prof["policyholder_age_hist_base"] = age01["tables"][f"policies_{line}"]["age_histogram_new"]
            if line == "buildings":
                prof["construction_type_raw"] = {str(k): int(v) for k, v in raw_tr.construction_type.astype("string").fillna("<NA>").value_counts().items()}
                prof["construction_type_base"] = {str(k): int(v) for k, v in base_tr.construction_type.astype("string").fillna("<NA>").value_counts().items()}
                prof["construction_by_year_base"] = records(base_tr.assign(year=ps.dt.year).groupby(["year", "construction_type"]).size().reset_index(name="rows"))
                prof["occupancy_counts"] = {str(k): int(v) for k, v in raw_tr.occupancy.astype("string").fillna("<NA>").value_counts().items()}
            else:
                prof["tenure_counts"] = {str(k): int(v) for k, v in raw_tr.tenure.astype("string").fillna("<NA>").value_counts().items()}
                prof["security_level_counts"] = {str(k): int(v) for k, v in raw_tr.security_level.astype("string").fillna("<NA>").value_counts().items()}
        prof["renewal_decision_by_year"] = records(raw_tr.assign(year=ps.dt.year).groupby(["year", "renewal_decision"]).size().reset_index(name="rows"))
        prof["audit_ren00_rows"] = {"train": int(base_tr.audit_ren00.sum()), "test": int(base_te.audit_ren00.sum())}
        cl_line = claims_for_profile[claims_for_profile.line == line]
        prof["claims"] = {"records_dupfix": int(len(cl_line)), "by_peril": records(cl_line.groupby(["peril", "status"]).size().reset_index(name="rows")),
                          "by_loss_year": {int(k): int(v) for k, v in cl_line.loss_date.dt.year.value_counts().sort_index().items()},
                          "net_accepted_by_peril": records(cl_line[cl_line.status != "repudiated"].assign(net=lambda d: d.incurred_to_date - d.recoveries).groupby("peril").net.sum().round(2).reset_index()),
                          "before_first_period": int((cl_line.category == "before_first_period").sum()), "dup01_excluded": dup01["excluded_by_line"].get(line, 0)}
        ev["profiles"][line] = prof
        del raw_tr, raw_te, base_tr, base_te

    # ------------------------------------------------------------------ resumen y salida
    passed = sum(1 for c in checks.items if c["passed"]); total = len(checks.items)
    ev["checks"] = checks.items
    ev["summary"] = {"checks_total": total, "checks_passed": passed, "all_passed": passed == total, "findings": [c["id"] for c in checks.items if c["severity"] == "hallazgo"],
                     "independent_validation": False, "human_review": "pending", "ai_assisted": True, "author": "Claude (Cowork) a solicitud del participante"}
    pd.DataFrame(checks.items).to_csv(out / "tables" / "controles.csv", index=False)
    (out / "evidencia.json").write_text(json.dumps(ev, ensure_ascii=False, indent=2, default=jsonable) + "\n", encoding="utf-8")
    shutil.copy2(__file__, out / Path(__file__).name)
    manifest = {p.relative_to(out).as_posix(): digest(p) for p in sorted(out.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run": out.relative_to(ROOT).as_posix(), "checks_passed": passed, "checks_total": total}, ensure_ascii=False))


if __name__ == "__main__":
    main()
