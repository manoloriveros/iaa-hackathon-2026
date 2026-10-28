"""A1 y mezcla protegidas; escenarios condicionales de la receta corregida.

No altera F3c, selección, PDF o guion. El contraste sigue siendo exploratorio.
"""
from __future__ import annotations
import argparse, ast, gc, hashlib, importlib.util, json, os, sys, time, traceback
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb

REPO=Path(__file__).resolve().parents[1]
ROOT=REPO.parents[1]
PARENT=REPO/'privado/validacion_cadena_f3c/20261027T153123Z'
RUN=REPO/'privado/validacion_cadena_f3c_A1_mezcla/20261027T175434Z'
spec=importlib.util.spec_from_file_location('protected_f3c',REPO/'herramientas/validar_cadena_f3c.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
L=v.LINES;V=v.V
VIEWS=['T2b','A1','mezcla'];MODELS=['sin_factores','F3c_reaprendido','constante']
A1ROOT=REPO/'privado/reentrenamiento_completo_20261026/corrida/noche'
POL=['start_month','voluntary_excess','compulsory_excess','channel','payment_method','missed_payments_12m','new_business','renewal_count','days_quote_to_inception']
CUST=['occupation_n','marital_status','household_size','prior_claims_5y','licence_points','years_at_address','cust_tenure','has_campaign','marketing_segment']
ADDR=['urban_density','flood_zone','distance_to_river_km','elevation_m','soil_type','prop_age','property_type','roof_type','basement','trees_within_5m','listed_building','bedrooms','energy_rating','solar_panels']
LINE={'motor':['age_band','years_licensed','ncb_years','vehicle_value_group','vehicle_age','engine_size_cc','body_type','transmission','seats','vehicle_colour','fuel_type','driver_assist','cover_type','overnight_parking','vehicle_use','named_young_driver'], 'buildings':['age_band','log_si','construction_type','occupancy','days_unoccupied','smoke_alarms','accidental_damage_cover','mortgage'], 'contents':['age_band','log_si','tenure','security_level','high_value_items','accidental_damage_cover','works_from_home','lodgers','bicycle_cover']}
CAT=set('channel payment_method occupation_n marital_status marketing_segment urban_density soil_type property_type roof_type energy_rating age_band body_type transmission vehicle_colour fuel_type cover_type overnight_parking vehicle_use construction_type occupancy smoke_alarms tenure security_level'.split())
PERILS={'motor':['own_damage','third_party_prop','bodily_injury','theft','glass_hail'],'buildings':['storm','flood','escape_of_water','subsidence','fire','accidental_damage'],'contents':['theft','escape_of_water','accidental_damage','flood']}
save=v.save;read=v.read;sha=v.sha;now=v.now
_FIT_CACHE={}

def event(name,**kw):
    d={'utc':now(),'pid':os.getpid(),'event':name,**kw}
    save(RUN/'live.json',d);print(json.dumps(v.clean(d),ensure_ascii=False),flush=True)

def freeze():
    assert not (RUN/'PLAN.json').exists();RUN.mkdir(parents=True,exist_ok=True)
    plan={'id':'F3C-A1-MEZCLA-PROTEGIDAS-20261027','author':'Codex','utc':now(),
      'authorization':'Aplica la misma protección a A1 y a la mezcla, repite la comparación con y sin factores y los escenarios de la receta corregida. Guarda los resultados y las conclusiones, manteniendo F3c.',
      'evidence_class':'Exploratoria por reutilización/adaptación de2024; T2b previo ya conocido. No confirma privado ni promueve.',
      'hypothesis':'Al excluir el retenido de RKM, participaciones, matrices, árbol fuente y calibraciones se puede medir el bloque propio en A1 y en una mezcla fija.',
      'views':VIEWS,'models':MODELS,'primary_retained':'T2b del padre; A1 y mezcla sensibilidades predefinidas, sin elegir el mejor.',
      'source_A1':{'years':[2021,2022,2023],'features':'49/41/42 del A1 de confirmación; ID01 corregido, sin make_model, sin F1 ni clima, exposición redondeada4decimales como predictor y offset. Es la rama histórica de validación, no la producción F1 de tres semillas.',
        'params':{'seed':11,'learning_rate':.02,'num_leaves':31,'min_data_in_leaf':1000,'lambda_l2':10.,'max_rounds':4000,'patience':400,'num_threads':2,'deterministic':True,'force_row_wise':True},
        'round_selection':'Componentes cliente-dirección globales por mercado; sourcefold0 retenido. Curva, pesos, vocabulario y constante inicial se aprenden fuera de sourcefold0. Después refit con sus objetos completos y rondas elegidas.',
        'curves':'RKM coste por peligro, B7d, cap0.995 propio, pool de siniestros aceptados asignados a filas fuente/emergente permitidas. Ocurrencias<=2023, valoración2024 fija. Fuente inner excluye su fold0 en todos los ramos; emergente excluye outerfold. CDF de número aparte con pesos1.',
        'outer_target':'Seis ámbitos A1: full2023 y cinco train2023 sin outerfold. En cada uno se rehace curva pooled y árbol fuente. Así el raw OOF también excluye etiquetas del retenido emergente.',
        'categorical':'Vocabulario fuente inner/full solo de su train; desconocidos como ausentes. Normalizaciones puntuales heredadas, sin estadísticas destino.'},
      'reuse_T2b':'Árboles, raw y curvas del padre por SHA; no repetir ajuste fuente ya verificado. Reconstruir niveles OOF y comparar precios con padre antes de nuevos scores.',
      'mix':'50% anual A1+50% anual T2b por ramo, fijo. Base observada=.5baseobsA1+.5baseobsT2b; q_mix=baseobs/(exposicion_nominal*tasaanualmixta). Mismo vínculo entre candidatos; exposición una sola vez.',
      'target_recipe':'En cada vista aprender F2 NCB/previos, forma0.9 autos renovación, propios género/teletrabajo/marketing K300 y niveles con OOF2023. Normalizadores propios de train. Nada de exponentes, A_M1 o niveles públicos. No volver a buscar variables, K, pesos o semillas.',
      'adversarial':['Reentrenar sourcefull con costes2024 alterados de ambos mercados: argumentos/modelo/raw/curvas/parámetros/precios iguales.','Reentrenar outerfold0 con sus costes emergentes alterados antes de la curva: mismos objetos y precios para ese fold.','Control positivo modificando siniestros permitidos debe cambiar la curva.','Componentes/direcciones separados, manual RKM/integración y aplicación por lotes.'],
      'fit_budget':{'baseline_A1_native':36,'replay2024_native':6,'replay_target_fold0_native':6,'total_source_native':48,'new_T2b_native':0,'new2025_inference':0,'remote':0,'submissions':0},
      'metrics':{'power':1.5,'temporal':'59202 filas2024, T0 canónico','segments':['motor','buildings','contents','new_business','renewal'],'margin':.0005,'floor':-.001,'NB_lower95':-.001,'bootstrap':10000,'seed':2026102301,'family':6,'quantiles':[.05/12,1-.05/12],'group':'Componentes cliente-dirección2024; mismos sorteos en vistas/modelos. IC condicionales, no repiten entrenamiento.'},
      'scenarios':{'target_stress':45,'completion':5,'list':'Reservas .75/1.25 global/ramo/15peligros; opuestos BI/resto; observado tardío>90d x.5/1.5/2; cola BI/subsidence5/10%; count/cost CDF y severidad no reportada .5/1.5/2.',
        'fixed_prices':'Evaluar precios baseline frente a T0 estresado; no ajuste.',
        'target_relearned':'Volver a aprender participaciones, exposición, niveles OOF2023, F2, factores propios y nivel final con los y2023 estresados. Raw, árboles y curvas fuente por ámbito quedan fijos de baseline; precios2024 no aprenden y2024. En completitud cambiar solo vínculo/mezcla y recalibrar receta destino.',
        'scope_limit':'Sensibilidad condicional a estructuras y curvas fuente. No es refit integral de fuente ante una valoración alternativa, ni probabilidades/IC de escenarios, ni suficiencia de reservas. No nueva calibración pública.'},
      'consequence':'Conservar todos los adversos; no selección/promoción, CSV producción, PDF/guion, API/Git o publicación. NB/influencia/último/disponibilidad/independencia conservan bloqueos hasta evidencia propia.'}
    files=[Path(__file__),Path(v.__file__),REPO/'registro/semana2_politica_seleccion_v1.json',REPO/'herramientas/seleccionar_semana2.py']
    files+=list((A1ROOT/'codigo').glob('*.py'))
    files+=[PARENT/'freeze.json',PARENT/'PLAN.json',PARENT/'training_complete.json',PARENT/'baseline_parameters.json',PARENT/'baseline_predictions.parquet',PARENT/'training2023.parquet',PARENT/'resultados.json',PARENT/'verificacion.json']
    files+=list((PARENT/'models/baseline').glob('*'))
    for market in ['developed','emerging']:
        files+=[v.LEGACY/'datos'/market/(name+'.parquet') for name in ['claims','customers','addresses','weather']+['policies_'+l for l in L]]
    files+=[v.LEGACY/'datos/emerging'/f'test_{l}.parquet' for l in L]
    files+=[REPO/'privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3/target_T0_and_stresses.parquet']
    sources=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(set(files))]
    save(RUN/'PLAN.json',plan);save(RUN/'sources.json',sources)
    save(RUN/'freeze.json',{'utc':now(),'code_sha256':sha(__file__),'plan_sha256':sha(RUN/'PLAN.json'),'sources_sha256':sha(RUN/'sources.json'),'no_new_A1_or_mix_score_seen':True,'historical2024_seen':True,'T2b_parent_results_seen':True,'promotion_allowed':False})
    event('frozen',sources=len(sources))

