# Trazabilidad de los siniestros que influyen en B19

Codex, corte UTC 2026-10-24T02:18:42.390763+00:00. Se cotejaron 12 componentes, 20 periodos y 12 siniestros aceptados de 2023 contra los originales. Pagos, recuperaciones, fechas, estado y asignación al periodo coinciden con los artefactos usados. El siniestro que más pesa en el deterioro de autos nuevos está cerrado y totalmente pagado. No aparece un error de origen que justifique quitarlo o modificar el objetivo.

## Qué se revisó

La selección fue registrada en el comentario 038 antes del cálculo: unión de los cinco componentes OOF más adversos de edificios y autos nuevos, y el de mayor influencia absoluta sobre cobertura de cada uno de los diez ajustes guardados de esos ramos. La unión contiene doce grupos; las razones de selección se solapan y no se suman como muestras distintas. Se conservaron todos sus periodos, incluidos los de coste cero y otros ramos. La selección es posterior a resultados de B19 y no representa al portafolio completo.

Los originales se consultaron con filtros por póliza y fecha de pérdida/periodo de 2023. La valoración fija del 31 de diciembre de 2024 admite reportes posteriores a 2023 sobre esos siniestros. No se consultaron precios, predicciones, scores, test, SEL01 o ledger de 2024. No hubo ajustes, nuevos modelos, predicciones, scores o bootstrap. B00 y todas las alternativas permanecen guardados; el catálogo activo de otras continuaciones no se sustituye.

## Pagado y reserva tienen efectos distintos

| Ramo, solo selección revisada | Siniestros | Pagado CU | Reserva CU | Recuperaciones CU | T0 neto CU |
| --- | ---: | ---: | ---: | ---: | ---: |
| buildings | 6 | 1.325.514,09 | 74.089,21 | 0,00 | 1.399.603,30 |
| motor | 6 | 201.475,05 | 14.954,51 | 0,00 | 216.429,56 |

La selección suma 1.616.032,86 CU de T0, con 89.043,72 CU de reserva, 5.51% del neto. Hay 10 cerrados y 2 abiertos. No aparecen recuperaciones, reservas en cerrados o recuperaciones superiores a pagos en estos doce casos. No hay rechazados dentro de esta selección; eso no modifica su exclusión del objetivo general.

El componente principal de autos nuevos es una lesión corporal de 136.767,16 CU, pagada por completo y cerrada: pérdida el 1 de diciembre de 2023, reporte el 28 de enero de 2024, retraso de 58 días. No es una reserva abierta ni un reporte de más de 365 días. Multiplicar su reserva actual por 0,75 o 1,25 deja ese T0 observado igual. No prueba ausencia de incertidumbre en último, reaperturas o recuperación futura; tampoco resuelve la incertidumbre del vínculo C0 o los siniestros aún no reportados.

En los cinco incendios OOF más adversos de edificios hay un abierto con 149.180,40 CU de incurrido neto: 75.091,19 pagados y 74.089,21 de reserva. Los otros cuatro están cerrados, pagados y sin reserva actual. El incendio de 286.093,00 CU, que más influye sobre el coeficiente AD en cuatro ajustes, también está cerrado, sin reserva y reportado a los 14 días. El otro abierto de la selección es una lesión corporal de autos de 18.915,80 CU, con 3.961,29 pagados y 14.954,51 de reserva.

## Fechas y composición del objetivo

Los retrasos van de 1 a 349 días. Ninguno supera 365; 2 se reportaron durante 2024 por pérdidas de 2023. Son conceptos diferentes: año de reporte y demora superior a un año no se sustituyen. Cada siniestro seleccionado se asigna a un único intervalo original y coincide con el componente/fold guardado. Los veinte periodos concilian en centavos tanto T0 como reserva, incluyendo ceros. Esto no vuelve prospectivo el corte de valoración o la formación histórica de grupos.

El [diccionario oficial archivado](../../../Semana%202/Codex/fuentes_variables_ultimo/data_description_response.json) define pagado neto de franquicia e incurrido como pagado más estimación de caso. Se conserva `reserva = incurrido − pagado` y `T0 = incurrido − recuperaciones = pagado − recuperaciones + reserva`. Restar otra vez franquicia o sumar otra vez reserva duplicaría el ajuste. Los cálculos usan enteros de centavos y unidades de cuarto de centavo para el estrés 0,75/1,25, sin redondeo intermedio.

Aplicado solo a esta selección, el estrés mecánico cambia el total en ±22.260,93 CU, aproximadamente ±1.38%. No es una estimación de adecuación, intervalo estadístico, nuevo objetivo o resultado de modelos reentrenados. Su efecto observado es cero en el siniestro principal de autos. No se extrapola ese porcentaje al resto del portafolio, a C0 o a 2025.

## Verificación y límites

Pasaron 60 controles del productor, 558 comprobaciones por otro método y 16 conciliaciones de lectura, con solapamiento. El revisor propio usa Decimal, diccionarios y datetime para reconstruir selección, importes, intervalos y balances; no reutiliza las funciones del productor para esas cuentas. Adversos de año, duplicado, identidad y orden de fechas fallan como corresponde. Una invocación real del productor con reserva sintética alterada en un centavo falla antes de la conciliación, sin ajustes o scores.

Se conservan dos fallos del comprobador: la primera construcción de una fecha sintética mezcló date y Timestamp; la segunda no resolvió el argumento relativo de la corrida antes de crear la ruta del fixture. Se corrigió solo el comprobador y se completó su tercera invocación. Las fuentes, el productor congelado y el plan no cambiaron. Esos intentos no son pases de verificación ni errores hallados en los siniestros. No se repitieron las suites GLM, remuestreo o entrenamiento anteriores.

El original y su copia son una sola fuente administrativa, no evidencia externa de transacciones ni revisión profesional independiente. Faltan movimientos históricos, fundamento actuarial de las estimaciones de caso, reaperturas y coste último. Se mantiene abierta la suficiencia de reservas y la cola no observada. No se elimina un coste válido porque concentre error; las conclusiones de B19 siguen siendo exploratorias tras búsqueda adaptativa. La exposición previa de un asunto externo se conserva declarada, sin usar sus cifras ni afirmar ceguera completa.

## Decisión y continuación

No se cambia T0/C0, una cobertura, un grupo o un modelo. Se documenta como conciliada la trazabilidad de esta selección, sin cerrar automáticamente las advertencias generales. Antes de otra tanda procede revisar la contracción y el nivel del GLM estándar regularizado B20 ya guardado frente a B19, sobre estos grupos fijados y solo 2023, con plan de diagnóstico previo y sin reajustar. La concordancia de origen no justifica más complejidad por sí sola.

Kaggle MCP releyó la [discusión 752144](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/discussion/752144): contenido semántico sin cambios, mismo mensaje y tres respuestas, sin nuevo anuncio de corrección del HOST. Se conservó un recibo de consulta; no se duplicó la fuente, repitió el cotejo de test o intentó un envío.

El [plan](../../registro/semana2_b19_traza2023_plan_v1.json), el índice `registro/semana2_b19_traza_actual.json` y la corrida privada contienen fuentes con SHA, razones de selección, conciliación por fila y comprobaciones. Las prácticas de Documentación IAA §2 y Gobernanza §§2.8–2.10 se aplican a linaje, límites y evidencia propia; no certifican aprobación humana. Foro 038/039. Sin remoto, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. La ventana nocturna termina a las 07:00 Bogotá.
