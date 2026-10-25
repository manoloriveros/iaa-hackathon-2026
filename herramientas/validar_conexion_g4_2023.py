"""Valida conexión nueva sin aprendizaje, incluso con fixtures; guarda intentos."""
from pathlib import Path
from datetime import datetime, timezone
from contextlib import ExitStack
from unittest.mock import patch
import json
import pickle
import socket
import sys
import traceback
ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(REPO/'src'))
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
sys.path.insert(0, str(REPO/'herramientas'))
import joblib
import pyarrow.parquet as pq
from sklearn.linear_model import TweedieRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from semana2 import conexion_g4_2023 as bridge, entradas_g4_2023 as ingress
from semana2 import c0_estricto2023 as c0, flujo_g4_sintetico2023 as old_flow
from probar_conexion_g4_2023 import verify

PLAN = REPO/'registro/semana2_g4_conexion_plan_v1.json'
RUN = REPO/'privado/semana2/conexion_g4_2023/contrato_20261024_v1'
rel = lambda p: p.relative_to(ROOT).as_posix()
now = lambda: datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    assert (ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes().count(('<!-- aporte:'+plan['forum_prior']+' -->').encode()) == 1
    for item in plan['frozen_code']:
        assert ingress.sha(ROOT/item['path']) == item['sha256'], item['path']
    attempt = 1
    while (RUN/f'attempt{attempt}').exists():
        attempt += 1
    out = RUN/f'attempt{attempt}'
    out.mkdir()
    for item in plan['frozen_code']:
        (out/Path(item['path']).name).write_bytes((ROOT/item['path']).read_bytes())
    forbidden, decoded = [], []
    def blocked(label):
        def fail(*args, **kwargs):
            forbidden.append(label)
            raise AssertionError('Prohibited during connection validation: '+label)
        return fail
    actual_read = pq.read_table
    def synthetic_only(path, *args, **kwargs):
        p = Path(path).resolve()
        assert p.is_relative_to(out), 'Contest or undeclared data decoder invoked'
        assert kwargs.get('columns') is not None, 'Explicit column projection required'
        decoded.append({'path': rel(p), 'columns': kwargs['columns']})
        return actual_read(path, *args, **kwargs)
    unchanged_work = dict(old_flow.WORK)
    try:
        with ExitStack() as stack:
            methods = [(TweedieRegressor, 'fit'), (TweedieRegressor, 'predict'), (Pipeline, 'fit'),
                (Pipeline, 'predict'), (ColumnTransformer, 'fit_transform'), (SimpleImputer, 'fit'),
                (StandardScaler, 'fit'), (OneHotEncoder, 'fit'), (c0, 'fit_c0_2023'),
                (c0, 'apply_c0_2023'), (old_flow, 'fit_scope'), (old_flow, 'fit_outer'),
                (old_flow, 'fit_calibrator'), (old_flow, 'predict_scope'), (joblib, 'load'), (pickle, 'load')]
            for owner, name in methods:
                stack.enter_context(patch.object(owner, name, blocked(name)))
            stack.enter_context(patch.object(socket.socket, 'connect', blocked('network')))
            stack.enter_context(patch.object(pq, 'read_table', synthetic_only))
            requests = {}
            from itertools import combinations
            for excluded in [[i] for i in range(5)]+[list(x) for x in combinations(range(5), 2)]:
                key = 'exclude_'+'_'.join(map(str, excluded))
                q = bridge.make_request(ROOT, plan['prepared_input_manifest'], excluded, 'existing_competition_emerging2023')
                requests[key] = q
                dump(out/'real_requests'/f'{key}.json', q)
                dump(out/'capital_requirements'/f'{key}.json', bridge.capital_template(q))
            validation = verify(ROOT, out/'generated_fixture', requests)
        assert not forbidden and dict(old_flow.WORK) == unchanged_work
        dump(out/'validation.json', {**validation, 'author': 'Codex', 'utc': now(), 'attempt': attempt,
            'frozen_plan': rel(PLAN), 'forbidden_calls': forbidden, 'decoder_events': decoded,
            'guards_installed': [name for _, name in methods]+['network'], 'old_synthetic_work_unchanged': True})
        result = {'id': plan['id'], 'author': 'Codex', 'utc': now(), 'success': True,
            'attempt': attempt, 'out': rel(out), 'contract_checks': len(validation['checks']),
            'synthetic_scope_connections': validation['synthetic_scope_connections'],
            'real_scope_requests_prepared': len(requests), 'real_missing_capital_blocks': validation['real_missing_parameter_blocks'],
            'real_row_values_decoded': 0, 'model_fits_including_synthetic': 0, 'C0_calls_including_synthetic': 0,
            'new_inferences': 0, 'new_scores': 0, 'real_capital_parameters': 0, 'real_capital_application': False,
            'G4_real_full_flow_validated': False, 'B00_preserved': True, '2024_test_closed': True}
        dump(out/'result.json', result)
        dump(RUN/'validated_current.json', result)
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except Exception as exc:
        dump(out/'failure.json', {'id': plan['id'], 'utc': now(), 'exception': type(exc).__name__,
            'message': str(exc), 'traceback': traceback.format_exc(), 'decoder_events': decoded,
            'forbidden_calls': forbidden, 'old_synthetic_work': dict(old_flow.WORK)})
        print(json.dumps({'success': False, 'attempt': attempt, 'failure': rel(out/'failure.json'),
                          'exception': type(exc).__name__, 'message': str(exc)}, ensure_ascii=True))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
