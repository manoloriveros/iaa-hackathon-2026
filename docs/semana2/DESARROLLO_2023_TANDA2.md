# Revisión del GLM y segunda tanda de desarrollo de 2023

Codex, 23 de octubre de 2026. Las nuevas recetas mejoran sus puntos de desarrollo y reducen las brechas de ajuste revisadas. W2-B03 tiene el mejor punto global de las seis recetas consultadas. Se conserva W2-B00: las tres diferencias nuevas frente a ella tienen intervalos exploratorios que cruzan cero y cambian de signo al retirar los 31 componentes más favorables. 2024 continúa cerrado.

El [plan v2](../../registro/semana2_desarrollo2023_plan_v2.json) y COD-S2-20261023-010 preceden a la prueba. El resultado está en COD-S2-20261023-011 del [foro](<../../../Semana 2/Foro/FORO.md>). El [índice activo](../../registro/semana2_desarrollo2023_actual.json) distingue la primera tanda, sus artefactos y esta ejecución. Los resultados de 2023 ya informaron esta nueva tanda: hay búsqueda adaptativa y la incertidumbre exploratoria no la corrige.

## Qué explicaba la primera brecha

La [revisión de v1](../../privado/semana2/desarrollo2023/revision_20261023T175646Z_4924665e/report.json) cargó únicamente datos y modelos guardados de 2023, con fit bloqueado. En edificios había 497 filas positivas y 12.083 sin coste. El GLM ganaba 0,07897 de contribución al D² completo de edificios sobre las filas sin coste; perdía más en las positivas, hasta dejar una diferencia neta de −0,06231 frente a la referencia. Es una descomposición por resultado observado, no un filtro que deba entrar como predictor.

Retirar solo cinco de los grupos más adversos cambiaba el signo de esa diferencia. Se conservaron todos los grupos y el objetivo íntegro. Los 26 capitales desconocidos de 2023 no tuvieron siniestros y apenas contribuían al deterioro. La revisión no justifica corregirlos por mil. Algunos coeficientes de categorías cambiaban de signo entre folds; se planteó mayor penalización sin seleccionar campos por su resultado.

