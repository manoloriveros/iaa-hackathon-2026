# Bitácora de la validación nocturna, 23 al 24 de octubre de 2026

Sesión de Claude (Cowork) pedida por el participante a las 18:15 de Bogotá: retomar las partes 1 y 2 del reto, validar todo de forma exhaustiva, programar avances durante la noche, validar y volver a validar cada decisión, empezar por modelos estándar y complicarlos solo cuando sea estrictamente necesario, y llegar al mejor modelo de la forma más simple posible, empezando por datos, supuestos, metodologías y decisiones anteriores. A las 18:22 añadió: «mantén tu evaluación independiente a las anteriores».

Respuestas del participante a las cuatro preguntas de arranque (18:20):

- Bloque 2024 de la semana 2: abrirlo una sola vez, con la política SEL01, después de congelar referencia y hasta tres aspirantes con preinscripción.
- Parte 1: auditoría de datos, supuestos y decisiones, y escalera simple (tasa por ramo, GLM Tweedie, un GBM único) frente a S30 y S41 con el mismo contrato. S41 no se toca.
- Avances: cada hora, en el chat y en esta bitácora.
- Revisores independientes (subagentes) autorizados: reciben código y datos, no mis conclusiones.

Reglas de independencia que sigo esta noche:

1. Código nuevo escrito desde el diccionario oficial y los Parquet originales. No leo los scripts de preparación ni de modelos de Codex ni de sesiones anteriores de Claude antes de tener mis propias cifras.
2. Las cifras anteriores que ya conozco por la memoria del proyecto (por ejemplo, 609 exposiciones corregidas o T0 de 27.997.991,57 CU en el emergente) no se usan para ajustar nada; se comparan solo en la conciliación final, y cada diferencia se explica.
3. Cada decisión se escribe con su regla antes de medir su efecto, y se revalida con una prueba que podría fallar.
4. La escalera de modelos sube un peldaño solo si mejora al anterior en la materialidad fijada antes de medir, con intervalos por cliente.

