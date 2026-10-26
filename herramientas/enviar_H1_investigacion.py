"""Un único CSV H1 de investigación; transporte idempotente y recibo público."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import math
import os
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
OUT=R/'privado/semana2/mision017_fase2/entrega_H1_investigacion_20261026_v1'
SLUG='iaa-ai-assisted-hackathon-2026-part-2'
SHA='d9cccc8dbcdd1ae7d12f00b6ce895c83c1d8018a38c1ffc44eb46017f4d42c89'
MESSAGE='Codex H1 observation correction | F3c base Claude | d9cccc8dbcdd1ae7 | research, no formal promotion'
now=lambda:datetime.now(timezone.utc).isoformat()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))


def save(folder,name,data):
    with (folder/name).open('x',encoding='utf8') as f:json.dump(data,f,ensure_ascii=False,indent=2)


def source():
    a=read(OUT/'admission.json');spec=a['CSV'];path=ROOT/spec['path']
    assert a['research_submission_only'] and a['explicit_research_exception'] and not a['formal_promotion']
    assert a['promotion_gates_passed'] is False and a['max_new_submissions']==1
    assert a['submission_code_sha256']==sha(Path(__file__))
    assert sha(path)==spec['sha256']==SHA and path.stat().st_size==spec['bytes'] and spec['rows']==209063
    policy=ROOT/a['policy'];assert sha(policy)==a['policy_sha256']
    dry=read(OUT/'dryrun_receipt.json');assert dry['official_skill_dryrun_all5passed']
    assert dry['CSV']['sha256']==SHA and sha(ROOT/dry['receipt'])==dry['receipt_sha256']
    for p,h in a['source_report_hashes'].items():assert sha(ROOT/p)==h
    return spec,path


def api():
    from kaggle.api.kaggle_api_extended import KaggleApi
    a=KaggleApi();a.authenticate();return a


def matching(rows):
    names={'codex_H1_observation_2025.csv','codex_H1_observation_2025.zip',
           'F3c_H1_solo_prototipo_2025.csv','F3c_H1_solo_prototipo_2025.zip'}
    return [r for r in rows if r.file_name in names or SHA[:16] in (r.description or '') or r.description==MESSAGE]


def limits_dict(value):
    return {k:getattr(value,k) for k in ['num_today','num_total','num_allowed_now','limited_by_total']}


def current_delivery_gate():
    # The newer direct participant priority takes precedence over the archived
    # conditional research admission. Fail closed before authentication or POST.
    path=R/'registro/semana2_control_entregas_codex_actual.json'
    control=read(path)
    assert control['author']=='Codex' and isinstance(control['allow_new_submission'],bool)
    assert sha(ROOT/control['policy'])==control['policy_sha256']
    return control


def send_once(client,folder,spec,path):
    assert not (folder/'submission_started.json').exists(),'Prior start exists: reconcile the same delivery; never blind retry'
    assert not (folder/'public_receipt.json').exists(),'Already processed'
    lim=limits_dict(client.competition_get_submission_limits(SLUG))
    rows=client.competition_submissions(SLUG,page_size=100) or []
    found=matching(rows)
    if found:
        result={'utc':now(),'status':'matching_remote_artifact_reconcile_without_upload',
                'refs':[r.ref for r in found],'limits':lim,'new_submissions':0}
        save(folder,'duplicate_reconciliation_required.json',result);return result
    if lim['num_allowed_now']<1:
        result={'utc':now(),'status':'no_current_quota_no_upload','limits':lim,'new_submissions':0}
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        save(folder,'quota_wait_'+stamp+'.json',result);return result
    # Exclusive durable intent precedes the only API POST, including uncertain failure.
    save(folder,'submission_started.json',{'utc':now(),'CSV':spec,'message':MESSAGE,'limits_before':lim,
                                         'max_new_submissions':1,'research_only':True,'formal_promotion':False})
    try:
        response=client.competition_submit(str(path),MESSAGE,SLUG,quiet=True)
        assert response.ref>0,'No positive submission reference'
        result={'utc':now(),'competition':SLUG,'ref':response.ref,'message':response.message,'CSV':spec,
                'submission_message':MESSAGE,'accepted_for_processing':True,'new_submissions':1,'research_only':True}
        save(folder,'submission_response.json',result);return result
    except Exception as exc:
        save(folder,'submission_uncertain.json',{'utc':now(),'exception_type':type(exc).__name__,
                                               'status_uncertain':True,'next':'Read remote receipt for this exact artifact; never retry POST'})
        raise


def check_remote(client,folder,spec,path):
    if (folder/'public_receipt.json').exists():return read(folder/'public_receipt.json')
    rows=client.competition_submissions(SLUG,page_size=100) or []
    if (folder/'submission_response.json').exists():
        ref=read(folder/'submission_response.json')['ref'];chosen=[r for r in rows if r.ref==ref]
    else:chosen=matching(rows)
    assert len(chosen)==1,'No unique authoritative receipt: do not upload again'
    row=chosen[0]
    assert row.file_name in {path.name,'F3c_H1_solo_prototipo_2025.csv'}
    assert row.description==MESSAGE and row.total_bytes==spec['bytes']
    status=str(row.status).rsplit('.',1)[-1]
    try:score=float(row.public_score)
    except (TypeError,ValueError):score=None
    result={'author':'Codex','utc':now(),'competition':SLUG,'ref':row.ref,'date_UTC':row.date.isoformat()+'Z' if row.date else None,
            'status':status,'public_score':score,'filename':row.file_name,'bytes':row.total_bytes,'CSV_sha256':spec['sha256'],
            'error':row.error_description,'submission_message':row.description,
            'limits':limits_dict(client.competition_get_submission_limits(SLUG)),
            'private_score_not_read':True,'other_scores_not_read_in_this_check':True,
            'research_only':True,'formal_promotion':False,'promotion_gates_passed':False,
            '2024_open':True,'B00_preserved':True,'no_final_selection':True,'goal_complete_claim':False}
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    save(folder,'public_check_'+stamp+'.json',result)
    if status=='COMPLETE':
        assert score is not None and math.isfinite(score) and score<=1,'Invalid public score'
        save(folder,'public_receipt.json',result)
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['submit','check']);args=parser.parse_args()
    if args.mode=='submit':
        control=current_delivery_gate()
        if not control['allow_new_submission']:
            print(json.dumps({'utc':now(),'status':'held_for_private_generalization_review',
                              'reason':control['reason'],'control_id':control['id'],
                              'API_authentication_called':False,'new_submissions':0},ensure_ascii=True))
            return
    spec,path=source()
    if args.mode=='submit':
        assert os.environ.get('KAGGLE_SKILL_READ_ONLY')!='1','Read-only account switch active; leave it unchanged'
        result=send_once(api(),OUT,spec,path)
    else:result=check_remote(api(),OUT,spec,path)
    print(json.dumps(result,ensure_ascii=True))


if __name__=='__main__':main()
