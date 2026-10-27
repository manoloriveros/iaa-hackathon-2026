"""Evalúa el algoritmo completo de selección interna común P84."""
from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
import importlib.util
import argparse
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);a=importlib.util.module_from_spec(s);s.loader.exec_module(a);return a
k=load('p85_inner_selection_kernel',R/'herramientas/preparar_seleccion_GLM_P84.py')
h=load('p85_unchanged_outer_evaluator',R/'herramientas/validar_GLM_fuente_directa_P75.py')
m=h.m;q=h.q;w=h.w;np=h.np;pd=h.pd;BASE=h.BASE;v=h.v
OUT=BASE/'P85_validacion_seleccion_GLM_20261027'
PLAN=R/'registro/semana2_seleccion_GLM_interna_validacion_plan.json';INDEX=R/'registro/semana2_seleccion_GLM_interna_validacion_actual.json'
DOC=R/'docs/semana2/PRIVADA_P85_VALIDACION_SELECCION_GLM.md'
OLD=BASE/'P82_validacion_GLM_bandas_negocio_20261027'
ORIGINAL_FIT_ALPHA=k.fit_alpha


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def frames_for(outer):return {line:k.k.frame_for(line,outer) for line in q.LINES}


def tables_for(outer):
    spec=w.read(k.OUT/'bindings.json')['outputs'];tables={member:{} for member in range(5)}
    for member in range(5):
        for line in q.LINES:
            path=k.OUT/'inputs'/f'o{outer}_i{member}_{line}.parquet';assert w.sha(path)==spec[w.rel(path)]
            tables[member][line]=pd.read_parquet(path)
    return tables


def fit_alpha(frame,line,alpha,folder):
    # Exact fixed-alpha1final learners already exist. Reuse rather than train the
    # identical function/data again when the NEWinner selector chooses that value.
    if folder.parent.name=='final' and alpha==1.:
        outer=int(folder.parents[2].name.removeprefix('outer'));prior=OLD/f'{line}_{outer}'
        a=w.read(prior/'learning.json');assert a==w.read(prior/'adverse_learning.json')
        assert a['fit_row_ids_digest']==m.p.b.digest(sorted(frame.loc[~frame.is_held,'row_id']))
        assert a['fit_groups_digest']==m.p.b.digest(sorted(set(frame.loc[~frame.is_held,'group_id'])))
        source=w.read(R/'registro/semana2_GLM_bandas_negocio_validacion_plan.json')['sources']
        for path in [Path(k.k.__file__),Path(k.k.b.__file__),Path(k.k.r.__file__),k.k.r.p.t.t.OUT/f'input_{line}_{outer}.parquet']:
            assert source[w.rel(path)]==w.sha(path)
        assert a['parameters']=={**k.k.r.PARAMS,'alpha':alpha} and a['sklearn_version']==k.k.r.sklearn.__version__
        folder.mkdir(parents=True,exist_ok=True)
        receipt=folder/'reused_exact_alpha1.json'
        if not receipt.exists():dump(receipt,{'author':'Codex','utc':utc(),'source':w.rel(prior/'learning.json'),'sha256':w.sha(prior/'learning.json'),
            'old_adverse_exact':True,'same_training_keys_code_data_params':True,'new_native_fits':0})
        return a
    return ORIGINAL_FIT_ALPHA(frame,line,alpha,folder)


def produce_bundle(outer,adverse):
    frames=frames_for(outer)
    if adverse:frames={line:k.k.poison(f,line) for line,f in frames.items()}
    folder=OUT/f'outer{outer}';name='adverse_bundle' if adverse else 'primary_bundle'
    def produce():
        fits=folder/('adverse_fits' if adverse else 'primary_fits')
        a=k.train_bundle(frames,tables_for(outer),fits)
        a['logical_GLMlearner_count']=a.pop('actual_GLMfit_count')
        a['actual_new_native_fits']=len(list(fits.rglob('actual_fit_invoked.json')))
        a['reused_exact_final_alpha1']=len(list(fits.rglob('reused_exact_alpha1.json')))
        assert a['logical_GLMlearner_count']==48 and a['actual_new_native_fits']+a['reused_exact_final_alpha1']==48
        print(json.dumps({'outer':outer,'adverse':adverse,'selected_alpha':a['selection']['alpha'],'new_nativefits':a['actual_new_native_fits'],'reused_final':a['reused_exact_final_alpha1']}),flush=True)
        return a
    return m.once(folder,name,produce)


