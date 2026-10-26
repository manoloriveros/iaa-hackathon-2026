"""Un efecto fuente GLM para marketing_segment; conserva los niveles del padre."""
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
import lightgbm as lgb
from scipy import sparse,optimize
from sklearn.preprocessing import OneHotEncoder
from threadpoolctl import threadpool_limits
from semana2 import fuente_f2_2024_cb as data
from semana2.fase2_2024_datos import sha,dump

OUT=R/'privado/semana2/mision017_fase2/tanda4_marketing_20261025_v1'
CV=OUT.parent/'tanda2_20261025_v1';PARENT=data.PARENT
PLAN=R/'registro/semana2_mision017_fase2_tanda4_plan_v1.json'
ADMISSION=OUT.parent/'admisibilidad_campos_comunes_v1/report.json'
rel=lambda p:p.relative_to(ROOT).as_posix()
now=lambda:datetime.now(timezone.utc).isoformat()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
CATS={'channel','payment_method','marital_status','age_band','occupation','urban_density','soil_type',
      'property_type','roof_type','energy_rating','body_type','transmission','fuel_type','cover_type',
      'overnight_parking','vehicle_use','construction','occupancy','tenure','security_level'}
ALPHA=.1


def unit(y,m):return 4*y/np.sqrt(m)+4*np.sqrt(m)-8*np.sqrt(y)


def source_matrix(f,model):
    cols=model.feature_name();cats=[c for c in cols if c in CATS];X=f[cols].copy()
    assert len(cats)==len(model.pandas_categorical)
    for c in cols:
        if c in CATS:X[c]=pd.Categorical(X[c].astype('string'),categories=model.pandas_categorical[cats.index(c)])
        else:X[c]=pd.to_numeric(X[c]).astype(float)
    return X


def fit_effect(f,offset):
    assert f.market.eq('developed').all() and f.year.isin([2021,2022,2023,2024]).all()
    assert f.marketing_segment.notna().all() and f.source_region.notna().all()
    mark=OneHotEncoder(drop='first',handle_unknown='ignore',sparse_output=True)
    region=OneHotEncoder(drop='first',handle_unknown='ignore',sparse_output=True)
    years=OneHotEncoder(drop=None,handle_unknown='error',sparse_output=True)
    xm=mark.fit_transform(f[['marketing_segment']]);xr=region.fit_transform(f[['source_region']]);xy=years.fit_transform(f[['year']])
    X=sparse.hstack([xm,xr,xy],format='csr');y=f.T0.to_numpy(float)
    assert np.isfinite(offset).all() and (offset>0).all()
    off=np.log(offset);nmark=xm.shape[1];nr=xr.shape[1]
    penalty=np.r_[np.ones(nmark+nr),np.zeros(xy.shape[1])]
    beta=np.zeros(X.shape[1])
    for i,year in enumerate(years.categories_[0]):
        m=f.year.eq(year).to_numpy();k=np.sum(y[m]/np.sqrt(offset[m]))/np.sum(np.sqrt(offset[m]));beta[nmark+nr+i]=np.log(k)
    def objective(b):
        eta=off+X@b;root=np.exp(eta/2);ratio=y/root
        value=2*np.mean(root+ratio-2*np.sqrt(y))+.5*ALPHA*np.dot(penalty*b,b)
        gradient=np.asarray(X.T@((root-ratio)/len(f))).ravel()+ALPHA*penalty*b
        return float(value),gradient
    result=optimize.minimize(objective,beta,jac=True,method='L-BFGS-B',options={'maxiter':2000,'gtol':1e-7,'ftol':1e-13,'maxls':40})
    value,g=objective(result.x);assert result.success and np.abs(g).max()<1e-4,str(result.message)
    categories=mark.categories_[0].tolist();coefs={categories[0]:0.}
    coefs.update({k:float(z) for k,z in zip(categories[1:],result.x[:nmark])})
    return {'marketing_log_factors':coefs,'source_region_nuisance':result.x[nmark:nmark+nr].tolist(),
        'source_year_nuisance':result.x[nmark+nr:].tolist(),'source_regions':region.categories_[0].tolist(),
        'source_years':years.categories_[0].tolist(),'alpha':ALPHA,'max_abs_gradient':float(np.abs(g).max()),
        'iterations':int(result.nit),'objective':value,'price_estimator_fits':1}


def overlay(f,pred,coefs,strength):
    labels=f.marketing_segment.astype(str);delta=labels.map(coefs).fillna(0.).to_numpy(float)
    factor=np.exp(strength*delta);out=pred.copy();norms={}
    for nb in [0,1]:
        mask=f.new_business.to_numpy(dtype=int)==nb
        assert mask.any() and pred[mask].sum()>0
        normalizer=float(np.sum(pred[mask]*factor[mask])/np.sum(pred[mask]))
        out[mask]=pred[mask]*factor[mask]/normalizer;norms[str(nb)]=normalizer
        assert np.isclose(out[mask].sum(),pred[mask].sum(),rtol=1e-12,atol=1e-6)
    return out,norms


