"""Resuelve la sonda por ramo × nuevo negocio con las puntuaciones públicas y construye el archivo final (preinscripción
salidas/sonda_segmento/preinscripcion.json).

Uso: python sonda_segmento_resolver.py final_sonda_global_2025.csv=D2 sonda_seg_contents_0.csv=D2 ... (las cinco sondas) [--forzar]
     python sonda_segmento_resolver.py --recibos recibos.json   (lista de {"sha256": ..., "d2": ...} tal como los registre Codex)
     Las puntuaciones entran por nombre de archivo o por SHA-256, nunca por nombre de celda.
     python sonda_segmento_resolver.py --prueba   (simula con 2024 todas las puntuaciones, incluida la global, y compara c*_s
                                                 con el óptimo verdadero del público simulado; no escribe nada propio;
                                                 evaluar_final.py reescribe sus salidas con el mismo contenido)
Paradas preinscritas (revisadas tras la revisión independiente del 25-10): D2(F) ± 0,000005 fuera del intervalo previsto por el
redondeo global, o a_s / b_s ≤ 0 en alguna celda (no se resuelve), y |log(c*_s / c*_g)| > max(0,7; 3 σ_s) (no se escribe el
final), salvo --forzar, que solo se usa con decisión del participante.
Escribe salidas/sonda_segmento/resultado.json y salidas/sonda_segmento/final_sonda_segmento_2025.csv.
"""
import hashlib, json, pathlib, sys
import numpy as np, pandas as pd

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/sonda_segmento'
pre = json.load(open(O / 'preinscripcion.json')); B = pre['base']; CEL = pre['celdas']; DED = pre['celda_deducida']
LO, HI = 0.75, 1.33; K = 1.2; PFX = {'M': 'motor', 'B': 'buildings', 'C': 'contents'}
PRUEBA = '--prueba' in sys.argv; FORZAR = '--forzar' in sys.argv
FILES = {'final_sonda_global_2025.csv': ('F', B['sha256'])}
FILES.update({fn: (v['celda'], v['sha256']) for fn, v in pre['sondas'].items()})
SHA2F = {sha: fn for fn, (_, sha) in FILES.items()}
args = {}
for a in sys.argv[1:]:
    if '=' in a:
        k, v = a.split('=', 1); assert k in FILES, f'{k} no es un archivo de la preinscripción'
        args[FILES[k][0]] = float(v)
if '--recibos' in sys.argv:
    for r_ in json.load(open(sys.argv[sys.argv.index('--recibos') + 1])):
        assert r_['sha256'] in SHA2F, f"SHA {r_['sha256'][:12]} no es de la preinscripción"
        args[FILES[SHA2F[r_['sha256']]][0]] = float(r_['d2'])
bA, bB, g, cg, cuota = B['beta_A'], B['beta_B'], B['g'], B['c_optimo_global'], {s: v['cuota_raiz_mu'] for s, v in CEL.items()}
dF_prev = B['d2_publico_previsto']; DF_INT = pre['d2_F_intervalo_redondeo']; SIGC = {s: v['sigma'] for s, v in CEL.items()}
if PRUEBA:
    import io, contextlib, runpy
    sys.path.insert(0, str(R / 'codigo')); import marco as M
    with contextlib.redirect_stdout(io.StringIO()):
        gg_ = runpy.run_path(str(R / 'codigo/evaluar_final.py'))
    P = gg_['P']; y = np.asarray(gg_['y'], float); mu = P['A1fixF1b3n'].values
    nbv = pd.concat([pd.read_parquet(R / f'salidas/s2/base_{l}.parquet', columns=['row_id', 'new_business']) for l in PFX.values()]).set_index('row_id').new_business
    celda = np.char.add(np.char.add(P.line.values.astype(str), '_'), nbv.loc[P.index].values.astype(int).astype(str))
    pub = np.random.default_rng(9).random(len(y)) < 0.33; r5 = lambda v: round(float(v), 5)
    d0 = r5(M.d2(y[pub], mu[pub])); X = np.array([[c ** -0.5 - 1, c ** 0.5 - 1] for c in (0.85, 1.2)])
    bA, bB = np.linalg.solve(X, np.array([d0 - r5(M.d2(y[pub], mu[pub] * c)) for c in (0.85, 1.2)])); cg = bA / bB
    g = float(np.clip(np.exp(0.854 * np.log(cg)), 0.75, 1.33)); dF_prev = d0 - (bA * (g ** -0.5 - 1) + bB * (g ** 0.5 - 1)); DF_INT = [dF_prev - 2e-5, dF_prev + 2e-5]
    T = pd.Series(np.sqrt(mu)).groupby(celda).sum(); cuota = (T / T.sum()).to_dict()
    args = {'F': r5(M.d2(y[pub], mu[pub] * g))}
    for s in CEL:
        if s != DED: args[s] = r5(M.d2(y[pub], mu[pub] * g * np.where(celda[pub] == s, K, 1.0)))
    verdad = {s: float((y[pub & (celda == s)] / np.sqrt(mu[pub & (celda == s)])).sum() / np.sqrt(mu[pub & (celda == s)]).sum()) for s in CEL}
