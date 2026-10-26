"""Puente de producción a observado, con objetos exteriores guardados y sin fit."""
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
BASE=R/'privado/semana2/mision017_fase2';HOME=BASE/'A1S_nucleo_20261026_v1'
SBASE=HOME/'target_complete_core';HET=BASE/'enlace_HET_20261026_v1'
PUL=BASE/'forma_ultima_PUL_20261026_v1'
OUT=BASE/'puente_ultimo_observado_H1_20261026_v1'
PLAN=R/'registro/semana2_puente_ultimo_observado_H1_plan_v1.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits


def load(name,path):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m


prod=load('H1_bridge_production',R/'herramientas/preparar_F3c_PUL2_2025.py')
complete=load('H1_bridge_complete_core',R/'herramientas/validar_nucleo_completo_A1S.py')
stats=load('H1_bridge_statistics',R/'herramientas/auditar_transferencia_PUL2.py')
w=prod.w;h=prod.het;b=h.b;g=h.g


def dump(path,value):
    with path.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)


def norm_product(f,ultimate,observed):
    assert set(ultimate)==set(observed)
    keys=[f'{int(year)}|{int(nb)}' for year,nb in zip(f.year,f.new_business)]
    value=np.ones(len(f))
    for variable in ultimate:
        assert set(ultimate[variable])==set(observed[variable])
        value*=np.array([ultimate[variable][k]/observed[variable][k] for k in keys])
    return value


def ultimate_forward(f,sf,n3,h1,gs,sa):
    gu,ng=prod.G3_future(f,n3,gs)
    hu,nh=h.replay(f,h1,ultimate=True)
    # S2 has a complete feasible source-safe base, distinct from actual F3c.
    s=sf.copy();s['exposure']=f.exposure.to_numpy();s['e_cost_scope']=f.exposure.to_numpy()
    s['base_N3']=prod.G3_future(f,n3,[])[0]
    result,ns=complete.replay(s,sa)
    return {'G3':gu,'H1':hu,'S2':result['S2']},{'G3':ng,'H1':nh,'S2':ns}


def synthetic():
    # An outcome-free counterexample and limiting identities for the bridge.
    n=80;f=pd.DataFrame({'year':2024,'new_business':np.arange(n)%2,
                        'gender':np.where(np.arange(n)%4<2,'F','M')})
    annual=np.linspace(50,250,n);exposure=np.linspace(.2,1,n)
    q=np.where(f.gender.eq('F'),.4,.95)
    stage={'variable':'gender','factors':{'F':.7,'M':1.3}}
    ult,nu=g.apply_stage(f,annual*exposure,stage)
    obs,no=g.apply_stage(f,annual*exposure*q,stage)
    L=norm_product(f,{'gender':nu},{'gender':no})
    assert np.allclose(obs,ult*q*L,rtol=2e-15,atol=1e-12)
    naive_error=float(np.max(np.abs(obs/(ult*q)-1)))
    assert naive_error>.01
    flat,nflat=g.apply_stage(f,annual*exposure*.6,stage)
    assert np.allclose(flat,ult*.6,rtol=2e-15,atol=1e-12)
    assert all(abs(nflat[k]/nu[k]-1)<1e-14 for k in nu)
    full,nfull=g.apply_stage(f,annual*exposure,stage)
    assert np.array_equal(full,ult) and nfull==nu
    return {'normalizer_bridge_identity':True,'naive_q_multiplication_counterexample_relative_error':naive_error,
            'within_cell_constant_completion_identity':True,'q1_ultimate_identity_exact':True,
            'synthetic_fits':0,'no_response_used':True}


