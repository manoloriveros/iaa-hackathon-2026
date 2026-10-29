# Guion del video: cómo elegí y contrasté la prima de riesgo

Edición española del 28 de octubre de 2026. Voz de Manuel Rodríguez; reescritura de Codex con las metodologías y evidencias registradas por Claude y Codex. El modelo y la adaptación abren el relato; la IA se muestra en tareas concretas y las validaciones se conectan con decisiones. El cierre comunica limitaciones observadas, sin una lista de trabajo futuro.

Duración objetivo: 4:45, con quince segundos de margen hasta cinco minutos. La narración tiene 641 palabras, unas 135 por minuto. Los tiempos son una previsión de lectura y montaje, sin medición de una grabación real. Se narra únicamente el texto marcado con `>`. Los rótulos no se leen completos.

## Escena 1 · 0:00-0:17 · El problema actuarial

> Soy Manuel Rodríguez. Construí primas de riesgo para autos, edificios y contenidos en dos mercados. Usé Claude y Codex para investigar métodos y como apoyo en programar y cuestionar resultados; conservé la responsabilidad de elegir y explicar las decisiones.

En pantalla: «Una prima de riesgo por periodo de póliza». Debajo: «Coste último esperado, antes de gastos · Datos sintéticos · Dos mercados». Distinguir el objetivo último del coste observado en los archivos.

## Escena 2 · 0:17-1:02 · Qué modelo elegí y por qué

> En el mercado con cuatro años de historia elegí una combinación por causa de siniestro. Un componente estima el coste total con árboles de aprendizaje automático y distribución Tweedie, que combina ceros y costes positivos. Otro separa cuántos siniestros ocurren y cuánto cuesta cada uno.
>
> Los combiné por ramo porque ningún modelo dominaba en todos: un incendio y una fuga de agua tienen mecanismos diferentes. Así aproveché las interacciones entre variables y la explicación por frecuencia y severidad. La mezcla obtuvo 0,138 de D cuadrado frente a 0,071 de una tasa por ramo; la entrega calibrada alcanzó 0,13864 en el privado, cuarta entre 54 equipos, y en la escala pública quedó en primer lugar.

En pantalla, primero el método:

| Componente | Qué aporta a la prima |
| --- | --- |
| Árboles de coste total: LightGBM y CatBoost, con objetivo Tweedie | Relaciones e interacciones entre características del riesgo |
| Frecuencia × severidad por causa de siniestro | Separa mecanismos y permite estudiar la evolución de la severidad |
| Combinación por ramo | Aprovecha fortalezas distintas de los componentes |

Después, sustituir el esquema por dos tarjetas: «Comparación histórica 2024: 0,138 frente a 0,071» y «Resultado privado, parte 1: 0,13864 · 4.º de 54». Pie: «Los cortes históricos también se usaron para elegir modelos. El privado corresponde a la entrega calibrada». D² Tweedie, potencia 1,5; no es un porcentaje de aciertos.

## Escena 3 · 1:02-1:46 · Cómo adapté el método al mercado nuevo

> El segundo mercado tenía solo dos años de datos. Además, el negocio nuevo pasó del 14 por ciento de las filas históricas al 76 por ciento en 2025. Reentrenar todo desde cero podía confundir escasez de experiencia con diferencias de riesgo.
>
> Preferí transferir relaciones aprendidas en el mercado con más historia, usando las variables comunes. Combiné predicciones transferidas y añadí ajustes locales de siniestralidad previa y variables propias. Les di credibilidad limitada cuando había poca información. En la comparación histórica de 2023, la transferencia dio 0,121 frente a 0,083 del mejor modelo entrenado solo con datos locales.

En pantalla: «Más historia → árboles con variables comunes → ajustes con experiencia local». Definir negocio nuevo como primer año de póliza con la aseguradora, sin equipararlo a una dirección nunca vista.

Mostrar las decisiones de adaptación: edad por bandas y variables comunes; historial de siniestros y bonificación; factores propios de género, teletrabajo y segmento de marketing con credibilidad. Explicar credibilidad como peso limitado a una señal con poca experiencia. No afirmar que estos factores tienen respaldo uniforme por segmento.

