# Técnicas actuariales y aprendizaje automático para autos, edificios y contenidos

Investigación del proyecto al 16 de octubre de 2026. Este informe relaciona los datos disponibles con métodos tradicionales, modelos de aprendizaje automático y combinaciones de ambos. Complementa la [metodología vigente](../METODOLOGIA_ACTUARIAL.md) y su [protocolo](../protocolo_metodologico.json). Las prioridades son propuestas para contrastar; todavía no hay modelos entrenados ni resultados que permitan declarar un ganador en esta cartera.

La primera comparación debe enfrentar un GLM Tweedie, un modelo de frecuencia–severidad y árboles potenciados por ramo. Después conviene probar correcciones sobre una base actuarial y modelos por peligro. En autos merece atención especial la separación de lesiones; en edificios, el reparto entre agua, incendio, inundación y hundimiento; en contenidos, robo y riesgos de agua. Una arquitectura más compleja se justifica si aporta mejora retenida y una explicación útil del cambio.

## Datos analizados y alcance de las cifras

El diagnóstico nuevo lee el catálogo preparado con CAP01, CAT01 y AGE01 indicado en [current_dataset.json](../../Limpieza/current_dataset.json), verifica hashes y conserva [evidencia JSON](runs/soporte_20261016T190621Z/evidencia.json), [tablas por ramo](runs/soporte_20261016T190621Z/ramos.csv), [peligro](runs/soporte_20261016T190621Z/riesgos.csv) y [cohorte](runs/soporte_20261016T190621Z/cohortes.csv). Se inspeccionan siniestros y columnas seleccionadas de las seis tablas preparadas. El perfil anterior se reutiliza solo para campos que ID01, EXP01, CAP01, CAT01 y AGE01 no cambiaron.

Los importes siguientes son incurridos netos de recuperaciones, en CU, de siniestros aceptados ocurridos en 2021–2024 y reportados al 31 de diciembre de 2024. Incluyen expedientes abiertos. Describen lo observado, con truncamiento de reporte y desarrollo pendiente. No son costes últimos conocidos.

| Característica | Autos | Edificios | Contenidos |
| --- | ---: | ---: | ---: |
| Periodos de entrenamiento | 979.968 | 707.726 | 721.617 |
| Periodos de test 2025 | 254.986 | 184.155 | 187.498 |
| Siniestros aceptados reportados, ocurrencia 2021–2024 | 110.999 | 26.396 | 23.773 |
| Incurrido neto observado, millones CU | 430,97 | 247,96 | 66,02 |
| Reserva de caso / incurrido neto | 14,82% | 9,62% | 4,01% |
| Severidad positiva mediana, CU por siniestro | 1.532,09 | 3.127,01 | 1.190,12 |
| Percentil 99 de severidad positiva, CU | 35.691,28 | 99.095,46 | 22.045,55 |
| Coste explicado por el 1% de siniestros positivos de mayor importe | 20,91% | 18,37% | 11,76% |
| Periodos con coste observado cero en el proxy descriptivo anterior | 89,99% | 96,42% | 96,82% |

La última fila reutiliza la asignación descriptiva de la auditoría D30 y excluye sus exposiciones y claves antiguas. Ese proxy asigna 110.901, 26.375 y 23.753 siniestros aceptados a autos, edificios y contenidos. Por eso sus sumas no coinciden con todos los siniestros de ocurrencia 2021–2024 del cuadro: hay expedientes fuera del periodo cubierto. La futura construcción T0 necesita reconciliarlo de nuevo. Los 414 siniestros anteriores al primer periodo observado identificados en la auditoría abarcan también otras fechas y estados; no se sustituyen por la diferencia de este cuadro.

El 1% de todos los periodos de mayor coste concentra el 53,47% del coste asignado de autos, el 81,94% de edificios y el 79,74% de contenidos. Este porcentaje incluye muchos ceros en el denominador de filas; es diferente del 1% de siniestros positivos del cuadro. Se calcula tomando el techo de 1% del número de observaciones, con el criterio conservado en el script.

La combinación de ceros y asimetría favorece pérdidas que modelen la esperanza monetaria. Optimizar RMSE sobre logaritmos o buscar la mediana puede dar predicciones muy diferentes de la prima de riesgo. Tampoco procede recortar los siniestros grandes antes de establecer su efecto: son parte del objetivo económico y de la evaluación.

## Qué cambia entre peligros y productos

La siguiente distribución procede de [riesgos.csv](runs/soporte_20261016T190621Z/riesgos.csv); los porcentajes de coste suman 100% dentro de cada ramo, salvo redondeo.

