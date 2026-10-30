"""Compare model families on common 2024 rows and production 2025 predictions.

Use the same 59,202 2024 rows and T0 labels, allowing each model's documented
completeness on the observed scale. Bootstrap customer-address components.
For 2025 inspect totals, rates, row correlations and power-1.5 Tweedie Bregman
divergence between predictions, without treating predictions as observed labels.
"""
import json, hashlib
import numpy as np, pandas as pd
from comun import *
from evaluar import tabla_eval
import receta

OTROS = RAIZ / "comparacion" / "otros"
res = {"fuentes": {}, "2024": {}, "2025": {}}
for f in sorted(OTROS.iterdir()):
    res["fuentes"][f.name] = sha256(f)

# 2024 comparison.
o = pd.read_parquet(OTROS / "predicciones_2024.parquet")
lista = json.load(open(ENTREGA / "lista_congelada.json"))
p = receta.parametros("dev", ["T2b"], "ramo")
t, mu_c1 = receta.aplicar("hold", p, None)
p2 = receta.parametros("dev", ["T2b"], "ramo_nb"); _, mu_c2 = receta.aplicar("hold", p2, None)
p3 = receta.parametros("dev", ["R0"], "ramo"); _, mu_r0 = receta.aplicar("hold", p3, None)
d = t.merge(o[["row_id", "address_id", "R0", "A1", "A2", "A3"]], on="row_id", how="inner")
assert len(d) == len(t) == len(o) == 59202
d["MLind_T2b_C1"] = mu_c1 * t.c_fila.values
d["MLind_T2b_C2"] = mu_c2 * t.c_fila.values
d["MLind_R0"] = mu_r0 * t.c_fila.values
d = d.rename(columns={"R0": "noct_R0", "A1": "noct_A1", "A2": "noct_A2", "A3": "noct_A3"})
mods = ["MLind_T2b_C1", "MLind_T2b_C2", "MLind_R0", "noct_R0", "noct_A1", "noct_A2", "noct_A3"]
y = d.y.values
# Customer-address connected components.
padre = {}
def f(x):
    while padre.setdefault(x, x) != x:
        padre[x] = padre[padre[x]]; x = padre[x]
    return x
for c, a in zip("C" + d.customer_id, "A" + d.address_id):
    rc, ra = f(c), f(a)
    if rc != ra: padre[ra] = rc
comp = np.array([f("C" + c) for c in d.customer_id])
_, gi = np.unique(comp, return_inverse=True)
res["2024"]["filas"] = int(len(d)); res["2024"]["componentes"] = int(gi.max() + 1)
for m in mods:
    r = {"D2": d2(y, d[m].values)}
    for l in LINEAS:
        i = (d.line == l).values
        r[f"D2_{l}"] = d2(y[i], d[m].values[i]); r[f"AE_{l}"] = float(y[i].sum() / d[m].values[i].sum())
    for nb in (True, False):
        i = d.new_business.values == nb
        r[f"D2_{'NB' if nb else 'REN'}"] = d2(y[i], d[m].values[i])
    res["2024"][m] = r
rng = np.random.default_rng(20261024)
dev = {m: desviacion(y, d[m].values) for m in mods}
sy = np.sqrt(y); B = 2000
pares = [("MLind_T2b_C1", "noct_A1"), ("MLind_T2b_C1", "noct_R0"), ("MLind_T2b_C2", "noct_A1"), ("noct_A1", "noct_R0"), ("MLind_T2b_C1", "noct_A2")]
boot = {k: [] for k in pares}; boot33 = {k: [] for k in pares}
G = gi.max() + 1
for s in range(0, B, 100):
    W = rng.poisson(1.0, size=(100, G)).astype(float)[:, gi]
    # Sample 33% of components as a public-subset-size diagnostic.
    W33 = (rng.random(size=(100, G)) < 0.33).astype(float)[:, gi]
    for WW, store in ((W, boot), (W33, boot33)):
        ybar = (WW @ y) / WW.sum(1)
        dn = 2 * ((WW @ sy) / (-0.25) - (WW @ y) * ybar ** -0.5 / (-0.5) + WW.sum(1) * ybar ** 0.5 / 0.5)
        for a, b in pares:
            store[(a, b)].append((WW @ dev[b] - WW @ dev[a]) / dn)
res["2024"]["pares"] = {}
for k in pares:
    r = np.concatenate(boot[k]); r33 = np.concatenate(boot33[k])
    res["2024"]["pares"][f"{k[0]} - {k[1]}"] = {"dif": res["2024"][k[0]]["D2"] - res["2024"][k[1]]["D2"],
        "ic95": [float(np.quantile(r, .025)), float(np.quantile(r, .975))], "p_mayor": float((r > 0).mean()),
        "sd_submuestra_33": float(np.std(r33)), "p_mayor_submuestra_33": float((r33 > 0).mean())}
