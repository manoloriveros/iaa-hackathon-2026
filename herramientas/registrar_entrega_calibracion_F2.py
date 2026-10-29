"""Registra el recibo procesado y conserva la misión y el cupo restante."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('writer', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'calibracion_F2_creible_20261025_v1'
P = R / 'registro/semana2_mision017_fase2_actual.json'

def main():
    assert not (OUT / 'completion_receipt.json').exists()
    receipt = w.read(OUT / 'public_receipt.json'); report = w.read(OUT / 'report.json'); admission = w.read(OUT / 'admission.json')
    assert receipt['status'] == 'COMPLETE' and receipt['ref'] == 57651126
    csv = ROOT / report['CSV']['path']; assert w.sha(csv) == receipt['CSV_sha256'] == report['CSV']['sha256']
    assert receipt['filename'] == csv.name and receipt['bytes'] == csv.stat().st_size
    phase = w.read(P); old = phase['best_user_team_public_receipt']; assert old['public_score'] == .16033
    gain = receipt['public_score'] - old['public_score']; forecast_gap = receipt['public_score'] - report['approximate_public_forecast']
    stamp = datetime.now(timezone.utc); archive = OUT / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    next_unit = (
        'Priorizar una mejora estructural con la composición real de 2025, sin gastar el último cupo en sondas menores. '
        'Primero revisar el clima de 2025 suministrado oficialmente y su semántica/variación frente a 2023–2024, reutilizando F05 y E13 para no repetir búsquedas o recetas. '
        'Distinguir los covariables oficiales entregados para una predicción condicional de una afirmación prospectiva de disponibilidad a la fecha de cotización; '
        'no traer observaciones futuras de fuera del concurso ni etiquetas de 2025. Resolver explícitamente ese alcance antes de cambiar una receta. '
        'El experimento E13 de clima anual y el FS/GLM fuente de cuatro años ya existen: no presentarlos como una familia nueva ni repetirlos sin una diferencia material. '
        'Si una incertidumbre cambia, congelar hipótesis/código/criterio/coste antes de ajustar o puntuar. '
        'No promover formalmente por el público, activar colas antiguas, sustituir B00/F2 o usar el último cupo sin una mejora sustentada. '
        '2024 permanece abierto como desarrollo; objetivo 0,17 activo, sin necesidad de una nueva pregunta al participante.')
    note = '\n\n## Entrega creíble de F2 procesada, 25 de octubre de 2026 (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. Kaggle procesó la referencia {receipt["ref"]}: D² público {receipt["public_score"]:.5f}, '
    note += f'frente a {old["public_score"]:.5f} de F2, una mejora de {gain:.5f}. '
    note += ('La cuota actual confirma nueve envíos del día, 21 totales y un cupo disponible. No se marca una entrega final. '
        'El objetivo 0,17 aún no se cumple; la diferencia pendiente es ' + f'{.17 - receipt["public_score"]:.5f}' + '.\n\n'
        'Se reprodujo exactamente el candidato creíble ya definido por Claude, con ejecución y auditoría de Codex. '
        'El archivo contiene 209.063 filas en el orden oficial, SHA 1a003d8682f1fcd71ad4a44f59f785d394488fc1cc95e60722f418b04c30ef29, '
        'y total 87.294.622,34 CU. Las identidades de nivel y las parábolas existentes se cotejaron con recibos públicos oficiales, '
        'la fórmula se verificó por otro método y los cinco controles del skill Kaggle pasaron. '
        'No hubo entrenamiento, C0 nuevo, recuperación de etiquetas individuales ocultas o cambio de parámetros después de ver este recibo.\n\n'
        'La calibración usa información del público y, por tanto, este score no es confirmación independiente. '
        'La previsión aproximada era ' + f'{report["approximate_public_forecast"]:.5f}' + '; el desvío es ' + f'{forecast_gap:+.5f}' + ', '
        'dentro del umbral de revisión de 0,0005 de la propuesta original. La forma de autos nuevos extrapola más allá de los tres puntos medidos. '
        'La cartera de 2025 contiene 76,04 % de nuevo negocio frente a 11,93 % en 2023 y 15,31 % en 2024. '
        'La simulación histórica de otro asistente, con A1 como sustituto, no acredita por sí sola la ganancia privada de esta cartera. '
        'La incertidumbre de reservas, cola, maestros sin fecha y transporte entre mercados sigue abierta.\n\n'
        'La decisión de enviar una única entrega de investigación se dejó en el foro antes del POST, bajo la autorización y autonomía expresas del participante. '
        'El marcador de inicio exclusivo impide repetir un envío incierto y la última conciliación exigió dos cupos antes de gastar uno. '
        'Se verificaron referencia, nombre, bytes y SHA del CSV al recoger el estado COMPLETE. No se leyó el score privado ni se alteraron las colas ajenas. '
        'Los GLM de la tanda 6 permanecen adversos; la mejora pública de esta calibración no los promueve.\n\n'
        'B00, F2, todas las alternativas y las versiones fallidas se conservan. 2024 continúa abierto como desarrollo adaptativo, '
        'sin presentarlo como holdout intacto ni la colaboración de IA como revisión profesional independiente. '
        'Se conserva el único cupo restante para una mejora con evidencia nueva.\n\n'
        'Evidencia: ' + w.rel(OUT / 'public_receipt.json') + '; ' + w.rel(OUT / 'report.json') + '.\n\nSiguiente unidad: ' + next_unit + '\n')
    doc = R / 'docs/archivo/semana2/MISION017_CALIBRACION_F2_ENVIO_RESULTADO.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    body = OUT / 'forum_resultado.md'; body.write_text(note, encoding='utf8')
    forum = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-CALF2-RESULTADO', '--asunto',
        'Kaggle COMPLETE: 0,16519, mejora de 0,00486; un cupo conservado', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    summary = {'id': 'S2-MISION017-C1-F2-CREIBLE', 'author_recipe': 'Claude', 'author_replay_audit_upload': 'Codex',
        'status': 'scored_research_not_formal_promotion', 'output': w.rel(OUT), 'CSV': report['CSV'],
        'receipt': w.rel(OUT / 'public_receipt.json'), 'receipt_sha256': w.sha(OUT / 'public_receipt.json'),
        'ref': receipt['ref'], 'public_score': receipt['public_score'], 'gain_vs_F2': gain,
        'forecast_gap': forecast_gap, 'new_fits': 0, 'new_C0_fits': 0, 'new_submissions': 1,
        'private_score_not_read': True, 'no_final_selection': True, 'forum': json.loads(forum.stdout)}
    (OUT / 'closure_manifest.json').write_text(json.dumps({'utc': stamp.isoformat(), 'files': {
        p.relative_to(OUT).as_posix(): w.sha(p) for p in OUT.rglob('*') if p.is_file() and 'state_cuts' not in p.parts and 'scratch_dryrun' not in p.parts}}, indent=2), encoding='utf8')
    (OUT / 'completion_receipt.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf8')
    counters = R / 'registro/semana2_contadores_propios_actual.json'; count = w.read(counters)
    assert 'phase2_C1_F2_calibrated_delivery' not in count
    w.update(counters, {'as_of_utc': stamp.isoformat(), 'phase2_C1_F2_calibrated_delivery': {
        'new_fits': 0, 'new_C0_fits': 0, 'new_submissions': 1, 'receipt': summary}}, archive)
    best = {'ref': receipt['ref'], 'date_UTC': receipt['date_UTC'], 'status': receipt['status'], 'public_score': receipt['public_score'],
        'bytes': receipt['bytes'], 'source_author': 'Claude recipe/F2', 'transport_author': 'Codex current phase',
        'replay_audit_author': 'Codex', 'receipt': summary['receipt'], 'receipt_sha256': summary['receipt_sha256'],
        'CSV_sha256': receipt['CSV_sha256'], 'research_not_formal_promotion': True}
    assert best['public_score'] > old['public_score'] and best['public_score'] < .17
    w.update(P, {'utc': stamp.isoformat(), 'status': 'active', 'previous_best_user_team_public_receipt': old,
        'best_user_team_public_receipt': best, 'current_delivery': summary,
        'latest_official_public_receipt': {'path': summary['receipt'], 'sha256': summary['receipt_sha256'], 'best': best},
        'new_submissions': phase['new_submissions'] + 1, 'last_quota': receipt['limits'], 'active_execution': None,
        'active_jobs': [], 'next_unit': next_unit, '2024_open': True, '2024_closed': False, 'goal_achieved': False}, archive)
    state_path = ROOT / 'Preparación/ESTADO_PROYECTO.json'; state = w.read(state_path)
    branch = state['week_2_mission017_phase2_20261025'].copy()
    branch.update(current_delivery=summary, best_user_team_public_receipt=best, next_unit=next_unit, active_jobs=[], status='active', goal_achieved=False,
        latest_official_public_receipt={'path': summary['receipt'], 'sha256': summary['receipt_sha256'], 'best': best})
    w.update(state_path, {'week_2_mission017_phase2_20261025': branch, 'week_2_mission017_phase2_execution': None}, archive)
    w.update(ROOT / 'RUTAS_PROYECTO.json', {'week_2_mission017_credible_F2_submission': summary['receipt'],
        'week_2_mission017_credible_F2_report': w.rel(doc)}, archive)
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT / 'Preparación' / name, note, archive)
    print(json.dumps({'goal_status': 'active', 'processed_public_score': receipt['public_score'], 'gain': gain,
        'remaining_daily_slots': receipt['limits']['num_allowed_now'], 'goal_achieved': False,
        'forum_id': summary['forum']['id'], 'new_fits': 0, 'new_submissions': 1}))

if __name__ == '__main__':
    main()