| Ramo y peligro | Siniestros aceptados | Participación en coste del ramo | Reserva / coste neto del peligro |
| --- | ---: | ---: | ---: |
| Autos, lesiones corporales | 7.564 | 37,90% | 31,41% |
| Autos, daños a terceros | 33.107 | 28,27% | 5,61% |
| Autos, daños propios | 48.480 | 20,88% | 4,60% |
| Autos, robo | 6.147 | 8,99% | 3,64% |
| Autos, cristales/granizo | 15.701 | 3,96% | 1,18% |
| Edificios, inundación | 2.228 | 28,19% | 9,35% |
| Edificios, escape de agua | 10.121 | 23,41% | 6,65% |
| Edificios, incendio | 1.115 | 23,24% | 7,85% |
| Edificios, hundimiento | 1.293 | 12,41% | 25,24% |
| Edificios, tormenta | 7.796 | 10,85% | 4,05% |
| Edificios, daño accidental | 3.843 | 1,89% | 1,88% |
| Contenidos, robo | 7.657 | 42,31% | 2,91% |
| Contenidos, inundación | 1.622 | 24,53% | 7,15% |
| Contenidos, escape de agua | 5.399 | 22,40% | 3,67% |
| Contenidos, daño accidental | 9.095 | 10,77% | 1,93% |

Las lesiones son solo aproximadamente el 6,8% de los siniestros aceptados de autos y explican el 37,9% del coste. En la cohorte 2024 siguen abiertos 940 de 1.178 expedientes de lesiones y 200 de 291 de hundimiento. En robo de contenidos, son 253 de 1.976. Estos controles, conservados en el [diagnóstico D35](../diagnosticos/actual.json), apoyan diagnósticos separados de desarrollo. No acreditan una curva de liquidación o un factor último.

Autos contiene `comprehensive`, `third_party_fire_theft` y `third_party_only`: 802.694, 89.070 y 88.204 periodos de entrenamiento. Las diferencias de cobertura deben entrar como estructura contractual. Antes de imponer ceros por peligro, construir una matriz de elegibilidad y contrastarla con el diccionario y los siniestros; no deducir el detalle completo del contrato solo por el nombre de la categoría. La entrega sigue siendo un coste por periodo: cualquier descomposición debe recomponerse sin duplicar componentes.

## Información disponible y consecuencias para los métodos

| Bloque | Información útil | Uso propuesto y límite |
| --- | --- | --- |
| Autos | Edad y experiencia del conductor, bonificación, vehículo, uso, kilometraje declarado, estacionamiento, cobertura y franquicias | GLM/GAM para curvas e interacciones elegidas; boosting para interacciones adicionales. La franquicia es predictor contractual, no una deducción repetida del coste ya neto. |
| Edificios | Capital, construcción, antigüedad, cubierta, sótano, ocupación, protecciones, suelo y variables de inundación | Modelos por peligro o interacciones entre peligro y características físicas; efectos del capital flexibles. |
| Contenidos | Capital, seguridad, objetos de alto valor, características del hogar y domicilio | Frecuencia–severidad de robo/agua, con regularización para segmentos pequeños. `high_value_items` es un conteo. |
| Historia | Póliza, cliente y domicilio repetidos, fechas de ocurrencia y notificación | Credibilidad e historia causal; conservar renovaciones. No retrotraer el estado o importe final observado en diciembre de 2024. |
| Clima | Resúmenes anuales por domicilio | Históricos anteriores al corte y escenarios conocidos; el clima realizado del año futuro no está disponible para cotizar. |
| Maestros y operaciones | Demografía, contactos, campaña, telemática agregada y prima registrada | Bloques condicionados a disponibilidad. La prima necesita una comparación separada porque reproduce decisiones del tarifario existente. |

Hay 300 categorías `make_model` en el perfil de autos, doce regiones y cuatro clases de densidad urbana. Esto favorece probar CatBoost y agrupación regularizada de categorías, sin convertir los identificadores en variables de riesgo de la primera ronda. Los faltantes de zona de inundación rondan el 2,92%; los de varios campos físicos y de póliza, el 2,5%. Imputar dentro de entrenamiento y conservar indicadores cuando tengan sentido; una ausencia no demuestra por sí sola riesgo cero.

`telematics_score` falta en el 87,58% de las filas de autos originales y no hay trayectorias de viajes, aceleraciones ni vectores temporales detallados. La revisión D38 comprueba que la ausencia coincide con no haber optado por el dispositivo: representa una selección de participantes y no una puntuación cero. Probar un bloque de telemática exige aclarar cuándo se midió; no sostener una propuesta de redes sobre viajes con esta tabla. [Perfil restringido reproducible](runs/soporte_20261016T190621Z/perfil_campos_sin_cambios.csv).

