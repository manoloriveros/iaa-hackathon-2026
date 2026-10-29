"""Evaluación completa de longitud elegida solo en entrenamiento interno."""
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
k=load('p93_common_length_kernel',R/'herramientas/preparar_selector_rondas_P92.py')
h=load('p93_outer_metric_engine',R/'herramientas/validar_boosting_residual_P72.py')
m=h.m;q=h.q;w=h.w;np=h.np;pd=h.pd;BASE=h.BASE;v=h.v
OUT=BASE/'P93_validacion_selector_rondas_20261027'
PLAN=R/'registro/semana2_selector_rondas_validacion_plan.json';INDEX=R/'registro/semana2_selector_rondas_validacion_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P93_VALIDACION_SELECTOR_RONDAS.md'
OLD=BASE/'P90_validacion_boosting_prior_20261027'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)
def frames_for(outer):return {line:k.rating.frame_for(line,outer) for line in q.LINES}


def tables_for(outer):
    outputs=w.read(k.scopes.OUT/'bindings.json')['outputs'];tables={member:{} for member in range(5)}
    for member in range(5):
        for line in q.LINES:
            path=k.scopes.OUT/'inputs'/f'o{outer}_i{member}_{line}.parquet';assert w.sha(path)==outputs[w.rel(path)];tables[member][line]=pd.read_parquet(path)
    return tables


def matched_old(frame,line,outer):
    folder=OLD/f'{line}_{outer}';a=w.read(folder/'learning.json');assert a==w.read(folder/'adverse_learning.json')
    train=frame.loc[~frame.is_held];assert a['fit_row_ids_digest']==m.p.b.digest(sorted(train.row_id)) and a['fit_groups_digest']==m.p.b.digest(sorted(set(train.group_id)))
    source=w.read(R/'registro/semana2_boosting_prior_validacion_plan.json')['sources']
    for path in [Path(k.k.__file__),Path(k.prior.__file__),Path(k.rating.__file__),Path(k.k.t.__file__),k.rating.r.p.t.t.OUT/f'input_{line}_{outer}.parquet']:
        assert source[w.rel(path)]==w.sha(path)
    assert a['parameters']==k.PARAMS and a['lightgbm_version']==k.lgb.__version__ and a['configured_rounds']==64
    return a


def final_model(frame,line,selection,folder,outer=None,adverse=False):
    assert outer is not None;old=matched_old(frame,line,outer);folder.mkdir(parents=True,exist_ok=True)
    receipt=folder/'reused_prior.json'
    if not receipt.exists():dump(receipt,{'author':'Codex','utc':utc(),'source':w.rel(OLD/f'{line}_{outer}/learning.json'),'sha256':w.sha(OLD/f'{line}_{outer}/learning.json'),
        'same_training_keys_code_data_params':True,'old_adverse_exact':True,'closed_levels_reused':6})
    if selection['rounds']==64:
        path=folder/'reused_exact64.json'
        if not path.exists():dump(path,{'author':'Codex','utc':utc(),'source':w.rel(OLD/f'{line}_{outer}/learning.json'),'sha256':w.sha(OLD/f'{line}_{outer}/learning.json'),'new_native_fits':0})
        return old
    maximum=k.fit_max(frame,line,folder,calibration=old['prior_level_calibration']);prefix=maximum['models']['64']
    assert prefix['preprocess']==old['preprocess'] and prefix['prior_level_calibration']==old['prior_level_calibration']
    left=k.lgb.Booster(model_str=prefix['model_string']);right=k.lgb.Booster(model_str=old['model_string'])
    assert left.dump_model()['tree_info']==right.dump_model()['tree_info'],'Maximum-fit prefix must reproduce original64structure without held scoring'
    return maximum['models'][str(selection['rounds'])]


def produce_bundle(outer,adverse):
    frames=frames_for(outer)
    if adverse:frames={line:k.rating.poison(f,line) for line,f in frames.items()}
    folder=OUT/f'outer{outer}';name='adverse_bundle' if adverse else 'primary_bundle'
    def produce():
        fits=folder/('adverse_fits' if adverse else 'primary_fits');bundle=k.train_bundle(frames,tables_for(outer),fits,outer,adverse)
        bundle['actual_new_nativefits']=len(list(fits.rglob('actual_fit_invoked.json')))
        bundle['reused_final64']=len(list(fits.rglob('reused_exact64.json')))
        bundle['new_closed_levels']=sum(w.read(p)['new_closed_levels'] for p in fits.rglob('maximum.json'))
        assert 75//5<=bundle['actual_new_nativefits']<=18 and bundle['new_closed_levels']==90
        print(json.dumps({'outer':outer,'adverse':adverse,'selected_rounds':bundle['selection']['rounds'],'native_maxfits':bundle['actual_new_nativefits'],'new_inner_levels':bundle['new_closed_levels'],'reused_final64':bundle['reused_final64']}),flush=True)
        return bundle
    return m.once(folder,name,produce)


