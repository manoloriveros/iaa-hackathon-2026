# Revisión independiente de la compuerta SEL01 sobre 2024 (rev2)

Revisión hecha el 23 de octubre de 2026 con código propio, sin leer `codigo/`, `salidas/` (salvo la descripción de datos) ni `revision/rev1/`. Un hilo de CPU. Todo se recalcula desde los trece Parquet originales del mercado emergente y desde las predicciones congeladas. Las cifras están en `resultados.json`; el código, en `codigo/` (`objetivo.py`, `compuerta.py`, `ensamblar.py`).

## Resultado

El titular final es R0. A1 y A2 superan con holgura el umbral global (límite inferior simultáneo 0,0272 y 0,0242 frente a 0,0005), pero los dos fallan la salvaguarda de cliente nuevo: su diferencia puntual en ese subconjunto es positiva (+0,0131 y +0,0111) y su límite unilateral del 95 % queda en −0,0104 y −0,0140, por debajo de −0,001. Las demás salvaguardas pasan. Como la política bloquea la promoción con cualquier salvaguarda fallida, R0 sigue como titular y A1 y A2 quedan como alternativas conservadas.

## Entradas y controles

Las predicciones tienen el SHA-256 esperado (`e4f55f69…3eb7`). Los trece Parquet coinciden con el manifiesto de descarga. El archivo de predicciones cubre exactamente las 59.202 filas de entrenamiento de 2024 (25.603 autos, 14.867 edificios, 18.732 contenidos), sin duplicados; `line`, `customer_id`, `address_id` y `new_business` coinciden con los originales, y R0, A1 y A2 son finitas y estrictamente positivas.

El objetivo T0 se construyó así: siniestros con `status != 'repudiated'`, asignados por `policy_id`, `line` y `period_start <= loss_date <= period_end`, sumando `incurred_to_date − recoveries`. Ningún siniestro cae en dos filas; 36 no caen en ninguna (6 de 2021, 28 de 2022 y 2 de 2023; 92.267,26 CU netos aceptados). Ningún neto aceptado es negativo ni cero, tampoco con la reserva ×0,75 o ×1,25, y ningún siniestro abierto tiene recuperaciones. Ninguna fila cruza de año.

| 2024 | Filas | T0 (CU) | Pagado | Incurrido | Recuperaciones | T0 lesiones | T0 hundimiento | Aceptados | Abiertos |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Autos | 25.603 | 7.693.126,75 | 5.733.188,71 | 8.097.176,53 | 404.049,78 | 2.014.762,31 | 0 | 3.491 | 709 |
| Edificios | 14.867 | 3.710.061,21 | 2.699.873,13 | 3.710.061,21 | 0 | 0 | 215.362,37 | 537 | 136 |
| Contenidos | 18.732 | 1.297.699,77 | 1.103.992,88 | 1.297.699,77 | 0 | 0 | 0 | 507 | 59 |

Cliente nuevo (cliente sin ninguna fila emergente de 2023 en cualquier ramo): 9.063 filas de 2024, que coinciden fila a fila con `new_business = True`.

## Métrica puntual

D² Tweedie con potencia 1,5 y nulo igual a la media de y de las filas evaluadas. Coincide con `sklearn.metrics.d2_tweedie_score`.

| D² | R0 | A1 | A2 |
| --- | ---: | ---: | ---: |
| Global | 0,07285 | 0,12144 | 0,11746 |
| Autos | 0,04991 | 0,08033 | 0,08045 |
| Edificios | −0,02129 | 0,06494 | 0,05202 |
| Contenidos | 0,04522 | 0,09204 | 0,09082 |
| Cliente nuevo | 0,10927 | 0,12233 | 0,12039 |
| Renovación | 0,06259 | 0,11653 | 0,11224 |

| A/E (Σy / Σpredicción) | R0 | A1 | A2 |
| --- | ---: | ---: | ---: |
| Autos | 1,0520 | 1,1051 | 1,1050 |
| Edificios | 0,6251 | 0,6148 | 0,6156 |
| Contenidos | 0,9727 | 0,9574 | 0,9582 |
| Global | 0,8709 | 0,8850 | 0,8855 |

