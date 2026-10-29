"""Una receta de credibilidad NB, con tronco y resto del operador congelados."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,importlib.util,json,math,os,subprocess,sys
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=module('NB_cred_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
p=module('NB_fixed_R1',R/'herramientas/producir_R1_prioridad_privada.py')
a=module('NB_group_metric',R/'herramientas/auditar_evaluacion_documento.py')
BASE=R/'privado/semana2/mision017_fase2'
OUT=BASE/'NB_nivel_credibilidad_20261027'
ACTIVE=p.ACTIVE;REVIEW=p.REVIEW
PLAN=R/'registro/semana2_NB_nivel_credibilidad_plan.json'
INDEX=R/'registro/semana2_NB_nivel_credibilidad_actual.json'
DOC=R/'docs/archivo/semana2/NB_NIVEL_CREDIBILIDAD_20261027.md'
PARTITIONS=ROOT/w.read(ROOT/'RUTAS_PROYECTO.json')['week_2_validation_partitions']
LINES=['motor','buildings','contents'];K=300.;COMPS=['R1','full','baseline']
F3=p.F3C;R1=p.OUT/'R1_T2b_2025.csv'
def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,obj):
    encoded=json.dumps(p.v.clean(obj),ensure_ascii=False,indent=2,allow_nan=False)+'\n';path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf8') as f:f.write(encoded)
def post(body,identifier,subject):
    path=OUT/(identifier+'.md');path.write_text(body,encoding='utf8')
    x=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',identifier,'--asunto',subject,'--cuerpo',str(path)],capture_output=True,text=True,encoding='utf8',check=True)
    return json.loads(x.stdout)
def source_paths():
    paths=[Path(__file__),Path(p.__file__),Path(p.v.__file__),Path(a.__file__),PARTITIONS,
        ACTIVE/'training2023_T2b.parquet',ACTIVE/'predictions_T2b.parquet',ACTIVE/'parameters_T2b.json',ACTIVE/'target2024_sealed.parquet',
        ACTIVE/'prediction_checks.json',ACTIVE/'preopening_verification.json',ACTIVE/'post_verification.json',
        ACTIVE/'composition_bootstrap_T2b.npz',ACTIVE/'scenario_results.json',REVIEW/'policy_T2b.parquet',REVIEW/'policy_bootstrap.npz',
        REVIEW/'first4_original_group_multiplicities.npy',REVIEW/'policy_results.json',REVIEW/'policy_verification.json',F3,R1,
        BASE/'R1_F3c_tronco_comun_20261027/next_standard_test_design.json']
    return paths+[ACTIVE/'scenarios'/f'{i:02d}.npz' for i in range(50)]
def guard():
    assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    for name,digest in w.read(PLAN)['sources'].items():assert w.sha(ROOT/name)==digest,name
def freeze():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists();OUT.mkdir()
    plan={'id':'NB-CRED300-20261027','author':'Codex','utc':utc(),'candidate':'NB_CRED300','request':'Register and test NB level contraction toward ramo, rest fixed; private robustness; preserve R1/F3c; no submission without evidence.',
        'prior_knowledge':'R1/F3c public difference and protected2024results known; exploratory after adaptive search, not blind confirmation. One recipe, no grid/ramo/seed selection.',
        'hypothesis':'NB terminal levels estimated on sparse historic business may overreact. Fixed geometric credibility toward a ramo optimum may reduce estimation variance without changing risk shape or renewal prices.',
        'scope':{'source':'Audited T2b source2021-23, categories/CDF/raw predictions and all original folds unchanged; no new source inference.',
            'target':'Saved OOF2023 training50094rows and valuation2024-12-31; observedT0 and exposure unchanged. Hold2024rows59202. Fit ONLY the new3ramo constants on2023.',
            'fixed':'Original F2, commonshape, all normalizers, source/target completion, own residual parameters and every renewal price. NB returns baseline without own factors as R1.',
            'formula':'mu=OOFbase after frozenF2/commonshape BEFORE terminal levels. lambda_ramo=sum(y/sqrt(mu))/sum(sqrt(mu)) over all2023train rows of ramo. lambda_NB original saved sin_factores level. n=sum(y>0 in NB ramo). Z=n/(n+300). lambda_new=exp(Z log(lambda_NB)+(1-Z) log(lambda_ramo)). Only NB price *=lambda_new/lambda_NB.',
            'application':'Parameters train-only, pointwise. No publicg/exponents, portfolio re-centering, clipping, removal or target2025quotes. Original NB levels reused, not refitted.',
            'partitions':'Keep saved OOF2023 folds and their grouping exactly. Report saved global2024fold slices from partitions.parquet, no new splits. Bootstrap uses same existing hold2024customer/address components and same10000multiplicities/seed.'},
        'comparators':['same-family R1','same-family full own block','same-family baseline'],
        'statistics':{'metric':'D2Tweedie1.5 observedT0; no weighting nominal','bootstrap':10000,'seed':2026102301,'family':15,
            'family_scope':'12prior contrasts plus3newT2b candidate comparisons; conditional bands, NOT full adaptive-history coverage.',
            'primary':'T2b only; no A1/mix search. Global, NB, renewal, ramo; sixcells/fivefolds; original2025composition diagnostic weights unchanged.',
            'gates':{'global_family15_lower_vs_R1_gt':0.,'global_family15_lower_vs_baseline_gt':.0005,
                'NB_point_vs_R1_nonnegative':True,'NB_CI95_lower_vs_R1_floor':-.001,'sixcell_point_vs_R1_floor':-.001,
                'broad_point_vs_baseline_floor':-.001,'positive_2024folds_vs_R1_min':4,
                'influence_remove':'max(5,ceil(.001*G)) most favorable groups; delta_vsR1>=0 AND delta_vsbaseline>=0',
                'fixed_stress_broad_floor_vs_R1':-.001},
            'tail':'Report top1% positive-cost rows and group concentration; retain all claims, no truncation.',
            'composition':'Report weighted global/NB intervals with existingweights. Descriptive shift sensitivity, no support cure or selection by test labels.'},
        'controls':['Synthetic geometric endpoints/bounds and wrongyear/duplicate/invalidtarget guards','Real full loader: protected2024labels poison cannot change2023learning or quotes; traincost positivecontrol changes new layer','Allrenewal prices exact and originalparameters/sourcefiles unchanged','Independent bounded scalar optimization for3ramo constants, weighted-power formula, sklearn metric and20stored bootstrap draws','Replay application with saved parameters only; same first4 original group counts; originalbootstrap difference identities for all10000draws'],
        'stress':'All50existinglabels stress fixed candidate/R1/full/base prices only, no refit and no probabilities. Prior target-relearned receipts DO NOT certify this new rule. If nominalpasses, new targeted learning-stress proof remains needed before admission.',
        'budget':{'primary_new_kopt_constants':3,'derived_NB_levels':3,'changed_layer_replay_kopt':3,'changed_layer_positive_control_kopt':3,
            'synthetic_constants_separate':3,'verification_only_scalar_optimizations':3,'native_fits':0,'CDF_fits':0,'Booster_inference':0,'submissions':0},
        'consequence':'Any failed nominal/influence/stress gate => do not adopt or send; retain adverse result and stop this recipe. No re-tuningK, choosing ramos, changing floors or rescuing with publicscore. Even allnominalpass is exploratory and needs changed-layer learning stresses and exact production before any admission.',
        'preserve_R1_F3c_B00':True,'formal_promotion':False,'sources':{w.rel(path):w.sha(path) for path in source_paths()}}
    dump(PLAN,plan)
    forum=post('Codex. Registro NB-CRED300 antes de ajustar o puntuar. Tronco T2b, F2, forma, curvas, normalizadores y todos los precios de renovación quedan fijos. En cada ramo calcularé solo en 2023 el nivel Tweedie óptimo previo al nivel terminal; el nivel NB original se contrae geométricamente hacia ese nivel, con Z=n/(n+300), n=siniestros positivos NB de entrenamiento. Una sola receta, sin buscar K o ramos. Evalúo 2024 adaptativo frente a R1, bloque completo y base de la misma familia; no lo confundo con F3c histórico. Exijo banda condicional familia15 positiva frente a R1, margen original0,0005 frente a base, protección NB/celdas, al menos cuatro folds no negativos e influencia. Reutilizo sorteos y particiones, no repito ajustes fuente. Cincuenta escenarios se revisarán con precios fijos; no acreditaré el reaprendizaje de esta regla por recibos antiguos. Presupuesto: tres constantes nuevas y tres niveles derivados; controles del cambio separados; cero árboles, curvas, inferencia de árboles, precios2025 o envíos. Un fallo detiene la receta. R1/F3c/B00 conservados. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),'COD-S2-20261027-NB-CRED300-PREVIO','Contraccion NB hacia ramo: receta y criterios previos')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':forum})
    dump(INDEX,{'author':'Codex','utc':utc(),'status':'registered_before_new_level_fit_and_scoring','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),'forum':forum,'output':w.rel(OUT),'new_submissions':0})
    print(json.dumps({'registered':True,'plan_sha256':w.sha(PLAN)}),flush=True)
def shrink(old,ramo,n):
    assert old>0 and ramo>0 and n>=0 and math.isfinite(old+ramo+n)
    z=n/(n+K);return math.exp(z*math.log(old)+(1-z)*math.log(ramo)),z
def learn_new_layer(tr,mu,original,tag):
    assert tr.year.eq(2023).all() and tr.row_id.is_unique and set(tr.line)==set(LINES)
    assert np.isfinite(tr.y).all() and tr.y.ge(0).all() and len(mu)==len(tr) and np.isfinite(mu).all() and (mu>0).all()
    out={}
    for line in LINES:
        j=tr.line.eq(line).to_numpy();nb=j&tr.new_business.eq(1).to_numpy();assert j.any() and nb.any()
        with (OUT/'fit_attempts.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps({'utc':utc(),'tag':tag,'line':line,'operation':'kopt_ramo'})+'\n')
        level=p.v.kopt(tr.y.to_numpy()[j],mu[j]);n=int((tr.y.to_numpy()[nb]>0).sum());old=original['levels']['sin_factores'][line+'_1'];new,z=shrink(old,level,n)
        out[line]={'lambda_ramo':level,'lambda_NB_original':old,'lambda_NB_cred':new,'npositive_NB':n,'Z':z,'quote_ratio':new/old,'training_rows_ramo':int(j.sum()),'training_rows_NB':int(nb.sum())}
    return out
def apply_new_layer(frame,r1,params):
    assert frame.new_business.isin([0,1]).all();out=np.asarray(r1,float).copy();nb=frame.new_business.eq(1).to_numpy()
    ratio=frame.line.map({line:z['quote_ratio'] for line,z in params.items()}).to_numpy();assert np.isfinite(ratio).all()
    out[nb]*=ratio[nb];assert np.isfinite(out).all() and (out>0).all();return out
def fixed_mu(tr,params):
    mu=tr.base.to_numpy(float).copy()
    for factor in params['F2']:mu=p.v.factor_apply(tr,mu,p.v.ks(tr,factor['variable']),factor)
    return p.v.shape_apply(tr,mu,params['shape'])
def preflight():
    guard();checks={}
    for old,ramo,n in [(2.,.5,0),(2.,.5,300),(.5,2.,900)]:
        x,z=shrink(old,ramo,n);assert min(old,ramo)-1e-15<=x<=max(old,ramo)+1e-15
        assert math.isclose(x,old**z*ramo**(1-z),rel_tol=3e-14)
    checks['geometric_bounds_and_n0_endpoint']=shrink(2.,.5,0)[0]==.5
    rows=[]
    for i,line in enumerate(LINES):
        for b in [0,1]:
            for j in range(3):rows.append({'row_id':line+str(b)+str(j),'line':line,'new_business':b,'year':2023,'y':float((i+1)*(j+1))})
    tr=pd.DataFrame(rows);mu=np.ones(len(tr));original={'levels':{'sin_factores':{line+'_1':2. for line in LINES}}}
    pars=learn_new_layer(tr,mu,original,'synthetic')
    checks['synthetic_ramo_optimum']=all(pars[line]['lambda_ramo']==2*(i+1) for i,line in enumerate(LINES))
    base=np.ones(len(tr))*5;quote=apply_new_layer(tr,base,pars)
    checks['renewal_identity']=np.array_equal(quote[tr.new_business.eq(0)],base[tr.new_business.eq(0)])
    checks['pointwise_subset_order']=np.array_equal(apply_new_layer(tr.iloc[::-1],base[::-1],pars)[::-1],quote)
    for name,bad in [('year',tr.assign(year=2024)),('duplicate',pd.concat([tr,tr.iloc[[0]]],ignore_index=True)),('negative',tr.assign(y=-1.))]:
        try:learn_new_layer(bad,np.ones(len(bad)),original,'invalid_'+name)
        except AssertionError:checks['reject_'+name]=True
        else:raise AssertionError('Invalid scope accepted: '+name)
    checks['all_passed']=all(checks.values());dump(OUT/'preflight.json',{'utc':utc(),'checks':checks,'synthetic_ramo_constants':3});assert checks['all_passed'];print(json.dumps(checks),flush=True)
def fit():
    guard();assert w.read(OUT/'preflight.json')['checks']['all_passed'];assert not (OUT/'parameters.json').exists()
    tr=pd.read_parquet(ACTIVE/'training2023_T2b.parquet');original=w.read(ACTIVE/'parameters_T2b.json')['recipe']
    assert len(tr)==50094 and tr.groupby('customer_id').fold.nunique().le(1).all() and tr.groupby('address_id').fold.nunique().le(1).all()
    mu=fixed_mu(tr,original);old_nb=tr.line.map({l:original['levels']['sin_factores'][l+'_1'] for l in LINES})
    target=pd.read_parquet(ACTIVE/'target2024_sealed.parquet')[['row_id','y']];labels=pd.concat([tr[['row_id','y']],target],ignore_index=True);assert labels.row_id.is_unique
    def flow(pool,tag):
        train=tr.copy();train['y']=train.row_id.map(pool.set_index('row_id').y);return learn_new_layer(train,mu,original,tag)
    params=flow(labels,'primary')
    poisoned=labels.copy();held=poisoned.row_id.isin(target.row_id);poisoned.loc[held,'y']=poisoned.loc[held,'y']*7+123.
    replay=flow(poisoned,'held2024_poison');positive=labels.copy();positive.loc[positive.row_id.isin(tr.row_id),'y']*=2.;changed=flow(positive,'train_positive_control')
    assert params==replay and params!=changed
    checks={'held2024_poison_nonvacuous':not labels.loc[held,'y'].equals(poisoned.loc[held,'y']),'new_params_exact_under_held_poison':params==replay,
        'train_positive_control_changes_params':params!=changed,'original_recipe_hash_unchanged':w.sha(ACTIVE/'parameters_T2b.json')==w.read(PLAN)['sources'][w.rel(ACTIVE/'parameters_T2b.json')],
        'saved_OOF_folds_preserved':True,'train_target_hash':p.v.digest(tr[['row_id','y']]),'frozen_mu_hash':p.v.digest(mu)}
    dump(OUT/'parameters.json',{'author':'Codex','utc':utc(),'candidate':'NB_CRED300','params':params,'K':K,'original_recipe_sha256':w.sha(ACTIVE/'parameters_T2b.json'),
        'primary_kopt_constants':3,'derived_NB_levels':3,'adverse_replay_kopt_constants_separate':3,'positive_control_kopt_constants_separate':3,'checks':checks})
    pd.DataFrame({'row_id':tr.row_id,'line':tr.line,'new_business':tr.new_business,'year':tr.year,'y':tr.y,'mu_afterF2shape':mu}).to_parquet(OUT/'training_new_layer.parquet',index=False)
    print(json.dumps({'fit_complete':True,'params':params,'native_fits':0}),flush=True)
def evaluate():
    guard();assert not (OUT/'results.json').exists();dump(OUT/'evaluation_started.json',{'utc':utc(),'pid':os.getpid()})
    cols=['row_id','line','new_business','year','customer_id','address_id','exposure','sin_factores','F3c_reaprendido']
    te=pd.read_parquet(ACTIVE/'predictions_T2b.parquet',columns=cols);assert len(te)==59202 and te.row_id.is_unique and te.year.eq(2024).all()
    cached=pd.read_parquet(REVIEW/'policy_T2b.parquet').set_index('row_id');r1=te.row_id.map(cached.DOC_R1).to_numpy();base=te.sin_factores.to_numpy();full=te.F3c_reaprendido.to_numpy()
    pars=w.read(OUT/'parameters.json')['params'];candidate=apply_new_layer(te,r1,pars)
    nb=te.new_business.eq(1).to_numpy();assert np.array_equal(candidate[~nb],r1[~nb]) and np.array_equal(r1[nb],base[nb])
    te['R1']=r1;te['candidate']=candidate;te.to_parquet(OUT/'predictions2024.parquet',index=False)
    target=pd.read_parquet(ACTIVE/'target2024_sealed.parquet').set_index('row_id').y;y=te.row_id.map(target).to_numpy(float)
    groups=a.groups(te);universe,ix=np.unique(groups,return_inverse=True);G=len(universe);assert G==36408
    futureweights=np.load(ACTIVE/'composition_bootstrap_T2b.npz')['weights'];assert len(futureweights)==len(te)
    masks={'global':np.ones(len(te),bool),'new_business':nb,'renewal':~nb,**{l:te.line.eq(l).to_numpy() for l in LINES}}
    weights={name:mask.astype(float) for name,mask in masks.items()};weights['mix2025_global']=futureweights;weights['mix2025_new_business']=futureweights*nb;names=list(weights)
    prices={'R1':r1,'full':full,'baseline':base};gain={name:a.loss(y,value)-a.loss(y,candidate) for name,value in prices.items()}
    metrics={}
    allmasks={**masks,**{line+'_'+str(b):te.line.eq(line).to_numpy()&(nb==b) for line in LINES for b in [0,1]}}
    folds=te.row_id.map(pd.read_parquet(PARTITIONS,columns=['row_id','fold']).set_index('row_id')['fold']);assert folds.notna().all() and set(folds)==set(range(5))
    allmasks.update({'saved_fold_'+str(f):folds.eq(f).to_numpy() for f in range(5)})
    for name,mask in allmasks.items():
        den=a.null_loss(y[mask]);metrics[name]={'rows':int(mask.sum()),'D2_candidate':float(1-math.fsum(a.loss(y[mask],candidate[mask]).tolist())/den),
            **{'delta_vs_'+comp:float(math.fsum(g[mask].tolist())/den) for comp,g in gain.items()}}
    stats=[]
    for name,ww in weights.items():
        den=a.null_loss(y,ww)
        if name.startswith('mix'):metrics[name]={'rows':int((ww>0).sum()),**{'delta_vs_'+comp:float(math.fsum((g*ww).tolist())/den) for comp,g in gain.items()},'composition_only':True}
        block=[np.bincount(ix,weights=ww,minlength=G),np.bincount(ix,weights=ww*y,minlength=G),np.bincount(ix,weights=ww*np.sqrt(y),minlength=G)]
        block += [np.bincount(ix,weights=ww*gain[comp],minlength=G) for comp in COMPS];stats.append(np.stack(block,axis=1))
    flat=np.stack(stats,axis=1).reshape(G,-1);rng=np.random.default_rng(2026102301);draws=np.empty((10000,len(names),3))
    for start in range(0,10000,25):
        size=min(25,10000-start);counts=np.stack([np.bincount(rng.integers(0,G,size=G),minlength=G) for _ in range(size)])
        if start==0:
            assert np.array_equal(counts[:4],np.load(REVIEW/'first4_original_group_multiplicities.npy'))
            np.save(OUT/'first20_original_group_counts.npy',counts[:20])
        z=(counts@flat).reshape(size,len(names),6);den=8*(np.sqrt(z[:,:,0]*z[:,:,1])-z[:,:,2]);assert (den>0).all();draws[start:start+size]=z[:,:,3:]/den[:,:,None]
    np.savez_compressed(OUT/'bootstrap_new_statistics.npz',delta=draws,segments=names,comparisons=COMPS)
    for si,name in enumerate(names):
        for ci,comp in enumerate(COMPS):
            metrics[name]['CI95_vs_'+comp]=np.quantile(draws[:,si,ci],[.025,.975]).tolist();metrics[name]['family15_vs_'+comp]=np.quantile(draws[:,si,ci],[.05/30,1-.05/30]).tolist()
    influence={}
    for comp in ['R1','baseline']:
        bygroup=np.bincount(ix,weights=gain[comp],minlength=G);order=np.argsort(-bygroup,kind='stable');remove=max(5,math.ceil(.001*G));keep=~np.isin(ix,order[:remove])
        influence[comp]={'groups':G,'removed':remove,'delta_after_top_removal':float(math.fsum(gain[comp][keep].tolist())/a.null_loss(y[keep]))}
    positive=np.flatnonzero(y>0);top=positive[np.argsort(-y[positive],kind='stable')[:max(1,math.ceil(.01*len(positive)))]]
    tail={'rows':len(top),'share_of_T0':float(y[top].sum()/y.sum()),'gain_deviance_vs_R1':float(math.fsum(gain['R1'][top].tolist())),
        'share_of_total_gain_vs_R1':float(gain['R1'][top].sum()/gain['R1'].sum()) if gain['R1'].sum()!=0 else None}
    guards={'global_family15_lower_vs_R1_positive':metrics['global']['family15_vs_R1'][0]>0,
        'global_family15_lower_vs_baseline_gt_margin':metrics['global']['family15_vs_baseline'][0]>.0005,
        'NB_point_nonnegative_and_CI95_floor':metrics['new_business']['delta_vs_R1']>=0 and metrics['new_business']['CI95_vs_R1'][0]>=-.001,
        'all_sixcell_floor_vs_R1':all(metrics[l+'_'+str(b)]['delta_vs_R1']>=-.001 for l in LINES for b in [0,1]),
        'broad_floor_vs_baseline':all(metrics[n]['delta_vs_baseline']>=-.001 for n in ['motor','buildings','contents','new_business','renewal']),
        'at_least4_savedfolds_nonnegative':sum(metrics['saved_fold_'+str(f)]['delta_vs_R1']>=0 for f in range(5))>=4,
        'influence_top_removal_nonnegative':all(z['delta_after_top_removal']>=0 for z in influence.values()),'renewal_exact_R1':np.array_equal(candidate[~nb],r1[~nb])}
    guard();dump(OUT/'results.json',{'author':'Codex','utc':utc(),'candidate':'NB_CRED300','metrics':metrics,'influence':influence,'tail':tail,'nominal_guards':guards,
        'all_nominal_guards_pass':all(guards.values()),'same_original_group_multiplicities':True,'family':15,'2024_adaptive':True,'new_native_fits':0,'new_submissions':0})
    print(json.dumps({'global':metrics['global'],'NB':metrics['new_business'],'nominal_guards':guards,'influence':influence}),flush=True)
def stress():
    guard();te=pd.read_parquet(OUT/'predictions2024.parquet');candidate=te.candidate.to_numpy();r1=te.R1.to_numpy();base=te.sin_factores.to_numpy();nb=te.new_business.eq(1).to_numpy()
    records=[];specs=w.read(ACTIVE/'scenario_results.json')['scenarios']
    for i,spec in enumerate(specs):
        pack=np.load(ACTIVE/'scenarios'/f'{i:02d}.npz');y=pack['y'];assert y.shape==(len(te),)
        masks={'global':np.ones(len(te),bool),'new_business':nb,'renewal':~nb,**{l:te.line.eq(l).to_numpy() for l in LINES}}
        values={}
        for name,mask in masks.items():
            den=a.null_loss(y[mask]);values[name]={'delta_vs_R1':float(math.fsum((a.loss(y[mask],r1[mask])-a.loss(y[mask],candidate[mask])).tolist())/den),
                'delta_vs_baseline':float(math.fsum((a.loss(y[mask],base[mask])-a.loss(y[mask],candidate[mask])).tolist())/den)}
        records.append({'scenario':spec['scenario'],'metrics':values})
    worst=min(z['metrics'][s]['delta_vs_R1'] for z in records for s in ['new_business','renewal','motor','buildings','contents'])
    dump(OUT/'fixed_price_stresses.json',{'utc':utc(),'scenarios':records,'worst_broad_delta_vs_R1':worst,'fixed_stress_floor_pass':worst>=-.001,
        'source_and_target_learning_not_replayed':True,'new_closed_or_native_fits':0,'no_probabilities_or_ultimate_adequacy_claim':True})
    print(json.dumps({'scenarios':len(records),'worst_broad_delta_vs_R1':worst,'fixed_stress_floor_pass':worst>=-.001}),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');arg=argparse.ArgumentParser();arg.add_argument('mode',choices=['freeze','preflight','fit','evaluate','stress']);args=arg.parse_args()
    with threadpool_limits(limits=2):globals()[args.mode]()
