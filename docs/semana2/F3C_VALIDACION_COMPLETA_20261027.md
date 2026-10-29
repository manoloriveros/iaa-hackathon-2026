# F3c completo: reproducción, evaluación temporal y límites para el privado

En mi revisión separo la reconstrucción de la cadena de las conclusiones que permite su evaluación temporal. Conservo la evidencia favorable y la adversa, con los supuestos y las restricciones que condicionan mi decisión.

Codex, 2026-10-28T14:02:32.421530+00:00. Receta registrada antes de nuevos ajustes y evaluador sellado antes de aprender o puntuar en destino. Conservo el CSV F3c ya enviado y todas las alternativas. Esta unidad no produce ni envía otro archivo del concurso.

## Qué se comprobó

El reentrenamiento integral de producción ya existente reproduce los 209.063 precios de F3c con el mismo SHA; se cotejó ese recibo y el archivo, sin volver a entrenar producción. La evaluación temporal nueva conserva ambas familias A1, sin F1 y con F1, cada una con las tres semillas fijas 11/12/13, la neutralización F1 por ramo, T2b con C1, la mezcla 50/50 y las capas F2, formas, niveles y factores propios. No se eligió una semilla o un ramo por el resultado.

Se entrenó la fuente con 2021–2023 y todas las calibraciones nuevas con 2023; se aplicaron precios fijos a 59.202 períodos de 2024. El aprendizaje de niveles usa los grupos/folds guardados. El OOF 2023 es material de entrenamiento, con curva compartida y tronco fuente común; no constituye una validación interna completamente anidada. Se reutilizaron curvas y T2b por sus hashes y controles previos.

## Resultados temporales

Las dos primeras vistas mantienen o retiran el bloque propio dentro de la misma estructura pública histórica. Las otras dos retiran global, formas NB y niveles públicos, y aprenden el nivel final por celda en 2023. Esta segunda vista sigue heredando decisiones históricas de variables e hiperparámetros y la forma A_M1 usada para aprender los factores.

| Población 2024 | F3c estructura pública | Misma estructura sin bloque propio | Nivel final 2023, con bloque | Nivel final 2023, sin bloque |
|---|---:|---:|---:|---:|
| global | 0.126806 | 0.124720 | 0.126727 | 0.124336 |
| new_business | 0.109150 | 0.110030 | 0.108411 | 0.107861 |
| renewal | 0.124586 | 0.122064 | 0.124602 | 0.121934 |
| motor | 0.084739 | 0.082147 | 0.080825 | 0.077559 |
| buildings | 0.070695 | 0.070695 | 0.077493 | 0.077493 |
| contents | 0.100372 | 0.095859 | 0.099034 | 0.094556 |

D² Tweedie 1,5 sobre incurrido neto observado T0. Son resultados locales de 2024 adaptativo; no equivalen al score privado ni permiten predecir su posición.

| Comparación registrada | Δ global | Banda condicional familia 18 | Δ nuevo negocio | Peor piso de estrés | Criterios completos |
|---|---:|---|---:|---:|---|
| public_full_vs_public_noown | +0.002086 | [+0.000209, +0.004045] | -0.000880 | -0.001409 | False |
| trainlevel_full_vs_trainlevel_noown | +0.002391 | [+0.000404, +0.004511] | +0.000550 | +0.000000 | False |
| public_full_vs_trainlevel_full | +0.000079 | [-0.006178, +0.006066] | +0.000738 | -0.007989 | False |

Las bandas usan los mismos 10.000 sorteos por 36.408 componentes cliente/dirección. Familia 18 cubre los contrastes declarados en esta secuencia, no toda la búsqueda adaptativa histórica. Los cinco cortes guardados de 2024 son particiones de un único período temporal, no cinco entrenamientos temporales independientes.

El remuestreo mantiene fijos los modelos y parámetros aprendidos. Por tanto, estas bandas no incluyen toda la incertidumbre de reentrenar los árboles, estimar C0 o elegir variables y formas; tampoco convierten 2024 adaptativo en una confirmación independiente.

Fallos public_full_vs_public_noown: global_family18_lower_above_margin, NB_nonnegative_and_lower95_floor, broad_and_sixcell_floor, top_favorable_group_removal_nonnegative, 50_fixed_price_stress_broad_floor. La diferencia tras retirar los 37 grupos más favorables es -0.000115.

Fallos trainlevel_full_vs_trainlevel_noown: global_family18_lower_above_margin, NB_nonnegative_and_lower95_floor. La diferencia tras retirar los 37 grupos más favorables es +0.000024.

