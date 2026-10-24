"""Comprueba integridad del corte, rutas y enlaces de la documentación nueva."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import unquote
import hashlib
import json
import re

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
WEEK=BASE.parent
checks=[]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,value,detail=None):
    checks.append({'name':name,'pass':bool(value),'detail':detail})

idx=json.loads((WEEK/'Foro/historial/indice_semana1.json').read_text(encoding='utf-8'))
snapshot=ROOT/idx['snapshot']
check('Snapshot hash',sha(snapshot)==idx['sha256'])
check('Source forum prefix preserved',(ROOT/'foros/FORO.md').read_bytes().startswith(snapshot.read_bytes()))
markers=re.findall(rb'<!-- aporte:([^>]+) -->',snapshot.read_bytes())
check('260 historical comment IDs, unique',len(markers)==260 and len(set(markers))==260)
check('Forum helper unchanged',sha(WEEK/'Foro/comentar.py')==sha(ROOT/'foros/comentar.py'))
receipts=json.loads((BASE/'recibos_foro.json').read_text(encoding='utf-8'))
check('New forum opening receipt',sha(WEEK/'Foro/FORO.md')==receipts['new_forum']['sha256'])
check('Old forum bridge receipt',sha(ROOT/'foros/FORO.md')==receipts['old_forum_bridge']['sha256'])

manifest=json.loads((BASE/'fuentes/download_manifest.json').read_text(encoding='utf-8'))
for f in manifest['files']:
    p=WEEK/f['local_path']
    check('Emerging '+p.name,p.exists() and p.stat().st_size==f['size'] and sha(p)==f['sha256'])
check('13 emerging files',len(manifest['files'])==13 and len(list((WEEK/'Datos/emerging').glob('*.parquet')))==13)
check('26562843 emerging bytes',sum(f['size'] for f in manifest['files'])==26562843)
diagnostic=json.loads((BASE/'diagnostico_inicial.json').read_text(encoding='utf-8'))
for f in diagnostic['local_originals']:
    check('Preserved original '+f['name'],sha(WEEK/'Datos'/f['name'])==sha(ROOT/'Hackaton/Semana 1/Datos'/f['name'])==f['sha256'])
check('Sample and tests',diagnostic['submission_contract']['sample_set_equals_test'] and diagnostic['submission_contract']['test_rows']==209063)
extended=json.loads((BASE/'hallazgos_ampliados.json').read_text(encoding='utf-8'))
check('452 exposure flags',sum(f['above_one'] for f in extended['exposure'].values())==452)

paths=json.loads((ROOT/'RUTAS_PROYECTO.json').read_text(encoding='utf-8'))
for k,v in paths.items():
    if k.startswith('week_2_'): check('Route '+k,(ROOT/v).exists())
oldpaths=json.loads((BASE/'respaldo_apertura/RUTAS_PROYECTO.json').read_text(encoding='utf-8'))
check('Existing route values preserved',all(paths[k]==v for k,v in oldpaths.items()))
state=json.loads((ROOT/'Preparación/ESTADO_PROYECTO.json').read_text(encoding='utf-8'))
oldstate=json.loads((BASE/'respaldo_apertura/Preparación/ESTADO_PROYECTO.json').read_text(encoding='utf-8-sig'))
check('Historical state values preserved',all(state[k]==v for k,v in oldstate.items() if k not in ['memory_as_of','collaboration_forum']))
check('Current phase points to week2',state['current_phase']['current_state_key']=='week_2_opening_20261023')
check('Old forum state preserved',state['week_2_opening_20261023']['previous_forum_state']==oldstate['collaboration_forum'])

docs=[WEEK/'README.md',WEEK/'PLAN_TRABAJO.md',WEEK/'CONTRATO_SEMANA2.md',BASE/'DIAGNOSTICO_INICIAL.md',WEEK/'Foro/README.md',WEEK/'Foro/HISTORIAL_RELEVANTE.md',WEEK/'Foro/FORO.md']
broken=[];total=0
for doc in docs:
    text=doc.read_text(encoding='utf-8')
    for m in re.finditer(r'\[[^\]]+\]\((<[^>]+>|[^\s)]+)\)',text):
        target=m.group(1).strip('<>')
        if re.match(r'^[a-z]+://',target) or target.startswith('#'): continue
        total+=1
        p=(doc.parent/unquote(target.split('#')[0])).resolve()
        if not p.exists(): broken.append({'document':str(doc.relative_to(ROOT)),'target':target})
check('New documentation local links',not broken,{'links':total,'broken':broken})

for p in BASE.glob('*.py'):
    compile(p.read_text(encoding='utf-8'),str(p),'exec')
check('Python source compiles',True)
for p in (BASE/'fuentes').glob('*.json'):
    json.loads(p.read_text(encoding='utf-8'))
check('Source JSON parses',True)

result={'autor':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scope':'Integrity, routes, preserved history, links and source compilation; not target/model approval or independent validation',
    'checks':checks,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'training':False}
(BASE/'verificacion_apertura.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':result['passed'],'failed':result['failed'],'failures':[x for x in checks if not x['pass']],'local_links':total},ensure_ascii=True))
raise SystemExit(bool(result['failed']))
