# Preflight de C0 y aislamiento del contraste mínimo de B20

El soporte continúa fallido y el contraste no es ejecutable. Los cinco C0 exteriores guardados concuerdan con la exclusión de su fold, y sus exposiciones efectivas de 2023 coinciden con las entradas de B20. Ese resultado no habilita su reutilización como C0 interno: los veinte casos ordenados del diseño incorporarían etiquetas que deben quedar protegidas si se usan los objetos actuales.

Codex, UTC 2026-10-24T03:32:38.109841+00:00. Auditoría de código, registros de pertenencia, parámetros y pesos C0 ya guardados, y cachés exclusivamente de 2023. Se congelaron 66 fuentes con SHA y snapshots. No se abren las tablas de observación que mezclan años, los resúmenes con filas de 2024, datos originales, bundles de modelos o resultados de confirmación. Los manifiestos superiores se leen solo como metadatos de rutas y hashes. Cero ajustes, parámetros, valores C0 o precios nuevos.

## Qué aprende C0 y qué debe aislarse

El código histórico de C0 coincide por SHA con su snapshot original. Para cada peril, `fit_reporting` usa los retrasos y edades de truncamiento de las notificaciones de ajuste para producir la distribución de conteos y pesos por notificación. Los mismos pesos y las marcas de coste producen la curva de coste y la marca media. Después se estima la frecuencia con el conteo y la exposición de ajuste corregida por completitud de conteos. El producto de frecuencia y marca media determina los pesos de la mezcla.

| Dependencia | Información que determina el objeto | Regla del contraste interno |
| --- | --- | --- |
| Curva de notificación | Retrasos, edades de truncamiento y conteos del ajuste | Excluir los folds exterior e interior |
| Pesos por notificación | Masas de la curva de conteos y tamaño de cada intervalo | Mismo ámbito que la curva |
| Curva de coste y marca media | Marcas T0 y pesos de las notificaciones de ajuste | Mismo ámbito, sin marcas protegidas |
| Frecuencia por peril | Conteo y denominador de exposición × completitud de conteos | Denominador construido solo con periodos de ajuste |
| Mezcla de coste por peril | Frecuencia × marca media, normalizadas entre perils | No reutilizar mezcla exterior o global |
| Completitud y exposición C0 por periodo | Curvas y mezcla congeladas del ámbito, fechas y exposición del periodo | Aplicar objetos ya fijados; las fechas de la fila no aportan sus etiquetas |

C0 es exposición nominal multiplicada por la completitud de coste mezclada. Aislar únicamente el GLM o las curvas de reporte deja sin proteger otras dependencias aprendidas. Medianas, escalas y OHE del B20 interno también deben usar el mismo conjunto de tres folds.

El corte histórico de valoración sigue siendo 31 de diciembre de 2024. Ese parámetro del objetivo observado no equivale a abrir pólizas, targets o validación de 2024. Se conservan las convenciones de T0 y C0, y las limitaciones retrospectivas y de coste último. En esta auditoría no se leyeron T0 o reservas de Parquet.

## Aislamiento observado de los cinco ámbitos exteriores

Se cotejaron los registros de entrenamiento de C0 y sus pesos con las identidades de los 50.094 periodos de 2023 y 30.869 componentes. Los 12.580 periodos de edificios tienen las mismas claves en cada vínculo de 2023 y en la caché usada por B20; exposición nominal y C0 base coinciden exactamente. Los recuentos y sumas de pesos también concuerdan con los recibos del GLM.

| Fold excluido | Periodos de ajuste de edificios | Periodos retenidos | Notificaciones de ajuste de edificios | Cruces de grupo / cliente / dirección |
| --- | ---: | ---: | ---: | --- |
| 0 | 10070 | 2510 | 424 | 0 / 0 / 0 |
| 1 | 10070 | 2510 | 416 | 0 / 0 / 0 |
| 2 | 10061 | 2519 | 414 | 0 / 0 / 0 |
| 3 | 9993 | 2587 | 417 | 0 / 0 / 0 |
| 4 | 10126 | 2454 | 405 | 0 / 0 / 0 |