Fallos public_full_vs_trainlevel_full: global_family18_lower_above_margin, NB_nonnegative_and_lower95_floor, broad_and_sixcell_floor, four_savedfolds_positive, top_favorable_group_removal_nonnegative, 50_fixed_price_stress_broad_floor. La diferencia tras retirar los 37 grupos más favorables es -0.006529.

La cola permanece completa: los 41 períodos del 1% superior entre los positivos concentran 21.23% de T0. No se eliminaron ni limitaron sus importes. Los 50 escenarios son sensibilidades de etiquetas con precios fijos; no aportan probabilidades ni demuestran suficiencia de reservas o IBNR.

## Diferencias necesarias y límites

El CSV 2025 exacto y este análogo temporal no son el mismo archivo ni el mismo horizonte de aprendizaje. Producción aprendió con 2023/2024 y fuente hasta 2024; para evaluar 2024 se corta todo aprendizaje nuevo antes de ese año. Las razones locales de F2, formas y factores se aprenden solo en la vista T2b OOF 2023, en lugar del promedio histórico de vistas 2023/2024. El contraste conserva arquitectura y configuración; no certifica retrospectivamente el archivo entregado como un holdout limpio.

El borrador inicial confundía tasas anuales con primas del período. Se corrigió por cotejo del código original antes de cualquier aprendizaje o score destino, mediante una enmienda previa en el foro y un nuevo sello, preservando código y sello iniciales. La neutralización F1 conserva el total de primas con exposición redondeada; la mezcla promedia primas del período. Factores y formas se aplican sobre primas últimas, con q=1, y solo después se usa q de T2b para contrastar incurrido. Las razones y factores se aprenden con la vista observada 2023 del legado. A1 conserva exposición redondeada a cuatro decimales para sus offsets; T2b usa exposición calendario. El cambio no afecta los modelos fuente ni selecciona el puente por score.

El cotejo de claves detectó también antes del ajuste destino que los nombres de NB_shapes ya contienen el sufijo de celda; duplicarlo habría omitido esas formas. Se corrigió y se comprobó que cada forma actúa en su celda, con rechazo de claves inválidas. El control positivo pasó de escala uniforme a una alteración parcial fija de 2023, para que la invariancia de escala no lo volviera ininformativo. Conservo estas correcciones y sus sellos; no son variantes seleccionadas por score.

El cotejo de valores base coincidió en todas las 109.296 filas destino 2023/24 y una muestra sistemática de 5.000 filas 2023 por ramo de la fuente (numéricas con tolerancia absoluta 1e-12 y categorías exactas). Los antecedentes F1 detectaron otro fallo real del adaptador: había excluido 36 reportes emergentes y 409 desarrollados aceptados sin fila de exposición asignada. El original sí los conserva como historia si el reporte precede a la póliza. Se preservó el fallo y se corrigió ese pool antes de puntuar. No se asignaron esos costos a T0 ni se cambió C0. La nueva comprobación usa todas las filas fuente 2021–2023 y destino 2023/24, con búsqueda temporal independiente; la duración desde primera póliza se conserva.

Los multiplicadores globales, por celda y las formas NB proceden de resultados públicos históricos. Aunque se fijen antes de esta evaluación, siguen condicionados por esa historia. Los antecedentes F1 respetan reporte anterior al inicio, pero la aceptación se observa en el corte posterior disponible. Los maestros no tienen todas las versiones temporales y T0 es una valoración posterior. No se reconstruye con ello la información que realmente habría existido al cotizar.

La receta histórica también depende del lote cotizado: normaliza F1 por ramo y factores/formas por celda dentro de la cartera de aplicación. En la comprobación del bloque posterior, aplicar a la mitad de filas cambia la predicción relativa máxima en public_full 0.16%, public_noown 0.16%, trainlevel_full 0.11%, trainlevel_noown 0.07%. Esa comprobación mantiene fijo el tronco; no cuantifica además toda la dependencia de neutralización F1. La consistencia punto a punto exige una decisión futura explícita, no un cambio silencioso de esta receta.

Seleccionar un subconjunto de un CSV fijo no cambia sus precios. La prueba de lote examina portabilidad y sensibilidad de cartera; no demuestra que el scoring privado vuelva a normalizar las filas. Los normalizadores usan entradas y predicciones, sin etiquetas retenidas, por lo que su dependencia de cartera tampoco constituye por sí sola fuga de etiquetas.

## Decisión y siguiente paso

F3c sigue siendo la referencia enviada y conservada; R1 y NB-CRED300 conservan su condición de alternativas. No se cambia la selección manual de Kaggle, no se promueve una receta por esta evaluación adaptativa y no se gasta otro envío. Antes de sustituir el archivo hacen falta una mejora que soporte los pisos por negocio y ramo, control de concentración, evaluación de la sensibilidad de reservas/tiempos y una producción que corresponda exactamente a la receta admitida. Los resultados adversos no se corrigen escogiendo después otro K, subconjunto o mezcla.

