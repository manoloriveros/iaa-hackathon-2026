# El modelo final de la parte 1: S41, la Mezcla por peligro con nivel calibrado

Presento el modelo que elegí para la primera semana y las hipótesis con las que lo interpreto. La descripción técnica procede del trabajo asistido por IA y conserva sus fuentes.

Documento de Claude (sesión Cowork de las sondas), 23 de octubre de 2026, 10:30 de Bogotá, a pedido del participante: describir S41 como el modelo único de la entrega, sin tratarlo como una variante entre varias. Las cifras salen de los registros que se citan en el anexo; las decisiones humanas y las de IA se distinguen en cada paso. Es trabajo de IA, sin revisión humana independiente.

## Qué predice y con qué se mide

Con S41 predigo, para cada uno de los 626.639 periodos de póliza de 2025 del test (254.986 de autos, 184.155 de edificios del hogar y 187.498 de contenidos), el coste último esperado de los siniestros ocurridos dentro del periodo, neto de franquicia y recuperaciones y sin siniestros rechazados. Es una prima de riesgo por periodo en unidades monetarias ficticias, no una prima comercial. El concurso la evalúa con el D² de la desviación Tweedie de potencia 1,5, a maximizar; el marcador público usa el 33 % de las filas y el privado, el 67 % restante; la evaluación global incorpora también el juicio del jurado.

Mi entrega es el archivo `S41_nivel_credibilidad.csv`, marcado por mí como selección final en Kaggle el 23 de octubre hacia las 09:45 de Bogotá, con puntuación pública 0,13016 (primer puesto al marcarlo; el segundo tenía 0,13003). Suma 213.685.158 CU: 118.454.953 en autos, 76.299.719 en edificios y 18.930.486 en contenidos; por año de exposición, 592 CU en autos, 508 en edificios y 126 en contenidos.

## En qué consiste, de los datos a la predicción

S41 es una cadena de cinco pasos. Los cuatro primeros son la Mezcla por peligro (S30), el modelo definitivo de D99; el quinto es la calibración del nivel con la que S30 se convierte en S41.

La capa de datos. Los once archivos originales no se modifican; sobre ellos se aplican ocho reglas deterministas y reversibles con bitácora por fila (rellenar los identificadores de cliente de autos que habían perdido ceros, unificar la convención de exposición a días inclusivos entre 365, dividir entre mil 2.073 capitales con salto de escala confirmado por la historia de la póliza, unificar mayúsculas de la construcción, recalcular la edad del tomador al inicio del periodo, excluir 604 siniestros duplicados, marcar 2.742 pólizas con rechazo de renovación y 413 siniestros anteriores al primer periodo observado). Para modelar, el capital de las 3.527 filas extremas de hogar se divide entre mil por una regla idempotente que solo mira la propia fila (contrato de F0, D66).

La etiqueta y el desarrollo. Cada siniestro aceptado se asigna a su periodo por póliza, ramo y fecha de ocurrencia; la etiqueta T0 es el incurrido neto de recuperaciones valorado al 31 de diciembre de 2024 (160.432 siniestros, 741,2 millones de CU). Como los siniestros tardíos de 2024 aún no se han reportado, el modelo no corrige la etiqueta: reduce la exposición efectiva de cada periodo según la completitud de reporte estimada con un chain-ladder de conteos por peligro (en autos el coste de 2024 está un 22,7 % por debajo de su nivel último). Entrenar con esa exposición como offset equivale a predecir a nivel último sin tocar los importes observados.

Los predictores. La matriz F0 declara, columna por columna, en qué fecha estaría disponible cada dato: contrato y características físicas del riesgo; historia de siniestros de la propia póliza anterior al corte; clima de los años estrictamente anteriores; información condicionada como telemática; y la prima tarifada actual como bloque aparte. Quedan fuera por contrato los contactos con el servicio al cliente (miden el siniestro del propio periodo y cambian de distribución en 2025), la decisión de renovación y las marcas de auditoría.

Los componentes y su mezcla. En cada ramo conviven dos familias: modelos de coste total con pérdida Tweedie y modelos de frecuencia por peligro multiplicados por una severidad por peligro con tendencia. Se entrenan con 2021–2024, con la mitad de calibración de 2023 para la parada temprana y los cortes V23 (predecir 2023 con 2021–2022) y V24 (predecir 2024 con 2021–2023) para elegir pesos. La tabla recoge la mezcla final, con pesos elegidos por la peor de las dos mejoras en V23 y V24 frente al candidato anterior.

