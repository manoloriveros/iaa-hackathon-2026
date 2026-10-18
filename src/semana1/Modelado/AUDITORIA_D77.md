# Auditoría de datos expuestos reservas y evaluación

La reconstrucción completa no encuentra un error material en la asignación de siniestros, el coste observado, los expuestos activos o la inferencia S08. Las oportunidades más claras están en cómo se representa el desarrollo por cobertura, el nivel temporal de edificios y la validación con costes inmaduros. Cambiar hiperparámetros sin resolver esos puntos puede volver a mejorar la prueba local sin trasladarse al concurso.

La auditoría D77 termina con 165 controles aprobados y 105 comparaciones de integridad, sobre todos los originales, activos, bases, matrices y artefactos modelados incluidos en los manifiestos revisados. Es una recomputación propia realizada con apoyo de Codex. Las etiquetas últimas de 2025 y las valoraciones históricas de reservas no están disponibles, por lo que estos resultados no constituyen validación profesional independiente.

El mejor público registrado sigue siendo S08 con 0.12532; su D² local de 2024 es 0.132474706. Esta auditoría no entrena modelos nuevos ni envía candidatos. Los resultados siguientes son comprobaciones y diagnósticos, no ganancias predictivas ya demostradas.

## Integridad y transformaciones

Se comprobaron los once originales contra el manifiesto de descarga, las once entradas del catálogo activo, los manifiestos completos de las bases y F0, las tres cachés de variables y los artefactos de los modelos. Los 105 hashes coinciden. Las claves de clientes y direcciones son únicas y los cruces de pólizas no tienen huérfanos. El clima es único por dirección y año, con 2.879.915 observaciones de 2021 a 2025. Las 626.639 filas de test coinciden exactamente con sample_submission.

Las diferencias originales frente a activos están contadas por campo en [raw_active_changes.csv](C:/dev/Hakaton/Preparación/artifacts/verification/audit_D77/raw_active_changes.csv): canonicalización de customer_id en autos, exposición, edades y capitales autorizados, y armonización de construction_type. Los valores originales de los siniestros retenidos siguen iguales. Se eliminaron 604 duplicados, cada uno con gemelo en todos los campos originales salvo claim_id. Las marcas de auditoría permanecen fuera de los predictores.

F0 aplica una sola vez las 1.454 escalas adicionales de capital: 691 en edificios y 763 en contenidos, de las cuales 190 están en test. Hay 1.305 con confirmación y 149 sin confirmación histórica; 123 de estas últimas están en test. El capital original se conserva y esas marcas no entran al modelo. Las excepciones no justifican una corrección masiva adicional.

## Asignación de siniestros y objetivo observado

De 163.150 siniestros originales quedan 162.546 activos. Se volvió a unir cada uno por policy_id, ramo e intervalo inclusivo de ocurrencia, sin importar la función del constructor. Los 162,133 siniestros distintos de PRE00 tienen una asignación única, sin ambigüedades. Los 413 de prehistoria permanecen fuera de las etiquetas y pueden contribuir a la historia de reportes conocida.

Hay 160.432 siniestros aceptados asignados. Los rechazados quedan fuera de T0. La suma reconstruida es 741,156,868.43 CU, con reserva de caso de 90,168,216.94 CU. Se reproducen por fila T0, aceptados, positivos, abiertos, pagado, incurrido, recuperaciones y reserva; también cada coste y conteo por peligro. Los conteos usados en frecuencia-severidad cuentan siniestros positivos, por lo que no mezclan costes positivos con conteos cero. Las etiquetas de test son nulas.

La identidad comprobada es T0 = incurrido − recuperaciones = pagado + reserva de caso − recuperaciones. El pagado ya es neto de franquicia según el diccionario oficial; deducirla otra vez reduciría erróneamente el coste. Las reservas son no negativas y los cerrados no tienen reserva residual. T0 incluye la estimación actual de abiertos, de modo que añadir toda la reserva otra vez también duplicaría importes.

## Expuestos y calendario

Se verificó fila por fila exposure = round((period_end − period_start + 1) / 365, 4), además de una partición diaria independiente en los 60 meses de 2021 a 2025. Coinciden todos los expuestos mensuales y los denominadores por cobertura de autos. No hay intervalos superpuestos de una misma póliza.

