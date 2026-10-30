"""A05: end the 365-day history window at min(policy start, valuation date).
Avoid interpreting an unobserved future interval as zero notifications. Only
post-valuation 2025 starts change; earlier rows must remain identical.
"""
import numpy as np, pandas as pd
from comun import *
INICIO = {"developed": "2021-01-01", "emerging": "2023-01-01"}
FIN = pd.Timestamp(str(V))
for m in ["developed", "emerging"]:
    c = pd.read_parquet(DATOS / m / "claims.parquet", columns=["claim_id", "policy_id", "line", "report_date", "loss_date"])
    c["report_date"] = pd.to_datetime(c.report_date)
    if m == "developed":
        full = pd.read_parquet(DATOS / m / "claims.parquet")
        cols = [x for x in full.columns if x != "claim_id"]
        q = full.duplicated(cols, keep=False) & (full.claim_id.str.len() == 11)
        c = c[~q.values]
    bases = {l: pd.read_parquet(TRABAJO / f"base_{m}_{l}.parquet", columns=["row_id", "policy_id", "customer_id", "line", "period_start"]) for l in LINEAS}
    mapa = pd.concat([b[["policy_id", "line", "customer_id"]] for b in bases.values()]).drop_duplicates(["policy_id", "line"])
    cc = c.merge(mapa, on=["policy_id", "line"])
    for l, df in bases.items():
        df["period_start"] = pd.to_datetime(df.period_start)
        df["fin"] = df.period_start.where(df.period_start <= FIN, FIN)
        ok = (df.fin - pd.Timedelta(days=365)) >= pd.Timestamp(INICIO[m])
        hp = c[c.line == l][["policy_id", "report_date"]].merge(df[["row_id", "policy_id", "fin"]], on="policy_id")
        hp = hp[(hp.report_date < hp.fin) & (hp.report_date >= hp.fin - pd.Timedelta(days=365))]
        hc = cc[["customer_id", "report_date"]].merge(df[["row_id", "customer_id", "fin"]], on="customer_id")
        hc = hc[(hc.report_date < hc.fin) & (hc.report_date >= hc.fin - pd.Timedelta(days=365))]
        out = pd.DataFrame({"row_id": df.row_id,
                            "hist_pol_12m": df.row_id.map(hp.groupby("row_id").size()).fillna(0).where(ok, np.nan),
                            "hist_cli_12m": df.row_id.map(hc.groupby("row_id").size()).fillna(0).where(ok, np.nan)})
        old = pd.read_parquet(TRABAJO / f"historia_{m}_{l}.parquet")
        assert (old.row_id.values == out.row_id.values).all()
        tarde = (df.period_start > FIN).values
        for v in ["hist_pol_12m", "hist_cli_12m"]:
            a, b = old[v].values[~tarde], out[v].values[~tarde]
            assert np.array_equal(np.isnan(a), np.isnan(b)) and np.allclose(np.nan_to_num(a), np.nan_to_num(b)), (m, l, v)
        out.to_parquet(TRABAJO / f"historia2_{m}_{l}.parquet", index=False)
        if tarde.any():
            print(m, l, "filas tras V:", int(tarde.sum()), "media hist_pol antes/después:",
                  round(float(np.nanmean(old.hist_pol_12m.values[tarde])), 4), round(float(np.nanmean(out.hist_pol_12m.values[tarde])), 4),
                  "cli:", round(float(np.nanmean(old.hist_cli_12m.values[tarde])), 4), round(float(np.nanmean(out.hist_cli_12m.values[tarde])), 4), flush=True)
