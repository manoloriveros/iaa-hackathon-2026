"""Registro con cortes antes/después; los cambios compartidos posteriores no son fuentes."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import unquote
import hashlib,json,os,re
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/incendio_AD_b20_20261024T025027Z_87782526'
INDEX=REPO/'registro/semana2_b20_incendio_AD_actual.json';NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
STATEKEY='week_2_B20_fixed_fire_AD2023_v1_20261024';NOW=datetime.now(timezone.utc).isoformat();BEFORE=RUN/'state_before_registration';AFTER=RUN/'state_after_registration';changes=[]
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
    before=path.read_bytes();b=BEFORE/path.relative_to(ROOT);a=AFTER/path.relative_to(ROOT);b.parent.mkdir(parents=True,exist_ok=True);a.parent.mkdir(parents=True,exist_ok=True)
    with b.open('xb') as f:f.write(before)
    after=fn(before.decode('utf-8-sig')).encode('utf-8')
    if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
    temp=path.with_name(path.name+'.incendioADregistro.tmp');assert path.read_bytes()==before,'Concurrent change '+rel(path)
    with temp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before,'Concurrent change before replace '+rel(path);os.replace(temp,path)
    with a.open('xb') as f:f.write(after)
    item={'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest(),'before_cut':rel(b),'after_cut':rel(a)};changes.append(item)
    with (RUN/'registration_steps.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(item,ensure_ascii=False)+'\n')


def main():
    p=read(RUN/'plan_snapshot.json');i=read(RUN/'index_proposed.json');r=read(RUN/'report.json');v=read(RUN/'verification.json');q=read(RUN/'readout_reconciliation.json');facts=read(RUN/'readout.json')
    assert r['failed']==v['failed']==q['failed']==0 and all(obj[k]==0 for obj in [r,v] for k in ['successful_fit_calls','model_loads','new_price_predictions','new_bootstrap'])
    assert not INDEX.exists() and not BEFORE.exists() and not AFTER.exists();assert all(sha(ROOT/x['path'])==x['sha256'] for x in p['frozen_sources'])
    n=read(NIGHT);assert n['confirmation_2024_open'] is False and not any(x['id']==p['id'] for x in n['completed_units'])
    BEFORE.mkdir();AFTER.mkdir()
    untouched={rel(REPO/'registro'/name):sha(REPO/'registro'/name) for name in ['semana2_desarrollo2023_actual.json','semana2_glm_ridge_actual.json','semana2_b20_contraccion_actual.json','semana2_b20_atribucion_actual.json','semana2_contadores_propios_actual.json']}
    counter=read(REPO/'registro/semana2_contadores_propios_actual.json');values={k:counter[k] for k in ['cumulative_price_base_fits','cumulative_closed_form_constants']}
    i.update(as_of_registration_utc=NOW,documentation_sha256=sha(ROOT/i['documentation']),unrelated_indices_and_counters_cut=untouched,counter_values_cut=values,this_unit_counter_increment=0,this_unit_active_catalog_mutations=0)
    dump(INDEX,i)
    def night(raw):
        obj=json.loads(raw);assert not any(x['id']==p['id'] for x in obj['completed_units']);current=obj.get('current_unit');ours=(current or {}).get('id')==p['id'];foreign=current is not None and not ours
        entry={k:i[k] for k in ['id','run','documentation','verification','decision_journal','forum_result']};entry.update(index=rel(INDEX),completed_utc=NOW,new_fits=0,model_loads=0,new_price_predictions=0,new_bootstrap=0)
        obj['completed_units'].append(entry);obj.update(updated_utc=NOW,latest_completed_unit=entry,latest_B20_fixed_fire_AD_index=rel(INDEX),latest_artifact_diagnostic=entry,next_artifact_diagnostic=i['next_artifact_diagnostic'],no_retraining_or_suite_repetition_for_completed_fixedfire_AD=True)
        obj.setdefault('completed_artifact_diagnostics',{})[p['id']]=entry
        if ours:obj['current_unit']=None
        if p['id'] in obj.get('parallel_artifact_diagnostics',{}):obj['parallel_artifact_diagnostics'][p['id']]=dict(entry,status='completed')
        if not foreign:
            obj['status']='scheduled_'+str(len(obj['completed_units']))+'_units_fixedfire_AD_checked_conditions_open';obj['next_unit_before_fixedfire_AD']=obj.get('next_unit');obj['next_unit']=i['next_artifact_diagnostic']
        warnings={x['id']:x for x in obj['open_conditions']}
        for x in i['warnings']:assert x['id'] not in warnings;warnings[x['id']]=x
        obj['open_conditions']=list(warnings.values());obj['integration_decisions']['fixedfire_AD']='Fixedfire35.8%globalnet and7.2%globalpositivegrosscomponent gain; singlecase exclusion leavespositivepoint. ADfit3 excludes bothfixedfires; composition descriptive and oldB19localinfluence approximate. Keepallrecords/B00/alternatives, no mask or promotion.'
        obj.setdefault('condition_progress_without_auto_closure',{})['B20-FIXED-GROUPS']='Denominators and onefixedfire sensitivity reviewed, not closure of prior31group or adaptive uncertainty warnings.'
        obj['latest_kaggle_752144_check']={'utc':read(RUN/'incident_check.json')['checked_utc'],'semantic_content_unchanged':True,'source_archive_duplicated':False,'test_row_check_repeated':False,'submission_attempt':False}
        return json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
    change(NIGHT,night)
    def routes(raw):
        for key,value in [('week_2_b20_fixed_fire_AD_index',rel(INDEX)),('week_2_b20_fixed_fire_AD_report',i['documentation']),('week_2_b20_fixed_fire_AD_plan',i['plan'])]:raw=top(raw,key,value,True)
        return raw
    change(ROOT/'RUTAS_PROYECTO.json',routes)
    def state(raw):
        obj=json.loads(raw);dev=dict(i,as_of_utc=NOW,producer_checks=r['passed'],verification_checks=v['passed'],readout_checks=q['passed'],findings=facts,confirmation_opened_by_this_task=False,external2024_artifacts_read_this_unit=False,prior_external2024_subject_exposure_disclosed=True)
        continuity=dict(obj['week_2_nocturnal_continuation_20261023'],as_of_utc=NOW,latest_artifact_diagnostic=rel(INDEX),next_artifact_diagnostic=i['next_artifact_diagnostic'])
        raw=top(raw,'week_2_nocturnal_continuation_20261023',continuity);raw=top(raw,'memory_as_of',datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat())
        if read(NIGHT).get('current_unit') is None:raw=top(raw,'current_phase',{'utc':NOW,'phase':'fixedfire_concentration_and_AD_composition_verified_without_models_own2024closed','current_state_key':STATEKEY,'historical_fields_notice':'Prior dated branches, concurrent work and active price catalog retained.'})
        return top(raw,STATEKEY,dev,True)
    change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
    note=f'''

## B20: concentración del incendio fijado e inestabilidad de AD

Codex, corte UTC {NOW}. Instrucción directa del participante: revisar concentración de la mejora de B20 en el incendio destacado y AD en edificios, solo con artefactos de 2023, sin reentrenar, conservar B00, publicar decisiones y mantener 2024 cerrado. Plan S2-B20-INCENDIO-AD2023-v1-20261024; comentario 043 a las 02:50:18 UTC antes de calcular y resultado 044 a las 02:54:25 UTC. Informe INCENDIO_Y_AD_B20_2023.md e índice semana2_b20_incendio_AD_actual.json. Cero ajustes, cargas de modelos, predicciones, recetas o bootstrap nuevos. B00, todas las alternativas, T0/C0 y cada siniestro se conservan. El alcance es distinto de las bandas de calibración y no repite sus replays, bandas o verificación.

Se mantuvo el incendio elegido por el primer grupo adverso de B19 en edificios; no se reseleccionó con B20. Su fila y componente completo coinciden: un periodo con 261.192,30 CU de T0 y 13.724,81 unidades de ganancia de desviación guardada. Ese importe es 93,9% de la ganancia neta de los doce grupos previos, 71,8% de su mejora bruta positiva por componente, 35,8% de la ganancia global neta y 7,2% de las mejoras brutas positivas globales por componente, o 6,6% por fila. Los denominadores no se intercambian. El global reúne 190.363,86 unidades positivas por componente y 152.064,68 adversas, neto 38.299,18, con 12.955 componentes positivos y 17.914 negativos. La fracción neta refleja compensaciones, sin probabilidad o muestra representativa implícita.

Al omitir solo de evaluación la fila o su componente, permanecen 24.574,37 unidades positivas netas y ΔD² B20−B19 +0,004480, frente a +0,006912 completo. El nulo común se recalcula en el subconjunto. No se borra el registro o cambia un precio; un D² para la sola fila se deja indefinido porque su nulo es cero. La advertencia anterior de sensibilidad a 31 grupos y búsqueda adaptativa sigue abierta: no se repitió ni se cura por mantener positivo el punto sin un caso. El incendio sigue siendo válido, cerrado, pagado y asignado según la traza anterior; una realización no se equipara a prima esperada.

AD es negativo solo en el fold 3 de B19/B20. Los incendios de 261.192,30 y 286.093 CU tienen AD activado, suman 547.285,30 CU y están fuera de ese ajuste; no pueden influir directamente en el modelo que produce su propia predicción OOF. En las otras cuatro vistas aportan entre 40,8% y 52,5% del coste de incendio de AD activado. El ajuste 3 tiene once incendios con AD y 581.039,46 CU, frente a 1,04–1,34 millones en las otras vistas; también omite muchos otros componentes. La composición es compatible con sensibilidad a pocos siniestros grandes, sin identificar una causa exclusiva o suficiente. El objetivo contiene todos los perils; AD no se convierte en máscara de T0 o exposición.

Las tablas conservan filas, positivos, exposición nominal/C0 y coste por peril, negocio, bandera y ajuste/retención, con ceros y celdas de ausentes explícitos. Cada fila aparece en cuatro ajustes y una retención, no cinco muestras independientes. Se reutilizan ocho influencias locales ya calculadas de B19: retiro aproximado del primer caso cambia su logcoeficiente AD entre −0,0699 y −0,0539, y del segundo entre −0,1557 y −0,0996 en las vistas donde participan. No son influencia de B20, reajustes exactos, betas conjuntas tras borrado o precios alterados; leverage alto limita la aproximación. No nuevos Hessianos o modelos.

Pasaron {r['passed']} controles del productor, {v['passed']} verificaciones propias por fsum/diccionarios/Decimal y desviación general de sklearn para las dos exclusiones fijadas, y {q['passed']} conciliaciones de lectura, con solapamiento. El flujo real rechaza año sintético ajeno a 2023 antes de las tablas. Se preservan ese fallo esperado y los adversos de claves, coste, AD no binario y denominador neto cero. No se repiten suites completas anteriores o remuestreo. Son revisiones propias de investigación adaptativa, no profesionales independientes o aprobación humana.

Decisión: no quitar un incendio caro, promover/retirar modelos, normalizar B20, cambiar alpha, máscara o lista final. Consolidar una matriz de riesgos y decisiones por ramo/negocio con los recibos existentes, incluidas bandas, atribución, contracción y este diagnóstico, antes de más complejidad. Catálogo y contador activos quedan fuera de las escrituras propias; se preservan concurrencia y autoría. Los cortes privados antes/después separan nuestras modificaciones de cambios posteriores legítimos en el foro o índices compartidos, sin confundirlos con fuentes alteradas.

Kaggle 752144 se releyó a las 02:47:05 UTC sin cambios semánticos: solo recibo de consulta, sin nueva fuente, cotejo de test o envío. 2024/test/SEL01/actas/precios/predicciones/scores/ledger siguen cerrados en este trabajo. Exposición previa de asunto externo declarada, sin usar cifras o afirmar ceguera completa. Sin remoto, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. Ventana hasta las 07:00 Bogotá intacta y balance parcial.
'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+note)
    brief='\n\n## Incendio fijado y AD de edificios\n\nLa [revisión focal](../Repositorio_IAA2026/docs/semana2/INCENDIO_Y_AD_B20_2023.md) distingue 93,9% de ganancia neta seleccionada, 35,8% global neta y 7,2% global bruta positiva por componente. Sin ese único caso en evaluación, el punto global sigue positivo (+0,004480), sin cerrar la advertencia por 31 grupos. Los dos incendios fijados están fuera del ajuste 3, donde AD es negativo; la composición orienta, sin causa exclusiva acreditada. No se eliminan registros, usan máscaras o promueven modelos. B00 y alternativas conservados, cero modelos/predicciones nuevos; 2024 cerrado. Foro 043/044. Siguiente paso: consolidar recibos existentes en matriz por ramo/negocio, sin repetirlos.\n'
    for name in ['README.md','PLAN_TRABAJO.md']:change(ROOT/'Hackaton/Semana 2'/name,lambda raw:raw+brief)
    brief2='\n\n## Concentración del incendio y composición de AD revisadas\n\nLa [revisión](INCENDIO_Y_AD_B20_2023.md) conserva el caso elegido antes de mirar B20 y distingue denominadores: 35,8% de ganancia global neta y 7,2% de mejora bruta positiva por componente. Su exclusión solo de evaluación deja ΔD² +0,004480; no cura la sensibilidad previa a 31 grupos. Ambos incendios están fuera del ajuste 3 con AD negativo; las demás diferencias del fold impiden causa única. No cambios de datos/modelos, B00 y alternativas conservados, cero cargas de modelos, entrenamiento o predicciones. Foro 043/044. Consolidar matriz de riesgos con recibos existentes, incluidos los de bandas, sin repetir suites. 2024 cerrado, ventana hasta las 07:00 Bogotá y balance aún parcial.\n'
    for name in ['PLAN_NOCTURNO_20261023.md','BALANCE_NOCTURNO_PARCIAL_20261024.md']:change(REPO/'docs/semana2'/name,lambda raw:raw+brief2)
    change(REPO/'registro/semana2_listo_entrenar.json',lambda raw:top(raw,'latest_fixedfire_AD_diagnostic',{'utc':NOW,'index':rel(INDEX),'documentation':i['documentation'],'new_fits':0,'model_loads':0,'new_price_predictions':0,'next_artifact_diagnostic':i['next_artifact_diagnostic'],'reference':'W2-B00','ledger_read':False,'confirmation_opened_by_this_task':False},True))
    tests=REPO/'registro/semana2_b20_incendio_AD2023_pruebas_v1.json'
    dump(tests,{'author':'Codex','utc':NOW,'producer':i['report'],'verification':i['verification'],'readout_reconciliation':i['readout_reconciliation'],'counts':[r['passed'],v['passed'],q['passed']],'counts_overlap':True,'expected_failure_runs':v['expected_failure_runs'],'no_previous_full_suites_or_resampling_repeated':True,'professional_independent_validation':False})
    dump(RUN/'registration.json',{'author':'Codex','utc':NOW,'changes':changes,'unrelated_indices_and_counters_cut':untouched,'counter_values_cut':values,'own_counter_increment':0,'own_model_index_mutations':0,'actual_before_current_unit':read(BEFORE/NIGHT.relative_to(ROOT)).get('current_unit'),'actual_after_current_unit':read(AFTER/NIGHT.relative_to(ROOT)).get('current_unit'),'successful_fit_calls':0})
    checks=[]
    def check(name,ok):checks.append({'name':name,'pass':bool(ok)})
    for name in ['report','verification','readout','readout_reconciliation','assessment','decision_journal','manifest','incident_check']:check('Index receipt '+name,sha(ROOT/i[name]['path'])==i[name]['sha256'])
    check('Documentation exact',sha(ROOT/i['documentation'])==i['documentation_sha256'])
    for x in p['frozen_sources']:check('Frozen source '+x['path'],sha(ROOT/x['path'])==x['sha256'])
    for x in read(RUN/'manifest.json')['files']:check('Producer artifact '+x['path'],sha(ROOT/x['path'])==x['sha256'])
    for x in changes:
        check('Before/after cuts exact '+x['path'],sha(ROOT/x['before_cut'])==x['before_sha256'] and sha(ROOT/x['after_cut'])==x['after_sha256'])
        if x['path'].endswith('.md'):check('Own prose append prefix '+x['path'],(ROOT/x['after_cut']).read_bytes().startswith((ROOT/x['before_cut']).read_bytes()))
    check('No model index/counter writes',not set(untouched).intersection(x['path'] for x in changes))
    oldstate=read(BEFORE/'Preparación/ESTADO_PROYECTO.json');state=read(AFTER/'Preparación/ESTADO_PROYECTO.json');allowed={'current_phase','memory_as_of','week_2_nocturnal_continuation_20261023'}
    check('Other state branches unchanged in own cut',all(state.get(k)==value for k,value in oldstate.items() if k not in allowed))
    routes=read(AFTER/'RUTAS_PROYECTO.json');oldroutes=read(BEFORE/'RUTAS_PROYECTO.json');check('Earlier routes unchanged in own cut',all(routes.get(k)==value for k,value in oldroutes.items()))
    for key in ['week_2_b20_fixed_fire_AD_index','week_2_b20_fixed_fire_AD_report','week_2_b20_fixed_fire_AD_plan']:check('New route '+key,(ROOT/routes[key]).exists())
    for path in [ROOT/i['documentation'],REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',REPO/'docs/semana2/BALANCE_NOCTURNO_PARCIAL_20261024.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md']:
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8-sig')):
            target=target.strip('<>').split('#')[0]
            if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',target):continue
            check('Local link '+rel(path)+' -> '+target,(path.parent/unquote(target)).resolve().exists())
    oldn=read(BEFORE/NIGHT.relative_to(ROOT));after=read(AFTER/NIGHT.relative_to(ROOT));live=read(NIGHT)
    check('Own completion exactly once in cut/live',sum(x['id']==p['id'] for x in after['completed_units'])==sum(x['id']==p['id'] for x in live['completed_units'])==1)
    check('Earlier completed units preserved',after['completed_units'][:len(oldn['completed_units'])]==oldn['completed_units'])
    check('Only own currentunit cleared in own cut',after['current_unit']==(None if (oldn.get('current_unit') or {}).get('id')==p['id'] else oldn['current_unit']))
    for key in ['window_start','window_end','frequency','automation_id','automation_kind','automation_target_thread','same_chat','other_automations_changed','forum_reading_guard','confirmation_header_exposure']:check('Schedule/guard unchanged '+key,after[key]==oldn[key] and live[key]==after[key])
    check('Earlier warnings not automatically closed',all(x in after['open_conditions'] for x in oldn['open_conditions']))
    check('Own2024scope closed',live['confirmation_2024_open'] is False and state[STATEKEY]['ledger_read'] is False)
    forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';data=forum.read_bytes();receipt=read(RUN/'forum_receipts.json')['receipts'][-1];digest=hashlib.sha256();prefix=False
    for line in data.splitlines(keepends=True):
        digest.update(line)
        if digest.hexdigest()==receipt['sha256']:prefix=True;break
    check('Serialized forum044 prefix intact',prefix)
    for suffix in ['043','044']:check('Own forum comment exactly once '+suffix,data.count(('<!-- aporte:COD-S2-20261024-'+suffix+' -->').encode())==1)
    for path in v['expected_failure_runs']:check('Actual-flow expected failure archived',(ROOT/path/'expected_adversary_failure.json').exists())
    result={'utc':NOW,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'scope':'Own before/after cuts plus live source/own completion guards. No statistical suite repeated. Shared pointer changes after this cut are allowed.'}
    dump(RUN/'closure_verification.json',result);assert result['failed']==0,[x for x in checks if not x['pass']]
    shared={x['path'] for x in changes}|{rel(forum)}
    paths={x for x in RUN.rglob('*') if x.is_file()};paths.update(ROOT/x['path'] for x in changes);paths.update([INDEX,tests,ROOT/i['documentation'],ROOT/i['plan'],ROOT/p['code'],Path(__file__),forum])
    paths.update(REPO/'herramientas'/name for name in ['verificar_incendio_AD_b20_2023.py','documentar_incendio_AD_b20_2023.py'])
    paths.update(ROOT/'Hackaton/Semana 2/Codex'/name for name in ['preinscribir_incendio_AD_b20_2023.py','incendio_AD_b20_2023_preinscripcion.md','incendio_AD_b20_2023_resultado.md'])
    for path in v['expected_failure_runs']:paths.update(x for x in (ROOT/path).rglob('*') if x.is_file())
    manifest={'utc':NOW,'notice':'Immutable artifacts exact; mutable shared files are dated cuts and verified by preserved source/append semantics, not a promise they never change.','files':[{'path':rel(x),'sha256':sha(x),'bytes':x.stat().st_size,'mutable_shared':rel(x) in shared} for x in sorted(paths)]};dump(RUN/'closure_manifest.json',manifest)
    immutable_bad=[x['path'] for x in manifest['files'] if not x['mutable_shared'] and sha(ROOT/x['path'])!=x['sha256']]
    integrity={'utc':datetime.now(timezone.utc).isoformat(),'immutable_artifacts_exact':not immutable_bad,'immutable_mismatches':immutable_bad,'frozen_sources_exact':all(sha(ROOT/x['path'])==x['sha256'] for x in p['frozen_sources']),'own_unit_retained':any(x['id']==p['id'] for x in read(NIGHT)['completed_units']),'new_fits':0,'model_loads':0,'new_price_predictions':0,'new_bootstrap':0,'closure_failed':result['failed']}
    dump(RUN/'final_integrity_receipt.json',integrity);assert integrity['immutable_artifacts_exact'] and integrity['frozen_sources_exact'] and integrity['own_unit_retained']
    print(json.dumps({'index':rel(INDEX),'closing_passed':result['passed'],'failed':0,'completed_units_at_cut':len(after['completed_units']),'actual_registration_mode':'current_unit' if (oldn.get('current_unit') or {}).get('id')==p['id'] else 'parallel_or_foreign_preserved','counter_values_cut':values,'new_fits':0,'model_loads':0},ensure_ascii=True))


if __name__=='__main__':main()