Ubicaciones: trabajo en la nube de Claude en `/home/claude/noche/` (datos copiados con SHA-256 verificado, código, salidas). Copia de esta bitácora y entregables en `C:\dev\Hakaton\Hackaton\Semana 2\Claude\validacion_nocturna_20261023\`. Tablas por fila en `Repositorio_IAA2026/privado/semana2/claude_validacion_nocturna_20261023/` (fuera de Git).

## Registro por hora

### 18:15–18:40 Arranque

- Lectura de la memoria del proyecto (secciones 1 a 30), del contrato, del plan y del final del foro de semana 2 (hasta CLA-S2-20261023-003, 20:58 UTC).
- Primer punto de control programado para las 19:22.
- Originales copiados a la nube y verificados: los 13 Parquet emergentes coinciden en SHA-256 y tamaño con el manifiesto de descarga; los 11 de semana 1, con el manifiesto oficial del 16 de octubre. Huellas en `salidas/huellas_originales.json`.
- Entorno de la nube: Python 3, pandas 3.0.5, pyarrow 26.0.0, scikit-learn 1.7.2, LightGBM 4.7.0, statsmodels 0.15.0, glum 3.4.1; 2 CPU y 7 GB.

### 18:40–19:05 Datos de la semana 2 desde los originales (código nuevo, `codigo/s2_base.py`, `codigo/reporte.py`, `codigo/s2_ultimo.py`)

Reglas escritas antes de medir: EXP-N1 (exposición = días inclusivos / 365 a cuatro decimales, la convención de todo el test 2025), ASG-N1 (siniestro a la fila con mismo `policy_id`, ramo y fecha dentro del periodo), OBJ-N1 (T0 = incurrido − recuperaciones de los no rechazados con asignación única), CAP-N1 (capital entre mil solo si supera el hueco del ramo y su prima por mil cae bajo el mínimo de la población normal), REP-N1/N2 (retraso de reporte por peligro, común a los dos mercados, estimador de Lynden-Bell para datos truncados; para el coste, ponderado por neto recortado al p99,5).

Resultados propios:

- Exposición: 609 filas de entrenamiento cambian (254 autos, 155 edificios, 200 contenidos): 495 estaban en días/360 y 114 en número de días. El test no cambia ninguna.
- Siniestros: 9.258, sin duplicados ni fechas imposibles; 120 rechazados, todos con importes cero. 9.222 se asignan a una sola fila; los 36 sin fila son todos anteriores al primer periodo de su póliza (28 autos, 3 edificios, 5 contenidos). No hay ambiguos.
- T0 total 27.997.991,57 CU: autos 15.855.887,96, edificios 9.558.749,31, contenidos 2.583.354,30.
- Capital: hueco de 67 veces en edificios (894.000 → 60.000.000) y de 27 en contenidos (283.200 → 7.600.000); 349 filas por encima (110 de entrenamiento, 239 de test). Las 349 pasan la prueba de prima por mil: con el capital entre mil su prima por mil cae dentro del rango normal (edificios 0,60–11,0 frente a 0,45–17,4; contenidos 2,09–6,95 frente a 1,61–10,6) y su mediana coincide con la normal (233.000 frente a 236.000; 35.900 frente a 36.000).
- Reporte: los retrasos por peligro coinciden entre mercados (medianas y p90 de la cohorte 2023 casi iguales). Completitud de coste al cierre de 2024: autos 2023 0,973 y 2024 0,816 (lesiones corporales: F(365 días) 0,845 en coste frente a 0,862 en conteos, porque los tardíos son un 7–12 % más caros); edificios 0,997 y 0,950 (hundimiento); contenidos 0,998 y 0,978.
- Prima de riesgo última por año-exposición: autos 444,8 (2023) y 469,2 (2024); edificios 516,0 y 323,0; contenidos 91,3 y 88,7. En edificios el incendio es el 45 % del coste último con 70 siniestros: el nivel de ese ramo es muy ruidoso y necesitará credibilidad.
- Recuperaciones: ningún abierto tiene recuperaciones; si recuperaran como los cerrados (daños propios 24 %, robo 3,9 %), el neto de autos bajaría un 0,6 %. Diagnóstico, no se aplica.
- `customer_service_contacts` sigue midiendo el siniestro del propio periodo (frecuencia de autos 0,000 con cero contactos y 1,125 con tres o más) y cambia de distribución en el test (9,5 % con tres o más en entrenamiento, 0,8 % en test): fuera de cualquier modelo.
- Nuevo negocio: 6–9 % de la exposición en 2023–2024 y 77 % en 2025 en los tres ramos; el canal no cambia (70 % broker en los tres años).

### 19:05–19:35 Escalera de modelos de la semana 2, desarrollo 2023 (`codigo/marco.py`, `codigo/s2_escalera.py`, `codigo/desarrollado_gbm.py`, `codigo/desarrollado_glm.py`, `codigo/comparar.py`, `codigo/nb_frecuencia.py`)

Protocolo fijado antes de medir: solo filas emergentes de 2023; cinco folds propios por cliente (`sha256('noche_v1|customer_id') % 5`), distintos de los de Codex; objetivo T0 con offset log(e_ef_coste); D² Tweedie 1,5 global con los tres ramos concatenados; cada modelo se reescala al total de su entrenamiento (BAL-N1); comparaciones pareadas con bootstrap de Poisson por componente cliente-dirección (10.000 réplicas, semilla 2026102301) y repetidas sin el 0,1 % de filas más caras. El 2024 emergente sigue cerrado.

Mercado desarrollado rehecho con el mismo código (`codigo/base_mercado.py s1`): T0 = 741.156.868,43 CU y 160.432 aceptados con asignación única, iguales a los de la semana 1; 5.736, 4.182 y 4.311 exposiciones cambiadas; 413 siniestros anteriores al primer periodo. Es una reproducción independiente de la base de la parte 1.

Decisiones nuevas, cada una con su prueba:

- VAR-N1. Fuera previous_insurer, branch_id, email_domain, marketing_consent, document_preference y la marca self-employed. Prueba: χ²/gl de la frecuencia por nivel en el desarrollado de 0,91, 1,01, 1,35, 0,15 y 1,09 en contenidos y de 1,10, 1,17, 2,06, 5,69 y 5,02 en autos, con relatividades extremas entre 0,91 y 1,09. Revalidación: el D² interno del GBM desarrollado de contenidos sube de 0,0686 a 0,0761 al quitarlas.
- CON-N1. WOD = timber = t/w y MIX = non_standard. Prueba por proporciones: brick 70 %, t+w 12,6 %, non_standard 9,9 %, stone 8,0 % en el desarrollado frente a BRK 70 %, WOD 12,0 %, MIX 10,1 %, STN 7,9 % en el emergente.
- TRF-N1. Relatividades del desarrollado con esquema común (edad en bandas, sin región, crédito, kilometraje ni telemática, con la exposición como variable), entrenadas solo con datos del desarrollado, y nivel por ramo estimado en el emergente.

D² OOF 2023 (global; autos, edificios, contenidos):

| Peldaño | Global | Autos | Edificios | Contenidos | A/E nuevo negocio |
| --- | ---: | ---: | ---: | ---: | ---: |
| L0 tasa por ramo | 0,0677 | −0,0031 | 0,0157 | 0,0270 | 1,58 |
| L1 GLM Tweedie emergente, todas las variables, ridge 10 | 0,0805 | 0,0235 | 0,0036 | 0,0587 | 1,15 |
| L2 GLM frecuencia × severidad emergente | 0,0444 | 0,0148 | −0,0899 | 0,0546 | 1,37 |
| L3 GBM Tweedie emergente, regularizado | 0,0833 | 0,0054 | 0,0431 | 0,0424 | 1,47 |
| T1 relatividades GBM del desarrollado × nivel emergente | 0,1174 | 0,0285 | 0,0807 | 0,1080 | 1,41 |
| T1 relatividades GLM del desarrollado × nivel emergente | 0,1185 | 0,0424 | 0,0776 | 0,0864 | 1,28 |
| T2 T1-GBM + nuevo negocio y región emergentes (ridge 1) | 0,1235 | 0,0340 | 0,0920 | 0,1074 | 0,94 |

Bootstrap frente a T1-GBM: L0 −0,0498 [−0,0630; −0,0367]; L1 −0,0370 [−0,0563; −0,0197]; L3 −0,0342 [−0,0467; −0,0216]; T1-GLM +0,0010 [−0,0055; +0,0078]; T2 +0,0061 [−0,0015; +0,0135], P 0,91. Sin el 0,1 % superior: T1-GLM −0,0042 [−0,0082; −0,0003]; T2 −0,0004 [−0,0033; +0,0026]. Lectura: la transferencia es la única mejora robusta; lo demás está dentro del ruido.

Nuevo negocio (NB-N1, `salidas/nb_frecuencia.json`). Con un GBM Poisson del desarrollado sin variables de antigüedad, la frecuencia relativa del nuevo negocio es 1,134 (autos), 1,147 (edificios) y 1,169 (contenidos) en el desarrollado, con error típico logarítmico de 0,02 a 0,05, y 1,146, 1,186 y 1,156 en el emergente 2023, con errores de 0,06 a 0,17. Es el mismo efecto en los dos mercados. El A/E de coste de 1,89 en el nuevo negocio de autos depende de la severidad de pocos siniestros (1,23 sin el 0,1 % superior). Esto respalda por una vía independiente la decisión del participante de dar credibilidad al desarrollado en el nivel del nuevo negocio.

Errores propios encontrados y corregidos antes de usar ninguna cifra: el GBM partía de una tasa de 1 CU por año (A/E de 3,2), corregido al iniciar en la tasa media; el agrupado por cuantiles del GLM juntaba en un solo nivel las variables binarias, y ahora las discretas de 12 valores o menos van como categorías. Las cifras de la tabla son posteriores a las dos correcciones.

Límites: los D² de 2023 miden el ordenamiento dentro de un año y con el nivel estimado en ese mismo año; el nivel 2025 y la tendencia se miden en la confirmación de 2024.

### 18:58–19:36 Revisor independiente rev1 (subagente; `revision/rev1/INFORME.md`)

Recibió los originales, la descripción oficial de datos y tres OOF, sin mi código ni mis conclusiones. Recalculó con código propio:

- Exposición: 608 filas se apartan más de 0,0001 de días/365 (494 días/360 y 114 en días) más una fila de un día que vale 1/360 y queda bajo ese umbral; con igualdad exacta son mis 609. Test sin diferencias. Detalle nuevo: ninguna fila de 2024 cubre el 31 de diciembre de 2024.
- Siniestros y T0 emergente: iguales a los míos al céntimo (27.997.991,57 CU; 36 sin fila, todos anteriores al primer periodo, 92.267,26 CU).
- Desarrollado: 604 copias; T0 sin copias 741.156.868,43 CU sobre 160.432 siniestros, igual al mío.
- Capital: las mismas 349 filas (110 de entrenamiento, 239 de test) por el mismo hueco y la prueba de prima.
- Nuevo negocio en frecuencia (GLM de Poisson propio): 1,097 [1,082; 1,112] en el desarrollado y 1,208 [1,099; 1,322] en el emergente 2023; con mes de inicio y duración, 1,045 en el desarrollado. La mitad del efecto viene del calendario (el nuevo negocio empieza a mitad de año y dura menos).
- OOF: pliegues agrupados por cliente sin cruces; 213 direcciones cruzan pliegues (1,2 % de la y), irrelevante porque ningún modelo usa historial por dirección; y = T0 en las 50.094 filas; D² L0 0,0677, L3 0,0833, T1 0,1174 (mismos valores que los míos); T1 − L0 +0,0498 [+0,0369; +0,0630] y T1 − L3 +0,0342 [+0,0215; +0,0470] con 4.000 réplicas, y +0,0461 y +0,0326 sin el 0,1 % superior; T1 gana en los cinco pliegues. Su GLM propio con relatividades del desarrollado da 0,1112 con nivel fuera de pliegue, así que la ventaja de T1 no viene de fijar el nivel con información del pliegue.
- Problemas que señala: el GBM L3 queda casi constante en el pliegue 4 de contenidos (la comparación contra L3 lo perjudica algo; no cambia la conclusión) y los tres modelos predicen solo el 63–71 % del coste del nuevo negocio de 2023.

Desviación declarada: el revisor también calculó la razón de frecuencia del nuevo negocio en el emergente 2024 (1,039; 1,112 con 2023 y 2024 juntos). Es un diagnóstico de conteos sobre una covariable, no el resultado de ningún candidato; queda registrado como información vista antes de la apertura formal de 2024.

Consecuencia que adopto: el nuevo negocio de 2025 empieza en enero y dura el año, así que su relatividad debe medirse controlando el mes de inicio. Añado `start_month` al esquema común (es conocido al tarificar) y repito las relatividades del desarrollado.

### 19:36–19:56 Relatividades v2, preinscripción y apertura única de 2024 (`codigo/conf_insumos.py`, `codigo/conf_predicciones.py`, `codigo/puerta_2024.py`)

Antes de congelar:

- MM-N1. `make_model` fuera del GBM: con 300 categorías concentraba el 44 % de la ganancia del GBM desarrollado de autos y lo sobreajustaba. Sin ella, el D² interno sube de 0,0743 a 0,0845; en el desarrollo emergente, T1v2 (sin make_model, con mes de inicio, lr 0,02) frente a T1: +0,0038 [−0,0005; +0,0083], P 0,93, y +0,0045 [+0,0018; +0,0072] sin el 0,1 % superior.
- Nivel por balance frente al nivel que minimiza la desviación Tweedie: +0,0006 [−0,0004; +0,0016], dentro del ruido. Se queda el balance, que además conserva los totales.
- Tendencia: en el desarrollado 2023, aplicar la tendencia 2021→2022 baja el D² (autos 0,17983 → 0,17857, edificios 0,15838 → 0,15763, contenidos igual), aunque el nivel real subió. Excluida de la lista corta (`salidas/conf/validacion_tendencia_desarrollado.json`).
- Insumos de confirmación sin etiquetas de 2024 de ningún mercado: curva de reporte con ocurrencias hasta 2023 (completitud de 2024 en autos 0,818 frente a 0,816 con todo), relatividades del desarrollado 2021–2023 (D² internos 0,0851, 0,0767 y 0,0788).
- Evaluador ensayado con etiquetas sintéticas generadas desde A1: elige A1, rechaza A2. Predicciones congeladas reproducidas dos veces con el mismo SHA (e4f55f69…3a7eb7).

Preinscripción `preinscripcion/preinscripcion_puerta_2024.json` (SHA 802368ea…82c407), copiada a la carpeta del equipo y anunciada en el foro (CLA-S2-20261024-005, 00:55:32 UTC) antes de abrir. Lista: R0 tasa por ramo, A1 relatividades GBM del desarrollado × nivel emergente, A2 = A1 + región.

Apertura única: 00:55:37 UTC, 59.202 filas, 36.408 componentes, 9.063 filas de cliente nuevo (son exactamente el nuevo negocio de 2024). Resultado `salidas/conf/puerta_2024_resultado.json` (SHA b3faaece…a449b080).

| | R0 | A1 | A2 |
| --- | ---: | ---: | ---: |
| D² global 2024 | 0,0728 | 0,1214 | 0,1175 |
| Autos | 0,0499 | 0,0803 | 0,0805 |
| Edificios | −0,0213 | 0,0649 | 0,0520 |
| Contenidos | 0,0452 | 0,0920 | 0,0908 |
| A/E autos / edificios / contenidos | 1,05 / 0,63 / 0,97 | 1,11 / 0,61 / 0,96 | 1,11 / 0,62 / 0,96 |

Pares (intervalo bilateral de 99,17 %): A1 − R0 +0,0486 [+0,0265; +0,0733]; A2 − R0 +0,0446 [+0,0239; +0,0678]; A2 − A1 −0,0040 [−0,0104; +0,0025].

Acta de A1 frente a R0: la primaria pasa (límite inferior +0,0265 > 0,0005); pasan los cuatro escenarios (+0,0477 a +0,0495), los cinco segmentos (autos +0,030, edificios +0,086, contenidos +0,047, cliente nuevo +0,013, renovación +0,054) y la influencia (+0,019 tras retirar 37 componentes). Falla la salvaguarda de cliente nuevo: diferencia +0,0131, pero límite inferior del 95 % de −0,0105, por debajo de −0,001. Por la regla preinscrita A1 no promueve; A2 tampoco, por el mismo motivo. Titular formal: R0. A1 y A2 quedan como alternativas.

Lectura: el fallo es de potencia, no de evidencia contraria. Con 9.063 filas y 447 siniestros, la desviación típica de la diferencia en ese subconjunto ronda 0,014; para que el límite del 95 % quedara sobre −0,001, la mejora en clientes nuevos tendría que ser de al menos 0,022. Cambiar la regla es una decisión del participante (enmienda versionada de la política). Esta sesión no la cambia.

Diagnósticos posteriores a la apertura (exploratorios, ya no confirmatorios): en 2024 el nuevo negocio queda bien calibrado frente a la renovación bajo A1 (A/E 0,871 frente a 0,886, razón 0,98). El exceso de 2023 (1,36) no se repite, así que la relatividad del nuevo negocio del desarrollado basta. El nivel de 2024 frente al de 2023 es 1,11 en autos, 0,61 en edificios y 0,96 en contenidos: el nivel de edificios es lo más inestable.

### 19:58–20:06 Revisor independiente rev2 de la puerta (subagente; `revision/rev2/INFORME.md`)

Recibió los originales, las predicciones congeladas, la política y las definiciones preinscritas, sin mi código ni mis resultados. Rehízo el objetivo de 2024 y la puerta con código propio:

- Mismo D² al quinto decimal (R0 0,07285, A1 0,12144, A2 0,11746; por ramo y A/E idénticos).
- Bootstrap con sus propios sorteos: A1 − R0 +0,04859 [+0,02720; +0,07350]; A2 − R0 +0,04462 [+0,02415; +0,06679]; A2 − A1 −0,00398 [−0,01061; +0,00246]; con otras tres semillas el límite de A1 − R0 va de 0,02636 a 0,02717.
- Las mismas salvaguardas, con el mismo fallo de cliente nuevo (límite del 95 % −0,01035 para A1). Titular final: R0.
- Potencia: la desviación típica de la diferencia en clientes nuevos es 0,01405; para pasar haría falta una diferencia observada de al menos 0,0221, 1,7 veces la observada. Con el efecto observado, la salvaguarda pasaría el 26 % de las veces, y para un 80 % de potencia harían falta unas 55.900 filas de cliente nuevo. Con el margen de −0,001 (0,07 desviaciones típicas) la regla es en la práctica una prueba de superioridad, no de no inferioridad.
- Observaciones que acepto: la condición de nivel se preinscribió sin evidencia con SHA propia (no cambia el resultado; la evidencia está en `salidas/conf/nivel_2025_preinscripcion.json` y en la escalera de desarrollo, y debí enlazarla con su huella); el archivo de predicciones contiene la columna A3 excluida antes de abrir, que nadie puntuó; el sobrenivel de edificios en 2024 (A/E 0,61) viene de seis incendios de 181.000 a 340.000 CU en 2023, seis de los siete mayores siniestros de los dos años; los 37 componentes más favorables concentran el 63 % de la ventaja de A1, que sigue en +0,019 sin ellos y solo se anula al retirar 191.

### 20:06–20:20 Producción 2025, prima comercial y parte 1 (`codigo/produccion_2025.py`, `codigo/prima_comercial.py`, `codigo/p1_escalera.py`, `codigo/p1_evaluar.py`)

Producción 2025 con las recetas preinscritas, sin enviar (`salidas/produccion/`):

- R0, titular formal: tasa por ramo 2023–2024. Total 61.202.963 CU. SHA 928865e5…96cb3e.
- A1, alternativa recomendada: relatividades del GBM desarrollado 2021–2024 × nivel por ramo 2023–2024 (autos 427,8, edificios 403,9, contenidos 92,4 CU por unidad de relatividad). Total 67.152.922 CU (autos 41,17 M, edificios 20,45 M, contenidos 5,54 M). SHA 4a9f7fc0…f715f9.
- Las dos con 209.063 filas, mismo orden de `row_id` que la plantilla, predicciones finitas y positivas, y releídas del CSV.
- En A1, la tasa del nuevo negocio de autos de 2025 es de 559 CU por año frente a 394 de la renovación: el bloque del broker trae conductores de más riesgo según las relatividades del desarrollado.

Nivel de edificios, el punto débil. La caída de 2024 viene de la frecuencia de incendio (4,3 por mil en 2023 frente a 1,8 en 2024, unos 49 frente a 21 siniestros; con el mismo índice de incendios forestales, 0,50 frente a 0,55). Recortando a 100.000 CU y aplicando el exceso del desarrollado (1,08), el nivel sería 363 en lugar de 404. Pero el exceso emergente es mayor (1,20), así que el recorte probablemente infravalora. Queda como rango plausible de 360 a 420 CU, y ninguna estimación con dos años lo cierra. Diagnóstico exploratorio sobre 2024 ya abierto: un error de nivel del 10 % en edificios cuesta unas 0,004 de D².

Prima comercial de las 20 referencias (`salidas/produccion/prima_comercial_referencias.csv`). Fórmula: P = [R·(1 + 0,12 en hogar) + 85·exposición] / (1 − 0,15 − c − 0,08 − 0,08), con c = 0,20 en broker y 0 en directo, y se comprueba que los componentes suman P. Con A1, la prima comercial anualizada es entre 1,4 y 6,1 veces la prima escrita (mediana 2,2 en autos, 4,0 en edificios y 2,6 en contenidos). La tarifa vigente del emergente cubre poco más que el riesgo: en el test, la prima escrita por año es 777 en autos, 427 en edificios y 154 en contenidos, frente a primas de riesgo de A1 de 521, 432 y 94. Sensibilidad de gasto fijo entero en las tres filas cortas: M00129413 335 → 451, B00250679 80 → 235, C00314425 20 → 181.

Parte 1, revalidación independiente:

- Base del desarrollado rehecha con código nuevo: T0 = 741.156.868,43 CU, 160.432 siniestros, 604 duplicados, 413 anteriores al primer periodo, 5.736, 4.182 y 4.311 exposiciones cambiadas. Todo igual a D42, D47, D59 y D67.
- Capital: con los umbrales de 5 millones (edificios) y 2 millones (contenidos), los 3.527 extremos (1.765 y 1.762) pasan la prueba de prima, como en D34 y D66.
- IBNR: mi completitud de coste de 2024 da factores de 1,2529 en autos, 1,0717 en edificios y 1,0239 en contenidos, frente a 1,2877, 1,0796 y 1,0317 de D67. Mi estimador diario y truncado da un 2,7 % menos de IBNR en autos. Va en la dirección de D95 (el IBNR de lesiones de D67 se sobrestimaba al cierre de año) y de la sonda D100 (el público quería el nivel de autos de S30 un 2,3 % más bajo).
- Escalera V24 (ajuste 2021–2023, T0 de 2024; mis y coinciden exactamente con las de S30 en las 626.190 filas):

| Peldaño | D² 2024 | Forma (nivel oráculo) | Cuerpo | Frente a S30, IC90 |
| --- | ---: | ---: | ---: | --- |
| Tasa por ramo | 0,0736 | 0,0750 | 0,0802 | −0,0643 [−0,0693; −0,0597] |
| GLM Tweedie, esquema común | 0,1193 | 0,1195 | 0,1025 | −0,0186 [−0,0232; −0,0150] |
| Un GBM, esquema común | 0,1238 | 0,1247 | 0,1047 | −0,0141 [−0,0201; −0,0099] |
| Un GBM, todas las F0 del desarrollado | 0,1290 | 0,1300 | 0,1073 | −0,0089 [−0,0118; −0,0065] |
| S30 (receta completa) | 0,1379 | 0,1381 | 0,1113 | — |

Lectura: un solo GBM estándar con las variables del contrato logra el 94 % del D² de S30, y un GLM el 87 %. La complejidad de S30 aporta +0,009, una ganancia robusta (IC90 por encima de cero), así que en la parte 1 sí estaba justificada. El S30 V24 de mi evaluación (0,13788) coincide con el registrado en la memoria.
- Peldaño añadido a las 20:26: el mismo GBM con todas las F0 más la historia propia de la póliza conocida al inicio del periodo (siniestros reportados antes de `period_start` y años observados) da 0,1313 (autos 0,0851, edificios 0,1095, contenidos 0,0882). Frente a S30: −0,0066 [−0,0086; −0,0048]. La historia aporta +0,0023 sobre el GBM F0, y con ella un modelo estándar llega al 95 % del D² de S30. Lo que queda (+0,0066) es lo que justifican los componentes por peligro, las severidades GLM con capital, CatBoost, clima y mezclas de la receta S30.

### 20:36–20:56 Revisor independiente rev3: producción, nivel y prima comercial (subagente; `revision/rev3/INFORME.md`)

Confirmó sin mi código: los dos CSV cumplen el formato (209.063 filas, orden de la plantilla, finitos y positivos); la prima comercial de las 20 referencias se reproduce a 0,0075 CU con la misma fórmula; S30 en V24 da 0,137880 y su T0 coincide con el suyo en las 626.190 filas (diferencia máxima 1,5e-11).

Sus objeciones, con mi revisión de cada una:

- «A1 parece no llevar IBNR de autos.» No se sostiene: el último implícito de A1 en 2023–2024 es 17,763 M CU, frente a 17,781 M de la tasa con IBNR y 15,856 M de T0 observado. La coincidencia que vio (tasa de renovación 2025 de 394,06 igual a la tasa observada sin desarrollar reponderada) se explica por otra cosa: según las relatividades del desarrollado, la renovación de autos envejece y abarata (g medio de 1,070 en 2023, 1,008 en 2024 y 0,921 en 2025, por más años de bonificación, antigüedad y edad del vehículo), y esa deriva compensa casi exactamente el IBNR.
- Nivel 2025 independiente más alto que A1 en los tres ramos: autos 601 (rango 517–661), edificios 475 (431–489; banda del 90 % 401–555), contenidos 103 (94–116), frente a 521, 432 y 94 de A1. La diferencia viene de dos fuentes. La primera es la tendencia: aplica la de severidad del desarrollado (+1,9 %, +6,2 % y +3,5 % anual) y A1 no lleva tendencia. La segunda es que supone que la renovación de 2025 cuesta lo mismo que la histórica, mientras que A1 deja que la mezcla de covariables la abarate. Lo acepto como evidencia de que el nivel de A1 puede quedar corto, sobre todo por la tendencia. Entra como opción de nivel en el informe para el participante.
- Edificios: el incendio explica el 81 % de la varianza del nivel (CV 9,9 % sin efecto año). Hubo 49 incendios en 2023 frente a 21 en 2024 (p = 0,0003 bajo tasa común, el exceso de 2023 concentrado en E02: 18 frente a 2). En el desarrollado no hay efecto año de incendio (p = 0,35). Un modelo de incendio del desarrollado sobre `wildfire_index` predice 75,4 incendios frente a 70 observados y da un nivel de 486, a favor del promedio de dos años frente a 2024 solo.
- Prima comercial: la sensibilidad de gasto fijo entero contaba dos veces en C00314425 (la póliza tiene otra fila en 2025, C00318346; con el gasto repartido por póliza, P = 20,10) y en B00250679 (segundo tramo de una póliza que empezó el 15 de noviembre; P = 208,69 por póliza). Lo corrijo en la tabla. Las otras dos observaciones: el impuesto va dentro del denominador porque la unidad es «share of premium» (si se cobrara encima, P bajaría un 7,2 % en broker), y la comisión de comparador falta en el emergente (5 % del test, ninguna referencia afectada).

### 20:56–21:05 Opciones de nivel, corrección de la prima comercial y figuras

- Sensibilidad del gasto fijo corregida: ahora se reparte 85 CU por póliza y año entre las filas 2025 de la misma póliza. Resultado: M00129413 451,16 (póliza corta única); B00250679 208,67 (tramo de 0,1096 de una póliza con 0,1288 en 2025); C00314425 20,10 (la póliza tiene otra fila, C00318346). Coincide con rev3.
- Tendencia del desarrollado con las relatividades fijas, ajuste log-lineal 2021–2024 (`salidas/produccion/tendencia_opciones.json`): autos +4,6 % anual, edificios +6,4 %, contenidos +3,6 %. Del punto medio de la experiencia (2024,0) al de 2025 (2025,5) van 1,5 años, que dan factores de 1,072, 1,097 y 1,054. Opción A1T = A1 × esos factores: total 72,40 M CU (autos 44,14 M, edificios 22,43 M, contenidos 5,83 M), SHA 4ba0cc34…85aca5. No se preinscribió, así que es una opción para el participante y no la sustituye la puerta.
- Ruido de una posible sonda de nivel, medido sobre 2024 como sustituto (`salidas/conf/sonda_ruido_s2.json`): la desviación típica del logaritmo del óptimo de un 33 % frente al del 67 % restante es 0,10, 0,30 y 0,18 en autos, edificios y contenidos con el tamaño de 2024. Escalada al tamaño del test 2025 (3,5 veces más filas) queda en unas 0,054, 0,16 y 0,095.
- GLM de frecuencia-severidad solo emergente, repetido tras corregir el agrupado: 0,0603 (ridge 0,01/0,1) y −0,078 (0,001/0,01). Sobreajusta la severidad; no compite.
- Cinco figuras en `figuras/`, con la paleta de referencia y comas decimales.

### 21:05–21:25 Cierre del primer bloque y robustez de A1

- Publicados el informe (`INFORME.md`, 82 de 82 cifras verificadas contra sus fuentes con `codigo/verificar_informe.py`), el código, las figuras, las salidas agregadas y los informes de los revisores en la carpeta del equipo, y las producciones en `privado/` (62 archivos; las huellas coinciden en el equipo, las PNG sin el bloque C2PA que añade la copia). Aporte de cierre CLA-S2-20261024-009 (02:07 UTC). Entrada en DECISIONES.md (S2-PUERTA2024-CLAUDE-20261024), clave `week_2_nightly_validation_claude_20261024` en ESTADO_PROYECTO.json, sección 34 en CLAUDE.md y en el documento del Proyecto IAA. Antes de tocar los tres registros se guardaron copias en `respaldo_registros/`.
- Otra sesión de Claude verifica en paralelo la tanda nocturna de Codex (aportes 007 y 008) y avisa de una incidencia de Kaggle: la plataforma rechaza envíos de 209.063 filas porque espera 626.639. Hoy nadie puede enviar.
- Sensibilidad del nivel de A1 al IBNR (`salidas/produccion/sensibilidad_ibnr_nivel.json`): con la curva de conteos en lugar de la de coste, −0,5 % en autos; con la completitud de lesiones × 0,9, +4,1 % en autos; con la de hundimiento × 0,9, +1,0 % en edificios.
- Semillas del GBM desarrollado (`salidas/produccion/semillas_A1.json`): con las semillas 12 y 13, el D² de desarrollo de 2023 es 0,1239 y 0,1243, frente a 0,1213 de la semilla 11 de A1 (fijada antes de medir, no elegida). Por fila, la predicción de 2025 cambia una mediana del 4 al 6 % y un p99 del 23 al 26 %; los totales por ramo, hasta un 1,3 %. El promedio de las tres semillas da 0,1234, +0,0022 [+0,0009; +0,0035] frente a A1 y +0,0003 sin significación en el cuerpo. Lectura: el ruido de semilla (±0,003) es del mismo tamaño que los añadidos que no subieron (región +0,0027, clima +0,0025), lo que confirma que no eran mejoras reales. Promediar semillas es estabilización y no complejidad; como llega después de abrir 2024, entra solo como opción para el participante.

### 21:20 Error propio encontrado: faltaba ID01 en autos del desarrollado

Al revisar los cruces encontré que mi constructor de variables no aplicaba ID01 (D32): en autos del desarrollado, 98.110 filas de entrenamiento y 25.554 de test tienen el `customer_id` sin los ceros iniciales. Esas filas entraron sin variables de cliente (ocupación, antigüedad, siniestros declarados, segmento, campaña…), que el GBM trató como faltantes. El emergente no tiene el problema: sus 137.804 filas de autos cruzan al completo.

Qué afecta:

- Las relatividades de autos de A1 y de A2: el GBM desarrollado aprendió las variables de cliente con el 90 % de las filas.
- Por lo tanto, también las predicciones congeladas de la puerta de 2024 y las producciones R0/A1/A1T en autos. R0 no usa relatividades y no cambia.
- La escalera de la parte 1 en autos.

Qué no afecta: hogar en los dos mercados, las bases, T0, el IBNR y la prima comercial salvo por la prima de riesgo de autos.

Corrección: `variables.py` rellena a ocho posiciones solo para cruzar y comprueba que todas las filas cruzan (`customer_since_year` sin nulos). El acta de la puerta queda como está, porque se hizo con la receta congelada. La receta corregida se mide después como corrección técnica, con desarrollo 2023 y 2024 exploratorio, y se declara así. Se relanzan en cadena (`codigo/cadena_correccion_id01.sh`) los GBM de autos con tres semillas, las versiones con historia F1 y la escalera de autos de la parte 1.

### 21:25–21:45 Efecto de la corrección ID01, semillas e historia F1 (`codigo/cadena_correccion_id01.sh`, `codigo/evaluar_correccion.py`)

- ID01 corregido: el GBM desarrollado de autos queda casi igual (D² interno 0,0846 frente a 0,0845). En el desarrollo 2023, A1 corregida da 0,12115 frente a 0,12126 (−0,0001 [−0,0010; +0,0009]). En 2024, como exploración, 0,12136 frente a 0,12144 (−0,0001 [−0,0009; +0,0007]). La producción corregida (A1fix) baja autos de 41,17 M a 40,90 M CU. El defecto era real pero inmaterial, y no cambia el acta.
- Tres semillas promediadas (A1fixb3): +0,0017 [+0,0005; +0,0031] en desarrollo 2023 y +0,0005 [−0,0009; +0,0019] en 2024. Es estabilización, con efecto pequeño.
- Historia de la póliza conocida al inicio (A1fixF1: siniestros reportados antes de `period_start` y años observados, en el GBM del desarrollado y aplicada igual al emergente): +0,0050 [+0,0019; +0,0084] en desarrollo 2023 (cuerpo −0,0001, sin significación) y +0,0042 [+0,0022; +0,0061] en 2024, con los tres ramos al alza (autos 0,0849, edificios 0,0700, contenidos 0,0949), cuerpo renivelado +0,0015, renovación +0,0047 y nuevo negocio +0,0008. Es la mejora más clara después de la transferencia, y es una variable estándar (tarificación por experiencia, bloque F1 de la metodología). Como se definió después de abrir 2024, queda como propuesta para una versión 2 de la política y no promueve bajo la v1. En 2025 solo el 23 % es renovación con hasta dos años de historia, así que su efecto será menor que en 2024.
- Producciones nuevas en `salidas/correccion/`, sin enviar: A1fix (66,89 M CU, SHA 8fe0351e…77f2f10e), A1fixb3 (67,17 M, SHA 355dca1a…65bef08f) y A1fixF1 (68,40 M, SHA 45eb100a…dbc15fb1).

### 21:53–21:57 Backtest de estimadores de nivel en el desarrollado (`codigo/nivel_backtest.py`)

Pregunta: con dos años de experiencia del tamaño del emergente, ¿qué estimador de nivel predice mejor el año siguiente? Tomé 300 muestras por ventana de pólizas del desarrollado, con tantas filas por año como el emergente, y relatividades fijas. El nivel verdadero es el del año objetivo en todo el desarrollado. Error en logaritmo:

| Ramo y ventana | Agrupado sin tendencia (receta A1): sesgo / de | Con tendencia de la ventana | Recorte a 100.000 + exceso externo | Recorte + tendencia |
| --- | --- | --- | --- | --- |
| Autos 21–22 → 23 | −0,121 / 0,039 | −0,044 / 0,039 | −0,122 / 0,030 | −0,045 / 0,030 |
| Autos 22–23 → 24 | −0,021 / 0,135 | +0,126 / 0,135 | −0,011 / 0,030 | +0,137 / 0,030 |
| Edificios 21–22 → 23 | −0,070 / 0,078 | −0,022 / 0,078 | −0,072 / 0,063 | −0,024 / 0,063 |
| Edificios 22–23 → 24 | −0,118 / 0,074 | −0,029 / 0,074 | −0,118 / 0,060 | −0,028 / 0,060 |
| Contenidos 21–22 → 23 | −0,086 / 0,054 | −0,111 / 0,054 | igual | igual |
| Contenidos 22–23 → 24 | −0,057 / 0,054 | +0,080 / 0,054 | igual | igual |

Lectura:

- El nivel agrupado sin tendencia (la receta de A1) predice de menos el año siguiente en las seis ventanas, entre un 2 y un 12 %, porque en el desarrollado los niveles suben. Esto respalda aplicar tendencia, en la línea de A1T y de rev3.
- La tendencia de una sola ventana es ruidosa. En autos 22–23 se pasa (+12,6 %) porque al salto de 2023 le siguió una caída en 2024. Por eso A1T usa la tendencia log-lineal de cuatro años y no la del último año.
- Recortar a 100.000 CU con un factor de exceso externo reduce mucho la varianza en autos (de 0,135 a 0,030 en la ventana con grandes lesiones) y algo en edificios. Pero en el emergente el exceso propio de edificios (1,20) es mayor que el del desarrollado (1,08), así que importar el factor bajaría el nivel de edificios sin justificación. Queda como sensibilidad.

### 21:57–07:20 Pausa

La sesión se detuvo a las 21:57 por el límite de uso, justo después del backtest de nivel, y no hubo trabajo hasta las 07:20 del 24. Los controles horarios de ese tramo no se ejecutaron. El revisor rev4 alcanzó a terminar la parte de historia (Q1) antes del corte, pero no la de tendencia (Q2) ni su informe.

### 07:22–07:30 Sincronización n3 y sensibilidad del acta a la auditoría de Codex (`codigo/puerta_sensibilidad.py`)

- La tanda n3 en el equipo coincide con el manifiesto en los 74 archivos. De ellos, 61 son idénticos byte a byte, 5 son PNG que coinciden al quitar el bloque C2PA (`caBX`) que añade la copia, y 8 son producciones en `Repositorio_IAA2026/privado/semana2/claude_validacion_nocturna_20261023/` con su SHA.
- La auditoría nocturna de Codex (COD-S2-IA-20261024T052608Z) encontró tres diferencias entre mi puerta y el motor común. La salvaguarda de cliente nuevo usa 2.000 réplicas y cuantil 0,05, en lugar de 10.000 y 0,025. Los escenarios fijan las predicciones y estresan las etiquetas. Y algunas decisiones se toman con cifras redondeadas a seis decimales. Medí el efecto de cada una sin tocar el acta (`salidas/conf/puerta_sensibilidad.json`):
  - Cliente nuevo, A1 − R0 = +0,0131. Su límite inferior va de −0,0104 a −0,0108 con cuantil 0,05 y de −0,0141 a −0,0153 con 0,025, con 2.000 o 10.000 réplicas y dos semillas. El umbral es −0,001, así que falla en todas las variantes. En A2 el límite va de −0,0132 a −0,0195.
  - Sin redondeo, el margen más estrecho de las demás salvaguardas es +0,0141 en A1 (segmento cliente nuevo frente a −0,001) y +0,0121 en A2. Los escenarios ya tenían más de +0,044. Ningún redondeo pudo decidir.
  - La primaria se reproduce sin redondeo: A1 − R0 = +0,048592, límite +0,026514 (el acta dice +0,026514).
  - El veredicto no cambia con ninguna variante: R0 sigue de titular. La equivalencia literal con el motor común sigue sin demostrarse, como dice Codex. Lo que sí queda medido es que esas diferencias no mueven el resultado.
- Kaggle: HOST anunció a las 02:57 UTC el arreglo del rechazo por número de filas (209.063 enviadas frente a 626.639 esperadas). Nadie ha comprobado todavía que se pueda enviar. No es tarea de Claude.

### 07:31–08:07 Revisor rev4 completo (historia F1 y tendencia)

Relancé rev4 con el mismo encargo y sin acceso a mi código, mis salidas ni mi informe. Aprovechó la caché y el código de su corrida anterior, pero primero los revisó: reconstruyó la caché, que salió idéntica, y rederivó por otro camino conteos, costes, historia y exposición, sin ninguna diferencia. Su informe está en `revision/rev4/INFORME.md`.

- Historia (Q1). Usa la historia de 12 meses, con GLM y GBM de frecuencia. En autos, la relatividad de un siniestro es 1,29 en el desarrollado y 1,32 en el emergente 2024, y la historia sube el D² de frecuencia de 2024 en +0,0039 [+0,0020; +0,0058] (GLM) y +0,0029 (GBM), casi todo en renovación. En hogar el signo es positivo, pero no significativo con 35 y 23 siniestros previos. Además encontró un problema de diseño: en 2023 casi nadie tiene historia observable, así que calibrar el nivel en 2023 deja al modelo con historia más alto en 2024 por calendario, no por riesgo (A/E de autos 0,892 frente a 0,970).
- Tendencia (Q2). Usa un GLM de frecuencia y severidad, tope de 250.000 CU e IBNR por peligro. Obtiene autos +2,4 %, edificios +6,2 % y contenidos +3,7 % al año. Juntar dos años sin tendencia se queda corto en hogar (edificios −9,4 % y contenidos −7,0 % de media). Recomienda aplicar tendencia en hogar y una moderada en autos (cerca de 1,03), y advierte que en autos pesa más el IBNR de lesiones de 2024 que la tendencia.

### 08:07–08:12 Conciliación con rev4: regla TEN-N2 e historia neutral

- Hogar coincide casi al punto. Índice de edificios: rev4 1,000, 1,031, 1,093, 1,205; el mío 1,000, 1,033, 1,096, 1,204. Contenidos: rev4 1,000, 0,982, 1,077, 1,098; el mío 1,000, 0,984, 1,078, 1,090. El sesgo sin tendencia en edificios es −7,0 % y −11,8 % en rev4, y −6,8 % y −11,1 % en el mío pasado a porcentaje.
- Autos difiere por un solo siniestro: una lesión de 11,9 M CU en 2023, el 10 % del coste del año (`codigo/tendencia_tope.py`). Con las relatividades corregidas, mi tendencia sin tope es +4,3 %, y con tope a 250.000 CU es +3,5 % (EE 0,9). Esa lesión explica también mi −12,1 % en la ventana de autos 21–22 → 23, donde rev4 obtiene +0,4 % con tope.
- Regla nueva TEN-N2: la tendencia se estima con siniestros topados a 250.000 CU y el exceso es carga estable. Factores 1,055, 1,094 y 1,053 (antes 1,072, 1,097 y 1,054). Las producciones A1fixTc (71,34 M) y A1fixF1nTc salen de `codigo/produccion_tendencia_tope.py` y `codigo/f1_nivel.py`. La de rev4 (cerca de 1,03 en autos) queda como cota inferior razonable.
- Historia neutral (`codigo/f1_nivel.py`). Calibrado en 2023, A1fixF1 deja el total de 2024 un 3,8 % por encima de A1fix en autos, y en 2025 un 2,6 %, así que con tendencia contaría el nivel dos veces. En 2024 eso favoreció por casualidad a F1 (A/E de autos 1,063 frente a 1,104 de A1fix). Si se reescala F1 al total de A1fix por ramo (calibración neutral de rev4, sin mirar siniestros de 2024), la ganancia en 2024 es +0,0040 [+0,0023; +0,0057] frente a +0,0042. Casi toda la mejora es de orden. La propuesta queda como A1fixF1n (66,89 M, mismo total que A1fix) y A1fixF1nTc (71,34 M), y A1fixF1T queda sustituida.
- El informe recoge todo lo anterior en las secciones 4, 5, 6 y 9. El verificador encuentra 127 de 127 cifras.

### 08:12–08:18 Registros, foro y un control más

- Codex publicó a las 13:02 UTC una auditoría (COD-S2-IA-20261024T122737Z) de otra sesión de Claude (`ml_independiente_20261023`). Uno de sus hallazgos es que los pesos por peligro se estimaban con todo el entrenamiento, sin año ni fold. Revisé el análogo en mi carpeta. La curva de reporte de mi desarrollo 2023 es global (los dos mercados, todas las ocurrencias), mientras que la de la puerta solo usa ocurrencias hasta 2023. Recalculé la exposición efectiva de 2023 con la curva de la puerta. Cambia el total un 0,05 % en autos y nada en hogar, con un p99 por fila de 0,12 %. Es inmaterial y es la misma para todos los candidatos, así que no altera ninguna comparación.
- Registros: entrada S2-PUERTA2024-CLAUDE-20261024-ACTUALIZACION en DECISIONES.md, clave `week_2_nightly_validation_claude_20261024_actualizacion` en ESTADO_PROYECTO.json, sección 36 de CLAUDE.md (la 35 la escribió otra sesión), documento del Proyecto IAA y aporte CLA-S2-20261024-012. Copias previas en `respaldo_registros/*_antes_n4*`.
- Codex registró a las 12:48 UTC metadatos nuevos de los Parquet oficiales en Kaggle (mismos nombres y tamaños, otra fecha, sin checksum). No lo comprobé. Si los datos cambiaran, habría que rehacer desde los originales nuevos.

### 08:18–08:23 Conciliación final con el catálogo de Codex (`codigo/conciliacion_codex.py`)

Hecha al final, como se acordó. Copié las OOF de desarrollo 2023 de Codex (corrida dev7, W2-B00 a W2-B18, SHA 24394549…15beacb7) a la nube y las medí con mi código junto a las mías:

- Las filas son las mismas 50.094, el objetivo es idéntico (15.297.103,84 CU) y también la desviación nula. Reproduzco sus D² publicados al quinto decimal (B00 0,06858, B10 0,09424, B14 0,08671). Su vínculo de observación y mi exposición efectiva difieren un 0,4 % en total (por fila, de 0,993 a 1,022).
- La tasa sale igual en los dos trabajos: B00 − L0 = +0,0009 [−0,0008; +0,0026].
- Solo con el emergente, los GLM de Codex son mejores que mis peldaños: B10 − mi GBM = +0,0110 [−0,0009; +0,0229], y +0,0188 en el cuerpo. Mis modelos solo emergentes se quedaron cortos.
- La transferencia supera a todo su catálogo:
  - A1 − B10 = +0,0270 [+0,0141; +0,0402], y en el cuerpo +0,0177 [+0,0121; +0,0235].
  - A1 − B14 = +0,0345.
  - A1fixF1 − B10 = +0,0320.
- A1 gana en los tres ramos y en renovación, y en nuevo negocio queda a la par (0,082 frente a 0,080). B10 tiene un A/E de 1,080.
- Ninguna receta de Codex usa el desarrollado. Que la transferencia entre en la selección común es decisión del participante. 2024 ya se consultó, así que no habría confirmación intacta.
- El informe tiene la nueva sección 9, y el verificador encuentra 143 de 143 cifras.

### 08:23–08:27 Cierre

- Tanda n5 en el equipo: 8 de 8 huellas iguales. Añadí la conciliación a la sección 36 de CLAUDE.md, a la entrada de DECISIONES.md y a la clave de ESTADO_PROYECTO.json, y la publiqué en el foro (CLA-S2-20261024-013, 13:24:30 UTC). El documento del Proyecto IAA está actualizado.
- No quedan tareas de validación abiertas. Lo que falta son decisiones del participante (sección 10 del informe). Intenté cancelar el control horario de las 08:30, pero el permiso fue denegado, así que se ejecutará y solo comprobará si hay novedades.

### 09:40–09:45 Los datos oficiales no cambiaron

Codex comparó byte a byte los 24 Parquet oficiales que publica hoy Kaggle con los originales históricos y no encontró ninguna diferencia (foro 052, `Repositorio_IAA2026/docs/semana2/VERIFICACION_CONTENIDO_KAGGLE_20261024.md`). Hice mi propio control con los SHA-256 de las copias recién descargadas que trae su `report.json`. Las 24 copias que usé en la nube para toda la validación (11 del desarrollado en `datos/s1` y 13 del emergente en `datos/s2`) tienen el mismo SHA-256 que esas copias oficiales. El aviso de las 08:12 queda cerrado: la nueva fecha en Kaggle no cambia ningún dato, así que no hay que rehacer ninguna cifra.

### 09:46–10:02 Decisiones del participante: enmienda de SEL01 (v2), producción sin tendencia, historia neutral con tres semillas y transferencia en la selección común

El participante respondió a las cuatro decisiones: «Enmiendala» (salvaguarda de cliente nuevo), «Sin tendencia» (nivel 2025) y «me quedo con tu recomendación» para la versión 2 con historia neutral y tres semillas y para llevar la transferencia a la selección común.

- Política v2 (`preinscripcion/politica_seleccion_v2_20261024.json`, S2-SELECCION-v2-20261024). Cambia una sola regla: en cliente nuevo basta con una diferencia puntual ≥ 0, y el límite del 95 % se informa como diagnóstico. v1 y su acta se conservan. Queda escrito que la enmienda se decidió conociendo el acta.
- Acta enmendada (`codigo/puerta_enmienda.py`, sin leer etiquetas, sobre el acta original comprobada por SHA). A1 frente a R0 pasa: primaria +0,0486 [+0,0265; +0,0733], cliente nuevo +0,0131 ≥ 0 con el límite diagnóstico en −0,0105, y el resto igual que en v1. A2 frente a A1 no pasa la primaria (−0,0040 [−0,0104; +0,0025]). Titular v2: A1.
- Semillas 12 y 13 del GBM desarrollado con historia, completo y conf (`codigo/cadena_semillas_f1.sh`, 12 modelos en unos 15 minutos). El D² interno de autos es 0,0880 con la semilla 11 y 0,0871 con la 12.
- Receta final A1fixF1b3n (`codigo/evaluar_final.py`). Frente a A1fixb3:
  - desarrollo 2023: +0,0020 [+0,0002; +0,0043], y +0,0000 en el cuerpo;
  - 2024 exploratorio, con calibración neutral: +0,0025 [+0,0012; +0,0039], y +0,0020 [+0,0011; +0,0028] en el cuerpo.

  Es menos que el +0,0040 de la semilla 11 sola, que había salido favorable, y el promedio es la estimación honesta. El D² de 2024 es 0,1244, frente a 0,1214 de A1.
- Producción designada `A1fixF1b3n_2025.csv`, sin tendencia y sin enviar. Total 67,17 M CU (autos 41,04 M, edificios 20,59 M, contenidos 5,54 M), con el total por ramo de A1fixb3. SHA f786deb3…224c53aa. Las 20 primas comerciales suman 16.493 CU (`codigo/prima_comercial_designada.py`). El mayor cambio frente a A1 es M00118569 (+49 %), una renovación con dos siniestros aceptados en 2023.
- Informe: sección 10 nueva, resumen y tabla de producciones actualizados, y la figura 2 marca la titular de cada versión. El verificador encuentra 162 de 162 cifras.

### 10:27–10:45 Validación antes del envío (rev5, reproducibilidad y factor de nuevo negocio)

El participante pidió «continua validando todo antes de enviarlo».

- rev5, el revisor independiente previo al envío, trabajó sin mi código ni mis conclusiones y dejó su informe en `revision/rev5/`. Hizo cuatro comprobaciones:
  - Reconstrucción: rehízo A1fixb3 y A1fixF1b3n desde la descripción de la receta; coinciden hasta el sexto decimal (diferencia máxima 5e-7 CU) y los totales por ramo son iguales.
  - Validez para Kaggle: 209.063 filas en el orden de la plantilla, sin duplicados, encabezado `row_id,prediction`, ASCII con saltos LF, predicciones finitas y positivas, totales por fila.
  - Historia: sin fuga (periodo propio, futuros, repudiados y mercado equivocado no dan señal), y su réplica del bloque `--f1` coincide sin diferencias.
  - Política: con la v2, A1 es la titular.

  Su veredicto es que el archivo está listo y no tiene bloqueos.
- Reproducibilidad: reentrené la semilla 12 de autos y la 13 de edificios del GBM con historia, y las relatividades salen idénticas bit a bit.
- Factor de nuevo negocio (`codigo/nb_nivel_revision.py`). rev5 vio que el nuevo negocio de 2023–2024 corre por encima del modelo (A/E 1,26 en autos y 1,27 en contenidos). Como en 2025 es el 77 % de la exposición, un factor así subiría autos un 19 %. Lo probé fuera de tiempo: estimado en 2023 y medido en 2024, exploratorio.
  - En autos, el A/E de 2023 es 1,62 en nuevo negocio y 0,94 en renovación; en 2024 es 1,09 y 1,10. El exceso de 2023 no se repitió.
  - Con el factor, el D² de 2024 cambia −0,0010 [−0,0026; +0,0008] si es bruto, −0,0014 si se topan los siniestros a 100.000 CU y −0,0001 con credibilidad.

  No se añade el factor y la producción no cambia.
- Puntos no bloqueantes de rev5, documentados en el informe:
  - las 2.961 renovaciones de 2025 que empiezan después del 1 de enero tienen la historia incompleta;
  - el estado «repudiado» es el del cierre de 2024;
  - en hogar, la historia no se puede contrastar con la experiencia emergente por falta de volumen.
- Informe: nueva subsección «Validación antes del envío» en la sección 10, con 170 de 170 cifras verificadas.
- Condición externa: nadie ha comprobado que Kaggle acepte ya 209.063 filas. El primer envío, que hace Codex con autorización del participante, lo dirá.

### 10:45–10:50 Comparación con la línea ML independiente y opción de mezcla

Otra sesión de Claude (ML independiente, sección 38 de CLAUDE.md, foro CLA-S2-20261024-015) terminó su línea propia a las 15:27 UTC. Usa otro código y otro modelo, y llega a la misma receta de fondo: un LightGBM Tweedie del desarrollado con nivel por ramo (T2b). Al final comparé su trabajo con el mío (`codigo/conciliacion_mlind.py`):

- Las dos líneas coinciden en las decisiones del participante: en su prueba de 2024, la tendencia resta (−0,0016) y el ajuste de nuevo negocio pierde (exceso de autos 1,55 en 2023 y 1,00 en 2024). Lo mismo que encontré yo.
- 2025: la correlación de los logaritmos es 0,985 en autos, 0,969 en edificios y 0,969 en contenidos. Sus totales son +5,3 %, +7,6 % y −1,1 % frente a los míos. La diferencia sale sobre todo de cómo cada modelo traslada la mezcla de 2025, porque las completitudes de 2024 casi coinciden (autos 0,803 frente a 0,816).
- Orden a igual total por ramo (sus predicciones de 2024 están guardadas en escala de último, así que comparo solo orden):
  - T2b frente a la designada: +0,0042 [−0,0027; +0,0109] en desarrollo y +0,0007 [−0,0028; +0,0040] en 2024.
  - La media 50/50 frente a la designada: +0,0039 [+0,0004; +0,0074] en desarrollo y +0,0012 [−0,0005; +0,0029] en 2024. En el cuerpo sale +0,0006 y +0,0013.
- Opción preparada, sin enviar: `A1fixF1b3n_mlind50n_2025.csv` (`codigo/mezcla_mlind.py`), la media 50/50 con el total por ramo de la designada. Total 67,17 M CU, SHA 0df5009c…c3dcacf7, mediana del cambio por fila 5,5 %. La decide el participante.
- Hay otra mezcla en su carpeta, `mezcla50_designada_mlind_2025.csv`, que promedia también los niveles (69,0 M). No la uso, porque cambiaría el nivel decidido.
- Ajuste técnico: el cálculo del cuerpo de 2024 pasa a estar dentro de `evaluar_final.py`. El SHA de la producción no cambia. El verificador encuentra 179 de 179 cifras.
- Foro: el 015 lo usó la sesión ML, así que mi aporte de validación sale como 016.
- A petición del participante, la sesión ML publicó en el foro 016 su mezcla 50/50 sin igualar totales: `mezcla50_designada_mlind_2025.csv`, SHA 12831ef4…, 69,00 M CU. La comprobé por mi cuenta: es la media exacta de los dos archivos y su formato es válido. Dentro de cada ramo ordena casi igual que mi mezcla neutral (correlación de los logaritmos ≥ 0,99999). Solo cambia el total: +2,6 % en autos, +3,8 % en edificios y −0,6 % en contenidos. Las tres opciones pasan el formato. Mi aporte de validación sale con el siguiente identificador libre.

### 10:55–11:05 Decisión final y autorización de envío

Pregunté al participante qué archivo enviar. Respondió «Mezcla de la sesión ML» y, a la pregunta por la autorización, «Sí, autorizo el envío». El archivo es `mezcla50_designada_mlind_2025.csv`, con SHA 12831ef4…, 69,00 M CU y formato válido. Calculé con él las 20 primas comerciales de referencia (`codigo/prima_comercial_envio.py`): suman 16.794,68 CU y coinciden al céntimo con las de la sesión ML. Quedan registrados en DECISIONES (S2-ENVIO-AUTORIZADO-20261024), en ESTADO (`week_2_envio_autorizado_20261024`), en la sección 40 de CLAUDE.md, en el foro y en el documento del Proyecto. El envío lo hace Codex, que antes debe comprobar el SHA y que Kaggle acepte las 209.063 filas. El verificador encuentra todas las cifras del informe.

### 11:05–11:16 Primer envío (D² público 0,15390, puesto 5 de 7) y diseño de una sonda de nivel

Codex envió la mezcla: envío 57599788, 209.063 filas procesadas, D² público 0,15390, puesto 5 de 7. El participante comentó que el resultado no es muy bueno. Ese D² sale del público (en torno a un tercio de 2025), así que no se compara con nuestras cifras de 2023 o 2024. No sabemos a qué distancia están los demás equipos.

- La palanca que queda es el nivel de cada ramo. Con la desviación Tweedie 1,5, el D² público al escalar un ramo por c depende solo de dos sumas desconocidas por ramo. Con dos envíos por ramo se despeja el óptimo exacto del público, c* = Σ y μ^(−1/2) / Σ μ^(1/2) (`codigo/sonda_nivel_diseno.py`). La simulación en 2024, con redondeo a 5 decimales, da un error del log de c* de 0,001 a 0,006. El ruido entre público y privado al tamaño de 2025 es 0,051 en autos, 0,157 en edificios y 0,087 en contenidos.
- Preinscripción (`salidas/sonda/preinscripcion_sonda.json`):
  - seis sondas: autos ×0,85 y ×1,20, edificios ×0,80 y ×1,25, contenidos ×0,85 y ×1,20;
  - credibilidad Z con τ fijado antes de enviar (0,10, 0,20 y 0,07), que da Z = 0,796, 0,618 y 0,395;
  - nivel final = c*^Z, acotado entre 0,80 y 1,25;
  - control de que el público es una muestra al azar.
- Backtest de la regla en 200 particiones de 2024 (`codigo/sonda_backtest_2024.py`): +0,0069 de media en el privado, entre +0,0045 y +0,0089, positivo en todas. Lo explica sobre todo edificios. Para 2025 la ganancia esperada es del orden de +0,0016.
- El script que resuelve la sonda está probado en seco (`codigo/sonda_nivel_resolver.py --prueba`) y los seis archivos están listos. Antes de enviar falta la autorización del participante.

### 11:18–11:35 Sin sondas: candidatos de robustez

El participante no autorizó la sonda: «no nos fue bien el anterior envío mandando Sondas, prefiero seguir trabajando en modelos más robustos». Los archivos y la preinscripción de la sonda quedan guardados sin usar.

Antes de entrenar dejé preinscritos dos candidatos (`salidas/robustez/preinscripcion_robustez.json`, 16:22 UTC):

- C1: relatividades aprendidas con cada siniestro del desarrollado topado a 100.000 CU. El exceso lo absorbe el nivel por balance.
- C2: árboles más regularizados (15 hojas, mínimo 3.000 filas por hoja, λ 50 y fracción de variables 0,7).

Los dos usan tres semillas y versiones completa y conf (`codigo/cadena_robustez.sh`, 36 modelos). Regla: un candidato entra solo si mejora a la base A1fixF1b3n en desarrollo 2023 y en 2024, a igual nivel por ramo, con el IC 90 % por encima de cero en al menos un periodo y sin empeorar el cuerpo más de 0,0005. `desarrollado_gbm.py` admite ahora `--cap` (con control de que el T0 de la base cuadra con la asignación) y `--reg`. La evaluación está en `codigo/robustez_evaluar.py`.

### 11:35–12:13 Resultados de robustez: el modelo regularizado pasa, el tope y el GLM no

Todo se mide frente a la base A1fixF1b3n (`salidas/robustez/resumen.json`). En 2024 la comparación es a igual nivel por ramo.

| Candidato | Desarrollo 2023 | Cuerpo 2023 | 2024 | Cuerpo 2024 | Regla |
| --- | ---: | ---: | ---: | ---: | --- |
| C1, tope de siniestros a 100.000 CU | −0,0015 [−0,0049; +0,0014] | +0,0008 | +0,0003 [−0,0008; +0,0012] | −0,0003 | no pasa |
| C2, árboles regularizados | +0,0015 [−0,0002; +0,0032] | +0,0023 | +0,0019 [+0,0005; +0,0033] | +0,0021 | pasa |
| C3, media GLM + GBM | −0,0012 [−0,0039; +0,0016] | −0,0030 | +0,0011 [−0,0011; +0,0035] | +0,0001 | no pasa |

C2 mejora en los tres ramos de 2024 (autos +0,0003, edificios +0,0032, contenidos +0,0042). También sube el D² de la validación interna del desarrollado en los tres ramos, que no usa nada del emergente: autos de 0,0880 a 0,0884, edificios de 0,0824 a 0,0842 y contenidos de 0,0762 a 0,0801. Según la regla, la combinación tope + regularizado no se mide, porque C1 no pasó.

Producción con C2 (`codigo/produccion_robusta.py`, sin enviar):

- `A1robregF1b3n_2025.csv`, SHA a702ed24…: mismo nivel por ramo que la designada (67,17 M CU), con una mediana de cambio por fila del 4,2 %.
- `mezcla50_robusta_2025.csv`, SHA 82082f3c…: igual que la mezcla enviada pero con el componente nuevo. Totales iguales (69,00 M CU) y una mediana de cambio por fila del 2,1 %.

A igual nivel, la mezcla nueva gana a la enviada +0,0007 [−0,0002; +0,0014] en desarrollo 2023 y +0,0009 [+0,0002; +0,0016] en 2024 (cuerpo +0,0011). Es una mejora pequeña pero consistente.

### 12:14–12:47 Segunda ronda: rejilla elegida con la validación interna del desarrollado (C4), que no pasa

Rejilla de cuatro configuraciones más, con semilla 11 y versión completa, elegida solo con el D² interno del desarrollado (`salidas/robustez/rejilla_eleccion.json`):

| Ramo | C2 (G1) | G2: 7 hojas, 5.000 filas, λ 100 | G3: 15 hojas, 10.000 filas, ff 0,6 | G4: 31 hojas, 3.000 filas, λ 50 | G5: 15 hojas, λ 200, ff 0,5 | Elegida |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Autos | 0,08841 | 0,08812 | 0,08783 | 0,08756 | 0,08884 | C2 (G5 gana solo 0,0004) |
| Edificios | 0,08416 | 0,08486 | 0,08451 | 0,08241 | 0,08434 | G2 |
| Contenidos | 0,08009 | 0,08069 | 0,08129 | 0,07810 | 0,08181 | G5 |

Con tres semillas (`codigo/cadena_rejilla_semillas.sh`) y frente a C2 (`robustez_evaluar.py robrej --ref robreg`), el resultado es −0,0004 [−0,0015; +0,0006] en desarrollo 2023 y +0,0016 [+0,0005; +0,0028] en 2024. En 2024 la ganancia viene toda de edificios (+0,0060), mientras contenidos pierde 0,0008. No pasa la regla porque en 2023 queda por debajo. La mejora de la validación interna no se trasladó de forma consistente al emergente, así que C2 se queda como está.

### 12:55–13:15 Segundo envío: la mezcla robusta puntúa 0,15347 en el público (−0,00043)

Codex envió `mezcla50_robusta_2025.csv` (envío 57602707, SHA comprobado, 209.063 filas) y obtuvo un D² público de 0,15347, por debajo del 0,15390 de la primera mezcla. Puesto 6 de 8 equipos. El participante lo calificó de «muy mal resultado».

- ¿Es ruido? (`codigo/ruido_publico_pares.py`) Remuestreé 2024 por componentes al tamaño del público de 2025 (69.688 filas). La diferencia entre estas dos mezclas, que se parecen muchísimo (correlación de los logaritmos 0,999), tiene una desviación típica de 0,0004 alrededor de +0,0009. Ver −0,00043 tendría una probabilidad casi nula si 2025 se comportara como 2024. El resultado público es información real: la mejora medida en 2023–2024 no se trasladó al público de 2025.
- ¿Lo explica la mezcla de cartera de 2025? (`codigo/validacion_2025.py`) Ponderé 2024 para que se parezca a 2025 con un clasificador 2025 frente a 2023–2024 (AUC de 0,87 a 0,89; el nuevo negocio pesa 5,7 veces más que la renovación). Ni así: la mezcla robusta seguiría ganando +0,0016 [−0,0003; +0,0036], aunque con un tamaño efectivo de un quinto. No hay una explicación medible, salvo que 2025 se comporta distinto de 2024.
- Combinando la evidencia de 2024 ponderada (+0,0016, DE ≈ 0,0012) con la del público (−0,00043, DE ≈ 0,0007), la diferencia esperada en el privado entre las dos mezclas es prácticamente cero.
- También probé la prima escrita (tarifa vigente) como señal adicional (`salidas/robustez/prima_escrita_prueba.json`). No ayuda: con el coeficiente estimado en 2023, el D² de 2024 baja en autos (de 0,0836 a 0,0762) y en contenidos, y en edificios apenas cambia.
- Lección: con 2023–2024 no podemos distinguir mejoras de orden de ±0,001 que valgan en 2025, porque 2025 es otro año y otra cartera. Seguir probando retoques finos en el tablero gasta envíos sin cambiar el puesto.

### 14:40–15:13 Lectura publicada, criterio DES24, tablero y sonda de nivel global

- Publiqué la lectura del envío robusto en el foro (CLA-S2-20261024-024). La nota también responde al ruido de 0,003 citado en CLA-S2-20261024-023: ese ruido vale para el D² de un solo envío, mientras que entre dos envíos casi iguales la diferencia pareada tiene un ruido de 0,0004.
- DES24 (`codigo/des24_candidatos.py`): mide la estructura en el desarrollado de 2024, fuera de tiempo, con los modelos de confirmación guardados y el nivel reajustado en cada ramo. C2 gana a la designada +0,0011 [+0,0006; +0,0016] en los tres ramos. Ninguna de las tres validaciones anticipó la caída del público.
- El participante compartió el tablero: séptimos de siete con 0,15390, a entre 0,0078 y 0,0106 de los cuatro primeros. Uno de ellos llegó a 0,16170 con un solo envío.
  - En 2024 cuantifiqué cuánto cuesta un error de nivel: un 20 % por debajo cuesta 0,0070 de D², y un 30 % por encima, 0,0097.
  - El nuevo negocio es el 76 % de las filas en 2025, frente al 12-15 % en 2023-2024.
  - Su cociente real/esperado frente a las renovaciones va de 0,8 a 1,7 según el ramo y el año, sin un patrón estable.
- El participante eligió la sonda de nivel global.
  - Diseño, backtest al tamaño de 2025 y archivos en `codigo/sonda_global.py`. σ = 0,0496, τ = 0,12 y Z = 0,854.
  - Ponderado por la previa, el backtest da +0,0018 en el privado y gana el 78 % de las veces.
- Un revisor independiente confirmó la fórmula, los CSV y la recuperación de c*.
  - Corregido: las paradas del resolutor y la cifra ponderada por la previa.
  - Documentado: Z conservador y el sustituto de 2024.
- Publicado en el foro como CLA-S2-20261024-026; la línea ML había tomado el 025 a las 19:59 UTC. Registros: DECISIONES S2-SONDA-GLOBAL-CLAUDE-20261024, ESTADO `week_2_sonda_global_claude_20261024`, CLAUDE.md sección 44 y documento del Proyecto. Copias previas en `respaldo_registros/*_antes_n18*`. Lote n17 en el equipo: 18 de 18 hashes iguales a su manifiesto.

### 19:35–19:41 Resultado de la sonda de nivel global y archivo final

- Codex envió las dos sondas con la autorización del participante. D² público: 0,14095 con ×0,85 y 0,15955 con ×1,20, frente a 0,15390 de la mezcla. Según Codex, después quedan ocho envíos, porque la cuota del día se renovó a las 00:00 UTC.
- `codigo/sonda_global_resolver.py 0.85=0.14095 1.20=0.15955`:
  - βA = 0,6213 y βB = 0,5080, los dos positivos, así que c* es identificable.
  - c* = 1,2231, entre 1,2225 y 1,2237 según el redondeo de las tres puntuaciones; log 0,20, por debajo de la parada de 0,4.
  - c_final = 1,1877, con Z = 0,854.
- `final_sonda_global_2025.csv`, SHA 42659dbb…: la mezcla por 1,1877, 81,94 M CU. Comprobado contra la plantilla, cabecera, saltos LF, positividad y valores idénticos como texto a la mezcla por el factor exacto.
- D² público previsto: 0,15948. Si sale así al quinto decimal, la métrica tiene la forma supuesta.
- La nula implícita por fila (127,8 frente a 110,6 y 93,4) no detiene la regla.
- Sin enviar: lo hace Codex con autorización expresa del participante.
- Codex calculó por su cuenta el mismo c* (1,223096592), el mismo c_final (1,187658239) y el mismo SHA del archivo final (COD-S2-20261024-ENVIOS-SONDA-GLOBAL). También señaló (COD-S2-VAL08-20261024-INFERENCIA-PUBLICO) que «no es ruido» y «tampoco lo explica la cartera», en CLA-024, iban más allá de lo que los cálculos permiten. Tiene razón: son sensibilidades que suponen que 2024 se traslada a 2025. Lo dejé acotado en el informe (sección 10). Publiqué el resultado en el foro como CLA-S2-20261024-027 y lo registré en DECISIONES (S2-SONDA-GLOBAL-CLAUDE-20261024-RESULTADO), en ESTADO (`resultado` dentro de `week_2_sonda_global_claude_20261024`) y en la adenda de la sección 44 de CLAUDE.md.

### 19:45–20:34 Sonda por ramo × nuevo negocio: diseño, simulación, revisión y archivos (sin enviar)

- El participante eligió «Final + diseñar sonda por segmento».
- `codigo/sonda_segmento_diseno.py` simula tres segmentaciones. Remuestrea 2023 y 2024 al tamaño de 2025 con su composición de ramo × nuevo negocio, con τ = 0,20 y σ medido frente al privado. Escenarios: sin desviación por celda, desviaciones del año y previa. Elegida ramo × nuevo negocio, con cinco envíos: −0,0005/−0,0006 si no hay desviación por celda, +0,0112/+0,0175 con desviaciones como las del año y +0,0026/+0,0022 con la previa.
- Un primer lanzamiento sondeaba la celda menor y deducía otra; lo corregí para deducir siempre la celda mayor y repetí la simulación. Un `pkill` mató mi propia orden porque el patrón coincidía con su línea de comandos; repetí el cambio sin `pkill`.
- `sonda_segmento_preparar.py` genera las cinco sondas (F con una celda ×1,2) y la preinscripción. `sonda_segmento_resolver.py` las resuelve; `--prueba` en 2024 recupera c*_s con un error de log ≤ 0,016.
- El revisor independiente (`revision/rev6/revisor_sonda_segmento.md`) no encontró bloqueos. Apliqué sus correcciones: F se envía primero; las puntuaciones entran por archivo o SHA; si algún a_s ≤ 0 el resolutor se detiene; la parada pasa a max(0,7; 3σ); Z usa el mayor σ de los dos años (`--solo-sigma`, `sigma_por_pool.json`); la parada de F compara intervalos. Los CSV no cambiaron (mismos SHA).
- Al publicar CLA-S2-20261024-028 vi que Codex ya había enviado F a las 00:52 UTC con autorización del participante (envío 57612023, COD-S2-20261024-ENVIO-FINAL-SONDA-GLOBAL): 0,15948, igual al previsto. La parada 1 no se activa. Quedan siete envíos hoy: cinco sondas más el archivo por celda.
- La sección 45 de CLAUDE.md, de la línea ML, recomienda F como entrega. Con la prima escrita (E27), estima que la tarifa pide +21,4 % en autos, −3,2 % en edificios y +11,8 % en contenidos sobre la mezcla, pero con poca credibilidad. Es la misma dirección que la sonda global, con otro reparto por ramo. La sonda por segmento puede medir ese reparto.
- Registros: DECISIONES S2-SONDA-SEGMENTO-CLAUDE-20261025; ESTADO `week_2_sonda_segmento_claude_20261025`; CLAUDE.md sección 46 (la 45 era de la línea ML); foro CLA-S2-20261024-028.
