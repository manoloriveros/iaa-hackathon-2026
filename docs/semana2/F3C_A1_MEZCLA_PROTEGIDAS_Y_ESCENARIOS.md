# A1 y mezcla protegidas: factores y escenarios de F3c

Reúno aquí las comprobaciones de la transferencia y la mezcla que alimentan mi entrega. Me interesa dejar claro qué se aisló en el cálculo y qué límites mantengo al interpretar los resultados.

Codex, 27 de octubre de 2026. Trabajo solicitado como continuación de la corrección de T2b. Las recetas históricas proceden de Claude; la corrección, el código de esta corrida y sus comprobaciones son de Codex. Mantengo F3c de producción, las referencias, la selección, el informe final y el guion. La comparación evalúa las recetas reaprendidas con 2023 y aplicadas a las 59.202 filas de 2024. Es una revisión propia de IA; 2024 conserva su carácter adaptativo.

La separación computacional ya está comprobada en las tres vistas históricas: T2b, A1 y mezcla fija de 50/50. A1 se rehízo desde sus curvas y árboles por ámbito; T2b conserva los objetos protegidos del padre por SHA. Las pruebas que alteran costes de 2024 y del fold retenido de 2023 dejan iguales sus argumentos, modelos, parámetros y precios pertinentes. Esta conclusión se refiere a la implementación nueva y a sus ámbitos. La disponibilidad real al cotizar y el coste último no quedan acreditados por esas igualdades.

## Comparación con y sin factores propios

| Base corregida | D² sin factores propios | D² con factores propios | Diferencia | Banda condicional familia 6 |
| --- | ---: | ---: | ---: | --- |
| T2b | 0,1233249 | 0,1256566 | +0,0023317 | [+0,0005769; +0,0042488] |
| A1 | 0,1209231 | 0,1233549 | +0,0024318 | [+0,0007219; +0,0042858] |
| mezcla | 0,1235341 | 0,1259002 | +0,0023662 | [+0,0006577; +0,0042339] |

El bloque propio mantiene género en autos/contenidos y teletrabajo/marketing en contenidos, K=300 y la secuencia fijada. La referencia conserva F2 de NCB y siniestros previos y la forma común de autos renovación. En cada vista se aprenden esos pasos con bases OOF de 2023; sus niveles y normalizadores quedan fijos al aplicar 2024. No se usan exponentes, A_M1 o niveles públicos. Conservo decisiones históricas de esquema y la forma 0,9; la nueva corrida no deshace la adaptación que las originó.

El margen global sigue siendo 0,0005, la salvaguarda de negocio nuevo exige diferencia no negativa y límite inferior del IC95 ≥ −0,001, y el piso puntual de autos nuevo sigue en −0,001. La influencia retira max(5, ceil(0,001×G)) grupos favorables. La tabla presenta los resultados sin cambiar esas reglas.

| Vista | Margen global | Protección NB | Diferencia autos NB | Diferencia después de retirar 37 grupos |
| --- | --- | --- | ---: | ---: |
| T2b | Pasa | No pasa | -0,0012241 | -0,0000129 |
| A1 | Pasa | No pasa | -0,0008807 | +0,0001283 |
| mezcla | Pasa | No pasa | -0,0010275 | +0,0000575 |

| Vista | Diferencia NB | IC95 condicional NB | Renovación: contribución al cambio neto de desviación |
| --- | ---: | --- | ---: |
| T2b | +0,0001148 | [-0,0037029; +0,0039767] | 99,39 % |
| A1 | +0,0003727 | [-0,0029973; +0,0039208] | 98,09 % |
| mezcla | +0,0002661 | [-0,0032702; +0,0039336] | 98,60 % |

Las participaciones de renovación usan contribuciones de desviación sobre el mismo total. Los D² de segmentos tienen su propio nulo y no se suman. Las tres vistas comparten las etiquetas de 2024 y los mismos componentes; no son tres confirmaciones independientes. Ninguna vista se selecciona por dar el resultado mayor.

NB conserva la definición contractual de primer año de póliza con la aseguradora. No implica por sí sola dirección o componente cliente–dirección nunca vistos. Las renovaciones pueden compartir entidades entre 2023 y 2024; el corte temporal y el aislamiento de folds tienen propósitos diferentes.

## Protección aplicada a A1 y a la mezcla

