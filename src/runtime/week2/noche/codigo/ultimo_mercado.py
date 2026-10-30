"""Estimate emerging ultimate costs, effective exposure and recovery sensitivity.
REP-N2 uses peril net-cost weights capped at p99.5 for reporting completeness.
Estimate emerging 2023-2024 peril ultimate cost as T0_p*e/e_ef_p for cost shares.
REC-N1 only diagnoses possible open-claim recoveries using closed-claim peril
patterns; it does not apply that adjustment to model predictions.
"""
import json, pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from exposicion_efectiva import add_effective, PERILS

R = pathlib.Path('__RUN_ROOT__/noche')
import sys as _s
MK = _s.argv[1] if len(_s.argv) > 1 else 's2'
O = R / f'salidas/{MK}'
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
    for y in sorted(b.loc[tr,'year'].unique()):
        s = b[tr & (b.year == y)]
        r[str(y)] = {'exposure': round(s.exposure_model.sum(), 2), 'eef_coste': round(s.eef_coste.sum(), 2),
                     'comp': round(s.eef_coste.sum() / s.exposure_model.sum(), 4), 't0': round(s.t0.sum(), 2),
                     'rate_t0': round(s.t0.sum() / s.exposure_model.sum(), 2),
                     'rate_ult': round(s.t0.sum() / s.eef_coste.sum(), 2),
                     'freq_obs': round(s.n_claims.sum() / s.exposure_model.sum(), 4)}
    res[ln] = r
# Pending-recovery diagnostic.
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
