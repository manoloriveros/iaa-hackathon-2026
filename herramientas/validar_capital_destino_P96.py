"""Evalúa el GLM con capital ordinario y reutiliza ámbitos P88 inalterados."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);a=importlib.util.module_from_spec(s);s.loader.exec_module(a);return a


k=load('p96_capital_main_effect',R/'herramientas/preparar_capital_destino_P95.py')
h=load('p96_unchanged_outer_evaluator',R/'herramientas/validar_GLM_fuente_directa_P75.py')
m=h.m;q=h.q;w=h.w;pd=h.pd;np=h.np;BASE=h.BASE
OUT=BASE/'P96_validacion_capital_destino_20261027'
OLD=BASE/'P88_validacion_prior_calibrado_20261027'
PLAN=R/'registro/semana2_capital_destino_validacion_plan.json'
INDEX=R/'registro/semana2_capital_destino_validacion_actual.json'
DOC=R/'docs/semana2/PRIVADA_P96_VALIDACION_CAPITAL_DESTINO.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def matched_old(frame,line,outer):
    folder=OLD/f'{line}_{outer}';artifact=w.read(folder/'learning.json')
    assert artifact==w.read(folder/'adverse_learning.json')
    train=frame.loc[~frame.is_held]
    assert artifact['fit_row_ids_digest']==m.p.b.digest(sorted(train.row_id))
    assert artifact['fit_groups_digest']==m.p.b.digest(sorted(set(train.group_id)))
    assert artifact['parameters']==k.r.PARAMS and artifact['sklearn_version']==k.r.sklearn.__version__
    sources=w.read(R/'registro/semana2_prior_calibrado_GLM_validacion_plan.json')['sources']
    for path in [Path(k.p.__file__),Path(k.k.__file__),Path(k.r.__file__),k.r.p.t.t.OUT/f'input_{line}_{outer}.parquet']:
        assert sources[w.rel(path)]==w.sha(path)
    assert artifact['prior_level_calibration']['target_learned_parameters']==6
    return artifact


def learn(frame,line):
    outer=int(frame.loc[frame.is_held,'fold'].unique().item())
    adverse=bool(frame.loc[frame.is_held,'T0'].lt(0).any())
    name='adverse' if adverse else 'primary';folder=OUT/f'{line}_{outer}'
    old=matched_old(frame,line,outer)
    dump(folder/(name+'_reused_P88.json'),{'author':'Codex','utc':utc(),'source':w.rel(OLD/f'{line}_{outer}/learning.json'),
        'sha256':w.sha(OLD/f'{line}_{outer}/learning.json'),'same_training_keys_source_code_data_parameters':True,
        'prior_reused':True,'native_model_reused':line=='motor','new_closed_levels':0})
    if line=='motor':
        dump(folder/(name+'_model_raw_levels.json'),old['prior_level_calibration'])
        return old
    h.FIT_PATH=folder/(name+'_fit_invoked.json')
    return k.fit(k.poison(frame,line) if adverse else frame,line,checkpoint=folder/(name+'_model_raw.json'),calibration=old['prior_level_calibration'])


def forward(frame,artifact,ultimate=True):
    assert ultimate
    value,relative=k.forward(frame,artifact)
    return value,{'kind':'Standard_GLM_with_ordinary_capital_and_same_scope_P88_prior',
        'relative_prediction_digest':m.p.b.digest(relative.tolist())}


def final_dump(path,data):
    if path==OUT/'report.json':
        models=[w.read(p) for p in OUT.glob('*_*/learning.json')];assert len(models)==15
        convergence=all(not a['warnings'] and a['gradient_inf']<1e-5 for a in models)
        for file in OUT.glob('*_*/learning.json'):
            a=w.read(file)
            assert a['prior_level_calibration']==w.read(file.parent/'primary_model_raw_levels.json')
            assert a['prior_level_calibration']==w.read(OLD/file.parent.name/'learning.json')['prior_level_calibration']
            if a['line'] in k.UPPER:assert k.FIELD+'__missing' not in a['preprocess']['columns']
        for key in ['primary_components','adverse_components_separate','primary_shared_residual_stages','adverse_shared_residual_stages_separate']:data.pop(key,None)
        data['primary_iterative_parameter_counts']=data.pop('primary_constants')
        data['pooled_gates']['all_direct_GLM_convergence_pass']=convergence
        data['all_pooled_gates_pass']=data['all_pooled_gates_pass'] and convergence
        data.update(status='P96ordinary_capital_main_effect_pooled_complete_transfer_unmeasured',
            decision='TRANSFER_REQUIRED_BEFORE_ADMISSION' if data['all_pooled_gates_pass'] else 'REJECT_FROM_POOLED_FAILURE_TRANSFER_UNEVALUATED',
            primary_GLM_fits=10,adverse_GLM_fits_separate=10,reused_primary_motor_models=5,reused_adverse_motor_models_separate=5,
            reused_primary_closed_levels=90,new_primary_closed_levels=0,new_CDF_fits=0,new_source_fits=0,
            target_learned_offset_levels=True,target_learned_shape_or_rowprice_feature_ancestors=False,
            all_direct_GLM_convergence_pass=convergence)
    return dump(path,data)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(k.PLAN);m.check_sources(parent)
    assert w.read(k.OUT/'completion_receipt.json')['report_sha256']==w.sha(k.OUT/'report.json')
    old_plan=R/'registro/semana2_prior_calibrado_GLM_validacion_plan.json';original=w.read(old_plan);m.check_sources(original)
    paths=[Path(__file__),Path(h.__file__),k.PLAN,k.OUT/'report.json',k.OUT/'synthetic.json',k.OUT/'bindings.json',k.OUT/'completion_receipt.json',old_plan,OLD/'report.json',OLD/'completion_receipt.json']
    paths += [k.OUT/f'capital_{line}.parquet' for line in k.UPPER]
    paths += [OLD/f'{line}_{outer}/{name}.json' for line in q.LINES for outer in range(5) for name in ['learning','adverse_learning']]
    OUT.mkdir()
    plan={'author':'Codex','utc':utc(),'candidate':'Same P88 standard GLM plus ordinary original capital main effect in buildings/contents',
        'need':parent['need'],'hypothesis':parent['hypothesis'],'one_change':parent['one_change'],'configuration':parent['configuration'],
        **{name:original[name] for name in ['criteria','bootstrap','cohort_guard','level_sensitivity','scenarios','validation']},
        'budget':parent['future_budget'],'staged_decision':parent['future_criterion'],
        'adverse':'Second real native GLM fit after ALL held target/source/exposure/q/raw attributes including capital are corrupted before training selection; same-scope cached prior object has already passed original whole held poison.',
        'integration':'Same complete five-fold outer evaluator; native-fit markers and raw coefficients before controls. Reuse 90 exact same-scope source-level parameters and all five unchanged motor models; zero new level estimation, source learning or q estimation.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P96 registra la evaluación completa antes de ajustar. Mismo GLM P88 y prior/exposición/reporte; único cambio: efecto principal del capital ordinario oficial en edificios/contenidos, con filtros F0 e imputación de mediana propia, sin bandera de calidad o prima. Motor idéntico reutilizado por hash. Diez ajustes nativos primarios y diez adversos;90 niveles propios P88 reutilizados por ámbito/claves/código/datos, sin reestimar. Todas las guardas globales, cohortes, reservas/cola, nivel, influencia, familia16 y convergencia permanecen. Si pasa falta transferencia antes del CSV; si falla no se afinan umbrales/alpha/ramos por retenido. Veneno integral con capital, matemática y replay real con todo aprendizaje bloqueado. Sin nueva fuente/CDF/2025/envíos, B00 preservado,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P96registered_before_real_property_GLMfits','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P96-CAPITAL-PREVIO','P96: capital ordinario, evaluación completa antes de ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def setup():
    h.OUT=OUT;h.PLAN=PLAN;h.INDEX=INDEX;h.DOC=DOC;h.frame_for=k.frame_for;h.learn=learn;h.forward=forward;h.dump=final_dump
    h.r.independent_math=k.independent_math
    h.setup()
    def reject(*args,**kwargs):raise AssertionError('P96 reuses levels; no fresh level estimator allowed')
    k.p.calibrate_levels=reject


def run():
    setup();h.r.TweedieRegressor.fit=h.observed_fit
    m.check_sources(w.read(PLAN));h.v.run();m.check_sources(w.read(PLAN))


def replay():
    setup()
    def reject(*args,**kwargs):raise AssertionError('P96 replay forbids all new learning')
    k.p.SCALAR.factor=reject;k.p.SCALAR.cell_levels=reject;k.p.r.p.u.reporting=reject
    h.replay()
    dump(OUT/'level_replay_controls.json',{'author':'Codex','utc':utc(),'report_sha256':w.sha(OUT/'report.json'),
        'all_prior_level_estimators_blocked':True,'all15persisted_models_replayed_exact':True,'new_levels':0,'new_native_fits':0})


def close():
    assert not (OUT/'completion_receipt.json').exists();m.check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.read(OUT/'level_replay_controls.json')['report_sha256']==w.sha(OUT/'report.json')
    assert len(list(OUT.glob('*_*/primary_fit_invoked.json')))==len(list(OUT.glob('*_*/adverse_fit_invoked.json')))==10
    assert len(list(OUT.glob('*_*/primary_reused_P88.json')))==len(list(OUT.glob('*_*/adverse_reused_P88.json')))==15
    assert len(list(OUT.glob('*_*/primary_model_raw_levels.json')))==len(list(OUT.glob('*_*/adverse_model_raw_levels.json')))==15
    old=pd.read_parquet(OLD/'POOLED_prices.parquet');new=pd.read_parquet(OUT/'POOLED_prices.parquet')
    assert old.loc[old.line.eq('motor')].reset_index(drop=True).equals(new.loc[new.line.eq('motor')].reset_index(drop=True))
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];prior=w.read(OLD/'report.json')['results']['POOLED']['NOMINAL']['delta']
    next_unit=('Register own2023 conditional transfer of the exact complete P96 algorithm and own reporting before CSV/admission; no P64 pooled2024 report borrowing.' if passed else
        'Inspect only new P96 property capital coefficients, train support and all saved held cells against P88, without new inference/fit/resampling. Establish whether the added ordinary-capital main effect was too weak, adverse or insufficient across both businesses; no threshold/alpha/line rescue. A next candidate requires a different concrete underwriting/source/observation mechanism, not a public probe.')
    text='# P96: capital ordinario, resultado completo\n\nCodex, '+utc()+'. '+('Pasa el combinado; falta transferencia propia antes de cualquier CSV.' if passed else 'El combinado falla; no se admite un CSV nuevo.')+'\n\n'
    text+=f"Diferencia D² frente a la referencia local: {a['delta']:+.7f}; IC95 por grupos [{a['bootstrap95'][0]:+.7f}, {a['bootstrap95'][1]:+.7f}]. Post31: {a['post31_delta']:+.7f}; peor celda: {a['worst_cell_delta']:+.7f}. Diferencia puntual frente a P88: {a['delta']-prior:+.7f}, sin intervalo pareado nuevo.\n\n"
    text+='Se hicieron diez GLM primarios y diez adversos en edificios/contenidos, con alpha1 y un único efecto principal añadido. Los cinco modelos de autos y los90 parámetros de nivel se reutilizaron en sus mismos ámbitos por claves/código/datos; no se reestimaron. Las filas y precios de autos coinciden exactamente con P88. El veneno integral incluyó el capital retenido antes del preproceso; parámetros iguales y replay de los quince modelos exacto con aprendizaje bloqueado. Pérdida/gradiente por otro cálculo e intervalos guardados cotejados sin nuevo remuestreo durante replay.\n\n'
    text+='Guardas globales: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+='El capital dudoso se imputó con mediana propia sin indicador de calidad en precio; no se leyó prima ni se reparó escala. Filtros históricos, disponibilidad de instantánea, fuentes condicionales, valoración, cola, reservas y búsqueda adaptativa siguen limitando la interpretación. Se conservaron los últimos nominales al sensibilizar escenarios; no se afirma reentrenamiento por escenario. Cero fuente/CDF/2025/envíos. B00 y todas las alternativas conservadas;2024abierto adaptativo. Sin mejora privada acreditada ni revisión profesional independiente.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{name:a[name] for name in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P96_minus_P88_point_only':a['delta']-prior,
        'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,'primary_GLM_fits':10,'adverse_GLM_fits_separate':10,
        'reused_primary_motor_models':5,'reused_primary_closed_levels':90,'new_primary_closed_levels':0,
        'motor_pooled_frame_exact_P88':True,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0,
        'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P96-CAPITAL-RESULTADO','P96: resultado del GLM con capital ordinario')}
    cut=R/'privado'/('corte_P96_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));cut.mkdir()
    cp=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(cp);assert 'phase2_private_P96_ordinary_capital' not in counts
    w.update(cp,{'cumulative_price_base_fits':counts['cumulative_price_base_fits']+20,'phase2_private_P96_ordinary_capital':receipt},cut)
    w.update(INDEX,receipt,cut)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P96'),(R/'registro/semana2_mision_privada_actual.json','P96')]:w.update(path,{key:receipt,'next_unit':next_unit},cut)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P96=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},cut)
    control=R/'registro/semana2_control_entregas_codex_actual.json';old_control=w.read(control)
    w.update(control,{'allow_new_submission':False,'reason':'P96 pooled pass still requires own transfer and exact CSV admission.' if passed else 'P96 ordinary-capital GLM fails unchanged outer guards. Preserve quota and alternatives; no missing human authorization.',
        'last_evidence_review_utc':receipt['utc'],'latest_rejected_research_alternatives':old_control['latest_rejected_research_alternatives']+([] if passed else ['P96'])},cut)
    note='\n\n## Privada P96: capital ordinario, evaluación\n\nCodex, '+receipt['utc']+'. Decisión='+receipt['decision']+'; veinte ajustes nativos nuevos, niveles y autos reutilizados por ámbito; replay exacto. Cero fuente/CDF/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cut)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_direct_capital_validation_index':w.rel(INDEX),'week_2_private_direct_capital_validation_report':w.rel(DOC)},cut)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');a=argparse.ArgumentParser(description=__doc__);a.add_argument('mode',choices=['prepare','run','replay','close'])
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[a.parse_args().mode]()
