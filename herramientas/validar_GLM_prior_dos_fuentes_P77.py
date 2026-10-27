"""Mismo GLM directo; único cambio: prior aritmético monetario de dos fuentes."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
k=load('p77_two_source_kernel',R/'herramientas/preparar_GLM_prior_dos_fuentes_P76.py')
h=load('p77_same_direct_evaluator',R/'herramientas/validar_GLM_fuente_directa_P75.py')
w=h.w;m=h.m;q=h.q;np=h.np;pd=h.pd;BASE=h.BASE
OUT=BASE/'P77_validacion_GLM_prior_dos_fuentes_20261027'
PLAN=R/'registro/semana2_GLM_prior_dos_fuentes_validacion_plan.json';INDEX=R/'registro/semana2_GLM_prior_dos_fuentes_validacion_actual.json'
DOC=R/'docs/semana2/PRIVADA_P77_VALIDACION_PRIOR_DOS_FUENTES.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def forward(frame,artifact,ultimate=True):
    assert ultimate;value,relative=k.forward(frame,artifact)
    return value,{'kind':'Single_direct_GLM_fixed_half_monetary_source_prior','relative_prediction_digest':m.p.b.digest(relative.tolist())}


def final_dump(path,d):
    if path==OUT/'report.json':
        d['status']='P77single_GLM_fixed_two_source_prior_pooled_complete_transfer_unmeasured'
        d['source_offset_prior']='Fixed arithmetic half A1Ssource monetaryproxy/T2bsource annualproxy before single targetGLM; no targetcalibration before mixture.'
        artifacts=[w.read(p) for p in OUT.glob('*_*/learning.json')];assert len(artifacts)==15
        assert all(a['source_A1S_anchor']==k.anchors()[a['line']] for a in artifacts)
        d['source_anchor_in_every_model_artifact']=True
    return dump(path,d)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(k.PLAN);m.check_sources(parent);pre=w.read(k.OUT/'report.json')
    assert w.read(k.OUT/'completion_receipt.json')['report_sha256']==w.sha(k.OUT/'report.json')
    assert pre['source_anchors_sha256']==w.sha(ROOT/pre['source_anchors'])
    original=w.read(h.PLAN);m.check_sources(original)
    paths=[Path(__file__),Path(h.__file__),k.PLAN,k.OUT/'report.json',k.OUT/'synthetic.json',k.OUT/'source_anchors.json',k.OUT/'completion_receipt.json',h.PLAN]
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':'Same_direct_target_GLM_fixed_half_monetary_source_prior',
        'need':parent['need'],'hypothesis':parent['hypothesis'],'configuration':parent['configuration'],
        'fields_and_parameters_unchanged':{name:original['configuration'][name] for name in ['numeric_source_signals','numeric_other','categorical','GLMparameters','fields_reason','preprocessing']},'source_contract':original['source_contract'],
        **{name:original[name] for name in ['criteria','bootstrap','cohort_guard','level_sensitivity','scenarios']},
        'budget':parent['future_budget'],'single_change':'P75sourceT2b-only baseline is replaced by fixed arithmetic half monetary-sourceA1S/T2b. The actual design matrix/preprocessing/source signal columns/alpha1and data are unchanged; only baseline offset y/band sqrt(b)weights change as required by the same Tweedieobjective.',
        'adverse':original['adverse'],'validation':original['validation'],'staged_decision':parent['future_criterion'],
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P77registra15GLMprimarios/15adversos reales con el MISMOdiseño/campos/preproceso/alpha1deP75. Único cambio: offset fuente pasa de T2bsolo a mezcla monetaria aritmética50/50A1S/T2bcon anclas DESARROLLADASfijas P76, persistidas en cada modelo. No nueva calibración targetantes de mezcla, nuevas fuentes/CDF, pesos elegidos o búsqueda. Se reutiliza el evaluador P75y TODASsus guardas, matemática/veneno/replay; riesgoúltimo no leeq/coste retenido. Pooledfallido impideCSV, pasado exige transferencia propia2023completa. No identidadS2/F3c o último identificado. B00preservado,2024abierto adaptativo, cero2025/envíos. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P77registered_before_real_two_source_prior_GLM','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P77-PRIOR-PREVIO','P77: mismo GLM con prior fijo de dos fuentes, antes de ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def setup():
    h.OUT=OUT;h.PLAN=PLAN;h.INDEX=INDEX;h.DOC=DOC;h.forward=forward;h.dump=final_dump
    # P75's actual fit marker and unchanged evaluator now invoke the P76kernel.
    h.r.fit=k.fit;h.r.forward=k.forward;h.r.independent_math=k.independent_math


def run():setup();h.run()
def replay():setup();h.replay()


def close():
    assert not (OUT/'completion_receipt.json').exists();m.check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    assert len(list(OUT.glob('*_*/primary_fit_invoked.json')))==len(list(OUT.glob('*_*/adverse_fit_invoked.json')))==15
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];previous=w.read(BASE/'P75_validacion_GLM_fuente_directa_20261027/report.json')['results']['POOLED']['NOMINAL']['delta']
    next_unit=('Register OWN2023-only conditional-transfer reporting/singleGLMwith SAMEfixed monetarysourcehalfprior, fields/alpha1and all gates. Source anchors stay developed-only; no pooled2024targettrained qobjects. Before production/CSVadmission whole transfer must pass.' if passed else
        'Review NEWP77whole validation and source-prior comparison against P75/P65without refitting/resampling. No weight/alpha/field or line rescue. Current scalar source monetary conversion is verified but not a transport/gain proof; identify a concrete remaining source/target/reporting mechanism before any next recipe. Preserve all alternatives and quota, no public probe.')
    text='# P77: mismo GLM con prior de dos fuentes\n\nCodex, '+utc()+'. '+('El combinado pasa; falta transferencia propia antes de admitir.' if passed else 'El combinado falla; no se admite CSV y transferencia permanece sin evaluar.')+'\n\n'
    text+=f"ΔD²nominal={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f};{a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}. Diferencia puntual P77menosP75={a['delta']-previous:+.7f}, sin nuevo intervalo pareado.\n\n"
    text+='Misma matriz de señales/campos, preprocesamiento y alpha1delGLMdirectoP75. Solo cambia el prior de offset: mezcla aritmética fija50/50A1Smonetaria/T2b, ambas fuente desarrollada. Las anclas calculadas con b0ycentros fuente quedaron en cada artefacto; no son niveles estimados en target. QuinceGLMprimarios/15adversos reales con veneno antes del selector/preproceso, coeficientes guardados antes de controles, objetivo/gradiente por otras sumas y15replays finales exactos sin ajuste/remuestreo.\n\n'
    text+='Guardas: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+='No pesos/semillas/campos/alphaelegidos ni nuevos modelos fuente/CDF/bases,2025o envíos. La mezcla previa alGLMno es la referencia que calibra ambos componentes en destino antes de mezclarlos; fuente monetaria no identifica último. Escenarios con últimos nominales fijos, sin reentrenamiento completo por escenario. Fuente2024/snapshots/mercado/cola/reservas y búsqueda adaptativa2023/2024limitan la interpretación; no mejora privada acreditada o revisión independiente. B00/F3cyalternativas conservados,2024abierto.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{name:a[name] for name in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P77_minus_P75_point_only':a['delta']-previous,'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,
        'primary_GLM_fits':15,'adverse_GLM_fits_separate':15,'primary_iterative_parameter_counts':d['primary_iterative_parameter_counts'],'source_anchor_in_all_models':True,
        'new_target_base_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_closed_constants':0,'new2025inference':0,'new_submissions':0,'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P77-PRIOR-RESULTADO','P77: resultado completo del prior monetario de dos fuentes')}
    archive=R/'privado'/('corte_P77_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    cp=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(cp);assert 'phase2_private_P77_two_source_direct_GLM' not in counts
    w.update(cp,{'cumulative_price_base_fits':counts['cumulative_price_base_fits']+30,'phase2_private_P77_two_source_direct_GLM':receipt},archive);w.update(INDEX,receipt,archive)
    for path,name in [(R/'registro/semana2_mision017_fase2_actual.json','private_P77'),(R/'registro/semana2_mision_privada_actual.json','P77')]:w.update(path,{name:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P77=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P77: GLM con prior monetario de dos fuentes\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+';15GLMprimarios/15adversos, replayexacto; cero nuevos padres/CDF/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_two_source_prior_validation_index':w.rel(INDEX),'week_2_private_two_source_prior_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['prepare','run','replay','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