La [revisión multitabla vigente](../../Limpieza/README.md), D38, normaliza mayúsculas de `construction_type` y recalcula edad del tomador de hogar desde nacimiento/inicio. No equivale `t` y `w`: esos códigos cambian de presencia entre años y su significado sigue pendiente. Comparar su efecto temporal y una agrupación explícita de material desconocido como sensibilidad, sin escribir esa equivalencia sobre los datos. Los 161.822 casos de NCB mayor que antigüedad de licencia permanecen para revisión semántica, sin imponer un tope automático. Estos puntos afectan a GLM, codificaciones y embeddings por igual.

CAP01 ya corrigió, por autorización, 2.073 capitales en derivados. Quedan 1.454 extremos pendientes: edificios tiene 593 en train y 98 en test; contenidos, 671 y 92. Las medianas preparadas son 223.000/240.000 CU en edificios train/test y 38.900/40.800 en contenidos. Los extremos restantes alcanzan cientos de millones. No usarlos como exposición monetaria fija: evaluar la sensibilidad de las predicciones y conservar el valor aprobado mientras se resuelve su unidad. Un logaritmo reduce escala, pero no corrige una unidad errónea. En cortes anteriores debe reconstruirse la evidencia de reparación que era conocida entonces.

La exposición es inferior a medio año en el 20,08% de autos, 16,76% de edificios y 18,41% de contenidos del entrenamiento preparado; en test asciende a 21,97%, 18,66% y 20,25%. Comparar por bandas de duración es una necesidad concreta de esta cartera.

## Métodos tradicionales que deben formar la referencia

