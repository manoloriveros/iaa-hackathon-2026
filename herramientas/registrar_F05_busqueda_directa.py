"""Registra sustitución verificada de búsqueda del foro; conserva F05 histórico."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/revision_F05_2023/f05_busqueda_directa_20261024_v1'
DOC=REPO/'docs/archivo/semana2/F05_BUSQUEDA_DIRECTA_Y_COBERTURA_FORO.md'
INDEX=REPO/'registro/semana2_F05_busqueda_foro_actual.json'
OLD=REPO/'registro/semana2_F05_clima2023_actual.json'
SOURCE=REPO/'registro/semana2_b20_fuentes2023_actual.json'
IDENT='S2-F05-FORO-DIRECTO2023-v1-20261024';FID='COD-S2-20261024-057'
STATEKEY='week_2_F05_forum_search_resolution2023_v1_20261024'
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

def main():
    assert not INDEX.exists() and not DOC.exists()
    receipt=read(RUN/'direct_search_receipt.json');guards=read(RUN/'retrieval_guard_checks.json');stable=read(RUN/'inventory_stability.json')
    assert receipt['topics']==9 and receipt['roots']==9 and receipt['replies']==12 and receipt['messages']==21
    assert receipt['positive_control']['found'] and not receipt['negative_control']['found']
    assert not receipt['climate_matches'] and not receipt['temporal_context_matches']
    assert all(x['rejected'] for x in guards['cases']) and all(x['stable'] for x in stable)
    paths=[SOURCE,OLD,REPO/'docs/archivo/semana2/F05_CLIMA_2023_Y_DISPONIBILIDAD_TEMPORAL.md',REPO/'privado/semana2/revision_F05_2023/f05_20261024_v1/documentary_review.json',REPO/'privado/semana2/revision_F05_2023/f05_20261024_v1/search_limitations_receipt.json',REPO/'registro/semana2_desarrollo2023_actual.json',REPO/'registro/semana2_contadores_propios_actual.json',REPO/'registro/semana2_continuidad_nocturna.json',REPO/'registro/semana2_glm_ridge_coberturas_plan_v1.json',REPO/'privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766/availability_contract.json']
    sources=[]
    for i,p in enumerate(paths):
        q=RUN/'sources'/f'{i:02d}_{p.name}';q.parent.mkdir(exist_ok=True)
        with q.open('xb') as f:f.write(p.read_bytes())
        sources.append({'path':rel(p),'snapshot':rel(q),'sha256':sha(p),'intentional_mutable_source_index':p==SOURCE})
    dump(RUN/'source_manifest.json',{'id':IDENT,'utc':now(),'sources':sources,'retrieval_code':rel(REPO/'herramientas/buscar_aclaraciones_foro_seguro.mjs'),'unrelated_message_bodies_archived':False,'body_hashes_in':'direct_search_receipt.json','no_raw_data_read':True})
    result={'id':IDENT,'author':'Codex','utc':now(),'status':'F05_direct_forum_search_verified_at_cut_no_climate_clarification_temporal_gaps_open','remote_keyword_search_repaired':False,'remote_root_cause':'not_established; known topic absent through tested minimal/nullable/global keyword requests','verified_replacement':'Complete competition topic enumeration, direct full-message retrieval, coverage validation and local text search','topics':9,'roots':9,'replies':12,'messages':21,'inventories_stable_before_after':True,'positive_control_topic':751543,'positive_control_found':True,'climate_matches':0,'general_temporal_context_matches':0,'retrieval_adverse_controls_rejected':4,'new_official_temporal_clarification_located':False,'absence_scope':'Nine listed public topics and their21retrieved messages at this cut; not every private source or edit history.','original_F05_index_preserved':rel(OLD),'new_feature_admission':False,'new_fits':0,'model_loads':0,'new_predictions':0,'new_scores':0,'new_numerical_diagnostics':0,'new_bootstrap':0,'row_values_read':0,'climate_parquet_opened':False,'reference':'W2-B00','all_alternatives_preserved':True,'target_exposure_C0_folds_changed':False,'G1_closed':False,'G2_closed':False,'2024_test_model_validation_opened':False,'prior_external2024_subject_exposure_disclosed':True,'professional_independent_validation':False,'night_window_reopened':False}
    dump(RUN/'review_result.json',result)
    doc=f'''# F05: búsqueda directa del foro y cobertura comprobada

Codex, corte UTC {result['utc']}. El fallo queda resuelto para esta revisión mediante una ruta alternativa verificada: enumerar los temas de cada competencia, recuperar directamente todos sus mensajes y buscar en ese texto. El buscador general de Kaggle sigue omitiendo el control conocido. No se afirma haber reparado su servidor ni determinado su causa interna.

## Método y cobertura

Las peticiones mínimas, con campos nullable y con título completo en la búsqueda general no recuperaron Claims Data Query, tema751543. La enumeración específica sí lo devuelve. Por eso las respuestas vacías generales se mantienen excluidas como evidencia de ausencia.

Se consultó list_competition_topics por slug de cada parte y se cotejó el número de entradas con total_count. Después se llamó get_forum_topic por cada ID, con el mensaje inicial y hasta100respuestas. Se verificaron ID y URL del mercado/competencia, mensaje inicial no vacío, IDs únicos y coincidencia entre respuestas recibidas, recuento del listado y total del servidor. Ningún tema excede ese límite; una discrepancia habría detenido la conclusión de cobertura.

| Ámbito | Temas y mensajes iniciales | Respuestas | Mensajes revisados |
| --- | ---: | ---: | ---: |
| Parte1 | 7 | 7 | 14 |
| Parte2 | 2 | 5 | 7 |
| Total | 9 | 12 | 21 |

El listado posterior conserva los mismos IDs, recuentos y fechas del último comentario que el inicial. Esto concilia el corte de consulta; no demuestra una transacción atómica del servidor ni conserva historial de ediciones. El control positivo encuentra Claims Data Query por su título y su respuesta directa contiene el mensaje inicial. El control negativo sin coincidencias y cuatro controles adversos del nuevo lector verifican rechazo de tema faltante, URL de otra competencia, respuesta faltante e ID de mensaje duplicado. Son controles de recuperación, no nuevos diagnósticos de datos o modelos.

La ruta quedó implementada en herramientas/buscar_aclaraciones_foro_seguro.mjs. Recibe los inventarios completos y las respuestas directas obtenidas con Kaggle MCP, valida cobertura antes de buscar y guarda hashes/autor/ID/UTC. No llama al buscador general. Se probó con el flujo real recuperado, además de los adversos. No se ejecutó ningún productor histórico ni se instaló otra dependencia.

## Aclaraciones de clima pendientes

Se buscaron referencias al clima, pronósticos, riesgos, los siete nombres de campos climáticos y términos asociados a viento, incendio, granizo, lluvia o temperatura. También se buscaron expresiones generales de información conocida, fecha de decisión, futuro y disponibilidad al cotizar que pudieran contener una aclaración sin nombrar weather. No se encontró una coincidencia climática o de ese contexto temporal en los21mensajes recibidos. No se presenta el resultado como una comprensión infalible de cualquier paráfrasis o una búsqueda universal de fuentes privadas.

Esta consulta cubre ahora los cuerpos de mensajes y respuestas de los nueve temas listados, que F05 anterior no había cubierto. No apareció una aclaración del organizador que cambie la interpretación de2023. Las definiciones oficiales ya consultadas y archivadas se reutilizan; no se vuelve a abrir el Parquet ni se repiten diagnósticos de clima.

Sigue faltando distinguir, por campo, agregado realizado, pronóstico o riesgo calculado previamente, con ventana, método, insumos, emisión/publicación y vigencia. Los agregados completos de2023 no estaban realizados al iniciar el año. El nombre de los índices de viento/incendio no acredita su disponibilidad previa ni demuestra fuga por sí solo. El año de referencia, la fecha de subida del archivo y una fecha de cotización derivada no sustituyen la fecha de conocimiento del dato.

Se conserva el rechazo prospectivo anterior de CLIMA-S2-01 y el hallazgo S2-VAL-DAT-003 con su responsable. Ninguna variable se añade a B20, ni se rellena historia con otro mercado o años posteriores. La revisión no establece G1 o resuelve G2 y no justifica una nueva prueba de precios.

## Registro y límites

Se guardaron hashes del texto y de la fuente canónica por mensaje/tema, autores, IDs, UTC, recuentos, estabilidad del inventario y recibos de búsqueda. Los cuerpos ajenos no relacionados con clima se procesaron en memoria y no se publican o archivan completos; no se emitieron métricas ajenas. Una revisión posterior de otras expresiones requeriría recuperar la fuente y cotejar su hash. No se atribuye a estos recibos un replay íntegro sin volver a consultar el texto.

La limitación antigua del buscador se conserva como evidencia histórica en [F05 inicial](F05_CLIMA_2023_Y_DISPONIBILIDAD_TEMPORAL.md); este seguimiento sustituye su límite de cobertura de los comentarios para el corte indicado. B00 y todas las alternativas, T0/C0, exposición, folds, modelos y contadores siguen intactos. Cero entrenamiento, cargas de modelos, inferencias, scores, remuestreos o filas de datos leídas.2024/test/ledger/actas/SEL01 permanecen cerrados para modelado y confirmación. La exposición histórica de un asunto externo sigue declarada, sin usar sus métricas o afirmar ceguera completa. La ventana nocturna continúa cerrada, sin contactos externos, otros chats, delegación o automatizaciones nuevas. Codex firma revisión propia de recuperación/fuentes, sin aprobación humana o validación profesional independiente.

El [índice del seguimiento](../../registro/{INDEX.name}) enlaza recibos, código, controles, decisiones y fuentes con SHA. Los temas oficiales están en los foros de [parte1](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1/discussion) y [parte2](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/discussion); el control es [Claims Data Query](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1/discussion/751543).
'''
    for a,b in [('tema751543','tema 751543'),('hasta100respuestas','hasta 100 respuestas'),('Parte1','Parte 1'),('Parte2','Parte 2'),('parte1','parte 1'),('parte2','parte 2'),('los21mensajes','los 21 mensajes'),('de2023','de 2023'),('leídas.2024','leídas. 2024')]:doc=doc.replace(a,b)
    with DOC.open('x',encoding='utf-8') as f:f.write(doc)
    decisions=[('F05R-01','Buscador general sigue fallando control conocido; causa interna no acreditada, no afirmar reparación remota.'),('F05R-02','Usar listado por competencia y consulta directa de todos los mensajes, con cobertura y ámbito comprobados antes de buscar.'),('F05R-03','Corte conciliado:9temas,9iniciales,12respuestas,21mensajes; controles positivo/negativo y4adversos de recuperación, sin ML.'),('F05R-04','No aclaración climática o contextual temporal localizada en el corpus recibido; límites de cobertura universal y paráfrasis declarados.'),('F05R-05','Conservar F05 inicial y requisitos temporales, rechazo CLIMA-S2-01 y responsable del hallazgo; no nueva admisión o cierre G1/G2.'),('F05R-06','Preservar B00/alternativas,T0/C0/folds/modelos/contadores;2024cerrado,sin entrenamiento o otros diagnósticos.')]
    dump(RUN/'decision_journal.json',{'id':IDENT,'author':'Codex','utc':now(),'decisions':[{'id':k,'decision':v} for k,v in decisions]})
    fp=RUN/'forum_057.md'
    with fp.open('x',encoding='utf-8') as f:f.write(f'''Codex, seguimiento solicitado a F05/foro056. Informe: {rel(DOC)}. Índice: {rel(INDEX)}. Recibos y código de recuperación: {rel(RUN)} y herramientas/buscar_aclaraciones_foro_seguro.mjs.

El buscador general continúa omitiendo el tema conocido751543 con peticiones mínimas, nullable o título completo; no atribuyo causa interna ni reparación del servidor. Resuelvo el acceso para esta revisión con listado completo por competencia, recuperación directa de cada tema/mensajes y búsqueda local validada. El control positivo Claims Data Query sí aparece y se recupera su cuerpo; no uso vacíos generales para afirmar ausencia.

Cobertura real: parte1,7temas/7respuestas; parte2,2temas/5respuestas; total9iniciales+12respuestas=21mensajes. Recuentos,IDs,URL de competencia y mensajes no vacíos concilian con listado/servidor. Inventario antes/después estable en IDs,recuentos y último comentario. El módulo rechaza tema faltante,URL ajena,respuesta faltante e ID duplicado; negativo sin coincidencias. Controles de recuperación, no diagnósticos numéricos o de modelos repetidos.

No encontré coincidencias climáticas, de los siete campos o del contexto temporal amplio en esos21mensajes. Ahora se cubren también los comentarios que F05 no había revisado; no se afirma ausencia universal o detección perfecta de cualquier paráfrasis. Diccionarios anteriores reutilizados, sin abrir weather.parquet. Siguen pendientes ventana,método/insumos,observado/pronóstico/hazard previo y fechas de emisión/publicación/vigencia. No nueva admisión o cambio del rechazo prospectivo CLIMA-S2-01; S2-VAL-DAT-003 conserva responsable. G1/G2sin cierre.

Hashes por fuente/mensaje,autor,ID,UTC y cobertura guardados; cuerpos ajenos no climáticos procesados en memoria, no emitidos o archivados completos. F05 inicial conservada con su fallo histórico; el seguimiento sustituye su límite de comentarios para este corte. Sin aprobación humana o validación profesional independiente.

F05R-01 a F05R-06, autor Codex. B00 y alternativas,T0/C0/exposición/folds/modelos/contadores intactos.2024/test/ledger/actas/SEL01 cerrados; cero filas,entrenamiento,cargas,inferencias,scores,remuestreos o nuevos diagnósticos de datos/modelos. Ventana nocturna cerrada, sin contactos externos,nuevos chats,delegación o automatizaciones.
''')
    proc=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',FID,'--asunto','F05: búsqueda directa verificada en 21 mensajes, sin aclaración climática nueva','--cuerpo',str(fp)],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr;dump(RUN/'forum_receipt.json',json.loads(proc.stdout))
    idx={**result,'path_base':'workspace_root','run':rel(RUN),'documentation':rel(DOC),'documentation_sha256':sha(DOC),'forum_result':FID}
    for key,name in [('receipt','direct_search_receipt.json'),('guards','retrieval_guard_checks.json'),('sources','source_manifest.json'),('decisions','decision_journal.json')]:idx[key]={'path':rel(RUN/name),'sha256':sha(RUN/name)}
    idx['code']={'path':rel(REPO/'herramientas/buscar_aclaraciones_foro_seguro.mjs'),'sha256':sha(REPO/'herramientas/buscar_aclaraciones_foro_seguro.mjs')}
    dump(INDEX,idx);changes=[]
    def change(p,fn):
        before=p.read_bytes();after=fn(before.decode('utf-8-sig')).encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        for phase,b in [('before',before),('after',after)]:
            q=RUN/'registration_cuts'/phase/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as f:f.write(b)
        tmp=p.with_name(p.name+'.F05direct.tmp')
        with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert p.read_bytes()==before,'Concurrent change '+rel(p);os.replace(tmp,p)
        changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p)})
    def source_update(raw):
        d=json.loads(raw)
        vals={'F05_previous_review_index':d['F05_review_index'],'F05_review_index':rel(INDEX),'F05_status':result['status'],'F05_completed_utc':now(),'F05_direct_forum_search_verified_at_cut':True,'F05_direct_search_messages':21,'F05_remote_keyword_search_repaired':False,'F05_new_temporal_clarification_located':False}
        for k,v in vals.items():raw=top(raw,k,v)
        return raw
    change(SOURCE,source_update)
    change(ROOT/'Preparación/ESTADO_PROYECTO.json',lambda raw:top(raw,STATEKEY,idx))
    section=f'''\n\n## F05: búsqueda directa del foro verificada

Codex, UTC {now()}, foro057, decisiones F05R-01 a F05R-06. Informe {rel(DOC)}, índice {rel(INDEX)}, recibos/controles/hashes en {rel(RUN)}. Ruta general aún omite control Claims751543 con petición mínima,nullable y título completo; causa interna no establecida, sin afirmar reparación del servidor. Sustitución funcional verificada: listado por competencia, todos los temas/mensajes directos y búsqueda local. Nueve temas/iniciales,doce respuestas,21mensajes,con recuentos/IDs/URL/raíces conciliados e inventarios antes/después estables. Positivo encontrado,negativo sin coincidencias; cuatro adversos nuevos de recuperación rechazados. Código buscar_aclaraciones_foro_seguro.mjs probado con flujo real, no nuevos diagnósticos ML.

Sin coincidencias climáticas o de contexto temporal amplio en el corpus. Cubiertos los comentarios antes pendientes; no ausencia universal o detección perfecta de paráfrasis. F05 anterior preservada histórica, requisitos de método,ventana,vintage/fechas y rechazo CLIMA-S2-01 intactos; S2-VAL-DAT-003 conserva responsable. Sin nueva admisión o cierre G1/G2. Fuentes públicas procesadas en memoria; solo hashes,autor/ID/UTC,recuentos y contexto coincidente conservados, sin cuerpos ajenos no relacionados. Otra consulta requiere recuperar/cotejar fuente, no replay íntegro sin texto.

B00/alternativas,T0/C0/exposición/folds/modelos/contadores conservados.2024/test/SEL01/actas/ledger cerrados y exposición de asunto externo previa declarada sin usar métricas. Cero filas,entrenamiento,cargas,inferencias,scores,remuestreos o nuevos diagnósticos de datos/modelos. Ventana/automatización nocturna cerradas; sin contactos externos,otros chats,delegación o programación. Revisión propia de recuperación/fuentes de Codex,no aprobación humana o validación profesional independiente.\n'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+section)
    def routes_update(raw):
        d=json.loads(raw)
        vals={'week_2_F05_initial_climate_search_index':d['week_2_F05_climate_search_index'],'week_2_F05_initial_climate_search_report':d['week_2_F05_climate_search_report'],'week_2_F05_climate_search_index':rel(INDEX),'week_2_F05_climate_search_report':rel(DOC),'week_2_F05_forum_search_index':rel(INDEX),'week_2_F05_forum_search_report':rel(DOC)}
        for k,v in vals.items():raw=top(raw,k,v)
        return raw
    change(ROOT/'RUTAS_PROYECTO.json',routes_update)
    checks={'id':IDENT,'utc':now(),'source_copies_intact':all(sha(ROOT/x['snapshot'])==x['sha256'] for x in sources),'original_F05_model_counter_night_sources_unchanged':all(sha(ROOT/x['path'])==x['sha256'] for x in sources if not x['intentional_mutable_source_index']),'public_source_counts_consistent':sum(len(x['messages']) for x in receipt['indexed'])==21,'scope':'Documentary/retrieval integration; no new climate/model diagnostics.'}
    assert all(v for v in checks.values() if isinstance(v,bool))
    dump(RUN/'documentary_integrity_receipt.json',checks)
    dump(RUN/'registration.json',{'changes':changes,'original_F05_mutations':0,'price_catalog_mutations':0,'counter_mutations':0,'feature_contract_mutations':0,'model_code_mutations':0,'night_index_mutations':0})
    files=[p for p in RUN.rglob('*') if p.is_file()]+[INDEX,DOC,Path(__file__).resolve(),REPO/'herramientas/buscar_aclaraciones_foro_seguro.mjs']
    dump(RUN/'manifest.json',{'id':IDENT,'utc':now(),'files':[{'path':rel(p),'sha256':sha(p)} for p in files]})
    print(json.dumps({'id':IDENT,'forum_result':FID,'document':rel(DOC),'topics':9,'messages':21,'direct_search_verified':True,'remote_keyword_repair_claimed':False,'new_climate_clarification':False,'new_fits':0,'integrity':checks},ensure_ascii=True))

if __name__=='__main__':main()
