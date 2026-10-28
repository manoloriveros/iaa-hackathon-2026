"""Evaluación temporal de la familia F3c registrada, sin CSV de concurso nuevo.

La reproducción exacta de producción es una vía separada. Los bloques públicos
siguen condicionados por su historia y 2024 sigue siendo desarrollo adaptativo.
"""
from pathlib import Path
import argparse,collections,gc,json,math,os,sys
import importlib.util
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
f=module('full_F3c_source',R/'herramientas/validar_F3c_completo.py')
a=f.a;v=f.v;w=f.w;OUT=f.OUT;read=f.read;sha=f.sha;dump=f.dump
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
audit=module('full_F3c_math',R/'herramientas/auditar_evaluacion_documento.py')
LINES=f.LINES;NAMES=['public_full','public_noown','trainlevel_full','trainlevel_noown']
COMPS=[('public_full','public_noown'),('trainlevel_full','trainlevel_noown'),('public_full','trainlevel_full')]
COUNTS=collections.Counter();ROLE='primary'
original_kopt=v.kopt
def kopt(y,mu):
    COUNTS[ROLE+'_kopt']+=1;return original_kopt(y,mu)
v.kopt=kopt

def guard():
    if f.HISTORY_ADMISSION.exists():
        f.guard();assert sha(Path(__file__))==read(f.HISTORY_ADMISSION)['evaluator_code_sha256'];return
    f.guard();sealpath=OUT/'evaluator_implementation_correction.json'
    if not sealpath.exists():sealpath=OUT/'evaluator_control_amendment.json'
    if not sealpath.exists():sealpath=OUT/'evaluator_amendment1.json'
    if not sealpath.exists():sealpath=OUT/'evaluator_sealed.json'
    assert sha(Path(__file__))==read(sealpath)['code_sha256']

def admit_implementation():
    f.guard();assert not (OUT/'parameters.json').exists() and not (OUT/'target_started.json').exists()
    body='Codex. El cotejo de claves con el JSON congelado detectó antes del ajuste destino que NB_shapes ya usa motor_1/buildings_1/contents_1; añadir otro sufijo habría omitido sus formas al no encontrar celdas. Corrijo la implementación para usar esas claves exactas e incorporo rechazo de claves desconocidas y un control de que cada forma configurada cambia su celda y conserva las demás. La receta matemática ya preinscrita no cambia: se hace efectiva y comprobable. El error no produjo parámetros, predicciones o scores destino. Se conservan código y sellos anteriores, fuente nativa intacta, sin repetir entrenamientos terminados ni enviar.'
    forum=f.post(body,'COD-S2-20261028-F3C-COMPLETO-CLAVES-PREVIO','F3c completo: claves de formas verificadas antes del ajuste destino')
    dump(OUT/'evaluator_implementation_correction.json',{'author':'Codex','utc':f.utc(),'code_sha256':sha(Path(__file__)),'previous_admission_sha256':sha(OUT/'evaluator_control_amendment.json'),'logical_recipe_unchanged':True,'target_learning_not_started':True,'correction':'Use frozen NB_shapes cell keys directly; reject unknown shape keys, never silently skip an invalid configuration.','forum':forum,'new_submissions':0})
    print(json.dumps({'implementation_corrected_before_target_learning':True,'code_sha256':sha(Path(__file__))}),flush=True)

def admit_control():
    f.guard();assert not (OUT/'parameters.json').exists() and not (OUT/'target_started.json').exists()
    body='Codex. Refuerzo técnico del control positivo antes de aprender o puntuar destino: duplicar uniformemente todos los costos2023 mueve el nivel del tronco, pero puede dejar invariantes los factores relativos por diseño. Para comprobar su sensibilidad real se duplicarán los costos y periles de una de cada tres filas2023, con índice fijo del cargador;2024 no cambia. La corrida primaria, receta, exposición, puente, semillas, criterios y presupuesto nativo permanecen iguales. Se conserva el sello anterior. No se deriva de un score y no agrega una variante de precio; es un control adverso separado, sin envíos.'
    forum=f.post(body,'COD-S2-20261028-F3C-COMPLETO-CONTROL-PREVIO','F3c completo: control positivo no uniforme antes del aprendizaje destino')
    dump(OUT/'evaluator_control_amendment.json',{'author':'Codex','utc':f.utc(),'code_sha256':sha(Path(__file__)),'previous_admission_sha256':sha(OUT/'evaluator_amendment1.json'),'primary_recipe_unchanged':True,'target_learning_not_started':True,'positive_control':'Double2023cost/perily onlywhere fixed loader index modulo3=0; no2024changes. Relative residual coefficients must materially change.','forum':forum,'new_submissions':0})
    print(json.dumps({'control_admitted_before_target_learning':True,'code_sha256':sha(Path(__file__))}),flush=True)

