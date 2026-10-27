"""Valida la mezcla fija P54 completa; toda guarda permanece preinscrita."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import importlib.util
import argparse
import math
import json
import os
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p55_fixed_standard_mixture',R/'herramientas/preparar_mezcla_estandar_P54.py')
k=importlib.util.module_from_spec(s);s.loader.exec_module(k)
m=k.m;w=k.w;pd=k.pd;np=k.np;BASE=k.BASE
SCENARIO=BASE/'P52_validacion_A1R_20261027'
OUT=BASE/'P55_validacion_mezcla_20261027'
PLAN=R/'registro/semana2_mezcla_estandar_validacion_plan.json';INDEX=R/'registro/semana2_mezcla_estandar_validacion_actual.json'
DOC=R/'docs/semana2/PRIVADA_P55_VALIDACION_MEZCLA_ESTANDAR.md'
m.OUT=OUT;m.e.OUT=OUT


def utc():return datetime.now(timezone.utc).isoformat()
def dump(p,v):return m.dump(p,v)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(k.PLAN);assert w.read(k.OUT/'completion_receipt.json')['plan_sha256']==w.sha(k.PLAN)
    assert (k.OUT/'preflight_code.py').read_bytes()==Path(k.__file__).read_bytes()
    assert all(w.sha(ROOT/p)==v for p,v in parent['sources'].items())
    branch=w.read(SCENARIO/'branch_report.json');assert branch['primary_curves']==110 and branch['adverse_separate']==110
    assert all(w.sha(ROOT/p)==v for p,v in branch['outputs'].items())
    sources={**parent['sources'],**branch['outputs']}
    paths=[Path(__file__),k.PLAN,k.OUT/'completion_receipt.json',k.OUT/'synthetic.json',k.OUT/'bindings.json',
        SCENARIO/'branch_report.json',R/'registro/semana2_mision_privada_plan_v1.json']
    sources.update({w.rel(p):w.sha(p) for p in paths})
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'candidate':'fixed_half_A1S_T2b_calendar_scoped_costq_single_complete_target_learner',
        'hypothesis':parent['hypothesis'],'need':parent['need'],'configuration':parent['frozen_recipe'],
        'observation':parent['observation'],'whole_algorithm':'Production would fit ONEcomplete calibrator perline on all known targettraining after the same two frozen developed-only source inputs and own all-training reporting. Outer evaluation fits exactly that same algorithm on80percent targetgroups. No nestedH1ratio or mean of5targetmodels; all3sourceA1Sseeds remain in its fixed geometric source input.',
        'comparator':'Same protected original A1S/S2/H1reference and109296historical rows as P52/P53. Different training fractions/observation/target architecture are explicit; no exactF3cidentity or causal component attribution.',
        **parent['future_acceptance'],
        'scenario':'Reuse byte-verified P52reserve075/125andtail005/010observation branches with same P50scope/train-only perilline shares; both components share this registered q. Whole ultimate prices nominal and fixed. No curve refit or full scenario price retraining claim.',
        'staged_decision':'All pooled global/scenario/cell/level/influence/cohort/family16guards apply unchanged. Any failure rejects admission; TRANSFERremains None/unmeasured, not a pass. A pooled pass requires OWNconditional-transfer reporting and target learning before production/file admission. Developed-only source coefficients stay fixed, with conditional-source2024limitation, no new90sourcefits needed here.',
        'budget':{'primary_whole_target_learners':15,'adverse_whole_target_learners_separate':15,
            'primary_component_calibrations':30,'adverse_component_calibrations_separate':30,
            'primary_shared_residual_stage_calls':20,'adverse_shared_residual_stage_calls_separate':20,
            'new_source_fits':0,'new_C0_fits':0,'new2025inference':0,'new_submissions':0},
        'limits':parent['limits']+['Common line/peril mixture qfor both components is an assumption, not a row-specific physical observation model.',
            'Conditional bootstrap on saved sources/reporting and adaptive2023/2024does not incorporate complete fitting/selection uncertainty. No professional independent validation.'],
        'sources':sources,'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P55registra la evaluación completa de la mezcla estándar P54antes de ajustar: componentes A1S/T2bcon calibraciones separadas, pesos aritméticos fijos50/50y residual común posterior. Quince aprendices primarios y15adversos (30+30componentes y20+20etapas residuales), mismos cincofolds globales/ambos años/tres ramos. Calendario una vez, reporte propio P50común y normalizadores de último antes de multiplicar por q. Se reutilizan escenarios P52por SHA, sin reestimar curvas ni árboles. Mismos mínimos/IC/folds/años/Post31/celdas/nivel/NB/broker/historia cero/familia16; ningún rescate por ramo o mezcla seleccionada. Si falla combinado basta para no admitir; si pasa, transferencia condicional propia obligatoria antes de producir CSV. Cero fuente nueva, C0, inferencias2025o envíos. B00/F3c/adversos conservados,2024abierto adaptativo y privada prioritaria. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'P55registered_before_real_learning_or_score','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':m.q.post(body,'COD-S2-20261027-PRIVADA-P55-MEZCLA-PREVIO','P55: mezcla fija completa, guardas intactas antes de ajustar')}
    dump(OUT/'registration.json',receipt);dump(INDEX,receipt);print(json.dumps(receipt))


def component_level_math(train,a):
    checks={}
    for name,obj in a['components'].items():
        f=k.component_frame(train,'annual_'+name);value=np.exp(f.log_relative_A1S.to_numpy())*f.e_cost_scope.to_numpy()
        for shape in obj['shape']:value=k.core.b.shape_apply(f,value,shape)
        numerator=math.fsum((f.T0.to_numpy()/np.sqrt(value)).tolist());denominator=math.fsum(np.sqrt(value).tolist())
        moment=numerator/denominator;assert math.isclose(moment,obj['level'],rel_tol=3e-12)
        checks[name]={'scalar_moment_level':moment,'artifact_level':obj['level']}
    return checks


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);m.check_sources(plan)
    assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    if not (OUT/'started.json').exists():dump(OUT/'started.json',{'author':'Codex','utc':utc(),'pid':os.getpid()})
    parts=[];counts=Counter()
    for outer in range(5):
        curves=w.read(m.REPORTING/f'outer{outer}/cost_curves.json')
        for line in m.q.LINES:
            folder=OUT/f'{line}_{outer}';folder.mkdir(exist_ok=True)
            if (folder/'committed.json').exists():
                saved=w.read(folder/'committed.json');assert all(w.sha(ROOT/p)==v for p,v in saved['outputs'].items())
                parts.append(pd.read_parquet(folder/'prices.parquet'));counts.update(saved['constants']);continue
            f=k.frame_for(line,outer);a=m.once(folder,'learning',lambda:k.learn(f,line));counts.update(k.constant_counts(a))
            bad=f.copy();bad.loc[bad.is_held,['T0','reserve']]=-1e30
            adverse=m.once(folder,'adverse_learning',lambda:k.learn(bad,line));assert a==adverse
            held=f.loc[f.is_held].copy();u,norm=k.forward(held,a,True)
            bad.loc[bad.is_held,'q_paired']=np.nan;other,nn=k.forward(bad.loc[bad.is_held],adverse,True)
            assert np.array_equal(u,other) and norm==nn
            math_checks=component_level_math(f.loc[~f.is_held],a)
            out=held[['row_id','line','year','new_business','fold','group_id','T0']].copy();out['ultimate']=u;out['new_nominal']=u*held.q_paired.to_numpy()
            perils=m.q.PERILS[line];share_map=w.read(m.REPORTING/f'outer{outer}/mixtures_{line}.json')['target_training_only']
            shares=np.array([share_map[p] for p in perils]);assert np.allclose(m.apply_q(held,curves,perils,shares),held.q_paired,rtol=2e-12,atol=1e-13)
            for name in ['RESERVE075','RESERVE125']:
                q=pd.read_parquet(SCENARIO/f'{name}_{line}_{outer}_q.parquet').set_index('row_id').loc[held.row_id,'q'].to_numpy()
                out[name+'_new']=u*q
            for name,tail in [('TAIL005',.05),('TAIL010',.1)]:out[name+'_new']=u*m.apply_q(held,curves,perils,shares,tail)
            out.to_parquet(folder/'prices.parquet',index=False);parts.append(out)
            dump(folder/'committed.json',{'line':line,'outer':outer,'constants':k.constant_counts(a),'ultimate_normalizers':norm,
                'held_label_and_q_ultimate_invariant':True,'independent_component_level_checks':math_checks,
                'outputs':{w.rel(p):w.sha(p) for p in folder.iterdir() if p.is_file()}})
    ref=pd.read_parquet(m.REF);f=pd.concat(parts);assert f.row_id.is_unique and set(f.row_id)==set(ref.row_id)
    f=f.set_index('row_id',drop=False).loc[ref.row_id].reset_index(drop=True)
    for name in ['row_id','line','year','new_business','fold','group_id','T0']:assert np.array_equal(f[name],ref[name])
    f['old_nominal']=ref.old_nominal.to_numpy()
    reserve=pd.concat([pd.read_parquet(m.P1/f'canonical_{line}.parquet',columns=['row_id','reserve']) for line in m.q.LINES]).set_index('row_id').loc[f.row_id,'reserve'].to_numpy()
    y=f.T0.to_numpy(float);ys=[y,y-.25*reserve,y+.25*reserve,y,y];data=[(y,f.old_nominal.to_numpy(),f.new_nominal.to_numpy())]
    for j,name in enumerate(m.e.NAMES[1:],1):f[name+'_old']=ref[name+'_old'].to_numpy();data.append((ys[j],f[name+'_old'].to_numpy(),f[name+'_new'].to_numpy()))
    f.to_parquet(OUT/'POOLED_prices.parquet',index=False)
    weights=pd.read_parquet(BASE/'estimando_cartera2025_v3/weights.parquet').set_index('row_id').loc[f.row_id]
    assert np.array_equal(weights.group_id,f.group_id)
    metrics=m.e.metrics(f,data,'POOLED',weights.weight.to_numpy(float),plan);cohorts=m.cohort_analysis();a=metrics['NOMINAL'];crit=plan['criteria']
    gates={'pooled_delta_ge002':a['delta']>=crit['nominal_pooled_delta_min'],'pooled_lower95_positive':a['bootstrap95'][0]>0,
        'pooled_atleast4positive_folds':sum(v>0 for v in a['folds'].values())>=4,'both_pooled_years_nonnegative':min(a['years'].values())>=0,
        'pooled_post31_nonnegative':a['post31_delta']>=0,'all_nominal_and_stress_cell_floors':all(v['worst_cell_delta']>=-.001 for v in metrics.values())}
    passed=all(gates.values()) and all(cohorts['gates'].values());m.check_sources(plan)
    report={'author':'Codex','utc':utc(),'status':'P55pooled_complete_transfer_unmeasured','plan_sha256':w.sha(PLAN),
        'results':{'POOLED':metrics,'TRANSFER':None},'pooled_gates':gates,'pooled_cohort_gates':cohorts['gates'],
        'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,'all_required_gates_pass':False,
        'decision':'TRANSFER_REQUIRED_BEFORE_ADMISSION' if passed else 'REJECT_FROM_POOLED_FAILURE_TRANSFER_UNEVALUATED',
        'primary_whole_learners':15,'adverse_whole_learners_separate':15,'primary_components':30,'adverse_components_separate':30,
        'primary_shared_residual_stages':20,'adverse_shared_residual_stages_separate':20,'primary_constants':dict(counts),
        'new_source_fits':0,'new_C0_fits':0,'new2025inference':0,'new_submissions':0,'adopted':False,'2024_open':True,'goal_achieved':False}
    dump(OUT/'report.json',report);print(json.dumps({'decision':report['decision'],'nominal':{p:a[p] for p in ['delta','bootstrap95','post31_delta','worst_cell_delta']},'gates':gates,'cohort_gates':cohorts['gates']}))


def replay():
    assert not (OUT/'replay_report.json').exists();plan=w.read(PLAN);m.check_sources(plan);report=w.read(OUT/'report.json')
    def reject(*a,**kw):raise AssertionError('P55replay blocks all learning and report fits')
    for module,name in [(k,'learn'),(k.core,'fit_component'),(k.core.b,'shape_fit'),(k.core.b,'cell_levels'),
        (k.core.b,'factor'),(k.g,'fit_stage'),(m.q,'cost_curves')]:setattr(module,name,reject)
    for outer in range(5):
        for line in m.q.LINES:
            folder=OUT/f'{line}_{outer}';saved=w.read(folder/'committed.json')
            assert all(w.sha(ROOT/p)==v for p,v in saved['outputs'].items())
            f=k.frame_for(line,outer);f.loc[f.is_held,['T0','reserve']]=1e30;f.loc[f.is_held,'q_paired']=np.nan
            u,norm=k.forward(f.loc[f.is_held],w.read(folder/'learning.json'),True)
            assert np.array_equal(u,pd.read_parquet(folder/'prices.parquet').ultimate) and norm==saved['ultimate_normalizers']
    totals,desc,_,_=m.cohort_blocks();weights=np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    draws=np.load(OUT/'cohort_bootstrap.npy');cohorts=w.read(OUT/'cohort_report.json')
    assert np.allclose(m.cohort_scores(weights@totals),draws[:4],rtol=2e-12,atol=2e-13)
    for j,z in enumerate(cohorts['comparisons']):
        assert desc[j]['delta']==z['delta'] and np.array_equal(np.quantile(draws[:,j],[.025/16,1-.025/16]),z['family16_band95'])
    draws=np.load(OUT/'POOLED_joint_bootstrap.npy')
    for j,name in enumerate(m.e.NAMES):assert np.array_equal(np.quantile(draws[:,j],[.025,.975]),report['results']['POOLED'][name]['bootstrap95'])
    m.check_sources(plan);dump(OUT/'replay_report.json',{'author':'Codex','utc':utc(),'report_sha256':w.sha(OUT/'report.json'),
        'all15whole_member_flows_exact':True,'all_learning_and_report_fits_blocked':True,'held_q_not_used_by_ultimate':True,
        'saved_intervals_and_first4weights_exact':True,'new_fits':0,'new_resampling':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'replay':'exact','whole_members':15,'components':30,'new_fits':0,'new_resampling':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json')
    assert w.read(OUT/'replay_report.json')['report_sha256']==w.sha(OUT/'report.json')
    passed=d['all_pooled_gates_pass'];a=d['results']['POOLED']['NOMINAL'];number=sum(d['primary_constants'].values())
    next_unit=('Prepare OWNconditional-transfer2023training reporting/target inputs for this exact fixed-half complete model. Frozen A1S/T2bsource-only coefficients need no new fits; retain source2024conditional limitation. Register cost/config/criterion/forum before learning. A pooled pass alone never admits production or upload.' if passed else
        'Use the NEW P55saved global/cell/cohort loss and parameters to identify one concrete unresolved mechanism before further fitting. Fixed-half mixture and source controls remain preserved, no selected weights/lines or oracle-level rescue. Do not repeat P49/P53or refit source/reporting on unchanged data. Full/private admission still missing; no public probe.')
    text='# P55: evaluación completa de la mezcla estándar fija\n\nCodex, '+utc()+'. '+('El combinado supera todas las guardas aplicables; falta transferencia propia antes de admitir.' if passed else 'El combinado no supera las guardas; se conserva sin admitir para envío. La transferencia no fue evaluada.')+'\n\n'
    text+=f"ΔD²nominal={a['delta']:+.7f}; IC95por grupos=[{a['bootstrap95'][0]:+.7f}; {a['bootstrap95'][1]:+.7f}]; Post31={a['post31_delta']:+.7f}; peor celda={a['worst_cell_delta']:+.7f}.\n\n"
    text+='Se ajustaron15aprendices completos primarios y15adversos:30+30calibraciones de componentes y20+20etapas residuales. Pesos fijos50/50sin selección por ramo. Cada componente recibió sus formas y niveles entrenados antes de la mezcla; después se aplicó el residual común. El calendario entra una vez, el avance a último conserva sus normalizadores propios y solo después se multiplica por qpropio. El qcomún por ramo sigue siendo un supuesto, sin composición por peril por fila acreditada.\n\n'
    text+='Guardas globales: '+json.dumps(d['pooled_gates'])+'. Cohortes: '+json.dumps(d['pooled_cohort_gates'])+'. Se conservaron todos los escenarios/celdas/años/folds, influencia y nivel. Los escenarios mantienen precios últimos nominales, sin afirmar reentrenamiento completo. Transferencia=None, sin aprobación inventada.\n\n'
    text+=f'Constantes primarias nuevas:{number};30niveles óptimos comprobados por sumas escalares independientes y15replays exactos con aprendizaje bloqueado. No hubo nuevos árboles, C0, inferencias2025o envíos. B00/F3c y todas las alternativas se conservan.2024es desarrollo adaptativo; la fuente2024condicional, cola/reservas, maestros sin fecha y búsqueda adaptativa limitan la generalización. No es revisión profesional independiente ni mejora privada acreditada.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
        'document':w.rel(DOC),'decision':d['decision'],'nominal':{p:a[p] for p in ['delta','bootstrap95','post31_delta','worst_cell_delta']},
        'all_pooled_gates_pass':passed,'conditional_transfer_gate':None,'primary_whole_learners':15,'adverse_whole_learners_separate':15,
        'primary_components':30,'adverse_components_separate':30,'primary_shared_residual_stages':20,'adverse_shared_residual_stages_separate':20,
        'new_primary_constants':number,'new_source_fits':0,'new_C0_fits':0,'new2025inference':0,'new_submissions':0,
        'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':m.q.post(body,'COD-S2-20261027-PRIVADA-P55-MEZCLA-RESULTADO','P55: resultado completo de mezcla fija, transferencia explícitamente pendiente')}
    archive=R/'privado'/('corte_P55_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    count_path=R/'registro/semana2_contadores_propios_actual.json';counts=w.read(count_path);assert 'phase2_private_P55_fixed_mixture' not in counts
    w.update(count_path,{'cumulative_closed_form_constants':counts['cumulative_closed_form_constants']+number,'phase2_private_P55_fixed_mixture':receipt},archive)
    w.update(INDEX,receipt,archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json',{'private_P55':receipt,'next_unit':next_unit},archive)
    w.update(R/'registro/semana2_mision_privada_actual.json',{'P55':receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P55=receipt,next_unit=next_unit)
    w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P55: validación de mezcla estándar fija\n\nCodex, '+receipt['utc']+'.Decisión='+receipt['decision']+f';15aprendices primarios/15adversos,{number}constantes, replay exacto. Cero árboles/C0/inferencias2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_fixed_mixture_validation_index':w.rel(INDEX),'week_2_private_fixed_mixture_validation_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'decision':d['decision'],'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','run','replay','close']);args=p.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'replay':replay,'close':close}[args.mode]()
