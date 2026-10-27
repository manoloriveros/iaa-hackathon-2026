"""Selección interna de 64/128/256 rondas con prefijos del mismo ajuste."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import math
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);a=importlib.util.module_from_spec(s);s.loader.exec_module(a);return a
k=load('p92_current_prior_tree',R/'herramientas/preparar_boosting_prior_calibrado_P89.py')
scopes=load('p92_protected_inner_selector',R/'herramientas/preparar_seleccion_GLM_P84.py')
m=k.m;q=k.q;w=k.w;np=k.np;pd=k.pd;BASE=k.BASE;rating=k.k.k;prior=k.k;lgb=k.t.lgb
OUT=BASE/'P92_selector_rondas_preflight_20261027'
PLAN=R/'registro/semana2_selector_rondas_preflight_plan.json';INDEX=R/'registro/semana2_selector_rondas_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P92_SELECTOR_RONDAS_PREFLIGHT.md'
GRID=[64,128,256];MAX_ROUNDS=256;PARAMS=dict(k.t.PARAMS);ORIGINAL_TRAIN=lgb.train


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)
def check_sources(plan):return k.check_sources(plan)


def fit_max(frame,line,folder,calibration=None):
    def produce():
        k.setup();train=frame.loc[~frame.is_held].copy();assert set(train.group_id).isdisjoint(set(frame.loc[frame.is_held,'group_id']))
        cal=prior.calibrate_levels(train,line) if calibration is None else calibration
        assert cal['fit_row_ids_digest']==m.p.b.digest(sorted(train.row_id)) and cal['fit_groups_digest']==m.p.b.digest(sorted(set(train.group_id)))
        dump(folder/'levels.json',cal)
        x,pre=rating.design(train,line);y=train.T0.to_numpy(float);base=prior.ultimate_offset(train,cal)*train.q_paired.to_numpy(float)
        dataset=lgb.Dataset(x,label=y,init_score=np.log(base),feature_name=['x'+str(j) for j in range(x.shape[1])],free_raw_data=False)
        history={}
        def native(*args,**kwargs):
            dump(folder/'actual_fit_invoked.json',{'author':'Codex','utc':utc(),'rounds':MAX_ROUNDS,'parameters':PARAMS,'actual_native_train':True})
            return ORIGINAL_TRAIN(*args,**kwargs)
        model=native(PARAMS,dataset,num_boost_round=MAX_ROUNDS,valid_sets=[dataset],valid_names=['train'],callbacks=[lgb.record_evaluation(history),lgb.log_evaluation(0)])
        raw_artifact={'line':line,'preprocess':pre,'model_string':model.model_to_string(),'prior_level_calibration':cal,'parameters':PARAMS,
            'maximum_rounds':MAX_ROUNDS,'native_metric_history':history['train']['tweedie']}
        dump(folder/'raw_maximum.json',raw_artifact)
        native_y=np.asarray(dataset.get_label(),float);assert np.allclose(y,native_y,rtol=6e-8,atol=0.)
        trees=model.dump_model()['tree_info'];assert 1<=len(trees)<=MAX_ROUNDS
        leaf_cap=PARAMS['learning_rate']*PARAMS['max_delta_step'];models={}
        for rounds in GRID:
            text=model.model_to_string(num_iteration=rounds);loaded=lgb.Booster(model_str=text);raw=loaded.predict(x,raw_score=True)
            take=min(rounds,len(trees));parts=[k.t.leaf_values(tree['tree_structure']) for tree in trees[:take]]
            assert loaded.num_trees()==take and all(len(z)<=PARAMS['num_leaves'] for z in parts)
            assert max(v[2] for z in parts for v in z)<=PARAMS['max_depth'] and max(abs(v[0]) for z in parts for v in z)<=leaf_cap+1e-12
            bound=rounds*leaf_cap;assert np.isfinite(raw).all() and np.max(np.abs(raw))<=bound+1e-10
            for pos in np.linspace(0,len(x)-1,7,dtype=int):assert math.isclose(math.fsum(k.t.walk(tree['tree_structure'],x[pos]) for tree in trees[:take]),float(raw[pos]),rel_tol=1e-11,abs_tol=1e-12)
            mu=base*np.exp(raw);metric=math.fsum((2*native_y/np.sqrt(mu)+2*np.sqrt(mu)).tolist())/len(y)
            recorded=history['train']['tweedie'][min(rounds,len(history['train']['tweedie']))-1]
            assert math.isclose(metric,recorded,rel_tol=3e-12)
            assert np.array_equal(raw,model.predict(x,num_iteration=rounds,raw_score=True))
            models[str(rounds)]={'line':line,'preprocess':pre,'model_string':text,'prior_level_calibration':cal,'parameters':PARAMS,'configured_rounds':rounds,
                'effective_trees':take,'lightgbm_version':lgb.__version__,'native_training_metric':recorded,'fit_row_ids_digest':cal['fit_row_ids_digest'],'fit_groups_digest':cal['fit_groups_digest'],
                'native_offset_metric_scalar_match':True,'leaf_sum_and_serialization_exact':True,'max_absolute_log_correction_bound':bound,
                'actual_max_absolute_train_log_correction':float(np.max(np.abs(raw))),'actual_min_leaf_count':min(v[1] for z in parts for v in z),
                'fitted_leaf_values':sum(len(z) for z in parts),'native_label_max_abs_rounding':float(np.max(np.abs(y-native_y))),
                'feature_contract':'Same P90rawsource/rating/businessband fields, ownscope scalarprior; no pricefeature'}
        prior.level_math(train,cal)
        return {'line':line,'maximum_rounds':MAX_ROUNDS,'models':models,'native_metric_history':history['train']['tweedie'],
            'fit_row_ids_digest':cal['fit_row_ids_digest'],'fit_groups_digest':cal['fit_groups_digest'],'new_closed_levels':6 if calibration is None else 0,
            'prior_calibration_reused':calibration is not None,'all_prefix_integrity_pass':True}
    artifact=m.once(folder,'maximum',produce)
    assert artifact['fit_row_ids_digest']==m.p.b.digest(sorted(frame.loc[~frame.is_held,'row_id']))
    return artifact


def choose(losses):
    assert len(losses)==len(GRID) and np.isfinite(losses).all();best=min(losses);tolerance=1e-12*max(1.,abs(best))
    index=next(j for j,value in enumerate(losses) if value<=best+tolerance)
    return {'index':index,'rounds':GRID[index],'losses':list(losses),'tie_tolerance':tolerance,'criterion':'Total original T0Tweedie15deviance over all5innerheld folds/3lines, common length; roundoff ties shorter'}


def validation_loss(frame,model):
    held=frame.loc[frame.is_held];ultimate,_=k.forward(held.drop(columns=['T0','reserve','q_paired']),model)
    y=held.T0.to_numpy(float);mu=ultimate*held.q_paired.to_numpy(float)
    scalar=math.fsum((4*y/np.sqrt(mu)+4*np.sqrt(mu)-8*np.sqrt(y)).tolist());assert math.isclose(scalar,float(m.e.unit(y,mu).sum()),rel_tol=4e-12,abs_tol=1e-7)
    return scalar


def final_model(frame,line,selection,folder,outer=None,adverse=False):
    # Future real evaluator may reuse an exactly matched P90final64model here.
    artifact=fit_max(frame,line,folder);return artifact['models'][str(selection['rounds'])]


def train_bundle(frames,tables,folder,outer=None,adverse=False):
    totals=[0.]*len(GRID);references=[]
    for member in range(5):
        scoped=scopes.inner_frames(frames,tables[member])
        for line in q.LINES:
            relative=f'i{member}/{line}';artifact=fit_max(scoped[line],line,folder/relative)
            references.append({'relative':relative,'sha256':w.sha(folder/relative/'maximum.json')})
            for j,rounds in enumerate(GRID):totals[j]+=validation_loss(scoped[line],artifact['models'][str(rounds)])
    selection=choose(totals);models={line:final_model(frames[line],line,selection,folder/'final'/line,outer,adverse) for line in q.LINES}
    return {'selection':selection,'models':models,'inner_maximum_refs':references,'all_inner_prefix_integrity_pass':True,
        'contract':'P92common-inner-selected-length-with-ownscope-priors-and-maxfit-prefixes'}


def replay_bundle(frames,tables,bundle,folder):
    totals=[0.]*len(GRID);refs={z['relative']:z['sha256'] for z in bundle['inner_maximum_refs']}
    for member in range(5):
        scoped=scopes.inner_frames(frames,tables[member])
        for line in q.LINES:
            relative=f'i{member}/{line}';path=folder/relative/'maximum.json';assert w.sha(path)==refs[relative];artifact=w.read(path)
            for j,rounds in enumerate(GRID):totals[j]+=validation_loss(scoped[line],artifact['models'][str(rounds)])
    assert choose(totals)==bundle['selection']
    return {line:k.forward(frames[line].loc[frames[line].is_held].drop(columns=['T0','reserve','q_paired']),bundle['models'][line])[0] for line in q.LINES}


def synthetic_inputs():
    rng=np.random.default_rng(2026102792);n=6000;i=np.arange(n);frames={};tables={member:{} for member in range(5)}
    for line in q.LINES:
        a=np.exp(rng.normal(0,.3,n));b=np.exp(rng.normal(5,.3,n));ee=rng.uniform(.3,1,n);qq=rng.uniform(.4,1,n);excess=rng.choice([0.,10.,100.],n)
        y=(.5*400*a+.5*b)*ee*qq*np.where(excess==100,2.,.5)*rng.gamma(2,.5,n)*(rng.random(n)<.5)*2
        f=pd.DataFrame({'row_id':[line+'s'+str(j) for j in i],'line':line,'group_id':['jointgroup'+str(j) for j in i],
            'is_held':i%5==0,'fold':i%5,'year':2023+(i//5)%2,'new_business':(i//10)%2,'T0':y,'reserve':0.,
            'annual_A1S':a,'annual_T2b':b,'exposure_calendar':ee,'q_paired':qq})
        for j,name in enumerate(rating.BASE_NUM[line]):f[name]=excess if j==0 else rng.choice([0.,10.,100.],n)
        for name in rating.BASE_CAT[line]:
            if name!='new_business':f[name]=rng.choice(['a','b','c'],n)
        f['prior_claims_5y']=rng.choice([0.,1.,2.,np.nan],n)
        if line=='motor':f['ncb_years']=rng.choice([0.,1.,2.,3.,5.,6.,9.,10.,np.nan],n)
        for member in range(5):
            z=f.loc[~f.is_held,['row_id','year','group_id','q_paired']].copy();z['is_held']=((i[~f.is_held]//5)%5)==member;z.q_paired*=.95+.01*member;tables[member][line]=z
        frames[line]=f
    return frames,tables


def synthetic():
    frames,tables=synthetic_inputs();folder=OUT/'synthetic'
    primary=m.once(folder,'primary_bundle',lambda:train_bundle(frames,tables,folder/'primary_fits'))
    bad={line:rating.poison(f,line) for line,f in frames.items()}
    adverse=m.once(folder,'adverse_bundle',lambda:train_bundle(bad,tables,folder/'adverse_fits'));assert primary==adverse
    equivalence=[]
    for line in q.LINES:
        maximum=w.read(folder/'primary_fits/final'/line/'maximum.json');prefix=maximum['models']['64'];cal=prefix['prior_level_calibration']
        destination=folder/'control64'/line
        def produce():
            k.setup();z=k.observed_frame(frames[line],cal);old=lgb.train
            def native(*args,**kwargs):
                dump(destination/'actual_fit_invoked.json',{'author':'Codex','utc':utc(),'standalone_rounds':64});return ORIGINAL_TRAIN(*args,**kwargs)
            lgb.train=native
            try:return k.t.fit(z,line,destination/'raw.json')
            finally:lgb.train=old
        standalone=m.once(destination,'standalone',produce);standalone['prior_level_calibration']=cal
        left=lgb.Booster(model_str=prefix['model_string']);right=lgb.Booster(model_str=standalone['model_string'])
        assert left.dump_model()['tree_info']==right.dump_model()['tree_info'] and prefix['preprocess']==standalone['preprocess']
        held=frames[line].loc[frames[line].is_held].drop(columns=['T0','reserve','q_paired'])
        one,_=k.forward(held,prefix);two,_=k.forward(held,standalone);assert np.array_equal(one,two)
        assert prefix['fitted_leaf_values']>prefix['effective_trees'];equivalence.append({'line':line,'prefix64_equals_standalone64_structure_and_predictions':True})
    before=lgb.train
    def reject(*args,**kwargs):raise AssertionError('P92synthetic replay forbids native fitting')
    lgb.train=reject
    try:
        one=replay_bundle(frames,tables,primary,folder/'primary_fits');two=replay_bundle(frames,tables,json.loads(json.dumps(adverse)),folder/'adverse_fits')
        assert all(np.array_equal(one[line],two[line]) for line in q.LINES)
    finally:lgb.train=before
    assert choose([10.,10.,10.])['rounds']==64 and choose([12.,10.,11.])['rounds']==128
    return {'author':'Codex','utc':utc(),'synthetic_selected_rounds_only':primary['selection']['rounds'],'primary_adverse_whole_bundles_exact':True,
        'all45inner_objectives_and_final_predictions_replayed_exact':True,'prefix64_equivalence':equivalence,'tie_prefers_shorter':True,
        'synthetic_primary_maximum_nativefits':18,'synthetic_adverse_maximum_nativefits_separate':18,'synthetic_standalone64_controls':3,
        'synthetic_primary_closed_levels':108,'synthetic_adverse_closed_levels_separate':108,
        'reporting_limit':'Synthetic qtables are fixed own-scope fixtures; real reporting uses unchanged P84protected tables/ancestry bySHA, no new RPLvalidation claim.',
        'new_real_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0}


def reuse_real_bindings():
    previous=w.read(scopes.OUT/'bindings.json');assert len(previous['records'])==75
    records=[]
    for outer in range(5):
        frames={line:rating.frame_for(line,outer) for line in q.LINES}
        partition=pd.read_parquet(m.P1/f'inner_groups_outer{outer}.parquet').set_index('group_id').inner_fold
        for member in range(5):
            expected={rid for f in frames.values() for rid in f.loc[~f.is_held&f.group_id.map(partition).ne(member),'row_id']}
            for line,frame in frames.items():
                record=next(z for z in previous['records'] if z['outer']==outer and z['member']==member and z['line']==line)
                path=ROOT/record['table'];assert w.sha(path)==record['table_sha256']==previous['outputs'][record['table']]
                assert w.sha(ROOT/record['report'])==record['report_sha256']
                table=pd.read_parquet(path);f=frame.loc[~frame.is_held].set_index('row_id').loc[table.row_id]
                assert table.row_id.is_unique and set(table.row_id)==set(frame.loc[~frame.is_held,'row_id'])
                assert np.array_equal(table.year,f.year) and np.array_equal(table.group_id,f.group_id)
                assert np.array_equal(table.is_held,f.group_id.map(partition).eq(member))
                assert record['report_training_ids_digest']==m.p.b.digest(sorted(expected))
                records.append({'outer':outer,'member':member,'line':line,'table':record['table'],'sha256':record['table_sha256'],
                    'exact_current_keys_and_scope':True,'prior_numeric_reporting_proof_reused_not_repeated':True})
    return {'author':'Codex','utc':utc(),'records':records,'existing75numeric_tables_reused':True,'new_CDF_fits':0,'new_real_fits':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert phase['P90_execution']['state']=='TERMINAL_SUCCESS' and not phase.get('active_jobs') and not phase.get('active_execution')
    previous=BASE/'P91_limites_arbol_guardado_20261027';assert w.read(previous/'completion_receipt.json')['report_sha256']==w.sha(previous/'report.json')
    parent=w.read(k.PLAN);k.check_sources(parent);bindings=w.read(scopes.OUT/'bindings.json')
    assert w.read(scopes.OUT/'report.json')['bindings_sha256']==w.sha(scopes.OUT/'bindings.json')
    paths=[Path(__file__),Path(k.__file__),Path(scopes.__file__),k.PLAN,scopes.PLAN,scopes.OUT/'bindings.json',scopes.OUT/'report.json',scopes.OUT/'completion_receipt.json',
        previous/'report.json',previous/'completion_receipt.json',BASE/'P90_validacion_boosting_prior_20261027/report.json']
    paths += [ROOT/path for path in bindings['outputs']]
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'New finite train-only tree-length selector/maxfit-prefix composition, synthetic and reuse75protected inner inputs only. No real fitting or outer prefix scoring.',
        'need':'P91inspected NEWP90:12/15models reached train logcorrection bound;50.5-92.2percent of late leafparameters used maximumstep. This is descriptive pressure under a finite small-step fit, not proof longer improves private/outer performance. Test fittinglength inside training without changing depth/fields/step.',
        'hypothesis':'An internally chosen fittinglength may balance bias/variance of SAMErestricted native model better than fixed64. No promised gain or claimed necessity of larger capacity.',
        'configuration':{'grid':GRID,'maximum_native_rounds':MAX_ROUNDS,'parameters':PARAMS,'selector':'ONEcommon length for all3lines, minimum total ORIGINALuncappedT0Tweedie15deviance over ALL5saved inner globalgroupfolds, ties within1e-12*max(1,abs(minloss))prefer shorter. No line-specific length or outer/public prefix scoring.',
            'learning':'Every inner scope learns its OWN6scalarprior levels and preprocessing, then ONEmax256native fit.64/128/256prefixes share that exact prior/preprocess and training trajectory. No full-outerprior, outerqor preprocess in innerfit.',
            'prefixes':'Persist native metric history/fullraw model before controls. Everyprefix validates actual metric WITHoffset and float32labels, independent leafwalk/bounds and native serialization. Synthetic standalone64comparison verifies native-prefix equivalence, no assumption of string-parameter equality.',
            'final':'Selected commonlength applied to one full-outer model perline. Future evaluator reuses EXACTP90final64model if selected64; otherwise one max256fit on fulltrain with cached own-scope P90prior and selectedprefix. Same scalarprior code/data/scope hashes required.',
            'inputs':'Reuse P84tables/own-inner CDFancestry by SHA plus fresh key/partition binding only; no repeated numeric CDFsuite or reestimation. Synthetic qtables are fixtures, no synthetic reporting-learning claim.',
            'unchanged':'P90rawsource signals/businessbands/rating fields, source models, T0/calendar, percomponent K400prior, depth3/7leaves/minleaf1000/L2=10/leafstep.003/seed/deterministic2CPU. No field/depth/step search.'},
        'criterion':'Whole synthetic18primary+18adverse maxfits plus3standalone64controls; exact selector/inner modelhashes/finalmodels under outerpayloadpoison, all45innerobjectives replayed without native fitting, correct tiebreak. Every sourcelevel/preprocess trained in its own scope, reused75real table identities. No new heldouter scores.',
        'budget':{'synthetic_primary_maximum_fits':18,'synthetic_adverse_maximum_fits_separate':18,'synthetic_standalone64_controls':3,'synthetic_primary_closed_levels':108,'synthetic_adverse_closed_levels_separate':108,
            'new_real_fits':0,'new_CDF_fits':0,'new_held_outer_scores':0,'new2025inference':0,'new_submissions':0},
        'future_budget':{'primary_inner_maximum_fits':75,'adverse_inner_maximum_fits_separate':75,'primary_new_final_maximum_fits_atmost':15,'adverse_new_final_maximum_fits_atmost':15,
            'primary_inner_closed_levels':450,'adverse_inner_closed_levels_separate':450,'fullouter_closed_levels_reused_each':90,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'future_criterion':'Separate P93registered/committed whole evaluation; EVERYunchanged P90outerpredictive/cohort/scenario/family16/level/influence guard plus all inner/final native integrity. Pooledpass still needs own2023-only conditionaltransfer before anyCSV. No grid refinement or chosen line overrides after results.',
        'runtime_sources':parent['runtime_sources'],'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},
        'limits':parent['limits']+['Training-only length selection is a new adaptive algorithm, not restored pristine validation or proof longer trees help.','Finite-grid conditional uncertainty and provided source2024/reporting/valuation assumptions remain.'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P92 registra ANTESdeprobar selector de rondas[64,128,256]SOLOinterno, común a3ramos/cincofolds, pérdidaTweedieoriginal y empate a menorlongitud. Cada ámbito estima sus propios niveles/preproceso; un solo máximo256produceprefijos, no q/niveles exteriores. Misma profundidad/campos/hojas/paso/semillaP90.18+18máximos sintéticos y3controles64independientes, veneno exterior completo, replaytodos45objetivos sin ajustar y equivalencia prefijo64/standalone64.75tablas internasP84reutilizadas porSHA/grupos, sin repetir CDF. Futuro75+75máximos internos y hasta15+15finales,450+450niveles internos, finalesP90reutilizados cuando64; todas las guardas y transferencia antes deCSV. La presión de pasosP91no demuestra que más rondas mejoren. Sin ajustes reales/2025/envíos; B00adversos preservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P92registered_before_length_selector_synthetic','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P92-RONDAS-PREVIO','P92: longitud aprendida solo en entrenamiento y prefijos del mismo ajuste')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    assert not (OUT/'report.json').exists();check_sources(w.read(PLAN));assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    dump(OUT/'synthetic.json',synthetic());dump(OUT/'bindings.json',reuse_real_bindings());check_sources(w.read(PLAN))
    dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P92whole_length_selector_prefix_synthetic_and_reused_bindings_passed',
        'synthetic':w.rel(OUT/'synthetic.json'),'synthetic_sha256':w.sha(OUT/'synthetic.json'),'bindings':w.rel(OUT/'bindings.json'),'bindings_sha256':w.sha(OUT/'bindings.json'),
        'new_real_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'preflight':'passed','synthetic_maximum_nativefits':36,'standalone64controls':3,'reused_inner_tables':75,'new_real_fits':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');check_sources(w.read(PLAN))
    next_unit='P93: register/commit EXACTP92common-inner-length-selection whole algorithm,75primary/75adverse max256inner fits plus atmost15+15newfinal fits,450+450newinnerlevels, reuse fullouterP90levels and exact64models when selected64. All old outerguards/native integrity/conditionaltransfer, no round/depth/field/step/line rescue. Replay225inner objectives/all5selectors and15final models without fitting.'
    text='# P92: selección interna de longitud y prefijos\n\nCodex, '+utc()+'. El número de rondas se elige exclusivamente dentro de cada entrenamiento entre64/128/256, común a los3ramos. Profundidad, hojas, campos, paso y semilla permanecen fijos. Empates numéricos prefieren menos rondas.\n\n'
    text+='Cada ámbito aprende sus propios niveles y preproceso, con un máximo256del que salen los tres prefijos. Pasaron18máximos sintéticos primarios/18adversos y3ajustes independientes64: los prefijos64coincidieron exactamente en estructura y predicciones con esos ajustes. Todos los prefijos validaron offset/métrica nativa/precisión/hojas/límites; selección, hashes de modelos internos y predicciones finales fueron iguales con payload exterior alterado. Replayde45objetivos internos y finales sin ajuste exacto.\n\n'
    text+='Se reutilizaron75tablas internas protegidasP84porSHA, con cotejo nuevo de claves/grupos, sin repetir CDFo tomar niveles/qexteriores. No hay mejor longitud real, score exterior nuevo o CSVadmitido. Una evaluación posterior conserva todas las guardas y transferencia propia; puede reutilizar finales64exactosP90ypriorsexteriores conocidos en sus mismos ámbitos, nunca dentro de un entrenamientointerno distinto. Cero ajustes reales/CDF/2025/envíos. B00/F3cyadversos preservados,2024abierto adaptativo; presión de límites no prueba mejora privada, sin revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic.json')+'; '+w.rel(OUT/'bindings.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        'new_real_fits':0,'new_CDF_fits':0,'new_scores':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P92-RONDAS-RESULTADO','P92: selector protegido y equivalencia de prefijos, sin ajuste real')}
    archive=R/'privado'/('corte_P92_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P92'),(R/'registro/semana2_mision_privada_actual.json','P92')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    cp=R/'registro/semana2_contadores_propios_actual.json';w.update(cp,{'phase2_private_P92_length_selector_preflight':{**receipt,'synthetic':w.read(OUT/'synthetic.json')}},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P92=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P92: selector de rondas, preflight\n\nCodex, '+receipt['utc']+'.36máximos nativos sintéticos/3controles64/75tablas propias reutilizadas; cero ajuste real/CDF/scoring/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_length_selector_preflight_index':w.rel(INDEX),'week_2_private_length_selector_preflight_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_real_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
