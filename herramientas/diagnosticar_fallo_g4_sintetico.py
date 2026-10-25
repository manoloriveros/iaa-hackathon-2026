"""Investigación mínima de fallos del intento1, exclusivamente sobre el fixture."""
from pathlib import Path
import os,sys,json
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='2'
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
sys.path.insert(0,str(REPO/'src'));sys.path.insert(0,str(REPO/'herramientas'))
import numpy as np,pandas as pd
from scipy.optimize import minimize
from threadpoolctl import threadpool_limits
from semana2 import flujo_g4_sintetico2023 as f
from probar_flujo_g4_sintetico2023 import poison,data_guard
RUN=REPO/'privado/semana2/desarrollo2023/g4_flujo_sintetico_20261024_v1'

def diff(a,b,path=''):
    rows=[]
    if isinstance(a,dict) and isinstance(b,dict):
        for key in a.keys()|b.keys():rows+=diff(a.get(key),b.get(key),path+'/'+key)
    elif isinstance(a,list) and isinstance(b,list):
        if len(a)!=len(b):rows.append({'path':path,'lengths':[len(a),len(b)]})
        else:
            for i,(x,y) in enumerate(zip(a,b)):rows+=diff(x,y,path+'/'+str(i))
    elif a!=b:rows.append({'path':path,'clean':a,'poisoned':b,'types':[type(a).__name__,type(b).__name__]})
    return rows

def main():
    f.reset_work();sources={'fixture':'a'*64};r={}
    with threadpool_limits(limits=2),data_guard():
        p,c=f.fixture();p2,c2=poison(p,c,[0,1])
        a=f.fit_scope(p,c,[0,1],sources);b=f.fit_scope(p2,c2,[0,1],sources)
        r['differences']=diff(json.loads(f.canonical(f.live_state(a))),json.loads(f.canonical(f.live_state(b))))
        r['synthetic_work']=f.WORK.copy();refs=[]
        rate=np.array([1.,2.,4.,8.,16.]);e=np.array([.2,.4,.6,.8,1.]);m=float(np.sum(e*np.log(rate))/e.sum());z=np.log(rate)-m
        for expected in [0.,.4,1.]:
            y=e*np.exp(.2+m+expected*z)
            def joint(v):
                mu=e*np.exp(v[0]+m+v[1]*z);g=np.sqrt(mu)-y/np.sqrt(mu)
                return float(f.deviance(y,mu).sum()),2*np.array([g.sum(),g@z])
            opt=minimize(joint,[0.,.5],jac=True,method='L-BFGS-B',bounds=[(None,None),(0.,1.)],options={'maxiter':500,'ftol':1e-14,'gtol':1e-9})
            refs.append({'expected':expected,'success':bool(opt.success),'message':str(opt.message),'a':float(opt.x[0]),'b':float(opt.x[1]),'loss':float(opt.fun),'gradient':opt.jac.tolist(),'iterations':int(opt.nit)})
        r['joint_references']=refs
    (RUN/'attempt1_failure_investigation.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r,ensure_ascii=True))

if __name__=='__main__':main()
