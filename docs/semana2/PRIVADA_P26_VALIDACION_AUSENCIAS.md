# P26: el punto global favorable no resiste las guardas privadas

Codex, 2026-10-26T20:44:15.756019+00:00. Se contrastó la receta preinscrita: relatividades fuente P25 con la misma mezcla50/50, calibración S2 y media H1/G3. La fuente no volvió a entrenarse. Los resultados se comparan con el algoritmo propio reproducible A1S/S2/H1, no con una reproducción exacta de F3c.

| Nominal | Δ D² | IC95 por grupos | Post31 | Peor celda |
|---|---:|---|---:|---:|
| POOLED | +0.0003331 | [-0.0000804; +0.0007877] | -0.0004121 | -0.0044724 |
| TRANSFER | +0.0004342 | [-0.0000414; +0.0009326] | -0.0004641 | -0.0002659 |

El combinado y la transferencia mejoran en punto, con intervalos que incluyen cero. Cuatro folds combinados y ambos años son positivos; no se alcanza el mínimo incremental registrado y la ganancia cambia de signo al retirar los31grupos más favorables. También falla el piso combinado por celda. No se adopta ni se envía la variante; tampoco se retira de las alternativas.

| Cohorte nominal | Δ combinado | IC95 combinado | Δ transferencia | IC95 transferencia |
|---|---:|---|---:|---|
| NB | -0.0004072 | [-0.0014696; +0.0006629] | +0.0002471 | [-0.0009781; +0.0015055] |
| NB_BROKER | -0.0005085 | [-0.0015515; +0.0005230] | +0.0000179 | [-0.0015311; +0.0016486] |
| NB_BROKER_ZERO | -0.0004161 | [-0.0014897; +0.0006834] | +0.0001495 | [-0.0014923; +0.0018810] |

Las tres cohortes de negocio nuevo combinadas empeoran. Sus límites inferiores marginales y de familia16incumplen el piso, aunque los puntos permanecen dentro de este. Los puntos de transferencia positivos tampoco prueban mejora privada. No se rescatan ramos, semillas o máscaras. Las bandas son exploratorias tras búsqueda adaptativa y sus colas tienen poca resolución.

| Escenario | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |
|---|---:|---:|---:|---:|
| RESERVE075 | +0.0003256 | -0.0044724 | +0.0004091 | -0.0001856 |
| RESERVE125 | +0.0003405 | -0.0044723 | +0.0004580 | -0.0003399 |
| TAIL005 | +0.0003341 | -0.0044724 | +0.0004322 | -0.0002742 |
| TAIL010 | +0.0003350 | -0.0044724 | +0.0004302 | -0.0002826 |

Se completaron30aprendizajes cerrados primarios y30controles adversos:30componentes fuente recalibrados y40etapas residuales por rol. Constantes primarias nuevas: 670, con desglose en el recibo. Los normalizadores de aplicación se registran aparte; no son tarifas por fila independientes del lote. No se vuelven a contar los18modelos fuente y9normalizadores de P25ni N3/C0/H1reutilizados. El adaptador nuevo rechazó claves duplicadas o ausentes, año incoherente, futuro, infinitos y etiquetas en su esquema. Se reutilizaron los fixtures completos y los replays de padres que no habían cambiado, vinculados por SHA. Los30flujos reales nuevos fueron invariantes a T0/reservas retenidos alterados. El replay bloqueó aprendizaje e inferencia fuente y cotejó precios, normalizadores, draws guardados e intervalos sin remuestreo.

La sensibilidad de reservas/cola mantiene precios y enlaces congelados; no acredita suficiencia de reservas ni recalibra toda la valoración de cada rama. El soporte ponderado2025insuficiente y la disponibilidad temporal de fuente/marcas siguen abiertos. No hay mejora privada acreditada ni revisión profesional independiente, conforme a la distinción de Gobernanza IAA§2.8y Documentación§3. B00/F3c y todas las alternativas se conservan;2024es desarrollo adaptativo abierto. Cero ajustes fuente/C0, inferencias2025, precios finales o envíos nuevos.

Siguiente trabajo: P27: inspect existing frequency/severity/peril recipes and their response/exposure/reporting contracts before considering a distinct standard source model. Use bounded existing B00-B20and phase2FS/FSp/tanda1/tanda8/tanda9recipes, preserve their adverse results and avoid rerunning them. Establish whether an untied count/severity model under current source2021-2024/eCost is genuinely new and identifiable with saved reporting objects. Never derive claim counts from aggregate positive T0, treat cost completion as frequency completion, or reuse absent C0ancestry. Inspect row/year/group/response/source hashes and missing dependencies only; no fitting, source inference, new target scores or2025prices in this readiness unit. If an equivalent recipe exists, reuse its evidence; if prerequisites fail, document the missing contract rather than fit an arbitrary offset. Do not search P25mask rates/seed/line mixtures or lift floors from its weak P26point gain. Keep B00/F3c and2024open/adaptive.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P26_validacion_ausencias_20261026/P26_context_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P26_validacion_ausencias_20261026/cohort_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P26_validacion_ausencias_20261026/P26_replay_context.json. Código congelado antes de calibrar:prefijo de commit e06b28b8. El informe crudo conserva el prefijo P10del motor reutilizado; el contexto identifica P26.
