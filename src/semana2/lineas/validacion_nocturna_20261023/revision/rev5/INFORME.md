# Revisión 5: auditoría previa al envío de A1fixF1b3n_2025.csv

Archivo auditado: `/home/claude/noche/salidas/correccion/A1fixF1b3n_2025.csv` (SHA-256 `f786deb3…c53aa`, 209.064 líneas).
Todo el código y las salidas de esta revisión están en `/home/claude/noche/revision/rev5/` (scripts `t1_` a `t9_`, resultados en `resultados.json`). Trabajé con un solo hilo y solo con pandas, pyarrow, numpy y scipy. No leí el INFORME, la BITÁCORA, otras revisiones ni el código del autor, salvo el bloque `if '--f1' in sys.argv:` de `desarrollado_gbm.py`, y solo después de terminar mi reconstrucción.

## 1. Reconstrucción de los dos archivos

Seguí la receta descrita: para cada ramo, g = exp(media de lg_dev de las tres semillas), L = Σ t0 / Σ (eef_coste · g) en las filas de entrenamiento, predicción = exposure_model · g · L, y para F1 el reescalado por ramo al total de A1fixb3.

| Ramo | L sin historia | L con historia | Factor neutral | Total F1 sin neutralizar | Total final (= A1fixb3) |
|---|---|---|---|---|---|
| Autos | 426,73 | 437,47 | 0,97899 | 41.922.773 | 41.042.171 |
| Edificios | 404,80 | 411,28 | 0,99159 | 20.765.754 | 20.591.198 |
| Contenidos | 92,42 | 93,03 | 0,99744 | 5.549.262 | 5.535.071 |

Fuente: `t1_rebuild.json`.

Mi A1fixb3 es idéntico byte a byte al del autor. Mi A1fixF1b3n difiere en 38 bytes, todos en el último decimal: la diferencia máxima es 5,0e-7 CU (relativa 4,5e-6), y los totales por ramo coinciden hasta 0,0002 CU. Las tres semillas de cada familia están muy correlacionadas (correlación mínima 0,986). Los archivos de modelo confirman lo declarado: los modelos F1 tienen las mismas variables que los modelos sin historia más `f1_siniestros_previos` y `f1_anios_observados`, los mismos hiperparámetros (Tweedie 1,5, lr 0,02, 31 hojas) y las semillas 11, 12 y 13; solo cambia el número de iteraciones. `m02` es la semilla 11 de la misma especificación. No hay columnas exclusivas de un mercado (género, telemática, kilometraje, banda de crédito). No hay factor de tendencia: la receta sin tendencia reproduce el archivo exacto.

También verifiqué t0 contra los siniestros brutos: neto = incurrido − recobros de los siniestros no repudiados con fecha de ocurrencia dentro del periodo de la fila. Coincide exactamente en los tres ramos. No reconstruí eef_coste ni reentrené LightGBM; los tomé como dados.

## 2. Validez del envío

Todo cumple (`t2_validity.json`):

- Encabezado `row_id,prediction`, ASCII sin BOM, finales de línea LF (ningún CR), salto de línea final, sin comillas, espacios ni notación científica.
- 209.063 filas = 90.521 de autos + 52.295 de edificios + 66.247 de contenidos. Ningún row_id falta ni sobra, no hay duplicados y el orden es el de `sample_submission.parquet` (autos, edificios, contenidos, en el orden de los archivos de prueba). Los row_id se conservan como texto (`[MBC]` + 8 dígitos) y ninguno coincide con un id del mercado desarrollado.
- Predicciones finitas y todas mayores que cero (mínimo 0,1035, máximo 4.105,10, media 321,28), con 6 decimales en todas las filas.
- Son totales por fila y no tasas: la pendiente de log(predicción) sobre log(exposición) es 1,04, y las filas cortas tienen predicciones proporcionalmente pequeñas (autos con exposición ≤ 0,1: media de 22 CU frente a 407 CU en el año completo). La exposición de prueba es igual a (días inclusivos)/365 redondeada a 4 decimales, y coincide con exposure_model de la base.

Nota menor: la descripción dice que el ejemplo de envío es CSV, pero aquí viene en parquet; el archivo auditado es CSV, como pide Kaggle.

## 3. Historia de la póliza: fuga y tiempos

Calculé por mi cuenta, desde `datos/s2/claims.parquet` y las tablas de pólizas y de prueba, los dos rasgos para las 318.359 filas emergentes (`t3_history.py`, `t3_features.parquet`):

- siniestros no repudiados de la misma póliza reportados estrictamente antes de period_start;
- años desde el primer period_start observado de la póliza, en días/365,25.

En la tabla de siniestros emergentes no hay claim_id duplicados ni duplicados de contenido; ningún reporte es anterior a la ocurrencia, y el reporte más tardío es del 2024-12-30. Por tanto, para las filas de 2025 solo entra información reportada antes del 2025-01-01. El siniestro de la propia fila nunca puede entrar en su rasgo: el reporte es posterior o igual a la ocurrencia, la ocurrencia es posterior o igual al inicio, y la comparación es estricta. Lo comprobé además: ningún siniestro propio está reportado antes del inicio de su fila.

