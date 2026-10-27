"""Evalúa el cambio único a bandas por negocio en el GLM directo P77."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(s);s.loader.exec_module(module);return module
k=load('p82_band_GLMkernel',R/'herramientas/preparar_GLM_bandas_negocio_P81.py')
h=load('p82_existing_direct_evaluator',R/'herramientas/validar_GLM_fuente_directa_P75.py')
w=h.w;m=h.m;q=h.q;np=h.np;pd=h.pd;BASE=h.BASE
OUT=BASE/'P82_validacion_GLM_bandas_negocio_20261027'
PLAN=R/'registro/semana2_GLM_bandas_negocio_validacion_plan.json';INDEX=R/'registro/semana2_GLM_bandas_negocio_validacion_actual.json'
DOC=R/'docs/semana2/PRIVADA_P82_VALIDACION_GLM_BANDAS_NEGOCIO.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def forward(frame,artifact,ultimate=True):
    assert ultimate;value,relative=k.forward(frame,artifact)
    return value,{'kind':'Single_direct_GLM_fixed_half_source_prior_history_NCBbusinessbands','relative_prediction_digest':m.p.b.digest(relative.tolist())}


def final_dump(path,data):
    if path==OUT/'report.json':
        data['status']='P82single_GLM_history_NCBbusinessbands_pooled_complete_transfer_unmeasured'
        models=[w.read(p) for p in OUT.glob('*_*/learning.json')];assert len(models)==15
        assert all(a['source_A1S_anchor']==k.b.anchors()[a['line']] for a in models)
        assert all(a['rating_form']=='P65existing_history_NCBbands_by_business_as_direct_GLMcategorical_effects' for a in models)
        data['same_source_anchors_all_models']=True;data['business_band_representation_all_models']=True
    return dump(path,data)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(k.PLAN);m.check_sources(parent);assert w.read(k.OUT/'completion_receipt.json')['report_sha256']==w.sha(k.OUT/'report.json')
    original_path=R/'registro/semana2_GLM_prior_dos_fuentes_validacion_plan.json';original=w.read(original_path);m.check_sources(original)
    control=BASE/'P77_validacion_GLM_prior_dos_fuentes_20261027'
    paths=[Path(__file__),Path(h.__file__),k.PLAN,k.OUT/'report.json',k.OUT/'synthetic.json',k.OUT/'completion_receipt.json',original_path,control/'report.json',control/'completion_receipt.json']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':'Same_P77single_direct_GLM_only_history_NCBbusinessband_representation',
        'need':parent['need'],'hypothesis':parent['hypothesis'],'one_change':parent['one_change'],'configuration':parent['configuration'],
        **{name:original[name] for name in ['criteria','bootstrap','cohort_guard','level_sensitivity','scenarios','adverse','validation']},
        'budget':parent['future_budget'],'staged_decision':parent['future_criterion'],
        'integration':'P75actual estimator fit marker/preprocessing evaluator, P81band design applied AFTERtrainselector, same P76prior with persisted source anchors, objective/gradient and actual adverse full payload checks, replay without any learning.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P82registra antes de ajustar15GLMprimarios/15adversos reales, misma fuente/prior50/50/alpha1deP77, cambiando solo historia/NCBde pendientes comunes a bandas por negocio ya usadas enP65. Sin nuevos campos, pesos, fuente/base/CDF,2025/envíos. Mismos5folds/ambos años, todas las guardas globales/IC/cohortes/familia16/escenarios/nivel/influencia y convergencia. Veneno completo antes de selector y creación de bandas, coeficientes crudos antes de controles, matemática y replay sin ajustar. Fallo combinado impideCSV; aprobado requiere transferencia propia2023. Ningún rescate posterior por campo/banda/alpha/ramo. B00yadversos preservados,2024abierto adaptativo, no ganancia privada asumida. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P82registered_before_real_band_GLMlearning','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P82-BANDAS-PREVIO','P82: GLM por bandas de negocio, evaluación completa antes de ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def setup():
    h.OUT=OUT;h.PLAN=PLAN;h.INDEX=INDEX;h.DOC=DOC;h.forward=forward;h.dump=final_dump
    h.r.frame_for=k.frame_for;h.r.poison=k.poison;h.r.fit=k.fit;h.r.forward=k.forward;h.r.independent_math=k.independent_math


def run():setup();h.run()
def replay():setup();h.replay()


def close():
    assert not (OUT/'completion_receipt.json').exists();m.check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    assert len(list(OUT.glob('*_*/primary_fit_invoked.json')))==len(list(OUT.glob('*_*/adverse_fit_invoked.json')))==15
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];prior=w.read(BASE/'P77_validacion_GLM_prior_dos_fuentes_20261027/report.json')['results']['POOLED']['NOMINAL']['delta']
    next_unit=('Register OWN2023-only conditionaltransfer for EXACTP82bandGLMwith own reporting and fixed source prior before production/admission. All criteria unchanged, no pooled2024targettrained qthere.' if passed else
        'Review NEWP82saved fitted band contrasts and whole held-cell losses against P77/P65without refit/resampling. Retain known source/report/valuation limits; do not tune bands/alpha/fields/weights or select line overrides. A new candidate needs a distinct documented mechanism and preregistration, no public probe or missing human authorization.')
    text='# P82: GLM con bandas por negocio, evaluación\n\nCodex, '+utc()+'. '+('El combinado pasa; falta transferencia propia antes de un CSV.' if passed else 'El combinado falla; no se admite CSV y transferencia queda sin evaluar.')+'\n\n'
    text+=f"ΔD²frente a referencia={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f};{a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}. P82menosP77={a['delta']-prior:+.7f}, punto sin nuevo intervalo pareado.\n\n"
    text+='Se cambió solo la representación de historia/NCBdel GLMdirecto: bandas del modelo estructurado separadas por negocio, en lugar de pendientes ordinales comunes. Mismo prior fuente50/50, alpha1, fuentes, entradas y resto de efectos. QuinceGLMprimarios/15adversos, veneno de todo payload retenido antes del selector/bandas/preproceso y coeficientes guardados antes de controles. Objetivo/gradiente por otra suma; quince replays exactos sin aprendizaje ni remuestreo.\n\n'
    text+='Guardas: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+='Cero nuevas bases/fuentes/CDF/2025/envíos. Precios últimos nominales fijos para escenarios, sin ajuste de toda la receta por escenario. No prueba causal de la pérdida anterior o de mejora privada; persistente fuente2024condicional, proxydeobservación, cola/reservas/snapshots/selección adaptativa. B00/F3cyalternativas conservados,2024abierto adaptativo; sin revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{name:a[name] for name in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P82_minus_P77_point_only':a['delta']-prior,'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,
        'primary_GLM_fits':15,'adverse_GLM_fits_separate':15,'primary_iterative_parameter_counts':d['primary_iterative_parameter_counts'],
        'new_target_base_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_closed_constants':0,'new2025inference':0,'new_submissions':0,'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P82-BANDAS-RESULTADO','P82: resultado completo del GLM por bandas y límites')}
    archive=R/'privado'/('corte_P82_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    cp=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(cp);assert 'phase2_private_P82_business_band_GLM' not in counts
    w.update(cp,{'cumulative_price_base_fits':counts['cumulative_price_base_fits']+30,'phase2_private_P82_business_band_GLM':receipt},archive);w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P82'),(R/'registro/semana2_mision_privada_actual.json','P82')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P82=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    control=R/'registro/semana2_control_entregas_codex_actual.json';old=w.read(control)
    reason=('P82pooledpass but own conditionaltransfer remains unmeasured; no exactCSVadmission.' if passed else 'P82band representation under the same fixed source prior/alpha1fails pooled/cohort admission guards. Preserve all alternatives and quota; no missing human authorization or private gain proof.')
    w.update(control,{'allow_new_submission':False,'reason':reason,'last_evidence_review_utc':receipt['utc'],'latest_rejected_research_alternatives':old['latest_rejected_research_alternatives']+([] if passed else ['P82'])},archive)
    note='\n\n## Privada P82: GLM con bandas por negocio, validación\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+';15GLMprimarios/15adversos, replay exacto; cero bases/fuente/CDF/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_business_band_GLM_validation_index':w.rel(INDEX),'week_2_private_business_band_GLM_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['prepare','run','replay','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
