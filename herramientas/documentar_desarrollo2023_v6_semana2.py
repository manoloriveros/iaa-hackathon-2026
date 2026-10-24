"""Valoración, decisiones y documentación del ensayo controlado de integraciones."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1];RUN=REPO/'privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,obj):
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
r=read(RUN/'report.json');plan=read(RUN/'plan_snapshot.json');vp=sorted((RUN/'verifications').glob('*.json'))[-1];v=read(vp);fixtures=read(RUN/'fixture_checks.json');assert v['failed']==fixtures['failed']==0
points={x['model_id']:x for x in r['summary']};segments=read(RUN/'diagnostics/segments.json');seg=lambda m,d,l:next(x for x in segments if x['model_id']==m and x['segment']==d and x['label']==l)
impact=read(RUN/'diagnostics/capital_row_impact.json')['records'];affected=[x for x in impact if x['corrected_rows']]
assert sum(x['rows'] for x in affected)==56 and sum(x['T0'] for x in affected)==0
assert abs(sum(x['gain_in_deviance'] for x in impact)-(points['W2-B13']['deviance_sum']-points['W2-B14']['deviance_sum']))<1e-6
assert abs(sum(x['new_predicted']-x['old_predicted'] for x in impact)-(points['W2-B14']['predicted_total']-points['W2-B13']['predicted_total']))<1e-6
dump(RUN/'diagnostics/capital_impact_verification.json',{'scope':'Additional row-effect summary only, no fitting/statistical repetition','passed':3,'failed':0,'checks':['56 affected and all T0zero','deviance contributions reconcile full B13/B14 difference','predicted totals reconcile full B13/B14 difference']})
for item in plan['frozen_received_sources']:
    p=ROOT/item['path'];assert sha(p)==item['sha256']
    if p.suffix=='.py':(RUN/('received_'+p.name)).write_bytes(p.read_bytes())
assessment={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','reference_retained':'W2-B00','alternatives_preserved':list(points)[1:],
 'promotion':False,'confirmation_2024_open':False,'final_confirmation_roster_frozen':False,'professional_independent_validation':False,
 'decisions':{'capital':'Passed arithmetic/training-scope checks and tested in B14 only. Do not claim economic confirmation or row-level immateriality.',
  'climate':'CLIMA-S2-01 not admitted to prospective feature contract; no historical weather prior to2023 available. No leaked-price comparator trained.',
  'credibility':'B15 preserved as conditional alternative; no demonstrated overall improvement. Emerging estimates fit-only, frozen developed prior not independently refitted here.'},
 'warnings':[
 {'id':'DEV6-CAPITAL-MATERIAL-ROWS','status':'open','class':'condition','effect':'56 corrected2023 rows have no positiveT0; predicted rates change -62.36% to+154.09% against masked imputation. Tiny portfolio metric effect does not prove per-policy immateriality, capital currency or economic truth.'},
 {'id':'DEV6-CLIMATE-TEMPORAL','status':'open','class':'block','effect':'2024 values for2023 and selector dependence on2025; keep current variant outside prospective pricing. Retain owner finding S2-VAL-DAT-003 without closing it.'},
 {'id':'DEV6-CRED-PRIOR','status':'open','class':'condition','effect':'Frozen developed2021-2023 prior is received evidence, not independently reproduced. Z ignores prior-estimation uncertainty and tau uses correlated coefficients; transfer/ultimate/Janfleet remain unknown.'},
 {'id':'DEV6-CRED-GAIN','status':'open','class':'condition','effect':'B15/B14 point negative, CI crosseszero; motor-new worsens while home-new improves. No general improvement or promotion.'},
 {'id':'DEV6-SEARCH','status':'open','class':'condition','effect':'120 unadjusted exploratory pairs after16 adaptive pricing recipes plus received research; no temporal confirmation.'},
 {'id':'DEV6-2024-CLOSED','status':'open','class':'block','effect':'Explicit current participant instruction; no opening or final roster.'}]}
dump(RUN/'assessment.json',assessment)
journal={'id':'S2-NOCHE-CICLO-02','utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','authorization_literal':plan['authorization_literal'],
 'decisions':[
 {'id':'I01-CAPITAL','decision':'Test row-wise /1000 with bounds fitted on outer-training2023 only','evidence':[rel(ROOT/plan['diagnostic_review']),rel(RUN/'diagnostics/capital_row_impact.json'),rel(vp)],'result':'technical_checks_passed_economic_scale_not_confirmed','consequence':'Preserve B14; no blanket global F0/test integration or per-row immateriality claim'},
 {'id':'I02-CLIMATE','decision':'Reject proposed current climate block from prospective price features','evidence':[rel(ROOT/plan['diagnostic_review']),rel(RUN/'fixture_checks.json')],'result':'temporal_guard_rejects2024_values_and2025_selector','consequence':'No weather comparator; need dated pre-quote history or separately declared retrospective purpose'},
 {'id':'I03-CRED-SCOPE','decision':'Re-estimate emerging Poisson/Gamma/SE/tau in each outer-training2023 scope, direct c on B14','evidence':[rel(RUN/'auxiliary/developed_prior_snapshot.json'),rel(vp)],'result':'30auxfits/15factors_and_sandwich_algebra_verified','consequence':'No full2023 c or ordinary other-fold OOF A/E calibration; prior condition remains'},
 {'id':'I04-CRED-READOUT','decision':'Keep conditional credibility alternative without promotion','evidence':[rel(RUN/'diagnostics/pairs.json'),rel(RUN/'diagnostics/segments.json')],'result':'overall_gain_unestablished_motor_new_adverse_home_new_improved','consequence':'Preserve B00/B14/B15, no adaptive c tuning or default takeover'},
 {'id':'I05-VALIDATION','decision':'Verify real consumer plus numerical formulas and temporal/ID adversaries','evidence':[rel(vp),rel(RUN/'fixture_checks.json')],'result':'832separate+26focusedchecks_passed_with_overlap','consequence':'Own technical review only, no independent professional validation'},
 {'id':'I06-HOLDOUT','decision':'Keep2024/test closed and preserve source/history','evidence':[rel(vp)],'result':'ledger_absent_and_2023_only','consequence':'No promotions/submissions/remote/delegation/final roster'}],
 'professional_independent_validation':False,'next_unit':'Investigate 2023 level/tail and reporting-link sensitivity with standard models; preregister any new experiment, do not retune c from these scores.'}
dump(RUN/'decision_journal.json',journal)
table='\n'.join(f"| {m} | {points[m]['D2']:.6f} | {points[m]['predicted_total']/1e6:.3f} | {points[m]['actual_over_expected']:.3f} | {seg(m,'business','new_business')['D2']:.5f} | {seg(m,'business','new_business')['actual_over_expected']:.3f} |" for m in ['W2-B00','W2-B13','W2-B14','W2-B15'])
contrasts=[x for x in r['pairs'] if (x['candidate'],x['reference']) in [('W2-B14','W2-B13'),('W2-B15','W2-B14'),('W2-B14','W2-B00'),('W2-B15','W2-B00')]]
pairtab='\n'.join(f"| {x['candidate']} / {x['reference']} | {x['delta_D2']:.8f} | [{x['exploratory_lower95']:.8f}; {x['exploratory_upper95']:.8f}] | {x['delta_after_removal']:.8f} |" for x in contrasts)
factortab='\n'.join('| '+line+' | '+' | '.join(f'{min(vals):.3f}–{max(vals):.3f}' for vals in [[x['ramos'][line]['c'] for x in r['credibility']],[x['ramos'][line]['Z_f'] for x in r['credibility']],[x['ramos'][line]['Z_s'] for x in r['credibility']]])+' |' for line in ['motor','buildings','contents'])
impacttab='\n'.join(f"| {x['line']} | {x['rows']} | {x['old_predicted']:.2f} | {x['new_predicted']:.2f} | {100*x['min_rate_change']:.2f} % a {100*x['max_rate_change']:.2f} % |" for x in affected)
cross='\n'.join('| '+label+' | '+' | '.join(f"{seg(m,'line_business',label)['D2']:.5f}" for m in ['W2-B13','W2-B14','W2-B15'])+' |' for label in ['motor_new_business','buildings_new_business','contents_new_business'])
rp='../../'+RUN.relative_to(REPO).as_posix();docpath=REPO/'docs/semana2/CAPITAL_CLIMA_CREDIBILIDAD_2023.md'
doc=f'''# Capital, clima y credibilidad antes de integrar

Codex, 23 de octubre de 2026. Capital supera la comprobación técnica por fila y se probó en el GLM estándar B14, pero el escaso efecto en el score agregado oculta cambios materiales en los registros corregidos. El clima propuesto queda fuera del contrato prospectivo. La credibilidad por fold se pudo reconstruir y probar como B15, con resultado global incierto y diferencias adversas en autos nuevos. Se conserva B00 y2024 permanece cerrado.

El [plan v6](../../registro/semana2_desarrollo2023_plan_v6.json), COD-S2-20261023-018, precede a todos los ajustes. La [revisión previa]({plan['diagnostic_review'].replace('Hackaton/Repositorio_IAA2026/','../../',1)}) no ajustó ni predijo precios. El resultado se registra en COD-S2-20261023-019 del [foro](<../../../Semana 2/Foro/FORO.md>). El [registro del ciclo]({rp}/decision_journal.json) conserva hipótesis, comprobación, resultado y consecuencia. Las fuentes de Claude y los hallazgos del otro encargo mantienen autoría y alcance.

## Capital: regla aplicada solo a la prueba de 2023

La tabla CAPS2-01 recibida tiene349filas de distintos años. Esta prueba materializó únicamente las56filas de2023 (26edificios,30contenidos). Todas estaban enmascaradas en F0 y tienen T0=0. Se cotejaron IDs, capital original y división por1000. No se presenta el análisis de todos los años de Claude como ejecutado por este chat.

Para evitar límites aprendidos con2024/test o con la distribución retenida, por cada ramo/fold se calcula el mínimo y máximo de prima por mil entre capitales normales del ajuste2023. Una fila sospechosa se divide solo si su propia prima por mil bruta está por debajo del mínimo y la corregida queda dentro de ese intervalo. Si falla permanece desconocida. Las56pasan también con estos límites de ajuste. Los umbrales son5millonesCU en edificios y2millones en contenidos, fijados en el plan. La prima escrita se usa como evidencia de escala y nunca entra en la matriz de predictores; esto conserva una dependencia de la tarifa y del supuesto de unidad monetaria, no confirmación económica independiente.

B14 mantiene exactamente las seis variables, alpha0, enlace log y transforms fit-only de B13. Se reentrenaron diez GLM de hogar y se copiaron exactamente los cinco modelos de autos. Solo cambia el valor de logcapital; no se edita el original o F0 global, ni se calcula una corrección/predicción para2024/test.

| Registros corregidos en OOF2023 | Filas | Predicho B13, CU | Predicho B14, CU | Rango relativo por fila |
| --- | ---: | ---: | ---: | --- |
{impacttab}

Estos son importes observados predichos de2023, comparados con la imputación anterior de capital desconocido. El rango conjunto es −62,36 % a+154,09 %. Cada fila OOF se evalúa una vez, aunque aparezca en varios ajustes. La suma predicha en los restantes registros cambia poco (menos de0,5 % por fila en hogar), pero eso no permite llamar inmaterial a la corrección por póliza. Tampoco sus56ceros pueden probar cuál escala reproduce la severidad esperada. La [descomposición por registros]({rp}/diagnostics/capital_row_impact.json) concilia exactamente los cambios de total y devianza.

## Clima: criterio temporal aplicado y prueba rechazada

CLIMA-S2-01 usa2024 para las filas2023 y elige las variables exigiendo persistencia también entre2024/2025. No basta con que los valores finales omitan2025: el selector depende de ese año. Se cotejó el hash del adverso de permutación recibido en COD-S2-VAL04-20261023-CLIMA-AVISO, sin repetir el ensayo sobre fuentes iguales ni adjudicar su autoría a este flujo.

Las guardas propias rechazan medidas del mismo año o posteriores a la cotización, selectores que dependan del futuro y ausencia de historia que se quiera rellenar con valores futuros. No hay filas climáticas emergentes anteriores a2023 que permitan materializar ese bloque para esta prueba. No se entrenó un comparador con fuga o un modelo artificialmente duplicado con todo el clima ausente. La variante queda fuera del contrato prospectivo actual; un uso como proxy físico condicionado o escenario requeriría otro alcance explícito y no constituiría backtest al momento de cotizar. El hallazgo S2-VAL-DAT-003 conserva su responsable y permanece abierto.

## Credibilidad: alcance corregido y probado

No se aplicó el c estimado con todo2023. Los factores recibidos por fold tienen una fórmula reconstruible, pero el script de aplicación sobre los otros OOF no aporta calibración interna anidada: las predicciones de un foldj distinto del retenidok se entrenaron con las etiquetas dek. Eliminar las filask del promedio final no elimina esa dependencia. La prueba evita por completo ese equilibrio A/E.

Se reestimaron treinta GLM auxiliares estándar (Poisson en conteos positivos y Gamma en importes positivos), solo dentro del ajuste emergente2023 de cada ramo/fold, usando asignaciones canónicas y los COVS fijados por la propuesta de Claude. La calidad del capital, mediana/centrado y referencia regional se fijan dentro del ajuste. Los errores robustos se agrupan por el componente cliente-dirección guardado, en lugar de solo cliente. Esos modelos auxiliares no se cuentan como nuevos candidatos de precio.

El prior desarrollado es el beta/SE, categorías de referencia e índice estacional guardados por Claude de su ajuste2021–2023. Se conservaron fuente/hash y copia privada; no se materializaron etiquetas o reestimaron modelos desarrollados de otros años en esta prueba. La igualdad de las cifras recibidas y la reconstrucción algebraica no reproducen aquel ajuste desde sus datos originales. Este prior sigue condicionado y su incertidumbre no se incorpora en Z. La validación por grupos de2023, tanto aquí como en las tandas anteriores, tampoco es un backtest histórico prospectivo al inicio de2023.

Por componente frecuencia/severidad, tau² es el máximo entre cero y la media de diferencias cuadradas entre coeficientes emergentes/desarrollados menos sus varianzas, sobre categorías comparables con al menos100siniestros de ajuste, excluyendo región, intercepto y nuevo negocio. Z=tau²/(tau²+SE_em²). La combinación de coeficientes produce c=exp(theta_cred−theta_em). Tau usa coeficientes correlacionados y pocos positivos; no se interpreta como un intervalo bayesiano calibrado o prueba de transferencia a la cartera que llega en enero.

B15 aplica c solo a las tasas nuevas de B14; las renovaciones quedan exactamente iguales. El GLM B14 ya tiene nuevo negocio como efecto no penalizado. Esta es una variante experimental de aplicación directa del factor, no la adopción sin cambios de todo NB-CRED-01. No hay balance A/E, pesos optimizados o ajuste con el fold retenido. C0 de precios sigue idéntico para todas las recetas; la estacionalidad solo participa en los auxiliares, que usan un objetivo distinto de la devianza final. No se añaden reservas/IBNR o exposición dos veces.

| Ramo | c, rango entre folds | Z frecuencia | Z severidad |
| --- | ---: | ---: | ---: |
{factortab}

La variación de c refleja cuánto se corrige cada estimación emergente de ajuste; no es por sí sola variación de igual tamaño en la relatividad creíble final. La severidad recibe casi todo el peso del prior. Esto requiere conservar la incertidumbre de la fuente, aunque la aritmética y los errores robustos coincidan.

## Resultados con los mismos 50.094 periodos de 2023

Treinta mil ochocientos sesenta y nueve componentes, cinco folds guardados y el mismo T0/C0. Observado global15,297millonesCU y nuevo negocio1,528millones. D² Tweedie1,5 global sobre importes, no media de los ramos; A/E=observado/predicho.

| Receta | D² global | Predicho, millones CU | A/E global | D² nuevo negocio | A/E nuevo negocio |
| --- | ---: | ---: | ---: | ---: | ---: |
{table}

Capital mueve el D² global −0,00000163 y el total predicho unos−590CU. Su intervalo cruza cero: no hay mejora o equivalencia establecida por esta muestra. La credibilidad mueve D² −0,00064909 frente a B14, también con intervalo que cruza cero. Nuevo negocio pasa de A/E0,906 a1,136; el agregado cercano a uno no sustituye la lectura por ramo.

| Comparación | Delta D² | Intervalo exploratorio95% | Delta tras retirar31grupos favorables |
| --- | ---: | --- | ---: |
{pairtab}

Se guardaron120parejas,2.000sorteos comunes por componente; se reconstruyeron separadamente las29nuevas. Son exploratorias después de16recetas adaptativas y de la investigación recibida, sin corrección por búsqueda o multiplicidad. No son el acta simultánea de2024. B14/B15 tampoco tienen mejora establecida sobre B00 y ambas diferencias se invierten con el retiro de sus31grupos favorables de evaluación, manteniendo modelos fijos.

| Nuevo negocio, D² por ramo | B13 | B14 | B15 |
| --- | ---: | ---: | ---: |
{cross}

La credibilidad mejora los puntos de hogar nuevo, pero empeora autos nuevos. En autos el A/E pasa de0,879 a1,223 y el D² de−0,01004 a−0,03324. En contenidos nuevos el A/E mejora de1,184 a1,052 y D² de0,15358 a0,17445. No se generaliza la mejora de un ramo al conjunto.

## Comprobaciones y decisiones

Pasaron25controles de revisión previa,26casos focales y832controles del [comprobador separado]({rp}/verifications/{vp.name}), con solapamiento. Este último no importa el productor ni ajusta modelos. Reconstruye la regla de capital, matrices auxiliares, score, sandwich agrupado con otro método de solución, tau/Z/c, transforms de precio, claves/ámbitos y replay con fit bloqueado. El máximo error absoluto de SE fue2,34e-15 y la condición máxima de sus matrices1382; el máximo score auxiliar medio fue8,09e-6, menor que1e-4 fijado antes. También coteja métricas/segmentos/escenarios e influencia y los29contrastes nuevos. Los escenarios conservan tasas fijas, no reestiman reservas o reportes.

El [informe completo]({rp}/report.json), [valoración]({rp}/assessment.json), [manifiesto]({rp}/manifest.json), [casos focales]({rp}/fixture_checks.json) y registro de decisiones conservan precisión y límites. Es revisión propia de Codex, no validación profesional independiente ni aprobación humana de la escala o transferencia.

Capital queda aplicado y probado solo en B14, con el riesgo material por fila abierto. Clima queda excluido del contrato prospectivo. B15 se conserva como alternativa creíble condicionada, sin mejora general demostrada; no se contradice la decisión referida del participante con una selección automática por score. El F0 global y sus históricos permanecen intactos. Se mantiene B00 y B01–B15, sin promoción, retiro, equivalencia o lista final congelada.

La continuidad nocturna retoma nivel/cola y vínculo de observación con modelos estándar, con receta previa para cualquier nuevo ensayo y sin ajustar c a posteriori por estos resultados. Quedan abiertos prior desarrollado no reproducido aquí, suficiencia de reservas/reporting, representatividad del negocio transferido y revisión humana.2024 sigue expresamente cerrado, sin ledger, precios/predicciones/scores de ese año o test; no envíos, remoto, publicación externa o delegación. Las [prácticas IAA](../../../../Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md) se concretan en límites/segmentos, separación de revisiones y trazabilidad, sin certificación profesional.
'''
with docpath.open('x',encoding='utf-8') as f:f.write(doc)
active=REPO/'registro/semana2_desarrollo2023_actual.json';idx=read(active);assert idx['id']=='S2-DEV2023-v5-20261023';snapshot=REPO/'registro/semana2_desarrollo2023_v5_snapshot.json'
with snapshot.open('xb') as f:f.write(active.read_bytes())
history=copy.deepcopy(idx['history']);history[-1].update(index_snapshot=rel(snapshot),index_sha256=sha(snapshot))
index={'id':plan['id'],'author':'Codex','as_of_utc':datetime.now(timezone.utc).isoformat(),'path_base':'workspace_root','status':'six_2023_trials_verified_capital_conditional_credibility_climate_excluded_B00_retained',
 'run':rel(RUN),'documentation':rel(docpath),'training_years':[2023],'scored_years':[2023],'rows_per_model':50094,'groups':30869,'folds':5,
 'new_price_base_fits':10,'new_auxiliary_Poisson_Gamma_fits':30,'new_credibility_factors':15,'exact_motor_reuses':5,'cumulative_price_base_fits':90,'cumulative_closed_form_constants':60,
 'auxiliary_counter_notice':'30 new auxiliary fits in this trial, separate from pricing and historical fits of other authors','models_consulted':list(points),'summary':r['summary'],'primary_contrasts':contrasts,
 'reference':'W2-B00','alternatives_preserved':list(points)[1:],'promotion':False,'confirmation_2024_open':False,'confirmation_closed_by_current_user_instruction':True,'final_confirmation_roster_frozen':False,
 'history':history+[{'id':plan['id'],'run':rel(RUN),'documentation':rel(docpath)}],'forum_prior':'COD-S2-20261023-018','forum_result':'COD-S2-20261023-019','submissions':0,
 'professional_independent_validation':False,'selector_status_not_assessed_here':True,'night_continuation_index':'Hackaton/Repositorio_IAA2026/registro/semana2_continuidad_nocturna.json',
 'verification':{'path':rel(vp),'sha256':sha(vp),'passed':v['passed'],'failed':0},'fixtures':{'path':rel(RUN/'fixture_checks.json'),'sha256':sha(RUN/'fixture_checks.json'),'passed':fixtures['passed'],'failed':0}}
for key,p in [('report',RUN/'report.json'),('plan',REPO/'registro/semana2_desarrollo2023_plan_v6.json'),('producer',ROOT/plan['code']),('auxiliary_producer',ROOT/plan['auxiliary_code']),('oof',RUN/'oof_2023.parquet'),('manifest',RUN/'manifest.json'),('assessment',RUN/'assessment.json'),('decision_journal',RUN/'decision_journal.json')]:index[key]=rel(p);index[key+'_sha256']=sha(p)
dump(RUN/'active_index_proposed.json',index)
body=f'''Codex. Resultado de COD-S2-20261023-018. [Informe de capital, clima y credibilidad](../../Repositorio_IAA2026/docs/semana2/CAPITAL_CLIMA_CREDIBILIDAD_2023.md), [registro de decisiones](../../{RUN.relative_to(ROOT/'Hackaton').as_posix()}/decision_journal.json). Solo2023, modelos estándar y las14tablas OOF anteriores exactas; B00 sigue referencia y2024 cerrado.

Capital: las56filas2023 (26edificios,30contenidos) pasan la regla /1000 aun aprendiendo los límites de prima por mil solo con ajuste del fold. Se reentrenaron diez GLM de hogar B14 con las seis variables de B13 y se conservaron cinco modelos motor exactos. Prima escrita solo audita escala, no entra en X. Todos esos registros tienen T0=0. El cambio de score es mínimo, pero las predicciones por fila afectada cambian entre−62,36% y+154,09% frente a imputar el capital desconocido. No es inmaterialidad por póliza o confirmación económica. No se corrigieron o predijeron2024/test ni se editó F0 global.

Clima: no se admite CLIMA-S2-01 en el contrato prospectivo por valores2024 en filas2023 y selección con2025. Se cotejó el adverso recibido de COD-S2-VAL04-20261023-CLIMA-AVISO sin repetirlo ni adjudicar su autoría. Las guardas propias rechazan fuente/selector futuros y ausencia de historia. Hay cero filas climáticas emergentes anteriores a2023 para materializar este bloque. No se hizo un comparador con fuga o un duplicado todo faltante. S2-VAL-DAT-003 conserva responsable y estado.

Credibilidad: treinta auxiliares Poisson/Gamma se reestimaron por ramo/fold solo en ajuste emergente2023, con asignaciones canónicas y SE por componente cliente-dirección. Se reconstruyeron tau/Z/c; se conserva como prior condicionado el desarrollado2021–2023 recibido de Claude, sin reestimar otros años o declarar su reproducción desde raw. B15 aplica c solo a nuevo negocio de B14, con renovación exacta y sin balance A/E adicional. No se usa c de todo2023 ni OOF de otros folds que incluya las etiquetas del retenido en su entrenamiento. La aplicación directa es una variante experimental de NB-CRED-01, no adopción final de toda la receta.

| Receta | D² global | Predicho millones CU | A/E global | D² nuevo negocio | A/E nuevo negocio |
| --- | ---: | ---: | ---: | ---: | ---: |
{table}

| Comparación | Delta D² | Intervalo exploratorio95% | Delta tras retirar31grupos favorables |
| --- | ---: | --- | ---: |
{pairtab}

B14/B13 delta−0,00000163 no establece mejora o equivalencia. B15/B14 delta−0,00064909 también tiene intervalo que cruza cero. Credibilidad mejora hogar nuevo, empeora autos nuevos: A/E0,879→1,223, D²−0,01004→−0,03324; contenidos nuevos A/E1,184→1,052 y D²0,15358→0,17445. La renovación B15 es exacta. No se interpreta como mejora general o decisión de retirar la alternativa.

Se guardaron120parejas con2.000sorteoscomunes,29nuevas reconstruidas separadamente. Son exploratorias tras16recetas adaptativas e investigación recibida, no confirmación o selección temporal. Pasaron25controles de revisión previa,26casos focales y832controles separados, con solapamiento: fuentes/ámbitos, transformaciones, score, matriz/sandwich por otro método, tau/Z/c, replay sin fit, métricas/segmentos/escenarios e influencia. Diferencia máxima de SE2,34e-15; condición máxima1382. Revisión técnica propia de Codex, no profesional independiente.

Quedan abiertos: materialidad de capital por fila y escala económica, prioridad/estacionalidad desarrolladas no reproducidas aquí y su incertidumbre omitida en Z, tau con coeficientes correlacionados, reporting/reservas/último y negocio transferido de enero. El prior2021–2023 y la validación por grupos2023 no son backtest prospectivo al inicio de2023. Los autores, propuestas y hallazgos ajenos se preservan. La continuidad nocturna revisará nivel/cola y vínculo de observación con modelos estándar y receta previa; no ajustará c a posteriori por estos scores.

Se conserva B00 y B01–B15, sin promoción, retiro, equivalencia o lista final.2024 permanece expresamente cerrado, sin ledger, precios/predicciones/scores de ese año o test; no envíos, remoto, publicación externa o delegación. No se alteraron la programación o las otras auditorías.
'''
with (ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v6_resultado.md').open('x',encoding='utf-8') as f:f.write(body)
print(json.dumps({'documentation':rel(docpath),'decision_journal':rel(RUN/'decision_journal.json'),'passed':v['passed'],'fixtures':fixtures['passed'],'failed':0}))
