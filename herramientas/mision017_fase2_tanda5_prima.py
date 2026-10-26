"""GLM fuente de información residual de prima anual; nunca confunde P con el objetivo."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import gc
import importlib.util
import json
import os
import subprocess
import sys
import time

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.path.insert(0,str(R/'src'))
import numpy as np
import pandas as pd
from scipy import sparse,optimize
from sklearn.preprocessing import OneHotEncoder
from threadpoolctl import threadpool_limits
spec=importlib.util.spec_from_file_location('mkt',R/'herramientas/mision017_fase2_tanda4_marketing.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
OUT=R/'privado/semana2/mision017_fase2/tanda5_prima_20261025_v1'
PLAN=R/'registro/semana2_mision017_fase2_tanda5_plan_v1.json'
UNIT=OUT.parent/'unidad_prima_vigente_v1/report.json'
CV=m.CV;PARENT=m.PARENT;data=m.data
sha=m.sha;dump=m.dump;read=m.read;rel=m.rel
now=lambda:datetime.now(timezone.utc).isoformat()
ALPHA=.1


def premium_feature(f):
    assert f.written_premium.gt(0).all() and np.isfinite(f.written_premium).all()
    # Annual-like input, never P/exposure. Group median is covariate-only.
    logp=np.log(f.written_premium.to_numpy(float))
    temp=pd.DataFrame({'year':f.year.to_numpy(),'channel':f.channel.astype(str).to_numpy(),'logp':logp})
    center=temp.groupby(['year','channel'],observed=True).logp.transform('median').to_numpy(float)
    return logp-center


def fit_source(f,offset,joint):
    assert f.market.eq('developed').all() and f.year.isin([2021,2022,2023,2024]).all()
    feature=premium_feature(f)
    catcols=(['marketing_segment'] if joint else [])+['source_region','channel']
    cats=OneHotEncoder(drop='first',handle_unknown='ignore',sparse_output=True)
    catframe=f[catcols].astype('string').fillna('__MISSING__').astype(str)
    xc=cats.fit_transform(catframe);years=OneHotEncoder(drop=None,sparse_output=True)
    xy=years.fit_transform(f[['year']]);X=sparse.hstack([feature[:,None],xc,xy],format='csr')
    y=f.T0.to_numpy(float);off=np.log(offset)
    penalty=np.r_[np.ones(1+xc.shape[1]),np.zeros(xy.shape[1])];beta=np.zeros(X.shape[1])
    for i,year in enumerate(years.categories_[0]):
        sel=f.year.eq(year).to_numpy();k=np.sum(y[sel]/np.sqrt(offset[sel]))/np.sum(np.sqrt(offset[sel]));beta[1+xc.shape[1]+i]=np.log(k)
    def objective(b):
        eta=off+X@b;root=np.exp(eta/2);ratio=y/root
        value=2*np.mean(root+ratio-2*np.sqrt(y))+.5*ALPHA*np.dot(penalty*b,b)
        grad=np.asarray(X.T@((root-ratio)/len(f))).ravel()+ALPHA*penalty*b
        return float(value),grad
    result=optimize.minimize(objective,beta,jac=True,method='L-BFGS-B',options={'maxiter':2000,'gtol':1e-7,'ftol':1e-13,'maxls':40})
    value,g=objective(result.x);assert result.success and np.abs(g).max()<1e-4,str(result.message)
    marketing={}
    if joint:
        labels=cats.categories_[0].tolist();marketing={labels[0]:0.}
        marketing.update({label:float(z) for label,z in zip(labels[1:],result.x[1:len(labels)])})
    return {'joint':joint,'logpremium_coefficient':float(result.x[0]),'marketing_log_factors':marketing,
        'coef':result.x.tolist(),'categories':[a.tolist() for a in cats.categories_],'catcols':catcols,
        'year_categories':years.categories_[0].tolist(),'penalty':penalty.tolist(),'alpha':ALPHA,
        'objective':value,'iterations':int(result.nit),'max_abs_gradient':float(np.abs(g).max()),
        'price_estimator_fits':1,'source_rows':len(f),'premium_unit':'annual-like provided quote, not divided by exposure'}


def apply(f,base,effect,strength):
    z=premium_feature(f)*effect['logpremium_coefficient']
    if effect['joint']:
        z+=f.marketing_segment.astype(str).map(effect['marketing_log_factors']).fillna(0).to_numpy(float)
    factor=np.exp(strength*z);out=base.copy();norms={}
    for nb in [0,1]:
        mask=f.new_business.to_numpy(dtype=int)==nb;assert mask.any()
        norm=float(np.sum(base[mask]*factor[mask])/np.sum(base[mask]));out[mask]=base[mask]*factor[mask]/norm;norms[str(nb)]=norm
        assert np.isclose(out[mask].sum(),base[mask].sum(),rtol=1e-12,atol=1e-6)
    return out,norms


def synthetic():
    rng=np.random.default_rng(621);n=600
    f=pd.DataFrame({'market':'developed','year':np.arange(n)%4+2021,'channel':rng.choice(['direct','broker'],n),
        'source_region':rng.choice(['r0','r1'],n),'marketing_segment':rng.choice(['a','b','c'],n),
        'written_premium':np.exp(rng.normal(6,.3,n)),'new_business':np.arange(n)%2,
        'exposure':rng.uniform(.05,1,n),'T0':rng.gamma(2,70,n)*(rng.random(n)<.3)})
    off=rng.uniform(30,160,n);checks=[]
    assert np.array_equal(premium_feature(f),premium_feature(f.assign(exposure=f.exposure*1000)))
    assert np.allclose(premium_feature(f),premium_feature(f.assign(written_premium=f.written_premium*1000)),atol=1e-12,rtol=0)
    for joint in [False,True]:
        b=fit_source(f,off,joint);pred,norm=apply(f,off,b,1.)
        poison=f.assign(T0=-1e30,reserve=-1e30);alt,_=apply(poison,off,b,1.)
        assert np.array_equal(pred,alt);checks.append({'joint':joint,'gradient':b['max_abs_gradient']})
    dump(OUT/'synthetic.json',{'pass':True,'premium_not_divided_by_exposure':True,'currency_shift_invariant':True,
        'held_label_invariant':True,'cell_totals_preserved':True,'checks':checks,'synthetic_price_fits':2,'contest_price_fits':0})


def register():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True);synthetic()
    audit=read(UNIT)
    assert all(abs(x['median_logP_change_per_logE_change'])<.02 for x in audit['pairs'])
    sources=[Path(__file__),Path(m.__file__),UNIT,CV/'oof_2023_2024.parquet',data.OUT/'report.json',
        data.RAW/'customers.parquet',data.RAW/'addresses.parquet',ROOT/'Hackaton/Semana 2/Datos/emerging/customers.parquet']
    for line in data.LINES:
        sources += [data.OUT/f'{line}.parquet',data.RAW/f'policies_{line}.parquet',
            ROOT/f'Hackaton/Semana 2/Datos/emerging/policies_{line}.parquet',PARENT/f'features_{line}.parquet',PARENT/f'modelos/prod/T2b_{line}.txt']
    plan={'id':'S2-MISION017-FASE2-TANDA5-PRIMA-v1','author':'Codex','utc':now(),
        'hypothesis':'The provided current premium behaves annual-like in both markets. Previous WP variants divided it by exposure or made it the dominant offset. Test only residual information in a source-trained small GLM, keeping claims as response and T2b risk as offset.',
        'unit_evidence':'Split-policy pairs selected by exposure, not price: median logP/logE change approximately0 in both markets; this is empirical unit support, not proof of a dated tariff formula.',
        'source_fit':'Tweedie1.5, source net observed cost, offset source_e_cost*T2b_rate on stored source precision. Main effect log(annualP)-median(logP bysourceyear/channel); source region/channel nuisance, four free source-year intercepts; alpha.1. No clipping. Variant joint adds marketing_segment. Only premium/marketing effects transfer.',
        'models':{'S1':'Full premium-only source effect','S2':'Full joint premium+marketing source effects','S3':'Half joint source effects'},
        'target':'Existing N3 held-component prices, 2023–2024. Target premium centering is year×channel within the known evaluated portfolio, using input values only. Cell predicted-cost normalization preserves line×new_business totals. No held claims fit parameters or levels.',
        'criterion':{'delta_min':.002,'lower95_gt':0.,'positive_folds_min':4,'min_cell_delta_full_null':-.001,
            'post31_nonnegative':True,'both_years_nonnegative':True},
        'bootstrap':{'replicates':2000,'seed':2026102506,'unit':'saved connected component','quantiles':[.025,.975]},
        'budget':{'source_price_estimator_fits':6,'source_C0_fits':0,'target_C0_fits':0,'new_target_label_fitted_levels':0,
            'portfolio_normalizers':90,'covariate_premium_medians':'source≤36;target≤90, input-only','submissions':0},
        'scope':'Available official historical information through2024, conditional competition prediction for2025. No2025claim labels or futureweather; no prospective2024 claim.',
        'limits':['Incumbent commercial premium is a conditional external input, not ultimate-risk truth or this model output.',
            'No exact equality between tariffs or commercial loading formula is assumed across countries.',
            'Supplied profiles/quotes lack historic versions; source effect transport must be validated.',
            'Portfolio transforms are covariate-only/transductive, not online pricing confirmation.',
            '2024adaptive development, source parameter/C0 uncertainty not fully identified.'],
        'sources':{rel(p):sha(p) for p in sources},'B00_preserved':True,'all_alternatives_preserved':True,'no_automatic_submission':True}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('La comprobación de unidades aporta una corrección concreta: written_premium se comporta como una prima anual, no como importe multiplicado por exposición. '+
        'En pares de tramos con duraciones muy distintas la mediana de cambio logP/logE es cercana a cero en los dos mercados. '+
        'No se convierte la prima cobrada en objetivo ni se supone una fórmula exacta de gastos.\n\n'+plan['source_fit']+'\n\n'+
        '\n'.join(f'- {k}: {x}' for k,x in plan['models'].items())+'\n\n'+plan['target']+'\n\n'+
        'Se mantienen criterios y folds. Máximo seis GLM fuente, cero curvas C0 nuevas y cero envíos. Las pruebas sintéticas verificaron gradientes, conservación de totales, invariancia al cambio de moneda y que modificar exposición no altera el predictor de prima. '+
        'Plan: '+rel(PLAN)+'.\n',encoding='utf8')
    p=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261025-MISION017-FASE2-TANDA5-PRIMA-PREVIO','--asunto','Prima vigente anual como información residual de fuente, con GLM sencillo','--cuerpo',str(body)],
        check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':sha(PLAN),'forum':json.loads(p.stdout)})
    print(json.dumps({'registered':rel(PLAN),'contest_fits':0}))


def run():
    plan=read(PLAN);assert read(OUT/'registration.json')['plan_sha256']==sha(PLAN)
    for p,h in plan['sources'].items():assert sha(ROOT/p)==h
    assert not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()})
    master=pd.read_parquet(data.RAW/'customers.parquet',columns=['customer_id','marketing_segment'])
    regions=pd.read_parquet(data.RAW/'addresses.parquet',columns=['address_id','region']).rename(columns={'region':'source_region'})
    targetmaster=pd.read_parquet(ROOT/'Hackaton/Semana 2/Datos/emerging/customers.parquet',columns=['customer_id','marketing_segment'])
    old=pd.read_parquet(CV/'oof_2023_2024.parquet');outputs=[]
    with threadpool_limits(limits=2):
        for line in data.LINES:
            f=pd.read_parquet(data.OUT/f'{line}.parquet')
            premium=pd.read_parquet(data.RAW/f'policies_{line}.parquet',columns=['row_id','written_premium'])
            f=f.merge(premium,on='row_id',validate='one_to_one').merge(master,on='customer_id',validate='many_to_one').merge(regions,on='address_id',validate='many_to_one')
            model=m.lgb.Booster(model_file=str(PARENT/f'modelos/prod/T2b_{line}.txt'))
            offset=f.e_cost.to_numpy(float)*np.exp(model.predict(m.source_matrix(f,model),raw_score=True,num_threads=2));del model
            effects={}
            for joint,name in [(False,'premium'),(True,'joint')]:
                print(json.dumps({'utc':now(),'event':'fit_started','line':line,'family':name,'rows':len(f)}),flush=True)
                a=fit_source(f,offset,joint);dump(OUT/f'{name}_{line}.json',{'line':line,'source_sha256':sha(data.OUT/f'{line}.parquet'),**a});effects[name]=a
                print(json.dumps({'event':'fit_complete','line':line,'family':name,'iterations':a['iterations'],'price_beta':a['logpremium_coefficient'],'max_gradient':a['max_abs_gradient']}),flush=True)
            ftarget=pd.read_parquet(PARENT/f'features_{line}.parquet',columns=['row_id','customer_id','channel'])
            pt=pd.read_parquet(ROOT/f'Hackaton/Semana 2/Datos/emerging/policies_{line}.parquet',columns=['row_id','written_premium'])
            t=old.loc[old.line.eq(line)].merge(ftarget,on='row_id',validate='one_to_one').merge(pt,on='row_id',validate='one_to_one').merge(targetmaster,on='customer_id',validate='many_to_one')
            for name in ['S1','S2','S3']:t[name]=np.nan
            for held in range(5):
                mask=t.fold.eq(held);batch=t.loc[mask];norms={}
                for name,family,strength in [('S1','premium',1.),('S2','joint',1.),('S3','joint',.5)]:
                    pred,norm=apply(batch,batch.N3.to_numpy(float),effects[family],strength);t.loc[mask,name]=pred;norms[name]=norm
                dump(OUT/f'normalizers_{line}_fold{held}.json',{'line':line,'fold':held,'normalizers':norms,
                    'kind':'portfolio-input-only, no claim labels','premium_effect_sha256':sha(OUT/f'premium_{line}.json'),'joint_effect_sha256':sha(OUT/f'joint_{line}.json')})
            outputs.append(t);del f,offset;gc.collect()
    p=pd.concat(outputs,ignore_index=True);assert p.row_id.is_unique and len(p)==109296
    assert p[['S1','S2','S3']].notna().all().all();p.to_parquet(OUT/'oof_2023_2024.parquet',index=False)
    y=p.T0.to_numpy(float);den=m.unit(y,np.full(len(y),y.mean())).sum()
    scores={name:float(1-m.unit(y,p[name].to_numpy(float)).sum()/den) for name in ['N0','N3','S1','S2','S3']}
    dump(OUT/'price_report.json',{'author':'Codex','utc':now(),'status':'prices_scored_validation_pending','scores':scores,
        'source_price_fits':6,'source_C0_fits':0,'target_C0_fits':0,'new_target_label_fitted_levels':0,'portfolio_normalizers':90,
        'new_submissions':0,'B00_preserved':True,'goal_achieved':False})
    print(json.dumps({'scores':scores,'source_price_fits':6,'new_submissions':0}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['register','run']);a=p.parse_args()
    try:register() if a.mode=='register' else run()
    except Exception as exc:
        if OUT.exists():
            with (OUT/f'failure_{a.mode}_{time.time_ns()}.json').open('x',encoding='utf8') as f:
                json.dump({'utc':now(),'type':type(exc).__name__,'error':str(exc)},f)
        raise
