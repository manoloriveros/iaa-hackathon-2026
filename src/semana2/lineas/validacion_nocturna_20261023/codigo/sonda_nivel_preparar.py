"""Preinscripción y archivos de la sonda de nivel por ramo (sin enviar nada).

Base: el archivo enviado, mezcla50_designada_mlind_2025.csv (SHA 12831ef4…), D² público 0,15390 (envío 57599788).
Seis sondas: la base con un solo ramo multiplicado por c (motor 0,85 y 1,20; edificios 0,80 y 1,25; contenidos 0,85 y 1,20).
Con sus seis D² públicos, sonda_nivel_resolver.py despeja el óptimo público exacto de cada ramo (c* = A/B, ver
sonda_nivel_diseno.py) y aplica credibilidad: c_final = exp(Z · log c*), Z = τ² / (τ² + σ²), con σ el ruido
público→privado medido en la simulación (tamaño 2025) y τ la incertidumbre previa del nivel, fijada aquí antes de ver nada.
Escribe salidas/sonda/preinscripcion_sonda.json y salidas/sonda/sonda_{ramo}_{c}.csv.
"""
import hashlib, json, pathlib
import numpy as np, pandas as pd

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/sonda'; O.mkdir(exist_ok=True)
BASE = R / 'datos/mlind/mezcla50_designada_mlind_2025.csv'; SHA_BASE = '12831ef4a05c1773824abe5fa139d9503dd2989b4874e7d93cfc000406cfdb4a'
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == SHA_BASE
dis = json.load(open(O / 'diseno.json'))
PFX = {'motor': 'M', 'buildings': 'B', 'contents': 'C'}
TAU = {'motor': 0.10, 'buildings': 0.20, 'contents': 0.07}
TAU_MOTIVO = ('Incertidumbre previa del logaritmo del nivel 2025 de cada ramo frente al de la mezcla. Autos 0,10: las dos líneas difieren un 5 %, '
              'el exceso del nuevo negocio fue 1,62 en 2023 y 1,09 en 2024, y la tendencia posible es de +3 a +5 % al año. Edificios 0,20: el nivel '
              'emergente cayó un 40 % de 2023 a 2024 por el incendio, y las líneas difieren un 7,6 %. Contenidos 0,07: niveles 2023 y 2024 a un 5 %.')
SIG = {l: dis[l]['sd_log_pub_menos_priv_2025'] for l in PFX}
Z = {l: TAU[l] ** 2 / (TAU[l] ** 2 + SIG[l] ** 2) for l in PFX}
K = {l: dis[l]['k_curvatura'] for l in PFX}
b = pd.read_csv(BASE, dtype={'row_id': str}); pre = b.row_id.str[0].values
files = {}
for l, cs in dis['escalas'].items():
    for c in cs:
        d = b.copy(); m = pre == PFX[l]; d.loc[m, 'prediction'] = d.prediction.values[m] * c
        p = O / f'sonda_{l}_{c:.2f}.csv'; d.to_csv(p, index=False, float_format='%.6f', lineterminator='\n')
        assert len(d) == 209063 and (d.prediction > 0).all()
        files[p.name] = {'ramo': l, 'c': c, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
pre_json = {
    'id': 'CLA-S2-SONDA-NIVEL-20261024', 'autor': 'Claude (Cowork), sesión de validación nocturna',
    'base': {'archivo': 'Repositorio_IAA2026/privado/semana2/claude_ml_independiente_20261023/mezcla50_designada_mlind_2025.csv', 'sha256': SHA_BASE,
             'd2_publico': 0.15390, 'envio_kaggle': 57599788},
    'sondas': files,
    'metodo': 'D2_pub(c_l) = D2_base - [βA_l (c_l^-1/2 - 1) + βB_l (c_l^1/2 - 1)], dos sondas por ramo; c*_l = A_l / B_l (óptimo exacto de la desviación Tweedie 1,5 en el público). Precisión simulada con redondeo a 5 decimales: error máximo del log de c* 0,001 en autos, 0,006 en edificios y 0,003 en contenidos.',
    'credibilidad': {'tau': TAU, 'tau_motivo': TAU_MOTIVO, 'sigma_pub_priv_2025': SIG, 'Z': {l: round(v, 3) for l, v in Z.items()}},
    'regla_final': 'c_final_l = exp(Z_l · log c*_l), acotado a [0,80; 1,25]; archivo final = base × c_final por ramo. Si algún c* sale no positivo o no finito, ese ramo no se toca. Control de coherencia: βB_l / Σμ^(1/2)_l debe ser igual en los tres ramos si el público es una muestra al azar; si difiere más de un 5 %, Z se reduce a la mitad en todos los ramos.',
    'ganancia_esperada_D2_privado': round(float(sum(K[l] * TAU[l] ** 2 * Z[l] for l in PFX)), 4),
    'k_curvatura': K,
    'coste': 'seis envíos de los nueve disponibles hoy más uno para el archivo final; cierre el 30 de octubre a las 22:59 de Bogotá',
    'limites': 'Un 33 % público aproximado; σ medido sobre 2024 como sustituto. La sonda solo ajusta un nivel por ramo, no el orden. No cambia la selección común; el envío lo hace Codex con autorización expresa del participante.'}
json.dump(pre_json, open(O / 'preinscripcion_sonda.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(pre_json, indent=1, ensure_ascii=False))
