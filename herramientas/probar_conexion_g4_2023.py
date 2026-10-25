"""Verifica la frontera nueva con archivos generados y parámetros fijos; cero fit."""
from copy import deepcopy
from decimal import Decimal
from itertools import combinations
from pathlib import Path
from unittest.mock import patch
import json
import math
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from semana2 import entradas_g4_2023 as ingress, conexion_g4_2023 as bridge
from semana2.flujo_g4_sintetico2023 import FEATURES as G4_FEATURES

ORIGIN = 'generated_synthetic2023'
PROVENANCE = {'kind': 'fixed_synthetic_constants', 'author': 'Codex (synthetic fixture)',
              'utc': '2026-10-24T20:00:00+00:00', 'evidence': 'not_estimated_from_rows'}


def dump(path, obj):
    with path.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def write(root, path, frame):
    path.parent.mkdir(exist_ok=True, parents=True)
    pq.write_table(pa.Table.from_pandas(frame, preserve_index=False), path)
    return {'path': path.relative_to(root).as_posix(), 'sha256': ingress.sha(path),
            'columns': list(frame), 'kind': 'prepared'}


def fixture(root, folder):
    metadata = []
    for fold in range(5):
        for line in ['buildings', 'motor', 'contents']:
            for j in range(8 if line == 'buildings' else 1):
                key = f'SYN-G4-CONNECT-{line}-{fold}-{j}'
                metadata.append(dict(market='emerging', line=line, row_id=key, year=2023, is_test=False,
                    fold=fold, group_id=key+'-G', customer_id=key+'-C', address_id=key+'-A', policy_id=key+'-P'))
    meta = pd.DataFrame(metadata).sort_values(ingress.KEY).reset_index(drop=True)
    periods = meta.loc[meta.line.eq('buildings')].copy().reset_index(drop=True)
    periods['period_start'] = pd.Timestamp('2023-01-01')
    periods['period_end'] = pd.Timestamp('2023-12-31')
    periods['exposure'] = 1.
    periods['x_new_business'] = [float(i % 2) for i in range(len(periods))]
    periods['x_property_age'] = 20.
    periods['x_flood_zone'] = 1.
    periods['x_accidental_damage_cover'] = periods.x_new_business
    periods['x_property_type'] = 'synthetic_house'
    periods['x_region'] = 'synthetic_region'
    targets = periods[ingress.META].copy()
    targets['T0_cents'] = np.arange(1000, 1000+len(periods), dtype='int64')
    targets['T0_observed_source'] = targets.T0_cents / 100.
    claims = periods[ingress.META].copy()
    claims['claim_id'] = claims.row_id + '-CLAIM'
    claims['included_in_T0'] = True
    claims['loss_date'] = pd.Timestamp('2023-06-01')
    claims['report_date'] = pd.Timestamp('2023-07-01')
    claims['peril'] = 'fire'
    claims['T0_cents'] = targets.T0_cents
    capital = periods[ingress.META].copy()
    capital['sum_insured_original'] = [200000., 300000000., 400000000., 500000000., 0., np.nan, 10000000., 200000000.]*5
    capital['written_premium_audit_only'] = [200., 300., .01, 1000000., 200., 200., 1., 100.]*5
    capital['exposure_supplied_raw_audit_only'] = 1.
    tables = dict(periods=periods, targets=targets, claims=claims, capital_audit=capital)
    foldfiles = {str(fold): {name: write(root, folder/name/f'fold_{fold}.parquet', frame.loc[frame.fold.eq(fold)].copy())
                            for name, frame in tables.items()} for fold in range(5)}
    manifest = {'id': 'GENERATED-G4-CONNECTION-FIXTURE-v1', 'market': 'emerging', 'cohort': 2023,
        'metadata': write(root, folder/'memberships.parquet', meta), 'fold_files': foldfiles,
        'scopes': ingress.make_scopes(meta, foldfiles), 'C0_present': False,
        'fixture_id_added': False, 'no_synthetic_relabeling': True}
    path = folder/'fixture_manifest_v1.json'
    dump(path, manifest)
    return {'path': path.relative_to(root).as_posix(), 'sha256': ingress.sha(path)}, manifest, tables, meta


