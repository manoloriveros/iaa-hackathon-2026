"""Registra el ingreso G4 ya preparado; solo lee recibos, hashes y footers."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.metadata as md
import json
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(REPO / 'src'))
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
from semana2 import entradas_g4_2023 as core

RUN = REPO / 'privado/semana2/entradas_g4_2023/ingreso_20261024_v1'
PLAN = REPO / 'registro/semana2_g4_entradas2023_plan_v1.json'
DOC = REPO / 'docs/archivo/semana2/G4_ADAPTADOR_Y_ENTRADAS_ESTRICTAS_2023.md'
INDEX = REPO / 'registro/semana2_g4_entradas2023_actual.json'
PRIORITY = REPO / 'registro/semana2_b20_prioridades_actual.json'
SOURCE = REPO / 'registro/semana2_b20_fuentes2023_actual.json'
DEVELOPMENT = REPO / 'registro/semana2_desarrollo2023_actual.json'
FID = 'COD-S2-20261024-062'
IDENT = 'S2-G4-ENTRADAS2023-FINAL-v1-20261024'
STATEKEY = 'week_2_G4_strict2023_input_ingress_v1_20261024'
G4STATUS = 'synthetic_full_flow_and_strict2023_ingress_verified_scope_capital_and_nested_objects_pending'

now = lambda: datetime.now(timezone.utc).isoformat()
rel = lambda p: p.relative_to(ROOT).as_posix()
sha = core.sha
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def top(raw, key, value):
    encoded = json.dumps(value, ensure_ascii=False, indent=2).replace('\n', '\n  ')
    if key not in json.loads(raw):
        return raw[:raw.rfind('}')].rstrip() + ',\n  ' + json.dumps(key) + ': ' + encoded + '\n}\n'
    match = re.search(r'(?m)^  ' + re.escape(json.dumps(key)) + r':\s*', raw)
    assert match, key
    _, end = json.JSONDecoder().raw_decode(raw[match.end():])
    return raw[:match.end()] + encoded + raw[match.end() + end:]


def main():
    assert not INDEX.exists() and not DOC.exists(), 'Registration already started; reconcile before retry'
    plan = read(PLAN)
    result = read(RUN / 'prepared_current.json')
    out = ROOT / result['out']
    validation = read(out / 'validation.json')
    manifest = read(out / 'input_manifest.json')
    events = read(out / 'reader_events.json')
    assert result['success'] and validation['success']
    assert len(validation['checks']) == 12 and all(c['pass'] for c in validation['checks'])
    assert not events['forbidden_calls'] and not validation['protected_value_files_decoded']
    assert all(result[k] == 0 for k in ['new_models', 'new_C0_fits', 'new_predictions', 'new_scores', 'learned_capital_parameters'])
    assert not result['model_input_ready'] and not result['C0_present']
    for item in plan['frozen_code']:
        assert sha(ROOT / item['path']) == item['sha256'], item['path']
    for spec in plan['sources'].values():
        assert sha(core.safe_path(ROOT, spec['path'])) == spec['sha256']
    prior = read(RUN / 'forum_prior_receipt.json')
    assert prior['id'] == plan['forum_prior'] and prior['author'] == 'Codex'

    # This is an archive integrity check. It does not decode another data frame.
    output_proofs = []
    specs = [(None, 'metadata', manifest['metadata'])]
    specs += [(int(fold), name, spec) for fold, values in manifest['fold_files'].items() for name, spec in values.items()]
    for fold, name, spec in specs:
        p = core.safe_path(ROOT, spec['path'])
        assert sha(p) == spec['sha256']
        output_proofs.append({'table': name, 'fold': fold, 'path': spec['path'], 'sha256': spec['sha256'],
                              **core.footer_proof(p, spec['columns'], expected_fold=fold)})
    trace = {'id': IDENT, 'author': 'Codex', 'utc': now(), 'sources': plan['sources'],
             'frozen_code': plan['frozen_code'], 'output_footer_proofs': output_proofs,
             'input_manifest': {'path': rel(out / 'input_manifest.json'), 'sha256': sha(out / 'input_manifest.json')},
             'source_values_decoded_again_during_registration': False,
             'scope': 'Integrity of new input copies, not another actuarial diagnostic or model evaluation.'}
    dump(RUN / 'source_output_traceability.json', trace)
    dump(RUN / 'environment.json', {'python': sys.version, 'platform': sys.platform,
         'packages': {k: md.version(k) for k in ['numpy', 'pandas', 'pyarrow', 'scikit-learn', 'joblib']},
         'hosted_Kaggle_or_Linux_verified': False})
    ignored = subprocess.run(['git', 'check-ignore', '--quiet', str(out / 'input_manifest.json')],
                             cwd=REPO, capture_output=True, text=True)
    assert ignored.returncode == 0, 'Private row artifacts must remain ignored by Git'

    current = read(PRIORITY)
    matrix = read(ROOT / current['matrix']['path'])
    for card in matrix['cards']:
        if card['gate'] == 'G4':
            card.update(status=G4STATUS,
                what_changed='Seis fuentes existentes2023 fijadas por SHA; adaptador de ingreso y copias por fold verificados sin fit ni C0. No se copian capitales aprendidos exteriores.',
                required_evidence='Parámetros de calidad de capital del ámbito exacto; integración del ingreso real sin el marcador sintético; objetos C0/preprocesado/GLM/calibrador internos y validación del flujo completo cuando esté autorizado.',
                boundary='Preparación de entradas y verificación sintética previa; no validación predictiva real, cierre de G1/G2 o autorización de ajuste.')
    matrix.update(id=IDENT, author='Codex', utc=now(), source_previous_matrix=current['matrix'],
                  verification_scope='Existing2023 input ingress only; all learned objects absent')
    dump(RUN / 'gate_matrix_updated_G4.json', matrix)
    decisions = [
        ('G4E-01', 'Leer solo seis proyecciones declaradas de Parquet2023 existentes, con SHA histórico y ámbito probado antes de decodificar; no productores multiaño.'),
        ('G4E-02', 'Conservar claves compuestas, componentes y folds; separar metadatos globales de valores por fold; quince ámbitos lógicos, sin resorteo.'),
        ('G4E-03', 'Conservar T0 heredado y sus519siniestros; conciliación en centavos verifica las copias, sin revaluar, recalcular C0 o eliminar casos.'),
        ('G4E-04', 'Capital original y prima separados para auditoría; no copiar x_log_sum_insured exterior, estimar referencias o admitir prima como predictor. Aplicación pura probada solo con constantes ficticias.'),
        ('G4E-05', 'Doce controles nuevos de ingreso pasados; dos lecturas reales por ámbito no abrieron valores protegidos. No extrapolar a todos los objetos aprendidos del flujo.'),
        ('G4E-06', 'G4 avanza en entradas base, no se cierra. G1/G2 y parámetros/objetos internos siguen pendientes. B00 y alternativas conservados;2024cerrado; cero modelos, C0, inferencias o scores nuevos.')]
    dump(RUN / 'decision_journal.json', {'id': IDENT, 'author': 'Codex', 'utc': now(),
         'decisions': [{'id': k, 'decision': v} for k, v in decisions]})

    doc = f'''# G4: adaptador y entradas estrictas de 2023

Codex, {now()}. Preinscripción COD-S2-20261024-061; resultado {FID}. Se preparó el ingreso de datos reales existentes de 2023 para edificios, sin ajustar modelos, recalcular C0, inferir o puntuar. Las entradas base están disponibles; todavía no forman una matriz completa lista para el modelo.

| Salida privada | Filas | Uso y límite |
| --- | ---: | --- |
| Metadatos de pertenencia de tres ramos | {result['counts']['metadata']} | Claves y componentes originales; sin etiquetas ni predictores de los otros ramos |
| Periodos de edificios | {result['counts']['periods']} | Fechas y exposición heredadas, seis características sin aprendizaje nuevo |
| Objetivos observados | {result['counts']['targets']} | T0 original y representación en centavos, separados de predictores |
| Siniestros incluidos | {result['counts']['claims']} | Ocurrencias de 2023 asignadas al periodo; importes heredados |
| Capital y prima para auditoría | {result['counts']['capital_audit']} | Tabla separada; la prima no entra como predictor |

Las seis proyecciones proceden de las entradas ya recortadas a 2023 de coberturas y dev6. Sus SHA coinciden con los manifiestos históricos. Antes de decodificar, el lector comprueba ruta, columnas explícitas y estadísticas de año o fechas por grupo de filas; rechaza fuentes mixtas, sin prueba de ámbito o con hash distinto. No lee columnas C0, precios, scores o capital corregido del fold exterior. Fuentes, columnas, hashes, pruebas de footer y código congelado están en `{rel(RUN / 'source_output_traceability.json')}`. No son fuentes nuevas ni aportan otra cohorte.

Los seis predictores conservados son nuevo negocio, edad del inmueble, zona de inundación, cobertura AD, tipo de inmueble y región. Se heredan del contrato previo; esta tarea no demuestra de nuevo su disponibilidad prospectiva ni admite campos de F02 o clima. La exposición y T0 permanecen iguales. La suma de los siniestros heredados concilia con T0 en centavos para comprobar estas copias. No hubo filas excluidas nuevas. Las fechas de reporte pueden llegar a la valoración original del 31 de diciembre de 2024 para ocurrencias de 2023; eso no abre la cohorte de pólizas de 2024.

Se guardaron archivos de valores por fold, metadatos globales y listas de cinco ámbitos exteriores más diez pares interiores únicos. Cada par puede reutilizarse en sus dos órdenes solo para las entradas simétricas; no declara intercambiables calibradores u otros objetos posteriores. El lector de ámbito abre únicamente los archivos de valores permitidos; conserva metadatos de los protegidos y deja ausentes sus fechas/exposición en la vista preparada para un C0 futuro. La firma de aprendizaje incluye pertenencias y archivos permitidos, sin hashes de valores protegidos. El manifiesto no contiene C0 ni objetos aprendidos.

El ingreso pasó doce controles nuevos: rechazo previo a decodificar de año mixto y hash alterado, rutas de modelos/predicciones, claves duplicadas y componentes cruzados; rechazo de capital sin parámetros o de otro ámbito; aplicación aritmética con constantes ficticias; dos lecturas reales (exclusiones [0] y [0,1]) con apertura de archivos protegidos prohibida; listas disjuntas de los quince ámbitos. No se presenta la inspección de esas listas como quince ejecuciones numéricas. Los fit de Tweedie, Pipeline y C0, las cargas de modelos y la red estuvieron bloqueados durante la preparación; no hubo llamadas prohibidas. Recibos: `{rel(out / 'validation.json')}` y `{rel(out / 'reader_events.json')}`. No se repitieron suites históricas o diagnósticos de soporte, reservas, clima, cola o desempeño.

La dependencia nueva explícita es CAPS2-01: sus referencias de prima por mil se aprendían en el ámbito de ajuste. Se conservó capital original y prima para auditoría y no se copió `x_log_sum_insured` exterior. La séptima característica requiere parámetros congelados y trazables del ámbito exacto. La función de aplicación no los estima y se probó solo con datos y parámetros ficticios; no se aplicó a capital real en este encargo.

G4 queda en ingreso estricto verificado y flujo sintético previo verificado. Faltan los parámetros de calidad de capital por ámbito, conectar el ingreso real mediante un contrato propio, los objetos interiores C0/preprocesado/GLM/calibradores y la comprobación integral de esos objetos bajo un encargo que permita crearlos. No se añade un marcador sintético a filas reales para eludir la protección del módulo anterior. G1 sigue plausible, sin establecer; G2 sigue fallido en soporte retenido y desconocido internamente. Esta preparación no modifica esas conclusiones ni habilita el ensayo del cambio de pendiente de B20.

API de ingreso: `src/semana2/entradas_g4_2023.py`, funciones `read_pinned`, `load_training_scope` y `masked_periods_for_future_C0`. El punto preparado es `{rel(RUN / 'prepared_current.json')}` y el manifiesto, `{rel(out / 'input_manifest.json')}`. El materializador `herramientas/preparar_entradas_g4_2023.py` tiene un resultado válido: reutilizarlo, no repetirlo sobre las mismas fuentes. Las salidas por fila quedan en `privado/`, ignoradas por Git; el paquete sintético anterior conserva su contenido.

Decisiones G4E-01 a G4E-06. B00, alternativas, T0/C0, folds, catálogo y contadores de modelos se conservan. Cero nuevos modelos, ajustes C0, inferencias o scores. 2024/test/ledger/actas/SEL01 permanecen cerrados en este trabajo; la exposición previa a un asunto de foro con información de 2024 no se repite ni se usa. Sin envío, publicación, remoto, otros chats, delegación o automatizaciones. Ventana nocturna cerrada. Verificación técnica propia de Codex en Windows, no revisión profesional independiente ni aprobación humana. Se aplica la ficha de procedencia y recorrido de datos de IAA Documentación §2 y la separación de verificación propia de Gobernanza §2.8.
'''
    with DOC.open('x', encoding='utf-8') as f:
        f.write(doc)
    result_index = {'id': IDENT, 'author': 'Codex', 'utc': now(), 'status': G4STATUS,
        'reference': 'W2-B00', 'all_alternatives_preserved': True, 'path_base': 'workspace_root',
        'run': rel(RUN), 'prepared_attempt': result['attempt'], 'counts': result['counts'],
        'source_projections': 6, 'scope_file_lists': 15, 'real_scope_reader_views_checked': 2,
        'contract_checks': 12, 'contract_failures': 0, 'protected_value_files_decoded_by_scope_reader': 0,
        'new_models': 0, 'new_C0_fits': 0, 'new_predictions': 0, 'new_scores': 0,
        'learned_capital_parameters': 0, 'real_capital_application': False, 'model_input_ready': False,
        'C0_present': False, 'G4_real_full_flow_validated': False, 'G4_real_gate_closed': False,
        'G1_G2_resolved': False, 'new_cohort_or_material_source_correction': False,
        'B00_or_selection_changed': False, '2024_test_closed': True, 'old_diagnostics_repeated': False,
        'submission': False, 'night_window_reopened': False, 'professional_independent_validation': False,
        'documentation': rel(DOC), 'documentation_sha256': sha(DOC),
        'forum_prior': plan['forum_prior'], 'forum_result': FID,
        'blockers': ['Exact-scope frozen capital-quality parameters absent',
                     'Real ingress not wired into a real-data learning contract; synthetic marker must not be bypassed',
                     'Real inner C0/preprocessing/GLM/calibration objects and full-flow validation absent',
                     'G1 mechanism not established; G2 retained support failed and inner support unknown'],
        'next_step': 'Design the exact-scope capital parameter and real orchestration contract without fitting; real learned objects remain outside this authorization.'}
    for key, p in [('plan', PLAN), ('input_manifest', out / 'input_manifest.json'),
                   ('validation', out / 'validation.json'), ('traceability', RUN / 'source_output_traceability.json'),
                   ('matrix', RUN / 'gate_matrix_updated_G4.json'), ('decisions', RUN / 'decision_journal.json')]:
        result_index[key] = {'path': rel(p), 'sha256': sha(p)}
    body = RUN / 'forum_062_result.md'
    with body.open('x', encoding='utf-8') as f:
        f.write(f'''Codex, resultado de la preinscripción061. Adaptador y entradas estrictas2023 preparados sin fit, recálculo C0, inferencias o puntuación. Informe: {rel(DOC)}. Índice: {rel(INDEX)}. Punto reutilizable: {rel(RUN / 'prepared_current.json')}.

Seis fuentes existentes fijadas por SHA histórico, con proyección explícita de columnas y ámbito demostrado por footer antes de decodificar. Salidas:50094pertenencias de tres ramos;12580periodos/objetivos/capitales de edificios;519siniestros2023. Folds/componentes, fechas, exposición y T0 heredados conservados; conciliación en centavos de las copias, sin excluir casos nuevos. Reportes hasta valoración2024-12-31 son seguimiento de ocurrencias2023, sin abrir cohorte2024. Ninguna fuente o cohorte nueva.

Doce controles de ingreso pasaron. Dos lectores reales de ámbito [0] y [0,1] con archivos de valores protegidos prohibidos; listas de cinco exteriores y diez pares interiores disjuntas. Se distinguen15listas de2lecturas comprobadas. Metadatos protegidos conservados, valores ausentes de la vista para C0 futuro; firma de aprendizaje sin hashes de valores protegidos. Fit de Tweedie/Pipeline/C0, carga de modelos y red bloqueados;0llamadas prohibidas. SHA/código/columnas y21footers de salida en source_output_traceability.json. Sin repetición de diagnósticos históricos.

Dependencia de capital explícita: CAPS2-01 aprendía sus referencias del ajuste. No se copia capital corregido exterior. Capital original y prima quedan separados para auditoría, la prima no es predictor; no se produce x_log_sum_insured real ni se estiman referencias. La aplicación pura con parámetros congelados rechaza ausencia u otro ámbito, y solo se comprobó con constantes ficticias. Entrada al modelo: no preparada todavía.

G4 avanza en ingreso real2023; no se cierra. Faltan parámetros de capital por ámbito, contrato de orquestación real y objetos interiores C0/preprocesado/GLM/calibrador con comprobación integral bajo autorización posterior. No se disfrazan datos reales con marcador sintético ni se añaden al ZIP sintético. G1/G2 no cambian y no habilitan el ensayo pendiente. Archivos por fila privados e ignorados por Git. G4E-01 a G4E-06, autor Codex.

B00 y alternativas, T0/C0/folds/catálogo/contadores conservados.2024/test/ledger/actas/SEL01 cerrados en este trabajo. Cero nuevos modelos/C0/inferencias/scores; sin envío, remoto, publicación, contactos, otros chats, delegación o automatizaciones. Ventana nocturna cerrada. Verificación propia exploratoria en Windows; no validación profesional independiente ni aprobación humana.
''')
    process = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor', 'Codex', '--id', FID, '--asunto', 'G4: entradas2023 y adaptador verificados, capital por ámbito y objetos internos pendientes',
        '--cuerpo', str(body)], capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    dump(RUN / 'forum_result_receipt.json', json.loads(process.stdout))
    dump(INDEX, result_index)

    changes = []
    preserved_paths = [REPO / 'registro/semana2_contadores_propios_actual.json',
        REPO / 'registro/semana2_continuidad_nocturna.json',
        REPO / 'privado/semana2/desarrollo2023/g4_flujo_sintetico_20261024_v1/paquete_G4_sintetico_revision_local.zip']
    preserved = {rel(p): sha(p) for p in preserved_paths}

    def change(path, transform, keys=None):
        before = path.read_bytes()
        raw = before.decode('utf-8-sig')
        transformed = transform(raw)
        if keys is not None:
            old, new = json.loads(raw), json.loads(transformed)
            assert {k: v for k, v in old.items() if k not in keys} == {k: v for k, v in new.items() if k not in keys}
        after = transformed.encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):
            after = b'\xef\xbb\xbf' + after
        for phase, payload in [('before', before), ('after', after)]:
            p = RUN / 'registration_cuts' / phase / path.relative_to(ROOT)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open('xb') as f:
                f.write(payload)
        temporary = path.with_name(path.name + '.G4ingress.tmp')
        with temporary.open('xb') as f:
            f.write(after)
            f.flush()
            os.fsync(f.fileno())
        assert path.read_bytes() == before, 'Concurrent edit: ' + rel(path)
        os.replace(temporary, path)
        changes.append({'path': rel(path), 'before_sha256': hashlib.sha256(before).hexdigest(), 'after_sha256': sha(path)})

    def updates(raw, values):
        for k, v in values.items():
            raw = top(raw, k, v)
        return raw

    def priority_update(raw):
        d = json.loads(raw)
        gates = d['current_gate_statuses']
        gates['G4'] = G4STATUS
        blockers = [('G4: strict2023 base inputs verified; scope capital parameters and nested learned objects pending'
                     if str(x).startswith('G4:') else x) for x in d.get('current_blockers', [])]
        return updates(raw, {'current_gate_statuses': gates, 'current_blockers': blockers,
            'previous_G4_input_matrix': d['matrix'], 'matrix': result_index['matrix'],
            'G4_input_preparation_index': rel(INDEX), 'G4_input_preparation_utc': now()})
    change(PRIORITY, priority_update, {'current_gate_statuses', 'current_blockers', 'previous_G4_input_matrix',
                                    'matrix', 'G4_input_preparation_index', 'G4_input_preparation_utc'})

    def source_update(raw):
        d = json.loads(raw)
        gates = d['current_B20_gate_statuses']
        gates['G4'] = G4STATUS
        return updates(raw, {'current_B20_gate_statuses': gates, 'G4_input_preparation_index': rel(INDEX),
            'G4_strict2023_base_inputs_prepared': True, 'G4_real_full_flow_validated': False})
    change(SOURCE, source_update, {'current_B20_gate_statuses', 'G4_input_preparation_index',
                                 'G4_strict2023_base_inputs_prepared', 'G4_real_full_flow_validated'})
    change(DEVELOPMENT, lambda raw: top(raw, 'G4_input_preparation', {
        'index': rel(INDEX), 'utc': now(), 'input_status': G4STATUS,
        'new_fits': 0, 'new_C0_fits': 0, 'new_scores': 0, 'price_catalog_changed': False}), {'G4_input_preparation'})
    change(ROOT / 'Preparación/ESTADO_PROYECTO.json', lambda raw: top(raw, STATEKEY, result_index), {STATEKEY})

    section = f'''\n\n## G4: ingreso estricto de 2023 preparado sin ajustes

Codex, UTC {now()}, preinscripción061 y resultado062; decisiones G4E-01 a G4E-06. Informe {rel(DOC)}, índice {rel(INDEX)}, recibos y punto preparado en {rel(RUN)}. Seis proyecciones de fuentes2023 existentes fijadas por SHA histórico y prueba de ámbito previa a decodificar.50094pertenencias globales,12580periodos/objetivos/capitales de edificios y519siniestros. T0/exposición/claves/componentes/folds heredados conservados; conciliación en centavos de las copias, sin nueva exclusión. Reportes hasta valoración original2024-12-31 son seguimiento de ocurrencias2023, sin abrir cohorte2024.

Doce controles nuevos de ingreso pasados; dos lectores reales con exclusiones [0] y [0,1] no abren valores protegidos. Quince listas de ámbitos disjuntas, no quince ejecuciones completas; metadatos protegidos permitidos y sus valores ausentes. Fit de modelos/C0, carga de modelos y red bloqueados; cero llamadas prohibidas. Código congelado, columnas/SHA de fuentes y21footers de salida archivados. Sin repetir diagnósticos anteriores o reclamar fuente/cohorte nueva.

CAPS2-01 requiere referencias de capital del mismo ámbito. Capital original y prima separados para auditoría; no se copia x_log_sum_insured exterior, no se estima referencia ni se usa prima como predictor. Función de aplicación comprobada solo con constantes ficticias. Faltan parámetros de capital por ámbito, contrato real propio sin eludir marcador sintético, objetos interiores C0/preprocesado/GLM/calibrador y validación integral. G4 no se cierra; G1/G2 conservan sus bloqueos. No reejecutar el materializador válido sobre fuentes iguales. Datos por fila privados, paquete sintético anterior sin cambios.

B00/alternativas/T0/C0/folds/catálogo/contadores conservados; cero modelos, C0, inferencias o scores nuevos.2024/test/ledger/actas/SEL01 cerrados en este trabajo; no se repite ni usa exposición previa ajena. Sin envío, remoto, publicación, contactos, otros chats, delegación o automatizaciones. Ventana nocturna cerrada. Verificación propia de Codex en Windows, exploratoria; no revisión profesional independiente ni aprobación humana.\n'''
    for filename in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        change(ROOT / 'Preparación' / filename, lambda raw: raw + section)
    route_values = {'week_2_G4_strict2023_inputs_index': rel(INDEX),
                    'week_2_G4_strict2023_inputs_report': rel(DOC),
                    'week_2_G4_strict2023_prepared_point': rel(RUN / 'prepared_current.json')}
    change(ROOT / 'RUTAS_PROYECTO.json', lambda raw: updates(raw, route_values), set(route_values))
    integrity = {'id': IDENT, 'utc': now(), 'frozen_code_still_matches': all(sha(ROOT / x['path']) == x['sha256'] for x in plan['frozen_code']),
        'input_source_hashes_still_match': all(sha(ROOT / x['path']) == x['sha256'] for x in plan['sources'].values()),
        'counters_night_index_and_synthetic_zip_unchanged_during_registration': all(sha(ROOT / p) == value for p, value in preserved.items()),
        'preserved_hashes': preserved, 'private_input_manifest_ignored_by_git': True,
        'unrelated_top_level_shared_keys_preserved': True, 'row_values_decoded_during_registration': 0}
    assert integrity['frozen_code_still_matches'] and integrity['input_source_hashes_still_match']
    assert integrity['counters_night_index_and_synthetic_zip_unchanged_during_registration']
    dump(RUN / 'closure_integrity_receipt.json', integrity)
    dump(RUN / 'registration.json', {'changes': changes, 'model_catalog_mutations': 0,
         'model_counter_mutations': 0, 'night_index_mutations': 0, 'old_synthetic_packet_mutations': 0})
    files = [p for p in RUN.rglob('*') if p.is_file()] + [INDEX, DOC, Path(__file__).resolve(),
              REPO / 'herramientas/registrar_plan_entradas_g4_2023.py']
    dump(RUN / 'manifest.json', {'id': IDENT, 'author': 'Codex', 'utc': now(),
        'files': [{'path': rel(p), 'sha256': sha(p)} for p in files]})
    print(json.dumps({'id': IDENT, 'forum_result': FID, 'document': rel(DOC), 'contract_checks': 12,
        'periods': result['counts']['periods'], 'claims': result['counts']['claims'],
        'model_input_ready': False, 'new_fits': 0, 'C0_recalculated': False, 'integrity': True}, ensure_ascii=True))


if __name__ == '__main__':
    main()
