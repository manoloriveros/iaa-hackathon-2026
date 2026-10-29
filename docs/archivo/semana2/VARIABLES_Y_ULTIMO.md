# Variables admisibles y paso del incurrido al último

Codex, 23 de octubre de 2026. Las primeras referencias de precio ya tienen entradas, particiones y vínculo de observación preparados y comprobados. El [índice de disponibilidad para entrenar](../../../registro/semana2_listo_entrenar.json) identifica los archivos vigentes. No se ha entrenado un modelo de precios.

La preparación permite entrenar una referencia sobre T0 y una variante a último bajo supuestos explícitos. No acredita suficiencia de reservas ni exactitud frente al último oculto. La revisión humana general conserva su estado pendiente.

## Qué entra en el primer modelo

La [lista por campo](../../../privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766/availability_contract.json) asigna un papel a cada columna original y fija la lista exacta de predictores. Los archivos contienen también claves y exposición para unir tablas; esas columnas de servicio no son predictores.

| Bloque | Decisión inicial |
| --- | --- |
| Características de la póliza y coberturas | Admitidas, con bandas de edad conservadas como categorías y sin inventar edades exactas |
| Ubicación y características físicas | Admitidas bajo el supuesto declarado de estabilidad del maestro de direcciones |
| Antigüedad como cliente | Año del periodo menos año de ingreso, con comprobación de coherencia |
| Prima comercial y descuento | Fuera del modelo base por circularidad con la tarifa existente |
| Contactos de servicio y decisión de renovación | Excluidos por disponibilidad posterior al resultado o al periodo |
| Identificadores, objetivos, grupos y folds | Solo claves, etiquetas o controles; nunca predictores |
| Ocupación, perfil y otros atributos sin fecha | Fuera de la base, pendientes de una variante condicional revisada |
| Género | El diccionario sintético permite su uso; se excluye de la base hasta evaluar finalidad y resultados por segmento |
| Clima anual | Fuera de la base inicial; variante histórica separada |
| Capitales en escala incierta | El logaritmo derivado queda ausente en los casos revisados; no se divide automáticamente por mil |

Las matrices F0 tienen 40 predictores en autos, 32 en edificios y 33 en contenidos. Conservan nulos numéricos y una categoría explícita para ausencias categóricas. No se ajustaron imputadores, codificadores, frecuencias de categorías ni transformaciones con etiquetas. Todo aprendizaje posterior de esas operaciones debe quedar dentro de cada partición de ajuste.

La exposición suministrada condiciona el coste total solicitado por el concurso. Se usa como exposición, no como una predicción de cancelaciones. Los atributos físicos no cuentan con snapshots históricos: admitirlos supone estabilidad, y no demuestra que cada valor estuviera disponible en una cotización real.

### Capitales y controles de calidad

Aparecen dos agrupaciones separadas: edificios hasta 894.000 CU frente a valores desde 60 millones; contenidos hasta 283.200 frente a valores desde 7,6 millones. Solo diez registros de contenidos tienen apoyo de otra fila de la misma póliza para una relación exacta de mil; eso no justifica corregir toda la agrupación.

Se fijaron filtros de revisión de 10 millones para edificios y un millón para contenidos, ambos dentro de los huecos observados. Por encima, `x_log_sum_insured` queda nulo. Son filtros de incertidumbre, no límites oficiales ni prueba de error de cada capital. Afectan 110 filas de entrenamiento y 239 de test. El [registro de casos](../../../privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766/capital_uncertainty_audit.parquet) conserva capital original y acción; la marca de revisión queda fuera de los predictores.

## Clima de 2025

La descripción de [Kaggle](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/data) se consultó de nuevo: sigue describiendo clima 2023–2024, mientras el archivo incluye 2025. Los valores de 2025 cambian respecto de 2024; no son una copia. No se ha identificado una prohibición específica de usar esas columnas en Kaggle, pero tampoco evidencia de que sean pronósticos conocidos al cotizar.

La base excluye todo clima anual contemporáneo. Se preparó otra tabla con el último año natural completo anterior a:

`fecha_cotización = period_start − days_quote_to_inception`

Una cotización en diciembre de 2024 usa clima de 2023; una de enero de 2025 puede usar 2024. Se supone disponibilidad del agregado anual una vez terminado ese año; la fecha real de publicación no consta.

En 2023 no hay historial anterior suficiente. Se dejan ausencias, sin rellenarlas con clima del mismo año ni del futuro. En todo el entrenamiento solo 18.774 filas encuentran ese historial; en test lo encuentran todas. Por eso esa variante todavía necesita una evaluación específica y no entra en el primer F0.

