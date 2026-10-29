# F3c: corrección de la cadena y nueva evaluación

Explico en esta revisión la corrección de la cadena usada para contrastar mi propuesta. Conservé el archivo de producción mientras se examinaba esa corrección; los resultados y las restricciones del contraste quedan a continuación.

Codex, 27 de octubre de 2026. Reevaluación exploratoria solicitada expresamente después de las cinco auditorías. Código nuevo sobre originales, con plan y fuentes congelados antes del entrenamiento. F3c de producción, las referencias, el PDF, el guion y la selección se conservan. La revisión es propia de IA y no equivale a validación profesional independiente.

Se corrigió la separación computacional de la cadena del contraste primario T2b: desde la construcción del objetivo y las curvas hasta los árboles fuente, los factores y el nivel. Los controles adversos nuevos pasan, incluida una repetición real de los ajustes fuente con costes de 2024 alterados. Esto cambia la conclusión técnica sobre esta implementación nueva; la cadena histórica conserva sus fallos documentados. La disponibilidad histórica de la información y la adaptación previa de 2024 siguen sin resolverse.

La ganancia global del bloque propio reaprendido es +0,0023317 de D², con banda condicional de familia 6 [+0,0005769; +0,0042488]. El límite exigido sigue siendo 0,0005. El resultado del control es favorable dentro de ese alcance. Ningún resultado de este expediente autoriza una promoción formal o acredita un score privado.

## Qué se corrigió

Se reconstruyen T0, exposición y atributos desde los Parquet originales, conservando reglas puntuales de limpieza e identificación y su procedencia. La asignación sigue ramo, póliza y ocurrencia dentro del periodo. Los importes permanecen valorados al 31 de diciembre de 2024: no son snapshots recuperados de 2023.

Las curvas maduras de coste y las participaciones por peligro se vuelven a calcular únicamente con las filas permitidas en cada ámbito. Para seleccionar rondas del árbol fuente, se excluye la componente interna retenida antes de aprender curvas, participaciones y categorías. Después se recalculan los objetos del train completo y se reajusta con las rondas elegidas. El árbol fuente usa desarrollado de 2021–2023; ninguna etiqueta de 2024 de ambos mercados entra en esos argumentos.

Los folds agrupan clientes conectados por dirección entre ramos, dentro de cada mercado. La evaluación temporal permite renovaciones presentes en 2023; eso es diferente de afirmar independencia de entidades entre años. Los diccionarios categóricos se aprenden solo del entrenamiento fuente, con categorías no vistas como ausentes. No se unen con el destino ni con el test.

Las bases emergentes de entrenamiento de 2023 usan niveles OOF de cinco folds, con completitud y participaciones aprendidas fuera del fold evaluado. F2 y los factores propios se aprenden sobre esas bases OOF de 2023. Los niveles finales se estiman solo con 2023. La normalización de factores y forma se aprende en entrenamiento y queda fija para aplicar precios fila a fila; no se recalcula a partir de la cartera retenida.

La receta mantiene el esquema T2b y sus hiperparámetros históricos, K=300 y la secuencia de factores. Conserva como decisión fija heredada la forma 0,9 de autos renovación. El contraste principal retira los exponentes y el nivel del tablero, además de la forma auxiliar A_M1 procedente del diagnóstico histórico. No se buscaron K, subconjuntos, semillas o variantes después de evaluar. Son decisiones de receta heredadas o fijadas ahora: esta corrección no borra la selección histórica que condujo a ellas.

La versión sin factores propios conserva F2, con NCB y siniestros previos, y la forma común. La diferencia evaluada corresponde al bloque adicional de género en autos/contenidos y teletrabajo/marketing en contenidos, con sus niveles aprendidos en 2023. «Sin factores» en las tablas se refiere a ese bloque propio.

## Resultado nuevo

