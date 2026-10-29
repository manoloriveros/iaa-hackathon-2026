"""Evalúa el GLM P56 completo reutilizando el evaluador P55 sin cambiar sus guardas."""
from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
import importlib.util
import argparse
import json
import math
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p57_frozen_offset_glm',R/'herramientas/preparar_GLM_offset_P56.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
v=g.v;m=g.m;w=g.w;pd=g.pd;np=g.np;BASE=g.BASE
OUT=BASE/'P57_validacion_GLM_offset_20261027'
PLAN=R/'registro/semana2_GLM_offset_validacion_plan.json';INDEX=R/'registro/semana2_GLM_offset_validacion_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P57_VALIDACION_GLM_OFFSET.md'
BASELINE=g.v.OUT;RAW_DUMP=m.dump;ORIGINAL_FIT=g.TweedieRegressor.fit;FIT_PATH=None


def utc():return datetime.now(timezone.utc).isoformat()
def dump(p,value):return RAW_DUMP(p,value)


def frame_for(line,outer):
    return pd.read_parquet(g.OUT/f'input_{line}_{outer}.parquet')


def observed_fit(self,*args,**kwargs):
    assert FIT_PATH is not None and not FIT_PATH.exists()
    dump(FIT_PATH,{'author':'Codex','utc':utc(),'actual_estimator_fit_invoked':True,'parameters':g.PARAMS})
    return ORIGINAL_FIT(self,*args,**kwargs)


def learn(f,line):
    global FIT_PATH
    outer=int(f.loc[f.is_held,'fold'].unique().item());folder=OUT/f'{line}_{outer}'
    adverse=f.loc[f.is_held,'T0'].lt(0).any();name='adverse' if adverse else 'primary'
    FIT_PATH=folder/(name+'_fit_invoked.json')
    payload=g.poison(f,line) if adverse else f
    return g.fit(payload,line,checkpoint=folder/(name+'_model_raw.json'))


def parameter_counts(a):return {'iterative_GLM_coefficients':len(a['coef']),'iterative_GLM_intercepts':1}


def forward(f,a,ultimate=True):
    assert ultimate,'P57uses ultimate prediction then own q, never an observed-stage substitution'
    u,relative=g.forward(f,a)
    return u,{'kind':'GLM_has_no_batch_normalizer_after_saved_P55base','relative_prediction_digest':m.p.b.digest(relative.tolist())}


def independent_math(train,a):
    x,_=g.design(train,a['line'],a['preprocess']);base=train.baseline_observed.to_numpy(float)
    relative=np.exp(x@np.asarray(a['coef'])+a['intercept']);y=train.T0.to_numpy(float)
    raw=math.fsum((4*y/np.sqrt(base*relative)+4*np.sqrt(base*relative)-8*np.sqrt(y)).tolist())
    transformed=math.fsum((np.sqrt(base)*(4*(y/base)/np.sqrt(relative)+4*np.sqrt(relative)-8*np.sqrt(y/base))).tolist())
    assert math.isclose(raw,transformed,rel_tol=2e-12,abs_tol=1e-7)
    weight=np.sqrt(base);score=weight*(np.sqrt(relative)-(y/base)/np.sqrt(relative))/weight.sum()
    vector=np.r_[score.sum(),x.T@score+g.PARAMS['alpha']*np.asarray(a['coef'])]
    assert math.isclose(float(np.abs(vector).max()),a['gradient_inf'],rel_tol=2e-9,abs_tol=2e-13)
    # Independent scalar dot products for the intercept and three fixed coordinate gradients.
    assert math.isclose(math.fsum(score.tolist()),vector[0],abs_tol=2e-13)
    for j in range(min(3,x.shape[1])):
        scalar=math.fsum((x[:,j]*score).tolist())+g.PARAMS['alpha']*a['coef'][j]
        assert math.isclose(scalar,vector[j+1],abs_tol=2e-13)
    return {'offset_loss_scalar_identity':True,'gradient_vector_and_scalar_coordinates_match':True,'gradient_inf':a['gradient_inf']}


