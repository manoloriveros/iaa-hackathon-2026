# Validación nocturna de las partes 1 y 2

Sesión de Claude (Cowork), 23 y 24 de octubre de 2026, hora de Bogotá. El participante pidió retomar las dos partes del reto y validarlo todo desde cero: datos, supuestos, metodologías y decisiones anteriores, empezando por modelos estándar y complicándolos solo cuando hiciera falta, con la evaluación independiente de las anteriores. Este informe explica qué se hizo, qué salió y qué queda por decidir. El registro hora a hora está en [BITACORA.md](BITACORA.md).

## Resumen

En la semana 2, el modelo más simple que funciona usa tres parámetros emergentes. Toma de un modelo estándar del mercado desarrollado (un LightGBM Tweedie entrenado solo con el desarrollado y las variables comunes a los dos mercados) las relatividades entre pólizas, y estima con los datos emergentes solo el nivel de cada ramo. En el desarrollo de 2023 supera por +0,038 a +0,061 de D² a cualquier modelo entrenado solo con el emergente. En la confirmación única de 2024, abierta según la política SEL01, mejora a la tasa por ramo en +0,049 (intervalo del 99,17 %: +0,027 a +0,073) y pasa todas las salvaguardas salvo una, la de cliente nuevo, que falla por potencia y no por evidencia en contra. Por la regla preinscrita, la titular formal quedó en la tasa por ramo. El 24 de octubre el participante enmendó esa salvaguarda (política S2-SELECCION-v2-20261024): bajo la versión 2, A1 promueve y es la titular, con la misma evidencia y sin volver a abrir 2024. Después de abrir aparecieron dos cosas. La primera, un error propio en el cruce de clientes de autos del desarrollado, ya corregido y sin efecto material. La segunda, una mejora clara con una variable estándar, la historia de siniestros de la póliza: +0,005 en desarrollo y +0,004 en 2024. Se definió tras la apertura y va en versión neutral: la historia ordena las pólizas pero no cambia el total del ramo, porque calibrada en 2023 subía el nivel por un efecto de calendario que encontró el revisor rev4. El participante la adoptó en la versión 2 junto con el promedio de tres semillas. Con las tres semillas su ganancia es menor de lo que daba una sola (sección 10).

Al final comparé con el catálogo de Codex en las mismas 50.094 filas de 2023, con el mismo objetivo y la misma métrica, y reproduje sus D² al quinto decimal. La transferencia supera a su mejor receta, B10, por +0,0270 [+0,0141; +0,0402]. Ninguna de sus recetas usa el desarrollado.

En la parte 1, la base del desarrollado rehecha con código nuevo coincide con la de la semana 1 en todo (T0, duplicados, prehistoria, exposiciones, capitales). Un solo GBM estándar con las variables del contrato y la historia de la póliza logra el 95 % del D² de S30 en V24. La complejidad de S30 añadía +0,0065 con intervalo por encima de cero, así que allí sí estaba justificada.

Lo que más pesa en el resultado privado de la semana 2 es el nivel 2025 por ramo, sobre todo en edificios, donde el incendio pasó de 49 siniestros en 2023 a 21 en 2024. Ningún dato disponible cierra esa duda. El informe deja tres opciones de nivel y el diseño de una sonda para que el participante decida. Recomendé aplicar la tendencia del desarrollado estimada con siniestros topados a 250.000 CU, porque dos backtests independientes coinciden en que juntar dos años sin tendencia se queda corto en hogar entre un 5 y un 12 %. El participante decidió producir sin tendencia. La producción designada era A1fixF1b3n_2025.csv (67,17 M CU). Después de validarla, el participante eligió enviar su media 50/50 con la producción de la línea ML independiente de Claude: 69,00 M CU, sin tendencia, con envío autorizado a Codex (sección 10).

En el público, esa mezcla dio 0,15390. La variante robusta, que ganaba en las tres validaciones, dio 0,15347. El tablero nos deja séptimos de siete, a entre 0,0078 y 0,0106 de los cuatro primeros, una distancia del tamaño de un error de nivel del 20-30 %. El participante eligió una sonda de nivel global: dos envíos que miden el nivel óptimo del público, con credibilidad preinscrita antes de ver nada (sección 10). Las dos sondas dieron 0,14095 y 0,15955. El óptimo del público queda un 22 % por encima de la mezcla, y con la credibilidad el archivo final lleva la mezcla por 1,1877 (81,94 M CU). Enviado, dio 0,15948, igual al previsto. Está preparada, sin enviar, una sonda por ramo × nuevo negocio para repartir ese nivel entre segmentos.

## 1. Cómo se trabajó

Para que la evaluación fuera independiente de las anteriores, todo el código es nuevo, escrito desde el diccionario oficial y los Parquet originales. Los 13 archivos emergentes y los 11 del desarrollado se comprobaron por SHA-256 contra sus manifiestos antes de leerlos. No se abrió el código de preparación ni de modelos de Codex ni de sesiones anteriores de Claude. Las cifras previas que ya constaban en la memoria del proyecto se compararon solo al final, y cada coincidencia o diferencia se anota.

Cada regla se escribió antes de medir su efecto. La escalera de modelos sube un peldaño solo si el siguiente mejora al anterior con intervalos por cliente. Los modelos se evaluaron sobre el emergente de 2023 con cinco folds propios por cliente (`sha256('noche_v1|customer_id') % 5`), con el objetivo T0 y el D² Tweedie 1,5 global, y con bootstrap por componentes cliente-dirección.

Cuatro revisores independientes (subagentes) recibieron los datos y el código de evaluación, nunca las conclusiones. El primero rehízo la base y auditó los OOF. El segundo rehízo la puerta de 2024 con su propio objetivo y su propio bootstrap. El tercero revisó la producción, el nivel 2025 y la prima comercial. El cuarto midió por su cuenta el efecto de la historia de la póliza y la tendencia de nivel; su primera corrida se cortó por el límite de uso y la terminó a la mañana siguiente. Sus informes están en `revision/`, y lo que encontraron se discute en cada sección.

## 2. Datos

### Semana 2, mercado emergente

| Regla | Qué hace | Resultado propio | Revisor | Coincide con lo anterior |
| --- | --- | --- | --- | --- |
| EXP-N1 | Exposición = días inclusivos / 365 | 609 filas de entrenamiento cambian (495 en días/360 y 114 en número de días); el test no cambia | 608 más una fila de un día bajo el umbral | Sí (609 de Codex) |
| ASG-N1 | Siniestro a la fila con mismo `policy_id`, ramo y fecha dentro del periodo | 9.222 con una sola fila, 36 sin fila, todos anteriores al primer periodo; ninguno ambiguo | Igual | Sí |
| OBJ-N1 | T0 = incurrido − recuperaciones, sin rechazados | 27.997.991,57 CU (autos 15.855.887,96, edificios 9.558.749,31, contenidos 2.583.354,30) | Igual al céntimo | Sí |
| CAP-N1 | Capital entre mil si supera el hueco del ramo y la prima por mil cae bajo el mínimo normal | 349 filas (110 de entrenamiento, 239 de test); huecos de 67 y 27 veces | Las mismas 349 | Sí (decisión CAPS2-01) |
| CON-N1 | WOD = timber = t/w; MIX = non_standard | Proporciones: t+w 12,6 % y non_standard 9,9 % en el desarrollado; WOD 12,0 % y MIX 10,1 % en el emergente | Llega a lo mismo | Nueva |
| VAR-N1 | Fuera previous_insurer, branch_id, email_domain, marketing_consent, document_preference y la marca self-employed | χ²/gl de la frecuencia por nivel entre 0,15 y 2,1 con 1,9 millones de filas del desarrollado; sin ellas el GBM desarrollado de contenidos sube de 0,0686 a 0,0761 | — | Nueva |
| MM-N1 | `make_model` fuera del GBM | Con 300 categorías concentraba el 44 % de la ganancia; sin ella, el D² interno de autos sube de 0,0743 a 0,0845 | — | Nueva |

Otros hechos verificados: no hay duplicados de siniestros en el emergente; los 120 rechazados tienen importes cero; ningún abierto tiene recuperaciones; `customer_service_contacts` mide el siniestro del propio periodo (frecuencia de autos 0,000 con cero contactos y 1,125 con tres o más) y cambia de distribución en el test (9,5 % frente a 0,8 % con tres o más), así que queda fuera; el nuevo negocio pasa del 6–9 % de la exposición en 2023–2024 al 77 % en 2025, sin cambio de canal (70 % broker los tres años); ninguna fila de 2024 cubre el 31 de diciembre de 2024.

### Semana 1, mercado desarrollado

La misma tubería, ejecutada sobre los once originales del desarrollado, da T0 = 741.156.868,43 CU y 160.432 siniestros aceptados con asignación única, quita 604 copias idénticas salvo `claim_id`, separa 413 siniestros anteriores al primer periodo y cambia 5.736, 4.182 y 4.311 exposiciones. Con los umbrales de 5 y 2 millones, los 3.527 capitales extremos pasan la prueba de prima. Todo coincide con D42, D47, D59, D66 y D67. Es una reproducción independiente de la base sobre la que se construyó S30.

