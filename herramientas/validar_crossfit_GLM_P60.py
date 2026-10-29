"""Evaluación completa cross-fit P59 con reportes/bases interiores propios."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import importlib.util
import argparse
import json
import os
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p60_crossfit_kernel',R/'herramientas/preparar_crossfit_GLM_P59.py')
u=importlib.util.module_from_spec(s);s.loader.exec_module(u)
t=u.t;g=u.g;k=u.k;m=u.m;q=u.q;w=u.w;np=u.np;pd=u.pd;BASE=u.BASE
OUT=BASE/'P60_validacion_crossfit_GLM_20261027'
PLAN=R/'registro/semana2_crossfit_GLM_validacion_plan.json';INDEX=R/'registro/semana2_crossfit_GLM_validacion_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P60_VALIDACION_CROSSFIT_GLM.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(p,v):return m.dump(p,v)


def check_sources(plan):
    m.check_sources(plan)
    # P56's pinned source manifest contains the reused reserve/tail numerical inputs.
    # Checking just the manifest's bytes would not verify those dependency files.
    m.check_sources(w.read(g.PLAN))


def immutable_dump(path,value):
    # A resumed child receipt must not add its own previous hash to its payload.
    if 'outputs' in value:value['outputs'].pop(w.rel(path),None)
    if path.exists():assert w.read(path)==value,'Saved receipt changed; reconcile, do not overwrite'
    else:dump(path,value)


def verify_inputs():
    report=w.read(OUT/'input_report.json')
    for p,value in report['outputs'].items():assert w.sha(ROOT/p)==value
    for outer in range(5):
        commit=w.read(OUT/f'outer{outer}/inputs_committed.json')
        assert all(w.sha(ROOT/p)==value for p,value in commit['outputs'].items())
    return report


def frame_for(line,outer):
    p=OUT/f'input_{line}_{outer}.parquet';expected=w.read(OUT/f'outer{outer}/inputs_committed.json')['outputs'][w.rel(p)]
    assert w.sha(p)==expected
    return pd.read_parquet(p)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(u.PLAN);receipt=w.read(u.OUT/'completion_receipt.json');assert receipt['report_sha256']==w.sha(u.OUT/'report.json')
    assert (u.OUT/'registered_code.py').read_bytes()==Path(u.__file__).read_bytes();m.check_sources(parent)
    report=w.read(u.OUT/'report.json');assert all(w.sha(ROOT/p)==value for p,value in report['outputs'].items())
    paths=[Path(__file__),u.PLAN,u.OUT/'report.json',u.OUT/'synthetic.json',u.OUT/'completion_receipt.json',t.PLAN]
    sources={**parent['sources'],**report['outputs']};sources.update({w.rel(p):w.sha(p) for p in paths})
    old=w.read(t.PLAN);OUT.mkdir()
    plan={'author':'Codex','utc':utc(),'candidate':'P54fixed_half_base_plus_crossfitted_P56offset_GLM',
        'need':'P58new GLMfit-vs-held discrepancy; P59numeric end-to-end protection passed. Cross-fitting is a standard test of dependence on in-sample base fits, not an established remedy.',
        'architecture':parent['architecture'],'source_ancestry':parent['source_ancestry'],'partitions':parent['partitions'],
        **{name:old[name] for name in ['model','numeric','categorical','additional_numeric','preprocessing','offset_identity','convergence','availability','criteria','bootstrap','cohort_guard','level_sensitivity']},
        'budget':parent['future_real_budget'],
        'outer_evaluation':'Reuse saved P55full outerbase ONLYon outerheld, with ownP50outerq. Train GLMon complete OOFoffsets from its outertraining groups. No mean5GLMs or copying inherited q/base into innertrain. Same109296historical rows and everyline/year/business/fold.',
        'scenarios':'Final ultimate prices nominal/fixed. Use exact saved P52reserve/tail outer observation branches with same scope/P50formula. Inner OOFlearners nominal, no full scenario retraining claim.',
        'decision':'Every unchanged pooled/convergence/cohort/family16/scenario/level/influence guard applies. Any pooled failure rejects admission; transfer remains None. A pooled pass needs OWNconditional-transfer inner/outer reporting/base/GLMtrained only on2023targetgroups, fixed developed-only sources with conditional2024limit. No public probe or automatic upload.',
        'recovery':'Ownper-scope source/input hashes and invocation/result checkpoints. Skip completed inputscopes by SHA; reuse saved primary/adverse modelresults, replay unsaved outputs only. A fit invoked without result stops for explicit reconciliation; no timeout-based restart.',
        'limits':parent['limits']+['OOFvsfull training-size and application-normalizer shift is part of the algorithm; conditional bootstrap does not cover all fitting/selection uncertainty.'],
        'sources':sources,'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P60registra antes de ajustar la evaluación completa del GLM cross-fit P59.25reportes interiores propios (275CDFprimarias/275adversas,75+75cuotas),75bases/75adversas (150+150componentes,100+100etapas residuales) y15GLM/15adversos. Objetivo/folds/atributos/alpha1sin cambios. Cada offset OOFexcluye su grupo de C0/base; la baseP55exterior solo predice su retenido. Se mantienen TODASlas guardas y convergencia, escenarios últimos fijos, transferencia propia pendiente si pasa. Producción interior80%/base100%con hash5ya congelado; no media5modelos. Cero nuevos árboles fuente, inferencias2025o envíos. B00/F3c/adversos conservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'P60registered_before_real_crossfit_learning','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P60-CROSSFIT-PREVIO','P60: evaluación completa cross-fit, coste y guardas antes de ajustar')}
    dump(OUT/'registration.json',receipt);dump(INDEX,receipt);print(json.dumps(receipt))


def inputs():
    plan=w.read(PLAN);check_sources(plan)
    if (OUT/'input_report.json').exists():verify_inputs();return
    if not (OUT/'inputs_started.json').exists():dump(OUT/'inputs_started.json',{'author':'Codex','utc':utc(),'pid':os.getpid()})
    frames={line:pd.read_parquet(u.OUT/f'canonical_{line}.parquet') for line in q.LINES}
    source=q.source_claims();claims=pd.read_parquet(q.CLAIMS);records=[];outputs={};counts=Counter();u.dump=immutable_dump
    for outer in range(5):
        folder=OUT/f'outer{outer}';commit_path=folder/'inputs_committed.json'
        if commit_path.exists():
            saved=w.read(commit_path);assert all(w.sha(ROOT/p)==value for p,value in saved['outputs'].items())
            records+=saved['records'];counts.update(saved['base_constant_counts']);outputs[w.rel(commit_path)]=w.sha(commit_path)
            for line in q.LINES:outputs[w.rel(OUT/f'input_{line}_{outer}.parquet')]=w.sha(OUT/f'input_{line}_{outer}.parquet')
            continue
        inner=pd.read_parquet(m.P1/f'inner_groups_outer{outer}.parquet').set_index('group_id').inner_fold
        oof,rr=u.build_inner(frames,source,claims,outer,inner,folder);local_counts=Counter()
        for row in rr:local_counts.update(row['base_constants'])
        for line in q.LINES:
            original=pd.read_parquet(g.OUT/f'input_{line}_{outer}.parquet');original=original.loc[original.is_held].copy()
            held=u.raw_frame(original,line)
            for name in ['baseline_ultimate','baseline_observed','q_paired','is_held']:held[name]=original[name].to_numpy()
            held['crossfit_member']=-1
            f=pd.concat([oof[line],held],ignore_index=True)
            assert f.row_id.is_unique and set(f.row_id)==set(frames[line].row_id)
            f=f.set_index('row_id',drop=False).loc[frames[line].row_id].reset_index(drop=True)
            assert np.array_equal(f.is_held,f.fold.eq(outer))
            assert set(f.loc[~f.is_held,'group_id']).isdisjoint(set(f.loc[f.is_held,'group_id']))
            path=OUT/f'input_{line}_{outer}.parquet';f.to_parquet(path,index=False);outputs[w.rel(path)]=w.sha(path)
        files=list(folder.rglob('*.json'))+[OUT/f'input_{line}_{outer}.parquet' for line in q.LINES]
        dump(commit_path,{'author':'Codex','utc':utc(),'outer':outer,'records':rr,'base_constant_counts':dict(local_counts),
            'outputs':{w.rel(p):w.sha(p) for p in files}})
        records+=rr;counts.update(local_counts);outputs[w.rel(commit_path)]=w.sha(commit_path)
        print(json.dumps({'crossfit_outer_inputs_complete':outer,'inner_reports':5,'primary_base_learners':15,'new_source_price_fits':0}),flush=True)
    assert len(records)==75;check_sources(plan)
    dump(OUT/'input_report.json',{'author':'Codex','utc':utc(),'records':records,'outputs':outputs,'base_constant_counts':dict(counts),
        'primary_cost_CDF_estimators':275,'adverse_cost_CDF_estimators_separate':275,'primary_base_learners':75,'adverse_base_learners_separate':75,
        'primary_components':150,'adverse_components_separate':150,'primary_shared_residual_stages':100,'adverse_shared_residual_stages_separate':100,
        'primary_share_vectors':75,'adverse_share_vectors_separate':75,'new_source_price_fits':0,'new2025inference':0,'new_submissions':0})
    verify_inputs()


def final_dump(path,d):
    if path==OUT/'report.json':
        report=verify_inputs();d['status']='P60crossfitted_GLM_pooled_complete_transfer_unmeasured'
        d['new_inner_base_closed_constants']=sum(report['base_constant_counts'].values());d['new_closed_constants']=d['new_inner_base_closed_constants']
        for name in ['primary_cost_CDF_estimators','adverse_cost_CDF_estimators_separate','primary_base_learners','adverse_base_learners_separate',
            'primary_components','adverse_components_separate','primary_shared_residual_stages','adverse_shared_residual_stages_separate','primary_share_vectors','adverse_share_vectors_separate']:d[name]=report[name]
        d['inherited_P55_base_components']=30;d['outer_base_refits']=0;d['GLM_offsets_crossfitted']=True
    return dump(path,d)


def run():
    inputs();t.OUT=OUT;t.PLAN=PLAN;t.INDEX=INDEX;t.frame_for=frame_for;t.dump=final_dump
    t.run();verify_inputs();check_sources(w.read(PLAN))


def replay():
    verify_inputs();t.OUT=OUT;t.PLAN=PLAN;t.INDEX=INDEX;t.frame_for=frame_for;t.dump=final_dump
    t.replay();verify_inputs();check_sources(w.read(PLAN))


def close():
    assert not (OUT/'completion_receipt.json').exists();check_sources(w.read(PLAN));d=w.read(OUT/'report.json');inputs_report=verify_inputs()
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    assert len(list(OUT.glob('*_*/primary_fit_invoked.json')))==len(list(OUT.glob('*_*/adverse_fit_invoked.json')))==15
    assert len(list(OUT.glob('outer*/inner*/report_primary.json')))==len(list(OUT.glob('outer*/inner*/report_adverse.json')))==25
    assert len(list(OUT.glob('outer*/inner*/*/base_primary.json')))==len(list(OUT.glob('outer*/inner*/*/base_adverse.json')))==75
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];number=d['new_inner_base_closed_constants']
    next_unit=('Prepare OWNconditional-transfer cross-fit pipeline with target2023ONLYat every inner/outer report, base and GLMstage. P55pooled outerbase cannot be used there. Fixed developed-only sources remain conditional2024. Freeze all330+330reportCDFs/90+90bases/15+15GLMs cost and same guards before learning; no production/CSVadmission from pooled alone.' if passed else
        'Review NEWP60cross-fitted results/coefficients versus the saved P57in-sample and P55base without refitting. Determine whether cross-fitting addressed the documented transport issue; no automatic alpha/field/weight rescue. Keep all adverse scenarios/cohorts and explain remaining standard-model need before another registered candidate. No repeat old support/C0audits or public probes.')
    text='# P60: evaluación completa del GLM con offsets cruzados\n\nCodex, '+utc()+'. '+('El combinado pasa las guardas aplicables; falta transferencia propia completa antes de admitir.' if passed else 'El combinado no supera las guardas; se conserva sin admitir para envío. Transferencia sin evaluar.')+'\n\n'
    text+=f"ΔD²nominal={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f}; {a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}.\n\n"
    text+='Se aprendieron25reportes interiores propios (275CDFprimarias/275adversas),75bases/75adversas (150+150componentes,100+100etapas residuales) y15GLM/15adversos. Cada fila de entrenamiento recibió exactamente un offset fuera de su grupo. q/precios/normalizadores exteriores se eliminaron antes del aprendizaje interior; la base exterior P55solo predijo el retenido exterior. Source-only fijo, mismos campos, alpha1y pesos50/50. El control numérico adverso fue real en curvas/bases/GLM, no un selector de metadatos.\n\n'
    text+='Guardas: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'. Se conservan todos los escenarios, celdas, años, folds, influencia, nivel y bandas16. Los últimos nominales permanecieron fijos en sensibilidades; no se afirma reentrenamiento completo por escenario. Quince replays finales exactos con aprendizaje/remuestreo bloqueados.\n\n'
    text+=f'Constantes cerradas interiores primarias:{number}. Treinta llamadas GLMiterativas reales, contadas aparte de esas constantes. Cero ajustes de árboles fuente, inferencias2025o envíos. B00/F3c/adversos conservados,2024abierto adaptativo. Persisten fuentes2024condicionales, normalizadores/tamaños64%/80%frente a80%/100%, qcomún por ramo, maestros/cola/reservas y búsqueda adaptativa. No es mejora privada establecida o revisión profesional independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'input_report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
        'document':w.rel(DOC),'decision':d['decision'],'nominal':{p:a[p] for p in ['delta','bootstrap95','post31_delta','worst_cell_delta']},
        'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,'primary_GLM_fits':15,'adverse_GLM_fits_separate':15,
        'primary_inner_base_learners':75,'adverse_inner_base_learners_separate':75,'primary_cost_CDF_estimators':275,'adverse_cost_CDF_estimators_separate':275,
        'primary_components':150,'adverse_components_separate':150,'primary_shared_residual_stages':100,'adverse_shared_residual_stages_separate':100,
        'new_primary_closed_constants':number,'new_source_price_fits':0,'new2025inference':0,'new_submissions':0,
        'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P60-CROSSFIT-RESULTADO','P60: validación completa cross-fit, resultado y transferencia pendiente')}
    archive=R/'privado'/('corte_P60_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    count_path=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(count_path);assert 'phase2_private_P60_crossfit_GLM' not in counts
    w.update(count_path,{'cumulative_price_base_fits':counts['cumulative_price_base_fits']+30,
        'cumulative_closed_form_constants':counts['cumulative_closed_form_constants']+number,'phase2_private_P60_crossfit_GLM':receipt},archive)
    w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P60'),(R/'registro/semana2_mision_privada_actual.json','P60')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P60=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P60: GLM con offsets cruzados, evaluación completa\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+f';275+275CDF,75+75bases,15+15GLM,{number}constantes primarias, replay exacto. Cero fuente/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_crossfit_GLM_validation_index':w.rel(INDEX),'week_2_private_crossfit_GLM_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','run','replay','close']);args=p.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