def report_dump(path,d):
    if path==OUT/'report.json':
        artifacts=[w.read(p) for p in OUT.glob('*_*/learning.json')]
        assert len(artifacts)==15
        convergence=all(not a['warnings'] and a['gradient_inf']<1e-5 for a in artifacts)
        d['pooled_gates']['all_GLM_convergence_controls_pass']=convergence
        d['all_pooled_gates_pass']=d['all_pooled_gates_pass'] and convergence
        d['decision']='TRANSFER_REQUIRED_BEFORE_ADMISSION' if d['all_pooled_gates_pass'] else 'REJECT_FROM_POOLED_FAILURE_TRANSFER_UNEVALUATED'
        for key in ['primary_components','adverse_components_separate','primary_shared_residual_stages','adverse_shared_residual_stages_separate']:d.pop(key,None)
        d['primary_parameter_counts']=d.pop('primary_constants');d['status']='P57offset_GLM_complete_pooled_transfer_unmeasured'
        d.update(primary_GLM_fits=15,adverse_GLM_fits_separate=15,new_P55_base_fits=0,new_closed_constants=0,
            inherited_P55_base_components=30,all_GLM_convergence_controls_pass=convergence)
    return dump(path,d)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(g.PLAN);assert w.read(g.OUT/'completion_receipt.json')['plan_sha256']==w.sha(g.PLAN)
    assert (g.OUT/'preflight_code.py').read_bytes()==Path(g.__file__).read_bytes();m.check_sources(parent)
    paths=[Path(__file__),g.PLAN,g.OUT/'completion_receipt.json',g.OUT/'synthetic.json',g.OUT/'bindings.json']
    sources=dict(parent['sources']);sources.update({w.rel(p):w.sha(p) for p in paths})
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':'P55fixed_half_base_plus_P56standard_main_effects_offset_GLM',
        **{name:parent[name] for name in ['need','hypothesis','base','model','numeric','categorical','additional_numeric','preprocessing','offset_identity','convergence','availability']},
        **parent['acceptance'],'validation':'Reuse unchanged P55numeric/scenario/cohort evaluator with a runtime adapter for the registered GLM. Saved P56train/held input frames already bind complete protected P55base ancestry. Refit only the new GLM. Full production later must learn base+GLMon all-training, no5GLMmean. Same109296rows,5globalfolds,2023/2024adaptive, all3lines.',
        'adverse_control':'Actual second GLMfit with ALLheld cost/offset/raw numeric/categorical values corrupted before entering the real train-only preprocessing function. Saved coefficients before controls, actual estimator-fit markers, scalar objective/gradient, saved full-flow replay without learning/resampling.',
        'staged_decision':'Every unchanged pooled guard AND solver/convergence guard must pass. Any failure prevents admission; transfer remains None. A pooled pass requires OWNconditional-transfer reporting, P54base and GLMtrained only on admissible2023targetgroups; NEVERreuse P55base trained on2024for that test. Source-only A1S/T2bcoefficients remain fixed with source2024conditional limit.',
        'budget':{'primary_GLM_fits':15,'adverse_GLM_fits_separate':15,'primary_preprocessors':15,'adverse_preprocessors_separate':15,
            'new_P55_base_fits':0,'new_source_fits':0,'new_C0_fits':0,'new_bootstrap_replicates_per_POOLED_and_cohort':2000,
            'new2025inference':0,'new_submissions':0},
        'limits':['Adaptive conditional competition comparison, not an as-of quote backtest or independent professional validation.',
            'Shared line reporting qand source ancestry/undated master assumptions persist. No proof of private gain from synthetic math or a public score.',
            'No interactions or field/hyperparameter search; every adverse fit/result retained. Coefficients are iterative GLMparameters, not new closed-form constants.'],
        'sources':sources,'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P57preinscribe quince GLM Tweedie1,5primarios y15adversos reales, L2=1, enlace log, efectos principales fijados en P56y offset completo P55. Objetivo/exposición intactos: y/bcon pesos√b, calendario/qincluidos una vez. Se alterarán etiquetas, atributos y offsets retenidos antes de preprocesamiento real train-only; coeficientes guardados antes de controles. Mismo evaluador P55y todas las guardas/celdas/escenarios/NB/broker/historia/familia16, más convergencia obligatoria. Sin árboles, C0, selección de pesos/campos, inferencias2025o envíos. Si falla combinado no se admite; si pasa, transferencia propia con base+GLMsolo2023, sin reutilizar baseP55aprendida en2024. B00/F3c/adversos conservados,2024abierto adaptativo y privada prioritaria. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'P57registered_before_real_GLM_fit_score','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':m.q.post(body,'COD-S2-20261027-PRIVADA-P57-GLM-PREVIO','P57: GLM estándar completo, offset y todas las guardas antes de ajustar')}
    dump(OUT/'registration.json',receipt);dump(INDEX,receipt);print(json.dumps(receipt))


