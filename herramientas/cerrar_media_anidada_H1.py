"""Registra evaluación y coste real sin confundir controles con nuevos modelos."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';OUT=BASE/'media_anidada_H1_20261026_v3'
sp=importlib.util.spec_from_file_location('private_nested_H1_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w);sys.stdout.reconfigure(encoding='utf8')


def main():
    assert not (OUT/'completion_receipt.json').exists()
    report=w.read(OUT/'report.json');primary=report['primary'];secondary=report['secondary_nested_minus_frozen_single']
    assert report['committed_scopes']==75 and len(list(OUT.glob('scope_*/committed.json')))==75
    counts=report['counts'];const=counts['primary']['constants']['pricing_constants_total']
    assert counts['primary']['reporting_peril_completed']==counts['poison']['reporting_peril_completed']==375
    assert counts['primary']['closed_learner_completed']==counts['poison']['closed_learner_completed']==150
    assert counts['poison']['constants']==counts['primary']['constants']
    assert not w.read(R/'registro/semana2_control_entregas_codex_actual.json')['allow_new_submission']
    stamp=datetime.now(timezone.utc);archive=OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ');archive.mkdir(parents=True)
    next_unit=('P3 private-generalization: inspect and preregister target-observation reserve/tail robustness of the completed nested five-member algorithm, not a new feature/model search. '
               'Use saved member C0countCDF/costCDF branches/meanmarks, fixed partitions and source components. First derive exactly what can be reused algebraically and what closed calibration must be re-estimated under changed training labels/exposure. '
               'Separate fixed-structure timing sensitivity from target-valuation recalibration and from a full source/model revaluation; do not claim the latter without doing it. '
               'Report every declared reserve075/125 and priorBI/subsidencecosttail05/10 convention, NB/REN/line/year, influence and the existing unsupported2025weight sensitivity honestly. '
               'No changing splits, thresholds, C0tail assumptions or weights to remove adverse cells; no repeat of finished primary nested assay/bootstraps on identical inputs. '
               'Freeze specific new uncertainty, criterion, source hashes/code/cost/forum before new calibration or scenario scoring. '
               'H1delivery remains deferred and B00/F3c/all alternatives preserved.2024open adaptive, public secondary, hidden private performance unproven.')
    synthetic=[]
    for version in [1,2,3]:
        path=BASE/f'media_anidada_H1_20261026_v{version}/synthetic_report.json';s=w.read(path)
        synthetic.append({'version':version,'report':w.rel(path),'sha256':w.sha(path),
                          'reporting_peril_fits':s['synthetic_reporting_peril_fits'],'closed_learner_calls':s['synthetic_closed_learner_calls']})
    receipts=[w.read(p) for p in sorted(OUT.glob('scope_*/committed.json'))]
    norm_primary=sum(c['primary_ultimate_normalizers'] for c in receipts)
    norm_control=sum(c['adverse_ultimate_normalizers_separate'] for c in receipts)
    max_bridge=max(z['bridge_max_relative_error'] for c in receipts for z in c['controls'].values())
    max_derivative=max(z['line_derivative_relative_residual'] for c in receipts for z in c['controls'].values())
    count_entry={'author':'Codex','utc':stamp.isoformat(),'primary_reporting_peril_fits':375,'adverse_reporting_peril_fits_separate':375,
                 'primary_frequency_constants':375,'primary_mark_means_threebranches_separate':1125,'primary_normalized_mixtures':75,
                 'primary_closed_scope_learner_calls':150,'adverse_closed_learner_calls_separate':150,
                 'unique_closed_price_constants':const,'breakdown':counts['primary']['constants'],
                 'adverse_recomputed_constants_separate':counts['poison']['constants'],
                 'predecessor_v2_primary_curves_reused_not_refit':5,'predecessor_v2_closed_learners_reused_not_refit':2,
                 'v3_new_primary_curves':370,'v3_new_primary_closed_learners':148,
                 'primary_ultimate_prediction_normalizers_committed':norm_primary,
                 'adverse_ultimate_normalizers_committed_separate':norm_control,
                 'extra_v2_partial_forward_and_v3_cache_replay_normalizers_separate':{'v2_ultimate':8,'v3_cached_observed':8},
                 'synthetic_by_version_excluded':synthetic,'new_iterative_price_fits':0,'new_source_models':0,
                 'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json')}
    counter_path=R/'registro/semana2_contadores_propios_actual.json';counter=w.read(counter_path)
    assert 'phase2_private_nested_H1' not in counter,'Do not increment a previously registered run twice'
    w.update(counter_path,{'as_of_utc':stamp.isoformat(),'cumulative_closed_form_constants':counter['cumulative_closed_form_constants']+const,
                           'supplementary_reporting_peril_fits_since_counter_start':counter['supplementary_reporting_peril_fits_since_counter_start']+375,
                           'mixture_frequency_constants_since_counter_start_separate':counter['mixture_frequency_constants_since_counter_start_separate']+375,
                           'mixture_positive_severity_means_since_counter_start_separate':counter['mixture_positive_severity_means_since_counter_start_separate']+1125,
                           'phase2_private_nested_H1':count_entry},archive)
    note='\n\n## Privada P2: promedio H1 evaluado con aprendizaje anidado completo, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. Se completaron los75ámbitos preinscritos de ramo/fold externo/miembro. '
    note+='Cada grupo externo quedó fuera de curvas de reporte, frecuencias, mezcla, formas, niveles y factores de sus cinco miembros. '
    note+='Los modelos fuente se mantuvieron congelados. La media aritmética de costes de último se pasó a observado después, con el puente exterior protegido de P0. '
    note+='Ese puente y la base S2exterior son solo de evaluación y no se usaron para aprender los miembros.\n\n'
    note+=f'Comparación principal frente a la base S2de producción: diferencia D² {primary["delta"]:+.8f}, IC95por grupos[{primary["bootstrap95"][0]:+.8f},{primary["bootstrap95"][1]:+.8f}], '
    note+=f'intervalo simultáneo exploratorio[{primary["simultaneous95_family"][0]:+.8f},{primary["simultaneous95_family"][1]:+.8f}]. '
    note+=f'Post31{primary["post31_delta"]:+.8f}, peor celda{primary["worst_cell_delta"]:+.8f}.\n\n'
    note+='| Año | Diferencia, denominador global |\n|---|---:|\n'
    for year,value in primary['years'].items():note+=f'| {year} | {value:+.8f} |\n'
    note+='\n| Fold externo | Diferencia, denominador global |\n|---|---:|\n'
    for fold,value in primary['folds'].items():note+=f'| {fold} | {value:+.8f} |\n'
    failed=[k for k,v in primary['diagnostic_gates'].items() if not v]
    note+='\nFallos de los criterios diagnósticos conservados: '+(', '.join(failed) if failed else 'ninguno en este contraste exploratorio')+'. '
    note+='No se modifica el mínimo0,002, se retiran alternativas o se promueve formalmente el modelo por este resultado.\n\n'
    note+=f'El secundario declarado, media anidada menos corrección de un miembro ya congelada, tiene diferencia {secondary["delta"]:+.8f}, '
    note+=f'IC95[{secondary["bootstrap95"][0]:+.8f},{secondary["bootstrap95"][1]:+.8f}]. '
    note+='Es una comparación pareada del algoritmo nuevo, no una repetición de la tanda anterior ni una prueba de cinco muestras independientes. '
    note+='Se conservaron todos los folds, años, celdas y sensibilidades de nivel±5%, sin elegir un nivel para entregar.\n\n'
    note+='Los75flujos reales pasaron la corrupción de T0, reservas, peril y fechas de siniestros externos, volviendo a ajustar realmente el papel adverso. '
    note+='Curvas, calibraciones y precios de último coincidieron exactamente con los primarios. '
    note+=f'El mayor error relativo del puente fue{max_bridge:.3g}; el residuo relativo máximo de la derivada de nivel,{max_derivative:.3g}. '
    note+='El momento se cotejó por suma escalar independiente y la media por otra operación aritmética. '
    note+='La métrica se cotejó con la implementación estándar, con draws conjuntos por los componentes globales. Los SHA de fuentes permanecieron iguales.\n\n'
    note+='Se conservaron dos versiones técnicas anteriores: V1detectó antes de ajustar que la tabla de siniestros no incluía año; V2se detuvo en el control adverso al intentar asignar un importe fuera de int64. '
    note+='V3adjuntó el año por metadatos de periodo y usó enteros representables con fixtures del mismo tipo. '
    note+='Los cinco ajustes de curva y dos calibraciones primarias de V2se recuperaron por SHA, firmas de argumentos y equivalencia AST del núcleo numérico; no se volvieron a ajustar. '
    note+='Los eventos heredados los contabilizan una sola vez. Se conservaron fallos, código y registros.\n\n'
    note+=f'Coste primario total de la unidad:375curvas por peril,150aprendizajes cerrados G3/H1 y{const}constantes de precio; '
    note+='el control adverso añade375curvas y150aprendizajes, registrados aparte. '
    note+='Hay375constantes de frecuencia y1.125medias de marca para las tres ramas de reserva, además de75mezclas normalizadas derivadas. '
    note+=f'Normalizadores de último comprometidos:{norm_primary}primarios y{norm_control}adversos; se señalan aparte los avances parciales/replays tras el fallo. '
    note+='Las tres versiones sumaron105curvas y42aprendizajes cerrados sintéticos, excluidos de esos contadores reales. '
    note+='Cero modelos iterativos de precio o fuente nuevos, inferencias fuente, precios finales2025, CSV nuevos o envíos.\n\n'
    note+='Esta evaluación comprueba la corrección completa de cinco miembros condicionada a la base reproducible S2. '
    note+='S2no es el F3c recibido y su aprendizaje histórico completo sigue sin reproducirse. '
    note+='Cada miembro interno usa aproximadamente64%de los datos frente al80%de sus homólogos de producción. '
    note+='La selección adaptativa previa de2023/2024, instantáneas sin fecha, composición de riesgo y masa tardía no identificadas limitan la interpretación. '
    note+='No constituye validación profesional independiente ni una mejora privada demostrada.\n\n'
    note+='La siguiente incertidumbre será reservas/cola y mezcla de negocio para este algoritmo completo. '
    note+='Primero se distinguirá qué transformación algebraica permiten las ramas de C0guardadas y qué calibraciones requieren etiquetas/exposiciones de entrenamiento distintas. '
    note+='Se separará sensibilidad de estructura fija, recalibración de valoración objetivo y revaloración del modelo fuente; no se afirmará lo último sin hacerlo. '
    note+='Se fijará una receta limitada antes de nuevos ajustes o scores, conservando los resultados adversos anteriores y el fallo de soporte de los pesos2025.\n\n'
    note+='H1permanece diferido por el control de prioridad privada. B00, F3c y todas las alternativas se conservan;2024abierto adaptativo, pública secundaria. '
    note+='No hay consulta de score privado, envío nuevo o declaración de éxito. Evidencia: '+w.rel(OUT/'report.json')+'.\n'
    doc=R/'docs/semana2/PRIVADA_P2_MEDIA_ANIDADA_H1.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    body=OUT/'forum_resultados.md';body.write_text(note,encoding='utf8')
    res=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
                        '--id','COD-S2-20261026-PRIVADA-MEDIA-H1-RESULTADO',
                        '--asunto','Privada P2: media anidada H1 completa, evidencia y límites conservados',
                        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt={'author':'Codex','utc':stamp.isoformat(),'status':report['status'],'report':w.rel(OUT/'report.json'),
             'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(doc),'forum':json.loads(res.stdout),
             'primary':primary,'secondary_nested_minus_frozen_single':secondary,'counts':count_entry,
             'actual_nested_correction_algorithm_validated':True,'actual_F3c_full_learning_replay':False,
             'new_source_models':0,'new_iterative_price_fits':0,'new_final_test_prices':0,'new_submissions':0,
             'submission_allowed':False,'formal_promotion':False,'2024_open':True,'B00_all_alternatives_preserved':True,
             'private_improvement_established':False,'goal_achieved':False,'next_unit':next_unit}
    index=R/'registro/semana2_media_anidada_H1_actual.json';assert not index.exists();index.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    priority_index=R/'registro/semana2_mision_privada_actual.json'
    w.update(priority_index,{'last_progress_utc':stamp.isoformat(),'P2':receipt,'next_unit':next_unit},archive)
    phase=R/'registro/semana2_mision017_fase2_actual.json';current=w.read(phase)
    assert current['active_execution'] is None and not current['active_jobs']
    w.update(phase,{'utc':stamp.isoformat(),'private_P2':receipt,'mission_private_priority':w.read(priority_index),
                    'new_C0_fits':current['new_C0_fits']+375,'new_emerging_C0_fits':current['new_emerging_C0_fits']+375,
                    'new_nested_H1_adverse_C0_fits_separate':375,'new_nested_H1_closed_price_constants':const,
                    'next_unit':next_unit,'active_execution':None,'active_jobs':[],
                    'last_goal_turn_classification':'progress: full75scope nestedmean, actual whole-learningpoison controls, paired grouped evidence and preserved failures'},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P2=receipt,mission_private_priority=w.read(priority_index),next_unit=next_unit,active_jobs=[],goal_achieved=False)
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_H1_nested_evaluation_index':w.rel(index),
                                       'week_2_private_H1_nested_evaluation_report':w.rel(doc)},archive)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'status':receipt['status'],'primary_delta':primary['delta'],'primary_C0fits':375,
                      'adverse_C0fits_separate':375,'closed_constants':const,'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':main()
