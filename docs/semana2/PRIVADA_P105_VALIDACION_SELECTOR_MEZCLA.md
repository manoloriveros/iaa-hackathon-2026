# P105: selección interna común de mezcla

Codex, 2026-10-27T10:34:39.552570+00:00. El combinado falla; no se admite un CSV nuevo.

Diferencia D² frente a referencia local: -0.0004141; IC95 por grupos [-0.0011842, +0.0002658]. Post31: -0.0010516; peor celda: -0.0073821. Diferencia puntual frente a P65 fijo50/50: -0.0004666, sin nuevo intervalo pareado.

| Fold exterior | Peso A1S elegido dentro de train |
|---|---:|
|0|0.25|
|1|0.25|
|2|0.25|
|3|0.50|
|4|0.50|

El guardián inicial reprodujo exactamente precios y normas50/50en75ámbitos internos y15exteriores antes de cualquier nuevo ajuste. Se reutilizaron sus180componentes propios distintos, sin nuevo CDF/fuente o modelo nativo. Para pesos distintos se hicieron412etapas Gprimarias y412adversas;5150constantes primarias nuevas contando factores, nuisance y centros de entrenamiento (adversos separados; no grados de libertad).

Los cinco selectores completos coincidieron bajo veneno exterior e interior. Se reprodujeron375objetivos internos, las cinco selecciones y quince finales, con aprendizaje bloqueado y el mismo payload limpio al cotizar. Intervalos y primeras ponderaciones se cotejaron sin nuevo remuestreo en replay. La selección usa solo costes interiores del entrenamiento; ningún peso proviene del público o del resultado exterior.

Guardas globales: {"pooled_delta_ge002": false, "pooled_lower95_positive": false, "pooled_atleast4positive_folds": false, "both_pooled_years_nonnegative": false, "pooled_post31_nonnegative": false, "all_nominal_and_stress_cell_floors": false}. Cohortes: {"cohort_nominal_points_above_floor": false, "cohort_nominal_lower95_above_floor": false, "cohort_family16_lower_above_floor": false, "cohort_all_stress_points_above_floor": false, "pooled_nominal_family16_lower_positive": false}.

Se conserva la normalización de Gdel algoritmo original por año/negocio al aplicar; no se mezcla aquí la alternativa de centros fijos P102. Sensibilidades con últimos nominales fijos, sin ajuste completo por escenario. Fuente2024 condicional, snapshots, observación/cola/reservas y búsqueda adaptativa siguen limitando la interpretación. Cero nuevo source/CDF/nativo/componentes,2025oenvíos. B00 y todas las alternativas conservadas,2024abierto adaptativo, sin garantía privada o revisión independiente.

Próximo: Inspect only saved new P105all5weight selections/inner margins and complete held cells against P65, without any refit/resampling. Do not expand weight grid, choose perline/stage, reuse selected weights outside their own training or probe the public board. If default half is selected everywhere, preserve exact existing result and move to distinct documented source/observation evidence.