| Partición | Filas | Expuestos activos | Días exactos divididos por 365 | Expuestos originales |
| --- | --- | --- | --- | --- |
| Entrenamiento | 2,409,311 | 1,968,577.0591 | 1,968,576.9890 | 2,658,636.1771 |
| Test | 626,639 | 500,351.2820 | 500,351.2548 | 500,351.2820 |

La diferencia de redondeo acumulada es 0,0701 años en entrenamiento y 0,0272 en test. Las correcciones EXP01 evitan una diferencia mucho mayor de escala en las exposiciones originales de entrenamiento. La convención ACT/365 se mantiene como decisión documentada basada en el test; no se presenta como una confirmación explícita del organizador. Los intervalos observados tienen de 1 a 365 días, incluso en 2024. La fórmula admite 366 días si aparecieran y no debe recortarse automáticamente a uno.

El denominador elegible cambia por peligro. Cristales exige cobertura comprensiva; robo excluye responsabilidad civil sola. Los cuadros [eligible_exposure.csv](C:/dev/Hakaton/Preparación/artifacts/verification/audit_D77/eligible_exposure.csv) separan denominador general, elegible y excepciones. No debe interpretarse una frecuencia baja calculada sobre todas las pólizas como frecuencia de la cobertura.

## Coberturas con excepciones

| line | peril | cover | positive_claims | cost |
| --- | --- | --- | --- | --- |
| motor | own_damage | third_party_fire_theft | 3 | 2,463.78 |
| motor | own_damage | third_party_only | 1 | 2,494.92 |
| buildings | accidental_damage | False | 502 | 629,283.30 |
| contents | accidental_damage | False | 1087 | 918,548.62 |

Los cuatro daños propios fuera de cobertura comprensiva suman 4.958,70 CU. En hogar, los 502 positivos de edificios y 1.087 de contenidos con accidental_damage_cover falso suman 1.547.831,92 CU. Los modelos FS desactivan el cero duro cuando encuentran positivos fuera de la máscara, preservando los costes. El origen contractual de esas excepciones sigue sin resolverse. No cambiar a cero sus predicciones por una regla simplificada.

## Desarrollo de reporte por cobertura

El offset agregado de autos mezcla peligros con pesos comunes a todo el ramo. La participación estimada de lesiones en el coste desarrollado de entrenamiento 2021–2023 es 36,65 % en cobertura comprensiva, 54,55 % en terceros incendio y robo, y 73,53 % en responsabilidad civil sola. Como lesiones tarda más en reportarse, esas mezclas requieren completitudes diferentes.

| cover | rows_valid | old_completion | cover_completion | ratio_total |
| --- | --- | --- | --- | --- |
| comprehensive | 207,455.00000 | 0.79122 | 0.81487 | 1.02988 |
| third_party_fire_theft | 23,699.00000 | 0.79093 | 0.73872 | 0.93400 |
| third_party_only | 23,544.00000 | 0.79058 | 0.66321 | 0.83890 |

Los pesos de este contraste se calculan solo con entrenamiento hasta 2023 y se aplican a 2024. El offset común supera al específico de responsabilidad civil sola en aproximadamente 19,2 % respecto al específico; la razón específico/común es 0,8389. La diferencia no se corrige necesariamente con un factor final por ramo. Es la primera comparación de modelos que priorizaría, manteniendo algoritmo y parámetros para aislar su efecto.

La diferencia de offsets no demuestra una desviación de predicción de igual magnitud. En S08, los cocientes observado/predicho de 2024 son 0,9597 en comprensiva, 0,8360 en terceros incendio y robo y 0,9963 en responsabilidad civil sola. El learner puede compensar parte del offset con sus variables. Multiplicar directamente predicciones guardadas por las razones de completitud no sustituye volver a entrenar con el offset coherente.

## Granularidad diaria y fecha de valoración

La aproximación mensual trata igual distintas fechas de ocurrencia del mismo mes. Un cálculo diario con estimador de producto límite inverso para retrasos truncados muestra diferencias concentradas en períodos cortos y comienzos tardíos. Para los períodos que comienzan en diciembre de 2024:

| line | rows | monthly_completion | daily_count_completion | daily_count_at_Dec31 | daily_cost_at_Dec31 |
| --- | --- | --- | --- | --- | --- |
| motor | 4,659.00000 | 0.38145 | 0.29425 | 0.31993 | 0.31794 |
| buildings | 2,808.00000 | 0.59814 | 0.48414 | 0.52440 | 0.51873 |
| contents | 3,145.00000 | 0.70205 | 0.57440 | 0.62126 | 0.62350 |

