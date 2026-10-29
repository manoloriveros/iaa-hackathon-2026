"""Publica lectura de la prueba v4 verificada, conserva decisiones y cortes."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
RUN=REPO/'privado/semana2/desarrollo2023/dev4_20261023T204811Z_4adcedec'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,obj):
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
r=read(RUN/'report.json');plan=read(RUN/'plan_snapshot.json');vp=sorted((RUN/'verifications').glob('*.json'))[-1];v=read(vp);fixtures=read(RUN/'fixture_checks.json')
assert v['failed']==fixtures['failed']==0
points={x['model_id']:x for x in r['summary']};segments=read(RUN/'diagnostics/segments.json');ss=read(RUN/'diagnostics/stress_segments.json')
seg=lambda m,d,l:next(x for x in segments if x['model_id']==m and x['segment']==d and x['label']==l)
assessment={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','reference_retained':'W2-B00','promotion':False,'confirmation_2024_open':False,
 'final_confirmation_roster_frozen':False,'alternatives_preserved':list(points)[1:],'professional_independent_validation':False,
 'findings':{'B08_improves_all_folds_vs_B00':True,'B08_level_sensitive_to_training_tail':True,'B09_new_business_concentrated_motor':True,
  'B11_new_business_improved_in_sample_of_development':True,'B10_B11_parent_gain_uncertain':True,'business_buildings_deviance_still_adverse':True},
 'warnings':[
 {'id':'DEV4-B08-TRAINING-TAIL','status':'open','effect':'Conditional price refit without 25 severe groups per training fold reduces S08 total 25.48% and D2 by .02402. No stable absolute level claim or full-pipeline robustness.'},
 {'id':'DEV4-SEGMENT-LEVEL','status':'open','effect':'New variants improve aggregate new-business level but worsen buildings-new D2 versus their parents; sparse building/content positives and fold factor dispersion remain.'},
 {'id':'DEV4-PARENT-GAIN','status':'open','effect':'B10/B08 and B11/B09 exploratory CIs cross zero; removal of their own favorable 31 evaluation groups reverses parent gain. No promotion.'},
 {'id':'DEV4-IN-SAMPLE','status':'open','effect':'Scalars minimize training loss on fitted parent predictions; not independent/inner-cross-fitted calibration or A/E=1 enforcement.'},
 {'id':'DEV4-ULTIMATE','status':'open','effect':'Observed T0 under frozen C0; reserve/reporting/master assumptions and unknown ultimate persist.'},
 {'id':'DEV4-2024-CLOSED','status':'open','effect':'Explicit participant instruction; no ledger, score, final roster or opening.'}],
 'prior_warnings':'Preserved with their original owners, including B02 generalization and B09 original recipe adverse new-business. New B11 does not close B09 warning.',
 'IAA_linkage':'Governance 2.8 and 3.3.2/3.4-3.6: distinguish own checks and conditional stress; Documentation 2-3: lineage/recipes/adverse results; Professional 3.3: business/line segments, not fairness certification.'}
dump(RUN/'assessment.json',assessment)
table='\n'.join(f"| {m} | {points[m]['D2']:.5f} | {points[m]['predicted_total']/1e6:.3f} | {points[m]['actual_over_expected']:.3f} | {seg(m,'business','new_business')['D2']:.5f} | {seg(m,'business','new_business')['actual_over_expected']:.3f} |" for m in ['W2-B00','W2-B08','W2-B09','W2-B10','W2-B11'])
pairtab='\n'.join(f"| {x['candidate']} / {x['reference']} | {x['delta_D2']:.5f} | [{x['exploratory_lower95']:.5f}; {x['exploratory_upper95']:.5f}] | {x['delta_after_removal']:.5f} |" for x in r['pairs'] if (x['candidate'],x['reference']) in [('W2-B10','W2-B00'),('W2-B11','W2-B00'),('W2-B10','W2-B08'),('W2-B11','W2-B09')])
cross='\n'.join('| '+label+' | '+' | '.join(f"{seg(m,'line_business',label)['D2']:.5f}" for m in ['W2-B00','W2-B08','W2-B09','W2-B10','W2-B11'])+' |' for label in ['motor_new_business','buildings_new_business','contents_new_business'])
qs=[]
for m in ['W2-B10','W2-B11']:
 for line in ['motor','buildings','contents']:
  vals=[[z['q'] for x in r['factors'] if x['model_id']==m and x['line']==line for z in x['factors'] if z['business']==b] for b in [0,1]]
  qs.append(f"| {m}, {line} | {min(vals[0]):.3f}–{max(vals[0]):.3f} | {min(vals[1]):.3f}–{max(vals[1]):.3f} |")
qtable='\n'.join(qs)
rp='../../'+RUN.relative_to(REPO).as_posix();docpath=REPO/'docs/archivo/semana2/DESARROLLO_2023_ESTABILIDAD_NEGOCIO.md'
doc=f'''# Estabilidad de B08 y nivel de nuevo negocio

Codex, 23 de octubre de 2026. B08 mejora frente a B00 en los cinco folds, pero su nivel es sensible a pocos siniestros grandes del ajuste. Las dos correcciones de nivel preinscritas mejoran sus puntos globales; la ventaja sobre sus propios padres sigue incierta y ambas empeoran la devianza de edificios nuevos. Se conserva B00 y todas las alternativas. 2024 permanece cerrado.

El [plan v4](../../registro/semana2_desarrollo2023_plan_v4.json) quedó en COD-S2-20261023-014 antes de calcular factores o reentrenar. El resultado es COD-S2-20261023-015 del [foro](<../../../Semana 2/Foro/FORO.md>). El [índice activo](../../registro/semana2_desarrollo2023_actual.json) mantiene las cuatro tandas y sus snapshots. Los cálculos se refieren a 50.094 periodos de 2023, 30.869 componentes cliente-dirección y cinco folds guardados. D² usa Tweedie 1,5 en importes observados T0, con nulo global; no es un promedio de D² por ramo ni una medición del último real.

## Diagnóstico antes de probar

La [revisión del OOF congelado](../../{Path(plan['diagnostic_review']).relative_to('Hackaton/Repositorio_IAA2026').as_posix()}) no calculó factores o nuevas predicciones. B08 mejora entre 0,01291 y 0,03360 puntos D² frente a B00 en cada fold; su A/E varía entre 0,779 y 1,133. Sus 31 componentes de evaluación más favorables concentran 78,0 % de la ventaja neta, y los de B09 90,8 %. Harían falta 68/40 grupos favorables para invertir sus ventajas con modelos fijos. Los folds comparten ajuste y estos retiros no comprueban estabilidad con reentrenamiento.

B09 pierde en autos nuevos (delta D² frente a B00 −0,01722, A/E 1,910) y edificios nuevos (−0,00843), mientras mejora en contenidos nuevos (+0,02782). Autos nuevos aporta 1,088 millones CU observados y solo 0,570 predichos; el propio B00 predice 0,543 millones. B08 mejora el agregado nuevo, pero pierde en edificios nuevos (−0,03269). Los tamaños positivos de nuevo negocio son 265 en autos, 40 en edificios y 36 en contenidos: unas pocas severidades pueden mover mucho las conclusiones por ramo.

## Recetas congeladas y frontera de información

B10 parte de B08 y B11 de B09. Para cada ramo/fold y negocio nuevo o renovación se calcula únicamente en ajuste:

`mu = exposición_efectiva_C0 × tasa_padre`

`q = sum(T0 / sqrt(mu)) / sum(sqrt(mu))`

`tasa_nueva = q × tasa_padre`

Es el mínimo escalar positivo de la devianza Tweedie 1,5 para esa forma de riesgo. Usa predicciones dentro del ajuste y no constituye calibración independiente o interna fuera de muestra. Cambia explícitamente el ancla de nivel en las dos variantes; no fuerza totales de ajuste/validación o A/E igual a uno. Conserva orden de tasas solo dentro de ramo, fold y tipo de negocio. Se aprendieron 60 factores y se guardaron 30 adaptadores, sin nuevos GLM/árboles para B10/B11. No hubo búsqueda de pesos, suavizado, cap o elección por score retenido.

Una sensibilidad separada, S08, retira los 25 componentes con mayor T0 de cada conjunto de ajuste (0,1 % redondeado hacia arriba). El orden usa solo costes de ajuste y desempata por ID; se retiran todas sus filas en los tres ramos. Reaprende transformaciones, GLM B03 (alpha 10 en edificios, 1 en los otros ramos), constante S00, ancla y mezcla fija del 50 %. Son quince GLM y quince constantes; cada fold conserva todas las filas de validación. S00/S08 son resultados de estrés, fuera de las doce alternativas candidatas. No se eliminó ninguna fila del ajuste principal de B10/B11, del objetivo completo o de los datos originales.

El estrés conserva C0 del fold. Sus curvas excluyen validación pero aún reflejan los grupos retirados; por eso mide sensibilidad del modelo de riesgo y sus transformaciones, condicional al vínculo de observación. No es reestimación integral de reporting, jackknife completo o validación temporal. La retirada deliberada de siniestros grandes tampoco es una regla admisible de limpieza o propuesta de producción.

## Resultados fuera de muestra en 2023

Observado total: 15,297 millones CU, de los cuales 1,528 son de nuevo negocio. A/E es observado dividido por predicho.

| Receta | D² global | Predicho, millones CU | A/E global | D² nuevo negocio | A/E nuevo negocio |
| --- | ---: | ---: | ---: | ---: | ---: |
{table}

B10 mejora 0,00106 puntos globales frente a B08 y B11 0,00582 frente a B09. Sus intervalos exploratorios incluyen cero. B11 acerca el nivel nuevo (A/E 1,043 frente a 1,502 de B09) y sube su D² nuevo a 0,08304; esto no corrige automáticamente la forma del riesgo. B10 deja un A/E global 1,080 frente a 0,981 de B08: mejorar la devianza no equivale a cuadrar el agregado.

| Comparación | Delta D² | Intervalo exploratorio 95 % | Delta tras retirar sus 31 grupos favorables |
| --- | ---: | --- | ---: |
{pairtab}

Las 66 parejas usan 2.000 sorteos comunes por componente, con semilla 2026102302. No corrigen búsqueda adaptativa ni comparaciones múltiples; no son el acta de confirmación 2024. Con las listas previamente congeladas de grupos favorables B08/B09, las diferencias B10/B11 frente a B00 son +0,00701/+0,00835. Las ventajas sobre sus propios padres se invierten al retirar sus respectivos 31 grupos favorables. Se conservan todos los resultados adversos.

| Nuevo negocio por ramo, D² | B00 | B08 | B09 | B10 | B11 |
| --- | ---: | ---: | ---: | ---: | ---: |
{cross}

En edificios nuevos, B10 logra A/E 1,003 pero su D² baja de 0,03253 a 0,01111; B11 llega a A/E 1,020 mientras su D² baja de 0,05680 a 0,02595. El nivel agregado oculta una pérdida de calidad dentro del segmento. En autos nuevos ambas correcciones mejoran, aunque sus D² siguen negativos frente al nulo específico del segmento.

| Factor q, rango entre folds | Renovación | Nuevo negocio |
| --- | ---: | ---: |
{qtable}

La corrección B11 en autos nuevos exige multiplicadores entre 1,703 y 1,889. Los rangos mayores de edificios/contenidos nuevos deben leerse junto con sus pocos positivos. No se extrae de esto una causa única del deterioro de B09 ni se cierra la advertencia de su receta original.

## Sensibilidad de B08 al reentrenar

Cada fold pierde 46–53 filas de ajuste, que suman entre 2,715 y 3,408 millones CU. Son conjuntos solapados de 25 componentes por fold, no 125 observaciones independientes. La validación y C0 quedan fijos.

| Resultado | D² | Predicho, millones CU | A/E |
| --- | ---: | ---: | ---: |
| B00 original | {points['W2-B00']['D2']:.5f} | {points['W2-B00']['predicted_total']/1e6:.3f} | {points['W2-B00']['actual_over_expected']:.3f} |
| B08 original | {points['W2-B08']['D2']:.5f} | {points['W2-B08']['predicted_total']/1e6:.3f} | {points['W2-B08']['actual_over_expected']:.3f} |
| S00 reestimada bajo estrés | {r['stress_summary'][0]['D2']:.5f} | {r['stress_summary'][0]['predicted_total']/1e6:.3f} | {r['stress_summary'][0]['actual_over_expected']:.3f} |
| S08 reestimado bajo estrés | {r['stress_summary'][1]['D2']:.5f} | {r['stress_summary'][1]['predicted_total']/1e6:.3f} | {r['stress_summary'][1]['actual_over_expected']:.3f} |

El total de S08 cae 25,48 % frente a B08 y el D² 0,02402 puntos. La mediana de cambio de tasa es −7,27 %; el percentil 1 es −67,34 % y el 99 +7,65 %. S08 supera a S00 en 0,02984 puntos bajo el mismo estrés. Esto sugiere que la forma conserva utilidad relativa frente a esa constante, mientras el nivel depende de grupos severos. No declara a B08 estable para 2025. El A/E 1,316 de S08 muestra el déficit de importe que esa perturbación puede introducir.

## Comprobaciones y decisiones

Pasaron {fixtures['passed']} casos focales y {v['passed']} controles del [comprobador separado]({rp}/verifications/{vp.name}), con solapamiento entre ellos; es revisión propia de Codex, no validación profesional independiente. Reconstruye factores con suma compensada y derivada, mínimo escalar, claves/ámbito, padres, imputación/escalado de estrés, constante/ancla, replay con fit bloqueado, segmentos, escenarios a tasas fijas, 66 parejas y retiros de grupos. El [manifiesto]({rp}/manifest.json), [informe íntegro]({rp}/report.json), [valoración]({rp}/assessment.json) y [casos focales]({rp}/fixture_checks.json) conservan precisión y trazabilidad.

El primer intento de corrida se detuvo antes de cualquier factor o entrenamiento: el cargador de una tabla por modelo rechazó las claves repetidas entre recetas del OOF. Se corrigió el contexto de unicidad a modelo/mercado/ramo/fila, sin cambiar la receta, y se preservó el intento. El primer comprobador se detuvo por una variable local que ocultaba el módulo de expresiones regulares; quedó registrado y se corrigió sin reentrenar. Hubo dos lecturas idénticas del OOF inicial al recuperar una sesión de herramienta, sin nuevas predicciones o ajustes; se conservan como lecturas, no evidencia independiente adicional.

Se mantienen B00 y B01–B11, sin promoción, retiro, equivalencia o lista final congelada. Quedan abiertas la sensibilidad del nivel de B08, el deterioro de edificios nuevos, la incertidumbre sobre la ventaja de los nuevos factores y los supuestos del último. Los escenarios de reservas/reporting mueven el vínculo y la respuesta a tasas fijas; no reentrenan ni acreditan suficiencia de reservas. La siguiente decisión metodológica tendría que tratar la dependencia del nivel y la forma por ramo sin ajustar a posteriori los folds vistos; no se inicia otra tanda en este encargo.

La aplicación de [prácticas IAA](../../../../Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md) queda concreta en el contraste de segmentos (consideraciones profesionales §3.3), sensibilidad y separación de revisión propia/independiente (gobernanza §2.8 y §§3.3.2, 3.4–3.6), y linaje/recetas/resultados adversos (documentación §§2–3). La comparación comercial no acredita equidad profesional o competencia para uso real. No aplican despliegue o monitorización de una tarifa en esta prueba local.

2024 sigue cerrado por instrucción expresa, con cero precios, predicciones o scores; tampoco hay test, envíos, entrenamiento remoto, publicación externa o delegación. El avance técnico del selector no autoriza abrirlo. Las advertencias de otros encargos conservan sus autores y alcance. Persiste la revisión humana pendiente.
'''
with docpath.open('x',encoding='utf-8') as f:f.write(doc)
parentindex=REPO/'registro/semana2_desarrollo2023_actual.json';snapshot=REPO/'registro/semana2_desarrollo2023_v3_snapshot.json'
assert read(parentindex)['id']=='S2-DEV2023-v3-20261023'
with snapshot.open('xb') as f:f.write(parentindex.read_bytes())
idx=read(snapshot);history=idx['history'];history[-1].update(index_snapshot=rel(snapshot),index_sha256=sha(snapshot))
index={'id':plan['id'],'author':'Codex','as_of_utc':datetime.now(timezone.utc).isoformat(),'path_base':'workspace_root','status':'four_2023_trials_verified_reference_retained_no_promotion',
 'run':rel(RUN),'documentation':rel(docpath),'training_years':[2023],'scored_years':[2023],'rows_per_model':50094,'groups':30869,'folds':5,
 'new_candidate_base_estimator_fits':0,'new_level_factors':60,'new_adapter_bundles':30,'stress_base_estimator_fits':15,'stress_constants':15,
 'cumulative_base_estimator_fits':65,'cumulative_closed_form_constants':30,'cumulative_level_factors':90,'cumulative_candidate_adapters':90,
 'models_consulted':list(points),'summary':r['summary'],'reference_pairs':[p for p in r['pairs'] if p['reference']=='W2-B00' and p['candidate'] in ['W2-B10','W2-B11']],
 'reference':'W2-B00','alternatives_preserved':list(points)[1:],'promotion':False,'confirmation_2024_open':False,'confirmation_closed_by_current_user_instruction':True,
 'final_confirmation_roster_frozen':False,'history':history+[{'id':plan['id'],'run':rel(RUN),'documentation':rel(docpath)}],
 'forum_prior':'COD-S2-20261023-014','forum_result':'COD-S2-20261023-015','submissions':0,'selector_status_not_assessed_here':True,'professional_independent_validation':False,
 'verification':{'path':rel(vp),'sha256':sha(vp),'passed':v['passed'],'failed':v['failed']},'fixtures':{'path':rel(RUN/'fixture_checks.json'),'sha256':sha(RUN/'fixture_checks.json'),'passed':fixtures['passed'],'failed':0}}
for key,p in [('report',RUN/'report.json'),('plan',ROOT/plan['code'].replace('src/semana2/entrenar_desarrollo2023_v4.py','registro/semana2_desarrollo2023_plan_v4.json')),
 ('producer',ROOT/plan['code']),('oof',RUN/'oof_2023.parquet'),('manifest',RUN/'manifest.json'),('assessment',RUN/'assessment.json'),('stress_oof',RUN/'stress_oof_2023.parquet')]:
 index[key]=rel(p);index[key+'_sha256']=sha(p)
dump(RUN/'active_index_proposed.json',index)
body=f'''Codex. Respondo a COD-S2-20261023-014. La [prueba v4]({rel(docpath).replace('Hackaton/','../../',1)}) quedó completada y verificada exclusivamente con 2023. Las diez tablas OOF anteriores, B00 incluido, son exactas; no se tocaron recetas históricas. [Índice activo](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json).

B08 mejora frente a B00 en los cinco folds, pero la sensibilidad preinscrita de reentrenamiento muestra dependencia del nivel de pocos grupos. Se retiraron del ajuste 25 componentes de mayor coste por fold (46–53 filas; 2,715–3,408 millones CU), sin eliminar validación. S08 cae de D² 0,09318 a 0,06916 y de 15,599 a 11,625 millones CU predichos (−25,48 %), A/E 1,316. La mediana de cambio de tasa es −7,27 %. La constante S00 reestimada bajo el mismo estrés queda en D² 0,03932: S08 conserva una diferencia +0,02984. Es sensibilidad del modelo de riesgo/preprocesado con C0 fijo, que aún refleja grupos retirados; no estabilidad integral de reporting, jackknife completo o confirmación temporal. No se propone recortar siniestros grandes.

{table}

Columnas de la tabla: receta, D² global, predicho millones CU, A/E global, D² nuevo negocio, A/E nuevo negocio. Observado total 15,297 millones CU y nuevo 1,528. B10/B11 usan los 60 escalares Tweedie por ramo/fold/tipo de negocio preinscritos, aprendidos solo en ajuste sobre B08/B09; sin nuevos estimadores base para estas dos variantes. El estrés ajustó quince GLM y quince constantes, sin árboles ni búsqueda. Acumulado de las cuatro tandas: 65 estimadores base y 30 constantes; reusos y adaptadores se cuentan aparte.

La brecha de B09 se concentra en autos nuevos (antes A/E 1,910, D² −0,14736); B11 pasa a A/E 1,042 y D² −0,04508. El agregado nuevo B11 mejora D² 0,04065→0,08304 y A/E 1,502→1,043. Sin embargo, edificios nuevos empeora en ambos: B08→B10 D² 0,03253→0,01111, B09→B11 0,05680→0,02595, pese a sus A/E cercanos a uno. Solo hay 40 positivos nuevos en edificios y 36 en contenidos. No se confunden nivel y forma ni se cierra la advertencia de B09 por una receta nueva.

{pairtab}

Comparaciones: candidato/padre o referencia, delta D², intervalo exploratorio 95 %, delta al retirar 31 grupos favorables a esa pareja. B10/B08 y B11/B09 tienen intervalos que incluyen cero y cambian a signo adverso tras el retiro. Frente a B00, B10/B11 siguen positivos tras retiro propio (+0,00691/+0,00346) y las listas congeladas de B08/B09 (+0,00701/+0,00835). Las 66 parejas y 2.000 sorteos comunes no corrigen búsqueda adaptativa o multiplicidad; no equivalen a la confirmación de2024.

Pasaron {fixtures['passed']} casos focales y {v['passed']} controles del comprobador separado (con solapamiento): factores/derivadas, fuentes, reproducción sin fit, transformaciones y selección de grupos del estrés, métricas, escenarios, remuestreo e influencia. Revisión propia de Codex, no validación profesional independiente. El intento inicial de corrida abortó antes de factores o entrenamiento por una comprobación de claves del OOF multirreceta; se corrigió sin cambiar recetas y se conserva. El primer comprobador abortó por una variable local y se corrigió sin reentrenar. La lectura inicial duplicada del OOF se conserva sin contarse como evidencia adicional.

Se mantiene B00 y B01–B11, sin promoción, retiro, equivalencia o lista final congelada. Quedan visibles sensibilidad del nivel de B08, celdas adversas de edificios nuevos, incertidumbre de la ventaja sobre los padres y supuestos de último/reservas. No se inicia otra tanda tras ver estos resultados. 2024 permanece cerrado por instrucción expresa independientemente del selector: cero precios, scores y predicciones de ese año o test, ningún ledger, envío, remoto, publicación externa o delegación. Las advertencias ajenas conservan responsables y alcance.
'''
# Use real Markdown table headers in the forum, retaining the same metrics.
body=body.replace(table,'| Receta | D² global | Predicho, millones CU | A/E global | D² nuevo | A/E nuevo |\n| --- | ---: | ---: | ---: | ---: | ---: |\n'+table)
body=body.replace(pairtab,'| Comparación | Delta D² | Intervalo exploratorio 95 % | Delta tras retirar 31 grupos |\n| --- | ---: | --- | ---: |\n'+pairtab)
bodypath=ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v4_resultado.md'
with bodypath.open('x',encoding='utf-8') as f:f.write(body)
print(json.dumps({'documentation':rel(docpath),'assessment':rel(RUN/'assessment.json'),'proposed_index':rel(RUN/'active_index_proposed.json'),'passed':v['passed'],'failed':0}))
