# La cola no observada y el nivel condicionado de 2023

Codex. Corte UTC 2026-10-24T00:13:37.890835+00:00. Dos interpretaciones de una cola del 10% producen casi el mismo ajuste observado y distintos niveles condicionados. Al renormalizar la mezcla, los tres modelos conservan sus predicciones observadas por identidad algebraica y el total nominal condicionado de 2023 aumenta alrededor de 2,5%. El score observado no identifica esa escala última. No se adopta un supuesto ni se promueve una receta.

## Qué se cambió y qué significa el contraste

Esta unidad sigue al [diagnóstico de capital y autos nuevos](CAPITAL_POR_FILA_Y_AUTOS_NUEVOS_2023.md). El [plan original](../../../registro/semana2_cola2023_plan_v1.json) se registró en el foro antes de ajustar o puntuar. Se mantienen T0, 50.094 periodos de 2023, 30.869 componentes y los cinco folds. Solo se usan los modelos estándar B00 (constante por ramo), B12 (constante por ramo/negocio) y B14 (GLM sin penalización con seis variables). Capital, clima y credibilidad no reciben cambios. La información de reporte y sus pesos se toma del ajuste 2023 propio de cada fold.

T10F conserva los pesos de coste por peril y usa el enlace guardado e_cost_mix_tail0.1. Reduce un 10% la completitud de bodily_injury y subsidence. Se reajustan la tasa/GLM dentro del ajuste de cada fold, con respuesta T0/e y peso sqrt(e). Los escenarios anteriores a tasa fija no hacían ese reajuste. Contenidos no tiene esos perils y se conserva exactamente.

T10R declara una interpretación distinta: si una fracción t del coste último de un peril queda fuera de observación, su coste último se divide por 1−t y su curva observada se multiplica por 1−t. Se renormalizan los pesos: w'_p=(w_p/(1−t_p))/Z, con Z=sum(w_p/(1−t_p)). Entonces sum(w'_p(1−t_p)q_p)=sum(w_pq_p)/Z. Esta es una hipótesis de masa de coste, no de número de siniestros. No prueba cómo se distribuye la severidad que falta ni su estacionariedad.

El enlace e_R=e_base/Z y la tasa r_R=Z·r_base dan e_R·r_R=e_base·r_base. Con GLM log, alpha0 y constantes Tweedie, esto equivale a desplazar el intercepto en logZ y conserva el óptimo bajo el nuevo enlace; no se vuelve a ajustar. No se extiende esa afirmación a modelos regularizados, anclas o árboles. Se verificó con curvas por peril, pesos renormalizados y predicciones nativas por otra vía.

| Ramo | Peso de coste largo entre folds | Aumento de tasa Z−1 entre folds |
| --- | ---: | ---: |
| motor | 32.761%–38.902% | 3.640%–4.322% |
| buildings | 6.295%–10.508% | 0.699%–1.168% |
| contents | 0.000%–0.000% | -0.000%–0.000% |

El total nominal condicionado es exposición nominal de esos mismos periodos de 2023 por su tasa, bajo la hipótesis de observación completa. No es una predicción de 2025, una nueva etiqueta observada o verdad de último. Las predicciones observadas siguen usando su exposición efectiva una sola vez.

## Resultado al reajustar y al transformar la escala

| Modelo | D² base | D² T10F reajustado | D² T10R | Nominal base, millones CU | Nominal T10F | Nominal T10R |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B00 | 0.06858169 | 0.06861450 | 0.06858169 | 15.7873 | 16.1475 | 16.1885 |
| B12 | 0.07491526 | 0.07492702 | 0.07491526 | 15.5441 | 15.8955 | 15.9356 |
| B14 | 0.08671008 | 0.08671999 | 0.08671008 | 15.6061 | 15.9582 | 15.9983 |

B14 pasa de un nominal condicionado de 15,6061 a 15,9582 millones CU en T10F (+2,256%) y a 15,9983 millones en T10R (+2,514%). En T10R su predicción observada por fila difiere de la base como máximo 1.82e-12 CU, precisión de máquina. D² se conserva. En T10F el D² global de B14 apenas cambia +0,00000991 y el total observado predicho baja unos 551 CU, pese a aumentar el nominal condicionado unos 352.141 CU.

Esto explica por qué una lectura favorable o estable del score no confirma la cola no observada. T10F y T10R son distintos supuestos explícitos. La mezcla por ramo mantiene una aproximación a la composición individual por peril. No se interpreta T10R como corrección económica demostrada de los datos ni se elige por su score idéntico.

## Incertidumbre exploratoria

Solo se calculan seis contrastes nuevos T10F, con 2.000 sorteos de componentes y los mismos números aleatorios guardados. T10R no recibe un bootstrap redundante de una identidad determinista. Se conserva el catálogo principal de 19 recetas y las comparaciones anteriores; estas seis configuraciones pertenecen a una sensibilidad de observación, no a una lista de candidatos con C0 común.