Las columnas diarias distinguen el 30 y el 31 de diciembre. El contrato oficial valora al 31 de diciembre; que el último reporte observado sea el día 30 no demuestra que la valoración sea el 30. El corte diario futuro debe partir del 31 y conservar la sensibilidad al 30. El contraste diario supone estabilidad de retrasos y fija completitud uno más allá del mayor retraso observado; una cola no observada continúa sin identificarse. El control con datos completamente maduros reproduce exactamente la CDF empírica ponderada.

La sustitución del estimador y la granularidad diaria cambian a la vez en este diagnóstico. La similitud agregada del conteo mensual y diario, junto con la diferencia en diciembre, apunta a un efecto de calendario, pero la ganancia del modelo necesita una comparación controlada. No se alteraron los expuestos nominales de los datos.

## IBNR de notificaciones y coste

Los quince triángulos mensuales y sus colas se reprodujeron con una construcción independiente. También coincide el IBNR publicado a su precisión: notificaciones faltantes × probabilidad de coste positivo × severidad seleccionada. En 2024, los factores de coste son 1,28768 en autos, 1,07958 en edificios y 1,03171 en contenidos. Un incremento de conteos de autos de aproximadamente 7,44 % produce un incremento de coste de 28,77 %, porque los faltantes se concentran en lesiones. Usar el factor de conteos sobre todo el coste sería incorrecto.

La severidad de lesiones usada para el IBNR ya distingue reportes tardíos: 25.773,73 CU frente a 21.806,90 CU de todos los positivos maduros, con 582 reportes a más de 365 días. En hundimiento usa 18.691,06 CU frente a 22.548,76 CU, basándose en solo 31 tardíos. Esa selección reduce su IBNR de unos 4,00 a 3,32 millones de CU. Es un supuesto de severidad relevante y poco estable en hundimiento; conviene aplicar credibilidad y sensibilidad al umbral, sin afirmar que faltaba por completo un tratamiento de severidad tardía.

Las curvas diarias ponderadas por coste también difieren de las de conteo. En lesiones de 2024, el contraste entrenado hasta 2023 estima completitud de conteos 0,5647 y de coste 0,5450 al día 30. Es compatible con severidad mayor entre reportes tardíos. El coste de abiertos sigue siendo una estimación actual, de modo que esta ponderación no resuelve el desarrollo futuro de sus reservas.

En las reconstrucciones a 2022 y 2023 se censuran los reportes después de cada corte antes de estimar los triángulos. Los peligros cortos suelen acercarse al conteo posteriormente observado. Lesiones proyecta aproximadamente 10 % más que lo observado al cierre de 2024 en ambas cohortes; todavía puede haber reportes futuros, por lo que esa diferencia no demuestra por sí sola sobreestimación. La tabla completa está en reporting_backtests.csv. El ejercicio prueba conteos, no costes históricos: no existen las valoraciones pasadas de incurrido ni de estado necesarias para reconstruirlos honestamente.

## Reservas de caso e IBNER

Las reservas de caso de 2024 son 26,52 millones de CU en autos, 18,93 en edificios y 2,48 en contenidos, equivalentes a 29,25 %, 28,11 % y 14,14 % del respectivo T0. La incertidumbre sobre el coste futuro de siniestros reportados, IBNER, queda fuera de una curva de notificaciones.

Un escenario de ±25 % sobre la reserva de caso, manteniendo fijo el IBNR de notificaciones, mueve el total T0 + IBNR de autos ±5,68 %, edificios ±6,51 % y contenidos ±3,43 %. Es sensibilidad, no intervalo de confianza ni una recomendación de aumentar reservas. Puede cambiar qué modelo parece mejor con un proxy de último.

## Frecuencia severidad y nivel temporal

Los componentes FS de hogar se entrenan con exposición nominal. En el conjunto 2021–2024, el contraste de exposiciones estima completitud 0,9080 para hundimiento, frente a aproximadamente 0,988–0,995 en los demás peligros de edificios. Un balance final por ramo restaura el total, pero no restaura la composición de peligros ni sus relatividades individuales. Conviene comparar frecuencia con exposición desarrollada por peligro, conservando la severidad positiva y todos los costes en evaluación.

El anclaje de todos los componentes al total S02 también neutraliza cambios de nivel que el modelo hubiera aprendido. La corrección OOF de S08 modifica ese anclaje, aunque sigue referida al histórico. El contraste más claro aparece en edificios:

