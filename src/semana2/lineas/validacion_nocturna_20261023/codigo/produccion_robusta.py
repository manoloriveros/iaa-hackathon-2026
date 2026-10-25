"""Producción con el candidato C2 (árboles regularizados), que pasó la regla preinscrita (CLA-S2-ROBUSTEZ-20261024).

1. A1robregF1b3n_2025.csv: relatividades de tres semillas del GBM regularizado con historia, nivel 2023-2024 por balance,
   reescalado por ramo al total de A1fixb3_2025.csv (historia neutral y mismo nivel que la designada; sin tendencia).
2. mezcla50_robusta_2025.csv: media 50/50 de (1) y de prediccion_2025_mlind.csv, igual que la mezcla enviada
   (mezcla50_designada_mlind_2025.csv) pero con el componente nuevo. Los totales por ramo no cambian.
3. Medición de las mezclas (vieja y nueva) a igual nivel por ramo: desarrollo 2023 (OOF) y 2024 exploratorio.
Escribe salidas/robustez/produccion_robusta.json y los dos CSV en salidas/robustez/. Sin enviar.
"""
import hashlib, io, contextlib, json, pathlib, runpy, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M

R = pathlib.Path('/home/claude/noche'); T = R / 'salidas/transfer'; C = R / 'salidas/conf'; O = R / 'salidas/robustez'
LINES = ['motor', 'buildings', 'contents']; PFX = {'motor': 'M', 'buildings': 'B', 'contents': 'C'}
lg = lambda tg, line: pd.concat([pd.read_parquet(T / f'lg_{t}_{line}_em.parquet').set_index('row_id').lg_dev for t in tg], axis=1).mean(axis=1)
FULL = lambda l: [f'dev21222324_robregs{s}' for s in (11, 12, 13)]
CONF = lambda l: [f'dev212223_robregconfs{s}' for s in (11, 12, 13)]
out = {}
# 1. producción
ss = pd.read_parquet(R / 'datos/s2/sample_submission.parquet')
ref = pd.read_csv(R / 'salidas/correccion/A1fixb3_2025.csv', dtype={'row_id': str}); assert (ref.row_id.values == ss.row_id.values).all()
parts = []
for line in LINES:
    b = pd.read_parquet(R / f'salidas/s2/base_{line}.parquet'); g = np.exp(b.row_id.map(lg(FULL(line), line)).values)
    tr = (b.split == 'train').values; te = (b.split == 'test').values
    L = b.t0.values[tr].sum() / (b.eef_coste.values[tr] * g[tr]).sum()
    parts.append(pd.DataFrame({'row_id': b.row_id.values[te], 'prediction': b.exposure_model.values[te] * g[te] * L}))
df = pd.concat(parts).set_index('row_id').loc[ss.row_id].reset_index(); pre = df.row_id.str[0].values
for line in LINES:
    m = pre == PFX[line]; df.loc[m, 'prediction'] = df.prediction.values[m] * ref.prediction.values[m].sum() / df.prediction.values[m].sum()
assert len(df) == 209063 and (df.row_id.values == ss.row_id.values).all() and np.isfinite(df.prediction).all() and (df.prediction > 0).all()
p1 = O / 'A1robregF1b3n_2025.csv'; df.to_csv(p1, index=False, float_format='%.6f', lineterminator='\n')
ml = pd.read_csv(R / 'datos/mlind/prediccion_2025_mlind.csv', dtype={'row_id': str}).set_index('row_id').loc[df.row_id].prediction.values
mz = df.copy(); mz['prediction'] = (df.prediction.values + ml) / 2
p2 = O / 'mezcla50_robusta_2025.csv'; mz.to_csv(p2, index=False, float_format='%.6f', lineterminator='\n')
old = pd.read_csv(R / 'datos/mlind/mezcla50_designada_mlind_2025.csv', dtype={'row_id': str}); assert (old.row_id.values == mz.row_id.values).all()
designada = pd.read_csv(R / 'salidas/correccion/A1fixF1b3n_2025.csv', dtype={'row_id': str})
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
out['produccion'] = {
    'A1robregF1b3n': {'sha256': sha(p1), 'total': round(float(df.prediction.sum()), 2), 'por_ramo': {k: round(float(df.prediction[pre == k].sum()), 2) for k in 'MBC'},
                      'cambio_por_fila_frente_designada': {'mediana_abs': round(float(np.median(np.abs(df.prediction / designada.prediction - 1))), 4),
                                                           'p99_abs': round(float(np.quantile(np.abs(df.prediction / designada.prediction - 1), 0.99)), 4)}},
    'mezcla50_robusta': {'sha256': sha(p2), 'total': round(float(mz.prediction.sum()), 2), 'por_ramo': {k: round(float(mz.prediction[pre == k].sum()), 2) for k in 'MBC'},
                         'cambio_por_fila_frente_mezcla_enviada': {'mediana_abs': round(float(np.median(np.abs(mz.prediction / old.prediction - 1))), 4),
                                                                   'p99_abs': round(float(np.quantile(np.abs(mz.prediction / old.prediction - 1), 0.99)), 4)}}}