| Segmento | Filas | D² sin factores | D² F3c reaprendido | Diferencia |
| --- | ---: | ---: | ---: | ---: |
| Global | 59.202 | 0,1233249 | 0,1256566 | +0,0023317 |
| Negocio nuevo | 9.063 | 0,1021513 | 0,1022661 | +0,0001148 |
| Renovación | 50.139 | 0,1215906 | 0,1242526 | +0,0026620 |
| Autos | 25.603 | 0,0766757 | 0,0798340 | +0,0031582 |
| Edificios | 14.867 | 0,0782224 | 0,0782224 | +0,0000000 |
| Contenidos | 18.732 | 0,0903980 | 0,0948270 | +0,0044290 |
| Autos nuevo | 3.915 | 0,0517409 | 0,0505168 | -0,0012241 |
| Edificios nuevo | 2.279 | 0,0460048 | 0,0460048 | +0,0000000 |
| Contenidos nuevo | 2.869 | 0,1252251 | 0,1284051 | +0,0031800 |
| Composición 2025 | 59.202 | 0,0626430 | 0,0636017 | +0,0009587 |

Todos los D² usan el mismo T0 observado y el mismo vínculo de completitud dentro de cada contraste. Los segmentos usan su propio nulo; no se promedian para obtener el global. La constante por ramo y negocio, aprendida en 2023, obtiene D² global 0.0702403.

En negocio nuevo, el IC95 condicional es [-0,0037029; +0,0039767]. Con composición de 2025, el cambio global es +0,0009587, IC95 [-0,0029745; +0,0047722]. Esa reponderación usa conteos por ramo, negocio y bandas de exposición; no identifica por sí sola el rendimiento futuro.

Mantengo 10.000 remuestreos pareados de componentes cliente–dirección, semilla 2026102301 y familia nominal de seis pares. Se recalcula el nulo en cada cartera. Son intervalos condicionales a precios y modelos ya aprendidos; no repiten el entrenamiento de toda la cadena ni corrigen la búsqueda histórica. La repetición adversa de entrenamiento comprueba aislamiento, no añade años independientes para la inferencia estadística.

| Control conservado | Resultado |
| --- | --- |
| Límite inferior familiar > 0,0005 | Pasa el control puntual/condicional |
| Cinco segmentos amplios ≥ −0,001 | Pasa el control puntual/condicional |
| Protección de negocio nuevo | No pasa |
| Autos nuevo ≥ −0,001 | No pasa |
| Ganancia después de retirar grupos favorables | No pasa |

El diagnóstico de influencia utiliza 36,408 componentes de las filas de 2024. Al retirar los 37 más favorables, la diferencia es -0,0000129. La retirada retrospectiva de 37 grupos alcanza la anulación de la ganancia según ese cálculo. Es un diagnóstico de concentración, sin probabilidad asociada. La agrupación se construye en el ámbito nuevo; no se sustituye silenciosamente la unidad histórica de la revisión anterior.

## Qué conclusiones cambian

La auditoría anterior demostró que los costes retenidos cambiaban completitud y nivel del entrenamiento. En la implementación nueva, los argumentos completos de los ajustes fuente, los modelos, sus predicciones y los parámetros/precios finales permanecen exactamente iguales al perturbar los costes de 2024. También se comprueba la separación de direcciones entre folds y que la aplicación de factores es invariante al orden de las filas. La corrección computacional del contraste primario queda verificada con esos límites explícitos.

El +0,0023923 histórico frente a la referencia sin factores se conserva como resultado de la receta antigua. El número nuevo es +0,0023317. No se interpreta su diferencia como efecto causal exclusivo de corregir la completitud: también cambian las particiones, las categorías, los normalizadores y la retirada de calibraciones públicas que estaban dentro de la comparación anterior. La vista antigua sin exponentes públicos tampoco es idéntica a esta receta nueva. No se suman ambos resultados ni se presentan como confirmaciones independientes.

