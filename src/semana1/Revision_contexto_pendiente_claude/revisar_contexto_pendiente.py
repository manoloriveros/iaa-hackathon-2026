"""Revisión de los capitales pendientes con contexto incompleto (grupo F de D48 tras CAP05R, sin las dos pólizas de D60).

Recalcula desde los Parquet originales, con código propio, la historia completa de cada póliza, todas sus referencias
originales, los puentes de cada campo ausente y una escalera de criterios (del más estricto al más laxo), y deja una
lista congelada de candidatas SIN APLICAR. No modifica datos, índices ni corridas de Codex; no entrena modelos.

Uso (desde la raíz del proyecto, con el Python de Preparación/.venv):
    python "Hackaton/Semana 1/Revision_contexto_pendiente_claude/revisar_contexto_pendiente.py"
Crea runs/ctx_<marca>_<id>/ con evidencia.json, tablas CSV, copia del script y manifest.json (SHA-256).
"""
from __future__ import annotations

import hashlib
import json
import platform
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "RUTAS_PROYECTO.json").is_file():
            return candidate
    raise FileNotFoundError("No se encontró RUTAS_PROYECTO.json hacia arriba.")


ROOT = find_root(HERE)
sys.path.insert(0, str(ROOT / "Preparación/.cache/parquet-reader"))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

RAW = ROOT / "Hackaton/Semana 1/Datos"
LIMP = ROOT / "Hackaton/Semana 1/Limpieza"
D56 = ROOT / "Hackaton/Semana 1/Revision_contexto_incompleto/runs/incomplete_20261016T230501Z_37407a29"
D57 = ROOT / "Hackaton/Semana 1/Revision_referencias_distantes/runs/distant_20261017T001932Z_e9a0e58f"
FIELDS = {
    "buildings": ["customer_id", "address_id", "construction_type", "occupancy", "accidental_damage_cover",
                  "voluntary_excess", "compulsory_excess", "smoke_alarms", "mortgage"],
    "contents": ["customer_id", "address_id", "tenure", "security_level", "high_value_items", "accidental_damage_cover",
                 "works_from_home", "lodgers", "bicycle_cover", "voluntary_excess", "compulsory_excess"],
}
NULLABLE = {"buildings": ["smoke_alarms"], "contents": ["security_level", "high_value_items"]}
THR = {"buildings": 10_000_000, "contents": 1_000_000}
BAND = (0.9, 1.1)
WINDOW = (1, 400)
KEEP = ["row_id", "policy_id", "customer_id", "address_id", "period_start", "period_end", "exposure", "sum_insured",
        "written_premium", "renewal_decision", "renewal_count", "new_business", "discount_applied"]
EXTRA = sorted({c for line in FIELDS for c in FIELDS[line]} - set(KEEP))


