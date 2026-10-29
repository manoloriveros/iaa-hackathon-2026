# P23: el efecto de canal no mejora la robustez

Codex, 2026-10-26T19:49:13.349151+00:00. Se completó la receta registrada antes de aprender: una etapa broker/no broker al final de S2, con los mismos padres A1S/N3, media H1/G3y enlace qSource. Se conservó el adverso anterior del ciclo13; esta prueba aisló otro efecto sobre el algoritmo actual.

| Nominal frente a A1S/S2/H1 | Δ D² | IC95 por grupos | Post31 | Peor celda |
|---|---:|---|---:|---:|
| POOLED | -0.0003554 | [-0.0008292; +0.0000689] | -0.0007745 | -0.0041961 |
| TRANSFER | +0.0001696 | [-0.0003050; +0.0006998] | -0.0005961 | -0.0026343 |

El combinado pierde. Solo dos folds combinados son positivos y2023pierde, mientras que2024gana muy poco. La transferencia condicional mejora en punto, con intervalo compatible con cero. El mínimo0,002, la concentración y los pisos por celda siguen incumplidos. No se adopta ni se envía esta variante.

| Cohorte nominal | Δ combinado | IC95 combinado | Δ transferencia | IC95 transferencia |
|---|---:|---|---:|---|
| NB | -0.0014145 | [-0.0026237; -0.0002475] | -0.0009085 | [-0.0020494; +0.0000507] |
| NB_BROKER | -0.0001711 | [-0.0008680; +0.0006100] | +0.0001997 | [-0.0006246; +0.0010306] |
| NB_BROKER_ZERO | -0.0001482 | [-0.0008708; +0.0006644] | +0.0003443 | [-0.0004301; +0.0011499] |

El nuevo negocio combinado pierde−0,0014145y su intervalo marginal es negativo. Los dos subconjuntos de broker son compatibles con cero; no se elige el punto favorable de transferencia para salvar la receta. Fallan las guardas adicionales de nuevo negocio, bandas y escenarios. Las seis comparaciones de cohorte usan multiplicidades compartidas con el diseño de P19, cotejadas con las cuatro guardadas, y2000réplicas. Las bandas de la familia16(globales+cohortes) son exploratorias y tienen poca resolución en sus colas; no se refinan para perseguir un pase. Ninguna banda elimina la búsqueda adaptativa anterior.

| Escenario | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |
|---|---:|---:|---:|---:|
| RESERVE075 | -0.0003242 | -0.0037605 | +0.0001544 | -0.0023623 |
| RESERVE125 | -0.0003852 | -0.0046204 | +0.0001840 | -0.0028836 |
| TAIL005 | -0.0003568 | -0.0042052 | +0.0001706 | -0.0026437 |
| TAIL010 | -0.0003582 | -0.0042144 | +0.0001717 | -0.0026532 |

La pérdida más alta del nominal corresponde a edificios nuevos en2023combinado y2024transferencia. Son sensibilidades con precios congelados, sin reestimar fuente y toda la valoración de cada rama. Los adversos y sus parámetros permanecen.

Se reutilizaron los30padres S2con grupos, filas y predicciones de partida cotejados; cada nivel tenía al menos108grupos positivos de entrenamiento. Se aprendieron solo30etapas nuevas y30controles adversos separados:60factores más90niveles auxiliares de entrenamiento,150constantes primarias nuevas. No se cuentan los parámetros reutilizados como ajustes nuevos. Los niveles auxiliares no se transfieren a la aplicación y el efecto no interactúa con negocio. La normalización usa la cohorte completa de predicciones por año/negocio; no se declara una tarifa independiente del lote.

El fixture completo comprobó padres sintéticos, aprendizaje de la etapa, alteración de todos los T0/reservas retenidos, JSON, avance a último, media de miembros y puente observado, con normalización por sumas escalares. Los30flujos reales nuevos fueron invariantes a la alteración retenida y se reprodujeron con aprendizaje e inferencia fuente bloqueados. El replay de cohortes verificó puntos, multiplicidades guardadas e intervalos sin otro remuestreo. El motor conserva el prefijo histórico P10en su informe crudo; P23_context_reportidentifica esta receta, sus fuentes y su aprendizaje.

Decisión siguiente: antes de añadir variables o capacidad, revisar una ablación estructural más sencilla, componente A1Scalibrado solo frente a la mezcla directa50/50A1S+N3actual. No se buscarán pesos ni se escogerán ramos; N3permanece como alternativa y como antecedente de la corrección H1 que seguiría congelada. Debe comprobarse primero qué parte de esta receta ya se evaluó en S0/S1/S2para no repetirla. Si es una comparación nueva, se reutilizarían forma/nivel A1Sy solo se reaprenderían los factores residuales cuya base cambia, después del fixture, criterios y registro previos. No se presenta como reproducción de F3c ni como eliminación de todas las variables condicionales del flujo.

Las cuatro discusiones públicas de parte2mantienen iguales sus metadatos respecto a la consulta anterior; no se volvieron a leer cuerpos en ese chequeo ni se infiere una aclaración temporal nueva. El aporte local CLA-S2-20261026-008se leyó como evidencia de trabajo concurrente de versionado; no se ejecutaron sus órdenes ni se inventó autorización humana en este chat para publicar, cambiar automatizaciones o reconstruir toda la historia.

B00/F3c/todas las alternativas permanecen.2024está abierto adaptativo, la fuente y las marcas incluyen2024, y el soporte ponderado2025sigue insuficiente. Cero nuevos modelos fuente, C0, inferencias2025, precios finales o envíos. No hay mejora privada acreditada ni revisión profesional independiente.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P23_canal_principal_20261026/P23_context_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P23_canal_principal_20261026/cohort_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P23_canal_principal_20261026/P23_replay_context.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P23_canal_principal_20261026/public_topic_check.json.
