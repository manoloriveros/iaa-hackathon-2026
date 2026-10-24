"""Cierre B19: archivo v7 exacto, veinte recetas, contador propio y novena unidad."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import unquote
import json,hashlib,re,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026';RUN=REPO/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214'
INDEX=REPO/'registro/semana2_desarrollo2023_actual.json';COUNTERS=REPO/'registro/semana2_contadores_propios_actual.json';NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
NOW=datetime.now(timezone.utc).isoformat();BACK=RUN/'state_before_registration';changes=[]

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
    after=fn(before.decode('utf-8-sig')).encode('utf-8');tmp=path.with_name(path.name+'.v8cierre.tmp')
    assert path.read_bytes()==before,'Concurrencia '+str(path)
    with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before,'Concurrencia '+str(path);os.replace(tmp,path)
    changes.append({'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path),'backup':rel(backup)})

p=read(RUN/'plan_snapshot.json');r=read(RUN/'report.json');i=read(RUN/'index_proposed.json');a=read(RUN/'assessment.json');v=read(RUN/'verification.json');f=read(RUN/'fixture_checks.json')
assert sha(INDEX)==p['parent_index_sha256'] and sha(COUNTERS)==p['counter_before_sha256']
assert (ROOT/p['parent_index_snapshot']).read_bytes()==INDEX.read_bytes()
assert read(NIGHT)['current_unit']['id']==p['id']
assert v['failed']==f['failed']==read(RUN/'readout_reconciliation.json')['failed']==0
assert all(sha(ROOT/x['path'])==x['sha256'] for x in p['frozen_sources'])
BACK.mkdir(exist_ok=False);old=read(INDEX)
preserved={rel(path):sha(path) for path in [REPO/'registro/semana2_sensibilidad_observacion_actual.json',REPO/'registro/semana2_soporte_calendario2023_actual.json',REPO/'registro/semana2_coberturas_peril2023_actual.json']}
historical=[{'path_at_original_cut':rel(INDEX),'sha256':p['parent_index_sha256'],'immutable_snapshot':p['parent_index_snapshot']},
    {'path_at_original_cut':rel(COUNTERS),'sha256':p['counter_before_sha256'],'immutable_snapshot':p['counter_before_snapshot']}]
i.update(all_alternatives_preserved=True,historical_active_index_resolution=historical,documentation_sha256=sha(ROOT/i['documentation']),as_of_registration_utc=NOW)
forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';cut=forum.read_bytes()
for suffix in ['034','035']:assert cut.count(('<!-- aporte:COD-S2-20261024-'+suffix+' -->').encode())==1
change(INDEX,lambda raw:json.dumps(i,ensure_ascii=False,indent=2)+'\n')

def counters(raw):
    co=json.loads(raw);assert co['cumulative_price_base_fits']==165 and co['cumulative_closed_form_constants']==285
    assert p['id'] not in [x['id'] for x in co['increments']]
    if co['baseline']['index']==rel(INDEX):
        co['baseline']['index_at_original_registration']=co['baseline']['index'];co['baseline']['index']=p['parent_index_snapshot']
    co['increments'].append({'id':p['id'],'run':rel(RUN),'price_GLM_fits':15,'constant_values':0,'auxiliary_fits':0,'reporting_fits':0,'new_scores':'Only B19; two new grouped pairs, no old-pair bootstrap repeated'})
    co.update(as_of_utc=NOW,cumulative_price_base_fits=180,cumulative_closed_form_constants=285,latest_development_index=rel(INDEX),historical_active_index_resolution=historical)
    return json.dumps(co,ensure_ascii=False,indent=2)+'\n'
change(COUNTERS,counters)

def night(raw):
    n=json.loads(raw);assert n['current_unit']['id']==p['id'] and len(n['completed_units'])==8
    for entry in n['completed_units']:
        if entry['id']==old['id']:
            if 'index' in entry:entry['index_at_original_registration']=entry['index']
            entry.update(index=p['parent_index_snapshot'],index_sha256=p['parent_index_sha256'])
    entry={k:i[k] for k in ['id','run','documentation','verification','fixtures','decision_journal','forum_result']};entry['index']=rel(INDEX)
    warnings={x['id']:x for x in n['open_conditions']}
    for item in a['warnings']:warnings[item['id']]=item
    n.update(status='scheduled_nine_units_verified_B19_adverse_parent_conditions_open',updated_utc=NOW,current_unit=None,
        latest_completed_unit=entry,completed_units=n['completed_units']+[entry],open_conditions=list(warnings.values()),current_global_fit_counter_index=rel(COUNTERS),
        historical_active_index_resolution=historical,
        next_unit='Review B19 coverage-coefficient stability and contributions of groups using saved models/OOF, without refitting or repeating its completed2-pair bootstrap. Building coverage ratio changes direction acrossfolds; motornewbusiness andthirdpartyonly worsen. Explain before any new registered standard recipe; no automatic regularization/trees. Own counters180/285, B00/B01-B19 retained,2024closed and prior header exposure disclosed.',
        queue=['Diagnose B19 coefficient/group stability from frozen artifacts, no routine fit or bootstrap repetition',
            'Keep coverage semantics, capital scale, climate availability, prior/reserves/ultimate and adaptive-search limitations open',
            'Maintain honest partial balance; final window balance at07:00Bogota. No external2024 subjects/artifacts/ledger or second batch'],
        no_retraining_or_suite_repetition_for_completed_v8=True)
    n['integration_decisions']['coverage_GLM']='B19 adds one coverage field perline withsameT0/C0. All15fit objectives improve but globalOOF.086710->.082470, building loss andmotornewbusiness deterioration. No promotion/retirement; no masks or hyperparameter changes.'
    return json.dumps(n,ensure_ascii=False,indent=2)+'\n'
change(NIGHT,night)

def routes(raw):
    for key,value in [('week_2_development_index',rel(INDEX)),('week_2_development_report',i['documentation']),('week_2_development_plan',i['plan']),('week_2_development_oof',i['oof'])]:raw=top(raw,key,value)
    return top(raw,'week_2_development_v7_snapshot',p['parent_index_snapshot'],True)
change(ROOT/'RUTAS_PROYECTO.json',routes)
statekey='week_2_development2023_v8_20261024'
def state(raw):
    obj=json.loads(raw)
    phase={'as_of_utc':NOW,'phase':'week2_B19_standard_coverage_GLM_verified_adverse_parent_B00_retained_own2024closed','current_state_key':statekey,
        'historical_fields_notice':'Previous states are dated cuts. Current catalog20/8cuts and ownpricecounter180/285; catalog-only105/60. Prior active-index SHA resolves to immutable v7 snapshot, no old run rewritten.'}
    dev={'as_of_utc':NOW,'index':rel(INDEX),'run':rel(RUN),'documentation':i['documentation'],'training_years':[2023],'scored_years':[2023],
        'rows':50094,'groups':30869,'folds':5,'new_price_base_fits':15,'new_constants':0,'new_curves':0,'new_auxiliaries':0,
        'own_cumulative_price_base_fits':180,'own_cumulative_constants':285,'catalog_only_price_fits':105,'catalog_only_constants':60,
        'summary':r['summary'],'new_pairs':r['pairs'],'verification':i['verification'],'fixtures':i['fixtures'],'readout_reconciliation':i['readout_reconciliation'],
        'reference':'W2-B00','all_alternatives_preserved':True,'promotion':False,'final_roster_frozen':False,'parent_snapshot':p['parent_index_snapshot'],
        'historical_active_index_resolution':historical,'forum_comments':['COD-S2-20261024-034','COD-S2-20261024-035'],
        'confirmation_opened_by_this_task':False,'ledger_read':False,'external2024_subject_exposure_previously_disclosed':True,'complete_blindness_claim_allowed':False,
        'external2024_artifacts_read_this_unit':False,'professional_independent_validation':False}
    continuity=dict(obj['week_2_nocturnal_continuation_20261023'],as_of_utc=NOW,latest_completed_unit=p['id'],next_unit=read(NIGHT)['next_unit'],historical_active_index_resolution=historical)
    collab=dict(obj['collaboration_forum'],updated_utc=NOW,latest_Codex_comment='COD-S2-20261024-035')
    for key,value in [('current_phase',phase),('memory_as_of',datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()),('week_2_nocturnal_continuation_20261023',continuity),('collaboration_forum',collab)]:raw=top(raw,key,value)
    return top(raw,statekey,dev,True)
change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
note=f'''

## GLM sencillo con coberturas: noveno avance nocturno y octavo corte del catálogo

Codex, corte UTC {NOW}. El participante autorizó expresamente registrar y probar coberturas como efectos principales sin cambiar T0/C0, solo en 2023, con B00 conservado y 2024 cerrado. Plan S2-DEV2023-v8-20261024 y comentario 034 a las 01:29:44 UTC preceden al ajuste; corrida dev8_20261024T013001Z_e8a35214; resultado 035 a las 01:37:31 UTC. Informe GLM_COBERTURAS_2023.md e índice de desarrollo actual. La copia exacta del índice v7 se conserva en semana2_desarrollo2023_v7_snapshot.json; el OOF viejo y sus diecinueve recetas mantienen todos sus valores.

B19 añade cover_type a autos y accidental_damage_cover a edificios/contenidos: siete variables originales por ramo, efectos principales sin interacciones o máscaras. Mismo Tweedie 1,5, log, alpha cero, lbfgs, máximo 2.000 iteraciones, tolerancia 1e-6 y preparación de B14 aprendida en ajuste. Quince GLM nuevos convergieron sin retocar receta o reintentar. Se mantienen exactamente los 50.094 periodos, 30.869 componentes, cinco folds y T0/exposición/C0 propios de cada fold, incluido capital de B14 condicionado. No entran clima, credibilidad o recalibración nuevos. Los treinta siniestros positivos de hogar con bandera desactivada se conservan, sin imponer coste cero.

Resultado adverso: B19 D² global 0,08246970 frente a B14 0,08671008; B00 mantiene 0,06858169. Edificios pasa de 0,02109431 a 0,00835168 y contenidos de 0,03734282 a 0,03628137. Autos agregado mejora de 0,03310128 a 0,03372198, pero autos nuevos deteriora de −0,01004489 a −0,03182203 y third_party_only de −0,01589187 a −0,04279272. En los quince ajustes mejora la desviancia de entrenamiento; no se sostiene globalmente fuera del fold. En edificios, la razón de tasa AD_yes/AD_no varía de 0,795 a 1,388 y cambia dirección entre folds. Un A/E más cercano a uno en celdas no acredita mejor predicción por fila. Las contribuciones al cambio global usan la nula global y no promedian D² de ramos.

Solo se calcularon dos contrastes nuevos, con 2.000 sorteos agrupados comunes. B19/B14 delta −0,00424038, intervalo exploratorio [−0,00996863; +0,00050667], e influencia tras retirar sus 31 grupos más favorables −0,00714544. B19/B00 delta +0,01388801, intervalo [−0,01105272; +0,03761405], con influencia −0,01472425. Ambos intervalos incluyen cero y omiten incertidumbre de reajuste de modelos/primera etapa; búsqueda adaptativa, sin garantía temporal. No se borran o reajustan grupos. El catálogo de veinte recetas conserva 171 parejas históricas más dos nuevas; las otras diecisiete parejas posibles con B19 no se calcularon. No se promueve, retira, declara equivalencia o congela lista final.

El predicho observado total cambia de 15.429.695,38 a 15.436.941,83 CU y el nominal condicionado de los mismos periodos de 2023 de 15.606.084,09 a 15.613.508,68 CU (+0,0476%). No son precios o verdad de último de 2025/test. Pasaron 569 comprobaciones separadas con fit bloqueado, 39 adversos focales y ocho conciliaciones, con solapamiento. Replay B19/B14 exacto, medianas/escalas/categorías propias, exp(X beta), gradiente y objetivo por otro método, métricas sklearn y bootstrap por multiplicidades cotejados. Cuatro comandos reales rechazan año sintético 2024, cobertura ausente o T0/C0 cambiado antes de fit; sus fallos esperados tienen marcador y no están pendientes. Una inspección auxiliar de metadatos encontró entradas antiguas sin clave index; se corrigió la lectura con claves opcionales, sin cambiar cálculos, repetir ajustes o alterar esas entradas.

El contador propio pasa de 165 a 180 ajustes de precio y conserva 285 constantes. El linaje exclusivo del catálogo tiene 105 ajustes y 60 constantes; las sensibilidades anteriores explican la diferencia. Los treinta auxiliares y contadores de reporte/mezcla quedan separados, sin incremento. La base del contador ahora resuelve su SHA antiguo por el snapshot v7. Los registros que apuntaban al índice activo en cortes anteriores son históricos; no marcar una regresión ni repetir sus suites por el cambio intencional del puntero. La memoria nocturna guarda rutas inmutables del índice y del contador previos.

Se conservan B00 y B01–B19, hipótesis adversas y condiciones de capital, clima, prior, reservas, cola, cobertura individual y adaptación. Próxima unidad: estudiar estabilidad de coeficientes y contribuciones de grupos de B19 desde modelos/OOF congelados antes de otra receta, sin reentrenamiento o bootstrap por rutina y sin salto automático a árboles/interacciones. Revisión técnica propia de Codex, no profesional independiente o aprobación humana. El entorno local y versiones quedaron archivados sin afirmar reproducción en otro sistema.

2024 permanece cerrado para este trabajo, también test, actas, predicciones, scores y lectura del ledger. Se conserva la exposición previa a un asunto externo con métricas de confirmación, sin repetirlas o usarlas ni afirmar ceguera completa. El lector del foro muestra solo autor, ID y UTC; seleccionar ramas y secciones propias de memoria/estado, no volcar contenido externo completo. No se verifica ni invalida autorización anunciada en otro chat y no se abre otra tanda. Sin remoto, envíos, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. La ventana y frecuencia existentes siguen hasta las 07:00 Bogotá; novena unidad terminada y balance todavía parcial.
'''
for filename in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/filename,lambda raw:raw+note)
update='\n\n## GLM con coberturas: noveno avance nocturno\n\n[B19](../Repositorio_IAA2026/docs/semana2/GLM_COBERTURAS_2023.md) añade un efecto de cobertura por ramo a B14 con T0/C0 y folds iguales. Quince ajustes convergieron; D² global cae de 0,086710 a 0,082470, con deterioro en edificios y autos nuevos. B00 y B01–B19 conservados, sin promoción o cambios de parámetros. Contador propio 180/285; catálogo solo 105/60. Próxima revisión: estabilidad de coeficientes y grupos desde artefactos, antes de otra receta. 2024 cerrado en este trabajo y exposición previa de un título externo declarada.\n'
for filename in ['README.md','PLAN_TRABAJO.md']:change(ROOT/'Hackaton/Semana 2'/filename,lambda raw:raw+update)
change(REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',lambda raw:raw+'\n\n## Novena unidad: GLM con coberturas principales\n\n[B19](GLM_COBERTURAS_2023.md) terminó con quince ajustes nuevos y T0/C0/folds originales. Mejora el ajuste de entrenamiento en todos los nodos y empeora OOF global frente a B14; edificios concentra la pérdida y autos nuevos también deteriora. No se promueve, retira o retoca regularización. Contador propio 180/285, catálogo exclusivo 105/60; dos parejas nuevas, sin repetir antiguas. Próxima unidad: estabilidad de coeficientes y grupos desde archivos, sin reentrenar por rutina. El [snapshot v7](../../registro/semana2_desarrollo2023_v7_snapshot.json) resuelve los hashes históricos del índice previo; el cambio intencional del puntero no invalida corridas cerradas. La guarda del foro seguro y la exposición anterior permanecen; 2024 cerrado.\n')
change(REPO/'docs/semana2/COBERTURAS_Y_DENOMINADORES_PERIL_2023.md',lambda raw:raw+'\n\n## Ensayo posterior registrado\n\nEl [GLM B19](GLM_COBERTURAS_2023.md) ya probó cobertura como efecto principal sobre B14, sin cambiar T0/C0 ni imponer ceros. Empeora el D² global y se conserva como resultado adverso; no se adopta máscara o elimina siniestros. La propuesta pendiente descrita en el corte anterior queda ejecutada bajo su receta propia.\n')
change(REPO/'docs/semana2/CAPITAL_POR_FILA_Y_AUTOS_NUEVOS_2023.md',lambda raw:raw+'\n\n## Corte posterior del catálogo\n\nEl [octavo corte](GLM_COBERTURAS_2023.md) conserva exactamente este OOF y añade B19, un GLM con cobertura principal y T0/C0 iguales. Este índice se archiva en el [snapshot v7](../../registro/semana2_desarrollo2023_v7_snapshot.json); no se reescriben resultados de capital o credibilidad.\n')
change(REPO/'docs/semana2/BALANCE_NOCTURNO_PARCIAL_20261024.md',lambda raw:raw+'\n\n## Novena unidad: B19 probado y conservado como adverso\n\nEl [GLM con coberturas](GLM_COBERTURAS_2023.md) mantiene T0/C0 y siete efectos principales por ramo. D² 0,082470 frente a 0,086710 de B14; mejora entrenamiento en quince ajustes, pierde OOF global, con deterioro en edificios y autos nuevos. Ambos intervalos nuevos incluyen cero. B00 y B01–B19 permanecen; no se promueve o retoca receta. Contador propio 180 ajustes/285 constantes; catálogo exclusivo 105/60, etapas anteriores separadas. La siguiente unidad revisará coeficientes y grupos desde artefactos sin repetir entrenamiento o bootstrap. Nueve unidades concluidas, balance todavía parcial hasta las 07:00 Bogotá.\n')
change(REPO/'registro/semana2_listo_entrenar.json',lambda raw:top(raw,'latest_development_execution',{'utc':NOW,'index':rel(INDEX),'run':rel(RUN),'documentation':i['documentation'],
    'training_years':[2023],'new_price_fits':15,'own_price_counters':[180,285],'catalog_only_counters':[105,60],'reference':'W2-B00','all_alternatives_preserved':True,
    'promotion':False,'confirmation_2024_open':False,'ledger_read':False,'external2024_subject_exposure_previously_disclosed':True,'complete_blindness_claim_allowed':False}))
tests=REPO/'registro/semana2_desarrollo2023_pruebas_v8.json'
dump(tests,{'author':'Codex','utc':NOW,'verification':i['verification'],'fixtures':i['fixtures'],'readout_reconciliation':i['readout_reconciliation'],
    'expected_failure_runs':f['expected_failure_runs'],'professional_independent_validation':False})
dump(RUN/'forum_receipts.json',{'source':'Serialized helper outputs in this chat','receipts':[
    {'id':'COD-S2-20261024-034','utc':'2026-10-24T01:29:44+00:00','previous_sha256':'120cc87e3db84e3b3342ed050c1f94d67001c369001f0b3ae5ba554e6b73c57b','sha256_at_append':'14f9f83e474d96bbf8d52d4d9bf4f04a90982955c1f2aceab6ebfd4fa07a86e9'},
    {'id':'COD-S2-20261024-035','utc':'2026-10-24T01:37:31+00:00','previous_sha256':'d9896e4e815fc776d451fd084cab208af4c70bd4344200df44806797d9f5d0cc','sha256_at_append':'cf673619e0f232ae3c33fc7f7c8b929346bbdedab9c0793d84029114326924a8'}]})
dump(RUN/'registration.json',{'author':'Codex','utc':NOW,'changes':changes,'prior_index_snapshot':p['parent_index_snapshot'],'historical_active_index_resolution':historical,
    'other_audit_indices_preserved':preserved,'metadata_probe_error':'Read-only probe used missing historical index key; corrected with optional-key inspection. No fit/test rerun or numerical change.',
    'reference':'W2-B00','ledger_read':False,'confirmation_opened_by_this_task':False})
checks=[]
def check(n,x):checks.append({'name':n,'pass':bool(x)})
for name in ['report','plan','producer','oof','manifest','assessment','decision_journal']:check('Index '+name,sha(ROOT/i[name])==i[name+'_sha256'])
for name in ['verification','fixtures','readout_reconciliation']:check('Receipt '+name,sha(ROOT/i[name]['path'])==i[name]['sha256'] and read(ROOT/i[name]['path'])['failed']==0)
check('Parent v7 exact',sha(ROOT/p['parent_index_snapshot'])==p['parent_index_sha256'] and (ROOT/p['parent_index_snapshot']).read_bytes()==(BACK/INDEX.relative_to(ROOT)).read_bytes())
check('20recipes and8historycuts',len(i['models_consulted'])==20 and len(i['alternatives_preserved'])==19 and len(i['history'])==8 and i['reference']=='W2-B00')
check('All prior summaries exact',i['summary'][:-1]==old['summary'])
check('173pairs with17uncomputed',i['pairs'][:171]==old['pairs'] and len(i['pairs'])==173 and i['pair_provenance']['B19_other_possible_pairs_uncomputed']==17)
for item in p['frozen_sources']:check('Frozen source '+item['path'],sha(ROOT/item['path'])==item['sha256'])
for item in read(RUN/'manifest.json')['files']:check('Run artifact '+item['path'],sha(RUN/item['path'])==item['sha256'])
for path,expected in preserved.items():check('Other audit exact '+path,sha(ROOT/path)==expected)
co=read(COUNTERS)
check('Owncounter reconciled once',co['baseline']['price_base_fits']+sum(x['price_GLM_fits'] for x in co['increments'])==180==co['cumulative_price_base_fits'] and co['baseline']['constants']+sum(x['constant_values'] for x in co['increments'])==285==co['cumulative_closed_form_constants'])
check('Baseline SHA resolvesimmutable',sha(ROOT/co['baseline']['index'])==co['baseline']['sha256'])
oldstate=read(BACK/'Preparación/ESTADO_PROYECTO.json');newstate=read(ROOT/'Preparación/ESTADO_PROYECTO.json')
check('Historical state branches exact',all(newstate.get(k)==x for k,x in oldstate.items() if k not in ['current_phase','memory_as_of','collaboration_forum','week_2_nocturnal_continuation_20261023']))
oldroutes=read(BACK/'RUTAS_PROYECTO.json');newroutes=read(ROOT/'RUTAS_PROYECTO.json')
check('Other routes exact',all(newroutes.get(k)==x for k,x in oldroutes.items() if k not in ['week_2_development_index','week_2_development_report','week_2_development_plan','week_2_development_oof']))
for key,value in newroutes.items():
    if key.startswith('week_2_'):check('Route '+key,(ROOT/value).exists())
for item in changes:
    if item['path'].endswith('.md'):check('Prose prefix '+item['path'],(ROOT/item['path']).read_bytes().startswith((ROOT/item['backup']).read_bytes()))
for doc in [ROOT/i['documentation'],REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',REPO/'docs/semana2/BALANCE_NOCTURNO_PARCIAL_20261024.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md']:
    for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        target=link.strip('<>').split('#')[0]
        if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',target):continue
        check('Link '+rel(doc)+' -> '+target,(doc.parent/unquote(target)).resolve().exists())
n=read(NIGHT);oldn=read(BACK/NIGHT.relative_to(ROOT))
check('Ninth unit complete',n['current_unit'] is None and n['latest_completed_unit']['id']==p['id'] and len(n['completed_units'])==9)
check('Native schedule exact',all(n[k]==oldn[k] for k in ['window_start','window_end','frequency','automation_id','automation_kind','automation_target_thread','same_chat','other_automations_changed']))
check('Exposure guard exact',n['forum_reading_guard']==oldn['forum_reading_guard'] and n['confirmation_header_exposure']==oldn['confirmation_header_exposure'])
check('Own2024closed',n['confirmation_2024_open'] is False and newstate[statekey]['ledger_read'] is False)
for path in f['expected_failure_runs']:check('Adversary marked notpending '+path,(ROOT/path/'expected_adversary_failure.json').exists())
check('Forum prefix preserved',forum.read_bytes().startswith(cut))
result={'utc':NOW,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'scope':'Closing hashes, lineage, counters and links only; no repeated statistical suite'}
dump(RUN/'closure_verification.json',result);assert result['failed']==0,[x for x in checks if not x['pass']]
paths={x for x in RUN.rglob('*') if x.is_file()};paths.update(ROOT/x['path'] for x in changes);paths.update([ROOT/i['documentation'],ROOT/i['plan'],ROOT/i['producer'],ROOT/p['parent_index_snapshot'],ROOT/p['counter_before_snapshot'],Path(__file__),forum,tests])
paths.update(REPO/'herramientas'/filename for filename in ['verificar_desarrollo2023_v8_semana2.py','probar_desarrollo2023_v8_semana2.py','documentar_desarrollo2023_v8_semana2.py'])
paths.update(ROOT/'Hackaton/Semana 2/Codex'/filename for filename in ['preinscribir_desarrollo2023_v8.py','desarrollo2023_v8_preinscripcion.md','desarrollo2023_v8_resultado.md','nocturno_antes_v8.json'])
for path in f['expected_failure_runs']:paths.update(x for x in (ROOT/path).rglob('*') if x.is_file())
dump(RUN/'closure_manifest.json',{'utc':NOW,'notice':'Dated cut; shared files can change later. Parent/current-index lineage resolves via immutable snapshots.','files':[{'path':rel(x),'sha256':sha(x),'bytes':x.stat().st_size} for x in sorted(paths)],'reference':'W2-B00','confirmation_opened_by_this_task':False})
print(json.dumps({'registered':rel(INDEX),'closure_checks':result['passed'],'failed':0,'recipes':20,'history_cuts':8,'night_units':9,'own_price_counters':[180,285],'catalog_only_counters':[105,60],'reference':'W2-B00'}))
