"""Casos conocidos para truncamiento, reserva, fechas y exclusión de variables."""
from pathlib import Path
import importlib.util
import hashlib
import json
from datetime import datetime, timezone

REPO=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('s2vu',REPO/'src/semana2/variables_ultimo.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
pd,np=m.pd,m.np
checks=[]
def check(name,ok):
    checks.append({'name':name,'pass':bool(ok)});assert ok,name
def rejects(name,fn,text):
    try:fn()
    except ValueError as e:check(name,text in str(e))
    else:check(name,False)

model,w=m.fit_reporting([1,1,2,2,3,3],[10]*6,[10]*6,[0]*6)
check('Untruncated product-limit equals empirical CDF',np.allclose(model['count_cdf'],[1/3,2/3,1]))
check('Constant marks preserve count CDF',np.allclose(model['count_cdf'],model['cost_cdf']['1.0']))
check('Probability weights normalized',abs(w.sum()-6)<1e-12)
delay=[1,1,3,1,1,3];age=[1,3,3,1,3,3]
model,w=m.fit_reporting(delay,age,[10,10,30,10,10,30],[0,0,20,0,0,20])
check('Right truncation corrects empirical two-thirds to one-half',np.allclose(model['count_cdf'],[.5,1]))
check('Cost-delay dependence gives cost CDF one-quarter',np.allclose(model['cost_cdf']['1.0'],[.25,1]))
check('Reserve075 changes marks once',np.isclose(model['cost_cdf']['0.75'][0],2/7))
check('Reserve125 changes marks once',np.isclose(model['cost_cdf']['1.25'][0],2/9))
check('Ties have same probability weight',w[0]==w[1]==w[3]==w[4])
rejects('Invalid truncation rejects',lambda:m.fit_reporting([3]*6,[1]*6,[10]*6,[0]*6),'imposible')
rejects('Negative reserve stress rejects',lambda:m.fit_reporting([1]*6,[2]*6,[1]*6,[10]*6),'negativa')
rejects('No data leakage fallback for tiny group',lambda:m.fit_reporting([1]*4,[2]*4,[1]*4,[0]*4),'cinco')
periods=pd.DataFrame({'period_start':pd.to_datetime(['2024-12-29','2025-01-01']),
    'period_end':pd.to_datetime(['2024-12-30','2025-12-31']),'is_test':[False,True]})
check('Inclusive daily count completion',np.allclose(m.average_completion(periods,model),[.5,1]))
check('Inclusive daily cost completion',np.allclose(m.average_completion(periods,model,'cost'),[.25,1]))
check('Tail stress affects observed link only, not nominal prediction',np.allclose(m.average_completion(periods,model,'cost',1.,.1),[.225,1]))
weather=pd.DataFrame({'address_id':['A']*3,'year':[2023,2024,2025],**{c:[7.,9.,11.] for c in m.WEATHER}})
pp=pd.DataFrame({'market':['emerging']*3,'line':['motor']*3,'row_id':['R1','R2','R3'],'address_id':['A']*3,
    'period_start':pd.to_datetime(['2025-01-01','2025-01-02','2023-06-01']),'days_quote_to_inception':[1,1,1]})
past=m.historical_weather(pp,weather)
check('Quote in December uses 2023, quote in January uses 2024',past.weather_source_year.tolist()==[2023,2024,2022])
check('Missing prior year remains missing',pd.isna(past.wq_hail_days.iloc[2]))
poison=weather.copy();poison.loc[poison.year.eq(2025),m.WEATHER]=1e50
check('Future weather values cannot alter past block',past.equals(m.historical_weather(pp,poison)))

base=REPO/'privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3'
data=m.ROOT/'Hackaton/Semana 2/Datos/emerging'
customers=m.pq.read_table(data/'customers.parquet').to_pandas()
addresses=m.pq.read_table(data/'addresses.parquet').to_pandas()
raw=m.pq.read_table(base/'periods_policies_buildings.parquet').to_pandas()
raw=pd.concat([raw.loc[raw.sum_insured.le(1e7)].head(2),raw.loc[raw.sum_insured.gt(1e7)].head(2)],ignore_index=True)
f,spec,a=m.make_features(raw,customers,addresses,'buildings')
check('Uncertain high capital masked without dividing raw',f.x_log_sum_insured.iloc[2:].isna().all() and raw.sum_insured.iloc[2:].gt(1e7).all())
bad=raw.copy()
for c in ['written_premium','customer_service_contacts','discount_applied','renewal_decision','missed_payments_12m']:bad[c]='poison'
cm=customers.copy()
for c in ['gender','occupation','prior_claims_5y','licence_points','marketing_segment']:cm[c]='poison'
ff,_,_=m.make_features(bad,cm,addresses,'buildings')
check('Excluded price, outcome and profile changes cannot affect F0',f.equals(ff))
check('Feature names exactly match frozen x whitelist',all(x.startswith('x_') for x in spec['all']) and not any(x.removeprefix('x_') in m.BLOCKED for x in spec['all']))

result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'passed':len(checks),'failed':0,'checks':checks,
    'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'pricing_models_trained':0,
    'scope':'Known-answer and metamorphic tests, not professional independent validation'}
path=REPO/'registro/semana2_variables_ultimo_pruebas.json'
with path.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'passed':len(checks),'failed':0,'output':str(path.relative_to(m.ROOT))},ensure_ascii=True))
