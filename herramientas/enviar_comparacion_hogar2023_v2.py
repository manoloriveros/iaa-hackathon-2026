"""Reanudación por cuota sin duplicar POST ni confundir un dry-run fallido con uno válido."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,os,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/comparacion_publica_hogar_20261025_v1';SLUG='iaa-ai-assisted-hackathon-2026-part-2'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();now=lambda:datetime.now(timezone.utc).isoformat()
def save(name,data):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as h:json.dump(data,h,ensure_ascii=False,indent=2)
def data():
 ready=read(OUT/'ready.json');assert read(OUT/'separate_process_replay.json')['success'];dry=read(OUT/'local_dryruns_complete_v2.json');assert dry['all_selected_csvs_passed']
 for x in ready['CSV']:
  assert sha(ROOT/x['path'])==x['sha256'];r=next(r for r in dry['receipts'] if r['model_id']==x['model_id']);assert r['all5passed'] and r['CSV_sha256']==x['sha256'] and sha(Path(r['dryrun_receipt']))==r['dryrun_receipt_sha256']
 return ready['CSV']
def api():
 from kaggle.api.kaggle_api_extended import KaggleApi
 a=KaggleApi();a.authenticate();return a
def remote(a):
 lim=a.competition_get_submission_limits(SLUG);return {key:getattr(lim,key) for key in ['num_today','num_total','num_allowed_now','limited_by_total']},a.competition_submissions(SLUG,page_size=100) or []
def message(x):return 'Codex RESEARCH '+x['model_id']+' | home weight '+str(x['home_weight'])+' | train2023 gates unresolved | '+x['sha256'][:16]
def matching(rows,x):return [r for r in rows if r.file_name==Path(x['path']).name or r.description==message(x)]
def preflight():
 specs=data();a=api();lim,rows=remote(a);matches=[{'model_id':x['model_id'],'ref':r.ref,'status':str(r.status).rsplit('.',1)[-1]} for x in specs for r in matching(rows,x)];selected=specs[:min(2,lim['num_allowed_now'])];result={'utc':now(),'competition':SLUG,'limits':lim,'matching_own_submissions':matches,'selected':selected,'no_scores_consulted':True,'no_account_write':True,'research_only':True};name='quota_checks/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json';save(name,result)
 assert not matches,'Conciliar antes de otro POST'
 if selected:
  p=OUT/'selected_frozen_batch.json'
  if p.exists():assert read(p)['selected']==selected,'No cambiar la tanda congelada'
  else:save('selected_frozen_batch.json',result)
 print(json.dumps({'receipt':name,**result}))
def submit():
 assert os.environ.get('KAGGLE_SKILL_READ_ONLY')!='1','Switch readonly activo:no alterar';specs=data();selected=read(OUT/'selected_frozen_batch.json')['selected'];assert selected and selected==specs[:len(selected)] and len(selected)<=2;a=api();created=[]
 for x in selected:
  lim,rows=remote(a);assert lim['num_allowed_now']>0,'Cuota agotada antes de POST';assert not matching(rows,x),'Conciliar envío existente;no duplicar';save('submission_started_'+x['model_id']+'.json',{'utc':now(),'CSV':x,'message':message(x),'limits_before':lim,'public_scores_not_read':True})
  try:
   response=a.competition_submit(str(ROOT/x['path']),message(x),SLUG,quiet=True);result={'utc':now(),'competition':SLUG,'model_id':x['model_id'],'ref':response.ref,'response_message':response.message,'CSV':x,'message':message(x),'accepted_for_processing':response.ref>0,'new_scores_read':False};save('submission_response_'+x['model_id']+'.json',result);assert response.ref>0;created.append(result);print(json.dumps(result),flush=True)
  except Exception as exc:
   save('submission_failure_'+x['model_id']+'.json',{'utc':now(),'error_type':type(exc).__name__,'status_uncertain':True,'action':'reconcile exactfilename/message before retry;never repeat uncertainPOST'});raise
 save('submission_batch_complete.json',{'utc':now(),'created':created,'no_public_scores_before_all_selected_POSTs':True})
def check(name):
 batch=read(OUT/'submission_batch_complete.json');a=api();lim,rows=remote(a);result=[]
 for x in batch['created']:
  chosen=[r for r in rows if r.ref==x['ref']];assert len(chosen)==1;r=chosen[0];assert r.file_name==Path(x['CSV']['path']).name and r.description==x['message'] and r.total_bytes==x['CSV']['bytes'] and sha(ROOT/x['CSV']['path'])==x['CSV']['sha256'];result.append({'model_id':x['model_id'],'ref':r.ref,'date_UTC':r.date.isoformat()+'Z' if r.date else None,'status':str(r.status).rsplit('.',1)[-1],'public_score':r.public_score,'error':r.error_description,'filename':r.file_name,'bytes':r.total_bytes,'CSV_sha256':x['CSV']['sha256']})
 payload={'utc':now(),'competition':SLUG,'results':result,'limits':lim,'new_fit_calls':0,'2024_policy_or_metrics_read':False,'private_score_read':False,'other_submission_scores_read':False,'recipes_changed_after_public':False,'manual_final_selection':False,'research_only_gates_unresolved':True};save(name,payload);print(json.dumps(payload))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['preflight','submit','check']);p.add_argument('--receipt',default='public_check01.json');a=p.parse_args();{'preflight':preflight,'submit':submit,'check':lambda:check(a.receipt)}[a.action]()
