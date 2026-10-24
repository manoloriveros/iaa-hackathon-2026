"""Informe y valoración de la prueba preinscrita de nivel/contracción."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,obj):
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args()
run=Path(args.run).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023')
report=read(run/'report.json');plan=read(run/'plan_snapshot.json');parent=ROOT/plan['parent_run'];review=read(ROOT/plan['diagnostic_review'])
verification_path=sorted((run/'verifications').glob('*.json'))[-1];verification=read(verification_path);assert verification['failed']==0
points={x['model_id']:x for x in report['summary']};pairs=report['pairs'];segments=read(run/'diagnostics/segments.json')
newids=[x['id'] for x in plan['models']]
refpairs=[p for p in pairs if p['reference']=='W2-B00' and p['candidate'] in newids]
fixed={x['model_id']:x for x in report['frozen_parent_influence']}
seg=lambda mid,dim,label:next(x for x in segments if x['model_id']==mid and x['segment']==dim and x['label']==label)
assessment={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'reference_retained':'W2-B00',
 'alternatives_preserved':list(points)[1:],'promotion':False,'confirmation_2024_open':False,'final_confirmation_roster_frozen':False,
 'readout':{'fit_anchor_verified':True,'heldout_levels_close_to_B00':True,
    'anchor_alone_does_not_resolve_top31_influence':['W2-B06','W2-B07'],
    'half_weight_positive_after_both_own_and_parent_top31_diagnostics':['W2-B08','W2-B09'],
    'highest_point_in_current_exploration':'W2-B08'},
 'warnings':[
  {'id':'DEV3-IN-SAMPLE-ANCHOR','class':'condition','status':'open','effect':'Factors normalize in-sample parent predictions within outer training. This is not independently calibrated, inner-OOF or a guarantee of future/ultimate level. B00 itself is sensitive to claims.'},
  {'id':'DEV3-SEARCH-UNCERTAINTY','class':'condition','status':'open','effect':'Intervals are exploratory, conditional and unadjusted for adaptive search or 45 pairs. Positive lower bounds do not establish temporal superiority or authorize promotion.'},
  {'id':'DEV3-ANCHOR-ONLY-INFLUENCE','class':'condition','status':'open','effect':'B06/B07 still turn negative after their own/frozen-parent favorable top31 removal; changing level alone did not fix this diagnostic.'},
  {'id':'DEV3-B09-NEW-BUSINESS','class':'condition','status':'open','effect':'B09 point D2 in new business remains below B00 despite global improvement; it is not a passed temporal segment safeguard.',
    'delta_new_business_D2':seg('W2-B09','business','new_business')['D2']-seg('W2-B00','business','new_business')['D2']},
  {'id':'DEV3-ULTIMATE','class':'condition','status':'open','effect':'T0/C0, reserves, report stationarity, unseen tails and physical master assumptions retain their earlier scope.'},
  {'id':'DEV3-2024-CLOSED','class':'block','status':'open','effect':'Explicit user instruction keeps 2024 closed independently of other selector repair work. No final roster freeze or opening here.'}],
 'independent_professional_validation':False,'native_estimator_fits':0,'scalar_factors_learned':30}
dump(run/'assessment.json',assessment)
labels={'W2-B00':'Referencia','W2-B03':'GLM, padre','W2-B05':'Boosting simple, padre',
        'W2-B06':'B03 con nivel B00','W2-B07':'B05 con nivel B00','W2-B08':'50 % B00 + 50 % B06','W2-B09':'50 % B00 + 50 % B07'}
table='\n'.join(f"| {mid}: {label} | {points[mid]['D2']:.5f} | {points[mid]['predicted_total']/1e6:.3f} | {points[mid]['actual_over_expected']:.3f} |" for mid,label in labels.items())
citab='\n'.join(f"| {p['candidate']} | {p['delta_D2']:.5f} | [{p['exploratory_lower95']:.5f}, {p['exploratory_upper95']:.5f}] | {p['delta_after_removal']:.5f} | {fixed[p['candidate']]['delta_D2_after_frozen_parent_removal']:.5f} |" for p in refpairs)
levelrows=[]
for pid in ['W2-B03','W2-B05']:
    for line in ['motor','buildings','contents']:
        vals=[x['scale'] for x in report['scales'] if x['parent_model']==pid and x['line']==line]
        levelrows.append(f"| {pid}, {line} | {min(vals):.4f} | {max(vals):.4f} |")
linetab='\n'.join('| '+name+' | '+' | '.join(f"{seg(mid,'line',line)['D2']:.5f}" for mid in ['W2-B00','W2-B08','W2-B09'])+' |' for line,name in [('motor','Autos'),('buildings','Edificios'),('contents','Contenidos')])
biztab='\n'.join('| '+name+' | '+' | '.join(f"{seg(mid,'business',business)['D2']:.5f}" for mid in ['W2-B00','W2-B08','W2-B09'])+' |' for business,name in [('new_business','Nuevo negocio'),('renewal','Renovación')])
scenarios=read(run/'diagnostics/observation_sensitivity.json');sc={(x['model_id'],x['scenario']):x['D2'] for x in scenarios}
scenetab='\n'.join('| '+case+' | '+' | '.join(f"{sc[mid,case]-sc['W2-B00',case]:.5f}" for mid in newids)+' |' for case in ['reserve075','reserve125','late_cost05','late_cost10'])
rp='../../'+run.relative_to(REPO).as_posix();review_link='../../'+Path(plan['diagnostic_review']).relative_to(Path('Hackaton/Repositorio_IAA2026')).as_posix()
doc=f'''# Nivel agregado e influencia: tercera prueba de 2023

Codex, 23 de octubre de 2026. Igualar el nivel de ajuste al de B00 acerca los totales fuera de muestra a la referencia, pero por sí solo no resuelve la concentración de la ventaja. Las dos contracciones fijas del 50 % mantienen una diferencia positiva después de los retiros de grupos preinscritos. B08 obtiene el mejor punto de esta exploración. Se conserva B00, no hay promoción y 2024 sigue cerrado.

El [plan v3](../../registro/semana2_desarrollo2023_plan_v3.json) y COD-S2-20261023-012 preceden al cálculo de factores y predicciones. El resultado está en COD-S2-20261023-013 del [foro](<../../../Semana 2/Foro/FORO.md>). El [índice activo](../../registro/semana2_desarrollo2023_actual.json) identifica esta prueba y las tandas anteriores.

## Diagnóstico que motivó la prueba

La [revisión previa]({review_link}) usa únicamente OOF2023 guardado. B03 predice 14,320 millones CU y B05 14,113 frente a 15,614 de B00 y 15,297 observados. Quedan 8,29 % y 9,61 % por debajo del nivel de B00. El déficit frente al observado se concentra en edificios: 0,718 millones CU en B03 y 0,695 en B05.

Los 31 componentes más favorables representan 140,49 % de la ventaja neta de B03 y 130,02 % de la de B05, porque compensan pérdidas en otros componentes. Concentran 12,31 %/9,48 % del coste observado y 0,12 %/0,13 % de la exposición. Basta retirar 14 grupos favorables de B03 o 18 de B05 para invertir su ventaja; diecinueve componentes pertenecen a ambas listas.

No se interpretan como errores de datos o permiso para recortar la cola. Los retiros mantienen los modelos fijos: miden influencia en la evaluación, no la influencia de reentrenar sin esos grupos. Se conservaron todos los periodos en ajuste, factores y objetivo completo.

## Recetas y frontera de información

Para cada padre, ramo y fold se calcula, solo en las filas de ajuste de ese fold:

`s = sum(e × tasa_B00) / sum(e × tasa_padre)`

`tasa_nueva = (1−w) × tasa_B00 + w × s × tasa_padre`

e es la exposición efectiva C0. Los modelos base y la tasa constante B00 ya estaban guardados, con los mismos ámbitos de ajuste. B06 usa B03 y w=1; B07 usa B05 y w=1. B08 y B09 repiten esas fórmulas con w=0,5, fijado antes de probar. Los treinta factores se comparten entre las variantes de peso uno y medio.

La fórmula iguala exactamente el total predicho de ajuste con el de B00 por ramo/fold y conserva el orden de las tasas anuales dentro de ese ámbito. La contracción reduce a la mitad la desviación de la tasa anclada respecto de B00. No minimiza de nuevo la pérdida Tweedie de la escala ni garantiza reducir a la mitad la contribución a la devianza.

No se usa el total observado de validación, sus características o su distribución para aprender s o w. La comprobación reconstruyó cada factor con las filas de ajuste sin columnas de respuesta. Las predicciones usadas para normalizar son de los modelos dentro de su ajuste: no es calibración independiente o interna fuera de muestra. B00 también depende de los siniestros de ajuste y puede ser sensible a eventos severos. No se forzó A/E a uno ni igualdad de los totales OOF.

| Padre y ramo | Factor mínimo entre folds | Máximo |
| --- | ---: | ---: |
{chr(10).join(levelrows)}

Se reutilizaron 45 archivos distintos de modelos base (treinta padres y quince B00). La referencia se usa para ambos padres por fold. Se aprendieron treinta factores y se guardaron sesenta adaptadores, con las funciones de ajuste de estimadores base bloqueadas y cero intentos de llamarlas. No se ajustaron otros GLM o árboles. Son 50.094 periodos, 30.869 componentes y los cinco folds de 2023, con F0, T0, C0 y seis comparadores anteriores exactamente iguales. La prueba y agregación inicial tardaron {report['elapsed_seconds']:.1f} segundos en CPU con dos hilos; revisión y documentación son trabajo adicional.

## Resultado fuera de muestra

El observado es 15,297 millones CU. A/E significa observado dividido por predicho. El D² es global sobre todas las filas, no promedio por ramo. Se evalúa T0 mediante C0; no es un score de Kaggle o una comprobación del último real.

| Receta | D² OOF2023 | Predicho, millones CU | A/E |
| --- | ---: | ---: | ---: |
{table}

Los totales nuevos quedan cerca de los de B00 sin haberlos impuesto en OOF. Por eso sus A/E cercanos a 0,98 también heredan el nivel de referencia; no demuestran calibración futura o suficiencia de reservas. B08 alcanza 0,09318 frente a 0,08672 de su padre B03, y B09 0,08077 frente a 0,07986 de B05. No se escogió un peso alternativo después de verlos.

## Influencia con dos listas de grupos

Se repite el retiro de los 31 grupos más favorables de cada receta. Además se retiran las listas congeladas de su padre, idénticas para comparar padre, ancla y contracción. Se recalcula el nulo en el conjunto retenido. Los retiros solo son diagnósticos de evaluación y no afectan el score principal.

| Frente a B00 | Diferencia D² completa | Intervalo exploratorio 95 % | Tras retirar sus propios 31 favorables | Tras retirar los 31 del padre |
| --- | ---: | --- | ---: | ---: |
{citab}

B06/B07 siguen cambiando de signo con ambas listas. Mover el nivel no resuelve ese diagnóstico. B08/B09 conservan signo positivo bajo los dos retiros fijados; es evidencia de menor dependencia en esta evaluación, no ausencia de influencia o de sensibilidad al reentrenamiento. La estructura B03/B05 y el ancla siguen aprendidas del mismo año.

Se conservaron 2.000 sorteos pareados comunes y se reconstruyó el nulo en cada réplica. Los cuatro intervalos nuevos frente a B00 tienen límites inferiores positivos, pero siguen siendo exploratorios, condicionales y sin corrección por la búsqueda de las tres tandas o por las 45 parejas de diez recetas. No equivalen a la confirmación simultánea de 2024. Los [recibos y réplicas]({rp}/diagnostics/pairs.json) mantienen todas las comparaciones; no solo el mejor punto.

## Ramos y negocio

| Ramo | B00 | B08 | B09 |
| --- | ---: | ---: | ---: |
{linetab}

| Segmento | B00 | B08 | B09 |
| --- | ---: | ---: | ---: |
{biztab}

B08 mejora el punto de los tres ramos y ambos segmentos frente a B00 en esta muestra. B09 mantiene deterioro en nuevo negocio pese a mejorar el global. Los nulos de cada subconjunto son propios y no se suman sus D². Nuevo negocio es una marca contractual, no la futura evaluación temporal de clientes nuevos.

## Sensibilidad y controles

Estas diferencias frente a B00 mantienen los adaptadores y sus factores base fijos. Cambian solo respuesta y exposición de los escenarios guardados. No reanclan o reentrenan, y no cumplen por sí solas las salvaguardas completas de confirmación.

| Escenario | B06−B00 | B07−B00 | B08−B00 | B09−B00 |
| --- | ---: | ---: | ---: | ---: |
{scenetab}

Pasaron 21 casos focales del ancla, contracción, guardas y bloqueo de fit. El comprobador separado pasó {verification['passed']:,} controles (los recuentos se solapan): reconstruyó factores con suma independiente, igualdad de ajuste, contracción y orden, parámetros padres inalterados, seis comparadores exactos, replay con fit bloqueado, pérdidas, intervalos, listas de grupos y sensibilidades. [Recibo]({rp}/{verification_path.relative_to(run).as_posix()}). Es revisión propia de Codex, no revisión profesional independiente.

## Decisión

Se conserva B00 y se mantienen B01–B09. B08 queda como resultado prometedor de desarrollo, sin promoción o lista final congelada. Las [advertencias]({rp}/assessment.json) mantienen la reutilización del ajuste para normalizar, búsqueda adaptativa, influencia residual de B06/B07, segmento adverso de B09 y supuestos del último. Los bloqueos de recetas anteriores conservan su autoría; estos IDs nuevos no los cierran.

2024 permanece cerrado por instrucción expresa del participante. El cierre técnico del vínculo del selector y el seguimiento GOV005 publicados por otros encargos tienen evidencia y responsables propios; aquí no se actualiza su estado ni se infiere permiso de abrir. No hay precios, ajuste o métricas de 2024 o test, apertura de ledger, envíos o entrenamiento remoto. Los [supuestos de T0 a último](VARIABLES_Y_ULTIMO.md) y la revisión humana pendiente mantienen su alcance.

## Reproducir la comprobación

```powershell
& 'Preparación/.venv/Scripts/python.exe' 'Hackaton/Repositorio_IAA2026/herramientas/verificar_desarrollo2023_v3_semana2.py' --run '{rel(run)}'
```

El comando comprueba los modelos guardados y reconstruye estadísticas con fit bloqueado. El [manifiesto de la prueba]({rp}/manifest.json) conserva su corte; la revisión y registro posteriores tienen anexos propios. No se necesita reentrenar para revisar esta prueba.
'''
docpath=REPO/'docs/semana2/DESARROLLO_2023_NIVEL_INFLUENCIA.md'
with docpath.open('x',encoding='utf-8') as f:f.write(doc)
active=REPO/'registro/semana2_desarrollo2023_actual.json';prior=read(active);assert prior['id']=='S2-DEV2023-v2-20261023'
snapshot=REPO/'registro/semana2_desarrollo2023_v2_snapshot.json'
with snapshot.open('xb') as f:f.write(active.read_bytes())
history=prior['history'][:];history[-1]=dict(history[-1],index_snapshot=rel(snapshot),index_sha256=sha(snapshot))
history.append({'id':report['id'],'run':rel(run),'documentation':rel(docpath)})
index={'id':report['id'],'author':'Codex','as_of_utc':datetime.now(timezone.utc).isoformat(),'path_base':'workspace_root',
 'status':'three_2023_trials_verified_reference_retained_no_promotion','run':rel(run),'report':rel(run/'report.json'),'report_sha256':sha(run/'report.json'),
 'documentation':rel(docpath),'plan':rel(REPO/'registro/semana2_desarrollo2023_plan_v3.json'),'plan_sha256':report['plan_sha256'],
 'producer':rel(REPO/'src/semana2/entrenar_desarrollo2023_v3.py'),'producer_sha256':report['code_sha256'],
 'oof':rel(run/'oof_2023.parquet'),'oof_sha256':sha(run/'oof_2023.parquet'),'manifest':rel(run/'manifest.json'),'manifest_sha256':sha(run/'manifest.json'),
 'assessment':rel(run/'assessment.json'),'assessment_sha256':sha(run/'assessment.json'),
 'verification':{'path':rel(verification_path),'sha256':sha(verification_path),'passed':verification['passed'],'failed':0},
 'training_years':[2023],'scored_years':[2023],'rows_per_model':50094,'groups':30869,'folds':5,
 'new_base_estimator_fits_this_trial':0,'new_level_factors':30,'new_adapter_bundles':60,
 'cumulative_base_estimator_fits':50,'cumulative_closed_form_constants':15,'cumulative_level_factors':30,
 'models_consulted':list(points),'summary':report['summary'],'reference_pairs':refpairs,'reference':'W2-B00',
 'alternatives_preserved':list(points)[1:],'promotion':False,'confirmation_2024_open':False,'confirmation_closed_by_current_user_instruction':True,
 'final_confirmation_roster_frozen':False,'history':history,'forum_prior':'COD-S2-20261023-012','forum_result':'COD-S2-20261023-013',
 'submissions':0,'selector_status_not_assessed_here':True,'professional_independent_validation':False}
dump(run/'active_index_proposed.json',index)
body=f'''Codex. Cierro la prueba de nivel/contracción preinscrita en COD-S2-20261023-012 por petición del participante. El [informe](../../Repositorio_IAA2026/docs/semana2/DESARROLLO_2023_NIVEL_INFLUENCIA.md) y el [índice activo](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json) conservan las tres tandas y sus snapshots.

Se reutilizaron GLM y árboles guardados de 2023, sin ajustes nuevos de estimadores base. Se aprendieron treinta factores exclusivamente en sus filas de ajuste y se guardaron sesenta adaptadores. El ancla fija el total predicho de ajuste al de B00, no al observado o al OOF. Las mezclas del 50 % estaban fijadas antes de probar. F0, T0/C0, folds, los seis comparadores y todos los periodos permanecen iguales.

| Receta | D² OOF2023 | Predicho, millones CU | A/E |
| --- | ---: | ---: | ---: |
{table}

Mover solo el nivel acerca los totales a B00, pero B06/B07 siguen perdiendo su ventaja al retirar grupos favorables. Las contracciones B08/B09 conservan signo positivo bajo el retiro de sus propios grupos y de las listas congeladas de sus padres:

| Frente a B00 | Diferencia D² completa | Intervalo exploratorio 95 % | Tras retirar sus propios 31 favorables | Tras retirar los 31 del padre |
| --- | ---: | --- | ---: | ---: |
{citab}

B08 tiene el mejor punto de esta exploración y mejora los puntos de los tres ramos y ambos segmentos de negocio. B09 sigue por debajo de B00 en nuevo negocio. Se conserva B00 y todas las alternativas B01–B09, sin promoción o equivalencia declarada. Los intervalos nuevos son positivos, pero son exploratorios de 2023 sin ajuste por búsqueda adaptativa o las 45 parejas; no son confirmación de2024. El retiro mide influencia de evaluación con modelos fijos, no robustez al reentrenamiento.

Los factores normalizan predicciones dentro del ajuste; no son calibración independiente o interna fuera de muestra, y B00 también depende de los siniestros. A/E alrededor de0,98 hereda el nivel de referencia, sin probar calibración futura, reservas o último. No se impuso A/E=1, recortaron grupos o eligieron pesos después de resultados. Las sensibilidades publicadas usan adaptadores base fijos y no sustituyen escenarios reentrenados.

Pasaron 21 casos focales y {verification['passed']} controles del comprobador separado, con solapamiento. Se reconstruyeron factores sin respuestas en su entrada, momento de ajuste, contracción/orden, padres intactos, comparadores, replay con fit bloqueado, métricas e influencia. La revisión es propia de Codex. Los bloqueos de recetas previas y los hallazgos del selector conservan sus responsables; no se cierran por este resultado.

2024 sigue cerrado por instrucción expresa. No hay ajuste, predicción o score de precios de2024/test, apertura del ledger, lista final congelada, envíos o remoto. Se recibió la evidencia de instalación del selector y el seguimiento GOV005 en el foro, sin inferir autorización de apertura o actualizar sus cierres aquí.
'''
with (ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v3_resultado.md').open('x',encoding='utf-8') as f:f.write(body)
print(json.dumps({'documentation':rel(docpath),'proposed_index':rel(run/'active_index_proposed.json'),'checks':verification['passed'],'reference':'W2-B00','confirmation_2024_open':False},ensure_ascii=True))
