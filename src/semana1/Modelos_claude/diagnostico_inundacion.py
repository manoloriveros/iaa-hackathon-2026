"""Diagnóstico de inundación en edificios para el foro (CLA-20261018-003).

Frecuencia, severidad y peso del coste de inundación por zona y por sótano en 2021-2024 (matriz F0 de Claude), y real
sobre esperado del total de edificios de S15_claude_propio por zona en V23 selección y V24. Descriptivo: agrega años,
incluye 2024 inmaduro y la severidad de los abiertos lleva reserva de caso.
Uso: python3 diagnostico_inundacion.py  (lee /home/claude/work, imprime tablas)
"""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/modelos_claude")
from comun import WORK
from mezcla3 import labels
from robustez import blend, parse
line = "buildings"
df = pd.read_parquet(WORK / "feat_buildings.parquet", columns=["row_id", "year", "flood_zone", "basement", "exposure", "e_ef_flood", "n_flood", "y_flood", "T0", "e_ef_coste"])
df["row_id"] = df.row_id.astype(str)
tr = df[df.year <= 2024]
g = tr.groupby(["flood_zone"]).agg(expo=("exposure", "sum"), e_ef=("e_ef_flood", "sum"), n=("n_flood", "sum"), coste=("y_flood", "sum"), coste_total=("T0", "sum"))
g["frecuencia"] = g.n / g.e_ef; g["severidad"] = g.coste / g.n; g["cuota_inundacion_en_coste"] = g.coste / g.coste_total; g["peso_expo"] = g.expo / g.expo.sum()
print("2021-2024 por zona de inundación"); print(g.round(4).to_string())
gb = tr.groupby(["flood_zone", "basement"]).agg(e_ef=("e_ef_flood", "sum"), n=("n_flood", "sum"), coste=("y_flood", "sum"))
gb["frecuencia"] = gb.n / gb.e_ef; gb["severidad"] = gb.coste / gb.n.clip(lower=1)
print("zona x sótano"); print(gb.round(4).to_string())
# A/E del total de edificios de la mezcla propia por zona, en V23 selección y V24 (factor de V23)
name, spec, forma = parse("S15p=/home/claude/work/spec_s15_propio.json@motor:1.09:0.95,buildings:1.08:1.14,contents:1.07:1")
ysel, y24, idx25 = labels(line)
fe = df.set_index("row_id")
expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
res, bsel, b24, _ = blend(spec, forma, line, ysel, y24, idx25, expos)
for fold, y, mu, idx in (("V23 sel", ysel.values, bsel * res["f23"], ysel.index), ("V24", y24.values, b24, y24.index)):
    z = fe.flood_zone.reindex(idx).values; bsm = fe.basement.reindex(idx).values; yf = fe.y_flood.reindex(idx).fillna(0).values
    t = pd.DataFrame({"z": z, "b": bsm, "y": y, "mu": mu, "yf": yf})
    a = t.groupby("z").agg(real=("y", "sum"), esperado=("mu", "sum"), inundacion=("yf", "sum"), filas=("y", "size"))
    a["real_sobre_esperado"] = a.real / a.esperado; a["cuota_inundacion"] = a.inundacion / a.real
    print(fold, "real/esperado del total de edificios por zona (S15_claude_propio)"); print(a.round(3).to_string())
