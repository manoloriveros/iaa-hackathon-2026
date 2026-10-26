"""Proceso separado, ajustes prohibidos, dos CSV completos reconstruidos."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/entrega_20261025_v1'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
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
def forbidden(*a,**k):raise AssertionError('Fit/optimización prohibido durante replay')
for cls in [TweedieRegressor,PoissonRegressor,GammaRegressor,OneHotEncoder,StandardScaler,SimpleImputer,ColumnTransformer,Pipeline,QuantileClipper,lgb.LGBMRegressor]:
 cls.fit=forbidden
 if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
optimize.minimize=forbidden
plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'));ready=json.loads((OUT/'ready.json').read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for x in plan['sources']:assert sha(ROOT/x['path'])==x['sha256']
parts=[];modelhashes={}
for line in core.FEATURES:
 p=OUT/f'models/R35_final_{line}.joblib';modelhashes[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
 b=joblib.load(p);q=pq.read_table(OUT/f'quotes/{line}_2025.parquet',filters=[('year','=',2025)]).to_pandas()
 with threadpool_limits(limits=2):rate=core.predict(b,q,training=False)
 parts.append(pd.DataFrame({'row_id':q.row_id.to_numpy(),'prediction':rate*q.exposure.to_numpy()}))
sample=pq.read_table(ROOT/'Hackaton/Semana 2/Datos/emerging/sample_submission.parquet',columns=['row_id']).to_pandas()
teacher=sample.merge(pd.concat(parts,ignore_index=True),on='row_id',validate='one_to_one',how='left')
baseline=pd.read_csv(ROOT/'Hackaton/Repositorio_IAA2026/privado/semana2/modelo_final_g4_2023/final_20261024_v1/attempt1/submission_g4_glm_2023_2025.csv',dtype={'row_id':str},float_precision='round_trip')
checks=[]
for spec in ready['CSV']:
 saved=pd.read_csv(ROOT/spec['path'],dtype={'row_id':str},float_precision='round_trip');w=spec['weight']
 reconstructed=(w*np.sqrt(teacher.prediction)+(1-w)*np.sqrt(baseline.prediction))**2
 assert len(saved)==209063 and saved.row_id.equals(sample.row_id) and np.array_equal(saved.prediction,reconstructed)
 assert sha(ROOT/spec['path'])==spec['sha256']
 checks.append({'model_id':spec['model_id'],'rows':len(saved),'replay_exact':True,'CSV_sha256':spec['sha256']})
assert all(sha(ROOT/p)==v for p,v in modelhashes.items())
report={'success':True,'independent_process':True,'fits_forbidden':True,'new_fits':0,'all_model_hashes_unchanged':True,
        'checks':checks,'model_hashes':modelhashes,'2024_rows_read':0,'professional_independent_validation':False}
with (OUT/'separate_process_replay.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