| line | ultimate_rate_D67 | S08_2025_rate | S08_over_cohort_rate |
| --- | --- | --- | --- |
| motor | 584.37637 | 603.55413 | 1.03282 |
| buildings | 485.02599 | 442.78877 | 0.91292 |
| contents | 120.50319 | 119.60511 | 0.99255 |

Son CU por año expuesto. En edificios, S08 queda 8,71 % por debajo de la estimación última de la cohorte 2024. Escalar esa cohorte solo por el cambio del capital medio llevaría a 499,60 CU para 2025. Una extrapolación loglineal ingenua de cuatro cohortes daría 515,44 CU. Ninguna es una tarifa validada: mezclan inflación, cartera, clima, reservas y supuestos de IBNR. Sirven para detectar que un anclaje histórico rígido puede limitar el nivel. La siguiente prueba debe aprender tendencia por ramo y peligro en validación rodante y no elegir un multiplicador mirando el leaderboard.

## Variables historia y disponibilidad

Se reconstruyen por separado todos los conteos F1, la recencia de última notificación, los conteos por peligro y la exposición previa. Coinciden con los reportes conocidos antes del 1 de enero del año de la póliza, incluyendo rechazados y prehistoria cuando corresponde. El clima prev1 coincide con el año anterior y mprev con la media de años estrictamente anteriores. La prima anualizada y el logaritmo de prima relativa coinciden con sus fórmulas sin usar etiquetas. Los predictores efectivos de S08 excluyen identificadores, año, etiquetas, contactos, renovación, flags y offsets como variables explicativas.

La historia se corta al inicio del año, no en la fecha individual de cotización. El diagnóstico cuantifica los casos en que una notificación incluida es posterior a la cotización pero anterior al inicio. Esto requiere una restricción adicional si se adopta una interpretación estricta a fecha de cotización; no es un incumplimiento automático del contrato vigente al inicio. Los recuentos están en quote_time_sensitivity.csv.

Hay 5.800 filas históricas y de test con al menos un reporte incluido en F1 que resulta posterior a la fecha individual de cotización; 1.366 corresponden a 2025. Además, la media anual usada para relativizar primas se calcula con la cartera suministrada del propio año, sin etiquetas. Es una normalización transductiva de cartera que debe distinguirse de una media conocida antes de cotizar cada póliza.

Los archivos incluyen clima anual de 2025. El diccionario describe medidas efectivas del año, sin identificarlas como pronósticos. Excluirlas es coherente con tarificación al inicio; predecir un escenario anual condicionado a información suministrada sería otra tarea. Esta decisión puede limitar señal del concurso, pero incorporar ese clima exige declarar y comprobar la interpretación del reto. No se admitió silenciosamente como disponible en el pasado.

Los maestros de clientes y direcciones carecen de instantáneas históricas. La estabilidad de atributos físicos y la disponibilidad de campos sin fecha siguen siendo supuestos. La revisión D76 de tres campos de incorporación no les dio peso efectivo en S08. Las anomalías físicas retenidas se detallan en physical_exceptions.csv y la escala y evolución de capitales en capital_profiles.csv.

## Deriva y dependencia entre entidades

Se compararon todos los predictores efectivos entre 2024 y 2025: faltantes, medias, percentil 99, desplazamiento estandarizado, categorías nuevas y variación de proporciones. feature_drift.csv conserva los resultados por columna. feature_profiles.csv muestra historia disponible, falta de clima anterior, prima anual y experiencia previa por año. Los faltantes de clima en 2021 son estructurales por falta de 2020; no se rellenaron con clima futuro.

No aparecen categorías nuevas entre 2024 y 2025 en los predictores revisados. La mayor variación categórica es make_model de autos, con distancia de variación total 0,00935. Los mayores desplazamientos numéricos están en la historia: recencia de última notificación entre 0,36 y 0,41 desviaciones estándar, y exposición previa alrededor de 0,34. La exposición acumulada máxima de entrenamiento es tres años y llega a cuatro en test; 46,65 % de autos, 46,70 % de edificios y 46,62 % de contenidos superan el máximo de entrenamiento. Los árboles no extrapolan libremente esa relación. Priorizar ventanas de historia de 365 y 730 días daría definiciones más comparables entre folds y 2025, con tasas suavizadas y sin usar reportes futuros. Su efecto predictivo sigue pendiente.

