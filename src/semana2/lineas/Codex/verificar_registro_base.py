"""Comprueba las referencias y la conservación de estado tras registrar la base."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import unquote
import hashlib
import json
import re

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3'
BACK=RUN/'shared_state_before_registration'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})

index=json.loads((REPO/'registro/semana2_preparacion_actual.json').read_text(encoding='utf-8'))
for key in ['run','report','plan','documentation','producer','target','partitions','splits_directory','group_membership','claim_audit','precoverage_claims']:
    check('Index route '+key,(ROOT/index[key]).exists())
for key in ['report','plan','producer','target','partitions']:
    check('Index hash '+key,sha(ROOT/index[key])==index[key+'_sha256'])
paths=json.loads((ROOT/'RUTAS_PROYECTO.json').read_text(encoding='utf-8'))
oldpaths=json.loads((BACK/'RUTAS_PROYECTO.json').read_text(encoding='utf-8'))
check('Previous route values preserved',all(paths[k]==v for k,v in oldpaths.items()))
for key,value in paths.items():
    if key.startswith('week_2_'):check('Workspace route '+key,(ROOT/value).exists())
state=json.loads((ROOT/'Preparación/ESTADO_PROYECTO.json').read_text(encoding='utf-8'))
oldstate=json.loads((BACK/'Preparación/ESTADO_PROYECTO.json').read_text(encoding='utf-8'))
check('Historical state values preserved',all(state[k]==v for k,v in oldstate.items() if k not in ['memory_as_of','current_phase','collaboration_forum']))
check('Current phase points to verified base',state['current_phase']['current_state_key']=='week_2_base_preparation_20261023')
for relative in ['Preparación/MEMORIA_PROYECTO.md','Preparación/DECISIONES.md','Hackaton/Semana 2/README.md','Hackaton/Semana 2/PLAN_TRABAJO.md']:
    check('Prior text prefix preserved '+relative,(ROOT/relative).read_bytes().startswith((BACK/relative).read_bytes()))
forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_text(encoding='utf-8')
for ident in ['COD-S2-20261023-001','COD-S2-20261023-002','COD-S2-20261023-003']:
    check('Forum ID unique '+ident,forum.count('<!-- aporte:'+ident+' -->')==1)
receipts=json.loads((REPO/'registro/semana2_preparacion_foro.json').read_text(encoding='utf-8'))
report=json.loads((RUN/'report.json').read_text(encoding='utf-8'))
verified=json.loads((ROOT/index['separate_checker']['report']).read_text(encoding='utf-8'))
check('Decision before preparation',datetime.fromisoformat(receipts['prior_decision']['utc'])<datetime.fromisoformat(report['started_utc']))
check('Result after separate check',datetime.fromisoformat(receipts['result']['utc'])>datetime.fromisoformat(verified['utc']))
first=json.loads((RUN/'verification.json').read_text(encoding='utf-8'))
check('First failed checker retained with exact source',first['failed']==6 and sha(RUN/'first_checker_source_recovered.py')==first['code_sha256'])
check('Final checker passed',verified['passed']==106 and verified['failed']==0)
check('No model reported',not index['training_performed'] and not index['model_inference_performed'] and not report['training'])

docs=[REPO/'docs/semana2/PREPARACION_BASE.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md',ROOT/'Hackaton/Semana 2/Foro/FORO.md']
broken=[];n=0
for doc in docs:
    for m in re.finditer(r'\[[^\]]+\]\((<[^>]+>|[^\s)]+)\)',doc.read_text(encoding='utf-8')):
        target=m.group(1).strip('<>')
        if re.match(r'^[a-z]+://',target) or target.startswith('#'):continue
        n+=1
        if not (doc.parent/unquote(target.split('#')[0])).exists():broken.append({'document':str(doc.relative_to(ROOT)),'target':target})
check('Documentation local links',not broken,{'links':n,'broken':broken})
out={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scope':'Registration, chronology, documentation and preservation; not new model validation',
    'checks':checks,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks)}
with (RUN/'registration_verification.json').open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'passed':out['passed'],'failed':out['failed'],'local_links':n,'failures':[x for x in checks if not x['pass']]},ensure_ascii=True))
raise SystemExit(bool(out['failed']))
