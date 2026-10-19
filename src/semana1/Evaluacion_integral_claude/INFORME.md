# Evaluación integral de la estimación 2025 (Claude), noche del 17 al 18 de octubre de 2026

Este informe revisa de punta a punta la cadena que lleva de los datos a la predicción de 2025: datos y ajustes, exposición efectiva e IBNR, frecuencia y severidad por peligro, y metodología de modelado, validación, nivel, forma y mezcla. Cada afirmación lleva su medida y el script que la produce está en esta carpeta o en `../Modelos_claude/`. Las cifras de D² se calculan sobre importes con potencia 1,5. V23 entrena con 2021–2022, para en la mitad de calibración de 2023 y compara en la mitad de selección. V24 entrena con 2021–2023, usa las rondas de V23 × 1,15 y evalúa 2024. Las dos se miden contra el T0 observado al 30-12-2024.

## Resumen

Actualización del 18 de octubre por la tarde. La estimación propia vigente de Claude es `S21_claude_propio.csv` (SHA-256 `4e934f595ab7e64d4bcde0e50c5a0a676a2570f46748260a5b1b86c2523d211b`), sin ningún componente, total ni factor de Codex (secciones 4.7 a 4.9). Frente a S09b, el envío mixto que obtuvo 0,12889 en el público, mejora los tres ramos en V23 y en V24: agregado +0,00218 y +0,00255, con probabilidad de mejora 1,00 en los dos cortes en bootstrap por cliente; autos +0,00095 y +0,00283, edificios +0,00350 y +0,00203, contenidos +0,00345 y +0,00350. Los cambios que la explican son estructurales: la severidad de la frecuencia por peligro deja de ser constante y pasa a depender del capital asegurado en hogar y del valor y la antigüedad del vehículo en autos (S18); esa misma severidad se aplica después a un modelo aditivo de frecuencia en hogar (S20), y en contenidos la severidad incorpora covariables físicas fijadas de antemano, como el nivel de seguridad y los objetos de valor en el robo (S21). En el D² local de 2024 da 0,13807, frente a 0,13610 de A_G (+0,00198, IC95 por cliente [+0,00068; +0,00353]) y 0,13726 de H (+0,00082, [−0,00019; +0,00174]), cuyas metas se ajustan dentro de 2024. Frente a S20 la mejora es pequeña (+0,00007 en V23 y +0,00004 en V24), depende de los siniestros grandes y retrocede en la cohorte que empieza en el segundo semestre de 2024 (sección 4.9). En el público S21 obtuvo 0,12874, por debajo de S09b, y S22 obtuvo 0,12988, el mejor resultado público al cierre de la tarde (sección 4.11); S22 (`c21a02e1…3541b0`) es la misma mezcla sin la forma de hogar, cuya ganancia dependía de la cola, y su mejora frente a S09b se mantiene sin el 0,1 % superior en los dos cortes (sección 4.10). S20 (`98f62b88…9c3659`), S18 (`a97ad416…79e7e8`) y S16 (`65023125…40e012`) fueron las estimaciones propias anteriores; S14, descrito a continuación, sigue disponible como candidato de linaje mixto.

El candidato recomendado al cierre de la noche fue `S14_claude_cat4s_forma.csv` (SHA-256 `f22b0033f457858e90c4d9c1d838a71119a838cd99f960a1549379ee8ec8da28`, en `Envios/archivos/`). Mejora a S09b en los tres ramos, en V23 selección y en V24. S09b es el envío de Claude que Codex subió esta noche y que obtuvo 0,12889 en el público. Diferencias pareadas con bootstrap por cliente (`../Modelos_claude/robustez.py`):

| Ramo | S09b V23 / V24 | S14 V23 / V24 | Diferencia V23 (P de mejora) | Diferencia V24 (P de mejora) |
| --- | --- | --- | --- | --- |
| Autos | 0,09344 / 0,08877 | 0,09401 / 0,09016 | +0,00057 (0,82) | +0,00139 (0,95) |
| Edificios | 0,11513 / 0,11437 | 0,11684 / 0,11552 | +0,00171 (0,95) | +0,00115 (0,94) |
| Contenidos | 0,08797 / 0,09322 | 0,08900 / 0,09448 | +0,00103 (0,94) | +0,00127 (0,99) |
| Global | 0,14361 / 0,13552 | 0,14462 / 0,13674 | +0,00101 (0,99) | +0,00122 (0,999) |

Los cambios que explican la mejora son cuatro. El más importante es una calibración de forma que abre la dispersión de las tasas, con parámetros que coinciden entre V23 y V24 (sección 4.2). En autos entra un CatBoost de frecuencia por peligro y el CatBoost Tweedie pasa a promediar cuatro semillas; en contenidos entra un modelo de frecuencia por peligro con severidad modelada, y en edificios el LightGBM pasa a ser menos restrictivo (sección 4.4). En hogar la ganancia de la forma viene de la cola de siniestros grandes, que se concentra en los riesgos con tasa predicha más alta en los dos años; por eso S14 no pasa la prueba de Codex sin el 0,1 % superior (sección 4.5). Para medir ese efecto en el público queda `S14c_claude_cat4s_forma_autos.csv` (SHA-256 `7360c1a4d68b2bfa7d5f5e708c63b21967226189386601820ce16856e59c7318`), con los mismos componentes y forma solo en autos: V23 +0,00047 y V24 +0,00086 frente a S09b, positivo también sin la cola. El nivel de 2025 por ramo de S14 coincide con lo que dan las tendencias de severidad y frecuencia por peligro (sección 3), y la exposición efectiva diaria confirma que la mensual de D67 es adecuada en el total (sección 2). La revisión deja además tres hallazgos para quien siga:

- la severidad de lesiones corporales cae de golpe desde 2023, con un patrón que hace poco probable que sea solo desarrollo de reservas (hipótesis; una sola valoración no permite descartarlo);
- en las filas que empiezan en diciembre de 2024, la exposición efectiva diaria es entre un 17,8 % y un 24,0 % menor que la mensual (la mensual excede a la diaria entre un 21,7 % y un 31,6 %);
- las predicciones de los modelos regularizados y de las mezclas quedan demasiado concentradas.


## 1. Datos y ajustes

