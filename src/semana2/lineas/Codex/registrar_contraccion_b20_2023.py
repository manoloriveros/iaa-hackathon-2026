"""Registra la auditoría focal B20/B19 sin sustituir el trabajo concurrente."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import unquote
import hashlib,json,os,re
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/contraccion_b20_20261024T023428Z_7f3565db'
INDEX=REPO/'registro/semana2_b20_contraccion_actual.json';NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
STATEKEY='week_2_B20_contraction2023_v2_20261024';NOW=datetime.now(timezone.utc).isoformat();BACK=RUN/'state_before_registration';changes=[]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()


def dump(path,x):
    with path.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')


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
    tmp=path.with_name(path.name+'.contraccionb20cierre.tmp');assert path.read_bytes()==before,'Concurrent change '+rel(path)
    with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before,'Concurrent change before replace '+rel(path)
    os.replace(tmp,path);entry={'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path),'backup':rel(backup)};changes.append(entry)
    with (RUN/'registration_steps.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')


def main():
    p=read(RUN/'plan_snapshot.json');i=read(RUN/'index_proposed.json');r=read(RUN/'report.json');v=read(RUN/'verification.json');q=read(RUN/'readout_reconciliation.json');facts=read(RUN/'readout.json')
    assert r['failed']==v['failed']==q['failed']==0 and r['successful_fit_calls']==v['successful_fit_calls']==0
    assert r['new_bootstrap']==v['new_bootstrap']==0 and r['new_price_predictions']==0
    assert all(sha(ROOT/x['path'])==x['sha256'] for x in p['frozen_sources'])
    assert all(read(RUN/'focused_interpretation_receipt.json')['checks'].values())
    assert not INDEX.exists() and not BACK.exists()
    n=read(NIGHT);assert n['confirmation_2024_open'] is False and not any(x['id']==p['id'] for x in n['completed_units'])
    forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';forum_cut=forum.read_bytes()
    for suffix in ['040','041','042']:assert forum_cut.count(('<!-- aporte:COD-S2-20261024-'+suffix+' -->').encode())==1
    BACK.mkdir()
    untouched={rel(REPO/'registro'/name):sha(REPO/'registro'/name) for name in ['semana2_desarrollo2023_actual.json','semana2_glm_ridge_actual.json','semana2_contadores_propios_actual.json','semana2_b19_estabilidad_actual.json','semana2_b19_traza_actual.json','semana2_sensibilidad_observacion_actual.json']}
    counter=read(REPO/'registro/semana2_contadores_propios_actual.json');countercut={k:counter[k] for k in ['cumulative_price_base_fits','cumulative_closed_form_constants']}
    i.update(as_of_registration_utc=NOW,documentation_sha256=sha(ROOT/i['documentation']),forum_followup='COD-S2-20261024-042',
             focused_interpretation_receipt={'path':rel(RUN/'focused_interpretation_receipt.json'),'sha256':sha(RUN/'focused_interpretation_receipt.json')},
             preregistration_completion_receipt={'path':'Hackaton/Semana 2/Codex/contraccion_b20_v2_preparation_receipt.json','sha256':sha(ROOT/'Hackaton/Semana 2/Codex/contraccion_b20_v2_preparation_receipt.json')},
             unrelated_indices_and_counters_cut=untouched,counter_values_cut=countercut,this_unit_counter_increment=0,this_unit_active_catalog_mutations=0)
    dump(INDEX,i)
    def night(raw):
        obj=json.loads(raw);assert not any(x['id']==p['id'] for x in obj['completed_units'])
        current=obj.get('current_unit');ours=(current or {}).get('id')==p['id'];foreign=current is not None and not ours
        entry={key:i[key] for key in ['id','run','documentation','verification','decision_journal','forum_result','forum_followup']};entry.update(index=rel(INDEX),completed_utc=NOW,new_fits=0,new_price_predictions=0,new_bootstrap=0)
        obj['completed_units'].append(entry);obj.update(updated_utc=NOW,latest_completed_unit=entry,latest_B20_contraction_audit_index=rel(INDEX),latest_artifact_diagnostic=entry,next_artifact_diagnostic=i['next_artifact_diagnostic'],no_retraining_or_suite_repetition_for_completed_B20_contraction=True)
        if ours:obj['current_unit']=None
        if p['id'] in obj.get('parallel_artifact_diagnostics',{}):obj['parallel_artifact_diagnostics'][p['id']]=dict(entry,status='completed')
        if not foreign:
            obj['status']='scheduled_'+str(len(obj['completed_units']))+'_units_B20_contraction_verified_conditions_open';obj['next_unit_before_B20_contraction']=obj.get('next_unit');obj['next_unit']=i['next_artifact_diagnostic']
        warnings={x['id']:x for x in obj['open_conditions']}
        for x in i['warnings']:assert x['id'] not in warnings;warnings[x['id']]=x
        obj['open_conditions']=list(warnings.values())
        obj['integration_decisions']['B20_contraction_level']='All15 standardizednorms contract but33coordinate exceptions; AD building effect still crosses1, motornew business effect littlechanged. Fixed12group/20period level and deviance gains descriptive only. PreserveB00/all data/models, no normalization/alpha/routing/promotion.'
        obj.setdefault('condition_progress_without_auto_closure',{})['B20-coefficients']='Joint contraction and selected level mechanisms checked; samecoding dependence, adaptive fixedgroup selection and unstableAD remain open.'
        obj['latest_kaggle_752144_check']={'utc':read(RUN/'incident_check.json')['checked_utc'],'semantic_content_unchanged':True,'new_source_archive':False,'test_row_check_repeated':False,'submission_attempt':False}
        return json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
    change(NIGHT,night)
    def routes(raw):
        for key,value in [('week_2_b20_contraction_index',rel(INDEX)),('week_2_b20_contraction_report',i['documentation']),('week_2_b20_contraction_plan',i['plan'])]:raw=top(raw,key,value,True)
        return raw
    change(ROOT/'RUTAS_PROYECTO.json',routes)
    def state(raw):
        obj=json.loads(raw);current=read(NIGHT)
        dev=dict(i,as_of_utc=NOW,producer_checks=r['passed'],verification_checks=v['passed'],readout_checks=q['passed'],focused_interpretation_checks=4,
                 source_findings=facts,confirmation_opened_by_this_task=False,external2024_artifacts_read_this_unit=False,complete_blindness_claim_allowed=False,
                 own_fixed_row_replay_only=True,concurrent_plan_reconciled_before_calculation=True,concurrent_source_ready_at_preregistration=p['concurrent_source_ready_at_preregistration'])
        continuity=dict(obj['week_2_nocturnal_continuation_20261023'],as_of_utc=NOW,latest_artifact_diagnostic=rel(INDEX),next_artifact_diagnostic=i['next_artifact_diagnostic'])
        collab=dict(obj['collaboration_forum'],updated_utc=NOW,latest_Codex_comment='COD-S2-20261024-042')
        for key,value in [('memory_as_of',datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()),('week_2_nocturnal_continuation_20261023',continuity),('collaboration_forum',collab)]:raw=top(raw,key,value)
        if current.get('current_unit') is None:raw=top(raw,'current_phase',{'utc':NOW,'phase':'B20_saved_coefficients_and_level_checked_no_refit_own2024closed','current_state_key':STATEKEY,'historical_fields_notice':'Previous dated branches preserved; concurrent attribution and active model catalog not replaced.'})
        return top(raw,STATEKEY,dev,True)
    change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
    note=f'''

## B20 frente a B19: contracción y nivel sobre los grupos fijados

Codex, corte UTC {NOW}. Instrucción directa del participante: revisar contracción y nivel de B20 frente a B19 en los mismos grupos con artefactos de 2023, sin reentrenar, conservar B00 y publicar resultados. Diagnóstico v2 S2-B20-CONTRACCION2023-v2-20261024, comentario 040 a las 02:34:23 UTC antes de calcular; resultados 041 a las 02:36:14 y complemento 042 a las 02:37:09. Informe CONTRACCION_Y_NIVEL_B20_VS_B19_2023.md e índice semana2_b20_contraccion_actual.json. Cero ajustes, nuevos modelos, recetas de precio o bootstrap; solo replay focal de veinte predicciones OOF existentes por modelo, sin precios con coeficientes alterados. B00, todas las alternativas, T0/C0 y registros se conservan.

El alcance se concilió con la unidad concurrente S2-B20-ATRIBUCION2023-v1-20261024. El borrador v1 propio se conserva sin comentario previo o cálculos. Al registrar v2 aún no estaban materializados el reporte y los términos concurrentes, y se fijó el modo focal de veinte filas, no la matriz de 50.094 o su retirada de 31 grupos. La disponibilidad se decidió antes del cálculo, sin mirar resultados. Una colisión con el archivo del cuerpo v1 detuvo la preparación después de guardar el plan v2; se conservó el cuerpo y completó otro separado con plan/fuentes intactos. La entrada v1 queda sustituida y la v2 terminada sin sobrescribir la unidad ajena activa. No se usan órdenes de otros documentos o chats; su plan es evidencia del solapamiento.

Los quince pares comparten siete efectos, medianas, medias/escalas y categorías/referencias entrenadas; solo alpha pasa de 0 a 1. La norma L2 conjunta del diseño estandarizado disminuye en 15/15, entre 28,7% y 61,4%, pero hay 33 coordenadas cuyo valor absoluto crece en catorce pares. AD de edificios apenas cambia su inestabilidad: B19 0,795–1,388 frente a B20 0,801–1,375, ambos cruzan 1. En autos third_party_only/comprehensive pasa de 0,567–0,857 a 0,759–1,005; third_party_fire_theft de 0,587–0,611 a 0,758–0,778. El efecto de nuevo negocio de autos cambia poco, 1,978–2,481 frente a 1,972–2,462. Los cinco ajustes solapan, sin CI independiente o estabilización uniforme acreditada. La norma usa unidades estandarizadas y referencias comunes; la penalización one-hot depende de la codificación.

Se preservan exactamente los doce componentes y veinte periodos de la traza. El total observado B20/B19 es 0,983588 en la unión y 0,979884 globalmente; en los cinco edificios adversos fijados es 0,945901 y en los cinco autos nuevos 1,121008. Los nominales condicionales de 2023 se guardan separados, sin extrapolar a 2025 o adoptar normalización. Un intercepto no equivale a calibración agregada. La lesión corporal principal de autos pasa de 90,25 a 95,07 CU esperadas, razón 1,053425; su siniestro realizado de 136.767,16 CU no se equipara a prima esperada. El cambio log concilia como intercepto −0,423120, cobertura +0,291127, nuevo negocio −0,002903 y otros +0,186943, total +0,052047.

Los veinte periodos aportan 14.620,81 unidades de mejora de desviación ya guardada, 38,2% de la ganancia global neta de 38.299,18. El resto aporta 23.678,36 unidades positivas netas. Son fracciones netas con compensaciones, no probabilidad, mejora bruta o muestra representativa; los grupos fueron seleccionados por errores/influencia previos de B19. El incendio antes fijado como primer adverso B19 aporta 13.724,81 unidades, 93,9% de la ganancia neta seleccionada. El de 286.093 CU empeora −557,25. Tienen el mismo cambio log de cobertura +0,004636 y distintos términos de otros efectos, +0,124759 y −0,267250, con tasas que suben y bajan respectivamente. No se atribuye la ganancia a cobertura sola ni se elimina un coste válido.

Pasaron {r['passed']} controles del productor, {v['passed']} cotejos focales por fsum/diccionarios/predictor manual, {q['passed']} conciliaciones de lectura y cuatro identidades contables del complemento, con solapamiento. Se reconstruyen tasas desde betas en escala original y medianas guardadas, además del replay nativo, sin repetir suites 542/48 o bootstrap. El comando real con C0 sintético alterado falla antes de abrir modelos; se conservan adversos de año, claves, T0, C0, transformación y fit bloqueado. No hay promoción, retirada, lista final, otro alpha, enrutamiento o mayor complejidad por esta revisión propia; no es profesional independiente o aprobación humana.

El próximo paso es conciliar los recibos de la atribución concurrente cuando termine y consolidar evidencia ya existente de ramos/negocio y advertencias, sin repetir los diagnósticos o entrenar. Catálogo activo, contador y trabajo ajeno preservados. Kaggle 752144 se releyó a las 02:25:10 UTC sin cambios semánticos; solo recibo de consulta, sin nueva fuente/cotejo de test/envío. 2024/test siguen cerrados en este trabajo, incluidos precios, predicciones, scores, actas, SEL01 y ledger. Exposición anterior de un asunto externo declarada, sin uso de cifras o ceguera completa. Sin remoto, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. Ventana hasta las 07:00 Bogotá intacta.
'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+note)
    update='\n\n## B20/B19: contracción y nivel en los mismos grupos\n\nLa [comparación de artefactos](../Repositorio_IAA2026/docs/semana2/CONTRACCION_Y_NIVEL_B20_VS_B19_2023.md) conserva doce grupos y veinte periodos. Contraen las quince normas conjuntas, pero crecen 33 coordenadas y AD de edificios sigue cambiando dirección. El nivel de los grupos se mueve de forma distinta por ramo; no se adopta normalización. Cero ajustes o nuevos precios, B00 y todas las alternativas conservados. Se concilió el alcance concurrente y se cotejó solo el diseño focal, sin repetir su atribución global/31grupos. Foro 040/041/042. 2024 cerrado; siguiente paso, conciliar recibos cuando termine la atribución y consolidar advertencias ya existentes.\n'
    for name in ['README.md','PLAN_TRABAJO.md']:change(ROOT/'Hackaton/Semana 2'/name,lambda raw:raw+update)
    partial='\n\n## B20/B19: coeficientes y nivel verificados sin ajustar\n\nLa [revisión focal](CONTRACCION_Y_NIVEL_B20_VS_B19_2023.md) compara quince pares de GLM guardados y los doce grupos previos. Contraen las normas conjuntas, con 33 coordenadas que crecen; AD de edificios continúa inestable. El nivel global baja 2,01% y la unión fija 1,64%, mientras el subconjunto de cinco autos nuevos sube 12,10%. El total o el intercepto no explican solos las diferencias por caso. Los grupos aportan 38,2% de la ganancia global neta existente, sin nueva validación o promoción. Se conservan B00, todas las alternativas y datos. Cero ajustes/nuevos precios/bootstrap; alcance concurrente conciliado, cotejo propio limitado a veinte filas. Foro 040/041/042. Conciliar los recibos concurrentes al terminar y consolidar advertencias, sin repetir suites. 2024 cerrado y ventana hasta las 07:00 Bogotá intacta; balance parcial.\n'
    for name in ['PLAN_NOCTURNO_20261023.md','BALANCE_NOCTURNO_PARCIAL_20261024.md']:change(REPO/'docs/semana2'/name,lambda raw:raw+partial)
    change(REPO/'registro/semana2_listo_entrenar.json',lambda raw:top(raw,'latest_B20_saved_coefficient_level_diagnostic',{'utc':NOW,'index':rel(INDEX),'documentation':i['documentation'],'new_fits':0,'new_price_predictions':0,'new_bootstrap':0,'next_artifact_diagnostic':i['next_artifact_diagnostic'],'reference':'W2-B00','ledger_read':False,'confirmation_opened_by_this_task':False},True))
    tests=REPO/'registro/semana2_b20_contraccion2023_pruebas_v2.json'
    dump(tests,{'author':'Codex','utc':NOW,'producer':i['report'],'verification':i['verification'],'readout_reconciliation':i['readout_reconciliation'],'interpretation':i['focused_interpretation_receipt'],'counts':[r['passed'],v['passed'],q['passed'],4],'counts_overlap':True,'expected_failure_runs':v['expected_failure_runs'],'successful_fit_calls':0,'new_bootstrap':0,'prior542_48_and_concurrent_full_suite_not_repeated':True,'professional_independent_validation':False})
    dump(RUN/'forum_receipts.json',{'receipts':[
        {'id':'COD-S2-20261024-040','utc':'2026-10-24T02:34:23+00:00','previous_sha256':'0e64ac22b5e0189a285b265ad7c44ebc9267e7835b4ba10e38b8413c3f317383','sha256_at_append':'07c29c8b7a62da91346f9265077812b8d016af5b21a6474e4a9968ce834ed0a3'},
        {'id':'COD-S2-20261024-041','utc':'2026-10-24T02:36:14+00:00','previous_sha256':'781e36ca7787d55b3a603631cac51689ef67b6e86c422221c92197817d508024','sha256_at_append':'d5289473c3ea891e600cefc1cbb8a21cee228e9a0468493d380374df09f48403'},
        {'id':'COD-S2-20261024-042','utc':'2026-10-24T02:37:09+00:00','previous_sha256':'d5289473c3ea891e600cefc1cbb8a21cee228e9a0468493d380374df09f48403','sha256_at_append':'49c95743022861ca708f05815990304d42a4178a8b0edfc57178bb8e704ee668'}]})
    dump(RUN/'registration.json',{'author':'Codex','utc':NOW,'changes':changes,'unrelated_indices_and_counters_cut':untouched,'counter_values_cut':countercut,'own_counter_increment':0,'own_active_catalog_mutations':0,'concurrency':'Exact backups and compare/replace; preserve foreign current unit, previous branches/routes/completed units. Own parallel v2 completed, v1 superseded before calculation.','ledger_read':False})
    checks=[]
    def check(name,ok):checks.append({'name':name,'pass':bool(ok)})
    for key in ['report','verification','readout','readout_reconciliation','assessment','decision_journal','manifest','incident_check','focused_interpretation_receipt','preregistration_completion_receipt']:check('Index receipt '+key,sha(ROOT/i[key]['path'])==i[key]['sha256'])
    check('Documentation exact',sha(ROOT/i['documentation'])==i['documentation_sha256'])
    for x in p['frozen_sources']:check('Frozen source '+x['path'],sha(ROOT/x['path'])==x['sha256'])
    for x in read(RUN/'manifest.json')['files']:check('Producer artifact '+x['path'],sha(ROOT/x['path'])==x['sha256'])
    check('No active catalog/counter written',not set(untouched).intersection(x['path'] for x in changes))
    pointerchanges={path:{'before':before,'now':sha(ROOT/path)} for path,before in untouched.items() if sha(ROOT/path)!=before}
    oldstate=read(BACK/'Preparación/ESTADO_PROYECTO.json');state=read(ROOT/'Preparación/ESTADO_PROYECTO.json');allowed={'current_phase','memory_as_of','week_2_nocturnal_continuation_20261023','collaboration_forum'}
    check('Old state branches preserved',all(state.get(k)==val for k,val in oldstate.items() if k not in allowed))
    oldroutes=read(BACK/'RUTAS_PROYECTO.json');routes=read(ROOT/'RUTAS_PROYECTO.json');check('Earlier routes preserved',all(routes.get(k)==val for k,val in oldroutes.items()))
    for key in ['week_2_b20_contraction_index','week_2_b20_contraction_report','week_2_b20_contraction_plan']:check('New route '+key,(ROOT/routes[key]).exists())
    for x in changes:
        if x['path'].endswith('.md'):check('Prose prefix '+x['path'],(ROOT/x['path']).read_bytes().startswith((ROOT/x['backup']).read_bytes()))
    for path in [ROOT/i['documentation'],REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',REPO/'docs/semana2/BALANCE_NOCTURNO_PARCIAL_20261024.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md']:
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8-sig')):
            target=link.strip('<>').split('#')[0]
            if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',target):continue
            check('Link '+rel(path)+' -> '+target,(path.parent/unquote(target)).resolve().exists())
    newn=read(NIGHT);oldn=read(BACK/NIGHT.relative_to(ROOT))
    check('Own unit complete exactly once',sum(x['id']==p['id'] for x in newn['completed_units'])==1)
    check('Previous completed units preserved',newn['completed_units'][:len(oldn['completed_units'])]==oldn['completed_units'])
    check('Foreign current unit preserved',newn['current_unit']==(None if (oldn.get('current_unit') or {}).get('id')==p['id'] else oldn['current_unit']))
    if p['id'] in oldn.get('parallel_artifact_diagnostics',{}):
        check('Own parallel entry completed',newn['parallel_artifact_diagnostics'][p['id']]['status']=='completed')
    else:
        check('Own actual current-unit mode completed',(oldn.get('current_unit') or {}).get('id')==p['id'] and newn['current_unit'] is None)
    check('Draftv1 not treated as performed',newn['parallel_artifact_diagnostics']['S2-B20-CONTRACCION2023-v1-20261024']['status']=='superseded_before_forum_or_calculation')
    for key in ['window_start','window_end','frequency','automation_id','automation_kind','automation_target_thread','same_chat','other_automations_changed','forum_reading_guard','confirmation_header_exposure']:check('Schedule/guard preserved '+key,newn[key]==oldn[key])
    check('Old warnings retained',all(x in newn['open_conditions'] for x in oldn['open_conditions']))
    check('Own2024closed',newn['confirmation_2024_open'] is False and state[STATEKEY]['ledger_read'] is False)
    check('Forum prefix preserved',forum.read_bytes().startswith(forum_cut))
    check('Focal appendix prefix retained',(ROOT/i['documentation']).read_bytes().startswith((RUN/'documentation_before_focused_interpretation.md').read_bytes()))
    for path in v['expected_failure_runs']:check('Expected actual-flow failure archived',(ROOT/path/'expected_adversary_failure.json').exists())
    receipt={'utc':NOW,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'concurrent_pointer_changes':pointerchanges,'scope':'Closing hashes/links and concurrency only, no statistical suite or model work.'}
    dump(RUN/'closure_verification.json',receipt);assert receipt['failed']==0,[x for x in checks if not x['pass']]
    paths={x for x in RUN.rglob('*') if x.is_file()};paths.update(ROOT/x['path'] for x in changes);paths.update([INDEX,tests,ROOT/i['documentation'],ROOT/i['plan'],ROOT/p['code'],Path(__file__),forum])
    paths.update(REPO/'herramientas'/name for name in ['verificar_contraccion_b20_2023.py','documentar_contraccion_b20_2023.py'])
    paths.update(ROOT/'Hackaton/Semana 2/Codex'/name for name in ['preinscribir_contraccion_b20_2023.py','preinscribir_contraccion_b20_2023_v2.py','completar_preinscripcion_contraccion_b20_v2.py','contraccion_b20_2023_preinscripcion.md','contraccion_b20_2023_v2_preinscripcion.md','contraccion_b20_2023_resultado.md','contraccion_b20_2023_complemento.md','contraccion_b20_v2_preparation_receipt.json','nocturno_antes_contraccion_b20.json','nocturno_antes_contraccion_b20_v2.json','catalogo_antes_contraccion_b20.json','catalogo_antes_contraccion_b20_v2.json','contadores_antes_contraccion_b20.json','contadores_antes_contraccion_b20_v2.json'])
    paths.add(REPO/'registro/semana2_b20_contraccion2023_plan_v1.json');paths.add(REPO/'src/semana2/diagnosticar_contraccion_b20_2023.py')
    for path in v['expected_failure_runs']:paths.update(x for x in (ROOT/path).rglob('*') if x.is_file())
    dump(RUN/'closure_manifest.json',{'utc':NOW,'notice':'Dated cut; legitimate later concurrent appends do not rewrite this receipt.','files':[{'path':rel(x),'sha256':sha(x),'bytes':x.stat().st_size} for x in sorted(paths)],'successful_fit_calls':0,'new_bootstrap':0,'reference':'W2-B00'})
    print(json.dumps({'index':rel(INDEX),'closing_passed':receipt['passed'],'failed':receipt['failed'],'completed_units_at_cut':len(newn['completed_units']),'foreign_current_unit_preserved':(newn.get('current_unit') or {}).get('id'),'new_fits':0,'counter_values_cut':countercut},ensure_ascii=True))


if __name__=='__main__':main()
