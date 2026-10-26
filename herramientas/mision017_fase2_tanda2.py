"""Credibilidad estándar sobre padre F2, con C0 y calibración excluyendo componentes."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from semana2 import variables_ultimo as v
from semana2.fase2_2024_datos import sha,dump,BASE
OUT=R/'privado/semana2/mision017_fase2/tanda2_20261025_v1'
PARENT=R/'privado/semana2/mision017_fase2/linaje_T2b_v1'
PLAN=R/'registro/semana2_mision017_fase2_tanda2_plan_v1.json'
rel=lambda p:p.relative_to(ROOT).as_posix()
now=lambda:datetime.now(timezone.utc).isoformat()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))


def factor(y,m):return float(np.sum(y/np.sqrt(m))/np.sum(np.sqrt(m)))
def unit(y,m):return 4*y/np.sqrt(m)+4*np.sqrt(m)-8*np.sqrt(y)


def digest(a):return hashlib.sha256(json.dumps(a,sort_keys=True,separators=(',',':'),default=float).encode()).hexdigest()


def reporting_scope(periods,claims,held):
    assert periods.row_id.is_unique and periods.year.isin([2023,2024]).all()
    trainmask=periods.fold.ne(held).to_numpy();keys=set(periods.loc[trainmask,'row_id'])
    selected=claims.loc[claims.row_id.isin(keys)].copy()
    # Selection precedes interpretation of protected dates, perils, amounts or outcomes.
    selected=selected.loc[selected.included_in_T0].copy()
    assert selected.year.isin([2023,2024]).all()
    curves={};levels={};qc={};frequency={}
    for peril,g in selected.groupby('peril'):
        loss=pd.to_datetime(g.loss_date);report=pd.to_datetime(g.report_date)
        model,_=v.fit_reporting((report-loss).dt.days,(pd.Timestamp('2024-12-31')-loss).dt.days,
                               g.T0_cents.to_numpy(float)/100,g.reserve_cents.to_numpy(float)/100)
        qn=v.average_completion(periods,model);qc[peril]=v.average_completion(periods,model,'cost',1.)
        freq=len(g)/np.sum(periods.exposure.to_numpy(float)[trainmask]*qn[trainmask])
        curves[peril]=model;frequency[peril]=float(freq);levels[peril]=freq*model['mean_net_mark']['1.0']
    assert len(curves)=={'motor':5,'buildings':6,'contents':4}[periods.line.iloc[0]]
    mix={p:float(x/sum(levels.values())) for p,x in levels.items()}
    q=sum(mix[p]*qc[p] for p in mix);assert np.isfinite(q).all() and (q>0).all() and (q<=1+1e-10).all()
    artifact={'curves':curves,'mixture':mix,'frequency':frequency,'fit_row_ids':sorted(keys),
              'fit_claim_ids':sorted(selected.claim_id.tolist()),'excluded_fold':int(held)}
    return periods.exposure.to_numpy(float)*q,artifact


def bands(f,which):
    if which=='ncb':
        x=pd.to_numeric(f.ncb_years,errors='coerce')
        return pd.cut(x,[-1,0,2,5,9,np.inf],labels=['0','1-2','3-5','6-9','10+']).astype('string').fillna('missing').to_numpy()
    return pd.to_numeric(f.prior_claims_5y).clip(upper=2).fillna(-1).astype(int).astype(str).to_numpy()


def shape_fit(f,m,which):
    labels=bands(f,which);new=f.new_business.to_numpy(dtype=int);y=f.T0.to_numpy(float)
    factors={};normalizers={};out=m.copy()
    for business in [0,1]:
        cell=new==business
        base=y[cell].sum()/m[cell].sum()
        assert base>0
        for label in sorted(set(labels[cell])):
            sel=cell&(labels==label);n=int(np.count_nonzero(y[sel]>0));z=n/(n+300)
            ae=(y[sel].sum()/m[sel].sum())/base
            factors[f'{business}|{label}']=float(1+z*(ae-1))
        g=np.array([factors[f'{business}|{x}'] for x in labels[cell]])
        norm=float(np.sum(m[cell]*g)/np.sum(m[cell]));normalizers[str(business)]=norm
        out[cell]*=g/norm
    return {'which':which,'factors':factors,'normalizers':normalizers},out


def shape_apply(f,m,artifact):
    labels=bands(f,artifact['which']);new=f.new_business.to_numpy(dtype=int)
    return m*np.array([artifact['factors'].get(f'{n}|{x}',1.)/artifact['normalizers'][str(n)] for n,x in zip(new,labels)])


def cell_levels(f,m,line_level):
    y=f.T0.to_numpy(float);new=f.new_business.to_numpy(dtype=int);out={}
    for nb in [0,1]:
        sel=new==nb;n=int(np.count_nonzero(y[sel]>0));z=n/(n+400)
        own=factor(y[sel],m[sel]);assert own>0
        out[str(nb)]=float(line_level*np.exp(z*np.log(own/line_level)))
    return out


def learn_predict(periods,claims,held):
    e,c0=reporting_scope(periods,claims,held)
    mask=periods.fold.ne(held).to_numpy();fit=periods.loc[mask].copy();valid=periods.loc[~mask].copy()
    y=fit.T0.to_numpy(float);m=periods.annual_raw_T2b.to_numpy(float)*e
    k=factor(y,m[mask]);k00=factor(y,e[mask]);ks={};a=[]
    mfit=m[mask].copy();mvalid=m[~mask].copy()
    for which in (['ncb','prior'] if periods.line.iloc[0]=='motor' else ['prior']):
        artifact,mfit=shape_fit(fit,mfit,which);mvalid=shape_apply(valid,mvalid,artifact);a.append(artifact)
    kshape=factor(y,mfit);cell=cell_levels(fit,m[mask],k);cellshape=cell_levels(fit,mfit,kshape)
    nb=valid.new_business.to_numpy(dtype=int)
    pred=np.column_stack([e[~mask]*k00,m[~mask]*k,mvalid*kshape,
                          m[~mask]*np.array([cell[str(n)] for n in nb]),
                          mvalid*np.array([cellshape[str(n)] for n in nb])])
    assert np.isfinite(pred).all() and (pred>0).all()
    learn={'C0':c0,'shape':a,'k':k,'kshape':kshape,'B00':k00,'cell':cell,'cellshape':cellshape}
    return pred,learn,e[~mask]


def synthetic():
    # The full numerical learning path, including reporting and all calibrators.
    n=200;f=pd.DataFrame({'row_id':['s'+str(i) for i in range(n)],'year':2023,
        'line':'motor','fold':np.arange(n)%5,'period_start':pd.Timestamp('2023-01-01'),
        'period_end':pd.Timestamp('2023-12-31'),'is_test':False,'exposure':1.,
        'annual_raw_T2b':np.linspace(100,500,n),'new_business':np.arange(n)%2,
        'ncb_years':np.arange(n)%12,'prior_claims_5y':np.arange(n)%3,'T0':np.arange(n)+100.})
    c=pd.DataFrame({'row_id':f.row_id,'claim_id':['c'+str(i) for i in range(n)],'year':2023,
        'included_in_T0':True,'peril':np.array(['own_damage','theft','bodily_injury','third_party_prop','glass_hail'])[(np.arange(n)//5)%5],
        'loss_date':pd.Timestamp('2023-02-01'),'report_date':pd.Timestamp('2023-03-01'),
        'T0_cents':f.T0*100,'reserve_cents':0.})
    p,a,e=learn_predict(f,c,0)
    bad=f.copy();bad.loc[bad.fold.eq(0),'T0']=1e30
    badc=c.copy();mask=badc.row_id.isin(f.loc[f.fold.eq(0),'row_id'])
    badc.loc[mask,['T0_cents','reserve_cents']]=-1e30
    badc.loc[mask,'peril']='protected_invalid'
    q,b,_=learn_predict(bad,badc,0)
    assert digest(a)==digest(b) and np.array_equal(p,q)
    changed=f.copy();changed.loc[changed.fold.ne(0),'T0']*=2
    _,other,_=learn_predict(changed,c,0);assert digest(a)!=digest(other)
    dump(OUT/'synthetic.json',{'pass':True,'full_learning_held_payload_invariant':True,
         'training_payload_changes_learning':True,'real_fits':0,'synthetic_reporting_curves':15})


def register():
    assert not OUT.exists() and not PLAN.exists();assert read(PARENT/'replay_report.json')['all_pass']
    OUT.mkdir(parents=True);synthetic()
    sources=[Path(__file__),R/'src/semana2/variables_ultimo.py',BASE/'partitions.parquet',
        BASE/'claim_assignment_audit.parquet',BASE/'target_T0_and_stresses.parquet',PARENT/'replay_report.json']
    sources += list(PARENT.glob('raw_rates_*.parquet'))+list(PARENT.glob('features_*.parquet'))
    plan={'id':'S2-MISION017-FASE2-TANDA2-v1','author':'Codex','utc':now(),
        'hypothesis':'Las pendientes libres aprendidas con 2023 dañaron la validación 2024. Se prueba la forma T2b conciliada y correcciones cerradas de credibilidad, con dos años de soporte emergente y exclusión conjunta de componentes.',
        'data':'emerging 2023–2024, cinco folds guardados por componentes cliente-dirección; padre T2b fuente developed 2021–2024 ya congelado y conciliado. Ámbito de información: inicio de 2025; no es un backtest prospectivo de 2024.',
        'C0':'Reestimar por ramo/fold solo con ocurrencias y grupos de entrenamiento; curvas, marcas, frecuencias y mezcla excluyen el grupo retenido. Conserva el estimador histórico, misma cola base y reserva 1. Sin cambios de siniestros, bandas o particiones.',
        'models':{'N0':'T2b + nivel Tweedie único por ramo aprendido dentro del fold',
            'N1':'N0 + factores relativos NCB por negocio en motor y previos 0/1/2+ por negocio en cada ramo, n/(n+300), normalización aprendida solo en entrenamiento y nuevo nivel por ramo',
            'N2':'T2b con nivel por negocio contraído al del ramo, n/(n+400), sin cambiar forma',
            'N3':'Forma de N1 y nivel por negocio contraído n/(n+400)'},
        'criterion':{'primary':'D2 sin pesos del OOF total de ambos años; comparador N0',
            'delta_min':.002,'lower95_gt':0.,'positive_folds_min':4,'min_cell_delta_full_null':-.001,
            'post_31_favorable_groups_delta_min':0.,'years':'diferencia puntual >=0 en 2023 y en 2024',
            'secondary':'nuevo/renovación, exposición >=.9, ramos, A/E y nivel; no ajustar sobre etiquetas retenidas ni seleccionar por público'},
        'bootstrap':{'groups':'saved connected component','replicates':2000,'seed':2026102503,'quantiles':[.025,.975]},
        'scope_limits':['2024 desarrollo adaptativo; no promoción formal por política v1','valoración común de reservas a diciembre 2024','maestros sin fecha; clima histórico <=2024, nunca 2025','parent conditional payment/discount snapshot fields retained as historical benchmark','no se considera que fuente desarrollada aumente soporte emergente'],
        'budget':{'new_price_estimator_fits':0,'new_reporting_peril_fits':75,'closed_form_level_constants':105,
            'bucket_credibility_factors_max':140,'bucket_normalizers_max':40,'new_parent_model_fits':0,'submissions':0},
        'sources':{rel(p):sha(p) for p in sources},'B00_preserved':True,'no_automatic_submission':True,'target_public_goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text(plan['hypothesis']+'\n\n'+plan['data']+'\n\n'+plan['C0']+'\n\n'+
        '\n'.join(f'- {k}: {x}' for k,x in plan['models'].items())+'\n\n'+
        'El replay del padre F2 pasó en todos los ramos (variación relativa máxima 4,44e-16); autor original Claude, revisión propia Codex. '+
        'Una prueba sintética del flujo completo confirma que cambiar costes/perils de los grupos retenidos no cambia ningún objeto aprendido ni predicción. '+
        'Criterios y presupuesto en '+rel(PLAN)+'. No hay ajuste de estimadores de precio ni envíos; son estimaciones cerradas de reporte, mezcla y credibilidad. B00 y todas las alternativas permanecen.\n',encoding='utf8')
    p=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261025-MISION017-FASE2-TANDA2-PREVIO','--asunto','2023–2024 por componentes: C0 y credibilidad dentro del fold','--cuerpo',str(body)],
        check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':sha(PLAN),'forum':json.loads(p.stdout)})
    print(json.dumps({'registered':rel(PLAN),'real_price_fits':0,'source_replay_pass':True}))


def run():
    plan=read(PLAN);assert read(OUT/'registration.json')['plan_sha256']==sha(PLAN)
    for p,h in plan['sources'].items():assert sha(ROOT/p)==h
    assert not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()})
    parts=pd.read_parquet(BASE/'partitions.parquet',filters=[('is_test','=',False)])
    target=pd.read_parquet(BASE/'target_T0_and_stresses.parquet',filters=[('is_test','=',False)])
    claims=pd.read_parquet(BASE/'claim_assignment_audit.parquet')
    claims=claims.merge(parts[['market','line','row_id','year','fold']],on=['market','line','row_id'],how='left',validate='many_to_one')
    allpred=[];counter={'reporting':0,'levels':0,'buckets':0,'normalizers':0}
    for line in v.LINES:
        f=pd.read_parquet(PARENT/f'features_{line}.parquet')
        raw=pd.read_parquet(PARENT/f'raw_rates_{line}.parquet')
        f=f.merge(raw[['row_id','annual_raw_T2b']],on='row_id',validate='one_to_one')
        f=f.merge(parts.loc[parts.line.eq(line),['row_id','group_id','fold']],on='row_id',validate='one_to_one')
        f=f.merge(target.loc[target.line.eq(line),['row_id','T0','reserve']],on='row_id',validate='one_to_one')
        f['line']=line;f['is_test']=False
        # Use the already reconciled nominal exposure for the observation link.
        exp=target.loc[target.line.eq(line)].set_index('row_id').exposure
        f['exposure']=exp.reindex(f.row_id).to_numpy(float)
        c=claims.loc[claims.line.eq(line)].copy()
        assert f.group_id.notna().all() and f.fold.notna().all()
        for col in ['group_id','customer_id','address_id']:
            assert f.groupby(col).fold.nunique().max()==1
        for held in range(5):
            pred,a,e=learn_predict(f,c,held);valid=f.loc[f.fold.eq(held)].copy()
            out=valid[['row_id','line','year','group_id','fold','new_business','exposure','T0','reserve']].copy()
            out['e_cost']=e
            for i,name in enumerate(['B00_TEMP_CV2','N0','N1','N2','N3']):out[name]=pred[:,i]
            allpred.append(out)
            digest_before=digest(a)
            dump(OUT/f'learning_{line}_fold{held}.json',{'training_signature':digest_before,'artifact':a})
            counter['reporting']+=len(a['C0']['curves']);counter['levels']+=7
            counter['buckets']+=sum(len(x['factors']) for x in a['shape']);counter['normalizers']+=sum(len(x['normalizers']) for x in a['shape'])
            print(json.dumps({'line':line,'fold':held,'rows':len(out),'training_signature':digest_before}),flush=True)
    p=pd.concat(allpred,ignore_index=True);assert p.row_id.is_unique and len(p)==109296
    p.to_parquet(OUT/'oof_2023_2024.parquet',index=False)
    y=p.T0.to_numpy(float);null=unit(y,np.full(len(y),y.mean())).sum()
    scores={n:float(1-unit(y,p[n].to_numpy(float)).sum()/null) for n in ['B00_TEMP_CV2','N0','N1','N2','N3']}
    dump(OUT/'price_report.json',{'author':'Codex','utc':now(),'status':'closed_form_prices_scored_validation_pending',
        'scores':scores,'rows':len(p),'groups':int(p.group_id.nunique()),'counters':counter,'new_price_estimator_fits':0,
        'new_submissions':0,'B00_preserved':True,'2024_adaptive_development':True,'goal_achieved':False})
    print(json.dumps({'scores':scores,'counters':counter,'submissions':0}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['register','run']);args=parser.parse_args()
    try:register() if args.mode=='register' else run()
    except Exception as exc:
        if OUT.exists():
            with (OUT/f'failure_{args.mode}_{time.time_ns()}.json').open('x',encoding='utf8') as f:
                json.dump({'utc':now(),'type':type(exc).__name__,'error':str(exc)},f)
        raise
