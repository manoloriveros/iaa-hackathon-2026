# Primeros modelos de desarrollo de 2023

Codex, 23 de octubre de 2026. La referencia conserva el mejor punto global de esta primera tanda. El GLM no demuestra mejora global; la receta inicial de LightGBM presenta un deterioro considerable. Se conservan las tres alternativas y sus resultados. La confirmación de 2024 sigue cerrada.

El [índice activo](../../../registro/semana2_desarrollo2023_actual.json) identifica recetas, modelos, predicciones y comprobaciones. La [preinscripción](../../../registro/semana2_desarrollo2023_plan_v1.json) y COD-S2-20261023-008 preceden al primer ajuste. El resultado se registra en COD-S2-20261023-009 del [foro](<../../../../Semana%202/Foro/FORO.md>).

## Qué se comparó

Son 50.094 periodos de 2023, con 30.869 componentes cliente-dirección y cinco folds ya guardados. Cada fila tiene una predicción fuera de muestra de cada receta, generada sin sus grupos, clientes o direcciones en el ajuste. Los 45 nodos incluyen quince constantes calculadas en forma cerrada y treinta estimadores (quince GLM y quince LightGBM). La tanda de cómputo, incluida su primera agregación, duró 60.0 segundos en CPU con dos hilos; preparar y revisar el flujo requirió trabajo adicional.

Se usó la lista F0 congelada, T0 como incurrido neto observado y el mismo vínculo C0 para las tres recetas, estimado fuera del fold. La respuesta fue Y/e y el peso sqrt(e), coherente con devianza total Tweedie 1,5 sin pesos adicionales de evaluación. La referencia es la constante que minimiza esa pérdida, no necesariamente sum(Y)/sum(e). No hubo calibración posterior, mezcla, nuevas semillas o búsqueda de parámetros.