La matriz de trabajo es la F0 v1 de D68 (`Matriz_F0_claude/runs/f0_20261017T141732Z_65df7fca`), construida sobre la capa preparada vigente `preaudit_20261016T211816Z_817285a5`. Esa capa contiene ID01, EXP01, CAP01, CAT01, AGE01, DUP01, REN00 y PRE00. La F0 añade además el contrato de capital de D66 y la armonización t/w. El objetivo T0 por fila sale de la asignación única de D67: 160.432 siniestros aceptados y 741.156.868,43 CU. Fuera de los predictores quedan `customer_service_contacts`, que mide el siniestro del propio periodo; `renewal_decision`, que solo existe en entrenamiento; las marcas `audit_*` y los identificadores crudos. En autos se usan F0, F1, F2, F3 completo (sin `marketing_segment`, autorización del participante) y F4. En hogar se usan F0, F1, F2 y F4, más las siete variables de cliente F3 autorizadas en D80.

La composición de la cartera de 2025 es casi idéntica a la de 2024. Entre 2024 y 2025 el índice de estabilidad poblacional (PSI) de las variables principales no pasa de 0,022 en ningún ramo (`salidas/psi_2024_2025.json`). El valor más alto corresponde a la prima escrita (0,015 a 0,022), que refleja el ajuste general de tarifa; la prima relativa, que lo descuenta, queda en 0,0005 o menos. Los periodos cortos pesan lo mismo cada año: alrededor del 22 % en autos, el 19 % en edificios y el 20 % en contenidos entre 2022 y 2025, y también es estable la proporción de periodos que terminan antes de fin de año, por cambio a mitad de año, anulación o no renovación.

Hay un único cambio de soporte relevante, que Codex ya había señalado en D77. La historia previa de la póliza llega hasta 4 años en 2025, frente a un máximo de 3 en 2024: el 46,65 % de las filas de autos de 2025 supera los 3 años de exposición previa. Los árboles tratan esos valores como el tramo superior que vieron en entrenamiento. Codex probó en D78 ventanas fijas de 365 y 730 días y no mejoraron.

## 2. Exposición efectiva e IBNR

La exposición efectiva de D67 y D68 multiplica la exposición por la completitud de reporte en conteos estimada por meses. Para comprobarla recalculé la completitud por días (`completitud_diaria.py`). Primero estimé la distribución del retraso de reporte de cada peligro con un estimador de producto para datos truncados por la derecha. Después promedié, sobre los días cubiertos de cada fila, la probabilidad de que un siniestro ocurrido ese día ya estuviera reportado el 30-12-2024.

| Ramo | Completitud 2024 mensual (D68) | Completitud 2024 diaria | Razón diaria/mensual, filas que empiezan en diciembre |
| --- | --- | --- | --- |
| Autos | 0,7947 | 0,7904 | 0,760 |
| Edificios | 0,9259 | 0,9305 | 0,822 |
| Contenidos | 0,9690 | 0,9688 | 0,818 |

El total apenas cambia. La diferencia está en las filas que empiezan en diciembre: con la razón diaria/mensual de la tabla (0,760, 0,822 y 0,818), la exposición efectiva diaria de esas filas es un 24,0 %, un 17,8 % y un 18,2 % menor que la mensual, o, con la diaria como base, la mensual la excede en un 31,6 %, un 21,7 % y un 22,2 %. La mensual sale más alta porque supone que un siniestro de diciembre ha tenido el mes entero para reportarse. (Corrección del 18 de octubre: la versión anterior decía «entre un 18 % y un 24 % más» sin aclarar la base; hallazgo MOD-007 de la revisión de Codex en `foros/FORO.md`.) Para decidir cuál de los dos cálculos se ajusta mejor a lo observado, reescalé las predicciones de 2024 del candidato S11 con la completitud diaria, conservando su total. El D² de V24 mejora en los tres ramos: autos +0,00017, edificios +0,00011, contenidos +0,00024 y global +0,00016. La completitud diaria es más exacta. Su efecto sobre 2025 es pequeño, porque solo cambia el peso de unas pocas filas de entrenamiento de finales de 2024, y por eso no justifica reentrenar todos los componentes. Queda como mejora documentada para el constructor de matrices.

La completitud en coste coincide con la de conteos en casi todos los peligros, es decir, los siniestros tardíos no son más caros (`severidad_por_retraso.py`). Hay dos excepciones moderadas: lesiones corporales de autos (0,543 en coste frente a 0,561 en conteos, un 3,3 % menos) y hundimiento de edificios (0,675 frente a 0,690). El IBNR de coste de lesiones de 2024 queda así algo por debajo de lo que dice el chain-ladder de conteos, del orden de un 3 % del coste de ese peligro.

Aparece un hallazgo que no parece de desarrollo: la severidad de lesiones corporales cae de golpe al empezar 2023. La mediana por semestre de ocurrencia está entre 13.029 y 13.478 CU de 2021 a 2022 y entre 8.641 y 10.525 CU de 2023 a 2024. Por trimestre, la mediana pasa de 13.916 en 2022T4 a 10.187 en 2023T1, con la misma proporción de expedientes abiertos (36 % y 35 %). Dentro de 2023, la severidad no crece con la antigüedad del reporte ni difiere entre cerrados y abiertos de la misma edad. Esa combinación hace poco probable que el escalón se deba solo a insuficiencia de reservas y es compatible con un cambio de régimen desde 2023. Es una hipótesis: con una sola valoración, sin trayectorias de pagos ni de reservas, no se puede descartar un desarrollo particular de las reservas ni identificar el mecanismo (corrección del 18 de octubre a raíz del hallazgo MOD-006 de la revisión de Codex en `foros/FORO.md`). Ningún otro peligro muestra un escalón: todos siguen tendencias suaves (sección 3).

## 3. Frecuencia y severidad

`tendencias.py` mide, por peligro, la frecuencia sobre la exposición efectiva del peligro (2021–2024) y la severidad media (tendencia con 2021–2023, porque 2024 sigue inmaduro en importes).

