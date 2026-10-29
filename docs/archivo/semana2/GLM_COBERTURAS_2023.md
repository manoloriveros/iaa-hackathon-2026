# GLM sencillo con coberturas como efectos principales

Codex, corte UTC 2026-10-24T01:36:31.346935+00:00. B19 añade un campo de cobertura a B14 y mantiene exactamente T0, C0 y las particiones de 2023. La receta se publicó antes del ajuste en el comentario 034. Terminaron quince GLM, sin retocar parámetros o volver a ajustar las referencias.

## Resultado observado

El D² global baja de **0,086710** en B14 a **0,082470** en B19. B00 conserva **0,068582**. El ajuste de entrenamiento mejora en los quince nodos respecto a B14, pero esa ganancia no se sostiene en el OOF global. No se promueve B19 ni se retira: B00 y todas las alternativas permanecen.

| Ramo | D² B14 | D² B19 | Cambio dentro del ramo |
| --- | ---: | ---: | ---: |
| Autos | 0.033101 | 0.033722 | +0.000621 |
| Edificios | 0.021094 | 0.008352 | -0.012743 |
| Contenidos | 0.037343 | 0.036281 | -0.001061 |

Edificios concentra el deterioro; contenidos también pierde. Autos mejora ligeramente agregado, con deterioro en nuevo negocio. Las contribuciones al cambio global se calculan con la misma desviancia nula global; no se promedian D² de ramos.

| Ramo | Negocio | D² B14 | D² B19 |
| --- | --- | ---: | ---: |
| Autos | Nuevo | -0.010045 | -0.031822 |
| Autos | Renovación | 0.039794 | 0.044035 |
| Edificios | Nuevo | 0.050163 | 0.048378 |
| Edificios | Renovación | 0.011464 | -0.002416 |
| Contenidos | Nuevo | 0.153579 | 0.151995 |
| Contenidos | Renovación | 0.020962 | 0.019948 |

Las tablas por cobertura conservan los resultados adversos: en autos third_party_only el D² pasa de −0,015892 a −0,042793. En edificios con cobertura accidental activa, el A/E se acerca a uno (1,076 a 1,010), mientras el D² empeora (−0,008318 a −0,029774). Una mejor conciliación del total no establece mejor predicción por fila. Son perfiles descriptivos, sin intervalos propios de cada celda ni pruebas nuevas de superioridad por segmento.

## La receta probada

Cada ramo usa las seis variables originales de B14 más cover_type en autos o accidental_damage_cover en hogar. No hay interacciones ni restricciones de coste cero. En hogar se conservan los treinta siniestros positivos con la bandera desactivada identificados en la [auditoría previa](COBERTURAS_Y_DENOMINADORES_PERIL_2023.md); cobertura se interpreta como predictor, no como exclusión contractual validada.

Tweedie de potencia 1,5, enlace log e intercepto, alpha cero, solver lbfgs, 2.000 iteraciones máximas y tolerancia 1e-6, sin warm_start. Medianas y escala numéricas y OHE dropfirst/min_frequency50/max_categories40/ignore, aprendidos únicamente en ajuste. Respuesta T0/e y peso raíz(e), con e=e_cost_mix_1.0 original de cada fold. La predicción observada multiplica la tasa por e una sola vez. Los valores de capital de B14 se conservan con sus condiciones abiertas; no entran clima o credibilidad nuevos.

C0 de entrenamiento procede del mismo archivo de B14 para ese fold. El C0 de una fila OOF se compara con el de su propio fold retenido, pues las curvas de otros folds son distintas por diseño. Se verifican 50.094 periodos, 30.869 componentes y cinco folds guardados, con clientes/direcciones/componentes disjuntos. No se reseleccionan variables, semillas o regularización tras ver resultados.

## Ajuste, incertidumbre y nivel

| Ramo | Rango D² de ajuste por fold | Rango D² de validación por fold |
| --- | ---: | ---: |
| Autos | 0.046833 a 0.069152 | -0.038790 a 0.067697 |
| Edificios | 0.082730 a 0.107039 | -0.039424 a 0.036117 |
| Contenidos | 0.061389 a 0.078698 | 0.002460 a 0.069942 |

Los rangos recorren muestras solapadas; no son intervalos de confianza. En edificios, la razón condicional AD_yes/AD_no varía entre 0,795 y 1,388 y cambia de dirección entre folds. En autos, third_party_only/comprehensive va de 0,567 a 0,857. Los coeficientes y sus razones por fold quedan archivados, sin atribución causal o contractual. Los quince ajustes convergen con gradiente normalizado por debajo de 1e-4. Ese control técnico no garantiza generalización.

| Contraste nuevo | Cambio D² | Intervalo exploratorio 95% | Tras retirar sus 31 grupos favorables |
| --- | ---: | ---: | ---: |
| W2-B19 / W2-B14 | -0.004240 | [-0.009969; +0.000507] | -0.007145 |
| W2-B19 / W2-B00 | +0.013888 | [-0.011053; +0.037614] | -0.014724 |

