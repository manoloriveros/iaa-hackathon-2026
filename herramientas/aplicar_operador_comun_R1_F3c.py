"""Mismo operador R1 congelado sobre las dos bases de riesgo; cero ajustes."""
from pathlib import Path
import argparse,importlib.util,json,sys
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=load('paired_trunk',R/'herramientas/comparar_R1_F3c_tronco_comun.py')
p=load('fixed_R1_operator',R/'herramientas/producir_R1_prioridad_privada.py')
OLD=R/'privado/semana2/claude_validacion_nocturna_20261023/sonda_global/final_sonda_global_2025.csv'
PLAN=R/'registro/semana2_R1_F3c_operador_comun_plan.json'
def freeze():
    m.guard();assert not PLAN.exists()
    sources=[Path(__file__),OLD,Path(m.__file__),Path(p.__file__),m.OUT/'results.json',m.R1/'parameters.json',m.R1/'production_quotes.parquet',m.F3]
    sources += [m.DATA/f'test_{line}.parquet' for line in ['motor','buildings','contents']]+[m.DATA/'customers.parquet']
    assert m.w.sha(OLD).startswith('42659dbb')
    plan={'author':'Codex','utc':m.utc(),'parent':m.w.rel(m.PLAN),'reason':'Matched policy showed small total changes but material individual effects; residual source/F2/nuisance confounding remains. Need SAME complete preprocessing operator for both incoming risks.',
      'scope':'Freeze all R1 F2/commonshape/normalizers/cell levels and own-renewal parameters. Apply rowwise to R1 incoming base and historical F input of F3c. Identical features, exposures and q1. No new fit or parameter selection.',
      'input_warning':'Old F is the existing global-calibrated mixture input, not pure source risk. Its inherited global multiplier stays fixed. This does not isolate source year, F1, seeds, mixture or internal old completion.',
      'price_path':'PublishedF3c -> frozenR1operator(oldFinput) -> frozenR1operator(R1input)=R1. Exact additive path in CU, order-dependent, not causal or D2 decomposition. No claim about uncomputed legacyoperator(R1input).',
      'controls':['All209063R1reproduced with identical full operator','AlloldFIDs align and no rowloss','Fixed parameters unchanged, no labels passed','OldFapplication reorder/singleton preserves per-row prices','Finite positive outputs, both original hashes preserved'],
      'budget':{'native_or_closed_fits':0,'CDF_fits':0,'Booster_inference':0,'submissions':0},'no_candidate_admission':True,
      'sources':{m.w.rel(path):m.w.sha(path) for path in sources}}
    m.dump(PLAN,plan)
    forum=m.post('Codex. Amplío el contraste, sin cambiar sus resultados ni aprender parámetros: aplicaré el MISMO operador R1 completo (F2, forma común, normalizadores, niveles y regla de renovación congelados) a las dos entradas de riesgo. La entrada histórica F de F3c conserva su calibración global anterior; no la presentaré como riesgo fuente puro. El camino F3c → operador R1 sobre F → operador R1 sobre su propia base separa entrada y operador en ese orden, sin atribuir D² ni causalidad. No se calcula ni supone el operador antiguo sobre la entrada nueva. Todas las variables y exposición serán idénticas. Cero ajustes, inferencia de árboles o envíos; controles de reproducción completa y aplicación por fila. Plan '+m.w.rel(PLAN)+' SHA '+m.w.sha(PLAN),'COD-S2-20261027-OPERADOR-COMUN-PREVIO','Mismo operador congelado sobre las dos entradas de riesgo')
    m.dump(m.OUT/'operator_registration.json',{'plan_sha256':m.w.sha(PLAN),'forum':forum});print(json.dumps({'registered':True,'plan_sha256':m.w.sha(PLAN)}))
