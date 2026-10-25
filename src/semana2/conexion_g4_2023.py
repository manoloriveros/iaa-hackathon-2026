"""Frontera de entradas G4: capital congelado por ámbito, sin estimadores o C0.

No llama al módulo de aprendizaje sintético ni añade su marcador a datos reales.
Un contrato válido no acredita que un parámetro externo esté bien estimado.
"""
from copy import deepcopy
from datetime import datetime
from numbers import Real, Integral
from pathlib import Path
import json
import math
import re
import numpy as np
import pandas as pd
from . import entradas_g4_2023 as ingress

CONTRACT = 'G4-INPUT-CONNECTION-2023-v1'
CAPITAL = 'CAPS2-01-SCOPE-v1'
FEATURES = ['x_new_business', 'x_log_sum_insured', 'x_property_age', 'x_flood_zone',
            'x_accidental_damage_cover', 'x_property_type', 'x_region']
ORIGINS = {'existing_competition_emerging2023', 'generated_synthetic2023'}
require = ingress.require


class MissingCapital(ValueError):
    """Estado pendiente esperado; nunca activa una estimación implícita."""


def exclusions(values):
    require(len(values) in (1, 2) and len(set(values)) == len(values), 'Excluir uno o dos folds distintos')
    require(all(isinstance(v, Integral) and not isinstance(v, bool) and 0 <= v < 5 for v in values), 'Fold no entero0..4')
    return sorted(int(v) for v in values)


def seal(payload):
    out = deepcopy(payload)
    require('sha256' not in out, 'Objeto ya sellado')
    out['sha256'] = ingress.digest(out)
    return out


def verify_seal(obj):
    require(isinstance(obj, dict) and 'sha256' in obj, 'Falta sello de contenido')
    payload = {k: v for k, v in obj.items() if k != 'sha256'}
    require(obj['sha256'] == ingress.digest(payload), 'Contrato modificado')


def pinned_json(root, spec):
    root = Path(root).resolve()
    path = (root / spec['path']).resolve()
    require(path.is_relative_to(root) and path.suffix == '.json', 'Ruta de manifiesto no admisible')
    require(not {p.lower() for p in path.parts}.intersection({'models', 'test', '2024', 'sel01', 'actas', 'ledger'}), 'Ámbito cerrado')
    require(not path.name.lower().startswith(('score', 'prediction', 'ledger')), 'No es un manifiesto de entradas')
    require(ingress.sha(path) == spec['sha256'], 'Manifiesto cambiado')
    return json.loads(path.read_text(encoding='utf-8-sig'))


def scope_from_manifest(manifest, excluded):
    excluded = exclusions(excluded)
    require(manifest['market'] == 'emerging' and manifest['cohort'] == 2023, 'Solo mercado emergente2023')
    require(manifest.get('C0_present') is False and manifest.get('fixture_id_added') is False, 'C0 o marcador no admisible')
    key = 'exclude_' + '_'.join(map(str, excluded))
    require(key in manifest['scopes'], 'Ámbito ausente')
    scope = manifest['scopes'][key]
    allowed = sorted(set(range(5)) - set(excluded))
    require(scope['excluded_folds'] == excluded and scope['training_folds'] == allowed, 'Lista de folds discrepante')
    files = [{'fold': f, **manifest['fold_files'][str(f)]} for f in allowed]
    require(scope['training_files'] == files, 'Lista de archivos fuera de ámbito')
    require(scope['training_input_sha256'] == ingress.digest({'membership': scope['fit_membership_sha256'], 'files': files}), 'Firma de ajuste discrepante')
    for name in ['fit_membership_sha256', 'training_input_sha256']:
        require(re.fullmatch('[0-9a-f]{64}', scope[name]) is not None, 'Firma inválida')
    require(scope.get('C0_present') is False and scope.get('learned_objects_present') is False, 'No reutilizar objetos aprendidos')
    return scope


def make_request(root, manifest_spec, excluded, source_origin):
    require(source_origin in ORIGINS, 'Procedencia no declarada')
    manifest = pinned_json(root, manifest_spec)
    scope = scope_from_manifest(manifest, excluded)
    return seal({'contract': CONTRACT, 'market': 'emerging', 'line': 'buildings', 'cohort': 2023,
        'source_origin': source_origin, 'manifest': manifest_spec, 'excluded_folds': scope['excluded_folds'],
        'training_input_sha256': scope['training_input_sha256'], 'fit_membership_sha256': scope['fit_membership_sha256'],
        'training_rows': scope['training_rows'], 'training_folds': scope['training_folds'],
        'capital_source_files': [x['capital_audit'] for x in scope['training_files']],
        'features': FEATURES, 'capital_contract': CAPITAL, 'fit_allowed': False, 'C0_present': False})


