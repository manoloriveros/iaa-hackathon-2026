"""¿El efecto de la historia F1 es de orden o de nivel? (conciliación con el revisor rev4, sección 2.3 de su informe)

rev4 encontró que, con historia de 12 meses y sin años observados, calibrar el nivel en el emergente 2023 (sin historia
observable) hace que el modelo con historia sobreestime 2024. Aquí se mide lo mismo para A1fixF1, que además lleva los años
observados de la póliza:
  1. 2024 exploratorio: A/E por ramo y por segmento (cliente nuevo frente a renovación) de A1fix y A1fixF1 con el nivel
     calibrado en 2023, y la diferencia de D² con la calibración neutral (A1fixF1 reescalado por ramo al total 2024 de
     A1fix, sin mirar los siniestros de 2024).
  2. Producción 2025: diferencia de totales entre A1fixF1 y A1fix por ramo y segmento, y una variante neutral
     (A1fixF1n: A1fixF1 reescalado por ramo al total de A1fix) con su versión con tendencia TEN-N2 (A1fixF1nTc).
Escribe salidas/correccion/f1_nivel.json y los CSV A1fixF1n_2025.csv y A1fixF1nTc_2025.csv. Sin enviar.
"""
import hashlib, json, pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M

R = pathlib.Path('/home/claude/noche'); T = R / 'salidas/transfer'; C = R / 'salidas/conf'; O = R / 'salidas/correccion'
LINES = ['motor', 'buildings', 'contents']; PFX = {'motor': 'M', 'buildings': 'B', 'contents': 'C'}
CONF = {'A1fix': {'motor': 'dev212223_v2fixconfs11', 'buildings': 'dev212223_v2conf', 'contents': 'dev212223_v2conf'},
        'A1fixF1': {'motor': 'dev212223_v2fixf1conf', 'buildings': 'dev212223_v2f1conf', 'contents': 'dev212223_v2f1conf'}}
lg = lambda tag, line: pd.read_parquet(T / f'lg_{tag}_{line}_em.parquet').set_index('row_id').lg_dev
out = {}
# 1. 2024 exploratorio
P = pd.read_parquet(C / 'predicciones/predicciones_2024.parquet').set_index('row_id')
lab = pd.concat([pd.read_parquet(C / f'base_s2_{l}.parquet').query('year==2024')[['row_id', 't0']] for l in LINES]).set_index('row_id').loc[P.index]
y = lab.t0.values
seen23 = set()
for line in LINES:
    b = pd.read_parquet(C / f'base_s2_{line}.parquet'); seen23 |= set(b.loc[b.year == 2023, 'customer_id'])
cold = ~P.customer_id.isin(seen23).values
for k, tags in CONF.items():
    col = np.zeros(len(P))
    for line in LINES:
        b = pd.read_parquet(C / f'base_s2_{line}.parquet'); g = np.exp(b.row_id.map(lg(tags[line], line)).values)
        f = (b.year == 2023).values; w = (b.year == 2024).values
        L = b.t0.values[f].sum() / (b.eef_coste.values[f] * g[f]).sum()
        pr = pd.Series(b.eef_coste.values[w] * g[w] * L, index=b.row_id.values[w])
        m = (P.line == line).values; col[m] = pr.loc[P.index[m]].values
    P[k] = col
P['A1fixF1n'] = P['A1fixF1'].values
for line in LINES:
    m = (P.line == line).values; P.loc[m, 'A1fixF1n'] = P['A1fixF1'].values[m] * P['A1fix'].values[m].sum() / P['A1fixF1'].values[m].sum()
ae = {}
for k in ['A1fix', 'A1fixF1', 'A1fixF1n']:
    ae[k] = {}
    for line in LINES:
        m = (P.line == line).values
        ae[k][line] = {'global': round(y[m].sum() / P[k].values[m].sum(), 4), 'cliente_nuevo': round(y[m & cold].sum() / P[k].values[m & cold].sum(), 4),
                       'renovacion': round(y[m & ~cold].sum() / P[k].values[m & ~cold].sum(), 4)}
comp = M.components(P.customer_id.values, P.address_id.values)
names = ['A1fix', 'A1fixF1', 'A1fixF1n']
bs = M.boot_d2_diff(y, {n: P[n].values for n in names}, comp, n=4000)
d2 = {n: {'D2': round(M.d2(y, P[n].values), 5), 'menos_A1fix': round(M.d2(y, P[n].values) - M.d2(y, P['A1fix'].values), 5),
          'IC90': [round(float(np.quantile(bs[n] - bs['A1fix'], q)), 5) for q in (0.05, 0.95)],
          **{f'D2_{l}': round(M.d2(y[P.line.values == l], P[n].values[P.line.values == l]), 5) for l in LINES},
          'D2_cliente_nuevo': round(M.d2(y[cold], P[n].values[cold]), 5), 'D2_renovacion': round(M.d2(y[~cold], P[n].values[~cold]), 5)} for n in names}
out['exploratorio_2024'] = {'AE': ae, 'D2': d2, 'cociente_total_F1_frente_A1fix': {l: round(P['A1fixF1'].values[(P.line == l).values].sum() / P['A1fix'].values[(P.line == l).values].sum(), 4) for l in LINES}}
# 2. producción 2025
a = pd.read_csv(O / 'A1fix_2025.csv'); f1 = pd.read_csv(O / 'A1fixF1_2025.csv'); assert (a.row_id == f1.row_id).all()
seen = set()
for line in LINES:
    b = pd.read_parquet(R / f'salidas/s2/base_{line}.parquet'); seen |= set(b.loc[b.split == 'train', 'customer_id'])
te = pd.concat([pd.read_parquet(R / f'salidas/s2/base_{l}.parquet').query("split=='test'")[['row_id', 'customer_id']] for l in LINES]).set_index('row_id').loc[a.row_id]
ren = te.customer_id.isin(seen).values
pre = a.row_id.str[0].values
prod = {}
for line in LINES:
    m = pre == PFX[line]
    prod[line] = {'cociente_total': round(f1.prediction.values[m].sum() / a.prediction.values[m].sum(), 4),
                  'cociente_cliente_nuevo': round(f1.prediction.values[m & ~ren].sum() / a.prediction.values[m & ~ren].sum(), 4),
                  'cociente_renovacion': round(f1.prediction.values[m & ren].sum() / a.prediction.values[m & ren].sum(), 4),
                  'peso_renovacion': round(a.prediction.values[m & ren].sum() / a.prediction.values[m].sum(), 4)}
out['produccion_2025'] = prod
tt = json.load(open(O / 'produccion_tendencia_tope.json'))['factores_exactos']
n = f1.copy()
for line in LINES:
    m = pre == PFX[line]; n.loc[m, 'prediction'] = f1.prediction.values[m] * a.prediction.values[m].sum() / f1.prediction.values[m].sum()
for tag, df in (('A1fixF1n', n), ('A1fixF1nTc', n.assign(prediction=n.prediction * pd.Series(pre).map(tt).values))):
    assert len(df) == 209063 and df.row_id.is_unique and (df.prediction > 0).all() and np.isfinite(df.prediction).all()
    p = O / f'{tag}_2025.csv'; df.to_csv(p, index=False, float_format='%.6f', lineterminator='\n')
    out[tag] = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'total': round(float(df.prediction.sum()), 2),
                'por_ramo': {k: round(float(df.prediction[pre == k].sum()), 2) for k in 'MBC'}}
json.dump(out, open(O / 'f1_nivel.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
