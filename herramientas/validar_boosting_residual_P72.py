"""Validación completa de boosting residual restringido con padres OOF fijos."""
from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
import importlib.util
import argparse
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p72_standard_residual_trees',R/'herramientas/preparar_boosting_residual_P71.py')
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
p=r.p;v=p.driver.v;g=r.g;m=r.m;q=r.q;w=r.w;pd=r.pd;np=r.np;BASE=r.BASE
OUT=BASE/'P72_validacion_boosting_residual_20261027'
PLAN=R/'registro/semana2_boosting_residual_validacion_plan.json';INDEX=R/'registro/semana2_boosting_residual_validacion_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P72_VALIDACION_BOOSTING_RESIDUAL.md'
ORIGINAL_TRAIN=r.lgb.train;FIT_PATH=None


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)
def frame_for(line,outer):return p.frame_for(line,outer)


def observed_train(*args,**kwargs):
    assert FIT_PATH is not None and not FIT_PATH.exists()
    dump(FIT_PATH,{'author':'Codex','utc':utc(),'actual_native_lgb_train_invoked':True,'parameters':r.PARAMS,'rounds':r.ROUNDS})
    return ORIGINAL_TRAIN(*args,**kwargs)


def learn(frame,line):
    global FIT_PATH
    outer=int(frame.loc[frame.is_held,'fold'].unique().item());folder=OUT/f'{line}_{outer}'
    adverse=frame.loc[frame.is_held,'T0'].lt(0).any();name='adverse' if adverse else 'primary';FIT_PATH=folder/(name+'_fit_invoked.json')
    payload=g.poison(frame,line) if adverse else frame
    return r.fit(payload,line,checkpoint=folder/(name+'_native_model_raw.json'))


def forward(frame,artifact,ultimate=True):
    assert ultimate;value,relative=r.forward(frame,artifact)
    return value,{'kind':'Native_residual_tree_after_P65ultimate_base','relative_prediction_digest':m.p.b.digest(relative.tolist())}


def parameter_counts(artifact):return {'fitted_tree_leaf_values':artifact['fitted_leaf_values']}


