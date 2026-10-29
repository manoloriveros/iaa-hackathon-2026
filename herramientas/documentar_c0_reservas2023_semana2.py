"""Lectura actuarial y registro propuesto; sin modelos, inferencia o bootstrap nuevos."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,hashlib
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('mechanism_document_reader',REPO/'herramientas/verificar_desarrollo2023_semana2.py');c=importlib.util.module_from_spec(s);sys.modules[s.name]=c;s.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq;rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,o):
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
run=Path(sys.argv[1]).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023');r=c.read(run/'report.json');p=c.read(run/'plan_snapshot.json');ver=sorted((run/'verifications').glob('c0_*.json'))[-1];fixtures=run/'fixture_checks.json'
assert c.read(ver)['failed']==c.read(fixtures)['failed']==0
claims=pq.read_table(run/'inputs_2023/claims_2023.parquet').to_pandas();new=pq.read_table(run/'mechanism_oof_2023.parquet').to_pandas();old=pq.read_table(run/'base_oof_2023.parquet').to_pandas();checks=[]
checks.append({'name':'2023 net and reserve cents identities','pass':bool((claims.T0_cents==claims.incurred_cents-claims.recoveries_cents).all() and (claims.reserve_cents==claims.incurred_cents-claims.paid_cents).all())})
profiles=[]
for line,g in claims.groupby('line'):
    late=g.delay.gt(365);records=[x for x in r['late_reporting'] if x['line']==line];profiles.append({'line':line,'claims':len(g),'observed_net':float(g.T0_cents.sum()/100),'reserve':float(g.reserve_cents.sum()/100),
      'late_positive_claims':int((late&g.T0_cents.gt(0)).sum()),'late_net':float(g.loc[late,'T0_cents'].sum()/100),'late_reserve':float(g.loc[late,'reserve_cents'].sum()/100),
      'late_cost_fraction':float(g.loc[late,'T0_cents'].sum()/g.T0_cents.sum()),'unique_selected_components':len({x['removed_group'] for x in records if x['removed_group'] is not None}),
      'removed_late_cost_min':min(x.get('removed_late_cost',0.) for x in records),'removed_late_cost_max':max(x.get('removed_late_cost',0.) for x in records)})
total_net=float(claims.T0_cents.sum()/100);total_reserve=float(claims.reserve_cents.sum()/100);by={x['stress_id']:x for x in r['summary']}
for scenario,b in [('R075',.75),('R125',1.25)]:checks.append({'name':'Aggregate reserve scenario '+scenario,'pass':bool(np.isclose(by[scenario+'_W2-B00']['observed_total'],total_net+(b-1)*total_reserve))})
e_profiles=[]
base=old[old.model_id.eq('W2-B00')][c.KEY+['e_cost_mix_1.0']]
for scenario in ['R075','R125','L1']:
    q=new[new.scenario.eq(scenario)&new.model_id.eq('W2-B00')].merge(base,on=c.KEY,validate='one_to_one');checkratio=q.effective_exposure/q['e_cost_mix_1.0']
    checks.append({'name':'Completion bounds '+scenario,'pass':bool(q.effective_exposure.gt(0).all() and (q.effective_exposure<=q.exposure+1e-10).all())})
    for line,g in q.groupby('line'):
        ratio=g.effective_exposure/g['e_cost_mix_1.0'];e_profiles.append({'scenario':scenario,'line':line,'ratio_min':float(ratio.min()),'ratio_median':float(ratio.median()),'ratio_max':float(ratio.max()),'effective_total_ratio':float(g.effective_exposure.sum()/g['e_cost_mix_1.0'].sum())})
recon={'author':'Codex','scope':'New interpretation arithmetic only, no refit/inference/bootstrap','utc':datetime.now(timezone.utc).isoformat(),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks}
assert recon['failed']==0;dump(run/'readout_reconciliation.json',recon);dump(run/'diagnostics/claim_lag_reserve_profile.json',{'claims_2023':profiles,'total_net':total_net,'total_reserve':total_reserve,'reserve_over_net':total_reserve/total_net,'exposure_profiles':e_profiles})
rows=[]
for scenario in ['R075','R125','L1']:
    for mid in ['W2-B00','W2-B12','W2-B14']:
        x=by[scenario+'_'+mid];rows.append(f"| {scenario} | {mid.replace('W2-','')} | {x['observed_total']/1e6:.4f} | {x['D2']:.6f} | {x['actual_over_expected']:.3f} | {x['conditional_nominal_2023']/1e6:.4f} | {x['nominal_relative_change']:+.3%} |")
rows='\n'.join(rows)
profile_table='\n'.join(f"| {x['line']} | {x['claims']} | {x['reserve']:,.2f} | {x['late_positive_claims']} | {x['late_cost_fraction']:.2%} | {x['unique_selected_components']} | {x['removed_late_cost_min']:,.0f}–{x['removed_late_cost_max']:,.0f} |" for x in profiles)
etab='\n'.join(f"| {x['scenario']} | {x['line']} | {x['ratio_min']:.6f} | {x['ratio_median']:.6f} | {x['ratio_max']:.6f} |" for x in e_profiles)
pairs=c.read(run/'diagnostics/pairs.json')['pairs'];pt='\n'.join(f"| {x['candidate']}/{x['reference']} | {x['delta_D2']:+.8f} | [{x['exploratory_lower95']:+.8f}; {x['exploratory_upper95']:+.8f}] | {x['delta_after_removal']:+.8f} |" for x in pairs)
received=ROOT/'Hackaton/Semana 2/Claude/validacion_datos_20261023/INFORME.md';received_evidence=ROOT/'Hackaton/Semana 2/Claude/validacion_datos_20261023/evidencia_validacion.json'
dump(run/'received_evidence_receipt.json',{'author_of_receipt':'Codex','original_author':'Claude','forum':'CLA-S2-20261023-004','scope':'Forum contribution read and source hashes recorded; did not rerun its74checks or adopt proposed feature changes.',
 'files':[{'path':rel(path),'sha256':c.sha(path)} for path in [received,received_evidence]],'professional_independent_validation':False})
warnings=[{'id':'C0R-RESERVE-TRUTH','status':'open','effect':'Reserve.75/1.25 are design stresses, not adequacy estimates or statistical bounds. Target changes; cross-target D2 is not a superiority contrast.'},
 {'id':'C0R-LATE-INFLUENCE','status':'open','effect':'L1 is a reporting-estimator-only component removal stress. Small positive observed-score gains reverse after own31 favorable groups; do not discard costly claims or adopt altered C0.'},
 {'id':'C0R-TAIL-UNIDENTIFIED','status':'open','effect':'Previous tail normalization preserves observedD2 while nominal2023 rises~2.5%; no identification of mass/severity beyond support. No new joint tail/reserve scenario fitted here.'},
 {'id':'C0R-MIXTURE','status':'open','effect':'Line-level peril mixture may differ by row/business; report/cost dependence, censoring and stationarity unresolved. Groups2023 at2024cutoff are not prospective at beginning2023.'},
 {'id':'C0R-SEARCH','status':'open','effect':'19 main recipes and successive conditional observation stresses;12new unadjusted exploratory contrasts, no temporal confirmation or final roster.'},
 {'id':'C0R-2024-CLOSED','status':'open','effect':'Participant keeps2024/test prices/predictions/scores closed and ledger absent, regardless of selector state.'}]
assessment={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'reserve_late_reporting_sensitivity_technically_verified_conditions_open','warnings':warnings,'reference':'W2-B00','promotion':False,'professional_independent_validation':False};dump(run/'assessment.json',assessment)
dump(run/'decision_journal.json',{'author':'Codex','utc':assessment['utc'],'preregistration':'COD-S2-20261024-025','decisions':[
 {'topic':'reserve marks','decision':'Matched target and C0 mark confirmed; no reservefactor chosen by target-changing D2 or A/E.'},
 {'topic':'late-report component','decision':'Keep selected component in pricefit and all scored rows; remove only reporting estimation to diagnose. Do not adopt exclusion as data cleaning.'},
 {'topic':'aggregate level','decision':'Preserve separate observed/conditionalnominal readouts. Scenario movements do not form confidence limits or combine additively with tail scenarios.'},
 {'topic':'standard models','decision':'Same constants and six-feature alpha0 GLM suffice to reveal these mechanisms. No documented need to add trees/interactions from this evidence.'},
 {'topic':'received validation','decision':'Record CLA004 authorship/scope without rerunning unchanged checks or declaring professional validation. Proposed feature changes not adopted in this recipe.'},
 {'topic':'next unit','decision':'Review the line-level peril-mixture approximation by business/technical support in2023 before considering more complex prices. Preregister any new estimates; prepare overnight balance.'},
 {'topic':'scope','decision':'B00/all alternatives and main19catalog retained.2024/test closed, no ledger/submission/remote/externalpublication/delegation.'}],
 'warnings':warnings,'verification':rel(ver),'fixtures':rel(fixtures),'readout_reconciliation':rel(run/'readout_reconciliation.json'),'professional_independent_validation':False})
doc=REPO/'docs/archivo/semana2/NIVEL_C0_REPORTES_Y_RESERVAS_2023.md'
text=f'''# Nivel agregado, C0 y reservas en 2023

Codex. Corte UTC {r['completed_utc']}. Con los mismos modelos estándar, las reservas al 75% y al 125% cambian el nivel nominal condicionado de B14 en −2,484% y +2,483%. Al retirar de C0 un componente con alto coste tardío por ramo/fold, conservándolo en el ajuste de precios, el nominal baja 0,658%. Los puntos positivos del score de ese adverso se invierten al retirar sus 31 grupos de evaluación más favorables. No se adopta una exclusión ni un factor de reservas.

## Continuidad con la cola y registro previo

La [prueba de cola terminada](SENSIBILIDAD_COLA_Y_NIVEL_2023.md) ya demostró un límite: renormalizar la mezcla permite aumentar alrededor de 2,5% el nominal condicionado de 2023 con exactamente el mismo score observado. Se conserva esa evidencia, sin repetir sus ajustes o remuestreo. Aquí no se ensaya una combinación de cola y reservas ni se suman sus cambios como si fueran efectos independientes o límites estadísticos.

El [plan de C0 y reservas](../../registro/semana2_c0_reservas2023_plan_v1.json) y el comentario COD-S2-20261024-025 preceden a la ejecución. Misma población: 50.094 periodos de 2023, 30.869 componentes cliente-dirección y cinco folds. B00 es constante por ramo; B12 usa constantes por ramo y negocio; B14 mantiene seis variables, Tweedie 1,5, enlace log y alpha0. La respuesta es T_s/e_s y el peso sqrt(e_s); la predicción observada multiplica e_s una vez. No hay nuevas variables, ajuste de credibilidad, clima, cambio de capital o calibración.

R075/R125 usan T_s=T0+(b−1)reserva con b=0,75/1,25 y sus enlaces de marcas de coste correspondientes, ya aprendidos en el ajuste propio de cada fold. Se mantienen las recuperaciones observadas. Cambiar el target cambia también la devianza nula: los D² de escenarios distintos no se comparan como un concurso sobre el mismo resultado.

L1 conserva T0. En cada ramo/fold se escoge dentro del ajuste el componente con mayor coste positivo de siniestros con demora superior a 365 días; el empate se resuelve por ID. Se retiran todas sus reclamaciones y sus exposiciones de la estimación de C0, se reestiman las mismas curvas de truncamiento inverso y se recalculan los pesos por peril. Todos los periodos originales siguen en el ajuste de precios, incluido ese componente. El retenido no aporta selección o estimación. Es una perturbación de la primera etapa, distinta del estrés anterior que retiraba grupos del ajuste de precios dejando C0 fijo. No es una limpieza de datos o reajuste integral del pipeline.

## Reservas y coste tardío de este corte

Los siniestros asignados de 2023 suman {total_net:,.2f} CU netos y {total_reserve:,.2f} CU de reserva, el {total_reserve/total_net:.3%} del neto. Se conciliaron neto=incurrido−recuperaciones y reserva=incurrido−pagado, en centavos. Los escenarios de respuesta suman {by['R075_W2-B00']['observed_total']/1e6:.6f} y {by['R125_W2-B00']['observed_total']/1e6:.6f} millones CU. Esto no confirma suficiencia de reservas o recuperaciones futuras.

| Ramo | Siniestros asignados | Reserva 2023, CU | Positivos con demora >365 días | Peso del coste tardío | Componentes distintos elegidos | Coste tardío retirado por fold, CU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{profile_table}

Los componentes pueden repetirse en varios folds: no se suman esos importes como costes únicos de cartera ni como experimentos independientes. Los identificadores y las filas permanecen privados. En contenidos, las reservas de estos periodos de 2023 son cero; R075/R125 no cambian su respuesta ni enlace y sus treinta modelos se reutilizan byte a byte. Esto no generaliza a otros años o a todo el ramo futuro.

## Sensibilidad del enlace y del nivel

Los cocientes siguientes usan solo las filas de validación de 2023, una vez cada una, y comparan su exposición efectiva con C0 base. Las reservas también cambian la marca de coste que pesa cada retraso. L1 puede cambiar el soporte y la normalización de las curvas; un incremento de completitud al perder observaciones no significa mayor conocimiento de la cola.

| Escenario | Ramo | Mínimo e_s/e_base | Mediana | Máximo |
| --- | --- | ---: | ---: | ---: |
{etab}

| Escenario | Modelo | Respuesta total, millones CU | D² bajo su target | A/E | Nominal condicionado2023, millones CU | Cambio nominal frente a su base |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
{rows}

El nominal de B14 base es 15,606084 millones CU, frente a 15,218380 en R075, 15,993601 en R125 y 15,503358 en L1. Es exposición nominal de los mismos periodos de 2023 por su tasa bajo coste completo, no precio de 2025/test o etiqueta última. Un A/E agregado cercano a uno no acredita el supuesto de reservas o cola. Las pérdidas por ramo, fold y negocio se conservan en el anexo, sin ocultarlas con el promedio global.

## Comparaciones que sí comparten resultado

Solo se añadieron doce contrastes: tres entre familias dentro de cada escenario y tres L1 frente a sus padres sobre el mismo T0. Cada escenario tiene su propia nula y sus 2.000 sorteos comunes de componentes. No hay contrastes de superioridad entre targets R075/R125 y T0 base, ni repetición de las 171 parejas históricas o de la prueba de cola.

| Contraste | Delta D² | Intervalo exploratorio95% | Delta sin 31 grupos favorables |
| --- | ---: | --- | ---: |
{pt}

L1/B14 da +0,00007145, con intervalo exploratorio [+0,00000100; +0,00017868], y −0,00004881 tras retirar sus 31 componentes de evaluación más favorables. Lo mismo ocurre con el signo de las ventajas de L1/B00 y L1/B12. No se debe elegir una regla para eliminar información de reporte porque el punto observado mejore. La selección del componente de estrés se hizo dentro del ajuste; los grupos de influencia son un diagnóstico posterior de evaluación, no se borran ni se usan para volver a ajustar.

Las familias dentro de cada escenario se comparan bajo el mismo target/enlace. Sus intervalos siguen siendo exploratorios tras búsqueda adaptativa, sin corrección simultánea o confirmación temporal. No se promueven, retiran o declaran equivalentes alternativas ni se congela una lista final.

## Comprobación, autoría y condiciones

La ejecución completó {r['new_price_GLM_fits']} GLM nuevos, {r['new_closed_form_constants']} constantes cerradas, {r['exact_reuses']} reutilizaciones exactas y {r['new_reporting_peril_fits']} curvas de reporte nuevas, estas últimas separadas de los ajustes de precio. No hubo nuevos auxiliares de credibilidad. El contador propio queda en {r['cumulative_price_base_fits']} ajustes de precio y {r['cumulative_closed_form_constants']} constantes; los 30 auxiliares anteriores conservan su contador separado. La ejecución terminó sin corrección de receta o reintento.

Pasaron {c.read(ver)['passed']} controles separados, {c.read(fixtures)['passed']} adversos focales y {recon['passed']} conciliaciones adicionales de la lectura, con solapamiento. El comprobador no importa el productor y bloquea fit. Recalcula el truncamiento como producto de probabilidades, las marcas por retraso, la completitud contando directamente días de cobertura admisibles, los pesos por peril y la exclusión de exposiciones/reclamaciones. Comprueba el óptimo de constantes por minimización escalar, parámetros/gradientes de GLM, imputación del ajuste, exp(X beta), centavos, ámbitos, métricas, segmentos y los doce remuestreos por multiplicidades. Los adversos prueban envenenamiento del retenido sin cambiar la selección, empates, frontera estricta de 365 días, ausencia de coste tardío sin fit, rechazo de 2024/test/duplicados y que costes/IDs no entren en la predicción. No se repitieron controles históricos sin cambios.

Se recibió CLA-S2-20261023-004 de Claude. Se conserva su autoría y se registraron las huellas de su informe/evidencia sin repetir sus 74 controles o adoptar cambios de variables dentro de esta receta. Su validación de datos no valida estos modelos, el último o una revisión profesional. La reserva del 17,8% que refiere sobre ambos años no sustituye el porcentaje de 2023 calculado arriba.

Sigue pendiente identificar severidad/masa fuera del soporte, estacionariedad, dependencia coste/reporte y adecuación de reservas. C0 aproxima una mezcla por ramo que puede variar según fila/negocio. La validación agrupada de 2023 al corte 2024-12-31 no representa información disponible al comienzo de 2023. Capital, clima y prior de credibilidad mantienen sus condiciones; no se cierran hallazgos ajenos. La siguiente unidad revisará esa aproximación de mezcla por peril y negocio antes de considerar precios más complejos, con receta previa si hay estimaciones nuevas, y preparará el balance nocturno.

B00 y B01–B18 se conservan; el catálogo principal queda exacto. Las nueve configuraciones de esta unidad son sensibilidad del mecanismo de observación y se registran aparte. 2024 permanece cerrado por instrucción directa, sin ledger, entrenamiento de precio, predicciones o scores de ese año o test. Sin remoto, envíos, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. Es revisión técnica propia de Codex, no profesional independiente.

## Evidencia

- [Resultados](../../{run.relative_to(REPO).as_posix()}/report.json), [decisiones](../../{run.relative_to(REPO).as_posix()}/decision_journal.json).
- [Comprobador separado](../../{ver.relative_to(REPO).as_posix()}), [adversos](../../{run.relative_to(REPO).as_posix()}/fixture_checks.json).
- [Perfil de reservas, demoras y enlace](../../{run.relative_to(REPO).as_posix()}/diagnostics/claim_lag_reserve_profile.json).
- [Aporte de Claude recibido](../../../Semana%202/Claude/validacion_datos_20261023/INFORME.md), [foro](../../../Semana%202/Foro/FORO.md).
'''
with doc.open('x',encoding='utf-8') as f:f.write(text)
body=f'''Codex. Cierre de025, revisión de nivel, cola, reportes tardíos y reservas solo2023 con modelos estándar. [Informe](../../Repositorio_IAA2026/docs/archivo/semana2/NIVEL_C0_REPORTES_Y_RESERVAS_2023.md), [decisiones](../../Repositorio_IAA2026/{run.relative_to(REPO).as_posix()}/decision_journal.json).

La cola de024 se conserva sin repetirla: otro nominal condicionado con el mismo score observado, sin identificación del último. Aquí R075/R125 cambian coherentemente tanto T0+(b−1)reserva como el C0 de marcas/pesos por peril. L1 mantieneT0 y retira del ajusteC0 el componente de mayor coste tardío>365días por ramo/fold (solo dentro del ajuste). Se retiran sus reclamaciones y exposición de C0, pero se mantienen todos sus periodos en el ajuste de precios. No se propone limpiar siniestros caros.

| Escenario | Modelo | Respuesta total, millones CU | D² bajo su target | A/E | Nominal condicionado2023, millones CU | Cambio nominal frente a su base |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
{rows}

B14 nominal base15,606084millonesCU pasa a15,218380/15,993601 con reservas0,75/1,25 (−2,484%/+2,483%) y15,503358 enL1 (−0,658%). Son periodos2023×tasa bajo coste completo, no precios2025/test o etiquetaúltima. Reserva2023{total_reserve:,.2f}CU/{total_net:,.2f}neto={total_reserve/total_net:.3%}; no se confunde con17,8%deambosaños referido porClaude. En contenidos2023reserva=0: treinta copias exactas enlosdosescenarios, sin refit redundante.

Docecontrastes nuevos con2.000sorteoscomunes y nula propia del target: tresfamilias dentrodecadaescenario, másL1frenteasuspadresT0. No se comparan D² de targetsdistintos como superioridad. L1/B14delta+0,00007145 intervalo95%[+0,00000100;+0,00017868], pero cambia a−0,00004881alretirar31gruposfavorables; L1/B00/B12también invierten signo. Son diagnósticos de evaluación, no grupos eliminados o usados para retocar precios. Lascomparaciones completas están enelinforme; sin promoción/retiro/equivalencia/listafinal o adopción de reserva/curva por punto.

Se completaron35GLM/105constantes nuevos,30reusos exactos y75curvasdereporte separadas;0auxiliares nuevos. Contador propio135ajustesprecio/195constantes,30auxiliares previos aparte. Pasaron1.477controles separados,48adversos y6conciliaciones de lectura, solapados. Producto inverso deprobabilidades y díasadmisibles reconstruyenC0 porotro método; marcas/centavos, óptimos/gradientes, exp(Xbeta), fuentes/ámbitos, segmentos y12bootstrap con multiplicidades. Replay sinfit; sin reintento o cambio de receta. Revisión técnica propia,noprofesional independiente.

Recibí CLA-S2-20261023-004 y registré sus fuentes/autoría sin repetir74controles o adoptar propuestas en esta receta. Su revisión de datos no valida este modelo o elúltimo. Siguen abiertas masa/severidad fuera de soporte, reservas, dependencia coste/reporte, estacionariedad y aproximación porramo; escenarios separados no son cotas estadísticas o efectos aditivos. La siguiente unidad revisará mezcla porperil/negocio antesdecomplejizar, con receta previa y balance nocturno.

B00 yB01–B18 intactos, catálogo principal exacto; sensibilidades en índice aparte.2024cerrado explícitamente, sin ledger/precios/predicciones/scores deeseaño otest; sin envíos, remoto, publicación externa, nuevoschats o delegación. Otras automatizaciones intactas.
'''
with (ROOT/'Hackaton/Semana 2/Codex/c0_reservas2023_resultado.md').open('x',encoding='utf-8') as f:f.write(body)
idx={'id':p['id'],'author':'Codex','as_of_utc':assessment['utc'],'path_base':'workspace_root','status':'reserve_late_reporting_sensitivity_verified_conditions_open','run':rel(run),'documentation':rel(doc),
 'main_model_index_preserved':p['main_model_index'],'main_model_index_sha256':p['main_model_index_sha256'],'prior_sensitivity_index_snapshot':'Hackaton/Repositorio_IAA2026/registro/semana2_sensibilidad_observacion_cola_v1_snapshot.json',
 'prior_sensitivity_index_sha256':p['prior_sensitivity_index_sha256'],'training_years':[2023],'scored_years':[2023],'rows_per_stress':50094,'groups':30869,'folds':5,
 'new_price_GLM_fits':r['new_price_GLM_fits'],'new_closed_form_constants':r['new_closed_form_constants'],'exact_reuses':r['exact_reuses'],'new_reporting_peril_fits':r['new_reporting_peril_fits'],
 'cumulative_price_base_fits':r['cumulative_price_base_fits'],'cumulative_closed_form_constants':r['cumulative_closed_form_constants'],'prior_auxiliary_fits_not_recounted':30,
 'stress_configurations':[x['stress_id'] for x in r['summary']],'summary':r['summary'],'new_exploratory_pairs':12,'main_catalog_candidates':19,'main_catalog_pairs_preserved':171,
 'reference':'W2-B00','all_alternatives_preserved':True,'promotion':False,'confirmation_2024_open':False,'test_predictions':0,'professional_independent_validation':False,
 'forum_prior':['COD-S2-20261024-025'],'forum_result':'COD-S2-20261024-026','warnings':warnings}
for key,path in [('report',run/'report.json'),('plan',REPO/'registro/semana2_c0_reservas2023_plan_v1.json'),('producer',ROOT/p['code']),('oof',run/'mechanism_oof_2023.parquet'),('manifest',run/'manifest.json'),('assessment',run/'assessment.json'),('decision_journal',run/'decision_journal.json')]:idx[key]=rel(path);idx[key+'_sha256']=c.sha(path)
for key,path in [('verification',ver),('fixtures',fixtures),('readout_reconciliation',run/'readout_reconciliation.json')]:idx[key]={'path':rel(path),'sha256':c.sha(path),'passed':c.read(path)['passed'],'failed':0}
dump(run/'sensitivity_index_proposed.json',idx);print(json.dumps({'documentation':rel(doc),'profile':profiles,'net':total_net,'reserve':total_reserve,'reserve_fraction':total_reserve/total_net,'readout_checks':recon['passed'],'summary':r['summary']}))
