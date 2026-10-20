# Una prima de riesgo para cada periodo de póliza, construida y contrastada con IA

<p class="sub">AI Hackathon IAA 2026 · Parte 1, mercado establecido · Manuel Rodríguez, equipo individual (Kaggle: manoloriveros) · Versión del 20 de octubre de 2026 · Copia en español del informe que se entrega en inglés</p>

## La respuesta en una página

El reto pide estimar, para cada periodo de póliza de 2025 en autos particulares, edificios y contenidos del hogar, el coste último esperado de los siniestros ocurridos en el periodo, neto de franquicias y recobros y sin siniestros rechazados. Es la prima de riesgo, antes de gastos y márgenes. El concurso la mide con el D² Tweedie de potencia 1,5, que indica qué fracción de la desviación explica el modelo frente a cobrar a todos el coste medio. Como más del 90 % de los periodos no tiene siniestros, valores entre 0,10 y 0,15 ya separan bien el riesgo. Los datos son sintéticos y los importes van en una unidad ficticia (CU).

<div class="kpis">
<div class="kpi"><div class="v">0,12996</div><div class="l">puntuación pública del modelo final; primer puesto del tablero público entre 19 equipos (consulta del 19 de octubre)</div></div>
<div class="kpi"><div class="v">0,138</div><div class="l">D² en 2024, fuera de muestra, frente a 0,071 de una tasa constante por ramo</div></div>
<div class="kpi"><div class="v">626.639</div><div class="l">periodos de 2025 predichos en tres ramos, con diez controles de formato e integridad</div></div>
<div class="kpi"><div class="v">217</div><div class="l">aportes de tres líneas de IA en un foro común durante 54 horas, con hipótesis preinscritas</div></div>
</div>

Construimos el modelo en seis etapas (Figura 1). Reconstruimos los datos con ocho reglas reversibles y asignamos cada siniestro al único periodo que lo cubre. Después llevamos el coste observado a nivel último: estimamos qué parte de cada peligro de 2024 seguía sin reportarse y la incorporamos a la exposición de entrenamiento, de modo que el ajuste por siniestros no reportados (IBNR) entra una sola vez. El modelo final, que llamamos Mezcla por peligro, combina en cada ramo modelos del coste total con modelos de frecuencia por severidad por peligro, y fija el nivel de 2025 con los años 2023 y 2024 como contraste fuera de muestra.

La IA intervino en todas las etapas, sobre todo para confrontar posturas. Tres líneas de trabajo independientes, apoyadas en dos asistentes de IA, publicaban sus hipótesis antes de calcularlas y también sus fracasos; un enjambre de agentes de validación auditaba el proyecto cada seis horas. Autoricé las reglas de datos y los envíos a Kaggle, y aprobé el modelo final.

<figure class="fig" data-fig="flujo" data-opts='{"filas": 2}'>
<img src="../figuras/es/flujo.png" alt="Flujo actuarial en seis etapas">
<figcaption><span class="fig-n">Figura 1</span>El flujo actuarial. La etapa 3 traslada el retraso de reporte a la exposición de entrenamiento; las etapas 4 a 6 se validan con años completos fuera de muestra y cada paso deja huellas SHA-256 comprobables.</figcaption>
</figure>

| Criterio de la rúbrica | Dónde se responde |
| --- | --- |
| Rendimiento y adaptación (40 %) | Puntuación pública y local, tratamiento de datos, límites; plan para el mercado nuevo |
| Uso eficaz de la IA (25 %) | Etapa por etapa: qué hizo la IA, cómo se verificó y qué cambió gracias a la confrontación |
| Confianza, validación y controles (20 %) | Validación temporal, 12 experimentos preinscritos con backtesting del IBNR, 45 casos de control, un reentrenamiento completo que reconstruye byte a byte el archivo entregado |
| Comunicación y documentación (15 %) | Este informe, el video, el repositorio versionado y un panel sin conexión con las mismas cifras, en español o inglés (`docs/entrega/panel_modelo.html`) |

## Datos: qué corregimos y qué dejamos como incertidumbre {: .pagina }

Los once Parquet originales (7,8 millones de filas) se conservan intactos. Todo cambio vive en una capa derivada, con bitácora por fila y posibilidad de revertirlo. La auditoría inicial revisó las 105 columnas y encontró problemas que habrían distorsionado las tasas:

