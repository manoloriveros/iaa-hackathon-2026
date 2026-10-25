# Revisión independiente rev4: historial de siniestros (Q1) y tendencia de nivel (Q2)

Revisor independiente, 24-oct-2026. Todo el código y las salidas están en `/home/claude/noche/revision/rev4/`. Cada cifra de este informe sale de `q1_{motor,buildings,contents}.json`, `q2_{...}.json` o `diag_q2_mix.json`, y está consolidada en `resultados.json`. Se usó un solo hilo de CPU y ninguna conexión de red.

## Resumen

- Q1, historial. En el mercado desarrollado, un siniestro aceptado reportado en los 12 meses previos al inicio de la fila multiplica la frecuencia por 1.29 en motor, 1.35 en edificio y 1.31 en contenido, después de controlar por las demás covariables comunes (incluidas NCB y siniestros declarados). En el emergente 2024 la relatividad de motor es casi igual (1.32 frente a 1.29); en hogar es compatible con la del desarrollado, pero con intervalos muy anchos.
- Al llevar los modelos desarrollados al emergente 2024, el historial mejora la desviación de Poisson de forma significativa solo en motor: ΔD² = +0.0039 (IC95 +0.0020 a +0.0058) con GLM y +0.0029 (+0.0009 a +0.0048) con GBM, concentrado en renovaciones. En edificio y contenido el efecto es positivo pero no distinguible de cero.
- La recalibración literal sobre 2023 (protocolo del enunciado) castiga artificialmente al modelo con historial: en 2023 nadie tiene historial observable, así que el modelo trata a todos como "sin siniestros" y en 2024 sobreestima el nivel en unos 8 puntos en motor. Con una calibración neutral, que iguala el total 2024 de ambos modelos sin mirar los resultados de 2024, la ganancia aparece y es estable frente al ajuste por IBNR.
- Q2, nivel. Con relatividades fijas, el índice de costo 2021-2024 crece +2.4 %/año en motor, +6.2 %/año en edificio y +3.7 %/año en contenido (IBNR central, siniestros topados a 250 000 CU). En hogar el motor del crecimiento es la severidad.
- Un asegurador con 10 % de las pólizas que proyecta el año siguiente juntando dos años sin tendencia queda corto en promedio: -2.0 % en motor, -9.4 % en edificio y -7.0 % en contenido (promedio de las ventanas 2021-22→2023 y 2022-23→2024, frente al nivel real del mercado). La dispersión por tamaño de muestra es de 3 a 6 %.
- Recomendación para 2025 desde 2023-2024: aplicar tendencia en edificio (cerca de +5 %/año) y contenido (cerca de +3.5 %/año), que es robusta a cualquier IBNR razonable; en motor, aplicar una tendencia moderada (cerca de +2 %/año) y dedicar el esfuerzo al IBNR de lesiones corporales 2024, que pesa 22 % del costo reportado y mueve el nivel proyectado ±10 % (por ejemplo, multiplicar ese IBNR por 0.5 o por 1.5), más que la propia tendencia.

## 1. Datos, verificación y revisión del código heredado

La corrida anterior de este revisor dejó `comun.py`, `build_cache.py`, `q1.py` y resultados de Q1. Antes de usarlos hice tres cosas:

1. Reconstruí la caché desde los Parquet originales con el código actual. Los 13 marcos comparados (filas, siniestros asignados y covariables) resultaron idénticos a la caché anterior.
2. Rederivé por un camino distinto (`chk_independiente.py`, con `merge_asof` y conteos acumulados) el número de siniestros por fila, el costo neto, el historial y la exposición en los seis marcos (2 mercados × 3 líneas). No hubo ni una diferencia.
3. Revisé la lógica de modelación. No encontré errores de cálculo. Sí encontré un problema de diseño en el protocolo de calibración sobre 2023 (sección 2.3), que la corrida anterior ya había empezado a tratar; lo formalicé y añadí la descomposición de la ganancia, los segmentos por historial y una evaluación ajustada por IBNR. Q2 lo escribí completo (`q2.py`).

Preparación de datos (cifras de `cache/build_info.json`):

