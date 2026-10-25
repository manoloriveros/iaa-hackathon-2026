"""Prima comercial de las 20 pólizas de referencia a partir de la prima de riesgo predicha (producción 2025).

P = [R (1 + cat) + F e] / (1 - gasto variable - comisión del canal - impuesto - margen),
cat = 0,12 solo en hogar (porcentaje de la prima de riesgo de propiedad), F = 85 CU por póliza y año repartido por exposición.
Sensibilidad: F entero por fila.
"""
import json
import numpy as np, pandas as pd
from comun import *

ex = pd.read_parquet(DATOS / "emerging" / "expenses.parquet").set_index("item").emerging
ref = pd.read_parquet(DATOS / "emerging" / "reference_policies.parquet")
pred = pd.read_csv(ENTREGA / "prediccion_2025_mlind.csv", dtype={"row_id": str})
d = ref.merge(pred, on="row_id", how="left")
bal = json.load(open(ENTREGA / "produccion_2025.json"))["balance_oof_pcv"]
assert d.prediction.notna().all()
com = {"direct": ex["commission_direct"], "broker": ex["commission_broker"], "comparison_site": ex["commission_comparison_site"]}
filas = []
for _, r in d.iterrows():
    R0 = r.prediction; e = r.exposure
    R = R0 * bal[r.line]  # prima de riesgo a nivel de balance (media), no al factor que minimiza la desviación
    cat = ex["cat_reinsurance"] * R if r.line in ("buildings", "contents") else 0.0
    c = com[r.channel]
    den = 1 - ex["variable_expense"] - c - ex["premium_tax"] - ex["target_profit_margin"]
    F = ex["fixed_expense_per_policy"] * e
    P = (R + cat + F) / den
    P_alt = (R + cat + ex["fixed_expense_per_policy"]) / den
    filas.append({"row_id": r.row_id, "ramo": r.line, "canal": r.channel, "exposicion": e, "nuevo_negocio": bool(r.new_business),
                  "prediccion_kaggle": R0, "factor_balance": bal[r.line], "prima_riesgo": R, "reaseguro_cat": cat, "gasto_fijo": F, "carga_neta": R + cat + F, "denominador": den,
                  "gasto_variable": P * ex["variable_expense"], "comision": P * c, "impuesto": P * ex["premium_tax"],
                  "margen": P * ex["target_profit_margin"], "prima_comercial": P, "prima_comercial_F_entero": P_alt,
                  "prima_escrita": r.written_premium, "razon_comercial_escrita": P / r.written_premium})
out = pd.DataFrame(filas)
out.round(2).to_csv(ENTREGA / "prima_comercial_20.csv", index=False)
print(out[["row_id", "ramo", "canal", "exposicion", "prima_riesgo", "prima_comercial", "prima_escrita", "razon_comercial_escrita"]].round(2).to_string())
