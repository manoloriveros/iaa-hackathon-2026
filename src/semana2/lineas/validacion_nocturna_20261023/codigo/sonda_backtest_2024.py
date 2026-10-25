"""Backtest de la regla de la sonda en 2024 (sustituto): 200 particiones 33/67; la regla preinscrita (dos sondas por ramo,
redondeo a 5 decimales, Z y cotas de la preinscripción) se aplica con el público y se mide el cambio de D² en el privado.
Escribe salidas/sonda/backtest_2024.json."""
import io, contextlib, json, pathlib, runpy, sys
import numpy as np
R = pathlib.Path('/home/claude/noche'); sys.path.insert(0, str(R / 'codigo')); import marco as M
pre = json.load(open(R / 'salidas/sonda/preinscripcion_sonda.json')); Z = pre['credibilidad']['Z']
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(R / 'codigo/evaluar_final.py'))
P, y = g['P'], g['y']; mu = P['A1fixF1b3n'].values; ln = P.line.values; LINES = ['motor', 'buildings', 'contents']
sond = [(v['ramo'], v['c']) for v in pre['sondas'].values()]
rng = np.random.default_rng(99); gains = []; gl = {l: [] for l in LINES}
for r in range(200):
    pub = rng.random(len(y)) < 0.33; prv = ~pub
    D0 = round(float(M.d2(y[pub], mu[pub])), 5); sc = {}
    for l, c in sond:
        m2 = mu.copy(); m2[ln == l] *= c; sc.setdefault(l, []).append((c, round(float(M.d2(y[pub], m2[pub])), 5)))
    mf = mu.copy()
    for l in LINES:
        X = np.array([[c ** -0.5 - 1, c ** 0.5 - 1] for c, _ in sc[l]]); d = np.array([D0 - s for _, s in sc[l]])
        a, b = np.linalg.solve(X, d); cs = a / b if (a > 0 and b > 0) else 1.0
        cf = float(np.clip(np.exp(Z[l] * np.log(cs)), 0.80, 1.25)); mf[ln == l] *= cf
        m1 = mu.copy(); m1[ln == l] *= cf; gl[l].append(M.d2(y[prv], m1[prv]) - M.d2(y[prv], mu[prv]))
    gains.append(M.d2(y[prv], mf[prv]) - M.d2(y[prv], mu[prv]))
g = np.array(gains)
out = {'ganancia_privado_media': round(float(g.mean()), 5), 'p05_p50_p95': [round(float(q), 5) for q in np.quantile(g, [0.05, 0.5, 0.95])],
       'prob_ganar': round(float((g > 0).mean()), 3), 'por_ramo_media': {l: round(float(np.mean(v)), 5) for l, v in gl.items()}}
json.dump(out, open(R / 'salidas/sonda/backtest_2024.json', 'w'), indent=1); print(json.dumps(out, indent=1))