def learn(frame,line):
    outer=int(frame.loc[frame.is_held,'fold'].unique().item());adverse=bool(frame.loc[frame.is_held,'T0'].lt(0).any())
    bundle=produce_bundle(outer,adverse);model=dict(bundle['models'][line]);model['common_inner_length_selection']=bundle['selection'];return model


def forward(frame,artifact,ultimate=True):
    assert ultimate;value,_=k.k.forward(frame,artifact)
    return value,{'kind':'Common_inner_selected_tree_length_no_batchnormalizer','rounds':artifact['configured_rounds']}


def report_dump(path,data):
    if path==OUT/'report.json':
        bundles=[w.read(OUT/f'outer{outer}/primary_bundle.json') for outer in range(5)]
        adverse=[w.read(OUT/f'outer{outer}/adverse_bundle.json') for outer in range(5)];assert bundles==adverse
        models=[a for bundle in bundles for a in bundle['models'].values()]
        integrity=all(bundle['all_inner_prefix_integrity_pass'] for bundle in bundles) and all(a['native_offset_metric_scalar_match'] and a['leaf_sum_and_serialization_exact'] for a in models)
        data['pooled_gates']['all_inner_final_prefix_offset_integrity_pass']=integrity;data['all_pooled_gates_pass']=data['all_pooled_gates_pass'] and integrity
        data['decision']='TRANSFER_REQUIRED_BEFORE_ADMISSION' if data['all_pooled_gates_pass'] else 'REJECT_FROM_POOLED_FAILURE_TRANSFER_UNEVALUATED'
        for name in ['primary_components','adverse_components_separate','primary_shared_residual_stages','adverse_shared_residual_stages_separate']:data.pop(name,None)
        data['primary_final_iterative_leaf_counts']=data.pop('primary_constants');data['primary_whole_learners']=5;data['adverse_whole_learners_separate']=5
        data.update(status='P93common_inner_selected_length_pooled_complete_transfer_unmeasured',
            primary_selections=[{'outer':j,**bundle['selection']} for j,bundle in enumerate(bundles)],
            actual_new_primary_nativefits=sum(a['actual_new_nativefits'] for a in bundles),actual_new_adverse_nativefits_separate=sum(a['actual_new_nativefits'] for a in adverse),
            reused_primary_final64=sum(a['reused_final64'] for a in bundles),reused_adverse_final64_separate=sum(a['reused_final64'] for a in adverse),
            new_primary_closed_levels=sum(a['new_closed_levels'] for a in bundles),adverse_closed_levels_separate=sum(a['new_closed_levels'] for a in adverse),
            new_source_fits=0,new_CDF_fits=0,new2025inference=0,new_submissions=0,GLM_stationarity_gate_not_applicable=True)
    return dump(path,data)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(k.PLAN);k.check_sources(parent);assert w.read(k.OUT/'completion_receipt.json')['report_sha256']==w.sha(k.OUT/'report.json')
    original_path=R/'registro/semana2_boosting_prior_validacion_plan.json';original=w.read(original_path);m.check_sources(original)
    paths=[Path(__file__),Path(h.__file__),k.PLAN,k.OUT/'report.json',k.OUT/'synthetic.json',k.OUT/'bindings.json',k.OUT/'completion_receipt.json',original_path,OLD/'report.json',OLD/'completion_receipt.json']
    for line in q.LINES:
        for outer in range(5):paths += [OLD/f'{line}_{outer}/learning.json',OLD/f'{line}_{outer}/adverse_learning.json']
    outputs=w.read(k.scopes.OUT/'bindings.json')['outputs']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':'P90same_model_prior_fields_with_FULLtrainingonly_commonlength_selector',
        'need':parent['need'],'hypothesis':parent['hypothesis'],'configuration':parent['configuration'],'budget':parent['future_budget'],
        **{name:original[name] for name in ['criteria','bootstrap','cohort_guard','level_sensitivity','scenarios']},
        'integration':'Five complete outer algorithms each learn a common length from45inner prefix objectives, with75inner maxfits overall. Per-line wrappers are not independent selection algorithms. Each innerprior/preprocess owns only its train; P84qscope tables fixed bySHA. Final P90prior always reused at exact same scope; final64model reused if chosen64, otherwise max256fit and prefix64structure verified against original without outer scoring.',
        'adverse':'Actual second complete selector/native prior tree flow after all outerheld payload corrupted before inner extraction. Primary/adverse inner artifact hashes and finalmodels must match. External own-scope prior caches retain original real adverse proof; no novel report learning claim.',
        'staged_decision':parent['future_criterion'],'runtime_sources':parent['runtime_sources'],
        'sources':{**parent['sources'],**outputs,**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P93 registra ANTESdeajustar algoritmo completoP92: longitud[64,128,256]común a3ramos elegida SOLOen5folds internos, empate a menor, mismos campos/prior/paso/depth.75+75máximos internos256 y hasta15+15finales nativos nuevos;450+450niveles internos propios, niveles exterioresP90reutilizados en su ámbito y modelos64exactos reutilizados si se elige64. Cada prefijo usa el mismo ajuste/propio preproceso, no q/niveles exteriores en selección. Cinco selectores completos exteriores, veneno real integral, modelos/hashes exactos, replay225objetivos y15finales sin ajustar. Todas las guardas globales/cohortes/escenarios/familia16/nivel/influencia e integridadnativa, más transferencia propia si pasa combinado. Sin refinargrid/campos/ramo, fuente/CDF/2025/envíos. B00/adversos conservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P93registered_before_real_commonlength_whole_learning','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P93-RONDAS-PREVIO','P93: selector interno completo de longitud, guardas antes de ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def setup():
    h.OUT=OUT;h.PLAN=PLAN;h.INDEX=INDEX;h.setup();k.final_model=final_model
    v.k=SimpleNamespace(frame_for=k.rating.frame_for,learn=learn,forward=forward,constant_counts=h.parameter_counts)
    v.component_level_math=k.k.independent_math;v.dump=report_dump


def run():k.check_sources(w.read(PLAN));setup();v.run();k.check_sources(w.read(PLAN))


def replay():
    assert not (OUT/'replay_report.json').exists();plan=w.read(PLAN);k.check_sources(plan);report=w.read(OUT/'report.json');m.OUT=OUT;m.e.OUT=OUT
    def reject(*args,**kwargs):raise AssertionError('P93replay blocks ALLnew maximumfits, priors, sources and reports')
    k.fit_max=reject;k.ORIGINAL_TRAIN=reject;k.lgb.train=reject;k.prior.calibrate_levels=reject;k.prior.SCALAR.factor=reject;k.prior.SCALAR.cell_levels=reject;q.cost_curves=reject
    for outer in range(5):
        frames=frames_for(outer)
        for f in frames.values():f.loc[f.is_held,['T0','reserve','q_paired']]=np.nan
        bundle=w.read(OUT/f'outer{outer}/primary_bundle.json');values=k.replay_bundle(frames,tables_for(outer),bundle,OUT/f'outer{outer}/primary_fits')
        for line in q.LINES:
            folder=OUT/f'{line}_{outer}';saved=w.read(folder/'committed.json');assert all(w.sha(ROOT/path)==value for path,value in saved['outputs'].items())
            assert np.array_equal(values[line],pd.read_parquet(folder/'prices.parquet').ultimate)
            assert saved['ultimate_normalizers']=={'kind':'Common_inner_selected_tree_length_no_batchnormalizer','rounds':bundle['selection']['rounds']}
    totals,desc,_,_=m.cohort_blocks();weights=np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    draws=np.load(OUT/'cohort_bootstrap.npy');cohort=w.read(OUT/'cohort_report.json')
    assert np.allclose(m.cohort_scores(weights@totals),draws[:4],rtol=2e-12,atol=2e-13)
    for j,z in enumerate(cohort['comparisons']):assert desc[j]['delta']==z['delta'] and np.array_equal(np.quantile(draws[:,j],[.025/16,1-.025/16]),z['family16_band95'])
    draws=np.load(OUT/'POOLED_joint_bootstrap.npy')
    for j,name in enumerate(m.e.NAMES):assert np.array_equal(np.quantile(draws[:,j],[.025,.975]),report['results']['POOLED'][name]['bootstrap95'])
    k.check_sources(plan);dump(OUT/'replay_report.json',{'author':'Codex','utc':utc(),'report_sha256':w.sha(OUT/'report.json'),'all5selectors225inner_objectives_exact':True,
        'all15selected_final_predictions_exact':True,'all_new_learning_blocked':True,'saved_intervals_and_first4weights_exact':True,'new_fits':0,'new_resampling':0,'new_submissions':0})
    print(json.dumps({'replay':'exact','whole_selectors':5,'inner_objectives':225,'final_models':15,'new_fits':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();k.check_sources(w.read(PLAN));d=w.read(OUT/'report.json');assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    number=d['actual_new_primary_nativefits']+d['actual_new_adverse_nativefits_separate'];assert number==len(list(OUT.glob('outer*/*_fits/**/actual_fit_invoked.json')))
    assert d['new_primary_closed_levels']==d['adverse_closed_levels_separate']==450
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];prior_delta=w.read(OLD/'report.json')['results']['POOLED']['NOMINAL']['delta']
    next_unit=('Register OWN2023-only conditionaltransfer for EXACTP93whole commonlength selector with own inner/outerreporting and priors before any production/admission. No pooled2024learned ancestors there.' if passed else
        'Review ONLYNEWP93saved inner selection margins and whole held cells against fixedP90/P88/P65without refit/resampling. No round-grid extension, depth/step/field or perline rescue from outer/public outcomes. Need distinct documented source/target/observation mechanism before another candidate; preserve quota/all alternatives.')
    text='# P93: selección interna de longitud, evaluación completa\n\nCodex, '+utc()+'. '+('El combinado pasa; falta transferencia propia antes de un CSV.' if passed else 'El combinado falla; no se admite CSV y la transferencia permanece sin evaluar.')+'\n\n'
    text+=f"ΔD²frente a referencia={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f};{a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}. P93menosP90={a['delta']-prior_delta:+.7f}, punto sin nuevo intervalo pareado.\n\n"
    text+='Cada uno de cinco algoritmos exteriores eligió una longitud común por los45objetivos internos propios. Misma familia/campos/profundidad/paso/prior; un máximo256por ámbito genera los tres prefijos. Cada prior/preproceso interno excluye su retenido; no se usó el qexterior para seleccionar. Guardas: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+=f"Nuevos ajustes nativos: primarios={d['actual_new_primary_nativefits']}, adversos={d['actual_new_adverse_nativefits_separate']}.450+450niveles internos nuevos;90+90niveles exteriores reutilizados. Finales64exactos reutilizados={d['reused_primary_final64']}+{d['reused_adverse_final64_separate']}. Toda selección/modelos coincidió bajo veneno exterior real. Replayde225objetivos/cinco selectores/15finales exacto sin ajustar; intervalos/multiplicidades/sumas guardados cotejados sin remuestreo adicional.\n\n"
    text+='| Fold exterior | Rondas elegidas solo en entrenamiento |\n|---|---:|\n'
    for z in d['primary_selections']:text+=f"|{z['outer']}|{z['rounds']}|\n"
    text+='\nSin nuevas fuentes/CDF/precios2025/envíos o refinamiento delgrid. Escenarios con últimos nominales fijos, sin reestimar todas las etapas por escenario. Datos fuente/snapshots/observación/cola/reservas y búsqueda adaptativa condicionan transporte; no mejora privada acreditada o revisión independiente. B00/F3cyadversos conservados;2024abierto adaptativo.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{name:a[name] for name in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P93_minus_P90_point_only':a['delta']-prior_delta,'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,
        'actual_new_primary_nativefits':d['actual_new_primary_nativefits'],'actual_new_adverse_nativefits_separate':d['actual_new_adverse_nativefits_separate'],'native_fits_added_to_counter':number,
        'new_primary_closed_levels':450,'adverse_closed_levels_separate':450,'primary_selected_lengths':[z['rounds'] for z in d['primary_selections']],
        'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0,'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P93-RONDAS-RESULTADO','P93: resultado completo del selector interno de longitud')}
    archive=R/'privado'/('corte_P93_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();cp=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(cp);assert 'phase2_private_P93_length_selector' not in counts
    w.update(cp,{'cumulative_price_base_fits':counts['cumulative_price_base_fits']+number,'cumulative_closed_form_constants':counts['cumulative_closed_form_constants']+450,'phase2_private_P93_length_selector':receipt},archive);w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P93'),(R/'registro/semana2_mision_privada_actual.json','P93')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P93=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    control=R/'registro/semana2_control_entregas_codex_actual.json';old=w.read(control)
    w.update(control,{'allow_new_submission':False,'reason':'P93pooledpass still needs own conditionaltransfer before exactCSVadmission.' if passed else 'P93training-only selected length fails unchanged outer admission guards. No grid/depth/field/line rescue or missing human authorization; preserve quota/alternatives.',
        'last_evidence_review_utc':receipt['utc'],'latest_rejected_research_alternatives':old['latest_rejected_research_alternatives']+([] if passed else ['P93'])},archive)
    note='\n\n## Privada P93: selector de longitud, validación\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+f';{number}fitsnativos nuevos/450niveles primarios, replayexacto de cinco selectores y15finales; cero fuente/CDF/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_length_selector_validation_index':w.rel(INDEX),'week_2_private_length_selector_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['prepare','run','replay','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