Tarjeta final: «Transferencia frente a aprendizaje solo local · Comparación histórica 2023 por cliente: 0,121 frente a 0,083». Pie: «Comparación utilizada en la selección, anterior a corregir toda la cadena; no es una evaluación independiente posterior». Esta cifra explica la elección histórica; no se presenta como prueba nueva de la receta final completa.

## Escena 4 · 1:46-2:21 · La IA en datos y decisiones de variables

> La IA ayudó a escribir controles y a contrastar hipótesis. Corregimos identificadores sin ceros iniciales, exposiciones con distintas convenciones y capitales fuera de escala.
>
> También cuestionamos variables demasiado predictivas. Los contactos con atención al cliente podían revelar siniestros del propio periodo: los excluí. Cada corrección quedó registrada y comprobada. El flujo también detectó un factor de calibración elevado al cuadrado por error y lo corrigió antes del envío. El valor de la IA estuvo en construir y desafiar los cálculos.

En pantalla: una captura real de control con «Hallazgo → contraste → corrección → comprobación». Mostrar sucesivamente la recuperación del cruce con clientes, la exclusión de contactos y la fórmula corregida, sin código pequeño o datos privados por fila.

Rótulo: «Originales preservados · Correcciones reversibles · Uso de IA verificado». Las verificaciones entre asistentes son propias, no revisión profesional independiente. No afirmar ahorro de tiempo medido.

## Escena 5 · 2:21-3:03 · Cómo puse a prueba los resultados

> Para juzgar los cambios, separé años y agrupé clientes y direcciones relacionados. En la revisión de la comparación histórica, completitud, categorías, árboles y ajustes se aprendieron excluyendo la información reservada para evaluar. Alteramos deliberadamente esos datos y comprobamos que no cambiaran los modelos pertinentes.
>
> También contrastamos modelos con y sin factores, retiramos grupos influyentes y probamos cincuenta escenarios de reservas y retraso de reporte. La diferencia global conservó signo positivo, con la fuente congelada. Hubo resultados adversos: el coste tardío de lesiones corporales superó lo previsto. Los cortes también orientaron la selección; esas pruebas acotan lo que puedo concluir.

En pantalla, un control por vez, vinculado a su decisión:

| Comprobación | Qué se aprendió |
| --- | --- |
| Corte temporal y grupos de clientes/direcciones | Distinguir pasado, evaluación y dependencias entre registros |
| Preparación y aprendizaje excluyendo lo retenido; alteración adversa de costes | Verificar el aislamiento computacional de las recetas históricas comparadas |
| Con y sin factores propios | Ganancia global aproximada de +0,0023 a +0,0024 de D²; no equivale a mejora uniforme |
| Retirada retrospectiva de grupos favorables | Entre 37 y 42 de 36.408 grupos bastan para anular la ganancia según la base |
| 50 escenarios: 45 de coste/reservas/cola y cinco de completitud | Mejora global positiva con precios fijos y destino reaprendido; árboles y curvas fuente congelados |

Pie: «Las vistas comparten etiquetas; no son confirmaciones independientes. Los intervalos condicionan los modelos aprendidos; no repiten aprendizaje ni búsqueda histórica. La rama histórica evaluada no equivale a toda la configuración de producción».

Mostrar brevemente el contraste adverso: «Lesiones corporales, cohorte emergente 2023: coste tardío +42,7 % frente al previsto · IC90: +2 % a +102 %». El coste observado al cierre de 2024 no es coste último. Los escenarios son deterministas, no probabilidades ni intervalos de confianza. La reproducción de los archivos históricos comprueba trazabilidad, sin aportar observaciones predictivas independientes.

## Escena 6 · 3:03-3:45 · Qué significa una salvaguarda y su excepción

