"""Flujo real de conciliación con API simulada; cero red y cero envíos reales."""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import importlib.util,json,hashlib,contextlib,io
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/comparacion_publica_hogar_20261025_v1/synthetic_resume_v3';assert not OUT.exists();OUT.mkdir()
SCRIPT=R/'herramientas/enviar_comparacion_hogar2023_v3.py';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def fixture(name,n=2):
 p=OUT/name;p.mkdir();spec=importlib.util.spec_from_file_location('resume_case_'+name,SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=p;m.base.OUT=p;m.os=SimpleNamespace(environ={});specs=[];receipts=[]
 for i in range(2):
  f=p/f'synthetic_resume_{i}.csv';f.write_text('id,prediction\ns0,1\ns1,2\n',encoding='utf8');dry=p/f'fixture_dry_{i}.txt';dry.write_text('SYNTHETIC receipt flags,not real Kaggle dryrun',encoding='utf8');x={'model_id':f'SYNTHETIC-RESUME-{i}','path':f.relative_to(ROOT).as_posix(),'sha256':sha(f),'bytes':f.stat().st_size,'rows':2,'home_weight':1. if i==0 else .5};specs.append(x);receipts.append({'model_id':x['model_id'],'all5passed':True,'CSV_sha256':x['sha256'],'dryrun_receipt':str(dry),'dryrun_receipt_sha256':sha(dry)})
 for filename,data in [('ready.json',{'CSV':specs}),('separate_process_replay.json',{'success':True}),('local_dryruns_complete_v2.json',{'all_selected_csvs_passed':True,'receipts':receipts}),('selected_frozen_batch.json',{'selected':specs[:n]})]:(p/filename).write_text(json.dumps(data),encoding='utf8')
 return m,p,specs
class Row:
 def __init__(self,a,ref,path,message,foreign=False):self.a=a;self.ref=ref;self.file_name=Path(path).name;self.description=message;self.total_bytes=Path(path).stat().st_size;self.date=None;self.status='COMPLETE';self.error_description=None;self.foreign=foreign
 @property
 def public_score(self):
  assert not self.foreign and (self.a.p/'submission_batch_complete.json').exists() and len([x for x in self.a.rows if not x.foreign])>=self.a.expected;self.a.score_reads+=1;return 'SYNTHETIC_ONLY'
 @property
 def private_score(self):raise AssertionError('Private score read')
class API:
 def __init__(self,p,specs,quota=2,expected=2):
  self.p=p;self.specs=specs;self.quota=quota;self.expected=expected;self.posts=0;self.score_reads=0;self.rows=[];self.lose_after_accept=False;self.lose_before_accept=False;self.hide_known=False
  self.rows.append(Row(self,9000,ROOT/specs[0]['path'],'UNRELATED',True));self.rows[0].file_name='foreign.csv'
 def competition_get_submission_limits(self,slug):return SimpleNamespace(num_today=10-self.quota,num_total=12,num_allowed_now=self.quota,limited_by_total=False)
 def competition_submissions(self,slug,page_size):return [self.rows[0]] if self.hide_known else self.rows
 def competition_submit(self,path,message,slug,quiet):
  assert Path(path).resolve().is_relative_to(OUT.resolve()) and self.quota>0;self.posts+=1
  if self.lose_before_accept:self.lose_before_accept=False;raise TimeoutError('SYNTHETIC request outcome unknown without accepted row')
  self.quota-=1;self.rows.append(Row(self,100+self.posts,path,message))
  if self.lose_after_accept:self.lose_after_accept=False;raise TimeoutError('SYNTHETIC response lost after acceptance')
  return SimpleNamespace(ref=100+self.posts,message='SYNTHETIC accepted')
def rejected(fn):
 try:fn()
 except AssertionError:return True
 raise AssertionError('Expected adverse guard did not reject')
results=[]
def record(name,a,extra=None):results.append({'case':name,'passed':True,'synthetic_POST_calls':a.posts,'synthetic_score_reads':a.score_reads,**(extra or {})})
with contextlib.redirect_stdout(io.StringIO()):
 m,p,s=fixture('normal_idempotent');a=API(p,s);m.api=lambda:a;m.resume();assert a.posts==2 and a.score_reads==0;m.resume();assert a.posts==2;m.check('check.json');assert a.score_reads==2;next(x for x in a.rows if x.ref==102).total_bytes+=1;rejected(lambda:m.check('bad_metadata.json'));assert a.score_reads==2 and not (p/'bad_metadata.json').exists();record('normal_idempotent_and_all_metadata_before_scores',a)
 m,p,s=fixture('partial');a=API(p,s,quota=1);m.api=lambda:a;m.resume();assert a.posts==1 and a.score_reads==0 and not (p/'submission_batch_complete.json').exists();a.quota=1;m.resume();assert a.posts==2 and a.score_reads==0;m.check('check.json');record('partial_quota_resumes_only_remaining',a)
 m,p,s=fixture('accepted_lost_response');a=API(p,s);a.lose_after_accept=True;m.api=lambda:a;m.resume();assert a.posts==1 and a.score_reads==0;m.resume();assert a.posts==2 and (p/('submission_reconciled_'+s[0]['model_id']+'.json')).exists();m.check('check.json');record('lost_response_reconciles_without_duplicate',a)
 m,p,s=fixture('unknown_no_row');a=API(p,s);a.lose_before_accept=True;m.api=lambda:a;m.resume();assert a.posts==1;m.resume();assert a.posts==1 and a.score_reads==0 and not (p/'submission_batch_complete.json').exists();record('uncertain_without_row_never_retries_POST',a)
 m,p,s=fixture('known_ref_not_visible');a=API(p,s,quota=1);m.api=lambda:a;m.resume();assert a.posts==1;a.quota=1;a.hide_known=True;m.resume();assert a.posts==1 and a.score_reads==0;a.hide_known=False;m.resume();assert a.posts==2;record('known_ref_visibility_waits_then_resumes',a)
 m,p,s=fixture('weak_collision');a=API(p,s);a.rows.append(Row(a,999,ROOT/s[0]['path'],'OTHER MESSAGE'));m.api=lambda:a;m.resume();assert a.posts==0 and a.score_reads==0;record('weak_metadata_collision_blocks',a)
 m,p,s=fixture('readonly');a=API(p,s);m.api=lambda:a;m.os=SimpleNamespace(environ={'KAGGLE_SKILL_READ_ONLY':'1'});rejected(m.resume);assert a.posts==0;record('readonly_blocks_POST',a)
 m,p,s=fixture('one_prefix',1);a=API(p,s,quota=1,expected=1);m.api=lambda:a;m.resume();assert a.posts==1 and a.score_reads==0;m.check('check.json');assert a.score_reads==1;record('one_slot_prefix_only',a)
 m,p,s=fixture('existing_without_marker');a=API(p,s);a.rows.append(Row(a,999,ROOT/s[0]['path'],m.base.message(s[0])));m.api=lambda:a;m.resume();assert a.posts==0 and a.score_reads==0 and not (p/'submission_batch_complete.json').exists();record('existing_without_local_history_not_adopted',a)
report={'utc':datetime.now(timezone.utc).isoformat(),'actual_submitter_v3_sha256':sha(SCRIPT),'frozen_helper_v2_sha256':sha(R/'herramientas/enviar_comparacion_hogar2023_v2.py'),'test_code_sha256':sha(Path(__file__)),'cases':results,'external_requests':0,'real_submissions':0,'new_price_fits':0,'new_C0_fits':0,'all_passed':True,'real_dryruns_remain_separate_from_fixture_flags':True,'limit':'Unknown POST without remote row remains unresolved;no blindretry. Remote contenthash unavailable;binding uses localSHA/marker/exact remote metadata.'}
(OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
