"""Ejercita el selector real usado por el runner, sin entrenar ni aprobar una matriz F0."""
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

import clean_data as c
sys.path.insert(0, str(c.ROOT / 'Preparación/src'))
import pandas as pd
import pyarrow.parquet as pq
from iaa_lab.data import feature_frames
from iaa_lab.predictor_guard import VERSION, assert_allowed_predictors, exclusion_reason


def main(out):
    if (out / 'manifest.json').exists():
        manifest = json.loads((out / 'manifest.json').read_text('utf-8'))
        assert all(c.digest(out / e['path']) == e['sha256'] for e in manifest['files'])
        print(json.dumps({'status':'closed_verified_run_manifest_intact_no_rewrite'})); return
    checks = []
    def check(name, condition):
        checks.append({'check': name, 'passed': bool(condition)})
        if not condition:
            raise AssertionError(name)
    report = ET.parse(out / 'predictor_guard_pytest.xml').getroot()
    suites = [report] if report.tag == 'testsuite' else list(report.iter('testsuite'))
    check('Targeted core tests passed, no failures/errors', sum(int(x.get('tests',0)) for x in suites) >= 12 and all(int(x.get('errors',0)) == int(x.get('failures',0)) == 0 for x in suites))
    cat = json.loads((out / 'dataset_catalog.json').read_text('utf-8'))
    old = json.loads((out / 'evidence/parent_catalog.json').read_text('utf-8'))
    config = {'id_column': 'row_id', 'target_column': '__T0_not_materialized__',
              'split': {'group_column':'policy_id', 'time_column':'period_start'}}
    inventories = []
    for line in ['motor','buildings','contents']:
        names = ['policies_' + line, 'test_' + line]
        tables = [pq.read_table(c.ROOT / cat[name]['workspace_relative_path']) for name in names]
        # Include positively marked rows as well as unmarked rows in each real-data probe.
        frames = []
        for table in tables:
            positions = list(range(min(300, table.num_rows)))
            flags = table['audit_ren00'].to_pylist()
            positions += [i for i,v in enumerate(flags) if v][:30]
            positions = sorted(set(positions))
            frames.append(table.take(positions).to_pandas())
        source_train, source_test = frames
        check(line + ': positive and negative audit flags present in source probes', source_train.audit_ren00.any() and source_test.audit_ren00.any() and not source_train.audit_ren00.all() and not source_test.audit_ren00.all())
        x, xt = feature_frames(source_train, source_test, config)
        check(line + ': real selector excludes renewal_decision and audit namespace in both matrices', not any(exclusion_reason(col) for frame in [x,xt] for col in frame.columns))
        check(line + ': train/test screened names agree, no rows filtered', list(x) == list(xt) and len(x) == len(source_train) and len(xt) == len(source_test))
        # Presence, values and test availability of outcome/audit fields must not affect inputs.
        poison_train = source_train.copy(); poison_test = source_test.copy()
        poison_train['renewal_decision'] = 'OUTCOME_MUST_NOT_ENTER'
        poison_test['renewal_decision'] = 'UNKNOWN_TEST_OUTCOME'
        poison_train['audit_ren00'] = ~poison_train.audit_ren00
        poison_test['audit_ren00'] = ~poison_test.audit_ren00
        poison_train['previous_renewal_decision'] = 'DERIVED_OUTCOME'
        poison_test['previous_renewal_decision'] = 'DERIVED_OUTCOME'
        poison_train['audit_ren00_extra_probe'] = 'AUDIT_METADATA'
        poison_test['audit_ren00_extra_probe'] = 'AUDIT_METADATA'
        px, pt = feature_frames(poison_train, poison_test, config)
        pd.testing.assert_frame_equal(x, px); pd.testing.assert_frame_equal(xt, pt)
        check(line + ': injected decisions and audit values cannot alter selected data', True)
        bx, bt = feature_frames(source_train.drop(columns=['audit_ren00']), source_test.drop(columns=['audit_ren00']), config)
        pd.testing.assert_frame_equal(x,bx); pd.testing.assert_frame_equal(xt,bt)
        check(line + ': adding REN00 has exactly zero effect on selected predictor values', True)
        for label, table in zip(names, tables):
            roles = {f.name: (f.metadata or {}).get(b'role',b'').decode('utf-8') for f in table.schema}
            assert_allowed_predictors(x.columns if label.startswith('policies_') else xt.columns, roles)
            blocked = {f.name: exclusion_reason(f.name, roles) for f in table.schema if exclusion_reason(f.name, roles)}
            expected = {'audit_ren00', 'renewal_decision'} if label.startswith('policies_') else {'audit_ren00'}
            check(label + ': schema-wide blocked fields explicit, not dependent on sampled values', set(blocked) == expected)
            inventories.append({'table': label, 'source_sha256': cat[label]['sha256'], 'blocked_fields': blocked,
                'screened_candidate_columns': list(x.columns if label.startswith('policies_') else xt.columns),
                'status': 'exclusion_control_only_not_approved_F0', 'F0_availability_contract_complete': False,
                'note': 'No T0, fitting or estimator approval; schema names test outcome/audit exclusion only.'})
        for forbidden in ['renewal_decision','audit_ren00','previous_renewal_decision','audit_future_column']:
            try:
                assert_allowed_predictors(['exposure',forbidden])
            except ValueError:
                failed_closed = True
            else:
                failed_closed = False
            check(line + ': explicit request for forbidden predictor fails: ' + forbidden, failed_closed)
    core = c.ROOT / 'Preparación/src/iaa_lab/data.py'
    runner = c.ROOT / 'Preparación/src/iaa_lab/runner.py'
    check('Existing runner consumes guarded feature_frames', 'X, X_test = feature_frames(train, test, config)' in runner.read_text('utf-8'))
    check('Core selector calls guard before returning matrices', 'select_predictor_columns(train.columns, excluded)' in core.read_text('utf-8') and 'assert_allowed_predictors(frame.columns)' in core.read_text('utf-8'))
    c.dump(out / 'predictor_schema_inventory.json', inventories)
    result = {'status':'passed_actual_core_selector_verification', 'passed':len(checks), 'failed':0, 'checks':checks,
        'guard_version':VERSION, 'core_data_sha256':c.digest(core),
        'guard_sha256':c.digest(c.ROOT/'Preparación/src/iaa_lab/predictor_guard.py'), 'runner_sha256':c.digest(runner),
        'targeted_tests':sum(int(x.get('tests',0)) for x in suites), 'models_trained':False,
        'F0_availability_contract_complete':False, 'operational_T0_materialized':False, 'independent_validation':False}
    c.dump(out / 'predictor_exclusion_verification.json',result)
    print(json.dumps({'status':result['status'],'passed':len(checks),'targeted_tests':result['targeted_tests'],'models_trained':False}))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
