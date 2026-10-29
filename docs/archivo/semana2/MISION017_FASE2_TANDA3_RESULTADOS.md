

## CatBoost fuente 2021–2024 y mezclas fijas, 2026-10-25 (Bogotá)

Codex, 2026-10-26T02:18:23.006423+00:00. La fuente de2.409.311periodos desarrollados quedó reconstruida con las variables comunes de F2. Se cotejaron las15CDF de coste maduro, las mezclas por peril y T0 por año con el antecedente de Claude. Los274siniestros anteriores a la cobertura disponible se preservan para reproducir el uso histórico en la CDF; no se asignan a periodos inventados. Se entrenaron tres CatBoost conservadores, con600rondas fijas, depth5 y pérdida Tweedie1,5. La versión inicial de integración falló por el control de orden de multiplicación: la diferencia máxima era2,28e-13CU. El modelo terminado de autos se conservó y reutilizó porSHA; solo se ajustaron después edificios y contenidos. No hubo un segundo ajuste de autos.

| Variante | D² local | Diferencia | IC95 por componentes | Después de retirar31grupos favorables |
|---|---:|---:|---|---:|
| Q1 | 0.131314 | -0.002515 | [-0.007399; +0.002496] | -0.009078 |
| Q2 | 0.134785 | +0.000955 | [-0.000258; +0.002240] | -0.000913 |
| Q3 | 0.134764 | +0.000935 | [-0.001437; +0.003402] | -0.002588 |

Referencia de esta comparación: N0=0.133829. Ninguna variante cumple todos los criterios preinscritos. Se conservan los adversos, B00, F2 y todas las alternativas; no se promueve ni retira ningún modelo por este score.

Los15ámbitos reales se reprodujeron con ajuste bloqueado; se verificaron las45condiciones de primer orden de los niveles aprendidos dentro del ámbito. Los cambios de etiquetas retenidas no alteraron los predictores ni las predicciones reproducidas. Coste de la tanda:3estimadores fuente,15CDF empíricas reconstruidas para las entradas y48constantes de precio; cero nuevos ajustes de C0 emergente.

2024 es desarrollo adaptativo autorizado, no un holdout intacto. El ámbito de fuente incluye2024 para información disponible al inicio de2025; no se afirma un backtest prospectivo de2024. La incertidumbre de cola, reservas, maestros sin fecha y semántica entre mercados sigue abierta. Los intervalos condicionan en los modelos fuente fijados. No es revisión profesional independiente. No hubo envíos ni consultas de nuevos scores para decidir estas recetas. La última marca pública conciliada del equipo es0,16033, inferior a0,17.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/tanda3_20261025_v3/validation_v1/report.json.