def synthetic():
    rng=np.random.default_rng(74);n=400
    f=pd.DataFrame({'market':'developed','year':np.arange(n)%4+2021,'marketing_segment':rng.choice(['a','b','c'],n),
        'source_region':rng.choice(['r0','r1'],n),'T0':rng.gamma(2,60,n)*(rng.random(n)<.4),'new_business':np.arange(n)%2})
    offset=rng.uniform(20,140,n);a=fit_effect(f,offset)
    p,norm=overlay(f,offset,a['marketing_log_factors'],1.)
    z,_=overlay(f.assign(T0=-1e30),offset,a['marketing_log_factors'],1.)
    assert np.array_equal(p,z)
    unknown=f.assign(marketing_segment='new');u,_=overlay(unknown,offset,a['marketing_log_factors'],1.)
    assert np.array_equal(u,offset)
    dump(OUT/'synthetic.json',{'pass':True,'GLM_gradient_checked':True,'held_label_invariance':True,
        'cell_total_preservation':True,'unknown_category_neutral':True,'synthetic_price_fits':1,'contest_price_fits':0})


def register():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True)
    admission=read(ADMISSION);record=next(x for x in admission['rows'] if x['field']=='marketing_segment')
    assert record['target_historical_covered_by_source']==record['target_test_covered_by_source']==1.
    assert record['source_mutual_information_with_credit_band_nats']>.9
    synthetic()
    paths=[Path(__file__),ADMISSION,CV/'oof_2023_2024.parquet',CV/'validation_v1/report.json',
        data.OUT/'report.json',data.RAW/'customers.parquet',data.RAW/'addresses.parquet',
        ROOT/'Hackaton/Semana 2/Datos/emerging/customers.parquet']
    paths+=list(data.OUT.glob('motor.parquet'))+list(data.OUT.glob('buildings.parquet'))+list(data.OUT.glob('contents.parquet'))
    paths+=list((PARENT/'modelos/prod').glob('T2b_*.txt'))
    plan={'id':'S2-MISION017-FASE2-TANDA4-MKT-v1','author':'Codex','utc':now(),
        'hypothesis':'marketing_segment is an available shared field omitted by the source T2b; in488180source historical customers it has mutual information .99777nats with unavailable emerging credit_band. Test its residual source effect with a small GLM, not a target-trained high-variance model.',
        'not_claimed':'Source association does not prove a causal effect, shared risk meaning or predictive transport; local component OOF must test it. credit_band is never an emerging input or invented label.',
        'source_GLM':'Tweedie1.5 loglink, offset source_e_cost*source_T2b_rate on stored sourcefeature precision; categorical marketing_segment main effects, source-region nuisance and four unpenalized source-year intercepts. Only marketing coefficients transfer. alpha.1 for marketing/region. No label clipping.',
        'source_years':[2021,2022,2023,2024],'source_model_count':3,
        'target':'Existing N3 OOF2023–2024, with all C0 and risk calibrators excluding the saved connected component. N3 is a research comparator close to F2 corrections; not a promotion/replacement of B00/F2.',
        'models':{'R1':'Full source marketing logeffect','R2':'Half source marketing logeffect','R3':'Quarter source marketing logeffect'},
        'portfolio_transform':'Multiply frozen N3 prices by exp(strength*source_marketing_coefficient). Normalize within line×new_business on the evaluated known portfolio using predicted costs only, preserving that cell total. No held labels fit levels. This is explicitly a batch-portfolio, covariate-only transform; no online/prospective independence claim.',
        'criterion':{'delta_min':.002,'lower95_gt':0.,'positive_folds_min':4,'min_cell_delta_full_null':-.001,
            'post31_nonnegative':True,'both_years_nonnegative':True},
        'bootstrap':{'replicates':2000,'seed':2026102505,'unit':'saved connected component','quantiles':[.025,.975]},
        'budget':{'price_estimator_fits':3,'source_reporting_refits':0,'target_reporting_refits':0,
            'new_label_fitted_target_levels':0,'portfolio_normalizers':90,'submissions':0},
        'quality_limits':['Undated profile and marketing definition availability is conditional on supplied snapshot.',
            'Shared tokens do not certify same underwriting effect across countries.',
            'Credit proxy/social-group effects require explanation; no real-world underwriting suitability or legal approval asserted.',
            'Source teacher is evaluated at the stored source numeric precision; original N3 reference values are preserved exactly.',
            '2024adaptive development, not intact independent confirmation.'],
        'sources':{rel(p):sha(p) for p in paths},'B00_preserved':True,'all_alternatives_preserved':True,'no_automatic_submission':True}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Se prioriza una variable común antes de añadir complejidad. La auditoría sin costes encontró que marketing_segment comparte las12categorías entre fuente, histórico y test, y está fuertemente relacionado con credit_band en fuente (I=.99777nats,488180clientes). '+
        'Eso solo justifica la hipótesis, no demuestra transporte ni mejora.\n\n'+plan['source_GLM']+'\n\n'+plan['portfolio_transform']+'\n\n'+
        'Se preinscriben fuerzas1,.5,.25; se usa N3 como referencia de investigación sin promoverlo ni reemplazar B00/F2. Cero nuevas curvas C0, niveles aprendidos con etiquetas retenidas o envíos. '+
        'Modelo y límites: '+rel(PLAN)+'. La prueba sintética del GLM, el gradiente, categorías nuevas y conservación de totales pasó antes de ajustar con datos reales.\n',encoding='utf8')
    p=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261025-MISION017-FASE2-TANDA4-MKT-PREVIO','--asunto','Efecto fuente sencillo de marketing_segment, con validación por componentes','--cuerpo',str(body)],
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
    old=pd.read_parquet(CV/'oof_2023_2024.parquet')
    # Match each existing prediction to its provided customer profile, never by another market's keys.
    ids=pd.concat([pd.read_parquet(PARENT/f'features_{line}.parquet',columns=['row_id','customer_id']) for line in data.LINES],ignore_index=True)
    output=old.merge(ids,on='row_id',validate='one_to_one').merge(targetmaster,on='customer_id',validate='many_to_one')
    assert len(output)==len(old) and output.marketing_segment.notna().all()
    for name in ['R1','R2','R3']:output[name]=np.nan
    with threadpool_limits(limits=2):
        for line in data.LINES:
            f=pd.read_parquet(data.OUT/f'{line}.parquet')
            f=f.merge(master,on='customer_id',validate='many_to_one').merge(regions,on='address_id',validate='many_to_one')
            model=lgb.Booster(model_file=str(PARENT/f'modelos/prod/T2b_{line}.txt'))
            X=source_matrix(f,model);rate=np.exp(model.predict(X,raw_score=True,num_threads=2));del X,model
            offset=f.e_cost.to_numpy(float)*rate
            print(json.dumps({'event':'source_GLM_fit_started','line':line,'rows':len(f),'utc':now()}),flush=True)
            effect=fit_effect(f,offset);dump(OUT/f'marketing_{line}.json',{'line':line,'source_sha256':sha(data.OUT/f'{line}.parquet'),**effect})
            coefs=effect['marketing_log_factors']
            for held in range(5):
                mask=output.line.eq(line)&output.fold.eq(held);t=output.loc[mask]
                norms={}
                for strength,name in [(1.,'R1'),(.5,'R2'),(.25,'R3')]:
                    p,n=overlay(t,t.N3.to_numpy(float),coefs,strength);output.loc[mask,name]=p;norms[name]=n
                dump(OUT/f'normalizers_{line}_fold{held}.json',{'kind':'held_covariate_predicted_cost_only_no_labels',
                    'line':line,'fold':held,'normalizers':norms,'marketing_effect_sha256':sha(OUT/f'marketing_{line}.json')})
            print(json.dumps({'event':'source_GLM_finished','line':line,'iterations':effect['iterations'],
                'max_abs_gradient':effect['max_abs_gradient'],'min_logeffect':min(coefs.values()),'max_logeffect':max(coefs.values())}),flush=True)
            del f,offset,rate;gc.collect()
    assert output[['R1','R2','R3']].notna().all().all()
    output.to_parquet(OUT/'oof_2023_2024.parquet',index=False)
    y=output.T0.to_numpy(float);null=unit(y,np.full(len(y),y.mean())).sum()
    scores={n:float(1-unit(y,output[n].to_numpy(float)).sum()/null) for n in ['N0','N3','R1','R2','R3']}
    dump(OUT/'price_report.json',{'author':'Codex','utc':now(),'status':'prices_scored_validation_pending','scores':scores,
        'price_estimator_fits':3,'reporting_refits':0,'new_label_fitted_target_levels':0,'portfolio_normalizers':90,
        'new_submissions':0,'B00_preserved':True,'goal_achieved':False})
    print(json.dumps({'scores':scores,'new_price_fits':3,'new_submissions':0}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['register','run']);a=p.parse_args()
    try:register() if a.mode=='register' else run()
    except Exception as exc:
        if OUT.exists():
            with (OUT/f'failure_{a.mode}_{time.time_ns()}.json').open('x',encoding='utf8') as f:
                json.dump({'utc':now(),'type':type(exc).__name__,'error':str(exc)},f)
        raise
