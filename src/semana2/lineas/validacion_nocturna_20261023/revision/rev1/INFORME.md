# Revisión independiente rev1: datos de la parte 2 y auditoría de tres OOF

Fecha: 23 de octubre de 2026. Revisor: Claude, revisión independiente asistida por IA (no sustituye una revisión profesional humana).

Todo se recalculó desde los Parquet originales con código propio, en `/home/claude/noche/revision/rev1/codigo/` (ocho scripts; huellas SHA-256 en `resultados.json`, clave `meta`). Los 24 Parquet de `datos/s1` y `datos/s2` coinciden por SHA-256 con sus manifiestos. De `salidas/` solo leí `data_description_p2.md` y los tres OOF autorizados; no abrí nada de `codigo/`. Los ajustes usaron un solo hilo.

Convenciones: exposición para modelar = días inclusivos / 365; un siniestro se asigna a una fila por `policy_id` + `line` + `loss_date` dentro de `[period_start, period_end]`; aceptado = `status` distinto de `repudiated`; neto = `incurred_to_date − recoveries`; D² = `sklearn.metrics.d2_tweedie_score(power=1.5)` sin pesos. Cada cifra de abajo está en `resultados.json` con el nombre de su ítem.

## 1. Exposición en el mercado emergente

| Ramo | Año | Filas | Difieren más de 0,0001 de días/365 | Explicadas por días/360 | Explicadas por número de días | Sin explicar |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| motor | 2023 | 21.680 | 129 | 107 | 22 | 0 |
| motor | 2024 | 25.603 | 125 | 100 | 25 | 0 |
| buildings | 2023 | 12.580 | 82 | 61 | 21 | 0 |
| buildings | 2024 | 14.867 | 72 | 60 | 12 | 0 |
| contents | 2023 | 15.834 | 89 | 75 | 14 | 0 |
| contents | 2024 | 18.732 | 111 | 91 | 20 | 0 |
| Total | | 109.296 | 608 | 494 | 114 | 0 |

Con el umbral pedido salen 608 filas. Si se exige igualdad exacta con días/365 redondeado a cuatro decimales salen 609: la fila B00078610 (1 de enero de 2024, un día) tiene exposición 0,0028 = 1/360, y su diferencia con 1/365 es 0,00006, por debajo del umbral. Las 609 quedan explicadas por una de las dos convenciones; ninguna queda sin explicar. 452 filas de entrenamiento tienen exposición registrada mayor que 1. La exposición registrada suma 127.105,45 años y la de días/365, 91.494,52.

En test, las 209.063 filas coinciden con días/365 redondeado a cuatro decimales; ninguna difiere.

Dato adicional: ninguna fila de 2024 cubre el 31 de diciembre de 2024 (el último `period_end` de 2024 es el 30 de diciembre), y el último `loss_date` del archivo de siniestros es el 29 de diciembre de 2024. Es el mismo hueco del 31 de diciembre que tenía el mercado desarrollado.

## 2. Siniestros del mercado emergente y T0

Estados: 8.082 closed, 1.056 open y 120 repudiated (107 en autos, 13 en contenidos y ninguno en edificios). Los 120 rechazados tienen incurrido cero y todos caen en una fila.

De los 9.138 aceptados, 9.102 caen en exactamente una fila de entrenamiento, 36 en ninguna y ninguno en más de una. Los 36 sin fila tienen la fecha de pérdida antes del primer periodo observado de su póliza en ese ramo, entre 14 y 431 días antes (mediana 232). Por año de pérdida son 6 de 2021, 28 de 2022 y 2 de 2023; por ramo, 28 de autos, 5 de contenidos y 3 de edificios. 35 de los 36 se reportaron mientras la póliza tenía un periodo observado. Suman 92.267,26 CU netos y quedan fuera de T0.

T0, incurrido neto observado de los aceptados con fila única:

