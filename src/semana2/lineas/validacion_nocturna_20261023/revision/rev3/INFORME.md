# Revisión independiente rev3: envíos R0 y A1 de la parte 2, prima comercial y comprobación de la parte 1

Fecha: 23 de octubre de 2026. Revisor: rev3, sin acceso al código de producción ni a las revisiones rev1 y rev2. Todo se recalculó desde los Parquet originales de `datos/s1` (desarrollado) y `datos/s2` (emergente), con un hilo de CPU. Scripts y salidas en `/home/claude/noche/revision/rev3/` (`t1_formato.py` a `t5_resumen.py`; cifras completas en `resultados.json`).

Convenciones: la exposición es días inclusivos / 365. En el test coincide exactamente con la columna `exposure`, pero en el entrenamiento emergente esa columna está corrupta en unas 600 filas (algunas traen el número de días). La tasa es el coste esperado por año-exposición. T0 es el incurrido menos los recobros de los siniestros aceptados.

## 1. Formato de los envíos

Los dos CSV tienen las 209.063 filas de `sample_submission`, en el mismo orden y sin duplicados. Todos los valores son finitos y estrictamente positivos. El prefijo de `row_id` (M, B, C) coincide con el ramo del archivo de test.

| | R0 | A1 |
| --- | ---: | ---: |
| SHA-256 | 928865e5…cb3e | 4a9f7fc0…15f9 |
| Mínimo / máximo | 0,243 / 456,29 | 0,097 / 3.491,81 |
| Total autos (CU) | 36.049.690 | 41.166.995 |
| Total edificios | 19.843.204 | 20.450.750 |
| Total contenidos | 5.310.069 | 5.535.177 |
| Total | 61.202.963 | 67.152.922 |
| Tasa autos (79.007,0 años) | 456,28 | 521,06 (NB 559,31; REN 394,06) |
| Tasa edificios (47.376,4) | 418,84 | 431,67 (NB 431,88; REN 430,97) |
| Tasa contenidos (59.016,5) | 89,98 | 93,79 (NB 94,32; REN 92,00) |
| Tasa global (185.399,9) | 330,11 | 362,21 |

R0 es una tasa plana por ramo multiplicada por la exposición: el coeficiente de variación de predicción/exposición es 0,0004. Esa tasa coincide con la tasa última sin tendencia del libro 2023–2024 que estimé en la sección 2 (cociente 1,005, 0,993 y 0,996).

## 2. Nivel independiente 2025 por ramo

### Método

1. Asigné cada siniestro por `policy_id`, ramo y `loss_date` dentro del periodo: 9.222 únicos y ningún ambiguo. Los 36 aceptados sin periodo (92.267 CU, casi todos con pérdida en 2021–2022) quedan fuera. Los 120 rechazados valen cero.
2. Medí el reporte con el desarrollado. Estimé la distribución del retraso por peligro con Lynden-Bell para datos truncados a la derecha, ponderada por coste. La completitud a 31-12-2024 de cada cohorte emergente se pondera por la exposición diaria del emergente y por la estacionalidad del desarrollado. El patrón propio del emergente da lo mismo: lesiones corporales 2024, 0,545 frente a 0,543. Completitud en coste de 2024: lesiones 0,543, hundimiento 0,669, terceros 0,937, escape de agua entre 0,936 y 0,938; el resto, entre 0,95 y 0,98.
3. Para el IBNR usé chain-ladder. En 2024, lesiones y hundimiento usan Bornhuetter-Ferguson con a priori igual a la tasa última de 2023 del emergente.
4. Como IBNER, anticipé recobros en los abiertos. Ningún abierto tiene recobros, mientras que los cerrados recuperan el 24 % (daños propios) y el 4 % (robo); el efecto es −97.292 CU en autos 2024, un 0,25 % del libro. No añadí más IBNER: una sola valoración no lo identifica.
5. La tendencia es la severidad anual del desarrollado 2021–2024: autos +1,9 %, edificios +6,2 %, contenidos +3,5 %. No apliqué tendencia de frecuencia. Como contraste, la tarifa de renovaciones del emergente sube de 2024 a 2025 un 1,1 %, un 6,3 % y un 5,2 %.
6. La mezcla 2025 es lo que más pesa. El 77 % de la exposición es nuevo negocio (NB), frente al 7,8 % de la historia. Las filas NB de 2025 son indistinguibles del NB orgánico de 2023–2024 en todas las variables observadas: edad, años de licencia, NCB, segmento de marketing, aseguradora previa, campaña y siniestros previos. La relatividad NB/REN es frecuencia × severidad, cada una con credibilidad de fluctuación limitada (1.082 siniestros, y 1.082 × (1 + CV²) en severidad) frente al desarrollado 2021–2023.

