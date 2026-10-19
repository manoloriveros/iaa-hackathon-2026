# Plan de pruebas: metodologías, expuestos, IBNR, frecuencia, severidad, envíos y cronograma

Claude (Cowork), 17 de octubre de 2026, a solicitud del participante. Versión 1.0. Corrida de cálculo: `runs/bases_20261017T120251Z_45443ff0` (18 de 18 controles). Todo lo que aquí se cifra sale de esa corrida o de documentos del proyecto citados por su ruta; `cifras_plan.json` y `verificar_entrega.py` comprueban cada número contra `evidencia.json`. Nada de lo que sigue entrena un modelo, modifica datos o índices, envía predicciones ni contacta con nadie. Es un plan con su primera base de cálculo; la ejecución de cada paso sigue necesitando la autorización del participante que fija `AGENTS.md`.

## 0. De dónde partimos y qué añade esta entrega

Al cierre de D66 el proyecto tenía la capa de datos preparada y verificada (`current_dataset.json` → `preaudit_20261016T211816Z_817285a5`), la metodología actuarial 1.11, un catálogo de 22 candidatos sin ejecutar y dos investigaciones de técnicas, pero ninguno de los cinco entregables que la metodología exige antes de los pilotos estaba materializado: ni la asignación de siniestros, ni la tabla T0, ni la matriz F0, ni las particiones, ni las referencias por ramo. Esta entrega cierra dos de ellos de forma preliminar y deja los otros tres especificados al detalle para que el flujo de Preparación los reproduzca con su propia verificación.

Lo que la corrida calculó sobre la capa vigente, comprobando antes los SHA-256 de las siete tablas usadas contra el catálogo activo:

| Pieza | Resultado | Dónde está |
| --- | --- | --- |
| Asignación de siniestros a periodos | 160.432 aceptados con asignación única (110.496 autos, 26.266 edificios, 23.670 contenidos), las mismas cifras que D42 y D50 obtuvieron por otros algoritmos; cero ambiguos, cero sin póliza, cero fuera de ventana; los 413 PRE00 quedan fuera por construcción | `tables/asignacion_por_siniestro.parquet`, `asignacion_siniestros.csv` |
| Tabla T0 por `row_id` | 2.409.311 filas de entrenamiento; T0 total 741.156.868,43 CU (autos 428.762.846,58; edificios 246.656.437,27; contenidos 65.737.584,58); 146.368 filas con coste positivo (6,07 %); 10.120 expedientes abiertos asignados con 90.168.216,94 CU de reserva de caso | `tables/t0_por_row_id.parquet` (columnas T0, conteos aceptados, positivos y abiertos, pagado, incurrido, recuperaciones, reserva) |
| Expuestos | Por ramo, año, mes natural y cobertura de autos; 1.968.577,0591 años en entrenamiento (idéntico a EXP01) y 500.351,282 en el test 2025 | `expuestos_ramo_anio.csv`, `expuestos_ramo_mes.csv`, `expuestos_autos_cobertura.csv` |
| Retraso de reporte e IBNR de conteos | Chain-ladder mensual por ramo y peligro, completitud por cohorte y por mes de ocurrencia de 2024, IBNR de notificaciones, de positivos y de coste | `chain_ladder_conteos.csv`, `completitud_2024_por_mes.csv`, `factores_desarrollo_conteos.csv`, `ibnr_2024_por_peligro.csv`, `ibnr_por_peligro_anio.csv` |
| Frecuencia y severidad | Por ramo, año y peligro; dispersión de conteos; severidad con colas, abiertos y reportados tardíos | `frecuencia_ramo_anio_peligro.csv`, `frecuencia_autos_cobertura.csv`, `severidad_ramo_peligro.csv` |
| Reservas de caso y T1 | Peso de la reserva de abiertos por ramo, peligro y año; rango T1 con a = 0,75 y 1,25 | `reservas_caso_T1.csv`, `reservas_caso_ramo_anio.csv` |
| Prima de riesgo observada y última | T0/expuestos y (T0 + IBNR)/expuestos por ramo y año | `prima_riesgo_ramo_anio.csv`, `prima_riesgo_ultima_ramo_anio.csv` |
| Referencias M00 | Tasa constante por ramo (balance y Tweedie) evaluada en V22, V23 y V24 con D² de potencia 1,5 | `referencias_M00.csv` |

Dos hallazgos condicionan todo el plan y por eso van antes que las metodologías.

El primero es que la referencia más simple ya reproduce la escala del leaderboard. Una tasa constante por ramo multiplicada por la exposición, estimada con 2021–2023 y evaluada sobre 2024, da D² = 0,07094; la captura que D64 archivó muestra 0,07169 para la referencia pública de coste medio. La coincidencia no demuestra que sea el mismo cálculo, pero sí que nuestra validación V24 habla en la misma escala que la puntuación pública, y que la distancia entre esa referencia y el GLM público (0,10563) o el primer puesto (0,11416) es la que tenemos que recorrer con señal tarifaria real, no con nivel.

El segundo es que el año 2024 está incompleto de forma material y desigual por ramo. El coste observado T0 de autos cae de 587,47 CU por año expuesto en 2023 a 453,82 en 2024 (un 22,7 % menos), y al añadir el IBNR estimado por chain-ladder vuelve a 584,38 CU. Casi toda la caída es desarrollo pendiente concentrado en lesiones corporales, no una bajada real del riesgo. Como la etiqueta de 2025 que puntúa el concurso es el coste último esperado, un modelo entrenado sobre T0 sin corregir aprendería un nivel de 2024 artificialmente bajo y lo trasladaría a 2025. Esto es lo que las secciones 3 a 5 resuelven y lo que la escalera de envíos de la sección 6 contrasta primero.

## 1. Metodologías que vamos a probar, en orden

El catálogo D64 tiene 22 candidatos. No vamos a probar los 22 en seis días: el criterio de D17 (un flujo que otro actuario pueda entender, reproducir y revisar) y el peso de la rúbrica (40 % rendimiento y adaptación, 25 % uso de IA, 20 % validación y controles, 15 % documentación) aconsejan ejecutar con rigor una escalera corta y documentar por qué el resto queda fuera. La escalera, con lo que decide cada peldaño:

| Orden | Candidatos | Pregunta que responde | Etiqueta y partición | Condición de paso |
| --- | --- | --- | --- | --- |
| 0 | Entregables previos: asignación, T0, F0 con contrato de disponibilidad, particiones V22/V23/V24 persistentes, runner multitabla con D² a maximizar | Nada se mide aquí; sin esto no hay comparación válida | — | Los cinco entregables de la metodología con verificación propia y hashes |
| 1 | M00 tasa constante por ramo; M01 GLM Tweedie F0 con enlace log y offset `log(e)`; M04 LightGBM, M05 XGBoost y M06 CatBoost Tweedie con `p_fit` 1,5 y 1,9 | Cuánta señal tarifaria hay en F0 y si la potencia de ajuste importa | T0 en V23 (desarrollo, mitades de calibración y selección) y V24 (evaluación congelada); p_eval siempre 1,5 | Un boosting entra si mejora al GLM en V23-selección y V24 con tres semillas y la mejora sobrevive al retirar el 0,1 % de periodos más costosos |
| 2 | M03 frecuencia–severidad (Poisson con offset `log(e_efectiva)` y gamma por siniestro positivo) por ramo y por componente de peligro; M07 variante CatBoost; duración como efecto propio; historia F1 con contracción | Si separar frecuencia y severidad y los peligros largos mejora la estimación última y sus supuestos | T0 reportado para frecuencia con exposición efectiva; severidad madura 2021–2022 para lesiones y hundimiento | Comparación sobre las mismas filas; se conserva la estructura que mejor transfiere de V23 a V24 |
| 3 | Calibración (sin ajustar, balance, factor Tweedie `sum(Y/sqrt(m))/sum(sqrt(m))`, isotónica) y sensibilidades: T1 (a = 0,75 y 1,25 en lesiones, hundimiento, incendio e inundación), corrección de reporte de noviembre–diciembre, tendencia 2025 de 0, +3 y +5 % en hogar y 0 y +3 % en autos | Qué nivel y qué supuestos declarados lleva el candidato de 2025 | Mitad de calibración de V23; V24 solo para confirmar transferencia | Se elige el supuesto por evidencia actuarial (sección 3 y 5), no por el leaderboard |
| 4 | M02 GAM Tweedie o EBM interpretable; SHAP del candidato; ablaciones F3 (telemática, contactos excluidos) y F4 (tarifario) | Explicación para el informe y prueba de que el candidato no depende de proxies prohibidos | V24 reutilizado, registrado como tal | Solo documentación; no cambia el candidato salvo hallazgo de proxy |
| 5 | M16 mezcla convexa de los dos mejores por ramo | Si los errores son complementarios | Predicciones fuera de muestra de V23 y evaluación en V24 | Solo si la mezcla mejora en V24 y los pesos son estables entre semillas |
| Fuera del plan de la parte 1 | M08 a M15, M17 a M21 (GLMM, CANN, LocalGLMnet, DRN, TabM, ANAM, Credibility Transformer, TabPFN, zero-inflated) | Se registran como extensiones con su condición; D50 no encontró evidencia de ceros extra ni margen para redes con 2.409.311 filas y seis días | — | Reabrir en la parte 2 si el dataset nuevo lo justifica |

Tres reglas de comparación que valen para todos los peldaños, tomadas de la metodología 1.11 y de D50: la etiqueta de evaluación no cambia dentro de una comparación (un D² sobre T0 no se compara con otro sobre T1); la diferencia se mide como desviación sobre las mismas filas con remuestreo por cliente, no como dos scores sueltos; y entre resultados parecidos gana el candidato más estable y más fácil de revisar. El runner tiene que seleccionar el mejor D² como máximo, no como mínimo (hoy ordena errores de menor a mayor y tomaría el peor).

## 2. Estimación de expuestos

La exposición es el denominador de la frecuencia, el offset de los modelos de conteo y el multiplicador de la prima de riesgo: cualquier error aquí se propaga a todo. La capa vigente ya la unificó con EXP01 (días inclusivos entre `period_start` y `period_end` divididos entre 365, cuatro decimales), y la corrida lo recomprobó fila a fila en las seis tablas con una diferencia máxima de 0,000049 años (el redondeo a cuatro decimales). La suma de entrenamiento es 1.968.577,0591 años, la misma cifra que dejó EXP01.

| Ramo | Año | Filas | Años expuestos | Exposición media | Filas de año completo | Filas con menos de medio año | Nuevo negocio | Prima escrita por año expuesto (CU) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Autos | 2021 | 216.008 | 187.991,55 | 0,870 | 75,1 % | 13,2 % | 12,0 % | 618,06 |
| Autos | 2022 | 254.685 | 199.698,50 | 0,784 | 59,4 % | 22,1 % | 15,2 % | 700,86 |
| Autos | 2023 | 254.577 | 199.681,87 | 0,784 | 59,3 % | 22,0 % | 15,3 % | 724,89 |
| Autos | 2024 | 254.698 | 199.785,64 | 0,784 | 59,5 % | 22,0 % | 15,4 % | 745,51 |
| Autos | 2025 (test) | 254.986 | 199.983,60 | 0,784 | 59,3 % | 22,0 % | 15,2 % | 765,73 |
| Edificios | 2021 | 155.729 | 140.782,93 | 0,904 | 81,4 % | 9,7 % | 12,0 % | 328,40 |
| Edificios | 2022 | 183.864 | 149.872,44 | 0,815 | 64,4 % | 18,7 % | 15,3 % | 385,49 |
| Edificios | 2023 | 184.132 | 149.987,30 | 0,815 | 64,3 % | 18,7 % | 15,3 % | 404,74 |
| Edificios | 2024 | 184.001 | 149.917,52 | 0,815 | 64,5 % | 18,8 % | 15,2 % | 426,54 |
| Edificios | 2025 (test) | 184.155 | 150.243,91 | 0,816 | 64,4 % | 18,7 % | 15,1 % | 449,36 |
| Contenidos | 2021 | 158.848 | 140.931,38 | 0,887 | 78,3 % | 11,4 % | 12,0 % | 140,96 |
| Contenidos | 2022 | 187.632 | 149.986,20 | 0,799 | 61,8 % | 20,4 % | 15,4 % | 164,77 |
| Contenidos | 2023 | 187.646 | 149.974,96 | 0,799 | 61,8 % | 20,4 % | 15,3 % | 173,76 |
| Contenidos | 2024 | 187.491 | 149.966,77 | 0,800 | 62,0 % | 20,4 % | 15,2 % | 183,08 |
| Contenidos | 2025 (test) | 187.498 | 150.123,77 | 0,801 | 62,0 % | 20,3 % | 15,2 % | 192,88 |