| Problema encontrado | Filas | Tratamiento |
| --- | --- | --- |
| Los identificadores de cliente de autos perdieron los ceros iniciales | 123.664 | Relleno a ocho dígitos; se recupera el cruce con el maestro |
| Parte de la exposición estaba en días o en base 360, no en años | 14.229 | Días cubiertos entre 365, la convención de todo 2025 |
| Capitales asegurados con saltos de unas mil veces dentro de una póliza | 2.073 + 1.454 | División entre mil cuando la historia de la póliza o una prueba de prima lo respalda; 149 se apoyan solo en la prueba de prima y quedan como incertidumbre declarada |
| Mayúsculas mezcladas en categorías y edad medida en fechas distintas | 700.210 · 2.936 | Unificación; la edad se calcula al inicio del periodo (cambio de convención, no corrección de errores) |
| Siniestros duplicados, idénticos salvo el identificador | 604 | Se excluye la copia |
| Rechazos de renovación con sucesor y siniestros previos al historial | 12.041 · 413 | Solo se marcan para auditoría; nunca entran como predictores |

Dos implementaciones independientes confirman la capa preparada: un segundo asistente recalculó las ocho reglas desde los originales con código propio (41 de 41 comprobaciones) y un productor alternativo reconstruyó las once tablas byte a byte, con 148 millones de celdas comparadas y ninguna diferencia.

## Del coste observado al coste último

Para aprender hace falta una etiqueta por periodo. Asignamos cada siniestro por póliza, ramo y fecha de ocurrencia dentro del periodo cubierto, sin usar la fecha de reporte. Tras excluir las copias exactas, los rechazados y los siniestros anteriores al historial de su póliza (que se concilian aparte), quedan 160.432 de los 163.150 registros como siniestros aceptados, cada uno en un solo periodo; ninguno queda ambiguo. La etiqueta T0 suma el incurrido de esos siniestros menos los recobros; los pagos ya vienen netos de franquicia, así que no se descuenta dos veces.


<div class="fila-60" markdown="1">
<div markdown="1">

T0 aún no es el coste último, porque al cierre de 2024 faltan siniestros por reportar. Un chain-ladder de conteos por peligro estima qué parte de la exposición de 2024 ya está «vista»: solo el 56 % en lesiones corporales de autos y el 66 % en hundimiento de edificios, frente a 94–98 % en los demás peligros (Figura 2). Entrenamos con esa exposición efectiva como offset y predecimos 2025 con la exposición nominal. El modelo aprende así tasas a nivel último sin aplicar el IBNR dos veces.

La Figura 3 muestra por qué importa. El coste observado de autos en 2024 (454 CU por año-exposición) parece una caída brusca; con el IBNR estimado sube a 584, en línea con 2021–2023, y la predicción de 2025 (595) continúa esa tendencia. Las reservas de caso de los siniestros abiertos se toman a su valor del cierre; con una única valoración no se puede demostrar que sean suficientes, por eso medimos su sensibilidad más abajo.

</div>
<figure class="fig" data-fig="completitud">
<img src="../figuras/es/completitud.png" alt="Completitud de 2024 por peligro">
<figcaption><span class="fig-n">Figura 2</span>Parte de la exposición de 2024 cuyos siniestros ya se han reportado, por peligro.</figcaption>
</figure>
</div>

<figure class="fig" data-fig="prima_anual" data-opts='{"alto": 172}'>
<img src="../figuras/es/prima_anual.png" alt="Prima de riesgo por año-exposición">
<figcaption><span class="fig-n">Figura 3</span>Prima de riesgo por año-exposición, en CU. Gris: coste observado (T0). Color: con el IBNR estimado. Círculo hueco: predicción del modelo final para 2025.</figcaption>
</figure>

## La Mezcla por peligro: un modelo final con diez componentes {: .pagina }

Ningún modelo único dominó en los tres ramos. Los modelos del coste total con distribución Tweedie (LightGBM y CatBoost) captan bien las interacciones entre variables; los de frecuencia por peligro multiplicada por la severidad separan mecanismos distintos (un incendio no se parece a una fuga de agua) y permiten proyectar la tendencia de severidad de cada peligro. El modelo final pondera ambos tipos por ramo (Figura 4). Los cambios se juzgaron con criterios escritos antes de calcularlos, en 2023 y en 2024, con todas las pérdidas y sin las más extremas; los criterios variaron entre líneas de trabajo, y el modelo final fue un ensayo que autoricé sin que pasara todos los filtros internos.

