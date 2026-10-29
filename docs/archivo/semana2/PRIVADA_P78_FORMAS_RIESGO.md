# P78: funciones de riesgo y estimadores

Codex, 2026-10-27T06:20:46.676740+00:00. Se mapearon los30GLMguardadosP75/P77en unidades originales y todas sus celdas; no se aplicaron modelos o puntuaron nuevos precios. Las elasticidades son derivadas parciales del modelo con otros inputs fijos, no efectos causales de cambiar riesgos. Se conservan todos los signos y rangos sin elegir campos.

P65usa bandasNCB0/1-2/3-5/6-9/10+e historial0/1/2+, con relatividades separadas por negocio y credibilidad linealK300. LosGLMdirectos usan pendientes log1pcomunes a ambos negocios. La forma funcional y la regularización difieren, además del prior; no se atribuye una pérdida a una sola causa.

EnP65solo las formasNCB/historia estiman razones A/Epor negocio. Los niveles de línea/negocio y los factores residuales YAusan momentosTweedie1,5yconservan su contrato. Un fixture sintético verificó por suma independiente y derivada que, con bases heterogéneas, el óptimo de escalaTweedie difiere de A/E. Eso no invalida A/Ecomo estimador de media agregada ni demuestra superioridad futura; la mezcla de credibilidad y normalización tampoco es una optimización conjunta.

El cambio siguiente propuesto sustituye solo esa ecuación de forma, conservando toda la arquitecturaP65ycredibilidad. No se eliminaron grupos, estimaron escalas reales, hicieron nuevos ajustes/CDF/scores/remuestreos/2025/envíos. B00/F3cyalternativas conservados,2024abierto adaptativo, fuente2024/cola/reservas/maestros limitan transporte, sin revisión independiente.

Próximo: P79: preflight SAMEP65structured calibrated half-source base with ONLYNCB/prior withinbusiness raw AEscale ratios replaced by relative Tweedie15scale moments. Keep bands, K300linearcred, normalization, K400business levels, source inputs/currentqand already-metric residual stages EXACT. Synthetic score/derivative/poison/full-flow checks first; no real fit until separate P80registration and all original gates. A/Eis not a proved bug; no guaranteed joint or private gain.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P78_formas_riesgo_20261027/report.json.

## Elasticidades guardadas en unidades originales

Cada fila usa el modelo y fold indicados sobre las mismas covariables históricas por ramo. A1S y T2b cambian individualmente con los demás inputs fijos; las columnas contienen percentiles 1/50/99. No se predijo un precio nuevo.

| Modelo | Ramo | Fold | A1S p1/p50/p99 | T2b p1/p50/p99 | Escala conjunta |
|---|---|---:|---|---|---:|
| P75 | motor | 0 | 0.00365/0.00365/0.00365 | 0.98994/0.98994/0.98994 | 0.99359 |
| P75 | motor | 1 | 0.00130/0.00130/0.00130 | 0.98333/0.98333/0.98333 | 0.98463 |
| P75 | motor | 2 | -0.01698/-0.01698/-0.01698 | 0.97303/0.97303/0.97303 | 0.95605 |
| P75 | motor | 3 | -0.00366/-0.00366/-0.00366 | 0.96794/0.96794/0.96794 | 0.96428 |
| P75 | motor | 4 | -0.00464/-0.00464/-0.00464 | 0.97345/0.97345/0.97345 | 0.96881 |
| P75 | buildings | 0 | 0.00820/0.00820/0.00820 | 0.99198/0.99198/0.99198 | 1.00018 |
| P75 | buildings | 1 | -0.01996/-0.01996/-0.01996 | 0.99694/0.99694/0.99694 | 0.97697 |
| P75 | buildings | 2 | -0.03866/-0.03866/-0.03866 | 0.98139/0.98139/0.98139 | 0.94273 |
| P75 | buildings | 3 | -0.02775/-0.02775/-0.02775 | 0.94626/0.94626/0.94626 | 0.91851 |
| P75 | buildings | 4 | 0.05260/0.05260/0.05260 | 0.99630/0.99630/0.99630 | 1.04890 |
| P75 | contents | 0 | 0.09599/0.09599/0.09599 | 0.97500/0.97500/0.97500 | 1.07099 |
| P75 | contents | 1 | 0.06777/0.06777/0.06777 | 0.94433/0.94433/0.94433 | 1.01211 |
| P75 | contents | 2 | 0.08761/0.08761/0.08761 | 0.96251/0.96251/0.96251 | 1.05013 |
| P75 | contents | 3 | 0.10594/0.10594/0.10594 | 0.98477/0.98477/0.98477 | 1.09072 |
| P75 | contents | 4 | 0.09415/0.09415/0.09415 | 0.96644/0.96644/0.96644 | 1.06059 |
| P77 | motor | 0 | 0.45314/0.53390/0.66320 | 0.36721/0.49652/0.57727 | 1.03041 |
| P77 | motor | 1 | 0.44986/0.53061/0.65992 | 0.36195/0.49125/0.57200 | 1.02186 |
| P77 | motor | 2 | 0.43160/0.51236/0.64166 | 0.35133/0.48064/0.56139 | 0.99299 |
| P77 | motor | 3 | 0.44533/0.52609/0.65539 | 0.34654/0.47584/0.55659 | 1.00193 |
| P77 | motor | 4 | 0.44410/0.52485/0.65415 | 0.35204/0.48134/0.56210 | 1.00619 |
| P77 | buildings | 0 | 0.44096/0.57377/0.70066 | 0.36828/0.49517/0.62799 | 1.06895 |
| P77 | buildings | 1 | 0.41399/0.54681/0.67370 | 0.37312/0.50001/0.63283 | 1.04682 |
| P77 | buildings | 2 | 0.39663/0.52945/0.65634 | 0.35779/0.48468/0.61749 | 1.01412 |
| P77 | buildings | 3 | 0.40481/0.53762/0.66451 | 0.32282/0.44971/0.58253 | 0.98734 |
| P77 | buildings | 4 | 0.48468/0.61750/0.74439 | 0.36792/0.49481/0.62763 | 1.11231 |
| P77 | contents | 0 | 0.46296/0.62037/0.72925 | 0.36326/0.47214/0.62955 | 1.09251 |
| P77 | contents | 1 | 0.43553/0.59295/0.70182 | 0.33406/0.44293/0.60035 | 1.03588 |
| P77 | contents | 2 | 0.45664/0.61406/0.72294 | 0.35002/0.45890/0.61632 | 1.07296 |
| P77 | contents | 3 | 0.47312/0.63053/0.73941 | 0.37344/0.48232/0.63974 | 1.11285 |
| P77 | contents | 4 | 0.46330/0.62072/0.72960 | 0.35565/0.46453/0.62194 | 1.08524 |

Fixture sintético, dos bases de 1 y 100 con costes de 100 y 100: A/E=1.98019802; escala Tweedie=10.00000000. La derivada de escala en el segundo valor es 0. No se usaron costes reales para esta comparación.
