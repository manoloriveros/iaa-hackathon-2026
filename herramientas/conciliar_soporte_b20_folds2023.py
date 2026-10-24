"""Cierre del inventario guardado; no reabre el diseño ni otras unidades."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[3]
REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/b20_soporte_folds_20261024_v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    output=RUN/'closure_verification.json'
    assert not output.exists(),'Cierre existente.'
    ip=REPO/'registro/semana2_b20_soporte_folds_actual.json'
    idx,p=read(ip),read(RUN/'plan_snapshot.json');checks=[]
    def check(name,value):checks.append({'name':name,'pass':bool(value)})
    for key in ['report','verification','fold_cells','pooled_cells','outer_training_proxy','decision_journal','evidence_gaps','manifest']:
        x=idx[key];check('IndexSHA '+key,sha(ROOT/x['path'])==x['sha256'])
    check('Plan/documentSHA',sha(ROOT/idx['plan'])==idx['plan_sha256'] and sha(ROOT/idx['documentation'])==idx['documentation_sha256'])
    manifest=read(RUN/'manifest.json')
    check('OutputSHA',all(sha(ROOT/x['path'])==x['sha256'] for x in manifest['outputs']))
    check('CodeSnapshotsSHA',all(sha(ROOT/x['path'])==x['sha256'] for x in manifest['code_snapshots']))
    check('FrozenSourcesSHA',all(sha(ROOT/x['path'])==sha(ROOT/x['snapshot'])==x['sha256'] for x in p['frozen_sources']))
    verification=read(RUN/'verification.json')
    check('911specificchecks',verification['passed']==911 and verification['failed']==0)
    report=read(RUN/'report.json')
    check('Failedconditionretained',idx['support_gate']==report['support_gate']=='failed' and idx['fold_gate_failed']==5
          and idx['failed_folds']==[1,2,3,4] and not idx['fit_authorized'] and not idx['can_execute'])
    check('Noinnerclaim',not idx['inner_oof_support_established'] and all(not x['proves_inner_gate'] for x in read(RUN/'outer_training_proxy.json')))
    check('Nochangeorexclusion',not idx['thresholds_relaxed'] and all(idx[x]==0 for x in
        ['new_fits','new_inference','parameters_estimated','new_bootstrap','new_recipes','claims_or_groups_excluded']))
    check('Eightdecisions',len(read(RUN/'decision_journal.json')['decisions'])==8)
    check('Closed2024testandroles',idx['2024_test_closed'] and not idx['ledger_read'] and not idx['promotion']
        and idx['reference']=='W2-B00' and idx['all_alternatives_preserved'] and not idx['complete_blindness_claim_allowed']
        and not idx['professional_independent_validation'])
    routes=read(ROOT/'RUTAS_PROYECTO.json')
    check('Routes',routes['week_2_b20_fold_support_index']==ip.relative_to(ROOT).as_posix()
        and routes['week_2_b20_fold_support_report']==idx['documentation'] and routes['week_2_b20_fold_support_plan']==idx['plan'])
    night=read(REPO/'registro/semana2_continuidad_nocturna.json')
    own=[x for x in night['completed_units'] if x['id']==idx['id']]
    check('Owncompleteonce',len(own)==1 and own[0]['support_gate']=='failed' and own[0]['verification']==idx['verification'])
    check('Nightreceiptpointer',night['latest_b20_fold_support_index']==routes['week_2_b20_fold_support_index']
        and night['no_repetition_for_completed_b20_fold_support'])
    reg=read(RUN/'registration_receipt.json')
    check('Otherunitpreserved',reg['preserved_other_current_unit'])
    check('Windowandfrequency',night['window_end']==reg['window_end']=='2026-10-24T07:00:00-05:00'
        and night['frequency']==reg['frequency']=='hourly_at_minute_zero')
    check('Incidentpreserved',night['submission_platform_incident']['topic_id']==752144)
    forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_text(encoding='utf-8-sig')
    for key in ['forum_prior','forum_result']:check('Ownpost '+key,forum.count('<!-- aporte:'+idx[key]+' -->')==1)
    for filename in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
        text=(ROOT/'Preparación'/filename).read_text(encoding='utf-8-sig')
        check('Ownsection '+filename,text.count('## '+idx['id']+':')==1)
    state=read(ROOT/'Preparación/ESTADO_PROYECTO.json')['semana2_b20_soporte_folds2023_20261024']
    check('Ownstate',state['fold_gate_failed']==5 and not state['fit_authorized'] and state['2024_test_closed']
        and state['claims_or_groups_excluded']==0 and not state['thresholds_relaxed'])
    doc=ROOT/idx['documentation'];text=doc.read_text(encoding='utf-8')
    check('Locallinks',all((doc.parent/x).resolve().is_file() for x in re.findall(r'\]\(([^)]+)\)',text)))
    for fold,band in [(1,1),(2,1),(3,1),(4,1),(4,5)]:
        c=next(x for x in read(RUN/'fold_cell_audit.json') if x['line']=='buildings' and x['fold']==fold and x['band']==band)
        percent=f"{100*c['largest_group_cost_share']:.2f}".replace('.',',')
        equivalent=f"{c['cost_concentration_equivalent_groups']:.2f}".replace('.',',')
        check('Failedcelltext '+str(fold)+'/'+str(band),f'| {fold} | {band} |' in text
              and percent+'%' in text and equivalent in text)
    result={'id':idx['id'],'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
        'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,
        'current_unit_read_only':(night.get('current_unit') or {}).get('id'),'other_units_not_modified':True,
        'support_gate':'failed','new_fits':0,'new_inference':0,'claims_or_groups_excluded':0,
        'checker_sha256':sha(Path(__file__)),'professional_independent_validation':False}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not result['failed']:
        idx['closure_verification']={'path':output.relative_to(ROOT).as_posix(),'sha256':sha(output),'passed':result['passed'],'failed':0}
        ip.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['passed','failed','support_gate','new_fits']}))
    return bool(result['failed'])


if __name__=='__main__':
    raise SystemExit(main())
