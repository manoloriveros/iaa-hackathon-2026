"""Cierre del diseño y comprobación de que su fallo no habilita entrenamiento."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'Hackaton/Repositorio_IAA2026'
RUN = REPO / 'privado/semana2/desarrollo2023/b20_diseno_contraste_20261024_v1'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    output = RUN / 'closure_verification.json'
    assert not output.exists(), 'No repetir cierre.'
    ip = REPO / 'registro/semana2_b20_contraste_minimo_actual.json'
    idx, plan = read(ip), read(RUN / 'plan_snapshot.json')
    checks = []

    def check(name, value):
        checks.append({'name':name, 'pass':bool(value)})

    for key in ['verification','decision_journal','readiness','terms','scope_graph','manifest']:
        d = idx[key]
        check('Index pointer ' + key, sha(ROOT/d['path']) == d['sha256'])
    check('Plan unchanged', sha(ROOT/idx['plan']) == idx['plan_sha256'] and read(ROOT/idx['plan']) == plan)
    check('Document SHA', sha(ROOT/idx['documentation']) == idx['documentation_sha256'])
    manifest = read(RUN/'manifest.json')
    check('Frozen outputs', all(sha(ROOT/x['path']) == x['sha256'] for x in manifest['outputs']))
    check('Code snapshots', all(sha(ROOT/x['path']) == x['sha256'] for x in manifest['code_snapshots']))
    check('174 checked, no failed', read(RUN/'verification.json')['passed'] == 174 and read(RUN/'verification.json')['failed'] == 0)
    ready = read(RUN/'current_readiness.json')
    check('Failed screen prevents fit', ready['support_screen'] == 'failed_on_existing_screen_no_fit_eligible'
          and not ready['can_execute'] and not ready['fit_authorized'] and ready['parameters_estimated'] == 0)
    check('Index says no execution', idx['support_gate']=='failed' and not idx['can_execute'] and not idx['fit_authorized'])
    check('No new work', all(idx[x] == 0 for x in ['new_fits','new_inference','new_bootstrap','parameters_estimated','new_catalog_recipes']))
    check('Repair preserved', (RUN/'checker_attempt1_failed.py').is_file()
          and not read(RUN/'verification_attempt1_failure.json')['design_or_thresholds_changed']
          and len(read(RUN/'decision_journal.json')['verification_repairs']) == 1)
    frozen = {x['path']:x for x in plan['frozen_sources']}
    for filename in ['semana2_contadores_propios_actual.json','semana2_desarrollo2023_actual.json',
                     'semana2_glm_ridge_actual.json','semana2_politica_seleccion_v1.json']:
        path = 'Hackaton/Repositorio_IAA2026/registro/' + filename
        check('Unchanged ' + filename, sha(ROOT/path) == frozen[path]['sha256'])
    routes = read(ROOT/'RUTAS_PROYECTO.json')
    check('Routes', routes['week_2_b20_minimal_contrast_design_index'] == ip.relative_to(ROOT).as_posix()
          and routes['week_2_b20_minimal_contrast_design_plan'] == idx['plan']
          and routes['week_2_b20_minimal_contrast_design_report'] == idx['documentation'])
    n = read(REPO/'registro/semana2_continuidad_nocturna.json')
    own = [x for x in n['completed_units'] if x['id'] == idx['id']]
    check('Own completion once', len(own) == 1 and own[0]['support_gate']=='failed' and not own[0]['fit_authorized'])
    check('No repeat marker', n['no_repetition_for_completed_b20_minimal_design'])
    check('Night design pointer', n['latest_b20_minimal_contrast_design_index'] == routes['week_2_b20_minimal_contrast_design_index'])
    receipt = read(RUN/'registration_receipt.json')
    check('Other current unit preserved', receipt['preserved_other_current_unit'])
    check('Window preserved', n['window_end'] == receipt['window_end'] == '2026-10-24T07:00:00-05:00'
          and n['frequency'] == receipt['frequency'] == 'hourly_at_minute_zero')
    check('Incident preserved', n['submission_platform_incident']['topic_id'] == 752144)
    forum = (ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_text(encoding='utf-8-sig')
    for key in ['forum_prior','forum_result']:
        check('Own post ' + key, forum.count('<!-- aporte:' + idx[key] + ' -->') == 1)
    for filename in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
        text = (ROOT/'Preparación'/filename).read_text(encoding='utf-8-sig')
        check('Own section ' + filename, text.count('## ' + idx['id'] + ':') == 1)
    state = read(ROOT/'Preparación/ESTADO_PROYECTO.json')['semana2_b20_diseno_contraste2023_20261024']
    check('Own state remains no fit', state['support_gate']=='failed' and not state['fit_authorized']
          and state['2024_test_closed'] and state['parameters_estimated'] == 0)
    doc = ROOT/idx['documentation']
    text = doc.read_text(encoding='utf-8')
    check('Links resolve', all((doc.parent/x).resolve().is_file() for x in re.findall(r'\]\(([^)]+)\)',text)))
    check('Ten decisions retained', len(read(RUN/'decision_journal.json')['decisions']) == 10)
    check('Scope and role', idx['2024_test_closed'] and not idx['ledger_read'] and not idx['promotion']
          and idx['reference']=='W2-B00' and idx['all_alternatives_preserved']
          and not idx['professional_independent_validation'] and not idx['complete_blindness_claim_allowed'])
    result = {'id':idx['id'],'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
              'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,
              'current_unit_read_only':(n.get('current_unit') or {}).get('id'), 'other_units_not_modified':True,
              'support_gate':'failed','new_fits':0,'parameters_estimated':0,'new_inference':0,
              'checker_sha256':sha(Path(__file__)),'professional_independent_validation':False}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not result['failed']:
        idx['closure_verification'] = {'path':output.relative_to(ROOT).as_posix(),'sha256':sha(output),
                                       'passed':result['passed'],'failed':0}
        ip.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['passed','failed','support_gate','new_fits','parameters_estimated']}))
    return bool(result['failed'])


if __name__ == '__main__':
    raise SystemExit(main())