def amend():
    f.guard();assert not (OUT/'parameters.json').exists() and not (OUT/'target_started.json').exists()
    body='Codex. Enmienda de integridad antes de todo aprendizaje o score destino, por cotejo de evaluar_final.py y construir_F2/final/F3c: los CSV originales contienen primas del período, E por tasa, no tasas anuales sin exposición. La neutralización F1 conserva el total de primas E_A1×riesgo; la mezcla conserva .5prima_A1+.5prima_T2b. La aplicación de F2/formas/factores se normaliza sobre primas últimas y usa exposición, con q=1; solo después se aplica qT2b para contrastar incurrido2024. Los factores y razones locales se siguen aprendiendo sobre T0 observado2023, como en el legado; el nivel final de la sensibilidad2023 se estima después del mismo puente. Corrijo el borrador anual/observado: no hay target_started, parámetros ni scores nuevos abiertos. Se conserva el evaluador inicial por SHA y commit, sin reescribir el plan original. No cambian modelos fuente, semillas, curvas, variables, criterios o presupuesto; no se repiten ajustes terminados. Cero envíos.'
    forum=f.post(body,'COD-S2-20261028-F3C-COMPLETO-PUENTE-PREVIO','F3c completo: corrección de exposición y puente antes de calibrar o puntuar')
    dump(OUT/'evaluator_amendment1.json',{'author':'Codex','utc':f.utc(),'code_sha256':sha(Path(__file__)),'original_seal_sha256':sha(OUT/'evaluator_sealed.json'),'initial_code_sha256':sha(OUT/'evaluator_initial_frozen.py'),'plan_sha256':sha(f.PLAN),
        'reason':'Source-equation correction, not a score-driven recipe search. Freeze before any target learning/evaluation.',
        'formula':'A1ultimate=round4(E)*exp(mean3logrisk)*balance; neutralize sumultimate F1 to N0 byramo. Mixultimate=.5A1ultimate+.5(T2bobservedC1/q). Normalize and transform ultimatepremiums with exposure and q=1; bridge toobserved onlyatend withqT2b.',
        'sources':{str(p):sha(p) for p in [ROOT/'Hackaton/Semana 2/Claude/validacion_nocturna_20261023/codigo/evaluar_final.py',R/'src/semana2/lineas/mision017_20261025/codigo/construir_F2.py',R/'src/semana2/lineas/mision017_20261025/codigo/construir_final.py']},'forum':forum,'native_source_recipe_unchanged':True,'new_submissions':0})
    print(json.dumps({'admitted_before_target_learning':True,'code_sha256':sha(Path(__file__)),'forum':forum}),flush=True)

def seal():
    f.guard();assert not (OUT/'predictions2024.parquet').exists()
    receipt={'author':'Codex','utc':f.utc(),'code_sha256':sha(Path(__file__)),'plan_sha256':sha(f.PLAN),
        'mathematics':'Implements the frozen plan; no target learning or score opened before this seal.',
        'clarifications':['F1 neutralization uses the annual-price portfolio as frozen for the production-family analogue. Legacy2024 evaluation instead neutralized observed-cost portfolios; retain this distinction.',
        '2023OOF consists of leave-componentfold target levels with a common source2021-23 model and training2023 pooled completion; it is training material, not unbiased nestedOOF.',
        'C1 is a second ramo-level calibration learned on2023OOF; target mixture observes commonT2bq after averaging annualrates.',
        'The typo entrenamiento2013 in the prior forum comment means entrenamiento2023; the JSON plan and paths already specify2023.'],
        'new_submissions':0,'private_validation_not_independent':True}
    dump(OUT/'evaluator_sealed.json',receipt)
    print(json.dumps(receipt),flush=True)

