"""Recupera solo los componentes fuente faltantes de motor y contenidos."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'; HOME = BASE / 'FSp_MC_recuperacion_20261026_v1'
MATRIX = HOME / 'matrices'; OUT = HOME / 'productor'
PLAN = R / 'registro/semana2_mision017_FSp_MC_recuperacion_plan_v1.json'
ORIGINAL = ROOT / 'Hackaton/Semana 2/Claude/mision017_20261025/exp26_20261026/ml2'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


w = load('writer_MC_recovery', R / 'herramientas/registrar_avance_mision017_fase2.py')
common = load('building_recovery_pure_helpers', R / 'herramientas/recuperar_productor_FSp_edificios.py')
import numpy as np
import pandas as pd
import lightgbm as lgb
PF, PS = common.PF, common.PS


def dump(p, a):
    p.write_text(json.dumps(a, ensure_ascii=False, indent=2), encoding='utf8')


def sources():
    report = w.read(MATRIX / 'report.json')
    paths = [Path(__file__), Path(common.__file__), MATRIX / 'report.json', HOME / 'received_output_inventory.json']
    paths += [MATRIX / name for name in report['outputs']]
    for line in ['motor', 'contents']:
        paths += [BASE / f'recuentos_fuente2024_v1/counts_{line}.parquet']
        paths += [ORIGINAL / f'trabajo/pred/fsp/{line}{suffix}_meta.json' for suffix in ['', '_prod']]
    return {w.rel(p): w.sha(p) for p in paths}


def register():
    assert not PLAN.exists() and not OUT.exists()
    report = w.read(MATRIX / 'report.json')
    assert report['new_fits'] == 0 and report['numeric_recovery_budget_if_registered'] == 36
    assert all(a['raw_precision_restored'] for a in report['lines'].values())
    OUT.mkdir()
    plan = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
            'hypothesis': 'Missing numerical f/s outputs prevent isolating FSp from the received composite F4c residual factors. Recover the existing two-line source producer, not new architectures or another round search.',
            'necessity': 'Selected received roots contain code/metadata/CSV but no numerical FSp Parquet or saved Boosters. Inventory and196feature/18scalar checks are archived.',
            'reference': 'No predictive comparison or candidate promotion in this recovery; preserve F3c/B00 and buildings models already completed.',
            'source_years': {'dev': [2021, 2022, 2023], 'prod': [2021, 2022, 2023, 2024]},
            'target_covariates': [2023, 2024, 2025], 'no_target_response_loaded': True,
            'climate': {'dev': {'source': [2021, 2022, 2023], 'target': [2023]},
                        'prod': {'source': [2021, 2022, 2023, 2024], 'target': [2023, 2024]}},
            'history': 'historia2 explicitly: [min(inception,V)-365days,min(inception,V)), V=2024-12-31',
            'parameters': {'f': PF, 's': PS},
            'rounds': {line: {phase: w.read(ORIGINAL / f'trabajo/pred/fsp/{line}{suffix}_meta.json')
                              for phase, suffix in [('dev', ''), ('prod', '_prod')]} for line in ['motor', 'contents']},
            'offset': 'Reuse saved b0/mean mark and original max(source_E_cost/source_exposure,1e-4); no CDF/C0 estimation.',
            'semantics': 'Cost-completion Poisson f times observed positive mark s is a cost proxy. f already includes calendar period exposure once; never apply future cp=0 to an ultimate price.',
            'criteria': ['Pinned sources unchanged', '36saved models and keyed per-row f/s/raw fields',
                         'Exact save/load and row-order replay', 'Independent sum of tree leaves and exponent/offset/exposure arithmetic',
                         'All outputs finite/positive and source/count row alignment exact'],
            'budget': {'source_component_model_fits': 36, 'new_early_stopping_searches': 0, 'new_C0_fits': 0,
                       'new_target_price_fits': 0, 'new_calibrations': 0, 'new_scores': 0, 'new_aggregated_price_CSVs': 0, 'new_submissions': 0},
            'reconstruction_not_exact_original_tree_replay': True, 'predictive_admission': False,
            'B00_all_alternatives_preserved': True, '2024_open': True, 'sources': sources()}
    dump(PLAN, plan)
    body = OUT / 'forum_previo.md'
    body.write_text('Codex. Registro antes de ajustar la recuperación faltante de FSp en motor y contenidos. '
        'La búsqueda acotada de los aportes recibidos no encontró sus salidas por fila ni Boosters; sí están el código y las rondas elegidas. '
        'Pasaron 196 cotejos de variables y 18 de recuento/marca/offset. '
        'Se harán 36 ajustes fuente Poisson/Gamma con esas rondas fijas, sin nueva búsqueda, C0 o aprendizaje emergente. '
        'Se guardarán todos los modelos y componentes con sus pruebas de replay y aritmética. '
        'No se repiten los 24 modelos de edificios ya completos. La disponibilidad de historia2 queda explícita y los maestros sin fecha siguen condicionados. '
        'El productor usa completitud de coste y no identifica separadamente frecuencia y severidad de último. '
        'Esta recuperación no puntúa, elige pesos o genera un CSV de entrega. B00/F3c y todas las alternativas permanecen; 2024 abierto. '
        'Plan y hashes: ' + w.rel(PLAN) + '.', encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-MISION017-FSP-MC-RECUPERACION-PREVIO',
        '--asunto', 'Motor y contenidos: recuperación de componentes faltantes con rondas fijas', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': w.sha(PLAN), 'forum': json.loads(response.stdout)})
    print(json.dumps({'registered': True, 'source_fit_budget': 36, 'forum': json.loads(response.stdout)}))


def run():
    assert not (OUT / 'report.json').exists()
    registration = w.read(OUT / 'registration.json'); assert w.sha(PLAN) == registration['plan_sha256']
    plan = w.read(PLAN); assert sources() == plan['sources']
    assert not (OUT / 'started.json').exists(), 'Reconcile prior execution/model checkpoints before rerunning.'
    dump(OUT / 'started.json', {'pid': os.getpid(), 'utc': datetime.now(timezone.utc).isoformat(), 'plan_sha256': w.sha(PLAN)})
    fitted = []; outputs = {}; start = time.monotonic()
    for line in ['motor', 'contents']:
        counts = pd.read_parquet(BASE / f'recuentos_fuente2024_v1/counts_{line}.parquet')
        for phase in ['dev', 'prod']:
            rows = pd.read_parquet(MATRIX / f'rows_{line}_source_{phase}.parquet')
            target = pd.read_parquet(MATRIX / f'rows_{line}_target_{phase}.parquet')
            X = pd.read_parquet(MATRIX / f'matrix_{line}_source_{phase}.parquet')
            Xe = pd.read_parquet(MATRIX / f'matrix_{line}_target_{phase}.parquet')
            cn = counts.loc[counts.year.isin(plan['source_years'][phase])].reset_index(drop=True)
            assert np.array_equal(cn.row_id, rows.row_id) and np.array_equal(cn.exposure, rows.exposure)
            assert len(X) == len(cn) and len(Xe) == len(target)
            result = target[['row_id', 'year', 'exposure']].copy()
            for peril, old in sorted(plan['rounds'][line][phase].items()):
                n = cn['N_' + peril].to_numpy(float); cost = cn['T0_cents_' + peril].to_numpy(float) / 100.
                e = cn.exposure.to_numpy(float); q = cn['E_cost_' + peril].to_numpy(float) / e
                off = np.log(e * np.maximum(q, 1e-4)) + old['b0']; positive = (n > 0) & (cost > 0)
                assert int(n.sum()) == old['n_dev']
                assert abs(np.log(n.sum() / np.sum(e * np.maximum(q, 1e-4))) - old['b0']) < 1e-12
                assert abs(cost[positive].sum() / n[positive].sum() / old['sev_media'] - 1) < 1e-10
                for kind, params, rounds in [('f', PF, old['rondas_f']), ('s', PS, old['rondas_s'])]:
                    key = f'{line}_{phase}_{peril}_{kind}'; folder = OUT / key; folder.mkdir()
                    dump(folder / 'fit_started.json', {'utc': datetime.now(timezone.utc).isoformat(), 'plan_sha256': w.sha(PLAN), 'rounds': rounds})
                    if kind == 'f':
                        train = lgb.Dataset(X, label=n, init_score=off); fit_rows = len(X)
                    else:
                        fit_rows = int(positive.sum())
                        train = lgb.Dataset(X.loc[positive].reset_index(drop=True), label=cost[positive] / n[positive],
                                            weight=n[positive], init_score=np.full(fit_rows, np.log(old['sev_media'])))
                    model = lgb.train(params, train, num_boost_round=int(rounds)); model_path = folder / 'model.txt'
                    model.save_model(str(model_path))
                    record = {'line': line, 'phase': phase, 'peril': peril, 'kind': kind, 'fit_rows': fit_rows,
                              'requested_rounds': rounds, 'actual_rounds': model.current_iteration(),
                              'model_sha256': w.sha(model_path), 'plan_sha256': w.sha(PLAN), 'lightgbm_version': lgb.__version__}
                    dump(folder / 'record.json', record)  # Retain fit even if a later inference check fails.
                    raw = model.predict(Xe, raw_score=True, num_threads=2)
                    sample = np.unique(np.linspace(0, len(Xe) - 1, 64, dtype=int)); loaded = lgb.Booster(model_file=str(model_path))
                    assert np.array_equal(raw[sample], loaded.predict(Xe.iloc[sample], raw_score=True, num_threads=2))
                    assert np.array_equal(raw[sample[::-1]], loaded.predict(Xe.iloc[sample[::-1]], raw_score=True, num_threads=2))
                    error = float(np.max(np.abs(common.leaf_sum(loaded, Xe.iloc[sample[:8]]) - raw[sample[:8]])))
                    assert error < 1e-11
                    base = old['b0'] if kind == 'f' else np.log(old['sev_media'])
                    value = np.exp(raw + base)
                    if kind == 'f': value *= target.exposure.to_numpy()
                    other = np.exp(raw[sample]) * np.exp(base)
                    if kind == 'f': other *= target.exposure.to_numpy()[sample]
                    assert np.allclose(value[sample], other, rtol=2e-14, atol=0)
                    assert np.isfinite(value).all() and (value > 0).all()
                    result[kind + '_' + peril] = value; result['raw_' + kind + '_' + peril] = raw
                    fitted.append({**record, 'save_load_shuffle_exact': True, 'independent_leaf_sum_max_error': error,
                                   'offset_exposure_math_passed': True, 'component_min': float(value.min()), 'component_max': float(value.max())})
                    print(json.dumps({'completed': key, 'models': len(fitted), 'elapsed_seconds': round(time.monotonic() - start, 1)}), flush=True)
                    del model, loaded, train
            path = OUT / f'components_{line}_{phase}.parquet'; result.to_parquet(path, index=False)
            assert pd.read_parquet(path).equals(result.reset_index(drop=True))
            outputs[path.name] = {'sha256': w.sha(path), 'rows': len(result), 'test_rows': int(target.is_test.sum())}
            del X, Xe, cn, result, rows, target
        del counts
    assert len(fitted) == 36 and sources() == plan['sources']
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
              'status': 'MC_numerical_producers_complete_predictive_admission_pending', 'models': fitted, 'outputs': outputs,
              'new_source_component_model_fits': 36, 'new_early_stopping_searches': 0, 'new_C0_fits': 0,
              'new_target_price_fits': 0, 'new_calibrations': 0, 'new_scores': 0, 'new_aggregated_price_CSVs': 0, 'new_submissions': 0,
              'new_component_row_predictions_before_replays': 20 * outputs['components_motor_prod.parquet']['rows'] + 16 * outputs['components_contents_prod.parquet']['rows'],
              'source_inputs_unchanged': True, 'plan_sha256': w.sha(PLAN),
              'original_producer_author': 'Claude', 'reconstruction_author': 'Codex',
              'original_exact_tree_replay_not_established': True, 'semantics': plan['semantics'],
              'predictive_improvement_established': False, 'B00_all_alternatives_preserved': True, '2024_open': True,
              'next': 'Preregister an isolated held-group comparison using saved C0 and frozen residual factors before any calibration or score. Do not repeat source fits or treat output QA as predictive admission.'}
    dump(OUT / 'report.json', report)
    print(json.dumps({'status': report['status'], 'new_fits': 36, 'new_C0_fits': 0, 'new_scores': 0, 'new_submissions': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(); p.add_argument('mode', choices=['register', 'run']); args = p.parse_args()
    register() if args.mode == 'register' else run()
