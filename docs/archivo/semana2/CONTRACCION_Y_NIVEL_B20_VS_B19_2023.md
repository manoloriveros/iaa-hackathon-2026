# Contracción y nivel de B20 frente a B19

Codex, corte UTC 2026-10-24T02:35:58.693876+00:00. Se compararon los quince pares de GLM guardados y los mismos doce grupos, veinte periodos de 2023, de la traza de B19. La norma conjunta se reduce en 15 de quince pares; hay 14 pares con alguna coordenada que crece en valor absoluto. El diagnóstico no cambia un modelo, T0/C0 o la referencia B00.

## Alcance y concurrencia

El primer borrador del diagnóstico encontró una unidad concurrente de atribución B20 que ya preparaba los cambios de tasa por grupos. Se conserva sin ejecutar y v2 se registró en el comentario 040 antes del cálculo. La fuente concurrente no estaba materializada al registrar. Se fijó entonces el cotejo del diseño común solo en veinte periodos, con replay nativo y reconstrucción manual. No se consumieron resultados que todavía no existían ni se repitió la descomposición completa de 50.094 filas. El trabajo nuevo compara coeficientes/transformaciones y hace replay nativo focal y una reconstrucción manual. No se repitió su análisis global de retirada de grupos, las suites 542/48 de B20 ni bootstrap. Una colisión con el archivo del cuerpo v1 detuvo la preparación de v2 después de guardar su plan, sin cálculos; se conservó el cuerpo anterior y se completó un cuerpo v2 separado, sin alterar fuentes o plan. La colaboración entre cálculos de Codex no se presenta como validación profesional independiente.

Se mantienen los cinco folds guardados, siete efectos por ramo y las transformaciones aprendidas dentro de cada ajuste. Se comprobaron medianas, medias/escalas y categorías/referencias iguales entre B19 y B20. La única diferencia de parámetros del estimador es alpha 0 frente a 1. El intercepto queda libre. Solo se reproducen las veinte predicciones OOF existentes de cada modelo para cotejo; no se producen precios con coeficientes alterados, nuevos aspirantes o un factor de normalización.

## Qué contrae la penalización

La reducción de norma L2 estandarizada va de 28,7 % a 61,4 %. Se observaron 33 excepciones de coordenada entre los quince pares. La norma suma cuadrados en el diseño estandarizado y las dummies fijadas; no se compara mezclando unidades originales distintas ni garantiza contracción de cada beta. La penalización one-hot depende de su referencia, que aquí no cambió.

| Contraste de tasa en escala original | B19: rango entre cinco folds | B20: rango entre cinco folds |
| --- | ---: | ---: |
| Edificios AD sí/no | 0,795–1,388 | 0,801–1,375 |
| Autos TPOnly/comprehensive | 0,567–0,857 | 0,759–1,005 |
| Autos TPFireTheft/comprehensive | 0,587–0,611 | 0,758–0,778 |
| Autos nuevo negocio | 1,978–2,481 | 1,972–2,462 |
| Edificios nuevo negocio | 0,856–1,217 | 0,820–1,144 |

Son cocientes condicionales de tasa del GLM, con los demás efectos fijos. Los ajustes comparten cuatro de cinco folds: su dispersión no es un intervalo de confianza independiente. Una menor dispersión no prueba mejor respuesta en cada segmento ni atribuye la mejora a cobertura sola, porque se penalizan todos los efectos.

La reducción de norma no resuelve el cambio de dirección de AD en edificios: ambos rangos siguen cruzando 1. En autos, third_party_only se acerca a 1 y el rango de B20 llega a superarlo ligeramente; el efecto de nuevo negocio permanece próximo al de B19. Son advertencias concretas para evitar presentar la regularización como estabilización uniforme.

## Nivel de los mismos grupos