def load_em(poison=False,positive=False):
    em=pd.concat([pd.read_parquet(f.ACTIVE/'prepared'/('emerging_'+line+'.parquet')) for line in LINES],ignore_index=True)
    assert em.row_id.is_unique and set(em.year)=={2023,2024}
    if poison or positive:
        mask=em.year.eq(2024 if poison else 2023)
        if positive:mask=mask&(np.arange(len(em))%3==0)
        for col in ['y']+[c for c in em if c.startswith('y_')]:em.loc[mask,col]=em.loc[mask,col]* (17 if poison else 2)+(123 if poison else 0)
    return em

def source_raw(tag,family):
    records=[]
    for line in LINES:
        seeds=[]
        for seed in f.SEEDS:
            rec=read(f.source_folder(line,tag,family,seed)/'complete.json')
            assert sha(ROOT/rec['model'])==rec['model_sha256'] and sha(ROOT/rec['raw'])==rec['raw_sha256']
            raw=pd.read_parquet(ROOT/rec['raw']).set_index('row_id').raw
            seeds.append(raw)
        assert all(seeds[0].index.equals(s.index) for s in seeds)
        records.append(pd.Series(np.mean(np.stack([s.to_numpy() for s in seeds]),axis=0),index=seeds[0].index))
    out=pd.concat(records);assert out.index.is_unique;return out

def base_scope(em,raw,F,fold,style,balance=False):
    tm=em.year.eq(2023)&(em.fold.ne(fold) if fold is not None else True)
    vm=em.year.eq(2024) if fold is None else em.year.eq(2023)&em.fold.eq(fold)
    tr=em[tm].copy().reset_index(drop=True);ev=em[vm].copy().reset_index(drop=True)
    pars={};ev['q']=np.nan;ev['annual']=np.nan
    for line in LINES:
        i=tr.line.eq(line);j=ev.line.eq(line)
        qt,qe,weights=a.completion(tr[i],ev[j],line,F,style)
        et=tr.loc[i,'exposure'].to_numpy(float);ee=ev.loc[j,'exposure'].to_numpy(float)
        if style=='A1':et=et.round(4);ee=ee.round(4)
        mu=np.exp(tr.loc[i,'row_id'].map(raw).to_numpy())*et*qt
        assert np.isfinite(mu).all() and (mu>0).all()
        if balance:COUNTS[ROLE+'_balance']+=1;level=float(tr.loc[i,'y'].sum()/mu.sum())
        else:level=kopt(tr.loc[i,'y'].to_numpy(float),mu)
        ev.loc[j,'q']=qe;ev.loc[j,'annual']=np.exp(ev.loc[j,'row_id'].map(raw).to_numpy())*level
        pars[line]={'level':level,'weights':weights,'kind':'balance' if balance else 'Tweedie'}
    return ev,pars

def build_trunk(em,raws):
    FC=a.parse_curves(read(f.ACTIVE/'curves_full.json')['full']);FT=a.t2b_curves()
    scope_params={};parts=[];target=None
    for fold in [0,1,2,3,4,None]:
        t,pt=base_scope(em,raws['T2b'],FT,fold,'T2b');n,pn=base_scope(em,raws['N0'],FC,fold,'A1',True);h,ph=base_scope(em,raws['F1'],FC,fold,'A1',True)
        assert np.array_equal(t.row_id,n.row_id) and np.array_equal(t.row_id,h.row_id)
        # Production CSV carries period premium, including rounded exposure.
        neutral={}
        for line in LINES:
            j=t.line.eq(line);expo=t.loc[j,'exposure'].to_numpy().round(4)
            ratio=float(np.sum(n.loc[j,'annual'].to_numpy()*expo)/np.sum(h.loc[j,'annual'].to_numpy()*expo));h.loc[j,'annual']*=ratio;neutral[line]=ratio
        t['A1_N0']=n.annual.to_numpy()*t.exposure.to_numpy().round(4);t['A1_F1']=h.annual.to_numpy()*t.exposure.to_numpy().round(4);t['T2b_raw']=t.annual.to_numpy()*t.exposure.to_numpy()*t.q.to_numpy()
        scope_params[str(fold)]={'T2b':pt,'N0':pn,'F1':ph,'periodpremium_F1_neutralizers':neutral}
        if fold is None:target=t
        else:parts.append(t)
    train=pd.concat(parts,ignore_index=True).sort_values('row_id').reset_index(drop=True);target=target.sort_values('row_id').reset_index(drop=True)
    C1={line:kopt(train.loc[train.line.eq(line),'y'].to_numpy(),train.loc[train.line.eq(line),'T2b_raw'].to_numpy()) for line in LINES}
    for t in [train,target]:
        t['T2b_C1']=t.T2b_raw*t.line.map(C1);t['mix']=.5*(t.A1_F1*t.q+t.T2b_C1)
        assert np.isfinite(t['mix']).all() and (t['mix']>0).all()
    return train,target,{'scopes':scope_params,'C1':C1}