def report_dump(path,d):
    if path==OUT/'report.json':
        artifacts=[w.read(path) for path in OUT.glob('*_*/learning.json')];assert len(artifacts)==15
        integrity=all(a['native_offset_metric_scalar_match'] and a['leaf_sum_and_serialization_exact'] and a['actual_max_absolute_train_log_correction']<=a['max_absolute_log_correction_bound']+1e-10 for a in artifacts)
        d['pooled_gates']['all_native_tree_offset_integrity_pass']=integrity;d['all_pooled_gates_pass']=d['all_pooled_gates_pass'] and integrity
        d['decision']='TRANSFER_REQUIRED_BEFORE_ADMISSION' if d['all_pooled_gates_pass'] else 'REJECT_FROM_POOLED_FAILURE_TRANSFER_UNEVALUATED'
        for key in ['primary_components','adverse_components_separate','primary_shared_residual_stages','adverse_shared_residual_stages_separate']:d.pop(key,None)
        d['primary_iterative_tree_leaf_counts']=d.pop('primary_constants');d['status']='P72standard_restricted_residual_trees_pooled_complete_transfer_unmeasured'
        d.update(primary_final_tree_fits=15,adverse_final_tree_fits_separate=15,new_closed_constants=0,new_base_fits=0,new_source_fits=0,new_CDF_fits=0,
            inherited_P67_inner_reporting_scopes=25,inherited_P67_inner_base_learners=75,configured_trees_per_fit=r.ROUNDS,all_native_tree_offset_integrity_pass=integrity,
            GLM_stationarity_gate_not_applicable=True,original_predictive_gates_unmodified=True)
    return dump(path,d)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(r.PLAN);r.check_sources(parent);assert w.read(r.OUT/'completion_receipt.json')['report_sha256']==w.sha(r.OUT/'report.json')
    original=w.read(p.PLAN);paths=[Path(__file__),r.PLAN,r.OUT/'report.json',r.OUT/'synthetic.json',r.OUT/'completion_receipt.json',p.PLAN]
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':'P71restricted_native_offset_residual_GBDT_current_report_crossfit_base',
        'need':parent['need'],'hypothesis':'The fixed shallow small-step piecewise correction may generalize more stably than the tested global main-effect GLMs. No observed interaction cause or known gain is asserted.',
        'configuration':parent['configuration'],'budget':parent['future_budget'],
        **{key:original[key] for key in ['criteria','bootstrap','cohort_guard','level_sensitivity','scenarios']},
        'ancestors':'Exact P67OOFnumeric inputs, own inner report/base artifacts and fullouterP65base on held. All parents fixed; actual nested artifact hashes verified. No price/source/CDFrefit or copied held-trained factors.',
        'adverse':'Actual second native train call with ALLheld cost/offset/raw fields corrupted before the real training/preprocessor selector. Raw native model saved before controls; exact primary/adverse artifact equality.',
        'staged_decision':parent['future_criterion'],'runtime_sources':parent['runtime_sources'],
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P72registra antes de entrenar15boosting residuales finales primarios/15adversos, receta únicaP71:64rondas/depth3/7hojas/paso.003, campos e inputsOOFP67idénticos, T0íntegro yoffset nativo. No earlystopping, búsqueda o nuevas fuentes/bases/CDF. Cada llamada real queda marcada y modelo nativo guardado antes de controles; métrica offset, suma de hojas, límites, precisión/replay. Conserva TODASlas guardas predictivas/cohortes/escenarios/nivel/influencia/familia16; solo el control de estacionariedadGLMes inaplicable, sustituido por integridad del algoritmo finito. Pooledfallido impide CSV, pasado exige transferencia propia. B00preservado,2024abierto adaptativo y cero2025/envíos. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P72registered_before_real_native_residual_tree_learning','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P72-ARBOL-PREVIO','P72: boosting residual completo, receta fija y guardas antes de ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def setup():
    v.OUT=OUT;v.PLAN=PLAN;v.INDEX=INDEX;m.OUT=OUT;m.e.OUT=OUT;v.SCENARIO=p.t.OUT/'scenario_inputs';m.apply_q=p.t.apply_row_q
    v.k=SimpleNamespace(frame_for=frame_for,learn=learn,forward=forward,constant_counts=parameter_counts)
    v.component_level_math=r.independent_math;v.dump=report_dump


def run():
    r.check_sources(w.read(PLAN));setup();r.lgb.train=observed_train;v.run();r.check_sources(w.read(PLAN))


