"""Produce capital por ámbito en2023 y comprueba G4, sin modelos/C0."""
from contextlib import ExitStack
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
import json
import math
import pickle
import socket
import sys
import traceback
ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(REPO/'src'))
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import joblib
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sklearn.linear_model import TweedieRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from semana2 import productor_capital_g4_2023 as producer, entradas_g4_2023 as ingress
from semana2 import c0_estricto2023 as c0, flujo_g4_sintetico2023 as old_flow
PLAN = REPO/'registro/semana2_g4_capital_real_plan_v1.json'
RUN = REPO/'privado/semana2/capital_real_g4_2023/produccion_20261024_v1'
rel = lambda p: p.relative_to(ROOT).as_posix()
now = lambda: datetime.now(timezone.utc).isoformat()


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def independent_arithmetic(raw, capital, connected):
    ratios, expected = [], []
    for cap, premium in zip(raw.sum_insured_original, raw.written_premium_audit_only):
        if math.isfinite(cap) and 0 < cap <= 10000000.:
            ratios.append(Decimal(1000)*Decimal(str(premium))/Decimal(str(cap)))
    assert ratios
    errors = {k: abs(capital[k]-float(ref)) for k, ref in [('ppm_min', min(ratios)), ('ppm_max', max(ratios))]}
    assert max(errors.values()) <= 1e-12, 'Independent normal bounds differ'
    lo, hi = Decimal(str(capital['ppm_min'])), Decimal(str(capital['ppm_max']))
    for cap, premium in zip(raw.sum_insured_original, raw.written_premium_audit_only):
        if not math.isfinite(cap) or cap <= 0:
            expected.append(np.nan)
            continue
        value = Decimal(str(cap))
        if value > Decimal(10000000):
            if not math.isfinite(premium):
                expected.append(np.nan)
                continue
            ratio = Decimal(1000)*Decimal(str(premium))/value
            if ratio < lo and lo <= ratio*1000 <= hi:
                value /= 1000
            else:
                expected.append(np.nan)
                continue
        expected.append(math.log(float(value)))
    actual = connected['periods'].x_log_sum_insured.to_numpy(float)
    expected = np.array(expected, float)
    assert np.array_equal(np.isnan(actual), np.isnan(expected)), 'Independent capital correction decisions differ'
    finite = np.isfinite(expected)
    max_log_error = float(np.max(np.abs(actual[finite]-expected[finite]))) if finite.any() else 0.
    assert max_log_error <= 1e-12, 'Independent log capital differs'
    return {'normal_rows': len(ratios), 'min_bound_abs_error': errors['ppm_min'], 'max_bound_abs_error': errors['ppm_max'],
        'log_capital_max_abs_error': max_log_error, 'all_missing_decisions_agree': True,
        'reference': 'Decimal on original capital/premium and math.log; no estimates overwritten'}


