

## Privada P8, revisión estática previa del contrato fuente, 26 de octubre de 2026

Codex, 2026-10-26T16:08:30.369369+00:00. Se revisaron los textos de los nueve modelos fuente congelados y sus listas de variables, sin cargarlos para inferencia. La suma de índices de partición de sus árboles coincide con la importancia por número de splits guardada en cada archivo. exposure_model está presente y activo en los nueve: 195/170/234 splits en autos, 99/136/74 en edificios y 393/372/333 en contenidos. El capital log_si está presente y activo en edificios y contenidos; no se declara una omisión de capital.

El contrato de entrenamiento usa log(e_cost) como offset de fuente y también permite exposure_model como predictor. La prueba de escalado de calendario de P6 mantuvo constantes las relatividades fuente guardadas. Por tanto, no cubre la ruta que cambia ese predictor dentro del modelo fuente. Esto no demuestra doble conteo, fuga, error o causa de la brecha: la duración puede representar diferencias de riesgo o selección de cartera. Los conteos de splits tampoco miden magnitud o calidad predictiva.

Siguiente unidad: registrar una prueba finita de sensibilidad del predictor de exposición en los nueve modelos congelados. Selección determinista sin respuestas, dos intervenciones fijas de días más cortos, ancla con cachés/centros originales y suma de hojas independiente. Será una intervención parcial de variables fuente; no se presentará como una cotización alternativa o prueba de que todo riesgo anual deba ser constante. Antes de inferir se congelarán código, criterio, configuración, coste y comentario previo. No se decide retirar la variable, reescalar, entrenar otra familia o enviar por esta revisión. La autorización humana automática existente sigue vigente; lo pendiente es concretar y verificar la prueba, no solicitar otra aprobación.

Cero ajustes, modelos cargados para predecir, inferencias, precios, scores o envíos nuevos. P6 y sus límites permanecen; B00/F3c/alternativas intactos y 2024 abierto adaptativo. Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P8_contrato_fuente_estatico_20261026_v1/report.json.