Lo que se lee en esa tabla. El test de 2025 tiene la misma estructura de exposición que 2022–2024 en los tres ramos (misma media, misma proporción de periodos cortos, misma proporción de nuevo negocio), así que una validación que entrene hasta 2023 y evalúe 2024 imita bien la composición del año a predecir; 2021 es el año distinto (más periodos completos, menos nuevo negocio) y por eso V22 solo sirve para ajuste interno. La prima escrita por año expuesto, que es el tarifario del generador y no nuestro objetivo, sube entre 2,7 % y 3,4 % anual en autos y entre 5,0 % y 5,5 % en hogar, también de 2024 a 2025 (2,7 % y 5,4 %); es el dato más directo que tenemos sobre la inflación que el generador aplica y lo usaremos como una de las referencias para la tendencia de 2025 (sección 5), nunca como predictor sin ablación (bloque F4).

La corrida añade una vista que la metodología necesita para el reporte: la exposición por mes natural de ocurrencia, calculada como los días de cada periodo que caen en cada mes entre 365. Suma la exposición por fila con una diferencia máxima por ramo y año de 0,0196 años (el redondeo de EXP01 acumulado sobre cientos de miles de filas) y es la base de la exposición efectiva de la sección 3. En autos los doce meses de 2024 llevan entre 15.865,82 y 16.976,81 años cada uno; 2025 es casi idéntico mes a mes.

Para el modelado se fijan estas reglas, que el runner tiene que respetar por código. La predicción es siempre `m_i = e_i * q_i` con la exposición nominal de la fila de test; si el modelo lleva `log(e_i)` como offset, la salida ya está en CU del periodo y no se multiplica otra vez. En frecuencia, el offset de entrenamiento es `log(e_efectiva)` (sección 3) y el de predicción `log(e_nominal)`. Los modelos de tasa que no admiten offset (CatBoost, y LightGBM o XGBoost sin `init_score`) ajustan `Y/e` con peso `e**(2 - p_fit)` (raíz de `e` con 1,5). La exposición no se recorta a 1 ni se redondea; el año bisiesto completo vale 1,0027. Una columna `exposure` de test igual a cero sería un error de flujo que detiene la corrida, no un caso que resuelva el piso numérico. Y la duración entra además como efecto propio candidato (indicador de periodo corto y `renewal_count`), porque el 22 % de los periodos de autos duran menos de medio año y D37 dejó abierta la pregunta de si el riesgo por día de un periodo corto es igual al de uno completo.

## 3. El ejercicio de IBNR y la madurez de 2024

### 3.1 Qué podemos y qué no podemos estimar

El archivo tiene una sola valoración al 30 de diciembre de 2024 (última fecha de reporte observada, comprobada en la corrida) sin trayectorias de pago ni de reserva. Con eso no se puede construir un triángulo de pagos ni estimar factores de desarrollo financiero: no sabemos cuánto valía un expediente cerrado cuando estaba abierto. Lo que sí se observa completo es la fecha de ocurrencia y la de reporte de cada notificación, y eso permite estimar con rigor el IBNR puro (siniestros ocurridos y aún no reportados al corte) con un chain-ladder de conteos. La parte de desarrollo de los reportados abiertos (IBNER) no se estima: se acota con la sensibilidad T1 de la metodología.

### 3.2 Método

Para cada ramo y peligro se construyó el triángulo acumulado de notificaciones por cohorte mensual de ocurrencia (48 cohortes, enero de 2021 a diciembre de 2024) y lag mensual de reporte (0 a 47 meses), con todas las notificaciones asignadas a un periodo, aceptadas o rechazadas, porque la rechazada también se reporta y la probabilidad de coste positivo se aplica después. Los factores de desarrollo son cocientes de sumas (ponderados por volumen) entre cohortes que tienen ambos lags observados; el factor a último de una edad es el producto de los factores posteriores. Para los dos peligros de cola larga, lesiones corporales de autos y hundimiento de edificios, se ajustó una cola exponencial sobre los factores de los lags 12 a 46 (`log(f_k - 1)` lineal en `k`, extrapolada 120 meses): la cola resulta 1,0013 en lesiones y 1,0020 en hundimiento, pequeña, porque a cuatro años el archivo ya ve casi todo. En los demás peligros la cola es 1.

El resultado por peligro, con las cohortes anuales:

| Ramo y peligro | Notificaciones 2021–2024 | Factor a último, edad 0 (ocurrido en diciembre) | Factor a último, edad 11 | Completitud 2021 | Completitud 2023 | Reportados 2024 | Completitud 2024 | IBNR de notificaciones 2024 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Autos, lesiones corporales | 7.512 | 13,21 | 1,181 | 0,9966 | 0,9389 | 1.178 | 0,5639 | 911,1 |
| Autos, daños a terceros | 33.630 | 2,114 | 1,004 | 1,0000 | 0,9985 | 7.774 | 0,9418 | 480,3 |
| Autos, daños propios | 48.656 | 1,496 | 1,003 | 1,0000 | 0,9989 | 11.620 | 0,9666 | 401,3 |
| Autos, cristales y granizo | 15.643 | 1,334 | 1,006 | 1,0000 | 0,9981 | 4.020 | 0,9723 | 114,6 |
| Autos, robo | 6.458 | 1,230 | 1,004 | 1,0000 | 0,9989 | 1.579 | 0,9806 | 31,2 |
| Edificios, hundimiento | 1.288 | 9,578 | 1,070 | 0,9980 | 0,9792 | 291 | 0,6210 | 177,6 |
| Edificios, escape de agua | 10.065 | 1,788 | 1,004 | 1,0000 | 0,9985 | 2.558 | 0,9313 | 188,8 |
| Edificios, tormenta | 7.762 | 1,524 | 1,005 | 1,0000 | 0,9978 | 1.894 | 0,9502 | 99,3 |
| Edificios, daño accidental | 3.825 | 1,496 | 1,003 | 1,0000 | 0,9989 | 989 | 0,9698 | 30,8 |
| Edificios, inundación | 2.219 | 1,525 | 1,004 | 1,0000 | 0,9989 | 530 | 0,9784 | 11,7 |
| Edificios, incendio | 1.107 | 1,243 | 1,003 | 1,0000 | 0,9992 | 309 | 0,9782 | 6,9 |
| Contenidos, daño accidental | 9.167 | 1,505 | 1,005 | 1,0000 | 0,9986 | 2.327 | 0,9652 | 84,0 |
| Contenidos, escape de agua | 5.366 | 1,809 | 1,005 | 1,0000 | 0,9983 | 1.362 | 0,9437 | 81,2 |
| Contenidos, robo | 7.820 | 1,220 | 1,004 | 1,0000 | 0,9990 | 2.025 | 0,9796 | 42,1 |
| Contenidos, inundación | 1.615 | 1,500 | 1,009 | 1,0000 | 0,9970 | 361 | 0,9622 | 14,2 |

