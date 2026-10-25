"""DES24: la estructura de mis candidatos medida en el desarrollado 2024, fuera de tiempo.

Criterio tomado de la línea ML independiente (CLAUDE.md, sección 43). Pregunta: ¿habría anticipado la caída pública del
envío 57602707 (mezcla con C2 regularizado, −0,00043 frente a la mezcla con la base)? Exploratorio, medido después de ese
envío; no decide nada por sí solo.

Modelos conf, ya guardados: LightGBM entrenados con el desarrollado 2021-2023 (salidas/transfer/gbm_dev212223_*). Para
cada ramo se toman las filas del desarrollado 2024 (base completa s1, split train), con las variables del esquema común,
exposure_model y la historia F1 (siniestros reportados antes de period_start; años observados desde el primer periodo de
la póliza en 2021-2024, igual que en el entrenamiento). Predicción = eef_coste × exp(media en log de las tres semillas) ×
nivel, con el nivel reajustado por balance en 2024 en cada ramo: solo se mide la estructura. D² Tweedie 1,5 por ramo y
global; diferencias pareadas con bootstrap de Poisson por componentes cliente-dirección (2.000 réplicas); cuerpo sin el
0,1 % de mayores importes. Escribe salidas/robustez/des24_candidatos.json.
"""
import json, pathlib, sys, time
import numpy as np, pandas as pd, lightgbm as lgb
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from variables import features
import marco as M

R = pathlib.Path('/home/claude/noche'); T = R / 'salidas/transfer'; O = R / 'salidas/robustez'
LINES = ['motor', 'buildings', 'contents']
S = lambda pfx: [f'{pfx}s{s}' for s in (11, 12, 13)]
CANDS = {
    'base': {'motor': ['v2fixf1conf', 'v2fixf1confs12', 'v2fixf1confs13'], 'buildings': ['v2f1conf', 'v2f1confs12', 'v2f1confs13'],
             'contents': ['v2f1conf', 'v2f1confs12', 'v2f1confs13']},
    'sinF1': {'motor': S('v2fixconf'), 'buildings': ['v2conf', 'v2confs12', 'v2confs13'], 'contents': ['v2conf', 'v2confs12', 'v2confs13']},
    'robreg': {l: S('robregconf') for l in LINES},
    'robcap': {l: S('robcapconf') for l in LINES},
    'robrej': {'motor': S('robregconf'), 'buildings': S('rejG2conf'), 'contents': S('rejG5conf')},
}
t0 = time.time(); rows = []
for line in LINES:
    b = pd.read_parquet(R / f'salidas/s1/base_{line}.parquet'); b = b[b.split == 'train'].reset_index(drop=True)
    X, _, _ = features(b, line, 's1'); X['exposure_model'] = b.exposure_model.values
    a = pd.read_parquet(R / 'salidas/s1/asignacion.parquet'); a = a[(a.line == line) & a.accepted][['policy_id', 'report_date']]
    a['rd'] = pd.to_datetime(a.report_date)
    bb = b[['row_id', 'policy_id', 'period_start']].copy(); bb['ps'] = pd.to_datetime(bb.period_start)
    mm = bb.merge(a, on='policy_id'); mm = mm[mm.rd < mm.ps]
    X['f1_siniestros_previos'] = bb.row_id.map(mm.groupby('row_id').size()).fillna(0).values
    X['f1_anios_observados'] = ((bb.ps - bb.policy_id.map(bb.groupby('policy_id').ps.min())).dt.days / 365.25).values
    w = (b.year == 2024).values; X = X.loc[w].reset_index(drop=True); b = b.loc[w].reset_index(drop=True)
    out = pd.DataFrame({'row_id': b.row_id.values, 'line': line, 'y': b.t0.values, 'e': b.eef_coste.values,
                        'cust': b.customer_id.astype(str).str.zfill(8).values, 'addr': b.address_id.astype(str).values})
    for c, spec in CANDS.items():
        lg_ = []
        for tg in spec[line]:
            bst = lgb.Booster(model_file=str(T / f'gbm_dev212223_{tg}_{line}.txt'))
            lg_.append(bst.predict(X[bst.feature_name()], raw_score=True))
        m0 = out.e.values * np.exp(np.mean(lg_, axis=0))
        out[c] = m0 * out.y.sum() / m0.sum()
    out['exposicion'] = out.e.values * out.y.sum() / out.e.sum()
    rows.append(out); print(line, len(out), round(time.time() - t0), flush=True)
P = pd.concat(rows, ignore_index=True); y = P.y.values
cands = list(CANDS) + ['exposicion']
res = {'filas': {l: int((P.line == l).sum()) for l in LINES}, 'D2': {}, 'frente_a_base': {}}
for scope in ['global'] + LINES:
    m = np.ones(len(P), bool) if scope == 'global' else (P.line == scope).values
    ym = y[m]; comp = M.components(P.cust.values[m], P.addr.values[m])
    res['D2'][scope] = {c: round(float(M.d2(ym, P[c].values[m])), 6) for c in cands}
    bs = M.boot_d2_diff(ym, {c: P[c].values[m] for c in CANDS}, comp, n=2000)
    kc = ym <= np.quantile(ym, 0.999)
    res['frente_a_base'][scope] = {c: {'diff': round(float(M.d2(ym, P[c].values[m]) - M.d2(ym, P['base'].values[m])), 6),
                                       'IC90': [round(float(np.quantile(bs[c] - bs['base'], q)), 6) for q in (0.05, 0.95)],
                                       'cuerpo': round(float(M.d2(ym[kc], P[c].values[m][kc]) - M.d2(ym[kc], P['base'].values[m][kc])), 6)}
                                   for c in CANDS if c != 'base'}
    print(scope, res['D2'][scope], json.dumps(res['frente_a_base'][scope]), flush=True)
prev = json.load(open(O / 'resumen.json'))
res['referencias'] = {'robreg_dev2023': prev['robreg']['desarrollo_2023']['diff'], 'robreg_2024_emergente': prev['robreg']['exploratorio_2024']['diff'],
                      'publico_mezcla_robusta_menos_enviada': -0.00043}
res['segundos'] = round(time.time() - t0)
json.dump(res, open(O / 'des24_candidatos.json', 'w'), indent=1, ensure_ascii=False)
