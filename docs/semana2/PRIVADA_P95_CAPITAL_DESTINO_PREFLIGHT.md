# P95: capital ordinario en el GLM directo

Codex, 2026-10-27T08:59:45.553109+00:00.

El flujo sintético pasó con tres ajustes primarios y tres adversos. Corromper todo el payload retenido, incluido el capital, conserva exactamente los parámetros; mediana, categorías y escalas se aprenden dentro del entrenamiento. El capital se transforma una vez con log1p; su indicador de ausencia queda fuera del precio. Se comprobó la pérdida con offset y el gradiente por otro cálculo. El replay JSON, con ajuste y estimación de niveles bloqueados, conserva las predicciones y su aplicación por subconjuntos/permutaciones.

| Ramo | Pólizas históricas enlazadas | Capital ordinario | Dudoso o ausente |
|---|---:|---:|---:|
|buildings|27447|27394|53|
|contents|34566|34509|57|

La unión por fila y año cubre exactamente las entradas 2023/2024; las quince vistas conservan sus folds. Solo se leyeron row_id, period_start y sum_insured de las pólizas. No se leyó prima ni siniestros para construir capital, ni se reparó una escala dudosa. Los filtros de 10 millones y un millón vienen de F0 y siguen siendo una decisión de incertidumbre; no son límites oficiales. Disponibilidad condicional de instantánea, sin historia transaccional que certifique cotización.

Cero ajuste real, nuevo score, CDF, inferencia2025 o envío. La evaluación real aún no está hecha: necesita registro separado. Se conserva P88 como comparador completo, B00 y todos los adversos.2024abierto adaptativo; no validación independiente ni evidencia de mejora privada.

Próximo: P96: separately register and freeze complete same-P88 standard GLM plus direct ordinary capital. Reuse all90 same-scope P88 prior levels and five motor models by code/data/keys; fit only10+10 property models. All old pooled/cohort/scenario/family/convergence/level/influence gates unchanged; whole poison includes capital; replay blocks fits and level estimators. No threshold/alpha/line rescue or 2025/upload before complete admission and transfer.
