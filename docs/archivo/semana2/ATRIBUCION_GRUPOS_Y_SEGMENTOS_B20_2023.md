# Por qué se invierte la ventaja de B20 al retirar grupos favorables

Codex, corte UTC 2026-10-24T02:34:03.822304+00:00. La ventaja se invierte porque los componentes retirados aportaban más mejora que el saldo neto del portafolio. El resto ya tenía una diferencia agregada de pérdidas desfavorable. La descomposición usa exclusivamente los OOF de 2023 guardados, sin reajustar modelos, generar precios nuevos o repetir remuestreo.

## La cuenta que explica el signo

Para cada fila se define la ganancia como desviancia de la referencia menos desviancia de B20. Una ganancia positiva favorece a B20. La diferencia de D² es la suma de ganancias dividida por la desviancia nula común, positiva. Por tanto, el signo depende del numerador. Recalcular la nula al retirar filas modifica la magnitud; conservar la nula original mantiene la misma inversión.

| Referencia | Ganancia total de desviancia | Ganancia de sus 31 grupos favorables | Ganancia del resto | Delta D² completo | Delta D² del resto |
| --- | ---: | ---: | ---: | ---: | ---: |
| W2-B19 | 38,299.18 | 58,110.36 | -19,811.18 | +0.006912 | -0.003869 |
| W2-B14 | 14,803.66 | 48,637.02 | -33,833.36 | +0.002672 | -0.006513 |
| W2-B00 | 115,251.18 | 149,206.53 | -33,955.35 | +0.020800 | -0.006580 |

Las primeras tres columnas son diferencias de desviancia, no importes monetarios. Frente a B14: 48.637,02 − 33.833,36 = 14.803,66. Con la nula original, el resto aporta −0,006106; al recalcularla para las filas retenidas queda −0,006513. Ambas cuentas tienen signo negativo.

Los 31 grupos son el 0.1004% de los 30.869 componentes. Frente a B14 contienen 62 periodos, 31 con T0 positivo, y 1,671,486.38 CU de coste observado: 10.93% del total. Se retira cada componente completo, con sus filas de coste cero y otros ramos; no solo sus filas convenientes.

Ese conjunto aporta el 328.5% de la ganancia neta, pero el 24.4% de las ganancias brutas positivas. El porcentaje neto supera cien porque otros grupos compensan las mejoras con pérdidas. No significa que todos los grupos restantes empeoren: hay 13,393 componentes con ganancia positiva y 17,476 con ganancia negativa en el contraste completo.

La ordenación usa ganancia observada descendente y group_id ascendente para empates. En esa ordenación bastan los tres primeros grupos para invertir B20/B14; frente a B19 son diez y frente a B00 trece. Son prefijos descriptivos calculados con los mismos resultados que se diagnostican. No se adopta un tamaño de recorte, no se borran registros y no se trata al resto como una nueva muestra de validación.

## Qué segmentos sostienen o pierden la ganancia

La siguiente tabla usa siempre la nula global original. Sus aportaciones sí se suman para obtener el cambio global, a diferencia de los D² de cada segmento.

| Segmento, B20 frente a B14 | Aportación antes de retirar | Aportación del resto |
| --- | ---: | ---: |
| buildings_new_business | +0.000568 | -0.000240 |
| buildings_renewal | +0.000374 | -0.004673 |
| contents_new_business | -0.000103 | -0.000272 |
| contents_renewal | +0.001422 | +0.000566 |
| motor_new_business | -0.000556 | -0.001425 |
| motor_renewal | +0.000967 | -0.000062 |

En el resto frente a B14, renovación de edificios pierde 25.890,09 unidades de desviancia y autos nuevos pierde 7.894,23. Contenidos en renovación conserva una ganancia de 3.134,90. La inversión global no equivale a un deterioro uniforme de todas las filas o segmentos.

Separando por resultado observado, frente a B14 el resto pierde 28.198,55 en periodos con T0 positivo y 5.634,81 en periodos sin coste. Frente a B19 la composición es distinta: pierde 2.039,30 en positivos y 17.771,88 en ceros. La clasificación por T0 es retrospectiva y solo diagnóstica; no está disponible para decidir una tarifa.

La desviancia de potencia 1,5 permite separar exactamente la ganancia por fila en `4y(1/√μ_ref − 1/√μ_20)` y `4(√μ_ref − √μ_20)`. En los 31 grupos favorables frente a B14, el primer término aporta +48.924,82 y el segundo −287,80: la parte que escala con el coste observado domina esa mejora. En el resto ambos términos agregados son adversos. No son componentes causales del riesgo ni medidas de suficiencia.

## Los grupos dependen del comparador