| Ramo | Peligro | Frecuencia 2021 → 2024 | Tendencia anual de frecuencia | Severidad 2021 → 2023 | Tendencia anual de severidad 2021–2023 |
| --- | --- | --- | --- | --- | --- |
| Autos | own_damage | 0,06373 → 0,05964 | -2,8 % | 1.727 → 1.874 (2024: 2.039) | +4,2 % |
| Autos | third_party_prop | 0,04351 → 0,04058 | -2,6 % | 3.284 → 3.821 (2024: 4.130) | +7,9 % |
| Autos | bodily_injury | 0,01144 → 0,01047 | -2,5 % | 21.451 → 23.308 (2024: 17.829) | +4,2 % |
| Autos | theft | 0,00787 → 0,00767 | -0,3 % | 6.074 → 6.663 (2024: 6.560) | +4,8 % |
| Autos | glass_hail | 0,01900 → 0,02066 | +3,0 % | 945 → 1.144 (2024: 1.191) | +10,0 % |
| Edificios | storm | 0,01259 → 0,01309 | +2,1 % | 3.082 → 3.622 (2024: 3.876) | +8,5 % |
| Edificios | flood | 0,00394 → 0,00366 | -2,8 % | 28.504 → 32.799 (2024: 34.946) | +7,3 % |
| Edificios | escape_of_water | 0,01759 → 0,01788 | +0,5 % | 5.133 → 5.964 (2024: 6.489) | +7,8 % |
| Edificios | subsidence | 0,00201 → 0,00293 | +13,7 % | 22.105 → 23.379 (2024: 27.130) | +2,8 % |
| Edificios | fire | 0,00168 → 0,00210 | +6,8 % | 54.347 → 50.509 (2024: 50.894) | -3,6 % |
| Edificios | accidental_damage | 0,00621 → 0,00681 | +2,5 % | 1.174 → 1.167 (2024: 1.286) | -0,4 % |
| Contenidos | theft | 0,01236 → 0,01342 | +2,6 % | 3.492 → 3.634 (2024: 3.976) | +2,1 % |
| Contenidos | escape_of_water | 0,00900 → 0,00953 | +1,8 % | 2.585 → 2.763 (2024: 2.812) | +3,3 % |
| Contenidos | accidental_damage | 0,01538 → 0,01579 | +1,4 % | 763 → 784 (2024: 823) | +1,4 % |
| Contenidos | flood | 0,00287 → 0,00250 | -2,7 % | 9.513 → 10.569 (2024: 10.928) | +5,6 % |

En tasa de coste por exposición efectiva, la tendencia anual es +1,1 % en autos, +8,0 % en edificios y +5,3 % en contenidos (`salidas/tendencias.json`). En autos la frecuencia baja alrededor de un 2,5 % al año en daños propios, terceros y lesiones, mientras la severidad de los peligros sin lesiones sube entre un 4 % y un 10 % al año. Lesiones rompe la serie: la severidad de 2021–2023 del cuadro (+4,2 %) mezcla los dos regímenes, y la tasa de autos de 2024 (571) queda por debajo de la de 2023 (603) por el escalón de 2023, no por falta de desarrollo. En edificios crecen a la vez la severidad (tormenta +8,5 %, inundación +7,3 %, escape de agua +7,8 %) y la frecuencia de hundimiento (+13,7 % al año) e incendio (+6,8 %). En contenidos el crecimiento es más suave y repartido.


Para contrastar el nivel de 2025 con un método actuarial independiente de los modelos, llevé el coste de 2021–2024 al nivel de 2025 peligro a peligro. La severidad sigue su tendencia log-lineal, con el escalón de 2023 en lesiones. La frecuencia sigue también su tendencia. Con todo eso se calcula la tasa de 2025 por unidad de exposición. El resultado coincide con el nivel de los candidatos con forma, cuyo nivel sale de los modelos con el factor de año siguiente; sin la forma en hogar (S14c, como S09b) el nivel de edificios queda un 3,6 % por debajo:

| Ramo | Tasa 2025 por tendencias (severidad y frecuencia) | S11 | S14 | S14c |
| --- | --- | --- | --- | --- |
| Autos | 586,4 | 588,3 | 586,3 | 586,3 |
| Edificios | 513,0 | 511,5 | 510,7 | 494,7 |
| Contenidos | 126,1 | 126,2 | 126,6 | 124,7 |

Llevar el objetivo al nivel del año antes de entrenar ("on-level", `onlevel.py`) también se probó como cambio de modelo. Corrige el nivel: el factor de año siguiente pasa a quedar cerca de 1. El orden de los riesgos, sin embargo, no mejora de forma consistente. Con el factor óptimo, en autos da +0,0007 en V23 y −0,0001 en V24; en edificios +0,0001 y +0,0003; en contenidos −0,0009 y −0,0001. Por eso no se adopta como objetivo de entrenamiento y se usa solo como contraste de nivel.

## 4. Metodología

### 4.1 Validación y escala

Las decisiones se toman con diferencias pareadas entre modelos sobre las mismas filas, primero en V23 selección y luego en V24. El nivel absoluto del D² oscila mucho por unos pocos siniestros grandes: el bootstrap de filas de V24 da ±0,0045, y ±0,005 en un subconjunto del 50 % como el público. Las diferencias entre modelos parecidos son mucho más estables (S04 − S03: +0,0013 ± 0,0003).

La relación entre V24 y el público se ajustó al principio como 0,0099 + 0,8644 × V24, con S01, S03 y S04, y predijo bien S07. Con S08 y S09b la respuesta del público a las mejoras recientes resulta mayor que esa pendiente: de S08 a S09b, V24 sube 0,00305 y el público sube 0,00357. S09b, que la escala situaba en 0,1270, obtuvo 0,12889. Por eso, para los candidatos nuevos conviene leer la ganancia pareada frente a S09b más que el valor que da la recta.

### 4.2 Calibración de forma

Las predicciones de los tres ramos salen demasiado concentradas. Las razones son el promedio de modelos, la regularización fuerte de los árboles (hojas pocas y grandes) y la mezcla con el S08 de Codex. Para corregirlo se reescribe cada predicción como mu' = e (e/ē)^(b−1) g (r/g)^a. Aquí r = mu/e es la tasa, g y ē son medias geométricas del corte y e es la exposición efectiva en V23 y V24 y la nominal en 2025. El exponente a > 1 abre la dispersión de las tasas. El exponente b permite que el coste no sea proporcional a la duración del periodo. El factor de año siguiente fija después el nivel.

| Ramo | (a, b) óptimos en V23 | (a, b) óptimos en V24 | Ajustado en un año, ganancia en el otro | Parámetros usados en S12 a S14 |
| --- | --- | --- | --- | --- |
| Autos | (1,091; 0,966); a solo 1,095 | (1,081; 0,849); a solo 1,097 | a solo: +0,00044 en V24 y +0,00041 en V23 | (1,09; 0,95) |
| Edificios | (1,076; 1,159) | (1,083; 1,122) | (a, b): +0,0009 en V24 y +0,0012 en V23 | (1,08; 1,14) |
| Contenidos | a solo 1,043 (b no coincide entre años) | a solo 1,091 | a solo: +0,0006 en V24 y +0,0001 en V23 | (1,07; 1) |

Los óptimos coinciden entre años en el exponente de la tasa en los tres ramos y en el de la exposición en edificios. En autos los dos años piden b < 1: los periodos cortos cuestan algo más por unidad de exposición que lo proporcional. Se usa 0,95, cerca del valor de V23 y lejos del más extremo de V24. En contenidos b no coincide entre años y se deja en 1. Los parámetros salen de la media de los óptimos, así que V24 deja de ser una comprobación ciega para la forma. Por eso se informa también la prueba cruzada: ajustar en un año y medir en el otro.

