Codex. Resultado de COD-S2-20261024-020, respuesta a019. [Informe por fila y autos nuevos](../../Repositorio_IAA2026/docs/semana2/CAPITAL_POR_FILA_Y_AUTOS_NUEVOS_2023.md), [decisiones](../../Repositorio_IAA2026/privado/semana2/desarrollo2023/dev7_20261023T235935Z_55507793/decision_journal.json).

Las 56 filas de capital corregido están dentro del rango normal de su ajuste. Se separó con B13 congelado el cambio de dato del reajuste B14: casi todo el movimiento (−62,36% a +154,09%) lo explica sustituir el capital imputado por el propio dividido; el reajuste aporta como máximo 0,157%/0,272% en escala log. Identidad verificada fila a fila, no una deducción del total. Todos T0=0: no confirma la escala económica. Se conservan B13/B14, la decisión CAPS2-01 y sus condiciones, sin retocar capital o F0 para ganar score.

En autos nuevos B15/B14 aumenta la pérdida 34.727,49 en 265 filas positivas y la baja 27.119,35 en 2.355 ceros; saldo adverso 7.608,15. Fold0 aporta 8.637,79. Los cinco grupos más perjudicados suman 18.085,65, compensados por otros; no se eliminan. Severidad domina el corrector. El coeficiente de negocio de precio difiere del auxiliar, por lo que multiplicar c no lo sustituye por theta_creíble. No se declara causalidad única ni error aritmético.

Se probaron las tres recetas previstas, solo2023, sin nuevos ajustes: B16 frecuencia sola, B17 severidad sola, B18 sustitución explícita del coeficiente. Hogar y renovaciones exactos B14. B15 tiene cambios de hogar también: su comparación global con estas ablaciones no aísla autos.

| Receta | D² global | A/E global | D² autos nuevos | A/E autos nuevos | Predicho autos nuevos, millones CU |
| --- | ---: | ---: | ---: | ---: | ---: |
| B00 | 0.068582 | 0.980 | -0.130134 | 2.006 | 0.543 |
| B14 | 0.086710 | 0.991 | -0.010045 | 0.879 | 1.238 |
| B15 | 0.086061 | 1.014 | -0.033244 | 1.223 | 0.890 |
| B16 | 0.086551 | 0.995 | -0.012726 | 0.919 | 1.184 |
| B17 | 0.085750 | 1.012 | -0.026267 | 1.170 | 0.931 |
| B18 | 0.081896 | 1.033 | -0.091376 | 1.752 | 0.621 |

| Comparación global | Delta D² | Intervalo exploratorio95% | Delta retirando31 grupos favorables |
| --- | ---: | --- | ---: |
| B16/B14 | -0.00015868 | [-0.00092851; +0.00030689] | -0.00019211 |
| B17/B14 | -0.00096016 | [-0.00437606; +0.00154672] | -0.00111190 |
| B18/B14 | -0.00481377 | [-0.01341707; +0.00158824] | -0.00513303 |

Ninguna corrección acredita mejora; los tres puntos son peores y los intervalos cruzan cero. B16 acerca A/E a uno pero empeora D². Sustituir el coeficiente empeora más: la diferencia detectada no se convierte por sí sola en arreglo. B18 conserva el intercepto en la representación original y las renovaciones exactas; no se confunde con congelar el intercepto numérico después de absorber el cambio en una variable estandarizada. No se elige otro peso a posteriori. Las16 OOF anteriores/120parejas siguen exactas; solo se calcularon51 parejas nuevas con2.000sorteos comunes.19recetas adaptativas/171contrastes exploratorios, sin promoción, retiro, equivalencia o lista final.

Pasaron31adversos focales,622controles separados y18conciliaciones adicionales, con solapamiento. Se bloqueó fit y se reconstruyeron exp(X beta), escala binaria, capital, factores, métricas y51remuestreos por multiplicidades, con influencia/segmentos/escenarios. Cero nuevos estimadores o calibraciones; quince factores algebraicos y treinta copias hogar;90ajustes de precio/60constantes históricos intactos,30auxiliaresv6 reutilizados. Es revisión técnica propia, no profesional independiente.

Prior desarrollado recibido y no reproducido aquí, incertidumbre omitida enZ, objetivos auxiliares/precio distintos, reporte/reservas/último y soporte conjunto siguen condicionados. Clima propuesto continúa excluido prospectivamente. Se mantienen B00 yB01–B18. La continuidad nocturna retoma nivel/cola/C0 con nueva receta previa, sin retocar c por estos resultados.2024 cerrado por instrucción directa, ledger ausente; sin precios/predicciones/scores de ese año o test, envíos, remoto, publicación externa o delegación. Se respetan autorías y estados de hallazgos ajenos.
