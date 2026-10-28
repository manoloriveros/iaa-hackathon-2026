"""Conciliación de ámbitos reales y optimizador sintético, sin modelos del concurso."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import itertools
import json
import subprocess
import sys

R = Path(__file__).resolve().parents[1]
ROOT = R.parents[1]
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import calibrador_F3c_regularizado as model

OUT = R / 'privado/semana2/F3c_regularizado_20261028/preflight'
PLAN = R / 'registro/semana2_F3c_regularizado_preflight_plan.json'
OLD = R / 'privado/semana2/mision017_fase2/F3c_validacion_completa_20261027'
ACTIVE = R / 'privado/validacion_cadena_f3c_A1_mezcla/20261027T175434Z'
LINES = ['motor', 'buildings', 'contents']


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(2**20), b''): h.update(b)
    return h.hexdigest()


def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def rel(path): return path.relative_to(ROOT).as_posix()
def utc(): return datetime.now(timezone.utc).isoformat()
def digest(values): return hashlib.sha256(json.dumps(sorted(values), separators=(',', ':')).encode()).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f: json.dump(value, f, indent=2, allow_nan=False)


def post(body, identifier, subject):
    p = OUT / (identifier + '.md'); p.write_text(body, encoding='utf-8')
    r = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor', 'Codex', '--id', identifier, '--asunto', subject, '--cuerpo', str(p)],
        check=True, capture_output=True, text=True, encoding='utf-8')
    return json.loads(r.stdout)


def register():
    assert not PLAN.exists() and not OUT.exists()
    phase = read(R / 'registro/semana2_mision017_fase2_actual.json')
    assert not phase.get('active_execution') and not phase.get('active_jobs')
    OUT.mkdir(parents=True)
    paths = [Path(__file__), Path(model.__file__), R / 'registro/semana2_F3c_regularizado_plan.json',
        R / 'herramientas/evaluar_F3c_completo.py', R / 'herramientas/validar_F3c_completo.py',
        R / 'herramientas/ampliar_validacion_cadena_f3c.py', OLD / 'parameters.json',
        OLD / 'source_history_admission.json', ACTIVE / 'curves_full.json', ACTIVE / 'source_training_complete.json']
    paths += [ACTIVE / 'prepared' / f'emerging_{line}.parquet' for line in LINES]
    paths += [ACTIVE / 'prepared/emerging_claims.parquet']
    for line in LINES:
        for family in ['N0', 'F1']:
            for seed in [11, 12, 13]:
                namespace = 'source_original_history' if family == 'F1' else 'source'
                paths.append(OLD / namespace / line / 'baseline' / f'{family}_seed{seed}' / 'complete.json')
        paths += [ACTIVE / 'models' / f'fold{k}' / f'{line}_receipt.json' for k in range(5)]
    plan = {'author': 'Codex', 'utc': utc(), 'scope': 'real lineage inventory and synthetic constrained optimizer only',
        'authorization': 'Proceed with proposed F3c-R. No new submission without evidence.',
        'pre_score_clarification': '16 terminal feature scopes require 10 additional leave-three-fold source/base scopes to preserve the historical OOF input to C1/F2/own learning. Total26 upstream source scopes; no extra candidate or score.',
        'known_dependency': 'A1 source fitting uses reverse-KM curves pooled with emerging2023 claims. Frozen full source raw is not internally independent merely because the trees fit developed rows.',
        'scope_closure': {'terminal_excluded_fold_sizes': [0, 1, 2], 'base_ancestor_excluded_fold_sizes': [0, 1, 2, 3]},
        'no_real_fit_before_actual_scope_admission': True,
        'optimizer': {'primary': 'L-BFGS-B analytic gradient, maxiter5000, ftol1e-14, gtol1e-9, maxls50, maxcor20',
            'independent_solver': 'SLSQP maxiter5000 ftol1e-14', 'KKT_limit': 1e-6,
            'unsupported_columns': 'exact zero, including absent cells', 'failure': 'keep failed receipt, no clipping or outcome-based threshold changes'},
        'synthetic_tests': ['full common-lambda selector', 'held payload corruption before selection', 'positive train perturbation',
            'alternative constrained optimizer', 'replay without fitting', 'currency scaling', 'missing cell identity', 'invalid inputs and group overlap rejection'],
        'current_budget': {'real_fits': 0, 'C0_fits': 0, 'real_predictions': 0, 'scores': 0, 'submissions': 0,
            'synthetic_optimizer_fits_max': 36},
        'sources': {rel(p): sha(p) for p in paths}}
    dump(PLAN, plan)
    forum = post('Codex. Inicio el preflight autorizado de F3c-R. Antes de ajustar, el grafo de dependencias muestra que A1 usa curvas con siniestros emergentes2023: sus raw completos no son OOF internos independientes. Los16 ambitos terminales necesitan ademas10 ambitos base con tres folds excluidos para conservar el aprendizajeOOF de C1/F2/factores. Conciliare26 ambitos fuente sin entrenar, conservando cualquier incompatibilidad. Implemento optimizador acotado y selector comun con datos sinteticos, KKT<1e-6, replay/veneno y segundo optimizador. No cambio receta, criterios o lambda por scores. Cero modelos/curvas/precios/scores reales o envios en este preflight. Plan '+rel(PLAN)+' SHA '+sha(PLAN)+'.',
        'COD-S2-20261028-F3CR-PREFLIGHT-PREVIO', 'F3c-R: dependencias anidadas y optimizador antes de ajustar')
    dump(OUT / 'registration.json', {'plan_sha256': sha(PLAN), 'forum': forum})
    print(json.dumps({'registered': True, 'sources': len(paths), 'forum': forum}))


def guard():
    assert sha(PLAN) == read(OUT / 'registration.json')['plan_sha256']
    amendment = read(OUT / 'inventory_reader_amendment.json') if (OUT / 'inventory_reader_amendment.json').exists() else None
    for p, h in read(PLAN)['sources'].items():
        if amendment and p == rel(Path(__file__)):
            assert h == amendment['old_code_sha256']
            h = amendment['new_code_sha256']
        assert sha(ROOT / p) == h, p


def inventory():
    guard()
    cols = ['row_id', 'year', 'group', 'fold', 'customer_id', 'address_id', 'new_business', 'line']
    rows = pd.concat([pd.read_parquet(ACTIVE / 'prepared' / f'emerging_{l}.parquet', columns=cols,
                         filters=[('year', '==', 2023)]) for l in LINES], ignore_index=True)
    assert rows.row_id.is_unique and len(rows) == 50094 and rows.fold.notna().all()
    assert rows.groupby('group').fold.nunique().max() == 1
    for key in ['customer_id', 'address_id']: assert rows.groupby(key).fold.nunique().max() == 1
    rows['fold'] = rows.fold.astype(int)
    claims = pd.read_parquet(ACTIVE / 'prepared/emerging_claims.parquet',
        columns=['claim_id', 'row_id', 'accepted', 'loss_date', 'period_year', 'row_fold', 'peril'])
    claims = claims.loc[claims.accepted & claims.period_year.eq(2023) & claims.loss_date.dt.year.le(2023)].copy()
    assert claims.row_id.isin(rows.row_id).all()
    mapped = claims.row_id.map(rows.set_index('row_id').fold)
    assert np.array_equal(mapped, claims.row_fold)
    scopes = []
    for size in range(4):
        for excluded in itertools.combinations(range(5), size):
            train = rows.loc[~rows.fold.isin(excluded)]
            held = rows.loc[rows.fold.isin(excluded)]
            assert set(train.group).isdisjoint(set(held.group))
            protected_claims = claims.loc[claims.row_fold.isin(excluded)]
            available_claims = claims.loc[~claims.row_fold.isin(excluded)]
            assert set(available_claims.row_id).issubset(set(train.row_id))
            tag = 'all' if not excluded else 'exclude_' + ''.join(map(str, excluded))
            membership = train[['row_id', 'group', 'fold', 'line', 'new_business']]
            path = OUT / 'scope_keys' / (tag + '.parquet'); path.parent.mkdir(exist_ok=True)
            if path.exists():
                assert pd.read_parquet(path).equals(membership.reset_index(drop=True)), 'El checkpoint no coincide'
            else:
                membership.to_parquet(path, index=False)
            counts = train.groupby(['line', 'new_business']).size()
            assert len(counts) == 6 and (counts > 0).all()
            scopes.append({'scope': tag, 'excluded_folds': list(excluded), 'terminal_scope': size <= 2,
                'rows': len(train), 'groups': train.group.nunique(), 'rows_digest': digest(train.row_id.tolist()),
                'groups_digest': digest(set(train.group)), 'keys': rel(path), 'keys_sha256': sha(path),
                'allowed_claims': len(available_claims), 'protected_claims_in_full_A1_curve_ancestor': len(protected_claims),
                'full_A1_cached_raw_eligible_for_this_scope': size == 0,
                'singlefold_N0_seed11_cache_candidate': size == 1,
                'numeric_full_recipe_input_ready': False})
    cached = []
    for p in read(PLAN)['sources']:
        if p.endswith('/complete.json') or ('/models/fold' in p and p.endswith('_receipt.json')):
            j = read(ROOT / p)
            cached.append({'receipt': p, 'sha256': sha(ROOT / p),
                'arguments_sha256': j['arguments_sha256'], 'model_sha256': j['model_sha256'],
                'reuse_status': 'candidate until exact scope arguments and complete producer lineage match'})
    assert len(scopes) == 26 and sum(s['terminal_scope'] for s in scopes) == 16 and len(cached) == 33
    # Synthetic lineage negative control: a full-data ancestor must fail every proper subset.
    assert all(s['protected_claims_in_full_A1_curve_ancestor'] > 0 for s in scopes if s['excluded_folds'])
    rec = {'author': 'Codex', 'utc': utc(), 'scope_membership_passed': True,
        'full_cached_source_reuse_admitted': False, 'ready_for_real_calibrator_fit': False,
        'rows_2023': len(rows), 'terminal_scopes': 16, 'all_source_base_scopes': 26,
        'terminal_proper_scopes_rejecting_full_curve_ancestor': 15,
        'all_proper_scopes_rejecting_full_curve_ancestor': 25,
        'scopes': scopes, 'cached_source_receipts': cached,
        'source_budget_before_numeric_reuse_proof': {'total_A1_model_pairs_required': 26 * 18,
            'full_scope_existing_pairs': 18, 'singlefold_existing_N0_seed11_pairs_candidates': 15,
            'new_primary_native_fit_calls_if_all_candidates_match': 870,
            'new_primary_native_fit_calls_if_only_full_scope_reused': 900,
            'definition': 'One source pair is early-stopping fit plus full fit. Not a time estimate; no fit launched.',
            'RKM_inner_and_full_bundles_required': 52,
            'additional_adverse_controls_and_reporting_fit_budget': 'must freeze in producer admission; not included in native primary bounds'},
        'T2b': 'source curves depend only on developed rows; target mixture weights/levels/C1 must still be own-scope',
        'next_required': 'Produce or reuse-by-exact-arguments scoped A1 curves/models/raw, then own-scope target bases/F2/own. Do not train calibrator on full2023 raw under an OOF label.',
        'new_real_fits': 0, 'new_C0_fits': 0, 'new_real_scores': 0, 'new_submissions': 0}
    dump(OUT / 'scope_inventory.json', rec)
    print(json.dumps({k: rec[k] for k in ['scope_membership_passed', 'ready_for_real_calibrator_fit',
        'terminal_scopes', 'all_source_base_scopes', 'terminal_proper_scopes_rejecting_full_curve_ancestor', 'source_budget_before_numeric_reuse_proof']}))


def synthetic():
    guard()
    rng = np.random.default_rng(2026102802)
    n = 900
    cell = np.arange(n) % 6
    z = rng.normal(0, .4, n); z[np.isin(cell, [1, 4])] = 0
    base = np.exp(rng.normal(3, .7, n))
    y = base * np.exp(.3 * (cell == 0) - .2 * (cell == 4) + 1.7 * z)
    y[rng.random(n) < .35] = 0
    frame = pd.DataFrame({'row_id': [f's{i}' for i in range(n)], 'group_id': [f'g{i // 3}' for i in range(n)],
        'fold': (np.arange(n) // 3) % 5, 'cell': cell, 'signal': z, 'base': base, 'y': y, 'is_held': np.arange(n) >= 750})
    held = frame.loc[frame.is_held].copy()
    counts = {'primary': 0, 'independent': 0}
    original = model.fit
    def counted(*a, **kw):
        counts['independent' if kw.get('independent') else 'primary'] += 1
        return original(*a, **kw)
    model.fit = counted
    bundle = model.synthetic_bundle(frame, held)
    altered = frame.copy()
    for c in ['y', 'base', 'signal', 'cell', 'fold']:
        altered.loc[altered.is_held, c] = -99999
    poison = model.synthetic_bundle(altered, held)
    tr = frame.loc[~frame.is_held]
    pos = tr.y.copy(); pos.iloc[::4] *= 3
    positive = model.fit(tr.base, tr.signal, tr.cell, pos, bundle['selection']['lambda'])
    other = model.fit(tr.base, tr.signal, tr.cell, tr.y, bundle['selection']['lambda'], independent=True)
    scaled = model.fit(100 * tr.base, tr.signal, tr.cell, 100 * tr.y, bundle['selection']['lambda'])
    missing = tr.loc[tr.cell != 5]
    miss = model.fit(missing.base, missing.signal, missing.cell, missing.y, .1)
    realfit_count = sum(counts.values()); assert realfit_count == 36
    model.fit = lambda *a, **k: (_ for _ in ()).throw(AssertionError('Replay must not fit'))
    saved = json.loads(json.dumps(bundle))
    prediction = model.predict(held.base, held.signal, held.cell, saved['final'])
    reverse = model.predict(held.base.iloc[::-1], held.signal.iloc[::-1], held.cell.iloc[::-1], saved['final'])
    checks = {'held_payload_before_selector_exact': bundle == poison,
        'positive_training_perturbation_effective': not np.allclose(positive['beta'], bundle['final']['beta']),
        'all_primary_KKT': all(m['projected_gradient_inf'] < 1e-6 for m in bundle['members'] + [bundle['final']]),
        'independent_solver_loss': abs(other['loss'] - bundle['final']['loss']) < 1e-10,
        'independent_solver_predictions': np.allclose(prediction, model.predict(held.base, held.signal, held.cell, other), rtol=2e-6),
        'currency_invariance_parameters': np.allclose(scaled['beta'], bundle['final']['beta'], rtol=1e-6, atol=1e-7),
        'absent_cell_identity': miss['beta'][5] == miss['beta'][11] == 0,
        'permutation_replay': np.allclose(prediction, reverse[::-1], rtol=1e-14),
        'single_row_replay': all(np.allclose(prediction[k], model.predict([r.base], [r.signal], [r.cell], saved['final'])[0], rtol=1e-14) for k, r in enumerate(held.itertuples())),
        'tie_prefers_strong_penalty': model.select([1., 1., 1.])['lambda'] == 1.,
        'zero_building_gamma': bundle['final']['beta'][7] == bundle['final']['beta'][10] == 0,
        'bound_feasibility': all(0 <= x <= 1 for x in bundle['final']['beta'][6:])}
    for tag, args in [('nonpositive_base', ([0.], [0.], [0])), ('unknown_cell', ([1.], [0.], [8])),
                      ('building_signal', ([1.], [.3], [1])), ('nan_signal', ([1.], [float('nan')], [0]))]:
        try: model.predict(*args, saved['final'])
        except ValueError: checks['reject_' + tag] = True
        else: checks['reject_' + tag] = False
    overlap = held.copy(); overlap['group_id'] = tr.group_id.iloc[0]
    try: model.synthetic_bundle(frame, overlap)
    except ValueError: checks['reject_group_overlap'] = True
    else: checks['reject_group_overlap'] = False
    model.fit = original
    dump(OUT / 'synthetic_optimizer.json', {'author': 'Codex', 'utc': utc(), 'checks': {k: bool(v) for k, v in checks.items()},
        'all_passed': all(checks.values()), 'synthetic_optimizer_fits': realfit_count, 'fit_counts': counts,
        'rows': n, 'bundle': bundle, 'independent_solver': other, 'new_real_fits': 0,
        'scope': 'Optimizer and selector on fixed synthetic b/z inputs; not proof of the real upstream learner',
        'new_scores': 0, 'new_submissions': 0})
    print(json.dumps({'all_passed': all(checks.values()), 'checks': {k: bool(v) for k, v in checks.items()}, 'synthetic_fits': realfit_count}))
    assert all(checks.values())


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('mode', choices=['register', 'inventory', 'synthetic'])
    globals()[p.parse_args().mode]()
