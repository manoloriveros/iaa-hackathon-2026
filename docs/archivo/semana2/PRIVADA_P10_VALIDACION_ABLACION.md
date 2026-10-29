

## Privada P10: la retirada de duración no acredita mejora robusta, 26 de octubre de 2026

Codex, 2026-10-26T16:42:14.873628+00:00. Se comparó el algoritmo completo S2/H1 con los nueve modelos fuente sin predictor de duración frente al mismo algoritmo original. Los 30 ámbitos de integración reprodujeron exactamente los precios últimos originales antes de cambiar la fuente. Se reutilizaron C0, N3 y los cinco cocientes H1/G3 por su independencia de A1S; se aprendieron solo las calibraciones S2 afectadas, bajo los grupos y la exposición originales.

| Comparación nominal | Δ D² | IC95 por grupos | Después de 31 grupos | Peor celda |
|---|---:|---|---:|---:|
| POOLED | 0.0001311 | [-0.0005309, 0.0009386] | -0.0008096 | -0.0039066 |
| TRANSFER | 0.0005714 | [-0.0003549, 0.0018785] | -0.0008469 | -0.0033421 |

La comparación combinada pierde en 2023 (contribución −0,0002290), mejora en 2024 (+0,0003601) y solo dos de los cinco folds aportan ganancia. Los intervalos incluyen cero y las mejoras quedan por debajo del mínimo incremental 0,002 fijado antes de probar. En autos nuevos2023 el deterioro de celda es −0,0039066; en edificios nuevos2024, −0,0028924. La transferencia de destino2023a2024 también depende de pocos grupos y empeora edificios nuevos en −0,0033421. No se seleccionan ramas o mezclas a partir de estas celdas.

| Escenario fijado | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |
|---|---:|---:|---:|---:|
| RESERVE075 | 0.0001089 | -0.0040769 | 0.0004987 | -0.0034369 |
| RESERVE125 | 0.0001524 | -0.0037475 | 0.0006391 | -0.0032717 |
| TAIL005 | 0.0001297 | -0.0039561 | 0.0005756 | -0.0033412 |
| TAIL010 | 0.0001282 | -0.0040079 | 0.0005799 | -0.0033402 |

Las cuatro sensibilidades conservan precios y cambian solo objetivo de valoración/enlace de observación común según el contrato anterior; no son recalibraciones completas de D0 en cada rama. Sus intervalos también incluyen cero y no resuelven los pisos por celda. Los intervalos simultáneos de la familia de diez contrastes, los cocientes A/E y sensibilidades de nivel comunes quedan guardados. Los pesos2025 se usaron solo para puntos descriptivos porque su ESS sigue siendo insuficiente. No se reestimaron para favorecer esta alternativa.

Treinta llamadas de aprendizaje cerrado primarias produjeron 670 constantes de precio; separadamente se hicieron treinta controles con todos los T0 y reservas retenidos alterados. Artefactos y precios últimos fueron exactamente iguales. El momento del nivel se verificó por sumas escalares independientes. Un proceso de replay recuperó los treinta flujos exactos con aprendizaje e inferencia fuente bloqueados. Cero C0, modelos fuente, inferencias2025, precios finales o envíos nuevos en esta etapa. Los nueve modelos fuente se cuentan en P9.

El fixture inicial acoplaba año y negocio y dejó celdas vacías: hubo una llamada sintética incompleta, sin ajuste con datos del concurso. Se conserva el intento y el fallo. Se corrigió solo el año sintético y pasaron seis llamadas sintéticas completas. Los replays originales anteriores al fallo no tenían recibo durable; la comprobación de integración se repitió para guardar evidencia verificable, sin repetir estimaciones o puntuar otra receta.

Decisión: no adoptar D0 ni quitar exposure_model del modelo actual. Dependencia de una variable no implica que retirarla ayude. Se mantiene la referencia y la alternativa fallida con sus costes y adversos. Antes de otra familia se cotejarán los GLM fuente ya hechos y la diferencia real de ámbito respecto a un GLM de efectos principales sobre los cuatro años actuales; no se repetirá la receta histórica2023 con otro nombre.

La fuente contiene2024y las marcas finales son comunes, así que la transferencia no es una validación prospectiva completa. Ambos años destino son adaptativos. No se reprodujo el F3c histórico completo y no se afirma ganancia frente a su envío ni mejora privada. B00/F3c/P6y todas las alternativas permanecen; 2024abierto por autorización humana vigente.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P10_validacion_sin_exposicion_20261026/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P10_validacion_sin_exposicion_20261026/replay_report.json.