| Ramo | Componentes de la Mezcla por peligro | Peso |
| --- | --- | ---: |
| Autos | CatBoost Tweedie sobre todos los bloques, cuatro semillas | 0,2 |
| Autos | CatBoost Poisson por peligro con severidad gamma por valor y antigüedad del vehículo y tendencia de severidad por peligro | 0,6 |
| Autos | Dos LightGBM Tweedie (completo y reducido) | 0,1 y 0,1 |
| Edificios | LightGBM Tweedie con siete variables de historia propia y hojas de al menos mil filas | 0,4 |
| Edificios | CatBoost Poisson por peligro con severidad gamma por capital y sótano y tendencia por peligro | 0,3 |
| Edificios | Frecuencia aditiva por peligro con la misma severidad | 0,3 |
| Contenidos | LightGBM Tweedie con las siete variables de historia | 0,3 |
| Contenidos | Modelo aditivo por peligro con severidad modelada | 0,3 |
| Contenidos | Frecuencia aditiva de cuatro semillas con severidad gamma ampliada con covariables físicas | 0,4 |

En autos las relatividades se amplían con el exponente 1,09 y la elasticidad de exposición es 0,95; en contenidos la elasticidad es 0,95; en edificios no hay transformación de forma. Cada componente se reescala al total de referencia del ramo antes de mezclar, y el nivel de 2025 recibe una sola vez el factor de año siguiente f = Σ(y/√μ)/Σ√μ, el multiplicador que minimiza la desviación Tweedie 1,5, promediado entre los cortes 2023 y 2024.

El quinto paso: el nivel calibrado con la experiencia de 2025. El factor de año siguiente de S30 difiere entre los dos cortes (en edificios, 1,059 en 2023 y 1,134 en 2024), así que el nivel de 2025 era la mayor incertidumbre que quedaba. Para medirla se enviaron seis archivos de sonda, S30 con un solo ramo multiplicado por 0,90 o por 1,10. Para la desviación Tweedie 1,5, el D² del público como función de ese factor c tiene forma cerrada, D²(c) − D²(1) = −4·[S1·(c^−½ − 1) + S2·(c^½ − 1)]/N, con S1 = Σ y/√μ y S2 = Σ √μ sobre las filas públicas del ramo; dos puntos por ramo bastan para despejar S1 y S2 y con ellos el factor óptimo del público, c* = S1/S2. Ese óptimo lleva el ruido de un tercio de las filas, así que S41 aplica solo la fracción creíble, fijada antes de ver las puntuaciones: c_Z = 1 + Z·(c* − 1), con Z = τ²/(τ² + σ²), τ la incertidumbre previa del nivel del ramo (la mitad de la distancia entre los factores de 2023 y 2024, ampliada en autos y contenidos con la evidencia sobre IBNR y recuperaciones) y σ el ruido medido por bootstrap sobre 2024.

| Ramo | f 2023 | f 2024 | Nivel de S30 (media) | c* del público | τ previa | σ ruido 33 % | Z | Factor aplicado en S41 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Autos | 0,986 | 1,005 | 0,996 | 0,9774 | 1,5 % | 3,4 % | 0,166 | 0,9962 |
| Edificios | 1,059 | 1,134 | 1,097 | 1,0751 | 3,5 % | 4,8 % | 0,346 | 1,0260 |
| Contenidos | 1,078 | 1,092 | 1,085 | 1,0840 | 1,5 % | 3,6 % | 0,150 | 1,0126 |

S41 es, por tanto, S30 con autos multiplicado por 0,9962, edificios por 1,0260 y contenidos por 1,0126. Nada más cambia: ni las relatividades, ni los pesos, ni la forma.

## Por qué lo elegí para el concurso

Separa lo que se puede aprender de lo que hay que suponer. La parte difícil de una prima de riesgo es ordenar bien las pólizas y repartir el coste entre peligros; eso lo hacen los componentes, entrenados con historia y validados en dos cortes temporales con contrastes pareados. El nivel del año, que ningún corte histórico puede enseñar, se trata como lo que es, una incertidumbre, con una regla explícita para incorporar la única medida disponible de 2025.

La calibración coincide en dirección con la evidencia histórica que usé como contexto. Esas fuentes no son una revisión independiente. Antes de las sondas, el backtesting del IBNR y el hallazgo de que ningún siniestro abierto de autos lleva recuperaciones apuntaban a un nivel de autos algo alto; la prima escrita de 2025 (+5,3 % en edificios, +5,4 % en contenidos), la severidad creciente de hogar y el salto del factor de edificios entre 2023 y 2024 apuntaban a niveles de hogar más altos. Las sondas apuntaron en esa dirección: autos un 2,3 % por debajo del nivel de S30, edificios un 7,5 % por encima y contenidos un 8,4 % por encima. La coincidencia de dirección es un indicio; no demuestra que la señal supere el ruido ni corrige la reutilización de los cortes.

