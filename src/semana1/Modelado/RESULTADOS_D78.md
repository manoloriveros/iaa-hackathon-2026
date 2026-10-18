# Comparación de desarrollo por cobertura historia y calibración

Se implementaron las tres mejoras prioritarias y se entrenaron 20 corridas en dos cortes temporales: 16 modelos nativos LightGBM y cuatro conjuntos de frecuencia-severidad, con 56 estimadores en total. La evidencia no justifica gastar otro envío. El único cambio retenido por la selección de 2023 es una calibración adicional de edificios; su mejora de 2024 es pequeña e incierta. S08 sigue siendo la referencia operativa y su mejor público registrado permanece en 0.12532.

## Resultado temporal completo

| line | S08 | D78 | delta |
| --- | --- | --- | --- |
| all | 0.13247471 | 0.13253477 | 0.00006006 |
| buildings | 0.11342890 | 0.11359876 | 0.00016986 |
| contents | 0.08841663 | 0.08841663 | 0.00000000 |
| motor | 0.08444106 | 0.08444106 | 0.00000000 |

Las 626.190 observaciones de 2024 se evalúan con todos los costes, incluidos los extremos, usando Tweedie D² de potencia 1,5 verificado con scikit-learn. La diferencia global es 0.00006006. El intervalo condicional aproximado por cliente, con 300 repeticiones, es [-0.00005980; 0.00019066]. Incluye cero y no cubre la selección de modelos ni eventos regionales.

Sin el 0,1 % más costoso, el D² de S08 es 0.09723330 y el candidato da 0.09614381. Esta sensibilidad empeora, aunque la métrica principal sube. No se transforma esta pequeña mejora local en una expectativa de superar 0,13 público.

## Implementación de los cambios

El módulo Preparación/src/iaa_lab/priority.py incorpora el desarrollo por cobertura. Para cada split, calcula por cobertura los pesos de coste por peligro como coste de entrenamiento dividido por exposición efectiva de entrenamiento y normaliza esos pesos. Reutiliza únicamente las curvas D75 estimadas sobre los años de entrenamiento y verificadas por hash. Las categorías nuevas reciben el perfil agregado de entrenamiento. En 2025 se conserva exposición nominal porque el objetivo es último. Las excepciones históricas de cobertura se preservan; no se imponen ceros nuevos.

Las ventanas cuentan notificaciones con report_date en el intervalo exacto [1 de enero menos 365 o 730 días, 1 de enero), sin filtrar por estado final ni usar importes. La exposición histórica se reconstruye mediante intersección diaria de los períodos con el mismo intervalo. Las tasas tienen un mínimo de 0,25 años en el denominador. La recencia queda limitada a 730 días y una marca distingue ausencia de historia conocida. En hogar se añaden conteos de la dirección y del otro ramo dentro de las mismas ventanas.

Se compararon dos tratamientos de historia. rolling sustituye los conteos acumulados y las variables de recencia/exposición por las ventanas. history_plus conserva los conteos acumulados útiles, añade las ventanas y limita exposición histórica antigua a dos años, sustituyendo la recencia sin límite. Una tercera comparación lleva las ventanas al modelo FS de hogar, manteniendo su familia y parámetros. Los metadatos de disponibilidad están en contract_D78.json; no se modificó el contrato F0 histórico.

La calibración de edificios usa el factor multiplicativo óptimo de desviación Tweedie sobre clientes de calibración de 2023, separado de los clientes usados para seleccionar. Se acerca el factor a uno con credibilidad 50 %. El valor retenido es 1.024079916411, equivalente a aproximadamente +2.4080 %. Se comparó con conservar el nivel anterior. Este factor residual se aplica una sola vez sobre S08, que ya conserva nivel último; no se vuelve a multiplicar por exposición o IBNR.

## Comparaciones pareadas

La tabla muestra cambios de D² respecto al mismo learner anterior, después de igualar el total predicho para separar relatividades y nivel. Las filas FS se comparan con el FS previo. En las tablas exploratorias iniciales de r3, FS aparecía junto a la referencia nativa; matched_family_ablations.csv es la comparación causal por familia corregida y debe usarse para ese propósito. Esa corrección de presentación no cambia predicciones, selección ni pesos.

| line | variant | family | V23 | V24 |
| --- | --- | --- | --- | --- |
| buildings | fs_history | FS | 0.00039368 | -0.00054449 |
| buildings | history_plus | native | -0.00098651 | 0.00000308 |
| buildings | rolling | native | -0.00124974 | -0.00014151 |
| contents | fs_history | FS | -0.00080380 | 0.00085553 |
| contents | history_plus | native | 0.00244734 | -0.00022649 |
| contents | rolling | native | -0.00090547 | 0.00008640 |
| motor | coverage | native | -0.00026298 | -0.00078581 |
| motor | coverage_rolling | native | -0.00003139 | -0.00203724 |
| motor | history_plus | native | -0.00031898 | -0.00085911 |
| motor | rolling | native | -0.00061629 | -0.00130030 |

