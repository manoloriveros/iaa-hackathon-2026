# P30: el GLM por peril no mejora la robustez en destino

Codex, 2026-10-26T21:13:54.957862+00:00. La receta completa conserva50/50N3, residuales S2y media H1/G3; solo cambia la fuente a la suma fija de GLM por peril. Que la fuente superara su referencia no fue suficiente para el transporte. Se conserva el resultado sin adopción ni envío.

| Nominal | Δ D² | IC95 por grupos | Post31 | Peor celda |
|---|---:|---|---:|---:|
| POOLED | +0.0003941 | [-0.0018510; +0.0027495] | -0.0035435 | -0.0138538 |
| TRANSFER | -0.0008506 | [-0.0031765; +0.0013607] | -0.0047927 | -0.0173233 |

El combinado gana poco y su intervalo incluye cero. La transferencia pierde; en ambos casos la retirada de los31grupos más favorables deja pérdidas. Solo el criterio de ambos años combinados no negativos pasa entre las guardas globales. No se alcanza la mejora mínima, estabilidad de folds o pisos de celdas.

| Cohorte nominal | Δ combinado | IC95 combinado | Δ transferencia | IC95 transferencia |
|---|---:|---|---:|---|
| NB | +0.0010262 | [-0.0090823; +0.0145778] | -0.0026636 | [-0.0074579; +0.0021907] |
| NB_BROKER | -0.0090340 | [-0.0145079; -0.0038403] | -0.0042988 | [-0.0093335; +0.0005614] |
| NB_BROKER_ZERO | -0.0089514 | [-0.0146723; -0.0034719] | -0.0042841 | [-0.0094934; +0.0006448] |

El punto de negocio nuevo combinado es positivo pero muy incierto. Broker nuevo pierde alrededor de0,009D²y su intervalo marginal combinado es negativo, también con historia cero. La transferencia de las tres cohortes pierde. Todas las guardas adicionales incumplen algún criterio; no se rescata una parte favorable o una semilla.

| Escenario | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |
|---|---:|---:|---:|---:|
| RESERVE075 | +0.0003451 | -0.0157907 | -0.0012176 | -0.0197377 |
| RESERVE125 | +0.0004397 | -0.0122047 | -0.0005108 | -0.0152662 |
| TAIL005 | +0.0004271 | -0.0138041 | -0.0008253 | -0.0172568 |
| TAIL010 | +0.0004610 | -0.0137541 | -0.0007997 | -0.0171899 |

Se completaron30calibraciones cerradas primarias y30controles adversos. Constantes primarias nuevas: 670. Los60ajustes fuente de P28/P29y sus constantes no se cuentan otra vez; C0/N3/H1se reutilizan. Los30flujos nuevos no cambiaron al alterar etiquetas y reservas retenidas. El replay bloqueó aprendizaje e inferencia fuente y verificó precios, normalizadores, multiplicidades guardadas e intervalos sin remuestrear. Las fuentes/modelos y la receta se congelaron antes de puntuar, en commit2a5b6c9d.

La evaluación usa el puente y qSourcefijados; el nuevo backbone suma perils, pero no introdujo un C0por riesgo nuevo en destino. Eso merece una revisión de compatibilidad antes de otra prueba; estos resultados no demuestran que el puente sea erróneo o que explique la pérdida. No se cambiará una observación u objetivo después del resultado para hacer pasar la receta. Se revisarán los HETya existentes sin repetirlos. Una hipótesis distinta necesitará sus propios objetivo, comparador, configuración, coste y foro previos.

Todo es exploratorio tras búsqueda adaptativa. Fuente2024, ancestros comunes de observación, cola y reservas, maestros sin fecha y soporte ponderado2025insuficiente conservan sus límites. No es una reproducción exacta de F3cni una revisión profesional independiente. B00/F3c y todas las alternativas se conservan,2024abierto adaptativo. Cero ajustes fuente/C0, inferencias2025, precios finales o envíos nuevos en P30.

Próximo trabajo: P31: review the compatibility of the frozen observation-to-ultimate bridge with the new peril source package using existing HET/P0/P1/P2/P26/P30metadata and code, without fitting or scoring. Distinguish an intentionally model-independent evaluation contract from a trainable/risk-dependent observation link. Inspect existing HETsource/outermix hypotheses and ancestry first; do not repeat their finished diagnostics or assume a new mechanism. Identify whether per-peril historical rates were persisted and whether a legitimate source/outer-held-free link exists for any proposed future adapter. Do not reconstruct missing peril weights from aggregate rates, modify the target/bridge posthoc to rescue P30, or claim reporting caused its failure. Any genuinely new observation contract would require separately frozen objective/comparator/configuration/cost and forum before new predictions or scores. No source inference, C0,2025prices or uploads in the review. Keep B00/F3c/all failures,2024open/adaptive.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P30_validacion_frecuencia_marca_20261026/P30_context_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P30_validacion_frecuencia_marca_20261026/cohort_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P30_validacion_frecuencia_marca_20261026/P30_replay_context.json.
