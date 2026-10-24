"""Informe e índice desde la única tanda 2023 ya terminada; no entrena."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import json

REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,obj):
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')

ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args()
run=Path(args.run).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023')
report=read(run/'report.json');summary={x['model_id']:x for x in report['summary']}
verification_path=sorted((run/'verifications').glob('*.json'))[-1];verification=read(verification_path)
assert verification['failed']==0 and all(x['technical_complete'] for x in summary.values())
assert report['fit_nodes_failed']==0 and not report['scope_2024']['confirmation_open']
diag=read(run/'diagnostics/fit_vs_oof.json');fits={x['model_id']:x for x in diag['summary']}
segments=read(run/'diagnostics/segments.json');pairs=read(run/'diagnostics/pairs.json')['pairs']
pair=next(x for x in pairs if x['candidate']=='W2-B01' and x['reference']=='W2-B00')
assessment={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'development_2023_verified_no_promotion',
    'reference_retained':'W2-B00','alternatives_preserved':['W2-B01','W2-B02'],
    'reference_not_promoted_here':'W2-B00 was designated before fitting; this records development results, not a gate promotion',
    'warnings':[
        {'id':'DEV2023-B01-GLOBAL-GAIN','class':'condition','status':'open','effect':'No demonstrated global improvement; do not treat line gains as a global promotion or tune on 2024',
         'delta_D2':pair['delta_D2'],'exploratory_interval95':[pair['exploratory_lower95'],pair['exploratory_upper95']]},
        {'id':'DEV2023-B02-GENERALIZATION','class':'block','status':'open','effect':'Current 300-round recipe must not be advanced as a validated challenger without resolving large generalization/level deterioration through new preregistered 2023 evidence; preserve this recipe and adverse result',
         'training_D2':fits['W2-B02']['training_repeated_rows']['D2'],'OOF_D2':summary['W2-B02']['D2'],
         'OOF_actual_over_expected':summary['W2-B02']['actual_over_expected'],
         'interpretation':'Gap consistent with overfit; no causal isolation of a parameter or proof that boosting as a family fails'},
        {'id':'S2-AUD-METRIC-BINDING','class':'block','status':'open','effect':'2024 closed until selector fix independently contrasted and final recipes/evidence frozen; this task does not close another author finding'},
        {'id':'DEV2023-ULTIMATE-UNCERTAINTY','class':'condition','status':'open','effect':'Observed T0/C0 validation is conditional on reserve, tail, report and undated-master assumptions; not actual ultimate validation'}],
    'price_fit_years':[2023],'price_scored_years':[2023],'confirmation_2024_open':False,
    'confirmation_roster_frozen':False,'models_removed':[],'new_tuned_models':[],
    'scenario_scope':'Fixed base OOF rates only; not full refitted confirmation safeguards',
    'next_development_focus':'Separate additive structure by line and generalization/level deterioration before any new candidate recipe; preregister new experiments, retain existing artifacts',
    'independent_professional_validation':False}
dump(run/'assessment.json',assessment)
names={'W2-B00':'Referencia constante','W2-B01':'GLM regularizado','W2-B02':'LightGBM limitado'}
rows='\n'.join(f"| {names[mid]} ({mid}) | {summary[mid]['D2']:.5f} | {summary[mid]['predicted_total']/1e6:.3f} | {summary[mid]['actual_over_expected']:.3f} |" for mid in names)
line_rows=[]
for line,label in [('motor','Autos'),('buildings','Edificios'),('contents','Contenidos')]:
    vals=[next(x['D2'] for x in segments if x['model_id']==mid and x['segment']=='line' and x['label']==line) for mid in names]
    line_rows.append('| '+label+' | '+' | '.join(f'{v:.5f}' for v in vals)+' |')
fold_rows='\n'.join(f"| {names[mid]} | {fits[mid]['fold_D2_mean']:.5f} | {fits[mid]['fold_D2_sample_std']:.5f} | {fits[mid]['fold_D2_min']:.5f} a {fits[mid]['fold_D2_max']:.5f} |" for mid in names)
fit_rows='\n'.join(f"| {names[mid]} | {fits[mid]['training_repeated_rows']['D2']:.5f} | {summary[mid]['D2']:.5f} |" for mid in names)
business_rows=[]
for business,label in [('new_business','Nuevo negocio'),('renewal','Renovación')]:
    items=[next(x for x in segments if x['model_id']==mid and x['segment']=='business' and x['label']==business) for mid in names]
    business_rows.append('| '+label+f" ({items[0]['rows']:,} filas) | "+' | '.join(f"{x['D2']:.5f}" for x in items)+' |')
pair_rows='\n'.join(f"| {p['candidate']} frente a {p['reference']} | {p['delta_D2']:.5f} | [{p['exploratory_lower95']:.5f}, {p['exploratory_upper95']:.5f}] | {p['delta_after_removal']:.5f} |" for p in pairs)
relative_run='../../'+run.relative_to(REPO).as_posix()
doc=f'''# Primeros modelos de desarrollo de 2023

Codex, 23 de octubre de 2026. La referencia conserva el mejor punto global de esta primera tanda. El GLM no demuestra mejora global; la receta inicial de LightGBM presenta un deterioro considerable. Se conservan las tres alternativas y sus resultados. La confirmación de 2024 sigue cerrada.

El [índice activo](../../registro/semana2_desarrollo2023_actual.json) identifica recetas, modelos, predicciones y comprobaciones. La [preinscripción](../../registro/semana2_desarrollo2023_plan_v1.json) y COD-S2-20261023-008 preceden al primer ajuste. El resultado se registra en COD-S2-20261023-009 del [foro](<../../../Semana 2/Foro/FORO.md>).

## Qué se comparó

Son 50.094 periodos de 2023, con 30.869 componentes cliente-dirección y cinco folds ya guardados. Cada fila tiene una predicción fuera de muestra de cada receta, generada sin sus grupos, clientes o direcciones en el ajuste. Los 45 nodos incluyen quince constantes calculadas en forma cerrada y treinta estimadores (quince GLM y quince LightGBM). La tanda de cómputo, incluida su primera agregación, duró {report['elapsed_seconds']:.1f} segundos en CPU con dos hilos; preparar y revisar el flujo requirió trabajo adicional.

Se usó la lista F0 congelada, T0 como incurrido neto observado y el mismo vínculo C0 para las tres recetas, estimado fuera del fold. La respuesta fue Y/e y el peso sqrt(e), coherente con devianza total Tweedie 1,5 sin pesos adicionales de evaluación. La referencia es la constante que minimiza esa pérdida, no necesariamente sum(Y)/sum(e). No hubo calibración posterior, mezcla, nuevas semillas o búsqueda de parámetros.

La receta GLM fija penalización alpha=1, con imputación mediana, escala numérica y categorías dentro del ajuste. LightGBM fija 300 rondas, 15 hojas, profundidad 4, mínimo 200 filas y L2=10, sin parada sobre validación. Las implementaciones y sus parámetros se contrastaron con la documentación de [scikit-learn 1.7](https://scikit-learn.org/1.7/modules/generated/sklearn.linear_model.TweedieRegressor.html) y [LightGBM 4.6](https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html). Las versiones efectivas están en el [entorno]({relative_run}/environment.json).

## Resultado global fuera de muestra

El observado de 2023 es 15,297 millones CU. Estos resultados predicen T0 mediante C0; no son scores de Kaggle o exactitud frente al último real. D² usa todas las filas juntas y un nulo global común. A/E significa observado dividido por predicho.

| Receta | D² OOF 2023 | Predicho, millones CU | A/E |
| --- | ---: | ---: | ---: |
{rows}

El GLM queda {abs(pair['delta_D2']):.5f} por debajo de la referencia. Su intervalo exploratorio incluye tanto mejoras como deterioros. No hay evidencia para reemplazar la referencia ni para afirmar equivalencia.

| Comparación | Diferencia D² | Intervalo exploratorio 95 % | Diferencia retirando 31 grupos favorables |
| --- | ---: | --- | ---: |
{pair_rows}

Se hicieron 2.000 remuestreos pareados de componentes, con semilla 2026102302 y los mismos sorteos entre parejas. Cada réplica recalcula la desviación nula. Los intervalos son condicionales, exploratorios y sin corrección por selección o multiplicidad; no son la confirmación Bonferroni de 2024. El retiro de grupos es un diagnóstico de influencia. Los [recibos]({relative_run}/diagnostics/pairs.json) y [réplicas]({relative_run}/diagnostics/bootstrap_2023.parquet) conservan precisión y hashes.

## Ramos, negocio y dispersión

Cada D² por ramo usa el nulo de su subconjunto. No se promedian para obtener el resultado global.

| Ramo | Referencia | GLM | LightGBM |
| --- | ---: | ---: | ---: |
{chr(10).join(line_rows)}

El GLM mejora el punto en autos y contenidos, y empeora en edificios. Son pistas de desarrollo, no una decisión de mezclar o retirar recetas por ramo. Edificios tiene 497 filas con coste positivo y contenidos 482; autos tiene 3.027. La escasez y la severidad de esos eventos condicionan la estabilidad.

| Segmento | Referencia | GLM | LightGBM |
| --- | ---: | ---: | ---: |
{chr(10).join(business_rows)}

Nuevo negocio es la marca contractual de cada periodo. No equivale a la validación temporal de clientes nuevos de 2024, que aún no se calculó. El buen ajuste de nivel del GLM en nuevo negocio tampoco garantiza menor devianza: su D² queda por debajo de la referencia en ese segmento.

| Receta | Media de D² por fold | Desviación entre cinco folds | Rango |
| --- | ---: | ---: | --- |
{fold_rows}

La media por fold es descriptiva. El score principal es el global OOF, cuya desviación nula es común a todo el portafolio. Los cinco folds no son cinco años o ensayos independientes.

## Diagnóstico del resultado adverso

La comparación desde modelos guardados muestra una brecha de generalización:

| Receta | D² dentro del ajuste | D² OOF |
| --- | ---: | ---: |
{fit_rows}

En la columna de ajuste, cada fila aparece en cuatro folds y se cuenta cuatro veces; es un diagnóstico dentro de muestra. LightGBM reduce mucho la pérdida de ajuste y deteriora los cinco folds y los tres ramos fuera de muestra. Además subestima el nivel agregado incluso en ajuste (A/E {fits['W2-B02']['training_repeated_rows']['actual_over_expected']:.3f}) y más en OOF (A/E {summary['W2-B02']['actual_over_expected']:.3f}). La brecha es compatible con sobreajuste y merece revisar capacidad, regularización y tratamiento de eventos raros. No identifica causalmente un hiperparámetro ni demuestra que toda la familia boosting falle.

No se corrigió el nivel, eligió una ronda intermedia o reentrenó otra configuración después de ver el resultado. DEV2023-B02-GENERALIZATION queda como bloqueo para avanzar esta receta como aspirante validado sin evidencia nueva de desarrollo. Su código, modelos y adversos se conservan. El [diagnóstico]({relative_run}/diagnostics/fit_vs_oof.json) se calculó sin permitir llamadas a fit.

## Sensibilidades y comprobaciones

Se recalcularon los escenarios de reserva y cola con las tasas OOF base fijas. La diferencia GLM−referencia sigue negativa en los cuatro. LightGBM también queda por debajo. Este diagnóstico de observación no reentrena las recetas y no sustituye los escenarios completos requeridos para confirmar un candidato. El [detalle]({relative_run}/diagnostics/observation_sensitivity.json) evita interpretar estos resultados como una validación de suficiencia de reservas.

Los quince casos sintéticos comprobaron pérdida, constante óptima y rechazo de otro año o test. El comprobador separado pasó {verification['passed']} controles, reconstruyó métricas e intervalos y reprodujo exactamente las predicciones desde los 45 modelos guardados con fit bloqueado. También contrastó transformaciones solo con filas de ajuste, parámetros y estacionariedad numérica del GLM. Los recuentos se solapan. Es comprobación propia de Codex, no revisión profesional independiente. [Evidencia]({relative_run}/{verification_path.relative_to(run).as_posix()}).

Objetivos, folds, matrices y vínculos conservaron sus hashes. El consumidor leyó objetivos y predictores con filtro año=2023 y rechazó otro año antes de ajustar o predecir. No produjo predicciones, métricas o modelos ajustados de 2024 ni test.

## Decisión y siguiente trabajo

Se mantiene W2-B00 como referencia designada previamente. B01 y B02 permanecen registrados, sin promoción, retirada o equivalencia declarada. La [evaluación de advertencias]({relative_run}/assessment.json) separa la mejora global no acreditada del GLM y el deterioro de LightGBM. Los próximos experimentos deberán preinscribir cómo contrastan la estructura por ramo y la generalización; esta tanda no fija otra receta por inferencia de estos resultados.

2024 continúa cerrado. Antes de abrir deben estar corregido y contrastado el vínculo semántico del selector, el productor y comprobador de métricas y la lista, prioridades, recetas y artefactos congelados que exige el [protocolo](PROTOCOLO_SELECCION.md). Congelar estas recetas de desarrollo no congela todavía la lista final de confirmación. El hallazgo S2-AUD-METRIC-BINDING permanece abierto en este corte. No se modificó el selector, abrió el ledger, envió a Kaggle o realizó entrenamiento remoto.

Las hipótesis de reserva, cola, reporte y estabilidad del maestro continúan descritas en [Variables y último](VARIABLES_Y_ULTIMO.md). Un mejor D² sobre T0 no las demuestra.

## Reproducir la comprobación

Desde la raíz del proyecto, con el entorno preparado:

```powershell
& 'Preparación/.venv/Scripts/python.exe' 'Hackaton/Repositorio_IAA2026/herramientas/verificar_desarrollo2023_semana2.py' --run '{rel(run)}'
```

Ese comando carga estimadores y recalcula la comprobación sin entrenar. El productor src/semana2/entrenar_desarrollo2023.py crea otra corrida si se solicita repetir el ajuste; no se necesita para revisar los resultados guardados. El [manifiesto inicial]({relative_run}/manifest.json) conserva el corte del entrenamiento; la verificación, el diagnóstico y el cierre posteriores se identifican por separado.
'''
doc_path=REPO/'docs/semana2/DESARROLLO_2023.md'
with doc_path.open('x',encoding='utf-8') as f:f.write(doc)
index={'id':report['id'],'author':'Codex','as_of_utc':datetime.now(timezone.utc).isoformat(),'path_base':'workspace_root',
       'status':assessment['status'],'run':rel(run),'report':rel(run/'report.json'),'report_sha256':sha(run/'report.json'),
       'documentation':rel(doc_path),'plan':rel(REPO/'registro/semana2_desarrollo2023_plan_v1.json'),'plan_sha256':report['plan_sha256'],
       'producer':rel(REPO/'src/semana2/entrenar_desarrollo2023.py'),'producer_sha256':report['code_sha256'],
       'oof':rel(run/'oof_2023.parquet'),'oof_sha256':sha(run/'oof_2023.parquet'),
       'manifest':rel(run/'manifest.json'),'manifest_sha256':sha(run/'manifest.json'),
       'verification':{'path':rel(verification_path),'sha256':sha(verification_path),'passed':verification['passed'],'failed':0},
       'assessment':rel(run/'assessment.json'),'assessment_sha256':sha(run/'assessment.json'),
       'training_years':[2023],'scored_years':[2023],'rows_per_model':50094,'groups':30869,'folds':5,
       'price_estimators_fitted':30,'closed_form_constants_fitted':15,'fit_nodes':45,
       'summary':report['summary'],'pairs':pairs,'development_recipes_frozen':True,'final_confirmation_roster_frozen':False,
       'reference':'W2-B00','alternatives_preserved':['W2-B01','W2-B02'],'promotion':False,'confirmation_2024_open':False,
       'selector_finding':'S2-AUD-METRIC-BINDING open; operational owner closure required',
       'forum_prior':'COD-S2-20261023-008','forum_result':'COD-S2-20261023-009',
       'professional_independent_validation':False,'human_review':'pending','submissions':0}
dump(REPO/'registro/semana2_desarrollo2023_actual.json',index)
body=f'''Codex. Cierro la primera tanda preinscrita en COD-S2-20261023-008, por autorización directa del participante. Se completaron los cinco folds persistidos de 2023 para tres ramos y tres recetas: quince constantes y treinta estimadores, sin fallos de ajuste. Hay una predicción OOF por cada una de las 50.094 filas y cada receta. El [informe](../../Repositorio_IAA2026/docs/semana2/DESARROLLO_2023.md) y el [índice activo](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json) identifican todos los artefactos.

| Receta | D² OOF 2023 | Predicho, millones CU | A/E |
| --- | ---: | ---: | ---: |
{rows}

El observado es 15,297 millones CU. Se evaluó T0 con el mismo vínculo C0, sin pesos extra de evaluación, calibración posterior o mezcla. No son resultados de último real ni de Kaggle.

GLM−referencia: {pair['delta_D2']:.5f}, con intervalo exploratorio del 95 % [{pair['exploratory_lower95']:.5f}, {pair['exploratory_upper95']:.5f}], 2.000 remuestreos de componentes pareados. No acredita mejora global ni equivalencia. El GLM mejora el punto en autos/contenidos y empeora en edificios y nuevo negocio. Al retirar los 31 grupos más favorables a la diferencia, esta queda en {pair['delta_after_removal']:.5f}. La referencia se mantiene; las otras recetas se conservan.

LightGBM queda por debajo en los cinco folds y los tres ramos. D² dentro de ajuste {fits['W2-B02']['training_repeated_rows']['D2']:.5f} frente a {summary['W2-B02']['D2']:.5f} OOF y A/E OOF {summary['W2-B02']['actual_over_expected']:.3f}. Es compatible con sobreajuste y deterioro de nivel, sin aislar causalmente un parámetro. No se reescaló, eligió otra ronda ni retocó la receta. DEV2023-B02-GENERALIZATION impide avanzar esta receta como aspirante validado sin nueva evidencia de desarrollo. No se retira la familia ni se borran resultados adversos.

Los quince casos conocidos y {verification['passed']} controles del comprobador separado pasaron; los recuentos se solapan. Se reprodujeron las predicciones desde los modelos guardados con fit bloqueado y se cotejaron pérdida, constantes, transformaciones dentro del fold, parámetros, gradientes GLM, intervalos e influencia. Es revisión propia de Codex. Las sensibilidades de reserva/cola usaron tasas base fijas: ambas alternativas siguen por debajo, pero esto no sustituye reentrenamientos o pruebas completas de confirmación.

Solo se materializó 2023 para el consumidor de precios. No hay ajuste, predicción o score de 2024 o test, envíos, remoto, promoción o lista final congelada. El ledger sigue sin abrir. S2-AUD-METRIC-BINDING continúa abierto; el trabajo de cierre coordinado en COD-S2-IA-20261023-CIERRE-ENCARGO conserva su alcance y responsable. Mantengo 2024 cerrado hasta que se corrija y contraste el selector y se congelen recetas, lista y evidencias requeridas. No atribuyo cierre a ese trabajo por este resultado.
'''
body_path=ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_resultado.md'
with body_path.open('x',encoding='utf-8') as f:f.write(body)
print(json.dumps({'documentation':rel(doc_path),'index':rel(REPO/'registro/semana2_desarrollo2023_actual.json'),
                  'forum_body':rel(body_path),'models':3,'promoted':False},ensure_ascii=True))
