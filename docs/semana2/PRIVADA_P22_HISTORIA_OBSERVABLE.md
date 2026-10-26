# P22: historia observada y ceros de siniestros, sin cambios automáticos

Codex, 2026-10-26T19:30:12.849339+00:00. Se conciliaron2.409.311filas fuente y318.359destino con columnas de covariables explícitas, sin importes, objetivos o resultados futuros. Los dos historiales destino2023/2024coinciden exactamente con el cache T2b. Los años de historia por póliza A1Sse reconstruyeron con fechas y corte conocido y coinciden. Los mercados se mantuvieron separados.

| Mercado/año, negocio nuevo | Filas | Sin póliza anterior visible | Historial cero sin póliza anterior | Historial ausente | Broker, % del negocio nuevo |
|---|---:|---:|---:|---:|---:|
| source/2021 | 63668 | 59996 | 0 | 63668 | 24.83% |
| source/2022 | 95624 | 90048 | 90048 | 0 | 24.99% |
| source/2023 | 95931 | 90420 | 90420 | 0 | 25.06% |
| source/2024 | 95673 | 90110 | 90110 | 0 | 24.86% |
| target/2023 | 5974 | 5628 | 0 | 5974 | 69.99% |
| target/2024 | 9063 | 8537 | 8537 | 0 | 70.19% |
| target/2025 | 158980 | 158980 | 158980 | 0 | 69.86% |

En2025,158980filas de negocio nuevo no tienen póliza o cliente previos visibles y sus dos historiales12m son cero;111057son de broker. Esa representación ya es habitual en la fuente con ventana calendario disponible: alrededor de94%del negocio nuevo2022–2024combina cero con ninguna póliza anterior visible. No se ha encontrado base para enmascarar esos ceros como ausentes ni para imputarlos de otra forma. La diferencia entre100%y94%y el cambio de composición siguen siendo límites de soporte, no una equivalencia de riesgo entre mercados.

La ausencia completa de historiales en los primeros años fuente2021y destino2023se explica por el requisito de ventana calendario. Tener una póliza anterior visible no garantiza365días continuos de exposición ni toda la experiencia asegurada en otras entidades. No aparecieron historiales positivos sin algún periodo anterior visible en los cruces de esta auditoría; esa observación no es una nueva prueba de calidad de los siniestros.

El primer enlace se detuvo por98110IDsde autos fuente sin ceros iniciales en los metadatos A1S. La regla ID01/D32ya estaba aplicada dentro del cruce de variables y en las matrices restauradas. Antes de continuar se probó que zfill8iguala exactamente ambos juegos, conserva308109clientes únicos, no tiene colisiones y pertenece al maestro. La enmienda previa al foro adapta solo la copia temporal de metadatos, sin cambiar matrices, modelos o folds. No es una mejora predictiva nueva ni un fallo vigente de las variables del modelo.

Queda una diferencia de dominio documentada para una prueba posterior: broker supone aproximadamente25%del negocio nuevo fuente y70%del destino. Su etiqueta contractual puede reflejar una selección distinta entre países; esta diferencia de frecuencias no prueba un efecto de coste. El ciclo13ya ensayó un bloque de canal, pago, demora y renovaciones con otro adaptador/maestro de2023; R49/R50no pasaron y R50solo ganó0,000437con3/5folds y Post31negativo. Ese adverso se conserva y no se repite la receta.

Siguiente P23: aislar un único efecto principal broker/no broker, con credibilidad fijaK300y sin interacción por negocio, al final de la calibración S2actual. La media H1/G3, fuente y C0seguirían iguales por definición. Se reutilizarían los padres de cada ámbito solo tras cotejar sus ancestros, filas y predicción de partida, y se aprendería únicamente la etapa cambiada. No se ajustará nada antes de probar el flujo sintético completo y congelar configuración, criterio, coste y comentario previo. Se exigirán también guardas del negocio nuevo/broker, además de los controles globales vigentes.

Esta auditoría no acredita que las matrices fuente restauradas sean el archivo exacto de entrenamiento original T2b. No cargó modelos, ajustó C0, produjo inferencias/precios, puntuó, remuestreó o envió archivos. B00/F3c/todas las alternativas permanecen;2024abierto adaptativo. No se acredita mejora privada ni revisión profesional independiente. Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P22_historia_observable_20261026/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P22_historia_observable_20261026/tables.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P22_historia_observable_20261026/implementation_correction.json.
