

## Privada P9: nueve modelos fuente de capacidad fija sin predictor de duración, 26 de octubre de 2026

Codex, 2026-10-26T16:35:31.960014+00:00. Se guardaron los nueve modelos preinscritos, con exposición solo en el offset de coste y sin exposure_model como predictor. Se mantuvieron los demás datos, categorías, parámetros y rondas originales de cada semilla. No hubo búsqueda nueva de capacidad ni parada temprana. La duración sigue ponderando el centro fuente, sin entrar en los árboles.

Las rondas fueron 205/153/190 en autos, 163/201/150 en edificios y 254/239/227 en contenidos. Se verificaron centros por suma escalar independiente, media ponderada unitaria, guardar/cargar, orden de filas y suma de hojas. El replay de cachés de las tres semillas fue exacto sin cargar modelos ni nuevas consultas. Las cachés de aplicación contienen exclusivamente 2023 y 2024. Cero inferencias 2025, C0, calibraciones destino, scores nuevos, precios finales o envíos.

Esta etapa es técnica y no permite retirar la variable del modelo actual. La ablación puede perder señal legítima; además, quitar una columna cambia el mapa del muestreo de variables, por lo que no equivale a intervenir una sola ruta de árboles ya ajustados. Las rondas proceden de la búsqueda fuente anterior con esa variable y el enlace fuente permanece condicionado. La siguiente etapa preinscribirá la comparación completa por grupos y transferencia de año. B00/F3c/P6, fallos y alternativas intactos; 2024 abierto adaptativo. No hay mejora privada demostrada.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P9_fuente_sin_exposicion_20261026/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P9_fuente_sin_exposicion_20261026/replay_report.json.
