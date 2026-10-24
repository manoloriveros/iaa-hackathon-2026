"""Casos conocidos del ancla, contracción y límites de información."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,json,sys,tempfile
REPO=Path(__file__).resolve().parents[1]
source=REPO/'src/semana2/entrenar_desarrollo2023_v3.py'
spec=importlib.util.spec_from_file_location('tested_dev3',source);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
np,pd=m.np,m.pd;checks=[]
def check(name,value):checks.append({'name':name,'pass':bool(value)})
def rejects(name,fn):
    try:fn()
    except ValueError:check(name,True)
    else:check(name,False)
e=np.array([.5,1.,.5]);r=np.array([1.,3.,2.]);ref=np.array([2.,2.,2.])
s=m.anchor_scale(e,r,ref)
check('Known scale 8/9',np.isclose(s,8/9,rtol=0,atol=1e-15))
check('Training total anchored',np.isclose(np.dot(e,s*r),np.dot(e,ref)))
mixed=.5*ref+.5*s*r
check('Contraction keeps training total',np.isclose(np.dot(e,mixed),np.dot(e,ref)))
check('Contraction halves deviations',np.allclose(mixed-ref,.5*(s*r-ref)))
check('Annual-rate ordering retained',np.array_equal(np.argsort(r),np.argsort(mixed)))
rejects('Zero exposure rejected',lambda:m.anchor_scale([0,1],r[:2],ref[:2]))
rejects('Nonpositive rate rejected',lambda:m.anchor_scale(e,[1,0,2],ref))
rejects('Nonfinite rate rejected',lambda:m.anchor_scale(e,[1,np.inf,2],ref))
rejects('Mismatched rows rejected',lambda:m.anchor_scale(e,r[:2],ref))
frame=pd.DataFrame({'market':['emerging']*3,'line':['motor']*3,'row_id':['a','b','c'],
                    'year':[2023]*3,'is_test':[False]*3,'fold':[1,2,3],'e_cost_mix_1.0':e,'T0':[0.,10.,100.]})
parent={'family':'constant_line_rate','rate':2.,'columns':[]};reference={'family':'constant_line_rate','rate':4.,'columns':[]}
factor,details,_=m.fit_anchor(frame,parent,reference,0)
check('Training factor from predictions only',factor==2.)
poisoned,_,_=m.fit_anchor(frame.assign(T0=[np.nan,np.inf,-1.]),parent,reference,0)
check('Response poisoning leaves factor unchanged',factor==poisoned)
without_labels,_,_=m.fit_anchor(frame.drop(columns='T0'),parent,reference,0)
check('No outcome column required',factor==without_labels)
rejects('Held-out row rejected before factor',lambda:m.fit_anchor(frame.assign(fold=0),parent,reference,0))
rejects('2024 factor rejected',lambda:m.fit_anchor(frame.assign(year=2024),parent,reference,0))
rejects('Invalid reference rejected',lambda:m.fit_anchor(frame,parent,dict(reference,family='wrong'),0))
bundle={'family':'AnchoredRate','parent':parent,'reference_rate':4.,'scale':factor,'shape_weight':.5}
check('Synthetic adapter known rate',np.array_equal(m.predict(bundle,frame),np.full(3,4.)))
rejects('2024 adapter prediction rejected',lambda:m.predict(bundle,frame.assign(year=2024)))
rejects('Test adapter prediction rejected',lambda:m.predict(bundle,frame.assign(is_test=True)))
rejects('Undeclared mixing weight rejected',lambda:m.predict(dict(bundle,shape_weight=.25),frame))
with tempfile.TemporaryDirectory(prefix='level_fixture_',dir=REPO/'privado/semana2/desarrollo2023') as tmp:
    p=Path(tmp)/'adapter.joblib';m.joblib.dump(bundle,p)
    check('Adapter serialization exact',np.array_equal(m.predict(m.joblib.load(p),frame),m.predict(bundle,frame)))
m.block_base_fits()
try:m.u.TweedieRegressor().fit(np.ones((2,1)),np.ones(2))
except RuntimeError:check('Base fit spy rejects attempted fit',m.BASE_FIT_ATTEMPTS==1)
else:check('Base fit spy rejects attempted fit',False)
result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'source_sha256':m.u.sha(source),'checks':checks,
 'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),
 'actual_base_estimator_fits':0,'synthetic_base_fit_attempts_blocked':m.BASE_FIT_ATTEMPTS,'real_data_calibrations_or_scores':0}
with (REPO/'registro/semana2_desarrollo2023_pruebas_v3.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=True));assert result['failed']==0
