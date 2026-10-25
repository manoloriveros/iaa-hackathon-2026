"""Etiquetas, completitud de reporte y esquema común de variables (línea ML independiente).

Salida: trabajo/base_{mercado}_{ramo}.parquet y trabajo/preparacion.json.
Todo se calcula desde los Parquet originales con huella comprobada.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from comun import *

TRABAJO.mkdir(parents=True, exist_ok=True)
info = {"huellas": comprobar_huellas()}

UMBRAL_CAPITAL = {"buildings": 5_000_000, "contents": 2_000_000}
CLIMA = ["wind_exposure_index", "wildfire_index", "rainfall_mm", "mean_temperature_c"]
CONSTR = {"brick": "brick", "brk": "brick", "stone": "stone", "stn": "stone", "t": "timber", "w": "timber",
          "wod": "timber", "non_standard": "non_standard", "mix": "non_standard"}


def banda_edad(a):
    return pd.cut(a, [-1, 24, 34, 49, 64, 200], labels=["17-24", "25-34", "35-49", "50-64", "65+"]).astype(str)


def leer_polizas(m):
    out = {}
    for l in LINEAS:
        tr = pd.read_parquet(DATOS / m / f"policies_{l}.parquet")
        tr["conjunto"] = "train"
        if m == "emerging":
            te = pd.read_parquet(DATOS / m / f"test_{l}.parquet"); te["conjunto"] = "test"
            tr = pd.concat([tr, te], ignore_index=True)
        tr["line"] = l
        out[l] = tr
    return out


def siniestros(m):
    c = pd.read_parquet(DATOS / m / "claims.parquet")
    n0 = len(c)
    if m == "developed":
        cols = [x for x in c.columns if x != "claim_id"]
        dup = c.duplicated(cols, keep=False)
        quitar = dup & (c.claim_id.str.len() == 11)
        c = c[~quitar].copy()
        info[f"{m}_duplicados_retirados"] = int(quitar.sum())
    c["loss_date"] = pd.to_datetime(c.loss_date); c["report_date"] = pd.to_datetime(c.report_date)
    c["neto"] = c.incurred_to_date - c.recoveries
    c["aceptado"] = c.status != "repudiated"
    info[f"{m}_siniestros"] = {"leidos": n0, "usados": len(c), "rechazados": int((~c.aceptado).sum()),
                                "neto_negativo": int((c.neto < 0).sum())}
    return c


# ---------- 1. completitud de reporte ponderada por coste (desarrollado, cohortes maduras) ----------
cd = siniestros("developed")
ce = siniestros("emerging")
D = 1095
F = {}
resumen_cdf = {}
for (l, p), g in cd[cd.aceptado].groupby(["line", "peril"]):
    g = g[(V - g.loss_date.values.astype("datetime64[D]")).astype(int) >= D]
    dly = (g.report_date - g.loss_date).dt.days.values
    w = g.neto.values
    ok = dly <= D
    tot = w[ok].sum()
    cum = np.bincount(dly[ok], weights=w[ok], minlength=D + 1).cumsum() / tot
    F[(l, p)] = np.clip(cum, 0, 1)
    resumen_cdf[f"{l}|{p}"] = {k: round(float(cum[k]), 4) for k in [0, 30, 90, 180, 365, 730]}
    resumen_cdf[f"{l}|{p}"]["n"] = int(ok.sum())
info["cdf_coste_desarrollado"] = resumen_cdf
# contraste emergente: cohorte 2023 con al menos 365 días, cociente F(d)/F(365)
contraste = {}
for (l, p), g in ce[ce.aceptado & (ce.loss_date.dt.year == 2023)].groupby(["line", "peril"]):
    g = g[(V - g.loss_date.values.astype("datetime64[D]")).astype(int) >= 365]
    dly = (g.report_date - g.loss_date).dt.days.values
    w = g.neto.values; ok = dly <= 365
    if ok.sum() < 20: continue
    em = [float(w[ok & (dly <= d)].sum() / w[ok].sum()) for d in (30, 90, 180)]
    dv = [float(F[(l, p)][d] / F[(l, p)][365]) for d in (30, 90, 180)]
    contraste[f"{l}|{p}"] = {"n": int(ok.sum()), "emergente_30_90_180": [round(x, 4) for x in em],
                              "desarrollado_30_90_180": [round(x, 4) for x in dv]}
info["contraste_reporte_emergente_2023"] = contraste
G = {k: np.concatenate([[0.0], np.cumsum(np.concatenate([v, np.ones(4000 - len(v))]))]) for k, v in F.items()}


def completitud_media(l, p, s, e):
    """Media de F(V - t) para t en [s, e]; G[x+1] = sum_{d<=x} F(d)."""
    g = G[(l, p)]
    a = (V - e).astype(int); b = (V - s).astype(int)
    a = np.clip(a, 0, None); b = np.clip(b, 0, None)
    return (g[b + 1] - g[a]) / (b - a + 1)


# ---------- 2. bases por mercado ----------
for m in ["developed", "emerging"]:
    c = cd if m == "developed" else ce
    pol = leer_polizas(m)
    cu = pd.read_parquet(DATOS / m / "customers.parquet")
    ad = pd.read_parquet(DATOS / m / "addresses.parquet")
    we = pd.read_parquet(DATOS / m / "weather.parquet")
    # pesos por peligro (coste aceptado de la cohorte más madura del mercado, corregido por completitud media)
    for l in LINEAS:
        df = pol[l].copy()
        n_in = len(df)
        if m == "developed" and l == "motor":
            df["customer_id"] = df.customer_id.str.zfill(8)
        df["period_start"] = pd.to_datetime(df.period_start); df["period_end"] = pd.to_datetime(df.period_end)
        df["exposure_original"] = df.exposure
        df["exposure"] = ((df.period_end - df.period_start).dt.days + 1) / 365.0
        df["year"] = df.period_start.dt.year
        # capital
        if l in UMBRAL_CAPITAL:
            df["sum_insured_raw"] = df.sum_insured
            adj = df.sum_insured > UMBRAL_CAPITAL[l]
            df["audit_capital_div1000"] = adj
            df["sum_insured"] = np.where(adj, df.sum_insured / 1000, df.sum_insured)
            info[f"{m}_{l}_capital_div1000"] = {"train": int((adj & (df.conjunto == "train")).sum()),
                                                  "test": int((adj & (df.conjunto == "test")).sum())}
        # asignación de siniestros
        cl = c[c.line == l]
        mm = cl.merge(df[["row_id", "policy_id", "period_start", "period_end"]], on="policy_id", how="inner")
        mm = mm[(mm.loss_date >= mm.period_start) & (mm.loss_date <= mm.period_end)]
        dup = mm.claim_id.duplicated(keep=False).sum()
        asign = mm.claim_id.nunique()
        info[f"{m}_{l}_asignacion"] = {"siniestros_ramo": int(len(cl)), "asignados": int(asign),
                                        "ambiguos": int(dup), "sin_periodo": int(len(cl) - asign)}
        acc = mm[mm.aceptado]
        y = acc.groupby("row_id").neto.sum()
        df["y"] = df.row_id.map(y).fillna(0.0)
        df.loc[df.conjunto == "test", "y"] = np.nan
        df["n_sin"] = df.row_id.map(acc.groupby("row_id").size()).fillna(0)
        for p_ in sorted(cl.peril.unique()):
            df[f"y_{p_}"] = df.row_id.map(acc[acc.peril == p_].groupby("row_id").neto.sum()).fillna(0.0)
        # completitud por fila
        s = df.period_start.values.astype("datetime64[D]"); e = df.period_end.values.astype("datetime64[D]")
        perils = sorted(cl.peril.unique())
        comp = {p_: completitud_media(l, p_, s, e) for p_ in perils}
        # pesos: coste aceptado del mercado en años completos de entrenamiento, dividido por completitud media
        tr = df.conjunto == "train"
        cost = {p_: df.loc[tr, f"y_{p_}"].sum() for p_ in perils}
        ult = {p_: cost[p_] / max(np.average(comp[p_][tr], weights=df.exposure[tr]), 1e-6) for p_ in perils}
        tot = sum(ult.values())
        wpk = {p_: ult[p_] / tot for p_ in perils}
        df["c_fila"] = sum(wpk[p_] * comp[p_] for p_ in perils)
        df.loc[df.conjunto == "test", "c_fila"] = 1.0
        info[f"{m}_{l}_pesos_peligro"] = {k: round(v, 4) for k, v in wpk.items()}
        info[f"{m}_{l}_completitud_media_por_anio"] = df[tr].groupby("year").apply(
            lambda g: float(np.average(g.c_fila, weights=g.exposure))).round(4).to_dict()
        # historia (avisos reportados antes del inicio, cualquier estado)
        hp = c[c.line == l][["policy_id", "report_date"]].merge(df[["row_id", "policy_id", "period_start"]], on="policy_id")
        hp = hp[hp.report_date < hp.period_start]
        df["hist_pol_n"] = df.row_id.map(hp.groupby("row_id").size()).fillna(0)
        df["prev_rows_pol"] = df.groupby("policy_id").period_start.rank(method="first") - 1
        out_rows = df
        pol[l] = out_rows
        assert len(df) == n_in
    # historia de cliente en todos los ramos
    mapa = pd.concat([pol[l][["policy_id", "customer_id"]].assign(line=l) for l in LINEAS]).drop_duplicates(["policy_id", "line"])
    cc = c[["policy_id", "line", "report_date"]].merge(mapa, on=["policy_id", "line"])
    for l in LINEAS:
        df = pol[l]
        h = cc.merge(df[["row_id", "customer_id", "period_start"]], on="customer_id")
        h = h[h.report_date < h.period_start]
        df["hist_cli_n"] = df.row_id.map(h.groupby("row_id").size()).fillna(0)
    # maestros
    cu = cu.copy()
    if m == "emerging":
        occ = cu.occupation.str.lower().str.strip()
        cu["self_employed"] = occ.str.startswith("self-employed")
        cu["occupation"] = occ.str.replace("self-employed ", "", regex=False).str.strip()
    ad = ad.copy()
    ad["energy_rating"] = ad.energy_rating
    for l in LINEAS:
        df = pol[l].merge(cu, on="customer_id", how="left", validate="m:1").merge(ad, on="address_id", how="left", validate="m:1")
        df["tenure_years"] = df.year - df.customer_since_year
        df["property_age"] = df.year - df.year_built
        df["start_month"] = df.period_start.dt.month
        df["start_doy"] = df.period_start.dt.dayofyear
        df["full_year"] = (df.exposure >= 0.99).astype(int)
        df["log_days_quote"] = np.log1p(df.days_quote_to_inception.clip(lower=0))
        wp = df.written_premium / df.exposure
        med = wp.groupby([df.year]).transform("median")
        df["log_wp_rel"] = np.log(wp / med)
        if l == "motor":
            if m == "developed":
                df["driver_age_band"] = banda_edad(df.driver_age)
            df["age_band"] = df.driver_age_band
        else:
            if m == "developed":
                df["policyholder_age_band"] = banda_edad(df.policyholder_age)
            df["age_band"] = df.policyholder_age_band
            df["log_si"] = np.log(df.sum_insured)
        if l == "buildings":
            df["construction"] = df.construction_type.str.lower().map(CONSTR)
            assert df.construction.notna().all(), df.construction_type[df.construction.isna()].unique()
        df["market"] = m
        df["fold"] = pliegue(df.customer_id.values)
        df.to_parquet(TRABAJO / f"base_{m}_{l}.parquet", index=False)
        info[f"{m}_{l}_filas"] = df.conjunto.value_counts().to_dict()
        info[f"{m}_{l}_T0_por_anio"] = df[df.conjunto == "train"].groupby("year").y.sum().round(2).to_dict()
    # clima persistente: medias por dirección para cada ventana de años
    for nombre, anios in ({"developed": {"hasta2023": [2021, 2022, 2023], "hasta2024": [2021, 2022, 2023, 2024]},
                           "emerging": {"hasta2023": [2023], "hasta2024": [2023, 2024]}}[m]).items():
        wm = we[we.year.isin(anios)].groupby("address_id")[CLIMA].mean().add_prefix("clima_")
        wm.reset_index().to_parquet(TRABAJO / f"clima_{m}_{nombre}.parquet", index=False)
guardar_json(info, TRABAJO / "preparacion.json")
print(json.dumps({k: v for k, v in info.items() if k != "huellas" and "cdf" not in k}, indent=0, default=str)[:6000])
