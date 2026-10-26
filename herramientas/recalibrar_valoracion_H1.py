"""P5: recalibración integral emergente en reservas75/125, con fuente congelada.

Reusa exclusivamente distribuciones de reporte/ramas de marca ya aprendidas y
protegidas. Nunca reusa parámetros nominales de precio como si fueran nuevos.
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
BASE = R/'privado/semana2/mision017_fase2'; P1 = BASE/'preflight_anidado_H1_20261026_v1'
P2 = BASE/'media_anidada_H1_20261026_v3'; P3 = BASE/'sensibilidad_congelada_media_H1_20261026_v1'
OUT = BASE/'P5_recalibracion_reservas_H1_20261026_v1'
PLAN = R/'registro/semana2_recalibracion_reservas_H1_plan_v1.json'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader')); sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits


def load(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(sp); sp.loader.exec_module(module); return module


p4 = load('P5_year_scope_math_helpers', R/'herramientas/validar_transferencia_anual_H1.py')
n = p4.n; h = p4.h; b = p4.b; g = p4.g; v = p4.v; w = p4.w
complete = p4.complete; frozen = p4.frozen; unit = frozen.unit
BRANCHES = [('RESERVE075', .75), ('RESERVE125', 1.25)]


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def event(kind, **values):
    with (OUT/'events.jsonl').open('a', encoding='utf8') as stream:
        stream.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'kind': kind, **values})+'\n')


def input_frames():
    return p4.input_frames()


def scope(full, outer, member):
    train = full.fold.ne(outer)
    if member >= 0:
        inner = pd.read_parquet(P1/f'inner_groups_outer{outer}.parquet').set_index('group_id').inner_fold
        train &= full.group_id.map(inner).ne(member)
    held = full.fold.eq(outer)
    f = full.loc[train | held].copy().reset_index(drop=True)
    f['original_fold'] = f.fold.to_numpy(); f['fold'] = held.loc[train | held].to_numpy(dtype=int)
    assert not set(f.loc[f.fold.eq(0), 'group_id']).intersection(f.loc[f.fold.eq(1), 'group_id'])
    return f


def learned_c0(line, outer, member):
    if member == -1:
        c0 = w.read(BASE/f'tanda2_20261025_v1/learning_{line}_fold{outer}.json')['artifact']['C0']
    else:
        c0 = w.read(P2/f'scope_{line}_outer{outer}_member{member}/primary/C0.json')
    return c0


def learner(f, c0, branch, line, folder, tag, role, with_core=False, replay=False):
    folder.mkdir(parents=True, exist_ok=True)
    train = f.fold.eq(0); held = f.fold.eq(1)
    assert c0['fit_row_ids'] == sorted(f.loc[train, 'row_id'])
    assert not set(f.loc[train, 'group_id']).intersection(f.loc[held, 'group_id'])
    work = f.copy()
    # Real new objective, not a nominal learned multiplier or an oracle scale.
    work['T0'] = f.T0.to_numpy(float)+(branch-1)*f.reserve.to_numpy(float)
    assert work.loc[train, 'T0'].ge(0).all()
    qg, qh = frozen.completion(work, c0, branch)
    assert (qg > 0).all() and (qh > 0).all()
    work['e_cost_scope'] = work.exposure.to_numpy()*qg
    work['e_source_mix'] = work.exposure.to_numpy()*qh
    artifacts = {}; prices = {}; controls = {}; normalizers = 0
    for name, link in [('G3', 'e_cost_scope'), ('H1', 'e_source_mix')]:
        path = folder/('learning_'+name+'.json')
        if not path.exists():
            assert not replay
            event('closed_started', tag=tag, role=role, model=name)
            _, a = h.learn(work, 1, line, link)
            dump(path, a); event('closed_completed', tag=tag, role=role, model=name, constants=n.count_constants(a))
        a = w.read(path)
        assert a['training_row_ids_digest'] == b.digest(sorted(work.loc[train, 'row_id']))
        assert a['training_groups_digest'] == b.digest(sorted(set(work.loc[train, 'group_id'])))
        valid = work.loc[held].copy(); observed, no = h.replay(valid, a)
        assert no == a['held_normalizers']
        Er = valid.exposure.to_numpy(); E = valid.exposure_calendar.to_numpy(); valid['exposure'] = E
        u, nu = h.replay(valid, a, ultimate=True)
        L = np.ones(len(valid)); cells = [f'{int(y)}|{int(nb)}' for y, nb in zip(valid.year, valid.new_business)]
        for variable, norm in nu.items():
            L *= np.array([norm[k]/no[variable][k] for k in cells]); normalizers += len(norm)
        q = (qg if name == 'G3' else qh)[held.to_numpy()]
        assert np.allclose(observed, u*(Er/E)*q*L, rtol=3e-12, atol=1e-9)
        tr = work.loc[train]; m = tr.annual_raw_T2b.to_numpy()*tr[link].to_numpy()
        for shape in a['shape']:
            m = b.shape_apply(tr, m, shape)
        moment = math.fsum((tr.T0.to_numpy()/np.sqrt(m)).tolist())/math.fsum(np.sqrt(m).tolist())
        assert math.isclose(moment, a['kshape'], rel_tol=3e-12)
        artifacts[name] = a; prices[name] = u
        controls[name] = {'bridge_relative_error': float(np.max(np.abs(observed/(u*(Er/E)*q*L)-1))),
                          'moment_relative_error': abs(moment/a['kshape']-1)}
    if with_core:
        tr = work.loc[train].copy(); valid = work.loc[held].copy()
        for part in [tr, valid]:
            part['base_N3'] = h.apply_component(part, artifacts['G3'], 'e_cost_scope')
        joined = pd.concat([tr, valid], ignore_index=True); path = folder/'learning_S2.json'
        if not path.exists():
            assert not replay
            event('closed_started', tag=tag, role=role, model='S2')
            _, a = complete.learn(joined, 1, line); dump(path, a)
            comp = a['component']
            constants = {'shape_factors': comp['shape_factor_constants'], 'levels': comp['level_constants'],
                         'residual_factors': sum(len(z['factors']) for z in a['stages']),
                         'training_nuisance_levels': sum(len(z['nuisance_year_business']) for z in a['stages']),
                         'shape_training_normalizers_separate': comp['shape_training_normalizers'],
                         'training_stage_normalizers_separate': sum(len(z) for z in a['training_normalizers'].values()),
                         'observed_held_stage_normalizers_separate': sum(len(z) for z in a['held_normalizers'].values()),
                         'stage_calls': len(a['stages'])}
            event('closed_completed', tag=tag, role=role, model='S2', constants=constants)
        a = w.read(path)
        assert a['fit_row_ids_digest'] == b.digest(sorted(tr.row_id))
        _, no = complete.replay(valid, a); assert no == a['held_normalizers']
        sf = valid.copy(); sf['exposure'] = sf.exposure_calendar; sf['e_cost_scope'] = sf.exposure_calendar
        sf['base_N3'] = h.apply_component(sf, artifacts['G3'], 'e_cost_scope', ultimate=True)
        uu, nu = complete.replay(sf, a)
        artifacts['S2'] = a; prices['S2'] = uu['S2']; normalizers += sum(len(z) for z in nu.values())
        comp = a['component']; m = np.exp(tr.log_relative_A1S.to_numpy())*tr.e_cost_scope.to_numpy()
        for shape in comp['shape']:
            m = b.shape_apply(tr, m, shape)
        moment = math.fsum((tr.T0.to_numpy()/np.sqrt(m)).tolist())/math.fsum(np.sqrt(m).tolist())
        assert math.isclose(moment, comp['level'], rel_tol=3e-12)
        controls['S2'] = {'moment_relative_error': abs(moment/comp['level']-1)}
    assert all(np.isfinite(z).all() and (z > 0).all() for z in prices.values())
    return {'artifacts': artifacts, 'ultimate': prices, 'controls': controls,
            'held_row_ids': work.loc[held, 'row_id'].tolist(), 'ultimate_normalizers': normalizers}


def corrupt(f):
    bad = f.copy(); held = bad.fold.eq(1)
    bad.loc[held, 'T0'] = -1e30; bad.loc[held, 'reserve'] = 1e30
    return bad


def synthetic():
    rng = np.random.default_rng(2026102632); checks = []
    for line, perils in [('motor', ['bodily_injury', 'glass_hail', 'own_damage', 'theft', 'third_party_prop']),
                         ('buildings', ['accidental_damage', 'escape_of_water', 'fire', 'flood', 'storm', 'subsidence']),
                         ('contents', ['accidental_damage', 'escape_of_water', 'flood', 'theft'])]:
        size = 1000; year = rng.integers(2023, 2025, size); groups = np.arange(size)//2
        E = np.where(year == 2024, 366/365, 1.)
        f = pd.DataFrame({'row_id': [line+'s'+str(i) for i in range(size)], 'line': line, 'year': year,
                          'group_id': ['g'+str(i) for i in groups], 'fold': (groups % 5 == 0).astype(int),
                          'new_business': rng.integers(0, 2, size), 'exposure': np.round(E, 4), 'exposure_calendar': E,
                          'period_start': pd.to_datetime(pd.Series(year).astype(str)+'-01-01'),
                          'period_end': pd.to_datetime(pd.Series(year).astype(str)+'-12-31'), 'is_test': False,
                          'annual_raw_T2b': rng.uniform(50, 250, size), 'log_relative_A1S': rng.normal(0, .4, size),
                          'prior_claims_5y': rng.integers(0, 3, size), 'ncb_years': rng.integers(0, 15, size),
                          'gender': rng.choice(['F', 'M'], size), 'works_from_home': rng.choice([True, False], size),
                          'marketing_segment': rng.choice(['a', 'b', 'c'], size), 'T0': rng.gamma(2, 80, size)})
        f['reserve'] = f.T0*rng.uniform(0, .7, size)
        for p in perils:
            f['f_'+p] = rng.uniform(.1, 1, size); f['s_'+p] = rng.uniform(20, 100, size)
        curves = {p: {'delay_days': [0, 30, 365, 730],
                      'cost_cdf': {'0.75': [.12, .72, .94, 1.], '1.0': [.11, .7, .93, 1.], '1.25': [.1, .68, .92, 1.]},
                      'mean_net_mark': {'0.75': 80.+j, '1.0': 100.+j, '1.25': 120.+j}}
                  for j, p in enumerate(perils)}
        c0 = {'curves': curves, 'frequency': {p: .1 for p in perils}, 'fit_row_ids': sorted(f.loc[f.fold.eq(0), 'row_id'])}
        for name, branch in BRANCHES:
            folder = OUT/'synthetic'/line/name
            a = learner(f, c0, branch, line, folder/'primary', 'synthetic', 'synthetic', True)
            z = learner(corrupt(f), c0, branch, line, folder/'poison', 'synthetic', 'synthetic', True)
            assert b.digest(a['artifacts']) == b.digest(z['artifacts'])
            assert all(np.array_equal(a['ultimate'][k], z['ultimate'][k]) for k in a['ultimate'])
            checks.append({'line': line, 'branch': branch, 'whole_new_price_learning_poison_exact': True,
                           'fresh_base_and_member_recalibration': True, 'moment_bridge_valid': True})
        nores = f.copy(); nores['reserve'] = 0.
        flat = json.loads(json.dumps(c0))
        for model in flat['curves'].values():
            for key in ['0.75', '1.25']:
                model['cost_cdf'][key] = model['cost_cdf']['1.0']; model['mean_net_mark'][key] = model['mean_net_mark']['1.0']
        # Zero-reserve / identical-link limiting identity tests the new entrypoint,
        # not the old nominal producer or a mirror-only utility.
        aa = learner(nores, flat, .75, line, OUT/'synthetic'/line/'zero075', 'synthetic', 'synthetic', True)
        zz = learner(nores, flat, 1.25, line, OUT/'synthetic'/line/'zero125', 'synthetic', 'synthetic', True)
        assert b.digest(aa['artifacts']) == b.digest(zz['artifacts'])
        assert all(np.array_equal(aa['ultimate'][k], zz['ultimate'][k]) for k in aa['ultimate'])
    return {'author': 'Codex', 'checks': checks, 'zero_reserve_identical_link_identity_exact_all_lines': True,
            'synthetic_closed_learners': 54, 'synthetic_reporting_fits': 0, 'new_contest_fits': 0}


def register():
    assert not OUT.exists() and not PLAN.exists(); OUT.mkdir()
    assert w.read(P3/'report.json')['ultimate_forecasts_unchanged_all_scenarios']
    files = [Path(__file__), Path(p4.__file__), Path(n.__file__), Path(h.__file__), Path(h.d.__file__), Path(b.__file__), Path(g.__file__),
             Path(v.__file__), Path(w.__file__), Path(complete.__file__), Path(frozen.__file__),
             P1/'report.json', P2/'report.json', P3/'report.json', P3/'held_frozen_scenario_prices.parquet',
             BASE/'P4_transferencia_anual_H1_20261026_v1/report.json', BASE/'P4_transferencia_anual_H1_20261026_v1/replay_report.json',
             frozen.TARGET, BASE/'estimando_cartera2025_v3/weights.parquet',
             R/'registro/semana2_mision_privada_plan_v1.json', R/'registro/semana2_control_entregas_codex_actual.json']
    frames = input_frames(); records = []
    for line, full in frames.items():
        files += [P1/f'canonical_{line}.parquet', BASE/f'A1S_nucleo_20261026_v1/source_models/target_{line}_three_seed_components.parquet']
        for outer in range(5):
            files.append(BASE/f'tanda2_20261025_v1/learning_{line}_fold{outer}.json')
            for member in [-1, 0, 1, 2, 3, 4]:
                f = scope(full, outer, member); c0 = learned_c0(line, outer, member)
                assert c0['fit_row_ids'] == sorted(f.loc[f.fold.eq(0), 'row_id'])
                records.append({'line': line, 'outer': outer, 'member': member,
                                'training_row_digest': b.digest(c0['fit_row_ids'])})
                if member >= 0:
                    files += [P2/f'scope_{line}_outer{outer}_member{member}/primary/C0.json',
                              P2/f'scope_{line}_outer{outer}_member{member}/committed.json']
    for outer in range(5):
        files.append(P1/f'inner_groups_outer{outer}.parquet')
    def forbidden(*args, **kwargs):
        raise AssertionError('No reporting estimation allowed for P5stored branch reuse')
    original = v.fit_reporting; v.fit_reporting = forbidden
    try:
        dump(OUT/'synthetic_report.json', synthetic())
    finally:
        v.fit_reporting = original
    files.append(OUT/'synthetic_report.json')
    plan = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'type': 'P5_complete_target_price_recalibration_two_reserve_bases',
            'hypothesis': 'P3afrozen prices do not establish whether the complete target learner remains stable when reserves change the training target and its observation link. Evaluate both predefined reserve valuations without selecting either as the new production objective.',
            'unchanged': 'T0nominal remains production reference. Same source models and profiles, sourceA1Sgeometricmean, fixedS2mixture50/50, K300/K400, source/targetfeatures, partitions and five-member arithmetic mean. No new model capacity or hyperparameter/level/weight searches.',
            'target': 'For each b=.75/1.25, train and score Y_b=T0+(b-1)*reserve. Use existing costCDF_b/meanmark_b, same countCDF and frequencies. qglobal_b=sum_p(frequency_p*meanmark_b normalized *costcompletion_b); qsource_b=source f_period*s weightedcostcompletion_b, sourceprofile fixed. No double exposure.',
            'algebraic_reuse': 'P3aevent-probability verification established stored branch equivalence for all90C0objects. Delay/countdistribution and frequencies do not depend on reserve marks. Reuse those protected branches; no C0refit, curve suite or mark reestimation. Every new target shape/level/stage and the complete S2outerbase must actually be relearned under each b.',
            'data_scope': 'All109296observed2023/2024rows, same five globalgroups and saved inner groups. Outer15and inner75target scopes per branch. No held target is used for learning; each branch target remains separate. Source is not revalued, so this is full emerging price recalibration conditional on fixed source, not a full all-market revaluation.',
            'algorithm': 'Same complete feasible S2ultimate outerbase * mean5(U_H1/U_G3), with fresh branch-specific S2and G3/H1calibrations. Outer branchC0only for evaluation, never inner learning. Calendar once and ultimate predictionnormalizers at forward; original rounded exposure at fit.',
            'contrasts': ['RESERVE075_recalibrated_vs_recalibrated_base', 'RESERVE125_recalibrated_vs_recalibrated_base',
                          'RESERVE075_new_candidate_vs_P3afrozen_candidate', 'RESERVE125_new_candidate_vs_P3afrozen_candidate'],
            'criterion': 'Diagnostic robustness: both primary intervals, allfold/year/cells, post31and failures recorded; loss below-.001byline/year/NBfails stability. Historical minimumgain.002and lower95/fold/year rules reported, no automatic promotion/valuationchoice or public-driven release. Secondary contrasts cannot rescue primary failures.',
            'bootstrap': {'replicates': 2000, 'seed': 2026102633, 'unit': 'saved globalconnectedcomponent', 'joint4': True, 'family': 'exploratory Bonferroni4'},
            'controls': ['Actual newbranch-learning and ultimateflow with heldT0/reservepoison, exactartifact/priceequality in all180line/outer/member/branchscopes',
                         'C0exact training keys; protected parent receipts pinned, no fitting reporting allowed',
                         'Synthetic same real entrypoint for three lines and bothbranches; zeroreserve+identicallink limitingidentity',
                         'Blocked-learning real replay, scalar moment, bridge, mean, standardmetric and immutable sources',
                         'Derived globalweights separate, not new frequencyfits; prediction normalizers/control/synthetic fits separate'],
            'budget': {'primary_closed_learners': 390, 'adverse_closed_learners_separate': 390, 'primary_price_constants_max': 11000,
                       'new_C0_fits': 0, 'new_source_models': 0, 'new_source_inference': 0, 'new_final_test_prices': 0, 'new_submissions': 0},
            'limits': ['Adaptive2023/2024and feasibleS2proxy, not full deliveredF3creplay or independent professional confirmation',
                       'Sourcefixed and final2024valuation/undatedmasteravailability; no pristine prospectiveor hiddenprivateproof',
                       'Same low2025NBsupport/ESSfailure and unidentifiedtrue ultimate tail, source peril mix and reserveadequacy',
                       'Reserve stress recalibrates targetonly; hypotheticaltail has no identifiedjointcountseverity model and is not falsely refit'],
            'scopes': records, '2024_open': True, 'B00_all_alternatives_preserved': True, 'submission_allowed': False,
            'sources': {w.rel(p): w.sha(p) for p in files}}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. Registro P5 antes de ajustes reales: recalibración integral emergente bajo reservas75/125. '
                    'Se aprenderán de nuevo las formas, niveles, factores, miembros G3/H1y baseS2 bajo cada objetivo y enlace correspondiente. '
                    'Las curvas de conteo y ramas de coste protegidas se reutilizan por la equivalencia algebraica ya verificada enP3a; '
                    'no se repiten curvas ni su auditoría. La fuente, los folds, credibilidad y media fija no cambian. '
                    'Dos contrastes primarios frente a sus bases recalibradas; secundarios frente a los precios congelados deP3a. '
                    'Se declararon todos los grupos/celdas/escenarios y criterios antes de puntuar, sin escoger una valoración para producción. '
                    'Presupuesto390aprendices cerrados primarios y390controles adversos separados. El flujo sintético de ambos escenarios y '
                    'tres ramos pasó, incluida identidad sin reservas/enlaces iguales y prohibición de ajustar reporte. '
                    'Cero modelos fuente, C0, precios2025oenvíos. Fuente fija, búsqueda adaptativa y falta de soporte2025limitan la lectura. '
                    'B00/alternativas conservados,2024abierto,H1diferido. Plan: '+w.rel(PLAN)+'.', encoding='utf8')
    res = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                          '--id', 'COD-S2-20261026-PRIVADA-P5-RESERVAS-PREVIO', '--asunto',
                          'P5 registrada: recalibración emergente completa bajo dos bases de reservas', '--cuerpo', str(body)],
                         check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT/'registration.json', {'plan_sha256': w.sha(PLAN), 'forum': json.loads(res.stdout)})
    print(json.dumps({'registered': True, 'synthetic': w.read(OUT/'synthetic_report.json'), 'forum': json.loads(res.stdout)}))


def counts():
    events = [json.loads(s) for s in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines()]; result = {}
    for role in ['primary', 'poison']:
        selected = [e for e in events if e.get('role') == role and e['kind'] == 'closed_completed']
        keys = ['shape_factors', 'levels', 'residual_factors', 'training_nuisance_levels', 'shape_training_normalizers_separate',
                'training_stage_normalizers_separate', 'observed_held_stage_normalizers_separate', 'stage_calls']
        constants = {k: sum(e['constants'][k] for e in selected) for k in keys}
        constants['price_total'] = sum(constants[k] for k in ['shape_factors', 'levels', 'residual_factors', 'training_nuisance_levels'])
        result[role] = {'closed_learners_completed': len(selected), 'constants': constants}
    return result


def statistics(meta, data, weight):
    # Same established math with a fixed, separately registered four-contrast family.
    codes, groups = pd.factorize(meta.group_id, sort=True); G = len(groups); size = len(meta)
    count = np.bincount(codes, minlength=G); gains = []; YY = []; SQ = []; null = []; rowgain = []
    for y, base, candidate in data:
        gain = unit(y, base)-unit(y, candidate); rowgain.append(gain)
        gains.append(np.bincount(codes, weights=gain, minlength=G)); YY.append(np.bincount(codes, weights=y, minlength=G))
        SQ.append(np.bincount(codes, weights=np.sqrt(y), minlength=G)); null.append(float(unit(y, np.full(size, y.mean())).sum()))
        assert abs(unit(y, candidate).mean()-p4.mean_tweedie_deviance(y, candidate, power=1.5)) < 1e-8
    gains = np.column_stack(gains); YY = np.column_stack(YY); SQ = np.column_stack(SQ)
    rng = np.random.default_rng(2026102633); draws = []
    for _ in range(2000):
        ii = rng.integers(0, G, G); den = 8*(np.sqrt(count[ii].sum()*YY[ii].sum(axis=0))-SQ[ii].sum(axis=0))
        assert (den > 0).all(); draws.append(gains[ii].sum(axis=0)/den)
    draws = np.asarray(draws); np.save(OUT/'joint_four_bootstrap.npy', draws); result = {}
    names = ['RESERVE075', 'RESERVE125', 'RESERVE075_VS_FROZEN', 'RESERVE125_VS_FROZEN']
    for j, name in enumerate(names):
        y, base, candidate = data[j]; gain = rowgain[j]; cells = []; den = null[j]
        for (line, year, nb), indices in meta.groupby(['line', 'year', 'new_business']).groups.items():
            ii = np.asarray(list(indices)); yy = y[ii]; dd = unit(yy, np.full(len(ii), yy.mean())).sum()
            cells.append({'line': line, 'year': int(year), 'NB': int(nb), 'rows': len(ii),
                          'delta_global': float(gain[ii].sum()/den), 'delta_cell_null': float(gain[ii].sum()/dd),
                          'AE_base': float(yy.sum()/base[ii].sum()), 'AE_candidate': float(yy.sum()/candidate[ii].sum())})
        result[name] = {'delta': float(gain.sum()/den), 'bootstrap95': np.quantile(draws[:, j], [.025, .975]).tolist(),
                        'simultaneous95_four': np.quantile(draws[:, j], [.025/4, 1-.025/4]).tolist(),
                        'post31_delta': float((gains[:, j].sum()-np.sort(gains[:, j])[::-1][:31].sum())/den),
                        'folds': {str(k): float(gain[meta.fold.eq(k)].sum()/den) for k in range(5)},
                        'years': {str(k): float(gain[meta.year.eq(k)].sum()/den) for k in [2023, 2024]},
                        'cells': cells, 'worst_cell_delta': min(c['delta_cell_null'] for c in cells),
                        'base_D2': float(1-unit(y, base).sum()/den), 'candidate_D2': float(1-unit(y, candidate).sum()/den),
                        'weighted2025_point_only_ESS_failed': float(np.sum(weight*gain)/np.sum(weight*unit(y, np.full(size, np.average(y, weights=weight)))))}
    return result


def run():
    plan = w.read(PLAN); assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    execution = {'author': 'Codex', 'pid': os.getpid(), 'utc': datetime.now(timezone.utc).isoformat(),
                 'script': w.rel(Path(__file__)), 'output': w.rel(OUT), 'kind': 'P5_full_target_reserve_recalibration'}
    dump(OUT/'started.json', execution); n.OUT = OUT; n.set_execution(execution)
    original = v.fit_reporting
    def reject(*args, **kwargs):
        raise AssertionError('P5must not refit any reporting distribution')
    v.fit_reporting = reject
    try:
        frames = input_frames()
        for name, branch in BRANCHES:
            for item in plan['scopes']:
                line, outer, member = item['line'], item['outer'], item['member']
                folder = OUT/name/f'scope_{line}_outer{outer}_member{member}'; folder.mkdir(parents=True, exist_ok=True)
                f = scope(frames[line], outer, member); c0 = learned_c0(line, outer, member)
                assert b.digest(c0['fit_row_ids']) == item['training_row_digest']
                tag = f'{name}|{line}|{outer}|{member}'
                a = learner(f, c0, branch, line, folder/'primary', tag, 'primary', member == -1)
                z = learner(corrupt(f), c0, branch, line, folder/'poison', tag, 'poison', member == -1)
                assert b.digest(a['artifacts']) == b.digest(z['artifacts'])
                assert all(np.array_equal(a['ultimate'][k], z['ultimate'][k]) for k in a['ultimate'])
                pd.DataFrame({'row_id': a['held_row_ids'], **{'U_'+k: value for k, value in a['ultimate'].items()}}).to_parquet(folder/'ultimate.parquet', index=False)
                paths = [folder/'ultimate.parquet', *list((folder/'primary').glob('*.json')), *list((folder/'poison').glob('*.json'))]
                dump(folder/'committed.json', {'line': line, 'outer': outer, 'member': member, 'branch': branch,
                                               'new_target_price_learning_poison_exact': True, 'controls': a['controls'],
                                               'primary_ultimate_normalizers': a['ultimate_normalizers'],
                                               'adverse_ultimate_normalizers_separate': z['ultimate_normalizers'],
                                               'outputs': {w.rel(p): w.sha(p) for p in paths}})
            print(json.dumps({'branch': name, 'committed_scopes': 90, 'complete_learning': True}), flush=True)
        meta = pd.concat(frames.values(), ignore_index=True); ix = pd.Series(np.arange(len(meta)), index=meta.row_id)
        assert meta.row_id.is_unique and len(meta) == 109296
        base = []; candidate = []
        for name, branch in BRANCHES:
            pb = np.full(len(meta), np.nan); pc = pb.copy(); UB = pb.copy(); UC = pb.copy()
            for line, full in frames.items():
                for outer in range(5):
                    valid = full.loc[full.fold.eq(outer)].copy(); c0 = learned_c0(line, outer, -1)
                    pp = pd.read_parquet(OUT/name/f'scope_{line}_outer{outer}_member-1/ultimate.parquet').set_index('row_id').loc[valid.row_id]
                    rr = []
                    for member in range(5):
                        part = pd.read_parquet(OUT/name/f'scope_{line}_outer{outer}_member{member}/ultimate.parquet').set_index('row_id').loc[valid.row_id]
                        rr.append(part.U_H1.to_numpy()/part.U_G3.to_numpy())
                    ub = pp.U_S2.to_numpy(); members = ub[:, None]*np.column_stack(rr); uc = members.mean(axis=1)
                    assert np.allclose(uc, sum(members[:, j] for j in range(5))/5, rtol=2e-15)
                    qg, qh = frozen.completion(valid, c0, branch); ii = ix.loc[valid.row_id].to_numpy()
                    pb[ii] = ub*qg; pc[ii] = uc*qh; UB[ii] = ub; UC[ii] = uc
            for a in [pb, pc, UB, UC]:
                assert np.isfinite(a).all() and (a > 0).all()
            saved = meta[['row_id', 'line', 'year', 'new_business', 'fold', 'group_id', 'T0', 'reserve']].copy()
            saved['Y_branch'] = meta.T0.to_numpy()+(branch-1)*meta.reserve.to_numpy()
            saved['base'] = pb; saved['candidate'] = pc; saved['U_base'] = UB; saved['U_candidate'] = UC
            saved.to_parquet(OUT/(name+'_recalibrated_prices.parquet'), index=False)
            base.append(pb); candidate.append(pc)
        previous = pd.read_parquet(P3/'held_frozen_scenario_prices.parquet').set_index('row_id').loc[meta.row_id]
        ys = [meta.T0.to_numpy()+(branch-1)*meta.reserve.to_numpy() for _, branch in BRANCHES]
        official = pd.read_parquet(frozen.TARGET, columns=['row_id', 'T1_reserve075', 'T1_reserve125']).set_index('row_id').loc[meta.row_id]
        assert np.allclose(ys[0], official.T1_reserve075, rtol=1e-14, atol=1e-8)
        assert np.allclose(ys[1], official.T1_reserve125, rtol=1e-14, atol=1e-8)
        weights = pd.read_parquet(BASE/'estimando_cartera2025_v3/weights.parquet').set_index('row_id').loc[meta.row_id]
        assert np.array_equal(weights.group_id, meta.group_id)
        data = [(ys[j], base[j], candidate[j]) for j in range(2)]
        data += [(ys[j], previous[name+'_C'].to_numpy(), candidate[j]) for j, (name, _) in enumerate(BRANCHES)]
        results = statistics(meta, data, weights.weight.to_numpy())
        fit_counts = counts(); assert all(fit_counts[role]['closed_learners_completed'] == 390 for role in ['primary', 'poison'])
        assert fit_counts['primary']['constants']['price_total'] <= 11000
        assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
        gates = {}
        for name, _ in BRANCHES:
            a = results[name]
            gates[name] = {'delta_ge002': a['delta'] >= .002, 'lower95_positive': a['bootstrap95'][0] > 0,
                           'four_positive_folds': sum(z > 0 for z in a['folds'].values()) >= 4,
                           'both_years_nonnegative': min(a['years'].values()) >= 0, 'post31_nonnegative': a['post31_delta'] >= 0,
                           'worst_cell_floor': a['worst_cell_delta'] >= -.001}
        report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'status': 'P5_full_emerging_reserve_recalibration_complete',
                  'results': results, 'diagnostic_gates': gates, 'counts': fit_counts, 'committed_scopes': 180,
                  'new_C0_fits': 0, 'new_source_models': 0, 'new_source_inference': 0, 'new_final_test_prices': 0,
                  'new_submissions': 0, 'nominal_production_objective_changed': False, 'formal_promotion': False,
                  'submission_allowed': False, 'private_improvement_established': False, '2024_open': True,
                  'B00_all_alternatives_preserved': True, 'goal_achieved': False, 'plan_sha256': w.sha(PLAN), 'limits': plan['limits']}
        dump(OUT/'report.json', report)
        print(json.dumps({'status': report['status'], 'results': {name: {k: a[k] for k in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']} for name, a in results.items()},
                          'gates': gates, 'counts': fit_counts}), flush=True)
    except Exception as exc:
        dump(OUT/f'failure_{datetime.now(timezone.utc).strftime("%H%M%S%f")}.json',
             {'exception': type(exc).__name__, 'message': str(exc), 'counts': counts() if (OUT/'events.jsonl').exists() else {},
              'committed_scopes': len(list(OUT.glob('*/scope_*/committed.json'))), 'next': 'Preserve completed fits; reconcile before resuming'})
        raise
    finally:
        v.fit_reporting = original; n.set_execution(None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['register', 'run']); args = parser.parse_args()
    with threadpool_limits(limits=2):
        register() if args.mode == 'register' else run()