def learn(frame,line):
    outer=int(frame.loc[frame.is_held,'fold'].unique().item());adverse=bool(frame.loc[frame.is_held,'T0'].lt(0).any())
    bundle=produce_bundle(outer,adverse);artifact=dict(bundle['models'][line]);artifact['common_inner_selection']=bundle['selection'];return artifact


def forward(frame,artifact,ultimate=True):
    assert ultimate;value,_=k.k.forward(frame,artifact)
    return value,{'kind':'common_inner_alpha_GLM_no_batch_normalizers','alpha':artifact['parameters']['alpha']}


def independent_math(train,artifact):
    params=k.k.r.PARAMS;k.k.r.PARAMS={**params,'alpha':artifact['parameters']['alpha']}
    try:return k.k.independent_math(train,artifact)
    finally:k.k.r.PARAMS=params


def report_dump(path,data):
    if path==OUT/'report.json':
        bundles=[w.read(OUT/f'outer{outer}/primary_bundle.json') for outer in range(5)]
        adverse=[w.read(OUT/f'outer{outer}/adverse_bundle.json') for outer in range(5)];assert bundles==adverse
        convergence=all(a['all_native_fits_converged'] for a in bundles)
        data['pooled_gates']['all_inner_and_final_GLM_convergence_pass']=convergence
        data['all_pooled_gates_pass']=data['all_pooled_gates_pass'] and convergence
        data['decision']='TRANSFER_REQUIRED_BEFORE_ADMISSION' if data['all_pooled_gates_pass'] else 'REJECT_FROM_POOLED_FAILURE_TRANSFER_UNEVALUATED'
        for name in ['primary_components','adverse_components_separate','primary_shared_residual_stages','adverse_shared_residual_stages_separate']:data.pop(name,None)
        data['primary_final_parameter_counts']=data.pop('primary_constants');data['primary_whole_learners']=5;data['adverse_whole_learners_separate']=5
        data.update(status='P85common_inner_selected_GLM_pooled_complete_transfer_unmeasured',primary_inner_GLMlearners=225,primary_final_GLMlearners=15,
            actual_new_primary_nativefits=sum(a['actual_new_native_fits'] for a in bundles),actual_new_adverse_nativefits_separate=sum(a['actual_new_native_fits'] for a in adverse),
            primary_reused_exact_alpha1_final=sum(a['reused_exact_final_alpha1'] for a in bundles),adverse_reused_exact_alpha1_final_separate=sum(a['reused_exact_final_alpha1'] for a in adverse),
            primary_selections=[{'outer':j,**a['selection']} for j,a in enumerate(bundles)],all_inner_and_final_convergence_pass=convergence,
            new_source_fits=0,new_target_base_fits=0,new_CDF_fits=0,new_closed_constants=0)
    return dump(path,data)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(k.PLAN);m.check_sources(parent);pre=w.read(k.OUT/'report.json');assert w.read(k.OUT/'completion_receipt.json')['report_sha256']==w.sha(k.OUT/'report.json')
    assert all(w.sha(ROOT/path)==value for path,value in pre['outputs'].items())
    original_path=R/'registro/semana2_GLM_bandas_negocio_validacion_plan.json';original=w.read(original_path);m.check_sources(original)
    paths=[Path(__file__),Path(h.__file__),k.PLAN,k.OUT/'report.json',k.OUT/'synthetic.json',k.OUT/'bindings.json',k.OUT/'completion_receipt.json',original_path,OLD/'report.json',OLD/'completion_receipt.json']
    for line in q.LINES:
        for outer in range(5):paths += [OLD/f'{line}_{outer}/learning.json',OLD/f'{line}_{outer}/adverse_learning.json']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':'P82standardGLMwith_FULLfive-inner-common-alpha-selection_then_final_perline',
        'need':parent['need'],'hypothesis':parent['hypothesis'],'configuration':parent['configuration'],
        **{key:original[key] for key in ['criteria','bootstrap','cohort_guard','level_sensitivity','scenarios']},
        'logical_budget':parent['future_budget'],'native_fit_budget':'At most240primary/240adverse nativefits;225inner each always new,15final each only if selectedalpha differs from1. Exact originalP82alpha1final model may be reused only after same trainingkeys/code/data/params checks and old actual adverse equality. No redundant final refit; algorithm unchanged.',
        'integration':'Five complete outer algorithms, each chooses ONEalpha across all3lines using all5innerfolds and45candidateGLMs; then three final GLMs. This couples lines through training-onlyselection. Old evaluator15line price wrappers do not imply15independent whole algorithms. Actual nativefit markers from P84inside every new estimator call; raw snapshots before math controls.',
        'adverse':'Full second whole selector/final flow with ALLouterheld target/source/rating/calendar/qpayload corrupted before inner extraction and final preprocessing. Own inner report objects are immutable protected P67ancestors with matched exact trainingIDs and new numeric binding. Preserve their historical real reporting-adverse proofs, no new CDFlearning claim.',
        'staged_decision':parent['future_criterion'],'sources':{**parent['sources'],**pre['outputs'],**{w.rel(path):w.sha(path) for path in paths}},
        'limits':parent['limits'],'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P85registra ANTESdeajustar evaluación completa del selectorP84, alpha[1,.1,.01]común a los3ramos, elegido SOLOen cincofolds internos propios.225GLMinternos+15finales lógicos porprimarioyadverso, hasta240+240fitsnativos nuevos; si se elige1se reutiliza el finalP82exacto por claves/código/datos/parámetros y su prueba adversa previa, sin repetir ajuste idéntico. Curvas internasP67propias y75vectores qverificados, nunca qexterior para elegiralpha. Preprocesos internos propios. Cincoalgoritmos completos exteriores, no15algoritmos independientes. Todas las guardas/IC/cohortes/familia16/escenarios/nivel/influencia, convergencia de TODOSlos candidatos y replay de225objetivos/15finales sin ajuste. Si pasa combinado falta transferencia propia2023; si falla noCSV. Sin refinargrid/campos/ramo, fuente/base/CDF/2025/envíos. B00/adversos conservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P85registered_before_real_whole_inner_selection','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P85-SELECTOR-PREVIO','P85: selección interna completa, todas las guardas antes de ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def setup():
    h.OUT=OUT;h.PLAN=PLAN;h.INDEX=INDEX;h.setup()
    k.fit_alpha=fit_alpha
    v.k=SimpleNamespace(frame_for=k.k.frame_for,learn=learn,forward=forward,constant_counts=h.parameter_counts)
    v.component_level_math=independent_math;v.dump=report_dump