En 2025, 6.767 filas tienen historia, todas renovaciones. El máximo es 7 siniestros en autos, 4 en edificios y 3 en contenidos, dentro del rango visto en el entrenamiento desarrollado (16, 5 y 4). Ninguna fila de nuevo negocio tiene historia emergente.

Antes de leer el código, busqué huellas de fuga en la diferencia de log-relatividades entre F1 y el modelo sin historia (`t3_probe.json`):

| Sonda | Qué esperaría si hubiera error | Resultado |
|---|---|---|
| Siniestros del propio periodo (filas de entrenamiento sin historia previa) | alza en filas con siniestro propio | sin alza; coeficiente ≤ 0 en los tres ramos |
| Siniestros futuros de la póliza (filas 2023 sin historia ni siniestro propio) | alza con siniestros posteriores | sin alza |
| Solo siniestros repudiados previos (134 filas) | alza | +0,001 frente a filas comparables |
| Reporte el mismo día del inicio (19 filas) | alza si la comparación fuera ≤ | −0,04; consistente con < estricto |
| Mercado equivocado: nuevo negocio 2025 con siniestros desarrollados bajo el mismo id (52 filas) | alza | +0,003 frente a −0,004; sin efecto |
| Historia previa real | alza monótona | +0,15 / +0,31 / +0,51 en autos con 1, 2 y 3+ previos |

El comportamiento pedido se cumple. Entre las renovaciones de 2025, la razón A1fixF1b3n / A1fixb3 es más alta con siniestros previos que sin ellos: 1,267 frente a 0,954 en autos, 1,235 frente a 0,989 en edificios y 1,154 frente a 1,004 en contenidos. En autos crece con el número de previos (1,20; 1,41; 1,73).

Después leí solo el bloque `--f1`. Usa `salidas/{mk}/asignacion.parquet` del mismo mercado (s1 para el desarrollado, s2 para el emergente), filtra por ramo y `accepted`, compara `rd < ps` de forma estricta y toma el primer inicio de la póliza en la base. Comprobé que en s2 `accepted` es exactamente "no repudiado", que la tabla de asignación tiene los 9.258 siniestros brutos sin duplicados y con las mismas fechas, y que en s1 la asignación quita 604 duplicados de contenido del bruto desarrollado. Al replicar la función sobre las bases emergentes obtengo 0 diferencias con mis conteos y mis años. La implementación coincide con la definición.

Hay tres matices, ninguno bloqueante:

- 2.961 renovaciones de 2025 (470 de ellas con historia) empiezan después del 1 de enero. Para ellas, la definición de entrenamiento incluiría los siniestros reportados entre el 1 de enero y su inicio, que no existen en los datos. El rasgo cuenta de menos, pero es inevitable.
- El estado "repudiado" es el del 31-12-2024 también para las filas de entrenamiento: es una mirada al futuro menor, que no tiene efecto medible según la sonda de repudiados.
- Los años observados de 9.259 filas de pólizas nuevas en 2025 usan el inicio de una fila anterior de 2025 de la misma póliza. Es información de las variables de prueba, no de resultados, y se trata igual que en el entrenamiento.

## 4. Decisión de política

El SHA-256 del acta original coincide (`b3faaece…b080`). Apliqué la regla enmendada a las cifras del acta, con promoción secuencial:

Paso 1, A1 contra R0. La primaria pasa: diferencia 0,048591, límite inferior 0,026514, por encima de delta_min = 0,0005. Las salvaguardas también pasan:

- cliente nuevo (versión 2): diferencia puntual 0,013062 ≥ 0; el límite 95 % de −0,010535 queda solo como diagnóstico;
- escenarios: diferencias de 0,0477 a 0,0495;
- segmentos: el mínimo es 0,0131, por encima de −0,001;
- influencia: se retiran 37 = max(5, ⌈0,001 · 36.408⌉) grupos y la diferencia sigue en 0,0194;
- condición de nivel: cumplida.

A1 promueve.

Paso 2, A2 contra A1, que ahora es el titular. La primaria no pasa: diferencia −0,003976, límite inferior −0,010405. A2 no promueve.

El titular final es A1, igual que en `puerta_2024_acta_enmendada.json`, cuyas cifras copian bien las del acta original.

Hay dos observaciones de gobernanza. La primera: la enmienda se decidió después de conocer el acta, y lo que se envía (A1 con historia neutral y tres semillas, entrenado en 2021-2024) no es el A1 que pasó la puerta; la política v2 lo reconoce y califica esa evidencia como exploratoria. La segunda: con la regla nueva, la salvaguarda de cliente nuevo queda casi redundante con la de segmentos, porque ambas usan la misma diferencia puntual. Y la incertidumbre en ese segmento es grande (límite −0,0105) justo cuando el nuevo negocio es el 77 % de la exposición 2025.

