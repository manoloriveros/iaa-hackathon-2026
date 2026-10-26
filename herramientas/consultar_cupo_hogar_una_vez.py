"""Una lectura de cuota de la sesión activa, respetando el backoff ya guardado."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,json,hashlib,time,os
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/comparacion_publica_hogar_20261025_v1'
read=lambda p:json.loads(p.read_text(encoding='utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();now=lambda:datetime.now(timezone.utc)
queue=read(OUT/'queue_followup4.json');deadline=datetime.fromisoformat(queue['retry_not_before_utc']);delay=(deadline-now()).total_seconds();assert 0<=delay<=1800
started=OUT/'single_deferred_quota_started.json';done=OUT/'single_deferred_quota_complete.json';assert not started.exists() and not done.exists()
helper=R/'herramientas/enviar_comparacion_hogar2023_v2.py';spec=importlib.util.spec_from_file_location('own_readonly_quota_preflight',helper);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
with started.open('x',encoding='utf8') as h:json.dump({'utc':now().isoformat(),'pid':os.getpid(),'not_before_utc':deadline.isoformat(),'one_query_only':True,'action':'preflight only; noPOST orscore read','helper_sha256':sha(helper),'queue_sha256':sha(OUT/'queue_followup4.json')},h,indent=2)
print(json.dumps({'state':'live_wait_before_one_readonly_preflight','pid':os.getpid(),'not_before_utc':deadline.isoformat(),'max_remaining_seconds':int(delay)}),flush=True)
while True:
 remaining=(deadline-now()).total_seconds()
 if remaining<=0:break
 time.sleep(min(30.,remaining))
module.preflight()
with done.open('x',encoding='utf8') as h:json.dump({'utc':now().isoformat(),'readonly_preflight_returned':True,'query_runs':1,'new_price_fits':0,'new_submissions':0,'new_public_scores':0,'recurring_job_created':False},h,indent=2)
