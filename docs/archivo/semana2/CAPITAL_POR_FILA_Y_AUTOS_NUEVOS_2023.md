# Capital por fila y credibilidad en autos nuevos

Codex. Corte UTC 2026-10-23T23:59:48.248018+00:00. La prueba registrada antes de calcular sus scores conserva los modelos estándar. Las tres correcciones nuevas empeoran el D² puntual de autos nuevos frente a B14. Los intervalos globales cruzan cero: esta tanda no establece superioridad, equivalencia o descarte. B00 sigue como referencia y 2024 permanece cerrado.

## Qué explica los cambios de capital

Se guardaron las 56 filas de 2023, sus valores bruto, dividido e imputado, el fold y el efecto separado de representación y reajuste. Para cada fila se volvió a predecir con B13 congelado, sustituyendo únicamente logcapital. El cociente satisface log(r_corregida/r_imputada)=beta_capital·(logcapital_corregido−mediana_del_ajuste). La discrepancia máxima de esta identidad es 8.88e-16. El reajuste B14 se mide después, con log(r_B14/r_B13_corregido). No se mezcla esa explicación con una nueva receta de precio.

| Ramo | Filas | Capital dividido, CU | Capital imputado previo según fold, CU | Cambio final de tasa | Mayor efecto absoluto del reajuste, log |
| --- | ---: | ---: | ---: | ---: | ---: |
| buildings | 26 | 80,000–366,000 | 225,000–226,000 | -60.70% a +59.90% | 0.00157 |
| contents | 30 | 10,400–108,100 | 35,300–35,500 | -62.36% a +154.09% | 0.00271 |

Los valores corregidos quedan dentro del rango normal de ajuste de cada fold; no son extrapolación univariante de capital. Eso tampoco garantiza soporte conjunto de las otras variables. El reajuste mueve como máximo 0,157%/0,272% en escala log, mientras la sustitución de un capital desconocido por uno propio explica los cambios grandes y su signo. No se debe interpretar como estabilidad de precio por póliza que el efecto agregado sea pequeño.

Las 56 filas tienen T0=0. El score premia una menor predicción en esas observaciones y no permite confirmar la moneda/unidad o severidad económica. Se conserva la decisión CAPS2-01 y su procedencia como hipótesis condicionada; no se retocan los capitales para mejorar ese score. B13, B14 y el F0 original permanecen guardados. Prima escrita solo audita escala; no es predictor. El detalle con identificadores queda privado.

## Dónde empeoró la credibilidad original

En los 2.620 autos nuevos hay 265 filas con coste positivo y 2.355 con coste cero. B15 reduce el predicho de 1,238 a 0,890 millones CU frente a 1,088 millones observados. La pérdida aumenta 34.727,49 en las positivas y baja 27.119,35 en las cero: saldo adverso 7.608,15. El fold 0 aporta 8.637,79, compensado parcialmente en otros folds. Los cinco grupos más perjudicados suman 18.085,65; esta cifra supera el saldo porque existen compensaciones. No son cinco grupos que expliquen una fracción acotada de la pérdida ni una regla para excluirlos.

El corrector original c=c_f·c_s reduce poco por frecuencia y mucho por severidad. La severidad recibe casi todo el peso del prior. La aplicación directa de c sobre B14 desplaza su coeficiente de negocio, pero no lo sustituye por el coeficiente creíble: el efecto bruto del GLM de precio ya es mayor que la suma de los efectos auxiliares. La estandarización de la variable binaria se deshace al comparar coeficientes. Esa diferencia entre objetivos y ajustes no demuestra un error de programación o causa única del deterioro.

| Fold | Theta precio | Theta auxiliares | Theta creíble | c frecuencia | c severidad | c sustitución |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.714 | 0.474 | 0.149 | 0.935 | 0.773 | 0.569 |
| 1 | 0.910 | 0.519 | 0.134 | 0.932 | 0.730 | 0.460 |
| 2 | 0.859 | 0.453 | 0.132 | 0.977 | 0.742 | 0.483 |
| 3 | 0.768 | 0.395 | 0.143 | 0.967 | 0.803 | 0.535 |
| 4 | 0.911 | 0.531 | 0.160 | 0.968 | 0.713 | 0.472 |

## Prueba registrada y resultado

El [plan v7](../../../registro/semana2_desarrollo2023_plan_v7.json) y el comentario COD-S2-20261024-020 preceden a las nuevas predicciones. B16 aplica solo c_f a autos nuevos; B17 solo c_s; B18 aplica exp(theta_creíble−theta_precio), sustituyendo el coeficiente bruto de negocio con intercepto y demás efectos congelados. Todas parten de B14 y conservan hogar y renovaciones exactamente. B15 sigue como comparación completa, pero su hogar también cambia; su comparación global con estas ablaciones no aísla únicamente autos.

Se usan los 50.094 periodos de 2023, los 30.869 componentes cliente-dirección y cinco folds guardados. T0, C0 y variables técnicas siguen idénticos. Cero nuevos ajustes de precio, auxiliares o calibración; se reutilizan las treinta estimaciones Poisson/Gamma v6 y se calculan quince factores algebraicos de autos. Treinta archivos nativos de hogar son copias exactas. Ningún factor consulta costes del retenido. No se usa un c estimado en todo 2023 o calibración ordinaria con OOF de otros folds.

| Receta | D² global | A/E global | D² autos nuevos | A/E autos nuevos | Predicho autos nuevos, millones CU |
| --- | ---: | ---: | ---: | ---: | ---: |
| B00 | 0.068582 | 0.980 | -0.130134 | 2.006 | 0.543 |
| B14 | 0.086710 | 0.991 | -0.010045 | 0.879 | 1.238 |
| B15 | 0.086061 | 1.014 | -0.033244 | 1.223 | 0.890 |
| B16 | 0.086551 | 0.995 | -0.012726 | 0.919 | 1.184 |
| B17 | 0.085750 | 1.012 | -0.026267 | 1.170 | 0.931 |
| B18 | 0.081896 | 1.033 | -0.091376 | 1.752 | 0.621 |

