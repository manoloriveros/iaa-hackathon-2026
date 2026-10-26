"""Mismo GLM de edad NB, nuevo offset H1 y REN PUL2 preservada."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import importlib.util
import json
import os
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';HET=BASE/'enlace_HET_20261026_v1'
PUL=BASE/'forma_ultima_PUL_20261026_v1';OUT=BASE/'edad_H1_PUL3_20261026_v1'
PROPOSAL=R/'registro/semana2_edad_H1_propuesta_v0.json'
PLAN=R/'registro/semana2_edad_H1_PUL3_plan_v1.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


age=load('AGEH1_unchanged_GLM_engine',R/'herramientas/glm_edad_NB.py')
het=load('AGEH1_parent_saved_replay',R/'herramientas/contrastar_enlace_HET.py')
d=load('AGEH1_primary_statistics',R/'herramientas/glm_discrepancia_A1S.py')
w=age.w;LINES=['motor','buildings','contents']


def dump(p,v):
    assert not p.exists(),'Preserve artifact: '+str(p)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')


def combine(f,pul2,age_h1):
    result=np.asarray(pul2,float).copy();nb=f.new_business.eq(1).to_numpy()
    result[nb]=np.asarray(age_h1,float)[nb]
    assert np.array_equal(result[~nb],np.asarray(pul2)[~nb])
    return result


def routing_fixtures():
    f=pd.DataFrame({'year':[2023]*10+[2024]*10,'new_business':[0,1]*10,
        'age_band':age.LEVELS*4,'baseline_G3':np.arange(20,dtype=float)+30.,'T0':-1e30,'reserve':-1e30})
    pul2=f.baseline_G3.to_numpy()*np.where(f.new_business.eq(0),1.2,1.)
    zero={'coef':[0.]*7}
    h1,_=age.apply(f,zero);assert np.array_equal(combine(f,pul2,h1),pul2)
    coef={'coef':[.1,-.1,.03,-.02,0.,.5,-.8]}
    moved,_=age.apply(f,coef);a=combine(f,pul2,moved)
    changed_nuisance={'coef':coef['coef'][:5]+[40.,-40.]}
    assert np.array_equal(a,combine(f,pul2,age.apply(f,changed_nuisance)[0]))
    assert np.array_equal(a[f.new_business.eq(0)],pul2[f.new_business.eq(0)])
    unknown=f.copy();unknown['age_band']='__UNKNOWN__'
    assert np.array_equal(combine(unknown,pul2,age.apply(unknown,coef)[0]),pul2)
    return {'new_no_fit_adapter_fixtures':True,'zero_effect_exact_PUL2':True,'REN_exact_PUL2':True,
            'nuisance_not_transferred':True,'unknown_age_neutral_exact':True,'synthetic_fits':0}


def prepare():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir()
    proposal=w.read(PROPOSAL);oldplan=w.read(age.PLAN)
    assert oldplan['sources'][w.rel(Path(age.__file__))]==w.sha(Path(age.__file__))
    assert proposal['configuration']['levels']==age.LEVELS and proposal['configuration']['K']==age.K
    assert w.read(age.OUT/'synthetic.json')['full_numeric_learning_held_poison_exact']
    pul=pd.read_parquet(PUL/'oof_2023_2024.parquet').set_index('row_id')
    sources=[Path(__file__),Path(age.__file__),Path(het.__file__),Path(d.__file__),PROPOSAL,age.PLAN,
        age.OUT/'synthetic.json',age.OUT/'report.json',HET/'report.json',PUL/'report.json',
        PUL/'oof_2023_2024.parquet',PUL/'statistics_PUL2/bootstrap.npy',
        R/'registro/semana2_forma_ultima_PUL_plan_v1.json',ROOT/w.read(PROPOSAL)['necessity_evidence']]
    scopes=[]
    for line in LINES:
        ap=age.OUT/f'inputs_{line}_fold0.parquet';sources.append(ap)
        cov=pd.read_parquet(ap,columns=['row_id','age_band']).set_index('row_id')
        for held in range(5):
            inp=HET/f'inputs_{line}_fold{held}.parquet';hp=HET/f'learning_H1_{line}_fold{held}.json'
            cp=BASE/f'tanda2_20261025_v1/learning_{line}_fold{held}.json'
            kp=BASE/f'FSp_REN_G3_prod_contraste_20261026_v1/learning_{line}_fold{held}.json'
            sources += [inp,hp,cp,kp]
            f=pd.read_parquet(inp);a=w.read(hp);c0=w.read(cp)['artifact']['C0'];kappa=w.read(kp)
            training=f.fold.ne(held)
            assert sorted(f.loc[training,'row_id'])==c0['fit_row_ids']==kappa['training_row_ids']
            assert het.b.digest(sorted(f.loc[training,'row_id']))==a['training_row_ids_digest']
            assert c0['excluded_fold']==held and not set(f.loc[training,'group_id']).intersection(f.loc[~training,'group_id'])
            saved_G3=f.baseline_G3.to_numpy().copy();new=np.full(len(f),np.nan)
            # Separate training/held normalization, exactly as HETlearn.
            for mask,normkey in [(training,'training_normalizers'),(~training,'held_normalizers')]:
                replay,norm=het.replay(f.loc[mask],a)
                assert norm==a[normkey]
                new[mask]=replay
            assert np.isfinite(new).all() and (new>0).all()
            valid=f.loc[~training];reference=pul.loc[valid.row_id]
            assert np.array_equal(new[~training],reference.H1)
            for col in ['T0','year','fold','group_id','new_business']:assert np.array_equal(valid[col],reference[col])
            assert np.array_equal(reference.loc[reference.new_business.eq(1),'PUL2'],reference.loc[reference.new_business.eq(1),'H1'])
            f['original_baseline_G3']=saved_G3;f['baseline_G3']=new
            f['age_band']=cov.loc[f.row_id,'age_band'].to_numpy()
            keep=['row_id','line','year','group_id','fold','new_business','exposure','T0','reserve','baseline_G3','original_baseline_G3','age_band']
            fp=OUT/f'inputs_{line}_fold{held}.parquet';f[keep].to_parquet(fp,index=False)
            nb=training&f.new_business.eq(1)
            assert not np.array_equal(f.loc[nb,'baseline_G3'],f.loc[nb,'original_baseline_G3'])
            scopes.append({'line':line,'held':held,'input':w.rel(fp),'sha256':w.sha(fp),
                'training_NB_rows':int(nb.sum()),'H1_training_and_held_replayed_separately':True,
                'H1_held_bit_exact_and_C0_kappa_membership_exact':True})
    # Raw original A1 only; no private scores or new source-model inference.
    proxyp=age.PARENT/'A1_original2024_proxy_prices.parquet';sources.append(proxyp)
    proxy=pd.read_parquet(proxyp,columns=['row_id','A1'])
    assert proxy.row_id.is_unique
    proxy.to_parquet(OUT/'A1_original_2024.parquet',index=False)
    dump(OUT/'routing_fixtures.json',routing_fixtures())
    dump(OUT/'preflight.json',{'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scopes':scopes,
        'sources':{w.rel(p):w.sha(p) for p in sources},'real_fits':0,'synthetic_optimizer_fits':0,
        'unchanged_optimizer_fixture_reused':w.rel(age.OUT/'synthetic.json'),'new_scores':0,'new_C0':0})
    print(json.dumps({'preflight':'passed','scopes':15,'real_fits':0,'new_synthetic_optimizer_fits':0}))


def register():
    assert not PLAN.exists() and not (OUT/'registration.json').exists()
    pre=w.read(OUT/'preflight.json');proposal=w.read(PROPOSAL)
    sources={**pre['sources'],w.rel(OUT/'preflight.json'):w.sha(OUT/'preflight.json'),
        w.rel(OUT/'routing_fixtures.json'):w.sha(OUT/'routing_fixtures.json'),
        w.rel(OUT/'A1_original_2024.parquet'):w.sha(OUT/'A1_original_2024.parquet'),
        **{s['input']:s['sha256'] for s in pre['scopes']}}
    assert all(w.sha(ROOT/p)==v for p,v in sources.items())
    plan={**proposal,'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'registered_before_new_fit_score',
        'primary':'PUL3withAGEH1NB; both combined and NBincrement guards mandatory',
        'criterion':proposal['criterion_combined_vs_G3'],
        'bootstrap':{'replicates':2000,'seed':2026102614,'unit':'same global connected components and paired draws as PUL2',
            'NB_increment':'Subtract savedPUL2vsG3draws from newPUL3vsG3draws, no second bootstrap'},
        'unchanged_engine':{'path':w.rel(Path(age.__file__)),'sha256':w.sha(Path(age.__file__)),
             'called_functions':['problem','fit','apply','mathematics'],'no_original_main_prepare_run_or_synthetic_called':True},
        'proxy_guards':'Weighted2024age-only NBdelta on raworiginalA1 nonnegative. Also report full PUL3/G3ratio proxy on A1; neither is corrected/fullF3c or independent confirmation.',
        'budget':proposal['budget_if_registered'],'prediction_only_normalizers':45,'synthetic_optimizer_fits_this_assay':0,
        'sources':sources,'formal_admission':False,'submission_allowed':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. Registro AGEH1/PUL3 antes de los 15 GLM nuevos. Se conserva exactamente el motor de edad anterior, cinco bandas, K300, objetivo y optimizador; ahora usa H1, cuyo enlace y offset cambiaron materialmente. '
        'El resultado adverso anterior permanece. La exposición por edad solo justifica revisar una entrada distinta; no demuestra un efecto de edad. '
        'H1 se reprodujo por separado en entrenamiento y retenido de cada ámbito, sin usar precios OOF de otros folds para aprender. Se cotejaron C0/kappas/ancestros y la edad por clave. '
        'PUL3 conservará REN de PUL2 exactamente. NB usará el GLM con offset H1, sin exposición adicional, e interceptos de año no transferidos. '
        'Deben pasar las guardas NB y las combinadas: REN no puede ocultar daño NB. Se mantienen sensibilidad ponderada y proxy A1. '
        'El código y fixture del optimizador no cambiaron y se verifican por hash; no se repite esa suite. Pasaron las rutas nuevas sin ajustar, identidad cero y nuisance ignorado. '
        'Cero árboles fuente, C0, kappas, inferencias fuente, precios finales de 2025 o envíos. B00/F3c y alternativas intactos; 2024 abierto. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-AGEH1-PUL3-PREVIO','--asunto','AGEH1/PUL3 registrado: mismo GLM, nuevo enlace y guardas NB',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(response.stdout)})
    print(json.dumps({'registered':True,'real_GLM_budget':15,'forum':json.loads(response.stdout)}))


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})
    p=pd.read_parquet(PUL/'oof_2023_2024.parquet');p['AGEH1']=p.H1;p['PUL3']=p.PUL2
    idx=pd.Series(p.index.to_numpy(),index=p.row_id)
    proxy=pd.read_parquet(OUT/'A1_original_2024.parquet')
    proxy=proxy.merge(p[['row_id','line','year','new_business','fold']],on='row_id',validate='one_to_one')
    proxy['A1_age_only']=proxy.A1;checks=[]
    with threadpool_limits(limits=2):
        for scope in w.read(OUT/'preflight.json')['scopes']:
            f=pd.read_parquet(ROOT/scope['input']);line,held=scope['line'],scope['held']
            problem=age.problem(f,held);path=OUT/f'model_{line}_fold{held}.json';assert not path.exists()
            dump(OUT/f'fit_invoked_{line}_fold{held}.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'problem_signature':problem['signature']})
            a=age.fit(problem,line,held,path);math=age.mathematics(problem,a)
            poison=f.copy();poison.loc[poison.fold.eq(held),['T0','reserve']]=-1e30
            other=age.problem(poison,held);assert problem['signature']==other['signature']
            for key in ['X','y','base','offset','penalty','initial']:assert np.array_equal(problem[key],other[key])
            valid=f.loc[f.fold.eq(held)];pred,norm=age.apply(valid,a)
            original=age.optimize.minimize
            def reject(*args,**kwargs):raise AssertionError('No fitting during saved replay')
            age.optimize.minimize=reject
            try:
                value,nn=age.apply(valid,w.read(path));assert np.array_equal(pred,value) and norm==nn
                assert np.array_equal(age.apply(valid.assign(T0=-1e30,reserve=-1e30),a)[0],pred)
            finally:age.optimize.minimize=original
            ii=idx.loc[valid.row_id].to_numpy();p.loc[ii,'AGEH1']=pred
            p.loc[ii,'PUL3']=combine(valid,p.loc[ii,'PUL2'].to_numpy(),pred)
            qi=proxy.index[proxy.line.eq(line)&proxy.fold.eq(held)]
            q=valid.set_index('row_id').loc[proxy.loc[qi,'row_id']].reset_index()
            aux,auxnorm=age.apply(q,a,base=proxy.loc[qi,'A1'].to_numpy())
            proxy.loc[qi,'A1_age_only']=aux
            dump(OUT/f'application_{line}_fold{held}.json',{'normalizers':norm,'proxy_normalizers':auxnorm,'model_sha256':w.sha(path),
                'REN_exact_PUL2':True,'full_numeric_problem_held_poison_invariant':True,'saved_replay_optimizer_blocked_exact':True})
            checks.append({'line':line,'held':held,'full_numeric_problem_held_poison_invariant':True,'saved_replay_optimizer_blocked_exact':True,**math})
        assert np.array_equal(p.loc[p.new_business.eq(0),'PUL3'],p.loc[p.new_business.eq(0),'PUL2'])
        p.to_parquet(OUT/'oof_2023_2024.parquet',index=False)
        d.OUT=OUT
        result=d.statistics(p[['row_id','line','year','group_id','fold','new_business','T0','N3','G3','PUL3']].rename(columns={'PUL3':'D1'}),plan)
        result['scores']['PUL3']=result['scores'].pop('D1')
    parent=pd.read_parquet(PUL/'oof_2023_2024.parquet')
    for col in ['row_id','group_id','T0','fold','G3','PUL2']:assert np.array_equal(parent[col],p[col])
    draws=np.load(OUT/'bootstrap.npy')-np.load(PUL/'statistics_PUL2/bootstrap.npy')
    np.save(OUT/'NB_increment_bootstrap.npy',draws)
    y=p.T0.to_numpy(float);den=d.unit(y,np.full(len(y),y.mean())).sum()
    gain=d.unit(y,p.PUL2.to_numpy())-d.unit(y,p.PUL3.to_numpy())
    assert np.array_equal(gain[p.new_business.eq(0)],np.zeros(int(p.new_business.eq(0).sum())))
    delta=float(gain.sum()/den);ci=np.quantile(draws,[.025,.975]).tolist()
    folds={str(k):float(gain[p.fold.eq(k)].sum()/den) for k in range(5)}
    years={str(k):float(gain[p.year.eq(k)].sum()/den) for k in [2023,2024]}
    cells=[]
    for (line,year,nb),ii in p.groupby(['line','year','new_business']).groups.items():
        ii=np.array(list(ii));yy=y[ii];dd=d.unit(yy,np.full(len(yy),yy.mean())).sum()
        cells.append({'line':line,'year':int(year),'NB':int(nb),'delta_cell_null':float(gain[ii].sum()/dd)})
    guards={'point_nonnegative':delta>=0,'both_years_nonnegative':min(years.values())>=0,
        'positive_folds_min4':sum(v>0 for v in folds.values())>=4,'lower95_positive':ci[0]>0,
        'cell_min':min(v['delta_cell_null'] for v in cells)>=-.001}
    wp=BASE/'estimando_cartera2025_v3/weights.parquet'
    weights=pd.read_parquet(wp,columns=['row_id','weight']).set_index('row_id').loc[p.row_id,'weight'].to_numpy()
    wd=d.unit(y,np.full(len(y),np.average(y,weights=weights)))
    weighted=float(np.sum(weights*gain)/np.sum(weights*wd))
    q=p.loc[p.year.eq(2024)].merge(proxy[['row_id','A1','A1_age_only']],on='row_id',validate='one_to_one')
    qw=pd.read_parquet(wp,columns=['row_id','weight']).set_index('row_id').loc[q.row_id,'weight'].to_numpy()
    yy=q.T0.to_numpy();qden=np.sum(qw*d.unit(yy,np.full(len(yy),np.average(yy,weights=qw))))
    proxy_age=float(np.sum(qw*(d.unit(yy,q.A1.to_numpy())-d.unit(yy,q.A1_age_only.to_numpy())))/qden)
    q['A1_PUL3_ratio_proxy']=q.A1.to_numpy()*(q.PUL3.to_numpy()/q.G3.to_numpy())
    proxy_full=float(np.sum(qw*(d.unit(yy,q.A1.to_numpy())-d.unit(yy,q.A1_PUL3_ratio_proxy.to_numpy())))/qden)
    proxy.to_parquet(OUT/'A1_age_only_proxy.parquet',index=False)
    q[['row_id','A1','A1_PUL3_ratio_proxy']].to_parquet(OUT/'A1_full_ratio_proxy.parquet',index=False)
    vetos={'weighted_NB_increment_nonnegative':weighted>=0,'weighted_full_nonnegative':result['weighted2025_sensitivity_delta']>=0,
           'A1_original2024_age_only_NB_proxy_nonnegative':proxy_age>=0,'A1_original2024_full_ratio_proxy_nonnegative':proxy_full>=0}
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'complete_exploratory_no_formal_admission',
        'primary':'PUL3','combined':result,'NB_increment':{'delta':delta,'paired_bootstrap95':ci,'folds':folds,'years':years,'cells':cells,
            'guards':guards,'all_guards_pass':all(guards.values()),'same_group_outcome_order_and_seed':True},
        'weighted_NB_increment':weighted,'A1_original_2024_age_only_NB_proxy':proxy_age,'A1_original_2024_full_ratio_proxy':proxy_full,
        'additional_vetoes':vetos,'all_additional_vetoes_pass':all(vetos.values()),'numeric_controls':checks,
        'new_real_GLM_fits':15,'new_C0_fits':0,'new_source_fits':0,'new_kappa_fits':0,'new_source_inference':0,
        'new_synthetic_optimizer_fits':0,'new_prediction_only_normalizers':45,'new_final_test_prices':0,'new_submissions':0,
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,'plan_sha256':w.sha(PLAN),
        'limits':['2024and cumulative search adaptive; not independent professional confirmation','H1observation mix is an unverified ultimate proxy',
            'Source tail/reserves/master vintage assumptions persist','A1original proxies not corrected/fullF3c; ratios are conditional diagnostics only','WeightedESSgate remains failed']}
    assert all(w.sha(ROOT/path)==value for path,value in plan['sources'].items())
    dump(OUT/'report.json',report)
    print(json.dumps({'combined':{k:result[k] for k in ['scores','delta_vs_G3','bootstrap95','post31_delta','gates','weighted2025_sensitivity_delta']},
        'NB_increment':{k:report['NB_increment'][k] for k in ['delta','paired_bootstrap95','folds','years','guards']},
        'weighted_NB_increment':weighted,'A1_age_proxy':proxy_age,'A1_full_proxy':proxy_full,'additional_vetoes':vetos},ensure_ascii=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','register','run']);a=p.parse_args()
    {'prepare':prepare,'register':register,'run':run}[a.mode]()
