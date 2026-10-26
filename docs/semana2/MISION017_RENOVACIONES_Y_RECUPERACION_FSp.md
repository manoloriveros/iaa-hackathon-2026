

## Renovaciones y entradas completas de edificios, 26 de octubre de 2026 (Bogotá)

Codex, 2026-10-26T05:49:54.645025+00:00. La conciliación establece que F3c/F3b y F4c/F4b solo cambian el nivel de las seis celdas de renovación, dentro del redondeo de los CSV. Sin embargo, poner a cero el peso FSp de nuevo negocio en la receta K recibida no congela sus precios: también se vuelven a estimar factores comunes aplicados a ese negocio. No se atribuye pureza FSp a una diferencia entre los CSV compuestos. La fórmula original K además diluye los multiplicadores F2; la variante posterior F4b conserva esos multiplicadores. No son un replay idéntico.

Se conservó una composición provisional F3c/F4c solo para las renovaciones de motor y contenidos, registrada antes de construirla. Cambia37.504filas;171.559precios, incluido todo nuevo negocio y edificios, quedan exactamente iguales. Los totales de las dos celdas afectadas se mantienen antes del redondeo y la diferencia final conjunta es0,000051CU. Pasaron claves/orden, identidades, datos fuera de ámbito alterados, escala del donante y aritmética racional independiente. Es una composición del donante F4c con FSp y factores reestimados, no un componente FSp puro ni el K ausente. No tiene validación predictiva acreditada y no está lista para enviar.

Edificios en renovación no fue rechazado por la evidencia recibida. Falta en este CSV provisional porque F4c tiene peso cero en edificios; el objetivo sigue siendo evaluar la alternativa completa. Las previsiones recibidas para K favorecían la variante con edificios, pero no se trasladan numéricamente a nuestra composición. No se repitió el inventario del CSV K que ya faltaba.

Se conciliaron las12combinaciones fase/peligro de edificios: recuentos, marcas positivas y constantes de offset coinciden con los metadatos originales; el máximo error de b0 es0. Se restauraron las matrices desde los originales porque32variables fuente estaban cuantizadas a float32. Pasaron45controles de fuente al aplicar su redondeo original y45de histórico emergente en precisión completa. Hay523.725filas fuente en desarrollo,707.726en producción y79.742filas emergentes por fase, incluidas52.295de2025. Clima separado: fuente2021–2023/emergente2023 para desarrollo; fuente2021–2024/emergente2023–2024 para producción. No se leyó clima2025. El historial termina en min(inicio,2024-12-31), ventana de365días [inicio,fin); se cotejó por otro método y con casos de frontera. No está acreditada la opción ambiental usada por FSp original en2025, por lo que cualquier recuperación será una reconstrucción nueva.

Los productores recibidos no guardaban Boosters. Antes de reconstruirlos se registró la receta de24ajustes fuente de edificios (Poisson/Gamma, seis peligros, dos fases), con las rondas existentes y sin nueva búsqueda. Se reutilizan C0 y las constantes guardadas. La frecuencia mantiene el offset de completitud de coste: f*s sigue siendo un proxy de coste y no identifica frecuencia de último por separado. El productor guardará modelos y componentes por fila; no estima pesos nuevos, no puntúa ni produce un CSV para enviar.

Esta conciliación y preparación suman cero ajustes, cero C0 y cero envíos; sí se creó un CSV provisional con37.504precios derivados y dos normalizaciones sin etiquetas, contados aparte. El productor tiene su propio presupuesto de24ajustes reales. El mejor recibo sigue en0,16914 y faltan0,00086para0,17. La cuota consultada sigue siendo0 y el trabajo local continúa. B00/F2/C1/F3c, versiones fallidas y todas las alternativas permanecen;2024está abierto como desarrollo adaptativo. La revisión es propia y exploratoria, sin certificación de mejora ni aprobación humana inventada.

Evidencia:

- received_semantics_audit: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/renovacion_fsp_recepcion_20261026_v1/audit.json
- provisional_candidate: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/renovacion_fsp_composicion_20261026_v1/report.json
- count_offset_inputs: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/FSp_edificios_recuperacion_entradas_20261026_v1/report.json
- raw_precision_matrices: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/FSp_edificios_matrices_20261026_v1/report.json
- producer_plan: Hackaton/Repositorio_IAA2026/registro/semana2_mision017_FSp_edificios_recuperacion_plan_v1.json


## Productor numérico de edificios recuperado, 26 de octubre de 2026 (Bogotá)

Codex, 2026-10-26T05:50:28.264793+00:00. Se completaron los24modelos fuente registrados de edificios con rondas fijas, sin búsqueda nueva ni reestimación de C0. Se guardaron todos los Boosters, metadatos, puntuaciones brutas y componentes f/s para79.742filas emergentes en cada fase. La fuente de desarrollo cubre2021–2023y la de producción2021–2024; no se cargaron respuestas emergentes. Los24modelos pasaron reproducción exacta al guardar/cargar y al cambiar el orden de las filas. La suma independiente de hojas y el cálculo separado de exponenciales/offset/exposición también coinciden. Los SHA de entrada permanecieron iguales y los componentes son finitos y positivos.

Son componentes nuevos de modelo, incluidos los de test2025, y no se oculta ese coste:24ajustes fuente y1.913.808predicciones de componente antes de los replays. No son24calibraciones de objetivo emergente ni un nuevo CSV agregado. No hubo C0, búsqueda de rondas, puntuación predictiva o envío. La reconstrucción conserva la limitación del offset de coste y la opción explícita historia2; no acredita los árboles originales bit a bit ni mejora de F3c.

El faltante del productor de edificios quedó resuelto para una comparación posterior; aún falta esa comparación por grupos y años, la separación de efectos FSp/factores en motor y contenidos y la validación del candidato completo de renovación. Antes de puntuar se registrarán comparador, pesos fijos, C0 reutilizado, grupos y criterio. No se escogerán pesos para perseguir0,17con el público. B00 y todas las alternativas permanecen,2024abierto. El mejor recibo procesado sigue0,16914; objetivo no alcanzado.

Evidencia:

- received_semantics_audit: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/renovacion_fsp_recepcion_20261026_v1/audit.json
- provisional_candidate: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/renovacion_fsp_composicion_20261026_v1/report.json
- count_offset_inputs: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/FSp_edificios_recuperacion_entradas_20261026_v1/report.json
- raw_precision_matrices: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/FSp_edificios_matrices_20261026_v1/report.json
- producer_plan: Hackaton/Repositorio_IAA2026/registro/semana2_mision017_FSp_edificios_recuperacion_plan_v1.json
- numerical_producer: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/FSp_edificios_productor_20261026_v1/report.json


## Edificios en renovación: contraste adverso conservado, 26 de octubre de 2026 (Bogotá)

Codex, 2026-10-26T05:58:35.136847+00:00. Se completó el único contraste registrado del componente recuperado: peso fijo del 25 % en edificios en renovación, sin cambiar nuevo negocio, los otros ramos o los totales de precio por año. El denominador conserva los multiplicadores de prior claims de N3; los componentes se anualizaron por la exposición original del productor y se aplicó una sola vez la exposición canónica. Se reutilizaron los cinco ámbitos globales y sus C0. Las treinta constantes por peligro se estimaron exclusivamente en entrenamiento.

| Medida | Resultado |
|---|---:|
| D² N3 | 0.13524973 |
| D² alternativa ER1 | 0.13540500 |
| Diferencia global | +0.00015527 |
| IC 95 % por grupos, condicionado a fuente fija | [-0.00115241; +0.00155308] |
| Aporte global de 2023 | +0.00036245 |
| Aporte global de 2024 | -0.00020718 |
| Tras retirar 31 grupos favorables, mismo denominador global | -0.00217443 |
| Sin los 31 grupos de mayor coste observado | -0.00019416 |

Tres de cinco folds empeoran. El intervalo incluye pérdidas; 2024 pierde y el contraste por renovación de edificios de ese año también incumple el umbral por celda registrado. La ganancia media no es robusta y queda por debajo del mínimo global de +0,002. Se conservan la alternativa, los modelos y todas las salidas; no se incorpora este cambio ni se genera otro CSV de envío por este resultado. Las previsiones positivas recibidas para K no se trasladan: esta reconstrucción, la fórmula y el ámbito son distintos.