| Comparación global | Delta D² | Intervalo exploratorio 95% | Delta retirando 31 grupos favorables |
| --- | ---: | --- | ---: |
| B16/B14 | -0.00015868 | [-0.00092851; +0.00030689] | -0.00019211 |
| B17/B14 | -0.00096016 | [-0.00437606; +0.00154672] | -0.00111190 |
| B18/B14 | -0.00481377 | [-0.01341707; +0.00158824] | -0.00513303 |

Las tres correcciones nuevas tienen puntos negativos frente a B14; ninguna acredita mejora. B16 acerca A/E a uno, pero empeora D²: el nivel agregado no basta para elegir. La sustitución explícita empeora más, aunque su intervalo global también cruza cero. La diferencia de coeficientes detectada no queda resuelta como explicación causal ni como arreglo de desempeño. No se elige un cuarto peso a partir de esta lectura.

En B18 se conserva el intercepto de la representación original, antes de estandarizar la variable binaria. Multiplicar por exp((theta_nueva−theta_anterior)·nuevo_negocio) equivale a sustituir ese coeficiente y conservar la predicción de todas las renovaciones. Si se absorbiera el cambio en el coeficiente estandarizado, su intercepto numérico cambiaría para mantener ese mismo intercepto original. El adaptador conserva la equivalencia sin reentrenar.

| Corrección | Aumento pérdida positivas | Aumento pérdida ceros | Saldo adverso frente a B14 |
| --- | ---: | ---: | ---: |
| B15 | 34,727.49 | -27,119.35 | 7,608.15 |
| B16 | 4,862.69 | -3,983.46 | 879.23 |
| B17 | 28,985.33 | -23,665.17 | 5,320.16 |
| B18 | 78,517.43 | -51,844.84 | 26,672.59 |

Las pérdidas de frecuencia y severidad no son aditivas al multiplicar factores sobre una devianza no lineal. La tabla sirve para localizar consecuencias, no para sumar efectos causales. Se conservan las 16 OOF previas y sus 120 parejas exactamente. Solo se añadieron 51 parejas y sus 2.000 réplicas con el mismo flujo aleatorio. Tras 19 recetas adaptativas hay 171 comparaciones exploratorias sin corrección por búsqueda o multiplicidad. No se abre la confirmación temporal ni se congela una lista final.

## Comprobaciones y límites vigentes

Pasaron 31 adversos focales, 622 controles del comprobador separado y 18 conciliaciones adicionales de esta lectura. Los recuentos se solapan y no equivalen a experimentos independientes. El comprobador no importa el productor, bloquea fit y reconstruye la predicción como exp(X beta+intercepto), las métricas con fórmula general/API externa y el bootstrap mediante multiplicidades de grupos y productos matriciales. Verifica las 51 parejas nuevas, influencia, factores, coeficiente bruto, copias nativas, ámbitos, invariancia de renovaciones y la identidad de capital de las 56 filas. Los adversos prueban escalas equivalentes, envenenamiento de costes/identificadores sin cambio de precio y rechazo de 2024, test, duplicados, ramo/fold incorrecto o negocio inválido.

El prior desarrollado 2021–2023 y su estacionalidad siguen como artefactos recibidos de Claude, sin reproducción desde raw en esta tanda. Su incertidumbre se omite en Z; tau usa efectos correlacionados. Una validación por grupos de 2023 con ese prior no es un backtest prospectivo al inicio de 2023. Los escenarios de reservas y reportes tardíos se recalculan a tasa fija, sin reajustar C0 o demostrar el último de 2025. El clima propuesto sigue fuera del contrato prospectivo por dependencia futura. Es revisión técnica propia de Codex, no revisión profesional independiente.

Se mantienen B00 y B01–B18, sin promoción o retiro. Continúa la programación nocturna existente; una próxima prueba de nivel/cola y vínculo de observación necesitará receta previa solo en 2023. No se ajustará c a estos resultados. 2024 queda cerrado por instrucción expresa, con ledger ausente, sin precios/predicciones/scores de ese año o test. No hubo envíos, entrenamiento remoto, publicación externa o delegación.

## Evidencia reproducible

- [Resultados y contadores](../../../privado/semana2/desarrollo2023/dev7_20261023T235935Z_55507793/report.json).
- [Decisiones y condiciones](../../../privado/semana2/desarrollo2023/dev7_20261023T235935Z_55507793/decision_journal.json).
- [Revisión de predicciones y estadística](../../../privado/semana2/desarrollo2023/dev7_20261023T235935Z_55507793/verifications/v7_20261024T000045Z_9a6648a0.json).
- [Capital por fila privado](../../../privado/semana2/desarrollo2023/revision_filas_20261023T235757Z_cafaba7d/capital_56_rows.parquet).
- [Desglose de autos nuevos](../../../privado/semana2/desarrollo2023/dev7_20261023T235935Z_55507793/diagnostics/motor_new_components.json).
- [Foro con registro previo y resultados](../../../../Semana%202/Foro/FORO.md).


## Corte posterior del catálogo

El [octavo corte](GLM_COBERTURAS_2023.md) conserva exactamente este OOF y añade B19, un GLM con cobertura principal y T0/C0 iguales. Este índice se archiva en el [snapshot v7](../../../registro/semana2_desarrollo2023_v7_snapshot.json); no se reescriben resultados de capital o credibilidad.