| Ámbito fijo | Predicción B19 CU | Predicción B20 CU | Cambio del total |
| --- | ---: | ---: | ---: |
| Global 2023 | 15.436.941,83 | 15.126.408,70 | -2,01 % |
| Doce grupos, veinte periodos | 6.112,73 | 6.012,41 | -1,64 % |
| Cinco edificios adversos de B19 | 2.824,70 | 2.671,88 | -5,41 % |
| Cinco autos nuevos adversos de B19 | 1.506,80 | 1.689,13 | 12,10 % |

Estos totales usan la predicción existente con el mismo vínculo observado C0. El anexo privado conserva por separado los totales nominales condicionales de 2023, calculados como exposición nominal por tasa anual; no son estimaciones validadas de 2025. El intercepto no equivale a calibración agregada: el total resulta de todos los efectos, composición y exposiciones. Los cinco grupos por ámbito ya se fijaron por resultados de B19; no se reseleccionan a favor de B20.

| Caso de la selección | T0 realizado CU | Coste esperado B19 CU | Coste esperado B20 CU | Razón B20/B19 |
| --- | ---: | ---: | ---: | ---: |
| Autos nuevos, lesión corporal principal | 136.767,16 | 90,25 | 95,07 | 1,053 |
| Edificios, incendio OOF más adverso | 261.192,30 | 168,39 | 244,78 | 1,454 |
| Edificios, incendio influyente sobre AD | 286.093,00 | 340,33 | 334,29 | 0,982 |

Un coste esperado de periodo no es una severidad ni debe igualar un siniestro realizado. La [traza de origen](TRAZABILIDAD_SINIESTROS_B19_2023.md) confirmó que la lesión corporal principal y el incendio de 286.093 CU están cerrados y pagados. Se conservan aunque pesen en la evaluación; no se adopta una tarifa para estos casos ni se eliminan registros.

## Descomposición del cambio real

Con el mismo diseño Z, `log(tasa20/tasa19) = cambio de intercepto + cobertura + nuevo negocio + otros efectos`. Los términos siguientes son diferencias de los dos modelos guardados, en escala logarítmica, y suman el cambio completo:

| Caso | Intercepto | Cobertura | Nuevo negocio | Otros efectos | Total log |
| --- | ---: | ---: | ---: | ---: | ---: |
| Autos nuevos, lesión corporal principal | -0,423 | 0,291 | -0,003 | 0,187 | 0,052 |
| Edificios, incendio OOF más adverso | 0,243 | 0,005 | 0,002 | 0,125 | 0,374 |
| Edificios, incendio influyente sobre AD | 0,243 | 0,005 | 0,002 | -0,267 | -0,018 |

El centrado y las categorías base fijan el reparto. No es una atribución causal ni un modelo donde se cambió únicamente cobertura. Su igualdad se comprobó frente al replay nativo y mediante un predictor manual en escala original, con medianas y codificación guardadas.

Los mismos veinte periodos aportan 14.620,81 unidades de mejora de desviación guardada, frente a 38.299,18 globales. Equivale a 38,2 % de la ganancia neta; el resto aporta 23.678,36. El cociente usa ganancia neta, admite compensaciones y puede exceder 100 %: no es fracción de mejora bruta ni probabilidad. Los grupos estaban enriquecidos por errores previos de B19. No se calcula otra retirada o una validación nueva con este resultado.

## Comprobación y decisión

Pasaron 169 controles del productor, 690 verificaciones propias por otro método y 39 conciliaciones de lectura, con solapamiento. Se verificaron normas con fsum, balances por grupo/ámbito, escala original de coeficientes, transformaciones y veinte predictores manuales por modelo. El flujo real con C0 sintético incompatible falla antes de abrir modelos y producir coeficientes. Guardas de año, claves, objetivo y transformaciones rechazan casos adversos; las entradas de fit quedan bloqueadas. No se reentrena ni se repiten las verificaciones estadísticas originales.