## 5. Sensatez

Totales por ramo (`t5_sanity.json`). A1fixF1b3n coincide con A1fixb3 en los tres ramos. Frente a R0 es +13,8 % en autos (41,04 M frente a 36,05 M), +3,8 % en edificios y +4,2 % en contenidos; en total, 67,17 M frente a 61,20 M (+9,7 %). El alza de autos viene de la mezcla: la relatividad media ponderada por exposición pasa de 1,068 en 2023-2024 a 1,217 en 2025, porque el nuevo negocio (77 % de la exposición) tiene g ≈ 1,29.

| Tasa anual 2025 (Σ pred / Σ exp) | Nuevo | Renovación | Ramo | R0 | Observada 2023-24 |
|---|---|---|---|---|---|
| Autos | 553,4 | 406,7 | 519,5 | 456,3 | 456,3 |
| Edificios | 434,0 | 436,9 | 434,6 | 418,8 | 418,8 |
| Contenidos | 94,0 | 93,0 | 93,8 | 90,0 | 90,0 |

Calibración en 2023-2024 con la receta auditada (`t5b_extra.json`):

- En autos la pendiente de A/E por deciles de g es plana (−0,01); los deciles extremos quedan algo sobre-dispersos (A/E 0,77 y 0,85).
- Las filas de nuevo negocio de 2023-2024 tienen A/E 1,26 en autos, 1,27 en contenidos y 0,83 en edificios. Si ese patrón siguiera en 2025, autos y contenidos quedarían cortos en nuevo negocio. Es una decisión de modelo ya documentada en la preinscripción (factor NB excluido), no un error técnico.
- La historia está bien respaldada en autos: en 2024, las filas con previos tienen A/E relativo 1,05 [0,90; 1,21] con F1, frente a 1,21 sin historia. En edificios y contenidos el alza del modelo (×1,25 y ×1,15) no se ve en los datos: A/E relativo 0,70 [0,34; 1,11] y 0,90 [0,45; 1,42], con solo 30 y 21 filas con siniestro. Es inconcluso, y su efecto se limita a unas 900 renovaciones por ramo, porque el paso neutral fija el total.

Extremos. Las 10 filas más altas son todas de edificios, con predicciones de 3.561 a 4.105 CU y exposición entre 0,98 y 1. La más alta equivale a 9,4 veces la tasa media del ramo. Las explican sumas aseguradas altas (329.000 a 656.000, frente a una mediana de 241.000), vivienda alquilada (4 de 10, frente al 10 % del ramo), construcción MIX o madera (3 de 10), tramo 65+ (5 de 10) y, en 4 casos, un siniestro previo. Ese siniestro sube la fila entre 17 % y 22 % frente a A1fixb3. El decil superior de g en edificios tiene A/E 1,11 en 2023-2024, así que estas relatividades altas no parecen exageradas. La predicción nunca pasa del 2,4 % de la suma asegurada en edificios ni del 3,9 % en contenidos. La razón F1 / sin historia va de 0,46 a 6,2; los extremos son filas de autos de 0,01 a 0,05 años en las que las dos familias de modelos discrepan (las semillas dentro de cada familia coinciden). Su impacto monetario es despreciable, y las filas con exposición ≤ 0,25 son el 0,85 % de la exposición de autos.

No encontré nada implausible que justifique bloquear el envío.

## Veredicto

El archivo está técnicamente listo para enviar. La reconstrucción independiente lo reproduce (diferencia máxima 5e-7 CU), el formato y las filas son correctos, el rasgo de historia no tiene fuga ni errores de tiempo, y la regla enmendada da A1 como titular, igual que el acta enmendada.

Bloqueantes: ninguno.

No bloqueantes:

1. Gobernanza: la enmienda v2 es posterior al acta, y la receta enviada (historia neutral y tres semillas) no pasó por la puerta; su evidencia es exploratoria.
2. Cliente nuevo: el límite 95 % de A1−R0 es −0,0105 con un 77 % de nuevo negocio en 2025; la mejora en ese segmento no está demostrada.
3. En 2023-2024, el nuevo negocio corrió por encima del modelo en autos y contenidos (A/E 1,26 y 1,27); es un riesgo de nivel por segmento.
4. La historia en edificios y contenidos no está respaldada por la experiencia emergente (inconcluso por volumen).
5. Las 2.961 renovaciones que empiezan después del 1 de enero de 2025 tienen el rasgo de historia incompleto por diseño de los datos.
6. El estado "repudiado" corresponde a la valoración del 31-12-2024 también en el entrenamiento.
7. eef_coste y el entrenamiento de LightGBM no se reconstruyeron; se aceptaron como insumos.
8. Hay razones extremas F1 / sin historia en filas de autos muy cortas, sin impacto material.
