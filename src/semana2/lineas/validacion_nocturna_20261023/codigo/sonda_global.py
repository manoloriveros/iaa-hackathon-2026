"""Sonda de nivel global: diseño, simulación, backtest, archivos y preinscripción (sin enviar nada).

Pedido del participante (24-10, tras ver el tablero: séptimos de siete, a 0,0078-0,0106 de los primeros): «Sonda de nivel
global». Sustituye a la sonda por ramo de seis envíos (salidas/sonda/preinscripcion_sonda.json), que no se usó.

Fórmula. Con la desviación Tweedie 1,5, si todas las predicciones se multiplican por c, la desviación del público es
  dev(c) = C0 + 4 (A c^(-1/2) + B c^(1/2)),  A = Σ y μ^(-1/2),  B = Σ μ^(1/2)  (sumas sobre las filas públicas),
y el D² público, D2(c) = 1 − dev(c) / nula, es lineal en (c^(-1/2) − 1, c^(1/2) − 1):
  D2(1) − D2(c) = βA (c^(-1/2) − 1) + βB (c^(1/2) − 1),  βA = 4A / nula,  βB = 4B / nula.
Con la base ya puntuada (c = 1, envío 57599788, 0,15390) y dos sondas se despejan βA y βB, y el óptimo público es exacto:
c* = A / B = βA / βB. No hace falta saber qué filas son públicas ni la desviación nula.

Credibilidad (fijada aquí, antes de ver ninguna puntuación de sonda). c_final = exp(Z · log c*), Z = τ² / (τ² + σ²).
σ: ruido entre el óptimo público y el privado, medido con 2024 como sustituto, remuestreado por componentes al tamaño de
2025 y partido al azar 33/67 (la escala por raíz del tamaño queda solo de control). τ = 0,12: incertidumbre previa del logaritmo del nivel global de 2025 frente al de la mezcla; es el salto
global observado de 2023 a 2024 (real/esperado 0,884, log −0,12) y no incluye el cambio de cartera (76 % de nuevo negocio en
2025 frente a 12-15 %), que podría ampliarlo. c_final se acota a [0,75; 1,33].

Backtest: 2024 remuestreado por componentes al tamaño de 2025 (200 réplicas, partición 33/67); la regla completa (dos sondas,
redondeo a 5 decimales, Z, cotas) en cuatro escenarios de nivel; se mide el cambio de D² en el privado. σ sale del mismo
remuestreo. Escribe salidas/sonda_global/{diseno,backtest,preinscripcion}.json y los CSV.
"""
import hashlib, io, contextlib, json, pathlib, runpy, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/sonda_global'; O.mkdir(exist_ok=True)
BASE = R / 'datos/mlind/mezcla50_designada_mlind_2025.csv'; SHA_BASE = '12831ef4a05c1773824abe5fa139d9503dd2989b4874e7d93cfc000406cfdb4a'
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == SHA_BASE
TAU = 0.12; COTAS = (0.75, 1.33); N25 = 209063
PARES = [(0.85, 1.20), (0.80, 1.25), (0.90, 1.12)]
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(R / 'codigo/evaluar_final.py'))
P, y = g['P'], g['y']; mu0 = P['A1fixF1b3n'].values; f_tam = len(y) / N25
r5 = lambda v: round(float(v), 5)


def resolver(d0, pts):
    """d0: D² público de la base (c = 1); pts: [(c, D²)]. Devuelve c* (nan si no es identificable)."""
    X = np.array([[c ** -0.5 - 1, c ** 0.5 - 1] for c, _ in pts]); d = np.array([d0 - s for _, s in pts])
    a, b = np.linalg.solve(X, d)
    return float(a / b) if (a > 0 and b > 0) else float('nan')


def copt(yv, m):
    return (yv / np.sqrt(m)).sum() / np.sqrt(m).sum()


# 1. diseño: error por redondeo para cada par de escalas y ruido público→privado del óptimo
rng = np.random.default_rng(20261024); dis = {'filas_2024': int(len(y)), 'filas_2025': N25, 'pares': {}}
splits = [rng.random(len(y)) < 0.33 for _ in range(300)]
lp, lv = [], []
for pub in splits:
    lp.append(np.log(copt(y[pub], mu0[pub]))); lv.append(np.log(copt(y[~pub], mu0[~pub])))
lp, lv = np.array(lp), np.array(lv)
sig24 = float((lp - lv).std()); SIG = sig24 * np.sqrt(f_tam)
for par in PARES:
    err = []
    for pub, t in zip(splits, lp):
        d0 = r5(M.d2(y[pub], mu0[pub])); pts = [(c, r5(M.d2(y[pub], mu0[pub] * c))) for c in par]
        err.append(np.log(resolver(d0, pts)) - t)
    err = np.array(err)
    dis['pares'][f'{par[0]:.2f}-{par[1]:.2f}'] = {'error_redondeo_log_max': round(float(np.abs(err).max()), 5), 'error_redondeo_log_sd': round(float(err.std()), 5)}
