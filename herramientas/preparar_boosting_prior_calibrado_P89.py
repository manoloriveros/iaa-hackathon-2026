"""Mismo prior/campos P88; boosting restringido P71 como respuesta final."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);a=importlib.util.module_from_spec(s);s.loader.exec_module(a);return a
k=load('p89_current_calibrated_prior',R/'herramientas/preparar_GLM_prior_calibrado_P87.py')
t=load('p89_fixed_native_tree_engine',R/'herramientas/preparar_boosting_residual_P71.py')
m=k.m;q=k.q;w=k.w;pd=k.pd;np=k.np;BASE=k.BASE
OUT=BASE/'P89_boosting_prior_preflight_20261027'
PLAN=R/'registro/semana2_boosting_prior_preflight_plan.json';INDEX=R/'registro/semana2_boosting_prior_preflight_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P89_BOOSTING_PRIOR_PREFLIGHT.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def setup():k.k.setup();t.g.design=k.k.design


def observed_frame(frame,calibration):
    z=frame.copy();train=~z.is_held;z['baseline_observed']=np.nan;z['baseline_ultimate']=np.nan
    raw=z.loc[train];value=k.ultimate_offset(raw,calibration)
    z.loc[train,'baseline_observed']=value*raw.q_paired.to_numpy(float);z.loc[train,'baseline_ultimate']=value
    return z


def fit(frame,line,checkpoint=None):
    setup();train=frame.loc[~frame.is_held].copy();assert set(train.group_id).isdisjoint(set(frame.loc[frame.is_held,'group_id']))
    calibration=k.calibrate_levels(train,line)
    if checkpoint is not None:dump(checkpoint.with_name(checkpoint.stem+'_levels.json'),calibration)
    z=observed_frame(frame,calibration);artifact=t.fit(z,line,checkpoint)
    assert not any('baseline' in name for name in artifact['preprocess']['columns'])
    artifact.update(prior_level_calibration=calibration,feature_contract='EXACTP88source signals/businessbands/main fields; no target-learned rowprice feature',
        offset_contract='Owntrain line/business scalar source prior, native log observed offset; ultimate applies stored prior/calendar and rawtree correction, no q')
    return artifact


def forward(frame,artifact):
    setup();z=frame.copy();z['baseline_ultimate']=k.ultimate_offset(frame,artifact['prior_level_calibration'])
    return t.forward(z,artifact)


def independent_math(train,artifact):
    setup();z=train.copy();z['baseline_observed']=k.ultimate_offset(train,artifact['prior_level_calibration'])*train.q_paired.to_numpy(float)
    return {'closed_levels':k.level_math(train,artifact['prior_level_calibration']),'native_tree_offset':t.independent_math(z,artifact)}


def check_sources(plan):
    m.check_sources(plan);assert all(w.sha(Path(path))==value for path,value in plan['runtime_sources'].items())


def synthetic():
    rng=np.random.default_rng(2026102789);n=6000;i=np.arange(n);records=[]
    for line in q.LINES:
        a=np.exp(rng.normal(0,.3,n));b=np.exp(rng.normal(5,.3,n));exposure=rng.uniform(.3,1,n);report=rng.uniform(.4,1,n);excess=rng.choice([0.,10.,100.],n)
        base=(.5*400*a+.5*b)*exposure*report
        y=base*np.where(excess==100,2.,.5)*rng.gamma(2,.5,n)*(rng.random(n)<.5)*2
        f=pd.DataFrame({'row_id':['s'+str(j) for j in i],'line':line,'group_id':['g'+str(j) for j in i],'is_held':i%5==0,'fold':i%5,
            'year':2023+(i//5)%2,'new_business':(i//10)%2,'T0':y,'reserve':0.,'annual_A1S':a,'annual_T2b':b,'exposure_calendar':exposure,'q_paired':report})
        for j,name in enumerate(k.k.BASE_NUM[line]):f[name]=excess if j==0 else rng.choice([0.,10.,100.],n)
        for name in k.k.BASE_CAT[line]:
            if name!='new_business':f[name]=rng.choice(['a','b','c'],n)
        f['prior_claims_5y']=rng.choice([0.,1.,2.,np.nan],n)
        if line=='motor':f['ncb_years']=rng.choice([0.,1.,2.,3.,5.,6.,9.,10.,np.nan],n)
        folder=OUT/'synthetic'/line;primary=m.once(folder,'primary',lambda:fit(f,line,folder/'primary_raw.json'))
        adverse=m.once(folder,'adverse',lambda:fit(k.k.poison(f,line),line,folder/'adverse_raw.json'));assert primary==adverse
        assert primary['fitted_leaf_values']>primary['effective_trees'],'New whole integration must exercise nonconstant splits'
        checks=independent_math(f.loc[~f.is_held],primary);held=f.loc[f.is_held];value,relative=forward(held,primary)
        clean=held.drop(columns=['T0','reserve','q_paired']);other,rr=forward(clean,json.loads(json.dumps(adverse)))
        assert np.array_equal(value,other) and np.array_equal(relative,rr)
        indices=np.arange(0,len(held),7);subset,_=forward(clean.iloc[indices],primary);assert np.array_equal(subset,value[indices])
        order=np.arange(len(held))[::-1];shuffled,_=forward(clean.iloc[order],primary);assert np.array_equal(shuffled,value[order])
        records.append({'line':line,'whole_prior_and_native_tree_held_payload_poison_exact':True,'JSONreplay_and_subset_permutation_exact':True,
            'native_observed_offset_and_label_precision_checked':True,'no_price_feature':True,'splits_exercised':True,'fitted_leaf_values':primary['fitted_leaf_values'],'independent_math':checks})
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_tree_fits':3,'synthetic_adverse_tree_fits_separate':3,
        'synthetic_primary_closed_levels':18,'synthetic_adverse_closed_levels_separate':18,'new_real_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert phase['P88_execution']['state']=='TERMINAL_SUCCESS' and not phase.get('active_jobs') and not phase.get('active_execution')
    previous=BASE/'P88_validacion_prior_calibrado_20261027';assert w.read(previous/'completion_receipt.json')['report_sha256']==w.sha(previous/'report.json')
    parent=w.read(k.PLAN);m.check_sources(parent);runtime=w.read(t.PLAN)['runtime_sources'];assert all(w.sha(Path(path))==value for path,value in runtime.items())
    paths=[Path(__file__),Path(k.__file__),Path(t.__file__),k.PLAN,t.PLAN,previous/'report.json',previous/'completion_receipt.json',
        BASE/'P72_validacion_boosting_residual_20261027/report.json',R/'registro/semana2_prior_calibrado_GLM_validacion_plan.json']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'New standard tree-response integration on SAMEP88source-level prior/features; synthetic only and15real bindings, no real fitting.',
        'need':'P88simple level calibration plus same-bandGLMstill fails, delta-.00394708with negative interval, including adverse NBcells despite converged gradients. A fixed additive logresponse remains insufficient empirically; no established interaction cause. Test existing constrained standard tree estimator before changing its capacity or fields.',
        'distinct_from_previous':'P72used a P67OOFtarget-price/shape base and its baseline-risk feature. This has NONEof those rowprice/base ancestors: currentP88raw source signals, businessbands and owntrain scalar levels. P39was developed-source CatBoost, not this final estimator. Earlier failures retained, no first-boosting claim.',
        'one_change_vs_P88':'Final conditional GLMresponse is replaced by EXACTexisting P71fixed restricted native TweedieGBDT; P88raw fields/bandpreprocessing/source-level calibration/currentq unchanged.',
        'configuration':{'parameters':t.PARAMS,'num_boost_round':t.ROUNDS,'features':'EXACTP88train-only design with source logs, existing rating fields and history/NCBbusinessbands. No annualtargetprice/baselinefeature; adapter baseline columns are internal offsets ONLYand excluded from design.',
            'prior':parent['configuration'],'offset':'Native init_score=log(owntrain calibratedprior*calendar*ownq), boost_from_averageFalse. Stored modelrawscore is correction ONLY; ultimate=storedcalibratedprior*calendar*exp(raw), then qfor evaluation.',
            'complexity':'Same64rounds/depth3/7leaves/min_data1000/L2=10/maxleafstep.003/logcorrectionbound.192/deterministic2CPU/seed2026102771, no search/earlystopping or depth increase.',
            'conditional_fit':'The prior and final tree are both targetlearned on same train scope. No target row-risk/baseprediction stacking or joint optimum claim. Native label float32tested; evaluation originalfloat64uncappedT0.'},
        'preflight_criterion':'3primary/3adverse full staged nativefits with splits, ALLheld payload poison before prior/design, scalar prior/nativeoffset metric, leafwalk/bounds/serialization, whole JSONand subset/permutation,15strict bindings; no old P67producer/source/report replay.',
        'future_budget':{'primary_final_tree_fits':15,'adverse_final_tree_fits_separate':15,'primary_closed_levels':90,'adverse_closed_levels_separate':90,'new_source_fits':0,'new_shape_price_base_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'future_criterion':'Separate P90registration/commit; EVERYunchanged predictive/cohort/scenario/family16/level/influence guard. Fixed-round native objective/offset/leaf integrity replaces GLMstationarity only, same as P72. Pooledpass needs own2023-only conditionaltransfer before anyCSV.',
        'runtime_sources':runtime,'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits']+['A restricted piecewise response is a standard alternative, not demonstrated necessity/causality or known private improvement.','Small step/minleaf parameters do not certify credibility, optimality or freedom from overfitting.'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P89 registra antes de probar el estimador final estándar restringido P71 sobre EXACTOprior y campos P88. Cambia GLMpor64rondas/7hojas/depth3/paso.003, MISMAcapacidad/semilla que el árbol anterior, sin búsqueda o campos nuevos. P72 dependía de bases/preciosOOFP67 y su riesgo estimado; aquí no hay esos ancestros, solo fuentes fijas y niveles propios de train. No se afirma primera prueba de boosting o que interacciones causaron el falloP88.3+3árboles sintéticos con niveles, veneno completo, offset nativo/precisión/hojas/replay y15enlaces sin entrenar. Futuro15+15árboles/90+90niveles, todas las guardas predictivas y transferencia; integridad nativa sustituye estacionariedadGLM, no pisos de rendimiento. Cero fuentes/forma-base/CDF/2025/envíos. B00/adversos preservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P89registered_before_direct_prior_tree_preflight','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P89-ARBOL-PREVIO','P89: mismo prior y campos, árbol estándar con capacidad fija')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    assert not (OUT/'report.json').exists();check_sources(w.read(PLAN));assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    dump(OUT/'synthetic.json',synthetic());bindings=[]
    for line in q.LINES:
        for outer in range(5):
            f=k.k.frame_for(line,outer);assert f.row_id.is_unique and set(f.loc[f.is_held,'group_id']).isdisjoint(set(f.loc[~f.is_held,'group_id']))
            bindings.append({'line':line,'outer':outer,'rows':len(f),'same_P88raw_input_sha256':w.sha(k.r.p.t.t.OUT/f'input_{line}_{outer}.parquet')})
    check_sources(w.read(PLAN));dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P89calibrated_prior_tree_whole_synthetic_and_bindings_passed','bindings':bindings,
        'new_real_fits':0,'new_CDF_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'preflight':'passed','bindings':len(bindings),'new_real_fits':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');check_sources(w.read(PLAN))
    next_unit='P90: register/commit EXACTP89restricted native tree on SAMEP88raw features/owntrain scalar calibratedprior.15primary/15adverse treefits,90+90closedlevels, no source/shapepricebase/CDFfits, all unchanged predictive/cohort/scenario/family16/level/influence gates and native integrity. Ownconditionaltransfer required beforeCSV; no depth/round/step/field/line rescue.'
    text='# P89: árbol estándar sobre el prior calibrado\n\nCodex, '+utc()+'. P88 no resolvió las pérdidas del GLM pese a calibración simple y convergencia. Se prepara el mismo prior/campos con el boosting restringido ya registrado:64rondas, profundidad3,7hojas y paso máximo0,003, sin aumentar capacidad o buscar parámetros. No se demostró que interacciones causaran la pérdida.\n\n'
    text+='P72 usaba precios/bases OOF P67 y un campo de riesgo derivado de esa base. Esta receta usa las fuentes y bandas originales P88, más sus niveles generales y por negocio; ningún modelo de formas/precio por fila o feature de precio ajustado. Las columnas internas baseline son únicamente offsets para el motor nativo y no entran al diseño.\n\n'
    text+='Pasaron3árboles primarios/3adversos sintéticos y18+18niveles. Hubo splits reales, métrica nativa con offset contrastada por suma escalar, precisión float32de etiquetas declarada, límites/suma de hojas y serialización/proyección exactas. Alterar el payload retenido completo antes de nivelar/preprocesar no cambió modelos o niveles.15entradas reales enlazadas sin ajustar; cero nuevos modelos fuente/CDF/scoring/2025/envíos.\n\n'
    text+='La integridad del algoritmo finito sustituye solo la estacionariedad específica del GLM; las guardas predictivas y transferencia propia siguen intactas. Los pasos cortos no garantizan credibilidad o mejora privada. B00/F3c/adversos preservados,2024abierto adaptativo y límites de información/observación/valoración y selección adaptativa persistentes; sin revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        'new_real_fits':0,'new_CDF_fits':0,'new_scores':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P89-ARBOL-RESULTADO','P89: prior y árbol protegidos, preflight completo sin ajuste real')}
    archive=R/'privado'/('corte_P89_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P89'),(R/'registro/semana2_mision_privada_actual.json','P89')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    cp=R/'registro/semana2_contadores_propios_actual.json';w.update(cp,{'phase2_private_P89_prior_tree_preflight':{**receipt,'synthetic':w.read(OUT/'synthetic.json')}},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P89=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P89: árbol con prior calibrado, preflight\n\nCodex, '+receipt['utc']+'.Tres+3árboles sintéticos/18+18niveles,15enlaces; cero ajuste real/CDF/scoring/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_calibrated_prior_tree_preflight_index':w.rel(INDEX),'week_2_private_calibrated_prior_tree_preflight_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_real_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