Un GLM Tweedie con enlace log permite modelar coste con ceros y valores positivos. La especificación inicial mantiene potencia 1,5, coherente con la métrica, y exposición como offset. GAM añade funciones suaves a variables continuas: edad, experiencia, valor/capital, antigüedad y riesgo físico. Ambas alternativas permiten detectar relaciones mal planteadas antes de introducir más flexibilidad. La [documentación de scikit-learn sobre prima pura](https://scikit-learn.org/stable/auto_examples/linear_model/plot_tweedie_regression_insurance_claims.html) ofrece una referencia operativa para comparar coste directo y frecuencia–severidad; el reparto por peligros de este proyecto es una extensión propia.

Para frecuencia–severidad, usar conteo de siniestros aceptados de coste neto positivo, Poisson con offset de exposición y severidad Gamma con enlace log. La severidad se ajusta por siniestro positivo o al promedio del periodo ponderado por su conteo positivo. Una binomial negativa es candidata si la heterogeneidad residual y el desempeño retenido lo apoyan. Sobredispersión aparente también puede venir de duración mal especificada. Hay un aceptado con coste neto cero; contar todos los aceptados y omitir ese cero de Gamma requeriría modelar además la probabilidad de coste positivo.

La identidad económica propuesta es:

```text
Predicción por periodo = exposición × frecuencia anual esperada × severidad esperada
Predicción multirriesgo = suma de predicciones de los peligros cubiertos
```

La descomposición necesita una formulación condicional compatible del coste medio por siniestro y del conteo. Si frecuencia y severidad tienen dependencia residual relevante, estudiar el efecto sobre el coste agregado y contrastar con el Tweedie directo. No multiplicar estimaciones marginales arbitrarias ni usar el número real de siniestros del periodo para predecir su severidad futura.

La credibilidad Bühlmann–Straub o un GLMM/HGLM permite combinar información de grupo e historial individual, reduciendo el peso de historias cortas. La literatura conecta credibilidad y ciertas familias Tweedie bajo supuestos distribucionales explícitos. En nuestra aplicación se propone contrastar frecuencia histórica con exposición y número de periodos conocidos, usando respaldo de cartera para nuevos clientes. La fórmula de contracción y sus parámetros se estiman dentro del entrenamiento; una media móvil sin esa especificación no recibe automáticamente las propiedades del modelo clásico. [Ohlsson y Johansson, 2006](https://www.casact.org/sites/default/files/database/astin_vol36no1_121.pdf).

La duración merece una prueba propia: comparar `log(exposure)` como offset frente al mismo offset con una función adicional regularizada de duración. El trabajo de Lindholm y Nazar muestra que fallar la proporcionalidad puede alterar la interpretación de prima y dispersión. Aquí se medirán sesgo y pérdida por bandas de duración, separando productos. No se puede concluir a partir del porcentaje de periodos cortos que ya existe esa desviación en nuestra cartera. [Lindholm y Nazar, 2024](https://link.springer.com/article/10.1007/s13385-024-00385-5).

## Aprendizaje automático sobre tablas

LightGBM, XGBoost y CatBoost con pérdida Tweedie son los candidatos de primera ronda más claros junto al GLM. Pueden aprender no linealidades e interacciones sin especificarlas todas a mano. El estudio de Yang, Qian y Zou aporta evidencia actuarial de árboles potenciados Tweedie sobre simulación y autos; sus resultados motivan la comparación, sin demostrar superioridad en nuestros datos sintéticos. [Artículo, versión 2016](https://arxiv.org/abs/1508.06378).

| Método | Razón concreta para probarlo | Decisión técnica que debe quedar registrada |
| --- | --- | --- |
| LightGBM Tweedie | Muchas filas, variables físicas y cruces entre cobertura, valor y riesgo | Tamaño mínimo de hoja, regularización y tratamiento de categorías. Controlar errores en segmentos pequeños. |
| XGBoost Tweedie | Comparador de boosting y base para una corrección sobre GLM | `base_margin` en escala de enlace tanto al ajustar como al predecir si contiene offset/base. No duplicar exposición. |
| CatBoost Tweedie | Variables categóricas como vehículo, construcción, región y seguridad | Categorías/ausencias, escala monetaria, orden temporal e historial. El tratamiento interno de categorías no sustituye nuestros cortes temporales. |
| Boosting frecuencia–severidad | Relacionar cada mejora con cambios en ocurrencia o importe | Pérdida Poisson y una pérdida válida de severidad positiva; la predicción agregada se evalúa en CU. |

La potencia 1,5 de evaluación permanece fija aunque se estudien otras potencias al ajustar. En coste directo con `m=e*q`, la homogeneidad de la desviación Tweedie da `d_p(y,e*q)=e^(2-p)*d_p(y/e,q)`. Por tanto, para reproducir la suma de pérdidas sobre importes sin pesos, un ajuste de tasas usa peso `sqrt(e)` cuando p=1,5. Ponderar tasas por `e` corresponde a otra prioridad actuarial y se conserva como sensibilidad; no garantiza el mismo D², pues cambia también la referencia nula. El proyecto ya guarda una [comprobación aritmética](../verificacion_metrica.json).

Los detalles del software importan: los [parámetros LightGBM](https://lightgbm.readthedocs.io/en/stable/Parameters.html) fijan los rangos Tweedie; XGBoost documenta el [margen base](https://xgboost.readthedocs.io/en/release_3.0.0/tutorials/intercept.html). La [documentación de pérdidas CatBoost](https://github.com/catboost/catboost/blob/master/catboost/docs/en/concepts/loss-functions-regression.md) advierte sobre escala de etiquetas; una transformación debe revertirse al predecir. Tweedie con potencia 2 no es una implementación válida de Gamma en CatBoost. Seleccionar una pérdida soportada o biblioteca apropiada para esa comparación.

Un clasificador de cero/coste positivo seguido de severidad es otra opción. En ese modelo de dos partes la primera salida es una probabilidad, no la frecuencia esperada si pueden ocurrir varios siniestros. La alta proporción de ceros no demuestra inflación estructural: Tweedie compuesto ya tiene una masa en cero. El modelo zero-inflated Tweedie de So y Valdez se deja condicionado a un diagnóstico de desajuste y a mejora retenida, considerando que su ejemplo usa telemática composicional que aquí falta. [So y Valdez, 2024](https://arxiv.org/abs/2406.16206).

## Combinaciones con mayor interés actuarial

La primera combinación propuesta es una base GLM/GAM corregida por boosting. Para mantener positividad, la corrección actúa en el enlace:

```text
log(m_i) = log(m_i_base) + f(X_i)
```

Si la base ya incluye exposición, la corrección no la incorpora de nuevo como offset. Entrenar `f` con pérdida Tweedie y margen base, o con una formulación equivalente verificada, conserva el objetivo de coste. Ajustar mínimos cuadrados a residuos monetarios y recortar predicciones negativas sería otro experimento, con diferentes propiedades. Si se usan residuos o predicciones base como etiquetas/features de segunda etapa, producirlos fuera de muestra dentro del entrenamiento cuando corresponda, sin usar V23 selección o V24 para construirlos.

CANN sustituye esa corrección por una red neuronal, inicializada para partir de la predicción de base. El benchmark de Holvoet, Antonio y Henckaerts compara GLM, boosting, redes y CANN en cuatro conjuntos de seguros; también estudia calibración y traducción a tarifas mediante modelos sustitutos. Justifica probar una base actuarial con corrección neuronal. Conviene comparar GLM+CANN frente a GLM+boosting antes de atribuir una ventaja a la red. [Benchmark, versión 2025](https://arxiv.org/abs/2310.12671).

La segunda combinación es un modelo predictivo flexible más una tarifa GLM/GAM que lo aproxime. Se medirá tanto la pérdida frente a los costes como la fidelidad al modelo original, con discrepancias por segmento. Puede aportar una salida explicable para el jurado, aunque sacrifique precisión. La propuesta de construir GLM guiados por un modelo de caja negra ofrece una referencia específica; la selección de variables/cortes debe permanecer dentro de desarrollo. [Lindholm y Palmquist, 2024](https://doi.org/10.1017/S1748499524000265).

Credibilidad más boosting o CANN es especialmente pertinente por la continuidad: alrededor del 84,75–84,85% de las filas 2025 pertenecen a clientes ya observados en el mismo ramo. Comparar un modelo contractual sin historia, historia causal sin ID directo y una contracción explícita permite saber de dónde viene la mejora. El grado de continuidad no autoriza usar costes valorados después del corte histórico. La literatura de CANN longitudinal y telemática aporta una idea de estructura, pero sus componentes de viajes y conteos correlacionados no están reproducidos aquí. [Duval, Boucher y Pigeon, 2023/2024](https://arxiv.org/abs/2308.01729).

## Redes tabulares e interpretables: prioridades de investigación

| Familia | Aportación que se contrastaría | Adaptación y prioridad |
| --- | --- | --- |
| LocalGLMnet | Coeficientes que dependen de las características de cada observación, con descomposición de predicción | Después de CANN; revisar estabilidad y contribuciones. Los coeficientes locales no son efectos causales ni una tarifa global constante. |
| ANAM, red aditiva actuarial | Funciones neuronales por variable e interacciones seleccionadas, con restricciones de forma | Candidato atractivo para comparar precisión y curvas explicables; elegir suavidad/monotonía por fundamento actuarial y validación. |
| TabM | Diversidad de predicción mediante ensamble eficiente de MLP | Comparador de redes antes de atribuir ventajas generales a la atención. Adaptar pérdida, exposición y categorías. |
| FT-Transformer, CAFTT y LocalGLMftt | Interacciones mediante representaciones de variables y atención, con base actuarial o coeficientes locales | Tercera ola. El trabajo de Brauer usa frecuencia: adaptar a frecuencia–severidad o coste Tweedie y revisar código/licencia. |
| Credibility Transformer | Mezcla de información previa y observada en un token de la red | Investigación avanzada; su mecanismo no equivale a aplicar credibilidad clásica al historial de una póliza. |
| In-context Credibility Transformer | Contexto de observaciones de entrenamiento similares | Condicionado a diseñar memoria/contexto sin etiquetas de validación o test y medir coste de inferencia. |
| DRN | Refinar una distribución de referencia en vez de solo su media | Útil si interesa incertidumbre; extraer esperanza en CU y comprobar masa en cero, colas y normalización. |
| TabPFN | Predicción con un modelo tabular preentrenado y contexto del entrenamiento | Piloto condicionado, primero severidad. Versión, soporte de pesos/offset, memoria, licencia y acceso requieren revisión antes de implementarlo. |

Las fuentes específicas son [LocalGLMnet](https://arxiv.org/abs/2107.11059), [ANAM](https://arxiv.org/abs/2509.08467), [TabM](https://arxiv.org/abs/2410.24210), [transformers actuariales de Brauer](https://arxiv.org/abs/2311.07597), [Credibility Transformer](https://link.springer.com/article/10.1007/s13385-025-00413-y), su [extensión con contexto](https://arxiv.org/abs/2509.08122) y [DRN](https://arxiv.org/abs/2406.00998). Estas propuestas respaldan alternativas de arquitectura. Sus benchmarks no proporcionan una clasificación de modelos para nuestra cartera.

La revisión de versiones cambia el diagnóstico de escala de TabPFN. El informe TabPFN-3 anuncia hasta un millón de filas y 200 variables, por lo que no corresponde descartarlo usando los límites de versiones anteriores. Sigue siendo necesario verificar consumo real, adaptación al objetivo y condiciones de uso. El benchmark actuarial actualizado el 9 de octubre de 2026 compara v2.6 y v3 en dos carteras MTPL: encuentra resultados menos favorables para frecuencia y competitividad en severidad, con diferencias de tratamiento de exposición y pesos entre métodos. Usa configuraciones concretas, sin ajuste específico de cada cartera; no demuestra inferioridad universal. Por ese motivo se prioriza un piloto de severidad frente a reemplazar todo el flujo. [Informe técnico TabPFN-3](https://arxiv.org/abs/2605.13986), [Deprez, Verbeke y Verdonck, versión 3](https://arxiv.org/html/2605.22892v3).

Un ensamble final puede mezclar predicciones compatibles en escala de coste. Primero probar una mezcla convexa sencilla con pesos aprendidos dentro de desarrollo. Stacking requiere predicciones fuera de muestra de todos los modelos base y evaluación separada del meta-modelo. Diversidad de arquitectura sin complementariedad de errores no justifica incorporarla.

## Propuestas concretas por ramo

### Autos

Comparar Tweedie directo con frecuencia–severidad por cobertura, usando curvas suaves para edad/experiencia y un tratamiento regularizado de vehículo, uso, kilometraje y estacionamiento. Las interacciones cobertura–vehículo y conductor–uso son hipótesis para contraste, no relaciones ya demostradas. Una parametrización conjunta con efectos de cobertura permite compartir información sin crear modelos muy pequeños para cada cruce.

Después probar una descomposición de lesiones frente a los demás peligros. En lesiones, el desarrollo y la cola pueden cambiar más la interpretación que pequeñas mejoras de algoritmo. La severidad máxima neta reportada de autos es 11,89 millones CU; revisar su expediente y cobertura antes de decidir cualquier tratamiento. Mantener la comparación con todos los importes y una sensibilidad explícita al peso de los mayores, sin presentar un score sobre pérdidas recortadas como equivalente al oficial.

La secuencia recomendada es GLM/GAM y boosting, frecuencia–severidad, GLM+boosting, historia con credibilidad y CANN. ANAM/LocalGLMnet sirven para comparar formas de riesgo; TabM y transformers compiten después con las mismas variables. TabPFN puede estudiarse en severidad positiva, condicionado a un tratamiento adecuado del sesgo de retransformación: exponentiar la media del log-coste no devuelve la media monetaria.

### Edificios

Usar un Tweedie de ramo como referencia y después frecuencia–severidad por grupos de peligro. Priorizar escape de agua, incendio, inundación y hundimiento, compartiendo efectos donde el número de expedientes no sostenga modelos independientes. Incendio tiene 1.115 expedientes y explica el 23,24% del coste; un modelo muy profundo de severidad por todas las categorías sería inestable.

Inundación debe relacionarse con zona, distancia al río, elevación y sótano cuando esos campos estén disponibles. Hundimiento requiere estudiar suelo, árboles, antigüedad y desarrollo pendiente. Estas asociaciones parten de la naturaleza del riesgo y se contrastarán con datos; los maestros sin vigencias impiden certificar que cada característica refleje el estado histórico exacto.

Comparar GLM/GAM por componentes, boosting de coste directo y corrección sobre la base. La exposición temporal lleva offset; `sum_insured` entra como predictor con función flexible, no como offset de coeficiente uno sin evidencia de proporcionalidad. Una sensibilidad separada examinará los capitales pendientes y la estabilidad de la parte alta. ANAM y restricciones de forma son alternativas interpretables, pero una restricción monotónica sobre capital total puede ser inapropiada si cambian mezcla o límites efectivos.

Sin coordenadas exactas ni catálogo de eventos no se propone un modelo físico de catástrofes o dependencia espacial fina como si estuviera identificado. Los resúmenes de clima pasado pueden mejorar características de localización; para riesgo 2025 se necesita una esperanza o escenario de clima futuro, no el año realizado.

### Contenidos

Comparar Tweedie directo y frecuencia–severidad con capital, seguridad y características del domicilio. Robo concentra el 42,31% del coste; inundación y escape de agua aportan otro 46,92%. Una partición robo/agua/accidental permite explicar qué mecanismo cambia con cada variable. Mantener agrupación o efectos compartidos si la validación revela inestabilidad.

Por su menor reserva relativa y colas positivas menos concentradas que autos/edificios, es un candidato razonable para iniciar la comparación de algoritmos con menos interferencia de desarrollo. Eso no hace que T0 sea último: falta reporte y hay abiertos. CatBoost, GAM, una base corregida y ANAM son comparaciones pertinentes. Un modelo más complejo entra si mejora coste retenido y estabilidad de segmentos, no por su novedad.

El cruce edificios–contenidos puede aportar historia de domicilio o cliente. Agregar solo antecedentes anteriores al corte, con contracción; no sumar siniestros del mismo periodo futuro ni transferir automáticamente una severidad entre coberturas. Un modelo multirramo será una sensibilidad frente a modelos separados, con indicador de ramo, variables comunes y predictores específicos. La correlación entre ramos no implica que una póliza carezca de coste porque otra no tiene siniestro.

## Desarrollo, reporte y grandes siniestros

Separar dos ejes: cómo estimamos la respuesta y qué algoritmo aprende esa respuesta. T0 conserva incurrido neto observado; T1 altera reservas con factores de diseño 0,75/1/1,25; T2 propone completar reporte. El escenario de reservas evalúa materialidad, no calcula un factor actuarial estimado ni un intervalo de confianza.

Hay fechas de ocurrencia y notificación, de modo que es posible investigar retrasos de reporte con truncamiento. Para una notificación observada con retraso `d` y edad observable `a` al corte, una contribución condicional tiene la forma `log f(d|X) - log F(a|X)`, bajo la especificación elegida. Ignorar el segundo término sesga las cohortes recientes hacia retrasos cortos. El proceso de frecuencia y la distribución temporal requieren una formulación conjunta o supuestos explícitos, con regularización y sensibilidad de cola. El principio de separar frecuencia/reportes y severidad aparece en [Triangle-free reserving, Parodi](https://www.cambridge.org/core/journals/british-actuarial-journal/article/abs/trianglefree-reserving/6897BBE13CC8692BF75DAD3A97B91416).

Completar conteos no completa automáticamente importes. Si los siniestros reportados tarde son más costosos, un factor de conteo aplicado a toda la prima puede fallar. Examinar retraso frente a severidad por peligro en cohortes más maduras, sin llamar a esos importes último verdadero. Una formulación conjunta de ocurrencia y desarrollo recuerda además la incertidumbre de las etiquetas imputadas. La valoración financiera única de nuestra base limita su implementación completa. [Crevecoeur y colaboradores, versión 2023](https://arxiv.org/abs/2203.07145).

No construir Chain-Ladder o Bornhuetter–Ferguson financiero con pagos/incurridos actuales colocados retrospectivamente en distintas celdas: falta la historia de esas valoraciones. Un análisis de conteos por retraso de notificación sí usa fechas reales, pero no recrea un triángulo de pagos. Tampoco hay fecha de cierre para estimar un modelo de tiempo de liquidación sin información adicional.

Un modelo separado de pérdidas grandes o una cola paramétrica queda como sensibilidad de investigación. Necesita suficiente soporte por peligro, umbral estable, revisión de límites contractuales y existencia de media finita de la distribución escogida. La concentración observada justifica inspección, no prueba que una distribución de Pareto sea correcta. El objetivo inmediato sigue siendo la media del coste total retenido.

## Comparación y validación que harán útil la búsqueda

Mantener V22 para ajuste interno, V23 para desarrollo y su división de calibración/selección por hash de cliente, y V24 como evaluación final de primera ronda una vez congelados candidatos. La [metodología](../METODOLOGIA_ACTUARIAL.md) fija los detalles. Las etiquetas están valoradas a diciembre de 2024 en todos los años: estos cortes no reconstruyen un backtest histórico estricto.

Cada comparación cambia un eje principal: familia, descomposición por peligro, historia, duración, capitales o respuesta T0/T1/T2. Si cambian datos y algoritmo a la vez, añadir una ablación que permita atribuir la diferencia. La primera ronda usa el bloque contractual F0 y supuestos de disponibilidad declarados; historia, clima, telemática/operaciones y prima se incorporan por separado.

| Evidencia de cada prueba | Criterio de interpretación |
| --- | --- |
| D² Tweedie p=1,5 global, en CU por periodo y sobre idénticas filas | Selección principal provisional sin pesos; no promediar los D² de ramos como si fuera el D² global. |
| Desviación total y por ramo/peligro/segmento | Identificar de dónde viene el cambio y el efecto de los importes grandes. |
| Observado/predicho total, deciles y bandas de duración/capital | Separar ordenación de riesgo y calibración; publicar tamaños y exposición. |
| Entidades conocidas y nuevas, productos, faltantes y capitales pendientes | Comprobar que una media global no oculta deterioro material. |
| Sensibilidad a reservas, retrasos y tendencia | Evitar elegir solo por el sesgo de madurez de una etiqueta. |
| Diferencia de pérdida por cliente/domicilio y estabilidad entre años | Respetar dependencia de renovaciones al estimar incertidumbre. Solo cuatro años limitan inferencia de tendencia/eventos. |
| Tiempo, memoria, estabilidad de semillas y explicación | Evaluar coste y reproducibilidad junto a precisión. |

Para recalibrar una predicción con Tweedie no se presume que el multiplicador óptimo sea siempre suma observada/suma predicha: la solución depende de la pérdida. Estimar la calibración en su parte reservada de V23; evaluar en selección sin volver a ajustarla y conservar también la predicción original. El [D² documentado por scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.d2_tweedie_score.html) es la referencia local, no una certificación de reproducción del scorer no publicado.

Los objetivos generados, selección de categorías, embeddings, normalización, elección de componentes y ensamblado deben respetar esas particiones. No usar etiquetas de selección o de V24 como contexto de un modelo preentrenado. Mantener renovaciones conocidas es representativo de 2025; agrupar todas las entidades fuera de entrenamiento constituye una prueba adicional de nuevos clientes, con otro propósito.

Tendencia monetaria requiere especial prudencia: solo hay cuatro años sintéticos y cambian mezcla y madurez. Contrastar una especificación sin tendencia y sensibilidades simples predefinidas después de controlar mezcla y desarrollo. No proyectar una inflación observada externamente sobre CU ficticias como si fueran moneda de un país real.

## Orden de pruebas y decisión de continuidad

| Ola | Trabajo propuesto | Candidatos del catálogo | Qué resuelve |
| --- | --- | --- | --- |
| Preparación | Asignación única, reconciliación, T0, contrato F0, particiones y métrica | Requisitos comunes | Hace comparables los modelos sin confundirlos con cambios de etiqueta. |
| Primera | Tasa de referencia, GLM Tweedie y boosting por ramo | M00, M01, M04–M06 | Cuánto aportan los patrones no lineales sobre una base actuarial. |
| Segunda | GAM, frecuencia–severidad, componentes por peligro, credibilidad, corrección sobre base y duración | M02, M03, M07–M09 | Qué estructura de riesgo e historia produce una mejora estable. |
| Tercera | CANN, ANAM, LocalGLMnet y TabM; comparar con MLP/FT-Transformer | M10–M12, M17, M18 | Valor de las redes y de la interpretación estructurada. |
| Condicionada | Transformers actuariales, longitudinal, DRN, Credibility Transformer, TabPFN y zero-inflated | M13–M15, M19–M21 | Beneficio adicional frente a adaptación, soporte de datos y coste. |
| Combinación | Mezcla sencilla; stacking solo con predicciones internas apropiadas | M16 | Complementariedad real y mejora retenida. |

No es necesario probar todas las familias antes de tener una primera referencia puntuable. Sí conservar las hipótesis y condiciones para reanudar las líneas que puedan aportar más. Una mejora en una única partición o un único gran siniestro no establece una ventaja estable. El catálogo distingue propuestas de modelos ajustados; la política D29 mantiene cinco envíos diarios como máximo provisional, sin obligación de usarlos todos.

## Fuentes, reproducción y responsabilidad

El [catálogo de fuentes](fuentes.json) identifica 23 referencias primarias, su versión o año, nivel de lectura y aplicación. La búsqueda cubrió tarificación Tweedie, frecuencia–severidad, credibilidad, duración, redes actuariales, modelos tabulares recientes y reporte/desarrollo. Se consultaron artículos originales y documentación oficial, y se localizaron repositorios de autores pendientes de auditoría; se descartaron resúmenes comerciales como prueba de superioridad. Es una búsqueda dirigida al proyecto, no una revisión sistemática exhaustiva ni reproducción de experimentos publicados.

Las consultas nativas a discusiones y notebooks de esta competición devolvieron objetos vacíos sin contenido utilizable. Ese resultado no prueba que no existan contribuciones públicas. No se extrajeron conclusiones sobre actividad de otros equipos ni se copió una solución del concurso.

Para reproducir solo el diagnóstico, desde C:/dev/Hakaton:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Modelado\Investigacion_tecnicas\analizar_soporte.py'
```

Cada corrida crea una carpeta nueva y conserva el script y hashes de entradas. El índice [actual.json](actual.json) identifica la evidencia revisada. No se cambia automáticamente al repetir el comando. Las comprobaciones de esta entrega verifican integridad, sumas, enlaces y coherencia documental; son comprobaciones propias asistidas por IA. El primer control detectó el cambio concurrente de la capa CAP01 a CAT01/AGE01 y del protocolo 1.1 a 1.2. Se conserva ese [resultado inicial](verification_initial_CAP01_pointer_drift.json) y la primera corrida. El diagnóstico se actualizó sobre la nueva capa, excluyendo del perfil histórico los campos recién modificados; los agregados de costes, exposición y capital del informe no cambiaron.

El análisis y las propuestas fueron redactados por Codex a solicitud del participante. La aplicación de métodos, supuestos de último, uso temporal de campos y elección final siguen sujetos a evidencia y revisión humana, hoy pendiente. La [matriz IAA del proyecto](../../../../Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md) vincula el trabajo con documentación de datos/modelos, responsabilidad y distinción de validación propia e independiente. Los datos originales permanecen intactos; no se entrenaron modelos, descargaron pesos, contrataron servicios ni hicieron envíos por esta investigación.
