"""Comprobacion escalar independiente del operador de precios R1 y sus claves."""
from pathlib import Path
import importlib.util, json, math, sys
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
s=importlib.util.spec_from_file_location('producer_r1',R/'herramientas/producir_R1_prioridad_privada.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)

def main():
    p.guard();pars=p.w.read(p.OUT/'parameters.json');recipe=pars['recipe'];q=pd.read_parquet(p.OUT/'production_quotes.parquet')
    f=p.features().set_index('row_id').loc[q.row_id].reset_index();maps={}
    for stage in ['F2','own']:
        maps[stage]=[(z,{(a,k):float(v) for a,k,v in z['factors']}) for z in recipe[stage]]
    def key(row,var):
        if var=='ncb':
            if row.line!='motor':return 'x'
            x=0 if pd.isna(row.ncb_years) else row.ncb_years
            return '0' if -1<x<=0 else '1-2' if 0<x<=2 else '3-5' if x<=5 else '6-9' if x<=9 else '10+' if x<=99 else 'nan'
        if var=='prior':return str(int(min(0 if pd.isna(row.prior_claims_5y) else row.prior_claims_5y,2)))
        return str(getattr(row,var))
    values=[];base=[]
    for row,raw in zip(f.itertuples(index=False),q.raw):
        cell=row.line+'_'+str(int(row.new_business));m=pars['full_base'][row.line]['level']*math.exp(raw)*row.exposure
        for z,lookup in maps['F2']:
            unit=cell if z['kind']=='ae' else row.line
            m*=lookup.get((unit,key(row,z['variable'])),1.)*z['normal'].get(cell,1.)
        shape=recipe['shape']
        if cell==shape['cell']:m=row.exposure*shape['gm']*(m/row.exposure/shape['gm'])**shape['power']*shape['norm']
        b=m*recipe['levels']['sin_factores'][cell];base.append(b)
        if int(row.new_business)==0:
            for z,lookup in maps['own']:
                unit=cell if z['kind']=='ae' else row.line
                m*=lookup.get((unit,key(row,z['variable'])),1.)*z['normal'].get(cell,1.)
            m*=recipe['levels']['F3c_reaprendido'][cell]
        else:m=b
        values.append(m)
    error=float(np.max(np.abs(np.array(values)-q.prediction.to_numpy())/q.prediction.to_numpy()))
    checks={'ALL209063_scalar_alternate_math':error<3e-13}
    routes=p.w.read(ROOT/'RUTAS_PROYECTO.json');canonical=pd.read_parquet(ROOT/routes['week_2_prepared_targets'])
    canonical=canonical[canonical.market.eq('emerging')&canonical.year.isin([2023,2024])&~canonical.is_test]
    hist=p.historical();c=canonical.set_index('row_id').T0_cents
    checks['ALL109296_canonical_keys_cents']=len(hist)==len(c)==109296 and set(hist.row_id)==set(c.index) and np.array_equal(np.rint(hist.y.to_numpy()*100).astype('int64'),hist.row_id.map(c).to_numpy('int64'))
    sample=pd.read_parquet(ROOT/'Hackaton/Semana 2/Datos/emerging/sample_submission.parquet')
    csv=pd.read_csv(p.OUT/'R1_T2b_2025.csv')
    checks['official_emerging_sample_IDs_order_columns']=sample.row_id.equals(csv.row_id) and list(sample)==list(csv)
    checks['source_code_committed_bytes']=all(subprocess_show(path)==path.read_bytes() for path in [Path(p.__file__),Path(p.v.__file__)])
    checks['all_passed']=all(checks.values())
    result={'utc':p.utc(),'checks':checks,'scalar_relative_error':error,'native_fits':0,'CDF_fits':0,'new_closed_fits':0,
        'verifier_sha256':p.v.sha(__file__),'independent_professional_review':False}
    p.dump(p.OUT/'alternate_verification.json',result);assert checks['all_passed'],checks
    print(json.dumps(result),flush=True)

def subprocess_show(path):
    import subprocess
    return subprocess.run(['git','show','HEAD:'+path.relative_to(R).as_posix()],cwd=R,capture_output=True,check=True).stdout
if __name__=='__main__':main()
