# R1 y F3c con el mismo tronco y preprocesamiento

Codex, 27 de octubre de 2026. Comparación local solicitada por el participante. Se conservan los dos archivos enviados y B00. No hubo otro envío, entrenamiento, ajuste de curvas ni inferencia de árboles.

La comparación cambia el diagnóstico de la diferencia entre las entregas. Los cambios de **calibración y posprocesamiento** explican grandes diferencias de precios. La regla de retirar el bloque propio en negocio nuevo afecta poco al total, pero modifica precios individuales de forma material. Todavía no podemos repartir la caída del D² público entre esos componentes ni afirmar qué alternativa será mejor en el privado.

## Qué se mantuvo fijo

Sobre la base `final_creible` de F3c se comparó el bloque propio completo con la regla que devuelve exactamente esa base en negocio nuevo y conserva el precio completo en renovación. Se repitió la comparación sobre la base T2b de R1, conservando los mismos parámetros de F2, forma, normalizadores y niveles. Esta segunda pareja usa el bloque completo aprendido con los parámetros de R1, no pretende ser el archivo histórico F3c.

| Tronco y preprocesamiento fijos | Bloque completo, millones CU | Base exacta en negocio nuevo, millones CU | Cambio del total |
|---|---:|---:|---:|
| F3c / `final_creible` | 87,2691 | 87,2923 | +0,0266 % |
| T2b / parámetros R1 | 83,3185 | 83,3315 | +0,0156 % |

Renovación queda igual dentro de cada pareja, con tolerancia de punto flotante en la segunda. En edificios el bloque propio es identidad: retirarlo no puede explicar que el total de edificios nuevos de R1 sea un 24,96 % menor que el de F3c.

El pequeño cambio de total no implica precios individuales parecidos. Sobre el tronco de F3c, retirar el bloque cambia los precios de autos nuevos un **11,40 % en promedio absoluto**, y los de contenidos nuevos un **10,48 %**. En contenidos nuevos, el percentil 95 del cambio absoluto es 23,97 %. Las subidas y bajadas se compensan en el total. Estas cifras describen precios; no miden errores predictivos ni una ganancia de D².

## Mismo operador completo sobre las dos entradas

Se aplicó después exactamente el operador R1 completo, con todas las variables, exposiciones y parámetros congelados, a las dos entradas de riesgo. La entrada histórica F de F3c conserva un factor global previo. Compararla directamente con la entrada de R1 mezcla ese factor con el efecto del tronco.

El registro histórico identifica **g = 1,187658238648521** y los hashes de la mezcla previa y de F. Se verificó en las 209.063 filas que F es la mezcla por ese g, dentro del redondeo de seis decimales. El factor no se reestimó con scores ni etiquetas nuevas.

| Entrada al mismo operador R1 | Total previsto, millones CU |
|---|---:|
| F histórico, incluido su g | 98,7173 |
| Mezcla histórica antes de g | 83,2423 |
| Entrada propia de R1 | 83,3315 |

Una vez separado el factor conocido, las entradas producen totales que difieren un **+0,1071 %** bajo el mismo operador. Por ramo y negocio, las razones entre esos totales van de **0,9711 a 1,0235**; la correlación global de logprecios es 0,9899. Esta proximidad de nivel no demuestra equivalencia de riesgos, rankings o rendimiento futuro. La mezcla histórica conserva su propia preparación y adaptación; no es riesgo fuente puro.

La primera comparación que incluía g mostraba una diferencia de −15,59 % y se conserva. La separación posterior explica por qué no debía atribuirse esa diferencia íntegra a fuente, año, semillas o F1. Tampoco convierte g en un multiplicador recomendable para el privado. La forma de motor renovación tiene potencia 0,9, por lo que el escalado de su entrada pasa al precio con esa potencia; se comprobó esa identidad, sin imponer homogeneidad incorrecta respecto a la entrada sola.

## Dónde revisar los niveles