| Conclusión del contraste | Auditoría anterior | Cadena nueva |
| --- | --- | --- |
| Separación computacional desde preparación | Fallaba | Pasa en el contraste primario corregido |
| Ganancia global | +0,0023923 | +0,0023317 |
| Protección de negocio nuevo | No acreditada | Sigue sin pasar |
| Diferencia de autos nuevo | −0,0010036 | -0,0012241 |
| Diferencia tras retirar 37 grupos favorables | +0,0000043; pasaba por poco el veto nominal | -0,0000129; falla el veto |
| Ganancia con composición de 2025 | +0,0012080; intervalo cruzaba cero | +0,0009587; intervalo sigue cruzando cero |

La concentración es una conclusión que empeora: el nuevo contraste falla el veto de influencia que el anterior apenas superaba. La renovación aporta aproximadamente 99.39% de la mejora neta de desviación del contraste nuevo. Esa proporción usa contribuciones de desviación sobre el mismo total; no suma D² con nulos distintos. Las recetas y las agrupaciones de ambas columnas tienen los límites de comparabilidad descritos.

El control de mejora global pasa ahora el umbral condicional registrado. La protección de negocio nuevo sigue sin pasar. El control puntual de autos nuevo no pasa. Estos resultados actualizan el dictamen de este contraste, con todas las cifras adversas conservadas. La estabilidad entre años de cada factor necesita su propio contraste; un piso puntual no la acredita.

## Pendientes que siguen abiertos

El año 2024 ya fue consultado y usado para decidir. El plan nuevo es anterior a esta corrida, pero la evaluación continúa siendo adaptativa. No hay un año futuro independiente ni un score privado observado. La puerta formal v1 y sus actas históricas no se reabren, ni se marca resuelta una advertencia de disponibilidad por pasar una prueba de aislamiento computacional.

Esta ejecución protege la cadena del contraste primario T2b, que era la base de la afirmación global sobre los factores. No reentrena la rama A1 ni la mezcla en sus propios ámbitos, ni convierte el CSV F3c de producción, aprendido con 2023 y 2024, en una predicción OOF. Repetir esas sensibilidades bajo el diseño corregido sigue pendiente antes de extender a ellas el dictamen técnico.

Permanecen sin acreditar los maestros fechados y el acceso real al cotizar, la duración inicialmente contratada, el vintage climático y la operación de la contingencia sin factores. La historia del nuevo contraste conserva su corte anterior al inicio de cobertura; no se afirma que fuera conocida en la cotización. La valoración única de 2024 tampoco permite reconstruir reservas, estados o costes de 2023 tal como se conocían entonces.

La suficiencia de reservas, la cola no reportada y el transporte de las curvas siguen necesitando valoraciones posteriores y evidencia nueva. Los escenarios y las salvaguardas completos deben repetirse sobre la receta nueva antes de cualquier promoción; los resultados históricos de otra cadena no se transfieren como aprobaciones. El soporte escaso de negocio nuevo de hogar no aumenta con esta corrección. La revisión profesional por otra persona también permanece pendiente.

## Evidencia y reproducción

El código está en `herramientas/validar_cadena_f3c.py` y `herramientas/cerrar_validacion_cadena_f3c.py`, relativos al repositorio. Plan, manifiesto SHA, apertura exploratoria, entorno, intentos de ajuste, modelos, parámetros, precios históricos, bootstrap, resultados y verificación están en `privado/validacion_cadena_f3c/20261027T153123Z/`. No se publican identificadores o precios por fila. Se completaron doce ajustes fuente, seis originales y seis de repetición adversa, más dos ajustes sintéticos de comprobación. Los controles estadísticos se cotejaron con scikit-learn; las primeras veinte réplicas del bootstrap coinciden con error máximo 1.67e-15.

F3c de producción conserva su SHA exacto. No se hicieron inferencias nuevas de 2025, envíos, entrenamiento remoto, cambios de marca, modificaciones del PDF o del guion. Las referencias y los fallos históricos se conservan.
