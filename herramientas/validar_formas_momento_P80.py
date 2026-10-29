"""Valida solo el nuevo momento de bandas dentro del modelo completo P65."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import importlib.util
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p80_shape_moment_preflight',R/'herramientas/preparar_formas_momento_P79.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
p=a.p;v=p.v;k=a.k;m=a.m;q=a.q;w=a.w;pd=a.pd;np=a.np;BASE=a.BASE
CONTROL=p.OUT
OUT=BASE/'P80_validacion_formas_momento_20261027'
PLAN=R/'registro/semana2_formas_momento_validacion_plan.json';INDEX=R/'registro/semana2_formas_momento_validacion_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P80_VALIDACION_FORMAS_MOMENTO.md'
ORIGINAL_LEVEL_MATH=v.component_level_math


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def component_math(train,artifact):
    levels=ORIGINAL_LEVEL_MATH(train,artifact);checks=[]
    for name,obj in artifact['components'].items():
        z=k.component_frame(train,'annual_'+name);mu=np.exp(z.log_relative_A1S.to_numpy())*z.e_cost_scope.to_numpy()
        for shape in obj['shape']:
            assert shape['estimator']=='relative_withinbusiness_Tweedie15scale_moment'
            value=k.core.b.shape_apply(z,mu,shape)
            checks.append({'component':name,'variable':shape['which'],**a.independent_shape(z,mu,shape['which'],shape,value)});mu=value
    return {'existing_component_levels':levels,'new_shape_scalar_checks':checks}


def report_dump(path,data):
    if path==OUT/'report.json':data.update(status='P80shape_moment_only_pooled_complete_transfer_unmeasured',new_GLM_fits=0,new_CDF_fits=0,
        one_change='P65NCBprior_withinbusiness_raw_AE_to_Tweedie15moment_only',all_actual_shape_moments_independently_checked=True)
    return dump(path,data)


def setup():
    a.setup();v.OUT=OUT;v.PLAN=PLAN;v.INDEX=INDEX;v.SCENARIO=CONTROL/'scenario_inputs'
    m.OUT=OUT;m.e.OUT=OUT;m.apply_q=p.apply_row_q;v.dump=report_dump;v.component_level_math=component_math


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(a.PLAN);m.check_sources(parent);assert w.read(a.OUT/'completion_receipt.json')['report_sha256']==w.sha(a.OUT/'report.json')
    assert w.read(a.OUT/'report.json')['status']=='P79shape_moment_whole_synthetic_and_bindings_passed'
    original=w.read(p.PLAN);m.check_sources(original)
    paths=[Path(__file__),Path(a.__file__),Path(p.__file__),Path(v.__file__),a.PLAN,a.OUT/'report.json',a.OUT/'synthetic.json',a.OUT/'completion_receipt.json',
        CONTROL/'report.json',CONTROL/'replay_report.json',CONTROL/'completion_receipt.json',p.PLAN]
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':'P65fixedhalf_same_bands_K300linearcred_only_raw_Tweedie15shape_moments',
        'need':parent['need'],'hypothesis':parent['hypothesis'],'one_change':parent['one_change'],'unchanged':parent['unchanged'],
        'configuration':'Exact P79kernel on exact P64saved inputs; same singlecompletelearner perline/outer and frozen two-source geometricseeds/fixedhalf, no newratingfields/weights/bands/alpha/caps/source/curves.',
        **{key:original[key] for key in ['criteria','bootstrap','cohort_guard','level_sensitivity']},
        'scenario':'Reuse exact P65scenario_inputs files and numeric P65line/peril qadapter. Final nominalultimateprices remain fixed in reserve/tail branches, no full scenario price refitting.',
        'integration':'P55complete validation driver, P79only shape_fit hook and unchanged original learner; independent scalar checks now cover ALLactual new shape moments/credibility/normalizers before existing level checks. Exact whole replay blocks all learning. No inference by metadata alone.',
        'budget':{'primary_closed_whole_learners':15,'adverse_closed_whole_learners_separate':15,'primary_components':30,'adverse_components_separate':30,
            'primary_shared_residual_stages':20,'adverse_shared_residual_stages_separate':20,'new_GLM_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'staged_decision':'Every unchanged P65pooled/global/interval/fold/year/Post31/scenario/cell/level/influence/NB/broker/historyzero/family16guard. Any failure prevents admission; transfer=None. Pooledpass requires OWN2023-only conditionaltransfer under its own report/price training before production or exactfileadmission. No automatic CSVor upload.',
        'limits':parent['limits'],'sources':{**original['sources'],**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P80registra antes de ajustar el único cambioP79frente aP65: momentoTweedie1,5crudo por banda/negocio en lugar de razónA/E. Conserva bandas, credibilidadLINEALK300, normalizadores, K400, mezcla fija50/50yresiduales ya métricos, qP64yfuentes congeladas.15aprendices completos primarios/15adversos (30+30componentes,20+20etapas), sin fuente/GLM/CDF/2025/envíos. Guardas globales, intervalos, folds, años, Post31, celdas, cohortes, familia16, nivel e influencia idénticas. Sumas escalares de todas las formas reales y replay sin aprendizaje. Si falla no se admite; si pasa falta transferencia propia2023antes deCSV. No rescate de pesos/bandas/credibilidad por resultados. B00/F3cyalternativas conservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P80registered_before_real_closed_shape_learning','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P80-MOMENTO-PREVIO','P80: momento de bandas, evaluación completa con guardas intactas')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():setup();v.run()


def replay():
    setup()
    def reject(*args,**kwargs):raise AssertionError('P80replay blocks new line/peril reporting')
    p.t.line_curves=reject;v.replay()


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');m.check_sources(w.read(PLAN))
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    nominal=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];number=sum(d['primary_constants'].values())
    prior=w.read(CONTROL/'report.json')['results']['POOLED']['NOMINAL']['delta'];paired=nominal['delta']-prior
    next_unit=('Prepare/register OWN2023-only conditionaltransfer for exact P80complete algorithm; own report/C0price scopes, frozen sources, same gates. No CSVor upload from pooled alone.' if passed else
        'Review NEWP80saved shape factors/whole cells and difference from P65without refit/resampling. No new bands/K/weights or perline rescue from held outcomes. Identify a distinct documented source/target/reporting mechanism before another standard recipe. Preserve alternatives/quota; no public probe or missing human authorization.')
    text='# P80: momento de bandas, validación completa\n\nCodex, '+utc()+'. '+('El combinado pasa; falta transferencia propia antes de admitir un CSV.' if passed else 'El combinado falla; no se admite CSV y la transferencia permanece sin evaluar.')+'\n\n'
    text+=f"ΔD²frente a referencia={nominal['delta']:+.7f}; IC95por grupos=[{nominal['bootstrap95'][0]:+.7f};{nominal['bootstrap95'][1]:+.7f}]; Post31={nominal['post31_delta']:+.7f}; peor celda={nominal['worst_cell_delta']:+.7f}. P80menosP65={paired:+.7f}, diferencia puntual sin nuevo intervalo pareado.\n\n"
    text+='Solo cambió el momento crudo de las bandasNCB/historia, conservando credibilidad linealK300, bandas/negocio/normalizadores, K400, fuentes y qP64, mezcla fija50/50yresiduales métricos. Quince aprendices cerrados primarios/15adversos,30+30componentes y20+20etapas residuales. Todas las formas nuevas reales coincidieron con sumas escalares independientes;15replays reprodujeron precios y normalizadores con aprendizaje bloqueado. Intervalos/multiplicidades guardados y sumas independientes fueron cotejados sin remuestreo adicional.\n\n'
    text+='Guardas: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+=f'{number}constantes primarias nuevas; cero GLM/árboles fuente/CDF/2025/envíos. Precios últimos nominales fijos en escenarios, sin reentrenamiento por escenario. No implica error deA/Eo superioridad privada. B00/F3cyalternativas preservados,2024desarrollo adaptativo, fuente2024condicional/transportedeproxy/cola/reservas/maestros sin fecha y selección adaptativa limitan la interpretación; sin revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),
        'decision':d['decision'],'nominal':{key:nominal[key] for key in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P80_minus_P65_point_only':paired,
        'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,'new_primary_constants':number,**w.read(PLAN)['budget'],
        'next_unit':next_unit,'2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P80-MOMENTO-RESULTADO','P80: resultado completo de momentos de bandas, adversos y límites')}
    archive=R/'privado'/('corte_P80_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    cp=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(cp);assert 'phase2_private_P80_shape_moment' not in counts
    w.update(cp,{'cumulative_closed_form_constants':counts['cumulative_closed_form_constants']+number,'phase2_private_P80_shape_moment':receipt},archive);w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P80'),(R/'registro/semana2_mision_privada_actual.json','P80')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P80=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    control=R/'registro/semana2_control_entregas_codex_actual.json';old=w.read(control)
    reason=('P80pooledpass but own conditionaltransfer remains unmeasured; no exactCSVadmission.' if passed else 'P80only shape-moment change fails unchanged pooled/cohort admission guards. Preserve baseline/alternatives/quota; no hidden-private proof or missing human authorization.')
    w.update(control,{'allow_new_submission':False,'reason':reason,'last_evidence_review_utc':receipt['utc'],'latest_rejected_research_alternatives':old['latest_rejected_research_alternatives']+([] if passed else ['P80'])},archive)
    note='\n\n## Privada P80: validación del momento de bandas\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+f';15aprendices primarios/15adversos,{number}constantes primarias, replay exacto. Cero GLM/fuente/CDF/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_shape_moment_validation_index':w.rel(INDEX),'week_2_private_shape_moment_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['prepare','run','replay','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
