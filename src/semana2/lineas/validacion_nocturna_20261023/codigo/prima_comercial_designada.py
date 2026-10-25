"""Prima comercial de las 20 referencias con la producción designada por el participante (A1fixF1b3n, política v2).

Misma fórmula y mismos supuestos que codigo/prima_comercial.py; solo cambia la prima de riesgo. Escribe
salidas/correccion/prima_comercial_designada.csv. No toca las salidas de A1 y R0.
"""
import json, pathlib
import numpy as np, pandas as pd

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/correccion'
ex = pd.read_parquet(R / 'datos/s2/expenses.parquet').set_index('item').emerging
ref = pd.read_parquet(R / 'datos/s2/reference_policies.parquet')
tests = pd.concat([pd.read_parquet(R / f'datos/s2/test_{l}.parquet')[['row_id', 'policy_id', 'exposure']] for l in ('motor', 'buildings', 'contents')])
pol_exp = tests.groupby('policy_id').exposure.sum(); pol_rows = tests.groupby('policy_id').row_id.apply(list)
preds = {'A1fixF1b3n': pd.read_csv(O / 'A1fixF1b3n_2025.csv', dtype={'row_id': str}).set_index('row_id').prediction}
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
T.to_csv(O / 'prima_comercial_designada.csv', index=False)
a1 = pd.read_csv(R / 'salidas/produccion/prima_comercial_referencias.csv', dtype={'row_id': str}).query("modelo == 'A1'").set_index('row_id')
T = T.set_index('row_id'); T['razon_frente_A1'] = (T.prima_comercial / a1.loc[T.index, 'prima_comercial']).round(3)
print(T[['ramo', 'canal', 'exposicion', 'riesgo', 'prima_comercial', 'razon_frente_A1', 'sens_F_por_poliza']].to_string())
print('suma', round(T.prima_comercial.sum(), 2), 'suma A1', round(a1.loc[T.index, 'prima_comercial'].sum(), 2))