La prueba de sustituir todas las celdas de clima 2025 por valores extremos deja intacto el bloque histórico. El modelo base ni recibe esas celdas. Las zonas de inundación y otras características físicas siguen disponibles bajo el supuesto del maestro.

## Lo que muestra el reporte tardío

Los 9.102 siniestros aceptados y asignados incluyen 35 reportados más de 365 días después de ocurrir, por 339.973,19 CU de incurrido neto. Veinticuatro corresponden a lesiones corporales de 2023. No es correcto suponer que todo está reportado al año.

Lesiones tiene 266 notificaciones de 2023 y un retraso máximo de 653 días; hundimiento, 32 y un máximo de 294 días. La escasez de hundimiento limita la precisión. Que el máximo observado sea menor que un año no demuestra ausencia de una cola más larga. Las medianas menores de 2024 tampoco prueban un reporte más rápido: ese año tiene menos seguimiento y más truncamiento.

No se usaron los 36 siniestros anteriores a cobertura para estimar la cola: son una selección fuera de las cohortes y exposiciones modeladas.

### Vínculo de observación preparado

Se estiman distribuciones de retraso por ramo y peligro mediante producto-límite en tiempo inverso, con el conjunto de riesgo:

`M(d) = número de observaciones con D_i ≤ d ≤ R_i`

`D_i = report_date − loss_date; R_i = 31-12-2024 − loss_date`

