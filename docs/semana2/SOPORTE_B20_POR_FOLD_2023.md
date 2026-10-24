# Soporte de B20 por fold: concentración y evidencia pendiente

El contraste mínimo de edificios sigue sin soporte admisible. Fallan cinco de las diez celdas de cola retenida, repartidas entre cuatro folds. Todas alcanzan el mínimo de componentes positivos; los incumplimientos vienen de la concentración del coste. Solo el fold 0 pasa ambas colas. No se retira ningún siniestro, componente, fold o banda.

Codex, corte UTC 2026-10-24T03:21:59.314936+00:00. Auditoría de artefactos guardados de 2023 con las reglas del [diseño previo](DISENO_CONTRASTE_MINIMO_B20_2023.md). Se inventarían las 75 celdas ramo/fold/banda y las 15 agrupadas de B20. La puerta de elegibilidad se aplica únicamente a las diez celdas de edificios bandas 1/5 y sus dos colas agrupadas; no se extiende a otros ramos o bandas. No se entrenan, cargan o consultan modelos, producen tasas, cambian cortes o calculan nuevos D²/intervalos.

## Resultado con los umbrales intactos

Por fold y cola se exigen simultáneamente al menos diez componentes con coste positivo, máximo 50% del coste en un componente y equivalente de concentración de al menos tres. En las colas agrupadas son cincuenta positivos, máximo 20% y equivalente de diez. Son límites prudenciales fijados por el diseño después de los diagnósticos; no son requisitos de Kaggle/IAA ni una garantía de precisión.

| Fold | Banda | Componentes positivos | Mayor participación en coste | Equivalente de concentración | Resultado |
| --- | --- | ---: | ---: | ---: | --- |
| 0 | 1 | 11 | 20,93% | 6,36 | Cumple la celda |
| 0 | 5 | 21 | 23,63% | 6,37 | Cumple la celda |
| 1 | 1 | 12 | 62,62% | 2,30 | Falla concentración y equivalente |
| 1 | 5 | 28 | 23,68% | 8,52 | Cumple la celda |
| 2 | 1 | 15 | 55,38% | 2,91 | Falla concentración y equivalente |
| 2 | 5 | 27 | 41,58% | 3,94 | Cumple la celda |
| 3 | 1 | 17 | 91,82% | 1,18 | Falla concentración y equivalente |
| 3 | 5 | 22 | 44,44% | 4,27 | Cumple la celda |
| 4 | 1 | 14 | 71,39% | 1,87 | Falla concentración y equivalente |
| 4 | 5 | 26 | 66,75% | 2,17 | Falla concentración y equivalente |

Los cinco incumplimientos son edificios banda 1 en folds 1, 2, 3 y 4, y banda 5 en fold 4. Ninguna de esas diez celdas falla por el mínimo de positivos: hay de 11 a 28. Contar positivos y medir concentración responde a preguntas diferentes. Tener diecisiete componentes positivos no compensa que uno reúna el 91,82% del coste, como ocurre en fold 3/banda 1.

El fold 2/banda 1 tiene equivalente 2,911 y participación 55,38%; también falla. La clasificación usa valores completos, sin redondear a tres equivalentes o a 50%. No se promedian criterios entre bandas ni se da por bueno un fold porque su otra cola pase. Se exigían cinco vistas admisibles: conservar solo el fold 0 o saltarse la cola problemática cambiaría el diseño.

| Cola de edificios agrupada | Positivos | Mayor participación | Equivalente | Resultado con 50 / 20% / 10 |
| --- | ---: | ---: | ---: | --- |
| Banda 1 | 69 | 31,65% | 6,09 | Falla concentración y equivalente |
| Banda 5 | 124 | 19,02% | 14,16 | Cumple la celda |

La banda 5 agrupada cumple, pero fold 4/banda 5 falla. La banda 1 agrupada también falla. La agregación oculta fragilidad y el paso de una celda no acredita el conjunto.

En cada celda se suma T0 por componente completo presente en ella: Cg. La participación máxima es max(Cg)/ΣCg; el equivalente es (ΣCg)²/ΣCg². Es una descripción de concentración de coste, no un número de observaciones independientes para un intervalo. Un componente puede tener varias filas o bandas; los recuentos no se suman entre bandas como muestras nuevas. Los folds comparten ajuste, aunque los componentes retenidos sean disjuntos.

## Qué aporta el ajuste exterior guardado

También se leyeron las tasas de ajuste ya guardadas para edificios. Son 50.320 apariciones de 12.580 periodos originales, cuatro usos por periodo entre modelos. Cada modelo deja fuera un fold y ve los otros cuatro. Estos valores son de ajuste, no tasas internas fuera de muestra del contraste propuesto.

| Fold exterior excluido | Positivos del ámbito de ajuste | Positivos banda 1 / banda 5 | log(P80/P20) de tasa de ajuste |
| --- | ---: | ---: | ---: |
| 0 | 409 | 53 / 111 | 1,0775 |
| 1 | 401 | 45 / 100 | 1,1036 |
| 2 | 393 | 48 / 104 | 1,0677 |
| 3 | 400 | 50 / 96 | 0,8583 |
| 4 | 385 | 42 / 120 | 1,0817 |

