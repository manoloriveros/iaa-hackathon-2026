"""Evaluación completa del único cambio de reporte por ramo/peril P64."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import argparse
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p65_line_reporting',R/'herramientas/preparar_reporte_por_ramo_P64.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t)
p=t.p;u=t.u;v=u.v;k=t.k;m=t.m;q=t.q;w=t.w;pd=t.pd;np=t.np;BASE=t.BASE
OUT=BASE/'P65_validacion_reporte_por_ramo_20261027'
PLAN=R/'registro/semana2_reporte_por_ramo_validacion_plan.json';INDEX=R/'registro/semana2_reporte_por_ramo_validacion_actual.json'
DOC=R/'docs/semana2/PRIVADA_P65_VALIDACION_REPORTE_POR_RAMO.md'
PROFILES={};CURVES={}


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)
def frame_for(line,outer):return pd.read_parquet(t.OUT/f'input_{line}_{outer}.parquet')


def apply_row_q(frame,unused_legacy_pooled_curves,perils,unused_legacy_line_shares,tail=0.):
    line=frame.line.unique().item();outer=int(frame.fold.unique().item());assert perils==q.PERILS[line]
    if line not in PROFILES:PROFILES[line]=pd.read_parquet(u.OUT/f'FSp_proxy_{line}.parquet').set_index('row_id')
    source=PROFILES[line].loc[frame.row_id];assert np.array_equal(source.year,frame.year)
    key=(line,outer)
    if key not in CURVES:CURVES[key]=w.read(t.OUT/f'NOMINAL_outer{outer}'/line/'primary_curves.json')
    rates=source[['FSp_annual_cost_proxy_'+name for name in perils]].to_numpy(float)
    # Legacy P55passes pooled curves and line shares; neither enters the new link.
    # The actual numeric dependency is the pinned P64line/peril object above.
    return u.row_q(frame,rates,CURVES[key],perils,tail)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(t.PLAN);m.check_sources(parent);pre=w.read(t.OUT/'report.json')
    assert w.read(t.OUT/'completion_receipt.json')['report_sha256']==w.sha(t.OUT/'report.json')
    assert pre['primary_real_curve_strata']==225 and pre['adverse_real_curve_strata_separate']==225
    assert all(w.sha(ROOT/path)==value for path,value in pre['outputs'].items())
    original=w.read(p.PLAN);m.check_sources(original);OUT.mkdir();adapter={};bindings=[]
    for line in q.LINES:
        for outer in range(5):
            f=frame_for(line,outer);held=f.loc[f.is_held]
            assert np.array_equal(apply_row_q(held,None,q.PERILS[line],None),held.q_paired)
            bindings.append({'line':line,'outer':outer,'held_rows':len(held),'actual_new_curve_adapter_exact':True})
            for case in ['RESERVE075','RESERVE125']:
                z=f[['row_id']].copy();z['q']=f['q_'+case].to_numpy();path=OUT/'scenario_inputs'/f'{case}_{line}_{outer}_q.parquet'
                path.parent.mkdir(exist_ok=True);z.to_parquet(path,index=False);adapter[w.rel(path)]=w.sha(path)
    dump(OUT/'actual_adapter_precheck.json',bindings)
    paths=[Path(__file__),t.PLAN,t.OUT/'report.json',t.OUT/'synthetic.json',t.OUT/'completion_receipt.json',p.PLAN,OUT/'actual_adapter_precheck.json']
    sources={**original['sources'],**parent['sources'],**pre['outputs'],**adapter};sources.update({w.rel(path):w.sha(path) for path in paths})
    plan={'author':'Codex','utc':utc(),'candidate':'P54fixed_half_price_FSp_PROXY_observation_line_peril_reporting',
        'hypothesis':parent['hypothesis'],'need':'P62recovers P55loss broadly but fails all required delivery guards. P63mature developed line/peril reporting contrasts support testing uniform standard stratification; no known improvement or causal diagnosis.',
        'one_change':parent['one_change'],'price_architecture':original['price_architecture'],'observation_profile':original['unit_contract'],
        **{key:original[key] for key in ['criteria','bootstrap','cohort_guard','level_sensitivity']},
        'scenarios':'Use exact saved P64line/peril nominal and reserve075/125curves, fixed nominal rowFSpPROXYweights. Final nominal ultimate prices held fixed across scenarios. Tail005/010only BI/subsidence. No scenario price/source/report refits.',
        'integration':'Unchanged P55driver reads its legacy pooled curve/share arguments, but P65adapter explicitly ignores both and computes with pinned P64line/peril objects and P61rowFSpPROXYweights. All15actual adapter vectors matched prepared qexactly before registration. This checks the actual numeric path, not just metadata.',
        'budget':{'primary_closed_whole_learners':15,'adverse_closed_whole_learners_separate':15,'primary_components':30,'adverse_components_separate':30,
            'primary_shared_residual_stages':20,'adverse_shared_residual_stages_separate':20,'new_GLM_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'staged_decision':'Every unchanged P62pooled/scenario/cell/level/influence/cohort/family16guard applies. Pooled failure prevents admission; transfer=None. Pooled pass requires OWN2023-only conditional transfer with scoped reporting/price learning before exact-file admission. No automatic price export or upload.',
        'limits':parent['limits']+original['limits'],'sources':sources,'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P65congela antes de ajustar un único cambio frente aP62: las curvas protegidasP64por ramo/peril, con exactamente los mismos topes previos. Conserva base estándar50/50A1S/T2b, calibración/residual/calendario y proxyFSpnominal, sin nuevas variables o pesos.15aprendices cerrados primarios/15adversos,30+30componentes y20+20etapas; todas las guardas previas y transferencia propia si pasa combinado. Los15enlaces numéricos reales ya coinciden con qpreparado. La compatibilidad del evaluador lee argumentos antiguos pero los descarta explícitamente; usa curvasP64pinnadas. Cero nuevos árboles/GLM/CDF/2025/envíos; no admisión por promedio o punto. B00preservado y2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'P65registered_before_real_closed_learning','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P65-RAMO-PREVIO','P65: evaluación completa del reporte por ramo, guardas intactas')}
    dump(OUT/'registration.json',receipt);dump(INDEX,receipt);print(json.dumps(receipt))


def report_dump(path,d):
    if path==OUT/'report.json':d.update(status='P65line_peril_reporting_pooled_complete_transfer_unmeasured',observation_profile='Fixed_FSpPROXY_P64line_peril_CDFs',new_GLM_fits=0,new_CDF_fits=0)
    return dump(path,d)


def setup():
    v.OUT=OUT;v.PLAN=PLAN;v.INDEX=INDEX;v.SCENARIO=OUT/'scenario_inputs';k.frame_for=frame_for
    m.OUT=OUT;m.e.OUT=OUT;m.apply_q=apply_row_q;v.dump=report_dump


def run():setup();v.run()


def replay():
    setup()
    def reject(*args,**kwargs):raise AssertionError('P65replay blocks new line/peril report fitting')
    t.line_curves=reject;v.replay()


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];number=sum(d['primary_constants'].values())
    previous=w.read(p.OUT/'report.json')['results']['POOLED']['NOMINAL']['delta'];paired=a['delta']-previous
    next_unit=('Prepare OWN2023-only conditional-transfer full validation for exact P65with line/peril reporting and fixed source proxies. Same criteria, cost/config/forum before learning; no production or upload from pooled alone.' if passed else
        'Use NEW P65saved failure to decide whether line/peril reporting materially addresses the observation miss. No resampling or refit of unchanged models, line/peril overrides, public probes or missing authorization. Preserve source/target transport and ultimate-tail uncertainties before registering the next standard mechanism.')
    text='# P65: evaluación completa del reporte por ramo/peril\n\nCodex, '+utc()+'. '+('El combinado pasa; falta transferencia propia antes de admisión.' if passed else 'El combinado falla; no se admite CSV y transferencia permanece sin evaluar.')+'\n\n'
    text+=f"ΔD²frente a referencia={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f};{a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}. Diferencia puntual P65menosP62={paired:+.7f}, sin nuevo intervalo pareado.\n\n"
    text+='Único cambio frente aP62: conjuntos de riesgo/evento de reporte por ramo/peril, manteniendo los topes previos y todo el precio estándar, composición proxy y fuentes. Quince aprendices cerrados primarios/15adversos;30+30componentes y20+20etapas. Los15replays con aprendizaje bloqueado reprodujeron precios últimos y normalizadores; intervalos/multiplicidades guardados y sumas independientes coincidieron.\n\n'
    text+='Guardas: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+=f'{number}constantes primarias nuevas. Sin GLM, árboles fuente, curvas nuevas en esta evaluación,2025o envíos. Los escenarios mantuvieron precios últimos y pesos proxy nominales fijos; no se afirma reentrenamiento por escenario. Transferencia=None;2024es desarrollo adaptativo, no confirmación prístina. Persisten transporte del proxy/CDF, costes y reservas a valoración, cola, fuente2024condicional y datos sin fecha; no mejora privada acreditada ni validación independiente. B00/F3cytodas las alternativas conservados.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{key:a[key] for key in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P65_minus_P62_point_only':paired,'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,
        'primary_closed_whole_learners':15,'adverse_closed_whole_learners_separate':15,'new_primary_constants':number,'new_GLM_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0,
        'next_unit':next_unit,'2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P65-RAMO-RESULTADO','P65: resultado completo de reporte por ramo y límites de entrega')}
    archive=R/'privado'/('corte_P65_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    cp=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(cp);assert 'phase2_private_P65_line_reporting' not in counts
    w.update(cp,{'cumulative_closed_form_constants':counts['cumulative_closed_form_constants']+number,'phase2_private_P65_line_reporting':receipt},archive);w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P65'),(R/'registro/semana2_mision_privada_actual.json','P65')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P65=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P65: reporte por ramo, validación completa\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+f';15aprendices primarios/15adversos,{number}constantes, replay exacto. Cero fuente/GLM/CDF/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_line_reporting_validation_index':w.rel(INDEX),'week_2_private_line_reporting_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['prepare','run','replay','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