A1 estima su curva de reporte con el pool permitido de ambos mercados. Para cada uno de los cinco folds emergentes de 2023 se retiran sus siniestros antes de capar costes, estimar RKM y entrenar los árboles fuente. Se prepara también el ámbito completo de 2023 para aplicar 2024. Dentro de cada ámbito, la selección de rondas del desarrollado excluye su fold interno de curvas, participaciones, vocabularios y constante inicial. El reajuste completo usa las rondas elegidas y sus objetos propios de entrenamiento.

Mantengo el esquema de la rama A1 de confirmación: 49, 41 y 42 entradas, semilla 11, tasa de aprendizaje 0,02 y los parámetros fijos registrados. Se corrige ID01, se excluye make_model en autos y no se añade F1 o clima a esa rama. La producción A1 con F1 y tres semillas conserva sus objetos históricos. Esta evaluación temporal no la presenta como una reconstrucción OOF del archivo de producción.

La exposición A1 redondeada a cuatro decimales entra una sola vez en el offset; la integración diaria de reporte se concilia con ella. El cociente de completitud puede superar ligeramente uno por esa convención de exposición y no se interpreta como probabilidad de un evento. Las curvas de coste y de número permanecen separadas.

La mezcla conserva 50/50 en tasas anuales. Su base observada combina las dos bases observadas con esos pesos; el vínculo efectivo se obtiene de esa base y de la tasa anual mixta, sin aprender con etiquetas retenidas. Ambos candidatos de cada vista comparten su vínculo. Los factores y niveles se reaprenden dentro de la vista, con la misma receta fija. Se comprueba además que T2b reproduce los precios del padre dentro de la tolerancia registrada.

Se completaron 48 ajustes nativos de A1: 36 para los seis ámbitos y doce para repetir adversos de año y fold. No se volvió a entrenar T2b ni se produjeron predicciones nuevas de 2025. Las pruebas de membresía literal por row_id cotejan los filtros de ámbitos antes de estimar la curva, además del caso matemático de riesgo inverso enumerado a mano. Los T0 de evaluación coinciden con el objetivo canónico por céntimo.

## Composición de 2025

| Vista | Diferencia reponderada | IC95 condicional |
| --- | ---: | --- |
| T2b | +0,0009587 | [-0,0029745; +0,0047722] |
| A1 | +0,0010299 | [-0,0028403; +0,0047931] |
| mezcla | +0,0009923 | [-0,0029018; +0,0047583] |

Se usan los mismos pesos por ramo, negocio y banda de exposición del análisis previo, fijados antes de abrir los scores nuevos de A1 y mezcla. Las covariables futuras solo intervienen en este diagnóstico. La reponderación no identifica el rendimiento futuro, la cola invisible o cambios de composición dentro de las celdas.

## Escenarios de la receta corregida

Se repiten 45 tensiones de reservas, severidad reportada tarde y cola, y cinco de completitud. Se distinguen precios baseline fijos frente al objetivo estresado y receta destino reaprendida con 2023. En la segunda se recalculan participaciones por peligro, exposición, niveles OOF, F2, factores propios y nivel final. Los árboles y curvas fuente de cada ámbito quedan congelados en su baseline. Es sensibilidad condicional; no se reentrena la fuente bajo cada valoración alternativa ni se transforma un escenario en un intervalo de confianza.

Los cuatro escenarios de diseño de la política se muestran con reaprendizaje de destino. La cola de 5/10 % añade coste de diseño en lesiones corporales y hundimiento; no es IBNR observado ni una probabilidad estimada.

| Escenario | Δ T2b | Δ A1 | Δ mezcla |
| --- | ---: | ---: | ---: |
| reserve075 | +0,0022239 | +0,0023271 | +0,0022596 |
| reserve125 | +0,0024312 | +0,0025285 | +0,0024647 |
| BI_subsidence_cost_tail_0.05 | +0,0023682 | +0,0024729 | +0,0024045 |
| BI_subsidence_cost_tail_0.1 | +0,0024042 | +0,0025134 | +0,0024422 |

El conjunto completo se resume sin ocultar escenarios adversos. Un conteo de resultados positivos no representa ensayos independientes ni probabilidad de ganar.

La diferencia global mantiene signo positivo en los 50 escenarios de cada vista, tanto con precios fijos como con destino reaprendido. Este resultado favorable es condicional a los ancestros fuente congelados.

