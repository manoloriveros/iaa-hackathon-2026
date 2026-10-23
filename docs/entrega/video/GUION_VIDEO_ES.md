# Guion del video

Video de cinco minutos para la entrega final. El jurado califica solo los primeros cinco minutos, y la página de envíos pide el enfoque, los resultados, el flujo asistido por IA y la adaptación al mercado nuevo. Este guion cubre la parte 1 en unos 4:46 a 160 palabras por minuto y deja cerca de 0:09 para la adaptación de la semana 2, más el tiempo de la lámina 17, que las láminas de la semana 2 reemplazan; esa parte solo puede grabarse cuando termine la parte 2. La versión en inglés está en `GUION_VIDEO_EN.md`.

## Qué se necesita

- Láminas: `docs/entrega/video/laminas_es.pdf` (17 láminas de 1920 × 1080) o los PNG de `docs/entrega/video/laminas/es/`. Salen de `docs/entrega/datos/cifras_entregables.json`, el mismo archivo del informe y del panel.
- Si cambia alguna cifra (un aporte nuevo en el foro, un ciclo nuevo del enjambre, otra posición en la tabla), hay que regenerar antes de grabar: `python herramientas/cifras_entregables.py --raiz <espacio de trabajo> --salida docs/entrega/datos/cifras_entregables.json` y luego `python herramientas/construir_entrega.py todo`.
- Capturas en vivo opcionales para la lámina 16: una terminal con las órdenes o el panel (`docs/entrega/panel_modelo.html`).

## Escena por escena

