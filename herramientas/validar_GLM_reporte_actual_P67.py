"""Evaluación completa del GLM cross-fit con observación por fila y ramo."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import importlib.util
import argparse
import json
import os
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p67_current_crossfit',R/'herramientas/preparar_GLM_reporte_actual_P66.py')
u=importlib.util.module_from_spec(s);s.loader.exec_module(u)
driver=u.x.t;g=u.g;k=u.k;m=u.m;q=u.q;w=u.w;np=u.np;pd=u.pd;t=u.t;BASE=u.BASE
OUT=BASE/'P67_validacion_GLM_reporte_actual_20261027'
PLAN=R/'registro/semana2_GLM_reporte_actual_validacion_plan.json';INDEX=R/'registro/semana2_GLM_reporte_actual_validacion_actual.json'
DOC=R/'docs/semana2/PRIVADA_P67_VALIDACION_GLM_REPORTE_ACTUAL.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def immutable_dump(path,value):
    if 'outputs' in value:value['outputs'].pop(w.rel(path),None)
    if path.exists():assert w.read(path)==value,'Receipt differs: reconcile before continuing'
    else:dump(path,value)


def verify_inputs():
    d=w.read(OUT/'input_report.json');assert all(w.sha(ROOT/path)==value for path,value in d['outputs'].items())
    for outer in range(5):assert all(w.sha(ROOT/path)==value for path,value in w.read(OUT/f'outer{outer}/inputs_committed.json')['outputs'].items())
    return d


def frame_for(line,outer):
    path=OUT/f'input_{line}_{outer}.parquet';assert w.read(OUT/f'outer{outer}/inputs_committed.json')['outputs'][w.rel(path)]==w.sha(path)
    return pd.read_parquet(path)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(u.PLAN);m.check_sources(parent);receipt=w.read(u.OUT/'completion_receipt.json');assert receipt['report_sha256']==w.sha(u.OUT/'report.json')
    pre=w.read(u.OUT/'report.json');assert all(w.sha(ROOT/path)==value for path,value in pre['outputs'].items())
    original=w.read(t.PLAN);m.check_sources(original);OUT.mkdir()
    paths=[Path(__file__),u.PLAN,u.OUT/'report.json',u.OUT/'synthetic.json',u.OUT/'completion_receipt.json',Path(driver.__file__),t.PLAN]
    sources={**parent['sources'],**pre['outputs'],**original['sources']}
    for line in q.LINES:
        for outer in range(5):
            commit=t.OUT/f'{line}_{outer}/committed.json';d=w.read(commit);assert all(w.sha(ROOT/path)==value for path,value in d['outputs'].items())
            sources.update(d['outputs']);paths.append(commit)
    sources.update({w.rel(path):w.sha(path) for path in paths})
    plan={'author':'Codex','utc':utc(),'candidate':'Current_line_peril_rowproxy_observation_fixed_P56GLM_crossfit',
        'hypothesis':parent['hypothesis'],'need':parent['need'],'architecture':parent['architecture'],'fields':parent['fields'],'outer_and_inner':parent['outer_and_inner'],
        **{key:original[key] for key in ['criteria','bootstrap','cohort_guard','level_sensitivity']},
        'budget':parent['future_budget'],'scenarios':original['scenarios'],
        'adverse':'Actual second report/base/GLMfit with protected parent claim payload and held cost/covariates/offsets corrupted before numerical training; all outputs and invocation markers preserved. Same convergence/objective/gradient checks as P57.',
        'observation_dependency':'Every INNERscope learns its own pooled-peril cap and line/peril RPLcurves on source+own targettraining, then fixed rowFSpPROXYq. Outer application uses exact P64curves/P65base only on held. Old P55evaluator curve/share arguments are explicitly ignored by pinned P65numeric adapter; reserve files are P65copies of P64vectors.',
        'recovery':'Committed per-outer input hashes, per-call invoked/result checkpoints; no repeating unsaved invocation. Saved outputs may replay without adjusting. Complete input dependency hashes before and after learning.',
        'staged_decision':parent['future_criterion'],'limits':parent['limits']+['OOF64percent/fullouter80percent vs production80percent/full100percent and batch normalizer shifts remain part of algorithm. Conditional bootstrap does not cover whole fitting/selection uncertainty.'],
        'sources':sources,'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P67registra antes de ajustar la evaluación completa del mismo GLMestándar P56, alpha1/campos intactos, con offsets OOFyobservación actualP64/P65.25reportes internos/375CDF/25vectores de topes,75bases (150componentes/100etapas),15GLMprimarios; controles adversos reales separados por igual. Ningún tope/curva/base exterior entra al aprendizaje interior. La base exteriorP65solo se aplica a su retenido mediante precios ya guardados. Todas las guardas previas y convergencia, escenarios últimos fijos y transferencia propia si pasa. Cero fuente nueva/hiperparámetros/2025/envíos. B00conservado y2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P67registered_before_real_learning','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P67-GLM-PREVIO','P67: GLM estándar completo con reporte actual, antes de ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def inputs():
    plan=w.read(PLAN);m.check_sources(plan)
    if (OUT/'input_report.json').exists():verify_inputs();return
    if not (OUT/'inputs_started.json').exists():dump(OUT/'inputs_started.json',{'author':'Codex','utc':utc(),'pid':os.getpid()})
    frames={line:pd.read_parquet(u.OUT/f'canonical_{line}.parquet') for line in q.LINES}
    source=q.source_claims();claims=pd.read_parquet(q.CLAIMS);records=[];outputs={};counts=Counter();u.dump=immutable_dump
    for outer in range(5):
        folder=OUT/f'outer{outer}';commit=folder/'inputs_committed.json'
        if commit.exists():
            saved=w.read(commit);assert all(w.sha(ROOT/path)==value for path,value in saved['outputs'].items())
            records+=saved['records'];counts.update(saved['base_constant_counts']);outputs[w.rel(commit)]=w.sha(commit)
            for line in q.LINES:outputs[w.rel(OUT/f'input_{line}_{outer}.parquet')]=w.sha(OUT/f'input_{line}_{outer}.parquet')
            continue
        partition=pd.read_parquet(m.P1/f'inner_groups_outer{outer}.parquet').set_index('group_id').inner_fold
        oof,rr=u.build_inner(frames,source,claims,outer,partition,folder);local=Counter()
        for row in rr:local.update(row['base_constants'])
        for line,raw in frames.items():
            held=raw.loc[raw.fold.eq(outer)].copy();held['is_held']=True
            prepared=pd.read_parquet(t.t.OUT/f'input_{line}_{outer}.parquet',columns=['row_id','year','group_id','q_paired']).set_index('row_id').loc[held.row_id]
            prices=pd.read_parquet(t.OUT/f'{line}_{outer}/prices.parquet').set_index('row_id').loc[held.row_id]
            for name in ['year','group_id']:assert np.array_equal(prepared[name],held[name]) and np.array_equal(prices[name],held[name])
            held['q_paired']=prepared.q_paired.to_numpy();held['baseline_ultimate']=prices.ultimate.to_numpy()
            held['baseline_observed']=held.baseline_ultimate.to_numpy()*held.q_paired.to_numpy();held['crossfit_member']=-1
            f=pd.concat([oof[line],held],ignore_index=True);assert f.row_id.is_unique and set(f.row_id)==set(raw.row_id)
            f=f.set_index('row_id',drop=False).loc[raw.row_id].reset_index(drop=True);assert np.array_equal(f.is_held,f.fold.eq(outer))
            assert set(f.loc[~f.is_held,'group_id']).isdisjoint(set(f.loc[f.is_held,'group_id']))
            path=OUT/f'input_{line}_{outer}.parquet';f.to_parquet(path,index=False);outputs[w.rel(path)]=w.sha(path)
        files=list(folder.rglob('*.json'))+[OUT/f'input_{line}_{outer}.parquet' for line in q.LINES]
        immutable_dump(commit,{'outer':outer,'records':rr,'base_constant_counts':dict(local),'outputs':{w.rel(path):w.sha(path) for path in files}})
        records+=rr;counts.update(local);outputs[w.rel(commit)]=w.sha(commit)
        print(json.dumps({'outer_inputs_complete':outer,'inner_reporting_scopes':5,'inner_line_CDFs':75,'primary_base_learners':15,'new_source_fits':0}),flush=True)
    assert len(records)==75;m.check_sources(plan)
    completed={key:value for key,value in plan['budget'].items() if key not in ['primary_GLMfits','adverse_GLMfits_separate']}
    dump(OUT/'input_report.json',{'author':'Codex','utc':utc(),'stage':'Inner reporting and base inputs complete; final GLMnot yet fitted by this stage.','records':records,'outputs':outputs,'base_constant_counts':dict(counts),**completed});verify_inputs()


def final_dump(path,d):
    if path==OUT/'report.json':
        data=verify_inputs();d['status']='P67current_reporting_crossfit_GLM_pooled_complete_transfer_unmeasured'
        d['new_inner_base_closed_constants']=sum(data['base_constant_counts'].values());d['new_closed_constants']=d['new_inner_base_closed_constants']
        d.update({key:value for key,value in w.read(PLAN)['budget'].items() if key not in ['primary_GLMfits','adverse_GLMfits_separate']})
        d['inherited_P65_base_components']=30;d.pop('inherited_P55_base_components',None);d['GLM_offsets_crossfitted']=True
    return dump(path,d)


def setup():
    driver.OUT=OUT;driver.PLAN=PLAN;driver.INDEX=INDEX;driver.frame_for=frame_for;driver.dump=final_dump
    driver.v.SCENARIO=t.OUT/'scenario_inputs';m.apply_q=t.apply_row_q;driver.forward=forward


def forward(frame,artifact,ultimate=True):
    assert ultimate,'Use the current P65ultimate base then own qonly after GLM'
    value,relative=g.forward(frame,artifact)
    return value,{'kind':'GLM_no_batch_normalizer_after_saved_P65base','relative_prediction_digest':m.p.b.digest(relative.tolist())}


def run():inputs();setup();driver.run();verify_inputs();m.check_sources(w.read(PLAN))


def replay():
    verify_inputs();setup()
    def reject(*args,**kwargs):raise AssertionError('P67replay blocks own reporting and base learning')
    u.reporting=reject;t.t.line_curves=reject;k.learn=reject
    driver.replay();verify_inputs();m.check_sources(w.read(PLAN))


def close():
    assert not (OUT/'completion_receipt.json').exists();m.check_sources(w.read(PLAN));d=w.read(OUT/'report.json');inputs_report=verify_inputs()
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    assert len(list(OUT.glob('*_*/primary_fit_invoked.json')))==len(list(OUT.glob('*_*/adverse_fit_invoked.json')))==15
    assert len(list(OUT.glob('outer*/inner*/report_primary.json')))==len(list(OUT.glob('outer*/inner*/report_adverse.json')))==25
    assert len(list(OUT.glob('outer*/inner*/*/base_primary.json')))==len(list(OUT.glob('outer*/inner*/*/base_adverse.json')))==75
    a=d['results']['POOLED']['NOMINAL'];passed=d['all_pooled_gates_pass'];number=sum(inputs_report['base_constant_counts'].values())
    next_unit=('Register OWN2023-only conditional-transfer complete current-reporting crossfit model, with own inner/outer caps/curves/base/GLM. No P65outer pooled objects learned on2024targetlabels. Same all gates, no CSVfrom pooled alone.' if passed else
        'Compare NEWP67saved coefficients/whole validation against P60old-observation GLM and P65current base, without refitting or resampling. Determine whether the observation change leaves a standard-model residual generalization failure. No alpha/field/weight rescue or public probes; document a concrete next mechanism before another registered candidate.')
    paired=a['delta']-w.read(t.OUT/'report.json')['results']['POOLED']['NOMINAL']['delta']
    text='# P67: GLM estándar con reporte actual, evaluación completa\n\nCodex, '+utc()+'. '+('El combinado pasa; transferencia propia sigue pendiente.' if passed else 'El combinado falla las guardas; no se admite CSV y transferencia sigue sin evaluar.')+'\n\n'
    text+=f"ΔD²nominal={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f};{a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}. Incremento puntual frente aP65={paired:+.7f}, sin intervalo pareado nuevo.\n\n"
    text+='Misma receta GLMde efectos principales/alpha1y pesos50/50de base; cambió la observación respecto aP60.25reportes interiores propios/375curvas por ramo-peril/25vectores de topes,75bases (150componentes/100etapas),15GLMprimarios; controles adversos reales separados por igual. Los topes/curvas/base interiores excluyen ambos retenidos. La base exteriorP65solo se reutiliza en el retenido exterior. Quince replays finales exactos, aprendizaje/remuestreo bloqueados; gradiente/objetivo por otro método y todas las sumas/bandas conservadas.\n\n'
    text+='Guardas: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'.\n\n'
    text+=f'Constantes cerradas primarias nuevas:{number};30llamadasGLMiterativas contadas aparte. No árboles fuente,2025o envíos. Las sensibilidades usan últimos nominales fijos, no ajuste completo por escenario. Se conservan B00/F3cytodas las alternativas, fallos, búsqueda adaptativa2023/2024, fuente2024condicional, transportedel proxy, maduración/cola/reservas/maestros sin fecha y diferencia de tamaño de aprendizaje. No mejora privada acreditada o validación independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'input_report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'decision':d['decision'],
        'nominal':{key:a[key] for key in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'P67_minus_P65_point_only':paired,'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,
        'primary_GLM_fits':15,'adverse_GLM_fits_separate':15,'primary_inner_base_learners':75,'adverse_inner_base_learners_separate':75,'primary_line_CDFs':375,'adverse_line_CDFs_separate':375,
        'primary_cap_vectors':25,'adverse_cap_vectors_separate':25,'new_primary_closed_constants':number,'new_source_fits':0,'new2025inference':0,'new_submissions':0,
        'next_unit':next_unit,'2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P67-GLM-RESULTADO','P67: resultado completo GLM con observación actual, sin rescates')}
    archive=R/'privado'/('corte_P67_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    cp=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(cp);assert 'phase2_private_P67_current_crossfit_GLM' not in counts
    w.update(cp,{'cumulative_price_base_fits':counts['cumulative_price_base_fits']+30,'cumulative_closed_form_constants':counts['cumulative_closed_form_constants']+number,'phase2_private_P67_current_crossfit_GLM':receipt},archive)
    w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P67'),(R/'registro/semana2_mision_privada_actual.json','P67')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P67=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P67: GLM con reporte actual completo\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+f';375+375CDF,75+75bases,15+15GLM,{number}constantes primarias, replay exacto. Cero fuentes nuevas/2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_GLM_current_reporting_validation_index':w.rel(INDEX),'week_2_private_GLM_current_reporting_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['prepare','run','replay','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