El comparador es N3, no el F3c completo. No está disponible aquí el contraste íntegro F3c/F2 ni los vetos de sensibilidad2025/A1, por lo que también faltan esos requisitos. No se confunde un fallo del contraste actual con una prueba de que cualquier FSp futuro de edificios deba retirarse. El bootstrap condiciona a los modelos fuente guardados y no incluye su incertidumbre. La valoración a diciembre de 2024, los maestros sin fecha y el desarrollo adaptativo limitan la interpretación prospectiva.

Pasaron los controles numéricos y de fuga del flujo nuevo: etiquetas retenidas totales y por peligro alteradas sin efecto en el aprendizaje o las predicciones, exclusión de grupos, integración independiente de C0, reproducción con parámetros guardados sin estimar, exponenciales/normalización por otra fórmula y pérdida Tweedie contrastada con scikit-learn. Los controles mecánicos no corrigen el deterioro predictivo. Coste de este contraste: 30 constantes de precio por peligro, 10 normalizadores de predicciones, cero árboles, C0, precios de test o envíos; las 30 recomputaciones idénticas del control adverso se cuentan aparte. Los 24 ajustes fuente de la recuperación anterior ya estaban contabilizados y no se suman de nuevo.

La comprobación acotada de las dos carpetas FSp recibidas encontró solo los cuatro metadatos de motor/contenidos, sin sus Parquet numéricos. Se guarda el inventario exacto y no se afirma ausencia global. El siguiente paso es resolver ese faltante para separar el componente FSp de los factores del donante compuesto, antes de otra comparación o envío. B00, F2/C1/F3c y las versiones fallidas se mantienen; 2024 está abierto por autorización humana. El mejor recibo continúa en 0,16914 y faltan 0,00086 para 0,17. La cuota 0 impide otro envío por ahora, pero el trabajo local sigue.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/FSp_edificios_REN_contraste_20261026_v1/report.json.

Siguiente unidad: FSp de edificios ya está reconstruido y su inserción REN .25 no pasó: no repetir esos24fits,30constantes o bootstrap. Mantener la alternativa y B00/F2/C1/F3c. La composición F3c/F4c REN motor/contenidos sigue provisional y no es FSp puro. Primero buscar de forma acotada salidas numéricas motor/contents f/s en otras rutas recibidas pertinentes, sin repetir las dos carpetas ya inventariadas ni el inventario K. Si no existen, preparar entradas de precisión completa de esos dos ramos y conciliar metadatos ya presentes usando los recuentos y C0 existentes; no reconstruir los edificios otra vez. Registrar la necesidad, rondas fijas, coste y foro antes de cualquier recuperación fuente adicional. El propósito es aislar FSp de los factores y contrastar en los mismos grupos antes de considerar un envío. No relajar criterios ni retocar pesos por el resultado adverso de edificios o el score público.2024abierto como desarrollo; cuota0; meta0.17activa.


## Motor y contenidos: componentes fuente recuperados, 26 de octubre de 2026 (Bogotá)

Codex, 2026-10-26T06:10:19.210262+00:00. Se completó la recuperación registrada de motor y contenidos: 36 modelos Poisson/Gamma con las rondas fuente existentes, sin nueva búsqueda ni reestimación de C0. Pasaron 196 cotejos de precisión de variables y 18 comprobaciones de recuentos, marcas y offsets. Se guardaron todos los modelos y sus salidas f/s/brutas para las fases fuente 2021–2023 y 2021–2024. El historial usa explícitamente el corte min(inicio,2024-12-31), y el clima se limita a las ventanas históricas por fase. No se leyó clima 2025 ni respuestas emergentes en este productor.

Los 36 modelos pasaron la reproducción exacta al guardar/cargar y al invertir el orden de las filas. Se comprobó la suma independiente de hojas y la aplicación del offset/exposición por otra fórmula. Todos los componentes son finitos y positivos; las fuentes conservaron sus huellas. La recuperación produce componentes nuevos para 2025 y ese trabajo se cuenta, aunque todavía no exista un nuevo precio agregado: 4369088 predicciones de componente antes de replays. No se reivindica identidad bit a bit con árboles originales no guardados.