> Una salvaguarda es una condición previa para aceptar un cambio. Exigí que la mejora global no ocultara un deterioro relevante en pólizas nuevas, considerando su intervalo de incertidumbre.
>
> La transferencia mejoró globalmente, pero no acreditó esa protección. Después de ver el resultado, flexibilicé la regla: acepté una diferencia puntual no negativa sin exigir el límite inferior previsto. Levantar esa exigencia permitió continuar como excepción; el riesgo no desapareció. En los factores propios, la mejora también se concentra en renovación y no demuestra estabilidad en negocio nuevo. Conservé la entrega con ese alcance exploratorio.

En pantalla, explicar la regla con palabras antes de mostrar números:

| Momento | Regla y significado |
| --- | --- |
| Antes de comparar la transferencia | Diferencia no negativa y límite inferior del intervalo al 95 % no inferior a −0,001 en negocio nuevo |
| Resultado observado de ese contraste | Diferencia aproximada +0,013, pero límite inferior −0,011: la protección no se acreditó |
| Excepción después de conocer el resultado | Se aceptó el resultado puntual no negativo sin exigir aquel límite inferior. La excepción no demuestra protección del segmento |

Rótulo: «Regla del proyecto, no umbral impuesto por la IAA». Separar este contraste de transferencia del contraste posterior de factores propios. En este último, las tres recetas históricas incumplen la protección de negocio nuevo; renovación explica el 98,09–99,39 % del aporte neto. La reponderación con composición de 2025 tiene intervalos que cruzan cero. No afirmar que se levantaron todos los controles ni que la excepción corrigió el fallo estadístico.

## Escena 7 · 3:45-4:08 · Qué papel tuvieron las sondas

> Separé la construcción del modelo de la calibración final. Usé envíos controlados al tablero para ajustar nivel y dispersión; su respuesta también influyó en algunos cambios del modelo. Por eso, 0,16914 es un resultado público condicionado por esas decisiones, que no demuestra por sí solo generalización.

En pantalla: «Modelo: relaciones de riesgo» y «Calibración: nivel y dispersión de las predicciones». Definir una sonda como envío de prueba multiplicado por un factor conocido, cuya puntuación informa del ajuste que favorece el tablero.

Tarjeta: «Público inicial: 0,15390 → Entrega conservada: 0,16914». Pie: «Los pasos de calibración suman 0,01044 y los del modelo 0,00480 según el orden de la secuencia. El reparto tiene interacciones y no es una atribución causal». Evitar presentar la estructura o el archivo final como independientes del tablero. La parte 1 tiene privado observado; en la parte 2 la evidencia mostrada aquí es pública e histórica.

## Escena 8 · 4:08-4:27 · Del riesgo a la prima comercial

> Convertí las predicciones de veinte referencias en prima comercial con los gastos proporcionados. Apliqué 85 unidades fijas por póliza, sin prorratearlas. El total fue 20.800,02 unidades. El margen de beneficio del ocho por ciento es un supuesto, no una garantía de suficiencia.

En pantalla: «Prima del periodo + catástrofe de hogar + 85 CU», dividido entre «1 − gastos proporcionales − comisión − impuesto − margen». Mostrar 15 % de gasto variable, 8 % de impuesto y 8 % de beneficio; comisión de 20 % con corredor y cero en directo; catástrofe 12 % de la prima de riesgo de hogar. Los gastos no entran en la predicción enviada al concurso. No volver a multiplicar el riesgo del periodo por exposición.

## Escena 9 · 4:27-4:45 · Alcance de la IA y del resultado

> La IA también ayudó a construir tableros y preparar traducciones y presentaciones. Amplió mi capacidad de analizar y comunicar. La evidencia muestra una mejora global, con límites en negocio nuevo, reservas y disponibilidad histórica de datos.

En pantalla: una captura real de tablero con controles y resultados, seguida de material de traducción y guion/láminas identificado por su fecha. Se presenta preparación previa, sin afirmar equivalencia final del inglés o existencia de un video ya grabado. Cerrar con nombre y repositorio de la entrega.

Rótulo final: «Decisión actuarial documentada · Incertidumbre explícita · Revisión propia con IA». Las revisiones entre asistentes no son revisión profesional independiente. Mostrar límites observados, sin una lista de próximas tareas o promesas de nuevas validaciones.