## Evidencia y coste

La familia admitida reúne 30 ajustes nativos A1 primarios y 30 replays con costos 2024 alterados. El costo total de esta unidad es 80 intentos nativos: incluye además 18 ajustes F1 del pool incorrecto conservados y excluidos, un ajuste interno N0 interrumpido antes de guardar checkpoint y 1 interrupciones adicionales documentadas. De los 60 útiles, 12 N0 ya terminados se reutilizaron y se completaron 48 después de corregir F1; las reanudaciones repiten únicamente etapas sin resultado guardado. Otros 12 ajustes históricos N0/semilla11 se reutilizan por argumentos, modelo y raw idénticos sin contarlos como nuevos. Cuatro ajustes sintéticos quedan separados. No hay ajustes T2b ni curvas C0 nuevos. Se registran 141 invocaciones analíticas primarias (kopt y balance), con replays adversos, control positivo y ejemplos sintéticos separados; las cantidades derivadas de credibilidad no son modelos nativos independientes.

Los controles verifican la igualdad de argumentos, modelo, iteraciones y raw bajo alteración real de 2024; el flujo completo destino vuelve a aprender desde el cargador alterado y da los mismos parámetros/precios. Cambiar el entrenamiento sí cambia el resultado. Hay replay exacto sin ajuste desde parámetros guardados, matemáticas escalares por otra implementación, métrica sklearn y 20 sorteos contrastados directamente. Esto es verificación propia de IA, sin aprobación humana inventada ni revisión profesional independiente.

El control preventivo de memoria detuvo una etapa antes del ajuste completo; se guardó el fallo y se retomó desde la selección de iteraciones existente. Los ajustes terminados de la misma receta no se repiten y los 80 intentos totales se concilian con sus recibos, incluidas las interrupciones registradas.

- Hackaton/Repositorio_IAA2026/registro/semana2_F3c_completo_validacion_plan.json; SHA 60c14fc6565a9018ec5e764d3d229b955b15e420459a43f553d94b7fac6dce87
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/evaluator_sealed.json; SHA 76b209bf0ae5d9dd9b9531663eaf4f54b3b2a5819a7c8456cd1215573a311591
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/evaluator_amendment1.json; SHA 76245d5ffdb3b38794ddfaa163567aa3253bd305c599ed0d60265d803aa3a325
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/evaluator_control_amendment.json; SHA 03499574db5f199994a5cad960195f04361c11a5ea59184ce85298eacdc16e58
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/evaluator_implementation_correction.json; SHA 8e4cf17f73adcacf72fbde414bf11a094515cadb0bf4a56f3c2dc9f4915dfcbf
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/source_history_admission.json; SHA f7be332803646cac525d08da0889cd5a7b209639aee84fde8091358c3fdd5f43
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/F1_pool_diagnosis.json; SHA eaf5f0091c8ae3e8ad93609937b712a14ce808dc97bbee7cd487086168ea461c
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/F1_history_value_parity.json; SHA 9a7c29f69daea223037876e04eb8cedc5d9d1f8b35d8b4f84ba6060c1aba1acb
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/original_history_preflight.json; SHA ff05c2e96124b9d0c801734b83898da1e3c427bc6dc68697dfa7aed584f0c4e8
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/feature_value_parity_corrected_metadata.json; SHA 4f7695e9c0233fc93d58d388e5966764517679e6ffada1461f51913cd3b4c5ce
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/evaluator_synthetic_amendment1.json; SHA 8854deaa24d3b559f218be28bd6433d05cb498031c6c0ebb6fc394a9e3711d56
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/bridge_verifier.json; SHA b12846121d0c0cd8bd2e51f3390523562c13b965268f1f4e5c5e170b7155f226
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/bridge_and_keys_verifier.json; SHA 18c19b856cd5b2c66b20e17da9c67fed764242bb2d32424572210cd91ae8fd91
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/original18_source_schemas.json; SHA 6950a3da483c900c6167774744c72ec4e4fb810b0068f83fca7797f141b8ada3
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/parameters.json; SHA cf1d033aa3200c66d60b6cd145fe662d5ceda031c8b62557b030f2068f3f86e0
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/target_controls.json; SHA 1b35deb0c3db87645887f51b4f20ffecb13e313e412f37cd843d112746cdd246
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/results.json; SHA 73a1eff91d99b61b8d778f56bd33e86e902161ce331ce0242a1c260d023fa1c1
- Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/F3c_validacion_completa_20261027/verification.json; SHA 900c866292e49b8d8bf44149294635d0f2acae3a1f0e7e8269228e473c1fdb35
