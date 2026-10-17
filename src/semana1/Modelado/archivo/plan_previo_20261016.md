# Modelos candidatos y plan de comparación para el concurso

Revisión del 16 de octubre de 2026, America/Bogota. El participante pidió analizar la propuesta compartida en Gemini y documentar los modelos que probaremos. El resultado es un portafolio de experimentos: todavía no acredita entrenamiento ni rendimiento de esos candidatos en este concurso.

La propuesta aporta familias pertinentes: GLM/GAM, frecuencia-severidad, credibilidad, boosting y redes híbridas. Su conclusión de que una arquitectura concreta será superior excede la evidencia disponible. Compararemos primero modelos actuariales y boosting sobre el mismo objetivo y las mismas particiones; los híbridos y las redes se incorporarán con comparaciones que permitan medir su aportación. Las variantes que requieren datos ausentes quedan condicionadas a obtenerlos o reformularlas.

## Fuente y documentos relacionados

- [Propuesta compartida en Gemini](https://share.gemini.google/d9DH352vPdnd), leída en navegador. La redirección observada apunta a https://gemini.google.com/share/fb23eb65536d. La fuente es una propuesta asistida por IA, no una regla del concurso ni un resultado del proyecto. Su procedencia y las afirmaciones revisadas están en [fuente_gemini.json](fuente_gemini.json).
- [Contrato oficial sintetizado](../../REGLAS_2026.md) y [páginas oficiales archivadas](../../../Preparación/artifacts/verification/iaa_launch_20261016/pages/).
- [Auditoría actuarial de datos](../Analisis/README.md) y [transformaciones trazables de identificadores y exposición](../Limpieza/README.md).
- [Memoria general](../../../Preparación/MEMORIA_PROYECTO.md), con la estrategia de envíos D29, y [prácticas IAA priorizadas](../../../Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md).
- [Catálogo de experimentos](experimentos.json), preparado para registrar el estado de cada candidato. Es una especificación, no una configuración ejecutable del runner actual.

## Contrato común de las pruebas

La predicción será el coste último esperado en CU del periodo cubierto de cada fila de 2025, neto de franquicia y recuperaciones y excluyendo rechazados. Incluye las tres carteras y respeta la exposición de cada subperiodo. La prima comercial escrita no es el objetivo. Cada entrega contiene `row_id,prediction` para todas las filas de los tres test.

La métrica oficial es Tweedie D² con potencia 1,5, mayor es mejor. Usaremos como cálculo local principal D² sobre importes del periodo sin pesos adicionales, declarado como aproximación operativa hasta disponer del código completo del scorer. Calcularemos también desviación Tweedie y diagnósticos por ramo. No promediar los D² de los ramos para afirmar que se obtuvo el D² global: sus referencias y denominadores difieren.

Los experimentos compartirán versión de tablas, definición del objetivo, disponibilidad de predictores, particiones y protocolo de selección. Cambiar el ajuste de IBNR a la vez que el algoritmo impide atribuir la mejora al modelo. Se conservarán las predicciones fuera de muestra y sus `row_id`, con identificación de la partición y de la versión del objetivo.

## Qué corregir antes de adoptar la propuesta

| Afirmación o supuesto de la fuente | Análisis para nuestros datos | Tratamiento acordado para las pruebas |
| --- | --- | --- |
| Reconstruir trayectorias históricas de expedientes abiertos y luego cerrados | `claims` contiene una sola valoración al cierre de 2024. No contiene pagos por fecha, historia de reservas ni fecha de cierre | No construir estados pasados inventados. Mantener una proxy observable y escenarios explícitos de desarrollo; reservar micro-reserving supervisado para datos longitudinales adicionales |
| Reconciliar con un triángulo trimestral de pagos Chain-Ladder | Sin movimientos o snapshots históricos no se identifican las celdas de desarrollo de pagos/incurridos | Se puede estudiar ocurrencia frente a notificación para conteos reportados; ese triángulo no es un triángulo de pagos ni identifica por sí solo el último |
| Estimar una distribución de retrasos con todos los siniestros observados | Los retrasos largos de cohortes recientes no están observados al corte: hay truncamiento por la derecha | Estimar con cohortes suficientemente maduras o un método que trate truncamiento, y documentar estabilidad y sensibilidad; no aplicar una CDF empírica global sin corrección |
| Usar vectores telemáticos horarios y de velocidad | El esquema verificado ofrece `telematics_opt_in` y `telematics_score`; no ofrece trayectos, histogramas horarios, peso o potencia del vehículo | Un CANN tabular puede usar variables disponibles tras revisar su fecha de disponibilidad. La reproducción telemática completa del paper queda fuera del alcance de estos archivos |
| Usar `occurrence_date` y `lob` como columnas | Los nombres efectivos son `loss_date` y `line` | Traducir conceptos al esquema real; enlazar por póliza, ramo e intervalo cubierto |
| Asignar todos los siniestros a una póliza y cuadrar el total sin excepciones | La auditoría D30 separó 414 siniestros anteriores al primer periodo observado | Conservar asignados, excluidos por rechazo, ambiguos y fuera de ventana; reconciliar categorías sin forzar asignaciones ni duplicar importes |
| Evaluar importes o tasas ponderadas como si fueran equivalentes en toda formulación | La equivalencia depende de la potencia, los pesos y la referencia del D² | Aplicar la identidad de desviación detallada más abajo; comparar formulaciones, sin prometer invarianza ante un scorer desconocido |
| Imponer balance de cartera y regresión isotónica para mejorar necesariamente el score | Cuadrar una suma en calibración no asegura mejorar D² ni calibrar datos futuros | Probar calibración como experimento separado y evaluarla en una partición no usada para ajustarla |
| Interpretar `min_child_weight` o `min_data_in_leaf` como años de exposición | El primero controla suma de Hessianos; el segundo, observaciones o su aproximación, según biblioteca | Medir exposición, número de filas y siniestros por hoja como diagnósticos propios. No declarar un mínimo de años-póliza a partir de esos parámetros |
| Gamma sin restricciones de dominio | Gamma requiere respuestas positivas; no admite directamente las filas sin siniestros | Ajustar severidad Gamma solo sobre observaciones positivas admisibles. Tweedie directo contempla ceros en la respuesta |
| `init_score` como parámetro de CatBoost | CatBoost usa `baseline` en `Pool`; LightGBM usa `init_score`; XGBoost, `base_margin` | Construir y comprobar adaptadores distintos, incluida la escala del margen y su uso en inferencia |
| Un modelo conjunto destruye necesariamente la estructura de los ramos | Un modelo conjunto con indicador de ramo e interacciones también puede aprender diferencias y compartir información | Comparar modelos separados y un modelo conjunto sobre las mismas particiones |
| El híbrido es superior, CatBoost en dos etapas mejora más del 17% y ciertos gráficos tendrán valores concretos | La fuente no aporta una corrida reproducida en este concurso que sostenga esas cifras | Registrar como afirmaciones no verificadas; no convertirlas en expectativa de mejora ni en resultados propios |
| Rechazos históricos como prueba directa de riesgo moral | Un rechazo puede tener causas contractuales, administrativas o de cobertura | No atribuir conducta indebida. Una señal histórica solo se estudia con disponibilidad temporal y revisión de sesgo e interpretación |
| Los papers IAA constituyen normas regulatorias | Las referencias priorizadas del proyecto son educativas; su uso no certifica cumplimiento | Aplicar sus prácticas con evidencia del caso y distinguir revisión propia, humana e independiente |

Los rangos de potencia por ramo, pisos de predicción, umbrales SHAP, tolerancia de balance y supuestos de cola de la fuente tampoco son parámetros oficiales ni valores estimados de nuestra cartera. Si se exploran, serán hiperparámetros o escenarios declarados. SHAP cercano a cero no demuestra que un GLM haya capturado toda la señal, y su descomposición no establece causalidad.

## Objetivo observable y desarrollo a último

Antes del modelado, terminar la asignación de siniestros y conservar una tabla auditable por periodo. La proxy del EDA suma incurrido neto de recuperaciones de siniestros aceptados con asignación temporal única. Es una observación al corte, no una etiqueta última. Revisar el significado de importes, valores negativos y reconciliación antes de fijar una política para cualquier caso fuera del dominio no negativo.

La primera comparación de algoritmos usará una versión congelada de esa proxy, claramente etiquetada. Evaluará capacidad predictiva respecto de la proxy, sin afirmar que mide error contra el último oculto. Otra comparación estudiará escenarios de maduración de abiertos y completitud de reporte por ramo, estimados solo con la información permitida en cada corte. Cada escenario conservará supuestos, procedencia y efectos sobre totales y selección de modelos.

Los siniestros antiguos cerrados permiten una sensibilidad sobre cohortes más maduras; entrenar solo con ellos introduce selección por cierre y no produce automáticamente factores de desarrollo para los abiertos. El supuesto de que un cerrado no reabre y de que las recuperaciones ya son completas debe declararse. No convertir predicciones del propio modelo en verdad de validación: una etiqueta ajustada por modelo sigue siendo una estimación.

Los ajustes de frecuencia por exposición efectiva requieren una distribución de notificación identificable y supuestos sobre la ocurrencia dentro del periodo. Aplicar un ajuste de exposición y otro al objetivo por el mismo IBNR duplicaría la corrección. Tampoco compensar desarrollo tardío, inflación y diferencias de cartera con un único factor presentado como estimación identificada.

## Métrica y exposición

Para importes no negativos `y` y predicciones positivas `m`, la desviación unitaria a potencia 1,5 se simplifica a:

```text
d_1.5(y, m) = 4 * (y / sqrt(m) - 2 * sqrt(y) + sqrt(m))
d_p(e*r, e*q) = e**(2-p) * d_p(r, q)
```

La segunda igualdad es una derivación algebraica de la desviación Tweedie. Con potencia 1,5, el peso equivalente de la tasa es `sqrt(e)`. Por tanto, minimizar desviación de importes sin pesos equivale a minimizar la suma de desviaciones de tasas ponderadas por `sqrt(e)`, para las mismas filas y exposiciones positivas. La media ponderada puede cambiar por su normalizador. El D² tampoco tiene necesariamente el mismo valor porque cambia su referencia constante. Ponderar tasas por `e` es otra función objetivo, aunque sea una formulación actuarial habitual. La evidencia numérica de estas diferencias se conservará en `verificacion_metrica.json`; usa datos sintéticos y no puntúa un modelo del concurso.

Para una predicción anual `q`, la salida de periodo es `e*q`. Un offset logarítmico sobre importes es `log(e)`; no multiplicar por exposición otra vez si el modelo ya predice importes. Documentar cuál de ambas escalas usa cada adaptador.

Comparar entrenamiento con tasas y peso `e` frente a `sqrt(e)` cuando sea pertinente, y puntuar siempre la salida final en CU por periodo. Las diferencias responden a objetivos de ajuste distintos. Un peso por exposición adicional sobre importes no se da por oficial.

Para calibración multiplicativa de importes, comparar sin calibrar, balance agregado y optimización Tweedie. Con `p=1.5`, pesos fijos `w`, predicciones positivas `m` y sin otras restricciones, el factor que minimiza la desviación de `c*m` en el conjunto de calibración es:

```text
c_tweedie = sum(w*y/sqrt(m)) / sum(w*sqrt(m))
c_balance = sum(y) / sum(m)  # balance agregado sin pesos
```

La primera expresión se obtiene al derivar respecto a `c`; no coincide en general con la segunda. Un caso con todos los objetivos cero necesita un tratamiento explícito del límite y del piso positivo. Ambos factores, la isotónica y cualquier piso se estiman dentro del entrenamiento/calibración, nunca con las etiquetas de la evaluación final. Un piso técnico protege el dominio numérico; subirlo para mejorar el score es otra decisión que exige validación.

## Validación temporal y disponibilidad de variables

La comparación principal será prospectiva: entrenar con periodos anteriores y evaluar un año posterior, inicialmente 2021–2022 frente a 2023 y 2021–2023 frente a 2024, si la cobertura efectiva lo permite. Las renovaciones del mismo cliente entre pasado y futuro no son por sí mismas fuga: forman parte de la cartera futura que queremos predecir. El historial usado debe existir antes de la predicción. Medir por separado clientes o direcciones conocidos y nuevos.

La limitación es material: la única valoración de importes es de diciembre de 2024. Filtrar `loss_date` no reconstruye lo que se sabía en enero de 2023. Para hacer un backtest estrictamente histórico faltan snapshots de importes, estado y maestros. Mientras no existan, documentar el experimento como validación temporal sobre la proxy disponible y su información posterior al corte simulado. Excluir importes de historial no reconstruibles, controlar `report_date` y separar la fecha de información de predictores de la fecha de madurez del objetivo.

Como prueba secundaria, evaluar clientes/direcciones no vistos. Las componentes del grafo cliente-dirección pueden usarse para separar entidades conectadas, después de medir tamaños y equilibrio. No imponer cinco particiones si una componente dominante lo impide. Esa prueba mide generalización a entidades nuevas; no sustituye al salto temporal de una cartera con renovaciones.

Dentro de cada partición, ajustar imputaciones, codificaciones por objetivo, credibilidad, base GLM, selección de variables y calibración solo con el entrenamiento pertinente. El esquema necesita un bloque interno para ajuste y calibración y otro externo para evaluación. Si se usan predicciones de un modelo de edificios como variable de contenidos, generarlas sin acceso a etiquetas de la fila o entidad retenida.

Los agregados de clima 2021–2024 son utilizables como información histórica para una decisión de 2025 bajo el supuesto declarado de disponibilidad. No calcularlos con 2024 para predecir 2023. El clima realizado de 2025, los contactos de servicio y la telemática necesitan una fecha de disponibilidad: estar presentes en test no demuestra que existieran al suscribir. Comparar bloques con y sin variables de disponibilidad dudosa. `renewal_decision` queda fuera del modelo principal; su uso auxiliar no es una corrección automática de selección y requeriría una investigación separada.

## Portafolio de modelos y orden de comparación

Las fases indican dependencias de evidencia, sin un límite propio de horas o cómputo. Todos los candidatos están pendientes de implementación para el contrato del concurso, aunque el laboratorio anterior tenga estimadores de algunas familias.

| ID | Candidato | Hipótesis y diseño de prueba | Condición para avanzar |
| --- | --- | --- | --- |
| M00 | Tasa constante por ramo | Separar nivel de riesgo y exposición. Calcular tasa con entrenamiento y emitir coste de periodo | Referencia para comprobar métrica, escalas e IDs |
| M01 | GLM Tweedie | Enlace log, `p=1.5`, regularización y variables tarifarias disponibles; comparación de ponderaciones explícita | Referencia actuarial interpretable, salida positiva y validación temporal |
| M02 | GAM Tweedie | Añadir splines para edad, antigüedad y capital, sin asumir de antemano una forma óptima | Mejorar o complementar M01 con curvas estables fuera de muestra |
| M03 | GLM/GAM frecuencia por severidad | Poisson para frecuencia; estudiar binomial negativa si hay sobredispersión. Gamma para severidad positiva; por periodo o siniestro según diseño documentado | Conteo y coste compatibles, maduración documentada y comparación directa con Tweedie |
| M04 | LightGBM Tweedie | Capturar interacciones con regularización, parada temprana y `p=1.5` | Comparación con M01 sobre exactamente las mismas filas |
| M05 | XGBoost Tweedie | Otra construcción de árboles puede mejorar estabilidad o diversidad respecto a M04 | Medir calidad individual y errores complementarios |
| M06 | CatBoost Tweedie | Tratamiento de categorías con escala numérica de respuesta controlada | Invertir escala antes de puntuar; comprobar dominio y categóricas |
| M07 | CatBoost en dos etapas | Frecuencia Poisson y severidad positiva con una implementación compatible; comparar con CatBoost Tweedie directo | No usar `Tweedie:variance_power=2` como Gamma. No asumir que existe un objetivo Gamma nativo en esta versión |
| M08 | Credibilidad y GLMM | Añadir historia causal de póliza/cliente/dirección mediante contracción; comparar con la base sin historia | Definir exposición, modelo de varianza y disponibilidad de historia; recuperar media colectiva para entidades nuevas |
| M09 | GLM/GAM con boosting residual | `m_hibrido = m_base * exp(f(X))`, ajustando la pérdida sobre el objetivo no negativo | Congelar base dentro de cada entrenamiento; conservar margen log y verificar inferencia |
| M10 | CANN tabular | Usar la predicción positiva del GLM como rama fija y una MLP residual inicializada para reproducirla | Comparar con M01, M09 y una MLP independiente; adaptación al esquema real |
| M11 | MLP y FT-Transformer | Estudiar representaciones categóricas y diversidad frente a árboles | Codificaciones, escalas y vocabularios ajustados dentro de cada partición; medir coste y estabilidad |
| M12 | LocalGLMnet | Estudiar contribuciones dependientes de covariables y flexibilidad frente a GLM/CANN | Implementación contrastada con el paper; evaluar sensibilidad a escalado, correlación e identificabilidad, sin interpretar contribuciones como efectos causales |
| M13 | LocalGLMftt y CAFTT | Explorar atención tabular en modelos locales o combinados según Brauer, §§3.6–3.7 | Paper y repositorio del autor localizados; revisar código, licencia y adaptación de frecuencia Poisson a coste Tweedie antes de incorporarlos |
| M14 | CANN longitudinal Poisson/NB/MVNB | Incorporar dependencia entre contratos de un asegurado usando variables tabulares disponibles | Historial causal y especificación probabilística comprobada; variante adaptada, no reproducción de telemática granular |
| M15 | DRN | Refinar la distribución alrededor de una base y evaluar si mejora la media o diagnósticos de incertidumbre | Tratar explícitamente la masa en cero, colas y media final; validar la implementación, sin prometer protección frente a catástrofes |
| M16 | Combinación de predicciones | Mezcla de candidatos con errores complementarios; stacking solo después de una mezcla simple | Pesos y meta-modelo ajustados con predicciones internas fuera de muestra; conservar evaluación externa intacta |

Primera ronda: M00, M01 y M04–M06. Segunda: M02–M03, M07–M09 y comparación separado/conjunto. Tercera: M10–M15, con M13 condicionado a revisar la implementación y su adaptación al objetivo. M16 se evalúa cuando haya candidatos diversos con predicciones compatibles. No atribuir una mejora a la fase sin separar el efecto de datos, objetivo y calibración.

La referencia de Brauer sí define ambos modelos: CAFTT sustituye la red residual de un CANN por un FT-Transformer; LocalGLMftt genera los coeficientes locales mediante ese Transformer. Sus experimentos publicados tratan frecuencia y pérdida Poisson. Para este concurso se debe validar su uso en frecuencia-severidad o adaptar la salida y pérdida a Tweedie, sin trasladar los resultados del paper al coste último.

Probar inicialmente cada ramo por separado y comparar con un modelo conjunto que incluya ramo y atributos disponibles; medir D² global y resultados por ramo. Las variables multirramo se incorporarán en una comparación específica con y sin ese bloque. En edificios y contenidos, no corregir automáticamente capitales con saltos de escala: usar una versión de tratamiento explícita y su sensibilidad. En autos, estudiar la señal disponible de telemática sin fabricar información de trayectos.

## Notas de implementación que deben comprobarse

- LightGBM: `objective="tweedie"`, `tweedie_variance_power=1.5`. `init_score` pertenece al conjunto de datos y no debe suponerse guardado como parte del modelo base. Verificar composición explícita del margen base y salida residual en una recarga, evitando aplicar dos veces el enlace exponencial.
- XGBoost: `objective="reg:tweedie"`, `tweedie_variance_power=1.5`. Un margen base debe estar en escala logarítmica y proporcionarse también al predecir cuando corresponda. No confundirlo con `base_score`.
- CatBoost: `loss_function="Tweedie:variance_power=1.5"`. La documentación recomienda escalar etiquetas a [0,1000] en CPU y [0,1] en GPU. Fijar un factor con entrenamiento, guardar su inversa y puntuar en CU; no truncar etiquetas para alcanzar el rango. La inicialización es `Pool(..., baseline=...)`, no `init_score`. Comprobar la escala de `RawFormulaVal` y `Exponent` y el comportamiento del margen al cargar y predecir.
- Frecuencia-severidad: el componente de frecuencia debe representar conteo esperado o tasa declarada, no intercambiar ambos. Si se ajusta la severidad media de periodo, usar el número de siniestros como peso cuando la formulación lo requiera. Gamma sobre costes cero o negativos exige otro tratamiento, no un cambio silencioso de etiqueta.
- Híbridos: no calcular `log(y/m_base)` como respuesta de regresión sin resolver ceros. La ruta propuesta optimiza la pérdida Tweedie sobre `y` con un margen base, o define otra pérdida explícita.
- Potencia 1,7, restricciones monótonas y regularización son variantes que se comparan frente a la misma evaluación con potencia 1,5. Monotonicidad del capital o franquicia es una hipótesis de diseño condicionada a cobertura y cartera; no es una ley empírica ya verificada.

El lock de preparación declara scikit-learn 1.7.2, LightGBM 4.6.0, XGBoost 3.0.5 y CatBoost 1.2.8. Las páginas web pueden describir versiones posteriores: comprobar cada API en el entorno fijado antes de entrenar. M02 puede empezar con bases spline y regresión Tweedie; GAM especializados, GLMM y redes podrían requerir dependencias adicionales. Esta revisión no instala paquetes ni modifica el runner CSV de ensayo, que todavía necesita adaptación a Parquet, multitabla y D².

## Registro y criterios de comparación

Cada corrida conservará fuente y hash de datos, reglas de limpieza, lista de predictores y fechas de disponibilidad, versión del objetivo y supuestos de desarrollo, configuración completa, semillas, entorno, particiones, código, predicciones fuera de muestra y archivo final. Registrar tiempo y memoria observados, sin estimarlos como resultados antes de correr.

La comparación incluirá D² global sobre las mismas filas y referencia, desviación por ramo y periodo, estabilidad entre cortes, razón agregado predicho/observado y bandas por segmentos con suficiente exposición. Los gráficos de calibración y doble lift se construirán a partir de predicciones retenidas, mostrando tamaños y variabilidad; sus curvas no tienen valores esperados prefijados. Analizar sensibilidad a cola, extremos y maduración sin eliminar siniestros del score principal.

Separar la comparación sin calibración de la calibrada. Ajustar balance o isotónica en un bloque interno y medir su efecto en otro. Un ajuste exacto del total dentro de calibración no acredita balance futuro. Para investigar heterogeneidad o sesgo, estudiar segmentos pertinentes sin atribuir mecanismos causales a asociaciones o a rechazos.

Un candidato avanza cuando aporta mejora o diversidad reproducible fuera de muestra, sin deterioro material no explicado en ramos o cohortes, y con supuestos defendibles. Fijar tolerancias y criterio de selección antes de abrir la evaluación externa; la variabilidad observada y la materialidad actuarial orientarán esos valores. No importar el umbral 0,1% de balance o 0,15 de SHAP de la fuente como norma del proyecto.

Conservar la política D29: hasta cinco envíos diarios como máximo provisional, sin obligación de agotarlos; cada envío responde a una hipótesis respaldada por validación. Guardar archivo exacto, versión, score público y diferencias frente a la validación local. Las referencias de la captura del participante (GLM 0,10563 y muestra 0,07169) son puntos públicos históricos de comparación, no objetivos garantizados ni puntuaciones propias.

## Relación con la evaluación profesional y la Parte 2

El plan conserva evidencia del uso de IA y de las decisiones humanas sobre propuestas aceptadas, modificadas o rechazadas. Documentar la intervención efectiva, sin inventar una revisión humana o independiente. Las prácticas IAA aplicables son propósito y límites (§3.1), comunicación y responsabilidad (§§3.2, 3.5–3.6), documentación de datos/modelo (§§2–3) y validación/gobernanza (§2.8).

Para la Parte 2 se medirá qué cambia en variables, faltantes, escalas y mezcla de riesgos antes de reutilizar modelos. Comparar transferencia sin cambios, recalibración y reentrenamiento permitido. Un tronco GLM puede ayudar a explicar o adaptar, pero no garantiza extrapolación correcta ni superioridad en un mercado nuevo. Mantener módulos separables de datos, objetivo, predictores, modelo y calibración.

La rúbrica combina rendimiento y adaptación 40%, uso de IA 25%, confianza/validación 20% y comunicación/documentación 15%. El leaderboard no sustituye ese juicio. Esta documentación prepara las pruebas; quedan pendientes el objetivo operativo, la disponibilidad temporal y la implementación del flujo. No se ha entrenado ni enviado ningún candidato como parte de esta revisión.

## Fuentes primarias para implementar

Consultadas el 16 de octubre de 2026. Las referencias describen métodos o APIs; sus resultados no se trasladan a nuestra cartera.

- [Ejemplo actuarial Tweedie de scikit-learn](https://scikit-learn.org/stable/auto_examples/linear_model/plot_tweedie_regression_insurance_claims.html): formulaciones de prima pura y frecuencia-severidad.
- [Desviación Tweedie](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_tweedie_deviance.html) y [D²](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.d2_tweedie_score.html): dominio y cálculo de métricas.
- [Parámetros LightGBM](https://lightgbm.readthedocs.io/en/stable/Parameters.html): Tweedie, regularización y límites de hojas.
- [Márgenes e intercepto en XGBoost](https://xgboost.readthedocs.io/en/release_3.0.0/tutorials/intercept.html) y [objetivos](https://xgboost.readthedocs.io/en/release_3.0.0/parameter.html): enlace, offset y parámetros.
- [Fuente oficial de pérdidas CatBoost](https://github.com/catboost/catboost/blob/master/catboost/docs/en/concepts/loss-functions-regression.md) y [Pool](https://catboost.ai/docs/en/concepts/python-reference_pool): Tweedie, escalas y baseline.
- [Schelldorfer y Wüthrich, Nesting Classical Actuarial Models into Neural Networks, 2019](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3320525): GLM anidado e inicialización.
- [Richman y Wüthrich, LocalGLMnet](https://arxiv.org/abs/2107.11059): arquitectura local e interpretación. El preprint es de 2021; distinguirlo de fechas de publicación posteriores.
- [Brauer, Enhancing Actuarial Non-Life Pricing Models via Transformers](https://arxiv.org/abs/2311.07597), [definiciones en §§3.6–3.7](https://arxiv.org/html/2311.07597v2) y [repositorio del autor](https://github.com/BrauerAlexej/Enhancing_actuarial_non-life_pricing_models_via_transformers_Public): CAFTT y LocalGLMftt; preprint 2023, revisado en 2024. Código localizado, pendiente de inspección y comprobación de licencia antes de reutilizarlo.
- [Gorishniy y otros, Revisiting Deep Learning Models for Tabular Data](https://arxiv.org/abs/2106.11959) e [implementación de los autores](https://github.com/yandex-research/rtdl-revisiting-models): MLP, FT-Transformer y comparaciones sin superioridad universal.
- [Duval, Boucher y Pigeon, Telematics CANN](https://arxiv.org/abs/2308.01729): preprint 2023, publicación en ASTIN 2024; requiere vectores telemáticos para reproducir la formulación completa.
- [Avanzi, Dong, Laub y Wong, Distributional Refinement Network](https://arxiv.org/abs/2406.00998): refina una distribución base; su preprint inicial es de 2024.