def verify_inputs():
    f=read(RUN/'freeze.json');assert sha(__file__)==f['code_sha256'];assert sha(RUN/'PLAN.json')==f['plan_sha256'];assert sha(RUN/'sources.json')==f['sources_sha256']
    for s in read(RUN/'sources.json'):assert sha(s['path'])==s['sha256'],s['path']

def rkm(asg,source_rows,target_rows,poison=None):
    pieces=[];changed=0
    for market,rows in [('developed',source_rows),('emerging',target_rows)]:
        c=asg[market].copy()
        mask=c.loss_date.dt.year.eq(2024)
        if poison=='fold0' and market=='emerging':mask=c.period_year.eq(2023)&c.row_fold.eq(0)
        elif poison=='fold0':mask=np.zeros(len(c),bool)
        if poison:
            changed+=int(mask.sum());c.loc[mask,'net']+=c.loc[mask,'incurred_to_date']
        allowed=c.period_year.le(2023)&c.accepted&c.loss_date.dt.year.le(2023)
        excluded=rows.attrs.get('excluded_fold')
        if excluded is not None:allowed &= c.row_fold.ne(excluded)
        c=c[allowed].copy()
        c['market']=market;pieces.append(c)
    c=pd.concat(pieces,ignore_index=True)
    delay=(c.report_date-c.loss_date).dt.days.to_numpy();window=(pd.Timestamp(V)-c.loss_date).dt.days.to_numpy();net=c.net.to_numpy(float)
    assert (delay>=0).all() and (delay<=window).all() and (net>=0).all()
    size=int(window.max())//7+1;cost={};count={};details={}
    for p in sorted(c.peril.unique()):
        i=c.peril.eq(p).to_numpy();dd=delay[i]//7;ww=window[i]//7;cap=float(np.quantile(net[i],.995));weights=np.minimum(net[i],cap)
        assert weights.sum()>0
        details[p]={'rows':int(i.sum()),'cap':cap,'positive':int((weights>0).sum())}
        for w,out in [(weights,cost),(np.ones(i.sum()),count)]:
            d=np.bincount(dd,weights=w,minlength=size)[:size]
            start=np.bincount(dd,weights=w,minlength=size+1)[:size]
            end=np.bincount(np.minimum(ww,size-1)+1,weights=w,minlength=size+1)[:size]
            risk=np.cumsum(start)-np.cumsum(end)
            h=np.divide(d,risk,out=np.zeros(size),where=risk>0);assert (h>=-1e-12).all() and (h<=1+1e-12).all()
            h=np.clip(h,0,1);surv=np.cumprod((1-h)[::-1])[::-1];F=np.r_[surv[1:],1.]
            assert np.all(np.diff(F)>=-1e-12) and F.min()>=0 and F.max()<=1
            out[p]=np.r_[np.repeat(F,7),np.ones(max(0,5000-len(F)*7))][:5000]
    # Peril estimado en pool, como A1 histórico; clave por ramo para aplicar.
    C={(line,p):cost[p] for line in L for p in PERILS[line]}
    N={(line,p):count[p] for line in L for p in PERILS[line]}
    return C,N,{'claim_pool_digest':v.digest(c[['market','row_id','peril','loss_date','report_date','net']]),'cost_sha':v.digest({str(k):x for k,x in C.items()}),'count_sha':v.digest({str(k):x for k,x in N.items()}),'perils':details,'poison_changed_claims_before_filter':changed}

