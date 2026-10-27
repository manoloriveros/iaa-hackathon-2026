# P92: selección interna de longitud y prefijos

Codex, 2026-10-27T08:25:31.188605+00:00. El número de rondas se elige exclusivamente dentro de cada entrenamiento entre64/128/256, común a los3ramos. Profundidad, hojas, campos, paso y semilla permanecen fijos. Empates numéricos prefieren menos rondas.

Cada ámbito aprende sus propios niveles y preproceso, con un máximo256del que salen los tres prefijos. Pasaron18máximos sintéticos primarios/18adversos y3ajustes independientes64: los prefijos64coincidieron exactamente en estructura y predicciones con esos ajustes. Todos los prefijos validaron offset/métrica nativa/precisión/hojas/límites; selección, hashes de modelos internos y predicciones finales fueron iguales con payload exterior alterado. Replayde45objetivos internos y finales sin ajuste exacto.

Se reutilizaron75tablas internas protegidasP84porSHA, con cotejo nuevo de claves/grupos, sin repetir CDFo tomar niveles/qexteriores. No hay mejor longitud real, score exterior nuevo o CSVadmitido. Una evaluación posterior conserva todas las guardas y transferencia propia; puede reutilizar finales64exactosP90ypriorsexteriores conocidos en sus mismos ámbitos, nunca dentro de un entrenamientointerno distinto. Cero ajustes reales/CDF/2025/envíos. B00/F3cyadversos preservados,2024abierto adaptativo; presión de límites no prueba mejora privada, sin revisión independiente.

Próximo: P93: register/commit EXACTP92common-inner-length-selection whole algorithm,75primary/75adverse max256inner fits plus atmost15+15newfinal fits,450+450newinnerlevels, reuse fullouterP90levels and exact64models when selected64. All old outerguards/native integrity/conditionaltransfer, no round/depth/field/step/line rescue. Replay225inner objectives/all5selectors and15final models without fitting.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P92_selector_rondas_preflight_20261027/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P92_selector_rondas_preflight_20261027/synthetic.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P92_selector_rondas_preflight_20261027/bindings.json.