def bycell_mult(t,mu,pars):return mu*np.array([pars[c] for c in v.cells(t)])
def batch_factor(t,mu,p,var):
    factors={(u,key):z for u,key,z in p['factors']};cell=v.cells(t);unit=cell if p['kind']=='ae' else t.line.to_numpy()
    out=mu*np.array([factors.get((u,str(key)),1.) for u,key in zip(unit,v.ks(t,var))])
    for cc in np.unique(cell):
        j=cell==cc;out[j]*=float(mu[j].sum()/out[j].sum())
    return out

def batch_shape(t,mu,powers):
    assert set(powers).issubset({line+'_'+str(b) for line in LINES for b in [0,1]}),'Unknown shape cell key'
    cell=v.cells(t);out=mu.copy();ef=(t.exposure*t.q).to_numpy(float)
    for cc,power in powers.items():
        j=cell==cc
        if not j.any():continue
        gm=float(mu[j].sum()/ef[j].sum());z=ef[j]*gm*(mu[j]/ef[j]/gm)**power;out[j]=z*mu[j].sum()/z.sum()
    return out

def ratios(t,before,after):
    c=v.cells(t);y=t.y.to_numpy(float)
    return {cc:kopt(y[c==cc],after[c==cc])/kopt(y[c==cc],before[c==cc]) for cc in np.unique(c)}

def transform_f2(t,mu,params):
    out=mu.copy()
    for p in params['F2']:out=batch_factor(t,out,p,p['variable'])
    return batch_shape(t,out,{'motor_0':.9})

def transform_own(t,mu,params):
    out=mu.copy()
    for p in params['own']:out=batch_factor(t,out,p,p['variable'])
    return out

def apply_recipe(t,params):
    pb=read(f.PLAN)['preprocessing_full_structure']['public_blocks']
    bridge=t.q.to_numpy(float).copy();u=t.copy(deep=False);u['q']=1.;u['mix']=t['mix'].to_numpy()/bridge
    t=u
    # Actual full F3c: g -> F2/shape -> local ratios -> public NB forms/levels -> own.
    public=transform_f2(t,t['mix'].to_numpy()*pb['g'],params);public=bycell_mult(t,public,params['F2_ratio'])
    powers=pb['NB_shapes'];assert set(powers)=={'motor_1','buildings_1','contents_1'}
    public=batch_shape(t,public,powers);public=bycell_mult(t,public,params['shape_ratio']);public=bycell_mult(t,public,pb['cell_level_relative_to_g'])
    pubown=bycell_mult(t,transform_own(t,public,params),params['own_ratio'])
    secondary=bycell_mult(t,transform_f2(t,t['mix'].to_numpy(),params),params['F2_ratio'])
    secown=bycell_mult(t,transform_own(t,secondary,params),params['own_ratio'])
    return {'public_noown':public*bridge,'public_full':pubown*bridge,'trainlevel_noown':bycell_mult(t,secondary,params['secondary_levels']['noown'])*bridge,
        'trainlevel_full':bycell_mult(t,secown,params['secondary_levels']['full'])*bridge}