El inventario de los aportes recibidos se conservó: tres raíces, sin Parquet FSp ni archivos de modelos numéricos disponibles en ellas; no es una afirmación de ausencia global. Las dos carpetas ya revisadas y la búsqueda K anterior no se repitieron. El código y la receta son de Claude; esta reconstrucción, verificaciones y registro son de Codex. No equivalen a revisión profesional independiente.

La revisión del código de calibración recibido encontró kf/ks/kg y contracción fija n/(n+100). La prueba adversa anterior de edificios usó otra igualación de coste, sin contracción, y sigue guardada con ese ámbito. Antes de comparar el componente recuperado se registrará la diferencia de receta y el uso de C0 retenido por grupos; no se retocará K o el peso por el score adverso. La frecuencia conserva la semántica de proxy basada en completitud de coste, con reservas y cola de último no identificadas. Los maestros sin fecha también siguen condicionados.

Coste nuevo: 36 ajustes fuente, cero C0, calibraciones emergentes, scores o envíos. Los 24 modelos anteriores de edificios no se ajustaron otra vez. Quedan 167 ajustes nuevos en la fase y 1.503 en el contador propio acumulado; se preserva el linaje de esos conteos. El mejor público continúa en 0,16914, con 0,00086 pendientes para 0,17. B00, F2/C1/F3c, los fallos y las alternativas quedan guardados. 2024 permanece abierto como desarrollo adaptativo y la cuota 0 se conserva para el siguiente periodo.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/FSp_MC_recuperacion_20261026_v1/productor/report.json; matrices: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/FSp_MC_recuperacion_20261026_v1/matrices/report.json; semántica de calibración recibida: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/FSp_MC_recuperacion_20261026_v1/calibracion_recibida_contrato.json.

Siguiente unidad: Los36modelos MC y los24de edificios ya están completos, con matrices/modelos/componentes guardados: no repetirlos. Preparar y registrar un contraste único de FSp aislado sobre la referencia G3 de factores residuales guardados, sin reestimarlos, solo REN y pesos fijos recibidos motor.25/buildings.25/contents.5. La calibración recibida contiene kf/ks/kg y n/(n+100), distinta de la igualación de coste sin contracción probada antes en edificios; documentar esa necesidad y adaptar expresamente a C0 protegido por grupos, sin llamarlo replay exacto de F4c. Usar los ámbitos guardados, exposición una sola vez, NB/total de celda fijos y los criterios sin relajar. Registrar antes de estimar constantes o puntuar. Sin nuevos árboles/C0/test/envíos en el contraste. El F3c completo sigue como comparador no reproducido íntegramente; G3 es proxy.2024abierto;cuota0;meta0.17activa.


## FSp aislado sobre G3: señal favorable, concentración pendiente, 26 de octubre de 2026 (Bogotá)

Codex, 2026-10-26T06:25:39.845489+00:00. Se completó el contraste único registrado de FSp en renovación: pesos motor/edificios de 0,25 y contenidos de 0,5, con los factores residuales G3 guardados, sin reestimarlos. Se mantuvieron exactamente nuevo negocio y los totales por año/ramo. Se usó la calibración recibida kf/ks/kg con contracción n/(n+100), adaptada expresamente al C0 protegido por grupos. No es el F4c/K original ni la igualación de coste sin contracción de la prueba anterior de edificios.

| Medida | Resultado |
|---|---:|
| D² G3 | 0.13709993 |
| D² RFS1 | 0.13868724 |
| Diferencia | +0.00158732 |
| IC 95 % por componentes | [+0.00007185; +0.00315472] |
| Aporte global de 2023 | +0.00090664 |
| Aporte global de 2024 | +0.00068068 |
| Sin los 31 grupos más favorables, mismo denominador | -0.00121593 |
| Sin los 31 grupos de mayor coste observado | +0.00111381 |