## 3. Supuestos

El reporte tardío se estima por peligro con el estimador de Lynden-Bell para datos truncados, uniendo los dos mercados. La razón es que los retrasos de cada peligro coinciden entre mercados (medianas y percentil 90 de la cohorte 2023 casi iguales). Para el coste, la curva se pondera por el neto, porque en lesiones corporales los siniestros tardíos son entre un 7 y un 12 % más caros. Completitud del coste de 2024 al cierre: autos 0,816, edificios 0,950, contenidos 0,978. Aplicado al desarrollado, da factores de desarrollo de 2024 de 1,2529, 1,0717 y 1,0239, frente a 1,2877, 1,0796 y 1,0317 del chain-ladder de D67. En autos son un 2,7 % menos de IBNR, en la misma dirección que el backtesting de D95 y que la sonda D100 de la parte 1.

En reservas, ningún abierto tiene recuperaciones. Si recuperaran como los cerrados (24 % en daños propios, 3,9 % en robo), el neto de autos bajaría un 0,6 %. Es un diagnóstico y no se aplica.

El efecto del nuevo negocio en frecuencia, medido con un GBM de Poisson del desarrollado sin variables de antigüedad, es de 1,13 a 1,17 en el desarrollado y de 1,15 a 1,19 en el emergente de 2023: el mismo en los dos mercados. El revisor rev1 añadió que la mitad del efecto viene del calendario, porque el nuevo negocio empieza a mitad de año y dura menos. Por eso el mes de inicio entró en las relatividades. Tras abrir 2024 se vio que, con las relatividades del desarrollado, el nuevo negocio de 2024 queda calibrado frente a la renovación (razón 0,98). Esto respalda la decisión del participante de dar credibilidad al desarrollado en el nivel del nuevo negocio, y deja sin uso un factor propio del emergente.

En clima, la base no usa el del propio año. La variante con el clima persistente de la dirección medido en los otros años (viento, incendio forestal, lluvia y temperatura; correlación interanual entre 0,79 y 0,96) mejora el desarrollo de 2023 en +0,0025, con P 0,96. Sin el 0,1 % de filas más caras, en cambio, empeora en −0,0004, y en 2024, ya como exploración, mejora +0,0016 con un intervalo que cruza cero. No es imprescindible y queda fuera.

Sobre tendencia: con las relatividades fijas, el índice de coste del desarrollado sube un 4,6 % al año en autos, un 6,4 % en edificios y un 3,6 % en contenidos. Probar si eso se traslada al emergente no es posible con un solo año de confirmación, así que se presenta como opción de nivel (sección 6).

## 4. Semana 2: la escalera de modelos

![Escalera de la semana 2](figuras/fig1_escalera_s2.png)

| Peldaño (OOF 2023) | Global | Autos | Edificios | Contenidos | A/E nuevo negocio |
| --- | ---: | ---: | ---: | ---: | ---: |
| Tasa por ramo | 0,0677 | −0,0031 | 0,0157 | 0,0270 | 1,58 |
| GLM Tweedie emergente, todas las variables | 0,0805 | 0,0235 | 0,0036 | 0,0587 | 1,15 |
| GLM frecuencia × severidad emergente | 0,0603 | 0,0178 | −0,0511 | 0,0629 | 1,09 |
| GBM Tweedie emergente regularizado | 0,0833 | 0,0054 | 0,0431 | 0,0424 | 1,47 |
| Relatividades GLM del desarrollado × nivel | 0,1185 | 0,0424 | 0,0776 | 0,0864 | 1,28 |
| Relatividades GBM del desarrollado × nivel | 0,1174 | 0,0285 | 0,0807 | 0,1080 | 1,41 |
| A1: GBM desarrollado v2 × nivel, 3 parámetros | 0,1213 | 0,0402 | 0,0766 | 0,1091 | 1,36 |
| A2: A1 + región emergente | 0,1240 | 0,0364 | 0,0899 | 0,1082 | 1,35 |

Con unos 500 siniestros de hogar en 2023, cualquier modelo entrenado solo con el emergente sobreajusta: el GLM con todas las variables daba −0,22 con poca penalización y los niveles fuera de muestra se desviaban hasta un 27 %. La transferencia es la única mejora robusta. Frente a A1, la tasa por ramo queda en −0,054 [−0,066; −0,041], y los modelos solo emergentes entre −0,038 y −0,061, con intervalos lejos de cero, también sin el 0,1 % superior (`salidas/s2/comparacion_frente_A1.txt`). Los añadidos sobre A1 no mejoraron de forma robusta en desarrollo. La región da +0,0027 [−0,0038; +0,0091]. Región más nuevo negocio, +0,0044 en el completo y −0,0010 en el cuerpo. El nivel que minimiza la desviación, +0,0006 [−0,0004; +0,0016]. El clima, ya comentado en la sección 3. Como fuente de relatividades, el GLM del desarrollado queda en −0,0028 en el completo y en −0,0087 [−0,0122; −0,0054] en el cuerpo, así que se queda el GBM. La versión v2 (sin `make_model`, con mes de inicio) mejora a la primera en el cuerpo: +0,0045 [+0,0018; +0,0072].

Las semillas importan. Con las semillas 12 y 13 del GBM desarrollado, el D² de desarrollo de A1 es 0,1239 y 0,1243, frente a 0,1213 con la semilla 11, que se fijó antes de medir y no se eligió. Ese ruido de ±0,003 es del tamaño de los añadidos que no subieron, lo que confirma que no eran mejoras reales. Promediar las tres semillas estabiliza: +0,0017 [+0,0005; +0,0031] en desarrollo y +0,0005 [−0,0009; +0,0019] en 2024, ya como exploración. Por fila, la predicción de 2025 cambia con la semilla una mediana del 4 al 6 % y un p99 del 23 al 26 %.

La historia de siniestros de la póliza conocida al inicio (siniestros reportados antes de `period_start` y años observados, aprendida en el desarrollado y aplicada igual al emergente) es la mejora más clara después de la transferencia: +0,0050 [+0,0019; +0,0084] en desarrollo y +0,0042 [+0,0022; +0,0061] en 2024. Sube los tres ramos, sobre todo la renovación (+0,0047), y en el cuerpo renivelado da +0,0015. Se definió después de abrir 2024, así que bajo SEL01 v1 no promueve. Queda como propuesta.

El revisor rev4 rehízo la pregunta por su cuenta (historia de 12 meses, GLM y GBM de frecuencia) y llegó a lo mismo en autos: la relatividad de un siniestro es 1,29 en el desarrollado y 1,32 en el emergente 2024, y añadir la historia sube el D² de frecuencia de autos en 2024 en +0,0039 [+0,0020; +0,0058]. En hogar el signo coincide, pero con muy pocos siniestros previos (35 y 23) no es significativo. También encontró un problema de diseño que afecta a mi cifra. En 2023 casi nadie tiene historia observable, así que calibrar el nivel en 2023 deja al modelo con historia más alto en 2024 por un efecto de calendario y no de riesgo. Lo medí en A1fixF1 (`codigo/f1_nivel.py`): con la calibración en 2023 su total de 2024 queda un 3,8 % por encima del de A1fix en autos, un 0,9 % en edificios y un 0,2 % en contenidos. En 2024 eso ayudó por casualidad, porque A1fix se quedaba corto (A/E de autos 1,104 frente a 1,063). Con la calibración neutral de rev4, que reescala la historia al total de A1fix sin mirar los siniestros de 2024, la ganancia es +0,0040 [+0,0023; +0,0057]. Es decir, casi toda la mejora es de orden y no de nivel. En 2025 el mismo efecto subiría el total de A1fixF1 un 2,6 % en autos y un 2,0 % en edificios, y sumado a la tendencia lo contaría dos veces. Por eso la versión que propongo de la historia es la neutral (A1fixF1n): ordena con la historia y toma el total por ramo de A1fix.

Dos errores propios aparecieron por el camino y se corrigieron antes de usar ninguna cifra. El GBM partía de una tasa de 1 CU y salía con un A/E de 3,2; ahora parte de la tasa media. El agrupado por cuantiles del GLM juntaba en un solo nivel las variables binarias; ahora las discretas de 12 valores o menos van como categorías. El revisor rev1 confirmó que ninguno de los tres OOF tiene fuga. Un tercer error apareció después de abrir 2024: el constructor de variables no aplicaba ID01 a los `customer_id` de autos del desarrollado, que perdieron sus ceros iniciales, y el 10 % de esas filas (98.110 de entrenamiento) entró sin variables de cliente. Corregido y reentrenado, el efecto es −0,0001 en desarrollo y en 2024, dentro del ruido. El acta no cambia porque se hizo con la receta congelada, y la producción corregida se llama A1fix.

## 5. Confirmación única de 2024

