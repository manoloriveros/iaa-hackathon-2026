"""Continúa una tanda congelada sin repetir POST ni consultar scores parciales."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,json,os,sys,argparse,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/comparacion_publica_hogar_20261025_v1';HELPER=R/'herramientas/enviar_comparacion_hogar2023_v2.py'
spec=importlib.util.spec_from_file_location('frozen_home_transport_v2',HELPER);base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();now=lambda:datetime.now(timezone.utc).isoformat()
def api():return base.api()
def save(name,data):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8') as h:json.dump(data,h,ensure_ascii=False,indent=2)
def event_receipt(data):
 name='resume_checks/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json';save(name,{'utc':now(),**data});print(json.dumps({'receipt':name,**data}),flush=True)
def metadata(row,x):
 return row.file_name==Path(x['path']).name and row.description==base.message(x) and row.total_bytes==x['bytes'] and sha(ROOT/x['path'])==x['sha256']
def canonical(x,row,origin):
 return {'utc':now(),'competition':base.SLUG,'model_id':x['model_id'],'ref':row.ref,'CSV':x,'message':base.message(x),'accepted_for_processing':True,'new_scores_read':False,'origin':origin,'remote_content_SHA_available':False,'binding':'local fullSHA + upload marker + exact ref/filename/message/bytes;server doesnotreturn contenthash'}

def resume():
 assert os.environ.get('KAGGLE_SKILL_READ_ONLY')!='1','Readonly switch active'
 specs=base.data();selected=read(OUT/'selected_frozen_batch.json')['selected'];assert selected and selected==specs[:len(selected)] and len(selected)<=2
 a=api();created=[]
 for x in selected:
  limits,rows=base.remote(a);weak=base.matching(rows,x);exact=[z for z in weak if metadata(z,x)];start=OUT/('submission_started_'+x['model_id']+'.json');response=OUT/('submission_response_'+x['model_id']+'.json');reconciled=OUT/('submission_reconciled_'+x['model_id']+'.json')
  if len(weak)!=len(exact) or len(exact)>1:
   event_receipt({'status':'blocked_ambiguous_remote_metadata','model_id':x['model_id'],'weak_matches':len(weak),'exact_matches':len(exact),'new_scores_read':False});return
  existing=read(response) if response.exists() else (read(reconciled) if reconciled.exists() else None)
  if existing is not None:
   assert existing['CSV']==x and existing['model_id']==x['model_id'] and existing['message']==base.message(x)
   matches=[z for z in exact if z.ref==existing['ref']]
   if len(matches)!=1:
    event_receipt({'status':'waiting_visibility_of_known_ref','model_id':x['model_id'],'known_ref':existing['ref'],'no_POST_retry':True,'new_scores_read':False});return
   created.append(existing);continue
  if start.exists():
   marker=read(start);assert marker['CSV']==x and marker['message']==base.message(x)
   if len(exact)!=1:
    event_receipt({'status':'waiting_reconciliation_of_uncertain_POST','model_id':x['model_id'],'no_POST_retry':True,'new_scores_read':False});return
   if exact[0].ref in marker.get('remote_refs_before',[]):
    event_receipt({'status':'blocked_remote_ref_predates_local_POST_marker','model_id':x['model_id'],'ref':exact[0].ref,'new_scores_read':False});return
   result=canonical(x,exact[0],'reconciled_existing_exact_metadata_after_local_upload_marker');save(reconciled.name,result);created.append(result);continue
  if exact:
   event_receipt({'status':'existing_remote_without_local_POST_marker','model_id':x['model_id'],'ref':exact[0].ref,'no_own_upload_history_fabricated':True,'new_scores_read':False});return
  if limits['num_allowed_now']<=0:
   event_receipt({'status':'waiting_quota_for_remaining_frozen_prefix','completed_model_ids':[z['model_id'] for z in created],'remaining_model_id':x['model_id'],'limits':limits,'new_scores_read':False});return
  assert sha(ROOT/x['path'])==x['sha256'] and (ROOT/x['path']).stat().st_size==x['bytes']
  assert read(OUT/'selected_frozen_batch.json')['selected']==selected
  save(start.name,{'utc':now(),'CSV':x,'message':base.message(x),'limits_before':limits,'public_scores_not_read':True,'selected_batch_sha256':sha(OUT/'selected_frozen_batch.json'),'remote_refs_before':[z.ref for z in rows]})
  try:
   r=a.competition_submit(str(ROOT/x['path']),base.message(x),base.SLUG,quiet=True)
   assert r.ref>0
   result={'utc':now(),'competition':base.SLUG,'model_id':x['model_id'],'ref':r.ref,'response_message':r.message,'CSV':x,'message':base.message(x),'accepted_for_processing':True,'new_scores_read':False,'origin':'own_POST_response'};save(response.name,result);created.append(result)
  except Exception as exc:
   save('submission_failure_v3_'+x['model_id']+'.json',{'utc':now(),'error_type':type(exc).__name__,'status_uncertain':True,'no_blind_POST_retry':True});event_receipt({'status':'waiting_reconciliation_after_POST_error','model_id':x['model_id'],'error_type':type(exc).__name__,'new_scores_read':False});return
 assert [x['model_id'] for x in created]==[x['model_id'] for x in selected]
 batch=OUT/'submission_batch_complete.json'
 if batch.exists():
  old=read(batch);assert [(x['model_id'],x['ref'],x['CSV']['sha256']) for x in old['created']]==[(x['model_id'],x['ref'],x['CSV']['sha256']) for x in created]
 else:save(batch.name,{'utc':now(),'created':created,'no_public_scores_before_all_selected_POSTs':True,'scope_of_score_order_statement':'this own flow','partial_or_uncertain_reconciliation_supported':True})
 event_receipt({'status':'frozen_selected_batch_complete','model_ids':[x['model_id'] for x in created],'refs':[x['ref'] for x in created],'new_scores_read':False})

def check(name):
 base.data();batch=read(OUT/'submission_batch_complete.json');selected=read(OUT/'selected_frozen_batch.json')['selected'];assert [x['CSV'] for x in batch['created']]==selected
 a=api();limits,rows=base.remote(a);chosen=[]
 for x in batch['created']:
  matches=[z for z in rows if z.ref==x['ref']];assert len(matches)==1 and metadata(matches[0],x['CSV']);chosen.append((x,matches[0]))
 # Every selected upload has a receipt and all metadata pass before reading firstscore.
 results=[]
 for x,r in chosen:
  results.append({'model_id':x['model_id'],'ref':r.ref,'date_UTC':r.date.isoformat()+'Z' if r.date else None,'status':str(r.status).rsplit('.',1)[-1],'public_score':r.public_score,'error':r.error_description,'filename':r.file_name,'bytes':r.total_bytes,'CSV_sha256':x['CSV']['sha256']})
 payload={'utc':now(),'competition':base.SLUG,'results':results,'limits':limits,'new_fit_calls':0,'2024_policy_or_metrics_read':False,'private_score_read':False,'other_submission_scores_read':False,'recipes_changed_after_public':False,'manual_final_selection':False,'research_only_gates_unresolved':True,'all_selected_metadata_validated_before_any_score':True};save(name,payload);print(json.dumps(payload))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['resume','check']);p.add_argument('--receipt',default='public_check_v3_01.json');a=p.parse_args();resume() if a.action=='resume' else check(a.receipt)
