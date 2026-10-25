"""Conciliación final con el catálogo de Codex en desarrollo 2023 (se hace al final, como se acordó).

Lee las OOF de Codex de la corrida dev7 (W2-B00 a W2-B18, copiadas de Repositorio_IAA2026/privado/semana2/desarrollo2023/
dev7_20261023T235935Z_55507793/oof_2023.parquet, SHA en la salida) y mis OOF (salidas/s2/oof). Comprueba que filas, objetivo
y nula coinciden, compara el vínculo de observación (e_cost_mix_1.0 de Codex frente a mi e_ef_coste) y mide pares con mi
bootstrap de componentes cliente-dirección (Poisson, 4.000 réplicas), en el completo y sin el 0,1 % superior de filas.
Los folds son distintos (cada OOF con los suyos). Escribe salidas/conciliacion_codex.json.
"""
import hashlib, json, pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M

R = pathlib.Path('/home/claude/noche'); F = R / 'datos/codex/dev7_oof_2023.parquet'
cx = pd.read_parquet(F)
wide = cx.pivot(index='row_id', columns='model_id', values='prediction')
base = cx[cx.model_id == 'W2-B00'].set_index('row_id')
mine = {n: pd.read_parquet(R / f'salidas/s2/oof/{n}.parquet').set_index('row_id') for n in
        ['L0_tasa', 'L1_glm_a10', 'L3_gbm', 'T1v2_nivel', 'A1fix_nivel', 'A1fixb3_nivel', 'A1fixF1_nivel']}
o = mine['T1v2_nivel']
idx = o.index
assert set(idx) == set(wide.index) and len(idx) == 50094
y = o.y.values
out = {'codex_oof_sha256': hashlib.sha256(F.read_bytes()).hexdigest(), 'filas': int(len(idx))}
out['objetivo_igual'] = bool(np.allclose(base.loc[idx, 'T0'].astype(float).values, y, atol=1e-6))
out['nula_mia'] = float(M.dev(y, np.full_like(y, y.mean())).sum())
eo = base.loc[idx, 'e_cost_mix_1.0'].values; em = o.eef.values
r = eo / em
out['vinculo_observacion'] = {'suma_codex': round(float(eo.sum()), 2), 'suma_mia': round(float(em.sum()), 2),
                              'cociente_p1_p50_p99': [round(float(q), 4) for q in np.percentile(r, [1, 50, 99])],
                              'exposicion_nominal_igual': bool(np.allclose(base.loc[idx, 'exposure'].values, o.exposure.values, atol=1e-4))}
P = {f'codex_{c}': wide.loc[idx, c].values for c in wide.columns}
P.update({f'mio_{k}': v.loc[idx, 'mu'].values for k, v in mine.items()})
d2 = {k: round(float(M.d2(y, v)), 5) for k, v in P.items()}
out['D2'] = dict(sorted(d2.items(), key=lambda kv: -kv[1]))
out['D2_codex_reproduce_informe'] = {'W2-B00': d2['codex_W2-B00'], 'W2-B10': d2['codex_W2-B10'], 'W2-B14': d2['codex_W2-B14']}
lines = o.line.values; nb = o.new_business.values.astype(bool)
seg = {}
for k in ['codex_W2-B00', 'codex_W2-B10', 'codex_W2-B14', 'mio_L0_tasa', 'mio_T1v2_nivel', 'mio_A1fixb3_nivel', 'mio_A1fixF1_nivel']:
    seg[k] = {l: round(float(M.d2(y[lines == l], P[k][lines == l])), 4) for l in ['motor', 'buildings', 'contents']}
    seg[k].update({'nuevo_negocio': round(float(M.d2(y[nb], P[k][nb])), 4), 'renovacion': round(float(M.d2(y[~nb], P[k][~nb])), 4),
                   'AE': round(float(y.sum() / P[k].sum()), 4)})
out['segmentos'] = seg
comp = M.components(o.customer_id.values, o.address_id.values)
names = ['codex_W2-B00', 'codex_W2-B08', 'codex_W2-B10', 'codex_W2-B14', 'mio_T1v2_nivel', 'mio_A1fixb3_nivel', 'mio_A1fixF1_nivel', 'mio_L3_gbm']
pares = [('mio_T1v2_nivel', 'codex_W2-B10'), ('mio_T1v2_nivel', 'codex_W2-B14'), ('mio_T1v2_nivel', 'codex_W2-B00'),
         ('mio_A1fixb3_nivel', 'codex_W2-B10'), ('mio_A1fixF1_nivel', 'codex_W2-B10'), ('codex_W2-B10', 'mio_L3_gbm'), ('codex_W2-B00', 'mio_L0_tasa')]
names = sorted(set(names) | {a for a, _ in pares} | {b for _, b in pares})
res = {}
for tag, keep in (('completo', np.ones(len(y), bool)), ('cuerpo', y < np.quantile(y, 0.999))):
    B = M.boot_d2_diff(y[keep], {n: P[n][keep] for n in names}, comp[keep], n=4000)
    res[tag] = {f'{a} − {b}': {'diff': round(float(M.d2(y[keep], P[a][keep]) - M.d2(y[keep], P[b][keep])), 7),
                               'IC90': [round(float(np.quantile(B[a] - B[b], q)), 7) for q in (0.05, 0.95)]} for a, b in pares}
out['pares'] = res
json.dump(out, open(R / 'salidas/conciliacion_codex.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