Elegí esta variante como la opción más prudente bajo los escenarios estudiados. Después de S41 se probaron en el público una revisión de la credibilidad con los propios resultados (S42, 0,13033) y una calibración adicional de la dispersión de autos (S43, 0,13048). Las dos puntúan más en el público y las dos se descartaron: la batería de sensibilidad (D103) midió el ruido de la sonda frente a la parte no vista, en lugar de frente al total de 2024, y con esa corrección S41 tiene mayor esperanza en el privado que S43 bajo los tres pares de previas (media +0,0000376), no queda por debajo de S30 bajo ninguno y tiene menos de la mitad de dispersión. Acepté esa recomendación por robustez, no por una ganancia segura.

El mecanismo está entendido, no solo ajustado. La puntuación pública de S41 se calculó antes de enviarlo con la forma cerrada y coincidió al quinto decimal (0,13016); lo mismo ocurrió con S42 y con S43. Esa concordancia apoya el cálculo usado para la calibración, pero no identifica por completo el scorer oficial ni sus posibles pesos.

Se reproduce desde los originales. S30 se reconstruyó en la nube desde los once archivos con todos sus estimadores guardados (D97: CSV con el SHA entregado; 19 de 181 huellas intermedias con diferencias intermedias registradas en ese corte), y el paso de nivel es aritmética que `sonda_nivel.py resolver` repite con las seis puntuaciones registradas.

## Las hipótesis que sostienen la predicción

Cada hipótesis se enuncia con lo que pasaría si fallara, porque eso es lo que un revisor necesita para decidir cuánto confiar.

La etiqueta T0 es un buen sustituto del coste último una vez corregida la exposición por completitud de reporte. Supone que las reservas de caso de los siniestros abiertos no tienen sesgo sistemático. Con una sola valoración no es verificable; D95 lo deja como incertidumbre material en los tres ramos, y un error del 3,7 % en la reserva de autos movería su nivel un 1 %.

El desarrollo de los siniestros se captura con la exposición efectiva y una sola vez. Supone que los conteos tardíos se comportan como en las cohortes anteriores (factores de coste de 2024 de 1,2877 en autos, 1,0796 en edificios y 1,0317 en contenidos) y que no se añade un segundo IBNR en ninguna parte de la cadena. El backtesting mostró el IBNR de lesiones sobrestimado al cierre de año en 2022 y 2023; la calibración del nivel absorbe parte de ese sesgo.

La pérdida Tweedie de potencia 1,5 es adecuada para ajustar, aunque la severidad dentro de cada peligro sea más dispersa. Por eso conviven modelos de coste total y modelos de frecuencia por peligro con severidad aparte, que tratan mejor las colas de lesiones corporales y hundimiento.

Las relatividades aprendidas en 2021–2024 valen para 2025. El público lo apoya en hogar y lo matiza en autos (prefiere relatividades un 8 % menos dispersas que las de S30); S41 conserva la dispersión de S30 porque la evidencia fuera del marcador no apoya el cambio y su efecto esperado es menor que el ruido.

Los maestros de clientes y direcciones son estables, el clima útil es el de los años anteriores al corte y la historia propia se conoce hasta el 31 de diciembre de 2024. Es el contrato de disponibilidad de F0; usar el clima realizado de 2025, aunque está en los datos, se midió y no mejora el total de ningún ramo.

Los 3.527 capitales extremos de hogar están en una escala mil veces mayor. Lo respaldan el hueco entre las dos nubes de capital, la prima por mil de capital y la historia de 3.378 de esas pólizas; para las 149 filas sin referencia la prueba de prima es la única evidencia. Sin la división, 123 filas del test tendrían predicciones entre 35 y 89 veces mayores.

El tercio público es una muestra aleatoria del año 2025. Es lo que permite que un nivel medido en el público valga para el privado; la credibilidad descuenta el ruido de esa muestra, medido en 2024 (3,4 %, 4,8 % y 3,6 % por ramo, y mayor frente a la parte no vista, como corrigió D103).

El nivel de S30, la media de los factores de 2023 y 2024, es el centro razonable de la previa y τ su anchura. Es una elección de juicio, declarada antes de ver el marcador; D101 y D102 exploraron previas más anchas y se descartaron.

