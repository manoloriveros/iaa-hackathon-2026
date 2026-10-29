"""Prior monetario de dos fuentes fijas para el mismo GLM destino directo."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import warnings
import math
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p76_same_direct_GLM',R/'herramientas/preparar_GLM_fuente_directa_P74.py')
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
m=r.m;q=r.q;w=r.w;pd=r.pd;np=r.np;BASE=r.BASE
OUT=BASE/'P76_GLM_prior_dos_fuentes_preflight_20261027'
PLAN=R/'registro/semana2_GLM_prior_dos_fuentes_preflight_plan.json';INDEX=R/'registro/semana2_GLM_prior_dos_fuentes_preflight_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P76_PRIOR_DOS_FUENTES_PREFLIGHT.md'
SOURCE=BASE/'A1S_nucleo_20261026_v1/source_models'
ANCHORS=None


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def anchors():
    global ANCHORS
    if ANCHORS is None:
        plan=w.read(R/'registro/semana2_mision017_A1S_fuente_plan_v1.json');values={}
        for line in q.LINES:
            records=[]
            for seed in plan['seeds']:
                folder=SOURCE/f'{line}_seed{seed}_full';fit=w.read(folder/'fit_record.json');app=w.read(folder/'application.json')
                assert fit['parameters']['seed']==seed and abs(app['source_weighted_relative_mean']-1)<2e-12
                records.append({'seed':seed,'log_source_base':fit['initial_base'],'log_source_center':app['center']})
            loglevel=math.fsum(z['log_source_base']+z['log_source_center'] for z in records)/len(records)
            values[line]={'source_annual_monetary_anchor':math.exp(loglevel),'log_anchor':loglevel,'source_seed_records':records}
        ANCHORS=values
    return ANCHORS


def annual_prior(frame):
    line=frame.line.unique().item();scale=anchors()[line]['source_annual_monetary_anchor']
    a=frame.annual_A1S.to_numpy(float)*scale;b=frame.annual_T2b.to_numpy(float)
    assert np.isfinite(a).all() and (a>0).all() and np.isfinite(b).all() and (b>0).all()
    value=.5*a+.5*b;assert np.isfinite(value).all() and (value>0).all();return value


def ultimate_source_offset(frame):
    result=annual_prior(frame)*frame.exposure_calendar.to_numpy(float);assert np.isfinite(result).all() and (result>0).all();return result


def fit(frame,line,checkpoint=None):
    train=frame.loc[~frame.is_held].copy();assert set(train.group_id).isdisjoint(set(frame.loc[frame.is_held,'group_id']))
    x,pre=r.design(train,line);y=train.T0.to_numpy(float);base=ultimate_source_offset(train)*train.q_paired.to_numpy(float)
    assert np.isfinite(y).all() and (y>=0).all() and np.isfinite(base).all() and (base>0).all()
    weight=np.sqrt(base);target=y/base;model=r.TweedieRegressor(**r.PARAMS)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',r.ConvergenceWarning);model.fit(x,target,sample_weight=weight)
    artifact={'line':line,'preprocess':pre,'coef':model.coef_.tolist(),'intercept':float(model.intercept_),'parameters':r.PARAMS,'sklearn_version':r.sklearn.__version__,
        'n_iter':int(model.n_iter_),'warnings':[str(z.message) for z in caught],'fit_row_ids_digest':m.p.b.digest(sorted(train.row_id)),
        'fit_groups_digest':m.p.b.digest(sorted(set(train.group_id))),'source_offset':'Fixed arithmetic half sourceA1Smonetaryproxy + sourceT2bannualproxy, then calendar and ownqfor observed fit.',
        'source_A1S_anchor':anchors()[line]}
    if checkpoint is not None:dump(checkpoint,artifact)
    relative=np.exp(x@model.coef_+model.intercept_);assert np.allclose(relative,model.predict(x),rtol=2e-13)
    direct=float(m.e.unit(y,base*relative).sum());converted=r.mean_tweedie_deviance(target,relative,power=1.5,sample_weight=weight)*weight.sum()
    assert math.isclose(direct,converted,rel_tol=2e-12,abs_tol=1e-7)
    score=weight*(np.sqrt(relative)-target/np.sqrt(relative))/weight.sum();gradient=np.r_[score.sum(),x.T@score+r.PARAMS['alpha']*model.coef_]
    artifact.update(gradient_inf=float(np.max(np.abs(gradient))),offset_homogeneity_loss_match=True,manual_linear_prediction_matches_API=True)
    return artifact


def forward(frame,artifact):
    # Persisted scalar anchor makes inference independent of live training metadata.
    x,_=r.design(frame,artifact['line'],artifact['preprocess']);relative=np.exp(x@np.asarray(artifact['coef'])+artifact['intercept'])
    rate=.5*frame.annual_A1S.to_numpy(float)*artifact['source_A1S_anchor']['source_annual_monetary_anchor']+.5*frame.annual_T2b.to_numpy(float)
    result=rate*frame.exposure_calendar.to_numpy(float)*relative;assert np.isfinite(result).all() and (result>0).all();return result,relative


def independent_math(train,artifact):
    x,_=r.design(train,artifact['line'],artifact['preprocess']);base=ultimate_source_offset(train)*train.q_paired.to_numpy(float)
    y=train.T0.to_numpy(float);relative=np.exp(x@np.asarray(artifact['coef'])+artifact['intercept'])
    direct=math.fsum((4*y/np.sqrt(base*relative)+4*np.sqrt(base*relative)-8*np.sqrt(y)).tolist())
    transformed=math.fsum((np.sqrt(base)*(4*(y/base)/np.sqrt(relative)+4*np.sqrt(relative)-8*np.sqrt(y/base))).tolist())
    assert math.isclose(direct,transformed,rel_tol=2e-12,abs_tol=1e-7)
    weight=np.sqrt(base);score=weight*(np.sqrt(relative)-(y/base)/np.sqrt(relative))/weight.sum();gradient=np.r_[score.sum(),x.T@score+r.PARAMS['alpha']*np.asarray(artifact['coef'])]
    assert math.isclose(float(np.max(np.abs(gradient))),artifact['gradient_inf'],rel_tol=2e-9,abs_tol=2e-13)
    for j in range(min(3,x.shape[1])):
        scalar=math.fsum((x[:,j]*score).tolist())+r.PARAMS['alpha']*artifact['coef'][j];assert math.isclose(scalar,gradient[j+1],abs_tol=2e-13)
    return {'fixed_half_offset_scalar_loss_identity':True,'gradient_scalar_and_vector_match':True,'gradient_inf':artifact['gradient_inf']}


def synthetic():
    rng=np.random.default_rng(2026102776);n=600;records=[]
    for line in q.LINES:
        i=np.arange(n);f=pd.DataFrame({'row_id':['s'+str(j) for j in i],'line':line,'group_id':['g'+str(j) for j in i],'is_held':i%5==0,'fold':i%5,'year':2023+(i//5)%2,
            'new_business':(i//10)%2,'T0':np.round(rng.gamma(2,90,n)*(rng.random(n)<.4),2),'reserve':0.,'annual_A1S':np.exp(rng.normal(0,.4,n)),
            'annual_T2b':np.exp(rng.normal(5,.5,n)),'exposure_calendar':rng.uniform(.1,1,n),'q_paired':rng.uniform(.3,1,n)})
        for name in r.NUM[line]:f[name]=rng.choice([0.,10.,100.],n)
        for name in r.CAT[line]:
            if name!='new_business':f[name]=rng.choice(['a','b','c'],n)
        folder=OUT/'synthetic'/line;a=m.once(folder,'primary',lambda:fit(f,line,folder/'primary_raw.json'))
        b=m.once(folder,'adverse',lambda:fit(r.poison(f,line),line,folder/'adverse_raw.json'));assert a==b
        assert not a['warnings'] and a['gradient_inf']<1e-5
        checks=independent_math(f.loc[~f.is_held],a);held=f.loc[f.is_held];value,rel=forward(held,a)
        clean=held.drop(columns=['T0','reserve','q_paired']);other,rr=forward(clean,json.loads(json.dumps(b)));assert np.array_equal(value,other) and np.array_equal(rel,rr)
        subset=np.arange(0,len(held),7);small,_=forward(clean.iloc[subset],a);assert np.allclose(small,value[subset],rtol=2e-13,atol=1e-13)
        records.append({'line':line,'held_all_payload_fit_invariant':True,'JSON_replay_exact':True,'fixed_source_anchor_in_artifact':True,'ultimate_no_q_target_or_batchcenter':True,
            'subset_projective_given_fixed_source_inputs':True,'independent_math':checks})
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_GLMfits':3,'synthetic_adverse_GLMfits_separate':3,'new_real_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_scores':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    previous=BASE/'P75_validacion_GLM_fuente_directa_20261027';assert w.read(previous/'completion_receipt.json')['report_sha256']==w.sha(previous/'report.json')
    parent=w.read(r.PLAN);m.check_sources(parent);source_plan=w.read(R/'registro/semana2_mision017_A1S_fuente_plan_v1.json')
    paths=[Path(__file__),r.PLAN,r.OUT/'report.json',r.OUT/'completion_receipt.json',previous/'report.json',previous/'completion_receipt.json',R/'herramientas/entrenar_nucleo_A1S.py',R/'registro/semana2_mision017_A1S_fuente_plan_v1.json']
    for line in q.LINES:
        for seed in source_plan['seeds']:
            folder=SOURCE/f'{line}_seed{seed}_full';app=w.read(folder/'application.json')
            assert w.sha(folder/'target_components.parquet')==app['outputs']['target_components.parquet']
            paths += [folder/'fit_record.json',folder/'application.json',folder/'target_components.parquet']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'New monetary source-anchor bridge and SAMEdirect GLMsynthetic preflight; historical2023/24algebra only, no model inference/real fit/score.',
        'need':'P75prior defaults to sourceT2bwhile A1Sonly has a penalized feature coefficient; it fails despite no target-price ancestors. The established reference uses equal arithmetic source contributions AFTERtarget calibration. Test a different SOURCE-ONLYequal monetary prior without restoring those target calibrations. This is not exactS2/F3creproduction or proof that source prior caused P75loss.',
        'hypothesis':'Anchoring the same targetGLMtoward both developed risk signals may retain complementary source information without target-base-offset variance. Unknown gain; no weight search or claim of optimum.',
        'configuration':{'seeds':source_plan['seeds'],'source_anchor':'For eachline/source seed, cached rawdelta d, sourcecenter c, initial logbase b: sourceannualproxy=exp(b+d)=exp(b+c)*exp(d-c). Three-seed geometric anchor=exp(mean_seed(b+c)); canonicalrelativeA1S=exp(mean_seed(d-c)). All b/cwere learned ONLYon developed source data.',
            'offset_change_only':'annualprior=.5*sourceA1Srelative*source_monetary_anchor+.5*originalannualT2bsource. Observedoffset=annualprior*calendar*ownP64q; ultimate ignoresq. Source monetary rates are conditional model proxies per completed-cost exposure-year, not identified ultimate costs.',
            'same_fields_and_model':'EXACT P74/P75numeric/categorical/preprocessing/alpha1parameters, including original logT2b/logA1Ssignals; no new signal, target price base, source fit, field pruning or tuned coefficient/weight.',
            'source_averaging':'Use all3source seeds symmetrically, no seed selection. Different source level/CDFdefinitions can still yield poor transport even with common monetary units.',
            'historical_scope':'Read cached per-seed components with explicit yearin2023/24filters; no2025vector derivation/native inference/testprice or public probe.'},
        'preflight_criterion':'Independent historical algebra between rawdelta+initialbase and relative*sourceanchor, scalar three-seed sum and exact keys; actual held payload poison fit invariance, objective/gradient checks, persisted anchor/JSONreplay and projectivity. Source scalar extraction not a refit.',
        'future_budget':{'primary_GLMfits':15,'adverse_GLMfits_separate':15,'new_target_base_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'future_criterion':'Every unchanged P75predictive/cohort/family16/scenario/level/influence and convergence gate. Pooledfail prevents admission; pooledpass needs OWN2023-only conditional-transfer reporting/directGLMbefore CSV. No alpha, field, weight or selected-line rescue.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits']+['Half arithmetic source prior differs from equal AFTERtargetcalibration source prices; no historical reference identity.','Pure source anchors/curves/relative risks remain conditional developed2024proxies; no independent ultimate or as-of2023certification.'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P76registra puente monetario fuente y preflight del MISMOGLMdirecto: fuenteA1Srelativa pasa a proxyanual monetario con sus b0/centros DESARROLLADOSya guardados,3semillas simétricas; prior aritmético fijo50/50con T2bantes del GLM. Mismos campos/preprocesamiento/alpha1, sin calibraciones targetbase o pesos elegidos. No replicaS2que mezcla DESPUÉSde calibraciones target. Verificaré exp(b+rawdelta)contra ancla*relativa por otro método y claves históricas2023/24filtradas, sin inferir2025.3+3GLMsintéticos, cero ajuste o scores reales; nueva evaluación exigiría15+15GLMyTODASlas guardas/transferencia. No causalidad atribuida al priorP75ni último identificado. B00preservado,2024abierto y ceroenvíos. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P76registered_before_two_source_monetary_prior_bridge','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P76-PRIOR-PREVIO','P76: dos señales fuente en escala monetaria, antes de probar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);m.check_sources(plan);assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    source_anchors=anchors();dump(OUT/'source_anchors.json',source_anchors);bindings=[]
    for line in q.LINES:
        frame=r.frame_for(line,0);logs=[]
        for item in source_anchors[line]['source_seed_records']:
            folder=SOURCE/f'{line}_seed{item["seed"]}_full'
            cached=pd.read_parquet(folder/'target_components.parquet',columns=['row_id','year','raw_delta','log_relative'],filters=[('year','in',[2023,2024])]).set_index('row_id').loc[frame.row_id]
            assert cached.index.is_unique and np.array_equal(cached.year,frame.year)
            assert np.allclose(cached.raw_delta-item['log_source_center'],cached.log_relative,rtol=2e-13,atol=2e-13)
            logs.append(item['log_source_base']+cached.raw_delta.to_numpy(float))
        direct=np.exp(np.mean(np.stack(logs),axis=0));by_relative=frame.annual_A1S.to_numpy(float)*source_anchors[line]['source_annual_monetary_anchor']
        assert np.allclose(direct,by_relative,rtol=2e-12,atol=1e-12)
        for pos in np.linspace(0,len(frame)-1,17,dtype=int):
            scalar=math.exp(math.fsum(float(z[pos]) for z in logs)/len(logs));assert math.isclose(scalar,float(by_relative[pos]),rel_tol=2e-12)
        prior=annual_prior(frame);scalar=.5*by_relative+.5*frame.annual_T2b.to_numpy(float);assert np.array_equal(prior,scalar)
        bindings.append({'line':line,'rows':len(frame),'source_anchor':source_anchors[line]['source_annual_monetary_anchor'],'historical_years':[2023,2024],
            'rawdelta_vs_relative_monetary_proxy_algebra_match':True,'no_native_inference_or_source_refit':True})
    dump(OUT/'synthetic.json',synthetic());m.check_sources(plan)
    dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P76two_source_prior_algebra_and_GLM_synthetic_passed','plan_sha256':w.sha(PLAN),'bindings':bindings,
        'source_anchors':w.rel(OUT/'source_anchors.json'),'source_anchors_sha256':w.sha(OUT/'source_anchors.json'),'new_real_fits':0,'new_source_model_inference':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'preflight':'passed','historical_source_bindings':3,'new_real_fits':0,'new_source_inference':0,'new_scores':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');m.check_sources(w.read(PLAN))
    next_unit='P77: register/commit same single direct GLMwith fixed half SOURCE-monetary prior,15primary/15adverse fits, unchanged fields/alpha1and every previous gate. No target-base/source/CDFrefits, source anchors fixed and persisted. Pooledpass requires OWN2023-only conditional transfer before any CSV.'
    text='# P76: prior de dos fuentes, preflight\n\nCodex, '+utc()+'. A1Srelativa se convierte a proxy monetario anual con las bases/centros de sus modelos desarrollados ya guardados: exp(b+d)=exp(b+c)exp(d-c), y el promedio geométrico conserva todas las3semillas. La mezcla aritmética50/50conT2bserá el prior del mismo GLMdirecto, sin fuente o nivel aprendido con costes emergentes. No reproduce la referencia que mezcla después de calibrar ambos componentes en destino.\n\n'
    text+='La identidad se contrastó por rutas vectoriales y sumas escalares independientes, con claves exactas y lectura explícita solo2023/24de los caches. No se cargaron modelos fuente para inferencia, ajustaron anclas nuevas o derivaron2025. TresGLMprimarios/3adversos sintéticos pasaron veneno retenido antes de preproceso, objetivo/gradiente por otro método, ancla persistida, replayJSONyproyección por subconjunto.\n\n'
    text+='Mismos campos/alpha1/preproceso delP75, sin búsqueda de pesos, fuente o señal adicional. Costes fuente en moneda común son proxies condicionados por modelos/CDFdistintos, no último identificado ni garantía de transporte. B00/F3cyalternativas preservados;2024abierto adaptativo, cero ajustes reales/CDF/scores/2025/envíos y sin revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        'new_real_fits':0,'new_source_inference':0,'new_CDF_fits':0,'new_scores':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P76-PRIOR-RESULTADO','P76: puente monetario fuente y GLM sintético, sin ajuste real')}
    archive=R/'privado'/('corte_P76_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P76'),(R/'registro/semana2_mision_privada_actual.json','P76')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    cp=R/'registro/semana2_contadores_propios_actual.json';w.update(cp,{'phase2_private_P76_two_source_prior_preflight':{**receipt,'synthetic':w.read(OUT/'synthetic.json')}},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P76=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P76: prior de dos fuentes\n\nCodex, '+receipt['utc']+'.Álgebra monetaria fuente histórica y flujo GLMsintético pasaron, cero ajuste real/CDF/scoring/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_two_source_prior_preflight_index':w.rel(INDEX),'week_2_private_two_source_prior_preflight_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_real_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
