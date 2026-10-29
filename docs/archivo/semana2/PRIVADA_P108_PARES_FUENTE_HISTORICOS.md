# P108: pares fuente históricos preparados

Codex, 2026-10-27T11:20:44.616903+00:00.

Se exportaron las frecuencias y marcas medias pareadas de los 30 GLM fuente P29 ya guardados a las 109.296 filas históricas de 2023 y 2024. El preprocesamiento, los coeficientes y los normalizadores son los originales. La suma por peril reproduce exactamente, bit a bit, los logaritmos brutos y relativos guardados por P29 en todas las filas. También se conserva cada columna original de P107 y el orden canónico.

El proceso bloqueó las funciones de aprendizaje. La prueba sintética recorrió el filtro histórico, el preprocesamiento congelado y los predictores pareados; la alteración del contenido excluido de 2025 no cambió ninguna salida histórica. Los predictores y la suma coincidieron con cálculos escalares y pasaron las consultas individuales, permutación y recarga JSON. Se rechazaron entradas desalineadas o un año futuro marcado como histórico.

Estas salidas son tasas estimadas del mercado fuente bajo los supuestos de observación y cola ya documentados. No prueban frecuencia o severidad última identificadas, transporte al mercado emergente ni mejora privada. El contraste adverso anterior P30 sigue vigente. Falta diseñar la corrección de frecuencia destino con sus comparadores y validación completa; no se ajustó ese modelo ni se recalibraron precios. Cero refits, nuevos normalizadores, scores, precios finales, inferencia de 2025 o envíos. B00 y alternativas preservados, prioridad privada y 2024 abierto como desarrollo adaptativo.

Próximo: P109: design and freeze a standard target Poisson frequency correction using actual accepted-event counts, source-paired annual frequency offset and count-weighted completion from P107/P108. Keep original T0cost for final price-level calibration, keep source mark allocation and cost completion distinct. Specify all training normalizers, scope exclusions, penalty rescaling, comparator and whole-pipeline synthetic invariance before any real fit. Do not repeat P30 full source transfer or treat this export as predictive improvement.