![Puerta 2024](figuras/fig2_puerta_2024.png)

Antes de abrir se congeló la lista (R0 tasa por ramo, A1 y A2), con predicciones de 2024 fijadas por SHA (e4f55f69…3a7eb7) y reproducidas dos veces. Ningún ajuste usa etiquetas de 2024 de ningún mercado: las relatividades salen del desarrollado 2021–2023 y la curva de reporte de las ocurrencias hasta 2023. La preinscripción se publicó en el foro (CLA-S2-20261024-005, 00:55:32 UTC) y la apertura fue a las 00:55:37 UTC. Se aplicaron los números de SEL01: 10.000 sorteos de componentes cliente-dirección con la semilla 2026102301, familia de seis pares con Bonferroni (cuantil inferior 0,4167 %), margen 0,0005 y promoción secuencial. Se excluyeron antes de abrir una variante con tendencia (en el desarrollado la tendencia bajaba el D²), el nivel Tweedie y el factor emergente de nuevo negocio.

| | R0 | A1 | A2 |
| --- | ---: | ---: | ---: |
| D² global 2024 | 0,0728 | 0,1214 | 0,1175 |
| Autos | 0,0499 | 0,0803 | 0,0805 |
| Edificios | −0,0213 | 0,0649 | 0,0520 |
| Contenidos | 0,0452 | 0,0920 | 0,0908 |

A1 frente a R0: +0,0486 [+0,0265; +0,0733]. Pasa los cuatro escenarios de reserva y masa tardía (+0,048 a +0,049), los cinco segmentos (cliente nuevo +0,013, renovación +0,054) y la influencia (+0,019 tras retirar 37 componentes; hace falta retirar 191 para anular la ventaja). Falla en clientes nuevos: la diferencia es +0,0131, pero el límite inferior del 95 % queda en −0,0105 y la regla pide −0,001. A2 queda por debajo de A1 (−0,0040) y falla por lo mismo. Titular formal bajo v1: R0, con A1 y A2 como alternativas. Bajo la enmienda v2 del participante, A1 pasa a titular (sección 10).

El revisor rev2 rehízo todo con su propio objetivo y su propio bootstrap y obtuvo el mismo D² al quinto decimal y el mismo veredicto. También midió la potencia de esa salvaguarda. La desviación típica de la diferencia en las 9.063 filas de cliente nuevo (447 siniestros) es 0,014. Con el efecto observado pasaría solo el 26 % de las veces, y para un 80 % harían falta unas 55.900 filas de cliente nuevo, casi todo 2024. Con un margen de 0,07 desviaciones típicas, la regla funciona en la práctica como una prueba de superioridad y no de no inferioridad, que era su propósito declarado. Una enmienda razonable, si el participante la quiere, sería exigir solo diferencia ≥ 0 en clientes nuevos o fijar el margen en proporción a la desviación típica del subconjunto. Cualquier enmienda debe versionar SEL01 y conservar este resultado.

La auditoría nocturna de Codex (COD-S2-IA-20261024T052608Z) señaló tres diferencias de esta puerta frente al motor común: la salvaguarda de cliente nuevo usa 2.000 réplicas y cuantil 0,05 en lugar de 10.000 y 0,025, los escenarios fijan las predicciones y estresan las etiquetas, y algunas decisiones se tomaron con cifras redondeadas a seis decimales. Medí si alguna cambia el acta (`codigo/puerta_sensibilidad.py`, sin tocar el resultado). El límite de cliente nuevo de A1 queda entre −0,0104 y −0,0108 con cuantil 0,05 y entre −0,0141 y −0,0153 con 0,025, para 2.000 o 10.000 réplicas y dos semillas, así que falla en todas las variantes. Sin redondear, el margen más estrecho de las demás salvaguardas es +0,014, y la primaria da el mismo límite (+0,026514). El veredicto no cambia. Lo que no queda demostrado es la equivalencia literal con el motor común; lo que sí queda medido es que esas diferencias no mueven el resultado.

## 6. Producción 2025 y nivel

Las dos producciones preinscritas están listas y validadas (209.063 filas, orden de la plantilla, predicciones finitas y positivas), sin enviar:

| Archivo | Qué es | Total 2025 | Autos | Edificios | Contenidos |
| --- | --- | ---: | ---: | ---: | ---: |
| R0_2025.csv | Titular formal: tasa por ramo 2023–2024 con IBNR | 61,20 M | 36,05 M | 19,84 M | 5,31 M |
| A1_2025.csv | Alternativa recomendada: relatividades del desarrollado 2021–2024 × nivel 2023–2024 | 67,15 M | 41,17 M | 20,45 M | 5,54 M |
| A1T_2025.csv | Opción: A1 con la tendencia del desarrollado durante 1,5 años (factores 1,072, 1,097 y 1,054) | 72,40 M | 44,14 M | 22,43 M | 5,83 M |
| A1fix_2025.csv | A1 con ID01 corregido en autos del desarrollado | 66,89 M | 40,90 M | 20,45 M | 5,54 M |
| A1fixb3_2025.csv | A1fix con tres semillas promediadas | 67,17 M | 41,04 M | 20,59 M | 5,54 M |
| A1fixF1_2025.csv | A1fix con la historia de la póliza (propuesta posterior a la apertura) | 68,40 M | 41,98 M | 20,86 M | 5,56 M |
| A1fixF1T_2025.csv | A1fixF1 con la tendencia sin tope (sustituida por las dos siguientes) | 73,75 M | 45,01 M | 22,88 M | 5,86 M |
| A1fixTc_2025.csv | A1fix con la tendencia TEN-N2, estimada con siniestros topados (factores 1,055, 1,094 y 1,053) | 71,34 M | 43,13 M | 22,37 M | 5,83 M |
| A1fixF1nTc_2025.csv | Historia neutral (orden de A1fixF1, total de A1fix) con la tendencia TEN-N2 | 71,34 M | 43,13 M | 22,37 M | 5,83 M |
| A1fixF1b3n_2025.csv | Designada por el participante (política v2): historia neutral con tres semillas, total de A1fixb3, sin tendencia (sección 10) | 67,17 M | 41,04 M | 20,59 M | 5,54 M |

En A1 el nuevo negocio de autos de 2025 cuesta 559 CU por año frente a 394 la renovación, porque el bloque del broker trae más conductores jóvenes y menos años de bonificación (el 28 % de 17 a 24 años frente al 16 %). Son los mismos rasgos del nuevo negocio orgánico de 2023–2024. La renovación de 2025, en cambio, abarata según las relatividades (g medio de 1,070 en 2023, 1,008 en 2024 y 0,921 en 2025) porque la cartera envejece. Esa deriva compensa casi exactamente el IBNR, lo que llevó al revisor rev3 a sospechar que A1 no lo incluía. Sí lo incluye: el último implícito de A1 en 2023–2024 es 17,76 M CU, frente a 15,86 M de T0 observado.

![Opciones de nivel](figuras/fig4_nivel_2025.png)

El revisor rev3, con su propio método (chain-ladder por peligro, Bornhuetter-Ferguson en lesiones y hundimiento, tendencia de severidad del desarrollado y relatividad del nuevo negocio con credibilidad), llega a 601, 475 y 103 CU por año, por encima de A1 (521, 432 y 94). La diferencia viene sobre todo de la tendencia y de suponer que la renovación de 2025 cuesta lo mismo que la histórica. A1T queda entre los dos.

![Incendio por año](figuras/fig5_incendio.png)

El nivel de edificios es el más incierto. El incendio es el 45 % del coste último del ramo con 70 siniestros: 49 en 2023 y 21 en 2024, cuando una tasa común daría 34 y 36 (p = 0,0003 según rev3). El exceso de 2023 se concentra en la región E02, y en el desarrollado no hay efecto año en incendio. Un modelo de incendio del desarrollado sobre `wildfire_index` predice 75 incendios frente a los 70 observados y apoya el promedio de los dos años frente a 2024 solo. Con 2023 solo, el nivel sería 590; con 2024 solo, 366.

Para decidir sobre la tendencia sin depender de dos años emergentes, hice un backtest en el desarrollado. Tomé 300 muestras por ventana con el tamaño del emergente, con relatividades fijas, y medí cuánto se aleja cada estimador del nivel del año siguiente en todo el mercado (error en logaritmo, expresado en puntos porcentuales):

| Ramo y ventana | Agrupado sin tendencia (A1): sesgo | Con tendencia: sesgo | Desviación típica |
| --- | ---: | ---: | ---: |
| Autos 2021–22 → 2023 | −12,1 % | −4,4 % | 3,9 % |
| Autos 2022–23 → 2024 | −2,1 % | +12,6 % | 13,5 % |
| Edificios 2021–22 → 2023 | −7,0 % | −2,2 % | 7,8 % |
| Edificios 2022–23 → 2024 | −11,8 % | −2,9 % | 7,4 % |
| Contenidos 2021–22 → 2023 | −8,6 % | −11,1 % | 5,4 % |
| Contenidos 2022–23 → 2024 | −5,7 % | +8,0 % | 5,4 % |

