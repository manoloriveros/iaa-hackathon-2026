"""Pasos de enlace para la reproducción histórica; sin búsquedas ni puntuación.

Las fórmulas se transcriben de las recetas originales de Claude. Las dos
restauraciones documentadas (curva global y cruce anterior a ID01) se contrastan
con salidas históricas fuera del proceso de cálculo.
"""
from __future__ import annotations
import json
import os
import shutil
import sys
from pathlib import Path
import numpy as np
import pandas as pd

WORK = Path(os.environ['RETRAIN_WORK'])
N = WORK / 'noche'
M = WORK / 'ml'
F = WORK / 'm017'
LINES = ('motor', 'buildings', 'contents')


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def curve():
    # Conf_insumos original, retirando únicamente la restricción de ocurrencia
    # <=2023 para la curva global descrita en REP-N2 y la bitácora.
    import reporte as RP
    claims = pd.concat([RP.load('s1'), RP.load('s2')], ignore_index=True)
    tmax = int(claims.window.max())
    curves = {}
    for peril, g in claims.groupby('peril'):
        weights = np.minimum(g.net.values, g.net.quantile(.995))
        db = (g.delay.values // RP.B).astype(int)
        wb = (g.window.values // RP.B).astype(int)
        nb = tmax // RP.B + 1
        d = np.bincount(db, weights=weights, minlength=nb)[:nb]
        start = np.bincount(db, weights=weights, minlength=nb + 1)[:nb]
        end = np.bincount(np.minimum(wb, nb - 1) + 1, weights=weights, minlength=nb + 1)[:nb]
        risk = np.cumsum(start) - np.cumsum(end)
        h = np.where(risk > 0, d / np.maximum(risk, 1e-9), 0)
        survival = np.cumprod((1 - h)[::-1])[::-1]
        curves[peril] = np.concatenate([survival[1:], [1.0]]).tolist()
    dump(N / 'salidas/reporte_F.json', {'bucket_days': RP.B, 'F_coste': curves,
         'provenance': 'Restauración Codex de REP-N2 con la expresión de conf_insumos de Claude, sin filtro anual.'})


def ml_c1():
    import receta
    params = receta.parametros('pcv', ['T2b'], 'ramo')
    t, values = receta.aplicar('prod', params)
    sample = pd.read_parquet(M / 'datos/emerging/sample_submission.parquet')
    out = sample[['row_id']].merge(pd.DataFrame({'row_id': t.row_id.values, 'prediction': values}), on='row_id', how='left')
    assert len(out) == 209063 and out.prediction.notna().all() and out.row_id.is_unique
    out.to_csv(M / 'privado/prediccion_2025_mlind.csv', index=False, float_format='%.6f', lineterminator='\n')
    dump(M / 'privado/params_C1.json', params)


def tag(line, seed, history=False):
    if history:
        suffix = '_v2fixf1' if line == 'motor' else '_v2f1'
        return 'dev21222324' + suffix + (f's{seed}' if seed != 11 else '')
    suffix = f'_v2fixs{seed}' if line == 'motor' else ('_m02' if seed == 11 else f'_v2s{seed}')
    return 'dev21222324' + suffix


def a1_post():
    sample = pd.read_parquet(N / 'datos/s2/sample_submission.parquet').row_id
    transfer = N / 'salidas/transfer'
    def lg(line, history=False):
        return pd.concat([pd.read_parquet(transfer / f'lg_{tag(line, seed, history)}_{line}_em.parquet')
                          .set_index('row_id').lg_dev for seed in (11, 12, 13)], axis=1).mean(axis=1)
    def production(history):
        parts = []
        for line in LINES:
            b = pd.read_parquet(N / f'salidas/s2/base_{line}.parquet')
            g = np.exp(b.row_id.map(lg(line, history)).values)
            train = (b.split == 'train').values
            test = (b.split == 'test').values
            level = b.t0.values[train].sum() / (b.eef_coste.values[train] * g[train]).sum()
            parts.append(pd.DataFrame({'row_id': b.row_id.values[test], 'prediction': b.exposure_model.values[test] * g[test] * level}))
        return pd.concat(parts).set_index('row_id').loc[sample].reset_index()
    # El original lee la referencia sin historia ya redondeada a seis decimales.
    baseline = production(False)
    path = N / 'salidas/correccion/A1fixb3_2025.csv'
    baseline.to_csv(path, index=False, float_format='%.6f', lineterminator='\n')
    baseline = pd.read_csv(path, dtype={'row_id': str})
    result = production(True)
    prefix = result.row_id.str[0].values
    for key in 'MBC':
        mask = prefix == key
        result.loc[mask, 'prediction'] = result.prediction.values[mask] * baseline.prediction.values[mask].sum() / result.prediction.values[mask].sum()
    result.to_csv(N / 'salidas/correccion/A1fixF1b3n_2025.csv', index=False, float_format='%.6f', lineterminator='\n')
    # Solo A1 y R0 se consumen en forma_local. No ajustar A2/A3 ajenos a la cadena.
    held = []
    for line in LINES:
        b = pd.read_parquet(N / f'salidas/conf/base_s2_{line}.parquet')
        g = pd.read_parquet(transfer / f'lg_dev212223_v2conf_{line}_em.parquet').set_index('row_id').lg_dev
        risk = np.exp(b.row_id.map(g).values)
        fit = (b.year == 2023).values
        test = (b.year == 2024).values
        level = b.t0.values[fit].sum() / (b.eef_coste.values[fit] * risk[fit]).sum()
        held.append(pd.DataFrame({'row_id': b.row_id.values[test], 'A1': b.eef_coste.values[test] * risk[test] * level,
                     'R0': b.eef_coste.values[test] * b.t0.values[fit].sum() / b.eef_coste.values[fit].sum()}))
    pd.concat(held, ignore_index=True).to_parquet(N / 'salidas/correccion/predicciones_2024.parquet', index=False)


def m017_inputs():
    # Todos los insumos por fila provienen de esta corrida, nunca de las salidas históricas.
    for phase in ('dev', 'hold'):
        for line in LINES:
            target = F / f'oof/pred/{phase}/T2b_{line}.parquet'
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(M / f'trabajo/pred/{phase}/T2b_{line}.parquet', target)
    shutil.copyfile(N / 'salidas/correccion/predicciones_2024.parquet', F / 'in/predicciones_2024.parquet')
    for name in ('customers', 'addresses', 'weather', *(f'policies_{l}' for l in LINES), *(f'test_{l}' for l in LINES)):
        target = F / f'datos/emerging/{name}.parquet'
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(M / f'datos/emerging/{name}.parquet', target)
    columns = ['row_id', 'line', 'conjunto', 'year', 'exposure', 'new_business', 'start_month', 'customer_id', 'y', 'c_fila', 'written_premium']
    labels = pd.concat([pd.read_parquet(M / f'trabajo/base_emerging_{line}.parquet', columns=columns) for line in LINES], ignore_index=True)
    labels.to_parquet(F / 'base_etiquetas.parquet', index=False)
    a = pd.read_csv(N / 'salidas/correccion/A1fixF1b3n_2025.csv', dtype={'row_id': str})
    b = pd.read_csv(M / 'privado/prediccion_2025_mlind.csv', dtype={'row_id': str})
    assert a.row_id.equals(b.row_id)
    blend = a.assign(prediction=.5 * a.prediction.values + .5 * b.prediction.values)
    p = F / 'in/mezcla50.csv'
    blend.to_csv(p, index=False, float_format='%.6f', lineterminator='\n')
    # Constante pública congelada del recibo original; no nueva sonda ni aprendizaje público.
    blend = pd.read_csv(p, dtype={'row_id': str})
    g = json.loads((F / 'in/constantes_publicas.json').read_text(encoding='utf-8'))['factor_global']
    blend['prediction'] = blend.prediction.values * g
    blend.to_csv(F / 'in/final_sonda_global_2025.csv', index=False, float_format='%.6f', lineterminator='\n')


def final_alias():
    shutil.copyfile(F / 'final_creible_2025.csv', F / 'revision/J_final_creible_2025.csv')


if __name__ == '__main__':
    {'curve': curve, 'ml_c1': ml_c1, 'a1_post': a1_post, 'm017_inputs': m017_inputs, 'final_alias': final_alias}[sys.argv[1]]()
