"""Escenarios de observación/valoración con curvas y estructura congeladas."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import bisect
import importlib.util
import json
import math
import os
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';HET=BASE/'enlace_HET_20261026_v1'
PUL=BASE/'forma_ultima_PUL_20261026_v1';HOME=BASE/'A1S_nucleo_20261026_v1'
OUT=BASE/'sensibilidad_observacion_PUL2_20261026_v1';PLAN=R/'registro/semana2_sensibilidad_observacion_PUL2_plan_v1.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


h=load('PUL2_stress_parent',R/'herramientas/contrastar_enlace_HET.py')
w=h.w;v=h.b.v;unit=h.b.unit
SCENARIOS=['R075_C','R125_C','R075_V','R125_V','TAIL005','TAIL010']


def dump(path,value):
    assert not path.exists();path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')


def targets_path():
    return ROOT/w.read(ROOT/'RUTAS_PROYECTO.json')['week_2_prepared_targets']


def register():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir()
    paths=[Path(__file__),Path(h.__file__),Path(v.__file__),PUL/'report.json',PUL/'oof_2023_2024.parquet',
        HET/'report.json',targets_path(),R/'src/semana2/preparar_base.py',
        R/'src/semana2/variables_ultimo.py',R/'herramientas/validar_mision017_fase2_tanda1.py']
    for line in h.LINES:
        paths.append(HOME/f'rows_s2_{line}.parquet')
        for held in range(5):
            paths += [HET/f'inputs_{line}_fold{held}.parquet',BASE/f'tanda2_20261025_v1/learning_{line}_fold{held}.json']
    plan={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'type':'fixed_structure_observation_valuation_sensitivity_only',
        'question':'Does the PUL2vsG3direction depend on assumed reserve valuation or a specified unseen reporting tail, keeping all fitted structures/rates and curves frozen?',
        'inputs':'Same109296held2023/2024rows. Use official preparedT0/T1reserve075/T1reserve125, saved scope C0perilCDFs/meanmarks/frequencies and sourcef*s risk profiles. No new claims or targetyears.',
        'scenarios':{'R075_C':'Y=T1reserve075; same ultimate aggregate rates, completion-only link with b=.75and analytically renormalized perilshares. Legacy sensitivity convention; not full revaluation.',
            'R125_C':'As above,b=1.25.',
            'R075_V':'Companion: same completion branch, plus per-peril training-only meanmark ratio revaluation. Frozen structure, no refit.',
            'R125_V':'As above,b=1.25.',
            'TAIL005':'Y=T0;5percent of cost mass beyond observed support in bodily_injury/subsidence only, exactly the prior design. Total ultimate rates held fixed.',
            'TAIL010':'As above,10percent.'},
        'formula':'For each scope/peril M_b=stored_meanmark_b/stored_meanmark1. Letw be fixed globalC0shares forG3 or sourcef*s shares per row forPUL2. R_b=sum(w*M_b); q_b=sum(w*M_b*q_peril_b)/R_b. Completion-onlyobservedmu=mu_base*(q_b/q_base). Revaluationcompanion additionally multipliesR_b. Tailchanges only designated q_peril to(1-tail)*q_peril, with w/M1fixed. Calendar exposure cancels in predictionratios and is never applied twice.',
        'why_two_reserve_modes':'A changed normalizedCDF is not the same as revaluing ultimate mark magnitude. Both conventions declared before readout; neither is full refit or evidence of adequate ultimate reserves.',
        'criterion':'Descriptive robustness: report all6point signs, groupCI,year/fold/cells andpost31. No winning-scenario choice, modeladoption, thresholdrelaxation or CSVchange.',
        'bootstrap':{'replicates':2000,'seed':2026102614,'unit':'same global connected components','joint6scenarios':True,
                     'intervals':'Marginal95and exploratoryBonferroni6; scenarios correlated, not independent evidence'},
        'controls':['C0fitgroup ancestry and exact rawtarget/cents alignment',
            'b1q_peril/global/source equals stored base within arithmetic tolerance, no new base statistical suite',
            'Independent directdaily scalar integration vs vector cumulativeCDF',
            'Midpoint identity M075*q075+M125*q125=2*q1, and weighted valuation symmetry',
            'Non-longtail/noreserve branches identities; no curvefit possible; all targets/predictions finite nonnegative/positive'],
        'budget':{'new_model_fits':0,'new_C0_fits':0,'new_calibration_fits':0,'new_source_inference':0,
            'new_scenario_observed_predictions':6*2*109296,'new_final_test_prices':0,'new_CSVs':0,'new_submissions':0},
        'limits':['PUL2post31failure remains; this does not approve a submission',
            'Risk-peril shares are a fixed proxy and ultimate reserve/tail truth is not identified',
            'Scenario responses and frozen-structure predictions are conditional, not a re-trained/revalued full pipeline',
            '2024adaptive research and repeated selection; no professional independent confirmation',
            'No complete historicF3creplay or nested futureensemblevalidation; weightedESSfailure persists'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'submission_allowed':False,'sources':{w.rel(p):w.sha(p) for p in paths}}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. Registro seis escenarios de observación/valoración para PUL2 frente a G3, sin ajustes nuevos. '
        'Reservas 75%/125% se miden con la convención de completitud anterior y, aparte, con revaloración analítica de marcas por peril. '
        'Se distinguen porque cambiar la CDF normalizada no equivale a cambiar la magnitud del coste. Las marcas/curvas/frecuencias ya están guardadas y excluyen el grupo retenido. '
        'Cola 5%/10% solo en lesión corporal y subsidencia, según la receta histórica, sin inventar siniestros tardíos o masa identificada fuera del soporte. '
        'Se conserva estructura y tasas; se reportarán todos los escenarios, intervalos por componentes, años/folds/celdas y concentración. No es revaloración completa con ajuste ni prueba de suficiencia de reservas. '
        'Cero curvas, modelos, inferencias fuente, precios finales o envíos. PUL2 mantiene el fallo post31; B00/F3c y alternativas intactos, 2024 abierto. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-PUL2-OBS-STRESS-PREVIO','--asunto','PUL2: escenarios de reservas y cola registrados, sin reentrenar',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(response.stdout)})
    print(json.dumps({'registered':True,'scenarios':SCENARIOS,'new_fits':0,'forum':json.loads(response.stdout)}))


def scalar_completion(start,end,model,branch):
    start=pd.Timestamp(start);end=pd.Timestamp(end);cut=pd.Timestamp('2024-12-31')
    low=(cut-end).days;high=(cut-start).days
    support=model['delay_days'];curve=model['cost_cdf'][str(branch)]
    result=[]
    for delay in range(low,high+1):
        j=bisect.bisect_right(support,delay)-1;result.append(0. if j<0 else curve[j])
    return math.fsum(result)/len(result)


def statistics(data,plan):
    first=data[SCENARIOS[0]];n=len(first['y'])
    codes,groups=pd.factorize(first['meta'].group_id,sort=True);G=len(groups)
    counts=np.bincount(codes,minlength=G)
    gs=[];ys=[];roots=[];nulls=[];gain_arrays={}
    for name in SCENARIOS:
        a=data[name];y=a['y'];gain=unit(y,a['G3'])-unit(y,a['PUL2']);gain_arrays[name]=gain
        gs.append(np.bincount(codes,weights=gain,minlength=G));ys.append(np.bincount(codes,weights=y,minlength=G))
        roots.append(np.bincount(codes,weights=np.sqrt(y),minlength=G))
        nulls.append(float(unit(y,np.full(n,y.mean())).sum()))
        assert abs(unit(y,a['PUL2']).mean()-mean_tweedie_deviance(y,a['PUL2'],power=1.5))<1e-8
    gains=np.column_stack(gs);Y=np.column_stack(ys);SQ=np.column_stack(roots)
    rng=np.random.default_rng(plan['bootstrap']['seed']);boot=[]
    for _ in range(2000):
        ix=rng.integers(0,G,G);nn=counts[ix].sum();den=8*(np.sqrt(nn*Y[ix].sum(axis=0))-SQ[ix].sum(axis=0))
        assert (den>0).all();boot.append(gains[ix].sum(axis=0)/den)
    boot=np.array(boot);np.save(OUT/'joint_scenario_bootstrap.npy',boot);results={}
    for j,name in enumerate(SCENARIOS):
        a=data[name];gain=gain_arrays[name];den=nulls[j];meta=a['meta'];gg=np.sort(gains[:,j])[::-1]
        cells=[]
        for (line,year,nb),ii in meta.groupby(['line','year','new_business']).groups.items():
            ii=np.asarray(list(ii));yy=a['y'][ii];dd=unit(yy,np.full(len(yy),yy.mean())).sum()
            cells.append({'line':line,'year':int(year),'NB':int(nb),'delta_global':float(gain[ii].sum()/den),'delta_cell_null':float(gain[ii].sum()/dd)})
        results[name]={'delta':float(gain.sum()/den),'bootstrap95':np.quantile(boot[:,j],[.025,.975]).tolist(),
            'simultaneous95_six':np.quantile(boot[:,j],[.025/6,1-.025/6]).tolist(),
            'scores':{model:float(1-unit(a['y'],a[model]).sum()/den) for model in ['G3','PUL2']},
            'post31_delta':float((gains[:,j].sum()-gg[:31].sum())/den),
            'folds':{str(k):float(gain[meta.fold.eq(k)].sum()/den) for k in range(5)},
            'years':{str(k):float(gain[meta.year.eq(k)].sum()/den) for k in [2023,2024]},'cells':cells}
    return results


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})
    p=pd.read_parquet(PUL/'oof_2023_2024.parquet');order=pd.Series(p.index.to_numpy(),index=p.row_id)
    raw=pd.read_parquet(targets_path(),columns=['row_id','year','is_test','T0','reserve','T0_cents','reserve_cents','T1_reserve075','T1_reserve125'])
    raw=raw.loc[~raw.is_test].set_index('row_id').loc[p.row_id]
    assert np.array_equal(p.T0,raw.T0) and np.array_equal(p.reserve,raw.reserve)
    assert np.array_equal(raw.T1_reserve075.to_numpy(),(4*raw.T0_cents-raw.reserve_cents).to_numpy(float)/400)
    assert np.array_equal(raw.T1_reserve125.to_numpy(),(4*raw.T0_cents+raw.reserve_cents).to_numpy(float)/400)
    data={name:{'meta':p[['row_id','line','year','new_business','fold','group_id']].copy(),
        'y':raw['T1_reserve075' if name.startswith('R075') else 'T1_reserve125' if name.startswith('R125') else 'T0'].to_numpy(float),
        'G3':np.full(len(p),np.nan),'PUL2':np.full(len(p),np.nan)} for name in SCENARIOS}
    metadata={line:pd.read_parquet(HOME/f'rows_s2_{line}.parquet',columns=['row_id','period_start','period_end','is_test','exposure_calendar']).set_index('row_id') for line in h.LINES}
    checks=[]
    def reject(*args,**kwargs):raise AssertionError('No reporting-curve fit during observation sensitivity')
    original=v.fit_reporting;v.fit_reporting=reject
    try:
        for line in h.LINES:
            for held in range(5):
                f=pd.read_parquet(HET/f'inputs_{line}_fold{held}.parquet')
                a=w.read(BASE/f'tanda2_20261025_v1/learning_{line}_fold{held}.json')['artifact']['C0']
                tr=f.fold.ne(held);assert sorted(f.loc[tr,'row_id'])==a['fit_row_ids'] and a['excluded_fold']==held
                assert not set(f.loc[tr,'group_id']).intersection(f.loc[~tr,'group_id'])
                valid=f.loc[~tr].copy();md=metadata[line].loc[valid.row_id]
                assert not md.is_test.any() and np.array_equal(md.exposure_calendar,valid.exposure)
                for field in ['period_start','period_end','is_test']:valid[field]=md[field].to_numpy()
                perils=list(a['curves']);risk=np.column_stack([valid['f_'+z].to_numpy()*valid['s_'+z].to_numpy() for z in perils])
                wr=risk/risk.sum(axis=1)[:,None];wg=np.array([a['mixture'][z] for z in perils])
                assert abs(wg.sum()-1)<1e-12
                q={};M={};scalarerror=0.
                for branch in [.75,1.,1.25]:
                    q[branch]=np.column_stack([v.average_completion(valid,a['curves'][z],'cost',branch) for z in perils])
                    M[branch]=np.array([a['curves'][z]['mean_net_mark'][str(branch)]/a['curves'][z]['mean_net_mark']['1.0'] for z in perils])
                    assert np.isfinite(M[branch]).all() and (M[branch]>0).all()
                    for j in np.unique(np.linspace(0,len(valid)-1,3,dtype=int)):
                        for k,z in enumerate(perils):
                            independent=scalar_completion(valid.period_start.iloc[j],valid.period_end.iloc[j],a['curves'][z],branch)
                            scalarerror=max(scalarerror,abs(independent-q[branch][j,k]));assert scalarerror<5e-12
                assert np.allclose(M[.75]*q[.75]+M[1.25]*q[1.25],2*q[1.],rtol=1e-11,atol=5e-12)
                qg1=q[1.]@wg;qr1=np.sum(wr*q[1.],axis=1)
                assert np.allclose(qg1,valid.e_cost_scope.to_numpy()/valid.exposure.to_numpy(),rtol=1e-12,atol=1e-13)
                assert np.allclose(qr1,valid.e_source_mix.to_numpy()/valid.exposure.to_numpy(),rtol=1e-12,atol=1e-13)
                assert (qg1>0).all() and (qr1>0).all()
                ii=order.loc[valid.row_id].to_numpy();baseg=p.loc[ii,'G3'].to_numpy();basep=p.loc[ii,'PUL2'].to_numpy()
                observed_frame=pd.DataFrame({'row_id':valid.row_id,'line':line,'fold':held})
                for branch,prefix in [(.75,'R075'),(1.25,'R125')]:
                    mg=float(np.dot(wg,M[branch]));mr=np.sum(wr*M[branch],axis=1)
                    valueg=q[branch]@(wg*M[branch]);valuer=np.sum(wr*M[branch]*q[branch],axis=1)
                    compg=valueg/mg;compr=valuer/mr
                    assert (compg>=0).all() and (compg<=1+1e-12).all() and (compr>=0).all() and (compr<=1+1e-12).all()
                    for suffix,gg,pp in [('C',compg,compr),('V',valueg,valuer)]:
                        name=prefix+'_'+suffix
                        data[name]['G3'][ii]=baseg*gg/qg1;data[name]['PUL2'][ii]=basep*pp/qr1
                        observed_frame[name+'_G3']=data[name]['G3'][ii];observed_frame[name+'_PUL2']=data[name]['PUL2'][ii]
                long=np.array([z in ['bodily_injury','subsidence'] for z in perils])
                for tail,name in [(.05,'TAIL005'),(.1,'TAIL010')]:
                    qt=q[1.]*(1-tail*long.astype(float));gtemp=qt@wg;rtemp=np.sum(wr*qt,axis=1)
                    if not long.any():assert np.array_equal(gtemp,qg1) and np.array_equal(rtemp,qr1)
                    data[name]['G3'][ii]=baseg*gtemp/qg1;data[name]['PUL2'][ii]=basep*rtemp/qr1
                    observed_frame[name+'_G3']=data[name]['G3'][ii];observed_frame[name+'_PUL2']=data[name]['PUL2'][ii]
                observed_frame.to_parquet(OUT/f'held_observation_{line}_fold{held}.parquet',index=False)
                checks.append({'line':line,'held':held,'group_ancestry_exact':True,'base_link_parity':True,
                    'max_direct_daily_integration_abs_error':scalarerror,'linear_reserve_valuation_midpoint':True,
                    'no_curvefit_called':True,'peril_zero_completion_allowed_without_floor':True})
    finally:v.fit_reporting=original
    for name,a in data.items():
        assert np.isfinite(a['y']).all() and (a['y']>=0).all()
        for model in ['G3','PUL2']:assert np.isfinite(a[model]).all() and (a[model]>0).all()
    with threadpool_limits(limits=2):results=statistics(data,plan)
    assert all(w.sha(ROOT/path)==v for path,v in plan['sources'].items())
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'fixed_structure_observation_sensitivity_complete',
        'results':results,'numeric_controls':checks,'all_scenario_point_deltas_nonnegative':all(r['delta']>=0 for r in results.values()),
        'all_scenario_lower95_positive':all(r['bootstrap95'][0]>0 for r in results.values()),
        'new_model_fits':0,'new_C0_fits':0,'new_calibration_fits':0,'new_source_inference':0,'new_final_test_prices':0,'new_submissions':0,
        'full_pipeline_refit_or_ultimate_adequacy_established':False,'post31_failure_not_removed':True,'submission_allowed':False,
        'limits':plan['limits'],'plan_sha256':w.sha(PLAN),'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(OUT/'report.json',report)
    print(json.dumps({'scenarios':{n:{k:r[k] for k in ['delta','bootstrap95','simultaneous95_six','post31_delta','years']} for n,r in results.items()},
        'all_points_nonnegative':report['all_scenario_point_deltas_nonnegative'],'new_fits':0,'submission_allowed':False},ensure_ascii=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['register','run']);a=p.parse_args()
    {'register':register,'run':run}[a.mode]()
