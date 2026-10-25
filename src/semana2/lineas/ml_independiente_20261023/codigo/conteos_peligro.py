"""Conteo de siniestros aceptados por peligro y fila (misma asignación que preparar_datos.py).

Salida: trabajo/conteos_{mercado}_{ramo}.parquet con row_id y n_{peligro}. Comprueba que la suma
por peligro reproduce n_sin y que el coste por peligro reproduce y_{peligro}.
"""
import numpy as np, pandas as pd
from comun import *

for m in ["developed", "emerging"]:
    c = pd.read_parquet(DATOS / m / "claims.parquet")
    if m == "developed":
        cols = [x for x in c.columns if x != "claim_id"]
        c = c[~(c.duplicated(cols, keep=False) & (c.claim_id.str.len() == 11))]
    c = c[c.status != "repudiated"].copy()
    c["loss_date"] = pd.to_datetime(c.loss_date)
    c["neto"] = c.incurred_to_date - c.recoveries
    for l in LINEAS:
        b = pd.read_parquet(TRABAJO / f"base_{m}_{l}.parquet")
        mm = c[c.line == l].merge(b[["row_id", "policy_id", "period_start", "period_end"]], on="policy_id")
        mm = mm[(mm.loss_date >= pd.to_datetime(mm.period_start)) & (mm.loss_date <= pd.to_datetime(mm.period_end))]
        out = pd.DataFrame({"row_id": b.row_id.values})
        perils = sorted(c[c.line == l].peril.unique())
        for p in perils:
            g = mm[mm.peril == p]
            out[f"n_{p}"] = out.row_id.map(g.groupby("row_id").size()).fillna(0).astype(int)
            cost = out.row_id.map(g.groupby("row_id").neto.sum()).fillna(0.0)
            tr = (b.conjunto == "train").values
            assert np.allclose(cost.values[tr], b[f"y_{p}"].values[tr]), (m, l, p)
        tr = (b.conjunto == "train").values
        assert (out[[f"n_{p}" for p in perils]].sum(1).values[tr] == b.n_sin.values[tr]).all(), (m, l)
        out.to_parquet(TRABAJO / f"conteos_{m}_{l}.parquet", index=False)
        print(m, l, {p: int(out[f"n_{p}"].values[tr].sum()) for p in perils}, flush=True)
