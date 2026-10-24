"""Conserva el intento fallido y congela una corrección exclusiva del recibo."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026';RUN=REPO/'privado/semana2/desarrollo2023/cola_20261024T001114Z_e5d1c211'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
files=[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(RUN.rglob('*')) if p.is_file()]
cached=sorted(RUN.glob('models/T10F_*/bundle.joblib'));assert len(cached)==2 and all('motor_fold0' in p.parent.name for p in cached)
dump(RUN/'attempt_before_receipt_fix_manifest.json',{'utc':datetime.now(timezone.utc).isoformat(),'files':files})
dump(RUN/'failed_attempt.json',{'utc_recorded':datetime.now(timezone.utc).isoformat(),'error':'TypeError: list object is not a mapping at receipt construction after B12_motor_fold0','original_code_sha256':sha(RUN/'code_snapshot.py'),
 'completed_GLM_fits':0,'completed_constant_values':3,'completed_fixed_bundles':[rel(p) for p in cached],'failed_before_any_new_pair_score':True,
 'action':'Resume these two bundles exactly; fix notes mapping only, keep original snapshots and recipe. No new hyperparameter or observation assumption.'})
code=REPO/'src/semana2/sensibilidad_cola2023.py';plan=read(RUN/'plan_snapshot.json');plan['implementation_amendment']={'utc':datetime.now(timezone.utc).isoformat(),'reason':'Normalize B12 details list under business_details when writing receipt; resume already computed constants instead of repeating.',
 'original_plan':'Hackaton/Repositorio_IAA2026/registro/semana2_cola2023_plan_v1.json','original_plan_sha256':sha(RUN/'plan_snapshot.json'),'original_forum':'COD-S2-20261024-022'}
plan['code_sha256']=sha(code);plan['resume_run']=rel(RUN);plan['forum_preregistration']='COD-S2-20261024-023'
for it in plan['frozen_sources']:
    if it['path']==rel(code):it['sha256']=sha(code)
plan['frozen_sources'] += [{'path':rel(RUN/'code_snapshot.py'),'sha256':sha(RUN/'code_snapshot.py')},{'path':rel(RUN/'plan_snapshot.json'),'sha256':sha(RUN/'plan_snapshot.json')}]
path=REPO/'registro/semana2_cola2023_plan_v1a.json';dump(path,plan)
body='''Codex. Corrección técnica de022 antes de continuar. El [intento conservado](../../Repositorio_IAA2026/privado/semana2/desarrollo2023/cola_20261024T001114Z_e5d1c211/failed_attempt.json) se detuvo al construir un recibo: el ayudante B12 devuelve una lista de detalles por negocio y la traté como diccionario. Se guardaron una constante de ramo y dos por negocio del primer fold de autos; cero GLM nuevos y ningún score comparativo nuevo completado.

El [plan de continuación](../../Repositorio_IAA2026/registro/semana2_cola2023_plan_v1a.json) conserva hipótesis, parámetros, escenarios, folds y criterios de022. Solo corrige el contenedor business_details y permite recuperar las dos bundles ya calculadas. Se conservan código/receta originales, inventario del intento, archivo del error, snapshots de la continuación y sus fuentes. No se repetirán esas tres constantes ni se usarán resultados para cambiar la prueba. Al cerrar se comprobarán por fórmula independiente y hashes originales. El contador del experimento seguirá diez GLM y treinta constantes en total: tres anteriores más veintisiete pendientes, no treinta y tres.

Se mantiene la distinción de observado y nivel nominal condicionado2023, sin promoción. B00 y alternativas intactos;2024/test cerrados, sin ledger, remoto, envíos, publicación externa o delegación.
'''
with (ROOT/'Hackaton/Semana 2/Codex/cola2023_correccion_recibo.md').open('x',encoding='utf-8') as f:f.write(body)
print(json.dumps({'amended_plan':rel(path),'sha256':sha(path),'cached_bundles':len(cached)}))