En las seis ventanas, el nivel agrupado sin tendencia (la receta de A1) se quedó corto, entre un 2 y un 12 %. La tendencia de una sola ventana corrige casi siempre, pero a veces se pasa (autos 2022–23), y por eso A1T usa la tendencia log-lineal de cuatro años. Recortar los siniestros a 100.000 CU con un factor de exceso externo reduce la varianza (en autos 2022–23 baja de 13,5 % a 3,0 %). En el emergente, sin embargo, el exceso de edificios (1,20) es mayor que el del desarrollado (1,08), así que importarlo bajaría el nivel sin justificación. Con esta evidencia y la de rev3, recomiendo aplicar la tendencia.

El revisor rev4 rehízo por su cuenta el índice y el backtest con otro método: GLM de frecuencia y severidad con factor de año, siniestros topados a 250.000 CU, IBNR por peligro con Lynden-Bell y 2.000 muestras del 10 % de las pólizas. En hogar los dos trabajos coinciden casi al punto. Su índice de edificios es 1,000, 1,031, 1,093 y 1,205 frente a mi 1,000, 1,033, 1,096 y 1,204. En contenidos tiene 1,000, 0,982, 1,077 y 1,098 frente a 1,000, 0,984, 1,078 y 1,090. Su sesgo sin tendencia en edificios (−7,0 % y −11,8 %) es casi el mío (−6,8 % y −11,1 % al pasar mi error logarítmico a porcentaje), y en contenidos pasa lo mismo (−8,0 % y −6,0 % frente a −8,2 % y −5,5 %). En autos difiere, y la causa es un solo siniestro: una lesión de 11,9 M CU en 2023, el 10 % del coste de autos de ese año. Con las relatividades corregidas por ID01, mi tendencia de autos sin tope es +4,3 % (A1T usó +4,6 %, con las de antes), y con tope a 250.000 CU baja a +3,5 % (`codigo/tendencia_tope.py`). La de rev4 con tope es +2,4 %. Las dos caben en la incertidumbre del IBNR de lesiones de 2024: rev4 muestra que multiplicarlo por 0,5 o por 1,5 mueve su tendencia de autos de −0,5 % a +5,1 %. Ese siniestro explica también el −12,1 % de mi ventana de autos 2021–22 → 2023, donde rev4, con tope, obtiene +0,4 %. Una tendencia no debe depender de un siniestro, así que fijé la regla TEN-N2: la tendencia se estima con los siniestros topados a 250.000 CU, y el exceso cuenta como carga estable. Los factores quedan en 1,055 para autos, 1,094 para edificios y 1,053 para contenidos, frente a 1,072, 1,097 y 1,054 de A1T. Solo cambia autos, y rev4 propone algo menos (cerca de 1,03). Entre 1,03 y 1,055 hay un 2,4 % de nivel en autos. Si la pérdida es cuadrática cerca del óptimo, con el coste del párrafo siguiente eso vale del orden de 0,0002 de D².

Como exploración sobre 2024 ya abierto, un error de nivel del 10 % en edificios cuesta unas 0,004 de D², y en autos, el ramo con más peso, un 10 % por debajo cuesta 0,003. Por eso el participante podría considerar una sonda de nivel como la de D100, con la lección de D103: medir el ruido frente a la parte no vista. Con el tamaño del test de 2025, la desviación típica del logaritmo del óptimo del 33 % público frente al 67 % privado ronda 0,054 en autos, 0,16 en edificios y 0,095 en contenidos. Con una incertidumbre previa de 0,07, 0,12 y 0,07, la credibilidad sería de 0,63, 0,36 y 0,35, y la ganancia esperada en el privado, del orden de +0,0005 en total. Costaría seis envíos más uno, y la decisión es del participante.

## 7. Prima comercial de las 20 referencias

La fórmula es P = [R·(1 + r) + 85·e] / (1 − v − c − t − m), con r = 0,12 en hogar (reaseguro catastrófico, «share of property risk premium»), v = 0,15, t = 0,08, m = 0,08 y c = 0,20 en broker o 0 en directo. Los denominadores quedan en 0,49 y 0,69. Los componentes suman P en cada fila. La tabla usa la prima de riesgo de A1. La última columna reparte el gasto fijo de 85 CU por póliza y año entre las filas 2025 de la misma póliza, de modo que una póliza corta lo paga entero una vez y una partida en tramos no lo paga dos veces (corrección señalada por rev3).

| Referencia | Ramo | Canal | Exposición | Riesgo R | Reaseguro | Gasto fijo | Variable | Comisión | Impuesto | Margen | Prima comercial | Con gasto fijo por póliza |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M00161473 | autos | broker | 0,9644 | 1.072,71 | 0,00 | 81,97 | 353,47 | 471,30 | 188,52 | 188,52 | 2.356,49 | 2.362,67 |
| M00176777 | autos | broker | 0,9918 | 690,01 | 0,00 | 84,30 | 237,03 | 316,04 | 126,42 | 126,42 | 1.580,22 | 1.581,64 |
| M00185311 | autos | direct | 0,9644 | 758,43 | 0,00 | 81,97 | 182,70 | 0,00 | 97,44 | 97,44 | 1.217,98 | 1.222,37 |
| M00167496 | autos | broker | 0,9836 | 471,85 | 0,00 | 83,61 | 170,04 | 226,72 | 90,69 | 90,69 | 1.133,58 | 1.136,43 |
| M00129413 | autos | broker | 0,3315 | 136,07 | 0,00 | 28,18 | 50,28 | 67,04 | 26,82 | 26,82 | 335,19 | 451,16 |
| M00118569 | autos | direct | 0,9397 | 523,09 | 0,00 | 79,87 | 131,08 | 0,00 | 69,91 | 69,91 | 873,87 | 881,30 |
| M00153851 | autos | broker | 0,9616 | 280,52 | 0,00 | 81,74 | 110,90 | 147,86 | 59,14 | 59,14 | 739,31 | 745,97 |
| B00229821 | edificios | broker | 0,9918 | 254,95 | 30,59 | 84,30 | 113,22 | 150,96 | 60,38 | 60,38 | 754,80 | 756,22 |
| B00218282 | edificios | broker | 0,9726 | 264,46 | 31,74 | 82,67 | 115,98 | 154,64 | 61,86 | 61,86 | 773,20 | 777,95 |
| B00250679 | edificios | broker | 0,1096 | 26,71 | 3,21 | 9,32 | 12,01 | 16,01 | 6,41 | 6,41 | 80,07 | 208,67 |
| B00223369 | edificios | broker | 0,9945 | 332,33 | 39,88 | 84,53 | 139,82 | 186,43 | 74,57 | 74,57 | 932,13 | 933,08 |
| B00215809 | edificios | direct | 0,9753 | 619,64 | 74,36 | 82,90 | 168,89 | 0,00 | 90,07 | 90,07 | 1.125,93 | 1.128,98 |
| B00215707 | edificios | broker | 0,9863 | 238,67 | 28,64 | 83,84 | 107,49 | 143,32 | 57,33 | 57,33 | 716,62 | 718,99 |
| B00217584 | edificios | broker | 0,9671 | 765,02 | 91,80 | 82,20 | 287,46 | 383,28 | 153,31 | 153,31 | 1.916,39 | 1.922,09 |
| C00259568 | contenidos | broker | 1,0 | 51,85 | 6,22 | 85,00 | 43,80 | 58,40 | 23,36 | 23,36 | 291,99 | 291,99 |
| C00283470 | contenidos | broker | 0,9726 | 54,14 | 6,50 | 82,67 | 43,87 | 58,49 | 23,40 | 23,40 | 292,47 | 297,22 |
| C00270331 | contenidos | broker | 0,9726 | 35,03 | 4,20 | 82,67 | 37,32 | 49,76 | 19,90 | 19,90 | 248,78 | 253,53 |
| C00314425 | contenidos | broker | 0,0685 | 3,42 | 0,41 | 5,82 | 2,95 | 3,94 | 1,58 | 1,58 | 19,69 | 20,10 |
| C00302985 | contenidos | broker | 0,9918 | 58,74 | 7,05 | 84,30 | 45,95 | 61,26 | 24,50 | 24,50 | 306,31 | 307,73 |
| C00286287 | contenidos | broker | 0,9671 | 108,99 | 13,08 | 82,20 | 62,53 | 83,38 | 33,35 | 33,35 | 416,89 | 422,60 |

Dos lecturas. La prima comercial anualizada es entre 0,85 y 6,1 veces la prima escrita, porque la tarifa vigente del emergente cubre poco más que el riesgo: en el test, la prima escrita por año es 777 en autos, 427 en edificios y 154 en contenidos, frente a primas de riesgo de A1 de 521, 432 y 94. Aun así, esa razón no debe leerse como la subida de tarifa necesaria, porque la prima escrita no lleva la estructura de gastos de la tabla. Quedan dos supuestos declarados: el impuesto va dentro del denominador porque su unidad es «share of premium» (si se cobrara encima, P bajaría un 7,2 % en broker), y la comisión de comparador falta para el emergente, aunque ninguna referencia usa ese canal.

