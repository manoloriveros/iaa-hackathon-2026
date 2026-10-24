"""Descarga solo los 13 archivos emerging del inventario leído, sin envíos."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
from kaggle.api.kaggle_api_extended import KaggleApi

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
items = json.loads((BASE / 'fuentes/file_listing.json').read_text(encoding='utf-8'))
items = [x for x in items if x['name'].startswith('emerging/') and x['name'].endswith('.parquet')]
assert len(items) == 13
dest = ROOT / 'Datos/emerging'
dest.mkdir(parents=True, exist_ok=False)
api = KaggleApi()
api.authenticate()
records = []
for item in items:
    name = Path(item['name']).name
    assert '/' not in name and '\\' not in name
    api.competition_download_file('iaa-ai-assisted-hackathon-2026-part-2', item['name'], path=str(dest), quiet=True)
    target = dest / name
    assert target.is_file(), f'Falta {name}'
    assert target.stat().st_size == item['size'], f'Tamaño distinto: {name}'
    records.append({**item, 'local_path': target.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
    print(json.dumps({'archivo':name,'bytes':item['size'],'estado':'descargado'}, ensure_ascii=True), flush=True)
manifest = {'autor':'Codex','utc':datetime.now(timezone.utc).isoformat(),'source':'Kaggle competition_download_file','competition':'iaa-ai-assisted-hackathon-2026-part-2','files':records,'remote_sizes_verified':True,'remote_hashes_available':False,'training':False,'submissions':False}
(BASE / 'fuentes/download_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
