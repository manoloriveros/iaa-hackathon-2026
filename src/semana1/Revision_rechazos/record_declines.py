"""Cierre inmutable de REN00; actualiza memoria y revisión, no el catálogo de datos."""
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


def number(v, decimals=0):
    return f'{v:,.{decimals}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def main(out):
    assert '--figure-inspected' in sys.argv, 'Record actual figure inspection before closure.'
    assert not (out / 'manifest.json').exists(), 'Already closed; never overwrite.'
    s = json.loads((out / 'summary.json').read_text('utf-8'))
    ver = json.loads((out / 'verification.json').read_text('utf-8'))
    ui = json.loads((out / 'interface_verification.json').read_text('utf-8'))
    assert ver['failed'] == ui['failed'] == 0 and ui['all_2742_policies_exercised']
    protected = json.loads((out / 'protected_hashes_before.json').read_text('utf-8'))
    assert all(c.digest(ROOT / p) == sha for p, sha in protected.items())
    now = datetime.now(timezone.utc).isoformat()
    manifest = {'created_utc': now, 'type': 'immutable_declined_renewal_review_no_data_changes', 'files': [
        {'path': p.relative_to(out).as_posix(), 'sha256': c.digest(p), 'bytes': p.stat().st_size}
        for p in sorted(out.rglob('*')) if p.is_file()]}
    c.dump(out / 'manifest.json', manifest)
    paths = {name: ROOT / 'Preparación' / name for name in ['ESTADO_PROYECTO.json', 'MEMORIA_PROYECTO.md', 'DECISIONES.md']}
    paths['RUTAS_PROYECTO.json'] = ROOT / 'RUTAS_PROYECTO.json'
    # Read current shared documents immediately before the append, retaining unrelated fields.
    state = json.loads(paths['ESTADO_PROYECTO.json'].read_text('utf-8'))
    memory = paths['MEMORIA_PROYECTO.md'].read_text('utf-8')
    decisions = paths['DECISIONES.md'].read_text('utf-8')
    routes = json.loads(paths['RUTAS_PROYECTO.json'].read_text('utf-8'))
    decision = 'D' + str(max(map(int, re.findall(r'\bD(\d+)\b', decisions))) + 1)
    rel = out.relative_to(ROOT).as_posix()
    close = BASE / 'closures' / datetime.now(timezone.utc).strftime('closure_%Y%m%dT%H%M%SZ')
    close.mkdir(parents=True, exist_ok=False)
    for name, p in paths.items():
        shutil.copy2(p, close / ('before_' + name))
    review = {'decision_id': decision, 'rule': 'REN00', 'status': 'verified_review_only_decision_semantics_pending',
        'run': '../' + rel, 'report': '../' + rel + '/informe.html', 'proposal': '../' + rel + '/proposal.json',
        'verification': '../' + rel + '/verification.json', 'index': '../Hackaton/Semana 1/Revision_rechazos/current_run.json',
        'frozen_policies': 2742, 'motor': 1513, 'buildings': 1010, 'contents': 219,
        'policy_history_rows': s['cohort_history_periods'], 'claim_history_rows': s['cohort_history_claims'],
        'test_rows_to_preserve': s['cohort_2025_rows'], 'same_customer': s['same_customer'], 'changed_motor_address': s['changed_address'],
        'multiple_declines_in_history': s['cohort_multiple_declines'], 'three_declines_in_history': s['cohort_three_declines'],
        'policies_no_observed_2024_occurrences': s['2024_no_observed_claim_policies'],
        'preceding_net_observed_CU': s['preceding_net_CU'], 'preceding_cost_share_2024_pct': s['preceding_cost_share_2024_pct'],
        'calendar_dates_pending_by_participant': True, 'dates_modified': False, 'exposure_modified': False,
        'decisions_reclassified': False, 'claims_modified': False, 'active_dataset_changed': False,
        'models_trained': False, 'correction_authorized': False, 'source_semantics_confirmed': False,
        'independent_validation': False, 'technical_checks': ver['passed'], 'interface_logic_checks': ui['passed'],
        'all_2742_policies_interaction_checked': True, 'case_histories': s['case_count'], 'control_policies': s['control_policies'],
        'figure_visually_inspected': True, 'browser_rendering_verified': False,
        'renewal_decision_predictor_exclusion_already_in_protocol': '1.3', 'pending_capitals_unchanged': 1454,
        'CON01_activated': False, 'closure': '../' + close.relative_to(ROOT).as_posix()}
    state['declined_renewal_review'] = review
    state['calendar_review']['participant_followup'] = {'decision_id': decision, 'dates_remain_pending': True,
        'instruction': 'Dejemos las fechas pendientes', 'calendar_correction_authorized': False}
    state['memory_as_of'] = now
    routes['week_1_declined_renewal_review_index'] = 'Hackaton/Semana 1/Revision_rechazos/current_run.json'
    paragraph = f'''

### {decision}, rechazos de renovación con continuidad y tratamiento REN00, 16 de octubre de 2026, America/Bogota

El participante dejó explícitamente las fechas pendientes y pidió revisar las 2.742 pólizas declined_by_insurer con sucesor 2025, historiales/siniestros, ejemplos y propuesta sin modificar datos. Nueva evidencia ../{rel}, sobre el catálogo DUP01, con cohorte exacta D43 congelada por par de row_id: 1.513 motor, 1.010 edificios y 219 contenidos. Reconstrucción de adyacencias desde las seis tablas fuente coincide con la lista. Se conservan {number(s['cohort_history_periods'])} periodos completos y {number(s['cohort_history_claims'])} expedientes de las pólizas, doce casos explicados y dos controles fuera de cohorte; el explorador permite inspeccionar cada una de las 2.742 pólizas. La comparación histórica y los controles no amplían la cohorte propuesta.

Todos los sucesores conservan cliente, aumentan renewal_count en uno y new_business es falso. Hay 22 cambios de dirección de motor, conservados. Las filas 2024 terminan el 30 de diciembre y siguen el 1 de enero, manteniendo CAL00 sin resolver. Las pólizas suman {number(s['cohort_2025_rows'])} filas de test 2025 por sus segmentos intranuales; conservarlas todas para predecir por periodo, sin borrarlas ni imponer cero por el rechazo previo. El campo literal no prueba cobertura contractual del día omitido.

La etiqueta no se comporta como estado absorbente de salida en los años 2021–2024. En 2024 hay 3.002 declined_by_insurer: 2.742 con sucesor y 260 sin sucesor observado. En la cohorte, 83 pólizas tienen más de un rechazo registrado y dos tienen tres. Sin sucesor en los archivos no acredita el motivo o momento de la baja. Entre las 2.742, hay 372 sin siniestros observados con ocurrencia en todo 2024; la falta de reporte al corte impide inferir pérdida última cero. También existen renewed con coste alto. La asociación de la etiqueta con severidad no identifica causa, intención del generador ni umbral determinista. No se reverse-engineerea una regla de corrección ni se elige tratamiento por score.

Los últimos segmentos 2024 de la cohorte contienen 2.855 expedientes, 2.850 aceptados y cinco repudiated. El neto incurrido aceptado es {number(s['preceding_net_CU'], 2)} CU, con reserva de casos abiertos de {number(s['preceding_open_reserve_CU'], 2)} CU incluida en el incurrido. Representan {number(s['preceding_row_share_2024_pct'], 4)} % de filas 2024 y {number(s['preceding_exposure_share_2024_pct'], 4)} % de exposición, pero {number(s['preceding_cost_share_2024_pct'], 4)} % de su neto observado. Los componentes se suman en céntimos y se concilian por separado con Decimal. Los escenarios de excluir solo el último segmento o todos los segmentos 2024 de esas pólizas cuantifican sesgo de selección, sin aplicar exclusiones ni estimar tarifa definitiva, pérdida última o beneficio predictivo.

REN00 recomienda conservar pólizas, fechas, primas, exposición y siniestros, y mantener semántica de declined_by_insurer pendiente en auditoría. No recodificar a renewed: pueden existir decisión preliminar/revertida, otra oferta o etiqueta sin propagación a supervivencia; faltan timestamps, motivos, ofertas y confirmación del generador. El protocolo 1.3 ya excluye renewal_decision del modelo por ser resultado del periodo y ausente en test; también deben quedar fuera sucesores/REN00/diagnósticos monetarios. No incorporar automáticamente el rechazo del año previo como predictor sin disponibilidad y semántica acreditadas. No se cambia el protocolo ni se afirma tener el control F0 operativo.

declined_by_insurer es estado/decisión de póliza; repudiated es estado de expediente. El primero no anula pagos o reservas cubiertos del periodo anterior. La asignación sigue por loss_date en intervalo inclusivo y el objetivo excluye repudiated por su propio estado, conservando conciliación. Los reportes posteriores al periodo no cambian el año de ocurrencia. La última ocurrencia 29-12 y reporte 30-12 de 2024 mantienen las limitaciones de truncamiento/desarrollo. No hay etiquetas de siniestros 2025; sus columnas diagnósticas quedan ausentes, sin fabricar ceros.

Preguntas preparadas, sin contactar a terceros: definición de rechazo final o recomendación/oferta, momento de firmeza y disponibilidad, reversión bajo mismo ID, propagación a periodos posteriores y fuente del motivo. Sin aclaración, conservar la limitación semántica. Una futura normalización autorizada podría crear una marca de auditoría o estado desconocido/contradictorio junto al literal; una corrección efectiva a renewed exigiría confirmación y otra capa con bitácora reversible. Continuidad observada puede ser una etiqueta para otro estudio de retención con corte propio, sin sustituir el dato oficial ni entrar como predictor de tarifa.

Pasaron {ver['passed']} comprobaciones propias de fuentes, cohorte, historias con cada campo original, adyacencias, asignación por ocurrencia, conciliación Decimal y sensibilidad. Pasaron {ui['passed']} pruebas de lógica del explorador con DOM mínimo, recorriendo las 2.742 pólizas y doce casos. Figura inspeccionada; sin renderizado real de navegador o validación independiente acreditados. Manifiesto SHA256 y código/contexto archivados. Todos los originales, siete derivados y puntero/catálogo activo conservan hashes; D43 y demás corridas históricas no se reescriben. No se modificó dato ni etiqueta, no se materializó T0 operativo, no hubo entrenamiento, proveedor externo, envío, nueva dependencia o delegación. CAP01 2.073 y los 1.454 capitales pendientes mantienen su estado; CON01 no se activa.

Aplican IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2, §3.3 y §§3.5–3.6. Codex trazó evidencia, contrastó hipótesis y propuso el tratamiento; el participante autorizó revisión, no reclasificación ni borrado. Consultar declined_renewal_review y Revision_rechazos/current_run.json.
'''
    paths['DECISIONES.md'].write_text(decisions.rstrip() + paragraph, encoding='utf-8')
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip() + f'\n\nRevisión de rechazos {decision}: las 2.742 pólizas D43 (1.513/1.010/219) conservan cliente y contador, con 22 mudanzas de motor; suman {number(s["cohort_2025_rows"])} filas test que deben conservarse. 83 tienen rechazos repetidos y 372 no tienen siniestro observado de ocurrencia 2024. Los últimos segmentos concentran {number(s["preceding_net_CU"], 2)} CU y {number(s["preceding_cost_share_2024_pct"], 4)} % del neto observado 2024: no borrarlas por la etiqueta. REN00 conserva la decisión literal pendiente; renewal_decision ya está fuera de predictores según protocolo 1.3. No recodificar a renewed ni confundir rechazo de póliza con repudiated. Fechas pendientes por instrucción expresa, sin cambios de datos/catálogo. [Informe con doce casos y explorador completo](../{rel}/informe.html); {ver["passed"]} controles de datos y {ui["passed"]} de interfaz. Ver declined_renewal_review y {decision}.\n', encoding='utf-8')
    c.dump(paths['ESTADO_PROYECTO.json'], state)
    c.dump(paths['RUTAS_PROYECTO.json'], routes)
    index = BASE / 'current_run.json'
    c.dump(index, {'workspace_relative_run': rel, 'report_workspace_relative': rel + '/informe.html', 'decision_id': decision,
        'status': review['status'], 'frozen_policies': 2742, 'data_changes': False, 'calendar_dates_pending': True})
    assert all(c.digest(ROOT / p) == sha for p, sha in protected.items())
    assert all(c.digest(out / e['path']) == e['sha256'] for e in manifest['files'])
    c.dump(close / 'closure.json', {'created_utc': now, 'decision_id': decision, 'review': review,
        'manifest_sha256': c.digest(out / 'manifest.json'), 'source_and_active_hashes_preserved': True,
        'post_documents': {p.relative_to(ROOT).as_posix(): c.digest(p) for p in list(paths.values()) + [index]}})
    print(json.dumps({'decision': decision, 'report': str(out / 'informe.html'), 'closure': str(close)}, ensure_ascii=False))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
