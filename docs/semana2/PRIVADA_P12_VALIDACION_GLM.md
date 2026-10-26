

## Privada P12: GLM simple sin estabilidad suficiente, 26 de octubre de 2026

Codex, 2026-10-26T16:57:50.971032+00:00. Se comparó GLM4/S2/H1 con A1S/S2/H1, conservando C0, exposición, mitades fuente/N3, etapas de calibración y los cinco cocientes H1/G3. Los grupos de treinta ámbitos se conciliaron exactamente antes de ajustar. El motor numérico es el de P10, con fuentes y preinscripción propias; se reutilizaron sus controles sin repetir fixtures idénticos.

| Nominal | Δ D² | IC95 por grupos | Después de 31 grupos | Peor celda |
|---|---:|---|---:|---:|
| POOLED | 0.0005933 | [-0.0022065, 0.0034678] | -0.0040023 | -0.0118749 |
| TRANSFER | -0.0006249 | [-0.0031233, 0.0021501] | -0.0051485 | -0.0171871 |

El punto agregado sube ligeramente y ambos años contribuyen positivamente en el esquema combinado, pero solo tres folds mejoran, el intervalo incluye cero y Post31 es negativo. El mínimo incremental0,002 no se cumple. Al aprender destino solo2023y retener2024, el resultado global empeora. La peor celda combinada es contenidos nuevos2023; edificios nuevos2024 pierde −0,011638 en el combinado y −0,017187 en transferencia. Una forma más simple no acredita por sí misma un modelo más robusto.

| Escenario fijado | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |
|---|---:|---:|---:|---:|
| RESERVE075 | 0.0003831 | -0.0154216 | -0.0013944 | -0.0213647 |
| RESERVE125 | 0.0007928 | -0.0118753 | 0.0000872 | -0.0135818 |
| TAIL005 | 0.0006233 | -0.0118749 | -0.0005653 | -0.0170593 |
| TAIL010 | 0.0006536 | -0.0118749 | -0.0005049 | -0.0169307 |

En reservas75% la peor celda de transferencia llega a −0,021365. Las sensibilidades mantienen precios y enlaces comunes fijados; no son nuevas calibraciones de todas las ramas. Se conservan los intervalos de familia10, la influencia por componente, A/E y los puntos ponderados2025con su ESS insuficiente. No se usan celdas positivas para una mezcla por ramo ni para cambiar la penalización después del resultado.

Treinta calibraciones cerradas produjeron670constantes primarias. Otras treinta llamadas adversas alteraron todos los T0 y reservas retenidos: artefactos y precios últimos fueron exactamente iguales. El momento del nivel pasó por sumas independientes y los treinta replays guardados fueron exactos con aprendizaje e inferencia fuente bloqueados. P12 no ajustó GLMfuente ni C0: los tres GLM se cuentan en P11. Tampoco calculó precios2025o envíos.

Decisión: no adoptar el GLM como sustitución completa ni retirar A1S. Se conserva con sus adversos y costes. La siguiente revisión distinguirá, sobre precios ya guardados, error de nivel y asignación relativa para precisar qué falla antes de otra receta. Cualquier nivel perfilado con respuestas retenidas será un oráculo de diagnóstico y no un factor admisible para predecir. No se inicia otra búsqueda para rescatar un score.

La interpretación continúa condicionada por fuentes2021–2024y valoración final común. Los años emergentes son adaptativos. La comparación no reproduce el F3c histórico completo y no establece rendimiento privado. B00/F3c/P6y todas las alternativas se mantienen; 2024abierto. Ningún nuevo envío en estos ciclos.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P12_validacion_GLM_20261026/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P12_validacion_GLM_20261026/replay_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P12_validacion_GLM_20261026/P12_replay_context.json.