<figure class="fig" data-fig="composicion" data-opts='{"cfg": {"alto": 124}}'>
<img src="../figuras/es/composicion.png" alt="Pesos del modelo final por ramo">
<figcaption><span class="fig-n">Figura 4</span>Composición del modelo final. Azul: frecuencia por peligro × severidad. Naranja: coste total con Tweedie. El anexo detalla cada componente.</figcaption>
</figure>

El nivel de 2025 se fija por ramo con el factor que minimiza la desviación Tweedie, f = Σ(y/√μ) / Σ√μ, promediado entre los cortes de 2023 y 2024; el anexo detalla los factores. Los componentes cuyo nivel es inestable entre cortes aportan el reparto del riesgo, pero no fijan el nivel. En autos y edificios la severidad de cada peligro se proyecta un año con su tendencia, acotada a ±15 %. El total de 2025 es de 212,0 millones de CU, y autos tiene la tasa más alta por año-exposición (594,6 CU).

## Cómo lo validamos

Validamos como se usaría la tarifa: ajustar con años pasados y medir en un año completo posterior (Figura 5). Ningún coste de 2025 entra en el ajuste; la regla de nivel y la normalización de tasas sí usan las covariables y las predicciones de la cartera de 2025.

<div class="fila-60" markdown="1">
<figure class="fig" data-fig="validacion_diseno">
<img src="../figuras/es/validacion_diseno.png" alt="Diseño de validación temporal">
<figcaption><span class="fig-n">Figura 5</span>Tres cortes temporales. Producción reentrena con 2021–2024 y predice 2025.</figcaption>
</figure>
<figure class="fig" data-fig="d2_ramo" data-opts='{"cfg": {"alto": 196, "ancho": 330, "margen": {"t": 34, "r": 38, "b": 22, "l": 74}}}'>
<img src="../figuras/es/d2_ramo.png" alt="D² por ramo en 2024">
<figcaption><span class="fig-n">Figura 6</span>D² de 2024 por ramo: el modelo final frente a una tasa constante por ramo.</figcaption>
</figure>
</div>

En 2024 el modelo final explica casi el doble de desviación que la tasa constante por ramo (0,138 frente a 0,071) y mejora cada ramo por separado. También ordena bien el riesgo: el 10 % de periodos con mayor coste predicho reúne entre el 29 % y el 34 % del coste observado, y en cada decil lo observado sigue a lo predicho (Figura 7).

<figure class="fig" data-fig="deciles" data-opts='{"alto": 158}'>
<img src="../figuras/es/deciles.png" alt="Coste medio por decil de predicción">
<figcaption><span class="fig-n">Figura 7</span>Coste medio por periodo en 2024 por decil de coste predicho (escala logarítmica). Línea: predicho. Círculos: observado.</figcaption>
</figure>

Con las reservas de caso de los abiertos multiplicadas por 0,75 o por 1,25, el D² de 2024 baja de 0,1379 a 0,1372 y el modelo conserva su ventaja frente a las alternativas, pero los mismos escenarios mueven el nivel de 2025 hasta un 6,8 %. En edificios, el coste de 2024 superó en un 10 % lo predicho con el factor de 2023, por eso el nivel de 2025 promedia los dos factores. La página 5 resume los experimentos que pusieron a prueba estos resultados después de la elección.

## Cómo trabajó la IA y cómo la pusimos a prueba {: .pagina }

Organizamos el trabajo para que la IA no se validara a sí misma (Figura 8). Dos asistentes de IA, Claude y Codex, trabajaron en tres líneas: modelado, alternativas creativas y contraste. Ninguna podía usar predicciones de otra sin autorización expresa, las hipótesis se publicaban con su criterio de aceptación antes de calcularse y los resultados adversos se registraban igual que los favorables. En 54 horas el foro reunió 217 aportes; más de un tercio fueron preinscripciones o resultados adversos.

<figure class="fig estrecha" data-fig="flujo_ia">
<img src="../figuras/es/flujo_ia.png" alt="Flujo de trabajo asistido por IA">
<figcaption><span class="fig-n">Figura 8</span>Organización de la IA. El participante encarga y autoriza; las líneas publican en el foro; un enjambre de tres agentes audita cada seis horas; nada llega a la entrega sin pasar los controles automáticos.</figcaption>
</figure>

