# Edificios nuevos: por qué falló la contracción y qué implica para F3c

Codex, 27 de octubre de 2026, Bogotá. F3c sigue siendo la referencia enviada de nuestra línea revisada. R1 se conserva como alternativa; la contracción NB-CRED300 no fue adoptada ni enviada. Este diagnóstico no sustituye ninguno de esos archivos y no cambia la selección final manual de Kaggle.

| Archivo o ensayo | Estado de nuestra revisión |
|---|---|
| F3c | Enviado, público revisado 0,16914; conservado como referencia de entrega |
| R1 | Enviado, público revisado 0,15820; alternativa conservada, sin adopción como reemplazo |
| Contracción NB-CRED300 | Ensayo local con controles fallidos; sin adopción ni envío |

Estos son los recibos propios revisados, no una consulta nueva de toda la cuenta. El score privado de 2025 continúa desconocido. Conservar F3c no significa haber demostrado que será el mejor modelo privado; exige evidencia antes de reemplazarlo.

## El fallo de la contracción es verificable en los precios fijos

La receta subía un 7,09 % todos los precios de edificios nuevos, sin cambiar su forma ni los precios de renovación. Sobre los 2.279 periodos de edificios nuevos de 2024, la diferencia de D² fue −0,009828 frente al R1 temporal de la misma familia. No es una evaluación del CSV F3c de 2025.

La identidad de devianza Tweedie permite separar exactamente el efecto del coste observado y el término de precio:

| Parte del cambio de devianza favorable, antes de dividir por la nula | Valor |
|---|---:|
| Término dependiente del coste observado | +2.340,84 |
| Término de precio, separado de los peligros | −4.048,29 |
| Balance | −1.707,45 |

Es una identidad del contraste con el T0 disponible, no una valoración del coste último. El término de precio no se reparte artificialmente entre peligros. En este corte, el coste observado no compensa el efecto del incremento uniforme. Esto no implica que una póliza sin siniestro deba tener prima cero.

El periodo de mayor coste mejora con la subida y representa el 14,51 % del T0 de la celda. Los demás periodos, conjuntamente, pierden más de lo que ese caso aporta. La contracción perjudica cuatro de los cinco cortes guardados de edificios nuevos; uno mejora. No procede explicar el fallo únicamente por un siniestro extremo o retirarlo de la evaluación.

## La exposición histórica no representa bien la cartera futura

Las duraciones medias de edificios nuevos en 2023 y 2024 son muy parecidas: 0,477 y 0,479 años. Por tanto, esa media no explica por sí sola el deterioro entre ambos años. Pero la exposición futura tiene una composición muy distinta.

| Edificios nuevos | Periodos históricos | Periodos con coste positivo | Exposición en la banda de al menos 0,9 años |
|---|---:|---:|---:|
| 2023 | 1.507 | 40 | 16,95 % |
| 2024 | 2.279 | 35 | 17,67 % |
| 2025, solo covariables guardadas | 39.716 | Desconocido | **94,27 %** |

En esa banda larga hubo ocho periodos positivos en 2023 y tres en 2024. Los cortes no son observaciones independientes de un nuevo mercado. El menor coste observado en tan pocos casos no respalda trasladar una rebaja a los 35.021 periodos largos de negocio nuevo de 2025.

El registro conserva todos los estratos previstos de construcción, ocupación, canal, siniestros previos, desocupación y capital, además de duración y trimestre de inicio. Se describieron sin seleccionar variables o subgrupos favorables ni entrenar con ellos.

## La madurez y la mezcla de peligros cambian

| Edificios nuevos, valoración diciembre de 2024 | Cohorte 2023 | Cohorte 2024 |
|---|---:|---:|
| Siniestros aceptados asignados | 40 | 37 |
| Periodos positivos | 40 | 35 |
| Coste T0, CU | 354.074,06 | 256.972,12 |
| Reservas / T0 | 10,35 % | **51,20 %** |
| Siniestros abiertos | 2 | 15 |
| Edad media de los siniestros al corte, días | 484,8 | 133,4 |
| Reportados en un año posterior al de ocurrencia, ya observados | 6 | 0 |

