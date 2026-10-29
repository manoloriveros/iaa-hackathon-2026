"""Oráculos escalares del estimador de completitud y normalizadores nuevos."""
from pathlib import Path
import importlib.util, json, hashlib
from datetime import datetime,timezone
import numpy as np
import pandas as pd

REPO=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('protected',REPO/'herramientas/validar_cadena_f3c.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
v.verify_inputs();checks={}
asg=pd.DataFrame({'row_id':['a','b','c'],'accepted':[True,True,True],'line':['motor']*3,'peril':['bodily_injury']*3,'loss_date':pd.to_datetime(['2021-01-01']*3),'report_date':pd.to_datetime(['2021-01-01','2021-01-03','2021-01-02']),'net':[1.,3.,1000.]})
rows=pd.DataFrame({'row_id':['a','b']});f=v.curves(asg,rows)[('motor','bodily_injury')]
checks['weighted_CDF_manual']=np.array_equal(f[:4],np.array([.25,.25,1.,1.]))
poison=asg.copy();poison.loc[poison.row_id.eq('c'),'net']=1e8
checks['excluded_cost_not_in_curve']=np.array_equal(f,v.curves(poison,rows)[('motor','bodily_injury')])
left=v.curves(asg,pd.DataFrame({'row_id':['a']}))[('motor','bodily_injury')]
checks['own_scope_changes_curve']=not np.array_equal(f,left) and (left==1).all()
tr=pd.DataFrame({'row_id':['a','b'],'period_start':pd.to_datetime(['2024-12-30','2024-12-30']),'period_end':pd.to_datetime(['2024-12-31','2024-12-31']),'exposure':[2/365,2/365],'y_bodily_injury':[1.,3.]})
q,qt,w=v.completion(tr,tr,'motor',{('motor','bodily_injury'):f})
checks['day_integration_manual']=np.array_equal(q,np.array([.25,.25])) and np.array_equal(q,qt) and w=={'bodily_injury':1.}
t=pd.DataFrame({'line':['motor']*4,'new_business':[False]*4,'y':[0.,3.,10.,7.],'exposure':[.2,.5,.8,1.],'q':[.7,.8,.9,.95],'gender':['M','F','M','F'],'ncb_years':[0,1,5,8],'prior_claims_5y':[0,1,0,2],'works_from_home':[False]*4,'marketing_segment':['x']*4})
m=np.array([5.,10.,8.,12.]);t['base']=m
for kind,key,lines in [('ae',v.ks(t,'ncb'),None),('tw',v.ks(t,'gender'),['motor'])]:
    p=v.factor_train(t,m,kind,key,lines);ap=v.factor_apply(t,m,key,p)
    checks[kind+'_train_total_preserved']=abs(ap.sum()-m.sum())<1e-12
    parts=np.r_[v.factor_apply(t.iloc[:2],m[:2],key[:2],p),v.factor_apply(t.iloc[2:],m[2:],key[2:],p)]
    checks[kind+'_application_batch_invariant']=np.array_equal(parts,ap)
shape=v.shape_train(t,m);s=v.shape_apply(t,m,shape)
checks['shape_train_total_preserved']=abs(s.sum()-m.sum())<1e-12
checks['shape_application_batch_invariant']=np.array_equal(np.r_[v.shape_apply(t.iloc[:2],m[:2],shape),v.shape_apply(t.iloc[2:],m[2:],shape)],s)
pred,pars=v.recipe(t,t.copy());unknown=t.copy();unknown['y']=99999
pred2,pars2=v.recipe(t,unknown)
checks['whole_recipe_held_y_invariant']=pars==pars2 and all(np.array_equal(pred[k],pred2[k]) for k in pred)
assert all(checks.values()),checks
v.save(v.RUN/'oraculos_escalares.json',{'utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'all_passed':True,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_or_model_fits':0,'new_scores2024':0})
print(json.dumps(v.clean(checks)))