Los cinco folds son positivos y ambos años ganan. El intervalo condicionado a los modelos fuente también es positivo. Aun así, la diferencia no llega al mínimo global de +0,002 y no resiste retirar los 31 grupos más favorables. Retirar los grupos de mayor coste observado mantiene una ganancia: esa comprobación distinta no sustituye el fallo de influencia. No se relaja el criterio ni se admite un envío por la media favorable.

| Ramo, solo renovación | Aporte 2023 al D² global | Aporte 2024 al D² global |
|---|---:|---:|
| motor | +0.00011269 | +0.00025628 |
| buildings | +0.00042564 | -0.00003003 |
| contents | +0.00036830 | +0.00045443 |

Motor y contenidos ganan en ambos años. Edificios mejora en 2023 y pierde ligeramente en 2024 con esta receta; los modelos, variantes y fallos quedan conservados. La separación del componente frente a G3 es ahora numérica y no una atribución a partir de CSV compuestos con factores reestimados. G3 sigue siendo un sustituto: el comparador F3c/F2 completo y sus vetos no están reproducidos íntegramente. No se asigna al público de F3c la mejora local de este contraste.

El primer intento falló antes de puntuar por un valor de control -1e30 que no cabe en int64. Se guardó el fallo, se cambió solo el payload adverso a un entero negativo válido y se preinscribió v2 antes de continuar. Las funciones matemáticas learn/apply/G3 conservaron su AST y los parámetros, criterios y bootstrap fueron idénticos. Se reutilizaron los 11 momentos de motor/fold0 ya guardados, sin estimarlos otra vez; los otros 154 se calcularon una sola vez. El control adverso recomputa esos mismos 165 momentos por separado y no añade parámetros distintos.

Pasaron los 15 controles del flujo real: costes, recuentos y reservas retenidos alterados sin efecto; reproducción exacta de los artefactos guardados sin aprender; identidad de peso cero; orden de claves; suma independiente de momentos y aritmética por otra fórmula. La pérdida coincide con scikit-learn. El bootstrap por componentes usa 2.000 réplicas y recalcula el nulo por fórmula cerrada en cada réplica; la incertidumbre fuente queda condicionada a sus modelos fijos. Estas verificaciones no eliminan la concentración ni acreditan prospectividad.

Coste: 15 niveles globales de coste, 75 momentos de frecuencia y 75 de marca; 75 factores contraídos derivados que no se cuentan otra vez como ajustes. Hay 30 normalizadores sin etiquetas, cero modelos/C0 nuevos, precios de2025 o envíos. Los 36 ajustes MC y los 24 de edificios ya estaban contabilizados. 2024 es desarrollo adaptativo y se mantienen los límites de maestros sin fecha, completitud de coste, cola y reservas. El mejor recibo sigue en 0,16914, sin alcanzar 0,17; B00, F2/C1/F3c y todas las alternativas permanecen.

Queda una diferencia concreta del flujo a resolver antes de preparar la producción: la referencia T2b/G3 usa fuente 2021–2024 para ambos años, mientras FSp usó 2021–2023 al evaluar 2023 en este contraste. La predicción 2025 usará fuente 2021–2024. Ese control de consistencia debe registrarse por adelantado y no convertirse en una elección de ventana por score. También se registró la búsqueda por tags exactos del A1 corregido de tres semillas: no aparecieron sus modelos o relatividades históricas en las raíces indicadas, aunque el productor original sí los guardaba. No se presenta el A1 original de2024 como su sustituto corregido.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/FSp_REN_G3_contraste_20261026_v2/report.json.

