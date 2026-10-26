"""Misma receta estándar N3/G3, nueva hipótesis de exposición por riesgo."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import importlib.util
import json
import os
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';PARENT=BASE/'FSp_REN_G3_prod_contraste_20261026_v1'
DIAG=BASE/'completitud_por_riesgo_diagnostico_20261026_v2'
HOME=BASE/'A1S_nucleo_20261026_v1'
OUT=BASE/'enlace_HET_20261026_v1';PLAN=R/'registro/semana2_enlace_HET_plan_v1.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


d=load('HET_existing_statistics',R/'herramientas/glm_discrepancia_A1S.py')
qengine=load('HET_saved_profile_math',R/'herramientas/diagnosticar_completitud_por_riesgo_v2.py')
w=d.w;b=d.c.b;g=d.c.g;LINES=d.LINES
LINKS={'H1':'e_source_mix','H2':'e_outer_mix'}


def dump(path,value):
    assert not path.exists(),'Preserve artifact: '+str(path)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')


def base(f,link,ultimate=False):
    exposure=f.exposure.to_numpy(float) if ultimate else f[link].to_numpy(float)
    assert np.isfinite(exposure).all() and (exposure>0).all()
    return f.annual_raw_T2b.to_numpy(float)*exposure


def apply_component(f,a,link,ultimate=False):
    value=base(f,link,ultimate)
    for shape in a['shape']:value=b.shape_apply(f,value,shape)
    return value*np.array([a['cellshape'][str(int(nb))] for nb in f.new_business])


def replay(f,a,ultimate=False):
    value=apply_component(f,a,a['link'],ultimate);norms={}
    for stage in a['stages']:
        value,norm=g.apply_stage(f,value,stage);norms[stage['variable']]=norm
    return value,norms


def learn(f,held,line,link):
    mask=f.fold.ne(held).to_numpy();train=f.loc[mask].copy();valid=f.loc[~mask].copy()
    assert not set(train.group_id).intersection(valid.group_id)
    mtrain=base(train,link);mvalid=base(valid,link);shapes=[]
    for variable in (['ncb','prior'] if line=='motor' else ['prior']):
        artifact,mtrain=b.shape_fit(train,mtrain,variable)
        mvalid=b.shape_apply(valid,mvalid,artifact);shapes.append(artifact)
    k=b.factor(train.T0.to_numpy(float),mtrain);cells=b.cell_levels(train,mtrain,k)
    mtrain*=np.array([cells[str(int(nb))] for nb in train.new_business])
    mvalid*=np.array([cells[str(int(nb))] for nb in valid.new_business])
    stages=[];training_norms={};held_norms={}
    for variable in g.STAGES[line]:
        a=g.fit_stage(train,mtrain,variable)
        mtrain,nt=g.apply_stage(train,mtrain,a);mvalid,nv=g.apply_stage(valid,mvalid,a)
        stages.append(a);training_norms[variable]=nt;held_norms[variable]=nv
    artifact={'line':line,'held':held,'link':link,'shape':shapes,'kshape':k,'cellshape':cells,
        'stages':stages,'training_normalizers':training_norms,'held_normalizers':held_norms,
        'training_rows':len(train),'training_row_ids_digest':b.digest(sorted(train.row_id)),
        'training_groups_digest':b.digest(sorted(set(train.group_id)))}
    return mvalid,artifact


def synthetic():
    rng=np.random.default_rng(2026102614);n=1600
    f=pd.DataFrame({'row_id':['s'+str(i) for i in range(n)],'group_id':['g'+str(i) for i in range(n)],
        'fold':np.arange(n)%5,'year':2023+(np.arange(n)//5)%2,'new_business':(np.arange(n)//10)%2,
        'T0':rng.gamma(2,100,n)*(rng.random(n)<.4),'reserve':0.,'exposure':1.,
        'annual_raw_T2b':rng.uniform(60,200,n),'e_cost_scope':rng.uniform(.3,.7,n),
        'ncb_years':rng.integers(0,15,n),'prior_claims_5y':rng.integers(0,3,n),
        'gender':rng.choice(['F','M'],n),'works_from_home':rng.integers(0,2,n),
        'marketing_segment':rng.choice(['a','b','c'],n)})
    f['e_source_mix']=f.e_cost_scope*rng.uniform(.8,1.2,n)
    f['e_outer_mix']=f.e_cost_scope*rng.uniform(.8,1.2,n)
    checks=[]
    for line in LINES:
        for name,link in LINKS.items():
            pred,a=learn(f,0,line,link)
            poisoned=f.copy();poisoned.loc[poisoned.fold.eq(0),['T0','reserve']]=-1e30
            q,z=learn(poisoned,0,line,link)
            assert b.digest(a)==b.digest(z) and np.array_equal(pred,q)
            changed=f.copy();changed.loc[changed.fold.ne(0),'T0']*=2
            _,other=learn(changed,0,line,link);assert b.digest(other)!=b.digest(a)
            valid=f.loc[f.fold.eq(0)];r,norm=replay(valid,a)
            assert np.array_equal(pred,r) and norm==a['held_normalizers']
            # The actual ultimate adapter must work when all observed links
            # at the old snapshot are zero for a future policy.
            future=valid.copy();future['year']=2025
            future[['e_cost_scope','e_source_mix','e_outer_mix']]=0.
            future['exposure']=.8
            ultimate,_=replay(future,a,ultimate=True)
            assert np.isfinite(ultimate).all() and (ultimate>0).all()
            assert np.array_equal(base(future,link,ultimate=True),future.annual_raw_T2b.to_numpy()*.8)
            checks.append({'line':line,'profile':name,'complete_learning_held_poison_invariant':True,
                'training_response_changes_learning':True,'saved_replay_exact':True,'future_zero_observed_link_ultimate_calendar_once':True})
        flat=f.copy();flat['e_source_mix']=flat.e_cost_scope;flat['e_outer_mix']=flat.e_cost_scope
        first,_=learn(flat,0,line,'e_source_mix');second,_=learn(flat,0,line,'e_outer_mix')
        assert np.array_equal(first,second)
    return {'checks':checks,'flat_profile_link_identity_exact':True,'synthetic_closed_scope_learning_calls':24,
            'contest_calibrations':0,'iterative_model_fits':0,'new_C0_fits':0}


def prepare():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir()
    assert w.read(DIAG/'report.json')['material_cells']==39
    pre=w.read(PARENT/'preflight.json')
    sources=[Path(__file__),Path(d.__file__),Path(b.__file__),Path(g.__file__),Path(qengine.__file__),
        DIAG/'report.json',DIAG/'completion_receipt.json',PARENT/'preflight.json',PARENT/'report.json',HOME/'report.json']
    references={}
    for item in w.read(DIAG/'report.json')['outputs']:
        path=ROOT/item['path'];assert w.sha(path)==item['sha256'];sources.append(path)
        frame=pd.read_parquet(path);references[(frame.line.iloc[0],int(frame.fold.iloc[0]))]=frame.set_index('row_id')
    cache={};scopes=[]
    for scope in pre['scopes']:
        line=scope['line'];held=scope['held'];perils=pre['perils'][line]
        inp=ROOT/scope['input'];assert w.sha(inp)==scope['sha256'];sources.append(inp)
        f=pd.read_parquet(inp)
        if line not in cache:
            rp=HOME/f'rows_s2_{line}.parquet';xp=HOME/f'matrix_s2_{line}.parquet'
            rawp=BASE/f'linaje_T2b_v1/raw_rates_{line}.parquet';sources += [rp,xp,rawp]
            feature_cols=['prior_claims_5y']+(['ncb_years'] if line=='motor' else [])
            cov=pd.read_parquet(xp,columns=feature_cols)
            cov['row_id']=pd.read_parquet(rp,columns=['row_id']).row_id.to_numpy()
            cache[line]=(cov.set_index('row_id'),pd.read_parquet(rawp,columns=['row_id','annual_raw_T2b']).set_index('row_id'))
        cov,raw=cache[line]
        for col in cov:f[col]=cov.loc[f.row_id,col].to_numpy()
        f['annual_raw_T2b']=raw.loc[f.row_id,'annual_raw_T2b'].to_numpy()
        assert np.array_equal(f.unshaped_T2b,f.annual_raw_T2b.to_numpy()*f.e_cost_scope.to_numpy())
        cp=BASE/f'tanda2_20261025_v1/learning_{line}_fold{held}.json';kp=PARENT/f'learning_{line}_fold{held}.json'
        sources += [cp,kp];c0=w.read(cp)['artifact']['C0'];kappa=w.read(kp)
        training=f.fold.ne(held)
        assert sorted(f.loc[training,'row_id'])==c0['fit_row_ids']==kappa['training_row_ids']
        assert sorted(set(f.loc[training,'group_id']))==kappa['training_groups']
        assert c0['excluded_fold']==held and not set(f.loc[training,'group_id']).intersection(f.loc[~training,'group_id'])
        for name,link in LINKS.items():
            weights={p:(1. if name=='H1' else kappa['perils'][p]['kappa']) for p in perils}
            # IMPORTANT: one outer profile is applied to both training and
            # held rows. OOF vectors from other folds are never used in fit.
            q,_,_=qengine.conditional_q(f,perils,weights)
            f[link]=f.exposure.to_numpy()*q
            assert f[link].gt(0).all() and (f[link]<=f.exposure+1e-12).all()
            column='q_source' if name=='H1' else 'q_outer_saved'
            ref=references[(line,held)].loc[f.loc[~training,'row_id'],column].to_numpy()
            assert np.array_equal(q[~training],ref)
        output=OUT/f'inputs_{line}_fold{held}.parquet';f.to_parquet(output,index=False)
        scopes.append({'line':line,'held':held,'input':w.rel(output),'sha256':w.sha(output),
            'one_outer_ancestry_for_training_and_held':True,'held_q_exact_previous_diagnostic':True,
            'training_rows':int(training.sum()),'held_rows':int((~training).sum())})
    with threadpool_limits(limits=2):dump(OUT/'synthetic.json',synthetic())
    dump(OUT/'preflight.json',{'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scopes':scopes,
        'sources':{w.rel(p):w.sha(p) for p in sources},'contest_calibrations':0,'new_scores':0,'new_C0_fits':0})
    print(json.dumps({'preflight':'passed','scopes':15,'contest_calibrations':0,'new_C0':0}))


def register():
    assert not PLAN.exists() and not (OUT/'registration.json').exists()
    pre=w.read(OUT/'preflight.json');syn=w.read(OUT/'synthetic.json')
    assert syn['flat_profile_link_identity_exact'] and len(syn['checks'])==6
    paths={**pre['sources'],w.rel(OUT/'preflight.json'):w.sha(OUT/'preflight.json'),
        w.rel(OUT/'synthetic.json'):w.sha(OUT/'synthetic.json'),**{s['input']:s['sha256'] for s in pre['scopes']}}
    assert all(w.sha(ROOT/p)==v for p,v in paths.items())
    plan={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'primary_candidate':'H2',
        'hypothesis':'Global fixed peril mixture can misstate the observation exposure of individual risks. The new diagnostic showed material completion differences mainly in2024motor/buildingNB. Change this observation link before adding model capacity.',
        'profiles':{'H1':'Fixed source-only f*s risk mixture, declared ablation; no post-score winner selection.',
                    'H2':'Primary: existing outer-trained shrunk kappa*f*s risk mixture. Same outer profile applied to its train and held rows.'},
        'formula':'e_risk_i=calendar_exposure_i*sum_p(r_ip*q_ip)/sum_p(r_ip), with r=f*s or savedkappa*f*s. Peril curves reused unchanged; no new frequency/severity/curve/kappa estimation.',
        'standard_recipe':'Same T2bsource raw annual risk, same N3NCB/prior shape rules (n/(n+300)), Tweedie line level and business shrink(n/(n+400)), then same G3gender/telework/marketing sequential factors(K300). Relearn only these standard closed calibrations on outer-training rows under the candidate exposure.',
        'response_metric':'T0incurred net recoveries unchanged, unweighted period-unit TweedieD2p1.5 on same109296rows. No annual-rate scoring or held-label calibration.',
        'ancestry':'Source models frozen2021-24; target2023/24global components unchanged. C0and kappa fit-row/group membership checked, each outer ancestry used for ALLrows of its scope. Never use otherfold OOFprofile values in training.',
        'future_ultimate':'Observed completion at oldsnapshot can be0 for2025. Ultimate2025adapter uses calendar exposure and explicit raw annual risk, q=1, no division by0 or applying observedq=0. Synthetic full flow tested; no contest2025prices in this assay.',
        'criterion':w.read(d.PLAN)['criterion'],'bootstrap':{'replicates':2000,'seed':2026102614,'unit':'saved global component','primary':'H2vsG3','H1':'fixed ablation; same draws, not independent evidence'},
        'budget':{'new_iterative_model_fits':0,'new_source_fits':0,'new_C0_fits':0,'new_kappa_fits':0,
            'closed_scope_learning_calls':30,'shape_calibrations':40,'shape_factor_constants':280,'component_level_constants':90,
            'residual_stage_calls':40,'residual_factor_constants':180,'nuisance_year_business_levels':160,
            'control_recomputation_same_constants_separate':True,'synthetic_scope_learning_calls_separate':24,
            'new_final_test_prices':0,'new_submissions':0},
        'controls':['Complete learner heldT0/reserve poisoning and saved replay with learning blocked',
            'Independent Tweedie moment/derivative and exposure multiplication arithmetic',
            'SamefoldC0/kappaancestry for training and held rows, pinned source hashes',
            'Flat mix link identity and positive calendar-only ultimate adapter under zeroobservedfuturelinks'],
        'limits':w.read(qengine.PLAN)['limits']+['This does not identify the true ultimate peril mix or fix reserve/tail assumptions',
            'A local G3improvement is not a full historicF3creplay or demonstrated public gain'],
        'formal_admission':False,'submission_allowed':False,'2024_open':True,'B00_all_alternatives_preserved':True,'sources':paths}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md'
    body.write_text('Codex. Registro HET antes de calibrar o puntuar. H2 es el candidato primario: completitud según mezcla por riesgo con kappas exteriores guardadas; H1 usa fuente sola como ablation fija. '
        'Solo cambia el enlace de observación. Se conservan T0, los modelos fuente, C0, folds y todas las reglas de forma/nivel/factores N3/G3. '
        'Se reaprenderán las mismas constantes cerradas bajo cada exposición, dentro del entrenamiento exterior; no hay árboles o capacidad nueva. '
        'Cada ámbito usa su propio perfil para entrenamiento y validación. Mezclar vectores OOF de otros folds en entrenamiento queda prohibido por sus ancestros protegidos. '
        'El flujo sintético completo pasó alteración de etiquetas retenidas, replay, identidad de mezclas planas y adaptador de último de 2025 con q=1 aunque el enlace observado sea cero. '
        'Presupuesto: 30 calibraciones de ámbito, hasta 710 constantes cerradas únicas, recomputaciones de control aparte; cero curvas, kappas, inferencias fuente, precios finales o envíos. '
        'Criterios previos intactos; H1 no será un ganador elegido después del resultado. Los perfiles son proxies y no identifican la verdadera mezcla última. '
        'B00/F3c 0,16914 y alternativas intactos; 2024 abierto y adaptativo. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-HET-PREVIO','--asunto','HET registrado: misma receta estándar, completitud por riesgo',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(response.stdout)})
    print(json.dumps({'registered':True,'primary':'H2','forum':json.loads(response.stdout)}))


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})
    p=pd.read_parquet(BASE/'tanda10_factores_20261026_v1/oof_2023_2024.parquet')
    for name in LINKS:p[name]=np.nan
    idx=pd.Series(p.index.to_numpy(),index=p.row_id);checks=[]
    constants={'shape_factors':0,'component_levels':0,'residual_factors':0,'nuisance_levels':0,'shape_training_normalizers':0}
    with threadpool_limits(limits=2):
        for scope in w.read(OUT/'preflight.json')['scopes']:
            f=pd.read_parquet(ROOT/scope['input']);held=scope['held'];line=scope['line']
            valid=f.loc[f.fold.eq(held)]
            for name,link in LINKS.items():
                pred,a=learn(f,held,line,link)
                dump(OUT/f'learning_{name}_{line}_fold{held}.json',a)
                bad=f.copy();bad.loc[bad.fold.eq(held),['T0','reserve']]=-1e30
                other,z=learn(bad,held,line,link)
                assert b.digest(a)==b.digest(z) and np.array_equal(pred,other)
                shape_original=b.shape_fit;stage_original=g.fit_stage;level_original=b.factor
                def reject(*args,**kwargs):raise AssertionError('No closed calibration learning during replay')
                b.shape_fit=reject;g.fit_stage=reject;b.factor=reject
                try:
                    q,norm=replay(valid,w.read(OUT/f'learning_{name}_{line}_fold{held}.json'))
                    assert np.array_equal(q,pred) and norm==a['held_normalizers']
                finally:b.shape_fit=shape_original;g.fit_stage=stage_original;b.factor=level_original
                train=f.loc[f.fold.ne(held)];m=base(train,link)
                for shape in a['shape']:m=b.shape_apply(train,m,shape)
                root=np.sqrt(m);observed=float(np.dot(train.T0.to_numpy(float),1/root));expected=float(root.sum())
                independent=observed/expected;assert abs(independent/a['kshape']-1)<1e-13
                assert abs(np.sqrt(independent)*expected-observed/np.sqrt(independent))/max(1,expected)<1e-11
                alternate=np.exp(np.log(f.annual_raw_T2b.to_numpy(float))+np.log(f[link].to_numpy(float)))
                assert np.allclose(base(f,link),alternate,rtol=1e-13)
                p.loc[idx.loc[valid.row_id].to_numpy(),name]=pred
                constants['shape_factors']+=sum(len(s['factors']) for s in a['shape'])
                constants['shape_training_normalizers']+=sum(len(s['normalizers']) for s in a['shape'])
                constants['component_levels']+=3
                constants['residual_factors']+=sum(len(s['factors']) for s in a['stages'])
                constants['nuisance_levels']+=sum(len(s['nuisance_year_business']) for s in a['stages'])
                checks.append({'line':line,'held':held,'profile':name,'full_learning_held_cost_reserve_invariant':True,
                    'saved_replay_all_learning_blocked_exact':True,'independent_level_moment_derivative_and_exposure_math':True})
        assert p[list(LINKS)].notna().all().all() and (p[list(LINKS)]>0).all().all()
        p.to_parquet(OUT/'oof_2023_2024.parquet',index=False);results={}
        for name in LINKS:
            statsout=OUT/f'statistics_{name}';statsout.mkdir();d.OUT=statsout
            result=d.statistics(p[['row_id','line','year','group_id','fold','new_business','T0','N3','G3',name]].rename(columns={name:'D1'}),plan)
            result['scores'][name]=result['scores'].pop('D1');results[name]=result
    assert all(w.sha(ROOT/path)==v for path,v in plan['sources'].items())
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'complete_exploratory_no_formal_admission',
        'primary':'H2','results':results,'constants_unique':constants,'control_recomputations_same_constants_separate':constants,
        'numeric_controls':checks,'new_iterative_model_fits':0,'new_C0_fits':0,'new_kappa_fits':0,
        'new_source_inference':0,'new_final_test_prices':0,'new_submissions':0,'2024_open':True,
        'B00_all_alternatives_preserved':True,'goal_achieved':False,'limits':plan['limits'],'plan_sha256':w.sha(PLAN)}
    dump(OUT/'report.json',report)
    print(json.dumps({'results':{name:{k:r[k] for k in ['scores','delta_vs_G3','bootstrap95','fold_contributions','year_contributions','post31_delta','gates','weighted2025_sensitivity_delta']} for name,r in results.items()},'constants_unique':constants},ensure_ascii=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','register','run']);a=p.parse_args()
    {'prepare':prepare,'register':register,'run':run}[a.mode]()
