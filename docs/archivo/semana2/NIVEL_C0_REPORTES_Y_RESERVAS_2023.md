# Nivel agregado, C0 y reservas en 2023

Codex. Corte UTC 2026-10-24T00:29:17.089471+00:00. Con los mismos modelos estándar, las reservas al 75% y al 125% cambian el nivel nominal condicionado de B14 en −2,484% y +2,483%. Al retirar de C0 un componente con alto coste tardío por ramo/fold, conservándolo en el ajuste de precios, el nominal baja 0,658%. Los puntos positivos del score de ese adverso se invierten al retirar sus 31 grupos de evaluación más favorables. No se adopta una exclusión ni un factor de reservas.

## Continuidad con la cola y registro previo

La [prueba de cola terminada](SENSIBILIDAD_COLA_Y_NIVEL_2023.md) ya demostró un límite: renormalizar la mezcla permite aumentar alrededor de 2,5% el nominal condicionado de 2023 con exactamente el mismo score observado. Se conserva esa evidencia, sin repetir sus ajustes o remuestreo. Aquí no se ensaya una combinación de cola y reservas ni se suman sus cambios como si fueran efectos independientes o límites estadísticos.

El [plan de C0 y reservas](../../../registro/semana2_c0_reservas2023_plan_v1.json) y el comentario COD-S2-20261024-025 preceden a la ejecución. Misma población: 50.094 periodos de 2023, 30.869 componentes cliente-dirección y cinco folds. B00 es constante por ramo; B12 usa constantes por ramo y negocio; B14 mantiene seis variables, Tweedie 1,5, enlace log y alpha0. La respuesta es T_s/e_s y el peso sqrt(e_s); la predicción observada multiplica e_s una vez. No hay nuevas variables, ajuste de credibilidad, clima, cambio de capital o calibración.

R075/R125 usan T_s=T0+(b−1)reserva con b=0,75/1,25 y sus enlaces de marcas de coste correspondientes, ya aprendidos en el ajuste propio de cada fold. Se mantienen las recuperaciones observadas. Cambiar el target cambia también la devianza nula: los D² de escenarios distintos no se comparan como un concurso sobre el mismo resultado.

L1 conserva T0. En cada ramo/fold se escoge dentro del ajuste el componente con mayor coste positivo de siniestros con demora superior a 365 días; el empate se resuelve por ID. Se retiran todas sus reclamaciones y sus exposiciones de la estimación de C0, se reestiman las mismas curvas de truncamiento inverso y se recalculan los pesos por peril. Todos los periodos originales siguen en el ajuste de precios, incluido ese componente. El retenido no aporta selección o estimación. Es una perturbación de la primera etapa, distinta del estrés anterior que retiraba grupos del ajuste de precios dejando C0 fijo. No es una limpieza de datos o reajuste integral del pipeline.

## Reservas y coste tardío de este corte

Los siniestros asignados de 2023 suman 15,297,103.84 CU netos y 1,427,914.85 CU de reserva, el 9.335% del neto. Se conciliaron neto=incurrido−recuperaciones y reserva=incurrido−pagado, en centavos. Los escenarios de respuesta suman 14.940125 y 15.654083 millones CU. Esto no confirma suficiencia de reservas o recuperaciones futuras.

| Ramo | Siniestros asignados | Reserva 2023, CU | Positivos con demora >365 días | Peso del coste tardío | Componentes distintos elegidos | Coste tardío retirado por fold, CU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| buildings | 519 | 290,510.88 | 2 | 0.25% | 2 | 7,329–7,582 |
| contents | 491 | 0.00 | 2 | 0.67% | 2 | 254–8,366 |
| motor | 3557 | 1,137,403.97 | 31 | 3.88% | 2 | 34,880–118,374 |

Los componentes pueden repetirse en varios folds: no se suman esos importes como costes únicos de cartera ni como experimentos independientes. Los identificadores y las filas permanecen privados. En contenidos, las reservas de estos periodos de 2023 son cero; R075/R125 no cambian su respuesta ni enlace y sus treinta modelos se reutilizan byte a byte. Esto no generaliza a otros años o a todo el ramo futuro.

## Sensibilidad del enlace y del nivel

Los cocientes siguientes usan solo las filas de validación de 2023, una vez cada una, y comparan su exposición efectiva con C0 base. Las reservas también cambian la marca de coste que pesa cada retraso. L1 puede cambiar el soporte y la normalización de las curvas; un incremento de completitud al perder observaciones no significa mayor conocimiento de la cola.

