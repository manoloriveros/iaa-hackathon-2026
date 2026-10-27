"""Transporte unico del R1 admitido, con conciliacion de estado y sin reintento ciego."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, os, subprocess, sys
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
OUT=R/'privado/semana2/mision017_fase2/produccion_R1_privada_20261027'
SLUG='iaa-ai-assisted-hackathon-2026-part-2'
SHA='1f5967ec88b7198397b11f5a8e41d1d22f20d0f8fe64ba9799c246b9d796daed'
MESSAGE='Codex R1 private robustness: audited T2b frozen source; NB baseline, renewal own; no public tuning | 1f5967ec88b71983'
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):
    encoded=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    with (OUT/name).open('x',encoding='utf8') as f:f.write(encoded)
def source():
    admission=read(OUT/'admission.json');path=ROOT/admission['csv']
    assert admission['allow_one_submission'] and not admission['formal_promotion']
    assert sha(path)==admission['sha256']==SHA
    for name,digest in admission['evidence'].items():assert sha(ROOT/name)==digest,name
    seal=read(OUT/'submission_code_seal.json');assert seal['limpio'] and not seal['problemas']
    for name in seal['rutas_comprobadas']:
        p=R/name;committed=subprocess.run(['git','show',seal['commit']+':'+name],cwd=R,capture_output=True,check=True).stdout
        assert p.read_bytes()==committed,name
    return path
def api():
    assert os.environ.get('KAGGLE_SKILL_READ_ONLY')!='1'
    for key in ['VERBOSE','VERBOSE_OUTPUT','KAGGLE_API_ENVIRONMENT']:os.environ.pop(key,None)
    from kaggle.api.kaggle_api_extended import KaggleApi
    a=KaggleApi();a.authenticate();return a
def matches(rows):return [r for r in rows if r.file_name=='R1_T2b_2025.csv' or SHA[:16] in (r.description or '')]
def submit():
    path=source();assert not (OUT/'submission_started.json').exists(),'Reconcile existing start; never blind retry'
    a=api();limits=a.competition_get_submission_limits(SLUG);rows=a.competition_submissions(SLUG,page_size=100) or []
    lim={k:getattr(limits,k) for k in ['num_today','num_total','num_allowed_now','limited_by_total']}
    assert lim['num_allowed_now']>=1 and not matches(rows)
    pending=[r.ref for r in rows if str(r.status).rsplit('.',1)[-1] not in ['COMPLETE','ERROR','CANCELLED']]
    assert not pending,pending
    save('submission_started.json',{'utc':now(),'csv_sha256':SHA,'message':MESSAGE,'limits_before':lim,'max_new_submissions':1,'code_seal':read(OUT/'submission_code_seal.json')})
    try:
        response=a.competition_submit(str(path),MESSAGE,SLUG,quiet=True)
        save('submission_response.json',{'utc':now(),'competition':SLUG,'ref':response.ref,'message':response.message,'csv_sha256':SHA,'accepted_for_processing':response.ref>0})
        assert response.ref>0
        print(json.dumps({'accepted_for_processing':True,'ref':response.ref,'csv_sha256':SHA}),flush=True)
    except Exception as exc:
        save('submission_uncertain.json',{'utc':now(),'exception_type':type(exc).__name__,'next':'Reconcile exact message/file before any upload; never retry blindly'})
        raise
def check():
    path=source();assert (OUT/'submission_started.json').exists()
    if (OUT/'public_receipt.json').exists():print(json.dumps(read(OUT/'public_receipt.json')));return
    a=api();rows=a.competition_submissions(SLUG,page_size=100) or []
    ref=read(OUT/'submission_response.json')['ref'] if (OUT/'submission_response.json').exists() else None
    selected=[r for r in rows if r.ref==ref] if ref else matches(rows)
    assert len(selected)==1;row=selected[0]
    assert row.file_name==path.name and row.description==MESSAGE and row.total_bytes==path.stat().st_size
    status=str(row.status).rsplit('.',1)[-1];score=float(row.public_score) if row.public_score not in [None,''] else None
    limits=a.competition_get_submission_limits(SLUG)
    receipt={'author':'Codex','utc':now(),'competition':SLUG,'ref':row.ref,'status':status,'public_score':score,'error':row.error_description,
        'filename':row.file_name,'bytes':row.total_bytes,'csv_sha256':SHA,'message':row.description,
        'limits':{k:getattr(limits,k) for k in ['num_today','num_total','num_allowed_now','limited_by_total']},
        'private_score_not_read':True,'manual_final_selection':False,'formal_promotion':False,'B00_F3c_preserved':True}
    save('public_check_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json',receipt)
    if status=='COMPLETE':assert score is not None;save('public_receipt.json',receipt)
    print(json.dumps(receipt),flush=True)
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');arg=argparse.ArgumentParser();arg.add_argument('mode',choices=['submit','check']);args=arg.parse_args()
    globals()[args.mode]()
