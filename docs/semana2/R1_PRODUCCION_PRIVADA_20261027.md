# Consecuencias de la revisión para el modelo

Codex, 27 de octubre de 2026. Trabajo solicitado sobre el chat «Evaluación del documento». La [auditoría y el contraste](REVISION_EVALUACION_DOCUMENTO_20261027.md) conservan las fuentes y la evidencia adversa. La valoración editorial de ese chat es una opinión provisional; no constituye la calificación del jurado ni una validación independiente.

## Qué cambia la decisión

La corrección de la cadena de validación sí aporta evidencia computacional: separa los componentes de cliente y dirección, aprende curvas, categorías, selección de rondas y normalizaciones dentro de sus ámbitos y comprueba invariancia ante etiquetas protegidas alteradas. Se cotejaron los hashes, las 24 parejas de artefactos de la ampliación y las 10.000 réplicas originales por otro cálculo. Esa comprobación respalda los cálculos, pero no deshace la búsqueda adaptativa ni convierte la nueva base de una semilla sin F1 en el F3c histórico de producción.

El bloque propio concentra su beneficio en renovaciones. En la reevaluación primaria, su efecto en negocio nuevo es incierto y autos nuevos pierde el piso del protocolo. La población futura tiene mucha más exposición de negocio nuevo. Por eso se registró R1 antes de calcularlo: todos los ramos usan exactamente la referencia sin el bloque propio en negocio nuevo; renovación conserva el bloque completo. Se mantuvo T2b como comparación primaria, con A1 y la mezcla fija como sensibilidades, sin escoger la mejor vista después de conocer sus resultados.

| Control exploratorio primario T2b | Resultado R1 |
|---|---:|
| Diferencia D² frente a base | +0,0023173 |
| Banda condicional de familia de 12 contrastes | [0,0005189; 0,0042882] |
| Diferencia en negocio nuevo frente a base | 0 exacto por construcción |
| Diferencia tras retirar 37 grupos favorables | +0,0001286 |
| Diferencia con composición futura frente a base | +0,0006885 |
| Peor diferencia en segmentos amplios, 50 escenarios | 0 |

R1 no demuestra una ganancia sobre el bloque completo: la diferencia global es −0,0000143 y su intervalo incluye cero. El cero de negocio nuevo demuestra que la regla devuelve la base, no que esa base sea suficiente. Los escenarios de la ampliación son condicionales al tronco fuente y sus curvas; no asignan probabilidades ni reentrenan toda la fuente. La banda de familia 12 no cubre toda la búsqueda histórica.

## Correspondencia con la producción

La alternativa usa los tres modelos fuente T2b de 2021–2023 ya auditados, con sus categorías y curvas de coste congeladas. Se aprendieron los parámetros cerrados del destino con las 109.296 filas emergentes de 2023–2024, mediante los mismos cinco folds por componentes y el mismo operador matemático. Mantener fija la base fuente evita sustituirla por otra receta al preparar el envío. El ajuste fuente con 2024 se pospone; 2024 permanece abierto como desarrollo adaptativo y sí interviene en la calibración destino.

Para 2025 se predice coste último del periodo: proporción de observación igual a uno y exposición inclusiva una sola vez. Se mantiene el clima suministrado hasta 2023 de la receta auditada, sin introducir clima futuro ni nuevas constantes del leaderboard. La historia usa avisos y ocurrencias anteriores al menor entre inicio y 1 de enero de 2025; no accede a información de siniestros posterior a la valoración conocida.

El código reprodujo exactamente las 59.202 cotizaciones del backtest y las salidas crudas de los modelos sobre las 109.296 filas históricas. Los objetivos conciliaron en céntimos con la base original. En las 209.063 filas futuras, otro operador escalar produjo los mismos precios; también pasaron los controles de orden, aplicación individual, composición de lotes, identificadores oficiales y valores positivos tras escribir el CSV. No se ajustaron árboles ni curvas nuevas. Hubo un fallo previo a la inferencia al exigir ocupación no nula; se archivó y se corrigió el control para comprobar enlaces completos y conservar ausencias legítimas, como admite el modelo validado.

Código de producción y transporte versionado; archivo admitido por SHA exacto. El envío consume como máximo un cupo, sin selección manual final ni promoción formal. El recibo definitivo y el estado se guardan en `registro/semana2_produccion_R1_privada_actual.json`. B00, F3c y las demás alternativas se conservan.

## Resultado de la entrega

Kaggle procesó el envío 57711536: D² público **0,15820**, frente al **0,16914** del F3c conservado. Se consumió un envío; el SDK confirmó nueve disponibles después. El resultado es adverso y no justifica promover R1 ni ajustar sus parámetros contra el público. El privado sigue desconocido.

La diferencia de −0,01094 no aísla el efecto de retirar el bloque propio en negocio nuevo. Cambian el tronco fuente, F1, semillas y constantes históricas respecto al F3c anterior. Un cotejo descriptivo, sin entrenar, encontró diferencias materiales de nivel: por ejemplo, el total previsto de edificios nuevos es el 75,04 % del de F3c. No hay etiquetas futuras por segmento para atribuir la caída a esa diferencia o corregirla. La comparación se guarda como diagnóstico, no como señal para multiplicar precios o enviar sondas.

Se comprobó además que los periodos históricos de los ámbitos usados no acaban después de la valoración; por tanto, la integración truncada de edades no explica este caso por una exposición histórica posterior al corte. El puente homogéneo y la reproducción de código tampoco acreditan suficiencia del coste último.

## Qué falta y qué revisar después

La prioridad sigue siendo resolver incertidumbres que afectan al privado. Faltan snapshots al cotizar para algunos atributos maestros, evidencia de desarrollo de reservas y suficiencia del coste último, y observaciones representativas de negocio nuevo y pólizas largas. La base sin el bloque propio conserva F2, forma común y atributos fuente con sus límites originales. La reponderación de composición mide sensibilidad, no aporta observaciones nuevas ni demuestra soporte conjunto.

Una prueba posterior debe partir de uno de esos fallos y conservar un comparador estándar y criterios previos. Primero hay que comparar la política conservadora con un comparador que mantenga exactamente el mismo tronco y preprocesamiento, separando el efecto de fuente/F1/semillas del bloque propio y del nivel último. Una segunda separación temporal solo sirve si existe historia legítima suficiente para aprender y evaluar; no debe fabricarse una confirmación a partir de los mismos datos adaptativos. La extensión fuente con 2024 requiere su propia correspondencia temporal y controles del aprendizaje. No se ajustarán pesos, ramos o exponentes para rescatar el resultado público de este único envío. Cualquier reproducción nueva debe citar sus propios hashes y ámbitos, y no presentarse como revisión profesional independiente.