| Escenario | Ramo | Mínimo e_s/e_base | Mediana | Máximo |
| --- | --- | ---: | ---: | ---: |
| R075 | buildings | 0.999938 | 0.999993 | 1.000000 |
| R075 | contents | 1.000000 | 1.000000 | 1.000000 |
| R075 | motor | 0.999890 | 1.003212 | 1.010580 |
| R125 | buildings | 1.000000 | 1.000007 | 1.000060 |
| R125 | contents | 1.000000 | 1.000000 | 1.000000 |
| R125 | motor | 0.990147 | 0.997040 | 1.000101 |
| L1 | buildings | 1.000000 | 1.000310 | 1.002243 |
| L1 | contents | 0.999993 | 1.001233 | 1.010336 |
| L1 | motor | 0.999905 | 1.012627 | 1.032141 |

| Escenario | Modelo | Respuesta total, millones CU | D² bajo su target | A/E | Nominal condicionado2023, millones CU | Cambio nominal frente a su base |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| R075 | B00 | 14.9401 | 0.067813 | 0.980 | 15.3859 | -2.542% |
| R075 | B12 | 14.9401 | 0.073512 | 0.995 | 15.1599 | -2.471% |
| R075 | B14 | 14.9401 | 0.086749 | 0.991 | 15.2184 | -2.484% |
| R125 | B00 | 15.6541 | 0.069347 | 0.979 | 16.1887 | +2.543% |
| R125 | B12 | 15.6541 | 0.076249 | 0.996 | 15.9283 | +2.472% |
| R125 | B14 | 15.6541 | 0.086622 | 0.992 | 15.9936 | +2.483% |
| L1 | B00 | 15.2971 | 0.068832 | 0.980 | 15.6820 | -0.667% |
| L1 | B12 | 15.2971 | 0.074995 | 0.996 | 15.4413 | -0.661% |
| L1 | B14 | 15.2971 | 0.086782 | 0.992 | 15.5034 | -0.658% |

El nominal de B14 base es 15,606084 millones CU, frente a 15,218380 en R075, 15,993601 en R125 y 15,503358 en L1. Es exposición nominal de los mismos periodos de 2023 por su tasa bajo coste completo, no precio de 2025/test o etiqueta última. Un A/E agregado cercano a uno no acredita el supuesto de reservas o cola. Las pérdidas por ramo, fold y negocio se conservan en el anexo, sin ocultarlas con el promedio global.

## Comparaciones que sí comparten resultado

Solo se añadieron doce contrastes: tres entre familias dentro de cada escenario y tres L1 frente a sus padres sobre el mismo T0. Cada escenario tiene su propia nula y sus 2.000 sorteos comunes de componentes. No hay contrastes de superioridad entre targets R075/R125 y T0 base, ni repetición de las 171 parejas históricas o de la prueba de cola.

| Contraste | Delta D² | Intervalo exploratorio95% | Delta sin 31 grupos favorables |
| --- | ---: | --- | ---: |
| R075_W2-B12/R075_W2-B00 | +0.00569821 | [-0.00195762; +0.01696239] | -0.00703756 |
| R075_W2-B14/R075_W2-B00 | +0.01893561 | [-0.00518277; +0.04304545] | -0.01123839 |
| R075_W2-B14/R075_W2-B12 | +0.01323740 | [-0.00811359; +0.03304785] | -0.01146840 |
| R125_W2-B12/R125_W2-B00 | +0.00690236 | [-0.00221854; +0.01957358] | -0.00774130 |
| R125_W2-B14/R125_W2-B00 | +0.01727524 | [-0.00691202; +0.04191629] | -0.01390932 |
| R125_W2-B14/R125_W2-B12 | +0.01037288 | [-0.01134353; +0.03040261] | -0.01428307 |
| L1_W2-B12/L1_W2-B00 | +0.00616372 | [-0.00209005; +0.01801065] | -0.00737307 |
| L1_W2-B14/L1_W2-B00 | +0.01794979 | [-0.00627608; +0.04252444] | -0.01253231 |
| L1_W2-B14/L1_W2-B12 | +0.01178607 | [-0.00970973; +0.03168348] | -0.01284985 |
| L1_W2-B00/W2-B00 | +0.00025005 | [+0.00004816; +0.00059180] | -0.00004192 |
| L1_W2-B12/W2-B12 | +0.00008020 | [-0.00000000; +0.00020867] | -0.00004618 |
| L1_W2-B14/W2-B14 | +0.00007145 | [+0.00000100; +0.00017868] | -0.00004881 |

