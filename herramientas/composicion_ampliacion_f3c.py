"""Reponderación descriptiva2025 en las tres vistas; sin ajuste de modelos."""
import argparse,importlib.util,json
from pathlib import Path
import numpy as np
import pandas as pd

REPO=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('expanded',REPO/'herramientas/ampliar_validacion_cadena_f3c.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
R=a.RUN;v=a.v
def key(line,nb,e):return np.array([str(l)+'|'+str(int(n))+'|'+str(b) for l,n,b in zip(line,nb,np.where(e<.5,'c',np.where(e<.9,'m','l')))])

def freeze():
    assert not (R/'composition_extension.json').exists();assert not (R/'opened.json').exists()
    a.save(R/'composition_extension.json',{'utc':a.now(),'author':'Codex','hypothesis':'Repetir descriptivamente el traslado de composición2025 ya previsto en el contraste primario para las tres vistas. No seleccionar modelos con esta sensibilidad.','weights':'Conteos por ramo/negocio/bandas exposición <.5,<.9,resto; mismos pesos entre modelos y vistas.','seed':2026102301,'draws':10000,'interval':'IC95 condicional por componente cliente-dirección2024; mismas realizaciones que baseline.','training_uses_future_rows':False,'new_fits':0,'source_sha256':a.sha(__file__),'extension_registered_before_new_A1_mix_scores':True})

def evaluate():
    assert a.sha(__file__)==a.read(R/'composition_extension.json')['source_sha256'];a.verify_inputs()
    target=pd.read_parquet(R/'target2024_sealed.parquet').set_index('row_id').y
    base=pd.read_parquet(R/'predictions_T2b.parquet');keys=key(base.line,base.new_business,base.exposure.to_numpy())
    old=pd.Series(keys).value_counts();future=[]
    for l in a.L:
        t=pd.read_parquet(v.LEGACY/'datos/emerging'/f'test_{l}.parquet',columns=['new_business','period_start','period_end'])
        e=((pd.to_datetime(t.period_end)-pd.to_datetime(t.period_start)).dt.days+1).to_numpy()/365.
        future.extend(key(np.repeat(l,len(t)),t.new_business,e))
    new=pd.Series(future).value_counts();assert not (set(new.index)-set(old.index))
    weights=np.array([new.get(k,0)/old[k] for k in keys]);weights*=len(weights)/weights.sum()
    groups,ix=np.unique(v.components(base)[0],return_inverse=True);G=len(groups);out={'utc':a.now(),'views':{},'test_rows':len(future),'limit':'Reponderación descriptiva sin equivalencia futura; datos2024 adaptativos, intervalos condicionales.'}
    for view in a.VIEWS:
        t=pd.read_parquet(R/f'predictions_{view}.parquet');assert np.array_equal(t.row_id,base.row_id);y=t.row_id.map(target).to_numpy(float);pred={k:t[k].to_numpy() for k in a.MODELS}
        masks={'global':np.ones(len(t),bool),'new_business':t.new_business.to_numpy(bool)};result={};stats=[]
        for name,mask in masks.items():
            result[name]=v.summarize(y,pred,mask,weights);w=weights*mask
            cols=[np.bincount(ix,weights=w,minlength=G),np.bincount(ix,weights=w*y,minlength=G),np.bincount(ix,weights=w*np.sqrt(y),minlength=G),np.bincount(ix,weights=w*(v.dev(y,pred['sin_factores'])-v.dev(y,pred['F3c_reaprendido'])),minlength=G)]
            stats.append(np.stack(cols,axis=1))
        flat=np.stack(stats,axis=1).reshape(G,-1);rng=np.random.default_rng(2026102301);draws=np.empty((10000,2))
        for start in range(0,10000,25):
            n=min(25,10000-start);counts=np.stack([np.bincount(rng.integers(0,G,size=G),minlength=G) for _ in range(n)]);z=(counts@flat).reshape(n,2,4);draws[start:start+n]=z[:,:,3]/(8*(np.sqrt(z[:,:,0]*z[:,:,1])-z[:,:,2]))
        for j,name in enumerate(masks):result[name]['CI95']=np.quantile(draws[:,j],[.025,.975])
        out['views'][view]=result;np.savez_compressed(R/f'composition_bootstrap_{view}.npz',delta=draws,weights=weights)
    a.save(R/'composition_results.json',out);print(json.dumps(v.clean(out),ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['freeze','evaluate']);z=p.parse_args();{'freeze':freeze,'evaluate':evaluate}[z.stage]()