ESC = PARES[0]
Z = TAU ** 2 / (TAU ** 2 + SIG ** 2)
c24 = copt(y, mu0); loss = {}
for r in (0.8, 0.9, 1.1, 1.2, 1.3):
    loss[str(r)] = round(float(M.d2(y, mu0 * c24) - M.d2(y, mu0 * c24 * r)), 5)
dis.update({'escalas_elegidas': ESC, 'c_optimo_2024_completo': round(float(c24), 4), 'sd_log_pub_menos_priv_2024': round(sig24, 4),
            'sigma_2025': round(float(SIG), 4), 'tau': TAU, 'Z': round(float(Z), 3), 'perdida_D2_por_error_de_nivel_2024': loss})
json.dump(dis, open(O / 'diseno.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(dis, ensure_ascii=False), flush=True)

# 2. remuestreo al tamaño de 2025: 2024 por componentes cliente-dirección con reemplazo hasta ~209.063 filas, y partición
#    al azar 33/67. Da σ al tamaño real (sin suponer la regla de la raíz) y el backtest de la regla completa en cuatro escenarios
#    fijos (nivel como salió en 2024, con óptimo 0,92; nivel correcto; ×1,3; ×0,8) y uno ponderado por la previa: en cada réplica
#    el error de nivel se sortea de N(0; τ²) alrededor del óptimo de 2024 (revisión independiente, 24-10).
comp = M.components(P.customer_id.values, P.address_id.values); K = comp.max() + 1
rows_by = pd.Series(np.arange(len(y))).groupby(comp).apply(np.array).values; n_comp = int(round(N25 / (len(y) / K)))
rng2 = np.random.default_rng(2026102403); REPS = []
for _ in range(200):
    ii = np.concatenate([rows_by[k] for k in rng2.integers(0, K, n_comp)]); REPS.append((ii, rng2.random(len(ii)) < 0.33))
lp25 = np.array([np.log(copt(y[ii][pub], mu0[ii][pub])) - np.log(copt(y[ii][~pub], mu0[ii][~pub])) for ii, pub in REPS])
SIG = float(lp25.std()); Z = TAU ** 2 / (TAU ** 2 + SIG ** 2)
dis.update({'sigma_2025_raiz': dis['sigma_2025'], 'sigma_2025': round(SIG, 4), 'Z': round(float(Z), 3),
            'sigma_nota': 'σ de 2025 medido por remuestreo de componentes al tamaño del test; sigma_2025_raiz es la escala por raíz del tamaño, solo de control.'})
json.dump(dis, open(O / 'diseno.json', 'w'), indent=1, ensure_ascii=False)
print('sigma remuestreo', round(SIG, 4), 'Z', round(Z, 3), flush=True)
bt = {}
for nombre, k in [('nivel_como_2024', 1.0), ('nivel_correcto', c24), ('nivel_x1.3', c24 * 1.3), ('nivel_x0.8', c24 * 0.8)]:
    mu = mu0 * k; gains = []; cfs = []
    for ii, pub in REPS:
        yy, mm = y[ii], mu[ii]; prv = ~pub; d0 = r5(M.d2(yy[pub], mm[pub]))
        cs = resolver(d0, [(c, r5(M.d2(yy[pub], mm[pub] * c))) for c in ESC])
        cf = float(np.clip(np.exp(Z * np.log(cs)), *COTAS)) if np.isfinite(cs) else 1.0
        cfs.append(cf); gains.append(M.d2(yy[prv], mm[prv] * cf) - M.d2(yy[prv], mm[prv]))
    gg = np.array(gains)
    bt[nombre] = {'c_optimo_completo_2024': round(float(copt(y, mu)), 4), 'c_final_mediana': round(float(np.median(cfs)), 4),
                  'c_final_p05_p95': [round(float(q), 4) for q in np.quantile(cfs, [0.05, 0.95])],
                  'ganancia_privado_media': round(float(gg.mean()), 5), 'p05_p50_p95': [round(float(q), 5) for q in np.quantile(gg, [0.05, 0.5, 0.95])],
                  'prob_ganar': round(float((gg > 0).mean()), 3)}
    print(nombre, bt[nombre], flush=True)
rng3 = np.random.default_rng(2026102404); gains = []; cfs = []
for ii, pub in REPS:
    mm = mu0[ii] * c24 * np.exp(rng3.normal(0, TAU)); yy = y[ii]; prv = ~pub; d0 = r5(M.d2(yy[pub], mm[pub]))
    cs = resolver(d0, [(c, r5(M.d2(yy[pub], mm[pub] * c))) for c in ESC])
    cf = float(np.clip(np.exp(Z * np.log(cs)), *COTAS)) if np.isfinite(cs) else 1.0
    cfs.append(cf); gains.append(M.d2(yy[prv], mm[prv] * cf) - M.d2(yy[prv], mm[prv]))
gg = np.array(gains)
bt['ponderado_por_la_previa'] = {'ganancia_privado_media': round(float(gg.mean()), 5), 'p05_p50_p95': [round(float(q), 5) for q in np.quantile(gg, [0.05, 0.5, 0.95])],
                                 'prob_ganar': round(float((gg > 0).mean()), 3)}
print('ponderado_por_la_previa', bt['ponderado_por_la_previa'], flush=True)
bt['nota'] = ('Tamaño 2025 por remuestreo de componentes de 2024 (200 réplicas); privado = 67 % de cada réplica. Los escenarios ×1,3 y ×0,8 '
              'son desvíos de unas dos τ; la cifra que resume la regla con la previa declarada es «ponderado_por_la_previa». El sustituto es '
              'A1fixF1b3n de 2024; la base enviada es la mezcla 50/50 con MLind (en 2025, +2,7 % de total y 5,8 % de cambio mediano por fila).')
json.dump(bt, open(O / 'backtest_2024.json', 'w'), indent=1, ensure_ascii=False)

# 3. archivos y preinscripción
b = pd.read_csv(BASE, dtype={'row_id': str}); files = {}
y23 = pd.read_parquet(R / 'salidas/s2/oof/A1fixF1b3_nivel.parquet').y.values.astype(float)
for c in ESC:
    d = b.copy(); d['prediction'] = b.prediction.values * c
    assert len(d) == N25 and np.isfinite(d.prediction).all() and (d.prediction > 0).all()
    p = O / f'sonda_global_{c:.2f}.csv'; d.to_csv(p, index=False, float_format='%.6f', lineterminator='\n')
    chk = pd.read_csv(p, dtype={'row_id': str})
    assert (chk.row_id.values == b.row_id.values).all() and np.allclose(chk.prediction.values, b.prediction.values * c, rtol=1e-6, atol=1e-6)
    files[p.name] = {'c': c, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'total': round(float(d.prediction.sum()), 2)}
pre = {
    'id': 'CLA-S2-SONDA-GLOBAL-20261024', 'autor': 'Claude (Cowork), sesión de validación nocturna',
    'pedido': 'El participante eligió «Sonda de nivel global» el 24-10 tras ver el tablero (séptimos de siete, 0,15390).',
    'base': {'archivo': 'Repositorio_IAA2026/privado/semana2/claude_ml_independiente_20261023/mezcla50_designada_mlind_2025.csv', 'sha256': SHA_BASE,
             'total': round(float(b.prediction.sum()), 2), 'd2_publico': 0.15390, 'envio_kaggle': 57599788},
    'sondas': files,
    'metodo': 'D2(1) − D2(c) = βA (c^-1/2 − 1) + βB (c^1/2 − 1); con las dos sondas se despejan βA y βB y c* = βA / βB, el óptimo exacto de la desviación Tweedie 1,5 en el público para un factor común a todas las filas.',
    'credibilidad': {'tau': TAU, 'tau_motivo': 'Salto global de nivel de 2023 a 2024 en el emergente (real/esperado 0,884, log −0,12); no incluye el cambio de cartera de 2025, que podría ampliarlo.',
                     'sigma_2025': round(float(SIG), 4), 'Z': round(float(Z), 3),
                     'nota_Z': 'σ es la desviación de log c*_público − log c*_privado. El predictor lineal óptimo del nivel privado solo necesita el error del público, algo menor, y daría Z ≈ 0,90 (pendiente empírica 0,908, revisión independiente). Se mantiene 0,854, más conservador; el efecto en la ganancia esperada es menor de 0,00001.'},
    'regla_final': f'c_final = exp(Z · log c*), acotado a [{COTAS[0]}; {COTAS[1]}]; archivo final = base × c_final en todas las filas. Si c* no es positivo y finito (βA o βB ≤ 0), no se aplica nada y se informa: el modelo de la fórmula no cuadraría con las puntuaciones.',
    'control': 'Si |log c*| > 0,4 (c* fuera de [0,67; 1,49]) el resolutor se detiene sin escribir el archivo final y se informa al participante: sería un desvío mayor que cualquiera visto entre años. Con dos ecuaciones y dos incógnitas no sobra ninguna para comprobar que la métrica de Kaggle es la supuesta; el único control directo son los signos de βA y βB. Como control indirecto, el resolutor informa la desviación nula por fila que implica βB (con Σμ^1/2 del público aproximada por un tercio de la del test) junto a la de 2023-2024.',
    'backtest_2024': bt,
    'nula_por_fila_referencia': {'2023': round(float(M.dev(y23, np.full_like(y23, y23.mean())).mean()), 2),
                                 '2024': round(float(M.dev(y, np.full_like(y, y.mean())).mean()), 2)},
    'coste': 'dos envíos para las sondas y uno para el archivo final, de los ocho que quedan; cierre el 30 de octubre a las 22:59 de Bogotá',
    'limites': 'Supone un público de un tercio elegido al azar por filas; σ medido con 2024 (59.202 filas) remuestreado por componentes al tamaño de 2025, sobre A1fixF1b3n como sustituto de la mezcla. Solo ajusta un nivel común, no el orden ni el reparto entre ramos. El envío lo hace Codex con autorización expresa del participante; la selección final es del participante.'}
json.dump(pre, open(O / 'preinscripcion.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(pre, indent=1, ensure_ascii=False))
