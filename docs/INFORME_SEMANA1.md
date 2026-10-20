> Borrador de trabajo de la semana 1. El informe final de la entrega está en [docs/entrega/report_en.pdf](entrega/report_en.pdf), con copia en español en [docs/entrega/informe_es.pdf](entrega/informe_es.pdf).

# Una prima de riesgo para cada periodo de póliza

AI Hackathon IAA 2026 · Primera semana · Borrador para revisión del participante

## Resumen

Estimamos el coste esperado de los siniestros de cada periodo asegurado. El enfoque combina modelos de coste total con modelos que separan la frecuencia y el importe de los siniestros. La combinación se adapta a autos, edificios y contenidos del hogar.

El trabajo empieza por reconstruir los datos y asignar cada siniestro a la cobertura que le corresponde. Después incorpora el retraso de notificación, compara alternativas en el tiempo y verifica el archivo de entrega. La IA interviene en ese recorrido con propuestas, código y revisión crítica de los resultados.

La propuesta principal obtiene una mejora pequeña frente al respaldo. Conservamos ambos candidatos porque la incertidumbre de la comparación todavía impide establecer una mejora concluyente. La elección final y la revisión humana siguen pendientes.

## Preparar los datos para que el modelo aprenda lo correcto

La información reúne clientes, ubicaciones, pólizas y siniestros de un mercado sintético. Algunas pólizas cambian durante el año y un mismo identificador reaparece en renovaciones. Por eso asignamos cada siniestro usando su póliza, ramo y fecha de ocurrencia. Un enlace que ignore el periodo de cobertura puede duplicar costes o asignarlos al año equivocado.

Las decisiones de preparación responden a problemas concretos:

| Decisión | Qué resuelve |
| --- | --- |
| Armonizar claves de cliente | Recupera enlaces con el maestro sin cambiar la identidad del asegurado. |
| Corregir unidades de exposición | Evita que días registrados como años distorsionen las tasas y el coste del periodo. |
| Revisar la escala de los capitales | Aplica el tratamiento documentado y conserva los casos sin confirmación como incertidumbre. |
| Unificar categorías y edad de referencia | Hace comparables las variables y distingue una convención de un error demostrado. |
| Excluir copias exactas de siniestros | Evita contar dos veces el mismo coste. |
| Conservar marcas de auditoría | Permite revisar incidencias sin convertirlas en predictores. |

Los originales se preservan. Cada transformación tiene una regla, una conciliación y una referencia al dato de origen. El diccionario y el panel permiten revisar el recorrido de cada variable.

## Del coste observado al coste último

El objetivo es el coste final esperado de los siniestros del periodo cubierto, neto de franquicias y recuperaciones. Para aprender usamos el coste incurrido de los siniestros aceptados, descontando las recuperaciones. Los pagos ya son netos de franquicia, por lo que evitamos descontarla de nuevo. Los siniestros rechazados quedan fuera del coste.

El cierre disponible todavía no recoge todos los siniestros que terminarán notificándose. Estimamos la proporción reportada por peligro con un método de desarrollo de conteos y la incorporamos a la exposición de entrenamiento. Al predecir usamos la duración nominal de la cobertura. Así, el ajuste por retraso de notificación entra una sola vez.

Las reservas de caso de los siniestros abiertos se mantienen en el coste observado. Disponemos de una única valoración, que no permite demostrar su suficiencia ni la ausencia de sesgo. Esa limitación acompaña la propuesta.

## Modelos con funciones distintas

Los modelos de coste total captan relaciones entre las características del riesgo y su coste. Los de frecuencia y severidad permiten estudiar qué peligros impulsan la predicción y cómo cambia el importe de sus siniestros. Combinamos ambas lecturas con pesos específicos por ramo.

| Ramo | Composición de la propuesta | Función de la combinación |
| --- | --- | --- |
| Autos | Frecuencia y severidad: 60 %. Modelos de coste total: 40 %. | Combina frecuencia por peligro, severidad con tendencia y relaciones de riesgo aprendidas con CatBoost y LightGBM. |
| Edificios | Frecuencia y severidad: 60 %. Modelo de coste total: 40 %. | Incorpora peligro, capital asegurado y características del inmueble junto a un modelo LightGBM. |
| Contenidos | Frecuencia y severidad: 70 %. Modelo de coste total: 30 %. | Combina frecuencia aditiva, distintas estimaciones de severidad y un modelo LightGBM. |

El nivel de la predicción se calibra con los cortes históricos. Los componentes con una evolución de nivel inestable aportan forma al reparto del riesgo y quedan fuera de la referencia de nivel. Los pesos, parámetros y reglas exactas están conservados en la receta y el anexo técnico.

## Cómo contrastamos la propuesta