def register():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir()
    files=[Path(__file__),Path(prod.__file__),Path(complete.__file__),Path(h.__file__),Path(b.__file__),Path(g.__file__),Path(stats.__file__),
           R/'registro/semana2_mision_privada_plan_v1.json',R/'registro/semana2_control_entregas_codex_actual.json',
           PUL/'oof_2023_2024.parquet',PUL/'report.json',SBASE/'oof_2023_2024.parquet',SBASE/'report.json',
           BASE/'transferencia_H1_solo_20261026_v1/report.json']
    for line in h.LINES:
        files.append(HOME/f'rows_s2_{line}.parquet')
        for k in range(5):
            files += [HET/f'inputs_{line}_fold{k}.parquet',HET/f'learning_H1_{line}_fold{k}.json',
                      SBASE/f'inputs_{line}_fold{k}.parquet',SBASE/f'learning_{line}_fold{k}.json',
                      BASE/f'tanda2_20261025_v1/learning_{line}_fold{k}.json']
            if line!='buildings':files.append(BASE/f'tanda10_factores_20261026_v1/learning_{line}_fold{k}.json')
    plan={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'type':'production_ultimate_to_observed_bridge_before_nested_learning',
          'question':'Do cached observed-fold H1/G3 corrections represent the actual ultimate-forward production transformation after exposure-dependent prediction normalizers?',
          'mathematics':'For each fixed model m and cell(year,NB), O_m/U_m=(Erounded/Ecalendar)*q_m*L_m, where L_m=product_j(N_mj_ultimate/N_mj_observed). Thus O_H/O_G=(U_H/U_G)*(q_H/q_G)*(L_H/L_G). No fitted factor or training normalizer changes.',
          'primary_base':'Complete source-safe S2 fixed outer artifact, forwarded with calendar exposure and cached source annual relativity. This is a feasible complete base, not actual F3c.',
          'primary_prices':'Baseline observed proxy B=U_S2*q_global. Correction C=U_S2*(U_H1/U_G3)*q_source. Ultimate components use production calendar once and stage normalizers computed on ultimate held prices. Common outer curves were fitted without outer held groups. No posthoc observed-stage renormalization.',
          'why_common_outer_link':'Observation adapter for evaluation uses the same protected outer C0 curves, with global/source profile hypotheses as declared. It is not an inner-independent learner or true identified ultimate mix.',
          'scope':'Same109296held2023/2024rows, saved five outer global components; one fixed saved member per outer scope. This stage is a bridge preflight, not a five-member nested validation.',
          'source_safe_ancestry':'Verify exact row/group membership of saved target artifacts and C0; no new source inference or learned weights.',
          'controls':['Synthetic nonuniformqcounterexample; constantwithin-cellqandq1identities',
                      'Independent reconstruction U=O/((Erounded/Ecalendar)*q*L) from cached prices forG3,H1,S2',
                      'Real ultimate forward with every learning function blocked and held outcome poisoning',
                      'No response, reserve or claim enters source risk ratios or prediction-only normalizers',
                      'Pinned source SHA remain unchanged; legitimate zero per-perilq is not floored'],
          'readout':'All normalizer and price ratios by line/year/NB; pooled paired-group delta, years/folds/cells, post31, worstgroup and fixed±5percentlevels. Reuse old H1transfer report by reference only; no rescoring old comparison.',
          'criterion':{'purpose':'Private-generalization evidence and exact flow correctness; no promotion/upload from this assay',
                       'retained_diagnostic_delta_min':.002,'lower95_gt':0,'at_least4positive_folds':True,
                       'both_years_nonnegative':True,'post31_nonnegative':True,'worst_cell_floor':-.001,
                       'no_threshold_change':True},
          'bootstrap':{'replicates':2000,'seed':2026102619,'unit':'existing global components','single_primary_contrast':'CvsB'},
          'level_sensitivity':[.95,1.,1.05],
          'budget':{'new_model_fits':0,'new_C0_fits':0,'new_calibration_fits':0,'new_source_inference':0,
                    'new_held_ultimate_component_prices':3*109296,'new_held_primary_observed_prices':2*109296,
                    'primary_prediction_normalizers':240,'held_poison_prediction_normalizers_separate':240,
                    'new_final_test_prices':0,'new_submissions':0},
          'limits':['2024adaptive development; all outcomes already informed hypotheses, so no pristine or independent confirmation',
                    'Single saved member per outer fold; actual five-member mean still requires nested evaluation',
                    'Complete S2proxy does not reconstruct deliveredF3c; source2024snapshot and undated masters conditional',
                    'Ultimate truth, reserves, late tail and source-riskmix not identified; weightedESS failure retained',
                    'Public score secondary; private improvement unknown; H1delivery remains deferred'],
          '2024_open':True,'B00_all_alternatives_preserved':True,'submission_allowed':False,
          'sources':{w.rel(p):w.sha(p) for p in files}}
    dump(PLAN,plan);dump(OUT/'synthetic.json',synthetic())
    body=OUT/'forum_previo.md'
    body.write_text('Codex. Registro P0 de la prioridad privada antes de nuevos precios/puntuaciones: puente exacto entre último y observado. '
                    'Los normalizadores de factores por cartera cambian con la exposición. La identidad incluye q y el producto Núltimo/Nobservado; '
                    'el cociente H1/G3 observado no se identifica automáticamente con el cociente de producción último. '
                    'Se usará la base completa reproducible S2 y los objetos guardados de cada ámbito externo, con calendario a precisión completa para último. '
                    'Se evaluará S2último*qglobal frente a S2último*(H1último/G3último)*qporriesgo, sin renormalizar después en observado. '
                    'Los adaptadores exteriores excluyen los grupos evaluados; se reportarán incertidumbre, concentración, celdas y niveles sin escoger un ajuste. '
                    'Cero ajustes, C0, inferencias fuente, CSV finales o envíos. La prueba sintética demuestra cuándo el producto por q basta y cuándo falta el factor de normalización. '
                    'Una única instancia guardada por fold aún no es el promedio anidado de cinco modelos y S2 no es el F3c real. '
                    'H1 sigue diferido; B00 y alternativas preservados,2024abierto adaptativo. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    res=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
                        '--id','COD-S2-20261026-PRIVADA-PUENTE-H1-PREVIO',
                        '--asunto','P0 privado: puente último-observado registrado antes de evaluar el algoritmo de producción',
                        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(res.stdout)})
    print(json.dumps({'registered':True,'synthetic':w.read(OUT/'synthetic.json'),'forum':json.loads(res.stdout)}))


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})
    p=pd.read_parquet(PUL/'oof_2023_2024.parquet')
    sb=pd.read_parquet(SBASE/'oof_2023_2024.parquet').set_index('row_id').loc[p.row_id]
    for c in ['T0','year','fold','group_id','new_business']:assert np.array_equal(p[c],sb[c])
    p['S2_cached_observed']=sb.S2.to_numpy();p['B']=np.nan;p['T_B']=np.nan
    position=pd.Series(p.index.to_numpy(),index=p.row_id);controls=[];cells=[]
    def reject(*args,**kwargs):raise AssertionError('Learning is forbidden during saved production bridge')
    blocked=[(h,'learn'),(b,'shape_fit'),(b,'cell_levels'),(b,'factor'),(b,'reporting_scope'),
             (g,'fit_stage'),(complete,'fit_component'),(complete,'learn'),(b.v,'fit_reporting')]
    saved=[(m,n,getattr(m,n)) for m,n in blocked]
    for m,n,_ in saved:setattr(m,n,reject)
    try:
        for line in h.LINES:
            md=pd.read_parquet(HOME/f'rows_s2_{line}.parquet').set_index('row_id')
            for held in range(5):
                full=pd.read_parquet(HET/f'inputs_{line}_fold{held}.parquet');f=full.loc[full.fold.eq(held)].copy().reset_index(drop=True)
                sf=pd.read_parquet(SBASE/f'inputs_{line}_fold{held}.parquet').set_index('row_id').loc[f.row_id].reset_index()
                ii=position.loc[f.row_id].to_numpy();n3=w.read(BASE/f'tanda2_20261025_v1/learning_{line}_fold{held}.json')['artifact']
                ha=w.read(HET/f'learning_H1_{line}_fold{held}.json');sa=w.read(SBASE/f'learning_{line}_fold{held}.json')
                gr={'stages':[],'held_normalizers':{}} if line=='buildings' else w.read(BASE/f'tanda10_factores_20261026_v1/learning_{line}_fold{held}.json')
                train=full.fold.ne(held)
                assert sorted(full.loc[train,'row_id'])==n3['C0']['fit_row_ids']
                assert not set(full.loc[train,'group_id']).intersection(f.group_id)
                for record in [ha,sa]:
                    key='training_row_ids_digest' if record is ha else 'fit_row_ids_digest'
                    assert record[key]==b.digest(sorted(full.loc[train,'row_id']))
                for c in ['row_id','T0','fold','group_id','year','new_business']:assert np.array_equal(f[c],sf[c])
                E=md.loc[f.row_id,'exposure_calendar'].to_numpy(float);Er=f.exposure.to_numpy(float)
                assert np.array_equal(md.loc[f.row_id,'exposure_model'],Er) and np.array_equal(np.round(E,4),Er)
                qg=f.e_cost_scope.to_numpy()/Er;qh=f.e_source_mix.to_numpy()/Er
                assert (qg>0).all() and (qh>0).all()
                u=f.copy();u['exposure']=E
                values,norms=ultimate_forward(u,sf,n3,ha,gr['stages'],sa)
                obs={'G3':p.loc[ii,'G3'].to_numpy(),'H1':p.loc[ii,'H1'].to_numpy(),'S2':p.loc[ii,'S2_cached_observed'].to_numpy()}
                obs_norm={'G3':gr['held_normalizers'],'H1':ha['held_normalizers'],'S2':sa['held_normalizers']}
                L={name:norm_product(f,norms[name],obs_norm[name]) for name in values}
                maxerror={}
                for name in values:
                    q=qh if name=='H1' else qg
                    reconstructed=obs[name]/((Er/E)*q*L[name])
                    maxerror[name]=float(np.max(np.abs(values[name]/reconstructed-1)))
                    assert np.allclose(values[name],reconstructed,rtol=3e-12,atol=1e-9)
                poisoned=u.copy();poisoned[['T0','reserve']]=-1e30
                poisoned_s=sf.copy();poisoned_s[['T0','reserve']]=1e30
                replay,other_norm=ultimate_forward(poisoned,poisoned_s,n3,ha,gr['stages'],sa)
                assert norms==other_norm and all(np.array_equal(values[k],replay[k]) for k in values)
                reference=values['S2']*qg;candidate=values['S2']*(values['H1']/values['G3'])*qh
                assert np.isfinite(reference).all() and np.isfinite(candidate).all() and (reference>0).all() and (candidate>0).all()
                p.loc[ii,'B']=reference;p.loc[ii,'T_B']=candidate
                record=f[['row_id','line','year','new_business','fold','group_id']].copy()
                for name in values:record['U_'+name]=values[name];record['L_'+name]=L[name]
                record['q_global']=qg;record['q_source']=qh
                record['old_observed_ratio_H1_G3']=obs['H1']/obs['G3']
                record['production_bridge_ratio']=(values['H1']/values['G3'])*(qh/qg)
                record['normalizer_ratio']=L['H1']/L['G3']
                assert np.allclose(record.old_observed_ratio_H1_G3,record.production_bridge_ratio*record.normalizer_ratio,rtol=3e-12,atol=1e-12)
                record.to_parquet(OUT/f'bridge_{line}_fold{held}.parquet',index=False)
                for (year,nb),jj in record.groupby(['year','new_business']).groups.items():
                    jj=np.asarray(list(jj));rr=record.normalizer_ratio.to_numpy()[jj]
                    cells.append({'line':line,'held':held,'year':int(year),'NB':int(nb),'rows':len(jj),
                                  'old_vs_production_normalizer_ratio_quantiles':np.quantile(rr,[0,.5,1]).tolist(),
                                  'base_ultimate_bridge_vs_old_observed_ratio_quantiles':np.quantile(reference[jj]/obs['S2'][jj],[0,.5,1]).tolist()})
                controls.append({'line':line,'held':held,'saved_scope_ancestry_exact':True,'held_payload_ultimate_forward_invariant':True,
                                 'all_learning_blocked':True,'independent_cached_observed_bridge_max_relative_errors':maxerror,
                                 'source_inference':0,'reused_cached_observed_prices_and_normalizers':True})
    finally:
        for m,n,original in saved:setattr(m,n,original)
    assert p[['B','T_B']].notna().all().all();p.to_parquet(OUT/'held_production_bridge_prices.parquet',index=False)
    stats.OUT=OUT
    with threadpool_limits(limits=2):result=stats.metrics(p,['B'],plan,'primary')['B']
    result['worst_cell_delta']=min(c['delta_cell_null'] for c in result['cells'])
    result['diagnostic_gates']={'delta_ge002':result['delta']>=.002,'lower95_positive':result['bootstrap95'][0]>0,
                                'at_least4positive_folds':sum(v>0 for v in result['folds'].values())>=4,
                                'both_years_nonnegative':min(result['years'].values())>=0,
                                'post31_nonnegative':result['post31_delta']>=0,'worst_cell_ge_minus001':result['worst_cell_delta']>=-.001}
    assert all(w.sha(ROOT/path)==v for path,v in plan['sources'].items())
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'production_observation_bridge_complete',
            'primary':result,'normalizer_cell_readout':cells,'numeric_controls':controls,
            'new_model_fits':0,'new_C0_fits':0,'new_calibration_fits':0,'new_source_inference':0,
            'primary_prediction_normalizers':240,'held_poison_prediction_normalizers_separate':240,
            'new_final_test_prices':0,'new_submissions':0,'actual_five_member_nested_validation':False,
            'full_F3c_replay':False,'submission_allowed':False,'limits':plan['limits'],
            '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,'plan_sha256':w.sha(PLAN)}
    dump(OUT/'report.json',report)
    print(json.dumps({'primary':{k:result[k] for k in ['delta','bootstrap95','post31_delta','worst_cell_delta','years','folds','diagnostic_gates']},
                      'max_bridge_errors':{name:max(c['independent_cached_observed_bridge_max_relative_errors'][name] for c in controls) for name in ['G3','H1','S2']},
                      'new_fits':0,'new_submissions':0},ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['register','run']);args=parser.parse_args()
    {'register':register,'run':run}[args.mode]()
