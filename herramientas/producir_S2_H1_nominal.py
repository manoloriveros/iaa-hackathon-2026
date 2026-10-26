"""P6: productor nominal S2/H1 explícito, con calibración completa y fuente congelada.

No consume precios F3c, mezcla REN de PUL2 ni API de Kaggle. La cartera completa
fija el ámbito de los normalizadores de aplicación; no admite precios por lotes
parciales como si fueran equivalentes.
"""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from pathlib import Path
import argparse
import csv
import importlib.util
import json
import math
import os
import sys
import subprocess

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'
OUT = BASE/'P6_productor_S2_H1_nominal_20261026_v1'
PLAN = R/'registro/semana2_productor_S2_H1_nominal_plan_v1.json'
PUL = BASE/'F3c_PUL2_prototipo_20261026_v1'
HOME = BASE/'A1S_nucleo_20261026_v1'
SAMPLE = R/'privado/semana2/envios/g4_20261025_v1/official_sample_format.csv'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader')); sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


p4 = load('P6_frozen_scope_math', R/'herramientas/validar_transferencia_anual_H1.py')
n = p4.n; h = p4.h; b = p4.b; g = p4.g; v = p4.v; w = p4.w; core = p4.complete
CLAIMS = b.BASE/'claim_assignment_audit.parquet'


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def event(folder, kind, **fields):
    folder.mkdir(parents=True, exist_ok=True)
    with (folder/'events.jsonl').open('a', encoding='utf8') as stream:
        stream.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'kind': kind, **fields})+'\n')


def round_ticks(values):
    assert np.isfinite(values).all() and (values > 0).all()
    result = []
    for value in values:
        numerator, denominator = float(value).as_integer_ratio()
        integer, rest = divmod(numerator*1_000_000, denominator)
        integer += int(2*rest > denominator or (2*rest == denominator and integer % 2 == 1))
        assert 0 < integer < 2**63
        result.append(integer)
    return np.array(result, dtype=np.int64)


def learn_n3(train):
    value = train.annual_raw_T2b.to_numpy(float)*train.e_cost_scope.to_numpy(float)
    shapes = []
    for variable in (['ncb', 'prior'] if train.line.iloc[0] == 'motor' else ['prior']):
        shape, value = b.shape_fit(train, value, variable); shapes.append(shape)
    level = b.factor(train.T0.to_numpy(float), value)
    cell = b.cell_levels(train, value, level)
    return {'line': train.line.iloc[0], 'link': 'e_cost_scope', 'shape': shapes, 'kshape': level,
            'cellshape': cell, 'stages': [], 'training_normalizers': {}, 'held_normalizers': {},
            'training_row_ids_digest': b.digest(sorted(train.row_id)),
            'training_groups_digest': b.digest(sorted(set(train.group_id)))}