- Se eliminaron 604 siniestros desarrollados duplicados, idénticos salvo por `claim_id` (los duplicados tienen 11 caracteres; se conserva el de 10).
- Aceptado = estado distinto de `repudiated`. Costo neto = `incurred_to_date − recoveries`.
- Asignación por `policy_id` + línea + `loss_date` dentro de [`period_start`, `period_end`]. Quedan sin fila 293 de 110 789 siniestros aceptados de motor desarrollado (0.3 %), 67 de 26 333 en edificio y 49 de 23 719 en contenido; ninguno cae en dos filas.
- Exposición recalculada como días inclusivos / 365. La columna original difería en 5 489 filas de motor desarrollado, algunas con la exposición en días (máximo 365).
- `customer_id` de motor desarrollado rellenado a 8 caracteres. Bandas de edad del desarrollado construidas desde la edad exacta. Códigos de construcción unificados (Brick/BRICK/brick, T y W como madera, BRK/STN/WOD/MIX en el emergente). Sumas aseguradas mayores a 5 M (edificio) o 2 M (contenido) divididas por 1 000 (1 395 y 1 402 filas desarrolladas).
- Ningún nivel de covariable del emergente quedó sin ver en el desarrollado después de este mapeo.

## 2. Q1: efecto del historial de siniestros

### 2.1 Método

Historial de una fila = siniestros aceptados de la misma póliza reportados en [`period_start` − 365 días, `period_start`), en tres categorías: 0, 1, 2+. Elegí la ventana de un año para que la variable signifique lo mismo en los dos mercados: en el emergente 2024 solo existe 2023 como pasado. En el desarrollado 2024, el historial "completo" abarcaría tres años y su relatividad no sería trasladable. Aparte medí qué aportan los siniestros más antiguos (sección 2.2).

Modelos, entrenados en el desarrollado 2022-2024 (2021 no tiene pasado observable; 763 960 filas en motor) con covariables comunes a ambos mercados (29 en motor, 40 en edificio, 30 en contenido; las numéricas en 8 tramos por cuantiles del desarrollado; clima del año anterior de la dirección), factor de año y log-exposición como offset:

- GLM de Poisson (glum, penalización casi nula), con y sin historial.
- LightGBM de Poisson (1 hilo, parada temprana con 10 % de clientes reservados), con y sin historial.

Transferencia: los cuatro modelos predicen las filas emergentes de 2023 y 2024. El nivel global se recalibra por línea y se evalúa sobre los conteos de 2024 con desviación de Poisson y D² (referencia: frecuencia media del segmento). La incertidumbre sale de un bootstrap por cliente (2 000 réplicas con pesos Poisson(1); se recalcula la recalibración en cada réplica, no se reentrenan los modelos).

Los conteos de 2024 están algo incompletos; los dos modelos se evalúan contra los mismos conteos. Como prueba de robustez repetí todo multiplicando cada esperado por la fracción que se espera reportada al 31-12-2024 según el patrón de reporte del desarrollado (0.936 en motor 2024, 0.950 en edificio, 0.971 en contenido).

### 2.2 Relatividades del historial

Relatividad frente a 0 siniestros, condicionada a la estructura del GLM desarrollado, con IC95 robusto por cliente. En el emergente se reestima solo el efecto del historial sobre la predicción base del modelo desarrollado (filas 2024).

| Línea | 1 siniestro, desarrollado | 1 siniestro, emergente 2024 | 2+, desarrollado | 2+, emergente 2024 |
|---|---|---|---|---|
| Motor | 1.29 (1.27 a 1.32) | 1.32 (1.21 a 1.45) | 1.78 (1.71 a 1.85) | 1.54 (1.31 a 1.80) |
| Edificio | 1.35 (1.27 a 1.43) | 1.44 (0.98 a 2.12) | 1.49 (1.15 a 1.94) | 3.7 (1.1 a 12.4), 16 filas |
| Contenido | 1.31 (1.23 a 1.41) | 1.32 (0.83 a 2.11) | 1.59 (1.18 a 2.14) | 3.5 (0.5 a 25.7), 9 filas |

Lectura:

