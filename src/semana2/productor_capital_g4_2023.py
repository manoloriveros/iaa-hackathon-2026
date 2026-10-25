"""Productor CAPS2-01 por ámbito y conexión G4 v2, sin modelos o C0.

La población de referencias es un subconjunto de capitales normales, no una
exclusión de filas del modelo. Los artefactos no autorizan aprendizaje posterior.
"""
from datetime import datetime, timezone
from pathlib import Path
import json
import numpy as np
import pandas as pd
from . import entradas_g4_2023 as ingress, conexion_g4_2023 as previous

CONTRACT = 'G4-INPUT-CONNECTION-2023-v2'
CAPITAL = 'CAPS2-01-SCOPE-v2'
METHOD = 'NORMAL_POSITIVE_CAP_LE_1E7_MINMAX_PPM-v1'
FEATURES = previous.FEATURES
require = ingress.require
POP_COLUMNS = ingress.KEY + ['fold', 'group_id', 'sum_insured_original', 'written_premium_audit_only', 'ppm']


def _payload(obj):
    return {k: v for k, v in obj.items() if k not in ['provenance', 'sha256']}


def make_request(root, manifest_spec, excluded, source_origin):
    old = previous.make_request(root, manifest_spec, excluded, source_origin)
    return previous.seal({**{k: v for k, v in old.items() if k != 'sha256'},
                          'contract': CONTRACT, 'capital_contract': CAPITAL})


def validate_request(root, request):
    previous.verify_seal(request)
    require(request['contract'] == CONTRACT and request['capital_contract'] == CAPITAL, 'Contrato v2 requerido')
    old = previous.seal({**{k: v for k, v in request.items() if k != 'sha256'},
        'contract': previous.CONTRACT, 'capital_contract': previous.CAPITAL})
    return previous.validate_request(root, old)


def capital_requirement(request):
    out = previous.capital_template(request)
    out.update(contract=CAPITAL, producer=METHOD, producer_implemented=True,
               status='missing_exact_scope_produced_parameters')
    return out


def read_capital_scope(root, request):
    manifest, scope = validate_request(root, request)
    meta, _ = ingress.read_pinned(root, manifest['metadata'])
    ingress.validate_membership(meta)
    selected, _ = ingress.select_scope(meta.to_dict('records'), request['excluded_folds'])
    require(ingress.membership_digest(selected) == request['fit_membership_sha256'], 'Pertenencias discrepantes')
    frames = []
    columns = ingress.META + ['sum_insured_original', 'written_premium_audit_only']
    for entry in scope['training_files']:
        require(entry['fold'] not in request['excluded_folds'], 'Capital protegido en solicitud')
        frame, _ = ingress.read_pinned(root, entry['capital_audit'], columns=columns, expected_fold=entry['fold'])
        frames.append(frame)
    frame = pd.concat(frames, ignore_index=True).sort_values(ingress.KEY).reset_index(drop=True)
    expected = pd.DataFrame(selected).sort_values(ingress.KEY).reset_index(drop=True)
    require(len(frame) == len(expected) and not frame.duplicated(ingress.KEY).any(), 'Capital incompleto o repetido')
    for col in ingress.META:
        require(frame[col].eq(expected[col]).all(), 'Linaje de capital discrepante: '+col)
    return frame


def normal_population(frame):
    """Cálculo determinista; no consulta etiquetas, exposiciones o predictores."""
    require(not frame.duplicated(ingress.KEY).any(), 'Capital repetido')
    cap = pd.to_numeric(frame.sum_insured_original, errors='raise').to_numpy(float)
    premium = pd.to_numeric(frame.written_premium_audit_only, errors='raise').to_numpy(float)
    normal = np.isfinite(cap) & (cap > 0) & (cap <= 10000000.)
    require(normal.any(), 'Población normal vacía; no hay fallback')
    with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
        ppm = 1000*premium[normal]/cap[normal]
    require(np.isfinite(ppm).all() and (ppm > 0).all(), 'Prima por mil normal no finita o no positiva')
    selected = frame.loc[normal, ingress.KEY+['fold', 'group_id']].copy()
    selected['sum_insured_original'] = cap[normal]
    selected['written_premium_audit_only'] = premium[normal]
    selected['ppm'] = ppm
    selected = selected.sort_values(ingress.KEY).reset_index(drop=True)
    records = selected[POP_COLUMNS].to_dict('records')
    return {'method': METHOD, 'normal_rows': len(selected), 'rows': records,
        'normal_keys_sha256': ingress.digest(selected[ingress.KEY].to_dict('records')),
        'normal_content_sha256': ingress.digest(records), 'ppm_min': float(ppm.min()), 'ppm_max': float(ppm.max())}


