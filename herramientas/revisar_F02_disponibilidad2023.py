"""Revisión documental y de esquema, sin leer valores de pólizas o recalcular diagnósticos."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/revision_F02_2023/f02_20261024_v1'
DOC=REPO/'docs/semana2/F02_SEMANTICA_Y_DISPONIBILIDAD_2023.md'
INDEX=REPO/'registro/semana2_F02_disponibilidad2023_actual.json'
SOURCEINDEX=REPO/'registro/semana2_b20_fuentes2023_actual.json'
IDENT='S2-F02-DISPONIBILIDAD2023-v1-20261024';STATEKEY='week_2_F02_temporal_availability2023_v1_20261024'
now=lambda:datetime.now(timezone.utc).isoformat()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
rel=lambda p:p.relative_to(ROOT).as_posix()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def dump(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')

def top(raw,key,value):
    val=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+val+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+val+raw[m.end()+end:]

def main():
    assert RUN.exists() and not INDEX.exists()
    schema=read(RUN/'policy_schema_only.json');columns={x['name']:x['type'] for x in schema['columns']}
    assert read(RUN/'dictionary_receipt.json')['unchanged_from_archive'] is True
    AV=REPO/'privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766/availability_contract.json'
    CODE=REPO/'src/semana2/variables_ultimo.py';RECIPE=REPO/'registro/semana2_glm_ridge_coberturas_plan_v1.json'
    av=read(AV);recipe=read(RECIPE)['recipe']['features_by_line']['buildings']['all']
    fields=[
      {'name':'construction_type','feature':'x_construction_type','meaning':'Material/tipo de construcción; distinto de la tipología de inmueble property_type.',
       'definition_status':'defined','type_expected':'string','earliest_plausible_information':'Declaración técnica anterior a cotización o al inicio del riesgo, si corresponde a la vivienda de ese subperiodo.',
       'temporal_status':'conditional_declared_or_stable_not_timestamped','quote_availability_proven':False,
       'current_transform':'Mapa fijo BRK→brick,STN→stone,WOD→timber,MIX→mixed_or_nonstandard; no se aprende con etiquetas.',
       'missing':'Fecha/versión de declaración y endosos ligados al riesgo; historial de cambios físicos si hubo modificaciones.',
       'decision':'Solo candidato condicional bajo declaración/estabilidad explícita. Codificar correctamente no acredita conocimiento en la cotización.'},
      {'name':'occupancy','feature':'x_occupancy','meaning':'Uso de la vivienda: habitada por propietario o arrendada; no profesión del cliente.',
       'definition_status':'defined','type_expected':'string','earliest_plausible_information':'Declaración de uso vigente para el periodo/endorso y su fecha efectiva.',
       'temporal_status':'conditional_contractual_state_not_timestamped','quote_availability_proven':False,
       'current_transform':'Copia categórica desde la fila de póliza con marca explícita de ausente; no as-of join.',
       'missing':'Declaración fechada y vigencia del uso; no asumir que una situación posterior representa todo2023.',
       'decision':'Candidato condicional al estado contractual conocido. Separarlo de customers.occupation, que es perfil/profesión sin fecha.'},
      {'name':'days_unoccupied','feature':'x_days_unoccupied','meaning':'Duración máxima de desocupación; el diccionario no delimita ventana de referencia o fecha de medición.',
       'definition_status':'measurement_window_unresolved','type_expected':'double','earliest_plausible_information':'Desconocida: depende de si es historial previo declarado, previsión o experiencia realizada.',
       'temporal_status':'hold_for_prospective_use_until_window_and_asof_clarified','quote_availability_proven':False,
       'current_transform':'Copia numérica sin filtro de ventana temporal o sello de captura del campo.',
       'missing':'Ventana exacta,fecha de referencia,captura y carácter declarado/realizado para cada registro2023.',
       'decision':'No dar por disponible prospectivamente bajo la etiqueta F0_contractual. Hay riesgo temporal no resuelto, no fuga demostrada. No recortar a365días/exposición para inventar una ventana.'},
      {'name':'smoke_alarms','feature':'x_smoke_alarms','meaning':'Indicador booleano de alarmas de humo instaladas; no número de alarmas.',
       'definition_status':'defined','type_expected':'bool','earliest_plausible_information':'Declaración o constatación previa del equipamiento, con su fecha de vigencia.',
       'temporal_status':'conditional_physical_state_not_timestamped','quote_availability_proven':False,
       'current_transform':'Indicador convertido al bloque numérico; no fecha de instalación/declaración comprobada.',
       'missing':'Cuestionario/constatación fechada y vigencia del estado; sin inferir que el maestro/fila es histórico.',
       'decision':'Candidato físico condicional. No afirmar ausencia o presencia antes de una cotización solo por su valor en el archivo.'},
      {'name':'voluntary_excess','feature':'x_voluntary_excess','meaning':'Franquicia elegida por el cliente, en CU; el diccionario enumera0,250,500,1000.',
       'definition_status':'defined','type_expected':'int64','earliest_plausible_information':'Término aceptado al contratar; su disponibilidad en una cotización concreta requiere la versión elegida entonces.',
       'temporal_status':'conditional_contract_term_binding_not_quote_attested','quote_availability_proven':False,
       'current_transform':'Importe copiado como predictor numérico; no transformación adicional de T0.',
       'missing':'Propuesta/condición contractual fechada,aceptación y endosos; regla conjunta con la franquicia obligatoria.',
       'decision':'Término contractual condicional, no sello temporal probado. El pago del diccionario ya es neto de franquicia; no descontarla otra vez.'},
      {'name':'compulsory_excess','feature':'x_compulsory_excess','meaning':'Franquicia fijada por la aseguradora, en CU.',
       'definition_status':'defined','type_expected':'int64','earliest_plausible_information':'Término de suscripción aplicable al inicio/endorso; no necesariamente la primera propuesta de precio.',
       'temporal_status':'conditional_contract_term_binding_not_quote_attested','quote_availability_proven':False,
       'current_transform':'Importe copiado como predictor numérico; no as-of join o nueva deducción del objetivo.',
       'missing':'Versión de condiciones y fecha efectiva/captura; regla conjunta/peril sin presumir suma o prioridad.',
       'decision':'Candidato contractual condicional. Conservar T0/C0; no sumar/restar de nuevo las franquicias de un coste ya neto.'}
    ]
    for row in fields:
        row.update(schema_type=columns[row['name']],initial_availability_role=next(x['role'] for x in av['source_fields'] if x['table']=='policies_buildings' and x['column']==row['name']),in_existing_F0=row['feature'] in av['blocks']['buildings']['all'],in_B20=row['feature'] in recipe)
        assert row['schema_type']==row['type_expected'] and row['in_existing_F0'] and not row['in_B20']
    temporal_columns=[x for x in schema['columns'] if 'date' in x['type'] or 'timestamp' in x['type']]
    assert {x['name'] for x in temporal_columns}=={'period_start','period_end'}
    review={'id':IDENT,'author':'Codex','utc':now(),'scope':'F02 semantic/temporal review for proposed2023 use; schema and documents only, no row values or diagnostics.','fields':fields,'explicit_quote_field_in_policy_schema':False,'field_capture_or_version_timestamp_in_policy_schema':False,'typed_temporal_fields':temporal_columns,'quote_date_proxy':'period_start - days_quote_to_inception; convention, not per-field capture evidence','static_code_review':'make_features copies row inputs; no per-field as-of join or capture-time check for these six fields. Constructor/run not executed.','prior_role_is_not_temporal_proof':True,'current_B20_includes_any_of_six':False,'future_default_decision':'No new prospective admission inferred from F0. Five defined fields remain conditional; days_unoccupied on hold until measurement window and temporal provenance clarified.','conditional_row_prediction_is_not_prospective_quote_backtest':True,'existing_feature_contract_modified':False,'old_models_retrained_or_discarded':False,'G1_closed':False,'G2_closed':False,'independent_components_added':0,'new_fits':0,'new_predictions':0,'new_scores':0,'new_numerical_diagnostics':0,'row_values_read':0,'2024_test_rows_read':0,'reference':'W2-B00','all_alternatives_preserved':True,'2024_model_validation_opened':False,'night_window_reopened':False,'professional_independent_validation':False}
    dump(RUN/'temporal_availability_review.json',review)
    paths=[AV,CODE,RECIPE,REPO/'docs/semana2/VARIABLES_Y_ULTIMO.md',ROOT/'Hackaton/Semana 2/Codex/fuentes_variables_ultimo/data_description_response.json',SOURCEINDEX,REPO/'registro/semana2_contenido_oficial_actual.json',REPO/'registro/semana2_desarrollo2023_actual.json',REPO/'registro/semana2_contadores_propios_actual.json',REPO/'registro/semana2_continuidad_nocturna.json']
    sources=[]
    for i,p in enumerate(paths):
        q=RUN/'sources'/f'{i:02d}_{p.name}';q.parent.mkdir(exist_ok=True)
        with q.open('xb') as f:f.write(p.read_bytes())
        sources.append({'path':rel(p),'snapshot':rel(q),'sha256':sha(p),'mutable_own_source_index':p==SOURCEINDEX})
    dump(RUN/'source_manifest.json',{'id':IDENT,'utc':now(),'sources':sources,'policy_schema_only':schema['source'],'policy_data_payload_not_read':True})
    rows='\n'.join('| '+x['name']+' | '+x['meaning']+' | '+('Retenido para uso prospectivo' if x['name']=='days_unoccupied' else 'Condicional, sin sello temporal probado')+' |' for x in fields)
    doc=f'''# F02: construcción, uso, desocupación, alarmas y franquicias en2023

Codex, corte UTC {review['utc']}. La revisión no acredita por sí sola que ninguno de los seis valores estuviera disponible en una cotización concreta. Cinco campos tienen significado físico/contractual definido y podrían conocerse al declarar o aceptar el riesgo, bajo condiciones que deben quedar explícitas. days_unoccupied además carece de ventana de medición documentada: se retiene para cualquier nueva admisión prospectiva hasta aclararla. No se detectó ni se afirma una fuga realizada a partir de sus valores.

Se consultó el [diccionario oficial de Kaggle](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/data), sin cambios respecto al archivado, el contrato de disponibilidad y el código fuente. Del Parquet original de edificios se inspeccionaron solo nombres/tipos de columnas. No se cargaron filas, calcularon distribuciones o cruzaron siniestros, costes, predicciones, grupos o bandas; tampoco se repitieron diagnósticos.

## Hallazgos por campo

| Campo | Significado comprobado en documentación/esquema | Disponibilidad para una cotización2023 |
| --- | --- | --- |
{rows}

Construcción distingue BRK/STN/WOD/MIX, transformados por un mapa fijo a material. Es distinto de property_type (tipología de inmueble), que sí forma parte de B20. La transformación fija de códigos no prueba que la declaración corresponda a la fecha de cotización; hace falta su versión y vigencia para la vivienda del subperiodo.

occupancy describe propietario ocupante o arrendamiento. No es customers.occupation, que describe profesión del cliente y tiene otra clasificación de disponibilidad. El término «ocupación» de un resumen general no debe confundirse con una autorización o exclusión común de ambos campos. Un uso de vivienda conocido para un periodo tampoco demuestra el uso en toda la anualidad o en una cotización anterior.

days_unoccupied se describe como el máximo de desocupación, sin precisar historial anterior, periodo asegurado, ventana móvil, previsión o experiencia realizada. El esquema es numérico y el código lo copia sin una comprobación de ventana temporal. La etiqueta inicial F0_contractual era una clasificación de trabajo, no evidencia de disponibilidad. No se justifica asignarlo al pasado a partir de su nombre, ni truncarlo a365días o a la exposición para fabricar esa interpretación.

smoke_alarms es booleano, no un recuento de detectores. Puede ser una característica declarada antes del riesgo, pero no hay fecha de instalación, declaración o comprobación del estado en la tabla. La plausibilidad de conocer una característica física no certifica que este valor sea una fotografía de la cotización.

Las dos franquicias son términos contractuales: una elegida por el cliente y otra fijada por la aseguradora. Es una inferencia razonable que el término aceptado sea conocido al contratar; no prueba cuál era la selección en la primera cotización o antes de un endoso. No consta una regla completa de suma, prelación o aplicación conjunta por peril. El diccionario define pagos ya netos de franquicia y su aplicación a todos los perils: no se altera T0 o descuenta de nuevo la retención.

## Fechas disponibles y lo que no demuestran

En el esquema suministrado las únicas columnas de tipo fecha/timestamp son period_start y period_end. Describen cobertura, no captura de cada atributo. También existe el número days_quote_to_inception. La convención actual deriva:

    quote_date_proxy = period_start - days_quote_to_inception

Esa resta no crea un registro de la cotización ni fecha de conocimiento de cada respuesta. Los cambios a mitad del año pueden generar subperiodos; no basta situar una fecha derivada para asegurar que todas las características se declararon en ella. Se necesitan fecha efectiva y fecha de captura/versión, vinculadas a la fila y, cuando corresponda, al endoso.

La inspección estática de make_features muestra copias de las columnas de póliza y codificación fija de construcción. No hay un as-of join o filtro por timestamp del atributo para estos campos. No se ejecutó el constructor ni el runner histórico, que recorre otros años. No se atribuye a esta revisión una prueba funcional del flujo completo o invariancia de objetos ajustados.

El reto condiciona la predicción al periodo y atributos suministrados. Esa investigación condicional no equivale a un backtest de tarifa cotizada con información históricamente disponible. Esta distinción evita tanto certificar prospectividad sin evidencia como declarar inválidos automáticamente todos los modelos anteriores. La revisión no decide una nueva admisión o cambia el contrato congelado.

## Evidencia concreta que falta

| Bloque | Documento o registro necesario | Qué permitiría resolver |
| --- | --- | --- |
| Los seis campos | Cuestionario/registro de declaración versionado, fecha de captura y vigencia para la fila2023; propuesta aceptada y endosos | Si el valor estaba disponible al momento de decisión elegido |
| Desocupación | Definición exacta de la ventana, fecha de referencia y naturaleza declarada/realizada | Si el máximo pertenece al pasado conocido o incorpora experiencia posterior |
| Construcción,uso,alarmas | Declaración o constatación fechada y cambios relevantes de estado | Si el dato representa ese riesgo/subperiodo y no un maestro posterior |
| Franquicias | Condiciones aplicables y versión aceptada; regla conjunta y por peril | Interpretación contractual y temporal, sin recalcular el coste neto ya observado |

No se localizaron esos historiales o condiciones completas en los archivos/documentos examinados; no es una afirmación sobre todos los registros que pudiera poseer el organizador. No se envían consultas a terceros bajo este encargo. Una distribución o asociación con el coste no puede sustituir la evidencia de cuándo se conoció el dato, por lo que no se hacen nuevas tablas de rendimiento o correlación.

## Consecuencia y continuidad

F02 queda revisada documentalmente con condiciones abiertas: cinco campos definidos pero sin acreditación de captura en cotización y desocupación retenida hasta aclarar ventana/procedencia temporal. Ninguno de los seis está en la receta de siete efectos de B20; su presencia en el F0 amplio no es una nueva orden humana o aprobación. Se conserva el contrato F0 histórico, código y artefactos entrenados, sin reescribirlos para hacer desaparecer el hallazgo. Esta ficha será la referencia de disponibilidad para una eventual propuesta posterior; no añade variables al modelo actual.

Puede orientar una hipótesis más precisa sobre heterogeneidad, pero no demuestra el mecanismo residual de B20, efectos causales o ganancia predictiva. No añade componentes o costes independientes y no resuelve el soporte retenido fallido. G1/G2 continúan abiertas. F01 ya acreditó igualdad binaria; no se repite ese cotejo.

B00 y todas las alternativas,T0/C0,exposición y folds se conservan.2024/test/SEL01/actas/ledger siguen cerrados para datos/resultados de modelado; de la tabla de pólizas solo se consultó el esquema común. Cero entrenamiento,cargas de modelos,inferencias,scores o remuestreos. La ventana/automatización nocturna permanecen cerradas y no se crea otra. Exposición previa de un asunto externo declarada sin usar métricas o afirmar ceguera completa. Codex firma revisión propia documental, no validación profesional independiente o aprobación humana. Las prácticas IAA de propósito,procedencia y documentación orientan la separación de hecho,inferencia y supuesto, sin certificar aptitud actuarial.

[Índice F02](../../registro/{INDEX.name}), [plan de fuentes](FUENTES_2023_Y_PLAN_REVISION_B20.md), [disponibilidad inicial histórica](VARIABLES_Y_ULTIMO.md) y [verificación binaria](VERIFICACION_CONTENIDO_KAGGLE_20261024.md). Matriz por campo,esquema,recibo documental,fuentes/SHA y decisiones en {rel(RUN)}.
'''
    for a,b in {'en2023':'en 2023','cotización2023':'cotización 2023','a365':'a 365','fila2023':'fila 2023','Construcción,uso,alarmas':'Construcción, uso y alarmas','alternativas,T0':'alternativas, T0','C0,exposición':'C0, exposición','propósito,procedencia':'propósito, procedencia','hecho,inferencia':'hecho, inferencia','campo,esquema':'campo, esquema','fuentes/SHA':'fuentes/SHA'}.items():doc=doc.replace(a,b)
    with DOC.open('x',encoding='utf-8') as f:f.write(doc)
    dump(RUN/'decision_journal.json',{'id':IDENT,'author':'Codex','utc':now(),'decisions':[
      {'id':'F02-01','decision':'Separar definición del campo, disponibilidad plausible y prueba temporal de la instancia; ninguna de las seis cotizaciones queda certificada.'},
      {'id':'F02-02','decision':'Retener days_unoccupied para nueva admisión prospectiva hasta aclarar ventana/as-of; riesgo no resuelto, no fuga demostrada.'},
      {'id':'F02-03','decision':'Construcción,occupancy,alarmas yfranquicias quedan condicionales; exigir declaración/vigencia si se reclama prospectividad.'},
      {'id':'F02-04','decision':'Distinguir uso de vivienda de profesión y material constructivo de tipología; no alarmas como recuento ni doble deducción de franquicia.'},
      {'id':'F02-05','decision':'quote_date derivada y period_start/end no acreditan cuándo se capturó un atributo; no temporal join para estos campos en código inspeccionado.'},
      {'id':'F02-06','decision':'No cambiar F0/B20/B00, targets,folds o artefactos; G1/G2 siguen abiertos, sin nuevos diagnósticos o entrenamiento.'}]})
    fid='COD-S2-20261024-053';fp=RUN/'forum_053.md'
    fp.write_text(f'''Codex, F02 solicitada: revisión documental/de esquema de construcción,ocupación/desocupación,alarmas yfranquicias para uso2023. Informe:{rel(DOC)}; matriz:{rel(RUN/'temporal_availability_review.json')}. Diccionario oficial igual al archivado; solo esquema de pólizas,fuente y contratos, sin valores de filas o nuevos diagnósticos.

Hallazgo: ninguna instancia queda acreditada como conocida en una cotización concreta. Construcción,uso de vivienda,alarmas y las dos franquicias tienen definición física/contractual y disponibilidad plausible condicionada a declaración/vigencia. days_unoccupied no define ventana ni fecha de referencia,declarado/realizado: retener para nueva admisión prospectiva hasta aclaración, sin afirmar fuga demostrada o fabricar ventana recortando a365días/exposición. F0_contractual inicial no es prueba temporal.

El esquema solo tiene period_start/end como fechas,también days_quote_to_inception. La resta derivada no crea fecha de captura por campo. El código copia estos inputs,con mapa fijo de construcción,sin as-of join o validación de captura para ellos; inspección estática,no runner ejecutado. occupancy es uso de vivienda,distinto de customers.occupation(profesión); construction_type es material,distinto de property_type; smoke_alarms es booleano,no número. Pagos ya netos de franquicia,no doble descuento; regla conjunta de franquicias/endosos pendiente.

Faltan declaraciones versionadas,captura/vigencia,endosos y ventana exacta de desocupación. No se localizaron en las fuentes delimitadas. Cinco campos condicionales y uno temporalmente retenido no equivalen a nuevos efectos probados o más componentes; G1/G2abiertos. Ninguno está en siete efectosB20. Mantengo contratoF0/código histórico y modelos intactos: ficha nueva cualifica disponibilidad,no reescribe antecedentes.

F02-01 aF02-06,Codex. B00/todas las alternativas,T0/C0/folds conservados;2024/test/SEL01/actas/ledgercerrados,no valores2024/test interpretados. Cero ajustes,cargas,inferencias,scores,bootstrap o diagnósticos repetidos. Sin reapertura de ventana/automatización,no mensajes externos o delegación. Revisión documental propia,no aprobación humana o validación profesional independiente.''',encoding='utf-8')
    proc=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',fid,'--asunto','F02: disponibilidad temporal condicionada y desocupación pendiente de definición','--cuerpo',str(fp)],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr;dump(RUN/'forum_receipt.json',json.loads(proc.stdout))
    idx={**{k:v for k,v in review.items() if k!='fields'},'path_base':'workspace_root','status':'F02_documentary_review_complete_five_conditional_unoccupied_window_unresolved','run':rel(RUN),'documentation':rel(DOC),'documentation_sha256':sha(DOC),'forum_result':fid,'field_matrix':{'path':rel(RUN/'temporal_availability_review.json'),'sha256':sha(RUN/'temporal_availability_review.json')},'source_manifest':{'path':rel(RUN/'source_manifest.json'),'sha256':sha(RUN/'source_manifest.json')},'decision_journal':{'path':rel(RUN/'decision_journal.json'),'sha256':sha(RUN/'decision_journal.json')}}
    dump(INDEX,idx);changes=[]
    def change(p,fn):
        before=p.read_bytes();after=fn(before.decode('utf-8-sig')).encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        for phase,b in [('before',before),('after',after)]:
            q=RUN/'registration_cuts'/phase/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as f:f.write(b)
        tmp=p.with_name(p.name+'.F02review.tmp')
        with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert p.read_bytes()==before,'Concurrent change '+rel(p);os.replace(tmp,p)
        changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p)})
    def source_update(raw):
        vals={'F02_status':'documentary_review_complete_five_conditional_unoccupied_window_unresolved','F02_review_index':rel(INDEX),'F02_completed_utc':now(),'F02_new_field_admission':False}
        for k,v in vals.items():raw=top(raw,k,v)
        return raw
    change(SOURCEINDEX,source_update)
    change(ROOT/('Preparaci'+chr(243)+'n')/'ESTADO_PROYECTO.json',lambda raw:top(raw,STATEKEY,idx))
    section=f'''\n\n## F02: semántica y disponibilidad temporal de seis campos de edificios2023

Codex,UTC {now()},foro053,decisiones F02-01 aF02-06. Informe {rel(DOC)},índice {rel(INDEX)},matriz por campo/recibos en {rel(RUN)}. Revisión documental de diccionario vigente,schema_arrow de pólizas y código,no valores de filas,modelos o nuevos diagnósticos. Los seis campos están enF0amplio,fuera de siete efectosB20; no se cambia contrato/código histórico o modelos.

Ninguna captura a cotización queda acreditada. Construcción,uso de vivienda,alarmas y las dos franquicias: definición y plausibilidad contractual/física,condicionadas a declaración/vigencia. days_unoccupied:ventana/as-of/declarado-realizado no aclarados,retenido para nueva admisión prospectiva sin declarar fuga observada o recortar datos para inventar ventana. F0_contractual no es evidencia temporal. Solo period_start/end son fechas en el esquema; la fecha derivada por days_quote_to_inception no fecha cada atributo. Código inspeccionado copia inputs sin as-of join o captura para estos campos; no se ejecutó runner.

occupancy no es profesión occupation,construction_type no es property_type,alarmas es booleano. Pago ya neto de franquicia,no doble descuento; regla conjunta y endosos pendientes. Faltan declaración/captura/vigencia versionadas y ventana exacta de desocupación; no localizadas en fuentes delimitadas. F02documental revisada con condiciones abiertas,no nueva admisión de campos o resolución deG1/G2. B00/alternativas,T0/C0/folds intactos,2024/test/SEL01/actas/ledgercerrados; sin valores2024/test o scores interpretados. Cero entrenamiento,inferencias,remuestreo o repetición de diagnósticos. Ventana/automatización nocturna cerradas,sin otra programación,mensajes externos o delegación. Revisión documental propia,no profesional independiente o aprobación humana.\n'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/('Preparaci'+chr(243)+'n')/name,lambda raw:raw+section)
    change(ROOT/'RUTAS_PROYECTO.json',lambda raw:top(top(raw,'week_2_F02_temporal_availability_index',rel(INDEX)),'week_2_F02_temporal_availability_report',rel(DOC)))
    obs={'id':IDENT,'utc':now(),'frozen_source_copies_intact':all(sha(ROOT/x['snapshot'])==x['sha256'] for x in sources),'original_code_contract_model_counter_night_sources_unchanged':all(sha(ROOT/x['path'])==x['sha256'] for x in sources if not x['mutable_own_source_index']),'six_fields_outside_B20':all(not x['in_B20'] for x in fields),'scope':'Documentary integration only; no numerical diagnosis or prior suite run.'}
    dump(RUN/'documentary_integrity_receipt.json',obs);dump(RUN/'registration.json',{'changes':changes,'price_catalog_mutations':0,'counter_mutations':0,'feature_contract_mutations':0,'model_code_mutations':0,'night_index_mutations':0})
    files=[p for p in RUN.rglob('*') if p.is_file()]+[INDEX,DOC,Path(__file__).resolve()]
    dump(RUN/'manifest.json',{'id':IDENT,'utc':now(),'files':[{'path':rel(p),'sha256':sha(p)} for p in files]})
    print(json.dumps({'id':IDENT,'forum_result':fid,'document':rel(DOC),'defined_but_conditional_fields':5,'unoccupied_window_unresolved':True,'quote_capture_proven_fields':0,'original_contract_model_sources_unchanged':obs['original_code_contract_model_counter_night_sources_unchanged'],'new_fits':0,'new_diagnostics':0},ensure_ascii=True))

if __name__=='__main__':main()
