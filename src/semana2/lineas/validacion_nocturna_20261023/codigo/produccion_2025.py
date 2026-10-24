"""Producción 2025 según las recetas preinscritas (preinscripcion_puerta_2024.json, clave 'produccion').

R0: tasa por ramo 2023-2024 (Σ T0 / Σ e_ef_coste) × exposición 2025.
A1: relatividades del GBM desarrollado 2021-2024 (lg_v2: motor sin make_model; todos con mes de inicio; lr 0,02)
    × nivel por ramo 2023-2024 por balance (Σ T0 / Σ e_ef_coste·g) × exposición 2025.
Valida: 209.063 filas, mismos row_id y orden que sample_submission, predicciones finitas y > 0, totales por ramo.
Salidas: salidas/produccion/{R0,A1}_2025.csv y produccion_info.json.
"""
import hashlib, json, pathlib
import numpy as np, pandas as pd

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/produccion'; O.mkdir(parents=True, exist_ok=True)
ss = pd.read_parquet(R / 'datos/s2/sample_submission.parquet')
info = {}; preds = {'R0': [], 'A1': []}
for line in ['motor', 'buildings', 'contents']:
    b = pd.read_parquet(R / f'salidas/s2/base_{line}.parquet')
    g = pd.read_parquet(R / f'salidas/transfer/lg_v2_{line}_em.parquet').set_index('row_id').lg_dev
    b['g'] = np.exp(b.row_id.map(g).values); assert b.g.notna().all()
    tr = b[b.split == 'train']; te = b[b.split == 'test']
    L0 = tr.t0.sum() / tr.eef_coste.sum(); L1 = tr.t0.sum() / (tr.eef_coste * tr.g).sum()
    r0 = te.exposure_model.values * L0
    a1 = te.exposure_model.values * te.g.values * L1
    preds['R0'].append(pd.DataFrame({'row_id': te.row_id.values, 'prediction': r0}))
    preds['A1'].append(pd.DataFrame({'row_id': te.row_id.values, 'prediction': a1}))
    nb = te.new_business.values
    info[line] = {'L_R0': round(L0, 4), 'L_A1': round(L1, 4), 'filas': int(len(te)), 'exposicion': round(te.exposure_model.sum(), 2),
                  'total_R0': round(r0.sum(), 2), 'total_A1': round(a1.sum(), 2),
                  'tasa_A1': round(a1.sum() / te.exposure_model.sum(), 2), 'tasa_A1_nb': round(a1[nb].sum() / te.exposure_model.values[nb].sum(), 2),
                  'tasa_A1_ren': round(a1[~nb].sum() / te.exposure_model.values[~nb].sum(), 2),
                  'g_p01_p50_p99': np.round(np.quantile(te.g, [0.01, 0.5, 0.99]), 3).tolist()}
for k, v in preds.items():
    df = pd.concat(v, ignore_index=True).set_index('row_id').loc[ss.row_id].reset_index()
    assert len(df) == 209063 and df.row_id.is_unique and (df.row_id.values == ss.row_id.values).all()
    assert np.isfinite(df.prediction).all() and (df.prediction > 0).all()
    p = O / f'{k}_2025.csv'
    df.to_csv(p, index=False, float_format='%.6f', lineterminator='\n')
    chk = pd.read_csv(p, dtype={'row_id': str})
    assert (chk.row_id.values == ss.row_id.values).all() and np.allclose(chk.prediction.values, df.prediction.values, rtol=0, atol=5.1e-7)
    info[f'{k}_sha256'] = hashlib.sha256(p.read_bytes()).hexdigest(); info[f'{k}_total'] = round(df.prediction.sum(), 2)
json.dump(info, open(O / 'produccion_info.json', 'w'), indent=1)
print(json.dumps(info, indent=1))