| Etapa | Qué hizo la IA | Cómo lo verificamos |
| --- | --- | --- |
| Datos y objetivo | Auditó 105 columnas; halló claves sin ceros, exposición en días, capitales ×1000 y 604 duplicados; asignó siniestros y estimó el IBNR | Recálculo independiente (41/41), reconstrucción byte a byte y dos algoritmos de asignación que coinciden |
| Variables | Contrato de disponibilidad por columna; detectó una variable que mide el siniestro del propio periodo (D² individual 0,43; las demás, menos de 0,04) | Exclusión por código con una guardia de predictores |
| Metodología | Dos búsquedas con 51 fuentes primarias cotejadas con DOI y arXiv, más tres papers de la IAA | Se descartó, por falta de evidencia, una mejora del 17 % que proponía otra herramienta de IA |
| Modelado y diagnóstico | 44 contrastes numerados, preinscripciones y una batería preinscrita de 12 experimentos de sensibilidad | Intervalos por cliente, dirección y región; escenarios de reserva, nivel y capital |
| Pruebas y gobierno | Orquestador de 30 nodos con huellas de 184 salidas; enjambre de validación con 21 hallazgos | Un validador detectó que el paquete daba «éxito» con archivos faltantes: corregido y probado con 36 casos adversos |

El hallazgo que más cambió el resultado se ve en la Figura 9. Varias propuestas mejoraban la validación local de 2024 y aun así bajaban en el tablero público. Una línea mostró que la inversión venía de unos pocos siniestros extremos y otra lo convirtió en un criterio medible: el D² sin el 0,5 % de pérdidas mayores ordena a los candidatos casi igual que el público (correlación de rangos 0,83, frente a 0,49 con todas las pérdidas). Con esa lectura se retiró una forma de hogar que dependía de la cola y se exigió mejorar también el «cuerpo», sin quitar la cola de la métrica. Los dos envíos siguientes marcaron el máximo público; el segundo es el modelo final. La misma confrontación rebajó a hipótesis una afirmación excesiva sobre las reservas.

<figure class="fig" data-fig="curva" data-opts='{"cfg": {"alto": 184}}'>
<img src="../figuras/es/curva.png" alt="Camino hasta el modelo final">
<figcaption><span class="fig-n">Figura 9</span>Camino hasta el modelo final: los 14 envíos puntuados, en orden. La zona sombreada marca las propuestas con mejor puntuación local y peor puntuación pública.</figcaption>
</figure>

## Controles, reproducibilidad y responsabilidad humana {: .pagina }

<div class="compacta" markdown="1">

| Capa | Control | Resultado |
| --- | --- | --- |
| Datos originales | Huellas SHA-256 de los once Parquet y reconstrucción independiente | 11 de 11 idénticos; 0 diferencias en 148 millones de celdas |
| Objetivo, exposición y variables | Conciliación de asignación, T0, reservas y exposición; contrato de disponibilidad por columna | 18 de 18 y 25 de 25 controles |
| Paquete | 9 casos nominales y 36 adversos lanzados desde la consola | 45 de 45 en la nube, en una máquina virtual y en Windows |
| Entrega | Columnas, filas, orden, identificadores, valores positivos y SHA-256 del recibo | 10 de 10 controles |

</div>

Con `python reproducir.py mezcla --objetivo=S30` el CSV final se regenera desde los componentes guardados con el SHA-256 que recibió Kaggle (S30 es el identificador del modelo en el código). Reentrenar toda la receta desde los originales lo reconstruyó byte a byte (162 de 181 huellas intermedias iguales y el resto dentro de 3,9e-15), y una réplica desde los 436 estimadores guardados, sin reajustes, dio 194 de 194 salidas idénticas. Lo hizo el mismo flujo, así que no es una reproducción independiente.

La responsabilidad es humana. Soy actuario, con 13 años de experiencia en actuaría y supervisión. Autoricé las reglas de datos y los envíos, fijé la prioridad de diseño (un flujo que otro actuario pueda entender, reproducir y adaptar), aprobé el modelo final el 18 de octubre y el 20 lo confirmé como definitivo, con lo que cerré la parte 1; la selección manual en Kaggle, aún pendiente, me corresponde. Acepté las correcciones técnicas del paquete y de la captura solo en ese alcance, y declaré como limitaciones la reproducción independiente y la suficiencia de las reservas. Ninguna verificación, de la IA o mía, es revisión independiente, porque participé en el desarrollo: cada uno de los 12 hallazgos abiertos indica qué revisor necesita.

