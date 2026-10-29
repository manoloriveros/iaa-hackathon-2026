"""Prima comercial de las 20 pólizas de referencia de la parte 2 (página 5 del informe final).

Entradas: reference_policies.parquet y expenses.parquet (datos oficiales del emergente) y la entrega F3c
(F3c_2025.csv, prima de riesgo por fila). Salida: prima_comercial_F3c_20ref.csv, el archivo citado en la página 5.

Fórmula: P = (R + 0,12·R_hogar + 85) / (1 − 0,15 − c − 0,08 − 0,08), con c = 0,20 con corredor y 0 en venta directa.
El gasto fijo (85 CU por póliza en expenses.parquet) se cobra completo en cada póliza por decisión de Manuel Rodríguez
(26 de octubre); la columna P_prorrateo conserva la alternativa anterior, 85·e repartidos por exposición. El reaseguro
catastrófico (12 %) solo aplica a edificios y contenidos. La anualización usa la exposición exacta de reference_policies.

Uso: python prima_comercial_20ref.py <carpeta_datos_emergente> <F3c_2025.csv> [salida.csv]
"""
import sys
import pandas as pd

datos = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/ml2/datos/emerging"
f3c = sys.argv[2] if len(sys.argv) > 2 else "/home/claude/m017/exp26/F3c_2025.csv"
salida = sys.argv[3] if len(sys.argv) > 3 else "prima_comercial_F3c_20ref.csv"

ref = pd.read_parquet(f"{datos}/reference_policies.parquet")[
    ["row_id", "line", "channel", "new_business", "exposure", "written_premium"]]
exp = pd.read_parquet(f"{datos}/expenses.parquet").set_index("item")["emerging"]
pred = pd.read_csv(f3c, dtype={"row_id": str}).set_index("row_id")["prediction"]

fijo_pol = float(exp["fixed_expense_per_policy"])          # 85 CU por póliza
variable = float(exp["variable_expense"])                  # 0,15
impuesto = float(exp["premium_tax"])                       # 0,08
margen = float(exp["target_profit_margin"])                # 0,08
cat = float(exp["cat_reinsurance"])                        # 0,12 de la prima de riesgo de hogar
comision = {"broker": float(exp["commission_broker"]), "direct": float(exp["commission_direct"])}

d = ref.copy()
d["R"] = pred.reindex(d.row_id).values
d["cat"] = d.R * cat * d.line.isin(["buildings", "contents"])
d["fijo"] = fijo_pol
d["den"] = 1 - variable - d.channel.map(comision) - impuesto - margen
d["P"] = ((d.R + d["cat"] + d.fijo) / d.den).round(2)
d["P_prorrateo"] = ((d.R + d["cat"] + fijo_pol * d.exposure) / d.den).round(2)
d["P_anual_vs_wp"] = d.P / d.exposure / d.written_premium   # prima comercial anualizada con la exposición exacta / prima escrita
cols = ["row_id", "line", "channel", "new_business", "exposure", "R", "cat", "fijo", "den", "P", "P_prorrateo", "written_premium", "P_anual_vs_wp"]
out = d[cols].copy()
out["exposure"] = out.exposure.round(4)
for c in ["R", "cat", "fijo", "den", "P", "P_prorrateo", "written_premium", "P_anual_vs_wp"]:
    out[c] = out[c].round(2)
out.to_csv(salida, index=False)
print(f"{len(out)} pólizas; suma P = {out.P.sum():,.2f} CU (prorrateo: {out.P_prorrateo.sum():,.2f}); prima escrita = {out.written_premium.sum():,.2f}; "
      f"cociente anualizado = {(d.P / d.exposure).sum() / d.written_premium.sum():.3f}")
