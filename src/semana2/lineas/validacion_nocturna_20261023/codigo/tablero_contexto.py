"""Contexto para leer el tablero público del 24-10 (cifras citadas en el informe, sección 10, y en la bitácora).

- Tablero tal como lo compartió el participante (captura del 24-10): puntuaciones públicas y envíos de los siete equipos.
- Real/esperado de 2024 por ramo con el nivel de 2023 (designada A1fixF1b3n, neutral) y su óptimo Tweedie global.
- Cuota de nuevo negocio por año (2023, 2024, test 2025) y real/esperado del nuevo negocio frente a renovaciones por ramo y año
  (2023: OOF del desarrollo con nivel por balance en cada fold; 2024: designada con nivel 2023).
Escribe salidas/sonda_global/contexto.json.
"""
import io, contextlib, json, pathlib, runpy, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
R = pathlib.Path('/home/claude/noche'); LINES = ['motor', 'buildings', 'contents']
tablero = {'fuente': 'captura del participante, 24-10-2026', 'equipos': [
    ['applause_bin', 0.16446, 10], ['Simone', 0.16324, 10], ['Krishna Shrestha', 0.16319, 8], ['Alex Scott', 0.16170, 1],
    ['Jasper Dube', 0.15736, 9], ['Fogarium', 0.15454, 10], ['ManuelRodríguez', 0.15390, 2]]}
tablero['distancia_al_primero'] = round(0.16446 - 0.15390, 5); tablero['distancia_al_cuarto'] = round(0.16170 - 0.15390, 5)
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(R / 'codigo/evaluar_final.py'))
P, y = g['P'], g['y']; mu = P['A1fixF1b3n'].values; ln = P.line.values
B = pd.concat([pd.read_parquet(R / f'salidas/s2/base_{l}.parquet', columns=['row_id', 'split', 'year', 'new_business']) for l in LINES]).set_index('row_id')
ae24 = {l: round(float(y[ln == l].sum() / mu[ln == l].sum()), 3) for l in LINES}
cuota = {str(k): round(float(v), 3) for k, v in B[B.split == 'train'].groupby('year').new_business.mean().items()}
cuota['2025'] = round(float(B[B.split == 'test'].new_business.mean()), 3)
o = pd.read_parquet(R / 'salidas/s2/oof/A1fixF1b3_nivel.parquet').set_index('row_id')
rel = {}
for nm, df, m in [('2023', o, o.mu.values), ('2024', P.assign(y=y), mu)]:
    nb = B.loc[df.index, 'new_business'].values.astype(bool)
    for l in LINES:
        k = (df.line.values == l)
        ae_nb = df.y.values[k & nb].sum() / m[k & nb].sum(); ae_rn = df.y.values[k & ~nb].sum() / m[k & ~nb].sum()
        rel[f'{l}_{nm}'] = round(float(ae_nb / ae_rn), 2)
out = {'tablero': tablero, 'real_esperado_2024_nivel_2023': ae24, 'real_esperado_2024_global': round(float(y.sum() / mu.sum()), 3),
       'cuota_nuevo_negocio': cuota, 'nb_frente_a_renovacion_real_esperado': rel,
       'nb_relativo_min_max': [min(rel.values()), max(rel.values())]}
json.dump(out, open(R / 'salidas/sonda_global/contexto.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
