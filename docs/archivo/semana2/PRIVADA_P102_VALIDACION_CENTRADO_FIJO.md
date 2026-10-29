# P102: centrado fijo, resultado completo

Codex, 2026-10-27T09:54:37.016315+00:00. El combinado falla; no admite un CSV nuevo.

Diferencia D² frente a referencia local: +0.0000519; IC95 por grupos [-0.0001520, +0.0002876]. Post31: -0.0002795; peor celda: -0.0032856. Diferencia puntual frente a P65 con normalización por lote: -0.0000006, sin nuevo intervalo pareado.

Se reutilizaron todos los componentes y factores G de sus mismos ámbitos. Solo se calcularon cuarenta centros de entrenamiento por negocio y cuarenta adversos, guardados antes de controles, con exclusión de todo el payload retenido. Modelos primarios/adversos coinciden. La invariancia de factores bajo el nuevo centrado se apoya en la identidad de nuisance por celda y en la cadena alternativa sintética completa, sin inventar nuevos ajustes reales de factores. Edificios sigue exactamente igual a P65.

Pasaron quince replays completos exactos con cálculo de centros/estimación/normalización por lote bloqueados. Cotizaciones individuales, por negocio y permutadas coincidieron dentro de tolerancia3e-13 sobre datos históricos reales; no se produjeron precios2025. Intervalos y primeras ponderaciones se cotejaron sin nuevo remuestreo en replay. Desconocidos conservan factor bruto1 antes del centro fijo; su efecto final no tiene que ser identidad.

Guardas globales: {"pooled_delta_ge002": false, "pooled_lower95_positive": false, "pooled_atleast4positive_folds": false, "both_pooled_years_nonnegative": true, "pooled_post31_nonnegative": false, "all_nominal_and_stress_cell_floors": false}. Cohortes: {"cohort_nominal_points_above_floor": true, "cohort_nominal_lower95_above_floor": false, "cohort_family16_lower_above_floor": false, "cohort_all_stress_points_above_floor": true, "pooled_nominal_family16_lower_positive": false}.

La cotización por fila es una propiedad del algoritmo, no prueba de mejora privada. Fuente2024 condicional, snapshots sin fecha de cotización, reporte/cola/reservas y búsqueda adaptativa siguen limitando la interpretación. Sensibilidades con últimos nominales fijos, sin ajuste completo por escenario. Cero ajustes nativos/factores/fuente/CDF, inferencias2025 o envíos. B00 y todas las alternativas conservadas,2024abierto adaptativo; sin revisión profesional independiente.

Próximo: Review only saved P102center values and all whole cells against P65/P100, without refit/resampling. Projective quoting alone does not solve predictive transport. Preserve all factors/lines/adverses and do not retune centering scope or weights. Next mechanism needs new documented source risk or observation/valuation evidence, not another normalization to public totals.
