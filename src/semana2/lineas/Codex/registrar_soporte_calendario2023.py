"""Cierre de diagnóstico sin ajustes: séptima unidad y balance parcial."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import unquote
import json,hashlib,re,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/soporte_20261024T010555Z_c4428b52'
NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
INDEX=REPO/'registro/semana2_soporte_calendario2023_actual.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
NOW=datetime.now(timezone.utc).isoformat();changes=[]
BACK=RUN/'state_before_registration'

def dump(path,obj):
    with path.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')

def top(raw,key,value,add=False):
    val=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if add:
        assert key not in json.loads(raw),key
        return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+val+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():])
    return raw[:m.end()]+val+raw[m.end()+end:]

def change(path,fn):
    before=path.read_bytes();backup=BACK/path.relative_to(ROOT);backup.parent.mkdir(parents=True,exist_ok=True)
    with backup.open('xb') as f:f.write(before)
    after=fn(before.decode('utf-8-sig')).encode('utf-8');tmp=path.with_name(path.name+'.soportecierre.tmp')
    assert path.read_bytes()==before,'Concurrencia '+str(path)
    with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before,'Concurrencia '+str(path);os.replace(tmp,path)
    changes.append({'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path),'backup':rel(backup)})

p=read(RUN/'plan_snapshot.json');i=read(RUN/'index_proposed.json');r=read(RUN/'report.json');v=read(RUN/'verification.json');q=read(RUN/'readout_reconciliation.json')
assert r['failed']==v['failed']==q['failed']==0
assert read(NIGHT)['current_unit']['id']==p['id']
assert all(sha(ROOT/x['path'])==x['sha256'] for x in p['frozen_sources'])
assert not INDEX.exists()
BACK.mkdir(exist_ok=False)
forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';cut=forum.read_bytes()
for suffix in ['030','031']:assert cut.count(('<!-- aporte:COD-S2-20261024-'+suffix+' -->').encode())==1
main=REPO/'registro/semana2_desarrollo2023_actual.json';obsidx=REPO/'registro/semana2_sensibilidad_observacion_actual.json';counters=REPO/'registro/semana2_contadores_propios_actual.json'
preserved={rel(x):sha(x) for x in [main,obsidx,counters]}
guard='Only emit author, ID and UTC from forum inventory via herramientas/leer_foro_semana2_seguro.py. Never emit external subjects/titles, bodies, actas, predictions, scores or SEL01 artifacts. Do not dump whole shared memory/state: select own current branches and own dated sections. An external subject already exposed2024 outcome metrics; do not claim complete blindness or use those outcomes for2023 choices. No ledger reading or second batch.'
exposure=dict(p['governance_exposure'],scope='External2024 metrics seen in one forum subject only; no body, acta, prediction or ledger opened. This is a disclosed information exposure, not a valid confirmation of this line.',
    subsequent_2023_fit_or_score_in_this_unit=False,safe_reader=rel(REPO/'herramientas/leer_foro_semana2_seguro.py'),verification=rel(RUN/'verification.json'))
i.update(forum_reading_guard=guard,confirmation_header_exposure=exposure,main_catalog_sha256_preserved=sha(main),sensitivity_index_sha256_preserved=sha(obsidx),own_counters_sha256_preserved=sha(counters))
dump(INDEX,i)

def night(raw):
    n=json.loads(raw);assert n['current_unit']['id']==p['id'] and len(n['completed_units'])==6
    entry={k:i[k] for k in ['id','run','documentation','decision_journal','verification','forum_result']};entry['index']=rel(INDEX)
    warnings={x['id']:x for x in n['open_conditions']}
    for x in i['warnings']:warnings[x['id']]=x
    n.update(status='scheduled_seven_units_verified_support_and_scope_conditions_open',updated_utc=NOW,current_unit=None,
        latest_completed_unit=entry,completed_units=n['completed_units']+[entry],open_conditions=list(warnings.values()),
        latest_data_support_audit_index=rel(INDEX),partial_night_balance=i['partial_balance'],forum_reading_guard=guard,confirmation_header_exposure=exposure,
        next_unit='Review admissible technical coverage and denominators by peril, only2023 and persisted folds. Descriptive audit first; no complexity or fits unless a concrete residual failure and frozen recipe justify them. Own pricing counters165/285 unchanged. Use safe forum inventory(author/id/UTC only), own shared-document branches and disclose prior2024 header exposure. No ledger, second batch or external confirmation artifacts.',
        queue=['Audit technical coverage/peril support only2023 before any new timing or pricing model',
            'Preserve conditional ultimate, reserve, capital, climate and credibility findings; no automatic warning closure',
            'Update partial balance only for new evidence; final honest balance at07:00Bogota, do not repeat unchanged suites'],
        no_retraining_or_suite_repetition_for_completed_calendar_support=True)
    n['confirmation_scope_conflict'].update(header_metric_exposure_recorded=True,external_2024_metrics_seen_in_subject=True,
        external_2024_prediction_files_or_acta_read=False,complete_blindness_claim_allowed=False,
        next_action='Keep external confirmation quarantined. Disclose subject exposure; do not use it for2023 choices. No additional confirmation batch.')
    n['integration_decisions']['calendar_support']='Direct daily exposure audit verified; newbusiness has less mature exposure at long delays and sparse reverse-risk support. No business timing curve adopted, no new price model or score.'
    return json.dumps(n,ensure_ascii=False,indent=2)+'\n'
change(NIGHT,night)

def routes(raw):
    for key,value in [('week_2_calendar_support_index',rel(INDEX)),('week_2_calendar_support_report',i['documentation']),('week_2_calendar_support_plan',i['plan']),('week_2_partial_night_balance',i['partial_balance'])]:raw=top(raw,key,value,True)
    return raw
change(ROOT/'RUTAS_PROYECTO.json',routes)
statekey='week_2_calendar_reporting_support2023_v1_20261024'
def state(raw):
    obj=json.loads(raw)
    phase={'as_of_utc':NOW,'phase':'week2_calendar_reporting_support_verified_no_new_fit_score_2024_header_exposure_disclosed','current_state_key':statekey,
        'historical_fields_notice':'Previous fields are dated cuts. Seven night units completed, own pricing counters165/285 and main19/sensitivity3 indices unchanged; no complete-blindness claim after external subject exposure.'}
    dev={'as_of_utc':NOW,'index':rel(INDEX),'run':rel(RUN),'documentation':i['documentation'],'partial_balance':i['partial_balance'],'audited_policy_years':[2023],
        'rows':50094,'groups':30869,'folds':5,'new_fits':0,'new_curves':0,'new_scores':0,'new_bootstrap':0,'cumulative_price_base_fits':165,'cumulative_closed_form_constants':285,
        'verification':i['verification'],'readout_reconciliation':i['readout_reconciliation'],'reference':'W2-B00','all_alternatives_preserved':True,
        'confirmation_opened_by_this_task':False,'ledger_read':False,'external_2024_metrics_seen_in_subject':True,'external_2024_prediction_files_or_acta_read':False,
        'complete_blindness_claim_allowed':False,'confirmation_header_exposure':exposure,'forum_reading_guard':guard,'professional_independent_validation':False,
        'forum_comments':['COD-S2-20261024-030','COD-S2-20261024-031']}
    continuity=dict(obj['week_2_nocturnal_continuation_20261023'],as_of_utc=NOW,latest_completed_unit=p['id'],next_unit=read(NIGHT)['next_unit'],forum_reading_guard=guard,confirmation_header_exposure=exposure)
    collab=dict(obj['collaboration_forum'],updated_utc=NOW,latest_Codex_comment='COD-S2-20261024-031')
    for key,value in [('current_phase',phase),('memory_as_of',datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()),('week_2_nocturnal_continuation_20261023',continuity),('collaboration_forum',collab)]:raw=top(raw,key,value)
    return top(raw,statekey,dev,True)
change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
note=f'''

## Soporte de calendario y reporte: séptimo avance y balance parcial

Codex, corte UTC {NOW}. La sexta unidad de mezcla estaba cerrada y no se repitió. Se registró en foro 030 la hipótesis y el alcance del diagnóstico de calendario antes de calcular; resultado 031. Plan S2-SOPORTE-CALENDARIO2023-v1-20261024, corrida soporte_20261024T010555Z_c4428b52, informe SOPORTE_CALENDARIO_REPORTE_2023.md e índice semana2_soporte_calendario2023_actual.json. El balance BALANCE_NOCTURNO_PARCIAL_20261024.md es parcial, no el cierre de las 07:00 de Bogotá.

Esta unidad no ajusta modelos o curvas, no predice precios, no puntúa y no hace bootstrap. Conserva 50.094 periodos, 30.869 componentes y cinco folds de 2023, además de B00 y todas las alternativas. Los índices principal de 19 recetas y sensibilidad de tres cortes y los contadores de precio 165/285 siguen exactos. Las primeras etapas de mezcla, curvas de reporte y auxiliares permanecen separadas y sin nuevos ajustes.

El calendario se reconstruye por días inclusivos y exposición nominal por día. Todos los días cubiertos y pérdidas observadas son de calendario 2023 y tienen al menos 366 días de seguimiento al corte 2024-12-31. A 540 días, la exposición madura de renovación es aproximadamente 52,33%, frente a 26,54–27,33% en nuevo negocio. Las distancias totales entre calendarios rondan 25–26% según ramo/fold. Los rangos de cinco ajustes solapan; no son cinco muestras independientes ni una explicación causal del deterioro de precios. Para perils con extremo de demora dentro de 365 días, la completitud congelada es uno por construcción bajo esa cola; esto no prueba que la cola real termine allí.

El perfil general deduplica 4.567 siniestros que aparecen en cuatro vistas de ajuste. En edificios nuevos hay 40 reclamaciones y demora máxima observada de 160 días; en contenidos nuevos, 37 y 44 días; en autos nuevos, 315 y 516 días. Los siniestros conocidos después de 365 días son cero, cero y tres, respectivamente. Es información truncada al corte y no probabilidades incondicionales o ausencia de riesgo futuro. En lesiones corporales de autos, los extremos agrupados de 609–653 días dejan 4,27–11,19% de exposición nueva madura y de uno a cinco siniestros nuevos en riesgo inverso, sin eventos nuevos en esos extremos. No se admite una curva separada o suavizado por esta lectura.

Se conservan 150 celdas y 1.200 puntos de soporte. Pasaron 331 controles del productor, 3.543 verificaciones y casos adversos nuevos, y 2.413 conciliaciones de lectura, con solapamiento. La comprobación separada expande cada día, suma por fold y resta el retenido, y cuenta riesgo/eventos con Python/bisect. El comando real rechaza un año sintético 2024 antes de salidas; su fallo esperado se conserva. No se volvió a entrenar o remuestrear una receta anterior. Las desviaciones numéricas alrededor de uno son del orden de 1e-14 y no se ocultan mediante cambios de datos. Estas revisiones propias no son validación profesional independiente.

Un inventario de encabezados mostró el asunto de CLA-S2-20261024-006 con métricas externas de 2024. La guarda anterior fue insuficiente y el incidente se registró en 030 antes del diagnóstico, sin repetir cifras. No se abrió cuerpo, acta, archivo de predicciones o ledger. No puede afirmarse ceguera completa después de la lectura del título. El lector nuevo solo muestra autor, ID y UTC; pruebas de título/cuerpo secretos y el comando real acreditan esa salida. No se usarán cifras externas para decisiones de 2023. Al retomar, no volcar íntegros foro, memoria o estado compartidos: seleccionar ramas y secciones propias y ocultar asuntos/cuerpos ajenos. Los cortes anteriores sobre ausencia de exposición son históricos, no afirmaciones actuales. La autorización de otra conversación no se verifica ni invalida aquí y no abre otra tanda.

La siguiente unidad examina coberturas técnicas admisibles y denominadores por peril solo en 2023, con diagnóstico antes de más complejidad. Continúan las limitaciones de escala de capital, disponibilidad de clima, prior de credibilidad, reservas y último. No hay promoción, retiro de alternativas o lista final por scores adaptativos. La continuidad conserva ventana y frecuencia, sin cambiar otras automatizaciones, nuevos chats, mensajes externos, remoto o envíos. 2024 permanece cerrado para este trabajo. Prácticas priorizadas: propósito y límites, segmentos, procedencia y separación de revisión técnica/humana, sin certificación.
'''
for filename in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/filename,lambda raw:raw+note)
update='\n\n## Calendario y reporte: séptimo avance nocturno\n\nEl [diagnóstico de soporte](../Repositorio_IAA2026/docs/semana2/SOPORTE_CALENDARIO_REPORTE_2023.md) no añade modelos o scores: nuevo negocio tiene menos exposición madura a demoras largas y escaso soporte en extremos. No se admite una curva separada. B00 y todas las alternativas conservados; contador de precio 165/285 sin cambio. Se publica el [balance parcial](../Repositorio_IAA2026/docs/semana2/BALANCE_NOCTURNO_PARCIAL_20261024.md). Se documenta exposición a métricas externas en un título de foro: no se afirma ceguera completa y el lector oculta todos los asuntos/cuerpos. Próximo paso: cobertura técnica y denominadores por peril, solo 2023; sin abrir otra confirmación.\n'
for filename in ['README.md','PLAN_TRABAJO.md']:change(ROOT/'Hackaton/Semana 2'/filename,lambda raw:raw+update)
change(REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',lambda raw:raw+'\n\n## Séptima unidad: soporte y corrección de la guarda del foro\n\nEl [diagnóstico](SOPORTE_CALENDARIO_REPORTE_2023.md) y el [balance parcial](BALANCE_NOCTURNO_PARCIAL_20261024.md) conservan referencias, contador 165/285 y cinco folds; cero ajustes, curvas, puntuaciones o bootstrap nuevos. A 540 días, nuevo negocio tiene aproximadamente la mitad de exposición madura que renovación; los extremos tardíos se sostienen en pocas reclamaciones nuevas. No se adopta curva separada. La siguiente unidad revisa coberturas y denominadores por peril antes de otro modelo.\n\nLa guarda de leer encabezados queda sustituida: un asunto ajeno ya mostró métricas de 2024 (incidente registrado en foro 030). No se afirma ceguera completa. Usar herramientas/leer_foro_semana2_seguro.py, que solo devuelve autor, ID y UTC, sin asuntos o cuerpos. Tampoco volcar íntegros memoria o estado compartidos: seleccionar ramas actuales y secciones propias para no exponer resultados ajenos. No usar la información externa para elegir en 2023; no leer acta, predicciones o ledger ni abrir otra tanda. Los avisos previos de no exposición describen su corte histórico. La instrucción de mantener 2024 cerrado en este trabajo sigue vigente; no se verifica o invalida la autorización anunciada en otro chat.\n')
change(REPO/'docs/semana2/MEZCLA_C0_PERIL_Y_NEGOCIO_2023.md',lambda raw:raw+'\n\n## Seguimiento posterior: calendario y exposición de información\n\nEl [diagnóstico siguiente](SOPORTE_CALENDARIO_REPORTE_2023.md) conserva esta prueba y examina calendario y soporte sin nuevos ajustes o scores. Después del corte de este informe, un título del foro mostró métricas ajenas de 2024; se registra el incidente y se corrige el lector para ocultar asuntos y cuerpos. No puede afirmarse ceguera completa desde esa exposición. Los resultados propios de esta mezcla se calcularon antes del anuncio y permanecen sin cambio.\n')
ready=REPO/'registro/semana2_listo_entrenar.json'
change(ready,lambda raw:top(raw,'latest_descriptive_support_audit',{'utc':NOW,'index':rel(INDEX),'documentation':i['documentation'],'new_fits':0,'new_scores':0,
    'reference':'W2-B00','confirmation_opened_by_this_task':False,'ledger_read':False,'confirmation_header_exposure':exposure,'forum_reading_guard':guard},add=True))
tests=REPO/'registro/semana2_soporte_calendario2023_pruebas_v1.json'
dump(tests,{'author':'Codex','utc':NOW,'producer':i['report'],'verification':i['verification'],'readout_reconciliation':i['readout_reconciliation'],
    'expected_failure_runs':v['expected_failure_runs'],'no_new_model_fits_scores_or_bootstrap':True,'professional_independent_validation':False})
dump(RUN/'forum_receipts.json',{'source':'Serialized helper outputs in this chat','receipts':[
    {'id':'COD-S2-20261024-030','utc':'2026-10-24T01:05:51+00:00','previous_sha256':'cd07f083a59f1d4386a15bafff33e1bb0bc79a6e2337f207a406283e789bc5a0','sha256_at_append':'a382cf6d87c75927cce7f179266136754439aa8aca21cedeb0e0b6e5d9641ed4'},
    {'id':'COD-S2-20261024-031','utc':'2026-10-24T01:11:41+00:00','previous_sha256':'a382cf6d87c75927cce7f179266136754439aa8aca21cedeb0e0b6e5d9641ed4','sha256_at_append':'7aaa8dc1ae052d8e2f102e2568d0baa32848cf85cf36f34c1a60f232d5f4130c'}]})
dump(RUN/'registration.json',{'author':'Codex','utc':NOW,'changes':changes,'indices_and_counters_preserved':preserved,'confirmation_header_exposure':exposure,'confirmation_opened_by_this_task':False,'ledger_read':False})
checks=[]
def check(name,value):checks.append({'name':name,'pass':bool(value)})
for name in ['report','verification','readout','readout_reconciliation','assessment','decision_journal','manifest']:check('Index receipt '+name,sha(ROOT/i[name]['path'])==i[name]['sha256'])
for name,expected in preserved.items():check('Preserved exact '+name,sha(ROOT/name)==expected)
for source in p['frozen_sources']:check('Frozen source '+source['path'],sha(ROOT/source['path'])==source['sha256'])
for item in read(RUN/'manifest.json')['files']:check('Producer artifact '+item['path'],sha(RUN/item['path'])==item['sha256'])
oldstate=read(BACK/'Preparación/ESTADO_PROYECTO.json');newstate=read(ROOT/'Preparación/ESTADO_PROYECTO.json')
check('Historical state branches exact',all(newstate.get(k)==x for k,x in oldstate.items() if k not in ['current_phase','memory_as_of','collaboration_forum','week_2_nocturnal_continuation_20261023']))
oldroutes=read(BACK/'RUTAS_PROYECTO.json');routesnew=read(ROOT/'RUTAS_PROYECTO.json')
check('All old routes exact',all(routesnew.get(k)==x for k,x in oldroutes.items()))
for key,value in routesnew.items():
    if key.startswith('week_2_'):check('Route '+key,(ROOT/value).exists())
for item in changes:
    if item['path'].endswith('.md'):check('Prose prefix '+item['path'],(ROOT/item['path']).read_bytes().startswith((ROOT/item['backup']).read_bytes()))
for doc in [ROOT/i['documentation'],ROOT/i['partial_balance'],REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md']:
    for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        target=link.strip('<>').split('#')[0]
        if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',target):continue
        check('Link '+rel(doc)+' -> '+target,(doc.parent/unquote(target)).resolve().exists())
n=read(NIGHT);oldn=read(BACK/NIGHT.relative_to(ROOT))
check('Seventh unit complete',n['current_unit'] is None and n['latest_completed_unit']['id']==p['id'] and len(n['completed_units'])==7)
check('Native schedule unchanged',all(n[k]==oldn[k] for k in ['window_start','window_end','frequency','automation_id','automation_kind','automation_target_thread','same_chat','other_automations_changed']))
check('Exposure and reader guard saved',n['confirmation_header_exposure']['use_for_2023_choices'] is False and n['confirmation_scope_conflict']['complete_blindness_claim_allowed'] is False and 'Never emit external subjects' in n['forum_reading_guard'])
check('Own scope remains2024closed',n['confirmation_2024_open'] is False and n['test_predictions_authorized'] is False and newstate[statekey]['ledger_read'] is False)
check('Forum prefix preserved',forum.read_bytes().startswith(cut))
result={'utc':NOW,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'scope':'Closure/source/links only, not a repeated statistical suite'}
dump(RUN/'closure_verification.json',result);assert result['failed']==0,[x for x in checks if not x['pass']]
paths={x for x in RUN.rglob('*') if x.is_file()};paths.update(ROOT/x['path'] for x in changes)
paths.update([INDEX,tests,ROOT/i['documentation'],ROOT/i['partial_balance'],ROOT/i['plan'],ROOT/p['code'],Path(__file__),forum])
paths.update(REPO/'herramientas'/filename for filename in ['leer_foro_semana2_seguro.py','verificar_soporte_calendario2023_semana2.py','documentar_soporte_calendario2023_semana2.py'])
paths.update(ROOT/'Hackaton/Semana 2/Codex'/filename for filename in ['preinscribir_soporte_calendario2023.py','soporte_calendario2023_preinscripcion.md','soporte_calendario2023_resultado.md','nocturno_antes_soporte_calendario2023.json'])
for path in v['expected_failure_runs']:paths.update(x for x in (ROOT/path).rglob('*') if x.is_file())
dump(RUN/'closure_manifest.json',{'utc':NOW,'notice':'Dated cut. Shared files may change in later cycles; do not rewrite this receipt.','files':[{'path':rel(x),'sha256':sha(x),'bytes':x.stat().st_size} for x in sorted(paths)],'no_new_fits_scores_bootstrap':True,'external2024_subject_exposure_disclosed':True})
print(json.dumps({'registered':rel(INDEX),'closure_checks':result['passed'],'failed':0,'night_units':7,'price_counters_unchanged':[165,285],'no_new_fit_score_bootstrap':True,'header_exposure_disclosed':True}))