| Contraste | Delta D² | Intervalo exploratorio 95% | Delta sin 31 grupos favorables |
| --- | ---: | --- | ---: |
| T10F_W2-B00/W2-B00 | +0.00003281 | [+0.00000652; +0.00007938] | -0.00000409 |
| T10F_W2-B12/W2-B12 | +0.00001176 | [+0.00000011; +0.00003116] | -0.00000519 |
| T10F_W2-B14/W2-B14 | +0.00000991 | [-0.00000049; +0.00002583] | -0.00000596 |
| T10F_W2-B12/T10F_W2-B00 | +0.00631252 | [-0.00205640; +0.01837598] | -0.00738969 |
| T10F_W2-B14/T10F_W2-B00 | +0.01810549 | [-0.00623196; +0.04265142] | -0.01250654 |
| T10F_W2-B14/T10F_W2-B12 | +0.01179297 | [-0.00971430; +0.03168543] | -0.01285051 |

Los contrastes de cada T10F frente a su base son pequeños y no acreditan por sí solos un supuesto de cola. Los intervalos de B00 y B12 quedan sobre cero; el de B14 cruza cero. Los tres incrementos frente a sus bases cambian de signo al retirar sus 31 grupos más favorables. Las comparaciones entre familias dentro de T10F conservan el mismo objetivo y enlace de ese escenario. Después de búsqueda adaptativa no son confirmación temporal, intervalos simultáneos o validación de último. No se promueven, retiran o declaran equivalentes alternativas por estas cifras.

## Ejecución, correcciones y comprobación

Se completaron diez GLM nuevos y treinta constantes cerradas. Quince modelos de contenidos son copias exactas. Los 45 adaptadores de escala T10R no son ajustes nuevos. No se reestimaron curvas de reporte, auxiliares de credibilidad o modelos desarrollados. Los contadores propios pasan a 100 ajustes de precio y 90 constantes cerradas; los 30 auxiliares de la sexta tanda permanecen separados. El índice principal conserva su corte histórico; el índice específico de sensibilidad registra estos nuevos contadores.

La primera pasada se detuvo después de calcular tres constantes y antes de cualquier GLM, por tratar como diccionario la lista de detalles de B12 al guardar un recibo. Se preservó el intento y se registró en el foro una [continuación de implementación](../../../registro/semana2_cola2023_plan_v1a.json), sin cambiar hipótesis, recetas o parámetros. Las dos bundles ya guardadas se recuperaron con sus hashes; solo se calcularon las 27 constantes pendientes. Los snapshots originales conservan el fallo, sin reescribirlo como ejecución limpia.

El comprobador separado pasó 715 controles: fuentes y ámbitos, pesos por peril, fórmulas de ambas mezclas, óptimo escalar por minimización numérica, gradiente GLM, imputación de ajuste, replay exponencial sin fit, identidad observada/nominal, métricas, segmentos y los seis bootstrap por multiplicidades. Bloquea fit y no importa el productor. Es revisión propia de Codex, no profesional independiente.

Los adversos terminaron con 34 casos válidos. El primer corte tuvo 33 pases y un fallo de prueba: exigía igualdad binaria entre un racional convertido a float y una suma float. La diferencia fue 2,22e-16. La identidad racional exacta ya se cumplía; se corrigió la comparación flotante a tolerancia absoluta 1e-14 y se repitió solo ese caso, conservando el informe/código fallidos y los otros 33 pases. No se repitieron modelos, remuestreo o comprobaciones inalteradas. Los casos también prueban ausencia de cola, cola total, orden de perils, mezclas inválidas, intercepto nativo equivalente, costes/IDs envenenados sin efecto y rechazo de 2024/test/fold/ramo/duplicados.

## Condiciones y continuación

Sigue sin identificarse la masa de coste que no ha llegado, su severidad o la estacionariedad de reporte. La validación por grupos de 2023 al corte 2024-12-31 no es conocimiento disponible al inicio de 2023. Las reservas de caso continúan condicionadas; reajustar sus escenarios 0,75/1,25 queda expresamente pendiente para la siguiente unidad, no se presenta como terminado por este ensayo de cola.

B00 y todas las alternativas se conservan. El índice principal no se reescribe con supuestos de observación distintos. 2024 permanece cerrado por el participante, con ledger ausente, sin entrenamiento de precio, predicciones o scores de ese año o test. No hubo envíos, remoto, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. La siguiente unidad nocturna deberá registrar su prueba antes de ajustar reservas.

## Evidencia

- [Resultados](../../../privado/semana2/desarrollo2023/cola_20261024T001114Z_e5d1c211/report.json), [decisiones](../../../privado/semana2/desarrollo2023/cola_20261024T001114Z_e5d1c211/decision_journal.json).
- [Comprobador separado](../../../privado/semana2/desarrollo2023/cola_20261024T001114Z_e5d1c211/verifications/cola_20261024T001611Z_2ed4b58a.json), [adversos y corrección de precisión](../../../privado/semana2/desarrollo2023/cola_20261024T001114Z_e5d1c211/fixture_checks.json).
- [Intento fallido conservado](../../../privado/semana2/desarrollo2023/cola_20261024T001114Z_e5d1c211/failed_attempt.json).
- [Foro](../../../../Semana%202/Foro/FORO.md), comentarios 022–024.


## Corte posterior: reservas y C0 ante reportes tardíos

La [siguiente prueba](NIVEL_C0_REPORTES_Y_RESERVAS_2023.md) conserva esta evidencia de cola y añade reservas coherentes y un adverso del estimador C0. El [snapshot del índice de cola](../../../registro/semana2_sensibilidad_observacion_cola_v1_snapshot.json) conserva exactamente este corte; el índice activo recoge el avance.
