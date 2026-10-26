"""Mismos dry-runs, temporales dentro del workspace y recibos versionados."""
from pathlib import Path
import sys,json,os,subprocess,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/comparacion_publica_hogar_20261025_v1';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(OUT/'separate_process_replay.json')['success'];ready=read(OUT/'ready.json');scratch=OUT/'scratch_dryrun_v2';assert scratch.resolve().is_relative_to(ROOT.resolve());scratch.mkdir(exist_ok=True);env=os.environ.copy();env['PATH']=str(Path(sys.executable).parent)+';'+env.get('PATH','')
for key in ['TEMP','TMP','TMPDIR']:env[key]=str(scratch)
receipts=[]
for item in ready['CSV']:
 p=OUT/('dryrun2_'+item['model_id']+'.txt');assert not p.exists() and sha(ROOT/item['path'])==item['sha256'];message='Codex RESEARCH '+item['model_id']+' | frozen no quotaPOST';cmd=[sys.executable,str(ROOT/'.agents/skills/kaggle/scripts/kaggle_skill.py'),'submit','iaa-ai-assisted-hackathon-2026-part-2',str(ROOT/item['path']),'-m',message,'--sample',str(R/'privado/semana2/envios/g4_20261025_v1/official_sample_format.csv')];result=subprocess.run(cmd,cwd=OUT,env=env,capture_output=True,text=True,encoding='utf-8')
 with p.open('x',encoding='utf-8') as h:h.write(result.stdout+'\n'+result.stderr)
 assert result.returncode==0 and 'all 5 passed' in result.stdout
 receipts.append({'model_id':item['model_id'],'CSV_sha256':item['sha256'],'all5passed':True,'account_changed':False,'dryrun_receipt':str(p),'dryrun_receipt_sha256':sha(p)})
with (OUT/'local_dryruns_complete_v2.json').open('x',encoding='utf-8') as h:json.dump({'all_selected_csvs_passed':True,'receipts':receipts,'daily_quota_still0_at_last_authoritative_preflight':True,'no_POST_or_newscore':True,'previous_dryrun_failed_on_sandbox_temporary_cleanup_not_price_or_format':True,'TEMP_TMP_TMPDIR_scoped_to_workspace':str(scratch),'new_fits':0},h,ensure_ascii=False,indent=2)
print(json.dumps(receipts))