En esos cinco ámbitos exteriores hay de 385 a 409 componentes positivos y un rango log(P80/P20) entre 0,8583 y 1,1036. Es mayor que log(1,25)=0,2231, pero el requisito del diseño se refiere al ámbito interno de calibración. No se traslada esa comprobación a tasas que todavía no existen. Las colas inferiores del ajuste exterior solo tienen de 42 a 53 positivos y conservan concentración; este contexto tampoco certifica soporte interno.

El futuro procedimiento tendría diez conjuntos únicos de tres folds para generar veinte predicciones internas ordenadas. El material actual tiene cinco modelos exteriores entrenados con cuatro folds. Las predicciones de ajuste guardadas vieron las etiquetas de sus propias filas; no pueden rebautizarse como OOF internas. Tampoco puede usarse sin más la OOF de otro fold si su modelo o C0 vio el fold exterior.

## Evidencia que ahora queda resuelta y la que falta

| Cuestión | Resultado de esta auditoría | Consecuencia |
| --- | --- | --- |
| Soporte retenido por fold de las dos colas | Inventario completo: cinco celdas fallan por dos criterios de concentración; mínimos de positivos cumplidos | Carencia medida, condición incumplida; no autoriza ajuste |
| Soporte de las colas agrupadas | Banda 1 falla; banda 5 pasa solo agrupada | La agregación no sustituye cada fold |
| Tasas y C0 internos sin ambos folds | No existen en estos artefactos; lo guardado excluye solo el fold exterior | No puede acreditarse sin un procedimiento distinto; no se produce aquí |
| Soporte de cada ámbito interno y su rango de log-tasa | Sigue desconocido; el ajuste exterior es solo contexto | No se marca como cumplido ni se extrapola de sus recuentos |
| Implementación estricta y coste de primera etapa | Adaptador 2023, grafo de ancestros y enumeración de flujos C0 aún pendientes | No invocar productores históricos que recorren otros años |
| Mecanismo residual y beneficio | Pendiente, intercepto y mejoras no estimados; los costes concentrados siguen siendo explicación rival | No promocionar, recalibrar o añadir complejidad |

Para superar la concentración haría falta evidencia legítima que cambie la información disponible y satisfaga las reglas conservadas. Volver a sumar estas mismas filas no crea componentes nuevos. Una corrección de origen solo sería admisible si hubiese evidencia de un error; esta auditoría no detecta ni declara inválidos los siniestros. No se recortan importes, eliminan costes grandes, combinan bandas después de ver resultados o relajan topes para obtener elegibilidad.

La documentación adicional del grafo o un lector más estricto puede resolver riesgos de implementación, pero no borra el incumplimiento numérico ya observado. Incluso un soporte completo del ajuste interno no anularía la pantalla retenida fallida. El mandato vigente mantiene el contraste sin ejecución.

## Verificación y decisiones

Pasaron 911 comprobaciones propias de esta auditoría, sin fallos. El productor clasifica celdas guardadas; el comprobador reconstruye cantidades de soporte con diccionarios y centavos a partir de las filas guardadas. Los umbrales se contrastan además con fracciones exactas. Se conservaron los 50.094 periodos OOF, los 30.869 componentes y todo su T0; las 75 celdas particionan las filas sin exclusión. Las celdas de coste nulo o vacías conservan concentración indefinida y no acreditan soporte.

También se cotejaron las tasas de ajuste y sus cortes ya guardados, las fronteras inclusivas de los umbrales y los casos indefinidos. No se repitieron las suites de entrenamiento o calibración, inferencias o bootstrap. Las cifras de controles acreditan esta conciliación, no independencia profesional, potencia estadística o mejora predictiva.

Se mantienen los umbrales, los siniestros y todos los candidatos. B00 conserva la referencia y B01–B20 permanecen como alternativas; contador propio 195 ajustes de precio y 285 constantes, sin cambios. Cero parámetros, ajustes, tasas nuevas, modelos cargados, remuestreos o recetas. La condición de soporte sigue fallida, sin promoción o complejidad añadida.

2024, test, actas, scores, SEL01 y ledger siguen cerrados en este trabajo. La exposición previa a un título de otro chat se mantiene declarada sin usar sus cifras o afirmar ceguera completa. Codex firma esta comprobación propia, que no constituye revisión humana o profesional independiente. Documentación IAA §§2–3 y Gobernanza §2.8 orientan procedencia y alcance; los umbrales pertenecen al diseño del proyecto.

[Plan](../../registro/semana2_b20_soporte_folds_plan_v1.json), [índice y recibos](../../registro/semana2_b20_soporte_folds_actual.json), [diseño condicionado](DISENO_CONTRASTE_MINIMO_B20_2023.md) y [bandas originales](CALIBRACION_B20_BANDAS_AJUSTE_2023.md). Los 75 registros por fold, 15 agrupados, cinco vistas de ajuste, decisiones, fuentes SHA y snapshots están en la corrida privada `b20_soporte_folds_20261024_v1`, fuera de Git.
