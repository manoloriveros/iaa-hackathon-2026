"""Casos conocidos del consumidor; ningún ajuste real ni acceso a etiquetas 2024."""
from pathlib import Path
import importlib.util
import json
import sys
import tempfile
from datetime import datetime, timezone

REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
source=REPO/'src/semana2/entrenar_desarrollo2023.py'
spec=importlib.util.spec_from_file_location('dev2023_tested',source)
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
np,pd,pq,pa=module.np,module.pd,module.pq,module.pa
checks=[]
def check(name,condition):
    checks.append({'name':name,'pass':bool(condition)})
def rejects(name,fn):
    try:fn()
    except ValueError:check(name,True)
    else:check(name,False)

y=np.array([0.,1.,16.,100.]);mu=np.array([1.,1.,4.,25.])
check('Known-answer p1.5 unit deviance',np.allclose(module.unit_deviance(y,mu),[4.,0.,8.,20.]))
check('Separate sklearn metric',np.isclose(module.unit_deviance(y,mu).mean(),module.mean_tweedie_deviance(y,mu,power=1.5)))
e=np.array([.01,.25,.5,1.]);r=np.array([5.,10.,20.,30.])
check('Total-rate loss identity',np.allclose(module.unit_deviance(y,e*r),np.sqrt(e)*module.unit_deviance(y/e,r)))
rejects('Nonpositive predictions rejected',lambda:module.unit_deviance(y,[0.,1.,4.,25.]))
rejects('Negative response rejected',lambda:module.unit_deviance([-1.],[1.]))
frame=pd.DataFrame({'market':['emerging']*4,'line':['motor']*4,'row_id':['a','b','c','d'],
                    'year':[2023]*4,'is_test':[False]*4,'T0':y,'e_cost_mix_1.0':e})
b,details=module.fit_bundle({'family':'constant_line_rate'},frame,{'all':[]})
expected=np.sum(y/np.sqrt(e))/np.sqrt(e).sum()
check('Constant equals total-loss optimum',np.isclose(b['rate'],expected))
check('Constant differs from actuarial ratio',not np.isclose(b['rate'],y.sum()/e.sum()))
optloss=module.unit_deviance(y,e*b['rate']).sum()
check('Constant beats both local perturbations',all(optloss<module.unit_deviance(y,e*b['rate']*factor).sum() for factor in [.99,1.01]))
bad=frame.assign(year=2024)
for family in ['constant_line_rate','TweedieRegressor','LGBMRegressor']:
    rejects('Reject 2024 before fit '+family,lambda family=family:module.fit_bundle({'family':family},bad,{'all':[]}))
rejects('Reject 2024 before prediction',lambda:module.predict_bundle(b,bad))
rejects('Reject test marked as 2023',lambda:module.predict_bundle(b,frame.assign(is_test=True)))
rejects('Duplicate row keys rejected',lambda:module.assert_2023(pd.concat([frame,frame.iloc[:1]],ignore_index=True)))
parent=REPO/'privado/semana2/desarrollo2023';parent.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='synthetic_loader_',dir=parent) as tmp:
    path=Path(tmp)/'synthetic.parquet'
    mixed=pd.concat([frame,bad.assign(row_id=['w','x','z','q'],T0=1e99)],ignore_index=True)
    pq.write_table(pa.Table.from_pandas(mixed,preserve_index=False),path)
    result=module.load_2023(path)
    check('Loader year predicate ignores poisoned other year',len(result)==4 and result.year.eq(2023).all() and np.array_equal(result.T0,y))
result={'utc':datetime.now(timezone.utc).isoformat(),'scope':'Synthetic known-answer and temporal guard cases only',
        'source':module.relative(source),'source_sha256':module.sha(source),'checks':checks,
        'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'real_pricing_models_fitted':0}
out=REPO/'registro/semana2_desarrollo2023_pruebas_v1.json'
with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=True))
assert result['failed']==0
