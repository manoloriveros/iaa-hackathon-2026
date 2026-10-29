"""Evaluación completa del prior calibrado sin GLM ni nuevos ajustes."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);a=importlib.util.module_from_spec(s);s.loader.exec_module(a);return a


k=load('p98_simple_prior',R/'herramientas/preparar_prior_solo_P97.py')
h=load('p98_same_outer_evaluator',R/'herramientas/validar_GLM_fuente_directa_P75.py')
m=h.m;q=h.q;w=h.w;np=h.np;pd=h.pd;BASE=h.BASE
OUT=BASE/'P98_validacion_prior_solo_20261027'
PLAN=R/'registro/semana2_prior_solo_validacion_plan.json';INDEX=R/'registro/semana2_prior_solo_validacion_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P98_VALIDACION_PRIOR_SOLO.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def learn(frame,line):
    outer=int(frame.loc[frame.is_held,'fold'].unique().item());adverse=bool(frame.loc[frame.is_held,'T0'].lt(0).any())
    artifact=k.cached(k.p.k.poison(frame,line) if adverse else frame,line,outer)
    folder=OUT/f'{line}_{outer}';name='adverse' if adverse else 'primary'
    dump(folder/(name+'_reused_prior.json'),{'author':'Codex','utc':utc(),'source':w.rel(k.OLD/f'{line}_{outer}/learning.json'),
        'sha256':w.sha(k.OLD/f'{line}_{outer}/learning.json'),'own_scope_key_code_data_matched':True,'reused_levels':6,'new_levels':0})
    return artifact


def forward(frame,artifact,ultimate=True):
    assert ultimate
    return k.forward(frame,artifact),{'kind':'Same_scope_calibrated_two_source_prior_only_no_GLM_or_batch_normalizer'}


def counts(artifact):return {'reused_source_level_parameters':artifact['prior_level_calibration']['target_learned_parameters']}


def level_math(train,artifact):
    return {'same_scope_level_moments':k.p.level_math(train,artifact['prior_level_calibration']),'native_optimization_not_applicable':True}


def final_dump(path,data):
    if path==OUT/'report.json':
        assert len(list(OUT.glob('*_*/learning.json')))==15
        assert len(list(OUT.glob('*_*/primary_reused_prior.json')))==15
        for key in ['primary_components','adverse_components_separate','primary_shared_residual_stages','adverse_shared_residual_stages_separate']:data.pop(key,None)
        data['reused_primary_parameter_counts']=data.pop('primary_constants')
        data.update(status='P98calibrated_prior_only_pooled_complete_transfer_unmeasured',new_native_fits=0,new_primary_closed_levels=0,
            reused_primary_closed_levels=90,reused_adverse_closed_levels_separate=90,new_source_fits=0,new_CDF_fits=0,
            native_convergence_not_applicable=True,target_learned_offset_levels=True,target_learned_shape_or_rowprice_feature_ancestors=False)
    return dump(path,data)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(k.PLAN);m.check_sources(parent);assert w.read(k.OUT/'completion_receipt.json')['report_sha256']==w.sha(k.OUT/'report.json')
    original=w.read(R/'registro/semana2_prior_calibrado_GLM_validacion_plan.json')
    paths=[Path(__file__),Path(h.__file__),k.PLAN,k.OUT/'report.json',k.OUT/'synthetic.json',k.OUT/'completion_receipt.json']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':parent['candidate'],'need':parent['need'],'hypothesis':parent['hypothesis'],
        'one_change':parent['one_change'],'configuration':parent['configuration'],
        **{name:original[name] for name in ['criteria','bootstrap','cohort_guard','level_sensitivity','scenarios','validation']},
        'budget':parent['future_budget'],'staged_decision':parent['future_criterion'],
        'adverse':'Whole cached level learner checked under all held payload poison; original P88 stored levels already passed fresh original train-only estimation under poison. No fresh estimation is repeated.',
        'integration':'Same fifteen outer numerical flows, fixed nominal ultimate forecasts with unchanged scenario links; no GLMfit, intercept, target rating design, new source/q/level estimation or batch normalization.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P98 registra antes de producir precios y puntuar el prior calibrado P97 sin GLM corrector. Mismos componentes, niveles propios por ramo/negocio,50/50, calendario, q y folds; se reutilizan los90 parámetros P88 por claves/datos/código. Cero nuevos ajustes nativos, parámetros cerrados, fuentes o CDF. Se evalúan todos los quince ámbitos y guardas originales globales/cohortes/familia16/nivel/influencia/reservas/cola. Los controles de optimización nativa no aplican al algoritmo cerrado. Veneno retenido, momentos por otro cálculo y replay numérico sin aprendizaje. Si pasa, transferencia propia antes de cualquier CSV; si falla no afinar pesos/K/ramos por el retenido. B00 y alternativas preservadas,2024abierto adaptativo; cero2025/envíos. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P98registered_before_prior_only_prices_and_scores','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P98-PRIOR-PREVIO','P98: evaluación del prior sin corrección, guardas intactas')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def setup():
    h.OUT=OUT;h.PLAN=PLAN;h.INDEX=INDEX;h.DOC=DOC;h.frame_for=k.frame_for;h.learn=learn;h.forward=forward;h.parameter_counts=counts;h.r.independent_math=level_math
    h.setup();h.v.dump=final_dump
    def reject(*args,**kwargs):raise AssertionError('Prior-only evaluation forbids new model and level learning')
    k.p.calibrate_levels=reject;k.p.r.TweedieRegressor.fit=reject


def run():
    setup();m.check_sources(w.read(PLAN));h.v.run();m.check_sources(w.read(PLAN))


def replay():
    setup();assert not (OUT/'replay_report.json').exists();m.check_sources(w.read(PLAN));report=w.read(OUT/'report.json')
    def reject(*args,**kwargs):raise AssertionError('Prior-only replay forbids all learning')
    k.cached=reject;k.p.SCALAR.factor=reject;k.p.SCALAR.cell_levels=reject;q.cost_curves=reject
    for outer in range(5):
        for line in q.LINES:
            folder=OUT/f'{line}_{outer}';saved=w.read(folder/'committed.json')
            assert all(w.sha(ROOT/path)==value for path,value in saved['outputs'].items())
            frame=k.frame_for(line,outer);held=frame.loc[frame.is_held].drop(columns=['T0','reserve','q_paired'])
            value,norm=forward(held,w.read(folder/'learning.json'),True)
            assert np.array_equal(value,pd.read_parquet(folder/'prices.parquet').ultimate) and norm==saved['ultimate_normalizers']
    totals,desc,_,_=m.cohort_blocks();weights=np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    draws=np.load(OUT/'cohort_bootstrap.npy');cohort=w.read(OUT/'cohort_report.json')
    assert np.allclose(m.cohort_scores(weights@totals),draws[:4],rtol=2e-12,atol=2e-13)
    for j,z in enumerate(cohort['comparisons']):assert desc[j]['delta']==z['delta'] and np.array_equal(np.quantile(draws[:,j],[.025/16,1-.025/16]),z['family16_band95'])
    draws=np.load(OUT/'POOLED_joint_bootstrap.npy')
    for j,name in enumerate(m.e.NAMES):assert np.array_equal(np.quantile(draws[:,j],[.025,.975]),report['results']['POOLED'][name]['bootstrap95'])
    m.check_sources(w.read(PLAN));dump(OUT/'replay_report.json',{'author':'Codex','utc':utc(),'report_sha256':w.sha(OUT/'report.json'),
        'all15prior_only_flows_exact':True,'ultimate_excludes_targets_q_and_live_calibration':True,'all_new_learning_blocked':True,
        'saved_intervals_and_first4weights_exact':True,'new_fits':0,'new_resampling':0,'new_submissions':0})
    print(json.dumps({'replay':'exact','members':15,'new_fits':0,'new_resampling':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();m.check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    assert len(list(OUT.glob('*_*/primary_reused_prior.json')))==len(list(OUT.glob('*_*/adverse_reused_prior.json')))==15
    assert not list(OUT.rglob('*fit_invoked.json'))
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];old=w.read(k.OLD/'report.json')['results']['POOLED']['NOMINAL']['delta']
    next_unit=('Register own2023 conditional-transfer evaluation of exact prior-only algorithm and own report before CSV/admission; no borrowed pooled2024 report.' if passed else
        'Use new saved P98 all-line/fold/business cells and levels to distinguish loss already present in the calibrated prior from the additional P88GLM correction, without new fits/inference/resampling. Do not tune source weights, K or retain favorable lines. Next mechanism must address a documented source risk allocation or observation/valuation mismatch rather than add another generic correction.')
    text='# P98: prior calibrado sin corrección, evaluación\n\nCodex, '+utc()+'. '+('Pasa el combinado; falta transferencia antes de un CSV.' if passed else 'El combinado falla y no admite un CSV nuevo.')+'\n\n'
    text+=f"Diferencia D² frente a referencia local: {a['delta']:+.7f}; IC95 por grupos [{a['bootstrap95'][0]:+.7f}, {a['bootstrap95'][1]:+.7f}]. Post31: {a['post31_delta']:+.7f}; peor celda: {a['worst_cell_delta']:+.7f}. Diferencia puntual frente a P88 con GLM: {a['delta']-old:+.7f}, sin nuevo intervalo pareado.\n\n"
    text+='Se evaluaron los quince ámbitos con los90 niveles propios P88 reutilizados por claves/datos/código, sin reestimación. La media fija de riesgos fuente conserva sus componentes/negocio/calendario; no hay GLM corrector, nuevo intercepto, forma de historial, selección de campos o centro por lote. Veneno integral, momentos por otra suma y quince replays finales exactos con todo aprendizaje bloqueado. Los intervalos guardados y cuatro primeras ponderaciones de cohorte se cotejaron sin remuestrear en replay.\n\n'
    text+='Guardas globales: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+='Esta simplificación se eligió tras resultados adversos; la evaluación sigue siendo exploratoria. No demuestra causalidad de cada efecto excluido o rendimiento privado. Fuentes2024 condicionales, snapshots sin fecha de cotización, C0, cola y reservas siguen siendo límites; sensibilidades con precios nominales fijos, sin ajuste completo por escenario. Cero nuevos ajustes nativos/cerrados, fuente/CDF/2025/envíos. B00 y todas las alternativas conservadas;2024abierto adaptativo, sin revisión profesional independiente.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{name:a[name] for name in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P98_minus_P88_point_only':a['delta']-old,
        'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,'reused_primary_closed_levels':90,
        'new_native_fits':0,'new_primary_closed_levels':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0,
        'next_unit':next_unit,'2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P98-PRIOR-RESULTADO','P98: resultado completo del prior sin corrección')}
    cut=R/'privado'/('corte_P98_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));cut.mkdir();w.update(INDEX,receipt,cut)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P98'),(R/'registro/semana2_mision_privada_actual.json','P98')]:w.update(path,{key:receipt,'next_unit':next_unit},cut)
    cp=R/'registro/semana2_contadores_propios_actual.json';w.update(cp,{'phase2_private_P98_prior_only':receipt},cut)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P98=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},cut)
    control=R/'registro/semana2_control_entregas_codex_actual.json';c=w.read(control)
    w.update(control,{'allow_new_submission':False,'reason':'P98 pooled pass requires own transfer and exact CSV admission.' if passed else 'P98 prior-only candidate fails unchanged outer guards; preserve quota and alternatives, no missing human authorization.',
        'last_evidence_review_utc':receipt['utc'],'latest_rejected_research_alternatives':c['latest_rejected_research_alternatives']+([] if passed else ['P98'])},cut)
    note='\n\n## Privada P98: prior sin GLM, evaluación\n\nCodex, '+receipt['utc']+'. Decisión='+receipt['decision']+'; quince flujos/niveles reutilizados, cero ajustes nuevos o envíos, replay exacto. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cut)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_prior_only_validation_index':w.rel(INDEX),'week_2_private_prior_only_validation_report':w.rel(DOC)},cut)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');a=argparse.ArgumentParser(description=__doc__);a.add_argument('mode',choices=['prepare','run','replay','close'])
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[a.parse_args().mode]()