- Motor transfiere bien para un siniestro (cociente emergente/desarrollado 1.01, IC 0.92 a 1.11, tomando renovaciones como referencia en el emergente). Para 2+ el emergente está algo por debajo (cociente 0.85, IC 0.73 a 1.00).
- En hogar hay muy pocas filas con historial en el emergente 2024 (edificio: 493 filas con 35 siniestros; contenido: 492 filas con 23 siniestros), así que los datos locales no permiten distinguir entre la relatividad desarrollada y otra distinta.
- El efecto bruto es mucho mayor que el ajustado. En renovaciones de motor emergente 2024, la frecuencia con 1 siniestro previo es 1.91 veces la de 0, y con 2+ es 3.05 veces (desarrollado 2022: 1.92 y 3.84). La mayor parte la capturan NCB, siniestros declarados y otras covariables; lo que queda es el 1.29-1.32 de la tabla.
- La relatividad desarrollada es estable en el tiempo: con solo filas de 2022, motor da 1.29 (1.25 a 1.34).
- El GBM, por dependencia parcial, da efectos algo menores: motor 1.24 y 1.41; edificio 1.25 y 1.26; contenido 1.19 y 1.20.
- Los siniestros más antiguos también informan. En el desarrollado 2023-2024, un siniestro reportado entre 1 y 3 años antes de la fila añade un factor de 1.23 en motor (1.20 a 1.26), 1.29 en edificio y 1.36 en contenido, encima del historial de 12 meses. En 2024 el emergente no puede aprovecharlo, pero en 2025 ya tendrá dos años de pasado.

### 2.3 El problema de calibrar sobre 2023

En 2023, primer año del emergente, casi ninguna fila tiene pasado observable (solo algunos cambios a mitad de año: historial medio 0.006 en motor), así que prácticamente todas entran con historial 0. El modelo con historial asigna a la categoría 0 el nivel de los asegurados sin siniestros, que está por debajo del promedio. Si la recalibración usa 2023, el factor absorbe esa diferencia; en 2024, cuando aparecen las filas con historial y se les aplica su recargo, el total previsto sube por encima del real. En motor el A/E de 2024 queda en 0.970 sin historial y 0.892 con historial. Esa diferencia de nivel penaliza al modelo con historial por un artefacto de calendario y no por su capacidad de ordenar riesgos.

Por eso reporto tres protocolos, aplicados igual a ambos modelos:

- `c2023`: nivel = A/E sobre 2023 (literal del enunciado).
- `neutral`: el modelo sin historial se calibra en 2023, y el modelo con historial se escala para que su total 2024 coincida con el del primero. Usa covariables e historial de 2024, pero no los siniestros de 2024. Es el protocolo que recomiendo para comparar.
- `oracle_seg`: nivel recalibrado dentro de cada segmento con los propios conteos 2024. Mide solo la capacidad de ordenar; sirve de referencia.

### 2.4 ¿Mejora el historial la predicción del emergente 2024?

ΔD² = D²(con historial) − D²(sin historial), ×1000, con IC95 del bootstrap por cliente (entre 14 000 y 24 000 clientes según la línea). Valores positivos favorecen al historial. Protocolo neutral.

| Línea | Modelo | D² sin → con (todas) | Todas | Renovaciones | Negocio nuevo |
|---|---|---|---|---|---|
| Motor | GLM | 0.0716 → 0.0755 | +3.85 (+1.96 a +5.82) | +3.33 (+1.21 a +5.59) | +7.79 (+3.46 a +11.79) |
| Motor | GBM | 0.0756 → 0.0785 | +2.86 (+0.89 a +4.81) | +3.03 (+0.90 a +5.21) | +1.65 (−1.07 a +4.22) |
| Edificio | GLM | 0.0401 → 0.0413 | +1.20 (−0.91 a +3.37) | +1.32 (−0.97 a +3.67) | −0.07 (−0.80 a +0.73) |
| Edificio | GBM | 0.0409 → 0.0415 | +0.57 (−2.07 a +3.21) | +0.80 (−1.99 a +3.60) | −1.94 (−11.6 a +7.5) |
| Contenido | GLM | 0.0312 → 0.0319 | +0.73 (−0.75 a +2.26) | +0.83 (−0.87 a +2.56) | +0.09 (−0.34 a +0.50) |
| Contenido | GBM | 0.0307 → 0.0307 | +0.01 (−2.14 a +2.06) | +0.34 (−1.98 a +2.65) | −2.25 (−8.2 a +3.2) |

