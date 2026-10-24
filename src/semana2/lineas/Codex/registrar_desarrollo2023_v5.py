"""Registra el ciclo estándar y la continuidad nocturna sin reescribir historia."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import unquote
import json,hashlib,os,re
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026';RUN=REPO/'privado/semana2/desarrollo2023/dev5_20261023T232328Z_69df9ead'
ACTIVE=REPO/'registro/semana2_desarrollo2023_actual.json';SNAP=REPO/'registro/semana2_desarrollo2023_v4_snapshot.json';NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
NOW=datetime.now(timezone.utc).isoformat();BACK=RUN/'state_before_registration';BACK.mkdir(exist_ok=False)
def dump(p,obj):
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def top(raw,key,value,add=False):
    value=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if add:
        assert key not in json.loads(raw),key;return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+value+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+value+raw[m.end()+end:]
changes=[]
def change(path,fn):
    before=path.read_bytes();backup=BACK/path.relative_to(ROOT);backup.parent.mkdir(parents=True,exist_ok=True)
    with backup.open('xb') as f:f.write(before)
    after=fn(before.decode('utf-8-sig')).encode('utf-8');tmp=path.with_name(path.name+'.s2dev5.tmp')
    assert path.read_bytes()==before,'Concurrencia '+str(path)
    with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before,'Concurrencia '+str(path);os.replace(tmp,path)
    changes.append({'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path),'backup':rel(backup)})
index=read(RUN/'active_index_proposed.json');report=read(RUN/'report.json');plan=read(RUN/'plan_snapshot.json')
assert ACTIVE.read_bytes()==SNAP.read_bytes(),'Conciliar índice concurrente'
for key in ['verification','fixtures']:assert read(ROOT/index[key]['path'])['failed']==0
selectorpath=REPO/'registro/semana2_seleccion_actual.json';selector=read(selectorpath);assert not (ROOT/selector['ledger_workspace_relative']).exists()
assert sha(ROOT/selector['policy']['path'])==plan['selection_policy_sha256'];(RUN/'selector_index_at_close.json').write_bytes(selectorpath.read_bytes())
forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';cut=forum.read_bytes();assert cut.count(b'<!-- aporte:COD-S2-20261023-017 -->')==1
change(ACTIVE,lambda raw:(RUN/'active_index_proposed.json').read_text(encoding='utf-8'))
def night(raw):
    obj=json.loads(raw);obj.update(status='scheduled_first_unit_verified',updated_utc=NOW,latest_completed_unit={'id':plan['id'],'run':rel(RUN),'documentation':index['documentation'],
      'decision_journal':index['decision_journal'],'verification':index['verification'],'fixtures':index['fixtures'],'forum_result':'COD-S2-20261023-017'},
      current_unit=None,next_unit='Audit CLA003 capital/credibility scope and temporal weather availability before a new integration recipe',
      no_retraining_or_suite_repetition_for_completed_v5=True,method_priority='Standard models first; added complexity requires a documented residual failure and a preregistered test')
    obj['queue']=obj['queue'][1:];return json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
change(NIGHT,night)
def routes(raw):
    for key,val in [('week_2_development_report',index['documentation']),('week_2_development_plan',index['plan']),('week_2_development_oof',index['oof'])]:raw=top(raw,key,val)
    for key,val in [('week_2_development_v4_snapshot',rel(SNAP)),('week_2_night_plan','Hackaton/Repositorio_IAA2026/docs/semana2/PLAN_NOCTURNO_20261023.md'),('week_2_night_index',rel(NIGHT))]:raw=top(raw,key,val,True)
    return raw
def state(raw):
    obj=json.loads(raw);phase={'as_of_utc':NOW,'phase':'week2_standard_models_verified_hourly_overnight_continuation_B00_retained_2024_closed','current_state_key':'week_2_development2023_v5_20261023',
      'historical_fields_notice':'Cortes anteriores preservados; cinco tandas de desarrollo y continuidad nocturna separada.'}
    dev={'as_of_utc':NOW,'path_base':'workspace_root','index':rel(ACTIVE),'run':rel(RUN),'documentation':index['documentation'],'training_years':[2023],'scored_years':[2023],
      'rows_per_recipe':50094,'groups':30869,'folds':5,'new_base_estimator_fits':15,'new_closed_form_constants':30,'new_postfit_factors':0,'cumulative_base_estimator_fits':80,'cumulative_closed_form_constants':60,
      'models_consulted':index['models_consulted'],'results_D2':{r['model_id']:r['D2'] for r in report['summary']},'reference_retained':'W2-B00','alternatives_preserved':index['alternatives_preserved'],
      'promotion':False,'confirmation_2024_open':False,'confirmation_closed_by_current_user_instruction':True,'final_confirmation_roster_frozen':False,
      'verification':index['verification'],'fixtures':index['fixtures'],'decision_journal':index['decision_journal'],'forum_decisions':['COD-S2-20261023-016','COD-S2-20261023-017'],
      'pending':['Uncertain advantages and top31 influence; no extra complexity justified by point scores','Future source-table integrations need separate availability/fold checks','T0/C0 and ultimate/reserve assumptions and human review remain pending'],
      'professional_independent_validation':False,'no_remote_training':True,'no_submissions':True,'no_delegation':True}
    continuation={'as_of_utc':NOW,'authorization_literal':plan['authorization_literal'],'plan':'Hackaton/Repositorio_IAA2026/docs/semana2/PLAN_NOCTURNO_20261023.md','index':rel(NIGHT),
      'automation_id':'iaa-semana-2-modelos-est-ndar-y-validaci-n-nocturna','kind':'heartbeat','same_chat':True,'status_verified':'ACTIVE','frequency':'hourly_at_minute_zero',
      'timezone':'America/Bogota','window_start':'2026-10-23T19:00:00-05:00','window_end':'2026-10-24T07:00:00-05:00',
      'standard_models_first':True,'added_complexity_requires_documented_need':True,'each_decision_has_evidence_and_consequence':True,'repeat_unchanged_training_or_suites':False,
      'latest_completed_unit':plan['id'],'next_unit':read(NIGHT)['next_unit'],'other_automations_changed':False,'confirmation_2024_open':False,'delegation_authorized':False,
      'scope':'Local 2023 development and validation only; future scheduled work not yet executed; no professional independence claim'}
    collab=dict(obj['collaboration_forum'],updated_utc=NOW,latest_Codex_comment='COD-S2-20261023-017',Claude_response_observed_in_week2=True)
    entries=re.findall(rb'^## Codex \| ([^|]+) \| ([^|]+) \|',cut,re.M)
    if entries:collab['latest_Codex_comment']=entries[-1][0].decode().strip()
    for key,val in [('memory_as_of',datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()),('current_phase',phase),('collaboration_forum',collab)]:raw=top(raw,key,val)
    raw=top(raw,'week_2_development2023_v5_20261023',dev,True);return top(raw,'week_2_nocturnal_continuation_20261023',continuation,True)
note='''

## Continuidad nocturna y modelos estándar, 23 de octubre

Codex. Nueva instrucción directa: continuar validación exhaustiva y avances toda la noche, validar cada decisión, modelos estándar primero y complejidad solo cuando sea necesaria. Se programó la automatización nativa heartbeat iaa-semana-2-modelos-est-ndar-y-validaci-n-nocturna en este chat, ACTIVE verificado, cada hora de19:00del23oct a07:00del24oct America/Bogota, con término24oct12:00UTC. Las otras tres automatizaciones no se modificaron. La ejecución local requiere equipo/aplicación disponibles; programación no demuestra ejecuciones futuras. Plan docs/semana2/PLAN_NOCTURNO_20261023.md e índice registro/semana2_continuidad_nocturna.json. No se autoriza delegar o modificar otros encargos.

Primera unidad manual ya concluida antes de la ventana: receta v5 preinscrita COD-S2-20261023-016 a23:22:33UTC, corrida dev5_20261023T232328Z_69df9ead. B12 usa constante Tweedie por ramo y nuevo negocio/renovación, solo ajuste, treinta constantes. B13 es GLM Tweedie1,5 log alpha0 con seis predictores técnicos principales por ramo, sin interacciones; quince GLM. Mediana/escalado/OHE dropfirst min50 max40 fit-only. Se conservaron T0/C0,50.094periodos2023,30.869componentes,cincofolds y B00–B11 exactos, capital enmascarado y ausencia de clima/transferencia. Sin nuevos factores/mezclas a posteriori; acumulado80estimadoresbase y60constantes. Recetas anteriores y estrés conservan linaje.

D² B12=0,07491526, predicho15,3675millonesCU, A/E0,99542; B13=0,08671171, predicho15,4303millonesCU, A/E0,99137. Observado15,2971millones. B12/B00 delta+0,00633358 intervalo exploratorio95%[−0,00205137;0,01842741], retiro31gruposfavorables−0,00739236. B13/B12 +0,01179644 [−0,00970450;0,03170111], retiro−0,01285602. B13/B00 +0,01813002 [−0,00620476;0,04265764], retiro−0,01250786. Son91parejas de14recetas adaptativas,2.000sorteoscomunes sin corrección de búsqueda o multiplicidad. No promoción, retiro o equivalencia.

B13 mejora puntos de los tres ramos respecto de B12. Nuevo negocio agregado B12/B13 D²0,09220/0,11119, A/E0,90592/0,90590; renovación B13 D²0,08293/A-E1,00186. Edificios global A/E1,00048 no resuelve pérdida de edificios nuevos frenteB00: D²0,05022vs0,06523. Autos nuevos B13 D²−0,01004/A-E0,87904 y contenidos nuevos0,15363/1,18353 conservan problemas de nivel/forma. No se concluye que hagan falta modelos más complejos.

Pasaron22casosfocales y712controlesseparados, con solapamiento. Gradiente total-unit independiente y diferencias finitas, constantes por suma compensada/óptimo, fuentes/particiones/guardas2023, transformaciones de ajuste, replay con fit bloqueado, invariancia a respuestas, métricas/segmentos/escenarios y25contrastes nuevos reconstruidos. Las parejas anteriores se conservan por OOF/utilidad/sorteos exactos, sin repetir suites históricas. Máximo gradiente4,843e-6, umbral técnico1e-4 fijado en fuente antes del ajuste. Comprobación propia de Codex, no validación profesional independiente o aprobación humana. Consulta duplicada a una sesión de herramienta ya terminada devolvió ID desconocido; no se reentrenó o repitió prueba, se recuperaron los recibos terminados.

Resultado COD-S2-20261023-017 e informe docs/semana2/DESARROLLO_2023_MODELOS_ESTANDAR.md. Se añade registro de decisiones por ciclo con hipótesis/criterio/fuente/comprobación/consecuencia, decisión_journal.json. Las fuentes idénticas no provocarán repetición rutinaria de entrenamiento/suites; se revisa lo cambiado y lo pendiente mediante pruebas pertinentes. Índice actual y snapshot exacto v4 conservan cinco tandas; histórico de preparación y campos anteriores mantienen sus cortes.

Se recibió CLA-S2-20261023-003 con decisiones humanas referidas sobre capital/clima/credibilidad/gasto fijo y evidencia de Claude. Próxima unidad: cotejar esas tablas y ámbitos de ajuste/tiempo antes de integrar otra receta. Clima2024 en filas2023 no es información prospectiva alinicio2023; factores de todo2023/OOF no validan esos mismos folds. Se conserva autoría, no se trata el aporte como nueva orden de otro chat o cierre ya comprobado. Los datos/objetivos/F0 actuales no se cambiaron silenciosamente.

B00 continúa referencia y B01–B13 alternativas. 2024 permanece cerrado por instrucción vigente independientemente del selector; no ledger, entrenamiento de precios, scores/predicciones2024 o test, envíos, remoto, publicación externa o delegación. No se congeló lista final. Los supuestos del último/reservas/reporte y revisión humana siguen pendientes. Avance horario con trabajo terminado, resultado/fallo y siguiente paso; balance al finalizar07:00Bogotá. Ninguna garantía de validación futura o de rendimiento competitivo se infiere de la programación.
'''
change(ROOT/'RUTAS_PROYECTO.json',routes);change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+note)
update='\n\n## Continuidad nocturna y referencias estándar\n\nEl [plan nocturno](../Repositorio_IAA2026/docs/semana2/PLAN_NOCTURNO_20261023.md) continúa este chat cada hora de19:00 a07:00Bogotá. La [primera unidad](../Repositorio_IAA2026/docs/semana2/DESARROLLO_2023_MODELOS_ESTANDAR.md) prueba B12 por negocio y un GLM B13 de seis variables por ramo. Pasaron22casos y712controles propios; sus ventajas siguen inciertas e influidas por grupos. Se conserva B00 y B01–B13, sin promoción;2024 permanece cerrado. El [índice de continuidad](../Repositorio_IAA2026/registro/semana2_continuidad_nocturna.json) identifica lo terminado y el siguiente paso.\n'
for name in ['README.md','PLAN_TRABAJO.md']:change(ROOT/'Hackaton/Semana 2'/name,lambda raw:raw+update)
change(REPO/'docs/semana2/DESARROLLO_2023_ESTABILIDAD_NEGOCIO.md',lambda raw:raw+'\n\n## Corte posterior: modelos estándar y continuidad nocturna\n\nLa [quinta prueba](DESARROLLO_2023_MODELOS_ESTANDAR.md) añade referencias estándar B12/B13 con receta previa, sin modificar esta tanda. Su [snapshot de índice v4](../../registro/semana2_desarrollo2023_v4_snapshot.json) conserva exactamente este corte. La continuación nocturna tiene índice separado.\n')
change(REPO/'registro/semana2_listo_entrenar.json',lambda raw:top(raw,'latest_development_execution',{'as_of_utc':NOW,'index':rel(ACTIVE),'documentation':index['documentation'],'training_years':[2023],
 'status':'five_2023_trials_verified_standard_models_first','confirmation_2024_open':False,'confirmation_closed_by_current_user_instruction':True,'night_index':rel(NIGHT),
 'historical_counter_notice':'Los contadores de preparación mantienen su corte; índice de desarrollo conserva ejecuciones actuales.'}))
dump(REPO/'registro/semana2_desarrollo2023_pruebas_v5.json',{'utc':NOW,'author':'Codex','verification':index['verification'],'fixtures':index['fixtures'],'professional_independent_validation':False})
dump(RUN/'registration.json',{'utc':NOW,'changes':changes,'reference':'W2-B00','confirmation_2024_open':False})
dump(RUN/'forum_preregistration_receipt.json',{'source':'Native serialized helper response in this task','id':'COD-S2-20261023-016','utc':'2026-10-23T23:22:33+00:00',
 'previous_sha256':'cc7fd47f673ce066d20c25a740dc0f4f1cff3c2aca030a63ca5322cb66966540','sha256_at_append':'16fe06edc45fd149f131e74e8ee5e7468edbdadb54be1048a0d1dc9502019b82'})
dump(RUN/'forum_result_receipt.json',{'source':'Native serialized helper response in this task','id':'COD-S2-20261023-017','utc':'2026-10-23T23:30:09+00:00',
 'previous_sha256':'16fe06edc45fd149f131e74e8ee5e7468edbdadb54be1048a0d1dc9502019b82','sha256_at_append':'7f32726fb71914ba282d230611001c0c86bbaab24ecbb5f71b6c409f9eee84a2'})
checks=[]
def check(n,v):checks.append({'name':n,'pass':bool(v)})
for key in ['report','plan','producer','oof','manifest','assessment','decision_journal']:check('Index '+key,sha(ROOT/index[key])==index[key+'_sha256'])
for key in ['verification','fixtures']:check('Verification '+key,sha(ROOT/index[key]['path'])==index[key]['sha256'] and read(ROOT/index[key]['path'])['failed']==0)
check('V4 exact snapshot',SNAP.read_bytes()==(BACK/'Hackaton/Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json').read_bytes())
oldstate=read(BACK/'Preparación/ESTADO_PROYECTO.json');newstate=read(ROOT/'Preparación/ESTADO_PROYECTO.json')
check('Historical state branches',all(newstate.get(k)==v for k,v in oldstate.items() if k not in ['memory_as_of','current_phase','collaboration_forum']))
oldroutes=read(BACK/'RUTAS_PROYECTO.json');newroutes=read(ROOT/'RUTAS_PROYECTO.json')
check('Other routes',all(newroutes.get(k)==v for k,v in oldroutes.items() if k not in ['week_2_development_report','week_2_development_plan','week_2_development_oof']))
for key,val in newroutes.items():
    if key.startswith('week_2_'):check('Route '+key,(ROOT/val).exists())
for it in changes:
    if it['path'].endswith('.md'):check('Preserved prose '+it['path'],(ROOT/it['path']).read_bytes().startswith((ROOT/it['backup']).read_bytes()))
docs=[ROOT/index['documentation'],REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',REPO/'docs/semana2/DESARROLLO_2023_ESTABILIDAD_NEGOCIO.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md',forum]
for doc in docs:
    for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        target=link.strip('<>').split('#')[0]
        if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',target):continue
        check('Link '+rel(doc)+' -> '+target,(doc.parent/unquote(target)).resolve().exists())
for it in read(RUN/'frozen_sources_before_fit.json')['files']:check('Source unchanged '+it['path'],sha(ROOT/it['path'])==it['sha256'])
for num in ['016','017']:check('Forum unique '+num,forum.read_bytes().count(('<!-- aporte:COD-S2-20261023-'+num+' -->').encode())==1)
check('B00 all thirteen alternatives',index['reference']=='W2-B00' and len(index['alternatives_preserved'])==13 and not index['promotion'])
check('Night completed unit',read(NIGHT)['current_unit'] is None and read(NIGHT)['latest_completed_unit']['id']==plan['id'])
check('2024 still closed',not (ROOT/selector['ledger_workspace_relative']).exists())
result={'utc':NOW,'scope':'Post-registration integrity, no repeated statistical tests/fits','passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks}
dump(RUN/'closure_verification.json',result);assert result['failed']==0,[x for x in checks if not x['pass']]
files={p for p in RUN.rglob('*') if p.is_file()};files.update(ROOT/x['path'] for x in changes)
files.update([ROOT/index['documentation'],ROOT/index['plan'],ROOT/index['producer'],SNAP,Path(__file__),forum,REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',REPO/'registro/semana2_desarrollo2023_pruebas_v5.json'])
files.update(REPO/'herramientas'/f'{name}_desarrollo2023_v5_semana2.py' for name in ['documentar','probar','verificar'])
files.update(ROOT/'Hackaton/Semana 2/Codex'/name for name in ['preinscribir_desarrollo2023_v5.py','desarrollo2023_v5_preinscripcion.md','desarrollo2023_v5_resultado.md'])
dump(RUN/'closure_manifest.json',{'utc':NOW,'notice':'Corte de cierre. Archivos compartidos pueden cambiar después; no confundir versiones históricas con el estado activo.',
 'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)],'reference':'W2-B00','confirmation_2024_open':False})
print(json.dumps({'registered':rel(ACTIVE),'integrity_checks':result['passed'],'failed':0,'night_index':rel(NIGHT),'reference':'W2-B00','confirmation_2024_open':False}))