## 8. Parte 1: revalidación y escalera

![Escalera de la parte 1](figuras/fig3_escalera_p1.png)

| Peldaño (ajuste 2021–2023, T0 de 2024) | D² | Forma (nivel oráculo) | Cuerpo | Frente a S30, IC90 |
| --- | ---: | ---: | ---: | --- |
| Tasa por ramo | 0,0736 | 0,0750 | 0,0802 | −0,0643 [−0,0693; −0,0597] |
| GLM Tweedie, esquema común | 0,1195 | 0,1197 | 0,1026 | −0,0184 [−0,0229; −0,0149] |
| Un GBM, esquema común | 0,1239 | 0,1247 | 0,1049 | −0,0140 [−0,0197; −0,0100] |
| Un GBM, todas las F0 | 0,1295 | 0,1305 | 0,1078 | −0,0084 [−0,0109; −0,0062] |
| Un GBM, F0 + historia de la póliza | 0,1314 | 0,1319 | 0,1089 | −0,0065 [−0,0087; −0,0045] |
| S30 | 0,1379 | 0,1381 | 0,1113 | — |

Mis etiquetas de 2024 coinciden exactamente con las de S30 en las 626.190 filas, y rev3 lo confirmó por su lado con su propio T0. El D² de S30 en V24 (0,137880) coincide con el registrado. Un solo GBM estándar con las variables del contrato y la historia de la póliza logra el 95 % del D² de S30, y un GLM el 87 %. La tabla ya lleva la corrección ID01; antes de corregirla los GBM de autos quedaban entre 0,0001 y 0,0005 más abajo. La parte de S30 que no alcanza un modelo estándar (+0,0065) es robusta, así que la complejidad de la parte 1 estaba justificada. Para la semana 2 deja una lección: con poco dato, el orden de la escalera cambia, y lo que más rinde es transferir y no complicar.

El IBNR de autos con mi estimador queda un 2,7 % por debajo del de D67, en la misma dirección que el ajuste de nivel de autos que pidió el tablero público (D100). La parte 1 está cerrada y nada de esto cambia la entrega S41.

## 9. Conciliación final con el catálogo de Codex

Como se acordó, comparé con las cifras previas solo al final. Copié las OOF de desarrollo 2023 de Codex de la corrida dev7 (W2-B00 a W2-B18, SHA 24394549…15beacb7) y las medí con mi métrica junto a las mías (`codigo/conciliacion_codex.py`). Las filas son las mismas 50.094, el objetivo coincide exactamente (15.297.103,84 CU) y la desviación nula también. Con mi código reproduzco al quinto decimal los D² que Codex publicó: B00 0,06858, B10 0,09424 y B14 0,08671. El vínculo de observación de Codex y mi exposición efectiva difieren un 0,4 % en total, con un cociente por fila de 0,993 a 1,022 (p1 a p99). Los folds son distintos, pero cada OOF usa los suyos.

| Par (desarrollo 2023, IC 90 % por componentes) | Completo | Cuerpo (sin el 0,1 % superior) |
| --- | ---: | ---: |
| Tasa: Codex B00 − mi L0 | +0,0009 [−0,0008; +0,0026] | +0,0003 |
| Solo emergente: Codex B10 − mi GBM | +0,0110 [−0,0009; +0,0229] | +0,0188 |
| A1 − Codex B10 (la mejor de sus 21 recetas) | +0,0270 [+0,0141; +0,0402] | +0,0177 [+0,0121; +0,0235] |
| A1 − Codex B14 | +0,0345 [+0,0134; +0,0543] | +0,0264 |
| A1fixF1 − Codex B10 | +0,0320 [+0,0187; +0,0460] | +0,0177 |

Lectura. La tasa de referencia es la misma en los dos trabajos. Entre los modelos entrenados solo con el emergente, los GLM de Codex son mejores que los míos, sobre todo en el cuerpo (+0,019): sus variables y su regularización están más trabajadas, y mis peldaños solo emergentes se quedaron cortos. Aun así, la transferencia del desarrollado supera a todas las recetas del catálogo por +0,027 o más, con el intervalo lejos de cero también en el cuerpo. Gana en los tres ramos y en renovación, y en nuevo negocio queda a la par (0,082 frente a 0,080). Además, B10 tiene un A/E de 1,080 frente a 1,000 de A1. Las recetas del catálogo de Codex usan solo datos emergentes. Si el proyecto quiere incorporar la transferencia a su selección común, ya es tarde para una confirmación intacta en 2024 (se consultó esta noche), y la decisión es del participante.

## 10. Decisiones del participante y producción designada

El 24 de octubre, a las 09:46 de Bogotá, el participante respondió a las cuatro decisiones abiertas: enmendar la salvaguarda de cliente nuevo, producir sin tendencia, adoptar la versión 2 con la historia neutral y el promedio de tres semillas, y llevar la transferencia a la selección común. Las dos últimas siguen mi recomendación. La segunda no: yo recomendaba la tendencia.

La enmienda está en `preinscripcion/politica_seleccion_v2_20261024.json` (S2-SELECCION-v2-20261024) y se apoya en lo que v1 prevé: una enmienda humana explícita, versionada, que conserva v1 y su acta y no restaura una confirmación intacta. Cambia una sola cosa. La salvaguarda de cliente nuevo pasa a exigir solo que la diferencia puntual sea ≥ 0, y el límite inferior del 95 % se sigue informando, pero como diagnóstico. El motivo es la potencia que midió rev2 (sección 5): con ese margen la regla funcionaba como una prueba de superioridad y no como la salvaguarda de no inferioridad que v1 dice ser. El acta enmendada (`codigo/puerta_enmienda.py`) aplica la regla nueva a las cifras del acta original, comprobada por su SHA, sin leer etiquetas. A1 frente a R0 pasa la primaria (+0,0486, límite +0,0265) y todas las salvaguardas: cliente nuevo +0,0131 ≥ 0, con el límite diagnóstico en −0,0105. A1 promueve. A2 frente a A1 no pasa la primaria (−0,0040 [−0,0104; +0,0025]). Titular de la versión 2: A1. La enmienda se decidió conociendo el acta, y así queda escrito en la política.

La receta de producción de la versión 2 es A1 con la corrección ID01, la historia neutral y tres semillas (11, 12 y 13) del GBM desarrollado con historia (`codigo/cadena_semillas_f1.sh`, `codigo/evaluar_final.py`). Con tres semillas la historia aporta menos que con la semilla 11 sola, que había salido favorable:

| Historia neutral frente a la misma receta sin historia, tres semillas | Completo | Cuerpo (sin el 0,1 % superior) |
| --- | ---: | ---: |
| Desarrollo 2023 (OOF) | +0,0020 [+0,0002; +0,0043] | +0,0000 |
| 2024, exploratorio | +0,0025 [+0,0012; +0,0039] | +0,0020 [+0,0011; +0,0028] |

La ganancia es positiva en los dos periodos. En 2023 viene de la cola, porque casi nadie tiene historia emergente, y en 2024 también aparece en el cuerpo. El D² de 2024 de la receta final es 0,1244, frente a 0,1214 de A1 (+0,0030 [+0,0013; +0,0047]). Con calibración en 2023, la historia de tres semillas subiría el total de autos de 2024 un 3,9 %, y por eso va en versión neutral.

Producción designada, sin enviar: `A1fixF1b3n_2025.csv`, con 209.063 filas en el orden de la plantilla y SHA f786deb3…224c53aa. Suma 67,17 M CU: autos 41,04 M, edificios 20,59 M y contenidos 5,54 M, que son 519,5, 434,6 y 93,8 CU por año-exposición. Sin tendencia, el total por ramo es el de A1fixb3, y la historia solo reparte. Frente a A1fixb3, la mediana del cambio por fila es del 3,3 % y el p99 del 30,5 %. Las 20 primas comerciales de referencia con esta prima de riesgo están en `salidas/correccion/prima_comercial_designada.csv` y suman 16.493 CU, frente a 16.112 con A1. El mayor cambio es M00118569 (+49 %), una renovación con dos siniestros aceptados en 2023. El envío lo hace Codex solo si el participante lo autoriza.

Sobre el nivel: con la decisión de no aplicar tendencia, los backtests de la sección 6 indican que el nivel de hogar puede quedar corto entre un 5 y un 12 %. A1fixTc y A1fixF1nTc siguen disponibles si el participante cambia de opinión.

La transferencia entra en la selección común como titular de la semana 2. Las alternativas de Codex se conservan. No modifiqué el registro de selección de Codex (`semana2_seleccion_actual.json`), y la decisión queda en DECISIONES.md, en ESTADO_PROYECTO.json y en el foro para que Codex la integre.