| Ramo | Siniestros | T0 2023 (CU) | T0 2024 (CU) | T0 total (CU) |
| --- | ---: | ---: | ---: | ---: |
| motor | 7.048 | 8.162.761,21 | 7.693.126,75 | 15.855.887,96 |
| buildings | 1.056 | 5.848.688,10 | 3.710.061,21 | 9.558.749,31 |
| contents | 998 | 1.285.654,53 | 1.297.699,77 | 2.583.354,30 |
| Total | 9.102 | | | 27.997.991,57 |

Comprobaciones sin hallazgos: `claim_id` único (todos de 10 caracteres), ningún par de siniestros idéntico salvo el identificador, sin nulos en importes, ningún reporte antes de la pérdida ni después del 31 de diciembre de 2024, pagado nunca mayor que incurrido y ningún neto aceptado menor o igual que cero. Edificios tiene un T0 de 2023 un 58 % mayor que el de 2024 con un número de siniestros parecido (519 frente a 537); no lo investigué.

## 3. Duplicados del mercado desarrollado

El archivo tiene 163.150 siniestros. Agrupando por todas las columnas salvo `claim_id` (con los nulos de `repairer_id` y `third_party_id` tratados como iguales) aparecen 604 grupos, todos de dos filas. En los 604 pares, un identificador tiene el formato habitual del archivo, «CL» más ocho dígitos (162.546 de los 163.150 identificadores), y el otro tiene «CL» más nueve dígitos (entre 100.177.477 y 199.846.653). Los 604 identificadores de nueve dígitos están todos en algún par, y el largo no se deriva del corto. Quitar `repairer_id` y `third_party_id` de la clave no descubre más pares.

Conservé la copia con el identificador de ocho dígitos porque es el formato del 99,6 % del archivo; el identificador de nueve dígitos solo aparece en las copias. La elección no cambia T0, porque las dos filas de cada par son idénticas en todos los demás campos.

Las copias eliminadas son 395 closed, 11 open y 5 repudiated en autos, 108 closed y 1 open en edificios y 83 closed y 1 repudiated en contenidos. Su neto aceptado suma 3.174.167,49 CU.

| Ramo | Aceptados con fila única | T0 sin copias (CU) | T0 con copias (CU) |
| --- | ---: | ---: | ---: |
| motor | 110.496 | 428.762.846,58 | 430.595.512,14 |
| buildings | 26.266 | 246.656.437,27 | 247.768.586,05 |
| contents | 23.670 | 65.737.584,58 | 65.966.578,85 |
| Total | 160.432 | 741.156.868,43 | 744.330.677,04 |

Después de quitar las copias quedan 409 aceptados sin fila, todos anteriores al primer periodo de su póliza (293 de autos, 67 de edificios y 49 de contenidos; 1.721.459,84 CU), y ninguno con más de una fila.

## 4. Capital de hogar en el mercado emergente

En los dos ramos la distribución de `sum_insured` (entrenamiento y test juntos) tiene un hueco claro. En edificios no hay ningún valor entre 894.000 y 60.000.000 (un salto de 67 veces) y en contenidos ninguno entre 283.200 y 7.600.000 (27 veces). La prueba por fila es la prima escrita por cada mil de capital, que usa solo la propia fila:

| | Edificios | Contenidos |
| --- | --- | --- |
| Población normal: prima por mil (mín.; mediana; máx.) | 0,451; 1,057; 17,44 | 1,606; 3,432; 10,59 |
| Nube extrema con el capital registrado | 0,0006; 0,0011; 0,0110 | 0,0021; 0,0034; 0,0070 |
| Nube extrema con el capital entre 1.000 | 0,603; 1,093; 11,00 | 2,089; 3,362; 6,95 |
| Capital entre 1.000 de la nube extrema (mín.; mediana; máx.) | 60.000; 233.000; 568.000 | 7.600; 35.900; 131.600 |
| Capital de la población normal (mín.; mediana; máx.) | 44.000; 236.000; 894.000 | 4.900; 36.000; 283.200 |

