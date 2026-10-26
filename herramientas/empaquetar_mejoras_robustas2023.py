"""Paquete local privado de entregas ya procesadas; sin nuevas predicciones o ajustes."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,zipfile,importlib.metadata
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';D=R/'privado/semana2/robustez2023/entrega_20261025_v1';OUT=R/'privado/semana2/robustez2023/paquete_20261025_v1';P=OUT/'content'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
assert not OUT.exists();P.mkdir(parents=True)
ready=json.loads((D/'ready.json').read_text(encoding='utf-8'));copies=[]
def copy(src,dst):
 dst=P/dst;dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();shutil.copyfile(src,dst);assert sha(src)==sha(dst);copies.append({'source':rel(src),'package_path':dst.relative_to(P).as_posix(),'sha256':sha(dst)})
for item in ready['CSV']:
 src=ROOT/item['path'];assert sha(src)==item['sha256'];copy(src,src.name)
copy(R/'privado/semana2/modelo_final_g4_2023/final_20261024_v1/attempt1/submission_g4_glm_2023_2025.csv','baseline.csv')
for line in ['motor','buildings','contents']:
 copy(D/f'models/R35_final_{line}.joblib',f'models/R35_final_{line}.joblib');copy(D/f'quotes/{line}_2025.parquet',f'quotes/{line}_2025.parquet')
for p in sorted((R/'src/semana2').glob('*.py')):copy(p,'code/semana2/'+p.name)
copy(R/'herramientas/replay_paquete_robusto2023.py','replay.py')
for name in ['public_check02.json','ready.json','separate_process_replay.json']:copy(D/name,'evidence/'+name)
copy(R/'privado/semana2/robustez2023/ciclo7_20261025_v1/report.json','evidence/OOF_2023_original_report.json')
packages=['numpy','pandas','scipy','scikit-learn','lightgbm','joblib','threadpoolctl']
versions={x:importlib.metadata.version(x) for x in packages};(P/'environment.json').write_text(json.dumps(versions,indent=2),encoding='utf-8')
(P/'README.md').write_text('''# Entregas propias congeladas, 25 de octubre de 2026

Paquete local privado. R36: envío Kaggle 57629589, COMPLETE, público 0,14331. R37: 57629584, COMPLETE, público 0,13956. Original G4: 0,13310. No hay cambio de selección final manual ni publicación externa de código/modelos.

R36 tiene D² OOF2023 0,11053677 frente a B20 0,08938179; pasa las cribas exploratorias originales en cinco folds y seis segmentos. R37 conserva la preferencia conservadora preinscrita. Los intervalos de esta búsqueda adaptativa no equivalen a confirmación independiente; el avance público es modesto y no demuestra el salto grande pedido.

Los tres modelos contienen sus profesores fuente2023 y adaptadores emergentes2023. Los CSV combinan sus precios con baseline.csv en raíz cuadrada con pesos fijos 0,5 o 0,25. Se conservan C0/capital y todos los artefactos previos. La fuente no amplía soporte emergente; su objetivo incurrido observado no es último independientemente identificado. Los atributos físicos siguen condicionados al maestro suministrado.

replay.py verifica cada SHA, bloquea ajustes/optimización y reproduce ambos CSV desde modelos y cotizaciones congelados incluidos aquí. Requiere las versiones de environment.json y pyarrow. No lee cohortes, métricas, ledger o actas de 2024, ni necesita datos de entrenamiento, red o credenciales. Solo certifica la reproducción de estas cotizaciones, no inferencias sobre cotizaciones nuevas o rendimiento futuro. Guardar la salida package_replay_receipt.json; no repetir sin una incertidumbre o cambio material.

Todos los archivos con datos permanecen privados y fuera de Git. No cargar este ZIP como dataset o notebook público. Autor: Codex, sin aprobación profesional independiente inventada.
''',encoding='utf-8')
manifest={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','files':[{'path':p.relative_to(P).as_posix(),'sha256':sha(p)} for p in sorted(P.rglob('*')) if p.is_file()]}
(P/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
zip_path=OUT/'modelo_propio_robusto2023_privado.zip'
with zipfile.ZipFile(zip_path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(P.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(P).as_posix())
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 for item in manifest['files']:assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
 z.extractall(OUT/'extracted_replay')
receipt={'utc':manifest['utc'],'zip':rel(zip_path),'zip_sha256':sha(zip_path),'bytes':zip_path.stat().st_size,'files':len(manifest['files'])+1,'all_archive_bytes_verified':True,'new_fits':0,'new_submissions':0,'copies':copies}
(OUT/'build_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in receipt.items() if k!='copies'}))