Con el protocolo literal `c2023` ninguna línea muestra mejora significativa: motor GLM +0.79 (−2.15 a +3.77), GBM +0.75 (−1.92 a +3.31); edificio GLM +0.98 (−1.31 a +3.20); contenido GLM +0.61 (−0.97 a +2.16), GBM −0.04. La diferencia con el protocolo neutral es el artefacto de nivel de la sección 2.3. El ajuste por IBNR lo confirma: el resultado neutral apenas cambia (motor GLM +3.82, IC +1.93 a +5.79), mientras que el de `c2023` salta a +3.35 (+0.48 a +6.23) porque depende casi todo del nivel.

Cómo leer la tabla:

- En motor la ganancia es real y de tamaño moderado: alrededor de 5 % más de desviación explicada en el GLM (de 0.0716 a 0.0755) y 4 % en el GBM. Es del mismo orden que la que da el historial dentro del propio desarrollado, cuando se entrena con 2022-2023 y se evalúa en 2024 (+2.2 ×1000 en motor, +0.8 en edificio, +0.24 en contenido).
- El beneficio está donde debe estar. Sin historial, el modelo de motor subestima las renovaciones que tuvieron siniestro (A/E 1.106, IC 1.017 a 1.195) y sobreestima las que no (0.941), cuando el A/E global es 0.970 por los conteos incompletos de 2024. Con historial ambos grupos quedan a menos de 1.5 puntos del global (0.958 y 0.984). En hogar pasa lo mismo, con más ruido: el A/E de las renovaciones con historial baja de 1.43 a 1.08 en edificio y de 1.30 a 1.00 en contenido. Los IC son amplios (por ejemplo, 0.90 a 2.00 en edificio sin historial).
- La ganancia del GLM en negocio nuevo de motor (+7.79) no viene del historial: solo 16 de 3 915 filas de negocio nuevo tienen historial. Con la descomposición `oracle_seg`, el factor de historial aporta −0.02 y el resto (+7.46, IC +3.15 a +11.45) sale de que, al incluir el historial, el GLM reestima otros coeficientes (NCB, siniestros declarados) de una forma que traslada mejor. El GBM no muestra ese efecto (+1.65, no significativo).
- Respuesta a la pregunta. El historial predice frecuencia más allá de las otras covariables en las tres líneas del desarrollado, y la relatividad de motor se traslada al emergente. Incluirlo mejora la predicción del emergente 2024 en motor (renovaciones). En hogar el efecto tiene el signo esperado, pero el volumen del emergente no alcanza para demostrar una mejora: usaría la relatividad desarrollada, que es estable y precisa, en lugar de estimarla localmente.

## 3. Q2: índice de nivel y sesgo de juntar dos años sin tendencia

### 3.1 Método

Relatividades fijas. GLM de frecuencia (Poisson, offset log-exposición) y GLM de severidad (Gamma, sobre el costo neto por siniestro topado a 250 000 CU), con todas las covariables del desarrollado: las comunes más región, banda de crédito, telemetría, edad exacta y kilometraje (34 en motor, 42 en edificio, 32 en contenido). El clima entra como promedio 2021-2024 de la dirección, para que un año de tormentas cuente como nivel y no como mezcla. Ajusté con factor de año y predije con el año fijo en 2022; así las relatividades no absorben la tendencia. Como sensibilidad ajusté sin factor de año (la variante literal del enunciado): las tendencias cambian a lo sumo 0.4 puntos.

Costo esperado de cada fila = exposición × frecuencia × severidad con relatividades fijas. Índice del año = (costo reportado topado + IBNR) / costo esperado, normalizado a 2021 = 1. El exceso sobre el tope se trata como una carga estable aparte: afecta a 19 siniestros de motor (el exceso de 2023 suma 12.1 M CU, casi todo de un siniestro de lesiones de 11.9 M) y 35 de edificio; ninguno en contenido.

IBNR de 2024 (y de años anteriores). Para cada línea y peligro estimé la distribución del retraso de reporte con el estimador producto-límite para datos truncados a la derecha (Lynden-Bell): un siniestro solo se ve si su retraso no supera los días entre la ocurrencia y el 31-12-2024. Con esa curva calculé la fracción esperada reportada de cada año, suponiendo ocurrencias uniformes dentro de cada fila y ponderando por frecuencia esperada. Ultimate = reportado / fracción. Para la sensibilidad multiplico todo el IBNR por k = 0, 0.5, 1, 1.5, 2 (k = 1 es la estimación central).

