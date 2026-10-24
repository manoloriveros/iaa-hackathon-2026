"""Prepara exposición, T0 observado y particiones de emerging; no ajusta modelos."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import platform
import sys
import uuid

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO.parents[1]
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

LINES = ('motor', 'buildings', 'contents')
KEY = ['market', 'line', 'row_id']
MONEY = ('paid', 'incurred', 'recoveries', 'reserve', 'T0')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2,
        default=lambda x: x.item() if hasattr(x, 'item') else str(x)) + '\n', encoding='utf-8')


def require(ok, message: str) -> None:
    if not bool(ok):
        raise ValueError(message)


def cents(series: pd.Series) -> np.ndarray:
    values = pd.to_numeric(series, errors='raise').to_numpy(dtype=float)
    require(np.isfinite(values).all(), 'Importe no finito')
    rounded = np.rint(values * 100)
    require(np.max(np.abs(values * 100 - rounded), initial=0) < 1e-5, 'Importe no expresado en centavos')
    return rounded.astype('int64')


def reconcile_exposure(frame: pd.DataFrame) -> pd.DataFrame:
    f = frame.copy()
    f['period_start'] = pd.to_datetime(f.period_start, errors='raise')
    f['period_end'] = pd.to_datetime(f.period_end, errors='raise')
    require(f[['period_start', 'period_end']].notna().all().all(), 'Fecha ausente')
    days = (f.period_end - f.period_start).dt.days + 1
    require(days.between(1, 366).all(), 'Duración fuera del contrato anual')
    raw = pd.to_numeric(f.exposure, errors='raise')
    require(np.isfinite(raw).all() and raw.gt(0).all(), 'Exposición original inválida')
    expected = (days / 365).round(4)
    changed = ~np.isclose(raw, expected, atol=1e-7, rtol=0)
    day_unit = changed & np.isclose(raw, days, atol=1e-7, rtol=0)
    basis360 = changed & np.isclose(raw, (days / 360).round(4), atol=1e-7, rtol=0)
    require((~changed | day_unit | basis360).all(), 'Discrepancia de exposición sin explicar')
    f['exposure_original'] = raw
    f['covered_days'] = days.astype('int32')
    f['exposure'] = expected
    f['audit_exposure_rule'] = np.select([day_unit, basis360], ['days_stored_as_years', 'basis_360'], default='unchanged')
    f['audit_exposure_delta'] = f.exposure - f.exposure_original
    return f


def assign_claims(claims: pd.DataFrame, periods: pd.DataFrame) -> pd.DataFrame:
    c = claims.copy().reset_index(drop=True)
    require(not c.duplicated(['market', 'claim_id']).any(), 'ID de siniestro duplicado')
    require(c.status.isin(['closed', 'open', 'repudiated']).all(), 'Estado desconocido')
    require(not periods.duplicated(KEY).any(), 'ID de periodo duplicado')
    c['loss_date'] = pd.to_datetime(c.loss_date, errors='raise')
    c['report_date'] = pd.to_datetime(c.report_date, errors='raise')
    require(c[['loss_date', 'report_date']].notna().all().all(), 'Fecha de siniestro ausente')
    require(c.report_date.ge(c.loss_date).all(), 'Reporte anterior a ocurrencia')
    c['_claim_position'] = np.arange(len(c))
    policy_key = ['market', 'line', 'policy_id']
    j = c[['_claim_position', *policy_key, 'loss_date']].merge(
        periods[[*KEY, 'policy_id', 'period_start', 'period_end']], on=policy_key, how='left')
    matches = j.loc[j.loss_date.ge(j.period_start) & j.loss_date.le(j.period_end)]
    counts = matches.groupby('_claim_position').size()
    require(counts.le(1).all(), 'Asignación ambigua de siniestros')
    mapping = matches.set_index('_claim_position').row_id
    c['row_id'] = c._claim_position.map(mapping)
    bounds = periods.groupby(policy_key).agg(first_start=('period_start', 'min'), last_end=('period_end', 'max'))
    c = c.merge(bounds, on=policy_key, how='left', validate='many_to_one')
    require(c.first_start.notna().all(), 'Póliza o ramo sin referencia')
    c['audit_precoverage'] = c.row_id.isna() & c.loss_date.lt(c.first_start)
    require((c.row_id.notna() | c.audit_precoverage).all(), 'Siniestro fuera de periodo sin explicación')
    c['audit_assignment'] = np.where(c.audit_precoverage, 'before_first_available_coverage', 'unique_period')
    c['included_in_T0'] = c.row_id.notna() & c.status.ne('repudiated')
    c['paid_cents'] = cents(c.paid_to_date)
    c['incurred_cents'] = cents(c.incurred_to_date)
    c['recoveries_cents'] = cents(c.recoveries)
    c['reserve_cents'] = c.incurred_cents - c.paid_cents
    c['T0_cents'] = c.incurred_cents - c.recoveries_cents
    require(c[['paid_cents', 'recoveries_cents', 'reserve_cents', 'T0_cents']].ge(0).all().all(), 'Importe negativo fuera del contrato observado')
    return c.drop(columns='_claim_position')


def make_targets(periods: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    a = audit.loc[audit.included_in_T0].copy()
    a['n_accepted'] = 1
    a['n_positive'] = a.T0_cents.gt(0).astype('int64')
    a['n_open'] = a.status.eq('open').astype('int64')
    value_cols = [x + '_cents' for x in MONEY] + ['n_accepted', 'n_positive', 'n_open']
    grouped = a.groupby(KEY)[value_cols].sum().reset_index()
    t = periods[[*KEY, 'policy_id', 'customer_id', 'address_id', 'year', 'is_test', 'exposure']].merge(grouped, on=KEY, how='left', validate='one_to_one')
    labelled = ~t.is_test
    for col in value_cols:
        t[col] = t[col].where(~labelled, t[col].fillna(0)).astype('Int64')
        require(t.loc[~labelled, col].isna().all(), 'Etiqueta hallada en test')
    for col in MONEY:
        t[col] = t[col + '_cents'].astype('Float64') / 100
    t['T1_reserve075'] = (4 * t.T0_cents - t.reserve_cents).astype('Float64') / 400
    t['T1_reserve125'] = (4 * t.T0_cents + t.reserve_cents).astype('Float64') / 400
    t['target_status'] = np.where(labelled, 'observed_net_incurred_not_ultimate', 'unlabelled_test')
    t['valuation_date'] = pd.Timestamp('2024-12-31')
    return t


def make_partitions(periods: pd.DataFrame, seed: str, folds: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    training = periods.loc[~periods.is_test].copy()
    parent = {}

    def find(x):
        if x not in parent:
            parent[x] = x
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        a, b = find(x), find(y)
        if a != b:
            parent[max(a, b)] = min(a, b)

    cnodes = training.market + '|customer|' + training.customer_id
    anodes = training.market + '|address|' + training.address_id
    for c, a in zip(cnodes, anodes):
        union(c, a)
    nodes = sorted(parent)
    components = {node: hashlib.sha256(find(node).encode()).hexdigest() for node in nodes}
    memberships = pd.DataFrame({'node': nodes, 'group_id': [components[x] for x in nodes]})
    groups = cnodes.map(components)
    unique = groups.unique()
    buckets = {g: int.from_bytes(hashlib.sha256((seed + '|' + g).encode()).digest()[:8], 'big') % folds for g in unique}
    p = periods[[*KEY, 'policy_id', 'customer_id', 'address_id', 'period_start', 'period_end', 'year', 'is_test']].copy()
    p['group_id'] = pd.Series(pd.NA, index=p.index, dtype='string')
    p.loc[training.index, 'group_id'] = groups.values
    p['fold'] = p.group_id.map(buckets).astype('Int64')
    p['temporal_role'] = np.select([p.year.eq(2023), p.year.eq(2024)], ['development_2023', 'temporal_validation_2024'], default='unlabelled_test_2025')
    p['customer_seen_prior_year_any_line'] = False
    p['address_seen_prior_year_any_line'] = False
    p['customer_seen_prior_year_same_line'] = False
    p['address_seen_prior_year_same_line'] = False
    for year in [2023, 2024, 2025]:
        prior = training.loc[training.year.lt(year)]
        mask = p.year.eq(year)
        for entity in ['customer', 'address']:
            col = entity + '_id'
            p.loc[mask, entity + '_seen_prior_year_any_line'] = p.loc[mask, col].isin(prior[col])
            for line in LINES:
                line_mask = mask & p.line.eq(line)
                p.loc[line_mask, entity + '_seen_prior_year_same_line'] = p.loc[line_mask, col].isin(prior.loc[prior.line.eq(line), col])
    require(p.loc[p.is_test, ['group_id', 'fold']].isna().all().all(), 'Test usado en grupos de desarrollo')
    return p, memberships


def materialize() -> Path:
    plan_path = REPO / 'registro/semana2_preparacion_plan.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    source_manifest = ROOT / plan['input_manifest_workspace_relative']
    manifest = json.loads(source_manifest.read_text(encoding='utf-8'))
    week = ROOT / 'Hackaton/Semana 2'
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8]
    out = REPO / 'privado/semana2/preparacion' / ('base_' + run_id)
    out.mkdir(parents=True, exist_ok=False)
    source_inputs = {x['local_path']: x['sha256'] for x in manifest['files']}
    report = {'id': plan['id'], 'author': 'Codex', 'run': out.relative_to(ROOT).as_posix(),
        'started_utc': datetime.now(timezone.utc).isoformat(), 'training': False, 'inference': False,
        'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__, 'pyarrow': pa.__version__},
        'checks': [], 'input_sha256': source_inputs, 'plan_sha256': sha(plan_path), 'code_sha256': sha(Path(__file__))}
    (out / 'code_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (out / 'plan_snapshot.json').write_bytes(plan_path.read_bytes())

    def check(name, ok, detail=None):
        report['checks'].append({'name': name, 'pass': bool(ok), 'detail': detail})
        require(ok, name)

    try:
        check('Input hashes before', all(sha(week / p) == h for p, h in source_inputs.items()))
        periods = []
        exposure_counts = []
        for line in LINES:
            for kind in ['policies', 'test']:
                f = pq.read_table(week / 'Datos/emerging' / f'{kind}_{line}.parquet').to_pandas()
                for key in ['row_id', 'policy_id', 'customer_id', 'address_id']:
                    require(f[key].notna().all() and f[key].map(lambda x: isinstance(x, str) and bool(x)).all(), f'Clave inválida {key}')
                f['market'] = 'emerging'; f['line'] = line; f['is_test'] = kind == 'test'
                f = reconcile_exposure(f)
                f['year'] = f.period_start.dt.year
                check(f'Period years {kind} {line}', f.year.isin([2025] if kind == 'test' else [2023, 2024]).all() and f.period_end.dt.year.eq(f.year).all())
                h = f.sort_values(['policy_id', 'period_start'])
                prev = h.groupby('policy_id').period_end.shift()
                check(f'No overlapping periods {kind} {line}', not prev.ge(h.period_start).any())
                exposure_counts.append({'line': line, 'set': kind, 'rows': len(f),
                    'changes': int(f.audit_exposure_rule.ne('unchanged').sum()),
                    'days_unit': int(f.audit_exposure_rule.eq('days_stored_as_years').sum()),
                    'basis360': int(f.audit_exposure_rule.eq('basis_360').sum()),
                    'before': float(f.exposure_original.sum()), 'after': float(f.exposure.sum())})
                f.to_parquet(out / f'periods_{kind}_{line}.parquet', index=False)
                periods.append(f)
        periods = pd.concat(periods, ignore_index=True)
        train = periods.loc[~periods.is_test].copy()
        test = periods.loc[periods.is_test].copy()
        check('Unique period keys', not periods.duplicated(KEY).any())
        check('Expected row counts', len(train) == 109296 and len(test) == 209063)
        tr = [x for x in exposure_counts if x['set'] == 'policies']
        check('609 explained train exposure changes', sum(x['changes'] for x in tr) == plan['exposure']['expected_train_changes'])
        check('114 days and 495 basis360', sum(x['days_unit'] for x in tr) == 114 and sum(x['basis360'] for x in tr) == 495)
        check('No test exposure change', sum(x['changes'] for x in exposure_counts if x['set'] == 'test') == 0)
        report['exposure'] = exposure_counts
        periods.loc[periods.audit_exposure_rule.ne('unchanged'), [*KEY, 'period_start', 'period_end', 'covered_days', 'exposure_original', 'exposure', 'audit_exposure_rule', 'audit_exposure_delta']].to_parquet(out / 'exposure_changes_609.parquet', index=False)

        claims = pq.read_table(week / 'Datos/emerging/claims.parquet').to_pandas()
        claims['market'] = 'emerging'
        audit = assign_claims(claims, train)
        check('All reports within valuation', audit.report_date.le(pd.Timestamp(plan['valuation_date'])).all())
        check('36 precoverage only', int(audit.audit_precoverage.sum()) == 36 and int(audit.row_id.isna().sum()) == 36)
        check('All 9258 claims retained in audit', len(audit) == 9258)
        check('All 120 declined excluded', int(audit.status.eq('repudiated').sum()) == 120 and not audit.loc[audit.status.eq('repudiated'), 'included_in_T0'].any())
        target = make_targets(periods, audit)
        check('Complete label contract', target.loc[~target.is_test, 'T0'].notna().all() and target.loc[target.is_test, 'T0'].isna().all())
        check('T0 nonnegative and 9102 accepted allocated', target.loc[~target.is_test, 'T0'].ge(0).all() and int(target.n_accepted.sum()) == 9102)
        accepted = audit.loc[audit.status.ne('repudiated')]
        assigned = audit.loc[audit.included_in_T0]
        pre = audit.loc[audit.audit_precoverage & audit.status.ne('repudiated')]
        report['money_reconciliation_cents'] = {}
        for money in MONEY:
            col = money + '_cents'
            raw_sum, assigned_sum, pre_sum = (int(g[col].sum()) for g in [accepted, assigned, pre])
            row_sum = int(target[col].sum())
            check('Cents reconcile ' + money, raw_sum == assigned_sum + pre_sum and assigned_sum == row_sum)
            report['money_reconciliation_cents'][money] = {'accepted_raw': raw_sum, 'assigned': assigned_sum, 'excluded_precoverage': pre_sum, 'row_target': row_sum}
        report['claims'] = {'raw': len(audit), 'precoverage': len(pre), 'assigned_including_declined': int(audit.row_id.notna().sum()), 'accepted_assigned': len(assigned), 'declined': int(audit.status.eq('repudiated').sum()), 'open_assigned': int(assigned.status.eq('open').sum()), 'positive_assigned': int(assigned.T0_cents.gt(0).sum())}
        audit.to_parquet(out / 'claim_assignment_audit.parquet', index=False)
        audit.loc[audit.audit_precoverage].to_parquet(out / 'precoverage_claims_36.parquet', index=False)
        target.to_parquet(out / 'target_T0_and_stresses.parquet', index=False)

        part, memberships = make_partitions(periods, plan['validation']['seed'], plan['validation']['folds'])
        labelled = part.loc[~part.is_test]
        check('Every group has one fold', labelled.groupby('group_id').fold.nunique().eq(1).all())
        for entity in ['customer_id', 'address_id']:
            check(entity + ' stays in group', labelled.groupby(['market', entity]).group_id.nunique().eq(1).all())
        part.to_parquet(out / 'partitions.parquet', index=False)
        memberships.to_parquet(out / 'group_membership_training_only.parquet', index=False)
        split_dir = out / 'splits'; split_dir.mkdir()
        split_summaries = []

        def save_split(name, fit_mask, eval_mask, group_disjoint):
            a, b = part.loc[fit_mask].copy(), part.loc[eval_mask].copy()
            check(name + ' nonempty disjoint keys', len(a) > 0 and len(b) > 0 and set(a.row_id).isdisjoint(b.row_id))
            if group_disjoint:
                for entity in ['customer_id', 'address_id', 'group_id']:
                    check(name + ' no overlap ' + entity, set(a[entity]).isdisjoint(b[entity]))
            a['role'] = 'train'; b['role'] = 'validation'
            s = pd.concat([a, b], ignore_index=True)
            s[[*KEY, 'group_id', 'fold', 'year', 'role']].to_parquet(split_dir / (name + '.parquet'), index=False)
            counts = s.groupby(['line', 'year', 'role']).size().reset_index(name='rows').to_dict('records')
            split_summaries.append({'name': name, 'train_rows': len(a), 'validation_rows': len(b), 'group_disjoint': group_disjoint, 'counts': counts})

        save_split('temporal_2024', part.year.eq(2023), part.year.eq(2024), False)
        for fold in range(plan['validation']['folds']):
            save_split(f'development_2023_fold{fold}', part.year.eq(2023) & part.fold.ne(fold).fillna(False), part.year.eq(2023) & part.fold.eq(fold).fillna(False), True)
            save_split(f'cold_2024_fold{fold}', part.year.eq(2023) & part.fold.ne(fold).fillna(False), part.year.eq(2024) & part.fold.eq(fold).fillna(False), True)
        production = part[[*KEY, 'year', 'group_id', 'fold']].copy()
        production['role'] = np.where(part.is_test, 'test_predict', 'train')
        production.to_parquet(split_dir / 'production_2025.parquet', index=False)
        balance = labelled.merge(target[[*KEY, 'T0_cents', 'n_accepted']], on=KEY, validate='one_to_one')
        rows = []
        for key, g in balance.groupby(['line', 'year', 'fold']):
            rows.append({'line': key[0], 'year': int(key[1]), 'fold': int(key[2]), 'rows': len(g), 'positive_rows': int(g.T0_cents.gt(0).sum()), 'accepted_claims': int(g.n_accepted.sum()), 'T0_cents': int(g.T0_cents.sum())})
        check('Every fold/line/year has positive cases', len(rows) == 30 and all(x['positive_rows'] > 0 for x in rows))
        report['fold_balance'] = rows
        report['splits'] = split_summaries
        report['groups'] = {'components': int(labelled.group_id.nunique()), 'largest_component_rows': int(labelled.groupby('group_id').size().max()), 'membership_nodes': len(memberships), 'test_edges_used': 0}
        report['targets_by_line_year'] = [{**{'line': k[0], 'year': int(k[1]), 'rows': len(g)}, **{m: int(g[m + '_cents'].sum()) for m in MONEY}, 'n_accepted': int(g.n_accepted.sum()), 'n_open': int(g.n_open.sum()), 'positive_rows': int(g.T0_cents.gt(0).sum()), 'exposure': float(g.exposure.sum())} for k, g in target.loc[~target.is_test].groupby(['line', 'year'])]
        report['new_business_diagnostics'] = [{'line': k[0], 'year': int(k[1]), 'rows': len(g), 'new_customer_same_line_share': float((~g.customer_seen_prior_year_same_line).mean()), 'new_address_any_line_share': float((~g.address_seen_prior_year_any_line).mean())} for k, g in part.groupby(['line', 'year'])]
        sample = pq.read_table(week / 'Datos/emerging/sample_submission.parquet', columns=['row_id']).column('row_id').to_pylist()
        check('Sample covers all test keys', len(sample) == len(test) == len(set(sample)) and set(sample) == set(test.row_id))
        check('No negative stress label', target.loc[~target.is_test, 'T1_reserve075'].ge(0).all())
        check('Input hashes after', all(sha(week / p) == h for p, h in source_inputs.items()))
        check('Code and plan stable', sha(plan_path) == report['plan_sha256'] and sha(Path(__file__)) == report['code_sha256'])
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        report['status'] = 'prepared_T0_and_partitions_not_ultimate_model'
        report['limitations'] = ['T0 is observed incurred, not ultimate truth.', 'No reporting completion or reserve sufficiency estimated.', '2023 and 2024 share valuation 2024-12-31; covariate snapshots unavailable.', 'No model trained, calibrated or scored.', '2025 weather, circular premium/service variables are not approved predictors.']
        dump(out / 'report.json', report)
        files = [{'path': x.relative_to(out).as_posix(), 'sha256': sha(x), 'bytes': x.stat().st_size} for x in sorted(out.rglob('*')) if x.is_file()]
        dump(out / 'manifest.json', {'run': report['run'], 'files': files, 'input_sha256': source_inputs})
        print(json.dumps({'run': report['run'], 'checks': len(report['checks']), 'claims': report['claims'], 'exposure': report['exposure'], 'money_cents': report['money_reconciliation_cents'], 'groups': report['groups']}, ensure_ascii=True))
        return out
    except Exception as exc:
        report['status'] = 'failed_not_promoted'; report['error'] = str(exc)
        dump(out / 'failed.json', report)
        raise


if __name__ == '__main__':
    materialize()