def fit_base(f, claims, line, folder, log):
    """Only strict historical periods enter this full-training calibration API."""
    assert f.year.isin([2023, 2024]).all() and not f.is_test.any()
    assert f.row_id.is_unique and f.T0.ge(0).all() and f.exposure.gt(0).all()
    assert set(f.year) == {2023, 2024} and set(f.new_business.astype(int)) == {0, 1}
    work = f.copy(); work['fold'] = 0
    keys = sorted(work.row_id); signature = b.digest(keys); folder.mkdir(parents=True, exist_ok=True)
    cp = folder/'C0.json'
    if not cp.exists():
        original = v.fit_reporting; perils = sorted(x[2:] for x in work if x.startswith('f_')); sequence = [0]
        def cached(*args, **kwargs):
            assert not kwargs
            peril = perils[sequence[0]]; sequence[0] += 1
            path = folder/('curve_'+peril+'.json'); digest = n.args_digest(args)
            if path.exists():
                a = w.read(path); assert a['argument_digest'] == digest
                return a['model'], np.asarray(a['prob_n'], float)
            event(log, 'reporting_started', line=line, peril=peril)
            model, probability = original(*args)
            dump(path, {'argument_digest': digest, 'model': model, 'prob_n': np.asarray(probability).tolist()})
            event(log, 'reporting_completed', line=line, peril=peril, sha256=w.sha(path))
            return model, probability
        v.fit_reporting = cached
        try:
            _, c0 = b.reporting_scope(work, claims, 1)
        finally:
            v.fit_reporting = original
        assert sequence[0] == len(perils)
        dump(cp, c0)
    c0 = w.read(cp); assert c0['fit_row_ids'] == keys
    selected = claims.loc[claims.row_id.isin(keys)]
    selected = selected.loc[selected.included_in_T0]
    assert selected.year.isin([2023, 2024]).all() and c0['fit_claim_ids'] == sorted(selected.claim_id.tolist())
    qg, _ = p4.frozen.completion(work, c0)
    assert (qg > 0).all()
    work['e_cost_scope'] = work.exposure.to_numpy()*qg
    npth = folder/'N3.json'
    if not npth.exists():
        event(log, 'N3_started', line=line)
        a = learn_n3(work); dump(npth, a)
        event(log, 'N3_completed', line=line, constants=n.count_constants(a))
    n3 = w.read(npth); assert n3['training_row_ids_digest'] == signature
    work['base_N3'] = h.apply_component(work, n3, 'e_cost_scope')
    sp = folder/'S2.json'
    if not sp.exists():
        event(log, 'S2_started', line=line)
        _, a = core.learn(work, 1, line)
        assert a['held_normalizers'] == {stage: {} for stage in g.STAGES[line]}
        dump(sp, a)
        comp = a['component']
        constants = {'shape_factors': comp['shape_factor_constants'], 'levels': comp['level_constants'],
                     'residual_factors': sum(len(z['factors']) for z in a['stages']),
                     'training_nuisance_levels': sum(len(z['nuisance_year_business']) for z in a['stages']),
                     'shape_training_normalizers_separate': comp['shape_training_normalizers'],
                     'training_stage_normalizers_separate': sum(len(z) for z in a['training_normalizers'].values()),
                     'observed_held_stage_normalizers_separate': 0, 'stage_calls': len(a['stages'])}
        event(log, 'S2_completed', line=line, constants=constants)
    s2 = w.read(sp); assert s2['fit_row_ids_digest'] == signature
    controls = {}
    for name, shapes, level, raw in [
        ('N3', n3['shape'], n3['kshape'], work.annual_raw_T2b.to_numpy()*work.e_cost_scope.to_numpy()),
        ('A1S_component', s2['component']['shape'], s2['component']['level'], np.exp(work.log_relative_A1S.to_numpy())*work.e_cost_scope.to_numpy()),
    ]:
        for shape in shapes:
            raw = b.shape_apply(work, raw, shape)
        moment = math.fsum((work.T0.to_numpy()/np.sqrt(raw)).tolist())/math.fsum(np.sqrt(raw).tolist())
        assert math.isclose(moment, level, rel_tol=3e-12)
        controls[name] = {'moment_relative_error': abs(moment/level-1)}
    worst_mean = 0.; worst_cdf = 0.
    for peril, model in c0['curves'].items():
        c = selected.loc[selected.peril.eq(peril)]
        delay = (pd.to_datetime(c.report_date)-pd.to_datetime(c.loss_date)).dt.days.to_numpy()
        support = np.asarray(model['delay_days']); index = np.searchsorted(support, delay)
        assert len(c) == model['n'] and np.array_equal(support[index], delay)
        probability = np.asarray(model['count_mass'])[index]/np.asarray(model['events'])[index]
        mark = c.T0_cents.to_numpy(float)/100
        mean = math.fsum((probability*mark).tolist())
        cdf = np.cumsum(np.bincount(index, weights=probability*mark, minlength=len(support)))/mean
        err = abs(mean/model['mean_net_mark']['1.0']-1); ce = float(np.max(np.abs(cdf-np.asarray(model['cost_cdf']['1.0']))))
        assert err < 3e-12 and ce < 3e-12
        worst_mean = max(worst_mean, err); worst_cdf = max(worst_cdf, ce)
    controls['new_full_C0_scalar_math'] = {'max_mean_relative_error': worst_mean, 'max_costCDF_absolute_error': worst_cdf}
    return {'N3': n3, 'S2': s2, 'C0': c0, 'controls': controls}


