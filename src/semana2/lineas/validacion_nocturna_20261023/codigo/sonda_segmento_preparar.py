"""Sonda de nivel por ramo × nuevo negocio: archivos y preinscripción (sin enviar nada).

Segmentación elegida con la simulación de sonda_segmento_diseno.py (salidas/sonda_segmento/diseno.json): seis celdas
(autos, edificios y contenidos, cada uno en nuevo negocio y renovación). Base: el archivo final de la sonda global,
F = mezcla × g (final_sonda_global_2025.csv, SHA 42659dbb…; g = 1,187658238648521). Cinco sondas: F con una sola celda
multiplicada por K = 1,2; la celda mayor (autos, nuevo negocio) se deduce de βA − Σ a_s. Se fija aquí, antes de ver
ninguna puntuación de F ni de las sondas: Z por celda (τ = 0,20 y σ de la simulación), cotas y paradas.
Escribe salidas/sonda_segmento/sonda_seg_{celda}.csv y salidas/sonda_segmento/preinscripcion.json.
"""
import hashlib, json, pathlib
import numpy as np, pandas as pd

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/sonda_segmento'
LINES = ['motor', 'buildings', 'contents']; PFX = {'M': 'motor', 'B': 'buildings', 'C': 'contents'}
dis = json.load(open(O / 'diseno.json')); glob = json.load(open(R / 'salidas/sonda_global/resultado.json'))
K = dis['K']; G = glob['c_final_exacto']
# Revisión independiente (25-10): σ de las celdas de nuevo negocio descansa en pocos datos; Z usa el mayor σ de los dos años
SPP = json.load(open(O / 'sigma_por_pool.json')); SIG = SPP['sigma_max']; SIG_POOL = dis['sigma']['ramo_nb']
Z = {s: round(dis['tau'] ** 2 / (dis['tau'] ** 2 + v ** 2), 3) for s, v in SIG.items()}
# intervalo de D2(F) que admite el redondeo de las tres puntuaciones globales
import itertools
Xg = np.array([[c ** -0.5 - 1, c ** 0.5 - 1] for c in (0.85, 1.2)]); _dF = []
for e0, e1, e2 in itertools.product([-5e-6, 5e-6], repeat=3):
    _a, _b = np.linalg.solve(Xg, np.array([0.15390 + e0 - 0.14095 - e1, 0.15390 + e0 - 0.15955 - e2]))
    _dF.append(0.15390 + e0 - (_a * (G ** -0.5 - 1) + _b * (G ** 0.5 - 1)))
DF_INT = [round(float(min(_dF)), 7), round(float(max(_dF)), 7)]
BASE = R / 'datos/mlind/mezcla50_designada_mlind_2025.csv'; FIN = R / 'salidas/sonda_global/final_sonda_global_2025.csv'
assert hashlib.sha256(FIN.read_bytes()).hexdigest() == glob['final']['sha256']
mu = pd.read_csv(BASE, dtype={'row_id': str}); F = pd.read_csv(FIN, dtype={'row_id': str})
assert (mu.row_id.values == F.row_id.values).all()
nb = pd.concat([pd.read_parquet(R / f'salidas/s2/base_{l}.parquet', columns=['row_id', 'split', 'new_business']).query("split == 'test'") for l in LINES]).set_index('row_id').new_business
celda = np.char.add(np.char.add(F.row_id.str[0].map(PFX).values.astype(str), '_'), nb.loc[F.row_id].values.astype(int).astype(str))
T = pd.Series(np.sqrt(mu.prediction.values)).groupby(celda).sum(); cuota = (T / T.sum()).to_dict()
orden = sorted(cuota, key=cuota.get); deducida = orden[-1]; sondeadas = orden[:-1]
files = {}
for s in sondeadas:
    d = F.copy(); m = celda == s; d.loc[m, 'prediction'] = F.prediction.values[m] * K
    assert len(d) == 209063 and np.isfinite(d.prediction).all() and (d.prediction > 0).all()
    p = O / f'sonda_seg_{s}.csv'; d.to_csv(p, index=False, float_format='%.6f', lineterminator='\n')
    chk = pd.read_csv(p, dtype={'row_id': str}); assert (chk.row_id.values == F.row_id.values).all()
    assert np.allclose(chk.prediction.values[m], F.prediction.values[m] * K, atol=1e-6) and np.array_equal(chk.prediction.values[~m], F.prediction.values[~m])
    files[p.name] = {'celda': s, 'K': K, 'filas_escaladas': int(m.sum()), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'total': round(float(d.prediction.sum()), 2)}
    print(p.name, files[p.name], flush=True)
