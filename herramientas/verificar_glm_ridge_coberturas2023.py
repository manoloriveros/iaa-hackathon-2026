"""Cotejo separado de B20, sin importar su productor y con fit bloqueado."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import hashlib
import json
import re
import sys

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
spec = importlib.util.spec_from_file_location('ridge_independent_oracle', REPO/'herramientas/verificar_desarrollo2023_semana2.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
np, pd, pq = c.np, c.pd, c.pq
KEY = c.KEY
MID = 'W2-B20'


def manual_matrix(frame, block, tr):
    numeric = tr.named_transformers_['numeric']
    raw = frame[block['numeric']].to_numpy(float)
    values = np.where(np.isnan(raw), numeric['median'].statistics_, raw)
    num = (values-numeric['scale'].mean_)/numeric['scale'].scale_
    enc = tr.named_transformers_['categorical']
    columns = []
    for j, field in enumerate(block['categorical']):
        inf = enc.infrequent_categories_[j]
        rare = set([] if inf is None else inf)
        levels = [v for v in enc.categories_[j] if v not in rare]
        if rare:
            levels.append('__infrequent__')
        dropped = enc.categories_[j][int(enc.drop_idx_[j])] if enc.drop_idx_[j] is not None else None
        if dropped in rare:
            dropped = '__infrequent__'
        for value in levels:
            if value == dropped:
                continue
            mask = frame[field].isin(rare) if value == '__infrequent__' else frame[field].eq(value)
            columns.append(mask.to_numpy(float))
    cat = np.column_stack(columns) if columns else np.empty((len(frame), 0))
    return np.column_stack([num, cat])


def main():
    run = Path(sys.argv[1]).resolve()
    run.relative_to(REPO/'privado/semana2/desarrollo2023')
    out = run/'verification.json'
    if out.exists():
        raise FileExistsError('Verificación existente; no repetir sin motivo nuevo')
    p, r = c.read(run/'plan_snapshot.json'), c.read(run/'report.json')
    checks, shrinkage = [], []
    def check(name, value):
        checks.append({'name': name, 'pass': bool(value)})
    close = lambda a, b: np.allclose(a, b, rtol=2e-10, atol=1e-8, equal_nan=True)
    for cls in [c.TweedieRegressor, c.SimpleImputer, c.StandardScaler, c.OneHotEncoder, c.ColumnTransformer, c.Pipeline]:
        cls.fit = c.forbid_fit
        if hasattr(cls, 'fit_transform'):
            cls.fit_transform = c.forbid_fit
    for item in p['frozen_sources']:
        check('Source '+item['path'], c.sha(ROOT/item['path']) == item['sha256'])
    for item in c.read(run/'manifest.json')['files']:
        check('Artifact '+item['path'], c.sha(run/item['path']) == item['sha256'])
    check('Plan/code snapshot', c.sha(run/'plan_snapshot.json') == r['plan_sha256'] and c.sha(run/'code_snapshot.py') == p['code_sha256'])
    match = re.search(r'^## Codex \| '+re.escape(p['forum_prior'])+r' \| ([^|]+) \|', (run/'forum_before_fit.md').read_text(encoding='utf-8'), re.M)
    check('Recipe precedes fit', match is not None and datetime.fromisoformat(match[1].strip()) < datetime.fromisoformat(r['started_utc']))
    events = [json.loads(x) for x in (run/'events.jsonl').read_text(encoding='utf-8').splitlines()]
    check('Exactly15fitnodes', sum(x['event'] == 'fit_started' for x in events) == sum(x['event'] == 'fit_completed' for x in events) == 15)
    source = ROOT/p['input_run']
    old = pq.read_table(source/'oof_2023.parquet').to_pandas()
    all_oof = pq.read_table(run/'oof_2023.parquet').to_pandas()
    new = pq.read_table(run/'new_oof_2023.parquet').to_pandas().sort_values(KEY).reset_index(drop=True)
    parent = old[old.model_id.eq('W2-B19')].sort_values(KEY).reset_index(drop=True)
    check('All20oldrecipes exact', all_oof[all_oof.model_id.ne(MID)].reset_index(drop=True).equals(old.sort_values(['model_id', *KEY]).reset_index(drop=True)))
    check('Catalog21unique complete', all_oof.model_id.nunique() == 21 and len(all_oof) == 21*50094 and not all_oof.duplicated(['model_id', *KEY]).any())
    check('New2023only', new.year.eq(2023).all() and len(new) == 50094 and new.group_id.nunique() == 30869 and new[KEY].equals(parent[KEY]))
    for field in parent:
        if field not in ['model_id', 'annual_rate', 'prediction', 'unit_deviance']:
            check('FrozenOOF '+field, new[field].equals(parent[field]))
    check('PositiveandC0once', new.annual_rate.gt(0).all() and np.isfinite(new.annual_rate).all() and np.array_equal(new.prediction, new.annual_rate*new['e_cost_mix_1.0']))
    check('Independentgeneraldeviance', close(new.unit_deviance, c.dev(new.T0, new.prediction)))
    trainval = c.read(run/'diagnostics/train_validation.json')
    coverage = []
    for line in ['motor', 'buildings', 'contents']:
        block = p['recipe']['features_by_line'][line]
        for fold in range(5):
            label = line+str(fold)
            f = pq.read_table(source/f'inputs_2023/{line}_fold{fold}.parquet').to_pandas()
            fit, valid = f[f.fold.ne(fold)], f[f.fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
            check('Year/graph '+label, f.year.eq(2023).all() and not f.is_test.any() and all(set(fit[z]).isdisjoint(valid[z]) for z in ['group_id', 'customer_id', 'address_id']))
            node = run/'models'/f'{line}_fold{fold}'
            b = c.joblib.load(node/'bundle.joblib')
            before = c.joblib.load(source/'models'/f'W2-B19_{line}_fold{fold}'/'bundle.joblib')
            rec = c.read(node/'receipt.json')
            tr, est = b['transformer'], b['estimator']
            check('Identical7effects '+label, b['columns'] == block['all'] == before['columns'] and len(b['columns']) == 7)
            check('Onlyparameteralpha '+label, all(est.get_params()[k] == v for k, v in p['recipe']['params'].items()) and est.alpha == 1.)
            check('Converged '+label, est.n_iter_ < 2000 and not any(n['category'] == 'ConvergenceWarning' for n in rec['warnings']))
            num = tr.named_transformers_['numeric']
            raw = fit[block['numeric']].to_numpy(float)
            med = np.array([np.nanmedian(raw[:, j]) if np.isfinite(raw[:, j]).any() else 0 for j in range(raw.shape[1])])
            filled = np.where(np.isnan(raw), med, raw)
            check('Trainingonlymedians '+label, close(num['median'].statistics_, med))
            check('Trainingonlyscales '+label, close(num['scale'].mean_, filled.mean(axis=0)) and close(num['scale'].var_, filled.var(axis=0)))
            enc = tr.named_transformers_['categorical']
            check('Trainingonlycategories '+label, all(np.array_equal(enc.categories_[j], np.sort(fit[col].unique())) for j, col in enumerate(block['categorical'])))
            check('FrozenOHE '+label, enc.drop == 'first' and enc.min_frequency == 50 and enc.max_categories == 40 and enc.handle_unknown == 'ignore')
            with c.threadpool_limits(limits=2):
                native = c.predict(b, valid)
                rates = c.predict(b, fit)
                X = tr.transform(fit[b['columns']])
                manual = manual_matrix(valid, block, tr)
            part = new[new.line.eq(line) & new.fold.eq(fold)].reset_index(drop=True)
            check('Blockedfitexactreplay '+label, np.array_equal(native, part.annual_rate.to_numpy()))
            check('Independentindicatorpredictor '+label, close(native, np.exp(manual@est.coef_+est.intercept_)))
            e = fit['e_cost_mix_1.0'].to_numpy(float)
            y, w = fit.T0.to_numpy(float)/e, np.sqrt(e)
            g = w*(rates-y)/np.sqrt(rates)/w.sum()
            gradient = np.r_[np.asarray(X.T@g).ravel()+est.alpha*est.coef_, g.sum()]
            check('PenalizedKKT '+label, np.abs(gradient).max() <= 1e-4 and close(np.abs(gradient).max(), rec['max_abs_penalized_gradient']))
            check('Originaltotalunitobjectiveidentity '+label, close(c.dev(fit.T0, e*rates), w*c.dev(y, rates)))
            check('SamelearneddesignasB19 '+label, close(tr.transform(fit[b['columns']]).toarray(), before['transformer'].transform(fit[b['columns']]).toarray()))
            def objective(beta, intercept):
                mu = np.exp(np.asarray(X@beta).ravel()+intercept)
                return float(.5*(w@c.dev(y, mu))/w.sum()+.5*est.alpha*(beta@beta))
            before_est = before['estimator']
            Jnew, Jold = objective(est.coef_, est.intercept_), objective(before_est.coef_, before_est.intercept_)
            norm_new, norm_old = float(est.coef_@est.coef_), float(before_est.coef_@before_est.coef_)
            check('PenalizedobjectiveversusB19 '+label, Jnew <= Jold+1e-5)
            check('Coefficientsnormshrink '+label, norm_new <= norm_old+1e-4)
            eps = 1e-4
            j = min(1, len(est.coef_)-1)
            plus, minus = est.coef_.copy(), est.coef_.copy()
            plus[j] += eps
            minus[j] -= eps
            finite = (objective(plus, est.intercept_)-objective(minus, est.intercept_))/(2*eps)
            check('Finitedifferencegradient '+label, abs(finite-gradient[j]) <= 2e-6)
            shrinkage.append({'line': line, 'fold': fold, 'B19_norm2': norm_old, 'B20_norm2': norm_new,
                              'B19_penalized_objective': Jold, 'B20_penalized_objective': Jnew})
            for role, ff, rr in [('fit', fit, rates), ('validation', valid, native)]:
                record = next(x for x in trainval if x['line'] == line and x['fold'] == fold and x['role'] == role)
                check('Train/OOF '+label+role, close(record['D2'], c.d2_tweedie_score(ff.T0, ff['e_cost_mix_1.0']*rr, power=1.5)))
            if fold == 0:
                field = 'x_cover_type' if line == 'motor' else 'x_accidental_damage_cover'
                meta = f[KEY].copy()
                meta['coverage'] = f[field].astype(str) if line == 'motor' else np.where(f[field].eq(1), 'AD_yes', 'AD_no')
                coverage.append(meta)
    meta = pd.concat(coverage, ignore_index=True)
    for row in r['summary']:
        f = all_oof[all_oof.model_id.eq(row['model_id'])]
        check('GlobalD2 '+row['model_id'], close(row['D2'], c.d2_tweedie_score(f.T0, f.prediction, power=1.5)))
        check('Globaltotals '+row['model_id'], close([row['observed_total'], row['predicted_total'], row['conditional_nominal_2023']], [f.T0.sum(), f.prediction.sum(), (f.exposure*f.annual_rate).sum()]))
    cells = {mid: all_oof[all_oof.model_id.eq(mid)].merge(meta, on=KEY, validate='one_to_one') for mid in [MID, 'W2-B19', 'W2-B14', 'W2-B00']}
    for row in c.read(run/'diagnostics/segments.json'):
        f = cells[row['model_id']]
        business = np.where(f.x_new_business.eq(1), 'new_business', 'renewal')
        labels = {'line': f.line.astype(str), 'fold': f.fold.astype(str), 'business': business,
                  'line_business': f.line.astype(str)+'_'+business, 'line_coverage': f.line.astype(str)+'_'+f.coverage,
                  'line_business_coverage': f.line.astype(str)+'_'+business+'_'+f.coverage}[row['dimension']]
        f = f[np.asarray(labels) == row['label']]
        check('Segment '+row['model_id']+row['dimension']+row['label'], len(f) == row['rows'] and close(row['D2'], c.d2_tweedie_score(f.T0, f.prediction, power=1.5)) and close(row['predicted_total'], f.prediction.sum()))
    ids = [MID, 'W2-B19', 'W2-B14', 'W2-B00']
    parts = {mid: all_oof[all_oof.model_id.eq(mid)].sort_values(KEY).reset_index(drop=True) for mid in ids}
    first = parts[MID]
    groups, codes = np.unique(first.group_id, return_inverse=True)
    G = len(groups)
    n, sy, sr = np.bincount(codes), np.bincount(codes, weights=first.T0), np.bincount(codes, weights=np.sqrt(first.T0))
    losses = np.column_stack([np.bincount(codes, weights=c.dev(parts[mid].T0, parts[mid].prediction), minlength=G) for mid in ids])
    cfg = p['bootstrap']
    rng, digest = np.random.default_rng(cfg['seed']), hashlib.sha256()
    values = {mid: [] for mid in ids[1:]}
    with c.threadpool_limits(limits=2):
        for start in range(0, cfg['replicates'], 32):
            draw = rng.integers(0, G, size=(min(32, cfg['replicates']-start), G), dtype=np.int64)
            digest.update(draw.tobytes())
            count = np.stack([np.bincount(row, minlength=G) for row in draw])
            N, Y, R = count@n, count@sy, count@sr
            mu = Y/N
            null = 4*(Y/np.sqrt(mu)+N*np.sqrt(mu)-2*R)
            sampled = count@losses
            for j, ref in enumerate(ids[1:], 1):
                values[ref].extend(((sampled[:, j]-sampled[:, 0])/null).tolist())
    diagnostic = c.read(run/'diagnostics/new_pairs.json')
    boot = pq.read_table(run/'diagnostics/bootstrap_new_pairs.parquet').to_pandas()
    check('Only3newpairs2000draws', len(boot) == 6000 and len(diagnostic['pairs']) == 3 and cfg['replicates'] == 2000 and cfg['seed'] == 2026102302)
    check('Samebootstrapstream', digest.hexdigest() == diagnostic['draws_sha256'])
    for j, ref in enumerate(ids[1:], 1):
        row = next(x for x in diagnostic['pairs'] if x['reference'] == ref)
        dist = np.asarray(values[ref])
        saved = boot[boot.reference.eq(ref)].sort_values('replicate').delta_D2
        check('Multiplicitybootstrap '+ref, np.allclose(saved, dist, rtol=2e-8, atol=2e-11))
        check('Bootstrapinterval '+ref, np.allclose([row['exploratory_lower95'], row['exploratory_upper95']], np.quantile(dist, [.025, .975]), rtol=2e-8, atol=2e-11))
        advantage = losses[:, j]-losses[:, 0]
        keep = np.ones(G, dtype=bool)
        keep[np.argsort(-advantage, kind='stable')[:31]] = False
        den = 8*(np.sqrt(n.sum()*sy.sum())-sr.sum())
        reduced = 8*(np.sqrt(n[keep].sum()*sy[keep].sum())-sr[keep].sum())
        check('Pointandinfluence '+ref, close(row['delta_D2'], advantage.sum()/den) and row['removed_favorable_groups'] == 31 and close(row['delta_after_removal'], advantage[keep].sum()/reduced))
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
              'checker_sha256': c.sha(Path(__file__)), 'passed': sum(x['pass'] for x in checks),
              'failed': sum(not x['pass'] for x in checks), 'checks': checks, 'shrinkage': shrinkage,
              'fit_calls': 0, 'professional_independent_validation': False,
              'scope': 'Separate checker with fits blocked; generaldeviance, sklearn, manual indicators, KKT/finite differences, objective/shrinkage, paired multiplicity bootstrap;2023only.'}
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'failed': result['failed'], 'failures': [x for x in checks if not x['pass']]}))
    return 1 if result['failed'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
