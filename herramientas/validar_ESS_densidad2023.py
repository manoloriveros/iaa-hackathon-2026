"""Segundo método de ESS en el ámbito decisivo, sin ajustes ni precios."""
from pathlib import Path
import sys,json,hashlib,math,importlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
cycle=int(sys.argv[1]);assert cycle in [34,35];OUT=R/f'privado/semana2/robustez2023/ciclo{cycle}_20261025_v1';assert not (OUT/'ESS_independent_check.json').exists()
m=importlib.import_module('semana2.modelo_fuente_densidad'+('_templada' if cycle==35 else '')+'2023')
import pyarrow.parquet as pq,joblib,numpy as np,lightgbm as lgb,scipy.optimize
from sklearn.linear_model import TweedieRegressor
from threadpoolctl import threadpool_limits
read=lambda p:json.loads(p.read_text(encoding='utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(OUT/'plan.json');pre=read(OUT/'combined_weight_preflight.json');scope=(min if pre['all_pass'] else max)(pre['checks'],key=lambda x:x['combined_weight_ESS_fraction'])
for x in plan['sources']:assert sha(ROOT/x['path'])==x['sha256']
def forbidden(*a,**k):raise AssertionError('No price fitting or inference in ESS control')
TweedieRegressor.fit=lgb.LGBMRegressor.fit=scipy.optimize.minimize=m.fit_source=m.fit=m.predict=m.teacher_rate=forbidden
cols=m.KEY+['year','is_test','exposure']+m.domain_model.columns('motor');f=pq.read_table(R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1/motor_2023.parquet',columns=cols,filters=[('year','=',2023)]).to_pandas();b=pq.read_table(R/'privado/semana2/robustez2023/bloques_fuente2023_v1/motor.parquet',columns=m.KEY+['source_fold']).to_pandas();f=f.merge(b,on=m.KEY,how='left',validate='one_to_one')
if scope['role']=='pilot':f=f[f.source_fold.ne(scope['fold'])].copy()
d=joblib.load(R/f'privado/semana2/robustez2023/prefiltro_dominio2023_v3/models/motor_fold{scope["fold"]}.joblib')
with threadpool_limits(limits=2):w,wr=m.weights(f,d)
assert wr['weights_joblib_hash']==scope['weights_joblib_hash'];mean=math.fsum(map(float,w))/len(w);variance=math.fsum((float(x)-mean)**2 for x in w)/len(w);other=1/(1+variance/mean**2)
assert abs(other-scope['combined_weight_ESS_fraction'])<1e-12 and bool(other>=.5)==pre['all_pass']
result={'cycle':cycle,'scope':{'fold':scope['fold'],'role':scope['role']},'weight_hash_matches_original':True,'ESS_fraction_original_dot_method':scope['combined_weight_ESS_fraction'],'ESS_fraction_independent_fsum_variance_method':other,'baseline_ESS_fraction':scope['baseline_sqrt_exposure_ESS_fraction'],'decision_unchanged':True,'gate_pass':bool(other>=.5),'new_price_fit_calls':0,'new_price_inference_calls':0,'new_domain_fits':0,'new_C0_fits':0,'costs_C0_not_loaded':True,'price_fitting_inference_optimizers_blocked':True,'control_code_sha256':sha(Path(__file__))}
with (OUT/'ESS_independent_check.json').open('x',encoding='utf8') as h:json.dump(result,h,indent=2)
print(json.dumps(result))