El trazado de las etapas congeladas de R1 muestra que NCB y siniestros previos apenas cambian el total de estas celdas futuras. Los niveles terminales por celda tienen efectos mayores. Son multiplicadores sobre el precio después de F2 y forma común, no factores sobre la prima final de F3c.

| Celda | Razón de total tras NCB | Razón tras previos | Nivel terminal de la base R1 |
|---|---:|---:|---:|
| Autos nuevos | 1,0011 | 1,0011 | 1,4485 |
| Edificios nuevos | 1,0000 | 1,0010 | 0,8896 |
| Contenidos nuevos | 1,0000 | 0,9994 | 1,1859 |
| Autos renovación | 1,0115 | 1,0000 | 0,9177 |

La identidad contable de cuatro componentes también cierra la diferencia total de −3,9376 millones CU entre R1 y F3c. El retiro de la forma y el nivel públicos históricos C1/F2 aporta −7,9441 millones en la descomposición simétrica, mientras el resto de base y parámetros auxiliares aporta +3,9546 millones. Hay compensaciones grandes, especialmente en autos nuevos. Son atribuciones del **cambio de precios**, no de pérdidas reales ni de la caída de 0,01094 puntos de D².

## Consecuencias para el privado

Se mantiene la evidencia histórica protegida anterior, sin volver a ajustar ni remuestrear. Con el mismo T2b, la diferencia de R1 frente al bloque completo es −0,0000143, con intervalo condicional 95 % [−0,0004931; +0,0004670]. La decisión de apagar el bloque en todo negocio nuevo no tiene superioridad predictiva demostrada. Tampoco queda demostrada la superioridad del bloque completo en esa población. Las sensibilidades A1 y mezcla se conservan con su alcance original; no certifican el F3c histórico de tres semillas/F1/calibración pública.

La siguiente prueba debe concentrarse en **estabilidad y contracción del nivel por negocio**, manteniendo el mismo tronco, variables y normalizadores aprendidos en entrenamiento. Una opción estándar es contraer el nivel terminal de negocio nuevo hacia el nivel de su ramo, con credibilidad basada únicamente en sus siniestros positivos de entrenamiento y K=300 heredado. Renovación permanecería igual para aislar el cambio. Es un diseño para evaluar, no un ajuste adoptado ni una corrección deducida del público.

El contraste necesitará aprender solo en 2023, aplicar en 2024 con la valoración conocida, conservar los folds y comparar contra R1 y el bloque completo de la misma familia. Los criterios se fijarán antes del cálculo: beneficio frente a R1 respaldado por intervalo, protección de negocio nuevo y de las seis celdas, influencia y sensibilidad de coste último. Un fallo detendrá esa receta. La valoración única, los maestros sin snapshots y el cambio de composición siguen limitando la lectura prospectiva. No se asignarán porcentajes del score público a segmentos sin etiquetas ni se copiarán multiplicadores públicos para rescatar la entrega.

## Evidencia y alcance de la comprobación

Los planes se registraron en el foro antes de cada cálculo. Las identidades multiplicativas y aditivas pasan en las 209.063 filas, con errores relativos inferiores a 10⁻¹³; la descomposición simétrica se cotejó mediante los 24 órdenes y muestras con Decimal. El operador común reprodujo R1 completo y pasó inversión de orden y aplicación individual. Ambos CSV originales conservan sus hashes. Los archivos de comparación son Parquet privados, sin nuevo CSV de entrega.

Índice: `registro/semana2_R1_F3c_tronco_comun_actual.json`. Código: `herramientas/comparar_R1_F3c_tronco_comun.py`, `verificar_R1_F3c_tronco_comun.py`, `aplicar_operador_comun_R1_F3c.py` y `separar_nivel_R1_F3c.py`. La revisión es computacional propia, exploratoria después de búsqueda adaptativa; no es revisión profesional independiente ni prueba de superioridad privada.
