"""Registro único de la octava unidad, sin entrenar por cambios de documentación."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import unquote
import json,hashlib,re,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/coberturas_20261024T011932Z_14b50ca9'
INDEX=REPO/'registro/semana2_coberturas_peril2023_actual.json';NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
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
    after=fn(before.decode('utf-8-sig')).encode('utf-8');tmp=path.with_name(path.name+'.coberturascierre.tmp')
    assert path.read_bytes()==before,'Concurrencia '+str(path)
    with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before,'Concurrencia '+str(path);os.replace(tmp,path)
    changes.append({'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path),'backup':rel(backup)})

p=read(RUN/'plan_snapshot.json');i=read(RUN/'index_proposed.json');r=read(RUN/'report.json');v=read(RUN/'verification.json');q=read(RUN/'readout_reconciliation.json')
assert r['failed']==v['failed']==q['failed']==0 and not INDEX.exists()
assert read(NIGHT)['current_unit']['id']==p['id']
assert all(sha(ROOT/x['path'])==x['sha256'] for x in p['frozen_sources'])
BACK.mkdir(exist_ok=False)
preserved={rel(path):sha(path) for path in [REPO/'registro/semana2_desarrollo2023_actual.json',REPO/'registro/semana2_sensibilidad_observacion_actual.json',REPO/'registro/semana2_soporte_calendario2023_actual.json',REPO/'registro/semana2_contadores_propios_actual.json']}
i.update(as_of_registration_utc=NOW,indices_and_counters_preserved=preserved,documentation_sha256=sha(ROOT/i['documentation']))
dump(INDEX,i)
forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';cut=forum.read_bytes()
for suffix in ['032','033']:assert cut.count(('<!-- aporte:COD-S2-20261024-'+suffix+' -->').encode())==1

def night(raw):
    n=json.loads(raw);assert n['current_unit']['id']==p['id'] and len(n['completed_units'])==7
    entry={k:i[k] for k in ['id','run','documentation','verification','decision_journal','forum_result']};entry['index']=rel(INDEX)
    warnings={x['id']:x for x in n['open_conditions']}
    for item in i['warnings']:warnings[item['id']]=item
    n.update(status='scheduled_eight_units_verified_home_coverage_mask_rejected_conditions_open',updated_utc=NOW,current_unit=None,
        latest_completed_unit=entry,completed_units=n['completed_units']+[entry],latest_coverage_exposure_audit_index=rel(INDEX),open_conditions=list(warnings.values()),
        next_unit='If continuing model work, preregister a standard GLM main-effect coverage test against frozen B14, with cover_type for motor and accidental_damage_cover for home. SameT0/C0/folds, no structuralzeros, no interactions or trees, preserveB00/all alternatives. Not yet preregistered or run. Read own counters165/285; keep external2024 subjects/artifacts quarantined and disclose prior header exposure.',
        queue=['Preregister standard GLM coverage main effects only if addressing documented omitted effects in reducedB14; no structural masks for home',
            'Keep motor coverage/peril mapping conditional despite no outside observed claims; numerator/denominator/row-composition coherence required for any future mask stress',
            'Preserve current balance and source lineage; no unchanged suite or bootstrap repetition; final honest balance at07:00Bogota'],
        no_retraining_or_suite_repetition_for_completed_coverage_audit=True)
    n['integration_decisions']['coverage_denominators']='Home hardaccidental_damage mask conflicts with30closed positive claims/29045.06CU; not adopted. Motor conventional masks observedcompatible only. No bicycle-to-alltheft mask. Broad current denominator remains conditional; no fits/scores this unit.'
    n.setdefault('condition_progress_without_auto_closure',{})['SUPPORT-COVERAGE']='Coverage audit complete: hardhome mask incompatible, motor mapping conditional, optionalbicycle not alltheft. Actual contractual crosswalk and row-specific composition still open.'
    return json.dumps(n,ensure_ascii=False,indent=2)+'\n'
change(NIGHT,night)

def routes(raw):
    for key,value in [('week_2_coverage_exposure_index',rel(INDEX)),('week_2_coverage_exposure_report',i['documentation']),('week_2_coverage_exposure_plan',i['plan'])]:raw=top(raw,key,value,True)
    return raw
change(ROOT/'RUTAS_PROYECTO.json',routes)
statekey='week_2_coverage_peril_exposure2023_v1_20261024'
def state(raw):
    obj=json.loads(raw)
    phase={'as_of_utc':NOW,'phase':'week2_coverage_denominator_audit_verified_home_mask_incompatible_no_price_change_own2024closed','current_state_key':statekey,
        'historical_fields_notice':'Earlier state entries are dated cuts. Main19/sensitivity3/calendar indices and counters165/285 unchanged. Eight night units complete, no full-blindness claim after prior external subject exposure.'}
    dev={'as_of_utc':NOW,'index':rel(INDEX),'documentation':i['documentation'],'run':rel(RUN),'audited_policy_years':[2023],'rows':50094,'groups':30869,'folds':5,
        'new_fits':0,'new_curves':0,'new_scores':0,'new_bootstrap':0,'home_outside_candidate_positive_claims':30,'home_outside_candidate_net_CU':29045.06,
        'motor_observed_compatibility_not_contract_approval':True,'mask_adoption':False,'reference':'W2-B00','all_alternatives_preserved':True,
        'own_price_counters':[165,285],'indices_and_counters_preserved':preserved,'verification':i['verification'],'readout_reconciliation':i['readout_reconciliation'],
        'forum_comments':['COD-S2-20261024-032','COD-S2-20261024-033'],'ledger_read':False,'confirmation_opened_by_this_task':False,
        'external2024_subject_exposure_previously_disclosed':True,'complete_blindness_claim_allowed':False,'external2024_artifacts_read_this_unit':False,
        'future_GLM_coverage_test_not_yet_preregistered_or_executed':True,'professional_independent_validation':False}
    continuity=dict(obj['week_2_nocturnal_continuation_20261023'],as_of_utc=NOW,latest_completed_unit=p['id'],next_unit=read(NIGHT)['next_unit'])
    collab=dict(obj['collaboration_forum'],updated_utc=NOW,latest_Codex_comment='COD-S2-20261024-033')
    for key,value in [('current_phase',phase),('memory_as_of',datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()),('week_2_nocturnal_continuation_20261023',continuity),('collaboration_forum',collab)]:raw=top(raw,key,value)
    return top(raw,statekey,dev,True)
change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
note=f'''

## Coberturas y denominadores por peril: octavo avance solo 2023

Codex, corte UTC {NOW}. Instrucción directa del participante: revisar coberturas y exposición por peril, registrar antes de cualquier ensayo, conservar B00, publicar decisiones/resultados y mantener 2024 cerrado. Plan S2-COBERTURAS-PERIL2023-v1-20261024 y foro 032 a las 01:19:28 UTC preceden al cruce; corrida coberturas_20261024T011932Z_14b50ca9; resultado 033 a las 01:23:21 UTC. Informe COBERTURAS_Y_DENOMINADORES_PERIL_2023.md e índice semana2_coberturas_peril2023_actual.json, ambos en el repositorio común.

Se conservan 50.094 periodos de 2023, 30.869 componentes, cinco folds y 4.567 siniestros con neto 15.297.103,84 CU. Los denominadores usan exposición nominal corregida de F0, en años de cobertura, por qN propia del peril/fold; qC de coste se conserva por separado. Se contrastan máscaras candidatas con particiones de nominal, conteo, coste y reclamaciones, no nuevas tasas de riesgo. El cociente D_all/D_candidate es solo una razón de exposición, no factor de precio aprendido. Los datos retenidos no entran en vistas de ajuste; el perfil global es descriptivo. No hay ajustes, curvas, predicciones de precio, scores o bootstrap nuevos. Índices principal de 19 recetas, sensibilidad de tres cortes, calendario y contador propio 165/285 exactos.

La máscara de daño accidental de hogar queda rechazada como exclusión estructural compatible con T0: seis siniestros de edificios y 24 de contenidos tienen bandera desactivada, coste neto positivo y status cerrado. Suman 3.175,58 y 25.869,48 CU, respectivamente, 29.045,06 CU en total. No se borran o reclasifican para sostener la hipótesis. La causa semántica o contractual sigue abierta. El denominador candidato retendría aproximadamente 38,66–40,32% de exposición efectiva de conteo en edificios y 43,41–45,33% en contenidos; reducir únicamente D elevaría n/D por una razón entre 2,21 y 2,59 sin resolver el numerador incompatible.

En autos no aparecen reclamaciones fuera de las reglas convencionales de daño propio/glass_hail en comprehensive o robo en comprehensive/third_party_fire_theft. Es compatibilidad observada de 2023, no clausulado validado o riesgo futuro nulo. Los denominadores candidatos retienen alrededor de 76,27–79,56% y 88,61–90,07%, respectivamente. Las descripciones oficiales archivadas enumeran categorías y coberturas opcionales pero no una matriz contractual completa. Bicycle_cover no se convierte en máscara para todo robo o daño accidental. Se conserva el denominador amplio actual como aproximación condicionada, sin pretender que represente cobertura individual comprobada.

Pasaron 167 controles del productor, 2.345 verificaciones y adversos focales y 725 conciliaciones de lectura, con solapamiento. La cuenta separada usa diccionarios y math.fsum para nominal, conteo/coste y centavos, y verifica categorías y ámbitos. Los comandos reales con año sintético 2024 o cobertura ausente fallan antes de salidas y conservan sus artefactos esperados. Estos pases técnicos no validan la hipótesis de hogar que falló. Son revisión propia, no profesional independiente ni aprobación humana. Se guardan las 150 celdas de denominador y 430 por categoría, con ceros y resultados adversos.

No se adopta máscara o cambia C0, T0, B00 o alternativa. El próximo ensayo justificable es un GLM sencillo con cobertura como efecto principal, sin ceros impuestos: cover_type en autos y accidental_damage_cover en hogar sobre B14. Responde a efectos omitidos concretos del GLM reducido; no exige árboles o interacciones. Todavía no está preinscrito, entrenado o puntuado y requiere una receta propia antes de hacerlo. No promover, retirar o congelar lista final por 2023 adaptativo.

Sigue vigente la exposición anterior a métricas externas en un título del foro, registrada en 030: no se repiten ni usan las cifras y no se afirma ceguera completa. Esta unidad no abrió títulos/cuerpos ajenos, actas, predicciones, scores o ledger de 2024/test. El lector seguro muestra solo autor, ID y UTC; al retomar seleccionar ramas y secciones propias de memoria/estado. La instrucción humana de mantener 2024 cerrado en este trabajo continúa; no se verifica ni invalida autorización ajena ni se abre otra tanda. Ventana y frecuencia nocturnas intactas hasta las 07:00 Bogotá; sin remoto, envíos, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. El balance de la noche sigue siendo parcial, con ocho unidades terminadas.
'''
for filename in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/filename,lambda raw:raw+note)
update='\n\n## Coberturas y denominadores: octavo avance nocturno\n\nLa [revisión por peril](../Repositorio_IAA2026/docs/semana2/COBERTURAS_Y_DENOMINADORES_PERIL_2023.md) encuentra 30 siniestros cerrados y positivos fuera de la máscara candidata de daño accidental de hogar: no se restringe exposición ni se borran. Autos muestra compatibilidad observada de máscaras convencionales, sin validación contractual; bicicleta no equivale a todo robo. B00, todas las alternativas y contador 165/285 exactos; cero ajustes o scores. Próximo ensayo justificable, aún sin preinscribir: cobertura como efecto principal de un GLM sencillo, con T0/C0 iguales. 2024 cerrado en este trabajo y lector seguro sin asuntos o cuerpos.\n'
for filename in ['README.md','PLAN_TRABAJO.md']:change(ROOT/'Hackaton/Semana 2'/filename,lambda raw:raw+update)
change(REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',lambda raw:raw+'\n\n## Octava unidad: cobertura y exposición por peril\n\nLa [revisión](COBERTURAS_Y_DENOMINADORES_PERIL_2023.md) termina sin ajustes o scores. La máscara de daño accidental de hogar deja 30 costes positivos cerrados fuera y no se integra; autos queda como hipótesis observacional, bicicleta no representa todo robo. B00 y todas las alternativas conservados, índices y contador 165/285 exactos. Próximo ensayo justificable: GLM estándar con efecto principal de cobertura sobre B14, manteniendo objetivo, C0 y folds; todavía no preinscrito o ejecutado. No imponer ceros, árboles o interacciones para resolver esta discrepancia. La guarda del lector seguro y la exposición previa del título siguen vigentes; 2024 cerrado en este trabajo.\n')
change(REPO/'docs/semana2/SOPORTE_CALENDARIO_REPORTE_2023.md',lambda raw:raw+'\n\n## Revisión posterior de coberturas\n\nLa [siguiente unidad](COBERTURAS_Y_DENOMINADORES_PERIL_2023.md) conserva este diagnóstico y revisa denominadores sin entrenar. Rechaza la máscara dura de daño accidental de hogar por costes positivos fuera, sin borrar siniestros; el supuesto de cobertura individual continúa abierto.\n')
change(REPO/'docs/semana2/BALANCE_NOCTURNO_PARCIAL_20261024.md',lambda raw:raw+'\n\n## Actualización: octava unidad terminada\n\nLa [auditoría de coberturas](COBERTURAS_Y_DENOMINADORES_PERIL_2023.md) no añade ajustes o scores. Hay 30 siniestros cerrados y positivos fuera de la máscara candidata de daño accidental de hogar, que no se integra; autos es compatible en lo observado pero sin matriz contractual completa. No se altera C0 o el objetivo, ni se aplica bicycle_cover a todo robo. Ocho unidades concluidas; contador propio 165/285 exacto. El próximo ensayo justificable añade cobertura como efecto principal de un GLM sencillo sobre B14, previa receta y comentario; aún no se ha preinscrito o ejecutado. Este balance sigue siendo parcial hasta el corte de las 07:00 Bogotá.\n')
change(REPO/'registro/semana2_listo_entrenar.json',lambda raw:top(raw,'latest_coverage_exposure_audit',{'utc':NOW,'index':rel(INDEX),'documentation':i['documentation'],'new_fits':0,'new_scores':0,
    'home_hard_mask_compatible_with_T0':False,'all_claims_preserved':True,'reference':'W2-B00','ledger_read':False,'confirmation_opened_by_this_task':False,'complete_blindness_claim_allowed':False},add=True))
tests=REPO/'registro/semana2_coberturas_peril2023_pruebas_v1.json'
dump(tests,{'author':'Codex','utc':NOW,'producer':i['report'],'verification':i['verification'],'readout_reconciliation':i['readout_reconciliation'],
    'expected_failure_runs':v['expected_failure_runs'],'home_mask_hypothesis_rejected_despite_technical_controls_passing':True,'professional_independent_validation':False})
dump(RUN/'forum_receipts.json',{'source':'Serialized helper outputs in this chat','receipts':[
    {'id':'COD-S2-20261024-032','utc':'2026-10-24T01:19:28+00:00','previous_sha256':'7aaa8dc1ae052d8e2f102e2568d0baa32848cf85cf36f34c1a60f232d5f4130c','sha256_at_append':'4815214c9c0cff620437703124f05f55f31338425c2269d49adfcac74857fa0e'},
    {'id':'COD-S2-20261024-033','utc':'2026-10-24T01:23:21+00:00','previous_sha256':'4815214c9c0cff620437703124f05f55f31338425c2269d49adfcac74857fa0e','sha256_at_append':'09fad812e1592da76164c629e6401951600f78aeff226a151b039bb9eeeefb57'}]})
dump(RUN/'registration.json',{'author':'Codex','utc':NOW,'changes':changes,'indices_and_counters_preserved':preserved,'no_new_fits_scores_bootstrap':True,'ledger_read':False,'confirmation_opened_by_this_task':False})
checks=[]
def check(n,x):checks.append({'name':n,'pass':bool(x)})
for name in ['report','verification','readout','readout_reconciliation','assessment','decision_journal','manifest','dictionary_scope_evidence']:check('Index receipt '+name,sha(ROOT/i[name]['path'])==i[name]['sha256'])
check('Documentation exact',sha(ROOT/i['documentation'])==i['documentation_sha256'])
for name,expected in preserved.items():check('Preserved exact '+name,sha(ROOT/name)==expected)
for source in p['frozen_sources']:check('Frozen source '+source['path'],sha(ROOT/source['path'])==source['sha256'])
for item in read(RUN/'manifest.json')['files']:check('Producer artifact '+item['path'],sha(RUN/item['path'])==item['sha256'])
oldstate=read(BACK/'Preparación/ESTADO_PROYECTO.json');newstate=read(ROOT/'Preparación/ESTADO_PROYECTO.json')
check('Historical state exact',all(newstate.get(k)==x for k,x in oldstate.items() if k not in ['current_phase','memory_as_of','collaboration_forum','week_2_nocturnal_continuation_20261023']))
oldroutes=read(BACK/'RUTAS_PROYECTO.json');newroutes=read(ROOT/'RUTAS_PROYECTO.json');check('Old routes exact',all(newroutes.get(k)==x for k,x in oldroutes.items()))
for key,value in newroutes.items():
    if key.startswith('week_2_'):check('Route '+key,(ROOT/value).exists())
for item in changes:
    if item['path'].endswith('.md'):check('Prose prefix '+item['path'],(ROOT/item['path']).read_bytes().startswith((ROOT/item['backup']).read_bytes()))
for doc in [ROOT/i['documentation'],REPO/'docs/semana2/BALANCE_NOCTURNO_PARCIAL_20261024.md',REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md']:
    for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        target=link.strip('<>').split('#')[0]
        if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',target):continue
        check('Link '+rel(doc)+' -> '+target,(doc.parent/unquote(target)).resolve().exists())
n=read(NIGHT);oldn=read(BACK/NIGHT.relative_to(ROOT))
check('Eighth unit complete',n['current_unit'] is None and n['latest_completed_unit']['id']==p['id'] and len(n['completed_units'])==8)
check('Native schedule exact',all(n[k]==oldn[k] for k in ['window_start','window_end','frequency','automation_id','automation_kind','automation_target_thread','same_chat','other_automations_changed']))
check('Safe reader/exposure guard exact',n['forum_reading_guard']==oldn['forum_reading_guard'] and n['confirmation_header_exposure']==oldn['confirmation_header_exposure'])
check('Own scope2024closed',n['confirmation_2024_open'] is False and newstate[statekey]['ledger_read'] is False)
check('Forum prefix exact',forum.read_bytes().startswith(cut))
result={'utc':NOW,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'scope':'Closing sources, indices, links and counters only; no statistical suite repeated'}
dump(RUN/'closure_verification.json',result);assert result['failed']==0,[x for x in checks if not x['pass']]
paths={x for x in RUN.rglob('*') if x.is_file()};paths.update(ROOT/x['path'] for x in changes)
paths.update([INDEX,tests,ROOT/i['documentation'],ROOT/i['plan'],ROOT/p['code'],Path(__file__),forum])
paths.update(REPO/'herramientas'/filename for filename in ['verificar_coberturas_peril2023_semana2.py','documentar_coberturas_peril2023_semana2.py'])
paths.update(ROOT/'Hackaton/Semana 2/Codex'/filename for filename in ['preinscribir_coberturas_peril2023.py','coberturas_peril2023_preinscripcion.md','coberturas_peril2023_resultado.md','nocturno_antes_coberturas_peril2023.json'])
for path in v['expected_failure_runs']:paths.update(x for x in (ROOT/path).rglob('*') if x.is_file())
dump(RUN/'closure_manifest.json',{'utc':NOW,'notice':'Dated cut; shared files can change later without rewriting this receipt.','files':[{'path':rel(x),'sha256':sha(x),'bytes':x.stat().st_size} for x in sorted(paths)],'no_new_fits_scores_bootstrap':True,'reference':'W2-B00'})
print(json.dumps({'registered':rel(INDEX),'closure_checks':result['passed'],'failed':0,'night_units':8,'price_counters_unchanged':[165,285],'home_mask_rejected':True,'no_new_fit_score_bootstrap':True}))