## Notas de realización y alcance

La elección metodológica se explica con comparaciones históricas y razones actuariales; no se declara óptima para todas las poblaciones. La calibración con el tablero y las excepciones de selección se conservan como hechos. La referencia declarada permanece intacta; sus códigos internos no se leen ni se usan en rótulos. Los nombres de algoritmos identifican métodos y se acompañan de su función.

Priorizar uno o dos mensajes legibles por pantalla. Las tablas son una guía de producción: no deben mostrarse todas simultáneamente ni leerse completas. Narración, rótulos y subtítulos deben usar el mismo tipo de muestra y las mismas unidades. La duración indicada es estimada. La fuente inglesa y las láminas históricas conservan su fecha, sin atribuirles la equivalencia de esta edición.

El PDF conserva su archivo y contenido. El cotejo del guion con sus primeras cinco páginas se registra por separado de la edición del PDF. La revisión integral de la configuración de producción figura en curso al corte y no se usa aquí para afirmar resultados favorables o cierre de validación. Las reconstrucciones históricas y las recetas de comparación conservan sus alcances respectivos.

## Evidencia para producción, fuera de narración y rótulos

Rutas relativas al repositorio, salvo el PDF, relativo a la raíz del proyecto:

- Rúbrica IAA: página Evaluation de la parte 2, consultada el 28 de octubre de 2026: rendimiento/adaptación 40 %, IA 25 %, validación/controles 20 %, comunicación/documentación 15 %. La distribución de escenas es editorial, no una fórmula de puntuación.
- Escenas 1–3: `docs/entrega/informe/INFORME_ES.md`, secciones de métodos y decisiones históricas; `docs/archivo/semana1/RESULTADOS_PRIVADOS_SEMANA1.md`; PDF `Hackaton/Semana 2/Claude/informe_final_20261026/informe_final_IAA2026_es.pdf`, páginas 1 y 3. Los documentos antiguos conservan su fecha y no sustituyen la edición final indicada.
- Escena 4: PDF, páginas 2 y 4, correcciones de claves/exposición/capitales, exclusión de contactos y fórmula de nivel. No confundir verificación propia con revisión independiente.
- Escena 5: `docs/semana2/F3C_CADENA_PROTEGIDA_REEVALUACION.md`, `docs/semana2/F3C_A1_MEZCLA_PROTEGIDAS_Y_ESCENARIOS.md` y `registro/validacion_cadena_f3c_A1_mezcla_actual.json`. Las tres vistas de comparación comparten etiquetas. La nueva configuración completa tiene un alcance distinto: `registro/semana2_F3c_completo_validacion_actual.json`, en curso, sin resultados favorables atribuidos en este guion.
- Escena 6: PDF, páginas 3–4; política de selección y excepción de la transferencia frente a referencia. Separar de la protección posterior de factores. La enmienda tras conocer el resultado no se presenta como una regla original intacta.
- Escena 7: PDF, página 3, y secuencia pública registrada. El uso del tablero también influyó en decisiones estructurales; no se presenta una entrega ajena a las sondas.
- Escena 8: PDF, página 5, y `privado/pendientes_F3c/20261026_cierre12_recuperado/veinte_primas_gasto_por_poliza.json`, filas nominales de la referencia declarada. Veinte precios sin cambios, total 20.800,02 CU y gasto fijo 85 CU por póliza.
- Escena 9: `docs/panel_revision.html`, `docs/entrega/panel_modelo.html`, `docs/entrega/panel_analisis.html`, textos ingleses y láminas existentes. Inventario de artefactos previos en `privado/edicion_informe_final/20261027T201801Z/evidencia_usos_IA.json`.

Edición y comprobación: `registro/guion_video_actual.json`. El texto no autoriza envíos, publicación, cambios de modelo o nuevas ejecuciones de entrenamiento. Los archivos por fila, los identificadores individuales y las conversaciones privadas no se muestran en el video.
