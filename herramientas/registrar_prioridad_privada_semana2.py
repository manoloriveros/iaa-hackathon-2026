"""Registra la nueva prioridad directa sin alterar pruebas ni aprobaciones históricas."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';DELIVERY=BASE/'entrega_H1_investigacion_20261026_v1'
PLAN=R/'registro/semana2_mision_privada_plan_v1.json'
CONTROL=R/'registro/semana2_control_entregas_codex_actual.json'
sp=importlib.util.spec_from_file_location('private_priority_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w);sys.stdout.reconfigure(encoding='utf8')


def main():
    index=R/'registro/semana2_mision_privada_actual.json';assert not index.exists()
    plan=w.read(PLAN);control=w.read(CONTROL);archives=sorted(DELIVERY.glob('prioridad_privada_*'));assert len(archives)==1
    archive=archives[0];test=w.read(archive/'private_priority_guard_test.json')
    assert not control['allow_new_submission'] and test['all_passed'] and test['API_calls']==0
    assert not (DELIVERY/'submission_started.json').exists() and not (DELIVERY/'public_receipt.json').exists()
    stamp=datetime.now(timezone.utc);cuts=archive/'state_cuts';cuts.mkdir()
    next_unit=('P0 private-generalization priority: preregister and implement the exact ultimate-to-observed H1/G3 production bridge using saved objects only. '
               'Prediction-only stage normalizers depend on observed vs ultimate exposure, so simple observed H1/G3 validation cannot stand in for the delivered ultimate correction. '
               'Use fixed saved outer groups and the primary source-safeS2 proxy, report exact mapping and any discrepancy before further C0/calibration fits. '
               'Then prepare deterministic inner-split support preflight for a finite full five-member nested algorithm; no rerun of completed H1/PUL2/age suites or weight/level tuning. '
               'H1 research delivery is explicitly deferred by current own execution gate even if quota returns; old admission and old transport evidence remain historical. '
               'Follow registro/semana2_mision_privada_plan_v1.json: private-generalization evidence primary, public secondary. Public0.17or approximate0.175does not complete the mission. '
               '2024open adaptive; B00/F3c and alternatives preserved; no claim of hidden private improvement, pristine holdout or professional independent validation.')
    note='\n\n## Nueva prioridad: generalización a la privada, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. Por instrucción directa del participante, la prioridad pasa a elegir y entregar un modelo con mejor evidencia de generalización a los casos no observados de la parte privada. '
    note+='La referencia pública cercana a0,175 proviene de su estimación del leaderboard; no se volvió a consultar ni se convierte en un nivel que ajustar. '
    note+='Superar0,17 o0,175 en la pública por sí solo no permite declarar alcanzada esta misión. La calificación privada futura es desconocida; su mejora solo podrá confirmarse con un resultado oficial cuando esté disponible.\n\n'
    note+='El plan prioriza objetivo y exposición correctos, flujo completo protegido, validación de la media final de cinco modelos, '
    note+='comportamiento por ramo/nuevo negocio/duración con soporte real y sensibilidad a reservas, cola y grupos influyentes. '
    note+='Se conservarán los criterios numéricos y los fallos históricos. El cambio de prioridad no convierte un diagnóstico exploratorio o un score público en promoción formal. '
    note+='La completitud del modelo incluye trazabilidad, variables disponibles a tiempo, incertidumbres y reproducción; se empezará por las recetas estándar existentes y solo se añadirá capacidad ante un fallo concreto documentado.\n\n'
    note+='La primera decisión operativa es diferir la entrega H1 preparada, antes de cualquier POST. Su candidato y admisión condicional previa se conservan como historia. '
    note+='El nuevo control propio impide el envío automático aunque reaparezca cupo, hasta revisar el puente último-observado y el algoritmo de cinco miembros. '
    note+='La última consulta real a las13:10UTC seguía devolviendo0cupos; no se ha enviado H1 ni hay ref o score nuevo. '
    note+='F3c procesado0,16914 continúa como referencia pública entregada; B00 y todas las alternativas siguen disponibles.\n\n'
    note+='Se archivó el transportador anterior con su SHA y se añadió una barrera en la entrada real, antes de comprobar la admisión antigua o autenticar la API. '
    note+='Las pruebas nuevas verificaron esa salida sin red, control ausente, booleano inválido y política alterada. '
    note+='Las siete funciones del núcleo de transporte mantuvieron exactamente su AST; no se repitieron sus catorce pruebas anteriores. '
    note+='La admisión antigua no autoriza el código modificado: una eventual liberación requerirá una nueva revisión de esa versión. '
    note+='No se cambió ninguna otra automatización, conversación, autorización ajena o artefacto entrenado.\n\n'
    note+='2024 permanece abierto por la instrucción directa anterior, como desarrollo adaptativo. Los folds externos guardados se conservarán y cualquier partición interna nueva se fijará antes de aprender. '
    note+='Una evaluación anidada posterior no borra que2023/2024 ya orientaron muchas decisiones. Tampoco se atribuirá independencia a la instantánea histórica, '
    note+='se fabricará soporte emergente con mercado desarrollado ni se ocultarán las pérdidas de NB bajo reservas/cola.\n\n'
    note+='P0 será comprobar el puente de último a observado del código de producción, incluyendo los normalizadores por cartera. '
    note+='P1 será preparar ámbitos internos y soporte para evaluar el promedio de cinco modelos sin ancestros del grupo externo en su aprendizaje. '
    note+='Los precios de un proxy se identificarán como tales mientras falte replay completo F3c. Se registrarán hipótesis, configuración, criterio y coste antes de nuevos ajustes o puntuaciones.\n\n'
    note+='Nota de continuidad: las herramientas disponibles del objetivo persistente solo permiten cambiar su estado, no editar el texto activo. '
    note+='La cadena antigua que menciona0,17 como meta principal y2024cerrado queda superada por las instrucciones directas del participante y este plan. '
    note+='No se marcó falsamente completo ni se pausó el objetivo para sustituir ese texto; el trabajo continúa bajo la prioridad nueva.\n\n'
    note+='Plan: '+w.rel(PLAN)+'. Control: '+w.rel(CONTROL)+'. Evidencia de entrada: '+w.rel(archive/'private_priority_guard_test.json')+'.\n'
    doc=R/'docs/archivo/semana2/MISION_PRIVADA_PRIORIDAD_Y_PLAN.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cuts)
    body=archive/'forum_prioridad_privada.md';body.write_text(note,encoding='utf8')
    res=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
                        '--id','COD-S2-20261026-PRIORIDAD-PRIVADA',
                        '--asunto','Prioridad privada: generalización antes de pública; entrega H1 diferida',
                        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt={'author':'Codex','utc':stamp.isoformat(),'status':'active_private_generalization_priority',
             'effective_goal':plan['objective'],'plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
             'execution_control':w.rel(CONTROL),'execution_control_sha256':w.sha(CONTROL),
             'guard_test':w.rel(archive/'private_priority_guard_test.json'),'guard_test_sha256':w.sha(archive/'private_priority_guard_test.json'),
             'document':w.rel(doc),'forum':json.loads(res.stdout),'next_unit':next_unit,
             'old_app_goal_text_stale':True,'public017_or0175_not_sufficient_for_completion':True,
             'hidden_private_improvement_established':False,'goal_achieved':False,'2024_open':True,
             'B00_all_alternatives_preserved':True,'new_fits':0,'new_C0_fits':0,'new_submissions':0}
    index.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    phase=R/'registro/semana2_mision017_fase2_actual.json';current=w.read(phase)
    pending=current['pending_research_delivery'].copy()
    pending.update(status='deferred_for_private_generalization_review',operational_allow_submission=False,
                   historical_conditional_admission_preserved=True,current_transport_requires_new_admission=True,
                   execution_control=w.rel(CONTROL),priority_amendment=w.rel(index))
    waits=sorted(DELIVERY.glob('quota_wait_*.json'));quota=w.read(waits[-1])
    w.update(phase,{'utc':stamp.isoformat(),'mission_private_priority':receipt,'effective_goal':plan['objective'],
                    'pending_research_delivery':pending,'next_unit':next_unit,'last_quota_read':quota,'last_quota':quota['limits'],
                    '2024_open':True,'2024_closed':False,'goal_achieved':False,
                    'active_execution':None,'active_jobs':[],'active_external_submission':None,
                    'last_goal_turn_classification':'progress: direct private-priority amendment, delivery gate implemented and tested, forum/state updated'},cuts)
    delivery_index=R/'registro/semana2_H1_entrega_investigacion_actual.json'
    w.update(delivery_index,pending,cuts)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(mission_private_priority=receipt,effective_goal=plan['objective'],pending_research_delivery=pending,
               next_unit=next_unit,last_quota_read=quota,last_quota=quota['limits'],active_jobs=[],goal_achieved=False,
               **{'2024_open':True,'2024_closed':False})
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},cuts)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_generalization_plan':w.rel(PLAN),
                                       'week_2_private_generalization_index':w.rel(index),
                                       'week_2_private_generalization_report':w.rel(doc),
                                       'week_2_codex_current_delivery_execution_control':w.rel(CONTROL)},cuts)
    (archive/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'status':receipt['status'],'delivery_deferred':True,'new_submissions':0,'2024_open':True,'forum':receipt['forum']}))


if __name__=='__main__':main()
