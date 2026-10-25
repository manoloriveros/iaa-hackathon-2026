"""Comparación binaria opaca. No importa Parquet, modelos, tablas, métricas o años."""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.parse import urlparse
import base64,hashlib,json,os,sys,requests

ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/integridad_oficial/contenido_20261024_v1'
COMP='iaa-ai-assisted-hackathon-2026-part-2'
SKILL=ROOT/'.agents/skills/kaggle';sys.path.insert(0,str(SKILL))
from shared import credentials,mcp_client
now=lambda:datetime.now(timezone.utc).isoformat()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
rel=lambda p:p.relative_to(ROOT).as_posix()

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def inventory(token):
    result=mcp_client.request('list_competition_data_files',{'competitionName':COMP,'pageSize':200},token=token)
    if not result.ok or not isinstance(result.data,dict):raise RuntimeError('Inventory request failed')
    if result.data.get('next_page_token'):raise RuntimeError('Inventory truncated')
    return sorted([{'name':f['name'],'total_bytes':int(f['total_bytes']),'creation_date':f.get('creation_date')} for f in result.data.get('files',[]) if isinstance(f,dict) and f.get('name','').startswith(('developed/','emerging/')) and f['name'].endswith('.parquet')],key=lambda x:x['name'])

def official_md5(headers):
    for value in headers.get('x-goog-hash','').split(','):
        value=value.strip()
        if value.startswith('md5='):return value[4:]
    return None

def one(item,token,expected_hashes):
    name=item['name'];part=PurePosixPath(name)
    assert part.parts[0] in ['developed','emerging'] and len(part.parts)==2 and part.name.endswith('.parquet')
    assert '..' not in part.parts and '\\' not in name
    baseline=(ROOT/'Hackaton/Semana 1/Datos'/part.name) if part.parts[0]=='developed' else ROOT/'Hackaton/Semana 2/Datos/emerging'/part.name
    baseline=baseline.resolve();assert baseline.is_relative_to(ROOT.resolve()) and baseline.is_file()
    target=(RUN/'opaque_downloads'/Path(*part.parts)).resolve();assert target.is_relative_to((RUN/'opaque_downloads').resolve())
    target.parent.mkdir(parents=True,exist_ok=True);partial=target.with_name(target.name+'.partial')
    start=now();stat_before=baseline.stat();expected=expected_hashes.get(name)
    result=mcp_client.request('download_competition_data_file',{'competitionName':COMP,'fileName':name},token=token)
    if not result.ok or not isinstance(result.data,dict):raise RuntimeError('Download URL request failed')
    url=result.data.get('url');assert isinstance(url,str) and urlparse(url).scheme=='https' and urlparse(url).hostname=='storage.googleapis.com'
    remote_sha=hashlib.sha256();local_sha=hashlib.sha256();remote_md5=hashlib.md5();local_md5=hashlib.md5()
    count=0;local_count=0;equal=True;first_difference=None;prefix=b'';suffix=b''
    with requests.get(url,stream=True,timeout=(20,90)) as response:
        if response.status_code!=200:raise RuntimeError('Unexpected download status '+str(response.status_code))
        assert urlparse(response.url).hostname=='storage.googleapis.com'
        if response.headers.get('Content-Encoding','identity') not in ['identity','']:raise RuntimeError('Unexpected content encoding')
        safeheaders={k:v for k,v in response.headers.items() if k.lower() in ['content-length','content-type','etag','x-goog-generation','x-goog-hash','last-modified']}
        server_md5=official_md5(response.headers)
        with baseline.open('rb') as local,partial.open('xb') as fresh:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if not chunk:continue
                if count+len(chunk)>item['total_bytes']:raise RuntimeError('Body exceeds listed size')
                old=local.read(len(chunk));local_count+=len(old)
                if old!=chunk:
                    equal=False
                    if first_difference is None:
                        first_difference=count+next((i for i,(a,b) in enumerate(zip(old,chunk)) if a!=b),min(len(old),len(chunk)))
                local_sha.update(old);local_md5.update(old);remote_sha.update(chunk);remote_md5.update(chunk);fresh.write(chunk)
                if len(prefix)<4:prefix=(prefix+chunk)[:4]
                suffix=(suffix+chunk)[-4:];count+=len(chunk)
            while True:
                extra=local.read(1024*1024)
                if not extra:break
                if first_difference is None:first_difference=count
                equal=False;local_count+=len(extra);local_sha.update(extra);local_md5.update(extra)
            fresh.flush();os.fsync(fresh.fileno())
    if count!=item['total_bytes']:raise RuntimeError('Body shorter than listed size')
    if prefix!=b'PAR1' or suffix!=b'PAR1':raise RuntimeError('Not an opaque Parquet container')
    if server_md5 is None:raise RuntimeError('Official object checksum absent')
    md5b64=base64.b64encode(remote_md5.digest()).decode('ascii')
    if md5b64!=server_md5:raise RuntimeError('Official object checksum differs from received bytes')
    os.replace(partial,target);stat_after=baseline.stat()
    record={'name':name,'started_utc':start,'finished_utc':now(),'baseline':rel(baseline),'fresh_opaque_copy':rel(target),'expected_remote_bytes':item['total_bytes'],'received_bytes':count,'local_bytes':local_count,'byte_for_byte_equal':equal,'first_difference_byte_offset':first_difference,'fresh_sha256':remote_sha.hexdigest(),'local_sha256':local_sha.hexdigest(),'sha256_equal':remote_sha.digest()==local_sha.digest(),'fresh_md5_hex':remote_md5.hexdigest(),'local_md5_hex':local_md5.hexdigest(),'official_md5_base64':server_md5,'official_md5_matches_received':md5b64==server_md5,'official_md5_matches_local':base64.b64encode(local_md5.digest()).decode('ascii')==server_md5,'expected_historical_local_sha256':expected,'local_matches_historical_manifest':local_sha.hexdigest()==expected,'baseline_size_mtime_unchanged':(stat_before.st_size,stat_before.st_mtime_ns)==(stat_after.st_size,stat_after.st_mtime_ns),'official_object_headers':safeheaders,'row_content_decoded':False,'model_operations':0,'signed_url_archived':False}
    dump(RUN/'per_file'/part.parts[0]/(part.name+'.json'),record)
    return record

