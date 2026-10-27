"""Evalúa niveles por componente y GLM como un único algoritmo protegido."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);a=importlib.util.module_from_spec(s);s.loader.exec_module(a);return a
k=load('p88_calibrated_prior_kernel',R/'herramientas/preparar_GLM_prior_calibrado_P87.py')
h=load('p88_same_outer_evaluator',R/'herramientas/validar_GLM_fuente_directa_P75.py')
m=h.m;q=h.q;w=h.w;pd=h.pd;np=h.np;BASE=h.BASE
OUT=BASE/'P88_validacion_prior_calibrado_20261027'
PLAN=R/'registro/semana2_prior_calibrado_GLM_validacion_plan.json';INDEX=R/'registro/semana2_prior_calibrado_GLM_validacion_actual.json'
DOC=R/'docs/semana2/PRIVADA_P88_VALIDACION_PRIOR_CALIBRADO.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def forward(frame,artifact,ultimate=True):
    assert ultimate;value,relative=k.forward(frame,artifact)
    return value,{'kind':'GLMwith_own_training_source_level_prior','relative_prediction_digest':m.p.b.digest(relative.tolist())}


def final_dump(path,data):
    if path==OUT/'report.json':
        models=[w.read(p) for p in OUT.glob('*_*/learning.json')];assert len(models)==15
        assert all(a['prior_level_calibration']['fit_row_ids_digest']==a['fit_row_ids_digest'] and a['prior_level_calibration']['target_learned_parameters']==6 for a in models)
        for p in OUT.glob('*_*/learning.json'):
            assert w.read(p)['prior_level_calibration']==w.read(p.parent/'primary_model_raw_levels.json')
        data.update(status='P88staged_source_level_prior_GLM_pooled_complete_transfer_unmeasured',target_cost_trained_price_base_ancestors_used=True,
            target_learned_offset_levels=True,target_learned_shape_or_rowprice_feature_ancestors=False,
            primary_component_level_sets=30,adverse_component_level_sets_separate=30,new_primary_closed_levels=90,adverse_closed_levels_separate=90)
    return dump(path,data)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(k.PLAN);m.check_sources(parent);assert w.read(k.OUT/'completion_receipt.json')['report_sha256']==w.sha(k.OUT/'report.json')
    original_path=R/'registro/semana2_GLM_bandas_negocio_validacion_plan.json';original=w.read(original_path);m.check_sources(original)
    paths=[Path(__file__),Path(h.__file__),k.PLAN,k.OUT/'report.json',k.OUT/'synthetic.json',k.OUT/'completion_receipt.json',original_path,
        BASE/'P82_validacion_GLM_bandas_negocio_20261027/report.json',BASE/'P85_validacion_seleccion_GLM_20261027/report.json']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':'SameP82GLMwith_owntrain_percomponent_line_business_level_calibrated_halfprior',
        'need':parent['need'],'hypothesis':parent['hypothesis'],'one_change':parent['one_change'],'configuration':parent['configuration'],
        **{name:original[name] for name in ['criteria','bootstrap','cohort_guard','level_sensitivity','scenarios','adverse','validation']},
        'budget':parent['future_budget'],'staged_decision':parent['future_criterion'],
        'integration':'Same P75actual nativefit observer/outer evaluator; P87selects train BEFOREestimating source-level prior or band preprocessing. Six closed level parameters stored permodel before nativeGLM. Both stages are targetlearned; this is no longer a pure-source offset or zero target-cost ancestor algorithm.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P88 registra antes de ajustar el algoritmo completoP87: niveles propios por fuente/línea/negocio, mezcla fija50/50 y mismo GLM P82alpha1/campos/bandas.15GLMprimarios/15adversos,30+30componentes de nivel y90+90constantes cerradas, guardadas ANTESdeajustarGLM. Ambos pasos aprenden del train: no offset puramente fuente ni causalidad aislada de pesos. Veneno de todo payload retenido antes del selector/calibración/preproceso, matemática de niveles y gradiente condicional, replay bloqueando también sus estimadores de nivel. Mismosfolds/ambos años y TODASlas guardas globales/cohortes/escenarios/familia16/nivel/influencia/convergencia; si pasa falta transferencia propia2023antes deCSV. Sin copiarP65, refinaralpha/campos/ramo, fuente/forma-base/CDF/2025/envíos. B00/adversos preservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P88registered_before_real_level_and_GLMlearning','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P88-NIVELES-PREVIO','P88: calibración y GLM completos, guardas intactas antes de ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def setup():
    h.OUT=OUT;h.PLAN=PLAN;h.INDEX=INDEX;h.DOC=DOC;h.forward=forward;h.dump=final_dump
    h.r.frame_for=k.k.frame_for;h.r.poison=k.k.poison;h.r.fit=k.fit;h.r.forward=k.forward;h.r.independent_math=k.independent_math


def run():setup();h.run()


def replay():
    setup()
    def reject(*args,**kwargs):raise AssertionError('P88replay blocks ALLnew prior-level/report/GLMlearning')
    k.calibrate_levels=reject;k.SCALAR.factor=reject;k.SCALAR.cell_levels=reject;k.r.p.u.reporting=reject
    h.replay()
    dump(OUT/'level_replay_controls.json',{'author':'Codex','utc':utc(),'report_sha256':w.sha(OUT/'report.json'),'all_prior_level_estimators_blocked':True,
        'all15persisted_prior_GLMflows_passed':True,'new_levels':0,'new_native_fits':0})


def close():
    assert not (OUT/'completion_receipt.json').exists();m.check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.read(OUT/'level_replay_controls.json')['report_sha256']==w.sha(OUT/'report.json')
    assert len(list(OUT.glob('*_*/primary_fit_invoked.json')))==len(list(OUT.glob('*_*/adverse_fit_invoked.json')))==15
    assert len(list(OUT.glob('*_*/primary_model_raw_levels.json')))==len(list(OUT.glob('*_*/adverse_model_raw_levels.json')))==15
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];prior=w.read(BASE/'P82_validacion_GLM_bandas_negocio_20261027/report.json')['results']['POOLED']['NOMINAL']['delta']
    next_unit=('Register OWN2023-only conditionaltransfer of EXACTP88whole staged level-calibration/GLMwith own reporting, same fields/alpha1and criteria. No P64pooled2024targettrained curves; before anyCSVproduction/admission all transfer guards required.' if passed else
        'Review ONLYNEWP88saved calibration multipliers, residual coefficients and whole cells against P82/P65without refit/resampling. Do not tune K/alpha/weights or line/field overrides from held outcomes. Distinguish calibration/relative-penalty effects and risk allocation; next recipe needs a concrete standard mechanism, no public probe or missing authorization.')
    text='# P88: prior calibrado y GLM, evaluación completa\n\nCodex, '+utc()+'. '+('El combinado pasa; falta transferencia propia antes de admitir un CSV.' if passed else 'El combinado falla; no se admite CSV y la transferencia sigue sin evaluar.')+'\n\n'
    text+=f"ΔD²frente a referencia={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f};{a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}. P88menosP82={a['delta']-prior:+.7f}, diferencia puntual sin nuevo intervalo pareado.\n\n"
    text+='Se ajustaron15GLMprimarios/15adversos y90+90niveles de fuente/línea/negocio, guardados antes de cada ajuste nativo. Mezcla fija50/50después de niveles; mismos campos/bandas/alpha1delGLM. Los dos pasos aprenden del entrenamiento propio y se evaluaron juntos. Alterar todo el payload retenido antes del selector dejó iguales niveles y modelos. Momentos/credibilidad/gradiente por otro cálculo;15replays exactos con estimadores de nivel,GLMyreporte bloqueados. Intervalos y sumas guardadas cotejados sin nuevo remuestreo.\n\n'
    text+='Guardas: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+='El cambio de prior afecta también la normalización de verosimilitud frente a alpha1; no es una atribución causal exclusiva a pesos fuente ni un óptimo conjunto de todas las etapas. No nivelesP65copiados o mezclas/pesos elegidos; no nuevos árboles, formas de precio, CDF,2025oenvíos. Últimos nominales fijos en escenarios, sin ajuste completo por escenario. B00/F3cyalternativas preservados;2024desarrollo adaptativo, fuentes/snapshots/cola/reservas y búsqueda adaptativa limitan transporte, sin revisión independiente o mejora privada acreditada.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'; '+w.rel(OUT/'level_replay_controls.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{name:a[name] for name in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P88_minus_P82_point_only':a['delta']-prior,'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,
        'primary_GLM_fits':15,'adverse_GLM_fits_separate':15,'primary_component_level_sets':30,'adverse_component_level_sets_separate':30,'new_primary_closed_levels':90,'adverse_closed_levels_separate':90,
        'new_source_fits':0,'new_shape_price_base_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0,'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P88-NIVELES-RESULTADO','P88: resultado completo del prior calibrado y sus límites')}
    archive=R/'privado'/('corte_P88_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    cp=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(cp);assert 'phase2_private_P88_calibrated_prior_GLM' not in counts
    w.update(cp,{'cumulative_price_base_fits':counts['cumulative_price_base_fits']+30,'cumulative_closed_form_constants':counts['cumulative_closed_form_constants']+90,'phase2_private_P88_calibrated_prior_GLM':receipt},archive);w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P88'),(R/'registro/semana2_mision_privada_actual.json','P88')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P88=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    control=R/'registro/semana2_control_entregas_codex_actual.json';old=w.read(control)
    w.update(control,{'allow_new_submission':False,'reason':'P88pooledpass still requires own conditionaltransfer before exactCSVadmission.' if passed else 'P88staged source-level prior/GLMfails unchanged pooled/cohort guards. No copiedlevels, alpha/field/line rescue or missing human authorization; preserve alternatives/quota.',
        'last_evidence_review_utc':receipt['utc'],'latest_rejected_research_alternatives':old['latest_rejected_research_alternatives']+([] if passed else ['P88'])},archive)
    note='\n\n## Privada P88: prior calibrado y GLM, validación\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+';15GLMprimarios/15adversos,90+90niveles, replayexacto con todo aprendizaje bloqueado; cero fuentes/CDF/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_calibrated_prior_validation_index':w.rel(INDEX),'week_2_private_calibrated_prior_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['prepare','run','replay','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
