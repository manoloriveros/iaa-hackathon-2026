"""Registro común del ciclo de integraciones con backups y control de concurrencia."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import unquote
import json,hashlib,os,re
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026';RUN=REPO/'privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b'
ACTIVE=REPO/'registro/semana2_desarrollo2023_actual.json';SNAP=REPO/'registro/semana2_desarrollo2023_v5_snapshot.json';NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
NOW=datetime.now(timezone.utc).isoformat();BACK=RUN/'state_before_registration';BACK.mkdir(exist_ok=False)
def dump(p,obj):
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def top(raw,key,value,add=False):
    val=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if add:
        assert key not in json.loads(raw),key;return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+val+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+val+raw[m.end()+end:]
changes=[]
def change(p,fn):
    before=p.read_bytes();backup=BACK/p.relative_to(ROOT);backup.parent.mkdir(parents=True,exist_ok=True)
    with backup.open('xb') as f:f.write(before)
    after=fn(before.decode('utf-8-sig')).encode('utf-8');tmp=p.with_name(p.name+'.s2dev6.tmp');assert p.read_bytes()==before,'Concurrencia '+str(p)
    with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert p.read_bytes()==before,'Concurrencia '+str(p);os.replace(tmp,p)
    changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p),'backup':rel(backup)})
index=read(RUN/'active_index_proposed.json');report=read(RUN/'report.json');plan=read(RUN/'plan_snapshot.json');assessment=read(RUN/'assessment.json')
assert ACTIVE.read_bytes()==SNAP.read_bytes(),'Conciliar índice concurrente'
for key in ['verification','fixtures']:assert read(ROOT/index[key]['path'])['failed']==0
selectorpath=REPO/'registro/semana2_seleccion_actual.json';selector=read(selectorpath);assert not (ROOT/selector['ledger_workspace_relative']).exists()
assert sha(ROOT/selector['policy']['path'])==plan['selection_policy_sha256'];(RUN/'selector_index_at_close.json').write_bytes(selectorpath.read_bytes())
forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';cut=forum.read_bytes();assert cut.count(b'<!-- aporte:COD-S2-20261023-019 -->')==1
change(ACTIVE,lambda raw:(RUN/'active_index_proposed.json').read_text(encoding='utf-8'))
def night(raw):
    obj=json.loads(raw);history=obj.get('completed_units',[obj['latest_completed_unit']])
    entry={'id':plan['id'],'run':rel(RUN),'documentation':index['documentation'],'decision_journal':index['decision_journal'],'verification':index['verification'],'fixtures':index['fixtures'],'forum_result':'COD-S2-20261023-019'}
    obj.update(status='scheduled_two_units_verified_conditions_open',updated_utc=NOW,latest_completed_unit=entry,completed_units=history+[entry],current_unit=None,
      next_unit='Investigate 2023 level/tail and reporting-link sensitivity with standard models; preregister any new experiment; do not retune c from these scores.',
      queue=['Review 2023 level/tail and common C0 observation-link sensitivity using standard models','Keep capital row materiality, climate timing and developed-prior reproduction/uncertainty conditions open','Verify new consumer changes only and prepare morning balance'],
      integration_decisions={'capital':'B14 trial2023 only, scope/formula checked, economic scale and row materiality open','climate':'not admitted prospectively; no pre2023 history','credibility':'B15 conditional alternative, no established overall improvement'},
      open_conditions=assessment['warnings'],no_retraining_or_suite_repetition_for_completed_v6=True)
    return json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
change(NIGHT,night)
def routes(raw):
    for key,val in [('week_2_development_report',index['documentation']),('week_2_development_plan',index['plan']),('week_2_development_oof',index['oof'])]:raw=top(raw,key,val)
    return top(raw,'week_2_development_v5_snapshot',rel(SNAP),True)
def state(raw):
    obj=json.loads(raw);phase={'as_of_utc':NOW,'phase':'week2_capital_credibility_trial_verified_climate_excluded_B00_retained_2024_closed','current_state_key':'week_2_development2023_v6_20261023',
      'historical_fields_notice':'Cortes y cinco snapshots anteriores preservados; seis tandas y continuidad nocturna separada.'}
    dev={'as_of_utc':NOW,'path_base':'workspace_root','index':rel(ACTIVE),'run':rel(RUN),'documentation':index['documentation'],'training_years':[2023],'scored_years':[2023],
      'rows_per_recipe':50094,'groups':30869,'folds':5,'new_price_base_fits':10,'new_auxiliary_Poisson_Gamma_fits':30,'new_credibility_factors':15,'exact_motor_reuses':5,
      'cumulative_price_base_fits':90,'cumulative_closed_form_constants':60,'auxiliary_counter_notice':index['auxiliary_counter_notice'],'models_consulted':index['models_consulted'],
      'results_D2':{x['model_id']:x['D2'] for x in report['summary']},'capital_corrected_2023':{'buildings':26,'contents':30,'all_T0_zero':True,'affected_rate_change_range':[-0.6236323923628572,1.5409219981637299]},
      'global_F0_changed':False,'climate_prospective_admitted':False,'credibility_default_adopted':False,'reference_retained':'W2-B00','alternatives_preserved':index['alternatives_preserved'],
      'promotion':False,'confirmation_2024_open':False,'confirmation_closed_by_current_user_instruction':True,'final_confirmation_roster_frozen':False,
      'verification':index['verification'],'fixtures':index['fixtures'],'decision_journal':index['decision_journal'],'forum_decisions':['COD-S2-20261023-018','COD-S2-20261023-019'],
      'pending':[x['effect'] for x in assessment['warnings']],'professional_independent_validation':False,'no_remote_training':True,'no_submissions':True,'no_delegation':True}
    collab=dict(obj['collaboration_forum'],updated_utc=NOW,latest_Codex_comment='COD-S2-20261023-019')
    headers=re.findall(rb'^## Codex \| ([^|]+) \| ([^|]+) \|',cut,re.M)
    if headers:collab['latest_Codex_comment']=headers[-1][0].decode().strip()
    continuity=dict(obj['week_2_nocturnal_continuation_20261023'],as_of_utc=NOW,latest_completed_unit=plan['id'],next_unit=read(NIGHT)['next_unit'])
    for key,val in [('memory_as_of',datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()),('current_phase',phase),('collaboration_forum',collab),('week_2_nocturnal_continuation_20261023',continuity)]:raw=top(raw,key,val)
    return top(raw,'week_2_development2023_v6_20261023',dev,True)
note='''

## Capital, clima y credibilidad: ensayo estándar de2023 antes de integrar

Codex, 23 de octubre de2026. Instrucción directa de revisar capital/clima/credibilidad antes de integrar, probar solo2023 con modelos estándar, conservarB00, dejar decisiones/resultados en foro y2024cerrado. Revisión previa revision_integracion_20261023T233806Z_0bd51230,25controles sin ajuste/predicción. Preinscripción COD-S2-20261023-018 a23:40:28UTC, resultado019 a23:50:01UTC. Corrida dev6_20261023T234239Z_fdab9f0b, planv6 e informe docs/semana2/CAPITAL_CLIMA_CREDIBILIDAD_2023.md. Índice activo con snapshot exactov5 conserva seis tandas; cortes previos intactos.

CAPS2:56filas2023 (26edificios,30contenidos), enmascaradas en F0 y todasT0=0, coinciden con la tabla recibida y división/1000. B14 aprende límites min/max de prima por mil solo con normales del ajuste2023 de cada ramo/fold; aplica prueba propia a sospechosas y las fallidas quedan desconocidas. Las56pasan; no se copian límites de2024/test. Misma receta GLM B13 (seisvariables,alpha0), diez refits hogar y cinco modelos motor exactos. Prima escrita solo en auditoría de escala, nunca en X; mantiene dependencia de tarifa/unidad no confirmada económicamente. No se modifica F0 global o datos originales ni se corrigen/predicen2024/test.

El efecto global B14/B13 D² es−0,00000162865, intervalo exploratorio95%[−0,00003090071;0,00002892635], total predicho unos−590CU. No equivale a inmaterialidad por fila: las56afectadas cambian tasas OOF entre−62,36% y+154,09% frente a imputar capital desconocido. Edificios afectados predicen14721,07→14270,45CU; contenidos2245,69→2846,27CU. Sin costes positivos no se valida su escala/severidad económica. Diagnóstico concilia totales/devianza (tres controles adicionales sin reentrenar).

Clima CLIMA-S2-01 excluido del contrato prospectivo: valores2024 para2023 y selector2024/2025. Se recibió COD-S2-VAL04-20261023-CLIMA-AVISO y se cotejó SHA1ead4dc…97f de su adverso sin repetirlo o adjudicárselo. Guardas propias rechazan fuente/selector futuros y ausencia de historia; no hay clima emergente anterior a2023. No se entrenó comparador con fuga o todo faltante. El hallazgo S2-VAL-DAT-003 mantiene responsable/estado. Un proxy físico condicionado o escenario exigiría alcance explícito; correlación no acredita disponibilidad.

NB-CRED:se reestimaron30GLM auxiliares estándar Poisson/Gamma por ramo/fold únicamente con ajuste emergente2023, asignaciones canónicas positivas, capital del ensayo, mediana/centrado y referencia regional fit-only. SE robustos por componente cliente-dirección, no solo cliente. Prior desarrollado2021–2023 de beta/SE, categorías y estacionalidad recibido/congelado desde Claude; cero refits desarrollados u otros años en este ensayo. No se declara reproducción del prior desde raw ni backtest prospectivo al inicio2023. Tau, Z y c reconstruidos; fuentes/autoría preservados. Z no incorpora incertidumbre del prior; tau usa coeficientes correlacionados y escasez de positivos; original/último y bloqueenero siguen condicionados.

B15=B14*c únicamente en nuevo negocio, renovación exacta, sin balanceA/E adicional. No se usa c de todo2023 ni calibración con OOF de otros folds cuyas predicciones se entrenaron con etiquetas del retenido. Es aplicación directa experimental sobre efecto de negocio no penalizado; no adopción sin cambios de todaNB-CRED-01. C porfold:autos0,681–0,777,edificios0,684–1,348,contenidos0,897–1,383. La variación del corrector no se confunde con igual variación de relatividad final. Severidad dominada por el prior.

D² B13=0,08671171,B14=0,08671008,B15=0,08606099. PredichoB14=15,4297millonesCU/A-E0,99141;B15=15,0876/A-E1,01388; observado15,2971. B15/B14 delta−0,00064909 intervalo95%[−0,00500418;0,00263310], retiro31gruposfavorables−0,00230283. FrenteB00:B14/B15 deltas+0,01812839/+0,01747930, intervaloscruzancero y retiropropio−0,01250214/−0,01078480.120parejas/2.000sorteos comunes,29nuevas reconstruidas, exploratorios tras16recetas adaptativas e investigación recibida sin corrección de búsqueda/multiplicidad; no promoción/equivalencia.

Nuevo negocio agregadoB14/B15 D²0,11117/0,10547,A-E0,90591/1,13629. Autos nuevo empeora con credibilidad (D²−0,01004→−0,03324,A-E0,879→1,223); edificios nuevo mejora0,05016→0,06336 y contenidos0,15358→0,17445,A-E1,184→1,052. Renovación exacta. No se presenta como mejora general ni se retira la alternativa creíble elegida como hipótesis por el participante.

Pasaron25controles de revisión,26casosfocales y832controlesseparados, con solapamiento. Comprobador no importa productor y bloquea fit en replay. Reconstruye regla de capital, matrices, score/sandwich por sistemaslineales, tau/Z/c, transformaciones, claves/ámbitos, métricas/segmentos/escenarios, remuestreo/influencia nuevos. MáximadiferenciaSE2,34e-15,condiciónmáxima1382;scoreaux8,09e-6 bajo umbral1e-4 fijado antes. Es revisión técnica propia deCodex,no profesional independiente o confirmación humana de escala/transferencia. Escenarios a tasasfijas no reestiman reservas/reportes.

Diez nuevos estimadores de precio (acumulado90, incluidos estrés históricos),30auxiliares separados,15factores/adaptadores;60constantes históricas sin cambios. No se mezclan los contadores con los ajustes históricos deClaude. Las14tablas OOF previas yB00son exactas. QuedanB01–B15como alternativas, sin promoción/retiro/listafinal. Estado nocturno:dosunidades terminadas, condiciones abiertas; siguiente nivel/cola y vínculoC0 solo2023 con modelosestándar y receta previa, sin retocar c a posteriori. Se conserva frecuencia/ventana nativa y otrasautomatizaciones intactas.

2024 sigue cerrado por instrucción directa:sin ledger, precios/predicciones/scores deeseaño otest, envíos, remoto, publicación externa o delegación. Siguen abiertos materialidad de capital/escala, clima temporal, prior no reproducido aquí/incertidumbre, reporte/reservas/último y negocio transferido. Revisión humana pendiente. Se conservan responsabilidades de los hallazgos ajenos y prácticasIAA de límites, segmentos, trazabilidad y separación de revisiones sin certificación.
'''
change(ROOT/'RUTAS_PROYECTO.json',routes);change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+note)
update='\n\n## Capital, clima y credibilidad: segunda unidad nocturna\n\nLa [prueba estándar solo2023](../Repositorio_IAA2026/docs/semana2/CAPITAL_CLIMA_CREDIBILIDAD_2023.md) aplica capital en B14 con límites de ajuste por fold y ensaya credibilidad B15. El score del capital apenas cambia pero las predicciones de sus56filas se mueven−62% a+154%; escala/materialidad siguen abiertas. Clima propuesto excluido por información futura. Credibilidad mejora hogar nuevo y empeora autos, sin ventaja global establecida. Se mantieneB00 yB01–B15,2024cerrado; el [índice nocturno](../Repositorio_IAA2026/registro/semana2_continuidad_nocturna.json) retoma nivel/cola y vínculoC0 sin retocar c por estos resultados.\n'
for name in ['README.md','PLAN_TRABAJO.md']:change(ROOT/'Hackaton/Semana 2'/name,lambda raw:raw+update)
change(REPO/'docs/semana2/DESARROLLO_2023_MODELOS_ESTANDAR.md',lambda raw:raw+'\n\n## Corte posterior: capital, clima y credibilidad\n\nLa [sexta prueba](CAPITAL_CLIMA_CREDIBILIDAD_2023.md) conserva estas recetas y ensaya dos cambios con criterios previos. El [snapshot de índice v5](../../registro/semana2_desarrollo2023_v5_snapshot.json) preserva exactamente este corte; el índice activo recoge el avance.\n')
change(REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',lambda raw:raw+'\n\n## Avance registrado tras revisar las integraciones\n\nLa [segunda unidad](CAPITAL_CLIMA_CREDIBILIDAD_2023.md) completó el ensayo2023 con capital por fold y credibilidad condicionada; clima propuesto no admisible prospectivamente. Se conservan las condiciones de escala/materialidad por fila, prior y disponibilidad, sin presentar todo como validado. La siguiente unidad aborda nivel/cola y C0 con modelos estándar y receta previa; no repetirá la tanda o ajustará c a posteriori. Frecuencia y ventana programadas se mantienen.\n')
change(REPO/'registro/semana2_listo_entrenar.json',lambda raw:top(raw,'latest_development_execution',{'as_of_utc':NOW,'index':rel(ACTIVE),'documentation':index['documentation'],'training_years':[2023],
 'status':'six_2023_trials_verified_integration_conditions_open','confirmation_2024_open':False,'confirmation_closed_by_current_user_instruction':True,'night_index':rel(NIGHT),
 'historical_counter_notice':'Contadores de preparación mantienen su corte. Índice de desarrollo distingue precios, auxiliares y reusos.'}))
dump(REPO/'registro/semana2_desarrollo2023_pruebas_v6.json',{'utc':NOW,'author':'Codex','verification':index['verification'],'fixtures':index['fixtures'],'review':plan['diagnostic_review'],'professional_independent_validation':False})
dump(RUN/'registration.json',{'utc':NOW,'changes':changes,'reference':'W2-B00','confirmation_2024_open':False})
dump(RUN/'forum_receipts.json',{'source':'Serialized helper responses in this task','receipts':[
 {'id':'COD-S2-20261023-018','utc':'2026-10-23T23:40:28+00:00','previous_sha256':'836b131f3b39494ff74a989e975cfeed24577681f4ba7622dae6d8e50d2d89f2','sha256_at_append':'82fe2ea16ff52065eb87a9b7decd210088edcb675b51c387fd581c60c3522752'},
 {'id':'COD-S2-20261023-019','utc':'2026-10-23T23:50:01+00:00','previous_sha256':'0d7c38f859236ab195c21d22d2f74361efe5bb85dc9489b90dd6bf0bc2b70be3','sha256_at_append':'7bde40ec4f6d52036c08fbf16344e5d7f072a3553daa524e6017e013cdeda4d8'}]})
checks=[]
def check(n,val):checks.append({'name':n,'pass':bool(val)})
for key in ['report','plan','producer','auxiliary_producer','oof','manifest','assessment','decision_journal']:check('Index '+key,sha(ROOT/index[key])==index[key+'_sha256'])
for key in ['verification','fixtures']:check('Checks '+key,sha(ROOT/index[key]['path'])==index[key]['sha256'] and read(ROOT/index[key]['path'])['failed']==0)
check('V5 snapshot exact',SNAP.read_bytes()==(BACK/'Hackaton/Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json').read_bytes())
oldstate=read(BACK/'Preparación/ESTADO_PROYECTO.json');newstate=read(ROOT/'Preparación/ESTADO_PROYECTO.json')
check('Historical branches preserved',all(newstate.get(k)==v for k,v in oldstate.items() if k not in ['memory_as_of','current_phase','collaboration_forum','week_2_nocturnal_continuation_20261023']))
oldroutes=read(BACK/'RUTAS_PROYECTO.json');newroutes=read(ROOT/'RUTAS_PROYECTO.json')
check('Other routes preserved',all(newroutes.get(k)==v for k,v in oldroutes.items() if k not in ['week_2_development_report','week_2_development_plan','week_2_development_oof']))
for key,val in newroutes.items():
    if key.startswith('week_2_'):check('Route '+key,(ROOT/val).exists())
for it in changes:
    if it['path'].endswith('.md'):check('Prose prefix '+it['path'],(ROOT/it['path']).read_bytes().startswith((ROOT/it['backup']).read_bytes()))
for doc in [ROOT/index['documentation'],REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',REPO/'docs/semana2/DESARROLLO_2023_MODELOS_ESTANDAR.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md',forum]:
    for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        target=link.strip('<>').split('#')[0]
        if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',target):continue
        check('Link '+rel(doc)+' -> '+target,(doc.parent/unquote(target)).resolve().exists())
for it in read(RUN/'frozen_sources_before_fit.json')['files']:check('Frozen source '+it['path'],sha(ROOT/it['path'])==it['sha256'])
for num in ['018','019']:check('Unique forum '+num,forum.read_bytes().count(('<!-- aporte:COD-S2-20261023-'+num+' -->').encode())==1)
check('B00 and15alternatives',index['reference']=='W2-B00' and len(index['alternatives_preserved'])==15 and not index['promotion'])
nightidx=read(NIGHT);check('Night completed and retained schedule',nightidx['current_unit'] is None and nightidx['latest_completed_unit']['id']==plan['id'] and nightidx['window_end']=='2026-10-24T07:00:00-05:00')
check('2024 ledger absent',not (ROOT/selector['ledger_workspace_relative']).exists())
result={'utc':NOW,'scope':'Registration/link/source integrity only; no statistical or training repetition','passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks}
dump(RUN/'closure_verification.json',result);assert result['failed']==0,[x for x in checks if not x['pass']]
paths={p for p in RUN.rglob('*') if p.is_file()};paths.update(ROOT/x['path'] for x in changes)
paths.update([ROOT/index['documentation'],ROOT/index['plan'],ROOT/index['producer'],ROOT/index['auxiliary_producer'],SNAP,Path(__file__),forum,REPO/'registro/semana2_desarrollo2023_pruebas_v6.json'])
paths.update(REPO/'herramientas'/f'{name}_desarrollo2023_v6_semana2.py' for name in ['documentar','probar','verificar'])
paths.add(REPO/'herramientas/revisar_integraciones2023_semana2.py')
paths.update(ROOT/'Hackaton/Semana 2/Codex'/n for n in ['preinscribir_desarrollo2023_v6.py','desarrollo2023_v6_preinscripcion.md','desarrollo2023_v6_resultado.md','nocturno_antes_v6.json'])
reviewdir=(ROOT/plan['diagnostic_review']).parent;paths.update(p for p in reviewdir.rglob('*') if p.is_file())
dump(RUN/'closure_manifest.json',{'utc':NOW,'notice':'Corte de cierre. Los archivos compartidos pueden cambiar después, los históricos conservan su corte.',
 'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)],'reference':'W2-B00','confirmation_2024_open':False})
print(json.dumps({'registered':rel(ACTIVE),'checks':result['passed'],'failed':0,'reference':'W2-B00','confirmation_2024_open':False}))
