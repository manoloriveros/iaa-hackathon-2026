"""Evaluación de los candidatos de robustez (preinscripción CLA-S2-ROBUSTEZ-20261024) frente a la base A1fixF1b3n.

Para cada candidato (robcap, robreg y, si se pide, robcapreg): compuestos de tres semillas (completo y conf), desarrollo 2023
con s2_escalera.py (nivel por balance en cada fold), 2024 exploratorio con nivel 2023 y calibración neutral al total de A1fixb3,
y la regla preinscrita. Uso: python robustez_evaluar.py robcap robreg
Escribe salidas/robustez/evaluacion_{candidato}.json y salidas/robustez/resumen.json.
"""
import io, contextlib, json, pathlib, runpy, subprocess, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M
from comparar import compare

R = pathlib.Path('/home/claude/noche'); T = R / 'salidas/transfer'; C = R / 'salidas/conf'; O = R / 'salidas/robustez'
LINES = ['motor', 'buildings', 'contents']
REF = sys.argv[sys.argv.index('--ref') + 1] if '--ref' in sys.argv else None
cands = [a for a in sys.argv[1:] if not a.startswith('--') and a != REF] or ['robcap', 'robreg']


def tags(c, line, conf):
    pref = 'dev212223' if conf else 'dev21222324'
    return [f'{pref}_{c}{"conf" if conf else ""}s{s}' for s in (11, 12, 13)]


def lg(tg, line):
    return pd.concat([pd.read_parquet(T / f'lg_{t}_{line}_em.parquet').set_index('row_id').lg_dev for t in tg], axis=1).mean(axis=1)


BASE_F1 = {False: {'motor': ['dev21222324_v2fixf1', 'dev21222324_v2fixf1s12', 'dev21222324_v2fixf1s13'],
                   'buildings': ['dev21222324_v2f1', 'dev21222324_v2f1s12', 'dev21222324_v2f1s13'],
                   'contents': ['dev21222324_v2f1', 'dev21222324_v2f1s12', 'dev21222324_v2f1s13']},
           True: {'motor': ['dev212223_v2fixf1conf', 'dev212223_v2fixf1confs12', 'dev212223_v2fixf1confs13'],
                  'buildings': ['dev212223_v2f1conf', 'dev212223_v2f1confs12', 'dev212223_v2f1confs13'],
                  'contents': ['dev212223_v2f1conf', 'dev212223_v2f1confs12', 'dev212223_v2f1confs13']}}


def lgc(c, line, conf):
    """Relatividad compuesta (log) del candidato."""
    if c == 'robrej':  # C4: autos C2; edificios G2; contenidos G5 (elegidas con la validación interna del desarrollado)
        nm = {'motor': 'robreg', 'buildings': 'rejG2', 'contents': 'rejG5'}[line]
        return lg(tags(nm, line, conf), line)
    if c == 'robglmgbm':  # C3: media en log del GBM base (tres semillas) y del GLM con historia
        glm = pd.read_parquet(T / f'lg_{"dev212223_glm1f1conf" if conf else "dev21222324_glm1f1"}_{line}_em.parquet').set_index('row_id').lg_dev
        gbm = lg(BASE_F1[conf][line], line)
        return (gbm + glm.loc[gbm.index]) / 2
    return lg(tags(c, line, conf), line)


with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(R / 'codigo/evaluar_final.py'))
P, y = g['P'], g['y']
comp = M.components(P.customer_id.values, P.address_id.values); kc = y < np.quantile(y, 0.999)
REFSPEC, REFCOL = 'A1fixF1b3_nivel', 'A1fixF1b3n'


def col2024(c):
    col = np.zeros(len(P))
    for line in LINES:
        b = pd.read_parquet(C / f'base_s2_{line}.parquet'); gg = np.exp(b.row_id.map(lgc(c, line, True)).values)
        f = (b.year == 2023).values; w = (b.year == 2024).values
        L = b.t0.values[f].sum() / (b.eef_coste.values[f] * gg[f]).sum()
        pr = pd.Series(b.eef_coste.values[w] * gg[w] * L, index=b.row_id.values[w])
        m = (P.line == line).values; v = pr.loc[P.index[m]].values
        col[m] = v * P['A1fixb3'].values[m].sum() / v.sum()
    return col


if REF:
    REFSPEC = {'robreg': 'ROBreg_nivel'}[REF]; P['REF'] = col2024(REF); REFCOL = 'REF'
