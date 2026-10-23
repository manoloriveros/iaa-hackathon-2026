# Frecuencia conservada y severidad compartida

Propuesta de Codex del 22 de octubre de 2026, a petición del participante. Estado: diseño para evaluar, sin entrenamiento, predicciones nuevas o envíos. No sustituye «Mezcla por peligro» (S30), sus pesos o el cierre registrado en D99. La solicitud actual permite plantear una alternativa; no se interpreta como selección final o autorización de un envío.

## La diferencia que queremos superar

La captura aportada muestra 0,13003 para el líder y 0,12996 para S30: 0,00007 según las cifras redondeadas. Es una diferencia pequeña. No conocemos sus predicciones, su puntuación privada ni un intervalo de la diferencia. La captura no permite inferir su método, que tenga un modelo radicalmente superior o que baste un ajuste de escala para ganarle.

La consulta oficial del 22 de octubre confirma posición2 y cierre el23 de octubre a las11:00 de Bogotá. El objetivo sigue siendo coste último esperado, neto de franquicia y recuperaciones, con rechazados excluidos; la métrica es D² Tweedie de potencia1,5. Los premios combinan ambas partes y evaluación del jurado, no solo esta clasificación pública.

## La oportunidad concreta del código actual

| Fuente inspeccionada | Limitación observable | Alcance de la observación |
| --- | --- | --- |
| `src/modelos/cat_frecsev.py` | La frecuencia por peligro se multiplica por una severidad media del peligro. | Existe una base sólida de frecuencias que podría reutilizarse. No demuestra que la media constante sea el principal error. |
| `src/modelos/severidad_cfs.py`, línea84 | En autos, las relatividades por valor y antigüedad se ajustan para daños propios, robo y lunas; lesiones y daños a terceros quedan sin esas covariables de severidad. | Afecta a esos componentes; los árboles de coste total que también integra S30 sí pueden aprender heterogeneidad. |
| `src/modelos/frecsev2.py`, líneas29 y63–66 | La severidad usa una media constante cuando hay menos de1.500 filas positivas; la proporción de coste positivo se calcula como cociente de filas. | El umbral es de filas positivas, aunque la descripción hable de siniestros. Falta comprobar qué peligros caen bajo el umbral y si hay suficientes siniestros de coste cero para modelarlos. |

La hipótesis es que un modelo de severidad que comparta información entre peligros puede aprender parte de esa heterogeneidad con menos ajustes y menos varianza que quince modelos aislados. No se afirma que el efecto exista o que mejorará la puntuación. La primera fase debe comprobar su viabilidad con entrenamiento histórico, sin mirar resultados nuevos de2024.

La alternativa difiere de C27, que ajustó Gamma por peligro con nueve campos en edificios, y de C34, que volvió a ajustar frecuencias CatPoisson. Esos resultados adversos se conservan. Aquí se congelan las frecuencias y se prueban dos cabezas compartidas por ramo sobre siniestros individuales. No se reabre una búsqueda de semillas, intensidades o peligros favorables de aquellas líneas.

## Modelo propuesto

Para cada póliza-periodo y peligro admisible:

```text
coste del peligro = frecuencia congelada × probabilidad de coste positivo dado un siniestro
                  × importe esperado si el coste es positivo
```

Las frecuencias proceden de los componentes guardados y verificados de la receta, sin nuevos ajustes. Se propone usar CFS_motor_4s para autos, CFS_buildings para edificios y la frecuencia aditiva de FSA_contents para contenidos. Antes de implementar hay que cotejar la disponibilidad de las frecuencias por peligro, sus factores de severidad de referencia y el orden de filas; no se da por hecho que cualquier vector de coste permita recuperar una frecuencia. Si falta un insumo se documenta el impedimento y se detiene esa rama.

La orden congelada de FSA_contents no incluye `--partes`; por tanto, no se presume que tenga vectores por peligro exportados. La recuperación por inferencia desde estimadores persistidos sería una opción sin reentrenar frecuencias, pero debe comprobarse y dejar recibo antes de usarla. También falta acreditar las predicciones del ancla en la mitad de calibración2023. Son requisitos de viabilidad, no comprobaciones ya realizadas.