def curve_q(t,f,style):
    f=np.r_[f,np.ones(max(0,5000-len(f)))][:5000];G=np.r_[0,np.cumsum(f)]
    a=(V-t.period_end.to_numpy('datetime64[D]')).astype(int).clip(0);b=(V-t.period_start.to_numpy('datetime64[D]')).astype(int).clip(0)
    effective=(G[b+1]-G[a])/365.
    exposure=t.exposure.to_numpy(float).round(4) if style=='A1' else t.exposure.to_numpy(float)
    return effective/exposure

def completion(tr,te,line,F,style):
    perils=PERILS[line];e=tr.exposure.to_numpy(float).round(4) if style=='A1' else tr.exposure.to_numpy(float)
    qc={p:curve_q(tr,F[(line,p)],style) for p in perils};qe={p:curve_q(te,F[(line,p)],style) for p in perils}
    ult={p:float(tr['y_'+p].sum()/max(np.average(qc[p],weights=e),1e-9)) for p in perils};assert sum(ult.values())>0
    w={p:x/sum(ult.values()) for p,x in ult.items()};a=sum(w[p]*qc[p] for p in perils);b=sum(w[p]*qe[p] for p in perils)
    assert (a>0).all() and (b>0).all();return a,b,w

def a1_features(t,line):
    d=t.copy(deep=False);d['occupation_n']=d.occupation.astype('string').str.strip().str.lower().str.replace(r'^self-employed\s+','',regex=True).str.replace(r'\s+',' ',regex=True)
    d['cust_tenure']=d.tenure_years;d['prop_age']=d.property_age;d['has_campaign']=d.campaign_code.notna();d['exposure_model']=d.exposure.round(4)
    if line=='buildings':d['construction_type']=d.construction;d['smoke_alarms']=d.smoke_alarms.map({True:'yes',False:'no'}).fillna('missing')
    cols=POL+CUST+ADDR+LINE[line]+['exposure_model']
    out=pd.DataFrame(index=np.arange(len(d)))
    for col in cols:
        if col in CAT:out[col]=d[col].astype('string').fillna('missing').to_numpy()
        else:out[col]=pd.to_numeric(d[col],errors='coerce').to_numpy(float)
    return out

def matrix(X,cats):
    x=X.copy()
    for col,levels in cats.items():x[col]=pd.Categorical(x[col].where(x[col].isin(levels),None),categories=levels)
    return x

def prepare():
    verify_inputs();assert not (RUN/'prepared.json').exists();event('prepare_start')
    hashes=[]
    for market in ['developed','emerging']:
        event('read_originals',market=market);base,asg=v.load_market(market)
        scope=base[base.year.le(2023)].copy();scope['group'],scope['fold']=v.components(scope)
        if market=='emerging':assert set(scope.year)=={2023}
        base['group']=base.row_id.map(scope.set_index('row_id').group);base['fold']=base.row_id.map(scope.set_index('row_id').fold)
        asg=asg.merge(base[['row_id','year','fold']].rename(columns={'year':'period_year','fold':'row_fold'}),on='row_id',validate='m:1')
        (RUN/'prepared').mkdir(exist_ok=True)
        for line in L:
            p=RUN/'prepared'/f'{market}_{line}.parquet';base[base.line.eq(line)].to_parquet(p,index=False);hashes.append({'path':str(p),'sha256':sha(p)})
        p=RUN/'prepared'/f'{market}_claims.parquet';asg.to_parquet(p,index=False);hashes.append({'path':str(p),'sha256':sha(p)})
        event('prepared_market',market=market,rows=len(base),claims=len(asg));del base,asg,scope;gc.collect()
    save(RUN/'prepared.json',{'utc':now(),'files':hashes});event('preparation_complete')