def forecast(future, components, artifact, expected_ids):
    assert future.row_id.is_unique and components.row_id.is_unique
    assert len(future) == len(components) == len(expected_ids) and len(set(expected_ids)) == len(expected_ids)
    assert set(future.row_id) == set(components.row_id) == set(expected_ids), 'Complete fixed cohort required'
    f = future.set_index('row_id').loc[expected_ids].reset_index()
    p = components.set_index('row_id').loc[expected_ids]
    assert f.year.eq(2025).all() and f.is_test.all()
    assert np.isfinite(f.exposure_calendar).all() and f.exposure_calendar.gt(0).all()
    assert np.isfinite(f.annual_raw_T2b).all() and f.annual_raw_T2b.gt(0).all()
    assert np.isfinite(f.log_relative_A1S).all()
    f['exposure'] = f.exposure_calendar.to_numpy(); f['e_cost_scope'] = f.exposure_calendar.to_numpy()
    f['base_N3'] = h.apply_component(f, artifact['N3'], 'e_cost_scope', ultimate=True)
    values, norms = core.replay(f, artifact['S2'])
    base = values['S2']; ratios = p[[f'ratio_H1_G3_{k}' for k in range(5)]].to_numpy(float)
    assert np.isfinite(ratios).all() and (ratios > 0).all()
    members = base[:, None]*ratios; candidate = members.mean(axis=1)
    assert np.allclose(candidate, sum(members[:, k] for k in range(5))/5, rtol=2e-15)
    assert np.isfinite(candidate).all() and (candidate > 0).all()
    return pd.DataFrame({'row_id': expected_ids, 'base_S2': base, 'candidate_S2_H1': candidate}), norms


def synthetic():
    rng = np.random.default_rng(2026102634); checks = []
    for line, perils in [('motor', ['bodily_injury', 'glass_hail', 'own_damage', 'theft', 'third_party_prop']),
                         ('buildings', ['accidental_damage', 'escape_of_water', 'fire', 'flood', 'storm', 'subsidence']),
                         ('contents', ['accidental_damage', 'escape_of_water', 'flood', 'theft'])]:
        size = 1000; years = rng.integers(2023, 2025, size); E = np.where(years == 2024, 366/365, 1.)
        f = pd.DataFrame({'row_id': [line+'h'+str(i) for i in range(size)], 'line': line, 'year': years,
                          'group_id': ['g'+str(i) for i in range(size)], 'is_test': False, 'fold': 0,
                          'new_business': rng.integers(0, 2, size), 'exposure': np.round(E, 4), 'exposure_calendar': E,
                          'period_start': pd.to_datetime(pd.Series(years).astype(str)+'-01-01'),
                          'period_end': pd.to_datetime(pd.Series(years).astype(str)+'-12-31'),
                          'annual_raw_T2b': rng.uniform(30, 250, size), 'log_relative_A1S': rng.normal(0, .3, size),
                          'prior_claims_5y': rng.integers(0, 3, size), 'ncb_years': rng.integers(0, 15, size),
                          'gender': rng.choice(['F', 'M'], size), 'works_from_home': rng.choice([True, False], size),
                          'marketing_segment': rng.choice(['a', 'b', 'c'], size)})
        marks = rng.integers(100, 80000, size, dtype=np.int64); reserves = marks//5
        f['T0'] = marks/100; f['reserve'] = reserves/100
        for p in perils:
            f['f_'+p] = rng.uniform(.1, 1, size); f['s_'+p] = rng.uniform(20, 100, size)
        loss = pd.to_datetime(pd.Series(years).astype(str)+'-06-01')
        claims = pd.DataFrame({'row_id': f.row_id, 'claim_id': [line+'c'+str(i) for i in range(size)], 'line': line,
                               'year': years, 'included_in_T0': True, 'peril': rng.choice(perils, size), 'loss_date': loss,
                               'report_date': loss+pd.to_timedelta(rng.integers(0, 90, size), unit='D'),
                               'T0_cents': marks, 'reserve_cents': reserves})
        folder = OUT/'synthetic'/line
        a = fit_base(f, claims, line, folder/'base', OUT/'synthetic')
        full = f.copy(); qg, _ = p4.frozen.completion(full, a['C0']); full['e_cost_scope'] = full.exposure.to_numpy()*qg
        _, old = h.learn(full, 1, line, 'e_cost_scope')
        assert b.digest(old['shape']) == b.digest(a['N3']['shape']) and old['cellshape'] == a['N3']['cellshape']
        assert old['kshape'] == a['N3']['kshape']
        future = f.iloc[:200].copy(); future['row_id'] = [line+'future'+str(i) for i in range(200)]
        future['year'] = 2025; future['is_test'] = True; future['exposure_calendar'] = .8
        future[['T0', 'reserve']] = [-1e30, 1e30]; future[['e_cost_scope', 'e_source_mix']] = 0.
        parts = pd.DataFrame({'row_id': future.row_id})
        for k in range(5):
            parts[f'ratio_H1_G3_{k}'] = rng.uniform(.9, 1.1, len(future))
        expected = future.row_id.tolist(); p, _ = forecast(future, parts, a, expected)
        shuffled, _ = forecast(future.sample(frac=1, random_state=1), parts.sample(frac=1, random_state=2), a, expected)
        assert p.equals(shuffled)
        half = future.copy(); half['exposure_calendar'] *= .5
        ph, _ = forecast(half, parts, a, expected)
        assert np.allclose(ph.candidate_S2_H1, p.candidate_S2_H1*.5, rtol=3e-15)
        for invalid in ['partial', 'duplicate', 'badexposure', 'wrongyear']:
            bad = future.copy()
            if invalid == 'partial': bad = bad.iloc[:-1]
            elif invalid == 'duplicate': bad.iloc[0, bad.columns.get_loc('row_id')] = bad.row_id.iloc[1]
            elif invalid == 'badexposure': bad.iloc[0, bad.columns.get_loc('exposure_calendar')] = 0.
            else: bad['year'] = 2024
            try: forecast(bad, parts, a, expected)
            except AssertionError: pass
            else: raise AssertionError('Invalid cohort accepted: '+invalid)
        try: fit_base(future, claims, line, folder/'must_not_fit_future', OUT/'synthetic')
        except AssertionError: pass
        else: raise AssertionError('Future training accepted')
        ticks = round_ticks(p.candidate_S2_H1.to_numpy())
        with localcontext() as ctx:
            ctx.prec = 60
            independent = [int((Decimal.from_float(float(x))*1_000_000).quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)) for x in p.candidate_S2_H1]
        assert ticks.tolist() == independent
        checks.append({'line': line, 'strict_full_training_C0_N3_S2_and_future_price_flow': True,
                       'synthetic_N3_parity_with_existing_component': True, 'future_poison_ignored_and_zero_observation_markers_ultimate': True,
                       'canonical_shuffle_exact': True, 'calendar_half_exposure_identity': True,
                       'partial_duplicate_badexposure_wrongyear_and_future_training_rejected': True, 'independent_rounding': True})
    return {'author': 'Codex', 'checks': checks, 'synthetic_reporting_fits': 15,
            'synthetic_closed_learners': 9, 'new_contest_fits': 0}