La lectura es la que D50 anticipó con cifras descriptivas, ahora con un estimador: en trece de los quince peligros el reporte es corto (entre el 98,0 % y el 99,7 % de la cohorte 2021 se reportó en 90 días; p90 del retraso entre 10 y 49 días) y el IBNR de 2024 se concentra en las ocurrencias de noviembre y diciembre, con completitudes de 2024 entre 0,93 y 0,98. En lesiones corporales (p90 de 421 días en 2021; 38 % reportado en 90 días) y hundimiento (p90 de 254 días; 51 % en 90 días) falta casi la mitad de las notificaciones de 2024 y todavía un 6 % y un 2 % de las de 2023. La completitud por mes de ocurrencia de 2024, que es la que usa la exposición efectiva, va en daños propios de 0,9966 (enero) a 0,6684 (diciembre), en lesiones de 0,8465 a 0,0757 y en hundimiento de 0,9350 a 0,1044.

### 3.3 De notificaciones a coste

El IBNR de notificaciones se convierte en positivos multiplicando por la probabilidad de coste positivo por notificación del peligro (entre 0,9475 en robo de autos y 1 en los peligros de hogar sin rechazos) y en coste multiplicando por la severidad media de las cohortes maduras 2021–2022; en lesiones y hundimiento se usa la media de los reportados a más de 365 días (25.773,73 y 18.691,06 CU) porque el coste de los tardíos difiere del resto. Es una hipótesis declarada, no un hecho: los no reportados de los peligros cortos cuestan como la media (D50 comprobó que la media no depende del retraso en esos peligros) y los de lesiones cuestan como los tardíos observados.

| Ramo | T0 2024 (CU) | IBNR de positivos 2024 | IBNR de coste 2024 (CU) | Factor de coste (T0 + IBNR)/T0 | Factor de conteo |
| --- | ---: | ---: | ---: | ---: | ---: |
| Autos | 90.666.976,89 | 1.924,1 | 26.083.030,24 | 1,2877 | 1,0744 |
| Edificios | 67.353.949,55 | 515,1 | 5.359.944,48 | 1,0796 | 1,0784 |
| Contenidos | 17.516.035,05 | 219,5 | 555.438,59 | 1,0317 | 1,0367 |

En autos el 90 % del IBNR de coste son lesiones (23.482.445,40 de 26.083.030,24 CU) y el factor de coste del peligro es 2,1181. En edificios, hundimiento aporta 3.319.532,26 CU con factor 1,4205 y escape de agua 987.040,74 con 1,0595. Con la misma regla aplicada a 2021–2023 el efecto es pequeño: factores de coste de 1,0018, 1,0053 y 1,0300 en autos, 1,0002, 1,0002 y 1,0033 en edificios, 1,0000, 1,0000 y 1,0016 en contenidos.

### 3.4 Reservas de caso y rango T1

El otro componente del desarrollo pendiente es la reserva de caso de los abiertos, que T0 incluye y que puede moverse en cualquier sentido. Su peso crece con la inmadurez: la reserva de abiertos es el 29,25 % del T0 de autos en 2024 (20,70 % en 2023, 4,23 % en 2021), el 28,11 % en edificios (5,60 % en 2023) y el 14,14 % en contenidos (0,97 % en 2023). El rango T1 de la metodología, a = 0,75 y 1,25 sobre esa reserva, mueve el T0 de 2024 en ±7,31 % en autos, ±7,03 % en edificios y ±3,54 % en contenidos, y menos del 2 % en 2021–2022. Es una perturbación de diseño; no se elegirá el valor de a que mejor puntúe.

### 3.5 La prima de riesgo última y lo que significa para 2025

Juntando T0, IBNR y la reserva, la prima de riesgo por año expuesto queda así:

| Ramo | Año | T0 (CU/año) | T0 + IBNR (CU/año) | Factor | Con T1 a = 0,75 e IBNR | Con T1 a = 1,25 e IBNR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Autos | 2021 | 563,31 | 564,31 | 1,0018 | 558,35 | 570,27 |
| Autos | 2022 | 575,32 | 578,38 | 1,0053 | 567,84 | 588,92 |
| Autos | 2023 | 587,47 | 605,11 | 1,0300 | 574,71 | 635,51 |
| Autos | 2024 | 453,82 | 584,38 | 1,2877 | 551,19 | 617,56 |
| Edificios | 2021 | 383,94 | 384,02 | 1,0002 | 383,64 | 384,41 |
| Edificios | 2022 | 403,12 | 403,22 | 1,0002 | 401,48 | 404,97 |
| Edificios | 2023 | 432,25 | 433,68 | 1,0033 | 427,63 | 439,73 |
| Edificios | 2024 | 449,27 | 485,03 | 1,0796 | 453,46 | 516,59 |
| Contenidos | 2021 | 105,45 | 105,45 | 1,0000 | 105,45 | 105,45 |
| Contenidos | 2022 | 105,48 | 105,48 | 1,0000 | 105,48 | 105,48 |
| Contenidos | 2023 | 116,95 | 117,13 | 1,0016 | 116,85 | 117,42 |
| Contenidos | 2024 | 116,80 | 120,50 | 1,0317 | 116,37 | 124,63 |

Con el IBNR, autos queda plano entre 2022 y 2024 (578, 605, 584), coherente con la caída de frecuencia de alrededor del 5 % que D50 midió al controlar el truncamiento y con una severidad que no sube; hogar crece entre 2021 y 2024 (edificios 384 → 485, contenidos 105 → 121), mezcla de severidad al alza (sección 5) y de reservas de 2024 que todavía pueden moverse. La tasa constante por ramo que M00 estimaría con T0 de 2021–2024 es 544,70, 417,67 y 111,26 CU; con el IBNR de los cuatro años pasa a unos 583, 427 y 112 CU. Una diferencia del 7 % en autos es material para una métrica de desviación.

### 3.6 Reglas operativas que salen de aquí

