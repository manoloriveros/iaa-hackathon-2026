# P110: evaluación del Poisson de frecuencia y nivel de coste

Codex, 2026-10-27T14:03:51.545804+00:00. El combinado falla las guardas; no se admite un CSV y la transferencia permanece sin evaluar.

Frente al algoritmo histórico S2/H1: delta D2=-0.0076049; IC95 por grupos=[-0.0134427, -0.0018166]; Post31=-0.0143807; peor celda=-0.0908053. No es una réplica histórica exacta del CSV F3c enviado.

Frente al null emparejado sin corrección de forma: delta=-0.0005521; IC95=[-0.0055215, +0.0039283]. Ambos conservan fuente, mezcla por peril, exposición y nivel de coste propio. La comparación de recuentos por celdas está en matched_null_report.json. Son contrastes exploratorios, sin forecast de score privado.

Quince Poisson primarios y quince adversos reales, con 45 constantes primarias y 45 adversas separadas. La forma aprende de recuentos aceptados con exposición de número; el nivel conserva T0 como objetivo final de coste. Todos los modelos completos coincidieron después de alterar el contenido retenido antes de seleccionar entrenamiento. Los quince replays reprodujeron precios con aprendizaje de Poisson, niveles, preprocesamiento y CDF bloqueado; también coincidieron los 75 enlaces nominales y de estrés. La suma por otro método comprobó gradiente y los tres niveles de cada ámbito.

Guardas globales: {"pooled_delta_ge002": false, "pooled_lower95_positive": false, "pooled_atleast4positive_folds": false, "both_pooled_years_nonnegative": false, "pooled_post31_nonnegative": false, "all_nominal_and_stress_cell_floors": false, "all_Poisson_convergence_pass": true}. Cohortes: {"cohort_nominal_points_above_floor": false, "cohort_nominal_lower95_above_floor": false, "cohort_family16_lower_above_floor": false, "cohort_all_stress_points_above_floor": false, "pooled_nominal_family16_lower_positive": false}. Los escenarios mantienen los modelos nominales fijos, sin refits por escenario. No se repitió fuente o CDF y no hubo inferencias de 2025 o envíos.

La fuente, las curvas, las reservas a valoración y la cola siguen siendo supuestos; ambos años destino son desarrollo adaptativo. La validación condicional no incluye toda la incertidumbre de ajuste/selección ni prueba generalización privada. B00, F3c y todas las alternativas se conservan, sin revisión profesional independiente.

Próximo: Review ONLY new saved P110cost/count matched-null loss, coefficients and group/cell influence without fits/resampling. Separate whether observed-count correction transfers but frozen source marks/level fail. Preserve all raw outputs; no alpha/line/feature/weight rescue. Identify a new evidence-backed mechanism before another recipe; no new CSVadmitted.
