

## Privada P7: la ventana corta no explica una gran brecha global en esta cohorte fuente, 26 de octubre de 2026

Codex, 2026-10-26T15:58:58.255932+00:00. Se completó el backtest preinscrito de reporte sobre coberturas desarrolladas de 2021. Los cortes virtuales fueron diciembre de 2022 y diciembre de 2023; la referencia es el coste aceptado conocido a diciembre de 2024. Los cinco folds globales de cliente/dirección se conservaron. Cada curva se estimó con otros grupos y solo con reportes disponibles al corte. Las marcas y el estado final de siniestros se mantuvieron comunes, de modo que esto es un diagnóstico retrospectivo de reporte, no un backtest prospectivo de reservas o una CV de precios.

| Corte virtual | Coste reportado / conocido2024 | Reconstruido / conocido2024 | IC95 por grupos |
|---|---:|---:|---:|
| 2022-12-31 | 98.3848% | 99.9674% | [99.4520%, 100.4474%] |
| 2023-12-31 | 99.7888% | 100.0301% | [99.8655%, 100.1648%] |

La referencia suma 174.811.576 CU. El criterio previo de infrarrecuperación global material no se cumple en ninguno de los dos cortes. Los intervalos simultáneos exploratorios de los dos primarios también quedan próximos a uno. Esta evidencia no respalda aplicar un incremento general de cola para explicar la diferencia de nivel de 10,83% de P6 frente a F3c. Tampoco demuestra que la cola emergente sea igual o esté identificada.

| Peril largo | Corte | Recuperación reconstruida | IC95 marginal exploratorio |
|---|---|---:|---:|
| motor, bodily_injury | 20221231 | 99.5449% | [97.6042%, 101.3190%] |
| buildings, subsidence | 20221231 | 99.6270% | [99.0035%, 100.0444%] |
| motor, bodily_injury | 20231231 | 100.1144% | [99.4828%, 100.6266%] |
| buildings, subsidence | 20231231 | 100.0000% | [100.0000%, 100.0000%] |

Se conservaron todas las salidas por peril, fold y trimestre de ocurrencia. En lesiones corporales el fold1 del corte2022 recupera 94,9149%, aunque el agregado del peril sea 99,5449%. Incendio2022 sobre-reconstruye aproximadamente 1,45%. Los intervalos por peril son marginales exploratorios; no se presentan como una familia de confirmaciones simultáneas. El diagnóstico Post31 excluye grupos solo del cálculo descriptivo, sin borrar datos o reajustar.

La reconstrucción usa el coste de siniestros ya reportados al corte como entrada y lo divide por la completitud de coste estimada para su antigüedad. No se afirmó que pudiera ignorar esa entrada. El coste de reportes posteriores solo sirve como referencia: al alterar sus marcas, periles y fechas no cambió la reconstrucción. Al alterar todos los retenidos y los reportes no disponibles del entrenamiento, las curvas quedaron exactamente iguales.

Los 30 ámbitos pasaron la comprobación independiente del conjunto de riesgo por búsquedas ordenadas, producto-límite por logaritmos y CDF/marca de coste por probabilidades de evento. El replay del flujo real, con estimación bloqueada, recuperó exactamente 78.081 contribuciones reportadas de los dos cortes. El bootstrap Poisson por componentes comparte los mismos pesos entre ventanas y periles; condiciona en las curvas ajustadas y no representa incertidumbre completa de su estimación. Los componentes con coste nulo se conservan en la cohorte y se omiten solo de las multiplicaciones de ratios donde aportan exactamente cero.

La cohorte contiene 311.317 componentes, de los que 34.571 aportan coste positivo. Se conciliaron los céntimos con los periodos fuente guardados. El intento técnico V1 se detuvo antes de ajustar porque exigía que todo siniestro de calendario2021 perteneciera a coberturas2021. V2 conserva por separado 34 siniestros de autos, nueve de edificios y cinco de contenidos fuera de ese ámbito, con IDs exactamente iguales a los no asignados históricos. El denominador sigue siendo el de coberturas asignadas definido antes de cualquier resultado. Código/fallo V1 quedan preservados con cero ajustes; no se descartaron filas para mejorar el contraste.

Coste: 149 ajustes de reporte primarios y 149 controles adversos separados. Se reutilizó una distribución por papel al ser idénticos todos los eventos/marcas y estar completamente observados en ambas ventanas; se cotejó la identidad con el conjunto de riesgo. Los 21 ajustes sintéticos se registran aparte. No hubo modelos de precio, C0 emergente, inferencias de modelos fuente, nuevos precios 2025, scores competitivos o envíos. El CSV P6 conserva su SHA.

Las limitaciones siguen siendo relevantes: un mercado fuente no aporta soporte emergente, la referencia observada2024 puede omitir desarrollos posteriores y las marcas finales no eran necesariamente conocidas en los cortes virtuales. La estacionalidad, dependencia de severidad y diferencias de cartera son explicaciones alternativas. La consulta bibliográfica archivada contiene resúmenes/fichas primarias; el acceso directo a los artículos falló y no se declara lectura íntegra o validación del método por esas fuentes.

Decisión: no adoptar un factor de cola fuente, no reescalar P6 a F3c y no modificar el objetivo nominal. La revisión siguiente comprobará contratos reales de variables, exposición y normalización de los backbones. En particular, una prueba de exposición sobre relatividades fuente ya guardadas no equivale a cambiar la exposición dentro de toda la inferencia fuente desde datos crudos. Cualquier discrepancia nueva material necesitará una prueba propia registrada antes de inferir o ajustar. B00, F3c, P6 y todas las alternativas/fallos permanecen; 2024 sigue abierto adaptativo y la privada continúa como prioridad. No se acredita mejora privada, promoción o validación profesional independiente.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P7_ventana_reporte_madura_20261026_v2/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P7_ventana_reporte_madura_20261026_v2/replay_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P7_ventana_reporte_madura_20261026_v2/preflight.json.