Para frecuencia, cada fila de entrenamiento lleva una exposición efectiva por peligro: `e_efectiva,ik = suma sobre meses m de (días de la fila i en m / 365) * c_k(m)`, donde `c_k(m)` es la completitud del peligro `k` para una ocurrencia en el mes `m` valorada al 30-12-2024 (la inversa del factor a último de la edad en meses entre `m` y diciembre de 2024; `factores_desarrollo_conteos.csv` tiene el factor por lag y `completitud_2024_por_mes.csv` los doce meses de 2024). Para una fila de 2021 la completitud es prácticamente 1; para una de diciembre de 2024 en daños propios es 0,6684 y en lesiones 0,0757. El conteo reportado se modela con offset `log(e_efectiva)` y la predicción de 2025 usa la exposición nominal. En agregado, la frecuencia positiva de 2024 por exposición efectiva queda en 0,05964 en daños propios (reportada 0,05775), 0,04058 en daños a terceros (0,03817) y 0,01047 en lesiones (0,00590).

Para el coste directo (Tweedie sobre T0), la ruta equivalente es un offset `log(e_efectiva,ramo)` con una completitud ponderada por la participación de cada peligro en el coste del ramo; la alternativa de escalar las etiquetas por un factor de ramo y año (la tabla anterior) se conserva solo como sensibilidad, porque inflar el coste de las filas con siniestro reportado confunde severidad con frecuencia. No se corrige a la vez exposición y coste por el mismo efecto.

Para la evaluación, V24 se puntúa siempre con T0 tal cual (es lo observable) y se acompaña de la descomposición por componente: un candidato que gana en V24 porque predice bajo en lesiones no ha aprendido nada útil para 2025. La comparación de niveles de 2025 entre candidatos se hace con el factor de IBNR declarado, no con V24.

Los límites que hay que escribir en el informe: el chain-ladder supone estabilidad del patrón de reporte entre cohortes (D50 lo comprobó para los peligros cortos y aquí los factores a último a edad 11 son 1,003–1,009 en todos ellos); la cola de lesiones y hundimiento es una extrapolación con 27 y 10 puntos; el coste de los no reportados es una hipótesis; las reservas de caso no se desarrollan; y nada de esto confirma cómo valoró el organizador la etiqueta de 2025.

## 4. Estimación de frecuencia

### 4.1 Lo que muestran los datos

La frecuencia se define como siniestros aceptados con coste neto positivo por año expuesto; con un solo aceptado de coste cero en todo el archivo, coincide en la práctica con la de aceptados.

| Ramo | 2021 | 2022 | 2023 | 2024 reportada | 2024 por exposición efectiva (sección 3) | Dispersión varianza/media de los conteos | Periodos sin coste |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Autos | 0,14551 | 0,14666 | 0,14017 | 0,12946 | ≈ 0,139 (suma por peligro) | 1,13–1,16 | 88,9–90,9 % |
| Edificios | 0,04400 | 0,04459 | 0,04545 | 0,04383 | ≈ 0,047 | 1,03–1,04 | 96,2–96,6 % |
| Contenidos | 0,03961 | 0,03962 | 0,04106 | 0,03993 | ≈ 0,041 | 1,03 | 96,6–96,9 % |

La dispersión de Pearson de los conteos con una sola tasa por ramo está entre 1,03 y 1,16: una Poisson con exposición, una vez entren las covariables, no deja margen para binomial negativa ni para un componente de ceros extra; eso confirma la decisión de D50 de no priorizar M21 y de tomar Poisson como modelo de conteo. En autos la cobertura cambia la frecuencia de forma estructural: en 2023, 0,15618 en `comprehensive`, 0,07224 en `third_party_fire_theft` y 0,06414 en `third_party_only`, y el cruce cobertura–peligro tiene ceros exactos (no hay cristales ni robo en terceros), así que la cobertura entra como estructura contractual con matriz de elegibilidad por peligro, no como una categoría más.

### 4.2 Especificación

La frecuencia se estima por ramo y, en la segunda ola, por componente de peligro, con esta receta común: conteo de positivos del periodo como respuesta, Poisson con enlace log, offset `log(e_efectiva)` en entrenamiento y `log(e_nominal)` en predicción, y predictores del bloque F0 (sección 1 de la metodología) más, cuando se midan por separado, F1 (historia propia conocida al inicio: D50 encontró que multiplica la frecuencia por 1,5–2,7) y F2 (clima de años anteriores: inundación 5,21 veces entre deciles extremos). `customer_service_contacts` queda fuera por contrato: mide el siniestro del propio periodo y cambia de distribución en el test. `renewal_decision` y las columnas `audit_*` las rechaza ya el guard 1.0.

Qué se compara en frecuencia: GLM Poisson frente a boosting Poisson (`HistGradientBoostingRegressor` con pérdida Poisson, LightGBM o CatBoost con el mismo offset) sobre las mismas particiones; una tasa por ramo frente a cinco componentes en autos, seis en edificios y cuatro en contenidos; con y sin exposición efectiva (la diferencia debería concentrarse en lesiones y en los periodos de fin de año). La tendencia de autos (0,146 en 2022 frente a 0,140 y 0,139 corregida en 2023–2024) se trata con un efecto de año en entrenamiento y una extrapolación declarada a 2025 (nivel de 2023–2024), nunca con una recta sobre cuatro puntos.

## 5. Estimación de severidad

### 5.1 Lo que muestran los datos

Severidad neta de los aceptados positivos asignados, ocurrencia 2021–2024:

| Ramo y peligro | Positivos | Media (CU) | Mediana | CV | p99 | Máximo | Abiertos | Reserva/incurrido | Coste del 1 % mayor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Autos, lesiones corporales | 7.512 | 21.592,51 | 11.529,81 | 6,526 | 134.481,18 | 11.894.276,93 | 38,2 % | 31,5 % | 18,4 % |
| Autos, daños propios | 48.258 | 1.856,74 | 970,39 | 1,299 | 11.227,88 | 62.697,30 | 4,1 % | 3,6 % | 7,8 % |
| Autos, daños a terceros | 32.963 | 3.682,62 | 2.551,54 | 1,009 | 17.160,25 | 44.546,09 | 6,4 % | 5,6 % | 5,8 % |
| Autos, robo | 6.119 | 6.301,43 | 4.292,68 | 1,064 | 31.298,12 | 74.682,02 | 4,0 % | 3,5 % | 6,5 % |
| Autos, cristales y granizo | 15.643 | 1.087,28 | 746,21 | 1,016 | 5.085,76 | 9.736,01 | 1,5 % | 1,2 % | 5,8 % |
| Edificios, incendio | 1.107 | 51.773,11 | 28.604,44 | 1,313 | 315.594,43 | 631.246,21 | 13,5 % | 7,9 % | 8,3 % |
| Edificios, inundación | 2.219 | 31.314,03 | 20.715,53 | 1,110 | 162.149,89 | 352.282,02 | 10,6 % | 9,4 % | 7,3 % |
| Edificios, hundimiento | 1.288 | 23.828,62 | 16.622,40 | 1,038 | 115.357,97 | 207.874,89 | 30,2 % | 25,3 % | 6,1 % |
| Edificios, escape de agua | 10.065 | 5.732,16 | 3.742,98 | 1,090 | 29.625,26 | 66.585,00 | 6,9 % | 6,6 % | 6,6 % |
| Edificios, tormenta | 7.762 | 3.455,06 | 2.302,72 | 1,059 | 16.406,47 | 41.282,92 | 4,5 % | 4,1 % | 6,3 % |
| Edificios, daño accidental | 3.825 | 1.216,76 | 840,93 | 1,018 | 5.693,45 | 11.003,06 | 1,9 % | 1,9 % | 5,9 % |
| Contenidos, inundación | 1.615 | 9.978,75 | 6.242,36 | 1,107 | 47.548,56 | 111.900,00 | 8,0 % | 7,2 % | 7,0 % |
| Contenidos, robo | 7.626 | 3.650,62 | 2.334,05 | 1,143 | 19.610,62 | 72.188,96 | 3,3 % | 2,9 % | 6,9 % |
| Contenidos, escape de agua | 5.366 | 2.738,53 | 1.729,91 | 1,131 | 14.734,04 | 35.553,42 | 4,3 % | 3,7 % | 6,8 % |
| Contenidos, daño accidental | 9.063 | 782,00 | 512,42 | 1,089 | 4.470,63 | 9.851,13 | 2,1 % | 1,9 % | 6,5 % |

Catorce de los quince peligros tienen coeficiente de variación entre 1,0 y 1,3, con el 1 % mayor aportando entre el 5,8 % y el 8,3 % del coste: una gamma con enlace log por peligro es una descripción adecuada y la potencia Tweedie implícita queda cerca de 1,5–1,6, como D50 ya midió. Lesiones corporales es otro mundo: CV 6,5, un siniestro de 11.894.276,93 CU, el 1 % mayor concentra el 18,4 % del coste y el 38 % de los expedientes siguen abiertos con la reserva como 31,5 % del incurrido. Mezclar lesiones con el resto en un único Tweedie por ramo es lo que empuja la potencia implícita de autos hacia 2 (D50: 1,99) y lo que justifica tratarlas como componente propio.

Sobre la tendencia, lo menos contaminado por madurez es la media de cerrados de las cohortes 2021–2023, y no cuenta una sola historia: en edificios la inundación sube (28.377 → 29.247 → 32.528 CU) y el incendio no (54.415 → 51.449 → 51.097), mientras que las medianas de cerrados de escape de agua, tormenta y de los peligros de contenidos suben entre 2 % y 5 % anual según D50; en autos la media de cerrados de 2024 baja por selección de madurez (los cerrados recientes son los pequeños), no porque bajen los costes. Con la prima escrita del generador subiendo alrededor del 5,4 % anual en hogar y entre 2,7 % y 3,4 % en autos, los escenarios de tendencia para 2025 se fijan en 0, +3 y +5 % en hogar y 0 y +3 % en autos, aplicados sobre el nivel último de 2023–2024.

### 5.2 Especificación

Por siniestro positivo, gamma con enlace log, un modelo por ramo con el peligro como factor y, en la segunda ola, un modelo por componente; predictores F0 del riesgo más el peligro; se ajusta sobre las cohortes 2021–2023 completas y 2024 como sensibilidad, porque en 2024 la mezcla abiertos/cerrados y los no reportados sesgan la media de lesiones y hundimiento hacia abajo (lesiones 2024: media 17.829 frente a 21.451–23.308 en 2021–2023). Para lesiones se prueba además un splicing: gamma hasta un umbral alto (p99, 134.481 CU) y, por encima, la media empírica de la cola de 2021–2023 con contracción; una red o un modelo de cola independiente no tienen soporte con 7.512 siniestros y seis días. El producto `e * lambda * s` se compara con el Tweedie directo sobre las mismas filas, y la esperanza se calcula en CU (si se modela `log(S)`, se corrige la retransformación; `exp(E[log S])` no es `E[S]`).

En hogar, la severidad de incendio e inundación se prueba también como fracción del capital asegurado (`sum_insured` bajo el contrato de F0 de D66: división por mil sobre el umbral del ramo, con las marcas `audit_capital_scale_*` fuera de los predictores), porque el capital acota el coste y su efecto debería ser monótono en esos dos peligros.

## 6. Coordinación de las pruebas y de los cinco envíos diarios

### 6.1 Reglas del juego

Kaggle cuenta los envíos por día UTC: el contador se reinicia a las 19:00 de Bogotá. La parte 1 cierra el 23 de octubre a las 11:00 de Bogotá (16:00 UTC), así que quedan siete días de envío: el 17 (hasta las 19:00), el 18, 19, 20, 21 y 22 completos, y el 23 desde las 19:00 del 22 hasta las 11:00. Son 35 huecos como máximo; D29 fija cinco diarios como tope provisional sin obligación de agotarlos y exige una hipótesis por envío con registro de hipótesis, cambios, versión de código y de datos, parámetros, esquema de validación, archivo exacto, score local y público. Ningún envío sale sin la autorización expresa del participante en la conversación; este plan solo ordena qué contrastaría cada uno.

El principio para no desperdiciar huecos: la validación local decide la estructura del modelo (qué variables, qué familia, qué componentes) y el leaderboard público solo se usa para lo que la validación local no puede ver, que es el nivel de la etiqueta de 2025 y la transferencia de 2024 a 2025. Con la escalera de abajo cada envío contrasta una sola cosa contra el anterior, y la selección final (una predicción por parte) sigue D29: validación local, evidencia actuarial y evaluación pública juntas.

### 6.2 Escalera de envíos propuesta