Por ramo se ajustan dos modelos LightGBM, cada uno con todos sus peligros y `peril` como categoría:

- Clasificación binaria para el indicador de coste neto positivo, condicionada a que haya siniestro aceptado. Los siniestros aceptados de coste cero permanecen aquí. Un peligro sin ambas clases conserva la probabilidad empírica de entrenamiento; no se fuerza una clasificación inexistente.
- Gamma con enlace log para el importe positivo. Los importes se dividen por la media positiva de su peligro calculada únicamente en entrenamiento y después se restituyen a CU. Cada siniestro único pesa una vez. No se recortan las colas ni se transforma una mediana en media.

La distinción entre «sin siniestro» y «siniestro de coste cero» evita duplicar la probabilidad de ocurrencia que ya recoge la frecuencia. El objetivo por siniestro debe conciliarse con los `n_p`, `y_p` y T0 de D67 antes de ajustar. Se usan abiertos y cerrados aceptados con la misma base contable; no se aprende solo de cerrados. Incurrido y recuperaciones son etiquetas de coste, nunca predictores. No se resta otra vez la franquicia, no se añade otro IBNR y no se adopta S3.

La severidad resultante se acerca a la media histórica mediante credibilidad:

```text
z_p = N_p / (N_p + 1000)
severidad_final = (1 - z_p) × media_histórica_p + z_p × probabilidad_positiva × importe_positivo
```

N_p es el número de siniestros aceptados de entrenamiento del peligro. El1000 es una decisión previa de regularización, no un valor óptimo demostrado. No se probarán otros después de ver2024. Si no existe una media de referencia válida, no se fabrica una: la rama queda no ejecutable hasta resolverlo.

La suma sobre peligros estima el coste del periodo. No hace falta asumir independencia entre peligros para sumar sus medias; compartir información busca mejorar su estimación, no demostrar una estructura causal o resolver la incertidumbre de reservas.

## Variables, ajuste y tamaño del ensayo

Las nuevas cabezas usan características de póliza y riesgo ya disponibles en las tablas congeladas: ambas franquicias; edad del conductor/asegurado; valor, edad y tipo de vehículo; cobertura; capital asegurado, características físicas del inmueble y protecciones, según ramo. El implementador debe fijar el manifiesto exacto antes de ajustar y comprobar su presencia. No entran identificadores, primas, campos de tramitación del siniestro, pérdidas futuras, decisión de renovación o un nuevo promedio de clima2021–2025. No se corrigen los149capitales sin confirmación. Las fechas no acreditadas de las fuentes heredadas siguen siendo una limitación del ejercicio.

La receta inicial se fija en500árboles,7hojas como máximo, profundidad3, tasa0,03, mínimo500observaciones por hoja, L2=20, sin submuestreo de filas o variables y semilla20261022. Se fija CPU determinista y `force_row_wise=true`, conservando la versión efectiva de LightGBM y los estimadores. Son decisiones propuestas, sin afirmar que sean óptimas. No hay rejilla, búsqueda de otra arquitectura ni elección de otra semilla tras un resultado adverso.

Máximo12ajustes de cabezas para evaluar: dos cabezas × tres ramos × dos cortes, más la estimación de un único peso de combinación. Se usarían2021–2022 para evaluar2023 y2021–2023 para evaluar2024. Si finalmente se aprobara el candidato, producción2025 añadiría como máximo otros seis ajustes de cabezas; no se hacen en esta propuesta. No se relanzan las frecuencias, N62 o la reproducción completa. El tiempo real debe medirse antes de comprometer la ventana restante; no hay una estimación de horas comprobada.

## Integración conservadora con S30

El componente nuevo aporta reparto de riesgo; en cada ramo y cartera se iguala su total al de S30 usando solo predicciones. Así el primer ensayo no cambia además el nivel anual, ya incierto. Esta normalización utiliza la composición de la cartera objetivo y no debe presentarse como información disponible al cotizar individualmente.

