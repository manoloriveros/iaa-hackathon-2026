"""Actualiza las entradas comunes conservando copia previa y guardas de SHA."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import re
import os

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
STAMP=datetime.now(timezone.utc).isoformat()
BOGOTA=datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()
BACK=BASE/'respaldo_apertura'
BACK.mkdir(exist_ok=False)
changes=[]

def digest(b): return hashlib.sha256(b).hexdigest()

def replace_value(raw,key,value):
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw)
    assert m, key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():])
    value=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    return raw[:m.end()]+value+raw[m.end()+end:]

def add_value(raw,key,value):
    assert key not in json.loads(raw),key
    index=raw.rfind('}')
    encoded=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    return raw[:index].rstrip()+',\n  '+json.dumps(key)+': '+encoded+'\n}\n'

def change(relative,transform):
    path=ROOT/relative
    before=path.read_bytes()
    target=BACK/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f: f.write(before)
    after=transform(before.decode('utf-8-sig')).encode('utf-8')
    assert path.read_bytes()==before, f'Cambio concurrente: {relative}'
    stage=path.with_name(path.name+'.apertura-s2.tmp')
    with stage.open('xb') as f:
        f.write(after);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before, f'Cambio concurrente: {relative}'
    os.replace(stage,path)
    changes.append({'path':relative,'before_sha256':digest(before),'after_sha256':digest(after),'backup':target.relative_to(ROOT).as_posix()})

def paths(raw):
    additions={
        'week_2_root':'Hackaton/Semana 2',
        'week_2_data':'Hackaton/Semana 2/Datos',
        'week_2_emerging_data':'Hackaton/Semana 2/Datos/emerging',
        'week_2_developed_reference':'Hackaton/Semana 1/Datos',
        'week_2_forum':'Hackaton/Semana 2/Foro/FORO.md',
        'week_2_forum_protocol':'Hackaton/Semana 2/Foro/README.md',
        'week_2_plan':'Hackaton/Semana 2/PLAN_TRABAJO.md',
        'week_2_contract':'Hackaton/Semana 2/CONTRATO_SEMANA2.md',
        'week_2_initial_diagnostic':'Hackaton/Semana 2/Codex/diagnostico_inicial.json'}
    for k,v in additions.items():
        assert (ROOT/v).exists(),v
        raw=add_value(raw,k,v)
    return raw

def state(raw):
    old=json.loads(raw)
    block={
        'id':'S2-APERTURA-20261023','author':'Codex','as_of_utc':STAMP,'path_base':'workspace_root',
        'status':'reviewed_downloaded_diagnosed_plan_proposed_forum_open',
        'competition':'iaa-ai-assisted-hackathon-2026-part-2','competition_id':173773,
        'opened_utc':'2026-10-23T16:00:00Z','deadline_utc':'2026-10-31T03:59:59Z',
        'deadline_bogota':'2026-10-30T22:59:59-05:00','participant_entry_verified_native_mcp':True,
        'rules':'Hackaton/Semana 2/CONTRATO_SEMANA2.md','plan':'Hackaton/Semana 2/PLAN_TRABAJO.md',
        'forum':'Hackaton/Semana 2/Foro/FORO.md','first_comment':'COD-S2-20261023-001',
        'history_index':'Hackaton/Semana 2/Foro/historial/indice_semana1.json','history_comments':260,
        'existing_loose_files':'11 copies exact by SHA256 of week1, preserved in place',
        'emerging_originals':'Hackaton/Semana 2/Datos/emerging','downloaded_files':13,'downloaded_bytes':26562843,
        'download_manifest':'Hackaton/Semana 2/Codex/fuentes/download_manifest.json',
        'diagnostic':'Hackaton/Semana 2/Codex/diagnostico_inicial.json','extended_findings':'Hackaton/Semana 2/Codex/hallazgos_ampliados.json',
        'training_policy_rows':109296,'test_rows':209063,'raw_claim_rows':9258,
        'priorities':['exposure_units_452_above_one','36_unmatched_claims','market_namespaced_keys','feature_availability_weather2025','target_and_reserve_uncertainty','persistent_temporal_and_new_customer_validation','20_office_premiums'],
        'unresolved':['rules_page_still_part1_header_and_placeholders','sample_format_documented_csv_actual_parquet','weather_documented_2023_2024_actual_2023_2025','missing_emerging_comparison_site_commission','fixed_expense_partial_period_allocation','final_form_not_yet_linked','prize_eligibility_and_human_review'],
        'week1_final':'S41, preserve specific selection and evidence; no new live selection check',
        'no_new_training':True,'no_data_corrections':True,'no_submissions':True,'no_remote_training':True,'no_external_messages':True,'no_automation':True,'no_delegation':True,
        'plan_adopted_by_participant':False,
        'authorization_scope':'Review folders/data/problem/Kaggle, local downloads and analysis, propose work plan, open local forum with history',
        'previous_forum_state':old['collaboration_forum']}
    raw=replace_value(raw,'memory_as_of',BOGOTA)
    raw=replace_value(raw,'collaboration_forum',{'path_base':'workspace_root','path':block['forum'],'protocol':'Hackaton/Semana 2/Foro/README.md','status':'week2_active_local','requested_by_participant':True,'first_Codex_comment':block['first_comment'],'updated_utc':STAMP,'week1_forum_preserved':'foros/FORO.md','history_index':block['history_index'],'estimate_organization':'No new separation imposed; shared-code proposal in week2 plan','Claude_response_observed_in_week2':False})
    raw=add_value(raw,'current_phase',{'as_of_utc':STAMP,'phase':'week2_emerging_market_planning','current_state_key':'week_2_opening_20261023','historical_fields_notice':'Los bloques de semana 1 conservan sus cortes; para parte 2 usar esta entrada y el contrato nuevo.'})
    raw=add_value(raw,'week_2_opening_20261023',block)
    return raw

memory='''

## Apertura de semana 2: fuentes, datos emergentes y foro con historial, 23 de octubre de 2026

Codex atiende la solicitud directa de revisar carpetas, datos, problema y Kaggle, plantear análisis y tiempos e iniciar un foro con el historial. Parte 2 confirmada por MCP: competición 173773, cuenta inscrita, apertura 23oct16:00UTC y cierre31oct03:59:59UTC (30oct22:59:59Bogotá). Diez envíos diarios, D² Tweedie1,5 y rúbrica40/25/20/15; predicción solo emerging y veinte primas comerciales para el jurado. La página de reglas conserva título/enlace de parte1 y fechas incompletas. Formulario final aún sin enlace; elegibilidad documental pendiente. Temas y notebooks consultados devolvieron objetos vacíos, sin evidencia pública recuperada.

Los once Parquet sueltos de Semana2/Datos son idénticos a semana1 por SHA y se preservan. Se descargaron trece Parquet emerging (26.562.843bytes), con tamaños oficiales conciliados, hashes locales y lectura completa. Diagnóstico:109.296filas de entrenamiento,209.063test,9.258siniestros; cerca76%deltest son filas de clientes nuevos por ramo. Hay452exposiciones>1,36siniestros sin periodo (34anteriores a2023),clima2025 pese al diccionario2023–24 y comisión comparison_site vacía. Coinciden IDs entre mercados:752clientes/8.046direcciones sin identidad común; usar claves con mercado. No se aplica limpieza ni se construyen etiquetas finales.

Foro nuevo Hackaton/Semana2/Foro (la carpeta real lleva espacio: «Semana 2»), aporte COD-S2-20261023-001. Copia literal del foro previo al corte16:20:46UTC:260aportes,765.287bytes,SHA490abd45003d1cbe13add559312967f54f6ff9fd38785b158600e9a3e2d61560, índice y síntesis con autoría. Puente en el foro anterior COD-20261023-APERTURA-S2, sin alterar aportes ajenos. S41 y su selección se conservan; incertidumbre de reservas y revisión humana mantienen su alcance, sin transferir factores D100 o autorizaciones a emerging.

Plan propuesto en ../Hackaton/Semana 2/PLAN_TRABAJO.md:24octbase/objetivo/disponibilidad/particiones;25referencias emergentes;26–27transferencia y veinte primas comerciales;28congelar/reproducir;29informe/video conjuntos;30revisión y entrega, cierre interno sugerido17Bogotá. Calendario orientativo, no adoptado aún por el participante. Contrato, diagnóstico y fuentes en la misma semana; rutas añadidas al mapa raíz. La estructura común de código futuro se propone, no se modifica la receta de semana1.

Sin entrenamiento, inferencia de modelos, ajuste, envíos, publicación, mensajes externos, automatizaciones, instalaciones o delegación. Descarga y consultas autenticadas fueron lecturas; no hubo inscripción o cambio de cuenta. La revisión es propia de IA, no validación profesional independiente. Estado vigente: clave week_2_opening_20261023. Se conservan los cortes históricos anteriores.
'''

decision='''

## S2-APERTURA-20261023: revisión inicial y propuesta de trabajo del mercado emergente

Codex, por solicitud directa del participante del 23 de octubre de 2026. Se abre el foro local de segunda semana en ../Hackaton/Semana 2/Foro/FORO.md, con copia literal e índice de260aportes del foro anterior y síntesis firmada por Codex. Aporte COD-S2-20261023-001 y puente COD-20261023-APERTURA-S2. No se inventan respuestas ni acuerdo de otro asistente.

Se confirma el contrato de parte2 mediante MCP y el inventario mediante API de solo lectura. Los once archivos locales eran copias exactas de semana1; se conservan y se descargan los trece emergentes en Datos/emerging. Tamaño26.562.843bytes y hashes locales. El diagnóstico no aprueba la base:452exposiciones mayores que uno,36siniestros sin periodo,clima2025 con disponibilidad por aclarar,IDs coincidentes entre mercados y comisión comparison_site vacía.

Se propone en PLAN_TRABAJO.md conciliar objetivo y disponibilidad, fijar validación temporal y de población nueva, comparar modelos emergentes con transferencia controlada y preparar veinte primas comerciales. El plan incluye calendario hasta30oct y congelación técnica28oct. El cierre de plataforma es30oct22:59:59Bogotá; formulario final aún pendiente. Prima comercial y prima de riesgo se mantienen separadas. La fórmula comercial propuesta exige conciliar las unidades y asignar el gasto fijo en periodos parciales.

La autorización actual alcanza revisión, descarga local, análisis descriptivo, documentación y foro. No adopta el plan como decisión humana ni inicia modelado/envíos/remoto/publicación/delegación. S41 permanece como entrega final de semana1; sus factores, límites y autorizaciones no se transfieren automáticamente. Reglas conservadas con sus discrepancias; revisión humana y elegibilidad siguen pendientes. Evidencia: carpeta Codex de Semana 2, contrato, diagnóstico, manifiesto, recibos de foro y copia previa de los archivos comunes.
'''

change('RUTAS_PROYECTO.json',paths)
change('Preparación/ESTADO_PROYECTO.json',state)
change('Preparación/MEMORIA_PROYECTO.md',lambda raw:raw.replace('\n', '\n\nActualización vigente del 23 de octubre: la segunda semana ya fue consultada, sus trece archivos emergentes se descargaron y se abrió un foro con historial. Consultar [el plan](<../Hackaton/Semana 2/PLAN_TRABAJO.md>) y la entrada «Apertura de semana 2» al final; los avisos pendientes de acceso siguientes son cortes anteriores.\n',1)+memory)
change('Preparación/DECISIONES.md',lambda raw:raw+decision)
change('README.md',lambda raw:raw+'\n\n## Segunda semana activa, 23 de octubre de 2026\n\nLa entrada actual es [Semana 2](<Hackaton/Semana 2/README.md>), con [plan propuesto](<Hackaton/Semana 2/PLAN_TRABAJO.md>), [foro nuevo con historial](<Hackaton/Semana 2/Foro/FORO.md>) y [contrato revisado](<Hackaton/Semana 2/CONTRATO_SEMANA2.md>). Los trece archivos emerging están en Datos/emerging; los once archivos sueltos son copias de semana1, comprobadas por SHA. La selección vigente de parte1 es S41; las menciones S30/S22 anteriores conservan su corte histórico. Cierre de plataforma parte2:30oct22:59:59Bogotá; formulario final pendiente.\n')
change('Hackaton/REGLAS_2026.md',lambda raw:raw+'\n\n## Parte 2 verificada el 23 de octubre de 2026\n\nConsultar [el contrato operativo de semana 2](<Semana 2/CONTRATO_SEMANA2.md>) y sus fuentes archivadas. Competicíon173773, apertura23oct16UTC, cierre31oct03:59:59UTC (30oct22:59:59Bogotá). Predicciones solo para emerging2025, D² Tweedie1,5, diez envíos diarios y rúbrica40/25/20/15. El informe incorpora la construcción de prima comercial para veinte pólizas; el CSV sigue conteniendo prima de riesgo. Los límites de cinco páginas/cinco minutos cubren la entrega conjunta.\n\nLos trece Parquet emergentes están descargados. Las reglas de esta página conservan encabezado de parte1 y marcadores de calendario; metadatos de parte2 confirman el plazo, mientras el formulario final sigue sin enlace. Se conserva la discrepancia clima2023–24 documentado/2023–25 real y CSV documentado/plantilla Parquet real. Esta actualización sustituye la falta de acceso, enlace, datos y hora de cierre de parte2 de los cortes anteriores; no elimina sus otras ambigüedades ni acredita elegibilidad o revisión humana. La selección final específica de parte1 es S41.\n')
change('foros/README.md',lambda raw:raw+'\n\n## Foro de segunda semana abierto el 23 de octubre de 2026\n\nPor petición directa del participante, el intercambio de semana2 continúa en [el foro nuevo](<../Hackaton/Semana 2/Foro/FORO.md>), con [protocolo](<../Hackaton/Semana 2/Foro/README.md>), copia íntegra de260aportes de este foro e historial sintetizado con autoría. El foro anterior conserva sus aportes y pendientes de semana1. El plan está propuesto; la apertura no transfiere autorizaciones de envíos, remoto o delegación.\n')
(BASE/'registro_apertura.json').write_text(json.dumps({'id':'S2-APERTURA-20261023','autor':'Codex','updated_utc':STAMP,'shared_files':changes,'forum_receipts':'recibos_foro.json','data_manifest':'fuentes/download_manifest.json','training':False,'submission':False,'independent_validation':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'updated_files':[x['path'] for x in changes],'utc':STAMP},ensure_ascii=True))