| Línea | IBNR 2024 / costo reportado | Peligro que lo explica | Ultimate de ese peligro 2021, 2022, 2023, 2024 |
|---|---|---|---|
| Motor | 22.0 % (conteo 7.3 %) | Lesiones: 56 % reportado | 2 148, 2 161, 2 178, 2 101 |
| Edificio | 8.8 % (conteo 5.7 %) | Hundimiento: 67 % reportado | 282, 335, 387, 437 |
| Contenido | 2.9 % (conteo 3.0 %) | Todos los peligros entre 95 y 98 % reportado | |

Dos comprobaciones que no dependen del IBNR respaldan k ≈ 1:

- El estimador Horvitz-Thompson con las fechas reales de ocurrencia da un ultimate 2024 de costo 2.3 % menor en motor y 2.0 % mayor en edificio.
- Índices a igual madurez. Tomé solo las ocurrencias del primer semestre de cada año reportadas en 183 días, algo observable completo para los cuatro años. Resultado: motor 1.000, 1.093, 1.080, 1.136; edificio 1.000, 1.025, 1.043, 1.203; contenido 1.000, 0.923, 1.002, 1.060. El k que hace coincidir el 2024 del índice principal con este es 1.07 en motor, 1.2 en edificio y 1.35 en contenido (impreciso, porque es medio año). Con k = 0, el 2024 de motor caería a 0.900, cosa que estos datos descartan.

Tendencia: regresión log-lineal sobre los cuatro índices anuales. Doy dos medidas de incertidumbre. El error estándar residual (2 grados de libertad) recoge los choques propios de cada año. La desviación del bootstrap por póliza (1 000 réplicas) recoge solo el ruido de muestreo.

### 3.2 Índice de nivel 2021-2024 (k = 1, topado, ajustado por mezcla)

| Línea | 2021 | 2022 | 2023 | 2024 | Tendencia/año | EE residual | DE bootstrap | Frecuencia | Severidad | Sin ajuste de mezcla |
|---|---|---|---|---|---|---|---|---|---|---|
| Motor | 1.000 | 1.066 | 1.030 | 1.096 | +2.4 % | 1.4 | 0.6 | +0.6 % | +1.8 % | −1.0 % |
| Edificio | 1.000 | 1.031 | 1.093 | 1.205 | +6.2 % | 1.1 | 1.3 | +1.3 % | +4.8 % | +7.8 % |
| Contenido | 1.000 | 0.982 | 1.077 | 1.098 | +3.7 % | 1.4 | 1.2 | +0.6 % | +3.1 % | +5.0 % |

Notas:

- La mezcla importa en motor. El costo esperado por año-póliza cae 10 % entre 2021 y 2024 por el envejecimiento de la cartera: más años de NCB (−6.0 % en log) y vehículos más viejos (−4.3 %). Sin ese ajuste, la tendencia aparente de motor sería negativa.
- En hogar, la suma asegurada se indexa: +3.0 %/año en edificio y +2.0 %/año en contenido para la misma póliza. La relatividad de suma asegurada convierte eso en unos +1.8 y +1.3 puntos/año de costo esperado. Las tendencias de la tabla son netas de esa indexación; sirven si la tarifa 2025 usa la suma asegurada indexada de 2025. Si no, la tendencia bruta es cerca de +8 % y +5 %.
- Sin tope, motor da 1.000, 1.061, 1.138, 1.095 (+3.4 %/año); el pico de 2023 es el siniestro de 11.9 M. Edificio y contenido casi no cambian.
- Usando solo 2021-2023, que no dependen del IBNR de 2024: motor +1.5 %, edificio +4.4 %, contenido +3.7 %.

### 3.3 Sesgo de un asegurador con dos años y 10 % de las pólizas

Diseño: 2 000 muestras aleatorias del 10 % de los `policy_id`. Una póliza en la muestra lo está todos los años, de modo que las altas nuevas del año siguiente también entran al 10 %. Cada muestra estima el nivel del año siguiente como el A/E agrupado de sus dos años (relatividades fijas del mercado; IBNR asignado en proporción al costo esperado), con cuatro variantes:

- sin tendencia;
- tendencia del mercado completo con los años disponibles en su momento (2021→2022 para la primera ventana, solo un paso; 2021-2023 para la segunda);
- tendencia 2021-2024 del mercado (mira hacia adelante, es solo una referencia);
- tendencia estimada con los dos años propios de la muestra.

La tendencia se aplica por la distancia entre el punto medio ponderado de los dos años y el año proyectado, unos 1.5 años. El error es estimado/real − 1 frente al nivel del mercado completo el año siguiente. Frente al propio año siguiente de la muestra, el sesgo es casi igual y la dispersión crece (motor 5-6 %, edificio 9-11 %, contenido 8-9 %).

Error medio (DE entre muestras), k = 1, topado:

| Línea | Variante | 2021-22 → 2023 | 2022-23 → 2024 | Promedio | RMSE |
|---|---|---|---|---|---|
| Motor | Sin tendencia | +0.4 % (3.4) | −4.4 % (3.1) | −2.0 % | 4.5 % |
| Motor | Tendencia disponible | +10.4 % (3.7) | −2.3 % (3.2) | +4.1 % | 8.3 % |
| Motor | Tendencia 2021-24 | +4.0 % (3.5) | −0.9 % (3.2) | +1.6 % | 4.5 % |
| Motor | Tendencia propia | +10.7 % (11.7) | −8.8 % (9.2) | +1.0 % | 14.4 % |
| Edificio | Sin tendencia | −7.0 % (6.2) | −11.8 % (5.6) | −9.4 % | 11.4 % |
| Edificio | Tendencia disponible | −2.7 % (6.5) | −5.7 % (6.0) | −4.2 % | 7.7 % |
| Edificio | Tendencia 2021-24 | +1.9 % (6.8) | −3.3 % (6.2) | −0.7 % | 7.0 % |
| Edificio | Tendencia propia | −0.5 % (21.1) | −2.1 % (20.1) | −1.3 % | 20.7 % |
| Contenido | Sin tendencia | −8.0 % (4.9) | −6.0 % (5.0) | −7.0 % | 8.6 % |
| Contenido | Tendencia disponible | −10.4 % (4.8) | −0.7 % (5.2) | −5.5 % | 8.9 % |
| Contenido | Tendencia 2021-24 | −2.7 % (5.2) | −0.6 % (5.2) | −1.7 % | 5.6 % |
| Contenido | Tendencia propia | −9.0 % (14.6) | +9.4 % (18.5) | +0.2 % | 19.1 % |

Lectura:

- Juntar dos años sin tendencia subestima en hogar en las dos ventanas, entre 6 y 12 %. Es lo esperable con una tendencia de 4-6 %/año aplicada durante 1.5 años. En motor el sesgo es pequeño y cambia de signo entre ventanas.
- Una tendencia estimada con un solo paso (2021→2022) puede ser peor que no usar tendencia: en motor ese paso fue +6.4 % y en contenido −1.8 %, ambos dominados por el choque de un año. Con tres años (segunda ventana) la tendencia disponible ya ayuda en las tres líneas.
- Estimar la tendencia con los dos años propios de un asegurador del 10 % es inservible (RMSE de 14 a 21 %).
- Solo hay dos ventanas, así que el "sesgo promedio" descansa en dos realizaciones de choques anuales; la DE entre muestras mide el ruido de muestreo, no ese riesgo.

### 3.4 Sensibilidad al IBNR de 2024

| Línea | k = 0 | k = 0.5 | k = 1 | k = 1.5 | k = 2 |
|---|---|---|---|---|---|
| Motor: tendencia 2021-24 | −3.7 % | −0.5 % | +2.4 % | +5.1 % | +7.5 % |
| Motor: sesgo sin tendencia, 2022-23→2024 | +14.8 % | +4.2 % | −4.4 % | −11.6 % | −17.8 % |
| Motor: nivel 2025 proyectado (A/E agrupado 2023-24 × factor de tendencia) | 0.848 | 0.942 | 1.038 | 1.137 | 1.238 |
| Edificio: tendencia 2021-24 | +3.6 % | +4.9 % | +6.2 % | +7.4 % | +8.5 % |
| Edificio: sesgo sin tendencia, 2022-23→2024 | −4.2 % | −8.1 % | −11.8 % | −15.2 % | −18.3 % |
| Contenido: tendencia 2021-24 | +2.9 % | +3.3 % | +3.7 % | +4.2 % | +4.6 % |
| Contenido: sesgo sin tendencia, 2022-23→2024 | −3.4 % | −4.7 % | −6.0 % | −7.3 % | −8.5 % |

