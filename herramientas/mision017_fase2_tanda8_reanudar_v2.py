"""Reanuda nueve ajustes pendientes con ftol más estricto; conserva dos modelos por SHA."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import subprocess
import sys
import time
import os

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('scientific8', R / 'herramientas/mision017_fase2_tanda8_poisson.py')
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

OUT = b.OUT.parent / 'tanda8_poisson_20261026_v2'
PLAN = R / 'registro/semana2_mision017_fase2_tanda8_plan_v2.json'
sha = b.sha; read = b.read; dump = b.dump; rel = b.rel; now = b.now
SOURCE_INPUTS = b.OUT
CURRENT = {}
ORIGINAL_MINIMIZE = b.optimize.minimize

def stricter_minimize(fun, initial, **kwargs):
    assert kwargs['options']['ftol'] == 1e-12 and kwargs['method'] == 'L-BFGS-B'
    options = dict(kwargs['options']); options['ftol'] = 1e-15
    kwargs = {**kwargs, 'options': options}
    result = ORIGINAL_MINIMIZE(fun, initial, **kwargs)
    value, gradient = fun(result.x)
    name = CURRENT['line'] + '_' + CURRENT['peril']
    dump(OUT / f'solver_{name}.json', {'utc': now(), 'options': options, 'coef': result.x.tolist(),
        'success': bool(result.success), 'message': str(result.message), 'nit': int(result.nit),
        'objective': float(value), 'max_abs_gradient': float(np.abs(gradient).max()),
        'raw_gradient': gradient.tolist(), 'checkpoint_before_scientific_guard': True,
        'scientific_gradient_guard_unchanged': 1e-6})
    return result

def register():
    assert not OUT.exists() and not PLAN.exists(); OUT.mkdir(parents=True)
    old = read(b.PLAN); terminal = read(b.OUT / 'terminal_reconciliation.json')
    assert terminal['terminal_exit_code'] == 1 and terminal['source_GLM_attempts'] == 3 and terminal['no_oof_or_price_report']
    for path, digest in old['sources'].items(): assert sha(ROOT / path) == digest, path
    for name, digest in terminal['completed_models'].items():
        assert sha(b.OUT / name) == digest
        (OUT / name).write_bytes((b.OUT / name).read_bytes()); assert sha(OUT / name) == digest
    probe = ORIGINAL_MINIMIZE(lambda x: (float(np.dot(x, x)), 2 * x), np.array([2., -3.]), jac=True,
        method='L-BFGS-B', options={'maxiter': 2000, 'gtol': 1e-8, 'ftol': 1e-15, 'maxls': 50})
    assert probe.success and np.max(abs(probe.jac)) < 1e-6
    sources = {**old['sources'], rel(b.PLAN): sha(b.PLAN), rel(Path(__file__)): sha(Path(__file__)),
        rel(b.OUT / 'terminal_reconciliation.json'): sha(b.OUT / 'terminal_reconciliation.json')}
    sources.update({rel(b.OUT / n): h for n, h in terminal['completed_models'].items()})
    plan = {'id': 'S2-MISION017-FASE2-TANDA8-NUMERICAL-RESUME-v2', 'author': 'Codex', 'utc': now(),
        'scientific_plan': rel(b.PLAN), 'scientific_plan_sha256': sha(b.PLAN),
        'hypothesis_features_objective_precision_and_acceptance_unchanged': True,
        'numeric_change': {'ftol_before': 1e-12, 'ftol_now': 1e-15, 'maxiter': 2000, 'gtol': 1e-8,
            'scientific_max_gradient_still': 1e-6, 'checkpoint_optimizer_result_before_guard': True},
        'completed_models_reused': terminal['completed_models'], 'remaining_primary_models': 9,
        'accounting': {'v1_successful_GLMs': 2, 'v1_failed_GLM_attempts': 1, 'new_primary_GLM_fits': 9,
            'total_primary_GLM_attempts': 12, 'unique_accepted_models_target': 11,
            'conditional_observation_stress_fits_max': 11, 'new_C0_fits': 0, 'submissions': 0},
        'criterion': old['criterion'], 'bootstrap': old['bootstrap'], 'sources': sources,
        'no_target_scores_consulted_before_repair': True, 'all_failed_versions_preserved': True,
        'B00_preserved': True, 'goal_achieved': False}
    dump(PLAN, plan)
    body = OUT / 'forum_reanudacion.md'
    body.write_text('El primer proceso de la tanda 8 terminó en el tercer GLM porque no pasó el gradiente máximo registrado, '
        'aunque el solver declaró convergencia por reducción relativa. No produjo OOF ni puntuación objetivo. '
        'Los dos modelos terminados se conservan por SHA y se reutilizan sin ajuste.\n\n'
        'La reparación exige ftol 1e-15, más preciso que 1e-12, y guarda el resultado del optimizador antes de comprobar el gradiente. '
        'No cambia variables, objetivo Poisson, priors, datos, C0 o el límite de gradiente 1e-6. '
        'Quedan nueve ajustes; el intento fallido se cuenta, de modo que el coste principal será 12 intentos para 11 modelos únicos. '
        'Los resultados y coeficientes del intento fallido no quedaron guardados en v1; no se inventa un valor de su gradiente. '
        'Se mantiene el presupuesto condicional de observación, solo si una variante supera la validación. Cero envíos. '
        'Enmienda numérica: ' + rel(PLAN) + '.\n', encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-FASE2-TANDA8-REANUDACION-PREVIO', '--asunto',
        'Poisson: reanudación numérica con dos modelos conservados y gradiente sin relajar', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': sha(PLAN), 'forum': json.loads(p.stdout)})
    print(json.dumps({'registered': rel(PLAN), 'models_reused': 2, 'new_primary_fits_budget': 9,
        'failed_attempts_accounted': 1, 'C0_fits': 0, 'submissions': 0}))

def run():
    plan = read(PLAN); assert read(OUT / 'registration.json')['plan_sha256'] == sha(PLAN)
    for path, digest in plan['sources'].items(): assert sha(ROOT / path) == digest, path
    assert not (OUT / 'started.json').exists(); dump(OUT / 'started.json', {'utc': now(), 'pid': os.getpid()})
    old = pd.read_parquet(b.m.CV / 'oof_2023_2024.parquet')
    weights = pd.read_parquet(b.WEIGHTS / 'weights.parquet', columns=['row_id', 'weight']); outputs = []; new_fits = 0; reused = 0
    b.optimize.minimize = stricter_minimize
    try:
        with threadpool_limits(limits=2):
            for line in b.MAP:
                f = pd.read_parquet(SOURCE_INPUTS / f'source_{line}.parquet'); models = {}
                for peril in b.MAP[line]:
                    path = OUT / f'{line}_{peril}.json'
                    if path.name in plan['completed_models_reused']:
                        assert sha(path) == plan['completed_models_reused'][path.name]
                        a = read(path); reused += 1
                    else:
                        CURRENT.clear(); CURRENT.update(line=line, peril=peril)
                        print(json.dumps({'event': 'fit_started', 'line': line, 'peril': peril}), flush=True)
                        a = b.fit(f, line, peril); new_fits += 1
                        dump(path, {**a, 'source_input_sha256': sha(SOURCE_INPUTS / f'source_{line}.parquet')})
                        print(json.dumps({'event': 'fit_completed', 'line': line, 'peril': peril, 'new_fits': new_fits,
                            'weather_coefficient': a['weather_coefficient'], 'max_gradient': a['max_abs_gradient']}), flush=True)
                    models[peril] = a
                t = old.loc[old.line.eq(line)].merge(pd.read_parquet(SOURCE_INPUTS / f'target_{line}.parquet')[['row_id', *b.DELTA]], on='row_id', validate='one_to_one')
                t = t.merge(weights, on='row_id', validate='one_to_one')
                for name in ['P1', 'P2', 'P3']: t[name] = np.nan
                for held in range(5):
                    parent = b.m.CV / f'learning_{line}_fold{held}.json'; c0 = read(parent)['artifact']['C0']
                    assert sorted(t.loc[t.fold.ne(held), 'row_id']) == c0['fit_row_ids']
                    valid = t.loc[t.fold.eq(held)]; normalizers = {}
                    for name, strength in [('P1', 1.), ('P2', .5), ('P3', .25)]:
                        prediction, norm = b.apply(valid, valid.N3.to_numpy(float), models, c0['mixture'], strength)
                        t.loc[t.fold.eq(held), name] = prediction; normalizers[name] = norm
                    dump(OUT / f'normalizers_{line}_fold{held}.json', {'parent_C0': rel(parent), 'parent_C0_sha256': sha(parent), 'normalizers': normalizers})
                outputs.append(t)
    finally: b.optimize.minimize = ORIGINAL_MINIMIZE
    p = pd.concat(outputs, ignore_index=True); assert len(p) == 109296 and p.row_id.is_unique and new_fits == 9 and reused == 2
    p.to_parquet(OUT / 'oof_2023_2024.parquet', index=False)
    y = p.T0.to_numpy(float); den = b.m.unit(y, np.full(len(y), y.mean())).sum()
    scores = {name: float(1 - b.m.unit(y, p[name].to_numpy(float)).sum() / den) for name in ['N3', 'P1', 'P2', 'P3']}
    dump(OUT / 'price_report.json', {'author': 'Codex', 'utc': now(), 'status': 'prices_scored_validation_pending',
        'scores': scores, 'source_unique_GLMs': 11, 'source_GLM_attempts_total': 12,
        'source_GLM_attempts_failed_v1': 1, 'source_GLMs_reused': reused, 'new_GLM_fits_this_resume': new_fits,
        'new_C0_fits': 0, 'new_source_T2b_inferences': 0, 'covariate_only_normalizers': 180,
        'new_test_predictions': 0, 'new_submissions': 0, 'B00_preserved': True, 'goal_achieved': False})
    print(json.dumps({'scores': scores, 'unique_GLMs': 11, 'total_attempts': 12, 'reused': reused, 'new_fits': new_fits, 'submissions': 0}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['register', 'run']); args = parser.parse_args()
    try: register() if args.mode == 'register' else run()
    except Exception as exc:
        if OUT.exists(): dump(OUT / f'failure_{args.mode}_{time.time_ns()}.json', {'utc': now(), 'mode': args.mode,
            'error': type(exc).__name__, 'message': str(exc), 'preserve_solver_checkpoints_and_completed_models': True})
        raise
