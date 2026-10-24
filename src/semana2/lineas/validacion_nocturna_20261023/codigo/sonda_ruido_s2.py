"""Diseño de una posible sonda de nivel para la semana 2: ruido del óptimo de nivel por ramo en un subconjunto público del 33 %
medido contra el 67 % restante (lección de D103), usando 2024 (ya abierto) como sustituto de 2025 con las predicciones A1.
Exploratorio: no es una decisión ni un envío. Salida: salidas/conf/sonda_ruido_s2.json
"""
import json, pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M
R = pathlib.Path('/home/claude/noche'); C = R / 'salidas/conf'
P = pd.read_parquet(C / 'predicciones/predicciones_2024.parquet').set_index('row_id')
lab = pd.concat([pd.read_parquet(C / f'base_s2_{l}.parquet').query('year==2024')[['row_id', 't0']] for l in ['motor', 'buildings', 'contents']]).set_index('row_id').loc[P.index]
y = lab.t0.values; mu = P.A1.values; line = P.line.values
rng = np.random.default_rng(7); out = {}
for l in ['motor', 'buildings', 'contents']:
    m = line == l; yl, ml = y[m], mu[m]
    c_all = (yl / np.sqrt(ml)).sum() / np.sqrt(ml).sum()
    pub, prv, gain_pub, gain_prv = [], [], [], []
    for _ in range(400):
        s = rng.random(m.sum()) < 0.33
        cp = (yl[s] / np.sqrt(ml[s])).sum() / np.sqrt(ml[s]).sum()
        cv = (yl[~s] / np.sqrt(ml[~s])).sum() / np.sqrt(ml[~s]).sum()
        pub.append(cp); prv.append(cv)
    pub, prv = np.log(pub), np.log(prv)
    out[l] = {'c_optimo_2024_todo': round(float(c_all), 4), 'sd_log_c_publico': round(float(pub.std()), 4),
              'sd_log_c_privado': round(float(prv.std()), 4), 'sd_log_diferencia_pub_priv': round(float((pub - prv).std()), 4),
              'corr_pub_priv': round(float(np.corrcoef(pub, prv)[0, 1]), 3)}
json.dump(out, open(C / 'sonda_ruido_s2.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