| Vista | Tratamiento | Escenarios negativos de coste/reserva | Peor Δ | Escenarios negativos de completitud | Peor Δ |
| --- | --- | ---: | ---: | ---: | ---: |
| T2b | Precios fijos | 0/45 | +0,0022126 | 0/5 | +0,0023317 |
| T2b | Destino reaprendido | 0/45 | +0,0021804 | 0/5 | +0,0023264 |
| A1 | Precios fijos | 0/45 | +0,0022884 | 0/5 | +0,0024318 |
| A1 | Destino reaprendido | 0/45 | +0,0022443 | 0/5 | +0,0024247 |
| mezcla | Precios fijos | 0/45 | +0,0022412 | 0/5 | +0,0023662 |
| mezcla | Destino reaprendido | 0/45 | +0,0022017 | 0/5 | +0,0023608 |

`cost_curve_train_peril_mix` recupera el baseline de cada vista dentro de tolerancia, como control de identidad. La alternativa de número cambia el vínculo de observación; no convierte estos árboles de coste en un modelo de frecuencia identificado. Las tensiones de severidad no reportada modifican F/(F+s(1−F)) como supuesto determinista. El efecto sobre precios corresponde a periodos históricos de 2024, sin nuevas primas 2025 o recalibración del tablero.

## Qué cambia y qué sigue abierto

Se cierra el trabajo computacional que faltaba en A1 y en la mezcla para estas vistas de validación histórica: sus ancestros propios excluyen el retenido, y la mezcla compone dos ramas verificadas. También quedan ejecutados los 50 escenarios sobre las recetas destino corregidas. Los informes anteriores y sus fallos se conservan como evidencia de la implementación histórica.

La ganancia, el soporte de negocio nuevo y la concentración se juzgan por las tablas nuevas. Un margen global favorable no borra un fallo de NB, autos nuevo o influencia. Los escenarios condicionales tampoco cierran el refit completo de fuente frente a reservas o demoras alternativas. F3c permanece declarada; no se emite una promoción formal nueva ni se sustituye una alternativa.

En esta corrida, el margen global pasa en las tres vistas y la protección de negocio nuevo falla en las tres. A1 pasa el piso puntual de autos nuevo y la retirada de 37 grupos; la mezcla pasa la retirada, pero autos nuevo queda en -0,0010275, por debajo de −0,001. Es una diferencia respecto de T2b, donde ambos controles fallan. La concentración sigue siendo frágil: la retirada retrospectiva que alcanza la anulación es de 42 grupos en A1 y 39 en la mezcla, entre 36.408. Ninguna de las tres reponderaciones de 2025 separa su mejora de cero al 95 %.

Continúan abiertos la adaptación de 2024, los intervalos condicionados a modelos aprendidos, la escasez de soporte de nuevo negocio de hogar, la estabilidad de factores entre años, los maestros y accesos fechados al cotizar, el vintage climático, la duración inicialmente contratada y la contingencia operativa. Pasar un piso puntual en 2024 no acredita estabilidad entre años. Los importes/estados se valoran al cierre de 2024: no se reconstruyen snapshots que faltan de 2023. La suficiencia de reservas y el último requieren evolución posterior real; los escenarios sin probabilidades no validan el beneficio objetivo del 8 %. También sigue pendiente la revisión profesional por otra persona.

Las prácticas IAA se usan como guía de alcance y límites (consideraciones profesionales §3.1), sesgos/poblaciones §3.3, revisión propia e independiente (gobernanza §2.8) y sensibilidad/retirada §§3.3.2–3.6. El expediente no constituye certificación.

## Evidencia y reproducción

Código: `herramientas/ampliar_validacion_cadena_f3c.py`, `revisar_ampliacion_f3c.py`, `composicion_ampliacion_f3c.py` y este generador. Plan, congelado, extensión de composición, fuentes SHA, preparación, modelos por ámbito, intentos, parámetros, precios históricos, bootstrap, 50 paquetes de escenarios y verificaciones están en `privado/validacion_cadena_f3c_A1_mezcla/20261027T175434Z/`, relativo al repositorio. Datos por fila, modelos y precios permanecen privados.

Los controles de métricas se cotejan con scikit-learn y veinte sorteos de cada vista se reconstruyen por separado. Error máximo de métricas baseline 2.22e-16; de bootstrap 1.67e-15; de métricas globales de escenarios 4.44e-16. Estos cotejos verifican aritmética, sin añadir observaciones independientes. F3c, PDF y guion conservan sus huellas. No hubo API, envío, publicación o entrenamiento remoto.
