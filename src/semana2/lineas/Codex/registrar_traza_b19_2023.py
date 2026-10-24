"""Cierre conservador de la traza B19, con respaldos y continuidad concurrente."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import unquote
import hashlib,json,os,re

ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/traza_b19_20261024T021036Z_fe5038de'
INDEX=REPO/'registro/semana2_b19_traza_actual.json';NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
STATEKEY='week_2_B19_claim_source_trace2023_v1_20261024'
NOW=datetime.now(timezone.utc).isoformat();BACK=RUN/'state_before_registration';changes=[]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()


def dump(path,obj):
    with path.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')


def top(raw,key,value,add=False):
    val=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if add:
        assert key not in json.loads(raw),key
        return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+val+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+val+raw[m.end()+end:]


def change(path,fn):
    before=path.read_bytes();backup=BACK/path.relative_to(ROOT);backup.parent.mkdir(parents=True,exist_ok=True)
    with backup.open('xb') as f:f.write(before)
    after=fn(before.decode('utf-8-sig')).encode('utf-8')
    if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
    tmp=path.with_name(path.name+'.trazab19cierre.tmp')
    assert path.read_bytes()==before,'Concurrencia antes de escritura '+rel(path)
    with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before,'Concurrencia antes de reemplazo '+rel(path)
    os.replace(tmp,path)
    item={'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path),'backup':rel(backup)}
    changes.append(item)
    with (RUN/'registration_steps.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(item,ensure_ascii=False)+'\n')


def main():
    p=read(RUN/'plan_snapshot.json');i=read(RUN/'index_proposed.json');r=read(RUN/'report.json');v=read(RUN/'verification.json');q=read(RUN/'readout_reconciliation.json');facts=read(RUN/'readout.json')
    assert r['failed']==v['failed']==q['failed']==0
    assert all(r[k]==v[k]==0 for k in ['new_fits','new_scores','new_bootstrap'])
    assert all(sha(ROOT/x['path'])==x['sha256'] for x in p['frozen_sources'])
    assert not INDEX.exists() and not BACK.exists()
    n=read(NIGHT);assert not any(x['id']==p['id'] for x in n['completed_units'])
    assert n['confirmation_2024_open'] is False
    forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';forum_cut=forum.read_bytes()
    for ending in ['038','039']:assert forum_cut.count(('<!-- aporte:COD-S2-20261024-'+ending+' -->').encode())==1
    BACK.mkdir()
    unchanged={rel(REPO/'registro'/name):sha(REPO/'registro'/name) for name in [
        'semana2_desarrollo2023_actual.json','semana2_contadores_propios_actual.json','semana2_glm_ridge_actual.json',
        'semana2_b19_estabilidad_actual.json','semana2_sensibilidad_observacion_actual.json']}
    counter=read(REPO/'registro/semana2_contadores_propios_actual.json')
    values={k:counter[k] for k in ['cumulative_price_base_fits','cumulative_closed_form_constants']}
    i.update(as_of_registration_utc=NOW,documentation_sha256=sha(ROOT/i['documentation']),unrelated_indices_and_counters_cut=unchanged,
             counter_values_cut=values,this_unit_counter_increment=0,this_unit_catalog_mutations=0)
    dump(INDEX,i)
    def night(raw):
        obj=json.loads(raw);assert not any(x['id']==p['id'] for x in obj['completed_units'])
        current=obj.get('current_unit');ours=(current or {}).get('id')==p['id'];foreign=current is not None and not ours
        entry={k:i[k] for k in ['id','run','documentation','verification','decision_journal','forum_result']}
        entry.update(index=rel(INDEX),completed_utc=NOW,new_fits=0,new_scores=0,new_bootstrap=0)
        obj['completed_units'].append(entry)
        obj.update(updated_utc=NOW,latest_completed_unit=entry,latest_B19_source_trace_index=rel(INDEX),
                   latest_artifact_diagnostic=entry,next_artifact_diagnostic=i['next_artifact_diagnostic'],
                   no_retraining_or_suite_repetition_for_completed_B19_source_trace=True)
        if ours:obj['current_unit']=None
        if not foreign:
            obj['status']='scheduled_'+str(len(obj['completed_units']))+'_units_B19_source_trace_reconciled_limits_open'
            obj['next_unit_before_B19_source_trace']=obj.get('next_unit');obj['next_unit']=i['next_artifact_diagnostic']
        if p['id'] in obj.get('parallel_artifact_diagnostics',{}):
            obj['parallel_artifact_diagnostics'][p['id']]=dict(entry,status='completed')
        warningmap={x['id']:x for x in obj['open_conditions']}
        for x in i['warnings']:assert x['id'] not in warningmap;warningmap[x['id']]=x
        obj['open_conditions']=list(warningmap.values())
        obj['integration_decisions']['B19_claim_source_trace']='Twelve selected2023 groups match original monetary fields/intervals and savedT0/reserve. Dominant motornew claim closed/fullypaid, not reserve-open or >365daylate. Keep claims/models; same-source snapshot does not establish reserve adequacy, ultimate or C0. No new fit/price/score.'
        obj.setdefault('condition_progress_without_auto_closure',{})['B19-SOURCE-TRACE']='Selected raw/cache source reconciliation complete with exact cents; single snapshot and ultimate/adequacy limitations retained. Existing warning not automatically closed.'
        obj['latest_kaggle_752144_check']={'utc':read(RUN/'incident_check.json')['checked_utc'],'semantic_content_unchanged':True,'source_archive_duplicated':False,'local_row_checks_repeated':False,'own_submission_attempt':False}
        return json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
    change(NIGHT,night)
    def routes(raw):
        for key,value in [('week_2_b19_source_trace_index',rel(INDEX)),('week_2_b19_source_trace_report',i['documentation']),('week_2_b19_source_trace_plan',i['plan'])]:raw=top(raw,key,value,True)
        return raw
    change(ROOT/'RUTAS_PROYECTO.json',routes)
    def state(raw):
        obj=json.loads(raw);current=read(NIGHT)
        dev=dict(i,as_of_utc=NOW,producer_checks=r['passed'],verification_checks=v['passed'],readout_checks=q['passed'],
                 source_findings=facts,confirmation_opened_by_this_task=False,external2024_artifacts_read_this_unit=False,
                 complete_blindness_claim_allowed=False,no_group_removed=True,verification_prior_implementation_failures_preserved=2)
        continuity=dict(obj['week_2_nocturnal_continuation_20261023'],as_of_utc=NOW,latest_artifact_diagnostic=rel(INDEX),next_artifact_diagnostic=i['next_artifact_diagnostic'])
        collab=dict(obj['collaboration_forum'],updated_utc=NOW,latest_Codex_comment='COD-S2-20261024-039')
        for key,value in [('memory_as_of',datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()),('week_2_nocturnal_continuation_20261023',continuity),('collaboration_forum',collab)]:raw=top(raw,key,value)
        if current.get('current_unit') is None:
            raw=top(raw,'current_phase',{'as_of_utc':NOW,'phase':'B19_selected2023_claim_sources_reconciled_no_retraining_own2024closed','current_state_key':STATEKEY,'historical_fields_notice':'Dated branches and concurrent active catalog retained; no own model/counter mutation.'})
        return top(raw,STATEKEY,dev,True)
    change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
    note=f'''

## B19: traza financiera de los componentes influyentes de 2023

Codex, corte UTC {NOW}. Siguiente unidad del índice nocturno, sin repetir B19, entrenamiento o remuestreo. Plan S2-B19-TRAZA2023-v1-20261024 y foro 038 a las 02:10:24 UTC preceden al cálculo; resultado 039 a las 02:19:19 UTC. Informe TRAZABILIDAD_SINIESTROS_B19_2023.md, índice semana2_b19_traza_actual.json y corrida traza_b19_20261024T021036Z_fe5038de en el repositorio común. Se conserva B00, todas las alternativas, T0/C0 y cada registro. Cero ajustes, modelos, predicciones, scores o bootstrap nuevos. Catálogo activo y contadores se preservan como corte, sin atribuir ajustes de otras continuaciones a esta unidad.

La unión preinscrita de cinco grupos OOF adversos de edificios y autos nuevos, más el de mayor influencia absoluta sobre cobertura de cada ajuste guardado, contiene doce componentes, veinte periodos y doce siniestros aceptados de 2023. Sus razones se solapan; no se suman como muestras independientes ni representan al portafolio. Se cotejaron los originales, filtrados por pólizas y fechas de 2023, y los campos guardados. Pagos, incurrido, recuperaciones, reserva derivada, fechas, estados, asignación única, grupo/fold y balances de cada periodo coinciden exactamente en centavos. Se conservan periodos de coste cero y otros ramos. No hay rechazados en esta selección, sin cambiar su exclusión general.

El siniestro principal de autos nuevos, lesiones corporales de 136.767,16 CU, está cerrado, totalmente pagado, sin reserva o recuperaciones. Pérdida del 1 de diciembre de 2023 y reporte del 28 de enero de 2024: 58 días. No se explica por reserva abierta o retraso superior a 365 días, ni cambia su T0 al multiplicar su reserva actual por 0,75/1,25. La incertidumbre de último, reapertura, recuperación futura y C0 sigue abierta; tampoco se pide que una prima esperada iguale el siniestro realizado. No se quita un coste válido por concentrar pérdida de evaluación.

Entre los cinco incendios OOF más adversos de edificios hay un abierto de 149.180,40 CU, con pagado 75.091,19 y reserva 74.089,21 CU. Los otros cuatro están cerrados y pagados. El incendio de 286.093 CU más influyente sobre AD en cuatro ajustes también está cerrado, sin reserva y reportado a los 14 días. El otro abierto seleccionado es una lesión corporal de autos de 18.915,80 CU, con 3.961,29 pagados y 14.954,51 de reserva. En los doce casos hay diez cerrados y dos abiertos, T0 1.616.032,86 CU y reserva 89.043,72 CU (5,51%). Ninguno tiene demora superior a 365 días; dos reportes son de 2024 por pérdidas de 2023. La selección no identifica la cola ausente ni resuelve la suficiencia de las reservas.

El diccionario archivado define incurrido como pagado más estimación de caso, y pagado ya neto de franquicia. Se conserva T0=pagado−recuperaciones+reserva, sin doble ajuste. El estrés mecánico 0,75/1,25 usa cuartos de centavo sin redondeo intermedio: solo en esta selección cambia el total en ±22.260,93 CU (±1,38%), sin adoptar objetivo o precio ni estimar adecuación. No se extrapola al portafolio, C0 o 2025.

Pasaron {r['passed']} controles del productor, {v['passed']} comprobaciones propias por Decimal/datetime/diccionarios y {q['passed']} conciliaciones de lectura, con solapamiento. Adversos de año, duplicado, identidad y fechas son rechazados; el comando real con reserva sintética alterada en un centavo falla antes de conciliación. Se archivan dos fallos anteriores del comprobador: fixture date frente a Timestamp y ruta relativa no resuelta. Se corrigió solo ese comprobador y pasó su tercera invocación; productor congelado, plan y fuentes intactos. No son fallos encontrados en los siniestros ni pases adicionales.

Es una concordancia dentro de un snapshot administrativo, no movimientos históricos, suficiencia, último o validación profesional independiente. La advertencia B19-SOURCE-TRACE recoge avance parcial y conserva límites, sin cierre automático. El próximo diagnóstico propuesto revisa contracción/nivel del GLM estándar regularizado B20 ya guardado frente a B19 sobre estos grupos fijados, solo 2023, con plan previo y sin ajustar. No hay justificación de una nueva receta por error de origen en esta selección; no se promueve, retira, congela lista final o añade complejidad por esta conciliación.

Kaggle MCP releyó la discusión 752144 a las 02:04:35 UTC: mismo contenido semántico, mensaje y tres respuestas, sin novedad del HOST. Solo se guarda recibo de consulta; no nueva copia de fuente, cotejo de test o envío. No se emite aviso dedicado por ausencia de cambio. 2024/test siguen cerrados en este trabajo, incluidos precios, predicciones, scores, SEL01, actas y ledger. Las fechas de reporte hasta valoración son historia de pérdidas 2023, no apertura de tarificación 2024. Exposición previa de un asunto externo declarada, sin uso de cifras ni afirmación de ceguera completa. Sin remoto, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. Continúa la ventana hasta las 07:00 Bogotá, con once unidades anteriores conservadas.
'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+note)
    update='\n\n## B19: siniestros influyentes conciliados\n\nLa [traza financiera](../Repositorio_IAA2026/docs/semana2/TRAZABILIDAD_SINIESTROS_B19_2023.md) coteja doce grupos y veinte periodos con los originales. El coste principal de autos nuevos está cerrado y totalmente pagado; no se corrige o borra. Hay dos casos abiertos con reserva, sin certificar suficiencia o último. Cero ajustes, predicciones, scores o bootstrap. Se conservan B00, todas las alternativas, T0/C0 y catálogo activo. Próximo diagnóstico propuesto: contracción/nivel del B20 estándar ya guardado frente a B19 sobre estos grupos fijados, con plan previo y sin reajustar. Foro 038/039; 2024 cerrado en este trabajo.\n'
    for name in ['README.md','PLAN_TRABAJO.md']:change(ROOT/'Hackaton/Semana 2'/name,lambda raw:raw+update)
    partial='\n\n## Traza de los siniestros influyentes de B19\n\nLa [conciliación focal](TRAZABILIDAD_SINIESTROS_B19_2023.md) revisa doce componentes, veinte periodos y doce siniestros aceptados con importes, fechas y asignación originales exactos. El coste principal de autos nuevos está cerrado y totalmente pagado; dos casos abiertos concentran la reserva de la selección. No se cambia T0/C0 o elimina un coste válido. Cero ajustes, nuevos precios, scores o bootstrap. El archivo es un único snapshot: suficiencia de reservas, último y cola no observada siguen pendientes. Se conserva el catálogo actual de otras continuaciones. Siguiente diagnóstico: contracción y nivel del B20 estándar guardado frente a B19 sobre grupos fijados, previa receta y sin reajustar. Kaggle 752144 sin cambios semánticos, sin fuente duplicada/cotejo/envío. Foro 038/039; 2024 cerrado. Balance parcial hasta las 07:00 Bogotá.\n'
    for name in ['PLAN_NOCTURNO_20261023.md','BALANCE_NOCTURNO_PARCIAL_20261024.md']:change(REPO/'docs/semana2'/name,lambda raw:raw+partial)
    change(REPO/'registro/semana2_listo_entrenar.json',lambda raw:top(raw,'latest_B19_claim_source_trace',{'utc':NOW,'index':rel(INDEX),'documentation':i['documentation'],'new_fits':0,'new_scores':0,'source_slice_reconciled':True,'reserve_adequacy_verified':False,'next_artifact_diagnostic':i['next_artifact_diagnostic'],'reference':'W2-B00','ledger_read':False,'confirmation_opened_by_this_task':False},True))
    tests=REPO/'registro/semana2_b19_traza2023_pruebas_v1.json'
    dump(tests,{'author':'Codex','utc':NOW,'producer':i['report'],'verification':i['verification'],'readout_reconciliation':i['readout_reconciliation'],'counts':[r['passed'],v['passed'],q['passed']],'counts_overlap':True,'expected_failure_runs':v['expected_failure_runs'],'checker_implementation_failure_receipts':[rel(RUN/'verification_first_attempt_failure.json'),rel(RUN/'verification_second_attempt_failure.json')],'new_fits':0,'new_scores':0,'professional_independent_validation':False})
    dump(RUN/'forum_receipts.json',{'receipts':[
        {'id':'COD-S2-20261024-038','utc':'2026-10-24T02:10:24+00:00','previous_sha256':'f63a863a804750ce36b697a94396fc699844d6587d1bd75760f3bf5e722de359','sha256_at_append':'7bcff5ae779a95e222efeda49006ea309866bda0ddaa665153a1dd7a9d79df39'},
        {'id':'COD-S2-20261024-039','utc':'2026-10-24T02:19:19+00:00','previous_sha256':'7bcff5ae779a95e222efeda49006ea309866bda0ddaa665153a1dd7a9d79df39','sha256_at_append':'f0cfc1d28a176dbc39dc5535b0f230755cb683aa5b56af5b187238eea301f62f'}]})
    dump(RUN/'registration.json',{'author':'Codex','utc':NOW,'changes':changes,'unrelated_indices_and_counters_cut':unchanged,'counter_values_cut':values,'own_counter_increment':0,'own_catalog_mutations':0,'concurrency':'Backups, compare-and-replace, preserve foreign current unit and all existing branches/routes. No other automation mutations.','ledger_read':False})
    checks=[]
    def check(name,ok):checks.append({'name':name,'pass':bool(ok)})
    for key in ['report','verification','readout','readout_reconciliation','assessment','decision_journal','manifest','incident_check']:check('Index receipt '+key,sha(ROOT/i[key]['path'])==i[key]['sha256'])
    check('Documentation exact',sha(ROOT/i['documentation'])==i['documentation_sha256'])
    for x in p['frozen_sources']:check('Frozen source '+x['path'],sha(ROOT/x['path'])==x['sha256'])
    for x in read(RUN/'manifest.json')['files']:check('Producer artifact '+x['path'],sha(ROOT/x['path'])==x['sha256'])
    check('No active catalog or counter write by this audit',not set(unchanged).intersection(x['path'] for x in changes))
    pointer_changes={path:{'before':before,'now':sha(ROOT/path)} for path,before in unchanged.items() if sha(ROOT/path)!=before}
    oldstate=read(BACK/'Preparación/ESTADO_PROYECTO.json');state=read(ROOT/'Preparación/ESTADO_PROYECTO.json')
    allowed={'current_phase','memory_as_of','week_2_nocturnal_continuation_20261023','collaboration_forum'}
    check('Historical state branches preserved',all(state.get(k)==val for k,val in oldstate.items() if k not in allowed))
    oldroutes=read(BACK/'RUTAS_PROYECTO.json');routes=read(ROOT/'RUTAS_PROYECTO.json')
    check('Earlier routes preserved',all(routes.get(k)==val for k,val in oldroutes.items()))
    for key in ['week_2_b19_source_trace_index','week_2_b19_source_trace_report','week_2_b19_source_trace_plan']:check('New route '+key,(ROOT/routes[key]).exists())
    for x in changes:
        if x['path'].endswith('.md'):check('Prose prefix '+x['path'],(ROOT/x['path']).read_bytes().startswith((ROOT/x['backup']).read_bytes()))
    for path in [ROOT/i['documentation'],REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',REPO/'docs/semana2/BALANCE_NOCTURNO_PARCIAL_20261024.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md']:
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8-sig')):
            target=link.strip('<>').split('#')[0]
            if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',target):continue
            check('Link '+rel(path)+' -> '+target,(path.parent/unquote(target)).resolve().exists())
    newnight=read(NIGHT);oldnight=read(BACK/NIGHT.relative_to(ROOT))
    check('Own unit completed once',sum(x['id']==p['id'] for x in newnight['completed_units'])==1)
    check('Earlier completed units preserved',newnight['completed_units'][:len(oldnight['completed_units'])]==oldnight['completed_units'])
    check('Only own current unit cleared',newnight['current_unit']==(None if (oldnight.get('current_unit') or {}).get('id')==p['id'] else oldnight['current_unit']))
    for key in ['window_start','window_end','frequency','automation_id','automation_kind','automation_target_thread','same_chat','other_automations_changed','forum_reading_guard','confirmation_header_exposure']:check('Schedule/guard preserved '+key,newnight[key]==oldnight[key])
    check('Existing warnings not closed',all(x in newnight['open_conditions'] for x in oldnight['open_conditions']))
    check('Own2024scope closed',newnight['confirmation_2024_open'] is False and state[STATEKEY]['ledger_read'] is False)
    check('Forum prefix preserved',forum.read_bytes().startswith(forum_cut))
    for path in v['expected_failure_runs']:check('Actual CLI expected failure archived',(ROOT/path/'expected_adversary_failure.json').exists())
    receipt={'utc':NOW,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'concurrent_pointer_changes':pointer_changes,'scope':'Closing integrity and preservation only; no new financial/statistical test or fit.'}
    dump(RUN/'closure_verification.json',receipt);assert receipt['failed']==0,[x for x in checks if not x['pass']]
    paths={x for x in RUN.rglob('*') if x.is_file()};paths.update(ROOT/x['path'] for x in changes)
    paths.update([INDEX,tests,ROOT/i['documentation'],ROOT/i['plan'],ROOT/p['code'],Path(__file__),forum])
    paths.update(REPO/'herramientas'/name for name in ['verificar_traza_b19_2023.py','documentar_traza_b19_2023.py'])
    paths.update(ROOT/'Hackaton/Semana 2/Codex'/name for name in ['preinscribir_traza_b19_2023.py','traza_b19_2023_preinscripcion.md','traza_b19_2023_resultado.md','nocturno_antes_traza_b19.json','catalogo_antes_traza_b19.json','contadores_antes_traza_b19.json'])
    for path in v['expected_failure_runs']:paths.update(x for x in (ROOT/path).rglob('*') if x.is_file())
    dump(RUN/'closure_manifest.json',{'utc':NOW,'notice':'Dated cut. Subsequent concurrent appends preserve this historical receipt.','files':[{'path':rel(x),'sha256':sha(x),'bytes':x.stat().st_size} for x in sorted(paths)],'new_fits':0,'new_scores':0,'new_bootstrap':0,'reference':'W2-B00'})
    print(json.dumps({'index':rel(INDEX),'closure_passed':receipt['passed'],'failed':receipt['failed'],'night_units':len(newnight['completed_units']),'own_new_fits':0,'counter_values_cut':values,'concurrent_pointer_changes':len(pointer_changes)},ensure_ascii=True))


if __name__=='__main__':main()
