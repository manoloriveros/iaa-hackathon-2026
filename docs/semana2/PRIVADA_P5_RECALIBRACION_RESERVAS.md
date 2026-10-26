

## Privada P5: recalibración completa de precios emergentes bajo reservas75/125, 26 de octubre de 2026

Codex, 2026-10-26T15:12:55.657179+00:00. Se completaron los 180 ámbitos de los dos escenarios y su replay con ajustes bloqueados. En cada escenario cambiaron tanto las etiquetas de entrenamiento como el enlace de observación correspondiente. Se aprendieron nuevamente las formas de NCB/previos, niveles por negocio, factores residuales, base S2 y cinco miembros G3/H1. El resultado no es una aplicación de un multiplicador a precios nominales. Se conservaron folds, grupos, reglas de credibilidad, fuentes y pesos fijos del algoritmo.

| Contraste | Diferencia D² | IC95 por grupos | Post31 | Peor celda |
|---|---:|---:|---:|---:|
| RESERVE075 | +0.00112276 | [+0.00073158, +0.00148760] | +0.00064046 | -0.00005506 |
| RESERVE125 | +0.00101494 | [+0.00050795, +0.00153803] | +0.00037693 | -0.00163690 |
| RESERVE075_VS_FROZEN | +0.00009957 | [-0.00087390, +0.00092595] | +0.00005940 | -0.01197276 |
| RESERVE125_VS_FROZEN | +0.00049015 | [-0.00031114, +0.00139093] | -0.00120832 | -0.00226717 |

Ambos primarios, frente a sus propias bases recalibradas, mantienen intervalos agregados positivos, también con la corrección exploratoria de cuatro contrastes. Ambos años y los cinco folds aportan ganancia. Los dos escenarios siguen por debajo del mínimo histórico 0,002. Con reservas125 persiste una pérdida de -0,00163690 en autos nuevos de 2023, superior al suelo admitido. Ese fallo se conserva aunque el agregado sea favorable.

Los secundarios comparan cada candidato recalibrado con los precios nominales congelados observados bajo ese mismo escenario en P3a. Sus intervalos incluyen cero. Con reservas125, la ganancia secundaria se vuelve negativa después de descontar los 31 grupos más favorables. La recalibración no queda establecida como mejora sobre mantener los precios congelados y muestra pérdidas locales. No se escogerá una valoración por su score ni se cambiará el objetivo nominal de producción.

| Contraste con pérdida superior a0,001 | Celda | Diferencia de celda |
|---|---|---:|
| RESERVE125 | motor, 2023, nuevo | -0.00163690 |
| RESERVE075_VS_FROZEN | buildings, 2023, renovación | -0.00189702 |
| RESERVE075_VS_FROZEN | buildings, 2023, nuevo | -0.00170893 |
| RESERVE075_VS_FROZEN | contents, 2024, nuevo | -0.00122072 |
| RESERVE075_VS_FROZEN | motor, 2023, nuevo | -0.01197276 |
| RESERVE125_VS_FROZEN | buildings, 2024, renovación | -0.00174385 |
| RESERVE125_VS_FROZEN | buildings, 2024, nuevo | -0.00226717 |
| RESERVE125_VS_FROZEN | motor, 2023, renovación | -0.00133949 |

Esta es una recalibración completa del precio emergente condicionada a fuentes fijas. Los modelos fuente y sus perfiles de periles no se revaloraron. Se usaron las ramas de coste protegidas que ya se habían comprobado por probabilidades de evento en P3a; las distribuciones de conteo y sus frecuencias no cambian con la marca de reserva. Por eso no se ajustaron curvas otra vez ni se repitió esa auditoría. La cola hipotética tampoco se presentó como un modelo conjunto de frecuencia y severidad identificado.

Los 390 aprendices cerrados primarios produjeron 9230 constantes de precio; los 390 controles adversos se cuentan aparte. Todos los artefactos y precios de último coincidieron exactamente al alterar T0 y reservas retenidos. El replay de los 180 ámbitos bloqueó nueve entradas de ajuste y recuperó los mismos precios con etiquetas corruptas, sin añadir eventos de aprendizaje. Se cotejaron momentos por suma escalar, puente de observación, media, métricas y etiquetas oficiales por clave. Los SHA registrados antes de ajustar permanecieron iguales. Los 54 aprendices sintéticos y los normalizadores se registran separados. Hubo cero C0, modelos fuente, inferencias fuente, precios 2025, CSV o envíos nuevos.

La evidencia sigue siendo exploratoria sobre 2023/2024 inspeccionados y sobre S2, un núcleo completo factible distinto del F3c recibido. El soporte ponderado hacia 2025 continúa siendo insuficiente; el mercado desarrollado no añade soporte emergente. Estos controles no identifican la reserva verdadera o la cola tardía, restauran disponibilidad histórica de los maestros o acreditan mejora privada.

Decisión: conservar objetivo nominal, B00, F3c, H1 y todas las alternativas/fallos. 2024 permanece abierto para desarrollo adaptativo. H1 no se promueve y su entrega sigue diferida. P5 no borra el fallo previo del precio congelado en autos nuevos, ni sustituye el resultado anual favorable de P4 por una aprobación general. El siguiente paso es preparar un productor nominal que coincida con el algoritmo S2/H1 realmente evaluado. Antes de ajustar o predecir, se conciliarán las cachés de entrenamiento completo y entradas futuras existentes para evitar repeticiones, y se registrará solo lo que falte.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P5_recalibracion_reservas_H1_20261026_v1/report.json; replay Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P5_recalibracion_reservas_H1_20261026_v1/replay_report.json.
