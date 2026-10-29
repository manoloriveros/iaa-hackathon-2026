"""Inspección de árboles P90 guardados, sin predecir o volver a ajustar."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p91_saved_tree_tools',R/'herramientas/preparar_boosting_prior_calibrado_P89.py')
k=importlib.util.module_from_spec(s);s.loader.exec_module(k)
m=k.m;q=k.q;w=k.w;np=k.np;BASE=k.BASE
SOURCE=BASE/'P90_validacion_boosting_prior_20261027';GLM=BASE/'P88_validacion_prior_calibrado_20261027'
OUT=BASE/'P91_limites_arbol_guardado_20261027'
PLAN=R/'registro/semana2_limites_arbol_guardado_revision_plan.json';INDEX=R/'registro/semana2_limites_arbol_guardado_revision_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P91_LIMITES_ARBOL_GUARDADO.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert phase['P90_execution']['state']=='TERMINAL_SUCCESS' and not phase.get('active_jobs') and not phase.get('active_execution')
    assert w.read(SOURCE/'completion_receipt.json')['report_sha256']==w.sha(SOURCE/'report.json')
    paths=[Path(__file__),Path(k.__file__),Path(k.t.__file__),SOURCE/'report.json',SOURCE/'completion_receipt.json',GLM/'report.json']
    for line in q.LINES:
        for outer in range(5):paths += [SOURCE/f'{line}_{outer}/learning.json',GLM/f'{line}_{outer}/learning.json']
    parent=w.read(k.PLAN);OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'ONLYNEWP90saved tree structure/leaf-bound pressure and exact P88prior/preprocess identity; no inference, fit, new score or repeated source/support suite.',
        'configuration':{'all_models':'ALL15line/outermodels, no field/fold/tree selection. Deserialize native model ONLYto dump structure; predict/native training and level estimators blocked.',
            'same_input_path':'Compare entire persisted prior_level_calibration and preprocess dictionaries against P88for every same scope. No recalibration or featurematrix applications.',
            'leaf_pressure':'Fraction of leaf PARAMETERS with abs(value)>=learning_rate*max_delta_step-1e-12, both alltrees and last16trees. This is NOTfraction of rows/claims or a derivative/significance test.',
            'train_bound':'Use stored actual_max_absolute_train_log_correction, compare to64*.003within1e-10. No trainingforward replay or fresh gradient/price.',
            'held_cells':'Copy ALLexisting P90/P88cells only, do not score prefixes/other rounds or select fittinglength from outer/public data.'},
        'criterion':'Native dump leafcounts match saved artifact counts; scalar-loop and vector clip counts agree; all numeric prior/preprocess objects exactlysame as P88. Treat pressure as descriptive, no proof extra rounds generalize.',
        'budget':{'native_model_deserializations_for_structure':15,'new_model_predictions':0,'new_real_fits':0,'new_CDF_fits':0,'new_scores':0,'new_resampling':0,'new2025inference':0,'new_submissions':0},
        'runtime_sources':parent['runtime_sources'],'sources':{w.rel(path):w.sha(path) for path in paths},'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P91 registra revisión nueva de TODOSlos15árbolesP90guardados: presión del paso máximo por parámetros de hoja, últimos16árboles y cota de corrección de entrenamiento YAguardada. Sin predecir, ajustar, puntuar otros números de rondas o repetir fuentes/soportes. Se comparan prior/preproceso completos contraP88en los mismos ámbitos para comprobar el cambio de estimador real. Fracción de hojas no es fracción de filas/claims o prueba de influencia/convergencia; saturación no demuestra beneficio de más rondas. Cualquier selección posterior tendría que aprender longitud SOLOen train con sus reportes internos propios, registro y flujo sintético antes de ajustar. B00/adversos preservados,2024abierto adaptativo, ceroenvíos. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P91registered_before_saved_tree_bound_review','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P91-LIMITES-PREVIO','P91: límites de los árboles guardados, sin nuevas inferencias')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);k.check_sources(plan);assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    def reject(*args,**kwargs):raise AssertionError('P91forbids predictions and learning')
    k.t.lgb.Booster.predict=reject;k.t.lgb.train=reject;k.k.calibrate_levels=reject
    records=[]
    for line in q.LINES:
        for outer in range(5):
            a=w.read(SOURCE/f'{line}_{outer}/learning.json');b=w.read(GLM/f'{line}_{outer}/learning.json')
            assert a['prior_level_calibration']==b['prior_level_calibration'] and a['preprocess']==b['preprocess']
            model=k.t.lgb.Booster(model_str=a['model_string']);trees=model.dump_model()['tree_info'];values=[k.t.leaf_values(tree['tree_structure']) for tree in trees]
            cap=a['parameters']['learning_rate']*a['parameters']['max_delta_step'];all_values=[z[0] for values0 in values for z in values0];late=[z[0] for values0 in values[-16:] for z in values0]
            assert len(all_values)==a['fitted_leaf_values']
            total=sum(abs(v)>=cap-1e-12 for v in all_values);assert total==int(np.count_nonzero(np.abs(all_values)>=cap-1e-12))
            clipped_late=sum(abs(v)>=cap-1e-12 for v in late);bound=a['max_absolute_log_correction_bound']
            records.append({'line':line,'outer':outer,'effective_trees':len(trees),'fitted_leaf_values':len(all_values),'all_leaf_parameter_fraction_at_step_bound':total/len(all_values),
                'last16_leaf_parameter_fraction_at_step_bound':clipped_late/len(late),'stored_max_abs_train_logcorrection':a['actual_max_absolute_train_log_correction'],
                'stored_max_reaches_configured_train_bound':a['actual_max_absolute_train_log_correction']>=bound-1e-10,
                'prior_and_preprocess_exact_P88':True,'no_model_prediction':True})
    k.check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P91saved_native_tree_bound_and_prior_identity_complete','records':records,
        'all_saved_held_cells':{name:w.read(folder/'report.json')['results']['POOLED']['NOMINAL']['cells'] for name,folder in [('P90',SOURCE),('P88',GLM)]},
        'no_extra_round_generalization_or_causal_claim':True,**plan['budget']})
    print(json.dumps({'complete':True,'models':len(records),'train_bound_reached_models':sum(z['stored_max_reaches_configured_train_bound'] for z in records),
        'last16_clipped_parameter_fraction_range':[min(z['last16_leaf_parameter_fraction_at_step_bound'] for z in records),max(z['last16_leaf_parameter_fraction_at_step_bound'] for z in records)],'new_predictions':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');k.check_sources(w.read(PLAN))
    next_unit='P92: design/syntheticpreflight finite TRAINING-ONLYcommon tree-length selection on SAMEP90features/scalarprior/step/depth. Candidate budgets64/128/256, no depth/field/step search or outer/public prefix scoring. Reuse P84protected inner qtables bySHA, learn each inner prior/preprocess ONLYon its train; one max256fit can yield cached prefix models after synthetic equivalence to standalone64. Freeze selector/tie/cost and full poison/replay before real fits; all old outerguards/conditionaltransfer remain. Leaf pressure is motivation, not evidence longer wins.'
    text='# P91: límites de los árboles guardados\n\nCodex, '+utc()+'. Se inspeccionaron los15modelosP90sin predecir o ajustar. Sus priors de calibración y preprocesos coinciden exactamente conP88; no hubo un cambio oculto de entradas en la comparación del estimador final.\n\n'
    text+='| Ramo | Fold | Fracción de parámetros al paso máximo | Últimos16árboles | Máximo de entrenamiento llega a cota |\n|---|---:|---:|---:|---|\n'
    for z in d['records']:text+=f"|{z['line']}|{z['outer']}|{z['all_leaf_parameter_fraction_at_step_bound']:.4%}|{z['last16_leaf_parameter_fraction_at_step_bound']:.4%}|{z['stored_max_reaches_configured_train_bound']}|\n"
    text+='\nSon fracciones de parámetros de hoja, no de filas/siniestros ni una prueba de convergencia o influencia por eliminación. La corrección máxima de entrenamiento se reutiliza del recibo original; no se volvió a aplicar un modelo. Que haya pasos aún limitados no demuestra que más árboles mejoren el retenido o la privada.\n\n'
    text+='La opción siguiente es una selección interna finita de longitud con todo el aprendizaje protegido, no elegir rondas por resultados exteriores. Mantiene profundidad/hojas/paso/campos y compara64/128/256dentro del entrenamiento, con empate a menor longitud. Requiere presupuesto y preflight nuevos; no modifica o admiteP90. Cero ajustes, predicciones, scores, remuestreos, CDF,2025oenvíos. B00/F3cyadversos preservados,2024abierto adaptativo y límites de fuente/observación/valoración/búsqueda persistentes; sin revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        **w.read(PLAN)['budget'],'2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P91-LIMITES-RESULTADO','P91: presión de límites y siguiente selección interna, sin predecir')}
    archive=R/'privado'/('corte_P91_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P91'),(R/'registro/semana2_mision_privada_actual.json','P91')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P91=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P91: límites guardados, sin inferir\n\nCodex, '+receipt['utc']+'.Quinceárboles inspeccionados, prior/preproceso iguales aP88; cero predicciones/fits/scores/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_saved_tree_bound_review_index':w.rel(INDEX),'week_2_private_saved_tree_bound_review_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_predictions':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