Los conjuntos favorables frente a B19 y B14 comparten 21 grupos de 31; con el conjunto frente a B00 comparten cinco y cuatro, respectivamente. Al aplicar el mismo retiro a las otras parejas se obtiene:

| Referencia del contraste B20 | Retiro elegido frente a B19 | Retiro elegido frente a B14 | Retiro elegido frente a B00 |
| --- | ---: | ---: | ---: |
| W2-B19 | -0.003869 | -0.002443 | +0.007661 |
| W2-B14 | -0.003658 | -0.006513 | +0.005437 |
| W2-B00 | +0.033220 | +0.032439 | -0.006580 |

La diagonal reproduce el diagnóstico original. Las otras celdas no son pruebas independientes: comparten filas, modelos y selecciones observadas. Muestran que no existe una lista universal de componentes problemáticos. Retirar los seleccionados frente a B00, por ejemplo, no invierte B20 frente a B19 o B14.

La selección fija de doce grupos de la revisión anterior de B19 se conserva sin volver a elegirla. En ella B20 mejora 14.620,81 unidades de desviancia frente a B19, pero pierde 16.127,18 frente a B14. Esto describe una recuperación parcial del problema anterior, sin confirmar superioridad. Es una selección enriquecida por errores e influencia de B19, no una muestra nueva; la trazabilidad previa no autoriza eliminar sus costes.

## Qué hizo la contracción

Con las mismas matrices de diseño, el cambio de logtasa B20−B19 se descompone exactamente en cambio de intercepto, negocio nuevo, cobertura y los demás efectos. La suma concilia con el logaritmo del cociente de tasas guardadas en las 50.094 filas, con error absoluto máximo de 2.36e-15. No se ajustan coeficientes ni se construye otro precio.

En los 32 periodos positivos de los grupos favorables frente a B19, el cambio medio de logtasa es aproximadamente +0,305. Sus bloques medios son +0,183 de intercepto, +0,005 de negocio, +0,051 de cobertura y +0,066 de otros efectos. La intervención ridge modifica toda la fórmula; estos bloques dependen del centrado y de las referencias categóricas. No asignan causalmente la ganancia de desviancia a una cobertura ni prueban una mejora futura en siniestros grandes.

## Verificación y decisión

Pasaron 1014 comprobaciones separadas y 16 adversos, con solapamiento. La segunda implementación usa la expresión cuadrática de desviancia, math.fsum y diccionarios para grupos y rankings; verifica pérdidas, perfiles, particiones, nulas, selecciones cruzadas y los bloques logarítmicos con indicadores independientes. Los comandos reales rechazan una fuente cambiada y una repetición de la corrida antes de calcular. Fit permanece bloqueado.

El primer arranque del productor resolvió mal la raíz y no encontró la caché de PyArrow: falló antes de main y de leer los OOF. Se preservaron código, plan y fallo; la enmienda v1a corrigió solo la raíz antes del cálculo. El primer comprobador rechazó diez celdas con contraste propio indefinido: Parquet representa como NaN lo que JSON conserva como None cuando la nula es cero. Se corrigió esa lectura, conservando el recibo fallido; no se cambiaron valores del productor, modelos o datos. Los contrastes indefinidos siguen sin convertirse en cero.

La decisión es mantener B00 como referencia y conservar B01–B20. La atribución explica fragilidad de la ganancia observada; no identifica un error de origen, no demuestra que B20 sea inferior en toda población y no exige más complejidad. No se busca otro alpha, combina una receta por segmento o elimina un coste válido para mejorar una métrica. Las siguientes comprobaciones pueden revisar calibración con bandas fijadas en ajuste y artefactos existentes, con su propio criterio previo.

Cero entrenamientos, nuevas recetas de precio, precios nuevos o bootstrap. El contador se conserva en 195 ajustes de precio y 285 constantes, con auxiliares y curvas separados. 2024, test, actas, scores y ledger permanecen cerrados para este trabajo. Se mantiene declarada la exposición anterior de un título ajeno, sin usar sus cifras o afirmar ceguera completa. Sin envíos, remoto, delegación, publicación externa o cambios a otras automatizaciones. Revisión técnica propia, no profesional independiente.

[Plan y enmienda](../../../registro/semana2_b20_atribucion_plan_v1a.json), [índice](../../../registro/semana2_b20_atribucion_actual.json), [productor](../../../src/semana2/atribuir_b20_grupos2023.py), [verificador separado](../../../herramientas/verificar_atribucion_b20_2023.py) y [adversos](../../../herramientas/probar_atribucion_b20_2023.py). Las tablas por fila/grupo y sus IDs permanecen en `privado/semana2/desarrollo2023/b20_atribucion_20261024_v1a`, fuera de Git. El [ensayo B20](GLM_RIDGE_COBERTURAS_2023.md) conserva sus resultados y límites.