En el último árbol de LightGBM se encontraron hojas con pocos siniestros positivos; en contenidos hubo hojas sin ninguno. Es un diagnóstico local de soporte, no una explicación causal de todo el bosque. min_child_samples=200 describe un parámetro aproximado por Hessianos y no garantiza doscientas filas reales por hoja, según [LightGBM 4.6](https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html#min_data_in_leaf). La revisión encontró hojas menores; se precisa la redacción de v1 y se conserva su receta.

## Recetas fijadas antes de probar

| Receta | Cambio registrado |
| --- | --- |
| W2-B03 | Alpha pasa de 1 a 10 solo en el GLM de edificios; autos y contenidos reutilizan exactamente B01 |
| W2-B04 | Primeros 25 árboles de cada B02 guardado; misma trayectoria y categorías, sin nuevo ajuste o elección de etapa por una curva de scores |
| W2-B05 | 80 árboles de profundidad uno, dos hojas, min_child_samples=1000 y L2=100; resto igual a B02 |

El prefijo usa la exportación por número de iteraciones de [Booster](https://lightgbm.readthedocs.io/en/v4.6.0/pythonapi/lightgbm.Booster.html). Se verificó igualdad con los primeros 25 árboles del padre y se reconstruyeron sus predicciones sumando valores de hojas. La receta simple cambia conjuntamente capacidad y regularización; no aísla la contribución causal de cada parámetro.

Se mantienen 50.094 periodos de 2023, 30.869 componentes y cinco folds. No cambian F0, T0, C0, pesos, exposición, semilla o particiones. Se hicieron veinte ajustes nuevos, diez reutilizaciones de bundles GLM y quince exportaciones de prefijos. Los tres comparadores de v1 se conservaron exactamente, incluida la referencia. La tanda y primera agregación tardaron 18.0 segundos en CPU con dos hilos; la revisión y documentación son trabajo adicional. No se calibraron niveles o mezclas.

## Resultado global fuera de muestra

El observado es 15,297 millones CU. Son predicciones del incurrido T0 con el vínculo C0, no scores de Kaggle ni validación contra el último real. A/E es observado dividido por predicho. El D² global usa un solo nulo sobre todas las filas.

| Receta | D² OOF 2023 | Predicho, millones CU | A/E |
| --- | ---: | ---: | ---: |
| W2-B00: Referencia | 0.06858 | 15.614 | 0.980 |
| W2-B01: GLM inicial | 0.06666 | 14.552 | 1.051 |
| W2-B02: LightGBM inicial, 300 árboles | -0.27353 | 7.559 | 2.024 |
| W2-B03: GLM, alpha=10 en edificios | 0.08672 | 14.320 | 1.068 |
| W2-B04: Prefijo LightGBM, 25 árboles | 0.07342 | 12.634 | 1.211 |
| W2-B05: Boosting simple, 80 árboles | 0.07986 | 14.113 | 1.084 |

La primera receta de GLM y el bosque de 300 árboles permanecen visibles y sin cambios. No se retira una alternativa por el mejor punto de otra.

| Nueva receta frente a B00 | Diferencia D² | Intervalo exploratorio 95 % | Diferencia retirando 31 grupos favorables |
| --- | ---: | --- | ---: |
| W2-B03 | 0.01814 | [-0.00230, 0.03745] | -0.00791 |
| W2-B04 | 0.00483 | [-0.01202, 0.02017] | -0.00665 |
| W2-B05 | 0.01128 | [-0.00304, 0.02280] | -0.00358 |

Los 2.000 remuestreos pareados usan los mismos componentes y sorteos que v1, con nulo recalculado en cada réplica. Se publican las quince parejas de las seis recetas en el [recibo](../../privado/semana2/desarrollo2023/dev2_20261023T180127Z_46d18106/diagnostics/pairs.json). Los intervalos son condicionales y sin ajuste de multiplicidad o búsqueda previa; no son confirmación simultánea de 2024. La inversión del diagnóstico de influencia tampoco demuestra equivalencia o inferioridad general. Las condiciones de incertidumbre e influencia permanecen abiertas.

## Qué cambió en edificios

| GLM de edificios | D² ajuste | D² OOF | Brecha | A/E OOF |
| --- | ---: | ---: | ---: | ---: |
| W2-B01 | 0.18548 | -0.04147 | 0.22694 | 1.091 |
| W2-B03 | 0.13228 | 0.01777 | 0.11452 | 1.140 |

El punto OOF de edificios mejora 0.05923, pero queda por debajo de la referencia del ramo (0.02085). La media de la desviación de coeficientes entre folds pasa de 0.0841 a 0.0337. Es variación descriptiva de cinco ajustes solapados, no incertidumbre inferencial de parámetros.

La penalización reduce la brecha y la pérdida, pero el nivel agregado observado de edificios empeora: A/E sube de 1.091 a 1.140. Una mejora de devianza no resuelve por sí sola esa diferencia de totales ni la incertidumbre del último. No se forzó A/E a uno. El [desglose de mecanismos](../../privado/semana2/desarrollo2023/dev2_20261023T180127Z_46d18106/diagnostics/mechanism_readout.json) conserva las contribuciones de filas positivas y sin coste.

## Qué cambió en LightGBM

| Receta | D² ajuste | D² OOF | Brecha |
| --- | ---: | ---: | ---: |
| W2-B01 | 0.18270 | 0.06666 | 0.11604 |
| W2-B03 | 0.16468 | 0.08672 | 0.07796 |
| W2-B02 | 0.53629 | -0.27353 | 0.80982 |
| W2-B04 | 0.20602 | 0.07342 | 0.13260 |
| W2-B05 | 0.14976 | 0.07986 | 0.06991 |

Las columnas de ajuste repiten cada fila en cuatro folds y solo son diagnósticas. El prefijo reduce la brecha de B02 de 0,80982 a 0.13260; la receta simple la reduce a 0.06991. Los nuevos puntos son positivos, pero conservan infrapredicción agregada observada. Los resultados son consistentes con exceso de capacidad en la receta inicial; no prueban que un único parámetro explique toda la diferencia.

| Ramo | B00 | B03 | B04 | B05 |
| --- | ---: | ---: | ---: | ---: |
| Autos | -0.00581 | 0.02026 | -0.00481 | -0.00829 |
| Edificios | 0.02085 | 0.01777 | 0.01606 | 0.02735 |
| Contenidos | 0.02893 | 0.07468 | 0.06298 | 0.08617 |

B03 mejora su antecedente en edificios y mantiene idénticos autos/contenidos de B01. B05 mejora los puntos de edificios/contenidos frente a B00 y empeora autos. Los D² por ramo tienen nulos propios; no se promedian para obtener el global.

| Segmento | B00 | B03 | B04 | B05 |
| --- | ---: | ---: | ---: | ---: |
| Nuevo negocio | 0.04783 | 0.05636 | 0.01279 | 0.00172 |
| Renovación | 0.07062 | 0.09001 | 0.08059 | 0.08929 |

Nuevo negocio es la marca contractual del periodo; no representa la prueba temporal de nuevos clientes de 2024. Ninguna tabla anterior ejecuta sus salvaguardas futuras de confirmación.

## Sensibilidad, verificación y decisión

Las siguientes diferencias frente a B00 mantienen las tasas OOF base fijas y cambian únicamente la observación y respuesta del escenario guardado. No reentrenan las recetas y no sustituyen los escenarios completos de confirmación.

| Escenario | B03−B00 | B04−B00 | B05−B00 |
| --- | ---: | ---: | ---: |
| reserve075 | 0.01886 | 0.00606 | 0.01237 |
| reserve125 | 0.01745 | 0.00365 | 0.01022 |
| late_cost05 | 0.01784 | 0.00425 | 0.01091 |
| late_cost10 | 0.01754 | 0.00366 | 0.01053 |

Pasaron 21 controles de rutas, guardas y prefijo y 1279 controles del comprobador separado. Los recuentos se solapan. Se contrastaron parámetros, transformaciones dentro de fold, gradiente GLM, árboles y categorías del prefijo, objetivos y exposición comunes, replay con fit bloqueado, métricas e intervalos por otra fórmula, influencia y sensibilidades. [Verificación](../../privado/semana2/desarrollo2023/dev2_20261023T180127Z_46d18106/verifications/20261023T180338Z_52cc32bc.json). Es revisión propia de Codex y no revisión profesional independiente.

Se mantiene W2-B00 como referencia y se conservan B01–B05. Los tres mecanismos cumplen la dirección descriptiva preinscrita, pero sus diferencias frente a la referencia siguen siendo inciertas y sensibles a pocos componentes. Los bloqueos DEV2023-B02-GENERALIZATION y S2-VAL-MOD-007 de la receta original permanecen con sus responsables; probar IDs nuevos no los cierra. Las [advertencias de esta tanda](../../privado/semana2/desarrollo2023/dev2_20261023T180127Z_46d18106/assessment.json) conservan incertidumbre, influencia, nivel y búsqueda.

2024 sigue cerrado por instrucción expresa del participante, con independencia del avance del encargo separado que repara el selector. No se abre el ledger, consulta un score de modelos de 2024 o congela la lista final aquí. Tampoco hay predicciones de test, envíos o entrenamiento remoto. Los [supuestos del último](VARIABLES_Y_ULTIMO.md) conservan su alcance. El [primer resultado](DESARROLLO_2023.md) permanece como corte histórico.

## Reproducir la comprobación

```powershell
& 'Preparación/.venv/Scripts/python.exe' 'Hackaton/Repositorio_IAA2026/herramientas/verificar_desarrollo2023_v2_semana2.py' --run 'Hackaton/Repositorio_IAA2026/privado/semana2/desarrollo2023/dev2_20261023T180127Z_46d18106'
```

El comando carga y comprueba, con fit bloqueado. Los modelos, OOF, filas, recetas y dependencias están identificados por SHA en el [manifiesto](../../privado/semana2/desarrollo2023/dev2_20261023T180127Z_46d18106/manifest.json); los anexos de revisión y cierre posteriores conservan sus propios cortes.


## Corte posterior: ancla de nivel e influencia

La [tercera prueba](DESARROLLO_2023_NIVEL_INFLUENCIA.md) contrasta nivel anclado y contracción fija preinscritos. El [snapshot del índice de esta segunda tanda](../../registro/semana2_desarrollo2023_v2_snapshot.json) conserva exactamente su registro; el índice activo recoge el avance posterior. Este documento y sus resultados mantienen el corte original.