| ID | Día (Bogotá) | Candidato | Hipótesis que contrasta | Qué decide | Depende de |
| --- | --- | --- | --- | --- | --- |
| S01 | 17 oct | M00 tasa por ramo × exposición, T0 2021–2024 (544,70; 417,67; 111,26 CU) | La escala local y pública coinciden (esperado ≈ 0,07) | Si el archivo y la métrica están bien; calibra la lectura del leaderboard | Archivo generado desde `t0_por_row_id.parquet` y el test; comprobación de 626.639 filas y predicciones positivas |
| S02 | 17 oct | M00 con nivel último (T0 + IBNR de 2021–2024) | La etiqueta de 2025 está a nivel último, no reportado | Si S02 > S01, los modelos deben predecir a nivel último; si no, hay que revisar la hipótesis de IBNR | S01 |
| S03 | 18 oct | M01 GLM Tweedie F0, p_fit 1,5, nivel último, sin calibrar | Hay señal tarifaria en F0 (esperado por encima de 0,10, como el GLM público) | Referencia de todas las comparaciones siguientes | Entregables 0 completos; V23 y V24 locales registrados |
| S04 | 18 oct | Mejor boosting Tweedie de la ola 1 (M04, M05 o M06 según V24) | Las interacciones mejoran al GLM | Si el boosting entra como base | S03 |
| S05 | 18 oct | El mismo boosting con p_fit 1,9 | La potencia de ajuste importa en el test | Potencia de la ola 2 | S04 |
| S06 | 19 oct | Frecuencia–severidad M03 por ramo (Poisson con exposición efectiva + gamma) | La descomposición iguala o supera al Tweedie directo | Estructura de la ola 2 | V24 local de M03 |
| S07 | 19 oct | Componentes por peligro (lesiones y hundimiento separados) | Separar los peligros largos mejora | Tratamiento de lesiones | S06 |
| S08 | 19 oct | Mejor estructura + bloque F1 (historia propia) | La historia aporta en 2025 | Inclusión de F1 | S07 |
| S09 | 19 oct | Mejor estructura + F1 + F2 (clima rezagado) | El clima aporta | Inclusión de F2 | S08 |
| S10 | 20 oct | Mejor candidato con calibración por factor Tweedie en la mitad de calibración de V23 | La calibración transfiere | Política de calibración | S09 |
| S11 | 20 oct | El mismo con isotónica | La isotónica supera al factor | Política de calibración | S10 |
| S12 | 20 oct | Tendencia 2025: hogar +3 %, autos 0 % | El nivel de 2025 lleva tendencia | Escenario de tendencia | S10 u S11 |
| S13 | 20 oct | Tendencia 2025: hogar +5 %, autos +3 % | Idem, escenario alto | Escenario de tendencia | S12 |
| S14 | 21 oct | Sensibilidad T1 a = 1,25 en lesiones, hundimiento, incendio e inundación | El nivel de reservas de 2024 está subestimado | Escenario de reservas | S12 o S13 |
| S15 | 21 oct | Sensibilidad T1 a = 0,75 | Idem, sobrestimado | Escenario de reservas | S14 |
| S16 | 21 oct | Candidato con tres semillas promediadas | Reducir varianza mejora | Semillas en producción | Mejor hasta aquí |
| S17 | 22 oct | Mezcla convexa de los dos mejores por ramo (M16) con pesos de V23 | Los errores son complementarios | Si la mezcla es el candidato | S16 |
| S18 | 22 oct | Candidato final reconstruido desde cero (snapshot limpio) | La reconstrucción reproduce el archivo (hash igual) | Reproducibilidad para el jurado | S17 |
| S19–S20 | 22–23 oct | Reserva para corregir un fallo o repetir el mejor con una hipótesis nueva | — | Selección final antes de las 11:00 del 23 | — |

Los huecos no usados cada día no se rellenan por rellenar. Si un peldaño local no pasa su condición (sección 1), su envío se cae y el siguiente se adelanta. Cada archivo se guarda con su hash en la corrida del runner y en el registro por candidato; dos archivos idénticos no se envían dos veces.

### 6.3 Qué debe quedar registrado por envío

Para la rúbrica (25 % uso de IA, 20 % validación y controles) cada envío necesita, además del registro de D29, la conversación o el script de IA que lo produjo con su prompt completo (P04 sigue pendiente: el registro de producción de conversaciones está vacío), el `split_id` y la versión del objetivo usados, el D² local en V23-selección y V24 con su descomposición por ramo, y la comprobación de que el archivo cubre las 626.639 filas con predicciones finitas y positivas (el piso de `1e-8 CU/año * exposición` solo como protección de dominio).

## 7. Tareas pendientes

Ordenadas por dependencia; el responsable es quien el participante decida, Codex o Claude, siempre con su autorización. Las que ya tienen número P en `ESTADO_PROYECTO.json` lo conservan.