Los diagnósticos físicos reproducen 3.717 edades implícitas de licencia inferiores a 16 y 161.822 filas con NCB mayor que años de licencia. No hay edades negativas de vehículo, capitales no positivos ni años de construcción posteriores al período en las matrices revisadas. Los nulos de cilindrada de 2.533 eléctricos siguen preservados. Estas excepciones requieren una comparación controlada de tratamiento; no se recortaron arbitrariamente.

entity_overlap.csv distingue clientes, pólizas y direcciones vistos en años previos, además del solapamiento entre calibración y selección de 2023. Repetir una póliza entre años refleja renovaciones y no equivale a usar su coste futuro como predictor. Compartir dirección entre clientes puede producir dependencia residual; las medias de clima y la historia de dirección están cortadas temporalmente, pero una partición por cliente no garantiza independencia espacial.

Alrededor del 84,8 % de las filas de test corresponde a una póliza vista antes, proporción muy similar a 2024. No hay clientes ni pólizas compartidos entre calibración y selección de 2023; sí hay 2.936 direcciones compartidas. Por tanto, el problema principal detectado en historia es la expansión de su ventana acumulada, más que un cambio brusco de cartera nueva frente a renovada.

## Evaluación y pérdidas grandes

La fórmula local de Tweedie D² con potencia 1,5 coincide con [scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.d2_tweedie_score.html), sin pesos de exposición adicionales en el scoring. El código íntegro del scorer oficial no está publicado en la evidencia disponible. El entrenamiento sí usa los offsets o pesos que corresponden a cada objetivo.

V22 entrena con 2021 y evalúa 2022; V23 con 2021–2022 y evalúa 2023; V24 con 2021–2023 y evalúa 2024. El combinador S08 se ajustó sobre todo el OOF de 2023: su score de 2023 es ajuste del combinador. La receta se congeló antes de los CatBoost correspondientes a V24, pero 2024 ya había sido consultado en otras decisiones y sigue siendo desarrollo reutilizado.

| stratum | rows | A_over_P | D2_S08 | D2_S07 | optimal_beta_in_sample |
| --- | --- | --- | --- | --- | --- |
| all | 626190 | 0.997948 | 0.132475 | 0.131729 | 0.998862 |
| line=buildings | 184001 | 1.065107 | 0.113429 | 0.112844 | 1.039847 |
| line=contents | 187491 | 1.002186 | 0.088417 | 0.087279 | 1.025247 |
| line=motor | 254698 | 0.952551 | 0.084441 | 0.083659 | 0.961516 |

El beta óptimo de esa tabla es un diagnóstico que usa el resultado del propio segmento. No debe trasladarse a producción como si fuera validación. validation_strata.csv añade duración, mes, negocio nuevo, póliza conocida, historia previa y cobertura.

El balance global observado/predicho de 0,99795 esconde diferencias: edificios tiene 1,06511 y autos 0,95255. En períodos de 1–30 días hay 24.244 filas, solo 72 con coste positivo y cociente 2,60036; el D² baja de 0,216353 en S07 a 0,202339 en S08. La escasez de positivos obliga a revisar los mayores siniestros antes de calibrar ese grupo. No es evidencia suficiente para multiplicar todas sus predicciones por 2,6.

| largest_fraction | rows | cost_share | D2_gain_from_group | D2_remaining_S08 | D2_remaining_S07 |
| --- | --- | --- | --- | --- | --- |
| 0.000100 | 63 | 0.076904 | 0.000321 | 0.126726 | 0.126282 |
| 0.001000 | 627 | 0.262698 | 0.001833 | 0.097233 | 0.098520 |
| 0.010000 | 6262 | 0.673006 | 0.007058 | -0.068555 | -0.057348 |
| 0.050000 | 31310 | 0.997085 | 0.011450 | -7.507007 | -7.327119 |

Al excluir el 0,1 % más costoso, S08 da 0,097233 y S07 0,098520. Por tanto, la mejora global S08 depende de pérdidas grandes y empeora en el resto bajo esa sensibilidad. Los costes extremos deben seguir en la métrica principal. El bootstrap condicional por dirección, con 400 repeticiones, da intervalo aproximado de la diferencia [0.0000096; 0.0013550]. No cubre la búsqueda de modelos ni la dependencia de eventos regionales; un intervalo estrecho no elimina el sesgo de selección.

## Reproducción de S08 y defecto heredado

