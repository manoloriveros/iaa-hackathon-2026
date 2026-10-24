"""Comprueba integración y explicaciones de coeficientes, sin ajuste o bootstrap."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import joblib
import numpy as np

read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    run = REPO/'privado/semana2/desarrollo2023/ridge20_20261024_v1'
    output = run/'integration_verification.json'
    assert not output.exists(), 'Conciliación ya guardada; no repetir sin cambios'
    routes = read(ROOT/'RUTAS_PROYECTO.json')
    index = read(ROOT/routes['week_2_development_index'])
    report = read(run/'report.json')
    plan = read(run/'plan_snapshot.json')
    checks = []
    def check(name, value):
        checks.append({'name': name, 'pass': bool(value)})
    check('Samecurrentandridgeindex', index == read(ROOT/routes['week_2_ridge_index']))
    for name in ['report', 'producer', 'plan', 'oof', 'manifest', 'decision_journal']:
        p = ROOT/index[name]
        check('CurrentpointerSHA '+name, p.exists() and sha(p) == index[name+'_sha256'])
    for name in ['verification', 'fixtures']:
        obj = index[name]
        check('Verificationpointer '+name, sha(ROOT/obj['path']) == obj['sha256'] and read(ROOT/obj['path'])['failed'] == 0)
    check('Developmentroutes', routes['week_2_development_plan'] == index['plan'] and routes['week_2_development_oof'] == index['oof'] and routes['week_2_development_report'] == index['documentation'])
    check('Historicalsnapshotpreserved', (ROOT/routes['week_2_development_v8_snapshot']).read_bytes() == (run/'main_index_before_integration.json').read_bytes())
    counter = read(ROOT/routes['week_2_own_fit_counters'])
    check('Owncounter195285', counter['cumulative_price_base_fits'] == 195 and counter['cumulative_closed_form_constants'] == 285)
    check('Exactlyonceincrement', sum(x['id'] == plan['id'] for x in counter['increments']) == 1)
    check('Counterindependentsum', counter['baseline']['price_base_fits']+sum(x['price_GLM_fits'] for x in counter['increments']) == 195)
    check('Threelevelsoffitcounts', report['new_price_base_fits'] == 15 and index['catalog_lineage_price_base_fits'] == 120 and index['cumulative_price_base_fits'] == 195)
    n = read(ROOT/routes['week_2_night_index'])
    check('Nightlatestandcount', n['latest_completed_unit']['id'] == plan['id'] and len(n['completed_units']) == 10)
    check('Nightnextdoesnotrepeatfit', n['current_unit'] is None and n['no_retraining_or_suite_repetition_for_completed_ridge20'] and 'no newfit' in n['next_unit'])
    check('Nightwindowunchanged', n['window_end'] == '2026-10-24T07:00:00-05:00' and n['frequency'] == 'hourly_at_minute_zero')
    check('Kaggleincidentpreserved', n['submission_platform_incident']['topic_id'] == 752144)
    # Read own automation settings only; never change the scheduler from this checker.
    ap = Path('C:/Users/manol/.codex/automations')/n['automation_id']/'automation.toml'
    auto = tomllib.loads(ap.read_text(encoding='utf-8'))
    check('Heartbeatstillactive', auto['status'] == 'ACTIVE' and auto['kind'] == 'heartbeat')
    check('Heartbeatwindowunchanged', auto['rrule'] == 'RRULE:FREQ=HOURLY;INTERVAL=1;BYMINUTE=0;BYSECOND=0;UNTIL=20261024T120000Z')
    check('Heartbeatfollowscurrentindex', 'índice de continuidad nocturna' in auto['prompt'] and '752144' in auto['prompt'])
    state = read(ROOT/routes['state'])['semana2_glm_ridge_coberturas2023_20261024']
    check('Stateconsistent', state['own_cumulative_price_fits'] == 195 and not state['promotion'] and not state['confirmation_2024_open'])
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        text = (ROOT/'Preparación'/name).read_text(encoding='utf-8-sig')
        check('Ownmemoryentry '+name, text.count('## S2-GLM-RIDGE-COBERTURAS2023-v1-20261024:') == 1)
    doc = (ROOT/index['documentation']).read_text(encoding='utf-8')
    for row in report['summary']:
        check('Reporttable '+row['model_id'], f"| {row['model_id']} | {row['D2']:.6f} |" in doc)
    forum = (ROOT/routes['week_2_forum']).read_text(encoding='utf-8-sig')
    for identifier in [index['forum_prior'], index['forum_result']]:
        check('Ownforumpost '+identifier, forum.count('<!-- aporte:'+identifier+' -->') == 1)
    co = read(run/'diagnostics/coefficient_stability.json')['rows']
    check('Coefficients15cells', len(co) == 15)
    for row in co:
        line, fold = row['line'], row['fold']
        for mid, node in [('B19', ROOT/plan['input_run']/'models'/f'W2-B19_{line}_fold{fold}'),
                          ('B20', run/'models'/f'{line}_fold{fold}')]:
            b = joblib.load(node/'bundle.joblib')
            tr, est = b['transformer'], b['estimator']
            numeric = list(tr.transformers_[0][2])
            scale = tr.named_transformers_['numeric']['scale'].scale_
            j = numeric.index('x_new_business')
            business = np.exp(est.coef_[j]/scale[j])
            if line == 'motor':
                k = list(tr.get_feature_names_out()).index('categorical__x_cover_type_third_party_only')
                coverage = np.exp(est.coef_[k])
            else:
                k = numeric.index('x_accidental_damage_cover')
                coverage = np.exp(est.coef_[k]/scale[k])
            check('Rawscalecontrast '+mid+line+str(fold), np.allclose([business, coverage], [row[mid+'_newbusiness_ratio'], row[mid+'_coverage_ratio']], rtol=1e-12, atol=1e-12))
    check('Referenceandallalternativesretained', index['reference'] == 'W2-B00' and len(index['models_consulted']) == 21 and not index['promotion'] and index['alternatives_preserved'])
    check('No2024testorsubmission', not index['confirmation_2024_open'] and report['submissions'] == 0 and 'closed' in report['scope_2024_test'])
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
              'passed': sum(x['pass'] for x in checks), 'failed': sum(not x['pass'] for x in checks),
              'checks': checks, 'new_fits': 0, 'bootstrap_repeated': False,
              'professional_independent_validation': False}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'failed': result['failed'], 'failures': [x for x in checks if not x['pass']]}))
    return 1 if result['failed'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
