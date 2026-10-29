

## Privada H3B: la mezcla agregada por negocio pierde frente a H1, 26 de octubre de 2026

Codex, 2026-10-26T14:43:17.468319+00:00. Se terminó la receta preinscrita H3B en los 75 ámbitos anidados. La mezcla de periles se calculó por nuevo negocio/renovación con f_period*s de las covariables de entrenamiento de cada miembro. La frecuencia ya incluye el periodo: no se multiplicó otra vez por exposición. Se conservaron T0, los folds, C0 y los denominadores G3 de P2. El coste último se promedió entre cinco miembros antes de aplicar la observación exterior protegida.

| Contraste | Diferencia D² | IC95 por grupos | Post31 | Peor celda |
|---|---:|---:|---:|---:|
| NOMINAL_VS_BASE | +0.00005620 | [-0.00026336, +0.00035635] | -0.00030648 | -0.00064612 |
| NOMINAL_VS_H1 | -0.00098227 | [-0.00161532, -0.00042348] | -0.00160184 | -0.01122617 |
| RESERVE075 | +0.00023791 | [-0.00009029, +0.00055089] | -0.00008797 | -0.00064549 |
| RESERVE125 | +0.00006960 | [-0.00021576, +0.00035489] | -0.00033347 | -0.00189537 |
| TAIL005 | +0.00002864 | [-0.00028243, +0.00031545] | -0.00024477 | -0.00082066 |
| TAIL010 | -0.00002127 | [-0.00032397, +0.00025759] | -0.00020973 | -0.00103385 |

H3B pierde frente a H1 en los cinco folds. La diferencia agregada es -0,00098227, con intervalo simultáneo exploratorio de seis contrastes [-0,00189433, -0,00027593]. La pérdida se concentra en 2024 y alcanza -0,01122617 en autos nuevos de ese año. Frente a S2 la mejora nominal es pequeña e incierta; falla el mínimo 0,002, el límite inferior, la consistencia de folds/años y Post31. Bajo reservas125 y cola10 también falla el suelo de celdas. Se preserva como resultado adverso, sin promoción o eliminación de candidatos. No se buscará un peso entre H1 y H3B para rescatar el resultado. El fallo de H3B tampoco prueba la robustez privada de H1.

Los 75 controles reales volvieron a calcular el aprendizaje nuevo con costes y reservas retenidos alterados, y perfiles fuente retenidos multiplicados por 1e8. Mezclas, artefactos y precios de último coincidieron exactamente. Esto verifica el aprendizaje nuevo de H3B; las curvas heredadas no se reajustaron y su validación de P2 conserva su alcance original. El mayor error relativo del puente es 1.33e-15. El flujo sintético de los tres ramos, el momento de Tweedie por otra suma, la media y la métrica también quedaron comprobados en los recibos de ejecución. Se conservan los SHA de fuentes y código.

Se registran 75 aprendices cerrados y 1775 constantes de precio primarias; otros tantos controles adversos se cuentan aparte. Las 150 mezclas de entrenamiento y 30 exteriores son resúmenes de covariables, separados de los parámetros de precio y de los normalizadores. Hubo cero ajustes C0, modelos fuente, inferencias fuente, precios 2025 o envíos nuevos.

La evaluación sigue condicionada al núcleo S2, a modelos fuente congelados y a muestras de miembro del 64% frente al 80% de producción. 2023 y 2024 ya son exploratorios tras búsqueda adaptativa. El escaso soporte de los pesos hacia la cartera 2025 sigue sin resolverse. No equivale a reproducción completa del F3c recibido, validación profesional independiente o evidencia de mejora privada.

Siguiente paso: revisar únicamente las recetas y recibos temporales ya existentes para identificar si queda un mecanismo de calendario o disponibilidad que justifique una prueba distinta. No se repetirán E13, T7, E27 ni diagnósticos terminados por cambiarles el nombre. B00, F3c y todas las alternativas se conservan; 2024 permanece abierto y la entrega H1 diferida.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/H3B_mezcla_negocio_20261026_v1/report.json; receta Hackaton/Repositorio_IAA2026/registro/semana2_H3B_mezcla_negocio_plan_v1.json.