El desarrollo por cobertura de autos empeora en ambos cortes bajo este learner. La sustitución completa por ventanas pierde señal de 2023 en los tres ramos; en2024 algunas alternativas de contenidos mejoran, pero no de manera consistente entre años ni por encima de S08 en la selección fijada. La ampliación history_plus mejora el nativo de contenidos en 2023, pero no mantiene esa mejora en2024. En consecuencia, ninguno de los nuevos modelos de relatividades recibe peso en el candidato final. Una diferencia grande de completitud en la auditoría no garantizaba que el learner actual no la compensara con otras variables.

## Diseño y límites de la evaluación

Se mantuvieron los parámetros D75 de LightGBM para aislar cambios de offset y variables: semilla 2026, hojas 7, learning_rate 0,025 y 400/600 rondas base según ramo, con el incremento preexistente para2024. En autos se limita el coste de ajuste a 15.000 CU, se restituye el exceso agregado y se puntúa siempre el coste completo. Los FS conservan 250 árboles Poisson y 200 Gamma por peligro, con cuatro hilos por ajuste.

V23 entrena con 2021–2022 y evalúa 2023; V24 entrena con 2021–2023 y evalúa 2024. Los pesos de mezcla se buscan en 0/25/50/75/100 % usando selección 2023. Los parámetros y la receta nativa r2 se fijaron antes de entrenar sus modelos 2024. La extensión FS se decidió a partir de 2023 antes de consultar la comparación nueva de 2024; su receta r3 se fijó antes de sus ajustes FS 2024. Se guardaron las recetas anteriores y las versiones de código.

S08 ya ajustó su combinador histórico con todo el OOF 2023. Por ello, su comparación de 2023 no es validación nueva, aunque los modelos base sean temporales y la calibración D78 use solo la mitad correspondiente. También 2024 fue consultado en rondas anteriores. Esta es evaluación propia sobre desarrollo reutilizado, sin independencia profesional ni etiquetas últimas 2025. Los targets de entrenamiento son T0 a la valoración común de diciembre 2024; no se reconstruyen reservas históricas que no existen.

La revisión de adopción es conservadora: una estimación puntual positiva no basta cuando la incertidumbre incluye cero y empeora la sensibilidad a pérdidas grandes. El flag exploratorio inicial que solo comprobaba signo positivo queda conservado en confirmation_V24_r3_initial_point_estimate.json; la confirmación y la decisión finales lo sustituyen por no adoptar ni enviar. Esta revisión no cambia los modelos ni el resultado medido.

## Candidato local y decisión

Se guardó un CSV experimental de 626.639 filas en [D78_calibracion_edificios_NO_ENVIADO.csv](<C:/dev/Hakaton/Preparación/artifacts/verification/improvement_D78/D78_calibracion_edificios_NO_ENVIADO.csv>). Usa el S08 de precisión completa y el factor de edificios fijado en 2023. No se vuelve a ajustar el factor con 2024 y no hace falta entrenar nuevos modelos de producción porque todos los pesos de los challengers fueron cero. El total de edificios pasa de 66,526,315.85 a 68,128,263.98 CU y la tasa anual equivalente queda en 453.45109 CU. Los otros ramos conservan sus predicciones.

El candidato está disponible para inspección y no tiene score público. SHA-256 792fe104f951f8d1b1522cd4e32cc5a0b1537b75eb7f1e4ea6fdfb2cd24204e4. Su existencia no lo convierte en reemplazo de S08. No se gastaron envíos, no hubo entrenamiento remoto, publicaciones, mensajes, automatizaciones ni delegación. El registro de envíos permanece idéntico al inicio de la ronda.

La siguiente hipótesis con fundamento sería separar desarrollo y severidad por peligro y revisar el calendario diario, manteniendo cortes de entrenamiento y comparación pareada. Esta ronda no la presenta como implementada ni como una mejora ya probada. Los tres cambios solicitados sí quedaron implementados, entrenados y comparados.

## Verificación y reproducción

Cinco pruebas funcionales cubren los extremos temporales de las ventanas y el año bisiesto, la invariancia frente a reportes futuros, los pesos de desarrollo calculados solo en entrenamiento, la condición óptima de calibración con ceros y pérdidas grandes, y el reemplazo explícito de variables acumuladas. Se leyeron completas las tres matrices y se recalcularon independientemente 360 filas de historia. Se recargaron los 20 modelos y se reprodujeron 2.000 filas de predicción y sus componentes, verificando sus hashes y el CSV final.

La evidencia está en Preparación/artifacts/verification/improvement_D78. plan.json, revision2.json y revision3.json conservan el alcance de cada comparación; recipe_V23_r3.json contiene la decisión congelada; metrics_V24_r3.csv y matched_family_ablations.csv contienen los resultados. model_verification.json conserva la reproducción, candidate_audit.json los controles del CSV y decision_D78.json la decisión de no enviar. Las fuentes y el entorno quedan en D78_source.zip y environment.json.

Se usa Preparación/.venv/Scripts/python.exe en Windows, con PyArrow de la caché y cuatro hilos por learner. run.py prepara y ajusta variantes por línea y split; train_fs.py cubre los FS; compare.py reproduce selección y comprobación; verify_and_prepare.py verifica artefactos y crea el candidato. Los scripts impiden sobrescribir modelos o un CSV ya creado. Una nueva reproducción requiere una carpeta de corrida nueva dentro de la misma estructura. No se modificaron originales, activos, F0, D75, D76 ni S08.