def learn_recipe(tr):
    assert tr.year.eq(2023).all() and tr.row_id.is_unique and np.isfinite(tr.y).all()
    pb=read(f.PLAN)['preprocessing_full_structure']['public_blocks'];params={'F2':[],'own':[]};m=tr.T2b_raw.to_numpy().copy()
    for var in ['ncb','prior']:
        p=v.factor_train(tr,m,'ae',v.ks(tr,var));p['variable']=var;params['F2'].append(p);m=batch_factor(tr,m,p,var)
    m=batch_shape(tr,m,{'motor_0':.9});params['F2_ratio']=ratios(tr,tr.T2b_raw.to_numpy(),m)
    form=batch_shape(tr,m,pb['NB_shapes']);params['shape_ratio']=ratios(tr,m,form)
    ownbase=batch_shape(tr,m,{'motor_1':pb['own_training_motor_NB_shape_A_M1']});mown=ownbase.copy()
    for var,lines in v.SEQ:
        p=v.factor_train(tr,mown,'tw',v.ks(tr,var),lines);p['variable']=var;params['own'].append(p);mown=batch_factor(tr,mown,p,var)
    params['own_ratio']=ratios(tr,ownbase,mown)
    bridge=tr.q.to_numpy(float);u=tr.copy(deep=False);u['q']=1.;u['mix']=tr['mix'].to_numpy()/bridge
    secondary=bycell_mult(u,transform_f2(u,u['mix'].to_numpy(),params),params['F2_ratio']);secown=bycell_mult(u,transform_own(u,secondary,params),params['own_ratio'])
    secondary*=bridge;secown*=bridge
    cell=v.cells(tr);y=tr.y.to_numpy();params['secondary_levels']={}
    for name,mu in [('noown',secondary),('full',secown)]:params['secondary_levels'][name]={cc:kopt(y[cell==cc],mu[cell==cc]) for cc in np.unique(cell)}
    return params

def predict():
    global ROLE
    guard();assert all(read(f.source_marker(line))['source2024_poison_replay_exact'] for line in LINES)
    assert read(OUT/'original_history_preflight.json')['all_passed'] and read(OUT/'feature_value_parity_corrected_metadata.json')['all_passed']
    assert not (OUT/'parameters.json').exists()
    dump(OUT/'target_started.json',{'utc':f.utc(),'pid':os.getpid(),'evaluator_sha256':sha(Path(__file__))})
    em=load_em();raws={family:source_raw('baseline',family) for family in ['N0','F1']};raws['T2b']=a.t2b_raw()
    tr,te,trunk=build_trunk(em,raws);params=learn_recipe(tr);pred=apply_recipe(te,params);primary_counts=dict(COUNTS)
    assert len(tr)==50094 and len(te)==59202 and tr.groupby('customer_id').fold.nunique().le(1).all() and tr.groupby('address_id').fold.nunique().le(1).all()
    y=te[['row_id','y']].copy();te['y']=np.nan
    for name,values in pred.items():te[name]=values
    tr.to_parquet(OUT/'training2023.parquet',index=False);te.to_parquet(OUT/'predictions2024.parquet',index=False);y.to_parquet(OUT/'labels2024.parquet',index=False)
    dump(OUT/'parameters.json',{'utc':f.utc(),'recipe':params,'trunk':trunk,'primary_counts':primary_counts})
    # Real full target loader, source replay outputs, target learning and all postprocessing.
    ROLE='held2024_poison';poison=load_em(poison=True);rp={family:source_raw('poison2024',family) for family in ['N0','F1']};rp['T2b']=raws['T2b']
    rt,re,rtp=build_trunk(poison,rp);rparams=learn_recipe(rt);rpred=apply_recipe(re,rparams)
    checks={'source_replays_all_exact':True,'held2024_changed_before_actual_loader':bool((poison.loc[poison.year.eq(2024),'y'].to_numpy()!=em.loc[em.year.eq(2024),'y'].to_numpy()).any()),
        'held2024_trunk_parameters_exact':trunk==rtp,'held2024_recipe_parameters_exact':params==rparams,'held2024_prices_exact':all(np.array_equal(pred[n],rpred[n]) for n in NAMES)}
    del poison,rt,re,rp;gc.collect()
    ROLE='positive_training_control';pos=load_em(positive=True);pt,pe,ptp=build_trunk(pos,raws);pp=learn_recipe(pt)
    checks['positive_train_changes_trunk_and_recipe']=ptp!=trunk and pp!=params
    reverse=apply_recipe(te.iloc[::-1].reset_index(drop=True),params);checks['row_permutation_tolerance']=all(np.allclose(pred[n],reverse[n][::-1],rtol=5e-14,atol=1e-9) for n in NAMES)
    replay=apply_recipe(te,read(OUT/'parameters.json')['recipe']);checks['saved_recipe_replay_exact']=all(np.array_equal(pred[n],replay[n]) for n in NAMES)
    # Normalizing over a different quote batch legitimately changes the legacy algorithm.
    subset=np.arange(0,len(te),2);sub=apply_recipe(te.iloc[subset].reset_index(drop=True),params)
    batch={n:{'median_relative':float(np.median(np.abs(sub[n]/pred[n][subset]-1))),'max_relative':float(np.max(np.abs(sub[n]/pred[n][subset]-1)))} for n in NAMES}
    checks['all_passed']=all(checks.values());dump(OUT/'target_controls.json',{'utc':f.utc(),'checks':checks,'analytical_counts':dict(COUNTS),'postprocessing_batch_dependence':batch,
        'scope':'Source newfits actually replay2024; reused curves/T2b inherit prior scoped controls, not a new refit. Historical public constants cannot become a prospective2024proof.'})
    guard();assert checks['all_passed'];print(json.dumps({'target_complete':True,'controls':checks,'counts':dict(COUNTS)}),flush=True)

