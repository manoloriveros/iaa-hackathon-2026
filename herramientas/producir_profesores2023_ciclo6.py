"""Seis ajustes fuente2023 preinscritos, independientes de etiquetas emergentes."""
from pathlib import Path
import sys,json,hashlib,os
from datetime import datetime,timezone
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/ciclo6_20261025_v1'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_profesor2023 as m
import pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
 p=json.loads((R/'registro/semana2_robustez2023_ciclo6_plan.json').read_text(encoding='utf-8'))
 assert (OUT/'forum_prior_receipt.json').exists()
 assert not (OUT/'teachers_started.json').exists(),'Conciliar productor antes de repetir'
 for it in p['sources']:assert sha(ROOT/it['path'])==it['sha256'],it['path']
 (OUT/'teachers_started.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'source_fit_budget':6}),encoding='utf-8')
 (OUT/'teachers').mkdir();receipts=[]
 for line in m.FEATURES:
  f=pq.read_table(R/f'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1/{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas()
  with threadpool_limits(limits=2):teachers,receipt=m.fit_teachers(f,line)
  for mid,bundle in teachers.items():
   path=OUT/f'teachers/{mid}_{line}.joblib';joblib.dump(bundle,path,compress=3)
   with threadpool_limits(limits=2):
    a=m.teacher_rate(bundle,f.iloc[:50]);b=m.teacher_rate(joblib.load(path),f.iloc[:50])
    assert (a==b).all()
  receipts.append(receipt)
  with (OUT/f'teachers/{line}_receipt.json').open('x',encoding='utf-8') as h:json.dump(receipt,h,indent=2)
  print(json.dumps({'source_line':line,'source_rows':len(f),'source_fits':2,'teacher_replay_exact':True}),flush=True)
 for it in p['sources']:assert sha(ROOT/it['path'])==it['sha256'],it['path']
 with (OUT/'teachers_ready.json').open('x',encoding='utf-8') as h:json.dump({'source_price_fits':6,'source_years':[2023],'emerging_label_rows_read':0,'2024_policy_rows_read':0,'receipts':receipts},h,indent=2)


if __name__=='__main__':main()
