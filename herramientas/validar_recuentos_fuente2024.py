"""Lectura de vuelta, conciliación de siniestros y matemática de la pareja número/coste."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd

SOURCE = R / 'privado/semana2/mision017_fase2/fuente_f2_2024_v2'
P = SOURCE.parent / 'recuentos_fuente2024_v1'; OUT = P / 'validation_v1'
PLAN = R / 'registro/semana2_mision017_recuentos_fuente2024_plan_v1.json'
RAW = ROOT / 'Hackaton/Semana 1/Datos'; VAL = pd.Timestamp('2024-12-31')
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not OUT.exists(); plan = read(PLAN); report = read(P / 'report.json')
    assert read(P / 'registration.json')['plan_sha256'] == sha(PLAN)
    for path, value in plan['sources'].items(): assert sha(ROOT / path) == value, path
    for name, value in report['outputs'].items(): assert sha(P / name) == value, name
    raw = pd.read_parquet(RAW / 'claims.parquet')
    duplicate = raw.duplicated([c for c in raw if c != 'claim_id'], keep=False) & raw.claim_id.str.len().eq(11)
    assert duplicate.sum() == 604; raw = raw.loc[~duplicate].copy()
    raw['loss_date'] = pd.to_datetime(raw.loss_date); raw['report_date'] = pd.to_datetime(raw.report_date)
    raw['net_cents_raw'] = np.rint(raw.incurred_to_date * 100).astype('int64') - np.rint(raw.recoveries * 100).astype('int64')
    assigned = pd.read_parquet(P / 'assigned_claims.parquet'); unassigned = pd.read_parquet(P / 'unassigned_claims.parquet')
    assert assigned.claim_id.is_unique and unassigned.claim_id.is_unique
    assert not set(assigned.claim_id) & set(unassigned.claim_id)
    assert set(assigned.claim_id) | set(unassigned.claim_id) == set(raw.claim_id)
    curves = read(P / 'count_curves.json'); checks = []; tails = []
    for line in ['motor', 'buildings', 'contents']:
        source = pd.read_parquet(SOURCE / f'{line}.parquet', columns=['row_id', 'policy_id', 'year', 'period_start', 'period_end', 'exposure', 'T0_cents'])
        f = pd.read_parquet(P / f'counts_{line}.parquet')
        assert np.array_equal(f.row_id, source.row_id) and np.array_equal(f.T0_cents_total, source.T0_cents)
        assert np.array_equal(f.year, source.year) and np.array_equal(f.exposure, source.exposure)
        witnessed = assigned.loc[assigned.line.eq(line)].merge(source[['row_id', 'policy_id', 'period_start', 'period_end']], on='row_id', validate='many_to_one')
        witnessed = witnessed.merge(raw[['claim_id', 'policy_id', 'status', 'net_cents_raw']], on='claim_id', validate='one_to_one', suffixes=('_assigned', '_raw'))
        assert witnessed.policy_id_assigned.eq(witnessed.policy_id_raw).all() and witnessed.status_assigned.eq(witnessed.status_raw).all()
        assert witnessed.net_cents.eq(witnessed.net_cents_raw).all()
        assert witnessed.loss_date.ge(witnessed.period_start).all() and witnessed.loss_date.le(witnessed.period_end).all()
        accepted = witnessed.loc[witnessed.status_raw.ne('repudiated')]
        positions = pd.Index(f.row_id).get_indexer(accepted.row_id)
        n = np.bincount(positions, minlength=len(f))
        assert np.array_equal(n, f.N_total)
        links = read(SOURCE / f'{line}_link.json')
        start_age = (VAL - pd.to_datetime(f.period_start)).dt.days.to_numpy()
        end_age = (VAL - pd.to_datetime(f.period_end)).dt.days.to_numpy()
        sample = np.unique(np.r_[0, len(f) - 1, np.argsort(start_age - end_age)[:4], np.flatnonzero(end_age == 0)[:4]])
        for peril in sorted(links['mature_cost_CDF']):
            key = line + '|' + peril; curve = curves[key]
            cohort = raw.loc[raw.line.eq(line) & raw.peril.eq(peril) & raw.status.ne('repudiated') & (VAL - raw.loss_date).dt.days.ge(1095)]
            delays = (cohort.report_date - cohort.loss_date).dt.days.to_numpy(); eligible = delays <= 1095
            expected = np.searchsorted(np.sort(delays[eligible]), np.arange(1096), side='right') / eligible.sum()
            assert np.array_equal(expected, curve['count_cdf'])
            old = links['mature_cost_CDF'][peril]; gc = np.asarray(old['cost_cdf']['1.0']); gn = np.asarray(curve['count_cdf'])
            en = f[f'E_count_{peril}'].to_numpy(float); ec = f[f'E_cost_{peril}'].to_numpy(float); ratio = f[f'mark_ratio_{peril}'].to_numpy(float)
            assert (en >= 0).all() and (ec >= 0).all()
            assert np.allclose(en[en > 0] * ratio[en > 0], ec[en > 0], rtol=1e-12, atol=1e-14)
            assert not ((f[f'N_{peril}'] > 0) & (en <= 0)).any()
            assert not ((f[f'T0_cents_{peril}'] > 0) & (ec <= 0)).any()
            errors = []
            for i in sample:
                durations = start_age[i] - end_age[i] + 1
                # Integrate by delay probability masses rather than by the
                # daily-CDF prefix sums used by the production helper.
                covered_fraction = np.maximum(0, start_age[i] - np.maximum(end_age[i], np.arange(1096)) + 1) / durations
                for cdf, actual in [(gn, en[i]), (gc, ec[i])]:
                    q = float(np.dot(np.diff(np.r_[0., cdf]), covered_fraction))
                    error = abs(f.exposure.iloc[i] * q - actual); assert error < 1e-12; errors.append(error)
            if (~eligible).any():
                tail = cohort.loc[~eligible]
                tails.append({'line': line, 'peril': peril, 'observed_mature_claims_beyond1095': len(tail),
                    'observed_net_cents_beyond1095': int(tail.net_cents_raw.sum()),
                    'max_observed_delay': int(delays.max()), 'not_estimate_of_unreported_tail': True})
            checks.append({'line': line, 'peril': peril, 'source_rows': len(f), 'curve_replay_by_sorted_delays': True,
                'source_claim_assignment_and_net_cents_witnessed': True, 'count_mark_product_identity': True,
                'delay_mass_integration_samples': len(sample), 'max_integration_error': max(errors), 'new_fit_calls': 0})
    OUT.mkdir()
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'checks': checks,
        'claim_ID_partition_complete_and_disjoint': True, 'source_counts_cents_and_row_membership_readback_exact': True,
        'zero_net_claims_not_dropped': int(assigned.loc[assigned.status.ne('repudiated')].net_cents.eq(0).sum()),
        'observed_tail': tails, 'conditional1095_count_CDF_not_full_ultimate_tail_identification': True,
        'new_source_curve_fits_in_this_validation': 0, 'new_price_fits': 0, 'new_target_C0_fits': 0,
        'new_scores': 0, 'new_submissions': 0, 'B00_preserved': True, 'goal_achieved': False,
        'code_sha256': sha(Path(__file__)), 'input_report_sha256': sha(P / 'report.json')}
    with (OUT / 'report.json').open('x', encoding='utf8') as f: json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({'checks': len(checks), 'source_rows': report['rows'], 'readback_exact': True,
        'observed_tail': tails, 'zero_net_claims_retained': result['zero_net_claims_not_dropped'], 'new_fits': 0, 'new_scores': 0}))

if __name__ == '__main__':
    main()