def prepare():
    assert not OUT.exists() and not PLAN.exists(); OUT.mkdir()
    priority = w.read(R/'registro/semana2_mision_privada_actual.json')
    assert priority['2024_open'] and priority['P5']['status'] == 'P5_full_emerging_reserve_recalibration_complete'
    assert not w.read(R/'registro/semana2_control_entregas_codex_actual.json')['allow_new_submission']
    assert w.sha(SAMPLE) == '0a4496eb14d6450bb4583b2e90ae31fde95d71c1629656a03d54ffd1515f666c'
    sample = pd.read_csv(SAMPLE, dtype=str); assert sample.columns.tolist() == ['row_id', 'prediction'] and len(sample) == 209063 and sample.row_id.is_unique
    before = w.read(PUL/'preflight.json'); source = w.read(HOME/'source_models/report.json'); rows = []; files = []
    for line in h.LINES:
        hist = pd.read_parquet(p4.P1/f'canonical_{line}.parquet'); assert hist.year.isin([2023, 2024]).all() and not hist.is_test.any()
        meta = ROOT/before['inputs'][line]['future_metadata']; assert w.sha(meta) == before['inputs'][line]['metadata_sha256']
        future = pd.read_parquet(meta); assert future.row_id.is_unique and future.year.eq(2025).all() and future.is_test.all()
        component_path = PUL/f'component_forward_{line}.parquet'
        columns = ['row_id', 'annual_raw_T2b', *[f'ratio_H1_G3_{k}' for k in range(5)]]
        parts = pd.read_parquet(component_path, columns=columns); assert parts.row_id.is_unique and set(parts.row_id) == set(future.row_id)
        parts = parts.set_index('row_id').loc[future.row_id].reset_index()
        relative_path = HOME/f'source_models/target_{line}_three_seed_components.parquet'
        assert w.sha(relative_path) == source['outputs'][relative_path.name]['sha256']
        relative = pd.read_parquet(relative_path); assert relative.row_id.is_unique
        relative = relative.set_index('row_id').loc[future.row_id]
        assert relative.year.eq(2025).all() and relative.is_test.all()
        future['annual_raw_T2b'] = parts.annual_raw_T2b.to_numpy(); future['log_relative_A1S'] = relative.log_relative_A1S.to_numpy()
        future['e_cost_scope'] = 0.; future['e_source_mix'] = 0.
        assert np.isfinite(parts.iloc[:, 1:].to_numpy(float)).all() and (parts.iloc[:, 1:].to_numpy(float) > 0).all()
        assert np.isfinite(future.log_relative_A1S).all()
        day = ((pd.to_datetime(future.period_end)-pd.to_datetime(future.period_start)).dt.days+1)/365
        assert np.array_equal(day, future.exposure_calendar) and future.exposure_calendar.gt(0).all()
        if line == 'contents': assert str(future.works_from_home.dtype) == 'bool'
        future.to_parquet(OUT/f'future_{line}.parquet', index=False); parts.to_parquet(OUT/f'components_{line}.parquet', index=False)
        files += [p4.P1/f'canonical_{line}.parquet', meta, component_path, relative_path,
                  OUT/f'future_{line}.parquet', OUT/f'components_{line}.parquet']
        rows.append({'line': line, 'train_rows': len(hist), 'future_rows': len(future),
                     'training_row_digest': b.digest(sorted(hist.row_id)), 'future_row_digest': b.digest(sorted(future.row_id)),
                     'future_metadata': w.rel(OUT/f'future_{line}.parquet'), 'future_components': w.rel(OUT/f'components_{line}.parquet')})
    assert sum(x['train_rows'] for x in rows) == 109296 and sum(x['future_rows'] for x in rows) == 209063
    ids = pd.concat([pd.read_parquet(OUT/f'future_{line}.parquet', columns=['row_id']) for line in h.LINES]).row_id
    assert ids.is_unique and set(ids) == set(sample.row_id)
    dump(OUT/'preflight.json', {'author': 'Codex', 'rows': rows, 'official_keyset_exact': True,
                               'existing_future_rate_and_relative_caches_verified': True,
                               'compatible_full_target_cache_identified_in_bounded_own_inventory': False,
                               'inventory_scope': 'Active own phase2main JSON,987files excluding archived cuts,nested/synthetic/source-modelcaches; G4oldfinal2023only; legacyClaudeCDFisdevelopedmatureempiricalanddifferent. Not a claim of global absence.',
                               'no_old_C0_G3_H1_or_source_suite_repeated': True, 'new_fits': 0, 'new_source_inference': 0,
                               'new_final_test_prices': 0, 'new_submissions': 0})
    dump(OUT/'synthetic_report.json', synthetic())
    files += [Path(__file__), Path(p4.__file__), Path(n.__file__), Path(h.__file__), Path(h.d.__file__), Path(b.__file__), Path(g.__file__), Path(v.__file__),
              Path(core.__file__), Path(w.__file__), Path(p4.frozen.__file__), CLAIMS, SAMPLE,
              PUL/'report.json', PUL/'preflight.json', HOME/'source_models/report.json',
              BASE/'media_anidada_H1_20261026_v3/report.json', BASE/'P4_transferencia_anual_H1_20261026_v1/report.json',
              BASE/'P5_recalibracion_reservas_H1_20261026_v1/report.json', OUT/'preflight.json', OUT/'synthetic_report.json',
              R/'registro/semana2_mision_privada_plan_v1.json', R/'registro/semana2_control_entregas_codex_actual.json']
    plan = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'type': 'P6_full_target_nominal_S2_H1_producer',
            'hypothesis': 'Prepare a concrete producer of the actual evaluated S2/H1procedure instead of interpreting proxyvalidation as direct historicalvalidation of the different F3cbackbone. This is the standard final full-training refit, not a new capacity/weight/target search.',
            'model': 'NominalT0, same reverse-truncation C0and observed rounded exposure. Fit full-targetN3and full-targetA1Scomponent/S2using all1092962023/2024rows. SourceA1Sthree-seed relativity/T2brates fixed; S2=.5*A1Scomponent+.5*N3then fixed residualstages. Same K300/K400. No source refit or inference.',
            'production': 'For each2025line, U_base=S2full_target ultimate, using calendaronce and ultimate applicationnormalizers over the complete official cohort. U_candidate=arithmeticmean5(U_base*cached_H1_k_ultimate/G3_k_ultimate). Reuse existing production80percent membercorrections; no refit of those members. Cached fields are annualrate and H1/G3ratio only; no F3cprices or RENshape consumed.',
            'validation_relation': 'P2trained outerbase80percent and innercorrections64percent; final training expands base to100percent and corrections80percent. Normal final training-size extrapolation, not a new heldtest or proof that more training improves. P4year-transfer positive but source/valuation conditional; P3aandP5motorNB2023adverses and poolednominalgainminimumfailure remain.',
            'cohort': 'Complete209063officialIDs only, orderfromofficialsample. Fixed cohortrequiredfor applicationnormalizers; rejectpartial/duplicate/missing/unexpectedIDs and wrongyear/nonpositiveexposure. Canonicalordering before summation makes wholecohortshuffle byte-identical. No per-row batching equivalence claim.',
            'rounding': 'Positivefinite costs, exact binaryfloat ratio to integer microCU with ties-to-even; verify everyvalue by independent Decimal.from_float and CSVreadback. Round once after costmean. No padding, scaling from public, or clipping.',
            'criterion': 'Technical reviewable prototype only: strict historical/future ingress, sourceSHA, exactkeys/years, parameterdigests, newC0probabilitymath, scalarcalibrationmoments, real savedreplay with fittingblocked, fullcohortshuffleidentity and exactroundtrip required. No in-samplescoreor publicoptimization, formalpromotion or upload.',
            'budget': {'new_reporting_peril_fits': 15, 'new_closed_calibration_calls': 6, 'price_constants_max': 400,
                       'new_iterative_source_or_target_fits': 0, 'new_source_inference': 0,
                       'new_final_test_candidate_rows': 209063, 'diagnostic_base_price_rows': 209063,
                       'new_candidate_CSVs': 1, 'new_submissions': 0},
            'limits': ['Private improvement unknown; adaptive2023/2024and unidentifiable ultimate/reserve/late-tail assumptions',
                       'Insufficient2025newbusinesssupport/ESS; no approval manufactured by final refit',
                       'Frozen source includes2024and undatedmasters; no pristine prospective or professional independent validation',
                       'Candidate is S2/H1with its own base, not F3c/H1or a claim that F3cpublic0.16914applies',
                       'Batch normalizers make the complete targetcohort part of the forecastcontract'],
            'scopes': rows, '2024_open': True, 'B00_all_alternatives_preserved': True, 'submission_allowed': False,
            'sources': {w.rel(p): w.sha(p) for p in files}}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. RegistroP6antes de ajustes reales: productor nominal del algoritmo S2/H1evaluado. '
                    'Se han conciliado109296periodos históricos y209063IDs futuros con tasasT2b, relatividadA1Sy los cinco cocientesH1/G3ya guardados. '
                    'No se identificó una calibración completa compatible en el ámbito propio revisado; el ajuste final necesario es15curvas C0y6calibraciones cerradas. '
                    'La fuente, miembros, objetivo nominal, reglas y pesos no cambian. No se consumen preciosF3cni la formaRENdePUL2. '
                    'La base se amplía de80%a100%y los miembros de64%a80%respecto a la evaluación anidada; no es una nueva validación. '
                    'La prueba sintética del mismo ingreso/aprendizaje/forecast pasó en tres ramos, con futuro observado0, controles de claves y calendario, '
                    'paridadN3, rechazo de entrenamiento futuro y redondeo independiente. El productor exigirá cartera completa, replay real sin ajustes y fuentes iguales. '
                    'Se prepara un único CSVtécnico, sin elegirlo por un score, certificar la privada, promover o enviar. '
                    'Permanecen los adversos y fallos deP2/P3a/P5. B00/F3c/alternativas intactos,2024abierto adaptativo. Plan: '+w.rel(PLAN)+'.', encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P6-PRODUCTOR-PREVIO', '--asunto',
                             'P6 registrado: productor S2/H1 nominal, cachés existentes y ajuste final acotado', '--cuerpo', str(body)],
                            check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT/'registration.json', {'plan_sha256': w.sha(PLAN), 'forum': json.loads(result.stdout)})
    print(json.dumps({'registered': True, 'preflight_rows': rows, 'synthetic': w.read(OUT/'synthetic_report.json'), 'forum': json.loads(result.stdout)}))


