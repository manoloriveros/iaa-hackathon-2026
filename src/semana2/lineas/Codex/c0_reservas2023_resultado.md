Codex. Resultado de 025: nivel, cola, reportes tardíos y reservas solo en 2023, con modelos estándar. [Informe](../../Repositorio_IAA2026/docs/semana2/NIVEL_C0_REPORTES_Y_RESERVAS_2023.md), [decisiones](../../Repositorio_IAA2026/privado/semana2/desarrollo2023/mecanismo_20261024T002849Z_c8f124bf/decision_journal.json).

La prueba de cola de 024 se conserva sin repetirla: otro nominal condicionado con el mismo score observado, sin identificación del último. Aquí R075/R125 cambian tanto T0+(b−1)reserva como el C0 de marcas y pesos por peril. L1 mantiene T0 y retira de la estimación de C0 el componente de ajuste con mayor coste reportado después de 365 días, por ramo y fold. Se retiran sus reclamaciones y exposición de C0, pero se mantienen todos sus periodos en el ajuste de precios. No se propone limpiar siniestros caros.

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

B14 pasa de un nominal base de 15,606084 millones CU a 15,218380/15,993601 con reservas al 75%/125% (−2,484%/+2,483%), y a 15,503358 en L1 (−0,658%). Es exposición de esos mismos periodos de 2023 por su tasa bajo coste completo, no precios de 2025/test o una etiqueta última. La reserva de 2023 es 1.427.914,85 CU, el 9,335% del neto de 15.297.103,84 CU; el 17,8% referido por Claude abarca ambos años. En contenidos de 2023 la reserva es cero: treinta copias exactas en los dos escenarios, sin reajuste redundante.

Se calcularon doce contrastes nuevos con 2.000 sorteos comunes y devianza nula propia de cada target: tres comparaciones entre familias dentro de cada escenario, más L1 frente a sus padres sobre T0. No se comparan D² de targets distintos como superioridad. L1/B14 da delta +0,00007145 e intervalo exploratorio 95% [+0,00000100; +0,00017868], pero cambia a −0,00004881 al retirar 31 grupos favorables; L1/B00 y L1/B12 también invierten su signo. Son diagnósticos de evaluación, no grupos eliminados o usados para retocar precios. Las comparaciones completas están en el informe. No hay promoción, retiro, equivalencia, lista final o adopción de reserva/curva por un punto.

Se completaron 35 GLM y 105 constantes nuevos, 30 reutilizaciones exactas y 75 curvas de reporte separadas; cero auxiliares nuevos. El contador propio queda en 135 ajustes de precio y 195 constantes, con 30 auxiliares previos aparte. Pasaron 1.477 controles separados, 48 adversos y seis conciliaciones adicionales, con solapamiento. Se reconstruyeron C0 por producto de probabilidades y días admisibles, marcas y centavos, óptimos y gradientes, exp(X beta), fuentes y ámbitos, segmentos y los doce remuestreos por multiplicidades. Replay sin fit; sin reintento o cambio de receta. Es revisión técnica propia, no profesional independiente.

Recibí CLA-S2-20261023-004 y registré sus fuentes y autoría sin repetir sus 74 controles o adoptar propuestas en esta receta. Su revisión de datos no valida este modelo o el último. Siguen abiertas la masa y severidad fuera de soporte, las reservas, la dependencia entre coste y reporte, la estacionariedad y la aproximación por ramo. Los escenarios separados no son cotas estadísticas o efectos aditivos. La siguiente unidad revisará la mezcla por peril y negocio antes de añadir complejidad, con receta previa, y preparará el balance nocturno.

B00 y B01–B18 permanecen intactos, con catálogo principal exacto y sensibilidades en un índice aparte. 2024 sigue cerrado expresamente, sin ledger, precios, predicciones o scores de ese año o test. Sin envíos, remoto, publicación externa, nuevos chats o delegación. Las otras automatizaciones permanecen intactas.
