"""Conciliación de recibos de la síntesis, sin recalcular diagnósticos."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'Hackaton/Repositorio_IAA2026'
RUN = REPO / 'privado/semana2/desarrollo2023/b20_sintesis_20261024_v1'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    output = RUN / 'verification.json'
    assert not output.exists(), 'Recibo existente, no repetir conciliación.'
    plan = read(RUN / 'plan_snapshot.json')
    report = read(RUN / 'report.json')
    checks = []

    def check(name, value):
        checks.append({'name': name, 'pass': bool(value)})

    frozen = {}
    for item in plan['frozen_sources']:
        path, snap = ROOT / item['path'], ROOT / item['snapshot']
        check('SHA source ' + item['path'], sha(path) == item['sha256'])
        check('SHA snapshot ' + item['path'], sha(snap) == item['sha256'])
        check('Only aggregate document ' + item['path'], path.suffix in ('.md', '.json')
              and '2024' not in item['path'].lower() and 'test' not in item['path'].lower())
        frozen[item['path']] = snap
    load = lambda path: read(frozen[path])
    indices = {key: load(path) for key, path in plan['indices'].items()}
    pointer = lambda d: load(d['path'] if isinstance(d, dict) else d)
    receipts = []
    for label, idx in indices.items():
        for key in ['report', 'verification', 'fixtures', 'decision_journal', 'manifest',
                    'readout', 'assessment', 'readout_reconciliation', 'focused_interpretation_receipt']:
            if key not in idx:
                continue
            item = idx[key]
            path = item['path'] if isinstance(item, dict) else item
            digest = item['sha256'] if isinstance(item, dict) else idx.get(key + '_sha256')
            if digest:
                check('Authoritative pointer ' + label + '/' + key, sha(frozen[path]) == digest)
        v = pointer(idx['verification'])
        check('Final receipt ' + label, v['failed'] == 0 and v['passed'] > 0)
        receipts.append({'diagnostic': label, 'passed': v['passed'], 'failed': v['failed'],
                         'path': idx['verification']['path'], 'not_rerun': True})
        if label != 'ridge':
            closure = load(idx['run'] + '/closure_verification.json')
            check('Stored closure ' + label, closure['failed'] == 0 and closure['passed'] > 0)
        if 'fixtures' in idx:
            check('Stored adversaries ' + label, pointer(idx['fixtures'])['failed'] == 0)
    ridge, attr, cont, band = (indices[x] for x in ['ridge', 'attribution', 'contraction', 'calibration'])
    a = {x['reference']: x for x in attr['summary']}
    cr, br, b = pointer(cont['readout']), pointer(band['readout']), pointer(band['report'])
    close = lambda x, y: math.isclose(x, y, abs_tol=1e-7, rel_tol=1e-10)
    for pair in ridge['pairs']:
        ref = pair['reference']
        x = a[ref]
        check('Same delta ' + ref, close(pair['delta_D2'], x['all']['delta_own_null']))
        check('Same removal ' + ref, close(pair['delta_after_removal'], x['remaining']['delta_own_null']))
        check('Gain partition ' + ref, close(x['all']['gain'], x['selected31']['gain'] + x['remaining']['gain']))
        check('Rows partition ' + ref, x['all']['rows'] == x['selected31']['rows'] + x['remaining']['rows'] == 50094)
        check('Groups partition ' + ref, x['all']['groups'] == x['selected31']['groups'] + x['remaining']['groups'] == 30869)
        check('Sign and positive denominator ' + ref, x['all']['gain'] > 0 > x['remaining']['gain']
              and x['all']['null_deviance'] > 0 and x['remaining']['null_deviance'] > 0)
    check('Corrected attribution receipt used', attr['verification']['path'].endswith('/verification_corrected.json'))
    check('Fixed groups shared gain', close(cr['gain_attribution']['fixed_group_saved_gain'], a['W2-B19']['fixed_B19_12']['gain']))
    check('Global gain shared', close(cr['gain_attribution']['saved_global_deviance_gain_B20'], a['W2-B19']['all']['gain']))
    global_level = next(x for x in cr['level_summaries'] if x['dimension'] == 'global')
    check('Shared observed level', close(global_level['observed_T0'], b['total_observed']))
    check('Shared expected B20', close(global_level['B20_observed_bridge_total'], b['total_expected_B20']))
    check('Shared expected B19', close(global_level['B19_observed_bridge_total'], b['total_expected_B19']))
    check('Same support', b['heldout_rows'] == 50094 and b['groups'] == 30869)
    check('A/E from totals', close(b['global_AE_B20'], b['total_observed']/b['total_expected_B20'])
          and close(b['global_AE_B19'], b['total_observed']/b['total_expected_B19']))
    check('Contraction not coordinatewise', cr['norm_pairs'] == cr['joint_norm_contracts'] == 15
          and cr['pairs_with_growing_coordinates'] == 14 and cr['growing_coordinates_across_pairs'] == 33)
    cases = cr['cases_no_private_ids']
    check('Same coverage opposite totals', close(cases[1]['delta_coverage'], cases[2]['delta_coverage'])
          and cases[1]['delta_log_rate'] > 0 > cases[2]['delta_log_rate'])
    check('Fixed sample not representative', cr['fixed_group_selection_not_representative'])
    counter = load('Hackaton/Repositorio_IAA2026/registro/semana2_contadores_propios_actual.json')
    check('Counter 195/285 unchanged', counter['cumulative_price_base_fits'] == 195
          and counter['cumulative_closed_form_constants'] == 285)
    check('Catalog and reference', len(ridge['models_consulted']) == 21 and ridge['reference'] == 'W2-B00' and not ridge['promotion'])
    policy = load('Hackaton/Repositorio_IAA2026/registro/semana2_politica_seleccion_v1.json')
    check('Policy margin and interval retained', policy['metric']['delta_min'] == .0005
          and close(policy['confirmation']['two_sided_interval_coverage'], .9916666666666667))
    check('No new work or opening', all(report[k] == 0 for k in ['new_fits', 'new_inference', 'new_bootstrap', 'new_recipes'])
          and report['2024_test_closed'] and not report['ledger_read'] and not report['promotion'])
    check('Exposure and independence accurate', report['prior_external2024_header_exposure_disclosed']
          and not report['complete_blindness_claim_allowed'] and not report['professional_independent_validation'])
    check('Nine decisions and six gaps', len(report['decisions']) == 9 and len(report['evidence_gaps']) == 6)
    doc = (REPO / 'docs/archivo/semana2/SINTESIS_B20_Y_SIGUIENTE_PASO_2023.md').read_text(encoding='utf-8')
    es = lambda v: f'{v:.3f}'.replace('.', ',')
    for line, title in [('motor', 'Autos'), ('buildings', 'Edificios'), ('contents', 'Contenidos')]:
        check('Band values in document ' + line, '| ' + title + ' | ' + ' | '.join(
            es(x['B20_AE']) for x in br['rows'] if x['line'] == line) + ' |' in doc)
    check('Shared source snapshot all present', len(frozen) == report['source_count'] == 44)
    result = {'id': report['id'], 'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
              'checker_sha256': sha(Path(__file__)), 'passed': sum(x['pass'] for x in checks),
              'failed': sum(not x['pass'] for x in checks), 'checks': checks, 'stored_receipts': receipts,
              'no_original_suites_repeated': True, 'new_fits': 0, 'new_inference': 0, 'new_bootstrap': 0,
              'scope': 'Aggregate2023 JSON/Markdown only; no OOF/models/raw-data/2024/test/ledger.',
              'professional_independent_validation': False}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'failed': result['failed'], 'new_fits': 0, 'new_inference': 0}))
    return bool(result['failed'])


if __name__ == '__main__':
    raise SystemExit(main())