### 4.3 Componentes y mezcla

| Ramo | Componentes de S14 | Peso | V23 selección | V24 (factor de V23) |
| --- | --- | --- | --- | --- |
| Autos | CatBoost Tweedie F01234 (profundidad 6, tasa 0,05, tope 15.000, cuatro semillas) | 0,4 | 0,09401 (mezcla) | 0,09016 (mezcla) |
| | CatBoost Poisson por peligro × severidad media del peligro | 0,4 | | |
| | LightGBM Tweedie F01234 y LightGBM reducido | 0,1 y 0,1 | | |
| Edificios | LightGBM F0124 + 7 F3, `min_data_in_leaf` 1000 | 0,5 | 0,11684 (mezcla) | 0,11552 (mezcla) |
| | Stack S08 de Codex | 0,5 | | |
| Contenidos | LightGBM F0124 + 7 F3 | 0,45 | 0,08900 (mezcla) | 0,09448 (mezcla) |
| | Frecuencia Poisson × severidad gamma por peligro | 0,30 | | |
| | Stack S08 de Codex | 0,25 | | |

Antes de mezclar, cada componente se reescala al total medio ponderado de los componentes de Claude en cada corte, usando solo predicciones; así los pesos actúan sobre relatividades. Mezclar las dos líneas de trabajo rinde sobre todo en edificios, donde la mezcla supera a las dos por separado en V23 y en V24. En autos el S08 de Codex resta en cualquier peso, porque no usa F3.

### 4.4 Pruebas de esta noche

| Prueba | V23 selección | V24 | Decisión |
| --- | --- | --- | --- |
| Calibración de forma por ramo | Mejora en los tres ramos | Autos +0,0011, edificios +0,0009, contenidos +0,0007 frente a S09b | Adoptada (S11, S12) |
| Frecuencia × severidad modelada en contenidos (gamma por peligro con 1.500 positivos o más) | Sola 0,0878 frente a 0,0848 del Tweedie; en la mezcla +0,0005 | Sola 0,0906 frente a 0,0928; en la mezcla, sustituyendo a la severidad constante, +0,0006 | Adoptada en contenidos (S12) |
| Misma estructura en edificios | Sola 0,1088 | — | No suma en la mezcla |
| Edificios con `min_data_in_leaf` 1000 | +0,0007 | +0,0004 | Adoptada (S12) |
| Edificios con más hojas, sin L2 o tasa 0,01 | −0,0017 a +0,0003 | −0,0023 a +0,0002 | No |
| Contenidos con menos o más restricción | −0,0022 a 0 | −0,0010 a +0,0004 | Se queda la vigente |
| CatBoost frecuencia por peligro en autos | Sola 0,0918 frente a 0,0901 de LightGBM; en la mezcla (CatBoost Tweedie 0,4, CatBoost frecuencia 0,4, dos LightGBM 0,1 cada uno) +0,00012 | Sola 0,0886, igual que el CatBoost Tweedie; en esa mezcla +0,00038 | Adoptada en autos (S13) |
| CatBoost frecuencia por peligro en edificios, con las siete F3 | Sola 0,1052; en la mezcla con peso 0,1, +0,00028 | Sola 0,1048; en la mezcla con peso 0,1, +0,00025 | Pequeña y coherente en los dos cortes; entra en el candidato final de la noche |
| La misma frecuencia CatBoost en contenidos | Sola 0,0752; en la mezcla con peso 0,1, +0,00036 | Sola 0,0758; en la mezcla con peso 0,1, −0,00022 | No: los cortes no coinciden |
| Dos semillas más del CatBoost Tweedie de autos | Sin cambio (la selección es un único modelo) | El par nuevo da 0,08795 frente a 0,08864 del primero; las cuatro, 0,08841; mezcla de autos 0,09016 frente a 0,09025 | Adoptada (S14): menos varianza en 2025; la diferencia entre pares muestra el ruido de semilla |
| Restricciones monótonas en autos | +0,0001 | −0,00055 | No |
| Variables de cambio respecto del periodo anterior | Autos −0,0010, edificios −0,0029, contenidos −0,0029 | −0,0011, −0,0003, −0,0006 | No |
| Variables de fin de periodo (fin anticipado, mes de fin) | Autos −0,0004, edificios +0,0002, contenidos −0,0005 | −0,0004, +0,0003, −0,0008 | No |
| Objetivo llevado al nivel del año ("on-level") | Autos +0,0007, edificios +0,0001, contenidos −0,0009 (con factor óptimo) | −0,0001, +0,0003, −0,0001 | Solo como contraste de nivel |
| Red neuronal Tweedie con embeddings | Autos 0,0859, edificios 0,1116, contenidos 0,0774 | 0,0817, 0,1007, 0,0862 | No (solo +0,0007 en V24 de contenidos con peso 0,1) |
| Reparto del exceso de autos por frecuencia de lesiones o por cobertura | Peor o inestable | Peor | No |
| Potencias Tweedie de entrenamiento 1,65 y 1,8 | Peor | Peor | No |

### 4.5 Robustez frente a la cola de siniestros grandes

Codex filtra sus candidatos con una prueba de sensibilidad: repetir la comparación sin el 0,1 % de filas con mayor pérdida observada. S12, S13 y S14 no la pasan en hogar. Antes de decidir conviene entender por qué (`../Modelos_claude/robustez.py` y `diagnostico_cola.py`; salidas en `salidas/diagnostico_cola.json` y en los `robustez_*.json` de `../Modelos_claude/experimentos/`).

En edificios, el 0,1 % superior son 93 filas en V23 selección y 184 en V24, casi todas de inundación, incendio y hundimiento, y concentra el 32 % y el 33 % de la pérdida. En contenidos pesa el 26 % y el 25 % (inundación y robo). La mitad de esas filas cae en el decil superior de tasa predicha por la mezcla sin forma: 47 de 93 y 77 de 184 en edificios, 58 de 94 y 82 de 188 en contenidos. En ese decil, el cociente entre pérdida real y esperada es 1,27 (V23) y 1,16 (V24) en edificios contando la cola, y 0,66 en los dos años sin ella. En contenidos es 1,20 y 1,03 con la cola y 0,57 y 0,58 sin ella. Los riesgos altos tienen una cola más pesada que el resto, y eso se repite en los dos años.

La forma con a > 1 sube las predicciones de ese decil, así que gana en la cola y pierde en el resto. Con los parámetros adoptados y cada predicción llevada a su nivel óptimo en el subconjunto, frente a la mezcla sin forma:

| Ramo | Todas las filas, V23 / V24 | Sin el 0,1 % superior, V23 / V24 |
| --- | --- | --- |
| Autos (1,09; 0,95) | +0,00046 / +0,00106 | +0,00043 / +0,00018 |
| Edificios (1,08; 1,14) | +0,00101 / +0,00080 | −0,00199 / −0,00170 |
| Contenidos (1,07; 1) | +0,00003 / +0,00041 | −0,00271 / −0,00160 |

En autos la forma gana con y sin cola. En hogar, la ganancia depende de la cola. La métrica es el D² sobre todas las filas, y una predicción que estime bien la media condicional tiene que incluir el riesgo de cola; la prueba sin cola penaliza por construcción una forma que lo recoge. A favor de que el efecto sea sistemático: la concentración de la cola en el decil alto se repite en los dos años, los óptimos de a coinciden entre años y el bootstrap pareado por cliente, que también remuestrea los siniestros grandes, da probabilidades de mejora de 0,92 y 0,96 en edificios. En contra: depende de unas 90 a 190 filas por ramo y año, menos en el subconjunto público, así que su resultado en Kaggle tendrá más varianza que el de una mejora repartida por toda la cartera.


### 4.6 Línea propia de Claude y dinámica de nivel de los componentes

El 18 de octubre por la mañana el participante pidió que Codex y Claude colaboren en `foros/FORO.md` con estimaciones nuevas independientes: ninguna línea incorpora predicciones, totales o factores de la otra sin una decisión explícita del participante. S09b, S14 y S14c conservan su linaje mixto, porque llevan el stack S08 de Codex en hogar. La primera estimación propia, `S15_claude_propio`, llevaba autos como S14, edificios con el LightGBM de `min_data_in_leaf` 1000 (0,8) y la frecuencia CatBoost por peligro (0,2), y contenidos con el LightGBM (0,3), la frecuencia por severidad gamma (0,4), la frecuencia CatBoost por peligro (0,1) y la red neuronal (0,2). Sin el stack de Codex, edificios pierde unas 0,0005 en V24 y queda igual en V23; en contenidos la red neuronal y la frecuencia CatBoost compensan la salida del stack.

La vigente, `S16_claude_propio`, cambia solo contenidos. Codex describió en el foro un GAM por peligro que en 2024 superaba a los árboles; Claude probó la misma idea con implementación propia (`frecsev2.py --aditivo`): frecuencia Poisson y severidad gamma por peligro con árboles de una sola división, sin interacciones. Es el mejor modelo de contenidos de la línea de Claude en los dos años (V23 0,08925 y V24 0,09352 solo, frente a 0,08775 y 0,09059 de la frecuencia con severidad gamma de árboles más profundos), y su nivel se mueve con el del LightGBM (razón 1,009 en V24 y 1,007 en 2025). Con la rejilla gruesa en pasos de 0,1, contenidos queda en LightGBM 0,3, red neuronal 0,1 y modelo aditivo 0,6, y sube de 0,08906 a 0,08979 en V23 y de 0,09494 a 0,09614 en V24. En edificios el modelo aditivo no suma. Los pesos salen de V23 y V24, ya consultados, así que no es validación nueva; lo que sostiene la elección es que la mejora aparece en los dos años por separado.

Al construirla apareció un problema de nivel. La mezcla reescala cada componente al total medio de los de Claude en cada corte, y eso supone que todos se mueven igual entre V24 y 2025. No es así:

| Componente frente al ancla del ramo | V23 | V24 | 2025 |
| --- | ---: | ---: | ---: |
| Autos: CatBoost frecuencia × severidad media / CatBoost Tweedie | 0,998 | 0,989 | 0,951 |
| Autos: LightGBM F01234 / CatBoost Tweedie | 0,989 | 0,990 | 0,983 |
| Edificios: CatBoost frecuencia × severidad media / LightGBM | 1,003 | 0,994 | 0,968 |
| Edificios: red neuronal / LightGBM | 1,037 | 0,954 | 1,015 |
| Contenidos: frecuencia × severidad gamma / LightGBM | 1,011 | 0,999 | 0,995 |
| Contenidos: CatBoost frecuencia × severidad media / LightGBM | 1,004 | 0,978 | 0,950 |
| Contenidos: red neuronal / LightGBM | 1,157 | 1,194 | 0,993 |

Los Tweedie de árboles y la frecuencia con severidad gamma se mueven juntos (±1 %). Las frecuencias con severidad media constante caen un 3 % a 4 % de V24 a 2025, y la red neuronal de contenidos sale un 10 % por encima del real en V24 y vuelve al nivel de los árboles en 2025. Con la red dentro de la referencia, el total de contenidos de 2025 bajaba a 18,2 millones (121,2 por unidad de exposición, un 3,9 % por debajo del contraste por tendencias). Desde S15 las redes aportan relatividades pero no nivel (`NIVEL_INESTABLE` en `mezcla3.py`): contenidos quedó en 18,8 millones en S15 (125,4 por unidad) y en 19,0 millones en S16 (126,6 por unidad, frente a 126,1 del contraste por tendencias). La razón de 2025 frente a V24 no necesita etiquetas, así que sirve de control previo para cualquier componente nuevo.

En la misma revisión se probaron, sin adoptarlos: CatBoost Tweedie de edificios con las siete F3 (sola 0,1117 en V23; en la mezcla propia no suma con ningún peso) y una rejilla del LightGBM de autos (`min_data_in_leaf` 1000, tasa 0,01, `feature_fraction` 0,8), que empeora V23 y V24 en las tres variantes (−0,0001 a −0,0018).

### 4.7 Severidad en la frecuencia por peligro y estimación S18

La frecuencia CatBoost por peligro (CFS) multiplicaba cada frecuencia por la severidad media del peligro, igual para todas las pólizas. Esa severidad no es constante (cifras del encabezado de `severidad_cfs.py`): en 2021–2023, del quintil inferior al superior de capital asegurado, el coste medio por siniestro pasa de 29.765 a 70.601 CU en incendio, de 20.136 a 40.027 en inundación y de 2.292 a 4.323 en tormenta, y en daños propios de autos de 1.417 a 2.231 CU por quintil de valor del vehículo. `../Modelos_claude/severidad_cfs.py` ajusta, por peligro y corte, un GLM gamma con enlace log sobre los siniestros positivos de los años de entrenamiento (log del capital relativo a la mediana, más sótano en inundación, en hogar; log del grupo de valor y antigüedad del vehículo en daños propios, robo y lunas en autos; terceros y lesiones con severidad constante) y multiplica la contribución guardada de cada peligro por la relatividad, normalizada a media 1 en los siniestros de entrenamiento. No reentrena la frecuencia. Las elasticidades al capital apenas cambian entre cortes (incendio 0,73 a 0,82, inundación 0,60 a 0,64, robo de contenidos 0,68 a 0,70).

