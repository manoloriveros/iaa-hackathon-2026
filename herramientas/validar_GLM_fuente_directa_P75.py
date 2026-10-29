"""Evaluación completa de un GLM destino con offset fuente, sin base target."""
from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
import importlib.util
import argparse
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p75_direct_source_offset',R/'herramientas/preparar_GLM_fuente_directa_P74.py')
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
p=r.p;v=p.driver.v;m=r.m;q=r.q;w=r.w;pd=r.pd;np=r.np;BASE=r.BASE
OUT=BASE/'P75_validacion_GLM_fuente_directa_20261027'
PLAN=R/'registro/semana2_GLM_fuente_directa_validacion_plan.json';INDEX=R/'registro/semana2_GLM_fuente_directa_validacion_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P75_VALIDACION_GLM_FUENTE_DIRECTA.md'
ORIGINAL_FIT=r.TweedieRegressor.fit;FIT_PATH=None


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)
def frame_for(line,outer):return r.frame_for(line,outer)


def observed_fit(self,*args,**kwargs):
    assert FIT_PATH is not None and not FIT_PATH.exists()
    dump(FIT_PATH,{'author':'Codex','utc':utc(),'actual_estimator_fit_invoked':True,'parameters':r.PARAMS})
    return ORIGINAL_FIT(self,*args,**kwargs)


def learn(frame,line):
    global FIT_PATH
    outer=int(frame.loc[frame.is_held,'fold'].unique().item());folder=OUT/f'{line}_{outer}'
    adverse=frame.loc[frame.is_held,'T0'].lt(0).any();name='adverse' if adverse else 'primary';FIT_PATH=folder/(name+'_fit_invoked.json')
    return r.fit(r.poison(frame,line) if adverse else frame,line,checkpoint=folder/(name+'_model_raw.json'))


def forward(frame,artifact,ultimate=True):
    assert ultimate;value,relative=r.forward(frame,artifact)
    return value,{'kind':'Single_target_GLM_on_pure_source_annual_T2b_calendar_offset','relative_prediction_digest':m.p.b.digest(relative.tolist())}


def parameter_counts(artifact):return {'iterative_GLM_coefficients':len(artifact['coef']),'iterative_GLM_intercepts':1}


