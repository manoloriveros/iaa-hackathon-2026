"""Operador exacto de producción sobre bases retenidas; no aprende ni envía."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';PUL=BASE/'forma_ultima_PUL_20261026_v1'
HET=BASE/'enlace_HET_20261026_v1';PROD=BASE/'F3c_PUL2_prototipo_20261026_v1'
SBASE=BASE/'A1S_nucleo_20261026_v1/target_complete_core'
OUT=BASE/'transferencia_PUL2_20261026_v1';PLAN=R/'registro/semana2_transferencia_PUL2_plan_v1.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


producer=load('transfer_exact_PUL2_producer',R/'herramientas/preparar_F3c_PUL2_2025.py')
stats=load('transfer_PUL2_metric',R/'herramientas/glm_discrepancia_A1S.py')
w=producer.w;unit=stats.unit
NAMES=['S0','S1','S2']


def dump(path,value):
    assert not path.exists();path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')


def register():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir()
    files=[Path(__file__),Path(producer.__file__),Path(stats.__file__),PUL/'report.json',PUL/'oof_2023_2024.parquet',
        SBASE/'oof_2023_2024.parquet',SBASE/'report.json',PROD/'report.json',PROD/'member_prices_2025.parquet',
        producer.old.COHORT,BASE/'FSp_REN_G3_prod_contraste_20261026_v1/A1_original2024_proxy_prices.parquet']
    pre=w.read(PUL/'preflight.json')
    for a in pre['scopes']:
        assert w.sha(ROOT/a['input'])==a['sha256'];files.append(ROOT/a['input'])
    plan={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'type':'diagnostic_only_no_admission',
        'question':'Does the exact actual-production operator preserve its direction on other frozen historical price bases, rather than infer F3cimprovement from G3alone?',
        'bases':{'S0':'Source-safe A1Swith standard calibration','S1':'Fixed .5A1S+.5T2b','S2':'S1plus frozen source-safe residual factors',
            'A1original2024':'Auxiliary conditional proxy only; its original pooled observation ancestry is not group-independent confirmation.',
            'G3':'Identity control only, reuse PUL2receipt without another statistical assay.'},
        'formula':'Use exact productioncorrect_member: base*(H1/G3), then same pureultimateFSpRENpower normalized to each correctedbase RENtotal per line/year. NBhas only exposure correction. Sourcefold profile/ratios fixed from the same held scope.',
        'fixed_weights_REN':producer.WEIGHTS,'level_sensitivity':[.95,1.,1.05],
        'bootstrap':{'replicates':2000,'seed':2026102614,'unit':'saved global component','joint_S0_S1_S2':True,
            'simultaneous95':'Bonferroni3, exploration only','A1cohort':'separate2024conditional diagnostic'},
        'readout':'Report all declared bases, folds/years/cells, post31and worst single-group removal, level sensitivities. No choosing proxy/level by score, fitting, clipping, source updates, promotion or CSVchange.',
        'future_member_stability':'Summarize stored5futuremember costs by line/business; correlated models are not independent confidence samples.',
        'budget':{'new_model_fits':0,'new_C0_fits':0,'new_calibrations':0,'new_source_inference':0,
            'new_adjusted_historical_price_rows':3*109296+59202,'new_prediction_normalizers':105,
            'G3_identity_recomputation_normalizers_separate':30,'new_CSVs':0,'new_submissions':0},
        'limits':['Not a full historicF3cnumerical replay','Does not erase mainPUL2post31failure or validate future5memberensemble',
            'Adaptive repeated research; CIs conditional/exploratory, not professional independent confirmation',
            'Source/risk-mixture/tail/reserve/vintage assumptions and weightedESSfailure remain'],
        'submission_allowed':False,'2024_open':True,'B00_all_alternatives_preserved':True,
        'sources':{w.rel(p):w.sha(p) for p in files}}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. Registro antes de nuevos precios/diagnósticos de score una revisión de transferencia del operador exacto de producción. '
        'Se aplicará a S0/S1/S2 guardados y, aparte, al proxy A1 original de 2024. G3 es solo control de identidad con PUL2; se reutiliza su informe. '
        'La forma REN se renormaliza sobre cada base ya corregida H1/G3, igual que en el prototipo, sin añadir parámetros o elegir el mejor proxy. '
        'Se reportarán todas las bases, años/folds/celdas, concentración y niveles fijos ±5%; bootstrap conjunto por grupos y bandas simultáneas exploratorias. '
        'Se revisará la dispersión de los cinco miembros futuros guardados; no son cinco muestras independientes. '
        'Cero ajustes, C0, inferencias fuente, CSV nuevos o envíos. Esta revisión no suple el F3c histórico completo ni elimina el fallo post31 o la falta de validación anidada. '
        'B00/F3c y alternativas intactos; 2024 abierto. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-PUL2-TRANSFERENCIA-PREVIO','--asunto','Transferencia PUL2 registrada: operador real sobre bases guardadas',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(response.stdout)})
    print(json.dumps({'registered':True,'new_fits':0,'forum':json.loads(response.stdout)}))


def metrics(p,names,plan,tag):
    y=p.T0.to_numpy(float);den=unit(y,np.full(len(y),y.mean())).sum()
    gain=np.column_stack([unit(y,p[n].to_numpy())-unit(y,p['T_'+n].to_numpy()) for n in names])
    for name in names:
        assert abs(unit(y,p['T_'+name].to_numpy()).mean()-mean_tweedie_deviance(y,p['T_'+name],power=1.5))<1e-8
    frame=pd.DataFrame({'group_id':p.group_id,'N':1.,'Y':y,'sqrtY':np.sqrt(y),**{n:gain[:,j] for j,n in enumerate(names)}})
    group=frame.groupby('group_id',sort=True).sum();v=group.to_numpy()
    rng=np.random.default_rng(plan['bootstrap']['seed']);draws=[]
    for _ in range(2000):
        z=v[rng.integers(0,len(v),len(v))].sum(axis=0)
        dd=8*(np.sqrt(z[0]*z[1])-z[2]);assert dd>0;draws.append(z[3:]/dd)
    draws=np.array(draws);np.save(OUT/(tag+'_bootstrap.npy'),draws);results={}
    for j,name in enumerate(names):
        gg=gain[:,j];delta=float(gg.sum()/den);ci=np.quantile(draws[:,j],[.025,.975]).tolist()
        sim=np.quantile(draws[:,j],[.025/len(names),1-.025/len(names)]).tolist()
        folds={str(k):float(gg[p.fold.eq(k)].sum()/den) for k in range(5)}
        years={str(k):float(gg[p.year.eq(k)].sum()/den) for k in sorted(p.year.unique())}
        cells=[]
        for (line,year,nb),ii in p.groupby(['line','year','new_business']).groups.items():
            ii=np.array(list(ii));yy=y[ii];dd=unit(yy,np.full(len(yy),yy.mean())).sum()
            cells.append({'line':line,'year':int(year),'NB':int(nb),'delta_global':float(gg[ii].sum()/den),'delta_cell_null':float(gg[ii].sum()/dd)})
        pergroup=group[name].sort_values(ascending=False)
        post31=float((pergroup.sum()-pergroup.iloc[:31].sum())/den)
        worst_single=float((pergroup.sum()-pergroup.iloc[0])/den)
        levels={str(c):float((unit(y,p[name].to_numpy()*c)-unit(y,p['T_'+name].to_numpy()*c)).sum()/den) for c in plan['level_sensitivity']}
        results[name]={'delta':delta,'bootstrap95':ci,'simultaneous95_family':sim,'folds':folds,'years':years,'cells':cells,
            'post31_delta':post31,'worst_single_group_removed_delta':worst_single,'same_level_sensitivities':levels,
            'scores':{'base':float(1-unit(y,p[name].to_numpy()).sum()/den),'corrected':float(1-unit(y,p['T_'+name].to_numpy()).sum()/den)},
            'direction_coherence':{'point_positive':delta>0,'lower95_positive':ci[0]>0,'all_years_positive':min(years.values())>0,
                'at_least4positive_folds':sum(z>0 for z in folds.values())>=4,'post31_nonnegative':post31>=0}}
    group.to_parquet(OUT/(tag+'_group_influence.parquet'))
    return results


def run():
    assert not (OUT/'report.json').exists() and not (OUT/'started.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    import os
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})
    p=pd.read_parquet(PUL/'oof_2023_2024.parquet')
    bases=pd.read_parquet(SBASE/'oof_2023_2024.parquet').set_index('row_id').loc[p.row_id]
    for col in ['T0','fold','group_id','year','new_business']:assert np.array_equal(p[col],bases[col])
    for name in NAMES:p[name]=bases[name].to_numpy();p['T_'+name]=np.nan
    raw=pd.read_parquet(BASE/'FSp_REN_G3_prod_contraste_20261026_v1/A1_original2024_proxy_prices.parquet',columns=['row_id','A1'])
    a=p.loc[p.year.eq(2024),['row_id','line','year','new_business','fold','group_id','T0']].merge(raw,on='row_id',validate='one_to_one')
    a['T_A1']=np.nan;assert len(a)==59202
    ix=pd.Series(p.index.to_numpy(),index=p.row_id);ia=pd.Series(a.index.to_numpy(),index=a.row_id)
    checks=[]
    for scope in w.read(PUL/'preflight.json')['scopes']:
        f=pd.read_parquet(ROOT/scope['input']);r=f.ratio_ultimate.to_numpy(float);ids=ix.loc[f.row_id].to_numpy()
        profile=p.loc[ids,'H1'].to_numpy()/p.loc[ids,'G3'].to_numpy()
        for year in [2023,2024]:
            select=f.year.eq(year).to_numpy();ff=f.loc[select];rr=r[select];u=profile[select];ii=ids[select]
            identity,_=producer.correct_member(ff,p.loc[ii,'G3'].to_numpy(),u,rr,scope['line'])
            assert np.allclose(identity,p.loc[ii,'PUL2'].to_numpy(),rtol=2e-13,atol=1e-9)
            for name in NAMES:
                pred,_=producer.correct_member(ff,p.loc[ii,name].to_numpy(),u,rr,scope['line'])
                p.loc[ii,'T_'+name]=pred
            if year==2024:
                jj=ia.loc[ff.row_id].to_numpy()
                pred,_=producer.correct_member(ff,a.loc[jj,'A1'].to_numpy(),u,rr,scope['line'])
                a.loc[jj,'T_A1']=pred
        checks.append({'line':scope['line'],'held':scope['held'],'G3_identity_matches_cached_PUL2_within_rounding':True,
            'same_production_operator_no_new_learning':True,'samefold_H1_and_FSp_profiles':True})
    assert p[['T_'+n for n in NAMES]].notna().all().all() and a.T_A1.notna().all()
    p.to_parquet(OUT/'held_proxy_prices_all_years.parquet',index=False);a.to_parquet(OUT/'held_A1_2024_proxy_prices.parquet',index=False)
    with threadpool_limits(limits=2):
        full=metrics(p,NAMES,plan,'source_safe_bases');conditional=metrics(a,['A1'],plan,'conditional_A1_2024')
    future=pd.read_parquet(PROD/'member_prices_2025.parquet');cohort=pd.read_parquet(producer.old.COHORT).set_index('row_id').loc[future.row_id]
    member=future[[f'member{k}' for k in range(5)]].to_numpy();spread=member.max(axis=1)/member.min(axis=1)
    stability=[]
    for (line,nb),ii in cohort.reset_index().groupby(['line','new_business']).groups.items():
        ii=np.asarray(list(ii));stability.append({'line':line,'new_business':int(nb),'rows':len(ii),
            'max_min_member_price_ratio_quantiles':np.quantile(spread[ii],[.5,.9,.99,1]).tolist(),
            'fraction_spread_gt1_10':float(np.mean(spread[ii]>1.10))})
    assert all(w.sha(ROOT/path)==v for path,v in plan['sources'].items())
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'exact_operator_transfer_diagnostic_complete',
        'source_safe_bases':full,'conditional_A1_2024':conditional,'future_five_member_stability':stability,'numeric_controls':checks,
        'new_model_fits':0,'new_C0_fits':0,'new_calibrations':0,'new_source_inference':0,'new_prediction_normalizers':105,
        'new_CSVs':0,'new_submissions':0,'submission_allowed':False,'not_full_F3c_validation':True,
        'main_PUL2_post31_failure_unchanged':True,'limits':plan['limits'],'2024_open':True,'B00_all_alternatives_preserved':True,
        'goal_achieved':False,'plan_sha256':w.sha(PLAN)}
    dump(OUT/'report.json',report)
    print(json.dumps({'bases':{n:{k:v[k] for k in ['delta','bootstrap95','simultaneous95_family','post31_delta','worst_single_group_removed_delta','same_level_sensitivities','direction_coherence']} for n,v in full.items()},
        'A1_2024':{k:conditional['A1'][k] for k in ['delta','bootstrap95','post31_delta','same_level_sensitivities']},
        'future_stability':stability,'new_fits':0,'submission_allowed':False},ensure_ascii=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['register','run']);a=p.parse_args()
    {'register':register,'run':run}[a.mode]()
