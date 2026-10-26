"""Reproduce las entregas congeladas desde el paquete, sin ajuste ni fuentes externas."""
from pathlib import Path
import sys,json,hashlib
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'code'))
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
from scipy import optimize
from sklearn.linear_model import TweedieRegressor,PoissonRegressor,GammaRegressor
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import lightgbm as lgb
from semana2 import modelo_profesor_comun2023 as core
from semana2.modelos_robustos2023 import QuantileClipper
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((P/'manifest.json').read_text(encoding='utf-8'))
for item in manifest['files']:assert sha(P/item['path'])==item['sha256'],item['path']
def forbidden(*a,**k):raise AssertionError('Fit/optimización prohibido durante replay de paquete')
for cls in [TweedieRegressor,PoissonRegressor,GammaRegressor,OneHotEncoder,StandardScaler,SimpleImputer,ColumnTransformer,Pipeline,QuantileClipper,lgb.LGBMRegressor]:
 cls.fit=forbidden
 if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
optimize.minimize=forbidden
parts=[]
for line in core.FEATURES:
 b=joblib.load(P/f'models/R35_final_{line}.joblib');q=pq.read_table(P/f'quotes/{line}_2025.parquet',filters=[('year','=',2025)]).to_pandas()
 with threadpool_limits(limits=2):rate=core.predict(b,q,training=False)
 parts.append(pd.DataFrame({'row_id':q.row_id.to_numpy(),'prediction':rate*q.exposure.to_numpy()}))
baseline=pd.read_csv(P/'baseline.csv',dtype={'row_id':str},float_precision='round_trip');assert baseline.row_id.is_unique and len(baseline)==209063
teacher=baseline[['row_id']].merge(pd.concat(parts,ignore_index=True),on='row_id',validate='one_to_one',how='left');checks=[]
for model_id,filename,w in [('W2-COD-R36-FINAL','submission_R36_transfer50_GLM50_2025.csv',.5),('W2-COD-R37-FINAL','submission_R37_transfer25_GLM75_2025.csv',.25)]:
 saved=pd.read_csv(P/filename,dtype={'row_id':str},float_precision='round_trip');pred=(w*np.sqrt(teacher.prediction)+(1-w)*np.sqrt(baseline.prediction))**2
 assert saved.row_id.equals(baseline.row_id) and np.array_equal(saved.prediction,pred) and np.isfinite(pred).all() and (pred>=0).all()
 checks.append({'model_id':model_id,'rows':len(saved),'bit_exact_predictions':True,'CSV_sha256':sha(P/filename)})
for item in manifest['files']:assert sha(P/item['path'])==item['sha256']
report={'success':True,'new_fits':0,'fits_and_optimizer_forbidden':True,'only_packaged_inputs_read':True,'checks':checks,'2024_policy_or_metrics_read':False,'scope':'frozen2025quote reproduction; not new-model performance verification','professional_independent_validation':False}
with (P/'package_replay_receipt.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report))