g = dis['ganancia']['ramo_nb']
pre = {
    'id': 'CLA-S2-SONDA-SEGMENTO-20261025', 'autor': 'Claude (Cowork), sesión de validación nocturna',
    'pedido': 'El participante eligió «Final + diseñar sonda por segmento» el 25-10 tras la sonda global.',
    'base': {'archivo': 'Repositorio_IAA2026/privado/semana2/claude_validacion_nocturna_20261023/sonda_global/final_sonda_global_2025.csv',
             'sha256': glob['final']['sha256'], 'g': G, 'd2_publico_previsto': glob['d2_publico_previsto_final'],
             'mezcla': {'sha256': '12831ef4a05c1773824abe5fa139d9503dd2989b4874e7d93cfc000406cfdb4a', 'd2_publico': 0.15390},
             'beta_A': glob['beta_A'], 'beta_B': glob['beta_B'], 'c_optimo_global': glob['c_optimo_publico_exacto']},
    'celdas': {s: {'cuota_raiz_mu': round(cuota[s], 6), 'filas': int((celda == s).sum()), 'Z': Z[s], 'sigma': SIG[s], 'sigma_agrupado_simulacion': SIG_POOL[s]} for s in orden},
    'd2_F_intervalo_redondeo': DF_INT,
    'celda_deducida': deducida, 'sondas': files,
    'metodo': ('b_s = βB × cuota_s (Σμ^½ de la celda en el test); a_s = [D2(F) − D2(sonda_s) − b_s((gK)^½ − g^½)] / ((gK)^−½ − g^−½) para las cinco '
               'celdas sondeadas, y a_deducida = βA − Σ a_s. c*_s = a_s / b_s. Factor final por celda: g × acotar((c*_s / c*_g)^Z_s, 0,75, 1,33). '
               'Archivo final = mezcla × factor de su celda.'),
    'credibilidad': {'tau': dis['tau'], 'tau_motivo': ('Desviación logarítmica de cada celda frente al nivel global: en 2024, con el nivel de 2023, los ramos '
                     'se desviaron +0,22, −0,36 y +0,08 del global (RMS 0,25), y el cociente nuevo negocio / renovación osciló entre 0,79 y 1,70 por ramo y año.'),
                     'sigma': 'desviación típica de log(c*_s/c*_g) público menos privado, remuestreo de 2023 y 2024 al tamaño y composición de 2025 (150 réplicas por año)'},
    'orden_de_envio': 'Primero F solo; si su D2 público es compatible con el intervalo de redondeo, después las cinco sondas. Así una parada en F no gasta las sondas.',
    'entrada_de_puntuaciones': 'Por nombre de archivo (o por recibo con SHA-256), nunca por nombre de celda, para que una puntuación no se asigne a la celda equivocada.',
    'paradas': ['Si el intervalo [D2(F) observado ± 0,000005] no toca el intervalo previsto por el redondeo de las puntuaciones globales, no se resuelve: la métrica no tendría la forma supuesta.',
                'Si a_s o b_s ≤ 0 en alguna celda, no se resuelve: el modelo implica a_s > 0, así que un valor no positivo indica un supuesto roto (público no aleatorio u otra métrica).',
                'Si |log(c*_s / c*_g)| > max(0,7; 3 σ_s) en alguna celda, el resolutor se detiene sin escribir el archivo final y se consulta al participante.'],
    'nota_Z': 'Z usa el mayor σ de los dos años de la simulación (sigma_por_pool.json), más conservador que el σ agrupado con que se simularon las ganancias de diseno.json.',
    'nota_previa': 'El escenario «previa» sortea seis desviaciones independientes con el mismo τ que fija Z; por construcción favorece a las segmentaciones con más celdas.',
    'simulacion_privado': {'nulo_2024': g['2024_nulo'], 'nulo_2023': g['2023_nulo'], 'previa_2024': g['2024_previa'], 'previa_2023': g['2023_previa'],
                           'como_2024': g['2024_como_el_año'], 'como_2023': g['2023_como_el_año']},
    'alternativas_simuladas': {k: {e: dis['ganancia'][k][e]['media'] for e in dis['ganancia'][k]} for k in ('nb', 'ramo')},
    'coste': 'el archivo final global, cinco sondas y el archivo final por celda: siete envíos; quedan ocho hoy y diez por día hasta el 30 de octubre',
    'limites': ('Supone un público de un tercio al azar por filas; b_s aproximado por cuotas del test; σ medido con 2023 y 2024 remuestreados (el nuevo negocio '
                'de esos años tiene pocos siniestros grandes). Solo ajusta un nivel por celda, no el orden dentro de la celda. El envío lo hace Codex con autorización '
                'expresa del participante; la selección final es del participante.')}
json.dump(pre, open(O / 'preinscripcion.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps({k: pre[k] for k in ('celdas', 'celda_deducida')}, indent=1, ensure_ascii=False))
