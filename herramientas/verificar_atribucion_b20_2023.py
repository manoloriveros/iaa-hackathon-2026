"""Verificador separado: desviancia cuadrática, math.fsum, diccionarios y logbloques."""
from pathlib import Path
from datetime import datetime, timezone
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
from sklearn.linear_model import TweedieRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline

read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: __import__('hashlib').sha256(p.read_bytes()).hexdigest()
KEY = ['market', 'line', 'row_id']


def dev(y, mu):
    return 4*(math.sqrt(y)-math.sqrt(mu))**2/math.sqrt(mu)


def main():
    run = Path(sys.argv[1]).resolve()
    run.relative_to(REPO/'privado/semana2/desarrollo2023')
    output = run/(sys.argv[2] if len(sys.argv) > 2 else 'verification.json')
    assert output.parent == run and output.suffix == '.json', 'Salida de verificación fuera de corrida'
    assert not output.exists(), 'Ya verificado; no repetir sin cambio'
    plan, report = read(run/'plan_snapshot.json'), read(run/'report.json')
    checks = []
    def check(name, value):
        checks.append({'name': name, 'pass': bool(value)})
    close = lambda a, b: np.allclose(a, b, rtol=3e-9, atol=2e-7, equal_nan=True)
    for cls in [TweedieRegressor, ColumnTransformer, SimpleImputer, StandardScaler, OneHotEncoder, Pipeline]:
        cls.fit = lambda *a, **k: (_ for _ in ()).throw(AssertionError('Fit bloqueado'))
        if hasattr(cls, 'fit_transform'):
            cls.fit_transform = cls.fit
    for item in plan['frozen_sources']:
        check('Source '+item['path'], sha(ROOT/item['path']) == item['sha256'])
    for item in read(run/'manifest.json')['files']:
        check('Artifact '+item['path'], sha(run/item['path']) == item['sha256'])
    check('Codeandplansnapshot', sha(run/'code_snapshot.py') == report['code_sha256'] == plan['producer_sha256'] and sha(run/'plan_snapshot.json') == report['plan_sha256'])
    text = (run/'forum_before_analysis.md').read_text(encoding='utf-8-sig')
    for ident in [plan['forum_prior'], plan['forum_amendment']]:
        m = re.search(r'^## Codex \| '+re.escape(ident)+r' \| ([^|]+) \|', text, re.M)
        check('Preregistrationbeforecalculation '+ident, m is not None and datetime.fromisoformat(m[1].strip()) < datetime.fromisoformat(report['started_utc']))
    old = pq.read_table(ROOT/plan['ridge_run']/'oof_2023.parquet', filters=[('model_id', 'in', ['W2-B20', 'W2-B19', 'W2-B14', 'W2-B00'])]).to_pandas()
    source = {mid: f.sort_values(KEY).reset_index(drop=True) for mid, f in old.groupby('model_id')}
    rows = pq.read_table(run/'row_attribution_2023.parquet').to_pandas()
    groups = pq.read_table(run/'group_attribution_2023.parquet').to_pandas()
    segments = pq.read_table(run/'segment_attribution_2023.parquet').to_pandas()
    check('Complete2023diagnostic', len(rows) == 3*50094 and rows.year.eq(2023).all() and not rows.duplicated(['reference', *KEY]).any())
    fixed = set(pq.read_table(ROOT/plan['fixed_B19_selection'], columns=['group_id']).column('group_id').to_pylist())
    check('Prior12selectionfixed', len(fixed) == 12)
    sets, arrays = {}, {}
    for ref in ['W2-B19', 'W2-B14', 'W2-B00']:
        f = rows[rows.reference.eq(ref)].sort_values(KEY).reset_index(drop=True)
        candidate, reference = source['W2-B20'], source[ref]
        check('SavedkeysT0C0 '+ref, f[KEY].equals(candidate[KEY]) and candidate[KEY].equals(reference[KEY]) and candidate.T0.equals(reference.T0) and candidate['e_cost_mix_1.0'].equals(reference['e_cost_mix_1.0']))
        check('Savedpricesonly '+ref, np.array_equal(f.mu20, candidate.prediction) and np.array_equal(f.muref, reference.prediction) and f.group_id.equals(candidate.group_id))
        gains = np.array([dev(y, r)-dev(y, c) for y, r, c in zip(f.T0, f.muref, f.mu20)])
        outcome = np.array([4*y*(1/math.sqrt(r)-1/math.sqrt(c)) for y, r, c in zip(f.T0, f.muref, f.mu20)])
        level = np.array([4*(math.sqrt(r)-math.sqrt(c)) for r, c in zip(f.muref, f.mu20)])
        check('Squaredeviancegain '+ref, close(gains, f.gain) and close(gains, outcome+level))
        check('Independentlossparts '+ref, close(outcome, f.outcome_term) and close(level, f.prediction_term))
        member = {}
        for i, gid in enumerate(f.group_id):
            member.setdefault(gid, []).append(i)
        gainmap = {gid: math.fsum(gains[ids]) for gid, ids in member.items()}
        rank = sorted(member, key=lambda gid: (-gainmap[gid], gid))
        selected = set(rank[:31])
        sets[ref] = selected
        arrays[ref] = (f, gains)
        g = groups[groups.reference.eq(ref)].sort_values('rank').reset_index(drop=True)
        check('Groupcountsandranking '+ref, len(g) == 30869 and set(g.head(31).group_id) == selected and list(g.head(31).group_id) == rank[:31])
        check('Independentallgroupsums '+ref, close(g.gain, [gainmap[gid] for gid in g.group_id]))
        check('Selectedwholecomponents '+ref, np.array_equal(f.selected31, f.group_id.isin(selected)))
        mean = math.fsum(f.T0)/len(f)
        fullnull = math.fsum(dev(y, mean) for y in f.T0)
        total = math.fsum(gains)
        s = next(x for x in report['summary'] if x['reference'] == ref)
        def verify_summary(label, cell, indices):
            ff = f.iloc[indices]
            GG = gains[indices]
            yy = math.fsum(ff.T0)
            nn = math.fsum(dev(y, yy/len(ff)) for y in ff.T0) if len(ff) and yy > 0 else 0.
            check('Profile '+ref+label, cell['rows'] == len(ff) and cell['groups'] == ff.group_id.nunique() and cell['positive_rows'] == ff.T0.gt(0).sum()
                  and close([cell['gain'], cell['observed_total'], cell['mu20_total'], cell['muref_total'], cell['null_deviance']],
                            [math.fsum(GG), yy, math.fsum(ff.mu20), math.fsum(ff.muref), nn]))
            check('Sharednullcontribution '+ref+label, close(cell['contribution_full_null'], math.fsum(GG)/fullnull))
            missing = cell['delta_own_null'] is None or pd.isna(cell['delta_own_null'])
            check('Ownnull '+ref+label, (missing and nn == 0) or (nn > 0 and close(cell['delta_own_null'], math.fsum(GG)/nn)))
        mask = f.group_id.isin(selected).to_numpy()
        for label, select in [('all', np.ones(len(f), bool)), ('selected31', mask), ('remaining', ~mask), ('fixed_B19_12', f.group_id.isin(fixed).to_numpy())]:
            verify_summary(label, s[label], np.flatnonzero(select))
        check('Gainselectedplusremaining '+ref, close(s['selected31']['gain']+s['remaining']['gain'], total))
        check('Grossgainlossconservation '+ref, close([s['gross_positive_gain'], s['gross_negative_gain']], [math.fsum(v for v in gainmap.values() if v > 0), math.fsum(v for v in gainmap.values() if v < 0)]))
        check('Selectedshares '+ref, close(s['selected_share_net_gain'], s['selected31']['gain']/total) and close(s['selected_share_gross_positive_gain'], s['selected31']['gain']/s['gross_positive_gain']))
        cumulative, crossing = 0., None
        for k, gid in enumerate(rank, 1):
            cumulative += gainmap[gid]
            if total-cumulative < 0:
                crossing = k
                break
        check('Smallestadverseprefix '+ref, crossing == s['first_adverse_prefix_k'])
        check('Signnotadenominatorartifact '+ref, s['remaining']['gain'] < 0 and s['remaining']['null_deviance'] > 0 and s['remaining']['contribution_full_null'] < 0 and s['remaining']['delta_own_null'] < 0)
        saved = next(x for x in read(ROOT/plan['ridge_run']/'diagnostics/new_pairs.json')['pairs'] if x['reference'] == ref)
        check('Originalpointand31reproduced '+ref, close(s['all']['delta_own_null'], saved['delta_D2']) and close(s['remaining']['delta_own_null'], saved['delta_after_removal']))
        for row in [x for x in read(run/'removal_paths.json') if x['reference'] == ref]:
            keep = ~f.group_id.isin(set(rank[:row['removed']])).to_numpy()
            verify_summary('remove'+str(row['removed']), row, np.flatnonzero(keep))
        for row in segments[segments.reference.eq(ref)].to_dict('records'):
            cohort = np.ones(len(f), bool) if row['cohort'] == 'all' else mask if row['cohort'] == 'selected31' else ~mask
            business = np.where(f.x_new_business.eq(1), 'new_business', 'renewal')
            labels = {'line': f.line.astype(str), 'business': business, 'line_business': f.line.astype(str)+'_'+business,
                      'fold': f.fold.astype(str), 'line_coverage': f.line.astype(str)+'_'+f.coverage,
                      'target_state': np.where(f.T0.gt(0), 'positive', 'zero')}[row['dimension']]
            indices = np.flatnonzero(cohort & (np.asarray(labels) == row['label']))
            verify_summary(row['cohort']+row['dimension']+row['label'], row, indices)
        for cohort in ['all', 'selected31', 'remaining']:
            for dim in ['line', 'business', 'line_business', 'fold', 'line_coverage', 'target_state']:
                ss = segments[segments.reference.eq(ref) & segments.cohort.eq(cohort) & segments.dimension.eq(dim)]
                check('Exclusivepartition '+ref+cohort+dim, close(math.fsum(ss.gain), s[cohort]['gain']) and ss.rows.sum() == s[cohort]['rows'])
    for row in read(run/'selection_overlap.json'):
        check('Selectionoverlap '+row['reference']+row['selection_reference'], row['shared_groups'] == len(sets[row['reference']] & sets[row['selection_reference']]))
    for row in read(run/'cross_selection_removal.json'):
        f, gain = arrays[row['reference']]
        mask = ~f.group_id.isin(sets[row['selection_reference']]).to_numpy()
        remain = f[mask]
        mean = math.fsum(remain.T0)/len(remain)
        null = math.fsum(dev(y, mean) for y in remain.T0)
        check('Fixedcrossremoval '+row['reference']+row['selection_reference'], close(row['gain'], math.fsum(gain[mask])) and close(row['delta_own_null'], math.fsum(gain[mask])/null))
    # Reuse an already checked independent indicator builder, not this producer's transform arithmetic.
    spec = importlib.util.spec_from_file_location('prior_ridge_indicator_oracle', REPO/'herramientas/verificar_glm_ridge_coberturas2023.py')
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    log = pq.read_table(run/'log_rate_change_components.parquet').to_pandas()
    candidate = source['W2-B20']
    check('Logkeysandratio', log[KEY].equals(candidate[KEY]) and close(log.log_change, np.log(candidate.annual_rate/source['W2-B19'].annual_rate)))
    recipe = read(ROOT/plan['ridge_run']/'plan_snapshot.json')['recipe']
    for line in ['motor', 'buildings', 'contents']:
        for fold in range(5):
            raw = pq.read_table(ROOT/plan['frame_source']/f'inputs_2023/{line}_fold{fold}.parquet').to_pandas()
            valid = raw[raw.fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
            b20 = joblib.load(ROOT/plan['ridge_run']/'models'/f'{line}_fold{fold}'/'bundle.joblib')
            b19 = joblib.load(ROOT/plan['frame_source']/'models'/f'W2-B19_{line}_fold{fold}'/'bundle.joblib')
            matrix = prior.manual_matrix(valid, recipe['features_by_line'][line], b20['transformer'])
            names = list(b20['transformer'].get_feature_names_out())
            coefficients = b20['estimator'].coef_-b19['estimator'].coef_
            pos = candidate.index[candidate.line.eq(line) & candidate.fold.eq(fold)]
            one = log.loc[pos]
            check('Independentintercept '+line+str(fold), close(one.log_intercept, b20['estimator'].intercept_-b19['estimator'].intercept_))
            num = recipe['features_by_line'][line]['numeric']
            bi = [num.index('x_new_business')]
            co = [num.index('x_accidental_damage_cover')] if line != 'motor' else [j for j, name in enumerate(names) if name.startswith('categorical__x_cover_type_')]
            ot = [j for j in range(len(names)) if j not in bi+co]
            for name, idx in [('business', bi), ('coverage', co), ('other', ot)]:
                check('Independentlogblock '+name+line+str(fold), close(one['log_'+name], matrix[:, idx]@coefficients[idx]))
            field = 'x_cover_type' if line == 'motor' else 'x_accidental_damage_cover'
            cov = valid[field].astype(str) if line == 'motor' else np.where(valid[field].eq(1), 'AD_yes', 'AD_no')
            check('Originalcoveragemetadata '+line+str(fold), np.array_equal(arrays['W2-B19'][0].loc[pos, 'coverage'], cov))
    logerr = np.abs(log.log_change-log[['log_intercept', 'log_business', 'log_coverage', 'log_other']].sum(axis=1)).max()
    check('Exactlogidentity', logerr < 2e-12 and close(logerr, report['max_log_identity_error']))
    check('Noadditionalmodelwork', report['new_fits'] == report['new_price_predictions'] == report['new_candidate_recipes'] == 0 and not report['bootstrap_repeated'] and not report['promotion'])
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'checker_sha256': sha(Path(__file__)),
              'passed': sum(x['pass'] for x in checks), 'failed': sum(not x['pass'] for x in checks), 'checks': checks,
              'new_fits': 0, 'bootstrap_repeated': False, 'professional_independent_validation': False,
              'scope': 'Separate squaredeviance/math.fsum/group dictionary ranking/partition/null and manualindicator logblock verification; no producer import.'}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'failed': result['failed'], 'failures': [x for x in checks if not x['pass']]}))
    return 1 if result['failed'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
