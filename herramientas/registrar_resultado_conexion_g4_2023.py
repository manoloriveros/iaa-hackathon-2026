"""Publica evidencia de la conexión ya validada, sin volver a leer sus tablas."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.metadata as md
import json
import os
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(REPO/'src'))
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import entradas_g4_2023 as ingress
from registrar_resultado_entradas_g4_2023 import top

RUN = REPO/'privado/semana2/conexion_g4_2023/contrato_20261024_v1'
PLAN = REPO/'registro/semana2_g4_conexion_plan_v1.json'
CONTRACT = REPO/'registro/semana2_g4_capital_contrato_v1.json'
INDEX = REPO/'registro/semana2_g4_conexion_actual.json'
DOC = REPO/'docs/archivo/semana2/G4_CONTRATO_CAPITAL_Y_CONEXION_2023.md'
PRIORITY = REPO/'registro/semana2_b20_prioridades_actual.json'
SOURCES = REPO/'registro/semana2_b20_fuentes2023_actual.json'
INGRESS_INDEX = REPO/'registro/semana2_g4_entradas2023_actual.json'
DEVELOPMENT = REPO/'registro/semana2_desarrollo2023_actual.json'
IDENT = 'S2-G4-CAPITAL-CONEXION2023-FINAL-v1-20261024'
FID = 'COD-S2-20261024-064'
STATEKEY = 'week_2_G4_capital_scope_contract_connection2023_v1_20261024'
STATUS = 'scope_capital_contract_and_input_connection_synthetic_verified_real_parameters_and_nested_objects_pending'
now = lambda: datetime.now(timezone.utc).isoformat()
rel = lambda p: p.relative_to(ROOT).as_posix()
sha = ingress.sha
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    assert not INDEX.exists() and not DOC.exists(), 'Reconcile partial registration before retry'
    plan = read(PLAN)
    result = read(RUN/'validated_current.json')
    out = ROOT/result['out']
    validation = read(out/'validation.json')
    assert result['success'] and validation['success'] and result['contract_checks'] == 55
    assert len(validation['checks']) == 55 and all(x['pass'] for x in validation['checks'])
    assert validation['capital_reference_max_abs_error'] <= 1e-12 and not validation['forbidden_calls']
    assert result['real_row_values_decoded'] == result['model_fits_including_synthetic'] == result['C0_calls_including_synthetic'] == 0
    assert not result['real_capital_application'] and not result['G4_real_full_flow_validated']
    assert all(sha(ROOT/p['path']) == p['sha256'] for p in plan['frozen_code'])
    assert sha(ROOT/plan['prepared_input_manifest']['path']) == plan['prepared_input_manifest']['sha256']
    requests = sorted((out/'real_requests').glob('*.json'))
    requirements = sorted((out/'capital_requirements').glob('*.json'))
    assert len(requests) == len(requirements) == 15
    assert all(read(p)['ppm_min'] is None and read(p)['ppm_max'] is None for p in requirements)
    dump(RUN/'connection_registry.json', {'id': IDENT, 'author': 'Codex', 'utc': now(),
        'contract': {'path': rel(CONTRACT), 'sha256': sha(CONTRACT)},
        'prepared_input_manifest': plan['prepared_input_manifest'],
        'entrypoint': 'semana2.conexion_g4_2023.connect_scope', 'status': 'blocked_missing_exact_scope_capital',
        'requests': [{'path': rel(p), 'sha256': sha(p), 'excluded_folds': read(p)['excluded_folds'],
                      'training_input_sha256': read(p)['training_input_sha256']} for p in requests],
        'capital_requirements': [{'path': rel(p), 'sha256': sha(p)} for p in requirements],
        'real_parameters_estimated': False, 'real_values_decoded': 0, 'fit_allowed': False,
        'C0_present': False, 'model_input_ready': False, 'synthetic_learner_marker_added': False})
    dump(RUN/'environment.json', {'python': sys.version, 'platform': sys.platform,
        'packages': {p: md.version(p) for p in ['numpy', 'pandas', 'pyarrow', 'scikit-learn', 'joblib']},
        'hosted_Kaggle_Linux_or_independent_reproduction_verified': False})
    ignored = subprocess.run(['git', 'check-ignore', '--quiet', str(out/'real_requests/exclude_0.json')], cwd=REPO)
    assert ignored.returncode == 0
    current = read(PRIORITY)
    matrix = read(ROOT/current['matrix']['path'])
    for card in matrix['cards']:
        if card['gate'] == 'G4':
            card.update(status=STATUS,
                what_changed='Contrato de capital por ámbito,15solicitudes del ingreso2023 y conexión numérica de entrada verificada con archivos sintéticos;55controles sin fit/C0.',
                required_evidence='Productor y parámetros de capital reales por ámbito con población/recibo verificables; flujo positivo de ese recibo y objetos interiores C0/preprocesado/GLM/calibradores con prueba integral cuando esté autorizado.',
                boundary='Conexión sintética y bloqueo temprano real comprobados; no ejecución real con parámetros ni invariancia de objetos aprendidos. G1/G2 sin cambios.')
    matrix.update(id=IDENT, author='Codex', utc=now(), source_previous_matrix=current['matrix'],
        verification_scope='Capital/data connection with generated fixtures and fixed constants; no model or C0 calls even synthetic')
    dump(RUN/'gate_matrix_updated_G4.json', matrix)
    decisions = [
        ('G4C-01', 'Conectar el lector estricto a una frontera G4 propia, sin llamar al aprendiz sintético o añadir su marcador a datos reales.'),
        ('G4C-02', 'Exigir capital ligado a exclusiones, firmas de ajuste/pertenencias, fuentes y origen; referencias finitas/positivas y recibo de productor para datos reales. No estimarlas implícitamente.'),
        ('G4C-03', 'Registrar15solicitudes reales y plantillas vacías; sin parámetros todas bloquean antes de leer valores y las constantes ficticias no las desbloquean.'),
        ('G4C-04', 'Aceptar55controles nuevos:15conexiones sintéticas,32filas de referencia Decimal/log, adversos,2invariancias de entradas,control de cambio permitido y contratos desde disco; no invariancia de objetos aprendidos.'),
        ('G4C-05', 'Mantener pendientes productor/parámetros reales de capital,flujo positivo de su recibo y objetos internos;no cerrar G4 ni resolver G1/G2 por este software.'),
        ('G4C-06', 'Conservar B00/alternativas/objetivo/exposición/C0/folds/catálogo/contadores;2024cerrado,cero ajustes incluso sintéticos,C0,inferencias o scores y ninguna promoción/envío.')]
    dump(RUN/'decision_journal.json', {'id': IDENT, 'author': 'Codex', 'utc': now(),
        'decisions': [{'id': k, 'decision': v} for k, v in decisions]})
    doc = f'''# G4: contrato de capital por ámbito y conexión de entradas

Codex, {now()}. Preinscripción COD-S2-20261024-063; resultado {FID}. El contrato y la conexión del ingreso de 2023 a la entrada base de G4 están implementados y comprobados con archivos sintéticos. Pasaron 55 controles. No se ajustaron modelos, tampoco sintéticos, ni se llamó a C0 para ajustar o aplicar; no hubo inferencias o scores.

| Comprobación nueva | Resultado |
| --- | --- |
| Lector por ámbito, capital fijo y siete predictores | 15 ámbitos sintéticos recorridos |
| Regla de capital con Decimal y `math.log` | 32 filas, error absoluto máximo {validation['capital_reference_max_abs_error']} (criterio 1e-12) |
| Valores protegidos alterados | 2 casos con tablas permitidas y firma de entrada idénticas |
| Cambio en un archivo permitido | Invalida el capital anterior; con otras constantes explícitas cambia la entrada |
| Contratos guardados y releídos | Mismo resultado, sin fit o C0 |
| Solicitudes de 2023 sin parámetros | 15 bloqueos antes de abrir valores |
| Constantes sintéticas ante solicitud real | Rechazadas antes de leer valores |

La función `semana2.conexion_g4_2023.connect_scope` valida la solicitud y el artefacto de capital antes de llamar al lector de valores. Con parámetros válidos, el recorrido numérico es lector estricto por folds, aplicación aritmética de capital, siete predictores y objetivos/notificaciones heredados, más metadatos y fechas/exposición enmascaradas para un C0 futuro. La prima queda fuera de predictores y de la tabla entregada al aprendizaje. El paquete resultante se identifica como `G4_BASE_INPUTS_ONLY`, con `fit_allowed=false`, `C0_present=false` y `model_input_ready=false`. No se estiman imputadores, escalas, categorías, modelos o calibradores.

El contrato `{rel(CONTRACT)}` exige mercado emergente, edificios, cohorte 2023, exclusiones exactas, firmas de pertenencias y entradas permitidas, archivos de capital y origen. Los parámetros deben ser positivos y finitos, con límite inferior no mayor al superior y umbral fijo de diez millones. La futura regla de estimación queda especificada sobre capitales normales del ajuste exacto y prima por mil válida; no hay productor implementado o parámetros reales estimados aquí. Su ausencia produce un bloqueo, sin usar referencias exteriores o un fallback.

La aplicación conserva capital positivo normal; para sospechosos aplica la división por mil solo si cumple la regla CAPS2-01 y deja los demás como ausentes. La prueba independiente con Decimal cubre capital normal, umbral exacto, sospechosos aceptados/rechazados, capital inválido y límite inferior inclusivo; `math.log` contrasta el predictor. Se usaron únicamente constantes ficticias fijadas antes del ensayo, no referencias estimadas de las filas.

Los parámetros reales necesitarán autor, fecha con zona y recibo de productor identificado por ruta/SHA, ligado al contenido del artefacto y al ajuste. Comprobar esas ligaduras no demuestra por sí solo que la estimación externa sea correcta. Ese productor, la evidencia de población y el flujo positivo con su recibo aún no existen ni están verificados. La prueba real de esta tarea cubre el bloqueo temprano y la separación de orígenes; ninguna fila real recibió capital calculado o un marcador sintético.

Las quince solicitudes y sus plantillas pendientes están en `{rel(out/'real_requests')}` y `{rel(out/'capital_requirements')}`. El registro consumible por G4 es `{rel(RUN/'connection_registry.json')}`. Se ligan al manifiesto de entrada preparado en el trabajo061/062; no se volvió a materializar ese ingreso ni se abrieron valores de datos reales. Las plantillas contienen `ppm_min=null`, `ppm_max=null` y procedencia pendiente: no son parámetros válidos. El punto de continuación es `{rel(RUN/'validated_current.json')}`.

La integración se probó desde Parquet generados mediante el mismo lector de producción. Cada ámbito impide abrir archivos de valores protegidos y conserva sus metadatos. Los dos controles de alteración protegida comparan todas las tablas de aprendizaje y la firma de entrada; el recibo archivístico de la solicitud cambia legítimamente al cambiar el manifiesto global. No se confunde esa firma con una prueba de invariancia de objetos aprendidos. Los adversos comprueban origen, ámbito, fuentes, hashes, números no finitos, umbral, campos de objetivo no admitidos, plantilla incompleta y procedencia.

Durante la verificación estuvieron bloqueados fit de modelos/preprocesadores, predict, C0 fit/apply, cargas de estimadores y red; el recibo registra cero llamadas prohibidas y cero lectores de filas reales. Las 287 lecturas de columnas registradas son únicamente archivos generados del ensayo. No se repitieron suites o diagnósticos históricos. Código congelado, configuración, entorno, solicitudes, fuentes de prueba y recibos quedan en la carpeta privada del ciclo. El trabajo previo y su paquete sintético se conservan.

G4 avanza al contrato de capital y conexión de entradas verificados sintéticamente. Quedan abiertos los parámetros y el productor de capital por ámbito, su integración positiva real y los objetos C0/preprocesado/GLM/calibradores interiores con comprobación integral bajo un encargo que permita crearlos. G1 y G2 conservan sus bloqueos; no hay nueva evidencia de mecanismo, soporte o cohorte. No se declara que el flujo real esté listo para entrenar o que se haya cerrado G4.

Decisiones G4C-01 a G4C-06. B00 y alternativas, T0/exposición/C0/folds/catálogo/contadores se conservan. 2024/test/ledger/actas/SEL01 siguen cerrados en este trabajo; la exposición previa a un asunto con información ajena de 2024 no se usa. Sin promoción, envío, publicación, remoto, otros chats, delegación o automatizaciones. Ventana nocturna cerrada. Verificación técnica propia de Codex en Windows, exploratoria, sin revisión profesional independiente ni aprobación humana. Se documentan procedencia y dependencias conforme a IAA Documentación §2 y límites de verificación propia conforme a Gobernanza §2.8.
'''
    with DOC.open('x', encoding='utf-8') as f:
        f.write(doc)
    index = {'id': IDENT, 'author': 'Codex', 'utc': now(), 'status': STATUS, 'path_base': 'workspace_root',
        'run': rel(RUN), 'prepared_attempt': result['attempt'], 'documentation': rel(DOC), 'documentation_sha256': sha(DOC),
        'forum_prior': plan['forum_prior'], 'forum_result': FID, 'reference': 'W2-B00', 'all_alternatives_preserved': True,
        'contract_checks': 55, 'contract_failures': 0, 'synthetic_scope_connections': 15,
        'real_scope_requests': 15, 'real_missing_capital_blocks_before_values': 15,
        'capital_Decimal_reference_rows': 32, 'capital_reference_max_abs_error': validation['capital_reference_max_abs_error'],
        'input_poison_invariance_cases': 2, 'whole_learned_object_invariance_claimed': False,
        'real_row_values_decoded': 0, 'model_fits_including_synthetic': 0, 'C0_calls_including_synthetic': 0,
        'new_inferences': 0, 'new_scores': 0, 'real_capital_parameters': 0, 'real_capital_application': False,
        'real_parameter_producer_available': False, 'real_parameter_receipt_positive_flow_tested': False,
        'G4_real_full_flow_validated': False, 'G4_real_gate_closed': False, 'G1_G2_resolved': False,
        'model_input_ready': False, 'B00_or_selection_changed': False, '2024_test_closed': True,
        'old_diagnostics_or_suites_repeated': False, 'submission': False, 'night_window_reopened': False,
        'professional_independent_validation': False,
        'remaining': ['Exact-scope capital parameter producer/population evidence and real parameters absent',
            'Positive real parameter receipt flow not tested', 'Real nested learned objects/full-flow validation absent',
            'G1 plausible,unestablished; G2 retained support failed,internal unknown'],
        'next_step': 'Implement and validate the scope parameter producer on synthetic data without learning from contest rows; real C0/models remain outside current scope.'}
    for key, p in [('plan', PLAN), ('capital_contract', CONTRACT), ('connection_registry', RUN/'connection_registry.json'),
        ('validation', out/'validation.json'), ('matrix', RUN/'gate_matrix_updated_G4.json'), ('decisions', RUN/'decision_journal.json')]:
        index[key] = {'path': rel(p), 'sha256': sha(p)}
    body = RUN/'forum_064_result.md'
    body.write_text(f'''Codex, resultado de la preinscripción063 y continuación de062. Informe: {rel(DOC)}. Índice: {rel(INDEX)}. Contrato de capital: {rel(CONTRACT)}. Conexión: {rel(RUN/'connection_registry.json')}.

La frontera propia de G4 conecta lector por folds, aplicación aritmética de capital congelado y siete predictores con T0/notificaciones heredados. No llama al aprendiz sintético ni añade su marcador a filas reales. Exige origen, exclusiones, firmas del ajuste/pertenencias y archivos exactos; referencias finitas/positivas, intervalo ordenado y umbral1e7. Se especifica la futura regla de estimación, sin estimarla o incorporar fallback.

Pasaron55controles nuevos, cero fallos:15conexiones sintéticas desde Parquet por el lector de producción;32filas de referencia Decimal/math.log con error máximo0 y tolerancia1e-12; contratos adversos antes de abrir valores;2invariancias de tablas/firma ante alteración protegida; cambio permitido que invalida capital anterior; contratos desde disco con entrada idéntica. La invariancia se limita a entradas, no objetos aprendidos. La firma archivística puede cambiar aunque la de aprendizaje permanezca igual.

Quedaron15solicitudes reales ligadas al manifiesto2023 y15plantillas con límites/procedencia vacíos. Todas se detienen antes de leer valores. Parámetros sintéticos no desbloquean solicitudes reales. Ninguna fila real decodificada ni capital real aplicado. La conexión válida requiere artefactos reales que aún no existen; el paquete resultante sigue con fit_allowed=false,C0_present=false,model_input_ready=false.

Fit/predict de modelos y preprocesadores, C0 fit/apply, cargas de estimadores y red bloqueados: cero llamadas prohibidas. No se ajustó nada, incluso sintético, ni se recalculó C0. Cero inferencias/scores. Las287lecturas registradas son solo fixtures generados. No se repitieron suites o diagnósticos anteriores.

G4C-01 a G4C-06: contrato y conexión verificados sintéticamente, G4 integral real abierto. Faltan productor y evidencia de población de capital por ámbito, parámetros reales, flujo positivo de su recibo y objetos C0/preprocesado/GLM/calibradores internos con validación integral. Un recibo ligado no prueba por sí solo corrección de la estimación externa. G1/G2 no cambian; no se reclama nueva cohorte o soporte.

B00/alternativas,T0/exposición/C0/folds/catálogo/contadores conservados.2024/test/ledger/actas/SEL01 cerrados en este trabajo. Sin promoción, envío, publicación, remoto, contactos, otros chats, delegación o automatizaciones; ventana nocturna cerrada. Autor Codex, verificación propia exploratoria en Windows, sin aprobación humana o validación profesional independiente.
''', encoding='utf-8')
    post = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', FID, '--asunto', 'G4: contrato y conexión sintética,55controles sin ajuste; capital real pendiente',
        '--cuerpo', str(body)], capture_output=True, text=True)
    assert post.returncode == 0, post.stderr
    dump(RUN/'forum_result_receipt.json', json.loads(post.stdout))
    dump(INDEX, index)
    preserved_paths = [REPO/'registro/semana2_contadores_propios_actual.json', REPO/'registro/semana2_continuidad_nocturna.json',
        REPO/'privado/semana2/desarrollo2023/g4_flujo_sintetico_20261024_v1/paquete_G4_sintetico_revision_local.zip',
        ROOT/plan['prepared_input_manifest']['path']]
    preserved = {rel(p): sha(p) for p in preserved_paths}
    changes = []
    def change(path, fn, allowed=None):
        before = path.read_bytes()
        raw = before.decode('utf-8-sig')
        updated = fn(raw)
        if allowed is not None:
            old, new = json.loads(raw), json.loads(updated)
            assert {k: v for k, v in old.items() if k not in allowed} == {k: v for k, v in new.items() if k not in allowed}
        after = updated.encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):
            after = b'\xef\xbb\xbf'+after
        for phase, payload in [('before', before), ('after', after)]:
            p = RUN/'registration_cuts'/phase/path.relative_to(ROOT)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open('xb') as f:
                f.write(payload)
        temporary = path.with_name(path.name+'.G4capital.tmp')
        with temporary.open('xb') as f:
            f.write(after)
            f.flush()
            os.fsync(f.fileno())
        assert path.read_bytes() == before, 'Concurrent edit: '+rel(path)
        os.replace(temporary, path)
        changes.append({'path': rel(path), 'before_sha256': hashlib.sha256(before).hexdigest(), 'after_sha256': sha(path)})
    def update(raw, values):
        for k, v in values.items():
            raw = top(raw, k, v)
        return raw
    def priority_update(raw):
        d = json.loads(raw)
        g = d['current_gate_statuses']
        g['G4'] = STATUS
        blockers = [('G4: input connection and capital contract synthetic verified; real scope parameters and nested objects pending'
                     if str(x).startswith('G4:') else x) for x in d.get('current_blockers', [])]
        return update(raw, {'current_gate_statuses': g, 'current_blockers': blockers,
            'G4_capital_connection_index': rel(INDEX), 'G4_capital_connection_utc': now(),
            'previous_G4_connection_matrix': d['matrix'], 'matrix': index['matrix']})
    change(PRIORITY, priority_update, {'current_gate_statuses', 'current_blockers', 'G4_capital_connection_index',
        'G4_capital_connection_utc', 'previous_G4_connection_matrix', 'matrix'})
    def source_update(raw):
        d = json.loads(raw)
        g = d['current_B20_gate_statuses']
        g['G4'] = STATUS
        return update(raw, {'current_B20_gate_statuses': g, 'G4_capital_connection_index': rel(INDEX),
            'G4_capital_contract_and_input_connection_synthetic_verified': True, 'G4_real_full_flow_validated': False})
    change(SOURCES, source_update, {'current_B20_gate_statuses', 'G4_capital_connection_index',
        'G4_capital_contract_and_input_connection_synthetic_verified', 'G4_real_full_flow_validated'})
    link = {'index': rel(INDEX), 'utc': now(), 'status': STATUS, 'new_fits': 0, 'new_C0_calls': 0,
        'real_parameters_pending': True, 'real_full_flow_validated': False}
    change(INGRESS_INDEX, lambda raw: top(raw, 'subsequent_capital_connection', link), {'subsequent_capital_connection'})
    change(DEVELOPMENT, lambda raw: top(raw, 'G4_capital_connection', link), {'G4_capital_connection'})
    change(ROOT/'Preparación/ESTADO_PROYECTO.json', lambda raw: top(raw, STATEKEY, index), {STATEKEY})
    section = f'''\n\n## G4: contrato de capital y conexión sin aprendizaje

Codex, UTC {now()}, preinscripción063 y resultado064; decisiones G4C-01 a G4C-06. Informe {rel(DOC)}, índice {rel(INDEX)}, registro y recibos {rel(RUN)}. Frontera propia conecta lector estricto por folds, capital congelado del mismo ámbito y siete predictores/T0/notificaciones heredados. Contrato {rel(CONTRACT)}:origen/exclusiones/firmas/fuentes,referencias finitas positivas,umbral1e7 y recibo externo. Se define regla futura de estimación,sin ejecutarla o usar fallback.

Pasaron55controles nuevos:15conexiones sintéticas desde Parquet,32filas con Decimal/math.log y error máximo0,adversos antes de abrir valores,2invariancias de entradas ante alteración protegida,control de cambio permitido y contratos desde disco. No es invariancia de objetos aprendidos. Quince solicitudes reales y15plantillas pendientes; todas bloquean antes de valores,y constantes sintéticas no las desbloquean. Cero filas reales decodificadas o capital real aplicado;287lecturas solo de fixtures.

Fit/predict de modelos/preprocesadores,C0 fit/apply,cargas y red bloqueados,cero llamadas prohibidas. Cero ajustes incluso sintéticos,C0,inferencias o scores. G4 avanza en contrato/conexión sintética,sigue abierto:productor/evidencia de población/parámetros reales por ámbito,flujo positivo de su recibo y objetos internos con validación integral pendientes. Recibo ligado no prueba estimación correcta. G1/G2 sin cambio; no nueva cohorte o soporte. No repetir suite o diagnósticos sobre fuentes iguales.

B00/alternativas,T0/exposición/C0/folds/catálogo/contadores conservados;2024/test/ledger/actas/SEL01 cerrados en este trabajo. No marcador sintético en filas reales,promoción,envío,publicación,remoto,contactos,otros chats,delegación o automatizaciones. Ventana nocturna cerrada. Verificación propia exploratoria de Codex en Windows;no revisión profesional independiente ni aprobación humana.\n'''
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        change(ROOT/'Preparación'/name, lambda raw: raw+section)
    routes = {'week_2_G4_capital_scope_contract': rel(CONTRACT), 'week_2_G4_capital_connection_index': rel(INDEX),
        'week_2_G4_capital_connection_report': rel(DOC), 'week_2_G4_capital_connection_registry': rel(RUN/'connection_registry.json')}
    change(ROOT/'RUTAS_PROYECTO.json', lambda raw: update(raw, routes), set(routes))
    integrity = {'id': IDENT, 'utc': now(), 'frozen_code_matches': all(sha(ROOT/p['path']) == p['sha256'] for p in plan['frozen_code']),
        'counters_night_index_old_packet_and_prepared_input_manifest_unchanged': all(sha(ROOT/p) == value for p, value in preserved.items()),
        'preserved_hashes': preserved, 'unrelated_shared_top_level_keys_preserved': True,
        'private_registry_ignored_by_git': True, 'new_data_decodes_during_registration': 0}
    assert integrity['frozen_code_matches'] and integrity['counters_night_index_old_packet_and_prepared_input_manifest_unchanged']
    dump(RUN/'closure_integrity_receipt.json', integrity)
    dump(RUN/'registration.json', {'changes': changes, 'model_catalog_mutations': 0, 'model_counter_mutations': 0,
        'night_index_mutations': 0, 'prior_packet_mutations': 0})
    files = [p for p in RUN.rglob('*') if p.is_file()] + [INDEX, DOC, Path(__file__).resolve(),
        REPO/'herramientas/registrar_plan_conexion_g4_2023.py', REPO/'herramientas/registrar_resultado_entradas_g4_2023.py']
    dump(RUN/'manifest.json', {'id': IDENT, 'author': 'Codex', 'utc': now(),
        'files': [{'path': rel(p), 'sha256': sha(p)} for p in files]})
    print(json.dumps({'id': IDENT, 'forum_result': FID, 'document': rel(DOC), 'contract_checks': 55,
        'real_requests': 15, 'model_fits': 0, 'C0_calls': 0, 'G4_real_closed': False, 'integrity': True}, ensure_ascii=True))


if __name__ == '__main__':
    main()