def metric(y,mu,weights=None):
    wt=np.ones(len(y)) if weights is None else weights
    return float(1-math.fsum((audit.loss(y,mu)*wt).tolist())/audit.null_loss(y,wt))

def evaluate():
    guard();assert read(OUT/'target_controls.json')['checks']['all_passed'];assert not (OUT/'results.json').exists()
    te=pd.read_parquet(OUT/'predictions2024.parquet');lab=pd.read_parquet(OUT/'labels2024.parquet').set_index('row_id').y;y=te.row_id.map(lab).to_numpy();prices={n:te[n].to_numpy() for n in NAMES}
    nb=te.new_business.eq(1).to_numpy();masks={'global':np.ones(len(te),bool),'new_business':nb,'renewal':~nb,**{line:te.line.eq(line).to_numpy() for line in LINES},**{line+'_'+str(b):te.line.eq(line).to_numpy()&(nb==b) for line in LINES for b in [0,1]}}
    routes=read(ROOT/'RUTAS_PROYECTO.json');foldpath=ROOT/routes['week_2_validation_partitions'];fold=te.row_id.map(pd.read_parquet(foldpath,columns=['row_id','fold']).set_index('row_id')['fold']);assert fold.notna().all()
    masks.update({'saved_fold_'+str(k):fold.eq(k).to_numpy() for k in range(5)})
    masks.update({'duration_'+name:mask for name,mask in [('short',te.exposure.lt(.5).to_numpy()),('medium',te.exposure.ge(.5).to_numpy()&te.exposure.lt(.9).to_numpy()),('long',te.exposure.ge(.9).to_numpy())]})
    results={};gains=np.stack([audit.loss(y,prices[ref])-audit.loss(y,prices[candidate]) for candidate,ref in COMPS],axis=1)
    compnames=[c+'_vs_'+r for c,r in COMPS]
    for name,mask in masks.items():
        den=audit.null_loss(y[mask]);results[name]={'rows':int(mask.sum()),'positive_periods':int((y[mask]>0).sum()),'D2':{n:metric(y[mask],mu[mask]) for n,mu in prices.items()},'deltas':dict(zip(compnames,(gains[mask].sum(axis=0)/den).tolist()))}
    groups=audit.groups(te);universe,ix=np.unique(groups,return_inverse=True);G=len(universe);assert G==36408
    original=pd.read_parquet(f.ACTIVE/'predictions_T2b.parquet',columns=['row_id']);future=np.load(f.ACTIVE/'composition_bootstrap_T2b.npz')['weights'];fw=te.row_id.map(pd.Series(future,index=original.row_id)).to_numpy();assert np.isfinite(fw).all()
    weights={n:masks[n].astype(float) for n in ['global','new_business','renewal']+LINES};weights['mix2025_global']=fw;weights['mix2025_new_business']=fw*nb;names=list(weights)
    stats=[]
    for name,ww in weights.items():
        den=audit.null_loss(y,ww)
        if name.startswith('mix'):results[name]={'composition_only':True,'D2':{n:metric(y,mu,ww) for n,mu in prices.items()},'deltas':dict(zip(compnames,((gains*ww[:,None]).sum(axis=0)/den).tolist()))}
        vals=[ww,ww*y,ww*np.sqrt(y)]+[ww*gains[:,i] for i in range(3)];stats.append(np.stack([np.bincount(ix,weights=z,minlength=G) for z in vals],axis=1))
    flat=np.stack(stats,axis=1).reshape(G,-1);rng=np.random.default_rng(2026102301);draws=np.empty((10000,len(names),3));review=f.BASE/'revision_chat_documento_20261027'
    for start in range(0,10000,25):
        size=min(25,10000-start);counts=np.stack([np.bincount(rng.integers(0,G,size=G),minlength=G) for _ in range(size)])
        if start==0:assert np.array_equal(counts[:4],np.load(review/'first4_original_group_multiplicities.npy'));np.save(OUT/'first20_group_counts.npy',counts[:20])
        z=(counts@flat).reshape(size,len(names),6);den=8*(np.sqrt(z[:,:,0]*z[:,:,1])-z[:,:,2]);assert (den>0).all();draws[start:start+size]=z[:,:,3:]/den[:,:,None]
    np.savez_compressed(OUT/'bootstrap.npz',delta=draws,segments=names,comparisons=compnames)
    for i,name in enumerate(names):results[name]['CI95']={c:np.quantile(draws[:,i,j],[.025,.975]).tolist() for j,c in enumerate(compnames)};results[name]['family18']={c:np.quantile(draws[:,i,j],[.05/36,1-.05/36]).tolist() for j,c in enumerate(compnames)}
    influence={};gates={};positive=np.flatnonzero(y>0);top=positive[np.argsort(-y[positive],kind='stable')[:max(1,math.ceil(.01*len(positive)))]];tail={'positive_top_rows':len(top),'T0_cost_share':float(y[top].sum()/y.sum()),'gains':{}}
    for j,comp in enumerate(compnames):
        bygroup=np.bincount(ix,weights=gains[:,j],minlength=G);remove=max(5,math.ceil(.001*G));order=np.argsort(-bygroup,kind='stable');keep=~np.isin(ix,order[:remove]);delta=float(gains[keep,j].sum()/audit.null_loss(y[keep]));influence[comp]={'removed_groups':remove,'delta_after_removal':delta}
        tail['gains'][comp]=float(gains[top,j].sum())
        gates[comp]={'global_family18_lower_above_margin':results['global']['family18'][comp][0]>.0005,'NB_nonnegative_and_lower95_floor':results['new_business']['deltas'][comp]>=0 and results['new_business']['CI95'][comp][0]>=-.001,
            'broad_and_sixcell_floor':all(results[n]['deltas'][comp]>=-.001 for n in ['new_business','renewal']+LINES+[line+'_'+str(b) for line in LINES for b in [0,1]]),
            'four_savedfolds_positive':sum(results['saved_fold_'+str(k)]['deltas'][comp]>0 for k in range(5))>=4,'top_favorable_group_removal_nonnegative':delta>=0}
    stresses=[]
    specs=read(f.ACTIVE/'scenario_results.json')['scenarios']
    for i,spec in enumerate(specs):
        old=pd.read_parquet(f.ACTIVE/'predictions_T2b.parquet',columns=['row_id']);ys=np.load(f.ACTIVE/'scenarios'/f'{i:02d}.npz')['y'];ys=te.row_id.map(pd.Series(ys,index=old.row_id)).to_numpy()
        gains_s=np.stack([audit.loss(ys,prices[ref])-audit.loss(ys,prices[candidate]) for candidate,ref in COMPS],axis=1)
        values={n:dict(zip(compnames,(gains_s[masks[n]].sum(axis=0)/audit.null_loss(ys[masks[n]])).tolist())) for n in ['global','new_business','renewal']+LINES}
        stresses.append({'scenario':spec['scenario'],'deltas':values})
    stressfloors={comp:min(z['deltas'][n][comp] for z in stresses for n in ['new_business','renewal']+LINES) for comp in compnames}
    for comp in compnames:gates[comp]['50_fixed_price_stress_broad_floor']=stressfloors[comp]>=-.001
    dump(OUT/'results.json',{'author':'Codex','utc':f.utc(),'metrics':results,'influence':influence,'tail':tail,'gates':gates,'all_gates_pass':{c:all(z.values()) for c,z in gates.items()},'groups':G,'family':18,'private_generalization_established':False,'adaptive2024':True,'new_submissions':0})
    dump(OUT/'fixed_price_stresses.json',{'utc':f.utc(),'scenarios':stresses,'worst_broad_delta':stressfloors,'fixed_prices_no_relearning':True,'no_probability_or_reserve_adequacy_proof':True})
    print(json.dumps({'global':results['global'],'NB':results['new_business'],'gates':gates,'stress':stressfloors}),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser();p.add_argument('mode',choices=['seal','amend','admit_control','admit_implementation','predict','evaluate']);args=p.parse_args()
    with threadpool_limits(limits=2):globals()[args.mode]()
