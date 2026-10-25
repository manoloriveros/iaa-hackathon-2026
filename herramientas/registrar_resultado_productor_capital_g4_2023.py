"""Registra productor y evidencia sintética existentes, sin repetir cálculo."""
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
RUN = REPO/'privado/semana2/productor_capital_g4_2023/productor_20261024_v1'
PLAN = REPO/'registro/semana2_g4_productor_capital_plan_v1.json'
CONTRACT = REPO/'registro/semana2_g4_capital_contrato_v2.json'
INDEX = REPO/'registro/semana2_g4_productor_capital_actual.json'
DOC = REPO/'docs/semana2/G4_PRODUCTOR_CAPITAL_Y_REPLAY_2023.md'
PRIORITY = REPO/'registro/semana2_b20_prioridades_actual.json'
SOURCES = REPO/'registro/semana2_b20_fuentes2023_actual.json'
PREVIOUS = REPO/'registro/semana2_g4_conexion_actual.json'
DEVELOPMENT = REPO/'registro/semana2_desarrollo2023_actual.json'
IDENT = 'S2-G4-PRODUCTOR-CAPITAL2023-FINAL-v1-20261024'
FID = 'COD-S2-20261024-066'
STATEKEY = 'week_2_G4_capital_producer_synthetic2023_v1_20261024'
STATUS = 'scope_capital_producer_receipt_integration_synthetic_verified_real_execution_and_nested_objects_pending'
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
    plan, result = read(PLAN), read(RUN/'validated_current.json')
    out = ROOT/result['out']
    validation = read(out/'validation.json')
    assert result['success'] and validation['success'] and len(validation['checks']) == result['contract_checks'] == 63
    assert all(x['pass'] for x in validation['checks']) and not validation['forbidden_calls']
    assert validation['normal_bound_Decimal_max_abs_error'] <= 1e-12
    assert validation['capital_application_math_log_max_abs_error'] <= 1e-12
    assert validation['coherent_bad_receipt_rejected_by_numeric_population_replay']
    assert result['real_row_values_decoded'] == result['real_parameter_artifacts'] == result['model_fits_including_synthetic'] == result['C0_calls_including_synthetic'] == 0
    assert all(sha(ROOT/x['path']) == x['sha256'] for x in plan['frozen_code'])
    assert sha(ROOT/plan['prepared_input_manifest']['path']) == plan['prepared_input_manifest']['sha256']
    parameter_files = sorted((out/'generated_fixture').rglob('capital_parameters.json'))
    assert len(parameter_files) == 31
    requests = sorted((out/'real_requests').glob('*.json'))
    requirements = sorted((out/'real_capital_requirements').glob('*.json'))
    assert len(requests) == len(requirements) == 15
    assert all(read(p)['ppm_min'] is None and read(p)['ppm_max'] is None for p in requirements)
    dump(RUN/'producer_and_connection_registry.json', {'id': IDENT, 'author': 'Codex', 'utc': now(),
        'contract': {'path': rel(CONTRACT), 'sha256': sha(CONTRACT)},
        'prepared_input_manifest': plan['prepared_input_manifest'],
        'producer_entrypoint': 'semana2.productor_capital_g4_2023.produce_parameters',
        'connection_entrypoint': 'semana2.productor_capital_g4_2023.connect_scope',
        'status': 'software_synthetic_verified_real_parameters_not_produced',
        'real_requests': [{'path': rel(p), 'sha256': sha(p), 'excluded_folds': read(p)['excluded_folds']} for p in requests],
        'real_capital_requirements': [{'path': rel(p), 'sha256': sha(p)} for p in requirements],
        'synthetic_parameter_artifacts': [{'path': rel(p), 'sha256': sha(p)} for p in parameter_files],
        'real_parameter_artifacts': 0, 'real_values_decoded': 0,
        'model_fits': 0, 'C0_calls': 0, 'model_input_ready': False, 'fit_allowed': False})
    dump(RUN/'environment.json', {'python': sys.version, 'platform': sys.platform,
        'packages': {p: md.version(p) for p in ['numpy', 'pandas', 'pyarrow', 'scikit-learn', 'joblib']},
        'hosted_Kaggle_Linux_or_independent_reproduction_verified': False})
    ignored = subprocess.run(['git', 'check-ignore', '--quiet', str(out/'generated_fixture/baseline_artifacts/exclude_0/capital_parameters.json')], cwd=REPO)
    assert ignored.returncode == 0
    current = read(PRIORITY)
    matrix = read(ROOT/current['matrix']['path'])
    for card in matrix['cards']:
        if card['gate'] == 'G4':
            card.update(status=STATUS,
                what_changed='Productor por ámbito y recibo con población implementados; replay numérico y conexión G4v2 verificados en15ámbitos sintéticos,63controles sin modelos/C0.',
                required_evidence='Ejecución/artefactos de capital reales del ámbito exacto y su evidencia cuando esté autorizada; objetos C0/preprocesado/GLM/calibradores internos y prueba integral aún ausentes.',
                boundary='Software del productor y flujo positivo con recibos calculados verificados solo con datos generados; no validez predictiva real o invariancia de objetos aprendidos. G1/G2 sin cambios.')
    matrix.update(id=IDENT, author='Codex', utc=now(), source_previous_matrix=current['matrix'],
        verification_scope='New parameter producer/population replay on generated Parquet only; previous suites not repeated')
    dump(RUN/'gate_matrix_updated_G4.json', matrix)
    decisions = [
        ('G4P-01', 'Implementar productor/recibo/conexión v2 conservando v1 y la regla numérica CAPS2-01; solo metadatos y capitales permitidos al estimar referencias.'),
        ('G4P-02', 'Guardar población normal exacta,claves/contenido/fuentes,autor/UTC y código; reproducir población y límites contra capital permitido antes de aplicar el artefacto.'),
        ('G4P-03', 'Separar firma numérica del sello archivístico: rutas/UTC/autor y hash global protegido no alteran parámetros o entrada permitidos.'),
        ('G4P-04', 'Aceptar63controles nuevos,15integraciones y15invariancias de entradas,referencia Decimal/log,error0,control positivo de prima y rechazo numérico de omisión reseñalada coherentemente.'),
        ('G4P-05', 'Distinguir31artefactos calculados de capital sintéticos de modelos; no producir parámetros reales,abrir valores reales o cerrar G4/G1/G2.'),
        ('G4P-06', 'Conservar B00/alternativas,T0/exposición/C0/folds/catálogo/contadores;2024cerrado,cero ajustes de modelos incluso sintéticos,C0,inferencias o scores y sin promoción/envío.')]
    dump(RUN/'decision_journal.json', {'id': IDENT, 'author': 'Codex', 'utc': now(),
        'decisions': [{'id': k, 'decision': v} for k, v in decisions]})
    doc = f'''# G4: productor de capital por ámbito e integración con evidencia de población

Codex, {now()} (24 de octubre, hora de Bogotá). Preinscripción COD-S2-20261024-065; resultado {FID}. El productor de parámetros de capital está implementado y su integración con G4 v2 pasó 63 controles con datos sintéticos. No se ajustaron modelos, tampoco sintéticos, ni se llamó a C0 para ajustar o aplicar. B00 y las alternativas se conservan; 2024 permanece cerrado en este trabajo.

| Comprobación nueva | Resultado |
| --- | --- |
| Productor, recibo, población y conexión desde Parquet | 15 ámbitos sintéticos completos |
| Alteración de valores protegidos | 15 casos con parámetros numéricos y entradas permitidas invariantes |
| Referencias por prima por mil con Decimal | Error absoluto máximo {validation['normal_bound_Decimal_max_abs_error']}, criterio 1e-12 |
| Aplicación y logaritmo por otro método | Error absoluto máximo {validation['capital_application_math_log_max_abs_error']}, criterio 1e-12 |
| Recibo con hashes coherentes que omite una fila normal | Pasa el control estructural y falla al reproducir la población contra el capital permitido |
| Prima permitida alterada | El máximo aprendido cambia de 9 a 18 en el fixture; el artefacto anterior se rechaza |
| Artefactos válidos calculados de capital | 31 sintéticos; cero reales |
| Modelos, llamadas C0, inferencias y scores | Cero, con funciones bloqueadas |

El productor `semana2.productor_capital_g4_2023.produce_parameters` valida la solicitud v2, lee los metadatos de pertenencia y solo los archivos de capital de los folds permitidos. Proyecta capital original y prima, sin etiquetas, siniestros, exposición o predictores. Comprueba claves únicas y pertenencia exacta. La población de referencias contiene capital positivo finito hasta diez millones y debe ser no vacía; toda prima por mil de esa población debe ser positiva y finita. Los límites son su mínimo y máximo, con umbral fijo. Ante datos inválidos se detiene, sin fallback, imputación o cambios de bandas.

El productor escribe `normal_population.json`, `producer_receipt.json` y `capital_parameters.json`. La población conserva filas de referencia y firmas de claves/contenido; el recibo incluye fuentes permitidas, exclusiones, firmas de ajuste, autor/fecha con zona, hash del código y vínculo al contenido numérico del artefacto. Los archivos por fila quedan en privado. Seleccionar capitales normales para las referencias no elimina periodos o siniestros de las entradas al modelo.

La conexión `semana2.productor_capital_g4_2023.connect_scope` comprueba el artefacto, su origen y el recibo antes de abrir valores. Luego reproduce la población normal y su aritmética contra el capital permitido que ya cargó el lector del ámbito; cualquier diferencia provoca rechazo, nunca una actualización silenciosa del parámetro. Después aplica los límites congelados y entrega los siete predictores con T0 y notificaciones heredados. La prima no entra a los predictores. El paquete permanece como `G4_BASE_INPUTS_ONLY`, con `C0_present=false`, `fit_allowed=false` y `model_input_ready=false`.

La versión v2 existe porque v1 solo admitía constantes sintéticas declaradas. Se conservan el contrato, código, ensayos y recibos v1; no se presentan como certificación de v2. La regla numérica CAPS2-01 permanece igual. Los parámetros calculados en fixtures llevan origen y recibo sintéticos propios, que no desbloquean solicitudes reales. No se añade el marcador del aprendiz sintético a filas reales.

En los quince controles de alteración protegida cambian las fuentes protegidas, la solicitud archivística y los sellos de publicación. El contenido numérico del parámetro, la población normal permitida, sus firmas y todas las tablas entregadas al aprendizaje permanecen iguales. La firma de aprendizaje v2 excluye ruta del recibo, autor, UTC y hash global de la solicitud, conservando la población y los archivos permitidos. Esto comprueba invariancia de entradas y parámetros de capital, no de objetos aprendidos que no se crearon en este encargo.

Los adversos nuevos incluyen población normal vacía, prima normal nula/negativa/no finita o con desbordamiento, claves duplicadas, artefacto exterior reutilizado como interior, hashes alterados y población del recibo incompleta. El caso de omisión tiene hashes y conteos internos recalculados: demuestra que la comprobación ejecuta el flujo numérico contra los capitales permitidos y no se limita a seleccionar metadatos. También se guardó y releyó el artefacto producido por disco con resultado idéntico. No se repitieron suites o diagnósticos históricos.

El ensayo produjo 15 artefactos base, 15 bajo alteración protegida y uno de control positivo. Se contabilizan como referencias de capital calculadas sobre fixtures, no como modelos ni candidatos. Las {len(validation['decoder_events'])} lecturas registradas corresponden únicamente a Parquet generados; fit/predict de modelos y preprocesadores, C0 fit/apply, cargas de estimadores y red estuvieron bloqueados sin llamadas prohibidas. Verificación propia en Windows, no Kaggle/Linux ni revisión profesional independiente.

Quedaron quince solicitudes reales v2 y quince requisitos pendientes en el registro `{rel(RUN/'producer_and_connection_registry.json')}`, ligados al manifiesto de ingreso de 2023 ya preparado. Se construyeron solo desde metadatos JSON. No se llamó al productor con filas del concurso, no se estimaron parámetros reales ni se aplicó capital a esas filas. Todas las conexiones reales sin parámetros continúan bloqueadas antes de leer valores. El estado anterior “productor no implementado” se resuelve para software e integración sintética; sigue pendiente su ejecución y evidencia sobre datos reales.

G4 integral real sigue abierto: faltan parámetros de capital reales del ámbito exacto, cuando corresponda producirlos, y objetos C0/preprocesado/GLM/calibradores interiores con su comprobación integral. G1/G2 no cambian; este ensayo no aporta otra cohorte, prueba del mecanismo o soporte adicional. No se declara listo el entrenamiento o el envío. La prioridad siguiente es revisar el alcance de una eventual producción real y sus dependencias temporales; no ejecutar ajustes o C0 bajo esta continuación.

Decisiones G4P-01 a G4P-06. Informe y evidencia enlazados desde `{rel(INDEX)}`. Punto reutilizable: `{rel(RUN/'validated_current.json')}`; no repetir el ensayo sobre fuentes iguales. B00/alternativas, T0/exposición/C0/folds/catálogo/contadores de modelos se conservan. 2024/test/ledger/actas/SEL01 cerrados en este trabajo; no se usa la exposición previa a información ajena de 2024. Sin promoción, envío, publicación, remoto, contactos, otros chats, delegación o automatizaciones. Ventana nocturna cerrada. Autor Codex; sin aprobación humana o validación profesional independiente. Procedencia y recorrido documentados conforme a IAA Documentación §2 y límites de verificación propia conforme a Gobernanza §2.8.
'''
    with DOC.open('x', encoding='utf-8') as f:
        f.write(doc)
    index = {'id': IDENT, 'author': 'Codex', 'utc': now(), 'status': STATUS, 'path_base': 'workspace_root',
        'run': rel(RUN), 'prepared_attempt': result['attempt'], 'documentation': rel(DOC), 'documentation_sha256': sha(DOC),
        'forum_prior': plan['forum_prior'], 'forum_result': FID, 'reference': 'W2-B00', 'all_alternatives_preserved': True,
        'capital_parameter_producer_implemented': True, 'producer_receipt_connection_synthetic_verified': True,
        'contract_checks': 63, 'contract_failures': 0, 'synthetic_parameter_artifacts': 31,
        'synthetic_scope_integrations': 15, 'protected_input_invariance_cases': 15,
        'coherently_resealed_population_omission_rejected_numerically': True,
        'normal_bound_Decimal_max_abs_error': validation['normal_bound_Decimal_max_abs_error'],
        'capital_application_math_log_max_abs_error': validation['capital_application_math_log_max_abs_error'],
        'whole_model_object_invariance_claimed': False, 'real_parameter_artifacts': 0, 'real_row_values_decoded': 0,
        'real_positive_parameter_execution_tested': False, 'model_fits_including_synthetic': 0,
        'C0_calls_including_synthetic': 0, 'new_inferences': 0, 'new_scores': 0,
        'G4_real_full_flow_validated': False, 'G4_real_gate_closed': False, 'G1_G2_resolved': False,
        'model_input_ready': False, 'B00_or_selection_changed': False, '2024_test_closed': True,
        'old_suites_or_diagnostics_repeated': False, 'submission': False, 'night_window_reopened': False,
        'professional_independent_validation': False,
        'remaining': ['Exact-scope real capital parameter execution/artifacts not produced in this work',
            'Real nested C0/preprocessing/GLM/calibration objects and full-flow validation absent',
            'G1 plausible,unestablished; G2 retained support failed,internal unknown'],
        'next_step': 'Review scope and temporal/provenance dependencies before eventual real capital production; no model or C0 execution under this continuation.'}
    for key, p in [('plan', PLAN), ('capital_contract', CONTRACT), ('registry', RUN/'producer_and_connection_registry.json'),
        ('validation', out/'validation.json'), ('matrix', RUN/'gate_matrix_updated_G4.json'), ('decisions', RUN/'decision_journal.json')]:
        index[key] = {'path': rel(p), 'sha256': sha(p)}
    body = RUN/'forum_066_result.md'
    body.write_text(f'''Codex, resultado de la preinscripción065 y continuación de064. Implementados productor CAPS2-01 por ámbito y conexión G4v2 con replay de población. Informe: {rel(DOC)}. Índice: {rel(INDEX)}. Contrato: {rel(CONTRACT)}. Registro: {rel(RUN/'producer_and_connection_registry.json')}.

Pasaron 63 controles nuevos. Quince ámbitos sintéticos por el recorrido lector-productor-población-recibo-conexión; quince alteraciones protegidas conservan parámetros numéricos, población permitida, tablas y firmas de aprendizaje. Referencias min/max con Decimal y log capital por otro método: error máximo 0, criterio absoluto 1e-12. Control positivo: prima permitida cambia máximo de 9 a 18 e invalida artefacto anterior. Recibo con hashes coherentes y una fila normal omitida pasa comprobación estructural y falla en el replay contra capital permitido. Artefacto/recibo/población guardados y releídos por disco con entrada idéntica.

El productor lee solo pertenencias y capital/prima permitidos, no etiquetas, siniestros, exposición o predictores. Normalidad y ratios finitos/positivos estrictos; población vacía o inválida falla sin fallback. La población de referencias no elimina periodos del modelo. Se archivan claves/contenido/fuentes, exclusiones, autor/UTC y código. V2 conserva v1 y la regla numérica; distingue parámetros estimados sintéticos de reales. La firma numérica excluye rutas/UTC/autor y hash global protegido; sellos archivísticos sí pueden diferir. No se afirma invariancia de modelos aprendidos.

Se produjeron 31 artefactos válidos de parámetros sintéticos (15base,15alterados,1control), no modelos. Fit/predict de modelos/preprocesadores, C0 fit/apply, cargas y red bloqueados: cero llamadas prohibidas. Cero ajustes de modelos incluso sintéticos, C0, inferencias o scores. Las {len(validation['decoder_events'])} lecturas corresponden solo a fixtures. No se repitieron diagnósticos o suites históricas.

Quince solicitudes reales v2 y requisitos pendientes se prepararon desde el manifiesto, sin leer valores. No se llamó al productor con filas del concurso ni se produjeron/aplicaron parámetros reales. Las conexiones sin parámetros siguen bloqueadas. G4 avanza de productor ausente a software y flujo positivo con recibos calculados verificados sintéticamente. Siguen pendientes la ejecución/evidencia real del capital por ámbito y los objetos C0/preprocesado/GLM/calibradores internos con validación integral. G1/G2 no cambian; no hay otra cohorte o soporte nuevo, ni entrenamiento/envío listo.

G4P-01 a G4P-06, autor Codex. B00/alternativas,T0/exposición/C0/folds/catálogo/contadores conservados. 2024/test/ledger/actas/SEL01 cerrados en este trabajo. Sin promoción,envío,publicación,remoto,contactos,otros chats,delegación o automatizaciones;ventana nocturna cerrada. Verificación propia exploratoria en Windows,sin aprobación humana o revisión profesional independiente.
''', encoding='utf-8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', FID, '--asunto', 'G4: productor y replay numérico verificados,63controles sintéticos sin modelos/C0',
        '--cuerpo', str(body)], capture_output=True, text=True)
    assert posted.returncode == 0, posted.stderr
    dump(RUN/'forum_result_receipt.json', json.loads(posted.stdout))
    dump(INDEX, index)
    preserved_paths = [REPO/'registro/semana2_contadores_propios_actual.json', REPO/'registro/semana2_continuidad_nocturna.json',
        REPO/'privado/semana2/desarrollo2023/g4_flujo_sintetico_20261024_v1/paquete_G4_sintetico_revision_local.zip',
        ROOT/plan['prepared_input_manifest']['path']]
    preserved = {rel(p): sha(p) for p in preserved_paths}
    changes = []
    def change(path, transform, allowed=None):
        before = path.read_bytes()
        raw = before.decode('utf-8-sig')
        updated = transform(raw)
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
        tmp = path.with_name(path.name+'.G4producer.tmp')
        with tmp.open('xb') as f:
            f.write(after)
            f.flush()
            os.fsync(f.fileno())
        assert path.read_bytes() == before, 'Concurrent edit: '+rel(path)
        os.replace(tmp, path)
        changes.append({'path': rel(path), 'before_sha256': hashlib.sha256(before).hexdigest(), 'after_sha256': sha(path)})
    def update(raw, values):
        for key, value in values.items():
            raw = top(raw, key, value)
        return raw
    def priority_update(raw):
        d = json.loads(raw)
        gates = d['current_gate_statuses']
        gates['G4'] = STATUS
        blockers = [('G4: capital producer/receipt integration synthetic verified; real execution and nested objects pending'
                     if str(x).startswith('G4:') else x) for x in d.get('current_blockers', [])]
        return update(raw, {'current_gate_statuses': gates, 'current_blockers': blockers,
            'G4_capital_producer_index': rel(INDEX), 'G4_capital_producer_utc': now(),
            'previous_G4_producer_matrix': d['matrix'], 'matrix': index['matrix']})
    change(PRIORITY, priority_update, {'current_gate_statuses', 'current_blockers', 'G4_capital_producer_index',
        'G4_capital_producer_utc', 'previous_G4_producer_matrix', 'matrix'})
    def sources_update(raw):
        d = json.loads(raw)
        gates = d['current_B20_gate_statuses']
        gates['G4'] = STATUS
        return update(raw, {'current_B20_gate_statuses': gates, 'G4_capital_producer_index': rel(INDEX),
            'G4_capital_producer_integration_synthetic_verified': True, 'G4_real_full_flow_validated': False})
    change(SOURCES, sources_update, {'current_B20_gate_statuses', 'G4_capital_producer_index',
        'G4_capital_producer_integration_synthetic_verified', 'G4_real_full_flow_validated'})
    link = {'index': rel(INDEX), 'utc': now(), 'status': STATUS, 'real_parameters_pending': True,
        'new_model_fits': 0, 'new_C0_calls': 0, 'real_full_flow_validated': False}
    change(PREVIOUS, lambda raw: top(raw, 'subsequent_capital_producer', link), {'subsequent_capital_producer'})
    change(DEVELOPMENT, lambda raw: top(raw, 'G4_capital_producer', link), {'G4_capital_producer'})
    change(ROOT/'Preparación/ESTADO_PROYECTO.json', lambda raw: top(raw, STATEKEY, index), {STATEKEY})
    section = f'''\n\n## G4: productor de capital por ámbito e integración sintética

Codex, UTC {now()}, preinscripción065 y resultado066; decisiones G4P-01 a G4P-06. Informe {rel(DOC)}, índice {rel(INDEX)}, registro/recibos {rel(RUN)}. Productor y conexión v2 implementados, v1 y regla numérica CAPS2-01 conservados. Lectura de metadatos/capital-prima permitidos, sin objetivos/siniestros/exposición/predictores. Población normal positiva/finita y ratios estrictos, sin fallback; población/firmas/fuentes/autor/UTC/código archivados y replay contra capital permitido antes de aplicar.

63 controles nuevos pasados:15integraciones sintéticas y15alteraciones protegidas,referencias Decimal/log con error máximo0,control positivo de prima y rechazo de recibo autoconsistente que omite fila normal al replay numérico. Artefacto/recibo/población desde disco con entrada idéntica. Firma numérica separada de rutas/UTC/autor y hash global archivístico. Se produjeron31parámetros sintéticos válidos, no modelos; no es invariancia de objetos aprendidos. Funciones fit/predict,C0 fit/apply,cargas y red bloqueadas,cero llamadas prohibidas. {len(validation['decoder_events'])}lecturas solo de fixtures,ninguna fila real; no repetir suites/diagnósticos terminados.

Quince solicitudes reales v2 y plantillas pendientes desde manifiesto JSON; no producir/aplicar capital real. Productor ausente resuelto solo en software/integración sintética. Siguen ejecución/evidencia de parámetros reales por ámbito y objetos internos C0/preprocesado/GLM/calibradores con validación integral pendientes. G4 integral real abierto,G1/G2 sin cambios. No entrenamiento o envío listo.

B00/alternativas,T0/exposición/C0/folds/catálogo/contadores conservados;2024/test/ledger/actas/SEL01 cerrados en este trabajo. Cero ajustes de modelos incluso sintéticos,C0,inferencias/scores. Sin marcador sintético en filas reales,promoción,envío,publicación,remoto,contactos,otros chats,delegación o automatizaciones. Ventana nocturna cerrada. Autor Codex,verificación propia exploratoria en Windows;sin aprobación humana o revisión profesional independiente.\n'''
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        change(ROOT/'Preparación'/name, lambda raw: raw+section)
    routes = {'week_2_G4_capital_producer_index': rel(INDEX), 'week_2_G4_capital_producer_report': rel(DOC),
        'week_2_G4_capital_scope_contract_v2': rel(CONTRACT), 'week_2_G4_capital_producer_registry': rel(RUN/'producer_and_connection_registry.json')}
    change(ROOT/'RUTAS_PROYECTO.json', lambda raw: update(raw, routes), set(routes))
    integrity = {'id': IDENT, 'utc': now(), 'frozen_code_and_v1_dependencies_match': all(sha(ROOT/x['path']) == x['sha256'] for x in plan['frozen_code']),
        'counters_night_old_packet_and_prepared_manifest_unchanged': all(sha(ROOT/p) == value for p, value in preserved.items()),
        'preserved_hashes': preserved, 'unrelated_top_level_shared_keys_preserved': True,
        'private_artifact_ignored_by_git': True, 'new_value_decodes_during_registration': 0}
    assert integrity['frozen_code_and_v1_dependencies_match'] and integrity['counters_night_old_packet_and_prepared_manifest_unchanged']
    dump(RUN/'closure_integrity_receipt.json', integrity)
    dump(RUN/'registration.json', {'changes': changes, 'model_catalog_mutations': 0, 'model_counter_mutations': 0,
        'night_index_mutations': 0, 'old_packet_mutations': 0, 'real_parameter_artifacts': 0})
    files = [p for p in RUN.rglob('*') if p.is_file()]+[INDEX, DOC, Path(__file__).resolve(),
        REPO/'herramientas/registrar_plan_productor_capital_g4_2023.py', REPO/'herramientas/registrar_resultado_entradas_g4_2023.py']
    dump(RUN/'manifest.json', {'id': IDENT, 'author': 'Codex', 'utc': now(),
        'files': [{'path': rel(p), 'sha256': sha(p)} for p in files]})
    print(json.dumps({'id': IDENT, 'forum_result': FID, 'document': rel(DOC), 'contract_checks': 63,
        'synthetic_parameter_artifacts': 31, 'real_parameter_artifacts': 0, 'model_fits': 0, 'C0_calls': 0,
        'G4_real_closed': False, 'integrity': True}, ensure_ascii=True))


if __name__ == '__main__':
    main()
