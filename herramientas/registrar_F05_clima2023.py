"""F05 documental: semántica/vintage de clima, sin abrir datos o repetir diagnósticos."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/revision_F05_2023/f05_20261024_v1'
DOC=REPO/'docs/archivo/semana2/F05_CLIMA_2023_Y_DISPONIBILIDAD_TEMPORAL.md'
INDEX=REPO/'registro/semana2_F05_clima2023_actual.json'
SOURCE=REPO/'registro/semana2_b20_fuentes2023_actual.json'
IDENT='S2-F05-CLIMA2023-v1-20261024';FID='COD-S2-20261024-056'
STATEKEY='week_2_F05_climate_availability2023_v1_20261024'
now=lambda:datetime.now(timezone.utc).isoformat()
rel=lambda p:p.relative_to(ROOT).as_posix()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))

def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def top(raw,key,val):
    v=json.dumps(val,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+v+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+v+raw[m.end()+end:]

def pages(p):return json.loads(next(x['text'] for x in read(p)['content'] if x['type']=='text'))['pages']

def weather(s):return s.split('### weather',1)[1].split('### Columns',1)[0]

def main():
    assert not INDEX.exists() and not DOC.exists()
    p2=pages(RUN/'data_description_part2_response.json');p1=pages(RUN/'data_description_part1_response.json')
    old=read(ROOT/'Hackaton/Semana 2/Codex/fuentes_variables_ultimo/data_description_response.json')['value']
    old=json.loads(next(x['text'] for x in old['content'] if x['type']=='text'))['pages']
    assert p2==old
    assert weather(p1[0]['content'])==weather(p2[0]['content'])
    query=read(RUN/'search_limitations_receipt.json');assert query['positive_control']['returned_empty']
    fields=[
      {'field':'hail_days','definition':'Número de días con granizo del año','interpretation':'Recuento anual; no se describe como pronóstico emitido antes del año','quote2023_availability':'No acreditada para el agregado anual de2023; no tratarlo como conocido al iniciar2023.'},
      {'field':'freezing_days','definition':'Días bajo cero, dentro de tabla por año','interpretation':'Recuento del año de referencia; sin vintage de pronóstico/publicación','quote2023_availability':'No acreditada para agregado completo2023.'},
      {'field':'rainfall_mm','definition':'Precipitación anual','interpretation':'Agregado anual; no previsión fechada en el diccionario','quote2023_availability':'No acreditada antes de completar ventana y publicación.'},
      {'field':'mean_temperature_c','definition':'Temperatura media anual','interpretation':'Agregado anual; no previsión fechada en el diccionario','quote2023_availability':'No acreditada antes de completar ventana y publicación.'},
      {'field':'dry_summer_index','definition':'Sequedad estival, escala húmedo/seco','interpretation':'Índice de estación/año; no consta metodología,ventana exacta o naturaleza observada/pronosticada','quote2023_availability':'No acreditada; no suponer que sea un hazard fijo anterior por ser índice.'},
      {'field':'wind_exposure_index','definition':'Exposición a viento dañino, escala0–10','interpretation':'Podría representar una medida de riesgo; no consta si es estática,realizada o prospectiva ni vintage','quote2023_availability':'Indeterminada; no declararlo conocido o fuga demostrada solo por su nombre.'},
      {'field':'wildfire_index','definition':'Riesgo de incendio forestal, escala0–1','interpretation':'No consta si es hazard previo,pronóstico o índice actualizado con experiencia del año','quote2023_availability':'Indeterminada; requiere emisión,ventana,insumos y vigencia, sin admisión nueva.'}]
    evidence={'id':IDENT,'author':'Codex','utc':now(),'part2_dictionary_unchanged':True,'part1_part2_weather_definitions_match':True,'new_official_temporal_clarification_located':False,'fields':fields,'reference_year_is_not_publication_date':True,'prior_calendar_guard_not_publication_proof':True,'prior_quote_date_proxy_not_capture_proof':True,'keyword_search_negative_evidence_valid':False,'keyword_search_reason':'Known Claims topic positive control returned empty; category filter also produced unrelated competitions. Discard these as absence evidence.','all_forum_comment_bodies_searched':False,'row_values_read':0,'climate_parquet_opened':False,'new_fits':0,'new_predictions':0,'new_scores':0,'new_numerical_diagnostics':0,'new_bootstrap':0,'new_feature_admission':False,'reference':'W2-B00','all_alternatives_preserved':True,'G1_closed':False,'G2_closed':False,'2024_test_model_validation_opened':False,'professional_independent_validation':False}
    dump(RUN/'documentary_review.json',evidence)
    paths=[SOURCE,REPO/'registro/semana2_b20_fuentes2023_plan_v1.json',REPO/'registro/semana2_F04_fuentes2023_actual.json',REPO/'registro/semana2_F02_disponibilidad2023_actual.json',REPO/'registro/semana2_desarrollo2023_plan_v6.json',REPO/'docs/archivo/semana2/CAPITAL_CLIMA_CREDIBILIDAD_2023.md',REPO/'docs/archivo/semana2/VARIABLES_Y_ULTIMO.md',REPO/'src/semana2/variables_ultimo.py',REPO/'src/semana2/credibilidad2023.py',REPO/'privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766/availability_contract.json',REPO/'registro/semana2_glm_ridge_coberturas_plan_v1.json',REPO/'registro/semana2_desarrollo2023_actual.json',REPO/'registro/semana2_contadores_propios_actual.json',REPO/'registro/semana2_continuidad_nocturna.json']
    sources=[]
    for i,p in enumerate(paths):
        q=RUN/'sources'/f'{i:02d}_{p.name}';q.parent.mkdir(exist_ok=True)
        with q.open('xb') as f:f.write(p.read_bytes())
        sources.append({'path':rel(p),'snapshot':rel(q),'sha256':sha(p),'intentional_mutable_source_index':p==SOURCE})
    dump(RUN/'source_manifest.json',{'id':IDENT,'utc':now(),'sources':sources,'weather_source_file_not_reopened':True,'prior_temporal_diagnostics_reused_not_rerun':True,'new_official_pages':{'part1':'data_description_part1_response.json','part2':'data_description_part2_response.json'},'topic_and_query_receipts':['topic_inventory_receipt.json','search_limitations_receipt.json']})
    table='\n'.join('| '+x['field']+' | '+x['definition']+' | '+x['interpretation']+' |' for x in fields)
    doc=f'''# F05: clima de 2023 y disponibilidad temporal

Codex, corte UTC {evidence['utc']}. No se localizó una aclaración oficial nueva que acredite la disponibilidad prospectiva del clima de 2023 o defina sus índices como riesgos conocidos antes de cotizar. La búsqueda tiene límites: el buscador de palabras del foro falló un control positivo y no se revisaron todos los cuerpos de comentarios. Por tanto, no se afirma ausencia universal de aclaraciones.

## Fuentes comprobadas y límites de búsqueda

El [diccionario de la parte2](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/data), releído por Kaggle MCP, coincide íntegramente con el archivado. La sección weather del [diccionario de la parte1](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1/data) coincide con la actual de la parte2. El texto define una fila por dirección/año, pero no fecha de publicación, captura, versión de pronóstico o entrenamiento del índice. No se abrió weather.parquet ni se contaron o compararon celdas.

Los listados específicos devuelven siete temas y total_count=7 en parte1, y dos y total_count=2 en parte2. No hay un título identificado como weather,climate,forecast o hazard. Los dos temas de parte2 mantienen las fechas/recuentos de la búsqueda F04, referidos a descarga y formato de envío, sin releerlos como si fueran una novedad climática. La revisión de títulos no cubre aclaraciones enterradas en comentarios de otros temas.

La búsqueda general por categoría devolvió temas de otras competencias y se descartó. Tras obtener el forum_id oficial, las consultas weather/climate por foro devolvieron objetos vacíos. También devolvió vacío Claims, aunque el listado específico contiene el tema conocido751543. Ese control impide convertir las respuestas vacías en evidencia de que no existe una aclaración. Las máscaras de metadatos no devolvieron el localizador; se obtuvo después de metadatos del tema, sin emitir o usar su cuerpo ajeno. Los recibos conservan estos fallos, sin presentar el buscador como verificado.

Como respaldo se consultó el índice web con las rutas de discusión de ambas competencias y términos climáticos. Los resultados visibles remitían a eventos ajenos, incluido el hackathon Ames2025; se excluyeron. No se adoptaron reglas, definiciones o permisos de otros concursos. El índice público tampoco acredita cobertura completa. No se contactó al organizador o a terceros.

## Qué significa cada medida y qué falta fechar

| Campo | Definición documental | Límite temporal |
| --- | --- | --- |
{table}

Los recuentos y agregados de todo2023 no estaban realizados al iniciar ese año. Su presencia en una tabla entregada posteriormente no los convierte en información disponible entonces. Si algún campo fuera un pronóstico, se necesitarían su fecha de emisión y versión; el diccionario no lo establece. dry_summer_index necesita además ventana de referencia y aclarar si resume la estación realizada o una previsión.

wind_exposure_index y wildfire_index tienen lenguaje de riesgo, pero eso no prueba un mapa estático anterior al periodo. Tampoco basta para afirmar que sus valores incorporen siniestros futuros o sean fuga demostrada. Método, insumos, periodo de cálculo, publicación y vigencia no constan en las definiciones examinadas. Correlación o persistencia entre años no resolverían estas preguntas y no se vuelven a medir.

## Año de referencia, publicación y fecha de decisión

year es el año al que corresponde la medida, no la fecha en que se conoció. Para un agregado realizado haría falta que su ventana hubiera terminado y su publicación/captura ocurriera antes de la decisión. Terminar el calendario no prueba publicación inmediata. Para un índice de riesgo o pronóstico se necesitaría acreditar una versión emitida con los insumos entonces disponibles y su vigencia, sin usar resultados posteriores para construirlo o elegirlo.

La variante histórica existente deriva quote_date=period_start−days_quote_to_inception y selecciona el año natural anterior. Es una convención conservadora de calendario con disponibilidad al terminar el año asumida en la documentación; no una comprobación de la fecha real de publicación. Como ya señaló F02, esa resta tampoco crea una cotización o declaración versionada. Se cualifica aquí su interpretación, sin editar la función, el contrato o artefactos históricos.

La revisión previa dejó documentada ausencia de historia climática emergente anterior a2023 para la prueba. Se reutiliza ese resultado y no se repite el inventario de valores. Los registros desarrollados no proporcionan una dirección emergente equivalente: los identificadores pueden colisionar y no existe correspondencia geográfica publicada entre regiones sintéticas. No se rellena con clima de otros mercados, del mismo año o posterior, ni se inventa un cruce a clima real.

## Decisión vigente y evidencia necesaria

La variante CLIMA-S2-01 ya quedó fuera del contrato prospectivo por sus fuentes y selección posteriores. Se conserva la revisión anterior y su hallazgo S2-VAL-DAT-003, con autoría y responsable; no se repiten permutaciones, guardas, replays o scores, ni se cierra el hallazgo. La búsqueda actual no aporta evidencia para cambiar esa decisión. No se entrena una copia con clima todo ausente ni una variante con información posterior.

Para reconsiderar F05 se necesitaría una aclaración oficial versionada por campo: observado/pronosticado/hazard estático, ventana de referencia, método e insumos, fecha de emisión o publicación y vigencia. Una fecha genérica de subida de Parquet no cumple esa función. También se necesitaría historia legítima para las direcciones emergentes y un instante de decisión verificable si se pretende uso prospectivo. Una autorización de uso en el concurso, si existiera, no fecharía por sí sola el conocimiento histórico de cada valor.

Esta ficha es una revisión documental de disponibilidad, no una nueva receta o admisión de predictores. Ninguno de los siete campos climáticos entra en B20. F05 queda buscada sin aclaración temporal nueva localizada, con clasificación de índices y fechas aún pendientes. No añade siniestros, exposición o componentes, ni establece G1 o resuelve G2.

B00 y todas las alternativas, T0/C0, exposición, folds, modelos y contadores se conservan.2024/test/ledger/actas/SEL01 siguen cerrados para datos/resultados de modelado; no se cargaron sus artefactos. Cero entrenamiento,cargas de modelos,inferencias,scores,remuestreos o nuevos diagnósticos. Exposición histórica de un asunto externo declarada, sin repetir o usar sus métricas ni afirmar ceguera completa. Ventana/automatización nocturna cerradas, sin nuevas continuaciones, contactos o delegación. Codex firma revisión propia de fuentes, no aprobación humana o validación profesional independiente. Las prácticas IAA de documentación §2 y gobernanza §2.8 orientan separar disponibilidad,supuesto y verificación.

El [índice F05](../../registro/{INDEX.name}) enlaza matriz por campo, consultas y limitaciones, fuentes/SHA y decisiones. Se conserva la [revisión climática previa](CAPITAL_CLIMA_CREDIBILIDAD_2023.md), la [disponibilidad inicial](VARIABLES_Y_ULTIMO.md) y [F02](F02_SEMANTICA_Y_DISPONIBILIDAD_2023.md) sin reescribirlas.
'''
    for a,b in [('parte2','parte 2'),('parte1','parte 1'),('todo2023','todo 2023'),('a2023','a 2023'),('Ames2025','Ames 2025'),('conocido751543','conocido 751543'),('conservan.2024','conservan. 2024')]:doc=doc.replace(a,b)
    with DOC.open('x',encoding='utf-8') as f:f.write(doc)
    decisions=[('F05-01','No nueva aclaración localizada en fuentes delimitadas; respuestas vacías de buscador con control positivo fallido no prueban ausencia.'),('F05-02','Diccionario parte2 idéntico al archivado; sección climática actual parte1 equivalente; no se reabre Parquet.'),('F05-03','Separar agregados anuales de índices con método/vintage no documentados; nombre risk/index no acredita disponibilidad ni demuestra fuga.'),('F05-04','year y fecha de subida no son publicación/conocimiento; año anterior y quote_date derivada conservan supuestos explícitos,no prueba as-of.'),('F05-05','Conservar rechazo prospectivo previo y responsable de S2-VAL-DAT-003; no repetir diagnóstico, rellenar historia o admitir clima nuevo.'),('F05-06','B00/alternativas,T0/C0/folds/modelos intactos; G1/G2 abiertos y2024cerrado, sin entrenamiento o nuevas pruebas.')]
    dump(RUN/'decision_journal.json',{'id':IDENT,'author':'Codex','utc':now(),'decisions':[{'id':k,'decision':v} for k,v in decisions]})
    fp=RUN/'forum_056.md'
    with fp.open('x',encoding='utf-8') as f:f.write(f'''Codex, F05 solicitada. Informe: {rel(DOC)}. Matriz y recibos de búsqueda: {rel(RUN)}. Sin abrir weather.parquet o repetir diagnósticos.

No localicé aclaración temporal oficial nueva en las fuentes delimitadas. El diccionario de la parte 2 sigue igual al archivado; su sección weather coincide con la actual de la parte 1. No indica publicación, captura o versión del pronóstico o índice. Los listados específicos devuelven siete temas de la parte 1 y dos de la parte 2, sin título climático identificado. No se afirma cubrir todos los comentarios. La búsqueda por categoría devolvió otros concursos; por forum_id también dio vacío el control positivo del tema conocido Claims, 751543. Los vacíos se descartan como prueba de ausencia. El respaldo web no identificó una fuente del concurso 2026; se excluyeron resultados ajenos. Limitaciones conservadas, sin contactos externos.

Los recuentos de días y agregados anuales de 2023 no son información realizada al inicio de 2023. dry_summer_index no aclara la ventana ni si es observado o pronosticado. wind_exposure_index y wildfire_index tienen lenguaje de riesgo, pero no método, insumos o fecha que acrediten un riesgo calculado antes del periodo; tampoco se declara fuga demostrada por sus nombres. La persistencia o correlación no fecha el dato y no se recalcula.

year es referencia, no publicación; terminar año no acredita disponibilidad inmediata. El selector histórico de año anterior y quote_date derivada siguen como convenciones con supuestos, sin prueba de captura/publicación real. No se edita código/contrato histórico o reejecuta flujo. La revisión previa de falta de historia emergente anterior2023 se reutiliza; no backfill contemporáneo/futuro,de otro mercado o geografía real inventada.

Sigue vigente el rechazo prospectivo de CLIMA-S2-01 y el hallazgo S2-VAL-DAT-003 con su responsable. Para reconsiderar: aclaración por campo de observado/pronóstico/hazard,ventana,método,insumos,emisión/publicación,vigencia e historia emergente legítima. Fecha de subida o permiso de concurso no prueban conocimiento al cotizar. F05 no añade variables a B20 ni evidencia de soporte; G1/G2 sin cierre.

F05-01 a F05-06, autor Codex. B00 y las alternativas, T0/C0, exposición, folds, modelos y contadores conservados. 2024/test/ledger/actas/SEL01 cerrados; cero filas, entrenamiento, cargas, inferencias, scores, remuestreos o diagnósticos nuevos. Ventana/automatización nocturna cerradas, sin delegación o nuevos chats. Revisión propia de fuentes, sin aprobación humana o validación profesional independiente.
''')
    proc=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',FID,'--asunto','F05: sin aclaración temporal nueva localizada; índices y fechas siguen pendientes','--cuerpo',str(fp)],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr;dump(RUN/'forum_receipt.json',json.loads(proc.stdout))
    idx={k:v for k,v in evidence.items() if k!='fields'}
    idx.update(path_base='workspace_root',status='F05_documentary_search_complete_no_new_clarification_located_temporal_gaps_open_search_limits_disclosed',run=rel(RUN),documentation=rel(DOC),documentation_sha256=sha(DOC),forum_result=FID)
    for key,name in [('review','documentary_review.json'),('source_manifest','source_manifest.json'),('decisions','decision_journal.json'),('search_limits','search_limitations_receipt.json')]:idx[key]={'path':rel(RUN/name),'sha256':sha(RUN/name)}
    dump(INDEX,idx);changes=[]
    def change(p,fn):
        before=p.read_bytes();after=fn(before.decode('utf-8-sig')).encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        for phase,b in [('before',before),('after',after)]:
            q=RUN/'registration_cuts'/phase/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as f:f.write(b)
        tmp=p.with_name(p.name+'.F05review.tmp')
        with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert p.read_bytes()==before,'Concurrent change '+rel(p);os.replace(tmp,p)
        changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p)})
    def update(raw):
        for k,v in {'F05_status':idx['status'],'F05_review_index':rel(INDEX),'F05_completed_utc':now(),'F05_new_temporal_clarification_located':False,'F05_keyword_search_absence_evidence_valid':False,'F05_new_feature_admission':False}.items():raw=top(raw,k,v)
        return raw
    change(SOURCE,update)
    change(ROOT/'Preparación/ESTADO_PROYECTO.json',lambda raw:top(raw,STATEKEY,idx))
    section=f'''\n\n## F05: clima de 2023 y aclaraciones de disponibilidad temporal

Codex, UTC {now()}, foro056, decisiones F05-01 a F05-06. Informe {rel(DOC)}, índice {rel(INDEX)}, evidencia/consultas/limitaciones en {rel(RUN)}. Diccionario oficial parte2 íntegro igual al archivado y definición weather actual parte1 igual a parte2. No se localizó aclaración nueva de publicación,captura,pronóstico o hazard previo. Listados específicos7/2temas sin título climático identificado; no todos los comentarios revisados. Búsqueda por categoría devolvió otros concursos y por foro falló control positivo Claims751543; vacíos no válidos para ausencia. Respaldo web sin fuente del concurso2026,ajenos descartados. No afirmar inexistencia universal o cobertura completa.

Agregados/recuentos anuales2023 no conocidos realizados al inicio2023. dry_summer_index necesita ventana/metodología; viento/incendio con lenguaje de riesgo no acreditan hazard previo o fuga por el nombre. year/fecha de subida no fechan publicación. Selector de año anterior y quote_date derivada conservan supuestos,no prueba as-of de publicación/captura; sin editar contrato o código histórico. Revisión previa de historia emergente faltante reutilizada,no recálculo o backfill de otro mercado/futuro. Rechazo prospectivo CLIMA-S2-01 y hallazgo S2-VAL-DAT-003 con responsable intactos. Faltan aclaración por campo,ventana,método/insumos,vintage,emisión/publicación/vigencia y fuente emergente histórica legítima. No nueva admisión en B20 o cierre G1/G2.

B00/alternativas,T0/C0/exposición/folds/modelos/contadores intactos. weather.parquet no abierto; cero filas,entrenamiento,cargas,inferencias,scores,remuestreos o diagnósticos repetidos.2024/test/SEL01/actas/ledger cerrados y asunto externo previo declarado sin repetir/usar métricas. Ventana/automatización nocturna cerradas; sin contactos,nuevos chats,delegación o programación. Revisión documental propia de Codex,no aprobación humana o validación profesional independiente.\n'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+section)
    change(ROOT/'RUTAS_PROYECTO.json',lambda raw:top(top(raw,'week_2_F05_climate_search_index',rel(INDEX)),'week_2_F05_climate_search_report',rel(DOC)))
    checks={'id':IDENT,'utc':now(),'source_copies_intact':all(sha(ROOT/x['snapshot'])==x['sha256'] for x in sources),'original_contract_model_counter_night_sources_unchanged':all(sha(ROOT/x['path'])==x['sha256'] for x in sources if not x['intentional_mutable_source_index']),'dictionary_unchanged':p2==old,'weather_definitions_match':weather(p1[0]['content'])==weather(p2[0]['content']),'search_failure_disclosed':idx['keyword_search_negative_evidence_valid'] is False,'scope':'Documentary integration only; no code/runtime or numerical climate validation claimed.'}
    assert all(v for v in checks.values() if isinstance(v,bool))
    dump(RUN/'documentary_integrity_receipt.json',checks)
    dump(RUN/'registration.json',{'changes':changes,'price_catalog_mutations':0,'counter_mutations':0,'feature_contract_mutations':0,'model_code_mutations':0,'night_index_mutations':0})
    files=[p for p in RUN.rglob('*') if p.is_file()]+[INDEX,DOC,Path(__file__).resolve()]
    dump(RUN/'manifest.json',{'id':IDENT,'utc':now(),'files':[{'path':rel(p),'sha256':sha(p)} for p in files]})
    print(json.dumps({'id':IDENT,'forum_result':FID,'document':rel(DOC),'new_temporal_clarification_located':False,'search_failure_disclosed':True,'new_fits':0,'row_values_read':0,'integrity':checks},ensure_ascii=True))

if __name__=='__main__':main()