resumen = {}
for c in cands:
    spec = {'robcap': 'ROBcap_nivel', 'robreg': 'ROBreg_nivel', 'robcapreg': 'ROBcapreg_nivel', 'robglmgbm': 'ROBglmgbm_nivel', 'robrej': 'ROBrej_nivel'}[c]
    for line in LINES:
        lgc(c, line, False).rename('lg_dev').reset_index().to_parquet(T / f'lg_{c}b3_{line}_em.parquet', index=False)
    subprocess.run([sys.executable, str(R / 'codigo/s2_escalera.py'), spec], check=True, capture_output=True)
    ob = pd.read_parquet(R / f'salidas/s2/oof/{REFSPEC}.parquet').set_index('row_id'); oc = pd.read_parquet(R / f'salidas/s2/oof/{spec}.parquet').set_index('row_id').loc[ob.index]
    yd = ob.y.values; cd = M.components(ob.customer_id.values, ob.address_id.values)
    bd = M.boot_d2_diff(yd, {'r': ob.mu.values, 'c': oc.mu.values}, cd, n=10000); dd = bd['c'] - bd['r']
    kd = yd <= np.quantile(yd, 0.999); bdk = M.boot_d2_diff(yd[kd], {'r': ob.mu.values[kd], 'c': oc.mu.values[kd]}, M.components(ob.customer_id.values[kd], ob.address_id.values[kd]), n=2000)
    dev = {'diff': M.d2(yd, oc.mu.values) - M.d2(yd, ob.mu.values), 'q05': np.quantile(dd, .05), 'q95': np.quantile(dd, .95)}
    devc = {'diff': M.d2(yd[kd], oc.mu.values[kd]) - M.d2(yd[kd], ob.mu.values[kd]), 'q05': np.quantile(bdk['c'] - bdk['r'], .05), 'q95': np.quantile(bdk['c'] - bdk['r'], .95)}
    col = np.zeros(len(P))
    for line in LINES:
        b = pd.read_parquet(C / f'base_s2_{line}.parquet'); gg = np.exp(b.row_id.map(lgc(c, line, True)).values)
        f = (b.year == 2023).values; w = (b.year == 2024).values
        L = b.t0.values[f].sum() / (b.eef_coste.values[f] * gg[f]).sum()
        pr = pd.Series(b.eef_coste.values[w] * gg[w] * L, index=b.row_id.values[w])
        m = (P.line == line).values; v = pr.loc[P.index[m]].values
        col[m] = v * P['A1fixb3'].values[m].sum() / v.sum()  # neutral: mismo total que la base
    P[c] = col
    bs = M.boot_d2_diff(y, {'base': P[REFCOL].values, c: col}, comp, n=4000)
    bsc = M.boot_d2_diff(y[kc], {'base': P[REFCOL].values[kc], c: col[kc]}, M.components(P.customer_id.values[kc], P.address_id.values[kc]), n=2000)
    e24 = {'diff': round(float(M.d2(y, col) - M.d2(y, P[REFCOL].values)), 6), 'IC90': [round(float(np.quantile(bs[c] - bs['base'], q)), 6) for q in (0.05, 0.95)],
           'cuerpo': round(float(M.d2(y[kc], col[kc]) - M.d2(y[kc], P[REFCOL].values[kc])), 6),
           'cuerpo_IC90': [round(float(np.quantile(bsc[c] - bsc['base'], q)), 6) for q in (0.05, 0.95)],
           'por_ramo': {l: round(float(M.d2(y[P.line.values == l], col[P.line.values == l]) - M.d2(y[P.line.values == l], P[REFCOL].values[P.line.values == l])), 5) for l in LINES}}
    d23 = {'diff': round(float(dev['diff']), 7), 'IC90': [round(float(dev['q05']), 7), round(float(dev['q95']), 7)], 'cuerpo': round(float(devc['diff']), 7), 'cuerpo_IC90': [round(float(devc['q05']), 7), round(float(devc['q95']), 7)]}
    pasa = bool(d23['diff'] > 0 and e24['diff'] > 0 and (d23['IC90'][0] > 0 or e24['IC90'][0] > 0) and d23['cuerpo'] > -0.0005 and e24['cuerpo'] > -0.0005)
    r = {'desarrollo_2023': d23, 'exploratorio_2024': e24, 'pasa_regla': pasa}
    r['referencia'] = REFCOL if not REF else REF; json.dump(r, open(O / f'evaluacion_{c}.json', 'w'), indent=1, ensure_ascii=False); resumen[c] = r
    print(c, json.dumps(r, ensure_ascii=False), flush=True)
old = json.load(open(O / 'resumen.json')) if (O / 'resumen.json').exists() else {}
old.update(resumen); json.dump(old, open(O / 'resumen.json', 'w'), indent=1, ensure_ascii=False)
