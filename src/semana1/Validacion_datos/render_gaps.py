"""Informe de cobertura de validación; conserva las incertidumbres y no cambia datos."""
from html import escape
from pathlib import Path
import json
import os

import audit_gaps as a
import pandas as pd
import pyarrow.parquet as pq


def render(out):
    s=json.loads((out/'summary.json').read_text(encoding='utf-8'))
    plan=json.loads((out/'review_controls.json').read_text(encoding='utf-8'))
    fields=json.loads((out/'field_inventory.json').read_text(encoding='utf-8'))
    evidence=json.loads((out/'evidence_index.json').read_text(encoding='utf-8'))
    v=json.loads((out/'verification.json').read_text(encoding='utf-8'))
    def table(f):return f.to_html(index=False,border=0,escape=True,na_rep='Sin dato')
    def external_file(path):return escape(Path(os.path.relpath(a.ROOT/path,out)).as_posix(),quote=True)
    labels={'verificado_con_alcance':'Verificado con alcance limitado','parcial':'Parcial',
        'hallazgo_nuevo':'Hallazgo nuevo por decidir','pendiente_implementacion':'Pendiente de implementación',
        'no_identificable_totalmente':'No identificable por completo con estos archivos',
        'abierto_semantico':'Significado o disponibilidad por resolver','candidato_sin_activar':'Candidata verificada sin activar',
        'pendiente_revision':'Revisión pendiente','no_realizado':'No realizado'}
    n=s['new_screens'];d=n['semantic_duplicate_claims']
    news=pd.DataFrame([
        {'screen':'Siniestros idénticos salvo claim_id','scope':'Todos los 163.150 siniestros','finding':'604 pares / 1.208 filas; 604 filas adicionales hipotéticas','decision':'Revisar antes de congelar T0; no se borró ninguna.'},
        {'screen':'Calendario 2024–2025','scope':'Tres ramos, train y test','finding':'500.245 continuidades con un día sin cobertura; 31-12-2024 ausente','decision':'Aclarar convención; no se extendieron fechas.'},
        {'screen':'Daños propios de autos','scope':'Aceptados asignados por fecha','finding':'4 own_damage fuera de comprehensive (3 TPFT y 1 TPO)','decision':'Revisar producto/peligro; no se descartan pagos.'},
        {'screen':'Daño accidental sin opción','scope':'Aceptados asignados de hogar','finding':'506 edificios + 1.090 contenidos con bandera falsa','decision':'Aclarar alcance básico/opcional antes de imponer exclusiones.'},
        {'screen':'Coste neto sobre capital','scope':'Aceptados asignados de hogar','finding':'8 edificios + 3 contenidos','decision':'Revisar límite, unidad y gastos; no truncar automáticamente.'},
        {'screen':'Cilindrada electric','scope':'99.376 filas de autos 2021–2025','finding':'96.843 positivas; 2.533 ausentes; ninguna informada igual a cero','decision':'Aclarar unidad/equivalencia y aplicabilidad; no sustituir por cero.'},
        {'screen':'Edad implícita al licenciarse','scope':'Autos 2021–2025','finding':'3.717 filas con edad − años de licencia <16','decision':'Cribado, sin afirmar un mínimo legal ni corregir roles.'}])
    duplicates=pq.read_table(out/'tables/claim_duplicate_candidates.parquet').to_pandas()
    example_groups=duplicates.duplicate_group.unique()[:3]
    duplicate_examples=duplicates[duplicates.duplicate_group.isin(example_groups)].sort_values(['duplicate_group','claim_id'])
    duplicate_examples=duplicate_examples[['duplicate_group','claim_id','policy_id','line','peril','loss_date','report_date','status','paid_to_date','incurred_to_date','recoveries']]
    calendars=pd.read_csv(out/'tables/calendar_summary.csv')
    coverage=pd.read_csv(out/'tables/coverage_screens.csv')
    core = [
        ('Originales y trazabilidad','Once archivos protegidos y bitácoras con hashes; versiones previas conservadas.','No certifica significado, disponibilidad histórica o un objetivo último.'),
        ('Claves y exposición','ID01 y EXP01 comprobados; joins a maestros y aritmética de duración coherentes.','La continuidad del calendario bisiesto requiere VD16.'),
        ('Capitales','2.073 CAP01 congelados y corregidos en derivados; el resto conservado.','Quedan 1.454 casos y su materialidad para modelos.'),
        ('Edades','2.936 edades de tomador recalculadas con DOB como referencia explícita.','No confirma externamente DOB ni identidad del conductor.'),
        ('Construcción','Alias T/W respaldado y candidata verificada.','No está activa y el nombre material sigue sin confirmarse.'),
        ('Siniestros','IDs únicos, fechas coherentes, dominios financieros y asignación diagnóstica comprobados.','IDs únicos no evitan duplicados semánticos; falta T0 operativo con conciliación.'),
        ('Faltantes y perfiles','242 ocurrencias de campo, 105 nombres; telemática ausente equivale exactamente a no optar.','No demuestra aleatoriedad de faltantes ni fecha del score.'),
        ('Validación temporal','Diseño V22/V23/V24, entidades conocidas/nuevas y límites de valoración documentados.','Particiones, transformadores y matriz de disponibilidad aún no están materializados.')]
    sections=[
        '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>Validación de datos: pendientes, evidencia y criterios de cierre</title>',
        '<style>body{font:16px/1.6 system-ui;color:#1b3344;background:#fafcfd;max-width:1350px;margin:36px auto;padding:0 24px}h1{line-height:1.2}h2{margin-top:2.2em}a{color:#08638d}table{border-collapse:collapse;display:block;overflow:auto;max-width:100%;font-size:13px;background:white}th,td{padding:9px 12px;border-bottom:1px solid #dce5ea;vertical-align:top;text-align:left}th{background:#e8f0f4}td{min-width:90px}td p{margin:.25em 0}.lead{background:#e8f4f1;border-left:5px solid #0c7e76;padding:16px 24px}.finding{background:#fff2db;border-left:5px solid #b87710;padding:16px 24px}code{background:#edf1f4;padding:1px 4px}input,select{font:inherit;padding:8px;margin:4px 8px 12px 0;max-width:100%}input{width:400px}.control td:nth-child(5){min-width:430px}.field td:nth-child(3){min-width:350px}details{margin:.5em 0}summary{cursor:pointer;font-weight:600}.muted{color:#526775}li{margin:.6em 0}</style></head><body>',
        '<h1>Qué validación de datos falta</h1>',
        '<div class="lead"><p>La integridad estructural tiene evidencia amplia. Quedan decisiones que afectan directamente el coste objetivo y qué información podemos usar al predecir. Esta revisión añade 58 controles/decisiones con estado, trabajo restante y criterio de cierre, más un inventario de los 105 nombres de columna y sus 242 apariciones.</p>',
        '<p>Se hicieron sondeos dirigidos nuevos y se revisó la evidencia anterior. No se corrigieron valores, eliminaron siniestros, activó CON01, construyó T0 o entrenaron modelos. Los sondeos señalan casos de revisión; no son autorización de reparación ni aprobación de toda la base.</p></div>',
        '<p>Fuente efectiva: catálogo D38, '+escape(s['active_dataset']['workspace_relative_run'])+'. D39 sigue siendo una candidata aislada. Se comprueba la integridad de los archivos usados y se distingue cada evidencia histórica de los controles ejecutados ahora.</p>',
        '<h2>Hallazgos nuevos con efecto potencial en los siguientes pasos</h2>',table(news),
        '<p>Los conjuntos pueden solaparse y no se suman como si fueran personas o errores independientes. Los conteos de coberturas conservan las filas de siniestros tal como están, incluidos posibles duplicados. El fichero de detalle registra el solapamiento.</p>',
        '<h2>Duplicados de contenido que la clave única no detectaba</h2>',
        '<p>604 grupos de dos siniestros coinciden en todos los campos salvo claim_id, incluidos reparador y tercero, cuando constan. Hay 1.208 filas implicadas. Si se confirmara que debe conservarse una por grupo, serían 604 filas adicionales: 598 aceptadas y seis rechazadas. Es una sensibilidad, no una eliminación aplicada ni prueba definitiva de que dos expedientes sean un único evento.</p>',
        '<p>El incurrido neto aceptado de una fila adicional por par suma '+d['hypothetical_net_reduction_all_reported_CU']+' CU en todo el fichero. Para los periodos observados asignables son '+d['hypothetical_net_reduction_assigned_current_periods_CU']+' CU; fuera de la historia actual, '+d['hypothetical_net_reduction_outside_history_CU']+' CU. Son importes observados a diciembre de 2024, no pérdida última. No se deben restar del objetivo hasta decidir el tratamiento.</p>',
        table(duplicate_examples),
        '<p>La coincidencia se verificó tanto con duplicación de filas como con un contador de tuplas independiente que trata explícitamente los nulos. claim_id sigue siendo único. Los pares completos y su pertenencia al periodo se conservan en <a href="tables/claim_duplicate_candidates.csv">CSV</a> y <a href="tables/claim_duplicate_candidates.parquet">Parquet</a>.</p>',
        '<h2>La exposición coincide con las fechas; las fechas no cubren todo el calendario</h2>',table(calendars),
        '<p>Los periodos que continúan de 2024 a 2025 terminan el 30 de diciembre y recomienzan el 1 de enero: falta un día. No existe una fila de póliza que cubra el 31-12-2024, y no hay siniestros ocurridos en esa fecha. La ausencia de siniestros allí no confirma que la omisión sea correcta: puede compartir el mismo supuesto del generador. Debemos aclarar la convención y documentar su efecto.</p>',
        '<p>EXP01 sigue siendo aritméticamente coherente con las fechas originales. Cambiar esas fechas sería una decisión distinta. No se añaden cobertura, exposición ni siniestros por inferencia. <a href="tables/calendar_gap_examples.csv">Ejemplos</a> y <a href="tables/calendar_gaps.parquet">todos los huecos</a>.</p>',
        '<h2>Cobertura, límite y coherencia del objeto asegurado</h2>',table(coverage),
        '<p>Los cuatro daños propios de autos y los 1.596 daños accidentales con opción falsa exigen revisar el alcance contractual. Un código de peligro puede incluir componentes distintos de la opción; tampoco sabemos todavía si hay errores en el indicador o en la clasificación. No se eliminan costes ni se imponen ceros solo por una lectura estándar del nombre.</p>',
        '<p>Los once siniestros cuyo neto supera el capital requieren revisión individual. Una suma anual superior al capital no sería por sí sola la misma anomalía, pues puede reunir varios eventos. Aquí el sondeo compara cada siniestro con el capital del periodo vigente y conserva cualquier posible excepción de gastos/límites o escala.</p>',
        '<p>En autos, todos los eléctricos con engine_size_cc informado tienen cilindrada positiva. Antes de explicar el modelo como si esa cifra fuera cilindrada física, hay que aclarar si es un equivalente o un error. Los 3.717 casos de edad implícita de licencia inferior a 16 son otro cribado: no asumimos una jurisdicción o una edad legal mínima. El conductor principal puede ser distinto del tomador.</p>',
        '<h2>Qué comprobaciones ya tenemos y qué no acreditan</h2>',table(pd.DataFrame(core,columns=['Bloque','Evidencia disponible','Límite pendiente'])),
        f'<p>D38 recorrió {s["profiled_rows"]:,} filas en once tablas y registró {s["existing_quality_checks"]} controles, {s["existing_strict_checks"]} estrictos sin fallo. Los perfiles no se convierten en un porcentaje de calidad: los controles se repiten entre tablas y miden aspectos diferentes. El nuevo código supera {v["checks_count"]} comprobaciones de coherencia de los sondeos y del inventario; no significa haber cerrado los 58 asuntos de la matriz.</p>',
        '<h2>Orden de trabajo y criterios para avanzar</h2>',
        '<ol><li>Fijar el libro de siniestros que alimentará T0: resolver o versionar la decisión de duplicados, conservar los 414 anteriores a la historia y conciliar conteos, pagos, reservas, recuperaciones y excluidos. Cada periodo debe quedar una sola vez, incluidos los ceros.</li>',
        '<li>Documentar los supuestos de calendario y cobertura. Los casos dudosos pueden conservarse en un escenario explícito mientras se investiga su fuente; no deben desaparecer silenciosamente del objetivo.</li>',
        '<li>Construir F0 con contrato de disponibilidad por campo. Excluir bloques temporales dudosos es una forma válida de cerrar un bloqueo para el piloto: no hace falta inventar timestamps o esperar a conocerlo todo.</li>',
        '<li>Guardar V22/V23/V24 y sus roles antes de ajustar modelos; los imputadores, agrupaciones, encoders y calibración deben aprenderse en su parte de entrenamiento. Los costes tienen valoración posterior y esa limitación debe acompañar los resultados.</li>',
        '<li>Iniciar una referencia T0 solo después de esas verificaciones. No exige un último perfectamente identificado, todos los 58 asuntos cerrados o una revisión independiente inexistente; exige un alcance honesto y reproducible.</li>',
        '<li>Antes de seleccionar para 2025, medir sensibilidad a reservas, reporte, recuperaciones, tendencia, extremos, capitales y campos dudosos; mantener la etiqueta de evaluación fija al comparar algoritmos. Revisar soporte y entidades nuevas.</li>',
        '<li>Antes de entregar, verificar predicciones en CU por periodo, dominio finito/no negativo según scorer, una fila por cada uno de los 626.639 IDs y versión exacta de datos/código. No se ha hecho una entrega real en esta revisión.</li></ol>',
        '<p>P0 indica una decisión que no puede quedar silenciosa al construir el objetivo, las variables o la evaluación. Puede cerrarse con evidencia, con exclusión justificada del bloque dudoso o con un escenario de alcance limitado. P1 agrupa revisiones y sensibilidades que deben priorizarse por materialidad. Estas prioridades son del proyecto, no pesos impuestos por IAA.</p>',
        '<h2>Matriz completa de controles y decisiones</h2>',
        '<p>Buscar por campo, ramo, problema o ID. Los criterios de cierre son requisitos propuestos, no controles ya superados.</p>',
        '<input id="search" aria-label="Buscar controles" placeholder="Buscar: NCB, clima, T0, duplicados…"><select id="priority" aria-label="Prioridad"><option value="">Todas las prioridades</option><option>P0</option><option>P1</option></select><select id="status" aria-label="Estado"><option value="">Todos los estados</option>'+''.join('<option value="'+escape(k)+'">'+escape(val)+'</option>' for k,val in labels.items())+'</select><span id="count"></span>',
        '<table id="controls"><thead><tr><th>ID</th><th>Área</th><th>Prioridad</th><th>Estado</th><th>Evidencia, trabajo restante y cierre</th><th>Campos</th></tr></thead><tbody>']
    for r in plan:
        sections.append('<tr class="control" id="'+r['id']+'" data-priority="'+r['priority']+'" data-status="'+r['status']+'"><td>'+r['id']+'</td><td>'+escape(r['area'])+'</td><td>'+r['priority']+'</td><td>'+escape(labels[r['status']])+'</td><td><p>'+escape(r['title'])+'</p><details><summary>Evidencia disponible</summary><p>'+escape(r['known'])+'</p></details><p>Falta: '+escape(r['remaining_work'])+'</p><p>Cierre: '+escape(r['closure_criterion'])+'</p></td><td>'+escape(' '.join(r['columns']))+'</td></tr>')
    sections.extend(['</tbody></table>',
        '<p><a href="review_controls.csv">Matriz CSV</a> · <a href="review_controls.json">Matriz JSON</a>. “Verificado con alcance limitado” conserva supuestos y mantenimiento del contrato; no equivale a aprobar una base final para modelar.</p>',
        '<h2>Inventario de los 105 nombres de columna</h2>',
        '<p>Incluye cada una de sus apariciones en las once tablas. Se hereda el perfil D38; los controles listados por sufijo solo identifican reglas directas del campo. Las relaciones y la disponibilidad deben comprobarse mediante los IDs de revisión. Los IDs generales VD01, VD02, VD18, VD29 y VD42 aplican a todo el inventario. La columna candidata de CON01 no pertenece todavía al esquema activo.</p>',
        '<input id="fieldsearch" aria-label="Buscar columna" placeholder="Buscar una columna o tabla"><table id="fields"><thead><tr><th>Campo</th><th>Tablas</th><th>Significado y perfil</th><th>Revisión pendiente o de alcance</th></tr></thead><tbody>'])
    for r in fields:
        occurrences='; '.join(x['table']+': '+str(x['rows'])+' filas, '+str(x['missing'])+' ausentes, '+x['dtype'] for x in r['occurrences'])
        refs=' '.join('<a href="#'+ref+'">'+ref+'</a>' for ref in r['review_control_ids'])
        sections.append('<tr class="field"><td><code>'+escape(r['column'])+'</code></td><td>'+escape(', '.join(r['tables']))+'</td><td>'+escape(r['meaning'])+'<details><summary>Perfil y reglas directas</summary><p>'+escape(occurrences)+'</p><p>'+escape(', '.join(r['existing_direct_rule_names']) or 'Perfil disponible; ninguna regla directa identificada por sufijo.')+'</p></details></td><td>'+refs+'</td></tr>')
    sections.extend(['</tbody></table><p><a href="field_inventory.csv">Inventario CSV</a> · <a href="field_inventory.json">Inventario completo con ocurrencias JSON</a>.</p>',
        '<h2>Carencias que estos archivos no pueden resolver por sí solos</h2>',
        '<p>No hay trayectorias de pago/reserva/estado ni verdad última de cada siniestro. Tampoco hay snapshots anuales de maestros, timestamps del score telemático, coordenadas, identidad explícita de vehículo/conductor o confirmación del generador para todos los códigos y unidades. Podemos limitar variables, declarar supuestos y medir sensibilidad. Una segunda llamada a IA no añade la información ausente.</p>',
        '<p>No afirmar validación independiente: los scripts y la revisión son propios asistidos por IA. Una reproducción por otra persona o entorno y la revisión competente siguen pendientes. La revisión no envió datos a proveedores, no añadió fondos y no contactó terceros. No hay prueba de que una corrección pendiente mejore el score.</p>',
        '<h2>Evidencia y reproducción</h2>',
        '<p>Desde C:/dev/Hakaton: <code>Preparación/.venv/Scripts/python.exe "Hackaton/Semana 1/Validacion_datos/audit_gaps.py"</code>. Crea una corrida nueva y no altera sus entradas. El inventario, los casos, las fuentes y el código quedan identificados por hash. Consultar <a href="verification.json">comprobaciones del sondeo</a>, <a href="summary.json">resumen</a>, <a href="evidence_index.json">procedencia</a> y <a href="review_controls.json">criterios completos</a>.</p>',
        '<ul>'+''.join('<li><a href="'+external_file(e['workspace_relative_path'])+'">'+escape(key)+'</a>, SHA-256 '+e['sha256']+'</li>' for key,e in evidence.items())+'</ul>',
        '<p>IAA Documentación §2 y §§4–6 respalda el recorrido de datos y el registro de limitaciones; Gobernanza §2.8 distingue revisión propia e independiente; Consideraciones profesionales §§3.1–3.3 y §§3.5–3.6 orienta propósito, comprensión y responsabilidad humana. Son referencias educativas, no certificación ni mínimos legales de licencia.</p>',
        '''<script>const search=document.getElementById('search'), priority=document.getElementById('priority'), status=document.getElementById('status');const controls=Array.from(document.querySelectorAll('#controls tbody tr'));function filter(){let visible=0;const query=search.value.toLocaleLowerCase('es');for(const row of controls){const ok=row.textContent.toLocaleLowerCase('es').includes(query)&&(!priority.value||row.dataset.priority===priority.value)&&(!status.value||row.dataset.status===status.value);row.hidden=!ok;if(ok)visible++;}document.getElementById('count').textContent=visible+' de '+controls.length+' controles';}for(const input of [search,priority,status])input.addEventListener('input',filter);filter();const fieldsearch=document.getElementById('fieldsearch');const fields=Array.from(document.querySelectorAll('#fields tbody tr'));fieldsearch.addEventListener('input',()=>{const q=fieldsearch.value.toLocaleLowerCase('es');for(const row of fields)row.hidden=!row.textContent.toLocaleLowerCase('es').includes(q);});</script></body></html>'''])
    (out/'informe.html').write_text('\n'.join(sections),encoding='utf-8')
