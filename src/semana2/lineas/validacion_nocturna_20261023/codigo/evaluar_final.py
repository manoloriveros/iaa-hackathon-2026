"""Receta final de la política v2 (S2-SELECCION-v2-20261024): A1 con ID01, historia neutral y tres semillas, sin tendencia.

1. Compuestos de relatividades A1fixF1b3 (media de los log de las semillas 11, 12 y 13 del GBM desarrollado con historia),
   completo (2021-2024) y conf (2021-2023).
2. 2024 exploratorio (ya abierto): A1fixb3 con nivel 2023 y A1fixF1b3n = A1fixF1b3 reescalado por ramo al total 2024 de
   A1fixb3 (calibración neutral, sin mirar siniestros de 2024). Pares frente a A1 del acta y frente a A1fixb3.
3. Producción 2025: A1fixF1b3n = A1fixF1b3 (nivel 2023-2024 por balance) reescalado por ramo al total de A1fixb3_2025.csv.
   Sin tendencia, por decisión del participante. Sin enviar.
Escribe salidas/correccion/evaluacion_final.json y salidas/correccion/A1fixF1b3n_2025.csv.
"""
import hashlib, json, pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M

R = pathlib.Path('/home/claude/noche'); T = R / 'salidas/transfer'; C = R / 'salidas/conf'; O = R / 'salidas/correccion'
LINES = ['motor', 'buildings', 'contents']; PFX = {'motor': 'M', 'buildings': 'B', 'contents': 'C'}
SRC = {'A1fixb3': {'full': {'motor': ['dev21222324_v2fixs11', 'dev21222324_v2fixs12', 'dev21222324_v2fixs13'],
                            'buildings': ['dev21222324_m02', 'dev21222324_v2s12', 'dev21222324_v2s13'],
                            'contents': ['dev21222324_m02', 'dev21222324_v2s12', 'dev21222324_v2s13']},
                   'conf': {'motor': ['dev212223_v2fixconfs11', 'dev212223_v2fixconfs12', 'dev212223_v2fixconfs13'],
                            'buildings': ['dev212223_v2conf', 'dev212223_v2confs12', 'dev212223_v2confs13'],
                            'contents': ['dev212223_v2conf', 'dev212223_v2confs12', 'dev212223_v2confs13']}},
       'A1fixF1b3': {'full': {'motor': ['dev21222324_v2fixf1', 'dev21222324_v2fixf1s12', 'dev21222324_v2fixf1s13'],
                              'buildings': ['dev21222324_v2f1', 'dev21222324_v2f1s12', 'dev21222324_v2f1s13'],
                              'contents': ['dev21222324_v2f1', 'dev21222324_v2f1s12', 'dev21222324_v2f1s13']},
                     'conf': {'motor': ['dev212223_v2fixf1conf', 'dev212223_v2fixf1confs12', 'dev212223_v2fixf1confs13'],
                              'buildings': ['dev212223_v2f1conf', 'dev212223_v2f1confs12', 'dev212223_v2f1confs13'],
                              'contents': ['dev212223_v2f1conf', 'dev212223_v2f1confs12', 'dev212223_v2f1confs13']}}}


def lg(tags, line):
    return pd.concat([pd.read_parquet(T / f'lg_{t}_{line}_em.parquet').set_index('row_id').lg_dev for t in tags], axis=1).mean(axis=1)


out = {'politica': 'S2-SELECCION-v2-20261024', 'receta': 'A1fixF1b3n', 'tendencia': 'ninguna (decisión del participante)'}
# 1. compuesto para la escalera de desarrollo
for line in LINES:
    lg(SRC['A1fixF1b3']['full'][line], line).rename('lg_dev').reset_index().to_parquet(T / f'lg_A1fixF1b3_{line}_em.parquet', index=False)
# 2. 2024 exploratorio
P = pd.read_parquet(C / 'predicciones/predicciones_2024.parquet').set_index('row_id')
lab = pd.concat([pd.read_parquet(C / f'base_s2_{l}.parquet').query('year==2024')[['row_id', 't0']] for l in LINES]).set_index('row_id').loc[P.index]
y = lab.t0.values
for k in SRC:
    col = np.zeros(len(P))
    for line in LINES:
        b = pd.read_parquet(C / f'base_s2_{line}.parquet'); g = np.exp(b.row_id.map(lg(SRC[k]['conf'][line], line)).values)
        f = (b.year == 2023).values; w = (b.year == 2024).values
        L = b.t0.values[f].sum() / (b.eef_coste.values[f] * g[f]).sum()
        pr = pd.Series(b.eef_coste.values[w] * g[w] * L, index=b.row_id.values[w])
        m = (P.line == line).values; col[m] = pr.loc[P.index[m]].values
    P[k] = col