Cada registro de notificación guardado pertenece a un periodo de 2023 y a los cuatro ámbitos que no excluyen su fold. La unión de edificios contiene 519 notificaciones distintas; no son 519 periodos positivos. Los pesos guardados se corresponden con esos registros y suman el número de notificaciones por peril. Las dimensiones y masas de las curvas concuerdan con los conteos. Se comprueba la coherencia de los artefactos guardados, sin reestimar curvas o contrastarlas contra transacciones originales.

El código histórico selecciona parte de sus ámbitos con `row_id`. En este inventario los 50.094 valores son globalmente únicos, por lo que no se detecta una colisión en los datos actuales. El nuevo contrato de pertenencia usa siempre `(market, line, row_id)`; una prueba sintética demuestra que una colisión entre ramos puede pasar un filtro por row_id y quedar rechazada por la clave compuesta. No se presenta ese caso sintético como un error real ya observado.

## Por qué los objetos actuales no sirven como primera etapa interna

Para predecir internamente el fold j mientras el fold k queda reservado para evaluación exterior, todos los objetos aprendidos deben usar solo los otros tres folds. Se enumeraron diez conjuntos únicos de ajuste y veinte casos ordenados k/j, con hashes de pertenencia de periodos y componentes. Son propuestas de pertenencia; no se crea ningún estimador o C0 para esos ámbitos.

Usar el C0 exterior k para las filas internas j incluiría las notificaciones de j en su propio ajuste de C0. Usar el C0 OOF ya guardado para j excluiría j, pero incluiría las notificaciones de k. Las veinte combinaciones contienen datos protegidos en ambas alternativas. Ninguna de las dos reutilizaciones pasa el contrato interno.

Esto no invalida el uso exterior documentado de los cinco C0 guardados. La incompatibilidad surge al intentar asignarles el papel interno del contraste nuevo. Una caché cuyo nombre o hash es correcto tampoco acredita por sí sola el ámbito requerido: el manifiesto debe incluir el conjunto exacto de entrenamiento y todos sus ancestros.

## Coste propuesto que ya puede enumerarse

Los seis perils de edificios están presentes en las cinco vistas exteriores. A partir de la unión de metadatos se contaron las notificaciones disponibles en cada uno de los diez tríos, sin usar sus marcas, ajustar curvas o eliminar registros:

| Peril | Mínimo de notificaciones entre los diez tríos | Llamadas de reporte previstas, una por trío |
| --- | ---: | ---: |
| Daño accidental | 29 | 10 |
| Escape de agua | 68 | 10 |
| Incendio | 27 | 10 |
| Inundación | 21 | 10 |
| Tormenta | 122 | 10 |
| Subsidencia | 14 | 10 |

Todos superan el mínimo de cinco notificaciones exigido por la rutina histórica. Ese mínimo técnico se refiere a notificaciones y no sustituye las reglas de componentes positivos, concentración o rango de tasas del contraste. Tampoco demuestra que los retrasos y marcas internos sean estables o que las curvas nuevas converjan a una verdad última.

El presupuesto hipotético queda desglosado: diez GLM internos de edificios; cinco pendientes de calibración y cinco constantes de nivel; diez flujos C0 con sesenta llamadas de reporte por peril, sesenta constantes de frecuencia derivadas y diez mezclas normalizadas de seis entradas. Las sesenta marcas medias son salidas de esas mismas llamadas de reporte, no sesenta modelos Gamma adicionales. Se reutilizarían cinco modelos exteriores. Estos son recuentos de trabajo previsto, no estimaciones hechas ni cambios del contador.

La base reserva ρ=1 se mantiene fija. La pendiente propuesta se denomina β de calibración, todavía sin estimar y acotada en [0,1]. El `b` histórico de `fit_reporting` designa el factor de reservas, no esa pendiente: pasar β a ese argumento cambiaría el objetivo y C0. La separación queda declarada en el contrato; su aplicación en un adaptador numérico sigue pendiente. No se añaden escenarios .75/1.25 o colas a este ensayo mínimo.

## Qué se implementó y qué falta