def real_counts():
    events = [json.loads(s) for s in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines()]
    selected = [e for e in events if e['kind'] in ['N3_completed', 'S2_completed']]
    keys = ['shape_factors', 'levels', 'residual_factors', 'training_nuisance_levels', 'shape_training_normalizers_separate',
            'training_stage_normalizers_separate', 'observed_held_stage_normalizers_separate', 'stage_calls']
    constants = {k: sum(e['constants'][k] for e in selected) for k in keys}
    constants['price_total'] = sum(constants[k] for k in ['shape_factors', 'levels', 'residual_factors', 'training_nuisance_levels'])
    return {'reporting_started': sum(e['kind'] == 'reporting_started' for e in events),
            'reporting_completed': sum(e['kind'] == 'reporting_completed' for e in events),
            'closed_calibrations': len(selected), 'constants': constants}


def produce():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan = w.read(PLAN); assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    execution = {'author': 'Codex', 'pid': os.getpid(), 'utc': datetime.now(timezone.utc).isoformat(),
                 'script': w.rel(Path(__file__)), 'output': w.rel(OUT), 'kind': 'P6_nominal_full_target_calibration_and_CSV'}
    dump(OUT/'started.json', execution); n.OUT = OUT; n.set_execution(execution)
    try:
        frames = p4.input_frames(); claims = n.attach_claim_year(pd.read_parquet(CLAIMS), frames)
        allprices = []; checks = []; norm_primary = 0; norm_replay = 0; norm_shuffle = 0
        for item in plan['scopes']:
            line = item['line']; f = frames[line]
            assert b.digest(sorted(f.row_id)) == item['training_row_digest']
            a = fit_base(f, claims, line, OUT/f'parameters_{line}', OUT)
            future = pd.read_parquet(ROOT/item['future_metadata']); parts = pd.read_parquet(ROOT/item['future_components'])
            expected = future.row_id.tolist()
            prices, norms = forecast(future, parts, a, expected); norm_primary += sum(len(z) for z in norms.values())
            guards = []
            def reject(*args, **kwargs):
                raise AssertionError('No learning in saved full-producer replay')
            for module, name in [(v, 'fit_reporting'), (b, 'reporting_scope'), (b, 'shape_fit'), (b, 'factor'),
                                 (core, 'learn'), (core, 'fit_component'), (core.g, 'fit_stage')]:
                guards.append((module, name, getattr(module, name))); setattr(module, name, reject)
            try:
                saved = {'N3': w.read(OUT/f'parameters_{line}/N3.json'), 'S2': w.read(OUT/f'parameters_{line}/S2.json')}
                bad = future.copy(); bad['T0'] = -1e30; bad['reserve'] = 1e30
                other, nr = forecast(bad, parts, saved, expected); norm_replay += sum(len(z) for z in nr.values())
                assert prices.equals(other) and norms == nr
                shuffled, ns = forecast(bad.sample(frac=1, random_state=71), parts.sample(frac=1, random_state=72), saved, expected)
                norm_shuffle += sum(len(z) for z in ns.values()); assert prices.equals(shuffled) and norms == ns
            finally:
                for module, name, old in reversed(guards): setattr(module, name, old)
            prices.to_parquet(OUT/f'forecast_{line}.parquet', index=False); allprices.append(prices)
            checks.append({'line': line, 'trained2023_2024only': True, 'rows': len(future),
                           'saved_full_forecast_fitblocked_future_poison_replay_exact': True,
                           'canonical_whole_cohort_shuffle_exact': True, 'controls': a['controls'],
                           'ultimate_normalizers': norms})
            print(json.dumps({'line': line, 'full_producer_complete': True, 'future_rows': len(future)}), flush=True)
        sample = pd.read_csv(SAMPLE, dtype=str); prices = pd.concat(allprices, ignore_index=True)
        assert prices.row_id.is_unique and len(prices) == 209063 and set(prices.row_id) == set(sample.row_id)
        prices = prices.set_index('row_id').loc[sample.row_id].reset_index()
        ticks = round_ticks(prices.candidate_S2_H1.to_numpy())
        with localcontext() as ctx:
            ctx.prec = 60
            independent = [int((Decimal.from_float(float(x))*1_000_000).quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)) for x in prices.candidate_S2_H1]
        assert ticks.tolist() == independent
        path = OUT/'codex_S2_H1_nominal_2025.csv'
        with path.open('x', encoding='utf8', newline='') as stream:
            writer = csv.writer(stream, lineterminator='\n'); writer.writerow(['row_id', 'prediction'])
            for rowid, tick in zip(prices.row_id, ticks):
                writer.writerow([rowid, f'{int(tick)//1_000_000}.{int(tick)%1_000_000:06d}'])
        with path.open(encoding='utf8', newline='') as stream:
            reader = csv.reader(stream); assert next(reader) == ['row_id', 'prediction']
            for i, (rowid, value) in enumerate(reader):
                assert rowid == sample.row_id.iloc[i] and int(Decimal(value)*1_000_000) == int(ticks[i]) and len(value.split('.')[1]) == 6
            assert i+1 == len(sample)
        assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
        count = real_counts(); assert count['reporting_completed'] == 15 and count['closed_calibrations'] == 6
        assert count['constants']['price_total'] <= plan['budget']['price_constants_max']
        cells = []
        for line in h.LINES:
            f = pd.read_parquet(OUT/f'future_{line}.parquet').set_index('row_id')
            pp = pd.read_parquet(OUT/f'forecast_{line}.parquet').set_index('row_id').loc[f.index]
            for nb in [0, 1]:
                ii = f.new_business.astype(int).eq(nb).to_numpy()
                cells.append({'line': line, 'NB': nb, 'rows': int(ii.sum()), 'base_total': float(pp.base_S2.to_numpy()[ii].sum()),
                              'candidate_total': float(pp.candidate_S2_H1.to_numpy()[ii].sum())})
        report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'status': 'P6_nominal_S2_H1_producer_and_CSV_complete_unadmitted',
                  'CSV': {'path': w.rel(path), 'sha256': w.sha(path), 'bytes': path.stat().st_size, 'rows': len(prices),
                          'total_microCU_exact': int(sum(int(z) for z in ticks)), 'total_CU': sum(int(z) for z in ticks)/1_000_000},
                  'counts': count, 'cells': cells, 'numeric_controls': checks, 'source_inference': 0,
                  'primary_prediction_normalizers_separate': norm_primary, 'replay_prediction_normalizers_separate': norm_replay,
                  'shuffle_prediction_normalizers_separate': norm_shuffle, 'official_IDs_order_exact': True,
                  'independent_rounding_and_readback_exact': True, 'new_candidate_CSVs': 1, 'new_candidate_final_prices': 209063,
                  'diagnostic_base_final_prices': 209063, 'new_source_models': 0, 'new_iterative_target_models': 0,
                  'new_submissions': 0, 'F3c_predictions_consumed': False, 'formal_promotion': False, 'submission_allowed': False,
                  'private_improvement_established': False, '2024_open': True, 'B00_all_alternatives_preserved': True,
                  'goal_achieved': False, 'plan_sha256': w.sha(PLAN), 'limits': plan['limits']}
        dump(OUT/'report.json', report)
        print(json.dumps({'status': report['status'], 'CSV': report['CSV'], 'counts': count, 'new_submissions': 0}), flush=True)
    except Exception as exc:
        dump(OUT/f'failure_{datetime.now(timezone.utc).strftime("%H%M%S%f")}.json',
             {'exception': type(exc).__name__, 'message': str(exc), 'counts': real_counts() if (OUT/'events.jsonl').exists() else {},
              'next': 'Preserve learned curves/parameters; reconcile before any correction or resume'})
        raise
    finally:
        n.set_execution(None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'produce']); args = parser.parse_args()
    with threadpool_limits(limits=2):
        prepare() if args.mode == 'prepare' else produce()
