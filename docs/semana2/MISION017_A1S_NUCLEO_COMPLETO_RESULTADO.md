

## A1S: núcleo guardado y contraste completo por grupos, 26 de octubre de 2026

Codex, 2026-10-26T08:23:44.252276+00:00. Se completaron los 18 ajustes fuente previstos (9 internos y 9 refits) con tres semillas fijas por ramo. Partición fuente por 476.444 componentes cliente/dirección, máximo 37 filas; modelos y componentes guardados. Las rondas se eligieron solo en fuente. No hubo curvas/C0 nuevos, entrenamiento emergente iterativo, precios finales de 2025 o envíos. A1S es alternativa nueva explícita con enlace aprendido solo en fuente e historia limitada al corte, no reproducción exacta ni certificación del A1 legado.

La calibración y aplicación completas excluyen los grupos emergentes retenidos; los 15 ámbitos pasaron alteración de T0/reservas retenidos y replay exacto con aprendizaje bloqueado. C0 exterior se reutilizó con membresía cotejada. La pérdida se cotejó con sklearn; los niveles, por momento y derivada independientes. La etapa fuente pasó reproducción desde archivo, orden y suma de hojas independiente.

D² local de desarrollo 2023–2024: N3 0.13524973, G3 0.13709993, S0 0.13381748, S1 0.13556822, S2 0.13736800. El primario S2 frente a G3 cambia +0.00026808; IC95 por componentes [-0.00168871, +0.00250153]. S0 es A1S calibrado; S1 su mezcla aritmética fija 50/50 con N3/T2b; S2 añade las correcciones residuales estándar. S0/S1 son ablaciones declaradas antes de puntuar, sin selección posterior de ganador.

Contribuciones por fold: {"0": 0.0003778641297103907, "1": 0.00042261759035185797, "2": 0.0003251710534871106, "3": -0.0006796348772966613, "4": -0.0001779413691419666}. Por año: {"2023": 0.0007293438303548399, "2024": -0.0004612673032441086}. Tras quitar los 31 grupos más favorables, diferencia -0.00286558. Sensibilidad ponderada a cartera 2025: -0.00373861; el ESS previamente fallido sigue impidiendo interpretarla como confirmación fiable. Criterios cumplidos: . Fallos: delta_ge_002, lower95_positive, positive_folds_ge4, both_years_nonnegative, post31_nonnegative, cell_min_ge_minus001.

No se compara directamente con F3c completo porque faltan los artefactos A1 corregidos históricos; una ganancia frente a G3 no equivale a mejora pública. 2024 está abierto y es desarrollo adaptativo; los maestros sin fecha, el corte único, cola y reservas siguen condicionando la interpretación. La selección interna fuente condiciona el enlace de observación ya aprendido con toda la fuente. Revisión propia exploratoria tras búsqueda adaptativa, sin aprobación humana o validación profesional independiente. B00, F3c (0,16914) y todas las alternativas/adversos intactos. Meta pública 0,17 activa.

Contabilidad nueva de esta unidad: 18 ajustes fuente ya anotados por invocación; 355 constantes de precio cerradas únicas, con normalizadores y recomputaciones adversas separados en el informe. Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/A1S_nucleo_20261026_v1/source_models/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/A1S_nucleo_20261026_v1/target_complete_core/report.json.

Siguiente unidad: Use this completed adverse full-core result to identify a concrete unresolved failure before another recipe. Do not repeat A1Sfits/calibration/bootstrap or tune seeds, weights, bands or rules to held losses; retain F3c0.16914and quota.
