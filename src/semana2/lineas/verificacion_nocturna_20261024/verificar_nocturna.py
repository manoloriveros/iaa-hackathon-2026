"""Verificación independiente de la tanda nocturna de Codex (solo 2023): recetas estándar B12–B18, cola, reservas y C0.

Claude (Cowork), 24 de octubre de 2026. Lee las corridas congeladas de Codex (OOF, informes, planes) después de comprobar
sus huellas frente a los manifiestos, recalcula con código propio lo que Codex publicó en el foro (COD-S2-20261023-017,
COD-S2-20261024-019, 021, 024 y 026) y en sus report.json, y deja la evidencia en evidencia_nocturna.json y
tablas/*.csv. No ajusta precios nuevos: la única estimación es el replay de B13/B14 (GLM Tweedie sin penalización con
la receta declarada) para comprobar que los OOF guardados son lo que dicen ser. No toca 2024 ni el test.

Controles VN01–VN17 (tanda 016–027), VN18–VN21 (ampliación a 028–033: mezcla de C0, escasez, coberturas y soporte de calendario) y VN22–VN29 (ampliación a 035–039: B19 con coberturas,
B20 ridge, estabilidad e influencia de B19 y trazabilidad de sus siniestros; incluye el replay de 45 GLM y la aproximación local H⁻¹G_g) y VN30–VN37 (ampliación a B20-ATTR, 040–044, B20-BANDS y B20-SYNTH:
atribución de la ganancia de B20 por grupos y segmentos, contracción y nivel, bandas de calibración, incendio y AD, síntesis). Resultados: pasa, hallazgo (con severidad), limite, informativo.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import pathlib
import sys
import time

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

AQUI = pathlib.Path(__file__).resolve().parent
LINES = ['motor', 'buildings', 'contents']
KEY = ['market', 'line', 'row_id']
RUNS = {'dev5': 'dev5_20261023T232328Z_69df9ead', 'dev6': 'dev6_20261023T234239Z_fdab9f0b', 'dev7': 'dev7_20261023T235935Z_55507793',
        'cola': 'cola_20261024T001114Z_e5d1c211', 'mecanismo': 'mecanismo_20261024T002849Z_c8f124bf',
        'mezcla': 'mezcla_20261024T004833Z_e8ff18e0', 'soporte': 'soporte_20261024T010555Z_c4428b52', 'coberturas': 'coberturas_20261024T011932Z_14b50ca9'}
AMPLIACION = ['mezcla', 'soporte', 'coberturas']  # unidades 028–033, añadidas en la ampliación del 24 de octubre
SEED, REPS = 2026102302, 2000

# Lo que Codex publicó en el foro (fuente: FORO.md, aportes citados). Se compara a la precisión impresa.
PUBLICADO = {
    'COD-S2-20261023-017': {
        'tabla': {'W2-B00': dict(D2=0.06858, pred_M=15.614, AE=0.980, D2_nb=0.04783, AE_nb=1.550),
                  'W2-B08': dict(D2=0.09318, pred_M=15.599, AE=0.981, D2_nb=0.07297, AE_nb=1.182),
                  'W2-B12': dict(D2=0.07492, pred_M=15.367, AE=0.995, D2_nb=0.09220, AE_nb=0.906),
                  'W2-B13': dict(D2=0.08671, pred_M=15.430, AE=0.991, D2_nb=0.11119, AE_nb=0.906)},
        'observado_M': 15.297, 'observado_nb_M': 1.528,
        'pares': {('W2-B12', 'W2-B00'): (0.00633, -0.00205, 0.01843, -0.00739), ('W2-B13', 'W2-B00'): (0.01813, -0.00620, 0.04266, -0.01251),
                  ('W2-B13', 'W2-B08'): (-0.00647, -0.02446, 0.01289, -0.02798), ('W2-B13', 'W2-B12'): (0.01180, -0.00970, 0.03170, -0.01286)},
        'segmentos': {('W2-B13', 'buildings', 'nb', 'D2'): 0.05022, ('W2-B00', 'buildings', 'nb', 'D2'): 0.06523, ('W2-B12', 'buildings', 'nb', 'D2'): 0.03542,
                      ('W2-B13', 'buildings', 'all', 'AE'): 1.0005, ('W2-B13', 'motor', 'nb', 'D2'): -0.01004, ('W2-B13', 'motor', 'nb', 'AE'): 0.879,
                      ('W2-B13', 'contents', 'nb', 'D2'): 0.15363, ('W2-B13', 'contents', 'nb', 'AE'): 1.184}},
    'COD-S2-20261024-019': {
        'tabla': {'W2-B00': dict(D2=0.068582, pred_M=15.614, AE=0.980, D2_nb=0.04783, AE_nb=1.550),
                  'W2-B13': dict(D2=0.086712, pred_M=15.430, AE=0.991, D2_nb=0.11119, AE_nb=0.906),
                  'W2-B14': dict(D2=0.086710, pred_M=15.430, AE=0.991, D2_nb=0.11117, AE_nb=0.906),
                  'W2-B15': dict(D2=0.086061, pred_M=15.088, AE=1.014, D2_nb=0.10547, AE_nb=1.136)},
        'pares': {('W2-B14', 'W2-B00'): (0.01812839, -0.00622581, 0.04266535, -0.01250214), ('W2-B15', 'W2-B00'): (0.01747930, -0.00562290, 0.03989653, -0.01078480),
                  ('W2-B14', 'W2-B13'): (-0.00000163, -0.00003090, 0.00002893, -0.00005245), ('W2-B15', 'W2-B14'): (-0.00064909, -0.00500418, 0.00263310, -0.00230283)},
        'segmentos': {('W2-B14', 'motor', 'nb', 'AE'): 0.879, ('W2-B15', 'motor', 'nb', 'AE'): 1.223, ('W2-B14', 'motor', 'nb', 'D2'): -0.01004, ('W2-B15', 'motor', 'nb', 'D2'): -0.03324,
                      ('W2-B14', 'contents', 'nb', 'AE'): 1.184, ('W2-B15', 'contents', 'nb', 'AE'): 1.052, ('W2-B14', 'contents', 'nb', 'D2'): 0.15358, ('W2-B15', 'contents', 'nb', 'D2'): 0.17445},
        'capital_56': dict(buildings=26, contents=30, cambio_min=-0.6236, cambio_max=1.5409)},
    'COD-S2-20261024-021': {
        'tabla_autos_nb': {'W2-B00': dict(D2=0.068582, AE=0.980, D2_mnb=-0.130134, AE_mnb=2.006, pred_mnb_M=0.543),
                           'W2-B14': dict(D2=0.086710, AE=0.991, D2_mnb=-0.010045, AE_mnb=0.879, pred_mnb_M=1.238),
                           'W2-B15': dict(D2=0.086061, AE=1.014, D2_mnb=-0.033244, AE_mnb=1.223, pred_mnb_M=0.890),
                           'W2-B16': dict(D2=0.086551, AE=0.995, D2_mnb=-0.012726, AE_mnb=0.919, pred_mnb_M=1.184),
                           'W2-B17': dict(D2=0.085750, AE=1.012, D2_mnb=-0.026267, AE_mnb=1.170, pred_mnb_M=0.931),
                           'W2-B18': dict(D2=0.081896, AE=1.033, D2_mnb=-0.091376, AE_mnb=1.752, pred_mnb_M=0.621)},
        'pares': {('W2-B16', 'W2-B14'): (-0.00015868, -0.00092851, 0.00030689, -0.00019211), ('W2-B17', 'W2-B14'): (-0.00096016, -0.00437606, 0.00154672, -0.00111190),
                  ('W2-B18', 'W2-B14'): (-0.00481377, -0.01341707, 0.00158824, -0.00513303)},
        'descomposicion_motor_nb': dict(filas_positivas=265, aumento_positivas=34727.49, filas_cero=2355, reduccion_ceros=27119.35, saldo=7608.15, fold0=8637.79, cinco_grupos=18085.65),
        'rangos_factores': dict(c_f=(0.932, 0.977), c_s=(0.713, 0.803)),
        'coeficiente_negocio_precio': (0.714, 0.911), 'coeficiente_negocio_auxiliar': (0.395, 0.531)},
    'COD-S2-20261024-024': {
        'tabla': {'W2-B00': dict(D2_base=0.06858169, D2_T10F=0.06861450, D2_T10R=0.06858169, nom_base_M=15.7873, nom_T10F_M=16.1475, nom_T10R_M=16.1885),
                  'W2-B12': dict(D2_base=0.07491526, D2_T10F=0.07492702, D2_T10R=0.07491526, nom_base_M=15.5441, nom_T10F_M=15.8955, nom_T10R_M=15.9356),
                  'W2-B14': dict(D2_base=0.08671008, D2_T10F=0.08671999, D2_T10R=0.08671008, nom_base_M=15.6061, nom_T10F_M=15.9582, nom_T10R_M=15.9983)},
        'B14': dict(T10R_delta_CU=392261, T10R_pct=0.02514, T10F_delta_CU=352141, T10F_pct=0.02256, T10F_D2_delta=0.00000991, T10F_obs_delta_CU=-551, T10R_max_dif=1.82e-12)},
    'COD-S2-20261024-028': {
        'tabla': [('MIXF', 'W2-B00', 0.06851857, 0.980, 15.789714, 0.00015), ('MIXFS', 'W2-B00', 0.06800887, 0.978, 15.801605, 0.00091),
                  ('MIXF', 'W2-B12', 0.07490354, 0.995, 15.546561, 0.00016), ('MIXFS', 'W2-B12', 0.07481207, 0.995, 15.560229, 0.00104),
                  ('MIXF', 'W2-B14', 0.08670076, 0.991, 15.608671, 0.00017), ('MIXFS', 'W2-B14', 0.08662626, 0.991, 15.621943, 0.00102)],
        'base': {'W2-B00': (0.06858169, 15.787289), 'W2-B12': (0.07491526, 15.544087), 'W2-B14': (0.08671008, 15.606084)},
        'B14_motor_nb_D2': dict(base=-0.010045, MIXF=-0.010191, MIXFS=-0.011551), 'B14_buildings_nb_D2': dict(base=0.050163, MIXFS=0.050177), 'B14_contents_nb_D2': dict(base=0.153579, MIXFS=0.153679),
        'MIXFS_motor_nb_reduccion_max': 0.0447, 'celdas_cero': 5, 'mayor_peso_un_siniestro': dict(buildings_nb=0.918, contents_nb=0.972),
        'siniestros_ajuste': {('buildings', 0): (374, 389), ('buildings', 1): (29, 35), ('contents', 0): (356, 370), ('contents', 1): (26, 33), ('motor', 0): (2554, 2629), ('motor', 1): (249, 258)},
        'siniestros_nb_por_peril': {('buildings', 'fire'): (0, 0), ('buildings', 'storm'): (12, 18), ('buildings', 'flood'): (2, 4), ('buildings', 'subsidence'): (3, 5), ('buildings', 'escape_of_water'): (6, 8), ('buildings', 'accidental_damage'): (2, 3),
                                    ('contents', 'theft'): (8, 12), ('contents', 'accidental_damage'): (12, 14), ('contents', 'flood'): (3, 4), ('contents', 'escape_of_water'): (3, 4),
                                    ('motor', 'own_damage'): (94, 104), ('motor', 'third_party_prop'): (78, 86), ('motor', 'glass_hail'): (34, 41), ('motor', 'bodily_injury'): (16, 23), ('motor', 'theft'): (10, 15)},
        'pares': {('MIXF_W2-B12', 'MIXF_W2-B00'): (0.00638497, -0.00205352, 0.01856298, -0.00740125), ('MIXF_W2-B14', 'MIXF_W2-B00'): (0.01818218, -0.00621997, 0.04268353, -0.01249804),
                  ('MIXF_W2-B14', 'MIXF_W2-B12'): (0.01179721, -0.00971461, 0.03168981, -0.01284945), ('MIXFS_W2-B12', 'MIXFS_W2-B00'): (0.00680320, -0.00192002, 0.01954421, -0.00743239),
                  ('MIXFS_W2-B14', 'MIXFS_W2-B00'): (0.01861739, -0.00571939, 0.04354553, -0.01239263), ('MIXFS_W2-B14', 'MIXFS_W2-B12'): (0.01181419, -0.00970709, 0.03170717, -0.01284616),
                  ('MIXF_W2-B00', 'W2-B00'): (-0.00006312, -0.00017003, 0.00000500, -0.00008596), ('MIXFS_W2-B00', 'MIXF_W2-B00'): (-0.00050970, -0.00117663, -0.00012247, -0.00058851),
                  ('MIXF_W2-B12', 'W2-B12'): (-0.00001172, -0.00003922, 0.00000474, -0.00001962), ('MIXFS_W2-B12', 'MIXF_W2-B12'): (-0.00009147, -0.00026056, 0.00000111, -0.00012636),
                  ('MIXF_W2-B14', 'W2-B14'): (-0.00000932, -0.00003275, 0.00000614, -0.00001849), ('MIXFS_W2-B14', 'MIXF_W2-B14'): (-0.00007450, -0.00021550, 0.00000760, -0.00011201)}},
    'COD-S2-20261024-031': {'madurez540': dict(renovacion=0.5233, nb_min=0.2654, nb_max=0.2733), 'siniestros_unicos': {('buildings', 0): 479, ('buildings', 1): 40, ('contents', 0): 454, ('contents', 1): 37, ('motor', 0): 3242, ('motor', 1): 315},
                             'siniestros_deduplicados': 4567, 'celdas': 150, 'puntos_soporte': 1200, 'distancia_calendarios': (0.25, 0.26)},
    'COD-S2-20261024-033': {'fuera_mascara_hogar': dict(buildings=(6, 3175.58), contents=(24, 25869.48)), 'autos_fuera': 0,
                             'exposicion_retenida': {('motor', 'own_damage'): (0.763, 0.796), ('motor', 'glass_hail'): (0.763, 0.796), ('motor', 'theft'): (0.886, 0.901), ('buildings', 'accidental_damage'): (0.387, 0.403), ('contents', 'accidental_damage'): (0.434, 0.453)}},
    'COD-S2-20261024-026': {
        'tabla': [('R075', 'W2-B00', 14.9401, 0.067813, 0.980, 15.3859, -0.02542), ('R075', 'W2-B12', 14.9401, 0.073512, 0.995, 15.1599, -0.02471), ('R075', 'W2-B14', 14.9401, 0.086749, 0.991, 15.2184, -0.02484),
                  ('R125', 'W2-B00', 15.6541, 0.069347, 0.979, 16.1887, 0.02543), ('R125', 'W2-B12', 15.6541, 0.076249, 0.996, 15.9283, 0.02472), ('R125', 'W2-B14', 15.6541, 0.086622, 0.992, 15.9936, 0.02483),
                  ('L1', 'W2-B00', 15.2971, 0.068832, 0.980, 15.6820, -0.00667), ('L1', 'W2-B12', 15.2971, 0.074995, 0.996, 15.4413, -0.00661), ('L1', 'W2-B14', 15.2971, 0.086782, 0.992, 15.5034, -0.00658)],
        'B14': dict(nom_base=15.606084, nom_R075=15.218380, nom_R125=15.993601, pct_R075=-0.02484, pct_R125=0.02483, nom_L1=15.503358, pct_L1=-0.00658),
        'reserva_2023': dict(reserva=1427914.85, cuota=0.09335, neto=15297103.84),
        'pares': {('L1_W2-B14', 'W2-B14'): (0.00007145, 0.00000100, 0.00017868, -0.00004881)}},
}


# ----------------------------------------------------------------------------------------------- utilidades
def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def to_py(o):
    if isinstance(o, dict):
        return {str(k): to_py(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [to_py(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (pd.Timestamp, dt.date)):
        return str(o)[:10]
    if isinstance(o, float) and (np.isnan(o) or np.isinf(o)):
        return None
    return o


def dev_unit(y, mu):
    y = np.asarray(y, float); mu = np.asarray(mu, float)
    return np.maximum(4 * (y / np.sqrt(mu) + np.sqrt(mu) - 2 * np.sqrt(y)), 0.0)


def metr(y, pred):
    y = np.asarray(y, float); pred = np.asarray(pred, float)
    loss = float(dev_unit(y, pred).sum())
    null = float(8 * (np.sqrt(len(y) * y.sum()) - np.sqrt(y).sum()))
    return dict(filas=int(len(y)), observado=float(y.sum()), predicho=float(pred.sum()), AE=float(y.sum() / pred.sum()),
                devianza=loss, devianza_nula=null, D2=float(1 - loss / null) if null > 0 else None)


def redondeo_igual(x, publicado, decimales):
    """¿coincide el valor recalculado con el publicado a la precisión impresa? Tolera medio dígito por el redondeo."""
    return abs(round(float(x), decimales) - publicado) <= 1.5 * 10 ** (-decimales) + 1e-12


class Registro:
    def __init__(self):
        self.controles, self.detalle = [], {}

    def add(self, id_, area, titulo, resultado, observado, esperado='', severidad='', detalle=None):
        if resultado in ('pasa', 'informativo'):
            severidad = ''
        self.controles.append(dict(id=id_, area=area, titulo=titulo, resultado=resultado, severidad=severidad, observado=str(observado), esperado=str(esperado)))
        if detalle is not None:
            self.detalle[id_] = to_py(detalle)
        print(f'  {id_} {resultado:11s} {titulo[:90]}', flush=True)


# ----------------------------------------------------------------------------------------------- carga
class Corridas:
    def __init__(self, raiz: pathlib.Path, base: pathlib.Path, dev3: pathlib.Path, f0: pathlib.Path, emerging: pathlib.Path, capital_claude: pathlib.Path, salida: pathlib.Path = None):
        self.raiz = raiz
        self.salida = salida
        self.dir = {k: raiz / v for k, v in RUNS.items()}
        self.man = {k: json.load(open(self.dir[k] / 'manifest.json', encoding='utf-8')) for k in RUNS}
        self.rep = {k: json.load(open(self.dir[k] / 'report.json', encoding='utf-8')) for k in RUNS}
        self.plan = {k: json.load(open(self.dir[k] / 'plan_snapshot.json', encoding='utf-8')) for k in RUNS}
        self.oof = {k: pq.read_table(self.dir[k] / 'oof_2023.parquet').to_pandas() for k in ['dev5', 'dev6', 'dev7']}
        self.cola_base = pq.read_table(self.dir['cola'] / 'base_oof_2023.parquet').to_pandas()
        self.cola_stress = pq.read_table(self.dir['cola'] / 'stress_oof_2023.parquet').to_pandas()
        self.mec = pq.read_table(self.dir['mecanismo'] / 'mechanism_oof_2023.parquet').to_pandas()
        self.base_dir, self.dev3_dir, self.f0_dir, self.emerging, self.capital_claude = base, dev3, f0, emerging, capital_claude
        tgt = pq.read_table(base / 'target_T0_and_stresses.parquet', columns=['line', 'row_id', 'year', 'is_test', 'exposure', 'T0', 'reserve', 'T1_reserve075', 'T1_reserve125']).to_pandas()
        self.tgt = tgt
        self.part = pq.read_table(base / 'partitions.parquet', columns=['line', 'row_id', 'year', 'group_id', 'fold']).to_pandas()
        self.dev3 = pq.read_table(dev3 / 'oof_2023.parquet', columns=['line', 'row_id', 'model_id', 'e_cost_mix_1.0', 'exposure', 'T0']).to_pandas()
        self.cap56 = pq.read_table(raiz / 'revision_filas_20261023T235757Z_cafaba7d' / 'capital_56_rows.parquet').to_pandas()
        self.mix = pq.read_table(self.dir['mezcla'] / 'mixture_oof_2023.parquet').to_pandas()
        self.cal = pq.read_table(self.dir['soporte'] / 'calendar_profile.parquet').to_pandas()
        self.celdas = pq.read_table(self.dir['soporte'] / 'peril_business_cells.parquet').to_pandas()
        self.denom = pq.read_table(self.dir['coberturas'] / 'denominators_and_numerators.parquet').to_pandas()
        self.readout = {k: json.load(open(self.dir[k] / 'readout.json', encoding='utf-8')) for k in ['soporte', 'coberturas']}
        self.audit = pq.read_table(base / 'claim_assignment_audit.parquet').to_pandas()
        pol = []
        for l in LINES:
            cols = ['row_id', 'policy_id', 'period_start', 'period_end', 'new_business'] + (['cover_type'] if l == 'motor' else ['accidental_damage_cover'])
            t = pq.read_table(emerging / f'policies_{l}.parquet', columns=cols).to_pandas()
            t['line'] = l
            pol.append(t)
        self.pol = pd.concat(pol, ignore_index=True)
        self.pol['period_start'] = pd.to_datetime(self.pol.period_start); self.pol['period_end'] = pd.to_datetime(self.pol.period_end)
        self.links = {(l, f): pq.read_table(self.dir['dev5'] / 'links_2023' / f'{l}_fold{f}.parquet', columns=['row_id', 'exposure', 'e_cost_mix_1.0']).to_pandas().set_index('row_id')
                      for l in LINES for f in range(5)}
        self.inputs = {l: pq.read_table(self.dir['dev5'] / 'inputs_2023' / f'{l}.parquet').to_pandas().set_index('row_id') for l in LINES}
        self.grupos_motor = pq.read_table(raiz / 'revision_filas_20261023T235757Z_cafaba7d' / 'motor_new_group_loss.parquet').to_pandas()

    def wide(self, k):
        """Una fila por row_id; columnas pred_<modelo>, rate_<modelo>, dev_<modelo> y las comunes."""
        o = self.oof[k]
        comunes = o.drop_duplicates(KEY).set_index('row_id')[['line', 'group_id', 'fold', 'exposure', 'T0', 'reserve', 'x_new_business', 'e_cost_mix_1.0']]
        p = o.pivot(index='row_id', columns='model_id', values='prediction')
        r = o.pivot(index='row_id', columns='model_id', values='annual_rate')
        d = o.pivot(index='row_id', columns='model_id', values='unit_deviance')
        w = comunes.join(p.add_prefix('pred_')).join(r.add_prefix('rate_')).join(d.add_prefix('dev_'))
        return w.reset_index()


# ----------------------------------------------------------------------------------------------- A. fuentes
def a_fuentes(C: Corridas, R: Registro):
    det, ok, n = {}, 0, 0
    for k, d in C.dir.items():
        files = {f['path']: f['sha256'] for f in C.man[k]['files']}
        for p in d.rglob('*'):
            if p.is_file() and p.name != 'manifest.json':
                rel = p.relative_to(d).as_posix()
                if rel in files:
                    n += 1
                    igual = sha256(p) == files[rel]
                    ok += igual
                    det.setdefault(k, {})[rel] = igual
                else:
                    det.setdefault(k, {})[rel] = 'fuera del manifiesto (escrito después)'
    det['oof_sha256'] = {k: sha256(C.dir[k] / 'oof_2023.parquet') for k in ['dev5', 'dev6', 'dev7']}
    det['oof_sha256']['cola_stress'] = sha256(C.dir['cola'] / 'stress_oof_2023.parquet')
    det['oof_sha256']['mecanismo'] = sha256(C.dir['mecanismo'] / 'mechanism_oof_2023.parquet')
    det['oof_sha256']['base_oof_cola'] = sha256(C.dir['cola'] / 'base_oof_2023.parquet')
    det['oof_sha256']['mezcla'] = sha256(C.dir['mezcla'] / 'mixture_oof_2023.parquet')
    det['informes'] = {k: dict(id=C.rep[k].get('id'), inicio=C.rep[k].get('started_utc'), fin=C.rep[k].get('completed_utc'), plan_sha256=C.rep[k].get('plan_sha256')) for k in RUNS}
    R.add('VN01', 'Fuentes', 'Huellas de las corridas copiadas (OOF, informes, planes, código) frente a los manifiestos de Codex', 'pasa' if ok == n else 'hallazgo',
          f'{ok} de {n} archivos con huella igual', 'todas', 'P0' if ok != n else '', det)
    # VN02 coherencia con la base
    det = {}
    tg = C.tgt[(C.tgt.year == 2023) & (~C.tgt.is_test.astype(bool))].set_index('row_id')
    pt = C.part[C.part.year == 2023].set_index('row_id')
    d3 = C.dev3[C.dev3.model_id == C.dev3.model_id.iloc[0]].set_index('row_id')
    fallos = 0
    for k in ['dev5', 'dev6', 'dev7']:
        w = C.wide(k).set_index('row_id')
        d = dict(filas=len(w), modelos=sorted(c[5:] for c in w.columns if c.startswith('pred_')),
                 mismo_conjunto_2023=set(w.index) == set(tg.index),
                 T0_igual=bool(np.allclose(w.T0, tg.loc[w.index, 'T0'], atol=1e-9)),
                 reserva_igual=bool(np.allclose(w.reserve, tg.loc[w.index, 'reserve'], atol=1e-9)),
                 exposure_igual=bool(np.allclose(w.exposure, tg.loc[w.index, 'exposure'], atol=1e-12)),
                 fold_igual=bool((w.fold.to_numpy() == pt.loc[w.index, 'fold'].to_numpy()).all()),
                 grupo_igual=bool((w.group_id.to_numpy() == pt.loc[w.index, 'group_id'].to_numpy()).all()),
                 e_cost_igual_a_dev3=bool(np.allclose(w['e_cost_mix_1.0'], d3.loc[w.index, 'e_cost_mix_1.0'], atol=1e-12)))
        det[k] = d
        fallos += sum(not d[x] for x in ['mismo_conjunto_2023', 'T0_igual', 'reserva_igual', 'exposure_igual', 'fold_igual', 'grupo_igual', 'e_cost_igual_a_dev3'])
    for nombre, df in [('cola_base', C.cola_base), ('mecanismo', C.mec)]:
        u = df.drop_duplicates('row_id').set_index('row_id')
        d = dict(filas=len(u), mismo_conjunto_2023=set(u.index) == set(tg.index), T0_igual=bool(np.allclose(u.T0, tg.loc[u.index, 'T0'], atol=1e-9)),
                 fold_igual=bool((u.fold.to_numpy() == pt.loc[u.index, 'fold'].to_numpy()).all()), grupo_igual=bool((u.group_id.to_numpy() == pt.loc[u.index, 'group_id'].to_numpy()).all()))
        det[nombre] = d
        fallos += sum(not d[x] for x in ['mismo_conjunto_2023', 'T0_igual', 'fold_igual', 'grupo_igual'])
    # nuevo negocio frente a las pólizas originales
    nb = pd.concat([pq.read_table(C.emerging / f'policies_{l}.parquet', columns=['row_id', 'new_business']).to_pandas() for l in LINES]).set_index('row_id').new_business.astype(int)
    w5 = C.wide('dev5').set_index('row_id')
    det['x_new_business_igual_a_policies'] = bool((w5.x_new_business.astype(int) == nb.loc[w5.index]).all())
    fallos += not det['x_new_business_igual_a_policies']
    R.add('VN02', 'Fuentes', 'Los OOF de dev5, dev6, dev7, cola y mecanismo tienen las 50.094 filas de 2023 con T0, reserva, exposición, fold, grupo y C0 iguales a la base y a dev3; x_new_business igual a las pólizas',
          'pasa' if fallos == 0 else 'hallazgo', f'{fallos} discrepancias', '0', 'P0' if fallos else '', det)
    # VN03 identidades por fila
    det, fallos = {}, 0
    for k in ['dev5', 'dev6', 'dev7']:
        o = C.oof[k]
        dif_pred = float((o.prediction - o.annual_rate * o['e_cost_mix_1.0']).abs().max())
        dif_dev = float((o.unit_deviance - dev_unit(o.T0, o.prediction)).abs().max())
        det[k] = dict(max_dif_prediction_vs_tasa_por_C0=dif_pred, max_dif_unit_deviance_vs_formula=dif_dev, predicciones_positivas_finitas=bool(np.isfinite(o.prediction).all() and (o.prediction > 0).all()),
                      filas_por_modelo=o.groupby('model_id').size().to_dict())
        fallos += (dif_pred > 1e-6) + (dif_dev > 1e-6) + (not det[k]['predicciones_positivas_finitas'])
    st = C.cola_stress
    det['cola_stress'] = dict(max_dif_prediction_vs_tasa_por_e=float((st.prediction - st.annual_rate * st.effective_exposure).abs().max()),
                              max_dif_nominal_vs_exposure_por_tasa=float((st.conditional_nominal_2023 - st.annual_rate * st.exposure).abs().max()),
                              max_dif_unit_deviance=float((st.unit_deviance - dev_unit(st.T0, st.prediction)).abs().max()))
    mx = C.mix
    det['mezcla'] = dict(max_dif_prediction_vs_tasa_por_e=float((mx.prediction - mx.annual_rate * mx.effective_exposure).abs().max()),
                         max_dif_nominal_vs_exposure_por_tasa=float((mx.conditional_nominal_2023 - mx.annual_rate * mx.exposure).abs().max()),
                         max_dif_unit_deviance=float((mx.unit_deviance - dev_unit(mx.T0, mx.prediction)).abs().max()))
    fallos += sum(v > 1e-6 for v in det['mezcla'].values())
    m = C.mec
    det['mecanismo'] = dict(max_dif_prediction_vs_tasa_por_e=float((m.prediction - m.annual_rate * m.effective_exposure).abs().max()),
                            max_dif_nominal_vs_exposure_por_tasa=float((m.conditional_nominal_2023 - m.annual_rate * m.exposure).abs().max()),
                            max_dif_unit_deviance_sobre_T_s=float((m.unit_deviance - dev_unit(m.T_s, m.prediction)).abs().max()))
    fallos += sum(v > 1e-6 for v in det['cola_stress'].values()) + sum(v > 1e-6 for v in det['mecanismo'].values())
    R.add('VN03', 'Fuentes', 'Identidades por fila: prediction = tasa × C0 (o × exposición efectiva), nominal = exposición × tasa, unit_deviance = fórmula Tweedie 1,5 sobre el objetivo del escenario',
          'pasa' if fallos == 0 else 'hallazgo', f'{fallos} identidades rotas', '0', 'P0' if fallos else '', det)


# ----------------------------------------------------------------------------------------------- B. resumen por receta
def segmentos(w, modelo):
    y, p = w.T0.to_numpy(), w[f'pred_{modelo}'].to_numpy()
    out = dict(global_=metr(y, p))
    nb = w.x_new_business.astype(int) == 1
    out['nb'] = metr(y[nb], p[nb])
    out['ren'] = metr(y[~nb], p[~nb])
    for l in LINES:
        ml = (w.line == l).to_numpy()
        out[f'{l}_all'] = metr(y[ml], p[ml])
        out[f'{l}_nb'] = metr(y[ml & nb.to_numpy()], p[ml & nb.to_numpy()])
    return out


def b_recetas(C: Corridas, R: Registro, salida: pathlib.Path):
    det, filas, fallos_rep, fallos_foro, comparaciones = {}, [], 0, 0, 0
    recalculado = {}
    for k in ['dev5', 'dev6', 'dev7']:
        w = C.wide(k)
        rep = {s['model_id']: s for s in C.rep[k]['summary']}
        modelos = sorted(c[5:] for c in w.columns if c.startswith('pred_'))
        det[k] = {}
        for mo in modelos:
            s = segmentos(w, mo)
            recalculado[(k, mo)] = s
            g = s['global_']
            r = rep.get(mo)
            comp = {}
            if r is not None:
                comp = dict(D2_informe=r['D2'], D2_dif=abs(r['D2'] - g['D2']), predicho_informe=r['predicted_total'], predicho_dif=abs(r['predicted_total'] - g['predicho']),
                            observado_igual=abs(r['observed_total'] - g['observado']) < 1e-6, nula_dif=abs(r['null_deviance_sum'] - g['devianza_nula']))
                fallos_rep += (comp['D2_dif'] > 1e-9) + (comp['predicho_dif'] > 1e-4) + (not comp['observado_igual']) + (comp['nula_dif'] > 1e-4)
            det[k][mo] = dict(recalculado={kk: vv for kk, vv in s.items()}, frente_al_informe=comp)
            filas.append(dict(corrida=k, modelo=mo, D2=g['D2'], predicho=g['predicho'], observado=g['observado'], AE=g['AE'], D2_nb=s['nb']['D2'], AE_nb=s['nb']['AE'],
                              predicho_nb=s['nb']['predicho'], D2_motor_nb=s['motor_nb']['D2'], AE_motor_nb=s['motor_nb']['AE'], predicho_motor_nb=s['motor_nb']['predicho'],
                              D2_buildings_nb=s['buildings_nb']['D2'], D2_contents_nb=s['contents_nb']['D2'], AE_contents_nb=s['contents_nb']['AE'],
                              D2_informe=comp.get('D2_informe'), D2_dif_informe=comp.get('D2_dif')))
    tabla = pd.DataFrame(filas)
    tabla.to_csv(salida / 'tablas' / 'recetas_recalculadas.csv', index=False)
    # frente al foro
    foro = {}
    for post in ['COD-S2-20261023-017', 'COD-S2-20261024-019']:
        k = 'dev5' if post.endswith('017') else 'dev6'
        for mo, pub in PUBLICADO[post]['tabla'].items():
            s = recalculado[(k, mo)]
            chk = dict(D2=redondeo_igual(s['global_']['D2'], pub['D2'], len(str(pub['D2']).split('.')[1])), pred_M=redondeo_igual(s['global_']['predicho'] / 1e6, pub['pred_M'], 3),
                       AE=redondeo_igual(s['global_']['AE'], pub['AE'], 3), D2_nb=redondeo_igual(s['nb']['D2'], pub['D2_nb'], 5), AE_nb=redondeo_igual(s['nb']['AE'], pub['AE_nb'], 3))
            foro[f'{post} {mo}'] = dict(publicado=pub, recalculado=dict(D2=s['global_']['D2'], pred_M=s['global_']['predicho'] / 1e6, AE=s['global_']['AE'], D2_nb=s['nb']['D2'], AE_nb=s['nb']['AE']), coincide=chk)
            comparaciones += len(chk); fallos_foro += sum(not v for v in chk.values())
        for (mo, l, seg, met), pub in PUBLICADO[post].get('segmentos', {}).items():
            s = recalculado[(k, mo)][f'{l}_{"nb" if seg == "nb" else "all"}']
            val = s['D2'] if met == 'D2' else s['AE']
            dec = len(str(pub).split('.')[1])
            okk = redondeo_igual(val, pub, dec)
            foro[f'{post} {mo} {l} {seg} {met}'] = dict(publicado=pub, recalculado=val, coincide=okk)
            comparaciones += 1; fallos_foro += not okk
    s017 = recalculado[('dev5', 'W2-B00')]
    foro['COD-S2-20261023-017 observado'] = dict(publicado_M=PUBLICADO['COD-S2-20261023-017']['observado_M'], recalculado_M=s017['global_']['observado'] / 1e6,
                                                  publicado_nb_M=PUBLICADO['COD-S2-20261023-017']['observado_nb_M'], recalculado_nb_M=s017['nb']['observado'] / 1e6,
                                                  coincide=redondeo_igual(s017['global_']['observado'] / 1e6, 15.297, 3) and redondeo_igual(s017['nb']['observado'] / 1e6, 1.528, 3))
    comparaciones += 2; fallos_foro += (not foro['COD-S2-20261023-017 observado']['coincide']) * 2
    for mo, pub in PUBLICADO['COD-S2-20261024-021']['tabla_autos_nb'].items():
        s = recalculado[('dev7', mo)]
        chk = dict(D2=redondeo_igual(s['global_']['D2'], pub['D2'], 6), AE=redondeo_igual(s['global_']['AE'], pub['AE'], 3), D2_mnb=redondeo_igual(s['motor_nb']['D2'], pub['D2_mnb'], 6),
                   AE_mnb=redondeo_igual(s['motor_nb']['AE'], pub['AE_mnb'], 3), pred_mnb_M=redondeo_igual(s['motor_nb']['predicho'] / 1e6, pub['pred_mnb_M'], 3))
        foro[f'COD-S2-20261024-021 {mo}'] = dict(publicado=pub, recalculado=dict(D2=s['global_']['D2'], AE=s['global_']['AE'], D2_mnb=s['motor_nb']['D2'], AE_mnb=s['motor_nb']['AE'], pred_mnb_M=s['motor_nb']['predicho'] / 1e6), coincide=chk)
        comparaciones += len(chk); fallos_foro += sum(not v for v in chk.values())
    det['frente_al_foro'] = foro
    det['comparaciones_con_el_foro'] = comparaciones
    det['fallos_frente_al_foro'] = fallos_foro
    det['fallos_frente_al_informe'] = fallos_rep
    R.add('VN04', 'Recetas', 'D², predicho, A/E y segmentos de nuevo negocio recalculados para los 49 pares corrida-modelo de dev5, dev6 y dev7 frente a report.json y a las tablas del foro (017, 019, 021)',
          'pasa' if fallos_rep == 0 and fallos_foro == 0 else 'hallazgo', f'{fallos_rep} discrepancias con los informes; {fallos_foro} de {comparaciones} cifras del foro no coinciden',
          '0 y 0', 'P1' if (fallos_rep or fallos_foro) else '', det)
    return recalculado


def c_constantes(C: Corridas, R: Registro):
    """B00 y B12 reconstruidos desde los folds de ajuste con la fórmula declarada."""
    w = C.wide('dev5')
    y = w.T0.to_numpy()
    det, fallos = {}, 0
    # el enlace C0 que usa el ajuste del fold k es el de links_2023/{ramo}_fold{k} para TODAS las filas (exclude_foldk); el OOF solo guarda el de la fila validada
    e_link = {}
    for l in LINES:
        for f in range(5):
            e_link[(l, f)] = C.links[(l, f)].loc[w.row_id[w.line == l], 'e_cost_mix_1.0'].to_numpy()
    enlace_val_igual_oof = max(float(np.abs(e_link[(l, f)][(w.fold[w.line == l] == f).to_numpy()] - w['e_cost_mix_1.0'][(w.line == l) & (w.fold == f)].to_numpy()).max()) for l in LINES for f in range(5))
    det['enlace_del_fold_en_filas_validadas_igual_al_OOF'] = enlace_val_igual_oof
    for mo, por_negocio in [('W2-B00', False), ('W2-B12', True)]:
        pred = np.full(len(w), np.nan)
        consts = {}
        for l in LINES:
            ml = (w.line == l).to_numpy()
            yl = y[ml]; foldl = w.fold.to_numpy()[ml]; nbl = w.x_new_business.astype(int).to_numpy()[ml]
            for f in range(5):
                e = e_link[(l, f)]
                celdas = [(0,), (1,)] if por_negocio else [(0, 1)]
                for celda in celdas:
                    fit = (foldl != f) & np.isin(nbl, celda)
                    val = (foldl == f) & np.isin(nbl, celda)
                    c = float((yl[fit] / np.sqrt(e[fit])).sum() / np.sqrt(e[fit]).sum())
                    idx = np.where(ml)[0][val]
                    pred[idx] = c * e[val]
                    consts[f'{l}_fold{f}' + (f'_nb{celda[0]}' if por_negocio else '')] = c
        dif = np.abs(pred - w[f'pred_{mo}'].to_numpy())
        rel = dif / w[f'pred_{mo}'].to_numpy()
        det[mo] = dict(constantes=consts, n_constantes=len(consts), max_dif_abs=float(dif.max()), max_dif_rel=float(rel.max()), reproducido=bool(rel.max() < 1e-9))
        fallos += not det[mo]['reproducido']
    # sin el enlace del fold (usando el C0 del OOF para las filas de ajuste) la reconstrucción falla por 1–2 %: queda anotado
    e_oof = w['e_cost_mix_1.0'].to_numpy()
    pred0 = np.full(len(w), np.nan)
    for l in LINES:
        for f in range(5):
            fit = (w.line == l).to_numpy() & (w.fold != f).to_numpy(); val = (w.line == l).to_numpy() & (w.fold == f).to_numpy()
            pred0[val] = float((y[fit] / np.sqrt(e_oof[fit])).sum() / np.sqrt(e_oof[fit]).sum()) * e_oof[val]
    det['B00_con_C0_del_OOF_en_el_ajuste_max_dif_rel'] = float(np.abs(pred0 / w['pred_W2-B00'].to_numpy() - 1).max())
    R.add('VN05', 'Recetas', 'B00 (15 constantes por ramo y fold) y B12 (30 por ramo, negocio y fold) reconstruidos con la fórmula declarada sum(T0/√e)/sum(√e) sobre los folds de ajuste y el enlace C0 del fold: predicciones OOF idénticas',
          'pasa' if fallos == 0 else 'hallazgo', f"max dif relativa B00 {det['W2-B00']['max_dif_rel']:.1e}, B12 {det['W2-B12']['max_dif_rel']:.1e}", '< 1e-9', 'P1' if fallos else '', det)


# ----------------------------------------------------------------------------------------------- C. capital, credibilidad y ablaciones
def d_capital_credibilidad(C: Corridas, R: Registro, recalculado):
    w6 = C.wide('dev6').set_index('row_id')
    # VN06 B14 frente a B13: solo las 56 filas de capital
    r = w6['pred_W2-B14'] / w6['pred_W2-B13']
    cap = C.cap56.set_index('row_id')
    mio = pq.read_table(C.capital_claude).to_pandas()
    mio_2023 = mio[(mio.year == 2023) & (~mio.is_test.astype(bool))]
    en56 = w6.index.isin(cap.index)
    hogar = (w6.line != 'motor').to_numpy()
    resto_hogar = hogar & ~en56
    log_resto = np.log(r[resto_hogar])
    det = dict(capital_56_por_ramo=cap.line.value_counts().to_dict(), T0_cero_en_las_56=bool((w6.loc[cap.index].T0 == 0).all()),
               las_56_son_las_2023_de_CAPS2_01=set(cap.index) == set(mio_2023.row_id), filas_2023_en_CAPS2_01=int(len(mio_2023)),
               cambio_relativo_56_min=float((r[en56] - 1).min()), cambio_relativo_56_max=float((r[en56] - 1).max()),
               cambio_publicado=(PUBLICADO['COD-S2-20261024-019']['capital_56']['cambio_min'], PUBLICADO['COD-S2-20261024-019']['capital_56']['cambio_max']),
               cambio_en_capital_56_parquet=(float(cap.total_relative_change.min()), float(cap.total_relative_change.max())),
               motor_identico=bool((r[~hogar] - 1).abs().max() < 1e-12),
               resto_hogar_filas=int(resto_hogar.sum()), resto_hogar_cambian=int((np.abs(log_resto) > 1e-12).sum()),
               resto_hogar_max_abs_log_cambio_por_ramo={l: float(np.abs(np.log(r[resto_hogar & (w6.line == l).to_numpy()])).max()) for l in ['buildings', 'contents']},
               efecto_reajuste_publicado_020=dict(buildings=0.00157, contents=0.00272),
               efecto_reajuste_en_las_56_segun_capital_56_parquet={l: float(cap[cap.line == l].refit_log_effect.abs().max()) for l in ['buildings', 'contents']},
               delta_D2_B14_B13=float(recalculado[('dev6', 'W2-B14')]['global_']['D2'] - recalculado[('dev6', 'W2-B13')]['global_']['D2']),
               lectura='B14 reajusta diez GLM de hogar con el capital corregido en 56 filas: esas 56 cambian mucho (sustitución del capital imputado) y el resto del hogar cambia poco (solo por los coeficientes reajustados); autos idéntico')
    ok = det['T0_cero_en_las_56'] and det['las_56_son_las_2023_de_CAPS2_01'] and det['capital_56_por_ramo'].get('buildings') == 26 and det['capital_56_por_ramo'].get('contents') == 30 \
        and redondeo_igual(det['cambio_relativo_56_min'], -0.6236, 4) and redondeo_igual(det['cambio_relativo_56_max'], 1.5409, 4) and det['motor_identico'] \
        and redondeo_igual(det['efecto_reajuste_en_las_56_segun_capital_56_parquet']['buildings'], 0.00157, 5) and redondeo_igual(det['efecto_reajuste_en_las_56_segun_capital_56_parquet']['contents'], 0.00272, 5)
    R.add('VN06', 'Capital', 'Las 56 filas de capital de 2023 (26 edificios, 30 contenidos) son las de CAPS2-01, tienen T0 = 0 y cambian entre −62,36 % y +154,09 % de B13 a B14, con un efecto del reajuste de como mucho 0,157 % y 0,272 % en escala log en esas filas; autos idéntico; el resto del hogar se mueve por los coeficientes reajustados',
          'pasa' if ok else 'hallazgo', f"56 filas {det['capital_56_por_ramo']}, cambio {det['cambio_relativo_56_min']:+.4f} a {det['cambio_relativo_56_max']:+.4f}; resto del hogar máx |Δlog| {det['resto_hogar_max_abs_log_cambio_por_ramo']}; T0 cero: {det['T0_cero_en_las_56']}",
          'cambios publicados en 019 y 020', 'P1' if not ok else '', det)
    # VN07 B15 = B14 × c en nuevo negocio
    nb = w6.x_new_business.astype(int) == 1
    ratio = w6['pred_W2-B15'] / w6['pred_W2-B14']
    det = dict(renovacion_identica=bool((ratio[~nb] - 1).abs().max() < 1e-12), max_dif_renovacion=float((ratio[~nb] - 1).abs().max()))
    cred = {(c['fold'], l): c['ramos'][l] for c in C.rep['dev6']['credibility'] for l in LINES}
    tabla, fallos = [], 0
    for l in LINES:
        for f in sorted(w6.fold.unique()):
            m = nb & (w6.line == l) & (w6.fold == f)
            vals = ratio[m]
            c_oof = float(vals.median()); disp = float((vals - c_oof).abs().max())
            c_rep = cred[(int(f), l)]['c']
            tabla.append(dict(ramo=l, fold=int(f), c_oof=c_oof, dispersion_dentro_de_la_celda=disp, c_informe=c_rep, dif=abs(c_oof - c_rep),
                              Z_f=cred[(int(f), l)]['Z_f'], Z_s=cred[(int(f), l)]['Z_s'], rel_em=cred[(int(f), l)]['rel_em'], rel_cred=cred[(int(f), l)]['rel_cred'],
                              tau_f=[c['tau_f'] for c in C.rep['dev6']['credibility'] if c['fold'] == f][0], tau_s=[c['tau_s'] for c in C.rep['dev6']['credibility'] if c['fold'] == f][0]))
            fallos += (disp > 1e-9) + (abs(c_oof - c_rep) > 1e-9)
    det['por_celda'] = tabla
    det['renovacion_identica'] = det['renovacion_identica']
    fallos += not det['renovacion_identica']
    mios = json.load(open(C.capital_claude.parent.parent / 'final' / 'decisiones_20261023' / 'factores_nb_cred.json', encoding='utf-8')) if (C.capital_claude.parent.parent / 'final' / 'decisiones_20261023' / 'factores_nb_cred.json').exists() else None
    det['c_de_Claude_todo_2023'] = {l: (mios['ramos'][l]['c'] if mios and 'ramos' in mios else None) for l in LINES} if mios else 'no disponible'
    det['rel_cred_de_Claude_todo_2023'] = {l: (mios['ramos'][l]['relatividad_creible'] if mios and 'ramos' in mios else None) for l in LINES} if mios else 'no disponible'
    det['rango_c_codex_por_ramo'] = {l: (min(t['c_oof'] for t in tabla if t['ramo'] == l), max(t['c_oof'] for t in tabla if t['ramo'] == l)) for l in LINES}
    det['rango_rel_em_codex_por_ramo'] = {l: (min(t['rel_em'] for t in tabla if t['ramo'] == l), max(t['rel_em'] for t in tabla if t['ramo'] == l)) for l in LINES}
    det['rango_rel_cred_codex_por_ramo'] = {l: (min(t['rel_cred'] for t in tabla if t['ramo'] == l), max(t['rel_cred'] for t in tabla if t['ramo'] == l)) for l in LINES}
    R.add('VN07', 'Credibilidad', 'B15 = B14 × c solo en el nuevo negocio: c constante dentro de cada ramo y fold e igual al c del informe de dev6; renovación idéntica; rangos de c frente al c de Claude con todo 2023',
          'pasa' if fallos == 0 else 'hallazgo', f"{fallos} celdas con c distinto o disperso; c por ramo {det['rango_c_codex_por_ramo']}", 'c constante por celda e igual al informe', 'P1' if fallos else '', det)
    # VN08 ablaciones B16, B17, B18 (dev7)
    w7 = C.wide('dev7').set_index('row_id')
    nb7 = w7.x_new_business.astype(int) == 1
    det, fallos = {}, 0
    for mo in ['W2-B15', 'W2-B16', 'W2-B17', 'W2-B18']:
        rr = w7[f'pred_{mo}'] / w7['pred_W2-B14']
        hogar = w7.line != 'motor'
        det[mo] = dict(hogar_identico_a_B14=bool((rr[hogar] - 1).abs().max() < 1e-12), renovacion_motor_identica=bool((rr[~nb7 & ~hogar] - 1).abs().max() < 1e-12))
        if mo == 'W2-B15':
            det[mo]['hogar_identico_a_B14'] = 'no aplica (B15 también corrige hogar)'
            det[mo]['hogar_nb_cambia'] = bool((rr[hogar & nb7] - 1).abs().max() > 1e-9)
        else:
            fallos += not det[mo]['hogar_identico_a_B14']
        fallos += not det[mo]['renovacion_motor_identica']
        celdas = {}
        for f in sorted(w7.fold.unique()):
            m = nb7 & (w7.line == 'motor') & (w7.fold == f)
            celdas[int(f)] = dict(factor=float(rr[m].median()), dispersion=float((rr[m] - rr[m].median()).abs().max()))
            fallos += celdas[int(f)]['dispersion'] > 1e-9
        det[mo]['factor_motor_nb_por_fold'] = celdas
    prod = {f: det['W2-B16']['factor_motor_nb_por_fold'][f]['factor'] * det['W2-B17']['factor_motor_nb_por_fold'][f]['factor'] for f in det['W2-B16']['factor_motor_nb_por_fold']}
    det['c_f_por_c_s_igual_a_c_B15'] = {f: dict(producto=prod[f], c_B15=det['W2-B15']['factor_motor_nb_por_fold'][f]['factor'], dif=abs(prod[f] - det['W2-B15']['factor_motor_nb_por_fold'][f]['factor'])) for f in prod}
    fallos += sum(v['dif'] > 1e-9 for v in det['c_f_por_c_s_igual_a_c_B15'].values())
    rangos = dict(c_f=(min(v['factor'] for v in det['W2-B16']['factor_motor_nb_por_fold'].values()), max(v['factor'] for v in det['W2-B16']['factor_motor_nb_por_fold'].values())),
                  c_s=(min(v['factor'] for v in det['W2-B17']['factor_motor_nb_por_fold'].values()), max(v['factor'] for v in det['W2-B17']['factor_motor_nb_por_fold'].values())),
                  B18=(min(v['factor'] for v in det['W2-B18']['factor_motor_nb_por_fold'].values()), max(v['factor'] for v in det['W2-B18']['factor_motor_nb_por_fold'].values())))
    det['rangos_recalculados'] = rangos
    det['rangos_publicados_021'] = PUBLICADO['COD-S2-20261024-021']['rangos_factores']
    ok_r = redondeo_igual(rangos['c_f'][0], 0.932, 3) and redondeo_igual(rangos['c_f'][1], 0.977, 3) and redondeo_igual(rangos['c_s'][0], 0.713, 3) and redondeo_igual(rangos['c_s'][1], 0.803, 3)
    fallos += not ok_r
    R.add('VN08', 'Ablaciones', 'B16, B17 y B18 cambian solo los autos nuevos (hogar y renovaciones idénticos a B14), con un factor constante por fold; c_f × c_s = c de B15; rangos 0,932–0,977 y 0,713–0,803 como en 021',
          'pasa' if fallos == 0 else 'hallazgo', f"{fallos} fallos; c_f {rangos['c_f']}, c_s {rangos['c_s']}, B18 {rangos['B18']}", 'ablaciones exactas', 'P1' if fallos else '', det)
    # VN09 descomposición de la pérdida de autos nuevos B15 frente a B14
    m = nb7 & (w7.line == 'motor')
    d15, d14 = w7.loc[m, 'dev_W2-B15'], w7.loc[m, 'dev_W2-B14']
    inc = d15 - d14
    pos = w7.loc[m, 'T0'] > 0
    por_grupo = inc.groupby(w7.loc[m, 'group_id']).sum().sort_values(ascending=False)
    pub = PUBLICADO['COD-S2-20261024-021']['descomposicion_motor_nb']
    det = dict(filas_positivas=int(pos.sum()), aumento_en_positivas=float(inc[pos].sum()), filas_cero=int((~pos).sum()), reduccion_en_ceros=float(-inc[~pos].sum()), saldo=float(inc.sum()),
               por_fold={int(f): float(v) for f, v in inc.groupby(w7.loc[m, 'fold']).sum().items()}, cinco_grupos_mas_perjudicados=float(por_grupo.head(5).sum()),
               grupos_con_aumento=int((por_grupo > 0).sum()), grupos_total=int(len(por_grupo)), publicado=pub,
               coincide_con_motor_new_group_loss=bool(np.allclose(np.sort(por_grupo.to_numpy()), np.sort(C.grupos_motor.loss_increase.to_numpy()), atol=1e-6)) if 'loss_increase' in C.grupos_motor.columns else None)
    ok = det['filas_positivas'] == pub['filas_positivas'] and det['filas_cero'] == pub['filas_cero'] and redondeo_igual(det['aumento_en_positivas'], pub['aumento_positivas'], 2) \
        and redondeo_igual(det['reduccion_en_ceros'], pub['reduccion_ceros'], 2) and redondeo_igual(det['saldo'], pub['saldo'], 2) and redondeo_igual(det['por_fold'][0], pub['fold0'], 2) \
        and redondeo_igual(det['cinco_grupos_mas_perjudicados'], pub['cinco_grupos'], 2)
    R.add('VN09', 'Ablaciones', 'Descomposición de la pérdida de autos nuevos B15 frente a B14: 265 filas positivas, 2.355 ceros, saldo, fold 0 y los cinco grupos más perjudicados, como en 021',
          'pasa' if ok else 'hallazgo', f"{det['filas_positivas']} positivas +{det['aumento_en_positivas']:.2f}; {det['filas_cero']} ceros −{det['reduccion_en_ceros']:.2f}; saldo {det['saldo']:+.2f}; fold0 {det['por_fold'][0]:+.2f}; cinco grupos {det['cinco_grupos_mas_perjudicados']:.2f}",
          'las cifras de 021', 'P1' if not ok else '', det)


# ----------------------------------------------------------------------------------------------- D. influencia y remuestreo
def pares_bootstrap(w, pares, seed=SEED, reps=REPS, objetivo=None, remove=None, distribuciones=None):
    """Replica paired_diagnostics de Codex: delta D², intervalo exploratorio por remuestreo de grupos y retirada de grupos favorables."""
    w = w.sort_values(KEY if all(c in w.columns for c in KEY) else ['line', 'row_id']).reset_index(drop=True)
    codes, groups = pd.factorize(w.group_id, sort=True)
    g = len(groups)
    n = np.bincount(codes, minlength=g).astype(float)
    y = (w.T0 if objetivo is None else w[objetivo]).to_numpy(float)
    sy = np.bincount(codes, weights=y, minlength=g); syroot = np.bincount(codes, weights=np.sqrt(y), minlength=g)
    modelos = sorted({m for p in pares for m in p})
    gl = {m: np.bincount(codes, weights=w[f'dev_{m}'].to_numpy(), minlength=g) for m in modelos}
    rng = np.random.default_rng(seed); digest = hashlib.sha256()
    dist = {p: [] for p in pares}
    for start in range(0, reps, 32):
        count = min(32, reps - start)
        draw = rng.integers(0, g, size=(count, g), dtype=np.int64)
        digest.update(draw.tobytes())
        ns = n[draw].sum(axis=1); ys = sy[draw].sum(axis=1)
        den = 8 * (np.sqrt(ns * ys) - syroot[draw].sum(axis=1))
        sums = {m: gl[m][draw].sum(axis=1) for m in modelos}
        for cand, ref in pares:
            dist[(cand, ref)].extend(((sums[ref] - sums[cand]) / den).tolist())
    denom = 8 * (np.sqrt(n.sum() * sy.sum()) - syroot.sum())
    remove = remove if remove is not None else min(g - 1, max(5, int(np.ceil(.001 * g))))
    out = {}
    for cand, ref in pares:
        adv = gl[ref] - gl[cand]
        excluded = np.argsort(-adv, kind='stable')[:remove]
        keep = np.ones(g, dtype=bool); keep[excluded] = False
        td = 8 * (np.sqrt(n[keep].sum() * sy[keep].sum()) - syroot[keep].sum())
        d = pd.Series(dist[(cand, ref)])
        if distribuciones is not None:
            distribuciones[(cand, ref)] = d.to_numpy()
        out[(cand, ref)] = dict(delta_D2=float(adv.sum() / denom), inferior95=float(d.quantile(.025)), superior95=float(d.quantile(.975)), grupos=int(g), retirados=int(remove),
                                delta_tras_retirar=float(adv[keep].sum() / td), mayor_grupo_favorable=float(adv.max() / denom))
    return out, digest.hexdigest()


def e_influencia(C: Corridas, R: Registro, salida: pathlib.Path):
    filas, fallos_rep, fallos_foro, n_foro = [], 0, 0, 0
    det = {}
    dists = {}
    for k, post in [('dev5', 'COD-S2-20261023-017'), ('dev6', 'COD-S2-20261024-019'), ('dev7', 'COD-S2-20261024-021')]:
        w = C.wide(k)
        w['market'] = 'emerging'
        pares = list(PUBLICADO[post]['pares'].keys())
        res, dig = pares_bootstrap(w, pares, distribuciones=dists)
        rep = {(p['candidate'], p['reference']): p for p in C.rep[k]['pairs']}
        det[k] = dict(draws_sha256=dig, pares={})
        decimales = {'COD-S2-20261023-017': 5, 'COD-S2-20261024-019': 8, 'COD-S2-20261024-021': 8}[post]
        for p, r in res.items():
            pr = rep.get(p)
            pub = PUBLICADO[post]['pares'][p]
            comp_rep = dict(delta_dif=abs(r['delta_D2'] - pr['delta_D2']), inferior_dif=abs(r['inferior95'] - pr['exploratory_lower95']), superior_dif=abs(r['superior95'] - pr['exploratory_upper95']),
                            retirar_dif=abs(r['delta_tras_retirar'] - pr['delta_after_removal']), retirados_igual=r['retirados'] == pr['removed_favorable_groups']) if pr else None
            if pr:
                fallos_rep += (comp_rep['delta_dif'] > 1e-9) + (comp_rep['inferior_dif'] > 1e-9) + (comp_rep['superior_dif'] > 1e-9) + (comp_rep['retirar_dif'] > 1e-9) + (not comp_rep['retirados_igual'])
            dec = decimales
            comp_foro = [redondeo_igual(r['delta_D2'], pub[0], dec), redondeo_igual(r['inferior95'], pub[1], dec), redondeo_igual(r['superior95'], pub[2], dec), redondeo_igual(r['delta_tras_retirar'], pub[3], dec)]
            n_foro += 4; fallos_foro += sum(not x for x in comp_foro)
            det[k]['pares'][f'{p[0]} / {p[1]}'] = dict(recalculado=r, informe=pr, publicado=pub, coincide_informe=comp_rep, coincide_foro=comp_foro)
            filas.append(dict(corrida=k, candidato=p[0], referencia=p[1], delta_D2=r['delta_D2'], inferior95=r['inferior95'], superior95=r['superior95'], delta_tras_retirar_31=r['delta_tras_retirar'],
                              delta_informe=pr['delta_D2'] if pr else None, inferior_informe=pr['exploratory_lower95'] if pr else None, superior_informe=pr['exploratory_upper95'] if pr else None,
                              retirar_informe=pr['delta_after_removal'] if pr else None, publicado=str(pub)))
    pd.DataFrame(filas).to_csv(salida / 'tablas' / 'pares_recalculados.csv', index=False)
    pd.DataFrame({f'{a} / {b}': v for (a, b), v in dists.items()}).to_csv(salida / 'tablas' / 'remuestreo_pares.csv', index=False)
    det['fallos_frente_al_informe'] = fallos_rep; det['fallos_frente_al_foro'] = fallos_foro; det['cifras_del_foro'] = n_foro
    R.add('VN10', 'Influencia', 'Once pares del foro (017, 019, 021): delta D², intervalo exploratorio al 95 % con 2.000 remuestreos de componentes (semilla 2026102302) y delta tras retirar 31 grupos favorables, replicados',
          'pasa' if fallos_rep == 0 and fallos_foro == 0 else 'hallazgo', f'{fallos_rep} discrepancias con los informes; {fallos_foro} de {n_foro} cifras del foro no coinciden', '0 y 0', 'P1' if (fallos_rep or fallos_foro) else '', det)


# ----------------------------------------------------------------------------------------------- E. cola y mecanismo
def f_cola(C: Corridas, R: Registro):
    st, base = C.cola_stress, C.cola_base
    b = base.set_index(['model_id', 'row_id'])
    det, fallos = {}, 0
    esc = {s['line'] + '_' + str(s['fold']): s['Z'] for s in C.rep['cola']['scales']}
    for sid, part in st.groupby('stress_id'):
        esc_id, mid = sid.split('_', 1)
        p = part.set_index('row_id')
        bb = b.loc[mid].loc[p.index]
        d = dict(filas=len(p), max_dif_prediction_frente_a_base=float((p.prediction - bb.prediction).abs().max()),
                 ratio_tasa_min=float((p.annual_rate / bb.annual_rate).min()), ratio_tasa_max=float((p.annual_rate / bb.annual_rate).max()),
                 e_por_ratio_igual_a_base=float(((p.effective_exposure * (p.annual_rate / bb.annual_rate)) - p.base_effective_exposure).abs().max()))
        m_all = metr(p.T0, p.prediction); m_base = metr(bb.T0, bb.prediction)
        d.update(D2=m_all['D2'], D2_base=m_base['D2'], D2_dif=m_all['D2'] - m_base['D2'], nominal=float(p.conditional_nominal_2023.sum()), nominal_base=float((bb.annual_rate * bb.exposure).sum()),
                 observado_predicho_dif=float(p.prediction.sum() - bb.prediction.sum()))
        d['nominal_cambio_rel'] = d['nominal'] / d['nominal_base'] - 1
        if esc_id == 'T10R':
            Z = (p.line.astype(str) + '_' + p.fold.astype(int).astype(str)).map(esc).to_numpy(float)
            d['tasa_igual_a_Z_por_base'] = float((p.annual_rate - Z * bb.annual_rate).abs().max())
            d['e_igual_a_base_entre_Z'] = float((p.effective_exposure - bb['e_cost_mix_1.0'] / Z).abs().max())
            fallos += (d['max_dif_prediction_frente_a_base'] > 1e-9) + (abs(d['D2_dif']) > 1e-12) + (d['tasa_igual_a_Z_por_base'] > 1e-9) + (d['e_igual_a_base_entre_Z'] > 1e-9)
        det[sid] = d
    pub = PUBLICADO['COD-S2-20261024-024']
    comp = {}
    for mid, t in pub['tabla'].items():
        rec = dict(D2_base=det[f'T10F_{mid}']['D2_base'], D2_T10F=det[f'T10F_{mid}']['D2'], D2_T10R=det[f'T10R_{mid}']['D2'], nom_base_M=det[f'T10F_{mid}']['nominal_base'] / 1e6,
                   nom_T10F_M=det[f'T10F_{mid}']['nominal'] / 1e6, nom_T10R_M=det[f'T10R_{mid}']['nominal'] / 1e6)
        chk = {kk: redondeo_igual(rec[kk], t[kk], 8 if kk.startswith('D2') else 4) for kk in t}
        comp[mid] = dict(publicado=t, recalculado=rec, coincide=chk)
        fallos += sum(not v for v in chk.values())
    b14 = pub['B14']
    rec14 = dict(T10R_delta_CU=det['T10R_W2-B14']['nominal'] - det['T10R_W2-B14']['nominal_base'], T10R_pct=det['T10R_W2-B14']['nominal_cambio_rel'],
                 T10F_delta_CU=det['T10F_W2-B14']['nominal'] - det['T10F_W2-B14']['nominal_base'], T10F_pct=det['T10F_W2-B14']['nominal_cambio_rel'],
                 T10F_D2_delta=det['T10F_W2-B14']['D2_dif'], T10F_obs_delta_CU=det['T10F_W2-B14']['observado_predicho_dif'], T10R_max_dif=det['T10R_W2-B14']['max_dif_prediction_frente_a_base'])
    chk14 = dict(T10R_delta_CU=abs(rec14['T10R_delta_CU'] - b14['T10R_delta_CU']) < 1, T10R_pct=redondeo_igual(rec14['T10R_pct'], b14['T10R_pct'], 5), T10F_delta_CU=abs(rec14['T10F_delta_CU'] - b14['T10F_delta_CU']) < 1,
                 T10F_pct=redondeo_igual(rec14['T10F_pct'], b14['T10F_pct'], 5), T10F_D2_delta=redondeo_igual(rec14['T10F_D2_delta'], b14['T10F_D2_delta'], 8), T10F_obs_delta_CU=abs(rec14['T10F_obs_delta_CU'] - b14['T10F_obs_delta_CU']) < 1,
                 T10R_max_dif=rec14['T10R_max_dif'] < 1e-9)
    fallos += sum(not v for v in chk14.values())
    det['frente_al_foro_024'] = dict(tabla=comp, B14=dict(publicado=b14, recalculado=rec14, coincide=chk14))
    det['Z_por_celda'] = esc
    R.add('VN11', 'Cola', 'Sensibilidad de cola (024): T10R es la identidad tasa × Z y e / Z con predicción y D² idénticos; T10F y los nominales condicionados de 2023 coinciden con la tabla publicada',
          'pasa' if fallos == 0 else 'hallazgo', f"{fallos} fallos; B14: T10R {rec14['T10R_pct']:+.3%} nominal, T10F {rec14['T10F_pct']:+.3%}, D² +{rec14['T10F_D2_delta']:.8f}", 'identidad exacta y tabla', 'P1' if fallos else '', det)


def g_mecanismo(C: Corridas, R: Registro):
    m = C.mec
    det, fallos = {}, 0
    for sid, p in m.groupby('stress_id'):
        esc, mid = p.scenario.iloc[0], p.model_id.iloc[0]
        b = {'R075': 0.75, 'R125': 1.25, 'L1': 1.0}[esc]
        d = dict(filas=len(p), T_s_igual_a_T0_mas_b_menos_1_por_reserva=float((p.T_s - (p.T0 + (b - 1) * p.reserve)).abs().max()), respuesta_total=float(p.T_s.sum()))
        mm = metr(p.T_s, p.prediction)
        d.update(D2=mm['D2'], AE=mm['AE'], predicho=mm['predicho'], nominal=float(p.conditional_nominal_2023.sum()))
        base = C.cola_base[C.cola_base.model_id == mid]
        d['nominal_base'] = float((base.annual_rate * base.exposure).sum()); d['cambio_rel'] = d['nominal'] / d['nominal_base'] - 1
        fallos += d['T_s_igual_a_T0_mas_b_menos_1_por_reserva'] > 1e-9
        det[sid] = d
    comp = []
    for esc, mid, resp_M, D2, AE, nom_M, pct in PUBLICADO['COD-S2-20261024-026']['tabla']:
        d = det[f'{esc}_{mid}']
        chk = dict(respuesta=redondeo_igual(d['respuesta_total'] / 1e6, resp_M, 4), D2=redondeo_igual(d['D2'], D2, 6), AE=redondeo_igual(d['AE'], AE, 3), nominal=redondeo_igual(d['nominal'] / 1e6, nom_M, 4), cambio=redondeo_igual(d['cambio_rel'], pct, 5))
        comp.append(dict(escenario=esc, modelo=mid, publicado=dict(respuesta_M=resp_M, D2=D2, AE=AE, nominal_M=nom_M, cambio=pct), recalculado=dict(respuesta_M=d['respuesta_total'] / 1e6, D2=d['D2'], AE=d['AE'], nominal_M=d['nominal'] / 1e6, cambio=d['cambio_rel']), coincide=chk))
        fallos += sum(not v for v in chk.values())
    det['frente_al_foro_026'] = comp
    # L1 / B14 par con la nula de T0
    w = pd.DataFrame({'line': m[m.stress_id == 'L1_W2-B14'].line.to_numpy(), 'row_id': m[m.stress_id == 'L1_W2-B14'].row_id.to_numpy(), 'group_id': m[m.stress_id == 'L1_W2-B14'].group_id.to_numpy(),
                      'T0': m[m.stress_id == 'L1_W2-B14'].T0.to_numpy(), 'dev_L1_W2-B14': m[m.stress_id == 'L1_W2-B14'].unit_deviance.to_numpy()})
    w['market'] = 'emerging'
    bse = C.cola_base[C.cola_base.model_id == 'W2-B14'].set_index('row_id')
    w['dev_W2-B14'] = bse.loc[w.row_id, 'unit_deviance'].to_numpy()
    # el remuestreo de mecanismo recorre 12 pares con la misma secuencia de sorteos; la secuencia no depende del par, así que basta un par
    dists = {}
    res, dig = pares_bootstrap(w, [('L1_W2-B14', 'W2-B14')], remove=31, distribuciones=dists)
    pd.DataFrame({'L1_W2-B14 / W2-B14': dists[('L1_W2-B14', 'W2-B14')]}).to_csv(C.salida / 'tablas' / 'remuestreo_L1.csv', index=False)
    def buscar_pares(o, acc):
        if isinstance(o, dict):
            if 'candidate' in o and 'reference' in o:
                acc.append(o)
            else:
                for v in o.values():
                    buscar_pares(v, acc)
        elif isinstance(o, list):
            for v in o:
                buscar_pares(v, acc)
        return acc
    pr = [p for p in buscar_pares(C.rep['mecanismo'], []) if p.get('candidate') == 'L1_W2-B14' and p.get('reference') == 'W2-B14']
    pub = PUBLICADO['COD-S2-20261024-026']['pares'][('L1_W2-B14', 'W2-B14')]
    r = res[('L1_W2-B14', 'W2-B14')]
    chk = [redondeo_igual(r['delta_D2'], pub[0], 8), redondeo_igual(r['inferior95'], pub[1], 8), redondeo_igual(r['superior95'], pub[2], 8), redondeo_igual(r['delta_tras_retirar'], pub[3], 8)]
    fallos += sum(not x for x in chk)
    det['par_L1_B14'] = dict(recalculado=r, publicado=pub, coincide=chk, informe=pr[0] if pr else 'buscar en diagnostics', draws_sha256=dig)
    # reserva 2023
    base = C.cola_base[C.cola_base.model_id == 'W2-B00']
    res2023 = float(base.reserve.sum()); neto2023 = float(base.T0.sum())
    tg = C.tgt[~C.tgt.is_test.astype(bool)]
    det['reserva'] = dict(reserva_2023=res2023, neto_2023=neto2023, cuota_2023=res2023 / neto2023, publicado=PUBLICADO['COD-S2-20261024-026']['reserva_2023'],
                          reserva_2023_contenidos=float(base[base.line == 'contents'].reserve.sum()),
                          reserva_dos_anios=float(tg.reserve.sum()), T0_dos_anios=float(tg.T0.sum()), cuota_dos_anios=float(tg.reserve.sum() / tg.T0.sum()),
                          reserva_2024=float(tg[tg.year == 2024].reserve.sum()), T0_2024=float(tg[tg.year == 2024].T0.sum()))
    okr = redondeo_igual(res2023, 1427914.85, 2) and redondeo_igual(res2023 / neto2023, 0.09335, 5) and redondeo_igual(neto2023, 15297103.84, 2) and det['reserva']['reserva_2023_contenidos'] == 0
    fallos += not okr
    R.add('VN12', 'Mecanismo', 'Reservas y reporte tardío (026): T_s = T0 + (b − 1) × reserva exacto, tabla de nueve filas (respuesta, D² bajo su objetivo, A/E, nominal y cambio) y par L1/B14 con remuestreo replicados; reserva de 2023 1.427.914,85 CU (9,335 %) frente al 17,8 % de los dos años',
          'pasa' if fallos == 0 else 'hallazgo', f"{fallos} fallos; reserva 2023 {res2023:,.2f} CU = {res2023 / neto2023:.3%} del neto; dos años {det['reserva']['cuota_dos_anios']:.3%}", 'tabla y par', 'P1' if fallos else '', det)


# ----------------------------------------------------------------------------------------------- F. replay por reajuste de B13 y B14
def h_replay_glm(C: Corridas, R: Registro):
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import TweedieRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    spec = [mo for mo in C.plan['dev5']['models'] if mo['id'] == 'W2-B13'][0]
    feats = spec['features_by_line']; params = spec['params']
    w = C.wide('dev6').set_index('row_id')
    cap = C.cap56.set_index('row_id')
    det, fallos = {}, 0
    t0 = time.time()
    for l in LINES:
        f0 = pq.read_table(C.f0_dir / f'F0_{l}.parquet', columns=['row_id'] + feats[l]['all']).to_pandas().set_index('row_id')
        wl = w[w.line == l]
        X = C.inputs[l].loc[wl.index, feats[l]['all']].copy()
        def iguales(a, b):
            if a.dtype.kind in 'fc' or b.dtype.kind in 'fc':
                return bool(((a.isna() & b.isna()) | np.isclose(a.astype(float), b.astype(float), equal_nan=True)).all())
            return bool(((a.isna() & b.isna()) | (a.astype(str) == b.astype(str))).all())
        resultados = {'inputs_iguales_a_F0': bool(all(iguales(X[c], f0.loc[wl.index, c]) for c in feats[l]['all']))}
        E = {f: C.links[(l, f)].loc[wl.index, 'e_cost_mix_1.0'].to_numpy() for f in range(5)}
        for variante in ['W2-B13', 'W2-B14']:
            Xv = X.copy()
            if variante == 'W2-B14' and l != 'motor':
                filas = [r for r in cap.index if r in Xv.index]
                Xv.loc[filas, 'x_log_sum_insured'] = np.log(cap.loc[filas, 'capital_divided'].to_numpy(float))
            pred = np.full(len(wl), np.nan)
            convergencias = []
            coef_nb = []
            for f in sorted(wl.fold.unique()):
                fit = (wl.fold != f).to_numpy(); val = ~fit
                e = E[int(f)]; y = wl.T0.to_numpy() / e; sw = np.sqrt(e)
                pre = ColumnTransformer([('num', Pipeline([('imp', SimpleImputer(strategy='median', keep_empty_features=True)), ('sc', StandardScaler())]), feats[l]['numeric']),
                                         ('cat', OneHotEncoder(drop='first', min_frequency=50, max_categories=40, handle_unknown='ignore'), feats[l]['categorical'])])
                glm = TweedieRegressor(power=params['power'], alpha=params['alpha'], link=params['link'], solver=params['solver'], max_iter=params['max_iter'], tol=params['tol'], fit_intercept=params['fit_intercept'])
                pipe = Pipeline([('pre', pre), ('glm', glm)])
                Xf = Xv.copy()
                for c in feats[l]['categorical']:
                    Xf[c] = Xf[c].astype(object).where(Xf[c].notna(), '__MISSING__').astype(str)
                pipe.fit(Xf[fit], y[fit], glm__sample_weight=sw[fit])
                pred[val] = pipe.predict(Xf[val]) * e[val]
                convergencias.append(int(getattr(pipe.named_steps['glm'], 'n_iter_', -1)))
                if variante == 'W2-B13':
                    j = feats[l]['numeric'].index('x_new_business')
                    escala = pipe.named_steps['pre'].named_transformers_['num'].named_steps['sc'].scale_[j]
                    coef_nb.append(float(pipe.named_steps['glm'].coef_[j] / escala))
            ref = wl[f'pred_{variante}'].to_numpy()
            rel = np.abs(pred / ref - 1)
            m_mio = metr(wl.T0.to_numpy(), pred); m_ref = metr(wl.T0.to_numpy(), ref)
            resultados[variante] = dict(max_dif_rel=float(rel.max()), p99_dif_rel=float(np.quantile(rel, 0.99)), mediana_dif_rel=float(np.median(rel)), D2_ramo_replay=m_mio['D2'], D2_ramo_oof=m_ref['D2'],
                                        predicho_replay=m_mio['predicho'], predicho_oof=m_ref['predicho'], iteraciones=convergencias, filas=int(len(wl)))
            if coef_nb:
                resultados[variante]['coeficiente_negocio_sin_escalar_por_fold'] = coef_nb
                resultados[variante]['coeficiente_negocio_rango'] = (min(coef_nb), max(coef_nb))
            fallos += resultados[variante]['max_dif_rel'] > 1e-4
        fallos += not resultados['inputs_iguales_a_F0']
        det[l] = resultados
    det['segundos'] = round(time.time() - t0, 1)
    det['receta'] = dict(features=feats, params=params, preprocesado=dict(numerico=spec['numeric'], categorico=spec['categorical']), respuesta='T0 / C0', peso='sqrt(C0)', ajuste='folds distintos de k, 2023')
    peor = max(det[l][v]['max_dif_rel'] for l in LINES for v in ['W2-B13', 'W2-B14'])
    rango = det['motor']['W2-B13']['coeficiente_negocio_rango']
    det['coeficiente_negocio_motor_publicado_021'] = PUBLICADO['COD-S2-20261024-021']['coeficiente_negocio_precio']
    det['coeficiente_negocio_motor_coincide'] = redondeo_igual(rango[0], 0.714, 3) and redondeo_igual(rango[1], 0.911, 3)
    fallos += not det['coeficiente_negocio_motor_coincide']
    R.add('VN13', 'Replay', 'Reajuste independiente de B13 y B14 (GLM Tweedie 1,5 log sin penalización, seis variables por ramo, imputación y OHE solo con el fold de ajuste, enlace C0 del fold): predicciones OOF reproducidas; inputs de Codex iguales a F0',
          'pasa' if fallos == 0 else 'hallazgo', f'máxima diferencia relativa {peor:.2e} en 30 GLM', '< 1e-4', 'P1' if fallos else '', det)


# ----------------------------------------------------------------------------------------------- G. estabilidad
def j_estabilidad(C: Corridas, R: Registro):
    cel = R.detalle['VN07']['por_celda']
    mios = R.detalle['VN07']['c_de_Claude_todo_2023']
    det = {}
    for l in LINES:
        t = [c for c in cel if c['ramo'] == l]
        det[l] = dict(c_por_fold=[c['c_oof'] for c in t], rel_em_por_fold=[c['rel_em'] for c in t], rel_cred_por_fold=[c['rel_cred'] for c in t], Z_f_por_fold=[c['Z_f'] for c in t],
                      c_min=min(c['c_oof'] for c in t), c_max=max(c['c_oof'] for c in t), rel_em_min=min(c['rel_em'] for c in t), rel_em_max=max(c['rel_em'] for c in t),
                      rel_cred_min=min(c['rel_cred'] for c in t), rel_cred_max=max(c['rel_cred'] for c in t), c_claude_todo_2023=mios[l],
                      c_claude_dentro_del_rango=bool(min(c['c_oof'] for c in t) <= mios[l] <= max(c['c_oof'] for c in t)))
    # siniestros de nuevo negocio por ramo en 2023 (pocos en hogar): cuenta desde la base
    w = C.wide('dev5')
    nbrows = w[w.x_new_business.astype(int) == 1]
    det['nuevo_negocio_2023'] = {l: dict(filas=int((nbrows.line == l).sum()), filas_con_coste=int(((nbrows.line == l) & (nbrows.T0 > 0)).sum()), coste=float(nbrows[nbrows.line == l].T0.sum())) for l in LINES}
    amplitud = {l: det[l]['c_max'] / det[l]['c_min'] for l in LINES}
    det['amplitud_c_max_sobre_min'] = amplitud
    R.add('VN14', 'Estabilidad', 'La relatividad creíble es estable entre folds (la fija el desarrollado) pero el factor c = creíble / emergente oscila con el fold en hogar porque la relatividad emergente depende de pocos siniestros de nuevo negocio',
          'informativo', f"c por ramo entre {det['motor']['c_min']:.3f}–{det['motor']['c_max']:.3f} (autos), {det['buildings']['c_min']:.3f}–{det['buildings']['c_max']:.3f} (edificios), {det['contents']['c_min']:.3f}–{det['contents']['c_max']:.3f} (contenidos); creíble {det['buildings']['rel_cred_min']:.3f}–{det['buildings']['rel_cred_max']:.3f} en edificios",
          '', '', det)
    # VN17 D² por fold
    det = {}
    for k, modelos in [('dev5', ['W2-B00', 'W2-B08', 'W2-B12', 'W2-B13']), ('dev7', ['W2-B14', 'W2-B15', 'W2-B16', 'W2-B17', 'W2-B18'])]:
        w = C.wide(k)
        for mo in modelos:
            det[mo] = {}
            for f in range(5):
                m = (w.fold == f).to_numpy()
                mm = metr(w.T0.to_numpy()[m], w[f'pred_{mo}'].to_numpy()[m])
                det[mo][f'fold{f}'] = dict(D2=mm['D2'], AE=mm['AE'], filas=mm['filas'])
            det[mo]['D2_min'] = min(det[mo][f'fold{f}']['D2'] for f in range(5)); det[mo]['D2_max'] = max(det[mo][f'fold{f}']['D2'] for f in range(5))
    orden_por_fold = {f'fold{f}': sorted(det, key=lambda mo: -det[mo][f'fold{f}']['D2']) for f in range(5)}
    det['orden_por_fold'] = orden_por_fold
    det['B13_supera_a_B00_en_folds'] = int(sum(det['W2-B13'][f'fold{f}']['D2'] > det['W2-B00'][f'fold{f}']['D2'] for f in range(5)))
    det['B08_supera_a_B13_en_folds'] = int(sum(det['W2-B08'][f'fold{f}']['D2'] > det['W2-B13'][f'fold{f}']['D2'] for f in range(5)))
    R.add('VN15', 'Estabilidad', 'D² por fold de B00, B08, B12, B13 y B14–B18: la dispersión entre folds es mayor que las diferencias entre recetas; el orden cambia de un fold a otro', 'informativo',
          f"B13 > B00 en {det['B13_supera_a_B00_en_folds']} de 5 folds; B08 > B13 en {det['B08_supera_a_B13_en_folds']} de 5; D² de B13 por fold {det['W2-B13']['D2_min']:.3f}–{det['W2-B13']['D2_max']:.3f}", '', '', det)


# ----------------------------------------------------------------------------------------------- I. ampliación: 028–033
def k_mezcla(C: Corridas, R: Registro):
    mx = C.mix
    base = C.cola_base.set_index(['model_id', 'row_id'])
    pub = PUBLICADO['COD-S2-20261024-028']
    det, fallos = {}, 0
    for sid, p in mx.groupby('stress_id'):
        var, mid = sid.split('_', 1)
        pp = p.set_index('row_id'); bb = base.loc[mid].loc[pp.index]
        mm = metr(pp.T0, pp.prediction)
        d = dict(D2=mm['D2'], AE=mm['AE'], nominal=float(pp.conditional_nominal_2023.sum()), nominal_base=float((bb.annual_rate * bb.exposure).sum()))
        d['cambio_rel'] = d['nominal'] / d['nominal_base'] - 1
        nb = pp.x_new_business.astype(int) == 1
        for l in LINES:
            m = (pp.line == l) & nb
            d[f'{l}_nb_D2'] = metr(pp.T0[m], pp.prediction[m])['D2']
        ratio = pp.effective_exposure / bb['e_cost_mix_1.0']
        d['reduccion_max_motor_nb'] = float(1 - ratio[nb & (pp.line == 'motor')].min())
        det[sid] = d
    comp = []
    for var, mid, D2, AE, nom, pct in pub['tabla']:
        d = det[f'{var}_{mid}']
        chk = dict(D2=redondeo_igual(d['D2'], D2, 8), AE=redondeo_igual(d['AE'], AE, 3), nominal=redondeo_igual(d['nominal'] / 1e6, nom, 6), cambio=redondeo_igual(d['cambio_rel'], pct, 5))
        comp.append(dict(variante=var, modelo=mid, publicado=dict(D2=D2, AE=AE, nominal_M=nom, cambio=pct), recalculado=dict(D2=d['D2'], AE=d['AE'], nominal_M=d['nominal'] / 1e6, cambio=d['cambio_rel']), coincide=chk))
        fallos += sum(not v for v in chk.values())
    det['frente_al_foro_028'] = comp
    seg = dict(motor_nb=dict(MIXF=det['MIXF_W2-B14']['motor_nb_D2'], MIXFS=det['MIXFS_W2-B14']['motor_nb_D2'], publicado=pub['B14_motor_nb_D2']),
               buildings_nb=dict(MIXFS=det['MIXFS_W2-B14']['buildings_nb_D2'], publicado=pub['B14_buildings_nb_D2']), contents_nb=dict(MIXFS=det['MIXFS_W2-B14']['contents_nb_D2'], publicado=pub['B14_contents_nb_D2']))
    okseg = redondeo_igual(seg['motor_nb']['MIXF'], -0.010191, 6) and redondeo_igual(seg['motor_nb']['MIXFS'], -0.011551, 6) and redondeo_igual(seg['buildings_nb']['MIXFS'], 0.050177, 6) and redondeo_igual(seg['contents_nb']['MIXFS'], 0.153679, 6)
    det['segmentos_B14'] = seg
    det['MIXFS_B14_reduccion_max_motor_nb'] = det['MIXFS_W2-B14']['reduccion_max_motor_nb']
    okred = redondeo_igual(det['MIXFS_B14_reduccion_max_motor_nb'], 0.0447, 4)
    fallos += (not okseg) + (not okred)
    # pares con remuestreo: doce, misma semilla, nula de T0
    w = mx[['line', 'row_id', 'group_id', 'T0', 'stress_id', 'unit_deviance']].copy()
    wide = w.pivot(index='row_id', columns='stress_id', values='unit_deviance').add_prefix('dev_')
    first = w.drop_duplicates('row_id').set_index('row_id')[['line', 'group_id', 'T0']]
    wide = first.join(wide).reset_index(); wide['market'] = 'emerging'
    for mid in ['W2-B00', 'W2-B12', 'W2-B14']:
        wide[f'dev_{mid}'] = base.loc[mid].loc[wide.row_id, 'unit_deviance'].to_numpy()
    pares = list(pub['pares'].keys())
    res, dig = pares_bootstrap(wide, pares, remove=31)
    pares_det, fallos_p = {}, 0
    for p_, r in res.items():
        pb = pub['pares'][p_]
        chk = [redondeo_igual(r['delta_D2'], pb[0], 8), redondeo_igual(r['inferior95'], pb[1], 8), redondeo_igual(r['superior95'], pb[2], 8), redondeo_igual(r['delta_tras_retirar'], pb[3], 8)]
        fallos_p += sum(not x for x in chk)
        pares_det[f'{p_[0]} / {p_[1]}'] = dict(recalculado=r, publicado=pb, coincide=chk)
    det['pares'] = pares_det; det['pares_fallos'] = fallos_p; det['draws_sha256'] = dig
    fallos += fallos_p
    R.add('VN18', 'Ampliación', 'Mezcla de C0 por peril y negocio (028): tabla de seis variantes (D², A/E, nominal, cambio), D² de nuevo negocio de B14, reducción máxima de exposición efectiva en autos nuevos (4,47 %) y los doce pares con remuestreo',
          'pasa' if fallos == 0 else 'hallazgo', f"{fallos} fallos; MIXFS reduce la exposición efectiva de autos nuevos hasta {det['MIXFS_B14_reduccion_max_motor_nb']:.2%}; {12 - fallos_p} de 12 pares iguales", 'tabla, segmentos y pares', 'P1' if fallos else '', det)


def l_escasez(C: Corridas, R: Registro):
    """Siniestros por celda de ajuste recalculados desde la asignación canónica de la base."""
    a = C.audit[(C.audit.status != 'repudiated') & C.audit.row_id.notna()].copy()
    w = C.wide('dev5').set_index('row_id')
    a = a[a.row_id.isin(w.index)]
    a['fold'] = a.row_id.map(w.fold); a['nb'] = a.row_id.map(w.x_new_business).astype(int)
    pub = PUBLICADO['COD-S2-20261024-028']
    det, fallos = {}, 0
    rangos = {}
    for (l, nb), (lo, hi) in pub['siniestros_ajuste'].items():
        cnt = [int(((a.line == l) & (a.nb == nb) & (a.fold != f)).sum()) for f in range(5)]
        rangos[f'{l}_nb{nb}'] = dict(por_fold_de_ajuste=cnt, min=min(cnt), max=max(cnt), publicado=(lo, hi), coincide=(min(cnt) == lo and max(cnt) == hi))
        fallos += not rangos[f'{l}_nb{nb}']['coincide']
    det['siniestros_de_ajuste'] = rangos
    perils = {}
    for (l, per), (lo, hi) in pub['siniestros_nb_por_peril'].items():
        cnt = [int(((a.line == l) & (a.nb == 1) & (a.peril == per) & (a.fold != f)).sum()) for f in range(5)]
        perils[f'{l}_{per}'] = dict(por_fold_de_ajuste=cnt, min=min(cnt), max=max(cnt), publicado=(lo, hi), coincide=(min(cnt) == lo and max(cnt) == hi))
        fallos += not perils[f'{l}_{per}']['coincide']
    det['siniestros_nuevos_por_peril'] = perils
    det['incendio_edificios_nuevos_2023'] = int(((a.line == 'buildings') & (a.nb == 1) & (a.peril == 'fire')).sum())
    det['celdas_cero'] = 5 if det['incendio_edificios_nuevos_2023'] == 0 else 'no son cinco'
    unicos = {f'{l}_nb{nb}': int(((a.line == l) & (a.nb == nb)).sum()) for (l, nb) in PUBLICADO['COD-S2-20261024-031']['siniestros_unicos']}
    det['siniestros_unicos_2023'] = dict(recalculado=unicos, publicado={f'{l}_nb{nb}': v for (l, nb), v in PUBLICADO['COD-S2-20261024-031']['siniestros_unicos'].items()})
    det['siniestros_unicos_coinciden'] = all(unicos[k] == v for k, v in det['siniestros_unicos_2023']['publicado'].items())
    det['siniestros_2023_total'] = int(len(a)); det['siniestros_2023_publicado'] = PUBLICADO['COD-S2-20261024-031']['siniestros_deduplicados']
    fallos += (not det['siniestros_unicos_coinciden']) + (det['siniestros_2023_total'] != det['siniestros_2023_publicado']) + (det['celdas_cero'] != 5)
    cel = C.celdas
    det['mayor_peso_un_siniestro_informe'] = {k: float(cel[(cel.line == l) & (cel.business == 1)].max_weighted_cost_share.max()) for k, l in [('buildings_nb', 'buildings'), ('contents_nb', 'contents')]}
    det['mayor_peso_publicado'] = pub['mayor_peso_un_siniestro']
    det['celdas_cero_en_informe'] = int(((cel.business == 1) & (cel.claims == 0)).sum())
    det['celdas_cero_en_informe_son_incendio_edificios'] = bool((cel[(cel.business == 1) & (cel.claims == 0)].peril == 'fire').all() and (cel[(cel.business == 1) & (cel.claims == 0)].line == 'buildings').all())
    fallos += (det['celdas_cero_en_informe'] != 5) + (not det['celdas_cero_en_informe_son_incendio_edificios'])
    R.add('VN19', 'Ampliación', 'Escasez del nuevo negocio (028 y 031): siniestros por celda de ajuste y por peril, siniestros únicos de 2023 por ramo y negocio (4.567), y las cinco celdas de frecuencia cero (incendio en edificios nuevos) recalculados desde la asignación canónica',
          'pasa' if fallos == 0 else 'hallazgo', f"{fallos} fallos; {det['siniestros_2023_total']} siniestros de 2023; incendio en edificios nuevos: {det['incendio_edificios_nuevos_2023']}", 'rangos de 028 y cifras de 031', 'P1' if fallos else '', det)


def m_coberturas(C: Corridas, R: Registro):
    a = C.audit[(C.audit.status != 'repudiated') & C.audit.row_id.notna()].copy()
    w = C.wide('dev5').set_index('row_id')
    a23 = a[a.row_id.isin(w.index)].copy()
    pol = C.pol.set_index('row_id')
    a23['cover_type'] = a23.row_id.map(pol.cover_type); a23['ad'] = a23.row_id.map(pol.accidental_damage_cover)
    pub = PUBLICADO['COD-S2-20261024-033']
    det, fallos = {}, 0
    am = a23[a23.line == 'motor']
    fuera_motor = am[((am.peril.isin(['own_damage', 'glass_hail'])) & (am.cover_type != 'comprehensive')) | ((am.peril == 'theft') & ~am.cover_type.isin(['comprehensive', 'third_party_fire_theft']))]
    det['autos_fuera_de_mascara_2023'] = int(len(fuera_motor))
    for l in ['buildings', 'contents']:
        f = a23[(a23.line == l) & (a23.peril == 'accidental_damage') & (~a23.ad.astype(bool))]
        pos = f[(f.status == 'closed') & (f.T0_cents > 0)]
        det[f'{l}_ad_fuera'] = dict(todos=int(len(f)), cerrados_con_coste=int(len(pos)), neto_cerrados_con_coste=float(pos.T0_cents.sum() / 100), estados=f.status.value_counts().to_dict(), publicado=pub['fuera_mascara_hogar'][l])
        fallos += (det[f'{l}_ad_fuera']['cerrados_con_coste'] != pub['fuera_mascara_hogar'][l][0]) + (not redondeo_igual(det[f'{l}_ad_fuera']['neto_cerrados_con_coste'], pub['fuera_mascara_hogar'][l][1], 2))
    fallos += det['autos_fuera_de_mascara_2023'] != 0
    # conciliación con VE42 de la validación de datos (23 de 122 y 47 de 335 en los dos años, todos los estados)
    todo = C.audit[(C.audit.status != 'repudiated') & C.audit.row_id.notna()].copy()
    todo['ad'] = todo.row_id.map(pol.accidental_damage_cover)
    det['VE42_dos_anios_todos_los_estados'] = {l: int(((todo.line == l) & (todo.peril == 'accidental_damage') & (~todo.ad.astype(bool))).sum()) for l in ['buildings', 'contents']}
    det['lectura'] = 'VE42 cuenta los siniestros aceptados de daño accidental sin cobertura en 2023 y 2024 con cualquier estado; 033 cuenta los de 2023 cerrados con coste positivo: 23 → 6 y 47 → 24'
    # exposición nominal retenida por la máscara, por ramo, negocio y fold de ajuste, frente a la tabla de denominadores de Codex
    tg = C.tgt[(C.tgt.year == 2023) & (~C.tgt.is_test.astype(bool))].set_index('row_id')
    w['exp_nominal'] = tg.loc[w.index, 'exposure']
    w['cover_type'] = pol.loc[w.index, 'cover_type']; w['ad'] = pol.loc[w.index, 'accidental_damage_cover']
    dn = C.denom
    comp, difs = [], []
    for l, per, mask in [('motor', 'own_damage', w.cover_type == 'comprehensive'), ('motor', 'glass_hail', w.cover_type == 'comprehensive'), ('motor', 'theft', w.cover_type.isin(['comprehensive', 'third_party_fire_theft'])),
                         ('buildings', 'accidental_damage', w.ad.astype(bool)), ('contents', 'accidental_damage', w.ad.astype(bool))]:
        for nb in [0, 1]:
            for f in range(5):
                fit = (w.line == l) & (w.fold != f) & (w.x_new_business.astype(int) == nb)
                nom_all = float(w.exp_nominal[fit].sum()); nom_cand = float(w.exp_nominal[fit & mask].sum())
                fila = dn[(dn.line == l) & (dn.peril == per) & (dn.business == nb) & (dn.fold == f)]
                ref_all, ref_cand = (float(fila.nominal_all.iloc[0]), float(fila.nominal_candidate.iloc[0])) if len(fila) else (np.nan, np.nan)
                difs.append(max(abs(nom_all - ref_all), abs(nom_cand - ref_cand)))
                comp.append(dict(ramo=l, peril=per, negocio=nb, fold=f, nominal_todo=nom_all, nominal_mascara=nom_cand, cuota_nominal=nom_cand / nom_all, informe_todo=ref_all, informe_mascara=ref_cand,
                                 cuota_conteo_informe=float(fila.count_retained_fraction.iloc[0]) if len(fila) else None))
    det['denominadores_nominales_max_dif'] = float(np.nanmax(difs))
    fallos += det['denominadores_nominales_max_dif'] > 1e-6
    tabla = pd.DataFrame(comp)
    det['cuota_nominal_retenida_rango'] = {f'{l}_{per}': (float(tabla[(tabla.ramo == l) & (tabla.peril == per)].cuota_nominal.min()), float(tabla[(tabla.ramo == l) & (tabla.peril == per)].cuota_nominal.max())) for (l, per) in pub['exposicion_retenida']}
    det['cuota_conteo_retenida_rango_informe'] = {f'{l}_{per}': (float(tabla[(tabla.ramo == l) & (tabla.peril == per)].cuota_conteo_informe.min()), float(tabla[(tabla.ramo == l) & (tabla.peril == per)].cuota_conteo_informe.max())) for (l, per) in pub['exposicion_retenida']}
    det['exposicion_retenida_publicada'] = {f'{l}_{per}': v for (l, per), v in pub['exposicion_retenida'].items()}
    ok_rangos = all(redondeo_igual(det['cuota_conteo_retenida_rango_informe'][k][0], v[0], 3) and redondeo_igual(det['cuota_conteo_retenida_rango_informe'][k][1], v[1], 3) for k, v in det['exposicion_retenida_publicada'].items())
    det['rangos_publicados_coinciden_con_la_tabla_de_Codex'] = ok_rangos
    fallos += not ok_rangos
    R.add('VN20', 'Ampliación', 'Coberturas (033): seis siniestros de edificios (3.175,58 CU) y 24 de contenidos (25.869,48 CU) de daño accidental sin bandera, cerrados y con coste; ninguno de autos fuera de las máscaras; denominadores nominales por celda iguales a la tabla de Codex; conciliación con VE42',
          'pasa' if fallos == 0 else 'hallazgo', f"{fallos} fallos; edificios {det['buildings_ad_fuera']['cerrados_con_coste']} ({det['buildings_ad_fuera']['neto_cerrados_con_coste']:,.2f} CU), contenidos {det['contents_ad_fuera']['cerrados_con_coste']} ({det['contents_ad_fuera']['neto_cerrados_con_coste']:,.2f} CU)", 'cifras de 033', 'P1' if fallos else '', det)


def n_calendario(C: Corridas, R: Registro):
    w = C.wide('dev5').set_index('row_id')
    pol = C.pol.set_index('row_id').loc[w.index]
    tg = C.tgt[(C.tgt.year == 2023) & (~C.tgt.is_test.astype(bool))].set_index('row_id').loc[w.index]
    corte = pd.Timestamp('2024-12-31'); madura = corte - pd.Timedelta(days=540)
    dias = (pol.period_end - pol.period_start).dt.days + 1
    fin_maduro = pol.period_end.where(pol.period_end <= madura, madura)
    dias_maduros = ((fin_maduro - pol.period_start).dt.days + 1).clip(lower=0)
    peso_dia = tg.exposure / dias
    det, fallos = {}, 0
    pub = PUBLICADO['COD-S2-20261024-031']
    res = {}
    for l in LINES:
        for nb in [0, 1]:
            vals = []
            for f in range(5):
                m = (w.line == l) & (w.fold != f) & (w.x_new_business.astype(int) == nb)
                vals.append(float((dias_maduros[m] * peso_dia[m]).sum() / (dias[m] * peso_dia[m]).sum()))
            ref = [x for x in C.readout['soporte']['maturity540'] if x['line'] == l and x['business'] == nb][0]
            res[f'{l}_nb{nb}'] = dict(por_fold_de_ajuste=vals, min=min(vals), max=max(vals), informe_min=ref['min'], informe_max=ref['max'], dif_max=max(abs(min(vals) - ref['min']), abs(max(vals) - ref['max'])))
            fallos += res[f'{l}_nb{nb}']['dif_max'] > 1e-6
    det['madurez_540'] = res
    det['madurez_540_publicada'] = pub['madurez540']
    # perfil de calendario: periodos, grupos, exposición, días cubiertos y siniestros por ramo, fold y negocio
    a = C.audit[(C.audit.status != 'repudiated') & C.audit.row_id.notna()]
    a = a[a.row_id.isin(w.index)]
    cal = C.cal
    difs = []
    for _, r in cal.iterrows():
        m = (w.line == r.line) & (w.fold != r.fold) & (w.x_new_business.astype(int) == int(r.business))
        mio = dict(periods=int(m.sum()), groups=int(w.group_id[m].nunique()), exposure=float(tg.exposure[m].sum()), covered_days=int(dias[m].sum()),
                   claims=int(((a.row_id.map(w.fold) != r.fold) & (a.line == r.line) & (a.row_id.map(w.x_new_business).astype(int) == int(r.business))).sum()))
        difs.append(dict(ramo=r.line, fold=int(r.fold), negocio=int(r.business), **{k: (mio[k], (float(r[k]) if k == 'exposure' else int(r[k]))) for k in mio}))
    det['perfil_calendario'] = difs
    det['perfil_calendario_max_dif'] = max(max(abs(d[k][0] - d[k][1]) for k in ['periods', 'groups', 'exposure', 'covered_days', 'claims']) for d in difs)
    fallos += det['perfil_calendario_max_dif'] > 1e-6
    det['celdas'] = int(len(C.celdas)); det['puntos_soporte'] = int(pq.ParquetFile(C.dir['soporte'] / 'delay_support.parquet').metadata.num_rows) if (C.dir['soporte'] / 'delay_support.parquet').exists() else None
    fallos += (det['celdas'] != pub['celdas']) + (det['puntos_soporte'] not in (None, pub['puntos_soporte']))
    R.add('VN21', 'Ampliación', 'Soporte de calendario (031): exposición madura a 540 días por ramo, negocio y fold de ajuste (52,33 % renovación, 26,54–27,33 % nuevo negocio) y el perfil de calendario (periodos, grupos, exposición, días cubiertos, siniestros) recalculados desde las pólizas',
          'pasa' if fallos == 0 else 'hallazgo', f"{fallos} fallos; renovación {res['motor_nb0']['min']:.4f}, nuevo negocio {min(res[k]['min'] for k in res if k.endswith('nb1')):.4f}–{max(res[k]['max'] for k in res if k.endswith('nb1')):.4f}", 'cifras de 031', 'P1' if fallos else '', det)


# ----------------------------------------------------------------------------------------------- H. límites
def i_limites(C: Corridas, R: Registro, recalculado):
    det = dict(dev7_modelos=sorted({m for (k, m) in recalculado if k == 'dev7'}), B00_referencia=recalculado[('dev7', 'W2-B00')]['global_']['D2'],
               mejor_D2_global={k: max(((m, v['global_']['D2']) for (kk, m), v in recalculado.items() if kk == k), key=lambda t: t[1]) for k in ['dev5', 'dev6', 'dev7']})
    orden = sorted(((m, v['global_']['D2']) for (k, m), v in recalculado.items() if k == 'dev7'), key=lambda t: -t[1])
    det['orden_global_dev7'] = orden
    R.add('VN16', 'Lectura', 'Ninguna receta nocturna acredita mejora: los intervalos exploratorios cruzan cero o las ventajas se invierten al retirar 31 grupos (replicado en VN10); el mayor D² global puntual entre las 19 recetas sigue siendo B10, luego B08', 'informativo',
          f"orden global: {', '.join(f'{m.replace('W2-', '')} {v:.4f}' for m, v in orden[:5])}", '', '', det)
    det = dict(no_verificado=['la selección de las seis variables, la convergencia declarada y los gradientes de los GLM auxiliares Poisson/Gamma de dev6 (treinta auxiliares) y sus errores por componente',
                              'las curvas de reporte q_N/q_C por peril y los pesos de C0 (se reciben como enlace congelado; VE60 comprobó la identidad prediction = tasa × C0)',
                              'la receta de los modelos B01–B11 (tandas anteriores; dev3 ya validado en VE60) y los modelos LightGBM',
                              'la exactitud económica del capital dividido (T0 = 0 en las 56 filas: no hay siniestros que la midan)',
                              'cualquier cosa de 2024 o del test: siguen cerrados'],
               verificado_por_recalculo=['métricas y segmentos de 49 pares corrida-modelo', 'constantes B00 y B12', 'identidades de capital, credibilidad y ablaciones', 'once pares con remuestreo', 'cola, reservas y L1', 'replay de 30 GLM'])
    R.add('VN17', 'Alcance', 'Lo que esta verificación no cubre y lo que sí; revisión de IA con código propio sobre copias con huella, no revisión profesional independiente', 'limite', 'revisión de IA', '', 'P1', det)


# ----------------------------------------------------------------------------------------------- J. ampliación: 035, B20, 037 y 039 (B19, B20 ridge, estabilidad e influencia, trazabilidad)
NUEVAS = {'dev8': 'dev8_20261024T013001Z_e8a35214', 'ridge': 'ridge20_20261024_v1',
          'estabilidad': 'estabilidad_b19_20261024T014815Z_9b2b1803', 'traza': 'traza_b19_20261024T021036Z_fe5038de'}

# Lo que Codex publicó sobre B19, B20, 037 y 039 (foro e informes citados). Se compara a la precisión impresa.
PUBLICADO_B19 = {
    'COD-S2-20261024-035': {
        'D2': {'W2-B14': 0.086710, 'W2-B19': 0.082470, 'W2-B00': 0.068582},
        'ramo': {('buildings', 'W2-B14'): 0.021094, ('buildings', 'W2-B19'): 0.008352, ('contents', 'W2-B14'): 0.037343, ('contents', 'W2-B19'): 0.036281,
                 ('motor', 'W2-B14'): 0.033101, ('motor', 'W2-B19'): 0.033722},
        'motor_nb': {'W2-B14': -0.010045, 'W2-B19': -0.031822},
        'pares': {('W2-B19', 'W2-B14'): (-0.004240, -0.009969, 0.000507, -0.007145), ('W2-B19', 'W2-B00'): (0.013888, -0.011053, 0.037614, -0.014724)},
        'nominal': {'W2-B14': 15606084.09, 'W2-B19': 15613508.68, 'pct': 0.000476},
        'B20_PRE_D2': {'W2-B19': 0.082469696, 'W2-B14': 0.086710078},
    },
    'GLM_COBERTURAS_2023': {   # docs/semana2/GLM_COBERTURAS_2023.md
        'negocio': {('motor', 1, 'W2-B14'): -0.010045, ('motor', 1, 'W2-B19'): -0.031822, ('motor', 0, 'W2-B14'): 0.039794, ('motor', 0, 'W2-B19'): 0.044035,
                    ('buildings', 1, 'W2-B14'): 0.050163, ('buildings', 1, 'W2-B19'): 0.048378, ('buildings', 0, 'W2-B14'): 0.011464, ('buildings', 0, 'W2-B19'): -0.002416,
                    ('contents', 1, 'W2-B14'): 0.153579, ('contents', 1, 'W2-B19'): 0.151995, ('contents', 0, 'W2-B14'): 0.020962, ('contents', 0, 'W2-B19'): 0.019948},
        'cobertura': {('motor', 'third_party_only', 'W2-B14', 'D2'): -0.015892, ('motor', 'third_party_only', 'W2-B19', 'D2'): -0.042793,
                      ('buildings', 'AD_yes', 'W2-B14', 'AE'): 1.076, ('buildings', 'AD_yes', 'W2-B19', 'AE'): 1.010,
                      ('buildings', 'AD_yes', 'W2-B14', 'D2'): -0.008318, ('buildings', 'AD_yes', 'W2-B19', 'D2'): -0.029774},
        'predicho': {'W2-B14': 15429695.38, 'W2-B19': 15436941.83},
        'rangos_ajuste_B19': {'motor': (0.046833, 0.069152), 'buildings': (0.082730, 0.107039), 'contents': (0.061389, 0.078698)},
        'rangos_validacion_B19': {'motor': (-0.038790, 0.067697), 'buildings': (-0.039424, 0.036117), 'contents': (0.002460, 0.069942)},
        'razon_AD_buildings': (0.795, 1.388), 'razon_TPO_motor': (0.567, 0.857),
        'mejora_ajuste_en_15': True,
    },
    'COD-S2-20261024-B20-RESULT': {
        'D2': {'W2-B20': 0.08938179, 'W2-B19': 0.08246970, 'W2-B14': 0.08671008, 'W2-B00': 0.06858169},
        'pares8': {('W2-B20', 'W2-B14'): (0.00267171, -0.00367289, 0.00868343), ('W2-B20', 'W2-B19'): (0.00691209, 0.00141971, 0.01351104)},
        'tres_invierten_signo_con_31': True,
    },
    'GLM_RIDGE_COBERTURAS_2023': {   # docs/semana2/GLM_RIDGE_COBERTURAS_2023.md
        'tabla': {'W2-B00': dict(D2=0.068582, AE=0.9797, pred=15614394.39), 'W2-B14': dict(D2=0.086710, AE=0.9914, pred=15429695.38),
                  'W2-B19': dict(D2=0.082470, AE=0.9909, pred=15436941.83), 'W2-B20': dict(D2=0.089382, AE=1.0113, pred=15126408.70)},
        'pares': {('W2-B20', 'W2-B19'): (0.006912, 0.001420, 0.013511, -0.003869), ('W2-B20', 'W2-B14'): (0.002672, -0.003673, 0.008683, -0.006513),
                  ('W2-B20', 'W2-B00'): (0.020800, 0.000346, 0.041688, -0.006580)},
        'segmentos_B20': {('buildings', 1): (0.069497, 0.019334), ('buildings', 0): (0.012680, 0.001216), ('contents', 1): (0.147164, -0.006415),
                          ('contents', 0): (0.029850, 0.008887), ('motor', 1): (-0.019444, -0.009399), ('motor', 0): (0.042435, 0.002641)},
        'nominal_pct_vs_B19': -0.02008, 'razon_AD_buildings': (0.801, 1.375), 'norma_baja_en_15': True,
    },
    'COD-S2-20261024-037': {   # foro 037 y docs/semana2/ESTABILIDAD_E_INFLUENCIA_B19_2023.md
        'razones': {('buildings', 'AD'): (0.795, 1.388), ('buildings', 'NB'): (0.856, 1.217), ('contents', 'AD'): (0.865, 1.020), ('contents', 'NB'): (0.671, 1.028),
                    ('motor', 'TPFT'): (0.587, 0.611), ('motor', 'TPO'): (0.567, 0.857), ('motor', 'NB'): (1.978, 2.481)},
        'signos': {('buildings', 'AD'): (1, 4), ('buildings', 'NB'): (3, 2), ('contents', 'AD'): (2, 3), ('contents', 'NB'): (4, 1), ('motor', 'TPFT'): (5, 0), ('motor', 'TPO'): (5, 0), ('motor', 'NB'): (0, 5)},
        'buildings': dict(grupos=12107, delta=-0.012743, top5_T0=1237635.60, top5_fraccion=0.315, retiro_un_adverso=-0.009127, individual_min=-0.013562, individual_max=-0.009127),
        'motor_nb': dict(grupos=2427, delta=-0.021777, principal_T0=136767.16, principal_fraccion=0.561, pred_B19=90.25, pred_B14=132.77, retiro_segmento=0.009766, retiro_global=-0.002430),
        'retiros': {('buildings', 'adverse'): {1: -0.009127, 5: -0.002984, 10: 0.000851, 31: 0.006178}, ('buildings', 'favorable'): {1: -0.013562, 5: -0.015222, 10: -0.016611, 31: -0.019760},
                    ('motor_new', 'adverse'): {1: 0.009766, 5: 0.016059, 10: 0.017917, 31: 0.020558}, ('motor_new', 'favorable'): {1: -0.025682, 5: -0.034901, 10: -0.039254, 31: -0.045867}},
        'influencia_local': dict(TPO=(-0.245, -0.223), NB=(-0.213, -0.195), incendio_286093_AD=(-0.156, -0.100)),
        'hessianos': dict(condicion=(80.9, 165.1), leverage_max_buildings=0.461, leverage_max_motor=0.293),
    },
    'COD-S2-20261024-039': {   # foro 039 y docs/semana2/TRAZABILIDAD_SINIESTROS_B19_2023.md
        'componentes': 12, 'periodos': 20, 'siniestros': 12,
        'ramo': {'buildings': dict(siniestros=6, pagado=1325514.09, reserva=74089.21, recuperaciones=0.0, T0=1399603.30),
                 'motor': dict(siniestros=6, pagado=201475.05, reserva=14954.51, recuperaciones=0.0, T0=216429.56)},
        'total': dict(T0=1616032.86, reserva=89043.72, cuota=0.0551, cerrados=10, abiertos=2, estres=22260.93, estres_pct=0.0138),
        'principal_autos': dict(T0=136767.16, perdida='2023-12-01', reporte='2024-01-28', demora=58, estado='closed'),
        'incendio_abierto': dict(T0=149180.40, pagado=75091.19, reserva=74089.21), 'incendio_286093': dict(T0=286093.00, demora=14, estado='closed'),
        'autos_abierto': dict(T0=18915.80, pagado=3961.29, reserva=14954.51),
        'demoras': dict(min=1, max=349, mayores_365=0, reportados_2024=2),
    },
}


# ----------------------------------------------------------------------------------------------- carga adicional
class Nuevas:
    """Carga perezosa de las corridas nuevas (dev8 = B19, ridge = B20, estabilidad = 037, traza = 039)."""

    def __init__(self, C: Corridas):
        self.C = C
        self.dir = {k: C.raiz / v for k, v in NUEVAS.items()}
        self.man = {k: json.load(open(self.dir[k] / 'manifest.json', encoding='utf-8')) for k in NUEVAS}
        self.rep = {k: json.load(open(self.dir[k] / 'report.json', encoding='utf-8')) for k in NUEVAS}
        self.plan = {k: json.load(open(self.dir[k] / 'plan_snapshot.json', encoding='utf-8')) for k in NUEVAS}
        self.readout = {k: json.load(open(self.dir[k] / 'readout.json', encoding='utf-8')) for k in ['dev8', 'estabilidad', 'traza']}
        self.new_oof = {k: pq.read_table(self.dir[k] / 'new_oof_2023.parquet').to_pandas() for k in ['dev8', 'ridge']}
        self.diag = {k: {n: json.load(open(self.dir[k] / 'diagnostics' / f'{n}.json', encoding='utf-8')) for n in ['new_pairs', 'segments', 'train_validation']} for k in ['dev8', 'ridge']}
        self.diag['dev8']['coefficients'] = json.load(open(self.dir['dev8'] / 'diagnostics' / 'coefficients.json', encoding='utf-8'))
        self.diag['ridge']['coefficient_stability'] = json.load(open(self.dir['ridge'] / 'diagnostics' / 'coefficient_stability.json', encoding='utf-8'))
        self.boot = {k: pq.read_table(self.dir[k] / 'diagnostics' / 'bootstrap_new_pairs.parquet').to_pandas() for k in ['dev8', 'ridge']}
        e = self.dir['estabilidad']
        self.est = dict(focus=json.load(open(e / 'focus_summary.json', encoding='utf-8')), removal=json.load(open(e / 'group_removal_evaluation.json', encoding='utf-8')),
                        hess=json.load(open(e / 'hessian_conditions.json', encoding='utf-8')), links=json.load(open(e / 'group_training_OOF_links.json', encoding='utf-8')),
                        coef_summary=pq.read_table(e / 'coefficient_stability_summary.parquet').to_pandas(), coef=pq.read_table(e / 'coefficients_original_scale.parquet').to_pandas(),
                        contrib=pq.read_table(e / 'oof_group_contributions.parquet').to_pandas(), loo=pq.read_table(e / 'leave_one_group_evaluation.parquet').to_pandas(),
                        ranked=pq.read_table(e / 'ranked_group_selections.parquet').to_pandas(), perils=pq.read_table(e / 'focus_group_perils.parquet').to_pandas(),
                        infl=pq.read_table(e / 'training_group_local_influence.parquet').to_pandas())
        t = self.dir['traza']
        self.tra = dict(sel=pq.read_table(t / 'selection_reasons.parquet').to_pandas(), fin=pq.read_table(t / 'group_financial_trace_2023.parquet').to_pandas(),
                        orig=pq.read_table(t / 'claims_original_selected_2023.parquet').to_pandas(), saved=pq.read_table(t / 'claims_saved_selected_2023.parquet').to_pandas(),
                        per=pq.read_table(t / 'period_reconciliation_2023.parquet').to_pandas())
        self.claims = pq.read_table(C.emerging / 'claims.parquet').to_pandas()
        self.inputs8 = {(l, f): pq.read_table(self.dir['dev8'] / 'inputs_2023' / f'{l}_fold{f}.parquet').to_pandas().set_index('row_id') for l in LINES for f in range(5)}

    def wide(self):
        """B00 y B14 (OOF de dev7) con B19 (dev8) y B20 (ridge) por row_id."""
        w = self.C.wide('dev7')[['row_id', 'line', 'group_id', 'fold', 'exposure', 'T0', 'reserve', 'x_new_business', 'e_cost_mix_1.0',
                                 'pred_W2-B00', 'rate_W2-B00', 'dev_W2-B00', 'pred_W2-B14', 'rate_W2-B14', 'dev_W2-B14']].set_index('row_id')
        for k, mo in [('dev8', 'W2-B19'), ('ridge', 'W2-B20')]:
            o = self.new_oof[k].set_index('row_id')
            w[f'pred_{mo}'] = o.prediction; w[f'rate_{mo}'] = o.annual_rate; w[f'dev_{mo}'] = o.unit_deviance
        w['market'] = 'emerging'
        return w.reset_index()


def _rel(path, run):
    """Ruta relativa a la carpeta de la corrida, tanto si el manifiesto la escribe relativa como con el prefijo del repositorio."""
    return path.split(f'{run}/', 1)[1] if f'{run}/' in path else path


# ----------------------------------------------------------------------------------------------- VN22 fuentes nuevas
def o_fuentes_nuevas(N: Nuevas, R: Registro):
    det, ok, n = {}, 0, 0
    for k, d in N.dir.items():
        files = {_rel(f['path'], NUEVAS[k]): f['sha256'] for f in N.man[k]['files']}
        det[k] = {}
        for p in sorted(d.rglob('*')):
            if p.is_file() and p.name != 'manifest.json':
                rel = p.relative_to(d).as_posix()
                if rel in files:
                    n += 1; igual = sha256(p) == files[rel]; ok += igual; det[k][rel] = igual
                else:
                    det[k][rel] = 'fuera del manifiesto (escrito después)'
        det[k]['_entradas_manifiesto'] = len(files); det[k]['_copiadas'] = sum(1 for v in det[k].values() if isinstance(v, bool))
    det['informes'] = {k: dict(id=N.rep[k].get('id'), fin=N.rep[k].get('completed_utc'), plan_sha256=N.rep[k].get('plan_sha256')) for k in NUEVAS}
    det['ridge_usa_dev8'] = dict(input_run=N.plan['ridge']['input_run'].endswith(NUEVAS['dev8']),
                                 fuentes_dev8_con_huella_igual=all(sha256(N.dir['dev8'] / _rel(s['path'], NUEVAS['dev8'])) == s['sha256'] for s in N.plan['ridge']['frozen_sources']
                                                                   if NUEVAS['dev8'] in s['path'] and (N.dir['dev8'] / _rel(s['path'], NUEVAS['dev8'])).exists()))
    # identidades por fila y coherencia con la base de los dos OOF nuevos
    tg = N.C.tgt[(N.C.tgt.year == 2023) & (~N.C.tgt.is_test.astype(bool))].set_index('row_id')
    pt = N.C.part[N.C.part.year == 2023].set_index('row_id')
    w7 = N.C.wide('dev7').set_index('row_id')
    fallos = 0
    for k, mo in [('dev8', 'W2-B19'), ('ridge', 'W2-B20')]:
        o = N.new_oof[k].set_index('row_id')
        d = dict(filas=int(len(o)), modelo_unico=o.model_id.unique().tolist(), mismo_conjunto_2023=set(o.index) == set(tg.index),
                 T0_igual=bool(np.allclose(o.T0.astype(float), tg.loc[o.index, 'T0'], atol=1e-9)), fold_igual=bool((o.fold.to_numpy() == pt.loc[o.index, 'fold'].to_numpy()).all()),
                 grupo_igual=bool((o.group_id.to_numpy() == pt.loc[o.index, 'group_id'].to_numpy()).all()),
                 C0_igual_a_dev7=bool(np.allclose(o['e_cost_mix_1.0'], w7.loc[o.index, 'e_cost_mix_1.0'], atol=1e-12)),
                 max_dif_prediction_vs_tasa_por_C0=float((o.prediction - o.annual_rate * o['e_cost_mix_1.0']).abs().max()),
                 max_dif_unit_deviance_vs_formula=float((o.unit_deviance - dev_unit(o.T0.astype(float), o.prediction)).abs().max()),
                 predicciones_positivas_finitas=bool(np.isfinite(o.prediction).all() and (o.prediction > 0).all()))
        d['modelo_esperado'] = d['modelo_unico'] == [mo]
        fallos += sum(not d[x] for x in ['mismo_conjunto_2023', 'T0_igual', 'fold_igual', 'grupo_igual', 'C0_igual_a_dev7', 'predicciones_positivas_finitas', 'modelo_esperado'])
        fallos += (d['max_dif_prediction_vs_tasa_por_C0'] > 1e-6) + (d['max_dif_unit_deviance_vs_formula'] > 1e-6)
        det[f'oof_{k}'] = d
    R.add('VN22', 'Fuentes', 'Huellas de las corridas de B19 (dev8), B20 (ridge), estabilidad (037) y traza (039) frente a sus manifiestos; los dos OOF nuevos tienen las 50.094 filas de 2023 con T0, fold, grupo y C0 iguales a la base y a dev7, y cumplen prediction = tasa × C0 y la fórmula de desviancia',
          'pasa' if ok == n and fallos == 0 else 'hallazgo', f'{ok} de {n} archivos con huella igual; {fallos} discrepancias en los OOF', 'todas y 0', 'P0' if (ok != n or fallos) else '', det)


# ----------------------------------------------------------------------------------------------- VN23 métricas publicadas de B19 y B20
def _seg_metr(w, mo, mask):
    return metr(w.T0.to_numpy()[mask], w[f'pred_{mo}'].to_numpy()[mask])


def p_recetas_b19_b20(N: Nuevas, R: Registro, salida: pathlib.Path):
    w = N.wide()
    pol = N.C.pol.set_index('row_id')
    cover = pd.Series(index=w.row_id, dtype=object)
    wi = w.set_index('row_id')
    cover.loc[wi.line == 'motor'] = pol.loc[wi.index[wi.line == 'motor'], 'cover_type'].astype(str).to_numpy()
    for l in ['buildings', 'contents']:
        cover.loc[wi.line == l] = np.where(pol.loc[wi.index[wi.line == l], 'accidental_damage_cover'].astype(float).to_numpy() == 1, 'AD_yes', 'AD_no')
    w['cover'] = cover.to_numpy()
    modelos = ['W2-B00', 'W2-B14', 'W2-B19', 'W2-B20']
    nb = (w.x_new_business.astype(int) == 1).to_numpy()
    rec = {}
    filas = []
    for mo in modelos:
        g = _seg_metr(w, mo, np.ones(len(w), bool))
        nominal = float((w[f'rate_{mo}'] * w.exposure).sum())
        rec[mo] = dict(global_=g, nominal=nominal)
        for l in LINES:
            ml = (w.line == l).to_numpy()
            rec[mo][f'{l}_all'] = _seg_metr(w, mo, ml); rec[mo][f'{l}_nb'] = _seg_metr(w, mo, ml & nb); rec[mo][f'{l}_ren'] = _seg_metr(w, mo, ml & ~nb)
            for c in sorted(w.cover[ml].unique()):
                rec[mo][f'{l}_{c}'] = _seg_metr(w, mo, ml & (w.cover == c).to_numpy())
        filas.append(dict(modelo=mo, D2=g['D2'], AE=g['AE'], predicho=g['predicho'], observado=g['observado'], nominal=nominal, D2_motor=rec[mo]['motor_all']['D2'], D2_buildings=rec[mo]['buildings_all']['D2'],
                          D2_contents=rec[mo]['contents_all']['D2'], D2_motor_nb=rec[mo]['motor_nb']['D2'], D2_buildings_nb=rec[mo]['buildings_nb']['D2'], D2_contents_nb=rec[mo]['contents_nb']['D2'],
                          AE_motor=rec[mo]['motor_all']['AE'], AE_buildings=rec[mo]['buildings_all']['AE'], AE_contents=rec[mo]['contents_all']['AE']))
    pd.DataFrame(filas).to_csv(salida / 'tablas' / 'recetas_b19_b20.csv', index=False)
    det = dict(recalculado={mo: {k: v for k, v in rec[mo].items()} for mo in modelos})
    # frente a los report.json y a los segments.json de Codex
    fallos_rep = 0; comp = {}
    for k in ['dev8', 'ridge']:
        for s in N.rep[k]['summary']:
            mo = s['model_id']; g = rec[mo]['global_']
            c = dict(D2_dif=abs(s['D2'] - g['D2']), predicho_dif=abs(s['predicted_total'] - g['predicho']), nula_dif=abs(s['null_deviance_sum'] - g['devianza_nula']),
                     nominal_dif=abs(s['conditional_nominal_2023'] - rec[mo]['nominal']), AE_dif=abs(s['actual_over_expected'] - g['AE']))
            fallos_rep += (c['D2_dif'] > 1e-9) + (c['predicho_dif'] > 1e-4) + (c['nula_dif'] > 1e-4) + (c['nominal_dif'] > 1e-4) + (c['AE_dif'] > 1e-9)
            comp[f'{k} {mo}'] = c
        segs = N.diag[k]['segments']; n_seg = 0; peor = 0.0
        for s in segs:
            mo = s['model_id']
            if mo not in rec:
                continue
            lab = s['label']; dim = s['dimension']
            if dim == 'line':
                m = rec[mo][f'{lab}_all']
            elif dim == 'line_business':
                l, b = lab.split('_', 1); m = rec[mo][f'{l}_{"nb" if b == "new_business" else "ren"}']
            elif dim == 'line_coverage':
                l, c = lab.split('_', 1); m = rec[mo][f'{l}_{c}']
            elif dim == 'business':
                mk = nb if lab == 'new_business' else ~nb; m = _seg_metr(w, mo, mk)
            elif dim == 'fold':
                m = _seg_metr(w, mo, (w.fold == int(lab)).to_numpy())
            else:
                continue
            n_seg += 1; peor = max(peor, abs(s['D2'] - m['D2']), abs(s['actual_over_expected'] - m['AE']))
        comp[f'{k} segmentos'] = dict(comparados=n_seg, max_dif=peor); fallos_rep += peor > 1e-9
    det['frente_a_informes'] = comp; det['fallos_frente_a_informes'] = int(fallos_rep)
    # frente al foro y a los documentos
    P = PUBLICADO_B19; foro = {}; n_foro = fallos_foro = 0
    def chk(nombre, val, pub, dec):
        nonlocal n_foro, fallos_foro
        okk = redondeo_igual(val, pub, dec); n_foro += 1; fallos_foro += not okk
        foro[nombre] = dict(publicado=pub, recalculado=float(val), coincide=okk)
    for mo, pub in P['COD-S2-20261024-035']['D2'].items():
        chk(f'035 D2 {mo}', rec[mo]['global_']['D2'], pub, 6)
    for (l, mo), pub in P['COD-S2-20261024-035']['ramo'].items():
        chk(f'035 D2 {l} {mo}', rec[mo][f'{l}_all']['D2'], pub, 6)
    for mo, pub in P['COD-S2-20261024-035']['motor_nb'].items():
        chk(f'035 D2 motor nb {mo}', rec[mo]['motor_nb']['D2'], pub, 6)
    for mo, pub in P['COD-S2-20261024-035']['nominal'].items():
        if mo != 'pct':
            chk(f'035 nominal {mo}', rec[mo]['nominal'], pub, 2)
    chk('035 nominal pct', rec['W2-B19']['nominal'] / rec['W2-B14']['nominal'] - 1, P['COD-S2-20261024-035']['nominal']['pct'], 6)
    for mo, pub in P['COD-S2-20261024-035']['B20_PRE_D2'].items():
        chk(f'B20-PRE D2 {mo}', rec[mo]['global_']['D2'], pub, 9)
    G = P['GLM_COBERTURAS_2023']
    for (l, b, mo), pub in G['negocio'].items():
        chk(f'doc B19 D2 {l} {"nb" if b else "ren"} {mo}', rec[mo][f'{l}_{"nb" if b else "ren"}']['D2'], pub, 6)
    for (l, c, mo, met), pub in G['cobertura'].items():
        chk(f'doc B19 {met} {l} {c} {mo}', rec[mo][f'{l}_{c}'][met], pub, 3 if met == 'AE' else 6)
    for mo, pub in G['predicho'].items():
        chk(f'doc B19 predicho {mo}', rec[mo]['global_']['predicho'], pub, 2)
    for mo, pub in P['COD-S2-20261024-B20-RESULT']['D2'].items():
        chk(f'B20-RESULT D2 {mo}', rec[mo]['global_']['D2'], pub, 8)
    for mo, pub in P['GLM_RIDGE_COBERTURAS_2023']['tabla'].items():
        chk(f'doc B20 D2 {mo}', rec[mo]['global_']['D2'], pub['D2'], 6); chk(f'doc B20 AE {mo}', rec[mo]['global_']['AE'], pub['AE'], 4); chk(f'doc B20 predicho {mo}', rec[mo]['global_']['predicho'], pub['pred'], 2)
    for (l, b), (d2, cambio) in P['GLM_RIDGE_COBERTURAS_2023']['segmentos_B20'].items():
        seg = f'{l}_{"nb" if b else "ren"}'
        chk(f'doc B20 D2 {seg}', rec['W2-B20'][seg]['D2'], d2, 6); chk(f'doc B20 cambio {seg} frente a B14', rec['W2-B20'][seg]['D2'] - rec['W2-B14'][seg]['D2'], cambio, 6)
    chk('doc B20 nominal pct frente a B19', rec['W2-B20']['nominal'] / rec['W2-B19']['nominal'] - 1, P['GLM_RIDGE_COBERTURAS_2023']['nominal_pct_vs_B19'], 5)
    # rangos de validación por fold de B19 (desde el OOF) frente al documento; D² por fold de los cuatro modelos para la figura
    for l in LINES:
        vals = [_seg_metr(w, 'W2-B19', ((w.line == l) & (w.fold == f)).to_numpy())['D2'] for f in range(5)]
        chk(f'doc B19 validacion min {l}', min(vals), G['rangos_validacion_B19'][l][0], 6); chk(f'doc B19 validacion max {l}', max(vals), G['rangos_validacion_B19'][l][1], 6)
        det.setdefault('validacion_B19_por_fold', {})[l] = vals
    det['D2_por_fold'] = {mo: [_seg_metr(w, mo, (w.fold == f).to_numpy())['D2'] for f in range(5)] for mo in modelos}
    det['B20_supera_a_B14_en_folds'] = int(sum(det['D2_por_fold']['W2-B20'][f] > det['D2_por_fold']['W2-B14'][f] for f in range(5)))
    det['B19_supera_a_B14_en_folds'] = int(sum(det['D2_por_fold']['W2-B19'][f] > det['D2_por_fold']['W2-B14'][f] for f in range(5)))
    det['frente_al_foro_y_documentos'] = foro; det['comparaciones'] = n_foro; det['fallos_frente_al_foro'] = fallos_foro
    # lectura del nivel: A/E por ramo de B20 frente a B14 y B19
    det['nivel'] = {mo: dict(AE=rec[mo]['global_']['AE'], predicho=rec[mo]['global_']['predicho'], nominal=rec[mo]['nominal'],
                             AE_por_ramo={l: rec[mo][f'{l}_all']['AE'] for l in LINES}, nominal_pct_vs_B14=rec[mo]['nominal'] / rec['W2-B14']['nominal'] - 1) for mo in modelos}
    R.add('VN23', 'Recetas', 'D², A/E, predicho, nominal condicionado y segmentos (ramo, negocio, cobertura, fold) de B00, B14, B19 y B20 recalculados desde los OOF frente a report.json, segments.json y a las cifras del foro (035, B20-PRE, B20-RESULT) y de los dos informes de Codex',
          'pasa' if fallos_rep == 0 and fallos_foro == 0 else 'hallazgo', f'{fallos_rep} discrepancias con los informes; {fallos_foro} de {n_foro} cifras publicadas no coinciden', '0 y 0', 'P1' if (fallos_rep or fallos_foro) else '', det)
    return w, rec


# ----------------------------------------------------------------------------------------------- VN24 pares con remuestreo
def q_pares_b19_b20(N: Nuevas, R: Registro, w, salida: pathlib.Path):
    pares = [('W2-B19', 'W2-B14'), ('W2-B19', 'W2-B00'), ('W2-B20', 'W2-B19'), ('W2-B20', 'W2-B14'), ('W2-B20', 'W2-B00')]
    dists = {}
    res, dig = pares_bootstrap(w, pares, distribuciones=dists)
    rep = {(p['candidate'], p['reference']): p for k in ['dev8', 'ridge'] for p in N.rep[k]['pairs']}
    det = dict(draws_sha256=dig, draws_sha256_codex={k: N.diag[k]['new_pairs'].get('draws_sha256') for k in ['dev8', 'ridge']}, pares={})
    det['sorteos_iguales_a_codex'] = all(dig == v for v in det['draws_sha256_codex'].values())
    fallos_rep = fallos_foro = n_foro = 0
    P = PUBLICADO_B19
    filas = []
    for p, r in res.items():
        pr = rep[p]
        comp_rep = dict(delta_dif=abs(r['delta_D2'] - pr['delta_D2']), inferior_dif=abs(r['inferior95'] - pr['exploratory_lower95']), superior_dif=abs(r['superior95'] - pr['exploratory_upper95']),
                        retirar_dif=abs(r['delta_tras_retirar'] - pr['delta_after_removal']), retirados_igual=r['retirados'] == pr['removed_favorable_groups'], grupos_igual=r['grupos'] == pr['groups'])
        fallos_rep += (comp_rep['delta_dif'] > 1e-9) + (comp_rep['inferior_dif'] > 1e-9) + (comp_rep['superior_dif'] > 1e-9) + (comp_rep['retirar_dif'] > 1e-9) + (not comp_rep['retirados_igual']) + (not comp_rep['grupos_igual'])
        # distribución guardada por Codex (bootstrap_new_pairs.parquet) frente a la mía, sorteo a sorteo
        b = N.boot['dev8' if p[0] == 'W2-B19' else 'ridge']
        if 'candidate' not in b.columns:
            b = b.assign(candidate='W2-B20')
        bb = b[(b.candidate == p[0]) & (b.reference == p[1])].sort_values('replicate').delta_D2.to_numpy()
        comp_rep['max_dif_distribucion_sorteo_a_sorteo'] = float(np.abs(bb - dists[p]).max()) if len(bb) == len(dists[p]) else None
        fallos_rep += (comp_rep['max_dif_distribucion_sorteo_a_sorteo'] is None) or (comp_rep['max_dif_distribucion_sorteo_a_sorteo'] > 1e-9)
        foro = {}
        if p in P['COD-S2-20261024-035']['pares']:
            pub = P['COD-S2-20261024-035']['pares'][p]
            foro['035'] = [redondeo_igual(r['delta_D2'], pub[0], 6), redondeo_igual(r['inferior95'], pub[1], 6), redondeo_igual(r['superior95'], pub[2], 6), redondeo_igual(r['delta_tras_retirar'], pub[3], 6)]
        if p in P['COD-S2-20261024-B20-RESULT']['pares8']:
            pub = P['COD-S2-20261024-B20-RESULT']['pares8'][p]
            foro['B20-RESULT'] = [redondeo_igual(r['delta_D2'], pub[0], 8), redondeo_igual(r['inferior95'], pub[1], 8), redondeo_igual(r['superior95'], pub[2], 8)]
        if p in P['GLM_RIDGE_COBERTURAS_2023']['pares']:
            pub = P['GLM_RIDGE_COBERTURAS_2023']['pares'][p]
            foro['doc ridge'] = [redondeo_igual(r['delta_D2'], pub[0], 6), redondeo_igual(r['inferior95'], pub[1], 6), redondeo_igual(r['superior95'], pub[2], 6), redondeo_igual(r['delta_tras_retirar'], pub[3], 6)]
        for v in foro.values():
            n_foro += len(v); fallos_foro += sum(not x for x in v)
        r['cruza_cero'] = bool(r['inferior95'] < 0 < r['superior95']); r['invierte_signo_al_retirar'] = bool(np.sign(r['delta_D2']) != np.sign(r['delta_tras_retirar']))
        det['pares'][f'{p[0]} / {p[1]}'] = dict(recalculado=r, informe=pr, coincide_informe=comp_rep, coincide_publicado=foro)
        filas.append(dict(candidato=p[0], referencia=p[1], **{k: v for k, v in r.items()}))
    pd.DataFrame(filas).to_csv(salida / 'tablas' / 'pares_b19_b20.csv', index=False)
    pd.DataFrame({f'{a}_vs_{b}': dists[(a, b)] for (a, b) in pares}).to_csv(salida / 'tablas' / 'remuestreo_b19_b20.csv', index=False)
    det['tres_de_B20_invierten_signo'] = all(det['pares'][f'W2-B20 / {ref}']['recalculado']['invierte_signo_al_retirar'] for ref in ['W2-B19', 'W2-B14', 'W2-B00'])
    fallos_foro += not det['tres_de_B20_invierten_signo']; n_foro += 1
    det['comparaciones_publicadas'] = n_foro; det['fallos_publicados'] = fallos_foro; det['fallos_frente_a_informes'] = int(fallos_rep)
    det['max_dif_distribucion_sorteo_a_sorteo'] = float(max(v['coincide_informe']['max_dif_distribucion_sorteo_a_sorteo'] for v in det['pares'].values()))
    det['max_dif_frente_a_informes'] = float(max(v['coincide_informe'][k] for v in det['pares'].values() for k in ['delta_dif', 'inferior_dif', 'superior_dif', 'retirar_dif']))
    R.add('VN24', 'Influencia', 'Los cinco pares nuevos (B19/B14, B19/B00, B20/B19, B20/B14, B20/B00) con remuestreo agrupado de 2.000 sorteos y retirada de 31 grupos favorables se replican con la misma semilla: deltas, intervalos y distribuciones sorteo a sorteo iguales a los informes; cifras del foro (035, B20-RESULT) y del informe ridge a la precisión publicada',
          'pasa' if fallos_rep == 0 and fallos_foro == 0 else 'hallazgo', f'{fallos_rep} discrepancias con los informes; {fallos_foro} de {n_foro} cifras publicadas no coinciden; sorteos iguales a Codex: {det["sorteos_iguales_a_codex"]}',
          '0 y 0', 'P1' if (fallos_rep or fallos_foro) else '', det)
    return res


# ----------------------------------------------------------------------------------------------- VN25–VN27 replay de B19 y B20, influencia local
def _pipeline(feats_num, feats_cat, params):
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import TweedieRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    pre = ColumnTransformer([('num', Pipeline([('imp', SimpleImputer(strategy='median', keep_empty_features=True)), ('sc', StandardScaler())]), feats_num),
                             ('cat', OneHotEncoder(drop='first', min_frequency=50, max_categories=40, handle_unknown='ignore'), feats_cat)], sparse_threshold=0.0)
    glm = TweedieRegressor(power=params['power'], alpha=params['alpha'], link=params['link'], solver=params['solver'], max_iter=params['max_iter'], tol=params['tol'], fit_intercept=params['fit_intercept'])
    return Pipeline([('pre', pre), ('glm', glm)])


def _coef_original(pipe, feats_num, feats_cat):
    """Coeficientes en escala original: numéricos beta/escala; categóricos tal cual (log-razón frente a la categoría omitida)."""
    pre = pipe.named_steps['pre']; glm = pipe.named_steps['glm']
    esc = pre.named_transformers_['num'].named_steps['sc'].scale_
    out = {}
    for j, f in enumerate(feats_num):
        out[(f, 'unit')] = float(glm.coef_[j] / esc[j])
    ohe = pre.named_transformers_['cat']
    nombres = ohe.get_feature_names_out(feats_cat)
    for j, nom in enumerate(nombres):
        f = next(c for c in feats_cat if nom.startswith(c + '_'))
        out[(f, nom[len(f) + 1:])] = float(glm.coef_[len(feats_num) + j])
    return out


def r_replay_b19_b20(N: Nuevas, R: Registro, w, salida: pathlib.Path):
    """Reajuste independiente de B19 (alpha 0) y B20 (alpha 1) con la receta declarada; B14 se reajusta también para las comparaciones de ajuste.
    Además, para B19: Hessiano observado, leverage por grupo e influencia local H⁻¹G_g por componente de ajuste (037)."""
    C = N.C
    spec19 = N.plan['dev8']['models'][0] if 'models' in N.plan['dev8'] else None
    plan8 = N.plan['dev8']
    rec19 = next(m for m in plan8['models'] if m['id'] == 'W2-B19') if 'models' in plan8 else plan8['recipe']
    rec20 = N.plan['ridge']['recipe']
    feats19 = rec19['features_by_line']; params19 = rec19['params']; params20 = rec20['params']
    feats20 = rec20['features_by_line']
    spec14 = [mo for mo in C.plan['dev5']['models'] if mo['id'] == 'W2-B13'][0]
    feats14 = spec14['features_by_line']
    cap = C.cap56.set_index('row_id')
    wi = w.set_index('row_id')
    det = dict(receta_B19=dict(features=feats19, params=params19), receta_B20=dict(features=feats20, params=params20), inputs={}, ramos={})
    fallos = 0
    t0 = time.time()
    # inputs de dev8 frente a dev5 + enlace del fold + capital de B14
    for l in LINES:
        base = C.inputs[l]
        d = {}
        for f in range(5):
            i8 = N.inputs8[(l, f)]
            comunes = [c for c in base.columns if c in i8.columns and c != 'x_log_sum_insured']
            iguales = True
            for c in comunes:
                a, b = i8.loc[base.index, c], base[c]
                if a.dtype.kind in 'fc' or b.dtype.kind in 'fc':
                    iguales &= bool(((a.isna() & b.isna()) | np.isclose(a.astype(float), b.astype(float), equal_nan=True)).all())
                else:
                    iguales &= bool(((a.isna() & b.isna()) | (a.astype(str) == b.astype(str))).all())
            link = C.links[(l, f)]
            d[f'fold{f}'] = dict(mismas_filas=set(i8.index) == set(base.index), columnas_de_dev5_iguales=iguales,
                                 C0_igual_al_enlace_del_fold=bool(np.allclose(i8.loc[link.index, 'e_cost_mix_1.0'], link['e_cost_mix_1.0'], atol=1e-12)),
                                 columnas_nuevas=sorted(set(i8.columns) - set(base.columns)))
            if l != 'motor':
                a, b = i8.loc[base.index, 'x_log_sum_insured'], base['x_log_sum_insured']
                distintas = ~((a.isna() & b.isna()) | np.isclose(a.astype(float), b.astype(float), equal_nan=True))
                rows = distintas[distintas].index
                d[f'fold{f}']['capital_distinto_de_dev5'] = dict(filas=int(len(rows)), todas_en_las_56=bool(set(rows) <= set(cap.index)), dev5_vacio=int(b.loc[rows].isna().sum()),
                                                                 dev8_igual_a_log_capital_dividido=bool(np.allclose(a.loc[rows], np.log(cap.loc[rows, 'capital_divided'].astype(float)))) if len(rows) else True)
                fallos += (not d[f'fold{f}']['capital_distinto_de_dev5']['todas_en_las_56']) + (not d[f'fold{f}']['capital_distinto_de_dev5']['dev8_igual_a_log_capital_dividido'])
            fallos += (not d[f'fold{f}']['mismas_filas']) + (not d[f'fold{f}']['columnas_de_dev5_iguales']) + (not d[f'fold{f}']['C0_igual_al_enlace_del_fold'])
        det['inputs'][l] = d
    det['inputs']['capital_B14_en_inputs'] = 'los inputs de dev8 son los de dev5 más el enlace C0 del fold; x_log_sum_insured solo difiere en las 56 filas de capital (vacías en dev5), donde vale log(capital_divided) como en B14; el replay aplica la misma sustitución'
    # replay
    resumen_tv = {(t['model_id'], t['line'], t['fold'], t['role']): t for t in N.diag['dev8']['train_validation']}
    resumen_tv20 = {(t.get('model_id', 'W2-B20'), t['line'], t['fold'], t['role']): t for t in N.diag['ridge']['train_validation']}
    coef_codex = N.est['coef']; coef_codex = coef_codex[coef_codex.model_id == 'W2-B19']
    cs20 = {(r['line'], r['fold']): r for r in N.diag['ridge']['coefficient_stability']['rows']}
    hess_codex = {(h['line'], h['fold']): h for h in N.est['hess']}
    infl_codex = N.est['infl']
    influencia = []   # por componente de ajuste (autos y edificios), para VN26
    fit_dev = {}      # desviancia de ajuste por celda y modelo
    modelos = {}      # (modelo, ramo, fold) -> pipeline ajustado, para la ampliación K (B20-ATTR, bandas, incendio)
    for l in LINES:
        wl = wi[wi.line == l]
        res = dict(B19={}, B20={}, B14={})
        preds = {m: np.full(len(wl), np.nan) for m in ['W2-B19', 'W2-B20', 'W2-B14']}
        coefs = {m: {} for m in ['W2-B19', 'W2-B20']}
        norma2 = {m: {} for m in ['W2-B19', 'W2-B20']}
        for f in range(5):
            X = N.inputs8[(l, f)].loc[wl.index].copy()
            if l != 'motor':
                filas = [r for r in cap.index if r in X.index]
                X.loc[filas, 'x_log_sum_insured'] = np.log(cap.loc[filas, 'capital_divided'].to_numpy(float))
            fit = (wl.fold != f).to_numpy(); val = ~fit
            e = X['e_cost_mix_1.0'].to_numpy(float); y = wl.T0.to_numpy(float) / e; sw = np.sqrt(e)
            for m, feats, params in [('W2-B19', feats19, params19), ('W2-B20', feats20, params20), ('W2-B14', feats14, spec14['params'])]:
                Xf = X[feats[l]['all']].copy()
                for c in feats[l]['categorical']:
                    Xf[c] = Xf[c].astype(object).where(Xf[c].notna(), '__MISSING__').astype(str)
                pipe = _pipeline(feats[l]['numeric'], feats[l]['categorical'], params)
                pipe.fit(Xf[fit], y[fit], glm__sample_weight=sw[fit])
                mu_fit = pipe.predict(Xf[fit]); preds[m][val] = pipe.predict(Xf[val]) * e[val]
                glm = pipe.named_steps['glm']
                modelos[(m, l, f)] = pipe
                fit_dev[(m, l, f)] = metr(wl.T0.to_numpy(float)[fit], mu_fit * e[fit])
                fit_dev[(m, l, f)]['n_iter'] = int(glm.n_iter_)
                if m in coefs:
                    coefs[m][f] = _coef_original(pipe, feats[l]['numeric'], feats[l]['categorical'])
                    norma2[m][f] = float(np.sum(glm.coef_ ** 2))
                if m == 'W2-B19' and l in ('motor', 'buildings'):
                    # Hessiano observado del objetivo de sklearn (1/Σs) Σ s·½d, gradiente por componente, leverage e influencia local H⁻¹G_g
                    Z = pipe.named_steps['pre'].transform(Xf[fit]); Z = Z.toarray() if hasattr(Z, 'toarray') else np.asarray(Z)
                    Z = np.hstack([np.ones((Z.shape[0], 1)), Z]); s = sw[fit] / sw[fit].sum(); yy = y[fit]
                    g_row = s * (mu_fit - yy) / np.sqrt(mu_fit); h_row = s * (mu_fit + yy) / (2 * np.sqrt(mu_fit))
                    H = (Z * h_row[:, None]).T @ Z
                    grad = Z.T @ g_row
                    eig = np.linalg.eigvalsh(H)
                    Hinv = np.linalg.inv(H)
                    codes, grupos = pd.factorize(wl.group_id.to_numpy()[fit], sort=True)
                    G = np.zeros((len(grupos), Z.shape[1])); np.add.at(G, codes, Z * g_row[:, None])
                    lev_row = h_row * np.einsum('ij,jk,ik->i', Z, Hinv, Z); lev = np.bincount(codes, weights=lev_row, minlength=len(grupos))
                    dbeta = G @ Hinv.T   # filas: Δθ ≈ H⁻¹ G_g por grupo
                    nombres = ['intercept'] + list(pipe.named_steps['pre'].get_feature_names_out())
                    esc = pipe.named_steps['pre'].named_transformers_['num'].named_steps['sc'].scale_
                    j_nb = 1 + feats[l]['numeric'].index('x_new_business')
                    if l == 'motor':
                        j_cov = nombres.index('cat__x_cover_type_third_party_only'); esc_cov = 1.0
                    else:
                        j_cov = 1 + feats[l]['numeric'].index('x_accidental_damage_cover'); esc_cov = esc[feats[l]['numeric'].index('x_accidental_damage_cover')]
                    nb_rows = np.bincount(codes, weights=(X['x_new_business'].to_numpy(float)[fit] == 1).astype(float), minlength=len(grupos))
                    T0g = np.bincount(codes, weights=wl.T0.to_numpy(float)[fit], minlength=len(grupos))
                    hc = hess_codex.get((l, f), {})
                    res['B19'][f'hessiano_fold{f}'] = dict(dimension=int(Z.shape[1]), condicion=float(eig.max() / eig.min()), autovalor_min=float(eig.min()), autovalor_max=float(eig.max()),
                                                           max_gradiente_normalizado=float(np.abs(grad).max()), suma_leverage=float(lev.sum()), max_leverage=float(lev.max()),
                                                           codex=dict(condicion=hc.get('condition'), autovalor_min=hc.get('min_eigenvalue'), autovalor_max=hc.get('max_eigenvalue'), max_leverage=hc.get('max_group_leverage'), dimension=hc.get('dimension')))
                    for gi, gid in enumerate(grupos):
                        influencia.append(dict(line=l, fold=f, group_id=gid, training_new_rows=int(nb_rows[gi]), T0_CU=float(T0g[gi]), leverage=float(lev[gi]),
                                               delta_cov=float(dbeta[gi, j_cov] / esc_cov), delta_nb=float(dbeta[gi, j_nb] / esc[feats[l]['numeric'].index('x_new_business')]),
                                               norma_gradiente=float(np.linalg.norm(G[gi]))))
        for m in ['W2-B19', 'W2-B20', 'W2-B14']:
            ref = wl[f'pred_{m}'].to_numpy(float); rel = np.abs(preds[m] / ref - 1)
            res[m[3:]].update(dict(max_dif_rel=float(rel.max()), p99_dif_rel=float(np.quantile(rel, .99)), mediana_dif_rel=float(np.median(rel)), filas=int(len(wl)),
                                   iteraciones=[fit_dev[(m, l, f)]['n_iter'] for f in range(5)], D2_ajuste_por_fold=[fit_dev[(m, l, f)]['D2'] for f in range(5)],
                                   devianza_ajuste_por_fold=[fit_dev[(m, l, f)]['devianza'] for f in range(5)]))
            fallos += res[m[3:]]['max_dif_rel'] > 1e-4
        # coeficientes de B19 frente a la tabla de Codex (escala original) y razones publicadas
        cc = coef_codex[coef_codex.line == l]
        dif = []
        for f in range(5):
            for (feat, lev_), val in coefs['W2-B19'][f].items():
                fila = cc[(cc.fold == f) & (cc.feature == feat) & (cc.level == lev_)]
                if len(fila) == 1:
                    dif.append(abs(float(fila.beta_raw.iloc[0]) - val))
        res['B19']['coeficientes_comparados_con_codex'] = len(dif); res['B19']['max_dif_coeficientes'] = float(max(dif)) if dif else None
        fallos += (not dif) or max(dif) > 1e-6
        razones = {}
        if l == 'motor':
            razones['TPO'] = [float(np.exp(coefs['W2-B19'][f][('x_cover_type', 'third_party_only')])) for f in range(5)]
            razones['TPFT'] = [float(np.exp(coefs['W2-B19'][f][('x_cover_type', 'third_party_fire_theft')])) for f in range(5)]
            razones['TPO_B20'] = [float(np.exp(coefs['W2-B20'][f][('x_cover_type', 'third_party_only')])) for f in range(5)]
            razones['TPFT_B20'] = [float(np.exp(coefs['W2-B20'][f][('x_cover_type', 'third_party_fire_theft')])) for f in range(5)]
        else:
            razones['AD'] = [float(np.exp(coefs['W2-B19'][f][('x_accidental_damage_cover', 'unit')])) for f in range(5)]
            razones['AD_B20'] = [float(np.exp(coefs['W2-B20'][f][('x_accidental_damage_cover', 'unit')])) for f in range(5)]
        razones['NB'] = [float(np.exp(coefs['W2-B19'][f][('x_new_business', 'unit')])) for f in range(5)]
        razones['NB_B20'] = [float(np.exp(coefs['W2-B20'][f][('x_new_business', 'unit')])) for f in range(5)]
        res['razones'] = razones
        # B20 frente a coefficient_stability.json de Codex
        dif20 = []
        for f in range(5):
            r20 = cs20[(l, f)]
            dif20.append(abs(r20['B20_newbusiness_ratio'] - razones['NB_B20'][f])); dif20.append(abs(r20['B19_newbusiness_ratio'] - razones['NB'][f]))
            dif20.append(abs(r20['B20_coverage_ratio'] - razones['TPO_B20' if l == 'motor' else 'AD_B20'][f])); dif20.append(abs(r20['B19_coverage_ratio'] - razones['TPO' if l == 'motor' else 'AD'][f]))
        res['B20']['max_dif_razones_frente_a_codex'] = float(max(dif20)); fallos += max(dif20) > 1e-6
        res['B20']['norma2_coeficientes_B19'] = [norma2['W2-B19'][f] for f in range(5)]; res['B20']['norma2_coeficientes_B20'] = [norma2['W2-B20'][f] for f in range(5)]
        res['B20']['norma_baja_en_los_5_folds'] = bool(all(norma2['W2-B20'][f] < norma2['W2-B19'][f] for f in range(5)))
        res['B19']['ajuste_B19_mejor_que_B14_en_los_5_folds'] = bool(all(fit_dev[('W2-B19', l, f)]['devianza'] < fit_dev[('W2-B14', l, f)]['devianza'] for f in range(5)))
        # ajuste y validación por celda frente a train_validation.json
        dtv = []
        for f in range(5):
            dtv.append(abs(resumen_tv[('W2-B19', l, f, 'fit')]['D2'] - fit_dev[('W2-B19', l, f)]['D2']))
            dtv.append(abs(resumen_tv20[('W2-B20', l, f, 'fit')]['D2'] - fit_dev[('W2-B20', l, f)]['D2']))
        res['max_dif_D2_ajuste_frente_a_train_validation'] = float(max(dtv)); fallos += max(dtv) > 1e-6
        det['ramos'][l] = res
    det['segundos'] = round(time.time() - t0, 1)
    # cifras publicadas sobre coeficientes y ajuste
    P = PUBLICADO_B19; pub = {}; n_pub = fallos_pub = 0
    def chk(nombre, val, p, dec):
        nonlocal n_pub, fallos_pub
        okk = redondeo_igual(val, p, dec); n_pub += 1; fallos_pub += not okk; pub[nombre] = dict(publicado=p, recalculado=float(val), coincide=okk)
    rz = {l: det['ramos'][l]['razones'] for l in LINES}
    for (l, k), (lo, hi) in P['COD-S2-20261024-037']['razones'].items():
        chk(f'037 razon {l} {k} min', min(rz[l][k]), lo, 3); chk(f'037 razon {l} {k} max', max(rz[l][k]), hi, 3)
    for (l, k), (neg, pos) in P['COD-S2-20261024-037']['signos'].items():
        vals = rz[l][k]; nn = sum(v < 1 for v in vals); pp = sum(v > 1 for v in vals)
        n_pub += 1; okk = (nn, pp) == (neg, pos); fallos_pub += not okk; pub[f'037 signos {l} {k}'] = dict(publicado=(neg, pos), recalculado=(nn, pp), coincide=okk)
    chk('doc ridge razon AD edificios B20 min', min(rz['buildings']['AD_B20']), P['GLM_RIDGE_COBERTURAS_2023']['razon_AD_buildings'][0], 3)
    chk('doc ridge razon AD edificios B20 max', max(rz['buildings']['AD_B20']), P['GLM_RIDGE_COBERTURAS_2023']['razon_AD_buildings'][1], 3)
    for l, (lo, hi) in P['GLM_COBERTURAS_2023']['rangos_ajuste_B19'].items():
        vals = det['ramos'][l]['B19']['D2_ajuste_por_fold']; chk(f'doc B19 ajuste min {l}', min(vals), lo, 6); chk(f'doc B19 ajuste max {l}', max(vals), hi, 6)
    n_pub += 2
    det['ajuste_B19_mejor_que_B14_en_15'] = bool(all(det['ramos'][l]['B19']['ajuste_B19_mejor_que_B14_en_los_5_folds'] for l in LINES)); fallos_pub += not det['ajuste_B19_mejor_que_B14_en_15']
    det['norma_B20_baja_en_15'] = bool(all(det['ramos'][l]['B20']['norma_baja_en_los_5_folds'] for l in LINES)); fallos_pub += not det['norma_B20_baja_en_15']
    det['fold_3_edificios_AD_menor_que_uno'] = bool(rz['buildings']['AD'][3] < 1)
    det['frente_a_publicado'] = pub; det['comparaciones_publicadas'] = n_pub; det['fallos_publicados'] = fallos_pub
    peor = max(det['ramos'][l][m]['max_dif_rel'] for l in LINES for m in ['B19', 'B20', 'B14'])
    det['max_dif_rel_45_glm'] = float(peor)
    R.add('VN25', 'Replay', 'Reajuste independiente de B19 (GLM Tweedie 1,5 log sin penalización, siete variables por ramo) y B20 (misma receta con alpha 1), más B14 para comparar el ajuste: predicciones OOF, D² de ajuste por celda, coeficientes en escala original y razones publicadas (037, informe ridge) reproducidos; inputs de dev8 iguales a dev5 más el enlace C0 del fold',
          'pasa' if fallos == 0 and fallos_pub == 0 else 'hallazgo', f'máxima diferencia relativa {peor:.2e} en 45 GLM; {fallos} fallos técnicos; {fallos_pub} de {n_pub} cifras publicadas no coinciden', '< 1e-4, 0 y 0', 'P1' if (fallos or fallos_pub) else '', det)
    infl = pd.DataFrame(influencia)
    return infl, fit_dev, modelos


# ----------------------------------------------------------------------------------------------- VN26 estabilidad e influencia (037)
def s_estabilidad_b19(N: Nuevas, R: Registro, w, infl: pd.DataFrame, salida: pathlib.Path):
    P = PUBLICADO_B19['COD-S2-20261024-037']
    det = {}; fallos_rep = 0; n_pub = fallos_pub = 0; pub = {}
    def chk(nombre, val, p, dec):
        nonlocal n_pub, fallos_pub
        okk = redondeo_igual(val, p, dec); n_pub += 1; fallos_pub += not okk; pub[nombre] = dict(publicado=p, recalculado=float(val), coincide=okk)
    wi = w.copy()
    wi['A'] = wi['dev_W2-B19'] - wi['dev_W2-B14']
    nb = wi.x_new_business.astype(int) == 1
    ambitos = {'buildings': (wi.line == 'buildings').to_numpy(), 'motor_new': ((wi.line == 'motor') & nb).to_numpy()}
    focus_codex = {f['scope']: f for f in N.est['focus']}
    removal_codex = {(r['scope'], r['direction'], r['requested_groups']): r for r in N.est['removal']}
    ranked_codex = N.est['ranked']
    audit = N.C.audit
    audit23 = audit[audit.included_in_T0.astype(bool)]
    peril_por_row = audit23.groupby('row_id').peril.agg(lambda s: '+'.join(sorted(set(s))))
    seleccion = {}
    for amb, mask in ambitos.items():
        s = wi[mask]
        g = s.groupby('group_id').agg(filas=('row_id', 'size'), T0=('T0', 'sum'), A=('A', 'sum'), dev19=('dev_W2-B19', 'sum'), dev14=('dev_W2-B14', 'sum'), fold=('fold', 'first'))
        y = s.T0.to_numpy(float); null = 8 * (np.sqrt(len(y) * y.sum()) - np.sqrt(y).sum())
        delta = float((s['dev_W2-B14'].sum() - s['dev_W2-B19'].sum()) / null)
        bruto_adv = float(g.A[g.A > 0].sum()); bruto_fav = float(-g.A[g.A < 0].sum())
        fc = focus_codex[amb]
        d = dict(filas=int(len(s)), grupos=int(len(g)), delta_B19_menos_B14=delta, perdida_neta=float(g.A.sum()), bruta_adversa=bruto_adv, bruta_favorable=bruto_fav, T0=float(y.sum()),
                 codex=dict(grupos=fc['groups'], delta=fc['delta_B19_minus_B14'], neta=fc['net_loss_delta'], bruta_adversa=fc['gross_adverse_loss'], bruta_favorable=fc['gross_favorable_loss']))
        fallos_rep += (d['grupos'] != fc['groups']) + (abs(delta - fc['delta_B19_minus_B14']) > 1e-9) + (abs(bruto_adv - fc['gross_adverse_loss']) > 1e-6) + (abs(bruto_fav - fc['gross_favorable_loss']) > 1e-6)
        # retiro de cada grupo de la evaluación del ámbito (nula recalculada)
        sy = g.T0.to_numpy(float); sroot = s.groupby('group_id').T0.agg(lambda v: np.sqrt(v.to_numpy(float)).sum()).loc[g.index].to_numpy(); n = g.filas.to_numpy(float)
        N_, SY, SR = n.sum(), sy.sum(), sroot.sum(); D19, D14 = g.dev19.to_numpy(), g.dev14.to_numpy()
        null_sin = 8 * (np.sqrt((N_ - n) * (SY - sy)) - (SR - sroot))
        delta_sin = (D14.sum() - D14 - (D19.sum() - D19)) / null_sin
        loo = N.est['loo']; loo = loo[loo.scope == amb].set_index('group_id').delta_D2_without_group
        d['retiro_individual'] = dict(min=float(delta_sin.min()), max=float(delta_sin.max()), todos_negativos=bool((delta_sin < 0).all()),
                                      max_dif_frente_a_codex=float(np.abs(loo.loc[g.index].to_numpy() - delta_sin).max()))
        fallos_rep += d['retiro_individual']['max_dif_frente_a_codex'] > 1e-9
        # retiros por bloques de 1, 5, 10 y 31 adversos o favorables (orden por A, empate por group_id) y retiro del componente completo en la métrica global
        orden_adv = g.sort_values(['A', 'group_id'], ascending=[False, True]).index.to_list(); orden_fav = g.sort_values(['A', 'group_id'], ascending=[True, True]).index.to_list()
        d['retiros'] = {}
        for direccion, orden in [('adverse', orden_adv), ('favorable', orden_fav)]:
            for k in [1, 5, 10, 31]:
                ids = orden[:k]
                keep = ~s.group_id.isin(ids).to_numpy()
                yk = y[keep]; nullk = 8 * (np.sqrt(len(yk) * yk.sum()) - np.sqrt(yk).sum())
                dk = float((s['dev_W2-B14'].to_numpy()[keep].sum() - s['dev_W2-B19'].to_numpy()[keep].sum()) / nullk)
                keep_g = ~wi.group_id.isin(ids).to_numpy(); yg = wi.T0.to_numpy(float)[keep_g]; nullg = 8 * (np.sqrt(len(yg) * yg.sum()) - np.sqrt(yg).sum())
                dg = float((wi['dev_W2-B14'].to_numpy()[keep_g].sum() - wi['dev_W2-B19'].to_numpy()[keep_g].sum()) / nullg)
                rc = removal_codex[(amb, direccion, k)]
                rk = ranked_codex[(ranked_codex.scope == amb) & (ranked_codex.direction == direccion) & (ranked_codex.requested_groups == k)].sort_values('rank').group_id.to_list()
                d['retiros'][f'{direccion} {k}'] = dict(delta_ambito=dk, delta_global_componente_completo=dg, T0_retirado=float(g.loc[ids, 'T0'].sum()), A_retirada=float(g.loc[ids, 'A'].sum()),
                                                        codex=dict(delta_ambito=rc['delta_scope_D2'], delta_global=rc['delta_global_D2_full_components'], T0=rc['selected_T0']), mismos_grupos_que_codex=rk == ids)
                fallos_rep += (abs(dk - rc['delta_scope_D2']) > 1e-9) + (abs(dg - rc['delta_global_D2_full_components']) > 1e-9) + (rk != ids)
                if (amb, direccion) in P['retiros'] and k in P['retiros'][(amb, direccion)]:
                    chk(f'037 retiro {amb} {direccion} {k}', dk, P['retiros'][(amb, direccion)][k], 6)
        top5 = orden_adv[:5]
        d['cinco_mas_adversos'] = [dict(group_id=gid[:12] + '…', fold=int(g.loc[gid, 'fold']), filas=int(g.loc[gid, 'filas']), T0=float(g.loc[gid, 'T0']), A=float(g.loc[gid, 'A']),
                                        fraccion_bruta_adversa=float(g.loc[gid, 'A'] / bruto_adv), perils=sorted({peril_por_row.get(r, '') for r in s[s.group_id == gid].row_id}),
                                        pred_B19=float(s[s.group_id == gid]['pred_W2-B19'].sum()), pred_B14=float(s[s.group_id == gid]['pred_W2-B14'].sum())) for gid in top5]
        seleccion[amb] = top5
        det[amb] = d
    # cifras publicadas (037)
    b = det['buildings']; m = det['motor_new']
    chk('037 edificios grupos', b['grupos'], P['buildings']['grupos'], 0); chk('037 edificios delta', b['delta_B19_menos_B14'], P['buildings']['delta'], 6)
    chk('037 edificios top5 T0', sum(x['T0'] for x in b['cinco_mas_adversos']), P['buildings']['top5_T0'], 2)
    chk('037 edificios top5 fraccion', sum(x['fraccion_bruta_adversa'] for x in b['cinco_mas_adversos']), P['buildings']['top5_fraccion'], 3)
    chk('037 edificios retiro individual min', b['retiro_individual']['min'], P['buildings']['individual_min'], 6); chk('037 edificios retiro individual max', b['retiro_individual']['max'], P['buildings']['individual_max'], 6)
    n_pub += 2; fallos_pub += not b['retiro_individual']['todos_negativos']; fallos_pub += not all(x['perils'] == ['fire'] for x in b['cinco_mas_adversos'])
    det['edificios_top5_son_incendios'] = bool(all(x['perils'] == ['fire'] for x in b['cinco_mas_adversos']))
    chk('037 autos nuevos grupos', m['grupos'], P['motor_nb']['grupos'], 0); chk('037 autos nuevos delta', m['delta_B19_menos_B14'], P['motor_nb']['delta'], 6)
    pr = m['cinco_mas_adversos'][0]
    chk('037 autos principal T0', pr['T0'], P['motor_nb']['principal_T0'], 2); chk('037 autos principal fraccion', pr['fraccion_bruta_adversa'], P['motor_nb']['principal_fraccion'], 3)
    chk('037 autos principal pred B19', pr['pred_B19'], P['motor_nb']['pred_B19'], 2); chk('037 autos principal pred B14', pr['pred_B14'], P['motor_nb']['pred_B14'], 2)
    chk('037 autos retiro segmento', m['retiros']['adverse 1']['delta_ambito'], P['motor_nb']['retiro_segmento'], 6); chk('037 autos retiro global', m['retiros']['adverse 1']['delta_global_componente_completo'], P['motor_nb']['retiro_global'], 6)
    n_pub += 1; fallos_pub += pr['perils'] != ['bodily_injury']; det['autos_principal_es_lesiones_corporales_una_fila'] = bool(pr['perils'] == ['bodily_injury'] and pr['filas'] == 1)
    # influencia local: Hessianos (condición y leverage) y los dos componentes destacados
    hess = {f'{l} {k}': v for l in ['motor', 'buildings'] for k, v in R.detalle['VN25']['ramos'][l]['B19'].items() if k.startswith('hessiano')}
    cond = [v['condicion'] for v in hess.values()]
    det['hessianos'] = dict(condicion_min=float(min(cond)), condicion_max=float(max(cond)), max_dif_condicion_frente_a_codex=float(max(abs(v['condicion'] - v['codex']['condicion']) for v in hess.values())),
                            max_dif_autovalores=float(max(max(abs(v['autovalor_min'] - v['codex']['autovalor_min']), abs(v['autovalor_max'] - v['codex']['autovalor_max'])) for v in hess.values())),
                            leverage_max_buildings=float(max(v['max_leverage'] for k, v in R.detalle['VN25']['ramos']['buildings']['B19'].items() if k.startswith('hessiano'))),
                            leverage_max_motor=float(max(v['max_leverage'] for k, v in R.detalle['VN25']['ramos']['motor']['B19'].items() if k.startswith('hessiano'))),
                            suma_leverage_igual_a_dimension=bool(all(abs(v['suma_leverage'] - v['dimension']) < 1e-8 for v in hess.values())))
    fallos_rep += (det['hessianos']['max_dif_condicion_frente_a_codex'] > 1e-6) + (det['hessianos']['max_dif_autovalores'] > 1e-8)
    chk('037 condicion min', det['hessianos']['condicion_min'], P['hessianos']['condicion'][0], 1); chk('037 condicion max', det['hessianos']['condicion_max'], P['hessianos']['condicion'][1], 1)
    chk('037 leverage max edificios', det['hessianos']['leverage_max_buildings'], P['hessianos']['leverage_max_buildings'], 3); chk('037 leverage max autos', det['hessianos']['leverage_max_motor'], P['hessianos']['leverage_max_motor'], 3)
    # frente a training_group_local_influence.parquet de Codex (128.084 filas): Δβ de cobertura y de negocio, leverage
    ic = N.est['infl'][['line', 'fold', 'group_id', 'group_leverage_trace', 'local_delete_delta_coverage_beta', 'local_delete_delta_newbusiness_beta', 'training_new_rows', 'T0_CU']]
    j = infl.merge(ic, on=['line', 'fold', 'group_id'], how='inner')
    det['influencia_local'] = dict(filas_comparadas=int(len(j)), filas_codex=int(len(ic)), filas_mias=int(len(infl)),
                                   max_dif_leverage=float((j.leverage - j.group_leverage_trace).abs().max()), max_dif_delta_cobertura=float((j.delta_cov - j.local_delete_delta_coverage_beta).abs().max()),
                                   max_dif_delta_negocio=float((j.delta_nb - j.local_delete_delta_newbusiness_beta).abs().max()), filas_nuevas_iguales=bool((j.training_new_rows_x == j.training_new_rows_y).all()),
                                   T0_igual=bool(np.allclose(j.T0_CU_x, j.T0_CU_y, atol=1e-6)))
    fallos_rep += (len(j) != len(ic)) + (det['influencia_local']['max_dif_leverage'] > 1e-8) + (det['influencia_local']['max_dif_delta_cobertura'] > 1e-8) + (det['influencia_local']['max_dif_delta_negocio'] > 1e-8)
    # los dos componentes destacados
    bi = seleccion['motor_new'][0]; fire = sorted(((g_, det['buildings']['cinco_mas_adversos'][i]['T0']) for i, g_ in enumerate(seleccion['buildings'])), key=lambda t: -abs(t[1] - 286093.0))[-1][0]
    ib = infl[(infl.line == 'motor') & (infl.group_id == bi)].sort_values('fold'); ifr = infl[(infl.line == 'buildings') & (infl.group_id == fire)].sort_values('fold')
    det['componente_lesiones_corporales'] = dict(group_id=bi[:12] + '…', folds_de_ajuste=ib.fold.to_list(), delta_log_TPO=ib.delta_cov.to_list(), delta_log_NB=ib.delta_nb.to_list(), leverage=ib.leverage.to_list(),
                                                 es_el_de_mayor_influencia_absoluta_sobre_TPO_entre_los_nuevos_en_sus_folds=bool(all(
                                                     infl[(infl.line == 'motor') & (infl.fold == f) & (infl.training_new_rows > 0)].set_index('group_id').delta_cov.abs().idxmax() == bi for f in ib.fold)))
    det['componente_incendio_286093'] = dict(group_id=fire[:12] + '…', folds_de_ajuste=ifr.fold.to_list(), delta_log_AD=ifr.delta_cov.to_list(), leverage=ifr.leverage.to_list(),
                                             es_el_de_mayor_influencia_absoluta_sobre_AD_en_sus_folds=bool(all(infl[(infl.line == 'buildings') & (infl.fold == f)].set_index('group_id').delta_cov.abs().idxmax() == fire for f in ifr.fold)))
    chk('037 TPO delta min', min(ib.delta_cov), P['influencia_local']['TPO'][0], 3); chk('037 TPO delta max', max(ib.delta_cov), P['influencia_local']['TPO'][1], 3)
    chk('037 NB delta min', min(ib.delta_nb), P['influencia_local']['NB'][0], 3); chk('037 NB delta max', max(ib.delta_nb), P['influencia_local']['NB'][1], 3)
    chk('037 incendio AD delta min', min(ifr.delta_cov), P['influencia_local']['incendio_286093_AD'][0], 3); chk('037 incendio AD delta max', max(ifr.delta_cov), P['influencia_local']['incendio_286093_AD'][1], 3)
    n_pub += 2; fallos_pub += not det['componente_lesiones_corporales']['es_el_de_mayor_influencia_absoluta_sobre_TPO_entre_los_nuevos_en_sus_folds']; fallos_pub += not det['componente_incendio_286093']['es_el_de_mayor_influencia_absoluta_sobre_AD_en_sus_folds']
    det['frente_a_publicado'] = pub; det['comparaciones_publicadas'] = n_pub; det['fallos_publicados'] = fallos_pub; det['fallos_frente_a_informes'] = int(fallos_rep)
    det['seleccion_top5'] = {k: [g_[:12] + '…' for g_ in v] for k, v in seleccion.items()}
    pd.DataFrame([dict(ambito=amb, retiro=k, **{kk: vv for kk, vv in v.items() if kk != 'codex'}, delta_ambito_codex=v['codex']['delta_ambito'], delta_global_codex=v['codex']['delta_global'])
                  for amb in ambitos for k, v in det[amb]['retiros'].items()]).to_csv(salida / 'tablas' / 'retiros_037.csv', index=False)
    destacados = infl[infl.group_id.isin(set(seleccion['buildings']) | set(seleccion['motor_new']) | {bi, fire})].copy()
    destacados['group_id'] = destacados.group_id.str[:12] + '…'
    destacados.sort_values(['line', 'group_id', 'fold']).to_csv(salida / 'tablas' / 'influencia_local_destacados.csv', index=False)
    pd.DataFrame([dict(celda=k, **{kk: vv for kk, vv in v.items() if kk != 'codex'}, condicion_codex=v['codex']['condicion'], max_leverage_codex=v['codex']['max_leverage']) for k, v in hess.items()]).to_csv(salida / 'tablas' / 'hessianos_b19.csv', index=False)
    R.add('VN26', 'Estabilidad', 'Diagnóstico 037 recalculado desde los OOF y mi replay de B19: pérdida OOF por componente, retiros de 1/5/10/31 grupos (ámbito y global), retiro individual de cada grupo, Hessianos observados, leverage e influencia local H⁻¹G_g de los 128.084 componentes de ajuste coinciden con los artefactos de Codex; los dos componentes destacados (lesiones corporales de 136.767 CU e incendio de 286.093 CU) a la precisión publicada',
          'pasa' if fallos_rep == 0 and fallos_pub == 0 else 'hallazgo', f'{fallos_rep} discrepancias con los artefactos; {fallos_pub} de {n_pub} cifras publicadas no coinciden', '0 y 0', 'P1' if (fallos_rep or fallos_pub) else '', det)
    return seleccion


# ----------------------------------------------------------------------------------------------- VN27 trazabilidad (039)
def t_traza_b19(N: Nuevas, R: Registro, w, infl: pd.DataFrame, seleccion):
    P = PUBLICADO_B19['COD-S2-20261024-039']
    det = {}; fallos_rep = 0; n_pub = fallos_pub = 0; pub = {}
    def chk(nombre, val, p, dec):
        nonlocal n_pub, fallos_pub
        okk = redondeo_igual(val, p, dec); n_pub += 1; fallos_pub += not okk; pub[nombre] = dict(publicado=p, recalculado=float(val), coincide=okk)
    # selección: unión de los cinco más adversos (edificios, autos nuevos) y el de mayor |Δβ cobertura| de cada uno de los diez ajustes de autos y edificios
    ids = set(seleccion['buildings']) | set(seleccion['motor_new'])
    for l in ['motor', 'buildings']:
        for f in range(5):
            t = infl[(infl.line == l) & (infl.fold == f)].set_index('group_id').delta_cov.abs()
            ids.add(t.idxmax())
    sel_codex = set(N.tra['sel'].group_id)
    det['seleccion'] = dict(mia=len(ids), codex=len(sel_codex), iguales=ids == sel_codex, razones_codex=N.tra['sel'].reason.value_counts().to_dict())
    fallos_rep += ids != sel_codex
    chk('039 componentes', len(ids), P['componentes'], 0)
    # periodos de esos componentes y siniestros originales
    per = w[w.group_id.isin(ids)]
    chk('039 periodos', len(per), P['periodos'], 0)
    cl = N.claims.copy()
    cl['loss_date'] = pd.to_datetime(cl.loss_date); cl['report_date'] = pd.to_datetime(cl.report_date)
    audit = N.C.audit.set_index('claim_id')
    pol = N.C.pol.set_index('row_id')
    filas = []
    for _, r in per.iterrows():
        ps, pe = pol.loc[r.row_id, 'period_start'], pol.loc[r.row_id, 'period_end']
        c = cl[(cl.policy_id == pol.loc[r.row_id, 'policy_id']) & (cl.line == r.line) & (cl.loss_date >= ps) & (cl.loss_date <= pe)]
        for _, x in c.iterrows():
            a = audit.loc[x.claim_id] if x.claim_id in audit.index else None
            filas.append(dict(row_id=r.row_id, group_id=r.group_id, line=r.line, claim_id=x.claim_id, peril=x.peril, status=x.status, loss_date=x.loss_date, report_date=x.report_date,
                              paid=float(x.paid_to_date), incurred=float(x.incurred_to_date), recoveries=float(x.recoveries), reserve=float(x.incurred_to_date) - float(x.paid_to_date),
                              T0=float(x.incurred_to_date) - float(x.recoveries), delay=int((x.report_date - x.loss_date).days), reportado_2024=bool(x.report_date.year == 2024),
                              incluido_en_T0=bool(a.included_in_T0) if a is not None else None, row_id_auditoria=(a.row_id if a is not None else None)))
    s = pd.DataFrame(filas)
    s = s[s.incluido_en_T0 == True]  # noqa: E712
    det['siniestros'] = dict(aceptados=int(len(s)), filas_coinciden_con_auditoria=bool((s.row_id == s.row_id_auditoria).all()), ids_iguales_a_codex=set(s.claim_id) == set(N.tra['orig'].claim_id))
    fallos_rep += (not det['siniestros']['ids_iguales_a_codex']) + (not det['siniestros']['filas_coinciden_con_auditoria'])
    chk('039 siniestros', len(s), P['siniestros'], 0)
    por_ramo = s.groupby('line').agg(siniestros=('claim_id', 'size'), pagado=('paid', 'sum'), reserva=('reserve', 'sum'), recuperaciones=('recoveries', 'sum'), T0=('T0', 'sum'))
    det['por_ramo'] = por_ramo.round(2).to_dict('index')
    for l, pr in P['ramo'].items():
        for k, v in pr.items():
            chk(f'039 {l} {k}', por_ramo.loc[l, k], v, 0 if k == 'siniestros' else 2)
    tot = dict(T0=float(s.T0.sum()), reserva=float(s.reserve.sum()), cerrados=int((s.status == 'closed').sum()), abiertos=int((s.status == 'open').sum()))
    tot['cuota_reserva'] = tot['reserva'] / tot['T0']; tot['estres'] = 0.25 * tot['reserva']; tot['estres_pct'] = tot['estres'] / tot['T0']
    det['total'] = tot
    decimales = {'T0': 2, 'reserva': 2, 'cuota': 4, 'cerrados': 0, 'abiertos': 0, 'estres': 2, 'estres_pct': 4}
    for k, v in P['total'].items():
        chk(f'039 total {k}', tot['cuota_reserva'] if k == 'cuota' else tot[k], v, decimales[k])
    # casos destacados
    pri = s[s.line == 'motor'].sort_values('T0', ascending=False).iloc[0]
    det['principal_autos'] = dict(claim=pri.claim_id[:4] + '…', T0=pri.T0, peril=pri.peril, estado=pri.status, perdida=str(pri.loss_date.date()), reporte=str(pri.report_date.date()), demora=int(pri.delay), reserva=pri.reserve, recuperaciones=pri.recoveries,
                                  dias_periodo=int((pol.loc[pri.row_id, 'period_end'] - pol.loc[pri.row_id, 'period_start']).days) + 1, exposicion=float(w.set_index('row_id').loc[pri.row_id, 'exposure']),
                                  nuevo_negocio=bool(w.set_index('row_id').loc[pri.row_id, 'x_new_business'] == 1))
    chk('039 principal T0', pri.T0, P['principal_autos']['T0'], 2); chk('039 principal demora', pri.delay, P['principal_autos']['demora'], 0)
    n_pub += 3; fallos_pub += str(pri.loss_date.date()) != P['principal_autos']['perdida']; fallos_pub += str(pri.report_date.date()) != P['principal_autos']['reporte']; fallos_pub += pri.status != P['principal_autos']['estado']
    ab = s[(s.line == 'buildings') & (s.status == 'open')]
    det['incendio_abierto'] = ab[['peril', 'T0', 'paid', 'reserve']].round(2).to_dict('records')
    n_pub += 1; fallos_pub += len(ab) != 1
    if len(ab) == 1:
        chk('039 incendio abierto T0', ab.T0.iloc[0], P['incendio_abierto']['T0'], 2); chk('039 incendio abierto pagado', ab.paid.iloc[0], P['incendio_abierto']['pagado'], 2); chk('039 incendio abierto reserva', ab.reserve.iloc[0], P['incendio_abierto']['reserva'], 2)
    f286 = s[np.isclose(s.T0, 286093.0)]
    n_pub += 1; fallos_pub += not (len(f286) == 1 and f286.status.iloc[0] == 'closed' and f286.peril.iloc[0] == 'fire')
    if len(f286) == 1:
        chk('039 incendio 286093 demora', f286.delay.iloc[0], P['incendio_286093']['demora'], 0)
    am = s[(s.line == 'motor') & (s.status == 'open')]
    n_pub += 1; fallos_pub += len(am) != 1
    if len(am) == 1:
        chk('039 autos abierto T0', am.T0.iloc[0], P['autos_abierto']['T0'], 2); chk('039 autos abierto pagado', am.paid.iloc[0], P['autos_abierto']['pagado'], 2); chk('039 autos abierto reserva', am.reserve.iloc[0], P['autos_abierto']['reserva'], 2)
    det['demoras'] = dict(min=int(s.delay.min()), max=int(s.delay.max()), mayores_365=int((s.delay > 365).sum()), reportados_2024=int(s.reportado_2024.sum()),
                          recuperaciones_total=float(s.recoveries.sum()), reservas_en_cerrados=int(((s.status == 'closed') & (s.reserve.abs() > 0.004)).sum()))
    for k, v in P['demoras'].items():
        chk(f'039 demora {k}', det['demoras'][k], v, 0)
    # frente a los artefactos de Codex (centavos)
    o = N.tra['orig'].set_index('claim_id'); ss = s.set_index('claim_id')
    det['frente_a_codex'] = dict(max_dif_T0_centavos=float((o.T0_cents / 100 - ss.loc[o.index, 'T0']).abs().max()), max_dif_reserva_centavos=float((o.reserve_cents / 100 - ss.loc[o.index, 'reserve']).abs().max()),
                                 max_dif_pagado=float((o.paid_cents / 100 - ss.loc[o.index, 'paid']).abs().max()), demoras_iguales=bool((o.delay_days == ss.loc[o.index, 'delay']).all()),
                                 periodos_T0_igual_a_base=bool(np.allclose(N.tra['per'].set_index('row_id').T0.astype(float), w.set_index('row_id').loc[N.tra['per'].row_id, 'T0'].astype(float), atol=1e-9)),
                                 periodos_son_los_mismos=set(N.tra['per'].row_id) == set(per.row_id))
    fallos_rep += (det['frente_a_codex']['max_dif_T0_centavos'] > 0.005) + (det['frente_a_codex']['max_dif_reserva_centavos'] > 0.005) + (not det['frente_a_codex']['demoras_iguales']) + (not det['frente_a_codex']['periodos_T0_igual_a_base']) + (not det['frente_a_codex']['periodos_son_los_mismos'])
    # suma de T0 de los periodos frente a la suma de siniestros
    det['T0_periodos_igual_a_siniestros'] = bool(abs(per.T0.astype(float).sum() - s.T0.sum()) < 0.005)
    fallos_rep += not det['T0_periodos_igual_a_siniestros']
    det['frente_a_publicado'] = pub; det['comparaciones_publicadas'] = n_pub; det['fallos_publicados'] = fallos_pub; det['fallos_frente_a_informes'] = int(fallos_rep)
    R.add('VN27', 'Trazabilidad', 'Traza 039 rehecha desde los siniestros originales: la unión de los cinco componentes más adversos (edificios, autos nuevos) y los de mayor influencia local de los diez ajustes da los mismos 12 componentes, 20 periodos y 12 siniestros; pagado, reserva, recuperaciones, T0, estado, fechas y demoras coinciden con los artefactos y con las cifras publicadas',
          'pasa' if fallos_rep == 0 and fallos_pub == 0 else 'hallazgo', f'{fallos_rep} discrepancias con los artefactos; {fallos_pub} de {n_pub} cifras publicadas no coinciden', '0 y 0', 'P1' if (fallos_rep or fallos_pub) else '', det)


# ----------------------------------------------------------------------------------------------- VN28 lectura
def u_lectura_b19_b20(N: Nuevas, R: Registro, rec, res_pares, w):
    orden_anterior = R.detalle['VN16']['orden_global_dev7']
    todos = {m: v for m, v in orden_anterior}
    todos.update({'W2-B19': rec['W2-B19']['global_']['D2'], 'W2-B20': rec['W2-B20']['global_']['D2']})
    orden = sorted(todos.items(), key=lambda t: -t[1])
    det = dict(orden_global_21_recetas=orden, posicion_B20=[m for m, _ in orden].index('W2-B20') + 1, posicion_B19=[m for m, _ in orden].index('W2-B19') + 1,
               B20_frente_a_B10=rec['W2-B20']['global_']['D2'] - todos.get('W2-B10', np.nan),
               nivel=R.detalle['VN23']['nivel'],
               pares={k: dict(delta=v['recalculado']['delta_D2'], intervalo=(v['recalculado']['inferior95'], v['recalculado']['superior95']), tras_retirar=v['recalculado']['delta_tras_retirar'],
                              cruza_cero=v['recalculado']['cruza_cero'], invierte=v['recalculado']['invierte_signo_al_retirar']) for k, v in R.detalle['VN24']['pares'].items()},
               lectura=['B19 empeora el D² global y el intervalo frente a B14 cruza cero: no acredita nada y Codex lo conserva como adverso',
                        'B20 recupera lo perdido por B19 y supera el punto de B14 en +0,0027, con intervalo que cruza cero y signo invertido al retirar 31 grupos; el intervalo positivo frente a B19 compara con una receta peor que B14',
                        'el punto de B20 (0,0894) sigue por debajo de B10 (0,0942) y B08 (0,0932), recetas de tandas anteriores que ningún contraste acreditó',
                        'la contracción cambia el nivel: A/E de B20 1,011 frente a 0,991 de B14 y B19; el nominal condicionado baja 2,0 %; el intercepto del GLM Tweedie con enlace log equilibra (y − μ)/√μ, no y − μ, y al encoger los coeficientes el total predicho cae',
                        'los diagnósticos 037 y 039 describen sensibilidad a siniestros grandes (un siniestro de 136.767 CU concentra el 56 % de la pérdida adversa de autos nuevos; cinco incendios el 31,5 % de edificios); su traza es limpia y no justifica retirarlos'])
    R.add('VN28', 'Lectura', 'Ninguna de las dos recetas nuevas acredita mejora: B19 es adverso; B20 recupera y supera el punto de B14 sin intervalo que lo sostenga y con una caída del nivel de 2 % (A/E 1,011); el mayor punto entre las 21 recetas sigue siendo B10', 'informativo',
          f"orden global: {', '.join(f'{m.replace('W2-', '')} {v:.4f}' for m, v in orden[:6])}; B20 es la {det['posicion_B20']}.ª", '', '', det)
    det = dict(no_verificado=['los 569, 542, 629 y 558 controles internos de Codex y sus adversos (se verifican los resultados, no sus comprobadores)',
                              'la convergencia declarada de los GLM se comprueba por replay (mismas predicciones), no leyendo los modelos serializados (bundle.joblib), que no se copiaron',
                              'la aproximación local H⁻¹G_g se reproduce con la misma convención (Hessiano observado del objetivo de sklearn, intercepto incluido); no se comprueba que esa convención sea la mejor para una retirada exacta',
                              'el diccionario oficial de pagado/incurrido/recuperaciones se toma de la base canónica (VE y VN previos), no se relee aquí',
                              'cualquier cosa de 2024 o del test: siguen cerrados en esta verificación'],
               verificado_por_recalculo=['métricas y segmentos de B19 y B20 (ramo, negocio, cobertura, fold)', 'cinco pares con remuestreo, sorteo a sorteo', 'replay de 45 GLM (B19, B20 y B14) con coeficientes en escala original',
                                         'pérdida OOF por componente, retiros, Hessianos, leverage e influencia local de 128.084 componentes de ajuste', 'trazabilidad de 12 siniestros desde los originales'])
    R.add('VN29', 'Alcance', 'Lo que la ampliación a 035–039 no cubre y lo que sí; sigue siendo revisión de IA con código propio sobre copias con huella, no revisión profesional independiente', 'limite', 'revisión de IA', '', 'P1', det)


def correr_ampliacion(C: Corridas, R: Registro, salida: pathlib.Path):
    t0 = time.time()
    N = Nuevas(C)
    print(f'[{time.time() - t0:5.0f} s] J fuentes nuevas', flush=True); o_fuentes_nuevas(N, R)
    print(f'[{time.time() - t0:5.0f} s] J recetas B19/B20', flush=True); w, rec = p_recetas_b19_b20(N, R, salida)
    print(f'[{time.time() - t0:5.0f} s] J pares', flush=True); res_pares = q_pares_b19_b20(N, R, w, salida)
    print(f'[{time.time() - t0:5.0f} s] J replay B19/B20/B14 e influencia', flush=True); infl, fit_dev, modelos = r_replay_b19_b20(N, R, w, salida)
    print(f'[{time.time() - t0:5.0f} s] J estabilidad 037', flush=True); seleccion = s_estabilidad_b19(N, R, w, infl, salida)
    print(f'[{time.time() - t0:5.0f} s] J traza 039', flush=True); t_traza_b19(N, R, w, infl, seleccion)
    print(f'[{time.time() - t0:5.0f} s] J lectura', flush=True); u_lectura_b19_b20(N, R, rec, res_pares, w)
    return N, dict(w=w, rec=rec, res_pares=res_pares, infl=infl, fit_dev=fit_dev, modelos=modelos, seleccion=seleccion)


# ----------------------------------------------------------------------------------------------- K. ampliación: B20-ATTR, 040–044, B20-BANDS y B20-SYNTH (atribución, contracción, bandas, incendio y AD, síntesis)
NUEVAS_B20 = {'atribucion': 'b20_atribucion_20261024_v1a', 'contraccion': 'contraccion_b20_20261024T023428Z_7f3565db', 'bandas': 'b20_bandas_calibracion_20261024_v1',
              'incendio': 'incendio_AD_b20_20261024T025027Z_87782526', 'sintesis': 'b20_sintesis_20261024_v1'}
REFS = ['W2-B19', 'W2-B14', 'W2-B00']

# Lo que Codex publicó (foro B20-ATTR-RESULT, 041, 042, B20-BANDS-RESULT, 044, B20-SYNTH-RESULT y los cinco informes). Se compara a la precisión impresa.
PUBLICADO_B20 = {
    'ATRIBUCION': {   # foro B20-ATTR-RESULT y docs/semana2/ATRIBUCION_GRUPOS_Y_SEGMENTOS_B20_2023.md
        'tabla': {'W2-B19': (38299.18, 58110.36, -19811.18, 0.006912, -0.003869), 'W2-B14': (14803.66, 48637.02, -33833.36, 0.002672, -0.006513), 'W2-B00': (115251.18, 149206.53, -33955.35, 0.020800, -0.006580)},
        'resto_B14_nula_original': -0.006106, 'cuota_31': 0.001004, 'B14_31': dict(periodos=62, positivos=31, T0=1671486.38, cuota_T0=0.1093),
        'B14_cuotas': dict(neta=3.285, bruta=0.244), 'B14_grupos': dict(positivos=13393, negativos=17476), 'prefijos': {'W2-B14': 3, 'W2-B19': 10, 'W2-B00': 13},
        'segmentos_B14': {('buildings', 1): (0.000568, -0.000240), ('buildings', 0): (0.000374, -0.004673), ('contents', 1): (-0.000103, -0.000272), ('contents', 0): (0.001422, 0.000566),
                          ('motor', 1): (-0.000556, -0.001425), ('motor', 0): (0.000967, -0.000062)},
        'resto_B14_perdidas': dict(buildings_ren=-25890.09, motor_nb=-7894.23, contents_ren=3134.90),
        'resto_por_T0': {'W2-B14': (-28198.55, -5634.81), 'W2-B19': (-2039.30, -17771.88)},
        'terminos_31_B14': (48924.82, -287.80), 'solapamientos': dict(B19_B14=21, B00_B19=5, B00_B14=4),
        'cruzado': {('W2-B19', 'W2-B19'): -0.003869, ('W2-B19', 'W2-B14'): -0.002443, ('W2-B19', 'W2-B00'): 0.007661, ('W2-B14', 'W2-B19'): -0.003658, ('W2-B14', 'W2-B14'): -0.006513,
                    ('W2-B14', 'W2-B00'): 0.005437, ('W2-B00', 'W2-B19'): 0.033220, ('W2-B00', 'W2-B14'): 0.032439, ('W2-B00', 'W2-B00'): -0.006580},
        'doce_fijos': {'W2-B19': 14620.81, 'W2-B14': -16127.18}, 'identidad_log_error': 2.36e-15,
        'medios_32_positivos_B19': dict(total=0.305, intercepto=0.183, negocio=0.005, cobertura=0.051, otros=0.066),
    },
    'CONTRACCION': {   # foro 041/042 y docs/semana2/CONTRACCION_Y_NIVEL_B20_VS_B19_2023.md
        'reduccion_norma': (0.287, 0.614), 'pares_con_coordenadas_crecientes': 14, 'excepciones': 33,
        'razones_B20': {('buildings', 'AD'): (0.801, 1.375), ('motor', 'TPO'): (0.759, 1.005), ('motor', 'TPFT'): (0.758, 0.778), ('motor', 'NB'): (1.972, 2.462), ('buildings', 'NB'): (0.820, 1.144)},
        'niveles': dict(global_=(15436941.83, 15126408.70, -0.0201), doce=(6112.73, 6012.41, -0.0164), cinco_edificios=(2824.70, 2671.88, -0.0541), cinco_autos=(1506.80, 1689.13, 0.1210)),
        'casos': {'BI': dict(T0=136767.16, mu19=90.25, mu20=95.07, razon=1.053425, intercepto=-0.423120, cobertura=0.291127, negocio=-0.002903, otros=0.186943, total=0.052047, ganancia=1478.30),
                  'incendio1': dict(T0=261192.30, mu19=168.39, mu20=244.78, razon=1.454, intercepto=0.243, cobertura=0.004636, negocio=0.002, otros=0.124759, total=0.374102, ganancia=13724.81),
                  'incendio2': dict(T0=286093.00, mu19=340.33, mu20=334.29, razon=0.982, intercepto=0.243, cobertura=0.004636, negocio=0.002, otros=-0.267250, total=-0.017907, ganancia=-557.25)},
        'veinte': dict(ganancia=14620.81, global_=38299.18, cuota=0.382, resto=23678.36), 'incendio1_cuota_doce': 0.939, 'razon_total_doce': 0.984, 'razon_total_global': 0.980,
    },
    'BANDAS': {   # foro B20-BANDS-RESULT y docs/semana2/CALIBRACION_B20_BANDAS_AJUSTE_2023.md
        'AE_global': {'W2-B20': 1.01128, 'W2-B19': 0.99094},
        'AE_B20': {'motor': (1.082, 0.861, 1.038, 1.019, 0.981), 'buildings': (1.966, 1.563, 0.856, 1.198, 0.714), 'contents': (1.226, 1.175, 0.759, 1.444, 0.789)},
        'AE_B19': {('buildings', 1): 2.232, ('buildings', 5): 0.644, ('motor', 5): 0.840, ('motor', 2): 0.905},
        'soporte': {('buildings', 1): (2525, 69, 0.3165, 6.09), ('buildings', 5): (2530, 124, 0.1902, 14.16), ('contents', 1): (3179, 97, 0.0767, 34.40), ('contents', 5): (3155, 110, 0.0825, 38.59),
                    ('motor', 1): (4365, 410, 0.0537, 80.57), ('motor', 5): (4329, 766, 0.0574, 110.78)},
        'autos_nuevos': {1: (0, 0, None), 2: (13, 2, 11.991), 3: (104, 6, 6.786), 5: (2145, 232, 0.823)}, 'autos_nuevos_banda3_mayor_grupo': 0.9391,
        'positivos_nb': dict(buildings=(6, 9), contents=(4, 10)),
        'folds': {('motor', 1): (0.710, 1.897, 2, 3), ('motor', 5): (0.750, 1.354, 2, 3), ('buildings', 1): (0.342, 3.457, 4, 1), ('buildings', 5): (0.285, 1.153, 2, 3), ('contents', 1): (0.653, 1.646, 4, 1), ('contents', 5): (0.545, 1.134, 2, 3)},
        'edificios_banda1_mayor_grupo_en_un_fold': 0.9182, 'fuera_de_rango': dict(total=4, buildings=2, contents=1, motor=1), 'apariciones_ajuste': 200376,
        'score_intercepto_max': 0.00000187, 'AE_ajuste': (0.9873, 1.0417), 'cortes_distintos': 4,
    },
    'INCENDIO': {   # foro 044 y docs/semana2/INCENDIO_Y_AD_B20_2023.md
        'cuotas': dict(neta_doce=0.939, bruta_doce=0.718, neta_global=0.358, bruta_global_componente=0.072, bruta_global_fila=0.066),
        'global_': dict(positiva=190363.86, adversa=152064.68, neta=38299.18, grupos_positivos=12955, grupos_negativos=17914),
        'incendio': dict(ganancia=13724.81, coste=13735.48, prediccion=-10.68), 'sin_incendio': dict(neta=24574.37, delta=0.004480, delta_completo=0.006912),
        'AD_por_fold': {0: (1.245, 1.254, 4017, 6053, 1342128.28, 1275858.24, True), 1: (1.183, 1.194, 4002, 6068, 1311331.73, 1649234.02, True), 2: (1.388, 1.375, 3994, 6067, 1336478.17, 1335134.65, True),
                        3: (0.795, 0.801, 3937, 6056, 581039.46, 1782607.11, False), 4: (1.021, 1.053, 4074, 6052, 1042824.32, 1235746.94, True)},
        'dos_incendios': dict(suma=547285.30, cuota_min=0.408, cuota_max=0.525), 'influencia_B19': dict(incendio1=(-0.0699, -0.0539), incendio2=(-0.1557, -0.0996)),
    },
    'SINTESIS': {   # foro B20-SYNTH-RESULT y docs/semana2/SINTESIS_B20_Y_SIGUIENTE_PASO_2023.md
        'fuentes': 44, 'contraccion': (0.287, 0.614, 33, 14), 'B14': (14803.66, 48637.02, -33833.36, 62, 31, 0.1093, 0.0010), 'nivel': (15436941.83, 15126408.70, 0.0201, -0.0164, 0.1210),
        'casos_ganancia': (1478.30, 13724.81, -557.25), 'cobertura_comun': 0.004636, 'totales_log': (0.374102, -0.017907), 'veinte': (14620.81, 38299.18, 0.382),
        'AE_global': (1.0113, 0.9909), 'bandas_edificios1': (69, 0.3165, 0.342, 3.457), 'bandas_edificios5': (124, 0.714), 'autos_nuevos': (13, 2, 11.991, 104, 6, 6.786, 0.9391, 2145, 232, 0.823),
        'apariciones': 200376, 'fuera_de_rango': 4, 'carencias': 6, 'decisiones': 9,
    },
}


# ----------------------------------------------------------------------------------------------- carga
class NuevasB20:
    def __init__(self, C, raiz_repo: pathlib.Path):
        self.C = C
        self.raiz_repo = raiz_repo  # .../uploads/Hakaton (donde cuelga Hackaton/Repositorio_IAA2026)
        self.dir = {k: C.raiz / v for k, v in NUEVAS_B20.items()}
        self.man = {k: json.load(open(self.dir[k] / 'manifest.json', encoding='utf-8')) for k in NUEVAS_B20}
        self.rep = {k: json.load(open(self.dir[k] / 'report.json', encoding='utf-8')) for k in NUEVAS_B20}
        self.readout = {k: json.load(open(self.dir[k] / 'readout.json', encoding='utf-8')) for k in ['contraccion', 'bandas', 'incendio']}
        a = self.dir['atribucion']
        self.atr = dict(removal=json.load(open(a / 'removal_paths.json', encoding='utf-8')), overlap=json.load(open(a / 'selection_overlap.json', encoding='utf-8')),
                        cross=json.load(open(a / 'cross_selection_removal.json', encoding='utf-8')), seg=pq.read_table(a / 'segment_attribution_2023.parquet').to_pandas(),
                        grp=pq.read_table(a / 'group_attribution_2023.parquet').to_pandas(), logc=pq.read_table(a / 'log_rate_change_components.parquet').to_pandas())
        c = self.dir['contraccion']
        self.con = dict(normas=pq.read_table(c / 'standardized_coefficient_norms.parquet').to_pandas(), per=pq.read_table(c / 'fixed_period_comparison_2023.parquet').to_pandas(),
                        logr=pq.read_table(c / 'fixed_period_logratio_decomposition.parquet').to_pandas(), nivel=json.load(open(c / 'level_diagnostics_2023.json', encoding='utf-8')),
                        fijo=json.load(open(c / 'fixed_gain_attribution.json', encoding='utf-8')), coef=pq.read_table(c / 'coefficients_original_scale.parquet').to_pandas())
        b = self.dir['bandas']
        self.ban = dict(cortes=json.load(open(b / 'band_cuts.json', encoding='utf-8')), celdas=pq.read_table(b / 'calibration_cells_2023.parquet').to_pandas(),
                        filas=pq.read_table(b / 'heldout_bands_2023.parquet').to_pandas())
        i = self.dir['incendio']
        self.inc = dict(conc=json.load(open(i / 'concentration_scopes.json', encoding='utf-8')), adcoef=pq.read_table(i / 'AD_coefficient_by_fold.parquet').to_pandas(),
                        perils=pq.read_table(i / 'AD_peril_composition_by_fold.parquet').to_pandas(), periodos=pq.read_table(i / 'AD_period_composition_by_fold.parquet').to_pandas(),
                        infl=pq.read_table(i / 'existing_B19_local_influence_fixed_fires.parquet').to_pandas(), miembro=pq.read_table(i / 'fixed_fire_training_membership.parquet').to_pandas())
        self.sin = dict(gaps=json.load(open(self.dir['sintesis'] / 'evidence_gaps.json', encoding='utf-8')), journal=json.load(open(self.dir['sintesis'] / 'decision_journal.json', encoding='utf-8')))


def _rel(path, run):
    return path.split(f'{run}/', 1)[1] if f'{run}/' in path else path


def _cover_cols(pipe, l):
    nombres = list(pipe.named_steps['pre'].get_feature_names_out())
    if l == 'motor':
        return [j for j, n in enumerate(nombres) if n.startswith('cat__x_cover_type_')], nombres.index('num__x_new_business')
    return [nombres.index('num__x_accidental_damage_cover')], nombres.index('num__x_new_business')


# ----------------------------------------------------------------------------------------------- VN30 fuentes
def v_fuentes_b20(N: NuevasB20, R: Registro):
    det, ok, n = {}, 0, 0
    for k in ['atribucion', 'contraccion', 'bandas', 'incendio']:
        d = N.dir[k]; files = {_rel(f['path'], NUEVAS_B20[k]): f['sha256'] for f in N.man[k]['files']}
        det[k] = {}
        for p in sorted(d.rglob('*')):
            if p.is_file() and p.name != 'manifest.json':
                rel = p.relative_to(d).as_posix()
                if rel in files:
                    n += 1; igual = sha256(p) == files[rel]; ok += igual; det[k][rel] = igual
                else:
                    det[k][rel] = 'fuera del manifiesto (escrito después)'
        det[k]['_entradas_manifiesto'] = len(files); det[k]['_copiadas'] = sum(1 for v in det[k].values() if isinstance(v, bool))
    # síntesis: manifiesto de entradas (44 fuentes con SHA) y salidas; se comprueban las que están copiadas
    m = N.man['sintesis']; ent = {}; ok_s = n_s = 0
    for grupo in ['inputs', 'outputs']:
        for f in m[grupo]:
            p = N.raiz_repo / f['path']
            if p.exists():
                n += 1; n_s += 1; igual = sha256(p) == f['sha256']; ok += igual; ok_s += igual; ent[f"{grupo}/{'/'.join(f['path'].split('/')[-2:])}"] = igual
    det['sintesis'] = dict(entradas_manifiesto=len(m['inputs']), salidas_manifiesto=len(m['outputs']), comprobadas=n_s, iguales=ok_s, detalle=ent)
    det['informes'] = {k: dict(id=N.rep[k].get('id'), fin=N.rep[k].get('completed_utc')) for k in NUEVAS_B20}
    R.add('VN30', 'Fuentes', 'Huellas de las corridas de atribución (B20-ATTR), contracción (041), bandas (B20-BANDS) e incendio/AD (044) frente a sus manifiestos, y de las fuentes y salidas de la síntesis (B20-SYNTH) que están copiadas',
          'pasa' if ok == n else 'hallazgo', f'{ok} de {n} archivos con huella igual ({n_s} de la síntesis)', 'todas', 'P0' if ok != n else '', det)


# ----------------------------------------------------------------------------------------------- VN31 atribución
def _delta(gain_rows, y_rows):
    null = 8 * (np.sqrt(len(y_rows) * y_rows.sum()) - np.sqrt(y_rows).sum())
    return float(gain_rows.sum() / null), float(null)


def w_atribucion_b20(N: NuevasB20, R: Registro, ctx, salida: pathlib.Path):
    P = PUBLICADO_B20['ATRIBUCION']
    w = ctx['w'].copy()
    y = w.T0.to_numpy(float); mu20 = w['pred_W2-B20'].to_numpy(float)
    nb = (w.x_new_business.astype(int) == 1).to_numpy()
    null_global = 8 * (np.sqrt(len(y) * y.sum()) - np.sqrt(y).sum())
    det = dict(nula_global=float(null_global)); fallos_rep = 0; n_pub = fallos_pub = 0; pub = {}
    def chk(nombre, val, p, dec):
        nonlocal n_pub, fallos_pub
        okk = redondeo_igual(val, p, dec); n_pub += 1; fallos_pub += not okk; pub[nombre] = dict(publicado=p, recalculado=float(val), coincide=okk)
    sel = {}; gan = {}; cum = {}
    rep = {s['reference']: s for s in N.rep['atribucion']['summary']}
    for ref in REFS:
        muref = w[f'pred_{ref}'].to_numpy(float)
        g = w[f'dev_{ref}'].to_numpy(float) - w['dev_W2-B20'].to_numpy(float)
        term_y = 4 * y * (1 / np.sqrt(muref) - 1 / np.sqrt(mu20)); term_mu = 4 * (np.sqrt(muref) - np.sqrt(mu20))
        gan[ref] = g
        gg = pd.DataFrame(dict(group_id=w.group_id.to_numpy(), g=g, y=y, ty=term_y, tm=term_mu, pos=(y > 0).astype(int)))
        G = gg.groupby('group_id').agg(g=('g', 'sum'), filas=('g', 'size'), T0=('y', 'sum'), pos=('pos', 'sum'), ty=('ty', 'sum'), tm=('tm', 'sum')).reset_index()
        G = G.sort_values(['g', 'group_id'], ascending=[False, True]).reset_index(drop=True)
        top = G.iloc[:31]; sel[ref] = set(top.group_id)
        keep = ~w.group_id.isin(sel[ref]).to_numpy()
        d_resto, null_resto = _delta(g[keep], y[keep])
        cums = np.cumsum(G.g.to_numpy()); total = float(g.sum())
        prefijo = int(np.argmax(total - cums < 0) + 1) if (total - cums < 0).any() else None
        cum[ref] = cums
        r = rep[ref]
        res = dict(ganancia_total=total, ganancia_31=float(top.g.sum()), ganancia_resto=float(total - top.g.sum()), delta_completo=float(total / null_global), delta_resto_nula_recalculada=d_resto,
                   delta_resto_nula_original=float((total - top.g.sum()) / null_global), filas_31=int(top.filas.sum()), positivos_31=int(top.pos.sum()), T0_31=float(top.T0.sum()), cuota_T0_31=float(top.T0.sum() / y.sum()),
                   cuota_31_de_componentes=float(31 / G.shape[0]), cuota_neta=float(top.g.sum() / total), cuota_bruta_positiva=float(top.g.sum() / G.g[G.g > 0].sum()),
                   grupos_positivos=int((G.g > 0).sum()), grupos_negativos=int((G.g < 0).sum()), bruta_positiva=float(G.g[G.g > 0].sum()), bruta_negativa=float(G.g[G.g < 0].sum()),
                   termino_coste_31=float(top.ty.sum()), termino_prediccion_31=float(top.tm.sum()), primer_prefijo_adverso=prefijo,
                   resto_positivos=float(g[keep & (y > 0)].sum()), resto_ceros=float(g[keep & (y == 0)].sum()))
        comp = dict(ganancia_dif=abs(total - r['all']['gain']), ganancia_31_dif=abs(res['ganancia_31'] - r['selected31']['gain']), resto_dif=abs(res['ganancia_resto'] - r['remaining']['gain']),
                    delta_resto_dif=abs(d_resto - r['remaining']['delta_own_null']), delta_resto_original_dif=abs(res['delta_resto_nula_original'] - r['remaining']['contribution_full_null']),
                    filas_31_igual=res['filas_31'] == r['selected31']['rows'], positivos_31_igual=res['positivos_31'] == r['selected31']['positive_rows'], T0_31_dif=abs(res['T0_31'] - r['selected31']['observed_total']),
                    grupos_pos_igual=res['grupos_positivos'] == r['positive_gain_groups'], grupos_neg_igual=res['grupos_negativos'] == r['negative_gain_groups'], bruta_pos_dif=abs(res['bruta_positiva'] - r['gross_positive_gain']),
                    prefijo_igual=prefijo == r['first_adverse_prefix_k'], termino_coste_dif=abs(res['termino_coste_31'] - r['selected31']['outcome_term']))
        fallos_rep += (comp['ganancia_dif'] > 1e-6) + (comp['ganancia_31_dif'] > 1e-6) + (comp['resto_dif'] > 1e-6) + (comp['delta_resto_dif'] > 1e-9) + (comp['delta_resto_original_dif'] > 1e-9) + (not comp['filas_31_igual']) + (not comp['positivos_31_igual']) + (comp['T0_31_dif'] > 1e-6) + (not comp['grupos_pos_igual']) + (not comp['grupos_neg_igual']) + (comp['bruta_pos_dif'] > 1e-6) + (not comp['prefijo_igual']) + (comp['termino_coste_dif'] > 1e-6)
        # mismos 31 grupos que Codex
        gc = N.atr['grp']; gc = gc[(gc.reference == ref) & (gc.selected31)]
        comp['mismos_31_grupos'] = set(gc.group_id) == sel[ref]; fallos_rep += not comp['mismos_31_grupos']
        # rutas de retiro 0/1/5/10/31
        rutas = {}
        for k in [1, 5, 10, 31]:
            ids = set(G.group_id.iloc[:k]); kp = ~w.group_id.isin(ids).to_numpy(); dk, _ = _delta(g[kp], y[kp])
            rc = next(x for x in N.atr['removal'] if x['reference'] == ref and x['removed'] == k)
            rutas[k] = dict(delta=dk, ganancia=float(g[kp].sum()), codex=rc['delta_own_null']); fallos_rep += abs(dk - rc['delta_own_null']) > 1e-9
        res['rutas'] = rutas
        res['frente_a_informe'] = comp
        det[ref] = res
        t = P['tabla'][ref]
        chk(f'ATTR {ref} ganancia total', total, t[0], 2); chk(f'ATTR {ref} ganancia 31', res['ganancia_31'], t[1], 2); chk(f'ATTR {ref} ganancia resto', res['ganancia_resto'], t[2], 2)
        chk(f'ATTR {ref} delta completo', res['delta_completo'], t[3], 6); chk(f'ATTR {ref} delta resto', d_resto, t[4], 6)
        chk(f'ATTR {ref} prefijo', prefijo, P['prefijos'][ref], 0)
        chk(f'ATTR {ref} resto positivos', res['resto_positivos'], P['resto_por_T0'][ref][0], 2) if ref in P['resto_por_T0'] else None
        chk(f'ATTR {ref} resto ceros', res['resto_ceros'], P['resto_por_T0'][ref][1], 2) if ref in P['resto_por_T0'] else None
    b14 = det['W2-B14']
    chk('ATTR B14 resto nula original', b14['delta_resto_nula_original'], P['resto_B14_nula_original'], 6); chk('ATTR cuota 31 componentes', b14['cuota_31_de_componentes'], P['cuota_31'], 6)
    chk('ATTR B14 periodos 31', b14['filas_31'], P['B14_31']['periodos'], 0); chk('ATTR B14 positivos 31', b14['positivos_31'], P['B14_31']['positivos'], 0); chk('ATTR B14 T0 31', b14['T0_31'], P['B14_31']['T0'], 2); chk('ATTR B14 cuota T0 31', b14['cuota_T0_31'], P['B14_31']['cuota_T0'], 4)
    chk('ATTR B14 cuota neta', b14['cuota_neta'], P['B14_cuotas']['neta'], 3); chk('ATTR B14 cuota bruta', b14['cuota_bruta_positiva'], P['B14_cuotas']['bruta'], 3)
    chk('ATTR B14 grupos positivos', b14['grupos_positivos'], P['B14_grupos']['positivos'], 0); chk('ATTR B14 grupos negativos', b14['grupos_negativos'], P['B14_grupos']['negativos'], 0)
    chk('ATTR B14 termino coste', b14['termino_coste_31'], P['terminos_31_B14'][0], 2); chk('ATTR B14 termino prediccion', b14['termino_prediccion_31'], P['terminos_31_B14'][1], 2)
    # segmentos B20 frente a B14 con la nula global: aportación antes de retirar y del resto
    g14 = gan['W2-B14']; keep14 = ~w.group_id.isin(sel['W2-B14']).to_numpy()
    segs = {}
    for (l, b), (p_all, p_rest) in P['segmentos_B14'].items():
        m = ((w.line == l).to_numpy()) & (nb if b else ~nb)
        segs[f'{l}_{"nb" if b else "ren"}'] = dict(aportacion=float(g14[m].sum() / null_global), aportacion_resto=float(g14[m & keep14].sum() / null_global), ganancia_resto=float(g14[m & keep14].sum()))
        chk(f'ATTR seg {l} {"nb" if b else "ren"} antes', segs[f'{l}_{"nb" if b else "ren"}']['aportacion'], p_all, 6); chk(f'ATTR seg {l} {"nb" if b else "ren"} resto', segs[f'{l}_{"nb" if b else "ren"}']['aportacion_resto'], p_rest, 6)
    det['segmentos_B14'] = segs
    chk('ATTR resto edificios renovacion', segs['buildings_ren']['ganancia_resto'], P['resto_B14_perdidas']['buildings_ren'], 2); chk('ATTR resto autos nuevos', segs['motor_nb']['ganancia_resto'], P['resto_B14_perdidas']['motor_nb'], 2); chk('ATTR resto contenidos renovacion', segs['contents_ren']['ganancia_resto'], P['resto_B14_perdidas']['contents_ren'], 2)
    # segment_attribution de Codex: todas las filas 'all' por ramo/negocio frente a mi recálculo
    sc = N.atr['seg']; dif = 0.0; nseg = 0
    for _, s in sc.iterrows():
        ref = s['reference']; g = gan[ref]
        if s['cohort'] == 'all':
            m = np.ones(len(w), bool)
        elif s['cohort'] == 'remaining':
            m = np.array(~w.group_id.isin(sel[ref]).to_numpy())
        elif s['cohort'] == 'selected31':
            m = np.array(w.group_id.isin(sel[ref]).to_numpy())
        else:
            continue
        if s['dimension'] == 'line':
            m &= (w.line == s['label']).to_numpy()
        elif s['dimension'] == 'business':
            m &= (nb if s['label'] == 'new_business' else ~nb)
        elif s['dimension'] == 'line_business':
            l, b = s['label'].split('_', 1); m &= (w.line == l).to_numpy() & (nb if b == 'new_business' else ~nb)
        elif s['dimension'] == 'target_state':
            m &= (y > 0) if s['label'] == 'positive' else (y == 0)
        elif s['dimension'] == 'fold':
            m &= (w.fold == int(s['label'])).to_numpy()
        else:
            continue
        nseg += 1; dif = max(dif, abs(float(g[m].sum()) - s['gain']))
    det['segmentos_codex'] = dict(comparados=nseg, max_dif_ganancia=dif); fallos_rep += dif > 1e-6
    # solapamientos y retiro cruzado
    ov = dict(B19_B14=len(sel['W2-B19'] & sel['W2-B14']), B00_B19=len(sel['W2-B00'] & sel['W2-B19']), B00_B14=len(sel['W2-B00'] & sel['W2-B14']))
    det['solapamientos'] = ov
    for k, v in ov.items():
        chk(f'ATTR solapamiento {k}', v, P['solapamientos'][k], 0)
    cruz = {}
    for ref in REFS:
        for sref in REFS:
            kp = ~w.group_id.isin(sel[sref]).to_numpy(); dk, _ = _delta(gan[ref][kp], y[kp])
            cc = next(x for x in N.atr['cross'] if x['reference'] == ref and x['selection_reference'] == sref)
            cruz[f'{ref} / seleccion {sref}'] = dict(delta=dk, codex=cc['delta_own_null']); fallos_rep += abs(dk - cc['delta_own_null']) > 1e-9
            chk(f'ATTR cruzado {ref} {sref}', dk, P['cruzado'][(ref, sref)], 6)
    det['retiro_cruzado'] = cruz
    # doce grupos fijos de B19
    doce = set(ctx['seleccion']['buildings']) | set(ctx['seleccion']['motor_new'])
    infl = ctx['infl']
    for l in ['motor', 'buildings']:
        for f in range(5):
            t = infl[(infl.line == l) & (infl.fold == f)].set_index('group_id').delta_cov.abs(); doce.add(t.idxmax())
    m12 = w.group_id.isin(doce).to_numpy()
    det['doce_fijos'] = {ref: float(gan[ref][m12].sum()) for ref in ['W2-B19', 'W2-B14']}; det['doce_fijos']['grupos'] = int(len(doce)); det['doce_fijos']['filas'] = int(m12.sum())
    chk('ATTR doce B19', det['doce_fijos']['W2-B19'], P['doce_fijos']['W2-B19'], 2); chk('ATTR doce B14', det['doce_fijos']['W2-B14'], P['doce_fijos']['W2-B14'], 2)
    # descomposición del cambio de log-tasa B20 − B19 con mis modelos (intercepto, negocio, cobertura, otros)
    modelos = ctx['modelos']; wi = w.set_index('row_id')
    comp_rows = []
    for l in LINES:
        for f in range(5):
            p19 = modelos[('W2-B19', l, f)]; p20 = modelos[('W2-B20', l, f)]
            idx = wi.index[(wi.line == l) & (wi.fold == f)]
            X = ctx['inputs8'][(l, f)].loc[idx]
            feats = ctx['feats19'][l]
            if l != 'motor':
                cap = ctx['cap56']; filas = [r for r in cap.index if r in X.index]
                X = X.copy(); X.loc[filas, 'x_log_sum_insured'] = np.log(cap.loc[filas, 'capital_divided'].to_numpy(float))
            Xf = X[feats['all']].copy()
            for c in feats['categorical']:
                Xf[c] = Xf[c].astype(object).where(Xf[c].notna(), '__MISSING__').astype(str)
            Z19 = p19.named_steps['pre'].transform(Xf); Z19 = Z19.toarray() if hasattr(Z19, 'toarray') else np.asarray(Z19)
            Z20 = p20.named_steps['pre'].transform(Xf); Z20 = Z20.toarray() if hasattr(Z20, 'toarray') else np.asarray(Z20)
            dZ = float(np.abs(Z19 - Z20).max())
            b19, b20 = p19.named_steps['glm'], p20.named_steps['glm']
            dcoef = b20.coef_ - b19.coef_
            cov_cols, j_nb = _cover_cols(p19, l)
            contrib = Z19 * dcoef[None, :]
            inter = np.full(len(idx), b20.intercept_ - b19.intercept_)
            neg = contrib[:, j_nb]; cov = contrib[:, cov_cols].sum(axis=1)
            otros = contrib.sum(axis=1) - neg - cov
            comp_rows.append(pd.DataFrame(dict(row_id=idx, log_intercept=inter, log_business=neg, log_coverage=cov, log_other=otros, log_change=inter + neg + cov + otros, dZ=dZ)))
    comp = pd.concat(comp_rows).set_index('row_id')
    comp['log_change_oof'] = np.log(wi.loc[comp.index, 'rate_W2-B20'].to_numpy(float) / wi.loc[comp.index, 'rate_W2-B19'].to_numpy(float))
    lc = N.atr['logc'].set_index('row_id').loc[comp.index]
    det['descomposicion_log'] = dict(filas=int(len(comp)), max_dif_disenos=float(comp.dZ.max()), identidad_vs_tasas_oof_max=float((comp.log_change - comp.log_change_oof).abs().max()),
                                     max_dif_frente_a_codex={c: float((comp[c] - lc[c]).abs().max()) for c in ['log_change', 'log_intercept', 'log_business', 'log_coverage', 'log_other']})
    fallos_rep += (det['descomposicion_log']['max_dif_disenos'] > 1e-9) + (det['descomposicion_log']['identidad_vs_tasas_oof_max'] > 1e-6) + (max(det['descomposicion_log']['max_dif_frente_a_codex'].values()) > 1e-6)
    # medias en los 32 periodos positivos de los 31 favorables frente a B19
    m32 = w.group_id.isin(sel['W2-B19']).to_numpy() & (y > 0)
    c32 = comp.loc[w.row_id.to_numpy()[m32]]
    det['medios_32_positivos_B19'] = dict(filas=int(m32.sum()), total=float(c32.log_change.mean()), intercepto=float(c32.log_intercept.mean()), negocio=float(c32.log_business.mean()), cobertura=float(c32.log_coverage.mean()), otros=float(c32.log_other.mean()))
    for k, v in P['medios_32_positivos_B19'].items():
        chk(f'ATTR medio 32 {k}', det['medios_32_positivos_B19'][k], v, 3)
    n_pub += 1; fallos_pub += det['medios_32_positivos_B19']['filas'] != 32
    det['curvas_acumuladas'] = {ref: cum[ref][:200].tolist() for ref in REFS}
    pd.DataFrame({ref: pd.Series(cum[ref][:500]) for ref in REFS}).to_csv(salida / 'tablas' / 'ganancia_acumulada_b20.csv', index_label='grupos_retirados')
    det['frente_a_publicado'] = pub; det['comparaciones_publicadas'] = n_pub; det['fallos_publicados'] = fallos_pub; det['fallos_frente_a_informes'] = int(fallos_rep)
    R.add('VN31', 'Atribución', 'Atribución de la ganancia de B20 (B20-ATTR): ganancias de desviancia por fila, grupo y segmento frente a B19, B14 y B00, los 31 grupos favorables de cada referencia, rutas de retiro, prefijos mínimos, retiro cruzado y descomposición del cambio de log-tasa con mis modelos replicados coinciden con los artefactos y con las cifras publicadas',
          'pasa' if fallos_rep == 0 and fallos_pub == 0 else 'hallazgo', f'{fallos_rep} discrepancias con los artefactos; {fallos_pub} de {n_pub} cifras publicadas no coinciden', '0 y 0', 'P1' if (fallos_rep or fallos_pub) else '', det)
    return dict(gan=gan, sel=sel, comp=comp, doce=doce)


# ----------------------------------------------------------------------------------------------- VN32 contracción y nivel
def x_contraccion_b20(N: NuevasB20, R: Registro, ctx, atr):
    P = PUBLICADO_B20['CONTRACCION']
    w = ctx['w']; wi = w.set_index('row_id'); modelos = ctx['modelos']
    det = {}; fallos_rep = 0; n_pub = fallos_pub = 0; pub = {}
    def chk(nombre, val, p, dec):
        nonlocal n_pub, fallos_pub
        okk = redondeo_igual(val, p, dec); n_pub += 1; fallos_pub += not okk; pub[nombre] = dict(publicado=p, recalculado=float(val), coincide=okk)
    normas = []
    nc = N.con['normas'].set_index(['line', 'fold'])
    for l in LINES:
        for f in range(5):
            b19 = modelos[('W2-B19', l, f)].named_steps['glm'].coef_; b20 = modelos[('W2-B20', l, f)].named_steps['glm'].coef_
            n19, n20 = float(np.sqrt((b19 ** 2).sum())), float(np.sqrt((b20 ** 2).sum()))
            crecen = int((np.abs(b20) > np.abs(b19)).sum())
            c = nc.loc[(l, f)]
            normas.append(dict(line=l, fold=f, L2_B19=n19, L2_B20=n20, reduccion=1 - n20 / n19, coordenadas_crecen=crecen, codex_reduccion=float(c.relative_norm_reduction), codex_crecen=int(c.absolute_coordinates_larger)))
            fallos_rep += (abs(n19 - c.B19_std_L2) > 1e-8) + (abs(n20 - c.B20_std_L2) > 1e-8) + (crecen != c.absolute_coordinates_larger)
    nt = pd.DataFrame(normas)
    det['normas'] = nt.to_dict('records')
    det['reduccion_min'] = float(nt.reduccion.min()); det['reduccion_max'] = float(nt.reduccion.max()); det['contrae_en_15'] = bool((nt.reduccion > 0).all())
    det['pares_con_coordenadas_crecientes'] = int((nt.coordenadas_crecen > 0).sum()); det['excepciones'] = int(nt.coordenadas_crecen.sum())
    chk('CON reduccion min', det['reduccion_min'], P['reduccion_norma'][0], 3); chk('CON reduccion max', det['reduccion_max'], P['reduccion_norma'][1], 3)
    chk('CON pares crecientes', det['pares_con_coordenadas_crecientes'], P['pares_con_coordenadas_crecientes'], 0); chk('CON excepciones', det['excepciones'], P['excepciones'], 0)
    n_pub += 1; fallos_pub += not det['contrae_en_15']
    rz = {l: R.detalle['VN25']['ramos'][l]['razones'] for l in LINES}
    for (l, k), (lo, hi) in P['razones_B20'].items():
        vals = rz[l][f'{k}_B20']; chk(f'CON razon B20 {l} {k} min', min(vals), lo, 3); chk(f'CON razon B20 {l} {k} max', max(vals), hi, 3)
    # niveles sobre ámbitos fijos
    doce = atr['doce']; sel_b = ctx['seleccion']['buildings']; sel_m = ctx['seleccion']['motor_new']
    def nivel(mask):
        return dict(B19=float(wi['pred_W2-B19'].to_numpy()[mask].sum()), B20=float(wi['pred_W2-B20'].to_numpy()[mask].sum()))
    niveles = dict(global_=nivel(np.ones(len(wi), bool)), doce=nivel(wi.group_id.isin(doce).to_numpy()), cinco_edificios=nivel(wi.group_id.isin(sel_b).to_numpy() & (wi.line == 'buildings').to_numpy()),
                   cinco_autos=nivel(wi.group_id.isin(sel_m).to_numpy() & (wi.line == 'motor').to_numpy() & (wi.x_new_business.astype(int) == 1).to_numpy()))
    for k, v in niveles.items():
        v['cambio'] = v['B20'] / v['B19'] - 1
        p19, p20, pc = P['niveles'][k]; chk(f'CON nivel {k} B19', v['B19'], p19, 2); chk(f'CON nivel {k} B20', v['B20'], p20, 2); chk(f'CON nivel {k} cambio', v['cambio'], pc, 4)
    det['niveles'] = niveles
    lv = {x['label']: x for x in N.con['nivel']}
    fallos_rep += (abs(niveles['doce']['B19'] - lv['same12groups20periods']['B19_observed_bridge_total']) > 1e-6) + (abs(niveles['doce']['B20'] - lv['same12groups20periods']['B20_observed_bridge_total']) > 1e-6)
    # tres casos
    comp = atr['comp']; gan19 = pd.Series(atr['gan']['W2-B19'], index=w.row_id.to_numpy())
    casos = {}
    for nombre, rid in [('BI', 'M00015013'), ('incendio1', 'B00026606'), ('incendio2', 'B00028485')]:
        c = comp.loc[rid]; r = wi.loc[rid]
        casos[nombre] = dict(row_id=rid, T0=float(r.T0), mu19=float(r['pred_W2-B19']), mu20=float(r['pred_W2-B20']), razon=float(r['pred_W2-B20'] / r['pred_W2-B19']), intercepto=float(c.log_intercept), cobertura=float(c.log_coverage),
                             negocio=float(c.log_business), otros=float(c.log_other), total=float(c.log_change), ganancia=float(gan19.loc[rid]))
        pc = P['casos'][nombre]
        chk(f'CON {nombre} T0', casos[nombre]['T0'], pc['T0'], 2); chk(f'CON {nombre} mu19', casos[nombre]['mu19'], pc['mu19'], 2); chk(f'CON {nombre} mu20', casos[nombre]['mu20'], pc['mu20'], 2)
        chk(f'CON {nombre} razon', casos[nombre]['razon'], pc['razon'], 6 if nombre == 'BI' else 3); chk(f'CON {nombre} ganancia', casos[nombre]['ganancia'], pc['ganancia'], 2)
        for k in ['intercepto', 'cobertura', 'negocio', 'otros', 'total']:
            dec = len(str(pc[k]).split('.')[1]); chk(f'CON {nombre} {k}', casos[nombre][k], pc[k], dec)
    det['casos'] = casos
    # frente a fixed_period_logratio_decomposition de Codex (20 filas)
    lr = N.con['logr'].set_index('row_id')
    mine = comp.loc[lr.index]
    det['veinte_frente_a_codex'] = dict(max_dif_intercepto=float((mine.log_intercept - lr.delta_intercept).abs().max()), max_dif_cobertura=float((mine.log_coverage - lr.delta_coverage).abs().max()),
                                        max_dif_negocio=float((mine.log_business - lr.delta_newbusiness).abs().max()), max_dif_otros=float((mine.log_other - lr.delta_other_main_effects).abs().max()))
    fallos_rep += max(det['veinte_frente_a_codex'].values()) > 1e-6
    m12 = w.group_id.isin(doce).to_numpy()
    det['veinte'] = dict(ganancia=float(atr['gan']['W2-B19'][m12].sum()), global_=float(atr['gan']['W2-B19'].sum()), filas=int(m12.sum()))
    det['veinte']['cuota'] = det['veinte']['ganancia'] / det['veinte']['global_']; det['veinte']['resto'] = det['veinte']['global_'] - det['veinte']['ganancia']
    chk('CON veinte ganancia', det['veinte']['ganancia'], P['veinte']['ganancia'], 2); chk('CON veinte global', det['veinte']['global_'], P['veinte']['global_'], 2); chk('CON veinte cuota', det['veinte']['cuota'], P['veinte']['cuota'], 3); chk('CON veinte resto', det['veinte']['resto'], P['veinte']['resto'], 2)
    chk('CON incendio1 cuota doce', casos['incendio1']['ganancia'] / det['veinte']['ganancia'], P['incendio1_cuota_doce'], 3)
    chk('CON razon total doce', niveles['doce']['B20'] / niveles['doce']['B19'], P['razon_total_doce'], 3); chk('CON razon total global', niveles['global_']['B20'] / niveles['global_']['B19'], P['razon_total_global'], 3)
    det['frente_a_publicado'] = pub; det['comparaciones_publicadas'] = n_pub; det['fallos_publicados'] = fallos_pub; det['fallos_frente_a_informes'] = int(fallos_rep)
    R.add('VN32', 'Contracción', 'Contracción y nivel de B20 frente a B19 (041/042): normas L2 estandarizadas y coordenadas que crecen en los 15 pares, razones condicionales de B20, niveles sobre los ámbitos fijos (12 grupos, cinco incendios, cinco autos nuevos) y la descomposición del cambio de log-tasa de los tres casos destacados coinciden con los artefactos y con lo publicado',
          'pasa' if fallos_rep == 0 and fallos_pub == 0 else 'hallazgo', f'{fallos_rep} discrepancias con los artefactos; {fallos_pub} de {n_pub} cifras publicadas no coinciden', '0 y 0', 'P1' if (fallos_rep or fallos_pub) else '', det)


# ----------------------------------------------------------------------------------------------- VN33 bandas de calibración
def y_bandas_b20(N: NuevasB20, R: Registro, ctx, salida: pathlib.Path):
    P = PUBLICADO_B20['BANDAS']
    w = ctx['w']; wi = w.set_index('row_id'); modelos = ctx['modelos']
    det = {}; fallos_rep = 0; n_pub = fallos_pub = 0; pub = {}
    def chk(nombre, val, p, dec):
        nonlocal n_pub, fallos_pub
        okk = redondeo_igual(val, p, dec); n_pub += 1; fallos_pub += not okk; pub[nombre] = dict(publicado=p, recalculado=float(val), coincide=okk)
    cortes_codex = {(c['line'], c['fold']): c for c in N.ban['cortes']}
    bandas = pd.Series(index=wi.index, dtype=float); fuera = pd.Series(False, index=wi.index, dtype=bool)
    cortes = {}; apariciones = 0; score_max = 0.0; ae_fit = []
    for l in LINES:
        feats = ctx['feats19'][l]
        for f in range(5):
            pipe = modelos[('W2-B20', l, f)]
            idx_all = wi.index[wi.line == l]
            X = ctx['inputs8'][(l, f)].loc[idx_all]
            if l != 'motor':
                cap = ctx['cap56']; filas = [r for r in cap.index if r in X.index]
                X = X.copy(); X.loc[filas, 'x_log_sum_insured'] = np.log(cap.loc[filas, 'capital_divided'].to_numpy(float))
            Xf = X[feats['all']].copy()
            for c in feats['categorical']:
                Xf[c] = Xf[c].astype(object).where(Xf[c].notna(), '__MISSING__').astype(str)
            fit = (wi.loc[idx_all, 'fold'] != f).to_numpy()
            rates_fit = pipe.predict(Xf[fit]); n = int(fit.sum()); apariciones += n
            srt = np.sort(rates_fit); edges = [float(srt[math.ceil(n * k / 5) - 1]) for k in range(1, 5)]
            e = X['e_cost_mix_1.0'].to_numpy(float)[fit]; yfit = wi.loc[idx_all, 'T0'].to_numpy(float)[fit]
            s = np.sqrt(e); score = float((s * (rates_fit - yfit / e) / np.sqrt(rates_fit)).sum() / s.sum())
            score_max = max(score_max, abs(score)); ae = float(yfit.sum() / (rates_fit * e).sum()); ae_fit.append(ae)
            cc = cortes_codex[(l, f)]
            cortes[f'{l}_fold{f}'] = dict(filas_ajuste=n, cortes=edges, cortes_distintos=len(set(edges)), minimo=float(srt[0]), maximo=float(srt[-1]), score_intercepto=score, AE_ajuste=ae,
                                          codex=dict(edges=cc['edges'], indices=cc['edge_indices0'], min=cc['training_rate_min'], max=cc['training_rate_max'], score=cc['normalized_intercept_score'], AE=cc['fit_AE_not_forced_to_one']))
            fallos_rep += (max(abs(a / b - 1) for a, b in zip(edges, cc['edges'])) > 1e-7) + ([math.ceil(n * k / 5) - 1 for k in range(1, 5)] != cc['edge_indices0']) + (n != cc['fit_rows']) + (abs(ae - cc['fit_AE_not_forced_to_one']) > 1e-7)
            # asignación de las filas OOF del fold por su tasa B20 guardada
            idx_val = idx_all[~fit]; r_oof = wi.loc[idx_val, 'rate_W2-B20'].to_numpy(float)
            bandas.loc[idx_val] = np.searchsorted(np.asarray(edges), r_oof, side='left') + 1
            fuera.loc[idx_val] = (r_oof < srt[0]) | (r_oof > srt[-1])
    det['cortes'] = cortes; det['apariciones_ajuste'] = int(apariciones); det['score_intercepto_max'] = float(score_max); det['AE_ajuste_min'] = float(min(ae_fit)); det['AE_ajuste_max'] = float(max(ae_fit))
    det['cortes_distintos_en_los_15'] = bool(all(v['cortes_distintos'] == 4 for v in cortes.values()))
    hb = N.ban['filas'].set_index('row_id')
    det['bandas_frente_a_codex'] = dict(filas=int(len(bandas)), distintas=int((bandas.astype(int) != hb.loc[bandas.index, 'band']).sum()), fuera_distintas=int((fuera != hb.loc[fuera.index, 'outside_training_rate_range']).sum()))
    fallos_rep += (det['bandas_frente_a_codex']['distintas'] > 0) + (det['bandas_frente_a_codex']['fuera_distintas'] > 0)
    chk('BAN apariciones', apariciones, P['apariciones_ajuste'], 0); chk('BAN score intercepto max', score_max, P['score_intercepto_max'], 8); chk('BAN AE ajuste min', det['AE_ajuste_min'], P['AE_ajuste'][0], 4); chk('BAN AE ajuste max', det['AE_ajuste_max'], P['AE_ajuste'][1], 4)
    n_pub += 1; fallos_pub += not det['cortes_distintos_en_los_15']
    # A/E por ramo y banda (B20 y B19), soporte, concentración y folds
    wb = wi.copy(); wb['banda'] = bandas.astype(int); wb['fuera'] = fuera
    y = wb.T0.to_numpy(float)
    celdas = {}; filas_tabla = []
    for l in LINES:
        for b in range(1, 6):
            m = ((wb.line == l) & (wb.banda == b)).to_numpy()
            if m.sum() == 0:
                celdas[f'{l}_{b}'] = dict(filas=0); continue
            sub = wb[m]
            g = sub.groupby('group_id').T0.sum()
            ae20 = float(sub.T0.sum() / sub['pred_W2-B20'].sum()); ae19 = float(sub.T0.sum() / sub['pred_W2-B19'].sum())
            por_fold = {}
            for f in range(5):
                sf = sub[sub.fold == f]
                por_fold[f] = float(sf.T0.sum() / sf['pred_W2-B20'].sum()) if len(sf) else None
            pf = [v for v in por_fold.values() if v is not None]
            celdas[f'{l}_{b}'] = dict(filas=int(m.sum()), positivos=int((sub.T0 > 0).sum()), grupos_positivos=int((g > 0).sum()), AE_B20=ae20, AE_B19=ae19, mayor_grupo=float(g.max() / g.sum()) if g.sum() > 0 else None,
                                      grupos_equivalentes=float(g.sum() ** 2 / (g ** 2).sum()) if g.sum() > 0 else None, fold_min=min(pf), fold_max=max(pf), folds_mayores_que_uno=int(sum(v > 1 for v in pf)), folds_menores_que_uno=int(sum(v < 1 for v in pf)),
                                      mayor_grupo_en_un_fold=float(max(sub[sub.fold == f].groupby('group_id').T0.sum().max() / sub[sub.fold == f].T0.sum() for f in range(5) if sub[sub.fold == f].T0.sum() > 0)))
            filas_tabla.append(dict(ramo=l, banda=b, **{k: v for k, v in celdas[f'{l}_{b}'].items()}))
    pd.DataFrame(filas_tabla).to_csv(salida / 'tablas' / 'bandas_b20.csv', index=False)
    det['celdas'] = celdas
    # frente al readout de Codex
    rd = {(r['line'], r['band']): r for r in N.readout['bandas']['rows']}
    dif = 0.0
    for (l, b), r in rd.items():
        c = celdas[f'{l}_{b}']
        dif = max(dif, abs(c['AE_B20'] - r['B20_AE']), abs(c['AE_B19'] - r['B19_AE']), abs(c['mayor_grupo'] - r['largest_group_cost_share']), abs(c['grupos_equivalentes'] - r['cost_concentration_equivalent_groups']), abs(c['fold_min'] - r['fold_AE_min']), abs(c['fold_max'] - r['fold_AE_max']))
        fallos_rep += (c['filas'] != r['rows']) + (c['positivos'] != r['positive_periods'])
    det['max_dif_readout'] = float(dif); fallos_rep += dif > 1e-9
    ae_glob = dict(B20=float(y.sum() / wb['pred_W2-B20'].sum()), B19=float(y.sum() / wb['pred_W2-B19'].sum()))
    chk('BAN AE global B20', ae_glob['B20'], P['AE_global']['W2-B20'], 5); chk('BAN AE global B19', ae_glob['B19'], P['AE_global']['W2-B19'], 5)
    for l, vals in P['AE_B20'].items():
        for b, v in enumerate(vals, start=1):
            chk(f'BAN AE B20 {l} {b}', celdas[f'{l}_{b}']['AE_B20'], v, 3)
    for (l, b), v in P['AE_B19'].items():
        chk(f'BAN AE B19 {l} {b}', celdas[f'{l}_{b}']['AE_B19'], v, 3)
    for (l, b), (fil, pos, mg, ge) in P['soporte'].items():
        c = celdas[f'{l}_{b}']; chk(f'BAN soporte {l} {b} filas', c['filas'], fil, 0); chk(f'BAN soporte {l} {b} positivos', c['positivos'], pos, 0); chk(f'BAN soporte {l} {b} mayor grupo', c['mayor_grupo'], mg, 4); chk(f'BAN soporte {l} {b} equivalentes', c['grupos_equivalentes'], ge, 2)
    for (l, b), (lo, hi, up, dn) in P['folds'].items():
        c = celdas[f'{l}_{b}']; chk(f'BAN fold {l} {b} min', c['fold_min'], lo, 3); chk(f'BAN fold {l} {b} max', c['fold_max'], hi, 3); chk(f'BAN fold {l} {b} arriba', c['folds_mayores_que_uno'], up, 0); chk(f'BAN fold {l} {b} abajo', c['folds_menores_que_uno'], dn, 0)
    chk('BAN edificios banda 1 mayor grupo en un fold', celdas['buildings_1']['mayor_grupo_en_un_fold'], P['edificios_banda1_mayor_grupo_en_un_fold'], 4)
    # autos nuevos por banda; nuevo negocio de hogar
    nb = wb.x_new_business.astype(int) == 1
    an = {}
    for b in range(1, 6):
        sub = wb[(wb.line == 'motor') & nb & (wb.banda == b)]
        g = sub.groupby('group_id').T0.sum() if len(sub) else pd.Series(dtype=float)
        an[b] = dict(filas=int(len(sub)), positivos=int((sub.T0 > 0).sum()), AE=float(sub.T0.sum() / sub['pred_W2-B20'].sum()) if len(sub) else None, mayor_grupo=float(g.max() / g.sum()) if len(sub) and g.sum() > 0 else None)
    det['autos_nuevos_por_banda'] = an
    for b, (fil, pos, ae) in P['autos_nuevos'].items():
        chk(f'BAN autos nuevos banda {b} filas', an[b]['filas'], fil, 0); chk(f'BAN autos nuevos banda {b} positivos', an[b]['positivos'], pos, 0)
        if ae is not None:
            chk(f'BAN autos nuevos banda {b} AE', an[b]['AE'], ae, 3)
    chk('BAN autos nuevos banda 3 mayor grupo', an[3]['mayor_grupo'], P['autos_nuevos_banda3_mayor_grupo'], 4)
    pos_nb = {l: [int(((wb.line == l) & nb & (wb.banda == b) & (wb.T0 > 0)).sum()) for b in range(1, 6)] for l in ['buildings', 'contents']}
    det['positivos_nuevo_negocio_hogar_por_banda'] = pos_nb
    for l, (lo, hi) in P['positivos_nb'].items():
        chk(f'BAN positivos nb {l} min', min(pos_nb[l]), lo, 0); chk(f'BAN positivos nb {l} max', max(pos_nb[l]), hi, 0)
    fr = dict(total=int(fuera.sum()), **{l: int(fuera[wi.line == l].sum()) for l in LINES})
    det['fuera_de_rango'] = fr
    for k, v in P['fuera_de_rango'].items():
        chk(f'BAN fuera de rango {k}', fr[k], v, 0)
    det['frente_a_publicado'] = pub; det['comparaciones_publicadas'] = n_pub; det['fallos_publicados'] = fallos_pub; det['fallos_frente_a_informes'] = int(fallos_rep)
    R.add('VN33', 'Calibración', 'Bandas de calibración de B20 (B20-BANDS): quintiles de la tasa de ajuste de mis 15 modelos replicados, asignación de las 50.094 filas OOF, A/E por ramo y banda de B20 y B19, soporte, concentración, rangos por fold, autos nuevos por banda y tasas fuera de rango coinciden con los artefactos y con lo publicado',
          'pasa' if fallos_rep == 0 and fallos_pub == 0 else 'hallazgo', f'{fallos_rep} discrepancias con los artefactos; {fallos_pub} de {n_pub} cifras publicadas no coinciden', '0 y 0', 'P1' if (fallos_rep or fallos_pub) else '', det)
    return wb


# ----------------------------------------------------------------------------------------------- VN34 incendio y AD
def z_incendio_ad_b20(N: NuevasB20, R: Registro, ctx, atr):
    P = PUBLICADO_B20['INCENDIO']
    w = ctx['w']; wi = w.set_index('row_id'); y = w.T0.to_numpy(float)
    det = {}; fallos_rep = 0; n_pub = fallos_pub = 0; pub = {}
    def chk(nombre, val, p, dec):
        nonlocal n_pub, fallos_pub
        okk = redondeo_igual(val, p, dec); n_pub += 1; fallos_pub += not okk; pub[nombre] = dict(publicado=p, recalculado=float(val), coincide=okk)
    g = atr['gan']['W2-B19']; comp = atr['comp']
    gg = pd.DataFrame(dict(group_id=w.group_id.to_numpy(), g=g)).groupby('group_id').g.sum()
    doce = atr['doce']; m12 = w.group_id.isin(doce).to_numpy()
    rid = 'B00026606'; i = int(np.where(w.row_id.to_numpy() == rid)[0][0])
    mu19, mu20 = float(wi.loc[rid, 'pred_W2-B19']), float(wi.loc[rid, 'pred_W2-B20']); t0 = float(wi.loc[rid, 'T0'])
    incendio = dict(ganancia=float(g[i]), coste=float(4 * t0 * (1 / np.sqrt(mu19) - 1 / np.sqrt(mu20))), prediccion=float(4 * (np.sqrt(mu19) - np.sqrt(mu20))), T0=t0, mu19=mu19, mu20=mu20, grupo_una_fila=bool((w.group_id == wi.loc[rid, 'group_id']).sum() == 1))
    g12 = gg.loc[list(doce)]
    glob = dict(positiva=float(gg[gg > 0].sum()), adversa=float(-gg[gg < 0].sum()), neta=float(g.sum()), grupos_positivos=int((gg > 0).sum()), grupos_negativos=int((gg < 0).sum()), positiva_filas=float(g[g > 0].sum()))
    cuotas = dict(neta_doce=incendio['ganancia'] / float(g[m12].sum()), bruta_doce=incendio['ganancia'] / float(g12[g12 > 0].sum()), neta_global=incendio['ganancia'] / glob['neta'], bruta_global_componente=incendio['ganancia'] / glob['positiva'], bruta_global_fila=incendio['ganancia'] / glob['positiva_filas'])
    keep = np.ones(len(w), bool); keep[i] = False
    d_sin, _ = _delta(g[keep], y[keep]); d_full = float(g.sum() / (8 * (np.sqrt(len(y) * y.sum()) - np.sqrt(y).sum())))
    sin = dict(neta=float(g[keep].sum()), delta=d_sin, delta_completo=d_full)
    det.update(incendio=incendio, global_=glob, cuotas=cuotas, sin_incendio=sin)
    cs = N.inc['conc']['scope_statistics']
    fallos_rep += (abs(glob['positiva'] - cs['global']['gross_group_positive_gain']) > 1e-6) + (abs(glob['adversa'] - cs['global']['gross_group_negative_gain_abs']) > 1e-6) + (glob['grupos_positivos'] != cs['global']['positive_groups']) + (abs(sin['delta'] - cs['global_without_fire_row']['derived_delta_D2']) > 1e-9) + (abs(incendio['ganancia'] - cs['fire_row']['net_gain']) > 1e-6)
    for k, v in P['cuotas'].items():
        chk(f'INC cuota {k}', cuotas[k], v, 3)
    for k, v in P['global_'].items():
        chk(f'INC global {k}', glob[k], v, 0 if k.startswith('grupos') else 2)
    for k, v in P['incendio'].items():
        chk(f'INC incendio {k}', incendio[k], v, 2)
    for k, v in P['sin_incendio'].items():
        chk(f'INC sin incendio {k}', sin[k], v, 2 if k == 'neta' else 6)
    # AD por fold: razones (replay), filas de ajuste AD sí/no, T0 de incendios por AD en la vista de ajuste, pertenencia de los dos incendios
    rz = R.detalle['VN25']['ramos']['buildings']['razones']
    pol = N.C.pol.set_index('row_id'); audit = N.C.audit
    fuego = audit[(audit.line == 'buildings') & (audit.peril == 'fire') & (audit.included_in_T0.astype(bool))].groupby('row_id').T0_cents.sum() / 100
    wb = wi[wi.line == 'buildings'].copy(); wb['AD'] = pol.loc[wb.index, 'accidental_damage_cover'].astype(float).to_numpy(); wb['fuego'] = fuego.reindex(wb.index).fillna(0.0).to_numpy()
    dos = ['B00026606', 'B00028485']; suma_dos = float(wb.loc[dos, 'T0'].sum())
    ad = {}
    for f in range(5):
        fit = wb[wb.fold != f]
        ad[f] = dict(razon_B19=rz['AD'][f], razon_B20=rz['AD_B20'][f], filas_AD_si=int((fit.AD == 1).sum()), filas_AD_no=int((fit.AD == 0).sum()), fuego_AD_si=float(fit.fuego[fit.AD == 1].sum()), fuego_AD_no=float(fit.fuego[fit.AD == 0].sum()),
                     ambos_en_ajuste=bool(all(r in fit.index for r in dos)))
        ad[f]['cuota_dos_incendios'] = suma_dos / ad[f]['fuego_AD_si'] if ad[f]['ambos_en_ajuste'] else None
        p = P['AD_por_fold'][f]
        chk(f'INC AD fold {f} razon B19', ad[f]['razon_B19'], p[0], 3); chk(f'INC AD fold {f} razon B20', ad[f]['razon_B20'], p[1], 3); chk(f'INC AD fold {f} filas si', ad[f]['filas_AD_si'], p[2], 0); chk(f'INC AD fold {f} filas no', ad[f]['filas_AD_no'], p[3], 0)
        chk(f'INC AD fold {f} fuego si', ad[f]['fuego_AD_si'], p[4], 2); chk(f'INC AD fold {f} fuego no', ad[f]['fuego_AD_no'], p[5], 2)
        n_pub += 1; fallos_pub += ad[f]['ambos_en_ajuste'] != p[6]
        pc = N.inc['periodos']; pcf = pc[(pc.fold_view == f) & (pc.role == 'fit')]
        fallos_rep += (int(pcf[pcf.AD_group == 'yes'].rows.sum()) != ad[f]['filas_AD_si']) + (int(pcf[pcf.AD_group == 'no'].rows.sum()) != ad[f]['filas_AD_no'])
        pp = N.inc['perils']; ppf = pp[(pp.fold_view == f) & (pp.role == 'fit') & (pp.peril == 'fire')]
        fallos_rep += (abs(float(ppf[ppf.AD_group == 'yes'].T0_cents.sum()) / 100 - ad[f]['fuego_AD_si']) > 0.005) + (abs(float(ppf[ppf.AD_group == 'no'].T0_cents.sum()) / 100 - ad[f]['fuego_AD_no']) > 0.005)
    det['AD_por_fold'] = ad
    det['dos_incendios'] = dict(suma=suma_dos, AD_activado=bool((wb.loc[dos, 'AD'] == 1).all()), fold=wb.loc[dos, 'fold'].astype(int).tolist(), cuota_min=min(v['cuota_dos_incendios'] for v in ad.values() if v['cuota_dos_incendios']), cuota_max=max(v['cuota_dos_incendios'] for v in ad.values() if v['cuota_dos_incendios']))
    chk('INC dos incendios suma', suma_dos, P['dos_incendios']['suma'], 2); chk('INC dos incendios cuota min', det['dos_incendios']['cuota_min'], P['dos_incendios']['cuota_min'], 3); chk('INC dos incendios cuota max', det['dos_incendios']['cuota_max'], P['dos_incendios']['cuota_max'], 3)
    det['AD_negativo_solo_en_fold_3'] = bool([f for f in range(5) if rz['AD'][f] < 1] == [3] and [f for f in range(5) if rz['AD_B20'][f] < 1] == [3]); n_pub += 1; fallos_pub += not det['AD_negativo_solo_en_fold_3']
    # influencia local de B19 (VN25) para los dos incendios
    infl = ctx['infl']; g1 = wi.loc['B00026606', 'group_id']; g2 = wi.loc['B00028485', 'group_id']
    i1 = infl[(infl.line == 'buildings') & (infl.group_id == g1)].sort_values('fold'); i2 = infl[(infl.line == 'buildings') & (infl.group_id == g2)].sort_values('fold')
    det['influencia_B19'] = dict(incendio1=i1.delta_cov.tolist(), incendio2=i2.delta_cov.tolist(), folds=i1.fold.tolist())
    chk('INC influencia incendio1 min', min(i1.delta_cov), P['influencia_B19']['incendio1'][0], 4); chk('INC influencia incendio1 max', max(i1.delta_cov), P['influencia_B19']['incendio1'][1], 4)
    chk('INC influencia incendio2 min', min(i2.delta_cov), P['influencia_B19']['incendio2'][0], 4); chk('INC influencia incendio2 max', max(i2.delta_cov), P['influencia_B19']['incendio2'][1], 4)
    ic = N.inc['infl']; j = ic.merge(infl, on=['line', 'fold', 'group_id']); det['influencia_frente_a_codex'] = dict(filas=int(len(j)), max_dif=float((j.local_delete_delta_coverage_beta - j.delta_cov).abs().max()))
    fallos_rep += (len(j) != 8) + (det['influencia_frente_a_codex']['max_dif'] > 1e-8)
    det['frente_a_publicado'] = pub; det['comparaciones_publicadas'] = n_pub; det['fallos_publicados'] = fallos_pub; det['fallos_frente_a_informes'] = int(fallos_rep)
    R.add('VN34', 'Incendio y AD', 'Incendio fijado y AD por fold (043/044): la ganancia del incendio de 261.192,30 CU con sus cinco denominadores, las ganancias brutas y adversas globales, la exclusión del incendio de la evaluación, las filas y el coste de incendio por AD en cada vista de ajuste y la influencia local de B19 reutilizada coinciden con los artefactos y con lo publicado',
          'pasa' if fallos_rep == 0 and fallos_pub == 0 else 'hallazgo', f'{fallos_rep} discrepancias con los artefactos; {fallos_pub} de {n_pub} cifras publicadas no coinciden', '0 y 0', 'P1' if (fallos_rep or fallos_pub) else '', det)


# ----------------------------------------------------------------------------------------------- VN35 síntesis y VN36 lectura
def aa_sintesis_b20(N: NuevasB20, R: Registro, ctx):
    P = PUBLICADO_B20['SINTESIS']
    det = {}; n_pub = fallos_pub = 0; pub = {}
    def chk(nombre, val, p, dec):
        nonlocal n_pub, fallos_pub
        okk = redondeo_igual(val, p, dec); n_pub += 1; fallos_pub += not okk; pub[nombre] = dict(publicado=p, recalculado=float(val), coincide=okk)
    d31, d32, d33, d34 = R.detalle['VN31'], R.detalle['VN32'], R.detalle['VN33'], R.detalle['VN34']
    chk('SYN fuentes', len(N.man['sintesis']['inputs']), P['fuentes'], 0)
    chk('SYN reduccion min', d32['reduccion_min'], P['contraccion'][0], 3); chk('SYN reduccion max', d32['reduccion_max'], P['contraccion'][1], 3); chk('SYN excepciones', d32['excepciones'], P['contraccion'][2], 0); chk('SYN pares', d32['pares_con_coordenadas_crecientes'], P['contraccion'][3], 0)
    b = d31['W2-B14']
    chk('SYN B14 total', b['ganancia_total'], P['B14'][0], 2); chk('SYN B14 31', b['ganancia_31'], P['B14'][1], 2); chk('SYN B14 resto', b['ganancia_resto'], P['B14'][2], 2); chk('SYN B14 periodos', b['filas_31'], P['B14'][3], 0); chk('SYN B14 positivos', b['positivos_31'], P['B14'][4], 0)
    chk('SYN B14 cuota T0', b['cuota_T0_31'], P['B14'][5], 4); chk('SYN cuota componentes', b['cuota_31_de_componentes'], P['B14'][6], 4)
    nv = d32['niveles']
    chk('SYN nivel B19', nv['global_']['B19'], P['nivel'][0], 2); chk('SYN nivel B20', nv['global_']['B20'], P['nivel'][1], 2); chk('SYN nivel cambio', -nv['global_']['cambio'], P['nivel'][2], 4); chk('SYN doce cambio', nv['doce']['cambio'], P['nivel'][3], 4); chk('SYN cinco autos cambio', nv['cinco_autos']['cambio'], P['nivel'][4], 4)
    for k, v in zip(['BI', 'incendio1', 'incendio2'], P['casos_ganancia']):
        chk(f'SYN ganancia {k}', d32['casos'][k]['ganancia'], v, 2)
    chk('SYN cobertura comun', d32['casos']['incendio1']['cobertura'], P['cobertura_comun'], 6); chk('SYN cobertura comun 2', d32['casos']['incendio2']['cobertura'], P['cobertura_comun'], 6)
    chk('SYN total incendio1', d32['casos']['incendio1']['total'], P['totales_log'][0], 6); chk('SYN total incendio2', d32['casos']['incendio2']['total'], P['totales_log'][1], 6)
    chk('SYN veinte', d32['veinte']['ganancia'], P['veinte'][0], 2); chk('SYN global', d32['veinte']['global_'], P['veinte'][1], 2); chk('SYN cuota veinte', d32['veinte']['cuota'], P['veinte'][2], 3)
    chk('SYN AE B20', R.detalle['VN23']['nivel']['W2-B20']['AE'], P['AE_global'][0], 4); chk('SYN AE B19', R.detalle['VN23']['nivel']['W2-B19']['AE'], P['AE_global'][1], 4)
    c1 = d33['celdas']['buildings_1']; c5 = d33['celdas']['buildings_5']
    chk('SYN edificios1 positivos', c1['positivos'], P['bandas_edificios1'][0], 0); chk('SYN edificios1 mayor grupo', c1['mayor_grupo'], P['bandas_edificios1'][1], 4); chk('SYN edificios1 fold min', c1['fold_min'], P['bandas_edificios1'][2], 3); chk('SYN edificios1 fold max', c1['fold_max'], P['bandas_edificios1'][3], 3)
    chk('SYN edificios5 positivos', c5['positivos'], P['bandas_edificios5'][0], 0); chk('SYN edificios5 AE', c5['AE_B20'], P['bandas_edificios5'][1], 3)
    an = d33['autos_nuevos_por_banda']; q = P['autos_nuevos']
    chk('SYN an2 filas', an['2']['filas'], q[0], 0); chk('SYN an2 positivos', an['2']['positivos'], q[1], 0); chk('SYN an2 AE', an['2']['AE'], q[2], 3); chk('SYN an3 filas', an['3']['filas'], q[3], 0); chk('SYN an3 positivos', an['3']['positivos'], q[4], 0); chk('SYN an3 AE', an['3']['AE'], q[5], 3)
    chk('SYN an3 mayor grupo', an['3']['mayor_grupo'], q[6], 4); chk('SYN an5 filas', an['5']['filas'], q[7], 0); chk('SYN an5 positivos', an['5']['positivos'], q[8], 0); chk('SYN an5 AE', an['5']['AE'], q[9], 3)
    chk('SYN apariciones', d33['apariciones_ajuste'], P['apariciones'], 0); chk('SYN fuera de rango', d33['fuera_de_rango']['total'], P['fuera_de_rango'], 0)
    gaps = N.sin['gaps']; jr = N.sin['journal']
    det['carencias'] = len(gaps['gaps']); det['decisiones'] = len(jr['decisions'])
    chk('SYN carencias', det['carencias'], P['carencias'], 0) if det['carencias'] is not None else None
    chk('SYN decisiones', det['decisiones'], P['decisiones'], 0) if det['decisiones'] is not None else None
    det['frente_a_publicado'] = pub; det['comparaciones_publicadas'] = n_pub; det['fallos_publicados'] = fallos_pub
    R.add('VN35', 'Síntesis', 'Síntesis de B20 (B20-SYNTH): cada cifra que consolida (pares, contracción, 31 grupos, nivel, tres casos, veinte periodos, bandas) se compara con mi recálculo, no con los informes de Codex que la síntesis consultó; las 44 fuentes con huella y las seis carencias y nueve decisiones registradas',
          'pasa' if fallos_pub == 0 else 'hallazgo', f'{fallos_pub} de {n_pub} cifras publicadas no coinciden', '0', 'P1' if fallos_pub else '', det)


def ab_lectura_b20(N: NuevasB20, R: Registro, ctx):
    d31, d33 = R.detalle['VN31'], R.detalle['VN33']
    b14 = d31['W2-B14']
    det = dict(prefijos={ref: d31[ref]['primer_prefijo_adverso'] for ref in REFS}, cuota_T0_31_B14=b14['cuota_T0_31'], cuota_componentes_31=b14['cuota_31_de_componentes'],
               grupos_con_ganancia_positiva_B14=b14['grupos_positivos'], grupos_total=b14['grupos_positivos'] + b14['grupos_negativos'],
               AE_bandas_B20={l: [d33['celdas'][f'{l}_{b}']['AE_B20'] for b in range(1, 6)] for l in LINES},
               autos_nuevos_bandas={b: d33['autos_nuevos_por_banda'][str(b)]['filas'] for b in range(1, 6)},
               cuota_autos_nuevos_banda5=d33['autos_nuevos_por_banda']['5']['filas'] / sum(d33['autos_nuevos_por_banda'][str(b)]['filas'] for b in range(1, 6)),
               AE_bandas_min_max={l: (min(d33['celdas'][f'{l}_{b}']['AE_B20'] for b in range(1, 6)), max(d33['celdas'][f'{l}_{b}']['AE_B20'] for b in range(1, 6))) for l in LINES},
               lectura=['la ventaja de B20 sobre B14 la sostienen 31 componentes (el 0,1 % de los 30.869) con el 10,9 % del coste; sin ellos el resto es adverso en renovación de edificios y en autos nuevos, y bastan los 3 grupos más favorables para invertir el signo',
                        'la mejora frente a B19 también está concentrada: un incendio de 261.192 CU aporta el 36 % de la ganancia neta global y el 94 % de la de los doce grupos fijados',
                        'el A/E global de 1,011 esconde bandas de 0,71 a 1,97 en edificios y de 0,76 a 1,44 en contenidos; en autos nuevos casi todo el nuevo negocio cae en el quintil más alto de tasa y las dos bandas intermedias tienen 2 y 6 periodos positivos',
                        'nada de esto cambia la lectura de 011: B20 no acredita mejora, su nivel baja un 2 % y las decisiones de integración siguen siendo del participante; la síntesis de Codex llega a la misma conclusión y no selecciona ningún B21'])
    R.add('VN36', 'Lectura', 'Lectura de B20-ATTR a B20-SYNTH: la ventaja de B20 la sostienen 31 componentes con el 10,9 % del coste y basta retirar 3 para invertirla frente a B14; un incendio aporta el 36 % de la ganancia frente a B19; el A/E 1,011 esconde bandas de 0,71 a 1,97 en edificios', 'informativo',
          f"prefijos mínimos B14/B19/B00: {det['prefijos']['W2-B14']}/{det['prefijos']['W2-B19']}/{det['prefijos']['W2-B00']}; cuota de coste de los 31 favorables frente a B14 {b14['cuota_T0_31']:.3f}", '', '', det)
    det = dict(no_verificado=['las 1.014, 690, 2.121 y 1.144 comprobaciones internas de Codex, sus adversos y sus comandos de rechazo (se verifican los resultados)',
                              'los 18 MB de atribución por fila (row_attribution_2023.parquet) y los 19 MB de replays de ajuste (training_rate_replays_2023.parquet): no se copiaron; las filas y las tasas de ajuste salen de mis modelos replicados',
                              'las conciliaciones documentales de la síntesis (205) y su registro de decisiones y carencias: se comprueban sus cifras, no su lectura',
                              'el aviso COD-S2-VAL05 sobre la apertura de 2024 de la otra sesión de Claude: fuera de alcance; 2024 y test siguen cerrados aquí'],
               verificado_por_recalculo=['ganancias por fila, grupo y segmento frente a tres referencias, 31 favorables, rutas y retiros cruzados, descomposición de log-tasa de 50.094 filas', 'normas y coordenadas de 15 pares, niveles de ámbitos fijos, tres casos',
                                         'cortes de quintiles de 15 modelos, 50.094 asignaciones, A/E por banda y soporte', 'incendio fijado con cinco denominadores, AD por vista de ajuste, influencia reutilizada', 'cifras de la síntesis'])
    R.add('VN37', 'Alcance', 'Lo que la ampliación a B20-ATTR, 040–044, B20-BANDS y B20-SYNTH no cubre y lo que sí; revisión de IA con código propio sobre copias con huella, no revisión profesional independiente', 'limite', 'revisión de IA', '', 'P1', det)


def correr_ampliacion_b20(C, R: Registro, ctx, salida: pathlib.Path, raiz_repo: pathlib.Path):
    t0 = time.time()
    N = NuevasB20(C, raiz_repo)
    print(f'[{time.time() - t0:5.0f} s] K fuentes B20', flush=True); v_fuentes_b20(N, R)
    print(f'[{time.time() - t0:5.0f} s] K atribución', flush=True); atr = w_atribucion_b20(N, R, ctx, salida)
    print(f'[{time.time() - t0:5.0f} s] K contracción', flush=True); x_contraccion_b20(N, R, ctx, atr)
    print(f'[{time.time() - t0:5.0f} s] K bandas', flush=True); y_bandas_b20(N, R, ctx, salida)
    print(f'[{time.time() - t0:5.0f} s] K incendio y AD', flush=True); z_incendio_ad_b20(N, R, ctx, atr)
    print(f'[{time.time() - t0:5.0f} s] K síntesis y lectura', flush=True); aa_sintesis_b20(N, R, ctx); ab_lectura_b20(N, R, ctx)
    return N


# ----------------------------------------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser()
    raiz_up = pathlib.Path('/mnt/user-data/uploads/Hakaton/Hackaton/Repositorio_IAA2026/privado/semana2')
    ap.add_argument('--corridas', type=pathlib.Path, default=raiz_up / 'desarrollo2023')
    ap.add_argument('--base', type=pathlib.Path, default=raiz_up / 'preparacion' / 'base_20261023T164102Z_b3e6c2a3')
    ap.add_argument('--dev3', type=pathlib.Path, default=raiz_up / 'desarrollo2023' / 'dev3_20261023T181613Z_24c943a3')
    ap.add_argument('--f0', type=pathlib.Path, default=raiz_up / 'ultimo' / 'f0_ultimo_20261023T170841Z_82038766')
    ap.add_argument('--emerging', type=pathlib.Path, default=pathlib.Path('/mnt/user-data/uploads/Hakaton/Hackaton/Semana 2/Datos/emerging'))
    ap.add_argument('--capital-claude', type=pathlib.Path, default=pathlib.Path('/home/claude/s2dec/final_privado/capital_caps2_01.parquet'))
    ap.add_argument('--out', type=pathlib.Path, default=AQUI)
    ap.add_argument('--raiz-repo', type=pathlib.Path, default=None, help='raíz donde cuelga Hackaton/Repositorio_IAA2026 (por defecto, cuatro niveles sobre --corridas)')
    ap.add_argument('--sin-replay', action='store_true')
    a = ap.parse_args()
    (a.out / 'tablas').mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    print('cargando corridas', flush=True)
    C = Corridas(a.corridas, a.base, a.dev3, a.f0, a.emerging, a.capital_claude, a.out)
    R = Registro()
    print(f'[{time.time() - t0:5.0f} s] A fuentes', flush=True); a_fuentes(C, R)
    print(f'[{time.time() - t0:5.0f} s] B recetas', flush=True); recalculado = b_recetas(C, R, a.out); c_constantes(C, R)
    print(f'[{time.time() - t0:5.0f} s] C capital, credibilidad, ablaciones', flush=True); d_capital_credibilidad(C, R, recalculado)
    print(f'[{time.time() - t0:5.0f} s] D influencia', flush=True); e_influencia(C, R, a.out)
    print(f'[{time.time() - t0:5.0f} s] E cola y mecanismo', flush=True); f_cola(C, R); g_mecanismo(C, R)
    if not a.sin_replay:
        print(f'[{time.time() - t0:5.0f} s] F replay GLM', flush=True); h_replay_glm(C, R)
    print(f'[{time.time() - t0:5.0f} s] G estabilidad', flush=True); j_estabilidad(C, R)
    print(f'[{time.time() - t0:5.0f} s] H límites', flush=True); i_limites(C, R, recalculado)
    print(f'[{time.time() - t0:5.0f} s] I ampliación 028–033', flush=True); k_mezcla(C, R); l_escasez(C, R); m_coberturas(C, R); n_calendario(C, R)
    print(f'[{time.time() - t0:5.0f} s] J ampliación 035–039', flush=True); N, ctx = correr_ampliacion(C, R, a.out)
    ctx['inputs8'] = N.inputs8; ctx['feats19'] = N.plan['dev8']['recipe']['features_by_line']; ctx['cap56'] = C.cap56.set_index('row_id')
    print(f'[{time.time() - t0:5.0f} s] K ampliación B20-ATTR a B20-SYNTH', flush=True); N2 = correr_ampliacion_b20(C, R, ctx, a.out, a.raiz_repo or a.corridas.parents[4])
    por_res = pd.Series([c['resultado'] for c in R.controles]).value_counts().to_dict()
    import platform, sklearn, scipy
    ev = dict(autor='Claude (Cowork)', utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
              entorno=dict(python=platform.python_version(), pandas=pd.__version__, numpy=np.__version__, sklearn=sklearn.__version__, scipy=scipy.__version__),
              corridas={k: dict(carpeta=RUNS[k], id_informe=C.rep[k].get('id'), oof_sha256=R.detalle['VN01']['oof_sha256'].get(k if k in ('dev5', 'dev6', 'dev7') else {'cola': 'cola_stress', 'mecanismo': 'mecanismo', 'mezcla': 'mezcla', 'soporte': None, 'coberturas': None}[k])) for k in RUNS},
              corridas_nuevas={k: dict(carpeta=NUEVAS[k], id_informe=N.rep[k].get('id'), fin=N.rep[k].get('completed_utc'), new_oof_sha256=(sha256(N.dir[k] / 'new_oof_2023.parquet') if (N.dir[k] / 'new_oof_2023.parquet').exists() else None)) for k in NUEVAS},
              corridas_b20={k: dict(carpeta=NUEVAS_B20[k], id_informe=N2.rep[k].get('id'), fin=N2.rep[k].get('completed_utc')) for k in NUEVAS_B20},
              publicado=to_py(PUBLICADO), publicado_b19=to_py(PUBLICADO_B19), publicado_b20=to_py(PUBLICADO_B20),
              resumen=dict(controles=len(R.controles), por_resultado=por_res, hallazgos=[c for c in R.controles if c['resultado'] == 'hallazgo'], limites=[c for c in R.controles if c['resultado'] == 'limite']),
              controles=R.controles, detalle=R.detalle, segundos=round(time.time() - t0))
    (a.out / 'evidencia_nocturna.json').write_text(json.dumps(to_py(ev), ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    pd.DataFrame(R.controles).to_csv(a.out / 'tablas' / 'controles.csv', index=False)
    print(f'[{time.time() - t0:5.0f} s] {len(R.controles)} controles: {por_res}', flush=True)


if __name__ == '__main__':
    main()
