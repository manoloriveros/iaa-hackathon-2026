"""Separa el factor global histórico conocido y traza F2/niveles ya congelados."""
from pathlib import Path
import argparse,importlib.util,json,sys
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
def mod(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=mod('price_pairs',R/'herramientas/comparar_R1_F3c_tronco_comun.py')
p=mod('level_fixed_operator',R/'herramientas/producir_R1_prioridad_privada.py')
META=R/'privado/semana2/claude_validacion_nocturna_20261023/sonda_segmento/preinscripcion.json'
RAW=R/'privado/semana2/claude_ml_independiente_20261023/mezcla50_designada_mlind_2025.csv'
OLD=R/'privado/semana2/claude_validacion_nocturna_20261023/sonda_global/final_sonda_global_2025.csv'
PLAN=R/'registro/semana2_R1_F3c_nivel_conocido_plan.json'
def freeze():
    m.guard();assert not PLAN.exists();meta=m.w.read(META)['base']
    assert m.w.sha(OLD)==meta['sha256'] and m.w.sha(RAW)==meta['mezcla']['sha256']
    sources=[Path(__file__),META,RAW,OLD,Path(p.__file__),Path(p.v.__file__),m.R1/'parameters.json',m.R1/'production_quotes.parquet',m.OUT/'same_operator_results.json',m.OUT/'same_operator_price_path.parquet']
    plan={'author':'Codex','utc':m.utc(),'reason':'The common-operator comparison still includes inherited global g in old F. Separate its already documented value to avoid calling calibration a source-trunk effect.',
      'known_global_g':meta['g'],'not_estimated_from_new_scores_or_outcomes':True,
      'configuration':'Use raw mixture with documented matchingSHA and verify oldF=rawmixture*g within original CSV rounding. Apply same frozen R1 operator to rawmixture; commonshape implies scaling power.9 in motorrenewal and1elsewhere. Trace each fixed F2 step, commonshape and final baseline level on rawmixture and R1incoming base.',
      'controls':'Full-file CSV roundoff and homogeneity identities, actualR1 reproduction, all stages finitepositive, identical covariates/exposure/fixed parameters. No fitting, changed coefficients, new centering, selected multiplier, price clipping, hidden-label inference or sending.',
      'scope_limits':'g is inherited historical public calibration, not justified for private by this decomposition. Rawmixture still contains its own source/target preparation and historical adaptation. Tracing stage totals does not establish which mean or multiplier is correct.',
      'budget':{'new_native_or_closed_fits':0,'new_CDF_fits':0,'new_Booster_inference':0,'new_submissions':0},
      'sources':{m.w.rel(path):m.w.sha(path) for path in sources}}
    m.dump(PLAN,plan)
    forum=m.post('Codex. Registro una separación final del nivel antes del cálculo: el metadato histórico identifica g='+str(meta['g'])+' y los SHA de la mezcla previa y F. Verificaré F=mezcla×g dentro del redondeo, y aplicaré el MISMO operador R1 a la mezcla previa, sin volver a estimar g. Trazaré NCB, previos, forma común y nivel final con parámetros intactos para localizar diferencias de nivel. No se adoptará el multiplicador público ni se fabricará un nuevo ajuste o normalizador; la comparación sigue siendo de precios sin etiquetas futuras. Cero entrenamientos, curvas, inferencia de árboles o envíos. Plan '+m.w.rel(PLAN)+' SHA '+m.w.sha(PLAN),'COD-S2-20261027-NIVEL-CONOCIDO-PREVIO','Separar la calibracion global heredada de los cambios del tronco')
    m.dump(m.OUT/'known_level_registration.json',{'plan_sha256':m.w.sha(PLAN),'forum':forum});print(json.dumps({'registered':True,'g':meta['g']}))
def analyze():
    m.guard();assert m.w.sha(PLAN)==m.w.read(m.OUT/'known_level_registration.json')['plan_sha256']
    for name,sha in m.w.read(PLAN)['sources'].items():assert m.w.sha(ROOT/name)==sha,name
    plan=m.w.read(PLAN);g=plan['known_global_g'];quotes=pd.read_parquet(m.R1/'production_quotes.parquet');order=quotes.row_id
    def aligned(path):
        f=pd.read_csv(path).set_index('row_id');assert f.index.is_unique and set(f.index)==set(order);return order.map(f.prediction).to_numpy()
    raw=aligned(RAW);old=aligned(OLD);checks={}
    e=float(np.max(np.abs(old-g*raw)));checks['ALL209063_oldF_known_g_only']=e<=.5001e-6
    t=quotes[['row_id','line','new_business','exposure','q','base']].copy();frames=[]
    cu=pd.read_parquet(m.DATA/'customers.parquet',columns=['customer_id','prior_claims_5y','gender','marketing_segment'])
    for line in ['motor','buildings','contents']:
        cols=['row_id','customer_id']+(['ncb_years'] if line=='motor' else [])+(['works_from_home'] if line=='contents' else [])
        frames.append(pd.read_parquet(m.DATA/f'test_{line}.parquet',columns=cols).merge(cu,on='customer_id',validate='m:1'))
    cov=pd.concat(frames,ignore_index=True).set_index('row_id').loc[order].reset_index();t=t.merge(cov.drop(columns='customer_id'),on='row_id',validate='1:1');assert t.row_id.equals(order)
    pars=m.w.read(m.R1/'parameters.json')['recipe'];cells=p.v.cells(t);levels=pars['levels'];out={};summaries=[]
    for tag,base in [('R1_input',quotes.base.to_numpy()),('old_mixture_no_global',raw),('old_F_with_global',old)]:
        f=t.copy();f['base']=base;stages={'incoming':base.copy()};value=base.copy()
        for factor in pars['F2']:
            value=p.v.factor_apply(f,value,p.v.ks(f,factor['variable']),factor);stages['after_'+factor['variable']]=value.copy()
        value=p.v.shape_apply(f,value,pars['shape']);stages['after_common_shape']=value.copy()
        value*=np.array([levels['sin_factores'][cc] for cc in cells]);stages['after_baseline_level']=value.copy()
        r1,baseline=p.apply(f,pars);out[tag]=r1
        checks[tag+'_baseline_trace']=np.array_equal(value,baseline)
        for (line,nb),block in t.groupby(['line','new_business']):
            i=t.index.isin(block.index);row={'input':tag,'line':line,'new_business':int(nb),'rows':len(block),'stage_totals':{name:float(v[i].sum()) for name,v in stages.items()},'R1_policy_total':float(r1[i].sum()),'baseline_final_multiplier':levels['sin_factores'][line+'_'+str(int(nb))]}
            summaries.append(row)
    checks['ALL_R1_actual_reproduced']=np.array_equal(out['R1_input'],quotes.prediction.to_numpy())
    exponent=np.where(cells=='motor_0',pars['shape']['power'],1.)
    # Input artifacts round to6decimals; propagate their existing rounding only.
    ratio_err=np.abs(out['old_F_with_global']-out['old_mixture_no_global']*g**exponent)/out['old_F_with_global']
    checks['global_homogeneity_with_roundoff']=float(ratio_err.max())<3e-5
    checks['all_stages_positive_finite']=all(np.isfinite(value).all() and (value>0).all() for value in out.values())
    checks['all_passed']=all(checks.values());assert checks['all_passed'],checks
    rows=[]
    for keys,block in [('global',t),*list(t.groupby(['line','new_business']))]:
        i=t.index.isin(block.index);a=out['R1_input'][i];b=out['old_mixture_no_global'][i]
        rows.append({'cell':list(keys) if isinstance(keys,tuple) else keys,'R1_input_common_operator_total':float(a.sum()),'old_mixture_without_global_common_operator_total':float(b.sum()),'ratio':float(a.sum()/b.sum()),
            'raw_incoming_R1_to_oldmix_total_ratio':float(quotes.base.to_numpy()[i].sum()/raw[i].sum()),'log_price_correlation':float(np.corrcoef(np.log(a),np.log(b))[0,1])})
    m.dump(m.OUT/'known_level_and_F2_trace.json',{'author':'Codex','utc':m.utc(),'checks':checks,'known_historical_g':g,'oldF_g_rawmix_max_absolute_error':e,
       'max_homogeneity_relative_error_with_CSV_roundoff':float(ratio_err.max()),'common_operator_after_removing_known_g':rows,'fixed_stage_trace':summaries,
       'native_or_closed_fits':0,'new_Booster_inference':0,'new_submissions':0,'no_private_superiority_or_multiplier_adoption':True,'code_sha256':m.w.sha(Path(__file__))})
    print(json.dumps({'all_passed':True,'known_g':g,'common_operator_after_removing_known_g':rows,'max_roundoff':e}),flush=True)
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');a=argparse.ArgumentParser();a.add_argument('mode',choices=['freeze','analyze']);args=a.parse_args();globals()[args.mode]()
