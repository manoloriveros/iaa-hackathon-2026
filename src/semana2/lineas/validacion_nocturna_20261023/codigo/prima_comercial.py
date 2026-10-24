"""Prima comercial de las 20 pólizas de referencia a partir de la prima de riesgo (A1 y R0).

P = [R·(1 + r) + F·e] / (1 − v − c − t − m), con r = 0,12 en hogar (cat_reinsurance, "share of property risk premium"),
F = 85 CU por póliza y año repartido por exposición (decisión GASTO-F-01 del participante), v = 0,15, t = 0,08, m = 0,08,
c = 0 directo y 0,20 broker. Cada componente se recalcula y se comprueba que suman P.
Sensibilidad: F = 85 por póliza y año repartido entre las filas 2025 de la misma póliza (proporcional a exposición):
una póliza corta paga el gasto fijo entero una vez, y una póliza partida en tramos no lo paga dos veces (corrección rev3).
"""
import json, pathlib
import numpy as np, pandas as pd

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/produccion'
ex = pd.read_parquet(R / 'datos/s2/expenses.parquet').set_index('item').emerging
ref = pd.read_parquet(R / 'datos/s2/reference_policies.parquet')
tests = pd.concat([pd.read_parquet(R / f'datos/s2/test_{l}.parquet')[['row_id', 'policy_id', 'exposure']] for l in ('motor', 'buildings', 'contents')])
pol_exp = tests.groupby('policy_id').exposure.sum(); pol_rows = tests.groupby('policy_id').row_id.apply(list)
preds = {k: pd.read_csv(O / f'{k}_2025.csv', dtype={'row_id': str}).set_index('row_id').prediction for k in ('A1', 'R0')}
v, t, m, F = ex['variable_expense'], ex['premium_tax'], ex['target_profit_margin'], ex['fixed_expense_per_policy']
rows = []
for _, p in ref.iterrows():
    c = {'direct': ex['commission_direct'], 'broker': ex['commission_broker']}.get(p.channel, np.nan)
    r = ex['cat_reinsurance'] if p.line in ('buildings', 'contents') else 0.0
    den = 1 - v - c - t - m
    for k, s in preds.items():
        Rk = float(s[p.row_id]); fixed = F * p.exposure
        P = (Rk * (1 + r) + fixed) / den
        comp = {'riesgo': Rk, 'reaseguro_cat': Rk * r, 'gasto_fijo': fixed, 'gasto_variable': v * P, 'comision': c * P,
                'impuesto': t * P, 'margen': m * P}
        assert abs(sum(comp.values()) - P) < 1e-6
        F_pol = F * p.exposure / pol_exp[p.policy_id]
        P_sens = (Rk * (1 + r) + F_pol) / den
        rows.append({'modelo': k, 'row_id': p.row_id, 'ramo': p.line, 'canal': p.channel, 'nuevo_negocio': bool(p.new_business),
                     'exposicion': p.exposure, **{x: round(y, 2) for x, y in comp.items()}, 'prima_comercial': round(P, 2),
                     'denominador': round(den, 2), 'prima_anualizada': round(P / p.exposure, 2), 'prima_escrita': p.written_premium,
                     'razon_anualizada_escrita': round(P / p.exposure / p.written_premium, 3),
                     'filas_2025_de_la_poliza': ','.join(pol_rows[p.policy_id]), 'exposicion_poliza_2025': round(pol_exp[p.policy_id], 4),
                     'sens_F_por_poliza': round(P_sens, 2)})
T = pd.DataFrame(rows)
T.to_csv(O / 'prima_comercial_referencias.csv', index=False)
s = T.groupby(['modelo', 'ramo']).apply(lambda x: pd.Series({'riesgo': x.riesgo.sum(), 'prima': x.prima_comercial.sum(),
                                                               'razon_mediana_anualizada_escrita': x.razon_anualizada_escrita.median()}), include_groups=False)
print(T[T.modelo == 'A1'][['row_id', 'ramo', 'canal', 'exposicion', 'riesgo', 'reaseguro_cat', 'gasto_fijo', 'gasto_variable', 'comision', 'impuesto', 'margen', 'prima_comercial', 'prima_anualizada', 'prima_escrita', 'razon_anualizada_escrita', 'exposicion_poliza_2025', 'sens_F_por_poliza']].to_string())
print(s.round(3).to_string())
