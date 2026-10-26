"""Tanda temporal finita: transferencia, GLM y boosting estándar; nunca envía."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import gc
import json
import os
import subprocess
import sys
import time

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(R/'src')); sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import lightgbm as lgb
import joblib
from scipy import optimize, sparse
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits
from semana2 import fase2_2024_datos as data

OUT = R/'privado/semana2/mision017_fase2/tanda1_20261025_v1'
PLAN = R/'registro/semana2_mision017_fase2_tanda1_plan_v1.json'
FID = 'COD-S2-20261025-MISION017-FASE2-TANDA1-PREVIO'
now = lambda: datetime.now(timezone.utc).isoformat()
rel = lambda p: p.relative_to(ROOT).as_posix()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
dump = data.dump
GLM_NUM = {
    'motor':['x_ncb_years','x_vehicle_age','x_vehicle_value_group','x_prior_claims_5y'],
    'buildings':['x_log_sum_insured','x_property_age','x_accidental_damage_cover','x_days_unoccupied','x_prior_claims_5y'],
    'contents':['x_log_sum_insured','x_high_value_items','x_accidental_damage_cover','x_bedrooms','x_prior_claims_5y']}
GLM_CAT = {
    'motor':['x_region','x_driver_age_band','x_cover_type'],
    'buildings':['x_region','x_property_type','x_construction_type','x_occupancy'],
    'contents':['x_region','x_property_type','x_security_level','x_tenure']}
PARAM = dict(objective='tweedie', tweedie_variance_power=1.5, learning_rate=.03,
             num_leaves=31, min_data_in_leaf=1000, lambda_l2=100., feature_fraction=.8,
             bagging_fraction=.8, bagging_freq=1, verbosity=-1, num_threads=2,
             deterministic=True, force_col_wise=True, seed=20261025)
SMALL = dict(PARAM, learning_rate=.02, num_leaves=7, min_data_in_leaf=500,
             lambda_l2=1000., feature_fraction=1., bagging_fraction=1., bagging_freq=0)


def event(name, **kw):
    row={'utc':now(),'event':name,**kw}
    with (OUT/'events.jsonl').open('a',encoding='utf8') as f:
        f.write(json.dumps(row,default=float)+'\n'); f.flush(); os.fsync(f.fileno())
    print(json.dumps(row,default=float),flush=True)


def unit(y,m):
    assert np.isfinite(m).all() and (m>0).all()
    return 4*y/np.sqrt(m)+4*np.sqrt(m)-8*np.sqrt(y)


def factor(y,m):
    return float(np.sum(y/np.sqrt(m))/np.sum(np.sqrt(m)))


def glm_design(f,line,premium=False):
    out=f.copy();out['x_new_business']=f.x_new_business.astype(float)
    nums=GLM_NUM[line]+['x_new_business']+(['x_log_incumbent_annual_premium'] if premium else [])
    cats=GLM_CAT[line]
    for c in cats: out[c]=out[c].astype('string').fillna('__MISSING__').astype(str)
    for c in nums:out[c]=pd.to_numeric(out[c]).astype(float)
    return out,nums,cats


def fit_glm(f,line,offset,premium=False):
    assert f.year.eq(2023).all() and f.T0.ge(0).all(), 'Solo aprendizaje emergente 2023 en esta tanda temporal.'
    assert np.isfinite(offset).all() and (offset>0).all()
    df,nums,cats=glm_design(f,line,premium)
    enc=ColumnTransformer([
        ('num',Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('scale',StandardScaler())]),nums),
        ('cat',OneHotEncoder(handle_unknown='ignore',min_frequency=100,max_categories=40,drop='first'),cats)],sparse_threshold=1.)
    X=enc.fit_transform(df);X=sparse.hstack([X,np.ones((len(df),1))],format='csr')
    y=f.T0.to_numpy(float);off=np.log(offset);penalty=np.r_[np.ones(X.shape[1]-1),0.]
    beta=np.zeros(X.shape[1]);beta[-1]=np.log(factor(y,offset))
    def obj(b):
        eta=off+X@b;mu=np.exp(eta);a=np.sqrt(mu);b0=y/a
        value=2*np.mean(a+b0-2*np.sqrt(y))+.5*np.dot(penalty*b,b)
        grad=np.asarray(X.T@((a-b0)/len(y))).ravel()+penalty*b
        return float(value),grad
    result=optimize.minimize(obj,beta,jac=True,method='L-BFGS-B',options={'maxiter':2000,'gtol':1e-7,'ftol':1e-13,'maxls':40})
    _,g=obj(result.x)
    assert result.success and np.max(np.abs(g))<1e-4, str(result.message)
    return {'transformer':enc,'coef':result.x,'line':line,'premium':premium}, {'iterations':result.nit,'max_abs_gradient':float(np.abs(g).max())}


def glm_predict(b,f,offset):
    df,_,_=glm_design(f,b['line'],b['premium'])
    X=b['transformer'].transform(df)
    return offset*np.exp(X@b['coef'][:-1]+b['coef'][-1])


def tree_frame(f,columns,categories=None):
    X=f[columns].copy()
    if categories is None:
        categories={c:sorted(f[c].dropna().astype(str).unique()) for c in columns if not pd.api.types.is_numeric_dtype(f[c])}
    for c in columns:
        if c in categories:X[c]=pd.Categorical(X[c].astype('string'),categories=categories[c])
        else:X[c]=pd.to_numeric(X[c]).astype('float32')
    return X,categories


def register():
    assert not OUT.exists() and not PLAN.exists()
    OUT.mkdir(parents=True)
    policy=R/'registro/semana2_politica_desarrollo2024_v2.json'
    plan={
        'id':'S2-MISION017-FASE2-TANDA1-v1','author':'Codex','utc':now(),'scope_policy':rel(policy),
        'scope_policy_sha256':data.sha(policy),'source_years':[2021,2022,2023],'emerging_fit':[2023],'evaluation':[2024],
        'hypothesis':'La fuente 2021–2023 y los perfiles declarados aportan relatividades; ajustes pequeños GLM/boosting pueden corregir el transporte. La prima comercial vigente es una hipótesis separada, con dependencia explícita de la tarifa del asegurador.',
        'observation':'T0 neto en centavos, exposición conciliada. Reutilizar C0 temporal emergente aprendido solo en 2023. Fuente: mismo estimador de reporte histórico, solo ocurrencias 2021–2023, sin mezclar soporte de mercados.',
        'availability':'Sin clima, sin resultados posteriores de póliza, sin identificadores como predictores. Maestros sin fecha bajo hipótesis de estabilidad. La valoración única a diciembre 2024 impide afirmar un backtest prospectivo de reservas disponible en enero 2024.',
        'models':{
            'M0':'LightGBM fuente 400 rondas fijas; nivel por ramo aprendido solo en emergente 2023, sin nuevas pendientes.',
            'M1':'M0 como offset y GLM Tweedie 1.5 de efectos principales, penalización 1 y constante libre; variables congeladas por ramo.',
            'M2':'M0 como offset y LightGBM residual de 100 rondas fijas, 7 hojas, mínimo 500 filas, lambda_l2 1000.',
            'M3':'GLM principal con prima comercial anual vigente como offset, pendiente log-prima libre y variables de M1. La prima no es el objetivo.'},
        'source_features':'F0 físico y contractual común, salvo región, más prior_claims_5y, licence_points, household_size, years_at_address y occupation normalizada. No premium ni outcomes en fuente.',
        'parameters':{'source':PARAM,'source_rounds':400,'residual':SMALL,'residual_rounds':100,'glm_penalty':1.,'glm_num':GLM_NUM,'glm_cat':GLM_CAT},
        'comparators':['M0 como referencia de esta tanda','B00 histórico conservado; constante equivalente con el mismo C0, identificado como B00-TEMP-v2'],
        'criterion_exploratory':{'primary':'D2 temporal 2024 sin pesos, sin ajustar nivel con etiquetas de 2024',
            'required_delta_vs_M0':.002,'paired_group_bootstrap_lower_95_gt':0.,'positive_2024_group_folds_min':4,
            'min_delta_each_line_x_business_full_null':-.001,'post_remove_31_favorable_groups_delta_min':0.,
            'stress':'Misma tarifa fija, mapear con links C0 2023 de reserva .75/1.25 y cola .05/.10; diferencia puntual no negativa.',
            'secondary':'Composición por ramo/negocio/exposición; A/E y cola. Ningún óptimo calculado en evaluación cuenta como predicción.'},
        'bootstrap':{'replicates':2000,'seed':2026102502,'unit':'saved customer-address connected group','quantiles':[.025,.975]},
        'not_formal_v1_promotion':True,'prior_2024_exposure_adaptive':True,
        'cost_budget':{'price_estimator_fits':12,'source_reporting_curves':15,'emerging_C0_fits':0,'closed_form_B00_M0_levels':6,'submissions':0},
        'code':{rel(Path(__file__)):data.sha(Path(__file__)),rel(Path(data.__file__)):data.sha(Path(data.__file__))},
        'B00_preserved':True,'all_alternatives_preserved':True,'no_automatic_submission':True}
    dump(PLAN,plan);dump(OUT/'plan.json',plan)
    body=OUT/'forum_previo.md'
    body.write_text('Nueva tanda exploratoria autorizada con 2024 abierto. '+plan['hypothesis']+'\n\n'+
        '\n'.join(f'- {k}: {v}' for k,v in plan['models'].items())+'\n\n'+
        'Entrenamiento fuente 2021–2023 y adaptación emergente 2023; evaluación 2024 con precios fijos. Reutilizar C0 temporal por ramo, sin recalcularlo con 2024. '+
        'Criterios, variables, parámetros y coste quedan en '+rel(PLAN)+'. Máximo 12 ajustes de precio y 15 curvas de reporte de fuente; cero envíos. '+
        'B00 y todas las alternativas se conservan. La evaluación es adaptativa; no abre ni modifica una confirmación formal anterior. '+
        'No se gastarán los dos cupos en las sondas antiguas. La prima comercial es una entrada condicional de la tarifa vigente; su unidad anual se ha contrastado por bandas de duración, no se divide por exposición.\n',encoding='utf8')
    p=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',FID,
        '--asunto','Tanda temporal preinscrita: transferencia y ajustes estándar, con 2024 abierto','--cuerpo',str(body)],
        check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'utc':now(),'forum':json.loads(p.stdout),'plan_sha256':data.sha(PLAN)})
    print(json.dumps({'registered':rel(PLAN),'new_fits':0,'forum_id':FID}))


def run():
    plan=read(PLAN)
    assert read(OUT/'registration.json')['plan_sha256']==data.sha(PLAN)
    for p,h in plan['code'].items():assert data.sha(ROOT/p)==h, 'Código posterior al registro; requiere nueva versión.'
    assert not (OUT/'started.json').exists(), 'Conciliar ejecución iniciada antes de repetir.'
    dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()})
    if not (data.OUT/'report.json').exists():
        report=data.prepare();event('data_ready',rows=sum(x['rows'] for x in report['rows']))
    outputs=[]
    with threadpool_limits(limits=2):
        for line in data.v.LINES:
            f=pd.read_parquet(data.OUT/f'emerging_{line}.parquet')
            s=pd.read_parquet(data.OUT/f'developed_{line}.parquet')
            assert s.year.isin([2021,2022,2023]).all()
            tr=f.loc[f.year.eq(2023)].copy();te=f.loc[f.year.eq(2024)].copy()
            assert len(tr)>0 and len(te)>0 and not set(tr.row_id)&set(te.row_id)
            columns=[c for c in s if c.startswith('x_') and c not in ['x_region','x_log_incumbent_annual_premium']]
            assert not any(x in columns for x in ['T0','reserve','row_id','exposure'])
            X,cats=tree_frame(s,columns);y=s.T0.to_numpy(float);e=s.e_cost.to_numpy(float)
            event('fit_started',line=line,model='source',rows=len(s))
            source=lgb.train(PARAM,lgb.Dataset(X,label=y/e,weight=np.sqrt(e)),num_boost_round=400)
            source.save_model(str(OUT/f'source_{line}.txt'))
            del s,X;gc.collect()
            Xt,_=tree_frame(tr,columns,cats);Xe,_=tree_frame(te,columns,cats)
            rate_tr=source.predict(Xt,num_threads=2);rate_te=source.predict(Xe,num_threads=2)
            y=tr.T0.to_numpy(float);e=tr.e_cost.to_numpy(float);ev=te.e_cost.to_numpy(float)
            k=factor(y,e*rate_tr);base_tr=k*rate_tr;base_te=k*rate_te
            b00=factor(y,e)
            pred=te[['market','line','row_id','group_id','fold','x_new_business','exposure','T0','reserve','T1_reserve075','T1_reserve125','e_cost','customer_seen_prior_year_any_line',
                'e_cost_mix_0.75','e_cost_mix_1.25','e_cost_mix_tail0.05','e_cost_mix_tail0.1']].copy()
            pred['B00_TEMP_v2']=b00*ev;pred['M0']=base_te*ev
            event('fit_started',line=line,model='M1',rows=len(tr))
            b,detail=fit_glm(tr,line,e*base_tr)
            pred['M1']=glm_predict(b,te,ev*base_te)
            joblib.dump(b,OUT/f'M1_{line}.joblib')
            event('fit_finished',line=line,model='M1',**detail)
            # New residual learner receives only explicit x_ features, no labels/offset in X.
            adaptcols=[c for c in tr if c.startswith('x_') and c!='x_log_incumbent_annual_premium']
            Xa,acats=tree_frame(tr,adaptcols);Xb,_=tree_frame(te,adaptcols,acats)
            event('fit_started',line=line,model='M2',rows=len(tr))
            residual=lgb.train(SMALL,lgb.Dataset(Xa,label=y,init_score=np.log(e*base_tr)),num_boost_round=100)
            residual.save_model(str(OUT/f'M2_{line}.txt'))
            pred['M2']=ev*base_te*np.exp(residual.predict(Xb,raw_score=True,num_threads=2))
            event('fit_started',line=line,model='M3',rows=len(tr))
            b3,detail3=fit_glm(tr,line,e*tr.written_premium.to_numpy(float),premium=True)
            pred['M3']=glm_predict(b3,te,ev*te.written_premium.to_numpy(float))
            joblib.dump(b3,OUT/f'M3_{line}.joblib')
            pred.to_parquet(OUT/f'predictions_2024_{line}.parquet',index=False)
            dump(OUT/f'{line}_metadata.json',{'line':line,'source_columns':columns,'source_categories':cats,
                'adapter_columns':adaptcols,'adapter_categories':acats,'source_level_k':k,'B00_level':b00,
                'M1':detail,'M3':detail3,'new_price_fits':4,'training_years':[2023],'evaluation_years':[2024]})
            outputs.append(pred)
            event('line_complete',line=line,new_price_fits=4)
            del f,tr,te,Xt,Xe,Xa,Xb,source,residual;gc.collect()
    p=pd.concat(outputs,ignore_index=True);y=p.T0.to_numpy(float)
    null=unit(y,np.full(len(y),y.mean())).sum()
    scores={}
    for name in ['B00_TEMP_v2','M0','M1','M2','M3']:
        m=p[name].to_numpy(float);d=unit(y,m)
        assert abs(d.mean()-mean_tweedie_deviance(y,m,power=1.5))<1e-7
        scores[name]=float(1-d.sum()/null)
    p.to_parquet(OUT/'predictions_2024.parquet',index=False)
    report={'author':'Codex','utc':now(),'status':'prices_scored_diagnostics_pending','scores':scores,
        'evaluation_rows':len(p),'evaluation_groups':int(p.group_id.nunique()),'primary_unweighted':True,
        'new_price_fits':12,'new_source_reporting_curves':15,'new_emerging_C0_fits':0,'submissions':0,
        'B00_preserved':True,'2024_is_adaptive_development':True,'prospective_reserve_backtest_proven':False,
        'goal_achieved':False,'outputs':{q.name:data.sha(q) for q in OUT.glob('*') if q.is_file()}}
    dump(OUT/'price_report.json',report);event('price_batch_finished',scores=scores)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['register','run']);args=parser.parse_args()
    try:
        register() if args.mode=='register' else run()
    except Exception as exc:
        if OUT.exists():
            with (OUT/f'failure_{args.mode}_{time.time_ns()}.json').open('x',encoding='utf8') as f:
                json.dump({'utc':now(),'type':type(exc).__name__,'error':str(exc),'mode':args.mode},f)
        raise
