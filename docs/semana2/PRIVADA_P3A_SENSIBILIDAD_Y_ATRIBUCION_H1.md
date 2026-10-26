

## Privada P3a: precios congelados, reservas/cola y atribución del fallo, 26 de octubre de 2026

Codex, 2026-10-26T14:17:33.725591+00:00. Se mantuvieron los precios de último de la base S2y la media H1 exactamente iguales en los cuatro escenarios. Solo cambiaron las etiquetas declaradas y su observación mediante C0exterior protegido. No hubo recalibración, ajuste de curvas, inferencia fuente, precio2025oenvío nuevo.

| Escenario | Diferencia D² | IC95 por grupos | Post31 | Peor celda |
|---|---:|---:|---:|---:|
| RESERVE075 | +0.00117202 | [+0.00078805, +0.00153106] | +0.00075332 | -0.00110531 |
| RESERVE125 | +0.00109721 | [+0.00059466, +0.00164958] | +0.00036974 | -0.00048151 |
| TAIL005 | +0.00104242 | [+0.00054476, +0.00153268] | +0.00049335 | -0.00237758 |
| TAIL010 | +0.00101948 | [+0.00041896, +0.00158796] | +0.00044145 | -0.00420176 |

Las cuatro diferencias agregadas y sus intervalos simultáneos exploratorios son positivas. Persisten pérdidas superiores a0,001en autos nuevos2023con reservas75%y cola5%/10%. En ese año la diferencia total bajo cola5%es-0,00000022y bajo cola10%,-0,00007313; no se redondean a una mejora. La sensibilidad ponderada hacia2025es positiva en los cuatro casos, pero el ESSsigue siendo2,67%de filas y4,32%de grupos, frente al mínimo10%. Esos puntos no habilitan validación o rescatan los fallos sin pesos.

Se comprobaron900ramas de coste en90objetos C0por probabilidades de evento independientes. El mayor error relativo de marca fue4,44e-16y el de CDF8,88e-16. Se conciliaron exactamente los céntimos de periodos y siniestros, incluidas las dos etiquetas de reservas. La reconstrucción nominal coincidió con P2sin repetir sus estadísticas. Las funciones de aprendizaje estuvieron bloqueadas y las etiquetas retenidas alteradas no cambiaron la observación de precios.

El diagnóstico registrado para las48celdas descompone la diferencia de Tweedie en reparto relativo y arrepentimiento de escala. Para A=sum(y/sqrt(mu)), B=sum(sqrt(mu)) y C=sum(sqrt(y)), la pérdida observada es4A+4B-8C y el límite de mejor escala es8sqrt(AB)-8C. Ese límite y el multiplicador A/Busan respuestas retenidas: son oracles descriptivos, no precios, modelos candidatos, CVválida o parámetros transferibles. Se conservaron96escalares diagnósticos marcados como inadmisibles para predicción, fuera de los contadores de parámetros de precio.

| Autos nuevos 2023 | Diferencia observada | Reparto relativo, descriptivo | Escala, descriptiva |
|---|---:|---:|---:|
| RESERVE075 | -0.00110531 | -0.00208914 | +0.00098383 |
| TAIL005 | -0.00237758 | -0.00286877 | +0.00049120 |
| TAIL010 | -0.00420176 | -0.00368530 | -0.00051646 |

El reparto relativo aporta pérdida en esos tres casos, incluso después de descontar descriptivamente la mejor escala. Esto no identifica una causa causal, pero justifica comprobar una restricción de heterogeneidad antes de añadir capacidad o mover el nivel. La identidad reproduce las diferencias previas con error máximo2,56e-16. No hubo precios oracle, nuevas puntuaciones competitivas o bootstrap de esa descomposición.

Siguiente hipótesis: H3Bcon mezcla fuente por tipo de negocio, agregada desde f*sde las covariables de entrenamiento y congelada para el retenido. Reduce la dependencia de la observación respecto al perfil individual, manteniendo los mismos modelos, C0, etiquetas, folds y reglas cerradas. Se evaluará como una alternativa nueva y más simple, sin dar por probado que resuelva el fallo. Requiere receta, código, coste, controles y comentario previo. La recalibración de todo el objetivo bajo otra valoración no se ha hecho; no se confundirá con esta robustez de precios congelados.

H1sigue diferido. B00, F3c y todas las alternativas/fallos se conservan;2024abierto adaptativo. Estos resultados locales condicionados a S2no prueban el F3c recibido, un holdout intacto o la mejora privada. Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/sensibilidad_congelada_media_H1_20261026_v1/report.json y Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/atribucion_error_P3a_H1_20261026_v1/report.json.
