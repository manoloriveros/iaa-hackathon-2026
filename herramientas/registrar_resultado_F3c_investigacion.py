"""Conserva el recibo F3c procesado y la excepción de investigación sin promover formalmente."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('writer_resultF3', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'entrega_F3c_investigacion_20261026_v1'; P = R / 'registro/semana2_mision017_fase2_actual.json'

def main():
    assert not (OUT / 'completion_receipt.json').exists()
    receipt = w.read(OUT / 'public_receipt.json'); admission = w.read(OUT / 'admission.json'); phase = w.read(P)
    assert receipt['ref'] == 57654514 and receipt['status'] == 'COMPLETE' and receipt['public_score'] == .16914
    assert receipt['CSV_sha256'] == admission['CSV']['sha256'] == w.sha(ROOT / admission['CSV']['path'])
    assert receipt['bytes'] == admission['CSV']['bytes'] and phase['new_submissions'] == 2
    assert receipt['private_score_not_read'] and receipt['no_final_selection'] and not receipt['promotion_gates_passed']
    previous_best = phase['best_user_team_public_receipt']; assert previous_best['public_score'] == .16519
    stamp = datetime.now(timezone.utc); archive = OUT / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    gain = receipt['public_score'] - previous_best['public_score']; gap = .17 - receipt['public_score']
    next_unit = ('El objetivo0.17 sigue activo: falta0.00086; no enviar más mientras la cuota actual sea0. '
        'No repetir F3c, los GLM secuenciales/conjuntos ni retocar K a partir del público. '
        'Priorizar la evidencia ya recibida de FSp solo en renovación, excluyendo edificios, antes de nueva complejidad. '
        'Buscar primero el CSV/receta K_F4_soloREN_sinedif y sus métricas/código ya aportados; no repetir el entrenamiento FSp por falta de búsqueda. '
        'Separar el incremento FSp del de los factores; los signos adversos en nuevo negocio justifican mantener ese bloque intacto en cualquier investigación posterior. '
        'Conciliar la base F3b del informe recibido con F3c medido: probar si la razón por celda de renovación es constante y qué parte de la mezcla/normalización/factores cambia. '
        'Si se prepara otro candidato, registrar antes una receta determinista y criterio, mantener exactamente los precios NB y los totales pertinentes, '
        'verificar fuentes/SHA, álgebra y efectos porfila, y conservar los controles predictivos no acreditados. '
        'Los resúmenes de otras IA no sustituyen la reproducción numérica que falte ni autorizan mensajes a otros chats, delegación o una selección final. '
        'No crear sondas, aumentar peso por el score público o gastar cupos sin revisión. '
        'Si no se recupera esa evidencia, avanzar en una necesidad material distinta: frecuencia por género con exposición de número correcta y ámbitos guardados, '
        'no recalcular C0 o estimar severidad/último no identificables. B00, C1/F2/F3c y alternativas preservados;2024 abierto como desarrollo.')
    note = '\n\n## F3c procesado: público0,16914, 26 de octubre de 2026 (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. '
    note += ('Kaggle completó el único envío de investigación de F3c:0,16914, frente a0,16519 de C1. '
        f'La mejora es{gain:+.5f} y falta{gap:.5f} para0,17. '
        'El recibo oficial está en estadoCOMPLETE, referencia57654514, nombre codex_F3c_residual_2025.csv,4351233bytes y '
        'SHA5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276. Se cotejaron nombre, mensaje, bytes, referencia y huella del archivo local. '
        'No se leyó score privado ni se cambió la selección final.\n\n'
        'La receta y el archivo son de Claude; Codex hizo la revisión, la copia, el replay de artefacto, el envío y la consulta del recibo. '
        'F3c aplica factores residuales de género, teletrabajo y segmento al C1 medido; no incorpora FSp. '
        'La copia y el replay de los102multiplicadores fueron idénticos byte a byte. '
        'Ese replay decodifica la representación del propio CSV recibido y no certifica su entrenamiento histórico independiente. '
        'El dryrun oficial pasó los cinco controles. Antes se conservaron y corrigieron los fallos de TEMP y de ruta de muestra; '
        'el dryrun sin muestra fue rechazado por nuestro control aunque la CLI devolvió0. Ninguno de esos intentos envió un archivo.\n\n'
        'La entrega usó una excepción de investigación registrada antes, bajo las instrucciones humanas vigentes de envío y continuidad automática. '
        'Se conservaron los controles no superados de G/J: mínimo+0,002, cuatro folds positivos y sustituto A1 original. '
        'Los resultados medios por ambos años, el intervalo simultáneo positivo de G3 y el mecanismo recibido de frecuencia motivaron medir este paso. '
        'El mejor público no transforma esos fallos en controles aprobados, no elimina el soporte escaso de NB ni acredita disponibilidad al cotizar de los maestros sin fecha. '
        'No hubo promoción formal, retiro de alternativas, nueva aprobación humana o revisión profesional independiente.\n\n'
        'La previsión recibida de0,1666 quedó0,00254 por debajo del resultado, y el score quedó0,00094 por encima de su intervalo80 % publicado '
        '[0,1647;0,1682]. Se registra el error de previsión. Un punto público tras búsqueda adaptativa no valida esa distribución, '
        'ni garantiza el resultado privado o la siguiente mejora.\n\n'
        'Se gastó exactamente un cupo. El API devuelve10usados hoy,22totales,0disponibles y limited_by_total=false. '
        'La cola de envío terminó; no habrá reenvío o sonda. El trabajo local puede continuar sin nuevos cupos. '
        'El objetivo0,17 sigue activo y no se declara alcanzado. B00, C1/F2, F3c, versiones fallidas y todas las alternativas quedan guardados. '
        '2024 permanece abierto por instrucción humana y se trata como desarrollo adaptativo.\n\n'
        'Recibo: ' + w.rel(OUT / 'public_receipt.json') + '. CSV: ' + admission['CSV']['path'] + '.\n\nSiguiente unidad: ' + next_unit + '\n')
    doc = R / 'docs/archivo/semana2/MISION017_F3c_ENVIO_RESULTADO.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    body = OUT / 'forum_resultado.md'; body.write_text(note, encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-MISION017-F3c-RESULTADO', '--asunto',
        'F3c procesado0,16914: mejora+0,00395 y objetivo0,17 todavía activo', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    best = {'ref': receipt['ref'], 'date_UTC': receipt['date_UTC'], 'status': 'COMPLETE', 'public_score': receipt['public_score'],
        'bytes': receipt['bytes'], 'source_author': 'Claude recipe/F3c', 'transport_author': 'Codex current phase',
        'replay_audit_author': 'Codex; artifact representation only, not full training replay',
        'receipt': w.rel(OUT / 'public_receipt.json'), 'receipt_sha256': w.sha(OUT / 'public_receipt.json'),
        'CSV_sha256': receipt['CSV_sha256'], 'research_not_formal_promotion': True, 'promotion_gates_passed': False}
    delivery = {'id': 'S2-MISION017-F3c-RESEARCH', 'author_recipe': 'Claude', 'author_replay_audit_upload': 'Codex',
        'status': 'scored_research_exception_not_formal_promotion', 'output': w.rel(OUT), 'CSV': admission['CSV'],
        'receipt': best['receipt'], 'receipt_sha256': best['receipt_sha256'], 'ref': receipt['ref'],
        'public_score': receipt['public_score'], 'gain_vs_C1': gain, 'gap_to017': gap,
        'received_forecast': .1666, 'received_forecast_error_actual_minus_expected': receipt['public_score'] - .1666,
        'new_fits': 0, 'new_C0_fits': 0, 'new_submissions': 1, 'private_score_not_read': True,
        'no_final_selection': True, 'formal_promotion': False, 'promotion_gates_passed': False,
        'forum': json.loads(response.stdout)}
    counters = R / 'registro/semana2_contadores_propios_actual.json'; c = w.read(counters)
    counted = c['phase2_F3c_research_submission'].copy(); assert counted['new_submissions'] == 1 and counted['ref'] == receipt['ref']
    counted.update(status='COMPLETE', public_score=receipt['public_score'], receipt=best['receipt'], receipt_sha256=best['receipt_sha256'])
    w.update(counters, {'as_of_utc': stamp.isoformat(), 'phase2_F3c_research_submission': counted}, archive)
    w.update(P, {'utc': stamp.isoformat(), 'status': 'active', 'previous_best_user_team_public_receipt': previous_best,
        'best_user_team_public_receipt': best, 'previous_delivery': phase['current_delivery'], 'current_delivery': delivery,
        'latest_official_public_receipt': {'path': best['receipt'], 'sha256': best['receipt_sha256'], 'best': best},
        'last_quota': receipt['limits'], 'active_external_submission': None, 'pending_research_delivery': None,
        'active_jobs': [], 'active_execution': None, 'next_unit': next_unit, 'goal_achieved': False,
        'gap_to017': gap, '2024_open': True, '2024_closed': False,
        'current_goal_turn_evidence': {'classification': 'progress', 'evidence': 'T10 closed-factor and T11 joint-GLM comparisons completed; one F3c research upload processed0.16914, gain0.00395; all failures and limits preserved.'}}, archive)
    state_path = ROOT / 'Preparación/ESTADO_PROYECTO.json'; branch = w.read(state_path)['week_2_mission017_phase2_20261025'].copy()
    branch.update(current_delivery=delivery, best_user_team_public_receipt=best, pending_research_delivery=None,
        next_unit=next_unit, active_jobs=[], new_submissions=2, status='active', goal_achieved=False, gap_to017=gap)
    w.update(state_path, {'week_2_mission017_phase2_20261025': branch,
        'week_2_mission017_phase2_external_submission': None}, archive)
    w.update(ROOT / 'RUTAS_PROYECTO.json', {'week_2_mission017_F3c_research_submission': best['receipt'],
        'week_2_mission017_F3c_research_report': w.rel(doc), 'week_2_mission017_F3c_research_CSV': admission['CSV']['path']}, archive)
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT / 'Preparación' / name, note, archive)
    (OUT / 'completion_receipt.json').write_text(json.dumps(delivery, ensure_ascii=False, indent=2), encoding='utf8')
    (OUT / 'closure_manifest.json').write_text(json.dumps({'utc': stamp.isoformat(), 'files': {
        p.relative_to(OUT).as_posix(): w.sha(p) for p in OUT.rglob('*') if p.is_file() and 'state_cuts' not in p.parts and 'dryrun_temp' not in p.parts}}, indent=2), encoding='utf8')
    print(json.dumps({'status': 'COMPLETE', 'ref': receipt['ref'], 'public_score': receipt['public_score'], 'gain_vs_C1': gain,
        'gap_to017': gap, 'phase_submissions_count_unchanged': 2, 'available_slots': 0, 'goal_status': 'active',
        'formal_promotion': False, 'forum_id': delivery['forum']['id']}))

if __name__ == '__main__': main()
