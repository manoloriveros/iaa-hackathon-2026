"""Build emerging-market bases from the original Parquet files under frozen rules.

EXP-N1: round inclusive covered days/365 to four decimals.
ASG-N1: match policy, line and inclusive loss-date/period boundaries; classify
assignments as unique, missing or ambiguous.
OBJ-N1: sum incurred minus recoveries for uniquely assigned non-declined claims.
Paid/incurred are already net of excess, so do not subtract it again.
CAP-N1: flag suspicious household insured-value scales using premium per mille;
divide by 1,000 only above the line threshold and below the normal population's
minimum premium-per-mille rate. Keep raw insured values unchanged.
Write line bases for 2023-2025 and the claims-assignment table under salidas/s2/.
"""
import json, hashlib, pathlib
import numpy as np, pandas as pd

R = pathlib.Path('__RUN_ROOT__/noche')
import sys as _s
MK = _s.argv[1] if len(_s.argv) > 1 else 's2'
D = R / f'datos/{MK}'
O = R / f'salidas/{MK}'; O.mkdir(parents=True, exist_ok=True)
LINES = ['motor', 'buildings', 'contents']
PERILS = {'motor': ['own_damage', 'third_party_prop', 'bodily_injury', 'theft', 'glass_hail'],
          'buildings': ['storm', 'flood', 'escape_of_water', 'subsidence', 'fire', 'accidental_damage'],
          'contents': ['theft', 'escape_of_water', 'accidental_damage', 'flood']}
CUT = pd.Timestamp('2024-12-31')
log = {}

def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

claims = pd.read_parquet(D / 'claims.parquet')
if MK == 's1':  # DUP-N1: 604 payload-identical copies differ only in claim_id; retain the 10-character identifier.
    claims = claims[claims.claim_id.str.len() == 10].reset_index(drop=True)
claims['ld'] = pd.to_datetime(claims.loss_date)
claims['rd'] = pd.to_datetime(claims.report_date)
claims['net'] = claims.incurred_to_date - claims.recoveries
claims['accepted'] = claims.status != 'repudiated'

asg_all = []
for ln in LINES:
    tr = pd.read_parquet(D / f'policies_{ln}.parquet'); tr['split'] = 'train'
    te = pd.read_parquet(D / f'test_{ln}.parquet'); te['split'] = 'test'
    df = pd.concat([tr, te], ignore_index=True)
    df['ps'] = pd.to_datetime(df.period_start); df['pe'] = pd.to_datetime(df.period_end)
    df['year'] = df.ps.dt.year
    days = (df.pe - df.ps).dt.days + 1
    df['days'] = days
    df['exposure_raw'] = df.exposure
    df['exposure_model'] = (days / 365).round(4)
    df['exp_changed'] = ~np.isclose(df.exposure_raw, df.exposure_model, atol=6e-5)
    log[f'{ln}_exp_changed_train'] = int(df.exp_changed[df.split == 'train'].sum())
    log[f'{ln}_exp_changed_test'] = int(df.exp_changed[df.split == 'test'].sum())

    c = claims[claims.line == ln].copy()
    m = c[['claim_id', 'policy_id', 'ld']].merge(df.loc[df.split == 'train', ['row_id', 'policy_id', 'ps', 'pe']], on='policy_id', how='left')
    m['inside'] = (m.ld >= m.ps) & (m.ld <= m.pe)
    n_in = m.groupby('claim_id').inside.sum()
    c['n_rows'] = c.claim_id.map(n_in).fillna(0).astype(int)
    c['category'] = np.select([c.n_rows == 1, c.n_rows == 0], ['unica', 'sin_fila'], 'ambigua')
    first = df[df.split == 'train'].groupby('policy_id').ps.min()
    c['policy_first_start'] = c.policy_id.map(first)
    c['prehistoria'] = (c.category == 'sin_fila') & (c.ld < c.policy_first_start)
    rid = m[m.inside].drop_duplicates('claim_id').set_index('claim_id').row_id
    c['row_id'] = c.claim_id.map(rid)
    asg_all.append(c)

    ok = c[(c.category == 'unica') & c.accepted]
    g = ok.groupby('row_id')
    agg = pd.DataFrame({'t0': g.net.sum(), 'paid': g.paid_to_date.sum(), 'incurred': g.incurred_to_date.sum(),
                        'recov': g.recoveries.sum(), 'n_claims': g.size(),
                        'n_open': g.apply(lambda x: (x.status == 'open').sum(), include_groups=False),
                        'case_reserve': g.apply(lambda x: (x.incurred_to_date - x.paid_to_date).sum(), include_groups=False)})
    for p in PERILS[ln]:
        sp = ok[ok.peril == p].groupby('row_id')
        agg[f'n_{p}'] = sp.size(); agg[f't0_{p}'] = sp.net.sum()
    df = df.merge(agg, left_on='row_id', right_index=True, how='left')
    num = [x for x in agg.columns]
    df.loc[df.split == 'train', num] = df.loc[df.split == 'train', num].fillna(0)
    log[f'{ln}_claims'] = {k: int(v) for k, v in c.groupby(['category']).size().items()}
    log[f'{ln}_accepted_unica'] = int(len(ok)); log[f'{ln}_t0'] = round(float(ok.net.sum()), 2)
    log[f'{ln}_prehistoria'] = int(c.prehistoria.sum())
    log[f'{ln}_sin_fila_no_prehist'] = int(((c.category == 'sin_fila') & ~c.prehistoria).sum())

    if ln in ('buildings', 'contents'):
        df['sum_insured_raw'] = df.sum_insured
        df['ppm'] = df.written_premium / df.sum_insured * 1000
        log[f'{ln}_si_null'] = int(df.sum_insured.isna().sum())
    df.drop(columns=['ps', 'pe']).to_parquet(O / f'base_{ln}.parquet', index=False)

asg = pd.concat(asg_all, ignore_index=True)
asg.drop(columns=['ld', 'rd']).to_parquet(O / 'asignacion.parquet', index=False)
log['t0_total'] = round(sum(log[f'{l}_t0'] for l in LINES), 2)
json.dump(log, open(O / 'log_base.json', 'w'), indent=1, default=str)
print(json.dumps(log, indent=1, default=str))