## Experimentos de validación y límites que dejan

Tras la elección, once experimentos preinscritos, entre ellos un backtesting del IBNR, y un análisis de reservas pusieron a prueba el modelo final; el anexo los detalla, junto con un duodécimo que no hizo falta correr. Reutilizan los cortes de 2023 y 2024: miden estabilidad, no rendimiento independiente, y cada resultado adverso queda como límite. Dos límites no dependen de un experimento: esos cortes eligieron el modelo, y las fechas de las variables al cotizar esperan la confirmación del dueño de los datos.

<div class="compacta" markdown="1">

| Experimento | Resultado | Qué hacemos |
| --- | --- | --- |
| Reservas ×0,75 y ×1,25; acotación con materialidad del 1 % | El D² solo pasa de 0,1379 a 0,1372, pero un error del 3,7 % en las reservas de caso de autos (4,0 % en edificios) ya mueve el nivel de 2025 un 1 % | Incertidumbre material en los tres ramos, declarada como limitación; hacen falta valoraciones sucesivas |
| Backtesting del IBNR en tres cortes anteriores | Fuera de su criterio en 6 o 7 de 15 peligros por corte, sobre todo en los de pocos avisos; IBNR de lesiones del año recién cerrado sobrestimado en 2022 y 2023 (+20,1 % y +7,9 %) | Con los recobros ausentes en los abiertos, un escenario sitúa autos alto entre un 1,5 % y un 2,5 %: escenario declarado, no sesgo identificado, y sin aplicar |
| Nivel de 2025 desde dos cortes | Los factores de edificios (1,059 y 1,134) distan un 3,4 % de su media | Se promedian los dos cortes; recalibrar es lo primero en la semana 2 |
| Influencia de clientes, semillas y pesos | Quitar 6 de 373.831 clientes invierte la ventaja sobre el mejor envío anterior; las semillas mueven el D² como mucho 0,00003; 0 de 40 conjuntos de pesos vecinos mejoran los dos cortes | La ventaja no es robusta y no se afirma equivalencia; los pesos están en una meseta |
| Los 149 capitales sin confirmación, sin dividir | Sus filas pasan a ser de 35 a 89 veces mayores; juntas pesan el 0,01 % del total predicho (24.668 CU) | Mantener la división; confirmarla con un actuario de hogar |

</div>

## Semana 2: cómo adaptaremos el modelo

En el mercado nuevo el modelo congelado será la referencia, con el mismo protocolo de preinscripción, foro y controles; cada diferencia decidirá la respuesta, y esta sección se reemplazará con lo observado:

<div class="compacta" markdown="1">

| Si cambia | Respuesta prevista |
| --- | --- |
| El contrato, las unidades o la exposición (moneda, convención de días, objetivo) | Reconstruir la capa preparada sin trasladar reglas que no tengan evidencia nueva |
| La mezcla de peligros o las colas | Reentrenar severidades por peligro; revisar el criterio de cuerpo y la regla de nivel |
| El patrón de reporte de los siniestros | Reestimar el chain-ladder por peligro antes de entrenar |
| Las variables disponibles o su fecha de captura | Actualizar el contrato por columna y la guardia de predictores |
| El rendimiento del modelo congelado (caída del D² o descalibración por decil) | Recalibrar primero; reconstruir solo si la recalibración no basta |

</div>

<!-- FIN-CALIFICABLE -->

<div class="apendice" markdown="1">

## Anexo, fuera de las cinco páginas calificables {: .pagina }

### Componentes y parámetros del modelo final

| Ramo | Componente | Tipo | Peso |
| --- | --- | --- | --- |
| Autos | CatBoost Tweedie del coste total, cuatro semillas | Coste total | 0,2 |
| Autos | CatBoost Poisson por peligro × severidad GLM gamma con tendencia | Frecuencia × severidad | 0,6 |
| Autos | LightGBM Tweedie con variables F0 a F4 | Coste total | 0,1 |
| Autos | LightGBM Tweedie con variables reducidas | Coste total | 0,1 |
| Edificios | LightGBM Tweedie con siete variables de cliente | Coste total | 0,4 |
| Edificios | CatBoost Poisson por peligro × severidad por capital con tendencia | Frecuencia × severidad | 0,3 |
| Edificios | Frecuencia aditiva por peligro × severidad por capital con tendencia | Frecuencia × severidad | 0,3 |
| Contenidos | LightGBM Tweedie | Coste total | 0,3 |
| Contenidos | Frecuencia aditiva por peligro × severidad LightGBM gamma | Frecuencia × severidad | 0,3 |
| Contenidos | Frecuencia aditiva por peligro × severidad GLM con covariables físicas | Frecuencia × severidad | 0,4 |

