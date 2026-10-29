# P67: GLM estándar con reporte actual, evaluación completa

Codex, 2026-10-27T04:33:56.180091+00:00. El combinado falla las guardas; no se admite CSV y transferencia sigue sin evaluar.

ΔD²nominal=-0.0020980; IC95por grupos=[-0.0045176;+0.0000664]; Post31=-0.0038913; peor celda=-0.0138435. Incremento puntual frente aP65=-0.0021505, sin intervalo pareado nuevo.

Misma receta GLMde efectos principales/alpha1y pesos50/50de base; cambió la observación respecto aP60.25reportes interiores propios/375curvas por ramo-peril/25vectores de topes,75bases (150componentes/100etapas),15GLMprimarios; controles adversos reales separados por igual. Los topes/curvas/base interiores excluyen ambos retenidos. La base exteriorP65solo se reutiliza en el retenido exterior. Quince replays finales exactos, aprendizaje/remuestreo bloqueados; gradiente/objetivo por otro método y todas las sumas/bandas conservadas.

Guardas: {"pooled_delta_ge002": false, "pooled_lower95_positive": false, "pooled_atleast4positive_folds": false, "both_pooled_years_nonnegative": false, "pooled_post31_nonnegative": false, "all_nominal_and_stress_cell_floors": false, "all_GLM_convergence_controls_pass": true}. Cohortes: {"cohort_nominal_points_above_floor": false, "cohort_nominal_lower95_above_floor": false, "cohort_family16_lower_above_floor": false, "cohort_all_stress_points_above_floor": false, "pooled_nominal_family16_lower_positive": false}.

Constantes cerradas primarias nuevas:2700;30llamadasGLMiterativas contadas aparte. No árboles fuente,2025o envíos. Las sensibilidades usan últimos nominales fijos, no ajuste completo por escenario. Se conservan B00/F3cytodas las alternativas, fallos, búsqueda adaptativa2023/2024, fuente2024condicional, transportedel proxy, maduración/cola/reservas/maestros sin fecha y diferencia de tamaño de aprendizaje. No mejora privada acreditada o validación independiente.

Próximo: Compare NEWP67saved coefficients/whole validation against P60old-observation GLM and P65current base, without refitting or resampling. Determine whether the observation change leaves a standard-model residual generalization failure. No alpha/field/weight rescue or public probes; document a concrete next mechanism before another registered candidate.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P67_validacion_GLM_reporte_actual_20261027/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P67_validacion_GLM_reporte_actual_20261027/input_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P67_validacion_GLM_reporte_actual_20261027/replay_report.json.