| N.º | Tarea | Estado | Bloquea a |
| --- | --- | --- | --- |
| T01 | Adoptar o reproducir en el flujo de Preparación la asignación y la tabla T0 de esta corrida (entregables 1 y 2 de la metodología), con sus hashes | Preliminar en `tables/` | T03, T05 |
| T02 | Construir la matriz F0 con contrato de disponibilidad por código: exclusión de `customer_service_contacts` en el guard (D50), contrato de capital de D66 (`sum_insured/1000` sobre el umbral, marcas `audit_capital_scale_*`), armonización t/w si entra `construction_type` (CON01 o equivalente), edad AGE01, exposición nominal y efectiva por peligro | Pendiente; el guard 1.0 ya excluye `renewal_decision` y `audit_*` | T05 |
| T03 | Particiones persistentes V22/V23/V24 con `split_id`, rol, corte, valoración, versión del objetivo y hash de cliente `cal_v1` | Pendiente | T05 |
| T04 | Adaptar el runner: lectura Parquet multitabla, métrica D² Tweedie 1,5 con selección a maximizar, offset de exposición, pesos `e**(2 - p_fit)`, registro de OOF y hash del archivo de envío | Pendiente (hoy es plantilla de regresión con RMSLE) | T05 |
| T05 | Ola 1 local: M00, M01, M04–M06 con p_fit 1,5 y 1,9 en V23 y V24 | Pendiente | S03–S05 |
| T06 | Ola 2 local: M03 por ramo y por peligro, exposición efectiva, F1 y F2 | Pendiente | S06–S09 |
| T07 | Ola 3 local: calibración, T1, tendencia, corrección de noviembre–diciembre, semillas | Pendiente | S10–S16 |
| T08 | Interpretación: GAM o EBM, SHAP, ablaciones F3 y F4 | Pendiente | Informe |
| T09 | Mezcla convexa y reconstrucción limpia del candidato | Pendiente | S17–S18 |
| T10 | Repositorio con control de versiones (la rúbrica lo exige; el espacio aún no es Git) con `.gitignore` que excluya datos y corridas | Pendiente | Entrega final |
| T11 | P04: proveedor de IA permitido y registro de conversaciones reales con revisión humana | Pendiente | 25 % de la rúbrica |
| T12 | P03: prueba del notebook en Kaggle alojado y conservación de artefactos | Pendiente | Entrega final |
| T13 | P01: elegibilidad al premio (consulta redactada, sin enviar) | Pendiente | Premio, no la participación |
| T14 | Aplicar en la rama CAP07R a CAP13R (D66) por el flujo apply/verify/finalize y repetir `Validacion_ajustes_claude` | Autorizado por D66, sin aplicar; F0 ya da la misma matriz leyendo la base | Auditoría, no el modelo |
| T15 | Cerrar o documentar los controles VD abiertos: VD09, VD10, VD11, VD34, VD35, NCB mayor que licencia, CAL00 | Sin cambios de datos previstos | Informe |
| T16 | Informe de cinco páginas y video de cinco minutos: estructura desde ahora (objetivo, datos, IBNR, modelos, validación, uso de IA, límites) | Pendiente | Entrega final tras la parte 2 |
| T17 | Diseño de adaptación a la parte 2: qué partes del flujo son genéricas (lector por catálogo, guard, asignación, chain-ladder, particiones) y qué hay que reconfigurar | Pendiente | 24–30 de octubre |
| T18 | Actualizar `METODOLOGIA_ACTUARIAL.md` a 1.12 con las reglas de las secciones 2 a 5 (exposición efectiva, IBNR, componentes, tendencia) | Pendiente | T05 |

## 8. Cronograma de pruebas

Fechas de Bogotá; el reinicio de envíos es a las 19:00. Sin límite propio de horas (D02), pero cada bloque termina con evidencia fechada y la memoria actualizada.

| Día | Bloque de datos y flujo | Bloque de pruebas locales | Envíos | Documentación |
| --- | --- | --- | --- | --- |
| Sáb 17 | T01 (adoptar asignación y T0), T02 (F0 con guard y contrato de capital), T03 (particiones), T04 (runner) | M00 en V22/V23/V24 ya calculado; comprobar el archivo de envío de M00 | S01, S02 (si el participante los autoriza) | D67 registrada; metodología 1.12 en borrador |
| Dom 18 | Cierre de T04; exposición efectiva por fila | Ola 1: M01, M04–M06, p_fit 1,5 y 1,9; tres semillas en boosting | S03–S05 | Registro por candidato; conversaciones de IA en producción (T11) |
| Lun 19 | Componentes por peligro; bloques F1 y F2 | Ola 2: M03 por ramo y por peligro; exposición efectiva frente a nominal; F1; F2 | S06–S09 | Tablas de comparación en V23 y V24 |
| Mar 20 | Calibradores; escenarios de tendencia | Ola 3: balance, factor Tweedie, isotónica; tendencia 0/+3/+5 | S10–S13 | Decisión de calibración y tendencia con su motivo |
| Mié 21 | T1; corrección de noviembre–diciembre; semillas | Sensibilidades T1; estabilidad por semilla; remuestreo por cliente | S14–S16 | Candidato preliminar congelado; abrir V24 queda registrado |
| Jue 22 | Mezcla; reconstrucción limpia desde snapshot (T09); repositorio Git (T10) | M16; ablaciones F3 y F4; SHAP o EBM (T08) | S17–S18 y, desde las 19:00, S19 si hace falta | Borrador del informe (T16) |
| Vie 23 (hasta 11:00) | Nada nuevo en datos | Comprobación final del archivo elegido | Selección de la predicción final; S20 solo para corregir un fallo | Cierre de la parte 1 en memoria, estado y decisiones |
| 24–30 oct | Parte 2: lector por catálogo sobre el dataset nuevo, auditoría de calidad abreviada con los mismos controles, asignación y chain-ladder si hay siniestros, reconfiguración de F0 | Repetir la escalera reducida (M00, M01, mejor boosting, M03, calibración) | Según las reglas de la parte 2 | Informe de cinco páginas, video, código versionado |

Los webinars ASTIN del 22 y 27 de octubre (07:00–08:00 de Bogotá) siguen anotados; no hay recordatorios creados.

## 9. Procedencia, verificación y límites

La corrida `runs/bases_20261017T120251Z_45443ff0` se ejecutó en la máquina virtual local del participante con Python 3.10.12, pandas 2.3.3 y pyarrow 25.0.1, leyendo las tablas que señala `current_dataset.json` (catálogo con SHA-256 `77daf0cf5a19…`, siete tablas comprobadas) sin copiar datos fuera del espacio de trabajo. Dejó `evidencia.json`, 21 tablas (19 CSV y dos Parquet), copia del script y `manifest.json` con el hash de cada archivo. Los 18 controles pasaron: hashes del catálogo, EXP01 recomprobado, 626.639 filas de test únicas, corte del 30-12-2024, 413 PRE00 fuera de la asignación, cero ambiguos y cero fuera de ventana, las tres cifras de asignación de D42/D50, T0 sin netos negativos, exposición total de EXP01, suma mensual igual a la anual, completitud 2021 por encima de 0,995 en los peligros cortos y menor en 2024 en los largos, identidad frecuencia × severidad, forma cerrada de la desviación Tweedie de potencia 1,5 (`4 (sqrt(mu) - sqrt(y))^2 / sqrt(mu)`) y comportamiento de las referencias M00 en los tres cortes. Una corrida anterior del mismo día (`bases_20261017T120043Z_d40a40af`) falló su control K18 porque el control estaba mal formulado (suponía D² cero por ramo para una tasa constante, cuando la exposición explica parte de la varianza); se conserva como historial y no es la vigente.

Lo que esta entrega no es: no es una revisión humana ni independiente (la verificación es propia y asistida por IA); no confirma cómo valoró el organizador la etiqueta de 2025; no aplica ninguna capa de datos ni cambia `approved_for_modeling`; no entrena modelos ni envía nada. La referencia pública de 0,07169 procede de una captura aportada por el participante (D64), no se verificó en vivo y no se atribuye a ningún método. Aplican Documentación IAA §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §§3.2 y 3.5–3.6 en los mismos términos que D50 y D66.
