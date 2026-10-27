"""Control de fuente A1S frente a A1R bajo el mismo destino P52, sin cambiar receta."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import argparse
import json
import math
import os
from collections import Counter
import sys

R=Path(__file__).resolve().parents[1]; ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p53_matched_target_kernel',R/'herramientas/validar_A1R_destino_P52.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
w=m.w; np=m.np; pd=m.pd; BASE=m.BASE
PARENT=m.OUT; OLD_SOURCE=BASE/'A1S_nucleo_20261026_v1/source_models'
OUT=BASE/'P53_control_fuente_20261027'
PLAN=R/'registro/semana2_control_fuente_privada_plan.json'; INDEX=R/'registro/semana2_control_fuente_privada_actual.json'
DOC=R/'docs/semana2/PRIVADA_P53_CONTROL_FUENTE_DESTINO_COMUN.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return m.dump(path,value)


def frame_for(line,outer):
    f=m.frame_for(line,outer)
    z=pd.read_parquet(OLD_SOURCE/f'target_{line}_three_seed_components.parquet',columns=['row_id','log_relative_A1S'])
    z=z.loc[z.row_id.isin(set(f.row_id))].set_index('row_id')
    assert z.index.is_unique and set(z.index)==set(f.row_id)
    f['annual_paired']=np.exp(z.loc[f.row_id,'log_relative_A1S'].to_numpy(float))
    assert f.year.isin([2023,2024]).all() and f.annual_paired.gt(0).all();return f


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    prior=w.read(PARENT/'report.json');assert prior['decision']=='REJECT_FROM_POOLED_FAILURE_TRANSFER_UNEVALUATED'
    assert w.read(PARENT/'replay_report.json')['report_sha256']==w.sha(PARENT/'report.json')
    paths=[Path(__file__),Path(m.__file__),Path(m.p.__file__),Path(m.p.b.__file__),Path(m.p.g.__file__),
        PARENT/'report.json',PARENT/'replay_report.json',PARENT/'completion_receipt.json',PARENT/'POOLED_prices.parquet',
        m.PLAN,m.INDEX,OLD_SOURCE/'report.json',R/'registro/semana2_mision017_A1S_fuente_plan_v1.json']
    parent=w.read(m.PLAN);sources=dict(parent['sources'])
    for line in m.q.LINES:paths.append(OLD_SOURCE/f'target_{line}_three_seed_components.parquet')
    sources.update({w.rel(p):w.sha(p) for p in paths})
    # The parent's live index is status, not a numerical dependency; do not lock later tracking changes.
    sources.pop(w.rel(m.INDEX),None)
    OUT.mkdir();plan={'author':'Codex','utc':utc(),
        'question':'Does P52loss persist with the previous source-safe A1Srelative risk under exactly the same calendar/P50reporting and P47closed target calibrator?',
        'need':'P52fails all5folds and bothyears, including +/-5percent same-level sensitivity. It changed the source and removed the original T2bmixture/nested corrections. A matched source control is needed before blaming reporting or adding capacity.',
        'single_change':'Replace only exp(P51own-outer log_relative_A1R) with the saved original3seed source-only log_relative_A1S. Same109296historical rows, groups, outer training keys, P50q, calendar, T0and P47NCB/priorK300,businessK400,residualK300. No tree refit, new inference, C0refit or selected blend.',
        'design':'15primary closed target calibrators and15held-label-poison controls. Save invocations/results, reload all15ultimate flows with learning blocked. Compare A1R/control/reference in every12line-year-business cell, all5folds, bothyears and global. No cherry-picking ramos.',
        'interpretation':'This is component diagnosis, not an admitted delivery. Primary contrast is deltaA1RminusControl=(lossControl-lossA1R)/common null. Remaining control-reference gap includes architecture AND observation changes; it cannot identify either separately. No causal actuarial or hidden-private claim.',
        'decision_before_results':'A control below the unchanged +.002global improvement minimum cannot admit a candidate. Even a positive control point would require full original scenario/cohort/transfer/uncertainty gates in a separately registered whole-algorithm evaluation. If A1Rbeats this control but both trail reference, retain its source and review the missing fixed T2b50/50mixture before any capacity increase. Otherwise review source observation differences, without tuning to held labels or public scores.',
        'budget':{'primary_closed_learners':15,'adverse_closed_learners_separate':15,'new_source_fits':0,'new_C0_fits':0,'new_bootstraps':0,'new2025inference':0,'new_submissions':0},
        'sources':sources,'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P53registra un control de mecanismo antes de otros ajustes: sustituir solo la fuente A1Rpor la A1Ssegura ya guardada, con exactamente los mismos grupos, reporte P50/calendario y calibrador cerrado P47del P52fallido. Quince aprendices primarios y15adversos; todas las celdas/folds/años, replay con aprendizaje bloqueado. El contraste controlado separa el cambio de fuente; el resto frente a referencia todavía mezcla arquitectura y observación, sin explicación causal. No es candidato admitido ni búsqueda de pesos/ramo. Cero árboles, C0, remuestreo, inferencias2025o envíos. Mantengo B00/F3c/adversos,2024abierto adaptativo y prioridad privada. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    d={'author':'Codex','utc':utc(),'status':'P53registered_before_matched_control_learning','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':m.q.post(body,'COD-S2-20261027-PRIVADA-P53-FUENTE-PREVIO','P53: control de fuente bajo un mismo modelo de destino')}
    dump(OUT/'registration.json',d);dump(INDEX,d);print(json.dumps(d))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    assert all(w.sha(ROOT/k)==v for k,v in plan['sources'].items());parts=[];counts=Counter()
    if not (OUT/'started.json').exists():dump(OUT/'started.json',{'author':'Codex','utc':utc(),'pid':os.getpid()})
    for outer in range(5):
        for line in m.q.LINES:
            folder=OUT/f'{line}_{outer}';f=frame_for(line,outer)
            def learning(data):
                a=m.p.learn(data,line);a['contract']='P53matched_A1S_source_P52target';return a
            a=m.once(folder,'learning',lambda:learning(f));counts.update(m.p.constant_counts(a))
            bad=f.copy();bad.loc[bad.is_held,['T0','reserve']]=-1e30
            adverse=m.once(folder,'adverse_learning',lambda:learning(bad));assert a==adverse
            held=f.loc[f.is_held];u,norm=m.p.forward(held,a,True)
            result=held[['row_id','line','year','new_business','fold','group_id','T0']].copy();result['ultimate']=u;result['control']=u*held.q_paired.to_numpy()
            result.to_parquet(folder/'prices.parquet',index=False)
            if not (folder/'applied.json').exists():dump(folder/'applied.json',{'normalizers':norm})
            else:assert w.read(folder/'applied.json')['normalizers']==norm
            parts.append(result)
    reference=pd.read_parquet(PARENT/'POOLED_prices.parquet');combined=pd.concat(parts).set_index('row_id',drop=False).loc[reference.row_id].reset_index(drop=True)
    assert combined.row_id.is_unique and len(combined)==len(reference)
    for key in ['row_id','line','year','new_business','fold','group_id','T0']:assert np.array_equal(combined[key],reference[key])
    combined['A1R']=reference.new_nominal.to_numpy();combined['reference']=reference.old_nominal.to_numpy();combined.to_parquet(OUT/'prices.parquet',index=False)
    def reject(*a,**kw):raise AssertionError('P53replay forbids learning')
    for module,key in [(m.p,'learn'),(m.p.b,'shape_fit'),(m.p.b,'factor'),(m.p.b,'cell_levels'),(m.p.g,'fit_stage'),(m.q,'cost_curves')]:setattr(module,key,reject)
    for outer in range(5):
        for line in m.q.LINES:
            folder=OUT/f'{line}_{outer}';f=frame_for(line,outer);f.loc[f.is_held,['T0','reserve']]=1e30
            u,norm=m.p.forward(f.loc[f.is_held],w.read(folder/'learning.json'),True)
            assert np.array_equal(u,pd.read_parquet(folder/'prices.parquet').ultimate) and norm==w.read(folder/'applied.json')['normalizers']
    results=[];scopes=[('GLOBAL',combined)]
    scopes += [(f'{line}|{year}|NB{int(nb)}',combined.loc[ix]) for (line,year,nb),ix in combined.groupby(['line','year','new_business']).groups.items()]
    scopes += [('FOLD'+str(k),combined.loc[combined.fold.eq(k)]) for k in range(5)]
    scopes += [('YEAR'+str(k),combined.loc[combined.year.eq(k)]) for k in [2023,2024]]
    for label,z in scopes:
        y=z.T0.to_numpy(float);den=m.e.unit(y,np.full(len(y),y.mean())).sum()
        loss={key:float(m.e.unit(y,z[key].to_numpy(float)).sum()) for key in ['control','A1R','reference']}
        from sklearn.metrics import mean_tweedie_deviance
        assert math.isclose(loss['control']/len(z),mean_tweedie_deviance(y,z.control,power=1.5),rel_tol=1e-12,abs_tol=1e-10)
        results.append({'scope':label,'rows':len(z),'groups':int(z.group_id.nunique()),'delta_control_vs_reference':(loss['reference']-loss['control'])/den,
            'delta_A1R_vs_control':(loss['control']-loss['A1R'])/den,'delta_A1R_vs_reference':(loss['reference']-loss['A1R'])/den})
    assert len(results)==20 and math.isclose(results[0]['delta_A1R_vs_reference'],w.read(PARENT/'report.json')['results']['POOLED']['NOMINAL']['delta'],abs_tol=1e-12)
    assert all(w.sha(ROOT/k)==v for k,v in plan['sources'].items())
    report={'author':'Codex','utc':utc(),'status':'P53matched_source_control_complete','plan_sha256':w.sha(PLAN),'results':results,
        'primary_constants':dict(counts),'primary_learners':15,'adverse_learners_separate':15,'replay15exact_learning_blocked':True,
        'new_source_fits':0,'new_C0_fits':0,'new_resampling':0,'new2025inference':0,'new_submissions':0,'adopted':False,'private_improvement_established':False,'goal_achieved':False}
    dump(OUT/'report.json',report);print(json.dumps({'global':results[0],'new_constants':sum(counts.values()),'replay':'exact','new_submissions':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');assert d['plan_sha256']==w.sha(PLAN);a=d['results'][0]
    next_unit=('Review the missing fixed50/50T2bmixture and original whole-algorithm target architecture using existing source-safe building blocks; A1Rbeats matched A1Sbut is still below reference. Preregister a standard complete protected comparator, preserving every threshold and scenario/cohort/transfer guard before fitting. No source retraining or selected line/weight rescue.' if a['delta_A1R_vs_control']>0 and a['delta_control_vs_reference']<0 else
        'Review the matched-source effect and its saved cell/fold support before another recipe. Do not tune levels, lines, qcurves or weights to retained outcomes. No control point alone admits a delivery; preserve all fixed gates and require a concrete mechanism.')
    text='# P53: fuente comparada con el mismo modelo de destino\n\nCodex, '+utc()+'. Control A1Sfrente a referencia: ΔD²='+f"{a['delta_control_vs_reference']:+.7f}"+'. A1Rfrente a control A1S: '+f"{a['delta_A1R_vs_control']:+.7f}"+'. Se conservan20cortes: global,12celdas,5folds y2años.\n\n'
    text+='Se ajustaron15calibradores cerrados primarios y15adversos con iguales grupos, calendario, P50y P47; solo cambió la fuente. Los15replays son exactos con aprendizaje bloqueado. No se recalcularon árboles, C0o intervalos; estos puntos no acreditan generalización o admisión. La brecha restante todavía incluye observación y arquitectura, sin separar sus efectos. Cero inferencias2025o envíos. B00/F3c/adversos conservados,2024abierto adaptativo.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
        'document':w.rel(DOC),'global':a,'primary_learners':15,'adverse_learners_separate':15,'new_primary_constants':sum(d['primary_constants'].values()),'new_source_fits':0,
        'new_C0_fits':0,'new_submissions':0,'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':m.q.post(body,'COD-S2-20261027-PRIVADA-P53-FUENTE-RESULTADO','P53: resultado del control de fuente y siguiente mecanismo')}
    archive=R/'privado'/('corte_P53_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    path=R/'registro/semana2_contadores_propios_actual.json';c=w.read(path);assert 'phase2_private_P53_matched_source' not in c
    w.update(path,{'cumulative_closed_form_constants':c['cumulative_closed_form_constants']+receipt['new_primary_constants'],'phase2_private_P53_matched_source':receipt},archive)
    w.update(INDEX,receipt,archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json',{'private_P53':receipt,'next_unit':next_unit},archive)
    w.update(R/'registro/semana2_mision_privada_actual.json',{'P53':receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P53=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P53: control de fuente con destino fijo\n\nCodex, '+receipt['utc']+'.15aprendices primarios/15adversos, replay exacto; cero árboles/C0/remuestreo/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_matched_source_index':w.rel(INDEX),'week_2_private_matched_source_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'global':a,'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','run','close']);args=p.parse_args()
    with m.e.threadpool_limits(limits=2):{'prepare':prepare,'run':run,'close':close}[args.mode]()
