"""Cierra la evidencia verificada y actualiza solo memoria e índice de revisión."""
from pathlib import Path
from datetime import datetime, timezone
import json
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'Hackaton/Semana 1/Limpieza'))
import clean_data as c


def main(out):
    if '--figure-inspected' not in sys.argv:
        raise RuntimeError('Record actual figure inspection explicitly before closure.')
    assert not (out / 'manifest.json').exists(), 'Already closed; do not overwrite.'
    summary = json.loads((out / 'summary.json').read_text('utf-8'))
    verify = json.loads((out / 'verification.json').read_text('utf-8'))
    ui = json.loads((out / 'interface_verification.json').read_text('utf-8'))
    assert verify['failed'] == ui['failed'] == 0
    protected = json.loads((out / 'protected_hashes_before.json').read_text('utf-8'))
    assert all(c.digest(ROOT / p) == sha for p, sha in protected.items())
    now = datetime.now(timezone.utc).isoformat()
    manifest = {'created_utc': now, 'type': 'immutable_calendar_review_no_data_changes', 'files': [
        {'path': p.relative_to(out).as_posix(), 'sha256': c.digest(p), 'bytes': p.stat().st_size}
        for p in sorted(out.rglob('*')) if p.is_file()]}
    c.dump(out / 'manifest.json', manifest)
    # Read latest shared documents immediately before appending, preserving other work.
    state_path = ROOT / 'Preparación/ESTADO_PROYECTO.json'
    decisions_path = ROOT / 'Preparación/DECISIONES.md'
    memory_path = ROOT / 'Preparación/MEMORIA_PROYECTO.md'
    routes_path = ROOT / 'RUTAS_PROYECTO.json'
    state = json.loads(state_path.read_text('utf-8'))
    decisions = decisions_path.read_text('utf-8')
    memory = memory_path.read_text('utf-8')
    routes = json.loads(routes_path.read_text('utf-8'))
    decision = 'D' + str(max(map(int, re.findall(r'\bD(\d+)\b', decisions))) + 1)
    rel = out.relative_to(ROOT).as_posix()
    close = BASE / 'closures' / datetime.now(timezone.utc).strftime('closure_%Y%m%dT%H%M%SZ')
    close.mkdir(parents=True, exist_ok=False)
    for name, source in {'state': state_path, 'decisions': decisions_path, 'memory': memory_path, 'routes': routes_path}.items():
        shutil.copy2(source, close / ('before_' + source.name))
    review = {'decision_id': decision, 'status': 'verified_review_only_dates_pending', 'rule': 'CAL00',
        'run': '../' + rel, 'report': '../' + rel + '/informe.html', 'verification': '../' + rel + '/verification.json',
        'proposal': '../' + rel + '/proposal.json', 'review_index': '../Hackaton/Semana 1/Revision_calendario/current_run.json',
        'gap_continuities': 500245, 'coherent_renewed_labels': 497503, 'declined_but_continued': 2742,
        'same_customer': summary['same_customer'], 'same_address': summary['same_address'], 'address_changes': 3153,
        'all_affected_policy_history_rows': summary['all_affected_history_rows'],
        'all_affected_claim_history_rows': summary['all_affected_claim_rows'],
        'latest_observed_loss': summary['claim_max_loss_date'], 'latest_observed_report': summary['claim_max_report_date'],
        'reported_valuation_date': '2024-12-31', 'coverage_convention_confirmed': False, 'report_cutoff_confirmed': False,
        'case_histories': summary['case_count'], 'technical_checks': verify['passed'], 'interface_logic_checks': ui['passed'],
        'figure_visually_inspected': True, 'browser_rendering_verified': False, 'dates_modified': False,
        'exposure_modified': False, 'claims_modified': False, 'active_dataset_changed': False,
        'correction_authorized': False, 'independent_validation': False, 'models_trained': False,
        'pending_capitals_unchanged': 1454, 'CON01_activated': False,
        'closure': '../' + close.relative_to(ROOT).as_posix()}
    state['calendar_review'] = review
    state['memory_as_of'] = now
    routes['week_1_calendar_review_index'] = 'Hackaton/Semana 1/Revision_calendario/current_run.json'
    paragraph = f'''

### {decision}, revisión del calendario 2024 y del corte de reportes, 16 de octubre de 2026, America/Bogota

Solicitud: revisar las 500.245 continuidades, historiales de pólizas/siniestros, ejemplos y tratamiento, sin modificar fechas. La corrida ../{rel} reconstruye adyacencias sobre los 3.035.950 periodos del catálogo DUP01 y reproduce exactamente la cohorte D40: 200.063 motor, 150.111 edificios y 150.071 contenidos. Todas terminan el 30-12-2024 y siguen el 01-01-2025, con un día omitido y el mismo cliente. La dirección coincide en 497.092 pares; hay 3.153 cambios de dirección de motor, 3.131 con renewed y 22 con rechazo. Modelo, cobertura y grupo de valor permanecen iguales en todos los 200.063 pares motor comparados, sin VIN para comprobar vehículo físico. No hay otras brechas positivas ni solapamientos. Las 500.245 filas que terminan ese 30 tienen sucesor, sin un conjunto adicional con ese cierre que no continúe. Se archivan los historiales completos de {summary['all_affected_history_rows']:,} periodos y {summary['all_affected_claim_rows']:,} expedientes actuales de la cohorte; trece casos reales, incluido un control de cancelación y un cambio de dirección de motor muestran los límites de inferencia.

497.503 precedentes dicen renewed; 2.742 dicen declined_by_insurer pese al sucesor (1.513 motor, 1.010 edificios, 219 contenidos). Conservar esa contradicción como revisión separada, sin convertir etiquetas ni inferir cobertura contractual solo por el ID o dirección. El patrón de cierres es el día 365 de cada año; en 2024 es el 30 de diciembre. El 29 de febrero sí está presente, con 90 siniestros. Es evidencia a favor de una generación de 365 posiciones o defecto de año bisiesto, no confirmación de su mecanismo ni intención.

El máximo loss_date es 29-12-2024 y report_date 30-12-2024, pese a describirse valoración al 31. Hay 111 reportes el 30 y ninguno el 31; las ocurrencias son cero tanto el 30 como el 31. El retraso mínimo observado es un día. El corte de reportes al 30 es compatible con última ocurrencia observable al 29; no prueba ausencia de riesgo o cobertura en los días finales. Se reconstituye la asignación inclusiva por ocurrencia y concilia con DUP01; los 413 registros anteriores a historia permanecen separados. No desplazar ocurrencias ni reportes, ni inventar pérdidas cero o coste del día omitido. Reporte y valoración no son la misma fecha.

CAL00 recomienda conservar fechas publicadas y EXP01 como escenario base por periodo; la marca solo existe en evidencia diagnóstica. Se proponen sensibilidades aritméticas sin datos corregidos: añadir un día a todos suma 500245/365 = 1.370,534247 años exactos ACT/365; al subconjunto renewed, 497503/365 = 1.363,021918. La tabla registra también diferencias de redondeo por fila y denominadores completos 2024. Son movimientos con numerador observado fijo, no tarifa definitiva, IBNR, pérdida última o mejora predictiva. Una fila de dos días pasaría hipotéticamente de 0,0055 a 0,0082; una de 365 a 366 días da 1,0027. ACT/365 y ACT/ACT son decisiones distintas de extender fechas; no imponer tope 1 manteniendo ACT/365. No recalcular written_premium sin reglas contractuales.

Antes de corregir falta confirmar con la fuente las 365 posiciones, la cobertura del día 366, el corte de reportes al 30, la base anual y las renovaciones rechazadas con sucesor. Las preguntas están preparadas, sin contactar a terceros. Si se confirma cobertura civil completa, la propuesta futura es extender solo el último segmento 2024 en otra capa, recalcular exposición desde fechas bajo base explícita y conservar bitácora reversible y cohorte/hash; no extender bajas tempranas ni todos los segmentos. El caso de rechazo contradictorio requiere resolución adicional. El uso de test 2025 es exclusivamente para comprobar continuidad y periodos provistos, sin etiquetas, entrenamiento o consulta de score.

Pasaron {verify['passed']} controles propios de datos, fuentes, adyacencias, historias completas, asignación, sensibilidad y enlaces; {ui['passed']} controles de lógica interactiva con DOM mínimo ejercitan trece casos, importes y navegación. La figura se inspeccionó visualmente; no se acredita renderizado real de navegador ni validación independiente. Los once originales, seis pólizas/test, claims DUP01, puntero y catálogos activos conservan hashes. Ningún cambio de fechas, exposición, prima, siniestros o catálogo, ningún modelo, proveedor externo, envío o delegación. CAP01 2.073 y los 1.454 capitales pendientes conservan su estado; CON01 no se activa. Se actualizan memoria, estado, rutas e índice de esta revisión, sin editar corridas históricas.

Aplican IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6. Codex contrastó hipótesis, calculó evidencia y propuso alternativas; la fuente no ha confirmado intención, y el participante no ha autorizado correcciones de calendario. Ver calendar_review y Revision_calendario/current_run.json.
'''
    c.dump(state_path, state)
    decisions_path.write_text(decisions.rstrip() + paragraph, encoding='utf-8')
    memory_path.write_text(memory.rstrip() + f'\n\nRevisión de calendario {decision}: 500.245 brechas del 31-12-2024, todas de un día y con el mismo cliente; hay 3.153 cambios de dirección de motor. 497.503 renewed y 2.742 declined_by_insurer pese a sucesor. Cierres en día 365; existen 90 siniestros en 29 de febrero. Última ocurrencia 29-12 y reporte 30-12, con retraso mínimo un día: no inferir riesgo cero en fechas finales. CAL00 deja fechas y EXP01 pendientes de confirmación, sin activar marca de modelado ni ampliar cobertura. Historiales completos y trece casos en [informe](../{rel}/informe.html); {verify["passed"]} controles de datos y {ui["passed"]} de interfaz. No se cambia el catálogo DUP01 ni los 1.454 capitales pendientes. Consultar calendar_review y la decisión para condiciones de una corrección futura.\n', encoding='utf-8')
    c.dump(routes_path, routes)
    c.dump(BASE / 'current_run.json', {'workspace_relative_run': rel, 'report_workspace_relative': rel + '/informe.html',
        'status': review['status'], 'decision_id': decision, 'gap_continuities': 500245, 'dates_modified': False,
        'active_dataset_changed': False})
    assert all(c.digest(ROOT / p) == sha for p, sha in protected.items())
    assert all(c.digest(out / e['path']) == e['sha256'] for e in manifest['files'])
    c.dump(close / 'closure.json', {'created_utc': now, 'decision_id': decision, 'review': review,
        'manifest_sha256': c.digest(out / 'manifest.json'), 'source_and_active_hashes_preserved': True,
        'post_documents': {p.relative_to(ROOT).as_posix(): c.digest(p) for p in [state_path, decisions_path, memory_path, routes_path, BASE / 'current_run.json']}})
    print(json.dumps({'decision': decision, 'report': str(out / 'informe.html'), 'closure': str(close)}, ensure_ascii=False))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