def new_manifest(root, folder, old, meta, folds, suffix):
    manifest = deepcopy(old)
    for fold in folds:
        for name in ['periods', 'targets', 'claims', 'capital_audit']:
            spec = manifest['fold_files'][str(fold)][name]
            path = root/spec['path']
            f = pq.read_table(path, columns=spec['columns']).to_pandas()
            if name == 'periods':
                f['x_property_age'] = 99999.
            elif name == 'capital_audit':
                f['sum_insured_original'] = 999999999.
                f['written_premium_audit_only'] = 0.
            elif name == 'targets':
                f['T0_cents'] = 999999999
                f['T0_observed_source'] = 9999999.99
            else:
                f['T0_cents'] = 999999999
            manifest['fold_files'][str(fold)][name] = write(root, path, f)
    manifest['scopes'] = ingress.make_scopes(meta, manifest['fold_files'])
    path = folder/f'fixture_manifest_{suffix}.json'
    dump(path, manifest)
    return {'path': path.relative_to(root).as_posix(), 'sha256': ingress.sha(path)}, manifest


def verify(root, folder, real_requests):
    root, folder = Path(root), Path(folder)
    folder.mkdir()
    spec, manifest, tables, meta = fixture(root, folder)
    checks = []
    def passed(name):
        checks.append({'check': name, 'pass': True})
    def rejected(name, fn):
        try:
            fn()
        except ValueError:
            passed(name)
            return
        raise AssertionError('Invalid input accepted: '+name)
    assert bridge.FEATURES == G4_FEATURES
    passed('seven_feature_contract_matches_G4')
    scopes = [[x] for x in range(5)] + [list(x) for x in combinations(range(5), 2)]
    baselines = {}
    for excluded in scopes:
        key = tuple(excluded)
        request = bridge.make_request(root, spec, excluded, ORIGIN)
        capital = bridge.seal_supplied_capital(request, .5, 5., PROVENANCE)
        protected = {manifest['fold_files'][str(f)][name]['path'] for f in excluded for name in ['periods', 'targets', 'claims', 'capital_audit']}
        original = ingress.read_pinned
        def guarded(r, s, *args, **kwargs):
            assert s['path'] not in protected, 'Protected value file opened'
            return original(r, s, *args, **kwargs)
        with patch.object(ingress, 'read_pinned', guarded):
            result = bridge.connect_scope(root, request, capital)
        assert len(result['learning_frame']) == (5-len(excluded))*8
        pd.testing.assert_series_equal(result['learning_frame'].T0, result['targets'].T0_observed_source, check_names=False)
        masked = result['c0_input_periods']
        assert masked.loc[masked.fold.isin(excluded), ['period_start', 'period_end', 'exposure']].isna().all().all()
        assert not result['receipt']['model_input_ready'] and not result['receipt']['C0_present']
        assert not result['receipt']['fit_allowed'] and not result['receipt']['synthetic_learner_marker_added']
        assert set(result['features']) == set(ingress.KEY + G4_FEATURES)
        assert 'written_premium_audit_only' not in result['learning_frame']
        baselines[key] = (request, capital, result)
        passed('synthetic_disk_ingress_to_G4_scope_'+str(excluded))

    # Otra aritmética: Decimal para la regla, math.log para el predictor.
    p = baselines[(0,)][2]['periods']
    raw = p[ingress.KEY].merge(tables['capital_audit'], on=ingress.KEY, validate='one_to_one')
    expected = []
    for cap, premium in zip(raw.sum_insured_original, raw.written_premium_audit_only):
        if not math.isfinite(cap) or cap <= 0:
            expected.append(np.nan)
            continue
        cap, premium = Decimal(str(cap)), Decimal(str(premium))
        if cap > Decimal('10000000'):
            ratio = Decimal('1000')*premium/cap
            if ratio < Decimal('.5') and Decimal('.5') <= ratio*1000 <= Decimal('5'):
                cap = cap/1000
            else:
                expected.append(np.nan)
                continue
        expected.append(math.log(float(cap)))
    np.testing.assert_allclose(p.x_log_sum_insured, expected, rtol=0, atol=1e-12, equal_nan=True)
    max_error = float(np.nanmax(np.abs(p.x_log_sum_insured.to_numpy()-expected)))
    passed('capital_Decimal_and_math_log_reference_32_rows')

    request, capital, _ = baselines[(0,) ]
    def mutate_cap(**changes):
        return bridge.seal({**{k: v for k, v in capital.items() if k != 'sha256'}, **changes})
    bad = [('wrong_exclusions', mutate_cap(excluded_folds=[0, 1])),
           ('wrong_training_hash', mutate_cap(training_input_sha256='a'*64)),
           ('wrong_membership_hash', mutate_cap(fit_membership_sha256='b'*64)),
           ('wrong_capital_sources', mutate_cap(capital_source_files=[])),
           ('infinite_min', mutate_cap(ppm_min=float('inf'))),
           ('nan_max', mutate_cap(ppm_max=float('nan'))),
           ('zero_min', mutate_cap(ppm_min=0.)),
           ('reversed_interval', mutate_cap(ppm_min=6.)),
           ('wrong_threshold', mutate_cap(threshold=100000.)),
           ('target_in_parameter_object', mutate_cap(T0=100.)),
           ('wrong_origin', mutate_cap(source_origin='existing_competition_emerging2023')),
           ('invented_provenance', mutate_cap(provenance={**PROVENANCE, 'kind': 'exact_scope_estimation_receipt'})),
           ('modified_seal', {**capital, 'ppm_max': 99.})]
    with patch.object(ingress, 'load_training_scope', side_effect=AssertionError('Values opened before capital validation')):
        for name, obj in bad:
            rejected(name+'_before_values', lambda obj=obj: bridge.connect_scope(root, request, obj))
        rejected('capital_template_is_not_a_parameter_artifact', lambda: bridge.connect_scope(root, request, bridge.capital_template(request)))
        rejected('missing_capital_before_values', lambda: bridge.connect_scope(root, request))
        altered = bridge.seal({**{k: v for k, v in request.items() if k != 'sha256'}, 'features': G4_FEATURES+['T0']})
        rejected('target_feature_rejected_before_values', lambda: bridge.connect_scope(root, altered, capital))
        changed = bridge.seal({**{k: v for k, v in request.items() if k != 'sha256'}, 'cohort': 2024})
        rejected('different_cohort_request_before_values', lambda: bridge.connect_scope(root, changed, capital))

    # Cambian solo archivos protegidos, no su ubicación ni archivos de ajuste.
    poisoned_spec, poisoned_manifest = new_manifest(root, folder, manifest, meta, [0], 'protected0')
    for excluded in [[0], [0, 1]]:
        request2 = bridge.make_request(root, poisoned_spec, excluded, ORIGIN)
        old_request, same_capital, old_result = baselines[tuple(excluded)]
        result2 = bridge.connect_scope(root, request2, same_capital)
        assert request2['sha256'] != old_request['sha256']
        assert result2['receipt']['learning_input_sha256'] == old_result['receipt']['learning_input_sha256']
        for name in ['periods', 'features', 'targets', 'claims', 'learning_frame']:
            pd.testing.assert_frame_equal(result2[name], old_result[name])
        passed('protected_value_poison_input_invariance_'+str(excluded))
    changed_spec, _ = new_manifest(root, folder, poisoned_manifest, meta, [2], 'allowed2')
    request3 = bridge.make_request(root, changed_spec, [0], ORIGIN)
    rejected('changed_allowed_source_invalidates_old_capital', lambda: bridge.connect_scope(root, request3, baselines[(0,)][1]))
    capital3 = bridge.seal_supplied_capital(request3, .5, 5., PROVENANCE)
    result3 = bridge.connect_scope(root, request3, capital3)
    assert result3['receipt']['learning_input_sha256'] != baselines[(0,)][2]['receipt']['learning_input_sha256']
    assert not result3['features'].equals(baselines[(0,)][2]['features'])
    passed('allowed_value_change_positive_control_without_fit')
    dump(folder/'request_roundtrip.json', request3)
    dump(folder/'capital_roundtrip.json', capital3)
    replay = bridge.connect_scope(root, json.loads((folder/'request_roundtrip.json').read_text(encoding='utf-8')),
        json.loads((folder/'capital_roundtrip.json').read_text(encoding='utf-8')))
    pd.testing.assert_frame_equal(replay['learning_frame'], result3['learning_frame'])
    passed('disk_contract_roundtrip_without_fit_or_C0')

    # Reales: solo manifiesto/contratos. Ninguna lectura de valores permitida.
    with patch.object(ingress, 'load_training_scope', side_effect=AssertionError('Real values opened in this work')):
        for key, real_request in real_requests.items():
            rejected('real_'+key+'_missing_capital_before_values', lambda q=real_request: bridge.connect_scope(root, q))
        q = next(iter(real_requests.values()))
        fake_for_real = bridge.seal_supplied_capital(q, .5, 5., PROVENANCE)
        rejected('synthetic_constants_cannot_unlock_real_request', lambda: bridge.connect_scope(root, q, fake_for_real))
    return {'success': True, 'checks': checks, 'synthetic_scope_connections': 15,
        'real_missing_parameter_blocks': len(real_requests), 'real_value_frames_decoded': 0,
        'capital_reference_rows': len(p), 'capital_reference_max_abs_error': max_error,
        'input_poison_invariance_cases': 2, 'whole_learned_object_invariance_claimed': False,
        'new_model_fits': 0, 'new_C0_fits': 0, 'new_inferences': 0, 'new_scores': 0,
        'real_parameter_producer_available': False, 'real_parameter_receipt_positive_flow_tested': False}