def validate_request(root, request):
    verify_seal(request)
    require(set(request) == {'contract', 'market', 'line', 'cohort', 'source_origin', 'manifest',
        'excluded_folds', 'training_input_sha256', 'fit_membership_sha256', 'training_rows',
        'training_folds', 'capital_source_files', 'features', 'capital_contract', 'fit_allowed',
        'C0_present', 'sha256'}, 'Campos ajenos al contrato de entrada')
    require(request['contract'] == CONTRACT and request['capital_contract'] == CAPITAL, 'Versión de contrato distinta')
    require(request['market'] == 'emerging' and request['line'] == 'buildings' and request['cohort'] == 2023, 'Cohorte ajena')
    require(request['source_origin'] in ORIGINS and request['features'] == FEATURES, 'Procedencia o predictores distintos')
    require(request['fit_allowed'] is False and request['C0_present'] is False, 'Frontera sin aprendizaje ni C0')
    manifest = pinned_json(root, request['manifest'])
    scope = scope_from_manifest(manifest, request['excluded_folds'])
    for k in ['training_input_sha256', 'fit_membership_sha256', 'training_rows', 'training_folds']:
        require(request[k] == scope[k], 'Contrato de otro ámbito: ' + k)
    require(request['capital_source_files'] == [x['capital_audit'] for x in scope['training_files']], 'Fuentes de capital distintas')
    return manifest, scope


def capital_template(request):
    """Petición pendiente, sin inventar estimaciones, autor o aprobación."""
    return {'contract': CAPITAL, 'status': 'missing_exact_scope_parameters',
        'source_origin': request['source_origin'], 'market': 'emerging', 'line': 'buildings', 'cohort': 2023,
        'excluded_folds': request['excluded_folds'], 'training_input_sha256': request['training_input_sha256'],
        'fit_membership_sha256': request['fit_membership_sha256'], 'capital_source_files': request['capital_source_files'],
        'threshold': 10000000., 'ppm_min': None, 'ppm_max': None, 'provenance': None,
        'rule': 'Referencias min/max de 1000*prima/capital solo en capital normal (0<capital<=1e7) del ajuste exacto; población no vacía, ratios finitos y positivos. No estimadas aquí.',
        'application': 'Capital>1e7 se divide por1000 solo si ppm<min y 1000*ppm pertenece a[min,max]; resto sospechoso aNaN; capital normal positivo se conserva.',
        'external_parameter_estimate_verified_here': False, 'fit_allowed': False}


def seal_supplied_capital(request, ppm_min, ppm_max, provenance):
    """Empaqueta valores ya suministrados. No calcula referencias de datos."""
    return seal({'contract': CAPITAL, 'source_origin': request['source_origin'], 'market': 'emerging',
        'line': 'buildings', 'cohort': 2023, 'excluded_folds': request['excluded_folds'],
        'training_input_sha256': request['training_input_sha256'], 'fit_membership_sha256': request['fit_membership_sha256'],
        'capital_source_files': request['capital_source_files'], 'threshold': 10000000.,
        'ppm_min': ppm_min, 'ppm_max': ppm_max, 'provenance': provenance})


