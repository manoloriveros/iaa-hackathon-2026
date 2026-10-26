"""Inspección de coeficientes guardados2023, sin inferir, puntuar o reajustar."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import joblib,numpy as np,pandas as pd
OUT=R/'privado/semana2/robustez2023/mision017_20261025_v1/calibration_coefficient_audit.json';assert not OUT.exists();rows=[];sources=[]
for line in ['motor','buildings','contents']:
 folder='ciclo7_20261025_v1' if line=='buildings' else 'ciclo6_20261025_v1';ident='W2-COD-R35' if line=='buildings' else 'W2-COD-R32'
 for k in range(5):
  p=R/f'privado/semana2/robustez2023/{folder}/models/{ident}_{line}_fold{k}.joblib';b=joblib.load(p);names=['new_business']+list(b['region_encoder'].get_feature_names_out())+['intercept'];assert len(names)==len(b['coef'])
  for name,v in zip(names,b['coef']):rows.append({'line':line,'fold':k,'term':name,'coefficient':float(v),'multiplicative_effect':float(np.exp(v))})
  sources.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
f=pd.DataFrame(rows);summary=[]
for (line,term),g in f.groupby(['line','term']):summary.append({'line':line,'term':term,'min':float(g.coefficient.min()),'max':float(g.coefficient.max()),'median':float(g.coefficient.median()),'same_sign_5folds':bool((g.coefficient>0).all()or(g.coefficient<0).all())})
report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scope':'existing2023offsetGLMcoefficients,no newprediction/score/fit','current_ridge':1.,'ridge_bias_or_optimal_regularization_not_proven':True,'rows':rows,'summary':summary,'sources':sources,'2024_artifacts_read':False}
with OUT.open('x',encoding='utf-8') as h:json.dump(report,h,ensure_ascii=False,indent=2)
print(json.dumps({'scope':report['scope'],'summary':summary}))
