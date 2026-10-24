"""Casos matemáticos y adversos focales de la receta v4, sin entrenar."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('v4_cases',REPO/'src/semana2/entrenar_desarrollo2023_v4.py')
v=importlib.util.module_from_spec(s);sys.modules[s.name]=v;s.loader.exec_module(v)
np,pd=v.np,v.pd
f=pd.DataFrame({'market':['m']*4,'line':['motor']*4,'row_id':range(4),'year':[2023]*4,'is_test':[False]*4,'fold':[0]*4,
 'group_id':['a','a','b','b'],'T0':[4.,0.,9.,1.],'e_cost_mix_1.0':[1.]*4,'x_new_business':[0.,0.,1.,1.]})
rate=np.array([1.,4.,9.,16.]);checks=[]
def check(name,val):checks.append({'name':name,'pass':bool(val)})
def rejected(name,call):
    try:call();check(name,False)
    except (ValueError,AssertionError):check(name,True)
r=v.business_factor(f,rate,1);check('Analytic q=4/3 and 13/28',np.allclose([x['q'] for x in r],[4/3,13/28],rtol=1e-15))
rejected('Held-out training rows',lambda:v.business_factor(f,rate,0))
rejected('2024',lambda:v.business_factor(f.assign(year=2024),rate,1))
rejected('Test row',lambda:v.business_factor(f.assign(is_test=True),rate,1))
rejected('Zero positive events in segment',lambda:v.business_factor(f.assign(T0=[4.,0.,0.,0.]),rate,1))
rejected('Missing segment',lambda:v.business_factor(f.assign(x_new_business=0),rate,1))
rejected('Negative response',lambda:v.business_factor(f.assign(T0=[-1.,0.,9.,1.]),rate,1))
rejected('Zero exposure',lambda:v.business_factor(f.assign(**{'e_cost_mix_1.0':[0.,1.,1.,1.]}),rate,1))
rejected('Nonfinite rate',lambda:v.business_factor(f,np.array([1.,np.nan,9.,16.]),1))
rejected('Invalid shape',lambda:v.business_factor(f,rate[:3],1))
rejected('Repeated row key',lambda:v.business_factor(pd.concat([f,f.iloc[:1]],ignore_index=True),np.append(rate,1),1))
b={'family':'BusinessLevelRate','factors':{0:2.,1:3.},'parent':{'family':'AnchoredRate','shape_weight':.5,'reference_rate':2.,'scale':1.,'parent':{'family':'constant_line_rate','rate':2.}}}
check('Business lookup and exact rate',np.array_equal(v.predict(b,f),[4.,4.,6.,6.]))
check('Response-invariant prediction',np.array_equal(v.predict(b,f),v.predict(b,f.assign(T0=0))))
rejected('Predict 2024',lambda:v.predict(b,f.assign(year=2024)))
rejected('Predict invalid business',lambda:v.predict(b,f.assign(x_new_business=2)))
rejected('Predict invalid factor',lambda:v.predict(dict(b,factors={0:-1.,1:3.}),f))
drop,n=v.stress_group_ids(f.assign(T0=[9.,1.,6.,6.]),1);check('Stress ranks whole component total',n==2 and drop.group_id.tolist()==['b'])
drop,n=v.stress_group_ids(f.assign(T0=[6.,6.,6.,6.]),1);check('Stress tie ascending group ID',drop.group_id.tolist()==['a'])
rejected('Stress rejects held-out',lambda:v.stress_group_ids(f,0))
rejected('Stress rejects 2024',lambda:v.stress_group_ids(f.assign(year=2024),1))
check('Original multi-model key context',not pd.concat([f.assign(model_id='A'),f.assign(model_id='B')]).duplicated(['model_id',*v.KEY]).any())
result={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','code_sha256':v.u.sha(Path(__file__)),'producer_sha256':v.u.sha(Path(v.__file__)),
 'checks':checks,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'fits':0,'professional_independent_validation':False}
target=REPO/'privado/semana2/desarrollo2023/dev4_20261023T204811Z_4adcedec/fixture_checks.json'
with target.open('x',encoding='utf-8') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps(result));raise SystemExit(int(result['failed']>0))
