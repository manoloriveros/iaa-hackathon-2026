"""Evalúa forma GLM con respuesta acotada y nivel íntegro; ancestros P67 fijos."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p70_shape_level',R/'herramientas/preparar_GLM_forma_acotada_P69.py')
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
p=r.p;driver=p.driver;g=r.g;m=r.m;q=r.q;w=r.w;pd=r.pd;np=r.np;BASE=r.BASE
OUT=BASE/'P70_validacion_GLM_forma_acotada_20261027'
PLAN=R/'registro/semana2_GLM_forma_acotada_validacion_plan.json';INDEX=R/'registro/semana2_GLM_forma_acotada_validacion_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P70_VALIDACION_FORMA_ACOTADA.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)
def frame_for(line,outer):return p.frame_for(line,outer)


def check_sources(plan):m.check_sources(plan);p.verify_inputs()


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(r.PLAN);check_sources(parent);assert w.read(r.OUT/'completion_receipt.json')['report_sha256']==w.sha(r.OUT/'report.json')
    original=w.read(p.PLAN);paths=[Path(__file__),r.PLAN,r.OUT/'report.json',r.OUT/'synthetic.json',r.OUT/'completion_receipt.json',p.PLAN,p.OUT/'replay_report.json',p.OUT/'completion_receipt.json']
    sources=dict(parent['sources']);sources.update({w.rel(path):w.sha(path) for path in paths});OUT.mkdir()
    plan={'author':'Codex','utc':utc(),'candidate':'Current_reporting_crossfit_GLM_response_bounded_shape_uncapped_level',
        'need':parent['need'],'hypothesis':parent['hypothesis'],'configuration':parent['configuration'],'architecture':original['architecture'],
        **{key:original[key] for key in ['criteria','bootstrap','cohort_guard','level_sensitivity','scenarios']},
        'budget':parent['future_budget'],'ancestor_reuse':'Exact15P67numeric inputs and own already-completed protected inner reports/bases; verify actual per-outer nested artifact hashes, not just input-manifest bytes. Those ancestors do not depend on the new final GLMshape rule. No new ancestor fits, 2025applications or submissions.',
        'adverse':'Second actual quantile/shapeGLM/uncapped-level learning with all held labels/covariates/offsets corrupted before the actual train-only selectors. Shape raw estimator coefficients saved before controls; both stages serialized and replayed.',
        'math':'Raw capped-response shape objective/gradient checks preserved. Final scalar level independently satisfies the UNCAPPEDTweedie fixed-shape optimum. No claim of joint uncapped penalized GLMstationarity after changing the level.',
        'staged_decision':'Every original pooled/scenario/cohort/family16/level/influence gate plus raw-shape convergence and uncapped-level math. Any failure prevents admission; transfer=None. Pooled pass needs OWN2023-only conditional-transfer full pipeline with this same final two-stage learner, never copied pooled outer objects. No automatic upload.',
        'limits':parent['limits']+original['limits'],'sources':sources,'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P70congela antes de ajustar15GLMde forma/15cuantiles positivos p995/15niveles íntegros primarios y otros15+15+15adversos. Mismos campos/alpha1yentradasOOFP67, sin nuevas curvas/bases/fuentes. Solo la respuesta del ajuste de forma se acota; T0original íntegro en nivel, evaluación, escenarios y todas las guardas. El gradiente de forma se comprueba sobre su respuesta explícita y el nivel por sumas/derivada íntegra; no óptimo conjunto falso. Se revisan hashes de objetos internos reales. Pooledfallido impide admisión; si pasa requiere transferencia propia completa. No rescatar ramos/celdas/campos/umbrales, borrar siniestros o producir2025/envíos. B00preservado y2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P70registered_before_real_shape_level_learning','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P70-FORMA-PREVIO','P70: forma acotada y nivel íntegro, guardas completas antes de ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def forward(frame,artifact,ultimate=True):
    assert ultimate;value,relative=r.forward(frame,artifact)
    return value,{'kind':'P69_response_bounded_shape_uncapped_level_after_P65base','relative_prediction_digest':m.p.b.digest(relative.tolist())}


def final_dump(path,d):
    if path==OUT/'report.json':
        artifacts=[w.read(path) for path in OUT.glob('*_*/learning.json')];assert len(artifacts)==15
        d['status']='P70bounded_response_shape_uncapped_level_pooled_complete_transfer_unmeasured'
        d.update(primary_shape_quantiles=15,adverse_shape_quantiles_separate=15,primary_uncapped_levels=15,adverse_uncapped_levels_separate=15,
            new_closed_constants=15,raw_shape_convergence_only=True,uncapped_fixed_shape_level_math_passed=True,inherited_P65_base_components=30,
            inherited_P67_inner_reporting_scopes=25,inherited_P67_inner_base_learners=75,new_source_fits=0,new_base_fits=0,new_CDF_fits=0)
        d.pop('inherited_P55_base_components',None)
        d['shape_learning_response']='Bounded training response only, fixed positiveT0p995. Stored/evaluated originalT0never clipped.'
    return dump(path,d)


def setup():
    driver.OUT=OUT;driver.PLAN=PLAN;driver.INDEX=INDEX;driver.frame_for=frame_for;driver.dump=final_dump;driver.forward=forward;driver.independent_math=r.independent_math
    driver.v.SCENARIO=p.t.OUT/'scenario_inputs';m.apply_q=p.t.apply_row_q;g.fit=r.fit


def run():check_sources(w.read(PLAN));setup();driver.run();check_sources(w.read(PLAN))


def replay():
    check_sources(w.read(PLAN));setup()
    def reject(*args,**kwargs):raise AssertionError('P70replay blocks own shape/level learning')
    r.fit=reject;driver.replay();check_sources(w.read(PLAN))


def close():
    assert not (OUT/'completion_receipt.json').exists();check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    assert len(list(OUT.glob('*_*/primary_fit_invoked.json')))==len(list(OUT.glob('*_*/adverse_fit_invoked.json')))==15
    assert len(list(OUT.glob('*_*/primary_model_raw_shape_level.json')))==len(list(OUT.glob('*_*/adverse_model_raw_shape_level.json')))==15
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];paired=a['delta']-w.read(p.OUT/'report.json')['results']['POOLED']['NOMINAL']['delta']
    next_unit=('Register OWN2023-only conditional-transfer full current-reporting base/OOF/shapeGLM/uncapped-level algorithm before production or admission. No pooled2024target-trained ancestors there; same all gates and fixedp995recipe.' if passed else
        'Review NEWP70whole comparison and saved shape/uncapped-level artifacts against P67/P65before another candidate, no refit/resampling. Do not tune the cap, alpha, fields or selected line overrides after failure. Distinguish shape sensitivity from remaining source-risk/observation/crossfit-normalizer limits; document the next concrete standard mechanism, no public probe.')
    text='# P70: forma GLM acotada y nivel íntegro, evaluación\n\nCodex, '+utc()+'. '+('El combinado pasa; falta transferencia propia antes de admitir.' if passed else 'El combinado falla; no se admite CSV y transferencia queda sin evaluar.')+'\n\n'
    text+=f"ΔD²nominal={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f};{a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}. Diferencia puntual P70menosP67={paired:+.7f}, sin nuevo intervalo pareado.\n\n"
    text+='QuinceGLMde forma/15cuantiles positivosp995/15niveles íntegros primarios, con otros15+15+15adversos reales. Se conservaron todos los datos y etiquetas originales: solo la respuesta de AJUSTEde forma se acota. El nivel y la evaluación usan TODOel coste original. Campos/alpha1yancestrosP67idénticos, sin nuevas curvas/bases/fuentes. El gradiente se verifica sobre el objetivo de forma declarado; el nivel por otras sumas y derivada cero del objetivo íntegro con forma fija. No se afirma estacionariedad conjunta del GLMíntegro. Quince replays finales exactos, sin aprendizaje/remuestreo.\n\n'
    text+='Guardas: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+='Treinta llamadasGLMiterativas nuevas,15niveles cerrados primarios y30cuantiles primarios/adversos contados aparte. No precios2025o envíos. Las sensibilidades mantienen últimos nominales fijos; no ajuste completo por escenario. B00/F3cyalternativas conservados,2024abierto adaptativo. El nivel y los ancestros siguen sensibles al coste íntegro; transporte/maduración/cola/reservas/maestros/fuente2024condicional y búsqueda adaptativa limitan generalización. No mejora privada acreditada ni revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{key:a[key] for key in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P70_minus_P67_point_only':paired,'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,
        'primary_GLMshape_fits':15,'adverse_GLMshape_fits_separate':15,'primary_positive_shape_quantiles':15,'adverse_positive_shape_quantiles_separate':15,
        'new_primary_uncapped_closed_levels':15,'adverse_uncapped_closed_levels_separate':15,'new_source_fits':0,'new_base_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0,
        'next_unit':next_unit,'2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P70-FORMA-RESULTADO','P70: resultado completo de forma acotada y nivel íntegro')}
    archive=R/'privado'/('corte_P70_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    cp=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(cp);assert 'phase2_private_P70_bounded_response_GLM' not in counts
    w.update(cp,{'cumulative_price_base_fits':counts['cumulative_price_base_fits']+30,'cumulative_closed_form_constants':counts['cumulative_closed_form_constants']+15,'phase2_private_P70_bounded_response_GLM':receipt},archive);w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P70'),(R/'registro/semana2_mision_privada_actual.json','P70')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P70=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P70: forma acotada y nivel íntegro, evaluación\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+';15GLMprimarios/15adversos y niveles íntegros, replay exacto. Cero nuevos ancestros/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_bounded_shape_GLM_validation_index':w.rel(INDEX),'week_2_private_bounded_shape_GLM_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['prepare','run','replay','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