def main():
    RUN.mkdir(parents=True,exist_ok=False)
    dump(RUN/'scope.json',{'author':'Codex','utc':now(),'user_request':'verifica el contenido','method':'Official download to isolated opaque directory; direct byte comparison and streamingSHA256/MD5 against unchanged originals and historicalSHA256 manifests. No Parquet decoder or model/dataframe code.','permission_scope':'Binary integrity only, including opaque multiyear/test containers; no row values, predictions, prices, scores,ledger,2024 validation or training.','active_data_overwritten':False,'quarantine':rel(RUN/'opaque_downloads'),'concurrency':3})
    em_manifest=ROOT/'Hackaton/Semana 2/Codex/fuentes/download_manifest.json'
    dev_manifest=ROOT/('Preparaci'+chr(243)+'n')/'artifacts/verification/iaa_launch_20261016/data_manifest.json'
    em=read(em_manifest);dev=read(dev_manifest)
    expected={x['name']:x['sha256'] for x in em['files']}
    expected.update({'developed/'+PurePosixPath(x['path']).name:x['sha256'] for x in dev['files']})
    assert len(expected)==24
    dump(RUN/'baseline_manifests.json',{'author':'Codex','utc':now(),'sources':[{'path':rel(p),'sha256':digest(p)} for p in [em_manifest,dev_manifest]],'expected_historical_sha256':expected})
    protected=[REPO/'registro/semana2_desarrollo2023_actual.json',REPO/'registro/semana2_contadores_propios_actual.json',REPO/'registro/semana2_continuidad_nocturna.json']
    dump(RUN/'unmodified_state_before.json',{'files':[{'path':rel(p),'sha256':digest(p)} for p in protected]})
    credentials.load_configured_env_file();token=mcp_client.resolve_token();before=inventory(token)
    assert {x['name'] for x in before}==set(expected) and sum(x['total_bytes'] for x in before)<1024**3
    dump(RUN/'inventory_before.json',{'author':'Codex','utc':now(),'competition':COMP,'files':before})
    results=[];errors=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        tasks={pool.submit(one,item,token,expected):item['name'] for item in before}
        for task in as_completed(tasks):
            name=tasks[task]
            try:
                result=task.result();results.append(result)
                print(json.dumps({'file':name,'bytes_equal':result['byte_for_byte_equal'],'sha256_equal':result['sha256_equal'],'historical_manifest_match':result['local_matches_historical_manifest']},ensure_ascii=True),flush=True)
            except Exception as exc:
                error={'name':name,'exception_type':type(exc).__name__,'error_message_omitted_to_avoid_signed_url_or_credential_disclosure':True};errors.append(error);dump(RUN/'errors'/(PurePosixPath(name).parts[0]+'_'+PurePosixPath(name).name+'.json'),error)
                print(json.dumps({'file':name,'status':'failed','exception_type':type(exc).__name__},ensure_ascii=True),flush=True)
    after=inventory(token);dump(RUN/'inventory_after.json',{'author':'Codex','utc':now(),'competition':COMP,'files':after})
    same_inventory=before==after;results.sort(key=lambda x:x['name'])
    all_equal=len(results)==24 and not errors and same_inventory and all(x['byte_for_byte_equal'] and x['sha256_equal'] and x['official_md5_matches_received'] and x['official_md5_matches_local'] and x['local_matches_historical_manifest'] and x['baseline_size_mtime_unchanged'] for x in results)
    report={'author':'Codex','utc':now(),'competition':COMP,'scope':'24 activeParquet binary integrity; no semantic decoding of2024/test or any model operations','files_expected':24,'files_checked':len(results),'errors':errors,'all_content_equal_to_historical_originals':all_equal,'inventory_metadata_stable_during_check':same_inventory,'different_files':[x['name'] for x in results if not x['byte_for_byte_equal'] or not x['sha256_equal']],'historical_baseline_mismatches':[x['name'] for x in results if not x['local_matches_historical_manifest']],'results':results,'row_content_decoded':False,'new_model_fits':0,'new_predictions':0,'new_scores':0,'signed_urls_or_credentials_saved':False,'unmodified_state':[{'path':rel(p),'sha256':digest(p)} for p in protected]}
    dump(RUN/'report.json',report)
    print(json.dumps({'complete':True,'files_checked':len(results),'files_expected':24,'all_content_equal':all_equal,'errors':len(errors),'inventory_stable':same_inventory,'report':rel(RUN/'report.json')},ensure_ascii=True),flush=True)
    if not all_equal:sys.exit(2)

if __name__=='__main__':main()
