"""Ensayo nuevo productor->recibo->G4 sobre Parquet generados; sin modelos."""
from copy import deepcopy
from decimal import Decimal
from itertools import combinations
from pathlib import Path
from unittest.mock import patch
import json
import math
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from semana2 import entradas_g4_2023 as ingress, conexion_g4_2023 as old
from semana2 import productor_capital_g4_2023 as producer
from probar_conexion_g4_2023 import fixture, write, new_manifest, dump


def _save_manifest(root, folder, manifest, meta, name):
    manifest = deepcopy(manifest)
    manifest['scopes'] = ingress.make_scopes(meta, manifest['fold_files'])
    path = folder/(name+'.json')
    dump(path, manifest)
    return {'path': path.relative_to(root).as_posix(), 'sha256': ingress.sha(path)}, manifest


def fixture_with_varied_bounds(root, folder):
    _, manifest, tables, meta = fixture(root, folder)
    capital = tables['capital_audit']
    for f in range(5):
        capital.loc[capital.fold.eq(f)&capital.sum_insured_original.eq(200000.), 'written_premium_audit_only'] = 1000.+200*f
        capital.loc[capital.fold.eq(f)&capital.sum_insured_original.eq(10000000.), 'written_premium_audit_only'] = 5000.+1000*f
        manifest['fold_files'][str(f)]['capital_audit'] = write(root,
            root/manifest['fold_files'][str(f)]['capital_audit']['path'], capital.loc[capital.fold.eq(f)].copy())
    spec, manifest = _save_manifest(root, folder, manifest, meta, 'varied_bounds_manifest')
    return spec, manifest, tables, meta


def fork_receipt(root, folder, capital, alter_population=None, alter_receipt=None):
    folder.mkdir()
    receipt = old.pinned_json(root, capital['provenance']['evidence'])
    population = old.pinned_json(root, receipt['normal_population'])
    if alter_population:
        alter_population(population)
    population['normal_rows'] = len(population['rows'])
    population['normal_content_sha256'] = ingress.digest(population['rows'])
    population['normal_keys_sha256'] = ingress.digest([{k: r[k] for k in ingress.KEY} for r in population['rows']])
    p = folder/'normal_population.json'
    dump(p, population)
    receipt['normal_population'] = {'path': p.relative_to(root).as_posix(), 'sha256': ingress.sha(p)}
    for k in ['normal_rows', 'normal_keys_sha256', 'normal_content_sha256']:
        receipt[k] = population[k]
    if alter_receipt:
        alter_receipt(receipt)
    p = folder/'producer_receipt.json'
    dump(p, receipt)
    payload = {k: v for k, v in capital.items() if k != 'sha256'}
    payload = deepcopy(payload)
    payload['provenance']['evidence'] = {'path': p.relative_to(root).as_posix(), 'sha256': ingress.sha(p)}
    return old.seal(payload)


