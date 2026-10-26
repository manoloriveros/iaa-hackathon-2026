"""Punto de continuación: puente correcto y ámbitos anidados listos, sin fit nuevo."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';P0=BASE/'puente_ultimo_observado_H1_20261026_v1'
P1=BASE/'preflight_anidado_H1_20261026_v1'
sp=importlib.util.spec_from_file_location('private_P0_P1_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w);sys.stdout.reconfigure(encoding='utf8')


def main():
    assert not (P0/'completion_receipt.json').exists() and not (P1/'completion_receipt.json').exists()
    bridge=w.read(P0/'report.json');pre=w.read(P1/'report.json');a=bridge['primary']
    assert len(bridge['numeric_controls'])==15 and len(pre['scopes'])==75
    assert pre['all75scopes_numerically_supported'] and pre['minimum_notification_count']==24
    assert bridge['new_model_fits']==pre['new_model_fits']==bridge['new_C0_fits']==pre['new_C0_fits']==0
    assert not w.read(R/'registro/semana2_control_entregas_codex_actual.json')['allow_new_submission']
    stamp=datetime.now(timezone.utc);archive=P1/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ');archive.mkdir(parents=True)
    next_unit=('P2 private-generalization: implement and preregister the full numerical nested five-member H1 correction with P1canonical inputs/saved inner groups. '
               'Primary algorithm is fixed P0outerS2ultimate * arithmetic_mean5(U_H1_inner/U_G3_inner) * q_source_outer versus P0outerS2ultimate*q_global_outer. '
               'Outer observation adapters are evaluation-only, never member-learning inputs. Use calendar exposure and ultimate stage normalizers only at forward; member fits use original rounded exposure and own C0. '
               '75line/outer/member scopes,375primary reporting-peril fits plus375full-poison-control reporting fits separately,150primary G3/H1closed learner calls plus150controlcalls. No source models, coefficient searches or new capacity. '
               'First test full synthetic C0+closedlearning+ultimateforward+mean+observation flow. Freeze code/source/hypothesis/criterion/cost/forum before real fit or scoring. '
               'Prove complete outer-held cost/reserve/peril/date poisoning invariance and scalar/metric/bridge mathematics; keep source hashes, fit events and per-scope commits so partial work is reconciled rather than repeated. '
               'Report pooled primary result, folds/years/cells/influence and all failed gates; adaptive2023/2024and64percent-vs80percenttraining-size limits remain. '
               'H1delivery stays deferred under current execution gate; no quota polling/upload during this local unit. Private-generalization priority from planv1, B00/F3c/alternatives preserved,2024open.')
    note='\n\n## Privada P0/P1: puente de producción y soporte anidado, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. Se cerró P0 con los objetos guardados y se prepararon los ámbitos de P1. '
    note+='No hubo ajustes de precio, C0, recalibraciones, inferencias de modelos fuente, CSV finales o envíos. H1 continúa diferido por la nueva prioridad privada.\n\n'
    note+='La relación correcta entre observado O y último U incluye exposición y normalizadores: '
    note+='O_m/U_m=(Eredondeada/Ecalendario)*q_m*L_m, con L_m=producto(Núltimo/Nobservado) de sus etapas. '
    note+='El cociente observado H1/G3 incluye L_H1/L_G3. Se verificó por otro cálculo usando precios observados y normalizadores guardados, con error relativo máximo1,11e-15. '
    note+='Una fixture sin respuestas demuestra que ignorar ese término puede producir una discrepancia; no es una medición de error real o privado.\n\n'
    note+='En las filas reales, L_H1/L_G3 varía entre0,99967337y1,00083912 en autos,0,99993926y1,00004074 en contenidos, y es1 en edificios sin etapas residuales. '
    note+='La fórmula de producción se reprodujo con la base S2 completa y protegida. La observación se aplicó después de los normalizadores de último, sin renormalizar precios observados a posteriori. '
    note+='La entrada de cinco miembros futura todavía no se considera validada por esta única instancia por fold.\n\n'
    note+=f'La diferencia primaria de H1 sobre esa base S2 es {a["delta"]:+.8f}, IC95por grupos[{a["bootstrap95"][0]:+.8f},{a["bootstrap95"][1]:+.8f}], '
    note+=f'post31{a["post31_delta"]:+.8f} y peor celda{a["worst_cell_delta"]:+.8f}. '
    note+='La dirección es positiva en los cinco folds y ambos años. El mínimo diagnóstico de fase2,0,002, sigue incumplido. '
    note+='El valor apenas cambia respecto al contraste anterior, que se conserva y no se volvió a puntuar. '
    note+='Estas diferencias son de desarrollo local adaptativo, sin una mejora privada demostrada, replay del F3c real o promoción formal.\n\n'
    note+='El nuevo avance de último usó calendario una sola vez, mantuvo los objetos aprendidos y pasó en quince ámbitos la invariancia ante costes/reservas retenidos alterados. '
    note+='Se bloquearon las entradas de aprendizaje durante ese avance. Se calcularon240normalizadores de predicción primarios y240en el control adverso, separados de parámetros ajustados. '
    note+='La base alternativa S2 es reproducible y distinta del F3c recibido; esa limitación permanece explícita.\n\n'
    note+='P1 conservó los cinco folds externos por componentes cliente/dirección y fijó los internos por SHA256 con salH1-NEST-v1 y módulo5, sin respuestas o scores en la asignación. '
    note+='Cada uno de los75ámbitos de ramo/fold externo/miembro excluye los grupos externos y su parte interna. '
    note+='Los componentes f/s y la tasa T2b fueron idénticos en las copias exteriores, por lo que pudieron conservarse como entradas fuente congeladas. '
    note+='Se retiraron de las entradas internas los precios, q y exposiciones efectivas aprendidas previamente.\n\n'
    note+='Todos los ámbitos pasan los mínimos numéricos de notificaciones, marcas de reservas75/100/125y fechas; el mínimo es24notificaciones. '
    note+='Ambas celdas de negocio tienen costes positivos de entrenamiento. Esto acredita que el estimador existente puede intentarse, no credibilidad o precisión suficiente. '
    note+='El mayor peso bruto de un grupo en el coste de un peril de entrenamiento llega a5,70% en autos,19,91% en edificios y12,68% en contenidos; '
    note+='se conserva para evaluar estabilidad y no motiva eliminación de siniestros o cambios de partición.\n\n'
    note+='La siguiente unidad será el flujo numérico anidado completo de la corrección estándar, con375ajustes primarios de curva por peril y375repeticiones adversas de invariancia contabilizadas aparte, '
    note+='además de150aprendizajes cerrados primarios G3/H1 y150controles. No requerirá nuevos modelos fuente ni mayor capacidad. '
    note+='Antes se congelarán el código, presupuesto, criterio y fuentes y se probará el flujo completo con datos sintéticos. '
    note+='La media usará cinco cocientes de último con pesos iguales y el puente externo solo para evaluar; no se aprovecharán objetos externos como si fueran internamente independientes.\n\n'
    note+='El tamaño de entrenamiento interno será aproximadamente64%de las filas frente al80%de los miembros de producción. '
    note+='Los resultados futuros conservarán esa limitación y el uso adaptativo previo de2023/2024. Una evaluación anidada no restituye un holdout intacto. '
    note+='Se mantienen las carencias de cola/reservas, soporte ponderado y disponibilidad temporal de maestros. '
    note+='B00, F3c y todas las alternativas quedan intactos;2024abierto. La prioridad es generalización privada, con pública secundaria y sin declaración de éxito.\n\n'
    note+='Evidencia: '+w.rel(P0/'report.json')+' y '+w.rel(P1/'report.json')+'.\n'
    doc=R/'docs/semana2/PRIVADA_P0_P1_PUENTE_Y_SOPORTE_H1.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    body=P1/'forum_resultados.md';body.write_text(note,encoding='utf8')
    res=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
                        '--id','COD-S2-20261026-PRIVADA-P0-P1-RESULTADO',
                        '--asunto','Privada P0/P1: puente exacto y75ámbitos con soporte; media anidada aún pendiente',
                        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt={'author':'Codex','utc':stamp.isoformat(),'status':'P0_bridge_and_P1_nested_support_complete',
             'bridge_report':w.rel(P0/'report.json'),'bridge_report_sha256':w.sha(P0/'report.json'),
             'nested_preflight_report':w.rel(P1/'report.json'),'nested_preflight_report_sha256':w.sha(P1/'report.json'),
             'primary_delta':a['delta'],'primary_bootstrap95':a['bootstrap95'],'primary_post31_delta':a['post31_delta'],
             'all75scopes_numerically_supported':True,'minimum_notifications':24,
             'new_model_fits':0,'new_C0_fits':0,'new_calibration_fits':0,'new_source_inference':0,
             'new_final_test_prices':0,'new_submissions':0,'actual_five_member_nested_validation':False,
             'submission_allowed':False,'formal_promotion':False,'2024_open':True,
             'B00_all_alternatives_preserved':True,'hidden_private_improvement_established':False,
             'goal_achieved':False,'document':w.rel(doc),'forum':json.loads(res.stdout),'next_unit':next_unit}
    for name in ['semana2_puente_ultimo_observado_H1_actual.json','semana2_preflight_anidado_H1_actual.json']:
        path=R/'registro'/name;assert not path.exists();path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    priority_index=R/'registro/semana2_mision_privada_actual.json'
    w.update(priority_index,{'last_progress_utc':stamp.isoformat(),'P0_P1':receipt,'next_unit':next_unit},archive)
    priority=w.read(priority_index)
    phase=R/'registro/semana2_mision017_fase2_actual.json'
    w.update(phase,{'utc':stamp.isoformat(),'private_P0_P1':receipt,'mission_private_priority':priority,
                    'next_unit':next_unit,'active_execution':None,'active_jobs':[],
                    'last_goal_turn_classification':'progress: exact ultimate-observed bridge priced/validated, canonical nested inputs and75supportscopes completed'},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P0_P1=receipt,mission_private_priority=priority,next_unit=next_unit,active_jobs=[],goal_achieved=False)
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_H1_bridge_index':w.rel(R/'registro/semana2_puente_ultimo_observado_H1_actual.json'),
                                       'week_2_private_H1_nested_preflight_index':w.rel(R/'registro/semana2_preflight_anidado_H1_actual.json'),
                                       'week_2_private_H1_P0_P1_report':w.rel(doc)},archive)
    for path in [P0,P1]:(path/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'status':receipt['status'],'primary_delta':a['delta'],'all75scopes_supported':True,
                      'new_fits':0,'new_submissions':0,'forum':receipt['forum']}))


if __name__=='__main__':main()