Forma de la tasa: en autos exponente 1,09 sobre la dispersión de tasas y elasticidad de exposición 0,95; en contenidos elasticidad 0,95; edificios sin forma. Factores de nivel f (2023 / 2024 / media): autos 0,986 / 1,005 / 0,996; edificios 1,059 / 1,134 / 1,097; contenidos 1,078 / 1,092 / 1,085. Validación: entrenamiento con offset log(exposición efectiva); V23 entrena 2021–2022 y para el boosting en la mitad de calibración de 2023; V24 entrena 2021–2023 con las rondas de V23 × 1,15; producción entrena 2021–2024 con × 1,3. D² recalculado desde las predicciones guardadas: V23 0,14542 y V24 0,13788 (autos 0,09168; edificios 0,11580; contenidos 0,09665). Archivo entregado (identificador S30): 626.639 filas, SHA-256 fd9528e0b1ee4b674dea63834a97523fd4ddc743d1495a422ce31a2eb76e3bc5, envío Kaggle 57371361.

### Experimentos tras la elección del modelo final

Once experimentos se escribieron con su hipótesis y su criterio de aceptación antes de calcular; el backtesting del IBNR se añadió a pedido del participante, con su propia preinscripción. Comparan el modelo final con el mejor envío anterior en la mitad de selección de 2023 y en el año 2024 completo, con el D² completo y el del cuerpo, y tratan como empate cualquier diferencia por debajo del piso de semillas. Un análisis preinscrito aparte acotó las reservas de caso con la materialidad del 1 % que el participante fijó antes de ver resultados.

| Experimento | Pregunta | Resultado frente al criterio fijado |
| --- | --- | --- |
| Influencia de clientes | ¿Depende la ventaja de pocos clientes? | Sí: quitar 6 de 373.831 clientes la invierte en 2024, y 1 en 2023. Rechazada |
| Nivel por ramo | ¿Es estable el nivel de 2025 entre los dos cortes? | No en edificios (1,059 frente a 1,134); autos dista un 0,9 % y contenidos un 0,7 % de su media. Rechazada en edificios |
| Reservas y recobros | ¿Resisten el orden y el nivel? | La ventaja se mantiene con reservas ×0,75, ×1 y ×1,25; los recobros ausentes en los abiertos de autos bajarían su nivel un 0,75 % |
| Pesos vecinos | ¿Hay pesos mejores cerca? | 0 de 40 vecinos mejoran los dos cortes y los dos criterios. Meseta confirmada |
| Capitales sin confirmación | ¿Es inmaterial la división entre mil? | No por fila: sin dividir, esas filas son de 35 a 89 veces mayores. Rechazada |
| Cohortes y segmentos | ¿Es homogénea la ventaja? | Los segmentos adversos no se repiten entre cortes; el A/E regional de edificios correlaciona 0,22 entre años. Rechazada en parte |
| Piso de ruido | ¿Es el piso de semillas menor que 0,0001? | Sí: las semillas mueven el D² como mucho 0,00003. Confirmada |
| Tendencia de severidad | ¿Resiste la ventaja a otros escenarios de tendencia? | Sí, en todos los escenarios probados, con matices de atribución. Confirmada |
| Forma y elasticidad | ¿Están en una meseta? | No: el D² se mueve entre 0,0002 y 0,0015 en ±0,02, pero ningún punto mejora los cuatro criterios |
| Reproducción | ¿Se reproducen los componentes al reentrenar? | Dos LightGBM de hogar: 1.111.301 predicciones guardadas, bit a bit. Confirmada |
| Semilla nueva | ¿Cuánto mueve una semilla nueva? | No ejecutado: ya lo cubren una corrida anterior de cinco semillas y la reproducción |
| Backtesting del IBNR | ¿Predice el chain-ladder los avisos posteriores? | No en varios peligros: 6 o 7 de 15 fuera del criterio por corte (figura A1). En lesiones, el IBNR del año recién cerrado se sobrestimó un 20,1 % (2022) y un 7,9 % (2023); en junio de 2024 la proyección quedó un 7,5 % corta. Rechazada, con efecto acotado |
| Acotación de reservas | ¿Cuánto error de reserva importaría? | Un 3,7 % en autos, un 4,0 % en edificios y un 9,0 % en contenidos mueven el nivel un 1 %; las estimaciones puntuales no sugieren reservas cortas, pero sus intervalos no las descartan. Incertidumbre material |

