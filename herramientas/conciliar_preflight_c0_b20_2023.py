"""Cierre de preflight, sin convertir comprobaciones en habilitación de ajuste."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/b20_preflight_c0_20261024_v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    output=RUN/'closure_verification.json';assert not output.exists(),'Cierre existente.'
    ip=REPO/'registro/semana2_b20_preflight_c0_actual.json';idx,p=read(ip),read(RUN/'plan_snapshot.json');checks=[]
    def check(name,value):checks.append({'name':name,'pass':bool(value)})
    for field in ['report','verification','outer_scopes','planned_inner_scope_receipt','unsafe_cache_reuse','dependencies','decision_journal','evidence_gaps','manifest']:
        item=idx[field];check('IndexSHA '+field,sha(ROOT/item['path'])==item['sha256'])
    check('PlanSHA',sha(ROOT/idx['plan'])==idx['plan_sha256'])
    check('DocumentSHA',sha(ROOT/idx['documentation'])==idx['documentation_sha256'])
    manifest=read(RUN/'manifest.json')
    check('OutputSHA',all(sha(ROOT/x['path'])==x['sha256'] for x in manifest['outputs']))
    check('CodeSnapshotsSHA',all(sha(ROOT/x['path'])==x['sha256'] for x in manifest['code_snapshots']))
    check('All66sourcespreserved',len(p['frozen_sources'])==66 and all(sha(ROOT/x['path'])==sha(ROOT/x['snapshot'])==x['sha256'] for x in p['frozen_sources']))
    v=read(RUN/'verification.json');report=read(RUN/'report.json')
    check('384checksand14fixtures',v['passed']==384 and v['failed']==0 and v['metadata_fixture_count']==14 and all(x['pass'] for x in v['metadata_fixtures']))
    check('Fiveoutersandteninners',idx['observed_outer_scopes_reconciled']==5 and idx['planned_inner_scopes_count']==10
        and len(read(ROOT/idx['outer_scopes']['path']))==5 and len(read(ROOT/idx['planned_inner_scope_receipt']['path']))==10)
    check('All20reusesrejected',idx['unsafe_existing_reuse_cases']==20 and all(x['both_existing_reuses_invalid'] for x in read(RUN/'unsafe_cache_reuse.json')))
    check('Proposed60notexecuted',idx['hypothetical_reporting_peril_calls']==60 and report['resource_enumeration']['hypothetical_only'])
    check('Numericcoreandactualpoisoningnotclaimed',not idx['C0_numeric_core_implemented'] and not idx['fitted_object_poisoning_tested'])
    check('Failedsupportkept',idx['support_gate']=='failed' and not idx['fit_authorized'] and not idx['can_execute'] and not idx['thresholds_relaxed'])
    check('Noestimationordeletions',all(idx[k]==0 for k in ['new_fits','new_inference','new_C0_values','parameters_estimated','new_bootstrap','claims_or_groups_removed']))
    check('Nine decisions',len(read(RUN/'decision_journal.json')['decisions'])==9)
    check('Closed scope and roles',idx['2024_test_closed'] and not idx['ledger_read'] and not idx['promotion'] and idx['reference']=='W2-B00'
        and idx['all_alternatives_preserved'] and not idx['professional_independent_validation'] and not idx['complete_blindness_claim_allowed'])
    frozen={x['path']:x for x in p['frozen_sources']}
    for name in ['semana2_contadores_propios_actual.json','semana2_desarrollo2023_actual.json','semana2_glm_ridge_actual.json',
                 'semana2_b20_soporte_folds_actual.json','semana2_b20_contraste_minimo_actual.json','semana2_politica_seleccion_v1.json']:
        path='Hackaton/Repositorio_IAA2026/registro/'+name
        check('Unchanged '+name,sha(ROOT/path)==frozen[path]['sha256'])
    routes=read(ROOT/'RUTAS_PROYECTO.json')
    check('Routes',routes['week_2_b20_C0_preflight_index']==ip.relative_to(ROOT).as_posix()
        and routes['week_2_b20_C0_preflight_report']==idx['documentation'] and routes['week_2_b20_C0_preflight_plan']==idx['plan'])
    n=read(REPO/'registro/semana2_continuidad_nocturna.json');own=[x for x in n['completed_units'] if x['id']==idx['id']]
    check('Completedonce',len(own)==1 and own[0]['support_gate']=='failed' and not own[0]['fit_authorized'] and own[0]['verification']==idx['verification'])
    check('Nightpointerandnorepeat',n['latest_b20_C0_preflight_index']==routes['week_2_b20_C0_preflight_index'] and n['no_repetition_for_completed_b20_C0_preflight'])
    reg=read(RUN/'registration_receipt.json')
    check('Concurrentunitpreserved',reg['preserved_other_current_unit'])
    check('Windowpreserved',n['window_end']==reg['window_end']=='2026-10-24T07:00:00-05:00' and n['frequency']==reg['frequency']=='hourly_at_minute_zero')
    check('Incidentpreserved',n['submission_platform_incident']['topic_id']==752144)
    forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_text(encoding='utf-8-sig')
    for key in ['forum_prior','forum_result']:check('Ownpost '+key,forum.count('<!-- aporte:'+idx[key]+' -->')==1)
    for filename in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
        text=(ROOT/'Preparación'/filename).read_text(encoding='utf-8-sig');check('Ownsection '+filename,text.count('## '+idx['id']+':')==1)
    state=read(ROOT/'Preparación/ESTADO_PROYECTO.json')['semana2_b20_preflight_c02023_20261024']
    check('Ownstate',state['outer_scopes_reconciled']==5 and state['nested_reuse_cases_rejected']==20 and state['support_gate']=='failed'
        and not state['fit_authorized'] and state['2024_test_closed'] and state['new_C0_values']==0)
    doc=ROOT/idx['documentation'];text=doc.read_text(encoding='utf-8')
    check('Locallinksresolve',all((doc.parent/x).resolve().is_file() for x in re.findall(r'\]\(([^)]+)\)',text)))
    check('No mixed-year tables in frozen source allowlist',not any('/observation_link_' in x['path'] or x['path'].endswith('/summary.json') for x in p['frozen_sources']))
    result={'id':idx['id'],'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
        'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,
        'current_unit_read_only':(n.get('current_unit') or {}).get('id'),'other_units_not_modified':True,
        'support_gate':'failed','new_fits':0,'new_inference':0,'new_C0_values':0,
        'checker_sha256':sha(Path(__file__)),'professional_independent_validation':False}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not result['failed']:
        idx['closure_verification']={'path':output.relative_to(ROOT).as_posix(),'sha256':sha(output),'passed':result['passed'],'failed':0}
        ip.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['passed','failed','support_gate','new_fits']}))
    return bool(result['failed'])


if __name__=='__main__':main()