La comparación respeta el orden temporal: ajustamos con años anteriores y evaluamos en un año posterior. Dentro del primer corte separamos clientes para calibración y selección.

| Evaluación | Periodo de ajuste | Uso del resultado |
| --- | --- | --- |
| Año 2023 | Años 2021 y 2022 | Calibración y comparación inicial de alternativas. |
| Año 2024 | Años 2021 a 2023 | Contraste temporal y diagnósticos de estabilidad. |
| Predicción de 2025 | Años 2021 a 2024 | Archivo que se entrega al concurso. |

Ambos cortes históricos participaron en decisiones de desarrollo. Sus resultados permiten comparar las recetas conservadas, pero no constituyen una prueba final independiente.

Revisamos la pérdida completa por ramo, la influencia de los siniestros grandes, periodos cortos, segmentos de cartera y escenarios de reservas. Los recortes de cola sirven para estudiar pérdidas extremas; la métrica principal conserva todas las pérdidas.

## Resultados y decisiones

La puntuación pública favorece ligeramente a la propuesta principal. El contraste local apunta en la misma dirección, con una diferencia agregada cuya incertidumbre incluye cero. La mejora se presenta con ese alcance.

| Candidato | Validación local sobre coste observado | Puntuación pública del concurso |
| --- | --- | --- |
| Propuesta principal | 0,13788 | 0,12996 |
| Respaldo | 0,13774 | 0,12988 |

Fuentes: comparación local y recibos archivados de ambos candidatos. La métrica es la puntuación Tweedie del concurso; mayor es mejor. Las columnas evalúan muestras y costes de referencia distintos y deben leerse por separado.

La revisión del nivel también importa. En edificios, el coste observado en el último corte supera la predicción. Ese resultado exige revisar la calibración y sus sensibilidades antes de trasladar un cambio al siguiente año.

| Ensayo | Decisión conservada |
| --- | --- |
| Tendencia de severidad por peligro y nuevos pesos en contenidos | Se incorpora a la propuesta por su mejora pequeña en los cortes revisados. |
| Más semillas | La variación observada no justificó sustituir el candidato. |
| Pesos y calibración por segmento | La mejora durante selección no se sostuvo de forma suficiente en el contraste posterior. |
| Deriva de frecuencia y cambio de régimen en lesiones | Quedan como alternativas documentadas; no sustituyen la receta elegida. |
| Clima del mismo año | La variante de la línea alternativa no aportó mejora suficiente para entregarla. |

## Qué aportó la IA y cómo se comprobó

La IA ayudó a explorar incidencias, escribir las reglas de preparación, construir modelos y cuestionar conclusiones. Las revisiones cruzadas detectaron afirmaciones excesivas sobre las reservas y controles del programa que podían continuar pese a archivos incompletos o distintos de los esperados.

Esos controles se corrigieron y se comprobaron con casos válidos y errores intencionados. También se reprodujeron los archivos finales desde los componentes guardados. Los fallos iniciales y sus correcciones se conservan para poder revisar cómo se llegó al resultado.

Claude desarrolló las líneas predictivas de la propuesta y el respaldo. Codex aportó reglas de datos, reconstrucción, contrastes técnicos y consolidación del expediente. El participante dirige el trabajo y debe aprobar sus decisiones. La colaboración entre asistentes no se presenta como validación profesional independiente.

## Lo que falta antes de cerrar

| Asunto | Estado y siguiente decisión |
| --- | --- |
| Coste último y reservas | La suficiencia de reservas sigue sin demostrarse. Hace falta información posterior para contrastarla; mientras tanto se conserva el supuesto y su incertidumbre. |
| Disponibilidad de variables | Debe aclararse cuándo existirían el historial, la información de dispositivos y los datos de clima en una cotización real. |
| Capitales sin confirmación | Se mantienen documentados los 149 casos tratados sin referencia histórica suficiente. Su tratamiento requiere revisión y aceptación de alcance. |
| Reproducción completa | Los archivos finales se reproducen desde componentes guardados. La corrida completa no se pudo recuperar y faltan modelos ajustados guardados; completar la cadena requeriría nuevos ajustes. |
| Revisión y selección | Falta registrar la decisión del participante y confirmar el candidato final en Kaggle. |

Al llegar el nuevo mercado compararemos unidades, cobertura, calidad e información disponible antes de adaptar el modelo. Conservaremos una referencia de la primera semana para explicar qué cambió y qué resultado produjo cada adaptación. La segunda parte todavía no tiene resultados en este informe.

El [anexo técnico](ANEXO_TECNICO_SEMANA1.md) reúne los identificadores de candidatos, las huellas de archivos, los parámetros efectivos, las cifras sin redondear y los enlaces a cada verificación. El repositorio conserva el código y las instrucciones de reproducción. El informe y el video finales incorporarán la adaptación al segundo mercado.