## Incertidumbre pareada

Bootstrap ordinario de componentes conexas del grafo cliente–dirección de las filas de 2024: 36.408 componentes (19.815 de una sola fila, la mayor con 7 filas), 10.000 réplicas con semilla 2026102301 y las mismas extracciones para los tres modelos. El nulo se recalcula en cada réplica. Los cuantiles son 0,05/12 y 1 − 0,05/12.

| Par | Diferencia | Cuantil 0,05/12 | Cuantil 1 − 0,05/12 | DE bootstrap | Supera 0,0005 |
| --- | ---: | ---: | ---: | ---: | --- |
| A1 − R0 | +0,04859 | +0,02720 | +0,07350 | 0,00871 | sí |
| A2 − R0 | +0,04462 | +0,02415 | +0,06679 | 0,00808 | sí |
| A2 − A1 | −0,00398 | −0,01061 | +0,00246 | 0,00244 | no |

Con otras tres semillas los límites inferiores de A1 − R0 van de 0,02636 a 0,02717 y los de A2 − R0, de 0,02319 a 0,02440. Mis números aleatorios no coinciden con los de otra implementación.

## Salvaguardas

| Salvaguarda | A1 − R0 | A2 − R0 | A2 − A1 (referencia) |
| --- | ---: | ---: | ---: |
| Cliente nuevo, diferencia (≥ 0) | +0,01306 | +0,01112 | −0,00194 |
| Cliente nuevo, límite 95 % unilateral (≥ −0,001) | **−0,01035** | **−0,01405** | −0,00964 |
| Reserva ×0,75 (≥ 0) | +0,04769 | +0,04403 | −0,00366 |
| Reserva ×1,25 | +0,04947 | +0,04520 | −0,00427 |
| Masa tardía +5 % lesiones y hundimiento | +0,04831 | +0,04434 | −0,00397 |
| Masa tardía +10 % | +0,04804 | +0,04408 | −0,00396 |
| Segmento autos (≥ −0,001) | +0,03042 | +0,03054 | +0,00012 |
| Segmento edificios | +0,08623 | +0,07331 | −0,01292 |
| Segmento contenidos | +0,04681 | +0,04560 | −0,00121 |
| Segmento cliente nuevo | +0,01306 | +0,01112 | −0,00194 |
| Segmento renovación | +0,05395 | +0,04966 | −0,00429 |
| Influencia: sin las 37 componentes más favorables (≥ 0) | +0,01936 | +0,01689 | −0,00956 |
| Resultado | falla cliente nuevo | falla cliente nuevo | falla casi todo |

El bootstrap de cliente nuevo usa las componentes del grafo completo restringidas al subconjunto (5.602 componentes, 10.000 réplicas, semilla 2026102302). Reconstruir el grafo solo con esas filas da las mismas 5.602 componentes y un límite de −0,01015 y −0,01390. Con tres semillas más, el límite de A1 − R0 va de −0,00958 a −0,01062. La influencia retira max(5, ⌈0,001 · 36.408⌉) = 37 componentes (80 filas en A1 − R0); esas 37 concentran 168.775 de las 268.607 unidades de desviación a favor de A1, y harían falta 191 para anular la ventaja (153 en A2 − R0).

## Regla secuencial

1. A1 frente a R0: el límite inferior 0,02720 supera 0,0005 y la condición de nivel se toma como satisfecha, pero falla la salvaguarda de cliente nuevo. No se promueve.
2. A2 frente a R0, que sigue de titular: límite 0,02415, también falla cliente nuevo. No se promueve.

Titular final: R0. Si A1 se hubiera promovido, A2 tampoco habría pasado frente a A1 (límite −0,01061 y fallos en escenarios, segmentos e influencia).

## Potencia de la salvaguarda de cliente nuevo

La desviación típica bootstrap de A1 − R0 en cliente nuevo es 0,01405. Para que el límite unilateral del 95 % quede en −0,001 o más, la diferencia observada tendría que ser al menos 1,645 × 0,01405 − 0,001 ≈ 0,0221 (0,0224 con los cuantiles empíricos), 1,7 veces la ganancia observada de 0,0131. En A2 − R0 haría falta 0,0236 frente a 0,0111.

