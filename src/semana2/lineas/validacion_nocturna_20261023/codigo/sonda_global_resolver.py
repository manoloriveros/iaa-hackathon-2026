"""Resuelve la sonda de nivel global con las dos puntuaciones públicas y construye el archivo final según la preinscripción.

Uso: python sonda_global_resolver.py 0.85=D2 1.20=D2 [--forzar]
     python sonda_global_resolver.py --prueba   (simula las puntuaciones con 2024 y comprueba que se recupera el óptimo; no
                                                 escribe resultado ni archivo final; evaluar_final.py, que se ejecuta para tener
                                                 2024, reescribe sus propias salidas con el mismo contenido)
Paradas preinscritas: si c* no es positivo y finito, o si |log c*| > 0,4, sale con código 2 sin escribir el archivo final
(--forzar lo escribe igualmente; solo con decisión del participante).
Escribe salidas/sonda_global/resultado.json y salidas/sonda_global/final_sonda_global_2025.csv.
"""
import hashlib, json, pathlib, sys
import numpy as np, pandas as pd

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/sonda_global'
pre = json.load(open(O / 'preinscripcion.json')); D0 = pre['base']['d2_publico']; Z = pre['credibilidad']['Z']
LO, HI = 0.75, 1.33; N25 = 209063
BASE = R / 'datos/mlind/mezcla50_designada_mlind_2025.csv'
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == pre['base']['sha256']
base = pd.read_csv(BASE, dtype={'row_id': str}); S_all = float(np.sqrt(base.prediction.values).sum())
args = {float(k): float(v) for k, v in (a.split('=') for a in sys.argv[1:] if '=' in a)}
PRUEBA = '--prueba' in sys.argv
if PRUEBA:
    import io, contextlib, runpy
    sys.path.insert(0, str(R / 'codigo')); import marco as M
    with contextlib.redirect_stdout(io.StringIO()):
        g = runpy.run_path(str(R / 'codigo/evaluar_final.py'))
    y = g['y']; mu = g['P']['A1fixF1b3n'].values; pub = np.random.default_rng(5).random(len(y)) < 0.33
    D0 = round(float(M.d2(y[pub], mu[pub])), 5)
    args = {v['c']: round(float(M.d2(y[pub], mu[pub] * v['c'])), 5) for v in pre['sondas'].values()}
    verdad = float((y[pub] / np.sqrt(mu[pub])).sum() / np.sqrt(mu[pub]).sum())
    S_all, n_all = float(np.sqrt(mu).sum()), len(y)
else:
    n_all = N25
assert sorted(args) == sorted(v['c'] for v in pre['sondas'].values()), 'faltan puntuaciones de sonda'
X = np.array([[c ** -0.5 - 1, c ** 0.5 - 1] for c in sorted(args)]); d = np.array([D0 - args[c] for c in sorted(args)])
bA, bB = np.linalg.solve(X, d)
ok = bool(bA > 0 and bB > 0)
cstar = float(bA / bB) if ok else None
grande = bool(ok and abs(np.log(cstar)) > 0.4)
cfin = float(np.clip(np.exp(Z * np.log(cstar)), LO, HI)) if ok else 1.0
prev = lambda c: D0 - (bA * (c ** -0.5 - 1) + bB * (c ** 0.5 - 1))
res = {'d2_base': D0, 'd2_sondas': {str(k): v for k, v in args.items()}, 'beta_A': float(bA), 'beta_B': float(bB),
       'identificable': ok, 'c_optimo_publico': round(cstar, 4) if ok else None, 'parada_log_mayor_0_4': grande,
       'Z': Z, 'c_final': round(cfin, 4), 'd2_publico_previsto_en_c_optimo': round(float(prev(cstar)), 5) if ok else None,
       'd2_publico_previsto_final': round(float(prev(cfin)), 5),
       # control indirecto: βB = 4 B / nula, con B ≈ Σμ^1/2 del público ≈ un tercio de la del conjunto
       'nula_por_fila_implicita': round(float(4 * S_all / (bB * n_all)), 2) if bB > 0 else None,
       'nula_por_fila_referencia': pre.get('nula_por_fila_referencia')}
if PRUEBA:
    res['prueba'] = {'c_optimo_verdadero_publico_simulado': round(verdad, 4), 'error_log': round(float(np.log(cstar) - np.log(verdad)), 5) if ok else None,
                     'd2_real_en_c_final': round(float(M.d2(y[pub], mu[pub] * cfin)), 5),
                     'nula_por_fila_real_publico': round(float(M.dev(y[pub], np.full(pub.sum(), y[pub].mean())).mean()), 2)}
    print(json.dumps(res, indent=1, ensure_ascii=False)); sys.exit(0)
json.dump(res, open(O / 'resultado.json', 'w'), indent=1, ensure_ascii=False)
if (not ok or grande) and '--forzar' not in sys.argv:
    print(json.dumps(res, indent=1, ensure_ascii=False))
    print('PARADA PREINSCRITA: c* no identificable o |log c*| > 0,4. No se escribe el archivo final; informar al participante.')
    sys.exit(2)
out = base.copy(); out['prediction'] = base.prediction.values * cfin
assert len(out) == N25 and np.isfinite(out.prediction).all() and (out.prediction > 0).all()
p = O / 'final_sonda_global_2025.csv'; out.to_csv(p, index=False, float_format='%.6f', lineterminator='\n')
res['final'] = {'archivo': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'total': round(float(out.prediction.sum()), 2),
                'forzado': '--forzar' in sys.argv}
json.dump(res, open(O / 'resultado.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
