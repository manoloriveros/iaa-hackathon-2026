# P91: límites de los árboles guardados

Codex, 2026-10-27T08:02:13.750917+00:00. Se inspeccionaron los15modelosP90sin predecir o ajustar. Sus priors de calibración y preprocesos coinciden exactamente conP88; no hubo un cambio oculto de entradas en la comparación del estimador final.

| Ramo | Fold | Fracción de parámetros al paso máximo | Últimos16árboles | Máximo de entrenamiento llega a cota |
|---|---:|---:|---:|---|
|motor|0|58.0569%|50.5155%|False|
|motor|1|58.9109%|61.0000%|True|
|motor|2|52.1092%|54.6392%|True|
|motor|3|56.7073%|53.5714%|False|
|motor|4|63.2911%|59.3750%|False|
|buildings|0|82.0000%|80.1887%|True|
|buildings|1|81.0268%|88.3929%|True|
|buildings|2|86.5297%|81.2500%|True|
|buildings|3|85.4911%|83.9286%|True|
|buildings|4|82.8979%|77.9817%|True|
|contents|0|69.9774%|65.1786%|True|
|contents|1|77.8523%|71.4286%|True|
|contents|2|90.0232%|92.1569%|True|
|contents|3|82.0331%|74.2574%|True|
|contents|4|81.1791%|70.5357%|True|

Son fracciones de parámetros de hoja, no de filas/siniestros ni una prueba de convergencia o influencia por eliminación. La corrección máxima de entrenamiento se reutiliza del recibo original; no se volvió a aplicar un modelo. Que haya pasos aún limitados no demuestra que más árboles mejoren el retenido o la privada.

La opción siguiente es una selección interna finita de longitud con todo el aprendizaje protegido, no elegir rondas por resultados exteriores. Mantiene profundidad/hojas/paso/campos y compara64/128/256dentro del entrenamiento, con empate a menor longitud. Requiere presupuesto y preflight nuevos; no modifica o admiteP90. Cero ajustes, predicciones, scores, remuestreos, CDF,2025oenvíos. B00/F3cyadversos preservados,2024abierto adaptativo y límites de fuente/observación/valoración/búsqueda persistentes; sin revisión independiente.

Próximo: P92: design/syntheticpreflight finite TRAINING-ONLYcommon tree-length selection on SAMEP90features/scalarprior/step/depth. Candidate budgets64/128/256, no depth/field/step search or outer/public prefix scoring. Reuse P84protected inner qtables bySHA, learn each inner prior/preprocess ONLYon its train; one max256fit can yield cached prefix models after synthetic equivalence to standalone64. Freeze selector/tie/cost and full poison/replay before real fits; all old outerguards/conditionaltransfer remain. Leaf pressure is motivation, not evidence longer wins.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P91_limites_arbol_guardado_20261027/report.json.