El margen de −0,001 equivale a 0,07 desviaciones típicas, así que en la práctica esta salvaguarda es una prueba de superioridad unilateral al 5 %, no de no inferioridad: si el efecto real fuera cero pasaría un 5,8 % de las veces, y si fuera igual al observado (0,0131) pasaría un 26 %. Con la misma ganancia, pasar la mitad de las veces pediría unas 24.500 filas de cliente nuevo y una potencia del 80 % pediría unas 55.900, casi toda la cartera de 2024 (59.202) y seis veces el subconjunto actual (9.063). Con los datos de 2024 esta salvaguarda casi no puede pasar para ningún aspirante realista. La interpretación de la propia política («diagnostic non-inferiority safeguard») no corresponde a cómo funciona con este margen.

## Observaciones de revisor

1. Columna no preinscrita. `predicciones_2024.parquet` trae una columna A3 que no está en el orden preinscrito (R0, A1, A2). Correlación con A1 de 0,9998 y totales un 7,7 %, 4,7 % y 4,0 % mayores en autos, edificios y contenidos: parece A1 con otro nivel. No la puntué contra 2024. La política no admite modelos nuevos después de abrir 2024; si A3 se evaluara, sería una enmienda humana fuera de v1.
2. Condición de nivel. La tomé como satisfecha por instrucción, pero la preinscripción no trae huella de la evidencia que cita («T1 frente a L0 en desarrollo 2023: +0,0498…») y la política dice que una condición sin evidencia con huella bloquea la promoción. No cambia el resultado, porque cliente nuevo ya bloquea. El cambio de nivel de A1 en autos para 2025 (+11,5 % frente a R0) supera el límite de 0,05 de cambio no explicado y descansa en la explicación por mezcla. 2024 la apoya en autos: el A/E de R0 es 1,296 en nuevo negocio y 1,030 en renovación, el de A1 es 1,061 y 1,110. En hogar no la apoya: los dos modelos se equivocan igual en nuevo negocio (edificios A/E 0,49 en los dos; contenidos 1,40 en R0 y 1,36 en A1). Además el nuevo negocio orgánico de 2024 no es la cartera transferida de 2025.
3. Nivel de edificios. Los tres modelos sobrestiman edificios 2024 en un 60 % aproximadamente (A/E 0,61–0,63) y R0 tiene D² negativo en ese ramo. Viene del nivel de 2023: seis incendios de 181.000 a 340.000 CU, que son seis de los siete mayores siniestros de los dos años. Buena parte de la ganancia de A1 en edificios (+0,086) se gana frente a un nivel común equivocado, y A1 no corrige ese nivel.
4. Concentración. En A1 − R0, el 0,1 % de las componentes aporta el 63 % de la ventaja en desviación. La salvaguarda de influencia pasa, pero la ventaja se apoya mucho en pocas filas con siniestro.
5. Familia de Bonferroni. Se fijó en seis contrastes para cuatro modelos y aquí hay tres (tres contrastes). El cuantil 0,05/12 es más conservador de lo necesario; no cambia el resultado.
6. Exposición. La exposición registrada de 2023 suma 26.536 años en autos frente a 18.865 años contados por fechas, por los errores de unidad ya conocidos. R0 no los arrastra a 2024: su tasa por año vale 363,76 (autos), 490,74 (edificios) y 89,23 (contenidos) y ninguna predicción supera la de un año completo. Sin el archivo de completitud no pude reproducir el vínculo e_ef_coste que define R0.

## Archivos

- `codigo/objetivo.py`: objetivo por fila y escenarios. Salidas: `objetivo_por_fila.parquet` y `objetivo_resumen.json`.
- `codigo/compuerta.py`: métrica, bootstrap, salvaguardas y regla secuencial. Salidas: `resultados_compuerta.json` y `bootstrap_difs.npz`.
- `codigo/ensamblar.py`: potencia, A/E por segmento y manifiesto. Salida: `resultados.json`.
