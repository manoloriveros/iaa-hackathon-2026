"""Opción para el participante: mezcla 50/50 de la producción designada (A1fixF1b3n) con T2b de la línea ML independiente,
con el total por ramo de la designada (T2b se reescala por ramo antes de promediar, así que se respeta el nivel decidido,
sin tendencia). Pesos fijados en 50/50 sin ajustar. Escribe salidas/correccion/A1fixF1b3n_mlind50n_2025.csv. Sin enviar.
"""
import hashlib, json, pathlib
import numpy as np, pandas as pd
R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/correccion'
rd = lambda p: pd.read_csv(p, dtype={'row_id': str})
a = rd(O / 'A1fixF1b3n_2025.csv'); b = rd(R / 'datos/mlind/prediccion_2025_mlind.csv')
ss = pd.read_parquet(R / 'datos/s2/sample_submission.parquet')
assert (a.row_id.values == ss.row_id.values).all() and set(b.row_id) == set(a.row_id) and b.row_id.is_unique and (b.prediction > 0).all()
b = b.set_index('row_id').loc[a.row_id].prediction.values; pre = a.row_id.str[0].values
bn = b.copy()
for k in 'MBC':
    m = pre == k; bn[m] = b[m] * a.prediction.values[m].sum() / b[m].sum()
out = a.copy(); out['prediction'] = (a.prediction.values + bn) / 2
assert len(out) == 209063 and np.isfinite(out.prediction).all() and (out.prediction > 0).all()
p = O / 'A1fixF1b3n_mlind50n_2025.csv'; out.to_csv(p, index=False, float_format='%.6f', lineterminator='\n')
info = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'sha256_mlind': hashlib.sha256((R / 'datos/mlind/prediccion_2025_mlind.csv').read_bytes()).hexdigest(),
        'total': round(float(out.prediction.sum()), 2), 'por_ramo': {k: round(float(out.prediction[pre == k].sum()), 2) for k in 'MBC'},
        'cambio_por_fila_frente_designada': {'mediana_abs': round(float(np.median(np.abs(out.prediction / a.prediction - 1))), 4),
                                              'p99_abs': round(float(np.quantile(np.abs(out.prediction / a.prediction - 1), 0.99)), 4)}}
json.dump(info, open(O / 'mezcla_mlind.json', 'w'), indent=1); print(json.dumps(info, indent=1))
