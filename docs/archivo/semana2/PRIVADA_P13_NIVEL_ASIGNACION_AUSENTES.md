

## Privada P13: nivel, asignación y ausencia de datos del GLM, 26 de octubre de 2026

Codex, 2026-10-26T17:20:37.986122+00:00. Se completaron las veinte descomposiciones nominales preinscritas, sin volver a ajustar, inferir, remuestrear o crear precios.

| Ámbito global | Δ total | Δ asignación perfilada | Δ penalización de nivel | Máxima Δ con nivel oráculo nuevo frente a referencia fija |
|---|---:|---:|---:|---:|
| POOLED | 0.0005933 | 0.0005773 | 0.0000160 | 0.0005941 |
| TRANSFER | -0.0006249 | 0.0001251 | -0.0007500 | 0.0008987 |

El deterioro global de transferencia se atribuye principalmente al nivel: la asignación perfilada mejora ligeramente. No corresponde afirmar que todo deterioro venga de la forma de riesgo. El nivel oráculo podría mejorar una referencia sin perfilar, pero usa respuestas retenidas y no es un factor admisible. No se ha estimado una corrección de nivel.

En contenidos2023, tanto nuevos como renovaciones, aun el mejor escalar del GLM queda por debajo de la referencia fija (−0,0098682 y −0,0044354 de Δ de celda respectivamente). Edificios nuevos2023 también queda por debajo (−0,0003851). En edificios nuevos2024 hay pérdidas tanto de asignación perfilada como de nivel; su mínimo oráculo sí podría superar una referencia fija sin perfilar. La pérdida perfilada no es una métrica pura de ranking ni una atribución causal. Se verificaron las identidades por sumas escalares, desviación directa, sklearn, derivada y la invariancia de escala sobre agregados, sin crear precios reescalados.

El censo de covariables produjo78banderas: trece pares ramo/variable repetidos en los seis ámbitos destino año/negocio. Todas se deben al aumento de ausentes, no a nuevas categorías o recortes numéricos grandes. En2025los campos señalados tienen entre11,37%y12,29%ausentes; las referencias fuente comparables están entre2,40%y2,54%. La máxima brecha de recorte numérico es0,65puntos porcentuales y no se observaron valores categóricos ausentes del conjunto de valores fuente en estas matrices. Esto no acredita soporte conjunto, transportabilidad o disponibilidad temporal de los maestros. El ESS2025fallido permanece.

| Ramo | Variables con brecha de ausentes |
|---|---|
| Autos | household_size, years_at_address, distance_to_river_km, vehicle_age, engine_size_cc |
| Edificios | household_size, years_at_address, distance_to_river_km, days_unoccupied |
| Contenidos | household_size, years_at_address, distance_to_river_km, high_value_items |

P11imputa la mediana numérica sin indicador, de modo que un ausente y un valor observado igual a la mediana tienen la misma representación. La revisión acotada de cinco productores GLM fuente anteriores tampoco encontró add_indicator; no se afirma ausencia en todas las familias históricas. El mayor porcentaje de ausentes era una carencia conocida de los mercados: este censo comprueba su persistencia en el contrato actual de cuatro años, sin presentarlo como un descubrimiento causal. No se repitieron los ajustes de las recetas enmascaradas de2023.

Decisión: probar primero una corrección estándar y concreta de representación, indicadores de ausencia numérica con penalización fija, antes de añadir no linealidad o interacciones. Los indicadores se decidirán por presencia no constante en fuente, nunca por su relación con respuestas destino. La hipótesis necesita nueva preinscripción y comparación completa; no se adopta una receta ni se explica todavía el fallo por los ausentes.

Se guardaron40escalares oráculo solo para diagnóstico, separados de ajustes y constantes de precio. Cero fits, C0, inferencias nuevas, vectores predictivos o envíos. B00/F3c/P6y todos los adversos permanecen;2024abierto adaptativo, prioridad privada activa.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P13_atribucion_GLM_20261026/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P13_atribucion_GLM_20261026/replay_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P13_atribucion_GLM_20261026/bounded_missing_indicator_review.json.
