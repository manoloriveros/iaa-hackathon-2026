# P37: clima en el algoritmo completo

Codex, 2026-10-26T22:31:58.400021+00:00. La prueba no supera todas las guardas de robustez. Se conservan los modelos y resultados; no hay adopción o nuevo envío.

Solo cambió la fuente A1S por los árboles de P36con siete campos climáticos anuales. Se mantuvieron mezcla50/50N3, residuales, media H1/G3y qsource. La comparación conserva objetivo, exposición, grupos y todos los criterios anteriores.

| Esquema | Δ D² | IC95 por grupos | Post31 | Peor celda |
|---|---:|---|---:|---:|
| POOLED | -0.0001443 | [-0.0008423; +0.0005331] | -0.0010850 | -0.0048348 |
| TRANSFER | -0.0004306 | [-0.0009983; +0.0001688] | -0.0012232 | -0.0041153 |

| Cohorte | Δ combinado | Δ transferencia |
|---|---:|---:|
| NB | -0.0006024 | -0.0006182 |
| NB_BROKER | +0.0003428 | +0.0004103 |
| NB_BROKER_ZERO | -0.0002769 | -0.0006472 |

| Esquema | Fuera del rango wildfire fuente | Grupos con coste positivo | Δ nominal | IC95 |
|---|---|---:|---:|---|
| POOLED | False | 5558 | -0.0005153 | [-0.0029208; +0.0011720] |
| POOLED | True | 1570 | +0.0010513 | [-0.0024301; +0.0046698] |
| TRANSFER | False | 3230 | -0.0006736 | [-0.0024414; +0.0003591] |
| TRANSFER | True | 748 | +0.0005635 | [-0.0021465; +0.0066719] |

El soporte climático se definió por los extremos empíricos de la fuente completa antes del ajuste destino. Las celdas pequeñas por ramo/año/negocio siguen visibles en el reporte. Las bandas adicionales de familia20se conservaron junto con las guardas previas de familia16, sin relajarlas. Que una fila esté dentro del rango marginal no acredita soporte multivariante, igualdad del mecanismo entre mercados o un pronóstico válido para2025. Aproximadamente23%de las covariables2025había excedido el rango wildfire de entrenamiento interno; el límite se registró antes de entrenar.

| Escenario | Δ combinado | Δ transferencia |
|---|---:|---:|
| RESERVE075 | -0.0001486 | -0.0003692 |
| RESERVE125 | -0.0001400 | -0.0004878 |
| TAIL005 | -0.0001451 | -0.0004369 |
| TAIL010 | -0.0001459 | -0.0004433 |

Se completaron30calibraciones cerradas primarias y30adversas; 670constantes primarias nuevas. Los18ajustes fuente P36no se cuentan otra vez. Se reutilizaron C0/N3/H1y el adaptador ya comprobado. Las nuevas membresías y el bloque métrico de rango se verificaron antes de ajustar. Los30flujos fueron invariantes al contaminar etiquetas y reservas retenidas; replay con aprendizaje e inferencia fuente bloqueados, precios y normalizadores exactos. Los puntos, intervalos y primeras multiplicidades de los contrastes de negocio y rango se reprodujeron sin remuestrear.

Los grupos de bootstrap son componentes cliente/dirección. Las colas de las bandas20tienen resolución limitada con2000réplicas; no se refinó el remuestreo para cambiar la conclusión. Se mantienen ancestros fuente/observación comunes, clima retrospectivo, reserva/cola, maestros sin fecha y búsqueda adaptativa de2023/2024. La revisión propia no es validación profesional independiente ni evidencia observada de la privada. B00/F3c y todas las alternativas permanecen.2024está abierto como desarrollo adaptativo. Cero ajustes fuente/C0, inferencias2025, CSVfinales o envíos nuevos en P37.

Guardas globales: {"pooled_delta_ge002": false, "pooled_lower95_positive": false, "pooled_atleast4positive_folds": false, "both_pooled_years_nonnegative": false, "pooled_post31_nonnegative": false, "conditional_transfer_nonnegative": false, "all_nominal_and_stress_cell_floors": false}. Guardas de negocio: {"cohort_nominal_points_above_floor": true, "cohort_nominal_lower95_above_floor": false, "cohort_family16_lower_above_floor": false, "cohort_all_stress_points_above_floor": true, "pooled_nominal_family16_lower_positive": false}. Guardas de rango: {"range_positive_group_support_min100": true, "range_nominal_point_floor": true, "range_nominal_lower95_floor": false, "range_family20_lower_floor": false, "range_all_stress_points_floor": true, "pooled_nominal_stricter_family20_lower_positive": false, "NB_stricter_family20_lower_floor": false}.

Próximo trabajo: P38: use saved P37evidence to distinguish climate range limitations from source category handling without refitting or repeating P13/P32. First inspect existing source CatBoost recipes and current complete-model inputs; only prepare a materially distinct standard source alternative if current evidence documents a failure it can address. Preserve all gates and failed weather/weight recipes; no favorable-line rescue, ad-hoc climate extrapolation, new weights or publicscore tuning. No2025inference or upload from a failed P37.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P37_validacion_clima_20261026/P37_context_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P37_validacion_clima_20261026/range_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P37_validacion_clima_20261026/P37_replay_context.json.
