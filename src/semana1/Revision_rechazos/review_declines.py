"""REN00: revisa rechazos con sucesor, conserva todos los datos y las fechas pendientes."""
from pathlib import Path
from datetime import datetime, timezone
import json
import shutil
import sys
import uuid

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'Hackaton/Semana 1/Limpieza'))
import clean_data as c
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

LINES = ['motor', 'buildings', 'contents']
REQUEST = ('Dejemos las fechas pendientes y revisemos las 2.742 pólizas rechazadas que continúan en 2025. '
           'Compara sus historiales y siniestros, muestra casos concretos y propón cómo tratarlas '
           'sin modificar los datos todavía.')
D43 = ROOT / 'Hackaton/Semana 1/Revision_calendario/runs/calendar_20261016T201406Z_01c55c49'


def rec(f):
    return json.loads(f.to_json(orient='records', date_format='iso'))


def save(f, out, name, csv=True):
    f.to_parquet(out / 'tables' / (name + '.parquet'), index=False)
    if csv:
        f.to_csv(out / 'tables' / (name + '.csv'), index=False)


def main():
    active = ROOT / 'Hackaton/Semana 1/Limpieza/current_dataset.json'
    pointer = json.loads(active.read_text('utf-8'))
    catpath = ROOT / pointer['catalog_workspace_relative']
    cat = json.loads(catpath.read_text('utf-8'))
    parent = ROOT / pointer['workspace_relative_run']
    for directory in [parent, D43]:
        manifest = json.loads((directory / 'manifest.json').read_text('utf-8'))
        assert all(c.digest(directory / e['path']) == e['sha256'] for e in manifest['files'])
    out = BASE / 'runs' / (datetime.now(timezone.utc).strftime('renewals_%Y%m%dT%H%M%SZ_') + uuid.uuid4().hex[:8])
    for name in ['tables', 'evidence', 'source_snapshot', 'figures']:
        (out / name).mkdir(parents=True, exist_ok=False)
    for name in ['review_declines.py', 'render_declines.py', 'verify_declines.py', 'verify_report.js', 'record_declines.py']:
        shutil.copy2(BASE / name, out / 'source_snapshot' / name)
    shutil.copy2(Path(c.__file__), out / 'source_snapshot/clean_data.py')
    protected = {p.relative_to(ROOT).as_posix(): c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']: c.digest(ROOT / e['workspace_relative_path']) for e in cat.values()})
    for p in [active, catpath, parent / 'manifest.json', D43 / 'manifest.json', D43 / 'tables/gap_cohort.parquet']:
        protected[p.relative_to(ROOT).as_posix()] = c.digest(p)
    assert all(c.digest(ROOT / e['workspace_relative_path']) == e['sha256'] for e in cat.values())
    c.dump(out / 'protected_hashes_before.json', protected)
    sources = {'active_index.json': active, 'dataset_catalog.json': catpath, 'D42_manifest.json': parent / 'manifest.json',
        'D43_manifest.json': D43 / 'manifest.json', 'D43_frozen_gaps.parquet': D43 / 'tables/gap_cohort.parquet',
        'D42_claim_assignment.parquet': parent / 'tables/claim_period_assignment.parquet',
        'official_data_description.md': ROOT / 'Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md',
        'IAA_priorities.md': ROOT / 'Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md',
        'methodological_protocol_1_3.json': ROOT / 'Hackaton/Semana 1/Modelado/protocolo_metodologico.json'}
    for name, p in sources.items():
        shutil.copy2(p, out / 'evidence' / name)
    for name in ['MEMORIA_PROYECTO.md', 'ESTADO_PROYECTO.json', 'DECISIONES.md']:
        shutil.copy2(ROOT / 'Preparación' / name, out / 'evidence' / ('before_' + name))
    c.dump(out / 'request.json', {'request': REQUEST, 'data_changes_authorized': False, 'calendar_dates_remain_pending': True,
        'purpose': 'Descriptive audit of longitudinal decision semantics and treatment proposal; no model selection.',
        'ai_role': 'Codex reconstructs histories, compares hypotheses and proposes treatment.',
        'external_ai_provider_used': False, 'independent_validation': False})
    frozen = pd.read_parquet(out / 'evidence/D43_frozen_gaps.parquet')
    cohort = frozen.loc[frozen.previous_renewal_decision.eq('declined_by_insurer')].copy()
    assert len(cohort) == 2742 and cohort.policy_id.nunique() == 2742
    ids = set(cohort.policy_id)
    save(cohort, out, 'frozen_cohort')
    common = ['row_id', 'policy_id', 'customer_id', 'address_id', 'period_start', 'period_end', 'exposure',
              'renewal_count', 'new_business', 'written_premium', 'voluntary_excess', 'compulsory_excess']
    frames = []
    for line in LINES:
        for prefix in ['policies', 'test']:
            name = prefix + '_' + line
            fields = common + (['renewal_decision'] if prefix == 'policies' else [])
            f = pq.read_table(ROOT / cat[name]['workspace_relative_path'], columns=fields).to_pandas()
            f['line'], f['source_table'] = line, name
            for col in ['period_start', 'period_end']:
                f[col] = pd.to_datetime(f[col])
            f['year'] = f.period_start.dt.year
            frames.append(f)
    f = pd.concat(frames, ignore_index=True).sort_values(['line', 'policy_id', 'period_start', 'period_end', 'row_id']).reset_index(drop=True)
    f['covered_days'] = (f.period_end - f.period_start).dt.days + 1
    groups = f.groupby(['line', 'policy_id'], sort=False)
    for col in ['row_id', 'period_start', 'year', 'customer_id', 'address_id', 'renewal_count', 'new_business', 'renewal_decision']:
        f['next_' + col] = groups[col].shift(-1)
    f['has_successor'] = f.next_row_id.notna()
    f['successor_next_year'] = f.next_year.eq(f.year + 1)
    f['successor_same_year'] = f.next_year.eq(f.year)
    f['gap_to_successor_days'] = (f.next_period_start - f.period_end).dt.days - 1
    all_declined = f.loc[f.renewal_decision.eq('declined_by_insurer')].copy()
    # Source-driven reconstruction is compared to, not substituted for, the frozen D43 list.
    independent = all_declined.loc[all_declined.year.eq(2024) & all_declined.next_year.eq(2025)]
    assert set(zip(independent.row_id, independent.next_row_id)) == set(zip(cohort.previous_row_id, cohort.row_id))
    annual_decisions = f.loc[f.year.le(2024)].groupby(['line', 'year', 'renewal_decision'], dropna=False).agg(
        rows=('row_id', 'size'), policies=('policy_id', 'nunique'), successors=('has_successor', 'sum'),
        next_year=('successor_next_year', 'sum'), same_year=('successor_same_year', 'sum')).reset_index()
    annual_decisions['no_observed_successor'] = annual_decisions.rows - annual_decisions.successors
    annual_decisions['successor_pct'] = annual_decisions.successors / annual_decisions.rows * 100
    save(annual_decisions, out, 'decision_successors_all_years')
    save(all_declined, out, 'all_declined_periods')
    transitions = all_declined.groupby(['line', 'year', 'next_year', 'next_renewal_decision'], dropna=False).size().reset_index(name='rows')
    save(transitions, out, 'declined_successor_decisions')

    claims = pq.read_table(ROOT / cat['claims']['workspace_relative_path']).to_pandas()
    for col in ['loss_date', 'report_date']:
        claims[col] = pd.to_datetime(claims[col])
    assignment = pd.read_parquet(out / 'evidence/D42_claim_assignment.parquet')
    claims = claims.merge(assignment[['claim_id', 'row_id', 'assignment_status']], on='claim_id', how='left', validate='one_to_one')
    claims['accepted'] = claims.status.isin(['closed', 'open'])
    claims['loss_year'] = claims.loss_date.dt.year
    # Sum monetary components in integer cents, never compare a rounded total to a binary float sum.
    for col in ['paid_to_date', 'incurred_to_date', 'recoveries']:
        raw = claims[col].to_numpy() * 100
        assert np.allclose(raw, np.rint(raw), rtol=0, atol=1e-4)
        claims[col + '_cents'] = np.rint(raw).astype('int64')
    claims['net_accepted_cents'] = np.where(claims.accepted,
        claims.incurred_to_date_cents - claims.recoveries_cents, 0).astype('int64')
    claims['observed_net_CU'] = claims.net_accepted_cents / 100
    claims['open_case_reserve_cents'] = np.where(claims.status.eq('open'),
        claims.incurred_to_date_cents - claims.paid_to_date_cents, 0).astype('int64')
    stats = claims.loc[claims.row_id.notna()].groupby('row_id').agg(
        observed_claim_records=('claim_id', 'size'), accepted_claims=('accepted', 'sum'),
        net_accepted_cents=('net_accepted_cents', 'sum'), open_case_reserve_cents=('open_case_reserve_cents', 'sum'),
        max_claim_net_cents=('net_accepted_cents', 'max'))
    f = f.merge(stats, left_on='row_id', right_index=True, how='left', validate='one_to_one')
    for col in stats.columns:
        f[col] = f[col].fillna(0).astype('Int64')
        f.loc[f.year.eq(2025), col] = pd.NA
    f['claim_observation_available'] = f.year.le(2024)
    # Claim diagnostics for 2025 are missing, never zero targets.
    scope = f.loc[f.row_id.isin(cohort.previous_row_id)].copy()
    save(scope, out, 'cohort_preceding_2024_periods')
    history = f.loc[f.policy_id.isin(ids)].copy()
    full_2024 = f.loc[f.year.eq(2024)]
    cohort_2024 = history.loc[history.year.eq(2024)]
    cohort_claims = claims.loc[claims.policy_id.isin(ids)].copy()
    year2024_claims = cohort_claims.loc[cohort_claims.loss_year.eq(2024)]
    old_claims = cohort_claims.loc[cohort_claims.row_id.isin(cohort.previous_row_id)]
    save(cohort_claims, out, 'cohort_claim_histories')
    # Full schemas for every cohort policy; extra controls are selected below.
    risk_fields = {'motor': ['driver_age', 'vehicle_age', 'make_model', 'vehicle_value_group', 'cover_type', 'annual_mileage',
        'overnight_parking', 'vehicle_use', 'telematics_opt_in', 'telematics_score'],
        'buildings': ['policyholder_age', 'sum_insured', 'construction_type', 'occupancy', 'days_unoccupied', 'smoke_alarms', 'accidental_damage_cover'],
        'contents': ['policyholder_age', 'sum_insured', 'tenure', 'security_level', 'high_value_items', 'accidental_damage_cover', 'works_from_home']}
    wide = []
    for line in LINES:
        for prefix in ['policies', 'test']:
            name = prefix + '_' + line
            cols = common + risk_fields[line] + (['renewal_decision'] if prefix == 'policies' else [])
            x = pq.read_table(ROOT / cat[name]['workspace_relative_path'], columns=cols).to_pandas()
            x = x.loc[x.policy_id.isin(ids)].copy()
            x['line'], x['source_table'] = line, name
            wide.append(x)
    risk_history = pd.concat(wide, ignore_index=True)
    for col in ['period_start', 'period_end']:
        risk_history[col] = pd.to_datetime(risk_history[col])
    extra_cols = [col for col in risk_history if col not in history or col == 'row_id']
    history = history.merge(risk_history[extra_cols], on='row_id', how='left', validate='one_to_one')
    save(history, out, 'cohort_policy_histories')
    before = risk_history.set_index('row_id').loc[cohort.previous_row_id].reset_index()
    after = risk_history.set_index('row_id').loc[cohort.row_id].reset_index()
    field_comparisons = []
    for line in LINES:
        mask = cohort.line.eq(line).to_numpy()
        for field in ['customer_id', 'address_id', 'voluntary_excess', 'compulsory_excess', 'exposure', 'written_premium'] + risk_fields[line]:
            a, b = before.loc[mask, field], after.loc[mask, field]
            both = a.notna() & b.notna()
            field_comparisons.append({'line': line, 'field': field, 'policies': int(mask.sum()),
                'both_observed': int(both.sum()), 'same_when_observed': int((a.eq(b) & both).sum()),
                'different_when_observed': int((a.ne(b) & both).sum()), 'both_missing': int((a.isna() & b.isna()).sum()),
                'missing_to_observed': int((a.isna() & b.notna()).sum()), 'observed_to_missing': int((a.notna() & b.isna()).sum())})
    save(pd.DataFrame(field_comparisons), out, 'endpoint_field_comparison')
    profile = []
    for line in LINES + ['ALL']:
        cc = cohort if line == 'ALL' else cohort.loc[cohort.line.eq(line)]
        pp = scope if line == 'ALL' else scope.loc[scope.line.eq(line)]
        hh = history if line == 'ALL' else history.loc[history.line.eq(line)]
        cl = old_claims if line == 'ALL' else old_claims.loc[old_claims.line.eq(line)]
        allp = full_2024 if line == 'ALL' else full_2024.loc[full_2024.line.eq(line)]
        yearclaims = year2024_claims if line == 'ALL' else year2024_claims.loc[year2024_claims.line.eq(line)]
        has_year_claim = set(yearclaims.policy_id)
        profile.append({'line': line, 'policies': len(cc), 'same_customer': int(cc.same_customer.sum()),
            'same_address': int(cc.same_address.sum()), 'changed_address': int((~cc.same_address).sum()),
            'history_periods': len(hh), 'test_2025_rows': int(hh.year.eq(2025).sum()),
            'last_2024_exposure': float(pp.exposure.sum()), 'last_2024_claim_records': len(cl),
            'last_2024_accepted_claims': int(cl.accepted.sum()), 'last_2024_open_claims': int(cl.status.eq('open').sum()),
            'last_2024_repudiated_claims': int(cl.status.eq('repudiated').sum()),
            'last_2024_net_CU': int(cl.net_accepted_cents.sum()) / 100,
            'last_2024_open_reserve_CU': int(cl.open_case_reserve_cents.sum()) / 100,
            'no_claims_in_preceding_row': int(pp.observed_claim_records.eq(0).sum()),
            'no_accepted_claims_in_preceding_row': int(pp.accepted_claims.eq(0).sum()),
            'no_observed_claims_any_2024': sum(pid not in has_year_claim for pid in cc.policy_id),
            'base_2024_rows': len(allp), 'base_2024_exposure': float(allp.exposure.sum()),
            'base_2024_net_CU': int(allp.net_accepted_cents.sum()) / 100,
            'preceding_row_cost_share_pct': float(cl.net_accepted_cents.sum() / allp.net_accepted_cents.sum() * 100),
            'preceding_row_count_share_pct': len(pp) / len(allp) * 100,
            'preceding_row_exposure_share_pct': float(pp.exposure.sum() / allp.exposure.sum() * 100)})
    profile = pd.DataFrame(profile)
    save(profile, out, 'cohort_profile')
    comparison = f.loc[f.year.le(2024)].groupby(['line', 'year', 'renewal_decision'], dropna=False).agg(
        rows=('row_id', 'size'), exposure=('exposure', 'sum'), observed_claims=('observed_claim_records', 'sum'),
        accepted_claims=('accepted_claims', 'sum'), net_accepted_cents=('net_accepted_cents', 'sum'),
        no_accepted_claims=('accepted_claims', lambda s: int(s.eq(0).sum()))).reset_index()
    comparison['observed_net_CU'] = comparison.net_accepted_cents / 100
    comparison['observed_net_per_exposure_CU'] = comparison.observed_net_CU / comparison.exposure
    save(comparison, out, 'claim_cost_by_decision_year')
    hstats = history.groupby(['line', 'policy_id']).agg(first_year=('year', 'min'), history_rows=('row_id', 'size'),
        declines_in_history=('renewal_decision', lambda x: int(x.eq('declined_by_insurer').sum())),
        periods_2024=('year', lambda x: int(x.eq(2024).sum()))).reset_index()
    hstats = hstats.merge(scope[['policy_id', 'observed_claim_records', 'accepted_claims', 'net_accepted_cents']], on='policy_id', validate='one_to_one')
    hstats = hstats.merge(cohort[['policy_id', 'same_address']], on='policy_id', validate='one_to_one')
    save(hstats, out, 'cohort_policy_index')
    sensitivity = []
    base_cost = int(full_2024.net_accepted_cents.sum())
    base_exp = float(full_2024.exposure.sum())
    for label, drop in [('delete_preceding_2742_rows', scope), ('delete_all_2024_rows_of_cohort', cohort_2024)]:
        cost = int(drop.net_accepted_cents.sum()); exp = float(drop.exposure.sum())
        sensitivity.append({'hypothetical_scope': label, 'rows_excluded': len(drop), 'observed_net_removed_CU': cost / 100,
            'exposure_removed': exp, 'cost_removed_pct': cost / base_cost * 100, 'exposure_removed_pct': exp / base_exp * 100,
            'before_observed_net_per_exposure_CU': base_cost / 100 / base_exp,
            'after_observed_net_per_exposure_CU': (base_cost - cost) / 100 / (base_exp - exp),
            'observed_rate_change_pct': ((base_cost - cost) / (base_exp - exp) / (base_cost / base_exp) - 1) * 100,
            'applied': False, 'purpose': 'Illustrates outcome-dependent selection; not a recommended cleaning rule or ultimate tariff effect.'})
    save(pd.DataFrame(sensitivity), out, 'exclusion_sensitivity_NOT_APPLIED')
    save(old_claims.groupby(['line', 'status']).agg(records=('claim_id', 'size'), net_cents=('net_accepted_cents', 'sum'),
        reserve_cents=('open_case_reserve_cents', 'sum')).reset_index(), out, 'preceding_claim_status')
    save(history.groupby(['line', 'year', 'renewal_decision'], dropna=False).size().reset_index(name='periods'), out, 'cohort_decision_history')

    cases = []; used = set()
    def choose(label, why, pool, order=None, ascending=True, cohort_member=True):
        pool = pool.loc[~pool.policy_id.isin(used)]
        if order is None:
            pool = pool.sort_values(['line', 'policy_id'])
        else:
            pool = pool.sort_values(order, ascending=ascending)
        assert len(pool), label
        r = pool.iloc[0]; used.add(r.policy_id)
        cases.append({'case': len(cases) + 1, 'line': r.line, 'policy_id': r.policy_id,
            'label': label, 'interpretation': why, 'cohort_member': cohort_member})
    choose('El rechazo ya identificado: B00134306', 'Conserva el ID, cliente y dirección después del rechazo. Los siniestros de 2024 no se anulan por esa etiqueta.', scope.loc[scope.policy_id.eq('B00134306')])
    for line in LINES:
        choose('Mayor coste de periodo: ' + line,
            'El coste elevado y el sucesor coexisten. El incurrido abierto es pagado más reserva al corte; conservar sus componentes y revisar desarrollo, sin convertir la decisión en un filtro de pérdidas.',
            scope.loc[scope.line.eq(line)], ['net_accepted_cents', 'policy_id'], False)
    for line in ['motor', 'buildings']:
        choose('Sin siniestros observados en 2024: ' + line,
            'La etiqueta de rechazo no puede reconstruirse universalmente a partir del coste observado. Faltan motivo y fecha de decisión; el corte de reportes también deja pérdidas no observadas. No inferir causa ni rellenar un siniestro.',
            scope.loc[scope.line.eq(line) & ~scope.policy_id.isin(year2024_claims.policy_id)])
    choose('Rechazo repetido en varios años', 'El mismo contrato aparece rechazado en más de un año y continúa. El campo no se comporta como un estado absorbente de baja en los archivos.', hstats,
           ['declines_in_history', 'policy_id'], False)
    choose('Cambio de dirección en motor', 'Son el mismo cliente y policy_id, con nueva dirección. El cambio territorial de riesgo se conserva; no prueba reciclaje del ID ni elimina la contradicción de decisión.',
           cohort.loc[~cohort.same_address])
    choose('Cambio intranual de segmento', 'La póliza tiene varios segmentos en 2024. Asignar siniestros por ocurrencia al segmento correcto; no borrarlos o moverlos según la decisión del último segmento.',
           hstats.loc[hstats.periods_2024.gt(1)])
    repeated_reject = old_claims.loc[old_claims.status.eq('repudiated')]
    choose('Rechazo de póliza y siniestro repudiado', 'declined_by_insurer describe la decisión de póliza; repudiated describe un expediente. Son conceptos distintos. Aplicar el tratamiento de estado a cada siniestro, sin extenderlo a todos los del contrato.', repeated_reject)
    # Contextual controls from the same sources, not additions to the frozen cohort.
    no_next = all_declined.loc[all_declined.year.eq(2024) & ~all_declined.has_successor]
    choose('Control: rechazo sin sucesor observado', 'La etiqueta también existe sin continuación 2025. No observar sucesor es compatible con salida de cartera, pero no acredita motivo ni momento del rechazo.', no_next,
           ['period_end', 'policy_id'], False, False)
    renewed = f.loc[f.year.eq(2024) & f.renewal_decision.eq('renewed') & ~f.policy_id.isin(ids)]
    choose('Control: renewed con coste muy alto', 'También hay pólizas renewed con costes elevados. La severidad observada no da una regla determinista para corregir la etiqueta ni prueba causalidad de selección.', renewed,
           ['net_accepted_cents', 'policy_id'], False, False)
    control_ids = {x['policy_id'] for x in cases if not x['cohort_member']}
    # Materialize complete source histories for controls; preserve all current source fields for the cohort as well.
    selected_ids = ids | control_ids
    source_hist = []
    for line in LINES:
        for prefix in ['policies', 'test']:
            name = prefix + '_' + line
            x = pq.read_table(ROOT / cat[name]['workspace_relative_path']).to_pandas()
            x = x.loc[x.policy_id.isin(selected_ids)].copy()
            x['line'], x['source_table'] = line, name
            for col in ['period_start', 'period_end']:
                x[col] = pd.to_datetime(x[col])
            x['year'] = x.period_start.dt.year
            x['covered_days'] = (x.period_end - x.period_start).dt.days + 1
            x['claim_observation_available'] = x.year.le(2024)
            source_hist.append(x)
    source_hist = pd.concat(source_hist, ignore_index=True).sort_values(['line', 'policy_id', 'period_start', 'period_end', 'row_id'])
    selected_claims = claims.loc[claims.policy_id.isin(selected_ids)].copy()
    intervals = source_hist[['row_id', 'period_start', 'period_end']]
    selected_claims = selected_claims.merge(intervals, on='row_id', how='left', validate='many_to_one')
    selected_claims['reported_after_period'] = selected_claims.report_date.gt(selected_claims.period_end)
    save(source_hist, out, 'cohort_and_control_source_histories')
    save(selected_claims, out, 'cohort_and_control_claim_histories')
    case_ids = {x['policy_id'] for x in cases}
    save(source_hist.loc[source_hist.policy_id.isin(case_ids)], out, 'case_policy_histories')
    save(selected_claims.loc[selected_claims.policy_id.isin(case_ids)], out, 'case_claim_histories')
    save(pd.DataFrame(cases), out, 'case_index')
    # Every cohort policy is inspectable locally. No 2025 claim records or zero outcomes are fabricated.
    ph = {pid: rec(h) for pid, h in source_hist.groupby('policy_id', sort=False)}
    ch = {pid: rec(h) for pid, h in selected_claims.groupby('policy_id', sort=False)}
    histories = {pid: {'policies': ph[pid], 'claims': ch.get(pid, [])} for pid in ph}
    c.dump(out / 'explorer_data.json', {'cases': cases, 'index': rec(hstats.sort_values(['line', 'policy_id'])), 'histories': histories})
    total = profile.loc[profile.line.eq('ALL')].iloc[0]
    s = {'run': out.relative_to(ROOT).as_posix(), 'created_utc': datetime.now(timezone.utc).isoformat(),
        'rule': 'REN00', 'status': 'review_only_no_reclassification_or_deletion', 'frozen_policies': len(ids),
        'by_line': rec(profile), 'cohort_history_periods': len(history), 'cohort_history_claims': len(cohort_claims),
        'cohort_2025_rows': int(history.year.eq(2025).sum()), 'case_count': len(cases),
        'control_policies': len(control_ids), 'all_declined_rows_2021_2024': len(all_declined),
        'all_declined_with_successor': int(all_declined.has_successor.sum()),
        '2024_declined_total': int(all_declined.year.eq(2024).sum()), '2024_declined_without_successor': len(no_next),
        'cohort_multiple_declines': int(hstats.declines_in_history.gt(1).sum()),
        'cohort_three_declines': int(hstats.declines_in_history.eq(3).sum()),
        'same_customer': int(cohort.same_customer.sum()), 'changed_address': int((~cohort.same_address).sum()),
        'renewal_delta_one': int(cohort.renewal_count_delta.eq(1).sum()), '2025_new_business_false': int(cohort.new_business.eq(False).sum()),
        'preceding_claim_records': len(old_claims), 'preceding_accepted_claims': int(old_claims.accepted.sum()),
        'preceding_repudiated_claims': int(old_claims.status.eq('repudiated').sum()),
        'preceding_net_CU': int(old_claims.net_accepted_cents.sum()) / 100,
        'preceding_open_reserve_CU': int(old_claims.open_case_reserve_cents.sum()) / 100,
        '2024_no_observed_claim_policies': int(total.no_observed_claims_any_2024),
        'preceding_cost_share_2024_pct': float(total.preceding_row_cost_share_pct),
        'preceding_row_share_2024_pct': float(total.preceding_row_count_share_pct),
        'preceding_exposure_share_2024_pct': float(total.preceding_row_exposure_share_pct),
        'dates_pending': True, 'dates_modified': False, 'exposures_modified': False, 'decisions_modified': False,
        'claims_modified': False, 'active_dataset_changed': False, 'models_trained': False,
        'independent_validation': False, 'organizer_confirmation': False, 'external_ai_provider_used': False}
    c.dump(out / 'summary.json', s)
    c.dump(out / 'proposal.json', {'rule': 'REN00', 'status': 'proposal_only_not_applied',
        'recommended_treatment': 'Preserve all source policy rows, accepted claims and published dates. Treat declined_by_insurer as a semantically unresolved diagnostic outcome, not an absorbing cancellation rule.',
        'cohort_scope': 'Exactly 2742 frozen 2024 preceding IDs and their Jan1 2025 successors, linked to source hashes. Historical comparison does not expand this proposed cohort.',
        'predictor_policy': 'renewal_decision already excluded by protocol 1.3. Keep REN00, successor flags and claim diagnostics outside predictors; do not automatically use a previous-year decision without availability and meaning evidence.',
        'no_deletion_or_zeroing': 'Do not delete contracts or severe claims, truncate dates, cancel test periods, assign zero predictions or drop any of the 2931 test rows of these policies.',
        'no_relabel': 'Do not overwrite declined_by_insurer with renewed: a reversed/stale decision, another offer or an unenforced generation flag cannot be distinguished with these files.',
        'claim_assignment': 'Use inclusive loss_date intervals; report_date determines reporting availability, not which coverage row owns the loss. Distinguish policy refusal from repudiated claim status.',
        'calendar': 'Participant explicitly left dates pending; CAL00 remains unresolved and no exposure change follows from REN00.',
        'future_options_if_authorized': ['Keep a separate audit flag and normalized outcome unknown_contradictory, preserving the raw decision.',
            'Build an observed continuation label only for a separate retention question and appropriate cutoff; it is not the official renewal decision or a pricing predictor.',
            'If source confirms a labeling error, correct only the approved rows in a new derived layer with old/new ledger; recheck schemas and every unaffected value.'],
        'questions_for_source': ['Does declined_by_insurer mean final nonrenewal, an underwriting recommendation or one rejected offer?',
            'Is the decision generated from loss information without propagation to subsequent policy survival?',
            'Can a rejection be reversed or followed by another offer under the same policy_id? Where are timestamps/reasons?',
            'Why do some rejections have successors in every observed year, while others have early termination?',
            'Which decision information was actually available when quoting each period?'],
        'causal_limit': 'Large observed losses are associated with the flag, but no threshold or causal rule is identified. Counterexamples include no observed claims and renewed with high observed cost. Valuation and reporting truncation matter.',
        'IAA': ['Documentation §2 and §§4–6: cohort, lineage and reproducibility', 'Governance §2.8: own verification, no independent validation',
                'Professional considerations §3.2, §3.3 and §§3.5–3.6: interpretation, selection bias and human responsibility']})
    assert all(c.digest(ROOT / p) == sha for p, sha in protected.items())
    print(json.dumps({'run': str(out), 'summary': s, 'cases': cases, 'sensitivity': rec(pd.DataFrame(sensitivity))}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
