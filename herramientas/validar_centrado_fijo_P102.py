"""Evalúa centros G de último persistidos, con cuarenta constantes propias."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import math
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p102_fixed_centers_kernel',R/'herramientas/preparar_centrado_fijo_P101.py')
k=importlib.util.module_from_spec(s);s.loader.exec_module(k)
h=k.h;v=h.v;m=h.m;q=h.q;w=h.w;np=h.np;pd=h.pd;BASE=h.BASE
OUT=BASE/'P102_validacion_centrado_fijo_20261027'
PLAN=R/'registro/semana2_centrado_fijo_validacion_plan.json';INDEX=R/'registro/semana2_centrado_fijo_validacion_actual.json'
DOC=R/'docs/semana2/PRIVADA_P102_VALIDACION_CENTRADO_FIJO.md'
ORIGINAL_CENTERS=k.centers;CENTER_FOLDER=None;CENTER_BRANCH=None;CENTER_INDEX=0


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def observed_centers(train,ultimate,factor):
    global CENTER_INDEX
    assert CENTER_FOLDER is not None
    value=ORIGINAL_CENTERS(train,ultimate,factor)
    dump(CENTER_FOLDER/f'{CENTER_BRANCH}_center_{CENTER_INDEX}.json',{'author':'Codex','utc':utc(),
        'raw_centers_before_controls':value,'own_training_rows_digest':m.p.b.digest(sorted(train.row_id)),
        'own_training_groups_digest':m.p.b.digest(sorted(set(train.group_id))),
        'input_ultimate_digest':m.p.b.digest(ultimate.tolist()),'input_factor_digest':m.p.b.digest(factor.tolist())})
    CENTER_INDEX+=1
    return value


def learn(frame,line):
    global CENTER_FOLDER,CENTER_BRANCH,CENTER_INDEX
    outer=int(frame.loc[frame.is_held,'fold'].unique().item());adverse=bool(frame.loc[frame.is_held,'T0'].lt(0).any())
    if adverse:
        frame=frame.copy()
        for name in frame.columns:
            if name not in ['row_id','line','group_id','fold','is_held','year','period_start','period_end']:
                frame[name]=frame[name].astype('object');frame.loc[frame.is_held,name]='INVALID_HELD'
    original=k.cached(frame,line,outer);CENTER_FOLDER=OUT/f'{line}_{outer}';CENTER_BRANCH='adverse' if adverse else 'primary';CENTER_INDEX=0
    dump(CENTER_FOLDER/(CENTER_BRANCH+'_reused_P65.json'),{'author':'Codex','utc':utc(),'source':w.rel(k.OLD/f'{line}_{outer}/learning.json'),
        'sha256':w.sha(k.OLD/f'{line}_{outer}/learning.json'),'own_scope_components_and_factors_match':True,
        'new_factor_or_nuisance_estimation':False,'normalizer_conversion_mathematical_invariance_verified_synthetic':True})
    artifact=k.freeze_centers(frame,original)
    assert CENTER_INDEX==len(artifact['stages'])
    dump(CENTER_FOLDER/(CENTER_BRANCH+'_frozen_centers_raw_model.json'),artifact)
    return artifact


def counts(artifact):
    return {'reused_component_shape_factors':sum(sum(len(s['factors']) for s in c['shape']) for c in artifact['components'].values()),
        'reused_component_levels':6,'reused_G_factors':sum(len(s['factors']) for s in artifact['stages']),
        'new_frozen_business_centers':sum(len(s['frozen_ultimate_business_centers']) for s in artifact['stages'])}


def final_dump(path,data):
    if path==OUT/'report.json':
        models=[w.read(p) for p in OUT.glob('*_*/learning.json')];assert len(models)==15
        assert len(list(OUT.glob('*_*/primary_center_*.json')))==len(list(OUT.glob('*_*/adverse_center_*.json')))==20
        for file in OUT.glob('*_*/learning.json'):
            a=w.read(file);old=w.read(k.OLD/file.parent.name/'learning.json')
            assert a['components']==old['components'] and len(a['stages'])==len(old['stages'])
            for stage,previous in zip(a['stages'],old['stages']):assert {name:value for name,value in stage.items() if name!='frozen_ultimate_business_centers'}==previous
        data['parameter_counts']=data.pop('primary_constants')
        data.update(status='P102fixed_training_ultimate_business_centers_pooled_complete_transfer_unmeasured',
            new_native_fits=0,new_G_factor_fits=0,new_primary_closed_levels=40,adverse_closed_levels_separate=40,
            reused_primary_components=30,reused_primary_G_stages=20,new_source_fits=0,new_CDF_fits=0,
            native_convergence_not_applicable=True,application_batch_normalization=False)
    return dump(path,data)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(k.PLAN);m.check_sources(parent);assert w.read(k.OUT/'completion_receipt.json')['report_sha256']==w.sha(k.OUT/'report.json')
    original=w.read(h.PLAN);paths=[Path(__file__),k.PLAN,k.OUT/'report.json',k.OUT/'synthetic.json',k.OUT/'typed_fixture_failure.json',k.OUT/'typed_fixture_repair_registration.json',k.OUT/'completion_receipt.json']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':parent['candidate'],'need':parent['need'],'hypothesis':parent['hypothesis'],
        'one_change':parent['one_change'],'configuration':parent['configuration'],
        **{name:original[name] for name in ['criteria','bootstrap','cohort_guard','level_sensitivity','scenarios']},
        'budget':parent['future_budget'],'staged_decision':parent['future_criterion'],
        'validation':'Same complete five global group folds/three lines/109296historical2023/2024rows, current P64q/scenarios. Learn ONLY own-training ultimate-weighted business centers sequentially; forty parameters, primary and adverse separate.',
        'adverse':'Cached P65 component/factor ancestry preserved with own keys/code/data; current synthetic original whole-learning poison and alternative-chain invariance verified. Real center conversion excludes ALL typed-invalid held payload before any transformation; parameter equality required. No repeated ancestral real fits claimed.',
        'integration':'Raw centers saved immediately after calculation and before scalar/control checks. Original Gfit/apply and all source/report/component fitting blocked. All final inputs use stored centers, including singleton/single-business cohorts.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P102 registra antes de aprender centros/precios o puntuar el algoritmo P101: mismos treinta componentes y veinte factores G propios P65; solo se guardan cuarenta centros de último calculados secuencialmente en entrenamiento por negocio. Cuarenta controles adversos separados; cero nuevo factor/nuisance, nativo, fuente o CDF. La equivalencia de reutilización se comprobó con una cadena alternativa sintética completa. Todos los centros se guardan antes de controles. Mismas guardas globales/cohortes/escenarios/familia16/nivel/influencia, sin rescate por campo/ramo/K/normalización. Replay real sin aprendizaje ni normalización del lote, incluyendo cotización individual y por negocio. Si pasa falta transferencia propia antes de CSV. La posición pública no interviene en parámetros o criterios; B00 y adversos conservados,2024abierto adaptativo, cero2025/envíos. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P102registered_before_real_frozen_center_learning_and_prices','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P102-CENTROS-PREVIO','P102: centros fijos completos, evaluación antes de calcular')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def setup():
    v.OUT=OUT;v.PLAN=PLAN;v.INDEX=INDEX;v.SCENARIO=k.OLD/'scenario_inputs'
    v.k.frame_for=k.frame_for;v.k.learn=learn;v.k.forward=k.forward;v.k.constant_counts=counts;v.dump=final_dump
    m.OUT=OUT;m.e.OUT=OUT;m.apply_q=h.apply_row_q;k.centers=observed_centers
    def reject(*args,**kwargs):raise AssertionError('No new G/component/source/report fitting or batch normalization')
    k.k.core.fit_component=reject;k.k.core.b.shape_fit=reject;k.k.core.b.factor=reject;k.k.core.b.cell_levels=reject
    k.k.g.fit_stage=reject;k.k.g.apply_stage=reject;q.cost_curves=reject;h.t.line_curves=reject


def run():setup();m.check_sources(w.read(PLAN));v.run();m.check_sources(w.read(PLAN))


def replay():
    setup();assert not (OUT/'replay_report.json').exists();m.check_sources(w.read(PLAN));report=w.read(OUT/'report.json')
    def reject(*args,**kwargs):raise AssertionError('Replay forbids center calculation and all learning')
    k.centers=reject;k.cached=reject;k.freeze_centers=reject
    checks=[]
    for outer in range(5):
        for line in q.LINES:
            folder=OUT/f'{line}_{outer}';saved=w.read(folder/'committed.json');assert all(w.sha(ROOT/path)==value for path,value in saved['outputs'].items())
            frame=k.frame_for(line,outer);held=frame.loc[frame.is_held].drop(columns=['T0','reserve','q_paired']);a=w.read(folder/'learning.json')
            value,norm=k.forward(held,a,True);assert np.array_equal(value,pd.read_parquet(folder/'prices.parquet').ultimate) and norm==saved['ultimate_normalizers']
            for j in [0,len(held)//2,len(held)-1]:assert math.isclose(k.forward(held.iloc[[j]],a,True)[0][0],value[j],rel_tol=3e-13)
            for business in [0,1]:
                mask=held.new_business.eq(business).to_numpy();assert np.allclose(k.forward(held.loc[mask],a,True)[0],value[mask],rtol=3e-13,atol=0)
            order=np.arange(len(held))[::-1];assert np.allclose(k.forward(held.iloc[order],a,True)[0],value[order],rtol=3e-13,atol=0)
            checks.append({'line':line,'outer':outer,'full_replay_bit_exact':True,'singleton_business_subsets_and_permutation_rtol3e13':True})
    totals,desc,_,_=m.cohort_blocks();weights=np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    draws=np.load(OUT/'cohort_bootstrap.npy');cohort=w.read(OUT/'cohort_report.json')
    assert np.allclose(m.cohort_scores(weights@totals),draws[:4],rtol=2e-12,atol=2e-13)
    for j,z in enumerate(cohort['comparisons']):assert desc[j]['delta']==z['delta'] and np.array_equal(np.quantile(draws[:,j],[.025/16,1-.025/16]),z['family16_band95'])
    draws=np.load(OUT/'POOLED_joint_bootstrap.npy')
    for j,name in enumerate(m.e.NAMES):assert np.array_equal(np.quantile(draws[:,j],[.025,.975]),report['results']['POOLED'][name]['bootstrap95'])
    m.check_sources(w.read(PLAN));dump(OUT/'replay_report.json',{'author':'Codex','utc':utc(),'report_sha256':w.sha(OUT/'report.json'),'records':checks,
        'all_learning_and_application_batch_normalization_blocked':True,'saved_intervals_and_first4weights_exact':True,'new_fits':0,'new_centers':0,'new_resampling':0,'new_submissions':0})
    print(json.dumps({'replay':'exact','members':15,'actual_historical_singleton_projectivity_pass':True,'new_fits':0,'new_centers':0,'new_resampling':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();m.check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    assert len(list(OUT.glob('*_*/primary_center_*.json')))==len(list(OUT.glob('*_*/adverse_center_*.json')))==20
    old=pd.read_parquet(k.OLD/'POOLED_prices.parquet');new=pd.read_parquet(OUT/'POOLED_prices.parquet')
    assert old.loc[old.line.eq('buildings')].reset_index(drop=True).equals(new.loc[new.line.eq('buildings')].reset_index(drop=True))
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];prior=w.read(k.OLD/'report.json')['results']['POOLED']['NOMINAL']['delta']
    next_unit=('Register own2023 conditional-transfer exact fixed-center algorithm with own reporting before CSV/admission; no borrowed pooled2024 q.' if passed else
        'Review only saved P102center values and all whole cells against P65/P100, without refit/resampling. Projective quoting alone does not solve predictive transport. Preserve all factors/lines/adverses and do not retune centering scope or weights. Next mechanism needs new documented source risk or observation/valuation evidence, not another normalization to public totals.')
    text='# P102: centrado fijo, resultado completo\n\nCodex, '+utc()+'. '+('Pasa el combinado; falta transferencia propia antes del CSV.' if passed else 'El combinado falla; no admite un CSV nuevo.')+'\n\n'
    text+=f"Diferencia D² frente a referencia local: {a['delta']:+.7f}; IC95 por grupos [{a['bootstrap95'][0]:+.7f}, {a['bootstrap95'][1]:+.7f}]. Post31: {a['post31_delta']:+.7f}; peor celda: {a['worst_cell_delta']:+.7f}. Diferencia puntual frente a P65 con normalización por lote: {a['delta']-prior:+.7f}, sin nuevo intervalo pareado.\n\n"
    text+='Se reutilizaron todos los componentes y factores G de sus mismos ámbitos. Solo se calcularon cuarenta centros de entrenamiento por negocio y cuarenta adversos, guardados antes de controles, con exclusión de todo el payload retenido. Modelos primarios/adversos coinciden. La invariancia de factores bajo el nuevo centrado se apoya en la identidad de nuisance por celda y en la cadena alternativa sintética completa, sin inventar nuevos ajustes reales de factores. Edificios sigue exactamente igual a P65.\n\n'
    text+='Pasaron quince replays completos exactos con cálculo de centros/estimación/normalización por lote bloqueados. Cotizaciones individuales, por negocio y permutadas coincidieron dentro de tolerancia3e-13 sobre datos históricos reales; no se produjeron precios2025. Intervalos y primeras ponderaciones se cotejaron sin nuevo remuestreo en replay. Desconocidos conservan factor bruto1 antes del centro fijo; su efecto final no tiene que ser identidad.\n\n'
    text+='Guardas globales: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+='La cotización por fila es una propiedad del algoritmo, no prueba de mejora privada. Fuente2024 condicional, snapshots sin fecha de cotización, reporte/cola/reservas y búsqueda adaptativa siguen limitando la interpretación. Sensibilidades con últimos nominales fijos, sin ajuste completo por escenario. Cero ajustes nativos/factores/fuente/CDF, inferencias2025 o envíos. B00 y todas las alternativas conservadas,2024abierto adaptativo; sin revisión profesional independiente.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{name:a[name] for name in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P102_minus_P65_point_only':a['delta']-prior,
        'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,'new_native_fits':0,'new_G_factor_fits':0,'new_primary_closed_levels':40,'adverse_closed_levels_separate':40,
        'reused_primary_components':30,'reused_primary_G_stages':20,'buildings_pooled_frame_exact_P65':True,'real_historical_singleton_projectivity_pass':True,
        'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0,'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P102-CENTROS-RESULTADO','P102: resultado completo del centrado fijo de entrenamiento')}
    cut=R/'privado'/('corte_P102_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));cut.mkdir();w.update(INDEX,receipt,cut)
    cp=R/'registro/semana2_contadores_propios_actual.json';c=w.read(cp);assert 'phase2_private_P102_fixed_centers' not in c
    w.update(cp,{'cumulative_closed_form_constants':c['cumulative_closed_form_constants']+40,'phase2_private_P102_fixed_centers':receipt},cut)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P102'),(R/'registro/semana2_mision_privada_actual.json','P102')]:w.update(path,{key:receipt,'next_unit':next_unit},cut)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P102=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},cut)
    control=R/'registro/semana2_control_entregas_codex_actual.json';c=w.read(control)
    w.update(control,{'allow_new_submission':False,'reason':'P102 pooled pass requires own transfer and exact CSV admission.' if passed else 'P102 fixed centers fail unchanged outer guards; projectivity is not predictive admission. Preserve quota/alternatives; no missing human authorization.',
        'last_evidence_review_utc':receipt['utc'],'latest_rejected_research_alternatives':c['latest_rejected_research_alternatives']+([] if passed else ['P102'])},cut)
    note='\n\n## Privada P102: centrado fijo, evaluación\n\nCodex, '+receipt['utc']+'. Decisión='+receipt['decision']+'; cuarenta centros propios nuevos/40adversos, cero nuevos factores/nativos/fuente/CDF/envíos. Quince replays y cotizaciones individuales reales pasaron. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cut)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_fixed_center_validation_index':w.rel(INDEX),'week_2_private_fixed_center_validation_report':w.rel(DOC)},cut)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');a=argparse.ArgumentParser(description=__doc__);a.add_argument('mode',choices=['prepare','run','replay','close'])
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[a.parse_args().mode]()