def verify(root, folder, real_requests):
    root, folder = Path(root), Path(folder)
    folder.mkdir()
    spec, manifest, tables, meta = fixture_with_varied_bounds(root, folder)
    checks, baseline = [], {}
    def passed(name):
        checks.append({'check': name, 'pass': True})
    def rejected(name, fn):
        try:
            fn()
        except ValueError:
            passed(name)
            return
        raise AssertionError('Invalid producer case accepted: '+name)
    scopes = [[f] for f in range(5)]+[list(x) for x in combinations(range(5), 2)]
    decimal_max_error, application_max_error = 0., 0.
    for excluded in scopes:
        name = 'exclude_'+'_'.join(map(str, excluded))
        request = producer.make_request(root, spec, excluded, 'generated_synthetic2023')
        protected = {manifest['fold_files'][str(f)][kind]['path'] for f in excluded
                     for kind in ['periods', 'targets', 'claims', 'capital_audit']}
        original = ingress.read_pinned
        phase = ['produce']
        def guarded(r, s, *args, **kwargs):
            assert s['path'] not in protected, 'Protected value file opened'
            if phase[0] == 'produce':
                assert s['path'] == manifest['metadata']['path'] or s['path'] in {x['path'] for x in request['capital_source_files']}
                assert not any(x in (kwargs.get('columns') or s['columns']) for x in ['T0', 'T0_cents', 'T0_observed_source', 'exposure_supplied_raw_audit_only'])
            return original(r, s, *args, **kwargs)
        with patch.object(ingress, 'read_pinned', guarded):
            capital = producer.produce_parameters(root, request, folder/'baseline_artifacts'/name)
            phase[0] = 'connect'
            connected = producer.connect_scope(root, request, capital)
        raw = tables['capital_audit'].loc[~tables['capital_audit'].fold.isin(excluded)]
        ratios = []
        for cap, premium in zip(raw.sum_insured_original, raw.written_premium_audit_only):
            if math.isfinite(cap) and 0 < cap <= 10000000.:
                ratios.append(Decimal(1000)*Decimal(str(premium))/Decimal(str(cap)))
        assert connected['receipt']['normal_rows'] == len(ratios) == 2*(5-len(excluded))
        for field, reference in [('ppm_min', min(ratios)), ('ppm_max', max(ratios))]:
            error = abs(capital[field]-float(reference))
            decimal_max_error = max(decimal_max_error, error)
            assert error <= 1e-12
        # Referencia independiente de aplicación, sin llamar al helper probado.
        expected = []
        for cap, premium in zip(raw.sum_insured_original, raw.written_premium_audit_only):
            if not math.isfinite(cap) or cap <= 0:
                expected.append(np.nan)
                continue
            value = Decimal(str(cap))
            if value > Decimal(10000000):
                ratio = Decimal(1000)*Decimal(str(premium))/value
                if ratio < min(ratios) and min(ratios) <= 1000*ratio <= max(ratios):
                    value /= 1000
                else:
                    expected.append(np.nan)
                    continue
            expected.append(math.log(float(value)))
        np.testing.assert_allclose(connected['periods'].x_log_sum_insured, expected, rtol=0, atol=1e-12, equal_nan=True)
        errors = np.abs(connected['periods'].x_log_sum_insured.to_numpy()-expected)
        application_max_error = max(application_max_error, float(np.nanmax(errors)))
        assert len(connected['learning_frame']) == len(raw)
        assert connected['receipt']['normal_population_replayed_against_allowed_capital']
        assert not connected['receipt']['fit_allowed'] and not connected['receipt']['C0_present']
        assert not any(c in connected['features'] for c in ['T0', 'C0', 'written_premium_audit_only'])
        baseline[tuple(excluded)] = (request, capital, connected)
        passed('producer_receipt_connection_Decimal_'+name)
    # Todos los ámbitos: nueva producción no depende de los valores protegidos.
    base_files = {root/s['path']: (root/s['path']).read_bytes() for kinds in manifest['fold_files'].values() for s in kinds.values()}
    for i, excluded in enumerate(scopes):
        for p, content in base_files.items():
            p.write_bytes(content)  # Solo se restauran fixtures generados.
        changed, _ = new_manifest(root, folder, manifest, meta, [excluded[0]], 'poison_'+str(i))
        request2 = producer.make_request(root, changed, excluded, 'generated_synthetic2023')
        capital2 = producer.produce_parameters(root, request2, folder/'poison_artifacts'/str(i))
        connected2 = producer.connect_scope(root, request2, capital2)
        request1, capital1, connected1 = baseline[tuple(excluded)]
        assert request1['sha256'] != request2['sha256']
        assert capital1['sha256'] != capital2['sha256']  # Recibos/rutas/UTC son archivísticos.
        assert producer._payload(capital1) == producer._payload(capital2)
        for key in ['parameter_learning_sha256', 'learning_input_sha256']:
            assert connected1['receipt'][key] == connected2['receipt'][key]
        for key in ['periods', 'features', 'targets', 'claims', 'learning_frame']:
            pd.testing.assert_frame_equal(connected1[key], connected2[key])
        passed('protected_poison_producer_and_connection_'+str(excluded))
    for p, content in base_files.items():
        p.write_bytes(content)
    request, capital, connected = baseline[(0,)]
    rejected('outer_parameters_not_inner', lambda: producer.connect_scope(root, baseline[(0, 1)][0], capital))
    bad_hash = {**capital, 'ppm_max': 999.}
    rejected('modified_parameter_seal', lambda: producer.connect_scope(root, request, bad_hash))
    bad = old.seal({**{k: v for k, v in capital.items() if k != 'sha256'}, 'ppm_min': float('inf')})
    rejected('nonfinite_produced_parameter', lambda: producer.connect_scope(root, request, bad))
    missing_receipt = deepcopy(capital)
    missing_receipt.pop('sha256')
    missing_receipt['provenance']['evidence']['sha256'] = '0'*64
    rejected('modified_receipt_hash', lambda: producer.connect_scope(root, request, old.seal(missing_receipt)))
    # Falsificación internamente coherente del recibo: solo replay contra capital
    # de ajuste puede descubrir que se omitió una fila de población normal.
    omitted = fork_receipt(root, folder/'omitted_normal', capital,
        alter_population=lambda p: p['rows'].pop())
    producer.validate_evidence(root, request, omitted)
    rejected('coherently_resealed_omitted_normal_fails_actual_population_replay', lambda: producer.connect_scope(root, request, omitted))
    bad_count = fork_receipt(root, folder/'bad_training_count', capital,
        alter_receipt=lambda r: r.update(training_rows=r['training_rows']-1))
    rejected('receipt_training_population_count_wrong', lambda: producer.connect_scope(root, request, bad_count))
    original_frame = tables['capital_audit'].loc[~tables['capital_audit'].fold.eq(0)].copy()
    normal_index = original_frame.index[original_frame.sum_insured_original.eq(200000.)][0]
    for label, value in [('zero', 0.), ('negative', -1.), ('nan', np.nan), ('infinite', np.inf), ('overflow', 1e308)]:
        frame = original_frame.copy()
        frame.loc[normal_index, 'written_premium_audit_only'] = value
        rejected('normal_premium_'+label, lambda frame=frame: producer.normal_population(frame))
    empty = original_frame.copy()
    empty['sum_insured_original'] = 10000001.
    rejected('empty_normal_population_no_fallback', lambda: producer.normal_population(empty))
    rejected('duplicated_capital_key', lambda: producer.normal_population(pd.concat([original_frame, original_frame.iloc[[0]]])))
    # Control de respuesta: un capital permitido cambia la referencia máxima.
    changed_manifest = deepcopy(manifest)
    p = root/changed_manifest['fold_files']['4']['capital_audit']['path']
    f = pq.read_table(p, columns=changed_manifest['fold_files']['4']['capital_audit']['columns']).to_pandas()
    f.loc[f.sum_insured_original.eq(200000.), 'written_premium_audit_only'] *= 2
    changed_manifest['fold_files']['4']['capital_audit'] = write(root, p, f)
    changed_spec, _ = _save_manifest(root, folder, changed_manifest, meta, 'allowed_capital_changed')
    new_request = producer.make_request(root, changed_spec, [0], 'generated_synthetic2023')
    rejected('changed_allowed_capital_invalidates_previous_parameters', lambda: producer.connect_scope(root, new_request, capital))
    new_capital = producer.produce_parameters(root, new_request, folder/'positive_control')
    assert capital['ppm_max'] == 9. and new_capital['ppm_max'] == 18.
    fresh = producer.connect_scope(root, new_request, new_capital)
    assert fresh['receipt']['parameter_learning_sha256'] != connected['receipt']['parameter_learning_sha256']
    passed('allowed_premium_positive_control_changes_estimated_bound')
    replay = producer.connect_scope(root, new_request, json.loads((folder/'positive_control/capital_parameters.json').read_text(encoding='utf-8')))
    pd.testing.assert_frame_equal(replay['learning_frame'], fresh['learning_frame'])
    passed('producer_disk_artifact_receipt_population_replay_without_models')
    # La v1 sigue intacta: no acepta artefactos v2 como constantes ficticias.
    old_request = old.make_request(root, changed_spec, [0], 'generated_synthetic2023')
    rejected('v2_artifact_not_silently_admitted_by_v1', lambda: old.connect_scope(root, old_request, new_capital))
    # Reales: solo solicitudes y falta de parámetros, nunca ejecutar productor.
    with patch.object(ingress, 'load_training_scope', side_effect=AssertionError('Real values opened')):
        for key, real_request in real_requests.items():
            rejected('real_'+key+'_still_missing_parameters', lambda q=real_request: producer.connect_scope(root, q))
        real = next(iter(real_requests.values()))
        forged = producer._payload(new_capital)
        forged = {**forged, **{k: real[k] for k in ['source_origin', 'excluded_folds', 'training_input_sha256', 'fit_membership_sha256', 'capital_source_files']}}
        forged['provenance'] = new_capital['provenance']
        rejected('synthetic_producer_receipt_cannot_unlock_real_request', lambda: producer.connect_scope(root, real, old.seal(forged)))
    return {'success': True, 'checks': checks, 'synthetic_parameter_artifacts': 31,
        'synthetic_baseline_scopes': 15, 'protected_input_invariance_cases': 15,
        'normal_bound_Decimal_max_abs_error': decimal_max_error,
        'capital_application_math_log_max_abs_error': application_max_error,
        'coherent_bad_receipt_rejected_by_numeric_population_replay': True,
        'new_model_fits': 0, 'new_C0_calls': 0, 'new_predictions': 0, 'new_scores': 0,
        'real_row_values_decoded': 0, 'real_parameter_artifacts': 0,
        'whole_model_object_invariance_claimed': False, 'real_positive_parameter_execution_tested': False}