Siguiente unidad: RFS1 está completo:15ámbitos,165momentos únicos (11reutilizados de v1 y154nuevos en v2),sin nuevos árboles/C0. No repetirlo, retocar K/pesos o ocultar el fallo post31. Siguiente incertidumbre concreta: alinear el flujo de despliegue con la fuente2021–2024 disponible para ambos años objetivo. G3/T2b usa el padre fuente2021–2024 en2023/24, mientras el primer FSp usó dev2021–2023 en2023; la producción2025 necesita prod2021–2024. Registrar antes un control de consistencia usando únicamente las salidas prod ya guardadas, sin nuevos modelos, conservando todos los demás parámetros y criterios. No elegir la ventana por el mejor score ni reescribir RFS1. Además, sigue faltando el comparador F3c/F2 completo: el A1 corregido de tres semillas no tiene archivos históricos/modelos con los tags exactos en la búsqueda registrada (el código original sí los guardaba). No repetir ese inventario; revisar el contrato/offset/matrices y metadatos de rondas de ese productor antes de proponer una reconstrucción, no usar el A1 original2024como si fuera el corregido. No hay CSV nuevo listo o aprobado para enviar. Cuota0conservada,2024abierto,B00/alternativas preservados,meta0.17activa.


## Despliegue FSp y prototipo2025: mejora parcial, nuevo negocio pendiente, 26 de octubre de 2026 (Bogotá)

Codex, 2026-10-26T07:11:27.519001+00:00. El control RFS1P usa los mismos productores fuente 2021–2024 y clima emergente 2023–2024 que el despliegue previsto. Sustituyó solo los componentes f/s de 2023 del contraste anterior; G3, grupos, C0, pesos, KP100, normalización y criterios quedaron iguales. Los 60 modelos ya guardados no se ajustaron otra vez. Este es un control del flujo disponible al corte de diciembre de 2024, no una predicción prospectiva de 2023 con información entonces disponible.

| Medida | Resultado |
|---|---:|
| D² G3 | 0.13709993 |
| D² RFS1P | 0.13894530 |
| Diferencia global | +0.00184537 |
| IC 95 % por componentes, fuente fija | [+0.00044928; +0.00324372] |
| Tras quitar los 31 grupos favorables | -0.00082403 |
| Sensibilidad hacia composición2025, solo punto | +0.00038157 |
| Sustituto A1 original2024, G3+RFS1P frente a A1 | -0.00003241 |

Los cinco folds y los dos años son positivos, con un intervalo positivo. Persisten el mínimo global de +0,002 incumplido y la concentración de la ganancia. El sustituto A1 original mejora respecto de añadir solo G3, pero la diferencia total sigue ligeramente negativa. Los pesos2025 se reutilizaron sin clasificador o remuestreo nuevo; su fallo anterior de ESS continúa, así que son sensibilidad y veto, no una evaluación primaria rescatada. El A1 original tampoco sustituye al A1 corregido o al F3c/F2 completo que aún falta reproducir.

La composición es decisiva: 94.259 de 109.296 filas históricas son renovación, frente a 50.083 de 209.063 en2025. El 76,04 % del test es nuevo negocio. La variante que solo cambia renovaciones deja ese bloque mayoritario intacto; no se extrapola su diferencia local de +0,00185 como si fuera una ganancia pública de igual tamaño. Antes de más complejidad se medirá la aportación aislada de FSp en NB con el mismo núcleo, sin ajustar otro parámetro.

Se construyó el prototipo2025 con el F3c medido como padre real. Son 209.063 filas en orden oficial, con los 158.980 precios NB exactamente iguales y 50.083 renovaciones modificadas. Usa la media fija de cinco miembros normalizados, cuyos kappa ya estaban guardados. No se aprendieron pesos de mezcla. El OOF evaluó un estimador por ámbito retenido y no un ensemble anidado de estos cinco miembros; esa diferencia de despliegue queda pendiente. Los totales REN se mantienen antes de redondear y cambian en conjunto solo +0,000074CU tras el redondeo.

El flujo anualiza f por su exposición original, forma una razón sin unidades frente a T2b y mantiene el precio de periodo del padre. El futuro usa q=1 y no multiplica por un cp2025cero. Se hicieron tres inferencias T2b sobre50.083REN, 192filas históricas de control y96de orden, además de15normalizadores sin etiquetas. Los 192controles históricos coinciden exactamente con las tasas guardadas. Pasaron identidad de peso cero, claves/orden, cambios arbitrarios de componentes NB ignorados, rechazo de claves faltantes/duplicadas y tasas negativas, redondeo racional exacto contrastado con Decimal y fórmula escalar independiente en espacio logarítmico.

