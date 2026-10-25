"""Resuelve la sonda de nivel con los seis D² públicos y construye el archivo final según la preinscripción.

Uso: python sonda_nivel_resolver.py motor_0.85=D2 motor_1.20=D2 buildings_0.80=D2 buildings_1.25=D2 contents_0.85=D2 contents_1.20=D2
     (con --prueba simula los D² con 2024 para comprobar que el código funciona; no escribe el archivo final)
Escribe salidas/sonda/resultado_sonda.json y salidas/sonda/final_sonda_2025.csv.
"""
import hashlib, json, pathlib, sys
import numpy as np, pandas as pd

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/sonda'
pre = json.load(open(O / 'preinscripcion_sonda.json')); D0 = pre['base']['d2_publico']
PFX = {'motor': 'M', 'buildings': 'B', 'contents': 'C'}
base = pd.read_csv(R / 'datos/mlind/mezcla50_designada_mlind_2025.csv', dtype={'row_id': str})
assert hashlib.sha256((R / 'datos/mlind/mezcla50_designada_mlind_2025.csv').read_bytes()).hexdigest() == pre['base']['sha256']
pfx = base.row_id.str[0].values
S = {l: float(np.sqrt(base.prediction.values[pfx == k]).sum()) for l, k in PFX.items()}
args = dict(a.split('=') for a in sys.argv[1:] if '=' in a)
if '--prueba' in sys.argv:  # D² simulados con 2024 para probar el código
    import io, contextlib, runpy
    sys.path.insert(0, str(R / 'codigo')); import marco as M
    with contextlib.redirect_stdout(io.StringIO()):
        g = runpy.run_path(str(R / 'codigo/evaluar_final.py'))
    P, y = g['P'], g['y']; mu = P['A1fixF1b3n'].values; ln = P.line.values; pub = np.random.default_rng(1).random(len(y)) < 0.33
    D0 = round(float(M.d2(y[pub], mu[pub])), 5); args = {}
    for f, v in pre['sondas'].items():
        m2 = mu.copy(); m2[ln == v['ramo']] *= v['c']; args[f"{v['ramo']}_{v['c']:.2f}"] = round(float(M.d2(y[pub], m2[pub])), 5)
    S = {l: float(np.sqrt(mu[pub & (ln == l)]).sum()) for l in PFX}  # en la prueba, Σμ^(1/2) del público simulado
res = {'d2_base': D0, 'd2_sondas': args}
cstar, bB = {}, {}
for l in PFX:
    pts = [(v['c'], float(args[f"{v['ramo']}_{v['c']:.2f}"])) for v in pre['sondas'].values() if v['ramo'] == l]
    X = np.array([[c ** -0.5 - 1, c ** 0.5 - 1] for c, _ in pts]); d = np.array([D0 - s for _, s in pts])
    a, b_ = np.linalg.solve(X, d); bB[l] = b_
    cstar[l] = float(a / b_) if (a > 0 and b_ > 0) else float('nan')
ratio = {l: bB[l] / S[l] for l in PFX}; rmean = np.mean(list(ratio.values()))
coh = max(abs(v / rmean - 1) for v in ratio.values())
Z = dict(pre['credibilidad']['Z']); fact = 0.5 if coh > 0.05 else 1.0
cfin = {}
for l in PFX:
    if not np.isfinite(cstar[l]): cfin[l] = 1.0; continue
    cfin[l] = float(np.clip(np.exp(fact * Z[l] * np.log(cstar[l])), 0.80, 1.25))
res.update({'c_optimo_publico': {l: round(v, 4) for l, v in cstar.items()}, 'coherencia_max_desvio': round(float(coh), 4), 'factor_Z': fact,
            'c_final': {l: round(v, 4) for l, v in cfin.items()},
            'd2_publico_previsto_final': round(float(D0 - sum((np.linalg.solve(np.array([[c ** -0.5 - 1, c ** 0.5 - 1] for c, _ in [(v['c'], 0) for v in pre['sondas'].values() if v['ramo'] == l]]),
                                                                                np.array([D0 - float(args[f"{v['ramo']}_{v['c']:.2f}"]) for v in pre['sondas'].values() if v['ramo'] == l])) @ np.array([cfin[l] ** -0.5 - 1, cfin[l] ** 0.5 - 1])) for l in PFX)), 5)})
if '--prueba' not in sys.argv:
    out = base.copy()
    for l, k in PFX.items():
        m = pfx == k; out.loc[m, 'prediction'] = out.prediction.values[m] * cfin[l]
    assert len(out) == 209063 and np.isfinite(out.prediction).all() and (out.prediction > 0).all()
    p = O / 'final_sonda_2025.csv'; out.to_csv(p, index=False, float_format='%.6f', lineterminator='\n')
    res['final'] = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'total': round(float(out.prediction.sum()), 2),
                    'por_ramo': {k: round(float(out.prediction[pfx == k].sum()), 2) for k in PFX.values()}}
    json.dump(res, open(O / 'resultado_sonda.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
