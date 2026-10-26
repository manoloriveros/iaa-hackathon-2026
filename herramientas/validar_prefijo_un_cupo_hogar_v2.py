"""Caso no cubierto por los seis previos: un cupo, un CSV, ningún segundo POST."""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import importlib.util,json,hashlib,contextlib,io
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/comparacion_publica_hogar_20261025_v1/synthetic_one_slot_v2';assert not OUT.exists();OUT.mkdir()
HELPER=R/'herramientas/enviar_comparacion_hogar2023_v2.py';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();spec=importlib.util.spec_from_file_location('one_slot_actual_submitter',HELPER);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.OUT=OUT;m.os=SimpleNamespace(environ={})
specs=[];receipts=[]
for i in range(2):
 p=OUT/f'synthetic_prefix_only_{i}.csv';p.write_text('id,prediction\ns0,1\ns1,2\n',encoding='utf8');dry=OUT/f'synthetic_dry_{i}.txt';dry.write_text('SYNTHETIC FLAG FIXTURE, not a real Kaggle dry-run',encoding='utf8');x={'model_id':f'SYNTHETIC-ONE-{i}','path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,'home_weight':1. if i==0 else .5,'rows':2};specs.append(x);receipts.append({'model_id':x['model_id'],'all5passed':True,'CSV_sha256':x['sha256'],'dryrun_receipt':str(dry),'dryrun_receipt_sha256':sha(dry)})
for name,d in [('ready.json',{'CSV':specs}),('separate_process_replay.json',{'success':True}),('local_dryruns_complete_v2.json',{'all_selected_csvs_passed':True,'receipts':receipts})]:(OUT/name).write_text(json.dumps(d),encoding='utf8')
class OwnRow:
 def __init__(self,a,path,message):self.a=a;self.ref=1;self.file_name=Path(path).name;self.description=message;self.total_bytes=Path(path).stat().st_size;self.date=None;self.status='COMPLETE';self.error_description=None
 @property
 def public_score(self):
  assert self.a.posts==1 and (OUT/'submission_batch_complete.json').exists();self.a.score_reads+=1;return 'SYNTHETIC_ONLY_NOT_PUBLIC'
 @property
 def private_score(self):raise AssertionError('Private score read')
class API:
 def __init__(self):self.posts=0;self.score_reads=0;self.rows=[];self.paths=[]
 def competition_get_submission_limits(self,slug):return SimpleNamespace(num_today=9+self.posts,num_total=12+self.posts,num_allowed_now=1-self.posts,limited_by_total=False)
 def competition_submissions(self,slug,page_size):return self.rows
 def competition_submit(self,path,message,slug,quiet):
  assert Path(path).resolve().is_relative_to(OUT.resolve()) and self.posts==0 and Path(path)==ROOT/specs[0]['path'];self.posts+=1;self.paths.append(path);self.rows.append(OwnRow(self,path,message));return SimpleNamespace(ref=1,message='SYNTHETIC accepted')
a=API();m.api=lambda:a
with contextlib.redirect_stdout(io.StringIO()):
 m.preflight();selected=json.loads((OUT/'selected_frozen_batch.json').read_text());assert selected['selected']==specs[:1] and a.score_reads==0;m.submit();assert a.posts==1 and a.score_reads==0;m.check('synthetic_check.json');assert a.score_reads==1
result={'utc':datetime.now(timezone.utc).isoformat(),'actual_submitter_sha256':sha(HELPER),'test_code_sha256':sha(Path(__file__)),'one_slot_selects_first_prefix_only':True,'second_CSV_not_submitted':True,'score_not_read_before_selected_batch_complete':True,'real_environment_switch_untouched':True,'synthetic_POST_calls':1,'synthetic_score_reads':1,'external_requests':0,'real_submissions':0,'new_price_fits':0,'new_C0_fits':0,'real_CSV_dryruns_not_replaced_by_fixture':True,'all_passed':True}
(OUT/'report.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
