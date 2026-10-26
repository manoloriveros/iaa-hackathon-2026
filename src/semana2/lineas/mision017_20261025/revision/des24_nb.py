import numpy as np, pandas as pd, lightgbm as lgb, json
from comun import *
from variables import *
def dev(y, m): return 4 * y / np.sqrt(m) + 4 * np.sqrt(m) - 8 * np.sqrt(y)
def kopt(y, m): return np.sum(y / np.sqrt(m)) / np.sum(np.sqrt(m))
out = {}
for linea in ["motor", "buildings", "contents"]:
    em = cargar("emerging", linea, "hasta2023"); dv = cargar("developed", linea, "hasta2023")
    cols = comunes(linea); cats = categorias_union([dv, em], cols + SOLO_EMERGENTE + MARKETING + TARIFA + MAKE)
    d = dv[dv.year == 2024].reset_index(drop=True)
    b2 = lgb.Booster(model_file=str(TRABAJO / "modelos/dev" / f"T2b_{linea}.txt")); r = b2.predict(matriz(d, cols, cats), raw_score=True)
    o = {}
    for et, msk in (("NB", d.new_business.values.astype(bool)), ("NB_anio_completo", d.new_business.values.astype(bool) & (d.exposure.values >= 0.9)), ("REN", ~d.new_business.values.astype(bool))):
        y = d.y.values[msk]; e = d.exposure.values[msk] * d.c_fila.values[msk]; null = dev(y, np.full(len(y), y.mean())).sum()
        m0 = e * kopt(y, e); m = np.exp(r[msk]) * e; m *= kopt(y, m)
        o[et] = {"n": int(msk.sum()), "pos": int((y > 0).sum()), "habilidad_T2b": round(float((dev(y, m0).sum() - dev(y, m).sum()) / null), 4)}
    out[linea] = o; print(linea, o, flush=True)
json.dump(out, open(RAIZ / "nb" / "des24_nb.json", "w"), indent=1)
