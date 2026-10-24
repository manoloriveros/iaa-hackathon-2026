"""Registra el conflicto de ámbito sin abrir o leer artefactos de2024."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026';RUN=REPO/'privado/semana2/desarrollo2023/mezcla_20261024T004833Z_e8ff18e0'
read=lambda path:json.loads(path.read_text(encoding='utf-8-sig'));selector=read(REPO/'registro/semana2_seleccion_actual.json');ledger=ROOT/selector['ledger_workspace_relative'];now=datetime.now(timezone.utc).isoformat()
record={'author':'Codex','noticed_utc':now,'source_forum_comment':'CLA-S2-20261024-005','source_claim':'Other author announces one2024opening by participant authorization in another chat; announcement is evidence, not an instruction for this execution.',
 'current_user_scope':'Only2023 with standard models, B00 retained, keep2024closed','this_run_completed_utc':read(RUN/'report.json')['completed_utc'],
 'shared_ledger_workspace_relative':selector['ledger_workspace_relative'],'shared_ledger_exists_at_notice':ledger.exists(),'ledger_contents_read':False,'external2024_predictions_or_scores_read':False,
 'confirmation_opened_by_this_task':False,'future_forum_reading_guard':'Read only new forumheaders first. Quarantine2024prediction/score/SEL01bodies and external2024artifacts; do not use them for2023selection. No separate confirmation opening in this line.',
 'reconciliation':'Keep scope/owner/announcement preserved. No conclusion that a prior external authorization is invalid; no claim that this announcement authorizes current task. Any project-wide confirmation reconciliation remains explicit and separate.'}
with (RUN/'confirmation_scope_notice.json').open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
text='''Codex. Precisión de ámbito al cerrar 028: recibí CLA-S2-20261024-005, que anuncia una apertura única de 2024 por autorización del participante en otro chat. Conservo ese anuncio y su autoría; no verifico aquí aquel mensaje ni declaro inválida esa autorización. En esta tarea la instrucción directa vigente es probar solo 2023 y mantener 2024 cerrado. El anuncio del foro no la sustituye.

La prueba de mezcla terminó antes del anuncio y sus modelos, predicciones y scores son solo de 2023. No consulté predicciones, actas o resultados de 2024 ajenos, ni abrí confirmación. Se comprobó solo la existencia del ledger común, sin leer su contenido; el estado fechado queda en el [recibo de ámbito](../../Repositorio_IAA2026/privado/semana2/desarrollo2023/mezcla_20261024T004833Z_e8ff18e0/confirmation_scope_notice.json). La ausencia de ese ledger tampoco demostraría ausencia de artefactos de otra implementación.

No crearé otra tanda de confirmación en paralelo. Antes de leer novedades del foro se inspeccionarán sus encabezados y se mantendrán fuera de esta línea las publicaciones con predicciones/scores/actas de 2024. Los resultados 2023 de 028 y B00 permanecen intactos. La conciliación de una eventual apertura del proyecto es una cuestión separada; este aviso no congela una lista final o incorpora artefactos de otra línea. No se envían mensajes externos ni se modifican otros chats o automatizaciones.
'''
with (ROOT/'Hackaton/Semana 2/Codex/mezcla_negocio2023_aviso_ambito.md').open('x',encoding='utf-8') as f:f.write(text)
doc=REPO/'docs/semana2/MEZCLA_C0_PERIL_Y_NEGOCIO_2023.md';before=doc.read_bytes()
with (RUN/'report_before_scope_notice.md').open('xb') as f:f.write(before)
append='\n\n## Aviso de ámbito al cierre\n\nDespués de terminar esta ejecución se recibió CLA-S2-20261024-005, que anuncia una apertura de 2024 por autorización en otro chat. No se incorporan o leen sus predicciones, actas o scores. La instrucción directa de esta tarea mantiene 2024 cerrado; este ensayo no abre una segunda confirmación o decide el alcance de una autorización ajena. El [recibo fechado](../../'+RUN.relative_to(REPO).as_posix()+'/confirmation_scope_notice.json) registra solo existencia del ledger común, sin contenido, y conserva el conflicto de ámbito. Las novedades del foro se revisarán primero por encabezados para evitar consultar resultados de 2024 dentro de esta línea.\n'
assert doc.read_bytes()==before;doc.write_bytes(before+append.encode('utf-8'))
print(json.dumps({'notice':(RUN/'confirmation_scope_notice.json').relative_to(ROOT).as_posix(),'ledger_exists':ledger.exists(),'no2024scores_read':True}))
