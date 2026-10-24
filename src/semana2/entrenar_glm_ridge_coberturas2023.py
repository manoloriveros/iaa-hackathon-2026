"""Una receta ridge estándar; mismos siete efectos, T0 y C0 de B19."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import platform
import sys
import time
import uuid
import warnings

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO.parents[1]
spec = importlib.util.spec_from_file_location('ridge_standard_scope', REPO/'src/semana2/entrenar_desarrollo2023_v8.py')
v8 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v8
spec.loader.exec_module(v8)
u = v8.u
np, pd, pq = u.np, u.pd, u.pq
KEY = u.KEY
MID = 'W2-B20'


def check_sources(plan):
    for item in plan['frozen_sources']:
        u.require(u.sha(ROOT/item['path']) == item['sha256'], 'Fuente cambió: '+item['path'])


def predict(bundle, frame, line):
    v8.guard(frame, line)
    u.require(bundle['line'] == line and bundle['model_id'] == MID, 'Modelo/ramo incompatible')
    u.require(set(bundle['columns']) <= set(frame), 'Faltan predictores')
    rate = u.predict_bundle(bundle, frame)
    u.require(np.isfinite(rate).all() and (rate > 0).all(), 'Tasa no positiva/finita')
    return rate


def fit_ridge(frame, line, fold, recipe):
    v8.guard(frame, line, fold)
    block = recipe['features_by_line'][line]
    u.require(len(block['all']) == 7 and len(set(block['all'])) == 7, 'Siete efectos exactos')
    tr = u.ColumnTransformer([
        ('numeric', u.Pipeline([('median', u.SimpleImputer(strategy='median', keep_empty_features=True)),
                               ('scale', u.StandardScaler())]), block['numeric']),
        ('categorical', u.OneHotEncoder(drop='first', handle_unknown='ignore', min_frequency=50,
                                       max_categories=40, sparse_output=True), block['categorical'])], sparse_threshold=1.)
    x = tr.fit_transform(frame[block['all']])
    e = frame['e_cost_mix_1.0'].to_numpy(float)
    response, weight = frame.T0.to_numpy(float)/e, np.sqrt(e)
    est = u.TweedieRegressor(**recipe['params'])
    with warnings.catch_warnings(record=True) as notes:
        warnings.simplefilter('always')
        est.fit(x, response, sample_weight=weight)
    messages = [{'category': n.category.__name__, 'message': str(n.message)} for n in notes]
    u.require(not any(issubclass(n.category, u.ConvergenceWarning) for n in notes)
              and est.n_iter_ < recipe['params']['max_iter'], 'No convergió; conservar fallo')
    rate = est.predict(x)
    g = weight*(np.sqrt(rate)-response/np.sqrt(rate))/weight.sum()
    score = np.r_[np.asarray(x.T@g).ravel()+est.alpha*est.coef_, g.sum()]
    u.require(np.abs(score).max() <= 1e-4, 'Gradiente penalizado supera criterio previo')
    bundle = {'family': 'TweedieRegressor', 'model_id': MID, 'line': line,
              'columns': block['all'], 'transformer': tr, 'estimator': est}
    receipt = {'line': line, 'fold': fold, 'fit_rows': len(frame), 'params': est.get_params(),
               'features': block['all'], 'warnings': messages, 'n_iter': int(est.n_iter_),
               'max_abs_penalized_gradient': float(np.abs(score).max()),
               'coefficient_squared_norm': float(est.coef_@est.coef_),
               'fit_weight_sum': float(weight.sum())}
    return bundle, receipt


def paired_new(oof, out, config):
    ids = [MID, 'W2-B19', 'W2-B14', 'W2-B00']
    parts = {mid: oof[oof.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True) for mid in ids}
    first = parts[MID]
    codes, groups = pd.factorize(first.group_id, sort=True)
    G = len(groups)
    n = np.bincount(codes, minlength=G)
    y = np.bincount(codes, weights=first.T0, minlength=G)
    sy = np.bincount(codes, weights=np.sqrt(first.T0), minlength=G)
    loss = []
    for mid in ids:
        f = parts[mid]
        u.require(f[KEY].equals(first[KEY]) and f.T0.equals(first.T0)
                  and f['e_cost_mix_1.0'].equals(first['e_cost_mix_1.0']), 'Comparadores incompatibles')
        loss.append(np.bincount(codes, weights=f.unit_deviance, minlength=G))
    loss = np.column_stack(loss)
    rng = np.random.default_rng(config['seed'])
    digest = __import__('hashlib').sha256()
    rows = []
    for start in range(0, config['replicates'], 32):
        draw = rng.integers(0, G, size=(min(32, config['replicates']-start), G), dtype=np.int64)
        digest.update(draw.tobytes())
        null = 8*(np.sqrt(n[draw].sum(axis=1)*y[draw].sum(axis=1))-sy[draw].sum(axis=1))
        vals = loss[draw].sum(axis=1)
        for j, ref in enumerate(ids[1:], 1):
            rows.extend({'replicate': start+k, 'reference': ref, 'delta_D2': float(d)}
                        for k, d in enumerate((vals[:, j]-vals[:, 0])/null))
    boot = pd.DataFrame(rows)
    boot.to_parquet(out/'bootstrap_new_pairs.parquet', index=False)
    pairs = []
    null = 8*(np.sqrt(n.sum()*y.sum())-sy.sum())
    for j, ref in enumerate(ids[1:], 1):
        advantage = loss[:, j]-loss[:, 0]
        keep = np.ones(G, dtype=bool)
        removed = max(5, int(np.ceil(.001*G)))
        keep[np.argsort(-advantage, kind='stable')[:removed]] = False
        reduced = 8*(np.sqrt(n[keep].sum()*y[keep].sum())-sy[keep].sum())
        vals = boot.loc[boot.reference.eq(ref), 'delta_D2']
        pairs.append({'candidate': MID, 'reference': ref, 'delta_D2': float(advantage.sum()/null),
                      'exploratory_lower95': float(vals.quantile(.025)), 'exploratory_upper95': float(vals.quantile(.975)),
                      'groups': G, 'removed_favorable_groups': removed,
                      'delta_after_removal': float(advantage[keep].sum()/reduced)})
    u.dump(out/'new_pairs.json', {'pairs': pairs, 'draws_sha256': digest.hexdigest(), 'config': config})
    return pairs


def main():
    planpath = Path(sys.argv[1]).resolve()
    plan = u.read(planpath)
    u.require(plan['model_id'] == MID and u.sha(Path(__file__)) == plan['code_sha256'], 'Código/receta cambió')
    check_sources(plan)
    # A deterministic output and exclusive creation prevent accidental repeat fits.
    out = ROOT/plan['output_run']
    out.mkdir(exist_ok=False)
    for name in ['models', 'diagnostics']:
        (out/name).mkdir()
    tick = time.perf_counter()
    start = datetime.now(timezone.utc).isoformat()
    forum = (ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes()
    u.require(forum.count(('<!-- aporte:'+plan['forum_prior']+' -->').encode()) == 1, 'Falta receta previa')
    for path, name in [(planpath, 'plan_snapshot.json'), (Path(__file__), 'code_snapshot.py')]:
        (out/name).write_bytes(path.read_bytes())
    (out/'forum_before_fit.md').write_bytes(forum)
    u.dump(out/'environment.json', {'python': sys.version, 'platform': platform.platform(),
                                  'numpy': np.__version__, 'pandas': pd.__version__,
                                  'sklearn': u.sklearn.__version__, 'threads': 2})
    def event(name, **values):
        item = {'utc': datetime.now(timezone.utc).isoformat(), 'event': name, **values}
        with (out/'events.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(item)+'\n')
        print(json.dumps(item), flush=True)
    event('started', run=u.relative(out), expected_new_fits=15)
    source = ROOT/plan['input_run']
    old = pq.read_table(source/'oof_2023.parquet').to_pandas()
    u.assert_2023(old.drop_duplicates(KEY))
    u.require(old.model_id.nunique() == 20 and len(old) == 20*50094, 'Catálogo padre incompleto')
    outputs, receipts, trainval, coverage = [], [], [], []
    for line in u.LINES:
        field = 'x_cover_type' if line == 'motor' else 'x_accidental_damage_cover'
        for fold in range(5):
            frame = pq.read_table(source/f'inputs_2023/{line}_fold{fold}.parquet').to_pandas()
            v8.guard(frame, line)
            fit, valid = frame[frame.fold.ne(fold)].copy(), frame[frame.fold.eq(fold)].copy()
            u.require(all(set(fit[c]).isdisjoint(valid[c]) for c in ['group_id', 'customer_id', 'address_id']), 'Fuga de componente')
            event('fit_started', line=line, fold=fold)
            with u.threadpool_limits(limits=2):
                bundle, receipt = fit_ridge(fit, line, fold, plan['recipe'])
            node = out/'models'/f'{line}_fold{fold}'
            node.mkdir()
            u.joblib.dump(bundle, node/'bundle.joblib', compress=3)
            with u.threadpool_limits(limits=2):
                rate = predict(bundle, valid, line)
                replay = predict(u.joblib.load(node/'bundle.joblib'), valid, line)
                fitrate = predict(bundle, fit, line)
            u.require(np.array_equal(rate, replay), 'Replay no exacto')
            receipt['replay_exact'] = True
            u.dump(node/'receipt.json', receipt)
            receipts.append(receipt)
            ref = old[old.model_id.eq('W2-B19') & old.line.eq(line) & old.fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
            ordered = valid.sort_values(KEY).reset_index(drop=True)
            u.require(ref[KEY].equals(ordered[KEY]) and ref.T0.equals(ordered.T0)
                      and ref['e_cost_mix_1.0'].equals(ordered['e_cost_mix_1.0']), 'T0/C0/claves cambió')
            rr = pd.DataFrame({**{k: valid[k].to_numpy() for k in KEY}, 'rate': rate}).sort_values(KEY).rate.to_numpy()
            ref['model_id'], ref['annual_rate'] = MID, rr
            ref['prediction'] = rr*ordered['e_cost_mix_1.0'].to_numpy()
            ref['unit_deviance'] = u.unit_deviance(ref.T0, ref.prediction)
            outputs.append(ref)
            for role, ff, rates in [('fit', fit, fitrate), ('validation', valid, rate)]:
                trainval.append({'line': line, 'fold': fold, 'role': role,
                                 **u.metrics(ff.assign(prediction=rates*ff['e_cost_mix_1.0'].to_numpy()))})
            if fold == 0:
                m = frame[KEY].copy()
                m['coverage'] = frame[field].astype(str) if line == 'motor' else np.where(frame[field].eq(1), 'AD_yes', 'AD_no')
                coverage.append(m)
            event('fit_completed', line=line, fold=fold, completed_fits=len(receipts))
    new = pd.concat(outputs, ignore_index=True).sort_values(KEY).reset_index(drop=True)
    u.require(len(new) == 50094 and not new.duplicated(KEY).any(), 'OOF incompleto')
    new.to_parquet(out/'new_oof_2023.parquet', index=False)
    combined = pd.concat([old, new], ignore_index=True).sort_values(['model_id', *KEY]).reset_index(drop=True)
    combined.to_parquet(out/'oof_2023.parquet', index=False)
    meta = pd.concat(coverage, ignore_index=True)
    summaries, segments = [], []
    for mid in [MID, 'W2-B19', 'W2-B14', 'W2-B00']:
        f = combined[combined.model_id.eq(mid)].merge(meta, on=KEY, validate='one_to_one')
        summaries.append({'model_id': mid, **u.metrics(f), 'conditional_nominal_2023': float((f.exposure*f.annual_rate).sum())})
        business = np.where(f.x_new_business.eq(1), 'new_business', 'renewal')
        dims = {'line': f.line.astype(str), 'fold': f.fold.astype(str), 'business': business,
                'line_business': f.line.astype(str)+'_'+business,
                'line_coverage': f.line.astype(str)+'_'+f.coverage,
                'line_business_coverage': f.line.astype(str)+'_'+business+'_'+f.coverage}
        for dim, labels in dims.items():
            for label, cell in f.assign(label=labels).groupby('label', observed=True):
                segments.append({'model_id': mid, 'dimension': dim, 'label': str(label), **u.metrics(cell)})
    u.dump(out/'diagnostics/segments.json', segments)
    u.dump(out/'diagnostics/train_validation.json', trainval)
    pairs = paired_new(combined, out/'diagnostics', plan['bootstrap'])
    check_sources(plan)
    report = {'id': plan['id'], 'author': 'Codex', 'model_id': MID, 'run': u.relative(out),
              'started_utc': start, 'completed_utc': datetime.now(timezone.utc).isoformat(),
              'plan_sha256': u.sha(planpath), 'code_sha256': u.sha(Path(__file__)),
              'summary': summaries, 'pairs': pairs, 'new_price_base_fits': len(receipts),
              'new_constants': 0, 'new_auxiliary_fits': 0, 'new_reporting_fits': 0,
              'reference': 'W2-B00', 'promotion': False, 'alternatives_preserved': True,
              'scope_2024_test': 'closed; no prices, predictions, scores or ledger access',
              'prior_external2024_header_exposure_disclosed': True,
              'submissions': 0, 'remote': False, 'professional_independent_validation': False,
              'elapsed_seconds': time.perf_counter()-tick}
    u.require(len(receipts) == 15, 'Conteo distinto de quince ajustes')
    u.dump(out/'report.json', report)
    event('completed', new_fits=15)
    u.dump(out/'manifest.json', {'files': [{'path': p.relative_to(out).as_posix(), 'sha256': u.sha(p)}
                                        for p in sorted(out.rglob('*')) if p.is_file()]})
    print(json.dumps({'run': u.relative(out), 'summary': summaries, 'pairs': pairs}), flush=True)


if __name__ == '__main__':
    main()