def load_prepared():
    rec=read(RUN/'prepared.json')
    for f in rec['files']:assert sha(f['path'])==f['sha256']
    src=pd.concat([pd.read_parquet(RUN/'prepared'/f'developed_{l}.parquet') for l in L],ignore_index=True)
    em=pd.concat([pd.read_parquet(RUN/'prepared'/f'emerging_{l}.parquet') for l in L],ignore_index=True)
    asg={m:pd.read_parquet(RUN/'prepared'/f'{m}_claims.parquet') for m in ['developed','emerging']}
    return src,em,asg

def source_curves(src,em,asg,outer,poison=None):
    s=src[src.year.le(2023)];e=em[em.year.eq(2023)&(em.fold.ne(outer) if outer is not None else True)].copy()
    si=s[s.fold.ne(0)].copy(deep=False);si.attrs['excluded_fold']=0;s.attrs['excluded_fold']=None;e.attrs['excluded_fold']=outer
    fi,ni,ri=rkm(asg,si,e,poison);ff,nf,rf=rkm(asg,s,e,poison)
    return {'inner':fi,'full':ff,'inner_count':ni,'full_count':nf,'inner_receipt':ri,'full_receipt':rf}

def curves_json(obj):return {str(k):a.tolist() for k,a in obj.items()}
def parse_curves(obj):return {ast.literal_eval(k):np.asarray(x,float) for k,x in obj.items()}

