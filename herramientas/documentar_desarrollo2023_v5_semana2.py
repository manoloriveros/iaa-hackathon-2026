"""Cierre de la primera unidad nocturna; documentación y decisiones verificadas."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy,os,tomllib
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1];RUN=REPO/'privado/semana2/desarrollo2023/dev5_20261023T232328Z_69df9ead'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,obj):
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
report=read(RUN/'report.json');plan=read(RUN/'plan_snapshot.json');vp=sorted((RUN/'verifications').glob('*.json'))[-1];v=read(vp);fixtures=read(RUN/'fixture_checks.json')
assert v['failed']==fixtures['failed']==0
idx=read(REPO/'registro/semana2_desarrollo2023_actual.json');assert idx['id']=='S2-DEV2023-v4-20261023'
snapshot=REPO/'registro/semana2_desarrollo2023_v4_snapshot.json'
with snapshot.open('xb') as f:f.write((REPO/'registro/semana2_desarrollo2023_actual.json').read_bytes())
automation=Path(os.environ.get('CODEX_HOME','C:/Users/manol/.codex'))/'automations/iaa-semana-2-modelos-est-ndar-y-validaci-n-nocturna/automation.toml'
auto=tomllib.loads(automation.read_text(encoding='utf-8'));assert auto['status']=='ACTIVE' and auto['target_thread_id']=='01a16986-60ad-7532-b2f5-2461a74fdcd7' and 'UNTIL=20261024T120000Z' in auto['rrule']
(RUN/'automation_at_close.toml').write_bytes(automation.read_bytes())
points={x['model_id']:x for x in report['summary']};segments=read(RUN/'diagnostics/segments.json');seg=lambda mid,dim,label:next(x for x in segments if x['model_id']==mid and x['segment']==dim and x['label']==label)
contrasts=[x for x in report['pairs'] if (x['candidate'],x['reference']) in [('W2-B12','W2-B00'),('W2-B13','W2-B12'),('W2-B13','W2-B00'),('W2-B13','W2-B08')]]
assessment={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','reference_retained':'W2-B00','alternatives_preserved':list(points)[1:],'promotion':False,
 'confirmation_2024_open':False,'final_confirmation_roster_frozen':False,'professional_independent_validation':False,
 'standard_models_first':True,'complexity_increase_justified_by_this_batch':False,'primary_contrasts':contrasts,
 'warnings':[
 {'id':'DEV5-UNCERTAIN-GAIN','status':'open','consequence':'B12/B00, B13/B12 and B13/B00 intervals include zero; own top31 removal reverses advantages. Keep incumbent and alternatives.'},
 {'id':'DEV5-LEVEL-NOT-ULTIMATE','status':'open','consequence':'Global A/E near one is observed T0 under common C0, not ultimate, reserve sufficiency or transfer calibration.'},
 {'id':'DEV5-NEW-SEGMENTS','status':'open','consequence':'Motor-new D2 still negative and A/E below one; contents-new A/E1.184; building-new still below B00 D2 despite good global line level.'},
 {'id':'DEV5-SEARCH','status':'open','consequence':'Fourteen adaptive 2023 recipes, 91 unadjusted exploratory pairs. No temporal confirmation.'},
 {'id':'DEV5-PARTICIPANT-TABLES','status':'pending_separate_review','consequence':'CLA003 tables retained as received evidence. No future climate or whole-2023 calibration silently added.'},
 {'id':'DEV5-2024-CLOSED','status':'open','consequence':'User instruction retains closure regardless selector technical repair.'}]}
dump(RUN/'assessment.json',assessment)
journal={'id':'S2-NOCHE-CICLO-01','utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','source_authorization':plan['authorization_literal'],
 'decisions':[
 {'id':'N01-KEEP-HOLDOUT','decision':'Only 2023, B00 incumbent','evidence':[rel(vp)],'check':'2023 inputs/OOF, disjoint groups and absent ledger','result':'passed','consequence':'2024 remains closed'},
 {'id':'N02-SIMPLE-FIRST','decision':'Business constants and six-feature main-effect GLM, no additional complexity','evidence':[rel(ROOT/plan['code']),rel(RUN/'plan_snapshot.json')],'check':'preregistration timestamp, exact core and effective alpha0 parameters','result':'passed','consequence':'Do not infer need for interactions/boosting'},
 {'id':'N03-OBJECTIVE','decision':'Same T0, scoped C0, rate target T0/e and sqrt(e) weights','evidence':[rel(RUN/'fixture_checks.json'),rel(vp)],'check':'total/rate loss identity, constant optimum and GLM score/finite differences','result':'passed','consequence':'Observed proxy only; no extra IBNR or exposure multiplication'},
 {'id':'N04-FIT-SCOPE','decision':'Fit preprocessing and all rates inside outer-training rows','evidence':[rel(vp)],'check':'training medians/scales/categories, groups, gradients and blocked-fit replay','result':'passed','consequence':'No held-out fitting, independent-professional review remains pending'},
 {'id':'N05-RETAIN-ALTERNATIVES','decision':'No promotion or retirement from this batch','evidence':[rel(RUN/'diagnostics/pairs.json'),rel(RUN/'assessment.json')],'check':'parent/reference uncertainty and favorable-group influence','result':'advantages_not_established','consequence':'Keep B00 and B01-B13; do not call equivalence'},
 {'id':'N06-NEW-SOURCE-TABLES','decision':'Retain F0 version for controlled standard-model comparison','evidence':['Hackaton/Semana 2/Foro/FORO.md#cla-s2-20261023-003',rel(RUN/'plan_snapshot.json')],'check':'no added capital/weather/credibility table in consumer','result':'integration_not_executed','consequence':'Separate fold/temporal review before any new integration'},
 {'id':'N07-OVERNIGHT','decision':'Hourly continuation in current chat until 07:00 Bogota, with progress','evidence':[rel(RUN/'automation_at_close.toml')],'check':'native create/view and saved ACTIVE state, target-thread and end bound','result':'scheduled_not_future_execution_proof','consequence':'Host/app must remain available; actual cycles record execution separately'}],
 'verification':{'passed':v['passed'],'failed':0,'path':rel(vp)},'fixtures':{'passed':fixtures['passed'],'failed':0,'path':rel(RUN/'fixture_checks.json')},
 'no_unchanged_suite_repetition':True,'professional_independent_validation':False,'next_unit':'Audit CLA003 capital and credibility fitting scopes and temporal-weather availability before another recipe'}
dump(RUN/'decision_journal.json',journal)
table='\n'.join(f"| {m} | {points[m]['D2']:.5f} | {points[m]['predicted_total']/1e6:.3f} | {points[m]['actual_over_expected']:.3f} | {seg(m,'business','new_business')['D2']:.5f} | {seg(m,'business','new_business')['actual_over_expected']:.3f} |" for m in ['W2-B00','W2-B08','W2-B12','W2-B13'])
pairtab='\n'.join(f"| {p['candidate']} / {p['reference']} | {p['delta_D2']:.5f} | [{p['exploratory_lower95']:.5f}; {p['exploratory_upper95']:.5f}] | {p['delta_after_removal']:.5f} |" for p in contrasts)
linetab='\n'.join('| '+label+' | '+' | '.join(f"{seg(mid,'line',line)['D2']:.5f}" for mid in ['W2-B00','W2-B12','W2-B13'])+' |' for line,label in [('motor','Autos'),('buildings','Edificios'),('contents','Contenidos')])
rp='../../'+RUN.relative_to(REPO).as_posix();docpath=REPO/'docs/semana2/DESARROLLO_2023_MODELOS_ESTANDAR.md'
doc=f'''# Modelos estándar: primera unidad nocturna

Codex, 23 de octubre de 2026. Una constante por tipo de negocio y un GLM con seis variables por ramo proporcionan referencias sencillas útiles. Sus ventajas observadas en 2023 siguen inciertas y dependen de pocos grupos de evaluación. Se conserva B00, todas las alternativas y el cierre de 2024. Esta prueba no justifica añadir complejidad.

La petición nueva del participante prioriza validación de decisiones y modelos estándar. El [plan nocturno](PLAN_NOCTURNO_20261023.md) programa continuidad en este chat cada hora de 19:00 a 07:00 de Bogotá. El estado nativo está activo y acotado al 24 de octubre de 2026 a las 07:00; eso acredita programación, no ejecuciones futuras. Se requiere que el equipo y la aplicación estén disponibles. Las otras automatizaciones no se modificaron.

El [plan v5](../../registro/semana2_desarrollo2023_plan_v5.json) quedó en COD-S2-20261023-016 antes del ajuste. El resultado está en COD-S2-20261023-017 del [foro](<../../../Semana 2/Foro/FORO.md>). El [índice de continuidad](../../registro/semana2_continuidad_nocturna.json) separa lo terminado del trabajo siguiente. El [registro de decisiones del ciclo]({rp}/decision_journal.json) vincula cada decisión con su comprobación y consecuencia.

## Recetas y entradas

B12 aprende una constante por ramo y nuevo negocio/renovación, solo con filas de ajuste: `r_b=sum(T0/sqrt(e))/sum(sqrt(e))`. Son treinta constantes Tweedie, no cocientes actuariales sum(T0)/sum(e), balance OOF o calibración posterior.

B13 es un GLM Tweedie 1,5 con enlace log, alpha0, intercepto, efectos principales y seis predictores por ramo. No tiene interacciones o selección posterior de variables. Autos usa nuevo negocio, NCB, edad y grupo de valor del vehículo, banda de edad del conductor y región. Edificios usa nuevo negocio, logcapital, edad del inmueble, zona inundable, tipo de inmueble y región. Contenidos usa nuevo negocio, logcapital, dormitorios, objetos valiosos, tipo de inmueble y región. Mediana y StandardScaler numéricos; OHE con primera categoría de referencia, mínimo50/máximo40. Todo se aprende dentro del ajuste. L-BFGS, tolerancia1e-6, máximo2000, sin rejilla. La fuente registra además tolerancia técnica del gradiente 1e-4 antes del ajuste; el máximo observado fue 4,843e-6.

Mismos 50.094 periodos de 2023, 30.869 componentes, cinco folds, T0 y C0 de las tandas anteriores. B13 usa un subconjunto exacto de F0; conserva el capital dudoso enmascarado, sin clima ni factores transferidos. El objetivo es tasa T0/e, peso sqrt(e), con predicción observada e×tasa. Se comprobó la identidad de pérdida que justifica esa ponderación. Los originales y las doce tablas OOF anteriores permanecen exactos. Se ajustaron quince GLM y treinta constantes, sin factores o mezclas posteriores. Acumulado: ochenta estimadores base y sesenta constantes; estrés y adaptadores históricos siguen identificados con su linaje.

## Resultados OOF de 2023

Observado total 15,297 millones CU; nuevo negocio 1,528 millones. A/E significa observado/predicho. D² es Tweedie1,5 sobre importes con nulo global, no media de los ramos.

| Receta | D² global | Predicho, millones CU | A/E global | D² nuevo negocio | A/E nuevo negocio |
| --- | ---: | ---: | ---: | ---: | ---: |
{table}

B12 mejora 0,00633 puntos frente a B00; B13 mejora 0,01180 frente a B12. Ambos contrastes tienen intervalos exploratorios que incluyen cero y ventajas que se invierten al retirar sus 31 grupos más favorables. La cercanía global de A/E a uno no acredita calibración futura, último o suficiencia de reservas.

| Comparación | Delta D² | Intervalo exploratorio 95 % | Delta tras retirar sus 31 grupos favorables |
| --- | ---: | --- | ---: |
{pairtab}

Se guardaron 91 parejas con 2.000 sorteos comunes por componente. Son exploratorias y no corrigen la búsqueda adaptativa entre catorce recetas, multiplicidad o cambio de población. B13 tiene menor punto global que B08, con intervalo de la diferencia que cruza cero; esto no prueba equivalencia ni autoriza retirar ninguna alternativa.

| Ramo, D² | B00 | B12 | B13 |
| --- | ---: | ---: | ---: |
{linetab}

B13 mejora los puntos de los tres ramos frente a B12. Edificios tiene A/E global1,0005, pero en edificios nuevos D²0,05022 sigue por debajo del 0,06523 de B00, aunque supera 0,03542 de B12. Autos nuevos sigue con D² negativo (−0,01004) y A/E0,879; contenidos nuevos tiene A/E1,184 y D²0,15363. La renovación agregada B13 tiene A/E1,0019 y D²0,08293. El diagnóstico por celdas sigue siendo necesario; solo hay40/36 positivos nuevos en edificios/contenidos.

## Qué quedó comprobado

Pasaron {fixtures['passed']} casos focales y {v['passed']} controles del [comprobador separado]({rp}/verifications/{vp.name}), con solapamiento. El comprobador no importa el productor y bloquea fit/fit_transform durante replay. Reconstruye constantes con suma compensada, pérdida por fórmula general, gradiente GLM en unidades totales y diferencias finitas; coteja parámetros efectivos, mediana/escalado/categorías aprendidos en ajuste, disjunción de grupos, predicciones sin respuestas, métricas/segmentos/escenarios e influencia. Se reconstruyeron numéricamente los 25 contrastes nuevos; las parejas anteriores se conservan mediante OOF exacto, utilidad y sorteos idénticos, sin repetir sus suites completas.

Los casos adversos rechazan2024, test, repetición de claves, segmentos inválidos, costes negativos, exposición inválida y ajustes sobre el fold retenido. Todos los quince GLM convergieron dentro del máximo y pasaron gradiente. El [informe íntegro]({rp}/report.json), [manifiesto]({rp}/manifest.json), [casos focales]({rp}/fixture_checks.json) y [valoración]({rp}/assessment.json) conservan cifras y fuentes. Estas son verificaciones propias de Codex, no validación profesional independiente ni aprobación humana.

## Decisiones y trabajo siguiente

Se conserva B00 y B01–B13. No se promueve, retira, congela lista final o abre2024. Tampoco se añaden interacciones, modelos por peligro, transferencia o boosting por estos resultados. Primero se revisará la evidencia recibida de CLA-S2-20261023-003: capital por fila, alcance temporal del clima y estimación de credibilidad/calibración dentro del fold. La versión que usa clima2024 para2023 requiere declarar retrospectividad; los factores estimados con todo2023 no pueden validar esos mismos folds como una prueba nueva. Las decisiones y tablas de Claude conservan su autoría y se integrarán únicamente mediante una receta y revisión propias del cambio.

Después se tratará el problema residual de nivel/cola con una prueba que pueda refutar la explicación, antes de escalar complejidad. El [plan de la noche](PLAN_NOCTURNO_20261023.md) y su índice evitan repetir trabajo ya concluido sobre fuentes idénticas. Cada ciclo conserva decisiones, fallos, verificaciones y pendientes y comunica un progreso breve. A las07:00 de Bogotá concluye esta ventana con un balance honesto.

Continúan los supuestos de observación T0/C0, reservas, reporte, datos físicos sin fecha y representatividad del negocio transferido. Se aplican las [prácticas IAA](../../../../Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md) de gobernanza §2.8 y §§3.3.2,3.4–3.6, documentación §§2–3 y comparación de segmentos de consideraciones profesionales §3.3, sin presentar cumplimiento o equidad certificados. No hay predicciones/scores/precios de2024 o test, ledger, envíos, cómputo remoto, publicación externa o delegación en esta unidad.
'''
with docpath.open('x',encoding='utf-8') as f:f.write(doc)
history=copy.deepcopy(idx['history']);history[-1].update(index_snapshot=rel(snapshot),index_sha256=sha(snapshot))
index={'id':plan['id'],'author':'Codex','as_of_utc':datetime.now(timezone.utc).isoformat(),'path_base':'workspace_root','status':'five_2023_trials_verified_standard_models_first_reference_retained',
 'run':rel(RUN),'documentation':rel(docpath),'training_years':[2023],'scored_years':[2023],'rows_per_model':50094,'groups':30869,'folds':5,
 'new_base_estimator_fits':15,'new_closed_form_constants':30,'new_postfit_factors':0,'cumulative_base_estimator_fits':80,'cumulative_closed_form_constants':60,
 'cumulative_candidate_level_factors':90,'models_consulted':list(points),'summary':report['summary'],'primary_contrasts':contrasts,'reference':'W2-B00','alternatives_preserved':list(points)[1:],
 'promotion':False,'confirmation_2024_open':False,'confirmation_closed_by_current_user_instruction':True,'final_confirmation_roster_frozen':False,
 'history':history+[{'id':plan['id'],'run':rel(RUN),'documentation':rel(docpath)}],'forum_prior':'COD-S2-20261023-016','forum_result':'COD-S2-20261023-017',
 'submissions':0,'professional_independent_validation':False,'selector_status_not_assessed_here':True,'night_continuation_index':'Hackaton/Repositorio_IAA2026/registro/semana2_continuidad_nocturna.json',
 'verification':{'path':rel(vp),'sha256':sha(vp),'passed':v['passed'],'failed':0},'fixtures':{'path':rel(RUN/'fixture_checks.json'),'sha256':sha(RUN/'fixture_checks.json'),'passed':fixtures['passed'],'failed':0}}
for key,path in [('report',RUN/'report.json'),('plan',REPO/'registro/semana2_desarrollo2023_plan_v5.json'),('producer',ROOT/plan['code']),('oof',RUN/'oof_2023.parquet'),('manifest',RUN/'manifest.json'),('assessment',RUN/'assessment.json'),('decision_journal',RUN/'decision_journal.json')]:index[key]=rel(path);index[key+'_sha256']=sha(path)
dump(RUN/'active_index_proposed.json',index)
body=f'''Codex. Resultado de COD-S2-20261023-016, primera unidad de la nueva continuidad nocturna autorizada. [Informe](../../Repositorio_IAA2026/docs/semana2/DESARROLLO_2023_MODELOS_ESTANDAR.md), [plan de la noche](../../Repositorio_IAA2026/docs/semana2/PLAN_NOCTURNO_20261023.md) e [índice de continuidad](../../Repositorio_IAA2026/registro/semana2_continuidad_nocturna.json).

B12 es la referencia con constantes por ramo y nuevo negocio/renovación; B13 es GLM Tweedie1,5 log sin penalización, seis predictores técnicos por ramo, sin interacciones. Los treinta niveles y quince GLM se ajustaron solo en los folds de2023; transformaciones fit-only. Mismos50.094periodos,30.869componentes,T0/C0, con B00–B11 exactos. Capital enmascarado vigente; sin clima o transferencia. No se añadieron factores o mezclas tras ver resultados.

| Receta | D² global | Predicho millones CU | A/E global | D² nuevo negocio | A/E nuevo negocio |
| --- | ---: | ---: | ---: | ---: | ---: |
{table}

Observado global15,297millonesCU, nuevo1,528. Los resultados globales cercanos en nivel no acreditan último o suficiencia de reservas. B13 mejora puntos de los tres ramos respecto de B12, pero no es una mejora establecida sobre B00/B12; B08 conserva mayor punto global sin que esto retire otra alternativa.

| Comparación | Delta D² | Intervalo exploratorio95% | Delta tras retirar31grupos favorables |
| --- | ---: | --- | ---: |
{pairtab}

Los intervalos de B12/B00 y B13/B12 incluyen cero y sus ventajas se invierten tras retirar31grupos favorables de evaluación con modelos fijos. No se recortaron esos grupos del entrenamiento o score primario. Las91parejas y2.000sorteos comunes son exploratorias tras14recetas adaptativas, sin corrección por búsqueda/multiplicidad. No promoción o equivalencia.

B13 edificios global A/E1,0005 no elimina la pérdida de edificios nuevos frenteB00: D²0,05022 frente0,06523; supera0,03542 deB12. Autos nuevos D²−0,01004/A-E0,879 y contenidos nuevos0,15363/1,184 conservan asuntos de forma/nivel. Continúan pocos positivos en hogar nuevo. No se justifica añadir complejidad por este corte.

Pasaron {fixtures['passed']} casos focales y {v['passed']} controles propios separados con solapamiento. Cotejo de fuentes/filas/particiones, fórmulas, constantes, gradientes y diferencias finitas, imputación/escalado/categorías de ajuste, replay sin fit, invariancia a respuestas, métricas/segmentos/escenarios,25contrastes nuevos e influencia. Máximo gradiente4,843e-6 con umbral técnico1e-4 fijado en fuente antes de ajustar. El [registro de decisiones](../../{RUN.relative_to(ROOT/'Hackaton').as_posix()}/decision_journal.json) vincula cada decisión con evidencia, prueba y consecuencia. Es revisión propia de Codex, no profesional independiente ni aprobación humana.

La automatización nativa quedó ACTIVE en este mismo chat, cada hora de19:00 a07:00Bogotá, con término24oct12:00UTC; requiere equipo/aplicación disponibles. No se alteraron otras automatizaciones. Cada ejecución registra trabajo terminado/pendiente y da un avance; no repite suites o entrenamiento de fuentes idénticas para acumular pases.

Se mantiene B00 y B01–B13. Siguiente unidad: revisar tablas/evidencia CLA003 de capital y los ámbitos temporales/fold de clima y credibilidad antes de integrarlos. Conservan autoría y decisiones referidas de Claude; no se adoptan como instrucciones de otro chat o se aplican factores de todo2023 a sus mismos folds como validación nueva. 2024 sigue expresamente cerrado, sin ledger, precios/predicciones/scores o test; no envíos, remoto, publicación externa, delegación o lista final. Los supuestos del último y la revisión humana siguen pendientes.
'''
with (ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v5_resultado.md').open('x',encoding='utf-8') as f:f.write(body)
print(json.dumps({'documentation':rel(docpath),'decision_journal':rel(RUN/'decision_journal.json'),'passed':v['passed'],'fixtures':fixtures['passed'],'failed':0}))