| # | Tiempo | Lámina | Narración | En pantalla |
| --- | --- | --- | --- | --- |
| 1 | 0:00–0:15 | Una prima de riesgo para cada periodo de póliza, construida y contrastada con IA | Soy Manuel Rodríguez, actuario, y compito como equipo individual. Este modelo, la Mezcla por peligro, tarifica cada periodo de póliza de 2025. Se construyó con IA y, con la misma intención, se puso a prueba con IA. | Portada con las tres cifras. Si la cámara está activa, este es el momento de mirarla. |
| 2 | 0:15–0:40 | La tarea: el coste último esperado de cada periodo | El objetivo es el coste último esperado de cada periodo, neto de franquicia y recobros. La mayoría de los periodos no cuesta nada, por eso la métrica es un D² Tweedie, donde cero equivale a cobrar a todos el promedio. Una tasa constante por ramo llega a 0,071; nuestro modelo, a 0,138 en 2024, y la entrega final, a 0,13016 en la tabla pública. | Señalar los cuadros de color y después las tres marcas de la escala del D². |
| 3 | 0:40–0:52 | Seis etapas, cada una comprobada | Son seis etapas y cada una se comprueba. El retraso de reporte entra una sola vez, por la exposición de entrenamiento, y cada etapa deja huellas que cualquiera puede verificar. | Recorrer las seis cajas en orden y detenerse en la etapa 3. |
| 4 | 0:52–1:10 | Datos: corregir lo demostrable, declarar lo que no | Los once archivos originales nunca se modifican. La IA auditó las 105 columnas y encontró defectos reales, como claves sin sus ceros iniciales, exposición guardada en días y 604 siniestros duplicados. Ocho reglas reversibles los corrigen, y una reconstrucción independiente coincidió en 148 millones de celdas. | Primero la tabla; luego el flujo de siniestros de abajo (de 163.150 a 160.432). |
| 5 | 1:10–1:20 | Parte de los siniestros de 2024 aún no se conocía | Al cierre de 2024 solo se había reportado el 56 % de las lesiones corporales de autos. Entrenamos con esa exposición efectiva como offset, | Señalar las dos barras cortas, lesiones y hundimiento; la tarjeta de la derecha explica el offset. |
| 6 | 1:20–1:31 | Con el IBNR, 2024 deja de ser una anomalía | y así 2024 deja de parecer barato: 454 observados, 584 con IBNR, en línea con los años anteriores, y 592 en la predicción final de 2025. | Panel de autos: la caída gris a 454, el punto de color en 584 y el círculo hueco en 592. |
| 7 | 1:31–1:45 | La Mezcla por peligro: un modelo, diez componentes | Cada ramo mezcla modelos Tweedie del coste total con frecuencia por severidad por peligro. Cada cambio se juzgó en 2023 y 2024, con y sin las pérdidas más extremas, según criterios escritos de antemano. | Azul es frecuencia × severidad y naranja, coste total; después, las tres tarjetas. |
| 8 | 1:45–2:04 | Ajustado con años pasados, medido en un año posterior | Validamos como se usa una tarifa: ajustar con años pasados y medir un año posterior completo. En 2024 el modelo explica cerca del doble de desviación que una tasa constante, y gana en cada ramo. Después, once experimentos preinscritos, con un backtesting del IBNR, volvieron a probarlo. | A la izquierda, los tres cortes temporales; a la derecha, barras grises frente a azules. |
| 9 | 2:04–2:16 | Ordena el riesgo y se mantiene calibrado | Ordena el riesgo y se mantiene calibrado. Mover las reservas de caso un veinticinco por ciento casi no cambia la métrica, pero mueve el nivel de 2025 hasta un siete por ciento. | En cada panel la línea es la predicción y los círculos, el coste observado. |
| 10 | 2:16–2:36 | La IA se organizó para que una línea contrastara a otra | Ahora, la IA. Dos asistentes, Claude y Codex, trabajaron en tres líneas: modelado, alternativas creativas y contraste. Las hipótesis iban a un foro común con su criterio de aceptación antes de calcular nada, y los fracasos también se publicaban. Las decisiones que llegaron al modelo pasaron por mi autorización. | Seguir fuentes → tres líneas → foro ← enjambre; luego el participante y la compuerta de controles. |
| 11 | 2:36–2:46 | Qué hizo la IA en cada etapa y cómo se comprobó | Cada etapa tuvo su propia comprobación: una segunda implementación recalculó las reglas de datos y una guardia retiró una variable que medía el propio siniestro. | No leer la tabla en voz alta; detenerse en la columna «Cómo se verificó». |
| 12 | 2:46–2:53 | Lo que mejoraba en local no mejoraba en público | Aquí el foro demostró su valor: la puntuación local seguía subiendo mientras la pública bajaba. | Señalar la primera zona sombreada, donde el naranja sube y el azul baja; las sondas de la derecha vuelven en la escena 15. |
| 13 | 2:53–3:16 | El foro propuso juzgar el cuerpo sin sacar la cola | Una línea lo atribuyó a unos pocos siniestros extremos y otra lo convirtió en un criterio. Sin el medio por ciento de periodos más costosos, el D² local ordena como la puntuación pública: 0,83 frente a 0,49. Los dos envíos que siguieron marcaron el máximo público de la búsqueda de modelos, y el segundo es la Mezcla por peligro. | Candidatos grises frente a la Mezcla por peligro en azul; comparar 0,49 a la izquierda con 0,83 a la derecha. |
| 14 | 3:16–3:34 | Un enjambre de agentes auditó el proyecto cada 6 horas | Tres agentes de validación auditaron datos, modelos y gobierno cada seis horas y levantaron veintidós hallazgos. Uno mostró que el paquete podía declarar éxito con archivos faltantes; se corrigió y se probó con 36 casos adversos. Trece siguen abiertos, cada uno con su criterio de cierre. | Barras por área y estado; después las tres tarjetas, primero GOV-007. |
| 15 | 3:34–4:02 | El nivel de 2025: tres factores leídos del tablero público | Los años pasados no miden el nivel de 2025, así que seis sondas lo leyeron de la puntuación pública, en forma cerrada. Una regla de credibilidad fijada antes de mirar convirtió esa lectura en tres factores, S41, que puntuó justo lo previsto, sin reentrenar. Una batería posterior halló el ruido subestimado; corregido, S41 es el único archivo calibrado que supera a la mezcla en esperanza con todas las previas probadas. | En cada panel, las dos sondas y la mezcla fijan la curva; el círculo hueco es el óptimo del público y el lleno, sobre la línea discontinua, el factor de S41. Después, la columna Lectura: parcial en autos, apoyado en edificios y contenidos. |
| 16 | 4:02–4:21 | Los archivos entregados se pueden regenerar y comprobar | Cuarenta y cinco casos de control pasan en tres entornos. Una orden reconstruye el archivo de la mezcla desde los componentes guardados, con el SHA-256 que recibió Kaggle, y otra aplica los tres factores para reconstruir S41. Reentrenar los treinta y seis nodos desde los originales dio el mismo archivo. | Tabla a la izquierda y recibos a la derecha; el último reconstruye S41. Opcional: una terminal con la orden, o 10 segundos del panel (docs/entrega/panel_modelo.html, sección Nivel 2025). |
| 17 | 4:21–4:46 | Lo que aún no podemos demostrar y cómo lo probaremos | Declaramos nuestros límites: una sola valoración de siniestros, que deja las reservas como incertidumbre material; un nivel de 2025 calibrado con un tercio del test, con autos solo en parte respaldado por la evidencia independiente; y una ventaja sobre el envío anterior que no es robusta. Para la semana dos congelamos esta entrega y adaptamos solo donde la evidencia del mercado nuevo lo exija. | Límites a la izquierda y protocolo de la semana 2 a la derecha. Tras la parte 2 esta lámina se reemplaza (ver la sección de la semana 2). |

