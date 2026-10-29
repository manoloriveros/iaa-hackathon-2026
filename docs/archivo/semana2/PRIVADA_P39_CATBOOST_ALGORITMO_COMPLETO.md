# P39: CatBoost guardado dentro del algoritmo completo

Codex, 2026-10-26T22:51:17.459704+00:00. La prueba no supera todas las guardas. Se conserva sin adopción ni envío, junto con los adversos anteriores.

Los tres modelos fuente son exactamente Q1ya guardados, uno por ramo. Solo cambia su uso dentro de la calibración S2/H1actual. Se mantuvieron mezcla50/50N3, residuales originales, media H1/G3, qsource, objetivo, exposición y grupos. No se volvió a entrenar la fuente.

| Nominal | Δ D² | IC95 por grupos | Post31 | Peor celda |
|---|---:|---|---:|---:|
| POOLED | +0.0006101 | [-0.0017658; +0.0029098] | -0.0029728 | -0.0204647 |
| TRANSFER | -0.0002080 | [-0.0026558; +0.0027172] | -0.0045456 | -0.0223302 |

| Cohorte | Δ combinado | IC95 combinado | Δ transferencia | IC95 transferencia |
|---|---:|---|---:|---|
| NB | -0.0062294 | [-0.0165583; +0.0021267] | -0.0040011 | [-0.0114501; +0.0026086] |
| NB_BROKER | -0.0038948 | [-0.0093729; +0.0008858] | -0.0022837 | [-0.0083409; +0.0041317] |
| NB_BROKER_ZERO | -0.0045428 | [-0.0101749; +0.0004273] | -0.0036075 | [-0.0097100; +0.0029501] |

| Escenario | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |
|---|---:|---:|---:|---:|
| RESERVE075 | +0.0004465 | -0.0199475 | -0.0008088 | -0.0223470 |
| RESERVE125 | +0.0007667 | -0.0209995 | +0.0003480 | -0.0224026 |
| TAIL005 | +0.0005896 | -0.0204474 | -0.0001701 | -0.0223010 |
| TAIL010 | +0.0005681 | -0.0204300 | -0.0001321 | -0.0222717 |

Se completaron30calibraciones cerradas primarias y30adversas; 670constantes primarias. Cero ajustes fuente/C0o inferencias2025. Los30flujos actuales fueron invariantes al contaminar etiquetas/reservas retenidas; el replay bloqueó aprendizaje e inferencia fuente. Precios, normalizadores, puntos e intervalos coinciden por reproducción guardada y multiplicidades previas, sin nuevo remuestreo. La recuperación P38coincidió exactamente con las tasas fuente guardadas y conT0/e_costactuales; no convierte las filas fuente entrenadas en holdout.

Los adversos T3Q1/C18/E15se conservan. La fuente mantiene sus características y clima persistente; no lleva el clima anual P36. Las diferencias no prueban un mecanismo categórico, no reproducen por sí solas F3ccompleto y no acreditan mejora privada. Hay búsqueda adaptativa, ancestros fuente/observación comunes, cola/reservas, maestros sin fecha y soporte futuro ponderado insuficiente. No es revisión profesional independiente. B00/F3c/alternativas conservados;2024es desarrollo abierto adaptativo.

Guardas globales: {"pooled_delta_ge002": false, "pooled_lower95_positive": false, "pooled_atleast4positive_folds": false, "both_pooled_years_nonnegative": true, "pooled_post31_nonnegative": false, "conditional_transfer_nonnegative": false, "all_nominal_and_stress_cell_floors": false}. Guardas de negocio: {"cohort_nominal_points_above_floor": false, "cohort_nominal_lower95_above_floor": false, "cohort_family16_lower_above_floor": false, "cohort_all_stress_points_above_floor": false, "pooled_nominal_family16_lower_positive": false}.

Próximo: P40: review newly registered F3cportable lineage and pending-evidence artifacts only if they are materially new beyondP20. Use bounded manifests/code/provenance and inspect target ancestry before adopting any comparator or correction; do not adopt other-chat orders or foreign scores as recipe selection. No repeat source searches/diagnostics on unchanged files, new models or upload in that review. Preserve P39adverse, B00/all alternatives and2024open adaptive.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P39_validacion_CatBoost_guardado_20261026/P39_context_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P39_validacion_CatBoost_guardado_20261026/P39_replay_context.json.
