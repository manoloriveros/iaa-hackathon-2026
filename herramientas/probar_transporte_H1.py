"""Prueba del transporte de entrega real con clientes sintéticos sin red."""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
import importlib.util
import json
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sp=importlib.util.spec_from_file_location('H1_transport_under_test',R/'herramientas/enviar_H1_investigacion.py')
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);sys.stdout.reconfigure(encoding='utf8')


class Row:
    def __init__(self,spec,path,ref=314,status='COMPLETE',score='0.12345'):
        self.ref=ref;self.file_name=path.name;self.description=m.MESSAGE;self.total_bytes=spec['bytes']
        self.status=status;self.public_score=score;self.error_description='';self.date=datetime(2026,10,26,tzinfo=timezone.utc)
    @property
    def private_score(self):raise AssertionError('Private score must never be read')


class Client:
    def __init__(self,allowed=1,rows=None,fail=False,ref=314,barrier=None):
        self.allowed=allowed;self.rows=rows or [];self.fail=fail;self.ref=ref
        self.posts=0;self.barrier=barrier;self.lock=Lock()
    def competition_get_submission_limits(self,slug):
        assert slug==m.SLUG
        return SimpleNamespace(num_today=10-self.allowed,num_total=22,num_allowed_now=self.allowed,limited_by_total=False)
    def competition_submissions(self,slug,page_size=100):
        assert slug==m.SLUG and page_size==100
        if self.barrier:self.barrier.wait(timeout=10)
        return self.rows
    def competition_submit(self,path,message,slug,quiet=True):
        assert slug==m.SLUG and message==m.MESSAGE and quiet
        with self.lock:self.posts+=1
        if self.fail:raise TimeoutError('Synthetic unknown remote outcome')
        return SimpleNamespace(ref=self.ref,message='Synthetic accepted')


def rejected(fn):
    try:fn()
    except (AssertionError,FileExistsError):return True
    raise AssertionError('Expected transport rejection')


def main():
    assert not (m.OUT/'transport_selftest.json').exists()
    fixture=m.OUT/'synthetic_transport';assert not fixture.exists();fixture.mkdir()
    copy=m.read(m.OUT/'copy_receipt.json');spec=copy['CSV'];path=ROOT/spec['path']
    assert m.sha(path)==spec['sha256']==m.SHA
    def folder(name):
        p=fixture/name;p.mkdir();return p
    checks=[]
    f=folder('zero_quota');c=Client(allowed=0)
    r=m.send_once(c,f,spec,path)
    assert r['status']=='no_current_quota_no_upload' and c.posts==0 and not (f/'submission_started.json').exists()
    checks.append('zero_quota_never_POST_or_claim_start')
    f=folder('duplicate');c=Client(rows=[Row(spec,path)])
    r=m.send_once(c,f,spec,path)
    assert r['status']=='matching_remote_artifact_reconcile_without_upload' and c.posts==0
    assert not (f/'submission_started.json').exists()
    checks.append('duplicate_remote_file_no_POST')
    f=folder('success_and_pending');c=Client()
    r=m.send_once(c,f,spec,path);assert r['ref']==314 and c.posts==1
    rejected(lambda:m.send_once(c,f,spec,path));assert c.posts==1
    c.rows=[Row(spec,path,status='PENDING',score='')]
    r=m.check_remote(c,f,spec,path);assert r['public_score'] is None and not (f/'public_receipt.json').exists()
    c.rows=[Row(spec,path)]
    r=m.check_remote(c,f,spec,path);assert r['status']=='COMPLETE' and r['public_score']==.12345
    assert r['private_score_not_read'] and c.posts==1
    again=m.check_remote(c,f,spec,path);assert r==again
    checks += ['exclusive_start_prevents_reentry','pending_is_not_processed','exact_ref_message_size_complete_receipt','private_score_property_never_read','processed_check_idempotent']
    f=folder('uncertain_response');c=Client(fail=True)
    try:m.send_once(c,f,spec,path)
    except TimeoutError:pass
    else:raise AssertionError('Expected synthetic timeout')
    assert c.posts==1 and (f/'submission_started.json').exists() and (f/'submission_uncertain.json').exists()
    rejected(lambda:m.send_once(c,f,spec,path));assert c.posts==1
    c.rows=[Row(spec,path,ref=2718)]
    r=m.check_remote(c,f,spec,path);assert r['ref']==2718 and c.posts==1
    checks += ['uncertain_response_never_rePOST','uncertain_response_reconciles_one_remote_artifact']
    f=folder('zero_reference');c=Client(ref=0)
    rejected(lambda:m.send_once(c,f,spec,path))
    assert c.posts==1 and (f/'submission_uncertain.json').exists()
    rejected(lambda:m.send_once(c,f,spec,path));assert c.posts==1
    checks.append('invalid_ack_ref_durable_uncertain_no_retry')
    for mutation in ['message','bytes','filename','different_ref','ambiguous']:
        f=folder('bad_'+mutation);row=Row(spec,path)
        if mutation=='message':row.description='Wrong delivery message'
        if mutation=='bytes':row.total_bytes+=1
        if mutation=='filename':row.file_name='other.csv'
        if mutation=='different_ref':
            m.save(f,'submission_response.json',{'ref':999});row.ref=314
        c=Client(rows=[row,row] if mutation=='ambiguous' else [row])
        rejected(lambda:m.check_remote(c,f,spec,path))
        assert c.posts==0 and not (f/'public_receipt.json').exists()
    checks.append('wrong_message_size_name_ref_and_ambiguity_rejected')
    # Valid D2 can be negative. A bad real result still must be retained.
    f=folder('negative_public_score');c=Client(rows=[Row(spec,path,score='-0.5')])
    r=m.check_remote(c,f,spec,path);assert r['public_score']==-.5 and (f/'public_receipt.json').exists()
    checks.append('valid_negative_D2_preserved_without_false_success')
    for text in ['nan','inf','1.1']:
        f=folder('invalid_score_'+text.replace('.','_'));c=Client(rows=[Row(spec,path,score=text)])
        rejected(lambda:m.check_remote(c,f,spec,path));assert not (f/'public_receipt.json').exists()
    checks.append('nonfinite_or_above_one_score_rejected')
    f=folder('concurrent_start');barrier=Barrier(2);c=Client(barrier=barrier)
    def contender():
        try:return m.send_once(c,f,spec,path)['accepted_for_processing']
        except (AssertionError,FileExistsError):return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        result=list(pool.map(lambda _:contender(),range(2)))
    assert sum(result)==1 and c.posts==1
    assert (f/'submission_started.json').exists() and (f/'submission_response.json').exists()
    checks.append('two_concurrent_real_flow_calls_only_one_exclusive_POST')
    receipt={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'all_passed':True,'checks':checks,
             'transport_code_sha256':m.sha(Path(m.__file__)),'selftest_code_sha256':m.sha(Path(__file__)),
             'network_calls':0,'synthetic_only':True,'synthetic_public_scores_not_competition_results':True,
             'real_CSV_copy_hash_verified':True,'new_competition_submissions':0}
    m.save(m.OUT,'transport_selftest.json',receipt)
    print(json.dumps(receipt,ensure_ascii=True))


if __name__=='__main__':main()