def report_dump(path,d):
    if path==OUT/'report.json':
        artifacts=[w.read(path) for path in OUT.glob('*_*/learning.json')];assert len(artifacts)==15
        convergence=all(not a['warnings'] and a['gradient_inf']<1e-5 for a in artifacts)
        d['pooled_gates']['all_direct_GLM_convergence_pass']=convergence;d['all_pooled_gates_pass']=d['all_pooled_gates_pass'] and convergence
        d['decision']='TRANSFER_REQUIRED_BEFORE_ADMISSION' if d['all_pooled_gates_pass'] else 'REJECT_FROM_POOLED_FAILURE_TRANSFER_UNEVALUATED'
        for key in ['primary_components','adverse_components_separate','primary_shared_residual_stages','adverse_shared_residual_stages_separate']:d.pop(key,None)
        d['primary_iterative_parameter_counts']=d.pop('primary_constants');d['status']='P75single_direct_source_GLM_pooled_complete_transfer_unmeasured'
        d.update(primary_GLM_fits=15,adverse_GLM_fits_separate=15,new_target_base_fits=0,new_source_fits=0,new_CDF_fits=0,new_closed_constants=0,
            target_cost_trained_price_base_ancestors_used=False,source2024conditional=True,all_direct_GLM_convergence_pass=convergence)
    return dump(path,d)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(r.PLAN);m.check_sources(parent);assert w.read(r.OUT/'completion_receipt.json')['report_sha256']==w.sha(r.OUT/'report.json')
    original=w.read(p.PLAN);paths=[Path(__file__),r.PLAN,r.OUT/'report.json',r.OUT/'synthetic.json',r.OUT/'completion_receipt.json',p.PLAN]
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':'Single_target_Tweedie_GLM_source_T2b_offset_A1Ssignal_current_own_reporting',
        'need':parent['need'],'hypothesis':parent['hypothesis'],'configuration':parent['configuration'],'source_contract':parent['source_contract'],'new_ancestry':parent['new_ancestry'],
        **{key:original[key] for key in ['criteria','bootstrap','cohort_guard','level_sensitivity','scenarios']},
        'budget':parent['future_budget'],'adverse':'Actual second sklearnGLMfit with ALLheld cost/source-risk/exposure/qand raw covariates corrupted BEFORE training-only preprocessing/offset construction. Raw coefficient snapshot before controls; primary/adverse model equality.',
        'validation':'Same109296historical rows,3lines/5saved global folds/both2023and2024adaptive;15single target learners. Current P64outertraining reporting and rowFSpPROXYcomposition reused, fixed developed source risks. No targetbase/nestedprice/targetfoldmean; ONEdirectGLMperline would learn from all admitted training data at production.',
        'staged_decision':parent['future_criterion'],'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P75registra antes de ajustar15GLMdestino únicos primarios/15adversos reales: offset T2bfuente anual*calendario*qP64propio, señalA1Sfuente, campos habituales con historia/NCBdirectos, alpha1fijo. Sin precio-base aprendido con costes target, centros por lote, modelosOOFde precio, nuevas fuentes/CDFo búsqueda. Matemática objetivo/gradiente, veneno retenido antes de selector/preproceso real y coeficientes guardados antes de controles; replay final sin ajuste. Mismos109296casos/5folds/globales/celdas/escenarios/nivel/influencia/cohortes/familia16yconvergencia. Pooledfallido impideCSV; si pasa, transferencia propia2023de CDF+GLMantes de producción. B00preservado y2024abierto adaptativo; cero2025/envíos. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P75registered_before_real_direct_GLM_learning','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P75-DIRECTO-PREVIO','P75: GLM destino único, toda la validación antes de ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def setup():
    v.OUT=OUT;v.PLAN=PLAN;v.INDEX=INDEX;m.OUT=OUT;m.e.OUT=OUT;v.SCENARIO=p.t.OUT/'scenario_inputs';m.apply_q=p.t.apply_row_q
    v.k=SimpleNamespace(frame_for=frame_for,learn=learn,forward=forward,constant_counts=parameter_counts);v.component_level_math=r.independent_math;v.dump=report_dump


def run():m.check_sources(w.read(PLAN));setup();r.TweedieRegressor.fit=observed_fit;v.run();m.check_sources(w.read(PLAN))


