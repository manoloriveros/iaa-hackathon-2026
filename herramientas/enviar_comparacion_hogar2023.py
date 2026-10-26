"""Envía dos CSV congelados antes de leer cualquier nuevo score público."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,subprocess,sys
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/comparacion_publica_hogar_20261025_v1'
SLUG='iaa-ai-assisted-hackathon-2026-part-2'
now=lambda:datetime.now(timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(name,obj):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,ensure_ascii=False)
def api():
 from kaggle.api.kaggle_api_extended import KaggleApi
 a=KaggleApi();a.authenticate();return a
def data():
 d=read(OUT/'ready.json');assert read(OUT/'separate_process_replay.json')['success']
 for x in d['CSV']:assert sha(ROOT/x['path'])==x['sha256']
 return d['CSV']
def message(x):return 'Codex RESEARCH '+x['model_id']+' | home weight '+str(x['home_weight'])+' | train2023 gates unresolved | '+x['sha256'][:16]
def remote(a):
 lim=a.competition_get_submission_limits(SLUG)
 counts={k:getattr(lim,k) for k in ['num_today','num_total','num_allowed_now','limited_by_total']}
 return counts,a.competition_submissions(SLUG,page_size=100) or []


def preflight():
 specs=data();a=api();lim,rows=remote(a)
 matches=[]
 for x in specs:
  for row in rows:
   if row.file_name==Path(x['path']).name or row.description==message(x):matches.append({'model_id':x['model_id'],'ref':row.ref,'status':str(row.status)})
 safe=[{'ref':row.ref,'date':row.date.isoformat() if row.date else None,'status':str(row.status).rsplit('.',1)[-1]} for row in rows]
 selected=specs[:min(lim['num_allowed_now'],2)]
 result={'utc':now(),'competition':SLUG,'limits':lim,'matching_submissions':matches,'other_rows_metadata_only':safe,
         'selected':selected,'no_scores_consulted':True,'no_account_write':True,'recipes_fixed_before_new_scores':True}
 save('submission_preflight.json',result);print(json.dumps(result))
 assert not matches,'Conciliar envío existente; no duplicar'
 assert selected,'Cuota sin cupos disponibles'


def dryrun():
 p=read(OUT/'submission_preflight.json');env=os.environ.copy();env['PATH']=str(Path(sys.executable).parent)+';'+env.get('PATH','')
 skill=ROOT/'.agents/skills/kaggle/scripts/kaggle_skill.py';sample=R/'privado/semana2/envios/g4_20261025_v1/official_sample_format.csv'
 assert sha(sample)=='0a4496eb14d6450bb4583b2e90ae31fde95d71c1629656a03d54ffd1515f666c'
 for x in p['selected']:
  output=OUT/('dryrun_'+x['model_id']+'.txt');assert not output.exists()
  cp=subprocess.run([sys.executable,str(skill),'submit',SLUG,str(ROOT/x['path']),'-m',message(x),'--sample',str(sample)],
                    cwd=OUT,env=env,capture_output=True,text=True,encoding='utf-8')
  with output.open('x',encoding='utf-8') as f:f.write(cp.stdout+'\n'+cp.stderr)
  assert cp.returncode==0 and 'all 5 passed' in cp.stdout,'Dry-run no satisfactorio'
  print(json.dumps({'model_id':x['model_id'],'dry_run':'all5passed','receipt':str(output),'account_changed':False}))


def submit():
 assert os.environ.get('KAGGLE_SKILL_READ_ONLY')!='1','Switch read-only activo; no alterar'
 specs=read(OUT/'submission_preflight.json')['selected'];data();a=api();created=[]
 for x in specs:
  assert (OUT/('dryrun_'+x['model_id']+'.txt')).exists()
  lim,rows=remote(a)
  assert lim['num_allowed_now']>0,'Cuota agotada antes del POST'
  assert not any(row.file_name==Path(x['path']).name or row.description==message(x) for row in rows),'Conciliar antes de repetir'
  save('submission_started_'+x['model_id']+'.json',{'utc':now(),'model_id':x['model_id'],'sha256':x['sha256'],'limits_before':lim,'no_new_scores_read':True})
  # El marcador x evita repetir un POST incierto. No se lee public_score hasta acabar la tanda.
  try:
   response=a.competition_submit(str(ROOT/x['path']),message(x),SLUG,quiet=True)
   result={'utc':now(),'competition':SLUG,'model_id':x['model_id'],'ref':response.ref,'response_message':response.message,
          'CSV':x,'message':message(x),'accepted_for_processing':response.ref>0,'new_scores_read':False}
   save('submission_response_'+x['model_id']+'.json',result)
   assert response.ref>0
   created.append(result);print(json.dumps(result),flush=True)
  except Exception as e:
   save('submission_failure_'+x['model_id']+'.json',{'utc':now(),'error_type':type(e).__name__,'status_uncertain':True,'action':'reconcile by ID/message before retry'})
   print(json.dumps({'model_id':x['model_id'],'error_type':type(e).__name__,'status_uncertain':True}));raise SystemExit(1)
 save('submission_batch_complete.json',{'utc':now(),'competition':SLUG,'created':created,'no_public_scores_read_before_all_posts':True})


def check(receipt):
 batch=read(OUT/'submission_batch_complete.json');a=api();lim,rows=remote(a);results=[]
 for x in batch['created']:
  match=[row for row in rows if row.ref==x['ref']];assert len(match)==1
  row=match[0];assert row.file_name==Path(x['CSV']['path']).name and row.description==x['message'] and row.total_bytes==x['CSV']['bytes']
  assert sha(ROOT/x['CSV']['path'])==x['CSV']['sha256']
  results.append({'model_id':x['model_id'],'ref':row.ref,'date_UTC':row.date.isoformat()+'Z' if row.date else None,
     'status':str(row.status).rsplit('.',1)[-1],'public_score':row.public_score,'error':row.error_description,
     'filename':row.file_name,'bytes':row.total_bytes,'CSV_sha256':x['CSV']['sha256']})
 result={'utc':now(),'competition':SLUG,'results':results,'limits':lim,'new_fit_calls':0,'2024_policy_or_metrics_read':False,
         'private_score_read':False,'other_submission_scores_read':False,'recipes_changed_after_public':False,'manual_final_selection':False}
 save(receipt,result);print(json.dumps(result))


if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['preflight','dryrun','submit','check']);p.add_argument('--receipt',default='public_check01.json');args=p.parse_args()
 if args.action=='preflight':preflight()
 elif args.action=='dryrun':dryrun()
 elif args.action=='submit':submit()
 else:check(args.receipt)
