"""Evalúa la retirada global de G con componentes P65 intactos y sin ajustar."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p100_component_only_kernel',R/'herramientas/preparar_componentes_sin_G_P99.py')
k=importlib.util.module_from_spec(s);s.loader.exec_module(k)
h=k.h;v=h.v;m=h.m;q=h.q;w=h.w;np=h.np;pd=h.pd;BASE=h.BASE
OUT=BASE/'P100_validacion_componentes_sin_G_20261027'
PLAN=R/'registro/semana2_componentes_sin_G_validacion_plan.json';INDEX=R/'registro/semana2_componentes_sin_G_validacion_actual.json'
DOC=R/'docs/semana2/PRIVADA_P100_VALIDACION_COMPONENTES_SIN_G.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def learn(frame,line):
    outer=int(frame.loc[frame.is_held,'fold'].unique().item());adverse=bool(frame.loc[frame.is_held,'T0'].lt(0).any())
    if adverse:
        frame=frame.copy()
        for name in frame.columns:
            if name not in ['row_id','line','group_id','fold','is_held','year','period_start','period_end']:
                frame[name]=frame[name].astype('object');frame.loc[frame.is_held,name]='INVALID_HELD'
    artifact=k.cached(frame,line,outer);name='adverse' if adverse else 'primary'
    dump(OUT/f'{line}_{outer}'/(name+'_reused_components.json'),{'author':'Codex','utc':utc(),
        'source':w.rel(k.OLD/f'{line}_{outer}/learning.json'),'sha256':w.sha(k.OLD/f'{line}_{outer}/learning.json'),
        'same_training_keys_code_data':True,'components_reused':2,'shared_stages_removed':True,'new_parameters':0})
    return artifact


def final_dump(path,data):
    if path==OUT/'report.json':
        assert len(list(OUT.glob('*_*/learning.json')))==15
        for p in OUT.glob('*_*/learning.json'):
            a=w.read(p);assert a['stages']==[] and a['training_normalizers']=={}
            assert a['components']==w.read(k.OLD/p.parent.name/'learning.json')['components']
        data['reused_primary_parameter_counts']=data.pop('primary_constants')
        data.update(status='P100components_only_no_shared_G_pooled_complete_transfer_unmeasured',
            reused_primary_components=30,reused_adverse_components_separate=30,primary_shared_residual_stages=0,adverse_shared_residual_stages_separate=0,
            new_native_fits=0,new_primary_closed_levels=0,new_source_fits=0,new_CDF_fits=0,
            no_target_batch_normalizers=True,native_convergence_not_applicable=True)
    return dump(path,data)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(k.PLAN);m.check_sources(parent);assert w.read(k.OUT/'completion_receipt.json')['report_sha256']==w.sha(k.OUT/'report.json')
    original=w.read(h.PLAN)
    paths=[Path(__file__),k.PLAN,k.OUT/'report.json',k.OUT/'synthetic.json',k.OUT/'recipe_inventory.json',k.OUT/'completion_receipt.json']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':parent['candidate'],'need':parent['need'],'hypothesis':parent['hypothesis'],
        'one_change':parent['one_change'],'configuration':parent['configuration'],
        **{name:original[name] for name in ['criteria','bootstrap','cohort_guard','level_sensitivity','scenarios']},
        'budget':parent['future_budget'],'staged_decision':parent['future_criterion'],
        'validation':'Same109296historical rows/three lines/five global group folds/2023and2024adaptive; exact current P64row-q and scenario links; all shared G stages omitted symmetrically.',
        'adverse':'Real cache/reuse branch excludes typed-invalid held payload before reading any learning values. Ancestral P65 target-poison equality and pinned train-selection code retained; current synthetic full-component learning also passed all held source/rating/exposure poison. No repeat real parameter estimation is claimed.',
        'integration':'Stored P65 component objects are fit before and independently of G. Omit G globally, apply ultimate component histories/levels and fixed half, then own reporting q for evaluation. All learning and G fit/apply blocked during this new real flow.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'limits':parent['limits'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P100 registra antes de generar precios y puntuar la separación exacta P99: treinta componentes P65 conservados en sus ámbitos y todas las etapas G finales omitidas. Sin nueva calibración, normalizador por lote, fuente, CDF o ajuste nativo. Mismas formas A/E/historial/NCB y niveles/negocio, mezcla50/50, calendario, q P64 y particiones. Todos los ramos y guardas originales globales/cohortes/familia16/cola/reservas/nivel/influencia. Se comprobarán componentes por hash, cache adverso con payload retenido inválido, momentos escalares y replay real bloqueando aprendizaje/G. La exclusión ancestral usa código propio y recibos P65; no se afirma repetir ajuste real bajo veneno completo. Si pasa falta transferencia propia antes del CSV. Sin seleccionar etapas/ramos, pesos o K por el resultado; B00 y adversos conservados,2024abierto adaptativo, cero2025/envíos. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P100registered_before_real_component_only_prices_and_scores','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P100-COMPONENTES-PREVIO','P100: componentes sin correcciones finales, evaluación registrada')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def setup():
    v.OUT=OUT;v.PLAN=PLAN;v.INDEX=INDEX;v.SCENARIO=k.OLD/'scenario_inputs'
    v.k.frame_for=k.frame_for;v.k.learn=learn;v.k.forward=k.forward;v.dump=final_dump
    m.OUT=OUT;m.e.OUT=OUT;m.apply_q=h.apply_row_q
    def reject(*args,**kwargs):raise AssertionError('No real learning or G application in this ablation')
    k.k.core.fit_component=reject;k.k.core.b.shape_fit=reject;k.k.core.b.factor=reject;k.k.core.b.cell_levels=reject
    k.k.g.fit_stage=reject;k.k.g.apply_stage=reject;q.cost_curves=reject;h.t.line_curves=reject


def run():
    setup();m.check_sources(w.read(PLAN));v.run();m.check_sources(w.read(PLAN))


def replay():
    setup();assert not (OUT/'replay_report.json').exists();m.check_sources(w.read(PLAN));report=w.read(OUT/'report.json')
    def reject(*args,**kwargs):raise AssertionError('Replay forbids cache-learning or estimation')
    k.cached=reject
    for outer in range(5):
        for line in q.LINES:
            folder=OUT/f'{line}_{outer}';saved=w.read(folder/'committed.json')
            assert all(w.sha(ROOT/path)==value for path,value in saved['outputs'].items())
            frame=k.frame_for(line,outer);held=frame.loc[frame.is_held].drop(columns=['T0','reserve','q_paired','gender','works_from_home','marketing_segment'],errors='ignore')
            value,norm=k.forward(held,w.read(folder/'learning.json'),True)
            assert np.array_equal(value,pd.read_parquet(folder/'prices.parquet').ultimate) and norm==saved['ultimate_normalizers']=={}
    totals,desc,_,_=m.cohort_blocks();weights=np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    draws=np.load(OUT/'cohort_bootstrap.npy');cohort=w.read(OUT/'cohort_report.json')
    assert np.allclose(m.cohort_scores(weights@totals),draws[:4],rtol=2e-12,atol=2e-13)
    for j,z in enumerate(cohort['comparisons']):assert desc[j]['delta']==z['delta'] and np.array_equal(np.quantile(draws[:,j],[.025/16,1-.025/16]),z['family16_band95'])
    draws=np.load(OUT/'POOLED_joint_bootstrap.npy')
    for j,name in enumerate(m.e.NAMES):assert np.array_equal(np.quantile(draws[:,j],[.025,.975]),report['results']['POOLED'][name]['bootstrap95'])
    m.check_sources(w.read(PLAN));dump(OUT/'replay_report.json',{'author':'Codex','utc':utc(),'report_sha256':w.sha(OUT/'report.json'),
        'all15component_only_flows_exact':True,'ultimate_excludes_target_q_and_removed_G_payload':True,
        'all_learning_and_G_application_blocked':True,'saved_intervals_and_first4weights_exact':True,'new_fits':0,'new_resampling':0,'new_submissions':0})
    print(json.dumps({'replay':'exact','members':15,'new_fits':0,'new_resampling':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();m.check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    assert len(list(OUT.glob('*_*/primary_reused_components.json')))==len(list(OUT.glob('*_*/adverse_reused_components.json')))==15
    old=pd.read_parquet(k.OLD/'POOLED_prices.parquet');new=pd.read_parquet(OUT/'POOLED_prices.parquet')
    assert old.loc[old.line.eq('buildings')].reset_index(drop=True).equals(new.loc[new.line.eq('buildings')].reset_index(drop=True))
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];prior=w.read(k.OLD/'report.json')['results']['POOLED']['NOMINAL']['delta']
    next_unit=('Register own2023 conditional-transfer evaluation of exact component-only algorithm and own reporting before CSV/admission; no pooled2024 report reuse.' if passed else
        'Review only new P100 complete stage-ablation result against P65/P98 from saved reports. Preserve all lines/adverses; do not choose individual G stages or adjust K/weights after this outcome. Next candidate needs a distinct documented observation/valuation/source-allocation mechanism unresolved by the standard component and prior paths, with a finite frozen scope and no public probing.')
    text='# P100: componentes sin etapas compartidas\n\nCodex, '+utc()+'. '+('Pasa el combinado; falta transferencia antes del CSV.' if passed else 'El combinado falla; no se admite un CSV nuevo.')+'\n\n'
    text+=f"Diferencia D² frente a referencia local: {a['delta']:+.7f}; IC95 por grupos [{a['bootstrap95'][0]:+.7f}, {a['bootstrap95'][1]:+.7f}]. Post31: {a['post31_delta']:+.7f}; peor celda: {a['worst_cell_delta']:+.7f}. Diferencia puntual frente a P65 completo: {a['delta']-prior:+.7f}, sin intervalo pareado nuevo.\n\n"
    text+='Treinta componentes propios P65 conservan exactamente sus formas de historial/NCB, normalizadores de entrenamiento y niveles de ramo/negocio. Todas las veinte etapas G posteriores se omiten, sin un nuevo ajuste o campo. Edificios, que no tenía G, conserva exactamente sus filas/precios completos. Se verificaron ámbitos/claves/código/datos, momentos por otra suma y quince replays finales con toda estimación y aplicación de G bloqueadas. El adverso real prueba el camino de reutilización; la exclusión del aprendizaje ancestral se apoya en código/recibos P65 y aprendizaje sintético integral actual, sin inventar nuevos ajustes reales.\n\n'
    text+='Guardas globales: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+='No hay normalizador por lote en el precio nuevo. Las sensibilidades conservan últimos nominales fijos, sin ajuste completo por escenario. Fuente2024 condicional, snapshots sin fecha, reporte/cola/reservas y búsqueda adaptativa siguen limitando generalización. Cero nuevos ajustes nativos/cerrados, fuente/CDF/2025/envíos. B00 y alternativas conservadas,2024abierto adaptativo; sin evidencia de mejora privada o revisión profesional independiente.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{name:a[name] for name in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P100_minus_P65_point_only':a['delta']-prior,
        'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,'reused_primary_components':30,'buildings_pooled_frame_exact_P65':True,
        'new_native_fits':0,'new_primary_closed_levels':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0,'next_unit':next_unit,
        '2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P100-COMPONENTES-RESULTADO','P100: resultado global de retirar las etapas compartidas')}
    cut=R/'privado'/('corte_P100_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));cut.mkdir();w.update(INDEX,receipt,cut)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P100'),(R/'registro/semana2_mision_privada_actual.json','P100')]:w.update(path,{key:receipt,'next_unit':next_unit},cut)
    w.update(R/'registro/semana2_contadores_propios_actual.json',{'phase2_private_P100_component_only':receipt},cut)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P100=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},cut)
    control=R/'registro/semana2_control_entregas_codex_actual.json';c=w.read(control)
    w.update(control,{'allow_new_submission':False,'reason':'P100 pooled pass needs own transfer and exact CSV admission.' if passed else 'P100 component-only algorithm fails unchanged outer guards; no stage/line/K rescue or missing human authorization.',
        'last_evidence_review_utc':receipt['utc'],'latest_rejected_research_alternatives':c['latest_rejected_research_alternatives']+([] if passed else ['P100'])},cut)
    note='\n\n## Privada P100: componentes sin G, evaluación\n\nCodex, '+receipt['utc']+'. Decisión='+receipt['decision']+'; treinta componentes propios reutilizados, quince replays exactos, cero ajustes o envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cut)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_component_only_validation_index':w.rel(INDEX),'week_2_private_component_only_validation_report':w.rel(DOC)},cut)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');a=argparse.ArgumentParser(description=__doc__);a.add_argument('mode',choices=['prepare','run','replay','close'])
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[a.parse_args().mode]()
