"""Lector por predicado2023 y entrenamiento único de la enmienda B20 v2."""
from pathlib import Path
from itertools import combinations
from datetime import datetime, timezone
import hashlib
import json
import sys
import time

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
RUN = REPO / 'privado/semana2/desarrollo2023/b20_contraste_exploratorio_20261024_v2'
sys.path.insert(0, str(REPO / 'src'))
from semana2 import contraste_b20_exploratorio as core
np, pd, pq = core.np, core.pd, core.base.u.pq
KEY = core.KEY
read = core.base.u.read
dump = core.base.u.dump
sha = core.base.u.sha
require = core.require


def write_frame(frame, path):
    # Evita el registro de tipos de extensión del motor pandas3. Los tipos de
    # Arrow se obtienen del DataFrame sin cambiar valores o parámetros.
    pq.write_table(core.base.u.pa.Table.from_pandas(frame, preserve_index=False), path)


def event(name, **kw):
    item = {'utc': datetime.now(timezone.utc).isoformat(), 'event': name, **kw}
    with (RUN / 'events.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(item) + '\n')
    print(json.dumps(item), flush=True)


def verify_sources(plan, include_counter=True):
    for item in plan['frozen_sources']:
        if not include_counter and item['path'].endswith('semana2_contadores_propios_actual.json'):
            continue
        require(sha(ROOT / item['path']) == item['sha256'], 'Fuente modificada: ' + item['path'])


def freeze_implementation():
    plan = read(RUN / 'plan_preregistered.json')
    require(read(RUN / 'synthetic_preflight.json')['success'], 'Falta preflight sintético completo.')
    verify_sources(plan)
    files = ['src/semana2/contraste_b20_exploratorio.py', 'src/semana2/c0_estricto2023.py',
        'src/semana2/ambitos_c0_b20_2023.py', 'src/semana2/entrenar_glm_ridge_coberturas2023.py',
        'src/semana2/entrenar_desarrollo2023_v8.py', 'src/semana2/entrenar_desarrollo2023.py',
        'herramientas/ejecutar_contraste_b20_exploratorio.py',
        'herramientas/probar_contraste_b20_exploratorio.py',
        'herramientas/evaluar_contraste_b20_exploratorio.py']
    plan['implementation_sources'] = []
    for name in files:
        path = REPO / name
        snapshot = RUN / 'sources' / path.name
        snapshot.write_bytes(path.read_bytes())
        plan['implementation_sources'].append({'path': path.relative_to(ROOT).as_posix(),
            'sha256': sha(path), 'snapshot': snapshot.relative_to(ROOT).as_posix()})
    plan['implementation_frozen'] = True
    plan['implementation_frozen_utc'] = datetime.now(timezone.utc).isoformat()
    plan['repairs_before_fit'] = ['Direct Arrow serialization replaces pandas engine after preserved pre-training write failure; recipe and acceptance unchanged.']
    plan['preregistered_plan_sha256'] = sha(RUN / 'plan_preregistered.json')
    dump(RUN / 'plan_execution.json', plan)
    event('implementation_frozen', files=len(files))


def checked_read(path, plan, columns, *, filters):
    path = Path(path).resolve()
    allowed = {str((ROOT / x['path']).resolve()): x['sha256'] for x in plan['frozen_sources']}
    require(str(path) in allowed and sha(path) == allowed[str(path)], 'Lector fuera de fuentes congeladas.')
    # Siempre un predicado antes de materializar, incluidas fuentes ya2023.
    result = pq.read_table(path, columns=columns, filters=filters).to_pandas()
    if 'year' in result:
        require(result.year.eq(2023).all(), 'Año ajeno materializado.')
    predicate = '; '.join(str(name) + ' ' + op + ' ' +
        (str(len(value)) + ' declared IDs' if op == 'in' else str(value)) for name, op, value in filters)
    event('scoped_read', source=path.relative_to(ROOT).as_posix(), rows=len(result),
          columns=columns, predicate=predicate)
    return result


def prepare():
    require(not (RUN / 'prepared_manifest.json').exists(), 'Entradas ya preparadas; no repetir.')
    plan = read(RUN / 'plan_execution.json')
    verify_sources(plan)
    folder = RUN / 'inputs_2023'
    folder.mkdir(exist_ok=False)
    block = plan['recipe']['features_by_line']['buildings']['all']
    columns = list(dict.fromkeys([*core.c0.META, 'period_start', 'period_end', 'exposure',
                                 'T0', 'e_cost_mix_1.0', 'x_customer_tenure_years', *block]))
    frames = {}
    for k, source in plan['inputs']['feature_frames'].items():
        frame = checked_read(source, plan, columns, filters=[('year', '=', 2023), ('is_test', '=', False)])
        core.c0._metadata(frame)
        require(frame.line.eq('buildings').all(), 'Ramo ajeno en base edificios.')
        write_frame(frame, folder / f'buildings_outer{k}.parquet')
        frames[int(k)] = frame
    main = frames[0]
    ordered = main.sort_values(KEY).reset_index(drop=True)
    for frame in frames.values():
        candidate = frame.sort_values(KEY).reset_index(drop=True)
        shared = [c for c in columns if c != 'e_cost_mix_1.0']
        require(ordered[shared].equals(candidate[shared]), 'Datos base distintos entre vistas exteriores.')
    metadata = [main[KEY + ['x_customer_tenure_years']]]
    for line, source in plan['inputs']['other_line_frames'].items():
        frame = checked_read(source, plan, KEY + ['year', 'x_customer_tenure_years'], filters=[('year', '=', 2023)])
        require(frame.line.eq(line).all(), 'Ramo de metadatos incompatible.')
        metadata.append(frame[KEY + ['x_customer_tenure_years']])
    write_frame(pd.concat(metadata, ignore_index=True), folder / 'customer_metadata.parquet')
    raw = checked_read(plan['inputs']['raw_oof'], plan, None, filters=[('year', '=', 2023)])
    require(len(raw) == 50094 and raw.model_id.eq('W2-B20').all() and not raw.duplicated(KEY).any(), 'Ancla B20 incompleta.')
    write_frame(raw, folder / 'raw_B20.parquet')
    bands = checked_read(plan['inputs']['original_bands'], plan, KEY + ['year', 'band'],
                         filters=[('year', '=', 2023), ('line', '=', 'buildings')])
    require(len(bands) == len(main) and not bands.duplicated(KEY).any(), 'Bandas originales incompletas.')
    write_frame(bands, folder / 'bands.parquet')
    memberships = []
    for source in plan['inputs']['claim_metadata'].values():
        memberships.append(checked_read(source, plan, [*KEY, 'claim_id', 'year', 'fold'],
                         filters=[('year', '=', 2023), ('line', '=', 'buildings')]))
    memberships = pd.concat(memberships, ignore_index=True)
    require(memberships.groupby(['market', 'line', 'claim_id']).row_id.nunique().max() == 1
            and memberships.groupby(['market', 'line', 'claim_id']).fold.nunique().max() == 1,
            'Notificación con pertenencia contradictoria.')
    memberships = memberships.drop_duplicates().reset_index(drop=True)
    ids = sorted(memberships.claim_id.unique().tolist())
    columns = [*KEY, 'claim_id', 'peril', 'loss_date', 'report_date', 'T0_cents', 'included_in_T0']
    predicate = [('market', '=', 'emerging'), ('line', '=', 'buildings'), ('included_in_T0', '=', True),
        ('claim_id', 'in', ids), ('loss_date', '>=', pd.Timestamp('2023-01-01')),
        ('loss_date', '<', pd.Timestamp('2024-01-01'))]
    # El origen contiene varios años. El predicado se aplica en Arrow antes de
    # devolver identidades/fechas/marcas; nunca se convierte la tabla completa.
    claims = checked_read(plan['inputs']['claim_audit'], plan, columns, filters=predicate)
    require(len(claims) == len(memberships), 'Notificaciones2023 faltantes o repetidas.')
    claims = claims.merge(memberships, on=KEY + ['claim_id'], validate='one_to_one')
    claims = claims.merge(main[KEY + ['fold', 'is_test']], on=KEY, validate='many_to_one', suffixes=('', '_period'))
    require(claims.fold.eq(claims.fold_period).all() and claims.year.eq(2023).all()
            and not claims.is_test.any(), 'Pertenencia temporal ajena en notificaciones.')
    claims = claims.drop(columns='fold_period')
    totals = claims.groupby(KEY, as_index=False).T0_cents.sum()
    check = main[KEY + ['T0']].merge(totals, on=KEY, how='left', validate='one_to_one').fillna({'T0_cents': 0})
    require(np.max(np.abs(check.T0 * 100 - check.T0_cents)) < 1e-6, 'T0 no concilia con notificaciones2023.')
    write_frame(claims, folder / 'claims.parquet')
    manifest = {'rows_buildings': len(main), 'accepted_claims': len(claims), 'all_years': [2023],
        'mixed_year_source_reader': 'Arrow predicate before materialization; labels only matched2023 keys',
        'files': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)} for p in sorted(folder.glob('*.parquet'))]}
    dump(RUN / 'prepared_manifest.json', manifest)
    event('inputs_prepared', buildings=len(main), accepted_claims=len(claims))