Con el capital registrado, la prima por mil de todas las filas extremas queda muy por debajo del mínimo de la población normal: la más cercana está 41 veces por debajo en edificios y 231 veces en contenidos. Dividida entre mil cae dentro del rango normal, con una mediana casi igual a la normal. La prima por mil de la población normal no depende de la exposición (medianas por tramo de 1,04 a 1,07 en edificios y de 3,38 a 3,49 en contenidos), así que la prima escrita es anual y la comparación vale también para filas cortas.

Regla aplicada a cada fila: dividir entre mil si la prima por mil está por debajo del mínimo normal y, dividida, cae dentro del rango normal. Marca exactamente las mismas filas que quedan por encima del hueco, sin ninguna discrepancia. Como contraste, ajusté por mínimos cuadrados el logaritmo de la prima sobre las demás variables de la fila en la población normal. Con el capital registrado, los residuos de las extremas quedan entre −4,7 y −2,1 en edificios y entre −5,1 y −4,2 en contenidos. Con el capital dividido caen dentro del rango normal: en edificios ninguna pasa de cuatro desviaciones típicas, y en contenidos una queda en 4,0. Ese ajuste explica poco la prima de edificios (R² 0,18), y por eso lo uso solo como apoyo. También como apoyo, fuera de la regla por fila: 80 de las 157 filas extremas de edificios y 95 de las 192 de contenidos tienen otra fila normal en la misma póliza, y la mediana del capital dividido frente a esa fila es 1,00.

Filas que dividiría entre mil: 157 en edificios (53 de entrenamiento y 104 de test) y 192 en contenidos (57 y 135). En total son 349: 110 de entrenamiento y 239 de test. Las listas están en `item4_filas_buildings.csv` e `item4_filas_contents.csv`.

## 5. Efecto del nuevo negocio en la frecuencia

Método. Ajusté un GLM de Poisson por ramo (glum, ridge 1e-6) sobre el entrenamiento desarrollado 2021–2024. La respuesta son los siniestros aceptados con fila única sin duplicados, con desplazamiento log(días/365) y un factor de año. Usé covariables presentes en los dos mercados, sin `new_business`, `renewal_count`, `customer_since_year` ni `customer_service_contacts` (esta última mide el siniestro del propio periodo):

- de la póliza: franquicias, canal, forma de pago, impagos y días entre cotización e inicio;
- del cliente: estado civil, tamaño del hogar, siniestros previos declarados, puntos del carné y años en la dirección;
- de la dirección: todas las del archivo salvo la región, que tiene códigos distintos en cada mercado;
- del clima del año: las siete variables en hogar y los días de granizo en autos;
- de cada ramo: en autos, el tramo de edad derivado de `driver_age`, los años de carné, el NCB, el vehículo y la cobertura; en hogar, el tramo de edad, el capital corregido con la regla del ítem 4 y las variables del ramo.

Las numéricas entran por deciles del desarrollado y los nulos como nivel propio. En el desarrollado, los `customer_id` de autos se completaron con ceros a ocho dígitos (sin eso, el 10 % de las filas no cruza con clientes). Para predecir el emergente se usa el nivel de año 2023 del desarrollado.

Las construcciones T y W del desarrollado se tratan como madera (timber). El desarrollado no tiene ninguna fila «timber», mientras que T y W son el 12,1 % de sus filas; en el emergente, WOD es el 12,0 %. En una primera corrida mía, WOD quedaba en el nivel de referencia. Corregido, el resultado casi no cambia (la razón de edificios en 2023 pasa de 1,2311 a 1,2319); la corrida anterior queda archivada como superada.

Los intervalos salen de un bootstrap de Poisson por cliente con 2.000 réplicas y no incluyen la incertidumbre de los coeficientes. Corrí tres especificaciones: la base; la base más el mes de inicio y la duración de la fila («calendario»); y la base más variables comerciales, prima escrita y descuento («ampliada»).

Razón entre el O/E de las filas de nuevo negocio y el de las demás, con los tres ramos juntos:

| Especificación | Desarrollado 2021–2024 (IC90) | Emergente 2023 (IC90) | Emergente 2024 | Emergente 2023+2024 | IC90 de emergente 2023 / desarrollado | P(emergente 2023 > desarrollado) |
| --- | --- | --- | ---: | ---: | --- | ---: |
| Base | 1,097 (1,082; 1,112) | 1,208 (1,099; 1,322) | 1,039 | 1,112 | (1,001; 1,206) | 0,95 |
| Calendario | 1,045 (1,030; 1,059) | 1,147 (1,043; 1,255) | 0,989 | 1,056 | (0,997; 1,203) | 0,94 |
| Ampliada | 1,038 (1,024; 1,053) | 1,166 (1,060; 1,276) | 1,011 | 1,077 | (1,018; 1,230) | 0,97 |

Con la especificación base, en el emergente de 2023 las filas de nuevo negocio tienen 392 siniestros frente a 288,8 esperados (O/E 1,356, IC90 1,233–1,479) y las demás 4.175 frente a 3.716,7 (1,122, IC90 1,092–1,153); el error típico de la razón es 0,069, frente a 0,009 en el desarrollado. Por ramo, también con la base, la razón de 2023 es 1,205 en autos (IC90 1,087–1,338), 1,232 en edificios (0,917–1,574) y 1,174 en contenidos (0,856–1,513); en 2024 es 1,028, 0,750 y 1,402.

Lectura. En el desarrollado, las filas de nuevo negocio tienen un 10 % más de siniestros de lo que predicen las covariables. Cerca de la mitad se explica por el calendario: esas filas empiezan a mitad de año y son más cortas (exposición media 0,46 años en autos frente a 0,86 de las renovaciones), y con el mes de inicio y la duración el efecto queda en un 4–5 %. En el emergente, la cifra de 2023 es mayor, y en dos de las tres especificaciones su intervalo frente al desarrollado apenas excluye el 1. La de 2024 es igual o menor que la del desarrollado, y juntando 2023 y 2024 la razón emergente (1,056 a 1,112) queda casi encima de la desarrollada (1,038 a 1,097). Con un año a favor y otro en contra, no veo evidencia sólida de que el efecto del nuevo negocio en la frecuencia sea distinto en los dos mercados. Los datos son compatibles con el mismo efecto del 4–10 % más ruido; si algo apuntan, es a un exceso en 2023 que 2024 no repite. Aparte, el emergente tiene en conjunto un 14–18 % más de frecuencia que la que predice el modelo desarrollado (O/E global de 1,139 a 1,178 según especificación y año).

Una advertencia sobre la variable: según la descripción, la aseguradora entró en el emergente en 2023. Sin embargo, el 88 % de las filas de 2023 no son nuevo negocio, `renewal_count` llega a 15 y `customer_since_year` empieza en 2008. Las filas de nuevo negocio tienen siempre `customer_since_year` igual al año de la fila. En el test, el 76 % de las filas son nuevo negocio.

## 6. Auditoría de los tres OOF (L0_tasa, L3_gbm, T1_dev_nivel)

Estructura. Los tres archivos tienen las mismas 50.094 filas, que son exactamente las de entrenamiento de 2023 (21.680 de autos, 12.580 de edificios y 15.834 de contenidos), con los mismos campos y pliegues. `customer_id`, `address_id`, `line` y `new_business` coinciden con los originales. La columna `exposure` es días/365 (diferencia máxima 0,00005, por redondeo) y difiere de la registrada en las 300 filas de 2023 con otra convención. `eef` depende solo del ramo y de las fechas de la fila y vale entre 0,939 y 1,000 veces días/365 (mediana 0,997). Parece un ajuste por completitud de reporte, pero su construcción no está en los archivos. En T1 la `eef` difiere de la de L0 solo en el último bit.

