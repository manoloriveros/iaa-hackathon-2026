"""Cierra el dossier y actualiza navegación/memoria sin alterar datos ni reglas."""
from datetime import datetime,timezone,timedelta
from pathlib import Path
import json
import re
import shutil
import sys
import collect_documentation as a
import clean_data as c
import correct_capitals as cap


def main(out):
    assert not (out/'manifest.json').exists()
    v=a.readj(out/'documentation_verification.json');f=a.readj(out/'facts.json');protected=a.readj(out/'protected_data_hashes.json')
    assert v['failed']==0 and v['main_sections']==20 and v['dictionary_fields']==107 and v['validation_controls']==58
    assert all(c.digest(out/path)==sha for path,sha in v['verified_files'].items())
    assert all(c.digest(c.ROOT/path)==sha for path,sha in protected.items())
    now=datetime.now(timezone.utc);rel=out.relative_to(c.ROOT).as_posix();short=out.relative_to(a.BASE).as_posix()
    close=a.BASE/'closures'/now.strftime('closure_%Y%m%dT%H%M%SZ');close.mkdir(parents=True,exist_ok=False)
    paths={name:c.ROOT/'Preparación'/name for name in ['ESTADO_PROYECTO.json','MEMORIA_PROYECTO.md','DECISIONES.md']}
    paths.update({'RUTAS_PROYECTO.json':c.ROOT/'RUTAS_PROYECTO.json','week_README.md':a.WEEK/'README.md',
        'cleaning_README.md':c.BASE/'README.md','refinement.md':c.BASE/'REFINAMIENTO.md','capital_rules.md':c.BASE/'CAPITALES.md',
        'model_README.md':a.WEEK/'Modelado/README.md'})
    for name,path in paths.items():shutil.copy2(path,close/('before_'+name))
    state=a.readj(paths['ESTADO_PROYECTO.json']);routes=a.readj(paths['RUTAS_PROYECTO.json']);memory=paths['MEMORIA_PROYECTO.md'].read_text('utf-8');decisions=paths['DECISIONES.md'].read_text('utf-8')
    decision='D'+str(max(map(int,re.findall(r'\bD(\d+)\b',decisions)))+1)
    for name in ['collect_documentation.py','write_dossier.py','verify_documentation.py','record_documentation.py']:
        dest=out/'source_snapshot'/name
        if dest.exists():assert c.digest(dest)==c.digest(a.BASE/name)
        else:shutil.copy2(a.BASE/name,dest)
    c.dump(out/'browser_preview_limit.json',{'action':'Automatic local HTML preview through Browser Use','status':'blocked_by_browser_security_policy',
        'reason':'Requested file:// protocol not allowed; tool allows http/https only. No alternate browser surface, server or workaround used.',
        'safe_checks_completed':['File/hash/metadata/ledger reconciliation','HTML structure and local links','Exact shipped search callback in minimal in-memory DOM','PNG chart inspected with view_image'],
        'real_browser_rendering_verified':False})
    c.dump(out/'figure_inspection.json',{'status':'inspected_by_Codex_with_view_image','file':'figures/capitales_y_pendientes.png',
        'sha256':c.digest(out/'figures/capitales_y_pendientes.png'),'finding':'Both panels legible; stacked capital groups sum3527 at every step; remaining counts1454/587/576/467/421/419 and six residual-group labels match source. Not a browser preview or independent review.'})
    draft=a.BASE/'runs/dossier_20261017T012556Z_59c4ed56'
    assert cap.manifest_ok(draft)
    c.dump(out/'draft_provenance.json',{'workspace_relative_draft':draft.relative_to(c.ROOT).as_posix(),
        'status':'closed_incomplete_document_draft_no_data_changes','manifest_sha256':c.digest(draft/'manifest.json'),
        'reason':'Initial source registration omitted report_workspace_relative-style reports. Collector now supports both report path styles. Finished dossier regenerated from a fresh capture; no data changes.'})
    record={'decision_id':decision,'version':'1.0','source_data_cut_decision':'D61','workspace_relative_run':rel,
        'created_utc':now.isoformat(),'status':'verified_documentation_only_no_data_changes',
        'report_workspace_relative':rel+'/informe.html','markdown_workspace_relative':rel+'/DOCUMENTACION_DATOS.md',
        'dictionary_workspace_relative':rel+'/diccionario.html','validation_register_workspace_relative':rel+'/validaciones.html',
        'source_register_workspace_relative':rel+'/source_register.json','facts_workspace_relative':rel+'/facts.json',
        'verification_workspace_relative':rel+'/documentation_verification.json','main_sections':20,'dictionary_fields':107,'validation_controls':58,
        'original_fields':105,'derived_audit_fields':2,'source_entries':199,'unique_source_files':168,
        'own_documentary_checks':v['passed'],'minimal_DOM_logic_checks':224,'real_browser_rendering_verified':False,
        'browser_preview_limit':'Browser Use policy disallowed file://; no workaround attempted.',
        'base_index_unchanged':'Hackaton/Semana 1/Limpieza/current_dataset.json','retrospective_index_unchanged':'Hackaton/Semana 1/Limpieza/current_retrospective_dataset.json',
        'retrospective_rule':'CAP06R','retrospective_pending':419,'base_pending':1454,'total_corrected_capitals':3108,'retrospective_corrected_capitals':1035,
        'retrospective_test2025_anchors':136,'pending_test_rows_retrospective':177,'pending_test_rows_base':190,
        'AGE01_explained_D59':2934,'AGE01_unexplained_D59':2,'D59_scope_retrospective':'CAP05R, not CAP06R',
        'protocol_version_unchanged':'1.10','guard_contacts_gap_preserved':True,'originals_modified':False,'derived_data_modified':False,
        'dataset_indexes_modified':False,'historical_closed_runs_modified':False,'models_trained':False,'independent_validation':False,
        'closure_workspace_relative':close.relative_to(c.ROOT).as_posix()}
    c.dump(out/'closure_record.json',record)
    c.dump(out/'manifest.json',{'created_utc':now.isoformat(),'type':'immutable_consolidated_data_documentation','files':[
        {'path':p.relative_to(out).as_posix(),'sha256':c.digest(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()]})
    index=a.BASE/'current_run.json';assert not index.exists();c.dump(index,record)
    entry=f'''# Documentación de los datos de la primera semana

La guía consolidada recoge el trabajo con los datos hasta D61, CAP06R y protocolo1.10. [Leer el dossier]({short}/informe.html) o [abrir la versión editable]({short}/DOCUMENTACION_DATOS.md).

Incluye fuentes, once tablas, relaciones, diccionario de107 campos, reglas y motivos, linaje de las dos ramas, casos, verificaciones, uso de IA y58 controles de seguimiento. [Diccionario consultable]({short}/diccionario.html) · [Validaciones y pendientes]({short}/validaciones.html) · [Registro de fuentes]({short}/fuentes.html).

La base conserva1.454 capitales pendientes; la rama retrospectiva CAP06R conserva419 y3.108 correcciones acumuladas,1.035 de ellas retrospectivas. Los originales y los índices de datos permanecen intactos. El dossier es una fotografía de documentación, no otra capa de datos ni aprobación para modelar. D59 cubre CAP05R; AGE01 fija una convención de edad y su evidencia deja dos diferencias sin explicar.

[current_run.json](current_run.json) identifica esta versión. Los datos se consumen por los índices de Limpieza, no por este índice documental. Las fuentes mutables se copiaron antes de actualizar memoria. El gráfico se inspeccionó como imagen; la vista automatizada HTML fue bloqueada por política de file://. La estructura, enlaces y lógica de búsqueda tienen controles propios.

Para crear otra fotografía sin transformar datos, ejecutar collect_documentation.py, pasar la carpeta generada a write_dossier.py y verify_documentation.py y revisar el contenido antes de un nuevo cierre. Los recolectores actuales fijan el corte CAP06R y las reglas documentadas: adaptar y versionar el corte si avanzan los datos. No ejecutar record_documentation.py sobre una corrida cerrada o reutilizar el índice de esta versión para sobrescribirla.
'''
    # New navigation entry is documentation, not a closed historical artifact.
    readme=a.BASE/'README.md';assert not readme.exists();readme.write_text(entry.replace('protocolo1.10','protocolo 1.10').replace('de107','de 107').replace('y58','y 58').replace('conserva1.454','conserva 1.454').replace('conserva419','conserva 419').replace('y3.108','y 3.108').replace('acumuladas,1.035','acumuladas, 1.035'),encoding='utf-8')
    week=f'''# Datos y documentación de la primera semana

La [documentación consolidada](Documentacion_datos/README.md) explica todo el recorrido de los datos hasta D61. Incluye [dossier de lectura](Documentacion_datos/{short}/informe.html), [versión editable](Documentacion_datos/{short}/DOCUMENTACION_DATOS.md), [diccionario de107 campos](Documentacion_datos/{short}/diccionario.html), [58 controles de seguimiento](Documentacion_datos/{short}/validaciones.html) y fuentes con hashes.

## Entradas vigentes

Los once Parquet originales están en Datos, y la descarga/ZIP se conservan en Preparación/data/raw/iaa_2026_part1_20261016. Las rutas se resuelven con [RUTAS_PROYECTO.json](../../RUTAS_PROYECTO.json) desde C:/dev/Hakaton. No se reescriben originales o corridas cerradas.

| Entrada | Contenido | Pendientes de capital |
| --- | --- | --- |
| [Base preparada](Limpieza/current_dataset.json) | ID01, EXP01, CAP01, CAT01, AGE01, DUP01, REN00 y PRE00 | 1.454 |
| [Rama retrospectiva](Limpieza/current_retrospective_dataset.json) | Base más CAP02R a CAP06R;3.108 capitales corregidos totales | 419 |

Los índices de datos apuntan a catálogos con rutas y SHA256. Los demás current_* identifican operaciones o revisiones concretas. La rama retrospectiva no está aprobada para backtests causales; ninguna entrada marca aprobación completa para modelar. Protocolo1.10; T0/F0 y particiones operativas siguen pendientes.

## Evidencia por tema

| Tema | Referencia |
| --- | --- |
| Contrato archivado del reto | [Reglas](../REGLAS_2026.md) |
| EDA y diccionario inicial D30 | [Análisis de originales](Analisis/README.md) |
| Claves, exposición y catálogo base | [Limpieza](Limpieza/README.md) |
| Capitales y bitácoras | [CAP01 e historial posterior](Limpieza/CAPITALES.md) |
| Categorías y definición de edad | [CAT01 y AGE01](Limpieza/REFINAMIENTO.md) |
| Construcción T/W | [Revisión y candidata CON01 fuera de catálogo](Revision_construccion/README.md) |
| Siniestros duplicados | [Revisión](Revision_duplicados/current_run.json) y [DUP01 aplicado](Limpieza/current_duplicate_application.json) |
| Calendario y31-12-2024 | [Revisión con fechas pendientes](Revision_calendario/current_run.json) |
| Rechazos con continuidad | [Revisión](Revision_rechazos/current_run.json) y [REN00 aplicado](Limpieza/current_renewal_audit_application.json) |
| Siniestros anteriores a la primera cobertura observada | [Revisión](Revision_prehistoria/current_run.json) y [PRE00 aplicado](Limpieza/current_prehistory_audit_application.json) |
| Dos ampliaciones y renovaciones | [Revisión D60](Revision_ampliaciones_capital/current_run.json) y [CAP06R aplicado](Limpieza/current_endorsement_capital_correction.json) |
| Riesgos de datos y pendientes | [Auditoría histórica D40](Validacion_datos/current_run.json) y [registro al cierre](Documentacion_datos/{short}/validaciones.html) |
| Jev/TypeSafe | [Evaluación sin financiación ni decisiones recibidas](Validacion_IA/jev_20261016/evaluacion.html) |
| Objetivo, predictores y validación | [Metodología](Modelado/METODOLOGIA_ACTUARIAL.md) y [protocolo](Modelado/protocolo_metodologico.json) |
| Investigación D50 de Claude | [Diagnósticos y fuentes](Modelado/Investigacion_tecnicas_claude/INFORME.md) |
| Segunda implementación D59 | [Informe histórico hasta CAP05R](Validacion_ajustes_claude/INFORME.md) y [dashboard bilingüe](Validacion_ajustes_claude/dashboard.html) |

## Cómo interpretar los estados

AGE01 fija edad al inicio de cobertura; no demuestra que todas las edades originales fueran errores. D59 explica2.934 de2.936 diferencias y deja dos sin explicar. CAT01 normaliza caja sin unificar T/W. DUP01 está aplicado a604 pares; los57 grupos no idénticos se conservaron. REN00 y PRE00 son marcas de auditoría, nunca predictores.

D30/D40 usan sus catálogos históricos; D56 reconcilia estados sin repetir todos los controles; D59 es una segunda implementación asistida por IA hasta CAP05R, sin revisión humana independiente. CAP06R tiene su propia verificación posterior. customer_service_contacts debe excluirse antes de entrenar y aún pasa el guard1.0. No se consideran cerradas las brechas por documentarlas.
'''
    # Keep technical names untouched while improving ordinary prose spacing.
    from write_dossier import clean_prose
    paths['week_README.md'].write_text(clean_prose(week),encoding='utf-8')
    oldclean=paths['cleaning_README.md'].read_text('utf-8');rest=oldclean.split('Los originales permanecen',1)
    assert len(rest)==2
    intro=f'''# Preparación y auditoría de los datos

La [guía consolidada](../Documentacion_datos/README.md) reúne reglas, motivos, bitácoras, verificaciones y pendientes hasta D61. La base vigente se lee con [current_dataset.json](current_dataset.json): ID01/EXP01/CAP01/CAT01/AGE01/DUP01/REN00/PRE00 y1.454 capitales pendientes. La rama [current_retrospective_dataset.json](current_retrospective_dataset.json) añade CAP02R a CAP06R, con419 pendientes y3.108 correcciones acumuladas,1.035 retrospectivas. No está aprobada para backtests causales.

current_run.json conserva D32 y los otros índices de operación identifican sus propias aplicaciones. Las descripciones y comandos siguientes corresponden al procedimiento histórico de cada operación; no deben usarse para sustituir el puntero vigente por una capa anterior. Los informes cerrados se conservan. D59 cubre hasta CAP05R; no acredita CAP06R ni una auditoría humana independiente.

## Procedimiento histórico de identificadores y exposición

Los originales permanecen'''
    paths['cleaning_README.md'].write_text(clean_prose(intro)+rest[1],encoding='utf-8')
    captext=paths['capital_rules.md'].read_text('utf-8');first,restcap=captext.split('\n',1)
    paths['capital_rules.md'].write_text(first+f'''\n\nEl estado consolidado se consulta en [el dossier de datos](../Documentacion_datos/README.md). CAP01 deja1.454 pendientes en la base; la rama retrospectiva ha avanzado a CAP06R y conserva419, con3.108 correcciones totales. Las notas CAP01 siguientes describen esa operación histórica; el índice de su aplicación no es el de la última rama.\n'''+restcap,encoding='utf-8')
    ref=paths['refinement.md'].read_text('utf-8');needle='No se rellenan nulos ni se recortan NCB'
    assert needle in ref
    correction='''La revisión posterior D59 interpreta AGE01 como fijación de una convención común, no como2.936 errores de captura:2.432 diferencias coinciden con edad a cotización,457 con cumpleaños en el inicio y45 con edad al final. Suman2.934; dos no quedaron explicadas en esa revisión. Los valores anteriores se conservan. El [dossier consolidado](../Documentacion_datos/README.md) distingue ese alcance de la verificación de la fórmula.\n\n'''
    paths['refinement.md'].write_text(ref.replace(needle,clean_prose(correction)+needle,1),encoding='utf-8')
    model=paths['model_README.md'].read_text('utf-8');first,body=model.split('\n',1)
    paths['model_README.md'].write_text(first+f'''\n\nAntes de preparar el conjunto para modelos, consultar la [documentación consolidada de datos](../Documentacion_datos/README.md): base con1.454 capitales pendientes, rama CAP06R con419, y brecha de exclusión de customer_service_contacts todavía abierta. El protocolo1.10 conserva alcance retrospectivo; documentar las transformaciones no implementa T0/F0 o aprueba entrenamiento.\n'''+body,encoding='utf-8')
    # These are current mutable guides, so update wording and spacing without altering closed runs.
    for name in ['capital_rules.md','model_README.md']:
        paths[name].write_text(clean_prose(paths[name].read_text('utf-8')),encoding='utf-8')
    state['data_documentation']=record;state['memory_as_of']=now.isoformat()
    old_catalog=state['competition_data'].get('active_prepared_catalog')
    state['competition_data']['active_prepared_catalog']='../'+f['base_catalog_workspace_relative']
    state['competition_data']['active_retrospective_index']='../Hackaton/Semana 1/Limpieza/current_retrospective_dataset.json'
    state['competition_data']['active_retrospective_catalog']='../'+f['retrospective_catalog_workspace_relative']
    state['competition_data']['current_documentation_decision']=decision
    routes['week_1_data_documentation_index']='Hackaton/Semana 1/Documentacion_datos/current_run.json'
    routes['week_1_data_documentation']='Hackaton/Semana 1/Documentacion_datos'
    c.dump(paths['ESTADO_PROYECTO.json'],state);c.dump(paths['RUTAS_PROYECTO.json'],routes)
    localdate=now.astimezone(timezone(timedelta(hours=-5))).strftime('%Y-%m-%d')
    note=f'''\n\n{decision}, documentación consolidada de datos hasta D61: [dossier](../{rel}/informe.html), [versión editable](../{rel}/DOCUMENTACION_DATOS.md), [diccionario107](../{rel}/diccionario.html) y [58 controles](../{rel}/validaciones.html). Registra20 secciones,199 entradas de procedencia sobre168 archivos,13 reglas aplicadas y el linaje base/retrospectivo. Base:1.454 capitales pendientes; CAP06R:419 pendientes,3.108 correcciones acumuladas y1.035 retrospectivas;136 anclas test posteriores,177 test pendientes en la rama y190 en base. AGE01 es cambio de definición: D59 explica2.934 y deja dos de2.936 diferencias sin explicar. D59 cubre CAP05R, no CAP06R. Se actualizan guías de entrada y el campo active_prepared_catalog del estado para que coincida con el índice base PRE00, sin mover ese índice. Protocolo1.10 y guard de contactos sin cambios; T0/F0 pendientes. {v['passed']} controles propios documentales y224 de lógica del buscador. Gráfico inspeccionado; previsualización HTML automatizada bloqueada por política file://, sin intento alternativo. Ningún dato, catálogo o corrida cerrada cambia. Ver data_documentation.\n'''
    marker='## Cómo usar esta memoria'
    assert marker in memory
    quick=f'''## Documentación consolidada de datos vigente

La entrada para comprender el recorrido completo de los datos es [Documentacion_datos](../Hackaton/Semana%201/Documentacion_datos/README.md), corte D61 y decisión documental {decision}. Distingue la base con1.454 pendientes de CAP06R con419, conserva el alcance histórico de D59 hasta CAP05R y matiza AGE01 como convención de edad. Contiene dossier editable y HTML, diccionario107, linaje, bitácoras, fuentes y58 controles. No aprueba modelos ni cambia datos.

'''
    paths['MEMORIA_PROYECTO.md'].write_text(memory.replace(marker,clean_prose(quick)+marker,1).rstrip()+clean_prose(note),encoding='utf-8')
    text=f'''\n\n### {decision}, documentación consolidada del trabajo con datos hasta D61, {localdate}, America/Bogota

El participante pidió documentar muy bien todo lo hecho con los datos hasta este punto. La corrida ../{rel} reúne una guía principal editable y HTML con20 secciones, diccionario consultable de107 campos (105 originales y2 marcas), registro de58 controles, decisiones D28–D61, fuentes y hashes, y gráfico de capitales/pendientes. La fotografía identifica CAP06R y protocolo1.10; esta decisión es documental y no crea una capa de datos.

Se concilian199 entradas de procedencia sobre168 archivos, metadatos de11 originales, catálogos base/retrospectivo, listas de capitales y evidencia histórica. Los originales mantienen SHA256 de D28. Se distingue cada regla aplicada de propuestas, marcadores de auditoría y pendientes. Las cifras actuales son3.108 capitales corregidos,1.035 retrospectivos,419 pendientes de rama y1.454 de base;136 anclas posteriores test no equivalen a13 filas test corregidas retrospectivamente. El test pendiente es177 en CAP06R y190 en base. Los58 controles no se vuelven a ejecutar en bloque; sus estados conservan alcance D56 con actualizaciones documentales explícitas.

La síntesis matiza AGE01: fija edad al inicio, y D59 explica2.934 de2.936 diferencias por otras convenciones, con dos sin explicar. La revisión D59 es segunda implementación asistida por IA hasta CAP05R, sin acreditación de auditoría humana independiente o validación de CAP06R. La brecha customer_service_contacts persiste comprobada. Se documentan los datos procesados previamente en nube de Claude según D59, y se distingue Jev: un intento bloqueado, saldo cero, sin fondos añadidos o decisiones de modelo. Las prácticas IAA vinculan ficha/linaje, reproducibilidad y responsabilidad, sin certificar cumplimiento profesional.

Se actualizaron las guías vigentes Semana1/README, Limpieza/README, CAPITALES, REFINAMIENTO y Modelado/README para enlazar la síntesis y separar lectura actual de procedimientos históricos. La memoria tiene entrada visible y cierre; estado y mapa de rutas apuntan al índice documental. Se corrigió únicamente un metadato obsoleto del estado, competition_data.active_prepared_catalog, que apuntaba a DUP01 y ahora coincide con el catálogo base PRE00; se conservó el valor anterior en el cierre. No se cambió current_dataset.json o current_retrospective_dataset.json, ni el protocolo1.10 o código funcional de limpieza/modelado. Los informes cerrados conservan contenido y hashes.

Pasaron {v['passed']} controles propios de documentación, fuentes, cifras, enlaces y estructura, más224 comprobaciones de la lógica real del buscador en DOM mínimo sin navegador/red. El gráfico se inspeccionó mediante view_image. Browser Use rechazó la previsualización file:// por política de protocolos; no se intentó otro navegador, servidor o vía indirecta. El resultado no se declara renderizado en navegador. El primer borrador incompleto quedó cerrado con el motivo de una referencia de informe omitida; la captura final se regeneró con ambos estilos de ruta admitidos. Esta tarea usa pages:write-page para organización y redacción en el repositorio existente, sin crear Page remoto.

La IA consolidó y verificó documentación; la autorización humana de esta solicitud no amplía listas de reparación, entrenamiento, publicaciones o contactos. Sin entrenamiento, proveedor externo nuevo, envío, publicación, automatización o delegación. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan alcance y trazabilidad. Ver data_documentation.
'''
    paths['DECISIONES.md'].write_text(decisions.rstrip()+clean_prose(text),encoding='utf-8')
    after=close/'after';after.mkdir()
    for name,path in paths.items():shutil.copy2(path,after/name)
    shutil.copy2(readme,after/'documentation_README.md')
    assert cap.manifest_ok(out) and all(c.digest(c.ROOT/path)==sha for path,sha in protected.items())
    c.dump(close/'closure.json',{'created_utc':now.isoformat(),'decision_id':decision,'documentation':record,
        'manifest_sha256':c.digest(out/'manifest.json'),'previous_stale_state_catalog':old_catalog,
        'current_state_catalog':state['competition_data']['active_prepared_catalog'],
        'documents':{path.relative_to(c.ROOT).as_posix():c.digest(path) for path in [*paths.values(),index,readme]}})
    print(json.dumps({'decision':decision,'run':str(out),'report':str(out/'informe.html'),'markdown':str(out/'DOCUMENTACION_DATOS.md'),
        'closure':str(close),'status':'verified_documentation_only_no_data_changes'},ensure_ascii=False))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
