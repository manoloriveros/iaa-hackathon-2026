"""Compara el algoritmo completo con/sin predictor fuente de exposición.

Reutiliza C0/N3/H1 no afectados; aprende solo las calibraciones S2 cambiadas.
Los dos esquemas son desarrollo adaptativo, no confirmación privada.
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
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
P9 = BASE/'P9_fuente_sin_exposicion_20261026'
P0 = BASE/'puente_ultimo_observado_H1_20261026_v1'
P1 = BASE/'preflight_anidado_H1_20261026_v1'; P2 = BASE/'media_anidada_H1_20261026_v3'
P3 = BASE/'sensibilidad_congelada_media_H1_20261026_v1'
P4 = BASE/'P4_transferencia_anual_H1_20261026_v1'
OUT = BASE/'P10_validacion_sin_exposicion_20261026'
PLAN = R/'registro/semana2_ablacion_fuente_validacion_plan.json'
INDEX = R/'registro/semana2_ablacion_fuente_validacion_actual.json'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


parent = load('p10_scoped_helpers', R/'herramientas/validar_transferencia_anual_H1.py')
core = parent.complete; h = parent.h; b = parent.b; g = parent.g; w = parent.w
unit = parent.unit
state = load('p10_source_state', R/'herramientas/ablar_exposicion_fuente_P9.py')
NAMES = ['NOMINAL', 'RESERVE075', 'RESERVE125', 'TAIL005', 'TAIL010']


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f: json.dump(obj, f, ensure_ascii=False, indent=2)


def event(kind, **values):
    with (OUT/'events.jsonl').open('a', encoding='utf8') as f:
        f.write(json.dumps({'utc': utc(), 'kind': kind, **values})+'\n')


def rowbind(f, other, columns):
    assert f.row_id.is_unique and other.row_id.is_unique
    extra = other.set_index('row_id').loc[f.row_id]
    for key in ['year', 'group_id', 'fold', 'new_business', 'T0', 'reserve']:
        if key in extra and key in f: assert np.array_equal(extra[key], f[key])
    result = f.copy()
    for name in columns: result[name] = extra[name].to_numpy()
    return result


def get_scope(cohort, line, outer, relative):
    canonical = pd.read_parquet(P1/f'canonical_{line}.parquet')
    if cohort == 'POOLED':
        f = pd.read_parquet(HOME/f'target_complete_core/inputs_{line}_fold{outer}.parquet')
        f = rowbind(f, canonical, ['exposure_calendar', 'annual_raw_T2b'])
        n3 = w.read(BASE/f'tanda2_20261025_v1/learning_{line}_fold{outer}.json')['artifact']
        assert n3['C0']['fit_row_ids'] == sorted(f.loc[f.fold.ne(outer), 'row_id'])
        held = outer
    else:
        f = parent.make_scope(canonical, outer, -1)
        folder = P4/f'scope_{line}_outer{outer}_member-1/primary'
        c0 = w.read(folder/'C0.json'); n3 = w.read(folder/'learning_G3.json')
        assert c0['fit_row_ids'] == sorted(f.loc[f.fold.eq(0), 'row_id'])
        qg, _ = parent.frozen.completion(f, c0)
        f['e_cost_scope'] = f.exposure.to_numpy()*qg
        f['base_N3'] = h.apply_component(f, n3, 'e_cost_scope')
        held = 1
    rel = relative.set_index('row_id').loc[f.row_id, 'log_relative_A1S']
    f['log_relative_A1S'] = rel.to_numpy()
    train = f.fold.ne(held); valid = ~train
    assert not set(f.loc[train, 'group_id']).intersection(f.loc[valid, 'group_id'])
    assert np.isfinite(f.log_relative_A1S).all()
    return f, held, n3


def forward(f, held, artifact, n3):
    valid = f.loc[f.fold.eq(held)].copy()
    sf = valid.copy(); sf['exposure'] = sf.exposure_calendar.to_numpy()
    sf['e_cost_scope'] = sf.exposure_calendar.to_numpy()
    val = sf.annual_raw_T2b.to_numpy(float)*sf.exposure_calendar.to_numpy(float)
    for shape in n3['shape']: val = b.shape_apply(sf, val, shape)
    sf['base_N3'] = val*np.asarray([n3['cellshape'][str(int(nb))] for nb in sf.new_business])
    result, norms = core.replay(sf, artifact)
    assert np.isfinite(result['S2']).all() and (result['S2'] > 0).all()
    return valid.row_id.to_numpy(), result['S2'], norms


def old_scope(cohort, line, outer, held_rows):
    if cohort == 'POOLED':
        bridge = pd.read_parquet(P0/f'bridge_{line}_fold{outer}.parquet').set_index('row_id').loc[held_rows]
        p = pd.read_parquet(P2/'held_nested_prices.parquet').set_index('row_id').loc[held_rows]
        return bridge.U_S2.to_numpy(), p.T_B.to_numpy()
    p = pd.read_parquet(P4/'held2024_transfer_prices.parquet').set_index('row_id').loc[held_rows]
    return p.U_base.to_numpy(), p.nominal_mean.to_numpy()


def constants(artifact):
    a = artifact['component']
    return {'shape_factors': a['shape_factor_constants'], 'level_constants': a['level_constants'],
            'residual_factors': sum(len(s['factors']) for s in artifact['stages']),
            'training_nuisance_levels': sum(len(s['nuisance_year_business']) for s in artifact['stages']),
            'shape_training_normalizers_separate': a['shape_training_normalizers'],
            'training_stage_normalizers_separate': sum(len(z) for z in artifact['training_normalizers'].values()),
            'held_stage_normalizers_separate': sum(len(z) for z in artifact['held_normalizers'].values())}


def synthetic():
    checks = []
    for line in parent.h.LINES:
        n = 120; idx = np.arange(n)
        f = pd.DataFrame({'row_id': [line+str(i) for i in idx], 'group_id': [line+str(i) for i in idx],
                          'line': line, 'fold': idx % 5, 'year': np.where((idx//2) % 2, 2024, 2023),
                          'new_business': idx % 2, 'exposure': .4+.6*(idx % 7)/7,
                          'T0': np.where(idx % 7 == 0, 100.+idx, 0.), 'reserve': 0.,
                          'prior_claims_5y': idx % 4, 'ncb_years': idx % 6,
                          'gender': np.where(idx % 3, 'F', 'M'), 'works_from_home': idx % 2 == 0,
                          'marketing_segment': np.where(idx % 3, 'A', 'B'),
                          'log_relative_A1S': (idx % 5)/10., 'annual_raw_T2b': 60.})
        f['e_cost_scope'] = f.exposure*.8; f['base_N3'] = f.exposure*50
        f['exposure_calendar'] = f.exposure+1e-5
        p, a = core.learn(f, 0, line)
        bad = f.copy(); bad.loc[bad.fold.eq(0), ['T0', 'reserve']] = -1e12
        pp, aa = core.learn(bad, 0, line)
        assert b.digest(a) == b.digest(aa) and np.array_equal(p['S2'], pp['S2'])
        n3 = {'shape': [], 'cellshape': {'0': 1., '1': 1.}}
        ids, u, nu = forward(f, 0, a, n3); _, ubad, nubad = forward(bad, 0, a, n3)
        assert np.array_equal(u, ubad) and nu == nubad
        ratio = np.tile([.98, 1.02, 1., 1.03, .97], (len(u), 1))
        assert np.allclose((u[:, None]*ratio).mean(axis=1)*.8, u*.8, rtol=2e-15)
        checks.append({'line': line, 'whole_current_learning_held_poison_exact': True,
                       'ultimate_forward_and_five_member_observation_scalar_parity': True})
    return {'checks': checks, 'synthetic_closed_learner_calls_separate': 6, 'contest_fits': 0}


def prepare():
    assert not PLAN.exists()
    if OUT.exists():
        assert (OUT/'defect_before_contest_learning.json').exists()
        assert not (OUT/'started.json').exists() and not (OUT/'registration.json').exists()
    assert (P9/'report.json').exists() and (P9/'replay_report.json').exists()
    assert not w.read(state.PHASE).get('active_jobs') and not w.read(state.PHASE).get('active_execution')
    OUT.mkdir(exist_ok=True)
    paths = [Path(__file__), Path(state.__file__), Path(parent.__file__), Path(core.__file__), Path(h.__file__),
             Path(b.__file__), Path(g.__file__), Path(parent.v.__file__), Path(parent.frozen.__file__),
             P9/'report.json', P9/'replay_report.json', P2/'held_nested_prices.parquet',
             P3/'held_frozen_scenario_prices.parquet', P4/'held2024_transfer_prices.parquet',
             BASE/'estimando_cartera2025_v3/weights.parquet']
    scopes = []; original_checks = []
    for line in parent.h.LINES:
        paths += [P1/f'canonical_{line}.parquet', P9/f'historical_{line}_three_seed.parquet',
                  HOME/f'source_models/target_{line}_three_seed_components.parquet']
        old_rel = pd.read_parquet(HOME/f'source_models/target_{line}_three_seed_components.parquet')
        new_rel = pd.read_parquet(P9/f'historical_{line}_three_seed.parquet')
        assert not new_rel.is_test.any() and new_rel.year.isin([2023, 2024]).all()
        for cohort in ['POOLED', 'TRANSFER']:
            for outer in range(5):
                folder = P4/f'scope_{line}_outer{outer}_member-1/primary'
                olda = HOME/f'target_complete_core/learning_{line}_fold{outer}.json' if cohort == 'POOLED' else folder/'learning_S2.json'
                paths.append(olda)
                if cohort == 'POOLED':
                    paths += [HOME/f'target_complete_core/inputs_{line}_fold{outer}.parquet',
                              BASE/f'tanda2_20261025_v1/learning_{line}_fold{outer}.json', P0/f'bridge_{line}_fold{outer}.parquet']
                else: paths += [folder/'C0.json', folder/'learning_G3.json']
                # This replay checks the new integration against original numerical prices.
                original, held, n3 = get_scope(cohort, line, outer, old_rel)
                ids, u, _ = forward(original, held, w.read(olda), n3)
                expected, price = old_scope(cohort, line, outer, ids)
                err = float(np.max(np.abs(u/expected-1))); assert err < 3e-12
                f, held, n3 = get_scope(cohort, line, outer, new_rel)
                assert np.array_equal(original.row_id, f.row_id)
                tr = f.fold.ne(held)
                scopes.append({'cohort': cohort, 'line': line, 'outer': outer, 'held': held,
                               'training_rows': int(tr.sum()), 'held_rows': int((~tr).sum()),
                               'training_row_digest': b.digest(sorted(f.loc[tr, 'row_id'])),
                               'training_groups_digest': b.digest(sorted(set(f.loc[tr, 'group_id']))),
                               'original_ultimate_replay_max_relative_error': err})
                original_checks.append(err)
    fixture = synthetic(); dump(OUT/'synthetic.json', fixture)
    plan = {'author': 'Codex', 'utc': utc(), 'hypothesis': 'Removing the active source duration predictor at identical capacity improves or harms complete emerging S2/H1prices; quantify rather than adopt by sensitivity alone.',
            'primary_comparator': 'A1S_D0/S2/five-member-H1 versus original A1S/S2/five-member-H1 on identical held groups.',
            'changed_learning': 'Only S2source component shape/level plus same residual stages, 15pooled and15conditionalyeartransfer scopes. All ratios, C0and N3are independent of A1S and reused with exact keys/ancestry.',
            'exposure': 'Original rounded observation exposure and training C0; calendar ultimateforward once, original source-mixture observation adapters evaluation-only.',
            'sensitivity': 'Four fixed P3/P4reserve075/125andtail005/010scenarios with prices frozen and common original observation links. Not full branch recalibration of new D0.',
            'budget': {'new_source_fits': 0, 'new_C0_fits': 0, 'primary_closed_learner_calls': 30,
                       'adverse_closed_learner_calls_separate': 30, 'new_future2025inference': 0,
                       'new_finaltestprices': 0, 'new_submissions': 0},
            'criteria': {'nominal_pooled_delta_min': .002, 'nominal_pooled_lower95_positive': True,
                         'at_least4positive_folds': True, 'both_pooled_years_nonnegative': True,
                         'post31_nonnegative': True, 'all_nominal_and_stress_cell_floors': -.001,
                         'conditional_transfer_nominal_nonnegative': True},
            'bootstrap': {'replicates': 2000, 'pooled_seed': 2026102640, 'transfer_seed': 2026102641,
                          'group': 'saved connected customer/address component', 'bonferroni_family': 10,
                          'interpretation': 'Exploratory conditional on fixed source, reused learned curves and adaptive search, not model-selection confirmation.'},
            'level_sensitivity': [.95, 1., 1.05], 'future_weights': 'Reuse failedESSweights for point sensitivity only, no significance claim.',
            'preflight': fixture, 'original_flow_replay_max_relative_error': max(original_checks),
            'scopes': scopes, 'sources': {w.rel(p): w.sha(p) for p in dict.fromkeys(paths)},
            'limits': ['Both target years adaptive; source2021-2024and undated master snapshot conditional.',
                       'Year transfer learns target only2023but source contains2024; no prospective sourceyear holdout.',
                       'No exact full delivered F3c historical replay; comparator is the reproducible S2/H1algorithm.',
                       'Same source round budget selected with original feature; dropping column also alters random feature subsampling mapping.',
                       'Prior H1reserve/tail adverses and inadequate futureweightESS remain; a new delta cannot erase them.',
                       'Frozen valuation stress is not reserve adequacy proof or whole branch recalibration.'],
            '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. Registro P10 antes de calibrar o puntuar: comparar completo S2/H1 con A1S sin predictor de duración frente al mismo algoritmo original. '
                    'Los9modelos fuente P9 quedan congelados; no se cambia capacidad, semillas, precio objetivo, exposición o mezcla50/50. '
                    'Se reutilizan C0/N3y los5cocientes H1/G3porque no aprenden de A1S. Se ajustan30calibraciones S2con30controles adversos separados. '
                    'Quince ámbitos usan ambos años por grupos y quince aprenden destino2023y retienen2024. La fuente sigue incluyendo2024: desarrollo condicional, no prueba prospectiva. '
                    'El replay de los30ámbitos originales concilió el flujo numérico guardado antes de cambiarlo; el fixture ejerció aprendizaje, poison, forwardúltimo y media con seis llamadas sintéticas. '
                    'Se mantienen mínimo incremental0,002, intervalos por grupo, cuatro de cinco folds, ambos años, Post31y piso por celda−0,001, incluyendo cuatro sensibilidades fijadas. '
                    'Se reporta todo sin elegir ramo/semilla o normalizar al total de F3c. Pesos2025siguen sin soporte suficiente. '
                    'Cero precios2025, inferencias fuente nuevas o envíos. 2024abierto adaptativo, B00/F3c/P6intactos. '
                    'Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P10-ABLACION-PREVIO', '--asunto',
                             'P10 previo: validar simplificación completa por grupos, años y escenarios',
                             '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P10registered_before_target_learning',
               'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(result.stdout), 'output': w.rel(OUT)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt)
    print(json.dumps({'preflight': 'passed', 'scopes': 30, 'original_flow_error': max(original_checks), 'forum': receipt['forum']}))


def metrics(meta, data, cohort, weight, plan):
    codes, groups = pd.factorize(meta.group_id, sort=True); G = len(groups); N = len(meta)
    count = np.bincount(codes, minlength=G); gaincols = []; ys = []; sq = []; losses = []
    for y, base, candidate in data:
        assert np.isfinite(candidate).all() and (candidate > 0).all()
        assert abs(unit(y, candidate).mean()-mean_tweedie_deviance(y, candidate, power=1.5)) < 1e-8
        gain = unit(y, base)-unit(y, candidate); losses.append(gain)
        gaincols.append(np.bincount(codes, weights=gain, minlength=G))
        ys.append(np.bincount(codes, weights=y, minlength=G)); sq.append(np.bincount(codes, weights=np.sqrt(y), minlength=G))
    gaincols = np.column_stack(gaincols); ys = np.column_stack(ys); sq = np.column_stack(sq)
    rng = np.random.default_rng(plan['bootstrap'][cohort.lower()+'_seed']); draws = []
    for _ in range(plan['bootstrap']['replicates']):
        ii = rng.integers(0, G, G); den = 8*(np.sqrt(count[ii].sum()*ys[ii].sum(axis=0))-sq[ii].sum(axis=0))
        assert (den > 0).all(); draws.append(gaincols[ii].sum(axis=0)/den)
    draws = np.asarray(draws); np.save(OUT/(cohort+'_joint_bootstrap.npy'), draws); result = {}
    for j, name in enumerate(NAMES):
        y, base, candidate = data[j]; gain = losses[j]; den = unit(y, np.full(N, y.mean())).sum(); cells = []
        for (line, year, nb), ix in meta.groupby(['line', 'year', 'new_business']).groups.items():
            ii = np.asarray(list(ix)); yy = y[ii]; dd = unit(yy, np.full(len(ii), yy.mean())).sum()
            cells.append({'line': line, 'year': int(year), 'NB': int(nb), 'rows': len(ii),
                          'delta_global': float(gain[ii].sum()/den), 'delta_cell_null': float(gain[ii].sum()/dd),
                          'AE_base': float(yy.sum()/base[ii].sum()), 'AE_candidate': float(yy.sum()/candidate[ii].sum())})
        weighted_den = np.sum(weight*unit(y, np.full(N, np.average(y, weights=weight))))
        result[name] = {'delta': float(gain.sum()/den), 'bootstrap95': np.quantile(draws[:, j], [.025, .975]).tolist(),
                        'simultaneous95_family10': np.quantile(draws[:, j], [.0025, .9975]).tolist(),
                        'post31_delta': float((gaincols[:, j].sum()-np.sort(gaincols[:, j])[::-1][:31].sum())/den),
                        'folds': {str(k): float(gain[meta.fold.eq(k)].sum()/den) for k in range(5)},
                        'years': {str(int(k)): float(gain[meta.year.eq(k)].sum()/den) for k in sorted(meta.year.unique())},
                        'cells': cells, 'worst_cell_delta': min(c['delta_cell_null'] for c in cells),
                        'base_D2': float(1-unit(y, base).sum()/den), 'candidate_D2': float(1-unit(y, candidate).sum()/den),
                        'futureweight_point_only_ESS_failed': float(np.sum(weight*gain)/weighted_den),
                        'same_level_sensitivity': {str(k): float((unit(y, k*base)-unit(y, k*candidate)).sum()/den)
                                                   for k in plan['level_sensitivity']}}
    influence = pd.DataFrame(gaincols, columns=NAMES); influence.insert(0, 'group_id', groups)
    influence.to_parquet(OUT/(cohort+'_group_influence.parquet'), index=False)
    return result


def evaluate_outputs(plan):
    results = {}
    for cohort in ['POOLED', 'TRANSFER']:
        old = pd.read_parquet(P2/'held_nested_prices.parquet' if cohort == 'POOLED' else P4/'held2024_transfer_prices.parquet')
        meta = old[['row_id', 'line', 'year', 'new_business', 'fold', 'group_id', 'T0']].copy().reset_index(drop=True)
        prices = pd.concat([pd.read_parquet(OUT/f'{cohort}_{line}_{k}/prices.parquet') for line in h.LINES for k in range(5)], ignore_index=True).set_index('row_id').loc[meta.row_id]
        base = old.T_B.to_numpy() if cohort == 'POOLED' else old.nominal_mean.to_numpy()
        candidate = prices.new_nominal.to_numpy(); assert np.allclose(prices.old_nominal, base, rtol=2e-15)
        canonical = pd.concat([pd.read_parquet(P1/f'canonical_{line}.parquet', columns=['row_id', 'reserve']) for line in h.LINES]).set_index('row_id').loc[meta.row_id]
        y = meta.T0.to_numpy(float); reserve = canonical.reserve.to_numpy(float)
        ys = [y, y-.25*reserve, y+.25*reserve, y, y]; data = [(y, base, candidate)]
        scenarios = pd.read_parquet(P3/'held_frozen_scenario_prices.parquet').set_index('row_id').loc[meta.row_id] if cohort == 'POOLED' else old.set_index('row_id').loc[meta.row_id]
        saved = meta.copy(); saved['old_nominal'] = base; saved['new_nominal'] = candidate
        for j, name in enumerate(NAMES[1:], 1):
            ob = scenarios[name+'_C'].to_numpy() if cohort == 'POOLED' else scenarios[name+'_mean'].to_numpy()
            nc = candidate*(ob/base)
            assert np.allclose(nc/ob, candidate/base, rtol=3e-15)
            data.append((ys[j], ob, nc)); saved[name+'_old'] = ob; saved[name+'_new'] = nc
        weights = pd.read_parquet(BASE/'estimando_cartera2025_v3/weights.parquet').set_index('row_id').loc[meta.row_id]
        assert np.array_equal(weights.group_id, meta.group_id)
        results[cohort] = metrics(meta, data, cohort, weights.weight.to_numpy(float), plan)
        saved.to_parquet(OUT/(cohort+'_prices.parquet'), index=False)
    return results


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan = w.read(PLAN); assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    execution = {'author': 'Codex', 'pid': os.getpid(), 'utc': utc(), 'script': w.rel(Path(__file__)),
                 'kind': 'P10complete_source_ablation_validation', 'output': w.rel(OUT)}
    dump(OUT/'started.json', execution); state.state_execution(execution)
    try:
        for scope in plan['scopes']:
            cohort, line, outer, held = [scope[k] for k in ['cohort', 'line', 'outer', 'held']]
            folder = OUT/f'{cohort}_{line}_{outer}'; folder.mkdir()
            relative = pd.read_parquet(P9/f'historical_{line}_three_seed.parquet')
            f, current_held, n3 = get_scope(cohort, line, outer, relative); assert held == current_held
            train = f.fold.ne(held)
            assert b.digest(sorted(f.loc[train, 'row_id'])) == scope['training_row_digest']
            event('closed_started', cohort=cohort, line=line, outer=outer, role='primary')
            observed, a = core.learn(f, held, line); dump(folder/'learning.json', a)
            event('closed_completed', cohort=cohort, line=line, outer=outer, role='primary', constants=constants(a))
            assert a['fit_groups_digest'] == scope['training_groups_digest']
            ids, u, norms = forward(f, held, a, n3)
            expected_old, old_price = old_scope(cohort, line, outer, ids)
            adapter = old_price/expected_old; new_price = u*adapter
            bad = f.copy(); bad.loc[~train, ['T0', 'reserve']] = -1e20
            event('closed_started', cohort=cohort, line=line, outer=outer, role='poison')
            adverse_observed, aa = core.learn(bad, held, line); dump(folder/'poison_learning.json', aa)
            event('closed_completed', cohort=cohort, line=line, outer=outer, role='poison', constants=constants(aa))
            _, adverse_u, adverse_norm = forward(bad, held, aa, n3)
            assert b.digest(a) == b.digest(aa) and np.array_equal(observed['S2'], adverse_observed['S2'])
            assert np.array_equal(u, adverse_u) and norms == adverse_norm
            tr = f.loc[train]; comp = a['component']; raw = np.exp(tr.log_relative_A1S.to_numpy())*tr.e_cost_scope.to_numpy()
            for shape in comp['shape']: raw = b.shape_apply(tr, raw, shape)
            moment = math.fsum((tr.T0.to_numpy()/np.sqrt(raw)).tolist())/math.fsum(np.sqrt(raw).tolist())
            assert math.isclose(moment, comp['level'], rel_tol=3e-12)
            pp = pd.DataFrame({'row_id': ids, 'new_ultimate': u, 'old_ultimate': expected_old,
                               'fixed_adapter': adapter, 'old_nominal': old_price, 'new_nominal': new_price})
            pp.to_parquet(folder/'prices.parquet', index=False)
            dump(folder/'committed.json', {'scope': scope, 'held_poison_current_learning_exact': True,
                                           'unchanged_C0_N3_H1_not_reestimated': True,
                                           'moment_relative_error': abs(moment/comp['level']-1),
                                           'ultimate_normalizers': norms,
                                           'outputs': {w.rel(p): w.sha(p) for p in folder.glob('*') if p.is_file()}})
            print(json.dumps({'scope': cohort+'|'+line+'|'+str(outer), 'complete': True}), flush=True)
        results = evaluate_outputs(plan); a = results['POOLED']['NOMINAL']; t = results['TRANSFER']['NOMINAL']
        gates = {'pooled_delta_ge002': a['delta'] >= .002, 'pooled_lower95_positive': a['bootstrap95'][0] > 0,
                 'pooled_atleast4positive_folds': sum(v > 0 for v in a['folds'].values()) >= 4,
                 'both_pooled_years_nonnegative': min(a['years'].values()) >= 0,
                 'pooled_post31_nonnegative': a['post31_delta'] >= 0, 'conditional_transfer_nonnegative': t['delta'] >= 0,
                 'all_nominal_and_stress_cell_floors': all(x['worst_cell_delta'] >= -.001 for c in results.values() for x in c.values())}
        assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
        report = {'author': 'Codex', 'utc': utc(), 'status': 'P10complete_source_ablation_evaluated', 'results': results,
                  'diagnostic_gates': gates, 'new_primary_closed_learners': 30, 'new_adverse_closed_learners_separate': 30,
                  'new_source_fits': 0, 'new_C0_fits': 0, 'new_future2025inference': 0, 'new_finaltestprices': 0,
                  'new_submissions': 0, 'formal_promotion': False, 'submission_allowed': False,
                  'private_improvement_established': False, 'goal_achieved': False, '2024_open': True,
                  'B00_all_alternatives_preserved': True, 'limits': plan['limits'], 'plan_sha256': w.sha(PLAN)}
        dump(OUT/'report.json', report)
        print(json.dumps({'status': report['status'], 'gates': gates, 'results':
                           {k: {name: {q: v[q] for q in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']}
                                for name, v in d.items()} for k, d in results.items()}}))
    except BaseException as exc:
        dump(OUT/('failure_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),
             {'exception': type(exc).__name__, 'message': str(exc), 'committed_scopes': len(list(OUT.glob('*/committed.json'))),
              'next': 'Reconcile saved learners and source cuts; preserve this attempt, no blind refits'})
        raise
    finally: state.state_execution(None)


def replay():
    assert (OUT/'report.json').exists() and not (OUT/'replay_report.json').exists()
    plan = w.read(PLAN); before = w.sha(OUT/'events.jsonl')
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    def reject(*a, **kw): raise AssertionError('No learning or source inference during saved-flow replay')
    guards = [(core, 'learn'), (core, 'fit_component'), (b, 'shape_fit'), (b, 'cell_levels'), (b, 'factor'),
              (g, 'fit_stage'), (core.b, 'shape_fit'), (core.b, 'cell_levels'), (core.b, 'factor'),
              (core.g, 'fit_stage'), (parent.v, 'fit_reporting'), (state.lgb, 'Booster'), (state.lgb, 'train')]
    saved = [(m, key, getattr(m, key)) for m, key in guards]
    for m, key, _ in saved: setattr(m, key, reject)
    try:
        for scope in plan['scopes']:
            cohort, line, outer, held = [scope[k] for k in ['cohort', 'line', 'outer', 'held']]
            folder = OUT/f'{cohort}_{line}_{outer}'; commit = w.read(folder/'committed.json')
            assert all(w.sha(ROOT/p) == z for p, z in commit['outputs'].items())
            f, _, n3 = get_scope(cohort, line, outer, pd.read_parquet(P9/f'historical_{line}_three_seed.parquet'))
            f.loc[f.fold.eq(held), ['T0', 'reserve']] = 1e30
            ids, u, norms = forward(f, held, w.read(folder/'learning.json'), n3)
            prices = pd.read_parquet(folder/'prices.parquet')
            assert np.array_equal(ids, prices.row_id) and np.array_equal(u, prices.new_ultimate)
            assert np.array_equal(u*prices.fixed_adapter.to_numpy(), prices.new_nominal) and norms == commit['ultimate_normalizers']
    finally:
        for m, key, obj in reversed(saved): setattr(m, key, obj)
    assert w.sha(OUT/'events.jsonl') == before
    dump(OUT/'replay_report.json', {'author': 'Codex', 'utc': utc(), 'status': 'P10all30saved_flow_replays_exact',
                                  'learning_and_source_inference_blocked': True, 'held_payload_poisoned': True,
                                  'scopes': 30, 'new_fits': 0, 'new_source_queries': 0,
                                  'report_sha256': w.sha(OUT/'report.json'), 'events_unchanged': True})
    print(json.dumps({'replay': 'exact', 'scopes': 30, 'new_fits': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'run', 'replay'])
    with threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[parser.parse_args().mode]()