def train():
    plan = read(RUN / 'plan_execution.json')
    verify_sources(plan)
    for item in plan['implementation_sources'] + read(RUN / 'prepared_manifest.json')['files']:
        require(sha(ROOT / item['path']) == item['sha256'], 'Código/entrada preparado cambió.')
    forum = (ROOT / 'Hackaton/Semana 2/Foro/FORO.md').read_bytes()
    require(forum.count(('<!-- aporte:' + plan['forum_prior'] + ' -->').encode()) == 1, 'Falta foro anterior a ajuste.')
    marker = RUN / 'training_started.json'
    with marker.open('x', encoding='utf-8') as handle:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'plan_sha256': sha(RUN / 'plan_execution.json')}, handle)
    (RUN / 'forum_before_fit.md').write_bytes(forum)
    dump(RUN / 'environment.json', {'python': sys.version, 'numpy': np.__version__, 'pandas': pd.__version__,
                                    'sklearn': core.base.u.sklearn.__version__, 'threads': 2})
    folder = RUN / 'inputs_2023'
    frame = pq.read_table(folder / 'buildings_outer0.parquet').to_pandas()
    claims = pq.read_table(folder / 'claims.parquet').to_pandas()
    versions = {'prepared_periods': sha(folder / 'buildings_outer0.parquet'),
                'prepared_claims': sha(folder / 'claims.parquet'),
                'C0_source': sha(REPO / 'src/semana2/c0_estricto2023.py')}
    predictions, fitted = {}, []
    (RUN / 'inner').mkdir()
    for pair in combinations(range(5), 2):
        label = ''.join(map(str, pair))
        node_path = RUN / 'inner' / label
        node_path.mkdir()
        dump(node_path / 'fit_intent.json', {'excluded': list(pair), 'utc': datetime.now(timezone.utc).isoformat()})
        event('inner_fit_started', excluded=list(pair), fit_folds=[x for x in range(5) if x not in pair])
        node = core.fit_inner(frame, claims, pair, plan['recipe'], versions)
        core.joblib.dump(node['bundle'], node_path / 'bundle.joblib', compress=3)
        dump(node_path / 'C0.json', node['C0'])
        dump(node_path / 'receipt.json', node['receipt'])
        pred = core.predict_inner(node, frame.loc[frame.fold.isin(pair)], pair)
        write_frame(pred, node_path / 'heldout_predictions.parquet')
        predictions[pair] = pred
        fitted.append(node['receipt'])
        event('inner_fit_completed', excluded=list(pair), completed_GLMs=len(fitted))
    (RUN / 'calibration').mkdir()
    (RUN / 'outer').mkdir()
    raw = pq.read_table(folder / 'raw_B20.parquet').to_pandas()
    result = []
    for outer in range(5):
        event('calibration_started', outer=outer)
        params, calibration = core.calibration_for_outer(frame, predictions, outer, plan['calibration_numerics'])
        dump(RUN / 'calibration' / f'fold{outer}.json', params)
        write_frame(calibration, RUN / 'calibration' / f'fold{outer}_inner_oof.parquet')
        current = pq.read_table(folder / f'buildings_outer{outer}.parquet').to_pandas()
        valid = current.loc[current.fold.eq(outer)].copy()
        bundle = core.joblib.load(plan['inputs']['outer_models'][str(outer)])
        with core.base.u.threadpool_limits(limits=2):
            rate = core.base.predict(bundle, valid, 'buildings')
        replay = valid[KEY + ['T0', 'e_cost_mix_1.0']].copy()
        replay['replayed_rate'] = rate
        anchor = raw.loc[raw.line.eq('buildings') & raw.fold.eq(outer)].copy()
        anchor = anchor.merge(replay, on=KEY, validate='one_to_one', suffixes=('', '_source'))
        require(np.array_equal(anchor.annual_rate, anchor.replayed_rate)
                and np.array_equal(anchor.T0, anchor.T0_source)
                and np.array_equal(anchor['e_cost_mix_1.0'], anchor['e_cost_mix_1.0_source']), 'Ancla exterior/replay no exactos.')
        write_frame(anchor, RUN / 'outer' / f'fold{outer}_raw_replay.parquet')
        for arm in ['L', 'S']:
            part = anchor[raw.columns].copy()
            part['model_id'] = arm
            part['prediction'] = core.apply_calibration(part.annual_rate, part['e_cost_mix_1.0'], params, arm)
            part['annual_rate'] = part.prediction / part['e_cost_mix_1.0']
            part['unit_deviance'] = core.base.u.unit_deviance(part.T0, part.prediction)
            result.append(part)
        event('calibration_completed', outer=outer)
    raw['model_id'] = 'raw'
    frames = [raw]
    for arm in ['L', 'S']:
        other = raw.loc[~raw.line.eq('buildings')].copy()
        other['model_id'] = arm
        frames.extend([other, pd.concat([p for p in result if p.model_id.eq(arm).all()], ignore_index=True)])
    combined = pd.concat(frames, ignore_index=True).sort_values(['model_id', *KEY]).reset_index(drop=True)
    require(len(combined) == 3 * 50094, 'OOF no cubre tres brazos completos.')
    write_frame(combined, RUN / 'contrast_oof_2023.parquet')
    dump(RUN / 'training_completed.json', {'utc': datetime.now(timezone.utc).isoformat(),
        'new_price_GLMs': len(fitted), 'new_reporting_fits': 60, 'new_frequency_constants': 60,
        'weighted_marks_from_reporting': 60, 'new_mixtures': 10, 'new_slope_calibrations': 5,
        'new_intercept_values': 10, 'outer_bundles_reused': 5, '2024_test_closed': True,
        'promotion': False, 'submission': False})
    event('training_completed', new_GLMs=10, slope_fits=5)


if __name__ == '__main__':
    action = sys.argv[1]
    require(action in ['freeze', 'prepare', 'train'], 'Acción desconocida.')
    try:
        {'freeze': freeze_implementation, 'prepare': prepare, 'train': train}[action]()
    except Exception as error:
        dump(RUN / (action + '_error.json'), {'utc': datetime.now(timezone.utc).isoformat(),
             'error_type': type(error).__name__, 'message': str(error)})
        raise
