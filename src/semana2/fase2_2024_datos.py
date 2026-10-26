"""Entradas explícitas para desarrollo temporal 2023→2024; no entrena precios."""
from pathlib import Path
from datetime import datetime, timezone
import gc
import hashlib
import json
import sys

ROOT = Path('C:/dev/Hakaton')
REPO = ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from . import variables_ultimo as v
from .preparar_base import reconcile_exposure

BASE = REPO/'privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3'
ULT = REPO/'privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766'
OUT = REPO/'privado/semana2/mision017_fase2/entradas_temporales_v1'
KEY = ['market', 'line', 'row_id']
EXTRA_NUM = ['prior_claims_5y', 'licence_points', 'household_size', 'years_at_address']


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1<<20), b''):
            h.update(block)
    return h.hexdigest()


def dump(path, obj):
    with Path(path).open('x', encoding='utf8') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2, default=str)


def add_profiles(f, raw, customers):
    extra = raw[['row_id', 'written_premium']].merge(
        f[['row_id', 'customer_id']], on='row_id', validate='one_to_one').merge(
        customers[['customer_id', *EXTRA_NUM, 'occupation']], on='customer_id', validate='many_to_one')
    assert len(extra) == len(f) and extra.customer_id.notna().all()
    extra['x_occupation'] = extra.occupation.astype('string').str.lower().str.strip().str.replace(
        'self-employed ', '', regex=False).str.replace(r'\s+', ' ', regex=True).fillna('__MISSING__')
    for c in EXTRA_NUM:
        extra['x_'+c] = pd.to_numeric(extra[c], errors='raise').astype('float32')
    assert extra.written_premium.gt(0).all() and np.isfinite(extra.written_premium).all()
    extra['x_log_incumbent_annual_premium'] = np.log(extra.written_premium)
    keep = ['row_id', 'written_premium', 'x_log_incumbent_annual_premium', 'x_occupation'] + ['x_'+c for c in EXTRA_NUM]
    return f.merge(extra[keep], on='row_id', validate='one_to_one')


def compact(f):
    for c in f:
        if c.startswith('x_'):
            if pd.api.types.is_numeric_dtype(f[c]):
                f[c] = f[c].astype('float32')
            else:
                f[c] = f[c].astype('category')
    return f


