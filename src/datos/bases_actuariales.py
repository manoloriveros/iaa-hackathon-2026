"""Bases actuariales para el modelado: expuestos, asignación de siniestros, retraso de reporte e IBNR, frecuencia,
severidad y referencias de tasa constante (M00), calculadas sobre la capa preparada vigente.

Lee current_dataset.json de Limpieza, comprueba los SHA-256 de las siete tablas que usa contra el catálogo activo y
no modifica ningún dato ni índice. Crea runs/bases_<marca>_<id>/ con evidencia.json, tablas CSV y Parquet, copia del
script y manifest.json con hashes. Cada ejecución crea una carpeta nueva; current_run.json se fija aparte tras
verificar. No entrena modelos: las referencias M00 son tasas constantes por ramo evaluadas sobre el corte siguiente.

Uso (Windows): & '.\\Preparación\\.venv\\Scripts\\python.exe' '.\\Hackaton\\Semana 1\\Bases_actuariales_claude\\bases_actuariales.py'
Uso (Linux):   python3 'Hackaton/Semana 1/Bases_actuariales_claude/bases_actuariales.py'
"""
from __future__ import annotations

import hashlib
import json
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
try:  # el lector aislado de Parquet del proyecto, si pyarrow no está en el entorno activo
    import pyarrow  # noqa: F401