def replay():
    assert not (OUT/'replay_report.json').exists();m.check_sources(w.read(PLAN));report=w.read(OUT/'report.json');m.OUT=OUT;m.e.OUT=OUT
    def reject(*args,**kwargs):raise AssertionError('P75replay blocks direct GLM/report/source learning')
    r.fit=reject;r.TweedieRegressor.fit=reject;q.cost_curves=reject;p.u.reporting=reject;p.k.learn=reject
    for outer in range(5):
        for line in q.LINES:
            folder=OUT/f'{line}_{outer}';saved=w.read(folder/'committed.json');assert all(w.sha(ROOT/path)==value for path,value in saved['outputs'].items())
            f=frame_for(line,outer);held=f.loc[f.is_held].drop(columns=['T0','reserve','q_paired'])
            value,norm=forward(held,w.read(folder/'learning.json'),True)
            assert np.array_equal(value,pd.read_parquet(folder/'prices.parquet').ultimate) and norm==saved['ultimate_normalizers']
    totals,desc,_,_=m.cohort_blocks();weights=np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    draws=np.load(OUT/'cohort_bootstrap.npy');cohort=w.read(OUT/'cohort_report.json')
    assert np.allclose(m.cohort_scores(weights@totals),draws[:4],rtol=2e-12,atol=2e-13)
    for j,z in enumerate(cohort['comparisons']):assert desc[j]['delta']==z['delta'] and np.array_equal(np.quantile(draws[:,j],[.025/16,1-.025/16]),z['family16_band95'])
    draws=np.load(OUT/'POOLED_joint_bootstrap.npy')
    for j,name in enumerate(m.e.NAMES):assert np.array_equal(np.quantile(draws[:,j],[.025,.975]),report['results']['POOLED'][name]['bootstrap95'])
    m.check_sources(w.read(PLAN));dump(OUT/'replay_report.json',{'author':'Codex','utc':utc(),'report_sha256':w.sha(OUT/'report.json'),'all15direct_GLM_flows_exact':True,
        'ultimate_no_target_q_or_target_base_reads':True,'all_new_learning_blocked':True,'saved_intervals_and_first4weights_exact':True,'new_fits':0,'new_resampling':0,'new_submissions':0})
    print(json.dumps({'replay':'exact','members':15,'new_fits':0,'new_resampling':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();m.check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    assert len(list(OUT.glob('*_*/primary_fit_invoked.json')))==len(list(OUT.glob('*_*/adverse_fit_invoked.json')))==15
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];control=w.read(p.t.OUT/'report.json')['results']['POOLED']['NOMINAL']['delta']
    next_unit=('Register OWN2023-only conditional-transfer direct-source GLMwith own reporting, same signals/fields/alpha1and all gates. No P64pooled2024target-trained qobjects there. Only after full pass may production/exact-file admission be prepared.' if passed else
        'Review NEWP75single-source-offset GLMloss/coefficients and source-signal contributions vs P65reference architecture without new fits/resampling. The target-base-offset miss is no longer its ancestor, so do not blame that missing stage for its loss. No alpha/field/line rescue, source feature leakage fixes by oracle or public probes; identify a new concrete standard mechanism before another recipe.')
    text='# P75: un GLM destino con riesgo fuente, evaluación\n\nCodex, '+utc()+'. '+('El combinado pasa; transferencia propia sigue requerida antes de admitir.' if passed else 'El combinado falla; no se admite CSV y transferencia queda sin evaluar.')+'\n\n'
    text+=f"ΔD²nominal={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f};{a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}. Diferencia puntual frente aP65={a['delta']-control:+.7f}, sin intervalo pareado nuevo.\n\n"
    text+='QuinceGLMprimarios/15adversos reales, un ajuste destino por ramo/fold. No usan ninguna base de precio estimada con costes emergentes: offset T2banual fuente por calendario y qde su entrenamiento, señal A1Srelativa fuente y campos habituales, historia/NCBdirectos. La estimación usa T0íntegro, alpha1yefectos principales fijos; sin búsqueda, targetfoldmean o centros por lote. Todos los costes/señales/offsets/atributos retenidos se alteraron antes del preprocesamiento real; los artefactos coinciden. Objetivo y gradiente por otras sumas; quince replays finales exactos con aprendizaje/remuestreo bloqueados.\n\n'
    text+='Guardas: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+='No se repitieron CDF, modelos fuente o bases, ni se produjeron precios2025/envíos. Las sensibilidades conservan los últimos nominales fijos; no se afirma ajuste completo por escenario. qes un nuisancepropio exterior, la fuente2024/snapshots/historias/clima siguen condicionales y no acreditan disponibilidad de cotización o último identificado. Persisten mercado/cola/reservas y búsqueda adaptativa;2024abierto, B00/F3cyalternativas conservados, sin mejora privada acreditada o revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{key:a[key] for key in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P75_minus_P65_point_only':a['delta']-control,'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,
        'primary_GLM_fits':15,'adverse_GLM_fits_separate':15,'primary_iterative_parameter_counts':d['primary_iterative_parameter_counts'],'target_price_base_ancestors':0,
        'new_target_base_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_closed_constants':0,'new2025inference':0,'new_submissions':0,'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P75-DIRECTO-RESULTADO','P75: resultado completo del GLM destino con riesgo fuente')}
    archive=R/'privado'/('corte_P75_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    cp=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(cp);assert 'phase2_private_P75_direct_source_GLM' not in counts
    w.update(cp,{'cumulative_price_base_fits':counts['cumulative_price_base_fits']+30,'phase2_private_P75_direct_source_GLM':receipt},archive);w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P75'),(R/'registro/semana2_mision_privada_actual.json','P75')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P75=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P75: GLM destino único, evaluación\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+';15GLMprimarios/15adversos, replayexacto, cero nuevos padres/CDF/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_direct_source_GLM_validation_index':w.rel(INDEX),'week_2_private_direct_source_GLM_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['prepare','run','replay','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