# ----------------------------------------------------------------------------- utilidades
def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def norm(value, col):
    if col == "construction_type":
        return str(value).strip().casefold()
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.floating, float)):
        return float(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    return value


def to_date(frame: pd.DataFrame, cols=("period_start", "period_end")) -> pd.DataFrame:
    for col in cols:
        frame[col] = pd.to_datetime(frame[col])
    return frame


def jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if pd.isna(obj) else float(obj)
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.strftime("%Y-%m-%d")
    if obj is pd.NaT:
        return None
    return obj


class Checks:
    def __init__(self):
        self.rows = []

    def add(self, cid, name, passed, expected=None, observed=None, detail=None):
        self.rows.append({"id": cid, "name": name, "passed": bool(passed), "expected": jsonable(expected),
                          "observed": jsonable(observed), "detail": detail})
        print(f"[{'OK' if passed else 'FALLA'}] {cid} {name}: {jsonable(observed)}")


# ----------------------------------------------------------------------------- carga
def load_inputs():
    retro_idx = json.loads((LIMP / "current_retrospective_dataset.json").read_text("utf-8"))
    retro_run = ROOT / retro_idx["workspace_relative_run"]
    retro_cat = json.loads((ROOT / retro_idx["catalog_workspace_relative"]).read_text("utf-8"))
    base_idx = json.loads((LIMP / "current_dataset.json").read_text("utf-8"))
    base_run = ROOT / base_idx["workspace_relative_run"]
    base_cat = json.loads((base_run / "dataset_catalog.json").read_text("utf-8"))
    pending = pd.read_parquet(retro_run / "tables/pending_capitals.parquet")
    ledger = pd.read_parquet(retro_run / "ledger/cumulative_retrospective_changes.parquet")
    held = pd.read_csv(D57 / "tables/held_numeric_conflicts.csv", dtype=str)
    cohort202 = pd.read_csv(D56 / "tables/frozen_202_cohort.csv", dtype=str)
    assessment56 = pd.read_csv(D56 / "tables/incomplete_assessment.csv", dtype=str)
    bridges56 = pd.read_csv(D56 / "tables/missing_field_bridges.csv", dtype=str)
    return dict(retro_idx=retro_idx, retro_run=retro_run, retro_cat=retro_cat, base_idx=base_idx, base_run=base_run,
                base_cat=base_cat, pending=pending, ledger=ledger, held=held, cohort202=cohort202,
                assessment56=assessment56, bridges56=bridges56)


def read_line_tables(pols: list[str], base_cat: dict, retro_cat: dict) -> pd.DataFrame:
    parts = []
    for line in ["buildings", "contents"]:
        for prefix in ["policies", "test"]:
            name = f"{prefix}_{line}"
            raw = pq.read_table(RAW / f"{name}.parquet", filters=[("policy_id", "in", pols)]).to_pandas()
            raw["source_table"] = name
            raw["line"] = line
            base = pq.read_table(ROOT / base_cat[name]["workspace_relative_path"], columns=["row_id", "sum_insured"],
                                 filters=[("policy_id", "in", pols)]).to_pandas().set_index("row_id").sum_insured
            branch = pq.read_table(ROOT / retro_cat[name]["workspace_relative_path"], columns=["row_id", "sum_insured"],
                                   filters=[("policy_id", "in", pols)]).to_pandas().set_index("row_id").sum_insured
            raw["base_capital"] = raw.row_id.map(base)
            raw["branch_capital"] = raw.row_id.map(branch)
            parts.append(raw)
    hist = pd.concat(parts, ignore_index=True)
    hist = to_date(hist).sort_values(["policy_id", "period_start", "row_id"]).reset_index(drop=True)
    hist["year"] = hist.period_start.dt.year
    hist["covered_days"] = (hist.period_end - hist.period_start).dt.days + 1
    hist["extreme"] = [cap > THR[line] for cap, line in zip(hist.sum_insured, hist.line)]
    hist["test2025"] = hist.source_table.str.startswith("test_")
    return hist


# ----------------------------------------------------------------------------- estadísticas globales
def global_field_statistics(checks: Checks) -> dict:
    out = {}
    for line in ["buildings", "contents"]:
        parts = []
        for prefix in ["policies", "test"]:
            t = pq.read_table(RAW / f"{prefix}_{line}.parquet").to_pandas()
            t["source_table"] = f"{prefix}_{line}"
            parts.append(t)
        df = to_date(pd.concat(parts, ignore_index=True))
        ext = df.sum_insured > THR[line]
        stats = {"rows": int(len(df)), "extreme_rows": int(ext.sum()), "extreme_share": float(ext.mean()), "fields": {}}
        for col in FIELDS[line]:
            miss = df[col].isna()
            stats["fields"][col] = {"null_rows": int(miss.sum()), "null_share": float(miss.mean()),
                                    "null_rows_extreme": int(miss[ext].sum()), "null_share_extreme": float(miss[ext].mean())}
        d = df.loc[~ext & (df.sum_insured > 0)].sort_values(["policy_id", "period_start", "row_id"])
        g = d.groupby("policy_id", sort=False)
        prev = g.shift(1)
        same_policy = g.cumcount() > 0
        same_addr = same_policy & (d.address_id == prev.address_id)
        moved = same_policy & (d.address_id != prev.address_id)
        ratio = d.sum_insured / prev.sum_insured
        stats["consecutive_normal_pairs"] = int(same_policy.sum())
        stats["consecutive_pairs_same_address"] = int(same_addr.sum())
        stats["consecutive_pairs_address_change"] = int(moved.sum())
        stats["ratio_consecutive_same_address_quantiles"] = {str(q): float(v) for q, v in ratio[same_addr].quantile([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).items()}
        stats["ratio_consecutive_same_address_in_band"] = float(ratio[same_addr].between(*BAND).mean())
        stats["ratio_consecutive_address_change_in_band"] = float(ratio[moved].between(*BAND).mean()) if moved.any() else None
        stats["ratio_consecutive_address_change_median"] = float(ratio[moved].median()) if moved.any() else None
        changes = {}
        for col in [c for c in FIELDS[line] if c not in ("customer_id", "address_id")]:
            both = same_policy & d[col].notna() & prev[col].notna()
            left = d.loc[both, col].map(lambda v: norm(v, col))
            right = prev.loc[both, col].map(lambda v: norm(v, col))
            chg = left != right
            both_same_addr = both & same_addr
            chg_same_addr = chg & same_addr.loc[chg.index]
            changes[col] = {"pairs_both_known": int(both.sum()), "changes": int(chg.sum()),
                            "pairs_both_known_same_address": int(both_same_addr.sum()),
                            "changes_same_address": int(chg_same_addr.sum()),
                            "changes_with_address_change": int((chg & moved.loc[chg.index]).sum())}
        stats["field_changes_between_consecutive_periods"] = changes
        for col in NULLABLE[line]:
            c = changes[col]
            checks.add(f"G_{line}_{col}", f"{col} nunca cambia entre periodos consecutivos de la misma póliza en la misma dirección ({line})",
                       c["changes_same_address"] == 0 and c["pairs_both_known_same_address"] > 100_000,
                       expected=0, observed={"cambios_misma_direccion": c["changes_same_address"], "pares": c["pairs_both_known_same_address"]})
        out[line] = stats
    return out


# ----------------------------------------------------------------------------- referencias y puentes
def build_references(hist: pd.DataFrame, focus_ids: set[str]) -> pd.DataFrame:
    rows = []
    for _, cur in hist[hist.row_id.isin(focus_ids)].iterrows():
        grp = hist[hist.policy_id.eq(cur.policy_id) & hist.row_id.ne(cur.row_id)]
        own_missing = [c for c in FIELDS[cur.line] if pd.isna(cur[c])]
        for _, ref in grp.iterrows():
            normal = bool(0 < ref.sum_insured <= THR[cur.line])
            missing, changed = [], []
            for col in FIELDS[cur.line]:
                if pd.isna(cur[col]) or pd.isna(ref[col]):
                    missing.append(col)
                    continue
                if norm(cur[col], col) != norm(ref[col], col):
                    changed.append(col)
            direction = "prior" if ref.period_start < cur.period_start else "later"
            gap = int(abs((cur.period_start - ref.period_start).days))
            nonoverlap = bool(ref.period_end < cur.period_start) if direction == "prior" else bool(cur.period_end < ref.period_start)
            ratio = float((cur.sum_insured / 1000) / ref.sum_insured) if ref.sum_insured > 0 else np.nan
            prem_cur = cur.written_premium / cur.exposure if cur.exposure else np.nan
            prem_ref = ref.written_premium / ref.exposure if ref.exposure else np.nan
            rows.append({
                "focus_row_id": cur.row_id, "policy_id": cur.policy_id, "line": cur.line, "focus_source_table": cur.source_table,
                "focus_period_start": cur.period_start, "focus_capital_CU": float(cur.sum_insured), "hypothetical_CU": float(cur.sum_insured / 1000),
                "focus_missing_fields": "|".join(own_missing), "reference_row_id": ref.row_id, "reference_source_table": ref.source_table,
                "reference_period_start": ref.period_start, "reference_period_end": ref.period_end, "reference_covered_days": int(ref.covered_days),
                "reference_capital_CU": float(ref.sum_insured), "reference_normal": normal, "reference_test2025": bool(ref.test2025),
                "direction": direction, "start_gap_days": gap, "nonoverlap": nonoverlap, "ratio_hypothetical_over_reference": ratio,
                "in_band": bool(BAND[0] <= ratio <= BAND[1]) if not np.isnan(ratio) else False,
                "in_window": bool(WINDOW[0] <= gap <= WINDOW[1]) and nonoverlap,
                "known_fields_equal": not changed, "changed_fields": "|".join(changed), "unknown_fields": "|".join(missing),
                "reference_missing_fields": "|".join(c for c in FIELDS[cur.line] if pd.isna(ref[c])),
                "same_address": bool(cur.address_id == ref.address_id),
                "premium_annualised_ratio_focus_over_reference": float(prem_cur / prem_ref) if prem_ref else np.nan,
            })
    refs = pd.DataFrame(rows)
    refs["compatible_known_context"] = refs.reference_normal & refs.known_fields_equal & refs.in_band & refs.in_window
    refs["complete_equal_context"] = refs.known_fields_equal & refs.unknown_fields.eq("")
    refs["strict_D34"] = refs.compatible_known_context & refs.complete_equal_context
    refs["contradiction_known_context"] = refs.reference_normal & refs.known_fields_equal & refs.in_window & ~refs.in_band
    refs["nearest_normal_in_direction"] = False
    for (_, _), g in refs[refs.reference_normal].groupby(["focus_row_id", "direction"]):
        refs.loc[g.start_gap_days.idxmin(), "nearest_normal_in_direction"] = True
    return refs


def build_bridges(hist: pd.DataFrame, focus_ids: set[str]) -> pd.DataFrame:
    """Para cada campo nulo de una fila pendiente: valores conocidos antes y después en la misma dirección."""
    rows = []
    for _, cur in hist[hist.row_id.isin(focus_ids)].iterrows():
        grp = hist[hist.policy_id.eq(cur.policy_id) & hist.row_id.ne(cur.row_id) & hist.address_id.eq(cur.address_id)]
        for field in [c for c in FIELDS[cur.line] if pd.isna(cur[c])]:
            before = grp[grp.period_start.lt(cur.period_start) & grp[field].notna()].sort_values("period_start")
            after = grp[grp.period_start.gt(cur.period_start) & grp[field].notna()].sort_values("period_start")
            prev = before.iloc[-1] if len(before) else None
            nxt = after.iloc[0] if len(after) else None
            known_values = sorted({str(norm(v, field)) for v in grp[field].dropna()})
            if prev is not None and nxt is not None:
                status = "AMBOS_LADOS_IGUALES" if norm(prev[field], field) == norm(nxt[field], field) else "AMBOS_LADOS_DISTINTOS"
            elif prev is not None:
                status = "SOLO_ANTERIOR_CONOCIDO"
            elif nxt is not None:
                status = "SOLO_POSTERIOR_CONOCIDO"
            else:
                status = "SIN_VECINO_CONOCIDO"
            rows.append({"focus_row_id": cur.row_id, "policy_id": cur.policy_id, "line": cur.line, "field": field, "bridge_status": status,
                         "prior_row_id": prev.row_id if prev is not None else None, "prior_value": str(norm(prev[field], field)) if prev is not None else None,
                         "prior_gap_days": int((cur.period_start - prev.period_start).days) if prev is not None else None,
                         "later_row_id": nxt.row_id if nxt is not None else None, "later_value": str(norm(nxt[field], field)) if nxt is not None else None,
                         "later_gap_days": int((nxt.period_start - cur.period_start).days) if nxt is not None else None,
                         "distinct_known_values_same_address": "|".join(known_values), "n_known_same_address": int(grp[field].notna().sum())})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- siniestros y pólizas vecinas
def claims_for(hist: pd.DataFrame, base_cat: dict) -> pd.DataFrame:
    claims = pq.read_table(ROOT / base_cat["claims"]["workspace_relative_path"],
                           filters=[("policy_id", "in", hist.policy_id.unique().tolist())]).to_pandas()
    claims["loss_date"] = pd.to_datetime(claims.loss_date)
    claims["report_date"] = pd.to_datetime(claims.report_date)
    periods = hist[["row_id", "policy_id", "line", "period_start", "period_end", "sum_insured", "extreme"]]
    merged = claims.merge(periods, on=["policy_id", "line"], how="left")
    inside = merged[(merged.loss_date >= merged.period_start) & (merged.loss_date <= merged.period_end)]
    assigned = inside.groupby("claim_id").row_id.agg(["nunique", "first"])
    claims["assigned_row_id"] = claims.claim_id.map(assigned["first"])
    claims["assignment_count"] = claims.claim_id.map(assigned["nunique"]).fillna(0).astype(int)
    claims["accepted"] = claims.status.ne("repudiated")
    claims["net_incurred_CU"] = claims.incurred_to_date - claims.recoveries
    cap = hist.set_index("row_id")
    claims["period_capital_CU"] = claims.assigned_row_id.map(cap.sum_insured)
    claims["period_extreme"] = claims.assigned_row_id.map(cap.extreme).fillna(False).astype(bool)
    claims["incurred_above_hypothetical_capital"] = claims.period_extreme & claims.accepted & (claims.incurred_to_date > claims.period_capital_CU / 1000)
    return claims


def neighbour_policies(hist: pd.DataFrame, focus: pd.DataFrame) -> pd.DataFrame:
    """Otras pólizas de hogar (otro ramo) del mismo cliente y dirección que solapan el periodo pendiente: solo descripción."""
    rows = []
    customers = focus.customer_id.unique().tolist()
    others = []
    for line in ["buildings", "contents"]:
        for prefix in ["policies", "test"]:
            name = f"{prefix}_{line}"
            t = pq.read_table(RAW / f"{name}.parquet", columns=["row_id", "policy_id", "customer_id", "address_id", "period_start", "period_end", "sum_insured"],
                              filters=[("customer_id", "in", customers)]).to_pandas()
            t["source_table"] = name
            t["line"] = line
            others.append(t)
    others = to_date(pd.concat(others, ignore_index=True))
    for _, cur in focus.iterrows():
        o = others[others.customer_id.eq(cur.customer_id) & others.address_id.eq(cur.address_id) & others.line.ne(cur.line)
                   & (others.period_start <= cur.period_end) & (others.period_end >= cur.period_start)]
        for _, r in o.iterrows():
            rows.append({"focus_row_id": cur.row_id, "policy_id": cur.policy_id, "line": cur.line, "hypothetical_CU": float(cur.sum_insured / 1000),
                         "other_policy_id": r.policy_id, "other_line": r.line, "other_row_id": r.row_id, "other_source_table": r.source_table,
                         "other_period_start": r.period_start, "other_capital_CU": float(r.sum_insured),
                         "other_extreme": bool(r.sum_insured > THR[r.line])})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- escalera
def evaluate_ladder(focus: pd.DataFrame, refs: pd.DataFrame, bridges: pd.DataFrame, claims: pd.DataFrame) -> pd.DataFrame:
    rows = []
    claims_bad = set(claims.loc[claims.incurred_above_hypothetical_capital, "assigned_row_id"].dropna())
    for _, cur in focus.iterrows():
        r = refs[refs.focus_row_id.eq(cur.row_id)]
        near = r[r.nearest_normal_in_direction]
        own_missing = [c for c in cur.own_missing_fields.split("|") if c] if isinstance(cur.own_missing_fields, str) else []
        b = bridges[bridges.focus_row_id.eq(cur.row_id)]
        statuses = set(b.bridge_status)
        compat = near[near.compatible_known_context]
        prior_ok = bool((compat.direction == "prior").any())
        later_ok = bool((compat.direction == "later").any())
        # referencia elegida: la compatible más próxima; anterior preferida cuando ambas existen
        chosen = None
        if len(compat):
            compat_sorted = compat.sort_values(["direction", "start_gap_days"], ascending=[False, True])  # 'prior' > 'later' alfabéticamente invertido
            chosen = compat_sorted.iloc[0]
        contradiction = bool(r.contradiction_known_context.any())
        nearer_contradiction = False
        if chosen is not None:
            nearer_contradiction = bool(r[r.contradiction_known_context & (r.start_gap_days < chosen.start_gap_days)].shape[0])
        ref_missing = [c for c in str(chosen.reference_missing_fields).split("|") if c] if chosen is not None and isinstance(chosen.reference_missing_fields, str) else []
        level = "N0_D34_estricto" if bool(near.strict_D34.any()) else None
        if level is None and chosen is not None:
            if own_missing:
                if statuses == {"AMBOS_LADOS_IGUALES"}:
                    level = "N1_puente_dos_lados"
                elif statuses <= {"AMBOS_LADOS_IGUALES", "SOLO_ANTERIOR_CONOCIDO", "SOLO_POSTERIOR_CONOCIDO"}:
                    level = "N2_vecino_conocido"
                else:
                    level = "N3_identidad_sin_campo"
            else:
                level = "N2_vecino_conocido" if cur.reference_missing_consistent else "N3_identidad_sin_campo"
        holds = []
        if contradiction:
            holds.append("referencia_contradictoria_en_la_poliza")
        if "AMBOS_LADOS_DISTINTOS" in statuses:
            holds.append("campo_ausente_con_vecinos_distintos")
        if cur.row_id in claims_bad:
            holds.append("siniestro_por_encima_del_capital_hipotetico")
        if chosen is None:
            holds.append("sin_referencia_compatible")
        rows.append({
            "row_id": cur.row_id, "policy_id": cur.policy_id, "line": cur.line, "source_table": cur.source_table, "year": int(cur.year),
            "period_start": cur.period_start, "period_end": cur.period_end, "original_capital_CU": float(cur.sum_insured),
            "hypothetical_CU": float(cur.sum_insured / 1000), "tier": "C_fila_incompleta" if own_missing else "B_referencias_incompletas",
            "own_missing_fields": "|".join(own_missing), "bridge_statuses": "|".join(sorted(statuses)),
            "n_normal_references": int(r.reference_normal.sum()), "n_nearest_compatible": int(len(compat)),
            "prior_compatible": prior_ok, "later_compatible": later_ok, "both_directions_compatible": prior_ok and later_ok,
            "chosen_reference_row_id": chosen.reference_row_id if chosen is not None else None,
            "chosen_reference_source_table": chosen.reference_source_table if chosen is not None else None,
            "chosen_direction": chosen.direction if chosen is not None else None,
            "chosen_gap_days": int(chosen.start_gap_days) if chosen is not None else None,
            "chosen_reference_capital_CU": float(chosen.reference_capital_CU) if chosen is not None else None,
            "chosen_ratio": float(chosen.ratio_hypothetical_over_reference) if chosen is not None else None,
            "chosen_reference_test2025": bool(chosen.reference_test2025) if chosen is not None else None,
            "chosen_reference_missing_fields": "|".join(ref_missing),
            "reference_missing_consistent_with_focus": cur.reference_missing_consistent,
            "any_reference_with_changed_fields": bool((~r.known_fields_equal & r.reference_normal).any()),
            "changed_fields_in_other_references": "|".join(sorted({f for s in r.loc[~r.known_fields_equal, "changed_fields"] for f in s.split("|") if f})),
            "contradiction_in_policy": contradiction, "contradiction_nearer_than_chosen": nearer_contradiction,
            "level": level, "holds": "|".join(holds), "candidate_NOT_APPLIED": chosen is not None and not holds,
            "test2025_row": bool(cur.test2025),
        })
    return pd.DataFrame(rows)


def reference_missing_consistency(hist: pd.DataFrame, focus: pd.DataFrame, refs: pd.DataFrame) -> pd.Series:
    """Filas completas (tier B): ¿los valores conocidos de la póliza (misma dirección) coinciden con el valor de la fila pendiente
    en los campos que faltan en sus referencias? True si todos los conocidos coinciden; None si no hay referencia incompleta."""
    out = {}
    for _, cur in focus.iterrows():
        own_missing = [c for c in FIELDS[cur.line] if pd.isna(cur[c])]
        if own_missing:
            out[cur.row_id] = None
            continue
        r = refs[refs.focus_row_id.eq(cur.row_id) & refs.reference_normal]
        fields = sorted({f for s in r.reference_missing_fields.fillna("") for f in s.split("|") if f})
        if not fields:
            out[cur.row_id] = None
            continue
        grp = hist[hist.policy_id.eq(cur.policy_id) & hist.row_id.ne(cur.row_id) & hist.address_id.eq(cur.address_id)]
        ok = True
        for field in fields:
            known = {norm(v, field) for v in grp[field].dropna()}
            if not known or known != {norm(cur[field], field)}:
                ok = False  # sin otro periodo que informe el campo, o con un valor distinto, no hay vecino conocido
        out[cur.row_id] = ok
    return pd.Series(out)


# ----------------------------------------------------------------------------- casos
def pick_cases(ladder: pd.DataFrame, bridges: pd.DataFrame, hist: pd.DataFrame, claims: pd.DataFrame) -> list[dict]:
    chosen, used = [], set()

    def take(mask, key, title, why):
        sub = ladder[mask & ~ladder.row_id.isin(used)]
        if len(sub):
            row = sub.sort_values("row_id").iloc[0]
            used.add(row.row_id)
            chosen.append({"key": key, "row_id": row.row_id, "policy_id": row.policy_id, "title": title, "why": why})

    moves = set(ladder.loc[ladder.changed_fields_in_other_references.str.contains("address_id", na=False), "row_id"])
    long_policies = set(hist.groupby("policy_id").size().loc[lambda s: s >= 6].index)
    short_focus = set(hist.loc[hist.focus & (hist.covered_days <= 31), "row_id"])
    claims_rows = set(claims.loc[claims.period_extreme & claims.accepted, "assigned_row_id"].dropna())
    two_fields = ladder.own_missing_fields.str.count(r"\|").gt(0)
    take(ladder.own_missing_fields.eq("smoke_alarms") & ladder.level.eq("N1_puente_dos_lados"), "C01", "smoke_alarms ausente, conocido e igual antes y después", "Caso típico del tier C en edificios: el campo falta solo en la fila extrema y vale lo mismo en los periodos vecinos de la misma dirección.")
    take(ladder.own_missing_fields.eq("security_level") & ladder.level.eq("N1_puente_dos_lados"), "C02", "security_level ausente con vecinos iguales", "Mismo patrón en contenidos; security_level nunca cambia dentro de una póliza en todo el archivo.")
    take(ladder.own_missing_fields.eq("high_value_items") & ladder.level.eq("N2_vecino_conocido") & ladder.chosen_direction.eq("prior"), "C03", "high_value_items ausente, solo vecinos anteriores", "Último periodo observado de la póliza: la referencia es anterior y el campo solo se conoce hacia atrás.")
    take(ladder.level.eq("N2_vecino_conocido") & ladder.chosen_direction.eq("later") & ~ladder.prior_compatible, "C04", "Primer periodo extremo con apoyo solo posterior", "Fila de 2021 o alta nueva: la única referencia está después del periodo, como en CAP02R.")
    take(two_fields, "C05", "Dos campos ausentes en la misma fila", "security_level y high_value_items faltan a la vez; los vecinos los conocen.")
    take(ladder.tier.eq("B_referencias_incompletas") & ladder.reference_missing_consistent_with_focus.eq(True), "C06", "Fila completa, referencia próxima incompleta", "Tier B: el nulo está en la referencia; el valor de la fila pendiente coincide con el resto de la póliza.")
    take(ladder.tier.eq("B_referencias_incompletas") & ladder.reference_missing_consistent_with_focus.ne(True), "C07", "Fila completa con referencia incompleta sin otros conocidos", "Tier B sin otros periodos que informen el campo ausente de la referencia.")
    take(ladder.test2025_row & ladder.candidate_NOT_APPLIED, "C08", "Fila de test 2025 con referencia anterior", "La corrección afectaría a una fila que hay que predecir; el apoyo es anterior y disponible al corte.")
    take(ladder.row_id.isin(moves) & ladder.candidate_NOT_APPLIED, "C09", "Historia con mudanza: la referencia válida es la de la misma dirección", "Otras referencias de la póliza cambian de dirección; solo cuentan las de la misma dirección.")
    take(ladder.contradiction_in_policy, "C10", "Referencia contradictoria por un tramo corto ampliado", "Un tramo breve con capital ampliado queda fuera de la banda; la referencia más próxima sí encaja. Se retiene para revisión manual.")
    take(ladder.holds.str.contains("campo_ausente_con_vecinos_distintos"), "C11", "Campo ausente con vecinos distintos", "Único caso en que los valores conocidos antes y después difieren; se retiene.")
    take(ladder.row_id.isin(claims_rows), "C12", "Periodo extremo con siniestro aceptado", "El coste incurrido se compara con el capital hipotético; ningún siniestro lo supera.")
    take(ladder.policy_id.isin(long_policies) & ladder.candidate_NOT_APPLIED, "C13", "Historia larga con un solo periodo extremo", "Seis o más periodos normales y uno solo fuera de escala.")
    take(ladder.row_id.isin(short_focus) & ladder.candidate_NOT_APPLIED, "C14", "Periodo extremo muy corto", "Un tramo de pocos días con capital fuera de escala entre periodos normales de la misma dirección.")
    cases = []
    for c in chosen:
        h = hist[hist.policy_id.eq(c["policy_id"])]
        cl = claims[claims.policy_id.eq(c["policy_id"])]
        lad = ladder[ladder.row_id.eq(c["row_id"])].iloc[0]
        c.update({"line": lad.line, "level": lad.level, "holds": lad.holds, "own_missing_fields": lad.own_missing_fields,
                  "chosen_reference_row_id": lad.chosen_reference_row_id, "chosen_direction": lad.chosen_direction, "chosen_ratio": lad.chosen_ratio,
                  "history": [jsonable({k: (h_row[k] if not pd.isna(h_row[k]) else None) for k in
                                        ["row_id", "source_table", "period_start", "period_end", "exposure", "sum_insured", "base_capital", "branch_capital",
                                         "address_id", "renewal_decision", "renewal_count", "new_business", "written_premium"] + FIELDS[lad.line][2:]})
                              for _, h_row in h.iterrows()],
                  "claims": [jsonable({k: (cl_row[k] if not pd.isna(cl_row[k]) else None) for k in
                                       ["claim_id", "peril", "loss_date", "status", "incurred_to_date", "recoveries", "assigned_row_id"]}) for _, cl_row in cl.iterrows()],
                  "bridges": [jsonable(b) for b in bridges[bridges.focus_row_id.eq(c["row_id"])].to_dict("records")]})
        cases.append(c)
    return cases


# ----------------------------------------------------------------------------- principal
def main() -> None:
    started = datetime.now(timezone.utc)
    checks = Checks()
    inp = load_inputs()
    out = HERE / "runs" / (started.strftime("ctx_%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    (out / "tables").mkdir(parents=True, exist_ok=False)

    # --- procedencia: originales con el hash del catálogo base; entradas usadas
    provenance = {"originals_sha256": {p.stem: digest(p) for p in sorted(RAW.glob("*.parquet"))}}
    cat_orig = {k: v["sha256"] for k, v in inp["base_cat"].items() if v.get("layer") == "original_unchanged"}
    checks.add("P01", "las tablas originales sin derivar conservan el hash del catálogo base",
               all(provenance["originals_sha256"][k] == h for k, h in cat_orig.items()), observed=sorted(cat_orig))
    provenance["inputs_sha256"] = {
        "current_retrospective_dataset.json": digest(LIMP / "current_retrospective_dataset.json"),
        "current_dataset.json": digest(LIMP / "current_dataset.json"),
        "retrospective_pending_capitals": digest(inp["retro_run"] / "tables/pending_capitals.parquet"),
        "retrospective_cumulative_ledger": digest(inp["retro_run"] / "ledger/cumulative_retrospective_changes.parquet"),
        "D56_frozen_202_cohort": digest(D56 / "tables/frozen_202_cohort.csv"),
        "D56_incomplete_assessment": digest(D56 / "tables/incomplete_assessment.csv"),
        "D56_missing_field_bridges": digest(D56 / "tables/missing_field_bridges.csv"),
        "D57_held_numeric_conflicts": digest(D57 / "tables/held_numeric_conflicts.csv"),
    }
    for name, run in [("D56", D56), ("D57", D57)]:
        manifest = json.loads((run / "manifest.json").read_text("utf-8"))
        expected = {e["path"].replace("\\", "/"): e["sha256"] for e in manifest["files"]}
        wanted = ["tables/frozen_202_cohort.csv", "tables/incomplete_assessment.csv", "tables/missing_field_bridges.csv"] if name == "D56" else ["tables/held_numeric_conflicts.csv"]
        bad = [rel for rel in wanted if expected.get(rel) != digest(run / rel)]
        checks.add(f"P02_{name}", f"las tablas de {name} usadas conservan el hash de su manifiesto", not bad, observed=bad)
    provenance["retrospective_run"] = inp["retro_idx"]["workspace_relative_run"]
    provenance["retrospective_status"] = inp["retro_idx"]["status"]
    provenance["base_run"] = inp["base_idx"]["workspace_relative_run"]

    # --- cohorte
    pending = inp["pending"]
    F = pending[pending.review_group.eq("F_incomplete_context")]
    held_ids = set(inp["held"].row_id)
    cohort = F[~F.row_id.isin(held_ids)].copy()
    cap05 = set(inp["ledger"].loc[inp["ledger"].rule.eq("CAP05R"), "row_id"])
    expected_ids = set(inp["cohort202"].row_id) - cap05 - held_ids
    checks.add("K01", "la cohorte es el grupo F de D48 vigente en la rama activa sin las dos pólizas retenidas en D57 (202 − 46 de CAP05R − 2)",
               set(cohort.row_id) == expected_ids and len(cohort) == 154, expected=154, observed=len(cohort))
    held_in_ledger = inp["ledger"][inp["ledger"].row_id.isin(held_ids)]
    held_status = {rid: ("corregida en " + ", ".join(sorted(held_in_ledger.loc[held_in_ledger.row_id.eq(rid), "rule"])) if rid in set(held_in_ledger.row_id)
                         else ("pendiente en la rama" if rid in set(pending.row_id) else "no pendiente")) for rid in sorted(held_ids)}
    checks.add("K02", "cada póliza de la cohorte aparece una sola vez", cohort.policy_id.nunique() == len(cohort), observed=int(cohort.policy_id.nunique()))
    cohort_hash = hashlib.sha256("\n".join(sorted(cohort.row_id)).encode()).hexdigest()
    focus_ids = set(cohort.row_id)
    pols = sorted(cohort.policy_id.unique())

    # --- historias
    hist = read_line_tables(pols, inp["base_cat"], inp["retro_cat"])
    checks.add("H01", "ninguna otra fila de estas pólizas es extrema ni fue corregida por CAP01 o la rama",
               int(hist.extreme.sum()) == 154 and bool((hist.base_capital == hist.sum_insured).all()) and bool((hist.branch_capital == hist.sum_insured).all()),
               observed={"extremas": int(hist.extreme.sum()), "base_distinta": int((hist.base_capital != hist.sum_insured).sum()), "rama_distinta": int((hist.branch_capital != hist.sum_insured).sum())})
    checks.add("H02", "un solo cliente por póliza; la dirección es siempre conocida",
               bool((hist.groupby("policy_id").customer_id.nunique() == 1).all()) and not hist.address_id.isna().any() and not hist.customer_id.isna().any(),
               observed={"polizas_una_direccion": int((hist.groupby("policy_id").address_id.nunique() == 1).sum()), "polizas": int(hist.policy_id.nunique())})
    hist["focus"] = hist.row_id.isin(focus_ids)
    focus = hist[hist.focus].copy()
    focus["own_missing_fields"] = ["|".join(c for c in FIELDS[r.line] if pd.isna(r[c])) for _, r in focus.iterrows()]
    nulls_focus = {line: {c: int(focus.loc[focus.line.eq(line), c].isna().sum()) for c in NULLABLE[line]} for line in NULLABLE}
    other_null = {line: [c for c in FIELDS[line] if c not in NULLABLE[line] and hist.loc[hist.line.eq(line), c].isna().any()] for line in NULLABLE}
    checks.add("H03", "los únicos campos D34 con nulos en estas historias son smoke_alarms, security_level y high_value_items",
               not other_null["buildings"] and not other_null["contents"], observed=nulls_focus)

    # --- estadísticas globales
    global_stats = global_field_statistics(checks)

    # --- referencias, puentes, siniestros, vecinas
    refs = build_references(hist, focus_ids)
    bridges = build_bridges(hist, focus_ids)
    claims = claims_for(hist, inp["base_cat"])
    neighbours = neighbour_policies(hist, focus)
    focus["reference_missing_consistent"] = focus.row_id.map(reference_missing_consistency(hist, focus, refs))
    ladder = evaluate_ladder(focus, refs, bridges, claims)

    near = refs[refs.nearest_normal_in_direction]
    per_focus = near.groupby("focus_row_id").compatible_known_context.any()
    checks.add("R01", "ninguna fila cumple el criterio estricto de D34 (es la definición del grupo F)", int(refs.strict_D34.sum()) == 0, expected=0, observed=int(refs.strict_D34.sum()))
    checks.add("R02", "todas las filas tienen una referencia original próxima compatible en los campos conocidos (ventana 1–400 días, razón 0,90–1,10)",
               bool(per_focus.all()) and len(per_focus) == 154, expected=154, observed=int(per_focus.sum()))
    tiers = ladder.tier.value_counts().to_dict()
    checks.add("R03", "los tiers coinciden con D56: 131 filas incompletas y 23 filas completas con referencias incompletas",
               tiers.get("C_fila_incompleta") == 131 and tiers.get("B_referencias_incompletas") == 23, expected={"C": 131, "B": 23}, observed=tiers)
    # comparación con los puentes de D56 bajo su propia definición (sin exigir misma dirección)
    b56 = inp["bridges56"][inp["bridges56"].focus_row_id.isin(focus_ids)]
    checks.add("R04", "los puentes de D56 para estas filas suman 132 campos (50 iguales a ambos lados, 69 de un solo lado, 12 iguales con cambio o faltante, 1 distinto)",
               len(b56) == 132 and b56.bridge_status.value_counts().to_dict() == {"ONE_SIDED_KNOWN": 69, "BOTH_EQUAL_RECORDED_CONTEXT": 50, "BOTH_EQUAL_WITH_CONTEXT_CHANGE_OR_MISSING": 12, "BOTH_DIFFERENT_VALUE": 1},
               observed=b56.bridge_status.value_counts().to_dict())
    my_bridges = bridges.bridge_status.value_counts().to_dict()
    checks.add("R05", "los puentes recalculados en la misma dirección cubren los 132 campos ausentes", len(bridges) == 132, expected=132, observed=my_bridges)
    checks.add("R06", "ningún siniestro aceptado de un periodo extremo supera el capital hipotético (capital/1000)",
               int(claims.incurred_above_hypothetical_capital.sum()) == 0, expected=0, observed=int(claims.incurred_above_hypothetical_capital.sum()))
    checks.add("R07", "la razón (capital/1000)/referencia de la referencia elegida queda dentro de 0,90–1,10 en todas las candidatas",
               bool(ladder.loc[ladder.candidate_NOT_APPLIED, "chosen_ratio"].between(*BAND).all()),
               observed={str(q): float(v) for q, v in ladder.loc[ladder.candidate_NOT_APPLIED, "chosen_ratio"].quantile([0, 0.05, 0.5, 0.95, 1]).round(4).items()})
    checks.add("R08", "las referencias elegidas no solapan el periodo pendiente y están a 1–400 días",
               bool(refs.loc[refs.compatible_known_context, "in_window"].all()), observed=int(refs.compatible_known_context.sum()))
    direction_mix = ladder[ladder.candidate_NOT_APPLIED].chosen_direction.value_counts().to_dict()
    checks.add("R09", "el capital hipotético (capital/1000) de todas las candidatas queda dentro de la banda normal de su ramo",
               bool(all(h <= THR[l] for h, l in zip(ladder.loc[ladder.candidate_NOT_APPLIED, "hypothetical_CU"], ladder.loc[ladder.candidate_NOT_APPLIED, "line"]))),
               observed={"max_hipotetico_edificios": float(ladder.loc[ladder.candidate_NOT_APPLIED & ladder.line.eq("buildings"), "hypothetical_CU"].max()),
                         "max_hipotetico_contenidos": float(ladder.loc[ladder.candidate_NOT_APPLIED & ladder.line.eq("contents"), "hypothetical_CU"].max())})
    checks.add("R10", "ninguna fila incompleta (tier C) queda en el nivel N3: todo campo ausente de la fila tiene al menos un valor conocido en la misma dirección",
               int((ladder.level.eq("N3_identidad_sin_campo") & ladder.tier.eq("C_fila_incompleta")).sum()) == 0, expected=0,
               observed={"N3_tier_C": int((ladder.level.eq("N3_identidad_sin_campo") & ladder.tier.eq("C_fila_incompleta")).sum()),
                         "N3_tier_B": int((ladder.level.eq("N3_identidad_sin_campo") & ladder.tier.eq("B_referencias_incompletas")).sum())})
    checks.add("R11", "las dos filas retenidas tienen su referencia más próxima compatible; la contradicción viene de un tramo ampliado más lejano",
               bool((~ladder.loc[ladder.contradiction_in_policy, "contradiction_nearer_than_chosen"]).all()) and bool(ladder.loc[ladder.contradiction_in_policy, "n_nearest_compatible"].ge(1).all()),
               observed=ladder.loc[ladder.contradiction_in_policy, ["row_id", "chosen_gap_days", "chosen_ratio"]].to_dict("records"))
    tier_b = refs[refs.focus_row_id.isin(ladder.loc[ladder.tier.eq("B_referencias_incompletas"), "row_id"]) & refs.reference_normal]
    tier_b_detail = {"rows": int(ladder.tier.eq("B_referencias_incompletas").sum()),
                     "reference_missing_fields": tier_b.loc[tier_b.reference_missing_fields.ne(""), "reference_missing_fields"].value_counts().to_dict(),
                     "focus_value_consistent_with_other_known": int(ladder.loc[ladder.tier.eq("B_referencias_incompletas"), "reference_missing_consistent_with_focus"].eq(True).sum()),
                     "only_focus_knows_the_field": int(ladder.loc[ladder.tier.eq("B_referencias_incompletas"), "reference_missing_consistent_with_focus"].eq(False).sum())}

    # --- escalera: conteos por nivel y por modo de dirección
    def count_levels(mask):
        return {lvl: int(((ladder.level == lvl) & mask).sum()) for lvl in ["N1_puente_dos_lados", "N2_vecino_conocido", "N3_identidad_sin_campo"]}
    ladder_summary = {
        "N0_D34_estricto": 0,
        "any_direction": {"candidates": int(ladder.candidate_NOT_APPLIED.sum()), "by_level": count_levels(ladder.candidate_NOT_APPLIED),
                          "cumulative": None, "held": int((~ladder.candidate_NOT_APPLIED).sum())},
        "prior_only": {"candidates": int((ladder.candidate_NOT_APPLIED & ladder.prior_compatible).sum()),
                       "by_level": count_levels(ladder.candidate_NOT_APPLIED & ladder.prior_compatible)},
        "later_only_support": int((ladder.candidate_NOT_APPLIED & ~ladder.prior_compatible).sum()),
        "test2025_rows_in_candidates": int((ladder.candidate_NOT_APPLIED & ladder.test2025_row).sum()),
        "candidates_with_test2025_reference": int((ladder.candidate_NOT_APPLIED & ladder.chosen_reference_test2025.fillna(False).astype(bool)).sum()),
        "held_reasons": ladder.loc[~ladder.candidate_NOT_APPLIED, "holds"].value_counts().to_dict(),
        "by_level_all": ladder.level.value_counts().to_dict(),
        "by_tier": tiers, "by_line": ladder.line.value_counts().to_dict(), "by_source_table": ladder.source_table.value_counts().to_dict(),
        "by_year": {int(k): int(v) for k, v in ladder.year.value_counts().sort_index().items()},
        "own_missing_fields": ladder.own_missing_fields.value_counts().to_dict(),
        "bridge_statuses_same_address": my_bridges,
        "direction_of_chosen_reference": direction_mix,
        "both_directions_compatible": int(ladder.both_directions_compatible.sum()),
        "rows_with_other_references_changed": int(ladder.any_reference_with_changed_fields.sum()),
        "changed_fields_in_other_references": ladder.loc[ladder.any_reference_with_changed_fields, "changed_fields_in_other_references"].value_counts().to_dict(),
        "contradictions": int(ladder.contradiction_in_policy.sum()),
        "tier_B_detail": tier_b_detail,
        "candidates_test2025_by_direction": {k: int(v) for k, v in ladder[ladder.candidate_NOT_APPLIED & ladder.test2025_row].chosen_direction.value_counts().items()},
        "candidates_with_test2025_reference_by_year": {int(k): int(v) for k, v in ladder[ladder.candidate_NOT_APPLIED & ladder.chosen_reference_test2025.fillna(False).astype(bool)].year.value_counts().sort_index().items()},
    }
    lv = ladder_summary["any_direction"]["by_level"]
    ladder_summary["any_direction"]["cumulative"] = {"N1": lv["N1_puente_dos_lados"], "N1+N2": lv["N1_puente_dos_lados"] + lv["N2_vecino_conocido"],
                                                     "N1+N2+N3": lv["N1_puente_dos_lados"] + lv["N2_vecino_conocido"] + lv["N3_identidad_sin_campo"]}

    # --- distribuciones de apoyo
    comp = refs[refs.compatible_known_context & refs.nearest_normal_in_direction]
    distributions = {
        "chosen_ratio_quantiles": {str(q): float(v) for q, v in ladder.loc[ladder.candidate_NOT_APPLIED, "chosen_ratio"].quantile([0, 0.05, 0.25, 0.5, 0.75, 0.95, 1]).round(4).items()},
        "chosen_gap_days_quantiles": {str(q): float(v) for q, v in ladder.loc[ladder.candidate_NOT_APPLIED, "chosen_gap_days"].quantile([0, 0.25, 0.5, 0.75, 1]).items()},
        "chosen_gap_days_counts": {str(int(k)): int(v) for k, v in ladder.loc[ladder.candidate_NOT_APPLIED, "chosen_gap_days"].value_counts().sort_index().items()},
        "nearest_compatible_by_direction": comp.direction.value_counts().to_dict(),
        "premium_annualised_ratio_focus_over_chosen_reference_quantiles": {str(q): float(v) for q, v in comp.premium_annualised_ratio_focus_over_reference.quantile([0.05, 0.25, 0.5, 0.75, 0.95]).round(3).items()},
        "history_periods_per_policy": {str(int(k)): int(v) for k, v in hist.groupby("policy_id").size().value_counts().sort_index().items()},
        "policies_with_address_change": int((hist.groupby("policy_id").address_id.nunique() > 1).sum()),
        "claims_total": int(len(claims)), "claims_accepted": int(claims.accepted.sum()), "claims_in_extreme_periods": int((claims.period_extreme & claims.accepted).sum()),
        "claims_net_incurred_accepted_CU": float(claims.loc[claims.accepted, "net_incurred_CU"].sum()),
        "neighbour_policies_rows": int(len(neighbours)), "focus_rows_with_neighbour_policy": int(neighbours.focus_row_id.nunique()) if len(neighbours) else 0,
        "neighbour_extreme_rows": int(neighbours.other_extreme.sum()) if len(neighbours) else 0,
        "focus_exposure_quantiles": {str(q): float(v) for q, v in focus.exposure.quantile([0, 0.25, 0.5, 0.75, 1]).round(4).items()},
        "focus_renewal_decision": focus.renewal_decision.fillna("test_2025").value_counts().to_dict(),
        "focus_new_business": int(focus.new_business.sum()),
    }
    # prima diagnóstica: prima anualizada por mil de capital, con el capital tal cual y con el hipotético
    premium = {}
    for line in ["buildings", "contents"]:
        f = focus[focus.line.eq(line) & (focus.exposure > 0)]
        t = pq.read_table(RAW / f"policies_{line}.parquet", columns=["sum_insured", "written_premium", "exposure"]).to_pandas()
        n = t[(t.sum_insured > 0) & (t.sum_insured <= THR[line]) & (t.exposure > 0)]
        premium[line] = {
            "normal_rows_premium_per_1000_capital_quantiles": {str(q): float(v) for q, v in (n.written_premium / n.exposure / n.sum_insured * 1000).quantile([0.05, 0.25, 0.5, 0.75, 0.95]).round(3).items()},
            "focus_premium_per_1000_hypothetical_capital_quantiles": {str(q): float(v) for q, v in (f.written_premium / f.exposure / (f.sum_insured / 1000) * 1000).quantile([0.05, 0.25, 0.5, 0.75, 0.95]).round(3).items()},
            "focus_premium_per_1000_recorded_capital_median": float((f.written_premium / f.exposure / f.sum_insured * 1000).median()),
        }

    # --- casos
    cases = pick_cases(ladder, bridges, hist, claims)

    # --- candidatas congeladas (NO APLICADAS)
    cand = ladder[ladder.candidate_NOT_APPLIED].copy()
    cand["new_hypothetical_CU"] = cand.original_capital_CU / 1000
    cand["unknown_fields_focus"] = cand.own_missing_fields
    cand["unknown_fields_reference"] = cand.chosen_reference_missing_fields
    cand = cand[["row_id", "policy_id", "line", "source_table", "year", "period_start", "period_end", "original_capital_CU", "new_hypothetical_CU",
                 "chosen_reference_row_id", "chosen_reference_source_table", "chosen_direction", "chosen_gap_days", "chosen_reference_capital_CU", "chosen_ratio",
                 "chosen_reference_test2025", "unknown_fields_focus", "unknown_fields_reference", "bridge_statuses", "level", "prior_compatible", "later_compatible",
                 "test2025_row"]].sort_values(["line", "row_id"]).reset_index(drop=True)
    cand["capital_change_applied"] = False
    cand["correction_authorized"] = False
    candidates_hash = hashlib.sha256("\n".join(cand.row_id).encode()).hexdigest()
    held_rows = ladder[~ladder.candidate_NOT_APPLIED].copy()

    # --- tablas
    tables = {
        "cohorte_154": focus[KEEP + ["source_table", "line", "year", "covered_days", "own_missing_fields", "test2025"] + EXTRA],
        "historias": hist[KEEP + ["source_table", "line", "year", "covered_days", "base_capital", "branch_capital", "extreme", "focus", "test2025"] + EXTRA],
        "referencias": refs, "puentes": bridges, "siniestros": claims, "polizas_vecinas": neighbours, "escalera": ladder,
        "candidatas_NO_APLICADAS": cand, "retenidas": held_rows,
    }
    for name, frame in tables.items():
        frame.to_csv(out / "tables" / f"{name}.csv", index=False, encoding="utf-8", lineterminator="\n", date_format="%Y-%m-%d")
    pd.DataFrame(checks.rows).to_csv(out / "tables" / "controles.csv", index=False, encoding="utf-8", lineterminator="\n")

    evidence = {
        "run_id": out.name, "created_utc": started.isoformat(timespec="seconds"), "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "author": "Claude (Cowork), a solicitud del participante",
        "request": "Ahora revisemos los 154 capitales con contexto incompleto que siguen pendientes. Compara sus historiales, muestra casos concretos y propón cómo tratarlos sin modificar los datos todavía.",
        "scope": {"review_only": True, "data_modified": False, "indices_modified": False, "models_trained": False, "external_providers": False,
                  "human_review": "pending", "independent_validation": False},
        "environment": {"python": platform.python_version(), "pandas": pd.__version__, "pyarrow": pq.__version__ if hasattr(pq, "__version__") else None, "platform": platform.platform()},
        "definitions": {"D34_fields": FIELDS, "nullable_fields": NULLABLE, "extreme_thresholds_CU": THR, "ratio_band": BAND, "start_gap_window_days": WINDOW,
                        "hypothesis": "sum_insured / 1000", "reference": "periodo original de la misma póliza con capital normal (0 < capital <= umbral), sin solape, inicio a 1–400 días",
                        "known_context_equal": "todos los campos D34 conocidos en ambas filas son iguales; un campo nulo en una de las dos se registra como desconocido, nunca se imputa",
                        "levels": {"N0_D34_estricto": "todos los campos D34 conocidos e iguales (criterio vigente): 0 filas por definición del grupo",
                                   "N1_puente_dos_lados": "cada campo ausente de la fila tiene un valor conocido antes y otro después, iguales entre sí, en la misma dirección",
                                   "N2_vecino_conocido": "cada campo ausente tiene al menos un valor conocido en otro periodo de la misma dirección (o, en tier B, los conocidos de la póliza coinciden con la fila)",
                                   "N3_identidad_sin_campo": "solo identidad (cliente, dirección y demás campos conocidos iguales); ningún otro periodo informa el campo ausente (en tier B, solo la propia fila pendiente lo conoce)"},
                        "holds": ["referencia_contradictoria_en_la_poliza", "campo_ausente_con_vecinos_distintos", "siniestro_por_encima_del_capital_hipotetico", "sin_referencia_compatible"],
                        "chosen_reference": "la referencia compatible más próxima; si hay anterior y posterior, se prefiere la anterior"},
        "provenance": provenance,
        "cohort": {"rows": int(len(cohort)), "policies": int(cohort.policy_id.nunique()), "sha256_sorted_row_ids": cohort_hash,
                   "derivation": "202 del grupo F (D56) − 46 aplicadas en CAP05R (D58) − 2 retenidas en D57 y revisadas en D60",
                   "held_D57_rows_status_in_active_branch": held_status,
                   "by_line": cohort.line.value_counts().to_dict(), "by_source_table": cohort.source_table.value_counts().to_dict(),
                   "history_rows": int(len(hist)), "pending_in_branch_total": int(len(pending)), "pending_groups_in_branch": pending.review_group.value_counts().to_dict()},
        "global_field_statistics": global_stats,
        "ladder": ladder_summary, "distributions": distributions, "premium_diagnostic": premium,
        "candidates_NOT_APPLIED": {"rows": int(len(cand)), "sha256_sorted_row_ids": candidates_hash, "by_line": cand.line.value_counts().to_dict(),
                                   "by_source_table": cand.source_table.value_counts().to_dict(), "by_level": cand.level.value_counts().to_dict(),
                                   "by_direction": cand.chosen_direction.value_counts().to_dict(), "prior_supported": int(cand.prior_compatible.sum()),
                                   "test2025_rows": int(cand.test2025_row.sum()), "reference_is_test2025": int(cand.chosen_reference_test2025.astype(bool).sum()),
                                   "sum_original_CU": float(cand.original_capital_CU.sum()), "sum_hypothetical_CU": float(cand.new_hypothetical_CU.sum())},
        "held": {"rows": int(len(held_rows)), "row_ids": held_rows.row_id.tolist(), "reasons": held_rows.holds.tolist()},
        "cases": cases,
        "checks": checks.rows,
        "summary": {"checks_total": len(checks.rows), "checks_passed": sum(1 for c in checks.rows if c["passed"]), "all_passed": all(c["passed"] for c in checks.rows)},
    }
    (out / "evidencia.json").write_text(json.dumps(jsonable(evidence), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(__file__, out / Path(__file__).name)
    manifest = {str(p.relative_to(out)).replace("\\", "/"): digest(p) for p in sorted(out.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run": str(out.relative_to(ROOT)).replace("\\", "/"), "checks": evidence["summary"], "candidates": len(cand), "held": len(held_rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
