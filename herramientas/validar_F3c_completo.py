"""F3c: familia completa temporal, sin sustituir el CSV enviado.

Reutiliza curvas verificadas y T2b; completa A1 con/sin F1 y tres semillas.
El legado publico se conserva como condicionamiento historico, no confirmacion.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,ast,gc,importlib.util,json,math,os,subprocess,sys,time
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import lightgbm as lgb
import psutil
from threadpoolctl import threadpool_limits
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=module('F3_full_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
a=module('F3_full_old_helpers',R/'herramientas/ampliar_validacion_cadena_f3c.py')
v=a.v;sha=v.sha;read=v.read
BASE=R/'privado/semana2/mision017_fase2'
OUT=BASE/'F3c_validacion_completa_20261027'
ACTIVE=a.RUN;PARENT=a.PARENT
PLAN=R/'registro/semana2_F3c_completo_validacion_plan.json'
INDEX=R/'registro/semana2_F3c_completo_validacion_actual.json'
DOC=R/'docs/semana2/F3C_VALIDACION_COMPLETA_20261027.md'
LEGACY=R/'privado/reentrenamiento_completo_20261026/corrida'
ORIGINAL=R/'privado/semana2/claude_mision017_20261025/F3c_2025.csv'
ORIGINAL_SHA='5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276'
PUBLIC=ROOT/'Hackaton/Semana 2/Claude/mision017_20261025/final_info_3puntos.json'
TRAIN_SHAPE=R/'src/semana2/lineas/mision017_20261025/exp26_20261026/m017/exp26/F3b_info.json'
SEEDS=[11,12,13];LINES=['motor','buildings','contents']
HISTORY_ADMISSION=OUT/'source_history_admission.json'
EXECUTION_RECONCILIATION=OUT/'execution_reconciliations.json'

def additional_interrupted(line=None):
    if not EXECUTION_RECONCILIATION.exists():return 0
    rec=read(EXECUTION_RECONCILIATION);counts=rec['additional_interrupted_by_line']
    assert len(rec['cases'])==sum(counts.values())
    return counts.get(line,0) if line else sum(counts.values())

def source_folder(line,tag,family,seed):
    namespace='source_original_history' if family=='F1' and HISTORY_ADMISSION.exists() else 'source'
    return OUT/namespace/line/tag/f'{family}_seed{seed}'

def source_marker(line):return OUT/(line+('_original_history' if HISTORY_ADMISSION.exists() else '')+'_source_complete.json')
def attempt_path(line):return OUT/(('fit_attempts_original_history_' if HISTORY_ADMISSION.exists() else 'fit_attempts_')+line+'.jsonl')
def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,obj):
    encoded=json.dumps(v.clean(obj),ensure_ascii=False,indent=2,allow_nan=False)+'\n';path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf8') as f:f.write(encoded)
def live(name,obj):
    path=OUT/(name+'.json');tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(v.clean({'utc':utc(),**obj}),ensure_ascii=False,indent=2),encoding='utf8');os.replace(tmp,path)
def post(body,identifier,subject):
    path=OUT/(identifier+'.md');path.write_text(body,encoding='utf8')
    q=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',identifier,'--asunto',subject,'--cuerpo',str(path)],capture_output=True,text=True,encoding='utf8',check=True)
    return json.loads(q.stdout)
def source_paths():
    paths=[Path(__file__),Path(a.__file__),Path(v.__file__),PUBLIC,TRAIN_SHAPE,ORIGINAL,LEGACY/'m017/exp26/F3c_2025.csv',
        R/'registro/reentrenamiento_originales_actual.json',LEGACY.parent/'comparacion_final.json',ACTIVE/'curves_full.json',ACTIVE/'source_training_complete.json',ACTIVE/'prediction_checks.json',
        ACTIVE/'prepared/emerging_claims.parquet',ACTIVE/'prepared/developed_claims.parquet',PARENT/'baseline_parameters.json',PARENT/'training2023.parquet',
        BASE/'revision_chat_documento_20261027/policy_T2b.parquet',ACTIVE/'composition_bootstrap_T2b.npz',ACTIVE/'target2024_sealed.parquet',
        R/'src/semana2/lineas/mision017_20261025/codigo/construir_F2.py',R/'src/semana2/lineas/mision017_20261025/codigo/construir_final.py',
        R/'src/semana2/lineas/mision017_20261025/exp26_20261026/m017/construir_F3b.py',R/'src/semana2/lineas/mision017_20261025/exp26_20261026_v2/m017/construir_F3c.py',
        LEGACY/'noche/codigo/desarrollado_gbm.py',LEGACY/'noche/codigo/variables.py',R/'src/semana2/lineas/ml_independiente_20261023/codigo/produccion.py',R/'src/semana2/lineas/ml_independiente_20261023/codigo/receta.py']
    for line in LINES:
        paths += [ACTIVE/'prepared'/f'{market}_{line}.parquet' for market in ['developed','emerging']]
        paths += [ACTIVE/'models'/scope/(line+suffix) for scope in ['full','replay_2024'] for suffix in ['_receipt.json','.txt','_raw.parquet']]
        paths += [PARENT/'models/baseline'/(line+suffix) for suffix in ['.txt','_receipt.json','_raw.parquet']]
        paths += [LEGACY/'noche/salidas/transfer'/f'gbm_{tag}_{line}.txt' for tag in (['dev21222324_v2fixf1','dev21222324_v2fixf1s12','dev21222324_v2fixf1s13'] if line=='motor' else ['dev21222324_v2f1','dev21222324_v2f1s12','dev21222324_v2f1s13'])]
    return paths
def freeze():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists();OUT.mkdir()
    assert sha(ORIGINAL)==sha(LEGACY/'m017/exp26/F3c_2025.csv')==ORIGINAL_SHA
    public=read(PUBLIC);am=read(TRAIN_SHAPE)['a_motor_1']
    plan={'author':'Codex','utc':utc(),'request':'Register and validate F3c with complete trunk/preprocessing; private robustness; preserve current submission; no submission without evidence.',
      'purpose':'Separate exact production-retraining reproduction already completed from new temporal full-structure evaluation. Do not call one-seed/noF1T2b a complete F3c validation.',
      'primary_evaluation':'Train all new learning on emerging2023 and developed2021-23, apply59202rows2024.2024isalreadyadaptive and valuation2024retrospective. Report fullstructure/frozenpublicblocks as historically conditioned, not independent private proof.',
      'source_full_structure':{'A1':'N0andF1 families, each geometricmean of seeds11,12,13. Same49/41/42N0fields; F1adds accepted priorpolicynotifications and years since first observed inception. No new feature or seed search.',
        'F1':'Use accepted assigned notices reported before inception, original calendar-history duration definition. Future acceptance-vintage and2025duration availability remain unproven; do not silently replace with A1S.',
        'model':'HistoricalA1 lr.02,31leaves,minleaf1000,L2=10,sourceinternal componentfold0 max4000/patience400; inner/full curve/categories/offsetinitialrate protected withinsource scopes. N0seed11cached full/replay reused only if argument/model/raw hashes agree.',
        'curves':'Reuse verified pooledsource<=2023/emerging2023 full andsourceinnerfold0-excluded RKM curves. No newC0. Different from source-onlyA1S. Held2024excluded from ancestors; original internalOOF training is not declared unbiased because shared trainingcurve includes2023labels.',
        'target_N0_F1':'Balance levels (sumy/sumobservedmu), neutralize F1 to N0applyportfolio total perramo without heldlabels. Allthree seed logmeans and both families retained.',
        'T2b':'Reuse audited source2021-23 three models. Recreate leavefold levels and actual C1secondramocalibration on2023OOF only; primary target-level crossfit cached historicalfolds. No newT2bmodel.',
        'mix':'50%annualneutralA1F1+50%annualT2bC1; fixed. Downstream observationbridge uses commonT2bq, as actualm017labels. Additionalq-mix description only, no score-based bridge choice.'},
      'preprocessing_full_structure':{'F2':'TrainNCBthenpriorAEfactors n/(n+300) onT2bOOF2023, portfolio-cellnormalization aslegacy; motorrenewalshape.9. F2levelratio estimated2023only.',
        'public_blocks':{'g':public['nivel']['g'],'NB_shapes':{k:z['a_cred'] for k,z in public['forma'].items()},'cell_level_relative_to_g':{k:z/public['nivel']['g'] for k,z in public['nivel']['cred'].items()},'own_training_motor_NB_shape_A_M1':am},
        'own':'Gender motor/contents, worksfromhome andmarketing contents, K300, learnedonT2bOOF2023 afterF2/commonshape andfrozenA_M1 aslegacy. Apply tofull mixture afterpublicshapes; batch-cellnormalizers andtraining-only ownlevelratio.',
        'historical_local_level_ratios':'Actualproduction uses2023/2024views; temporalcut makes2024unavailable forlearning. Use availableT2bOOF2023 only for F2/shape/own local ratios. Record this unavoidable temporal adaptation, never relabel exact2025CSV as clean holdout.',
        'secondary':'Samefull source/variables/F2andown coefficients with publicg/NBshapes/cellfactors removed; final sixcelllevels learned ontrainingmixtureOOF2023. Called training-only LEVEL calibration, not globallypublic-free because originalhyperparameters andA_M1 historicallychosen.',
        'exact_file_lane':'Verify existing full native retraining comparison, sourceobjects/columns andbyteexactF3c209063CSV; reuse ratherthan repeat it. Reproduction is not prospective validation.'},
      'comparisons':['primaryfullpublicstructure minus samepublicstructure noown','training-onlylevel full minus sameview noown','primaryfullpublicstructure minus training-onlylevel full'],
      'criteria':{'conditional_family':18,'scope':'15previous contrasts plus3new; not full adaptive search coverage','global_margin':.0005,'broad_and_sixcell_floor':-.001,'NB_point_nonnegative':True,'NB_lower95_floor':-.001,'positive_savedfolds_min':4,'influence_remove':'max(5,ceil(.001*G)); delta>=0 after top favorablegroups','tail':'Report top1%positivecost andduration/mix strata, no deletion or clipping','stress':'50fixed-price existinglabelscenarios, no probabilities; target/source learning stress remains separate if relevant','production_consequence':'No replacement or newsubmission from thisunit, even conditionalgatespass. Preserve originalfile and identify timing/reserve/futuresupport limits.'},
      'controls':['Four real syntheticGBMfits for family/history/category/heldpoison/positivechange flow','Real newsource models re-fit under source/emerging2024cost poison: arguments/model/raw/rounds equal; frozen ancestor curves retain their independent prior proofs','Targetfit2024poison does not alter any newtrain parameters/predictions; trainingpositivecontrol changes learnedlevels','Exact cachedN0seed11argument/hash reuse; all3seeds used and no bestseed selection','Metric sklearn, groupedbootstrap identities, manual observationbridge/F1history and replay without fit','Wholeportfolio vs subset dependence documented, not confused with new hiddenlabels or a changed private scoring population'],
      'cost':{'new_A1_native_primary':30,'new_A1_native_replay2024':30,'cached_N0seed11_native_reused':12,'new_T2b_native':0,'new_CDF_fits':0,'synthetic_native':4,'source_processes':'Sequential perramo due measured2.6GiBavailable; bounded resumable inner/full checkpoints','new2025model_inference':0,'new_submissions':0},
      'evaluator_implementation':'May be completed while sourcejobsrun; mathematical design above frozen. Seal its code before any targetlearning or scoring. No recipe changes after source diagnostics.',
      'preserve_B00_R1_F3c':True,'formal_promotion':False,'private_superiority_not_established':True,'sources':{w.rel(path):sha(path) for path in source_paths()}}
    dump(PLAN,plan)
    forum=post('Codex. Registro la validación completa antes de nuevos ajustes o scores. Conservaré N0 y F1 de A1, tres semillas11/12/13, neutralización por ramo, T2b con C1, mezcla50/50, F2, formas, niveles y factores propios. El archivo enviado ya tiene un reentrenamiento integral con SHA exacto; lo cotejaré sin repetirlo. La evaluación nueva aprende solo2023/fuente2021–2023 y aplica2024. Los bloques públicos históricos quedan explícitamente condicionados; las razones locales usarán solo2023, diferencia temporal que impide llamar al CSV2025 un holdout limpio. La curva compartida de entrenamiento2013 no se presentará como OOF interno independiente. Mediré también la misma estructura con nivel final aprendido en entrenamiento. Presupuesto:30ajustes A1 nuevos,30replays2024, cuatro sintéticos, T2b/curvas existentes reutilizados por hash; ejecución secuencial por memoria. No cambian las variables ni se eligen semillas o recetas por score. Cero inferencias2025, envíos o selección final manual. F3c sigue como referencia enviada, sin prueba de superioridad privada. Plan '+w.rel(PLAN)+' SHA '+sha(PLAN),'COD-S2-20261028-F3C-COMPLETO-PREVIO','F3c completo: protocolo temporal, publico condicionado y controles de toda la cadena')
    dump(OUT/'registration.json',{'plan_sha256':sha(PLAN),'forum':forum});dump(INDEX,{'author':'Codex','utc':utc(),'status':'registered_full_structure_before_fit','plan':w.rel(PLAN),'plan_sha256':sha(PLAN),'forum':forum,'output':w.rel(OUT),'new_submissions':0})
    print(json.dumps({'registered':True,'plan_sha256':sha(PLAN),'native_budget':60,'synthetic_budget':4}),flush=True)
def guard():
    assert sha(PLAN)==read(OUT/'registration.json')['plan_sha256']
    adm=read(HISTORY_ADMISSION) if HISTORY_ADMISSION.exists() else None
    execution=read(EXECUTION_RECONCILIATION) if EXECUTION_RECONCILIATION.exists() else None
    if execution:
        assert adm and execution['source_history_admission_sha256']==sha(HISTORY_ADMISSION)
        additional_interrupted()
    for name,digest in read(PLAN)['sources'].items():
        if adm and name==w.rel(Path(__file__)):digest=execution['source_code_sha256'] if execution else adm['source_code_sha256']
        assert sha(ROOT/name)==digest,name
    if adm:
        assert adm['plan_sha256']==sha(PLAN)
        for name,digest in adm['new_sources'].items():assert sha(ROOT/name)==digest,name

def admit_history():
    assert not HISTORY_ADMISSION.exists() and not (OUT/'target_started.json').exists() and not (OUT/'parameters.json').exists()
    assert sha(PLAN)==read(OUT/'registration.json')['plan_sha256']
    for name,digest in read(PLAN)['sources'].items():
        if name!=w.rel(Path(__file__)):assert sha(ROOT/name)==digest,name
    diagnosis=read(OUT/'F1_pool_diagnosis.json');assert diagnosis['counts_before_correction']=={'total_started_native':31,'F1_wrong_pool_started':18,'N0_started':13}
    assert all(z['extra_in_prepared']==0 and set(z['missing_by_category'])=={'sin_fila'} for z in diagnosis['records'])
    body='Codex. El cotejo integral de variables base pasó en109296filas destino2023/24 y5000por ramo fuente2023; F1 falló. El pool original conserva36reportes aceptados sin_fila emergentes y409desarrollados, omitidos por el adaptador de filas asignadas. Esto afecta conteos previos, no T0/exposición:24/2/4filas destino por motor/edificios/contenidos. Se detuvo el productor propio y la cola antes de todo ajuste o score destino. Conservo31intentos nativos:12N0completos reutilizables,18F1delpoolincorrecto no admisibles en la réplica, y1N0interno interrumpido sin checkpoint. Registro la corrección antes de ajustar: usar exactamente reportes aceptados de asignacion.parquet original, incluida sin_fila, siempre report_date<inception; duración desde primera póliza igual. No mover siniestros a etiquetas ni recalcular C0. F1 corregido irá en source_original_history; N0completo se reutiliza por argumentos/modelo/raw. Faltan48ajustes nativos para completar60útiles,79intentos totales incluida la versión fallida y el interrumpido; cuatro sintéticos separados. Exijo primero igualdad F1 en toda fuente2021–23 y destino2023/24 por búsqueda temporal independiente. Recetas/criterios/familia18/folds/curvas/semillas y entrega intactos. No envíos.'
    forum=post(body,'COD-S2-20261028-F3C-POOL-HISTORIA-PREVIO','F3c: pool original de antecedentes, fallo conservado y corrección antes de puntuar')
    paths=[LEGACY/'noche/salidas'/mk/'asignacion.parquet' for mk in ['s1','s2']]
    dump(HISTORY_ADMISSION,{'author':'Codex','utc':utc(),'plan_sha256':sha(PLAN),'source_code_sha256':sha(Path(__file__)),'evaluator_code_sha256':sha(R/'herramientas/evaluar_F3c_completo.py'),'new_sources':{w.rel(p):sha(p) for p in paths},'forum':forum,
        'definition':'Original accepted report pool including sin_fila; event before inception only; same original first observed inception duration. No claim amount from unassigned events enters y or C0.',
        'require_original_history_parity_before_fit':True,'expected_new_native_by_line':{'motor':12,'buildings':16,'contents':20},'prior_native_attempts':31,'prior_completed_wrong_F1_fits':18,'prior_aborted_N0_inner':1,'expected_total_native_attempts':79,'expected_useful_native_fits':60,'new_C0':0,'new_submissions':0})
    print(json.dumps({'original_history_admitted_before_fit':True,'remaining_native_fits':48,'preserved_wrong_pool_fits':18,'original_interrupted_fit':1}),flush=True)

def history_preflight():
    guard();assert HISTORY_ADMISSION.exists();records=[]
    for line in LINES:
        src,em,_,_=source_inputs(line)
        for name,mk,frame in [('source','s1',src),('target','s2',em)]:
            cut=2023 if mk=='s1' else 2024
            old=pd.read_parquet(LEGACY/'noche/salidas'/mk/f'base_{line}.parquet',columns=['row_id','policy_id','period_start','year'],filters=[('year','<=',cut)]);old['period_start']=pd.to_datetime(old.period_start)
            first=old.groupby('policy_id').period_start.min();query=old.set_index('row_id').loc[frame.row_id].reset_index()
            events=pd.read_parquet(LEGACY/'noche/salidas'/mk/'asignacion.parquet',columns=['policy_id','report_date'],filters=[('line','==',line),('accepted','==',True)]);events['report_date']=pd.to_datetime(events.report_date)
            mapping={p:np.sort(g.report_date.to_numpy('datetime64[ns]')) for p,g in events.groupby('policy_id')}
            count=np.array([np.searchsorted(mapping.get(p,np.array([],dtype='datetime64[ns]')),np.datetime64(start,'ns'),side='left') for p,start in query[['policy_id','period_start']].itertuples(index=False,name=None)],float)
            years=((query.period_start-query.policy_id.map(first)).dt.days/365.25).to_numpy()
            checks={'accepted_report_count_exact':bool(np.array_equal(count,frame.f1_siniestros_previos.to_numpy())),'first_inception_duration_exact':bool(np.allclose(years,frame.f1_anios_observados.to_numpy(),rtol=0,atol=1e-12))}
            records.append({'market':name,'line':line,'rows':len(frame),'years':sorted(frame.year.unique().tolist()),'checks':checks});assert all(checks.values()),records[-1]
            del old,query,first,events,mapping;gc.collect()
        del src,em;gc.collect()
    dump(OUT/'original_history_preflight.json',{'author':'Codex','utc':utc(),'records':records,'all_passed':True,'real_fits':0,'new_submissions':0});print(json.dumps({'history_full_inputs_passed':True,'rows_checked':sum(z['rows'] for z in records)}),flush=True)
def preflight():
    guard();checks={};rng=np.random.default_rng(71);X=pd.DataFrame({'x':rng.normal(size=120),'f1':np.tile([0.,1.,2.],40)})
    y=np.exp(.3*X.x.to_numpy()+.1*X.f1.to_numpy());pp=dict(objective='tweedie',tweedie_variance_power=1.5,num_leaves=3,min_data_in_leaf=5,learning_rate=.1,verbosity=-1,num_threads=2,seed=11,deterministic=True,force_row_wise=True)
    models=[]
    for i in range(4):
        cols=['x'] if i==0 else ['x','f1'];target=y[:90]*(2 if i==3 else 1)
        b=lgb.train(pp,lgb.Dataset(X.loc[:89,cols],label=target),6);models.append(b.model_to_string())
    checks['heldlabels_not_in_source_arguments']=models[1]==models[2];checks['positive_source_train_changes_model']=models[1]!=models[3];checks['F1_schema_is_distinct']=models[0]!=models[1]
    # Hand F1 chronology: accepted event before inception only; original duration.
    q=pd.DataFrame({'row_id':['a','b'],'policy_id':['p','p'],'period_start':pd.to_datetime(['2023-01-01','2024-01-01'])});events=pd.DataFrame({'policy_id':['p','p','p'],'report_date':pd.to_datetime(['2022-12-01','2023-07-01','2025-01-01']),'accepted':[True,False,True]})
    n,years=history(q,events);checks['history_manual']=np.array_equal(n,[1.,1.]) and np.allclose(years,[0.,365/365.25])
    checks['all_passed']=all(checks.values());dump(OUT/'preflight.json',{'utc':utc(),'checks':checks,'synthetic_native_fits':4});assert checks['all_passed'];print(json.dumps(checks),flush=True)
def history(rows,events):
    base=rows[['row_id','policy_id','period_start']].copy();base['period_start']=pd.to_datetime(base.period_start)
    c=events[events.accepted][['policy_id','report_date']].copy();c['report_date']=pd.to_datetime(c.report_date)
    joined=base.merge(c,on='policy_id');joined=joined[joined.report_date.lt(joined.period_start)]
    n=base.row_id.map(joined.groupby('row_id').size()).fillna(0).to_numpy(float)
    first=base.groupby('policy_id').period_start.min();years=((base.period_start-base.policy_id.map(first)).dt.days/365.25).to_numpy(float)
    return n,years
def needed_columns(line):
    generated={'occupation_n','cust_tenure','prop_age','has_campaign','exposure_model'}
    cols=set(a.POL+a.CUST+a.ADDR+a.LINE[line])-generated
    cols.update(['row_id','policy_id','customer_id','address_id','year','period_start','period_end','y','exposure','fold','group','occupation','tenure_years','property_age','campaign_code'])
    cols.update('y_'+peril for peril in a.PERILS[line])
    if line=='buildings':cols.add('construction')
    return sorted(cols)
def source_inputs(line,poison=False):
    src=pd.read_parquet(ACTIVE/'prepared'/f'developed_{line}.parquet',columns=needed_columns(line));em=pd.read_parquet(ACTIVE/'prepared'/f'emerging_{line}.parquet',columns=needed_columns(line))
    changed={}
    for name,frame in [('source',src),('target',em)]:
        future=frame.year.eq(2024);changed[name]=int(future.sum())
        if poison:
            for col in ['y']+['y_'+peril for peril in a.PERILS[line]]:frame.loc[future,col]=frame.loc[future,col]*17+123.
    src=src[src.year.le(2023)].reset_index(drop=True);assert src.groupby('address_id').fold.nunique().le(1).all()
    for name,frame in [('developed',src),('emerging',em)]:
        if HISTORY_ADMISSION.exists():
            mk='s1' if name=='developed' else 's2';events=pd.read_parquet(LEGACY/'noche/salidas'/mk/'asignacion.parquet',columns=['policy_id','report_date','accepted'],filters=[('line','==',line)])
        else:
            events=pd.read_parquet(ACTIVE/'prepared'/f'{name}_claims.parquet',columns=['policy_id','line','report_date','accepted']);events=events[events.line.eq(line)]
        n,years=history(frame,events);frame['f1_siniestros_previos']=n;frame['f1_anios_observados']=years
        del events;gc.collect()
    curves=read(ACTIVE/'curves_full.json');F={k:a.parse_curves(curves[k]) for k in ['inner','full']}
    return src,em,F,changed
def train_line_body(line):
    guard();assert read(OUT/'preflight.json')['checks']['all_passed'];assert line in LINES
    if HISTORY_ADMISSION.exists():assert read(OUT/'original_history_preflight.json')['all_passed']
    for tag,poison in [('baseline',False),('poison2024',True)]:
        src,em,F,changed=source_inputs(line,poison);inner=src.fold.ne(0).to_numpy();di=src[inner].reset_index(drop=True);dv=src[~inner].reset_index(drop=True)
        qi,qv,wi=a.completion(di,dv,line,F['inner'],'A1');qf,_,wf=a.completion(src,em,line,F['full'],'A1')
        yi=di.y.to_numpy(float);yv=dv.y.to_numpy(float);yf=src.y.to_numpy(float)
        oi=np.log(di.exposure.to_numpy().round(4)*qi);ov=np.log(dv.exposure.to_numpy().round(4)*qv);of=np.log(src.exposure.to_numpy().round(4)*qf)
        bi=float(np.log(yi.sum()/np.exp(oi).sum()));bf=float(np.log(yf.sum()/np.exp(of).sum()))
        for family in ['N0','F1']:
            features=a.a1_features(src,line);ev=a.a1_features(em,line)
            if family=='F1':
                for col in ['f1_siniestros_previos','f1_anios_observados']:features[col]=src[col].to_numpy();ev[col]=em[col].to_numpy()
            ci={col:sorted(features.loc[inner,col].unique().tolist()) for col in features if col in a.CAT};cf={col:sorted(features[col].unique().tolist()) for col in features if col in a.CAT}
            Xi=a.matrix(features[inner].reset_index(drop=True),ci);Xv=a.matrix(features[~inner].reset_index(drop=True),ci);Xf=a.matrix(features,cf);Xe=a.matrix(ev,cf)
            del features,ev;gc.collect()
            baseparams=read(ACTIVE/'models/full'/f'{line}_receipt.json')['params']
            for seed in SEEDS:
                params={**baseparams,'seed':seed};folder=source_folder(line,tag,family,seed);folder.mkdir(parents=True,exist_ok=True)
                ah=v.digest(Xi,yi,oi+bi,Xv,yv,ov+bi,Xf,yf,of+bf,Xe,ci,cf,params,wi,wf)
                complete=folder/'complete.json'
                if complete.exists():
                    rec=read(complete);assert rec['arguments_sha256']==ah;assert sha(ROOT/rec['model'])==rec['model_sha256'] and sha(ROOT/rec['raw'])==rec['raw_sha256'];continue
                if family=='N0' and seed==11:
                    oldscope='replay_2024' if poison else 'full';old=ACTIVE/'models'/oldscope;rec=read(old/f'{line}_receipt.json')
                    assert rec['arguments_sha256']==ah,(line,tag,'N0_cached_arguments');assert sha(old/f'{line}.txt')==rec['model_sha256']
                    assert sha(old/f'{line}_raw.parquet')==rec['raw_file_sha256']
                    dump(complete,{'utc':utc(),'arguments_sha256':ah,'reused':True,'model':w.rel(old/f'{line}.txt'),'raw':w.rel(old/f'{line}_raw.parquet'),'receipt':w.rel(old/f'{line}_receipt.json'),'model_sha256':rec['model_sha256'],'raw_sha256':rec['raw_file_sha256'],'rounds':rec['rounds'],'columns':list(Xf),'full_categories':cf,'source_center':rec['source_center']})
                    continue
                dump(folder/'start.json',{'utc':utc(),'arguments_sha256':ah,'line':line,'tag':tag,'family':family,'seed':seed,'future_rows_poisoned_before_filter':changed,'source_rows':len(src),'columns':list(Xf),'params':params}) if not (folder/'start.json').exists() else None
                live('live_'+line,{'pid':os.getpid(),'line':line,'tag':tag,'family':family,'seed':seed,'stage':'source_fit','arguments_sha256':ah,'available_GiB':psutil.virtual_memory().available/2**30})
                print(json.dumps({'event':'source_start','line':line,'tag':tag,'family':family,'seed':seed}),flush=True)
                roundfile=folder/'inner_complete.json'
                if roundfile.exists():
                    innerrec=read(roundfile);assert innerrec['arguments_sha256']==ah;rounds=innerrec['rounds']
                else:
                    with attempt_path(line).open('a',encoding='utf8') as f:f.write(json.dumps({'utc':utc(),'tag':tag,'family':family,'seed':seed,'stage':'inner'})+'\n')
                    bst=lgb.train(params,lgb.Dataset(Xi,label=yi,init_score=oi+bi),4000,valid_sets=[lgb.Dataset(Xv,label=yv,init_score=ov+bi)],callbacks=[lgb.early_stopping(400,verbose=False)])
                    rounds=max(1,bst.best_iteration);dump(roundfile,{'utc':utc(),'arguments_sha256':ah,'rounds':rounds});del bst;gc.collect()
                assert psutil.virtual_memory().available>350*2**20,'Insufficient memory before full fit; resume this stage later'
                with attempt_path(line).open('a',encoding='utf8') as f:f.write(json.dumps({'utc':utc(),'tag':tag,'family':family,'seed':seed,'stage':'full'})+'\n')
                bst=lgb.train(params,lgb.Dataset(Xf,label=yf,init_score=of+bf),rounds)
                center=float(np.log(np.average(np.exp(bst.predict(Xf,raw_score=True,num_threads=2)),weights=src.exposure.to_numpy().round(4))))
                raw=bst.predict(Xe,raw_score=True,num_threads=2)-center;model=folder/'model.txt';bst.save_model(str(model));rawpath=folder/'raw.parquet';pd.DataFrame({'row_id':em.row_id.to_numpy(),'raw':raw}).to_parquet(rawpath,index=False)
                rec={'utc':utc(),'arguments_sha256':ah,'reused':False,'model':w.rel(model),'raw':w.rel(rawpath),'model_sha256':sha(model),'raw_sha256':sha(rawpath),'rounds':rounds,'columns':list(Xf),'full_categories':cf,'source_center':center}
                if poison:
                    old=read(source_folder(line,'baseline',family,seed)/'complete.json')
                    for field in ['arguments_sha256','model_sha256','raw_sha256','rounds','source_center']:assert rec[field]==old[field],(line,family,seed,field)
                dump(complete,rec);del bst,raw;gc.collect();print(json.dumps({'event':'source_complete','line':line,'tag':tag,'family':family,'seed':seed,'rounds':rounds}),flush=True)
            del Xi,Xv,Xf,Xe;gc.collect()
        del src,em,di,dv;gc.collect()
    attempts=[json.loads(z) for z in attempt_path(line).read_text().splitlines()];expected=read(HISTORY_ADMISSION)['expected_new_native_by_line'][line]+additional_interrupted(line) if HISTORY_ADMISSION.exists() else 20;assert len(attempts)==expected
    live('live_'+line,{'pid':os.getpid(),'line':line,'status':'complete','new_native_fits':len(attempts),'original_history':HISTORY_ADMISSION.exists()});dump(source_marker(line),{'utc':utc(),'line':line,'new_native_fits':len(attempts),'new_CDF_fits':0,'source2024_poison_replay_exact':True,'original_history':HISTORY_ADMISSION.exists()});print(json.dumps({'line_complete':line,'new_native_fits':len(attempts),'original_history':HISTORY_ADMISSION.exists()}),flush=True)

def train_line(line):
    # Per-line ownership prevents a sequential queue duplicating an independently
    # launched line. Nothing in the native model or its arguments changes.
    assert line in LINES;path=OUT/('source_lease_'+line+'.json');started=time.monotonic()
    owner={'pid':os.getpid(),'created':psutil.Process().create_time(),'line':line,'utc':utc()};announced=False
    while True:
        if source_marker(line).exists():guard();return
        try:
            with path.open('x',encoding='utf8') as stream:json.dump(owner,stream);stream.flush();os.fsync(stream.fileno())
            break
        except FileExistsError:
            try:old=read(path)
            except json.JSONDecodeError:
                time.sleep(.2);assert time.monotonic()-started<30,'Incomplete source lease; reconcile manually.';continue
            alive=psutil.pid_exists(old['pid'])
            if alive:
                try:alive=abs(psutil.Process(old['pid']).create_time()-old['created'])<.1
                except psutil.NoSuchProcess:alive=False
            if not alive:
                before=path.read_bytes();dump(OUT/('stale_source_lease_'+line+'_'+str(time.time_ns())+'.json'),{'utc':utc(),'owner':old,'confirmed_not_alive':True})
                assert path.read_bytes()==before;path.unlink();continue
            if not announced:print(json.dumps({'event':'wait_existing_line_owner','line':line,'owner_pid':old['pid']}),flush=True);announced=True
            assert time.monotonic()-started<3600,'Finite source-lease wait expired.';time.sleep(5)
    try:train_line_body(line)
    finally:
        if path.exists() and read(path)==owner:path.unlink()

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');arg=argparse.ArgumentParser();arg.add_argument('mode',choices=['freeze','preflight','admit_history','history_preflight','train']);arg.add_argument('--line',choices=LINES);args=arg.parse_args()
    with threadpool_limits(limits=2):
        if args.mode=='train':train_line(args.line)
        else:globals()[args.mode]()
