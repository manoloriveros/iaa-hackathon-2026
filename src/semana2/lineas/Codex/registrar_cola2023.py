"""Registra una sensibilidad distinta del catálogo principal, con backup y cierre."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import unquote
import json,hashlib,re,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026';RUN=REPO/'privado/semana2/desarrollo2023/cola_20261024T001114Z_e5d1c211'
INDEX=REPO/'registro/semana2_sensibilidad_observacion_actual.json';COUNTERS=REPO/'registro/semana2_contadores_propios_actual.json';NIGHT=REPO/'registro/semana2_continuidad_nocturna.json';NOW=datetime.now(timezone.utc).isoformat()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
BACK=RUN/'state_before_registration';BACK.mkdir(exist_ok=False);changes=[]
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
    after=fn(before.decode('utf-8-sig')).encode('utf-8');tmp=path.with_name(path.name+'.cola.tmp');assert path.read_bytes()==before,'Concurrencia '+str(path)
    with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==before,'Concurrencia '+str(path);os.replace(tmp,path)
    changes.append({'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path),'backup':rel(backup)})
i=read(RUN/'sensitivity_index_proposed.json');r=read(RUN/'report.json');p=read(RUN/'plan_amendment_snapshot.json');assessment=read(RUN/'assessment.json');main=ROOT/p['main_model_index']
assert sha(main)==p['main_model_index_sha256'];assert not INDEX.exists() and not COUNTERS.exists()
for key in ['verification','fixtures']:assert read(ROOT/i[key]['path'])['failed']==0 and sha(ROOT/i[key]['path'])==i[key]['sha256']
selectorpath=REPO/'registro/semana2_seleccion_actual.json';selector=read(selectorpath);assert not (ROOT/selector['ledger_workspace_relative']).exists();(RUN/'selector_index_at_close.json').write_bytes(selectorpath.read_bytes())
forum=ROOT/'Hackaton/Semana 2/Foro/FORO.md';cut=forum.read_bytes()
for suffix in ['022','023','024']:assert cut.count(('<!-- aporte:COD-S2-20261024-'+suffix+' -->').encode())==1
dump(INDEX,i)
dump(COUNTERS,{'author':'Codex','as_of_utc':NOW,'scope':'Own pricing/development lineage only; not all project fits or other authors. Historical main catalog retains its dated counter.',
 'cumulative_price_base_fits':100,'cumulative_closed_form_constants':90,'auxiliary_Poisson_Gamma_fits_separate':30,
 'baseline':{'index':rel(main),'sha256':sha(main),'price_base_fits':90,'constants':60,'auxiliary_fits':30},
 'increments':[{'id':p['id'],'run':rel(RUN),'price_GLM_fits':10,'constant_values':30,'auxiliary_fits':0,'reporting_fits':0,
  'constants_before_receipt_failure':3,'constants_after_resume':27,'cached_bundles_reused':2,'analytic_adapters_not_fits':45,'exact_content_reuses_not_fits':15}],
 'latest_sensitivity_index':rel(INDEX),'next_unit_must_read_this_counter':True})
def night(raw):
    obj=json.loads(raw);assert obj['current_unit']['id']==p['id']
    entry={'id':p['id'],'run':rel(RUN),'index':rel(INDEX),'documentation':i['documentation'],'decision_journal':i['decision_journal'],'verification':i['verification'],'fixtures':i['fixtures'],'forum_result':i['forum_result']}
    history=obj['completed_units'];assert p['id'] not in [x['id'] for x in history]
    obj.update(status='scheduled_four_units_verified_conditions_open',updated_utc=NOW,current_unit=None,latest_completed_unit=entry,completed_units=history+[entry],
      current_global_fit_counter_index=rel(COUNTERS),latest_observation_sensitivity_index=rel(INDEX),
      next_unit='Preregister reserve.75/1.25 response and ownfold reporting-mark exposure sensitivity, refit standard models only2023. Read common counter100pricefits/90constants first. Preserve main19recipe catalog, prior tail assumptions, B00 and2024closed.',
      queue=['Reconcile reserve.75/1.25 target and reporting marks, preregister standard-model sensitivity only2023','Keep capital units/joint support, climate timing, credibility prior and tail identifiability conditions open','Prepare morning balance, no repeated unchanged fits/suites or optimized credibility weight'],
      open_conditions=assessment['warnings'],no_retraining_or_suite_repetition_for_completed_tail=True)
    obj.setdefault('integration_decisions',{})['tail']='T10F standard refit andT10R mixture normalization verified conditionally; observedD2 fails to identify nominal ultimate scale. No adopted mass or mixture.'
    return json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
change(NIGHT,night)
def routes(raw):
    for key,value in [('week_2_observation_sensitivity_index',rel(INDEX)),('week_2_observation_sensitivity_report',i['documentation']),('week_2_observation_sensitivity_plan',i['plan']),('week_2_own_fit_counters',rel(COUNTERS))]:raw=top(raw,key,value,True)
    return raw
def state(raw):
    obj=json.loads(raw);key='week_2_tail_sensitivity2023_v1_20261024'
    phase={'as_of_utc':NOW,'phase':'week2_tail_observation_sensitivity_verified_nominal_level_unidentified_B00_retained_2024_closed','current_state_key':key,
      'historical_fields_notice':'Main19recipe catalog/v7 preserves dated100%unchanged artifacts; tail sensitivity has separate index/counter, four night units completed.'}
    dev={'as_of_utc':NOW,'path_base':'workspace_root','index':rel(INDEX),'run':rel(RUN),'documentation':i['documentation'],'training_years':[2023],'scored_years':[2023],
      'rows_per_stress':50094,'groups':30869,'folds':5,'main_model_index_preserved':rel(main),'main_model_index_sha256':sha(main),'main_candidates':19,
      'stress_configurations':6,'new_exploratory_contrasts':6,'new_price_GLM_fits':10,'new_closed_form_constants':30,'exact_content_reuses':15,'analytic_adapters_not_fits':45,
      'new_reporting_fits':0,'new_auxiliary_fits':0,'cumulative_price_base_fits':100,'cumulative_closed_form_constants':90,'own_fit_counter_index':rel(COUNTERS),
      'B14_nominal2023_base':15606084.086153384,'B14_nominal2023_fixed':15958225.191781856,'B14_nominal2023_renormalized':15998345.080129558,
      'B14_observed_D2_base':0.0867100784503696,'B14_observed_D2_fixed':0.08671999071807002,'B14_observed_D2_renormalized':0.0867100784503696,
      'actual_2025_predictions':0,'nominal2023_is_conditional_not_truth':True,'tail_mass_adopted':False,'reference':'W2-B00','all_alternatives_preserved':True,'promotion':False,
      'confirmation_2024_open':False,'ledger_absent':True,'test_predictions':0,'verification':i['verification'],'fixtures':i['fixtures'],
      'forum_comments':['COD-S2-20261024-022','COD-S2-20261024-023','COD-S2-20261024-024'],'decision_journal':i['decision_journal'],
      'failed_attempt_preserved':rel(RUN/'failed_attempt.json'),'resumed_two_constant_bundles_no_repeat':True,'fixture_failure_preserved':rel(RUN/'fixture_checks_attempt1.json'),
      'pending':[x['effect'] for x in assessment['warnings']],'professional_independent_validation':False,'no_remote':True,'no_submissions':True,'no_delegation':True}
    collab=dict(obj['collaboration_forum'],updated_utc=NOW);headers=re.findall(rb'^## Codex \| ([^|]+) \| ([^|]+) \|',cut,re.M)
    if headers:collab['latest_Codex_comment']=headers[-1][0].decode().strip()
    continuity=dict(obj['week_2_nocturnal_continuation_20261023'],as_of_utc=NOW,latest_completed_unit=p['id'],next_unit=read(NIGHT)['next_unit'])
    for k,v in [('memory_as_of',datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).isoformat()),('current_phase',phase),('collaboration_forum',collab),('week_2_nocturnal_continuation_20261023',continuity)]:raw=top(raw,k,v)
    return top(raw,key,dev,True)
note=f'''

## Cuarta unidad nocturna: cola y nivel condicionado, solo 2023

Codex, corte UTC {NOW}. Se continúa la autorización nocturna vigente con modelos estándar, sin complejizar o abrir2024. Plan S2-COLA2023-v1-20261024 y comentario previo022 a00:10:54UTC. Corrida cola_20261024T001114Z_e5d1c211. Corrección técnica023 a00:13:15UTC; resultado024 a00:20:51UTC. Informe docs/semana2/SENSIBILIDAD_COLA_Y_NIVEL_2023.md e índice específico registro/semana2_sensibilidad_observacion_actual.json. El índice principal desarrollo2023_v7, sus19recetas/171parejas y todaslasOOF permanecen idénticos porSHA; seisconfiguraciones de observación no se mezclan como nuevos candidatos conC0común.

Se revisa solo cola10%, dejando refit de reservas0,75/1,25 pendiente. T10F conserva pesosdeperil yreajustaB00/B12/B14 sobre e_cost_mix_tail0.1. T10R interpreta10% como masadecosteúltimo noobservada en bodily_injury/subsidence: w'_p proporcional w_p/(1−t_p), q'_p=(1−t_p)q_p y Z=sum(w_p/(1−t_p)). Entonces q'_mix=q_mix/Z; con e'=e/Z y r'=Zr el observado quedaidéntico. GLMlogalpha0/constantes conservanóptimo porhomogeneidad, intercepto+logZ, sinfit extra. No seextiende aGLMpenalizado/árbol/ancla o prueba de severidad/frecuencia faltante. Pesos ycurvas delajuste2023propio, ningúnretenido.

MismosT0/50.094periodos2023/30.869componentes/5folds; respuestaT0/e,peso√e,predicciónobservadae*r. Nominalcondicionado=exposiciónnominal2023*r deesosmismosperiodos, sinpredicciones2025/test ni etiquetasúltimas. B14nominalbase15.606.084,09CU,T10F15.958.225,19(+2,256%),T10R15.998.345,08(+2,514%/392.261CU). D²base0,08671008,T10F0,08671999,T10R0,08671008exacto. Identidadobservadaporfilamáxdiferencia1,82e-12CU; observadoT10Fbajaunos551CU peseaaumentarnominal352.141CU. Elscoreobservadonoidentificalacolanoobservada; ningunamasao mezclaadoptada.

Base/T10F/T10R B00D²0,06858169/0,06861450/0,06858169,nominal15,7873/16,1475/16,1885millones; B12D²0,07491526/0,07492702/0,07491526,nominal15,5441/15,8955/15,9356millones. Z−1autos3,640–4,322%,edificios0,699–1,168%,contenidos0(salvoprecisión). Seisseiscontrastes T10F/2.000sorteoscomunes nuevos; no repetir171previos o bootstrapT10Ridéntico. IncrementospropiosT10F/B00+0,00003281IC95%[+0,00000652;+0,00007938],B12+0,00001176[+0,00000011;+0,00003116],B14+0,00000991[−0,00000049;+0,00002583]. Los tres cambiansigno alretirarsus31gruposfavorables. DentroT10F B14/constante+0,01810549intervalocruzacero yretiro−0,01250654. Exploratorios sincorregirbúsqueda/multiplicidad, sinpromoción/equivalencia/retiro/listafinal o verdadúltima.

DiezGLM nuevos,treintaconstantes cerradas,quincecopias exactascontenidos y45adaptadoresalgebraicos(noajustes). Cero curvasdereporte oauxiliaresnuevos. Contador propio actual registro/semana2_contadores_propios_actual.json:100ajustesprecio/90constantes;30auxiliaresv6 separados,norecontados. El índice principal conserva90/60de sucortehistórico;usarcontadoractualantesdenuevosajustes. Noclaimdetotalproyecto/otrosautores.

La primera pasada falló alguardarreciboB12(listatratadacomodict) despuésde3constantes,antesdeGLM oscorecomparativonuevo. Seconservan código/plan/intento, manifestantesdefallo, failed_attempt.json ycomentario023; larecetapermanece ydosbundlesrecuperadasbyteexactas. Se calcularonsolo27constantespendientes y10GLM,no33constantes. Pasaron715controlesseparados que noimportanproductor ybloqueanfit, reconstruyenpesos/curvas/mezcla, óptimoescalar, gradiente/imputación, exp(Xbeta), métricas/segmentos/6bootstrap/influencia. 34adversosfinales; primerrecibo33pases/1falloporigualdadbinariaracional/float2,22e-16, nocambioenmodelo. Seconservanfallo/código;comparaciónfloatcon1e-14repiteúnicamentecasofallido,identidadracionalsigueexacta. Sinrepetirsuites,entrenamientooremuestrainalterados. Revisión técnicapropia,noprofesionalindependiente.

Siguencondicionados masayseveridadnobservada, estacionariedad/censura, mezclaporperilindividual,capitalunidad/soporteconjunto,climatemporal,priorcredibilidadytau/reportes/reservas/último. Validaciónagrupada2023alcorte2024-12-31norepresentaconocimientoalinicio2023. Siguienteunidad:recetapreviareservas0,75/1,25conmodelosestándar2023,leercontadoractual,noajustarcporresultados. B00ytodaslasalternativaspreservados,2024cerradoexplícito,ledgerausente;sinprecios/predicciones/scoresdeeseañootest,remoto,envíos,publicaciónexterna,nuevoschats,delegaciónocambiosaotrasautomatizaciones. Cuartaunidadnocturnaterminada,programaciónexistentecontinúa.
'''
change(ROOT/'RUTAS_PROYECTO.json',routes);change(ROOT/'Preparación/ESTADO_PROYECTO.json',state)
for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+note)
update='\n\n## Cola y nivel condicionado de 2023\n\nLa [sensibilidad de cola](../Repositorio_IAA2026/docs/semana2/SENSIBILIDAD_COLA_Y_NIVEL_2023.md) compara modelos estándar reajustados con pesos fijos y una mezcla renormalizada. Esta última sube alrededor de2,5% el nominal condicionado de2023 conservando el score observado: el score no identifica la cola no observada. B00 y el catálogo principal conservan su corte; nuevo índice de sensibilidad y contador propio100ajustes/90constantes.2024cerrado. Siguiente unidad: reservas0,75/1,25 con receta previa.\n'
for name in ['README.md','PLAN_TRABAJO.md']:change(ROOT/'Hackaton/Semana 2'/name,lambda raw:raw+update)
change(REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',lambda raw:raw+'\n\n## Cuarta unidad: cola y nivel condicionado\n\nLa [sensibilidad de observación](SENSIBILIDAD_COLA_Y_NIVEL_2023.md) conserva B00 y el catálogo principal. El mismo score observado admite un nominal condicionado2023 alrededor de2,5% mayor bajo otra mezcla de cola, sin probarla verdadera. Fuentes, fallos y correcciones preservados; siguiente reservas0,75/1,25 con receta previa2023. Leer el [contador propio actual](../../registro/semana2_contadores_propios_actual.json):100ajustes/90constantes; auxiliares separados.2024cerrado y programación sin cambios.\n')
change(REPO/'registro/semana2_listo_entrenar.json',lambda raw:top(raw,'latest_observation_sensitivity_execution',{'as_of_utc':NOW,'index':rel(INDEX),'documentation':i['documentation'],'run':rel(RUN),
 'training_years':[2023],'status':'conditional_tail_scale_unidentified','counters':rel(COUNTERS),'confirmation_2024_open':False,'test_predictions':0,'historical_fields_preserved':True},True))
dump(REPO/'registro/semana2_cola2023_pruebas_v1.json',{'utc':NOW,'author':'Codex','verification':i['verification'],'fixtures':i['fixtures'],'failed_attempt':rel(RUN/'failed_attempt.json'),'fixture_precision_recheck':rel(RUN/'fixture_precision_recheck.json'),'professional_independent_validation':False})
dump(RUN/'registration.json',{'utc':NOW,'changes':changes,'main_catalog_sha256_preserved':sha(main),'reference':'W2-B00','confirmation_2024_open':False})
dump(RUN/'forum_receipts.json',{'source':'Serialized helper responses in this chat','receipts':[
 {'id':'COD-S2-20261024-022','utc':'2026-10-24T00:10:54+00:00','previous_sha256':'b161924502d237e861b47a3303134c5ac5e68d2dc94325ba59dd6fa7cc5b3c98','sha256_at_append':'f0596fd31ebb505e0f484487628a2274a7a63e9013a90f3d1c2ec8548aab7ffe'},
 {'id':'COD-S2-20261024-023','utc':'2026-10-24T00:13:15+00:00','previous_sha256':'f0596fd31ebb505e0f484487628a2274a7a63e9013a90f3d1c2ec8548aab7ffe','sha256_at_append':'33869ef010497c585318f4212f84d2b398d4c76ece77d608c4bc62f5401b50f9'},
 {'id':'COD-S2-20261024-024','utc':'2026-10-24T00:20:51+00:00','previous_sha256':'33869ef010497c585318f4212f84d2b398d4c76ece77d608c4bc62f5401b50f9','sha256_at_append':'9cedd3bc2ef3fb36ca81e42089ed24db9bee4842e4b4ff011729ed03c3c62bf0'}]})
checks=[]
def check(n,v):checks.append({'name':n,'pass':bool(v)})
for key in ['report','plan','producer','oof','manifest','assessment','decision_journal']:check('Index '+key,sha(ROOT/i[key])==i[key+'_sha256'])
for key in ['verification','fixtures']:check('Check receipt '+key,sha(ROOT/i[key]['path'])==i[key]['sha256'] and read(ROOT/i[key]['path'])['failed']==0)
check('Main catalog exact',sha(main)==p['main_model_index_sha256'] and read(main)['reference']=='W2-B00' and len(read(main)['alternatives_preserved'])==18)
oldstate=read(BACK/'Preparación/ESTADO_PROYECTO.json');newstate=read(ROOT/'Preparación/ESTADO_PROYECTO.json')
check('All historical branches preserved',all(newstate.get(k)==v for k,v in oldstate.items() if k not in ['memory_as_of','current_phase','collaboration_forum','week_2_nocturnal_continuation_20261023']))
oldroutes=read(BACK/'RUTAS_PROYECTO.json');newroutes=read(ROOT/'RUTAS_PROYECTO.json');check('All old routes preserved',all(newroutes.get(k)==v for k,v in oldroutes.items()))
for k,v in newroutes.items():
    if k.startswith('week_2_'):check('Route '+k,(ROOT/v).exists())
for it in changes:
    if it['path'].endswith('.md'):check('Prose prefix '+it['path'],(ROOT/it['path']).read_bytes().startswith((ROOT/it['backup']).read_bytes()))
for doc in [ROOT/i['documentation'],REPO/'docs/semana2/PLAN_NOCTURNO_20261023.md',ROOT/'Hackaton/Semana 2/README.md',ROOT/'Hackaton/Semana 2/PLAN_TRABAJO.md',forum]:
    for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        target=link.strip('<>').split('#')[0]
        if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://',target):continue
        check('Link '+rel(doc)+' -> '+target,(doc.parent/unquote(target)).resolve().exists())
for it in p['frozen_sources']:check('Frozen source '+it['path'],sha(ROOT/it['path'])==it['sha256'])
n=read(NIGHT);oldn=read(ROOT/'Hackaton/Semana 2/Codex/nocturno_antes_cola2023.json')
check('Fourth unit complete',n['current_unit'] is None and n['latest_completed_unit']['id']==p['id'] and len(n['completed_units'])==4)
check('Native schedule unchanged',all(n[k]==oldn[k] for k in ['window_start','window_end','frequency','automation_id','automation_kind','automation_target_thread','same_chat']))
check('Counters correct',read(COUNTERS)['cumulative_price_base_fits']==100 and read(COUNTERS)['cumulative_closed_form_constants']==90)
check('2024ledger absent',not (ROOT/selector['ledger_workspace_relative']).exists())
result={'utc':NOW,'scope':'Registration/source/link integrity only, no repeated statistical suite or fit','passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks}
dump(RUN/'closure_verification.json',result);assert result['failed']==0,[x for x in checks if not x['pass']]
paths={q for q in RUN.rglob('*') if q.is_file()};paths.update(ROOT/x['path'] for x in changes);paths.update([INDEX,COUNTERS,ROOT/i['documentation'],ROOT/i['plan'],ROOT/i['producer'],Path(__file__),forum,REPO/'registro/semana2_cola2023_plan_v1.json',REPO/'registro/semana2_cola2023_pruebas_v1.json'])
paths.update(REPO/'herramientas'/name for name in ['documentar_cola2023_semana2.py','verificar_cola2023_semana2.py','probar_cola2023_semana2.py','revisar_precision_fixture_cola2023.py'])
paths.update(ROOT/'Hackaton/Semana 2/Codex'/name for name in ['preinscribir_cola2023.py','conciliar_cola2023.py','cola2023_preinscripcion.md','cola2023_correccion_recibo.md','cola2023_resultado.md','nocturno_antes_cola2023.json'])
dump(RUN/'closure_manifest.json',{'utc':NOW,'notice':'Corte histórico; los archivos compartidos podrán cambiar después conservando este recibo.','files':[{'path':rel(q),'sha256':sha(q),'bytes':q.stat().st_size} for q in sorted(paths)],'reference':'W2-B00','confirmation_2024_open':False})
print(json.dumps({'registered':rel(INDEX),'main_catalog_unchanged':True,'closure_checks':result['passed'],'failed':0,'counters':rel(COUNTERS)}))