Se usan 2.000 sorteos agrupados comunes por pareja y la misma nula del objetivo. Ambos intervalos incluyen cero. Son intervalos sin ajuste por búsqueda adaptativa, condicionados a modelos y primera etapa ya ajustados; no incorporan su incertidumbre de reajuste. El diagnóstico de influencia no borra siniestros o grupos del modelo. La ventaja puntual sobre B00 invierte signo con esa perturbación de evaluación. No se repite el bootstrap de las parejas antiguas ni se interpreta un punto como permiso de selección.

El total observado predicho pasa de 15.429.695,38 CU a 15.436.941,83 CU. El nominal condicionado de los mismos periodos de 2023 pasa de 15.606.084,09 a 15.613.508,68 CU (+0,0476%). Es exposición nominal de esos contratos por su tasa bajo el vínculo declarado, no prima final o verdad de último de 2025/test. Mantener un nivel cercano tampoco demuestra equivalencia estadística.

## Controles y decisiones

Pasaron 569 comprobaciones separadas con fit bloqueado, 39 adversos focales y 8 conciliaciones de lectura, con solapamiento. El comprobador reconstruye medianas, escalas y categorías de ajuste, la predicción exp(Xβ), el gradiente, la igualdad entre objetivo ponderado y desviancia observada, métricas con sklearn y dos remuestreos nuevos mediante multiplicidades. El replay de B19 y B14 es exacto sin ajuste. Los cuatro comandos adversos reales rechazan año sintético 2024, cobertura ausente o cambios de T0/C0 antes de iniciar fit; sus fallos esperados llevan marcador para que no se confundan con entrenamientos pendientes.

Se conservan exactamente las 19 alternativas anteriores en el OOF de veinte modelos, más los archivos e índices históricos. El contador propio actual suma 180 ajustes de precio y 285 constantes. El linaje exclusivo del catálogo principal tiene 105 ajustes y 60 constantes; las diferencias corresponden a sensibilidades previas, no se ocultan o recuentan como trabajo nuevo. Auxiliares, curvas de reporte y estimaciones de mezcla mantienen sus contadores separados. Hay dos contrastes nuevos y 171 históricos heredados; no se calcularon las otras 17 parejas posibles con B19.

La decisión es conservar la receta adversa y estudiar estabilidad de coeficientes y contribuciones de grupos antes de otra receta. Este resultado no demuestra que hagan falta árboles o interacciones ni justifica ajustar regularización después de verlo. No se promueve, retira o congela una lista final. Revisión propia de Codex, no profesional independiente ni aprobación humana.

## Ámbito temporal y trazabilidad

2024 permanece cerrado para este trabajo, sin precios, predicciones, puntuación, acta o lectura del ledger; también test, remoto y envíos. Se conserva la exposición previa de un asunto ajeno con métricas de confirmación, sin repetirlas o usarlas; no se afirma ceguera completa. El lector del foro solo emite autor, ID y UTC. Sin nuevas conversaciones, delegación, publicación externa o cambios a otras automatizaciones.

[Plan congelado](../../../registro/semana2_desarrollo2023_plan_v8.json), [índice actual](../../../registro/semana2_desarrollo2023_actual.json), [snapshot anterior](../../../registro/semana2_desarrollo2023_v7_snapshot.json), [productor](../../../src/semana2/entrenar_desarrollo2023_v8.py), [comprobador](../../../herramientas/verificar_desarrollo2023_v8_semana2.py), [adversos](../../../herramientas/probar_desarrollo2023_v8_semana2.py). Fuentes, modelos, entorno, OOF y recibos restringidos: `Hackaton/Repositorio_IAA2026/privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214`. El [balance nocturno](BALANCE_NOCTURNO_PARCIAL_20261024.md) conserva su carácter parcial hasta las 07:00 de Bogotá.


## Diagnóstico posterior de B19 con artefactos guardados

La [revisión de estabilidad e influencia](ESTABILIDAD_E_INFLUENCIA_B19_2023.md) termina sin ajustes, modelos o bootstrap nuevos. La cobertura de edificios cambia dirección entre folds; ninguna retirada individual de evaluación revierte su deterioro. En autos nuevos un grupo concentra 56,1% de pérdida bruta adversa; su retirada de evaluación revierte el segmento, pero el portafolio continúa negativo. No se borra ningún registro ni se adopta una beta alterada. La influencia local del GLM es aproximada y se distingue de su error OOF. B00 y todas las alternativas se conservan, sin reemplazar el catálogo que actualizan otras continuaciones. Próximo trabajo: trazabilidad de pagado, reservas, recuperaciones, estado y fechas de esos grupos, con artefactos de 2023. Foro 036/037; 2024 cerrado en este trabajo. Balance parcial hasta las 07:00 Bogotá.