def main():
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    assert (ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes().count(('<!-- aporte:'+plan['forum_prior']+' -->').encode()) == 1
    for item in plan['frozen_code']:
        assert ingress.sha(ROOT/item['path']) == item['sha256'], item['path']
    assert ingress.sha(ROOT/plan['input_manifest']['path']) == plan['input_manifest']['sha256']
    manifest = json.loads((ROOT/plan['input_manifest']['path']).read_text(encoding='utf-8'))
    attempt = 1
    while (RUN/f'attempt{attempt}').exists():
        attempt += 1
    out = RUN/f'attempt{attempt}'
    out.mkdir()
    for item in plan['frozen_code']:
        (out/Path(item['path']).name).write_bytes((ROOT/item['path']).read_bytes())
    allowed = {str((ROOT/manifest['metadata']['path']).resolve())}
    allowed.update(str((ROOT/spec['path']).resolve()) for files in manifest['fold_files'].values() for spec in files.values())
    events, forbidden, scope_results = [], [], []
    reader = pq.read_table
    current_scope = [None, 'none']
    def checked_read(path, *args, **kwargs):
        p = Path(path).resolve()
        assert str(p) in allowed, 'Undeclared real data decoder'
        assert kwargs.get('columns') is not None
        events.append({'scope': current_scope[0], 'phase': current_scope[1], 'path': rel(p), 'columns': kwargs['columns']})
        return reader(path, *args, **kwargs)
    def blocked(label):
        def fn(*args, **kwargs):
            forbidden.append(label)
            raise AssertionError('Forbidden during real capital preparation: '+label)
        return fn
    old_work = dict(old_flow.WORK)
    try:
        with ExitStack() as stack:
            methods = [(TweedieRegressor, 'fit'), (TweedieRegressor, 'predict'), (Pipeline, 'fit'), (Pipeline, 'predict'),
                (ColumnTransformer, 'fit_transform'), (SimpleImputer, 'fit'), (StandardScaler, 'fit'), (OneHotEncoder, 'fit'),
                (c0, 'fit_c0_2023'), (c0, 'apply_c0_2023'), (old_flow, 'fit_scope'), (old_flow, 'fit_outer'),
                (old_flow, 'fit_calibrator'), (old_flow, 'predict_scope'), (joblib, 'load'), (pickle, 'load')]
            for owner, name in methods:
                stack.enter_context(patch.object(owner, name, blocked(name)))
            stack.enter_context(patch.object(socket.socket, 'connect', blocked('network')))
            stack.enter_context(patch.object(pq, 'read_table', checked_read))
            from itertools import combinations
            for excluded in [[i] for i in range(5)]+[list(x) for x in combinations(range(5), 2)]:
                key = 'exclude_'+'_'.join(map(str, excluded))
                folder = out/'scopes'/key
                folder.mkdir(parents=True)
                request = producer.make_request(ROOT, plan['input_manifest'], excluded, 'existing_competition_emerging2023')
                dump(folder/'request.json', request)
                permitted = {manifest['metadata']['path']}
                permitted.update(s[k]['path'] for s in manifest['scopes'][key]['training_files'] for k in ['periods','targets','claims','capital_audit'])
                cap_only = {manifest['metadata']['path']} | {x['path'] for x in request['capital_source_files']}
                original = ingress.read_pinned
                def scoped_reader(root, spec, *args, **kwargs):
                    assert spec['path'] in permitted, 'Protected fold value file opened'
                    if current_scope[1] in ['produce', 'independent_arithmetic']:
                        assert spec['path'] in cap_only, 'Producer read labels or predictors'
                    return original(root, spec, *args, **kwargs)
                with patch.object(ingress, 'read_pinned', scoped_reader):
                    current_scope[:] = [key, 'produce']
                    capital = producer.produce_parameters(ROOT, request, folder/'capital', author='Codex')
                    current_scope[1] = 'connect'
                    connected = producer.connect_scope(ROOT, request, capital)
                    current_scope[1] = 'independent_arithmetic'
                    raw = producer.read_capital_scope(ROOT, request)
                    check = independent_arithmetic(raw, capital, connected)
                pd.testing.assert_series_equal(connected['learning_frame'].T0, connected['targets'].T0_observed_source, check_names=False)
                assert len(connected['periods']) == request['training_rows']
                assert not connected['periods'].fold.isin(excluded).any()
                assert connected['receipt']['normal_population_replayed_against_allowed_capital']
                assert not connected['receipt']['C0_present'] and not connected['receipt']['fit_allowed']
                p = folder/'g4_periods_features.parquet'
                pq.write_table(pa.Table.from_pandas(connected['periods'], preserve_index=False), p)
                ingress.footer_proof(p, list(connected['periods']))
                view = {'path': rel(p), 'sha256': ingress.sha(p), 'rows': len(connected['periods'])}
                dump(folder/'connection_receipt.json', connected['receipt'])
                dump(folder/'independent_arithmetic.json', check)
                row = {'scope': key, 'excluded_folds': excluded, 'training_rows': len(connected['periods']),
                    'normal_rows': check['normal_rows'], 'ppm_min': capital['ppm_min'], 'ppm_max': capital['ppm_max'],
                    'missing_log_capital_rows': int(connected['periods'].x_log_sum_insured.isna().sum()),
                    'parameters': {'path': rel(folder/'capital/capital_parameters.json'), 'sha256': ingress.sha(folder/'capital/capital_parameters.json')},
                    'features': view, 'receipt': rel(folder/'connection_receipt.json'), 'arithmetic': check,
                    'base_features_ready': True, 'model_input_ready': False, 'C0_present': False, 'fit_allowed': False}
                dump(folder/'scope_ready.json', row)
                scope_results.append(row)
        assert not forbidden and dict(old_flow.WORK) == old_work
        assert len(scope_results) == 15 and sum(r['training_rows'] for r in scope_results) == 125800
        dump(out/'reader_events.json', {'events': events, 'forbidden_calls': forbidden, 'guards_installed': [name for _,name in methods]+['network']})
        result = {'id': plan['id'], 'author': 'Codex', 'utc': now(), 'success': True, 'attempt': attempt, 'out': rel(out),
            'scope_results': scope_results, 'real_parameter_artifacts': 15, 'real_feature_views': 15,
            'total_period_copies': sum(r['training_rows'] for r in scope_results), 'unique_building_periods': 12580,
            'all_scope_readers_protected_values_blocked': True, 'all_independent_arithmetic_checks_passed': True,
            'model_fits': 0, 'C0_calls': 0, 'new_predictions': 0, 'new_scores': 0,
            'G4_real_base_input_connection_verified': True, 'G4_real_full_flow_validated': False,
            'B00_preserved': True, '2024_test_closed_for_capital_work': True}
        dump(out/'result.json', result)
        dump(RUN/'prepared_current.json', result)
        print(json.dumps({k:v for k,v in result.items() if k!='scope_results'}, ensure_ascii=True))
        return 0
    except Exception as exc:
        dump(out/'failure.json', {'id': plan['id'], 'utc': now(), 'exception': type(exc).__name__, 'message': str(exc),
            'traceback': traceback.format_exc(), 'completed_scopes': scope_results, 'reader_events': events, 'forbidden_calls': forbidden})
        print(json.dumps({'success': False, 'attempt': attempt, 'exception': type(exc).__name__, 'message': str(exc),
            'failure': rel(out/'failure.json'), 'completed_scopes': len(scope_results)}, ensure_ascii=True))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
