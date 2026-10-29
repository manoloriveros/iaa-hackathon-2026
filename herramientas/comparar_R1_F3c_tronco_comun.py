"""Contrastes de política sobre troncos fijos y atribución contable de precios.

No estima respuestas ocultas ni atribuye cambios de D2 público sin etiquetas.
Las razones F3c/C1 son representación de artefactos, no parámetros aprendidos.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,importlib.util,itertools,json,math,subprocess,sys
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=module('matched_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
BASE=R/'privado/semana2/mision017_fase2'
OUT=BASE/'R1_F3c_tronco_comun_20261027'
R1=BASE/'produccion_R1_privada_20261027'
REVIEW=BASE/'revision_chat_documento_20261027'
C1=BASE/'calibracion_F2_creible_20261025_v1/final_creible_2025.csv'
F2=R/'privado/semana2/claude_mision017_20261025/F2_ncb_previos_2025.csv'
F3=R/'privado/semana2/claude_mision017_20261025/F3c_2025.csv'
PLAN=R/'registro/semana2_R1_F3c_tronco_comun_plan.json'
INDEX=R/'registro/semana2_R1_F3c_tronco_comun_actual.json'
DOC=R/'docs/archivo/semana2/R1_F3C_TRONCO_COMUN_20261027.md'
ML=R/'src/semana2/lineas/mision017_20261025'
DATA=ROOT/'Hackaton/Semana 2/Datos/emerging'
SHA_F3='5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276'
SHA_R1='1f5967ec88b7198397b11f5a8e41d1d22f20d0f8fe64ba9799c246b9d796daed'
NAMES=['regla_NB_sobre_F3c','reaprendizaje_bloque_renovacion','retirar_forma_nivel_publicos_C1','resto_base_y_nuisance']
def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,x):
    encoded=json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False,default=lambda z:z.item() if isinstance(z,np.generic) else str(z))+'\n'
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf8') as f:f.write(encoded)
def post(text,identifier,subject):
    p=OUT/(identifier+'.md');p.write_text(text,encoding='utf8')
    a=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',identifier,'--asunto',subject,'--cuerpo',str(p)],capture_output=True,text=True,encoding='utf8',check=True)
    return json.loads(a.stdout)
def paths():
    return [Path(__file__),C1,F2,F3,R1/'R1_T2b_2025.csv',R1/'parameters.json',R1/'production_quotes.parquet',R1/'production_validation.json',R1/'public_receipt.json',
      REVIEW/'policy_results.json',REVIEW/'scenario_review.json',REVIEW/'policy_verification.json',
      BASE/'entrega_F3c_investigacion_20261026_v1/replay_report.json',BASE/'entrega_F3c_investigacion_20261026_v1/public_receipt.json',
      BASE/'calibracion_F2_creible_20261025_v1/report.json',
      ML/'exp26_20261026_v2/m017/construir_F3c.py',ML/'exp26_20261026/m017/construir_F3b.py',ML/'codigo/construir_F2.py',
      R/'herramientas/producir_R1_prioridad_privada.py',R/'herramientas/validar_cadena_f3c.py',DATA/'customers.parquet',DATA/'sample_submission.parquet',
      *[DATA/f'test_{l}.parquet' for l in ['motor','buildings','contents']]]
def freeze():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists();OUT.mkdir()
    assert w.sha(F3)==SHA_F3 and w.sha(R1/'R1_T2b_2025.csv')==SHA_R1
    plan={'author':'Codex','utc':utc(),'request':'Compare R1 and F3c on identical trunk/preprocessing, preserve both, publish findings locally, no new submission without evidence.',
      'prior_knowledge':'R1 public .15820 vs F3c .16914 known. Earlier diagnostic showed substantial six-cell level differences. No hidden target/segment scores inferred.2024 is adaptive development.',
      'hypothesis':'The delivery gap confounds own-NB policy with source/preprocessing, F2/nuisance, learned renewal effects and public shape/level overlays. Matched policy applications and an exact price bridge can locate price changes, not score loss.',
      'design':{'matched_F3c_trunk':'Hold final_creible C1 baseline and ALL preprocessing fixed. PublishedF3c versus NB=C1, renewal=publishedF3c. No later normalization, factor or level; preserve exact baseline.',
       'matched_R1_trunk':'Hold R1 frozen T2b baseline, F2/shape, target2023-24 parameters and cell normalizers fixed. PublishedR1 policy versus full own block with those SAME parameters. No re-estimation.',
       'control':'Both matched pairs must be identical on renewal; F3c-NB andR1-NB fallback equal their own base. Buildings own-block identity within CSV-rounding tolerance. NB data missing from own fields does not alter NB fallback.',
       'decomposition':'Four fixed positive price multipliers: NB own-policy removal on F3c, own-block relearning only in renewal, removal of C1/F2 historical public shape/level, remaining R1baseline/F2. Exact multiplicative bridge, and order-invariant 4factor Shapley CU decomposition. Not causal D2 attribution.',
       'historical_evidence':'Reuse existing protected T2b primary and A1/mix sensitivity policy intervals/scenario receipts exactly; no repeat bootstrap/fit/scoring. They compare policies within each matched family, not exact legacy3seedF1/public F3c.',
       'strata':'Six ramo/business cells; exposure fixed bins <.5,.5-.9,>=.9. No data-driven bins or weight search.',
       'limits':'Ratios F3c/C1 derive from published output artifacts; do not claim recovery of fitted factors or clean training. C1/F2 are historical public-calibration changes, not evidence to adopt public multipliers on T2b.'},
      'acceptance':'Diagnostic only: all provenance, price identities, independent permutation-average Shapley, full-file and fallback controls pass. No candidate promotion/admission or private-superiority statement from aggregate prices. Failure preserved, no rescue by new factors.',
      'budget':{'new_native_or_closed_fits':0,'new_CDF_fits':0,'new_Booster_inference':0,'new_bootstrap_draws':0,'new_submissions':0,'shadow_price_files':'private Parquet only, no upload CSV'},
      'future_decision':'Prioritize matched protected history and target-level/ultimate transport before further source/feature complexity; any later experiment needs its own criterion and scope. Preserve failed versions and concurrent authorship.',
      'sources':{w.rel(p):w.sha(p) for p in paths()}}
    dump(PLAN,plan)
    forum=post('Codex. Registro antes del cálculo una comparación cruzada sin ajustar ni enviar. Sobre el tronco F3c/C1 fijo compararé el archivo completo con la regla NB=base exacta y renovación=F3c; sobre el tronco T2b/R1 fijo compararé la regla R1 con el bloque completo usando los mismos parámetros. Mantengo idénticos preprocesamiento, normalizadores y niveles dentro de cada pareja. Separaré contablemente regla NB, reaprendizaje del bloque en renovación, forma/nivel públicos históricos C1/F2 y resto de base/nuisance; suma exacta y Shapley por otro método. Son cambios de precios sin etiquetas futuras, no aportes a D² público. Reutilizaré la evidencia histórica protegida, sin repetir ajustes ni bootstrap ni tratarla como prueba de la familia antigua. Cero envíos y cero inferencias de árboles; ambos originales y B00 conservados. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),'COD-S2-20261027-TRONCO-COMUN-PREVIO','R1 y F3c: contraste de política con tronco y preprocesamiento fijos')
    dump(INDEX,{'author':'Codex','utc':utc(),'status':'registered_before_matched_price_calculation','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),'forum':forum,'output':w.rel(OUT),'new_submissions':0})
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':forum});print(json.dumps({'registered':True,'plan_sha256':w.sha(PLAN)}),flush=True)
def guard():
    assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    for name,sha in w.read(PLAN)['sources'].items():assert w.sha(ROOT/name)==sha,name
    assert w.sha(F3)==SHA_F3 and w.sha(R1/'R1_T2b_2025.csv')==SHA_R1
def bridge_shapley(start,factors):
    n=factors.shape[1];result=np.zeros_like(factors)
    for i in range(n):
        rest=[j for j in range(n) if j!=i]
        for size in range(n):
            weight=math.factorial(size)*math.factorial(n-size-1)/math.factorial(n)
            for subset in itertools.combinations(rest,size):
                product=np.prod(factors[:,subset],axis=1) if subset else np.ones(len(start))
                result[:,i]+=weight*start*product*(factors[:,i]-1)
    return result
def scalar_permutations(start,factors):
    result=np.zeros_like(factors)
    for order in itertools.permutations(range(factors.shape[1])):
        current=start.copy()
        for i in order:
            updated=current*factors[:,i];result[:,i]+=updated-current;current=updated
    return result/math.factorial(factors.shape[1])
def summary(t,mask):
    g=t.loc[mask];out={'rows':len(g),'exposure':float(g.exposure.sum())}
    for name in ['F3c','C1','F2','F3c_trunk_NBfallback','R1','R1base','R1_trunk_fullown']:
        out[name+'_total']=float(g[name].sum())
    out['R1_minus_F3c_total']=float((g.R1-g.F3c).sum())
    out['NB_rule_on_F3c_total_change']=float((g.F3c_trunk_NBfallback-g.F3c).sum())
    out['NB_rule_on_R1_total_change']=float((g.R1-g.R1_trunk_fullown).sum())
    out['R1_to_F3c_total_ratio']=float(g.R1.sum()/g.F3c.sum())
    out['shapley_CU']={name:float(g['shapley_'+name].sum()) for name in NAMES}
    out['mean_absolute_log_components']={name:float(np.abs(np.log(g['factor_'+name])).mean()) for name in NAMES}
    out['price_ratio_quantiles']={str(q):float((g.R1/g.F3c).quantile(q)) for q in [.01,.1,.5,.9,.99]}
    return out
def analyze():
    guard();assert not (OUT/'results.json').exists()
    f3=pd.read_csv(F3);order=f3.row_id
    def aligned(path):
        x=pd.read_csv(path).set_index('row_id');assert set(x.index)==set(order) and x.index.is_unique
        return order.map(x.prediction).to_numpy(float)
    q=pd.read_parquet(R1/'production_quotes.parquet').set_index('row_id').loc[order].reset_index()
    t=q[['row_id','line','new_business','exposure']].copy();t['F3c']=f3.prediction.to_numpy();t['C1']=aligned(C1);t['F2']=aligned(F2)
    t['R1']=q.prediction.to_numpy();t['R1_published']=aligned(R1/'R1_T2b_2025.csv');t['R1base']=q.baseline.to_numpy()
    cu=pd.read_parquet(DATA/'customers.parquet',columns=['customer_id','gender','marketing_segment']);cov=[]
    for line in ['motor','buildings','contents']:
        cols=['row_id','customer_id']+(['works_from_home'] if line=='contents' else [])
        f=pd.read_parquet(DATA/f'test_{line}.parquet',columns=cols).merge(cu,on='customer_id',validate='m:1');cov.append(f)
    cov=pd.concat(cov,ignore_index=True).set_index('row_id').loc[order].reset_index()
    params=w.read(R1/'parameters.json')['recipe'];cells=t.line.astype(str)+'_'+t.new_business.astype(int).astype(str)
    m=t.R1base.to_numpy()/cells.map(params['levels']['sin_factores']).to_numpy()
    for stage in params['own']:
        lookup={(unit,key):value for unit,key,value in stage['factors']};keys=cov[stage['variable']].astype(str)
        units=cells if stage['kind']=='ae' else t.line
        m*=np.array([lookup.get((unit,key),1.)*stage['normal'].get(cell,1.) for unit,key,cell in zip(units,keys,cells)])
    t['R1_trunk_fullown']=m*cells.map(params['levels']['F3c_reaprendido']).to_numpy()
    nb=t.new_business.eq(1).to_numpy();t['F3c_trunk_NBfallback']=np.where(nb,t.C1,t.F3c)
    factors=np.column_stack([np.where(nb,t.C1/t.F3c,1.),np.where(nb,1.,(t.R1/t.R1base)/(t.F3c/t.C1)),t.F2/t.C1,t.R1base/t.F2])
    sp=bridge_shapley(t.F3c.to_numpy(),factors)
    for i,name in enumerate(NAMES):t['factor_'+name]=factors[:,i];t['shapley_'+name]=sp[:,i]
    checks={}
    checks['fixed_F3c_pair_renewal_exact']=np.array_equal(t.loc[~nb,'F3c_trunk_NBfallback'],t.loc[~nb,'F3c'])
    checks['fixed_R1_pair_renewal']=np.allclose(t.loc[~nb,'R1_trunk_fullown'],t.loc[~nb,'R1'],rtol=3e-14,atol=0)
    checks['F3c_NB_fallback_exact_C1']=np.array_equal(t.loc[nb,'F3c_trunk_NBfallback'],t.loc[nb,'C1'])
    checks['R1_NB_fallback_exact_base']=np.array_equal(t.loc[nb,'R1'],t.loc[nb,'R1base'])
    checks['R1_csv_rounding_only']=np.max(np.abs(t.R1-t.R1_published))<.5001e-6
    b=t.line.eq('buildings').to_numpy()
    checks['buildings_F3c_own_block_identity']=np.max(np.abs(t.loc[b,'F3c']-t.loc[b,'C1']))<=1e-6
    checks['buildings_R1_own_block_identity']=np.allclose(t.loc[b,'R1_trunk_fullown'],t.loc[b,'R1base'],rtol=3e-14,atol=0)
    mult=t.F3c.to_numpy()*np.prod(factors,axis=1);add=t.F3c.to_numpy()+sp.sum(axis=1)
    me=float(np.max(np.abs(mult-t.R1.to_numpy())/t.R1.to_numpy()));ae=float(np.max(np.abs(add-t.R1.to_numpy())/t.R1.to_numpy()))
    checks['ALL209063_multiplicative_bridge']=me<3e-13;checks['ALL209063_ShAP_sum']=ae<3e-13
    selected=np.unique(np.r_[np.arange(0,len(t),1999),np.argmax(np.max(np.abs(np.log(factors)),axis=1))])
    independently=scalar_permutations(t.F3c.to_numpy()[selected],factors[selected])
    pe=float(np.max(np.abs(independently-sp[selected])/np.maximum(np.abs(sp[selected]),1.)))
    checks['permutation_average_independent_math']=pe<3e-12
    checks['official_ID_order']=order.equals(pd.read_parquet(DATA/'sample_submission.parquet').row_id)
    checks['finite_positive_all_shadow_prices']=all(np.isfinite(t[n]).all() and t[n].gt(0).all() for n in ['F3c_trunk_NBfallback','R1_trunk_fullown'])
    checks['all_passed']=all(checks.values())
    t.to_parquet(OUT/'paired_prices_and_bridge.parquet',index=False)
    global_result=summary(t,np.ones(len(t),bool));groups=[];bands=[]
    for (line,new),g in t.groupby(['line','new_business']):
        groups.append({'line':line,'new_business':int(new),**summary(t,t.index.isin(g.index))})
    band=np.where(t.exposure<.5,'short_<.5',np.where(t.exposure<.9,'medium_.5_.9','long_>=.9'))
    for (line,new,bb),g in t.assign(band=band).groupby(['line','new_business','band']):
        bands.append({'line':line,'new_business':int(new),'band':bb,**summary(t,t.index.isin(g.index))})
    protected=w.read(REVIEW/'policy_results.json');history={view:{'global':z['metrics']['global'],'NB':z['metrics']['new_business'],'renewal':z['metrics']['renewal']} for view,z in protected['results'].items()}
    output={'author':'Codex','utc':utc(),'kind':'matched-price experiment and exact accounting; no2025target and no publicD2attribution','checks':checks,
      'max_relative_errors':{'multiplicative':me,'additive':ae,'alternate_permutation':pe},'global':global_result,'six_cells':groups,'exposure_bands':bands,
      'protected_historical_reused_without_rescoring':history,'protected_scenarios_receipt_sha256':w.sha(REVIEW/'scenario_review.json'),
      'no_clean_exact_legacy_F3c_backtest_available':True,'rounding':'R1 unrounded stored quote is endpoint; CSV differs<=.5e-6. F3c,C1,F2 are original six-decimal artifacts.',
      'new_native_or_closed_fits':0,'new_inferences':0,'new_bootstrap_draws':0,'new_submissions':0,'code_sha256':w.sha(Path(__file__))}
    dump(OUT/'results.json',output);assert checks['all_passed'],checks
    print(json.dumps({'all_passed':True,'global':global_result,'max_relative_errors':output['max_relative_errors']}),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['freeze','analyze']);args=parser.parse_args();globals()[args.mode]()
