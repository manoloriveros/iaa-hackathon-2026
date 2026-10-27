"""Evalúa el árbol restringido sobre los mismos campos/prior calibrado P88."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);a=importlib.util.module_from_spec(s);s.loader.exec_module(a);return a
k=load('p90_direct_prior_tree_kernel',R/'herramientas/preparar_boosting_prior_calibrado_P89.py')
h=load('p90_existing_tree_evaluator',R/'herramientas/validar_boosting_residual_P72.py')
rating=k.k.k
m=h.m;q=h.q;w=h.w;pd=h.pd;np=h.np;BASE=h.BASE
OUT=BASE/'P90_validacion_boosting_prior_20261027'
PLAN=R/'registro/semana2_boosting_prior_validacion_plan.json';INDEX=R/'registro/semana2_boosting_prior_validacion_actual.json'
DOC=R/'docs/semana2/PRIVADA_P90_VALIDACION_BOOSTING_PRIOR.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def forward(frame,artifact,ultimate=True):
    assert ultimate;value,relative=k.forward(frame,artifact)
    return value,{'kind':'Restricted_native_tree_with_scalar_source_prior','relative_prediction_digest':m.p.b.digest(relative.tolist())}


def final_dump(path,data):
    if path==OUT/'report.json':
        models=[w.read(p) for p in OUT.glob('*_*/learning.json')];assert len(models)==15
        for p in OUT.glob('*_*/learning.json'):
            a=w.read(p);assert a['prior_level_calibration']==w.read(p.parent/'primary_native_model_raw_levels.json')
            assert a['prior_level_calibration']['fit_row_ids_digest']==a['fit_row_ids_digest']
            assert not any('baseline' in name for name in a['preprocess']['columns'])
        data.update(status='P90restricted_tree_calibrated_source_prior_pooled_complete_transfer_unmeasured',
            inherited_P67_inner_reporting_scopes=0,inherited_P67_inner_base_learners=0,
            actual_report_ancestry='Current P64own_outer_lineperil_CDFs; no inner targetprice/report objects used by this recipe',
            target_learned_offset_levels=True,target_learned_shape_or_rowprice_feature_ancestors=False,
            primary_closed_levels=90,adverse_closed_levels_separate=90,new_closed_constants=90)
    return dump(path,data)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(k.PLAN);k.check_sources(parent);assert w.read(k.OUT/'completion_receipt.json')['report_sha256']==w.sha(k.OUT/'report.json')
    original_path=R/'registro/semana2_prior_calibrado_GLM_validacion_plan.json';original=w.read(original_path);m.check_sources(original)
    paths=[Path(__file__),Path(h.__file__),k.PLAN,k.OUT/'report.json',k.OUT/'synthetic.json',k.OUT/'completion_receipt.json',original_path,
        BASE/'P88_validacion_prior_calibrado_20261027/report.json',BASE/'P72_validacion_boosting_residual_20261027/report.json']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':'P88same_calibrated_source_prior_fields_with_P71restricted_native_tree_response',
        'need':parent['need'],'hypothesis':'A fixed restricted piecewise response on a source-level prior may generalize differently from P88additiveGLMwithout inheriting P72noisy target-price bases. No known gain or causal interaction proof.',
        'one_change':parent['one_change_vs_P88'],'configuration':parent['configuration'],'budget':parent['future_budget'],
        **{name:original[name] for name in ['criteria','bootstrap','cohort_guard','level_sensitivity','scenarios']},
        'adverse':'Actual second native tree/level pipeline, allheld original target/source/rating/calendar/qpayload corrupted before levelselector/preprocessing; exact final artifacts. Native model and closedlevels checkpointed before integrity checks.',
        'integration':'Reuse outer metric/scenario driver only. Strict P88raw frames; own scalar levels, native P71treeengine with P88design hook, no legacy rowprice feature or P67innerbase dependency. Native integrity replaces only GLMstationarity, every predictive guard unchanged.',
        'staged_decision':parent['future_criterion'],'runtime_sources':parent['runtime_sources'],
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P90 registra antes de ajustar15árboles primarios/15adversos y90+90niveles, mismos campos/priorP88 y capacidadP71fija64rondas/depth3/7hojas/paso.003, sin búsqueda. Diferencia frenteP88: estimador final; frenteP72: no bases/preciosOOFP67 ni riesgo derivado de precio, con campos/prioractuales. Marcos de evaluación no implican dependencia numérica de esos padres antiguos. Nativefit marcado/modelo y niveles guardados antes de controles, offset/hojas/precisión/replay real. Todas las guardas globales/cohortes/escenarios/nivel/influencia/familia16, integridad nativa en vez de estacionariedadGLM. Si pasa falta transferencia propia2023antes deCSV; si falla no aumentar profundidad/rondas o elegirramo. Sin fuente/forma-base/CDF/2025/envíos; B00/adversos preservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P90registered_before_real_calibrated_prior_tree_learning','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P90-ARBOL-PREVIO','P90: árbol y prior calibrado completos, guardas antes de ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def setup():
    h.OUT=OUT;h.PLAN=PLAN;h.INDEX=INDEX;h.DOC=DOC;h.forward=forward;h.dump=final_dump;h.frame_for=rating.frame_for
    h.g.poison=rating.poison;h.r.fit=k.fit;h.r.forward=k.forward;h.r.independent_math=k.independent_math;h.r.check_sources=k.check_sources


def run():setup();h.run()


def replay():
    setup()
    def reject(*args,**kwargs):raise AssertionError('P90replay blocks ALLnew levels/native trees/reporting')
    k.k.calibrate_levels=reject;k.k.SCALAR.factor=reject;k.k.SCALAR.cell_levels=reject;k.k.r.p.u.reporting=reject
    def replay_frame(line,outer):
        f=rating.frame_for(line,outer);f['baseline_observed']=np.nan;return f
    # The old replay's poisoned-offset column is an unused local NaNplaceholder;
    # the new numeric model computes its ultimate only from stored levels/sources.
    h.frame_for=replay_frame;h.replay()
    dump(OUT/'level_replay_controls.json',{'author':'Codex','utc':utc(),'report_sha256':w.sha(OUT/'report.json'),'all_prior_level_estimators_blocked':True,
        'legacy_observed_offset_placeholder_is_NaN_and_not_a_feature':True,'all15persisted_level_native_tree_flows_passed':True,'new_levels':0,'new_native_fits':0})


def close():
    assert not (OUT/'completion_receipt.json').exists();k.check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.read(OUT/'level_replay_controls.json')['report_sha256']==w.sha(OUT/'report.json')
    assert len(list(OUT.glob('*_*/primary_fit_invoked.json')))==len(list(OUT.glob('*_*/adverse_fit_invoked.json')))==15
    assert len(list(OUT.glob('*_*/primary_native_model_raw_levels.json')))==len(list(OUT.glob('*_*/adverse_native_model_raw_levels.json')))==15
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];prior=w.read(BASE/'P88_validacion_prior_calibrado_20261027/report.json')['results']['POOLED']['NOMINAL']['delta']
    next_unit=('Register OWN2023-only conditionaltransfer of EXACTP90source-level/native-tree pipeline with own reporting and unchanged guards before CSV. No borrowed pooled2024targetcurves or stageobjects.' if passed else
        'Review ONLYNEWP90saved whole cells/tree corrections and prior levels against P88/P65without refit/resampling. No tree depth/round/leaf/step/field or perline rescue. Separate failure of this specific constrained response from an interaction cause or a general capacity claim; new recipe needs distinct evidence before fitting.')
    text='# P90: árbol restringido con prior calibrado, evaluación\n\nCodex, '+utc()+'. '+('El combinado pasa; falta transferencia propia antes de admitir un CSV.' if passed else 'El combinado falla; no se admite CSV y la transferencia sigue sin evaluar.')+'\n\n'
    text+=f"ΔD²frente a referencia={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f};{a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}. P90menosP88={a['delta']-prior:+.7f}, punto sin nuevo intervalo pareado.\n\n"
    text+='Quinceárboles primarios/15adversos reales,90+90niveles propios, receta fija64rondas/depth3/7hojas/paso0,003. Mismos campos/bandas/prior deP88, sin fuente/precio-baseOOF o featuredeprecio; el estimador final reemplaza alGLM. La capacidad es la deP71ya usada; no se amplió después de resultados. Toda calibración/modelos coincidió bajo veneno retenido antes de selector/preproceso. Métrica nativa con offset, hojas/límites/precisión por otro cálculo y15replays exactos con nivel/árbol/reporte bloqueados. Intervalos/sumas guardados cotejados sin remuestreo adicional.\n\n'
    text+='Guardas: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+='Las hojas son parámetros iterativos y se registran aparte de90constantes primarias nuevas. Ningún nuevo modelo fuente, forma-base, curva, precio2025oenvío. Escenarios con últimos nominales fijos, sin reestimación completa por escenario. Minleaf/pasos cortos no certifican credibilidad ni rendimiento privado. Fuente/maestros/observación/cola/reservas y búsqueda adaptativa limitan transporte. B00/F3cyalternativas preservados,2024abierto adaptativo, sin revisión independiente o causa de interacciones acreditada.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'; '+w.rel(OUT/'level_replay_controls.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{name:a[name] for name in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P90_minus_P88_point_only':a['delta']-prior,'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,
        'primary_native_tree_fits':15,'adverse_native_tree_fits_separate':15,'new_primary_closed_levels':90,'adverse_closed_levels_separate':90,'primary_iterative_tree_leaf_counts':d['primary_iterative_tree_leaf_counts'],
        'new_source_fits':0,'new_shape_price_base_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0,'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P90-ARBOL-RESULTADO','P90: resultado completo del árbol con prior calibrado')}
    archive=R/'privado'/('corte_P90_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    cp=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(cp);assert 'phase2_private_P90_prior_tree' not in counts
    w.update(cp,{'cumulative_price_base_fits':counts['cumulative_price_base_fits']+30,'cumulative_closed_form_constants':counts['cumulative_closed_form_constants']+90,'phase2_private_P90_prior_tree':receipt},archive);w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P90'),(R/'registro/semana2_mision_privada_actual.json','P90')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P90=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    control=R/'registro/semana2_control_entregas_codex_actual.json';old=w.read(control)
    w.update(control,{'allow_new_submission':False,'reason':'P90pooledpass still requires own conditionaltransfer before exactCSVadmission.' if passed else 'P90fixed restricted native response on calibrated prior fails unchanged pooled/cohort guards; preserve quota/alternatives, no missing human authorization or parameter rescue.',
        'last_evidence_review_utc':receipt['utc'],'latest_rejected_research_alternatives':old['latest_rejected_research_alternatives']+([] if passed else ['P90'])},archive)
    note='\n\n## Privada P90: árbol y prior calibrado, validación\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+';15árboles primarios/15adversos,90+90niveles, replayexacto; cero fuente/CDF/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_calibrated_prior_tree_validation_index':w.rel(INDEX),'week_2_private_calibrated_prior_tree_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['prepare','run','replay','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
