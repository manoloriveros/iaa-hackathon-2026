"""Casos adversos de información temporal, capital y factores, sin ajustar."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('v6_cases',REPO/'src/semana2/entrenar_desarrollo2023_v6.py')
v=importlib.util.module_from_spec(s);sys.modules[s.name]=v;s.loader.exec_module(v)
np,pd=v.np,v.pd
f=pd.DataFrame({'market':['m']*4,'line':['buildings']*4,'row_id':['a','b','c','d'],'year':[2023]*4,'is_test':[False]*4,'fold':[0,0,1,1],
 'x_log_sum_insured':[np.log(1e5),np.log(2e5),np.nan,np.nan],'x_new_business':[0.,1.,0.,1.],'T0':[0.,10.,99.,12.]})
raw=pd.DataFrame({'row_id':['a','b','c','d'],'sum_insured':[1e5,2e5,3e8,6e8],'written_premium':[100.,200.,300.,600.]})
checks=[]
def check(n,val):checks.append({'name':n,'pass':bool(val)})
def reject(n,fn):
    try:fn();check(n,False)
    except (ValueError,AssertionError):check(n,True)
p,r=v.a.capital_frame(f,raw,1,5e6)
check('Scale divisor and training bounds',r['fit_ppm_min']==r['fit_ppm_max']==1. and np.allclose(p.x_log_sum_insured.iloc[2:],[np.log(3e5),np.log(6e5)]))
check('Unflagged values exact',p.x_log_sum_insured.iloc[:2].equals(f.x_log_sum_insured.iloc[:2]))
mut=raw.copy();mut.loc[2:,'written_premium']*=100
pm,rm=v.a.capital_frame(f,mut,1,5e6);check('Validation tariff does not fit bounds',rm['fit_ppm_min']==r['fit_ppm_min'] and rm['fit_ppm_max']==r['fit_ppm_max'])
check('Unsubstantiated correction stays missing',pm.x_log_sum_insured.iloc[2:].isna().all())
py,ry=v.a.capital_frame(f.assign(T0=9999),raw,1,5e6);check('Correction does not read loss',np.allclose(py.x_log_sum_insured,p.x_log_sum_insured,equal_nan=True) and ry==r)
reject('Capital rejects2024',lambda:v.a.capital_frame(f.assign(year=2024),raw,1,5e6))
reject('Capital rejects test',lambda:v.a.capital_frame(f.assign(is_test=True),raw,1,5e6))
reject('Capital rejects duplicate raw ID',lambda:v.a.capital_frame(f,pd.concat([raw,raw.iloc[:1]]),1,5e6))
reject('Capital rejects mixed line',lambda:v.a.capital_frame(f.assign(line=['buildings','motor','buildings','buildings']),raw,1,5e6))
reject('Capital rejects invalid training premium',lambda:v.a.capital_frame(f,raw.assign(written_premium=[0.,200.,300.,600.]),1,5e6))
dates=pd.Series(pd.to_datetime(['2023-06-01','2023-09-01']))
check('Past-source temporal control',v.a.weather_guard(dates,[2021,2021],[2021],[True,True]))
reject('Climate2024 in2023',lambda:v.a.weather_guard(dates,[2024,2024],[2021],[True,True]))
reject('Climate same calendar year',lambda:v.a.weather_guard(dates,[2023,2023],[2021],[True,True]))
reject('Selector trained with2025',lambda:v.a.weather_guard(dates,[2021,2021],[2023,2024,2025],[True,True]))
reject('Selector future despite past values',lambda:v.a.weather_guard(dates,[2021,2021],[2024],[True,True]))
reject('No history means no future backfill',lambda:v.a.weather_guard(dates,[2021,2021],[2021],[False,True]))
reject('Quote previous year cutoff',lambda:v.a.weather_guard(pd.Series(pd.to_datetime(['2022-12-20'])),[2022],[2021],[True]))
reject('Auxiliary rejects retained fold before any fitting',lambda:v.a.auxiliary_fit(None,None,raw,f,None,'buildings',1))
reject('Auxiliary rejects2024 before fitting',lambda:v.a.auxiliary_fit(None,None,raw,f.assign(year=2024),None,'buildings',1))
b={'family':'CredibilityRate','c':.7,'parent':{'family':'constant_line_rate','rate':100.}}
check('Credibility only changes new business',np.array_equal(v.predict(b,f),[100.,70.,100.,70.]))
check('Pricing ignores loss',np.array_equal(v.predict(b,f),v.predict(b,f.assign(T0=0))))
reject('Credibility rejects negative c',lambda:v.predict(dict(b,c=-1.),f))
reject('Credibility rejects nonfinite c',lambda:v.predict(dict(b,c=np.nan),f))
reject('Credibility rejects2024',lambda:v.predict(b,f.assign(year=2024)))
reject('Credibility rejects test',lambda:v.predict(b,f.assign(is_test=True)))
reject('Credibility rejects unknown business',lambda:v.predict(b,f.assign(x_new_business=2)))
result={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','checker_sha256':v.u.sha(Path(__file__)),'producer_sha256':v.u.sha(Path(v.__file__)),
 'auxiliary_code_sha256':v.u.sha(Path(v.a.__file__)),'fits':0,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'professional_independent_validation':False}
out=REPO/'privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b/fixture_checks.json'
with out.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'passed':result['passed'],'failed':result['failed'],'failures':[x for x in checks if not x['pass']]}));raise SystemExit(int(result['failed']>0))
