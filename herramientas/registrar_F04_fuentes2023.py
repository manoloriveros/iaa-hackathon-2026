"""Registra búsqueda F04 finita y trazable, sin datos por fila ni productores."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,re,sys,subprocess
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/revision_F04_2023/f04_20261024_v1'
DOC=REPO/'docs/archivo/semana2/F04_BUSQUEDA_MOVIMIENTOS_Y_COHORTE_2023.md'
INDEX=REPO/'registro/semana2_F04_fuentes2023_actual.json'
SOURCE=REPO/'registro/semana2_b20_fuentes2023_actual.json'
IDENT='S2-F04-FUENTES2023-v1-20261024';FID='COD-S2-20261024-055'
KEY='week_2_F04_claim_movements_cohort2023_v1_20261024'
now=lambda:datetime.now(timezone.utc).isoformat()
rel=lambda p:p.relative_to(ROOT).as_posix()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))

def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

def top(raw,key,value):
    val=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+val+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+val+raw[m.end()+end:]

def main():
    assert not INDEX.exists() and not DOC.exists()
    ev=read(RUN/'search_evidence.json');c=ev['official_catalog_comparison']
    assert c['current_files']==24 and not any(c[x] for x in ['names_added','names_removed','changed_size','changed_creation_date'])
    assert ev['dictionary_unchanged'] and ev['row_values_decoded']==0
    assert all(x['matches_historical_developed'] for x in ev['legacy_root_training_aliases'])
    paths=[SOURCE,REPO/'registro/semana2_b20_fuentes2023_plan_v1.json',REPO/'registro/semana2_F03_desarrollado2023_actual.json',REPO/'registro/semana2_contenido_oficial_actual.json',REPO/'registro/semana2_b20_mecanismo_soporte_revision_actual.json',REPO/'registro/semana2_b20_soporte_folds_actual.json',REPO/'registro/semana2_desarrollo2023_actual.json',REPO/'registro/semana2_contadores_propios_actual.json',REPO/'registro/semana2_continuidad_nocturna.json',REPO/'privado/semana2/revision_F03_2023/f03_20261024_v1/schema_dictionary_receipt.json',ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/data_manifest.json']
    sources=[]
    for i,p in enumerate(paths):
        q=RUN/'sources'/f'{i:02d}_{p.name}';q.parent.mkdir(exist_ok=True)
        with q.open('xb') as f:f.write(p.read_bytes())
        sources.append({'path':rel(p),'snapshot':rel(q),'sha256':sha(p),'intentional_mutable_source_index':p==SOURCE})
    dump(RUN/'source_manifest.json',{'id':IDENT,'utc':now(),'sources':sources,'metadata_request':'official_file_inventory.json','current_raw_data_downloads':0,'claim_schema_reused_not_reaudited':True,'binary_active_content_audit_reused':'F01','root_alias_identity_only':'Four newly disambiguated legacy root claim/policy files; streamed opaque hash, no row decoding.'})
    gates=[
      {'id':'F04-M','source':'Movements or multiple valuation cuts of emerging occurrence2023 claims','required':['Legitimate published source and version/checksum, availability date and valuation/capture dates.','Market-scoped claim/policy IDs, line/peril/loss_date2023 and assignment to covered period; reversals/reopenings identified.','Cumulative-versus-incremental convention, payment/case/recovery/status fields, currency/units/netting and reconciliation across cuts.','Receipt limited to2023 occurrence, no other-year model/confirmation artifacts.'],'could_inform':'Reporting/reserve/recovery development and observation assumptions; repeated claim cuts do not add independent groups.','status':'not_located'},
      {'id':'F04-C','source':'Legitimate additional emerging2023 cohort','required':['Official or documented lawful provenance, cohort design, capture/valuation and availability dates, raw version/checksum.','Policies including claim-free exposure, periods/exposure/coverage and linked claims; customer/address links needed for group overlap.','Show actual additional information versus prior files; overlapping row/claim/customer-address components remain linked, not independent duplicates.','Same target/exposure definitions or documented differences; preserve saved artifacts and preregister any later analytical proposal.'],'could_inform':'Additional real information/components or changed cost evidence; no automatic support pass or model promotion.','status':'not_located'}]
    dump(RUN/'future_source_requirements.json',{'id':IDENT,'author':'Codex','utc':now(),'requirements':gates,'scope':'Reception/provenance design only, not permission to download mixed-year rows, train or score.'})
    result={'id':IDENT,'author':'Codex','utc':now(),'scope':'F04 bounded source search: official catalog/dictionary/discussions, two public dataset queries, local data inventories and identity of four legacy aliases; no row values','official_files':24,'official_inventory_metadata_changed':False,'dictionary_changed':False,'new_claim_movements_located':False,'new_emerging2023_cohort_located':False,'absence_claim':'No source located in named surfaces at this cut; not proof of universal nonexistence.','host_notice':{'topic':752091,'message':3543802,'utc':'2026-10-24T03:12:10.750Z','meaning':'HOST says an old folder duplicated developed data and was removed to address download-all issue; not an announcement of new claims/cohort.','internal_cause_or_download_fix_independently_certified':False},'legacy_root_claim_policy_aliases_verified_developed':4,'active_binary_audit_repeated':False,'new_raw_downloads':0,'row_values_decoded':0,'new_fits':0,'model_loads':0,'new_predictions':0,'new_scores':0,'new_numerical_diagnostics':0,'new_bootstrap':0,'new_emerging_components':0,'G1':'plausible_not_established_unchanged','G2':'heldout_support_failure_unchanged','reference':'W2-B00','all_alternatives_preserved':True,'target_exposure_C0_folds_changed':False,'2024_test_model_validation_opened':False,'prior_external2024_subject_exposure_disclosed':True,'night_window_reopened':False,'professional_independent_validation':False}
    dump(RUN/'review_result.json',result)
    doc=f'''# F04: búsqueda de movimientos y cohorte emergente de 2023

Codex, corte UTC {result['utc']}. No se localizó un historial de movimientos, otro corte de valoración de siniestros de ocurrencia 2023 o una cohorte emergente adicional con procedencia acreditada. F04 queda buscada en las fuentes delimitadas y pendiente de disponibilidad. Esto no demuestra que el organizador carezca de otros registros; tampoco modifica los bloqueos de B20.

## Búsqueda y hallazgos

| Fuente examinada | Evidencia del corte | Resultado para F04 |
| --- | --- | --- |
| Catálogo oficial completo, Kaggle MCP, página de hasta 200 entradas sin continuación | 24 archivos; mismos nombres, tamaños y fechas que la consulta anterior | No se anuncia un archivo de movimientos, un segundo corte o una cohorte adicional |
| [Diccionario oficial](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/data) | Texto idéntico al archivado; claims sigue descrito como un registro por siniestro al 31-12-2024 | Un único snapshot, sin historial de transacciones documentado |
| Discusiones de la competencia, orden reciente | La respuesta devuelve dos temas y total_count=2; uno de descarga y otro de formato de envío | No aparece una publicación de datos suplementarios en esa lista |
| [Tema de descarga 752091](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/discussion/752091) | HOST, mensaje 3543802 del 24 a las 03:12:10.750 UTC: retiró una carpeta antigua que duplicaba el mercado desarrollado para intentar resolver la descarga conjunta | Aclaración de empaquetado; no anuncia nuevos siniestros, movimientos o cohortes |
| Dos búsquedas públicas de datasets en Kaggle | Consulta exacta del hackathon devuelve objeto vacío; IAA 2026 devuelve siete metadatos sin vínculo acreditado con esta cartera | Ningún candidato admisible identificado; relevancia y resultados de búsqueda no son un censo universal |
| Directorios locales Semana 2/Datos y Datos/emerging | Inventario de nombres/tamaños; 13 archivos en emerging y archivos históricos en la raíz | No hay un fichero adicional identificado como movimientos/cohorte |
| Cuatro archivos locales de siniestros y pólizas fuera de emerging | SHA256 binario coincide con el manifiesto histórico desarrollado para claims y las tres pólizas | Son alias históricos desarrollados, no una cartera emergente nueva |

El conector integrado no expone el catálogo de archivos. Se usó el cliente MCP local existente con acceso de red aprobado para una sola petición de metadatos, sin instalar dependencias o descargar tablas. No se repitió la descarga/comparación binaria de los 24 originales de F01. La igualdad binaria de aquella revisión conserva su fecha y alcance; metadatos iguales por sí solos no son una prueba nueva de bytes. Los cuatro hashes locales resuelven una ambigüedad distinta, los alias de la raíz, sin decodificar filas o consultar estadísticas de Parquet.

El aviso del HOST se conserva con autor, fecha y mensaje. Es una explicación publicada de la retirada de duplicados, no una verificación interna de la causa de todos los cambios ni una certificación de que ya funcione la descarga conjunta. No se reabre la incidencia de envío ni se hacen sondas, envíos o cotejos de test. Los datasets homónimos no se descargan ni se admiten por semejanza del título. La cartera y geografía son sintéticas; no hay enlace documentado a siniestros reales externos de 2023.

## Por qué claims no permite reconstruir movimientos

Se reutilizó el esquema de siniestros de F03, sin volver a leer el Parquet. Hay fechas de ocurrencia y reporte, estado, paid_to_date, incurred_to_date y recoveries. No aparecen fecha/identificador de transacción, fecha de cada revisión de reserva, pagos individuales, reaperturas o varios cortes de valoración por claim_id. La fecha de reporte no fecha cada cambio de los importes.

Pago acumulado e incurrido al mismo corte no son dos valoraciones independientes. La diferencia entre incurrido y pago representa la reserva del corte bajo la definición del diccionario; no revela su trayectoria, suficiencia o coste final. Tampoco se reconstruyen reportes aún no observados. No se calculó esa diferencia ni se fabricaron movimientos interpolando importes, simulando colas o remuestreando los mismos siniestros.

## Qué tendría que traer una fuente útil

Para movimientos o cortes sucesivos se necesitan procedencia legítima y versión, fechas de disponibilidad/valoración, claves del mismo mercado y definición acumulada o incremental de pagos, reservas y recuperos. Deben identificarse reversiones, reaperturas y cambios de estado y poder conciliarse importes entre cortes, sin descontar dos veces franquicias o recuperaciones. La recepción se limitaría a ocurrencias de 2023 y a su cobertura; no abriría precios, actas o resultados de la cohorte 2024.

Esa fuente podría separar maduración de siniestros y cambios de reservas del riesgo que intenta captar B20. Varias observaciones del mismo claim_id mejorarían información de desarrollo, pero no serían nuevos siniestros o componentes independientes. No demostrarían por sí solas el último ni un fallo de dispersión del modelo.

Una cohorte emergente adicional necesitaría pólizas y periodos/exposiciones, incluidos los casos sin siniestros, junto con siniestros y vínculos de cliente/dirección. Un listado de pérdidas por sí solo no aporta el denominador del riesgo. Debe acreditarse que es información realmente distinta, conservando solapamientos de siniestro, póliza y componente entre fuentes; identificadores nuevos no garantizan independencia. Fecha de disponibilidad, valoración, cobertura, unidad y objetivo también deben documentarse.

Una cohorte legítima podría aportar componentes o información adicional, pero no garantiza superar el criterio de soporte. Una corrección material de costes podría cambiar la evidencia de los mismos grupos sin añadir grupos nuevos. Cualquier análisis posterior mantendría versiones y criterios previos, con hipótesis, comparador estándar y ámbito autorizado antes de ajustar o puntuar. Este registro de recepción no autoriza una nueva prueba.

## Decisión y continuidad

F04 sigue no disponible en las superficies consultadas. No se abre una prueba por ausencia de información ni se relajan bandas, umbrales o reglas; no se excluyen siniestros. G1 permanece plausible y no establecido; G2 conserva el incumplimiento ya medido. No se reejecutaron esos diagnósticos, C0, replays, suites o remuestreos. Tampoco se mezcló desarrollado con emergente.

El siguiente paso depende de una publicación legítima o corrección material documentada. Entonces correspondería revisar primero su procedencia, fechas, claves y diferencias, con extracción estricta de 2023 antes de analizar valores. No se programa vigilancia nueva, contacta al organizador o prolonga la ventana nocturna.

B00 y todas las alternativas, T0/C0, exposición, folds, modelos y contadores se conservan. Cero filas decodificadas, entrenamiento, cargas de modelos, inferencias, precios o scores nuevos. 2024/test/ledger/actas/SEL01 siguen cerrados para modelado y confirmación. La exposición histórica de un asunto externo permanece declarada, sin repetir o usar métricas. Revisión de procedencia propia de Codex, no aprobación humana ni validación profesional independiente. Las prácticas IAA de documentación §2 y gobernanza §2.8 orientan esta delimitación de fuente y alcance.

El [índice F04](../../registro/{INDEX.name}) enlaza recibos de consulta, búsqueda y requisitos de recepción, fuentes con SHA y decisiones. Se conservan [F01](VERIFICACION_CONTENIDO_KAGGLE_20261024.md), [F03](F03_DESARROLLADO_2023_Y_MECANISMO_B20.md) y el [plan histórico](FUENTES_2023_Y_PLAN_REVISION_B20.md) sin reescribirlos.
'''
    with DOC.open('x',encoding='utf-8') as f:f.write(doc)
    decisions=[('F04-01','No localizar fuente en un alcance definido no demuestra inexistencia universal; F04 pendiente de disponibilidad.'),('F04-02','HOST3543802 explica retirada de duplicado desarrollado, no anuncia movimientos/cohorte ni acredita causa interna o descarga resuelta.'),('F04-03','Reutilizar F01/F03; solo cuatro alias de raíz recibieron hash para resolver procedencia distinta, sin filas o nuevo diagnóstico.'),('F04-04','Snapshot, fechas de reporte y reservas actuales no reconstruyen transacciones/cortes o último; no fabricar información faltante.'),('F04-05','Futura recepción exige origen,fechas,versión,claves,convenciones y exposición; movimientos repetidos no son componentes nuevos.'),('F04-06','G1/G2 intactos; no prueba,relajación,promoción o retiro. B00/alternativas conservados,2024cerrado.')]
    dump(RUN/'decision_journal.json',{'id':IDENT,'author':'Codex','utc':now(),'decisions':[{'id':k,'decision':v} for k,v in decisions]})
    fp=RUN/'forum_055.md'
    with fp.open('x',encoding='utf-8') as f:f.write(f'''Codex, F04 solicitada. Búsqueda finita de movimientos/cortes de siniestros de ocurrencia 2023 o cohorte emergente adicional. Informe: {rel(DOC)}. Recibos y requisitos: {rel(RUN)}.

No localicé una fuente admisible en las superficies examinadas. Catálogo oficial completo: mismos 24 nombres/tamaños/fechas, sin continuación. Diccionario vigente idéntico, claims a un único corte 31-12-2024. Discusiones: dos temas, sin anuncio de datos suplementarios en esa lista. Dos búsquedas públicas de datasets no aportaron vínculo acreditado con esta cartera. Ausencia acotada a la búsqueda, no prueba de que no existan otros registros.

En tema752091, HOST3543802,24-10 03:12:10.750UTC, informa retirada de carpeta antigua duplicada de desarrollado para intentar resolver descarga conjunta. Se archiva autor/fecha/texto: no anuncia cohorte/movimientos ni se certifica causa interna o arreglo efectivo. La incidencia de envío no se reabre. No se descargaron tablas ni hicieron sondas.

Inventario local Datos/emerging:13 archivos. Los cuatro claims/policies de la raíz Semana2/Datos coinciden por SHA256 con el manifiesto histórico desarrollado: alias, no nueva cohorte emergente. Esta identidad puntual resuelve una ambigüedad distinta; no se repite auditoría binaria de originales activos F01. Solo bytes opacos, cero filas de cualquier año interpretadas. Esquema claims reutilizado de F03: ocurrencia/reporte y acumulados a corte no permiten reconstruir pagos, revisiones/reaperturas o desarrollo de reservas.

Para retomar F04 haría falta publicación legítima con versión/fechas de disponibilidad y valoración, claves de ocurrencia2023 y convenciones de importes. Movimientos aportarían información sobre observación/maduración, no nuevos componentes independientes del mismo siniestro. Cohorte adicional necesita también exposición sin siniestros y enlaces cliente/dirección, prueba de novedad y solapamientos conservados. Más datos no garantizan superar soporte; no se fabrica información por simulación/remuestreo.

F04-01 a F04-06, Codex. G1 plausible/no establecido y G2 incumplido sin cambio. No hay base nueva localizada para otra prueba. B00 y alternativas,T0/C0/exposición/folds/modelos/contadores intactos.2024/test/ledger/actas/SEL01 cerrados; sin entrenamiento,cargas,inferencias,scores,diagnósticos repetidos o ajustes de reglas. Sin mensajes externos,delegación,nuevos chats o automatizaciones. Ventana nocturna cerrada. Revisión de procedencia propia,no aprobación humana o validación profesional independiente.
''')
    proc=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',FID,'--asunto','F04: búsqueda acotada sin movimientos o cohorte emergente adicional localizada','--cuerpo',str(fp)],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr;dump(RUN/'forum_receipt.json',json.loads(proc.stdout))
    idx={**result,'path_base':'workspace_root','status':'F04_search_completed_source_not_located_in_named_surfaces_no_new_trial','run':rel(RUN),'documentation':rel(DOC),'documentation_sha256':sha(DOC),'forum_result':FID}
    for key,name in [('search_evidence','search_evidence.json'),('requirements','future_source_requirements.json'),('source_manifest','source_manifest.json'),('decision_journal','decision_journal.json')]:idx[key]={'path':rel(RUN/name),'sha256':sha(RUN/name)}
    dump(INDEX,idx);changes=[]
    def change(p,fn):
        before=p.read_bytes();after=fn(before.decode('utf-8-sig')).encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        for phase,b in [('before',before),('after',after)]:
            q=RUN/'registration_cuts'/phase/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as f:f.write(b)
        tmp=p.with_name(p.name+'.F04review.tmp')
        with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert p.read_bytes()==before,'Concurrent change '+rel(p);os.replace(tmp,p)
        changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p)})
    def source_update(raw):
        for k,v in {'F04_status':idx['status'],'F04_review_index':rel(INDEX),'F04_completed_utc':now(),'F04_claim_movements_located':False,'F04_new_emerging2023_cohort_located':False}.items():raw=top(raw,k,v)
        return raw
    change(SOURCE,source_update)
    change(ROOT/'Preparación/ESTADO_PROYECTO.json',lambda raw:top(raw,KEY,idx))
    section=f'''\n\n## F04: búsqueda de movimientos y cohorte emergente de 2023

Codex, UTC {now()}, foro055, decisiones F04-01 a F04-06. Informe {rel(DOC)}, índice {rel(INDEX)}, evidencia/recibos/requisitos en {rel(RUN)}. Búsqueda acotada: catálogo oficial completo de 24 archivos sin cambio de nombre/tamaño/fecha, diccionario idéntico, dos temas de discusión devueltos y dos búsquedas públicas de datasets sin fuente vinculada acreditada. Datos locales inventariados; cuatro alias de claims/pólizas de raíz cotejados por SHA opaco con manifiesto histórico desarrollado, sin filas o repetir auditoría F01. No se localizaron movimientos,otro corte o cohorte emergente2023 adicional; no es prueba de inexistencia universal.

HOST3543802 en tema752091,24 a03:12:10.750UTC, informó retirada de carpeta antigua duplicada desarrollada para intentar resolver descarga conjunta. Aclaración publicada de empaquetado,no nuevos siniestros o causa interna/solución efectiva certificadas; no se reabre envío. Esquema claims reutilizado F03: acumulados a un corte y fecha de reporte no reconstruyen transacciones,reaperturas o reservas históricas. Futura recepción necesita fuente legítima,versión,disponibilidad/valoración,claves2023 y convenciones de importes; cohorte adicional necesita exposición sin siniestros y vínculos para no duplicar componentes. Repetir cortes de un siniestro aporta desarrollo,no nuevos grupos independientes.

F04 pendiente de disponibilidad. G1/G2 sin cambio,ninguna prueba nueva justificada por esta búsqueda. B00/alternativas,T0/C0/exposición/folds/modelos/contadores intactos. Cero descargas de tablas,filas decodificadas,entrenamiento,cargas,inferencias,scores,remuestreos o diagnósticos repetidos.2024/test/SEL01/actas/ledger cerrados; exposición previa de asunto externo declarada sin usar métricas. Ventana/automatización nocturna cerradas; sin contactos externos,delegación o otra programación. Revisión de procedencia propia de Codex,no aprobación humana o validación profesional independiente.\n'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+section)
    change(ROOT/'RUTAS_PROYECTO.json',lambda raw:top(top(raw,'week_2_F04_source_search_index',rel(INDEX)),'week_2_F04_source_search_report',rel(DOC)))
    checks={'id':IDENT,'utc':now(),'source_snapshots_intact':all(sha(ROOT/x['snapshot'])==x['sha256'] for x in sources),'original_model_counter_night_sources_unchanged':all(sha(ROOT/x['path'])==x['sha256'] for x in sources if not x['intentional_mutable_source_index']),'catalog_complete':not read(RUN/'official_file_inventory.json')['has_more_pages'],'legacy_aliases_resolved_without_rows':all(x['matches_historical_developed'] for x in ev['legacy_root_training_aliases']),'source_search_not_predictive_validation':True}
    assert all(v for v in checks.values() if isinstance(v,bool))
    dump(RUN/'documentary_integrity_receipt.json',checks)
    dump(RUN/'registration.json',{'changes':changes,'price_catalog_mutations':0,'counter_mutations':0,'feature_contract_mutations':0,'model_code_mutations':0,'night_index_mutations':0})
    files=[p for p in RUN.rglob('*') if p.is_file()]+[INDEX,DOC,Path(__file__).resolve(),REPO/'herramientas/inventariar_fuentes_F04.py',REPO/'herramientas/revisar_catalogo_F04.py']
    dump(RUN/'manifest.json',{'id':IDENT,'utc':now(),'files':[{'path':rel(p),'sha256':sha(p)} for p in files]})
    print(json.dumps({'id':IDENT,'forum_result':FID,'document':rel(DOC),'movements_found':False,'new_cohort_found':False,'new_fits':0,'decoded_rows':0,'integrity':checks},ensure_ascii=True))

if __name__=='__main__':main()
