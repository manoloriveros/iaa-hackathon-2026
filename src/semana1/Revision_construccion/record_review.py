"""Cierra la revisión sin modificar su corrida ni el catálogo preparado activo."""
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import shutil
import subprocess

import analyze_construction as a


def main():
    root = a.ROOT
    pointer = json.loads((a.BASE / 'current_run.json').read_text(encoding='utf-8'))
    out = root / pointer['workspace_relative_run']
    assert pointer['status'] == 'verified_review_candidate_not_active'
    summary = json.loads((out / 'summary.json').read_text(encoding='utf-8'))
    verification = json.loads((out / 'verification.json').read_text(encoding='utf-8'))
    assert verification['passed'] and verification['checks_count'] == 100
    manifest_hash = a.c.digest(out / 'manifest.json')
    protocol = root / 'Hackaton/Semana 1/Modelado/protocolo_metodologico.json'
    protocol_hash = a.c.digest(protocol)
    manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
    assert all(a.c.digest(out / x['path']) == x['sha256'] for x in manifest['files'])
    # Closure is a new artifact. The verified 48-file run remains byte-identical.
    ident = datetime.now(timezone.utc).strftime('closure_%Y%m%dT%H%M%SZ')
    closure = a.BASE / 'closures' / ident
    (closure / 'before').mkdir(parents=True, exist_ok=False)
    (closure / 'after').mkdir()
    docs = ['Preparación/MEMORIA_PROYECTO.md','Preparación/ESTADO_PROYECTO.json','Preparación/DECISIONES.md',
            'RUTAS_PROYECTO.json','Hackaton/Semana 1/README.md']
    for path in docs:
        dest = closure / 'before' / path
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(root / path, dest)
    for name in ['record_review.py','verify_report.js']:
        shutil.copy2(a.BASE / name, closure / name)
    # Report logic only; no data/target/model processing is repeated.
    report_check = subprocess.run(['node', str(a.BASE / 'verify_report.js'), str(out / 'informe.html')],
                                  capture_output=True,text=True,encoding='utf-8',check=True)
    js = json.loads(report_check.stdout)
    assert js['passed'] and js['checks_count'] == 8
    a.c.dump(closure / 'report_logic_verification.json', js)
    decisions = root / 'Preparación/DECISIONES.md'
    decision_text = decisions.read_text(encoding='utf-8')
    number = max(int(x) for x in re.findall(r'\bD(\d+)\b',decision_text)) + 1
    decision = 'D' + str(number)
    rel = '../' + out.relative_to(root).as_posix()
    body = f'''

### {decision}, construcción T/W y recodificación de 2023, 16 de octubre de 2026, America/Bogota

El participante pidió revisar si T y W representan la misma construcción, comparando historiales antes y después de 2023, y decidir si pueden unificarse sin alterar originales. Se concluye que hay respaldo fuerte para tratarlos como alias temporales de una misma clase observada en estos datos. La recomendación técnica CON01 es t,w→tw_code en un campo adicional construction_type_harmonized. No se declara equivalencia física confirmada ni nombre timber confirmado por el organizador. La aprobación de activación por el participante no se presume: se preparó una copia candidata aislada y el catálogo activo de D38 permanece byte a byte igual.

La corrida {rel} examina las 707.726 filas de edificios de entrenamiento y 184.155 de test. T tiene 40.994 filas en 2021–2022; W tiene 44.562 en entrenamiento 2023–2024 y 22.261 en test 2025. La decisión se apoya solo en X de entrenamiento; test X sirve de confirmación. No se consultan resultados de siniestros para inferir el mapa ni se entrenan modelos. T termina el 31-12-2022 y W empieza el 01-01-2023.

Se comparan periodos consecutivos de la misma póliza y dirección, sin productos cartesianos por año. En 2022→2023 hay 149.887 pares: brick→brick 104.960; non_standard→non_standard 14.830; stone→stone 11.879; T→W 18.218. Las 18.218 son pólizas y direcciones distintas; el cambio ocurre el 1 de enero de 2023 y no hay hueco de cobertura. Tomador, dirección, ocupación, daño accidental, hipoteca, deducibles, canal y forma de pago coinciden en todos esos pares. Los campos anuales y el capital pueden cambiar; no se exige falsa estabilidad absoluta. La mediana del cociente de capital 2023/2022 ronda 1,03 en todas las clases, tras excluir las filas de la cohorte congelada pendiente, sin ajustar ningún importe ni inferir una tarifa.

La revisión completa cubre 449.658 transiciones de entrenamiento con igual dirección, 599.769 incluyendo test y 292.112 direcciones. No hay contradicciones de clase tras agrupar T/W. Las direcciones están anidadas en la póliza; esa comprobación no constituye otra muestra independiente. Hay 34.356 cambios de dirección y 16.297 conservan un cambio de clase armonizada. No se fusionan brick, stone o non_standard ni se confunden mudanzas con recodificación. Las filas T de 2022 se concilian en 18.218 continuaciones, 831 con periodo posterior dentro de 2022 en otra dirección y 3.225 sin observación posterior. W de 2023 incluye esas 18.218 continuaciones, 815 direcciones nuevas dentro de 2023 y 3.320 primeras observaciones.

El informe conserva seis casos reales y su historia completa. B00002966, A4975624, muestra T,T,W,W,W y capitales 200.000, 206.000, 212.000, 219.000 y 225.000 CU. B00122195 cambia el 04-04-2023 de brick/A8648946 a W/A9770512. B00159762 cambia el 24-09-2022 de T/A5112030 a brick/A6226236. B00025264 es una primera observación W en 2023 sin historia T individual. La selección y tablas exhaustivas quedan conservadas.

Las dos tablas candidatas añaden una columna sin cambiar ninguna celda previa. Se agrupan 107.817 filas (85.556 de entrenamiento y 22.261 de test), manteniendo construction_type literal normalizado. El catálogo candidato referencia sin cambios las otras nueve tablas; las bitácoras identifican cada fila agrupada y distinguen adición de campo de sustitución de valores. Eliminar el campo añadido revierte exactamente los datos y metadatos previos. No se modifican las 2.073 reparaciones CAP01 ni los 1.454 capitales pendientes. Se conservan originales, datos previos y todos los archivos de sus manifiestos.

Pasaron 100 controles propios, incluido un emparejamiento separado por fechas desde los códigos originales, correspondencia directa a candidata, todos los valores anteriores, reversión, idempotencia, rechazo de códigos nuevos, cohortes, casos y hashes. Ocho controles adicionales prueban el explorador con DOM mínimo y CSV alternativo; no acreditan renderizado en navegador. Se inspeccionaron visualmente ambas figuras. La lógica alternativa no es revisión independiente. run.json conserva el estado al acabar el análisis; verification.json y current_run.json registran el estado final verificado, sin reescribir esa corrida al cerrar la memoria.

Para preparar 2025, el mapa se congela con referencia de disponibilidad 31-12-2024. No se declara conocido antes de 2023 en un backtest sin fuente previa. Si se adopta, usar la variable armonizada en lugar de añadir simultáneamente el código literal como predictor y conservar una ablación literal; los códigos T/W identifican el régimen de calendario. Una adaptación de esquema basada en X de validación debe declararse. La mejora predictiva y el efecto tarifario siguen sin estimarse.

Aplican IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §§3.2 y 3.5–3.6. Codex generó hipótesis, análisis, código, candidata y verificaciones locales; el participante pidió esta revisión. No hubo llamadas a proveedores externos, fondos, entrenamiento, envíos, publicación o delegación. Quedan pendientes el nombre material, la revisión humana de activación y las carencias de modelado ya registradas. Revisar la correspondencia si llega un diccionario explícito o aparecen códigos, fechas o historias contradictorias en la segunda semana.
'''
    decisions.write_text(decision_text + body, encoding='utf-8')
    memory = root / 'Preparación/MEMORIA_PROYECTO.md'
    memory.write_text(memory.read_text(encoding='utf-8') + f'''

## {decision}: T/W como alias temporales, candidata sin activar, 16 de octubre de 2026

La [revisión longitudinal]({rel}/informe.html) respalda t,w→tw_code como clase común observada, con material físico aún sin confirmar. [Reproducción y límites](../Hackaton/Semana 1/Revision_construccion/README.md). Se compararon las 891.881 filas de edificios, 149.887 pares en la misma dirección al cruzar 2022→2023 y 18.218 T→W, todos el 1 de enero sin hueco. Las otras tres clases permanecen iguales. No hay contradicción después de agrupar en 449.658 transiciones de entrenamiento o 599.769 con confirmación de test, ni en 292.112 direcciones. Direcciones e historias están anidadas, no son evidencia independiente adicional.

Se concilian altas, bajas y mudanzas, con seis casos reales. B00002966 muestra T,T,W,W,W en A4975624; B00122195 cambia de brick a W con otra dirección en abril de 2023. El diccionario enumera timber pero no explica T/W; no asignarle ese nombre como confirmado. La propuesta usa solo X de entrenamiento de 2021–2024; 2025 es confirmación. No usar el mapa como conocimiento anterior a 2023 en backtests sin fuente previa; conservar una variante literal y declarar adaptaciones desde X de validación.

El [catálogo candidato]({rel}/candidate/dataset_catalog.json) añade construction_type_harmonized en dos tablas, con 107.817 filas agrupadas (85.556 train y 22.261 test), sin modificar ningún campo anterior. construction_type conserva t o w. El índice activo sigue en D38; la candidata está aislada y no se atribuye aprobación humana de activación. Los 2.073 CAP01, los 1.454 pendientes y todos los originales mantienen sus valores. Pasaron 100 comprobaciones específicas y ocho de lógica del informe con DOM mínimo; ambas figuras se inspeccionaron. No hubo navegador verificado, revisión independiente, entrenamiento ni efecto sobre tarifa medido. Consultar {decision} y construction_review en el estado. El significado físico y las otras limitaciones del proyecto siguen abiertos.
''', encoding='utf-8')
    statepath = root / 'Preparación/ESTADO_PROYECTO.json'
    state = json.loads(statepath.read_text(encoding='utf-8'))
    state['construction_review'] = {
        'decision_id':decision, 'status':'review_verified_operational_alias_recommended_candidate_not_active',
        'run':rel, 'report':rel+'/informe.html', 'reproduction':'../Hackaton/Semana 1/Revision_construccion/README.md',
        'candidate_catalog':rel+'/candidate/dataset_catalog.json', 'rule':'CON01', 'map':a.MAP,
        'new_field':a.FIELD, 'source_field_preserved':True, 'preexisting_cells_changed':0,
        'construction_material_confirmed':False, 'timber_label_applied':False,
        'mapping_inputs':'Training X 2021-2024 only', 'test_X_used_to_learn_map':False,
        'mapping_availability_reference':'2024-12-31', 'historical_backtest_limit':'Do not claim map known before 2023 without prior source; declare validation-X schema adaptation.',
        'boundary_pairs':149887, 'distinct_t_to_w_policies':18218, 'same_address_train_transitions':449658,
        'same_address_transitions_with_test':599769, 'addresses':292112, 'post_merge_contradictions':0,
        'nested_address_histories_are_not_independent_evidence':True,
        'candidate_grouped_rows':107817, 'candidate_train_grouped_rows':85556, 'candidate_test_grouped_rows':22261,
        'technical_checks':100, 'report_logic_checks':8, 'verification':rel+'/verification.json',
        'closure':'../'+closure.relative_to(root).as_posix(),
        'originals_modified':False, 'historical_runs_modified':False, 'active_dataset_modified':False,
        'capital_changes_inherited':2073, 'pending_capitals_unchanged':1454,
        'two_figures_visually_inspected':True, 'browser_rendering_verified':False,
        'human_activation_review':'pending; detailed comparison requested, no activation approval claimed',
        'independent_validation':False, 'models_trained':False, 'tariff_effect_estimated':False}
    state['data_refinement']['followup_construction_review_decision'] = decision
    a.c.dump(statepath,state)
    routespath = root / 'RUTAS_PROYECTO.json'
    routes = json.loads(routespath.read_text(encoding='utf-8'))
    routes['week_1_construction_review_index'] = 'Hackaton/Semana 1/Revision_construccion/current_run.json'
    a.c.dump(routespath,routes)
    week = root / 'Hackaton/Semana 1/README.md'
    week.write_text(week.read_text(encoding='utf-8') + '\n\nLa [revisión longitudinal de construcción T/W](Revision_construccion/README.md) respalda una clase común de código, sin confirmar el material físico. Su informe compara continuidades y mudanzas; añade una copia candidata con construction_type_harmonized, conservando los códigos anteriores. La candidata permanece fuera del catálogo activo de limpieza.\n',encoding='utf-8')
    for path in docs:
        dest = closure / 'after' / path
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(root / path,dest)
    integration = []
    def check(name, value):
        integration.append({'name':name,'passed':bool(value)})
        assert value,name
    check('immutable_review_manifest_still_identical', a.c.digest(out / 'manifest.json') == manifest_hash and all(a.c.digest(out / e['path']) == e['sha256'] for e in manifest['files']))
    check('active_prepared_index_still_identical', a.c.digest(root / 'Hackaton/Semana 1/Limpieza/current_dataset.json') == a.c.digest(out / 'evidence/active_dataset_before.json'))
    check('candidate_never_published_in_active_index', 'Revision_construccion' not in (root / 'Hackaton/Semana 1/Limpieza/current_dataset.json').read_text(encoding='utf-8'))
    check('state_preserves_all_preexisting_top_level_fields', set(json.loads((closure / 'before/Preparación/ESTADO_PROYECTO.json').read_text(encoding='utf-8'))).issubset(state))
    check('state_paths_resolve', all((root / 'Preparación' / state['construction_review'][key]).exists() for key in ['run','report','reproduction','candidate_catalog','verification','closure']))
    check('route_index_and_report_resolve', (root / routes['week_1_construction_review_index']).is_file() and (root / pointer['report_workspace_relative']).is_file())
    check('decision_unique_and_referenced', len(re.findall(r'^### '+decision+r',', decisions.read_text(encoding='utf-8'),flags=re.M)) == 1
          and decision in memory.read_text(encoding='utf-8') and state['construction_review']['decision_id'] == decision)
    check('no_model_protocol_or_active_data_change_in_documentation', a.c.digest(protocol) == protocol_hash
          and state['methodological_plan']['version'] == '1.2' and not state['construction_review']['models_trained'])
    check('report_logic_passed_without_browser_claim', js['passed'] and js['checks_count'] == 8 and not js['real_browser_rendering'])
    a.c.dump(closure / 'integration_verification.json', {'passed':True,'checks_count':len(integration),'checks':integration,
          'decision_id':decision,'review_run':out.relative_to(root).as_posix(),'review_manifest_sha256':manifest_hash,
          'original_data_checks_not_repeated_for_editorial_changes':True,'independent_validation':False})
    closure_manifest = [{'path':p.relative_to(closure).as_posix(),'sha256':a.c.digest(p),'bytes':p.stat().st_size}
                        for p in sorted(closure.rglob('*')) if p.is_file()]
    a.c.dump(closure / 'manifest.json', {'count':len(closure_manifest),'files':closure_manifest})
    print(json.dumps({'decision':decision,'technical_checks':100,'report_checks':8,'integration_checks':len(integration),
        'closure':str(closure),'active_prepared_data_unchanged':True}),flush=True)


if __name__ == '__main__':
    main()
