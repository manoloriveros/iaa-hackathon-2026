"""Reutiliza las curvas RKM fuente existentes, con testigo de su cohorte y sin refit."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader')); sys.path.insert(0, str(R / 'src'))
import numpy as np
import pandas as pd
from semana2.variables_ultimo import average_completion

BASE = R / 'privado/semana2/mision017_fase2'
COUNTS = BASE / 'recuentos_fuente2024_v1'; OUT = BASE / 'recuentos_fuente2024_rkm_reuse_v1'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()

def main():
    assert not OUT.exists(); OUT.mkdir(parents=True)
    assert len(read(COUNTS / 'validation_v1/report.json')['checks']) == 15
    assigned = pd.read_parquet(COUNTS / 'assigned_claims.parquet')
    cohort = assigned.loc[assigned.status.ne('repudiated') & assigned.year.isin([2021, 2022, 2023])].copy()
    assert cohort.loss_date.dt.year.isin([2021, 2022, 2023]).all()
    sources = [Path(__file__), COUNTS / 'report.json', COUNTS / 'assigned_claims.parquet', COUNTS / 'validation_v1/report.json',
        R / 'src/semana2/fase2_2024_datos.py', R / 'src/semana2/variables_ultimo.py']
    checks = []; comparisons = []; new_curves = 0; total_violations = 0; count_cost_support_mismatch = 0
    for line in ['motor', 'buildings', 'contents']:
        model_path = BASE / f'entradas_temporales_v1/source_reporting_{line}.json'
        sources += [model_path, COUNTS / f'counts_{line}.parquet']
        old = read(model_path); assert old['years'] == [2021, 2022, 2023]
        perils = sorted(old['models'])
        cols = ['row_id', 'year', 'period_start', 'period_end', 'exposure']
        for p in perils: cols += [f'N_{p}', f'T0_cents_{p}', f'E_cost_{p}', f'E_count_{p}']
        f = pd.read_parquet(COUNTS / f'counts_{line}.parquet', columns=cols); f['is_test'] = False
        out = f[['row_id', 'year']].copy(); out['line'] = line
        for peril in perils:
            model = old['models'][peril]
            g = cohort.loc[cohort.line.eq(line) & cohort.peril.eq(peril)]
            delay = (g.report_date - g.loss_date).dt.days.to_numpy()
            age = (pd.Timestamp('2024-12-31') - g.loss_date).dt.days.to_numpy()
            support, events = np.unique(delay, return_counts=True)
            risk = np.array([np.count_nonzero((delay <= d) & (age >= d)) for d in support])
            assert len(g) == model['n'] and int(delay.max()) == model['max_delay'] and int(age.max()) == model['max_followup']
            assert np.array_equal(support, model['delay_days']) and np.array_equal(events, model['events']) and np.array_equal(risk, model['risk_set'])
            # Replay the frozen reverse product by cumulative products, not by
            # calling fit_reporting or replacing the saved parameter object.
            terms = 1 - events / risk
            expected = np.r_[np.cumprod(terms[:0:-1])[::-1], 1.]
            assert np.allclose(expected, model['count_cdf'], rtol=0, atol=1e-14)
            en = f.exposure.to_numpy(float) * average_completion(f, model)
            ec = f[f'E_cost_{peril}'].to_numpy(float)
            ratio = np.divide(ec, en, out=np.full(len(f), np.nan), where=en > 0)
            violations = int(np.count_nonzero((en <= 0) & (f[f'N_{peril}'].to_numpy() > 0)))
            mismatch = int(np.count_nonzero((en <= 0) & (ec > 0)))
            total_violations += violations; count_cost_support_mismatch += mismatch
            assert np.allclose(en[en > 0] * ratio[en > 0], ec[en > 0], rtol=1e-12, atol=1e-14)
            out[f'E_count_rkm_{peril}'] = en; out[f'mark_ratio_rkm_{peril}'] = ratio
            for year in [2021, 2022, 2023, 2024]:
                sel = f.year.eq(year).to_numpy()
                empirical = f[f'E_count_{peril}'].to_numpy(float)
                comparisons.append({'line': line, 'peril': peril, 'year': year, 'E_count_existing_RKM': float(en[sel].sum()),
                    'E_count_new_mature_empirical1095': float(empirical[sel].sum()), 'E_cost_frozen': float(ec[sel].sum()),
                    'RKM_to_empirical_exposure_ratio': float(en[sel].sum() / empirical[sel].sum())})
            checks.append({'line': line, 'peril': peril, 'historical_source_claims': len(g), 'cohort': [2021, 2022, 2023],
                'existing_valuation': '2024-12-31', 'events_and_risk_sets_match_current_assignment': True,
                'frozen_count_CDF_replayed': True, 'max_delay': model['max_delay'],
                'positive_N_zero_RKM_exposure': violations, 'positive_cost_link_zero_count_link_rows': mismatch,
                'new_reporting_fits': 0, 'old_model_path': rel(model_path), 'old_model_sha256': sha(model_path)})
        out.to_parquet(OUT / f'rkm_links_{line}.parquet', index=False)
    pd.DataFrame(comparisons).to_csv(OUT / 'count_link_comparison.csv', index=False)
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'purpose': 'Reuse existing source count objects for a possible count interpretation without truncating known1361day support',
        'checks': checks, 'positive_count_zero_exposure_violations': total_violations,
        'cost_link_positive_count_link_zero_rows': count_cost_support_mismatch,
        'count_likelihood_input_positivity_pass': total_violations == 0,
        'paired_mark_link_support_pass': count_cost_support_mismatch == 0,
        'all_source_2021_2024_count_records_retained': True, 'new_reporting_fits': new_curves,
        'new_source_cost_CDF_fits': 0, 'new_target_C0_fits': 0, 'new_price_fits': 0, 'new_scores': 0, 'new_submissions': 0,
        'cost_curves_not_switched_to_RKM': True, 'tail_beyond_RKM_max_observed_delay_not_identified': True,
        'sources': {rel(p): sha(p) for p in sources}, 'outputs': {p.name: sha(p) for p in OUT.glob('*.parquet')},
        'empirical1095_count_objects_preserved_as_alternative': True, 'B00_preserved': True, 'goal_achieved': False}
    with (OUT / 'report.json').open('x', encoding='utf8') as f: json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({'existing_RKM_count_objects_replayed': len(checks), 'new_fits': 0,
        'positive_count_zero_exposure': total_violations, 'count_cost_support_mismatches': count_cost_support_mismatch,
        'max_count_support': max(x['max_delay'] for x in checks), 'new_scores': 0, 'new_submissions': 0}))

if __name__ == '__main__':
    main()
