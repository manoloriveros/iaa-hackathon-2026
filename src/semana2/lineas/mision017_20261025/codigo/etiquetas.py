"""y (T0) y c_fila por fila del emergente, réplica reducida de preparar_datos.py de la línea ML independiente."""
import numpy as np, pandas as pd, json
V = np.datetime64("2024-12-31"); D = 1095; L = ["motor", "buildings", "contents"]
def sin(p, dev):
    c = pd.read_parquet(p)
    if dev:
        cols = [x for x in c.columns if x != "claim_id"]; c = c[~(c.duplicated(cols, keep=False) & (c.claim_id.str.len() == 11))].copy()
    c["loss_date"] = pd.to_datetime(c.loss_date); c["report_date"] = pd.to_datetime(c.report_date)
    c["neto"] = c.incurred_to_date - c.recoveries; c["aceptado"] = c.status != "repudiated"; return c
cd = sin("datos/developed/claims.parquet", True); ce = sin("datos/emerging/claims.parquet", False)
G = {}
for (l, p), g in cd[cd.aceptado].groupby(["line", "peril"]):
    g = g[(V - g.loss_date.values.astype("datetime64[D]")).astype(int) >= D]
    dly = (g.report_date - g.loss_date).dt.days.values; w = g.neto.values; ok = dly <= D
    cum = np.clip(np.bincount(dly[ok], weights=w[ok], minlength=D + 1).cumsum() / w[ok].sum(), 0, 1)
    G[(l, p)] = np.concatenate([[0.0], np.cumsum(np.concatenate([cum, np.ones(4000 - len(cum))]))])
def comp(l, p, s, e):
    g = G[(l, p)]; a = np.clip((V - e).astype(int), 0, None); b = np.clip((V - s).astype(int), 0, None); return (g[b + 1] - g[a]) / (b - a + 1)
out = []
for l in L:
    tr = pd.read_parquet(f"datos/emerging/policies_{l}.parquet"); tr["conjunto"] = "train"
    te = pd.read_parquet(f"datos/emerging/test_{l}.parquet"); te["conjunto"] = "test"
    df = pd.concat([tr, te], ignore_index=True); df["line"] = l
    df["period_start"] = pd.to_datetime(df.period_start); df["period_end"] = pd.to_datetime(df.period_end)
    df["exposure"] = ((df.period_end - df.period_start).dt.days + 1) / 365.0; df["year"] = df.period_start.dt.year
    cl = ce[ce.line == l]
    mm = cl.merge(df[["row_id", "policy_id", "period_start", "period_end"]], on="policy_id")
    mm = mm[(mm.loss_date >= mm.period_start) & (mm.loss_date <= mm.period_end)]; acc = mm[mm.aceptado]
    df["y"] = df.row_id.map(acc.groupby("row_id").neto.sum()).fillna(0.0); df.loc[df.conjunto == "test", "y"] = np.nan
    perils = sorted(cl.peril.unique())
    for p_ in perils: df[f"y_{p_}"] = df.row_id.map(acc[acc.peril == p_].groupby("row_id").neto.sum()).fillna(0.0)
    s = df.period_start.values.astype("datetime64[D]"); e = df.period_end.values.astype("datetime64[D]")
    cp = {p_: comp(l, p_, s, e) for p_ in perils}; t = df.conjunto == "train"
    ult = {p_: df.loc[t, f"y_{p_}"].sum() / max(np.average(cp[p_][t], weights=df.exposure[t]), 1e-6) for p_ in perils}
    tot = sum(ult.values()); df["c_fila"] = sum(ult[p_] / tot * cp[p_] for p_ in perils); df.loc[~t, "c_fila"] = 1.0
    df["start_month"] = df.period_start.dt.month
    out.append(df[["row_id", "line", "conjunto", "year", "exposure", "new_business", "start_month", "customer_id", "y", "c_fila", "written_premium"]])
b = pd.concat(out, ignore_index=True); b.to_parquet("base_etiquetas.parquet", index=False)
print(b.groupby(["conjunto", "year"]).agg(n=("row_id", "size"), y=("y", "sum"), cf=("c_fila", "mean")))
print("T0 total", round(b.y.sum(), 2))