L1/B14 da +0,00007145, con intervalo exploratorio [+0,00000100; +0,00017868], y −0,00004881 tras retirar sus 31 componentes de evaluación más favorables. Lo mismo ocurre con el signo de las ventajas de L1/B00 y L1/B12. No se debe elegir una regla para eliminar información de reporte porque el punto observado mejore. La selección del componente de estrés se hizo dentro del ajuste; los grupos de influencia son un diagnóstico posterior de evaluación, no se borran ni se usan para volver a ajustar.

Las familias dentro de cada escenario se comparan bajo el mismo target/enlace. Sus intervalos siguen siendo exploratorios tras búsqueda adaptativa, sin corrección simultánea o confirmación temporal. No se promueven, retiran o declaran equivalentes alternativas ni se congela una lista final.

## Comprobación, autoría y condiciones

La ejecución completó 35 GLM nuevos, 105 constantes cerradas, 30 reutilizaciones exactas y 75 curvas de reporte nuevas, estas últimas separadas de los ajustes de precio. No hubo nuevos auxiliares de credibilidad. El contador propio queda en 135 ajustes de precio y 195 constantes; los 30 auxiliares anteriores conservan su contador separado. La ejecución terminó sin corrección de receta o reintento.

Pasaron 1477 controles separados, 48 adversos focales y 6 conciliaciones adicionales de la lectura, con solapamiento. El comprobador no importa el productor y bloquea fit. Recalcula el truncamiento como producto de probabilidades, las marcas por retraso, la completitud contando directamente días de cobertura admisibles, los pesos por peril y la exclusión de exposiciones/reclamaciones. Comprueba el óptimo de constantes por minimización escalar, parámetros/gradientes de GLM, imputación del ajuste, exp(X beta), centavos, ámbitos, métricas, segmentos y los doce remuestreos por multiplicidades. Los adversos prueban envenenamiento del retenido sin cambiar la selección, empates, frontera estricta de 365 días, ausencia de coste tardío sin fit, rechazo de 2024/test/duplicados y que costes/IDs no entren en la predicción. No se repitieron controles históricos sin cambios.

Se recibió CLA-S2-20261023-004 de Claude. Se conserva su autoría y se registraron las huellas de su informe/evidencia sin repetir sus 74 controles o adoptar cambios de variables dentro de esta receta. Su validación de datos no valida estos modelos, el último o una revisión profesional. La reserva del 17,8% que refiere sobre ambos años no sustituye el porcentaje de 2023 calculado arriba.

Sigue pendiente identificar severidad/masa fuera del soporte, estacionariedad, dependencia coste/reporte y adecuación de reservas. C0 aproxima una mezcla por ramo que puede variar según fila/negocio. La validación agrupada de 2023 al corte 2024-12-31 no representa información disponible al comienzo de 2023. Capital, clima y prior de credibilidad mantienen sus condiciones; no se cierran hallazgos ajenos. La siguiente unidad revisará esa aproximación de mezcla por peril y negocio antes de considerar precios más complejos, con receta previa si hay estimaciones nuevas, y preparará el balance nocturno.

B00 y B01–B18 se conservan; el catálogo principal queda exacto. Las nueve configuraciones de esta unidad son sensibilidad del mecanismo de observación y se registran aparte. 2024 permanece cerrado por instrucción directa, sin ledger, entrenamiento de precio, predicciones o scores de ese año o test. Sin remoto, envíos, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. Es revisión técnica propia de Codex, no profesional independiente.

## Evidencia

- [Resultados](../../../privado/semana2/desarrollo2023/mecanismo_20261024T002849Z_c8f124bf/report.json), [decisiones](../../../privado/semana2/desarrollo2023/mecanismo_20261024T002849Z_c8f124bf/decision_journal.json).
- [Comprobador separado](../../../privado/semana2/desarrollo2023/mecanismo_20261024T002849Z_c8f124bf/verifications/c0_20261024T003122Z_eb2e940d.json), [adversos](../../../privado/semana2/desarrollo2023/mecanismo_20261024T002849Z_c8f124bf/fixture_checks.json).
- [Perfil de reservas, demoras y enlace](../../../privado/semana2/desarrollo2023/mecanismo_20261024T002849Z_c8f124bf/diagnostics/claim_lag_reserve_profile.json).
- [Aporte de Claude recibido](../../../../Semana%202/Claude/validacion_datos_20261023/INFORME.md), [foro](../../../../Semana%202/Foro/FORO.md).


## Corte posterior: composición por negocio

La [prueba siguiente](MEZCLA_C0_PERIL_Y_NEGOCIO_2023.md) conserva esta sensibilidad y examina la mezcla por peril y negocio. El [snapshot del índice de reservas](../../../registro/semana2_sensibilidad_observacion_c0_reservas_v1_snapshot.json) mantiene este corte exacto.
