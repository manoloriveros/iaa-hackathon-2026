# Capital, clima y credibilidad antes de integrar

Codex, 23 de octubre de 2026. Capital supera la comprobación técnica por fila y se probó en el GLM estándar B14, pero el escaso efecto en el score agregado oculta cambios materiales en los registros corregidos. El clima propuesto queda fuera del contrato prospectivo. La credibilidad por fold se pudo reconstruir y probar como B15, con resultado global incierto y diferencias adversas en autos nuevos. Se conserva B00 y2024 permanece cerrado.

El [plan v6](../../../registro/semana2_desarrollo2023_plan_v6.json), COD-S2-20261023-018, precede a todos los ajustes. La [revisión previa](../../../privado/semana2/desarrollo2023/revision_integracion_20261023T233806Z_0bd51230/report.json) no ajustó ni predijo precios. El resultado se registra en COD-S2-20261023-019 del [foro](<../../../../Semana%202/Foro/FORO.md>). El [registro del ciclo](../../../privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b/decision_journal.json) conserva hipótesis, comprobación, resultado y consecuencia. Las fuentes de Claude y los hallazgos del otro encargo mantienen autoría y alcance.

## Capital: regla aplicada solo a la prueba de 2023

La tabla CAPS2-01 recibida tiene349filas de distintos años. Esta prueba materializó únicamente las56filas de2023 (26edificios,30contenidos). Todas estaban enmascaradas en F0 y tienen T0=0. Se cotejaron IDs, capital original y división por1000. No se presenta el análisis de todos los años de Claude como ejecutado por este chat.

Para evitar límites aprendidos con2024/test o con la distribución retenida, por cada ramo/fold se calcula el mínimo y máximo de prima por mil entre capitales normales del ajuste2023. Una fila sospechosa se divide solo si su propia prima por mil bruta está por debajo del mínimo y la corregida queda dentro de ese intervalo. Si falla permanece desconocida. Las56pasan también con estos límites de ajuste. Los umbrales son5millonesCU en edificios y2millones en contenidos, fijados en el plan. La prima escrita se usa como evidencia de escala y nunca entra en la matriz de predictores; esto conserva una dependencia de la tarifa y del supuesto de unidad monetaria, no confirmación económica independiente.

B14 mantiene exactamente las seis variables, alpha0, enlace log y transforms fit-only de B13. Se reentrenaron diez GLM de hogar y se copiaron exactamente los cinco modelos de autos. Solo cambia el valor de logcapital; no se edita el original o F0 global, ni se calcula una corrección/predicción para2024/test.

| Registros corregidos en OOF2023 | Filas | Predicho B13, CU | Predicho B14, CU | Rango relativo por fila |
| --- | ---: | ---: | ---: | --- |
| buildings | 26 | 14721.07 | 14270.45 | -60.70 % a 59.90 % |
| contents | 30 | 2245.69 | 2846.27 | -62.36 % a 154.09 % |

Estos son importes observados predichos de2023, comparados con la imputación anterior de capital desconocido. El rango conjunto es −62,36 % a+154,09 %. Cada fila OOF se evalúa una vez, aunque aparezca en varios ajustes. La suma predicha en los restantes registros cambia poco (menos de0,5 % por fila en hogar), pero eso no permite llamar inmaterial a la corrección por póliza. Tampoco sus56ceros pueden probar cuál escala reproduce la severidad esperada. La [descomposición por registros](../../../privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b/diagnostics/capital_row_impact.json) concilia exactamente los cambios de total y devianza.

## Clima: criterio temporal aplicado y prueba rechazada

CLIMA-S2-01 usa2024 para las filas2023 y elige las variables exigiendo persistencia también entre2024/2025. No basta con que los valores finales omitan2025: el selector depende de ese año. Se cotejó el hash del adverso de permutación recibido en COD-S2-VAL04-20261023-CLIMA-AVISO, sin repetir el ensayo sobre fuentes iguales ni adjudicar su autoría a este flujo.

Las guardas propias rechazan medidas del mismo año o posteriores a la cotización, selectores que dependan del futuro y ausencia de historia que se quiera rellenar con valores futuros. No hay filas climáticas emergentes anteriores a2023 que permitan materializar ese bloque para esta prueba. No se entrenó un comparador con fuga o un modelo artificialmente duplicado con todo el clima ausente. La variante queda fuera del contrato prospectivo actual; un uso como proxy físico condicionado o escenario requeriría otro alcance explícito y no constituiría backtest al momento de cotizar. El hallazgo S2-VAL-DAT-003 conserva su responsable y permanece abierto.

