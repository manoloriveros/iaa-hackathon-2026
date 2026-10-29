"""Cambio único P55: observación por composición FSp explícitamente proxy."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p62_proxy_adapter',R/'herramientas/preparar_proxy_observacion_P61.py')
u=importlib.util.module_from_spec(s);s.loader.exec_module(u)
v=u.v;k=u.k;m=u.m;q=u.q;w=u.w;pd=u.pd;np=u.np;BASE=u.BASE
OUT=BASE/'P62_validacion_proxy_observacion_20261027'
PLAN=R/'registro/semana2_proxy_observacion_validacion_plan.json';INDEX=R/'registro/semana2_proxy_observacion_validacion_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P62_VALIDACION_PROXY_OBSERVACION.md'
PROFILES={}


def utc():return datetime.now(timezone.utc).isoformat()
def dump(p,z):return m.dump(p,z)


def frame_for(line,outer):return pd.read_parquet(u.OUT/f'input_{line}_{outer}.parquet')


def apply_row_q(f,curves,perils,unused_old_line_shares,tail=0.):
    line=f.line.unique().item();assert perils==q.PERILS[line]
    if line not in PROFILES:PROFILES[line]=pd.read_parquet(u.OUT/f'FSp_proxy_{line}.parquet').set_index('row_id')
    source=PROFILES[line].loc[f.row_id]
    assert np.array_equal(source.year,f.year)
    rates=source[['FSp_annual_cost_proxy_'+p for p in perils]].to_numpy(float)
    # The legacy evaluator supplies old line shares; they have NOrole in this new hypothesis.
    return u.row_q(f,rates,curves,perils,tail)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(u.PLAN);receipt=w.read(u.OUT/'completion_receipt.json');assert receipt['report_sha256']==w.sha(u.OUT/'report.json')
    assert (u.OUT/'registered_code.py').read_bytes()==Path(u.__file__).read_bytes();m.check_sources(parent)
    report=w.read(u.OUT/'report.json');assert all(w.sha(ROOT/p)==value for p,value in report['outputs'].items())
    original=w.read(v.PLAN);m.check_sources(original)
    OUT.mkdir();adapter_outputs={}
    # Numeric identity adapters for the unchanged P55scenario evaluator, frozen before fit.
    for line in q.LINES:
        for outer in range(5):
            f=frame_for(line,outer)
            for case in ['RESERVE075','RESERVE125']:
                z=f[['row_id']].copy();z['q']=f['q_'+case].to_numpy()
                path=OUT/'scenario_inputs'/f'{case}_{line}_{outer}_q.parquet';path.parent.mkdir(exist_ok=True)
                z.to_parquet(path,index=False);adapter_outputs[w.rel(path)]=w.sha(path)
    paths=[Path(__file__),u.PLAN,u.OUT/'report.json',u.OUT/'synthetic.json',u.OUT/'completion_receipt.json',v.PLAN]
    sources={**original['sources'],**parent['sources'],**report['outputs'],**adapter_outputs};sources.update({w.rel(p):w.sha(p) for p in paths})
    plan={'author':'Codex','utc':utc(),'candidate':'P54fixed_half_price_P50curves_FSp_PROXYrow_observation',
        'hypothesis':parent['observation_hypothesis'],'need':'P55/P57/P60miss original guards. Before increasing price capacity test one observation assumption under already learned P50curves, using the now correctly named FSpcostproxy. No causal failure diagnosis or known improvement follows from P61.',
        'configuration':parent['new_recipe_if_later_registered'],'unit_contract':parent['unit_contract'],'formula':parent['formula'],
        'price_architecture':'Exactly unchanged P54two calibrated cost components, arithmetic weights .5/.5and original shared residual stages. ONEcomplete targetlearner perline on alltraining for eventual production; sourceA1S3seeds geometric input and totalT2bunchanged. No new GLM/cross-fit stack, price-source substitution or extra mixture weight.',
        'single_change':'Same P55scope, target/calendar/source/closed rules; qfrom target-training constant perilline shares is replaced by fixed rowFSpPROXYcomposition and same per-peril P50costCDFs. Proxyprofile is NOTa T2bdecomposition and does not identify true ultimate costcomposition. Legacy evaluator line-share argument explicitly ignored; it is not blended or estimated anew.',
        **{name:original[name] for name in ['criteria','bootstrap','cohort_guard','level_sensitivity']},
        'scenarios':'Frozen nominal FSpweights and final nominal ultimate prices in all5cases. Reserve075/125use exact saved per-perilP52CDFs only; tail005/010scale BI/subsidence completions. No targetmix reestimate or full scenario price retraining. Scenario compatibility files are exact copies of P61qvectors by key.',
        'budget':{'primary_closed_whole_learners':15,'adverse_closed_whole_learners_separate':15,'primary_components':30,'adverse_components_separate':30,
            'primary_shared_residual_stages':20,'adverse_shared_residual_stages_separate':20,'new_source_price_fits':0,'new_GLM_fits':0,'new_CDF_fits':0,
            'new2025inference':0,'new_submissions':0},
        'staged_decision':'Every unchanged pooled/scenario/cell/level/influence/cohort/family16guard applies. Any failure prevents admission; transfer remains None. A pooled pass requires OWNconditional-transfer reporting/price learning trained only on2023targetgroups, fixed source proxies with source2024conditional limit. No automatic production/upload or originalT2bperil claim.',
        'limits':['Borrowing FSpcomposition for both total-price components and cross-market transport is a modeling assumption, not identified truth.',
            'P50costCDFpooling by peril name acrosslines, p995weights, mature-source1095FSpoffset and tail/reserves remain limitations.',
            'Adaptive2023/2024, source2024conditional, supplied snapshot/history/climate availability limits and conditional bootstrap persist. No independent professional validation.'],
        'sources':sources,'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P62registra antes de ajustar un único cambio sobreP55: igual base estándar A1S/T2bal50/50, formas/niveles/residual/calendario, curvasP50ya guardadas; solo qpasará de mezcla constante por ramo a composición por fila del PROXYFSpcorrectamente identificado. No es descomposición T2bni verdad última identificada.15aprendices cerrados primarios/15adversos (30+30componentes,20+20etapas). Pesos proxy nominales y últimos fijos en reservas/cola; se verifica SHAde cada qcompatibilidad. Mismos umbrales/celdas/folds/años/IC/Post31/nivel/NB/broker/historia/familia16. Si falla combinado no se admite; si pasa exige transferencia propia2023antes de CSV. Cero GLM/árboles fuente/CDFnuevas/2025/envíos. B00/F3c/adversos conservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'P62registered_before_real_closed_learning','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P62-PROXY-PREVIO','P62: un cambio de observación, proxy explícito y guardas intactas')}
    dump(OUT/'registration.json',receipt);dump(INDEX,receipt);print(json.dumps(receipt))


def report_dump(path,d):
    if path==OUT/'report.json':
        d['status']='P62FSp_proxy_observation_pooled_complete_transfer_unmeasured'
        d.update(observation_profile='FSpPRODexplicit_cost_PROXY_NOT_T2bdecomposition',new_GLM_fits=0,new_CDF_fits=0)
    return dump(path,d)


def setup():
    v.OUT=OUT;v.PLAN=PLAN;v.INDEX=INDEX;v.SCENARIO=OUT/'scenario_inputs';v.k.frame_for=frame_for
    m.OUT=OUT;m.e.OUT=OUT;m.apply_q=apply_row_q;v.dump=report_dump


def run():setup();v.run()
def replay():setup();v.replay()


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];number=sum(d['primary_constants'].values())
    next_unit=('Prepare OWNconditional-transfer2023-only target CDFs and exact P54price learning with this fixed FSpPROXYrow link. Source coefficients stay fixed/source2024conditional. Same complete gates, no source/candidate admission from pooled alone.' if passed else
        'Review the NEW P62closed comparison against P55same-price/common-q before further capacity. Do not attribute causality, turn FSpinto T2bdecomposition, tune weights/fields or repeat old P46tests. If rowproxy fails, return to the declared reporting/line/market assumptions and source evidence before another registered standard candidate; no public probe or missing authorization.')
    text='# P62: cambio de observación con proxy FSp explícito\n\nCodex, '+utc()+'. '+('El combinado pasa las guardas; transferencia propia sigue pendiente antes de admitir.' if passed else 'El combinado falla las guardas; se conserva sin admitir para envío y transferencia sin evaluar.')+'\n\n'
    text+=f"ΔD²nominal={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f}; {a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}.\n\n"
    text+='Única intervención respecto a P55: composición por fila FSpPROXYen el enlace de observación, con las mismas curvas de coste P50y la base de precio fija50/50A1S/T2b. No es una descomposición de T2bo una composición última identificada. El peso de exposición del periodo se canceló en el proxy; calendario de precio una vez. Quince aprendices cerrados primarios/15adversos,30+30componentes y20+20etapas residuales;15replays finales exactos. Sin GLM, nuevas fuentes/curvas, hiperparámetros o pesos seleccionados.\n\n'
    text+='Guardas: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'. Las sensibilidades mantuvieron pesos proxynominales y precios últimos fijos; no se afirma reentrenamiento completo por escenario. Transferencia=None.\n\n'
    text+=f'Constantes primarias nuevas:{number}. Se conservaron controles adversos, niveles por sumas independientes, intervalos/multiplicidades y replay sin ajuste. Cero inferencias2025o envíos. B00/F3c/adversos conservados,2024abierto adaptativo. Subsisten supuestos de transporte del proxy/CDF, nombres de peril compartidos entre líneas, datos sin fecha y fuente2024condicional; no mejora privada acreditada ni revisión profesional independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
        'document':w.rel(DOC),'decision':d['decision'],'nominal':{p:a[p] for p in ['delta','bootstrap95','post31_delta','worst_cell_delta']},
        'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,'primary_closed_learners':15,'adverse_closed_learners_separate':15,
        'new_primary_constants':number,'new_source_price_fits':0,'new_GLM_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0,
        'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P62-PROXY-RESULTADO','P62: resultado completo con proxy de observación y controles')}
    archive=R/'privado'/('corte_P62_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    count_path=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(count_path);assert 'phase2_private_P62_proxy_observation' not in counts
    w.update(count_path,{'cumulative_closed_form_constants':counts['cumulative_closed_form_constants']+number,'phase2_private_P62_proxy_observation':receipt},archive)
    w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P62'),(R/'registro/semana2_mision_privada_actual.json','P62')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P62=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P62: observación por proxy FSp explícito\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+f';15aprendices primarios/15adversos,{number}constantes, replay exacto. Cero fuente/GLM/CDF/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_proxy_observation_validation_index':w.rel(INDEX),'week_2_private_proxy_observation_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','run','replay','close']);args=p.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