def run():setup();v.run()


def replay():
    assert not (OUT/'replay_report.json').exists();plan=w.read(PLAN);m.check_sources(plan);report=w.read(OUT/'report.json');m.OUT=OUT;m.e.OUT=OUT
    def reject(*args,**kwargs):raise AssertionError('P85replay blocks ALLnew GLM/source/report learning')
    k.fit_alpha=reject;k.k.r.TweedieRegressor.fit=reject;k.ORIGINAL_NATIVE_FIT=reject;q.cost_curves=reject;k.k.r.p.u.reporting=reject
    for outer in range(5):
        frames=frames_for(outer)
        for f in frames.values():f.loc[f.is_held,['T0','reserve','q_paired']]=float('nan')
        bundle=w.read(OUT/f'outer{outer}/primary_bundle.json');values=k.replay_bundle(frames,tables_for(outer),bundle)
        for line in q.LINES:
            folder=OUT/f'{line}_{outer}';saved=w.read(folder/'committed.json');assert all(w.sha(ROOT/path)==value for path,value in saved['outputs'].items())
            assert np.array_equal(values[line],pd.read_parquet(folder/'prices.parquet').ultimate)
            assert saved['ultimate_normalizers']=={'kind':'common_inner_alpha_GLM_no_batch_normalizers','alpha':bundle['selection']['alpha']}
    totals,desc,_,_=m.cohort_blocks();weights=np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    draws=np.load(OUT/'cohort_bootstrap.npy');cohort=w.read(OUT/'cohort_report.json')
    assert np.allclose(m.cohort_scores(weights@totals),draws[:4],rtol=2e-12,atol=2e-13)
    for j,z in enumerate(cohort['comparisons']):assert desc[j]['delta']==z['delta'] and np.array_equal(np.quantile(draws[:,j],[.025/16,1-.025/16]),z['family16_band95'])
    draws=np.load(OUT/'POOLED_joint_bootstrap.npy')
    for j,name in enumerate(m.e.NAMES):assert np.array_equal(np.quantile(draws[:,j],[.025,.975]),report['results']['POOLED'][name]['bootstrap95'])
    m.check_sources(plan);dump(OUT/'replay_report.json',{'author':'Codex','utc':utc(),'report_sha256':w.sha(OUT/'report.json'),'all5whole_selectors225inner_objectives_exact':True,
        'all15final_GLMpredictions_exact':True,'all_new_learning_blocked':True,'held_q_target_not_used_by_final':True,'saved_intervals_and_first4weights_exact':True,'new_fits':0,'new_resampling':0,'new_submissions':0})
    print(json.dumps({'replay':'exact','complete_selectors':5,'inner_objectives':225,'final_models':15,'new_fits':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();m.check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];number=d['actual_new_primary_nativefits']+d['actual_new_adverse_nativefits_separate']
    assert number==len(list(OUT.glob('outer*/*_fits/**/actual_fit_invoked.json')))
    next_unit=('Register OWN2023-only conditionaltransfer of EXACTP85whole common-alpha selector, with own outer/innerreporting and unchanged criteria before any production/CSVadmission. No pooled2024targettrained report borrowed.' if passed else
        'Review NEWP85saved selectedalphas/inner-vs-outer losses and complete held cells against fixedP82/P65without refit/resampling. Do not refine grid, choose perline alphas or override fields/bands from outer/public outcomes. Need a distinct documented source/target/reporting mechanism before another recipe; preserve all alternatives/quota.')
    text='# P85: selección interna de regularización, evaluación completa\n\nCodex, '+utc()+'. '+('El combinado pasa; falta transferencia propia antes de admitir un CSV.' if passed else 'El combinado falla; no se admite CSV y la transferencia permanece sin evaluar.')+'\n\n'
    text+=f"ΔD²frente a referencia={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f};{a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}.\n\n"
    text+='Cinco algoritmos completos exteriores eligieron cada uno unalpha común a los3ramos, exclusivamente con sus cincofolds internos y45GLMcandidatos. Después se ajustó/reutilizó un modelo final por ramo. Mismo GLM/fields/bandas/prior y qpropio de cada ámbito; no elección de pesos oalpha por resultados exteriores/públicos. Guardas: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+=f"Ajustes nativos NUEVOS: primarios={d['actual_new_primary_nativefits']}, adversos={d['actual_new_adverse_nativefits_separate']}; finalesalpha1exactos reutilizados={d['primary_reused_exact_alpha1_final']}+{d['adverse_reused_exact_alpha1_final_separate']}. No se repitió un ajuste final idéntico. Toda selección/modelos coincidió al alterar el payload exterior completo. Replay de225objetivos internos/cinco selectores y15predicciones finales exacto con aprendizaje bloqueado; intervalos y sumas guardadas cotejados sin remuestreo adicional.\n\n"
    text+='| Fold exterior | Alpha elegido dentro del entrenamiento |\n|---|---:|\n'
    for z in d['primary_selections']:text+=f"|{z['outer']}|{z['alpha']}|\n"
    text+='\nEscenarios con últimos nominales fijos, sin reajuste completo por escenario. Cero nuevos modelos fuente/bases/CDF/2025/envíos. Las curvas internas son ancestrosP67propios reutilizados porSHA/grupos/enlace numérico, no nuevas estimaciones. Persisten información fuente2024condicional, proxy/cola/reservas/maestros y selección adaptativa; sin mejora privada acreditada o revisión independiente. B00/F3cyalternativas conservados,2024abierto adaptativo.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{key:a[key] for key in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,
        'actual_new_primary_nativefits':d['actual_new_primary_nativefits'],'actual_new_adverse_nativefits_separate':d['actual_new_adverse_nativefits_separate'],'native_fits_added_to_counter':number,
        'primary_selected_alphas':[z['alpha'] for z in d['primary_selections']],'new_source_fits':0,'new_target_base_fits':0,'new_CDF_fits':0,'new_closed_constants':0,'new2025inference':0,'new_submissions':0,
        'next_unit':next_unit,'2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P85-SELECTOR-RESULTADO','P85: resultado completo del selector interno y límites')}
    archive=R/'privado'/('corte_P85_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    cp=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(cp);assert 'phase2_private_P85_inner_selection' not in counts
    w.update(cp,{'cumulative_price_base_fits':counts['cumulative_price_base_fits']+number,'phase2_private_P85_inner_selection':receipt},archive);w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P85'),(R/'registro/semana2_mision_privada_actual.json','P85')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P85=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    control=R/'registro/semana2_control_entregas_codex_actual.json';old=w.read(control)
    w.update(control,{'allow_new_submission':False,'reason':'P85requires own conditionaltransfer before admission.' if passed else 'P85whole training-only common-alpha selector fails unchanged outer admission guards; preserve quota/alternatives, no missing human authorization.',
        'last_evidence_review_utc':receipt['utc'],'latest_rejected_research_alternatives':old['latest_rejected_research_alternatives']+([] if passed else ['P85'])},archive)
    note='\n\n## Privada P85: selección interna común, validación\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+f';{number}fitsnativos nuevos, cinco selectores y15modelos finales replayexacto; cero fuente/CDF/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_inner_selection_validation_index':w.rel(INDEX),'week_2_private_inner_selection_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['prepare','run','replay','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