## Credibilidad: alcance corregido y probado

No se aplicó el c estimado con todo2023. Los factores recibidos por fold tienen una fórmula reconstruible, pero el script de aplicación sobre los otros OOF no aporta calibración interna anidada: las predicciones de un foldj distinto del retenidok se entrenaron con las etiquetas dek. Eliminar las filask del promedio final no elimina esa dependencia. La prueba evita por completo ese equilibrio A/E.

Se reestimaron treinta GLM auxiliares estándar (Poisson en conteos positivos y Gamma en importes positivos), solo dentro del ajuste emergente2023 de cada ramo/fold, usando asignaciones canónicas y los COVS fijados por la propuesta de Claude. La calidad del capital, mediana/centrado y referencia regional se fijan dentro del ajuste. Los errores robustos se agrupan por el componente cliente-dirección guardado, en lugar de solo cliente. Esos modelos auxiliares no se cuentan como nuevos candidatos de precio.

El prior desarrollado es el beta/SE, categorías de referencia e índice estacional guardados por Claude de su ajuste2021–2023. Se conservaron fuente/hash y copia privada; no se materializaron etiquetas o reestimaron modelos desarrollados de otros años en esta prueba. La igualdad de las cifras recibidas y la reconstrucción algebraica no reproducen aquel ajuste desde sus datos originales. Este prior sigue condicionado y su incertidumbre no se incorpora en Z. La validación por grupos de2023, tanto aquí como en las tandas anteriores, tampoco es un backtest histórico prospectivo al inicio de2023.

Por componente frecuencia/severidad, tau² es el máximo entre cero y la media de diferencias cuadradas entre coeficientes emergentes/desarrollados menos sus varianzas, sobre categorías comparables con al menos100siniestros de ajuste, excluyendo región, intercepto y nuevo negocio. Z=tau²/(tau²+SE_em²). La combinación de coeficientes produce c=exp(theta_cred−theta_em). Tau usa coeficientes correlacionados y pocos positivos; no se interpreta como un intervalo bayesiano calibrado o prueba de transferencia a la cartera que llega en enero.

B15 aplica c solo a las tasas nuevas de B14; las renovaciones quedan exactamente iguales. El GLM B14 ya tiene nuevo negocio como efecto no penalizado. Esta es una variante experimental de aplicación directa del factor, no la adopción sin cambios de todo NB-CRED-01. No hay balance A/E, pesos optimizados o ajuste con el fold retenido. C0 de precios sigue idéntico para todas las recetas; la estacionalidad solo participa en los auxiliares, que usan un objetivo distinto de la devianza final. No se añaden reservas/IBNR o exposición dos veces.

| Ramo | c, rango entre folds | Z frecuencia | Z severidad |
| --- | ---: | ---: | ---: |
| motor | 0.681–0.777 | 0.100–0.503 | 0.000–0.004 |
| buildings | 0.684–1.348 | 0.016–0.131 | 0.000–0.001 |
| contents | 0.897–1.383 | 0.016–0.121 | 0.000–0.002 |

La variación de c refleja cuánto se corrige cada estimación emergente de ajuste; no es por sí sola variación de igual tamaño en la relatividad creíble final. La severidad recibe casi todo el peso del prior. Esto requiere conservar la incertidumbre de la fuente, aunque la aritmética y los errores robustos coincidan.

## Resultados con los mismos 50.094 periodos de 2023

Treinta mil ochocientos sesenta y nueve componentes, cinco folds guardados y el mismo T0/C0. Observado global15,297millonesCU y nuevo negocio1,528millones. D² Tweedie1,5 global sobre importes, no media de los ramos; A/E=observado/predicho.

| Receta | D² global | Predicho, millones CU | A/E global | D² nuevo negocio | A/E nuevo negocio |
| --- | ---: | ---: | ---: | ---: | ---: |
| W2-B00 | 0.068582 | 15.614 | 0.980 | 0.04783 | 1.550 |
| W2-B13 | 0.086712 | 15.430 | 0.991 | 0.11119 | 0.906 |
| W2-B14 | 0.086710 | 15.430 | 0.991 | 0.11117 | 0.906 |
| W2-B15 | 0.086061 | 15.088 | 1.014 | 0.10547 | 1.136 |

Capital mueve el D² global −0,00000163 y el total predicho unos−590CU. Su intervalo cruza cero: no hay mejora o equivalencia establecida por esta muestra. La credibilidad mueve D² −0,00064909 frente a B14, también con intervalo que cruza cero. Nuevo negocio pasa de A/E0,906 a1,136; el agregado cercano a uno no sustituye la lectura por ramo.