Se cargaron los modelos guardados y se recalcularon los dos nativos LightGBM, los componentes frecuencia-severidad de hogar y los tres CatBoost de producción. Después se reprodujeron las normalizaciones a S02, los pesos del combinador y el beta estadístico una sola vez. La exposición se multiplica una vez por canal; el IBNR no se aplica otra vez tras el balance último.

Las 626.639 predicciones coinciden con el CSV enviado a seis decimales. La máxima diferencia antes de redondeo es 0.0000005000 CU. Coinciden orden, claves, positividad, suma y SHA-256 f6c11e366fa3663fed7187c9c45db30f5542155e864bdfef25857277b33363e6.

Se confirmó un defecto menor en el constructor F0 antiguo: solo carga factores de edades 0–46 y deja completitud 1 en edad 47, omitiendo la cola para lesiones y hundimiento. Su efecto aproximado sobre exposición efectiva agregada de coste es 8,07 años en autos y 3,04 en edificios, frente a 787.157,56 y 590.560,20 años nominales de entrenamiento. D75 inicializa esa edad con la cola y S08 usa sus offsets, por lo que este defecto no explica su score. Se registra para corregirlo en una nueva versión del constructor, sin reescribir F0 ni repetir entrenamientos históricos.

## Próximas comparaciones

1. Mantener S08 como referencia y comparar autos con mezcla de desarrollo por cobertura, con el mismo learner. Hacer después frecuencia-severidad con desarrollo por peligro y severidad con credibilidad. Separar ambos cambios para atribuir sus efectos.
2. Comparar granularidad diaria con mensual a corte oficial del 31 de diciembre, congelando curvas solo con entrenamiento. Revisar diciembre y períodos de hasta 30 días, además de la métrica completa.
3. Aprender nivel y tendencia de edificios en OOF temporal por ramo y peligro, contrastando promedio histórico, años recientes y capital. Mantener el objetivo último y evitar duplicar desarrollo. Evaluar tanto riesgo relativo como nivel; un único score de T0 no identifica último.
4. Comparar ventanas de historia de 365 y 730 días con la historia acumulada actual. La versión acumulada pone aproximadamente el 46,6 % del test fuera del rango de exposición histórica de entrenamiento.
5. Evaluar FS de hogar con frecuencia desarrollada por peligro, manteniendo excepciones de cobertura. Medir si la corrección afecta la distribución además de la suma del ramo.
6. Antes de otra búsqueda amplia, fijar comparaciones rodantes y criterios de estabilidad frente a pérdidas grandes, segmentos y reservas. Mantener V24 etiquetado como desarrollo reutilizado y documentar cada consulta.

El orden responde a los mecanismos y magnitudes medidos; todavía no demuestra qué alternativa superará 0,13 público. No se gastaron envíos durante esta revisión.

## Evidencia y reproducción

Los scripts y las tablas están en Preparación/artifacts/verification/audit_D77. all_checks.csv contiene cada control; findings.json clasifica hallazgos y prioridades. Los JSON por área conservan resultados y supuestos, y las tablas CSV detallan excepciones, denominadores, desarrollo, niveles, deriva y segmentos.

Desde C:/dev/Hakaton, con el entorno Windows existente, correr en orden: data_audit.py; inference_audit.py; development_audit.py; features_validation_audit.py; actuarial_gaps.py; exposure_calendar_audit.py; level_diagnostic.py; history_support_audit.py; additional_feature_checks.py; build_report.py. Usar Preparación/.venv/Scripts/python.exe y la ruta de evidencia como prefijo de cada script. El auditor importa PyArrow desde la caché registrada y no instala paquetes, entrena ni escribe en los datos de origen. start_audit.py es la apertura histórica de esta revisión y no se debe repetir.

El tratamiento de triángulos se contrasta con la documentación de [chainladder](https://chainladder-python.readthedocs.io/stable/user_guide/development.html). El estimador inverso para retrasos truncados se contrasta con la sección 2.2 del trabajo de [Korn en Variance](https://variancejournal.org/article/115769-a-comprehensive-non-aggregated-stochastic-approach-to-loss-development) y la documentación de [DTDA](https://search.r-project.org/CRAN/refmans/DTDA/html/shen.html). La ponderación por coste es una extensión diagnóstica propia con los límites de valoración indicados. La trazabilidad y los límites de validación siguen las secciones de documentación 2–6, gobernanza 2.8 y consideraciones profesionales 3.1 y 3.5–3.6 de las referencias IAA adoptadas por el proyecto.