def fit_pair(src,em,line,curves,scope):
    out=RUN/'models'/scope;out.mkdir(parents=True,exist_ok=True)
    global _FIT_CACHE
    if _FIT_CACHE.get('line')!=line:
        _FIT_CACHE.clear();gc.collect()
        dv=src[src.line.eq(line)&src.year.le(2023)].reset_index(drop=True);ev=em[em.line.eq(line)].reset_index(drop=True)
        inner=dv.fold.ne(0).to_numpy();di=dv[inner].reset_index(drop=True);dd=dv[~inner].reset_index(drop=True)
        features=a1_features(dv,line);ex=a1_features(ev,line)
        ci={c:sorted(features.loc[inner,c].unique().tolist()) for c in features if c in CAT};cf={c:sorted(features[c].unique().tolist()) for c in features if c in CAT}
        Xi=matrix(features[inner].reset_index(drop=True),ci);Xv=matrix(features[~inner].reset_index(drop=True),ci);Xf=matrix(features,cf);Xe=matrix(ex,cf)
        _FIT_CACHE={'line':line,**{k:x for k,x in locals().copy().items() if k in ['dv','ev','di','dd','ci','cf','Xi','Xv','Xf','Xe']}}
    dv,ev,di,dd,ci,cf,Xi,Xv,Xf,Xe=(_FIT_CACHE[k] for k in ['dv','ev','di','dd','ci','cf','Xi','Xv','Xf','Xe'])
    qi,qv,wi=completion(di,dd,line,curves['inner'],'A1');qf,_,wf=completion(dv,ev,line,curves['full'],'A1')
    yi=di.y.to_numpy(float);yv=dd.y.to_numpy(float);yf=dv.y.to_numpy(float)
    oi=np.log(di.exposure.to_numpy().round(4)*qi);ov=np.log(dd.exposure.to_numpy().round(4)*qv);of=np.log(dv.exposure.to_numpy().round(4)*qf)
    bi=float(np.log(yi.sum()/np.exp(oi).sum()));bf=float(np.log(yf.sum()/np.exp(of).sum()))
    p=dict(objective='tweedie',tweedie_variance_power=1.5,learning_rate=.02,num_leaves=31,min_data_in_leaf=1000,feature_fraction=.8,bagging_fraction=.8,bagging_freq=1,lambda_l2=10.,min_data_per_group=1000,cat_smooth=50,verbosity=-1,seed=11,deterministic=True,force_row_wise=True,num_threads=2)
    ah=v.digest(Xi,yi,oi+bi,Xv,yv,ov+bi,Xf,yf,of+bf,Xe,ci,cf,p,wi,wf)
    receipt=out/f'{line}_receipt.json';modelpath=out/f'{line}.txt';rawpath=out/f'{line}_raw.parquet'
    if receipt.exists() and read(receipt).get('complete'):
        rec=read(receipt);assert rec['arguments_sha256']==ah and sha(modelpath)==rec['model_sha256'];assert sha(rawpath)==rec['raw_file_sha256'];event('reuse_completed_pair',line=line,scope=scope);return rec
    rec={'utc':now(),'line':line,'scope':scope,'arguments_sha256':ah,'rows':len(dv),'inner_rows':len(di),'validation_rows':len(dd),'inner_initial_rate_log':bi,'full_initial_rate_log':bf,'inner_weights':wi,'full_weights':wf,'inner_categories':ci,'full_categories':cf,'params':p,'complete':False}
    save(receipt,rec);event('source_pair_start',line=line,scope=scope)
    for stage in ['inner','full']:
        with (RUN/'fit_attempts.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps({'utc':now(),'scope':scope,'line':line,'stage':stage})+'\n')
        if stage=='inner':
            dtr=lgb.Dataset(Xi,label=yi,init_score=oi+bi);dva=lgb.Dataset(Xv,label=yv,init_score=ov+bi,reference=dtr)
            bst=lgb.train(p,dtr,4000,valid_sets=[dva],callbacks=[lgb.early_stopping(400,verbose=False)]);rounds=max(1,bst.best_iteration)
            del bst,dtr,dva;gc.collect()
        else:bst=lgb.train(p,lgb.Dataset(Xf,label=yf,init_score=of+bf),rounds)
    center=float(np.log(np.average(np.exp(bst.predict(Xf,raw_score=True,num_threads=2)),weights=dv.exposure.to_numpy().round(4))))
    raw=bst.predict(Xe,raw_score=True,num_threads=2)-center;bst.save_model(str(modelpath))
    pd.DataFrame({'row_id':ev.row_id.to_numpy(),'raw':raw}).to_parquet(rawpath,index=False)
    rec.update(complete=True,completed_utc=now(),rounds=rounds,source_center=center,model_sha256=sha(modelpath),raw_sha256=v.digest(raw),raw_file_sha256=sha(rawpath))
    save(receipt,rec);event('source_pair_complete',line=line,scope=scope,rounds=rounds);return rec

def train():
    verify_inputs();assert read(RUN/'preflight.json')['all_passed'];src,em,asg=load_prepared()
    assert src[src.year.le(2023)].groupby('address_id').fold.nunique().le(1).all();assert em[em.year.eq(2023)].groupby('address_id').fold.nunique().le(1).all()
    curvecache={}
    for outer in [None,0,1,2,3,4]:
        scope='full' if outer is None else f'fold{outer}';cur=source_curves(src,em,asg,outer)
        save(RUN/f'curves_{scope}.json',{k:curves_json(x) if k in ['inner','full','inner_count','full_count'] else x for k,x in cur.items()})
        curvecache[scope]=cur
    checks={}
    for outer,poison in [(None,'2024'),(0,'fold0')]:
        original='full' if outer is None else 'fold0';scope='replay_'+poison
        cur=source_curves(src,em,asg,outer,poison)
        old=read(RUN/f'curves_{original}.json')
        for branch in ['inner','full','inner_count','full_count']:checks[f'{scope}_{branch}_exact']=curves_json(cur[branch])==old[branch]
        checks[scope+'_poison_changed_claims']=cur['full_receipt']['poison_changed_claims_before_filter']>0
        curvecache[scope]=cur
    for line in L:
        for scope,cur in curvecache.items():
            rec=fit_pair(src,em,line,cur,scope)
            if scope.startswith('replay_'):
                original='full' if scope=='replay_2024' else 'fold0';base=read(RUN/'models'/original/f'{line}_receipt.json')
                for field in ['arguments_sha256','rounds','model_sha256','raw_sha256']:checks[scope+'_'+line+'_'+field]=rec[field]==base[field]
    # Control positivo: multiplicar solo BI emergente permitido cambia la curva.
    altered={m:a.copy() for m,a in asg.items()};a=altered['emerging'];mask=a.loss_date.dt.year.eq(2023)&a.peril.eq('bodily_injury');a.loc[mask,'net']*=2
    cp=source_curves(src,em,altered,None);base=read(RUN/'curves_full.json');checks['positive_control_curve_changes']=curves_json(cp['full'])!=base['full']
    assert all(checks.values()),checks
    recs=[read(p) for p in (RUN/'models').glob('*/*_receipt.json')];assert len(recs)==24 and all(x['complete'] for x in recs)
    save(RUN/'source_training_complete.json',{'utc':now(),'checks':checks,'all_passed':True,'complete_pairs':len(recs),'native_fit_attempts':len((RUN/'fit_attempts.jsonl').read_text().splitlines()),'source_T2b_fits':0,'inference2025':0})
    event('source_training_complete',pairs=len(recs));del src,em,asg;gc.collect()

def raw_series(scope):return pd.concat([pd.read_parquet(RUN/'models'/scope/f'{l}_raw.parquet') for l in L],ignore_index=True).set_index('row_id').raw
def t2b_raw():return pd.concat([pd.read_parquet(PARENT/'models/baseline'/f'{l}_raw.parquet') for l in L],ignore_index=True).set_index('row_id').raw
def t2b_curves():return parse_curves(read(PARENT/'baseline_parameters.json')['source_curves'])

def target_base(em,raw,F,outer,style):
    trainmask=em.year.eq(2023)&(em.fold.ne(outer) if outer is not None else True)
    evalmask=em.year.eq(2024) if outer is None else em.year.eq(2023)&em.fold.eq(outer)
    tr=em[trainmask].copy().reset_index(drop=True);te=em[evalmask].copy().reset_index(drop=True)
    tr['raw']=tr.row_id.map(raw);te['raw']=te.row_id.map(raw)
    assert tr.raw.notna().all() and te.raw.notna().all();pars={}
    tr['q']=np.nan;te['q']=np.nan;tr['base']=np.nan;te['base']=np.nan
    for line in L:
        i=tr.line.eq(line);j=te.line.eq(line);qt,qe,w=completion(tr[i],te[j],line,F,style)
        et=tr.loc[i,'exposure'].to_numpy(float);ee=te.loc[j,'exposure'].to_numpy(float)
        if style=='A1':et=et.round(4);ee=ee.round(4)
        level=v.kopt(tr.loc[i,'y'].to_numpy(float),np.exp(tr.loc[i,'raw'].to_numpy())*et*qt)
        tr.loc[i,'q']=qt;te.loc[j,'q']=qe;tr.loc[i,'base']=level*np.exp(tr.loc[i,'raw'].to_numpy())*et*qt;te.loc[j,'base']=level*np.exp(te.loc[j,'raw'].to_numpy())*ee*qe
        pars[line]={'level':level,'weights':w}
    if style=='A1':tr['exposure']=tr.exposure.round(4);te['exposure']=te.exposure.round(4)
    return tr,te,pars

def blend(a,b):
    assert np.array_equal(a.row_id,b.row_id)
    out=a.copy();obs=.5*a.base.to_numpy()+.5*b.base.to_numpy()
    rate=.5*a.base.to_numpy()/(a.exposure*a.q).to_numpy()+.5*b.base.to_numpy()/(b.exposure*b.q).to_numpy()
    out['base']=obs;out['q']=obs/(out.exposure.to_numpy()*rate);return out

def all_base(em,raws,Fs):
    target={view:{'tr':[],'te':None,'scope_params':{}} for view in VIEWS}
    for outer in [0,1,2,3,4,None]:
        scope='full' if outer is None else f'fold{outer}'
        ta,ea,pa=target_base(em,raws[scope],Fs['A1'][scope],outer,'A1')
        tt,et,pt=target_base(em,raws['T2b'],Fs['T2b'],outer,'T2b')
        for view,tr,te,params in [('T2b',tt,et,pt),('A1',ta,ea,pa),('mezcla',blend(tt,ta),blend(et,ea),{'T2b':pt,'A1':pa,'weights':[.5,.5]})]:
            target[view]['scope_params'][scope]=params
            if outer is None:target[view]['te']=te
            else:target[view]['tr'].append(te)
    for view in VIEWS:target[view]['tr']=pd.concat(target[view]['tr'],ignore_index=True).sort_values('row_id').reset_index(drop=True)
    return target

def objects():
    raws={s:raw_series(s) for s in ['full','fold0','fold1','fold2','fold3','fold4']};raws['T2b']=t2b_raw()
    Fs={'A1':{s:parse_curves(read(RUN/f'curves_{s}.json')['full']) for s in ['full','fold0','fold1','fold2','fold3','fold4']},'T2b':t2b_curves()}
    return raws,Fs

def predictions():
    verify_inputs();assert read(RUN/'source_training_complete.json')['all_passed'];src,em,asg=load_prepared();del src,asg;gc.collect()
    raws,Fs=objects();targets=all_base(em,raws,Fs);checks={}
    for view in VIEWS:
        tr=targets[view]['tr'];te=targets[view]['te'];y=te[['row_id','y']].copy();te['y']=np.nan
        out,params=v.recipe(tr,te);rev,rp=v.recipe(tr,te.iloc[::-1].reset_index(drop=True))
        checks[view+'_row_order_invariant']=all(np.array_equal(out[k],rev[k][::-1]) for k in MODELS) and params==rp
        for k,a in out.items():te[k]=a
        tr.to_parquet(RUN/f'training2023_{view}.parquet',index=False);te.to_parquet(RUN/f'predictions_{view}.parquet',index=False)
        save(RUN/f'parameters_{view}.json',{'recipe':params,'scopes':targets[view]['scope_params']})
        if view=='T2b':
            parent=pd.read_parquet(PARENT/'baseline_predictions.parquet').set_index('row_id')
            checks['T2b_parent_prices_preserved']=all(np.allclose(te.set_index('row_id').loc[parent.index,k],parent[k],rtol=1e-10,atol=1e-9) for k in MODELS)
            y.to_parquet(RUN/'target2024_sealed.parquet',index=False)
    # Nuevas curvas/full ya repitieron entrenamiento; recalcular toda la capa
    # destino bajo y2024 alterado y con ancestros replay, sin pasar y2024 a recipe.
    poisoned=em.copy();m=poisoned.year.eq(2024)
    for c in ['y']+[c for c in em if c.startswith('y_')]:poisoned.loc[m,c]*=2
    replay_raws={**raws,'full':raw_series('replay_2024')};replay_Fs={**Fs,'A1':{**Fs['A1'],'full':parse_curves(read(RUN/'curves_full.json')['full'])}}
    rt=all_base(poisoned,replay_raws,replay_Fs)
    for view in VIEWS:
        te=rt[view]['te'];te['y']=np.nan;out,p=v.recipe(rt[view]['tr'],te)
        prev=pd.read_parquet(RUN/f'predictions_{view}.parquet');old=read(RUN/f'parameters_{view}.json')['recipe']
        checks[view+'_poison2024_params_exact']=p==old
        checks[view+'_poison2024_prices_exact']=all(np.array_equal(out[k],prev[k].to_numpy()) for k in MODELS)
    assert all(checks.values()),checks
    save(RUN/'prediction_checks.json',{'utc':now(),'checks':checks,'all_passed':True});event('predictions_complete')

def preflight():
    verify_inputs();checks={}
    # Enumeración de riesgo inverso: tres casos, ventanas que incluyen eventos.
    delay=np.array([0,1,1]);window=np.array([2,1,2]);weights=np.array([1.,1.,1.]);size=3
    risk=np.array([sum(w for d,r,w in zip(delay,window,weights) if d<=s<=r) for s in range(size)])
    events=np.bincount(delay,weights=weights,minlength=size);h=np.divide(events,risk,out=np.zeros(size),where=risk>0)
    F=np.array([np.prod(1-h[s+1:]) for s in range(size)])
    checks['manual_reverse_risk']=np.array_equal(risk,np.array([1.,3.,2.])) and np.allclose(F,[1/3,1,1],rtol=0,atol=1e-12)
    fixture=[]
    for p in sorted(set(p for ps in PERILS.values() for p in ps)):
        for n,(lag,age) in enumerate([(0,700),(371,371),(371,700)]):
            ld=pd.Timestamp(V)-pd.Timedelta(days=age)
            fixture.append({'row_id':p+str(n),'line':'motor','peril':p,'loss_date':ld,'report_date':ld+pd.Timedelta(days=lag),'net':1.,'incurred_to_date':1.,'accepted':True,'period_year':2023,'row_fold':1})
    fixture=pd.DataFrame(fixture);fake_rows=pd.DataFrame({'row_id':fixture.row_id});fake_rows.attrs['excluded_fold']=None
    empty=pd.DataFrame({'row_id':[]});empty.attrs['excluded_fold']=None
    C,N,_=rkm({'developed':fixture,'emerging':fixture.iloc[:0].copy()},fake_rows,empty)
    checks['production_RKM_matches_enumeration']=abs(C[('motor','bodily_injury')][0]-1/3)<1e-12 and C[('motor','bodily_injury')][371]==1 and np.array_equal(C[('motor','bodily_injury')],N[('motor','bodily_injury')])
    t=pd.DataFrame({'period_start':pd.to_datetime(['2024-12-30']),'period_end':pd.to_datetime(['2024-12-31']),'exposure':[2/365]})
    checks['A1_rounding_once']=np.allclose(curve_q(t,np.ones(5000),'A1'),[(2/365)/round(2/365,4)],rtol=0,atol=1e-12)
    x=pd.DataFrame({'channel':['A','B']});cats={'channel':['A']};checks['unseen_category_missing']=matrix(x,cats).channel.isna().tolist()==[False,True]
    g,f=v.components(pd.DataFrame({'customer_id':['a','b','c'],'address_id':['x','x','y']}));checks['address_component']=g[0]==g[1] and f[0]==f[1]
    checks={k:bool(a) for k,a in checks.items()};save(RUN/'preflight.json',{'utc':now(),'checks':checks,'all_passed':all(checks.values())});assert all(checks.values()),checks
    event('preflight_complete',checks=checks)

def open_evaluation():
    verify_inputs();assert read(RUN/'prediction_checks.json')['all_passed'];assert not (RUN/'opened.json').exists()
    paths=[RUN/f'predictions_{x}.parquet' for x in VIEWS]+[RUN/'target2024_sealed.parquet']
    save(RUN/'opened.json',{'utc':now(),'plan_sha256':sha(RUN/'PLAN.json'),'files':[{'path':str(p),'sha256':sha(p)} for p in paths],'first_A1_mix_scores_not_yet_computed':True,'2024_adaptive':True,'formal_promotion':False,'formal_v1_reopened':False});event('exploratory_evaluation_opened')

def segments(t):
    out={'global':np.ones(len(t),bool),'new_business':t.new_business.to_numpy(bool),'renewal':~t.new_business.to_numpy(bool)}
    for line in L:
        out[line]=t.line.eq(line).to_numpy()
        for nb in [0,1]:out[line+'_'+str(nb)]=out[line]&(t.new_business.to_numpy(int)==nb)
    return out

def metrics(t,preds,y):return {s:v.summarize(y,preds,m) for s,m in segments(t).items()}

def evaluate():
    verify_inputs()
    for f in read(RUN/'opened.json')['files']:assert sha(f['path'])==f['sha256']
    target=pd.read_parquet(RUN/'target2024_sealed.parquet').set_index('row_id').y;results={'utc':now(),'views':{}}
    for view in VIEWS:
        t=pd.read_parquet(RUN/f'predictions_{view}.parquet');y=t.row_id.map(target).to_numpy(float);pred={k:t[k].to_numpy() for k in MODELS};met=metrics(t,pred,y)
        groups,ix=np.unique(v.components(t)[0],return_inverse=True);G=len(groups);ss=['global','new_business','renewal']+L
        st=[]
        for s in ss:
            m=segments(t)[s];arr=[np.bincount(ix,weights=m,minlength=G),np.bincount(ix,weights=y*m,minlength=G),np.bincount(ix,weights=np.sqrt(y)*m,minlength=G)]+[np.bincount(ix,weights=v.dev(y,pred[k])*m,minlength=G) for k in MODELS];st.append(np.stack(arr,axis=1))
        stats=np.stack(st,axis=1);flat=stats.reshape(G,-1);rng=np.random.default_rng(2026102301);draws=np.empty((10000,len(ss),len(MODELS)))
        for start in range(0,10000,25):
            n=min(25,10000-start);counts=np.stack([np.bincount(rng.integers(0,G,size=G),minlength=G) for _ in range(n)])
            z=(counts@flat).reshape(n,len(ss),6);null=8*(np.sqrt(z[:,:,0]*z[:,:,1])-z[:,:,2]);draws[start:start+n]=1-z[:,:,3:]/null[:,:,None]
        intervals={}
        for j,s in enumerate(ss):d=draws[:,j,1]-draws[:,j,0];intervals[s]={'CI95':np.quantile(d,[.025,.975]),'family6':np.quantile(d,[.05/12,1-.05/12])}
        np.savez_compressed(RUN/f'bootstrap_{view}.npz',scores=draws,segments=ss,models=MODELS)
        gain=np.bincount(ix,weights=v.dev(y,pred[MODELS[0]])-v.dev(y,pred[MODELS[1]]),minlength=G);order=np.argsort(-gain,kind='stable');nr=max(5,int(np.ceil(.001*G)));keep=~np.isin(ix,order[:nr]);cum=np.flatnonzero(np.cumsum(gain[order])>=gain.sum())
        influence={'groups':G,'removed':nr,'delta_without_top':v.summarize(y,pred,keep)['delta'],'groups_to_erase':int(cum[0]+1) if len(cum) else None}
        guards={'global_margin':intervals['global']['family6'][0]>.0005,'NB_protection':met['new_business']['delta']>=0 and intervals['new_business']['CI95'][0]>=-.001,'segments':all(met[s]['delta']>=-.001 for s in ['motor','buildings','contents','new_business','renewal']),'motor_NB_floor':met['motor_1']['delta']>=-.001,'influence':influence['delta_without_top']>=0,'promotion':False}
        results['views'][view]={'metrics':met,'intervals':intervals,'influence':influence,'guards':guards}
        event('view_metrics_complete',view=view,delta=met['global']['delta'])
    save(RUN/'results.json',results)

def scenario_definitions():
    specs=[('reserve075','reserve',.75,None,None),('reserve125','reserve',1.25,None,None)]
    specs +=[(f'reserve_{l}_{f}','reserve',f,l,None) for l in L for f in [.75,1.25]]
    specs +=[(f'reserve_{l}_{p}_{f}','reserve',f,l,p) for l in L for p in sorted(PERILS[l]) for f in [.75,1.25]]
    specs +=[('opposed_BI125_rest075','opposed',1.25,None,None),('opposed_BI075_rest125','opposed',.75,None,None)]
    specs +=[(f'late_observed_severity_x{f}','late',f,None,None) for f in [.5,1.5,2.]]
    specs +=[(f'BI_subsidence_cost_tail_{f}','tail',f,None,None) for f in [.05,.10]]
    assert len(specs)==45;return specs

def stress_em(em,claims,spec):
    name,kind,f,line,peril=spec;c=claims.copy();accepted=c.accepted.to_numpy();net=c.net.to_numpy(float);reserve=(c.incurred_to_date-c.paid_to_date).to_numpy(float)*accepted
    mask=accepted.copy()
    if line:mask &= c.line.eq(line).to_numpy()
    if peril:mask &= c.peril.eq(peril).to_numpy()
    if kind=='reserve':delta=reserve*mask*(f-1)
    elif kind=='opposed':delta=reserve*(np.where(c.peril.eq('bodily_injury'),f,2-f)-1)
    elif kind=='late':delta=net*accepted*((c.report_date-c.loss_date).dt.days.to_numpy()>90)*(f-1)
    else:delta=net*accepted*c.peril.isin(['bodily_injury','subsidence']).to_numpy()*f
    assert np.isfinite(delta).all();out=em.copy();d=pd.Series(delta).groupby(c.row_id.to_numpy()).sum();out['y']=out.y+out.row_id.map(d).fillna(0)
    for p in sorted(c.peril.unique()):
        key='y_'+p
        if key not in out:continue
        i=c.peril.eq(p).to_numpy();z=pd.Series(delta[i]).groupby(c.loc[i,'row_id'].to_numpy()).sum();out[key]=out[key]+out.row_id.map(z).fillna(0)
    assert out.y.ge(0).all();return out

def transform_curves(F,name,N=None):
    if name=='count_curve':return N
    if name=='cost_curve_train_peril_mix':return F
    scale=float(name.split('x')[-1]);return {k:f/np.maximum(f+scale*(1-f),1e-30) for k,f in F.items()}

def scenarios():
    verify_inputs();assert (RUN/'results.json').exists();src,em,asg=load_prepared();raws,Fs=objects();del src;gc.collect()
    baseline={view:pd.read_parquet(RUN/f'predictions_{view}.parquet') for view in VIEWS}
    records=[];(RUN/'scenarios').mkdir(exist_ok=True)
    specs=scenario_definitions();names=[x[0] for x in specs]+['count_curve','cost_curve_train_peril_mix','unreported_severity_x0.5','unreported_severity_x1.5','unreported_severity_x2.0']
    # CDF número madura T2b, misma elegibilidad y ámbito fuente del padre.
    source=pd.concat([pd.read_parquet(RUN/'prepared'/f'developed_{l}.parquet',columns=['row_id','year']) for l in L]);source=source[source.year.le(2023)]
    acc=asg['developed'];acc=acc[acc.row_id.isin(set(source.row_id))&acc.accepted].copy();acc['net']=1.
    Nt=v.curves(acc,source);del source,acc;gc.collect()
    for number,name in enumerate(names):
        spec=specs[number] if number<45 else None;stressed=stress_em(em,asg['emerging'],spec) if spec else em
        usedF=Fs
        if spec is None:
            usedF={'T2b':transform_curves(Fs['T2b'],name,Nt),'A1':{}}
            for scope in Fs['A1']:
                count=parse_curves(read(RUN/f'curves_{scope}.json')['full_count']);usedF['A1'][scope]=transform_curves(Fs['A1'][scope],name,count)
        targets=all_base(stressed,raws,usedF);bundle=[];params={};result={'scenario':name,'index':number,'conditional_source_fixed':True,'views':{}}
        for view in VIEWS:
            tr=targets[view]['tr'];te=targets[view]['te'];y=te.y.to_numpy(float).copy();te['y']=np.nan;out,p=v.recipe(tr,te);params[view]={'recipe':p,'scopes':targets[view]['scope_params']};bundle.append(np.stack([out[k] for k in MODELS]))
            fixed={k:baseline[view][k].to_numpy() for k in MODELS}
            result['views'][view]={'fixed_prices':metrics(te,fixed,y),'target_relearned':metrics(te,out,y)}
        np.savez_compressed(RUN/'scenarios'/f'{number:02d}.npz',predictions=np.stack(bundle),y=y,views=VIEWS,models=MODELS)
        save(RUN/'scenarios'/f'{number:02d}_parameters.json',params);records.append(result)
        save(RUN/'scenario_results_partial.json',{'utc':now(),'completed':len(records),'scenarios':records})
        event('scenario_complete',scenario=name,completed=len(records),total=50)
    save(RUN/'scenario_results.json',{'utc':now(),'scenarios':records,'target_scenarios':45,'completion_scenarios':5,'scope':'Árboles y curvas fuente por ámbito baseline congelados. Participaciones y receta destino reaprendidas solo2023. No probabilidades, nuevo público o refit integral fuente.'})

def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['freeze','preflight','prepare','train','predict','open','evaluate','scenarios','verify']);a=p.parse_args()
    try:
        {'freeze':freeze,'preflight':preflight,'prepare':prepare,'train':train,'predict':predictions,'open':open_evaluation,'evaluate':evaluate,'scenarios':scenarios,'verify':verify_inputs}[a.stage]()
    except Exception:
        if RUN.exists():save(RUN/('failure_'+str(time.time_ns())+'.json'),{'utc':now(),'stage':a.stage,'error':traceback.format_exc()})
        raise

if __name__=='__main__':main()
