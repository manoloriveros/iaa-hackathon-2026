"""Preflight de boosting residual estándar acotado por árbol sobre offsets OOF."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import math
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p71_current_offsets',R/'herramientas/validar_GLM_reporte_actual_P67.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
g=p.g;m=p.m;q=p.q;w=p.w;pd=p.pd;np=p.np;BASE=p.BASE
import lightgbm as lgb
OUT=BASE/'P71_boosting_residual_preflight_20261027'
PLAN=R/'registro/semana2_boosting_residual_preflight_plan.json';INDEX=R/'registro/semana2_boosting_residual_preflight_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P71_BOOSTING_RESIDUAL_PREFLIGHT.md'
ROUNDS=64
PARAMS={'objective':'tweedie','tweedie_variance_power':1.5,'metric':'tweedie','boosting':'gbdt','learning_rate':.03,'num_leaves':7,'max_depth':3,
    'min_data_in_leaf':1000,'lambda_l2':10.,'max_delta_step':.1,'max_bin':63,'feature_fraction':1.,'bagging_fraction':1.,'bagging_freq':0,
    'boost_from_average':False,'deterministic':True,'force_col_wise':True,'num_threads':2,'seed':2026102771,'verbosity':-1}


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def leaf_values(node,depth=0):
    if 'leaf_value' in node:return [(float(node['leaf_value']),int(node.get('leaf_count',0)),depth)]
    return leaf_values(node['left_child'],depth+1)+leaf_values(node['right_child'],depth+1)


def walk(node,row):
    if 'leaf_value' in node:return float(node['leaf_value'])
    assert node['decision_type']=='<='
    return walk(node['left_child'] if float(row[node['split_feature']])<=float(node['threshold']) else node['right_child'],row)


def fit(frame,line,checkpoint=None):
    train=frame.loc[~frame.is_held].copy();held_groups=set(frame.loc[frame.is_held,'group_id'])
    assert set(train.group_id).isdisjoint(held_groups)
    x,pre=g.design(train,line);y=train.T0.to_numpy(float);base=train.baseline_observed.to_numpy(float)
    assert np.isfinite(y).all() and (y>=0).all() and np.isfinite(base).all() and (base>0).all()
    dataset=lgb.Dataset(x,label=y,init_score=np.log(base),feature_name=['x'+str(j) for j in range(x.shape[1])],free_raw_data=False)
    history={};model=lgb.train(PARAMS,dataset,num_boost_round=ROUNDS,valid_sets=[dataset],valid_names=['train'],callbacks=[lgb.record_evaluation(history),lgb.log_evaluation(0)])
    # Save raw model before numerical controls; init_score is external, checked below.
    artifact={'line':line,'preprocess':pre,'model_string':model.model_to_string(),'parameters':PARAMS,'configured_rounds':ROUNDS,'effective_trees':model.num_trees(),
        'lightgbm_version':lgb.__version__,'fit_row_ids_digest':m.p.b.digest(sorted(train.row_id)),'fit_groups_digest':m.p.b.digest(sorted(set(train.group_id))),
        'native_training_metric':history['train']['tweedie'][-1],'label_storage':'LightGBMnative label float32; evaluate original uncappedfloat64T0.'}
    if checkpoint is not None:dump(checkpoint,artifact)
    raw=model.predict(x,raw_score=True);mu=base*np.exp(raw);native_y=np.asarray(dataset.get_label(),float)
    assert np.allclose(y,native_y,rtol=6e-8,atol=0.)
    metric=math.fsum((2*native_y/np.sqrt(mu)+2*np.sqrt(mu)).tolist())/len(y)
    assert math.isclose(metric,artifact['native_training_metric'],rel_tol=3e-12)
    trees=model.dump_model()['tree_info'];values=[leaf_values(tree['tree_structure']) for tree in trees]
    assert 1<=len(trees)<=ROUNDS and all(len(z)<=PARAMS['num_leaves'] for z in values)
    max_leaf=PARAMS['learning_rate']*PARAMS['max_delta_step'];assert max(abs(v[0]) for z in values for v in z)<=max_leaf+1e-12
    assert max(v[2] for z in values for v in z)<=PARAMS['max_depth']
    bound=ROUNDS*max_leaf;assert np.max(np.abs(raw))<=bound+1e-10
    for pos in np.linspace(0,len(x)-1,7,dtype=int):assert math.isclose(math.fsum(walk(tree['tree_structure'],x[pos]) for tree in trees),float(raw[pos]),rel_tol=1e-11,abs_tol=1e-12)
    loaded=lgb.Booster(model_str=artifact['model_string']);assert np.array_equal(raw,loaded.predict(x,raw_score=True))
    artifact.update(native_offset_metric_scalar_match=True,leaf_sum_and_serialization_exact=True,max_absolute_log_correction_bound=bound,
        actual_max_absolute_train_log_correction=float(np.max(np.abs(raw))),actual_min_leaf_count=min(v[1] for z in values for v in z),
        fitted_leaf_values=sum(len(z) for z in values),native_label_max_abs_rounding=float(np.max(np.abs(y-native_y))))
    return artifact


def forward(frame,artifact):
    x,_=g.design(frame,artifact['line'],artifact['preprocess']);model=lgb.Booster(model_str=artifact['model_string']);raw=model.predict(x,raw_score=True)
    assert np.isfinite(raw).all() and np.max(np.abs(raw))<=artifact['max_absolute_log_correction_bound']+1e-10
    relative=np.exp(raw);value=frame.baseline_ultimate.to_numpy(float)*relative
    assert np.isfinite(value).all() and (value>0).all();return value,relative


def independent_math(train,artifact):
    x,_=g.design(train,artifact['line'],artifact['preprocess']);model=lgb.Booster(model_str=artifact['model_string']);raw=model.predict(x,raw_score=True)
    y=train.T0.to_numpy(float).astype('float32').astype(float);mu=train.baseline_observed.to_numpy(float)*np.exp(raw)
    scalar=math.fsum((2*y/np.sqrt(mu)+2*np.sqrt(mu)).tolist())/len(y)
    assert math.isclose(scalar,artifact['native_training_metric'],rel_tol=3e-12)
    original=train.T0.to_numpy(float);deviance=math.fsum((4*original/np.sqrt(mu)+4*np.sqrt(mu)-8*np.sqrt(original)).tolist())
    assert math.isclose(deviance,float(m.e.unit(original,mu).sum()),rel_tol=3e-12)
    return {'native_training_metric_scalar_with_actual_label_precision':scalar,'original_uncapped_Tweedie_deviance_scalar':deviance,
        'offset_in_actual_training_metric_verified':True,'no_stationarity_or_convergence_claim_from_fixed_rounds':True}


def synthetic():
    rng=np.random.default_rng(2026102771);n=6000;records=[]
    for line in q.LINES:
        i=np.arange(n);base=np.exp(rng.normal(4.5,.3,n));excess=rng.choice([0.,10.,100.],n)
        y=np.round(base*np.where(excess==100,2.,.5)*rng.gamma(2,.5,n)*(rng.random(n)<.5)*2,2)
        f=pd.DataFrame({'row_id':['s'+str(j) for j in i],'group_id':['g'+str(j) for j in i],'is_held':i%5==0,'year':2023+(i//5)%2,
            'new_business':(i//10)%2,'T0':y,'reserve':0.,'baseline_ultimate':base,'baseline_observed':base*.8,'q_paired':.8,'exposure_calendar':1.})
        for name in g.NUM[line]:f[name]=excess if name==g.NUM[line][0] else rng.choice([0.,10.,100.],n)
        for name in g.CAT[line]:
            if name!='new_business':f[name]=rng.choice(['a','b','c'],n)
        folder=OUT/'synthetic'/line;a=m.once(folder,'primary',lambda:fit(f,line,folder/'primary_raw.json'))
        b=m.once(folder,'adverse',lambda:fit(g.poison(f,line),line,folder/'adverse_raw.json'));assert a==b
        assert a['fitted_leaf_values']>a['effective_trees'],'Synthetic must exercise splits, not just constant trees'
        checks=independent_math(f.loc[~f.is_held],a);held=f.loc[f.is_held].copy();value,relative=forward(held,a)
        poison=held.copy();poison[['T0','reserve','baseline_observed','q_paired']]=np.nan
        replay,rr=forward(poison,json.loads(json.dumps(b)));assert np.array_equal(value,replay) and np.array_equal(relative,rr)
        records.append({'line':line,'native_training_offset_metric_verified':True,'held_all_payload_learning_invariant':True,'held_labels_q_observedoffset_not_used_by_ultimate':True,
            'JSON_native_model_replay_exact':True,'tree_splits_exercised':True,'fitted_leaf_values':a['fitted_leaf_values'],'actual_min_leaf_count':a['actual_min_leaf_count'],'independent_math':checks})
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_tree_fits':3,'synthetic_adverse_tree_fits_separate':3,'new_real_fits':0,'new_scores':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    previous=BASE/'P70_validacion_GLM_forma_acotada_20261027';assert w.read(previous/'completion_receipt.json')['report_sha256']==w.sha(previous/'report.json')
    parent=w.read(p.PLAN);m.check_sources(parent);inputs=p.verify_inputs()
    paths=[Path(__file__),Path(g.__file__),p.PLAN,p.OUT/'input_report.json',p.OUT/'completion_receipt.json',previous/'report.json',previous/'completion_receipt.json',
        BASE/'P68_GLM_actual_guardado_20261027/report.json',Path(lgb.__file__),Path(lgb.basic.__file__),Path(lgb.engine.__file__),Path(lgb.basic._LIB._name),
        R/'registro/semana2_CatBoost_guardado_validacion_privada_plan.json']
    # Runtime package paths are pinned separately because they are outside ROOT.
    runtime={str(path):w.sha(path) for path in paths if not path.is_relative_to(ROOT)};paths=[path for path in paths if path.is_relative_to(ROOT)]
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'Synthetic full native offset/tree/JSONflow and15real frozen input bindings only, ZEROreal price/CDF/source fit or score.',
        'need':'Standard closed P65and main-effect GLMP67/response-bounded P70fail robustness under verified target/exposure/reporting. Global linear residual correction did not generalize; test a different standard, strongly restricted piecewise response before deeper architectures. This is not proof that interactions explain failure or that more flexibility helps.',
        'distinct_from_prior':'P39replaced a developed-only CatBoost SOURCEinside S2/H1; this learns a FINALtarget residual on the new P67OOFinputs/current reporting, with frozen parents. Historical B03/B05contracts and P39are not repeated.',
        'configuration':{'parameters':PARAMS,'num_boost_round':ROUNDS,'lightgbm_version':lgb.__version__,'input_features':'Exactly P56NUM/CATand baseline annual risk, same train-only median/scale/missing/onehot. Generic xNfeature names map back to saved columns; no new fields or feature search.',
            'objective_offset':'Native Tweedie1.5uses original uncappedT0and init_score=log(OOFbaseline_observed), boost_from_averageFalse. At application model returns residual rawscore; ultimate=baseline_ultimate*exp(rawscore), then ownqfor observed validation.',
            'complexity':'64fixed rounds/depth3/7leaves/min_data1000/L2=10/full rows/features/deterministic2CPU; no early stopping, tree/seed/hyperparameter search or public probe.',
            'step_bound':'Leaf output <=learning_rate*max_delta_step=.003; absolute sum <=.192with64trees. Verify actual dump and leaf path sums, not posthoc prediction clipping.',
            'count_limit':'Record actual leafcounts; native min_data_in_leafis Hessian-based approximate, not a credibility guarantee.',
            'target_precision':'LightGBMnative labelstorage float32is recorded/tested, while all evaluation uses originalfloat64uncappedT0. No row/claim deletion or shape response cap.'},
        'preflight_criterion':'Native train metric equals scalar Tweedieloss WITH actual offset, native label precision explicit, actual tree leaf/depth/output bounds and independent path sums, nonconstant splits exercised, actual held-payload poison invariance, serializationexact, no q/held cost in ultimate.',
        'future_budget':{'primary_final_tree_fits':15,'adverse_final_tree_fits_separate':15,'maximum_trees_per_fit':ROUNDS,'maximum_leaves_per_tree':7,'new_base_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'future_criterion':'All unchanged P67predictive/cohort/family16/scenario/level/influence gates plus native objective/offset/tree integrity. Fixed-round trees do not have a GLMstationarity/convergence gate; no predictive threshold is relaxed. Pooled failure prevents admission; pooled pass requires OWN2023conditional-transfer whole pipeline.',
        'technical_sources':['https://lightgbm.readthedocs.io/en/v4.6.0/pythonapi/lightgbm.Dataset.html','https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html#max_delta_step','https://raw.githubusercontent.com/microsoft/LightGBM/v4.6.0/src/metric/regression_metric.hpp'],
        'runtime_sources':runtime,'sources':{**parent['sources'],**inputs['outputs'],**{w.rel(path):w.sha(path) for path in paths}},
        'limits':['Small-step/shallow restrictions are fixed regularization choices, not proved optimal/private-robust. More piecewise flexibility can still overfit.','Parent targets/reporting/offsets remain uncapped and source2024conditional; adaptive search, market/valuation/tail/master availability and OOF/full training-size shifts persist.'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P71registra un preflight de otro modelo estándar después del falloP65/P67/P70: LightGBMresidual final, no fuenteCatBoostP39. Mismos campos/offsetsOOFP67yobjetivo íntegroTweedie1.5;64rondas fijas, profundidad3/7hojas, min_data1000/L2=10, paso por hoja.003ylogcorrecciónmáxima.192, sin búsqueda o earlystopping. Se probará el offset NATIVOen la métrica real, suma escalar de hojas, precisión de etiquetas, veneno retenido y serialización,3ajustes sintéticos primarios/3adversos;15enlaces reales sin entrenarlos. No se infiere causalidad/interacciones o mejora. Futura evaluación conserva TODASlas guardas predictivas, con integridad de árbol en lugar de estacionariedadGLM; transferencia propia si pasa. Cero fuentes/bases/CDFnuevas/2025/envíos. B00preservado y2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P71registered_before_standard_residual_tree_preflight','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P71-ARBOL-PREVIO','P71: boosting estándar restringido y offset nativo, antes de probar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def check_sources(plan):
    m.check_sources(plan);p.verify_inputs();assert all(w.sha(Path(path))==value for path,value in plan['runtime_sources'].items())


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);check_sources(plan);assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    dump(OUT/'synthetic.json',synthetic());bindings=[]
    for line in q.LINES:
        for outer in range(5):
            f=p.frame_for(line,outer);assert np.array_equal(f.is_held,f.fold.eq(outer)) and f.year.isin([2023,2024]).all()
            assert set(f.loc[~f.is_held,'group_id']).isdisjoint(set(f.loc[f.is_held,'group_id']))
            bindings.append({'line':line,'outer':outer,'rows':len(f),'input_sha256':w.sha(p.OUT/f'input_{line}_{outer}.parquet')})
    check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P71native_offset_tree_synthetic_and_real_bindings_passed','plan_sha256':w.sha(PLAN),'bindings':bindings,
        'new_real_fits':0,'new_scores':0,'new_base_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'preflight':'passed','bindings':15,'new_real_fits':0,'new_scores':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');check_sources(w.read(PLAN))
    next_unit='P72: register/commit fixed64round restricted native-offset residual GBDT,15primary/15adverse fits on exact P67inputs. No base/report/source fits or field/hyperparameter search. Every old predictive/cohort/scenario/family16gate plus actual tree/offset math; transfer OWN2023required after pooled pass, no automatic CSV.'
    text='# P71: boosting residual estándar, preflight\n\nCodex, '+utc()+'. Los GLMactuales no superaron las guardas, incluida la forma con respuesta acotada. Se prepara un boosting final estándar restringido sobre los mismos offsetsOOFycampos, para probar una respuesta por tramos; no se ha demostrado que esa estructura resuelva la falta de generalización.\n\n'
    text+='64rondas fijas, profundidad3/7hojas, min_data1000yL2=10, sin earlystopping o búsqueda. La cota por hoja y la suma de64árboles se comprueban en el modelo real, sin capar predicciones después. La documentación de [LightGBM4.6.0](https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html#max_delta_step) describe esa restricción; el preflight contrasta la implementación instalada.\n\n'
    text+='Tres ajustes sintéticos primarios/3adversos ejercitaron splits, offset nativo real comprobado por métrica escalar, suma de hojas por otro método, límites de árbol, precisiónfloat32de etiquetas y replayJSONnativo exacto. El último no lee q/coste/offsetobservado retenidos. Se enlazaron15entradas reales sin ajustarlas. No se repitieron bases/curvas, ni hubo scoring/2025/envíos. La cuenta mínima de filas por hoja es aproximada en el algoritmo y no acredita credibilidad.\n\n'
    text+='Se mantienen todas las guardas predictivas y la necesidad de transferencia propia; la integridad del algoritmo finito sustituye el control de estacionariedad exclusivo delGLM. B00/F3cyalternativas conservados,2024abierto adaptativo. Persisten supuestos de reporte/fuente/cola/mercado/maestros y selección adaptativa; sin mejora privada acreditada o revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        'new_real_fits':0,'new_base_fits':0,'new_CDF_fits':0,'new_scores':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P71-ARBOL-RESULTADO','P71: offset nativo y árboles verificados, aún sin ajuste real')}
    archive=R/'privado'/('corte_P71_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P71'),(R/'registro/semana2_mision_privada_actual.json','P71')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    cp=R/'registro/semana2_contadores_propios_actual.json';w.update(cp,{'phase2_private_P71_residual_tree_preflight':{**receipt,'synthetic':w.read(OUT/'synthetic.json')}},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P71=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P71: boosting residual estándar, preflight\n\nCodex, '+receipt['utc']+'.Offset/métrica/hojas/veneno/replaynativo pasaron con splits reales;15enlaces, cero ajuste real/scoring/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_residual_boosting_preflight_index':w.rel(INDEX),'week_2_private_residual_boosting_preflight_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_real_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