except ImportError:  # pragma: no cover
    sys.path.insert(0, str(ROOT / "Preparación" / ".cache" / "parquet-reader"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

LINES = ["motor", "buildings", "contents"]
LINE_ES = {"motor": "autos", "buildings": "edificios", "contents": "contenidos"}
CUTOFF = pd.Timestamp("2024-12-30")  # última fecha de reporte observada; se comprueba contra los datos
POWER = 1.5
LONG_TAIL = {("motor", "bodily_injury"), ("buildings", "subsidence")}
MONTHS = pd.period_range("2021-01", "2025-12", freq="M")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tweedie_deviance(y: np.ndarray, mu: np.ndarray, p: float = POWER) -> np.ndarray:
    """Desviación unitaria de Tweedie. Para p=1,5 equivale a 4*(sqrt(mu)-sqrt(y))**2/sqrt(mu)."""
    y = np.asarray(y, dtype=float)
    mu = np.asarray(mu, dtype=float)
    return 2.0 * (np.power(y, 2 - p) / ((1 - p) * (2 - p)) - y * np.power(mu, 1 - p) / (1 - p) + np.power(mu, 2 - p) / (2 - p))


def d2_tweedie(y: np.ndarray, mu: np.ndarray, p: float = POWER) -> float:
    """D² como scikit-learn: 1 - dev(y, mu) / dev(y, media de y)."""
    y = np.asarray(y, dtype=float)
    mu = np.asarray(mu, dtype=float)
    null = np.full_like(y, y.mean())
    return float(1.0 - tweedie_deviance(y, mu, p).sum() / tweedie_deviance(y, null, p).sum())


def r(x, nd=4):
    if x is None:
        return None
    if isinstance(x, (np.floating, float)):
        if not np.isfinite(x):
            return None
        return round(float(x), nd)
    if isinstance(x, (np.integer,)):
        return int(x)
    return x


def main() -> None:
    started = datetime.now(timezone.utc)
    run_id = f"bases_{started.strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    run_dir = HERE / "runs" / run_id
    tables_dir = run_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=False)
    checks: list[dict] = []

    def check(code: str, name: str, ok: bool, detail=None):
        checks.append({"code": code, "name": name, "passed": bool(ok), "detail": detail})

    # ------------------------------------------------------------------ 1. capa vigente y hashes
    index_path = ROOT / "Hackaton/Semana 1/Limpieza/current_dataset.json"
    current = json.loads(index_path.read_text(encoding="utf-8"))
    catalog_path = ROOT / current["catalog_workspace_relative"]
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    verification = json.loads((catalog_path.parent / "verification.json").read_text(encoding="utf-8"))
    check("K01", "la corrida vigente de Limpieza tiene verificación con cero fallos", verification.get("failed") == 0 and verification.get("passed", 0) > 0,
          {"status": verification.get("status"), "passed": verification.get("passed"), "failed": verification.get("failed")})
    used = ["claims", "policies_motor", "policies_buildings", "policies_contents", "test_motor", "test_buildings", "test_contents"]
    hashes = {}
    bad = []
    for name in used:
        path = ROOT / catalog[name]["workspace_relative_path"]
        hashes[name] = digest(path)
        if hashes[name] != catalog[name]["sha256"]:
            bad.append(name)
    check("K02", "los SHA-256 de las siete tablas usadas coinciden con el catálogo activo", not bad, bad)

    def read(name: str, columns: list[str]) -> pd.DataFrame:
        path = ROOT / catalog[name]["workspace_relative_path"]
        df = pd.read_parquet(path, columns=columns)
        for col in df.columns:  # cadenas compactas: la VM de cálculo tiene poca memoria
            if df[col].dtype == object:
                df[col] = df[col].astype("string[pyarrow]")
        return df

    base_cols = ["row_id", "policy_id", "customer_id", "period_start", "period_end", "exposure", "new_business", "written_premium"]
    frames = []
    for line in LINES:
        extra = ["cover_type"] if line == "motor" else []
        for kind, table in (("train", f"policies_{line}"), ("test", f"test_{line}")):
            df = read(table, base_cols + extra)
            df["line"] = line
            df["is_test"] = kind == "test"
            if line != "motor":
                df["cover_type"] = "n/a"
            frames.append(df)
    periods = pd.concat(frames, ignore_index=True)
    del frames
    periods["period_start"] = pd.to_datetime(periods["period_start"])
    periods["period_end"] = pd.to_datetime(periods["period_end"])
    periods["year"] = periods["period_start"].dt.year.astype(int)
    days = ((periods["period_end"] - periods["period_start"]).dt.days + 1).values
    max_abs_diff = float(np.abs(periods["exposure"].values - days / 365.0).max())
    check("K03", "exposición EXP01 = días inclusivos / 365 en todas las filas (tolerancia 1e-4)", max_abs_diff < 1e-4, {"max_abs_diff": r(max_abs_diff, 6)})
    del days
    check("K04", "626.639 filas de test con row_id único", int(periods["is_test"].sum()) == 626639 and periods.loc[periods.is_test, "row_id"].is_unique,
          {"test_rows": int(periods["is_test"].sum())})
    check("K05", "los periodos de test son todos de 2025 y los de entrenamiento de 2021-2024",
          set(periods.loc[periods.is_test, "year"].unique()) == {2025} and set(periods.loc[~periods.is_test, "year"].unique()) == {2021, 2022, 2023, 2024})

    # ------------------------------------------------------------------ 2. expuestos
    def exposure_block(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
        g = df.groupby(keys)
        out = g.agg(filas=("row_id", "size"), expuestos_anios=("exposure", "sum"), exposicion_media=("exposure", "mean"),
                    polizas=("policy_id", "nunique"), clientes=("customer_id", "nunique"),
                    prima_escrita_CU=("written_premium", "sum")).reset_index()
        out["pct_filas_anio_completo"] = g["exposure"].apply(lambda s: float((s >= 0.99).mean())).values * 100
        out["pct_filas_menos_medio_anio"] = g["exposure"].apply(lambda s: float((s < 0.5).mean())).values * 100
        out["pct_filas_nuevo_negocio"] = g["new_business"].apply(lambda s: float(s.mean())).values * 100
        out["prima_escrita_por_anio_expuesto_CU"] = out["prima_escrita_CU"] / out["expuestos_anios"]
        return out

    exp_line_year = exposure_block(periods, ["line", "year"])
    exp_line_year.to_csv(tables_dir / "expuestos_ramo_anio.csv", index=False)
    exp_cover = exposure_block(periods[periods.line == "motor"], ["year", "cover_type"])
    exp_cover.to_csv(tables_dir / "expuestos_autos_cobertura.csv", index=False)
    train_exposure_total = float(periods.loc[~periods.is_test, "exposure"].sum())
    test_exposure_total = float(periods.loc[periods.is_test, "exposure"].sum())
    check("K12", "exposición total del entrenamiento igual a la de EXP01 (1.968.577,0591 años, tolerancia 0,01)", abs(train_exposure_total - 1968577.0591) < 0.01, r(train_exposure_total, 4))

    # exposición por mes natural de ocurrencia: días cubiertos en cada mes / 365
    ps = periods["period_start"].values.astype("datetime64[D]")
    pe = periods["period_end"].values.astype("datetime64[D]")
    line_codes = periods["line"].map({l: i for i, l in enumerate(LINES)}).values.astype(int)
    month_rows = []
    month_exposure = np.zeros((len(LINES), len(MONTHS)))
    for j, m in enumerate(MONTHS):
        ms = np.datetime64(m.start_time.date(), "D")
        me = np.datetime64(m.end_time.date(), "D")
        overlap = (np.minimum(pe, me) - np.maximum(ps, ms)).astype("timedelta64[D]").astype(int) + 1
        overlap = np.clip(overlap, 0, None) / 365.0
        for i in range(len(LINES)):
            month_exposure[i, j] = overlap[line_codes == i].sum()
            month_rows.append({"line": LINES[i], "mes": str(m), "expuestos_anios": month_exposure[i, j]})
    del ps, pe, line_codes, overlap
    month_df = pd.DataFrame(month_rows)
    month_df.to_csv(tables_dir / "expuestos_ramo_mes.csv", index=False)
    year_from_months = month_df.assign(anio=month_df.mes.str[:4].astype(int)).groupby(["line", "anio"])["expuestos_anios"].sum()
    ely = exp_line_year.set_index(["line", "year"])["expuestos_anios"]
    diff_month = max(abs(year_from_months[(l, y)] - ely[(l, y)]) for l in LINES for y in range(2021, 2026))
    check("K13", "la exposición por meses naturales suma la exposición por fila en cada ramo y año (tolerancia 0,5 años)", diff_month < 0.5, r(float(diff_month), 4))

    train = periods.loc[~periods.is_test, ["row_id", "policy_id", "line", "period_start", "period_end", "year", "exposure", "cover_type"]].reset_index(drop=True)
    del periods

    claims = read("claims", ["claim_id", "policy_id", "line", "peril", "loss_date", "report_date", "status", "paid_to_date", "incurred_to_date", "recoveries", "audit_pre00"])
    claims["loss_date"] = pd.to_datetime(claims["loss_date"])
    claims["report_date"] = pd.to_datetime(claims["report_date"])
    claims["accepted"] = claims["status"].isin(["closed", "open"])
    claims["net"] = claims["incurred_to_date"] - claims["recoveries"]
    claims["reserve"] = claims["incurred_to_date"] - claims["paid_to_date"]
    claims["delay_days"] = (claims["report_date"] - claims["loss_date"]).dt.days
    observed_cutoff = claims["report_date"].max()
    check("K06", "la última fecha de reporte observada es el 30-12-2024 (corte de valoración)", observed_cutoff == CUTOFF, str(observed_cutoff.date()))
    check("K07", "claims vigente: 162.546 registros, 413 marcados audit_pre00, ningún reporte anterior a la ocurrencia",
          len(claims) == 162546 and int(claims["audit_pre00"].sum()) == 413 and int((claims["delay_days"] < 0).sum()) == 0,
          {"rows": len(claims), "pre00": int(claims["audit_pre00"].sum()), "negative_delays": int((claims["delay_days"] < 0).sum())})

    # ------------------------------------------------------------------ 3. asignación de siniestros a periodos
    cand = claims.loc[~claims.audit_pre00, ["claim_id", "policy_id", "line", "loss_date"]].merge(train[["row_id", "policy_id", "line", "period_start", "period_end"]], on=["policy_id", "line"], how="left")
    cand["inside"] = (cand["loss_date"] >= cand["period_start"]) & (cand["loss_date"] <= cand["period_end"])
    has_policy = cand.groupby("claim_id")["row_id"].count() > 0
    n_inside = cand[cand.inside].groupby("claim_id")["row_id"].nunique()
    assign = pd.DataFrame({"claim_id": claims.loc[~claims.audit_pre00, "claim_id"].values})
    assign["has_policy"] = assign["claim_id"].map(has_policy).fillna(False).astype(bool)
    assign["n_periods"] = assign["claim_id"].map(n_inside).fillna(0).astype(int)
    assign["category"] = np.select([~assign.has_policy, assign.n_periods == 1, assign.n_periods == 0, assign.n_periods > 1],
                                   ["sin_correspondencia", "unica", "fuera_de_ventana", "ambigua"], default="?")
    unique_map = cand[cand.inside & cand.claim_id.isin(assign.loc[assign.category == "unica", "claim_id"])][["claim_id", "row_id"]]
    pre = pd.DataFrame({"claim_id": claims.loc[claims.audit_pre00, "claim_id"].values, "has_policy": True, "n_periods": 0, "category": "prehistoria_PRE00"})
    assign = pd.concat([assign, pre], ignore_index=True).merge(unique_map, on="claim_id", how="left")
    claims = claims.merge(assign[["claim_id", "category", "row_id"]], on="claim_id", how="left")
    check("K08", "PRE00: ningún siniestro audit_pre00 queda asignado a un periodo", claims.loc[claims.audit_pre00, "row_id"].isna().all())
    cat_counts = claims.groupby(["line", "category"]).size().unstack(fill_value=0)
    acc_counts = claims[claims.accepted].groupby(["line", "category"]).size().unstack(fill_value=0)
    check("K09", "sin siniestros ambiguos ni sin póliza", int(cat_counts.get("ambigua", pd.Series(0, index=cat_counts.index)).sum()) == 0 and int(cat_counts.get("sin_correspondencia", pd.Series(0, index=cat_counts.index)).sum()) == 0)
    expected_unique_accepted = {"motor": 110496, "buildings": 26266, "contents": 23670}
    got_unique_accepted = {line: int(acc_counts.loc[line].get("unica", 0)) for line in LINES}
    check("K10", "asignación única de aceptados igual a D42/D50 (110.496, 26.266, 23.670)", got_unique_accepted == expected_unique_accepted, got_unique_accepted)
    fuera = claims[(claims.category == "fuera_de_ventana")]
    fuera_desc = {
        "total": int(len(fuera)), "aceptados": int(fuera.accepted.sum()),
        "net_aceptado_CU": r(float(fuera.loc[fuera.accepted, "net"].sum()), 2),
        "loss_31_12_2024": int((fuera.loss_date == pd.Timestamp("2024-12-31")).sum()),
        "loss_dec_2024": int(((fuera.loss_date >= pd.Timestamp("2024-12-01")) & (fuera.loss_date <= pd.Timestamp("2024-12-31"))).sum()),
        "loss_after_last_period_of_policy": None,
    }
    last_end = train.groupby("policy_id")["period_end"].max()
    first_start = train.groupby("policy_id")["period_start"].min()
    fuera_after = fuera.loss_date > fuera.policy_id.map(last_end)
    fuera_before = fuera.loss_date < fuera.policy_id.map(first_start)
    fuera_desc["loss_after_last_period_of_policy"] = int(fuera_after.sum())
    fuera_desc["loss_before_first_period_of_policy"] = int(fuera_before.sum())
    fuera_desc["loss_in_gap_between_periods"] = int((~fuera_after & ~fuera_before).sum())
    assignment_table = claims.groupby(["line", "category", "status"]).agg(n=("claim_id", "size"), net_CU=("net", "sum")).reset_index()
    assignment_table.to_csv(tables_dir / "asignacion_siniestros.csv", index=False)
    claims[["claim_id", "policy_id", "line", "peril", "loss_date", "report_date", "status", "category", "row_id"]].to_parquet(tables_dir / "asignacion_por_siniestro.parquet", index=False)

    # ------------------------------------------------------------------ 4. T0 por row_id
    acc = claims[claims.accepted & (claims.category == "unica")].copy()
    acc["positive"] = acc["net"] > 0
    acc["is_open"] = acc["status"] == "open"
    t0 = acc.groupby("row_id").agg(T0=("net", "sum"), n_accepted=("claim_id", "size"), n_positive=("positive", "sum"), n_open=("is_open", "sum"),
                                  paid=("paid_to_date", "sum"), incurred=("incurred_to_date", "sum"), recoveries=("recoveries", "sum"), reserve=("reserve", "sum"))
    t0_rows = train[["row_id", "line", "year", "exposure", "cover_type"]].merge(t0, on="row_id", how="left")
    for col in ["T0", "n_accepted", "n_positive", "n_open", "paid", "incurred", "recoveries", "reserve"]:
        t0_rows[col] = t0_rows[col].fillna(0)
    for col in ["n_accepted", "n_positive", "n_open"]:
        t0_rows[col] = t0_rows[col].astype(int)
    check("K11", "la suma de T0 por fila iguala el neto de los aceptados asignados y no hay netos negativos",
          abs(t0_rows["T0"].sum() - acc["net"].sum()) < 1e-6 and int((acc["net"] < 0).sum()) == 0,
          {"T0_total_CU": r(float(t0_rows["T0"].sum()), 2), "net_zero_accepted": int((acc["net"] == 0).sum())})
    t0_rows[["row_id", "line", "year", "exposure", "T0", "n_accepted", "n_positive", "n_open", "paid", "incurred", "recoveries", "reserve"]].to_parquet(tables_dir / "t0_por_row_id.parquet", index=False)

    # ------------------------------------------------------------------ 5. retraso de reporte y chain-ladder de conteos
    rep = claims[(claims.category == "unica")].copy()  # todas las notificaciones asignadas, aceptadas o rechazadas
    rep["occ_m"] = (rep.loss_date.dt.year - 2021) * 12 + rep.loss_date.dt.month - 1
    rep["rep_m"] = (rep.report_date.dt.year - 2021) * 12 + rep.report_date.dt.month - 1
    rep["lag"] = rep["rep_m"] - rep["occ_m"]
    N = 48  # cohortes mensuales 2021-01 .. 2024-12
    delay_rows, cl_rows, tail_rows, month_complete_rows, factor_rows = [], [], [], [], []
    completeness = {}  # (line, peril) -> array de 12 completitudes 2024 por mes de ocurrencia
    cdf_by_group = {}
    for (line, peril), g in rep.groupby(["line", "peril"]):
        # triángulo acumulado de conteos por cohorte mensual y lag
        tri = np.zeros((N, N))
        for occ, lag in zip(g.occ_m.values, g.lag.values):
            if 0 <= occ < N and 0 <= lag < N:
                tri[occ, lag:] += 1  # acumulado
        factors = []
        for k in range(N - 1):
            rows = [i for i in range(N) if i + k + 1 <= N - 1]  # cohortes con lag k+1 observado
            num = sum(tri[i, k + 1] for i in rows)
            den = sum(tri[i, k] for i in rows)
            factors.append(num / den if den > 0 else 1.0)
        factors = np.array(factors)
        # cola: ajuste exponencial sobre los últimos factores > 1 (lags 12..46) para los dos peligros largos
        tail = 1.0
        tail_fit = None
        if (line, peril) in LONG_TAIL:
            ks = np.arange(12, N - 1)
            fk = factors[12:N - 1]
            mask = fk > 1.0
            if mask.sum() >= 6:
                a, b = np.polyfit(ks[mask], np.log(fk[mask] - 1.0), 1)
                if a < 0:
                    future = np.arange(N - 1, N - 1 + 120)
                    tail = float(np.prod(1.0 + np.exp(a * future + b)))
                    tail_fit = {"pendiente": r(float(a), 5), "intercepto": r(float(b), 4), "puntos": int(mask.sum()), "cola_120_meses": r(tail, 4)}
                else:
                    tail_fit = {"pendiente": r(float(a), 5), "nota": "sin decaimiento; cola fijada en 1"}
        cdf = np.ones(N)  # edad k -> factor a último
        for k in range(N - 2, -1, -1):
            cdf[k] = cdf[k + 1] * factors[k]
        cdf = cdf * tail
        cdf_by_group[(line, peril)] = cdf
        reported_2024 = float(tri[36:48, :].max(axis=1).sum())
        ult_2024 = float(sum(tri[i, N - 1 - i] * cdf[N - 1 - i] for i in range(36, 48)))
        rep_by_year = {y: float(sum(tri[i, N - 1 - i] for i in range((y - 2021) * 12, (y - 2021) * 12 + 12))) for y in range(2021, 2025)}
        ult_by_year = {y: float(sum(tri[i, N - 1 - i] * cdf[N - 1 - i] for i in range((y - 2021) * 12, (y - 2021) * 12 + 12))) for y in range(2021, 2025)}
        comp_months = np.array([1.0 / cdf[N - 1 - i] for i in range(36, 48)])
        completeness[(line, peril)] = comp_months
        for i in range(36, 48):
            month_complete_rows.append({"line": line, "peril": peril, "mes_ocurrencia": str(MONTHS[i]), "edad_meses": N - 1 - i,
                                        "reportados": int(tri[i, N - 1 - i]), "factor_a_ultimo": r(float(cdf[N - 1 - i]), 4), "completitud": r(float(1.0 / cdf[N - 1 - i]), 4)})
        for k in range(N - 1):
            factor_rows.append({"line": line, "peril": peril, "lag_meses": k, "factor": r(float(factors[k]), 5), "factor_a_ultimo": r(float(cdf[k]), 5)})
        # retraso empírico en días por cohorte de ocurrencia (aceptados y rechazados)
        for y in range(2021, 2025):
            gy = g[g.loss_date.dt.year == y]
            d = gy.delay_days
            delay_rows.append({"line": line, "peril": peril, "cohorte": y, "n": int(len(d)), "p50": r(float(d.quantile(0.5)), 1) if len(d) else None,
                               "p90": r(float(d.quantile(0.9)), 1) if len(d) else None, "p99": r(float(d.quantile(0.99)), 1) if len(d) else None,
                               "pct_30d": r(float((d <= 30).mean() * 100), 2) if len(d) else None, "pct_90d": r(float((d <= 90).mean() * 100), 2) if len(d) else None,
                               "pct_365d": r(float((d <= 365).mean() * 100), 2) if len(d) else None, "max": int(d.max()) if len(d) else None})
        cl_rows.append({"line": line, "peril": peril, "notificaciones_2021_2024": int(len(g)), "cola": r(tail, 4), "cola_ajuste": json.dumps(tail_fit, ensure_ascii=False) if tail_fit else "",
                        **{f"reportados_{y}": int(rep_by_year[y]) for y in range(2021, 2025)},
                        **{f"ultimo_{y}": r(ult_by_year[y], 1) for y in range(2021, 2025)},
                        **{f"completitud_{y}": r(rep_by_year[y] / ult_by_year[y], 4) if ult_by_year[y] else None for y in range(2021, 2025)},
                        "ibnr_conteo_2024": r(ult_2024 - reported_2024, 1), "factor_1_mes": r(float(factors[0]), 4), "factor_a_ultimo_edad_0": r(float(cdf[0]), 4), "factor_a_ultimo_edad_11": r(float(cdf[11]), 4)})
    pd.DataFrame(delay_rows).to_csv(tables_dir / "retraso_reporte_cohortes.csv", index=False)
    cl = pd.DataFrame(cl_rows)
    cl.to_csv(tables_dir / "chain_ladder_conteos.csv", index=False)
    pd.DataFrame(month_complete_rows).to_csv(tables_dir / "completitud_2024_por_mes.csv", index=False)
    pd.DataFrame(factor_rows).to_csv(tables_dir / "factores_desarrollo_conteos.csv", index=False)
    short = cl[~cl.apply(lambda row: (row.line, row.peril) in LONG_TAIL, axis=1)]
    check("K14", "completitud de reporte 2021 >= 0,995 en todos los peligros de cola corta", bool((short["completitud_2021"] >= 0.995).all()), r(float(short["completitud_2021"].min()), 4))
    check("K15", "completitud 2024 < completitud 2021 en lesiones corporales y hundimiento",
          all(cl.loc[(cl.line == l) & (cl.peril == p), "completitud_2024"].iloc[0] < cl.loc[(cl.line == l) & (cl.peril == p), "completitud_2021"].iloc[0] for l, p in LONG_TAIL))

    # ------------------------------------------------------------------ 6. severidad
    sev_rows = []
    pos = acc[acc.positive]
    for (line, peril), g in pos.groupby(["line", "peril"]):
        for y in [2021, 2022, 2023, 2024, "2021-2022", "2021-2024"]:
            if isinstance(y, int):
                gy = g[g.loss_date.dt.year == y]
            elif y == "2021-2022":
                gy = g[g.loss_date.dt.year <= 2022]
            else:
                gy = g
            s = gy["net"]
            if len(s) == 0:
                continue
            closed = gy[gy.status == "closed"]["net"]
            opened = gy[gy.status == "open"]["net"]
            late = gy[gy.delay_days > 365]["net"]
            sev_rows.append({"line": line, "peril": peril, "ocurrencia": y, "n_positivos": int(len(s)), "media": r(float(s.mean()), 2), "mediana": r(float(s.median()), 2),
                             "cv": r(float(s.std(ddof=1) / s.mean()), 3) if len(s) > 1 else None, "p90": r(float(s.quantile(0.9)), 2), "p99": r(float(s.quantile(0.99)), 2), "max": r(float(s.max()), 2),
                             "pct_abiertos": r(float((gy.status == "open").mean() * 100), 2), "media_cerrados": r(float(closed.mean()), 2) if len(closed) else None,
                             "media_abiertos": r(float(opened.mean()), 2) if len(opened) else None, "reserva_sobre_incurrido_pct": r(float(gy.reserve.sum() / gy.incurred_to_date.sum() * 100), 2),
                             "n_reportados_mas_365d": int(len(late)), "media_reportados_mas_365d": r(float(late.mean()), 2) if len(late) else None,
                             "coste_1pct_mayor_pct": r(float(s.nlargest(max(1, int(np.ceil(len(s) * 0.01)))).sum() / s.sum() * 100), 2)})
    sev = pd.DataFrame(sev_rows)
    sev.to_csv(tables_dir / "severidad_ramo_peligro.csv", index=False)
    share_positive = (acc.groupby(["line", "peril"])["positive"].mean()).to_dict()
    notif_positive = (rep.merge(acc[["claim_id", "positive"]], on="claim_id", how="left").assign(positive=lambda d: d.positive.fillna(False)).groupby(["line", "peril"])["positive"].mean()).to_dict()

    # ------------------------------------------------------------------ 7. frecuencia
    freq_rows = []
    exp_ly = exp_line_year.set_index(["line", "year"])["expuestos_anios"]
    for line in LINES:
        for y in range(2021, 2025):
            e = float(exp_ly[(line, y)])
            rows = t0_rows[(t0_rows.line == line) & (t0_rows.year == y)]
            n_pos = int(rows.n_positive.sum())
            n_acc = int(rows.n_accepted.sum())
            lam = rows.n_positive.values
            disp = float(((lam - lam.mean()) ** 2).sum() / (len(lam) - 1) / lam.mean()) if lam.mean() > 0 else None
            freq_rows.append({"line": line, "year": y, "peril": "todos", "expuestos_anios": r(e, 2), "aceptados": n_acc, "positivos": n_pos,
                              "frecuencia_aceptados": r(n_acc / e, 5), "frecuencia_positivos": r(n_pos / e, 5), "dispersion_varianza_media": r(disp, 3),
                              "pct_periodos_sin_coste": r(float((rows.T0 == 0).mean() * 100), 2)})
            for peril, g in acc[(acc.line == line) & (acc.loss_date.dt.year == y)].groupby("peril"):
                freq_rows.append({"line": line, "year": y, "peril": peril, "expuestos_anios": r(e, 2), "aceptados": int(len(g)), "positivos": int(g.positive.sum()),
                                  "frecuencia_aceptados": r(len(g) / e, 5), "frecuencia_positivos": r(float(g.positive.sum()) / e, 5), "dispersion_varianza_media": None, "pct_periodos_sin_coste": None})
    freq = pd.DataFrame(freq_rows)
    freq.to_csv(tables_dir / "frecuencia_ramo_anio_peligro.csv", index=False)
    freq_cover = []
    for (y, cov), rows in t0_rows[t0_rows.line == "motor"].groupby(["year", "cover_type"]):
        e = float(rows.exposure.sum())
        freq_cover.append({"year": y, "cover_type": cov, "filas": int(len(rows)), "expuestos_anios": r(e, 2), "frecuencia_positivos": r(rows.n_positive.sum() / e, 5),
                           "prima_riesgo_T0_CU": r(float(rows.T0.sum() / e), 2)})
    pd.DataFrame(freq_cover).to_csv(tables_dir / "frecuencia_autos_cobertura.csv", index=False)

    # frecuencia última 2024 (IBNR de conteos aplicado a positivos) y exposición efectiva
    ult_rows = []
    for (line, peril), comp in completeness.items():
        g24 = acc[(acc.line == line) & (acc.peril == peril) & (acc.loss_date.dt.year == 2024)]
        n_pos = int(g24.positive.sum())
        n_all = int(len(rep[(rep.line == line) & (rep.peril == peril) & (rep.loss_date.dt.year == 2024)]))
        e24 = month_exposure[LINES.index(line), 36:48]
        e_eff = float((e24 * comp).sum())
        e_nom = float(e24.sum())
        ibnr_notif = float(cl.loc[(cl.line == line) & (cl.peril == peril), "ibnr_conteo_2024"].iloc[0])
        p_pos = float(notif_positive.get((line, peril), 0.0))
        ibnr_pos = ibnr_notif * p_pos
        sev_mature = sev[(sev.line == line) & (sev.peril == peril) & (sev.ocurrencia == "2021-2022")]
        mean_sev = float(sev_mature["media"].iloc[0]) if len(sev_mature) else float("nan")
        late_sev = sev_mature["media_reportados_mas_365d"].iloc[0] if len(sev_mature) else None
        sev_for_ibnr = float(late_sev) if ((line, peril) in LONG_TAIL and late_sev is not None and not pd.isna(late_sev)) else mean_sev
        t0_24 = float(g24["net"].sum())
        ult_rows.append({"line": line, "peril": peril, "notificaciones_2024": n_all, "positivos_2024": n_pos, "expuestos_2024": r(e_nom, 2), "expuestos_efectivos_2024": r(e_eff, 2),
                         "completitud_ponderada_2024": r(e_eff / e_nom, 4), "frecuencia_positivos_reportada": r(n_pos / e_nom, 5), "frecuencia_positivos_ultima_por_exposicion_efectiva": r(n_pos / e_eff, 5),
                         "ibnr_notificaciones": r(ibnr_notif, 1), "prob_positivo_por_notificacion": r(p_pos, 4), "ibnr_positivos": r(ibnr_pos, 1),
                         "severidad_media_2021_2022": r(mean_sev, 2), "severidad_usada_ibnr": r(sev_for_ibnr, 2), "ibnr_coste_CU": r(ibnr_pos * sev_for_ibnr, 2),
                         "T0_2024_CU": r(t0_24, 2), "factor_ibnr_coste": r((t0_24 + ibnr_pos * sev_for_ibnr) / t0_24, 4) if t0_24 > 0 else None})
    ult = pd.DataFrame(ult_rows)
    ult.to_csv(tables_dir / "ibnr_2024_por_peligro.csv", index=False)
    ult_line = ult.groupby("line").agg(T0_2024_CU=("T0_2024_CU", "sum"), ibnr_coste_CU=("ibnr_coste_CU", "sum"), ibnr_positivos=("ibnr_positivos", "sum"), positivos_2024=("positivos_2024", "sum")).reset_index()
    ult_line["factor_ibnr_coste"] = (ult_line.T0_2024_CU + ult_line.ibnr_coste_CU) / ult_line.T0_2024_CU
    ult_line["factor_ibnr_conteo"] = (ult_line.positivos_2024 + ult_line.ibnr_positivos) / ult_line.positivos_2024
    ult_line.to_csv(tables_dir / "ibnr_2024_por_ramo.csv", index=False)

    # IBNR por peligro y año de ocurrencia 2021-2024 con la misma regla, y prima de riesgo última por ramo y año
    sev_used = {(row.line, row.peril): row.severidad_usada_ibnr for row in ult.itertuples()}
    ibnr_year_rows = []
    for row in cl.itertuples():
        for y in range(2021, 2025):
            reported = getattr(row, f"reportados_{y}")
            ultimate = getattr(row, f"ultimo_{y}")
            ibnr_notif = float(ultimate) - float(reported)
            p_pos = float(notif_positive.get((row.line, row.peril), 0.0))
            gy = acc[(acc.line == row.line) & (acc.peril == row.peril) & (acc.loss_date.dt.year == y)]
            t0_y = float(gy.net.sum())
            cost = ibnr_notif * p_pos * float(sev_used[(row.line, row.peril)])
            ibnr_year_rows.append({"line": row.line, "peril": row.peril, "year": y, "notificaciones": int(reported), "ultimo": r(float(ultimate), 1), "ibnr_notificaciones": r(ibnr_notif, 1),
                                   "ibnr_positivos": r(ibnr_notif * p_pos, 1), "ibnr_coste_CU": r(cost, 2), "T0_CU": r(t0_y, 2), "factor_ibnr_coste": r((t0_y + cost) / t0_y, 4) if t0_y > 0 else None})
    ibnr_year = pd.DataFrame(ibnr_year_rows)
    ibnr_year.to_csv(tables_dir / "ibnr_por_peligro_anio.csv", index=False)
    prima_ult_rows = []
    for line in LINES:
        for y in range(2021, 2025):
            e = float(exp_ly[(line, y)])
            sub = ibnr_year[(ibnr_year.line == line) & (ibnr_year.year == y)]
            t0_y = float(sub.T0_CU.sum())
            cost = float(sub.ibnr_coste_CU.sum())
            res_y = float(acc[(acc.line == line) & (acc.loss_date.dt.year == y) & acc.is_open].reserve.sum())
            prima_ult_rows.append({"line": line, "year": y, "expuestos_anios": r(e, 2), "T0_CU": r(t0_y, 2), "ibnr_coste_CU": r(cost, 2), "reserva_abiertos_CU": r(res_y, 2),
                                   "prima_riesgo_T0_CU": r(t0_y / e, 2), "prima_riesgo_T0_mas_IBNR_CU": r((t0_y + cost) / e, 2), "factor_ibnr_coste": r((t0_y + cost) / t0_y, 4),
                                   "prima_T1_a075_mas_IBNR_CU": r((t0_y - 0.25 * res_y + cost) / e, 2), "prima_T1_a125_mas_IBNR_CU": r((t0_y + 0.25 * res_y + cost) / e, 2)})
    prima_ult = pd.DataFrame(prima_ult_rows)
    prima_ult.to_csv(tables_dir / "prima_riesgo_ultima_ramo_anio.csv", index=False)

    # ------------------------------------------------------------------ 8. reservas de caso y sensibilidad T1
    res_rows = []
    for (line, peril, y), g in acc.groupby(["line", "peril", acc.loss_date.dt.year.rename("year")]):
        op = g[g.is_open]
        res_rows.append({"line": line, "peril": peril, "year": int(y), "aceptados": int(len(g)), "abiertos": int(len(op)), "pct_abiertos": r(float(len(op) / len(g) * 100), 2),
                         "T0_CU": r(float(g.net.sum()), 2), "reserva_abiertos_CU": r(float(op.reserve.sum()), 2), "reserva_sobre_T0_pct": r(float(op.reserve.sum() / g.net.sum() * 100), 2) if g.net.sum() > 0 else None,
                         "T1_a075_CU": r(float(g.net.sum() - 0.25 * op.reserve.sum()), 2), "T1_a125_CU": r(float(g.net.sum() + 0.25 * op.reserve.sum()), 2)})
    res = pd.DataFrame(res_rows)
    res.to_csv(tables_dir / "reservas_caso_T1.csv", index=False)
    res_line_year = res.groupby(["line", "year"]).agg(T0_CU=("T0_CU", "sum"), reserva_abiertos_CU=("reserva_abiertos_CU", "sum"), abiertos=("abiertos", "sum"), aceptados=("aceptados", "sum")).reset_index()
    res_line_year["reserva_sobre_T0_pct"] = res_line_year.reserva_abiertos_CU / res_line_year.T0_CU * 100
    res_line_year["T1_rango_pct"] = 0.25 * res_line_year["reserva_sobre_T0_pct"]
    res_line_year.to_csv(tables_dir / "reservas_caso_ramo_anio.csv", index=False)

    # ------------------------------------------------------------------ 9. prima de riesgo y referencias M00
    pr_rows = []
    for line in LINES:
        for y in range(2021, 2025):
            rows = t0_rows[(t0_rows.line == line) & (t0_rows.year == y)]
            e = float(rows.exposure.sum())
            n_pos = float(rows.n_positive.sum())
            pr_rows.append({"line": line, "year": y, "expuestos_anios": r(e, 2), "T0_CU": r(float(rows.T0.sum()), 2), "prima_riesgo_T0_CU": r(float(rows.T0.sum() / e), 2),
                            "frecuencia_positivos": r(n_pos / e, 5), "severidad_media_positivos_CU": r(float(rows.T0.sum() / n_pos), 2) if n_pos else None,
                            "identidad_freq_x_sev": r(float(n_pos / e * rows.T0.sum() / n_pos), 2) if n_pos else None})
    pr = pd.DataFrame(pr_rows)
    pr.to_csv(tables_dir / "prima_riesgo_ramo_anio.csv", index=False)
    check("K16", "identidad prima de riesgo = frecuencia positiva x severidad media positiva en todos los ramos y años",
          bool(np.allclose(pr["prima_riesgo_T0_CU"], pr["identidad_freq_x_sev"], rtol=1e-6)))

    # comprobación de la desviación cerrada para p=1,5
    yy = np.array([0.0, 0.0, 12.5, 3000.0, 1.0])
    mm = np.array([100.0, 2.0, 10.0, 2500.0, 0.5])
    closed_form = 4.0 * (np.sqrt(mm) - np.sqrt(yy)) ** 2 / np.sqrt(mm)
    check("K17", "la desviación Tweedie p=1,5 coincide con la forma cerrada 4(sqrt(mu)-sqrt(y))^2/sqrt(mu)", bool(np.allclose(tweedie_deviance(yy, mm), closed_form)))

    m00_rows = []
    splits = {"V22": ([2021], 2022), "V23": ([2021, 2022], 2023), "V24": ([2021, 2022, 2023], 2024)}
    for split, (train_years, eval_year) in splits.items():
        tr = t0_rows[t0_rows.year.isin(train_years)]
        ev = t0_rows[t0_rows.year == eval_year].copy()
        q_bal = tr.groupby("line")["T0"].sum() / tr.groupby("line")["exposure"].sum()
        q_tw = (tr.T0 / np.sqrt(tr.exposure)).groupby(tr.line).sum() / np.sqrt(tr.exposure).groupby(tr.line).sum()
        q_glob_bal = tr.T0.sum() / tr.exposure.sum()
        ev["m_bal"] = ev.exposure * ev.line.map(q_bal)
        ev["m_tw"] = ev.exposure * ev.line.map(q_tw)
        ev["m_glob"] = ev.exposure * q_glob_bal
        ev["m_const"] = tr.T0.mean()
        rowd = {"split": split, "train": "-".join(map(str, train_years)), "eval": eval_year, "filas_eval": int(len(ev)),
                "d2_constante_por_fila": r(d2_tweedie(ev.T0.values, ev.m_const.values), 5),
                "d2_tasa_global_x_exposicion": r(d2_tweedie(ev.T0.values, ev.m_glob.values), 5),
                "d2_tasa_ramo_balance_x_exposicion": r(d2_tweedie(ev.T0.values, ev.m_bal.values), 5),
                "d2_tasa_ramo_tweedie_x_exposicion": r(d2_tweedie(ev.T0.values, ev.m_tw.values), 5)}
        for line in LINES:
            evl = ev[ev.line == line]
            rowd[f"q_balance_{line}"] = r(float(q_bal[line]), 4)
            rowd[f"q_tweedie_{line}"] = r(float(q_tw[line]), 4)
            rowd[f"d2_ramo_{line}_balance"] = r(d2_tweedie(evl.T0.values, evl.m_bal.values), 5)
            rowd[f"d2_ramo_{line}_tweedie"] = r(d2_tweedie(evl.T0.values, evl.m_tw.values), 5)
            rowd[f"balance_{line}_pred_sobre_obs"] = r(float(evl.m_bal.sum() / evl.T0.sum()), 4)
        m00_rows.append(rowd)
    prod = t0_rows
    q_bal_prod = prod.groupby("line")["T0"].sum() / prod.groupby("line")["exposure"].sum()
    q_tw_prod = (prod.T0 / np.sqrt(prod.exposure)).groupby(prod.line).sum() / np.sqrt(prod.exposure).groupby(prod.line).sum()
    m00 = pd.DataFrame(m00_rows)
    m00.to_csv(tables_dir / "referencias_M00.csv", index=False)
    check("K18", "en los tres cortes: D² de la constante por fila dentro de ±0,01 y D² de tasa por ramo x exposición > tasa global x exposición > 0",
          bool((m00["d2_constante_por_fila"].abs() < 0.01).all() and (m00["d2_tasa_ramo_balance_x_exposicion"] > m00["d2_tasa_global_x_exposicion"]).all() and (m00["d2_tasa_global_x_exposicion"] > 0).all()),
          m00[["split", "d2_constante_por_fila", "d2_tasa_global_x_exposicion", "d2_tasa_ramo_balance_x_exposicion"]].to_dict(orient="records"))

    # ------------------------------------------------------------------ 10. evidencia y manifiesto
    evidence = {
        "run_id": run_id,
        "created_utc": started.isoformat(timespec="seconds"),
        "author": "Claude (Cowork), a solicitud del participante; cálculo propio asistido por IA sin revisión humana ni independiente",
        "scope": {"data_modified": False, "indices_modified": False, "models_trained": False, "remote_execution": False, "external_providers": False,
                  "description": "Bases actuariales (expuestos, asignación, T0, retraso e IBNR de conteos, frecuencia, severidad, reservas de caso, referencias M00) sobre la capa preparada vigente"},
        "provenance": {"active_index": "Hackaton/Semana 1/Limpieza/current_dataset.json", "active_run": current["workspace_relative_run"], "active_status": current["status"],
                       "catalog_sha256": digest(catalog_path), "tables_sha256": hashes, "cutoff_observed": str(observed_cutoff.date()), "power_eval": POWER},
        "assignment": {"by_line_category": {line: {cat: int(cat_counts.loc[line].get(cat, 0)) for cat in cat_counts.columns} for line in LINES},
                       "accepted_unique_by_line": got_unique_accepted, "accepted_unique_total": int(sum(got_unique_accepted.values())),
                       "accepted_reported_by_line": {line: int(claims[(claims.line == line) & claims.accepted].shape[0]) for line in LINES},
                       "out_of_window": fuera_desc, "pre00_claims": 413, "pre00_accepted_net_CU": r(float(claims.loc[claims.audit_pre00 & claims.accepted, "net"].sum()), 2)},
        "t0": {"total_CU": r(float(t0_rows.T0.sum()), 2), "by_line_CU": {line: r(float(t0_rows.loc[t0_rows.line == line, "T0"].sum()), 2) for line in LINES},
               "rows_train": int(len(t0_rows)), "rows_with_positive_cost": int((t0_rows.T0 > 0).sum()), "accepted_net_zero": int((acc.net == 0).sum()),
               "open_claims_assigned": int(acc.is_open.sum()), "reserve_open_total_CU": r(float(acc.loc[acc.is_open, "reserve"].sum()), 2)},
        "exposure": {"train_total_years": r(train_exposure_total, 4), "test_total_years": r(test_exposure_total, 4),
                     "by_line_year": exp_line_year.round(4).to_dict(orient="records"), "motor_by_cover": exp_cover.round(4).to_dict(orient="records"),
                     "by_line_month_2024": {line: [r(float(v), 2) for v in month_exposure[LINES.index(line), 36:48]] for line in LINES},
                     "by_line_month_2025": {line: [r(float(v), 2) for v in month_exposure[LINES.index(line), 48:60]] for line in LINES}},
        "reporting": {"chain_ladder_by_peril": cl.to_dict(orient="records"), "delay_by_cohort": delay_rows, "long_tail_perils": [list(x) for x in sorted(LONG_TAIL)],
                      "method": "chain-ladder de conteos acumulados por cohorte mensual de ocurrencia y lag mensual de reporte, factores ponderados por volumen, cola exponencial solo en lesiones y hundimiento"},
        "ibnr_2024": {"by_peril": ult.to_dict(orient="records"), "by_line": ult_line.round(4).to_dict(orient="records"),
                      "note": "IBNR de notificaciones por chain-ladder; positivos = notificaciones x probabilidad de coste positivo (2021-2024); coste = positivos x severidad media 2021-2022 (en lesiones y hundimiento, media de los reportados a más de 365 días)"},
        "ibnr_by_year": {"by_peril_year": ibnr_year.to_dict(orient="records"), "risk_premium_ultimate_by_line_year": prima_ult.to_dict(orient="records")},
        "frequency": {"by_line_year_peril": freq.to_dict(orient="records"), "motor_by_cover": freq_cover},
        "severity": {"by_line_peril": sev.to_dict(orient="records"), "share_positive_among_accepted": {f"{k[0]}|{k[1]}": r(float(v), 4) for k, v in share_positive.items()}},
        "case_reserves": {"by_line_peril_year": res.to_dict(orient="records"), "by_line_year": res_line_year.round(4).to_dict(orient="records")},
        "risk_premium": {"by_line_year": pr.to_dict(orient="records")},
        "m00": {"splits": m00.to_dict(orient="records"), "production_2021_2024": {line: {"q_balance": r(float(q_bal_prod[line]), 4), "q_tweedie": r(float(q_tw_prod[line]), 4)} for line in LINES},
                "deviance_closed_form_p15": "4*(sqrt(mu)-sqrt(y))^2/sqrt(mu)"},
        "checks": checks,
        "checks_summary": {"checks_total": len(checks), "checks_passed": sum(c["passed"] for c in checks), "all_passed": all(c["passed"] for c in checks)},
    }
    (run_dir / "evidencia.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=1, default=lambda o: r(o) if isinstance(o, (np.floating, np.integer)) else str(o)), encoding="utf-8")
    pd.DataFrame(checks).to_csv(tables_dir / "controles.csv", index=False)
    shutil.copy2(Path(__file__), run_dir / Path(__file__).name)
    manifest = {}
    for path in sorted(run_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            manifest[str(path.relative_to(run_dir)).replace("\\", "/")] = digest(path)
    (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    summary = evidence["checks_summary"]
    print(f"Corrida {run_id}: {summary['checks_passed']}/{summary['checks_total']} controles; T0 total {evidence['t0']['total_CU']:,} CU")
    for c in checks:
        print(("OK  " if c["passed"] else "FALLA ") + c["code"] + " " + c["name"] + ("" if c["passed"] else f" -> {c['detail']}"))
    if not summary["all_passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