| Comparación | Delta D² | Intervalo exploratorio95% | Delta tras retirar31grupos favorables |
| --- | ---: | --- | ---: |
| W2-B14 / W2-B00 | 0.01812839 | [-0.00622581; 0.04266535] | -0.01250214 |
| W2-B15 / W2-B00 | 0.01747930 | [-0.00562290; 0.03989653] | -0.01078480 |
| W2-B14 / W2-B13 | -0.00000163 | [-0.00003090; 0.00002893] | -0.00005245 |
| W2-B15 / W2-B14 | -0.00064909 | [-0.00500418; 0.00263310] | -0.00230283 |

Se guardaron120parejas,2.000sorteos comunes por componente; se reconstruyeron separadamente las29nuevas. Son exploratorias después de16recetas adaptativas y de la investigación recibida, sin corrección por búsqueda o multiplicidad. No son el acta simultánea de2024. B14/B15 tampoco tienen mejora establecida sobre B00 y ambas diferencias se invierten con el retiro de sus31grupos favorables de evaluación, manteniendo modelos fijos.

| Nuevo negocio, D² por ramo | B13 | B14 | B15 |
| --- | ---: | ---: | ---: |
| motor_new_business | -0.01004 | -0.01004 | -0.03324 |
| buildings_new_business | 0.05022 | 0.05016 | 0.06336 |
| contents_new_business | 0.15363 | 0.15358 | 0.17445 |

La credibilidad mejora los puntos de hogar nuevo, pero empeora autos nuevos. En autos el A/E pasa de0,879 a1,223 y el D² de−0,01004 a−0,03324. En contenidos nuevos el A/E mejora de1,184 a1,052 y D² de0,15358 a0,17445. No se generaliza la mejora de un ramo al conjunto.

## Comprobaciones y decisiones

Pasaron25controles de revisión previa,26casos focales y832controles del [comprobador separado](../../../privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b/verifications/20261023T234646Z_f84baa76.json), con solapamiento. Este último no importa el productor ni ajusta modelos. Reconstruye la regla de capital, matrices auxiliares, score, sandwich agrupado con otro método de solución, tau/Z/c, transforms de precio, claves/ámbitos y replay con fit bloqueado. El máximo error absoluto de SE fue2,34e-15 y la condición máxima de sus matrices1382; el máximo score auxiliar medio fue8,09e-6, menor que1e-4 fijado antes. También coteja métricas/segmentos/escenarios e influencia y los29contrastes nuevos. Los escenarios conservan tasas fijas, no reestiman reservas o reportes.

El [informe completo](../../../privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b/report.json), [valoración](../../../privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b/assessment.json), [manifiesto](../../../privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b/manifest.json), [casos focales](../../../privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b/fixture_checks.json) y registro de decisiones conservan precisión y límites. Es revisión propia de Codex, no validación profesional independiente ni aprobación humana de la escala o transferencia.

Capital queda aplicado y probado solo en B14, con el riesgo material por fila abierto. Clima queda excluido del contrato prospectivo. B15 se conserva como alternativa creíble condicionada, sin mejora general demostrada; no se contradice la decisión referida del participante con una selección automática por score. El F0 global y sus históricos permanecen intactos. Se mantiene B00 y B01–B15, sin promoción, retiro, equivalencia o lista final congelada.

La continuidad nocturna retoma nivel/cola y vínculo de observación con modelos estándar, con receta previa para cualquier nuevo ensayo y sin ajustar c a posteriori por estos resultados. Quedan abiertos prior desarrollado no reproducido aquí, suficiencia de reservas/reporting, representatividad del negocio transferido y revisión humana.2024 sigue expresamente cerrado, sin ledger, precios/predicciones/scores de ese año o test; no envíos, remoto, publicación externa o delegación. Las [prácticas IAA](../../../../../Preparaci%C3%B3n/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md) se concretan en límites/segmentos, separación de revisiones y trazabilidad, sin certificación profesional.


## Corte posterior: explicación por fila y ablaciones de autos nuevos

La [séptima prueba](CAPITAL_POR_FILA_Y_AUTOS_NUEVOS_2023.md) conserva este corte y separa representación/refit del capital y componentes de credibilidad. El [snapshot v6](../../../registro/semana2_desarrollo2023_v6_snapshot.json) conserva exactamente este índice; el índice activo recoge el avance.
