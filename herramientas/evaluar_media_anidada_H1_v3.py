"""Media H1 de cinco miembros: aprendizaje completo protegido y sin fuente nueva."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import ast
import shutil
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';PREF=BASE/'preflight_anidado_H1_20261026_v1'
BRIDGE=BASE/'puente_ultimo_observado_H1_20261026_v1'
OUT=BASE/'media_anidada_H1_20261026_v3';PLAN=R/'registro/semana2_media_anidada_H1_plan_v3.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
import psutil
from threadpoolctl import threadpool_limits


def load(name,path):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m


h=load('nested_H1_standard_learner',R/'herramientas/contrastar_enlace_HET.py')
metrics=load('nested_H1_grouped_metric',R/'herramientas/auditar_transferencia_PUL2.py')
w=h.w;b=h.b;g=h.g;v=b.v
CLAIMS=b.BASE/'claim_assignment_audit.parquet'
PHASE=R/'registro/semana2_mision017_fase2_actual.json'


def dump(path,value):
    with path.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)


def event(folder,kind,**fields):
    folder.mkdir(parents=True,exist_ok=True)
    with (folder/'events.jsonl').open('a',encoding='utf8') as f:
        f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'kind':kind,**fields},ensure_ascii=False)+'\n')
        f.flush();os.fsync(f.fileno())


def args_digest(args):
    d=hashlib.sha256()
    for arg in args:
        a=np.ascontiguousarray(np.asarray(arg))
        d.update(a.dtype.str.encode());d.update(str(a.shape).encode());d.update(a.tobytes())
    return d.hexdigest()


def count_constants(a):
    return {'shape_factors':sum(len(s['factors']) for s in a['shape']),
            'shape_training_normalizers_separate':sum(len(s['normalizers']) for s in a['shape']),
            'levels':3,'residual_factors':sum(len(s['factors']) for s in a['stages']),
            'training_nuisance_levels':sum(len(s['nuisance_year_business']) for s in a['stages']),
            'stage_calls':len(a['stages']),
            'training_stage_normalizers_separate':sum(len(s) for s in a['training_normalizers'].values()),
            'observed_held_stage_normalizers_separate':sum(len(s) for s in a['held_normalizers'].values())}


def attach_claim_year(claims,frames):
    metadata=pd.concat([f[['row_id','line','year']] for f in frames.values()],ignore_index=True)
    assert metadata.row_id.is_unique
    lookup=metadata.set_index('row_id')
    result=claims.drop(columns=['year'],errors='ignore').copy()
    result['year']=result.row_id.map(lookup.year)
    assigned=result.row_id.isin(lookup.index)
    assert np.array_equal(result.loc[assigned,'line'].to_numpy(),lookup.loc[result.loc[assigned,'row_id'],'line'].to_numpy())
    assert len(result)==len(claims) and np.array_equal(result.claim_id,claims.claim_id)
    return result


def poison(f,claims):
    bad=f.copy();held=bad.fold.eq(1);keys=set(bad.loc[held,'row_id'])
    bad.loc[held,'T0']=-1e30;bad.loc[held,'reserve']=1e30
    c=claims.copy();mask=c.row_id.isin(keys)
    c.loc[mask,'T0_cents']=np.int64(-(1<<61));c.loc[mask,'reserve_cents']=np.int64(1<<61);c.loc[mask,'included_in_T0']=True
    for col in ['peril','loss_date','report_date']:
        c[col]=c[col].astype(object);c.loc[mask,col]='__PROTECTED_INVALID__'
    return bad,c


def learn_and_forward(f,claims,line,folder,logfolder,scope,role):
    """The same real entry point is used in synthetic and contest scopes."""
    folder.mkdir(parents=True,exist_ok=True)
    train=f.fold.eq(0);held=f.fold.eq(1)
    assert (train|held).all() and train.any() and held.any()
    keys=set(f.loc[train,'row_id']);groups=set(f.loc[train,'group_id'])
    assert not groups.intersection(f.loc[held,'group_id'])
    assert all((f.loc[train&f.new_business.eq(n),'T0']>0).any() for n in [0,1])
    if g.STAGES[line]:
        assert all((f.loc[train&f.year.eq(y)&f.new_business.eq(n),'T0']>0).any() for y in [2023,2024] for n in [0,1])
    perils=sorted(c.removeprefix('f_') for c in f if c.startswith('f_'))
    cp=folder/'C0.json'
    if cp.exists():
        c0=w.read(cp);assert c0['fit_row_ids']==sorted(keys)
        event(logfolder,'reporting_scope_cache_reused',scope=scope,role=role)
    else:
        # A separate cache for each role forces the adverse control to really
        # refit; it cannot borrow a matching primary curve by argument digest.
        original=v.fit_reporting;sequence=[0]
        def fit_cached(*args,**kwargs):
            assert not kwargs
            peril=perils[sequence[0]];sequence[0]+=1
            path=folder/('curve_'+peril+'.json');signature=args_digest(args)
            if path.exists():
                cached=w.read(path);assert cached['argument_digest']==signature
                event(logfolder,'reporting_peril_cache_reused',scope=scope,role=role,peril=peril)
                return cached['model'],np.asarray(cached['prob_n'],float)
            event(logfolder,'reporting_peril_started',scope=scope,role=role,peril=peril,argument_digest=signature)
            model,prob=original(*args)
            dump(path,{'argument_digest':signature,'model':model,'prob_n':np.asarray(prob,float).tolist()})
            event(logfolder,'reporting_peril_completed',scope=scope,role=role,peril=peril,cache_sha256=w.sha(path))
            return model,prob
        v.fit_reporting=fit_cached
        try:_,c0=b.reporting_scope(f,claims,1)
        finally:v.fit_reporting=original
        assert sequence[0]==len(perils)
        dump(cp,c0);event(logfolder,'reporting_scope_completed',scope=scope,role=role,perils=len(perils))
    assert c0['fit_row_ids']==sorted(keys) and c0['excluded_fold']==1
    allowed_claims=claims.loc[claims.row_id.isin(keys)]
    allowed_claims=allowed_claims.loc[allowed_claims.included_in_T0]
    assert c0['fit_claim_ids']==sorted(allowed_claims.claim_id.tolist())
    assert set(c0['curves'])==set(perils)
    work=f.copy();qc=np.column_stack([v.average_completion(work,c0['curves'][p],'cost',1.) for p in perils])
    wr=np.column_stack([work['f_'+p].to_numpy(float)*work['s_'+p].to_numpy(float) for p in perils])
    assert np.isfinite(wr).all() and (wr>0).all() and (qc>=0).all() and (qc<=1).all()
    qg=qc@np.array([c0['mixture'][p] for p in perils]);qh=np.sum(wr*qc,axis=1)/wr.sum(axis=1)
    assert (qg>0).all() and (qh>0).all(),'Zero aggregate completion; no floor/fallback allowed'
    work['e_cost_scope']=work.exposure.to_numpy()*qg;work['e_source_mix']=work.exposure.to_numpy()*qh
    artifacts={};ultimate={};controls={};ultnorms=0
    for name,link in [('G3','e_cost_scope'),('H1','e_source_mix')]:
        path=folder/('learning_'+name+'.json')
        if path.exists():
            a=w.read(path);assert a['training_row_ids_digest']==b.digest(sorted(keys))
            observed,_=h.replay(work.loc[held],a)
            event(logfolder,'closed_learner_cache_reused',scope=scope,role=role,model=name)
        else:
            event(logfolder,'closed_learner_started',scope=scope,role=role,model=name)
            observed,a=h.learn(work,1,line,link)
            assert a['training_row_ids_digest']==b.digest(sorted(keys)) and a['training_groups_digest']==b.digest(sorted(groups))
            dump(path,a)
            event(logfolder,'closed_learner_completed',scope=scope,role=role,model=name,constants=count_constants(a),artifact_sha256=w.sha(path))
        valid=work.loc[held].copy();Er=valid.exposure.to_numpy(float);E=valid.exposure_calendar.to_numpy(float)
        valid['exposure']=E;u,nu=h.replay(valid,a,ultimate=True)
        assert np.isfinite(u).all() and (u>0).all()
        L=np.ones(len(valid));cellkeys=[f'{int(y)}|{int(n)}' for y,n in zip(valid.year,valid.new_business)]
        for variable,norm in nu.items():
            L*=np.array([norm[k]/a['held_normalizers'][variable][k] for k in cellkeys]);ultnorms+=len(norm)
        q=(qg if name=='G3' else qh)[held.to_numpy()]
        assert np.allclose(observed,u*(Er/E)*q*L,rtol=3e-12,atol=1e-9)
        # Independent scalar moment / first derivative of the learned line level.
        tr=work.loc[train];base=tr.annual_raw_T2b.to_numpy(float)*tr[link].to_numpy(float)
        for shape in a['shape']:base=b.shape_apply(tr,base,shape)
        y=tr.T0.to_numpy(float);sqrt=np.sqrt(base)
        independent=math.fsum((y/sqrt).tolist())/math.fsum(sqrt.tolist())
        assert math.isclose(independent,a['kshape'],rel_tol=3e-12,abs_tol=1e-12)
        mu=a['kshape']*base;derivative=math.fsum((np.sqrt(mu)-y/np.sqrt(mu)).tolist())
        scale=math.fsum((np.sqrt(mu)+y/np.sqrt(mu)).tolist())
        assert abs(derivative)/scale<3e-12
        artifacts[name]=a;ultimate[name]=u
        controls[name]={'bridge_max_relative_error':float(np.max(np.abs(observed/(u*(Er/E)*q*L)-1))),
                        'line_moment_relative_difference':abs(independent/a['kshape']-1),
                        'line_derivative_relative_residual':abs(derivative)/scale}
    return {'C0':c0,'artifacts':artifacts,'ultimate':ultimate,'controls':controls,
            'held_row_ids':work.loc[held,'row_id'].tolist(),'ultimate_prediction_normalizers':ultnorms}


def synthetic():
    rng=np.random.default_rng(2026102620);report=[];log=OUT/'synthetic'
    for line,perils in [('motor',['bodily_injury','glass_hail','own_damage','theft','third_party_prop']),
                        ('buildings',['accidental_damage','escape_of_water','fire','flood','storm','subsidence']),
                        ('contents',['accidental_damage','escape_of_water','flood','theft'])]:
        n=1000;year=rng.integers(2023,2025,n);groups=np.arange(n)//2
        E=np.where(year==2024,366/365,1.)
        f=pd.DataFrame({'row_id':[line+'s'+str(i) for i in range(n)],'line':line,'year':year,
                        'group_id':['syntheticg'+str(i) for i in groups],'fold':(groups%5==0).astype(int),
                        'new_business':rng.integers(0,2,n),'exposure':np.round(E,4),'exposure_calendar':E,
                        'period_start':pd.to_datetime(pd.Series(year).astype(str)+'-01-01'),
                        'period_end':pd.to_datetime(pd.Series(year).astype(str)+'-12-31'),'is_test':False,
                        'annual_raw_T2b':rng.uniform(40,200,n),'prior_claims_5y':rng.integers(0,3,n),
                        'ncb_years':rng.integers(0,15,n),'gender':rng.choice(['F','M'],n),
                        'works_from_home':rng.choice([True,False],n),'marketing_segment':rng.choice(['a','b','c'],n)})
        f['T0']=rng.gamma(2,80,n);f['reserve']=f.T0*.2
        for p in perils:f['f_'+p]=rng.uniform(.1,1,n);f['s_'+p]=rng.uniform(20,100,n)
        loss=pd.to_datetime(pd.Series(year).astype(str)+'-06-01')
        c=pd.DataFrame({'row_id':f.row_id,'claim_id':[line+'claim'+str(i) for i in range(n)],'line':line,
                        'year':year,'included_in_T0':True,'peril':rng.choice(perils,n),'loss_date':loss,
                        'report_date':loss+pd.to_timedelta(rng.integers(0,90,n),unit='D'),
                        'T0_cents':np.rint(f.T0.to_numpy()*100).astype(np.int64),'reserve_cents':np.rint(f.reserve.to_numpy()*100).astype(np.int64)})
        f['T0']=c.T0_cents.to_numpy()/100;f['reserve']=c.reserve_cents.to_numpy()/100
        original_c=c.copy()
        c=attach_claim_year(c.drop(columns=['year']),{line:f})
        assert c.drop(columns=['year']).equals(original_c.drop(columns=['year'])) and np.array_equal(c.year,original_c.year)
        primary=learn_and_forward(f,c,line,log/line/'primary',log,'synthetic_'+line,'primary')
        bad,badc=poison(f,c)
        adverse=learn_and_forward(bad,badc,line,log/line/'poison',log,'synthetic_'+line,'poison')
        assert b.digest(primary['C0'])==b.digest(adverse['C0'])
        assert b.digest(primary['artifacts'])==b.digest(adverse['artifacts'])
        assert all(np.array_equal(primary['ultimate'][k],adverse['ultimate'][k]) for k in ['G3','H1'])
        if line=='motor':
            changed=f.copy();cc=c.copy();sel=changed.fold.eq(0)&changed.prior_claims_5y.eq(0)
            changed.loc[sel,['T0','reserve']]*=2;cc.loc[cc.row_id.isin(changed.loc[sel,'row_id']),['T0_cents','reserve_cents']]*=2
            different=learn_and_forward(changed,cc,line,log/line/'training_changed',log,'synthetic_'+line,'training_changed')
            assert b.digest(different['C0'])!=b.digest(primary['C0']) and b.digest(different['artifacts'])!=b.digest(primary['artifacts'])
        ratio=primary['ultimate']['H1']/primary['ultimate']['G3'];base=rng.uniform(40,300,len(ratio));q=rng.uniform(.3,1,len(ratio))
        # Five identical members provide an exact limiting check of the cost mean.
        members=np.column_stack([base*ratio for _ in range(5)])
        result=members.mean(axis=1)*q
        assert np.allclose(result,base*ratio*q,rtol=3e-15,atol=1e-12)
        report.append({'line':line,'full_C0_and_both_closed_learners_held_poison_invariant':True,
                       'ultimate_forward_bridge_and_moment_controls':True,'equal_five_member_mean_identity':True})
    return {'author':'Codex','checks':report,'training_payload_changes_learning':True,
            'yearless_claim_ingress_matches_canonical_year_and_preserves_payload':True,'synthetic_only':True,'synthetic_reporting_peril_fits':35,'synthetic_closed_learner_calls':14,
            'source_model_fits':0,'contest_fits':0,'submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir()
    previous=BASE/'media_anidada_H1_20261026_v2'
    failures=list(previous.glob('failure_*.json'));assert len(failures)==1
    failure=w.read(failures[0]);assert failure['counts']['primary']['reporting_peril_completed']==5
    assert failure['counts']['primary']['closed_learner_completed']==2 and failure['counts']['poison']['reporting_peril_completed']==0
    frozen=previous/'registered_script_v2.py'
    def bodies(path):
        return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text(encoding='utf8')).body if isinstance(n,ast.FunctionDef)}
    oldbody,newbody=bodies(frozen),bodies(Path(__file__))
    stable=['learn_and_forward','attach_claim_year','args_digest','count_constants']
    assert all(oldbody[n]==newbody[n] for n in stable)
    oldfolder=previous/'scope_motor_outer0_member0/primary'
    newfolder=OUT/'scope_motor_outer0_member0/primary';newfolder.mkdir(parents=True)
    copied=[]
    for path in oldfolder.glob('*.json'):
        target=newfolder/path.name;shutil.copyfile(path,target);assert w.sha(target)==w.sha(path);copied.append(target)
    assert len(list(newfolder.glob('curve_*.json')))==5 and (newfolder/'learning_G3.json').exists() and (newfolder/'learning_H1.json').exists()
    shutil.copyfile(previous/'events.jsonl',OUT/'inherited_fit_events.jsonl')
    dump(OUT/'reuse_predecessor.json',{'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
        'reason':'V2adverse payload overflowed int64; primary numerical code unchanged, fitted primary curves/learners preserved without fitting again.',
        'failure':w.rel(failures[0]),'failure_sha256':w.sha(failures[0]),'stable_primary_function_AST':stable,
        'reused_reporting_peril_fits':5,'reused_closed_learners':2,
        'copied_cache':{w.rel(p):w.sha(p) for p in copied},'inherited_events_sha256':w.sha(OUT/'inherited_fit_events.jsonl')})
    pre=w.read(PREF/'report.json');assert pre['all75scopes_numerically_supported'] and len(pre['scopes'])==75
    assert not w.read(R/'registro/semana2_control_entregas_codex_actual.json')['allow_new_submission']
    files=[Path(__file__),Path(h.__file__),Path(b.__file__),Path(g.__file__),Path(v.__file__),Path(metrics.__file__),
           OUT/'reuse_predecessor.json',OUT/'inherited_fit_events.jsonl',frozen,failures[0],*copied,BASE/'media_anidada_H1_20261026_v1/defect_before_real_start.json',BASE/'media_anidada_H1_20261026_v1/registered_script_v1.py',CLAIMS,PREF/'report.json',R/'registro/semana2_preflight_anidado_H1_plan_v1.json',
           BRIDGE/'report.json',BRIDGE/'held_production_bridge_prices.parquet',
           R/'registro/semana2_mision_privada_plan_v1.json',R/'registro/semana2_control_entregas_codex_actual.json']
    for item in pre['outputs']:
        p=ROOT/item['path'];assert w.sha(p)==item['sha256'];files.append(p)
    for line in h.LINES:
        for outer in range(5):files.append(BRIDGE/f'bridge_{line}_fold{outer}.parquet')
    dump(OUT/'synthetic_report.json',synthetic())
    files.append(OUT/'synthetic_report.json')
    plan={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'type':'complete_nested_five_member_standard_H1_correction',
          'repair_v2':'Adverse cents now use representable int64 values; synthetic input uses actual integer-cent schema. Primary learner core unchanged by AST. Reuse5C0and2closedlearners with exact cached signatures; inherited fit events count them once. No split/hyperparameter/criterion change.',
          'repair_v1_before_real_learning':'Prepared claims lack year. Attach period year by unique row metadata; preserve unassigned keys/order. V1had no real fits. Same estimator/splits/criteria/budget, yearless ingress included in synthetic full-flow check.',
          'hypothesis':'A fixed arithmetic mean of five protected standard H1corrections can preserve the single-member improvement with less dependence on one fitted target observation/calibration scope. Evaluate the delivered algorithm before spending submission quota.',
          'priority':'Private-generalization evidence first, public secondary. Direct participant opened2024; no pristine holdout claim.',
          'partition_contract':'P1frozen SHA256innergroups; five unchanged global outer folds. For every line/outer/member, train only outer!=held and inner!=member. Inner-excluded rows are entirely absent from that member learner.',
          'training':'Same reverse-truncation reporting estimator and b1costCDF/target peril mixture, refitted from selected training claims; sourcef*sper-risk H1profile frozen. Same NCB/prior K300, business shrink K400 and G3residual K300. No coefficient/seed/weight/level search or new model capacity.',
          'primary_algorithm':'Protected outerS2ultimate base fromP0; member cost=base*(H1ultimate_member/G3ultimate_member). Equal arithmetic mean of five costs, then multiply common protected outerq_source for observed evaluation. Baseline is the storedP0S2ultimate*q_global. No normalization after observation. Calendar exposure exactly once in ultimateforward; original rounded exposure in learning.',
          'outer_adapter_role':'Old outer C0/proxy base are evaluation-only, not inner-independent training inputs. Canonical member inputs have inherited target prices/q/exposures removed. No outer held target enters these parent artifacts.',
          'primary_comparison':'Nested corrected complete feasible S2proxy versus its production-bridge baseline',
          'declared_secondary':'New nested correction versus the previously frozen single-member P0correction, using common paired draws; no old single-member-versus-base assay repeated.',
          'criterion':{'delta_ge':.002,'lower95_gt':0,'positive_folds_min':4,'both_years_nonnegative':True,'post31_nonnegative':True,'worst_cell_floor':-.001,
                       'interpretation':'Retained exploratory diagnostic gates, not formal promotion or automatic submission; report every failure.'},
          'bootstrap':{'replicates':2000,'seed':2026102620,'unit':'stored global customer/address components','joint_primary_secondary':True,'family_interval':'exploratory Bonferroni2'},
          'level_sensitivity':[.95,1.,1.05],
          'controls':['Full actual C0+G3/H1learning+ultimateforward must be invariant to outer held cost/reserve/peril/report/lossdate corruption in every75scope',
                      'Adverse roles genuinely refit their own curves/learners; primary caches cannot satisfy the control',
                      'Training row/claim/group digests match P1; both business and nuisance year/business cells have positive training costs',
                      'Independent scalar line moment/firstderivative, observed-to-ultimate bridge, arithmetic mean and Tweedie metric',
                      'Per-peril and per-learner caches/events preserve partial work; source/code hashes frozen; no blind live-job restart'],
          'budget':{'new_iterative_price_models':0,'new_source_models':0,'new_source_inference':0,
                    'primary_reporting_peril_fits':375,'adverse_reporting_peril_fits_separate':375,
                    'primary_closed_G3_H1_learner_calls':150,'adverse_closed_learner_calls_separate':150,
                    'primary_pricing_constants_max':4000,'primary_reporting_frequency_constants':375,
                    'primary_reporting_mark_means_threebranches_separate':1125,
                    'primary_member_ultimate_price_rows':2*5*109296,'adverse_member_ultimate_rows_separate':2*5*109296,
                    'final_test_prices':0,'new_submissions':0},
          'failure_policy':'No floor, case removal, split change or silently missing member. Commit completed substeps by scope/role; retain failure receipts and fit events. Resume only unchanged pinned code with prior job confirmed terminal.',
          'limits':['Prior adaptive2023/2024selection remains even with nested evaluation; not independent confirmation or professional review',
                    'Nested members learn about64percent of targetrows versus80percent in production; same algorithm but training-size mismatch',
                    'Full feasible S2proxy is not actual deliveredF3chistorical replay','Source2024snapshot and undated masters conditional; true ultimate riskmix/reportingtail/reserve adequacy not identified',
                    'Existing reserve/tail NB adverses and weightedESSfailure remain; this unit does not rerun those sensitivities',
                    'Public/hidden private improvement not established by local delta; H1delivery stays explicitly deferred'],
          '2024_open':True,'B00_all_alternatives_preserved':True,'submission_allowed':False,
          'sources':{w.rel(p):w.sha(p) for p in files}}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md'
    body.write_text('Codex. V2se detuvo al fabricar el control adverso con un importe que no cabe en int64. V3usa enteros representables y fixtures con los tipos reales; preserva el fallo y reutiliza5curvas y2calibraciones primarias cuyo núcleo numérico es idéntico por AST. Los eventos heredados se cuentan una sola vez. Sin cambio de receta, particiones o umbrales. Enmienda de entrada antes de cualquier ajuste real: el audit oficial de siniestros no contiene año y se adjunta por metadatos únicos de periodo, sin cambiar el contenido de costes o grupos. V1y su defecto se conservan con cero ajustes reales. La prueba completa ahora empieza por ese mismo ingreso sin año. Registro P2 antes de ajustes reales: evaluación numérica anidada del promedio de cinco correcciones H1 estándar. '
                    'Se conservan los75ámbitos de P1, sus grupos y la receta de credibilidad/factores. Cada miembro ajustará su C0 y G3/H1 exclusivamente con su entrenamiento, '
                    'y avanzará a último con calendario/normalizadores de producción. La media de costes se observará mediante el adaptador exterior protegido, sin usarlo para aprender miembros. '
                    'Se comparará contra S2último*qglobal y, como secundario declarado, la corrección de un miembro ya congelada. '
                    'La prueba sintética del flujo completo pasó para los tres ramos, incluyendo C0, ambos aprendices, corrupción retenida, puente y media. '
                    'Presupuesto375curvas primarias y375controles adversos separados,150aprendizajes cerrados primarios y150controles; cero modelos fuente, nuevas capacidades o envíos. '
                    'Se guardarán eventos/cachés por peril/modelo/ámbito para conciliar interrupciones. No se cambiarán particiones, mínimos o pesos por el resultado. '
                    'La revisión es adaptativa y usa S2como proxy completo, no reproduce F3c ni prueba la privada. Entrenamiento64%frente a80%de producción, reservas/cola/ESSsiguen limitando. '
                    'B00/alternativas intactos,2024abierto; H1diferido. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    res=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
                        '--id','COD-S2-20261026-PRIVADA-MEDIA-H1-V3-PREVIO',
                        '--asunto','P2 privado: media anidada H1 registrada y flujo sintético comprobado',
                        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(res.stdout)})
    print(json.dumps({'registered':True,'synthetic':w.read(OUT/'synthetic_report.json'),'forum':json.loads(res.stdout)}))


def fit_counts():
    path=OUT/'events.jsonl';events=[json.loads(s) for s in path.read_text(encoding='utf8').splitlines()] if path.exists() else []
    inherited=OUT/'inherited_fit_events.jsonl'
    if inherited.exists():events=[json.loads(s) for s in inherited.read_text(encoding='utf8').splitlines()]+events
    result={}
    for role in ['primary','poison']:
        selected=[e for e in events if e.get('role')==role]
        completed=[e for e in selected if e['kind']=='closed_learner_completed']
        constants={key:sum(e['constants'][key] for e in completed) for key in ['shape_factors','shape_training_normalizers_separate','levels','residual_factors','training_nuisance_levels','stage_calls','training_stage_normalizers_separate','observed_held_stage_normalizers_separate']}
        constants['pricing_constants_total']=sum(constants[k] for k in ['shape_factors','levels','residual_factors','training_nuisance_levels'])
        result[role]={'reporting_peril_started':sum(e['kind']=='reporting_peril_started' for e in selected),
                      'reporting_peril_completed':sum(e['kind']=='reporting_peril_completed' for e in selected),
                      'closed_learner_started':sum(e['kind']=='closed_learner_started' for e in selected),
                      'closed_learner_completed':len(completed),'constants':constants}
    return result


def set_execution(value):
    cuts=OUT/'execution_state_cuts'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');cuts.mkdir(parents=True)
    current=w.read(PHASE)
    if value is not None:assert current.get('active_execution') is None and not current.get('active_jobs')
    elif current.get('active_execution') is not None:assert current['active_execution'].get('pid')==os.getpid()
    w.update(PHASE,{'active_execution':value,'active_jobs':[] if value is None else [value]},cuts)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(active_jobs=[] if value is None else [value])
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':value},cuts)


def run(resume=False):
    assert not (OUT/'report.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    if resume:
        old=w.read(OUT/'execution_last.json')
        try:
            proc=psutil.Process(old['pid']);cmd=proc.cmdline()
            assert not any(Path(a).name==Path(__file__).name for a in cmd),'Same job is still live; do not resume'
        except psutil.NoSuchProcess:pass
    else:assert not (OUT/'started.json').exists()
    execution={'author':'Codex','pid':os.getpid(),'utc':datetime.now(timezone.utc).isoformat(),
               'script':w.rel(Path(__file__)),'output':w.rel(OUT),'kind':'nested_H1_local_standard_learning'}
    if not resume:dump(OUT/'started.json',execution)
    last=OUT/'execution_last.json'
    if last.exists():
        cuts=OUT/'resume_cuts'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');cuts.mkdir(parents=True);w.update(last,execution,cuts)
    else:dump(last,execution)
    set_execution(execution)
    try:
        pre=w.read(PREF/'report.json');scopes=pre['scopes'];frames={line:pd.read_parquet(PREF/f'canonical_{line}.parquet') for line in h.LINES}
        claims=attach_claim_year(pd.read_parquet(CLAIMS),frames)
        for scope in scopes:
            outer,member,line=scope['outer'],scope['member'],scope['line'];tag=f'{line}|{outer}|{member}'
            folder=OUT/f'scope_{line}_outer{outer}_member{member}';folder.mkdir(exist_ok=True)
            commit=folder/'committed.json'
            if commit.exists():
                cached=w.read(commit)
                assert all(w.sha(ROOT/p)==v for p,v in cached['outputs'].items())
                print(json.dumps({'scope':tag,'committed_reused':True}),flush=True);continue
            full=frames[line]
            inner=pd.read_parquet(PREF/f'inner_groups_outer{outer}.parquet').set_index('group_id').inner_fold
            training=full.fold.ne(outer)&full.group_id.map(inner).ne(member);held=full.fold.eq(outer)
            assert b.digest(sorted(full.loc[training,'row_id']))==scope['training_row_digest']
            f=full.loc[training|held].copy().reset_index(drop=True);f['fold']=np.where(f.fold.eq(outer),1,0)
            c=claims.loc[claims.line.eq(line)].copy()
            primary=learn_and_forward(f,c,line,folder/'primary',OUT,tag,'primary')
            bad,badc=poison(f,c)
            adverse=learn_and_forward(bad,badc,line,folder/'poison',OUT,tag,'poison')
            assert b.digest(primary['C0'])==b.digest(adverse['C0'])
            assert b.digest(primary['artifacts'])==b.digest(adverse['artifacts'])
            assert primary['held_row_ids']==adverse['held_row_ids']
            assert all(np.array_equal(primary['ultimate'][k],adverse['ultimate'][k]) for k in ['G3','H1'])
            ratio=primary['ultimate']['H1']/primary['ultimate']['G3']
            result=pd.DataFrame({'row_id':primary['held_row_ids'],'U_G3':primary['ultimate']['G3'],'U_H1':primary['ultimate']['H1'],'ratio':ratio})
            path=folder/'member_ultimate.parquet';result.to_parquet(path,index=False)
            outputs=[path]+list((folder/'primary').glob('*.json'))+list((folder/'poison').glob('*.json'))
            receipt={'scope':tag,'outer':outer,'member':member,'line':line,'primary_and_full_poison_learning_exact':True,
                     'controls':primary['controls'],'training_row_digest':scope['training_row_digest'],
                     'primary_ultimate_normalizers':primary['ultimate_prediction_normalizers'],
                     'adverse_ultimate_normalizers_separate':adverse['ultimate_prediction_normalizers'],
                     'outputs':{w.rel(p):w.sha(p) for p in outputs}}
            dump(commit,receipt)
            print(json.dumps({'scope':tag,'complete':True,'held_rows':len(result)}),flush=True)
        p=pd.read_parquet(BRIDGE/'held_production_bridge_prices.parquet')
        p['SINGLE']=p.T_B.to_numpy();p['T_B']=np.nan;p['T_SINGLE']=np.nan
        ix=pd.Series(p.index.to_numpy(),index=p.row_id);dispersion=[];checks=[]
        for line in h.LINES:
            for outer in range(5):
                bridge=pd.read_parquet(BRIDGE/f'bridge_{line}_fold{outer}.parquet')
                ratios=[]
                for member in range(5):
                    record=pd.read_parquet(OUT/f'scope_{line}_outer{outer}_member{member}/member_ultimate.parquet').set_index('row_id').loc[bridge.row_id]
                    ratios.append(record.ratio.to_numpy())
                rr=np.column_stack(ratios);costs=bridge.U_S2.to_numpy()[:,None]*rr
                corrected=costs.mean(axis=1)*bridge.q_source.to_numpy()
                independent=bridge.U_S2.to_numpy()*np.array([math.fsum(row.tolist())/5 for row in rr])*bridge.q_source.to_numpy()
                assert np.allclose(corrected,independent,rtol=3e-14,atol=1e-9)
                ii=ix.loc[bridge.row_id].to_numpy()
                assert np.allclose(p.loc[ii,'B'],bridge.U_S2*bridge.q_global,rtol=2e-15,atol=1e-9)
                p.loc[ii,'T_B']=corrected;p.loc[ii,'T_SINGLE']=corrected
                spread=rr.max(axis=1)/rr.min(axis=1)
                for (year,nb),jj in bridge.groupby(['year','new_business']).groups.items():
                    jj=np.asarray(list(jj));dispersion.append({'line':line,'outer':outer,'year':int(year),'NB':int(nb),
                                                               'member_ratio_max_min_quantiles':np.quantile(spread[jj],[.5,.9,.99,1.]).tolist()})
                checks.append({'line':line,'outer':outer,'five_member_cost_mean_scalar_parity':True,'baseline_reused_P0exact':True})
        assert p[['B','T_B','SINGLE','T_SINGLE']].notna().all().all()
        p.to_parquet(OUT/'held_nested_prices.parquet',index=False)
        metrics.OUT=OUT
        result=metrics.metrics(p,['B','SINGLE'],plan,'joint_primary_secondary')
        primary=result['B'];primary['worst_cell_delta']=min(c['delta_cell_null'] for c in primary['cells'])
        primary['diagnostic_gates']={'delta_ge002':primary['delta']>=.002,'lower95_positive':primary['bootstrap95'][0]>0,
                                     'at_least4positive_folds':sum(x>0 for x in primary['folds'].values())>=4,
                                     'both_years_nonnegative':min(primary['years'].values())>=0,
                                     'post31_nonnegative':primary['post31_delta']>=0,'worst_cell_ge_minus001':primary['worst_cell_delta']>=-.001}
        counts=fit_counts()
        assert all(counts[role]['reporting_peril_completed']==375 and counts[role]['closed_learner_completed']==150 for role in ['primary','poison'])
        assert counts['primary']['constants']['pricing_constants_total']<=4000
        assert all(w.sha(ROOT/path)==v for path,v in plan['sources'].items())
        report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'nested_five_member_H1_correction_evaluation_complete',
                'primary':primary,'secondary_nested_minus_frozen_single':result['SINGLE'],'member_dispersion':dispersion,'mean_controls':checks,
                'committed_scopes':75,'counts':counts,'predecessor_primary_reporting_fits_reused':5,'predecessor_primary_closed_learners_reused':2,'new_primary_reporting_fits_in_v3':370,'new_iterative_price_fits':0,'new_source_models':0,'new_source_inference':0,
                'new_final_test_prices':0,'new_submissions':0,'synthetic_costs_excluded_from_real_counters':w.read(OUT/'synthetic_report.json'),
                'complete_nested_correction_given_protected_S2base':True,'complete_actual_F3c_learning_replay':False,
                'formal_promotion':False,'submission_allowed':False,'limits':plan['limits'],'2024_open':True,
                'B00_all_alternatives_preserved':True,'private_improvement_established':False,'goal_achieved':False,'plan_sha256':w.sha(PLAN)}
        dump(OUT/'report.json',report);set_execution(None)
        print(json.dumps({'primary':{k:primary[k] for k in ['delta','bootstrap95','post31_delta','worst_cell_delta','years','folds','diagnostic_gates']},
                          'secondary':{k:result['SINGLE'][k] for k in ['delta','bootstrap95','post31_delta']},'counts':counts,'new_submissions':0},ensure_ascii=True))
    except Exception as exc:
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        dump(OUT/('failure_'+stamp+'.json'),{'utc':datetime.now(timezone.utc).isoformat(),'exception_type':type(exc).__name__,
                                          'message':str(exc),'counts':fit_counts(),'committed_scopes':len(list(OUT.glob('scope_*/committed.json'))),
                                          'next':'Reconcile same handle/cache before any resume; no blind restart or split/criterion change'})
        set_execution(None);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['register','run','resume']);args=parser.parse_args()
    with threadpool_limits(limits=2):
        if args.mode=='register':register()
        else:run(resume=args.mode=='resume')
