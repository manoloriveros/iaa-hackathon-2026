# P73: entradas OOF y escala de aplicación

Codex, 2026-10-27T05:13:54.764234+00:00. Se compararon15ámbitos actuales por claves/fuentes/grupos/calendario idénticos, aplicando la base exterior guardada solo a su propio entrenamiento y sin ajustar modelos. Sus etiquetas/reservas se retiraron y qse anuló antes del último. Estas salidas de entrenamiento no se usan para entrenar un stacker.

| Ramo | Fold | Ratio último full/OOF p01 | Mediana | p99 | SD logratio |
|---|---|---|---|---|---|
| motor | 0 | 0.9309 | 0.9975 | 1.1229 | 0.0375 |
| motor | 1 | 0.9347 | 0.9959 | 1.1650 | 0.0445 |
| motor | 2 | 0.9298 | 1.0014 | 1.1611 | 0.0390 |
| motor | 3 | 0.9364 | 0.9991 | 1.1298 | 0.0395 |
| motor | 4 | 0.9273 | 0.9958 | 1.1450 | 0.0455 |
| buildings | 0 | 0.9207 | 1.0046 | 1.1012 | 0.0492 |
| buildings | 1 | 0.9388 | 0.9764 | 1.1247 | 0.0426 |
| buildings | 2 | 0.8891 | 0.9788 | 1.2092 | 0.0702 |
| buildings | 3 | 0.8922 | 1.0001 | 1.1397 | 0.0771 |
| buildings | 4 | 0.9340 | 1.0004 | 1.0727 | 0.0337 |
| contents | 0 | 0.9326 | 0.9981 | 1.0930 | 0.0342 |
| contents | 1 | 0.8750 | 0.9953 | 1.1985 | 0.0663 |
| contents | 2 | 0.9114 | 1.0043 | 1.1343 | 0.0554 |
| contents | 3 | 0.9257 | 0.9941 | 1.1070 | 0.0395 |
| contents | 4 | 0.9259 | 0.9938 | 1.1121 | 0.0428 |

Las diferencias son de estimadores/ámbitos64%/80%yde normalizadores, sin verdad de error conocida o causalidad establecida. Se verificó por otro cálculo ratioobservado=ratioultimo*ratioq. Motor/contentsusan etapas residuales centradas por lote; buildingscarece de ellas, así que esa propiedad no explica universalmente sus pérdidas. Se conserva la distribución P72desde precios guardados sin elegir más paso/profundidad/rondas.

Cero nuevos ajustes, curvas, remuestreo, scores,2025o envíos. No hay CSVadmitido, eliminación de grupos o selección de campos por resultados. B00/F3cyalternativas conservados,2024abierto adaptativo y límites de transporte/cola/reservas/fuente2024condicional/maestros presentes; sin mejora privada acreditada o revisión independiente.

Próximo: P74: investigate a simpler SINGLEtargetGLMwith exposure/currentqand PUREdeveloped-only risk inputs (e.g.T2bannual offset plus A1Ssignal and existing rating covariates), removing noisy target-derived base offsets rather than stacking on in-sample parents or adding capacity. Not yet a recipe: verify source/units, freeze all fields/criterion/cost, synthetic full flow and forum before real fitting. Preserve all failed recipes; no alpha/step/line or public-score rescue.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P73_offsets_guardados_20261027/report.json.

Comprobación adicional acotada: las fechas de inicio/fin yT0/reservas originales coinciden exactamente en las15comparaciones de entrenamiento, además de año/exposición ya verificados. No produjo aplicaciones/modelos/scores nuevos. Recibo: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P73_offsets_guardados_20261027/calendar_identity_receipt.json.
