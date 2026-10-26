"""Una vista fuente con ausencias adicionales, sin ampliar árboles ni cambiar etiquetas."""
from datetime import datetime, timezone
import argparse
import gc
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
ORIGINAL = HOME/'source_models'; OUT = BASE/'P25_fuente_ausencias_20261026'
PLAN = R/'registro/semana2_fuente_ausencias_privada_plan.json'
INDEX = R/'registro/semana2_fuente_ausencias_privada_actual.json'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.special import logsumexp
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits
spec = importlib.util.spec_from_file_location('p25_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
LINES = ['motor', 'buildings', 'contents']; SEEDS = [11, 12, 13]
COMMON = {'household_size': 'customer_id', 'years_at_address': 'customer_id',
    'flood_zone': 'address_id', 'distance_to_river_km': 'address_id'}
FIELDS = {'motor': {**COMMON, 'vehicle_age': 'policy_id', 'engine_size_cc': 'policy_id'},
    'buildings': {**COMMON, 'days_unoccupied': 'policy_id'},
    'contents': {**COMMON, 'high_value_items': 'policy_id'}}
KEYS = ['row_id', 'customer_id', 'address_id', 'policy_id']
PROBABILITY = .1; STRESS_SEED = 2026102665


def utc(): return datetime.now(timezone.utc).isoformat()


def digest(values):
    return hashlib.sha256('\n'.join(sorted(map(str, values))).encode('utf8')).hexdigest()


def split_receipt(rows, partition):
    assert rows.row_id.is_unique and np.array_equal(partition.row_id, rows.row_id)
    held = partition.internal_validation.to_numpy(bool)
    assert held.any() and (~held).any()
    for field in ['source_group', 'customer_canonical', 'address_id']:
        assert set(partition.loc[held, field]).isdisjoint(set(partition.loc[~held, field]))
    assert partition.groupby('source_group').internal_validation.nunique().max() == 1
    return {'train_rows': int((~held).sum()), 'held_rows': int(held.sum()),
        'train_row_digest': digest(rows.loc[~held, 'row_id']),
        'held_row_digest': digest(rows.loc[held, 'row_id']),
        'train_group_digest': digest(partition.loc[~held, 'source_group'].unique()),
        'held_group_digest': digest(partition.loc[held, 'source_group'].unique()),
        'group_customer_address_disjoint': True}


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def progress(path, value):
    tmp = path.with_name(path.name+'.p25.tmp')
    with tmp.open('x', encoding='utf8') as handle: json.dump(value, handle)
    os.replace(tmp, path)


def mask_source(x, metadata, line, seed):
    assert list(metadata) == KEYS and len(metadata) == len(x) and metadata.row_id.is_unique
    out = x.copy(deep=True); receipt = {}
    for variable, entity in FIELDS[line].items():
        assert pd.api.types.is_numeric_dtype(x[variable])
        key = metadata[entity].astype(str)
        if entity == 'customer_id': key = key.str.zfill(8)
        salt = variable+'|'+(line+'|' if entity == 'policy_id' else '')
        hashed = pd.util.hash_pandas_object(salt+key, index=False, hash_key=f'{seed:016d}').to_numpy(np.uint64)
        selected = ((hashed >> np.uint64(11)).astype(float)/2**53 < PROBABILITY)
        selected &= x[variable].notna().to_numpy()
        out.loc[selected, variable] = np.nan
        assert out.loc[x[variable].isna(), variable].isna().all()
        receipt[variable] = {'entity': entity, 'probability_on_observed': PROBABILITY,
            'native_missing': int(x[variable].isna().sum()), 'additional_missing': int(selected.sum()),
            'masked_missing': int(out[variable].isna().sum()),
            'mask_sha256': __import__('hashlib').sha256(np.packbits(selected).tobytes()).hexdigest()}
    assert out.drop(columns=list(FIELDS[line])).equals(x.drop(columns=list(FIELDS[line])))
    return out, receipt


def input_paths():
    paths = [Path(__file__), HOME/'report.json', HOME/'partition_source/report.json', ORIGINAL/'report.json',
        R/'registro/semana2_GLM_ausentes_fuente_plan.json', R/'registro/semana2_robustez2023_ciclo26_plan.json',
        R/'privado/semana2/robustez2023/ciclo26_20261025_v1/report.json',
        R/'privado/semana2/robustez2023/ciclo26_20261025_v1/source_veto.json']
    for line in LINES:
        paths += [HOME/f'matrix_s1_{line}.parquet', HOME/f'rows_s1_{line}.parquet',
            HOME/f'matrix_s2_{line}.parquet', HOME/f'rows_s2_{line}.parquet',
            HOME/f'partition_source/folds_{line}.parquet']
        for seed in SEEDS:
            paths += [ORIGINAL/f'{line}_seed{seed}_{kind}/fit_record.json' for kind in ['inner', 'full']]
            paths.append(ORIGINAL/f'{line}_seed{seed}_inner/model.txt')
    return paths


def check_sources():
    assert w.read(PLAN)['sources'] == {w.rel(p): w.sha(p) for p in input_paths()}


def synthetic():
    n = 160; keys = pd.DataFrame({'row_id': ['toy'+str(i) for i in range(n)],
        'customer_id': [str(i//2) for i in range(n)], 'address_id': ['a'+str(i//4) for i in range(n)],
        'policy_id': ['p'+str(i//2) for i in range(n)]})
    x = pd.DataFrame({c: np.arange(n, dtype=float) for c in sorted(set().union(*[set(x) for x in FIELDS.values()]))})
    x['protected_exposure'] = .5
    for c in x.columns[:-1]: x.loc[np.arange(n) % 19 == 0, c] = np.nan
    receipts = []
    for line in LINES:
        a, _ = mask_source(x, keys, line, 11)
        b, _ = mask_source(x.iloc[::-1], keys.iloc[::-1], line, 11)
        pd.testing.assert_frame_equal(a, b.iloc[::-1], check_exact=True)
        again, _ = mask_source(x, keys, line, 11); pd.testing.assert_frame_equal(a, again)
        assert np.array_equal(a.protected_exposure, x.protected_exposure)
        for variable, entity in FIELDS[line].items():
            selected = a[variable].isna() & x[variable].notna()
            available = x[variable].notna()
            counts = pd.DataFrame({'key': keys[entity].astype(str), 'mask': selected, 'available': available})
            assert counts.loc[counts.available].groupby('key')['mask'].nunique().max() == 1
        receipts.append({'line': line, 'stable_entity_and_row_reversal_exact': True,
            'original_missing_preserved_and_other_columns_unchanged': True})
    return {'checks': receipts, 'financial_fields_not_mask_arguments': True, 'model_fits': 0}


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert not w.read(R/'registro/semana2_mision017_fase2_actual.json').get('active_jobs')
    OUT.mkdir(); fixture = synthetic(); dump(OUT/'synthetic_mask.json', fixture)
    preflight = {}; global_groups = []
    for line in LINES:
        part = pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet')
        rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['row_id'])
        matrix = pd.read_parquet(HOME/f'matrix_s1_{line}.parquet', columns=list(FIELDS[line]))
        assert len(matrix) == len(rows)
        assert all(pd.api.types.is_numeric_dtype(matrix[c]) and matrix[c].isna().any() for c in FIELDS[line])
        preflight[line] = {'split': split_receipt(rows, part),
            'source_rows': len(rows), 'native_missing': {c: int(matrix[c].isna().sum()) for c in FIELDS[line]}}
        global_groups.append(part[['source_group', 'internal_validation']])
    assert pd.concat(global_groups).groupby('source_group').internal_validation.nunique().max() == 1
    dump(OUT/'input_preflight.json', {'utc': utc(), 'by_line': preflight, 'cross_line_group_assignment_exact': True})
    rounds = {}; parameters = {}; offsets = {}
    for line in LINES:
        for seed in SEEDS:
            full = w.read(ORIGINAL/f'{line}_seed{seed}_full/fit_record.json')
            inner = w.read(ORIGINAL/f'{line}_seed{seed}_inner/fit_record.json')
            assert full['current_iteration'] == inner['best_iteration'] > 0
            assert full['parameters'] == inner['parameters']
            assert inner['model_sha256'] == w.sha(ORIGINAL/f'{line}_seed{seed}_inner/model.txt')
            key = f'{line}_seed{seed}'; rounds[key] = full['current_iteration']
            parameters[key] = full['parameters']; offsets[key] = {'inner': inner['initial_base'], 'full': full['initial_base']}
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'A1S_native_trees_with_fixed_entity_missingness_augmentation',
        'hypothesis': 'La mayor ausencia de covariables en destino puede hacer frágiles ramas de valores faltantes aprendidas con menos ausencias. Una vista fuente con pérdidas de información independientes de etiquetas puede robustecerlas, sin añadir variables o capacidad.',
        'prior_adverse': 'Ciclo26: seis pares en fuente2023, GLM y corrección200árboles pequeños. GLMpasó fuente pero no destino; árboles fallaron motor. No se repite ese contrato ni se supone MCAR. P14/P15indicadores lineales tampoco establecieron mejora.',
        'why_distinct': 'Actual fuente2021-2024/eCost,16pares de variables nativas faltantes y3semillas de31hojas. Se fijan parámetros y rondas ya elegidas por A1Soriginal. La intervención es información disponible al entrenar, no capacidad o búsqueda de hiperparámetros.',
        'mask': {'probability_on_observed': PROBABILITY, 'fields': FIELDS,
            'training_mask_seeds': SEEDS, 'shared_stress_seed': STRESS_SEED,
            'key': 'Pandas hash_pandas_object with16digit seed hash_key; field+normalized entity; policy also salted by line.',
            'customer_normalization': 'Source customer IDzfill8consistent with ID01/D32; only mask keys, no source file changes.',
            'protected': 'Labels, costs, eCost/exposure, dates, histories, rows and categorical variables unchanged.'},
        'source_partitions': 'Exact stored A1Sinternal_validationglobal customer/address group partition; source held responses never in lgb.train arguments.',
        'source_views': 'Same held groups/labels/exposure in native and one fixed masked view shared by all seeds. Each ensemble uses all3seeds geometrically, no selection. Views/seeds are not independent support.',
        'source_veto': {'max_relative_deviance_increase': .002,
            'rule': 'Each line and each of the2held-source views must have ensemble mean Tweedie deviance <=1.002times original saved inner ensemble. No line salvage.',
            'limitation': 'One source grouped holdout already used for original early stopping, conditional on frozen whole-source observation link; not the old5block veto or independent validation.'},
        'rounds': rounds, 'parameters': parameters, 'reused_initial_bases': offsets,
        'source_years': [2021, 2022, 2023, 2024],
        'budget': {'initial_fixed_round_inner_fits': 9, 'full_refits_only_after_all_source_gates': 9,
            'max_source_fits': 18, 'new_C0_fits': 0, 'new_target_calibrations': 0, 'new_target_scores': 0,
            'future2025inference': 0, 'new_final_prices': 0, 'new_submissions': 0},
        'criteria': ['SHA/keys unchanged and all actual fit attempts reconciled, save models before downstream checks.',
            'Mask stable under row reversal and entity repeats, label-independent by construction.',
            'Source deviance manual/sklearn agreement, old native loss agrees with its original source validation.',
            'No held-source fit rows and same offsets/iterations/model capacity.',
            'Save/load/order and independent leaf sums for new models; source weighted relative mean one.',
            'No full refits if any source veto fails; no target admission inferred from passing source.'],
        'normalization': 'Full refits centered on predictions of original unmasked source matrix weighted by original exposure_model, same as A1S; no learned target normalization in source stage.',
        'consumer': 'If source passes, later separately preregister full current50/50S2/H1comparison, keeping all global and new-business/cohort guards. No public tuning.',
        'sources': {w.rel(p): w.sha(p) for p in input_paths()},
        'preflight': {'synthetic': w.rel(OUT/'synthetic_mask.json'), 'synthetic_sha256': w.sha(OUT/'synthetic_mask.json'),
            'inputs': w.rel(OUT/'input_preflight.json'), 'inputs_sha256': w.sha(OUT/'input_preflight.json')},
        'limits': ['MCAR and label-preservation of artificial missingness are hypotheses, not proven data-generation facts.',
            'Entity-consistent masks simplify time-varying capture quality; private support is not certified.',
            'Source2024and common marks remain retrospective;2024target already adaptive.',
            'No private result, no source model promotion and no professional independent validation.'],
        'B00_all_alternatives_preserved': True, '2024_open': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text(
        'Codex. P25fuente preinscrita: mismos árboles nativos A1S, parámetros y rondas originales, '
        'solo10%adicional de ausencia en16pares numéricos que ya tienen faltantes. Máscaras '
        'independientes de etiquetas y coherentes por cliente/dirección/póliza; sin tocar '
        'costes, exposición, fechas, historia o eliminar filas. No es la primera prueba de '
        'esta idea: ciclo26y P14/P15adversos conservados; aquí cambian familia/contrato fuente '
        'a los actuales cuatro años y eCost. Primero9ajustes internos a rondas fijas, '
        'comparados con los9originales guardados en las mismas vistas nativa y enmascarada '
        'de grupos retenidos. Todas las semillas se usan en cada ensemble; ninguna equivale '
        'a un holdout independiente. Veto por ramo/vista: desviación media no mayor de1,002 '
        'veces la original. Si falla alguno, cero refits completos y cero evaluación destino. '
        'Solo si todos pasan,9refits fuente más y componentes históricos2023/2024. Máximo18 '
        'ajustes, ceroC0, calibración/score destino, inferencias2025, precios finales o envíos. '
        'El único holdout fuente ya se usó para elegir las rondas originales y su enlace '
        'es condicional, por lo que no es validación independiente. No se demuestra MCAR. '
        'Máscara sintética sin ajustes pasó claves/coherencia/orden y campos protegidos. '
        'B00/F3c/alternativas conservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P25-AUSENCIAS-PREVIO',
        '--asunto', 'P25: una vista de ausencias con capacidad fija y veto fuente antes de refits',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    dump(INDEX, {'author': 'Codex', 'utc': utc(), 'status': 'P25source_registered_no_fit',
        'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(posted.stdout)})
    print(json.dumps({'registered': True, 'max_fits': 18, 'forum': w.read(INDEX)['forum']}))


def state(status, execution):
    stamp = datetime.now(timezone.utc); archive = R/'privado'/('p25_state_'+stamp.strftime('%H%M%S%f')); archive.mkdir()
    attempts = sorted(p.parent.name for p in OUT.glob('*/fit_invoked.json'))
    completed = sorted(p.parent.name for p in OUT.glob('*/fit_record.json'))
    counter_path = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(counter_path)
    counted = counters.get('phase2_private_P25_source_masks', {}).get('counted_fit_keys', [])
    assert set(counted).issubset(attempts); added = len(set(attempts)-set(counted))
    phase_path = R/'registro/semana2_mision017_fase2_actual.json'; phase = w.read(phase_path)
    current = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': status, 'attempts': len(attempts),
        'completed': len(completed), 'execution': execution, 'output': w.rel(OUT),
        'plan': w.rel(PLAN), 'new_C0_fits': 0, 'new_target_scores': 0, 'new_submissions': 0}
    w.update(counter_path, {'as_of_utc': stamp.isoformat(),
        'cumulative_price_base_fits': counters['cumulative_price_base_fits']+added,
        'phase2_private_P25_source_masks': {'counted_fit_keys': attempts, 'attempts': len(attempts),
            'completed': len(completed), 'new_C0_fits': 0, 'plan': w.rel(PLAN)}}, archive)
    w.update(INDEX, current, archive)
    jobs = [] if execution is None else [execution]
    w.update(phase_path, {'private_P25_source': current, 'new_price_fits': phase['new_price_fits']+added,
        'active_execution': execution, 'active_jobs': jobs}, archive)
    path = ROOT/'Preparación/ESTADO_PROYECTO.json'; whole = w.read(path); own = whole['week_2_mission017_phase2_20261025']
    own.update(private_P25_source=current, new_price_fits=phase['new_price_fits']+added, active_jobs=jobs)
    w.update(path, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': execution}, archive)


def fit(folder, x, y, e_cost, initial, params, rounds, selected, rows, partition):
    assert not (folder/'fit_invoked.json').exists()
    data = lgb.Dataset(x.loc[selected], label=y[selected], init_score=np.log(e_cost[selected])+initial)
    dump(folder/'fit_invoked.json', {'author': 'Codex', 'utc': utc(), 'pid': os.getpid(),
        'rows': int(selected.sum()), 'rounds': rounds, 'source_only': True, 'plan_sha256': w.sha(PLAN),
        'fit_row_digest': digest(rows.loc[selected, 'row_id']),
        'fit_group_digest': digest(partition.loc[selected, 'source_group'].unique()),
        'full_fit_after_source_veto': bool(selected.all())})
    execution = {'author': 'Codex', 'pid': os.getpid(), 'script': w.rel(Path(__file__)), 'kind': 'P25source_missingness', 'checkpoint': folder.name}
    state('P25source_training_running', execution); start = time.monotonic()
    def callback(env):
        if (env.iteration+1) % 100 == 0:
            progress(folder/'progress.json', {'utc': utc(), 'iteration': env.iteration+1, 'seconds': time.monotonic()-start})
    try:
        model = lgb.train(params, data, num_boost_round=rounds, callbacks=[callback])
        model.save_model(str(folder/'model.txt'))
        dump(folder/'fit_record.json', {'author': 'Codex', 'utc': utc(), 'parameters': params,
            'current_iteration': model.current_iteration(), 'initial_base': initial,
            'source_rows': int(selected.sum()), 'model_sha256': w.sha(folder/'model.txt'),
            'seconds': time.monotonic()-start, 'plan_sha256': w.sha(PLAN), 'lightgbm_version': lgb.__version__})
        assert model.current_iteration() == rounds
        state('P25source_fit_saved', execution)
        print(json.dumps({'completed': folder.name, 'rounds': rounds, 'seconds': round(time.monotonic()-start, 1)}), flush=True)
        return model
    except BaseException as exc:
        dump(folder/'failure.json', {'utc': utc(), 'exception': type(exc).__name__, 'message': str(exc)})
        raise


def leaf_sum(model, x):
    leaves = model.predict(x, pred_leaf=True, num_threads=2); total = np.zeros(len(x))
    for j, tree in enumerate(model.dump_model()['tree_info']):
        table = {}
        def visit(node):
            if 'leaf_index' in node: table[node['leaf_index']] = node['leaf_value']
            else: visit(node['left_child']); visit(node['right_child'])
        visit(tree['tree_structure']); total += np.array([table[int(v)] for v in leaves[:, j]])
    return total


def report_source_veto():
    result = []
    for line in LINES:
        rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['row_id', 'T0'])
        p = pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet')
        held = p.internal_validation.to_numpy(bool); y = rows.T0.to_numpy(float)[held]
        frames = [pd.read_parquet(OUT/f'{line}_seed{seed}_inner/validation_predictions.parquet') for seed in SEEDS]
        assert all(np.array_equal(f.row_id, rows.loc[held, 'row_id']) for f in frames)
        for view in ['native', 'masked']:
            old = np.exp(np.mean([f['old_'+view].to_numpy() for f in frames], axis=0))
            new = np.exp(np.mean([f['new_'+view].to_numpy() for f in frames], axis=0))
            a = float(mean_tweedie_deviance(y, old, power=1.5)); b = float(mean_tweedie_deviance(y, new, power=1.5))
            result.append({'line': line, 'view': view, 'rows': len(y), 'baseline_mean_deviance': a,
                'candidate_mean_deviance': b, 'relative_loss': b/a-1, 'pass': b <= 1.002*a})
    report = {'author': 'Codex', 'utc': utc(), 'results': result, 'all_pass': all(x['pass'] for x in result),
        'one_conditional_grouped_holdout_not_independent_seeds_or_views': True}
    dump(OUT/'source_veto.json', report); return report


def run(resume=False):
    assert not (OUT/'report.json').exists(); check_sources(); plan = w.read(PLAN)
    if resume:
        import psutil
        started = w.read(OUT/'started.json')
        if psutil.pid_exists(started['pid']):
            process = psutil.Process(started['pid'])
            assert not any(Path(arg).name == Path(__file__).name for arg in process.cmdline())
        assert all((p.parent/'fit_record.json').exists() for p in OUT.glob('*/fit_invoked.json'))
        dump(OUT/('resume_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'), {'utc': utc(), 'pid': os.getpid()})
    else:
        assert not (OUT/'started.json').exists()
        dump(OUT/'started.json', {'utc': utc(), 'pid': os.getpid(), 'plan_sha256': w.sha(PLAN)})
    start = time.monotonic(); checkpointed = False
    try:
        for full in [False, True]:
            if full:
                veto = w.read(OUT/'source_veto.json')
                if not veto['all_pass']: break
            for line in LINES:
                x = pd.read_parquet(HOME/f'matrix_s1_{line}.parquet')
                rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=KEYS+['year', 'T0', 'e_cost', 'exposure_model'])
                partition = pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet')
                assert np.array_equal(partition.row_id, rows.row_id) and len(x) == len(rows)
                assert split_receipt(rows, partition) == w.read(OUT/'input_preflight.json')['by_line'][line]['split']
                held = partition.internal_validation.to_numpy(bool)
                y = rows.T0.to_numpy(float); e_cost = rows.e_cost.to_numpy(float)
                assert rows.year.isin([2021, 2022, 2023, 2024]).all() and np.isfinite(y).all() and (y >= 0).all()
                assert np.isfinite(e_cost).all() and (e_cost > 0).all()
                metadata = rows[KEYS]
                stress, stress_record = mask_source(x.loc[held], metadata.loc[held], line, STRESS_SEED)
                stress_path = OUT/f'stress_mask_{line}.json'
                if not stress_path.exists(): dump(stress_path, stress_record)
                for seed in SEEDS:
                    kind = 'full' if full else 'inner'; key = f'{line}_seed{seed}'; folder = OUT/f'{key}_{kind}'
                    folder.mkdir(exist_ok=True)
                    augmented, mask_record = mask_source(x, metadata, line, seed)
                    if not (folder/'mask.json').exists(): dump(folder/'mask.json', mask_record)
                    selected = np.ones(len(rows), dtype=bool) if full else ~held
                    initial = plan['reused_initial_bases'][key][kind]
                    assert math.isclose(initial, float(np.log(y[selected].sum()/e_cost[selected].sum())), rel_tol=0, abs_tol=1e-14)
                    if not (folder/'fit_record.json').exists():
                        model = fit(folder, augmented, y, e_cost, initial, plan['parameters'][key], plan['rounds'][key], selected, rows, partition)
                    else:
                        record = w.read(folder/'fit_record.json'); assert record['model_sha256'] == w.sha(folder/'model.txt')
                        model = lgb.Booster(model_file=str(folder/'model.txt'))
                    if not full and not (folder/'validation.json').exists():
                        baseline_record = w.read(ORIGINAL/f'{key}_inner/fit_record.json')
                        baseline = lgb.Booster(model_file=str(ORIGINAL/f'{key}_inner/model.txt'))
                        held_x = x.loc[held]; sample = np.unique(np.linspace(0, len(held_x)-1, 32, dtype=int))
                        loaded = lgb.Booster(model_file=str(folder/'model.txt'))
                        raw_sample = model.predict(held_x.iloc[sample], raw_score=True, num_threads=2)
                        assert np.array_equal(raw_sample, loaded.predict(held_x.iloc[sample], raw_score=True, num_threads=2))
                        assert np.array_equal(raw_sample[::-1], loaded.predict(held_x.iloc[sample[::-1]], raw_score=True, num_threads=2))
                        leaf_error = float(np.max(np.abs(leaf_sum(loaded, held_x.iloc[sample[:6]])-raw_sample[:6])))
                        assert leaf_error < 1e-10
                        saved = pd.DataFrame({'row_id': rows.loc[held, 'row_id'].to_numpy()}); losses = {}
                        for view, frame in [('native', x.loc[held]), ('masked', stress)]:
                            raw_new = model.predict(frame, raw_score=True, num_threads=2)
                            raw_old = baseline.predict(frame, raw_score=True, num_threads=2)
                            saved['new_'+view] = raw_new+np.log(e_cost[held])+initial
                            saved['old_'+view] = raw_old+np.log(e_cost[held])+baseline_record['initial_base']
                            mu = np.exp(saved['new_'+view].to_numpy()); yy = y[held]
                            manual = float(np.mean(2*yy/np.sqrt(mu)+2*np.sqrt(mu)))
                            independent = float(.5*mean_tweedie_deviance(yy, mu, power=1.5)+4*np.mean(np.sqrt(yy)))
                            assert math.isclose(manual, independent, rel_tol=2e-13)
                            losses[view] = manual
                            if view == 'native':
                                old_mu = np.exp(saved.old_native.to_numpy())
                                old_loss = float(np.mean(2*yy/np.sqrt(old_mu)+2*np.sqrt(old_mu)))
                                assert abs(old_loss/baseline_record['best_score']['source_internal']['tweedie']-1) < 2e-6
                        saved.to_parquet(folder/'validation_predictions.parquet', index=False)
                        dump(folder/'validation.json', {'utc': utc(), 'losses': losses,
                            'manual_sklearn_cost_deviance_exact': True, 'old_native_metric_reconciled': True,
                            'held_rows_excluded_from_fit': True, 'views_not_independent': True,
                            'save_load_order_exact': True, 'independent_leaf_error': leaf_error})
                    if full and not (folder/'application.json').exists():
                        target_rows = pd.read_parquet(HOME/f'rows_s2_{line}.parquet', columns=['row_id', 'year', 'is_test'])
                        target_x = pd.read_parquet(HOME/f'matrix_s2_{line}.parquet')
                        keep = ~target_rows.is_test; target_rows = target_rows.loc[keep].reset_index(drop=True)
                        target_x = target_x.loc[keep].reset_index(drop=True)
                        assert target_rows.year.isin([2023, 2024]).all() and list(x) == list(target_x)
                        raw = model.predict(x, raw_score=True, num_threads=2); weights = rows.exposure_model.to_numpy(float)
                        center = float(logsumexp(raw, b=weights)-np.log(weights.sum()))
                        independent = math.log(math.fsum((np.exp(raw)*weights).tolist())/math.fsum(weights.tolist()))
                        assert abs(center-independent) < 1e-12
                        assert abs(np.average(np.exp(raw-center), weights=weights)-1) < 2e-12
                        target_raw = model.predict(target_x, raw_score=True, num_threads=2)
                        loaded = lgb.Booster(model_file=str(folder/'model.txt')); sample = np.unique(np.linspace(0, len(target_x)-1, 32, dtype=int))
                        assert np.array_equal(target_raw[sample], loaded.predict(target_x.iloc[sample], raw_score=True, num_threads=2))
                        assert np.array_equal(target_raw[sample[::-1]], loaded.predict(target_x.iloc[sample[::-1]], raw_score=True, num_threads=2))
                        leaf_error = float(np.max(np.abs(leaf_sum(loaded, target_x.iloc[sample[:6]])-target_raw[sample[:6]])))
                        assert leaf_error < 1e-10
                        target_rows['raw_log_rate'] = target_raw+initial
                        target_rows['log_relative_A1S'] = target_raw-center
                        assert np.isfinite(target_rows[['raw_log_rate', 'log_relative_A1S']]).all().all()
                        target_rows.to_parquet(folder/'historical_components.parquet', index=False)
                        dump(folder/'application.json', {'utc': utc(), 'source_center': center,
                            'source_rows': len(rows), 'historical_target_rows': len(target_rows),
                            'future2025inference': 0, 'save_load_order_exact': True,
                            'independent_leaf_error': leaf_error, 'components_sha256': w.sha(folder/'historical_components.parquet')})
                        del target_x, target_rows
                    del model, augmented; gc.collect()
                    if time.monotonic()-start > 45*60:
                        checkpointed = True
                        state('P25checkpoint_between_completed_fits', None); print(json.dumps({'checkpoint': folder.name}), flush=True); return
                del x, rows, partition, stress; gc.collect()
            if not full and not (OUT/'source_veto.json').exists(): report_source_veto()
        veto = w.read(OUT/'source_veto.json'); outputs = {}
        if veto['all_pass']:
            for line in LINES:
                fs = [pd.read_parquet(OUT/f'{line}_seed{seed}_full/historical_components.parquet') for seed in SEEDS]
                assert all(np.array_equal(f.row_id, fs[0].row_id) for f in fs)
                result = fs[0][['row_id', 'year', 'is_test']].copy()
                for name in ['raw_log_rate', 'log_relative_A1S']: result[name] = np.mean([f[name].to_numpy() for f in fs], axis=0)
                path = OUT/f'historical_{line}_three_seed.parquet'; result.to_parquet(path, index=False)
                outputs[w.rel(path)] = w.sha(path)
        check_sources(); attempted = len(list(OUT.glob('*/fit_invoked.json')))
        assert attempted == (18 if veto['all_pass'] else 9)
        report = {'author': 'Codex', 'utc': utc(), 'status': 'P25source_complete_not_admitted' if veto['all_pass'] else 'P25source_veto_failed_no_full_refit',
            'new_source_fits': attempted, 'inner_fixed_round_fits': 9, 'full_refits': 9 if veto['all_pass'] else 0,
            'source_veto_all_pass': veto['all_pass'], 'source_veto': veto['results'],
            'new_C0_fits': 0, 'new_target_calibrations': 0, 'new_target_scores': 0,
            'new_future2025inference': 0, 'new_final_prices': 0, 'new_submissions': 0,
            'outputs': outputs, 'plan_sha256': w.sha(PLAN), 'private_improvement_established': False,
            'goal_achieved': False, '2024_open': True, 'B00_all_alternatives_preserved': True,
            'limits': plan['limits']}
        dump(OUT/'report.json', report); state(report['status'], None)
        print(json.dumps({'status': report['status'], 'new_source_fits': attempted, 'source_veto': veto['results']}), flush=True)
    finally:
        if not (OUT/'report.json').exists() and not checkpointed: state('P25unfinished_reconcile_attempts_before_resume', None)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['prepare', 'run', 'resume']); args = p.parse_args()
    with threadpool_limits(limits=2):
        if args.mode == 'prepare': prepare()
        else: run(resume=args.mode == 'resume')