| Componente solo | V23 selección | V24 |
| --- | ---: | ---: |
| Edificios, CFS → CFSS | 0,10519 → 0,11562 | 0,10477 → 0,11307 |
| Contenidos, CFS → CFSS | 0,07523 → 0,08961 | 0,07582 → 0,09060 |
| Autos, CFS → CFSS | 0,0918 → 0,09306 | 0,08861 → 0,09100 |

Es la mayor mejora de un componente en toda la evaluación, y sale de corregir un supuesto actuarial: la prima de riesgo por peligro es frecuencia por severidad, y la severidad crece con lo asegurado. El nivel de estas frecuencias, en cambio, deriva entre V24 y 2025 frente al Tweedie de árboles del ramo (medido sin etiquetas): −4,3 % en autos, −2,7 % en edificios y −2,9 % en contenidos sin severidad, y −4,4 %, −2,0 % y −2,0 % con ella. Desde S17 la regla s17 de `mezcla3.py` deja fuera de la referencia de nivel cualquier componente que se aparte más de un 1,5 %; aporta relatividades y no nivel, como las redes neuronales.

S18 lleva en autos el CatBoost Tweedie de cuatro semillas (0,2), CFSS (0,6) y dos LightGBM (0,1 y 0,1); en edificios el LightGBM con `min_data_in_leaf` 1000 (0,5) y CFSS (0,5); en contenidos el LightGBM (0,3), la red neuronal (0,1), el modelo aditivo (0,4) y CFSS (0,2). Total 2025 de 214,4 millones de CU; por unidad de exposición 594,5 en autos, 509,1 en edificios y 126,6 en contenidos, frente a 586,4, 513,0 y 126,1 del contraste por tendencias de la sección 3. En 1.000 subconjuntos del 30 % de los clientes supera a S09b en el 99 % de los casos en V24 y el 97 % en V23. Sin el 0,1 % superior de la pérdida el agregado queda en −0,00072 (V23) y +0,00008 (V24), y edificios en −0,00247 y −0,00091: su ganancia sigue apoyada en la cola, como se explica en la sección 4.5. Detalle en `../Modelos_claude/experimentos/robustez_s18.json`, `bootstrap_codex_s18.json` y `publico_simulado_s18.json`.

Pruebas de esta ronda que no se adoptaron:

- Severidad híbrida (`severidad_cfs2.py`): el GLM con un LightGBM gamma encima mejora el componente en contenidos (+0,0010 en V23 y +0,0007 en V24) y apenas en edificios, empeora en autos y no suma en la mezcla (agregado V24 0,13776 frente a 0,13779). Lo que el boosting añade a la severidad ya lo recogen el LightGBM Tweedie y el modelo aditivo.
- Una forma nueva para S18 (`rejilla_forma.py`): autos y edificios mantienen el par vigente. En contenidos los dos cortes prefieren una elasticidad a la exposición b < 1 (con b = 0,9, +0,0033 en V23 y +0,0005 en V24). Los periodos se parten por año natural y por cambios de póliza, y en contenidos los tramos de menos de un trimestre que empiezan en el primer trimestre tienen un cociente real/esperado de 1,50 (V23) y 1,26 (V24) frente a la mezcla sin forma (`ae_exposicion_trimestre.py`). La ganancia de V23 es siete veces la de V24 y coincide con que 2021, dentro de su entrenamiento, tiene la mitad de periodos parciales que los años siguientes, así que la corrección que necesitaría producción es menor; no se adopta.
- Más peso para la frecuencia CatBoost en contenidos: sube V23 y baja V24.

### 4.8 Frecuencia aditiva con severidad por capital (S20), reservas y repetición en el equipo

La frecuencia del modelo aditivo de la sección 4.6 (árboles de una división) tenía en edificios severidad constante en incendio, inundación y hundimiento, porque esos peligros no llegaban a 1.500 siniestros para el boosting de severidad. `frecsev2.py --partes` guarda la frecuencia por peligro y `severidad_cfs.py` le aplica la severidad por capital de la sección 4.7. El componente (FSAS) pasa en edificios de 0,10934 a 0,11521 en V23 y de 0,11021 a 0,11439 en V24, y en contenidos de 0,08925 a 0,09175 y de 0,09352 a 0,09470. Con cuatro semillas de la frecuencia (FSAS4), adoptadas sin mirar su resultado, V24 queda en 0,11449 y 0,09459. Su total se mueve con el ancla en edificios (+0,06 % entre V24 y 2025) y se aparta en contenidos (−1,57 %), así que por la regla s17 entra en la referencia de nivel solo en edificios.

Los cortes discrepan sobre los pesos de contenidos: V23 premia quitar el LightGBM y V24 lo contrario. Por eso los pesos de S20 salen de la combinación que maximiza la peor de las dos mejoras frente a S18 (`rejilla_pesos.py`, rejilla de 0,1 en el símplex), un criterio declarado antes de ver el resultado de autos. Edificios queda en LightGBM 0,4, CFSS 0,3 y FSAS4 0,3; contenidos en LightGBM 0,2, red 0,1, aditivo 0,3 y FSAS4 0,4; autos como S18. Frente a S18 suma +0,00022 en V23 y +0,00024 en V24 (probabilidades de mejora 0,83 y 0,97), y sin el 0,1 % superior de la pérdida V24 sigue positivo (+0,00033). En edificios, sin ese 0,1 %, V24 mejora +0,00116 frente a S18: el componente nuevo no añade dependencia de la cola.

La reserva de caso de los siniestros abiertos es el punto débil del T0 en edificios y autos: al 31-12-2024 es el 28 % del T0 de 2024 en edificios y el 29 % en autos, y en todos los años y ramos suma 90,2 millones de CU. `influencia_reservas.py` evalúa 2024 con esa reserva × 0,75, × 1 y × 1,25 en la etiqueta, sin tocar las predicciones:

| Ramo | S20 − H, −25 % | S20 − H, nominal | S20 − H, +25 % | S20 − S18, nominal |
| --- | ---: | ---: | ---: | ---: |
| Autos | +0,00076 | +0,00090 | +0,00102 | 0 |
| Edificios | +0,00129 | +0,00062 | −0,00001 | +0,00053 |
| Contenidos | +0,00108 | +0,00098 | +0,00088 | +0,00032 |
| Agregado | +0,00098 | +0,00078 | +0,00059 | +0,00024 |