La interpretación del impuesto y el reparto del gasto fijo de la prima comercial siguen como se decidieron (gasto × exposición, con la sensibilidad por póliza corregida).

### Validación antes del envío

El participante pidió validar todo antes de enviar. Hice cuatro comprobaciones más.

1. El revisor independiente rev5 rehízo la producción a partir de la descripción de la receta, sin ver mi código ni mis conclusiones (`revision/rev5/`). Sus dos archivos, A1fixb3 y la designada, coinciden con los míos hasta el sexto decimal: la diferencia máxima es de 5e-7 CU, y los totales por ramo son iguales. También comprobó el T0 contra los siniestros brutos. El archivo es válido para Kaggle:
   - tiene las 209.063 filas de prueba en el orden de la plantilla, sin duplicados ni faltantes;
   - el encabezado es `row_id,prediction`, en ASCII con saltos LF, con predicciones finitas y positivas;
   - son totales por fila y no tasas anuales.

   La historia de la póliza no tiene fuga. Para 2025 solo entran siniestros reportados antes del 1 de enero, y el periodo de cada fila nunca alimenta su propio rasgo. Probó por separado el periodo propio, los siniestros futuros, los repudiados y el mercado equivocado, y ninguno da señal. Su réplica del código coincide con sus propios conteos sin diferencias. Con la regla v2, también llega a A1 como titular. Su veredicto es que el archivo está listo y no tiene bloqueos.
2. Reproducibilidad. Reentrené dos de los GBM de la receta, la semilla 12 de autos y la 13 de edificios. Dan relatividades idénticas bit a bit.
3. Factor de nivel para el nuevo negocio. rev5 señaló que, con el nivel de 2023–2024 agrupado, el nuevo negocio sale por encima del modelo: A/E de 1,26 en autos y 1,27 en contenidos con la receta final. La prueba está en `codigo/nb_nivel_revision.py`. Como el nuevo negocio es el 77 % de la exposición de 2025, ese factor subiría el total de autos un 19 %. Lo probé fuera de tiempo, estimándolo en 2023 y midiéndolo en 2024, que ya estaba abierto, así que la prueba es exploratoria. En autos, el nuevo negocio de 2023 salió muy por encima (A/E 1,62 frente a 0,94 de la renovación), pero en 2024 no se repitió (1,09 frente a 1,10). Con el factor de 2023, el D² de 2024 baja:

| Factor de nuevo negocio estimado en 2023, medido en 2024 (receta final) | Diferencia de D² | IC 90 % |
| --- | ---: | ---: |
| Bruto | −0,0010 | [−0,0026; +0,0008] |
| Con siniestros topados a 100.000 CU | −0,0014 | [−0,0029; +0,0003] |
| Con credibilidad (Z = n / (n + 300)) | −0,0001 | [−0,0009; +0,0009] |

   El exceso de 2023 no anticipó 2024, y ninguna variante mejora. Por eso no añado el factor y la producción no cambia. Es la misma conclusión que se tomó antes de abrir 2024. El riesgo sigue ahí: si el nuevo negocio de 2025 se pareciera al de 2023, autos quedaría corto.
4. Puntos no bloqueantes que deja rev5. En las 2.961 renovaciones de 2025 que empiezan después del 1 de enero, la historia cuenta menos de lo que contaría en el entrenamiento, porque los datos terminan el 31 de diciembre. El estado «repudiado» es el del cierre de 2024 también en el entrenamiento. En hogar, el alza por historia no se ve en la experiencia emergente, aunque con tan poco volumen no se puede concluir. Ninguno cambia el archivo.

5. Comparación con la línea ML independiente de Claude. Otra sesión de Claude, que trabajó sin mirar esta línea, llegó también a la transferencia: un LightGBM Tweedie entrenado en el desarrollado con nivel por ramo (T2b). Su producción, `prediccion_2025_mlind.csv` (SHA d261388c…), es la segunda estimación independiente y la comparé al final con la designada (`codigo/conciliacion_mlind.py`). Las dos coinciden en lo que decide el participante:
   - en 2024, la tendencia del desarrollado les resta D² (−0,0016);
   - un factor de nuevo negocio que ganaba en 2023 pierde en 2024 (exceso de autos 1,55 en 2023 y 1,00 en 2024).

   Las predicciones de 2025 se parecen mucho: la correlación de los logaritmos es 0,985 en autos, 0,969 en edificios y 0,969 en contenidos. Los totales difieren +5,3 % en autos, +7,6 % en edificios y −1,1 % en contenidos. La diferencia viene sobre todo de cómo cada modelo traslada la mezcla de 2025, con un 77 % de nuevo negocio; las completitudes de 2024 casi coinciden (autos 0,803 en su línea frente a 0,816 en la mía).

   Para comparar el orden sin la escala, reescalé sus predicciones por ramo al total de las mías, sin usar siniestros. Las predicciones guardadas de su 2024 están en escala de último, no del T0 observado. Resultados:

| Frente a la designada, a igual total por ramo | Desarrollo 2023 | 2024 (exploratorio) |
| --- | ---: | ---: |
| T2b sola | +0,0042 [−0,0027; +0,0109] | +0,0007 [−0,0028; +0,0040] |
| Media 50/50 de las dos | +0,0039 [+0,0004; +0,0074] | +0,0012 [−0,0005; +0,0029] |

   La media gana en los dos periodos, también en el cuerpo (+0,0006 y +0,0013), aunque en 2024 el intervalo cruza cero. Es la ganancia habitual de promediar dos implementaciones independientes muy correlacionadas. Dejé preparada esa opción con el total por ramo de la designada, para respetar el nivel decidido: `A1fixF1b3n_mlind50n_2025.csv`, 67,17 M CU, SHA 0df5009c…c3dcacf7. Frente a la designada, la mediana del cambio por fila es del 5,5 %. A petición del participante, la sesión ML preparó además la media 50/50 sin igualar totales (`mezcla50_designada_mlind_2025.csv`, SHA 12831ef4…, foro 016). Esa mezcla promedia también el nivel de las dos líneas y suma 69,00 M CU: 42,12 M en autos, 21,37 M en edificios y 5,50 M en contenidos. Dentro de cada ramo, las dos mezclas ordenan las pólizas casi igual: la correlación de sus logaritmos es 0,99999 o más, y la razón entre ellas varía por fila menos del 0,4 %. En la práctica solo cambia el total: la de la sesión ML suma un 2,6 % más en autos, un 3,8 % más en edificios y un 0,6 % menos en contenidos. Comprobé que la suya es exactamente la media de los dos archivos, y que las tres opciones (la designada y las dos mezclas) pasan los controles de formato de Kaggle. Cuál se envía lo decide el participante.

Queda una condición externa. Nadie ha comprobado todavía que Kaggle acepte ya envíos de 209.063 filas tras el arreglo anunciado por HOST. Lo dirá el primer envío, que hace Codex con la autorización expresa del participante.

### Decisión final

A las 10:55 de Bogotá el participante eligió la mezcla de la sesión ML, `mezcla50_designada_mlind_2025.csv`, y autorizó que Codex la envíe. El archivo tiene SHA 12831ef4a05c1773824abe5fa139d9503dd2989b4874e7d93cfc000406cfdb4a y suma 69,00 M CU (autos 42,12 M, edificios 21,37 M, contenidos 5,50 M). Antes de subirlo, Codex debe comprobar ese SHA y que Kaggle ya acepta las 209.063 filas. Si Kaggle lo rechaza, el archivo no se toca y se avisa en el foro.

Las 20 primas comerciales de referencia calculadas con esta prima de riesgo están en `salidas/correccion/prima_comercial_envio.csv` (`codigo/prima_comercial_envio.py`) y suman 16.794,68 CU. Coinciden al céntimo con las que calculó por su lado la sesión ML. En la sensibilidad del gasto fijo por póliza hay diferencias de hasta 0,04 CU.

La designada, la mezcla neutral y las variantes con tendencia se conservan como alternativas. 2024 no es una confirmación intacta para la mezcla, y todo lo medido sobre ese año después de abrirlo es exploratorio.

### Primer envío y sonda de nivel

Codex envió la mezcla (envío 57599788). Kaggle procesó las 209.063 filas y dio un D² público de 0,15390, el puesto 5 de 7 equipos. Ese número sale de una parte del test 2025 (el público, en torno a un tercio) y no se compara con los D² de 2023 o 2024. Tampoco sabemos todavía a qué distancia están los otros equipos.

La duda más grande que queda es el nivel de cada ramo, y el tablero público lo puede medir con exactitud. Con la desviación Tweedie 1,5, si se multiplican las predicciones de un ramo por c, el D² público cambia según una fórmula con solo dos incógnitas por ramo. Dos envíos por ramo, cada uno escalando solo ese ramo, bastan para despejar el nivel óptimo del público, c* = Σ y μ^(−1/2) / Σ μ^(1/2), sin saber qué filas son públicas (`codigo/sonda_nivel_diseno.py`). Simulé el procedimiento con 2024 como sustituto, con un 33 % al azar como público y las puntuaciones redondeadas a 5 decimales como las da Kaggle. El error del logaritmo de c* por redondeo es como mucho 0,001 en autos, 0,006 en edificios y 0,003 en contenidos.

