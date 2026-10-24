"""Registro común con respaldo, conservación de ramas y cierre incremental."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import unquote
import json,hashlib,os,re
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026';RUN=REPO/'privado/semana2/desarrollo2023/dev7_20261023T235935Z_55507793'
ACTIVE=REPO/'registro/semana2_desarrollo2023_actual.json';SNAP=REPO/'registro/semana2_desarrollo2023_v6_snapshot.json';NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
NOW=datetime.now(timezone.utc).isoformat();BACK=RUN/'state_before_registration';BACK.mkdir(exist_ok=False);changes=[]
def dump(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
def top(raw,key,value,add=False):
    val=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if add:
        assert key not in json.loads(raw),key;return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+val+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+val+raw[m.end()+end:]
def change(path,fn):
    before=path.read_bytes();backup=BACK/path.relative_to(ROOT);backup.parent.mkdir(parents=True,exist_ok=True)
    with backup.open('xb') as f:f.write(before)
    after=fn(before.decode('utf-8-sig')).encode('utf-8');tmp=path.with_name(path.name+'.dev7.tmp');assert path.read_bytes()==before,'Concurrencia '+str(path)
    with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before,'Concurrencia '+str(path);os.replace(tmp,path)
    changes.append({'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path),'backup':rel(backup)})
index=read(RUN/'active_index_proposed.json');report=read(RUN/'report.json');plan=read(RUN/'plan_snapshot.json');assessment=read(RUN/'assessment.json')
assert read(ACTIVE)['id']=='S2-DEV2023-v6-20261023' and sha(ACTIVE)==index['history'][-2]['index_sha256'],'Índice concurrente'
for key in ['verification','fixtures','motor_reconciliation']:assert read(ROOT/index[key]['path'])['failed']==0
selectorpath=REPO/'registro/semana2_seleccion_actual.json';selector=read(selectorpath);assert not (ROOT/selector['ledger_workspace_relative']).exists()
assert sha(ROOT/plan['selection_policy'])==plan['selection_policy_sha256'];(RUN/'selector_index_at_close.json').write_bytes(selectorpath.read_bytes())
forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';cut=forum.read_bytes()
for ident in [plan['forum_preregistration'],index['forum_result']]:assert cut.count(('<!-- aporte:'+ident+' -->').encode())==1
with SNAP.open('xb') as f:f.write(ACTIVE.read_bytes())
change(ACTIVE,lambda raw:(RUN/'active_index_proposed.json').read_text(encoding='utf-8'))
def night(raw):
    obj=json.loads(raw);assert obj['current_unit']['id']==plan['id'],'Unidad concurrente'
    entry={'id':plan['id'],'run':rel(RUN),'documentation':index['documentation'],'decision_journal':index['decision_journal'],'verification':index['verification'],'fixtures':index['fixtures'],'forum_result':index['forum_result']}
    history=obj.get('completed_units',[obj['latest_completed_unit']]);assert plan['id'] not in [x['id'] for x in history]
    obj.update(status='scheduled_three_units_verified_conditions_open',updated_utc=NOW,latest_completed_unit=entry,completed_units=history+[entry],current_unit=None,
      next_unit='Review2023 level/tail and common C0 late-report/reserve observation-link sensitivity with standard models. Preregister any new fit. Do not retune credibility c from these scores.',
      queue=['Review common2023 level/tail and reporting/reserve linkage with a prespecified standard-model test','Keep capital economic unit and joint support, climate timing, and prior/objective uncertainty open','Verify only new code/consumer evidence and prepare morning balance'],
      integration_decisions={'capital':'56-row representation/refit decomposition verified; no economic scale proof; B13/B14 retained without new score-driven capital rule',
        'climate':'Not admitted prospectively; availability conditions unchanged','credibility':'B15 and motor-only B16/B17/B18 conditional alternatives; none establishes improvement over B14; no optimized weight'},
      open_conditions=assessment['warnings'],no_retraining_or_suite_repetition_for_completed_v7=True)
    return json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
change(NIGHT,night)
def routes(raw):
    for key,value in [('week_2_development_report',index['documentation']),('week_2_development_plan',index['plan']),('week_2_development_oof',index['oof'])]:raw=top(raw,key,value)
    return top(raw,'week_2_development_v6_snapshot',rel(SNAP),True)
def state(raw):
    obj=json.loads(raw);key='week_2_development2023_v7_20261024'
    phase={'as_of_utc':NOW,'phase':'week2_capital_rows_motor_credibility_ablation_verified_B00_retained_2024_closed','current_state_key':key,
      'historical_fields_notice':'Seven exploratory2023 waves; prior six cuts and exact index snapshots preserved. Current forum comments and UTC timestamps govern chronology.'}
    dev={'as_of_utc':NOW,'path_base':'workspace_root','index':rel(ACTIVE),'run':rel(RUN),'documentation':index['documentation'],'training_years':[2023],'scored_years':[2023],
      'rows_per_recipe':50094,'groups':30869,'folds':5,'new_price_base_fits':0,'new_auxiliary_fits':0,'new_calibrated_factors':0,'new_motor_algebraic_factors':15,'exact_home_reuses':30,
      'cumulative_price_base_fits':90,'cumulative_closed_form_constants':60,'auxiliary_fits_v6_reused':30,'models_consulted':index['models_consulted'],
      'results_D2':{x['model_id']:x['D2'] for x in report['summary']},'capital_row_review':index['capital_row_diagnostic'],'global_F0_changed':False,'climate_prospective_admitted':False,
      'credibility_default_adopted':False,'reference_retained':'W2-B00','alternatives_preserved':index['alternatives_preserved'],'promotion':False,'confirmation_2024_open':False,
      'confirmation_closed_by_current_user_instruction':True,'final_confirmation_roster_frozen':False,'verification':index['verification'],'fixtures':index['fixtures'],
      'motor_reconciliation':index['motor_reconciliation'],'decision_journal':index['decision_journal'],'forum_decisions':[plan['forum_preregistration'],index['forum_result']],
      'pending':[x['effect'] for x in assessment['warnings']],'professional_independent_validation':False,'no_remote_training':True,'no_submissions':True,'no_delegation':True}
    collab=dict(obj['collaboration_forum'],updated_utc=NOW);headers=re.findall(rb'^## Codex \| ([^|]+) \| ([^|]+) \|',cut,re.M)
    if headers:collab['latest_Codex_comment']=headers[-1][0].decode().strip()
    continuity=dict(obj['week_2_nocturnal_continuation_20261023'],as_of_utc=NOW,latest_completed_unit=plan['id'],next_unit=read(NIGHT)['next_unit'])
    for k,v in [('memory_as_of',datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()),('current_phase',phase),('collaboration_forum',collab),('week_2_nocturnal_continuation_20261023',continuity)]:raw=top(raw,k,v)
    return top(raw,key,dev,True)
note=f'''

## Capital por fila y credibilidad en autos nuevos: séptima prueba solo 2023

Codex, corte UTC {NOW}. Instrucción directa del participante: revisar capital por fila y deterioro de credibilidad en autos nuevos, registrar la prueba antes de calcular resultados con modelos estándar, conservar B00, registrar en foro y mantener 2024 cerrado. Revisión congelada revision_filas_20261023T235757Z_cafaba7d, sin fit. Preinscripción COD-S2-20261024-020 a2026-10-23T23:59:26UTC; ejecución dev7_20261023T235935Z_55507793; resultado COD-S2-20261024-021 a2026-10-24T00:03:21UTC. Los IDs de la tanda anticipan el día UTC de su cierre; los recibos conservan horas reales. Planv7 e informe docs/semana2/CAPITAL_POR_FILA_Y_AUTOS_NUEVOS_2023.md. Seis snapshots de índice y siete cortes preservados.

Capital:56filas2023 con T0=0,26edificios/30contenidos, conservan detalle privado de bruto/dividido/imputado, fold y tasas. Contrafactual B13 congelado sobre capital corregido separa representación del reajuste B14: identidad log(r_corregida/r_imputada)=beta_cap·(logcap−mediana) conciliada. Los56valores están dentro del soporte univariante normal del ajuste; no prueba soporte conjunto o unidad económica. El cambio final−62,36% a+154,09% lo explica casi totalmente sustituir el imputado, con reajuste residual absoluto máximo0,001568/0,002712 en log. Se conserva CAPS2-01 con procedencia/condiciones y B13/B14, sin ajustar capital por score, editar F0 global u originales. Prima escrita sigue solo auditoría, no predictor.

Autos nuevos:2.620filas/265positivas. B15/B14 aumenta pérdida34.727,49 en positivas y baja27.119,35 en2.355ceros, saldo+7.608,15; fold0+8.637,79. Cinco grupos más perjudicados+18.085,65 con compensaciones externas, no proporción acotada o regla de eliminación. Corrector frecuencia0,932–0,977 y severidad0,713–0,803. Theta de precio0,714–0,911 difiere del auxiliar0,395–0,531. Multiplicar c no sustituye por theta_creíble; distinto objetivo/observación no prueba error o causalidad única.

Tres ablaciones previas de GLM estándar, partiendo B14 y cambiando solo autos nuevos: B16frecuencia sola,B17severidad sola,B18sustitución de coeficiente bruto exp(theta_creíble−theta_precio), intercepto original y renovaciones exactos. Hogar exacto; B15global contiene también cambios de hogar y no aísla autos frente a estas variantes. D²global B14=0,08671008,B15=0,08606099,B16=0,08655140,B17=0,08574992,B18=0,08189631. Autos nuevos D² B14−0,01004489,B15−0,03324409,B16−0,01272589,B17−0,02626742,B18−0,09137649; A/E0,879/1,223/0,919/1,170/1,752. B16acercaA/E a1 pero empeoraD². Ninguna corrección acredita mejora; la sustitución empeora más, no confirma una reparación. No se elige un cuarto peso.

Contrastesglobales B16/B14delta−0,00015868 intervalo95%[−0,00092851;+0,00030689],retiro31−0,00019211; B17/B14−0,00096016[−0,00437606;+0,00154672],retiro−0,00111190; B18/B14−0,00481377[−0,01341707;+0,00158824],retiro−0,00513303. Todos intervalos cruzan cero; no superioridad/equivalencia/retiro.19recetasadaptativas/171comparaciones exploratorias sin corregir búsqueda/multiplicidad;120parejas/16OOF previas exactas, solo51parejas nuevas con2.000sorteos comunes.50.094periodos/30.869componentes/5folds2023, mismoT0/C0.

Cero nuevos ajustes de precio, auxiliares o calibración. Quince factores algebraicos y treinta copias nativas hogar;90ajustes de precio y60constantes históricos intactos. Treinta auxiliaresv6 se reutilizan sin fit, no se suman otra vez. Pasaron31adversos focales,622controles separados y18conciliaciones incrementales (solapados). Se bloquea fit; comprobador no importa productor y usa exp(Xbeta), devianza general/scikit-learn, remuestreo con multiplicidades/producto matricial y51parejas/influencia. Se verifica la representación de escala, coste/identificador envenenado no cambia precio y rechazo2024/test/clavesduplicadas/ramo/fold/negocio inválidos. Revisión técnica propia, no profesional independiente.

Prior desarrollado2021–2023 recibido de Claude y estacionalidad no reproducidos desde raw aquí; incertidumbre omitida enZ, tau correlacionado y distinta observación siguen condicionados. No backtest prospectivo al inicio2023. Capital unidad/soporteconjunto, clima temporal, reporte/reservas/último/negociotransferido abiertos, sin cerrar hallazgos ajenos. B00 yB01–B18 preservados sin promoción/listafinal. Tercera unidad nocturna terminada; próxima nivel/cola y C0 solo2023 con receta previa, sin retocar c a estos scores. Frecuencia/ventana nativa y otras automatizaciones intactas.2024cerrado explícitamente, ledger ausente; sinprecios/predicciones/scores deeseaño otest, envíos, remoto, publicaciónexterna o delegación.
'''
change(ROOT/'RUTAS_PROYECTO.json',routes);change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+note)
update='\n\n## Capital por fila y autos nuevos\n\nLa [séptima prueba solo2023](../Repositorio_IAA2026/docs/semana2/CAPITAL_POR_FILA_Y_AUTOS_NUEVOS_2023.md) separa el efecto del capital propio frente al imputado y prueba frecuencia, severidad y sustitución del coeficiente de negocio con GLM congelados. Ninguna corrección de autos acredita mejora. Se mantienen B00 yB01–B18, capital condicionado y2024cerrado; cero nuevos ajustes. La continuidad nocturna retoma nivel/cola/C0 con receta previa.\n'
for name in ['README.md','PLAN_TRABAJO.md']:change(ROOT/'Hackaton/Semana 2'/name,lambda raw:raw+update)
change(REPO/'docs/semana2/CAPITAL_CLIMA_CREDIBILIDAD_2023.md',lambda raw:raw+'\n\n## Corte posterior: explicación por fila y ablaciones de autos nuevos\n\nLa [séptima prueba](CAPITAL_POR_FILA_Y_AUTOS_NUEVOS_2023.md) conserva este corte y separa representación/refit del capital y componentes de credibilidad. El [snapshot v6](../../registro/semana2_desarrollo2023_v6_snapshot.json) conserva exactamente este índice; el índice activo recoge el avance.\n')
change(REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',lambda raw:raw+'\n\n## Tercera unidad terminada: capital por fila y autos nuevos\n\nLa [revisión y prueba registrada](CAPITAL_POR_FILA_Y_AUTOS_NUEVOS_2023.md) usa GLM congelados sin nuevos ajustes; las tres correcciones de autos nuevos no acreditan mejora. Se conserva B00 y toda alternativa, capital condicionado y2024cerrado. Próxima unidad: nivel/cola y vínculoC0 con receta previa2023; no retocar c con estos scores. La frecuencia, ventana y automatización existentes permanecen.\n')
change(REPO/'registro/semana2_listo_entrenar.json',lambda raw:top(raw,'latest_development_execution',{'as_of_utc':NOW,'index':rel(ACTIVE),'documentation':index['documentation'],'training_years':[2023],
 'status':'seven_2023_trials_verified_capital_rows_motor_credibility_conditions_open','confirmation_2024_open':False,'confirmation_closed_by_current_user_instruction':True,
 'night_index':rel(NIGHT),'historical_counter_notice':'Contadores de preparación conservan su corte; v7 no añade ajustes, solo factores algebraicos y reusos.'}))
dump(REPO/'registro/semana2_desarrollo2023_pruebas_v7.json',{'utc':NOW,'author':'Codex','verification':index['verification'],'fixtures':index['fixtures'],'motor_reconciliation':index['motor_reconciliation'],'professional_independent_validation':False})
dump(RUN/'registration.json',{'utc':NOW,'changes':changes,'reference':'W2-B00','confirmation_2024_open':False})
dump(RUN/'forum_receipts.json',{'source':'Serialized helper responses in this chat','receipts':[
 {'id':'COD-S2-20261024-020','utc':'2026-10-23T23:59:26+00:00','previous_sha256':'7bde40ec4f6d52036c08fbf16344e5d7f072a3553daa524e6017e013cdeda4d8','sha256_at_append':'77b4d17a20120d3db84bdc94d3742879e1bd7b8e98c6cb72a8529e2b1cbf21a6'},
 {'id':'COD-S2-20261024-021','utc':'2026-10-24T00:03:21+00:00','previous_sha256':'77b4d17a20120d3db84bdc94d3742879e1bd7b8e98c6cb72a8529e2b1cbf21a6','sha256_at_append':'b161924502d237e861b47a3303134c5ac5e68d2dc94325ba59dd6fa7cc5b3c98'}]})
checks=[]
def check(n,v):checks.append({'name':n,'pass':bool(v)})
for key in ['report','plan','producer','oof','manifest','assessment','decision_journal']:check('Index '+key,sha(ROOT/index[key])==index[key+'_sha256'])
for key in ['verification','fixtures','motor_reconciliation']:check('Check receipt '+key,sha(ROOT/index[key]['path'])==index[key]['sha256'] and read(ROOT/index[key]['path'])['failed']==0)
check('Exactv6 snapshot',SNAP.read_bytes()==(BACK/'Hackaton/Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json').read_bytes())
oldstate=read(BACK/'Preparación/ESTADO_PROYECTO.json');newstate=read(ROOT/'Preparación/ESTADO_PROYECTO.json')
check('Historical state branches preserved',all(newstate.get(k)==v for k,v in oldstate.items() if k not in ['memory_as_of','current_phase','collaboration_forum','week_2_nocturnal_continuation_20261023']))
oldroutes=read(BACK/'RUTAS_PROYECTO.json');newroutes=read(ROOT/'RUTAS_PROYECTO.json')
check('Other routes preserved',all(newroutes.get(k)==v for k,v in oldroutes.items() if k not in ['week_2_development_report','week_2_development_plan','week_2_development_oof']))
for k,v in newroutes.items():
    if k.startswith('week_2_'):check('Route '+k,(ROOT/v).exists())
for it in changes:
    if it['path'].endswith('.md'):check('Prose prefix '+it['path'],(ROOT/it['path']).read_bytes().startswith((ROOT/it['backup']).read_bytes()))
for doc in [ROOT/index['documentation'],REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',REPO/'docs/semana2/CAPITAL_CLIMA_CREDIBILIDAD_2023.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md',forum]:
    for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        target=link.strip('<>').split('#')[0]
        if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',target):continue
        check('Link '+rel(doc)+' -> '+target,(doc.parent/unquote(target)).resolve().exists())
for it in read(RUN/'frozen_sources_before_trial.json')['files']:check('Frozen source '+it['path'],sha(ROOT/it['path'])==it['sha256'])
check('B00 and18 alternatives',index['reference']=='W2-B00' and len(index['alternatives_preserved'])==18 and not index['promotion'])
check('Seven history cuts',len(index['history'])==7)
nightidx=read(NIGHT);oldnight=read(ROOT/'Hackaton/Semana 2/Codex/nocturno_antes_v7.json')
check('Third unit completed',nightidx['current_unit'] is None and nightidx['latest_completed_unit']['id']==plan['id'] and len(nightidx['completed_units'])==3)
check('Native schedule fields unchanged',all(nightidx[k]==oldnight[k] for k in ['window_start','window_end','frequency','automation_id','automation_kind','automation_target_thread','same_chat']))
check('2024 ledger absent',not (ROOT/selector['ledger_workspace_relative']).exists())
result={'utc':NOW,'scope':'Registration, sources and links only, no statistical suite or fitting repetition','passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks}
dump(RUN/'closure_verification.json',result);assert result['failed']==0,[x for x in checks if not x['pass']]
paths={p for p in RUN.rglob('*') if p.is_file()};paths.update(ROOT/x['path'] for x in changes)
paths.update([ROOT/index['documentation'],ROOT/index['plan'],ROOT/index['producer'],SNAP,Path(__file__),forum,REPO/'registro/semana2_desarrollo2023_pruebas_v7.json'])
paths.update(REPO/'herramientas'/f'{name}_desarrollo2023_v7_semana2.py' for name in ['documentar','probar','verificar'])
paths.add(REPO/'herramientas/diagnosticar_filas_capital_motor2023.py')
paths.update(ROOT/'Hackaton/Semana 2/Codex'/n for n in ['preinscribir_desarrollo2023_v7.py','desarrollo2023_v7_preinscripcion.md','desarrollo2023_v7_resultado.md','nocturno_antes_v7.json'])
reviewdir=(ROOT/plan['diagnostic_review']).parent;paths.update(p for p in reviewdir.rglob('*') if p.is_file())
dump(RUN/'closure_manifest.json',{'utc':NOW,'notice':'Corte de cierre; archivos compartidos pueden cambiar después conservando este registro histórico.',
 'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)],'reference':'W2-B00','confirmation_2024_open':False})
print(json.dumps({'registered':rel(ACTIVE),'closure_checks':result['passed'],'failed':0,'reference':'W2-B00','confirmation_2024_open':False}))
