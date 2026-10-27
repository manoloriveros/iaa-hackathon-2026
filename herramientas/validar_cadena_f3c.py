"""Reevaluación exploratoria protegida del contraste primario F3c/SF.

No modifica producción ni reabre la selección v1. Las etiquetas se valoran a
2024: proteger el cálculo no reconstruye la información disponible en 2023.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, os, platform, sys, time
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import lightgbm as lgb

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
LEGACY = REPO/'privado/reentrenamiento_completo_20261026/corrida/ml'
V = np.datetime64('2024-12-31', 'D')
LINES = ['motor', 'buildings', 'contents']
RUN = REPO/'privado/validacion_cadena_f3c/20261027T153123Z'
SEQ = [('gender', ['motor','contents']), ('works_from_home',['contents']), ('marketing_segment',['contents'])]
POLIZA = ['voluntary_excess','channel','payment_method','missed_payments_12m','new_business','renewal_count','log_days_quote','discount_applied','start_month','full_year','hist_pol_12m','hist_cli_12m']
CLIENTE = ['marital_status','household_size','prior_claims_5y','licence_points','years_at_address','tenure_years','age_band','occupation']
DIRECCION = ['urban_density','flood_zone','distance_to_river_km','elevation_m','soil_type','property_age','property_type','roof_type','basement','trees_within_5m','listed_building','bedrooms','energy_rating','solar_panels','clima_wind_exposure_index','clima_wildfire_index','clima_rainfall_mm','clima_mean_temperature_c']
RAMO = {'motor':['years_licensed','ncb_years','vehicle_value_group','vehicle_age','engine_size_cc','body_type','transmission','seats','fuel_type','driver_assist','cover_type','overnight_parking','vehicle_use','named_young_driver'], 'buildings':['log_si','construction','occupancy','days_unoccupied','smoke_alarms','accidental_damage_cover','mortgage'], 'contents':['log_si','tenure','security_level','high_value_items','accidental_damage_cover','works_from_home','lodgers','bicycle_cover']}
CATS = set('channel payment_method marital_status age_band occupation email_domain document_preference previous_insurer campaign_code marketing_segment urban_density soil_type property_type roof_type energy_rating body_type transmission fuel_type cover_type overnight_parking vehicle_use construction occupancy tenure security_level gender region make_model branch_id'.split())
WEATHER = ['wind_exposure_index','wildfire_index','rainfall_mm','mean_temperature_c']
CONSTR = {'brick':'brick','brk':'brick','stone':'stone','stn':'stone','t':'timber','w':'timber','wod':'timber','non_standard':'non_standard','mix':'non_standard'}

def now(): return datetime.now(timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def clean(x):
    if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v) for v in x]
    if isinstance(x,np.ndarray):return clean(x.tolist())
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,Path):return str(x)
    return x
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def digest(*args):
    h=hashlib.sha256()
    for x in args:
        if isinstance(x,pd.DataFrame):
            h.update(json.dumps([(str(c),str(x[c].dtype)) for c in x],ensure_ascii=False).encode())
            for c in x:
                if isinstance(x[c].dtype,pd.CategoricalDtype):h.update(json.dumps(x[c].cat.categories.tolist()).encode())
            h.update(pd.util.hash_pandas_object(x,index=False).to_numpy().tobytes())
        elif isinstance(x,np.ndarray):h.update(str((x.dtype,x.shape)).encode());h.update(np.ascontiguousarray(x).tobytes())
        else:h.update(json.dumps(clean(x),sort_keys=True).encode())
    return h.hexdigest()
def dev(y,m):
    y=np.asarray(y,float);m=np.asarray(m,float)
    assert np.isfinite(y).all() and (y>=0).all() and np.isfinite(m).all() and (m>0).all()
    return 4*(y/np.sqrt(m)+np.sqrt(m)-2*np.sqrt(y))
def kopt(y,m):return float(np.sum(y/np.sqrt(m))/np.sqrt(m).sum())
def cells(t):return (t.line.astype(str)+'_'+t.new_business.astype(int).astype(str)).to_numpy()
def ks(t,v):
    if v=='ncb':return np.where(t.line.to_numpy()=='motor',pd.cut(pd.to_numeric(t.ncb_years,errors='coerce').fillna(0),[-1,0,2,5,9,99],labels=['0','1-2','3-5','6-9','10+']).astype(str),'x')
    if v=='prior':return np.minimum(pd.to_numeric(t.prior_claims_5y,errors='coerce').fillna(0).to_numpy(),2).astype(int).astype(str)
    return t[v].astype(str).to_numpy()

def freeze():
    assert not (RUN/'PLAN.json').exists(), 'No sobrescribir plan'
    RUN.mkdir(parents=True,exist_ok=True)
    plan={'id':'F3C-CADENA-PROTEGIDA-20261027','utc':now(),'author':'Codex',
      'authorization':'Corrige primero la protección de toda la cadena de validación y vuelve a evaluar F3c frente a la versión sin factores. Guarda los resultados y deja claro qué conclusiones cambian y qué pendientes siguen abiertos.',
      'class':'Reevaluación exploratoria expresamente solicitada; 2024 adaptativo, sin promoción o reapertura v1.',
      'hypothesis':'Al separar completitud, categorías, grupos y calibración de las etiquetas retenidas se puede medir de nuevo la ganancia residual del bloque propio.',
      'primary':'Mismo contraste primario de la revisión anterior: tronco T2b desarrollado<=2023, factores emergentes2023, T0 observado2024. Nueva implementación protegida, no el CSV de producción aprendido con ambos años.',
      'candidates':['sin_factores','F3c_reaprendido','constante'],
      'pipeline':{'raw':'Originales inalterados; reglas puntuales heredadas de exposición/capital/ID/duplicados, y asignación por ramo, póliza, ocurrencia.',
        'groups':'Componentes cliente-dirección entre ramos por mercado, calculados en las filas de entrenamiento del ámbito. Cinco folds por SHA de representante mínimo; mercados separados.',
        'source':'Esquema T2b y P_DEVB fijos; desarrollado2021-2023. Selección de rondas en fold0 de componentes, max5000/patience150, categorías, CDF y pesos aprendidos solo en inner-train; refit completo con rondas elegidas y transformaciones propias del train completo.',
        'completion':'CDF de coste madura1095d solo de siniestros aceptados asignados a filas fuente dentro del ámbito y edades>=1095; participaciones por peligro/coste y completitud solo del mercado y train de cada ámbito. V2024 fijo, sin afirmar snapshot2023.',
        'target':'Cinco predicciones OOF de nivel en2023 con completitud train sin fold; tronco fuente independiente de todo y emergente. Factores F2 y propios aprendidos con predicciones OOF2023; niveles finales solo2023.',
        'categories':'Solo source-inner-train/source-full-train. Desconocidas=NaN. No unión con destino/test.',
        'normalizers':'Toda normalización de factores/forma y nivel aprendida en2023 y congelada para aplicar fila a fila. No renormalizar con cartera retenida.',
        'shape':'Forma F2 autos renovación0.9 heredada fija. Sin exponentes/overlay públicos ni A_M1 de fuga/sigma; factor propio aprendido sobre esa base. No es el mismo estimando que la vista histórica con constantes públicas.',
        'factors':'F2 NCB y previos en secuencia, credibilidad n/(n+300). Propios género autos/contenidos, teletrabajo/marketing contenidos, Tweedie n/(n+300), sin buscar subconjuntos/K.',
        'timing':'Historia anterior al inicio, clima<=2023; maestros sin snapshots y cotización individual permanecen pendientes. No weather2024/2025 ni datos/CSV2025 en aprendizaje.'},
      'adversarial':['Poison costes2024 de ambos mercados antes de construir objetivos/completitud; 6 ajustes fuente completos nuevos baseline y6 replay poison con entradas/modelos/precios exactamente iguales.','Poison etiquetas del fold0 emergente2023: completitud, factores y precios del fold0 iguales; control positivo costes del train cambian nivel.','Poison categorías/clima futuros: diccionarios/matrices de train invariantes; inversión del orden de aplicación no cambia primas por fila; y retenida no se pasa al ajuste.','Flujo sintético con LightGBM real y controles de curvas/normalización/agrupación/métrica antes de ajustar datos reales.'],
      'cost':{'source_native_fits_expected':12,'new_2025_inference':0,'submissions':0,'remote':0,'model_family_search':0},
      'statistics':{'metric':'D2 Tweedie1.5 completo/no ponderado/T0', 'delta_min':0.0005,'segments':['motor','buildings','contents','new_business','renewal'],'segment_floor':-0.001,'motor_NB_stability_floor':-0.001,'bootstrap':10000,'seed':2026102301,'family':6,'quantiles':[0.05/12,1-0.05/12],'cluster':'componentes cliente-dirección hold2024','NB_lower95_floor':-0.001,'influence_remove':'max(5,ceil(.001*G))','future_mix':'Diagnóstico con composición por ramo/negocio/bandas exposición2025, sin optimización ni equivalencia futura.'},
      'consequences':'Informar todos los resultados aunque adversos; cero rescate de hiperparámetros, factores o semillas tras evaluar. Integridad técnica no acredita revisión profesional, suficiencia o ganancia privada. No modificar selección/F3c/PDF/guion.',
      'scope_limits':['Receta y esquema elegidos históricamente; el nuevo plan no deshace adaptación.','Se corrige la cadena del contraste primario T2b; A1/mezcla y producción2023+2024 no se convierten retrospectivamente en OOF.','Bootstrap condicional a precios; no replica todo aprendizaje ni búsqueda.','Valoración única2024, disponibilidad al cotizar, transporte de curvas y cola siguen abiertos.']}
    sources=[]
    for market in ['developed','emerging']:
        for name in ['claims','customers','addresses','weather']+['policies_'+l for l in LINES]:
            p=LEGACY/'datos'/market/(name+'.parquet')
            sources.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'role':'original'})
    for p in [Path(__file__),REPO/'registro/semana2_politica_seleccion_v1.json',REPO/'herramientas/seleccionar_semana2.py',REPO/'docs/validacion_cinco_prioridades/20261027T142339Z/P01.md',REPO/'docs/validacion_cinco_prioridades/20261027T142339Z/P03.md']:
        sources.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'role':'code_or_contract'})
    save(RUN/'fuentes.json',sources);save(RUN/'PLAN.json',plan)
    save(RUN/'freeze.json',{'utc':now(),'plan_sha256':sha(RUN/'PLAN.json'),'sources_sha256':sha(RUN/'fuentes.json'),'code_sha256':sha(__file__),'no_new_recipe2024_score_seen':True,'historical2024_seen':True,'formal_promotion_allowed':False})
    print(json.dumps({'frozen':str(RUN),'plan_sha256':sha(RUN/'PLAN.json')},ensure_ascii=False),flush=True)

def verify_inputs():
    f=read(RUN/'freeze.json');assert sha(__file__)==f['code_sha256'];assert sha(RUN/'PLAN.json')==f['plan_sha256'];assert sha(RUN/'fuentes.json')==f['sources_sha256']
    for s in read(RUN/'fuentes.json'):assert sha(s['path'])==s['sha256'],s['path']

def components(t):
    # Factorizar por cliente, después unir clientes que comparten cualquier dirección.
    ids=sorted(t.customer_id.astype(str).unique());ix={v:i for i,v in enumerate(ids)};parent=np.arange(len(ids))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    a=t[['address_id','customer_id']].drop_duplicates().sort_values(['address_id','customer_id'])
    last=None;first=None
    for addr,cust in a.itertuples(index=False,name=None):
        i=ix[str(cust)]
        if addr==last:
            u,v=find(first),find(i)
            if u!=v:parent[max(u,v)]=min(u,v)
        else:last=addr;first=i
    labels={v:ids[find(i)] for v,i in ix.items()}
    group=t.customer_id.astype(str).map(labels).to_numpy()
    foldmap={v:int(hashlib.sha256(('F3c_protected|'+v).encode()).hexdigest()[:16],16)%5 for v in set(group)}
    return group,np.array([foldmap[v] for v in group],np.int8)

def load_market(m,poison=False):
    d=LEGACY/'datos'/m
    c=pd.read_parquet(d/'claims.parquet')
    if m=='developed':
        cols=[x for x in c if x!='claim_id'];c=c[~(c.duplicated(cols,keep=False)&c.claim_id.str.len().eq(11))].copy()
    for x in ['loss_date','report_date']:c[x]=pd.to_datetime(c[x])
    if poison:c.loc[c.loss_date.dt.year.eq(2024),'incurred_to_date']*=2
    c['net']=c.incurred_to_date-c.recoveries;c['accepted']=c.status.ne('repudiated')
    cu=pd.read_parquet(d/'customers.parquet');ad=pd.read_parquet(d/'addresses.parquet')
    if m=='emerging':cu['occupation']=cu.occupation.str.lower().str.strip().str.replace('self-employed ','',regex=False).str.strip()
    weather=pd.read_parquet(d/'weather.parquet')
    if poison:weather.loc[weather.year.ge(2024),WEATHER]*=100
    weather=weather[weather.year.le(2023)].groupby('address_id')[WEATHER].mean().add_prefix('clima_')
    frames=[];assigned=[]
    for line in LINES:
        t=pd.read_parquet(d/f'policies_{line}.parquet');t['line']=line
        if m=='developed' and line=='motor':t['customer_id']=t.customer_id.str.zfill(8)
        t['period_start']=pd.to_datetime(t.period_start);t['period_end']=pd.to_datetime(t.period_end)
        t['year']=t.period_start.dt.year;t['exposure']=((t.period_end-t.period_start).dt.days+1)/365.
        if poison and m=='developed':t.loc[t.year.eq(2024),'channel']='FUTURE_ONLY_POISON'
        mm=c[c.line.eq(line)].merge(t[['row_id','policy_id','period_start','period_end']],on='policy_id')
        mm=mm[mm.loss_date.ge(mm.period_start)&mm.loss_date.le(mm.period_end)].copy()
        assert not mm.claim_id.duplicated().any()
        acc=mm[mm.accepted]
        t['y']=t.row_id.map(acc.groupby('row_id').net.sum()).fillna(0)
        for peril in sorted(c.loc[c.line.eq(line),'peril'].unique()):t['y_'+peril]=t.row_id.map(acc[acc.peril.eq(peril)].groupby('row_id').net.sum()).fillna(0)
        t=t.merge(cu,on='customer_id',validate='m:1').merge(ad,on='address_id',validate='m:1')
        assert len(t)==len(pd.read_parquet(d/f'policies_{line}.parquet',columns=['row_id']))
        t=t.merge(weather,on='address_id',how='left',validate='m:1')
        t['tenure_years']=t.year-t.customer_since_year;t['property_age']=t.year-t.year_built
        t['start_month']=t.period_start.dt.month;t['full_year']=t.exposure.ge(.99).astype(int);t['log_days_quote']=np.log1p(t.days_quote_to_inception.clip(lower=0))
        if m=='developed':
            age=t.driver_age if line=='motor' else t.policyholder_age
            t['age_band']=pd.cut(age,[-1,24,34,49,64,200],labels=['17-24','25-34','35-49','50-64','65+']).astype(str)
        else:t['age_band']=t.driver_age_band if line=='motor' else t.policyholder_age_band
        t['occupation']=t.occupation.str.lower().str.strip()
        if line!='motor':
            cap=5000000 if line=='buildings' else 2000000
            t['sum_insured']=np.where(t.sum_insured.gt(cap),t.sum_insured/1000,t.sum_insured);t['log_si']=np.log(t.sum_insured)
        else:t['ncb_years']=pd.to_numeric(t.ncb_years)
        if line=='buildings':t['construction']=t.construction_type.str.lower().map(CONSTR);assert t.construction.notna().all()
        if line!='motor':t['ncb_years']=np.nan
        frames.append(t);assigned.append(mm)
    base=pd.concat(frames,ignore_index=True);assert base.row_id.is_unique
    asg=pd.concat(assigned,ignore_index=True)
    # Historia conocida al inicio; no usa importes ni estados y queda limitada por ocurrencia/reporte.
    mapping=base[['policy_id','line','customer_id']].drop_duplicates()
    assert not mapping.duplicated(['policy_id','line']).any()
    hc=c.merge(mapping,on=['policy_id','line'],how='inner')
    for kind,key in [('pol','policy_id'),('cli','customer_id')]:
        groupkeys=[key,'line'] if kind=='pol' else [key]
        queries=base[['row_id','period_start']+groupkeys]
        reports=(c if kind=='pol' else hc)[groupkeys+['report_date','loss_date']]
        merged=queries.merge(reports,on=groupkeys)
        merged=merged[merged.report_date.lt(merged.period_start)&merged.report_date.ge(merged.period_start-pd.Timedelta(days=365))&merged.loss_date.lt(merged.period_start)]
        n=base.row_id.map(merged.groupby('row_id').size()).fillna(0)
        start=pd.Timestamp('2021-01-01' if m=='developed' else '2023-01-01')
        base['hist_'+kind+'_12m']=n.where(base.period_start-pd.Timedelta(days=365)>=start,np.nan)
    return base,asg

def curves(asg,rows):
    a=asg[asg.row_id.isin(set(rows.row_id))&asg.accepted].copy()
    mature=(pd.Timestamp(V)-a.loss_date).dt.days.ge(1095);a=a[mature]
    out={}
    for (line,p),g in a.groupby(['line','peril']):
        delay=(g.report_date-g.loss_date).dt.days.to_numpy();w=g.net.to_numpy(float)
        ok=(delay>=0)&(delay<=1095);assert w[ok].sum()>0 and (w[ok]>=0).all()
        out[(line,p)]=np.clip(np.bincount(delay[ok],weights=w[ok],minlength=1096).cumsum()/w[ok].sum(),0,1)
    return out

def completion(train, apply, line, F):
    cs={};train_cs={}
    perils=sorted(p for ll,p in F if ll==line)
    assert perils
    def integrate(t,f):
        ff=np.r_[f,np.ones(5000-len(f))];G=np.r_[0,np.cumsum(ff)]
        s=t.period_start.to_numpy('datetime64[D]');e=t.period_end.to_numpy('datetime64[D]')
        a=(V-e).astype(int).clip(0);b=(V-s).astype(int).clip(0)
        return (G[b+1]-G[a])/(b-a+1)
    for p in perils:train_cs[p]=integrate(train,F[(line,p)]);cs[p]=integrate(apply,F[(line,p)])
    ult={p:train['y_'+p].sum()/max(np.average(train_cs[p],weights=train.exposure),1e-6) for p in perils}
    assert sum(ult.values())>0
    weights={p:u/sum(ult.values()) for p,u in ult.items()}
    qtr=sum(weights[p]*train_cs[p] for p in perils);qap=sum(weights[p]*cs[p] for p in perils)
    assert (qtr>0).all() and (qap>0).all()
    return qtr,qap,weights

def categories(t,cols):return {c:sorted(t[c].dropna().astype(str).unique().tolist()) for c in cols if c in CATS}
def matrix(t,cols,cat):
    x=pd.DataFrame(index=np.arange(len(t)))
    for c in cols:
        if c in CATS:x[c]=pd.Categorical(t[c].astype(str).where(t[c].notna(),None).to_numpy(),categories=cat[c])
        else:x[c]=pd.to_numeric(t[c],errors='coerce').to_numpy(float)
    return x

def fit_source(src,asg,em,line,tag):
    out=RUN/'models'/tag;out.mkdir(parents=True,exist_ok=True)
    dv=src[src.line.eq(line)].reset_index(drop=True);et=em[em.line.eq(line)].reset_index(drop=True)
    tr=dv[dv.fold.ne(0)].reset_index(drop=True);va=dv[dv.fold.eq(0)].reset_index(drop=True)
    # Curvas maduras usan todos los ramos permitidos, pero excluyen todos los componentes internos retenidos.
    source_inner=src[src.fold.ne(0)]
    Finner=curves(asg,source_inner);Ffull=curves(asg,src)
    qi,qv,wi=completion(tr,va,line,Finner);qf,_,wf=completion(dv,et,line,Ffull)
    cols=POLIZA+CLIENTE+DIRECCION+RAMO[line]
    ci=categories(tr,cols);cf=categories(dv,cols)
    Xi=matrix(tr,cols,ci);Xv=matrix(va,cols,ci);Xf=matrix(dv,cols,cf)
    yi=tr.y.to_numpy(float);yv=va.y.to_numpy(float);yf=dv.y.to_numpy(float)
    oi=np.log(tr.exposure.to_numpy()*qi);ov=np.log(va.exposure.to_numpy()*qv);of=np.log(dv.exposure.to_numpy()*qf)
    p=dict(objective='tweedie',tweedie_variance_power=1.5,learning_rate=.03,num_leaves=63,min_data_in_leaf={'motor':300,'buildings':3000,'contents':3000}[line],feature_fraction=.8,bagging_fraction=.8,bagging_freq=1,lambda_l2=10. if line=='contents' else 0.,max_cat_to_onehot=8,cat_smooth=50,verbosity=-1,num_threads=2,seed=20261024,deterministic=True,force_col_wise=True)
    argument_hash=digest(Xi,yi,oi,Xv,yv,ov,Xf,yf,of,p,ci,cf,wi,wf,{str(k):v for k,v in Finner.items()},{str(k):v for k,v in Ffull.items()})
    record={'utc':now(),'line':line,'tag':tag,'argument_sha256':argument_hash,'source_train_rows':len(dv),'inner_train_rows':len(tr),'inner_valid_rows':len(va),'params':p,'inner_weights':wi,'full_weights':wf,'inner_categories':ci,'full_categories':cf,'stage':'started'}
    save(out/f'{line}_receipt.json',record)
    print(json.dumps({'event':'source_fit_start','line':line,'tag':tag,'rows':len(dv)},ensure_ascii=False),flush=True)
    for stage in ['inner','full']:
        with (RUN/'fit_attempts.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps({'utc':now(),'line':line,'tag':tag,'stage':stage})+'\n')
        if stage=='inner':
            b=lgb.train(p,lgb.Dataset(Xi,label=yi,init_score=oi),5000,valid_sets=[lgb.Dataset(Xv,label=yv,init_score=ov,reference=None)],callbacks=[lgb.early_stopping(150,verbose=False)])
            rounds=max(1,b.best_iteration)
        else:b=lgb.train(p,lgb.Dataset(Xf,label=yf,init_score=of),rounds)
    model=out/f'{line}.txt';b.save_model(str(model))
    raw=b.predict(matrix(et,cols,cf),raw_score=True,num_threads=2)
    pred=pd.DataFrame({'row_id':et.row_id,'raw':raw});pred.to_parquet(out/f'{line}_raw.parquet',index=False)
    record.update(stage='complete',rounds=rounds,model_sha256=sha(model),raw_sha256=digest(raw),completed_utc=now())
    save(out/f'{line}_receipt.json',record)
    print(json.dumps({'event':'source_fit_done','line':line,'tag':tag,'rounds':rounds},ensure_ascii=False),flush=True)
    return pred,record,Ffull

def factor_train(t,m,kind,key,lines=None):
    c=cells(t);f={};y=t.y.to_numpy(float)
    if kind=='ae':
        for cc in np.unique(c):
            i=c==cc;base=y[i].sum()/m[i].sum()
            for v in np.unique(key[i]):
                j=i&(key==v);n=(y[j]>0).sum();f[(cc,str(v))]=1+n/(n+300)*(y[j].sum()/m[j].sum()/base-1)
    else:
        ref=m.copy()
        for cc in np.unique(c):i=c==cc;ref[i]*=kopt(y[i],ref[i])
        for line in lines:
            for v in np.unique(key[t.line.eq(line).to_numpy()]):
                j=t.line.eq(line).to_numpy()&(key==v);n=(y[j]>0).sum()
                if n:f[(line,str(v))]=math.exp(n/(n+300)*math.log(max(kopt(y[j],ref[j]),1e-3)))
    unit=c if kind=='ae' else t.line.to_numpy()
    mult=np.array([f.get((a,str(v)),1.) for a,v in zip(unit,key)])
    normal={cc:float(m[c==cc].sum()/(m[c==cc]*mult[c==cc]).sum()) for cc in np.unique(c)}
    return {'kind':kind,'factors':[[a,v,x] for (a,v),x in sorted(f.items())],'normal':normal}
def factor_apply(t,m,key,p):
    f={(a,v):x for a,v,x in p['factors']};c=cells(t);u=c if p['kind']=='ae' else t.line.to_numpy()
    return m*np.array([f.get((a,str(v)),1.)*p['normal'].get(cc,1.) for a,v,cc in zip(u,key,c)])
def shape_train(t,m):
    c=cells(t);j=c=='motor_0';e=t.exposure.to_numpy()*t.q.to_numpy();gm=m[j].sum()/e[j].sum()
    transformed=e[j]*gm*(m[j]/e[j]/gm)**.9
    return {'cell':'motor_0','power':.9,'gm':float(gm),'norm':float(m[j].sum()/transformed.sum())}
def shape_apply(t,m,p):
    j=cells(t)==p['cell'];out=m.copy();e=t.exposure.to_numpy()*t.q.to_numpy()
    out[j]=e[j]*p['gm']*(m[j]/e[j]/p['gm'])**p['power']*p['norm'];return out
def recipe(tr,te):
    mtr=tr.base.to_numpy().copy();mte=te.base.to_numpy().copy();params={'F2':[],'own':[],'levels':{}}
    for v in ['ncb','prior']:
        f=factor_train(tr,mtr,'ae',ks(tr,v));params['F2'].append({'variable':v,**f})
        mtr=factor_apply(tr,mtr,ks(tr,v),f);mte=factor_apply(te,mte,ks(te,v),f)
    form=shape_train(tr,mtr);params['shape']=form;mtr=shape_apply(tr,mtr,form);mte=shape_apply(te,mte,form)
    owntr=mtr.copy();ownte=mte.copy()
    for v,lines in SEQ:
        f=factor_train(tr,owntr,'tw',ks(tr,v),lines);params['own'].append({'variable':v,**f})
        owntr=factor_apply(tr,owntr,ks(tr,v),f);ownte=factor_apply(te,ownte,ks(te,v),f)
    out={};c=cells(tr);ce=cells(te);y=tr.y.to_numpy()
    for name,mt,me in [('sin_factores',mtr,mte),('F3c_reaprendido',owntr,ownte)]:
        levels={cc:kopt(y[c==cc],mt[c==cc]) for cc in np.unique(c)}
        params['levels'][name]=levels;out[name]=me*np.array([levels[cc] for cc in ce])
    rates={cc:kopt(y[c==cc],(tr.exposure*tr.q).to_numpy()[c==cc]) for cc in np.unique(c)}
    params['constant_rates']=rates;out['constante']=(te.exposure*te.q).to_numpy()*np.array([rates[cc] for cc in ce])
    return out,params

def target_base(em,raw,F,train_mask,eval_mask):
    tr=em.loc[train_mask].copy().reset_index(drop=True);ev=em.loc[eval_mask].copy().reset_index(drop=True)
    tr['raw']=tr.row_id.map(raw);ev['raw']=ev.row_id.map(raw);assert tr.raw.notna().all() and ev.raw.notna().all()
    tr['q']=0.;ev['q']=0.;tr['base']=0.;ev['base']=0.;pars={}
    for line in LINES:
        i=tr.line.eq(line);j=ev.line.eq(line)
        qt,qe,w=completion(tr[i],ev[j],line,F);tr.loc[i,'q']=qt;ev.loc[j,'q']=qe
        level=kopt(tr.loc[i,'y'].to_numpy(),np.exp(tr.loc[i,'raw'].to_numpy())*tr.loc[i,'exposure'].to_numpy()*qt)
        tr.loc[i,'base']=level*np.exp(tr.loc[i,'raw'])*tr.loc[i,'exposure']*qt
        ev.loc[j,'base']=level*np.exp(ev.loc[j,'raw'])*ev.loc[j,'exposure']*qe
        pars[line]={'level':level,'weights':w}
    return tr,ev,pars

def preflight():
    verify_inputs();checks={}
    t=pd.DataFrame({'customer_id':['a','b','c','a'],'address_id':['x','x','y','z']});g,f=components(t);checks['connected_address_customer']=g[0]==g[1]==g[3] and f[0]==f[1]==f[3] and g[2]!=g[0]
    xx=pd.DataFrame({'channel':['train','train']});ca=categories(xx,['channel']);future=pd.DataFrame({'channel':['new']});checks['unknown_is_missing']=matrix(future,['channel'],ca).channel.isna().all()
    y=np.array([0.,1.,6.]);m=np.array([.2,2.,5.]);from sklearn.metrics import mean_tweedie_deviance
    checks['metric_matches_sklearn']=abs(dev(y,m).mean()-mean_tweedie_deviance(y,m,power=1.5))<1e-12
    # Prueba con el estimador real, determinista, sin y retenida en sus argumentos.
    rng=np.random.default_rng(17);X=pd.DataFrame({'x':rng.normal(size=90)});ys=np.exp(X.x.to_numpy())
    params=dict(objective='tweedie',tweedie_variance_power=1.5,num_leaves=3,min_data_in_leaf=5,verbosity=-1,num_threads=2,deterministic=True,force_col_wise=True,seed=17)
    models=[]
    for held in [np.ones(30),np.ones(30)*999]:
        model=lgb.train(params,lgb.Dataset(X.iloc[:60],label=ys[:60]),8);models.append(model.model_to_string())
    checks['real_lgbm_synthetic_held_y_invariant']=models[0]==models[1]
    checks['all_passed']=all(bool(x) for x in checks.values());save(RUN/'preflight.json',{'utc':now(),'checks':checks,'synthetic_native_fits':2});assert checks['all_passed']
    print(json.dumps(clean(checks)),flush=True)

def train():
    verify_inputs();assert read(RUN/'preflight.json')['checks']['all_passed'];assert not (RUN/'training_complete.json').exists()
    start=time.time();receipts={};raws={};Fs={};raw_checks={}
    for tag,poison in [('baseline',False),('poison2024',True)]:
        src,asg=load_market('developed',poison);em,ema=load_market('emerging',poison)
        raw_checks[tag]={m:{'rows':int(b.year.eq(2024).sum()),'positive_rows':int((b.year.eq(2024)&b.y.gt(0)).sum()),'target_hash':digest(b.loc[b.year.eq(2024),'y'].to_numpy(float))} for m,b in [('developed',src),('emerging',em)]}
        src=src[src.year.le(2023)].reset_index(drop=True);src['group'],src['fold']=components(src)
        e23=em[em.year.eq(2023)].copy();e23['group'],e23['fold']=components(e23)
        em['group']=em.row_id.map(e23.set_index('row_id').group);em['fold']=em.row_id.map(e23.set_index('row_id').fold)
        predictions=[];receipts[tag]={}
        for line in LINES:
            pred,rec,F=fit_source(src,asg,em,line,tag);predictions.append(pred);receipts[tag][line]=rec
            if line==LINES[0]:Fs[tag]=F
        raw=pd.concat(predictions).set_index('row_id').raw;raws[tag]=raw
        # OOF de nivel y exposición protegida de cada fold emergente.
        oof=[];scope=[]
        for fold in range(5):
            a,b,p=target_base(em,raw,Fs[tag],em.year.eq(2023)&em.fold.ne(fold),em.year.eq(2023)&em.fold.eq(fold))
            oof.append(b);scope.append({'fold':fold,'params':p,'train_rows':len(a),'eval_rows':len(b),'groups_disjoint':not bool(set(a.group)&set(b.group))})
        tr=pd.concat(oof).sort_values('row_id').reset_index(drop=True)
        # El coste2024 no llega a recipe: se quita explícitamente antes de aplicar.
        a,te,p=target_base(em,raw,Fs[tag],em.year.eq(2023),em.year.eq(2024));te['y']=np.nan
        pred,params=recipe(tr,te)
        save(RUN/f'{tag}_parameters.json',{'target_folds':scope,'temporal_base':p,'recipe':params,'source_curves':{str(k):v for k,v in Fs[tag].items()}})
        output=te[['row_id','line','customer_id','address_id','new_business','exposure','q','base']].copy()
        for name,values in pred.items():output[name]=values
        output.to_parquet(RUN/f'{tag}_predictions.parquet',index=False)
        if tag=='baseline':
            tr.to_parquet(RUN/'training2023.parquet',index=False)
            em[em.year.eq(2024)][['row_id','y']+[c for c in em if c.startswith('y_')]].to_parquet(RUN/'target2024_sealed.parquet',index=False)
            # Control de aislamiento del fold0 con todos los costes/peril retenidos alterados.
            poisoned=em.copy();mask=poisoned.year.eq(2023)&poisoned.fold.eq(0)
            for col in ['y']+[c for c in em if c.startswith('y_')]:poisoned.loc[mask,col]*=2
            a0,b0,p0=target_base(em,raw,Fs[tag],em.year.eq(2023)&em.fold.ne(0),mask)
            a1,b1,p1=target_base(poisoned,raw,Fs[tag],poisoned.year.eq(2023)&poisoned.fold.ne(0),mask)
            b0['y']=np.nan;b1['y']=np.nan
            r0,z0=recipe(a0,b0);r1,z1=recipe(a1,b1)
            cp=a0.copy();cp['y']*=2;_,zplus=recipe(cp,b0)
            rev,zrev=recipe(tr,te.iloc[::-1].reset_index(drop=True))
            save(RUN/'target_fold_adversarial.json',{'utc':now(),'poisoned_rows':int(mask.sum()),'completion_params_equal':p0==p1,'recipe_params_equal':z0==z1,'prices_exact':all(np.array_equal(r0[k],r1[k]) for k in r0),'positive_control_params_change':zplus!=z0,'row_order_invariant':all(np.array_equal(pred[k],rev[k][::-1]) for k in pred),'parameters_do_not_depend_on_eval_order':params==zrev,'source_address_fold_isolated':bool(src.groupby('address_id').fold.nunique().le(1).all()),'target_address_fold_isolated':bool(e23.groupby('address_id').fold.nunique().le(1).all()),'warning':'El control de fold0 usa base train directa para el fold; el aprendizaje final usa OOF2023 y excluye2024 íntegro.'})
        print(json.dumps({'event':'target_predictions_saved','tag':tag,'rows':len(output)},ensure_ascii=False),flush=True)
        del src,asg,em,ema
    checks={}
    for line in LINES:
        for field in ['argument_sha256','model_sha256','raw_sha256','rounds']:checks[line+'_'+field]=receipts['baseline'][line][field]==receipts['poison2024'][line][field]
    checks['target_parameters_exact']=read(RUN/'baseline_parameters.json')==read(RUN/'poison2024_parameters.json')
    for market in ['developed','emerging']:checks[market+'_poison_is_nonvacuous']=raw_checks['baseline'][market]['target_hash']!=raw_checks['poison2024'][market]['target_hash'] and raw_checks['baseline'][market]['positive_rows']>0
    b=pd.read_parquet(RUN/'baseline_predictions.parquet');p=pd.read_parquet(RUN/'poison2024_predictions.parquet');checks['all_hold_predictions_exact']=b.equals(p)
    for key,val in read(RUN/'target_fold_adversarial.json').items():
        if isinstance(val,bool):checks['fold_'+key]=val
    assert all(checks.values()),checks
    save(RUN/'training_complete.json',{'utc':now(),'seconds':time.time()-start,'checks':checks,'raw_poison_controls':raw_checks,'source_native_fit_attempts':len((RUN/'fit_attempts.jsonl').read_text().splitlines()),'synthetic_native_fits':2,'source_receipts':receipts,'all_passed':True,'selection_changed':False,'new_2025_predictions':0})
    print(json.dumps({'event':'training_complete','checks':checks,'seconds':time.time()-start}),flush=True)

def open_evaluation():
    verify_inputs();assert read(RUN/'training_complete.json')['all_passed'];assert not (RUN/'opened.json').exists()
    # La política v1 bloquea promoción por disponibilidad/confirmación. La nueva
    # instrucción autoriza esta reevaluación exploratoria, sin borrar ese bloqueo.
    save(RUN/'opened.json',{'utc':now(),'plan_sha256':sha(RUN/'PLAN.json'),'training_receipt_sha256':sha(RUN/'training_complete.json'),'predictions_sha256':sha(RUN/'baseline_predictions.parquet'),'target_sha256':sha(RUN/'target2024_sealed.parquet'),'historical2024_already_seen':True,'first_scores_of_this_recipe_not_yet_computed':True,'formal_v1_reopened':False,'promotion_allowed':False,'authorization':read(RUN/'PLAN.json')['authorization']})
    print(json.dumps({'opened_exploratory':True,'promotion_allowed':False}),flush=True)

def summarize(y,preds,mask=None,weights=None):
    mask=np.ones(len(y),bool) if mask is None else mask
    yy=y[mask];w=np.ones(len(yy)) if weights is None else weights[mask];null=np.sum(w*dev(yy,np.full(len(yy),np.average(yy,weights=w))))
    scores={k:float(1-np.sum(w*dev(yy,v[mask]))/null) for k,v in preds.items()}
    return {'rows':int(mask.sum()),'D2':scores,'delta':scores['F3c_reaprendido']-scores['sin_factores'],'null_deviance':float(null)}

def evaluate():
    verify_inputs();op=read(RUN/'opened.json');assert sha(RUN/'baseline_predictions.parquet')==op['predictions_sha256']
    t=pd.read_parquet(RUN/'baseline_predictions.parquet').merge(pd.read_parquet(RUN/'target2024_sealed.parquet'),on='row_id',validate='1:1')
    y=t.y.to_numpy(float);preds={k:t[k].to_numpy() for k in ['sin_factores','F3c_reaprendido','constante']};g,_=components(t);t['group']=g
    seg={'global':np.ones(len(t),bool),'new_business':t.new_business.to_numpy(bool),'renewal':~t.new_business.to_numpy(bool)}
    for line in LINES:
        seg[line]=t.line.eq(line).to_numpy()
        for nb in [0,1]:seg[line+'_'+str(nb)]=seg[line]&(t.new_business.to_numpy(int)==nb)
    results={'utc':now(),'class':'exploratory_protected_refit_conditional','metrics':{s:summarize(y,preds,m) for s,m in seg.items()},'intervals':{}}
    # Covariables futuras se leen solo para el diagnóstico de composición, sin
    # intervenir en ninguno de los ajustes ni sus normalizadores.
    def mixkey(line,nb,exposure):return np.array([str(a)+'|'+str(int(b))+'|'+str(c) for a,b,c in zip(line,nb,np.where(exposure<.5,'c',np.where(exposure<.9,'m','l')))])
    keys24=mixkey(t.line,t.new_business,t.exposure.to_numpy());future=[]
    for line in LINES:
        q=pd.read_parquet(LEGACY/'datos/emerging'/f'test_{line}.parquet',columns=['new_business','period_start','period_end'])
        ee=((pd.to_datetime(q.period_end)-pd.to_datetime(q.period_start)).dt.days+1).to_numpy()/365.
        future.extend(mixkey(np.repeat(line,len(q)),q.new_business,ee))
    old=pd.Series(keys24).value_counts();new=pd.Series(future).value_counts()
    missing=set(new.index)-set(old.index);assert not missing,missing
    weights=np.array([new.get(k,0)/old[k] for k in keys24]);weights*=len(weights)/weights.sum()
    for s,mask in [('mix2025_global',seg['global']),('mix2025_new_business',seg['new_business'])]:
        seg[s]=mask;results['metrics'][s]=summarize(y,preds,mask,weights)
    results['mix2025']={'test_rows':len(future),'training_uses_future_rows':False,'cell_exposure_band_weights':{k:float(new.get(k,0)/old[k]) for k in old.index},'limit':'Reponderación descriptiva, sin equivalencia futura.'}
    # Agrupar suficientes estadísticos Tweedie; mismo sorteo para todos los modelos/segmentos.
    groups,ix=np.unique(g,return_inverse=True);G=len(groups);names=list(preds);segments=['global','new_business','renewal']+LINES+['mix2025_global','mix2025_new_business']
    arrays=[]
    for s in segments:
        m=seg[s]*(weights if s.startswith('mix2025_') else 1.);a=[np.bincount(ix,weights=m,minlength=G),np.bincount(ix,weights=y*m,minlength=G),np.bincount(ix,weights=np.sqrt(y)*m,minlength=G)]
        a +=[np.bincount(ix,weights=dev(y,preds[k])*m,minlength=G) for k in names];arrays.append(np.stack(a,axis=1))
    stats=np.stack(arrays,axis=1);flat=stats.reshape(G,-1);rng=np.random.default_rng(2026102301);draws=np.empty((10000,len(segments),len(names)))
    for start in range(0,10000,25):
        n=min(25,10000-start);counts=np.stack([np.bincount(rng.integers(0,G,size=G),minlength=G) for _ in range(n)])
        z=(counts@flat).reshape(n,len(segments),3+len(names));null=8*(np.sqrt(z[:,:,0]*z[:,:,1])-z[:,:,2]);draws[start:start+n]=1-z[:,:,3:]/null[:,:,None]
    np.savez_compressed(RUN/'bootstrap.npz',scores=draws,segments=segments,models=names)
    for j,s in enumerate(segments):
        d=draws[:,j,names.index('F3c_reaprendido')]-draws[:,j,names.index('sin_factores')]
        results['intervals'][s]={'CI95':np.quantile(d,[.025,.975]).tolist(),'family6':np.quantile(d,[.05/12,1-.05/12]).tolist()}
    contribution=np.bincount(ix,weights=dev(y,preds['sin_factores'])-dev(y,preds['F3c_reaprendido']),minlength=G)
    order=np.argsort(-contribution,kind='stable');nremove=max(5,math.ceil(.001*G));keep=~np.isin(ix,order[:nremove]);cum=np.cumsum(contribution[order]);total=contribution.sum();cross=np.flatnonzero(cum>=total)
    results['influence']={'groups':G,'removed':nremove,'delta_without_top':summarize(y,preds,keep)['delta'],'groups_to_erase':int(cross[0]+1) if len(cross) else None,'top_removed_sum_share':float(contribution[order[:nremove]].sum()/total) if total!=0 else None}
    results['guard_status']={'global_lower_above_margin':results['intervals']['global']['family6'][0]>.0005,'broad_segments_floor':all(results['metrics'][s]['delta']>=-.001 for s in ['motor','buildings','contents','new_business','renewal']),'new_business_protection':results['metrics']['new_business']['delta']>=0 and results['intervals']['new_business']['CI95'][0]>=-.001,'motor_NB_stability_floor':results['metrics']['motor_1']['delta']>=-.001,'influence':results['influence']['delta_without_top']>=0,'all_historical_guards_accredited':False,'formal_promotion':False}
    results['bootstrap']={'replicates':10000,'seed':2026102301,'family':6,'same_draws':True,'scope':'Condicional a precios reentrenados. No aprendizaje completo ni adaptación histórica.'}
    save(RUN/'resultados.json',results);print(json.dumps(clean(results),ensure_ascii=False,indent=2),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['freeze','preflight','train','open','evaluate','verify']);a=p.parse_args()
    if a.stage=='freeze':freeze()
    elif a.stage=='preflight':preflight()
    elif a.stage=='train':train()
    elif a.stage=='open':open_evaluation()
    elif a.stage=='evaluate':evaluate()
    else:
        verify_inputs();print(json.dumps({'inputs_verified':True,'plan_sha256':sha(RUN/'PLAN.json')}))

if __name__=='__main__':main()
