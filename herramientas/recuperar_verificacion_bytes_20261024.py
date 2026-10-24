"""Recupera solo transferencias pendientes mediante rangos pequeños; sin decodificar tablas."""
from pathlib import Path,PurePosixPath
from urllib.parse import urlparse
import base64,hashlib,importlib.util,json,os,sys,time,requests

ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
spec=importlib.util.spec_from_file_location('binary_verifier',REPO/'herramientas/verificar_bytes_parquet_oficiales_20261024.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
RUN=v.RUN;ATTEMPT=RUN/'recovery_1';BLOCK=4*1024*1024

def attempt_request(method,url,**kwargs):
    for attempt in range(3):
        try:
            response=requests.request(method,url,timeout=(20,45),**kwargs)
            if response.status_code in [200,206]:return response
            response.close()
        except requests.RequestException:pass
        if attempt<2:time.sleep(2**attempt)
    raise RuntimeError('Network or HTTP failure after finite retries')

def verify_file(item,token,expected):
    name=item['name'];part=PurePosixPath(name);assert len(part.parts)==2 and part.parts[0] in ['developed','emerging'] and '..' not in part.parts
    baseline=ROOT/('Hackaton/Semana 1/Datos' if part.parts[0]=='developed' else 'Hackaton/Semana 2/Datos/emerging')/part.name
    baseline=baseline.resolve();assert baseline.is_relative_to(ROOT.resolve()) and baseline.is_file()
    target=ATTEMPT/'opaque_downloads'/Path(*part.parts);target.parent.mkdir(parents=True,exist_ok=True)
    start=v.now();before=baseline.stat();oldsha=hashlib.sha256();oldmd5=hashlib.md5()
    with baseline.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):oldsha.update(b);oldmd5.update(b)
    lookup=None
    for retry in range(3):
        lookup=v.mcp_client.request('download_competition_data_file',{'competitionName':v.COMP,'fileName':name},token=token)
        if lookup.ok and isinstance(lookup.data,dict):break
        if retry<2:time.sleep(2**retry)
    if not lookup.ok or not isinstance(lookup.data,dict):raise RuntimeError('Official download URL unavailable')
    url=lookup.data.get('url');assert isinstance(url,str) and urlparse(url).scheme=='https' and urlparse(url).hostname=='storage.googleapis.com'
    with attempt_request('HEAD',url,allow_redirects=True) as h:
        assert urlparse(h.url).hostname=='storage.googleapis.com'
        safe={k:val for k,val in h.headers.items() if k.lower() in ['content-length','content-type','etag','x-goog-generation','x-goog-hash','last-modified']}
        object_md5=v.official_md5(h.headers);generation=h.headers.get('x-goog-generation')
        assert int(h.headers['Content-Length'])==item['total_bytes'] and object_md5
    newsha=hashlib.sha256();newmd5=hashlib.md5();equal=before.st_size==item['total_bytes'];offset=None;size=0;prefix=b'';suffix=b'';ranges=0
    with baseline.open('rb') as old,target.open('xb') as fresh:
        for begin in range(0,item['total_bytes'],BLOCK):
            end=min(begin+BLOCK,item['total_bytes'])-1
            with attempt_request('GET',url,headers={'Range':f'bytes={begin}-{end}'}) as response:
                assert response.status_code==206 or (begin==0 and end+1==item['total_bytes'])
                if response.status_code==206:assert response.headers.get('Content-Range')==f"bytes {begin}-{end}/{item['total_bytes']}"
                assert response.headers.get('x-goog-generation')==generation
                b=response.content
            assert len(b)==end-begin+1
            previous=old.read(len(b))
            if previous!=b:
                equal=False
                if offset is None:offset=begin+next((i for i,(a,c) in enumerate(zip(previous,b)) if a!=c),min(len(previous),len(b)))
            fresh.write(b);newsha.update(b);newmd5.update(b);size+=len(b);ranges+=1
            if len(prefix)<4:prefix=(prefix+b)[:4]
            suffix=(suffix+b)[-4:]
        if old.read(1):equal=False;offset=offset if offset is not None else size
        fresh.flush();os.fsync(fresh.fileno())
    after=baseline.stat();md5b64=base64.b64encode(newmd5.digest()).decode('ascii')
    assert prefix==suffix==b'PAR1' and md5b64==object_md5
    record={'name':name,'started_utc':start,'finished_utc':v.now(),'baseline':v.rel(baseline),'fresh_opaque_copy':v.rel(target),'expected_remote_bytes':item['total_bytes'],'received_bytes':size,'local_bytes':before.st_size,'byte_for_byte_equal':equal,'first_difference_byte_offset':offset,'fresh_sha256':newsha.hexdigest(),'local_sha256':oldsha.hexdigest(),'sha256_equal':newsha.digest()==oldsha.digest(),'fresh_md5_hex':newmd5.hexdigest(),'local_md5_hex':oldmd5.hexdigest(),'official_md5_base64':object_md5,'official_md5_matches_received':md5b64==object_md5,'official_md5_matches_local':base64.b64encode(oldmd5.digest()).decode('ascii')==object_md5,'expected_historical_local_sha256':expected[name],'local_matches_historical_manifest':oldsha.hexdigest()==expected[name],'baseline_size_mtime_unchanged':(before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'official_object_headers':safe,'row_content_decoded':False,'model_operations':0,'signed_url_archived':False,'transfer':'Finite sequential ranged recovery','range_requests_completed':ranges}
    v.dump(ATTEMPT/'per_file'/part.parts[0]/(part.name+'.json'),record);return record

def main():
    ATTEMPT.mkdir(exist_ok=False)
    completed=[v.read(p) for p in (RUN/'per_file').rglob('*.json')];names={x['name'] for x in completed}
    assert all(x['byte_for_byte_equal'] and x['sha256_equal'] and x['local_matches_historical_manifest'] for x in completed)
    expected=v.read(RUN/'baseline_manifests.json')['expected_historical_sha256'];before=v.read(RUN/'inventory_before.json')['files']
    pending=[x for x in before if x['name'] not in names]
    v.dump(ATTEMPT/'recovery_scope.json',{'author':'Codex','utc':v.now(),'first_attempt_complete_files_retained':sorted(names),'pending_only':[x['name'] for x in pending],'first_attempt_error_receipts_retained':True,'cause':'Transient transfer/API connection failures, followed by successful metadata connectivity check. Original closing inventory request had failed; no original final report was published.','chunk_bytes':BLOCK,'old_verifier_sha256':v.digest(REPO/'herramientas/verificar_bytes_parquet_oficiales_20261024.py'),'new_model_operations':0,'no_completed_file_redownload':True})
    v.credentials.load_configured_env_file();token=v.mcp_client.resolve_token();current=v.inventory(token)
    v.dump(ATTEMPT/'inventory_before.json',{'utc':v.now(),'files':current});assert current==before
    errors=[]
    for item in pending:
        try:
            rec=verify_file(item,token,expected);completed.append(rec)
            print(json.dumps({'file':item['name'],'bytes_equal':rec['byte_for_byte_equal'],'sha256_equal':rec['sha256_equal'],'total_verified_so_far':len(completed)},ensure_ascii=True),flush=True)
        except Exception as exc:
            err={'name':item['name'],'exception_type':type(exc).__name__,'message_omitted_to_avoid_signed_url_disclosure':True};errors.append(err);v.dump(ATTEMPT/'errors'/(PurePosixPath(item['name']).parts[0]+'_'+PurePosixPath(item['name']).name+'.json'),err)
            print(json.dumps({'file':item['name'],'status':'failed','exception_type':type(exc).__name__},ensure_ascii=True),flush=True)
    after=v.inventory(token);v.dump(RUN/'inventory_after.json',{'author':'Codex','utc':v.now(),'competition':v.COMP,'files':after})
    same=before==after;completed.sort(key=lambda x:x['name']);all_equal=len(completed)==24 and not errors and same and all(x['byte_for_byte_equal'] and x['sha256_equal'] and x['official_md5_matches_received'] and x['official_md5_matches_local'] and x['local_matches_historical_manifest'] and x['baseline_size_mtime_unchanged'] for x in completed)
    protected=v.read(RUN/'unmodified_state_before.json')['files']
    report={'author':'Codex','utc':v.now(),'competition':v.COMP,'scope':'24 activeParquet binary integrity only; no rows decoded','files_expected':24,'files_checked':len(completed),'errors':errors,'all_content_equal_to_historical_originals':all_equal,'inventory_metadata_stable_during_check':same,'different_files':[x['name'] for x in completed if not x['byte_for_byte_equal'] or not x['sha256_equal']],'historical_baseline_mismatches':[x['name'] for x in completed if not x['local_matches_historical_manifest']],'results':completed,'initial_network_failures_preserved':True,'initial_successes_not_repeated':len(names),'recovery_scope':v.rel(ATTEMPT/'recovery_scope.json'),'row_content_decoded':False,'new_model_fits':0,'new_predictions':0,'new_scores':0,'signed_urls_or_credentials_saved':False,'unmodified_state':[{'path':x['path'],'sha256':v.digest(ROOT/x['path'])} for x in protected]}
    v.dump(RUN/'report.json',report);print(json.dumps({'complete':True,'files_checked':len(completed),'all_content_equal':all_equal,'errors':len(errors),'initial_successes_not_repeated':len(names)},ensure_ascii=True),flush=True)
    if not all_equal:sys.exit(2)

if __name__=='__main__':main()
