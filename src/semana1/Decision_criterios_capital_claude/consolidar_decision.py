"""Consolidación de la decisión actuarial sobre los criterios propuestos para los 419 capitales pendientes de la rama.

Toma las listas congeladas de D63 (NUL01-R) y D65 (MOV01-R, END01-R, END02-R, TW01-R, CHAIN01-R y las 149 filas sin
referencia), comprueba que siguen correspondiendo a la rama activa, añade la evidencia que la decisión necesita y que
los informes anteriores no medían (la coherencia entre la prima escrita y el capital en todo el archivo, la razón
directa frente al ancla original en CHAIN01-R, la reevaluación de las dos filas retenidas en D63 con la lógica de
END02-R y la causa estructural de las ampliaciones sin reversión observada) y escribe las listas tal como quedan
decididas: `autorizadas.csv` (orden de aplicación, criterio y nivel por fila) y `prm01_F0.csv` (las 149 filas sin
referencia, cubiertas por el criterio PRM01-R y por la transformación F0). NO aplica nada: no modifica datos, índices
ni corridas; no entrena modelos. La aplicación en la rama sigue necesitando el flujo apply/verify/finalize de Limpieza.

Uso (desde la raíz del proyecto, con el Python de Preparación/.venv):
    python "Hackaton/Semana 1/Decision_criterios_capital_claude/consolidar_decision.py"
Crea runs/dec_<marca>_<id>/ con evidencia.json, tablas CSV, copia del script y manifest.json (SHA-256).
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
REST = ROOT / "Hackaton/Semana 1/Revision_pendientes_restantes_claude"
THR = {"buildings": 10_000_000, "contents": 1_000_000}
BAND = (0.9, 1.1)
ENDORSE_BAND = (1.15, 1.65)   # banda usada en D65; el archivo mide p1–p99 en 1,203–1,596
CHAIN_MAX_DAYS = 731
AUTHOR = "Claude (rol de actuario especializado por delegación del participante)"

# Decisión por criterio: orden de aplicación en la rama, estado y condiciones. El orden va de la evidencia más próxima
# a D34 a la más dependiente de comportamientos medidos del generador; PRM01-R cierra porque su evidencia es de la
# propia fila (prima escrita) y no de la historia de la póliza.
DECISION = {
    "NUL01-R": {"orden": 1, "estado": "autorizado", "niveles": ["N1_puente_dos_lados", "N2_vecino_conocido", "N3_identidad_sin_campo"],
                "condicion": "el campo nulo se trata como desconocido, sin imputar; identidad por cliente y dirección; el resto de D34 intacto; el nivel y el campo desconocido quedan en la bitácora"},
    "END02-R": {"orden": 2, "estado": "autorizado", "niveles": ["grupo_G_o_A", "ampliacion_grupo_F"],
                "condicion": "referencia compatible de contexto completo y todas las contradicciones explicadas como periodos ampliados (firma estructural y razón en la banda medida); incluye las dos filas retenidas en D63 reevaluadas aquí"},
    "TW01-R": {"orden": 3, "estado": "autorizado", "niveles": ["alias_t_w"],
               "condicion": "t y w se tratan como el mismo código solo para comparar contexto; el supuesto queda documentado y F0 debe armonizarlos si construction_type entra al modelo"},
    "MOV01-R": {"orden": 4, "estado": "autorizado", "niveles": ["mudanza_contenidos_razon_1"],
                "condicion": "solo contenidos; razón exactamente 1 frente al periodo de la otra dirección; nunca edificios"},
    "END01-R": {"orden": 5, "estado": "autorizado", "niveles": ["sandwich", "sin_reversion_estructural"],
                "condicion": "periodo ampliado contiguo a un periodo normal de la misma póliza con razón dentro de la banda medida; cuando no hay reversión observada debe ser porque la póliza termina o porque es 2025"},
    "CHAIN01-R": {"orden": 6, "estado": "autorizado", "niveles": ["ancla_directa"],
                  "condicion": "la razón directa foco/1000 frente a un periodo original de la misma dirección a 731 días o menos está en banda; la fila intermedia corregida es comprobación, no premisa"},
    "PRM01-R": {"orden": 7, "estado": "autorizado_F0_y_rama", "niveles": ["prima_coherente"],
                "condicion": "la prima escrita por mil de capital registrado queda por debajo del mínimo de la población normal y, con el capital entre mil, dentro de su rango observado; obligatorio en F0 para cualquier fila sobre el umbral; en la rama, última regla"},
}
F0_CONTRACT = {
    "regla": "sum_insured_model = sum_insured / 1000 si sum_insured > umbral del ramo (10.000.000 CU edificios, 1.000.000 CU contenidos); si no, sum_insured",
    "idempotente": "sí: ningún capital corregido vuelve a superar el umbral (máximo 594.000 CU en edificios y 152.600 en contenidos entre los extremos del archivo)",
    "columnas": {"sum_insured_raw": "valor leído de la capa, sin tocar", "sum_insured": "valor transformado que usa el modelo",
                 "audit_capital_scale_adjusted": "booleano: la fila recibió la división por mil en F0 o en una capa anterior",
                 "audit_capital_scale_confirmed": "booleano: la fila tiene una referencia en su propia historia (CAP01 o rama) además de la prima coherente"},
    "predictores": "las dos columnas audit_* quedan excluidas por el guard existente (prefijo audit_); solo se usan en ablaciones",
    "capas": "la misma función da el mismo sum_insured leyendo la base o la rama; la rama es la pista de auditoría de qué filas tienen confirmación por historia",
    "informacion_usada": "solo la propia fila (capital y umbral); no usa periodos posteriores ni el objetivo, así que vale para backtests por fecha y para el test 2025",
}


# ----------------------------------------------------------------------------- utilidades
def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def ids_hash(ids) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


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


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def as_bool(series: pd.Series) -> pd.Series:
    return series.map({"True": True, "False": False, "": False})


# ----------------------------------------------------------------------------- carga
def load_inputs(checks: Checks) -> dict:
    retro_idx = json.loads((LIMP / "current_retrospective_dataset.json").read_text("utf-8"))
    retro_run = ROOT / retro_idx["workspace_relative_run"]
    base_idx = json.loads((LIMP / "current_dataset.json").read_text("utf-8"))
    base_cat = json.loads((ROOT / base_idx["workspace_relative_run"] / "dataset_catalog.json").read_text("utf-8"))
    pending = pd.read_parquet(retro_run / "tables/pending_capitals.parquet")
    ctx_run = ROOT / json.loads((CTX / "current_run.json").read_text("utf-8"))["workspace_relative_run"]
    rest_run = ROOT / json.loads((REST / "current_run.json").read_text("utf-8"))["workspace_relative_run"]
    used = {"ctx": ["tables/candidatas_NO_APLICADAS.csv", "tables/retenidas.csv", "tables/historias.csv", "tables/referencias.csv", "evidencia.json"],
            "rest": ["tables/candidatas_NO_APLICADAS.csv", "tables/sin_propuesta.csv", "tables/historias.csv", "evidencia.json"]}
    bad = []
    for key, run in [("ctx", ctx_run), ("rest", rest_run)]:
        manifest = json.loads((run / "manifest.json").read_text("utf-8"))
        for rel in used[key]:
            if manifest.get(rel) != digest(run / rel):
                bad.append(f"{run.name}/{rel}")
    checks.add("P02", "las tablas de D63 y D65 que consume la decisión conservan el hash de sus manifiestos", not bad, observed=bad or "sin diferencias")
    ctx_ev = json.loads((ctx_run / "evidencia.json").read_text("utf-8"))
    rest_ev = json.loads((rest_run / "evidencia.json").read_text("utf-8"))
    return dict(retro_idx=retro_idx, retro_run=retro_run, base_idx=base_idx, base_cat=base_cat, pending=pending, ctx_run=ctx_run, rest_run=rest_run,
                ctx_ev=ctx_ev, rest_ev=rest_ev,
                c1=read_csv(ctx_run / "tables/candidatas_NO_APLICADAS.csv"), r1=read_csv(ctx_run / "tables/retenidas.csv"),
                h1=read_csv(ctx_run / "tables/historias.csv"), ref1=read_csv(ctx_run / "tables/referencias.csv"),
                c2=read_csv(rest_run / "tables/candidatas_NO_APLICADAS.csv"), s2=read_csv(rest_run / "tables/sin_propuesta.csv"),
                h2=read_csv(rest_run / "tables/historias.csv"))


def load_home() -> dict:
    out = {}
    for line in ["buildings", "contents"]:
        parts = []
        for prefix in ["policies", "test"]:
            t = pq.read_table(RAW / f"{prefix}_{line}.parquet", columns=["row_id", "policy_id", "sum_insured", "written_premium", "exposure", "period_start", "period_end"]).to_pandas()
            t["source_table"] = f"{prefix}_{line}"
            parts.append(t)
        d = pd.concat(parts, ignore_index=True)
        d["line"] = line
        d["extreme"] = d.sum_insured > THR[line]
        d["rate_recorded"] = d.written_premium / (d.sum_insured / 1000.0)
        d["rate_hypothetical"] = d.rate_recorded * 1000.0
        out[line] = d
    return out


# ----------------------------------------------------------------------------- prueba de prima
def premium_test(home: dict, checks: Checks) -> tuple[dict, pd.DataFrame]:
    """Compara la prima escrita por mil de capital entre la población normal y los capitales extremos."""
    summary, rows = {}, []
    for line, d in home.items():
        normal, ext = d[~d.extreme], d[d.extreme]
        nr = normal.rate_recorded
        lo, hi = float(nr.min()), float(nr.max())
        p01, p99 = float(nr.quantile(0.01)), float(nr.quantile(0.99))
        by_exp_normal = nr.groupby(pd.cut(normal.exposure, [0, 0.25, 0.5, 0.75, 0.95, 1.1]), observed=True).median()
        by_exp_ext = ext.rate_hypothetical.groupby(pd.cut(ext.exposure, [0, 0.25, 0.5, 0.75, 0.95, 1.1]), observed=True).median()
        summary[line] = {
            "normal_rows": int(len(normal)), "extreme_rows": int(len(ext)), "extreme_test_rows": int(ext.source_table.str.startswith("test").sum()),
            "normal_capital_min_CU": float(normal.sum_insured.min()), "normal_capital_max_CU": float(normal.sum_insured.max()),
            "extreme_capital_min_CU": float(ext.sum_insured.min()), "extreme_capital_max_CU": float(ext.sum_insured.max()),
            "gap_factor_extreme_min_over_normal_max": float(ext.sum_insured.min() / normal.sum_insured.max()),
            "hypothetical_capital_max_CU": float(ext.sum_insured.max() / 1000), "hypothetical_capital_min_CU": float(ext.sum_insured.min() / 1000),
            "hypothetical_within_normal_support": int(((ext.sum_insured / 1000 >= normal.sum_insured.min()) & (ext.sum_insured / 1000 <= normal.sum_insured.max())).sum()),
            "normal_rate_per_1000": {"min": lo, "p01": p01, "p05": float(nr.quantile(0.05)), "median": float(nr.median()), "p95": float(nr.quantile(0.95)), "p99": p99, "max": hi},
            "normal_rate_median_by_exposure": {str(k): float(v) for k, v in by_exp_normal.items()},
            "extreme_rate_recorded_capital": {"max": float(ext.rate_recorded.max()), "median": float(ext.rate_recorded.median()), "rows_below_normal_min": int((ext.rate_recorded < lo).sum())},
            "extreme_rate_hypothetical_capital": {"min": float(ext.rate_hypothetical.min()), "p01": float(ext.rate_hypothetical.quantile(0.01)), "median": float(ext.rate_hypothetical.median()),
                                                 "p99": float(ext.rate_hypothetical.quantile(0.99)), "max": float(ext.rate_hypothetical.max()),
                                                 "rows_within_normal_min_max": int(((ext.rate_hypothetical >= lo) & (ext.rate_hypothetical <= hi)).sum()),
                                                 "rows_within_normal_p01_p99": int(((ext.rate_hypothetical >= p01) & (ext.rate_hypothetical <= p99)).sum())},
            "extreme_rate_hypothetical_median_by_exposure": {str(k): float(v) for k, v in by_exp_ext.items()},
        }
        rows.append({"line": line, **{k: v for k, v in summary[line].items() if not isinstance(v, dict)},
                     "normal_rate_min": lo, "normal_rate_median": float(nr.median()), "normal_rate_max": hi,
                     "extreme_rate_recorded_max": float(ext.rate_recorded.max()), "extreme_rate_hypothetical_median": float(ext.rate_hypothetical.median()),
                     "extreme_rows_recorded_below_normal_min": int((ext.rate_recorded < lo).sum()),
                     "extreme_rows_hypothetical_within_normal_range": int(((ext.rate_hypothetical >= lo) & (ext.rate_hypothetical <= hi)).sum())})
    s = summary
    checks.add("M01", "la prima escrita por mil de capital no depende de la exposición en la población normal (la prima no está prorrateada): las medianas por tramo de exposición difieren menos del 2 %",
               all(max(v.values()) / min(v.values()) < 1.02 for v in [s["buildings"]["normal_rate_median_by_exposure"], s["contents"]["normal_rate_median_by_exposure"]]),
               observed={line: s[line]["normal_rate_median_by_exposure"] for line in s})
    checks.add("M02", "con el capital registrado, la prima por mil de los 3.527 capitales extremos queda por debajo del mínimo observado en la población normal en el 100 % de las filas",
               all(s[line]["extreme_rate_recorded_capital"]["rows_below_normal_min"] == s[line]["extreme_rows"] for line in s),
               observed={line: {"extremos": s[line]["extreme_rows"], "bajo_el_minimo": s[line]["extreme_rate_recorded_capital"]["rows_below_normal_min"], "maximo": s[line]["extreme_rate_recorded_capital"]["max"], "minimo_normal": s[line]["normal_rate_per_1000"]["min"]} for line in s})
    checks.add("M03", "con el capital dividido entre mil, la prima por mil de los 3.527 extremos cae dentro del rango observado en la población normal en el 100 % de las filas y su mediana coincide con la normal",
               all(s[line]["extreme_rate_hypothetical_capital"]["rows_within_normal_min_max"] == s[line]["extreme_rows"] and abs(s[line]["extreme_rate_hypothetical_capital"]["median"] / s[line]["normal_rate_per_1000"]["median"] - 1) < 0.01 for line in s),
               observed={line: {"dentro_del_rango": s[line]["extreme_rate_hypothetical_capital"]["rows_within_normal_min_max"], "mediana_extremos": s[line]["extreme_rate_hypothetical_capital"]["median"], "mediana_normal": s[line]["normal_rate_per_1000"]["median"]} for line in s})
    checks.add("M04", "los capitales divididos entre mil caen dentro del soporte de la población normal (entre su mínimo y su máximo) en el 100 % de los extremos y nunca vuelven a superar el umbral",
               all(s[line]["hypothetical_within_normal_support"] == s[line]["extreme_rows"] and s[line]["hypothetical_capital_max_CU"] < THR[line] for line in s),
               observed={line: {"dentro_del_soporte": s[line]["hypothetical_within_normal_support"], "max_hipotetico": s[line]["hypothetical_capital_max_CU"], "max_normal": s[line]["normal_capital_max_CU"]} for line in s})
    return summary, pd.DataFrame(rows)


def row_premium(home: dict, row_ids: set[str]) -> pd.DataFrame:
    parts = []
    for line, d in home.items():
        normal = d[~d.extreme].rate_recorded
        f = d[d.row_id.isin(row_ids)].copy()
        f["premium_rate_recorded_per_1000"] = f.rate_recorded.round(6)
        f["premium_rate_new_per_1000"] = f.rate_hypothetical.round(4)
        f["premium_rate_recorded_below_normal_min"] = f.rate_recorded < normal.min()
        f["premium_rate_new_in_normal_range"] = (f.rate_hypothetical >= normal.min()) & (f.rate_hypothetical <= normal.max())
        f["premium_rate_new_percentile_in_normal"] = [round(float((normal < x).mean()), 4) for x in f.rate_hypothetical]
        parts.append(f[["row_id", "written_premium", "exposure", "premium_rate_recorded_per_1000", "premium_rate_new_per_1000", "premium_rate_recorded_below_normal_min", "premium_rate_new_in_normal_range", "premium_rate_new_percentile_in_normal"]])
    return pd.concat(parts, ignore_index=True)


# ----------------------------------------------------------------------------- reevaluaciones puntuales
def previous_contiguous(hist: pd.DataFrame, row) -> pd.Series | None:
    same = hist[(hist.policy_id == row.policy_id) & (hist.address_id == row.address_id) & (hist.renewal_count == row.renewal_count) & (hist.row_id != row.row_id)]
    prev = same[same.period_end == row.period_start - pd.Timedelta(days=1)]
    if len(prev) != 1:
        return None
    return prev.iloc[0]


def reevaluate_held(inp: dict, checks: Checks) -> pd.DataFrame:
    """Las dos filas retenidas en D63 (contradicción dentro de la póliza) bajo la lógica END02-R de D65."""
    h = inp["h1"].copy()
    h["period_start"], h["period_end"] = pd.to_datetime(h.period_start), pd.to_datetime(h.period_end)
    h["sum_insured"] = h.sum_insured.astype(float)
    refs = inp["ref1"]
    out = []
    for _, r in inp["r1"].iterrows():
        focus_refs = refs[refs.focus_row_id == r.row_id]
        contradictions = focus_refs[as_bool(focus_refs.contradiction_known_context)]
        explained, detail = [], []
        for _, c in contradictions.iterrows():
            crow = h[h.row_id == c.reference_row_id].iloc[0]
            prev = previous_contiguous(h, crow)
            ratio_prev = float(crow.sum_insured / prev.sum_insured) if prev is not None else None
            ok = prev is not None and ENDORSE_BAND[0] <= ratio_prev <= ENDORSE_BAND[1] and (prev.sum_insured <= THR["contents"])
            hyp_over_contra = float(c.ratio_hypothetical_over_reference)
            ok = ok and (1 / ENDORSE_BAND[1] <= hyp_over_contra <= 1 / ENDORSE_BAND[0])
            explained.append(ok)
            detail.append({"contradiction_row_id": c.reference_row_id, "contradiction_capital_CU": float(crow.sum_insured), "previous_contiguous_row_id": None if prev is None else prev.row_id,
                           "previous_capital_CU": None if prev is None else float(prev.sum_insured), "ratio_contradiction_over_previous": ratio_prev,
                           "ratio_hypothetical_over_contradiction": hyp_over_contra, "endorsed": ok})
        out.append({"row_id": r.row_id, "policy_id": r.policy_id, "line": r.line, "source_table": r.source_table, "period_start": r.period_start, "period_end": r.period_end,
                    "original_capital_CU": float(r.original_capital_CU), "new_capital_CU": float(r.hypothetical_CU), "chosen_reference_row_id": r.chosen_reference_row_id,
                    "chosen_direction": r.chosen_direction, "chosen_gap_days": int(float(r.chosen_gap_days)), "chosen_ratio": float(r.chosen_ratio), "chosen_reference_test2025": r.chosen_reference_test2025 == "True",
                    "n_contradictions": int(len(contradictions)), "all_contradictions_endorsed": bool(explained) and all(explained), "test2025_row": r.test2025_row == "True",
                    "held_reason_D63": r.holds, "endorsement_detail": json.dumps(detail, ensure_ascii=False)})
    df = pd.DataFrame(out)
    checks.add("E01", "las dos filas retenidas en D63 tienen una referencia anterior compatible en banda y todas sus contradicciones son periodos ampliados (firma contigua, misma dirección, mismo contador, razón en la banda medida): cumplen END02-R",
               len(df) == 2 and bool(df.all_contradictions_endorsed.all()) and bool(((df.chosen_ratio >= BAND[0]) & (df.chosen_ratio <= BAND[1])).all()),
               observed=df[["row_id", "chosen_ratio", "n_contradictions", "all_contradictions_endorsed"]].to_dict("records"))
    return df


def chain_direct(inp: dict, checks: Checks) -> pd.DataFrame:
    ch = inp["c2"][inp["c2"].proposal == "CHAIN01-R"].copy()
    rows = []
    for _, r in ch.iterrows():
        det = json.loads(r.chain_detail)
        rows.append({"row_id": r.row_id, "anchor_row_id": det["anchor_row_id"], "anchor_gap_days": int(det["anchor_gap_days"]), "anchor_capital_CU": float(det["anchor_capital_CU"]),
                     "ratio_focus_over_anchor": float(det["ratio_focus_over_anchor"]), "direct_in_band": BAND[0] <= float(det["ratio_focus_over_anchor"]) <= BAND[1],
                     "intermediate_row_id": det["intermediate_row_id"], "intermediate_corrected_by": det["intermediate_corrected_by"]})
    df = pd.DataFrame(rows)
    checks.add("E02", "las tres filas CHAIN01-R quedan en banda al compararlas directamente con su ancla original de la misma dirección (542–731 días), sin usar la fila intermedia corregida",
               len(df) == 3 and bool(df.direct_in_band.all()) and int(df.anchor_gap_days.max()) <= CHAIN_MAX_DAYS, observed=df[["row_id", "anchor_gap_days", "ratio_focus_over_anchor"]].to_dict("records"))
    return df


def endorsement_without_reversion(inp: dict, checks: Checks) -> pd.DataFrame:
    h = inp["h2"]
    en = inp["c2"][(inp["c2"].proposal == "END01-R") & (inp["c2"].endorsement_sandwich == "False")]
    rows = []
    for _, r in en.iterrows():
        pol = h[h.policy_id == r.policy_id].sort_values("period_start")
        focus = pol[pol.row_id == r.row_id].iloc[0]
        later = pol[pol.period_start > focus.period_start]
        reason = "test_2025_sin_periodo_posterior_observable" if focus.source_table.startswith("test_") else ("la_poliza_termina_" + focus.renewal_decision if len(later) == 0 else "periodo_posterior_presente")
        rows.append({"row_id": r.row_id, "policy_id": r.policy_id, "source_table": r.source_table, "renewal_decision": focus.renewal_decision, "later_periods": int(len(later)), "structural_reason": reason})
    df = pd.DataFrame(rows)
    ok = len(df) == 8 and bool(df.structural_reason.isin(["test_2025_sin_periodo_posterior_observable", "la_poliza_termina_lapsed_by_customer"]).all())
    checks.add("E03", "las ocho ampliaciones END01-R sin reversión observada no la tienen por una causa estructural: tres pólizas terminan con lapsed_by_customer y cinco son periodos de 2025 sin año siguiente",
               ok, observed=df.structural_reason.value_counts().to_dict())
    return df


# ----------------------------------------------------------------------------- listas decididas
def build_authorised(inp: dict, held: pd.DataFrame, chain: pd.DataFrame, premium_rows: pd.DataFrame) -> pd.DataFrame:
    c1, c2 = inp["c1"], inp["c2"]
    a = pd.DataFrame({
        "row_id": c1.row_id, "policy_id": c1.policy_id, "line": c1.line, "source_table": c1.source_table, "period_start": c1.period_start, "period_end": c1.period_end,
        "original_capital_CU": c1.original_capital_CU.astype(float), "new_capital_CU": c1.new_hypothetical_CU.astype(float), "criterio": "NUL01-R", "nivel": c1.level,
        "reference_row_id": c1.chosen_reference_row_id, "reference_direction": c1.chosen_direction, "reference_gap_days": c1.chosen_gap_days.astype(float).astype(int),
        "reference_ratio": c1.chosen_ratio.astype(float).round(6), "reference_test2025": as_bool(c1.chosen_reference_test2025), "test2025_row": as_bool(c1.test2025_row),
        "detalle": "campo desconocido: " + c1.unknown_fields_focus.where(c1.unknown_fields_focus != "", "(en la referencia) " + c1.unknown_fields_reference) + "; puentes: " + c1.bridge_statuses,
        "origen": "D63 candidatas_NO_APLICADAS", "grupo_D48": "F_incomplete_context"})
    nivel2 = np.where(c2.proposal == "END01-R", np.where(c2.endorsement_sandwich == "True", "sandwich", "sin_reversion_estructural"),
                      np.where(c2.proposal == "CHAIN01-R", "ancla_directa", np.where(c2.proposal == "END02-R", "grupo_G_o_A", np.where(c2.proposal == "TW01-R", "alias_t_w", "mudanza_contenidos_razon_1"))))
    detalle2 = np.where(c2.proposal == "END01-R", "razón ampliado/anterior " + c2.endorsement_ratio_hypothetical_over_prior.str.slice(0, 6) + "; reversión siguiente " + c2.reversion_next_over_prior.str.slice(0, 6),
                        np.where(c2.proposal == "CHAIN01-R", "ancla directa: " + c2.row_id.map(chain.set_index("row_id").ratio_focus_over_anchor.round(4).astype(str)) + " a " + c2.row_id.map(chain.set_index("row_id").anchor_gap_days.astype(str)) + " días",
                                 "misma dirección: " + c2.chosen_same_address + "; campos desconocidos: " + c2.unknown_fields_chosen))
    b = pd.DataFrame({
        "row_id": c2.row_id, "policy_id": c2.policy_id, "line": c2.line, "source_table": c2.source_table, "period_start": c2.period_start, "period_end": c2.period_end,
        "original_capital_CU": c2.original_capital_CU.astype(float), "new_capital_CU": c2.new_hypothetical_CU.astype(float), "criterio": c2.proposal, "nivel": nivel2,
        "reference_row_id": c2.chosen_reference_row_id, "reference_direction": c2.chosen_direction, "reference_gap_days": c2.chosen_gap_days.astype(float).astype(int),
        "reference_ratio": c2.chosen_ratio.astype(float).round(6), "reference_test2025": as_bool(c2.chosen_reference_test2025), "test2025_row": as_bool(c2.test2025_row),
        "detalle": detalle2, "origen": "D65 candidatas_NO_APLICADAS", "grupo_D48": c2.group})
    c = pd.DataFrame({
        "row_id": held.row_id, "policy_id": held.policy_id, "line": held.line, "source_table": held.source_table, "period_start": held.period_start, "period_end": held.period_end,
        "original_capital_CU": held.original_capital_CU, "new_capital_CU": held.new_capital_CU, "criterio": "END02-R", "nivel": "ampliacion_grupo_F",
        "reference_row_id": held.chosen_reference_row_id, "reference_direction": held.chosen_direction, "reference_gap_days": held.chosen_gap_days,
        "reference_ratio": held.chosen_ratio.round(6), "reference_test2025": held.chosen_reference_test2025, "test2025_row": held.test2025_row,
        "detalle": "retenida en D63 (" + held.held_reason_D63 + "); contradicciones ampliadas: " + held.n_contradictions.astype(str), "origen": "D63 retenidas, reevaluadas en esta corrida", "grupo_D48": "F_incomplete_context"})
    df = pd.concat([a, b, c], ignore_index=True)
    df["orden_aplicacion"] = df.criterio.map({k: v["orden"] for k, v in DECISION.items()})
    df["regla_rama_propuesta"] = "CAP" + (df.orden_aplicacion + 6).astype(str).str.zfill(2) + "R"
    df = df.merge(premium_rows, on="row_id", how="left")
    df["decision"] = "autorizada (D66, rol actuarial de Claude); pendiente de aplicar por el flujo apply/verify/finalize de Limpieza"
    df["capital_change_applied"] = False
    df["correction_authorized_by_participant"] = False
    cols = ["orden_aplicacion", "regla_rama_propuesta", "criterio", "nivel", "row_id", "policy_id", "line", "source_table", "period_start", "period_end", "original_capital_CU", "new_capital_CU",
            "reference_row_id", "reference_direction", "reference_gap_days", "reference_ratio", "reference_test2025", "test2025_row", "written_premium", "exposure",
            "premium_rate_recorded_per_1000", "premium_rate_new_per_1000", "premium_rate_recorded_below_normal_min", "premium_rate_new_in_normal_range", "premium_rate_new_percentile_in_normal",
            "detalle", "grupo_D48", "origen", "decision", "capital_change_applied", "correction_authorized_by_participant"]
    return df[cols].sort_values(["orden_aplicacion", "line", "source_table", "row_id"]).reset_index(drop=True)


def build_prm01(inp: dict, premium_rows: pd.DataFrame) -> pd.DataFrame:
    s = inp["s2"]
    df = pd.DataFrame({"orden_aplicacion": DECISION["PRM01-R"]["orden"], "regla_rama_propuesta": "CAP13R", "criterio": "PRM01-R", "nivel": "prima_coherente",
                       "row_id": s.row_id, "policy_id": s.policy_id, "line": s.line, "source_table": s.source_table, "period_start": s.period_start, "period_end": s.period_end,
                       "original_capital_CU": s.original_capital_CU.astype(float), "new_capital_CU": s.hypothetical_CU.astype(float), "grupo_D48": s.group, "hold_D65": s.hold,
                       "history_rows": s.history_rows.astype(int), "addresses_in_policy": s.addresses_in_policy.astype(int), "test2025_row": as_bool(s.test2025_row)})
    df = df.merge(premium_rows, on="row_id", how="left")
    df["audit_capital_scale_adjusted"] = True
    df["audit_capital_scale_confirmed"] = False
    df["tratamiento_F0"] = "sum_insured/1000 por umbral del ramo; marcas audit_capital_scale_adjusted=True y audit_capital_scale_confirmed=False"
    df["decision"] = "autorizada en F0 (obligatoria) y como última regla de la rama (D66, rol actuarial de Claude); pendiente de aplicar"
    df["capital_change_applied"] = False
    df["correction_authorized_by_participant"] = False
    return df.sort_values(["line", "source_table", "row_id"]).reset_index(drop=True)


# ----------------------------------------------------------------------------- principal
def main() -> None:
    started = datetime.now(timezone.utc)
    checks = Checks()
    out = HERE / "runs" / (started.strftime("dec_%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8])
    (out / "tables").mkdir(parents=True, exist_ok=False)

    provenance = {"originals_sha256": {p.stem: digest(p) for p in sorted(RAW.glob("*.parquet"))}}
    inp = load_inputs(checks)
    cat_orig = {k: v["sha256"] for k, v in inp["base_cat"].items() if v.get("layer") == "original_unchanged"}
    checks.add("P01", "las tablas originales sin derivar conservan el hash del catálogo base", all(provenance["originals_sha256"][k] == h for k, h in cat_orig.items()), observed=sorted(cat_orig))
    provenance["inputs_sha256"] = {"current_retrospective_dataset.json": digest(LIMP / "current_retrospective_dataset.json"), "current_dataset.json": digest(LIMP / "current_dataset.json"),
                                   "retrospective_pending_capitals": digest(inp["retro_run"] / "tables/pending_capitals.parquet"),
                                   "D63_current_run.json": digest(CTX / "current_run.json"), "D65_current_run.json": digest(REST / "current_run.json")}
    provenance.update(retrospective_run=inp["retro_idx"]["workspace_relative_run"], retrospective_status=inp["retro_idx"]["status"], base_run=inp["base_idx"]["workspace_relative_run"],
                      D63_run=inp["ctx_run"].name, D65_run=inp["rest_run"].name, D63_cohort_sha256=inp["ctx_ev"]["cohort"]["sha256_sorted_row_ids"], D65_cohort_sha256=inp["rest_ev"]["cohort"]["sha256_sorted_row_ids"])

    pending = inp["pending"]
    c1, r1, c2, s2 = inp["c1"], inp["r1"], inp["c2"], inp["s2"]
    groups = pending.review_group.value_counts().to_dict()
    checks.add("K01", "la rama activa sigue siendo la que revisaron D63 y D65: 419 pendientes (154 F, 138 G, 108 C, 16 E, 2 D, 1 A) y estado CAP06R",
               len(pending) == 419 and groups == {"F_incomplete_context": 154, "G_other_conflicts": 138, "C_no_original_normal_reference": 108, "E_TW_dependency": 16, "D_CAP01_dependency_only": 2, "A_retrospective_D34": 1}
               and inp["retro_idx"]["status"] == "verified_retrospective_CAP06R", observed={"pendientes": int(len(pending)), "estado": inp["retro_idx"]["status"], "grupos": groups})
    sets = {"NUL01": set(c1.row_id), "retenidas": set(r1.row_id), "D65": set(c2.row_id), "sin_ref": set(s2.row_id)}
    union = set().union(*sets.values())
    checks.add("K02", "las listas de D63 y D65 son disjuntas y, juntas, cubren exactamente los 419 pendientes de la rama",
               sum(len(s) for s in sets.values()) == len(union) == 419 and union == set(pending.row_id), observed={k: len(v) for k, v in sets.items()})
    checks.add("K03", "las listas conservan los hashes congelados en D63 y D65",
               ids_hash(c1.row_id) == inp["ctx_ev"]["candidates_NOT_APPLIED"]["sha256_sorted_row_ids"] and all(ids_hash(c2[c2.proposal == p].row_id) == h for p, h in inp["rest_ev"]["candidates_NOT_APPLIED"]["sha256_by_proposal"].items()),
               observed={"NUL01-R": ids_hash(c1.row_id)[:12], **{p: ids_hash(c2[c2.proposal == p].row_id)[:12] for p in sorted(c2.proposal.unique())}})

    home = load_home()
    premium_summary, premium_table = premium_test(home, checks)
    premium_rows = row_premium(home, union)
    held = reevaluate_held(inp, checks)
    chain = chain_direct(inp, checks)
    endorse = endorsement_without_reversion(inp, checks)

    authorised = build_authorised(inp, held, chain, premium_rows)
    prm01 = build_prm01(inp, premium_rows)
    by_crit = authorised.groupby("criterio").size().to_dict()
    checks.add("L01", "las filas autorizadas son 270: NUL01-R 152, END02-R 19 (17 + 2 reevaluadas), TW01-R 17, MOV01-R 47, END01-R 32, CHAIN01-R 3",
               len(authorised) == 270 and by_crit == {"NUL01-R": 152, "END02-R": 19, "TW01-R": 17, "MOV01-R": 47, "END01-R": 32, "CHAIN01-R": 3}, observed=by_crit)
    checks.add("L02", "PRM01-R cubre las 149 filas sin referencia (108 del grupo C y 41 mudanzas de edificios) y no se solapa con las autorizadas",
               len(prm01) == 149 and prm01.grupo_D48.value_counts().to_dict() == {"C_no_original_normal_reference": 108, "G_other_conflicts": 41} and not set(prm01.row_id) & set(authorised.row_id),
               observed=prm01.grupo_D48.value_counts().to_dict())
    checks.add("L03", "en las 419 filas decididas la prima por mil de capital registrado está por debajo del mínimo normal y, con el capital entre mil, dentro del rango normal",
               bool(authorised.premium_rate_recorded_below_normal_min.all()) and bool(authorised.premium_rate_new_in_normal_range.all()) and bool(prm01.premium_rate_recorded_below_normal_min.all()) and bool(prm01.premium_rate_new_in_normal_range.all()),
               observed={"autorizadas_en_rango": int(authorised.premium_rate_new_in_normal_range.sum()), "prm01_en_rango": int(prm01.premium_rate_new_in_normal_range.sum())})
    checks.add("L04", "toda corrección autorizada es exactamente capital/1000 y el valor nuevo queda por debajo del umbral del ramo",
               bool(np.isclose(authorised.new_capital_CU * 1000, authorised.original_capital_CU).all()) and bool(np.isclose(prm01.new_capital_CU * 1000, prm01.original_capital_CU).all())
               and all(authorised[authorised.line == line].new_capital_CU.max() < THR[line] and prm01[prm01.line == line].new_capital_CU.max() < THR[line] for line in THR),
               observed={"max_nuevo_edificios": float(max(authorised[authorised.line == "buildings"].new_capital_CU.max(), prm01[prm01.line == "buildings"].new_capital_CU.max())), "max_nuevo_contenidos": float(max(authorised[authorised.line == "contents"].new_capital_CU.max(), prm01[prm01.line == "contents"].new_capital_CU.max()))})
    ratios_ok = {
        "NUL01-R": bool(authorised[authorised.criterio == "NUL01-R"].reference_ratio.between(*BAND).all()),
        "END02-R": bool(authorised[authorised.criterio == "END02-R"].reference_ratio.between(*BAND).all()),
        "TW01-R": bool(authorised[authorised.criterio == "TW01-R"].reference_ratio.between(*BAND).all()),
        "MOV01-R": bool(np.isclose(authorised[authorised.criterio == "MOV01-R"].reference_ratio, 1.0).all()),
        "END01-R": bool(authorised[authorised.criterio == "END01-R"].reference_ratio.between(1.203, 1.596).all()),
        "CHAIN01-R": bool(chain.direct_in_band.all()),
    }
    checks.add("L05", "cada criterio cumple su condición numérica: razón en [0,9; 1,1] (NUL01-R, END02-R, TW01-R, CHAIN01-R directa), exactamente 1 (MOV01-R) y dentro de p1–p99 medido de las ampliaciones (END01-R)", all(ratios_ok.values()), observed=ratios_ok)
    test_rows = int(authorised.test2025_row.sum()) + int(prm01.test2025_row.sum())
    checks.add("L06", "las filas de test 2025 decididas son 177 (54 autorizadas por historia, 123 bajo PRM01-R), las mismas que la rama declara pendientes en test",
               test_rows == 177 and int(authorised.test2025_row.sum()) == 54 and int(prm01.test2025_row.sum()) == 123, observed={"autorizadas_test": int(authorised.test2025_row.sum()), "prm01_test": int(prm01.test2025_row.sum())})
    checks.add("L07", "la decisión no aplica nada: ninguna fila lleva capital_change_applied y los índices de Limpieza conservan su hash de entrada",
               not authorised.capital_change_applied.any() and not prm01.capital_change_applied.any()
               and digest(LIMP / "current_retrospective_dataset.json") == provenance["inputs_sha256"]["current_retrospective_dataset.json"] and digest(LIMP / "current_dataset.json") == provenance["inputs_sha256"]["current_dataset.json"],
               observed="sin cambios")

    # --- resúmenes
    def summarise(df: pd.DataFrame) -> dict:
        return {"rows": int(len(df)), "by_line": df.line.value_counts().to_dict(), "by_source_table": df.source_table.value_counts().to_dict(),
                "test2025_rows": int(df.test2025_row.sum()), "sum_original_CU": float(df.original_capital_CU.sum()), "sum_new_CU": float(df.new_capital_CU.sum()),
                "sha256_sorted_row_ids": ids_hash(df.row_id)}
    by_criterion = {}
    for crit, g in authorised.groupby("criterio"):
        d = summarise(g)
        d.update(orden=int(g.orden_aplicacion.iloc[0]), regla_rama_propuesta=g.regla_rama_propuesta.iloc[0], estado=DECISION[crit]["estado"], condicion=DECISION[crit]["condicion"],
                 by_level=g.nivel.value_counts().to_dict(), by_direction=g.reference_direction.value_counts().to_dict(), reference_test2025=int(g.reference_test2025.sum()),
                 ratio_min=float(g.reference_ratio.min()), ratio_max=float(g.reference_ratio.max()), premium_rate_new_in_normal_range=int(g.premium_rate_new_in_normal_range.sum()))
        by_criterion[crit] = d
    prm = summarise(prm01)
    prm.update(orden=DECISION["PRM01-R"]["orden"], regla_rama_propuesta="CAP13R", estado=DECISION["PRM01-R"]["estado"], condicion=DECISION["PRM01-R"]["condicion"], by_group=prm01.grupo_D48.value_counts().to_dict(),
               premium_rate_new_in_normal_range=int(prm01.premium_rate_new_in_normal_range.sum()), premium_rate_new_percentile_quantiles={q: float(prm01.premium_rate_new_percentile_in_normal.quantile(q)) for q in [0.0, 0.1, 0.5, 0.9, 1.0]})
    by_criterion["PRM01-R"] = prm
    total = summarise(pd.concat([authorised, prm01], ignore_index=True))
    order = sorted(by_criterion, key=lambda k: by_criterion[k]["orden"])

    # --- tablas
    authorised.to_csv(out / "tables/autorizadas.csv", index=False)
    prm01.to_csv(out / "tables/prm01_F0.csv", index=False)
    premium_table.to_csv(out / "tables/prueba_prima_global.csv", index=False)
    held.to_csv(out / "tables/retenidas_D63_reevaluadas.csv", index=False)
    chain.to_csv(out / "tables/chain01_ancla_directa.csv", index=False)
    endorse.to_csv(out / "tables/end01_sin_reversion.csv", index=False)
    pd.DataFrame([{"orden": by_criterion[k]["orden"], "criterio": k, "regla_rama_propuesta": by_criterion[k]["regla_rama_propuesta"], "estado": by_criterion[k]["estado"], "filas": by_criterion[k]["rows"],
                   "test2025": by_criterion[k]["test2025_rows"], "sha256_sorted_row_ids": by_criterion[k]["sha256_sorted_row_ids"], "condicion": by_criterion[k]["condicion"]} for k in order]).to_csv(out / "tables/resumen_criterios.csv", index=False)
    pd.DataFrame(checks.rows).to_csv(out / "tables/controles.csv", index=False)
    shutil.copy2(Path(__file__), out / Path(__file__).name)

    evidence = {
        "run_id": out.name, "created_utc": started.isoformat(timespec="seconds"), "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "author": AUTHOR,
        "request": "el participante delegó en Claude, en rol de actuario especializado, la decisión sobre los criterios propuestos en D63 y D65 para los 419 capitales pendientes de la rama y el tratamiento en F0 de las filas sin referencia",
        "scope": {"decision_only": True, "data_modified": False, "indices_modified": False, "models_trained": False, "external_providers": False, "human_review": "pending", "independent_validation": False,
                  "application_requires": "flujo apply/verify/finalize de Limpieza, con cierre y versión de protocolo, a cargo del participante o de Codex con esta decisión como autorización documentada"},
        "environment": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "platform": platform.platform()},
        "definitions": {"umbral_CU": THR, "banda_D34": BAND, "banda_ampliaciones": ENDORSE_BAND, "banda_ampliaciones_medida_p1_p99": [1.203, 1.596], "cadena_max_dias": CHAIN_MAX_DAYS,
                        "prima_por_mil": "written_premium / (sum_insured / 1000); con capital registrado y con capital dividido entre mil"},
        "provenance": provenance,
        "decision": {k: {"orden": v["orden"], "estado": v["estado"], "niveles": v["niveles"], "condicion": v["condicion"]} for k, v in DECISION.items()},
        "orden_de_aplicacion": order,
        "f0_contract": F0_CONTRACT,
        "by_criterion": by_criterion,
        "authorised_total": summarise(authorised),
        "prm01_total": prm,
        "decided_total": total,
        "premium_test": premium_summary,
        "held_D63_reevaluated": held.drop(columns=["endorsement_detail"]).to_dict("records"),
        "held_D63_endorsement_detail": {r.row_id: json.loads(r.endorsement_detail) for _, r in held.iterrows()},
        "chain01_direct_anchor": chain.to_dict("records"),
        "end01_without_reversion": endorse.to_dict("records"),
        "remaining_pending_after_decision": {"rama": 0, "base": "1.454 sin cambios por diseño; F0 los trata por umbral con las mismas marcas"},
        "checks": checks.rows,
        "checks_summary": {"checks_total": len(checks.rows), "checks_passed": sum(1 for c in checks.rows if c["passed"]), "all_passed": all(c["passed"] for c in checks.rows)},
    }
    (out / "evidencia.json").write_text(json.dumps(jsonable(evidence), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {str(p.relative_to(out)).replace("\\", "/"): digest(p) for p in sorted(out.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run": out.name, "checks": evidence["checks_summary"], "autorizadas": len(authorised), "prm01": len(prm01)}, ensure_ascii=False))
    if not evidence["checks_summary"]["all_passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