# Correlation between models on 2024 rows.
res["2024"]["corr_log_T2b_A1"] = float(np.corrcoef(np.log(d.MLind_T2b_C1), np.log(d.noct_A1))[0, 1])

# 2025 prediction comparison.
sub = pd.read_parquet(DATOS / "emerging" / "sample_submission.parquet")[["row_id"]]
base = pd.concat([pd.read_parquet(TRABAJO / f"base_emerging_{l}.parquet", columns=["row_id", "exposure", "new_business", "conjunto"]).assign(line=l)
                  for l in LINEAS])
base = base[base.conjunto == "test"]
q = sub.merge(base, on="row_id", how="left")
arch = {"MLind_final": PRIVADO / "prediccion_2025_mlind.csv", "MLind_C2": PRIVADO / "prediccion_2025_mlind_C2.csv",
        "MLind_C1_tendencia": PRIVADO / "prediccion_2025_mlind_C1_tendencia.csv",
        "noct_A1fixF1b3n_designada": OTROS / "A1fixF1b3n_2025.csv", "noct_A1": OTROS / "A1_2025.csv", "noct_R0": OTROS / "R0_2025.csv",
        "noct_A1fixTc": OTROS / "A1fixTc_2025.csv", "noct_A1fixF1nTc": OTROS / "A1fixF1nTc_2025.csv"}
for k, fpath in arch.items():
    x = pd.read_csv(fpath, dtype={"row_id": str})
    assert (x.row_id.values == sub.row_id.values).all() and x.prediction.notna().all()
    q[k] = x.prediction.values
for k in arch:
    r = {"total": float(q[k].sum())}
    for l in LINEAS:
        i = (q.line == l).values; e = q.exposure.values[i]; nb = q.new_business.values[i]
        r[l] = {"total": float(q[k].values[i].sum()), "tasa": float(q[k].values[i].sum() / e.sum()),
                "tasa_NB": float(q[k].values[i][nb].sum() / e[nb].sum()), "tasa_REN": float(q[k].values[i][~nb].sum() / e[~nb].sum())}
    res["2025"][k] = r
# Distance between the candidate and designated delivery predictions.
a = q.MLind_final.values; b = q.noct_A1fixF1b3n_designada.values
res["2025"]["final_vs_designada"] = {
    "corr_log": float(np.corrcoef(np.log(a), np.log(b))[0, 1]),
    "spearman": float(pd.Series(a).rank().corr(pd.Series(b).rank())),
    "cociente_p01_p50_p99": [float(x) for x in np.quantile(a / b, [0.01, 0.5, 0.99])],
    "por_ramo": {}}
# Mean Bregman divergence relative to expected null deviance per exposure year.
null24 = {}
for l in LINEAS:
    i = (d.line == l).values
    yl = y[i]; ybar = yl.mean()
    null24[l] = float(desviacion(yl, np.full(i.sum(), ybar)).sum() / t.exposure.values[i].sum())
nulo25 = sum(null24[l] * q.exposure.values[(q.line == l).values].sum() for l in LINEAS)
def breg(mt, mo):  # E_y~mt[d(y,mo) - d(y,mt)] = d(mt, mo)
    return desviacion(mt, mo)
res["2025"]["final_vs_designada"]["gap_D2_si_la_verdad_es_designada"] = float(breg(b, a).sum() / nulo25)
res["2025"]["final_vs_designada"]["gap_D2_si_la_verdad_es_final"] = float(breg(a, b).sum() / nulo25)
for l in LINEAS:
    i = (q.line == l).values
    res["2025"]["final_vs_designada"]["por_ramo"][l] = {"corr_log": float(np.corrcoef(np.log(a[i]), np.log(b[i]))[0, 1]),
                                                       "cociente_total": float(a[i].sum() / b[i].sum())}
# Portion of the distance attributable solely to line-level differences.
a_niv = a.copy()
for l in LINEAS:
    i = (q.line == l).values; a_niv[i] = a[i] * b[i].sum() / a[i].sum()
res["2025"]["final_vs_designada"]["gap_D2_misma_forma_nivel_designada"] = float(breg(b, a_niv).sum() / nulo25)
guardar_json(res, RAIZ / "comparacion" / "comparacion_lineas.json")
print(json.dumps({k: v for k, v in res.items() if k != "fuentes"}, indent=1, default=float)[:9000])