La referencia estadística describe esta construcción para datos truncados; su aplicación a los importes y a la mezcla de peligros de este reto es una adaptación propia condicionada a los supuestos siguientes. [Seaman, Presanis y Jackson (2022)](https://journals.sagepub.com/doi/10.1177/09622802211023955).

Se separan la distribución de conteos y la del coste observado. Para el coste se combinan la masa de retraso estimada y el incurrido neto medio de cada demora. Así no se impone que la severidad de los reportados pronto y tarde sea idéntica. Las marcas siguen siendo incurridos al corte, no costes finales conocidos.

Se prepararon siete ámbitos: 2023 completo para el contraste temporal; 2023 sin cada uno de los cinco grupos retenidos, reutilizados en desarrollo y población nueva; y 2023–2024 para producción. Son 105 curvas de conteos por peligro, con curvas de coste para cada estrés de reserva. Ningún siniestro del grupo o año de validación interviene en el ajuste correspondiente.

Las proporciones de coste por peligro también se estiman solo en el ajuste. Su mezcla por ramo aproxima la composición de cada fila; se conservan los vínculos por peligro para contrastar después una estructura frecuencia-severidad.

| Ramo | Completitud de coste de 2024 ponderada por exposición, estimada con 2023 |
| --- | ---: |
| Autos | 80,64 % |
| Edificios | 95,27 % |
| Contenidos | 96,98 % |

Son resultados del modelo de observación bajo sus supuestos, no porcentajes de último comprobados ni factores generales para multiplicar cualquier predicción.

## Reservas y cola no observada

El incurrido ya contiene pagos y reserva de caso. La estimación de pasivos distingue esa reserva del desarrollo adicional y de los siniestros todavía no reportados. Esa separación evita duplicar componentes. [Friedland, CAS](https://www.casact.org/sites/default/files/2021-03/5_Friedland.pdf).

La reserva incluida en T0 es 3.501.391,79 CU en autos, 1.300.698,96 en edificios y 193.706,89 en contenidos. El escenario base mantiene `b=1` como hipótesis condicional sobre las estimaciones actuales, sin acreditar suficiencia. Una valoración no identifica el desarrollo posterior de reservas, reaperturas o recuperaciones.

Los escenarios `b=0,75` y `b=1,25` cambian únicamente:

`marca = incurrido neto observado + (b−1) × reserva de caso`

Se recalculan las curvas y mezclas de coste con esas marcas dentro de los mismos ámbitos. No se añade la reserva completa otra vez. Estos escenarios no abarcan toda la incertidumbre de recuperaciones o cambios operativos.

La curva base asigna masa total al soporte estimado. La historia no identifica cuánto coste podría reportarse fuera de ella. Se guardaron sensibilidades con 5 % o 10 % de masa de coste de lesiones/hundimiento después de la ventana máxima histórica de 730 días. Son escenarios de diseño, no probabilidades estimadas, intervalos de confianza o una cola validada. No se tomaron factores del mercado desarrollado ni de S41.

## Cómo se entrena sin duplicar el ajuste

El [contrato de entrenamiento](../../../registro/semana2_contrato_entrenamiento.json) conserva dos lecturas, con funciones distintas:

- Diagnóstico observado W2-D00-OBS: respuesta T0 y exposición nominal. No se mezcla con la lista de confirmación primaria como si tuviera el mismo vínculo.
- Comparación primaria condicional a último: referencia W2-B00 y aspirantes con respuesta T0 (o su estrés) y el mismo vínculo de exposición efectiva del ámbito correspondiente. La exposición efectiva integra la proporción reportada sobre los días de cobertura.

Si el modelo aprende una tasa anual `r`, la predicción observada de validación es `exposición_efectiva × r`; la predicción a último de 2025 es `exposición_nominal × r`. No se agrega después otro multiplicador IBNR ni otra reserva.

Para minimizar la devianza Tweedie de importes totales con potencia 1,5 al ajustar tasas, se preparó la identidad:

`d_p(Y,e×r) = e^(2−p) × d_p(Y/e,r)`

El objetivo de tasa es `Y/e` y el peso es `sqrt(e)`, con `e` nominal o efectiva según el comparador. Es una elección para alinear la pérdida con la devianza unitaria del proxy local; no identifica el código privado del evaluador. La identidad se comprobó numéricamente.

El contraste de 2024 continúa sobre T0 mediante el vínculo de observación fijado con 2023. No ofrece verdad última de validación. Las etiquetas comparten valoración al cierre de 2024 y faltan snapshots: se conserva la limitación del backtest.

## Estado para el primer entrenamiento

Las matrices, el vínculo por ámbito y las dependencias están listos para entrenar las primeras referencias. Se comprobó la importación de scikit-learn, LightGBM y CatBoost, sin ajustar estimadores. Permanecen condiciones de uso: estabilidad de los maestros, estacionariedad de retrasos y marcas dentro de peligro, independencia respecto del truncamiento de calendario y las hipótesis de reserva y cola descritas.

La preparación pasó 194 controles; el comprobador separado pasó 1.138, con reconstrucción racional de las curvas y contraste de claves y grupos; veinte pruebas cubren casos conocidos y envenenamiento de variables excluidas. Otros nueve controles verifican la escala de pérdida e importaciones. Se solapan y no se suman como pruebas independientes.

Se incorporó el [protocolo de selección vigente](../../semana2/PROTOCOLO_SELECCION.md), recibido durante esta preparación en COD-S2-20261023-SEL01. Los primeros ajustes de desarrollo pueden empezar en 2023. No se consultan scores de modelos en 2024 hasta congelar la lista, recetas, vínculo común y productor de métricas y registrar la apertura con el evaluador común. Su implementación de scores/bootstrap sigue siendo un requisito antes de abrir, no un impedimento para preparar o ajustar las referencias en desarrollo. La referencia designada es W2-B00 con el mismo vínculo C0 que sus aspirantes. No se abre confirmación ni se modifica esa política aquí. La disponibilidad técnica para ajustar no constituye permiso de promoción: las advertencias y condiciones pendientes tendrán las consecuencias de ese evaluador.

La revisión del selector registrada en COD-S2-IA-20261023-GATE reprodujo una brecha: se comprueba el hash del recibo, pero no la correspondencia entre su contenido y las cifras consumidas. El hallazgo S2-AUD-METRIC-BINDING permanece abierto y bloquea una promoción verificada. Antes de abrir confirmación se exige cerrar ese vínculo semántico, además de contar con productor y comprobador de métricas desde predicciones congeladas. Esta lectura no modifica el selector ni atribuye un cierre a quien mantiene el hallazgo. El desarrollo de 2023 puede empezar.

La revisión es propia de Codex. Se estimaron patrones actuariales de reporte, pero no se entrenaron modelos de precios, no se eligió candidato y no hubo envíos. La decisión previa está en COD-S2-20261023-004, el resultado en COD-S2-20261023-005, la integración con SEL01 en COD-S2-20261023-006 y la condición del selector en COD-S2-20261023-007 del [foro](<../../../../Semana%202/Foro/FORO.md>). El [catálogo de fuentes](<../../../../Semana%202/Codex/fuentes_variables_ultimo/referencias.json>) distingue páginas leídas de extractos indexados y de intentos de acceso incompletos.


## Avance posterior: primera tanda de desarrollo

Después del corte de preparación de este documento se entrenaron las primeras recetas exclusivamente en 2023. El [resultado de desarrollo](DESARROLLO_2023.md) y el [índice](../../../registro/semana2_desarrollo2023_actual.json) contienen ese nuevo corte, sus resultados adversos y las condiciones pendientes. La preparación original y sus contadores conservan su alcance histórico. La confirmación de 2024 continúa cerrada.