### Resultados (CU por año-exposición)

| | Autos | Edificios | Contenidos |
| --- | ---: | ---: | ---: |
| Reportado 2023 / 2024 | 432,7 / 382,7 | 514,3 / 306,7 | 91,1 / 86,8 |
| Último 2023 / 2024 | 444,4 / 463,3 | 516,1 / 333,3 | 91,3 / 89,5 |
| Libro último sin tendencia (L0) | 454,2 | 421,9 | 90,4 |
| Libro último con tendencia (L1) | 466,8 | 464,6 | 95,2 |
| L1 con mezcla según tarifa (L2) | 516,6 | 459,2 | 94,2 |
| Relatividad NB/REN emergente (frecuencia × severidad) | 1,335 × 1,228 = 1,63 | 0,975 × 0,868 = 0,85 | 1,395 × 0,956 = 1,33 |
| Relatividad NB/REN desarrollado | 1,404 × 0,978 = 1,37 | 1,109 × 0,969 = 1,08 | 1,201 × 0,876 = 1,05 |
| Credibilidad Z (frecuencia, severidad) | 0,80; 0,33 | 0,27; 0,08 | 0,31; 0,16 |
| Relatividad con credibilidad | 1,430 | 1,032 | 1,120 |
| Central L3 (tendencia y mezcla de experiencia) | 601,0 (REN 451,6; NB 646,0) | 474,7 | 103,0 |
| L3 sin tendencia | 584,8 | 431,1 | 97,8 |
| L3 con la relatividad del desarrollado / del emergente | 583,8 / 660,8 | 488,6 / 414,4 | 98,6 / 116,2 |
| CV del nivel del libro (Poisson compuesto) | 2,9 % | 10,1 % | 6,2 % |
| R0 (cociente con el central) | 456,3 (0,76) | 418,8 (0,88) | 90,0 (0,87) |
| A1 (cociente con el central) | 521,1 (0,87) | 431,7 (0,91) | 93,8 (0,91) |

En autos, A1 es más plausible que R0. A1 recoge un efecto de nuevo negocio (NB/REN 1,42) que coincide con mi relatividad con credibilidad (1,43). En el desarrollado, el NB tiene 1,40 veces la frecuencia y una razón de siniestralidad sobre prima escrita 1,22 veces la de renovación, así que el efecto es sistemático en el generador. R0 lo ignora y queda un 24 % por debajo.

Aun así, el nivel base de A1 parece bajo. Su tasa de renovación (394,06) coincide al 0,01 % con la tasa reportada del libro, sin IBNR ni tendencia, descargada de la mezcla NB con su propia relatividad (394,00). Eso indica que A1 en autos no lleva el IBNR de lesiones de 2024 (completitud 0,54). La renovación último sin tendencia es de unos 440. En hogar, A1 sí queda entre un 4 % y un 6 % por encima del reportado. Si se corrige el IBNR, A1 en autos subiría hacia 580–600.

El escenario más bajo defendible es 517: ocurre si el bloque transferido del broker solo es más caro en lo que ya recoge la tarifa (NB 700 frente a REN 608 de prima escrita anual) y no arrastra el efecto de NB de la experiencia. Supuesto clave no verificable: que la cartera del broker se comporte como el NB orgánico. Sus características observadas dicen que sí.