Se añade al ancla mediante una única combinación convexa: `(1 - alfa) × S30 + alfa × componente_nuevo`, con0≤alfa≤0,25. Un solo alfa para los tres ramos, ajustado con Tweedie1,5 exclusivamente en la mitad de calibración2023 fijada en la receta. La disponibilidad de predicciones auditables de S30 y de las frecuencias en esa mitad debe verificarse; si no existen, no se sustituye silenciosamente por2024 o por el público. Alfa cero significa ausencia de aportación útil; no produce un «modelo nuevo» para enviar.

La mitad de selección2023 y2024 sirven para los contrastes previstos. Ambos cortes tienen una larga historia de selección previa, también en S30: los nuevos contrastes son condicionales y no crean una validación independiente. No se modifican los pesos internos de S30 ni se escoge después un ramo o peligro ganador.

## Criterio de aceptación anterior a resultados

Se conserva el filtro exigente usado frente a S30: mismos objetivos, filas, exposiciones y denominadores; D² Tweedie1,5 completo; ramos, cartera, semestres y escenarios de reservas ×0,75/1/1,25 sin retrocesos puntuales en los ámbitos definidos. Ganancia global nominal2024 de al menos0,0002. Inferiores95% por cliente y dirección mayores que cero en nominal y+25%, con1.000réplicas, semilla281001 y denominador fijo. Solo si pasa lo anterior se calcula el control regional exacto N35 y se exige inferior no negativo.

La exigencia local0,0002 no es una predicción del público ni se reduce al0,00007 observado en la captura. Las colas y la influencia de grandes siniestros se informan con el denominador completo; no se eliminan clientes para aprobar. Los intervalos condicionales no cubren toda la selección previa, el próximo año o el sesgo del proxy de reservas. Si falla, se descarta la receta completa sin rescatar peligros, pesos, rondas o severidades favorables.

El préstamo entre peligros puede generar transferencia negativa, especialmente para lesiones. Una Gamma puede seguir siendo inadecuada para la cola. La valoración única no permite demostrar que las etiquetas sean costes últimos o reservas suficientes. Estos son riesgos de la hipótesis, no problemas resueltos por una nueva familia.

## Orden de trabajo y decisión que quedaría pendiente

Primero, auditoría de viabilidad del contrato de etiquetas, ceros, exposición, insumos por peligro y predicciones de calibración, limitada a datos de entrenamiento. Después, fijar el manifiesto y realizar el único ensayo descrito. Solo tras superar las comprobaciones correspondería preparar una producción2025 reproducible, CSV, auditoría y una decisión de envío. Ninguno de esos pasos se ha ejecutado o se da por autorizado por este documento.

Se mantienen S30 y su CSV entregado como referencia. No se promete recuperar el primer lugar: no se conoce el modelo rival ni su rendimiento privado. Esta propuesta busca una aportación distinta y comprobable con el menor cambio necesario en la cadena existente.

## Procedencia

Las fuentes locales y sus SHA se archivan en `privado/propuestas/severidad_compartida_20261022/fuentes.json`. El registro estructurado está en `registro/propuesta_modelo_20261022.json`. La captura del participante se conserva como evidencia recibida, separada de la consulta oficial de metadatos.

- [Concurso y cierre vigente](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1).
- [Reglas y evaluación global de ambas partes](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1/rules).
- [Consulta pública de siniestros del22oct](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1/discussion/751543): la respuesta recibida no contenía aclaración del organizador; no cambia el contrato de recuperaciones por esa pregunta.
- [LightGBM: objetivos y parámetros](https://lightgbm.readthedocs.io/en/latest/Parameters.html): soporte de Gamma/binaria y controles de determinismo. No garantiza igualdad entre versiones o sistemas.
- [Frees, Meyers y Cummings: modelos de múltiples peligros](https://www.casact.org/abstract/predictive-modeling-multi-peril-homeowners-insurance-0): antecedente para comparar estructuras por peligro fuera de muestra; no prueba la mejora de esta receta.