Aparecieron 199 discrepancias de compatibilidad con el T2b publicado de2025, incluidas diferencias grandes por fila. Se registró antes una prueba de199inferencias: al cambiar únicamente los dos historiales al modo legado, las199reproducen el CSV antiguo dentro de1microCU. Esto explica la diferencia de ventana, sin certificar cuál fue el entorno original ni cambiar el prototipo para forzar coincidencia. El prototipo conserva la ventana explícita que termina en el corte conocido; no interpreta el tramo posterior al corte como observado sin avisos. Las fechas de reporte aportadas llegan al30/12/2024; no se extendió su conocimiento a un día no observado.

El archivo resultante es un prototipo mecánicamente comprobado, no una entrega admitida. Fallan pruebas predictivas y faltan comparador completo y validación del ensemble final. Su creación no autoriza enviarlo cuando cambie la cuota. Se mantienen F3c como entrega vigente y B00, F2/C1 y todas las alternativas. No hubo envíos, nuevos modelos o C0 en esta unidad. Sí se cuentan165momentos de calibración del control prod,30normalizadores del contraste, 30nuevos del sustituto A1 y40reproducidos de G3,15del prototipo, un CSV nuevo y las inferencias descritas.

Se revisó también el enlace número/marca con los quince peligros de la fuente. El ejemplo homogéneo confirma que el producto del proxy con offset de coste y la marca observada puede recuperar el coste esperado; no se declaró inválido FSp. El enlace con offset de número y marca corregida por G_C/G_N permite interpretar sus componentes bajo supuestos condicionales, pero esta revisión sin ajuste no demuestra mejor rendimiento ni justifica rehacer treinta modelos. En autos NB2024 las razones de coste/número son cercanas a uno para la mayor parte de exposiciones; subsidence y algunos peligros de hogar tienen mayor variación. Los supuestos de cola1095, reservas y maestros sin fecha siguen abiertos.

Mejor público procesado: 0,16914; objetivo0,17 aún no conseguido. La cuota consultada continúa en0 y se preserva. 2024 sigue abierto por autorización humana, con evaluación exploratoria adaptativa y sin revisión profesional independiente.

Evidencia principal: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/FSp_REN_G3_prod_contraste_20261026_v1/report.json; vetos: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/FSp_REN_G3_prod_contraste_20261026_v1/additional_veto_points.json; prototipo: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_FSp_REN_prototipo_20261026_v1/report.json; compatibilidad: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/FSp_historia_compatibilidad_20261026_v1/report.json; número/marca: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/enlace_numero_marca_revision_20261026_v1/report.json.

Siguiente unidad: No repetir los60modelos fuente, las matrices, RFS1/RFS1P, el bootstrap REN o la compatibilidad de199filas: ya terminaron. El test2025es76.04%NB y la receta REN no lo cambia; la sensibilidad ponderada de RFS1P es solo+.00038157 y el veto A1 original sigue negativo. Antes de añadir modelos/variables, registrar un único contraste de aplicación FSp a NB con la misma configuración prod, G3, C0 protegido, kappa por ámbito ya guardados y pesos .25/.25/.5. No reestimar nada. Medir la aportación NB separadamente y la receta completa REN+NB como combinación fija, con totales año/ramo/negocio conservados y criterios existentes. La evidencia NB negativa recibida era de otra receta/ámbito y no sustituye este contraste aislado sobre el núcleo reconstruido. Registrar hipótesis, coste y foro antes de puntuar; si también falla, documentar el fallo concreto antes de una calibración estándar adicional. El prototipo ed639b1c conserva158980NB y50083RENcambiadas, está explícitamente no admitido; no enviarlo al recuperar cuota. La revisión número/marca preserva la validez del producto proxy agregado en un riesgo homogéneo y no demuestra superioridad de otro enlace: no rehacer30modelos solo por una diferencia semántica. Para interpretar frecuencia nativa se necesitarían ambos offsets coherentes y nueva prueba. Falta aún F3c/F2 histórico completo y el A1 corregido; no sustituirlo por A1 original ni repetir el inventario exacto sin cambios. 2024abierto como desarrollo, B00/alternativas preservados, mejor público0.16914,cuota0,meta0.17activa.