En edificios, R0 y A1 son indistinguibles con estos datos. Los dos caen dentro de la banda bootstrap del 90 % (401 a 555 para L3). A1 queda un poco más cerca del central y, sin tendencia, ambos coinciden con la experiencia (L3 sin tendencia 431). La diferencia entre ellos (13 CU) es pequeña frente a la incertidumbre de incendio.

En contenidos, A1 es más plausible: tiene algo de recargo NB (1,025, frente a mi 1,12) y un nivel algo mayor. Los dos están probablemente entre un 5 % y un 10 % bajos. R0 queda 2 desviaciones típicas por debajo del central.

### Incertidumbre de edificios (incendio)

Incendio explica el 81 % de la varianza bootstrap del nivel de edificios. En 2023 hubo 49 incendios, que costaron 3,22 M CU (tasa 284). En 2024 hubo 21 (1,13 M CU; tasa 95). Con una tasa común se esperaban 33,9 y 36,1 (χ² = 13,0 con 1 g.l., p = 0,0003). El exceso de 2023 se concentra en la región E02, con 18 incendios frente a 2 en 2024 con la misma exposición. En el desarrollado, incendio no muestra efecto año (p = 0,35) ni región-año (p = 0,59). Los incendios grandes son pérdidas totales al capital (hasta 361.093 CU); la severidad media es 62.120 CU en el emergente y 51.773 en el desarrollado, con CV² de 1,86.

| Supuesto | Tasa de incendio | Edificios L1 | Edificios L3 |
| --- | ---: | ---: | ---: |
| Media 2023–2024 (central) | 208 | 465 | 475 |
| Solo 2023 | 321 | 578 | 590 |
| Solo 2024 | 101 | 358 | 366 |
| Frecuencia del modelo del desarrollado con `wildfire_index` × severidad emergente | 218 | 475 | 486 |

El bootstrap de Poisson por fila, con 4.000 réplicas y sin efecto año, da para L1 una media de 465, una desviación típica de 46 (CV 9,9 %) y un intervalo del 90 % de 393 a 543; para L3, de 401 a 555. Si se añade un efecto año estimado por momentos (CV del efecto año 0,59, con solo 1 g.l.), el intervalo del 90 % de L3 se abre a 310–640.

Hay una referencia externa que apoya la media de dos años y no la de 2024 sola. La frecuencia de incendio del desarrollado crece con `wildfire_index` (coeficiente 1,51 ± 0,27 en escala log). Aplicada al clima emergente, predice 35,7 y 39,7 incendios frente a los 49 y 21 observados (75,4 frente a 70 en total) y una frecuencia de 0,0032 para 2025, frente a 0,0030 observada en 2023–2024. Es una extrapolación: el índice emergente llega a 1,0 y el desarrollado solo a 0,6.

## 3. Prima comercial de las 20 pólizas de referencia

La construcción que usaría coincide con la del CSV revisado:

P = [R + 0,12·R·1{edificios o contenidos} + 85·e] / (1 − 0,15 − c − 0,08 − 0,08), con c = 0 en directo y 0,20 en broker.

El denominador vale 0,69 en directo y 0,49 en broker. R es la prima de riesgo de la fila, es decir, el coste del periodo. "Share of premium" se lee como fracción de la prima comercial. El reaseguro catastrófico se carga sobre R solo en hogar y pasa por la comisión, el impuesto y el margen.

Recalculé las 20 primas desde `A1_2025.csv`. Coinciden con las filas `modelo == 'A1'` del CSV con una diferencia máxima de 0,0075 CU, y las primas de riesgo con una de 0,0045 CU (redondeo a dos decimales). El reaseguro es igual a 0,12·R y el gasto fijo igual a 85·e. No hay errores aritméticos.

Interpretaciones discutibles:

1. Gasto fijo en filas cortas. La base proporcional (85·e) es correcta cuando la fila es un tramo de una póliza que tiene otra fila en 2025. La sensibilidad "F entero" del CSV carga 85 completos a cada fila, y eso cuenta el gasto dos veces en dos casos:
   - C00314425 tiene otra fila de su póliza en 2025 (C00318346, e = 0,899). Con el gasto de la póliza repartido entre sus filas, F = 6,02 y P = 20,10, en lugar de 181,28.
   - B00250679 es el segundo tramo de una póliza nueva iniciada el 15 de noviembre (la otra fila es B00213756). Si F se cobra por póliza y término, le tocan 72,34 y P = 208,69, no 234,53. Si F es un coste anual, la base de 80,07 es la correcta.
   - M00129413 es una póliza nueva de una sola fila desde el 2 de septiembre. Ahí sí aplica la disyuntiva entre 335,19 (coste anual proporcional) y 451,16 (coste por contrato).
2. El impuesto va dentro del denominador. Si se cobra encima de la prima neta, con la comisión, los gastos y el margen calculados sobre la prima sin impuesto, P baja un 7,2 % en broker y un 3,3 % en directo. Para las 20 de A1, la suma pasa de 16.112 a 15.085 CU.
3. Reaseguro catastrófico. Aplicarlo a contenidos es la lectura literal de "property"; si solo se aplicara a edificios, las primas de contenidos bajarían unos 13 CU. El cargo pasa por el gross-up de comisión, impuesto y margen; es una elección razonable, pero conviene declararla.
4. La comisión de comparadores está en blanco en el emergente, pero el 5,0 % de las filas de test de 2025 son `comparison_site`. Ninguna de las 20 referencias lo es, pero la construcción para toda la cartera necesita un supuesto.
5. El gasto fijo es entre el 40 % y el 68 % de la prima comercial de contenidos a año completo (56–68 % cuando R < 60 CU). La prima anualizada es entre 0,85 y 6,13 veces la prima escrita (mediana 2,67). En los dos mercados la prima escrita está cerca de la prima de riesgo (razón de siniestralidad sobre ella entre 0,6 y 1,3), así que se comporta como una tarifa técnica: la columna `razon_anualizada_escrita` no debe leerse como un aumento de tarifa necesario sin esa advertencia.
6. Las primas de autos heredan el nivel de A1, que en la sección 2 parece entre un 10 % y un 15 % bajo.

## 4. Comprobación de la parte 1 (S30)

SHA-256 del archivo: afd72dca…131e. El D² Tweedie de potencia 1,5, con el nulo igual a la media de y del conjunto, sale así:

| | Global | Autos | Edificios | Contenidos |
| --- | ---: | ---: | ---: | ---: |
| V24 (626.190 filas) | 0,137880 | 0,091681 | 0,115798 | 0,096650 |
| V23 (313.515 filas) | 0,145418 | 0,094408 | 0,116871 | 0,092594 |

Por ramo, el nulo es la media del propio ramo. scikit-learn da el mismo global. En V24, la suma de las predicciones dividida por la de T0 es 0,99 en autos, 0,91 en edificios y 0,98 en contenidos.

Recalculé T0 de forma independiente: siniestros aceptados, neto de recobros, sin las 604 copias que solo difieren en `claim_id`, asignados por póliza, ramo y fecha. Coincide con `y_T0` en las 626.190 filas de V24 (diferencia máxima 1,5e-11; total 175.536.961,49 CU; 35.372 filas con siniestro; ninguna asignación múltiple). `reserva_caso` también coincide. Las 604 copias tienen fecha de pérdida en 2020–2022 (600 en 2022), así que no afectan a T0 de 2024: el total sale igual con o sin depurarlas.

## Límites

- El nivel de autos depende sobre todo de un supuesto que estos datos no permiten comprobar: que el bloque transferido del broker tenga el mismo efecto de nuevo negocio que el NB orgánico.
- La tendencia viene del desarrollado; con dos años, el emergente no la identifica.
- El IBNER se supone nulo salvo los recobros.
- En edificios, el intervalo con efecto año se apoya en un solo grado de libertad.
- El patrón de reporte del desarrollado está condicionado a retrasos de hasta unos 1.460 días.
