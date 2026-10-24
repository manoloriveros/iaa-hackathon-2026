"""Comprobación separada: replay manual, orden estadístico, bisect y fsum."""
from pathlib import Path
from datetime import datetime, timezone
import bisect
import importlib.util
import json
import math
import re
import sys

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from threadpoolctl import threadpool_limits

spec = importlib.util.spec_from_file_location('band_manual_predictor_oracle', REPO/'herramientas/verificar_glm_ridge_coberturas2023.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: __import__('hashlib').sha256(p.read_bytes()).hexdigest()
KEY = ['market', 'line', 'row_id']


def main():
    run = Path(sys.argv[1]).resolve()
    run.relative_to(REPO/'privado/semana2/desarrollo2023')
    output = run/'verification.json'
    assert not output.exists(), 'Verificación existente: no repetir sin cambios'
    p, r = read(run/'plan_snapshot.json'), read(run/'report.json')
    checks = []
    def check(name, value):
        checks.append({'name': name, 'pass': bool(value)})
    close = lambda a, b: np.allclose(a, b, rtol=3e-10, atol=1e-8, equal_nan=True)
    for cls in [prior.c.TweedieRegressor, prior.c.SimpleImputer, prior.c.StandardScaler, prior.c.OneHotEncoder, prior.c.ColumnTransformer, prior.c.Pipeline]:
        cls.fit = prior.c.forbid_fit
        if hasattr(cls, 'fit_transform'):
            cls.fit_transform = prior.c.forbid_fit
    for item in p['frozen_sources']:
        check('Source '+item['path'], sha(ROOT/item['path']) == item['sha256'])
    for item in read(run/'manifest.json')['files']:
        check('Artifact '+item['path'], sha(run/item['path']) == item['sha256'])
    check('Planandcodesnapshot', sha(run/'plan_snapshot.json') == r['plan_sha256'] and sha(run/'code_snapshot.py') == p['producer_sha256'])
    match = re.search(r'^## Codex \| '+re.escape(p['forum_prior'])+r' \| ([^|]+) \|', (run/'forum_before_analysis.md').read_text(encoding='utf-8'), re.M)
    check('Registrationprecedesbands', match is not None and datetime.fromisoformat(match[1].strip()) < datetime.fromisoformat(r['started_utc']))
    fit = pq.read_table(run/'training_rate_replays_2023.parquet').to_pandas()
    held = pq.read_table(run/'heldout_bands_2023.parquet').to_pandas()
    cells = pq.read_table(run/'calibration_cells_2023.parquet').to_pandas()
    cuts = read(run/'band_cuts.json')
    old = pq.read_table(ROOT/p['ridge_run']/'oof_2023.parquet', filters=[('model_id', 'in', ['W2-B20', 'W2-B19'])]).to_pandas()
    a = old[old.model_id.eq('W2-B20')].sort_values(KEY).reset_index(drop=True)
    b = old[old.model_id.eq('W2-B19')].sort_values(KEY).reset_index(drop=True)
    check('2023cohortsandroles', len(fit) == 200376 and len(held) == 50094 and fit.year.eq(2023).all() and held.year.eq(2023).all() and not held.duplicated(KEY).any() and not fit.duplicated(['model_fold', *KEY]).any())
    check('ExactOOFkeys', held[KEY].equals(a[KEY]) and a[KEY].equals(b[KEY]))
    for field in ['T0', 'fold', 'group_id', 'exposure', 'e_cost_mix_1.0']:
        check('OriginalOOF '+field, held[field].equals(a[field]) and a[field].equals(b[field]))
    check('Bothsamepopulationprices', np.array_equal(held.mu20, a.prediction) and np.array_equal(held.mu19, b.prediction) and np.array_equal(held.annual_rate, a.annual_rate))
    recipe = read(ROOT/p['ridge_run']/'plan_snapshot.json')['recipe']
    for line in ['motor', 'buildings', 'contents']:
        for fold in range(5):
            label = line+str(fold)
            raw = pq.read_table(ROOT/p['frame_source']/f'inputs_2023/{line}_fold{fold}.parquet').to_pandas()
            train = raw[raw.fold.ne(fold)].sort_values(KEY).reset_index(drop=True)
            valid = raw[raw.fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
            fr = fit[fit.line.eq(line) & fit.model_fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
            hr = held[held.line.eq(line) & held.fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
            entry = next(x for x in cuts if x['line'] == line and x['fold'] == fold)
            check('Exacttrainingrows '+label, fr[KEY].equals(train[KEY]) and len(fr) == entry['fit_rows'] and len(hr) == entry['heldout_rows'])
            for field in ['T0', 'group_id', 'customer_id', 'address_id', 'exposure', 'fold', 'e_cost_mix_1.0']:
                check('Trainingfield '+label+field, fr[field].equals(train[field]))
            check('Groupdisjoint '+label, all(set(train[k]).isdisjoint(valid[k]) for k in ['group_id', 'customer_id', 'address_id']))
            bundle = joblib.load(ROOT/p['ridge_run']/'models'/f'{line}_fold{fold}'/'bundle.joblib')
            with threadpool_limits(limits=2):
                X = prior.manual_matrix(train, recipe['features_by_line'][line], bundle['transformer'])
                rates = np.exp(X@bundle['estimator'].coef_+bundle['estimator'].intercept_)
            check('Independenttraininginference '+label, np.allclose(fr.annual_rate, rates, rtol=2e-12, atol=1e-8))
            check('TrainingC0once '+label, np.array_equal(fr.mu20, fr.annual_rate*fr['e_cost_mix_1.0']))
            ordered = sorted(float(x) for x in fr.annual_rate)
            order_indices = [(len(ordered)*k-1)//5 for k in range(1, 5)]
            expected_edges = [ordered[j] for j in order_indices]
            check('Independentorderstatcuts '+label, expected_edges == entry['edges'] and order_indices == entry['edge_indices0'])
            check('Fitonlyedgeaccounting '+label, not entry['labels_used_for_edges'] and entry['training_rate_min'] == ordered[0] and entry['training_rate_max'] == ordered[-1])
            check('Trainingbisectbands '+label, list(fr.band) == [bisect.bisect_left(expected_edges, x)+1 for x in fr.annual_rate])
            check('Heldoutbisectbands '+label, list(hr.band) == [bisect.bisect_left(expected_edges, x)+1 for x in hr.annual_rate])
            check('Outofrangesupport '+label, list(hr.outside_training_rate_range) == [x < ordered[0] or x > ordered[-1] for x in hr.annual_rate])
            response, weights = fr.T0.to_numpy()/fr['e_cost_mix_1.0'].to_numpy(), np.sqrt(fr['e_cost_mix_1.0'].to_numpy())
            grad = math.fsum(weights*(fr.annual_rate.to_numpy()-response)/np.sqrt(fr.annual_rate.to_numpy()))/math.fsum(weights)
            check('Interceptscore_notAEconstraint '+label, abs(grad) <= 1e-4 and close(grad, entry['normalized_intercept_score']) and close(entry['fit_AE_not_forced_to_one'], math.fsum(fr.T0)/math.fsum(fr.mu20)))
    for row in cells.to_dict('records'):
        source = fit if row['cohort'] == 'fit' else held
        labels = row['label'].split('|')
        mask = source.line.eq(labels[0])
        if row['dimension'] == 'line_fold':
            field = 'model_fold' if row['cohort'] == 'fit' else 'fold'
            mask &= source[field].eq(int(labels[1]))
        elif row['dimension'] == 'line_business':
            mask &= source.x_new_business.eq(1 if labels[1] == 'new_business' else 0)
        f = source[mask & source.band.eq(row['band'])]
        pred = f.mu20 if row['model_id'] == 'W2-B20' else f.mu19
        observed, expected = math.fsum(f.T0), math.fsum(pred)
        name = row['cohort']+row['model_id']+row['dimension']+row['label']+str(row['band'])
        check('Cellsum '+name, row['rows'] == len(f) and row['positive_rows'] == f.T0.gt(0).sum() and close([row['observed_total'], row['predicted_total'], row['observed_minus_expected']], [observed, expected, observed-expected]))
        undefined = row['actual_over_expected'] is None or pd.isna(row['actual_over_expected'])
        check('Ratioofsums '+name, (undefined and expected == 0) or (expected > 0 and close(row['actual_over_expected'], observed/expected)))
        costs = {}
        for gid, amount in zip(f.group_id, f.T0):
            costs.setdefault(gid, []).append(amount)
        values = [math.fsum(x) for x in costs.values()]
        check('Cellgroups '+name, row['groups'] == len(costs) and row['positive_groups'] == sum(x > 0 for x in values))
        if observed > 0:
            check('Costconcentration '+name, close([row['largest_group_cost_share'], row['cost_concentration_equivalent_groups']], [max(values)/observed, observed*observed/math.fsum(x*x for x in values)]))
        else:
            check('Undefinedcostconcentration '+name, (row['largest_group_cost_share'] is None or pd.isna(row['largest_group_cost_share'])) and (row['cost_concentration_equivalent_groups'] is None or pd.isna(row['cost_concentration_equivalent_groups'])))
        check('Exposuresandsupport '+name, close([row['nominal_exposure'], row['effective_cost_exposure']], [math.fsum(f.exposure), math.fsum(f['e_cost_mix_1.0'])]) and row['outside_training_rate_range'] == f.outside_training_rate_range.sum())
    for cohort, source, models in [('fit', fit, ['W2-B20']), ('heldout', held, ['W2-B20', 'W2-B19'])]:
        for dim in ['line', 'line_fold', 'line_business']:
            for model in models:
                f = cells[cells.cohort.eq(cohort) & cells.dimension.eq(dim) & cells.model_id.eq(model)]
                pred = source.mu20 if model == 'W2-B20' else source.mu19
                check('Partition '+cohort+dim+model, f.rows.sum() == len(source) and close(math.fsum(f.observed_total), math.fsum(source.T0)) and close(math.fsum(f.predicted_total), math.fsum(pred)))
    check('Globalcalibrationonly', close(r['global_AE_B20'], math.fsum(held.T0)/math.fsum(held.mu20)) and close(r['global_AE_B19'], math.fsum(held.T0)/math.fsum(held.mu19)))
    check('Noadditionalfitsorrecipes', r['new_fits'] == r['new_model_recipes'] == r['new_test_prices'] == r['new_bootstrap'] == 0 and r['saved_estimators_replayed_on_training_rows'] == 15)
    check('Closed2024testledger', r['2024_test_closed'] and not r['ledger_read'] and not r['promotion'])
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'checker_sha256': sha(Path(__file__)),
              'passed': sum(x['pass'] for x in checks), 'failed': sum(not x['pass'] for x in checks), 'checks': checks,
              'new_fits': 0, 'professional_independent_validation': False,
              'scope': 'Manualindicator training replay, Python orderstatistics/bisect, math.fsum dictionary cells and conservation. No producer import or refitting.'}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'failed': result['failed'], 'failures': [x for x in checks if not x['pass']]}))
    return 1 if result['failed'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