def run():
    v.OUT=OUT;v.PLAN=PLAN;v.INDEX=INDEX;m.OUT=OUT;m.e.OUT=OUT
    v.k=SimpleNamespace(frame_for=frame_for,learn=learn,forward=forward,constant_counts=parameter_counts)
    v.component_level_math=independent_math;v.dump=report_dump;g.TweedieRegressor.fit=observed_fit
    v.run()


def replay():
    assert not (OUT/'replay_report.json').exists();m.check_sources(w.read(PLAN));report=w.read(OUT/'report.json')
    m.OUT=OUT;m.e.OUT=OUT
    def reject(*a,**kw):raise AssertionError('P57replay blocks GLM/base/report learning')
    g.fit=reject;g.TweedieRegressor.fit=reject;m.q.cost_curves=reject
    for outer in range(5):
        for line in m.q.LINES:
            folder=OUT/f'{line}_{outer}';saved=w.read(folder/'committed.json')
            assert all(w.sha(ROOT/p)==vv for p,vv in saved['outputs'].items())
            f=frame_for(line,outer);f.loc[f.is_held,['T0','reserve','baseline_observed','q_paired']]=np.nan
            u,norm=forward(f.loc[f.is_held],w.read(folder/'learning.json'),True)
            assert np.array_equal(u,pd.read_parquet(folder/'prices.parquet').ultimate) and norm==saved['ultimate_normalizers']
    totals,desc,_,_=m.cohort_blocks();weights=np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    draws=np.load(OUT/'cohort_bootstrap.npy');cohort=w.read(OUT/'cohort_report.json')
    assert np.allclose(m.cohort_scores(weights@totals),draws[:4],rtol=2e-12,atol=2e-13)
    for j,z in enumerate(cohort['comparisons']):assert desc[j]['delta']==z['delta'] and np.array_equal(np.quantile(draws[:,j],[.025/16,1-.025/16]),z['family16_band95'])
    draws=np.load(OUT/'POOLED_joint_bootstrap.npy')
    for j,name in enumerate(m.e.NAMES):assert np.array_equal(np.quantile(draws[:,j],[.025,.975]),report['results']['POOLED'][name]['bootstrap95'])
    m.check_sources(w.read(PLAN));dump(OUT/'replay_report.json',{'author':'Codex','utc':utc(),'report_sha256':w.sha(OUT/'report.json'),
        'all15saved_GLM_flows_exact':True,'labels_observed_offset_and_q_not_read_during_ultimate':True,'all_new_learning_blocked':True,
        'saved_intervals_and_first4weights_exact':True,'new_fits':0,'new_resampling':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'replay':'exact','members':15,'new_fits':0,'new_resampling':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    primary=list(OUT.glob('*_*/primary_fit_invoked.json'));adverse=list(OUT.glob('*_*/adverse_fit_invoked.json'))
    assert len(primary)==len(adverse)==15 and len(list(OUT.glob('*_*/primary_model_raw.json')))==len(list(OUT.glob('*_*/adverse_model_raw.json')))==15
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass']
    next_unit=('Prepare OWNconditional-transfer2023target reporting, full P54base and this fixed P56GLM. P55pooled base uses2024target labels and cannot be reused there. Source-only coefficients remain fixed with conditional2024source limit. Register whole cost/config/criteria/forum before any learning; pooled pass alone does not admit a CSV.' if passed else
        'Review NEW P57saved coefficients, convergence and group/cohort loss for a concrete unresolved mechanism before another recipe. Preserve all main effects, failed outcomes and source baselines; do not tune alpha/weights/fields by held or public scores. No repeat old source/scalar/control diagnostics or unchanged curve fits. Goal active, no admitted delivery or missing human authorization.')
    text='# P57: GLM estándar sobre un offset completo\n\nCodex, '+utc()+'. '+('El combinado pasa todas las guardas, incluida convergencia. Falta transferencia propia con base y GLMaprendidos solo en2023.' if passed else 'El combinado no supera las guardas; no se admite para envío y la transferencia queda sin evaluar.')+'\n\n'
    text+=f"ΔD²nominal={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f}; {a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}.\n\n"
    text+='Quince GLMprimarios y15adversos, con coeficientes guardados antes de controles. El control adverso cambió TODOSlos costes/offsets y atributos retenidos antes de la llamada real que aprende categorías, medianas y escalas solo en entrenamiento. La identidad Tweediecon offset, predictor por coeficientes y gradiente se contrastaron con otro cálculo; los15replays son exactos con aprendizaje bloqueado. Se conservaron nivel, escenarios, celdas, cohortes y bandas16sin elegir ramos o hiperparámetros.\n\n'
    text+='Guardas: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'. Transferencia=None. No se recalcularon fuente, baseP55o C0, ni se produjeron precios2025o envíos. Los parámetros GLMson iterativos, no constantes cerradas nuevas.\n\n'
    text+='Los datos son atributos suministrados condicionales, sin acreditar snapshots de cotización. Persisten los límites de reporte, fuente2024y maestros sin fecha, además de la búsqueda adaptativa2023/2024. No se acredita mejora privada ni revisión profesional independiente. B00/F3c y todas las alternativas se conservan.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
        'document':w.rel(DOC),'decision':d['decision'],'nominal':{q:a[q] for q in ['delta','bootstrap95','post31_delta','worst_cell_delta']},
        'all_pooled_gates_pass':passed,'all_GLM_convergence_controls_pass':d['all_GLM_convergence_controls_pass'],'conditional_transfer_gate':None,
        'primary_GLM_fits':15,'adverse_GLM_fits_separate':15,'actual_fit_invocations_total':30,'primary_parameter_counts':d['primary_parameter_counts'],
        'new_source_fits':0,'new_P55_base_fits':0,'new_C0_fits':0,'new_closed_constants':0,'new2025inference':0,'new_submissions':0,
        'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':m.q.post(body,'COD-S2-20261027-PRIVADA-P57-GLM-RESULTADO','P57: resultado del GLM con offset y guardas completas')}
    archive=R/'privado'/('corte_P57_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    count_path=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(count_path);assert 'phase2_private_P57_offset_GLM' not in counts
    w.update(count_path,{'cumulative_price_base_fits':counts['cumulative_price_base_fits']+30,'phase2_private_P57_offset_GLM':receipt},archive)
    w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P57'),(R/'registro/semana2_mision_privada_actual.json','P57')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P57=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P57: GLM con offset, evaluación completa\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+';15GLMprimarios/15adversos reales, replay exacto. Cero fuente/baseP55/C0/inferencias2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_offset_GLM_validation_index':w.rel(INDEX),'week_2_private_offset_GLM_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','run','replay','close']);args=p.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
