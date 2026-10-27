"""Cinco selectores completos de mezcla, con guardián previo de paridad 50/50."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p105_complete_mix_selector',R/'herramientas/preparar_selector_mezcla_P104.py')
k=importlib.util.module_from_spec(s);s.loader.exec_module(k)
p=k.p;h=p.p.h;v=h.v;m=k.m;q=k.q;w=k.w;pd=k.pd;np=k.np;BASE=k.BASE
OUT=BASE/'P105_validacion_selector_mezcla_20261027'
PLAN=R/'registro/semana2_selector_mezcla_validacion_plan.json';INDEX=R/'registro/semana2_selector_mezcla_validacion_actual.json'
DOC=R/'docs/semana2/PRIVADA_P105_VALIDACION_SELECTOR_MEZCLA.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)
def frames_for(outer):return {line:p.p.frame_for(line,outer) for line in q.LINES}


def tables_for(outer):
    binding=w.read(p.scopes.OUT/'bindings.json');tables={member:{} for member in range(5)}
    for member in range(5):
        for line in q.LINES:
            path=p.scopes.OUT/f'inputs/o{outer}_i{member}_{line}.parquet'
            assert binding['outputs'][w.rel(path)]==w.sha(path);tables[member][line]=pd.read_parquet(path)
    return tables


def bases_for(outer):
    records={z['source']:z['sha256'] for z in w.read(p.OUT/'report.json')['records']}
    inner={member:{} for member in range(5)};full={}
    for line in q.LINES:
        path=p.p.OLD/f'{line}_{outer}/learning.json';assert records[w.rel(path)]==w.sha(path);full[line]=w.read(path)
        for member in range(5):
            path=p.INNER/f'outer{outer}/inner{member}/{line}/base_primary.json'
            assert records[w.rel(path)]==w.sha(path);inner[member][line]=w.read(path)
    return inner,full


def half_parity():
    receipt=OUT/'half_parity.json'
    if receipt.exists():
        saved=w.read(receipt);assert saved['all90_price_and_norm_parity_bit_exact']
        for path,sha in saved['source_outputs'].items():assert w.sha(ROOT/path)==sha
        return
    assert not list(OUT.glob('outer*/primary_fits')), 'Parity must precede any new G fitting'
    records=[];sources={}
    for outer in range(5):
        frames=frames_for(outer);tables=tables_for(outer);inner,full=bases_for(outer)
        old_inner={}
        for line in q.LINES:
            file=p.INNER/f'input_{line}_{outer}.parquet'
            old_inner[line]=pd.read_parquet(file,columns=['row_id','crossfit_member','baseline_ultimate']).set_index('row_id');sources[w.rel(file)]=w.sha(file)
            folder=p.p.OLD/f'{line}_{outer}';saved=w.read(folder/'committed.json');f=frames[line].loc[frames[line].is_held]
            value,norm=k.forward(f,full[line],True);expected=pd.read_parquet(folder/'prices.parquet').set_index('row_id').loc[f.row_id]
            assert np.array_equal(value,expected.ultimate.to_numpy()) and norm==saved['ultimate_normalizers']
            for file in [folder/'prices.parquet',folder/'committed.json']:sources[w.rel(file)]=w.sha(file)
            records.append({'kind':'outer','outer':outer,'line':line,'rows':len(f),'price_and_norm_bit_exact':True})
        for member in range(5):
            scoped=k.scopes.inner_frames(frames,tables[member])
            for line,f in scoped.items():
                held=f.loc[f.is_held];expected=old_inner[line].loc[held.row_id]
                assert expected.crossfit_member.eq(member).all()
                value,norm=k.forward(held,inner[member][line],True)
                commit=p.INNER/f'outer{outer}/inner{member}/{line}/committed.json';saved=w.read(commit)
                assert np.array_equal(value,expected.baseline_ultimate.to_numpy()) and norm==saved['record']['ultimate_normalizers']
                sources[w.rel(commit)]=w.sha(commit)
                records.append({'kind':'inner','outer':outer,'member':member,'line':line,'rows':len(held),'price_and_norm_bit_exact':True})
    assert len(records)==90
    dump(receipt,{'author':'Codex','utc':utc(),'all90_price_and_norm_parity_bit_exact':True,'records':records,'source_outputs':sources,
        'new_Gfits':0,'new_components':0,'new_scores':0,'new_CDF_fits':0})
    print(json.dumps({'half_guard_pass':True,'all90_price_and_norms':'bit_exact','new_Gfits_before_guard':0}),flush=True)


def produce_bundle(outer,adverse):
    assert w.read(OUT/'half_parity.json')['all90_price_and_norm_parity_bit_exact']
    frames=frames_for(outer)
    if adverse:frames={line:k.poison(frame) for line,frame in frames.items()}
    inner,full=bases_for(outer);folder=OUT/f'outer{outer}';name='adverse_bundle' if adverse else 'primary_bundle'
    def produce():
        result=k.train_bundle(frames,tables_for(outer),inner,full,folder/('adverse_fits' if adverse else 'primary_fits'),adverse)
        assert 80<=result['actual_Gfit_calls']<=84
        print(json.dumps({'outer':outer,'adverse':adverse,'selected_weight':result['selection']['weight'],
            'new_Gstage_calls':result['actual_Gfit_calls'],'new_closed_constants':result['new_closed_constants_including_train_prediction_normalizers']}),flush=True)
        return result
    result=m.once(folder,name,produce);commit=folder/(name+'_committed.json');path=folder/(name+'.json')
    if commit.exists():assert w.read(commit)['bundle_sha256']==w.sha(path)
    else:dump(commit,{'author':'Codex','utc':utc(),'bundle':w.rel(path),'bundle_sha256':w.sha(path)})
    return result


def learn(frame,line):
    outer=int(frame.loc[frame.is_held,'fold'].unique().item());adverse=bool(frame.loc[frame.is_held,'T0'].lt(0).any())
    bundle=produce_bundle(outer,adverse);model=dict(bundle['models'][line]);model['common_inner_weight_selection']=bundle['selection']
    assert model.get('mix_weight',.5)==bundle['selection']['weight'];return model


def counts(artifact):
    return {'final_component_shape_factors':sum(sum(len(s['factors']) for s in c['shape']) for c in artifact['components'].values()),
        'final_component_levels':6,'final_Gfactors':sum(len(s['factors']) for s in artifact['stages']),
        'final_Gnuisance':sum(len(s['nuisance_year_business']) for s in artifact['stages'])}


def final_dump(path,data):
    if path==OUT/'report.json':
        primary=[w.read(OUT/f'outer{i}/primary_bundle.json') for i in range(5)]
        adverse=[w.read(OUT/f'outer{i}/adverse_bundle.json') for i in range(5)];assert primary==adverse
        calls=sum(b['actual_Gfit_calls'] for b in primary)
        constants=sum(b['new_closed_constants_including_train_prediction_normalizers'] for b in primary)
        assert 400<=calls<=420 and constants<=5250
        data['final_parameter_counts']=data.pop('primary_constants')
        data.update(status='P105complete_common_source_mix_selection_pooled_transfer_unmeasured',
            primary_whole_learners=5,adverse_whole_learners_separate=5,primary_final_models=15,
            primary_components=0,adverse_components_separate=0,reused_distinct_component_objects=180,
            primary_shared_residual_stages=calls,adverse_shared_residual_stages_separate=calls,
            new_primary_closed_constants=constants,adverse_closed_constants_separate=constants,
            selected_weights=[b['selection']['weight'] for b in primary],all5whole_selector_poison_exact=True,
            new_native_fits=0,new_component_fits=0,new_source_fits=0,new_CDF_fits=0)
    return dump(path,data)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(k.PLAN);m.check_sources(parent);assert w.read(k.OUT/'completion_receipt.json')['report_sha256']==w.sha(k.OUT/'report.json')
    original=w.read(h.PLAN);paths=[Path(__file__),k.PLAN,k.OUT/'report.json',k.OUT/'synthetic.json',k.OUT/'completion_receipt.json']
    for outer in range(5):
        for line in q.LINES:
            paths += [p.INNER/f'input_{line}_{outer}.parquet',p.p.OLD/f'{line}_{outer}/committed.json',p.p.OLD/f'{line}_{outer}/prices.parquet']
            paths += [p.INNER/f'outer{outer}/inner{member}/{line}/committed.json' for member in range(5)]
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':'Complete P104 training-only common source-weight selector with own G per nonhalf mix',
        'need':parent['need'],'hypothesis':parent['hypothesis'],'configuration':parent['configuration'],
        **{name:original[name] for name in ['criteria','bootstrap','cohort_guard','level_sensitivity','scenarios']},
        'budget':parent['future_budget'],'staged_decision':parent['future_criterion'],'real_first_gate':parent['real_first_gate'],
        'validation':'Five whole common-weight selectors over all3lines/5saved inner folds, then15final line models; same109296historical2023/2024rows and5global outer folds. No source weight is selected from outer/public outcomes.',
        'integration':'Reuse P103verified75inner/15outer caches and protected P84qtables by SHA. Exact half price/norm parity before ANYreal nonhalf Gfit. All new Gstages/checkpoints owntrain only; raw factors saved before applications/controls; no new CDF/source/component/native fitting.',
        'adverse':'ALLouter held payload poisoned before inner filtering and selection. ALLinnerheld payload poisoned for each fresh Glearner, then clean innerheld labels used legitimately to select weight. Replayed objectives use identical clean quoting payload; no claim prices ignore their covariates.',
        'counters':parent['counters'],'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P105 registra la evaluación real completa del selector P104antes de ajustar/puntuar. Primer guardián: reproducir exactamente precios/normas50/50en75ámbitos internos y15exteriores; si falla no hay nuevos ajustes G. Después cinco selectores completos con un peso común a tres ramos, elegido por las75pérdidas internas originales de cada selector entre cinco pesos fijos. Componentes y qpropios reutilizados; Gse aprende para cada peso no50/50, hasta400+20etapas primarias y otras tantas adversas, cero nativos/componentes/CDF/fuentes. Veneno exterior e interior, todos los375objetivos y finales en replay con aprendizaje bloqueado. Mismas guardas globales/cohortes/escenarios/familia16/nivel/influencia; si pasa falta transferencia propia antes deCSV. Sin ampliar cuadrícula, elegir por ramo o tabla pública, sin2025/envíos. B00 preservado,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P105registered_before_real_weight_selection_and_Glearning','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P105-MEZCLA-PREVIO','P105: evaluación de cinco selectores completos, guardas intactas')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def setup():
    v.OUT=OUT;v.PLAN=PLAN;v.INDEX=INDEX;v.SCENARIO=p.p.OLD/'scenario_inputs'
    v.k.frame_for=lambda line,outer:p.p.frame_for(line,outer);v.k.learn=learn;v.k.forward=k.forward;v.k.constant_counts=counts;v.dump=final_dump
    m.OUT=OUT;m.e.OUT=OUT;m.apply_q=h.apply_row_q
    def reject(*args,**kwargs):raise AssertionError('No component/report/source learning in weight selection')
    k.base.core.fit_component=reject;k.base.core.b.shape_fit=reject;k.base.core.b.factor=reject;k.base.core.b.cell_levels=reject;q.cost_curves=reject;h.t.line_curves=reject


def run():
    setup();m.check_sources(w.read(PLAN));half_parity();v.run();m.check_sources(w.read(PLAN))


def replay():
    setup();assert not (OUT/'replay_report.json').exists();m.check_sources(w.read(PLAN));report=w.read(OUT/'report.json')
    def reject(*args,**kwargs):raise AssertionError('Replay blocks all component/G/report and selector learning')
    k.fit_weight=reject;k.train_bundle=reject;k.base.g.fit_stage=reject
    for outer in range(5):
        frames=frames_for(outer);tables=tables_for(outer);folder=OUT/f'outer{outer}'
        primary=w.read(folder/'primary_bundle.json');adverse=w.read(folder/'adverse_bundle.json');assert primary==adverse
        for name in ['primary_bundle','adverse_bundle']:assert w.read(folder/(name+'_committed.json'))['bundle_sha256']==w.sha(folder/(name+'.json'))
        one=k.replay_bundle(frames,tables,primary,folder/'primary_fits')
        bad={line:k.poison(frame) for line,frame in frames.items()}
        two=k.replay_bundle(bad,tables,adverse,folder/'adverse_fits',quote_frames=frames)
        for line in q.LINES:
            scope=OUT/f'{line}_{outer}';saved=w.read(scope/'committed.json')
            assert all(w.sha(ROOT/path)==sha for path,sha in saved['outputs'].items())
            model=w.read(scope/'learning.json');selection=model.pop('common_inner_weight_selection')
            assert selection==primary['selection'] and model==primary['models'][line]
            expected=pd.read_parquet(scope/'prices.parquet').ultimate.to_numpy()
            assert np.array_equal(one[line],expected) and np.array_equal(two[line],expected)
            held=frames[line].loc[frames[line].is_held].drop(columns=['T0','reserve','q_paired'])
            value,norm=k.forward(held,model,True);assert np.array_equal(value,expected) and norm==saved['ultimate_normalizers']
        print(json.dumps({'replayed_outer':outer,'inner_objectives':75,'whole_selector_and3finals_exact':True}),flush=True)
    totals,desc,_,_=m.cohort_blocks();weights=np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    draws=np.load(OUT/'cohort_bootstrap.npy');cohort=w.read(OUT/'cohort_report.json')
    assert np.allclose(m.cohort_scores(weights@totals),draws[:4],rtol=2e-12,atol=2e-13)
    for j,z in enumerate(cohort['comparisons']):assert desc[j]['delta']==z['delta'] and np.array_equal(np.quantile(draws[:,j],[.025/16,1-.025/16]),z['family16_band95'])
    draws=np.load(OUT/'POOLED_joint_bootstrap.npy')
    for j,name in enumerate(m.e.NAMES):assert np.array_equal(np.quantile(draws[:,j],[.025,.975]),report['results']['POOLED'][name]['bootstrap95'])
    m.check_sources(w.read(PLAN));dump(OUT/'replay_report.json',{'author':'Codex','utc':utc(),'report_sha256':w.sha(OUT/'report.json'),
        'all375inner_objectives_and5selectors_exact':True,'all15finals_primary_adverse_exact':True,'all_learning_blocked':True,
        'saved_intervals_and_first4weights_exact':True,'new_fits':0,'new_resampling':0,'new_submissions':0})
    print(json.dumps({'replay':'exact','selectors':5,'inner_objectives':375,'finals':15,'new_fits':0,'new_resampling':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();m.check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    assert w.read(OUT/'half_parity.json')['all90_price_and_norm_parity_bit_exact']
    primary=[w.read(OUT/f'outer{i}/primary_bundle.json') for i in range(5)]
    calls=sum(z['actual_Gfit_calls'] for z in primary);constants=d['new_primary_closed_constants']
    assert calls==len(list(OUT.glob('outer*/primary_fits/**/actual_G*_fit.json')))==len(list(OUT.glob('outer*/adverse_fits/**/actual_G*_fit.json')))
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];old=w.read(p.p.OLD/'report.json')['results']['POOLED']['NOMINAL']['delta']
    next_unit=('Register own2023 conditional-transfer complete common-weight selection with own inner/outer reporting and exact component ancestors before CSV/admission. No P67pooled2024target-trained report/components there.' if passed else
        'Inspect only saved new P105all5weight selections/inner margins and complete held cells against P65, without any refit/resampling. Do not expand weight grid, choose perline/stage, reuse selected weights outside their own training or probe the public board. If default half is selected everywhere, preserve exact existing result and move to distinct documented source/observation evidence.')
    text='# P105: selección interna común de mezcla\n\nCodex, '+utc()+'. '+('Pasa el combinado; transferencia propia requerida antes del CSV.' if passed else 'El combinado falla; no se admite un CSV nuevo.')+'\n\n'
    text+=f"Diferencia D² frente a referencia local: {a['delta']:+.7f}; IC95 por grupos [{a['bootstrap95'][0]:+.7f}, {a['bootstrap95'][1]:+.7f}]. Post31: {a['post31_delta']:+.7f}; peor celda: {a['worst_cell_delta']:+.7f}. Diferencia puntual frente a P65 fijo50/50: {a['delta']-old:+.7f}, sin nuevo intervalo pareado.\n\n"
    text+='| Fold exterior | Peso A1S elegido dentro de train |\n|---|---:|\n'
    for outer,z in enumerate(primary):text+=f"|{outer}|{z['selection']['weight']:.2f}|\n"
    text+=f'\nEl guardián inicial reprodujo exactamente precios y normas50/50en75ámbitos internos y15exteriores antes de cualquier nuevo ajuste. Se reutilizaron sus180componentes propios distintos, sin nuevo CDF/fuente o modelo nativo. Para pesos distintos se hicieron{calls}etapas Gprimarias y{calls}adversas;{constants}constantes primarias nuevas contando factores, nuisance y centros de entrenamiento (adversos separados; no grados de libertad).\n\n'
    text+='Los cinco selectores completos coincidieron bajo veneno exterior e interior. Se reprodujeron375objetivos internos, las cinco selecciones y quince finales, con aprendizaje bloqueado y el mismo payload limpio al cotizar. Intervalos y primeras ponderaciones se cotejaron sin nuevo remuestreo en replay. La selección usa solo costes interiores del entrenamiento; ningún peso proviene del público o del resultado exterior.\n\n'
    text+='Guardas globales: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+='Se conserva la normalización de Gdel algoritmo original por año/negocio al aplicar; no se mezcla aquí la alternativa de centros fijos P102. Sensibilidades con últimos nominales fijos, sin ajuste completo por escenario. Fuente2024 condicional, snapshots, observación/cola/reservas y búsqueda adaptativa siguen limitando la interpretación. Cero nuevo source/CDF/nativo/componentes,2025oenvíos. B00 y todas las alternativas conservadas,2024abierto adaptativo, sin garantía privada o revisión independiente.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{name:a[name] for name in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P105_minus_P65_point_only':a['delta']-old,
        'selected_weights':d['selected_weights'],'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,
        'primary_whole_selectors':5,'primary_final_models':15,'new_primary_Gstage_calls':calls,'new_adverse_Gstage_calls_separate':calls,
        'new_primary_closed_constants':constants,'adverse_closed_constants_separate':constants,'reused_distinct_component_objects':180,
        'new_native_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_component_fits':0,'new2025inference':0,'new_submissions':0,
        'next_unit':next_unit,'2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P105-MEZCLA-RESULTADO','P105: resultado de la mezcla elegida solo en entrenamiento')}
    cut=R/'privado'/('corte_P105_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));cut.mkdir();w.update(INDEX,receipt,cut)
    cp=R/'registro/semana2_contadores_propios_actual.json';c=w.read(cp);assert 'phase2_private_P105_common_mix_selector' not in c
    w.update(cp,{'cumulative_closed_form_constants':c['cumulative_closed_form_constants']+constants,'phase2_private_P105_common_mix_selector':receipt},cut)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P105'),(R/'registro/semana2_mision_privada_actual.json','P105')]:w.update(path,{key:receipt,'next_unit':next_unit},cut)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P105=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},cut)
    control=R/'registro/semana2_control_entregas_codex_actual.json';c=w.read(control)
    w.update(control,{'allow_new_submission':False,'reason':'P105 pooled pass still requires own transfer and exact CSV admission.' if passed else 'P105common training-only weight selector fails unchanged outer gates. No grid/line/public rescue or missing human authorization.',
        'last_evidence_review_utc':receipt['utc'],'latest_rejected_research_alternatives':c['latest_rejected_research_alternatives']+([] if passed else ['P105'])},cut)
    note='\n\n## Privada P105: mezcla interna, evaluación\n\nCodex, '+receipt['utc']+'. Decisión='+receipt['decision']+'; cinco selectores completos/375objetivos internos/quince finales en replay exacto,90paridades50/50antes de ajustarG. Cero nativos/fuente/CDF/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cut)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_mix_selector_validation_index':w.rel(INDEX),'week_2_private_mix_selector_validation_report':w.rel(DOC)},cut)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');a=argparse.ArgumentParser(description=__doc__);a.add_argument('mode',choices=['prepare','run','replay','close'])
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[a.parse_args().mode]()