El nivel del público no es el del privado. Al tamaño del test 2025, la desviación típica entre los dos es de 0,051 en autos, 0,157 en edificios y 0,087 en contenidos. Por eso la regla aplica credibilidad: nivel final = c*^Z, con Z = τ² / (τ² + σ²), acotado entre 0,80 y 1,25. La incertidumbre previa τ quedó fijada antes de enviar: 0,10 en autos, 0,20 en edificios y 0,07 en contenidos. Eso da Z de 0,796, 0,618 y 0,395 (`salidas/sonda/preinscripcion_sonda.json`). Aplicada a 200 particiones de 2024, esa misma regla ganó en el privado +0,0069 de media (p05 +0,0045, p95 +0,0089) y ganó en todas. Casi todo vino de edificios, donde 2024 quedó muy por debajo de lo esperado. Para 2025, con la incertidumbre fijada, la ganancia esperada es del orden de +0,0016. Cuesta seis envíos más el final, de los nueve disponibles hoy, y el cierre es el 30 de octubre. Los seis archivos de sonda están preparados, y el script que construye el final a partir de los seis D² públicos ya está probado (`codigo/sonda_nivel_resolver.py`).

El participante no quiso usar sondas («no nos fue bien el anterior envío mandando Sondas, prefiero seguir trabajando en modelos más robustos»), y los archivos quedan guardados sin usar.

### Modelos más robustos

Fijé cuatro candidatos con su regla antes de medir (`salidas/robustez/preinscripcion_robustez.json`). Un candidato entra solo si mejora en el desarrollo 2023 y en 2024, con el IC 90 % por encima de cero en al menos uno de los dos y sin empeorar el cuerpo más de 0,0005. En 2024 la comparación es a igual nivel por ramo, para medir solo el orden. Todos usan tres semillas (`codigo/robustez_evaluar.py`):

| Candidato | Frente a | Desarrollo 2023 | 2024 | Regla |
| --- | --- | ---: | ---: | --- |
| C1: relatividades con siniestros topados a 100.000 CU | designada | −0,0015 [−0,0049; +0,0014] | +0,0003 [−0,0008; +0,0012] | no pasa |
| C2: árboles más regularizados (15 hojas, 3.000 filas por hoja, λ 50) | designada | +0,0015 [−0,0002; +0,0032] | +0,0019 [+0,0005; +0,0033] | pasa |
| C3: media de un GLM y el GBM | designada | −0,0012 [−0,0039; +0,0016] | +0,0011 [−0,0011; +0,0035] | no pasa |
| C4: rejilla elegida con la validación interna del desarrollado | C2 | −0,0004 [−0,0015; +0,0006] | +0,0016 [+0,0005; +0,0028] | no pasa |

C2 mejora también el cuerpo (+0,0023 en 2023 y +0,0021 en 2024), mejora los tres ramos de 2024 y mejora la validación interna del desarrollado en los tres ramos. Las relatividades más suaves se trasladan mejor al mercado emergente. Con C2 dejé lista, sin enviar, `mezcla50_robusta_2025.csv` (SHA 82082f3c…, `codigo/produccion_robusta.py`). Es la misma mezcla enviada, con nuestro componente regularizado, y tiene los mismos totales (69,00 M CU). A igual nivel, gana a la enviada +0,0007 [−0,0002; +0,0014] en 2023 y +0,0009 [+0,0002; +0,0016] en 2024. La mejora es pequeña y consistente: hace más sólido el orden, pero no cambia el nivel, que es lo que más pesa en la puntuación.

El participante autorizó enviarla. Codex la subió (envío 57602707) y el público dio 0,15347, por debajo del 0,15390 de la primera mezcla. Medí cuánto ruido tiene esa diferencia entre dos archivos tan parecidos remuestreando 2024 al tamaño del público de 2025 (`codigo/ruido_publico_pares.py`): la desviación típica es de 0,0004 alrededor de +0,0009, así que −0,00043 no se explica por azar si 2025 se comportara como 2024. Tampoco lo explica la composición de la cartera. Ponderé 2024 para que se parezca a 2025, con un 78 % de nuevo negocio (`codigo/validacion_2025.py`), y la mezcla robusta seguiría ganando +0,0016 [−0,0003; +0,0036]. Si se combina esa evidencia con la del público, la diferencia esperada en el privado entre las dos mezclas es casi nula. Codex (COD-S2-VAL08-20261024-INFERENCIA-PUBLICO) señala, con razón, que estos dos cálculos usan las respuestas de 2024 y suponen que la relación entre las variables y el coste se traslada a 2025. Por eso no descartan el azar del reparto de 2025 ni cualquier deriva de cartera, y la causa de la diferencia sigue sin identificar. Son sensibilidades bajo esos supuestos, no un descarte. La lección es que 2023–2024 no permiten separar mejoras de ±0,001 que valgan en 2025. También probé la prima escrita como señal adicional y no ayuda: baja el D² de 2024 en autos y contenidos (`salidas/robustez/prima_escrita_prueba.json`).

### El criterio DES24 tampoco habría anticipado la caída

La línea ML independiente propuso medir la estructura en el desarrollado de 2024, fuera de tiempo. Allí hay muchas más filas que en el emergente: 254.698 en autos, 184.001 en edificios y 187.491 en contenidos. Lo apliqué a mis candidatos con los modelos de confirmación ya guardados, entrenados con el desarrollado 2021-2023. Usé las mismas variables y la misma historia de la póliza. El nivel se reajusta en 2024 en cada ramo, de modo que solo se mide el orden (`codigo/des24_candidatos.py`, `salidas/robustez/des24_candidatos.json`).

| Frente a la designada | Global | Autos | Edificios | Contenidos |
| --- | ---: | ---: | ---: | ---: |
| Sin historia de la póliza | −0,0034 [−0,0043; −0,0026] | −0,0050 | −0,0029 | −0,0015 |
| C1, tope a 100.000 CU | −0,0005 [−0,0013; +0,0002] | +0,0002 | −0,0015 | −0,0002 |
| C2, regularizado | +0,0011 [+0,0006; +0,0016] | +0,0011 | +0,0009 | +0,0015 |
| C4, rejilla interna | +0,0016 [+0,0009; +0,0023] | +0,0011 | +0,0021 | +0,0020 |

DES24 confirma que la historia de la póliza ayuda y que el tope no. También prefiere C2 a la designada, con el intervalo por encima de cero y en los tres ramos. Las tres validaciones que tenemos son 2023 emergente, 2024 emergente y 2024 desarrollado, y las tres daban la mezcla robusta por mejor. El público dijo lo contrario. Con un tamaño de muestra mayor, DES24 sirve para descartar ideas que empeoran mucho. Para diferencias de ±0,001 entre modelos casi iguales, no anticipa 2025, porque lo que cambia en 2025 es el mercado y la cartera, no el tamaño de la muestra.

### El tablero y la sonda de nivel global

El participante compartió el tablero público: estamos séptimos de siete con 0,15390. El primero tiene 0,16446 y el cuarto 0,16170, este último con un solo envío. La distancia, de 0,0078 a 0,0106, es unas diez veces lo que mueven los retoques de orden, y tiene el tamaño de un error de nivel. En 2024, con la designada, quedarse un 20 % por debajo del nivel óptimo cuesta 0,0070 de D², y pasarse un 30 % cuesta 0,0097. Saltos así ocurren entre años. Con el nivel de 2023, el cociente real/esperado de 2024 fue 1,10 en autos y 0,62 en edificios. Además, en 2025 el 76 % de las filas es nuevo negocio, frente al 12 % de 2023 y el 15 % de 2024, y el nivel de ese bloque no se puede aprender de 2023-2024.

El participante eligió una sonda de nivel global (`codigo/sonda_global.py`). Es la misma fórmula de la sonda por ramo, aplicada a un factor común para todas las filas. Si todas las predicciones se multiplican por c, el D² público cambia según D²(1) − D²(c) = βA (c^(−1/2) − 1) + βB (c^(1/2) − 1). Con la mezcla ya puntuada y dos envíos más (la mezcla por 0,85 y por 1,20), se despejan βA y βB, y el óptimo del público sale exacto: c* = βA / βB. Simulado con 2024 y con las puntuaciones redondeadas a 5 decimales, el error del logaritmo de c* es como mucho 0,0004.

El óptimo del público no coincide con el del privado. Remuestreé 2024 por componentes al tamaño de 2025 y la desviación típica entre los dos sale 0,0496. Por eso se aplica credibilidad: c_final = c*^Z, con τ = 0,12 fijado antes de ver ninguna puntuación (el salto global de 2023 a 2024 fue de log −0,12) y Z = 0,854, acotado entre 0,75 y 1,33. La regla completa, probada al tamaño de 2025 (`salidas/sonda_global/backtest_2024.json`), da estos resultados en el privado:

