"""Estrés de transferencia emergente 2023 -> 2024, con fuente congelada y valoración común.

No es un backtest prospectivo a diciembre de 2023: las fuentes incluyen 2024 y
los importes están valorados a diciembre de 2024. No llama productores antiguos.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'
P1 = BASE/'preflight_anidado_H1_20261026_v1'
OUT = BASE/'P4_transferencia_anual_H1_20261026_v1'
PLAN = R/'registro/semana2_transferencia_anual_H1_plan_v1.json'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


n = load('P4_nested_helpers', R/'herramientas/evaluar_media_anidada_H1_v3.py')
complete = load('P4_complete_source_safe_core', R/'herramientas/validar_nucleo_completo_A1S.py')
frozen = load('P4_fixed_observation_stresses', R/'herramientas/sensibilidad_congelada_media_H1.py')
h = n.h; b = h.b; g = h.g; v = b.v; w = h.w; unit = frozen.unit
CLAIMS = b.BASE/'claim_assignment_audit.parquet'
NAMES = ['NOMINAL_VS_BASE', 'MEAN_VS_SINGLE', *frozen.SCENARIOS]


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def event(log, kind, **values):
    log.mkdir(parents=True, exist_ok=True)
    with (log/'events.jsonl').open('a', encoding='utf8') as stream:
        stream.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'kind': kind, **values})+'\n')


def input_frames():
    frames = {}
    for line in h.LINES:
        f = pd.read_parquet(P1/f'canonical_{line}.parquet')
        rel = pd.read_parquet(BASE/f'A1S_nucleo_20261026_v1/source_models/target_{line}_three_seed_components.parquet')
        assert rel.row_id.is_unique
        rel = rel.set_index('row_id').loc[f.row_id, 'log_relative_A1S']
        f['log_relative_A1S'] = rel.to_numpy()
        assert np.isfinite(f.log_relative_A1S).all()
        frames[line] = f
    return frames


def make_scope(full, outer, member):
    # Filtering happens before any learning. No 2024 response can enter fit.
    train = full.year.eq(2023) & full.fold.ne(outer)
    if member >= 0:
        inner = pd.read_parquet(P1/f'inner_groups_outer{outer}.parquet').set_index('group_id').inner_fold
        train &= full.group_id.map(inner).ne(member)
    held = full.year.eq(2024) & full.fold.eq(outer)
    f = full.loc[train | held].copy().reset_index(drop=True)
    f['original_fold'] = f.fold.to_numpy()
    f['fold'] = f.year.eq(2024).astype(int)
    assert f.loc[f.fold.eq(0), 'year'].eq(2023).all()
    assert f.loc[f.fold.eq(1), 'year'].eq(2024).all()
    assert not set(f.loc[f.fold.eq(0), 'group_id']).intersection(f.loc[f.fold.eq(1), 'group_id'])
    return f


def scope_support(f, claims, line, outer, member):
    train = f.fold.eq(0); held = f.fold.eq(1); keys = set(f.loc[train, 'row_id'])
    selected = claims.loc[claims.row_id.isin(keys)]
    selected = selected.loc[selected.included_in_T0]
    perils = sorted(x[2:] for x in f if x.startswith('f_'))
    counts = selected.peril.value_counts().reindex(perils, fill_value=0)
    assert selected.year.eq(2023).all()
    assert counts.min() >= 5, (line, outer, member, counts.to_dict())
    assert all((f.loc[train & f.new_business.eq(nb), 'T0'] > 0).any() for nb in [0, 1])
    return {'line': line, 'outer': outer, 'member': member, 'train_rows': int(train.sum()),
            'held_rows': int(held.sum()), 'peril_counts': {p: int(z) for p, z in counts.items()},
            'train_row_digest': b.digest(sorted(keys)),
            'train_group_digest': b.digest(sorted(set(f.loc[train, 'group_id']))),
            'held_row_digest': b.digest(sorted(f.loc[held, 'row_id']))}


def learn_scope(f, claims, line, folder, log, tag, role, with_core=False):
    """Actual synthetic/contest entry point. Each role has its own numerical cache."""
    folder.mkdir(parents=True, exist_ok=True)
    train = f.fold.eq(0); held = f.fold.eq(1)
    assert f.loc[train, 'year'].eq(2023).all() and f.loc[held, 'year'].eq(2024).all()
    keys = set(f.loc[train, 'row_id'])
    assert keys and held.any()
    assert not set(f.loc[train, 'group_id']).intersection(f.loc[held, 'group_id'])
    perils = sorted(x[2:] for x in f if x.startswith('f_'))
    cp = folder/'C0.json'
    if not cp.exists():
        original = v.fit_reporting; sequence = [0]
        def fit_cached(*args, **kwargs):
            assert not kwargs
            peril = perils[sequence[0]]; sequence[0] += 1
            path = folder/('curve_'+peril+'.json'); signature = n.args_digest(args)
            if path.exists():
                old = w.read(path); assert old['argument_digest'] == signature
                return old['model'], np.asarray(old['prob_n'], float)
            event(log, 'reporting_started', tag=tag, role=role, peril=peril)
            model, probability = original(*args)
            dump(path, {'argument_digest': signature, 'model': model, 'prob_n': np.asarray(probability).tolist()})
            event(log, 'reporting_completed', tag=tag, role=role, peril=peril, sha256=w.sha(path))
            return model, probability
        v.fit_reporting = fit_cached
        try:
            _, c0 = b.reporting_scope(f, claims, 1)
        finally:
            v.fit_reporting = original
        assert sequence[0] == len(perils)
        dump(cp, c0)
    c0 = w.read(cp)
    assert c0['fit_row_ids'] == sorted(keys)
    eligible = claims.loc[claims.row_id.isin(keys)]
    eligible = eligible.loc[eligible.included_in_T0]
    assert eligible.year.eq(2023).all() and c0['fit_claim_ids'] == sorted(eligible.claim_id.tolist())
    qg, qh = frozen.completion(f, c0)
    assert (qg > 0).all() and (qh > 0).all()
    work = f.copy()
    work['e_cost_scope'] = work.exposure.to_numpy()*qg
    work['e_source_mix'] = work.exposure.to_numpy()*qh
    artifacts = {}; ultimate = {}; controls = {}; normalizers = 0
    for name, link in [('G3', 'e_cost_scope'), ('H1', 'e_source_mix')]:
        path = folder/('learning_'+name+'.json')
        if not path.exists():
            event(log, 'closed_started', tag=tag, role=role, model=name)
            _, a = h.learn(work, 1, line, link)
            dump(path, a)
            event(log, 'closed_completed', tag=tag, role=role, model=name, constants=n.count_constants(a))
        a = w.read(path)
        assert a['training_row_ids_digest'] == b.digest(sorted(keys))
        assert a['training_groups_digest'] == b.digest(sorted(set(work.loc[train, 'group_id'])))
        valid = work.loc[held].copy()
        observed, no = h.replay(valid, a)
        assert no == a['held_normalizers']
        Er = valid.exposure.to_numpy(float); E = valid.exposure_calendar.to_numpy(float)
        valid['exposure'] = E
        u, nu = h.replay(valid, a, ultimate=True)
        L = np.ones(len(valid)); cellkeys = [f'{int(y)}|{int(nb)}' for y, nb in zip(valid.year, valid.new_business)]
        for variable, norm in nu.items():
            L *= np.array([norm[k]/no[variable][k] for k in cellkeys]); normalizers += len(norm)
        q = (qg if name == 'G3' else qh)[held.to_numpy()]
        assert np.allclose(observed, u*(Er/E)*q*L, rtol=3e-12, atol=1e-9)
        tr = work.loc[train]; m = tr.annual_raw_T2b.to_numpy()*tr[link].to_numpy()
        for shape in a['shape']:
            m = b.shape_apply(tr, m, shape)
        moment = math.fsum((tr.T0.to_numpy()/np.sqrt(m)).tolist())/math.fsum(np.sqrt(m).tolist())
        assert math.isclose(moment, a['kshape'], rel_tol=3e-12)
        artifacts[name] = a; ultimate[name] = u
        controls[name] = {'bridge_error': float(np.max(np.abs(observed/(u*(Er/E)*q*L)-1))),
                          'scalar_moment_relative_error': abs(moment/a['kshape']-1)}
    if with_core:
        # S2 base is also relearned from 2023 only, never borrowed from pooled-year fits.
        tr = work.loc[train].copy(); va = work.loc[held].copy()
        tr['base_N3'] = h.apply_component(tr, artifacts['G3'], 'e_cost_scope')
        va['base_N3'] = h.apply_component(va, artifacts['G3'], 'e_cost_scope')
        joined = pd.concat([tr, va], ignore_index=True)
        path = folder/'learning_S2.json'
        if not path.exists():
            event(log, 'closed_started', tag=tag, role=role, model='S2')
            _, a = complete.learn(joined, 1, line)
            dump(path, a)
            comp = a['component']
            constants = {'shape_factors': comp['shape_factor_constants'], 'levels': comp['level_constants'],
                         'residual_factors': sum(len(s['factors']) for s in a['stages']),
                         'training_nuisance_levels': sum(len(s['nuisance_year_business']) for s in a['stages']),
                         'shape_training_normalizers_separate': comp['shape_training_normalizers'],
                         'training_stage_normalizers_separate': sum(len(z) for z in a['training_normalizers'].values()),
                         'observed_held_stage_normalizers_separate': sum(len(z) for z in a['held_normalizers'].values()),
                         'stage_calls': len(a['stages'])}
            event(log, 'closed_completed', tag=tag, role=role, model='S2', constants=constants)
        a = w.read(path)
        assert a['fit_row_ids_digest'] == b.digest(sorted(keys))
        check, no = complete.replay(va, a)
        assert no == a['held_normalizers']
        sf = va.copy(); sf['exposure'] = sf.exposure_calendar
        sf['e_cost_scope'] = sf.exposure_calendar
        sf['base_N3'] = h.apply_component(sf, artifacts['G3'], 'e_cost_scope', ultimate=True)
        u, nu = complete.replay(sf, a)
        assert np.isfinite(u['S2']).all() and (u['S2'] > 0).all()
        normalizers += sum(len(z) for z in nu.values())
        artifacts['S2'] = a; ultimate['S2'] = u['S2']
        comp = a['component']; m = np.exp(tr.log_relative_A1S.to_numpy())*tr.e_cost_scope.to_numpy()
        for shape in comp['shape']:
            m = b.shape_apply(tr, m, shape)
        moment = math.fsum((tr.T0.to_numpy()/np.sqrt(m)).tolist())/math.fsum(np.sqrt(m).tolist())
        assert math.isclose(moment, comp['level'], rel_tol=3e-12)
        controls['S2'] = {'scalar_moment_relative_error': abs(moment/comp['level']-1), 'observed_replay_exact': True}
    return {'C0': c0, 'artifacts': artifacts, 'ultimate': ultimate, 'controls': controls,
            'held_row_ids': work.loc[held, 'row_id'].tolist(), 'ultimate_normalizers': normalizers}


def corrupt(f, claims):
    bad, cc = n.poison(f, claims)
    # All remaining 2024 claims, including rows entirely absent from this scope,
    # are also poisoned. Future-year payload must be excluded before parsing.
    future = cc.year.eq(2024)
    cc.loc[future, 'T0_cents'] = np.int64(-(1 << 61))
    cc.loc[future, 'reserve_cents'] = np.int64(1 << 61)
    cc.loc[future, 'included_in_T0'] = True
    for column in ['peril', 'loss_date', 'report_date']:
        cc[column] = cc[column].astype(object); cc.loc[future, column] = '__FUTURE_PROTECTED__'
    return bad, cc


def synthetic():
    rng = np.random.default_rng(2026102630); checks = []
    for line, perils in [('motor', ['bodily_injury', 'glass_hail', 'own_damage', 'theft', 'third_party_prop']),
                         ('buildings', ['accidental_damage', 'escape_of_water', 'fire', 'flood', 'storm', 'subsidence']),
                         ('contents', ['accidental_damage', 'escape_of_water', 'flood', 'theft'])]:
        size = 1200; year = np.where(np.arange(size) < 900, 2023, 2024)
        E = np.where(year == 2024, 366/365, 1.)
        f = pd.DataFrame({'row_id': [line+'syn'+str(i) for i in range(size)], 'line': line, 'year': year,
                          'group_id': ['g'+str(i) for i in range(size)], 'fold': (year == 2024).astype(int),
                          'new_business': rng.integers(0, 2, size), 'exposure': np.round(E, 4), 'exposure_calendar': E,
                          'period_start': pd.to_datetime(pd.Series(year).astype(str)+'-01-01'),
                          'period_end': pd.to_datetime(pd.Series(year).astype(str)+'-12-31'), 'is_test': False,
                          'annual_raw_T2b': rng.uniform(40, 200, size), 'log_relative_A1S': rng.normal(0, .4, size),
                          'prior_claims_5y': rng.integers(0, 3, size), 'ncb_years': rng.integers(0, 15, size),
                          'gender': rng.choice(['F', 'M'], size), 'works_from_home': rng.choice([True, False], size),
                          'marketing_segment': rng.choice(['a', 'b', 'c'], size)})
        marks = rng.integers(100, 90000, size, dtype=np.int64); reserves = marks//5
        f['T0'] = marks/100; f['reserve'] = reserves/100
        for p in perils:
            f['f_'+p] = rng.uniform(.1, 1, size); f['s_'+p] = rng.uniform(20, 100, size)
        loss = pd.to_datetime(pd.Series(year).astype(str)+'-06-01')
        claims = pd.DataFrame({'row_id': f.row_id, 'claim_id': [line+'c'+str(i) for i in range(size)], 'line': line,
                               'year': year, 'included_in_T0': True, 'peril': rng.choice(perils, size), 'loss_date': loss,
                               'report_date': loss+pd.to_timedelta(rng.integers(0, 90, size), unit='D'),
                               'T0_cents': marks, 'reserve_cents': reserves})
        claims = n.attach_claim_year(claims.drop(columns=['year']), {line: f})
        log = OUT/'synthetic'; folder = log/line
        a = learn_scope(f, claims, line, folder/'primary', log, line, 'primary', True)
        bad, cc = corrupt(f, claims)
        z = learn_scope(bad, cc, line, folder/'poison', log, line, 'poison', True)
        assert b.digest(a['C0']) == b.digest(z['C0']) and b.digest(a['artifacts']) == b.digest(z['artifacts'])
        assert all(np.array_equal(a['ultimate'][k], z['ultimate'][k]) for k in a['ultimate'])
        valid = f.loc[f.fold.eq(1)].copy(); valid['exposure'] = valid.exposure_calendar
        valid['year'] = 2025; valid['e_source_mix'] = 0.
        prices, _ = h.replay(valid, a['artifacts']['H1'], ultimate=True)
        assert np.isfinite(prices).all() and (prices > 0).all()
        checks.append({'line': line, 'single_training_year_real_schema_flow': True,
                       'all_future_payload_poison_exact': True, 'fresh_S2_base_and_H1_G3_ultimate_forward': True,
                       'year2025_zero_observed_marker_valid': True})
    return {'author': 'Codex', 'checks': checks, 'synthetic_reporting_fits': 30,
            'synthetic_closed_learners': 18, 'new_contest_fits': 0}


def register():
    assert not OUT.exists() and not PLAN.exists()
    OUT.mkdir()
    frames = input_frames(); claims = n.attach_claim_year(pd.read_parquet(CLAIMS), frames)
    scopes = [scope_support(make_scope(f, outer, member), claims, line, outer, member)
              for line, f in frames.items() for outer in range(5) for member in [-1, 0, 1, 2, 3, 4]]
    assert len(scopes) == 90 and min(min(s['peril_counts'].values()) for s in scopes) >= 5
    dump(OUT/'preflight.json', {'author': 'Codex', 'scopes': scopes, 'all90_supported': True,
                              'minimum_peril_reports': min(min(s['peril_counts'].values()) for s in scopes),
                              'training_target_years': [2023], 'held_target_years': [2024], 'new_fits': 0})
    with threadpool_limits(limits=2):
        dump(OUT/'synthetic_report.json', synthetic())
    old = ROOT/'Hackaton/Semana 2/Claude/ml_independiente_20261023'
    files = [Path(__file__), Path(n.__file__), Path(h.__file__), Path(b.__file__), Path(g.__file__), Path(v.__file__),
             Path(complete.__file__), Path(frozen.__file__), CLAIMS, frozen.TARGET,
             OUT/'preflight.json', OUT/'synthetic_report.json',
             BASE/'H3B_mezcla_negocio_20261026_v1/report.json', BASE/'media_anidada_H1_20261026_v3/report.json',
             BASE/'estimando_cartera2025_v3/weights.parquet', BASE/'estimando_cartera2025_v3/report.json',
             R/'registro/semana2_mision_privada_plan_v1.json', R/'registro/semana2_control_entregas_codex_actual.json']
    for rel in ['codigo/tendencia.py', 'codigo/e13_clima_anual.py', 'codigo/e27_backtest.py',
                'hold_prueba_tendencia.json', 'e13_clima_anual.json', 'nivel2025/e27_backtest_2024.json']:
        files.append(old/rel)
    for line in h.LINES:
        files += [P1/f'canonical_{line}.parquet', BASE/f'A1S_nucleo_20261026_v1/source_models/target_{line}_three_seed_components.parquet']
    for outer in range(5):
        files.append(P1/f'inner_groups_outer{outer}.parquet')
    plan = {
        'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'type': 'P4_conditional_target_year_transfer_complete_H1_mean',
        'hypothesis': 'A correction validated with random target groups over both years may rely on contemporaneous target labels. Test whether the complete five-member H1 algorithm transfers to target2024 when every target learner sees2023only.',
        'why_distinct': 'P2 used pooled2023/2024training. Existing E13annualweather, trend and E27premium-level holdout are different algorithms, with recorded adverse/uncertain results. They are not rerun. This test adds no model capacity or new candidate weights.',
        'static_review': {'trend_hold_deltas': [-.0012641297930696682, -.0016005310040791976],
                          'annual_weather_hold_delta': .00025603561147746756,
                          'annual_weather_hold95': [-.0025386089821575557, .0032032405765009763],
                          'E27_held_T2b': .12599104719844045, 'E27_held_shrunk_level': .12478897819166834},
        'partition': 'Existing five global outer component folds unchanged. Held=year2024&outerfoldk. Outer training=year2023&fold!=k. Each of five members additionally excludes its saved P1innerfold. Every target2024row is absent from all learning, as are held globalgroups. No reassignments or favourable cell deletion.',
        'valuation_and_source': 'Common2024-12-31claim valuation, not a reconstructed2023snapshot. Frozen T2b/A1S/FSp source includes2024and undated master fields; their precomputed profiles are fixed conditional covariates, not proven2023available. Do not call this prospective/pristine or validate source learning with targetpoison.',
        'training': 'Same nominalT0, rounded observed exposure, reverse-truncation reporting, K300NCB/prior/residual and K400business levels. Own C0in every scope, no reuse of pooled-year learned values. S2base also rebuilt using only2023targetresponses: same frozen50/50N3+A1Scomponent and residual stages. No calendarcoefficient, alpha, seed, clipping, feature or hyperparameter search.',
        'algorithm': 'Outer S2ultimate trained on2023outertraining * arithmetic_mean5(U_H1member/U_G3member), all members trained on their2023innertraining. Ultimate forward uses calendar once and ultimate prediction normalizers. Outer2023onlyC0evaluation adapter applied aftermean; baseline qglobal, correction qsource. Outer C0never an inner learner input.',
        'contrasts': {'primary': 'nominal complete H1mean versus freshly2023calibrated S2base',
                      'secondary': 'five-member mean versus2023outertraining single H1/G3correction',
                      'sensitivity': 'All four frozen P3areserve/tail conventions with identical fitted ultimate prices; no valuation-specific recalibration'},
        'bootstrap': {'replicates': 2000, 'seed': 2026102631, 'unit': 'unchanged global customer/address component', 'joint_contrasts': 6, 'family': 'exploratory Bonferroni6'},
        'criterion': {'diagnostic_delta_min': .002, 'lower95_positive': True, 'positive_folds_min': 4,
                      'post31_nonnegative': True, 'all_nominal_and_four_stress_line_business_cells_floor': -.001,
                      'not_applicable': 'Both-year held gate cannot be tested with held2024only. Report this absence, no synthetic zero gain2023 or substitute approval.',
                      'no_formal_promotion': True, 'no_automatic_submission': True},
        'controls': ['Whole actual2024claim/T0/reserve/peril/datepoison and savedartifact/ultimateprice exact equality for all90new scopes',
                     'No inherited pooled-year target calibration, source inference or oracle multiplier input',
                     'Exact training row/group digests and complete key coverage, integer cents ingestion',
                     'Independent scalar Tweedie moment, observed/ultimate bridge and mean arithmetic, standard metric check, immutable SHA',
                     'Synthetic exact same yearfiltered entrypoint with all3ramos and actual types'],
        'budget': {'target_outer_scopes': 15, 'inner_member_scopes': 75, 'primary_reporting_peril_fits': 450,
                   'adverse_reporting_fits_separate': 450, 'primary_closed_learner_calls': 195,
                   'adverse_closed_learner_calls_separate': 195, 'primary_price_constants_max': 5000,
                   'new_iterative_source_models': 0, 'new_source_inference': 0, 'new_final_test_prices': 0, 'new_submissions': 0},
        'limits': ['Adaptive inspected2023/2024; one heldtargetyear and reduced training support do not reproduce production2025',
                   'Frozen source2024and final2024valuation exclude a prospective2023asof claim',
                   'Complete feasible S2proxy, not exact deliveredF3c; unidentified delay-tail/reserve/sourceprofile assumptions persist',
                   '2025newbusiness composition support/ESS failure remains; weights sensitivity cannot rescue failure',
                   'No private performance guarantee or independent professional validation'],
        '2024_open': True, 'B00_all_alternatives_preserved': True, 'submission_allowed': False,
        'sources': {w.rel(p): w.sha(p) for p in files},
    }
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. Registro P4 antes de ajustes o scores reales: transferencia del algoritmo completo H1 de etiquetas emergentes2023 a2024. '
                    'Los90ámbitos tienen soporte numérico, con mínimo14reportes por peril. Se conservarán grupos/folds y particiones internas, '
                    'filtrando todo2024antes del aprendizaje. Se reconstruirán C0, G3/H1 y baseS2 solo con2023; los modelos fuente permanecen fijos. '
                    'Primario: media de cinco correcciones frente a baseS2. Secundario: media frente a un miembro exterior. Cuatro escenarios congelados, '
                    'todas las celdas, Post31e intervalos por grupos se declararon antes de puntuar. '
                    'Esto es un estrés condicionado a fuente y valoración2024, no un pronóstico intacto con información disponible a diciembre2023. '
                    'La revisión estática preserva los resultados previos: tendencia y nivelE27adversos; climaanualsin mejora estable. No se repiten esas recetas. '
                    'Presupuesto450curvas y195aprendices cerrados primarios, con controles adversos separados de igual coste. '
                    'La prueba sintética de los tres ramos pasó por el mismo ingreso, aprendizaje, baseS2y avance a último. '
                    'Cero modelos fuente, inferencias fuente, precios2025oenvíos nuevos. B00/alternativas conservados,2024abierto adaptativo,H1diferido. '
                    'Plan: '+w.rel(PLAN)+'.', encoding='utf8')
    res = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                          '--id', 'COD-S2-20261026-PRIVADA-P4-ANUAL-PREVIO', '--asunto',
                          'P4 registrada: transferencia a2024 sin etiquetas emergentes de ese año, con fuente congelada',
                          '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT/'registration.json', {'plan_sha256': w.sha(PLAN), 'forum': json.loads(res.stdout)})
    print(json.dumps({'registered': True, 'scopes': 90, 'min_reports': 14, 'synthetic': w.read(OUT/'synthetic_report.json'), 'forum': json.loads(res.stdout)}))


def summarize(meta, data, weight):
    codes, groups = pd.factorize(meta.group_id, sort=True); G = len(groups); size = len(meta)
    counts = np.bincount(codes, minlength=G); gains = []; YY = []; SQ = []; null = []; rowgains = []
    for y, base, candidate in data:
        gain = unit(y, base)-unit(y, candidate); rowgains.append(gain)
        gains.append(np.bincount(codes, weights=gain, minlength=G))
        YY.append(np.bincount(codes, weights=y, minlength=G)); SQ.append(np.bincount(codes, weights=np.sqrt(y), minlength=G))
        null.append(float(unit(y, np.full(size, y.mean())).sum()))
        assert abs(unit(y, candidate).mean()-mean_tweedie_deviance(y, candidate, power=1.5)) < 1e-8
    gains = np.column_stack(gains); YY = np.column_stack(YY); SQ = np.column_stack(SQ)
    rng = np.random.default_rng(2026102631); draws = []
    for _ in range(2000):
        ii = rng.integers(0, G, G); number = counts[ii].sum()
        den = 8*(np.sqrt(number*YY[ii].sum(axis=0))-SQ[ii].sum(axis=0))
        assert (den > 0).all(); draws.append(gains[ii].sum(axis=0)/den)
    draws = np.asarray(draws); np.save(OUT/'joint_six_bootstrap.npy', draws); results = {}
    for j, name in enumerate(NAMES):
        y, base, candidate = data[j]; gain = rowgains[j]; cells = []; den = null[j]
        for (line, nb), indices in meta.groupby(['line', 'new_business']).groups.items():
            ii = np.asarray(list(indices)); yy = y[ii]; dd = unit(yy, np.full(len(ii), yy.mean())).sum()
            cells.append({'line': line, 'year': 2024, 'NB': int(nb), 'rows': len(ii), 'delta_global': float(gain[ii].sum()/den),
                          'delta_cell_null': float(gain[ii].sum()/dd), 'AE_base': float(yy.sum()/base[ii].sum()),
                          'AE_candidate': float(yy.sum()/candidate[ii].sum())})
        weighted_mean = np.average(y, weights=weight); weighted_den = np.sum(weight*unit(y, np.full(size, weighted_mean)))
        results[name] = {'delta': float(gain.sum()/den), 'bootstrap95': np.quantile(draws[:, j], [.025, .975]).tolist(),
                         'simultaneous95_six': np.quantile(draws[:, j], [.025/6, 1-.025/6]).tolist(),
                         'post31_delta': float((gains[:, j].sum()-np.sort(gains[:, j])[::-1][:31].sum())/den),
                         'folds': {str(k): float(gain[meta.fold.eq(k)].sum()/den) for k in range(5)}, 'held_year': 2024,
                         'cells': cells, 'worst_cell_delta': min(c['delta_cell_null'] for c in cells),
                         'weighted2025_point_only_unvalidated': float(np.sum(weight*gain)/weighted_den),
                         'base_D2': float(1-unit(y, base).sum()/den), 'candidate_D2': float(1-unit(y, candidate).sum()/den)}
    group_weight = np.bincount(codes, weights=weight, minlength=G)
    support = {'held2024_row_ESS': float(weight.sum()**2/np.sum(weight**2)), 'rows': size,
               'held2024_group_ESS': float(weight.sum()**2/np.sum(group_weight**2)), 'groups': G,
               'weights_reused_not_reestimated': True, 'overall2023_2024_ESS_prior_gate_failed': True}
    return results, support


def counts():
    events = [json.loads(s) for s in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines()]
    result = {}
    for role in ['primary', 'poison']:
        selected = [e for e in events if e.get('role') == role]
        fits = [e for e in selected if e['kind'] == 'closed_completed']
        keys = ['shape_factors', 'levels', 'residual_factors', 'training_nuisance_levels',
                'shape_training_normalizers_separate', 'training_stage_normalizers_separate',
                'observed_held_stage_normalizers_separate', 'stage_calls']
        constants = {k: sum(e['constants'][k] for e in fits) for k in keys}
        constants['price_total'] = sum(constants[k] for k in ['shape_factors', 'levels', 'residual_factors', 'training_nuisance_levels'])
        result[role] = {'reporting_started': sum(e['kind'] == 'reporting_started' for e in selected),
                        'reporting_completed': sum(e['kind'] == 'reporting_completed' for e in selected),
                        'closed_learners_started': sum(e['kind'] == 'closed_started' for e in selected),
                        'closed_learners_completed': len(fits), 'constants': constants}
    return result


def run(resume=False):
    assert not (OUT/'report.json').exists()
    plan = w.read(PLAN)
    assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    assert w.read(R/'registro/semana2_mision017_fase2_actual.json').get('active_execution') is None
    if resume:
        import psutil
        old = w.read(OUT/'execution_last.json')
        if psutil.pid_exists(old['pid']):
            assert not any(Path(x).name == Path(__file__).name for x in psutil.Process(old['pid']).cmdline())
    else:
        assert not (OUT/'started.json').exists()
    execution = {'author': 'Codex', 'pid': os.getpid(), 'utc': datetime.now(timezone.utc).isoformat(),
                 'script': w.rel(Path(__file__)), 'output': w.rel(OUT), 'kind': 'P4_conditional_target_year_transfer'}
    if not resume:
        dump(OUT/'started.json', execution)
    last = OUT/'execution_last.json'
    if last.exists():
        cut = OUT/'execution_cuts'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'); cut.mkdir(parents=True)
        w.update(last, execution, cut)
    else:
        dump(last, execution)
    n.OUT = OUT
    n.set_execution(execution)
    try:
        frames = input_frames(); claims = n.attach_claim_year(pd.read_parquet(CLAIMS), frames)
        for scope in w.read(OUT/'preflight.json')['scopes']:
            line, outer, member = scope['line'], scope['outer'], scope['member']
            folder = OUT/f'scope_{line}_outer{outer}_member{member}'; folder.mkdir(exist_ok=True)
            if (folder/'committed.json').exists():
                old = w.read(folder/'committed.json')
                assert all(w.sha(ROOT/p) == z for p, z in old['outputs'].items())
                continue
            f = make_scope(frames[line], outer, member)
            assert b.digest(sorted(f.loc[f.fold.eq(0), 'row_id'])) == scope['train_row_digest']
            tag = f'{line}|{outer}|{member}'
            a = learn_scope(f, claims, line, folder/'primary', OUT, tag, 'primary', member == -1)
            bad, cc = corrupt(f, claims)
            z = learn_scope(bad, cc, line, folder/'poison', OUT, tag, 'poison', member == -1)
            assert b.digest(a['C0']) == b.digest(z['C0']) and b.digest(a['artifacts']) == b.digest(z['artifacts'])
            assert all(np.array_equal(a['ultimate'][k], z['ultimate'][k]) for k in a['ultimate'])
            data = pd.DataFrame({'row_id': a['held_row_ids'], **{'U_'+k: val for k, val in a['ultimate'].items()}})
            data.to_parquet(folder/'ultimate.parquet', index=False)
            paths = [folder/'ultimate.parquet', *list((folder/'primary').glob('*.json')), *list((folder/'poison').glob('*.json'))]
            dump(folder/'committed.json', {'line': line, 'outer': outer, 'member': member,
                                           'all_future_payload_poison_exact': True, 'controls': a['controls'],
                                           'primary_ultimate_normalizers': a['ultimate_normalizers'],
                                           'adverse_ultimate_normalizers_separate': z['ultimate_normalizers'],
                                           'outputs': {w.rel(p): w.sha(p) for p in paths}})
            print(json.dumps({'scope': tag, 'complete': True}), flush=True)
        meta = pd.concat([f.loc[f.year.eq(2024)] for f in frames.values()], ignore_index=True)
        assert meta.row_id.is_unique and meta.year.eq(2024).all()
        rowix = pd.Series(np.arange(len(meta)), index=meta.row_id)
        UB = np.full(len(meta), np.nan); UC = UB.copy(); US = UB.copy()
        base = [UB.copy() for _ in range(5)]; candidate = [UB.copy() for _ in range(5)]
        for line, full in frames.items():
            for outer in range(5):
                valid = full.loc[full.year.eq(2024) & full.fold.eq(outer)].copy()
                folder = OUT/f'scope_{line}_outer{outer}_member-1'
                c0 = w.read(folder/'primary/C0.json')
                outer_prices = pd.read_parquet(folder/'ultimate.parquet').set_index('row_id').loc[valid.row_id]
                ratios = []
                for member in range(5):
                    pp = pd.read_parquet(OUT/f'scope_{line}_outer{outer}_member{member}/ultimate.parquet').set_index('row_id').loc[valid.row_id]
                    ratios.append(pp.U_H1.to_numpy()/pp.U_G3.to_numpy())
                ub = outer_prices.U_S2.to_numpy(); members = ub[:, None]*np.column_stack(ratios)
                uc = members.mean(axis=1)
                assert np.allclose(uc, sum(members[:, j] for j in range(5))/5, rtol=2e-15)
                single = ub*outer_prices.U_H1.to_numpy()/outer_prices.U_G3.to_numpy()
                ii = rowix.loc[valid.row_id].to_numpy(); UB[ii] = ub; UC[ii] = uc
                qg, qh = frozen.completion(valid, c0); base[0][ii] = ub*qg; candidate[0][ii] = uc*qh; US[ii] = single*qh
                for j, name in enumerate(frozen.SCENARIOS, 1):
                    branch = .75 if name == 'RESERVE075' else 1.25 if name == 'RESERVE125' else 1.
                    tail = .05 if name == 'TAIL005' else .1 if name == 'TAIL010' else 0.
                    qg, qh = frozen.completion(valid, c0, branch, tail)
                    base[j][ii] = ub*qg; candidate[j][ii] = uc*qh
        for val in [UB, UC, US, *base, *candidate]:
            assert np.isfinite(val).all() and (val > 0).all()
        stress = pd.read_parquet(frozen.TARGET, columns=['row_id', 'T1_reserve075', 'T1_reserve125']).set_index('row_id').loc[meta.row_id]
        ys = [meta.T0.to_numpy(float), stress.T1_reserve075.to_numpy(float), stress.T1_reserve125.to_numpy(float),
              meta.T0.to_numpy(float), meta.T0.to_numpy(float)]
        data = [(ys[0], base[0], candidate[0]), (ys[0], US, candidate[0])]
        data += [(ys[j], base[j], candidate[j]) for j in range(1, 5)]
        weights = pd.read_parquet(BASE/'estimando_cartera2025_v3/weights.parquet').set_index('row_id').loc[meta.row_id]
        assert np.array_equal(weights.group_id, meta.group_id)
        results, support = summarize(meta, data, weights.weight.to_numpy(float))
        saved = meta[['row_id', 'line', 'year', 'new_business', 'fold', 'group_id', 'T0']].copy()
        saved['U_base'] = UB; saved['U_mean'] = UC; saved['nominal_base'] = base[0]; saved['nominal_mean'] = candidate[0]
        for j, name in enumerate(frozen.SCENARIOS, 1):
            saved[name+'_base'] = base[j]; saved[name+'_mean'] = candidate[j]
        saved.to_parquet(OUT/'held2024_transfer_prices.parquet', index=False)
        fit_counts = counts()
        assert all(fit_counts[role]['reporting_completed'] == 450 and fit_counts[role]['closed_learners_completed'] == 195 for role in ['primary', 'poison'])
        assert fit_counts['primary']['constants']['price_total'] <= 5000
        primary = results['NOMINAL_VS_BASE']
        gates = {'nominal_delta_ge002': primary['delta'] >= .002, 'nominal_lower95_positive': primary['bootstrap95'][0] > 0,
                 'at_least4positive_folds': sum(z > 0 for z in primary['folds'].values()) >= 4,
                 'post31_nonnegative': primary['post31_delta'] >= 0,
                 'all_nominal_and_four_scenario_cell_floors': all(results[name]['worst_cell_delta'] >= -.001 for name in [NAMES[0], *frozen.SCENARIOS])}
        assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
        report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'status': 'P4_conditional_target_year_transfer_complete',
                  'results': results, 'diagnostic_gates': gates, 'counts': fit_counts, 'committed_scopes': 90,
                  'held2024_rows': len(meta), 'support': support, 'target_training_years': [2023], 'target_held_years': [2024],
                  'source_training_year2024_excluded': False, 'prospective2023_asof_reconstruction': False,
                  'both_held_years_gate_established': False, 'new_source_models': 0, 'new_source_inference': 0,
                  'new_final_test_prices': 0, 'new_submissions': 0, 'formal_promotion': False, 'submission_allowed': False,
                  'private_improvement_established': False, 'limits': plan['limits'], '2024_open': True,
                  'B00_all_alternatives_preserved': True, 'goal_achieved': False, 'plan_sha256': w.sha(PLAN)}
        dump(OUT/'report.json', report)
        print(json.dumps({'status': report['status'], 'results': {name: {k: a[k] for k in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']} for name, a in results.items()},
                          'gates': gates, 'counts': fit_counts}), flush=True)
    except Exception as exc:
        dump(OUT/f'failure_{datetime.now(timezone.utc).strftime("%H%M%S%f")}.json',
             {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'exception': type(exc).__name__,
              'message': str(exc), 'counts': counts() if (OUT/'events.jsonl').exists() else {},
              'committed_scopes': len(list(OUT.glob('scope_*/committed.json'))), 'next': 'Reconcile actual caches before any resume; preserve failures'})
        raise
    finally:
        n.set_execution(None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['register', 'run', 'resume']); args = parser.parse_args()
    with threadpool_limits(limits=2):
        register() if args.mode == 'register' else run(args.mode == 'resume')
