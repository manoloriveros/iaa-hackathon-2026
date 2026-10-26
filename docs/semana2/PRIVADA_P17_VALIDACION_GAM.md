

## Privada P17: GAM mejora el punto, pero no supera estabilidad, 26 de octubre de 2026

Codex, 2026-10-26T18:20:12.682434+00:00. Se completó el contraste preinscrito del GAMcon curvas5/4/3y dormitorios lineales, en el algoritmo completo S2/H1.

| Nominal frente a A1S/S2/H1 | Δ D² | IC95 por grupos | Post31 | Peor celda |
|---|---:|---|---:|---:|
| POOLED | 0.0013249 | [-0.0006916, 0.0036034] | -0.0022146 | -0.0154700 |
| TRANSFER | 0.0015262 | [-0.0012781, 0.0049545] | -0.0037172 | -0.0198070 |

El punto mejora en ambos años y al menos cuatro folds, y la transferencia es positiva. Persisten intervalos compatibles con cero, Post31negativo y pérdidas por celda. El mínimo0,002no se cumple en el combinado. No se adopta ni se envía el GAM.

| Nominal frente al GLM con indicadores | Δ D² | IC95 emparejado | Post31 | Peor celda |
|---|---:|---|---:|---:|
| POOLED | 0.0008594 | [-0.0011198, 0.0029196] | -0.0018366 | -0.0133097 |
| TRANSFER | 0.0020759 | [-0.0000334, 0.0043002] | -0.0015306 | -0.0082829 |

La comparación secundaria de transferencia es prometedora en punto, pero su intervalo también incluye cero. Se obtuvieron diferencias de draws existentes con los mismos grupos, outcomes, orden, semillas y denominadores; no hubo otro remuestreo para el secundario. No se atribuye causalmente la diferencia a una curva o variable concreta.

| Escenario frente a referencia | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |
|---|---:|---:|---:|---:|
| RESERVE075 | 0.0011168 | -0.0170604 | 0.0009492 | -0.0221378 |
| RESERVE125 | 0.0015232 | -0.0141327 | 0.0020620 | -0.0178343 |
| TAIL005 | 0.0013334 | -0.0154084 | 0.0015623 | -0.0197221 |
| TAIL010 | 0.0013418 | -0.0153462 | 0.0015988 | -0.0196366 |

Las sensibilidades no resuelven los pisos; reservas75%empeora hasta−0,0221378en una celda de transferencia. Son precios congelados bajo objetivos/enlaces fijados, no recalibraciones completas de cada valoración. Todo adverso queda guardado.

La inspección de parámetros guardados muestra que el nivel de la mitad fuente de edificios varía1,20veces entre folds de transferencia, frente a1,14en autos y1,06en contenidos. Son parámetros de un componente, no niveles de todo el algoritmo. La credibilidad existente ya cuenta siniestros con coste positivo en sus pesos, no filas; no se ha encontrado un fallo de conteo. P13ya distinguió pérdida de nivel y de asignación. No corresponde añadir capacidad fuente para corregir sin más una calibración de nivel inestable.

Siguiente contraste: un algoritmo más sencillo, GAMfuente absoluto con calibración Tweedie conjunta regularizada. Un intercepto país y ajustes de ramo/negocio compartirán información, con penalización fija y solo las covariables destino de G3ya usadas. No conservará N3ni la corrección de cinco miembros o normalizadores de cartera al predecir: es otra receta completa, no una ablación de un único efecto. La hipótesis de compartir escala entre ramos necesita validación y puede fallar si sus diferencias entre mercados son reales. No se ha aplicado todavía una nueva tarifa. El prototipo y el criterio se preinscribirán antes de ajustar.

Se hicieron treinta calibraciones cerradas primarias,670constantes de precio y treinta controles adversos separados. La alteración completa de T0/reserva retenidos dejó iguales artefactos y precios últimos. El momento se cotejó por sumas independientes y los treinta replays reales guardados fueron exactos con aprendizaje/inferencia fuente bloqueados; el secundario emparejado también pasó replay. Cero modelos fuente, C0, inferencias2025, precios finales o envíos en P17.

B00/F3c/P6y todos los fallos/alternativas permanecen.2024está abierto adaptativo; fuente y marcas incluyen2024, y el soporte ponderado2025sigue insuficiente. No se acredita mejora privada ni validación profesional independiente.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P17_validacion_GAM_20261026/context_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P17_validacion_GAM_20261026/P17_replay_context.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P17_validacion_GAM_20261026/component_level_metadata.json.
