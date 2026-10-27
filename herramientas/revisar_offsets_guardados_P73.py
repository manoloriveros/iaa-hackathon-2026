"""Compara las entradas OOF actuales con su base exterior guardada, sin ajustar."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import math
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p73_existing_scope_inputs',R/'herramientas/validar_GLM_reporte_actual_P67.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
k=p.k;m=p.m;q=p.q;w=p.w;pd=p.pd;np=p.np;BASE=p.BASE
CONTROL=p.t.OUT;RAW=p.t.t.OUT;TREE=BASE/'P72_validacion_boosting_residual_20261027'
OUT=BASE/'P73_offsets_guardados_20261027'
PLAN=R/'registro/semana2_offsets_actuales_revision_plan.json';INDEX=R/'registro/semana2_offsets_actuales_revision_actual.json'
DOC=R/'docs/semana2/PRIVADA_P73_OFFSETS_Y_ESCALA.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)
def describe(values):
    z=np.asarray(values,float);assert np.isfinite(z).all()
    return {str(key):float(value) for key,value in zip([.01,.05,.5,.95,.99],np.quantile(z,[.01,.05,.5,.95,.99]))}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    assert w.read(TREE/'completion_receipt.json')['report_sha256']==w.sha(TREE/'report.json')
    parent=w.read(p.PLAN);m.check_sources(parent);p.verify_inputs()
    paths=[Path(__file__),Path(k.__file__),Path(k.g.__file__),Path(k.core.__file__),Path(k.core.b.__file__),p.PLAN,TREE/'report.json',TREE/'completion_receipt.json']
    for line in q.LINES:
        for outer in range(5):paths += [RAW/f'input_{line}_{outer}.parquet',CONTROL/f'{line}_{outer}/learning.json',CONTROL/f'{line}_{outer}/committed.json',CONTROL/f'{line}_{outer}/prices.parquet',TREE/f'{line}_{outer}/prices.parquet']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'NEW numeric comparison of current P67OOFtraining offsets vs saved fullouterP65base on SAMEtraining rows;15new base applications only. Saved P72held correction distribution, no tree applications or new loss/score.',
        'known_outcomes':'P67/P70/P72failures and native integrity already known. The existing stage normalizer is intentionally batch-dependent for motor/contents, while buildings has no such residual stages. Reuse this code fact, do not repeat a general bridge/projectivity suite or claim it explains buildings failure.',
        'questions':['How much do actual whole-base and qinputs differ between64percent inner and80percent outer training? These are different estimators/scopes, not known error or causal evidence.',
            'Are fixed P72corrections near the registered step bound? Describe only, never increase depth/round/step after failure.'],
        'configuration':{'ratio_percentiles':[.01,.05,.5,.95,.99],'rows':'All15outertraining scopes; exact raw source/row/year/group/calendar/business identity before application.',
            'applications':'FullouterP65model on own training rows, with T0/reserve removed and qpoisoned before ultimate. Do not fit a stacker on these in-sample outputs: descriptive comparison ONLY.',
            'comparison':'Full-training ultimate/OOFultimate, fullq/innerq and observed ratio factorization; actual fulltrain vs saved held ultimate residual normalizers. No new price score, group deletion or significance.',
            'tree_description':'Saved P72ultimate/P65ultimate rawlogcorrection, fraction >=99percent of registered absolute.192bound; fixed descriptive threshold, no candidate tuning.'},
        'criterion':'Source/key/group/calendar identities, saved model SHAand fitrowdigest, independent scalar ratio factorization. Describe model-size/normalizer differences without diagnosing causality or choosing individual fields.',
        'budget':{'new_fits':0,'new_CDF_fits':0,'new_resampling':0,'new_historical_base_applications':15,'new_scores':0,'new2025inference':0,'new_submissions':0},
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'2024_open':True,'B00_all_alternatives_preserved':True}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P73registra una comparación numérica nueva de inputsOOFP67frente a base exteriorP65aplicada SOLOa su propio entrenamiento:15aplicaciones históricas, sin ajustar o entrenar stacker sobre ellas. Fuentes/filas/grupos/calendario idénticos, ratioúltimo*qycontraste de normalizadores reales; se retiran etiquetas/qantes del último. Buildingsno tiene etapas residuales dependientes de lote, por lo que esa propiedad no explica por sí sola sus pérdidas. Distribución de correccionesP72desde artefactos guardados, sin aumentar paso/rondas/depth. Cero nuevos scores, curvas, remuestreo,2025o envíos; no causalidad u óptimo privado. B00preservado y2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P73registered_before_new_offset_comparison','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P73-OFFSET-PREVIO','P73: entradas cruzadas y escala actual, sin reentrenar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);m.check_sources(plan);p.verify_inputs();assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    def reject(*args,**kwargs):raise AssertionError('P73cannot fit')
    k.learn=reject;k.core.fit_component=reject;k.g.fit_stage=reject;q.cost_curves=reject;p.u.reporting=reject
    results=[]
    for line in q.LINES:
        for outer in range(5):
            raw=pd.read_parquet(RAW/f'input_{line}_{outer}.parquet');full=raw.loc[~raw.is_held].copy()
            cross=p.frame_for(line,outer);cross=cross.loc[~cross.is_held].set_index('row_id').loc[full.row_id]
            for name in ['year','group_id','new_business','exposure_calendar','annual_A1S','annual_T2b']:assert np.array_equal(full[name],cross[name]),name
            folder=CONTROL/f'{line}_{outer}';saved=w.read(folder/'committed.json');assert all(w.sha(ROOT/path)==value for path,value in saved['outputs'].items())
            model=w.read(folder/'learning.json');assert model['fit_row_ids_digest']==m.p.b.digest(sorted(full.row_id))
            clean=full.drop(columns=['T0','reserve']);clean['q_paired']=np.nan
            value,norm=k.forward(clean,model,True)
            ultimate_ratio=value/cross.baseline_ultimate.to_numpy(float);qratio=full.q_paired.to_numpy(float)/cross.q_paired.to_numpy(float)
            observed_ratio=value*full.q_paired.to_numpy(float)/cross.baseline_observed.to_numpy(float)
            assert np.allclose(observed_ratio,ultimate_ratio*qratio,rtol=2e-14)
            for pos in np.linspace(0,len(full)-1,17,dtype=int):assert math.isclose(float(observed_ratio[pos]),float(ultimate_ratio[pos])*float(qratio[pos]),rel_tol=2e-14)
            base=pd.read_parquet(folder/'prices.parquet',columns=['row_id','ultimate']).set_index('row_id')
            pred=pd.read_parquet(TREE/f'{line}_{outer}/prices.parquet',columns=['row_id','ultimate']).set_index('row_id').loc[base.index]
            logcorrection=np.log(pred.ultimate.to_numpy()/base.ultimate.to_numpy());assert np.max(np.abs(logcorrection))<=.192+1e-10
            results.append({'line':line,'outer':outer,'training_rows':len(full),'full80_vs_OOF64_ultimate_ratio':describe(ultimate_ratio),
                'full_vs_inner_qratio':describe(qratio),'full_vs_OOF_observed_ratio':describe(observed_ratio),'sd_log_ultimate_ratio':float(np.std(np.log(ultimate_ratio))),
                'residual_stages':k.g.STAGES[line],'whole_training_ultimate_normalizers':norm,'held_ultimate_normalizers':saved['ultimate_normalizers'],
                'P72held_log_correction':describe(logcorrection),'P72fraction_at99percent_absolute_bound':float(np.mean(np.abs(logcorrection)>=.99*.192))})
    m.check_sources(plan);p.verify_inputs();dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P73new_current_offset_comparison_complete','results':results,
        'interpretation':'Differences are actual estimator/scope/batch differences, not known measurement error, proved source of failure or an admission. Buildings have no residual batch normalizers, so a universal batch-centering diagnosis is false.',**plan['budget']})
    print(json.dumps({'complete':True,'scopes':len(results),'ratios':[{'line':z['line'],'outer':z['outer'],'ultimate_ratio':z['full80_vs_OOF64_ultimate_ratio'],'qratio':z['full_vs_inner_qratio']} for z in results]}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');m.check_sources(w.read(PLAN));p.verify_inputs()
    next_unit='P74: investigate a simpler SINGLEtargetGLMwith exposure/currentqand PUREdeveloped-only risk inputs (e.g.T2bannual offset plus A1Ssignal and existing rating covariates), removing noisy target-derived base offsets rather than stacking on in-sample parents or adding capacity. Not yet a recipe: verify source/units, freeze all fields/criterion/cost, synthetic full flow and forum before real fitting. Preserve all failed recipes; no alpha/step/line or public-score rescue.'
    text='# P73: entradas OOF y escala de aplicación\n\nCodex, '+utc()+'. Se compararon15ámbitos actuales por claves/fuentes/grupos/calendario idénticos, aplicando la base exterior guardada solo a su propio entrenamiento y sin ajustar modelos. Sus etiquetas/reservas se retiraron y qse anuló antes del último. Estas salidas de entrenamiento no se usan para entrenar un stacker.\n\n'
    text+='| Ramo | Fold | Ratio último full/OOF p01 | Mediana | p99 | SD logratio |\n|---|---|---|---|---|---|\n'
    for z in d['results']:
        a=z['full80_vs_OOF64_ultimate_ratio'];text+=f"| {z['line']} | {z['outer']} | {a['0.01']:.4f} | {a['0.5']:.4f} | {a['0.99']:.4f} | {z['sd_log_ultimate_ratio']:.4f} |\n"
    text+='\nLas diferencias son de estimadores/ámbitos64%/80%yde normalizadores, sin verdad de error conocida o causalidad establecida. Se verificó por otro cálculo ratioobservado=ratioultimo*ratioq. Motor/contentsusan etapas residuales centradas por lote; buildingscarece de ellas, así que esa propiedad no explica universalmente sus pérdidas. Se conserva la distribución P72desde precios guardados sin elegir más paso/profundidad/rondas.\n\n'
    text+='Cero nuevos ajustes, curvas, remuestreo, scores,2025o envíos. No hay CSVadmitido, eliminación de grupos o selección de campos por resultados. B00/F3cyalternativas conservados,2024abierto adaptativo y límites de transporte/cola/reservas/fuente2024condicional/maestros presentes; sin mejora privada acreditada o revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        **w.read(PLAN)['budget'],'2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P73-OFFSET-RESULTADO','P73: escala OOF actual y siguiente mecanismo sencillo')}
    archive=R/'privado'/('corte_P73_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P73'),(R/'registro/semana2_mision_privada_actual.json','P73')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P73=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P73: escala de los offsets actuales\n\nCodex, '+receipt['utc']+'.15aplicaciones históricas a entrenamiento, cero ajuste/remuestreo/scoring/envíos; sin prueba causal. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_current_offset_review_index':w.rel(INDEX),'week_2_private_current_offset_review_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
