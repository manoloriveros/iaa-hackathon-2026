"""Evaluación de la receta A1 corregida (ID01) y de dos estabilizaciones: promedio de tres semillas e historia F1.

Desarrollo 2023 (OOF, folds propios) y 2024 exploratorio (ya abierto; no confirmatorio). Producción 2025 de cada variante.
"""
import json, pathlib, sys, hashlib
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M

R = pathlib.Path('/home/claude/noche'); T = R / 'salidas/transfer'; C = R / 'salidas/conf'; O = R / 'salidas/correccion'; O.mkdir(exist_ok=True)
LINES = ['motor', 'buildings', 'contents']
SRC = {  # etiqueta -> {ramo: [sufijos de lg a promediar]} ; 'full' (2021-2024) y 'conf' (2021-2023)
    'A1fix': {'full': {'motor': ['dev21222324_v2fixs11'], 'buildings': ['dev21222324_m02'], 'contents': ['dev21222324_m02']},
              'conf': {'motor': ['dev212223_v2fixconfs11'], 'buildings': ['dev212223_v2conf'], 'contents': ['dev212223_v2conf']}},
    'A1fixb3': {'full': {'motor': ['dev21222324_v2fixs11', 'dev21222324_v2fixs12', 'dev21222324_v2fixs13'],
                         'buildings': ['dev21222324_m02', 'dev21222324_v2s12', 'dev21222324_v2s13'],
                         'contents': ['dev21222324_m02', 'dev21222324_v2s12', 'dev21222324_v2s13']},
                'conf': {'motor': ['dev212223_v2fixconfs11', 'dev212223_v2fixconfs12', 'dev212223_v2fixconfs13'],
                         'buildings': ['dev212223_v2conf', 'dev212223_v2confs12', 'dev212223_v2confs13'],
                         'contents': ['dev212223_v2conf', 'dev212223_v2confs12', 'dev212223_v2confs13']}},
    'A1fixF1': {'full': {'motor': ['dev21222324_v2fixf1'], 'buildings': ['dev21222324_v2f1'], 'contents': ['dev21222324_v2f1']},
                'conf': {'motor': ['dev212223_v2fixf1conf'], 'buildings': ['dev212223_v2f1conf'], 'contents': ['dev212223_v2f1conf']}},
}


def lg(tags, line):
    return pd.concat([pd.read_parquet(T / f'lg_{t}_{line}_em.parquet').set_index('row_id').lg_dev for t in tags], axis=1).mean(axis=1)


res = {}
# 1. compuestos para la escalera de desarrollo (usa salidas/transfer/lg_{tag}_{ramo}_em.parquet)
for k, v in SRC.items():
    for line in LINES:
        lg(v['full'][line], line).rename('lg_dev').reset_index().to_parquet(T / f'lg_{k}_{line}_em.parquet', index=False)
# 2. 2024 exploratorio
P = pd.read_parquet(C / 'predicciones/predicciones_2024.parquet').set_index('row_id')
lab = pd.concat([pd.read_parquet(C / f'base_s2_{l}.parquet').query('year==2024')[['row_id', 't0']] for l in LINES]).set_index('row_id').loc[P.index]
y = lab.t0.values
for k, v in SRC.items():
    col = np.zeros(len(P))
    for line in LINES:
        b = pd.read_parquet(C / f'base_s2_{line}.parquet'); g = np.exp(b.row_id.map(lg(v['conf'][line], line)).values)
        f = (b.year == 2023).values; w = (b.year == 2024).values
        L = b.t0.values[f].sum() / (b.eef_coste.values[f] * g[f]).sum()
        pr = pd.Series(b.eef_coste.values[w] * g[w] * L, index=b.row_id.values[w])
        m = (P.line == line).values; col[m] = pr.loc[P.index[m]].values
    P[k] = col
comp = M.components(P.customer_id.values, P.address_id.values)
names = ['R0', 'A1', 'A1fix', 'A1fixb3', 'A1fixF1']
bs = M.boot_d2_diff(y, {n: P[n].values for n in names}, comp, n=4000)
res['exploratorio_2024'] = {n: {'D2': round(M.d2(y, P[n].values), 5), 'menos_A1': round(M.d2(y, P[n].values) - M.d2(y, P['A1'].values), 5),
                                'IC90_menos_A1': [round(float(np.quantile(bs[n] - bs['A1'], q)), 5) for q in (0.05, 0.95)],
                                **{f'D2_{l}': round(M.d2(y[P.line.values == l], P[n].values[P.line.values == l]), 5) for l in LINES}} for n in names}
# 3. producción 2025
ss = pd.read_parquet(R / 'datos/s2/sample_submission.parquet')
prod = {}
for k, v in SRC.items():
    parts = []
    for line in LINES:
        b = pd.read_parquet(R / f'salidas/s2/base_{line}.parquet'); g = np.exp(b.row_id.map(lg(v['full'][line], line)).values)
        tr = (b.split == 'train').values; te = (b.split == 'test').values
        L = b.t0.values[tr].sum() / (b.eef_coste.values[tr] * g[tr]).sum()
        parts.append(pd.DataFrame({'row_id': b.row_id.values[te], 'prediction': b.exposure_model.values[te] * g[te] * L}))
    df = pd.concat(parts).set_index('row_id').loc[ss.row_id].reset_index()
    assert len(df) == 209063 and (df.row_id.values == ss.row_id.values).all() and (df.prediction > 0).all() and np.isfinite(df.prediction).all()
    p = O / f'{k}_2025.csv'; df.to_csv(p, index=False, float_format='%.6f', lineterminator='\n')
    prod[k] = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'total': round(df.prediction.sum(), 2),
               'por_ramo': df.groupby(df.row_id.str[0]).prediction.sum().round(2).to_dict()}
res['produccion'] = prod
json.dump(res, open(O / 'evaluacion_correccion.json', 'w'), indent=1)
print(json.dumps(res, indent=1))
