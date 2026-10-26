"""H3B: mezcla fuente agregada por negocio, validación anidada y estrés fijo."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import importlib.util
import json
import math
import os
import sys
import subprocess

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';P2=BASE/'media_anidada_H1_20261026_v3'
P1=BASE/'preflight_anidado_H1_20261026_v1';P0=BASE/'puente_ultimo_observado_H1_20261026_v1'
P3=BASE/'sensibilidad_congelada_media_H1_20261026_v1'
OUT=BASE/'H3B_mezcla_negocio_20261026_v1';PLAN=R/'registro/semana2_H3B_mezcla_negocio_plan_v1.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits


def load(name,path):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m


n=load('H3B_protected_scope_tools',R/'herramientas/evaluar_media_anidada_H1_v3.py')
frozen=load('H3B_frozen_observation_contract',R/'herramientas/sensibilidad_congelada_media_H1.py')
h=n.h;b=h.b;g=h.g;v=b.v;w=h.w;unit=frozen.unit
NAMES=['NOMINAL_VS_BASE','NOMINAL_VS_H1',*frozen.SCENARIOS]


def dump(path,value):
    with path.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)


def fit_business_mix(train,perils):
    r=np.column_stack([train['f_'+p].to_numpy(float)*train['s_'+p].to_numpy(float) for p in perils])
    assert np.isfinite(r).all() and (r>0).all();weights={}
    for nb in [0,1]:
        selected=train.new_business.eq(nb).to_numpy();assert selected.any()
        sums=r[selected].sum(axis=0);value=sums/sums.sum()
        independent=np.array([math.fsum(r[selected,j].tolist()) for j in range(len(perils))]);independent/=independent.sum()
        assert np.allclose(value,independent,rtol=3e-12,atol=1e-14)
        weights[str(nb)]={p:float(z) for p,z in zip(perils,value)}
    return {'weights':weights,'perils':perils,'training_rows_digest':b.digest(sorted(train.row_id)),
            'training_groups_digest':b.digest(sorted(set(train.group_id))),
            'period_cost_source_profile_no_second_exposure':True,'no_response_used':True}


def business_completion(f,c0,mix,branch=1.,tail=0.):
    perils=mix['perils'];assert set(perils)==set(c0['curves'])
    qq=np.column_stack([v.average_completion(f,c0['curves'][p],'cost',branch) for p in perils])
    if tail:qq*=1-tail*np.array([p in ['bodily_injury','subsidence'] for p in perils],float)
    ww=np.array([[mix['weights'][str(int(nb))][p] for p in perils] for nb in f.new_business])
    q=np.sum(ww*qq,axis=1)
    assert np.isfinite(q).all() and (q>=0).all() and (q<=1+1e-12).all()
    return q


def learn_scope(f,c0,line,folder,role,logfolder):
    folder.mkdir(parents=True,exist_ok=True);train=f.fold.eq(0);held=f.fold.eq(1)
    assert c0['fit_row_ids']==sorted(f.loc[train,'row_id']) and not set(f.loc[train,'group_id']).intersection(f.loc[held,'group_id'])
    perils=sorted(c0['curves']);mix=fit_business_mix(f.loc[train],perils)
    work=f.copy();q=business_completion(work,c0,mix);assert (q>0).all()
    work['e_business_mix']=work.exposure.to_numpy()*q
    path=folder/'learning_H3B.json'
    if path.exists():
        record=w.read(path);assert record['mix']==mix
        a=record['artifact'];observed,_=h.replay(work.loc[held],a)
    else:
        n.event(logfolder,'H3B_closed_started',role=role,scope=folder.parent.name)
        observed,a=h.learn(work,1,line,'e_business_mix')
        assert a['training_row_ids_digest']==mix['training_rows_digest'] and a['training_groups_digest']==mix['training_groups_digest']
        record={'mix':mix,'artifact':a};dump(path,record)
        n.event(logfolder,'H3B_closed_completed',role=role,scope=folder.parent.name,constants=n.count_constants(a),
                source_business_mixtures=2,derived_covariate_weights=2*len(perils),artifact_sha256=w.sha(path))
    valid=work.loc[held].copy();Er=valid.exposure.to_numpy(float);E=valid.exposure_calendar.to_numpy(float);valid['exposure']=E
    ultimate,norm=h.replay(valid,a,ultimate=True);L=np.ones(len(valid))
    keys=[f'{int(y)}|{int(nb)}' for y,nb in zip(valid.year,valid.new_business)]
    for variable,z in norm.items():L*=np.array([z[k]/a['held_normalizers'][variable][k] for k in keys])
    assert np.allclose(observed,ultimate*(Er/E)*q[held.to_numpy()]*L,rtol=3e-12,atol=1e-9)
    tr=work.loc[train];m=tr.annual_raw_T2b.to_numpy()*tr.e_business_mix.to_numpy()
    for shape in a['shape']:m=b.shape_apply(tr,m,shape)
    yy=tr.T0.to_numpy();independent=math.fsum((yy/np.sqrt(m)).tolist())/math.fsum(np.sqrt(m).tolist())
    assert math.isclose(independent,a['kshape'],rel_tol=3e-12,abs_tol=1e-12)
    return {'record':record,'row_id':valid.row_id.tolist(),'ultimate':ultimate,
            'bridge_max_relative_error':float(np.max(np.abs(observed/(ultimate*(Er/E)*q[held.to_numpy()]*L)-1))),
            'ultimate_normalizers':sum(len(z) for z in norm.values())}


def corrupt(f):
    bad=f.copy();held=bad.fold.eq(1);bad.loc[held,'T0']=-1e30;bad.loc[held,'reserve']=1e30
    # Source profiles on held rows must not estimate the business mixtures.
    for c in bad.columns:
        if c.startswith(('f_','s_')):bad.loc[held,c]*=1e8
    return bad


def synthetic():
    rng=np.random.default_rng(2026102622);rows=[]
    for line,perils in [('motor',['bodily_injury','glass_hail','own_damage','theft','third_party_prop']),
                        ('buildings',['accidental_damage','escape_of_water','fire','flood','storm','subsidence']),
                        ('contents',['accidental_damage','escape_of_water','flood','theft'])]:
        size=1000;year=rng.integers(2023,2025,size);groups=np.arange(size)//2
        start=pd.to_datetime(pd.Series(year).astype(str)+'-01-01')+pd.to_timedelta(rng.integers(0,150,size),unit='D')
        end=pd.to_datetime(pd.Series(year).astype(str)+'-12-31');E=((end-start).dt.days+1).to_numpy()/365
        f=pd.DataFrame({'row_id':[line+'s'+str(i) for i in range(size)],'line':line,'year':year,'group_id':['sg'+str(x) for x in groups],
                        'fold':(groups%5==0).astype(int),'new_business':rng.integers(0,2,size),'period_start':start,'period_end':end,
                        'is_test':False,'exposure':np.round(E,4),'exposure_calendar':E,'T0':rng.gamma(2,80,size),'reserve':0.,
                        'annual_raw_T2b':rng.uniform(40,300,size),'prior_claims_5y':rng.integers(0,3,size),'ncb_years':rng.integers(0,15,size),
                        'gender':rng.choice(['F','M'],size),'works_from_home':rng.choice([True,False],size),'marketing_segment':rng.choice(['a','b','c'],size)})
        for p in perils:f['f_'+p]=rng.uniform(.05,.3,size)*E;f['s_'+p]=rng.uniform(50,300,size)
        curves={p:{'delay_days':[0,30,365],'cost_cdf':{'1.0':[.1+i*.01,.7+i*.01,1.]}} for i,p in enumerate(perils)}
        c0={'fit_row_ids':sorted(f.loc[f.fold.eq(0),'row_id']),'curves':curves}
        folder=OUT/'synthetic'/line
        a=learn_scope(f,c0,line,folder/'primary','synthetic_primary',OUT/'synthetic')
        z=learn_scope(corrupt(f),c0,line,folder/'poison','synthetic_poison',OUT/'synthetic')
        assert b.digest(a['record'])==b.digest(z['record']) and np.array_equal(a['ultimate'],z['ultimate'])
        future=f.loc[f.fold.eq(1)].copy();future['year']=2025;future['exposure']=.8;future['e_business_mix']=0.
        u,_=h.replay(future,a['record']['artifact'],ultimate=True);assert np.isfinite(u).all() and (u>0).all()
        flat=f.copy()
        for j,p in enumerate(perils):flat['f_'+p]=E*(j+1);flat['s_'+p]=1.+flat.new_business.to_numpy()
        mix=fit_business_mix(flat.loc[flat.fold.eq(0)],perils);q=business_completion(flat,c0,mix)
        Q=np.column_stack([v.average_completion(flat,curves[p],'cost',1.) for p in perils])
        profile=np.column_stack([flat['f_'+p].to_numpy()*flat['s_'+p].to_numpy() for p in perils])
        assert np.allclose(q,np.sum(profile*Q,axis=1)/profile.sum(axis=1),rtol=2e-14,atol=1e-14)
        changed=f.loc[f.fold.eq(0)].copy();changed['f_'+perils[0]]*=2
        assert fit_business_mix(changed,perils)['weights']!=a['record']['mix']['weights']
        rows.append({'line':line,'full_new_learning_response_and_held_profile_poison_invariant':True,
                     'within_business_proportional_profile_matches_perrisk':True,'training_covariates_change_mix':True,
                     'future_zero_observed_marker_ultimate_positive':True,'moment_and_bridge':True})
    return {'author':'Codex','checks':rows,'new_contest_fits':0,'synthetic_closed_H3B_learners':6,'synthetic_reporting_fits':0}


def register():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir()
    assert w.read(P2/'report.json')['committed_scopes']==75
    files=[Path(__file__),Path(n.__file__),Path(frozen.__file__),Path(h.__file__),Path(b.__file__),Path(g.__file__),Path(v.__file__),
           P2/'report.json',P2/'held_nested_prices.parquet',P1/'report.json',P0/'report.json',P3/'report.json',P3/'held_frozen_scenario_prices.parquet',
           BASE/'atribucion_error_P3a_H1_20261026_v1/report.json',frozen.TARGET,
           BASE/'estimando_cartera2025_v3/weights.parquet',BASE/'estimando_cartera2025_v3/report.json',
           R/'registro/semana2_mision_privada_plan_v1.json',R/'registro/semana2_control_entregas_codex_actual.json']
    for k in range(5):files.append(P1/f'inner_groups_outer{k}.parquet')
    for line in h.LINES:
        files.append(P1/f'canonical_{line}.parquet')
        for outer in range(5):
            files += [P0/f'bridge_{line}_fold{outer}.parquet',BASE/f'tanda2_20261025_v1/learning_{line}_fold{outer}.json']
            for member in range(5):
                path=P2/f'scope_{line}_outer{outer}_member{member}'
                files += [path/'primary/C0.json',path/'member_ultimate.parquet',path/'committed.json']
    def nofit(*args,**kwargs):raise AssertionError('H3Bmust not refit reporting')
    oldfit=v.fit_reporting;v.fit_reporting=nofit
    try:dump(OUT/'synthetic_report.json',synthetic())
    finally:v.fit_reporting=oldfit
    files.append(OUT/'synthetic_report.json')
    plan={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'type':'H3B_simpler_business_source_mixture_nested_standard_assay',
          'hypothesis':'The individually varying source peril shares may transport poorly into sparse motorNB. A training-only NB/RENportfolio mixture restricts observation heterogeneity while preserving business composition. P3arelative-allocation loss motivates the test, not a causal proof.',
          'formula':'r_ip=f_period_ip*s_ip; f_period already contains calendar exposure. w_nb,p=sum_train_nb(r_ip)/sum_train_nb,p(r_ip), with no second exposure. q_i=sum_p(w_nb,p*savedq_ip). Same line/years pool within business; no year/region cells, pooling constant or tunable weight.',
          'learning':'Same nominalT0, original rounded exposure, source models, memberC0and nested splits. New H3BclosedN3/G3shape/levels/stages only; K300/K400unchanged. Every mixture uses member-training covariates only. No diagnostic oracle multiplier read as input.',
          'production':'For each outer, protected S2ultimate base and five fixed G3ultimate denominators fromP2; equal arithmetic mean base*H3Bultimate/G3ultimate. Apply outer H3Bbusinessmix q only after ultimate mean, for observed evaluation. Ultimate forward uses calendar once and its own prediction normalizers.',
          'outer_business_adapter':'Fit the analogous business source weights on outer training covariates only; old outer C0is evaluation-only and never used for inner learning.',
          'primary':'Nominal new H3Bmean versus protectedS2baseline','secondary':'Nominal H3Bmean versus existing H1mean',
          'frozen_scenarios':frozen.SCENARIOS,'scenario_contract':'Exactly P3a, with H3Bouterbusinessprofile replacing individualsourceprofile; trained ultimate prices frozen under every reserve/tail scenario. No scenario-specific recalibration.',
          'criterion':{'retained_nominal_delta_min':.002,'lower95_gt':0,'positive_folds_min':4,'both_years_nonnegative':True,'post31_nonnegative':True,'nominal_worst_cell_floor':-.001,
                       'required_robustness_guard':'All line/year/NBcells in all4frozen scenarios must be reported; losses below-.001fail. Do not hide regression outside the previously adverse motorNBcell.',
                       'interpretation':'No formal promotion, threshold change, publicscore selection or upload from this assay'},
          'bootstrap':{'replicates':2000,'seed':2026102622,'unit':'same globalcomponents','joint6':True,'family_interval':'exploratory Bonferroni6'},
          'weighted':'Frozen2025weights point sensitivity only, failedESSretained, no new weights/classifier/bootstrap',
          'controls':['Synthetic whole newlearning+ultimateforward with held response/sourceprofile poisoning',
                      'Businessmix independent scalar sums; proportional-within-business identity and futureq0markerignoredforultimate',
                      'All75real newmixture+learner+forward flows must match fullpoison control exactly',
                      'ParentC0exact member training keys; old wholeC0poisonreceipt pinned, no newcurvefit',
                      'Independent line moment, observed-ultimate bridge, fivecostmean and metric/weights; unchanged sourceSHA'],
          'budget':{'primary_closed_H3B_learners':75,'adverse_closed_learners_separate':75,'primary_price_constants_max':2000,
                    'primary_source_covariate_business_mixtures':150,'primary_derived_covariate_weights':750,
                    'outer_evaluation_business_mixtures':30,'outer_derived_covariate_weights':150,
                    'new_reporting_fits':0,'new_source_models':0,'new_source_inference':0,'new_final_test_prices':0,'new_submissions':0},
          'limits':['Adaptive search and inspected2023/2024, no pristine confirmation or professional independent validation',
                    'Complete S2proxy not actualF3chistoricalreplay; nested64percent versusproduction80percent',
                    'Changing observation hypotheses does not identify true ultimate mix/reserves/latecost or prove private performance',
                    'Source2024snapshot/masteravailability and failedweightedESSremain; all previous failures retained'],
          '2024_open':True,'B00_all_alternatives_preserved':True,'submission_allowed':False,
          'sources':{w.rel(p):w.sha(p) for p in files}}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md'
    body.write_text('Codex. Registro H3Bantes de ajustes reales: observación con mezcla fuente agregada por NB/REN, calculada con f*sdel entrenamiento de cada miembro y sin exposición duplicada. '
                    'La motivación es la pérdida relativa de P3aen autos nuevos bajo estrés; la agregación es una hipótesis de menor heterogeneidad, no una solución probada. '
                    'Se conservan etiquetas nominales, C0, fuente, particiones y reglas K300/K400. Se reutilizan los denominadores G3y las curvas protegidas; solo se aprenden75calibraciones H3By sus75controles reales. '
                    'Primario frente a S2, secundario frente a H1, más los cuatro escenarios congelados y todas las celdas, con bootstrap conjunto y bandas exploratorias para6contrastes. '
                    'La prueba sintética del flujo nuevo pasó para los tres ramos, incluida corrupción de respuestas y perfiles externos. '
                    'No se usan los multiplicadores oracle, nuevos árboles, C0oenvíos. Cualquier pérdida en otra celda se conservará. '
                    'Privada prioritaria,2024abierto adaptativo,B00/alternativas intactos y H1diferido. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    res=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
                        '--id','COD-S2-20261026-PRIVADA-H3B-PREVIO','--asunto','H3B registrada: mezcla por negocio con menor heterogeneidad, sin nuevos C0',
                        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(res.stdout)})
    print(json.dumps({'registered':True,'synthetic':w.read(OUT/'synthetic_report.json'),'forum':json.loads(res.stdout)}))


def summarize(meta,data,weight):
    codes,groups=pd.factorize(meta.group_id,sort=True);G=len(groups);nn=len(meta);counts=np.bincount(codes,minlength=G)
    gain=[];YY=[];SQ=[];null=[];rowgain=[]
    for y,base,candidate in data:
        gg=unit(y,base)-unit(y,candidate);rowgain.append(gg)
        gain.append(np.bincount(codes,weights=gg,minlength=G));YY.append(np.bincount(codes,weights=y,minlength=G));SQ.append(np.bincount(codes,weights=np.sqrt(y),minlength=G))
        null.append(float(unit(y,np.full(nn,y.mean())).sum()))
        assert abs(unit(y,candidate).mean()-mean_tweedie_deviance(y,candidate,power=1.5))<1e-8
    gain=np.column_stack(gain);YY=np.column_stack(YY);SQ=np.column_stack(SQ);rng=np.random.default_rng(2026102622);draws=[]
    for _ in range(2000):
        ii=rng.integers(0,G,G);number=counts[ii].sum();den=8*(np.sqrt(number*YY[ii].sum(axis=0))-SQ[ii].sum(axis=0))
        assert (den>0).all();draws.append(gain[ii].sum(axis=0)/den)
    draws=np.array(draws);np.save(OUT/'joint_six_bootstrap.npy',draws);result={}
    for j,name in enumerate(NAMES):
        y,base,candidate=data[j];gg=rowgain[j];den=null[j];cells=[]
        for (line,year,nb),ii in meta.groupby(['line','year','new_business']).groups.items():
            ii=np.asarray(list(ii));yy=y[ii];dd=unit(yy,np.full(len(ii),yy.mean())).sum()
            cells.append({'line':line,'year':int(year),'NB':int(nb),'rows':len(ii),'delta_global':float(gg[ii].sum()/den),'delta_cell_null':float(gg[ii].sum()/dd)})
        wm=float(np.average(y,weights=weight));wd=float(np.sum(weight*unit(y,np.full(nn,wm))))
        result[name]={'delta':float(gg.sum()/den),'bootstrap95':np.quantile(draws[:,j],[.025,.975]).tolist(),
                      'simultaneous95_six':np.quantile(draws[:,j],[.025/6,1-.025/6]).tolist(),
                      'post31_delta':float((gain[:,j].sum()-np.sort(gain[:,j])[::-1][:31].sum())/den),
                      'folds':{str(k):float(gg[meta.fold.eq(k)].sum()/den) for k in range(5)},
                      'years':{str(k):float(gg[meta.year.eq(k)].sum()/den) for k in [2023,2024]},'cells':cells,
                      'worst_cell_delta':min(c['delta_cell_null'] for c in cells),'weighted2025_point_only_ESS_failed':float(np.sum(weight*gg)/wd)}
    return result


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==z for p,z in plan['sources'].items())
    execution={'author':'Codex','pid':os.getpid(),'utc':datetime.now(timezone.utc).isoformat(),'script':w.rel(Path(__file__)),'output':w.rel(OUT),'kind':'H3B_nested_standard_learning'}
    dump(OUT/'started.json',execution);n.OUT=OUT;n.set_execution(execution)
    oldfit=v.fit_reporting;v.fit_reporting=lambda *a,**k:(_ for _ in ()).throw(AssertionError('No new C0fits in H3B'))
    try:
        scopes=w.read(P1/'report.json')['scopes'];frames={l:pd.read_parquet(P1/f'canonical_{l}.parquet') for l in h.LINES}
        for scope in scopes:
            outer,member,line=scope['outer'],scope['member'],scope['line'];full=frames[line]
            folder=OUT/f'scope_{line}_outer{outer}_member{member}';folder.mkdir(exist_ok=True)
            inner=pd.read_parquet(P1/f'inner_groups_outer{outer}.parquet').set_index('group_id').inner_fold
            train=full.fold.ne(outer)&full.group_id.map(inner).ne(member);held=full.fold.eq(outer)
            assert b.digest(sorted(full.loc[train,'row_id']))==scope['training_row_digest']
            f=full.loc[train|held].copy().reset_index(drop=True);f['fold']=np.where(f.fold.eq(outer),1,0)
            c0=w.read(P2/f'scope_{line}_outer{outer}_member{member}/primary/C0.json')
            primary=learn_scope(f,c0,line,folder/'primary','primary',OUT)
            bad=learn_scope(corrupt(f),c0,line,folder/'poison','poison',OUT)
            assert b.digest(primary['record'])==b.digest(bad['record']) and np.array_equal(primary['ultimate'],bad['ultimate'])
            frame=pd.DataFrame({'row_id':primary['row_id'],'U_H3B':primary['ultimate']});frame.to_parquet(folder/'member_ultimate.parquet',index=False)
            dump(folder/'committed.json',{'outer':outer,'member':member,'line':line,'new_learning_poison_exact':True,
                                          'bridge_max_relative_error':primary['bridge_max_relative_error'],
                                          'primary_ultimate_normalizers':primary['ultimate_normalizers'],
                                          'member_sha256':w.sha(folder/'member_ultimate.parquet')})
            print(json.dumps({'line':line,'outer':outer,'member':member,'complete':True}),flush=True)
        p=pd.read_parquet(P2/'held_nested_prices.parquet');ix=pd.Series(p.index.to_numpy(),index=p.row_id)
        nominal=np.full(len(p),np.nan);scenario_base=[np.full(len(p),np.nan) for _ in range(4)];scenario_new=[np.full(len(p),np.nan) for _ in range(4)]
        oldsc=pd.read_parquet(P3/'held_frozen_scenario_prices.parquet').set_index('row_id').loc[p.row_id]
        for line,full in frames.items():
            for outer in range(5):
                valid=full.loc[full.fold.eq(outer)].copy().reset_index(drop=True);train=full.loc[full.fold.ne(outer)]
                c0=w.read(BASE/f'tanda2_20261025_v1/learning_{line}_fold{outer}.json')['artifact']['C0']
                assert c0['fit_row_ids']==sorted(train.row_id)
                mix=fit_business_mix(train,sorted(c0['curves']));dump(OUT/f'outer_mix_{line}_fold{outer}.json',mix)
                bridge=pd.read_parquet(P0/f'bridge_{line}_fold{outer}.parquet').set_index('row_id').loc[valid.row_id]
                rr=[]
                for member in range(5):
                    hp=pd.read_parquet(OUT/f'scope_{line}_outer{outer}_member{member}/member_ultimate.parquet').set_index('row_id').loc[valid.row_id]
                    gp=pd.read_parquet(P2/f'scope_{line}_outer{outer}_member{member}/member_ultimate.parquet').set_index('row_id').loc[valid.row_id]
                    rr.append(hp.U_H3B.to_numpy()/gp.U_G3.to_numpy())
                UB=bridge.U_S2.to_numpy();UC=(UB[:,None]*np.column_stack(rr)).mean(axis=1);ii=ix.loc[valid.row_id].to_numpy()
                nominal[ii]=UC*business_completion(valid,c0,mix)
                for j,name in enumerate(frozen.SCENARIOS):
                    branch=.75 if name=='RESERVE075' else 1.25 if name=='RESERVE125' else 1.;tail=.05 if name=='TAIL005' else .1 if name=='TAIL010' else 0.
                    qg=frozen.completion(valid,c0,branch,tail)[0];q3=business_completion(valid,c0,mix,branch,tail)
                    scenario_base[j][ii]=UB*qg;scenario_new[j][ii]=UC*q3
                    assert np.allclose(UB*qg,oldsc[name+'_B'].to_numpy()[ii],rtol=2e-12,atol=1e-9)
        for x in [nominal,*scenario_base,*scenario_new]:assert np.isfinite(x).all() and (x>0).all()
        target=pd.read_parquet(frozen.TARGET,columns=['row_id','T1_reserve075','T1_reserve125']).set_index('row_id').loc[p.row_id]
        data=[(p.T0.to_numpy(),p.B.to_numpy(),nominal),(p.T0.to_numpy(),p.T_B.to_numpy(),nominal)]
        ys=[target.T1_reserve075.to_numpy(float),target.T1_reserve125.to_numpy(float),p.T0.to_numpy(),p.T0.to_numpy()]
        data += [(ys[j],scenario_base[j],scenario_new[j]) for j in range(4)]
        weights=pd.read_parquet(BASE/'estimando_cartera2025_v3/weights.parquet').set_index('row_id').loc[p.row_id]
        assert np.array_equal(weights.group_id,p.group_id)
        result=summarize(p,data,weights.weight.to_numpy())
        saved=p[['row_id','line','year','new_business','group_id','fold','T0']].copy();saved['H3B_nominal']=nominal
        for j,name in enumerate(frozen.SCENARIOS):saved[name+'_H3B']=scenario_new[j]
        saved.to_parquet(OUT/'held_H3B_prices.parquet',index=False)
        events=[json.loads(s) for s in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines()]
        counts={}
        for role in ['primary','poison']:
            ee=[e for e in events if e['kind']=='H3B_closed_completed' and e['role']==role]
            assert len(ee)==75
            constants={k:sum(e['constants'][k] for e in ee) for k in n.count_constants(w.read(OUT/'scope_motor_outer0_member0/primary/learning_H3B.json')['artifact'])}
            constants['price_total']=sum(constants[k] for k in ['shape_factors','levels','residual_factors','training_nuisance_levels'])
            counts[role]={'closed_learners':75,'constants':constants,'source_business_mixtures':150,'derived_covariate_weights':750}
        assert counts['primary']['constants']['price_total']<=2000
        assert all(w.sha(ROOT/path)==z for path,z in plan['sources'].items())
        primary=result['NOMINAL_VS_BASE']
        gates={'delta_ge002':primary['delta']>=.002,'lower95_positive':primary['bootstrap95'][0]>0,
               'at_least4positive_folds':sum(z>0 for z in primary['folds'].values())>=4,
               'both_years_nonnegative':min(primary['years'].values())>=0,'post31_nonnegative':primary['post31_delta']>=0,
               'nominal_cell_floor':primary['worst_cell_delta']>=-.001,
               'all_frozen_scenario_cell_floors':all(result[name]['worst_cell_delta']>=-.001 for name in frozen.SCENARIOS)}
        report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'H3B_business_source_mixture_nested_assay_complete',
                'results':result,'diagnostic_gates':gates,'counts':counts,'committed_scopes':75,
                'outer_covariate_mixtures_separate':30,'outer_derived_covariate_weights_separate':150,
                'new_reporting_fits':0,'new_source_models':0,'new_source_inference':0,'new_final_test_prices':0,'new_submissions':0,
                'old_G3_C0_estimators_reused_without_refit':True,'oracle_multipliers_not_read_as_model_inputs':True,
                'formal_promotion':False,'submission_allowed':False,'private_improvement_established':False,
                'limits':plan['limits'],'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,'plan_sha256':w.sha(PLAN)}
        dump(OUT/'report.json',report);n.set_execution(None)
        print(json.dumps({'results':{name:{k:a[k] for k in ['delta','bootstrap95','post31_delta','worst_cell_delta']} for name,a in result.items()},
                          'gates':gates,'counts':counts,'new_C0fits':0,'new_submissions':0},ensure_ascii=True))
    except Exception as exc:
        dump(OUT/'failure.json',{'utc':datetime.now(timezone.utc).isoformat(),'exception_type':type(exc).__name__,'message':str(exc),
                                 'committed_scopes':len(list(OUT.glob('scope_*/committed.json'))),'next':'Reconcile caches/handle; no blind refit'})
        n.set_execution(None);raise
    finally:v.fit_reporting=oldfit


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['register','run']);args=parser.parse_args()
    with threadpool_limits(limits=2):{'register':register,'run':run}[args.mode]()
