"""Casos resolubles y guardas del flujo estándar; cero entrenamiento."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('v5_cases',REPO/'src/semana2/entrenar_desarrollo2023_v5.py')
v=importlib.util.module_from_spec(s);sys.modules[s.name]=v;s.loader.exec_module(v)
np,pd=v.np,v.pd
f=pd.DataFrame({'market':['m']*4,'line':['motor']*4,'row_id':range(4),'year':[2023]*4,'is_test':[False]*4,'fold':[0]*4,'T0':[4.,0.,9.,1.],
 'e_cost_mix_1.0':[1.,4.,9.,16.],'x_new_business':[0.,0.,1.,1.]})
checks=[]
def check(n,val):checks.append({'name':n,'pass':bool(val)})
def rejected(n,fn):
    try:fn();check(n,False)
    except (ValueError,AssertionError):check(n,True)
b,details=v.constant_fit(f,1)
check('Closed form 4/3 and 13/28',np.allclose([b['rates'][0],b['rates'][1]],[4/3,13/28],rtol=1e-15))
rejected('Training held-out row',lambda:v.constant_fit(f,0))
rejected('Training 2024',lambda:v.constant_fit(f.assign(year=2024),1))
rejected('Training test',lambda:v.constant_fit(f.assign(is_test=True),1))
rejected('Training repeated keys',lambda:v.constant_fit(pd.concat([f,f.iloc[:1]],ignore_index=True),1))
rejected('Unknown business',lambda:v.constant_fit(f.assign(x_new_business=2),1))
rejected('Missing business',lambda:v.constant_fit(f.assign(x_new_business=0),1))
rejected('All-zero segment',lambda:v.constant_fit(f.assign(T0=[4.,0.,0.,0.]),1))
rejected('Negative cost',lambda:v.constant_fit(f.assign(T0=[-1.,0.,9.,1.]),1))
rejected('Nonfinite exposure',lambda:v.constant_fit(f.assign(**{'e_cost_mix_1.0':[np.nan,4.,9.,16.]}),1))
rejected('Zero exposure',lambda:v.constant_fit(f.assign(**{'e_cost_mix_1.0':[0.,4.,9.,16.]}),1))
rejected('Negative exposure',lambda:v.constant_fit(f.assign(**{'e_cost_mix_1.0':[-1.,4.,9.,16.]}),1))
check('Prediction matches segment lookup',np.array_equal(v.predict(b,f),[4/3,4/3,13/28,13/28]))
check('Predictions ignore responses',np.array_equal(v.predict(b,f),v.predict(b,f.assign(T0=999))))
rejected('Predict unknown business',lambda:v.predict(b,f.assign(x_new_business=2)))
rejected('Predict 2024',lambda:v.predict(b,f.assign(year=2024)))
rejected('Predict test',lambda:v.predict(b,f.assign(is_test=True)))
rejected('GLM rejects year before fitting',lambda:v.glm_fit(f.assign(year=2024),1,{},'motor'))
rejected('GLM rejects held-out before fitting',lambda:v.glm_fit(f,0,{},'motor'))
# Identity between rate-target loss and total-unit loss for fractional exposure.
e=np.array([.01,.2,.75,1.]);y=np.array([0.,50.,1000.,5.]);r=np.array([20.,100.,200.,30.])
check('Tweedie homogeneity and single exposure',np.allclose(v.u.unit_deviance(y,e*r),np.sqrt(e)*v.u.unit_deviance(y/e,r),rtol=1e-13))
q=v.predict(b,f);mu=f['e_cost_mix_1.0'].to_numpy()*q
for biz in [0,1]:
 m=f.x_new_business.eq(biz).to_numpy();loss=v.u.unit_deviance(f.T0.to_numpy()[m],mu[m]).sum()
 check('Constant exact optimum '+str(biz),all(loss<=v.u.unit_deviance(f.T0.to_numpy()[m],mu[m]*z).sum()+1e-10 for z in [.5,.99,1.01,2.]))
result={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','checker_sha256':v.u.sha(Path(__file__)),'producer_sha256':v.u.sha(Path(v.__file__)),
 'fits':0,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'professional_independent_validation':False}
out=REPO/'privado/semana2/desarrollo2023/dev5_20261023T232328Z_69df9ead/fixture_checks.json'
with out.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'passed':result['passed'],'failed':result['failed'],'failures':[x for x in checks if not x['pass']]}));raise SystemExit(int(result['failed']>0))