need = ['F'] + [s for s in CEL if s != DED]
assert sorted(args) == sorted(need), f'faltan puntuaciones: {sorted(set(need) - set(args))}'
dF = args['F']
res = {'d2_F_observado': dF, 'd2_F_previsto': round(float(dF_prev), 5), 'd2_sondas': {s: args[s] for s in need[1:]}}
res['d2_F_intervalo_previsto'] = DF_INT
if (dF + 5e-6 < DF_INT[0] - 1e-9 or dF - 5e-6 > DF_INT[1] + 1e-9) and not PRUEBA:
    res['parada'] = 'D2(F) no es compatible con el intervalo previsto por el redondeo: la métrica no tendría la forma supuesta. No se resuelve.'
    json.dump(res, open(O / 'resultado.json', 'w'), indent=1, ensure_ascii=False); print(json.dumps(res, indent=1, ensure_ascii=False)); sys.exit(2)
b_s = {s: bB * cuota[s] for s in CEL}; a_s = {}
for s in need[1:]:
    a_s[s] = (dF - args[s] - b_s[s] * ((g * K) ** 0.5 - g ** 0.5)) / ((g * K) ** -0.5 - g ** -0.5)
a_s[DED] = bA - sum(a_s.values())
noneg = [s for s in CEL if not (a_s[s] > 0 and b_s[s] > 0)]
if noneg:
    res.update({'a_s': a_s, 'b_s': b_s, 'parada': f'a_s o b_s no positivo en {noneg}: supuesto roto (público no aleatorio u otra métrica). No se resuelve.'})
    if not PRUEBA: json.dump(res, open(O / 'resultado.json', 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False)); sys.exit(2)
cstar, fac, grande = {}, {}, []
for s in CEL:
    cstar[s] = a_s[s] / b_s[s]; rel = cstar[s] / cg
    if abs(np.log(rel)) > max(0.7, 3 * SIGC[s]): grande.append(s)
    fac[s] = g * float(np.clip(rel ** CEL[s]['Z'], LO, HI))
prev = dF - sum(a_s[s] * (fac[s] ** -0.5 - g ** -0.5) + b_s[s] * (fac[s] ** 0.5 - g ** 0.5) for s in CEL)
res.update({'a_s': a_s, 'b_s': b_s, 'c_optimo_publico': {s: round(v, 4) for s, v in cstar.items()},
            'relativo_al_global': {s: round(v / cg, 4) for s, v in cstar.items()},
            'factor_final': {s: round(v, 4) for s, v in fac.items()}, 'factor_final_exacto': fac, 'parada_log_mayor_0_7': grande,
            'd2_publico_previsto_final': round(float(prev), 5)})
if PRUEBA:
    res['prueba'] = {'c_optimo_verdadero': {s: round(v, 4) for s, v in verdad.items()},
                     'error_log': {s: round(float(np.log(cstar[s] / verdad[s])), 4) for s in CEL},
                     'd2_real_final': r5(M.d2(y[pub], mu[pub] * np.array([fac[c] for c in celda])[pub]))}
    print(json.dumps(res, indent=1, ensure_ascii=False)); sys.exit(0)
json.dump(res, open(O / 'resultado.json', 'w'), indent=1, ensure_ascii=False)
if grande and not FORZAR:
    print(json.dumps(res, indent=1, ensure_ascii=False)); print('PARADA PREINSCRITA: |log(c*_s/c*_g)| > max(0,7; 3σ) en', grande); sys.exit(2)
BASE = R / 'datos/mlind/mezcla50_designada_mlind_2025.csv'
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == B['mezcla']['sha256']
mz = pd.read_csv(BASE, dtype={'row_id': str})
nb = pd.concat([pd.read_parquet(R / f'salidas/s2/base_{l}.parquet', columns=['row_id', 'split', 'new_business']).query("split == 'test'") for l in PFX.values()]).set_index('row_id').new_business
celda = np.char.add(np.char.add(mz.row_id.str[0].map(PFX).values.astype(str), '_'), nb.loc[mz.row_id].values.astype(int).astype(str))
out = mz.copy(); out['prediction'] = mz.prediction.values * np.array([fac[c] for c in celda])
assert len(out) == 209063 and np.isfinite(out.prediction).all() and (out.prediction > 0).all()
p = O / 'final_sonda_segmento_2025.csv'; out.to_csv(p, index=False, float_format='%.6f', lineterminator='\n')
res['final'] = {'archivo': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'total': round(float(out.prediction.sum()), 2),
                'por_celda': {s: round(float(out.prediction.values[celda == s].sum()), 2) for s in CEL}, 'forzado': FORZAR}
json.dump(res, open(O / 'resultado.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