def prepare():
    if OUT.exists():
        recovery = json.loads((OUT/'partial_reuse_manifest.json').read_text(encoding='utf8'))
        assert not (OUT/'report.json').exists(), 'Producción ya terminada.'
        for name, expected in recovery['files'].items():
            assert sha(OUT/name) == expected, 'Cambió una salida parcial conciliada.'
    else:
        OUT.mkdir(parents=True)
        recovery = None
    raw_e = ROOT/'Hackaton/Semana 2/Datos/emerging'
    raw_d = ROOT/'Hackaton/Semana 1/Datos'
    sources = [Path(__file__), REPO/'src/semana2/variables_ultimo.py',
               REPO/'src/semana2/preparar_base.py', BASE/'target_T0_and_stresses.parquet', BASE/'partitions.parquet']
    for folder in [raw_e, raw_d]:
        sources += [folder/(x+'.parquet') for x in ['customers', 'addresses', 'claims', 'policies_motor', 'policies_buildings', 'policies_contents']]
    for line in v.LINES:
        sources += [ULT/f'F0_{line}.parquet', BASE/f'periods_policies_{line}.parquet',
                    ULT/f'temporal_2024/observation_link_{line}.parquet', ULT/f'exclude_fold0/observation_link_{line}.parquet']
    sources += [ULT/'temporal_2024/reporting_fit_claims.parquet', ULT/'temporal_2024/summary.json']
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}
    dump(OUT/'sources_before_v2.json', before)
    target = pd.read_parquet(BASE/'target_T0_and_stresses.parquet', filters=[('is_test', '=', False)])
    parts = pd.read_parquet(BASE/'partitions.parquet', filters=[('is_test', '=', False)])
    fit_claims = pd.read_parquet(ULT/'temporal_2024/reporting_fit_claims.parquet')
    assert fit_claims.year.eq(2023).all() and fit_claims.market.eq('emerging').all()
    customers_e = pd.read_parquet(raw_e/'customers.parquet')
    receipts = []
    for line in v.LINES:
        cached = OUT/f'emerging_{line}.parquet'
        if recovery and cached.name in recovery['files']:
            f = pd.read_parquet(cached)
            reference = target.loc[target.line.eq(line)].set_index('row_id').T0_cents
            assert np.array_equal(f.T0_cents.to_numpy(), reference.reindex(f.row_id).to_numpy())
            assert f.year.isin([2023,2024]).all() and f.market.eq('emerging').all()
            receipts.append({'market':'emerging','line':line,'rows':len(f),'groups':int(f.group_id.nunique()),
                             'reused_frozen_partial':True,'sha256':sha(cached)})
            del f
            continue
        raw = pd.read_parquet(BASE/f'periods_policies_{line}.parquet')
        f = pd.read_parquet(ULT/f'F0_{line}.parquet', filters=[('is_test', '=', False)])
        assert f.year.isin([2023, 2024]).all() and f.row_id.is_unique
        f = add_profiles(f, raw, customers_e)
        f = f.merge(target[KEY+['T0', 'T0_cents', 'reserve', 'T1_reserve075', 'T1_reserve125']], on=KEY, validate='one_to_one')
        f = f.merge(parts[KEY+['fold', 'group_id', 'customer_seen_prior_year_any_line']], on=KEY, validate='one_to_one')
        for scope, name in [('temporal_2024', 'e_cost'), ('exclude_fold0', 'e_inner0')]:
            obs = pd.read_parquet(ULT/f'{scope}/observation_link_{line}.parquet', columns=KEY+['e_cost_mix_1.0'])
            f = f.merge(obs.rename(columns={'e_cost_mix_1.0': name}), on=KEY, validate='one_to_one')
        stress = pd.read_parquet(ULT/f'temporal_2024/observation_link_{line}.parquet', columns=KEY+[
            'e_cost_mix_0.75','e_cost_mix_1.25','e_cost_mix_tail0.05','e_cost_mix_tail0.1'])
        f = f.merge(stress, on=KEY, validate='one_to_one')
        assert f[['e_cost', 'e_inner0', 'exposure']].gt(0).all().all()
        assert f.T0_cents.sum() == target.loc[target.line.eq(line), 'T0_cents'].sum()
        compact(f).to_parquet(OUT/f'emerging_{line}.parquet', index=False)
        stats = f.groupby(['year', 'x_new_business'], observed=True).agg(n=('row_id', 'size'),
            positive=('T0', lambda x: int(x.gt(0).sum())), cost=('T0', 'sum'), exposure=('exposure', 'sum'))
        receipts.append({'market': 'emerging', 'line': line, 'rows': len(f), 'groups': f.group_id.nunique(),
                         'cohorts': stats.reset_index().to_dict('records')})
        del f, raw
        gc.collect()
    del customers_e, target, parts
    gc.collect()

    # Source claims are selected by occurrence year BEFORE fitting any curve or mark.
    claims = pd.read_parquet(raw_d/'claims.parquet')
    duplicate = claims.duplicated([c for c in claims if c != 'claim_id'], keep=False) & claims.claim_id.str.len().eq(11)
    removed = int(duplicate.sum())
    claims = claims.loc[~duplicate].copy()
    claims['loss_date'] = pd.to_datetime(claims.loss_date)
    claims['report_date'] = pd.to_datetime(claims.report_date)
    claims = claims.loc[claims.loss_date.dt.year.isin([2021, 2022, 2023])].copy()
    assert claims.report_date.ge(claims.loss_date).all() and claims.report_date.le('2024-12-31').all()
    claims['T0_cents'] = np.rint(claims.incurred_to_date*100).astype('int64') - np.rint(claims.recoveries*100).astype('int64')
    claims['reserve'] = claims.incurred_to_date-claims.paid_to_date
    assert claims.T0_cents.ge(0).all()
    cu = pd.read_parquet(raw_d/'customers.parquet')
    ad = pd.read_parquet(raw_d/'addresses.parquet')
    for line in v.LINES:
        cached = OUT/f'developed_{line}.parquet'
        if recovery and cached.name in recovery['files']:
            f = pd.read_parquet(cached)
            assert f.year.isin([2021,2022,2023]).all() and f.market.eq('developed').all()
            models = json.loads((OUT/f'source_reporting_{line}.json').read_text(encoding='utf8'))['models']
            receipts.append({'market':'developed','line':line,'rows':len(f),'cost_cents':int(f.T0_cents.sum()),
                             'source_C0_curves':len(models),'reused_frozen_partial':True,'sha256':sha(cached)})
            del f
            continue
        raw = pd.read_parquet(raw_d/f'policies_{line}.parquet', filters=[
            ('period_start', '>=', datetime(2021,1,1)), ('period_start', '<', datetime(2024,1,1))])
        raw = reconcile_exposure(raw)
        if line == 'motor':
            raw['customer_id'] = raw.customer_id.str.zfill(8)
        raw['market'] = 'developed'; raw['line'] = line
        raw['year'] = raw.period_start.dt.year; raw['is_test'] = False
        assert raw.year.isin([2021,2022,2023]).all() and raw.period_end.dt.year.eq(raw.year).all()
        age = raw['driver_age' if line == 'motor' else 'policyholder_age']
        raw['driver_age_band' if line == 'motor' else 'policyholder_age_band'] = pd.cut(
            age, [16,24,34,49,64,np.inf], labels=['17-24','25-34','35-49','50-64','65+']).astype(str)
        if line == 'buildings':
            raw['construction_type'] = raw.construction_type.str.lower().str.strip().replace(
                {'brick':'BRK','stone':'STN','timber':'WOD','w':'WOD','t':'WOD','non_standard':'MIX'})
            assert raw.construction_type.isin(['BRK','STN','WOD','MIX']).all()
        f, feature_contract, audit = v.make_features(raw, cu, ad, line)
        f = add_profiles(f, raw, cu)
        c = claims.loc[claims.line.eq(line)].copy()
        joined = c.merge(raw[['row_id','policy_id','period_start','period_end']], on='policy_id', how='left')
        matched = joined.loc[joined.loss_date.ge(joined.period_start) & joined.loss_date.le(joined.period_end)].copy()
        assert not matched.claim_id.duplicated().any(), 'Asignación ambigua en fuente.'
        missing = c.loc[~c.claim_id.isin(matched.claim_id)]
        missing.to_parquet(OUT/f'precoverage_source_{line}.parquet', index=False)
        good = matched.loc[matched.status.ne('repudiated')].copy()
        good['year'] = good.loss_date.dt.year
        assert good.year.isin([2021,2022,2023]).all()
        cost = good.groupby('row_id').T0_cents.sum()
        f['T0_cents'] = f.row_id.map(cost).fillna(0).astype('int64'); f['T0'] = f.T0_cents/100
        assert f.T0_cents.sum() == good.T0_cents.sum()
        # Fifteen ordinary reporting fits in total; same verified estimator as historical C0.
        obs = np.zeros(len(f)); rates = {}; models = {}; perils = {}
        for peril, g in good.groupby('peril'):
            model, _ = v.fit_reporting((g.report_date-g.loss_date).dt.days,
                (pd.Timestamp('2024-12-31')-g.loss_date).dt.days, g.T0_cents/100, g.reserve)
            qn = v.average_completion(f, model)
            qc = v.average_completion(f, model, 'cost', 1.)
            rate = len(g)/np.sum(f.exposure.to_numpy()*qn)*model['mean_net_mark']['1.0']
            models[peril] = model; rates[peril] = float(rate); perils[peril] = qc
        for peril in models:
            obs += rates[peril]/sum(rates.values())*perils[peril]
        f['e_cost'] = f.exposure*obs
        assert f.e_cost.gt(0).all() and f.e_cost.le(f.exposure*(1+1e-10)).all()
        compact(f).to_parquet(OUT/f'developed_{line}.parquet', index=False)
        dump(OUT/f'source_reporting_{line}.json', {'years':[2021,2022,2023], 'models':models,
              'cost_mixture':{p:r/sum(rates.values()) for p,r in rates.items()}})
        receipts.append({'market':'developed','line':line,'rows':len(f),'cost_cents':int(f.T0_cents.sum()),
            'source_C0_curves':len(models),'unassigned_claims_preserved':len(missing), 'features':feature_contract, 'audit':audit})
        del f, raw, joined, matched, good, perils
        gc.collect()
    assert before == {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}, 'Cambió una fuente durante la producción.'
    report = {'author':'Codex','utc':datetime.now(timezone.utc).isoformat(), 'sources':before, 'rows':receipts,
        'duplicate_clones_rule_unchanged':removed, 'source_pricing_years':[2021,2022,2023],
        'emerging_fit_years':[2023], 'emerging_evaluation_years':[2024], 'new_price_fits':0,
        'new_source_reporting_curves':sum(x.get('source_C0_curves',0) for x in receipts),
        'target_C0_reestimated':False, 'weather_loaded':False, 'B00_preserved':True,
        'availability_limits':['One shared 2024-12-31 claim valuation; not a true as-of-inception backtest.',
            'Undated customer/address masters assumed stable; no historical master snapshots.',
            'Current incumbent premium is a conditional competition input, not a price generated by this model.',
            'C0 tail beyond observed support and case-reserve adequacy remain unidentified.'],
        'outputs':{p.name:sha(p) for p in sorted(OUT.glob('*.parquet'))}}
    dump(OUT/'report.json', report)
    return report
