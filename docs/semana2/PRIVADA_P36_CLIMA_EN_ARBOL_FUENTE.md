# P36: clima anual en el árbol fuente

Codex, 2026-10-26T22:25:29.265520+00:00.

Los tres vetos fuente pasan; se completaron los nueve refits permitidos y se guardaron componentes históricos. Falta comprobar el algoritmo destino completo.

| Ramo | Cambio relativo de desviación fuente | Veto |
|---|---:|---|
| motor | -0.6885% | True |
| buildings | +0.0022% | True |
| contents | -0.2639% | True |

Se agregaron solo siete medidas climáticas oficiales del año, manteniendo capacidad y rondas originales por semilla, costes, exposición y grupos. Todas las semillas entraron en el ensemble geométrico. Pasar admite hasta0,2%de deterioro y no equivale a mejorar. Los precedentes E13/T7/T8y los fallos P33/P34se conservan. No hay ponderación de dominio o nueva curva C0.

Se comprobaron los argumentos reales de entrenamiento contra contaminación de etiquetas, exposición y clima retenidos; los modelos se guardaron antes de validar. Guardado/carga, inversión de orden, suma independiente de hojas y desviación por otro método coincidieron. El cierre reproduce las predicciones guardadas por suma escalar, sin ajustes o inferencias nuevas. La fuente tiene un único holdout ya adaptativo y un enlace de observación con ancestros fuente completos; el clima es condicional y no un pronóstico disponible al cotizar. No se acredita mejora privada o revisión profesional independiente. Esta distinción sigue Gobernanza IAA§2.8y Documentación§3.

Ajustes nuevos: 18; normalizadores fuente: 9. Cero C0, calibraciones/scores destino, inferencias2025o envíos. B00/F3c/alternativas conservados,2024abierto adaptativo. Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P36_fuente_clima_20261026/report.json y Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P36_fuente_clima_20261026/scalar_replay.json.

Próximo: P37: preregister the whole original50/50S2/H1target assay with P36source only changed; keep nestedC0/N3/H1and original qsource/evaluation mapping. Reuse verified source-swap adapter and test only changed bindings, not old fixtures. Preserve all pooled/transfer/cohort/tail/31group gates; no2025inference or CSVbefore acceptance.
