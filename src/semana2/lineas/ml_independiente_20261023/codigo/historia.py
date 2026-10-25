"""Historia de avisos en ventana de 365 días por póliza y por cliente (todos los ramos)."""
import numpy as np, pandas as pd
from comun import *
INICIO = {"developed": "2021-01-01", "emerging": "2023-01-01"}
for m in ["developed", "emerging"]:
    c = pd.read_parquet(DATOS / m / "claims.parquet", columns=["claim_id", "policy_id", "line", "report_date", "loss_date"])
    c["report_date"] = pd.to_datetime(c.report_date)
    if m == "developed":  # mismos duplicados que en preparar_datos
        full = pd.read_parquet(DATOS / m / "claims.parquet")
        cols = [x for x in full.columns if x != "claim_id"]
        q = full.duplicated(cols, keep=False) & (full.claim_id.str.len() == 11)
        c = c[~q.values]
    bases = {l: pd.read_parquet(TRABAJO / f"base_{m}_{l}.parquet", columns=["row_id", "policy_id", "customer_id", "line", "period_start"]) for l in LINEAS}
    mapa = pd.concat([b[["policy_id", "line", "customer_id"]] for b in bases.values()]).drop_duplicates(["policy_id", "line"])
    cc = c.merge(mapa, on=["policy_id", "line"])
    for l, df in bases.items():
        df["period_start"] = pd.to_datetime(df.period_start)
        ok = (df.period_start - pd.Timedelta(days=365)) >= pd.Timestamp(INICIO[m])
        hp = c[c.line == l][["policy_id", "report_date"]].merge(df[["row_id", "policy_id", "period_start"]], on="policy_id")
        hp = hp[(hp.report_date < hp.period_start) & (hp.report_date >= hp.period_start - pd.Timedelta(days=365))]
        hc = cc[["customer_id", "report_date"]].merge(df[["row_id", "customer_id", "period_start"]], on="customer_id")
        hc = hc[(hc.report_date < hc.period_start) & (hc.report_date >= hc.period_start - pd.Timedelta(days=365))]
        out = pd.DataFrame({"row_id": df.row_id,
                            "hist_pol_12m": df.row_id.map(hp.groupby("row_id").size()).fillna(0).where(ok, np.nan),
                            "hist_cli_12m": df.row_id.map(hc.groupby("row_id").size()).fillna(0).where(ok, np.nan)})
        out.to_parquet(TRABAJO / f"historia_{m}_{l}.parquet", index=False)
        print(m, l, out.hist_pol_12m.notna().mean().round(3), out.hist_pol_12m.mean().round(4), out.hist_cli_12m.mean().round(4))
