

## Privada P15: indicadores sin mejora robusta establecida, 26 de octubre de 2026

Codex, 2026-10-26T17:35:07.654137+00:00. Se cerró la comparación completa de GLM4_MI/S2/H1frente al algoritmo A1S/S2/H1y, secundariamente, al GLMlineal P12. Los mismos grupos, C0, N3, exposición, mitades fuente/N3y media de cinco cocientes H1/G3se mantuvieron.

| Nominal frente a A1S/S2/H1 | Δ D² | IC95 por grupos | Post31 | Peor celda |
|---|---:|---|---:|---:|
| POOLED | 0.0004656 | [-0.0020998, 0.0030850] | -0.0037067 | -0.0111331 |
| TRANSFER | -0.0005497 | [-0.0028141, 0.0019993] | -0.0044869 | -0.0161575 |

El punto combinado mejora ligeramente y ambos años contribuyen positivamente, pero solo tres folds mejoran, el intervalo incluye cero y Post31es negativo. La transferencia de destino2023a2024empeora. En edificios nuevos2024la pérdida es −0,0111331en el combinado y −0,0161575en transferencia. La variante incumple los criterios primarios conservados.

| Nominal frente a GLM sin indicadores | Δ D² | IC95 emparejado | Post31 | Peor celda |
|---|---:|---|---:|---:|
| POOLED | -0.0001277 | [-0.0010179, 0.0007835] | -0.0014605 | -0.0045051 |
| TRANSFER | 0.0000752 | [-0.0008153, 0.0009644] | -0.0012563 | -0.0047893 |

Los indicadores no acreditan una mejora consistente ni siquiera frente al GLMsin indicadores. La brecha de ausentes y la colisión de representación siguen siendo hechos, pero no se ha establecido que expliquen el adverso. Los intervalos secundarios se obtuvieron restando draws con los mismos grupos, etiquetas, orden, semillas y denominadores. Se verificaron las diferencias con las pérdidas directas y un replay de los arrays; no se repitió el remuestreo anterior. Son intervalos condicionales exploratorios, no una replicación independiente ni ajuste global por toda la búsqueda.

| Escenario frente a referencia | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |
|---|---:|---:|---:|---:|
| RESERVE075 | 0.0002997 | -0.0144217 | -0.0012491 | -0.0198787 |
| RESERVE125 | 0.0006228 | -0.0108297 | 0.0000976 | -0.0129486 |
| TAIL005 | 0.0004879 | -0.0110402 | -0.0004963 | -0.0160465 |
| TAIL010 | 0.0005103 | -0.0109467 | -0.0004423 | -0.0159348 |

Las sensibilidades fijadas no resuelven los pisos: reservas75%alcanza −0,0198787en la peor celda de transferencia. Son precios congelados con objetivo/enlace de observación variados, sin nuevas calibraciones completas de cada valoración. Todos los adversos nominales y de escenarios se conservan; no se eligen pesos o ramas positivas para una mezcla.

Se hicieron treinta calibraciones cerradas primarias,670constantes de precio, y treinta controles adversos separados. Alterar todos los T0y reservas retenidos dejó exactamente iguales artefactos y precios últimos. El momento se cotejó por sumas escalares y los treinta flujos reales guardados pasaron replay con aprendizaje/inferencia fuente bloqueados. Los tres fitsfuente se cuentan solo en P14; P15no ajustó modelos fuente ni C0y no produjo inferencias2025, precios finales o envíos.

Decisión: no adoptar GLM4_MIcomo sustitución. Antes de más complejidad se contrastará una forma aditiva estándar con curvas univariadas fijadas, sin interacciones. P13mostró pérdidas de asignación que un escalar no compensaba en algunas celdas; P15no demostró que indicadores solos las resuelvan. Eso justifica probar flexibilidad funcional, sin afirmar una causa no lineal. La lista física y4nudos/grado2procederán de la especificación GAMfuente anterior, aplicada al contrato actual de cuatro años y conservando indicadores; no se elegirán por ganancias de celda. Los experimentos fuente2023históricos no se repetirán sobre las mismas entradas. El nuevo preflight y la receta completa se congelarán antes de cualquier ajuste.

B00/F3c/P6y todas las variantes fallidas se mantienen. La fuente contiene2024y destino es adaptativo; el ESS2025sigue insuficiente. No se acredita mejora privada, promoción formal o validación profesional independiente.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P15_validacion_ausentes_20261026/context_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P15_validacion_ausentes_20261026/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P15_validacion_ausentes_20261026/P15_replay_context.json.