def _dump(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def produce_parameters(root, request, output_folder, author='Codex', utc=None):
    """Lee solo metadatos y capitales permitidos; escribe población/recibo/objeto.

    No se invoca sobre datos reales durante la validación sintética de este ciclo.
    """
    require(isinstance(author, str) and bool(author.strip()), 'Falta autor')
    utc = utc or datetime.now(timezone.utc).isoformat()
    require(datetime.fromisoformat(utc).utcoffset() is not None, 'Fecha sin zona')
    root, output_folder = Path(root).resolve(), Path(output_folder).resolve()
    require(output_folder.is_relative_to(root), 'Salida fuera del workspace')
    require(not output_folder.exists(), 'No sobrescribir artefactos del productor')
    frame = read_capital_scope(root, request)
    population = normal_population(frame)
    payload = {'contract': CAPITAL, 'source_origin': request['source_origin'], 'market': 'emerging',
        'line': 'buildings', 'cohort': 2023, 'excluded_folds': request['excluded_folds'],
        'training_input_sha256': request['training_input_sha256'],
        'fit_membership_sha256': request['fit_membership_sha256'],
        'capital_source_files': request['capital_source_files'], 'threshold': 10000000.,
        'ppm_min': population['ppm_min'], 'ppm_max': population['ppm_max']}
    output_folder.mkdir(parents=True)
    pop_path, receipt_path = output_folder/'normal_population.json', output_folder/'producer_receipt.json'
    _dump(pop_path, {'contract': CAPITAL, 'source_origin': request['source_origin'],
        'training_input_sha256': request['training_input_sha256'], **population})
    receipt = {'contract': CAPITAL, 'method': METHOD, 'author': author, 'utc': utc,
        'source_origin': request['source_origin'], 'excluded_folds': request['excluded_folds'],
        'training_input_sha256': request['training_input_sha256'],
        'fit_membership_sha256': request['fit_membership_sha256'],
        'capital_source_files': request['capital_source_files'], 'training_rows': len(frame),
        'normal_rows': population['normal_rows'], 'normal_keys_sha256': population['normal_keys_sha256'],
        'normal_content_sha256': population['normal_content_sha256'],
        'ppm_min': population['ppm_min'], 'ppm_max': population['ppm_max'],
        'capital_artifact_payload_sha256': ingress.digest(payload),
        'normal_population': {'path': pop_path.relative_to(root).as_posix(), 'sha256': ingress.sha(pop_path)},
        'producer_source_sha256': ingress.sha(Path(__file__)), 'model_fits': 0, 'C0_calls': 0}
    _dump(receipt_path, receipt)
    kind = ('synthetic_scope_estimation_receipt' if request['source_origin'] == 'generated_synthetic2023'
            else 'exact_scope_estimation_receipt')
    capital = previous.seal({**payload, 'provenance': {'kind': kind, 'author': author, 'utc': utc,
        'evidence': {'path': receipt_path.relative_to(root).as_posix(), 'sha256': ingress.sha(receipt_path)}}})
    _dump(output_folder/'capital_parameters.json', capital)
    return capital


def validate_evidence(root, request, capital):
    if capital is None:
        raise previous.MissingCapital('Faltan parámetros producidos del ámbito exacto')
    previous.verify_seal(capital)
    expected = {'contract', 'source_origin', 'market', 'line', 'cohort', 'excluded_folds', 'training_input_sha256',
        'fit_membership_sha256', 'capital_source_files', 'threshold', 'ppm_min', 'ppm_max', 'provenance', 'sha256'}
    require(set(capital) == expected and capital['contract'] == CAPITAL, 'Artefacto de otro contrato')
    for field in ['source_origin', 'market', 'line', 'cohort', 'excluded_folds', 'training_input_sha256',
                  'fit_membership_sha256', 'capital_source_files']:
        require(capital[field] == request[field], 'Parámetros de otro ámbito/origen: '+field)
    for field in ['threshold', 'ppm_min', 'ppm_max']:
        value = capital[field]
        require(isinstance(value, (int, float)) and not isinstance(value, bool) and np.isfinite(value) and value > 0, 'Parámetro inválido')
    require(capital['threshold'] == 10000000. and capital['ppm_min'] <= capital['ppm_max'], 'Regla incompatible')
    provenance = capital['provenance']
    require(set(provenance) == {'kind', 'author', 'utc', 'evidence'}, 'Procedencia incompleta')
    kind = ('synthetic_scope_estimation_receipt' if request['source_origin'] == 'generated_synthetic2023'
            else 'exact_scope_estimation_receipt')
    require(provenance['kind'] == kind, 'No transferir parámetros sintéticos a datos reales')
    receipt = previous.pinned_json(root, provenance['evidence'])
    require(receipt['contract'] == CAPITAL and receipt['method'] == METHOD, 'Productor/contrato distinto')
    require(receipt['author'] == provenance['author'] and receipt['utc'] == provenance['utc'], 'Autor o fecha distintos')
    require(isinstance(receipt['author'], str) and bool(receipt['author'].strip()), 'Falta autor')
    require(datetime.fromisoformat(receipt['utc']).utcoffset() is not None, 'Fecha sin zona')
    for field in ['source_origin', 'excluded_folds', 'training_input_sha256', 'fit_membership_sha256', 'capital_source_files']:
        require(receipt[field] == request[field], 'Recibo de otro ámbito: '+field)
    require(receipt['capital_artifact_payload_sha256'] == ingress.digest(_payload(capital)), 'Recibo de otro contenido')
    population = previous.pinned_json(root, receipt['normal_population'])
    require(population['contract'] == CAPITAL and population['method'] == METHOD, 'Población de otro método')
    require(population['source_origin'] == request['source_origin'] and population['training_input_sha256'] == request['training_input_sha256'], 'Población de otro origen/ajuste')
    require(isinstance(population['normal_rows'], int) and 0 < population['normal_rows'] <= request['training_rows'], 'Población normal inválida')
    require(population['normal_rows'] == len(population['rows']) == receipt['normal_rows'], 'Conteo de población distinto')
    require(ingress.digest(population['rows']) == population['normal_content_sha256'] == receipt['normal_content_sha256'], 'Contenido de población modificado')
    keys = [{k: row[k] for k in ingress.KEY} for row in population['rows']]
    require(ingress.digest(keys) == population['normal_keys_sha256'] == receipt['normal_keys_sha256'], 'Claves de población distintas')
    for field in ['ppm_min', 'ppm_max']:
        require(population[field] == receipt[field] == capital[field], 'Límite del recibo distinto')
    return receipt, population


def connect_scope(root, request, capital=None):
    manifest, scope = validate_request(root, request)
    receipt, population = validate_evidence(root, request, capital)
    data = ingress.load_training_scope(root, manifest, request['excluded_folds'])
    replay = normal_population(data['capital_audit'])
    for field in ['normal_rows', 'normal_keys_sha256', 'normal_content_sha256', 'ppm_min', 'ppm_max']:
        require(replay[field] == population[field], 'Población/aritmética del recibo no reproduce el ajuste: '+field)
    require(receipt['training_rows'] == len(data['periods']), 'Población de ajuste incompleta')
    parameters = {k: capital[k] for k in ['excluded_folds', 'training_input_sha256', 'threshold', 'ppm_min', 'ppm_max']}
    periods = ingress.apply_frozen_capital(data, parameters)
    targets = data['targets'].copy()
    require(not targets.duplicated(ingress.KEY).any(), 'Objetivos duplicados')
    require(pd.MultiIndex.from_frame(targets[ingress.KEY]).equals(pd.MultiIndex.from_frame(periods[ingress.KEY])), 'Objetivos no alineados')
    for name in ['fold', 'group_id', 'policy_id']:
        require(periods[name].eq(targets[name]).all(), 'Linaje de objetivo distinto')
    require(targets.T0_observed_source.ge(0).all() and np.isfinite(targets.T0_observed_source).all(), 'T0 inválido')
    features = periods[ingress.KEY+FEATURES].copy()
    numeric = [x for x in FEATURES if x not in ['x_property_type', 'x_region']]
    require(not np.isinf(features[numeric].to_numpy(float)).any(), 'Predictor infinito')
    frame = periods.copy()
    frame['T0'] = targets.T0_observed_source.to_numpy(copy=True)
    parameter_signature = ingress.digest({'payload': _payload(capital), 'normal_content_sha256': population['normal_content_sha256']})
    learning_signature = ingress.digest({'contract': CONTRACT, 'training_input_sha256': request['training_input_sha256'],
        'parameter_learning_sha256': parameter_signature, 'features': FEATURES})
    return {'stage': 'G4_BASE_INPUTS_ONLY', 'source_origin': request['source_origin'],
        'periods': periods, 'features': features, 'targets': targets, 'learning_frame': frame,
        'claims': data['claims'].copy(), 'cohort_metadata': data['cohort_metadata'], 'scope': scope,
        'c0_input_periods': ingress.masked_periods_for_future_C0(data),
        'receipt': {'contract': CONTRACT, 'request_sha256': request['sha256'], 'capital_sha256': capital['sha256'],
            'parameter_learning_sha256': parameter_signature, 'learning_input_sha256': learning_signature,
            'normal_population_replayed_against_allowed_capital': True, 'training_rows': len(frame),
            'normal_rows': population['normal_rows'], 'base_features_ready': True,
            'model_input_ready': False, 'C0_present': False, 'fit_allowed': False,
            'new_models': 0, 'new_C0_calls': 0, 'new_predictions': 0, 'new_scores': 0,
            'synthetic_learner_marker_added': False}}
