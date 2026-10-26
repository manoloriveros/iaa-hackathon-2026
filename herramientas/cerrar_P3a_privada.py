"""Conserva sensibilidad congelada y diagnóstico oracle como evidencia descriptiva."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';OUT=BASE/'sensibilidad_congelada_media_H1_20261026_v1'
ATTR=BASE/'atribucion_error_P3a_H1_20261026_v1'
sp=importlib.util.spec_from_file_location('private_P3a_state',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w);sys.stdout.reconfigure(encoding='utf8')


def main():
    assert not (OUT/'completion_receipt.json').exists()
    report=w.read(OUT/'report.json');attribution=w.read(ATTR/'report.json');stamp=datetime.now(timezone.utc)
    assert report['ultimate_forecasts_unchanged_all_scenarios'] and len(attribution['cells'])==48
    archive=OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ');archive.mkdir(parents=True)
    next_unit=('Register one simpler standard observation-link alternative H3B: source f*s peril mixture aggregated by NB/REN on member-training covariates only, rather than per-row risk mixtures. '
               'The documented need is P3afrozen adverse relative-allocation loss in motorNB2023 underreserve075/tail05/tail10; a global level correction cannot remove its relative-shape component. This is a hypothesis, not a proven cause. '
               'Use same nominalT0, existing P2memberC0andG3denominators, canonical inputs and frozen nested splits; no newC0/sourcefit or hyperparameter/RENweight/level search. '
               'Fit H3Bclosedcalibration inside each75scope, sourcebusinessmixtures fit only on its training rows; apply equal five-member ultimatecostmean and protected outer business-mixture observation adapter. '
               'Primary vs protectedS2baseline, secondary vs existing H1mean, and all4frozen scenario diagnostics predeclared before any newfit/score. Whole newlearning poison controls, synthetic real-schema flow, source hashes and scalar/metric math required. '
               'Do not use diagnostic oracle multipliers as inputs or a candidate; do not repeat old H1/P3asuites. Preserve the still-unperformed target-valuation recalibration distinction. '
               'Private priority,2024open adaptive,B00/F3c/alternatives retained,H1delivery deferred,no quota polling or uploads.')
    note='\n\n## Privada P3a: precios congelados, reservas/cola y atribución del fallo, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. Se mantuvieron los precios de último de la base S2y la media H1 exactamente iguales en los cuatro escenarios. '
    note+='Solo cambiaron las etiquetas declaradas y su observación mediante C0exterior protegido. No hubo recalibración, ajuste de curvas, inferencia fuente, precio2025oenvío nuevo.\n\n'
    note+='| Escenario | Diferencia D² | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---:|---:|---:|\n'
    for name,a in report['results'].items():
        note+=f'| {name} | {a["delta"]:+.8f} | [{a["bootstrap95"][0]:+.8f}, {a["bootstrap95"][1]:+.8f}] | {a["post31_delta"]:+.8f} | {a["worst_cell_delta"]:+.8f} |\n'
    note+='\nLas cuatro diferencias agregadas y sus intervalos simultáneos exploratorios son positivas. Persisten pérdidas superiores a0,001en autos nuevos2023con reservas75%y cola5%/10%. '
    note+='En ese año la diferencia total bajo cola5%es-0,00000022y bajo cola10%,-0,00007313; no se redondean a una mejora. '
    note+='La sensibilidad ponderada hacia2025es positiva en los cuatro casos, pero el ESSsigue siendo2,67%de filas y4,32%de grupos, frente al mínimo10%. '
    note+='Esos puntos no habilitan validación o rescatan los fallos sin pesos.\n\n'
    note+='Se comprobaron900ramas de coste en90objetos C0por probabilidades de evento independientes. '
    note+='El mayor error relativo de marca fue4,44e-16y el de CDF8,88e-16. Se conciliaron exactamente los céntimos de periodos y siniestros, incluidas las dos etiquetas de reservas. '
    note+='La reconstrucción nominal coincidió con P2sin repetir sus estadísticas. Las funciones de aprendizaje estuvieron bloqueadas y las etiquetas retenidas alteradas no cambiaron la observación de precios.\n\n'
    note+='El diagnóstico registrado para las48celdas descompone la diferencia de Tweedie en reparto relativo y arrepentimiento de escala. '
    note+='Para A=sum(y/sqrt(mu)), B=sum(sqrt(mu)) y C=sum(sqrt(y)), la pérdida observada es4A+4B-8C y el límite de mejor escala es8sqrt(AB)-8C. '
    note+='Ese límite y el multiplicador A/Busan respuestas retenidas: son oracles descriptivos, no precios, modelos candidatos, CVválida o parámetros transferibles. '
    note+='Se conservaron96escalares diagnósticos marcados como inadmisibles para predicción, fuera de los contadores de parámetros de precio.\n\n'
    note+='| Autos nuevos 2023 | Diferencia observada | Reparto relativo, descriptivo | Escala, descriptiva |\n|---|---:|---:|---:|\n'
    for a in attribution['cells']:
        if a['line']=='motor' and a['year']==2023 and a['NB']==1 and a['observed_delta_cell']<-.001:
            note+=f'| {a["scenario"]} | {a["observed_delta_cell"]:+.8f} | {a["relative_shape_component_descriptive"]:+.8f} | {a["scale_regret_component_descriptive"]:+.8f} |\n'
    note+='\nEl reparto relativo aporta pérdida en esos tres casos, incluso después de descontar descriptivamente la mejor escala. '
    note+='Esto no identifica una causa causal, pero justifica comprobar una restricción de heterogeneidad antes de añadir capacidad o mover el nivel. '
    note+='La identidad reproduce las diferencias previas con error máximo2,56e-16. No hubo precios oracle, nuevas puntuaciones competitivas o bootstrap de esa descomposición.\n\n'
    note+='Siguiente hipótesis: H3Bcon mezcla fuente por tipo de negocio, agregada desde f*sde las covariables de entrenamiento y congelada para el retenido. '
    note+='Reduce la dependencia de la observación respecto al perfil individual, manteniendo los mismos modelos, C0, etiquetas, folds y reglas cerradas. '
    note+='Se evaluará como una alternativa nueva y más simple, sin dar por probado que resuelva el fallo. Requiere receta, código, coste, controles y comentario previo. '
    note+='La recalibración de todo el objetivo bajo otra valoración no se ha hecho; no se confundirá con esta robustez de precios congelados.\n\n'
    note+='H1sigue diferido. B00, F3c y todas las alternativas/fallos se conservan;2024abierto adaptativo. '
    note+='Estos resultados locales condicionados a S2no prueban el F3c recibido, un holdout intacto o la mejora privada. '
    note+='Evidencia: '+w.rel(OUT/'report.json')+' y '+w.rel(ATTR/'report.json')+'.\n'
    doc=R/'docs/semana2/PRIVADA_P3A_SENSIBILIDAD_Y_ATRIBUCION_H1.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    body=OUT/'forum_resultados.md';body.write_text(note,encoding='utf8')
    res=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
                        '--id','COD-S2-20261026-PRIVADA-P3A-RESULTADO',
                        '--asunto','P3a: señal agregada estable, persiste fallo relativo en autos nuevos bajo estrés',
                        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt={'author':'Codex','utc':stamp.isoformat(),'status':report['status'],'report':w.rel(OUT/'report.json'),
             'report_sha256':w.sha(OUT/'report.json'),'attribution':w.rel(ATTR/'report.json'),'attribution_sha256':w.sha(ATTR/'report.json'),
             'document':w.rel(doc),'forum':json.loads(res.stdout),'results':report['results'],
             'new_model_fits':0,'new_C0_fits':0,'new_calibration_fits':0,'new_source_inference':0,'new_final_test_prices':0,'new_submissions':0,
             'diagnostic_oracles_not_price_parameters':96,'target_valuation_recalibration_performed':False,
             'submission_allowed':False,'formal_promotion':False,'2024_open':True,'B00_all_alternatives_preserved':True,
             'private_improvement_established':False,'goal_achieved':False,'next_unit':next_unit}
    index=R/'registro/semana2_sensibilidad_congelada_media_H1_actual.json';assert not index.exists();index.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    priority=R/'registro/semana2_mision_privada_actual.json';w.update(priority,{'last_progress_utc':stamp.isoformat(),'P3a':receipt,'next_unit':next_unit},archive)
    phase=R/'registro/semana2_mision017_fase2_actual.json'
    w.update(phase,{'utc':stamp.isoformat(),'private_P3a':receipt,'mission_private_priority':w.read(priority),
                    'next_unit':next_unit,'active_execution':None,'active_jobs':[],
                    'last_goal_turn_classification':'progress: complete frozen-price robustness and descriptive loss attribution, adverse cells preserved, simpler next hypothesis documented'},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P3a=receipt,mission_private_priority=w.read(priority),next_unit=next_unit,active_jobs=[],goal_achieved=False)
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_H1_frozen_sensitivity_index':w.rel(index),
                                       'week_2_private_H1_frozen_sensitivity_report':w.rel(doc)},archive)
    for path in [OUT,ATTR]:(path/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'status':receipt['status'],'new_fits':0,'new_submissions':0,'adverse_cells_retained':True,'forum':receipt['forum']}))


if __name__=='__main__':main()
