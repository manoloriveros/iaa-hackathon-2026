"""Cierra producción de capital y prepara receta estándar, sin entrenamiento."""
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
RUN = REPO/'privado/semana2/capital_real_g4_2023/produccion_20261024_v1'
PLAN = REPO/'registro/semana2_g4_capital_real_plan_v1.json'
INDEX = REPO/'registro/semana2_g4_capital_real_actual.json'
DOC = REPO/'docs/semana2/G4_CAPITAL_REAL_Y_PREPARACION_MODELO_2023.md'
MODEL = REPO/'registro/semana2_g4_modelo_envio_preparacion_v1.json'
PRIORITY = REPO/'registro/semana2_b20_prioridades_actual.json'
SOURCES = REPO/'registro/semana2_b20_fuentes2023_actual.json'
PREVIOUS = REPO/'registro/semana2_g4_productor_capital_actual.json'
DEVELOPMENT = REPO/'registro/semana2_desarrollo2023_actual.json'
IDENT = 'S2-G4-CAPITAL-REAL2023-FINAL-v1-20261024'
FID = 'COD-S2-20261024-068'
STATEKEY = 'week_2_G4_real_capital_and_model_preparation2023_v1_20261024'
STATUS = 'real_scope_capital_and_base_input_connection_verified_full_learning_and_final_scope_pending'
now = lambda: datetime.now(timezone.utc).isoformat()
rel = lambda p: p.relative_to(ROOT).as_posix()
sha = ingress.sha
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    assert not INDEX.exists() and not MODEL.exists() and not DOC.exists(), 'Reconcile partial closure before retry'
    plan, result = read(PLAN), read(RUN/'prepared_current.json')
    out = ROOT/result['out']
    rows = result['scope_results']
    assert result['success'] and len(rows) == result['real_parameter_artifacts'] == result['real_feature_views'] == 15
    assert result['model_fits'] == result['C0_calls'] == result['new_predictions'] == result['new_scores'] == 0
    assert result['all_scope_readers_protected_values_blocked'] and result['all_independent_arithmetic_checks_passed']
    assert all(sha(ROOT/x['path']) == x['sha256'] for x in plan['frozen_code'])
    assert sha(ROOT/plan['input_manifest']['path']) == plan['input_manifest']['sha256']
    for row in rows:
        for key in ['parameters', 'features']:
            assert sha(ROOT/row[key]['path']) == row[key]['sha256']
        assert row['base_features_ready'] and not row['C0_present'] and not row['fit_allowed']
    events = read(out/'reader_events.json')
    assert not events['forbidden_calls']
    max_bound_error = max(max(r['arithmetic']['min_bound_abs_error'], r['arithmetic']['max_bound_abs_error']) for r in rows)
    max_log_error = max(r['arithmetic']['log_capital_max_abs_error'] for r in rows)
    assert max(max_bound_error, max_log_error) <= 1e-12
    dump(RUN/'real_capital_connection_registry.json', {'id': IDENT, 'author': 'Codex', 'utc': now(),
        'input_manifest': plan['input_manifest'], 'scopes': rows, 'real_parameter_artifacts': 15,
        'base_features_ready': True, 'model_input_ready': False, 'C0_present': False,
        'fit_allowed': False, 'new_models': 0, 'new_scores': 0})

    # Preparación del modelo: receta preexistente, sin repetir la tandaB20.
    recipe_path = REPO/'registro/semana2_glm_ridge_coberturas_plan_v1.json'
    recipe = read(recipe_path)
    assert recipe['model_id'] == 'W2-B20'
    old_run = ROOT/recipe['output_run']
    old_manifest_path = old_run/'manifest.json'
    old_manifest = read(old_manifest_path)
    bundles = [x for x in old_manifest['files'] if x['path'].replace('\\','/').startswith('models/') and x['path'].endswith('/bundle.joblib')]
    assert len(bundles) == 15
    model_inventory = []
    for item in bundles:
        p = old_run/item['path']
        assert sha(p) == item['sha256'], 'Saved2023 model bytes changed'
        model_inventory.append({'path': rel(p), 'sha256': item['sha256'], 'role': 'existing_saved_fold_model_not_final_all2023_model'})
    dump(RUN/'existing_standard_model_inventory.json', {'id': IDENT, 'author': 'Codex', 'utc': now(),
        'source_manifest': {'path': rel(old_manifest_path), 'sha256': sha(old_manifest_path)},
        'models': model_inventory, 'model_deserializations': 0, 'new_inferences': 0,
        'scope': 'Byte identity and inventory only; no new execution or scoring certification'})
    gaps = [
        {'gate': 'final_scope', 'status': 'not_registered_in_this_G4_pipeline',
         'needed': 'Explicit full2023 deployment scope. Current capital contract supports one/two exclusions; do not use an outer artifact as a full-cohort object.'},
        {'gate': 'C0', 'status': 'final_scope_object_not_registered_in_this_package',
         'needed': 'Traceable same-scope frozen C0 and contract for2025 application. This continuation cannot estimate/recalculate it.'},
        {'gate': 'final_standard_model', 'status': 'not_fitted_under_this_request',
         'needed': 'Complete2023 final GLM/preprocessor objects for each branch, or explicit justified use of existing fold objects; no silent ensemble or duplicate OOF run.'},
        {'gate': 'all_branches_and_2025', 'status': 'not_connected_in_this_G4_package',
         'needed': 'Complete motor/contents feature contracts and2025 inference/ID-order pipeline. Only buildings base capital connection was checked here.'}]
    model_config = {'id': 'G4-STANDARD-SUBMISSION-PREPARATION-v1-20261024', 'author': 'Codex', 'utc': now(),
        'status': 'standard_recipe_prepared_no_new_fit_no_prediction',
        'participant_latest_literal': 'no,continua con las validaciciones y empecemos a preparar un modelo para enviar',
        'existing_csv_reuse_declined': True, 'candidate_is_G4_preparation_not_existing_mixture': True,
        'source_recipe': {'path': rel(recipe_path), 'sha256': sha(recipe_path), 'model_id': 'W2-B20'},
        'recipe': recipe['recipe'], 'objective': recipe['objective'],
        'reference': 'W2-B00', 'all_alternatives_preserved': True,
        'model_choice_rationale': 'Reuse an already specified standard main-effects GLM without extra calibration or a new hyperparameter search; not selected by a new2023score.',
        'unchanged_standard_params': recipe['recipe']['params'],
        'no_new_recipe_or_validation_training': True,
        'no_extra_climate_credibility_trend_or_calibration': True,
        'capital_registry': {'path': rel(RUN/'real_capital_connection_registry.json'), 'sha256': sha(RUN/'real_capital_connection_registry.json')},
        'existing_fold_model_inventory': {'path': rel(RUN/'existing_standard_model_inventory.json'), 'sha256': sha(RUN/'existing_standard_model_inventory.json')},
        'readiness_gaps': gaps, 'fit_allowed_by_current_preparation': False, 'C0_recalculation_allowed': False,
        'training_years_if_later_authorized': [2023], '2024_closed': True,
        'current_G1_G2_resolved': False, 'B20_historical_adverse_results_preserved': True,
        'promotion': False, 'final_roster_frozen': False, 'CSV_produced': False, 'submission_sent': False}
    dump(MODEL, model_config)
    dump(RUN/'model_readiness.json', {'id': model_config['id'], 'author': 'Codex', 'utc': now(),
        'scope': 'Configuration/asset inventory and missing contracts,not a numerical model test',
        'capital_base_connection_ready': True, 'standard_recipe_available': True,
        'existing_fold_model_bytes_verified': 15, 'fit_or_final_prediction_ready': False,
        'gaps': gaps, 'models_loaded': 0, 'models_fitted': 0, 'C0_calls': 0})
    dump(RUN/'environment.json', {'python': sys.version, 'platform': sys.platform,
        'packages': {p: md.version(p) for p in ['numpy', 'pandas', 'pyarrow', 'scikit-learn', 'joblib']},
        'hosted_Kaggle_or_Linux_verified': False})
    ignored = subprocess.run(['git','check-ignore','--quiet',str(out/'scopes/exclude_0/g4_periods_features.parquet')], cwd=REPO)
    assert ignored.returncode == 0

    current = read(PRIORITY)
    matrix = read(ROOT/current['matrix']['path'])
    for card in matrix['cards']:
        if card['gate'] == 'G4':
            card.update(status=STATUS,
                what_changed='Quince artefactos reales de capital y quince conexiones base G4 de2023,población/replay/aritmética independientes verificados sin modelos/C0.',
                required_evidence='Ámbito final de todo2023,C0 del ámbito correcto y objetos de preprocesado/GLM/calibración que correspondan;conexión de demás ramos/2025 y prueba integral bajo alcance posterior.',
                boundary='Conexión numérica real de entradas base,no entrenamiento o flujo predictivo completo;G1/G2 y adversos históricos conservados.')
    matrix.update(id=IDENT, author='Codex', utc=now(), source_previous_matrix=current['matrix'],
        verification_scope='Real2023 capital parameter production and base input connection; standard model configuration only')
    dump(RUN/'gate_matrix_updated_G4.json', matrix)
    decisions = [
        ('G4R-01','Producir15parámetros y15vistas reales2023 con receta/folds congelados,solo desde capital permitido;sin referencias exteriores usadas como interiores.'),
        ('G4R-02','Reconocer replay de población y comparación Decimal/math.log con error máximo0,ausencias iguales y claves/objetivos heredados conservados;no prueba de último o disponibilidad prospectiva.'),
        ('G4R-03','Mantener G4 integral abierto:capital/conexión base reales resueltos,objetos aprendidos y ámbito final pendientes;G1/G2 no cambian.'),
        ('G4R-04','Seguir instrucción de modelo propio:sin copiar mezcla50 o emitirCSV existente.Preparar receta GLM estándar preexistente y verificar15objetos de fold solo como bytes.'),
        ('G4R-05','No repetir entrenamientoB20 sobre mismas fuentes,crear otro idexperimental,usar un ámbito exterior como final o inventarC0.No ajustar bajo la restricción vigente.'),
        ('G4R-06','B00/alternativas,T0/exposición/C0/folds/catálogo/contadores conservados;2024cerrado,cero modelos,C0,inferencias/scores/envíos y sin promoción o lista final.')]
    dump(RUN/'decision_journal.json', {'id': IDENT, 'author': 'Codex', 'utc': now(),
        'decisions': [{'id':k,'decision':v} for k,v in decisions]})
    table = '\n'.join('| '+r['scope']+' | '+str(r['training_rows'])+' | '+str(r['normal_rows'])+' | '+str(r['missing_log_capital_rows'])+' |' for r in rows)
    doc = f'''# G4: capital real de 2023 y preparación de un modelo propio

Codex, {now()}. Preinscripción COD-S2-20261024-067; resultado {FID}. Se generaron quince artefactos de parámetros de capital y quince vistas de entrada de edificios con datos reales de 2023. La conexión base a G4 pasó los controles por ámbito. No se ajustaron modelos ni se llamó a C0; no hubo inferencias, scores o CSV nuevos. El participante pide continuar con un modelo propio para el envío.

Son 12.580 periodos únicos de edificios. Las vistas contienen 125.800 copias de periodos porque cada uno aparece en cuatro ajustes exteriores y seis pares interiores. Cada ámbito abre únicamente los archivos permitidos; la producción y referencia independiente solo leen metadatos, capital y prima. La conexión abre objetivos/notificaciones de los folds permitidos, conserva T0/exposición y no usa valores protegidos. Los reportes heredados hasta valoración2024 corresponden a ocurrencias2023, sin abrir la cohorte2024.

| Ámbito | Periodos permitidos | Capitales normales de referencia | Log capital ausente |
| --- | ---: | ---: | ---: |
{table}

La población normal de los ámbitos tiene entre {min(r['normal_rows'] for r in rows)} y {max(r['normal_rows'] for r in rows)} filas. Los recibos de población se reprodujeron contra el capital permitido. La referencia independiente calculó límites con Decimal y capital corregido/log con Decimal y `math.log`: error absoluto máximo de límites {max_bound_error} y de log {max_log_error}, con criterio1e-12 y las mismas decisiones de ausencia. Seleccionar capitales normales para referencias no elimina periodos o siniestros del modelo. La prima sigue fuera de los predictores.

Los parámetros, poblaciones/recibos, vistas por ámbito y comprobaciones independientes están enlazados desde `{rel(RUN/'real_capital_connection_registry.json')}`. Cada vista tiene `base_features_ready=true`, `C0_present=false`, `fit_allowed=false` y `model_input_ready=false`. El punto reutilizable es `{rel(RUN/'prepared_current.json')}`. La suite sintética anterior no se repitió; sus fuentes congeladas se conservaron. Fit/predict de modelos/preprocesadores,C0 fit/apply,cargas de modelos y red estuvieron bloqueados durante la producción real, sin llamadas prohibidas.

## Preparación del modelo para el envío

La configuración `{rel(MODEL)}` conserva la receta GLM estándar de efectos principales ya especificada en B20: Tweedie1,5, enlace log, alpha1, mediana y escala numéricas aprendidas solo del ajuste y codificación categórica del ajuste. Copia la definición por los tres ramos y su objetivo original; no añade clima, credibilidad, tendencia o calibración de nivel/pendiente. B00 permanece como referencia y los resultados adversos previos se conservan. Esta preparación no promueve B20 ni reabre su ensayo de calibración.

Se inventariaron quince objetos guardados por fold de la receta B20 y sus SHA coinciden con el manifiesto de origen. No se deserializaron, predijeron o puntuaron; esa comprobación solo identifica activos reutilizables. No se repite la tanda histórica sobre las mismas fuentes ni se crea otro identificador experimental por cambiar el empaquetado.

Faltan contratos y objetos concretos antes de producir un CSV propio. El flujo actual soporta exclusiones de uno o dos folds; debe declararse un ámbito de despliegue de todo2023, sin disfrazar un objeto exterior como si fuera de toda la cohorte. Hace falta C0 congelado del ámbito correcto y la aplicación a2025, más los objetos finales de preprocesado/GLM de los ramos que se usen. El paquete actual no registra esos objetos finales ni la conexión de motor/contenidos y2025. La restricción de esta continuación sigue siendo no ajustar modelos ni recalcular C0. La lista exacta está en `{rel(RUN/'model_readiness.json')}`; es una revisión de configuración y activos, no una nueva validación numérica del modelo.

La entrega se preparará con el modelo propio cuando estén resueltas esas dependencias. No se copió el CSV existente de otra receta, no se generó un CSV de ceros o valores auxiliares y no se envió nada a Kaggle. Los metadatos públicos de Kaggle se consultaron para el contrato de entrega; siguen las inconsistencias documentales de la página de reglas etiquetada parte1. No se usaron scores públicos para elegir receta o parámetros, ni se abrieron resultados de2024.

G4 avanza a parámetros/conexión base reales verificados. Su flujo predictivo completo continúa abierto; G1/G2, mecanismo/soporte y límites de último/disponibilidad temporal no se resuelven con estos cálculos. Ningún artefacto de capital equivale a un precio o modelo listo para producción.

Decisiones G4R-01 a G4R-06. B00/alternativas,T0/exposición/C0/folds/catálogo/contadores de modelos conservados;2024/test de modelado/ledger/actas/SEL01 cerrados en este trabajo. Cero modelos, C0, predicciones, scores o envíos nuevos. Sin promoción,lista final,publicación,remoto,otros chats,delegación o automatizaciones. Ventana nocturna cerrada. Autor Codex,verificación propia exploratoria en Windows,no revisión profesional independiente ni aprobación humana. Procedencia y límites conforme a IAA Documentación§2 y Gobernanza§2.8.
'''
    with DOC.open('x', encoding='utf-8') as f:
        f.write(doc)
    index = {'id':IDENT,'author':'Codex','utc':now(),'status':STATUS,'path_base':'workspace_root','run':rel(RUN),
        'documentation':rel(DOC),'documentation_sha256':sha(DOC),'forum_prior':plan['forum_prior'],'forum_result':FID,
        'reference':'W2-B00','all_alternatives_preserved':True,'real_parameter_artifacts':15,'real_feature_views':15,
        'unique_building_periods':12580,'total_period_copies':125800,'all_scope_reads_protected_values_blocked':True,
        'max_independent_bound_error':max_bound_error,'max_independent_log_error':max_log_error,
        'G4_real_base_input_connection_verified':True,'G4_real_full_flow_validated':False,'G4_real_gate_closed':False,
        'G1_G2_resolved':False,'standard_model_recipe_prepared':True,'existing_fold_models_bytes_verified':15,
        'model_deserializations':0,'model_fits':0,'C0_calls':0,'new_predictions':0,'new_scores':0,
        'model_input_ready':False,'2024_closed':True,'submission_sent':False,'CSV_produced':False,
        'existing_csv_reuse_declined':True,'old_suites_or_diagnostics_repeated':False,'professional_independent_validation':False,
        'remaining_model_gaps':gaps,'next_step':'Declare final all2023 deployment scope and resolve frozen C0/final model dependencies before fitting or2025inference; keep2024closed.'}
    for key,p in [('plan',PLAN),('registry',RUN/'real_capital_connection_registry.json'),('model_preparation',MODEL),
        ('readiness',RUN/'model_readiness.json'),('matrix',RUN/'gate_matrix_updated_G4.json'),('decisions',RUN/'decision_journal.json')]:
        index[key]={'path':rel(p),'sha256':sha(p)}
    body = RUN/'forum_068_result.md'
    body.write_text(f'''Codex,resultado de la preinscripción067 y nueva instrucción del participante de continuar con un modelo propio. Informe:{rel(DOC)}. Índice:{rel(INDEX)}. Capital real:{rel(RUN/'real_capital_connection_registry.json')}. Modelo preparado:{rel(MODEL)}.

Quince ámbitos reales2023 completos:15artefactos de parámetros y15vistas de edificios,12580periodos únicos y125800copias de ajuste. Productor/referencia independiente solo leen capital/prima y metadatos permitidos; conexión por archivos permitidos con valores protegidos prohibidos. Población normal/replay de recibo y comparación Decimal de límites y Decimal/math.log de capital:errores máximos0,criterio1e-12 y mismas ausencias. T0/exposición/folds y periodos/siniestros conservados. No se repitió la suite sintética o diagnósticos históricos.

Fit/predict de modelos/preprocesadores,C0 fit/apply,cargas de modelos y red bloqueados durante producción;0llamadas prohibidas. Cero ajustes de modelos,C0,inferencias o scores. Los parámetros/vistas reales cierran ese tramo de entrada base,G4 integral sigue abierto.

Se prepara receta estándar de efectos principales ya congelada en B20 (Tweedie1,5,alpha1),sin nueva búsqueda,clima,credibilidad,tendencia o calibración. B00 como referencia y adversos previos preservados;no promoción ni reapertura del ensayo de pendiente. Quince objetos existentes de fold cotejados como bytes con su manifiesto,sin cargar estimadores. No repetir su entrenamiento sobre mismas fuentes por empaquetar.

Para un CSV propio faltan ámbito final de todo2023,C0 congelado de ese ámbito y su aplicación2025,objetos finales por ramo y conexión completa2025. No usar objeto exterior como final ni fabricar C0. La preparación mantiene la restricción de no ajustar/recalcular. Readiness detalla carencias,no certifica el flujo numérico del modelo. El participante descarta copiarCSVexistente;no se generóCSV ni se envió nada. Los metadatos públicos de Kaggle se verificaron sin scores utilizados para decidir.

G4R-01 a G4R-06,autor Codex.B00/alternativas,T0/exposición/C0/folds/catálogo/contadores conservados.2024/test de modelado/ledger/actas/SEL01 cerrados en este trabajo;G1/G2 sin cambio. Sin promoción,lista final,publicación,remoto,contactos,otros chats,delegación o automatizaciones;ventana nocturna cerrada. Verificación propia exploratoria en Windows,sin aprobación humana o revisión profesional independiente.
''', encoding='utf-8')
    post = subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',FID,
        '--asunto','G4: capital real2023 verificado y receta estándar propia preparada,sin modelos/C0 nuevos','--cuerpo',str(body)],capture_output=True,text=True)
    assert post.returncode == 0,post.stderr
    dump(RUN/'forum_result_receipt.json',json.loads(post.stdout));dump(INDEX,index)
    preserved_paths=[REPO/'registro/semana2_contadores_propios_actual.json',REPO/'registro/semana2_continuidad_nocturna.json',
        ROOT/plan['input_manifest']['path'],old_manifest_path]+[ROOT/x['path'] for x in model_inventory]
    preserved={rel(p):sha(p) for p in preserved_paths};changes=[]
    def change(path,fn,allowed=None):
        before=path.read_bytes();raw=before.decode('utf-8-sig');updated=fn(raw)
        if allowed is not None:
            old,new=json.loads(raw),json.loads(updated)
            assert {k:v for k,v in old.items() if k not in allowed}=={k:v for k,v in new.items() if k not in allowed}
        after=updated.encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        for phase,payload in [('before',before),('after',after)]:
            p=RUN/'registration_cuts'/phase/path.relative_to(ROOT);p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(payload)
        tmp=path.with_name(path.name+'.G4real.tmp')
        with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert path.read_bytes()==before,'Concurrent edit: '+rel(path);os.replace(tmp,path)
        changes.append({'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path)})
    def update(raw,values):
        for key,value in values.items():raw=top(raw,key,value)
        return raw
    def priority_update(raw):
        d=json.loads(raw);g=d['current_gate_statuses'];g['G4']=STATUS
        blockers=[('G4: real scope capital/base connection verified; final scope and learned objects pending' if str(x).startswith('G4:') else x) for x in d.get('current_blockers',[])]
        return update(raw,{'current_gate_statuses':g,'current_blockers':blockers,'G4_real_capital_index':rel(INDEX),
            'G4_real_capital_utc':now(),'previous_G4_real_capital_matrix':d['matrix'],'matrix':index['matrix']})
    change(PRIORITY,priority_update,{'current_gate_statuses','current_blockers','G4_real_capital_index','G4_real_capital_utc','previous_G4_real_capital_matrix','matrix'})
    def source_update(raw):
        d=json.loads(raw);g=d['current_B20_gate_statuses'];g['G4']=STATUS
        return update(raw,{'current_B20_gate_statuses':g,'G4_real_capital_index':rel(INDEX),'G4_real_base_input_connection_verified':True,'G4_real_full_flow_validated':False})
    change(SOURCES,source_update,{'current_B20_gate_statuses','G4_real_capital_index','G4_real_base_input_connection_verified','G4_real_full_flow_validated'})
    link={'index':rel(INDEX),'utc':now(),'status':STATUS,'real_capital_artifacts':15,'model_fits':0,'C0_calls':0,'full_learning_pending':True}
    change(PREVIOUS,lambda raw:top(raw,'subsequent_real_capital',link),{'subsequent_real_capital'})
    change(DEVELOPMENT,lambda raw:top(raw,'G4_real_capital_and_model_preparation',link),{'G4_real_capital_and_model_preparation'})
    change(ROOT/'Preparación/ESTADO_PROYECTO.json',lambda raw:top(raw,STATEKEY,index),{STATEKEY})
    section=f'''\n\n## G4: capital real verificado y modelo propio en preparación

Codex,UTC {now()},preinscripción067 y resultado068;G4R-01 a G4R-06.Informe {rel(DOC)},índice {rel(INDEX)},registro {rel(RUN/'real_capital_connection_registry.json')}.Quince parámetros reales y quince vistas2023,12580periodos únicos/125800copias por ámbito.Valores protegidos no abiertos dentro de cada ajuste;poblaciones/recibos reproducidos y Decimal/math.log con errores máximos0/ausencias iguales,tolerancia1e-12.Sin suite sintética o diagnósticos repetidos.Sin fit/predict,C0 fit/apply,cargas o red durante producción;0llamadas prohibidas.

Participante pide continuar con modelo propio,no copiarCSVexistente.Configuración {rel(MODEL)} conserva receta GLM estándarB20(Tweedie1,5,alpha1) y objetivo/preprocesado por ramo;sin nueva búsqueda o calibración.Quince objetos de fold verificados solo como bytes,no cargados.No duplicar entrenamiento2023 por empaquetar.B00 y adversos/alternativas preservados,no promoción.ParaCSVpropio faltan ámbito final de todo2023,C0del ámbito/aplicación2025,objetos finales por ramo y conexión completa;readiness {rel(RUN/'model_readiness.json')}.No usar exterior como final o fabricarC0.No ajustar bajo esta continuación.

G4base real resuelto,G4integral/G1/G2 abiertos.Cero modelos,C0,inferencias,scores,CSV o envíos nuevos.T0/exposición/folds/catálogo/contadores conservados;2024/test de modelado/ledger/actas/SEL01 cerrados.Sin remoto,publicación,contactos,otros chats,delegación o automatizaciones;ventana nocturna cerrada.Verificación propia exploratoria de Codex en Windows,sin aprobación humana o revisión profesional independiente.\n'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+section)
    routes={'week_2_G4_real_capital_index':rel(INDEX),'week_2_G4_real_capital_report':rel(DOC),
        'week_2_G4_real_capital_registry':rel(RUN/'real_capital_connection_registry.json'),'week_2_G4_submission_model_preparation':rel(MODEL)}
    change(ROOT/'RUTAS_PROYECTO.json',lambda raw:update(raw,routes),set(routes))
    integrity={'id':IDENT,'utc':now(),'frozen_numeric_sources_match':all(sha(ROOT/x['path'])==x['sha256'] for x in plan['frozen_code']),
        'original_models_counter_night_input_manifest_preserved':all(sha(ROOT/p)==value for p,value in preserved.items()),
        'preserved_hashes':preserved,'unrelated_top_level_shared_keys_preserved':True,'private_feature_file_ignored_by_git':True,
        'model_loads_or_fits_during_registration':0,'new_data_value_decodes_during_registration':0}
    assert integrity['frozen_numeric_sources_match'] and integrity['original_models_counter_night_input_manifest_preserved']
    dump(RUN/'closure_integrity_receipt.json',integrity);dump(RUN/'registration.json',{'changes':changes,'model_catalog_mutations':0,'model_counter_mutations':0,'night_index_mutations':0})
    files=[p for p in RUN.rglob('*') if p.is_file()]+[INDEX,DOC,MODEL,Path(__file__).resolve(),REPO/'herramientas/registrar_plan_capital_real_g4_2023.py',REPO/'herramientas/registrar_resultado_entradas_g4_2023.py']
    dump(RUN/'manifest.json',{'id':IDENT,'author':'Codex','utc':now(),'files':[{'path':rel(p),'sha256':sha(p)} for p in files]})
    print(json.dumps({'id':IDENT,'forum_result':FID,'document':rel(DOC),'real_parameter_artifacts':15,'model_recipe_prepared':rel(MODEL),
        'existing_fold_models_verified_as_bytes':15,'model_fits':0,'C0_calls':0,'CSV_produced':False,'G4_full_flow_validated':False,'integrity':True},ensure_ascii=True))


if __name__=='__main__':main()
