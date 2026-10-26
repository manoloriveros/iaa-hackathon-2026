"""Post-mortem de la parte 1 con los privados revelados (Claude, 25-oct-2026).

Lee la consulta viva de Kaggle que Codex guardo el 23-oct y calcula:
1) correlacion de rangos de V24 local y del publico frente al privado (candidatos de estructura);
2) optimo de nivel por ramo en el publico y en el privado con la forma cerrada de D100
   (D2(c) - D2(1) = -A (c^-1/2 - 1) - B (c^1/2 - 1)), usando las sondas S40 (x0,90 y x1,10 sobre S30);
3) el privado que habrian dado S41, S42, el optimo publico pleno y el optimo privado.
Solo biblioteca estandar. No envia nada ni lee etiquetas.
"""
import json, math, hashlib, pathlib, datetime
RAIZ = next(d for d in pathlib.Path(__file__).resolve().parents if (d / 'RUTAS_PROYECTO.json').exists())
F = RAIZ / 'Hackaton/Repositorio_IAA2026/privado/resultados_privados_parte1_20261023/consulta_viva_envios.json'
filas = {r['file_name']: r for r in json.load(open(F, encoding='utf-8'))['rows']}
sc = lambda n, k: float(filas[n][k])
# V24 local de CLAUDE.md seccion 13 (tabla de envios)
V24 = {'S07_D75_mezcla_desarrollo_train_ultimo.csv': 0.13173, 'S08_D76_CatBoost_stacking_calibrado_ultimo.csv': 0.13247,
       'S09b_claude_mezcla_hogar_F3s2.csv': 0.13552, 'N01_A_G_meta_GAM_ultimo.csv': 0.13610, 'N01_B_motor_Poisson_F3_ultimo.csv': 0.13703,
       'N01_G_frecuencia_EBM_ultimo.csv': 0.13751, 'N01_H_meta_geometrico_ultimo.csv': 0.13726, 'S21_riesgo_integral_ultimo.csv': 0.13807,
       'S22_riesgo_ultimo.csv': 0.13774, 'S30_riesgo_ultimo.csv': 0.13788}
def rangos(a):
    return [sorted(a).index(v) + 1 for v in a]
def spearman(a, b):
    ra, rb, n = rangos(a), rangos(b), len(a)
    return 1 - 6 * sum((x - y) ** 2 for x, y in zip(ra, rb)) / (n * (n * n - 1))
def corr(nombres):
    v = [V24[n] for n in nombres]; p = [sc(n, 'public_score') for n in nombres]; q = [sc(n, 'private_score') for n in nombres]
    return {'n': len(nombres), 'v24_privado': round(spearman(v, q), 4), 'publico_privado': round(spearman(p, q), 4)}
todos = list(V24); top8 = [n for n in todos if sc(n, 'private_score') > 0.135]
u = lambda c: c ** -0.5 - 1; w = lambda c: c ** 0.5 - 1
def AB(base, d09, d11):
    a11, a12, a21, a22 = -u(0.9), -w(0.9), -u(1.1), -w(1.1); y1, y2 = d09 - base, d11 - base
    det = a11 * a22 - a12 * a21
    return ((y1 * a22 - a12 * y2) / det, (a11 * y2 - y1 * a21) / det)
sondas = {'motor': ('S40_01_riesgo_ultimo.csv', 'S40_02_riesgo_ultimo.csv'), 'buildings': ('S40_03_riesgo_ultimo.csv', 'S40_04_riesgo_ultimo.csv'), 'contents': ('S40_05_riesgo_ultimo.csv', 'S40_06_riesgo_ultimo.csv')}
base = 'S30_riesgo_ultimo.csv'; res = {}
for parte, k in (('publico', 'public_score'), ('privado', 'private_score')):
    res[parte] = {}
    for ramo, (a, b) in sondas.items():
        A, B = AB(sc(base, k), sc(a, k), sc(b, k)); res[parte][ramo] = {'A': A, 'B': B, 'c_opt': A / B}
def score(parte, k, f):
    return sc(base, k) + sum(-res[parte][r]['A'] * u(f[r]) - res[parte][r]['B'] * w(f[r]) for r in f)
casos = {'S41': {'motor': 0.9962, 'buildings': 1.0260, 'contents': 1.0126}, 'S42': {'motor': 0.9838, 'buildings': 1.0413, 'contents': 1.0579},
         'optimo_publico_pleno': {r: res['publico'][r]['c_opt'] for r in sondas}, 'optimo_privado': {r: res['privado'][r]['c_opt'] for r in sondas}}
sigma_no_vista = {'motor': 0.034 * 1.49, 'buildings': 0.048 * 1.49, 'contents': 0.036 * 1.49}  # D100 x correccion D103 (L03)
salida = {
 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'autor': 'Claude (sesion de consolidacion)',
 'fuente': str(F.relative_to(RAIZ)), 'sha256_fuente': hashlib.sha256(F.read_bytes()).hexdigest(),
 'correlacion_rangos': {'diez_candidatos': corr(todos), 'ocho_mejores': corr(top8)},
 'nivel_por_ramo': {r: {'c_opt_publico': round(res['publico'][r]['c_opt'], 4), 'c_opt_privado': round(res['privado'][r]['c_opt'], 4),
                        'desvio_en_sigmas': round(abs(math.log(res['publico'][r]['c_opt'] / res['privado'][r]['c_opt'])) / sigma_no_vista[r], 2)} for r in sondas},
 'privado_previsto': {n: round(score('privado', 'private_score', f), 5) for n, f in casos.items()},
 'privado_observado': {'S41': sc('S41_riesgo_ultimo.csv', 'private_score'), 'S42': sc('S42_riesgo_ultimo.csv', 'private_score')},
 'limites': ['Scores a cinco decimales; el redondeo mueve c_opt privado menos de 0,002.', 'Una sola realizacion del privado.', 'V24 tomado de CLAUDE.md seccion 13.']}
json.dump(salida, open(pathlib.Path(__file__).with_name('postmortem_parte1.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(salida, ensure_ascii=False, indent=1))