<figure class="fig" data-fig="backtest">
<img src="../figuras/es/backtest.png" alt="Backtesting del IBNR por peligro y corte">
<figcaption><span class="fig-n">Figura A1</span>Backtesting del IBNR. El chain-ladder de reporte se reestimó con los datos disponibles en tres cortes anteriores; cada celda compara los avisos que proyectaba recibir después del corte con los reportados hasta diciembre de 2024. Las cifras del año recién cerrado que cita el texto comparan el IBNR de ese año con su reestimación con todos los datos.</figcaption>
</figure>

### Glosario breve

| Término | Significado |
| --- | --- |
| D² Tweedie | 1 menos el cociente entre la desviación Tweedie del modelo y la de predecir la media; 0 equivale a no saber nada y 1 a acertar cada periodo |
| T0 | Incurrido neto observado al 31-12-2024 de los siniestros aceptados del periodo |
| IBNR | Siniestros ocurridos y aún no reportados al cierre |
| Exposición efectiva | Exposición nominal multiplicada, mes a mes, por la proporción de siniestros de ese peligro que ya se habría reportado |
| Cuerpo | La distribución sin el 0,5 % de periodos más costosos, usada solo como diagnóstico |
| Preinscripción | Hipótesis, datos y criterio de aceptación escritos antes de calcular |

### Referencias principales

- Smyth y Jørgensen (2002). Fitting Tweedie's compound Poisson model to insurance claims data. ASTIN Bulletin 32(1).
- Delong, Lindholm y Wüthrich (2021). Making Tweedie's compound Poisson model more accessible. European Actuarial Journal.
- Denuit, Charpentier y Trufin (2021). Autocalibration and Tweedie-dominance for insurance pricing with machine learning. Insurance: Mathematics and Economics.
- Henckaerts, Côté, Antonio y Verbelen (2021). Boosting insights in insurance tariff plans with tree-based machine learning methods. North American Actuarial Journal.
- Yang, Qian y Zou (2018). Insurance premium prediction via gradient tree-boosted Tweedie compound Poisson models. arXiv:1508.06378.
- Fissler, Lorentzen y Mayer (2023). Model comparison and calibration assessment. arXiv:2202.12780.
- Denuit, Sznajder y Trufin (2019). Model selection based on Lorenz and concentration curves, Gini indices and convex order. Insurance: Mathematics and Economics 89.
- Lindholm y Nazar (2024). On duration effects in non-life insurance pricing. European Actuarial Journal.
- Verbelen, Antonio, Claeskens y Crevecoeur (2022). Modeling the occurrence of events subject to a reporting delay via an EM algorithm. Statistical Science.
- Lindholm, Richman, Tsanakas y Wüthrich (2022). Discrimination-free insurance pricing. ASTIN Bulletin.
- Wüthrich y Merz (2023). Statistical Foundations of Actuarial Learning and its Applications. Springer.
- Goldburd, Khare, Tevet y Guller. Generalized Linear Models for Insurance Rating. CAS Monograph 5.
- IAA AI Task Force: Professional Considerations for Actuaries Interacting with Artificial Intelligence (2026); Artificial Intelligence Governance Framework (2025); Documentation of Artificial Intelligence Models or Systems (2025).

### Procedencia de las cifras

Cada número de este informe sale de `docs/entrega/datos/cifras_entregables.json`, que guarda la ruta y el SHA-256 de cada fuente que lee y se regenera con `herramientas/cifras_entregables.py`; `herramientas/verificar_entregables.py` comprueba que el texto coincide con ese archivo. El foro completo (con identificadores sintéticos omitidos), el registro de decisiones y los recibos de cada envío se conservan como expediente de trabajo en `docs/expediente/` y `registro/`.

</div>