# 3. mezclas a igual nivel: desarrollo 2023 y 2024
def neutral(ref_, other, lines):
    o2 = other.copy()
    for l in LINES:
        k = lines == l; o2[k] = other[k] * ref_[k].sum() / other[k].sum()
    return o2
ML = R / 'datos/mlind/oof/pred'
theirs = lambda part: pd.concat([pd.read_parquet(ML / part / f'T2b_{l}.parquet') for l in LINES]).set_index('row_id').mu
o_base = pd.read_parquet(R / 'salidas/s2/oof/A1fixF1b3_nivel.parquet').set_index('row_id'); o_new = pd.read_parquet(R / 'salidas/s2/oof/ROBreg_nivel.parquet').set_index('row_id').loc[o_base.index]
y = o_base.y.values; lnd = o_base.line.values; th = neutral(o_base.mu.values, theirs('dev').loc[o_base.index].values, lnd)
Pd = {'base': o_base.mu.values, 'robreg': o_new.mu.values, 'mezcla_vieja': (o_base.mu.values + th) / 2, 'mezcla_nueva': (o_new.mu.values + neutral(o_base.mu.values, th, lnd)) / 2}
comp = M.components(o_base.customer_id.values, o_base.address_id.values); bs = M.boot_d2_diff(y, Pd, comp, n=4000)
out['desarrollo_2023'] = {k: {'D2': round(float(M.d2(y, v)), 6), 'menos_mezcla_vieja': round(float(M.d2(y, v) - M.d2(y, Pd['mezcla_vieja'])), 6),
                              'IC90': [round(float(np.quantile(bs[k] - bs['mezcla_vieja'], q)), 6) for q in (0.05, 0.95)]} for k, v in Pd.items()}
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(R / 'codigo/evaluar_final.py'))
P, y4 = g['P'], g['y']; ln = P.line.values
col = np.zeros(len(P))
for line in LINES:
    b = pd.read_parquet(C / f'base_s2_{line}.parquet'); gg = np.exp(b.row_id.map(lg(CONF(line), line)).values)
    f = (b.year == 2023).values; w = (b.year == 2024).values
    L = b.t0.values[f].sum() / (b.eef_coste.values[f] * gg[f]).sum()
    pr = pd.Series(b.eef_coste.values[w] * gg[w] * L, index=b.row_id.values[w])
    m = (P.line == line).values; v = pr.loc[P.index[m]].values; col[m] = v * P['A1fixb3'].values[m].sum() / v.sum()
base4 = P['A1fixF1b3n'].values; th4 = neutral(base4, theirs('hold').loc[P.index].values, ln)
P4 = {'base': base4, 'robreg': col, 'mezcla_vieja': (base4 + th4) / 2, 'mezcla_nueva': (col + th4) / 2}
comp4 = M.components(P.customer_id.values, P.address_id.values); bs4 = M.boot_d2_diff(y4, P4, comp4, n=4000)
kc = y4 < np.quantile(y4, 0.999)
out['exploratorio_2024'] = {k: {'D2': round(float(M.d2(y4, v)), 6), 'menos_mezcla_vieja': round(float(M.d2(y4, v) - M.d2(y4, P4['mezcla_vieja'])), 6),
                                'IC90': [round(float(np.quantile(bs4[k] - bs4['mezcla_vieja'], q)), 6) for q in (0.05, 0.95)],
                                'cuerpo_menos_mezcla_vieja': round(float(M.d2(y4[kc], v[kc]) - M.d2(y4[kc], P4['mezcla_vieja'][kc])), 6)} for k, v in P4.items()}
json.dump(out, open(O / 'produccion_robusta.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