def replay():
    assert not (OUT/'replay_report.json').exists();r.check_sources(w.read(PLAN));report=w.read(OUT/'report.json');m.OUT=OUT;m.e.OUT=OUT
    def reject(*args,**kwargs):raise AssertionError('P72replay blocks all new tree/base/report learning')
    r.fit=reject;r.lgb.train=reject;g.fit=reject;p.k.learn=reject;p.u.reporting=reject;q.cost_curves=reject
    for outer in range(5):
        for line in q.LINES:
            folder=OUT/f'{line}_{outer}';saved=w.read(folder/'committed.json');assert all(w.sha(ROOT/path)==value for path,value in saved['outputs'].items())
            f=frame_for(line,outer);f.loc[f.is_held,['T0','reserve','baseline_observed','q_paired']]=np.nan
            value,norm=forward(f.loc[f.is_held],w.read(folder/'learning.json'),True)
            assert np.array_equal(value,pd.read_parquet(folder/'prices.parquet').ultimate) and norm==saved['ultimate_normalizers']
    totals,desc,_,_=m.cohort_blocks();weights=np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    draws=np.load(OUT/'cohort_bootstrap.npy');cohort=w.read(OUT/'cohort_report.json')
    assert np.allclose(m.cohort_scores(weights@totals),draws[:4],rtol=2e-12,atol=2e-13)
    for j,z in enumerate(cohort['comparisons']):assert desc[j]['delta']==z['delta'] and np.array_equal(np.quantile(draws[:,j],[.025/16,1-.025/16]),z['family16_band95'])
    draws=np.load(OUT/'POOLED_joint_bootstrap.npy')
    for j,name in enumerate(m.e.NAMES):assert np.array_equal(np.quantile(draws[:,j],[.025,.975]),report['results']['POOLED'][name]['bootstrap95'])
    r.check_sources(w.read(PLAN));dump(OUT/'replay_report.json',{'author':'Codex','utc':utc(),'report_sha256':w.sha(OUT/'report.json'),'all15native_tree_flows_exact':True,
        'labels_observed_offset_q_not_read_during_ultimate':True,'all_new_learning_blocked':True,'saved_intervals_and_first4weights_exact':True,'new_fits':0,'new_resampling':0,'new_submissions':0})
    print(json.dumps({'replay':'exact','members':15,'new_fits':0,'new_resampling':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();r.check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    assert len(list(OUT.glob('*_*/primary_fit_invoked.json')))==len(list(OUT.glob('*_*/adverse_fit_invoked.json')))==15
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];parent_point=w.read(p.t.OUT/'report.json')['results']['POOLED']['NOMINAL']['delta']
    next_unit=('Register OWN2023-only conditional-transfer complete reporting/base/OOF/residualGBDTpipeline with same fixed64roundrecipe and all guards before any production/CSV. Never reuse pooled2024target-trained parents there.' if passed else
        'Review NEWP72saved tree corrections/held cohort losses vs P65/P67/P70without refitting/resampling. No depth/round/leaf/step/feature or line rescue from this failure. Identify an actual source/observation/target mechanism before further capacity or a new registered model; no public probe or missing human authorization.')
    text='# P72: boosting residual restringido, evaluación completa\n\nCodex, '+utc()+'. '+('El combinado pasa; falta transferencia propia antes de admitir.' if passed else 'El combinado falla; no se admite CSV, transferencia sin evaluar.')+'\n\n'
    text+=f"ΔD²nominal={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f};{a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}. Diferencia puntual frente aP65={a['delta']-parent_point:+.7f}, sin nuevo intervalo pareado.\n\n"
    text+='15modelos nativos primarios/15adversos reales;64rondas fijadas/depth3/7hojas/pasos pequeños, mismos campos y padresOOFP67. La métrica nativa verificó el offset aplicado durante entrenamiento; suma escalar de hojas/límites/serialización, selector train-only y veneno retenido coincidieron. Quince replays finales exactos sin aprendizaje/remuestreo. Se registra precisiónfloat32de etiquetas nativas; evaluación con T0originalfloat64íntegro. No hay búsqueda de parámetros, pesos o campos.\n\n'
    text+='Guardas: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+='Los parámetros de hojas son iterativos, no constantes cerradas nuevas. No nuevos padres fuente/base/CDF, precios2025o envíos. Las sensibilidades mantienen últimos nominales fijos; no se afirma ajuste completo por escenario. Min_dataes aproximado y no certifica credibilidad; los pasos limitados no prueban mejora privada. Se conservan B00/F3cyalternativas,2024abierto adaptativo y límites de mercado/cola/reservas/maestros/fuente2024condicional y aprendizaje64%/80%. Sin revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{key:a[key] for key in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P72_minus_P65_point_only':a['delta']-parent_point,'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,
        'primary_final_tree_fits':15,'adverse_final_tree_fits_separate':15,'primary_iterative_tree_leaf_counts':d['primary_iterative_tree_leaf_counts'],
        'new_closed_constants':0,'new_base_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0,'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P72-ARBOL-RESULTADO','P72: resultado completo de boosting residual restringido')}
    archive=R/'privado'/('corte_P72_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    cp=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(cp);assert 'phase2_private_P72_residual_trees' not in counts
    w.update(cp,{'cumulative_price_base_fits':counts['cumulative_price_base_fits']+30,'phase2_private_P72_residual_trees':receipt},archive);w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P72'),(R/'registro/semana2_mision_privada_actual.json','P72')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P72=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P72: boosting residual restringido completo\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+';15modelos nativos primarios/15adversos, replay exacto, cero nuevos padres/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_residual_boosting_validation_index':w.rel(INDEX),'week_2_private_residual_boosting_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['prepare','run','replay','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