En motor la conclusión depende del IBNR de lesiones: con k = 0 parecería que no hay que tendenciar y que juntar dos años sobreestima; con k ≥ 1 ocurre lo contrario. La evidencia de madurez igual (k implícito 1.07) y el ultimate de lesiones 2024 (2 101, en línea con 2 148-2 178 de los años previos) sostienen k ≈ 1. En edificio y contenido la tendencia es positiva con cualquier k.

### 3.5 Recomendación para proyectar 2025 desde 2023-2024

- Edificio: aplicar tendencia, alrededor de +5 %/año (rango 4.4 % con 2021-23 a 6.2 % con 2021-24), lo que da un factor de 1.07 a 1.10 sobre el nivel agrupado 2023-24. Es la severidad la que crece (+4.8 %/año); el hundimiento ultimate sube año a año (282, 335, 387, 437).
- Contenido: aplicar tendencia, alrededor de +3.5 %/año, factor de 1.05 a 1.06. Robusto a k (rango del factor 1.044 a 1.071).
- Motor: aplicar una tendencia moderada, alrededor de +2 %/año (factor cerca de 1.03). Se apoya en la tendencia 2021-24 con k = 1 (+2.4 %, EE 1.4), en la de 2021-23 (+1.5 %), en la de severidad (+1.8 %) y en los índices a igual madurez (+2.2 a +3.7 %). La decisión que más pesa en motor es el IBNR de lesiones de 2024: entre k = 0.5 y k = 1.5 el nivel 2025 proyectado va de 0.94 a 1.14.
- En todos los casos, la tendencia debe venir del mercado completo con al menos tres años y descompuesta en frecuencia y severidad, nunca de los dos años propios.
- Si esto se traslada al emergente (dos años de experiencia, tamaño cercano al 10 % del desarrollado), lo prudente es importar la tendencia del desarrollado en lugar de estimarla localmente.

## 4. Limitaciones

- Todo está valorado al 31-12-2024. En el estudio de sesgo, la experiencia 2021-22 se usa más madura de lo que la tendría un asegurador a fines de 2022, así que el error real en tiempo real sería mayor.
- El IBNR supone un patrón de reporte estable y sin cola más allá de unos 4 años (el retraso máximo observado de lesiones es 1 361 días). No modelé el desarrollo de reservas de siniestros abiertos (IBNER): 21 % de los siniestros de motor 2024 y 25 % de los de edificio siguen abiertos, y su incurrido se toma tal cual.
- Cuatro puntos anuales dan una tendencia con EE residual de 1.1 a 1.4 puntos. Esa incertidumbre es mayor que la de muestreo (0.6 a 1.3).
- El tope de 250 000 CU trata el exceso como carga estable; el siniestro de 11.9 M de 2023 domina el índice sin tope de motor.
- Q1: el bootstrap no reentrena los modelos (la incertidumbre de estimación en el desarrollado es pequeña frente a la de evaluación en el emergente). El GBM se entrenó una sola vez con hiperparámetros fijos. Para las filas emergentes de 2023, el clima "del año anterior" es el del mismo año, porque no hay 2022. El historial cuenta siniestros reportados antes del inicio de la fila con su estado al 31-12-2024, y lo mismo vale en ambos mercados.
- Las relatividades de Q2 son de un GLM de efectos principales sin interacciones; sirven para ajustar la mezcla, no como tarifa.

## 5. Archivos

- `comun.py`, `build_cache.py`: preparación de datos (heredados, revisados, caché reconstruida).
- `chk_independiente.py`: rederivación independiente de conteos, costos, historial y exposición.
- `q1.py` (versión heredada en `q1_v0_original.py`), `q1_*.json`, `resumen_q1.py`.
- `q2.py`, `q2_*.json`, `resumen_q2.py`, `diag_q2_mix.py`, `diag_q2_mix.json`.
- `hacer_resultados.py` → `resultados.json` (incluye un bloque `headline` con las cifras principales).
- Registros: `log_build.txt`, `log_q1.txt`, `log_q2.txt`, `log_diag.txt`, `log_resultados.txt`.