def validate_capital(request, capital):
    if capital is None:
        raise MissingCapital('Faltan parámetros congelados de capital del ámbito exacto; no se estiman implícitamente')
    verify_seal(capital)
    expected = {'contract', 'source_origin', 'market', 'line', 'cohort', 'excluded_folds',
        'training_input_sha256', 'fit_membership_sha256', 'capital_source_files', 'threshold',
        'ppm_min', 'ppm_max', 'provenance', 'sha256'}
    require(set(capital) == expected, 'Campos ajenos al contrato de capital')
    require(capital['contract'] == CAPITAL, 'Contrato de capital distinto')
    for name in ['source_origin', 'market', 'line', 'cohort', 'excluded_folds', 'training_input_sha256',
                 'fit_membership_sha256', 'capital_source_files']:
        require(capital[name] == request[name], 'Capital de otra procedencia o ámbito: ' + name)
    for name in ['threshold', 'ppm_min', 'ppm_max']:
        value = capital[name]
        require(isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value) and value > 0, 'Parámetro no finito/positivo: ' + name)
    require(capital['threshold'] == 10000000. and capital['ppm_min'] <= capital['ppm_max'], 'Regla CAPS2-01 incompatible')
    provenance = capital['provenance']
    require(isinstance(provenance, dict) and set(provenance) == {'kind', 'author', 'utc', 'evidence'}, 'Procedencia incompleta')
    require(isinstance(provenance['author'], str) and bool(provenance['author'].strip()), 'Falta autor real del artefacto')
    stamp = datetime.fromisoformat(provenance['utc'])
    require(stamp.tzinfo is not None, 'Fecha de procedencia sin zona')
    if request['source_origin'] == 'generated_synthetic2023':
        require(provenance['kind'] == 'fixed_synthetic_constants' and provenance['evidence'] == 'not_estimated_from_rows', 'Parámetros sintéticos deben ser constantes declaradas')
    else:
        require(provenance['kind'] == 'exact_scope_estimation_receipt', 'Constantes sintéticas no admisibles para concurso')
        evidence = provenance['evidence']
        require(isinstance(evidence, dict) and set(evidence) == {'path', 'sha256'}, 'Falta recibo del productor de parámetros')
        require(re.fullmatch('[0-9a-f]{64}', evidence['sha256']) is not None, 'Recibo no identificado por SHA')
    return {k: capital[k] for k in ['excluded_folds', 'training_input_sha256', 'threshold', 'ppm_min', 'ppm_max']}


def connect_scope(root, request, capital=None):
    """Lector estricto -> capital fijo -> siete predictores -> entrada base G4.

    Es una frontera de datos. No crea transformadores, C0, GLM o calibradores.
    """
    manifest, scope = validate_request(root, request)
    parameters = validate_capital(request, capital)  # Antes de abrir valores.
    if request['source_origin'] == 'existing_competition_emerging2023':
        # Validación documental del recibo externo; su matemática no se repite.
        evidence = pinned_json(root, capital['provenance']['evidence'])
        require(evidence['contract'] == CAPITAL and evidence['training_input_sha256'] == scope['training_input_sha256'], 'Recibo de otro productor/ámbito')
        require(evidence['capital_artifact_payload_sha256'] == ingress.digest({k: v for k, v in capital.items() if k not in ['provenance', 'sha256']}), 'Recibo no corresponde a los parámetros')
    data = ingress.load_training_scope(root, manifest, request['excluded_folds'])
    periods = ingress.apply_frozen_capital(data, parameters)
    targets = data['targets'].copy()
    require(not targets.duplicated(ingress.KEY).any(), 'Objetivos duplicados')
    target_keys = pd.MultiIndex.from_frame(targets[ingress.KEY])
    require(target_keys.equals(pd.MultiIndex.from_frame(periods[ingress.KEY])), 'Objetivos/predictores no alineados')
    for name in ['fold', 'group_id', 'policy_id']:
        require(periods[name].eq(targets[name]).all(), 'Linaje de objetivo distinto')
    require(targets.T0_observed_source.ge(0).all() and np.isfinite(targets.T0_observed_source).all(), 'T0 observado inválido')
    features = periods[ingress.KEY + FEATURES].copy()
    numeric = [x for x in FEATURES if x not in ['x_property_type', 'x_region']]
    require(not np.isinf(features[numeric].to_numpy(float)).any(), 'Predictor infinito')
    require(not any(x in features for x in ['T0', 'C0', 'written_premium', 'written_premium_audit_only']), 'Columna fuera de predictores')
    frame = periods.copy()
    frame['T0'] = targets.T0_observed_source.to_numpy(copy=True)
    masked = ingress.masked_periods_for_future_C0(data)
    learning_signature = ingress.digest({'contract': CONTRACT, 'training_input_sha256': scope['training_input_sha256'],
        'capital_sha256': capital['sha256'], 'features': FEATURES})
    return {'stage': 'G4_BASE_INPUTS_ONLY', 'source_origin': request['source_origin'],
        'periods': periods, 'features': features, 'targets': targets, 'learning_frame': frame,
        'claims': data['claims'].copy(), 'c0_input_periods': masked,
        'cohort_metadata': data['cohort_metadata'], 'scope': scope,
        'receipt': {'contract': CONTRACT, 'request_sha256': request['sha256'], 'capital_sha256': capital['sha256'],
            'learning_input_sha256': learning_signature, 'training_rows': len(frame), 'features': FEATURES,
            'base_features_ready': True, 'model_input_ready': False, 'fit_allowed': False, 'C0_present': False,
            'external_parameter_estimate_verified_here': False, 'new_models': 0, 'new_C0_fits': 0,
            'new_predictions': 0, 'new_scores': 0, 'synthetic_learner_marker_added': False}}
