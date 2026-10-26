"""Flujo real del ejecutor con API simulada aislada, sin red o precios nuevos."""
from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
import importlib.util,json,hashlib,contextlib,io
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
SCRIPT=R/'herramientas/enviar_comparacion_hogar2023_v2.py'
OUT=R/'privado/semana2/robustez2023/comparacion_publica_hogar_20261025_v1/synthetic_actual_submitter_v2'
assert not OUT.exists();OUT.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def load():
    s=importlib.util.spec_from_file_location('isolated_submitter',SCRIPT);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def fixture(name):
    p=OUT/name;p.mkdir();specs=[];receipts=[]
    for i in range(2):
        csv=p/f'synthetic_only_{i}.csv';csv.write_text('id,prediction\ns0,10\ns1,20\n',encoding='utf8')
        dr=p/f'dummy_dryrun_{i}.txt';dr.write_text('SYNTHETIC receipt only; not a Kaggle dry-run.',encoding='utf8')
        x={'model_id':f'SYNTHETIC-{i}','path':csv.relative_to(ROOT).as_posix(),'sha256':sha(csv),'home_weight':1. if i==0 else .5,'bytes':csv.stat().st_size,'rows':2};specs.append(x)
        receipts.append({'model_id':x['model_id'],'all5passed':True,'CSV_sha256':x['sha256'],'dryrun_receipt':str(dr),'dryrun_receipt_sha256':sha(dr)})
    for n,d in [('ready.json',{'CSV':specs}),('separate_process_replay.json',{'success':True}),('local_dryruns_complete_v2.json',{'all_selected_csvs_passed':True,'receipts':receipts})]:
        (p/n).write_text(json.dumps(d),encoding='utf8')
    return p,specs

class Row:
    def __init__(self,api,ref,filename,message,size,foreign=False):
        self.api=api;self.ref=ref;self.file_name=filename;self.description=message;self.total_bytes=size;self.status='COMPLETE';self.date=None;self.error_description=None;self.foreign=foreign
    @property
    def public_score(self):
        assert not self.foreign,'Foreign score read'
        assert self.api.all_posts_complete,'Score read before completing selected batch'
        self.api.score_reads+=1;return '0.12345'
    @property
    def private_score(self):raise AssertionError('Private score read')

class API:
    def __init__(self,m,p,specs,quota=2,partial=False,uncertain=False):
        self.m=m;self.p=p;self.specs=specs;self.quota=quota;self.partial=partial;self.uncertain=uncertain;self.posts=0;self.score_reads=0;self.all_posts_complete=False
        self.rows=[Row(self,9000,'foreign.csv','unrelated',1,True)]
    def competition_get_submission_limits(self,slug):return SimpleNamespace(num_today=10-self.quota,num_total=12,num_allowed_now=self.quota,limited_by_total=False)
    def competition_submissions(self,slug,page_size):return self.rows
    def competition_submit(self,path,message,slug,quiet):
        assert Path(path).resolve().is_relative_to(OUT.resolve()),'Synthetic isolation failed'
        assert self.quota>0;self.posts+=1;self.quota-=1
        self.rows.insert(0,Row(self,100+self.posts,Path(path).name,message,Path(path).stat().st_size))
        if self.partial:self.quota=0
        if self.uncertain:raise TimeoutError('Synthetic lost response after server acceptance')
        return SimpleNamespace(ref=100+self.posts,message='Synthetic API receipt')

def expect_error(call,types=(AssertionError,FileExistsError,TimeoutError)):
    try:call()
    except types:return True
    raise AssertionError('Expected adverse control did not fail')

results=[]
with contextlib.redirect_stdout(io.StringIO()):
    for name,quota,partial,uncertain in [('zero_quota',0,False,False),('two_posts',2,False,False),('partial_quota',2,True,False),('lost_response',2,False,True),('readonly',2,False,False),('tampered_csv',2,False,False)]:
        m=load();p,specs=fixture(name);m.OUT=p;a=API(m,p,specs,quota,partial,uncertain);m.api=lambda:a
        # Patch only this module's environment view, never the actual user's switch.
        m.os=SimpleNamespace(environ={'KAGGLE_SKILL_READ_ONLY':'1'} if name=='readonly' else {})
        if name=='tampered_csv':
            (ROOT/specs[0]['path']).write_text('tampered',encoding='utf8');expect_error(m.preflight);assert a.posts==0 and a.score_reads==0
        else:
            m.preflight();assert a.score_reads==0
            if not quota:assert not (p/'selected_frozen_batch.json').exists() and a.posts==0
            elif name=='readonly':expect_error(m.submit);assert not list(p.glob('submission_started*')) and a.posts==0
            elif partial or uncertain:
                expect_error(m.submit);assert a.posts==1 and a.score_reads==0 and not (p/'submission_batch_complete.json').exists()
                expect_error(m.submit);assert a.posts==1 and a.score_reads==0
            else:
                m.submit();assert a.posts==2 and a.score_reads==0 and (p/'submission_batch_complete.json').exists()
                a.all_posts_complete=True;m.check('public_synthetic_check.json');assert a.score_reads==2
                own=next(x for x in a.rows if not x.foreign);own.total_bytes+=1;expect_error(lambda:m.check('invalid_size_check.json'));assert not (p/'invalid_size_check.json').exists()
        results.append({'case':name,'passed':True,'synthetic_POSTs':a.posts,'synthetic_public_score_reads':a.score_reads,'foreign_private_scores_read':False})
report={'utc':datetime.now(timezone.utc).isoformat(),'actual_submitter':SCRIPT.relative_to(ROOT).as_posix(),'actual_submitter_sha256':sha(SCRIPT),'test_code_sha256':sha(Path(__file__)),'cases':results,'external_requests':0,'real_submissions':0,'real_price_fits':0,'C0_fits':0,'synthetic_csvs_cannot_leave_fixture':True,'all_passed':True,'limitation':'Partial/uncertain batches stop safely; automatic reconciliation/resumption not implemented and requires exact receipt reconciliation before further POST. Fixture flags do not certify real CSV dry-runs; those existing receipts remain separate.','2024_closed':True}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
