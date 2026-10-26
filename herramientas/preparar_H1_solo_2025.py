"""H1 sin forma REN: sensibilidad ya parametrizada y prototipo con cachés."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton'); R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2'
OUT=BASE/'H1_solo_prototipo_20261026_v1'
PLAN=R/'registro/semana2_H1_solo_prototipo_plan_v1.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader')); sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits


def load(name,path):
    sp=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


prod=load('H1_prototype_saved_producer',R/'herramientas/preparar_F3c_PUL2_2025.py')
stress=load('H1_reuse_scenario_contract',R/'herramientas/sensibilidad_observacion_PUL2_v2.py')
w=prod.w; io=prod.io; unit=stress.unit; SCENARIOS=stress.SCENARIOS
TRANSFER=BASE/'transferencia_H1_solo_20261026_v1'


def dump(path,value):
    with path.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)


def register():
    assert not OUT.exists() and not PLAN.exists(); OUT.mkdir()
    files=[Path(__file__),Path(prod.__file__),Path(stress.__file__),Path(prod.old.__file__),
           prod.PUL/'oof_2023_2024.parquet',prod.PUL/'report.json',TRANSFER/'report.json',
           stress.OUT/'report.json',stress.PLAN,stress.targets_path(),prod.OUT/'report.json',
           prod.OUT/'member_prices_2025.parquet',prod.old.PARENT,prod.old.COHORT,
           ROOT/'Hackaton/Repositorio_IAA2026/privado/semana2/envios/g4_20261025_v1/official_sample_format.csv']
    for line in prod.het.LINES:
        files.append(prod.OUT/f'component_forward_{line}.parquet')
        for held in range(5):files.append(stress.OUT/f'held_observation_{line}_fold{held}.parquet')
    plan={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
          'type':'H1_only_cached_scenario_reuse_and_2025_numeric_prototype',
          'motivation':'H1-only transfer is positive across S0/S1/S2 and remains positive after31favorablegroups, unlike full PUL2. Test the simpler observation correction, retain all adverse NB and concentration results.',
          'historical_formula':'Read exact saved six-scenario observed predictions and official stress targets. H1_scenario=H1_base*(PUL2_scenario/PUL2_base), because H1 and PUL2 differ only by frozen REN shape. Preserve NB scenario prices byte-identical because baseH1=basePUL2 there. No new CDF, integration or curve estimation.',
          'future_formula':'Five fixed own-scope members: actual F3c_i*cachedH1_ultimate_i/cachedG3_ultimate_i. Arithmetic mean of costs, no FSp shape, no learned weight/normalizer/level. Round to6decimals only at end.',
          'scenario_readout':'All6reserve/tailcases from prior contract, allC/Vconventions unchanged; pooledDelta/CIs/folds/years/cells/post31. Reuse old NB adverse cells by identity; do not rescore PUL2 or choose a favorable scenario.',
          'bootstrap':{'replicates':2000,'seed':2026102614,'unit':'same saved global group','joint6':True,'simultaneous':'exploratory Bonferroni6'},
          'criterion':'Numerical controls and honest diagnostic readout only. Existing formal minimum gain.002, post31, cell and other gates unchanged. No automatic upload or promotion; quota0not a local-work block.',
          'future_controls':['Official209063IDs/order/positive finite prices and exact sixdecimalformat',
                             'NB price identity with previous PUL2 CSV; REN totals same before rounding per member, but distribution differs',
                             'Independent log-domain formula, rational and Decimal rounding, readback',
                             'Source SHA unchanged; cached profile/member mapping by rowID,5members never treated as independent samples'],
          'budget':{'new_model_fits':0,'new_C0_fits':0,'new_calibration_fits':0,'new_source_inference':0,
                    'new_scenario_H1_observed_prices':6*109296,'new_primary_final_price_rows':209063,'new_prediction_normalizers':0,'new_CSVs':1,'new_submissions':0},
          'limits':['2024adaptive development and repeated search; exploratory conditional intervals',
                    'Full historic F3c replay and nested final5membervalidation still unavailable',
                    'A1original2024proxy not independent evidence; source/riskmix/vintage assumptions and weightedESSfailure persist',
                    'H1 and PUL2 share NB weaknesses; simplification does not erase reserve/tail adverse cases',
                    'PublicF3c0.16914retained; cannot infer a public gain or attainment of.17 from local delta'],
          '2024_open':True,'B00_all_alternatives_preserved':True,'submission_allowed':False,
          'sources':{w.rel(p):w.sha(p) for p in files}}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md'
    body.write_text('Codex. H1 sola mejoró las tres bases S0/S1/S2 entre+0,00105y+0,00117, con intervalos por grupos positivos y post31 entre+0,00049y+0,00060. '
                    'En S2, principal, diferencia+0,00104636 e IC95[+0,00061610,+0,00149156]; no supera el mínimo formal0,002. '
                    'El proxy A1original2024 mejora+0,00226989, pero su linaje no acredita confirmación independiente ni replay F3c. '
                    'Registro antes de nuevos precios los seis escenarios H1 usando los multiplicadores de observación ya guardados, sin repetir CDFs o controles terminados. '
                    'NB será idéntico a PUL2 y conserva sus deterioros bajo reservas/cola. Se preparará un prototipo2025 de cinco miembros F3c*H1/G3, sin forma REN, '
                    'con las cachés verificadas; su media es aritmética, sin pesos aprendidos o normalizadores nuevos. Se mantendrá el nivel REN de PUL2 por miembro. '
                    'Cero ajustes, inferencias fuente, C0 o envíos. La revisión no aprueba upload; falta replay F3c completo y validación anidada. B00/F3c y alternativas intactos;2024abierto. '
                    'Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    res=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
                        '--id','COD-S2-20261026-MISION017-H1-SOLO-PROTO-PREVIO',
                        '--asunto','H1 transfiere con menor concentración: escenarios y prototipo simple registrados',
                        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(res.stdout)})
    print(json.dumps({'registered':True,'new_fits':0,'forum':json.loads(res.stdout)}))


def scenario_statistics(meta,ys,baselines,corrected):
    n=len(meta);codes,groups=pd.factorize(meta.group_id,sort=True);G=len(groups)
    counts=np.bincount(codes,minlength=G); gains=[]; Ys=[]; SQs=[]; nulls=[]; rows=[]
    for j in range(6):
        y=ys[j]; gain=unit(y,baselines[j])-unit(y,corrected[j]); rows.append(gain)
        assert abs(unit(y,corrected[j]).mean()-mean_tweedie_deviance(y,corrected[j],power=1.5))<1e-8
        gains.append(np.bincount(codes,weights=gain,minlength=G))
        Ys.append(np.bincount(codes,weights=y,minlength=G)); SQs.append(np.bincount(codes,weights=np.sqrt(y),minlength=G))
        nulls.append(float(unit(y,np.full(n,y.mean())).sum()))
    gain=np.column_stack(gains); Y=np.column_stack(Ys); SQ=np.column_stack(SQs)
    rng=np.random.default_rng(2026102614); draws=[]
    for _ in range(2000):
        ix=rng.integers(0,G,G);nn=counts[ix].sum();den=8*(np.sqrt(nn*Y[ix].sum(axis=0))-SQ[ix].sum(axis=0))
        assert (den>0).all();draws.append(gain[ix].sum(axis=0)/den)
    draws=np.array(draws);np.save(OUT/'H1_scenario_bootstrap.npy',draws);result={}
    for j,name in enumerate(SCENARIOS):
        g=rows[j];den=nulls[j];cells=[]
        for (line,year,nb),ii in meta.groupby(['line','year','new_business']).groups.items():
            ii=np.asarray(list(ii));y=ys[j][ii];dd=unit(y,np.full(len(ii),y.mean())).sum()
            cells.append({'line':line,'year':int(year),'NB':int(nb),'delta_global':float(g[ii].sum()/den),'delta_cell_null':float(g[ii].sum()/dd)})
        result[name]={'delta':float(g.sum()/den),'bootstrap95':np.quantile(draws[:,j],[.025,.975]).tolist(),
                      'simultaneous95_six':np.quantile(draws[:,j],[.025/6,1-.025/6]).tolist(),
                      'post31_delta':float((gain[:,j].sum()-np.sort(gain[:,j])[::-1][:31].sum())/den),
                      'years':{str(k):float(g[meta.year.eq(k)].sum()/den) for k in [2023,2024]},
                      'folds':{str(k):float(g[meta.fold.eq(k)].sum()/den) for k in range(5)},'cells':cells}
    return result


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})
    p=pd.read_parquet(prod.PUL/'oof_2023_2024.parquet'); nb=p.new_business.eq(1).to_numpy()
    assert np.array_equal(p.H1.to_numpy()[nb],p.PUL2.to_numpy()[nb])
    raw=pd.read_parquet(stress.targets_path(),columns=['row_id','T0','T1_reserve075','T1_reserve125']).set_index('row_id').loc[p.row_id]
    scenario=pd.concat([pd.read_parquet(z) for z in stress.OUT.glob('held_observation_*.parquet')],ignore_index=True)
    assert len(scenario)==len(p) and scenario.row_id.is_unique
    scenario=scenario.set_index('row_id').loc[p.row_id]
    ys=[];oldprices=[];newprices=[]
    for name in SCENARIOS:
        y=raw['T1_reserve075' if name.startswith('R075') else 'T1_reserve125' if name.startswith('R125') else 'T0'].to_numpy(float)
        g=scenario[name+'_G3'].to_numpy(float);previous=scenario[name+'_PUL2'].to_numpy(float)
        pred=p.H1.to_numpy()*(previous/p.PUL2.to_numpy());pred[nb]=previous[nb]
        assert np.isfinite(pred).all() and (pred>0).all()
        ys.append(y);oldprices.append(g);newprices.append(pred)
    with threadpool_limits(limits=2): scenarios=scenario_statistics(p,ys,oldprices,newprices)
    previous_stress=w.read(stress.OUT/'report.json')['results']
    for name,row in scenarios.items():
        oldcells={(c['line'],c['year'],c['NB']):c for c in previous_stress[name]['cells']}
        for c in row['cells']:
            if c['NB']==1:assert c==oldcells[(c['line'],c['year'],1)]
    parent=pd.read_csv(prod.old.PARENT,dtype=str);parent_ticks=io.ticks(parent);base=parent_ticks/1e6
    cohort=pd.read_parquet(prod.old.COHORT).set_index('row_id').loc[parent.row_id]
    official=pd.read_csv(ROOT/'Hackaton/Repositorio_IAA2026/privado/semana2/envios/g4_20261025_v1/official_sample_format.csv',dtype=str)
    assert len(parent)==209063 and np.array_equal(parent.row_id,official.row_id)
    oldmembers=pd.read_parquet(prod.OUT/'member_prices_2025.parquet').set_index('row_id').loc[parent.row_id]
    members=np.full((len(parent),5),np.nan);checks=[]
    for line in prod.het.LINES:
        frame=pd.read_parquet(prod.OUT/f'component_forward_{line}.parquet').set_index('row_id')
        indices=np.flatnonzero(cohort.line.eq(line).to_numpy());ids=parent.row_id.iloc[indices]
        f=frame.loc[ids];ren=f.new_business.eq(0).to_numpy()
        for k in range(5):
            h=f[f'H1_{k}'].to_numpy();g=f[f'G3_{k}'].to_numpy();value=base[indices]*(h/g)
            assert np.array_equal(value[~ren],oldmembers[f'member{k}'].to_numpy()[indices][~ren])
            assert np.isclose(value[ren].sum(),oldmembers[f'member{k}'].to_numpy()[indices][ren].sum(),rtol=1e-12,atol=1e-6)
            for j in np.unique(np.linspace(0,len(f)-1,32,dtype=int)):
                scalar=math.exp(math.fsum([math.log(float(base[indices[j]])),math.log(float(h[j])),-math.log(float(g[j]))]))
                assert np.isclose(scalar,value[j],rtol=2e-14,atol=1e-9)
            members[indices,k]=value
        checks.append({'line':line,'cached_member_mapping_exact':True,'NB_matches_PUL2_members_exact':True,
                       'REN_unrounded_member_total_matches_PUL2':True,'independent_log_price_math':True})
    assert np.isfinite(members).all() and (members>0).all()
    mean=members.mean(axis=1);ticks=prod.rounding(mean)
    for i in np.unique(np.linspace(0,len(mean)-1,256,dtype=int)):
        with localcontext() as ctx:
            ctx.prec=100;expected=int((Decimal.from_float(float(mean[i]))*1000000).quantize(Decimal(1),rounding=ROUND_HALF_EVEN))
        assert expected==int(ticks[i])
    csvpath=OUT/'F3c_H1_solo_prototipo_2025.csv';io.write_csv(csvpath,parent.row_id,ticks)
    back=pd.read_csv(csvpath,dtype=str);assert np.array_equal(back.row_id,official.row_id) and np.array_equal(io.ticks(back),ticks)
    oldcsv=pd.read_csv(ROOT/w.read(prod.OUT/'report.json')['CSV']['path'],dtype=str);oldticks=io.ticks(oldcsv)
    assert np.array_equal(oldcsv.row_id,parent.row_id)
    future_nb=cohort.new_business.eq(1).to_numpy();assert np.array_equal(ticks[future_nb],oldticks[future_nb])
    pd.DataFrame({'row_id':parent.row_id,**{f'member{k}':members[:,k] for k in range(5)},'unrounded_mean':mean}).to_parquet(OUT/'member_prices_2025.parquet',index=False)
    cells=[]
    for (line,nbflag),ii in cohort.reset_index().groupby(['line','new_business']).groups.items():
        ii=np.asarray(list(ii));cells.append({'line':line,'NB':int(nbflag),'rows':len(ii),'total_CU':float(ticks[ii].sum()/1e6),
                                              'changed_vs_PUL2':int(np.count_nonzero(ticks[ii]!=oldticks[ii])),'changed_vs_F3c':int(np.count_nonzero(ticks[ii]!=parent_ticks[ii]))})
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'H1_only_sensitivity_and_numeric_prototype_complete',
            'scenarios':scenarios,'CSV':{'path':w.rel(csvpath),'sha256':w.sha(csvpath),'bytes':csvpath.stat().st_size,'rows':len(back),'total_CU':int(ticks.sum())/1e6},
            'cells':cells,'numeric_controls':checks,'NB_scenario_adverses_preserved_exact':True,'NB_future_PUL2_identity_exact':True,
            'new_model_fits':0,'new_C0_fits':0,'new_calibration_fits':0,'new_source_inference':0,'new_prediction_normalizers':0,'new_CSVs':1,'new_submissions':0,
            'submission_allowed':False,'submission_ready':False,'formal_promotion':False,'limits':plan['limits'],
            '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,'plan_sha256':w.sha(PLAN)}
    dump(OUT/'report.json',report)
    print(json.dumps({'CSV':report['CSV'],'scenarios':{n:{k:a[k] for k in ['delta','bootstrap95','post31_delta']} for n,a in scenarios.items()},
                      'cells':cells,'new_fits':0,'new_submissions':0},ensure_ascii=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['register','run']);a=p.parse_args();{'register':register,'run':run}[a.mode]()