La receta GLM fija penalización alpha=1, con imputación mediana, escala numérica y categorías dentro del ajuste. LightGBM fija 300 rondas, 15 hojas, profundidad 4, mínimo 200 filas y L2=10, sin parada sobre validación. Las implementaciones y sus parámetros se contrastaron con la documentación de [scikit-learn 1.7](https://scikit-learn.org/1.7/modules/generated/sklearn.linear_model.TweedieRegressor.html) y [LightGBM 4.6](https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html). Las versiones efectivas están en el [entorno](../../../privado/semana2/desarrollo2023/dev_20261023T173828Z_7efe46fc/environment.json).

## Resultado global fuera de muestra

El observado de 2023 es 15,297 millones CU. Estos resultados predicen T0 mediante C0; no son scores de Kaggle o exactitud frente al último real. D² usa todas las filas juntas y un nulo global común. A/E significa observado dividido por predicho.

| Receta | D² OOF 2023 | Predicho, millones CU | A/E |
| --- | ---: | ---: | ---: |
| Referencia constante (W2-B00) | 0.06858 | 15.614 | 0.980 |
| GLM regularizado (W2-B01) | 0.06666 | 14.552 | 1.051 |
| LightGBM limitado (W2-B02) | -0.27353 | 7.559 | 2.024 |

El GLM queda 0.00192 por debajo de la referencia. Su intervalo exploratorio incluye tanto mejoras como deterioros. No hay evidencia para reemplazar la referencia ni para afirmar equivalencia.

| Comparación | Diferencia D² | Intervalo exploratorio 95 % | Diferencia retirando 31 grupos favorables |
| --- | ---: | --- | ---: |
| W2-B01 frente a W2-B00 | -0.00192 | [-0.03811, 0.02869] | -0.03415 |
| W2-B02 frente a W2-B00 | -0.34211 | [-0.53319, -0.21631] | -0.36615 |
| W2-B02 frente a W2-B01 | -0.34019 | [-0.53345, -0.21874] | -0.35834 |

Se hicieron 2.000 remuestreos pareados de componentes, con semilla 2026102302 y los mismos sorteos entre parejas. Cada réplica recalcula la desviación nula. Los intervalos son condicionales, exploratorios y sin corrección por selección o multiplicidad; no son la confirmación Bonferroni de 2024. El retiro de grupos es un diagnóstico de influencia. Los [recibos](../../../privado/semana2/desarrollo2023/dev_20261023T173828Z_7efe46fc/diagnostics/pairs.json) y [réplicas](../../../privado/semana2/desarrollo2023/dev_20261023T173828Z_7efe46fc/diagnostics/bootstrap_2023.parquet) conservan precisión y hashes.

## Ramos, negocio y dispersión

Cada D² por ramo usa el nulo de su subconjunto. No se promedian para obtener el resultado global.

| Ramo | Referencia | GLM | LightGBM |
| --- | ---: | ---: | ---: |
| Autos | -0.00581 | 0.02026 | -0.35680 |
| Edificios | 0.02085 | -0.04147 | -0.41762 |
| Contenidos | 0.02893 | 0.07468 | -0.22120 |

El GLM mejora el punto en autos y contenidos, y empeora en edificios. Son pistas de desarrollo, no una decisión de mezclar o retirar recetas por ramo. Edificios tiene 497 filas con coste positivo y contenidos 482; autos tiene 3.027. La escasez y la severidad de esos eventos condicionan la estabilidad.

| Segmento | Referencia | GLM | LightGBM |
| --- | ---: | ---: | ---: |
| Nuevo negocio (5,974 filas) | 0.04783 | 0.01275 | -0.91082 |
| Renovación (44,120 filas) | 0.07062 | 0.07296 | -0.19235 |

Nuevo negocio es la marca contractual de cada periodo. No equivale a la validación temporal de clientes nuevos de 2024, que aún no se calculó. El buen ajuste de nivel del GLM en nuevo negocio tampoco garantiza menor devianza: su D² queda por debajo de la referencia en ese segmento.

| Receta | Media de D² por fold | Desviación entre cinco folds | Rango |
| --- | ---: | ---: | --- |
| Referencia constante | 0.06640 | 0.02667 | 0.03585 a 0.09654 |
| GLM regularizado | 0.06573 | 0.01731 | 0.03844 a 0.08173 |
| LightGBM limitado | -0.27052 | 0.19318 | -0.57102 a -0.10886 |

La media por fold es descriptiva. El score principal es el global OOF, cuya desviación nula es común a todo el portafolio. Los cinco folds no son cinco años o ensayos independientes.

## Diagnóstico del resultado adverso

La comparación desde modelos guardados muestra una brecha de generalización:

| Receta | D² dentro del ajuste | D² OOF |
| --- | ---: | ---: |
| Referencia constante | 0.07185 | 0.06858 |
| GLM regularizado | 0.18270 | 0.06666 |
| LightGBM limitado | 0.53629 | -0.27353 |

En la columna de ajuste, cada fila aparece en cuatro folds y se cuenta cuatro veces; es un diagnóstico dentro de muestra. LightGBM reduce mucho la pérdida de ajuste y deteriora los cinco folds y los tres ramos fuera de muestra. Además subestima el nivel agregado incluso en ajuste (A/E 1.778) y más en OOF (A/E 2.024). La brecha es compatible con sobreajuste y merece revisar capacidad, regularización y tratamiento de eventos raros. No identifica causalmente un hiperparámetro ni demuestra que toda la familia boosting falle.

No se corrigió el nivel, eligió una ronda intermedia o reentrenó otra configuración después de ver el resultado. DEV2023-B02-GENERALIZATION queda como bloqueo para avanzar esta receta como aspirante validado sin evidencia nueva de desarrollo. Su código, modelos y adversos se conservan. El [diagnóstico](../../../privado/semana2/desarrollo2023/dev_20261023T173828Z_7efe46fc/diagnostics/fit_vs_oof.json) se calculó sin permitir llamadas a fit.

## Sensibilidades y comprobaciones

Se recalcularon los escenarios de reserva y cola con las tasas OOF base fijas. La diferencia GLM−referencia sigue negativa en los cuatro. LightGBM también queda por debajo. Este diagnóstico de observación no reentrena las recetas y no sustituye los escenarios completos requeridos para confirmar un candidato. El [detalle](../../../privado/semana2/desarrollo2023/dev_20261023T173828Z_7efe46fc/diagnostics/observation_sensitivity.json) evita interpretar estos resultados como una validación de suficiencia de reservas.

Los quince casos sintéticos comprobaron pérdida, constante óptima y rechazo de otro año o test. El comprobador separado pasó 937 controles, reconstruyó métricas e intervalos y reprodujo exactamente las predicciones desde los 45 modelos guardados con fit bloqueado. También contrastó transformaciones solo con filas de ajuste, parámetros y estacionariedad numérica del GLM. Los recuentos se solapan. Es comprobación propia de Codex, no revisión profesional independiente. [Evidencia](../../../privado/semana2/desarrollo2023/dev_20261023T173828Z_7efe46fc/verifications/20261023T174057Z_33a474bd.json).

Objetivos, folds, matrices y vínculos conservaron sus hashes. El consumidor leyó objetivos y predictores con filtro año=2023 y rechazó otro año antes de ajustar o predecir. No produjo predicciones, métricas o modelos ajustados de 2024 ni test.

## Decisión y siguiente trabajo

Se mantiene W2-B00 como referencia designada previamente. B01 y B02 permanecen registrados, sin promoción, retirada o equivalencia declarada. La [evaluación de advertencias](../../../privado/semana2/desarrollo2023/dev_20261023T173828Z_7efe46fc/assessment.json) separa la mejora global no acreditada del GLM y el deterioro de LightGBM. Los próximos experimentos deberán preinscribir cómo contrastan la estructura por ramo y la generalización; esta tanda no fija otra receta por inferencia de estos resultados.

2024 continúa cerrado. Antes de abrir deben estar corregido y contrastado el vínculo semántico del selector, el productor y comprobador de métricas y la lista, prioridades, recetas y artefactos congelados que exige el [protocolo](../../semana2/PROTOCOLO_SELECCION.md). Congelar estas recetas de desarrollo no congela todavía la lista final de confirmación. El hallazgo S2-AUD-METRIC-BINDING permanece abierto en este corte. No se modificó el selector, abrió el ledger, envió a Kaggle o realizó entrenamiento remoto.

Las hipótesis de reserva, cola, reporte y estabilidad del maestro continúan descritas en [Variables y último](VARIABLES_Y_ULTIMO.md). Un mejor D² sobre T0 no las demuestra.

## Reproducir la comprobación

Desde la raíz del proyecto, con el entorno preparado:

```powershell
& 'Preparación/.venv/Scripts/python.exe' 'Hackaton/Repositorio_IAA2026/herramientas/verificar_desarrollo2023_semana2.py' --run 'Hackaton/Repositorio_IAA2026/privado/semana2/desarrollo2023/dev_20261023T173828Z_7efe46fc'
```

Ese comando carga estimadores y recalcula la comprobación sin entrenar. El productor src/semana2/entrenar_desarrollo2023.py crea otra corrida si se solicita repetir el ajuste; no se necesita para revisar los resultados guardados. El [manifiesto inicial](../../../privado/semana2/desarrollo2023/dev_20261023T173828Z_7efe46fc/manifest.json) conserva el corte del entrenamiento; la verificación, el diagnóstico y el cierre posteriores se identifican por separado.


## Corte posterior: segunda tanda

La [segunda tanda](DESARROLLO_2023_TANDA2.md) prueba las recetas preinscritas para las brechas identificadas aquí. El [snapshot del índice de esta primera tanda](../../../registro/semana2_desarrollo2023_v1_snapshot.json) conserva exactamente el registro original; el índice activo contiene el avance posterior. Las cifras y decisiones anteriores mantienen su corte.
