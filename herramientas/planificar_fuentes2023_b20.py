"""Identifica procedencia y prioriza revisión documental; no lee filas ni ajusta modelos."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/fuentes_nuevas2023_20261024_v1'
PLAN=REPO/'registro/semana2_b20_fuentes2023_plan_v1.json'
INDEX=REPO/'registro/semana2_b20_fuentes2023_actual.json'
DOC=REPO/'docs/semana2/FUENTES_2023_Y_PLAN_REVISION_B20.md'
NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
IDENT='S2-B20-FUENTES-NUEVAS2023-v1-20261024';STATEKEY='week_2_B20_new_sources_plan20261024_v1'
now=lambda:datetime.now(timezone.utc).isoformat()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()

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
    night_hash=sha(NIGHT);night=read(NIGHT);assert night['status'].startswith('window_closed')
    ownstate=read(ROOT/('Preparaci'+chr(243)+'n')/'ESTADO_PROYECTO.json')['week_2_night_final_balance20261024'];assert ownstate['2024_test_closed'] and ownstate['automation_status']=='DELETED'
    oldpath=ROOT/'Hackaton/Semana 2/Codex/fuentes/file_listing.json';old=read(oldpath)
    new=read(RUN/'official_file_inventory.json')['response'];assert new['ok'] and not new['has_more_pages']
    oldactive={x['name']:x for x in old if x['name'].startswith(('developed/','emerging/')) and x['name'].endswith('.parquet')}
    current={x['name']:x for x in new['files'] if x['name'].startswith(('developed/','emerging/')) and x['name'].endswith('.parquet')}
    comparison={'author':'Codex','utc':now(),'old_active_parquet_files':len(oldactive),'current_active_parquet_files':len(current),'active_parquet_names_added':sorted(current.keys()-oldactive.keys()),'active_parquet_names_removed':sorted(oldactive.keys()-current.keys()),'active_parquet_size_differences':[k for k in oldactive.keys()&current.keys() if int(oldactive[k]['size'])!=int(current[k]['total_bytes'])],
      'creation_metadata_changed':[k for k in oldactive.keys()&current.keys() if oldactive[k]['creationDate']!=current[k]['creation_date']],
      'historical_nonactive_or_nondataset_entries':[x['name'] for x in old if x['name'] not in oldactive],
      'remote_checksum_available_in_queried_metadata':False,'binary_equality_established':False,'new_2023_observations_confirmed':False,
      'interpretation':'ActiveParquet names and sizes agree. Creation metadata differs. Neither equality nor content revision is proved without content evidence. No new independent2023 cohort is established.'}
    dump(RUN/'metadata_comparison.json',comparison)
    avpath=REPO/'privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766/availability_contract.json';av=read(avpath)
    recipepath=REPO/'registro/semana2_glm_ridge_coberturas_plan_v1.json';recipe=read(recipepath)['recipe']['features_by_line']['buildings']['all']
    proposed=['x_construction_type','x_occupancy','x_days_unoccupied','x_smoke_alarms','x_voluntary_excess','x_compulsory_excess']
    fields=[{'feature':f,'in_existing_F0_buildings_whitelist':f in av['blocks']['buildings']['all'],'in_B20_seven_feature_recipe':f in recipe,'first_use_in_other_project_models':'not_established_not_claimed','review_scope':'definition and temporal provenance, no new effect estimation'} for f in proposed]
    dump(RUN/'candidate_fields.json',{'author':'Codex','utc':now(),'availability_source':rel(avpath),'B20_recipe_source':rel(recipepath),'fields':fields,'physical_address_notice':av['physical_master_assumption']})
    candidates=[
      {'id':'F01','priority':1,'source':'Versión oficial de los archivos emergentes y documentación de cambios','locator':['Kaggle MCP list_competition_data_files','https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/data'],
       'availability':'Metadatos nuevos consultados; cambio de contenido no verificado','novelty':'Fecha remota distinta; mismos24nombres/tamaños Parquet activos. No cohorte nueva demostrada.',
       'question':'¿Existe corrección real de datos2023 o solo cambio de publicación/metadatos?','mechanism_contribution':'Una errata real y trazable podría cambiar la interpretación; aún no existe evidencia suficiente.','support_contribution':'Solo si añade información2023 legítima o corrige un error real; fecha/tamaño no aportan soporte.',
       'first_review':'Localizar checksum/versionado/nota de cambios oficial para claims,policies_buildings,addresses. Comparar con hashes locales declarados en manifiesto; no descargar tablas mixtas o test.','stop':'Sin evidencia de contenido, dejar versión no resuelta y no repetir diagnósticos. Con hashes iguales, cerrar revisión sin reanalizar.','estimated_documentary_minutes':'hasta20, si existe evidencia oficial accesible; después registrar carencia','execution':'metadata_search_completed_content_evidence_pending'},
      {'id':'F02','priority':2,'source':'Declaraciones y términos contractuales de edificios de ocurrencia/exposición2023','locator':['Hackaton/Semana 2/Datos/emerging/policies_buildings.parquet',rel(avpath),rel(recipepath)],
       'availability':'Archivo y diccionario disponibles; historial/endosos/condiciones completas no localizados','novelty':'Campos existentes fuera de los siete efectos B20; no nuevo archivo, observaciones o primera utilización global demostrada.',
       'question':'¿Construcción, ocupación, desocupación, alarmas y franquicias distinguen heterogeneidad real y escala de coste neto de un fallo de dispersión?','mechanism_contribution':'Nueva pregunta de procedencia/semántica respecto al contraste; puede delimitar hipótesis, sin estimar efectos o probar causalidad.','support_contribution':'No aumenta el número de componentes ni cura la pantalla retenida de bandas ya fijadas.',
       'first_review':'Revisar significado y fecha de declaración de los seis campos. Exigir selección2023 antes de leer valores en cualquier revisión posterior. days_unoccupied requiere aclarar si fue declarado o realizado; no dar por admisible por estar en F0. Paid ya es neto de franquicia: no descontarla otra vez.','stop':'Sin fecha/definición, no admitir el campo. Sin dato nuevo pertinente, no recalcular grupos, bandas, A/E o costes ya revisados.','estimated_documentary_minutes':'30–45, solo definición/procedencia','execution':'field_inventory_completed_documentary_review_prioritized'},
      {'id':'F03','priority':3,'source':'Contratos y cartera desarrollada2023, como contraste documental separado','locator':['Hackaton/Semana 1/Datos/policies_buildings.parquet','Hackaton/Semana 1/Datos/addresses.parquet','Hackaton/Semana 1/Datos/claims.parquet'],
       'availability':'Archivos existentes de varios años; no se leen filas en este plan','novelty':'Fuente ya disponible y relacionada con el prior histórico; no cohorte emergente nueva ni evidencia totalmente inédita.',
       'question':'¿Son comparables construcción, cobertura, franquicias y corte de valoración antes de cualquier referencia externa al mercado emergente?','mechanism_contribution':'Aclarar comparabilidad/transportabilidad; no una confirmación de efecto B20.','support_contribution':'No sumar componentes o siniestros desarrollados al soporte emergente ni mezclar mercados.',
       'first_review':'Ficha de correspondencia de campos/códigos y procedencia2023. El acceso posterior debe excluir2024 antes de materializar datos, sin cargar modelos, predicciones o scores previos. Mantener claves con mercado y grupos separados.','stop':'Sin equivalencia contractual/temporal, no transferencia. Este plan no propone rehacer credibilidad o el prior.','estimated_documentary_minutes':'20–30 si la documentación de correspondencia existe','execution':'source_located_metadata_only'},
      {'id':'F04','priority':'alta_condicionada_a_existencia','source':'Historial de movimientos y cortes comparables de siniestros de ocurrencia2023; cohorte emergente2023 adicional','locator':['No incluido como archivo separado en el inventario oficial consultado'],
       'availability':'No localizado; fuente requerida, no disponible confirmada','novelty':'Sería nueva información si el organizador la proporcionara con procedencia; no reconstruible de un único snapshot.',
       'question':'¿El desarrollo de pagos,reservas,recuperos/reaperturas o más componentes2023 legítimos cambia la información que limita G1/G2?','mechanism_contribution':'Distinguir observación/maduración de riesgo.','support_contribution':'Podría cambiar información de costes o añadir componentes reales; no garantiza superar reglas y requiere versión nueva.',
       'first_review':'Solo ante una publicación legítima: verificar disponibilidad, valoración, llaves y exportación restringida a ocurrencia2023. No abrir un ledger2024 o solicitar datos por mensaje externo bajo este encargo.','stop':'Ausencia confirmada de archivo no se rellena con simulación, pseudoetiquetas, bootstrap o duplicados. No prometer que la fuente existe.','estimated_documentary_minutes':'sin estimación mientras no exista','execution':'required_but_not_located'},
      {'id':'F05','priority':'baja_solo_contexto_retrospectivo','source':'weather2023 sintético enlazado a address_id','locator':['Hackaton/Semana 2/Datos/emerging/weather.parquet'],
       'availability':'Archivo existente; datos anuales realizados, no observaciones nuevas','novelty':'Ya inventariado; no reabrir diagnósticos de clima','question':'¿Una futura aclaración oficial separa hazard estático de realización anual?','mechanism_contribution':'Solo contexto retrospectivo si hubiera aclaración nueva y ámbito justificado.','support_contribution':'Ninguna nueva cohorte de siniestros. No cura concentración.',
       'first_review':'Solo revisar aclaración documental nueva. Clima anual2023 no es conocido al cotizar a inicios2023. Los códigosE01–E06 no tienen correspondencia real publicada; no unir clima real a identificadores sintéticos.','stop':'No introducir clima2024/2025, selector futuro o asignación geográfica inventada. Sin aclaración, no revisar nuevamente.','estimated_documentary_minutes':'no iniciar sin aclaración nueva','execution':'deferred_no_repeat'}
    ]
    scope={'id':IDENT,'author':'Codex','utc':now(),'request':'Identificar fuentes nuevas2023 y priorizar revisión, sin entrenamiento ni repetición de diagnósticos; B00 conservado y2024cerrado.','kind':'source_provenance_and_documentary_plan_not_model_recipe','current_official_data_page_unchanged':True,'new_official_active_parquet_names':comparison['active_parquet_names_added'],'new_2023_cohort_confirmed':False,'content_version_resolved':False,'candidates':candidates,'evidence_gate_current':'G1plausible,G2retenido fallido,interno desconocido; ningún cierre de carencia','review_order':['F01','F02','F03'],'conditional_high_value_source':'F04','deferred_source':'F05','row_data_reads':0,'new_fits':0,'new_scores':0,'new_numerical_diagnostics':0,'new_bootstrap':0,'new_models_or_recipes':0,'reference':'W2-B00','all_alternatives_preserved':True,'2024_test_closed':True,'night_window_reopened':False,'automation_created_or_updated':False,'professional_independent_validation':False}
    dump(PLAN,scope);dump(RUN/'source_plan.json',scope)
    sources=[]
    for i,p in enumerate([oldpath,ROOT/'Hackaton/Semana 2/Codex/fuentes/download_manifest.json',ROOT/'Hackaton/Semana 2/Codex/fuentes_variables_ultimo/data_description_response.json',avpath,recipepath,REPO/'registro/semana2_b20_mecanismo_soporte_revision_actual.json',REPO/'registro/semana2_b20_soporte_folds_actual.json',REPO/'registro/semana2_contadores_propios_actual.json',REPO/'registro/semana2_desarrollo2023_actual.json']):
        q=RUN/'sources'/f'{i:02d}_{p.name}';q.parent.mkdir(exist_ok=True)
        with q.open('xb') as f:f.write(p.read_bytes())
        sources.append({'path':rel(p),'snapshot':rel(q),'sha256':sha(p)})
    dump(RUN/'source_manifest.json',{'id':IDENT,'author':'Codex','utc':now(),'sources':sources,'raw_tables_not_opened':True})
    doc=f'''# Fuentes2023 para revisar mecanismo y soporte de B20

Codex, corte UTC {now()}. No se confirmó una cohorte adicional de2023 ni una corrección material de los datos. Sí se identificó un cambio de metadatos de publicación que merece resolver primero y fuentes existentes con preguntas de procedencia/semántica aún pertinentes al mecanismo. No las presento como nuevos siniestros o como variables nunca usadas en otro modelo del proyecto.

## Qué se buscó y qué apareció

Se consultó el [diccionario oficial](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/data) mediante KaggleMCP y el inventario autenticado de archivos, sin descargar tablas. El diccionario es igual al archivado. El inventario actual contiene24Parquet activos de developed/emerging: mismos nombres y tamaños que sus equivalentes históricos. Las fechas de creación remotas ahora son del24deoctubre alrededor de03:07UTC; las históricas eran del22. No se atribuye la causa a la incidencia de envío ni se infiere cambio de contenido por esa fecha.

El inventario histórico también contenía11rutas archive/public y dos desktop.ini, ausentes en el actual; se separan de los24Parquet activos para no llamar ampliación o pérdida de una cohorte a un cambio de estructura del catálogo. La consulta de campos confirmó que el servicio devuelve solo nombre,tamaño,fecha, sin checksum. Mismo tamaño no prueba igualdad binaria. Los hashes locales siguen en el manifiesto de descarga; no se recalcularon o compararon con un hash remoto inexistente en esa respuesta.

El conector integrado no exponía el listado. La CLI local no tenía el paquete Kaggle; no se instaló. Se usó el cliente MCP existente para una petición limitada al inventario con acceso de red aprobado, sin leaderboard, notebooks, descargas, filas o cambios de cuenta. Esa consulta de procedencia no repite un diagnóstico predictivo o cotejo de test. Los intentos y la respuesta filtrada quedan guardados sin credenciales.

## Prioridad y contribución esperada

| Orden | Fuente y disponibilidad | Qué podría aportar | Límite y primer paso |
| --- | --- | --- | --- |
| 1, F01 | Versión oficial de claims,policies_buildings,addresses emergentes: metadatos consultados, contenido pendiente | Una nota de corrección/versionado o checksum podría establecer si hay una fuente2023 realmente distinta | Buscar evidencia oficial de contenido. No descargar tablas mixtas o test. Si no existe, dejar identidad de versión no resuelta; si hashes coinciden, no repetir revisión |
| 2, F02 | Declaraciones y términos de edificios2023; archivo/diccionario existentes, condiciones/endosos completos no localizados | Delimitar heterogeneidad técnica y significado del coste neto usando construcción,ocupación,desocupación,alarmas,franquicias | Revisar definición y fecha de declaración. No sumar positivos o recalcular bandas/A/E; campos fuera de B20 no crean nuevas observaciones |
| 3, F03 | Cartera desarrollada2023, disponible en originales multiaño y ya relacionada con prior histórico | Contrastar semántica y transportabilidad contractual como contexto separado | Solo correspondencia documental2023. No juntar mercados, sumar su soporte al emergente o cargar modelos/scores de2024 |
| Alta si aparece, F04 | Movimientos/cortes de siniestros de ocurrencia2023 o cohorte emergente adicional: no localizados | Es la vía potencial para nueva información de maduración o componentes reales que pueda afectar G1/G2 | No prometer disponibilidad. Exigir fuente legítima,fecha,valoración,llaves y extracción solo2023; no sustituirla con simulación o remuestreo |
| Baja, F05 | Clima anual sintético2023: ya existente | Solo una aclaración oficial nueva de hazard estático frente a realización anual podría aportar contexto | No repetir el diagnóstico climático. Año realizado no es información disponible al inicio de2023; no usar años posteriores |

## Primera revisión documental accesible

El contrato F0 enumera x_construction_type,x_occupancy,x_days_unoccupied,x_smoke_alarms,x_voluntary_excess y x_compulsory_excess. La receta B20 de siete efectos de edificios no los incluye. Esa diferencia de listas se comprobó en los metadatos, sin leer valores o medir efectos. No se afirma que nunca hayan aparecido en otra receta amplia.

La revisión debe precisar qué era conocido al cotizar o al iniciar cada periodo2023. days_unoccupied necesita distinguir declaración de experiencia realizada. Los campos físicos sin fecha conservan la hipótesis de estabilidad del maestro, no una fotografía histórica demostrada. Construcción conserva su regla de calidad/codificación; no se retoca para mejorar un score. La documentación dice que paid_to_date ya es neto de franquicia: no descontarla de nuevo.

No se añaden automáticamente campos por estar en F0 ni se propone ampliar el GLM ahora. Esta fuente podría ayudar a formular o descartar una explicación de G1; no altera el soporte de las bandas originales y no resuelve por sí sola G2. Una revisión posterior de valores necesitaría lectura restringida a2023 antes de materializar datos; no se ejecuta un productor que lea todos los años.

## Fuentes que no resolverían el bloqueo

Las regionesE01–E06, direcciones y moneda son sintéticas, según el diccionario. No se encontró una correspondencia geográfica que admita unir siniestros/clima reales de2023. No se inventa esa correspondencia ni se recomienda una descarga externa sin ella. Información real general no añade componentes de esta cartera ficticia.

reference_policies son20pólizas2025 tomadas del test y expenses sirve para prima comercial; no son fuentes de siniestros2023 y no se abrieron. El único claims oficial descrito es un snapshot de valoración, no historial de transacciones. Los grupos ya trazados, curvas,perils,reservas y metadatos C0 siguen como evidencia anterior; no se renombran como fuente nueva o repiten para llenar el plan.

## Plan finito de revisión y parada

F01: hasta20minutos documentales si existe evidencia oficial accesible de versión; ante falta de checksum/cambio documentado, dejar la carencia sin más peticiones idénticas. F02:30–45minutos de semántica/disponibilidad de los seis campos y condiciones2023, con ficha que separe hechos y supuestos. F03:20–30minutos de correspondencia documental si hay sustento para comparar mercados; detenerse si no lo hay. Son estimaciones orientativas del trabajo documental futuro, no tareas programadas ni autorización de entrenamiento.

F04 es de alto impacto potencial, pero no existe una tarea de análisis ejecutable mientras no aparezca la fuente. No se envían mensajes externos para obtenerla bajo este encargo. Si aparece legítimamente, primero origen/corte/diferencias y versiones; después se decide si cambia la información. F05 queda aparcada salvo aclaración nueva. No hay nueva automatización ni reapertura de la ventana nocturna.

Hasta entonces el mecanismo sigue plausible/no establecido y el soporte retenido del contraste sigue fallido. No relajar reglas, combinar bandas, eliminar casos o usar la cartera desarrollada para pasar la pantalla emergente. Solo evidencia nueva admisible permitiría revisar la necesidad y una eventual receta estándar congelada con comentario previo; este plan no entrena o puntúa.

B00 y B01–B20 se conservan, con T0/C0 y folds intactos.2024/test/SEL01/actas/ledger permanecen cerrados aquí; solo se consultó documentación e inventario de nombres/tamaños/fechas, sin datos o resultados protegidos. Se mantiene declarada la exposición previa a un asunto ajeno sin usar sus métricas o afirmar ceguera completa. Cero ajustes,cargas de modelos,inferencias,scores,remuestreos o diagnósticos numéricos nuevos. Codex firma revisión propia exploratoria, no aprobación humana o validación profesional independiente.

[Plan estructurado](../../registro/{PLAN.name}), [índice](../../registro/{INDEX.name}), [balance concluido](BALANCE_NOCTURNO_20261024.md) y [evidencia anterior](EVIDENCIA_DISPONIBLE_MECANISMO_SOPORTE_B20_2023.md). Fuentes, comparación de metadatos y decisiones en {rel(RUN)}.
'''
    # Editorial spacing only on the newly authored artifact.
    for a,b in {'de2023':'de 2023','de2024':'de 2024','de2025':'de 2025','al2023':'al 2023','solo2023':'solo 2023','2023realmente':'2023 realmente','24Parquet':'24 Parquet','24deoctubre':'24 de octubre','de03:07':'de 03:07','11rutas':'11 rutas','los24Parquet':'los 24 Parquet','regionesE01':'regiones E01','son20pólizas2025':'son 20 pólizas 2025','20minutos':'20 minutos','F02:30':'F02: 30','F03:20':'F03: 20','periodo2023':'periodo 2023','edificios2023':'edificios 2023','desarrollada2023':'desarrollada 2023','sintético2023':'sintético 2023','fuente2023':'fuente 2023','documental2023':'documental 2023'}.items():doc=doc.replace(a,b)
    with DOC.open('x',encoding='utf-8') as f:f.write(doc)
    dump(RUN/'decision_journal.json',{'id':IDENT,'author':'Codex','utc':now(),'decisions':[
      {'id':'FU-01','decision':'No afirmar nueva cohorte2023: solo metadatos de fecha cambiados, sin checksum/contenido confirmado.'},
      {'id':'FU-02','decision':'Priorizar identidad de versión y luego semántica temporal de campos disponibles fuera de la receta B20.'},
      {'id':'FU-03','decision':'Desarrollado2023 es contexto separado, no aumento del soporte emergente; fuentes ya existentes no se rebautizan como observaciones nuevas.'},
      {'id':'FU-04','decision':'Historial/cortes y cohorte adicional son requeridos pero no localizados; no inventar disponibilidad o datos.'},
      {'id':'FU-05','decision':'No unir clima/siniestros reales a regiones sintéticas sin correspondencia; clima realizado no prospectivo.'},
      {'id':'FU-06','decision':'Mantener B00/alternativas,G1/G2abiertas y2024cerrado; no modelos,diagnósticos repetidos o reapertura de automatización nocturna.'}]})
    fid='COD-S2-20261024-051';fp=RUN/'forum_051.md'
    fp.write_text(f'''Codex, plan solicitado de fuentes2023 para B20, posterior al cierre nocturno050. Informe:{rel(DOC)}; plan:{rel(PLAN)}. No confirmé una cohorte adicional o corrección material. Inventario oficial actual:24Parquet activos con mismos nombres/tamaños,fechas remotas del24a03:07UTCfrente al22en listado anterior. Catálogo previo incluía además11aliasarchive/publicydosdesktop.ini. El servicio expone solo nombre,tamaño,fecha,sin checksum: no prueba igualdad binaria o cambios de contenido. Diccionario oficial igual al archivado. No atribuir esto a la causa del fallo deenvío.

Orden:F01 resolver versión oficial/changelog/checksum, sin descargar tablas mixtas o test; F02 revisar semántica y disponibilidad2023de construcción,ocupación,desocupación,alarmas yfranquicias,existentes pero fuera de siete efectosB20; F03 comparar documentalmente desarrollado2023como contexto separado,sin sumar soporte o unir mercados. Campos fuera deB20no son observaciones nuevas ni se afirman inéditos en otras recetas. F04historial de movimientos/cortes y cohorte emergente adicional tiene alto impacto potencial,pero no está localizado. F05clima2023solo ante aclaración documental nueva;no repetir su diagnóstico o unir regiones sintéticasE01–E06a clima real.

F01hasta20minutos documentales si existe evidencia,F0230–45yF0320–30,sin tareas programadas. Ante fuente inexistente o versión sin contenido acreditado,registrar carencia y parar; no inventar grupos,simular o reanalizar mismas bandas. FU-01 aFU-06conservan mecanismo plausible/soporte fallido; sin carencias cerradas o nueva receta.

Se consultó documentación e inventario autenticado,nunca leaderboard,filas2024/test o nuevos modelos. CLI sin paquete y DNS restringido se resolvieron con clienteMCPexistente y acceso de red aprobado,solo metadatos; no instalaciones,descargas o credenciales archivadas. Cero ajustes,cargas,inferencias,scores,remuestreo o diagnósticos numéricos nuevos. B00/B01-B20,T0/C0/folds conservados,2024/test/SEL01/actas/ledgercerrados. Ventana nocturna y su automatización siguen cerradas; otros chats/automatizaciones sin cambios. Revisión propia exploratoria,no aprobación humana o validación profesional independiente.''',encoding='utf-8')
    proc=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',fid,'--asunto','Fuentes2023 para B20: versión pendiente, semántica contractual y plan sin entrenamiento','--cuerpo',str(fp)],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr;receipt=json.loads(proc.stdout);dump(RUN/'forum_receipt.json',receipt)
    idx={**{k:v for k,v in scope.items() if k!='candidates'},'path_base':'workspace_root','status':'source_plan_recorded_no_new_cohort_confirmed_version_unresolved','run':rel(RUN),'documentation':rel(DOC),'documentation_sha256':sha(DOC),'plan':rel(PLAN),'plan_sha256':sha(PLAN),'forum_result':fid,'source_manifest':{'path':rel(RUN/'source_manifest.json'),'sha256':sha(RUN/'source_manifest.json')},'decision_journal':{'path':rel(RUN/'decision_journal.json'),'sha256':sha(RUN/'decision_journal.json')}}
    dump(INDEX,idx);changes=[]
    def change(p,fn):
        before=p.read_bytes();after=fn(before.decode('utf-8-sig')).encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        for phase,b in [('before',before),('after',after)]:
            q=RUN/'registration_cuts'/phase/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as f:f.write(b)
        tmp=p.with_name(p.name+'.fuentes2023B20.tmp')
        with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert p.read_bytes()==before,'Concurrent change '+rel(p);os.replace(tmp,p)
        changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p)})
    change(ROOT/('Preparaci'+chr(243)+'n')/'ESTADO_PROYECTO.json',lambda raw:top(raw,STATEKEY,idx))
    section=f'''\n\n## Fuentes2023 y plan de revisión de B20 fuera de la ventana concluida

Codex,UTC {now()},foro051,decisiones FU-01 aFU-06. Informe {rel(DOC)},plan {rel(PLAN)},índice {rel(INDEX)}. No nueva cohorte2023o corrección material confirmada. Metadatos oficiales nuevos:24Parquet activos,mismos nombres/tamaños y fecha de creación distinta;sin checksum remoto,contenido/igualdad binaria no resueltos. Diccionario actual igual al archivado; comparación del catálogo separa11aliasarchive/publicydosdesktop.ini históricos. No se descargaron tablas o leyeron filas.

Prioridad F01versión/changelog/hash, F02definición/disponibilidad de seis campos contractuales fuera de la recetaB20, F03desarrollado2023como contexto separado. F04movimientos/cortes/cohorte adicional:alto impacto si aparece pero no localizado. F05climaanual2023sin revisión repetida,sin correspondencia sintética-real inventada. Ningún campo existente aporta por sí más componentes o cierra soporte. No afirmar primera utilización global de campos o legitimidad temporal por una etiquetaF0. Parada ante falta de fuente/evidencia real; no nuevas bandas,datos simulados o fuentes rebautizadas.

B00/B01-B20,T0/C0/folds conservados,G1/G2abiertas,2024/test/SEL01/actas/ledgercerrados aquí. Cero entrenamiento,cargas,inferencias,scores,remuestreos o diagnósticos numéricos nuevos. Sin instalaciones,descargas,credenciales archivadas o mensajes externos. La ventana y automatización nocturnas permanecen cerradas; no otras automatizaciones. Revisión propia exploratoria,no revisión profesional independiente o aprobación humana.\n'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/('Preparaci'+chr(243)+'n')/name,lambda raw:raw+section)
    change(ROOT/'RUTAS_PROYECTO.json',lambda raw:top(top(top(raw,'week_2_b20_new_sources_plan_index',rel(INDEX)),'week_2_b20_new_sources_plan_report',rel(DOC)),'week_2_b20_new_sources_plan',rel(PLAN)))
    obs={'id':IDENT,'utc':now(),'night_index_untouched':sha(NIGHT)==night_hash,'old_source_files_untouched':all(sha(ROOT/x['path'])==x['sha256'] for x in sources),'source_copies_exact':all(sha(ROOT/x['snapshot'])==x['sha256'] for x in sources),'six_proposed_fields_not_in_B20':all(x['in_existing_F0_buildings_whitelist'] and not x['in_B20_seven_feature_recipe'] for x in fields),'new_2023_cohort_confirmed':False,'new_model_operations':0,'scope':'Document/metadata integration only; no numerical diagnostics or old suites executed.'}
    dump(RUN/'documentary_integrity_receipt.json',obs);dump(RUN/'registration.json',{'changes':changes,'price_catalog_mutations':0,'counter_mutations':0,'night_index_mutations':0})
    files=[p for p in RUN.rglob('*') if p.is_file()]+[PLAN,INDEX,DOC,Path(__file__).resolve()]
    dump(RUN/'manifest.json',{'id':IDENT,'utc':now(),'files':[{'path':rel(p),'sha256':sha(p)} for p in files]})
    print(json.dumps({'id':IDENT,'forum_result':fid,'document':rel(DOC),'new_cohort_confirmed':False,'active_file_names_added':comparison['active_parquet_names_added'],'content_version_resolved':False,'night_index_untouched':obs['night_index_untouched'],'source_files_untouched':obs['old_source_files_untouched'],'new_fits':0},ensure_ascii=True))

if __name__=='__main__':main()