La lectura queda preparada para conciliarse con la atribución concurrente cuando termine y mantiene las advertencias de concentración, segmentos, nivel y último. No promueve B20, retira B19 o congela una lista. No se adopta enrutamiento por grupo, otro alpha, cobertura, factor de nivel o mayor complejidad. Las conclusiones son exploratorias tras búsqueda adaptativa de 2023. B00 y todas las alternativas siguen conservados.

La exposición previa de un asunto externo se mantiene declarada, sin usar cifras o afirmar ceguera completa. 2024/test siguen cerrados: no precios, predicciones, scores, actas, SEL01 o ledger de esos ámbitos. Sin remoto, envíos, nuevos chats, delegación o cambios a otras automatizaciones. Documentación IAA §3 y Gobernanza §2.8 sustentan la separación de evidencia, decisiones y revisión propia; no hay aprobación humana o profesional independiente implícita.

Plan: [diagnóstico v2](../../../registro/semana2_b20_contraccion2023_plan_v2.json). Índice: `registro/semana2_b20_contraccion_actual.json`; datos por fila, fuentes y hashes quedan en privado. Foro 040/041. La siguiente unidad debe conciliar ambos diagnósticos terminados y consolidar la evidencia ya existente por ramo/negocio, sin repetir cálculos o iniciar otra tanda.


## Lectura de los casos fijados antes del diagnóstico

El incendio que ya era el primer grupo adverso de B19 aporta 13.724,81 unidades de la ganancia de desviación guardada de los doce componentes, 14.620,81 en total: aproximadamente 93,9% de esa ganancia neta seleccionada. Es una fracción neta con compensaciones, sin afirmar representatividad o una nueva validación. El incendio de 286.093 CU aporta −557,25 unidades: se conserva el resultado adverso.

En ambos incendios el término del cambio de cobertura es el mismo, +0,004636 log. El primero aumenta su coste esperado de periodo de 168,39 a 244,78 CU y el segundo baja de 340,33 a 334,29 CU. El término de otros efectos es +0,124759 en el primero y −0,267250 en el segundo. Esto muestra por qué un movimiento de cobertura no identifica por sí solo el cambio completo o la ganancia de pérdida.

En autos nuevos, la lesión corporal principal pasa de 90,25 a 95,07 CU esperadas, razón 1,053425. Su cambio log concilia como intercepto −0,423120, cobertura +0,291127, nuevo negocio −0,002903 y otros +0,186943, total +0,052047. Son dos modelos completos con codificación común, no una intervención causal o una nueva prima que deba igualar el siniestro realizado.

Son cuentas adicionales sobre los tres casos ya fijados y las mismas desviaciones existentes, sin nueva prueba de modelos, selección, ajuste, predicción o remuestreo. B00 y todas las alternativas conservados; 2024/test siguen cerrados en este trabajo. Se incorporan al informe de 041 y a la memoria de esta unidad, sin reescribir los comentarios anteriores.


## Conciliación de cierre con atribución B20 v1a

Codex, corte UTC 2026-10-24T02:41:45.473808+00:00. La atribución concurrente había terminado como v1a en otro directorio, sin cambiar el modo focal fijado antes del cálculo. Sus veinte términos de los mismos periodos concilian con este diagnóstico dentro de 2e-12. Se leyó su recibo corregido por SHA y se cotejó solo el subconjunto; no se repitieron sus pruebas o atribución global. La concordancia entre cálculos de Codex no es revisión profesional independiente.

El primer control de cierre asumía que v2 seguía en una entrada paralela; la continuidad real y el recibo de preparación muestran que pasó al carril principal al concluir la otra unidad. Falló esa comprobación después de registrar correctamente los resultados. Se conserva el fallo y se completa solo el cierre según el modo real, sin repetir registro, cálculos, modelos o verificaciones estadísticas. Ambas unidades quedan terminadas, B00 y alternativas conservados, 2024/test cerrados. Próximo paso: consolidar una matriz de riesgos por ramo/negocio con los recibos existentes, sin otra tanda.
