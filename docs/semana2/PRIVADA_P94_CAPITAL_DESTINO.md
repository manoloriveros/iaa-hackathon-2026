# P94: capital directo al destino

Codex, 2026-10-27T08:54:58.665287+00:00.

P93 conserva exactamente las 109296 filas, columnas, tipos y valores del archivo agrupado P90. Los cinco selectores internos prefieren64rondas; ampliar a128/256 empeora sus objetivos guardados. No se calculó otro score.

| Fold exterior | Exceso interno128 frente64 | Exceso interno256 frente64 |
|---|---:|---:|
|0|0.4253%|0.9563%|
|1|0.4055%|1.1610%|
|2|0.3918%|1.0609%|
|3|0.3406%|1.3315%|
|4|0.5713%|1.2450%|

El capital ya existe en las fuentes congeladas. El productor real de A1S aplica una división determinista por1000por encima de5M/2M; esa expresión no consulta prima. Su comentario CAP-N1 y el contrato G4 describen otros caminos: G4 sí depende de prima y sus ámbitos de edificios2023no se trasladan aquí. El GLM directo actual excluye el capital por decisión de P56, no por una pérdida accidental de columnas.

La necesidad que se plantea es una respuesta de capital propia del destino, además de la incorporada en las predicciones fuente. No demuestra una mejora. Se conserva el capital oficial positivo dentro de los filtros de incertidumbre F0 (10M edificios,1M contenidos), sin corregir la escala de los casos dudosos. Esos casos se imputarían con mediana de entrenamiento, sin bandera de calidad como predictor. Los límites son filtros históricos, no límites oficiales. La instantánea de pólizas carece de fecha de transacción que certifique la disponibilidad al cotizar.

La próxima opción conserva GLM Tweedie1,5, alpha1, efectos principales, prior y exposición de P88. Motor queda igual. Se reutilizan parámetros solo si coinciden ámbito, claves, datos y código; nunca se prestan a un ámbito interno. Primero se probará el flujo sintético y el enlace estricto por fila. P43/P44 y B13/B14 siguen registrados; esto no es la primera revisión de capital. Cero ajustes, predicciones, remuestreos o envíos. B00 y alternativas preservados.2024abierto adaptativo; conclusiones exploratorias sin validación privada ni revisión profesional independiente.

Próximo: P95: implement strict raw-capital historical join and same P88 standard GLM with one additional capital main effect for buildings/contents, no uncertainty pricing flag. Validate whole synthetic held-poison/replay/offset math and no premium reads; separate full evaluation registration before real fits. Reuse exact same-scope levels/motor, no threshold/alpha/line rescue.
