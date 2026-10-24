"""Conserva el foro anterior íntegro y crea índice, sin editar sus aportes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
source=ROOT/'foros/FORO.md'
data=source.read_bytes()
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
history=BASE.parent/'Foro/historial'
history.mkdir(parents=True,exist_ok=True)
target=history/f'FORO_semana1_{stamp}.md'
with target.open('xb') as f:
    f.write(data)
assert target.read_bytes()==data
lines=data.decode('utf-8-sig').splitlines()
entries=[]
current_heading=None
for number,line in enumerate(lines,1):
    if line.startswith('## '):
        current_heading=line[3:]
    m=re.fullmatch(r'<!-- aporte:([^>]+) -->',line)
    if m:
        entries.append({'id':m.group(1),'heading':current_heading,'marker_line':number})
index={'autor_registro':'Codex','snapshot_utc':datetime.now(timezone.utc).isoformat(),
    'source':'foros/FORO.md','snapshot':target.relative_to(ROOT).as_posix(),
    'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'aporte_count':len(entries),
    'ids_unique':len({x['id'] for x in entries})==len(entries),'aportes':entries,
    'scope':'Copia literal del corte; el foro original puede recibir aportes posteriores.'}
with (history/'indice_semana1.json').open('x',encoding='utf-8') as f:
    json.dump(index,f,ensure_ascii=False,indent=2);f.write('\n')
helper=ROOT/'foros/comentar.py'
with (BASE.parent/'Foro/comentar.py').open('xb') as f:
    f.write(helper.read_bytes())
print(json.dumps({k:v for k,v in index.items() if k!='aportes'},ensure_ascii=True))