## Espacio de la semana 2, unos 0:34

Se graba solo con resultados que existan. La lámina 17 se reemplaza por dos láminas hechas con los datos del mercado nuevo y las mismas herramientas:

1. Una lámina sobre lo que cambió en el mercado nuevo: las diferencias encontradas en contrato, unidades, peligros, desarrollo de siniestros y variables, cada una junto a la respuesta que preveía el protocolo (recalibrar, reajustar severidades, reestimar el chain-ladder, actualizar el contrato de variables).
2. Otra sobre lo que logró la adaptación: D² del modelo congelado en el mercado nuevo frente al adaptado, calibración por decil, puntuación pública de la semana 2 y lo que encontraron el foro y el enjambre de validación durante la semana.

Guía de narración (los corchetes se llenan solo con valores medidos): «En el mercado nuevo medimos primero el modelo congelado: [D²]. Las diferencias principales fueron [lista]. Siguiendo el protocolo, [respuesta], y el D² pasó a [valor]. El foro hizo [n] contrastes nuevos y el enjambre levantó [n] hallazgos; [un ejemplo]. De los límites declarados en la parte 1, [cuáles se pusieron a prueba y cómo].»

Si el espacio necesita más de un minuto, conviene acortar primero las escenas 9 y 12: su contenido también está en el informe.

## De dónde sale cada cifra en pantalla

| Cifra | Valor actual | Clave en `cifras_entregables.json` |
| --- | --- | --- |
| Puntuación pública de la entrega final (S41) | 0,13016 | `entrega_final.publico` |
| Envío de Kaggle de S41 | 57531719 | `entrega_final.envio_kaggle` |
| Puntuación pública del modelo solo (S30) | 0,12996 | `s30.publico` |
| Factores de nivel de S41: autos / edificios / contenidos | 0,9962 / 1,0260 / 1,0126 | `entrega_final.factores_calibracion` |
| Ganancia esperada de S41 en el privado frente a la mezcla, tres pares de previas | +0,000019 / +0,000062 / +0,000083 | `sensibilidad_final.esperanza_privado` |
| D² de 2024 fuera de muestra | 0,13788 | `validacion.d2_recalculado.V24.agregado` |
| Tasa constante por ramo, 2024 | 0,07094 | `validacion.referencia_m00.V24.agregado` |
| Periodos de 2025 predichos | 626.639 | `entrega_final.filas` |
| Lesiones de autos reportadas al cierre de 2024 | 56 % | `ibnr.completitud_2024_por_peligro` |
| Prima de autos 2024: observada / con IBNR; predicción 2025 | 454 / 584; 592 | `ibnr.prima_riesgo_por_anio` |
| Correlación de rangos con el público: cuerpo / completo | 0,83 / 0,49 | `publico_vs_local` |
| Aportes y horas del foro | 252 · 124,8 | `foro.aportes, foro.horas` |
| Hallazgos del enjambre: total / abiertos | 22 / 13 | `validacion_ia.hallazgos, validacion_ia.abiertos` |
| Cambio del nivel 2025 con reservas ×0,75 o ×1,25 (mayor ramo): mezcla / S41 | 6,8 % / 5,7 % | `reservas_acotacion.nivel_max_con_b_075_125, calibracion_nivel.evidencia.reservas_S41.nivel_max_b_075_125_S41` |
| Casos de control superados | 45/45 · 45/45 · 45/45 | `controles_paquete.baterias` |

## Antes de grabar

- Comprobar la puntuación pública y la posición en la tabla el mismo día; la portada toma ambas del archivo de datos.
- Mantener un ritmo tranquilo, unas 160 palabras por minuto en español. El video completo debe quedar por debajo de 4:55.
- Contar las decisiones en primera persona y nombrar las herramientas de IA como herramientas («dos asistentes, Claude y Codex»).
- No mostrar credenciales, tokens, datos por fila ni conversaciones privadas. Las láminas y el panel solo muestran agregados.
- Exportar a 1920 × 1080 (MP4, H.264), con subtítulos si el editor lo permite, y verlo una vez a velocidad normal contra el informe.
- Subirlo donde lo pida el formulario de la entrega final; el enlace todavía no se ha publicado.
