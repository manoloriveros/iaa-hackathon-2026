"""Conciliación con la línea ML independiente de Claude (T2b), hecha al final y antes del envío.

Compara mis predicciones con las de T2b (Repositorio_IAA2026/privado/semana2/claude_ml_independiente_20261023/,
oof_dev_hold_pcv_mlind.tar.gz, sin modificar) en las mismas filas, con mi métrica y mi bootstrap de componentes:
  DEV 2023 (OOF): mi A1fixF1b3_nivel frente a su T2b, y la media de las dos.
  2024 (exploratorio, ya abierto): mi receta final con nivel 2023 y calibración neutral (evaluar_final.py) frente a su
  T2b HOLD, y la media.
Lee las predicciones tal como las guardó cada línea (escala observada con su vínculo de observación). Si su escala no
cuadra con el T0 observado, se informa el A/E en vez de suponer nada. Escribe salidas/conciliacion_mlind.json.
"""
import hashlib, io, contextlib, json, pathlib, runpy, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M

R = pathlib.Path('/home/claude/noche'); ML = R / 'datos/mlind/oof/pred'
LINES = ['motor', 'buildings', 'contents']
theirs = lambda part: pd.concat([pd.read_parquet(ML / part / f'T2b_{l}.parquet') for l in LINES]).set_index('row_id').mu
out = {}
# DEV 2023
o = pd.read_parquet(R / 'salidas/s2/oof/A1fixF1b3_nivel.parquet').set_index('row_id')
y = o.y.values; th = theirs('dev').loc[o.index].values; mi = o.mu.values
comp = M.components(o.customer_id.values, o.address_id.values)
P = {'mio_A1fixF1b3': mi, 'T2b': th, 'media': (mi + th) / 2}
bs = M.boot_d2_diff(y, P, comp, n=4000)
out['dev2023'] = {k: {'D2': round(float(M.d2(y, v)), 6), 'AE': round(float(y.sum() / v.sum()), 4),
                      'menos_mio': round(float(M.d2(y, v) - M.d2(y, mi)), 6), 'IC90': [round(float(np.quantile(bs[k] - bs['mio_A1fixF1b3'], q)), 6) for q in (0.05, 0.95)]} for k, v in P.items()}
out['dev2023']['corr_log'] = round(float(np.corrcoef(np.log(mi), np.log(th))[0, 1]), 4)
# 2024
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(R / 'codigo/evaluar_final.py'))
PP, y4 = g['P'], g['y']
mi4 = PP['A1fixF1b3n'].values; th4 = theirs('hold').loc[PP.index].values
comp4 = M.components(PP.customer_id.values, PP.address_id.values)
P4 = {'mio_A1fixF1b3n': mi4, 'T2b_hold': th4, 'media': (mi4 + th4) / 2, 'A1_acta': PP['A1'].values}
bs4 = M.boot_d2_diff(y4, P4, comp4, n=4000)
ln = PP.line.values
out['hold2024'] = {k: {'D2': round(float(M.d2(y4, v)), 6), 'AE': {l: round(float(y4[ln == l].sum() / v[ln == l].sum()), 4) for l in LINES},
                       'D2_ramo': {l: round(float(M.d2(y4[ln == l], v[ln == l])), 5) for l in LINES},
                       'menos_mio': round(float(M.d2(y4, v) - M.d2(y4, mi4)), 6), 'IC90': [round(float(np.quantile(bs4[k] - bs4['mio_A1fixF1b3n'], q)), 6) for q in (0.05, 0.95)]} for k, v in P4.items()}
out['hold2024']['corr_log'] = round(float(np.corrcoef(np.log(mi4), np.log(th4))[0, 1]), 4)
# 2025
rd = lambda p: pd.read_csv(p, dtype={'row_id': str}).set_index('row_id').prediction
m25 = rd(R / 'salidas/correccion/A1fixF1b3n_2025.csv'); t25 = rd(R / 'datos/mlind/prediccion_2025_mlind.csv').loc[m25.index]
pre = m25.index.str[0]
out['produccion_2025'] = {'sha_mlind': hashlib.sha256((R / 'datos/mlind/prediccion_2025_mlind.csv').read_bytes()).hexdigest(),
                          'total_mio': round(float(m25.sum()), 2), 'total_mlind': round(float(t25.sum()), 2),
                          'por_ramo_mlind_sobre_mio': {k: round(float(t25[pre == k].sum() / m25[pre == k].sum()), 4) for k in 'MBC'},
                          'corr_log_por_ramo': {k: round(float(np.corrcoef(np.log(m25[pre == k]), np.log(t25[pre == k]))[0, 1]), 4) for k in 'MBC'}}
# Comparación de orden, sin efecto de escala: su predicción se reescala por ramo al total de la mía (no usa siniestros)
def neutral(ref, other, lines):
    o2 = other.copy()
    for l in LINES:
        k = lines == l; o2[k] = other[k] * ref[k].sum() / other[k].sum()
    return o2
lnd = o.line.values
thn = neutral(mi, th, lnd); P = {'mio_A1fixF1b3': mi, 'T2b_neutral': thn, 'media_neutral': (mi + thn) / 2}
bs = M.boot_d2_diff(y, P, comp, n=4000); kc = y < np.quantile(y, 0.999)
out['dev2023_orden'] = {k: {'D2': round(float(M.d2(y, v)), 6), 'menos_mio': round(float(M.d2(y, v) - M.d2(y, mi)), 6),
                            'IC90': [round(float(np.quantile(bs[k] - bs['mio_A1fixF1b3'], q)), 6) for q in (0.05, 0.95)],
                            'cuerpo_menos_mio': round(float(M.d2(y[kc], v[kc]) - M.d2(y[kc], mi[kc])), 6)} for k, v in P.items()}
th4n = neutral(mi4, th4, ln); P4 = {'mio_A1fixF1b3n': mi4, 'T2b_neutral': th4n, 'media_neutral': (mi4 + th4n) / 2}
bs4 = M.boot_d2_diff(y4, P4, comp4, n=4000); kc4 = y4 < np.quantile(y4, 0.999)
out['hold2024_orden'] = {k: {'D2': round(float(M.d2(y4, v)), 6), 'menos_mio': round(float(M.d2(y4, v) - M.d2(y4, mi4)), 6),
                             'IC90': [round(float(np.quantile(bs4[k] - bs4['mio_A1fixF1b3n'], q)), 6) for q in (0.05, 0.95)],
                             'cuerpo_menos_mio': round(float(M.d2(y4[kc4], v[kc4]) - M.d2(y4[kc4], mi4[kc4])), 6),
                             'D2_ramo': {l: round(float(M.d2(y4[ln == l], v[ln == l])), 5) for l in LINES}} for k, v in P4.items()}
out['nota_escala'] = 'Las predicciones guardadas de T2b HOLD no están en la escala del T0 observado de 2024 (A/E de autos 0,81, que coincide con su completitud de 2024 de 0,80), así que la comparación justa es la de orden, con el total por ramo igualado al mío.'
json.dump(out, open(R / 'salidas/conciliacion_mlind.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
