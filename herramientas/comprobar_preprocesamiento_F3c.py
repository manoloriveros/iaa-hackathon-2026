"""Cotejo de valores del preprocesamiento original, sin fit ni inferencia."""
from pathlib import Path
from datetime import datetime,timezone
import gc,hashlib,importlib.util,json,sys
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pandas as pd
import numpy as np
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
a=load('a1_feature_audit',R/'herramientas/ampliar_validacion_cadena_f3c.py')
legacy=R/'privado/reentrenamiento_completo_20261026/corrida/noche'
original=load('original_features_audit',legacy/'codigo/variables.py')
OUT=R/'privado/semana2/mision017_fase2/F3c_validacion_completa_20261027'
def main():
    assert not (OUT/'feature_value_parity.json').exists();records=[]
    for market,mk in [('developed','s1'),('emerging','s2')]:
        for line in ['motor','buildings','contents']:
            basepath=legacy/'salidas'/mk/f'base_{line}.parquet'
            base=pd.read_parquet(basepath,filters=[('year','==',2023)] if mk=='s1' else [('year','in',[2023,2024])])
            population=len(base)
            if mk=='s1':base=base.iloc[np.linspace(0,len(base)-1,min(5000,len(base))).astype(int)].copy()
            base=base.reset_index(drop=True);assert base.row_id.is_unique and base.year.le(2024).all()
            X,_,_=original.features(base,line,mk);X['exposure_model']=base.exposure_model.to_numpy();del _;gc.collect()
            p=a.RUN/'prepared'/f'{market}_{line}.parquet';now=pd.read_parquet(p,filters=[('row_id','in',base.row_id.tolist())]).set_index('row_id').loc[base.row_id].reset_index()
            new=a.a1_features(now,line);diff={}
            for col in new:
                assert col in X
                if col in a.CAT:bad=X[col].astype('string').fillna('missing').to_numpy()!=new[col].astype('string').fillna('missing').to_numpy()
                else:bad=~np.isclose(X[col].to_numpy(float),new[col].to_numpy(float),rtol=0,atol=1e-12,equal_nan=True)
                count=int(np.sum(bad))
                if count:diff[col]={'different_rows':count,'max_abs':float(np.nanmax(np.abs(X[col].to_numpy(float)-new[col].to_numpy(float)))) if col not in a.CAT else None}
            records.append({'market':market,'line':line,'rows_compared':len(base),'eligible_rows':population,'scope':'systematic5000source2023' if mk=='s1' else 'alltarget2023and2024','features_compared':len(new),'mismatches':diff,'row_key_digest':a.v.digest(base.row_id.to_numpy()),'original_feature_code_sha256':a.v.sha(Path(original.__file__))})
            print(json.dumps(records[-1]),flush=True);del X,new,now,base;gc.collect()
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'records':records,'all_passed':all(not z['mismatches'] for z in records),'model_inferences':0,'native_fits':0,'2025_rows_read':0,'source_sample_not_all_source_rows':True,'code_sha256':a.v.sha(Path(__file__))}
    with (OUT/'feature_value_parity.json').open('x',encoding='utf8') as stream:json.dump(result,stream,indent=2)
    assert result['all_passed'],'Original/temporal feature preprocessing discrepancy; preserve receipt and investigate before claiming equivalence.'

if __name__=='__main__':sys.stdout.reconfigure(encoding='utf8');main()