Se incorporó un selector puro de pertenencias que exige 2023, test falso, claves compuestas únicas, folds válidos y ausencia de cruces por componente, cliente y dirección. Solo recibe metadatos. Las catorce pruebas incluyen ámbitos válidos, año/test indebido sintéticos, duplicados, cruces, exclusiones inválidas, colisión de row_id y etiquetas sintéticas alteradas que no cambian la pertenencia.

Esas pruebas validan el selector, no la invariancia de un C0 ajustado al envenenar etiquetas protegidas. No existe aquí un núcleo numérico C0 nuevo ni se lo invoca. El ejecutor histórico `run()` lee tablas de todos los años y test antes de recorrer los ámbitos; no es un punto de entrada admisible para esta actuación. Se conserva sin cambios como evidencia y no se ejecuta.

| Carencia | Estado después del preflight | Evidencia aún necesaria |
| --- | --- | --- |
| Dependencias y pertenencia exterior | Inventariadas y conciliadas en los artefactos guardados | No constituye revisión independiente o de transacciones |
| Contrato interno de pertenencia | Diez tríos y veinte casos enumerados; selector de metadatos comprobado | Conectarlo a un adaptador numérico de ámbito estricto, sin lectura previa de otros años |
| C0 numérico interno | No implementado ni estimado aquí | Rutinas puras con fechas/marcas/denominadores y mezcla del mismo ámbito; clave de caché que incorpore fuentes, grupos, receta, valoración y parámetros |
| Invariancia de todo el aprendizaje | Solo se comprobó el selector | Alterar etiquetas de ambos folds protegidos y cotejar curvas, marcas, frecuencias, mezcla, transformaciones, GLM y calibrador del flujo real |
| Artefactos internos y su soporte | Ausentes de esta actuación | Tasas y C0 internos válidos, manifiestos completos y comprobación de las reglas originales; no generarlos bajo el mandato actual |
| Soporte retenido | Sigue fallido: cinco de diez celdas en cuatro folds | Evidencia legítima suficiente; los controles de implementación no eliminan la concentración medida |

El recuento de llamadas de primera etapa queda resuelto para el caso base de edificios. Sigue pendiente un presupuesto de ejecución verificable del adaptador real, su entorno y pruebas del flujo completo. Un cambio de código futuro necesita sus propios recibos: los de este preflight no certifican una implementación posterior.

La condición de soporte no se rebaja a advertencia informativa. No se relajan umbrales, combinan bandas para pasar, eliminan siniestros, fijan un nuevo roster o promueven alternativas. B00 conserva referencia y B01–B20 se preservan. No se calcula nueva calibración, mejora o precio.

## Recibos y alcance

Pasaron 384 comprobaciones propias, incluidas catorce pruebas del contrato de metadatos, sin fallos. Se mantienen 195 ajustes de precio y 285 constantes en el contador propio. Cero ajustes, inferencias, valores C0, parámetros o remuestreos nuevos; no hay entrenamiento remoto, envíos, mensajes externos o delegación.

2024, test, actas, scores, SEL01 y ledger permanecen cerrados en este trabajo. La exposición previa a un título ajeno se mantiene declarada sin usar sus métricas o afirmar ceguera completa. La comprobación de Codex no equivale a revisión profesional independiente. Documentación IAA §§2–3 y Gobernanza §2.8 orientan procedencia y alcance; la condición de soporte sigue regida por el diseño del proyecto.

[Plan previo](../../registro/semana2_b20_preflight_c0_plan_v1.json), [índice y recibos](../../registro/semana2_b20_preflight_c0_actual.json), [auditoría de soporte](SOPORTE_B20_POR_FOLD_2023.md), [diseño mínimo](DISENO_CONTRASTE_MINIMO_B20_2023.md), [selector de metadatos](../../src/semana2/ambitos_c0_b20_2023.py) y [código histórico C0](../../src/semana2/variables_ultimo.py). El detalle de ámbitos, reutilizaciones incompatibles, dependencias y fuentes SHA queda en `privado/semana2/desarrollo2023/b20_preflight_c0_20261024_v1`, fuera de Git.
