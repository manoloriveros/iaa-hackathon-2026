"""Registro de C0/reservas, conservación de cortes y contador común propio."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import unquote
import json,hashlib,re,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026';RUN=REPO/'privado/semana2/desarrollo2023/mecanismo_20261024T002849Z_c8f124bf'
INDEX=REPO/'registro/semana2_sensibilidad_observacion_actual.json';SNAP=REPO/'registro/semana2_sensibilidad_observacion_cola_v1_snapshot.json';COUNTERS=REPO/'registro/semana2_contadores_propios_actual.json';NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
NOW=datetime.now(timezone.utc).isoformat();BACK=RUN/'state_before_registration';BACK.mkdir(exist_ok=False);changes=[]
def dump(path,obj):
    with path.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def top(raw,key,value,add=False):
    val=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if add:
        assert key not in json.loads(raw),key;return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+val+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+val+raw[m.end()+end:]
def change(path,fn):
    before=path.read_bytes();backup=BACK/path.relative_to(ROOT);backup.parent.mkdir(parents=True,exist_ok=True)
    with backup.open('xb') as f:f.write(before)
    after=fn(before.decode('utf-8-sig')).encode('utf-8');tmp=path.with_name(path.name+'.c0reservas.tmp');assert path.read_bytes()==before,'Concurrencia '+str(path)
    with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before,'Concurrencia '+str(path);os.replace(tmp,path)
    changes.append({'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path),'backup':rel(backup)})
i=read(RUN/'sensitivity_index_proposed.json');r=read(RUN/'report.json');p=read(RUN/'plan_snapshot.json');a=read(RUN/'assessment.json');main=ROOT/p['main_model_index'];oldidx=read(INDEX)
assert sha(main)==p['main_model_index_sha256'];assert sha(INDEX)==p['prior_sensitivity_index_sha256'] and sha(COUNTERS)==p['counter_before_sha256'],'Conciliar índice o contadores concurrentes'
for key in ['verification','fixtures','readout_reconciliation']:assert read(ROOT/i[key]['path'])['failed']==0 and sha(ROOT/i[key]['path'])==i[key]['sha256']
with SNAP.open('xb') as f:f.write(INDEX.read_bytes())
i['history']=[{'id':oldidx['id'],'run':oldidx['run'],'documentation':oldidx['documentation'],'index_snapshot':rel(SNAP),'index_sha256':sha(SNAP)},
 {'id':i['id'],'run':i['run'],'documentation':i['documentation']}]
selectorpath=REPO/'registro/semana2_seleccion_actual.json';selector=read(selectorpath);assert not (ROOT/selector['ledger_workspace_relative']).exists();(RUN/'selector_index_at_close.json').write_bytes(selectorpath.read_bytes())
forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';cut=forum.read_bytes()
for suffix in ['025','026']:assert cut.count(('<!-- aporte:COD-S2-20261024-'+suffix+' -->').encode())==1
change(INDEX,lambda raw:json.dumps(i,ensure_ascii=False,indent=2)+'\n')
def counters(raw):
    obj=json.loads(raw);assert obj['cumulative_price_base_fits']==100 and obj['cumulative_closed_form_constants']==90
    obj['increments'].append({'id':p['id'],'run':rel(RUN),'price_GLM_fits':r['new_price_GLM_fits'],'constant_values':r['new_closed_form_constants'],'auxiliary_fits':0,
      'reporting_fits':r['new_reporting_peril_fits'],'exact_reuses_not_fits':r['exact_reuses']})
    obj.update(as_of_utc=NOW,cumulative_price_base_fits=r['cumulative_price_base_fits'],cumulative_closed_form_constants=r['cumulative_closed_form_constants'],latest_sensitivity_index=rel(INDEX),
      supplementary_reporting_peril_fits_since_counter_start=sum(x.get('reporting_fits',0) for x in obj['increments']),
      reporting_counter_notice='75 new reporting-peril fits in C0 sensitivity, separate from historical preparation105 and from pricing/credibility. Counts do not cover other authors.')
    return json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
change(COUNTERS,counters)
def night(raw):
    obj=json.loads(raw);assert obj['current_unit']['id']==p['id'];history=obj['completed_units']
    for entry in history:
        if entry['id']==oldidx['id']:
            entry['index_at_original_registration']=entry.get('index',rel(INDEX));entry['index']=rel(SNAP);entry['index_sha256']=sha(SNAP)
    entry={'id':p['id'],'run':rel(RUN),'index':rel(INDEX),'documentation':i['documentation'],'decision_journal':i['decision_journal'],'verification':i['verification'],'fixtures':i['fixtures'],'forum_result':i['forum_result']}
    assert p['id'] not in [x['id'] for x in history]
    carried={x['id']:x for x in obj.get('open_conditions',[])}
    for warning in read(ROOT/read(main)['assessment'])['warnings']+a['warnings']:carried[warning['id']]=warning
    obj.update(status='scheduled_five_units_verified_conditions_open',updated_utc=NOW,current_unit=None,latest_completed_unit=entry,completed_units=history+[entry],
      current_global_fit_counter_index=rel(COUNTERS),latest_observation_sensitivity_index=rel(INDEX),open_conditions=list(carried.values()),
      next_unit='Review the line-level C0 peril-mixture approximation by business and admissible technical support only2023 before adding price complexity. Preregister new estimation; read counter135pricefits/195constants; prepare overnight balance. No2024/test or credibility retuning.',
      queue=['Diagnose C0 peril-mixture heterogeneity by business/technical support2023, preregister before new fitting/scoring','Preserve uncertainty in capital, climate, prior, tail/reporting/reserves and level; no automatic warning closure','Prepare honest overnight balance with lineage/counters, no unchanged suite or model repetition'],
      no_retraining_or_suite_repetition_for_completed_c0_reserves=True)
    obj.setdefault('integration_decisions',{})['reserves_and_late_reports']='Matched reserve-mark/target/C0 verified; B14 nominal about±2.48%; lateC0component stress−0.658% and point gains reverse under own31 influence. No adopted factor or exclusion.'
    return json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
change(NIGHT,night)
def routes(raw):
    for key,value in [('week_2_observation_sensitivity_report',i['documentation']),('week_2_observation_sensitivity_plan',i['plan'])]:raw=top(raw,key,value)
    return top(raw,'week_2_observation_sensitivity_cola_snapshot',rel(SNAP),True)
def state(raw):
    obj=json.loads(raw);key='week_2_c0_reserves_sensitivity2023_v1_20261024';phase={'as_of_utc':NOW,'phase':'week2_aggregate_level_tail_reserve_late_reporting_sensitivity_verified_B00_retained_2024_closed','current_state_key':key,
      'historical_fields_notice':'Main19recipe catalog remains exact; separate sensitivity index has2cuts, five completed night units and current own counters135/195.'}
    dev={'as_of_utc':NOW,'path_base':'workspace_root','index':rel(INDEX),'run':rel(RUN),'documentation':i['documentation'],'training_years':[2023],'scored_years':[2023],
      'rows_per_stress':50094,'groups':30869,'folds':5,'main_model_index_preserved':rel(main),'main_model_index_sha256':sha(main),'prior_tail_index_snapshot':rel(SNAP),
      'stress_configurations':9,'new_exploratory_contrasts':12,'new_price_GLM_fits':35,'new_closed_form_constants':105,'exact_reuses':30,'new_reporting_peril_fits':75,
      'new_auxiliary_fits':0,'cumulative_price_base_fits':135,'cumulative_closed_form_constants':195,'own_fit_counter_index':rel(COUNTERS),
      'B14_nominal2023':{'base':15606084.086153384,'reserve075':15218380.007030904,'reserve125':15993600.62670173,'late_component_C0':15503357.77986121},
      'reserve2023':1427914.85,'T0_2023':15297103.84,'target_changing_scores_not_superiority':True,'no_joint_tail_reserve_run':True,'nominal2023_is_conditional_not_truth':True,
      'reference':'W2-B00','all_alternatives_preserved':True,'promotion':False,'confirmation_2024_open':False,'ledger_absent':True,'test_predictions':0,
      'verification':i['verification'],'fixtures':i['fixtures'],'readout_reconciliation':i['readout_reconciliation'],'forum_comments':['COD-S2-20261024-025','COD-S2-20261024-026'],
      'decision_journal':i['decision_journal'],'received_Claude004_scope':rel(RUN/'received_evidence_receipt.json'),'pending':[x['effect'] for x in a['warnings']],
      'professional_independent_validation':False,'no_remote':True,'no_submissions':True,'no_delegation':True}
    collab=dict(obj['collaboration_forum'],updated_utc=NOW);headers=re.findall(rb'^## Codex \| ([^|]+) \| ([^|]+) \|',cut,re.M)
    if headers:collab['latest_Codex_comment']=headers[-1][0].decode().strip()
    continuity=dict(obj['week_2_nocturnal_continuation_20261023'],as_of_utc=NOW,latest_completed_unit=p['id'],next_unit=read(NIGHT)['next_unit'])
    for k,v in [('memory_as_of',datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()),('current_phase',phase),('collaboration_forum',collab),('week_2_nocturnal_continuation_20261023',continuity)]:raw=top(raw,k,v)
    return top(raw,key,dev,True)
note=f'''

## Nivel agregado, C0, reportes tardíos y reservas: prueba de 2023

Codex, corte UTC {NOW}. Por instrucción directa del participante se registró el plan S2-C0-RESERVAS2023-v1-20261024 y el comentario 025 a las 00:28:39 UTC, antes de ajustar o puntuar. La corrida mecanismo_20261024T002849Z_c8f124bf terminó sin reintento o cambio de receta; resultado 026 a las 00:35:36 UTC. Informe en docs/semana2/NIVEL_C0_REPORTES_Y_RESERVAS_2023.md. B00 y B01–B18 y el índice principal de 19 recetas siguen exactos. El índice de sensibilidad guarda su segundo corte y el snapshot exacto de la prueba de cola anterior.

R075 y R125 cambian a la vez T0+(b−1)reserva y el enlace C0 de marcas y pesos por peril para b=0,75/1,25, dentro del ajuste propio. B00, B12 y B14 conservan sus recetas estándar, variables y folds. En L1 se retira de la estimación de C0 el componente con mayor coste de demora superior a 365 días dentro de cada ramo/fold, con desempate por ID. Se retiran sus reclamaciones y sus exposiciones de C0, pero todos sus periodos permanecen en el ajuste de precios. Es una sensibilidad de la primera etapa, no una limpieza de siniestros caros ni un reajuste integral del pipeline. No usa el retenido para escoger o estimar.

Los 50.094 periodos y 30.869 componentes de 2023 conservan los cinco folds. El neto suma 15.297.103,84 CU y la reserva 1.427.914,85 CU, el 9,335%. Neto=incurrido−recuperaciones y reserva=incurrido−pagado conciliados en centavos. Contenidos de estos periodos tiene reserva cero: treinta modelos de R075/R125 se reutilizan exactos. No se generaliza a otro año. Se recibieron las fuentes del aporte CLA-S2-20261023-004 de Claude, sin repetir sus 74 controles ni adoptar propuestas en esta receta. Su 17,8% de reserva sobre ambos años tiene otro ámbito y no valida los modelos o el último.

El nominal condicionado de B14 pasa de 15,606084 millones CU a 15,218380/15,993601 bajo R075/R125 (−2,484%/+2,483%) y a 15,503358 bajo L1 (−0,658%). Es exposición nominal de esos mismos periodos de 2023 por su tasa bajo coste completo, no precios de 2025/test o verdad de último. Cambiar la respuesta cambia el estimando del D². No se elige el factor de reservas mediante comparación de scores con targets distintos ni A/E cercano a uno. La prueba de cola anterior se conserva sin repetir: otra escala nominal puede mantener el score observado. No se combinan aditivamente escenarios ni se presentan como límites estadísticos.

Se calcularon doce contrastes nuevos con 2.000 sorteos comunes y nula propia del escenario: tres comparaciones entre familias dentro de cada escenario y tres L1 frente a sus padres bajo el mismo T0. L1/B14 da delta D² +0,00007145, intervalo exploratorio 95% [+0,00000100; +0,00017868], pero −0,00004881 al retirar sus 31 grupos de evaluación más favorables. Las ventajas de L1/B00 y L1/B12 también invierten signo. Esos grupos son diagnóstico de evaluación, no se borran o usan para reajustar. Sin promoción, retiro, equivalencia, adopción de curva o lista final tras búsqueda adaptativa.

Hubo 35 GLM y 105 constantes nuevos, 30 reutilizaciones exactas y 75 curvas de reporte nuevas por separado; cero auxiliares nuevos. El contador propio actual es 135 ajustes de precio y 195 constantes, más 30 auxiliares de credibilidad anteriores separados. Las 75 curvas de esta unidad tampoco se confunden con las 105 de la preparación histórica. Pasaron 1.477 controles separados, 48 adversos focales y seis conciliaciones adicionales, con solapamiento. El comprobador no importa el productor y bloquea fit: producto de probabilidades y días admisibles reconstruyen C0; verifica centavos, marcas, ámbito, óptimos, gradientes, imputación, exp(X beta), segmentos y doce remuestreos por multiplicidades. Los adversos cubren costes enormes del retenido sin cambio de selección, orden, empates, frontera de 365 días, identidad sin coste tardío, 2024/test/duplicados y ausencia de costes/IDs como predictores. Es revisión técnica propia, no profesional independiente.

Siguen condicionados la masa y severidad fuera de soporte, reservas, estacionariedad, dependencia coste/reporte y composición individual por peril. Una validación agrupada de 2023 al corte 2024-12-31 no es conocimiento disponible al inicio de 2023. Se conservan las condiciones de capital, clima y prior de credibilidad y los responsables de hallazgos ajenos. Próxima unidad nocturna: revisar la mezcla por peril y negocio antes de añadir complejidad, con receta previa si hay estimación nueva, y preparar el balance. Quinta unidad terminada, programación existente sin cambios. 2024 sigue cerrado expresamente: ledger ausente, sin entrenamiento de precio, predicciones o scores de ese año o test; sin remoto, envíos, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones.
'''
change(ROOT/'RUTAS_PROYECTO.json',routes);change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+note)
update='\n\n## C0 y reservas: quinto avance nocturno\n\nLa [sensibilidad de reservas y reportes tardíos](../Repositorio_IAA2026/docs/semana2/NIVEL_C0_REPORTES_Y_RESERVAS_2023.md) usa modelos estándar solo en 2023. B14 mueve su nivel nominal condicionado alrededor de ±2,48% al cambiar reservas y −0,66% al perturbar un componente del ajuste de C0. Los puntos positivos de ese adverso invierten signo bajo influencia. Se conservan B00, todas las alternativas, el resultado previo de cola y 2024 cerrado, sin adoptar factor o exclusión. Contador propio: 135 ajustes de precio y 195 constantes; curvas de reporte y auxiliares por separado.\n'
for name in ['README.md','PLAN_TRABAJO.md']:change(ROOT/'Hackaton/Semana 2'/name,lambda raw:raw+update)
change(REPO/'docs/semana2/SENSIBILIDAD_COLA_Y_NIVEL_2023.md',lambda raw:raw+'\n\n## Corte posterior: reservas y C0 ante reportes tardíos\n\nLa [siguiente prueba](NIVEL_C0_REPORTES_Y_RESERVAS_2023.md) conserva esta evidencia de cola y añade reservas coherentes y un adverso del estimador C0. El [snapshot del índice de cola](../../registro/semana2_sensibilidad_observacion_cola_v1_snapshot.json) conserva exactamente este corte; el índice activo recoge el avance.\n')
change(REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',lambda raw:raw+'\n\n## Quinta unidad: reservas y reportes tardíos\n\nLa [prueba registrada](NIVEL_C0_REPORTES_Y_RESERVAS_2023.md) mantiene los modelos estándar y separa cambios de respuesta/enlace por reservas de una perturbación del ajuste C0. No adopta un factor o regla de exclusión; los pequeños puntos favorables del adverso se invierten bajo influencia. B00 y catálogo exactos, 2024 cerrado. Próxima unidad: mezcla por peril y negocio de 2023, con receta previa, y balance nocturno. Contador propio actual: 135 ajustes de precio y 195 constantes; auxiliares y nuevas curvas de reporte por separado.\n')
change(REPO/'registro/semana2_listo_entrenar.json',lambda raw:top(raw,'latest_observation_sensitivity_execution',{'as_of_utc':NOW,'index':rel(INDEX),'documentation':i['documentation'],'run':rel(RUN),'training_years':[2023],
 'status':i['status'],'counters':rel(COUNTERS),'confirmation_2024_open':False,'test_predictions':0,'historical_fields_preserved':True}))
dump(REPO/'registro/semana2_c0_reservas2023_pruebas_v1.json',{'utc':NOW,'author':'Codex','verification':i['verification'],'fixtures':i['fixtures'],'readout_reconciliation':i['readout_reconciliation'],'professional_independent_validation':False})
dump(RUN/'registration.json',{'utc':NOW,'changes':changes,'main_catalog_sha256_preserved':sha(main),'reference':'W2-B00','confirmation_2024_open':False})
dump(RUN/'forum_receipts.json',{'source':'Serialized helper responses in this chat','receipts':[
 {'id':'COD-S2-20261024-025','utc':'2026-10-24T00:28:39+00:00','previous_sha256':'0929633b3a759de6ef1bd06950f143d98a73a3bd43f49e660a6f06cd2568565a','sha256_at_append':'e54eb977c22a3b1c7e09deb9d91fe639399f63f0e7b547dc71e83dd2dc412ae7'},
 {'id':'COD-S2-20261024-026','utc':'2026-10-24T00:35:36+00:00','previous_sha256':'e54eb977c22a3b1c7e09deb9d91fe639399f63f0e7b547dc71e83dd2dc412ae7','sha256_at_append':'951a307a57049ce5971390e9da8a28356d3a3d393a5bdfd29b892bb2ed9286d8'}]})
checks=[]
def check(n,v):checks.append({'name':n,'pass':bool(v)})
for key in ['report','plan','producer','oof','manifest','assessment','decision_journal']:check('Index '+key,sha(ROOT/i[key])==i[key+'_sha256'])
for key in ['verification','fixtures','readout_reconciliation']:check('Check receipt '+key,sha(ROOT/i[key]['path'])==i[key]['sha256'] and read(ROOT/i[key]['path'])['failed']==0)
check('Main catalog exact',sha(main)==p['main_model_index_sha256'] and read(main)['reference']=='W2-B00' and len(read(main)['alternatives_preserved'])==18)
check('Tail snapshot exact',sha(SNAP)==p['prior_sensitivity_index_sha256'] and SNAP.read_bytes()==(BACK/'Hackaton/Repositorio_IAA2026/registro/semana2_sensibilidad_observacion_actual.json').read_bytes())
oldstate=read(BACK/'Preparación/ESTADO_PROYECTO.json');newstate=read(ROOT/'Preparación/ESTADO_PROYECTO.json');check('Historical state branches preserved',all(newstate.get(k)==v for k,v in oldstate.items() if k not in ['memory_as_of','current_phase','collaboration_forum','week_2_nocturnal_continuation_20261023']))
oldroutes=read(BACK/'RUTAS_PROYECTO.json');newroutes=read(ROOT/'RUTAS_PROYECTO.json');check('Other routes preserved',all(newroutes.get(k)==v for k,v in oldroutes.items() if k not in ['week_2_observation_sensitivity_report','week_2_observation_sensitivity_plan']))
for k,v in newroutes.items():
    if k.startswith('week_2_'):check('Route '+k,(ROOT/v).exists())
for it in changes:
    if it['path'].endswith('.md'):check('Prose prefix '+it['path'],(ROOT/it['path']).read_bytes().startswith((ROOT/it['backup']).read_bytes()))
for doc in [ROOT/i['documentation'],REPO/'docs/semana2/SENSIBILIDAD_COLA_Y_NIVEL_2023.md',REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md',forum]:
    for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        target=link.strip('<>').split('#')[0]
        if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',target):continue
        check('Link '+rel(doc)+' -> '+target,(doc.parent/unquote(target)).resolve().exists())
for it in p['frozen_sources']:check('Frozen source '+it['path'],sha(ROOT/it['path'])==it['sha256'])
n=read(NIGHT);oldn=read(ROOT/'Hackaton/Semana 2/Codex/nocturno_antes_c0_reservas2023.json');check('Fifth unit complete',n['current_unit'] is None and n['latest_completed_unit']['id']==p['id'] and len(n['completed_units'])==5)
check('Native schedule unchanged',all(n[k]==oldn[k] for k in ['window_start','window_end','frequency','automation_id','automation_kind','automation_target_thread','same_chat']))
co=read(COUNTERS);check('Counters reconciled once',co['baseline']['price_base_fits']+sum(x['price_GLM_fits'] for x in co['increments'])==135==co['cumulative_price_base_fits'] and co['baseline']['constants']+sum(x['constant_values'] for x in co['increments'])==195==co['cumulative_closed_form_constants'])
check('Reporting separate',co['supplementary_reporting_peril_fits_since_counter_start']==75 and co['auxiliary_Poisson_Gamma_fits_separate']==30)
check('2024ledger absent',not (ROOT/selector['ledger_workspace_relative']).exists());result={'utc':NOW,'scope':'Registration, sources and links only; no repeated statistical suite or fit','passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks}
dump(RUN/'closure_verification.json',result);assert result['failed']==0,[x for x in checks if not x['pass']]
paths={q for q in RUN.rglob('*') if q.is_file()};paths.update(ROOT/x['path'] for x in changes);paths.update([ROOT/i['documentation'],ROOT/i['plan'],ROOT/i['producer'],SNAP,Path(__file__),forum,REPO/'registro/semana2_c0_reservas2023_pruebas_v1.json'])
paths.update(REPO/'herramientas'/f'{name}_c0_reservas2023_semana2.py' for name in ['documentar','probar','verificar'])
paths.update(ROOT/'Hackaton/Semana 2/Codex'/name for name in ['preinscribir_c0_reservas2023.py','c0_reservas2023_preinscripcion.md','c0_reservas2023_resultado.md','nocturno_antes_c0_reservas2023.json','sensibilidad_antes_c0_reservas2023.json','contadores_antes_c0_reservas2023.json'])
dump(RUN/'closure_manifest.json',{'utc':NOW,'notice':'Corte histórico; archivos compartidos pueden cambiar después sin reescribir este recibo.','files':[{'path':rel(q),'sha256':sha(q),'bytes':q.stat().st_size} for q in sorted(paths)],'reference':'W2-B00','confirmation_2024_open':False})
print(json.dumps({'registered':rel(INDEX),'main_catalog_unchanged':True,'closure_checks':result['passed'],'failed':0,'price_fits':135,'constants':195,'night_units':5}))