Solo el agregado con −25 % tiene un IC95 por cliente por encima de cero ([+0,00011; +0,00189]). En edificios la ventaja frente a H se agota al subir la reserva; el cambio del numerador pareado se reparte entre incendio, inundación y escape de agua más que en hundimiento. Los diez clientes más favorables explican toda la ventaja nominal frente a H, mientras que la mejora frente a S18 no depende de ellos. Codex llega a la misma lectura para S18 en su revisión N16 y N17.

Por peligro aislado en 2024 (`peligro_aislado.py`, coste T0 del peligro como etiqueta), la severidad por capital mejora la cabeza de cada peligro de edificios frente a la severidad media, y la mejora se conserva con la reserva ±25 %: incendio pasa de 0,0602 a 0,0737 nominal (de 0,0587 a 0,0717 con +25 %), escape de agua de 0,0621 a 0,0713, tormenta de 0,0852 a 0,0920, hundimiento de 0,1200 a 0,1260 (de 0,1107 a 0,1166 con +25 %) e inundación de 0,4357 a 0,4381. La frecuencia aditiva con esa severidad es mejor que la CatBoost en inundación (0,4594), escape de agua, incendio y daños accidentales, y peor en hundimiento (0,1068) y tormenta; por eso las dos entran en la mezcla de edificios. En hundimiento la reserva de los abiertos de 2024 es el 57 % del coste T0 del peligro. Por decil de tasa predicha (`calibracion_deciles.py`), el cociente real/esperado de S20 en V24 oscila entre 0,92 y 1,09 en autos, 0,79 y 1,24 en edificios y 0,88 y 1,07 en contenidos; el total de edificios queda en 1,07 con el factor de V23 (en edificios el factor de año siguiente es 0,99 en V23 y 1,06 en V24, y 2025 recibe la media), y sin el 0,1 % superior de la pérdida el decil más alto baja a 0,59 en edificios y 0,51 en contenidos, como en la sección 4.5.

`reproducir_mezcla.py` repite las mezclas en la máquina virtual del equipo del participante con los archivos guardados en `../Modelos_claude/` (predicciones de cada componente, selecciones de V23 y exposiciones): S18 sale con el SHA-256 idéntico y S20 con el mismo total y una predicción distinta en 1e-6 por redondeo. Es una repetición de la mezcla, no del entrenamiento de cada componente.

### 4.9 Severidad con covariables físicas (S21), medias por ramo, semestres y tercer motor de frecuencia

La severidad por capital de la sección 4.7 usa una sola covariable por peligro (dos en inundación). `severidad_cfs3.py` le añade covariables F0 elegidas antes de ajustar por razones físicas: nivel de seguridad, objetos de valor y densidad urbana en el robo de contenidos; zona de inundación y sótano en inundación; suelo, árboles a menos de 5 m y antigüedad en hundimiento; carrocería, combustible y asistencia a la conducción en los daños propios de autos, entre otras. Solo las covariables nuevas llevan ridge, de modo que el modelo contiene al anterior como caso particular. En contenidos mejora los dos cortes: la frecuencia aditiva con esa severidad pasa de 0,09175 a 0,09286 en V23 y de 0,09459 a 0,09542 en V24, y la CatBoost de 0,08961 a 0,09052 y de 0,09060 a 0,09139. En edificios y en autos empeora V23 (edificios, aditivo, de 0,11521 a 0,11455; autos de 0,09306 a 0,09260) y no se adopta; con diez veces más ridge, edificios empeora en los dos cortes. Una explicación posible, que no está medida, es que en contenidos el robo y los daños accidentales dependen de lo que hay dentro de la vivienda, que el capital refleja peor que en edificios.

S21 cambia de S20 solo en hogar. Contenidos queda en LightGBM 0,2, red 0,1, aditivo 0,2 y aditivo con severidad ampliada 0,5 (rejilla de la peor de las dos mejoras), y la frecuencia CatBoost de edificios promedia cuatro semillas, adoptadas sin mirar el resultado. Frente a S20 gana +0,00007 en V23 y +0,00004 en V24 (probabilidades de mejora 0,93 y 0,79) y lo supera en el 67,8 % y el 79,1 % de los subconjuntos del 30 % de los clientes. La mejora es frágil en dos sentidos medidos. Sin el 0,1 % superior de las filas se invierte (−0,00002 y −0,00005). En la cohorte que empieza en el segundo semestre de 2024, el 3,1 % de la exposición y la menos madura (exposición efectiva entre nominal 0,76), S21 pierde frente a S20 con un IC95 por cliente que no toca cero: −0,00035, [−0,00064; −0,00003], y −0,00038 con la reserva × 1,25. La pérdida es de contenidos y la explican diez filas con siniestro (sin ellas, la diferencia de devianza del semestre pasa de −1.483 a −103); el cociente real/esperado del semestre es el mismo con las dos estimaciones (0,915), así que no es un problema de nivel.

Las medias por ramo (`exportar_predicciones.py`) completan la lectura de nivel de la sección 4.8. En V24, con el factor de V23, el cociente observado/predicho es 1,009 en autos, 1,070 en edificios y 0,989 en contenidos (1,029 en el agregado); en V23 es 0,988, 1,001 y 1,020. En edificios baja a 0,994 con la reserva de caso × 0,75 y sube a 1,145 con × 1,25, así que buena parte del desfase de 2024 en edificios depende de cómo se cierren los siniestros abiertos. Las predicciones por fila de V23 y V24 que dan estos números quedaron en `../Modelos_claude/experimentos/predicciones_v23_v24_s21.parquet` para la revisión de Codex.

Como tercer motor de frecuencia, preinscrito en el foro con el umbral de +0,0001 en el agregado en los dos cortes, se probó un LightGBM Poisson por peligro de profundidad intermedia con la severidad GLM encima. En edificios da 0,11472 en V23 y 0,11433 en V24, y en contenidos 0,09175 y 0,09322; en ninguno de los dos ramos hay una combinación con peso positivo que mejore V23 y V24 a la vez, así que no entra. En autos da 0,09166 y 0,08926 y la mejor combinación sube el agregado +0,00003 y +0,00004, por debajo del umbral, así que tampoco entra.

### 4.10 Resultado público de S21 y variante robusta S22

