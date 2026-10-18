# Envíos a Kaggle: archivos preparados y registro

Carpeta del proyecto para los archivos de envío de la parte 1 y su registro por candidato (D29). Abierta por Claude el 17 de octubre de 2026 (D68) con los dos primeros peldaños de la escalera del plan D67. D70: el participante autorizó expresamente y Codex envió ambos archivos el 17 de octubre. Kaggle los procesó con estado COMPLETE; `registro_envios.json` conserva autorización, fechas, IDs, hashes y puntuaciones públicas.

| Archivo | Qué es |
| --- | --- |
| `preparar_envio_m00.py` | Genera S01 y S02 desde la capa vigente y la corrida vigente de `Bases_actuariales_claude`, con comprobación de hashes, de las 626.639 filas en el orden de `sample_submission` y de predicciones finitas y positivas |
| `archivos/S01_m00_tasa_ramo_T0.csv` | Tasa constante por ramo a nivel T0 por exposición: 544,6976 CU por año expuesto en autos, 417,6652 en edificios y 111,2576 en contenidos |
| `archivos/S02_m00_tasa_ramo_ultimo.csv` | La misma referencia a nivel último (T0 más el IBNR de coste 2021–2024 de D67): 583,3222, 427,1487 y 112,2447 CU |
| `registro_envios.json` | Hipótesis, cambios, versión de código y datos, parámetros, esquema de validación, archivo exacto con SHA-256, puntuación local y espacio para la pública |

## Qué contrasta cada uno

S01 comprueba que la escala local y la pública coinciden: en V24 (tasa con 2021–2023 evaluada sobre el T0 de 2024) puntúa 0,07094, y la referencia pública de coste medio de la captura D64 está en 0,07169. Si el público da algo muy distinto, hay un problema de formato, de métrica o de alineación antes que de modelo.

S02 cambia solo el nivel. Su mejora pública respalda la decisión operativa D70 de calibrar los candidatos siguientes a nivel último; no demuestra cómo se construyó toda la etiqueta privada. El desarrollo se aplica una sola vez, mediante el factor IBNR declarado o la exposición efectiva, según la comparación. Su V24 local (0,07057) es algo menor que el de S01 porque se mide contra el T0 de 2024, que está incompleto: la validación local no puede mostrar esta ganancia, y por eso es la primera pregunta que se lleva al leaderboard.

Ambos archivos tienen cabecera `row_id,prediction`, seis decimales y el orden de la plantilla. SHA-256: S01 `4a7f799810d78727a8551122bda7ff2f20b4cc3ccd0d4abc29699fa2573aecbd`, S02 `cd495bc877b27c5d92c5fbe8b03808579d2b11c2bfff144d254f6ff4f4251546`. La página del concurso menciona CSV; la plantilla descargada es Parquet, y el archivo sigue sus columnas.


## Resultados públicos y decisión D70

| Candidato | ID Kaggle | Estado | D² público |
| --- | --- | --- | ---: |
| S01, nivel T0 | 57320526 | COMPLETE | 0,07118 |
| S02, nivel último | 57320534 | COMPLETE | 0,07211 |

S02 mejora 0,00093. Nivel último fijado para los siguientes modelos de producción de la parte 1, con calibración por ramo y sin doble desarrollo. V23/V24 conservan T0 como etiqueta de evaluación. Quedan tres cupos provisionales hasta las 19:00 Bogotá del 17 de octubre. Recibos: `Preparación/artifacts/verification/s01_s02_scoring_20261017T174306Z/submission_receipt.json`, desde la raíz.
