"""Revisión de los capitales pendientes de la rama retrospectiva que no pertenecen al grupo F de D48.

Cubre los grupos de D48 que siguen pendientes en la rama activa: G (otros conflictos de capital, riesgo o distancia
temporal), C (sin referencia original habitual), E (dependientes de interpretar T/W), D (apoyo dependiente de
correcciones CAP01) y A (la discrepancia C48613718). Recalcula desde los Parquet originales, con código propio, la
historia de cada póliza y todas sus referencias, clasifica el motivo por el que cada fila no cumple D34, mide en todo
el archivo los comportamientos que permiten interpretar cada motivo (mudanzas, ampliaciones a mitad de año, alias T/W)
y deja, por grupo, una propuesta de tratamiento con listas congeladas SIN APLICAR. No modifica datos, índices ni
corridas de Codex; no entrena modelos.

Uso (desde la raíz del proyecto, con el Python de Preparación/.venv):
    python "Hackaton/Semana 1/Revision_pendientes_restantes_claude/revisar_pendientes_restantes.py"
Crea runs/rest_<marca>_<id>/ con evidencia.json, tablas CSV, copia del script y manifest.json (SHA-256).
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
CTX = ROOT / "Hackaton/Semana 1/Revision_contexto_pendiente_claude"
FIELDS = {
    "buildings": ["customer_id", "address_id", "construction_type", "occupancy", "accidental_damage_cover",
                  "voluntary_excess", "compulsory_excess", "smoke_alarms", "mortgage"],
    "contents": ["customer_id", "address_id", "tenure", "security_level", "high_value_items", "accidental_damage_cover",
                 "works_from_home", "lodgers", "bicycle_cover", "voluntary_excess", "compulsory_excess"],
}
THR = {"buildings": 10_000_000, "contents": 1_000_000}
BAND = (0.9, 1.1)
WINDOW = (1, 400)
ENDORSE_BAND = (1.15, 1.65)          # banda empírica de las ampliaciones a mitad de año en contenidos (p1–p99 observados: 1,203–1,596)
CHAIN_MAX_DAYS = 731                 # dos años calendario, como DIST01-R
GROUP_NAMES = {"G_other_conflicts": "G · otros conflictos", "C_no_original_normal_reference": "C · sin referencia original habitual",
               "E_TW_dependency": "E · dependientes de T/W", "D_CAP01_dependency_only": "D · apoyo dependiente de CAP01", "A_retrospective_D34": "A · discrepancia C48613718"}
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
        self.rows.append({"id": cid, "name": name, "passed": bool(passed), "expected": jsonable(expected), "observed": jsonable(observed), "detail": detail})
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
    ctx_run = None
    if (CTX / "current_run.json").is_file():
        ctx_run = ROOT / json.loads((CTX / "current_run.json").read_text("utf-8"))["workspace_relative_run"]
    return dict(retro_idx=retro_idx, retro_run=retro_run, retro_cat=retro_cat, base_idx=base_idx, base_run=base_run, base_cat=base_cat,
                pending=pending, ledger=ledger, ctx_run=ctx_run)


def load_line(line: str) -> pd.DataFrame:
    parts = []
    for prefix in ["policies", "test"]:
        t = pq.read_table(RAW / f"{prefix}_{line}.parquet").to_pandas()
        t["source_table"] = f"{prefix}_{line}"
        parts.append(t)
    return to_date(pd.concat(parts, ignore_index=True))


def read_histories(pols: list[str], base_cat: dict, retro_cat: dict) -> pd.DataFrame:
    parts = []
    for line in ["buildings", "contents"]:
        for prefix in ["policies", "test"]:
            name = f"{prefix}_{line}"
            raw = pq.read_table(RAW / f"{name}.parquet", filters=[("policy_id", "in", pols)]).to_pandas()
            raw["source_table"] = name
            raw["line"] = line
            base = pq.read_table(ROOT / base_cat[name]["workspace_relative_path"], columns=["row_id", "sum_insured"], filters=[("policy_id", "in", pols)]).to_pandas().set_index("row_id").sum_insured
            branch = pq.read_table(ROOT / retro_cat[name]["workspace_relative_path"], columns=["row_id", "sum_insured"], filters=[("policy_id", "in", pols)]).to_pandas().set_index("row_id").sum_insured
            raw["base_capital"] = raw.row_id.map(base)
            raw["branch_capital"] = raw.row_id.map(branch)
            parts.append(raw)
    hist = pd.concat(parts, ignore_index=True)
    hist = to_date(hist).sort_values(["policy_id", "period_start", "row_id"]).reset_index(drop=True)
    hist["year"] = hist.period_start.dt.year
    hist["covered_days"] = (hist.period_end - hist.period_start).dt.days + 1
    hist["extreme"] = [cap > THR[line] for cap, line in zip(hist.sum_insured, hist.line)]
    hist["cap01_corrected"] = hist.base_capital != hist.sum_insured
    hist["branch_corrected"] = hist.branch_capital != hist.sum_insured
    hist["test2025"] = hist.source_table.str.startswith("test_")
    return hist


# ----------------------------------------------------------------------------- estadísticas globales
def global_statistics(checks: Checks) -> dict:
    out = {}
    # edificios: alias T/W y mudanzas
    b = load_line("buildings")
    d = b[(b.sum_insured > 0) & (b.sum_insured <= THR["buildings"])].sort_values(["policy_id", "period_start", "row_id"])
    g = d.groupby("policy_id", sort=False)
    prev = g.shift(1)
    same = g.cumcount() > 0
    same_addr = same & (d.address_id == prev.address_id)
    moved = same & (d.address_id != prev.address_id)
    ratio = d.sum_insured / prev.sum_insured
    ct = d.construction_type.map(lambda v: norm(v, "construction_type"))
    pct = prev.construction_type.map(lambda v: norm(v, "construction_type") if isinstance(v, str) else None)
    tw = same_addr & (pct == "t") & (ct == "w")
    other_change = same_addr & pct.notna() & (pct != ct) & ~tw
    on_2023 = (d.period_start.dt.year == 2023) & (d.period_start.dt.month == 1) & (d.period_start.dt.day == 1)
    out["buildings"] = {
        "rows": int(len(b)), "extreme_rows": int((b.sum_insured > THR["buildings"]).sum()),
        "normal_max_capital_CU": float(d.sum_insured.max()), "extreme_min_capital_CU": float(b.loc[b.sum_insured > THR["buildings"], "sum_insured"].min()),
        "pairs_same_address": int(same_addr.sum()), "pairs_same_address_in_band": float(ratio[same_addr].between(*BAND).mean()),
        "pairs_address_change": int(moved.sum()), "pairs_address_change_in_band": float(ratio[moved].between(*BAND).mean()),
        "pairs_address_change_ratio_quantiles": {str(q): float(v) for q, v in ratio[moved].quantile([0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]).items()},
        "tw_alias_pairs_same_address": int(tw.sum()), "tw_alias_pairs_in_band": float(ratio[tw].between(*BAND).mean()),
        "tw_alias_ratio_quantiles": {str(q): float(v) for q, v in ratio[tw].quantile([0.01, 0.5, 0.99]).items()},
        "tw_alias_pairs_starting_2023_01_01": float(on_2023[tw].mean()),
        "other_construction_changes_same_address": int(other_change.sum()),
        "pairs_same_address_no_construction_change_in_band": float(ratio[same_addr & (pct == ct)].between(*BAND).mean()),
    }
    checks.add("G01", "en edificios, el cambio de código t→w en la misma dirección no altera el capital (razón en banda en el 100 % de los pares) y no hay otros cambios de construcción en la misma dirección",
               out["buildings"]["tw_alias_pairs_in_band"] == 1.0 and other_change.sum() == 0, observed={"pares_t_w": int(tw.sum()), "en_banda": out["buildings"]["tw_alias_pairs_in_band"], "otros_cambios": int(other_change.sum())})
    checks.add("G02", "en edificios, una mudanza recalcula el capital (razón en banda en menos del 20 % de los pares con cambio de dirección)",
               out["buildings"]["pairs_address_change_in_band"] < 0.2, observed=out["buildings"]["pairs_address_change_in_band"])
    # contenidos: mudanzas y ampliaciones
    c = load_line("contents")
    d = c[(c.sum_insured > 0) & (c.sum_insured <= THR["contents"])].sort_values(["policy_id", "period_start", "row_id"])
    g = d.groupby("policy_id", sort=False)
    prev = g.shift(1)
    nxt = g.shift(-1)
    same = g.cumcount() > 0
    same_addr = same & (d.address_id == prev.address_id)
    moved = same & (d.address_id != prev.address_id)
    ratio = d.sum_insured / prev.sum_insured
    after_mtc = same_addr & prev.renewal_decision.eq("mid_term_change")
    up = after_mtc & (ratio > 1.1)
    nxt_same = up & nxt.address_id.notna() & (nxt.address_id == d.address_id)
    reversion = (nxt.sum_insured / prev.sum_insured)[nxt_same]
    out["contents"] = {
        "rows": int(len(c)), "extreme_rows": int((c.sum_insured > THR["contents"]).sum()),
        "normal_max_capital_CU": float(d.sum_insured.max()), "extreme_min_capital_CU": float(c.loc[c.sum_insured > THR["contents"], "sum_insured"].min()),
        "pairs_same_address": int(same_addr.sum()), "pairs_same_address_in_band": float(ratio[same_addr].between(*BAND).mean()),
        "pairs_address_change": int(moved.sum()), "pairs_address_change_in_band": float(ratio[moved].between(*BAND).mean()),
        "pairs_address_change_ratio_exactly_1": float((ratio[moved] == 1).mean()),
        "periods_after_mid_term_change_same_address": int(after_mtc.sum()),
        "after_mid_term_change_ratio_quantiles": {str(q): float(v) for q, v in ratio[after_mtc].quantile([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).items()},
        "after_mid_term_change_share_above_1_1": float((ratio[after_mtc] > 1.1).mean()), "after_mid_term_change_share_below_0_9": float((ratio[after_mtc] < 0.9).mean()),
        "after_mid_term_change_share_in_endorse_band": float(ratio[after_mtc].between(*ENDORSE_BAND).mean()),
        "endorsements_with_next_period_same_address": int(nxt_same.sum()),
        "reversion_next_over_base_quantiles": {str(q): float(v) for q, v in reversion.quantile([0.01, 0.5, 0.99]).items()},
        "reversion_next_over_base_in_band": float(reversion.between(*BAND).mean()),
        "pairs_same_address_without_prior_mid_term_change_in_band": float(ratio[same_addr & ~prev.renewal_decision.eq("mid_term_change")].between(*BAND).mean()),
    }
    checks.add("G03", "en contenidos, el capital se conserva exactamente al cambiar de dirección (razón igual a 1 en más del 99 % de los pares con mudanza)",
               out["contents"]["pairs_address_change_ratio_exactly_1"] > 0.99, observed=out["contents"]["pairs_address_change_ratio_exactly_1"])
    checks.add("G04", "en contenidos, el periodo que sigue a un mid_term_change en la misma dirección sube el capital entre 1,15 y 1,65 veces en más del 99 % de los casos y nunca lo baja",
               out["contents"]["after_mid_term_change_share_in_endorse_band"] > 0.99 and out["contents"]["after_mid_term_change_share_below_0_9"] == 0.0,
               observed={"en_banda_ampliacion": out["contents"]["after_mid_term_change_share_in_endorse_band"], "bajan": out["contents"]["after_mid_term_change_share_below_0_9"]})
    checks.add("G05", "en contenidos, tras una ampliación el siguiente periodo vuelve al nivel base indexado (razón siguiente/base dentro de 0,90–1,10 en el 100 % de los casos)",
               out["contents"]["reversion_next_over_base_in_band"] == 1.0, observed=out["contents"]["reversion_next_over_base_in_band"])
    # firma estructural de la ampliación: periodo contiguo (sin hueco) con el mismo contador de renovaciones en la misma dirección
    contiguous = same_addr & (prev.period_end + pd.Timedelta(days=1)).eq(d.period_start) & prev.renewal_count.eq(d.renewal_count)
    labelled = same_addr & prev.renewal_decision.notna()
    out["contents"]["structural_signature"] = {
        "pairs_labelled": int(labelled.sum()),
        "share_mid_term_change_given_contiguous_same_counter": float(prev.renewal_decision.eq("mid_term_change")[contiguous & labelled].mean()),
        "share_contiguous_same_counter_given_mid_term_change": float(contiguous[after_mtc].mean()),
        "pairs_contiguous_same_counter_unlabelled_test": int((contiguous & ~labelled).sum()),
    }
    checks.add("G06", "en contenidos, la etiqueta mid_term_change equivale a la firma estructural 'periodo contiguo con el mismo contador de renovaciones en la misma dirección' (más del 99 % en ambos sentidos), lo que permite reconocer ampliaciones en test 2025",
               out["contents"]["structural_signature"]["share_mid_term_change_given_contiguous_same_counter"] > 0.99 and out["contents"]["structural_signature"]["share_contiguous_same_counter_given_mid_term_change"] > 0.99,
               observed=out["contents"]["structural_signature"])
    return out


# ----------------------------------------------------------------------------- referencias
def previous_contiguous(hist: pd.DataFrame, policy_id: str, row):
    """Periodo inmediatamente anterior de la misma póliza y dirección que termina el día antes de que empiece `row`, con el mismo
    contador de renovaciones y, si la etiqueta existe, renewal_decision == mid_term_change. Es la firma estructural de una
    ampliación a mitad de año; devuelve None si no existe."""
    grp = hist[hist.policy_id.eq(policy_id) & hist.row_id.ne(row.row_id) & hist.address_id.eq(row.address_id)]
    cand = grp[(grp.period_end + pd.Timedelta(days=1)).eq(row.period_start) & grp.renewal_count.eq(row.renewal_count)]
    cand = cand[cand.renewal_decision.isna() | cand.renewal_decision.eq("mid_term_change")]
    if len(cand) != 1:
        return None
    return cand.iloc[0]


def build_references(hist: pd.DataFrame, focus_ids: set[str]) -> pd.DataFrame:
    rows = []
    for _, cur in hist[hist.row_id.isin(focus_ids)].iterrows():
        grp = hist[hist.policy_id.eq(cur.policy_id) & hist.row_id.ne(cur.row_id)]
        for _, ref in grp.iterrows():
            normal = bool(0 < ref.sum_insured <= THR[cur.line])
            missing, changed = [], []
            for col in FIELDS[cur.line]:
                if pd.isna(cur[col]) or pd.isna(ref[col]):
                    missing.append(col)
                    continue
                if norm(cur[col], col) != norm(ref[col], col):
                    changed.append(col)
            tw_only = changed == ["construction_type"] and {norm(cur.construction_type, "construction_type"), norm(ref.construction_type, "construction_type")} <= {"t", "w"}
            addr_only = changed == ["address_id"]
            direction = "prior" if ref.period_start < cur.period_start else "later"
            gap = int(abs((cur.period_start - ref.period_start).days))
            nonoverlap = bool(ref.period_end < cur.period_start) if direction == "prior" else bool(cur.period_end < ref.period_start)
            ratio = float((cur.sum_insured / 1000) / ref.sum_insured) if ref.sum_insured > 0 else np.nan
            # ¿la referencia es un periodo ampliado? Sigue, en la misma dirección y sin hueco, a un periodo con el mismo contador de
            # renovaciones (en entrenamiento ese periodo termina con mid_term_change; en test no hay etiqueta). Si ese periodo previo es la
            # propia fila pendiente, la base es su capital dividido entre mil.
            prev_row = previous_contiguous(hist, cur.policy_id, ref)
            ref_after_mtc = prev_row is not None
            if ref_after_mtc:
                base_cap = cur.sum_insured / 1000 if prev_row.row_id == cur.row_id else (prev_row.sum_insured if 0 < prev_row.sum_insured <= THR[cur.line] else np.nan)
            ref_endorse_ratio = float(ref.sum_insured / base_cap) if ref_after_mtc and not np.isnan(base_cap) and base_cap > 0 else np.nan
            rows.append({
                "focus_row_id": cur.row_id, "policy_id": cur.policy_id, "line": cur.line, "focus_source_table": cur.source_table, "focus_period_start": cur.period_start,
                "focus_capital_CU": float(cur.sum_insured), "hypothetical_CU": float(cur.sum_insured / 1000),
                "reference_row_id": ref.row_id, "reference_source_table": ref.source_table, "reference_period_start": ref.period_start, "reference_period_end": ref.period_end,
                "reference_covered_days": int(ref.covered_days), "reference_capital_CU": float(ref.sum_insured), "reference_normal": normal, "reference_extreme": bool(ref.extreme),
                "reference_cap01_corrected": bool(ref.cap01_corrected), "reference_branch_corrected": bool(ref.branch_corrected), "reference_base_capital_CU": float(ref.base_capital),
                "reference_corrected_capital_CU": float(ref.base_capital if ref.cap01_corrected else (ref.branch_capital if ref.branch_corrected else np.nan)),
                "reference_corrected_by": "CAP01" if ref.cap01_corrected else ("rama" if ref.branch_corrected else None), "reference_test2025": bool(ref.test2025),
                "direction": direction, "start_gap_days": gap, "nonoverlap": nonoverlap, "ratio_hypothetical_over_reference": ratio,
                "in_band": bool(BAND[0] <= ratio <= BAND[1]) if not np.isnan(ratio) else False, "in_window": bool(WINDOW[0] <= gap <= WINDOW[1]) and nonoverlap,
                "within_two_years": bool(gap <= CHAIN_MAX_DAYS) and nonoverlap,
                "known_fields_equal": not changed, "changed_fields": "|".join(changed), "unknown_fields": "|".join(missing),
                "same_address": bool(cur.address_id == ref.address_id), "tw_alias_only": bool(tw_only), "address_only": bool(addr_only),
                "reference_after_mid_term_change": ref_after_mtc, "reference_endorsement_ratio": ref_endorse_ratio,
                "ratio_hypothetical_over_corrected": float((cur.sum_insured / 1000) / (ref.base_capital if ref.cap01_corrected else ref.branch_capital)) if (ref.cap01_corrected or ref.branch_corrected) else np.nan,
            })
    refs = pd.DataFrame(rows)
    refs["compatible_known_context"] = refs.reference_normal & refs.known_fields_equal & refs.in_band & refs.in_window
    refs["contradiction_known_context"] = refs.reference_normal & refs.known_fields_equal & refs.in_window & ~refs.in_band
    refs["compatible_tw_alias"] = refs.reference_normal & refs.tw_alias_only & refs.same_address & refs.in_band & refs.in_window
    refs["compatible_move_contents"] = refs.reference_normal & refs.address_only & refs.line.eq("contents") & refs.in_band & refs.in_window
    refs["endorsed_reference"] = refs.reference_after_mid_term_change & refs.reference_endorsement_ratio.between(*ENDORSE_BAND)
    return refs


def reason_for(ref) -> str:
    changed = [c for c in ref.changed_fields.split("|") if c]
    if not ref.same_address and not ref.address_only:
        return "otra_direccion_y_otros_campos"
    if not ref.same_address:
        return "otra_direccion"
    if changed and not ref.tw_alias_only:
        return "otro_campo:" + "|".join(changed)
    base = "tw" if ref.tw_alias_only else "ctx_ok"
    if not ref.nonoverlap:
        return base + "+solape"
    if not (WINDOW[0] <= ref.start_gap_days <= WINDOW[1]):
        return base + "+distancia" + ("+razon" if not ref.in_band else "")
    if not ref.in_band:
        return base + "+razon"
    return base + "+compatible"


# ----------------------------------------------------------------------------- siniestros y vecinas
def claims_for(hist: pd.DataFrame, base_cat: dict) -> pd.DataFrame:
    claims = pq.read_table(ROOT / base_cat["claims"]["workspace_relative_path"], filters=[("policy_id", "in", hist.policy_id.unique().tolist())]).to_pandas()
    claims["loss_date"] = pd.to_datetime(claims.loss_date)
    periods = hist[["row_id", "policy_id", "line", "period_start", "period_end", "sum_insured", "extreme"]]
    merged = claims.merge(periods, on=["policy_id", "line"], how="left")
    inside = merged[(merged.loss_date >= merged.period_start) & (merged.loss_date <= merged.period_end)]
    assigned = inside.groupby("claim_id").row_id.agg(["nunique", "first"])
    claims["assigned_row_id"] = claims.claim_id.map(assigned["first"])
    claims["accepted"] = claims.status.ne("repudiated")
    claims["net_incurred_CU"] = claims.incurred_to_date - claims.recoveries
    cap = hist.set_index("row_id")
    claims["period_capital_CU"] = claims.assigned_row_id.map(cap.sum_insured)
    claims["period_extreme"] = claims.assigned_row_id.map(cap.extreme).fillna(False).astype(bool)
    claims["incurred_above_hypothetical_capital"] = claims.period_extreme & claims.accepted & (claims.incurred_to_date > claims.period_capital_CU / 1000)
    return claims


def neighbour_policies(focus: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Otras pólizas de hogar (otro ramo) del mismo cliente y dirección que solapan el periodo pendiente, y la distribución
    poblacional de la razón contenidos/edificios para el mismo cliente, dirección y solape (solo filas normales)."""
    bl = load_line("buildings")
    co = load_line("contents")
    bl = bl[(bl.sum_insured > 0)]
    co = co[(co.sum_insured > 0)]
    keyb = bl[["row_id", "policy_id", "customer_id", "address_id", "period_start", "period_end", "sum_insured", "source_table"]].rename(columns={"row_id": "b_row_id", "policy_id": "b_policy_id", "period_start": "b_start", "period_end": "b_end", "sum_insured": "b_capital", "source_table": "b_source"})
    keyc = co[["row_id", "policy_id", "customer_id", "address_id", "period_start", "period_end", "sum_insured", "source_table"]].rename(columns={"row_id": "c_row_id", "policy_id": "c_policy_id", "period_start": "c_start", "period_end": "c_end", "sum_insured": "c_capital", "source_table": "c_source"})
    pairs = keyc.merge(keyb, on=["customer_id", "address_id"], how="inner")
    pairs = pairs[(pairs.c_start <= pairs.b_end) & (pairs.c_end >= pairs.b_start)]
    normal = pairs[(pairs.c_capital <= THR["contents"]) & (pairs.b_capital <= THR["buildings"])]
    normal_ratio = normal.c_capital / normal.b_capital
    population = {"pairs_same_customer_address_overlap_normal": int(len(normal)),
                  "contents_over_buildings_ratio_quantiles": {str(q): float(v) for q, v in normal_ratio.quantile([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).items()}}
    rows = []
    for _, cur in focus.iterrows():
        if cur.line == "contents":
            o = pairs[pairs.c_row_id.eq(cur.row_id)]
            for _, r in o.iterrows():
                ratio = (cur.sum_insured / 1000) / r.b_capital if r.b_capital <= THR["buildings"] else np.nan
                rows.append({"focus_row_id": cur.row_id, "policy_id": cur.policy_id, "line": cur.line, "hypothetical_CU": float(cur.sum_insured / 1000), "other_policy_id": r.b_policy_id, "other_line": "buildings",
                             "other_row_id": r.b_row_id, "other_source_table": r.b_source, "other_period_start": r.b_start, "other_capital_CU": float(r.b_capital), "other_extreme": bool(r.b_capital > THR["buildings"]),
                             "ratio_contents_over_buildings_hypothetical": ratio, "ratio_recorded": float(cur.sum_insured / r.b_capital) if r.b_capital <= THR["buildings"] else np.nan,
                             "percentile_in_population": float((normal_ratio < ratio).mean()) if not np.isnan(ratio) else np.nan})
        else:
            o = pairs[pairs.b_row_id.eq(cur.row_id)]
            for _, r in o.iterrows():
                ratio = r.c_capital / (cur.sum_insured / 1000) if r.c_capital <= THR["contents"] else np.nan
                rows.append({"focus_row_id": cur.row_id, "policy_id": cur.policy_id, "line": cur.line, "hypothetical_CU": float(cur.sum_insured / 1000), "other_policy_id": r.c_policy_id, "other_line": "contents",
                             "other_row_id": r.c_row_id, "other_source_table": r.c_source, "other_period_start": r.c_start, "other_capital_CU": float(r.c_capital), "other_extreme": bool(r.c_capital > THR["contents"]),
                             "ratio_contents_over_buildings_hypothetical": ratio, "ratio_recorded": float(r.c_capital / cur.sum_insured) if r.c_capital <= THR["contents"] else np.nan,
                             "percentile_in_population": float((normal_ratio < ratio).mean()) if not np.isnan(ratio) else np.nan})
    return pd.DataFrame(rows), population


# ----------------------------------------------------------------------------- evaluación por fila
def evaluate(focus: pd.DataFrame, hist: pd.DataFrame, refs: pd.DataFrame, claims: pd.DataFrame) -> pd.DataFrame:
    rows = []
    claims_bad = set(claims.loc[claims.incurred_above_hypothetical_capital, "assigned_row_id"].dropna())
    for _, cur in focus.iterrows():
        r = refs[refs.focus_row_id.eq(cur.row_id)]
        rn = r[r.reference_normal]
        grp = hist[hist.policy_id.eq(cur.policy_id)].sort_values("period_start").reset_index(drop=True)
        i = int(grp.index[grp.row_id.eq(cur.row_id)][0])
        prev_row = grp.iloc[i - 1] if i > 0 else None
        next_row = grp.iloc[i + 1] if i + 1 < len(grp) else None
        reasons = sorted({reason_for(ref) for _, ref in rn.iterrows()})
        compat = rn[rn.compatible_known_context]
        contradictions = rn[rn.contradiction_known_context]
        tw_compat = rn[rn.compatible_tw_alias]
        move_compat = rn[rn.compatible_move_contents]
        # ampliación con error de escala (contenidos): sigue, sin hueco y con el mismo contador, a un periodo normal en la misma dirección
        prev_contig = previous_contiguous(hist, cur.policy_id, cur)
        follows_mtc = bool(prev_contig is not None and 0 < prev_contig.sum_insured <= THR[cur.line])
        endorse_ratio = float((cur.sum_insured / 1000) / prev_contig.sum_insured) if follows_mtc else np.nan
        prev_ctx_equal = False
        if follows_mtc:
            pr = rn[rn.reference_row_id.eq(prev_contig.row_id)]
            prev_ctx_equal = bool(len(pr) and pr.known_fields_equal.iloc[0])
        reversion_ratio = np.nan
        if follows_mtc and next_row is not None and next_row.address_id == cur.address_id and 0 < next_row.sum_insured <= THR[cur.line]:
            reversion_ratio = float(next_row.sum_insured / prev_contig.sum_insured)
        endorse_ok = cur.line == "contents" and follows_mtc and prev_ctx_equal and ENDORSE_BAND[0] <= endorse_ratio <= ENDORSE_BAND[1]
        endorse_sandwich = endorse_ok and not np.isnan(reversion_ratio) and BAND[0] <= reversion_ratio <= BAND[1]
        # base con ampliación adyacente: compatible + todas las contradicciones son periodos ampliados
        all_contr_endorsed = bool(len(contradictions)) and bool(contradictions.endorsed_reference.all())
        base_with_endorsement = bool(len(compat)) and all_contr_endorsed
        # cadena: referencia corregida (CAP01 o rama) en ventana y ancla original normal a más de 400 días y hasta dos años
        corr_refs = r[(r.reference_cap01_corrected | r.reference_branch_corrected) & r.in_window & r.known_fields_equal & r.same_address]
        anchors = rn[rn.known_fields_equal & rn.within_two_years & rn.same_address & ~rn.in_window & rn.in_band]
        chain_ok = False
        chain_detail = None
        if len(corr_refs) and len(anchors):
            c01 = corr_refs.sort_values("start_gap_days").iloc[0]
            an = anchors.sort_values("start_gap_days").iloc[0]
            step1 = c01.reference_corrected_capital_CU / an.reference_capital_CU
            step2 = (cur.sum_insured / 1000) / c01.reference_corrected_capital_CU
            chain_ok = BAND[0] <= step1 <= BAND[1] and BAND[0] <= step2 <= BAND[1] and BAND[0] <= an.ratio_hypothetical_over_reference <= BAND[1]
            chain_detail = {"anchor_row_id": an.reference_row_id, "anchor_gap_days": int(an.start_gap_days), "anchor_capital_CU": float(an.reference_capital_CU), "intermediate_row_id": c01.reference_row_id,
                            "intermediate_corrected_by": c01.reference_corrected_by, "intermediate_corrected_CU": float(c01.reference_corrected_capital_CU), "ratio_intermediate_over_anchor": float(step1),
                            "ratio_focus_over_intermediate": float(step2), "ratio_focus_over_anchor": float(an.ratio_hypothetical_over_reference)}
        # propuesta primaria por prioridad
        compat_strict = compat[compat.unknown_fields.eq("")]
        if cur.row_id in claims_bad:
            proposal, hold = None, "siniestro_por_encima_del_capital_hipotetico"
        elif len(compat) and not len(contradictions):
            # compatible salvo por un campo nulo: es el caso de NUL01-R (D63); si además hay referencia t/w completa, TW01-R la cubre con contexto completo
            proposal, hold = ("D34_estricto", "") if len(compat_strict) else (("TW01-R", "") if len(tw_compat) else ("NUL01-R", ""))
        elif base_with_endorsement:
            proposal, hold = "END02-R", ""
        elif len(compat) and len(contradictions):
            proposal, hold = None, "referencia_contradictoria_no_ampliada"
        elif len(move_compat):
            proposal, hold = "MOV01-R", ""
        elif endorse_ok:
            proposal, hold = "END01-R", ""
        elif len(tw_compat):
            proposal, hold = "TW01-R", ""
        elif chain_ok:
            proposal, hold = "CHAIN01-R", ""
        elif follows_mtc and cur.line == "contents":
            proposal, hold = None, "ampliacion_fuera_de_banda"
        else:
            proposal, hold = None, "sin_referencia_en_la_poliza" if not len(rn) or all(x.startswith("otra_direccion") for x in reasons) else "sin_criterio"
        # referencia elegida
        chosen = None
        if proposal in ("END02-R", "D34_estricto", "NUL01-R"):
            chosen = compat.sort_values(["direction", "start_gap_days"], ascending=[False, True]).iloc[0]
        elif proposal == "MOV01-R":
            chosen = move_compat.sort_values(["direction", "start_gap_days"], ascending=[False, True]).iloc[0]
        elif proposal == "END01-R":
            chosen = rn[rn.reference_row_id.eq(prev_row.row_id)].iloc[0]
        elif proposal == "TW01-R":
            chosen = tw_compat.sort_values(["direction", "start_gap_days"], ascending=[False, True]).iloc[0]
        elif proposal == "CHAIN01-R":
            chosen = anchors.sort_values("start_gap_days").iloc[0]
        rows.append({
            "row_id": cur.row_id, "policy_id": cur.policy_id, "group": cur.review_group, "line": cur.line, "source_table": cur.source_table, "year": int(cur.year),
            "period_start": cur.period_start, "period_end": cur.period_end, "covered_days": int(cur.covered_days), "original_capital_CU": float(cur.sum_insured), "hypothetical_CU": float(cur.sum_insured / 1000),
            "history_rows": int(len(grp)), "extreme_rows_in_policy": int(grp.extreme.sum()), "addresses_in_policy": int(grp.address_id.nunique()),
            "n_normal_references": int(len(rn)), "reasons": "; ".join(reasons), "n_compatible_known": int(len(compat)), "n_contradictions": int(len(contradictions)),
            "n_contradictions_endorsed": int(contradictions.endorsed_reference.sum()) if len(contradictions) else 0,
            "n_compatible_tw": int(len(tw_compat)), "n_compatible_move_contents": int(len(move_compat)),
            "follows_mid_term_change": follows_mtc, "endorsement_ratio_hypothetical_over_prior": endorse_ratio, "reversion_next_over_prior": reversion_ratio,
            "endorsement_sandwich": endorse_sandwich, "chain_cap01": chain_ok, "chain_intermediate_corrected_by": chain_detail["intermediate_corrected_by"] if chain_detail else None, "chain_detail": json.dumps(jsonable(chain_detail), ensure_ascii=False) if chain_detail else None,
            "proposal": proposal, "hold": hold, "test2025_row": bool(cur.test2025),
            "chosen_reference_row_id": chosen.reference_row_id if chosen is not None else None,
            "chosen_direction": chosen.direction if chosen is not None else None,
            "chosen_gap_days": int(chosen.start_gap_days) if chosen is not None else None,
            "chosen_reference_capital_CU": float(chosen.reference_capital_CU) if chosen is not None else None,
            "chosen_ratio": float(chosen.ratio_hypothetical_over_reference) if chosen is not None else None,
            "chosen_reference_test2025": bool(chosen.reference_test2025) if chosen is not None else None,
            "chosen_same_address": bool(chosen.same_address) if chosen is not None else None,
            "unknown_fields_chosen": chosen.unknown_fields if chosen is not None else None,
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- casos
def pick_cases(ev: pd.DataFrame, hist: pd.DataFrame, claims: pd.DataFrame, refs: pd.DataFrame) -> list[dict]:
    chosen, used = [], set()

    def take(mask, key, title, why):
        sub = ev[mask & ~ev.row_id.isin(used)]
        if len(sub):
            row = sub.sort_values("row_id").iloc[0]
            used.add(row.row_id)
            chosen.append({"key": key, "row_id": row.row_id, "policy_id": row.policy_id, "title": title, "why": why})

    take(ev.proposal.eq("MOV01-R") & ev.chosen_direction.eq("prior"), "R01", "Contenidos con mudanza: el capital viaja con el cliente", "El periodo extremo está en la nueva dirección; el anterior, en la antigua, tiene exactamente el mismo capital que el hipotético.")
    take(ev.proposal.eq("MOV01-R") & ev.chosen_direction.eq("later"), "R02", "Contenidos con mudanza y apoyo posterior", "La única referencia está en la dirección siguiente; en contenidos la mudanza no cambia el capital.")
    take(ev.proposal.eq("END01-R") & ev.endorsement_sandwich, "R03", "Ampliación a mitad de año con error de escala y vuelta al nivel base", "El periodo pendiente sigue a un mid_term_change: dividido entre mil queda un 20–60 % por encima del nivel previo, como toda ampliación del archivo, y la renovación siguiente vuelve al nivel base indexado.")
    take(ev.proposal.eq("END01-R") & ~ev.endorsement_sandwich & ~ev.test2025_row, "R04", "Ampliación con error de escala sin periodo posterior", "Mismo patrón, pero la póliza termina en ese periodo (lapsed o cancelled): no hay renovación que confirme la vuelta al nivel base.")
    take(ev.proposal.eq("END01-R") & ev.test2025_row, "R04b", "Ampliación con error de escala en test 2025", "En test no existe la etiqueta mid_term_change; la ampliación se reconoce por la firma estructural: periodo contiguo, misma dirección y mismo contador de renovaciones, que en entrenamiento coincide con la etiqueta en el 100 % de los casos.")
    take(ev.proposal.eq("END02-R") & ev.group.eq("A_retrospective_D34"), "R05", "C48613718: nivel base con error de escala y ampliación adyacente", "La discrepancia de D51 es un tramo ampliado de 2022; las renovaciones de 2022 y 2024 encajan con el capital dividido entre mil.")
    take(ev.proposal.eq("END02-R"), "R06", "Nivel base con error de escala y ampliación adyacente", "El patrón de las dos pólizas de D60: la referencia que contradice es un tramo ampliado; las demás renovaciones encajan.")
    take(ev.proposal.eq("TW01-R"), "R07", "Alias T/W: el único cambio es el código de construcción", "El periodo extremo lleva el código t de 2021–2022 y la referencia el w de 2023 en adelante; en todo el archivo ese cambio no altera el capital.")
    take(ev.proposal.eq("TW01-R") & (ev.addresses_in_policy > 1), "R08", "Alias T/W con mudanza en la historia", "Hay referencias en otra dirección, que no cuentan, y una en la misma dirección que solo difiere en t/w.")
    take(ev.proposal.eq("CHAIN01-R") & ev.chain_intermediate_corrected_by.eq("CAP01"), "R09", "Apoyo a través de una corrección CAP01 con ancla original a dos años", "La referencia próxima es la fila de 2024 ya corregida por CAP01; el ancla original de 2023 está a 731 días y cada paso de la cadena queda en banda.")
    take(ev.proposal.eq("CHAIN01-R") & ev.chain_intermediate_corrected_by.eq("rama"), "R09b", "Apoyo a través de una corrección de la rama con ancla original", "Dos periodos extremos consecutivos tras una mudanza: el segundo ya fue corregido por la rama con apoyo posterior; el primero encaja con esa corrección y con el ancla original de 2024.")
    take(ev.hold.eq("sin_referencia_en_la_poliza") & ev.line.eq("buildings") & (ev.addresses_in_policy > 1), "R10", "Edificios con mudanza: no hay referencia comparable", "El inmueble anterior tiene otro capital; en edificios la mudanza recalcula el capital en el 86 % de los casos.")
    take(ev.group.eq("C_no_original_normal_reference") & ev.test2025_row & ev.line.eq("buildings") & ev.history_rows.eq(1), "R11", "Sin historia: póliza de un solo periodo en test 2025 (edificios)", "No hay nada en la póliza con qué comparar; solo la distribución, la prima y la póliza vecina del mismo cliente dan contexto.")
    take(ev.group.eq("C_no_original_normal_reference") & ev.line.eq("contents"), "R12", "Sin historia: póliza de un solo periodo (contenidos)", "Mismo caso en contenidos; si existe una póliza de edificios del mismo cliente y dirección, la razón contenidos/edificios dice si el valor dividido entre mil es verosímil.")
    take(ev.group.eq("C_no_original_normal_reference") & (ev.extreme_rows_in_policy > 1), "R13", "Dos periodos y los dos fuera de escala", "La única póliza del grupo C con dos periodos: ambos extremos, sin ningún capital normal en la historia.")
    take(ev.hold.eq("referencia_contradictoria_no_ampliada"), "R14", "Contradicción que no es una ampliación", "Hay referencia compatible y otra que contradice sin el patrón de ampliación; se retiene.")
    cases = []
    for c in chosen:
        h = hist[hist.policy_id.eq(c["policy_id"])]
        cl = claims[claims.policy_id.eq(c["policy_id"])]
        row = ev[ev.row_id.eq(c["row_id"])].iloc[0]
        c.update({"group": row.group, "line": row.line, "proposal": row.proposal, "hold": row.hold, "reasons": row.reasons,
                  "chosen_reference_row_id": row.chosen_reference_row_id, "chosen_direction": row.chosen_direction, "chosen_ratio": row.chosen_ratio,
                  "endorsement_ratio": row.endorsement_ratio_hypothetical_over_prior, "reversion_ratio": row.reversion_next_over_prior, "chain_detail": row.chain_detail,
                  "history": [jsonable({k: (h_row[k] if not pd.isna(h_row[k]) else None) for k in
                                        ["row_id", "source_table", "period_start", "period_end", "exposure", "sum_insured", "base_capital", "branch_capital", "address_id", "renewal_decision", "renewal_count", "new_business", "written_premium"] + FIELDS[row.line][2:]})
                              for _, h_row in h.iterrows()],
                  "claims": [jsonable({k: (cl_row[k] if not pd.isna(cl_row[k]) else None) for k in ["claim_id", "peril", "loss_date", "status", "incurred_to_date", "recoveries", "assigned_row_id"]}) for _, cl_row in cl.iterrows()]})
        cases.append(c)
    return cases


# ----------------------------------------------------------------------------- principal
def main() -> None:
    started = datetime.now(timezone.utc)
    checks = Checks()
    inp = load_inputs()
    out = HERE / "runs" / (started.strftime("rest_%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    (out / "tables").mkdir(parents=True, exist_ok=False)

    provenance = {"originals_sha256": {p.stem: digest(p) for p in sorted(RAW.glob("*.parquet"))}}
    cat_orig = {k: v["sha256"] for k, v in inp["base_cat"].items() if v.get("layer") == "original_unchanged"}
    checks.add("P01", "las tablas originales sin derivar conservan el hash del catálogo base", all(provenance["originals_sha256"][k] == h for k, h in cat_orig.items()), observed=sorted(cat_orig))
    provenance["inputs_sha256"] = {"current_retrospective_dataset.json": digest(LIMP / "current_retrospective_dataset.json"), "current_dataset.json": digest(LIMP / "current_dataset.json"),
                                   "retrospective_pending_capitals": digest(inp["retro_run"] / "tables/pending_capitals.parquet"),
                                   "retrospective_cumulative_ledger": digest(inp["retro_run"] / "ledger/cumulative_retrospective_changes.parquet")}
    provenance["retrospective_run"] = inp["retro_idx"]["workspace_relative_run"]
    provenance["retrospective_status"] = inp["retro_idx"]["status"]
    provenance["base_run"] = inp["base_idx"]["workspace_relative_run"]

    pending = inp["pending"]
    cohort = pending[~pending.review_group.eq("F_incomplete_context")].copy()
    groups = cohort.review_group.value_counts().to_dict()
    checks.add("K01", "la cohorte son los pendientes de la rama activa fuera del grupo F: 138 G, 108 C, 16 E, 2 D y 1 A",
               groups == {"G_other_conflicts": 138, "C_no_original_normal_reference": 108, "E_TW_dependency": 16, "D_CAP01_dependency_only": 2, "A_retrospective_D34": 1}, observed=groups)
    ctx_info = None
    if inp["ctx_run"] is not None and (inp["ctx_run"] / "evidencia.json").is_file():
        ctx_ev = json.loads((inp["ctx_run"] / "evidencia.json").read_text("utf-8"))
        ctx_info = {"run": inp["ctx_run"].name, "cohort_rows": ctx_ev["cohort"]["rows"], "cohort_sha256": ctx_ev["cohort"]["sha256_sorted_row_ids"]}
        checks.add("K02", "junto con las 154 del grupo F revisadas en D63, la cohorte completa los pendientes de la rama", len(cohort) + ctx_ev["cohort"]["rows"] == len(pending), expected=len(pending), observed=len(cohort) + ctx_ev["cohort"]["rows"])
    cohort_hash = hashlib.sha256("\n".join(sorted(cohort.row_id)).encode()).hexdigest()
    focus_ids = set(cohort.row_id)
    pols = sorted(cohort.policy_id.unique())

    hist = read_histories(pols, inp["base_cat"], inp["retro_cat"])
    hist["focus"] = hist.row_id.isin(focus_ids)
    focus = hist[hist.focus].merge(cohort[["row_id", "review_group", "group_label"]], on="row_id", how="left")
    checks.add("H01", "cada fila pendiente se encuentra en los originales y la dirección y el cliente están siempre informados",
               len(focus) == len(cohort) and not hist.address_id.isna().any() and not hist.customer_id.isna().any(), observed={"filas": int(len(focus)), "periodos": int(len(hist)), "polizas": int(hist.policy_id.nunique())})
    checks.add("H02", "en estas pólizas hay 269 periodos extremos (265 pendientes y 4 ya corregidos por CAP01 o la rama) y 3 filas corregidas por CAP01",
               int(hist.extreme.sum()) == 269 and int(hist.cap01_corrected.sum()) == 3, observed={"extremos": int(hist.extreme.sum()), "cap01": int(hist.cap01_corrected.sum()), "rama": int(hist.branch_corrected.sum())})

    gstats = global_statistics(checks)
    refs = build_references(hist, focus_ids)
    claims = claims_for(hist, inp["base_cat"])
    neighbours, population = neighbour_policies(focus)
    ev = evaluate(focus, hist, refs, claims)

    # --- comprobaciones de estructura
    rn = refs[refs.reference_normal]
    per_focus_reasons = ev.set_index("row_id").reasons
    strict_ids = set(rn.loc[rn.compatible_known_context & rn.unknown_fields.eq(""), "focus_row_id"])
    with_strict = ev[ev.row_id.isin(strict_ids)]
    checks.add("R01", "toda fila con una referencia compatible de contexto completo tiene además una referencia contradictoria (por eso D48 no la dejó en el grupo A); ninguna fila cumple D34 sin conflicto",
               bool((with_strict.n_contradictions > 0).all()) and int(ev.proposal.eq("D34_estricto").sum()) == 0,
               observed={"con_compatible_completa": int(len(with_strict)), "de_ellas_con_contradiccion": int((with_strict.n_contradictions > 0).sum()), "D34_estricto_sin_conflicto": int(ev.proposal.eq("D34_estricto").sum())})
    C = ev[ev.group.eq("C_no_original_normal_reference")]
    checks.add("R02", "las 108 del grupo C no tienen ninguna referencia original con capital normal", bool((C.n_normal_references == 0).all()), observed=int((C.n_normal_references == 0).sum()))
    G = ev[ev.group.eq("G_other_conflicts")]
    g_moves = G[G.reasons.str.fullmatch("otra_direccion(_y_otros_campos)?(; otra_direccion(_y_otros_campos)?)*")]
    checks.add("R03", "en el grupo G, 88 filas tienen todas sus referencias en otra dirección y 48 tienen un conflicto numérico con contexto igual",
               len(g_moves) == 88 and int(G.reasons.str.contains("razon").sum()) == 48, observed={"solo_otra_direccion": int(len(g_moves)), "conflicto_numerico": int(G.reasons.str.contains("razon").sum())})
    checks.add("R04", "las 47 mudanzas de contenidos del grupo G tienen razón exactamente 1 frente al periodo de la otra dirección",
               int((G.proposal.eq("MOV01-R")).sum()) >= 47 and bool(ev.loc[ev.proposal.eq("MOV01-R"), "chosen_ratio"].round(6).eq(1.0).all()), observed={"MOV01": int(G.proposal.eq("MOV01-R").sum()), "razones": sorted(set(ev.loc[ev.proposal.eq("MOV01-R"), "chosen_ratio"].round(4)))})
    checks.add("R05", "todas las filas END01-R siguen a un mid_term_change en la misma dirección y su razón frente al nivel previo queda en la banda empírica de ampliación 1,15–1,65",
               bool(ev.loc[ev.proposal.eq("END01-R"), "endorsement_ratio_hypothetical_over_prior"].between(*ENDORSE_BAND).all()),
               observed={str(q): float(v) for q, v in ev.loc[ev.proposal.eq("END01-R"), "endorsement_ratio_hypothetical_over_prior"].quantile([0, 0.5, 1]).round(4).items()})
    checks.add("R06", "en todas las filas END02-R la referencia que contradice es un periodo ampliado (sigue a un mid_term_change con subida 1,15–1,65) y existe otra compatible",
               bool((ev.loc[ev.proposal.eq("END02-R"), "n_contradictions"] == ev.loc[ev.proposal.eq("END02-R"), "n_contradictions_endorsed"]).all()) and bool((ev.loc[ev.proposal.eq("END02-R"), "n_compatible_known"] >= 1).all()),
               observed=int(ev.proposal.eq("END02-R").sum()))
    checks.add("R07", "todas las filas TW01-R tienen una referencia en la misma dirección que solo difiere en el código t/w, con razón en banda y ventana 1–400",
               bool(ev.loc[ev.proposal.eq("TW01-R"), "chosen_ratio"].between(*BAND).all()) and bool(ev.loc[ev.proposal.eq("TW01-R"), "chosen_same_address"].all()), observed=int(ev.proposal.eq("TW01-R").sum()))
    checks.add("R08", "las filas CHAIN01-R tienen ancla original a más de 400 días y hasta dos años en la misma dirección, una fila intermedia corregida (CAP01 o rama) y cada paso de la cadena en banda",
               bool(ev.loc[ev.proposal.eq("CHAIN01-R"), "chain_cap01"].all()) and int(ev.proposal.eq("CHAIN01-R").sum()) >= 2,
               observed=[json.loads(x) for x in ev.loc[ev.proposal.eq("CHAIN01-R"), "chain_detail"]])
    checks.add("R09", "ningún siniestro aceptado de un periodo pendiente supera el capital hipotético (capital/1000)", int(claims.incurred_above_hypothetical_capital.sum()) == 0, expected=0, observed=int(claims.incurred_above_hypothetical_capital.sum()))
    checks.add("R10", "el capital hipotético de todas las filas queda dentro del rango normal de su ramo", bool(all(h <= THR[l] for h, l in zip(ev.hypothetical_CU, ev.line))), observed={"max_edificios": float(ev.loc[ev.line.eq("buildings"), "hypothetical_CU"].max()), "max_contenidos": float(ev.loc[ev.line.eq("contents"), "hypothetical_CU"].max())})
    checks.add("R11", "la razón de la referencia elegida queda en banda en todas las candidatas MOV01-R, END02-R, TW01-R y CHAIN01-R", bool(ev.loc[ev.proposal.isin(["MOV01-R", "END02-R", "TW01-R", "CHAIN01-R"]), "chosen_ratio"].between(*BAND).all()),
               observed={str(q): float(v) for q, v in ev.loc[ev.proposal.isin(["MOV01-R", "END02-R", "TW01-R", "CHAIN01-R"]), "chosen_ratio"].quantile([0, 0.5, 1]).round(4).items()})

    # --- resumen por grupo y propuesta
    summary = {
        "by_group": {g: {"rows": int(len(s)), "by_line": s.line.value_counts().to_dict(), "by_source_table": s.source_table.value_counts().to_dict(),
                         "test2025_rows": int(s.test2025_row.sum()), "proposals": s.proposal.fillna("ninguna").value_counts().to_dict(), "holds": s.hold.replace("", np.nan).dropna().value_counts().to_dict(),
                         "reasons": s.reasons.value_counts().to_dict()} for g, s in ev.groupby("group")},
        "by_proposal": {p: {"rows": int(len(s)), "by_group": s.group.value_counts().to_dict(), "by_line": s.line.value_counts().to_dict(), "test2025_rows": int(s.test2025_row.sum()),
                            "prior_supported": int(s.chosen_direction.eq("prior").sum()), "later_supported": int(s.chosen_direction.eq("later").sum()),
                            "reference_test2025": int(s.chosen_reference_test2025.fillna(False).astype(bool).sum()),
                            "ratio_quantiles": {str(q): float(v) for q, v in s.chosen_ratio.quantile([0, 0.5, 1]).round(4).items()} if s.chosen_ratio.notna().any() else None,
                            "sum_original_CU": float(s.original_capital_CU.sum()), "sum_hypothetical_CU": float(s.hypothetical_CU.sum())} for p, s in ev[ev.proposal.notna()].groupby("proposal")},
        "without_proposal": {h: {"rows": int(len(s)), "by_group": s.group.value_counts().to_dict(), "by_line": s.line.value_counts().to_dict(), "test2025_rows": int(s.test2025_row.sum())} for h, s in ev[ev.proposal.isna()].groupby("hold")},
        "END01_sandwich": int((ev.proposal.eq("END01-R") & ev.endorsement_sandwich).sum()),
        "END01_without_next": int((ev.proposal.eq("END01-R") & ~ev.endorsement_sandwich).sum()),
        "endorsement_ratio_quantiles_END01": {str(q): float(v) for q, v in ev.loc[ev.proposal.eq("END01-R"), "endorsement_ratio_hypothetical_over_prior"].quantile([0, 0.25, 0.5, 0.75, 1]).round(4).items()},
        "reversion_ratio_quantiles_END01": {str(q): float(v) for q, v in ev.loc[ev.proposal.eq("END01-R"), "reversion_next_over_prior"].dropna().quantile([0, 0.5, 1]).round(4).items()},
        "contradiction_ratio_quantiles_END02": {str(q): float(v) for q, v in rn.loc[rn.contradiction_known_context & rn.focus_row_id.isin(ev.loc[ev.proposal.eq("END02-R"), "row_id"]), "ratio_hypothetical_over_reference"].quantile([0, 0.5, 1]).round(4).items()},
        "no_reference_rows": int(ev.hold.eq("sin_referencia_en_la_poliza").sum()),
        "no_reference_by_line": ev.loc[ev.hold.eq("sin_referencia_en_la_poliza"), "line"].value_counts().to_dict(),
        "no_reference_by_source_table": ev.loc[ev.hold.eq("sin_referencia_en_la_poliza"), "source_table"].value_counts().to_dict(),
        "no_reference_test2025_rows": int((ev.hold.eq("sin_referencia_en_la_poliza") & ev.test2025_row).sum()),
    }
    # grupo sin referencia: percentil del capital hipotético en la distribución normal del ramo y vecinas
    no_ref = ev[ev.hold.eq("sin_referencia_en_la_poliza")]
    pct = {}
    for line in ["buildings", "contents"]:
        normal = load_line(line)
        normal = normal.loc[(normal.sum_insured > 0) & (normal.sum_insured <= THR[line]), "sum_insured"]
        sub = no_ref[no_ref.line.eq(line)]
        p = sub.hypothetical_CU.map(lambda v: float((normal < v).mean()))
        pct[line] = {"rows": int(len(sub)), "hypothetical_min_CU": float(sub.hypothetical_CU.min()) if len(sub) else None, "hypothetical_max_CU": float(sub.hypothetical_CU.max()) if len(sub) else None,
                     "normal_max_CU": float(normal.max()), "percentile_of_hypothetical_in_normal_distribution_quantiles": {str(q): float(v) for q, v in p.quantile([0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]).round(3).items()} if len(sub) else None}
    nb = neighbours[neighbours.focus_row_id.isin(no_ref.row_id)] if len(neighbours) else neighbours
    neighbour_summary = {"population": population, "no_reference_rows_with_neighbour": int(nb.focus_row_id.nunique()) if len(nb) else 0,
                         "neighbour_extreme_rows": int(nb.other_extreme.sum()) if len(nb) else 0,
                         "percentile_quantiles_hypothetical": {str(q): float(v) for q, v in nb.percentile_in_population.dropna().quantile([0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]).round(3).items()} if len(nb) else None,
                         "share_within_population_p05_p95": float(nb.percentile_in_population.dropna().between(0.05, 0.95).mean()) if len(nb) else None,
                         "recorded_ratio_quantiles": {str(q): float(v) for q, v in nb.ratio_recorded.dropna().quantile([0, 0.5, 1]).round(3).items()} if len(nb) else None}
    checks.add("R12", "en las filas sin referencia con póliza vecina del otro ramo, la razón contenidos/edificios con el capital dividido entre mil cae en el 90 % central de la población en la mayoría de los casos",
               (neighbour_summary["share_within_population_p05_p95"] or 0) > 0.8, observed=neighbour_summary["share_within_population_p05_p95"])

    # --- prima diagnóstica
    premium = {}
    for line in ["buildings", "contents"]:
        f = focus[focus.line.eq(line) & (focus.exposure > 0)]
        t = pq.read_table(RAW / f"policies_{line}.parquet", columns=["sum_insured", "written_premium", "exposure"]).to_pandas()
        n = t[(t.sum_insured > 0) & (t.sum_insured <= THR[line]) & (t.exposure > 0)]
        ff = f[f.exposure >= 0.95]
        premium[line] = {"normal_rows_premium_per_1000_capital_quantiles": {str(q): float(v) for q, v in (n.written_premium / n.exposure / n.sum_insured * 1000).quantile([0.05, 0.25, 0.5, 0.75, 0.95]).round(3).items()},
                         "normal_full_year_rows_premium_per_1000_capital_quantiles": {str(q): float(v) for q, v in (n[n.exposure >= 0.95].written_premium / n[n.exposure >= 0.95].sum_insured * 1000).quantile([0.05, 0.25, 0.5, 0.75, 0.95]).round(3).items()},
                         "focus_premium_per_1000_hypothetical_capital_quantiles": {str(q): float(v) for q, v in (f.written_premium / f.exposure / (f.sum_insured / 1000) * 1000).quantile([0.05, 0.25, 0.5, 0.75, 0.95]).round(3).items()},
                         "focus_full_year_rows": int(len(ff)),
                         "focus_full_year_premium_per_1000_hypothetical_capital_quantiles": {str(q): float(v) for q, v in (ff.written_premium / (ff.sum_insured / 1000) * 1000).quantile([0.05, 0.25, 0.5, 0.75, 0.95]).round(3).items()} if len(ff) else None,
                         "focus_premium_per_1000_recorded_capital_median": float((f.written_premium / f.exposure / f.sum_insured * 1000).median()),
                         "note": "la prima escrita de un periodo corto no está prorrateada de forma documentada; la comparación útil es entre periodos de año completo"}

    cases = pick_cases(ev, hist, claims, refs)

    # --- listas congeladas (NO APLICADAS)
    cand = ev[ev.proposal.notna() & ev.proposal.ne("D34_estricto")].copy()
    cand["new_hypothetical_CU"] = cand.original_capital_CU / 1000
    cand = cand[["row_id", "policy_id", "group", "line", "source_table", "year", "period_start", "period_end", "original_capital_CU", "new_hypothetical_CU", "proposal",
                 "chosen_reference_row_id", "chosen_direction", "chosen_gap_days", "chosen_reference_capital_CU", "chosen_ratio", "chosen_reference_test2025", "chosen_same_address",
                 "unknown_fields_chosen", "endorsement_ratio_hypothetical_over_prior", "reversion_next_over_prior", "endorsement_sandwich", "chain_detail", "test2025_row"]].sort_values(["proposal", "line", "row_id"]).reset_index(drop=True)
    cand["capital_change_applied"] = False
    cand["correction_authorized"] = False
    hashes = {p: hashlib.sha256("\n".join(sorted(cand.loc[cand.proposal.eq(p), "row_id"])).encode()).hexdigest() for p in sorted(cand.proposal.unique())}
    no_ref_list = ev[ev.proposal.isna()].copy()

    tables = {
        "cohorte_265": focus[KEEP + ["source_table", "line", "year", "covered_days", "review_group", "group_label", "test2025"] + EXTRA],
        "historias": hist[KEEP + ["source_table", "line", "year", "covered_days", "base_capital", "branch_capital", "extreme", "cap01_corrected", "branch_corrected", "focus", "test2025"] + EXTRA],
        "referencias": refs, "siniestros": claims, "polizas_vecinas": neighbours, "evaluacion": ev,
        "candidatas_NO_APLICADAS": cand, "sin_propuesta": no_ref_list,
    }
    for name, frame in tables.items():
        frame.to_csv(out / "tables" / f"{name}.csv", index=False, encoding="utf-8", lineterminator="\n", date_format="%Y-%m-%d")
    pd.DataFrame(checks.rows).to_csv(out / "tables" / "controles.csv", index=False, encoding="utf-8", lineterminator="\n")

    evidence = {
        "run_id": out.name, "created_utc": started.isoformat(timespec="seconds"), "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "author": "Claude (Cowork), a solicitud del participante",
        "request": "Revisar los grupos pendientes restantes (otros conflictos 138, sin referencia 108, dependientes de T/W 16, apoyo dependiente de CAP01 2, discrepancia C48613718): historiales, casos y propuesta sin modificar los datos.",
        "scope": {"review_only": True, "data_modified": False, "indices_modified": False, "models_trained": False, "external_providers": False, "human_review": "pending", "independent_validation": False},
        "environment": {"python": platform.python_version(), "pandas": pd.__version__, "platform": platform.platform()},
        "definitions": {"D34_fields": FIELDS, "extreme_thresholds_CU": THR, "ratio_band": BAND, "start_gap_window_days": WINDOW, "endorsement_band": ENDORSE_BAND, "chain_max_days": CHAIN_MAX_DAYS,
                        "proposals": {
                            "MOV01-R": "contenidos: referencia original normal de la misma póliza y cliente en otra dirección, demás campos conocidos iguales, ventana 1–400, razón 0,90–1,10 (el capital de contenidos se conserva exactamente al mudarse)",
                            "END01-R": "contenidos: periodo que sigue a un mid_term_change en la misma dirección con contexto conocido igual; (capital/1000)/capital previo dentro de la banda empírica de ampliación 1,15–1,65; subnivel 'sandwich' cuando el periodo siguiente vuelve al nivel base (razón siguiente/previo 0,90–1,10)",
                            "END02-R": "nivel base con error de escala: existe referencia compatible (D34 con nulos como desconocidos) y toda referencia contradictoria es un periodo ampliado (sigue a un mid_term_change con subida 1,15–1,65); la ampliación se conserva",
                            "TW01-R": "edificios: referencia en la misma dirección que solo difiere en el código de construcción t/w (alias de 2023-01-01), ventana 1–400, razón 0,90–1,10",
                            "CHAIN01-R": "ancla original normal en la misma dirección a más de 400 días y hasta dos años, con una fila intermedia corregida por CAP01; razón en banda en cada paso (ancla→CAP01 corregida→fila/1000) y entre la fila/1000 y el ancla",
                            "sin_referencia": "sin ningún periodo comparable en la póliza (grupo C y mudanzas de edificios): sin propuesta de corrección; tratamiento en el modelado",
                        },
                        "priority": ["END02-R", "MOV01-R", "END01-R", "TW01-R", "CHAIN01-R"],
                        "NUL01-R": "fila con referencia compatible salvo por un campo nulo y sin contradicción: es el criterio propuesto en D63 para el grupo F; se lista aparte",
                        "holds": ["siniestro_por_encima_del_capital_hipotetico", "referencia_contradictoria_no_ampliada", "sin_referencia_en_la_poliza", "sin_criterio"]},
        "provenance": provenance,
        "cohort": {"rows": int(len(cohort)), "policies": int(cohort.policy_id.nunique()), "sha256_sorted_row_ids": cohort_hash, "groups": groups, "history_rows": int(len(hist)),
                   "pending_in_branch_total": int(len(pending)), "pending_groups_in_branch": pending.review_group.value_counts().to_dict(), "group_F_review": ctx_info},
        "global_statistics": gstats, "summary": summary, "no_reference_percentiles": pct, "neighbour_evidence": neighbour_summary, "premium_diagnostic": premium,
        "candidates_NOT_APPLIED": {"rows": int(len(cand)), "by_proposal": cand.proposal.value_counts().to_dict(), "sha256_by_proposal": hashes,
                                   "test2025_rows": int(cand.test2025_row.sum()), "prior_supported": int(cand.chosen_direction.eq("prior").sum()), "later_supported": int(cand.chosen_direction.eq("later").sum()),
                                   "sum_original_CU": float(cand.original_capital_CU.sum()), "sum_hypothetical_CU": float(cand.new_hypothetical_CU.sum())},
        "without_proposal": {"rows": int(len(no_ref_list)), "by_hold": no_ref_list.hold.value_counts().to_dict(), "by_group": no_ref_list.group.value_counts().to_dict()},
        "cases": cases,
        "checks": checks.rows,
        "checks_summary": {"checks_total": len(checks.rows), "checks_passed": sum(1 for c in checks.rows if c["passed"]), "all_passed": all(c["passed"] for c in checks.rows)},
    }
    (out / "evidencia.json").write_text(json.dumps(jsonable(evidence), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(__file__, out / Path(__file__).name)
    manifest = {str(p.relative_to(out)).replace("\\", "/"): digest(p) for p in sorted(out.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run": str(out.relative_to(ROOT)).replace("\\", "/"), "checks": evidence["checks_summary"], "candidates": cand.proposal.value_counts().to_dict(), "without_proposal": evidence["without_proposal"]["by_hold"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