H y S21 se enviaron con autorización del participante y obtuvieron 0,12886 y 0,12874 en el público, por debajo de A_G (0,12908) y de S09b (0,12889). En V24, S21 superaba a S09b en +0,00255 y lo hacía en el 99,6 % de los subconjuntos del 30 % de los clientes de 2024, así que el resultado no se parece al ruido de muestreo de clientes de ese año. Sin mirar etiquetas de 2025, el nivel no alcanza para explicarlo: S21 predice un 2,4 % más que S09b y, en V24, mover todas sus predicciones un 2,4 % cambia el D² entre −0,00031 y +0,00015. La forma tampoco desplaza el nivel de 2025 respecto de los cortes en que se ajusta el factor: el cociente entre el total con forma y sin ella es casi el mismo en V23, V24 y 2025 (edificios 1,079, 1,083 y 1,080; `diagnostico_forma_nivel.py`).

Lo que sí estaba medido antes es que la ganancia de la forma de hogar viene de la cola (sección 4.5). Frente a S09b, sin el 0,1 % superior de las filas, S21 pierde en V23 (−0,00103). S22 es la misma mezcla con la forma solo en autos: cede −0,00054 en V23 y −0,00033 en V24 frente a S21, pero mejora a S09b en los tres ramos y los dos cortes con y sin ese 0,1 % (agregado +0,00164 y +0,00222; sin la cola +0,00097 y +0,00114). En 2024 gana a A_G por +0,00165 (IC95 por cliente [+0,00052; +0,00308]) y queda por encima de H en el agregado (+0,00048, con un intervalo que incluye cero) y por debajo en edificios. El cambio es uno solo y la regla para leer su resultado público quedó escrita antes de cualquier envío: si supera a S21, la forma de hogar probablemente no se traslada a 2025; si no, la inversión viene de otra parte. Con un solo envío no se identifica la causa, y en los subconjuntos de 2024 lo esperable sería que S21 quedara por encima de S22 (lo hace en el 80 % al 86 % de los casos).

Después de fijar S22 se comparó el orden de los candidatos enviados en el cuerpo de la distribución de 2024 (`diagnostico_cuerpo_cola.py`): sin el percentil superior de T0 y con cada candidato reescalado por ramo a su factor óptimo, para que pese la forma y no el nivel. Con todas las filas el orden local es S21, S22, H, A_G y S09b, casi el inverso del público; sin el p99,5 es S22 (0,11168), S09b (0,11160), A_G (0,11143), H (0,10996) y S21 (0,10968), y sin el p99 S09b, A_G, S22, H y S21. El público se parece más al orden del cuerpo que al de la distribución completa, lo que apoya la lectura de que la cola de 2024 no se traslada al subconjunto público. Son cuatro puntos y el recorte por la etiqueta no es una regla de puntuación válida, así que queda como indicio.

### 4.11 S22 en el público y pruebas posteriores

S22 se envió por decisión del participante y obtuvo 0,12988 en el público, por encima de A_G (0,12908), S09b (0,12889), H (0,12886) y S21 (0,12874). El orden de los cinco en el público coincide en lo esencial con el orden en el cuerpo de la distribución de 2024 de la sección 4.10, y no con el de la distribución completa; sigue siendo un indicio con cinco puntos.

Sobre S22 se probaron tres cambios, cada uno fijado antes de calcularlo. Quitar la forma de autos empeora autos con y sin la cola, así que esa forma se queda: a diferencia de la de hogar, su ganancia no depende de los siniestros grandes. Estimar las relatividades de severidad con la severidad por fila acotada al p99,5 de cada peligro casi no cambia la mezcla (−0,00001 con todas las filas, hasta +0,00004 sin el 0,1 % superior). Entrenar los LightGBM de hogar con la etiqueta acotada y un recargo multiplicativo uniforme mejora edificios en 2024 y lo empeora en 2023; la combinación no llega al mínimo fijado y no se adopta. La lectura posible, sin medir, es que la cola de 2024 está más cargada de reserva de caso que la de 2023, y un modelo que la descuenta gana en un año y pierde en el otro. Dos semillas más en la frecuencia CatBoost de autos no cambian la mezcla (+0,00000 en V24). La línea B de Claude partió de S22 con severidad con tendencia y pesos de cuerpo en contenidos (S30) y obtuvo 0,12996 en el público; la diferencia con S22 y con 0,13 está dentro del ruido del subconjunto.

## 5. Límites

V24 ya se consultó muchas veces y funciona como desarrollo reutilizado, no como validación independiente. Los parámetros de forma se fijaron con los óptimos de V23 y V24. El ruido de nivel del público es grande (±0,005 en un subconjunto del 50 %), aunque las diferencias pareadas entre modelos parecidos son mucho más precisas. El ruido de semilla también cuenta: dos pares de semillas del mismo CatBoost dan V24 de autos 0,08864 y 0,08795, así que diferencias de 0,0003 en un ramo no distinguen modelos. La ganancia de la forma de hogar depende de la cola (sección 4.5) y tendrá en el público más varianza que una mejora repartida. Codex observó esta noche que dos candidatos suyos con mejor D² local de 2024 (N01_B y N01_G) bajaron en el público; sus metas usaban 2024 en validación cruzada por cliente y el escenario de autos de N01_G incluía `marketing_segment`, que S14 no usa, pero el aviso vale para cualquier selección hecha mirando 2024. La evidencia del cambio de régimen en lesiones es observacional: con una sola valoración no se puede probar del todo frente a un desarrollo muy particular de las reservas. Seis de las siete variables F3 de hogar tienen fecha de referencia sin confirmar; el participante aceptó ese riesgo en D80. Codex comprobó en N15 que la historia F1 con corte del 1 de enero incluye, en unos cientos de filas por año, avisos posteriores a la fecha de cotización reconstruida; las F1 de Claude salen de `construir_variables.py` con el mismo corte, así que la observación les alcanza; son unos cientos de filas por año y no se midió su efecto en el D². La regla de nivel s17 y los pesos de S18 se eligieron mirando V23 y V24. La elección de los pesos de S20 por la peor de las dos mejoras usa V23 y V24, y su ventaja frente a H depende de pocos clientes y se reduce al subir la reserva de caso. En su revisión periódica VAL03 (hallazgo DATA-005), Codex señala además que el clima del año anterior (`*_prev1`) todavía no está cerrado en la fecha de cotización de los periodos cotizados antes del 31 de diciembre; las variables F2 de Claude usan ese mismo año anterior y la media de los años previos, así que la observación les alcanza. No es una fuga de la etiqueta, pero limita lo que puede afirmarse sobre una tarifa calculada en la fecha real de cotización. La severidad ampliada de S21 se adoptó en contenidos viendo V23 y V24; su mejora frente a S20 depende de los siniestros grandes y retrocede en la cohorte del segundo semestre de 2024 (sección 4.9).
