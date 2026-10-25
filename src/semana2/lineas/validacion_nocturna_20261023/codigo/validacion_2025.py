"""Validación con la mezcla de 2025: pesos de desplazamiento de covariables (importance weighting).

Motivo: la mezcla robusta ganaba +0,0009 en 2024 y el público la puntuó −0,00043. Con el ruido medido para un par de envíos
tan parecidos (desviación típica 0,0004 al tamaño del público), eso es improbable si 2025 se pareciera a 2024. Y 2025 no
se parece: el 77 % es un bloque de nuevo negocio de un broker. Nuestra validación (2023 y 2024) está dominada por
renovaciones. Aquí se pondera cada fila de 2023-2024 por lo mucho que se parece a la cartera de 2025.

Método, por ramo: un LightGBM binario distingue filas de 2025 (test) de filas de 2023-2024 (entrenamiento) con las
variables de riesgo del esquema común (sin fechas, mes ni exposición). Las probabilidades de las filas de entrenamiento
salen fuera de muestra (5 folds por cliente). Peso w = p / (1 − p), recortado al percentil 99,5 y normalizado a media 1.
Con esos pesos se recalcula el D² ponderado de 2024 (exploratorio) para los pares que importan, y se informa el tamaño
efectivo de muestra (Kish). Escribe salidas/robustez/validacion_2025.json y salidas/robustez/pesos_2025.parquet.
"""
import io, contextlib, json, pathlib, runpy, sys
import numpy as np, pandas as pd, lightgbm as lgb
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from variables import features
import marco as M

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/robustez'
LINES = ['motor', 'buildings', 'contents']
DROP = {'start_month', 'exposure_model', 'make_model'}
pesos = []; diag = {}
for line in LINES:
    b = pd.read_parquet(R / f'salidas/s2/base_{line}.parquet')
    X, cols, _ = features(b, line, 's2'); cols = [c for c in cols if c not in DROP]
    z = (b.split == 'test').values.astype(int)
    fold = M.fold_of(b.customer_id.values, salt='pesos2025', k=5)
    p = np.zeros(len(b))
    prm = dict(objective='binary', learning_rate=0.05, num_leaves=31, min_data_in_leaf=200, feature_fraction=0.8, bagging_fraction=0.8,
               bagging_freq=1, lambda_l2=10.0, verbose=-1, seed=7, deterministic=True, force_row_wise=True, num_threads=2)
    for k in range(5):
        tr, te = fold != k, fold == k
        bst = lgb.train(prm, lgb.Dataset(X.loc[tr, cols], z[tr]), num_boost_round=300)
        p[te] = bst.predict(X.loc[te, cols])
    trn = z == 0
    w = p[trn] / (1 - p[trn]); w = np.minimum(w, np.quantile(w, 0.995)); w = w / w.mean()
    auc = float(pd.Series(p).rank().values[z == 1].sum() - z.sum() * (z.sum() + 1) / 2) / (z.sum() * (len(z) - z.sum()))
    ess = float(w.sum() ** 2 / (w ** 2).sum())
    nb = b.new_business.values.astype(bool)
    diag[line] = {'auc_2025_frente_2023_24': round(auc, 4), 'filas_entrenamiento': int(trn.sum()), 'tamano_efectivo_kish': round(ess, 0),
                  'peso_medio_nuevo_negocio': round(float(w[nb[trn]].mean()), 3), 'peso_medio_renovacion': round(float(w[~nb[trn]].mean()), 3),
                  'cuota_nb_ponderada': round(float(w[nb[trn]].sum() / w.sum()), 3), 'cuota_nb_2025': round(float(nb[z == 1].mean()), 3)}
    pesos.append(pd.DataFrame({'row_id': b.row_id.values[trn], 'w2025': w}))
    print(line, diag[line], flush=True)
W = pd.concat(pesos).set_index('row_id').w2025
W.reset_index().to_parquet(O / 'pesos_2025.parquet', index=False)


def d2w(y, mu, w):
    y = np.asarray(y, float); nul = np.full_like(y, np.average(y, weights=w))
    return 1 - (w * M.dev(y, mu)).sum() / (w * M.dev(y, nul)).sum()


with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(R / 'codigo/produccion_robusta.py'))
P = g['P']; P4 = g['P4']; y = g['y4']; ln = P.line.values; w = W.loc[P.index].values
comp = M.components(P.customer_id.values, P.address_id.values); Kc = comp.max() + 1
pairs = {'mezcla_robusta_menos_enviada': ('mezcla_nueva', 'mezcla_vieja'), 'C2_menos_designada': ('robreg', 'base')}
rng = np.random.default_rng(11); res = {}
for nm, (a, b_) in pairs.items():
    full = d2w(y, P4[a], w) - d2w(y, P4[b_], w); unw = M.d2(y, P4[a]) - M.d2(y, P4[b_])
    bs = []
    for _ in range(1000):  # bootstrap de Poisson por componente, con los pesos de 2025
        cw = rng.poisson(1.0, Kc)[comp] * w
        bs.append(d2w(y, P4[a], cw) - d2w(y, P4[b_], cw))
    res[nm] = {'sin_pesos_2024': round(float(unw), 6), 'con_pesos_2025': round(float(full), 6), 'IC90_con_pesos': [round(float(q), 6) for q in np.quantile(bs, [0.05, 0.95])],
               'por_ramo_con_pesos': {l: round(float(d2w(y[ln == l], P4[a][ln == l], w[ln == l]) - d2w(y[ln == l], P4[b_][ln == l], w[ln == l])), 5) for l in LINES}}
    print(nm, res[nm], flush=True)
out = {'diagnostico_pesos': diag, 'pares_2024': res, 'diferencia_publica_observada': -0.00043}
json.dump(out, open(O / 'validacion_2025.json', 'w'), indent=1, ensure_ascii=False)
