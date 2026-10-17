"""Investigación CAL00: evidencia y escenarios; no crea ni activa datos corregidos."""
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

REQUEST = ('Ahora revisemos las 500.245 continuidades que omiten el 31 de diciembre de 2024. '
           'Compara los historiales de pólizas y siniestros, muéstrame casos concretos y propón '
           'cómo tratarlo sin modificar las fechas todavía.')
D40 = ROOT / 'Hackaton/Semana 1/Validacion_datos/runs/gaps_20261016T193906Z_70462cf9'
LINES = ['motor', 'buildings', 'contents']


def records(frame):
    return json.loads(frame.to_json(orient='records', date_format='iso'))


def save(frame, out, name, csv=True):
    frame.to_parquet(out / 'tables' / (name + '.parquet'), index=False)
    if csv:
        frame.to_csv(out / 'tables' / (name + '.csv'), index=False)


def main():
    active = ROOT / 'Hackaton/Semana 1/Limpieza/current_dataset.json'
    pointer = json.loads(active.read_text('utf-8'))
    catalog_path = ROOT / pointer['catalog_workspace_relative']
    catalog = json.loads(catalog_path.read_text('utf-8'))
    parent = ROOT / pointer['workspace_relative_run']
    # Verify the prior immutable evidence before making a new diagnostic run.
    for directory in [D40, parent]:
        manifest = json.loads((directory / 'manifest.json').read_text('utf-8'))
        assert all(c.digest(directory / e['path']) == e['sha256'] for e in manifest['files'])
    ident = datetime.now(timezone.utc).strftime('calendar_%Y%m%dT%H%M%SZ_') + uuid.uuid4().hex[:8]
    out = BASE / 'runs' / ident
    for directory in ['tables', 'evidence', 'source_snapshot', 'figures']:
        (out / directory).mkdir(parents=True, exist_ok=False)
    for name in ['review_calendar.py', 'render_calendar.py', 'verify_calendar.py', 'verify_report.js', 'record_calendar.py']:
        shutil.copy2(BASE / name, out / 'source_snapshot' / name)
    shutil.copy2(Path(c.__file__), out / 'source_snapshot/clean_data.py')
    protected = {p.relative_to(ROOT).as_posix(): c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']: c.digest(ROOT / e['workspace_relative_path']) for e in catalog.values()})
    for p in [active, catalog_path, parent / 'manifest.json', D40 / 'manifest.json']:
        protected[p.relative_to(ROOT).as_posix()] = c.digest(p)
    assert all(c.digest(ROOT / e['workspace_relative_path']) == e['sha256'] for e in catalog.values())
    c.dump(out / 'protected_hashes_before.json', protected)
    sources = {'active_index.json': active, 'dataset_catalog.json': catalog_path,
               'D40_manifest.json': D40 / 'manifest.json', 'D42_manifest.json': parent / 'manifest.json',
               'D40_frozen_calendar_gaps.parquet': D40 / 'tables/calendar_gaps.parquet',
               'D42_claim_assignment.parquet': parent / 'tables/claim_period_assignment.parquet',
               'official_data_description.md': ROOT / 'Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md',
               'IAA_priorities.md': ROOT / 'Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md'}
    for name, source in sources.items():
        shutil.copy2(source, out / 'evidence' / name)
    for name in ['MEMORIA_PROYECTO.md', 'ESTADO_PROYECTO.json', 'DECISIONES.md']:
        shutil.copy2(ROOT / 'Preparación' / name, out / 'evidence' / ('before_' + name))
    c.dump(out / 'request.json', {'request': REQUEST, 'scope': 'Review only; no date, exposure, premium, claim or catalog changes.',
                                'ai_role': 'Codex proposes hypotheses, runs reproducible checks and drafts this review.',
                                'external_ai_provider_used': False, 'independent_validation': False})
    common = ['row_id', 'policy_id', 'customer_id', 'address_id', 'period_start', 'period_end', 'exposure',
              'new_business', 'renewal_count', 'written_premium', 'voluntary_excess', 'compulsory_excess']
    frames = []
    for line in LINES:
        extra = ['cover_type', 'make_model', 'vehicle_value_group'] if line == 'motor' else ['sum_insured', 'accidental_damage_cover']
        for prefix in ['policies', 'test']:
            name = prefix + '_' + line
            fields = common + extra + (['renewal_decision'] if prefix == 'policies' else [])
            frame = pq.read_table(ROOT / catalog[name]['workspace_relative_path'], columns=fields).to_pandas()
            frame['line'], frame['source_table'] = line, name
            for col in ['period_start', 'period_end']:
                frame[col] = pd.to_datetime(frame[col])
            frames.append(frame)
    f = pd.concat(frames, ignore_index=True).sort_values(['line', 'policy_id', 'period_start', 'period_end', 'row_id']).reset_index(drop=True)
    f['year'] = f.period_start.dt.year
    f['covered_days'] = (f.period_end - f.period_start).dt.days + 1
    assert (f.period_start.dt.year == f.period_end.dt.year).all()
    assert np.allclose(f.exposure, (f.covered_days / 365).round(4), atol=1e-10, rtol=0)
    groups = f.groupby(['line', 'policy_id'], sort=False)
    for col in ['row_id', 'period_end', 'year', 'renewal_decision', 'customer_id', 'address_id', 'renewal_count']:
        f['previous_' + col] = groups[col].shift()
    f['gap_days'] = (f.period_start - f.previous_period_end).dt.days - 1
    frozen = pd.read_parquet(out / 'evidence/D40_frozen_calendar_gaps.parquet')
    g = f.loc[f.gap_days > 0].copy()
    assert len(g) == 500245 and (g.gap_days == 1).all()
    assert set(zip(g.line, g.row_id, g.previous_row_id)) == set(zip(frozen.line, frozen.row_id, frozen.previous_row_id))
    assert (g.period_start == pd.Timestamp('2025-01-01')).all()
    assert (g.previous_period_end == pd.Timestamp('2024-12-30')).all()
    assert not (f.gap_days < 0).any()
    # Freeze both endpoints, not a corrected period table.
    prev = f.set_index('row_id').loc[g.previous_row_id].reset_index()
    g = g.reset_index(drop=True)
    cohort = g[['line', 'policy_id', 'row_id', 'previous_row_id', 'customer_id', 'address_id', 'period_start',
                'previous_period_end', 'gap_days', 'renewal_count', 'new_business']].copy()
    for col in ['period_start', 'exposure', 'covered_days', 'renewal_decision', 'renewal_count', 'customer_id',
                'address_id', 'written_premium']:
        cohort['previous_' + col] = prev[col].to_numpy()
    cohort['same_customer'] = cohort.customer_id == cohort.previous_customer_id
    cohort['same_address'] = cohort.address_id == cohort.previous_address_id
    cohort['renewal_count_delta'] = cohort.renewal_count - cohort.previous_renewal_count
    cohort['consistent_renewed_label'] = cohort.previous_renewal_decision == 'renewed'
    cohort['diagnostic_flag'] = 'CAL00_gap_2024_12_31_review_only'
    save(cohort, out, 'gap_cohort', csv=False)

    boundaries = f.loc[f.previous_year.notna() & (f.year != f.previous_year)].copy()
    boundary_summary = boundaries.groupby(['line', 'year', 'gap_days', 'previous_renewal_decision'], dropna=False).size().reset_index(name='transitions')
    save(boundary_summary, out, 'annual_boundaries')
    annual = f.groupby(['line', 'year']).agg(rows=('row_id', 'size'), policies=('policy_id', 'nunique'),
        covered_days=('covered_days', 'sum'), exposure=('exposure', 'sum'), max_end=('period_end', 'max'),
        max_start=('period_start', 'max'), full365=('covered_days', lambda s: int((s == 365).sum())),
        full366=('covered_days', lambda s: int((s == 366).sum()))).reset_index()
    save(annual, out, 'annual_calendar')
    affected_ids = set(cohort.policy_id)
    hist = f.loc[f.policy_id.isin(affected_ids)].copy()
    history_fields = [col for col in common + ['line', 'source_table', 'year', 'covered_days', 'renewal_decision',
        'cover_type', 'make_model', 'vehicle_value_group', 'sum_insured', 'accidental_damage_cover', 'gap_days'] if col in hist]
    save(hist[history_fields], out, 'all_affected_policy_histories', csv=False)
    tenure = hist.groupby(['line', 'policy_id']).agg(first_year=('year', 'min'), periods=('row_id', 'size'),
        observed_years=('year', 'nunique'), addresses=('address_id', 'nunique')).reset_index()
    prior2024 = hist.loc[hist.year == 2024].groupby(['line', 'policy_id']).agg(
        periods_2024=('row_id', 'size'), covered_days_2024=('covered_days', 'sum'), exposure_2024=('exposure', 'sum')).reset_index()
    cohort = cohort.merge(tenure, on=['line', 'policy_id'], validate='one_to_one').merge(prior2024, on=['line', 'policy_id'], validate='one_to_one')
    save(cohort, out, 'gap_cohort', csv=False)
    profile = cohort.groupby('line').agg(continuities=('row_id', 'size'), consistent_renewed=('consistent_renewed_label', 'sum'),
        same_customer=('same_customer', 'sum'), same_address=('same_address', 'sum'),
        full365_previous_rows=('previous_covered_days', lambda s: int((s == 365).sum())),
        multiple_periods_2024=('periods_2024', lambda s: int((s > 1).sum())),
        full365_policy_days_2024=('covered_days_2024', lambda s: int((s == 365).sum())),
        all_history_rows=('periods', 'sum'), previous_row_exposure=('previous_exposure', 'sum'),
        cohort_2024_exposure=('exposure_2024', 'sum')).reset_index()
    save(profile, out, 'cohort_profile')
    save(cohort.groupby(['line', 'previous_renewal_decision', 'renewal_count_delta', 'new_business'], dropna=False).size().reset_index(name='rows'), out, 'renewal_consistency')
    save(cohort.groupby(['line', 'first_year', 'observed_years', 'periods_2024'], dropna=False).size().reset_index(name='policies'), out, 'history_profile')

    claims = pq.read_table(ROOT / catalog['claims']['workspace_relative_path']).to_pandas()
    for col in ['loss_date', 'report_date']:
        claims[col] = pd.to_datetime(claims[col])
    claims['accepted'] = claims.status.isin(['closed', 'open'])
    claims['observed_net_CU'] = np.where(claims.accepted, claims.incurred_to_date - claims.recoveries, 0.)
    claims['report_delay_days'] = (claims.report_date - claims.loss_date).dt.days
    claims['loss_year'] = claims.loss_date.dt.year
    # Reconstruct assignment from current source intervals, without using report_date as coverage date.
    j = claims[['claim_id', 'line', 'policy_id', 'loss_date']].merge(
        f[['row_id', 'line', 'policy_id', 'period_start', 'period_end']], on=['line', 'policy_id'], how='left')
    hits = j.loc[j.loss_date.between(j.period_start, j.period_end)]
    assert not hits.claim_id.duplicated().any()
    claims = claims.merge(hits[['claim_id', 'row_id', 'period_start', 'period_end']], on='claim_id', how='left', validate='one_to_one')
    prior_assignment = pd.read_parquet(out / 'evidence/D42_claim_assignment.parquet').set_index('claim_id')
    assert claims.set_index('claim_id').row_id.fillna('NONE').equals(prior_assignment.row_id.reindex(claims.claim_id).set_axis(claims.claim_id).fillna('NONE'))
    claims['report_after_assigned_period'] = claims.row_id.notna() & (claims.report_date > claims.period_end)
    affected_claims = claims.loc[claims.policy_id.isin(affected_ids)].copy()
    save(affected_claims, out, 'all_affected_claim_histories', csv=False)
    cs = affected_claims.groupby(['line', 'loss_year', 'status'], dropna=False).agg(records=('claim_id', 'size'),
        observed_net_CU=('observed_net_CU', 'sum'), reports_after_period=('report_after_assigned_period', 'sum')).reset_index()
    save(cs, out, 'cohort_claim_summary')
    claim_annual = claims.groupby(['line', 'loss_year']).agg(records=('claim_id', 'size'), accepted=('accepted', 'sum'),
        observed_net_CU=('observed_net_CU', 'sum')).reset_index()
    save(claim_annual, out, 'claims_by_occurrence_year')
    # All days, including zero-event days; zero reported observations are not zero ultimate risk.
    daily_rows = []
    for line in LINES:
        for year in range(2021, 2026):
            days = pd.date_range(f'{year}-01-01', f'{year}-12-31')
            ff = f.loc[(f.line == line) & (f.year == year)]
            delta = np.zeros(len(days) + 1, dtype=np.int64)
            a = (ff.period_start - days[0]).dt.days.to_numpy()
            b = (ff.period_end - days[0]).dt.days.to_numpy() + 1
            np.add.at(delta, a, 1); np.add.at(delta, b, -1)
            cc = claims.loc[claims.line == line]
            daily = pd.DataFrame({'line': line, 'year': year, 'date': days, 'covered_policy_rows': delta.cumsum()[:-1]})
            daily['loss_records'] = cc.groupby('loss_date').size().reindex(days, fill_value=0).to_numpy()
            daily['report_records'] = cc.groupby('report_date').size().reindex(days, fill_value=0).to_numpy()
            daily['claims_snapshot_available'] = year <= 2024
            daily_rows.append(daily)
    daily = pd.concat(daily_rows, ignore_index=True)
    save(daily, out, 'daily_calendar')
    tail = daily.loc[(daily.date.dt.month == 12) & (daily.date.dt.day >= 15) & (daily.year <= 2024)]
    save(tail, out, 'year_end_daily')
    report_tail = claims.loc[claims.report_date.ge('2024-12-15')].groupby('report_date').agg(
        records=('claim_id', 'size'), earliest_loss=('loss_date', 'min'), latest_loss=('loss_date', 'max'),
        min_delay=('report_delay_days', 'min'), median_delay=('report_delay_days', 'median'), max_delay=('report_delay_days', 'max')).reset_index()
    save(report_tail, out, 'last_reports')
    special = claims.loc[(claims.loss_date.dt.strftime('%m-%d').isin(['01-01', '02-29', '12-29', '12-30', '12-31'])) |
                         (claims.report_date.ge('2024-12-28'))].copy()
    save(special, out, 'boundary_claims', csv=False)

    # Arithmetic sensitivities only; none of these columns are model inputs or active exposure.
    scenario_rows = []
    for line in LINES + ['ALL']:
        z = cohort if line == 'ALL' else cohort.loc[cohort.line == line]
        aa = f.loc[f.year == 2024] if line == 'ALL' else f.loc[(f.year == 2024) & (f.line == line)]
        den = float(aa.exposure.sum())
        for name, zz in [('bridge_all', z), ('bridge_consistent_renewed', z.loc[z.consistent_renewed_label])]:
            exact_delta = len(zz) / 365
            rounded_delta = float((((zz.previous_covered_days + 1) / 365).round(4) - zz.previous_exposure).sum())
            scenario_rows.append({'line': line, 'scenario': name, 'rows': len(zz), 'added_days': len(zz),
                'ACT365_unrounded_extra_years': exact_delta, 'ACT365_row_rounded_extra_years': rounded_delta,
                'base_2024_all_row_exposure': den, 'denominator_increase_pct': 100 * rounded_delta / den,
                'fixed_observed_cost_rate_change_pct': 100 * (den / (den + rounded_delta) - 1),
                'dates_modified': False, 'exposure_modified': False,
                'note': 'Illustrative fixed observed numerator; no omitted-day claims estimated, no seasonality or IBNR adjustment.'})
    scenarios = pd.DataFrame(scenario_rows)
    save(scenarios, out, 'hypothetical_exposure_scenarios')
    ageometry = []
    for line in LINES + ['ALL']:
        aa = f.loc[f.year == 2024] if line == 'ALL' else f.loc[(f.year == 2024) & (f.line == line)]
        z = cohort if line == 'ALL' else cohort.loc[cohort.line == line]
        base_days = int(aa.covered_days.sum())
        ageometry.append({'line': line, 'unchanged_dates_ACT365_exact': base_days / 365,
            'unchanged_dates_ACT366_exact': base_days / 366, 'bridge_all_ACT365_exact': (base_days + len(z)) / 365,
            'bridge_all_ACT366_exact': (base_days + len(z)) / 366,
            'warning': 'Date extension and denominator convention are separate assumptions; no scenario applied.'})
    save(pd.DataFrame(ageometry), out, 'day_count_conventions')
    last_dates = f.loc[f.year == 2024].groupby(['line', 'renewal_decision']).agg(
        rows=('row_id', 'size'), latest_end=('period_end', 'max')).reset_index()
    save(last_dates, out, 'end_dates_by_decision_2024')

    # Real cases selected deterministically by an explanatory question, not by model performance.
    cases = []; seen = set()
    def choose(label, text, candidates):
        pool = candidates.loc[~candidates.policy_id.isin(seen)].sort_values(['line', 'policy_id'])
        assert len(pool), label
        r = pool.iloc[0]; seen.add(r.policy_id)
        cases.append({'case': len(cases) + 1, 'label': label, 'line': r.line, 'policy_id': r.policy_id, 'interpretation': text})
    for line in LINES:
        choose('Continuidad anual: ' + line,
            'La misma póliza conserva cliente y dirección. Compare cierres 2023/2024/2025 y renovación; la historia no acredita por sí sola el contrato legal del día omitido.',
            cohort.loc[(cohort.line == line) & (cohort.first_year == 2021) & (cohort.periods_2024 == 1) & cohort.consistent_renewed_label])
    latest = claims.loc[claims.loss_date == pd.Timestamp('2024-12-29')]
    for line in LINES:
        choose('Ocurrencia 29-12-2024: ' + line,
            'Ocurrió dentro del intervalo publicado y se reportó antes del corte observado. Está asignado por loss_date. Es un expediente observado, no coste último consolidado.',
            cohort.loc[(cohort.line == line) & cohort.policy_id.isin(latest.policy_id)])
    choose('Cambio intranual antes de renovar',
        'El último segmento es parcial. Extender únicamente ese segmento evita duplicar el día entre segmentos, pero requiere confirmar cobertura y recalcular exposición; no prorratear written_premium automáticamente.',
        cohort.loc[(cohort.periods_2024 > 1) & (cohort.previous_covered_days < 365) & cohort.consistent_renewed_label])
    choose('Segmento final de solo dos días',
        'Un día adicional es material para esta fila: pasa hipotéticamente de dos a tres días, aunque su efecto sobre el total sea pequeño. Su exposición redondeada debe recalcularse desde los días.',
        cohort.loc[cohort.previous_covered_days == 2])
    choose('Rechazo de renovación con continuidad',
        'renewal_decision dice declined_by_insurer, pero existe periodo 2025 con el mismo policy_id. No borrar historia ni imponer automáticamente una interpretación contractual; aislar contradicción.',
        cohort.loc[~cohort.consistent_renewed_label])
    delayed = claims.loc[(claims.loss_date == pd.Timestamp('2023-12-31')) & (claims.report_date.dt.year == 2024)]
    choose('Ocurrencia 31-12-2023 y reporte 2024',
        'El siniestro pertenece al periodo de ocurrencia 2023 aunque se reportase en 2024. No reasignarlo al año del reporte ni desplazarlo para cerrar un hueco.',
        cohort.loc[cohort.policy_id.isin(delayed.policy_id)])
    leap = claims.loc[claims.loss_date == pd.Timestamp('2024-02-29')]
    choose('Siniestro en el día bisiesto',
        'Existe 29 de febrero en fechas de cobertura y siniestros. No es un calendario que simplemente omita el día bisiesto; el déficit está al final del año.',
        cohort.loc[cohort.policy_id.isin(leap.policy_id)])
    # A genuine early termination is an explicit counterexample to extending every 2024 row.
    terminal = f.loc[(f.year == 2024) & (~f.policy_id.isin(affected_ids)) & (f.renewal_decision == 'cancelled') &
                     f.period_end.ge('2024-12-20') & f.period_end.lt('2024-12-30')]
    choose('Control: cancelación antes de fin de año',
        'Termina antes del 30 y no tiene sucesor 2025. Este caso queda fuera de la cohorte. Una normalización global de todos los period_end inventaría cobertura.', terminal)
    case_index = pd.DataFrame(cases)
    save(case_index, out, 'case_index')
    selected = set(case_index.policy_id)
    case_policies = f.loc[f.policy_id.isin(selected), history_fields]
    case_claims = claims.loc[claims.policy_id.isin(selected)]
    save(case_policies, out, 'case_policy_histories')
    save(case_claims, out, 'case_claim_histories')
    c.dump(out / 'cases.json', [{'case': row, 'policies': records(case_policies.loc[case_policies.policy_id == row['policy_id']]),
        'claims': records(case_claims.loc[case_claims.policy_id == row['policy_id']])} for row in cases])
    # Day-365 clustering is evidence of a mechanism, not access to the synthetic data generator.
    terminal_rows = []
    for year in range(2021, 2026):
        terminal_date = pd.Timestamp(f'{year}-01-01') + pd.Timedelta(days=364)
        ff = f.loc[f.year == year]
        terminal_rows.append({'year': year, 'day_365_date': terminal_date.isoformat(),
            'rows_ending_day365': int((ff.period_end == terminal_date).sum()),
            'rows_ending_calendar_dec31': int((ff.period_end == pd.Timestamp(f'{year}-12-31')).sum()),
            'rows_ending_day366': int((ff.period_end == pd.Timestamp(f'{year}-01-01') + pd.Timedelta(days=365)).sum())})
    save(pd.DataFrame(terminal_rows), out, 'day365_pattern')
    total2024 = annual.loc[annual.year == 2024]
    summary = {'run': out.relative_to(ROOT).as_posix(), 'created_utc': datetime.now(timezone.utc).isoformat(),
        'active_source': pointer, 'status': 'review_only_no_calendar_correction', 'gap_rows': len(cohort),
        'gap_distinct_policies': int(cohort.policy_id.nunique()), 'gap_days_each': 1,
        'gap_day': '2024-12-31', 'by_line': records(profile), 'all_policy_rows': len(f),
        'all_affected_history_rows': len(hist), 'all_affected_claim_rows': len(affected_claims),
        'consistent_renewed': int(cohort.consistent_renewed_label.sum()),
        'declined_but_continued': int((cohort.previous_renewal_decision == 'declined_by_insurer').sum()),
        'same_customer': int(cohort.same_customer.sum()), 'same_address': int(cohort.same_address.sum()),
        'renewal_delta_counts': {str(k): int(v) for k, v in cohort.renewal_count_delta.value_counts().items()},
        'new_business_counts': {str(k): int(v) for k, v in cohort.new_business.value_counts().items()},
        'no_overlaps': bool(not (f.gap_days < 0).any()),
        'end_dec30_2024_rows': int(((f.year == 2024) & (f.period_end == pd.Timestamp('2024-12-30'))).sum()),
        'no_2024_coverage_dec31': bool((daily.loc[daily.date == pd.Timestamp('2024-12-31'), 'covered_policy_rows'] == 0).all()),
        'covered_days_2024': int(total2024.covered_days.sum()), 'exposure_2024': float(total2024.exposure.sum()),
        'claim_rows': len(claims), 'claim_max_loss_date': str(claims.loss_date.max().date()),
        'claim_max_report_date': str(claims.report_date.max().date()), 'claim_min_report_delay_days': int(claims.report_delay_days.min()),
        'loss_dec30_2024': int((claims.loss_date == pd.Timestamp('2024-12-30')).sum()),
        'loss_dec31_2024': int((claims.loss_date == pd.Timestamp('2024-12-31')).sum()),
        'reports_dec30_2024': int((claims.report_date == pd.Timestamp('2024-12-30')).sum()),
        'reports_dec31_2024': int((claims.report_date == pd.Timestamp('2024-12-31')).sum()),
        'loss_leapday_2024': int((claims.loss_date == pd.Timestamp('2024-02-29')).sum()),
        'case_count': len(cases), 'case_policy_rows': len(case_policies), 'case_claim_rows': len(case_claims),
        'protected_files': len(protected), 'original_files': len(list(c.RAW.glob('*.parquet'))),
        'dates_modified': False, 'exposure_modified': False, 'claims_modified': False, 'active_dataset_changed': False,
        'independent_validation': False, 'organizer_confirmation': False, 'models_trained': False}
    c.dump(out / 'summary.json', summary)
    c.dump(out / 'proposal.json', {
        'rule': 'CAL00', 'status': 'diagnostic_proposal_not_approved_or_applied',
        'recommended_current_treatment': 'Preserve published dates and current EXP01 exposure as the provided-period baseline. Flag the 500245 bridges only in diagnostic evidence; leave calendar convention and report cutoff unresolved.',
        'inference': 'Terminal dates cluster on day 365 of each year. This supports a 365-position generation convention or leap-year defect; its cause and intended contract coverage are not confirmed.',
        'strong_candidate_subset': 497503, 'contradictory_renewal_subset': 2742,
        'conditional_future_extension': 'Only if coverage through 31 Dec 2024 is confirmed, extend the preceding last 2024 segment by one day in a new derived layer and recompute exposure under an explicitly chosen basis. Freeze row IDs and source hashes; check no overlap and retain reversal ledger.',
        'never_do': ['Shift loss_date or report_date', 'Invent a zero-loss observation or synthetic claim for 31 Dec',
                     'Extend cancellations or every 2024 segment', 'Automatically change written_premium',
                     'Treat no observed claims on the missing day as absence of risk',
                     'Choose the calendar rule for a favorable leaderboard or rate'],
        'questions_for_source_when_authorized': ['Was each year intentionally limited to 365 date positions?',
            'Were policy coverage and claim generation both stopped on day 365 in 2024?',
            'Why is the latest report 30 Dec when valuation is described as 31 Dec?',
            'Is exposure ACT/365, ACT/ACT, a 365-day simulation time, or another definition?',
            'How should declined_by_insurer followed by the same policy in 2025 be read?'],
        'claim_cutoff_hypothesis': 'If observed minimum report delay is 1 day, cutoff on 30 Dec is compatible with latest loss on 29 Dec. This is an implication of the observed data, not proof of the generation mechanism.',
        'sensitivity_scope': 'Arithmetic denominator checks only. No inference of ultimate losses, missing-day cost, actual tariff change or predictive benefit.',
        'IAA': ['Documentation §2 and §§4–6: lineage, assumptions and reproduction',
                'Governance §2.8: own verification, no independent validation',
                'Professional considerations §3.2 and §§3.5–3.6: explain uncertainty and preserve human decision']})
    assert all(c.digest(ROOT / name) == sha for name, sha in protected.items())
    print(json.dumps({'run': str(out), 'summary': summary, 'scenarios': records(scenarios), 'cases': cases}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