(a) Pliegues. Ninguno de los 31.160 clientes ni ninguna póliza aparece en más de un pliegue, así que la agrupación por cliente es real. Las direcciones no están agrupadas: 213 de las 31.581 aparecen en más de un pliegue. Afectan a 595 filas (388 de autos, 144 de contenidos y 63 de edificios), con 177.038,22 CU de y, el 1,2 % del total. Esto solo es una fuga si algún modelo usa información de la dirección construida con el objetivo; con covariables físicas no lo es.

(b) La y coincide con mi T0 del ítem 2 en las 50.094 filas, con diferencia máxima 0 y suma 15.297.103,84 CU en ambos casos.

(c) D² con potencia 1,5:

| Archivo | Global | Autos | Edificios | Contenidos |
| --- | ---: | ---: | ---: | ---: |
| L0_tasa | 0,06766 | −0,00307 | 0,01568 | 0,02702 |
| L3_gbm | 0,08328 | 0,00542 | 0,04311 | 0,04237 |
| T1_dev_nivel | 0,11743 | 0,02848 | 0,08067 | 0,10803 |

(d) Bootstrap por componentes conexas del grafo cliente–dirección: 30.869 componentes, la mayor de 7 filas, y 4.000 réplicas, con las predicciones fijas.

| Diferencia | Puntual | Error típico | IC90 | P(> 0) |
| --- | ---: | ---: | --- | ---: |
| T1 − L0, todas las filas | +0,0498 | 0,0080 | (+0,0369; +0,0630) | 1,00 |
| T1 − L3, todas las filas | +0,0342 | 0,0077 | (+0,0215; +0,0470) | 1,00 |
| T1 − L0, sin el 0,1 % mayor | +0,0461 | 0,0048 | (+0,0382; +0,0540) | 1,00 |
| T1 − L3, sin el 0,1 % mayor | +0,0326 | 0,0043 | (+0,0255; +0,0396) | 1,00 |

(e) El 0,1 % superior son 50 filas, con y de 37.716,45 CU o más: 39 de edificios y 11 de autos. Esas filas suman el 29,6 % de toda la y. Sin ellas, el D² es 0,0364 en L0, 0,0499 en L3 y 0,0825 en T1. En edificios sale negativo para los tres (−0,143, −0,127 y −0,100) porque el nivel de las predicciones lleva dentro esas pérdidas grandes. Si se renivela cada ramo sobre las filas que quedan, las diferencias son +0,0399 frente a L0 y +0,0321 frente a L3. T1 supera a L0 y a L3 en los cinco pliegues.

Firmas de cada archivo.

- L0_tasa es una tasa constante por ramo multiplicada por `eef`, y en las 15 celdas de ramo y pliegue su tasa es exactamente la de los otros cuatro pliegues (razón 1,000000): es un OOF correcto. Su balance total (1,00026) sale de la aritmética de pliegues de tamaño parecido, no de una fuga.
- L3_gbm tiene, por ramo y pliegue, un nivel dentro de ±2 % del de los otros pliegues. En contenidos, el pliegue 4 está degenerado: solo produce 7 tasas distintas (83,2 a 87,6 por unidad de `eef`), con un coeficiente de variación de 0,017 frente a 0,24–0,53 en los demás pliegues. Su D² en ese pliegue es 0,023, casi igual al de L0 (0,019) y muy lejos del de T1 (0,154). En una quinta parte de contenidos, L3 es en la práctica un modelo constante.
- T1_dev_nivel cuadra los totales por ramo con un error de 1e-5 en autos y contenidos (0,999995 y 0,99999) y de 6,5e-4 en edificios. Con los archivos no puedo saber si su nivel se fijó fuera de pliegue o con todas las filas; L0 muestra que un nivel fuera de pliegue también cuadra casi exacto.