| Escenario de nivel | Ganancia media | p05 a p95 | Gana |
| --- | ---: | --- | ---: |
| Como salió 2024 (óptimo 0,92) | +0,0009 | −0,0003 a +0,0020 | 90 % |
| Nivel correcto | −0,0002 | −0,0010 a +0,0002 | 28 % |
| Nivel un 30 % alto | +0,0095 | +0,0063 a +0,0127 | 100 % |
| Nivel un 20 % bajo | +0,0066 | +0,0043 a +0,0095 | 100 % |
| Error sorteado de la previa (τ = 0,12) | +0,0018 | −0,0006 a +0,0089 | 78 % |

Si el nivel ya está bien, la sonda cuesta unas dos diezmilésimas. Si está desviado un 20-30 %, recupera casi todo lo que se pierde. Un revisor independiente comprobó la fórmula (residuo de 2e−16 frente al cálculo directo), los dos CSV (iguales a la mezcla por c en todas las filas, con los SHA de la preinscripción) y la recuperación de c* con niveles verdaderos entre 0,60 y 1,39. Pidió dos cosas y ya están hechas: el resolutor se detiene sin escribir el archivo final si c* no es identificable o si |log c*| > 0,4, y la preinscripción incluye la cifra ponderada por la previa. Además señaló que Z podría ser 0,90. Se mantiene 0,854, que es más conservador; la diferencia en la ganancia esperada es menor de 0,00001.

Cuesta tres envíos de los ocho que quedan: las dos sondas y el archivo final. Los archivos están en `Repositorio_IAA2026/privado/semana2/claude_validacion_nocturna_20261023/sonda_global/`: `sonda_global_0.85.csv` (SHA c59923b0…) y `sonda_global_1.20.csv` (SHA 02b1f58b…). La preinscripción está en `salidas/sonda_global__preinscripcion.json`; la revisión, en `revision/rev6/revisor_sonda_global.md`. Codex los envía solo con la autorización expresa del participante. Con las dos puntuaciones, `codigo/sonda_global_resolver.py 0.85=D2 1.20=D2` construye el archivo final.

Resultado. Con la autorización del participante, Codex envió las dos sondas. El D² público fue 0,14095 con el factor 0,85 y 0,15955 con 1,20, frente al 0,15390 de la mezcla. La fórmula da βA = 0,6213 y βB = 0,5080, los dos positivos. El óptimo del público es c* = 1,2231: el público pide un nivel un 22 % más alto que el de la mezcla, lejos del límite de parada (log 0,20 frente a 0,4). Como las puntuaciones vienen redondeadas a cinco decimales, c* queda entre 1,2225 y 1,2237. La regla preinscrita da c_final = 1,2231^0,854 = 1,1877.

El archivo final es `final_sonda_global_2025.csv` (SHA 42659dbb…), la mezcla multiplicada por 1,1877 en todas las filas. Suma 81,94 M CU: autos 50,03 M, edificios 25,38 M y contenidos 6,54 M. Comprobaciones: 209.063 filas en el orden de la plantilla, cabecera `row_id,prediction`, saltos LF, todos los valores positivos e idénticos como texto a la mezcla por el factor exacto. Su D² público previsto es 0,15948, algo menos que la sonda de 1,20, porque la credibilidad no aplica el óptimo del público entero y ese óptimo trae ruido que no se traslada al privado. Codex lo envió con autorización del participante (envío 57612023) y dio 0,15948, exactamente lo previsto: la métrica se comporta como supone la fórmula. Como control indirecto, la desviación nula por fila que implica βB es 127,8, frente a 110,6 en 2023 y 93,4 en 2024. Es coherente con un nivel de costes más alto y con la cola, y no detiene la regla (`salidas/sonda_global__resultado.json`).

### Sonda de nivel por ramo y nuevo negocio (preparada, sin enviar)

La sonda global solo mide un factor común. Para saber dónde está la falta de nivel, el participante pidió diseñar una sonda por segmento antes de gastar envíos (`codigo/sonda_segmento_diseno.py`). La fórmula se separa por celdas: si en el archivo final F solo se multiplica una celda s por K, el cambio de D² público es a_s [(gK)^(−1/2) − g^(−1/2)] + b_s [(gK)^(1/2) − g^(1/2)]. Lo que se necesita de cada celda se obtiene así:

- b_s no necesita envío: es βB por la cuota de la celda en Σ μ^(1/2) del test, si el público es un tercio al azar. El revisor midió que esa aproximación cambia log c*_s en menos de 0,001.
- a_s sale de un envío por celda.
- La celda mayor se deduce de βA, así que S celdas cuestan S − 1 envíos.

El nivel final de cada celda se acerca al global con credibilidad: c_s = g × (c*_s / c*_g)^Z_s, con τ = 0,20 fijado antes de ver nada y σ_s medido frente al privado. La simulación remuestrea 2023 y 2024 al tamaño de 2025 y a su composición de ramo × nuevo negocio (76 % de nuevo negocio) y mide la ganancia en el privado frente a F:

| Segmentación | Envíos | Sin desviación por celda | Desviaciones como en 2024 / 2023 | Desviaciones de la previa |
| --- | ---: | --- | --- | --- |
| Nuevo negocio / renovación | 1 | −0,0002 / −0,0003 | +0,0001 / +0,0053 | +0,0006 / +0,0006 |
| Ramo | 2 | −0,0004 / −0,0004 | +0,0112 / +0,0110 | +0,0011 / +0,0009 |
| Ramo × nuevo negocio | 5 | −0,0005 / −0,0006 | +0,0112 / +0,0175 | +0,0026 / +0,0022 |

La elegida es ramo × nuevo negocio, en seis celdas. Si ninguna celda se desvía del nivel global, cuesta unas cinco diezmilésimas. Si las celdas se desvían como lo hicieron en 2023 o 2024, gana más de una centésima. El revisor independiente señaló que el escenario de la previa favorece por construcción a las segmentaciones con más celdas, y que frente a la de solo ramo la ventaja depende de que el nuevo negocio y la renovación se aparten entre sí: en la repetición de 2024 esa separación no gana nada.

Hay cinco archivos, en `Repositorio_IAA2026/privado/semana2/claude_validacion_nocturna_20261023/sonda_segmento/`. Cada uno es F con una sola celda multiplicada por 1,2: renovación de autos, edificios y contenidos, más nuevo negocio de edificios y de contenidos. El nuevo negocio de autos se deduce. La preinscripción (`salidas/sonda_segmento__preinscripcion.json`) fija las reglas de lectura:

- Z por celda, con el mayor σ de los dos años, porque las celdas de nuevo negocio vienen de pocos siniestros (35 a 348).
- El orden de envío: primero F; las sondas, solo si su puntuación encaja con lo previsto (0,15947 o 0,15948). F ya se envió y dio 0,15948, así que esta parada no se activa.
- Las puntuaciones entran por nombre de archivo o por SHA-256, nunca por nombre de celda.
- Las paradas: si D²(F) no encaja, si algún a_s no es positivo, o si alguna celda se aparta del global más de max(0,7; 3σ) en logaritmo.

El revisor (`revision/rev6/revisor_sonda_segmento.md`) no encontró bloqueos y sus correcciones están aplicadas.

## 11. Límites

Todas las verificaciones son de IA (esta sesión y cuatro subagentes), no una revisión profesional humana. Las etiquetas de 2023 y 2024 están valoradas al mismo cierre, así que la confirmación es temporal pero no un backtest histórico estricto. El nivel 2025 depende de supuestos que dos años de datos no pueden validar (tendencia, incendio, comportamiento del bloque transferido). La transferencia supone que las relatividades del desarrollado valen en el emergente para las variables comunes; la confirmación de 2024 lo respalda para el nuevo negocio orgánico, no para el bloque de enero de 2025. 2024 ya no es una confirmación intacta: cualquier análisis posterior sobre ese año es exploratorio y así se marca.

## Archivos

En esta carpeta: `BITACORA.md`, `INFORME.md`, `preinscripcion_puerta_2024.json` (SHA 802368ea…82c407), `puerta_2024_resultado.json` (SHA b3faaece…a449b080), `codigo/`, `figuras/`, `salidas/` (agregados, sin filas), `revision/` (informes de los cuatro revisores) y los aportes y recibos del foro. Los CSV de 2025 y las tablas por fila están en `Repositorio_IAA2026/privado/semana2/claude_validacion_nocturna_20261023/`, fuera de Git, con sus SHA en `salidas/produccion__produccion_info.json`, `salidas/correccion__evaluacion_correccion.json`, `salidas/correccion__produccion_tendencia_tope.json`, `salidas/correccion__f1_nivel.json` y `salidas/correccion__evaluacion_final.json`. La política v2 está en `preinscripcion/politica_seleccion_v2_20261024.json` y el acta enmendada en `salidas/conf__puerta_2024_acta_enmendada.json`.
