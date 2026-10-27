"""Mismo GLM P82 con prior de dos fuentes niveladas en su propio entrenamiento."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import warnings
import math
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p87_existing_band_GLM',R/'herramientas/preparar_GLM_bandas_negocio_P81.py')
k=importlib.util.module_from_spec(s);s.loader.exec_module(k)
r=k.r;m=k.m;q=k.q;w=k.w;np=k.np;pd=k.pd;BASE=k.BASE
SCALAR=r.p.k.core.b
OUT=BASE/'P87_prior_calibrado_preflight_20261027'
PLAN=R/'registro/semana2_prior_calibrado_GLM_preflight_plan.json';INDEX=R/'registro/semana2_prior_calibrado_GLM_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P87_PRIOR_CALIBRADO_GLM_PREFLIGHT.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def calibrate_levels(train,line):
    y=train.T0.to_numpy(float);exposure=train.exposure_calendar.to_numpy(float)*train.q_paired.to_numpy(float)
    assert np.isfinite(y).all() and (y>=0).all() and np.isfinite(exposure).all() and (exposure>0).all()
    assert np.isin(train.new_business.to_numpy(int),[0,1]).all()
    components={}
    for name in ['A1S','T2b']:
        raw=train['annual_'+name].to_numpy(float);base=raw*exposure
        assert np.isfinite(base).all() and (base>0).all()
        level=SCALAR.factor(y,base);assert level>0
        cells=SCALAR.cell_levels(train,base,level)
        components[name]={'line_level':level,'cell_levels':cells,'input_units':'dimensionless source relative risk' if name=='A1S' else 'source CU/exposure-year',
            'level_units':'target CU/exposure-year per relative risk' if name=='A1S' else 'dimensionless target/source scale'}
    return {'line':line,'components':components,'business_credibility_K':400,'business_credibility_form':'geometric npositive/(npositive+400)',
        'fit_row_ids_digest':m.p.b.digest(sorted(train.row_id)),'fit_groups_digest':m.p.b.digest(sorted(set(train.group_id))),
        'target_learned_parameters':6,'no_target_shape_or_price_feature':True}


def annual_prior(frame,calibration):
    nb=frame.new_business.to_numpy(int);assert np.isin(nb,[0,1]).all()
    pieces=[]
    for name in ['A1S','T2b']:
        raw=frame['annual_'+name].to_numpy(float);levels=calibration['components'][name]['cell_levels']
        value=raw*np.array([levels[str(business)] for business in nb]);assert np.isfinite(value).all() and (value>0).all();pieces.append(value)
    return .5*pieces[0]+.5*pieces[1]


def ultimate_offset(frame,calibration):
    base=annual_prior(frame,calibration)*frame.exposure_calendar.to_numpy(float);assert np.isfinite(base).all() and (base>0).all();return base


def fit(frame,line,checkpoint=None):
    k.setup();train=frame.loc[~frame.is_held].copy();assert set(train.group_id).isdisjoint(set(frame.loc[frame.is_held,'group_id']))
    calibration=calibrate_levels(train,line)
    if checkpoint is not None:dump(checkpoint.with_name(checkpoint.stem+'_levels.json'),calibration)
    x,pre=k.design(train,line);y=train.T0.to_numpy(float);base=ultimate_offset(train,calibration)*train.q_paired.to_numpy(float)
    weight=np.sqrt(base);target=y/base;model=r.TweedieRegressor(**r.PARAMS)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',r.ConvergenceWarning);model.fit(x,target,sample_weight=weight)
    artifact={'line':line,'preprocess':pre,'coef':model.coef_.tolist(),'intercept':float(model.intercept_),'parameters':dict(r.PARAMS),'sklearn_version':r.sklearn.__version__,
        'n_iter':int(model.n_iter_),'warnings':[str(z.message) for z in caught],'prior_level_calibration':calibration,
        'fit_row_ids_digest':calibration['fit_row_ids_digest'],'fit_groups_digest':calibration['fit_groups_digest'],
        'source_offset':'Fixed half after own-training percomponent line/business level calibration; no target-learned shape risk feature.',
        'rating_form':'Same P82business-specific history/NCBbands and other main effects'}
    if checkpoint is not None:dump(checkpoint,artifact)
    relative=np.exp(x@model.coef_+model.intercept_);assert np.allclose(relative,model.predict(x),rtol=2e-13)
    direct=float(m.e.unit(y,base*relative).sum());other=r.mean_tweedie_deviance(target,relative,power=1.5,sample_weight=weight)*weight.sum()
    assert math.isclose(direct,other,rel_tol=3e-12,abs_tol=1e-7)
    score=weight*(np.sqrt(relative)-target/np.sqrt(relative))/weight.sum();gradient=np.r_[score.sum(),x.T@score+r.PARAMS['alpha']*model.coef_]
    artifact.update(gradient_inf=float(np.max(np.abs(gradient))),conditional_GLM_offset_loss_identity=True,manual_linear_prediction_matches_API=True)
    return artifact


def forward(frame,artifact):
    k.setup();x,_=k.design(frame,artifact['line'],artifact['preprocess']);relative=np.exp(x@np.asarray(artifact['coef'])+artifact['intercept'])
    value=ultimate_offset(frame,artifact['prior_level_calibration'])*relative;assert np.isfinite(value).all() and (value>0).all();return value,relative


def level_math(train,calibration):
    y=train.T0.to_numpy(float);nb=train.new_business.to_numpy(int);exposure=train.exposure_calendar.to_numpy(float)*train.q_paired.to_numpy(float);records=[]
    for name,obj in calibration['components'].items():
        base=train['annual_'+name].to_numpy(float)*exposure
        scalar=math.fsum((y/np.sqrt(base)).tolist())/math.fsum(np.sqrt(base).tolist());assert math.isclose(scalar,obj['line_level'],rel_tol=3e-13)
        derivative=math.fsum((np.sqrt(base*scalar)-y/np.sqrt(base*scalar)).tolist());normalizer=math.fsum(np.sqrt(base*scalar).tolist())
        assert abs(derivative)<=max(1e-9,3e-13*normalizer)
        for business in [0,1]:
            cell=nb==business;own=math.fsum((y[cell]/np.sqrt(base[cell])).tolist())/math.fsum(np.sqrt(base[cell]).tolist());n=sum(float(v)>0 for v in y[cell])
            expected=scalar*math.exp(n/(n+400)*math.log(own/scalar));assert math.isclose(expected,obj['cell_levels'][str(business)],rel_tol=3e-13)
        records.append({'component':name,'global_moment_and_business_K400_scalar_match':True,'raw_global_logscale_derivative_zero':True})
    return records


def independent_math(train,artifact):
    k.setup();cal=artifact['prior_level_calibration'];levels=level_math(train,cal)
    x,_=k.design(train,artifact['line'],artifact['preprocess']);base=ultimate_offset(train,cal)*train.q_paired.to_numpy(float);y=train.T0.to_numpy(float)
    relative=np.exp(x@np.asarray(artifact['coef'])+artifact['intercept'])
    direct=math.fsum((4*y/np.sqrt(base*relative)+4*np.sqrt(base*relative)-8*np.sqrt(y)).tolist())
    converted=math.fsum((np.sqrt(base)*(4*(y/base)/np.sqrt(relative)+4*np.sqrt(relative)-8*np.sqrt(y/base))).tolist())
    assert math.isclose(direct,converted,rel_tol=3e-12,abs_tol=1e-7)
    weight=np.sqrt(base);score=weight*(np.sqrt(relative)-(y/base)/np.sqrt(relative))/weight.sum();grad=np.r_[score.sum(),x.T@score+artifact['parameters']['alpha']*np.asarray(artifact['coef'])]
    assert math.isclose(float(np.max(np.abs(grad))),artifact['gradient_inf'],rel_tol=2e-9,abs_tol=2e-13)
    for j in range(min(3,x.shape[1])):assert math.isclose(math.fsum((x[:,j]*score).tolist())+artifact['parameters']['alpha']*artifact['coef'][j],grad[j+1],abs_tol=2e-13)
    return {'calibration_scalar_checks':levels,'conditional_GLM_loss_and_gradient_scalar_match':True,'gradient_inf':artifact['gradient_inf'],
        'limit':'Conditional GLMstationarity given estimated prior; not a joint optimum for the staged shrunk calibration and GLM.'}


def synthetic():
    rng=np.random.default_rng(2026102787);n=720;i=np.arange(n);records=[]
    for line in q.LINES:
        f=pd.DataFrame({'row_id':['s'+str(j) for j in i],'line':line,'group_id':['g'+str(j) for j in i],'is_held':i%5==0,'fold':i%5,
            'year':2023+(i//5)%2,'new_business':(i//10)%2,'T0':rng.gamma(2,80,n)*(rng.random(n)<.4),'reserve':0.,
            'annual_A1S':np.exp(rng.normal(0,.4,n)),'annual_T2b':np.exp(rng.normal(5,.5,n)),'exposure_calendar':rng.uniform(.1,1,n),'q_paired':rng.uniform(.3,1,n)})
        for name in k.BASE_NUM[line]:f[name]=rng.choice([0.,10.,100.],n)
        for name in k.BASE_CAT[line]:
            if name!='new_business':f[name]=rng.choice(['a','b','c'],n)
        f['prior_claims_5y']=rng.choice([0.,1.,2.,np.nan],n)
        if line=='motor':f['ncb_years']=rng.choice([0.,1.,2.,3.,5.,6.,9.,10.,np.nan],n)
        folder=OUT/'synthetic'/line;primary=m.once(folder,'primary',lambda:fit(f,line,folder/'primary_raw.json'))
        adverse=m.once(folder,'adverse',lambda:fit(k.poison(f,line),line,folder/'adverse_raw.json'));assert primary==adverse
        assert not primary['warnings'] and primary['gradient_inf']<1e-5
        math_checks=independent_math(f.loc[~f.is_held],primary);held=f.loc[f.is_held];value,relative=forward(held,primary)
        clean=held.drop(columns=['T0','reserve','q_paired']);other,rr=forward(clean,json.loads(json.dumps(adverse)));assert np.array_equal(value,other) and np.array_equal(relative,rr)
        small=np.arange(0,len(held),7);subset,_=forward(clean.iloc[small],primary);assert np.allclose(subset,value[small],rtol=2e-13,atol=1e-13)
        order=np.arange(len(held))[::-1];shuffled,_=forward(clean.iloc[order],primary);assert np.allclose(shuffled,value[order],rtol=2e-13,atol=1e-13)
        # Unit transformation of the stored A1Srelative risk and its multiplier.
        scaled=clean.copy();scaled['annual_A1S']*=10.;cal=json.loads(json.dumps(primary['prior_level_calibration']))
        cal['components']['A1S']['line_level']/=10.;cal['components']['A1S']['cell_levels']={key:v/10 for key,v in cal['components']['A1S']['cell_levels'].items()}
        assert np.allclose(annual_prior(scaled,cal),annual_prior(clean,primary['prior_level_calibration']),rtol=3e-14)
        records.append({'line':line,'full_held_payload_poison_calibration_and_GLM_exact':True,'JSONwhole_flow_exact':True,'ultimate_no_cost_q_or_live_calibration':True,
            'subset_permutation_projective_given_sources':True,'prior_units_equivariant':True,'independent_math':math_checks})
    train=f.loc[~f.is_held].copy();train.loc[train.new_business.eq(1),'T0']=0.
    try:calibrate_levels(train,line)
    except AssertionError:pass
    else:raise AssertionError('Business with zero positive support must be rejected, no silent fallback')
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_GLMfits':3,'synthetic_adverse_GLMfits_separate':3,
        'synthetic_primary_component_level_sets':6,'synthetic_adverse_component_level_sets_separate':6,'synthetic_primary_stored_level_parameters':18,'synthetic_adverse_level_parameters_separate':18,
        'zero_positive_business_guard_rejected_before_GLM':True,'new_real_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    previous=BASE/'P86_prior_y_selector_20261027';assert w.read(previous/'completion_receipt.json')['report_sha256']==w.sha(previous/'report.json')
    parent=w.read(k.PLAN);m.check_sources(parent)
    paths=[Path(__file__),Path(k.__file__),Path(SCALAR.__file__),k.PLAN,previous/'report.json',previous/'completion_receipt.json',
        R/'registro/semana2_GLM_bandas_negocio_validacion_plan.json',R/'registro/semana2_mision_privada_plan_v1.json']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'New simple percomponent line/business level prior before SAMEP82GLM; synthetic whole flow and15strict real bindings only, no real learning.',
        'need':'P85training-only selection chose alpha1in all folds, exactly reproducing rejectedP82. P86quantified7-16percent relative-level differences between separately calibrated P65sources and a common rescale of developed-only prior. This is a structural difference, not an established cause or an unshaped optimal level estimate.',
        'hypothesis':'Calibrate only broad line/business levels of each frozen source BEFOREfixedhalf and GLM, retaining source risk allocation without target-trained history/NCBshape base or noisy row-level price feature. Benefit unknown.',
        'one_change':'Replace developed-only monetary source anchor prior by TWOsource components with own-target-training scalar levels before arithmetic50/50mixture. No P65levels copied; unshaped source inputs reestimated within train.',
        'configuration':{'components':'A1Sannual relative dimensionless and T2bannual source monetary proxy. Multiply each by calendar*ownqfor level learning. Rawglobal level=sum(y/sqrt(mu))/sum sqrt(mu); perbusiness ownmoment shrunk geometrically to linelevel with npositive/(npositive+400), EXACTexisting standard rule.',
            'support':'Require positive line and bothbusiness moments, finite source/exposure/target; no new neutral fallback or threshold relaxation.',
            'GLM':'EXACTP82source logsignals/rating fields/history-NCBbusinessbands/preprocessing/alpha1and otherparameters. Prior learned on same targettraining as GLM, allstage exclusion protects held; not independent stacking or jointly optimized stage parameters.',
            'units':'A1Slevel learns targetCU/exposure-year per relative risk; T2blevel is target/source ratio. Both calibrated annualcomponents have comparable target proxy units before mixing. Original developedA1Sanchor not needed after targetleveling.',
            'normalization':'Same transformed relative-GLMobjective y/bwith sqrt(b)weights, alpha1. New bchanges transformedtargets/weights and likelihood-to-penalty normalization too; not an isolated causal test of source weights.',
            'application':'Only stored calibration plus source risks/NB/calendar, no q/target/live reestimation/applicationnormalizer in ultimate. Shared currentFSpPROXYobservation remains an assumption; apply ownqafter ultimate for evaluation.'},
        'preflight_criterion':'3primary/3adverse whole stagedsyntheticfits, ALLheld payload poison before levelselector/design, closedlevels and conditionalGLMmath independently, levelcheckpoint beforeGLM, JSONexact, unit/subset/permutation checks, unsupportedbusiness reject beforeGLM.15unchanged real input bindings without fitting.',
        'future_budget':{'primary_GLMfits':15,'adverse_GLMfits_separate':15,'primary_component_level_sets':30,'adverse_component_level_sets_separate':30,'new_primary_closed_levels':90,'adverse_closed_levels_separate':90,
            'new_source_fits':0,'new_shape_price_base_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'future_criterion':'Separate P88registration/commit; EVERYunchanged P82outerpredictive/cohort/scenario/family16/level/influence/convergence guard. Pooledpass requires own2023-only conditionaltransfer of ALLstages beforeCSV. No alpha/fields/line/weights rescue.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits']+['Simple target calibration is learned, not a pure-source offset or a known optimal source mixture. Whole pipeline evaluation includes that estimation.','Line-level scalar stationarity and conditionalGLMgradient do not certify a joint maximum likelihood optimum of the staged shrunk pipeline.'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P87 registra antes de probar el mismo GLM P82 con un prior nuevo: cada señal fuente se nivela usando SOLO su entrenamiento, nivel general Tweedie y nuevo/renovación con credibilidad geométrica K400; después mezcla fija50/50 y mismo GLM alpha1/campos/bandas. Sin formas de precio NCB/historia, pesos elegidos o niveles copiados de P65. No offset puramente fuente ni óptimo conjunto: ambos pasos aprenden del mismo train y se valida TODO el algoritmo exterior. Cambian b, cocientes/pesos y normalización relativa de la penalización. Tres+3 GLM sintéticos,18+18 niveles guardados, veneno completo, matemática/JSON/unidades/proyección y soporte de negocio; cero ajustes reales/CDF/2025/envíos. Futuro P88:15+15GLM y90+90 niveles, TODAS las guardas y transferencia. B00/adversos conservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P87registered_before_calibrated_prior_synthetic','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P87-NIVELES-PREVIO','P87: niveles por componente antes del mismo GLM, preflight registrado')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    assert not (OUT/'report.json').exists();m.check_sources(w.read(PLAN));assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    dump(OUT/'synthetic.json',synthetic());bindings=[]
    for line in q.LINES:
        for outer in range(5):
            f=k.frame_for(line,outer);assert f.row_id.is_unique and set(f.loc[f.is_held,'group_id']).isdisjoint(set(f.loc[~f.is_held,'group_id']))
            bindings.append({'line':line,'outer':outer,'rows':len(f),'same_strict_P64input_sha256':w.sha(r.p.t.t.OUT/f'input_{line}_{outer}.parquet'),'new_levels_not_estimated':True})
    m.check_sources(w.read(PLAN));dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P87calibrated_prior_whole_synthetic_and_bindings_passed','bindings':bindings,
        'new_real_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'preflight':'passed','bindings':len(bindings),'new_real_fits':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');m.check_sources(w.read(PLAN))
    next_unit='P88: register/commit EXACTP87same-bandGLMwith own-training unshaped percomponent line/business calibratedhalfprior.15primary/15adverseGLMfits,90primary/90adverse closedlevels, no source/shapepricebase/CDFfits. ALLexisting outerguards and conditionaltransfer requirement; no copiedP65levels, alpha/grid/field/line rescue.'
    text='# P87: calibrar niveles antes de la mezcla y del GLM\n\nCodex, '+utc()+'. Se prepara el mismo GLM P82, cambiando su prior: cada fuente recibe niveles generales y por tipo de negocio aprendidos en el entrenamiento propio, con la regla Tweedie y credibilidad K400 ya usada. Luego se mezclan 50/50. No se estiman formas de precio ni se copian niveles de otra receta.\n\n'
    text+='Pasaron tres GLM primarios y tres adversos sintéticos con sus18+18 niveles guardados. El payload retenido completo se alteró antes del selector, la calibración y el preproceso; modelos y niveles coincidieron. Momentos/credibilidad por suma escalar, objetivo y gradiente condicional por otro cálculo, replay JSON exacto y proyección por subconjuntos/permutación. El prior conserva unidades al reexpresar la fuente relativa; un negocio sin positivos fue rechazado antes de ajustar el GLM. Se enlazaron15entradas reales, sin estimar sus nuevos niveles.\n\n'
    text+='La calibración y el GLM aprenden del mismo entrenamiento como algoritmo por etapas. No es un offset puramente fuente, stacking independiente ni un óptimo conjunto. El nuevo prior también cambia la normalización de la verosimilitud frente a alpha1 en el objetivo relativo. La prueba futura evalúa el algoritmo completo, sin atribuir una eventual diferencia solo a pesos fuente. Cero ajustes reales/CDF/scores/2025/envíos. B00/F3c/adversos preservados,2024abierto adaptativo; persisten información fuente/observación/valoración y búsqueda adaptativa, sin revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        'new_real_fits':0,'new_CDF_fits':0,'new_scores':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P87-NIVELES-RESULTADO','P87: prior nivelado protegido, preflight sin ajuste real')}
    archive=R/'privado'/('corte_P87_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P87'),(R/'registro/semana2_mision_privada_actual.json','P87')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    cp=R/'registro/semana2_contadores_propios_actual.json';w.update(cp,{'phase2_private_P87_calibrated_prior_preflight':{**receipt,'synthetic':w.read(OUT/'synthetic.json')}},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P87=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P87: prior nivelado, preflight\n\nCodex, '+receipt['utc']+'.Tres+3GLM sintéticos,18+18niveles guardados y15enlaces; cero ajuste real/CDF/scoring/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_calibrated_prior_preflight_index':w.rel(INDEX),'week_2_private_calibrated_prior_preflight_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_real_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