def analyze():
    m.guard();assert m.w.sha(PLAN)==m.w.read(m.OUT/'operator_registration.json')['plan_sha256']
    for name,sha in m.w.read(PLAN)['sources'].items():assert m.w.sha(ROOT/name)==sha,name
    pairs=pd.read_parquet(m.OUT/'paired_prices_and_bridge.parquet');order=pairs.row_id
    q=pd.read_parquet(m.R1/'production_quotes.parquet').set_index('row_id').loc[order].reset_index()
    old=pd.read_csv(OLD).set_index('row_id');assert old.index.is_unique and set(old.index)==set(order)
    t=q[['row_id','line','new_business','exposure','q','base']].copy();cu=pd.read_parquet(m.DATA/'customers.parquet',columns=['customer_id','prior_claims_5y','gender','marketing_segment']);cov=[]
    for line in ['motor','buildings','contents']:
        cols=['row_id','customer_id']+(['ncb_years'] if line=='motor' else [])+(['works_from_home'] if line=='contents' else [])
        f=pd.read_parquet(m.DATA/f'test_{line}.parquet',columns=cols).merge(cu,on='customer_id',validate='m:1');cov.append(f)
    f=pd.concat(cov,ignore_index=True).set_index('row_id').loc[order].reset_index();t=t.merge(f.drop(columns='customer_id'),on='row_id',validate='1:1');assert t.row_id.equals(order)
    pars=m.w.read(m.R1/'parameters.json')['recipe'];before=p.v.digest(pars)
    replay,baseline=p.apply(t,pars);checks={}
    checks['ALL209063_R1_replay_exact']=np.array_equal(replay,pairs.R1.to_numpy()) and np.array_equal(baseline,pairs.R1base.to_numpy())
    changed=t.copy();changed['base']=order.map(old.prediction).to_numpy();value,without=p.apply(changed,pars)
    rev,_=p.apply(changed.iloc[::-1],pars);checks['old_input_order_exact']=np.array_equal(value,rev[::-1])
    selected=np.arange(0,len(t),4051);checks['old_input_singleton_exact']=all(np.array_equal(p.apply(changed.iloc[[i]],pars)[0],value[i:i+1]) for i in selected)
    checks['frozen_parameters_unchanged']=before==p.v.digest(pars)
    checks['positive_finite']=np.isfinite(value).all() and (value>0).all()
    delta_operator=value-pairs.F3c.to_numpy();delta_input=replay-value
    checks['ALL209063_price_path']=np.allclose(delta_operator+delta_input,pairs.R1-pairs.F3c,rtol=1e-12,atol=1e-10)
    checks['original_CSVs_preserved']=m.w.sha(m.F3)==m.SHA_F3 and m.w.sha(m.R1/'R1_T2b_2025.csv')==m.SHA_R1
    checks['all_passed']=all(checks.values());assert checks['all_passed'],checks
    result=pairs[['row_id','line','new_business','exposure','F3c','R1']].copy();result['R1operator_old_input']=value;result['change_operator_on_old_input']=delta_operator;result['change_input_under_R1operator']=delta_input
    result.to_parquet(m.OUT/'same_operator_price_path.parquet',index=False)
    rows=[]
    for keys,g in [('global',result),*list(result.groupby(['line','new_business']))]:
        rows.append({'cell':list(keys) if isinstance(keys,tuple) else keys,'rows':len(g),'F3c_total':float(g.F3c.sum()),'common_operator_old_input_total':float(g.R1operator_old_input.sum()),'R1_total':float(g.R1.sum()),
            'operator_change_CU':float(g.change_operator_on_old_input.sum()),'incoming_risk_change_CU':float(g.change_input_under_R1operator.sum()),
            'old_to_R1_input_under_same_operator_ratio':float(g.R1.sum()/g.R1operator_old_input.sum())})
    m.dump(m.OUT/'same_operator_results.json',{'author':'Codex','utc':m.utc(),'checks':checks,'path':rows,'plan_sha256':m.w.sha(PLAN),'code_sha256':m.w.sha(Path(__file__)),
        'same_features_exposure_and_all_postprocessor_parameters':True,'old_input_includes_historical_global_multiplier':True,
        'price_path_order_dependent_not_D2_attribution':True,'new_native_or_closed_fits':0,'new_Booster_inference':0,'new_submissions':0})
    print(json.dumps({'all_passed':True,'path':rows}),flush=True)
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');arg=argparse.ArgumentParser();arg.add_argument('mode',choices=['freeze','analyze']);args=arg.parse_args();globals()[args.mode]()