P['A1fixF1b3n'] = P['A1fixF1b3'].values
for line in LINES:
    m = (P.line == line).values
    P.loc[m, 'A1fixF1b3n'] = P['A1fixF1b3'].values[m] * P['A1fixb3'].values[m].sum() / P['A1fixF1b3'].values[m].sum()
comp = M.components(P.customer_id.values, P.address_id.values)
names = ['R0', 'A1', 'A1fixb3', 'A1fixF1b3', 'A1fixF1b3n']
bs = M.boot_d2_diff(y, {n: P[n].values for n in names}, comp, n=4000)
ex = {}
for n in names:
    ex[n] = {'D2': round(float(M.d2(y, P[n].values)), 6),
             **{f'D2_{l}': round(float(M.d2(y[P.line.values == l], P[n].values[P.line.values == l])), 5) for l in LINES},
             'AE': {l: round(float(y[P.line.values == l].sum() / P[n].values[P.line.values == l].sum()), 4) for l in LINES}}
    for ref in ('A1', 'A1fixb3'):
        if n != ref:
            d = bs[n] - bs[ref]
            ex[n][f'menos_{ref}'] = round(float(M.d2(y, P[n].values) - M.d2(y, P[ref].values)), 6)
            ex[n][f'IC90_menos_{ref}'] = [round(float(np.quantile(d, q)), 6) for q in (0.05, 0.95)]
out['exploratorio_2024'] = ex
kc = y < np.quantile(y, 0.999); compc = M.components(P.customer_id.values[kc], P.address_id.values[kc])
bc = M.boot_d2_diff(y[kc], {n: P[n].values[kc] for n in ['A1fixb3', 'A1fixF1b3n']}, compc, n=2000)
out['exploratorio_2024_cuerpo_F1b3n_menos_b3'] = {'diff': round(float(M.d2(y[kc], P['A1fixF1b3n'].values[kc]) - M.d2(y[kc], P['A1fixb3'].values[kc])), 6),
                                                  'IC90': [round(float(np.quantile(bc['A1fixF1b3n'] - bc['A1fixb3'], q)), 6) for q in (0.05, 0.95)]}
out['cociente_total_F1b3_frente_b3_2024'] = {l: round(float(P['A1fixF1b3'].values[(P.line == l).values].sum() / P['A1fixb3'].values[(P.line == l).values].sum()), 4) for l in LINES}
# 3. producción 2025
ss = pd.read_parquet(R / 'datos/s2/sample_submission.parquet')
ref = pd.read_csv(O / 'A1fixb3_2025.csv'); assert (ref.row_id.values == ss.row_id.values).all()
parts = []
for line in LINES:
    b = pd.read_parquet(R / f'salidas/s2/base_{line}.parquet'); g = np.exp(b.row_id.map(lg(SRC['A1fixF1b3']['full'][line], line)).values)
    tr = (b.split == 'train').values; te = (b.split == 'test').values
    L = b.t0.values[tr].sum() / (b.eef_coste.values[tr] * g[tr]).sum()
    parts.append(pd.DataFrame({'row_id': b.row_id.values[te], 'prediction': b.exposure_model.values[te] * g[te] * L}))
df = pd.concat(parts).set_index('row_id').loc[ss.row_id].reset_index()
pre = df.row_id.str[0].values; raw = {}
for line in LINES:
    m = pre == PFX[line]; tot_ref = ref.prediction.values[m].sum(); raw[line] = round(float(df.prediction.values[m].sum() / tot_ref), 4)
    df.loc[m, 'prediction'] = df.prediction.values[m] * tot_ref / df.prediction.values[m].sum()
assert len(df) == 209063 and (df.row_id.values == ss.row_id.values).all() and (df.prediction > 0).all() and np.isfinite(df.prediction).all()
p = O / 'A1fixF1b3n_2025.csv'; df.to_csv(p, index=False, float_format='%.6f', lineterminator='\n')
out['produccion_2025'] = {'archivo': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'filas': int(len(df)),
                          'total': round(float(df.prediction.sum()), 2), 'por_ramo': {k: round(float(df.prediction[pre == k].sum()), 2) for k in 'MBC'},
                          'cociente_antes_de_neutral': raw,
                          'tasa_por_ramo': {l: round(float(df.prediction[pre == PFX[l]].sum() / pd.read_parquet(R / f'salidas/s2/base_{l}.parquet').query("split=='test'").exposure_model.sum()), 1) for l in LINES},
                          'cambio_por_fila_frente_A1fixb3': {'mediana_abs': round(float(np.median(np.abs(df.prediction.values / ref.prediction.values - 1))), 4),
                                                             'p99_abs': round(float(np.quantile(np.abs(df.prediction.values / ref.prediction.values - 1), 0.99)), 4)}}
json.dump(out, open(O / 'evaluacion_final.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
