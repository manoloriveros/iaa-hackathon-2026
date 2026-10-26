"""P3a: precios de último fijos y escenarios observables, sin recalibración."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';P2=BASE/'media_anidada_H1_20261026_v3'
P1=BASE/'preflight_anidado_H1_20261026_v1';P0=BASE/'puente_ultimo_observado_H1_20261026_v1'
WEIGHTS=BASE/'estimando_cartera2025_v3'
OUT=BASE/'sensibilidad_congelada_media_H1_20261026_v1'
PLAN=R/'registro/semana2_sensibilidad_congelada_media_H1_plan_v1.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits


def load(name,path):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m


h=load('frozen_nested_H1_helpers',R/'herramientas/contrastar_enlace_HET.py');w=h.w;b=h.b;v=b.v
unit=h.d.unit
SCENARIOS=['RESERVE075','RESERVE125','TAIL005','TAIL010']
CLAIMS=b.BASE/'claim_assignment_audit.parquet'
TARGET=b.BASE/'target_T0_and_stresses.parquet'


def dump(path,value):
    with path.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)


def completion(f,c0,branch=1.,tail=0.):
    perils=sorted(c0['curves'])
    qq=np.column_stack([v.average_completion(f,c0['curves'][p],'cost',branch) for p in perils])
    if tail:
        qq*=1-tail*np.array([p in ['bodily_injury','subsidence'] for p in perils],float)
    # Under reserve valuation use the stored branch mean marks, while count
    # curves/frequencies stay exactly fixed. Tail is the prior fixed-mixture
    # cost-completion stress, without a claim of a joint count/severity model.
    levels=np.array([c0['frequency'][p]*c0['curves'][p]['mean_net_mark'][str(branch)] for p in perils])
    mix=levels/levels.sum()
    rr=np.column_stack([f['f_'+p].to_numpy(float)*f['s_'+p].to_numpy(float) for p in perils])
    assert np.isfinite(rr).all() and (rr>0).all()
    qg=qq@mix;qh=np.sum(rr*qq,axis=1)/rr.sum(axis=1)
    assert (qg>=0).all() and (qh>=0).all() and (qg<=1+1e-12).all() and (qh<=1+1e-12).all()
    return qg,qh


def verify_branch_math(c0,eligible):
    selected=eligible.loc[c0['fit_claim_ids']]
    assert set(selected.row_id).issubset(c0['fit_row_ids']) and len(selected)==len(c0['fit_claim_ids'])
    worst_mean=0.;worst_cdf=0.;checked=0
    for peril,model in c0['curves'].items():
        c=selected.loc[selected.peril.eq(peril)]
        delay=(pd.to_datetime(c.report_date)-pd.to_datetime(c.loss_date)).dt.days.to_numpy()
        support=np.asarray(model['delay_days']);buckets=np.searchsorted(support,delay)
        assert len(c)==model['n'] and np.array_equal(support[buckets],delay)
        assert np.array_equal(np.bincount(buckets,minlength=len(support)),np.asarray(model['events']))
        probability=np.asarray(model['count_mass'])[buckets]/np.asarray(model['events'])[buckets]
        assert abs(math.fsum(probability.tolist())-1)<1e-12
        for branch in [.75,1.25]:
            mark=(c.T0_cents.to_numpy(float)+(branch-1)*c.reserve_cents.to_numpy(float))/100
            assert np.isfinite(mark).all() and (mark>=0).all()
            weighted=probability*mark;mean=math.fsum(weighted.tolist())
            independent=np.cumsum(np.bincount(buckets,weights=weighted,minlength=len(support)))/mean
            expected=model['mean_net_mark'][str(branch)]
            error=abs(mean/expected-1);cdferror=float(np.max(np.abs(independent-np.asarray(model['cost_cdf'][str(branch)]))))
            worst_mean=max(worst_mean,error);worst_cdf=max(worst_cdf,cdferror)
            assert math.isclose(mean,expected,rel_tol=3e-12,abs_tol=1e-9) and cdferror<3e-12
            checked+=1
        assert math.isclose(model['mean_net_mark']['0.75']+model['mean_net_mark']['1.25'],2*model['mean_net_mark']['1.0'],rel_tol=3e-12)
    return {'branch_checks':checked,'max_mean_relative_error':worst_mean,'max_CDF_absolute_error':worst_cdf,
            'training_claim_keys_only':True,'new_curve_fits':0}


def register():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir()
    files=[Path(__file__),Path(h.__file__),Path(b.__file__),Path(v.__file__),CLAIMS,TARGET,
           P2/'report.json',P2/'held_nested_prices.parquet',P0/'report.json',WEIGHTS/'weights.parquet',WEIGHTS/'report.json',
           R/'registro/semana2_mision_privada_plan_v1.json',R/'registro/semana2_control_entregas_codex_actual.json']
    for line in h.LINES:
        files.append(P1/f'canonical_{line}.parquet')
        for outer in range(5):
            files += [P0/f'bridge_{line}_fold{outer}.parquet',BASE/f'tanda2_20261025_v1/learning_{line}_fold{outer}.json']
            for member in range(5):
                folder=P2/f'scope_{line}_outer{outer}_member{member}'
                files += [folder/'member_ultimate.parquet',folder/'primary/C0.json',folder/'committed.json']
    plan={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'type':'P3a_frozen_deliverable_sensitivity_before_any_scenario_recalibration',
          'question':'Does the already-fitted full five-member correction retain its advantage if reserve valuation or cost-completion assumptions differ, without letting it adapt after the fact?',
          'fixed':'All current member prices, source models, target calibration parameters, weights and partitions. No new final2025predictions or CSV changes.',
          'prices':'Recover U_B from protected P0S2ultimate and U_C as the exact P2arithmetic mean of five base*H1ultimate/G3ultimate members. U_B/U_C never change between scenarios. Observedscenario prices=U_B*qGscenario and U_C*qHscenario; no observed-stage renormalization or meanmark multiplier to alter ultimate forecasts.',
          'scenarios':{'RESERVE075':'Official Y=T0-.25reserve. CostCDF/meanmark at storedb=.75, same countCDF/frequency; recompute globalperilweights as frequency*meanmark_b normalized. H1sourcef*sprofile fixed.',
                       'RESERVE125':'Same with Y=T0+.25reserve and b=1.25.',
                       'TAIL005':'Y=T0, oldglobalperilweights and sourceprofilefixed; costcompletion multiplied.95 only for BI/subsidence, no countcurvechange or fabricated lateclaim.',
                       'TAIL010':'Same with.90.'},
          'algebraic_reuse':'Reverse-count distribution and claim event probabilities do not depend on marks. For probability_i=countmass[delay_i]/events[delay_i], meanmark_b=sum(probability_i*mark_bi) and costCDF_b(d)=sum_delay<=d(probability_i*mark_bi)/meanmark_b. Verify independently for15outer+75memberC0objects. No new curve fit needed.',
          'distinctions':['This is robustness of fixed actual ultimate forecasts under scenario observation/labels, not their ability to recalibrate',
                          'Full target-valuation recalibration would need new closed N3/A1S/S2outerbase and G3/H1inner learning under changed train labels/exposure; saved C0branches alone do not reproduce those new learned parameters',
                          'No full source/model revaluation or coherent identified joint count/severity tail model is asserted'],
          'readout':'All4paired aggregate differences/CIs, year/fold/line/NBcells,A/E,post31and worstgroup. Full baseline and candidate levels. No favorable scenario selection or target/row trimming.',
          'bootstrap':{'replicates':2000,'seed':2026102621,'unit':'same global customer/address component','joint4':True,'family_interval':'exploratory Bonferroni4'},
          'weighted2025_sensitivity':'Use existing frozenweights and prior ESSreceipt only; report weightedpoint per scenario, no new classifier, weights, bootstrap or validation approval. ESSrow2.67percent/group4.32percent remains failed.',
          'controls':['Exact official period target/claim cents reconciliation including reservebranches',
                      'Reconstruct nominal P2prices by key without repeating its statistical assay',
                      'Independent event-probability mark/CDF arithmetic and reserve linearity over all90C0objects',
                      'Peril completion zeros allowed, aggregate observed predictions must remain positive; no floors',
                      'Response-poisoned held covariates must not change scenario completion; learning forbidden',
                      'Independent Tweedie metric and weighted metric, source hashes unchanged'],
          'criterion':'Diagnostic robustness only: report adverse cases and losses beyond.001 by line/year/NB; no threshold change or automatic admission. Current formal gain.002 failure and private/model lineage limits remain.',
          'budget':{'new_model_fits':0,'new_C0_fits':0,'new_calibration_fits':0,'new_source_inference':0,
                    'new_scenario_observed_price_rows':4*2*109296,'new_final_test_prices':0,'new_submissions':0},
          'limits':['Adaptive2023/2024and proxyS2not full deliveredF3creplay','P2nested training64percent versus80percent in production',
                    'Riskmix/ultimate/latecost assumptions not identified; no hidden private improvement established',
                    'Severe weighted support failure retained; weighted point cannot rescue any failed unweighted diagnostic',
                    'Fixed predictions cannot show performance of a newly recalibrated valuation-basis algorithm'],
          '2024_open':True,'B00_all_alternatives_preserved':True,'submission_allowed':False,
          'sources':{w.rel(p):w.sha(p) for p in files}}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md'
    body.write_text('Codex. Registro P3a antes de nuevos scores: cuatro escenarios para el promedio completo, manteniendo fijos sus precios de último. '
                    'Reservas75/125usan etiquetas oficiales y ramas de C0guardadas con mezcla global coherente con sus marcas; cola5/10es la convención previa de completitud de coste solo enBI/subsidencia, sin inventar siniestros. '
                    'La media de cinco miembros, base y parámetros no se recalibran. Primero se verificará por probabilidades de eventos la equivalencia de las ramas en90objetos C0y la conciliación de céntimos. '
                    'Se reportarán todas las celdas, concentración, intervalos conjuntos y nivel; los pesos2025solo darán puntos de sensibilidad con su ESSinsuficiente vigente. '
                    'Esto mide robustez del precio actual; una recalibración bajo otra valoración requeriría otros parámetros y no se finge con las ramas de C0. '
                    'Cero ajustes, C0, inferencias fuente, precios2025oenvíos. B00/alternativas conservados,2024abierto adaptativo y privada prioritaria. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    res=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
                        '--id','COD-S2-20261026-PRIVADA-P3A-CONGELADO-PREVIO',
                        '--asunto','P3a privado: sensibilidad del precio congelado, sin confundirla con recalibración',
                        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(res.stdout)})
    print(json.dumps({'registered':True,'new_fits':0,'forum':json.loads(res.stdout)}))


def summarize(meta,ys,base,candidate,weight):
    codes,groups=pd.factorize(meta.group_id,sort=True);G=len(groups);n=len(meta)
    count=np.bincount(codes,minlength=G);gains=[];Y=[];SQ=[];den=[];rowg=[]
    for j in range(4):
        y=ys[j];gain=unit(y,base[j])-unit(y,candidate[j]);rowg.append(gain)
        assert abs(unit(y,candidate[j]).mean()-mean_tweedie_deviance(y,candidate[j],power=1.5))<1e-8
        gains.append(np.bincount(codes,weights=gain,minlength=G));Y.append(np.bincount(codes,weights=y,minlength=G));SQ.append(np.bincount(codes,weights=np.sqrt(y),minlength=G))
        den.append(float(unit(y,np.full(n,y.mean())).sum()))
    gain=np.column_stack(gains);YY=np.column_stack(Y);QQ=np.column_stack(SQ)
    rng=np.random.default_rng(2026102621);draws=[]
    for _ in range(2000):
        ix=rng.integers(0,G,G);nn=count[ix].sum();dd=8*(np.sqrt(nn*YY[ix].sum(axis=0))-QQ[ix].sum(axis=0))
        assert (dd>0).all();draws.append(gain[ix].sum(axis=0)/dd)
    draws=np.asarray(draws);np.save(OUT/'scenario_bootstrap.npy',draws);result={}
    for j,name in enumerate(SCENARIOS):
        y=ys[j];gg=rowg[j];cells=[]
        for (line,year,nb),ii in meta.groupby(['line','year','new_business']).groups.items():
            ii=np.asarray(list(ii));yy=y[ii];dd=unit(yy,np.full(len(ii),yy.mean())).sum()
            cells.append({'line':line,'year':int(year),'NB':int(nb),'rows':len(ii),'delta_global':float(gg[ii].sum()/den[j]),
                          'delta_cell_null':float(gg[ii].sum()/dd),'AE_base':float(yy.sum()/base[j][ii].sum()),'AE_candidate':float(yy.sum()/candidate[j][ii].sum())})
        wm=float(np.average(y,weights=weight));wd=float(np.sum(weight*unit(y,np.full(n,wm))))
        wpoint=float(np.sum(weight*gg)/wd)
        assert abs(np.average(unit(y,candidate[j]),weights=weight)-mean_tweedie_deviance(y,candidate[j],power=1.5,sample_weight=weight))<1e-8
        result[name]={'delta':float(gg.sum()/den[j]),'bootstrap95':np.quantile(draws[:,j],[.025,.975]).tolist(),
                      'simultaneous95_four':np.quantile(draws[:,j],[.025/4,1-.025/4]).tolist(),
                      'post31_delta':float((gain[:,j].sum()-np.sort(gain[:,j])[::-1][:31].sum())/den[j]),
                      'worst_single_removed_delta':float((gain[:,j].sum()-gain[:,j].max())/den[j]),
                      'years':{str(k):float(gg[meta.year.eq(k)].sum()/den[j]) for k in [2023,2024]},
                      'folds':{str(k):float(gg[meta.fold.eq(k)].sum()/den[j]) for k in range(5)},'cells':cells,
                      'worst_cell_delta':min(c['delta_cell_null'] for c in cells),'weighted2025_point_only_ESS_failed':wpoint,
                      'AE_base':float(y.sum()/base[j].sum()),'AE_candidate':float(y.sum()/candidate[j].sum()),
                      'scores':{'base':float(1-unit(y,base[j]).sum()/den[j]),'candidate':float(1-unit(y,candidate[j]).sum()/den[j])}}
    return result


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})
    p=pd.read_parquet(P2/'held_nested_prices.parquet');ix=pd.Series(p.index.to_numpy(),index=p.row_id)
    raw=pd.read_parquet(TARGET,columns=['row_id','T0','T0_cents','reserve_cents','T1_reserve075','T1_reserve125']).set_index('row_id').loc[p.row_id]
    claims=pd.read_parquet(CLAIMS);allocated=claims.loc[claims.included_in_T0].copy();assert allocated.claim_id.is_unique
    grouped=allocated.groupby('row_id')[['T0_cents','reserve_cents']].sum().reindex(p.row_id,fill_value=0)
    assert np.array_equal(grouped.T0_cents,raw.T0_cents) and np.array_equal(grouped.reserve_cents,raw.reserve_cents)
    assert np.array_equal(p.T0,raw.T0)
    assert np.array_equal(raw.T1_reserve075.to_numpy(float),(4*raw.T0_cents-raw.reserve_cents).to_numpy(float)/400)
    assert np.array_equal(raw.T1_reserve125.to_numpy(float),(4*raw.T0_cents+raw.reserve_cents).to_numpy(float)/400)
    eligible=allocated.set_index('claim_id');curve_checks=[]
    def reject(*args,**kwargs):raise AssertionError('No learning during frozen sensitivity')
    blocked=[(v,'fit_reporting'),(h,'learn'),(b,'reporting_scope'),(b,'shape_fit'),(b,'factor'),(b,'cell_levels'),(h.g,'fit_stage')]
    originals=[(m,k,getattr(m,k)) for m,k in blocked]
    for m,k,_ in originals:setattr(m,k,reject)
    base=[np.full(len(p),np.nan) for _ in SCENARIOS];candidate=[np.full(len(p),np.nan) for _ in SCENARIOS]
    try:
        for line in h.LINES:
            canonical=pd.read_parquet(P1/f'canonical_{line}.parquet').set_index('row_id')
            for outer in range(5):
                bridge=pd.read_parquet(P0/f'bridge_{line}_fold{outer}.parquet');f=canonical.loc[bridge.row_id].reset_index()
                ii=ix.loc[bridge.row_id].to_numpy();c0=w.read(BASE/f'tanda2_20261025_v1/learning_{line}_fold{outer}.json')['artifact']['C0']
                assert not set(c0['fit_row_ids']).intersection(f.row_id)
                curve_checks.append({'line':line,'outer':outer,'role':'outer',**verify_branch_math(c0,eligible)})
                rr=[]
                for member in range(5):
                    folder=P2/f'scope_{line}_outer{outer}_member{member}'
                    record=pd.read_parquet(folder/'member_ultimate.parquet').set_index('row_id').loc[bridge.row_id]
                    rr.append(record.ratio.to_numpy());memberC0=w.read(folder/'primary/C0.json')
                    assert not set(memberC0['fit_row_ids']).intersection(f.row_id)
                    curve_checks.append({'line':line,'outer':outer,'member':member,'role':'inner',**verify_branch_math(memberC0,eligible)})
                UB=bridge.U_S2.to_numpy();UC=(UB[:,None]*np.column_stack(rr)).mean(axis=1)
                qg,qh=completion(f,c0)
                assert np.allclose(qg,bridge.q_global,rtol=2e-12,atol=1e-13) and np.allclose(qh,bridge.q_source,rtol=2e-12,atol=1e-13)
                assert np.allclose(UB*qg,p.loc[ii,'B'],rtol=2e-12,atol=1e-9) and np.allclose(UC*qh,p.loc[ii,'T_B'],rtol=2e-12,atol=1e-9)
                for j,name in enumerate(SCENARIOS):
                    branch=.75 if name=='RESERVE075' else 1.25 if name=='RESERVE125' else 1.
                    tail=.05 if name=='TAIL005' else .1 if name=='TAIL010' else 0.
                    qg,qh=completion(f,c0,branch,tail)
                    poisoned=f.copy();poisoned[['T0','reserve']]=-1e30
                    pg,ph=completion(poisoned,c0,branch,tail)
                    assert np.array_equal(qg,pg) and np.array_equal(qh,ph)
                    base[j][ii]=UB*qg;candidate[j][ii]=UC*qh
    finally:
        for m,k,original in originals:setattr(m,k,original)
    for arr in base+candidate:assert np.isfinite(arr).all() and (arr>0).all(),'Unsupported zero aggregate scenario price; do not floor or drop rows'
    ys=[raw.T1_reserve075.to_numpy(float),raw.T1_reserve125.to_numpy(float),p.T0.to_numpy(float),p.T0.to_numpy(float)]
    weighted=pd.read_parquet(WEIGHTS/'weights.parquet').set_index('row_id').loc[p.row_id]
    for col in ['group_id','fold','line','year','new_business']:assert np.array_equal(weighted[col],p[col])
    weights=weighted.weight.to_numpy(float);assert np.isfinite(weights).all() and (weights>0).all()
    with threadpool_limits(limits=2):results=summarize(p,ys,base,candidate,weights)
    prices=p[['row_id','line','year','new_business','group_id','fold']].copy()
    for j,name in enumerate(SCENARIOS):prices[name+'_B']=base[j];prices[name+'_C']=candidate[j]
    prices.to_parquet(OUT/'held_frozen_scenario_prices.parquet',index=False)
    assert len(curve_checks)==90 and sum(c['branch_checks'] for c in curve_checks)==900
    assert all(w.sha(ROOT/path)==v for path,v in plan['sources'].items())
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'P3a_frozen_nested_algorithm_sensitivity_complete',
            'results':results,'algebra_controls':curve_checks,'target_claim_cents_and_stress_exact':True,
            'nominal_nested_prices_reconstructed_without_rescoring':True,'ultimate_forecasts_unchanged_all_scenarios':True,
            'weighted_support_receipt_reused':w.read(WEIGHTS/'report.json'),
            'new_model_fits':0,'new_C0_fits':0,'new_calibration_fits':0,'new_source_inference':0,'new_final_test_prices':0,'new_submissions':0,
            'target_valuation_recalibration_performed':False,'source_full_revaluation_performed':False,
            'submission_allowed':False,'formal_promotion':False,'private_improvement_established':False,
            'limits':plan['limits'],'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,'plan_sha256':w.sha(PLAN)}
    dump(OUT/'report.json',report)
    print(json.dumps({'scenarios':{n:{k:a[k] for k in ['delta','bootstrap95','simultaneous95_four','post31_delta','worst_cell_delta','weighted2025_point_only_ESS_failed']} for n,a in results.items()},
                      'branch_math_checks':900,'new_fits':0,'new_submissions':0},ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['register','run']);args=parser.parse_args();{'register':register,'run':run}[args.mode]()
