"""Exposición efectiva, último estimado y recuperaciones pendientes del emergente.

REP-N2: para el coste se usa la F ponderada por coste (neto recortado al p99,5 del peligro).
Participaciones s_p del peligro en el coste último del ramo: emergente 2023-2024, último_p = T0_p * e / e_ef_p.
REC-N1 (diagnóstico, no se aplica): ningún abierto tiene recuperaciones; se mide cuánto bajaría el neto si los abiertos
recuperaran como los cerrados del mismo peligro.
"""
import json, pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from exposicion_efectiva import add_effective, PERILS

R = pathlib.Path('/home/claude/noche')
O = R / 'salidas/s2'
rep = json.load(open(R / 'salidas/reporte_F.json'))
F = rep['F_coste']; B = rep['bucket_days']
res = {}
for ln in PERILS:
    b = pd.read_parquet(O / f'base_{ln}.parquet')
    tr = b.split == 'train'
    tmp = add_effective(b.copy(), ln, F, B, {p: 1.0 for p in PERILS[ln]})
    ult = {}
    for p in PERILS[ln]:
        ult[p] = float(b.loc[tr, f't0_{p}'].sum() * tmp.loc[tr, 'exposure_model'].sum() / tmp.loc[tr, f'eef_{p}'].sum())
    tot = sum(ult.values()); shares = {p: ult[p] / tot for p in ult}
    b = add_effective(b, ln, F, B, shares)
    b.to_parquet(O / f'base_{ln}.parquet', index=False)
    r = {'shares': {p: round(v, 4) for p, v in shares.items()}}
    for y in (2023, 2024):
        s = b[tr & (b.year == y)]
        r[str(y)] = {'exposure': round(s.exposure_model.sum(), 2), 'eef_coste': round(s.eef_coste.sum(), 2),
                     'comp': round(s.eef_coste.sum() / s.exposure_model.sum(), 4), 't0': round(s.t0.sum(), 2),
                     'rate_t0': round(s.t0.sum() / s.exposure_model.sum(), 2),
                     'rate_ult': round(s.t0.sum() / s.eef_coste.sum(), 2),
                     'freq_obs': round(s.n_claims.sum() / s.exposure_model.sum(), 4)}
    res[ln] = r
# recuperaciones pendientes
a = pd.read_parquet(O / 'asignacion.parquet')
a = a[(a.category == 'unica') & a.accepted]
rec = {}
for (ln, p), g in a.groupby(['line', 'peril']):
    cl = g[g.status == 'closed']; op = g[g.status == 'open']
    rate = cl.recoveries.sum() / cl.incurred_to_date.sum() if cl.incurred_to_date.sum() > 0 else 0
    if rate > 0:
        rec[f'{ln}/{p}'] = {'rate_closed': round(rate, 4), 'open_incurred': round(op.incurred_to_date.sum(), 2),
                            'implied_recov': round(rate * op.incurred_to_date.sum(), 2), 'n_open': int(len(op))}
for ln in PERILS:
    t0 = a[a.line == ln].net.sum()
    imp = sum(v['implied_recov'] for k, v in rec.items() if k.startswith(ln + '/'))
    res[ln]['recov_open_implied_share_t0'] = round(imp / t0, 4)
res['recoveries'] = rec
json.dump(res, open(O / 'ultimo_resumen.json', 'w'), indent=1)
print(json.dumps(res, indent=1))