El cero de reportes posteriores para la cohorte 2024 refleja que el archivo termina en 2024. No prueba que esa cohorte carezca de reportes tardíos. Los importes actuales de pago y reserva tampoco reconstruyen lo que se conocía al cierre de 2023.

La composición de los pocos siniestros cambia: inundación y subsidencia reúnen aproximadamente el 77 % del T0 de edificios nuevos de 2023; en 2024 aparecen cuatro incendios y varias reservas importantes. Son descripciones de una muestra pequeña, no evidencia suficiente para estimar otro factor por peligro.

El desajuste de nivel no se limita al negocio nuevo. Con los precios temporales guardados, el cociente de coste observado sobre predicción de edificios en renovación pasa de 1,012 en 2023 a 0,619 en 2024; en negocio nuevo pasa de 0,999 a 0,516. Esos cocientes no son nuevos niveles de precio ni estimaciones del coste último. Señalan incertidumbre temporal y de valoración que un prior medio de ramo no resuelve por sí solo.

La completitud del modelo también cambia entre cohortes; se conservó su valor guardado, sin reestimarlo. No se presenta como la fracción verdadera de siniestros ya conocida.

## Qué dicen los escenarios y qué no pueden decir

En el nuevo corte específico de edificios nuevos, la diferencia de la receta fallida es negativa en las cincuenta etiquetas de escenarios existentes: entre −0,012609 y −0,007423. Son los mismos precios, sin aprendizaje adicional. El recuento no equivale a una probabilidad.

Los escenarios cambian los costes registrados o el marco de observación contemplado; no aportan los siniestros todavía desconocidos ni prueban suficiencia del último. Tampoco demuestran qué nivel será correcto en el privado de 2025. Los resultados por periodo y siniestro permanecen privados.

## Decisión y continuación

Se conserva el rechazo de NB-CRED300. No se modifica K, no se excluye edificios para rescatar el ensayo y no se aplica una rebaja a 2025 con los cocientes observados. El nivel de ramo como prior de negocio nuevo no quedó respaldado en esta prueba.

La prioridad vuelve a la evidencia sobre la familia que sostiene F3c: preparar una validación temporal consistente con su tronco y preprocesamiento, distinguiendo los bloques aprendidos de las calibraciones públicas históricas y separando una aproximación protegida del archivo exacto ya enviado. Las pruebas anteriores de una semilla sin F1 no certifican retrospectivamente toda la receta publicada. Antes de ajustar otra alternativa, su mecanismo, configuración y controles deberán quedar registrados.

Este diagnóstico ayuda a evitar un reemplazo basado en un promedio local favorable. F3c permanece como referencia de entrega; R1 y todos los resultados adversos se conservan. No hubo nuevos parámetros, árboles, curvas, sorteos, inferencia de árboles, precios de 2025 o envíos.

## Evidencia

Las asignaciones de siniestros ya existentes se conciliaron con el T0 por periodo en céntimos. Neto pagado más reserva coincide con coste neto, y las contribuciones de peligros y de pago/reserva cierran el término de coste. La descomposición y las métricas se cotejaron con sklearn; las derivadas se comprobaron por diferencias finitas. Los originales conservan sus hashes.

Índice: `registro/semana2_NB_edificios_prior_diagnostico_actual.json`. Plan: `registro/semana2_NB_edificios_prior_diagnostico_plan.json`. Código: `herramientas/diagnosticar_prior_edificios_NB.py` y `herramientas/verificar_prior_edificios_NB.py`. Revisión computacional propia y exploratoria sobre 2024 adaptativo, sin acreditación profesional independiente ni demostración de superioridad privada.
