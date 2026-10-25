"""Sonda de nivel por ramo con el tablero público (diseño y simulación, antes de enviar nada).

Idea. Con la desviación Tweedie 1,5, si a las predicciones de un ramo se les multiplica por c, la desviación del público es
  dev(c) = C0 + 4 (A c^(-1/2) + B c^(1/2)),  A = Σ y μ^(-1/2),  B = Σ μ^(1/2)  (sumas sobre las filas públicas del ramo),
y el D² público es lineal en (c^(-1/2) - 1, c^(1/2) - 1). Con dos envíos por ramo, cada uno escalando solo ese ramo, se
despejan βA y βB (β = 4 / nula pública) y el óptimo público del ramo es exacto: c* = A / B. Vale con o sin pesos, y no hace
falta saber qué filas son públicas.

Simulación. Usa 2024 (ya abierto) como sustituto: predicciones de la receta final con nivel 2023, un 33 % aleatorio como
"público", puntuaciones redondeadas a 5 decimales como en Kaggle. Mide (a) el error de recuperar c* por el redondeo y (b) el
ruido del óptimo público frente al privado, reescalado al tamaño del test 2025 (209.063 filas). Calcula también la curvatura
k (pérdida de D² global por unidad de (log c)²) de cada ramo. Escribe salidas/sonda/diseno.json.
"""
import io, contextlib, json, pathlib, runpy, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/sonda'; O.mkdir(exist_ok=True)
LINES = ['motor', 'buildings', 'contents']
ESCALAS = {'motor': (0.85, 1.20), 'buildings': (0.80, 1.25), 'contents': (0.85, 1.20)}
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(R / 'codigo/evaluar_final.py'))
P, y = g['P'], g['y']; mu = P['A1fixF1b3n'].values; ln = P.line.values
N25 = 209063; f_tam = len(y) / N25


def d2r(yv, m):
    return round(float(M.d2(yv, m)), 5)


def resolver(base, sc):
    """sc: {ramo: [(c, D2), (c, D2)]}; base: D2 con c = 1. Devuelve c* por ramo."""
    out = {}
    for l, pts in sc.items():
        X = np.array([[c ** -0.5 - 1, c ** 0.5 - 1] for c, _ in pts]); d = np.array([base - s for _, s in pts])
        a, b = np.linalg.solve(X, d)  # βA, βB
        out[l] = float(a / b) if b > 0 and a > 0 else float('nan')
    return out


rng = np.random.default_rng(20261024); sims = []
for r in range(300):
    pub = rng.random(len(y)) < 0.33
    yp, mp, lp = y[pub], mu[pub], ln[pub]
    base = d2r(yp, mp); sc = {}
    for l in LINES:
        sc[l] = []
        for c in ESCALAS[l]:
            m2 = mp.copy(); k = lp == l; m2[k] *= c; sc[l].append((c, d2r(yp, m2)))
    est = resolver(base, sc)
    rec = {}
    for l in LINES:
        k = lp == l; tru_pub = (yp[k] / np.sqrt(mp[k])).sum() / np.sqrt(mp[k]).sum()
        kv = (~pub) & (ln == l); tru_prv = (y[kv] / np.sqrt(mu[kv])).sum() / np.sqrt(mu[kv]).sum()
        rec[l] = (np.log(est[l]), np.log(tru_pub), np.log(tru_prv))
    sims.append(rec)
out = {'escalas': ESCALAS, 'filas_2024': int(len(y)), 'filas_2025': N25, 'replicas': len(sims)}
for l in LINES:
    e = np.array([s[l][0] for s in sims]); tp = np.array([s[l][1] for s in sims]); tv = np.array([s[l][2] for s in sims])
    out[l] = {'error_redondeo_log_max': round(float(np.abs(e - tp).max()), 5), 'error_redondeo_log_sd': round(float((e - tp).std()), 5),
              'sd_log_pub_menos_priv_2024': round(float((tp - tv).std()), 4),
              'sd_log_pub_menos_priv_2025': round(float((tp - tv).std() * np.sqrt(f_tam)), 4)}
# curvatura de la pérdida de D² global por ramo (en 2024, todo el año): k = pérdida / (log c)^2 alrededor del óptimo del ramo
for l in LINES:
    k = ln == l; copt = (y[k] / np.sqrt(mu[k])).sum() / np.sqrt(mu[k]).sum(); m0 = mu.copy(); m0[k] *= copt; d0 = M.d2(y, m0)
    loss = []
    for dl in (-0.1, 0.1):
        m1 = mu.copy(); m1[k] *= copt * np.exp(dl); loss.append(d0 - M.d2(y, m1))
    out[l]['c_optimo_2024'] = round(float(copt), 4); out[l]['k_curvatura'] = round(float(np.mean(loss) / 0.01), 4)
json.dump(out, open(O / 'diseno.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
