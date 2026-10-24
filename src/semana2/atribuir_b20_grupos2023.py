"""Atribución de pérdidas OOF ya guardadas; cero fit, precios nuevos o bootstrap."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import sys

for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[name] = '2'
REPO = Path(__file__).resolve().parents[2]
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
from threadpoolctl import threadpool_limits

KEY = ['market', 'line', 'row_id']
REFS = ['W2-B19', 'W2-B14', 'W2-B00']
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
dump = lambda p, x: p.write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def require(condition, message):
    if not bool(condition):
        raise ValueError(message)


def guard(frame):
    require(len(frame) > 0 and frame.year.eq(2023).all(), 'Solo2023')
    require(not frame.is_test.any() if 'is_test' in frame else True, 'Test cerrado')
    require(not frame.duplicated(KEY).any(), 'Claves repetidas')
    require(np.isfinite(frame.T0).all() and frame.T0.ge(0).all(), 'T0 inválido')
    require(np.isfinite(frame.prediction).all() and frame.prediction.gt(0).all(), 'Predicción inválida')


def pair_frame(candidate, reference):
    guard(candidate)
    guard(reference)
    a, b = candidate.sort_values(KEY).reset_index(drop=True), reference.sort_values(KEY).reset_index(drop=True)
    require(a[KEY].equals(b[KEY]), 'Claves incompatibles')
    for name in ['T0', 'fold', 'group_id', 'x_new_business', 'e_cost_mix_1.0']:
        require(a[name].equals(b[name]), 'Fuente incompatible '+name)
    f = a[KEY+['year', 'fold', 'group_id', 'T0', 'x_new_business']].copy()
    f['reference'], f['mu20'], f['muref'] = b.model_id.iloc[0], a.prediction, b.prediction
    s20, sr = np.sqrt(f.mu20), np.sqrt(f.muref)
    f['outcome_term'] = 4*f.T0*(1/sr-1/s20)
    f['prediction_term'] = 4*(sr-s20)
    f['gain'] = f.outcome_term+f.prediction_term
    f['stored_gain'] = b.unit_deviance-a.unit_deviance
    require(np.allclose(f.gain, f.stored_gain, rtol=2e-9, atol=2e-8), 'Identidad de pérdida falla')
    return f


def null_deviance(f):
    if len(f) == 0 or f.T0.sum() == 0:
        return 0.
    return float(8*(np.sqrt(len(f)*f.T0.sum())-np.sqrt(f.T0).sum()))


def describe(f, full_null):
    gain = float(f.gain.sum())
    null = null_deviance(f)
    return {'rows': len(f), 'groups': int(f.group_id.nunique()), 'positive_rows': int(f.T0.gt(0).sum()),
            'observed_total': float(f.T0.sum()), 'mu20_total': float(f.mu20.sum()), 'muref_total': float(f.muref.sum()),
            'gain': gain, 'outcome_term': float(f.outcome_term.sum()), 'prediction_term': float(f.prediction_term.sum()),
            'null_deviance': null, 'delta_own_null': gain/null if null > 0 else None,
            'contribution_full_null': gain/full_null, 'mean_log_change_20_vs19': float(f.log_change.mean()) if len(f) else None}


def main():
    pp = Path(sys.argv[1]).resolve()
    p = read(pp)
    require(sha(Path(__file__)) == p['producer_sha256'], 'Código cambió')
    for item in p['frozen_sources']:
        require(sha(ROOT/item['path']) == item['sha256'], 'Fuente cambió '+item['path'])
    forum = (ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes()
    require(forum.count(('<!-- aporte:'+p['forum_prior']+' -->').encode()) == 1, 'Falta preinscripción')
    def no_fit(*args, **kwargs):
        raise AssertionError('Fit bloqueado en atribución')
    for cls in [TweedieRegressor, ColumnTransformer, SimpleImputer, StandardScaler, OneHotEncoder, Pipeline]:
        cls.fit = no_fit
        if hasattr(cls, 'fit_transform'):
            cls.fit_transform = no_fit
    source = ROOT/p['ridge_run']
    wanted = ['W2-B20', *REFS]
    oof = pq.read_table(source/'oof_2023.parquet', filters=[('model_id', 'in', wanted)]).to_pandas()
    parts = {mid: f.sort_values(KEY).reset_index(drop=True) for mid, f in oof.groupby('model_id')}
    require(set(parts) == set(wanted) and all(len(f) == 50094 for f in parts.values()), 'OOF incompleto')
    for f in parts.values():
        guard(f)
    out = ROOT/p['output_run']
    out.mkdir(exist_ok=False)
    (out/'plan_snapshot.json').write_bytes(pp.read_bytes())
    (out/'code_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (out/'forum_before_analysis.md').write_bytes(forum)
    started = datetime.now(timezone.utc).isoformat()
    candidate = parts['W2-B20']
    logframe = candidate[KEY].copy()
    logframe['log_change'] = np.log(candidate.annual_rate/parts['W2-B19'].annual_rate)
    for term in ['intercept', 'business', 'coverage', 'other']:
        logframe['log_'+term] = 0.
    meta = []
    frame_source = ROOT/p['frame_source']
    for line in ['motor', 'buildings', 'contents']:
        for fold in range(5):
            f = pq.read_table(frame_source/f'inputs_2023/{line}_fold{fold}.parquet').to_pandas()
            require(f.year.eq(2023).all() and not f.is_test.any(), 'Entradas fuera de2023')
            valid = f[f.fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
            pos = candidate.index[candidate.line.eq(line) & candidate.fold.eq(fold)]
            require(candidate.loc[pos, KEY].reset_index(drop=True).equals(valid[KEY]), 'Orden del diseño')
            b20 = joblib.load(source/'models'/f'{line}_fold{fold}'/'bundle.joblib')
            b19 = joblib.load(frame_source/'models'/f'W2-B19_{line}_fold{fold}'/'bundle.joblib')
            require(b20['columns'] == b19['columns'], 'Diseños no comparables')
            names = list(b20['transformer'].get_feature_names_out())
            require(names == list(b19['transformer'].get_feature_names_out()), 'Nombres de diseño distintos')
            with threadpool_limits(limits=2):
                X = b20['transformer'].transform(valid[b20['columns']])
            diff = b20['estimator'].coef_-b19['estimator'].coef_
            business = [j for j, n in enumerate(names) if n.endswith('__x_new_business')]
            coverage = [j for j, n in enumerate(names) if '__x_cover_type_' in n or n.endswith('__x_accidental_damage_cover')]
            other = [j for j in range(len(names)) if j not in business+coverage]
            require(len(business) == 1 and len(coverage) > 0, 'Bloques de efectos ausentes')
            logframe.loc[pos, 'log_intercept'] = float(b20['estimator'].intercept_-b19['estimator'].intercept_)
            for label, ids in [('business', business), ('coverage', coverage), ('other', other)]:
                logframe.loc[pos, 'log_'+label] = np.asarray(X[:, ids]@diff[ids]).ravel()
            if fold == 0:
                field = 'x_cover_type' if line == 'motor' else 'x_accidental_damage_cover'
                m = f[KEY].copy()
                m['coverage'] = f[field].astype(str) if line == 'motor' else np.where(f[field].eq(1), 'AD_yes', 'AD_no')
                meta.append(m)
    log_error = float(np.abs(logframe.log_change-logframe[['log_intercept', 'log_business', 'log_coverage', 'log_other']].sum(axis=1)).max())
    require(log_error < 2e-12, 'Descomposición log no concilia')
    logframe.to_parquet(out/'log_rate_change_components.parquet', index=False)
    meta = pd.concat(meta, ignore_index=True)
    require(not meta.duplicated(KEY).any(), 'Metadata duplicada')
    fixed_ids = set(pq.read_table(ROOT/p['fixed_B19_selection'], columns=['group_id']).column('group_id').to_pylist())
    require(len(fixed_ids) == 12, 'Selección B19 fija distinta de12')
    rows, groups, segments, path, summaries, selected = [], [], [], [], [], {}
    for ref in REFS:
        f = pair_frame(candidate, parts[ref]).merge(meta, on=KEY, validate='one_to_one').merge(logframe, on=KEY, validate='one_to_one')
        full_null = null_deviance(f)
        require(full_null > 0, 'Nula no positiva')
        g = f.groupby('group_id', sort=True).agg(gain=('gain', 'sum'), rows=('T0', 'size'), T0=('T0', 'sum'),
                positive_rows=('T0', lambda x: int(x.gt(0).sum())), outcome_term=('outcome_term', 'sum'),
                prediction_term=('prediction_term', 'sum'), mu20=('mu20', 'sum'), muref=('muref', 'sum')).reset_index()
        g = g.sort_values(['gain', 'group_id'], ascending=[False, True], kind='stable').reset_index(drop=True)
        require(len(g) == 30869, 'Grupos incompletos')
        g['rank'] = np.arange(1, len(g)+1)
        g['reference'] = ref
        g['selected31'] = g['rank'].le(31)
        chosen = set(g.head(31).group_id)
        selected[ref] = chosen
        f['selected31'] = f.group_id.isin(chosen)
        gain = float(f.gain.sum())
        prefix = g.gain.cumsum().to_numpy()
        crossing = np.flatnonzero(gain-prefix < 0)
        crossing_k = int(crossing[0]+1) if len(crossing) else None
        for k in [0, 1, 5, 10, 31]:
            keep = ~f.group_id.isin(set(g.head(k).group_id))
            path.append({'reference': ref, 'removed': k, **describe(f[keep], full_null)})
        saved = next(x for x in read(source/'diagnostics/new_pairs.json')['pairs'] if x['reference'] == ref)
        remainder = describe(f[~f.selected31], full_null)
        require(np.isclose(gain/full_null, saved['delta_D2'], rtol=1e-10, atol=1e-12), 'Delta original no concilia')
        require(np.isclose(remainder['delta_own_null'], saved['delta_after_removal'], rtol=1e-10, atol=1e-12), 'Retiro original no concilia')
        select = describe(f[f.selected31], full_null)
        summaries.append({'reference': ref, 'all': describe(f, full_null), 'selected31': select, 'remaining': remainder,
                          'positive_gain_groups': int(g.gain.gt(0).sum()), 'negative_gain_groups': int(g.gain.lt(0).sum()),
                          'gross_positive_gain': float(g.loc[g.gain.gt(0), 'gain'].sum()),
                          'gross_negative_gain': float(g.loc[g.gain.lt(0), 'gain'].sum()),
                          'selected_share_net_gain': select['gain']/gain,
                          'selected_share_gross_positive_gain': select['gain']/g.loc[g.gain.gt(0), 'gain'].sum(),
                          'first_adverse_prefix_k': crossing_k,
                          'fixed_B19_12': describe(f[f.group_id.isin(fixed_ids)], full_null)})
        business = np.where(f.x_new_business.eq(1), 'new_business', 'renewal')
        dims = {'line': f.line.astype(str), 'business': business, 'line_business': f.line.astype(str)+'_'+business,
                'fold': f.fold.astype(str), 'line_coverage': f.line.astype(str)+'_'+f.coverage,
                'target_state': np.where(f.T0.gt(0), 'positive', 'zero')}
        for cohort, mask in [('all', np.ones(len(f), dtype=bool)), ('selected31', f.selected31), ('remaining', ~f.selected31)]:
            for dimension, labels in dims.items():
                for label, cell in f[mask].assign(label=np.asarray(labels)[mask]).groupby('label', observed=True):
                    segments.append({'reference': ref, 'cohort': cohort, 'dimension': dimension, 'label': str(label), **describe(cell, full_null),
                                     **{name: float(cell[name].mean()) for name in ['log_intercept', 'log_business', 'log_coverage', 'log_other']}})
        rows.append(f)
        groups.append(g)
    overlap, cross = [], []
    for ref in REFS:
        for selection in REFS:
            overlap.append({'reference': ref, 'selection_reference': selection, 'shared_groups': len(selected[ref] & selected[selection])})
            f = next(x for x in rows if x.reference.iloc[0] == ref)
            cross.append({'reference': ref, 'selection_reference': selection,
                          **describe(f[~f.group_id.isin(selected[selection])], null_deviance(f))})
    pd.concat(rows, ignore_index=True).to_parquet(out/'row_attribution_2023.parquet', index=False)
    pd.concat(groups, ignore_index=True).to_parquet(out/'group_attribution_2023.parquet', index=False)
    pd.DataFrame(segments).to_parquet(out/'segment_attribution_2023.parquet', index=False)
    dump(out/'removal_paths.json', path)
    dump(out/'selection_overlap.json', overlap)
    dump(out/'cross_selection_removal.json', cross)
    report = {'id': p['id'], 'author': 'Codex', 'started_utc': started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
              'run': rel(out), 'summary': summaries, 'max_log_identity_error': log_error,
              'new_fits': 0, 'new_price_predictions': 0, 'new_candidate_recipes': 0, 'bootstrap_repeated': False,
              'scope': 'Saved2023only; reconstruct declared loss differences and evaluation deletions, not a new validation sample.',
              'scope_2024_test': 'closed; no fit,prediction,score or ledger access', 'prior_external2024_subject_exposure_disclosed': True,
              'reference': 'W2-B00', 'promotion': False, 'professional_independent_validation': False,
              'code_sha256': sha(Path(__file__)), 'plan_sha256': sha(pp)}
    for item in p['frozen_sources']:
        require(sha(ROOT/item['path']) == item['sha256'], 'Fuente cambió al cierre')
    dump(out/'report.json', report)
    dump(out/'manifest.json', {'files': [{'path': x.relative_to(out).as_posix(), 'sha256': sha(x)} for x in sorted(out.rglob('*')) if x.is_file()]})
    print(json.dumps({'run': rel(out), 'summary': summaries, 'max_log_error': log_error}), flush=True)


if __name__ == '__main__':
    main()