Referencia propia para juzgar si T1 es creíble. Ajusté un GLM Tweedie 1,5 solo con el desarrollado 2021–2024 (mismas covariables que el ítem 5, sin ajuste fino) y lo apliqué al emergente de 2023. Con el nivel por ramo fijado fuera de pliegue con los mismos pliegues de los archivos da D² 0,1112 (autos 0,0248, edificios 0,0709, contenidos 0,1005). Con el nivel calculado con todas las filas da 0,1143, así que un nivel dentro de muestra vale unas 0,003 de D². La correlación de los logaritmos con T1 es 0,83–0,85. El 0,117 de T1 es por tanto creíble para relatividades del desarrollado con nivel emergente, y no veo señales de fuga del objetivo: aunque su nivel fuera dentro de muestra, eso explicaría como mucho 0,003 de una ventaja de 0,034 a 0,050.

Cruce entre mercados. Los 47.283 `row_id` de autos del entrenamiento emergente existen también como `row_id` de autos del desarrollado (en hogar no hay ninguno). Un cruce por `row_id` entre mercados funcionaría en silencio. No veo rastro de que eso ocurriera: la tasa de T1 en autos no se correlaciona con el T0 desarrollado del mismo `row_id` (Spearman 0,009).

Calibración por nuevo negocio. Los tres modelos, y también mi referencia, predicen solo el 63–71 % del coste observado en las filas de nuevo negocio, es decir, un A/E de 1,41 a 1,58. En las demás predicen el 103–104 %. Esto cuadra con el ítem 5 y pesa en 2025, cuando el 76 % del test es nuevo negocio.

Lo que no pude verificar: con qué datos y variables se entrenaron L3 y T1, en particular si entraron filas de 2024 de clientes del pliegue retenido o si los hiperparámetros se eligieron mirando todos los pliegues; cómo se construyó `eef` (si se estimó con siniestros emergentes que incluyen los pliegues retenidos, sería un elemento dentro de muestra pequeño y común a los tres archivos); y si el nivel de T1 es fuera de pliegue. El bootstrap mide la variación por muestreo de filas con predicciones fijas y no la de reajustar los modelos.

## Problemas encontrados, de más a menos grave

1. L3_gbm, contenidos, pliegue 4: el modelo está degenerado (7 predicciones distintas). La comparación T1 − L3 en contenidos subestima lo que daría un GBM bien ajustado.
2. Nuevo negocio infrapredicho en los tres OOF (A/E 1,41–1,58) y en mi referencia. Es la parte del 2025 que más pesa.
3. Pliegues agrupados solo por cliente: 213 direcciones cruzan pliegues (1,2 % de la y). Es inocuo salvo que algún modelo use historial de siniestros por dirección.
4. No se puede saber si el nivel de T1 es fuera de pliegue; el efecto posible es de unas 0,003 de D².
5. El recorte del 0,1 % superior, tal como se pidió, deja negativo el D² de edificios en los tres modelos; conviene mirar también la versión renivelada.
6. Datos: los `row_id` de autos del entrenamiento emergente repiten los del desarrollado; los códigos T/W del desarrollado son con mucha probabilidad madera; ninguna fila de 2024 cubre el 31 de diciembre; y la marca de nuevo negocio de 2023 contradice la entrada al mercado en 2023 que describe la página de datos.
7. Error mío ya corregido: en la primera corrida del ítem 5, WOD no tenía nivel propio. El cambio en los resultados fue despreciable.

## Archivos

- `resultados.json`: todas las cifras, las huellas de las entradas y de los scripts y las convenciones.
- `codigo/`: `comun.py`, `item1_exposicion.py`, `item2_siniestros_emergente.py`, `item3_duplicados_desarrollado.py`, `item4_capital.py`, `item5_nb_frecuencia.py` (argumentos `core`, `timing` y `extended`), `item6_auditoria_oof.py` e `item6b_referencia_desarrollado.py`.
- Tablas: `t0_emergente_por_fila.parquet`, `t0_desarrollado_por_fila.parquet`, `item2_sin_periodo.csv`, `item4_filas_buildings.csv` e `item4_filas_contents.csv`. Contienen datos del concurso: no se redistribuyen.