No hay eventos catastróficos y la prima escrita es anual. Lo primero se comprobó en los datos; lo segundo (DATA-006) no está confirmado por el diccionario y solo afecta a cuánto apoya la prima el nivel de edificios, no al modelo.

## Qué rendimiento tiene y qué margen de error lleva

| Medida | Valor | Lectura |
| --- | --- | --- |
| D² en 2024 (corte V24, Mezcla por peligro) | 0,13788 | Frente a 0,07094 de una tasa constante por ramo y 0,13610 del mejor candidato de la línea de Codex |
| Mejora frente al candidato anterior (S22) en V23 y V24 | +0,00016 y +0,00014 | Consistente en los dos cortes y en los dos criterios (completo y sin el 0,1 % superior) |
| Público de S30 | 0,12996 | Primer puesto al enviarlo el 18 de octubre |
| Público de S41 | 0,13016 | Igual al calculado antes de enviarlo; +0,00020 frente a S30 |
| Ruido entre modelos distintos en un tercio de las filas | ±0,0003 aproximado | El orden del privado entre los cinco primeros puede ser otro |
| Esperanza en el privado frente a S30 | positiva bajo los tres pares de previas de D103 | Pequeña frente al ruido; no es una garantía |

## Límites que el lector debe conocer

El nivel de 2025 se calibró con la retroalimentación del marcador público, con reglas fijadas antes de puntuar y declaradas aquí; es una práctica admitida por las reglas del concurso, pero no es información que un actuario tendría al tarifar. La incertidumbre de reservas es material en los tres ramos. Los cortes V23 y V24 se reutilizaron para elegir pesos y forma, así que sus cifras no son una validación independiente. Las unidades de los capitales extremos son una inferencia del proyecto. La prima escrita no tiene periodicidad confirmada. Toda la verificación es de IA, con revisión humana general pendiente.

## Cómo reproducirlo

Reconstruir S30 con `reproducir.py` (versión 1.2, modos `datos`, `componentes` y `mezcla`) desde los once originales, o repetir la mezcla desde los componentes guardados. Después, desde la raíz del repositorio, `python3 herramientas/sonda_nivel.py resolver --s30 0.12996 --motor 0.12954 0.12906 --buildings 0.12873 0.13018 --contents 0.12929 0.13011` escribe `S41_nivel_credibilidad.csv` con el SHA-256 del anexo.

## Lo que deja para la parte 2

Dos herramientas (`sonda_nivel.py`, `sonda_forma.py`) con su regla de credibilidad preinscrita, y tres lecciones: medir el ruido de cualquier sonda frente a la parte no vista y no frente al total; dejar en 1 los parámetros de forma afinados en los cortes salvo evidencia fuera de muestra; y fijar las reglas de lectura antes de enviar, porque lo que se gana con ellas es confianza, no solo décimas.

## Anexo: identificadores y procedencia

| Elemento | Valor |
| --- | --- |
| Archivo entregado | `Hackaton/Semana 1/Envios/archivos/S41_nivel_credibilidad.csv`, SHA-256 d8661c2874e9112bd3dd62ea4470a465ee309832dee53fd9dcaa4144dac643a5, ID Kaggle 57531719 |
| Base | `S30_claude_b.csv`, SHA-256 fd9528e0b1ee4b674dea63834a97523fd4ddc743d1495a422ce31a2eb76e3bc5 (D88, D99) |
| Sondas de nivel | S40_sonda_{motor,buildings,contents}_{x090,x110}; públicos 0,12954 / 0,12906, 0,12873 / 0,13018, 0,12929 / 0,13011 (COD-20261022-D100-ENVIOS) |
| Decisiones | D100 (sonda con credibilidad), D101 y D102 (variantes probadas y no elegidas), D103 y CIE-D103 (marca final S41) |
| Registros | `registro/sonda_nivel_D100_preinscripcion.json`, `registro/sonda_nivel_D100_resolucion.json`, `registro/decision_marca_final_S41_20261023.json`, `registro_envios.json` |
| Foro | CLA-20261022-001 a 004 y 009 a 011; CLA-20261023-002 (marca final) |
| Reproducción y reservas | `docs/REPRODUCCION_COMPLETA.md`, `docs/archivo/semana1/RESERVAS_ACOTACION.md`, `docs/archivo/semana1/SENSIBILIDAD_S30_S22.md`, `docs/archivo/semana1/SENSIBILIDAD_S43.md` |
