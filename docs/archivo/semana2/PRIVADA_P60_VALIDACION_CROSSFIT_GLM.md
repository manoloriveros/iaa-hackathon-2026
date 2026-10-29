# P60: evaluación completa del GLM con offsets cruzados

Codex, 2026-10-27T03:20:08.162754+00:00. El combinado no supera las guardas; se conserva sin admitir para envío. Transferencia sin evaluar.

ΔD²nominal=-0.0030589; IC95por grupos=[-0.0055698; -0.0008299]; Post31=-0.0047855; peor celda=-0.0144000.

Se aprendieron25reportes interiores propios (275CDFprimarias/275adversas),75bases/75adversas (150+150componentes,100+100etapas residuales) y15GLM/15adversos. Cada fila de entrenamiento recibió exactamente un offset fuera de su grupo. q/precios/normalizadores exteriores se eliminaron antes del aprendizaje interior; la base exterior P55solo predijo el retenido exterior. Source-only fijo, mismos campos, alpha1y pesos50/50. El control numérico adverso fue real en curvas/bases/GLM, no un selector de metadatos.

Guardas: {"pooled_delta_ge002": false, "pooled_lower95_positive": false, "pooled_atleast4positive_folds": false, "both_pooled_years_nonnegative": false, "pooled_post31_nonnegative": false, "all_nominal_and_stress_cell_floors": false, "all_GLM_convergence_controls_pass": true}. Cohortes: {"cohort_nominal_points_above_floor": false, "cohort_nominal_lower95_above_floor": false, "cohort_family16_lower_above_floor": false, "cohort_all_stress_points_above_floor": false, "pooled_nominal_family16_lower_positive": false}. Se conservan todos los escenarios, celdas, años, folds, influencia, nivel y bandas16. Los últimos nominales permanecieron fijos en sensibilidades; no se afirma reentrenamiento completo por escenario. Quince replays finales exactos con aprendizaje/remuestreo bloqueados.

Constantes cerradas interiores primarias:2700. Treinta llamadas GLMiterativas reales, contadas aparte de esas constantes. Cero ajustes de árboles fuente, inferencias2025o envíos. B00/F3c/adversos conservados,2024abierto adaptativo. Persisten fuentes2024condicionales, normalizadores/tamaños64%/80%frente a80%/100%, qcomún por ramo, maestros/cola/reservas y búsqueda adaptativa. No es mejora privada establecida o revisión profesional independiente.

Próximo: Review NEWP60cross-fitted results/coefficients versus the saved P57in-sample and P55base without refitting. Determine whether cross-fitting addressed the documented transport issue; no automatic alpha/field/weight rescue. Keep all adverse scenarios/cohorts and explain remaining standard-model need before another registered candidate. No repeat old support/C0audits or public probes.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P60_validacion_crossfit_GLM_20261027/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P60_validacion_crossfit_GLM_20261027/input_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P60_validacion_crossfit_GLM_20261027/replay_report.json.
