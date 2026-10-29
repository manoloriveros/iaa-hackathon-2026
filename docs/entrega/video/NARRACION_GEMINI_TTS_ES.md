# Narración para Gemini TTS: dirección de voz y montaje

Adaptación del archivo español guardado al 28 de octubre de 2026. Voz de Manuel Rodríguez en el contenido; preparación de Codex. El guion base, el PDF y el modelo entregado permanecen intactos.

## Cómo cargarla

La opción recomendada para este proyecto es generar nueve clips con la misma voz predefinida y unirlos en el editor. Es una decisión de montaje: permite corregir una cifra o una interpretación sin regenerar todo el relato. Los marcadores no se envían como parte del texto hablado.

La documentación actual de Gemini 3.8 separa la locución literal y el estilo. En API, el estilo se envía en `speech_metadata.style`; `<short pause>` sirve para una pausa local. Los tags se mantienen en inglés. En una interfaz con campos de estilo y texto, pega cada parte en su campo. [Guía oficial](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/text-to-speech/prompting-guide).

Para modelos anteriores, usa los archivos de texto plano y las instrucciones de estilo que admita esa versión. La sintaxis 3.8 no se presume compatible. Aquí no se usa SSML ni etiquetas inventadas de tiempo o emoción.

Gemini genera voz desde texto; esto es una adaptación para locución, no una transcripción de un audio existente. [Descripción de Google](https://firebase.google.com/docs/ai-logic/generate-speech).

## Voz y expresión

Sugiero probar Charon, descrita por Google como informativa, para una exposición actuarial. La elección es provisional: no se ha escuchado una muestra. El español está admitido por los modelos documentados. [Voces y modelos](https://ai.google.dev/gemini-api/docs/speech-generation).

Perfil editorial: registro medio o medio grave, voz adulta clara, tono conversacional y profesional, energía contenida, articulación precisa y finales de frase naturales. El matiz colombiano debe ser suave. La confianza aparece al explicar decisiones; la cautela, al reconocer los límites.

Estilo base para copiar en el campo de dirección, fuera del texto hablado:

```text
Español colombiano suave. Narración profesional, clara y conversacional; tono sobrio, dicción precisa y énfasis moderado en decisiones y cifras. Ritmo ágil, aproximadamente ciento cuarenta y cinco a ciento cincuenta palabras por minuto.
```

Añade solo la indicación breve de cada escena. El campo no necesita una biografía extensa del narrador. En 3.8, las indicaciones sostenidas van en metadata; los archivos `.gemini38.txt` añaden únicamente pausas locales.

## Marcadores de montaje

Texto original leído: 646 palabras. Adaptación pronunciable: 693, al explicitar cifras. Objetivo: 4:45; margen hasta cinco minutos: quince segundos. Los tiempos se redistribuyen respecto al guion para acomodar los números. Son orientativos y no garantizan duración exacta; no existe aún audio medido.

| Clip | Inicio–fin objetivo | Expresión |
|---|---|---|
| 01 | 00:00–00:16 | Apertura cercana y segura. Destaca la responsabilidad de elegir y explicar las decisiones. |
| 02 | 00:16–01:10 | Explicación didáctica y analítica. Contrasta coste total con frecuencia y severidad. Articula los decimales con precisión; satisfacción contenida al dar el resultado. |
| 03 | 01:10–01:55 | Tono reflexivo y razonado. Resalta la escasez de historia local y la decisión de transferir. Distingue con claridad las dos cifras comparadas. |
| 04 | 01:55–02:28 | Tono preciso y activo. Da énfasis moderado a excluir variables que revelan siniestros y a corregir el error de cálculo. |
| 05 | 02:28–03:08 | Tono metódico y firme. Marca el paso de las pruebas a sus límites; baja ligeramente la inflexión al reconocer resultados adversos. |
| 06 | 03:08–03:47 | Tono sereno y responsable. Explica la regla con calma. Enfatiza «como excepción» y «el riesgo no desapareció», con claridad y sin dramatización. |
| 07 | 03:47–04:09 | Tono transparente y explicativo. Distingue modelo y calibración. Enuncia cada decimal y cierra con cautela al hablar de generalización. |
| 08 | 04:09–04:30 | Tono concreto y práctico. Articula el gasto fijo y el total comercial; contrasta un supuesto con una garantía de suficiencia. |
| 09 | 04:30–04:45 | Cierre cálido y sobrio. Convicción al describir el aporte de la IA y contención al exponer las limitaciones. |

Los archivos `tts_es/01.txt` a `09.txt` son locución limpia, sin rótulos. Los equivalentes `.gemini38.txt` incorporan `<short pause>` entre párrafos. El archivo de texto completo tampoco contiene tiempos ni instrucciones. La hoja JSON es editorial, no una solicitud lista para enviar a una API.

## Narración por clips

### 01 · 00:00–00:16 · El problema actuarial

Dirección, fuera de la locución: Apertura cercana y segura. Destaca la responsabilidad de elegir y explicar las decisiones.

Texto hablado, listo para el campo de texto:

```text
Soy Manuel Rodríguez. Construí primas de riesgo para autos, edificios y contenidos en dos mercados. Usé Clod y Códex para investigar métodos y como apoyo para programar y cuestionar resultados; conservé la responsabilidad de elegir y explicar las decisiones.
```

### 02 · 00:16–01:10 · Qué modelo elegí y por qué

Dirección, fuera de la locución: Explicación didáctica y analítica. Contrasta coste total con frecuencia y severidad. Articula los decimales con precisión; satisfacción contenida al dar el resultado.

Texto hablado, listo para el campo de texto:

```text
En el mercado con cuatro años de historia elegí una combinación por causa de siniestro. Un componente estima el coste total con árboles de aprendizaje automático y distribución Tuídi, que combina ceros y costes positivos. Otro separa cuántos siniestros ocurren y cuánto cuesta cada uno.

Los combiné por ramo porque ningún modelo dominaba en todos: un incendio y una fuga de agua tienen mecanismos diferentes. Así aproveché las interacciones entre variables y la explicación por frecuencia y severidad. La mezcla obtuvo cero coma uno tres ocho de D cuadrado frente a cero coma cero siete uno de una tasa por ramo; la entrega calibrada alcanzó cero coma uno tres ocho seis cuatro en el privado, cuarta entre cincuenta y cuatro equipos. Durante la primera semana, nuestros envíos también llegaron al primer puesto público.
```

### 03 · 01:10–01:55 · Cómo adapté el método al mercado nuevo

Dirección, fuera de la locución: Tono reflexivo y razonado. Resalta la escasez de historia local y la decisión de transferir. Distingue con claridad las dos cifras comparadas.

Texto hablado, listo para el campo de texto:

```text
El segundo mercado tenía solo dos años de datos. Además, el negocio nuevo pasó del catorce por ciento de las filas históricas al setenta y seis por ciento en dos mil veinticinco. Reentrenar todo desde cero podía confundir escasez de experiencia con diferencias de riesgo.

Preferí transferir relaciones aprendidas en el mercado con más historia, usando las variables comunes. Combiné predicciones transferidas y añadí ajustes locales de siniestralidad previa y variables propias. Les di credibilidad limitada cuando había poca información. En la comparación histórica de dos mil veintitrés, la transferencia dio cero coma uno dos uno frente a cero coma cero ocho tres del mejor modelo entrenado solo con datos locales.
```

### 04 · 01:55–02:28 · La IA en datos y decisiones de variables

Dirección, fuera de la locución: Tono preciso y activo. Da énfasis moderado a excluir variables que revelan siniestros y a corregir el error de cálculo.

Texto hablado, listo para el campo de texto:

```text
La IA ayudó a escribir controles y a contrastar hipótesis. Corregimos identificadores sin ceros iniciales, exposiciones con distintas convenciones y capitales fuera de escala.

También cuestionamos variables demasiado predictivas. Los contactos con atención al cliente podían revelar siniestros del propio periodo: los excluí. Cada corrección quedó registrada y comprobada. El flujo también detectó un factor de calibración elevado al cuadrado por error y lo corrigió antes del envío. El valor de la IA estuvo en construir y desafiar los cálculos.
```

### 05 · 02:28–03:08 · Cómo puse a prueba los resultados

Dirección, fuera de la locución: Tono metódico y firme. Marca el paso de las pruebas a sus límites; baja ligeramente la inflexión al reconocer resultados adversos.

Texto hablado, listo para el campo de texto:

```text
Para juzgar los cambios, separé años y agrupé clientes y direcciones relacionados. En la revisión de la comparación histórica, completitud, categorías, árboles y ajustes se aprendieron excluyendo la información reservada para evaluar. Alteramos deliberadamente esos datos y comprobamos que no cambiaran los modelos pertinentes.

También contrastamos modelos con y sin factores, retiramos grupos influyentes y probamos cincuenta escenarios de reservas y retraso de reporte. La diferencia global conservó signo positivo, con la fuente congelada. Hubo resultados adversos: el coste tardío de lesiones corporales superó lo previsto. Los cortes también orientaron la selección; esas pruebas acotan lo que puedo concluir.
```

### 06 · 03:08–03:47 · Qué significa una salvaguarda y su excepción

Dirección, fuera de la locución: Tono sereno y responsable. Explica la regla con calma. Enfatiza «como excepción» y «el riesgo no desapareció», con claridad y sin dramatización.

Texto hablado, listo para el campo de texto:

```text
Una salvaguarda es una condición previa para aceptar un cambio. Exigí que la mejora global no ocultara un deterioro relevante en pólizas nuevas, considerando su intervalo de incertidumbre.

La transferencia mejoró globalmente, pero no acreditó esa protección. Después de ver el resultado, flexibilicé la regla: acepté una diferencia puntual no negativa sin exigir el límite inferior previsto. Levantar esa exigencia permitió continuar como excepción; el riesgo no desapareció. En los factores propios, la mejora también se concentra en renovación y no demuestra estabilidad en negocio nuevo. Conservé la entrega con ese alcance exploratorio.
```

### 07 · 03:47–04:09 · Qué papel tuvieron las sondas

Dirección, fuera de la locución: Tono transparente y explicativo. Distingue modelo y calibración. Enuncia cada decimal y cierra con cautela al hablar de generalización.

Texto hablado, listo para el campo de texto:

```text
Separé la construcción del modelo de la calibración final. Usé envíos controlados al tablero para ajustar nivel y dispersión; su respuesta también influyó en algunos cambios del modelo. Por eso, cero coma uno seis nueve uno cuatro es un resultado público condicionado por esas decisiones, que no demuestra por sí solo generalización.
```

### 08 · 04:09–04:30 · Del riesgo a la prima comercial

Dirección, fuera de la locución: Tono concreto y práctico. Articula el gasto fijo y el total comercial; contrasta un supuesto con una garantía de suficiencia.

Texto hablado, listo para el campo de texto:

```text
Convertí las predicciones de veinte referencias en prima comercial con los gastos proporcionados. Apliqué ochenta y cinco unidades fijas por póliza, sin prorratearlas. El total fue de veinte mil ochocientas unidades con dos centésimas. El margen de beneficio del ocho por ciento es un supuesto, no una garantía de suficiencia.
```

### 09 · 04:30–04:45 · Alcance de la IA y del resultado

Dirección, fuera de la locución: Cierre cálido y sobrio. Convicción al describir el aporte de la IA y contención al exponer las limitaciones.

Texto hablado, listo para el campo de texto:

```text
La IA también ayudó a construir tableros y preparar traducciones y presentaciones. Amplió mi capacidad de analizar y comunicar. La evidencia muestra una mejora global, con límites en negocio nuevo, reservas y disponibilidad histórica de datos.
```

## Pronunciación y cambios de oralidad

| Escrito en el guion | Lectura preparada |
|---|---|
| Claude | Clod |
| Codex | Códex |
| Tweedie | Tuídi |
| 0,13864 | cero coma uno tres ocho seis cuatro |
| 0,16914 | cero coma uno seis nueve uno cuatro |
| 0,138 | cero coma uno tres ocho |
| 0,071 | cero coma cero siete uno |
| 0,121 | cero coma uno dos uno |
| 0,083 | cero coma cero ocho tres |
| 20.800,02 | veinte mil ochocientas unidades con dos centésimas |
| 85 | ochenta y cinco |
| 54 | cincuenta y cuatro |
| 14 | catorce |
| 76 | setenta y seis |
| 2023 | dos mil veintitrés |
| 2025 | dos mil veinticinco |

El primer puesto público se contextualiza como hito de envíos durante la primera semana; se conserva el cuarto puesto privado de la entrega seleccionada. La cronología del informe acredita primeros puestos públicos al enviar candidatos. Esto evita atribuir un primer puesto definitivo al mismo archivo sin su contexto.

Para comprobar el resultado, escucha especialmente las cifras decimales, los nombres y la negación en «no acreditó esa protección». El tiempo final se comprueba con los clips reales y el montaje. Las pausas de 3.8 no se presentan aquí como silencios de un número exacto de milisegundos.

## Fuentes y trazabilidad

Guion usado: `docs/entrega/video/GUION_VIDEO_ES.md`. SHA-256: `65049a236ee81285dc8f6f225b2fa426b8e4718b24d974831e48af52e703bcbc`. Se usó el texto real guardado, incluidas sus ediciones posteriores al índice. Copia de ese texto en `privado/guion_video/20261028T150122Z/antes/`. La adaptación no sustituye el guion original.

Documentación de Google consultada el 28 de octubre de 2026:

- [Separación de texto literal/metadata, modelos, voz predefinida Charon informativa y sintaxis Interactions 3.8](https://ai.google.dev/gemini-api/docs/speech-generation).
- [Estilo en speech_metadata.style; pausas cortas con etiquetas en inglés; instrucciones breves y distinción por versión](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/text-to-speech/prompting-guide).
- [Generación de voz frente a transcripción y diferencias de soporte entre familias de modelos](https://firebase.google.com/docs/ai-logic/generate-speech).
