"""Consolidación documental de fuentes y seis carencias; no ejecuta productores o pruebas."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/revision_fuentes2023/consolidacion_F01_F05_20261024_v1'
DOC=REPO/'docs/archivo/semana2/CONSOLIDACION_F01_F05_Y_BLOQUEOS_B20_2023.md'
INDEX=REPO/'registro/semana2_b20_consolidacion_F01_F05_actual.json'
SOURCE=REPO/'registro/semana2_b20_fuentes2023_actual.json'
PRIORITY=REPO/'registro/semana2_b20_prioridades_actual.json'
IDENT='S2-B20-CONSOLIDACION-F01-F05-2023-v1-20261024';FID='COD-S2-20261024-058'
STATEKEY='week_2_F01_F05_B20_consolidation2023_v1_20261024'
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
    names={'F01':'semana2_contenido_oficial_actual.json','F02':'semana2_F02_disponibilidad2023_actual.json','F03':'semana2_F03_desarrollado2023_actual.json','F04':'semana2_F04_fuentes2023_actual.json','F05':'semana2_F05_busqueda_foro_actual.json','mechanism':'semana2_b20_mecanismo_soporte_revision_actual.json','support':'semana2_b20_soporte_folds_actual.json','preflight':'semana2_b20_preflight_c0_actual.json','adapter':'semana2_b20_c0_adaptador_sintetico_actual.json'}
    records={k:read(REPO/'registro'/n) for k,n in names.items()}
    assert records['F01']['files_verified']==24 and records['F01']['byte_equal_all']
    assert not records['F04']['new_emerging2023_cohort_located'] and not records['F04']['new_claim_movements_located']
    assert records['F05']['messages']==21 and not records['F05']['new_official_temporal_clarification_located']
    assert records['support']['fold_gate_failed']==5 and records['support']['fold_gate_cells']==10
    assert records['adapter']['G4_C0_software_stage']=='implemented_and_synthetic_verified' and not records['adapter']['G4_full_flow_closed']
    assert read(PRIORITY)['author']=='Codex'
    RUN.mkdir(parents=True,exist_ok=False)
    paths=[REPO/'registro'/n for n in names.values()]+[SOURCE,PRIORITY,REPO/'registro/semana2_desarrollo2023_actual.json',REPO/'registro/semana2_contadores_propios_actual.json',REPO/'registro/semana2_continuidad_nocturna.json',REPO/'registro/semana2_glm_ridge_coberturas_plan_v1.json',REPO/'privado/semana2/desarrollo2023/prioridades_b20_20261024_v1/priority_matrix.json',ROOT/'Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md']
    paths += [ROOT/x['documentation'] for x in records.values()]
    adapter=records['adapter'];paths.append(ROOT/adapter['verification']['path'])
    paths += [ROOT/x['path'] for x in adapter['source_and_snapshot_hashes']]
    paths=list(dict.fromkeys(paths));sources=[];doc_checks=[]
    for k,d in records.items():
        if 'documentation_sha256' in d:
            ok=sha(ROOT/d['documentation'])==d['documentation_sha256'];assert ok,k+' documentation changed'
            doc_checks.append({'source':k,'documentation_matches_index':ok})
    adapter_checks=[]
    for x in adapter['source_and_snapshot_hashes']:
        a=sha(ROOT/x['path'])==x['sha256'];b=sha(ROOT/x['snapshot'])==x['sha256'];assert a and b
        adapter_checks.append({'path':x['path'],'source_matches_recorded_sha':a,'snapshot_matches':b})
    assert sha(ROOT/adapter['verification']['path'])==adapter['verification']['sha256']
    vr=read(ROOT/adapter['verification']['path']);assert vr['success'] and vr['errors']==0 and vr['failures']==0
    dump(RUN/'integration_source_receipt.json',{'id':IDENT,'utc':now(),'document_links':doc_checks,'concurrent_C0_adapter_identity':adapter_checks,'received_verification_receipt_hash_matches':True,'received_scope':vr['scope'],'received_tests_not_rerun':True,'new_tests':0,'new_numeric_diagnostics':0})
    for i,p in enumerate(paths):
        q=RUN/'sources'/f'{i:02d}_{p.name}';q.parent.mkdir(exist_ok=True)
        with q.open('xb') as f:f.write(p.read_bytes())
        sources.append({'path':rel(p),'snapshot':rel(q),'sha256':sha(p),'intentional_mutable_index':p in [SOURCE,PRIORITY]})
    previous_priority=next(x['snapshot'] for x in sources if x['path']==rel(PRIORITY))
    summary=[
      {'id':'F01','status':'Identidad binaria resuelta para los24archivos revisados','finding':'Fecha remota distinta; contenido idéntico a históricos en el corte verificado.','B20_effect':'No se acreditó una corrección de origen o cohorte2023 nueva por republicación. No demuestra que no haya errores en el dato.','remaining':'Ninguno de identidad para ese corte; una futura corrección necesita versión y diferencias documentadas.'},
      {'id':'F02','status':'Semántica revisada, disponibilidad por cotización pendiente','finding':'Cinco campos físicos/contractuales condicionales; days_unoccupied sin ventana/declarado-realizado aclarados. Ninguno de los seis está en B20.','B20_effect':'Delimita hipótesis, no demuestra efecto residual ni aporta nuevos grupos; no nueva admisión prospectiva.','remaining':'Declaración/captura y vigencia/endosos ligados a2023; ventana y referencia de desocupación; regla contractual conjunta de franquicias.'},
      {'id':'F03','status':'Contexto desarrollado revisado, transporte no establecido','finding':'Definiciones comunes con diferencias de códigos/edad/región. Prior recibido2021-2023, no aislado2023; B20ridge no contrae hacia ese prior.','B20_effect':'No suma soporte emergente ni constituye confirmación independiente.','remaining':'Comparabilidad y disponibilidad fechadas; evidencia específica2023 para una eventual comparación, sin mezclar mercados.'},
      {'id':'F04','status':'Búsqueda delimitada terminada, fuente adicional no localizada','finding':'No se localizó movimiento,segundo corte o cohorte emergente2023 adicional; alias locales de claims/pólizas son históricos desarrollados.','B20_effect':'No cambia observación o soporte disponible; ausencia acotada, no inexistencia universal.','remaining':'Fuente legítima/versionada de movimientos o cohorte con fechas,claves,importes y exposición incluidos ceros; comprobar solapamientos.'},
      {'id':'F05','status':'Cobertura del foro resuelta por sustitución; carencia temporal abierta','finding':'Nueve temas y21mensajes recuperados directamente sin aclaración climática localizada; buscador general sigue fallando.','B20_effect':'No fecha los índices ni agrega historia/cohorte; rechazo prospectivo previo conservado.','remaining':'Observado/pronóstico/hazard previo,ventana,método/insumos,emisión/publicación y vigencia por campo; historia emergente legítima.'}
    ]
    for row in summary:row.update(index=rel(REPO/'registro'/names[row['id']]),source_utc=records[row['id']]['utc'],forum_result=records[row['id']]['forum_result'])
    dump(RUN/'source_review_matrix.json',{'id':IDENT,'utc':now(),'sources':summary,'all_rows_are_prior_work_reused':True,'new_source_search_performed':False})
    gates=[
      {'gate':'G6','priority':1,'title':'Objetivo y alcance actuarial','status':'local_scope_preserved_ultimate_conditional','what_changed':'F02/F04/F05 precisan incertidumbres de contrato,observación y disponibilidad; no prueba de último.','required_evidence':'Para ampliar interpretación: desarrollo longitudinal2023 y condiciones/capital/fechas acreditados; revisión competente del uso previsto.','boundary':'T0 observado y C0/exposición guardados permiten describir el alcance local condicionado; falta de prueba de último no es veto universal a investigación2023.'},
      {'gate':'G1','priority':2,'title':'Mecanismo residual','status':'plausible_not_established','what_changed':'F01-F05 no aportan hecho2023 nuevo que distinga dispersión de nivel,concentración,mezcla contractual o maduración.','required_evidence':'Hecho2023 pertinente,con procedencia/fecha,que distinga o fortalezca materialmente una hipótesis refutable frente a alternativas. No se exige identificación causal única.','boundary':'Volver a puntuar bandas,asociaciones o quitar el incendio no suministra ese hecho.'},
      {'gate':'G2','priority':3,'title':'Soporte del contraste de pendiente','status':'heldout_failed_internal_unknown','what_changed':'Recibo guardado:fallan5de10celdas de cuatro folds. F01-F05 no añaden componentes o corrección material acreditada.','required_evidence':'Información emergente2023 legítima adicional o corrección material demostrada que cambie la evidencia; después,soporte por ámbito bajo versión y criterios previos.','boundary':'Soporte interno sigue desconocido. No relajar límites,reagrupar bandas o eliminar pérdidas; el fallo corresponde al diseño concreto,no a todo modelo posible.'},
      {'gate':'G3','priority':4,'title':'Necesidad de la modificación estándar','status':'added_complexity_not_justified','what_changed':'No nueva necesidad establecida para otra pendiente,alpha,interacción o segmentación; conservar comparador sencillo de nivel.','required_evidence':'Un cambio mínimo ligado a G1 y G2,con comparador estándar,configuración/coste/criterios congelados y daños vigilados antes de cualquier fit o score.','boundary':'No B21 o receta nueva por esta consolidación; ninguna selección por un punto2023.'},
      {'gate':'G4','priority':5,'title':'Flujo numérico y validación sin fuga','status':'C0_numeric_stage_synthetic_verified_full_flow_pending','what_changed':'Ámbitos exteriores conciliados antes; ahora hay núcleo numérico C0 con recibo sintético de17:08UTC. Fuentes y recibo cotejados por SHA,sin reejecutar.','required_evidence':'Entradas y objetos internos reales estrictos2023,procedencia/caché completas y validación de todo el aprendizaje:preprocesado,C0,GLM y calibrador,bajo exclusión exterior/interior. Presupuesto total,lectores y límites de parada.','boundary':'C0 sintético no acredita flujo completo ni uso con datos del concurso. Los20reusos exteriores inválidos siguen rechazados para interior,sin invalidar su papel exterior original.'},
      {'gate':'G5','priority':6,'title':'Promoción y uso posterior','status':'not_evaluated_no_promotion','what_changed':'Ningún candidato promovido/retirado o lista final congelada; B00 sigue referencia.','required_evidence':'Recibos de la política común y revisión/acta aplicable bajo el ámbito que corresponda a una autorización futura; fuera de esta tarea.','boundary':'La ausencia de promoción no impide por sí sola una exploración2023 admisible; no se abre2024,ledger,actas oSEL01 aquí.'}
    ]
    dump(RUN/'updated_gate_matrix.json',{'id':IDENT,'author':'Codex','utc':now(),'priority_order':[g['gate'] for g in gates],'cards':gates,'gates_closed':[],'current_slope_design_eligible':False})
    evidence_packet=[
      {'order':1,'deliverable':'Ficha de novedad de fuente2023','needs':'Origen legítimo,versión/hash,disponibilidad/corte,mercado,claves,diferencias reales y relación con una carencia.','available_now':False,'not_a_substitute':'Otra fecha de archivo,duplicado de mercado,remuestreo o nota del foro no vinculada a un dato nuevo.'},
      {'order':2,'deliverable':'Nota de mecanismo y efecto esperado de nueva información sobre soporte','needs':'Hipótesis material/refutable y alternativas; denominadores completos y solapamiento de componentes conservado.','available_now':False,'not_a_substitute':'Mismo A/E,misma mejora de score o más cortes del mismo siniestro presentados como grupos nuevos.'},
      {'order':3,'deliverable':'Propuesta mínima estándar versionada','needs':'Comparador,objetivo/exposición correctos,criterios y costes previos,salvaguardas y comentario en foro antes de ajustar/puntuar.','available_now':'Existing blocked slope design retained; eligibility not established.','not_a_substitute':'Ampliar capacidad o bajar exigencias para obtener un score2023.'},
      {'order':4,'deliverable':'Flujo completo y artefactos interiores estrictos2023','needs':'Conectar entradas legítimas al C0 ya disponible y verificar todos los ancestros aprendidos/preprocesado/GLM/calibrador y recursos,solo bajo alcance futuro admisible.','available_now':'C0 software stage synthetic verified; full pipeline and real nested objects absent.','not_a_substitute':'Un selector de metadatos,pruebas solo C0 o reutilizar C0 exterior en ámbito interior.'}
    ]
    dump(RUN/'reentry_evidence_packet.json',{'id':IDENT,'author':'Codex','utc':now(),'items':evidence_packet,'current_scope':'Consolidation only; no fit/inference authorized by this artifact.','next_useful_action':'Review a legitimately supplied new source/correction when one exists; no repeat work over unchanged sources.'})
    result={'id':IDENT,'author':'Codex','utc':now(),'status':'F01_F05_consolidated_B20_current_slope_blocked_no_new_trial','priority_order':[g['gate'] for g in gates],'current_gate_statuses':{g['gate']:g['status'] for g in gates},'gates_closed':[],'non_model_issues_resolved':['F01 binary identity at reviewed cut','F05 public-message retrieval coverage at reviewed cut'],'concurrent_progress_reconciled':'C0 numerical software stage implemented and synthetic verified; complete learning flow still open','current_blockers':['G1: residual mechanism not established','G2: current slope support failed; internal support unknown','G4: full numerical learning flow and real nested2023 artifacts not verified'],'can_start_current_slope_trial':False,'new_emerging2023_information_established':False,'material_source_correction_established':False,'new_fits':0,'model_loads':0,'new_predictions':0,'new_scores':0,'new_bootstrap':0,'new_numeric_diagnostics':0,'new_model_tests':0,'new_source_searches':0,'row_values_read':0,'reference':'W2-B00','all_alternatives_preserved':True,'target_exposure_C0_folds_changed':False,'promotion':False,'final_roster_frozen':False,'2024_test_closed':True,'prior_external2024_subject_exposure_disclosed':True,'professional_independent_validation':False,'night_window_reopened':False}
    dump(RUN/'consolidation_result.json',result)
    rows='\n'.join('| '+x['id']+' | '+x['status']+' | '+x['B20_effect']+' |' for x in summary)
    labels={'G6':'Alcance local conservado; último condicionado','G1':'Plausible, no establecido','G2':'Soporte retenido incumplido; interno desconocido','G3':'Complejidad adicional sin justificar','G4':'C0 sintético disponible; flujo completo pendiente','G5':'Promoción no evaluada'}
    grow='\n'.join('| '+g['gate']+' | '+labels[g['gate']]+' | '+g['required_evidence']+' |' for g in gates)
    doc=f'''# F01–F05 consolidadas: bloqueos y evidencia pendiente de B20

Codex, corte UTC {result['utc']}. El contraste de pendiente propuesto a partir de B20 sigue sin estar listo para una nueva prueba. F01 resolvió identidad de archivos y F05 la recuperación de comentarios por una ruta de sustitución, pero no se acreditaron datos emergentes2023 adicionales ni una corrección material de origen. El mecanismo sigue plausible y no establecido; el soporte retenido del diseño conserva su fallo. B20 se mantiene como artefacto exploratorio y B00 como referencia, con todas las alternativas preservadas.

Esta consolidación reutiliza índices y recibos existentes. No se repiten búsquedas,diagnósticos,suites,ajustes o puntuaciones. Se conciliaron fechas y versiones y se cotejaron enlaces/hashes documentales. La evidencia sintética concurrente de C0 se registra según su alcance,sin reproducir sus pruebas o adoptar órdenes de otro trabajo.

## Qué terminó cada revisión de fuentes

| Fuente | Estado al corte de su revisión | Consecuencia para B20 |
| --- | --- | --- |
{rows}

F01 compara24archivos oficiales con sus históricos mediante bytes/hashes en el corte14:38UTC. La identidad no corrige los datos ni demuestra su calidad. F04 no localizó movimientos o cohorte adicional en su búsqueda acotada; el aviso del HOST sobre retirada de un duplicado desarrollado aclara empaquetado,no aporta nuevas observaciones. Las conclusiones de búsqueda no son prueba de inexistencia universal.

F02 distingue uso de vivienda de profesión,material constructivo de tipología y alarmas como indicador. Construcción,uso,alarmas y franquicias requieren declaración/vigencia si se afirma conocimiento al cotizar. days_unoccupied conserva riesgo temporal no resuelto,sin afirmar fuga observada. F03 no vuelve independiente el prior recibido2021–2023 ni lo convierte en una estimación aislada2023. B20ridge no se centra en ese prior. No se suman siniestros o componentes desarrollados a soporte emergente.

F05 ahora cubre9temas y21mensajes de ambas partes al corte17:05UTC,con controles de recuperación y recuentos conciliados. El buscador general sigue fallando; se conserva la sustitución verificada,sin atribuir reparación del servidor. No se localizó aclaración climática que feche los valores. Los agregados anuales2023 no estaban realizados al iniciar ese año. Los índices de viento/incendio requieren método,vintage,emisión/publicación y vigencia; sus nombres no prueban disponibilidad previa o fuga. Se mantiene el rechazo prospectivo anterior y el responsable del hallazgo S2-VAL-DAT-003.

## Las seis carencias,actualizadas

Se conserva la prioridad G6→G1→G2→G3→G4→G5. Ninguna de estas seis carencias se declara cerrada por terminar una búsqueda documental.

| Carencia | Estado vigente | Evidencia pendiente |
| --- | --- | --- |
{grow}

G6 mantiene el encuadre local en T0 observado y exposición/vínculo C0 guardados,bajo supuestos explícitos. No se necesita fingir que existe último observado para describir esa exploración. Faltan desarrollo longitudinal y revisión del uso si se amplía la interpretación hacia suficiencia de reservas o tarifa prospectiva. Esta carencia no es un veto absoluto a toda investigación2023.

Para G1 hace falta un hecho pertinente2023 que distinga o fortalezca materialmente la hipótesis residual frente a nivel,concentración,mezcla contractual y maduración. No se exige demostrar una causa única. Los mismos diagnósticos descriptivos no suplen ese hecho. Para G2 se reutiliza el resultado guardado:fallan5de10celdas en cuatro folds y el soporte interno sigue desconocido. Cambiar bandas,cortes,umbrales o retirar siniestros para pasar no crea información. Los umbrales pertenecen al diseño concreto,no son reglas universales IAA/Kaggle ni invalidan todos los modelos.

## El avance concurrente que cambia G4

El índice del adaptador C0 tiene corte17:08UTC,posterior al preflight de03:32UTC. Ya no corresponde decir que falta todo el núcleo numérico. Existe c0_estricto2023.py y un recibo de etapa C0 con13pruebas sintéticas,20pares exterior/interior y79invocaciones sintéticas. El primer intento con tres errores de construcción de fixtures sigue conservado. Se cotejaron SHA de fuentes,snapshots y recibo final; no se reejecutó la suite. Sus cifras son evidencia recibida de trabajo previo,no pruebas nuevas de esta consolidación o validación profesional independiente.

El alcance acreditado es C0 sintético:curvas,marcas,pesos,frecuencias,mezcla,caché y aplicación dentro de su contrato. No se ejecutó sobre filas del concurso,no creó objetos internos reales ni verificó conjuntamente preprocesado,GLM y calibrador. El presupuesto C0 enumera diez ámbitos internos,sesenta ajustes de reporte,sesenta constantes de frecuencia y diez mezclas; no es coste total de precios/calibración ni ejecución realizada. Los veinte reusos del C0 exterior siguen inválidos para el ámbito interior,conservando su papel exterior original.

Por tanto,G4 avanza parcialmente y permanece abierto como flujo total. Hacer esa ingeniería tampoco borraría el fallo de soporte G2. No se conecta el adaptador a datos o productores bajo este encargo.

## Qué permitiría retomar el contraste

Primero debe recibirse información2023 legítima y pertinente o una corrección material documentada,con origen,versión,fechas,claves y diferencias. F02 necesita declaración/captura y endosos ligados a la fila; F04 necesitaría movimientos/cortes o cohorte con exposición completa,incluidos ceros. Más cortes del mismo siniestro pueden informar maduración,pero no son nuevos componentes independientes. Una cohorte requiere conservar solapamientos de cliente/dirección,póliza y siniestro; nombres o IDs distintos no prueban independencia.

Con esa evidencia se podría redactar una nota refutable de mecanismo y de cómo cambia el soporte. Si sigue siendo insuficiente,se registra el fallo y se detiene ese diseño. Solo cuando corresponda habría base para una propuesta mínima estándar versionada,con comparador,objetivo/exposición correctos,criterios,salvaguardas,coste y comentario previo al ajuste o puntuación. No se crea ahora B21,otro alpha o más segmentación.

Después quedarían entradas estrictas2023,objetos internos y validación de todos los ancestros aprendidos,usando el C0 disponible sin sustituir la prueba de todo el flujo. La receta y el presupuesto deben cubrir preprocesado,C0,GLM y calibrador,con exclusión exterior/interior. Ni un selector de metadatos ni una prueba solo C0 bastan. Los trabajos requieren el ámbito que autorice el participante en su momento; esta ficha no dispara entrenamiento ni crea permisos. Una bandera deIA no es revocación humana ni aprobación nueva.

G5 corresponde a promoción y uso posterior,separados de elegibilidad exploratoria. Esta consolidación no consulta esos recibos,no promueve o retira candidatos y no fija la lista final por un score2023. La falta de promoción tampoco es por sí sola un impedimento a cualquier exploración2023 admisible.

## Decisión y continuidad

No hay un nuevo ensayo que iniciar con las fuentes actuales. El siguiente paso útil es recibir y revisar una fuente o corrección pertinente,cuando exista; no repetir trabajo terminado para llenar una cadencia. Sin esa novedad no hay una fecha sustentable para retomar el contraste. B00 y todas las alternativas,T0/C0,exposición,folds,modelos y contadores se conservan.

2024/test/ledger/actas/SEL01 siguen cerrados para este trabajo. No se entrenó,cargó un modelo,predijo,puntuó,reestimó C0 o leyó una fila de datos. Se conserva la exposición histórica de un asunto externo sin repetir/usar métricas ni afirmar ceguera completa. La ventana/automatización nocturna continúan cerradas. Sin contactos externos,nuevos chats,delegación o programación. Codex firma consolidación documental propia,no revisión profesional independiente o aprobación humana. Las prácticas IAA de documentación de datos/modelos y gobernanza §2.8 orientan estas distinciones,sin convertir recibos técnicos en aptitud actuarial certificada.

El [índice consolidado](../../registro/{INDEX.name}) enlaza la matriz F01–F05,la matriz de seis carencias,el paquete de evidencia para retomar,fuentes/SHA y decisiones. Se actualiza el índice propio de prioridades con este estado y se conserva su corte anterior. Los estudios originales,recibos adversos y autorías permanecen intactos.
'''
    replacements={'emergentes2023':'emergentes de 2023','B20ridge':'B20 ridge','anuales2023':'anuales de 2023','prior recibido2021':'prior recibido 2021','aislada2023':'aislada de 2023','pertinente2023':'pertinente de 2023','información2023':'información de 2023','estrictas2023':'estrictas de 2023','investigación2023':'investigación de 2023','exploración2023':'exploración de 2023','score2023':'score de 2023','bandera deIA':'bandera de IA','carencias,actualizadas':'carencias, actualizadas','compara24archivos':'compara 24 archivos','corte14:38UTC':'corte de las 14:38 UTC','cubre9temas y21mensajes':'cubre nueve temas y 21 mensajes','corte17:05UTC':'corte de las 17:05 UTC','fallan5de10celdas':'fallan 5 de 10 celdas','corte17:08UTC':'corte de las 17:08 UTC','de03:32UTC':'de las 03:32 UTC','con13pruebas':'con 13 pruebas','sintéticas,20pares':'sintéticas, 20 pares','y79invocaciones':'y 79 invocaciones'}
    for a,b in replacements.items():doc=doc.replace(a,b)
    doc=re.sub(r',(?=\S)',', ',doc)
    with DOC.open('x',encoding='utf-8') as f:f.write(doc)
    decisions=[('CF-01','Separar cierre de identidad/cobertura documental de seis carencias B20:ninguna puerta de modelado se cierra por F01-F05.'),('CF-02','Reutilizar todos los recibos y preservar resultados adversos; sin nuevos diagnósticos,fuentes,modelos o ajustes.'),('CF-03','G1 no establecido y G2 fallido con internos desconocidos; nueva evidencia pertinente requerida,sin relajar criterios o quitar siniestros.'),('CF-04','Actualizar G4 con núcleo C0 sintético existente y SHA cotejados; no afirmar inexistencia del núcleo o cierre de flujo completo.'),('CF-05','Priorizar G6,G1,G2,G3,G4,G5 y definir paquete de procedencia/mecanismo/soporte/estándar/flujo antes de retomar.'),('CF-06','Mantener G5 y revisión profesional separadas de ensayo local; no nueva aprobación humana o autorización implícita.'),('CF-07','B00 y alternativas intactas,2024cerrado y sin entrenamiento; actualizar solo índices/documentación propios con historial y concurrencia.')]
    dump(RUN/'decision_journal.json',{'id':IDENT,'author':'Codex','utc':now(),'decisions':[{'id':k,'decision':v} for k,v in decisions]})
    fp=RUN/'forum_058.md'
    body=f'''Codex, consolidación F01–F05 solicitada. Informe: {rel(DOC)}. Índice: {rel(INDEX)}. Matrices/paquete para retomar: {rel(RUN)}. Solo evidencia existente; sin búsquedas,diagnósticos,suites o ajustes nuevos.

F01: identidad binaria de los24archivos resuelta en su corte; no corrección/cohorte nueva por republicación. F02: cinco campos condicionales y desocupación sin ventana/declarado-realizado; ninguna nueva disponibilidad por cotización acreditada o variable añadida. F03: contexto desarrollado,prior2021–2023 no aislado2023 y no equivalente a contracción ridge; no sumar soporte entre mercados. F04: movimientos/otro corte/cohorte emergente adicional no localizados en búsqueda acotada,alias de raíz desarrollados. F05: acceso por búsqueda directa verificado en9temas/21mensajes,sin aclaración climática localizada; buscador remoto sigue fallando y fechas/método de índices continúan pendientes. Cerrar identidad y cobertura no cierra G1–G6.

Prioridad conservada G6→G1→G2→G3→G4→G5. G6: T0/C0 local condicionado conservado,último/reservas no acreditados. G1: mecanismo plausible/no establecido,falta hecho2023 pertinente que distinga nivel,concentración,contrato o maduración,sin exigir causa única. G2: recibo retenido fallido5/10celdas de cuatro folds,internos desconocidos; no nueva información/corrección que cambie evidencia. G3: no necesidad de más capacidad u otra receta. G5: promoción no evaluada,separada de elegibilidad local; B00/alternativas intactos y sin lista final.

G4 recibe una actualización material por trabajo concurrente de17:08UTC: existe núcleo numérico C0 y recibo sintético13pruebas/20pares/79invocaciones. Se cotejaron fuentes,snapshots y recibo por SHA,sin reejecutarlo. Se preservan los adversos del primer intento y la autoría Codex. Ya no se afirma que falte todo el núcleo. Siguen pendientes entradas/objetos internos reales2023 y todo el aprendizaje conjunto preprocesado/C0/GLM/calibrador,con recursos completos. Prueba solo C0 no certifica el flujo;20reusos exteriores siguen rechazados para interior,sin invalidar uso exterior original. No altera G1/G2.

Para retomar el contraste:ficha de fuente/corrección legítima2023 con origen,versión,disponibilidad/valoración,claves y diferencias; evidencia que distinga mecanismo y cambie soporte; propuesta mínima estándar con comparador/criterios/configuración/coste y comentario previo; después,flujo estricto2023 completo y ancestría. Movimientos repetidos no son grupos nuevos; cohorte necesita exposición sin siniestros y solapamientos conservados. No bajar límites,reagrupar bandas,eliminar pérdidas o perseguir un punto2023. Sin hecho pertinente nuevo,no iniciar otra tanda ni repetir diagnósticos.

CF-01 a CF-07,autor Codex. El encargo vigente solo consolida; no dispara entrenamiento ni inventa aprobación humana. B00 y todas las alternativas,T0/C0/exposición/folds/modelos/contadores conservados.2024/test/ledger/actas/SEL01 cerrados; cero filas,cargas,inferencias,scores,remuestreos o reestimación C0. Ventana/automatización nocturna cerradas,sin contactos externos,otros chats o delegación. Revisión documental propia,no validación profesional independiente. Índice de prioridades propio actualizado,con corte anterior y fuentes preservados.
'''
    for a,b in replacements.items():body=body.replace(a,b)
    body=re.sub(r',(?=\S)',', ',body)
    with fp.open('x',encoding='utf-8') as f:f.write(body)
    assert sha(PRIORITY)==next(x['sha256'] for x in sources if x['path']==rel(PRIORITY)),'Concurrent priority update: reconcile before publication'
    proc=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',FID,'--asunto','F01–F05 consolidadas: B20 sigue bloqueado; C0 sintético disponible, flujo completo pendiente','--cuerpo',str(fp)],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr;dump(RUN/'forum_receipt.json',json.loads(proc.stdout))
    dump(RUN/'source_manifest.json',{'id':IDENT,'utc':now(),'sources':sources,'numeric_model_tests_rerun':False,'row_data_read':False})
    idx={**result,'path_base':'workspace_root','run':rel(RUN),'documentation':rel(DOC),'documentation_sha256':sha(DOC),'forum_result':FID,'previous_priority_index_snapshot':previous_priority}
    for key,name in [('source_reviews','source_review_matrix.json'),('matrix','updated_gate_matrix.json'),('reentry_packet','reentry_evidence_packet.json'),('sources','source_manifest.json'),('decisions','decision_journal.json')]:idx[key]={'path':rel(RUN/name),'sha256':sha(RUN/name)}
    dump(INDEX,idx);changes=[]
    def change(p,fn):
        before=p.read_bytes()
        if p==PRIORITY:assert hashlib.sha256(before).hexdigest()==next(x['sha256'] for x in sources if x['path']==rel(PRIORITY)),'Concurrent priority change requires reconciliation'
        after=fn(before.decode('utf-8-sig')).encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        for phase,b in [('before',before),('after',after)]:
            q=RUN/'registration_cuts'/phase/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as f:f.write(b)
        tmp=p.with_name(p.name+'.F01F05consolidation.tmp')
        with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert p.read_bytes()==before,'Concurrent change '+rel(p);os.replace(tmp,p)
        changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p)})
    def priority_update(raw):
        prior=json.loads(raw);assert prior['id']=='S2-B20-PRIORIDADES2023-v1-20261024','Newer priority record requires reconciliation'
        return json.dumps({**idx,'id':'S2-B20-PRIORIDADES2023-v2-F01F05-20261024','consolidation_index':rel(INDEX),'original_gate_statuses':prior['original_gate_statuses'],'previous_index_snapshot':previous_priority,'verification_scope':'Documentary source identity/integration only; prior numerical/synthetic tests reused, not rerun.'},ensure_ascii=False,indent=2)+'\n'
    change(PRIORITY,priority_update)
    def source_update(raw):
        for k,v in {'consolidation_status':result['status'],'consolidation_index':rel(INDEX),'consolidation_completed_utc':now(),'current_B20_gate_statuses':result['current_gate_statuses'],'can_start_current_B20_slope_trial':False,'C0_synthetic_stage_received':True}.items():raw=top(raw,k,v)
        return raw
    change(SOURCE,source_update)
    change(ROOT/'Preparación/ESTADO_PROYECTO.json',lambda raw:top(raw,STATEKEY,idx))
    section=f'''\n\n## F01–F05: consolidación y bloqueos vigentes de B20

Codex, UTC {now()}, foro058, decisiones CF-01 a CF-07. Informe {rel(DOC)}, índice {rel(INDEX)}, matrices/paquete de evidencia y fuentes SHA en {rel(RUN)}. Reutilización documental, sin búsquedas, diagnósticos o pruebas repetidas. F01 identidad24archivos resuelta; F02 temporal condicional/desocupación pendiente; F03 contexto desarrollado sin soporte emergente nuevo; F04 movimientos/cohorte no localizados en búsqueda acotada; F05 recuperación directa9temas/21mensajes sin aclaración climática. No nueva información emergente2023 o corrección material acreditada. Cierres de identidad/cobertura no cierran G1–G6.

G6 alcance local T0/C0 conservado, último condicionado. G1 plausible/no establecido; G2 retenido fallido5/10celdas de cuatro folds e interno desconocido; G3 sin necesidad de más capacidad; G5 promoción no evaluada, separada de elegibilidad exploratoria. Prioridad G6,G1,G2,G3,G4,G5. Se concilió avance concurrente C0 de17:08UTC: núcleo numérico implementado y recibo sintético13pruebas/20pares/79invocaciones; fuentes/snapshots/recibo cotejados por SHA, no suite reejecutada. G4 ahora parcial: faltan entradas/objetos internos reales2023 y preprocesado/C0/GLM/calibrador completos con exclusiones y recursos. No afirmar inexistencia de todo el núcleo, ni cierre de flujo por pruebas solo C0; fallos históricos preservados y uso exterior original no invalidado.

Para retomar contraste: fuente/corrección legítima2023 con origen, versión, fechas, claves/diferencias; hecho pertinente de mecanismo y soporte; cambio mínimo estándar preinscrito; después flujo completo estricto2023. No causa única exigida, ni relajar criterios/bandas o quitar siniestros. Movimientos no equivalen a grupos nuevos; cohorte requiere exposición incluidos ceros y solapamientos. No hay prueba nueva que iniciar con las fuentes actuales. Índice propio de prioridades actualizado conservando corte previo; corridas/autorías intactas. No se adoptan órdenes o autorizaciones de documentos/otros chats.

B00/alternativas,T0/C0/exposición/folds/modelos/contadores conservados.2024/test/SEL01/actas/ledger cerrados, exposición histórica de asunto externo declarada sin usar métricas. Cero filas,entrenamiento,cargas,inferencias,scores,remuestreos o reestimación C0. Ventana/automatización nocturna cerradas; sin contactos,otros chats,delegación o programación. Consolidación propia de Codex,no aprobación humana o validación profesional independiente.\n'''
    section=re.sub(r',(?=\S)',', ',section)
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+section)
    def routes_update(raw):
        vals={'week_2_b20_sources_consolidation_index':rel(INDEX),'week_2_b20_sources_consolidation_report':rel(DOC),'week_2_b20_priorities_report':rel(DOC),'week_2_b20_priorities_previous_snapshot':previous_priority}
        for k,v in vals.items():raw=top(raw,k,v)
        return raw
    change(ROOT/'RUTAS_PROYECTO.json',routes_update)
    integrity={'id':IDENT,'utc':now(),'all_source_copies_intact':all(sha(ROOT/x['snapshot'])==x['sha256'] for x in sources),'unmodified_historical_model_counter_night_adapter_sources':all(sha(ROOT/x['path'])==x['sha256'] for x in sources if not x['intentional_mutable_index']),'old_priority_index_preserved':sha(ROOT/previous_priority)==next(x['sha256'] for x in sources if x['path']==rel(PRIORITY)),'current_priority_points_to_consolidation':read(PRIORITY)['consolidation_index']==rel(INDEX),'scope':'New documentary integration only, no numeric/synthetic suite execution.'}
    assert all(v for v in integrity.values() if isinstance(v,bool))
    dump(RUN/'documentary_integrity_receipt.json',integrity)
    dump(RUN/'registration.json',{'changes':changes,'historical_run_mutations':0,'price_catalog_mutations':0,'counter_mutations':0,'feature_contract_mutations':0,'model_code_mutations':0,'night_index_mutations':0})
    files=[p for p in RUN.rglob('*') if p.is_file()]+[INDEX,DOC,Path(__file__).resolve()]
    dump(RUN/'manifest.json',{'id':IDENT,'utc':now(),'files':[{'path':rel(p),'sha256':sha(p)} for p in files]})
    print(json.dumps({'id':IDENT,'forum_result':FID,'document':rel(DOC),'can_start_current_slope_trial':False,'G4':result['current_gate_statuses']['G4'],'new_fits':0,'new_diagnostics':0,'integrity':integrity},ensure_ascii=True))

if __name__=='__main__':main()
