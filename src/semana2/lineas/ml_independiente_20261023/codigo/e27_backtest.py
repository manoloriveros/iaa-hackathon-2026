"""E27, diagnóstico preinscrito: la regla con 2023 solo aplicada a T2b en 2024 (HOLD, exploratorio).
Con un solo año no hay var_año: sigma = bootstrap por cliente de 2023 (se declara)."""
import json, numpy as np, pandas as pd
from comun import *
from receta import tabla, componentes
TAU, K = 0.07, 200.0
rows = []
for l in LINEAS:
    b = pd.read_parquet(TRABAJO / f"base_emerging_{l}.parquet", columns=["row_id", "customer_id", "year", "conjunto", "y", "n_sin", "c_fila", "exposure", "written_premium", "new_business"])
    rows.append(b.assign(line=l))
d = pd.concat(rows, ignore_index=True); d["seg"] = d.line + "|" + np.where(d.new_business, "NB", "REN"); d["P"] = d.written_premium * d.exposure
h = d[(d.conjunto == "train") & (d.year == 2023)].reset_index(drop=True); h["U"] = h.y / h.c_fila
th = tabla("hold"); mu = componentes("hold", ["T2b"], th)["T2b"]
t = th.merge(d[["row_id", "seg", "P"]], on="row_id", how="left"); t["mu"] = mu
def lrs(w):
    o = {}
    for l in LINEAS:
        il = (h.line == l).values; lr_l = np.sum(w[il] * h.U.values[il]) / np.sum(w[il] * h.P.values[il])
        for s in ("NB", "REN"):
            m = il & (h.seg == f"{l}|{s}").values
            n = np.sum(w[m] * h.n_sin.values[m]); z = n / (n + K)
            o[f"{l}|{s}"] = z * np.sum(w[m] * h.U.values[m]) / np.sum(w[m] * h.P.values[m]) + (1 - z) * lr_l
    return o
c0 = lrs(np.ones(len(h))); cli, idx = np.unique(h.customer_id.values, return_inverse=True)
rng = np.random.default_rng(20261024); sims = [lrs(rng.poisson(1.0, len(cli))[idx].astype(float)) for _ in range(500)]
f = {}; res = {}
for s in c0:
    m = (t.seg == s).values
    g = c0[s] * t.P.values[m].sum() / t.mu.values[m].sum()
    sig2 = np.var([np.log(x[s]) for x in sims]); z = TAU ** 2 / (TAU ** 2 + sig2)
    f[s] = float(np.clip(np.exp(z * np.log(g)), 0.85, 1.15))
    ae = t.y.values[m].sum() / (t.mu.values[m] * t.c_fila.values[m]).sum()
    res[s] = {"g": g, "sigma_boot": float(np.sqrt(sig2)), "Z": z, "f": f[s], "AE_T2b_2024": float(ae)}
mu2 = t.mu.values * t.seg.map(f).values
out = {"segmentos": res, "D2_T2b": d2(t.y.values, t.mu.values * t.c_fila.values), "D2_con_f": d2(t.y.values, mu2 * t.c_fila.values),
       "D2_con_g_pleno": d2(t.y.values, t.mu.values * t.seg.map({s: r["g"] for s, r in res.items()}).values * t.c_fila.values)}
for s, r in res.items(): print(s, {k: round(v, 3) for k, v in r.items()})
print("D2 2024: T2b %.4f, con f %.4f, con g sin credibilidad %.4f" % (out["D2_T2b"], out["D2_con_f"], out["D2_con_g_pleno"]))
guardar_json(out, ENTREGA / "nivel2025" / "e27_backtest_2024.json")
