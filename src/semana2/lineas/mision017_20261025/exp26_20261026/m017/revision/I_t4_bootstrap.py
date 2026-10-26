"""Tarea 4 (y base de la 7): bootstrap por cliente (remuestreo global de clientes, mismo peso en ambos años y en
todas las líneas) de la ganancia fuera de tiempo secuencial. Se reestima todo (nivelación, factores) en cada réplica.
Variantes de ponderación del año de prueba: sin pesos; composición 2025 por celda (NB/REN); por celda × banda de
exposición (<0,5 / 0,5-0,9 / >=0,9)."""
import sys, json, time
sys.path.insert(0, "/home/claude/m017/revision")
import numpy as np, pandas as pd
from I_lib import *

NB_ = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
OUT = "/home/claude/m017/revision"
df = cargar()
b = pd.read_parquet(f"{R}/base_etiquetas.parquet")


def banda(e):
    return np.where(e < 0.5, "c", np.where(e < 0.9, "m", "l"))


t25 = b[b.year == 2025]
DIRS = ((2023, 2024), (2024, 2023))
lines = {l: Linea(df, l) for l in VARS}
WX = {}
for l, L in lines.items():
    s25 = t25[t25.line == l]
    k25 = pd.Series(s25.new_business.astype(int).astype(str).values + banda(s25.exposure.values)).value_counts(normalize=True)
    c25 = s25.new_business.astype(int).value_counts(normalize=True)
    for yr in (2023, 2024):
        B = L.yr[yr]
        kk = pd.Series(B["cell"].astype(str) + banda(B["expo"]))
        sh = kk.value_counts(normalize=True)
        w_cb = (kk.map(k25) / kk.map(sh)).values
        cs = pd.Series(B["cell"]).value_counts(normalize=True)
        w_c = (pd.Series(B["cell"]).map(c25) / pd.Series(B["cell"]).map(cs)).values
        WX[(l, yr)] = {"none": None, "cell25": w_c, "cellband25": w_cb}

allc = pd.Index(pd.unique(df.customer_id))
cmap = {l: allc.get_indexer(L.cust_uni) for l, L in lines.items()}
CONF = [(300, "none"), (300, "cell25"), (300, "cellband25"), (150, "none"), (600, "none")]


def una(wglob):
    rec = []
    for l, L in lines.items():
        w = None if wglob is None else wglob[cmap[l]]
        vs = VARS[l]
        for tr, te in DIRS:
            for K, wn in CONF:
                gs = oot(L, tr, te, vs, K, w=w, steps=True, wx=WX[(l, te)][wn])
                for j, g in enumerate(gs):
                    rec.append(dict(line=l, dir=f"{tr}->{te}", K=K, wt=wn, step="+".join(vs[:j + 1]),
                                    all=g["all"], nb=g["nb"], ren=g["ren"]))
    return rec


real = pd.DataFrame(una(None))
rng = np.random.default_rng(4242)
rows = []
t0 = time.time()
for r in range(NB_):
    cnt = np.bincount(rng.integers(0, len(allc), len(allc)), minlength=len(allc)).astype(float)
    for d in una(cnt):
        d["rep"] = r
        rows.append(d)
    if r % 100 == 0:
        print(r, round(time.time() - t0, 1), flush=True)
bt = pd.DataFrame(rows)
bt.to_csv(f"{OUT}/I_t4_bootstrap.csv", index=False)
real.to_csv(f"{OUT}/I_t4_real.csv", index=False)

key = ["line", "dir", "K", "wt", "step"]
summ = []
for k, g in bt.groupby(key):
    rr = real.set_index(key).loc[k]
    d = dict(zip(key, k))
    for c in ("all", "nb", "ren"):
        d[f"{c}_obs"] = rr[c]
        d[f"{c}_p05"] = g[c].quantile(.05)
        d[f"{c}_p95"] = g[c].quantile(.95)
        d[f"{c}_Pneg"] = (g[c] < 0).mean()
    summ.append(d)
S = pd.DataFrame(summ)
S.to_csv(f"{OUT}/I_t4_resumen.csv", index=False)
pd.set_option("display.width", 250)
v = S.copy()
for c in v.columns:
    if c.endswith(("_obs", "_p05", "_p95")):
        v[c] = (v[c] * 1e4).round(1)
    elif c.endswith("_Pneg"):
        v[c] = v[c].round(3)
print(v.to_string(index=False))
