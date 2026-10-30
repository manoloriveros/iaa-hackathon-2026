"""Measure two historical audit sensitivities on the fixed emerging-market recipe.

Compare 2023-only peril-cost completeness weights with the exported 2023-2024
weights, and customer-address connected-component folds with customer-only
folds for DEV T2b. Preserve the registered scope and original audit records.
"""
import hashlib, json
import numpy as np, pandas as pd
from comun import *
from completitud import por_peligro
from evaluar import metricas
import receta

res = {"a_c_fila": {}, "b_agrupacion": {}}
PEL = {"motor": ["bodily_injury", "glass_hail", "own_damage", "theft", "third_party_prop"],
       "buildings": ["accidental_damage", "escape_of_water", "fire", "flood", "storm", "subsidence"],
       "contents": ["accidental_damage", "escape_of_water", "flood", "theft"]}
nuevas = {}
for l in LINEAS:
    b = pd.read_parquet(TRABAJO / f"base_emerging_{l}.parquet")
    tr = b[b.conjunto == "train"]
    comp = {p: por_peligro(l, p, b.period_start, b.period_end) for p in PEL[l]}
    def pesos(mask):
        ult = {p: tr.loc[mask, f"y_{p}"].sum() / np.average(comp[p][(b.conjunto == "train").values][mask.values], weights=tr.exposure[mask]) for p in PEL[l]}
        s = sum(ult.values()); return {p: v / s for p, v in ult.items()}
    w23 = pesos(tr.year == 2023)
    c23 = sum(w23[p] * comp[p] for p in PEL[l])
    c_old = b.c_fila.values
    r = np.where(b.conjunto == "test", 1.0, c23 / c_old)
    res["a_c_fila"][l] = {"pesos_2023": {k: round(v, 4) for k, v in w23.items()},
                          "cambio_relativo_max_2023": float(np.abs(r[(b.year == 2023).values] - 1).max()),
                          "cambio_relativo_max_2024": float(np.abs(r[(b.year == 2024).values] - 1).max()),
                          "cambio_medio_2024": float(np.average(r[(b.year == 2024).values], weights=b.exposure[(b.year == 2024).values]) - 1)}
    nuevas[l] = pd.DataFrame({"row_id": b.row_id, "c_nueva": np.where(b.conjunto == "test", 1.0, c23)})
# Effect on the fixed final model's evaluation metrics.
def con_c(t):
    c = pd.concat(nuevas.values()); t2 = t.merge(c, on="row_id", how="left"); t2["c_fila"] = t2.c_nueva; return t2
t, mu, _ = receta.oof_cruzado("dev", ["T2b"], "sin")
res["a_c_fila"]["DEV_T2b_sin"] = {"exportada": metricas(t, mu)["D2"], "pesos_2023": metricas(con_c(t), mu)["D2"]}
p = receta.parametros("dev", ["T2b"], "ramo")
th, mh = receta.aplicar("hold", p, None)
res["a_c_fila"]["HOLD_T2b_C1"] = {"exportada": metricas(th, mh)["D2"], "pesos_2023_solo_en_evaluacion": metricas(con_c(th), mh)["D2"]}
# Customer-address connected components in emerging-market 2023.
filas = []
for l in LINEAS:
    b = pd.read_parquet(TRABAJO / f"base_emerging_{l}.parquet", columns=["row_id", "customer_id", "address_id", "year", "conjunto", "fold"])
    filas.append(b[(b.conjunto == "train") & (b.year == 2023)].assign(line=l))
e = pd.concat(filas, ignore_index=True)
padre = {}
def f(x):
    while padre.setdefault(x, x) != x:
        padre[x] = padre[padre[x]]; x = padre[x]
    return x
for c, a in zip("C" + e.customer_id, "A" + e.address_id):
    rc, ra = f(c), f(a)
    if rc != ra: padre[ra] = rc
comp_id = np.array([f("C" + c) for c in e.customer_id])
e["fold_ca"] = [int(hashlib.sha256(("mlind_ca|" + x).encode()).hexdigest()[:16], 16) % 5 for x in comp_id]
cruce = e.groupby("address_id").fold.nunique()
res["b_agrupacion"]["direcciones_en_mas_de_un_pliegue_por_cliente"] = int((cruce > 1).sum())
res["b_agrupacion"]["componentes"] = int(len(set(comp_id)))
# Recompute T2b's line-level emerging calibration k2 under the alternate folds.
raw = pd.concat([pd.read_parquet(TRABAJO / "pred" / "dev" / f"T2braw_{l}.parquet") for l in LINEAS])
bb = pd.concat([pd.read_parquet(TRABAJO / f"base_emerging_{l}.parquet", columns=["row_id", "exposure", "c_fila", "y"]) for l in LINEAS])
e = e.merge(raw, on="row_id").merge(bb, on="row_id")
mu = np.zeros(len(e))
for k in range(5):
    for l in LINEAS:
        a = ((e.fold_ca != k) & (e.line == l)).values; bm = ((e.fold_ca == k) & (e.line == l)).values
        k2 = factor_tweedie(e.y.values[a], np.exp(e.raw.values[a]) * e.exposure.values[a] * e.c_fila.values[a])
        mu[bm] = k2 * np.exp(e.raw.values[bm]) * e.exposure.values[bm]
tt = receta.tabla("dev")
mu_al = tt[["row_id"]].merge(pd.DataFrame({"row_id": e.row_id, "mu": mu}), on="row_id").mu.values
res["b_agrupacion"]["DEV_T2b_sin"] = {"pliegues_cliente": metricas(t, receta.componentes("dev", ["T2b"], t)["T2b"])["D2"],
                                       "pliegues_cliente_direccion": metricas(tt, mu_al)["D2"]}
guardar_json(res, ENTREGA / "respuesta_audit_checks.json")
print(json.dumps(res, indent=1, default=float))
