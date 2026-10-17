"""Complementa CAL00 con cambios de dirección/vehículo, sin releer o modificar datos activos."""
from pathlib import Path
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'Hackaton/Semana 1/Limpieza'))
import clean_data as c
import numpy as np
import pandas as pd


def main(out):
    assert not (out / 'manifest.json').exists(), 'Closed immutable run.'
    initial = out / 'evidence/initial_diagnostic_snapshot'
    initial.mkdir(exist_ok=False)
    for name in ['summary.json', 'cases.json', 'tables/case_index.csv', 'tables/case_index.parquet',
                 'tables/case_policy_histories.csv', 'tables/case_policy_histories.parquet',
                 'tables/case_claim_histories.csv', 'tables/case_claim_histories.parquet']:
        p = out / name
        shutil.copy2(p, initial / p.name)
    g = pd.read_parquet(out / 'tables/gap_cohort.parquet')
    h = pd.read_parquet(out / 'tables/all_affected_policy_histories.parquet')
    before = h.set_index('row_id').loc[g.previous_row_id].reset_index()
    after = h.set_index('row_id').loc[g.row_id].reset_index()
    risk = g[['line', 'policy_id', 'previous_row_id', 'row_id', 'previous_address_id', 'address_id',
              'previous_renewal_decision', 'same_customer', 'same_address']].copy()
    motor = g.line.eq('motor')
    for field in ['make_model', 'cover_type', 'vehicle_value_group']:
        risk['same_' + field] = pd.Series(pd.NA, index=g.index, dtype='boolean')
        equality = before[field].eq(after[field]).to_numpy()
        risk.loc[motor, 'same_' + field] = equality[motor]
    risk.to_parquet(out / 'tables/risk_context_comparison.parquet', index=False)
    counts = risk.groupby(['line', 'same_address', 'previous_renewal_decision'], dropna=False).size().reset_index(name='policies')
    counts.to_csv(out / 'tables/address_changes_summary.csv', index=False)
    movers = risk.loc[~risk.same_address]
    assert len(movers) == 3153 and movers.line.eq('motor').all()
    assert risk.loc[motor, ['same_make_model', 'same_cover_type', 'same_vehicle_value_group']].all().all()
    cases = json.loads((out / 'cases.json').read_text('utf-8'))
    pid = movers.sort_values('policy_id').iloc[0].policy_id
    assert pid not in {x['case']['policy_id'] for x in cases}
    meta = {'case': len(cases) + 1, 'label': 'Motor: cambio de dirección en la renovación', 'line': 'motor', 'policy_id': pid,
        'interpretation': 'La dirección de residencia cambia entre 2024 y 2025. Cliente, modelo, grupo de valor y tipo de cobertura permanecen iguales en los campos comparados. La continuidad de póliza puede coexistir con un cambio de exposición territorial; no trasladar la dirección 2025 al supuesto día final de 2024.'}
    hp = h.loc[h.policy_id == pid]
    ac = pd.read_parquet(out / 'tables/all_affected_claim_histories.parquet')
    hc = ac.loc[ac.policy_id == pid]
    cases.append({'case': meta, 'policies': json.loads(hp.to_json(orient='records', date_format='iso')),
                  'claims': json.loads(hc.to_json(orient='records', date_format='iso'))})
    c.dump(out / 'cases.json', cases)
    cp = pd.concat([pd.read_parquet(out / 'tables/case_policy_histories.parquet'), hp], ignore_index=True)
    cc = pd.concat([pd.read_parquet(out / 'tables/case_claim_histories.parquet'), hc], ignore_index=True)
    ix = pd.DataFrame([x['case'] for x in cases])
    for frame, name in [(cp, 'case_policy_histories'), (cc, 'case_claim_histories'), (ix, 'case_index')]:
        frame.to_parquet(out / 'tables' / (name + '.parquet'), index=False)
        frame.to_csv(out / 'tables' / (name + '.csv'), index=False)
    summary = json.loads((out / 'summary.json').read_text('utf-8'))
    summary.update({'address_changes': len(movers), 'address_changes_renewed': int(movers.previous_renewal_decision.eq('renewed').sum()),
        'address_changes_declined': int(movers.previous_renewal_decision.eq('declined_by_insurer').sum()),
        'motor_same_make_model': int(risk.loc[motor, 'same_make_model'].sum()),
        'motor_same_cover_type': int(risk.loc[motor, 'same_cover_type'].sum()),
        'motor_same_vehicle_value_group': int(risk.loc[motor, 'same_vehicle_value_group'].sum()),
        'case_count': len(cases), 'case_policy_rows': len(cp), 'case_claim_rows': len(cc)})
    c.dump(out / 'summary.json', summary)
    c.dump(out / 'evidence/pre_verification_correction_note.json', {
        'issue': 'An interim prose assumption generalized constant address to motor before full endpoint comparison.',
        'evidence': 'The first computed cohort and summary already record same_address=497092, not 500245.',
        'correction': 'Retain exact cohort evidence; add risk comparison and a moving motor case. Update report, verifier and memory draft before first verification and closure.',
        'original_or_active_data_modified': False, 'initial_diagnostics_preserved': 'evidence/initial_diagnostic_snapshot',
        'source_versions': 'Initial scripts in source_snapshot; scripts actually executed after the correction in source_snapshot/executed.'})
    executed = out / 'source_snapshot/executed'
    executed.mkdir(exist_ok=False)
    for name in ['review_calendar.py', 'add_continuity_context.py', 'render_calendar.py', 'verify_calendar.py', 'verify_report.js', 'record_calendar.py']:
        shutil.copy2(BASE / name, executed / name)
    protected = json.loads((out / 'protected_hashes_before.json').read_text('utf-8'))
    assert all(c.digest(ROOT / p) == sha for p, sha in protected.items())
    print(json.dumps({'cases': len(cases), 'moving_motor_policy': pid, 'address_changes': len(movers), 'unchanged_model_cover_value_motor': int(motor.sum())}))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
