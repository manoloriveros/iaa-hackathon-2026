# P45: mezcla fija entre referencia y GLM

Codex, 2026-10-26T23:38:11.829853+00:00. La mezcla no supera las guardas conjuntas y no se adopta ni se envía.

Se combinan por media geométrica los costes completos de la referencia y el GLM P15. Los pesos son fijos e iguales sobre log-coste; no hay ajustes, niveles o normalizadores nuevos. La media de cinco cocientes H1/G3 y el adaptador común se conservan. La propuesta aritmética futura de P44 se corrigió por la convexidad de la pérdida respecto al log-coste antes de calcular o puntuar esta mezcla. Esa cota limita la pérdida frente al promedio de ambos padres; no garantiza mejora frente a la referencia.

| Nominal | Δ D² frente a referencia | IC95 por grupos | Post31 | Peor celda |
|---|---:|---|---:|---:|
| POOLED | +0.0009063 | [-0.0003954; +0.0022463] | -0.0012542 | -0.0048186 |
| TRANSFER | +0.0004098 | [-0.0007307; +0.0017075] | -0.0016203 | -0.0070117 |

Guardas globales: {"pooled_delta_ge002": false, "pooled_lower95_positive": false, "pooled_atleast4positive_folds": false, "both_pooled_years_nonnegative": true, "pooled_post31_nonnegative": false, "conditional_transfer_nonnegative": true, "all_nominal_and_stress_cell_floors": false}. Guardas NB/broker/historia cero: {"cohort_nominal_points_above_floor": false, "cohort_nominal_lower95_above_floor": false, "cohort_family16_lower_above_floor": false, "cohort_all_stress_points_above_floor": false, "pooled_nominal_family16_lower_positive": false}. Se guardan todos los folds, años, ramos, escenarios y sensibilidades de nivel, incluidos los adversos. No se probaron pesos alternativos o una mezcla aritmética tras conocer el resultado.

Se cotejaron treinta ámbitos y sus padres/adversos por hash. El nuevo flujo consume únicamente precios guardados; ajustes e inferencia fuente bloqueados. La composición en coste último y observado concuerda, con controles de claves, precios inválidos y etiquetas alteradas; replay por raíces escalares, métrica por sumas independientes y cuatro multiplicidades de remuestreo guardadas, sin ajustes o remuestreo nuevos. Los replays de aprendizaje de padres se reutilizan por bytes idénticos, no se presentan como repetidos hoy. Cero ajustes fuente/destino/C0, constantes nuevas, inferencias2025 y envíos.

2024 es desarrollo abierto y adaptativo. La transferencia es condicional a fuente desarrollada que incluye2024; no prueba prospectiva. Persisten maestros sin fecha, soporte escaso en algunas cohortes y reservas/cola no identificadas. No hay demostración de mejora privada ni revisión profesional independiente. B00, F3c y todas las alternativas se conservan.

Próximo: P46: inspect the complete target observation/response contract and the already saved P13allocated-loss cells alongside group support, before selecting another model. All standard source-family changes and this fixed mixture failed current whole-algorithm robustness. Isolate whether one material observation/exposure or validation-target uncertainty can be resolved with existing legitimate evidence, or document a concrete standard target-level hypothesis with protected prospective comparison. Do not repeat prior audits on unchanged inputs, search mixture weights or add source capacity to chase public/private proxies. Preserve failed P45 and no automatic upload.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P45_mezcla_fija_20261026/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P45_mezcla_fija_20261026/replay_report.json.
