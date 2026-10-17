# Objetivo actuarial y validación para la tarificación multirramo

Propuesta metodológica del proyecto, 16 de octubre de 2026. Versión 1.4, con REN00 como marca de auditoría sobre la capa DUP01/CAP01/CAT01/AGE01. Su finalidad es fijar un contrato común para construir el objetivo, preparar predictores y comparar modelos de autos, edificios y contenidos. Las decisiones parten del enunciado oficial, la auditoría de las once tablas y la limpieza trazable de claves y exposición.

Para empezar, proponemos modelos por ramo sobre el incurrido neto observado, con una validación temporal común y una segunda línea de experimentos sobre completitud de reporte y reservas. El coste último sigue siendo el objetivo económico; el incurrido es la referencia observable para las primeras pruebas. Mantener esa distinción permite iniciar comparaciones sin presentar estimaciones de desarrollo como hechos conocidos.

## Decisiones de la primera versión

| Aspecto | Propuesta operativa |
| --- | --- |
| Unidad | Un periodo o subperiodo de póliza, identificado por `row_id` |
| Salida | Esperanza del coste último en CU del periodo, neto de franquicias y recuperaciones, excluyendo siniestros repudiated; conservar las pólizas con declined_by_insurer |
| Primera etiqueta de trabajo | Suma de `incurred_to_date - recoveries` de siniestros aceptados y asignados de manera única al periodo, valorada a 31 de diciembre de 2024 |
| Exposición | Derivados verificados de D32: días inclusivos / 365, redondeados a cuatro decimales; conservar la convención como supuesto del proyecto |
| Primeros modelos | GLM Tweedie y árboles potenciados por ramo, con potencia 1,5 como referencia de ajuste |
| Comparación actuarial | Frecuencia de siniestros con coste positivo por severidad positiva, además del modelo directo de coste |
| Validación | Desarrollo sobre 2023, con ajuste interno previo; evaluación final de la primera ronda sobre 2024 después de congelar candidatos |
| Generalización | Medir por separado entidades conocidas y nuevas; las renovaciones entre pasado y futuro se conservan |
| Variables | Primera versión basada en información contractual y características razonablemente disponibles; bloques temporales dudosos se evalúan aparte |
| Selección | Tweedie D² global en las mismas filas, acompañado por resultados de cada ramo, calibración, estabilidad y sensibilidad al objetivo |

El [protocolo estructurado](protocolo_metodologico.json) identifica estas decisiones y su estado. El catálogo de modelos es un conjunto de candidatos; sus parámetros y arquitectura no sustituyen este contrato.

## Qué queremos predecir

Para el periodo `i`, sea `U_i` el coste final de todos los siniestros ocurridos entre `period_start` y `period_end`, que correspondan a la póliza y ramo de esa fila. La predicción buscada es:

```text
m_i = E[U_i | información de riesgo y cobertura disponible para el periodo i]
U_i = suma de costes últimos aceptados, netos de franquicia y recuperaciones
```

Es una prima de riesgo para el periodo entregado. No incluye gastos, margen comercial ni una carga de beneficio. `written_premium` describe el tarifario comercial existente y no se convierte en etiqueta. La plantilla de entrega tampoco proporciona valores verdaderos para entrenar.

La duración forma parte de la tarea: no entregaremos una tasa anual sin convertirla al periodo. Si `q_i` es una tasa anual y `e_i` su exposición, `m_i = e_i*q_i`. Si el modelo usa importes con `log(e_i)` como offset, la predicción ya contiene esa exposición y no se multiplica una segunda vez.

Se condiciona la predicción al periodo que aporta el concurso, incluida su duración final. En una aplicación real de cotización, una cancelación futura podría ser desconocida. La validación de este reto no demuestra por sí sola que un modelo pueda tarificar en emisión sin conocer esa duración.

## Base de datos y preparación

Leer las tablas desde el catálogo de la corrida de limpieza indicada en [current_dataset.json](../Limpieza/current_dataset.json), después de comprobar su estado y hashes. Las seis tablas de pólizas/test y claims son derivadas; clientes, direcciones, clima y plantilla siguen referenciando los originales. DUP01 excluye únicamente las 604 copias autorizadas y conserva 162.546 registros de siniestro, sin cambiar ningún valor retenido. El ID de ocho dígitos queda como representante y la bitácora conserva filas excluidas y alias de los IDs de nueve. La cohorte no se expande y no se depura por longitud sola. Consultar [la aplicación DUP01](../Limpieza/current_duplicate_application.json). Las bitácoras de reparación, indicadores diagnósticos y archivos de revisión no son predictores.

El participante autorizó CAP01: dividir por mil exactamente las 2.073 filas con respaldo anterior de D34, en una versión derivada nueva. La primera especificación leerá esa capa verificada; los 1.454 capitales extremos restantes conservan sus valores y siguen pendientes. CAP01 no es una regla general que se vuelva a ejecutar al leer datos. Se conservan D32 sin corrección de capitales, la lista aprobada, bitácoras, reversión y hashes para una comparación identificada. No corregir por siniestralidad o score ni extender automáticamente la cohorte. La unidad sigue siendo una inferencia del proyecto, no confirmación del generador.

La revisión D34 identificó 3.527 filas de banda extrema y 2.073 con apoyo en una referencia anterior comparable; estas últimas ya se corrigieron en CAP01 por autorización del participante. El informe D34 conserva el diagnóstico anterior, sin reescribirse. La evidencia posterior puede servir para revisión retrospectiva, pero no entra automáticamente en un corte histórico anterior. Si se ensaya una reparación, recalcular sus apoyos con la fecha de información de cada partición y separar el uso de características de test como decisión transductiva. [Revisión detallada de capitales](../Revision_capitales/README.md).

Antes de unir variables, exigir unicidad del maestro y cardinalidad esperada. La clave `customer_id` normalizada recupera los cruces de autos; las asociaciones antiguas hechas antes de esa reparación no deben usarse como prueba de un segmento demográfico nuevo. Conservar `policy_id`, `customer_id` y `address_id` para relaciones y controles; su uso directo como categorías predictivas no entra en la primera especificación.

## Construcción del coste observado

Para cada siniestro aceptado `j`, definir:

```text
P_j = paid_to_date
C_j = incurred_to_date
R_j = recoveries
O_j = C_j - P_j
Y_j_observado = C_j - R_j
Y_i_observado = suma de Y_j_observado de los siniestros asignados al periodo i
```

El diccionario indica que los pagos ya son netos de franquicia; no volver a restar `voluntary_excess` o `compulsory_excess`. La recuperación se descuenta una sola vez. Los rechazados se excluyen del coste y del conteo de siniestros aceptados; pueden conservarse como categoría de auditoría. Las filas sin siniestros aceptados reciben coste observado cero.

Asignar con la condición conjunta `policy_id`, `line` e inclusión de `loss_date` en el intervalo de cobertura. `report_date` determina cuándo se conoció la notificación; no decide a qué periodo corresponde el coste. Un siniestro ocurrido en diciembre y reportado después sigue perteneciendo al periodo de ocurrencia.

Cada siniestro tendrá una categoría de asignación: única, fuera de ventana, sin correspondencia o ambigua. Una multiplicidad positiva exige resolver el cruce antes de sumar. La auditoría anterior a DUP01 encontró 414 registros anteriores al primer periodo observado; después de excluir una copia autorizada quedan 413. Se conservan fuera del objetivo de los periodos actuales y dentro de la reconciliación. No se cambia su fecha ni se imputan a la primera renovación disponible.

Antes de materializar la etiqueta, comprobar importes finitos, costes netos no negativos, relación entre incurrido y pagado y estados conocidos. Si aparece una anomalía, conservarla en una cola con su efecto monetario y decidir una regla explícita. No aplicar `max(0, importe)` de forma silenciosa. El diagnóstico de soporte y el registro de construcción deberán mostrar cuántos casos afectan a cada decisión.

El archivo de entrenamiento tendrá, como mínimo, `row_id`, ramo, año de ocurrencia del periodo, exposición, coste observado, número aceptado, número con coste positivo, número abierto e importes de pago, recuperación y reserva. Las columnas de coste, estado y conteos del propio periodo son etiquetas o diagnósticos, no predictores de ese mismo periodo.

En frecuencia–severidad, contar `N_i+`, los siniestros aceptados con coste neto positivo, y modelar su coste medio positivo `S_i+`. La predicción será `e_i * lambda_i+ * s_i+`, bajo una especificación de frecuencia y severidad condicional compatible. Puede ajustarse Gamma por siniestro positivo, o al coste medio por periodo con peso `N_i+`; Poisson modela el conteo, con extensión binomial negativa si la sobredispersión y la validación lo justifican. Si se usa el conteo de todos los aceptados y se excluyen ceros de Gamma, falta un componente para la probabilidad de coste positivo: no son modelos equivalentes. El diagnóstico actual encontró un aceptado con coste neto cero y ninguno con coste neto negativo; se conserva el caso cero y se distingue de un rechazo.

## Desarrollo pendiente y estimación del último

### Referencia inicial y escenarios de reservas

La primera etiqueta, denominada `T0`, será el incurrido neto observado. Incluye la estimación de caso de los abiertos; no equivale a usar únicamente pagado. Entrenar solo con cerrados descartaría selectivamente expedientes lentos o severos. Por ello, los abiertos permanecen en T0, con un diagnóstico separado de su peso.

La valoración única de diciembre de 2024 no contiene trayectorias de pago, reservas históricas ni fecha de cierre. No permite estimar factores de desarrollo financiero mediante un triángulo de pagos reconstruido ni aprender qué reserva tenía un cerrado años antes. Las cohortes antiguas son más maduras en promedio, pero su grado de cierre no convierte sus importes en una verdad última completa.

Proponemos un escenario de sensibilidad de reservas `T1(a)`:

```text
Y_j_T1 = P_j + a_(ramo,peligro)*O_j - R_j     si el siniestro sigue abierto
Y_j_T1 = C_j - R_j                           si está cerrado
```

El caso central `a=1` reproduce T0. Para estudiar materialidad se fijan inicialmente `a=0,75` y `a=1,25` sobre la reserva pendiente, primero por separado en lesiones corporales de autos y hundimiento de edificios, y después sobre los demás abiertos. Son perturbaciones de diseño, no factores estimados ni intervalos de confianza. No se elegirán sus valores para hacer coincidir las etiquetas con el modelo ni para presentar una mejora de score contra su propia etiqueta artificial.

Las recuperaciones observadas tampoco son necesariamente últimas. En autos se estudiará por separado su concentración por peligro y estado. Un ajuste de recuperaciones futuras necesita una hipótesis propia y evidencia de cohortes maduras comparables; no se confundirá la ausencia de recuperación en abiertos con recuperación final nula. T0 mantiene lo observado y T1 anterior aísla solo la sensibilidad de la reserva.

### Siniestros no reportados

Para el retraso `D = report_date - loss_date`, se observan únicamente siniestros reportados antes del corte. En cohortes recientes faltan precisamente retrasos largos. La distribución empírica de todos los reportados no estima sin sesgo esa cola.

La propuesta `T2` estudiará un modelo de retraso condicionado por ramo y peligro, con agrupación parcial cuando haya poca muestra. La contribución de un retraso observado `d_j` a una verosimilitud truncada contiene `f(d_j)/F(T-loss_date_j)`. Su especificación, estabilidad entre cohortes y cola necesitan verificarse antes de usarla para corregir etiquetas. Los siniestros de 2020 recibidos fuera de nuestra ventana contractual no son una muestra completa de ese año y no se usarán como cohorte madura representativa.

Primero evaluar la predicción del número de notificaciones que llegan después de un corte artificial pero antes de diciembre de 2024, usando solo fechas ya reportadas al estimar cada corte. Ese experimento verifica parte del retraso observable; no mide por completo notificaciones posteriores al archivo ni el desarrollo monetario.

Para frecuencia, una ruta es ajustar la exposición observada por completitud de reporte:

```text
e_i_efectiva = integral sobre el periodo de F(T-t | ramo, peligro, información admisible) dt / 365
```

Con tasas de ocurrencia suficientemente estables dentro del periodo, se modela el conteo reportado usando esa exposición efectiva y se predice el conteo último de 2025 con exposición nominal. Estacionalidad o cambio de riesgo intraperiodo requieren ampliar el modelo, no ocultarlos dentro de un offset fijo. Si `e_efectiva` es prácticamente nula, no usar un inverso enorme sin un tratamiento documentado.

Para coste directo, una corrección por probabilidades de reporte requiere una hipótesis sobre la relación entre retraso y severidad. Una completitud de conteos no es automáticamente una completitud de importes. Se comparará una corrección por peligro con escenarios de dependencia de severidad, conservando la incertidumbre y el riesgo de factores extremos. No corregir a la vez exposición y coste por el mismo efecto de reporte.

T2 y su combinación con T1 se aplicarán después de una referencia T0 reproducible. Cada versión conservará el coste antes/después y su contribución a la selección. La literatura conjunta de tarificación y reservas trata explícitamente la incertidumbre de las estimaciones de último; no respalda tratarlas como observaciones exactas. [Crevecoeur y otros](https://arxiv.org/abs/2203.07145), [Parodi](https://www.cambridge.org/core/journals/british-actuarial-journal/article/abs/trianglefree-reserving/6897BBE13CC8692BF75DAD3A97B91416).

### Inflación y año

La variación anual de incurrido mezcla inflación, composición, cobertura y desarrollo pendiente. No ajustar una recta sobre el coste medio de 2021–2024 y llamar inflación a su pendiente. La primera comparación usará el año como control cuya extrapolación se declare, y contrastará estabilidad de relatividades en cohortes más maduras.

Una tendencia monetaria a 2025 será un experimento separado: estimar con entrenamiento, fijar qué parte del nivel es tendencia y mantener sin modificar la evaluación. Comparar sin tendencia adicional frente a esa versión. Un árbol que recibe el número 2025 no extrapola por sí solo una tendencia económica. No añadir un factor de inflación encima de un modelo que ya reproduce ese mismo cambio sin verificar la doble corrección.

## Tratamiento por ramo y producto

### Autos particulares

Los productos disponibles son `comprehensive`, `third_party_fire_theft` y `third_party_only`. El tipo de cobertura debe entrar en la especificación junto con franquicia, edad y experiencia del conductor, antigüedad y grupo de valor del vehículo, uso, kilometraje declarado y estacionamiento. Las interacciones cobertura–vehículo y cobertura–franquicia son candidatas; no se estima un tarifario totalmente independiente por producto antes de comprobar soporte y número de siniestros.

Empezar con un modelo directo Tweedie del coste por ramo. La alternativa actuarial descompone frecuencia y severidad, con una extensión que separa lesiones corporales del resto. El archivo distingue `own_damage`, `third_party_prop`, `bodily_injury`, `theft` y `glass_hail`; cada componente puede generar una etiqueta de coste para todas las pólizas y luego sumar predicciones. No usar el peligro de un siniestro futuro como entrada conocida.

La separación de lesiones responde a evidencia del archivo: hay abiertos de 2021 y 2022 y retrasos de reporte más largos que en daños propios o cristales. Su maduración se estudia antes de interpretar la caída de frecuencia observada de 2024. Daños propios y robo requieren además revisar recuperaciones. Una aparente incompatibilidad entre cobertura y peligro se audita con el diccionario y el contrato; no se eliminan costes imponiendo una interpretación propia de las coberturas.

`telematics_score` y adhesión a telemática se estudiarán como bloque adicional, con indicador de ausencia y de adhesión. No existen trayectos ni histogramas de conducción. Un score presente en la fila puede haberse generado durante la cobertura; hasta justificar su disponibilidad previa no forma parte del modelo contractual principal. NCB y años de licencia se contrastan como variables observadas, sin corregir automáticamente uno para que coincida con el otro.

### Edificios del hogar

El riesgo corresponde a la estructura, con `sum_insured`, construcción, tipo y antigüedad del inmueble, ocupación, desocupación, protecciones y franquicia. El límite de suma asegurada modifica cobertura y severidad; no equivale al coste esperado. Se probarán curvas suaves de `log(sum_insured)` y efectos de franquicia, sin declarar monotonicidad o concavidad demostradas en esta cartera.

Empezar con Tweedie por ramo. La comparación de frecuencia-severidad puede ganar utilidad para explicar una frecuencia baja con costes altos. Separar inicialmente hundimiento del resto en una extensión diagnóstica: sus retrasos y expedientes abiertos antiguos justifican un tratamiento de maduración propio. Incendio e inundación se revisan por severidad y abiertos, pero una cartera pequeña de eventos no justifica una red o un modelo de cola independiente sin comprobar estabilidad.

La tabla de direcciones aporta región, zona de inundación, elevación, distancia al río y características físicas. No hay coordenadas que permitan presuponer un modelo espacial geográfico detallado. Clima histórico y factores territoriales son candidatos; se evalúan con la ventana temporal permitida. Para tormenta/inundación, medir concentración por región y periodo y revisar la sensibilidad a shocks comunes; no asumir que cada fila aporta información independiente.

`accidental_damage_cover` permite estudiar diferencias de cobertura. Un indicador de cobertura opcional no convierte automáticamente cualquier siniestro con nombre similar en inválido; el mapeo contractual debe verificarse. Los capitales señalados para revisión se conservan en la evaluación y se diagnostican por separado.

### Contenidos del hogar

El objeto asegurado es el contenido, con capital, tenencia, seguridad, bienes de alto valor, cobertura accidental, bicicleta, trabajo desde casa y presencia de huéspedes. Empezar con Tweedie y contrastar frecuencia-severidad. La seguridad y las características del hogar pueden actuar de forma distinta sobre probabilidad de siniestro y cuantía, lo que permite una comparación interpretable entre ambas rutas.

El archivo distingue robo, escape de agua, daño accidental e inundación. Los primeros tres suelen mostrar reportes observados más cortos que lesiones de autos o hundimiento de edificios, pero la muestra reciente sigue truncada y contiene abiertos. No fijar IBNR a cero ni asumir liquidación inmediata por la etiqueta del ramo.

La información de edificios sobre la misma dirección puede ayudar, por ejemplo mediante características del inmueble ya conocidas. Los importes de siniestros de otro ramo solo podrán incorporarse como historia disponible antes de la predicción. Una predicción de edificios usada en contenidos debe generarse dentro del esquema de entrenamiento, sin acceso a etiquetas retenidas. La señal multirramo se comparará con una base sin ella antes de incorporarla.

## Predictores y fecha de información

Se establece un corte de información anterior al inicio del periodo para construir historia predictiva. En la aplicación a 2025, el archivo tiene valoración a 31 de diciembre de 2024: para filas que empiezan después de enero de 2025 se usa como máximo ese corte disponible, sin inventar actualizaciones durante 2025.

| Bloque | Contenido y uso inicial |
| --- | --- |
| F0 contractual | Coberturas, franquicias, exposición, características del riesgo en la fila y variables físicas de direcciones bajo el supuesto explícito de estabilidad de esos maestros |
| F1 historia de notificaciones | Conteos y recencia con `loss_date` y `report_date` anteriores al corte; no usar el estado final de 2024 para reconstruir si un expediente estaba aceptado o abierto años antes |
| F2 clima histórico | Agregados de años anteriores al corte; para 2023 no incorporar el clima de 2023 o 2024. Sin historia suficiente, usar una regla de ausencia ajustada dentro del entrenamiento |
| F3 información condicionada | Telemática, contactos de servicio, pagos incumplidos y atributos cambiantes del maestro sin fecha de referencia: prueba separada tras documentar disponibilidad |
| F4 tarifario existente | `written_premium`, descuentos y señales comerciales: comparación aparte para medir dependencia del tarifario previo, evitando confundir prima comercial con objetivo |
| Fuera de la primera matriz | `renewal_decision`, importes o estado del siniestro del propio periodo, diagnósticos de reparaciones, nombres personales e IDs crudos como categorías de memorización |

Los siniestros con fecha pasada pero todavía no reportados al corte no entran en historia. Para 2023 y 2024 no se conocen los pagos o reservas a esos cortes a partir de su valor final de 2024: esos importes no se usarán en la primera historia predictiva. Los conteos de notificaciones se construirán sin filtrar por un estado final que aún no era observable. Su validez presupone que el archivo conserva las notificaciones existentes y sus fechas.

La edad del tomador de hogar se toma de la capa AGE01: años naturales cumplidos desde customers.date_of_birth hasta period_start, adoptando el maestro de nacimiento como referencia explícita del proyecto. La edad informada antes del recálculo permanece en bitácora. En autos se conserva driver_age porque el conductor principal puede diferir del tomador. Las variantes de mayúscula/minúscula de construcción se normalizan mediante CAT01; t/w siguen separados y sin material confirmado, con ruptura de codificación observada en 2023. Una variable del maestro que cambia en el tiempo necesita fecha o supuesto. Año de construcción y geografía física pueden ser razonablemente persistentes, pero ocupación, estado civil, años en domicilio o banda de crédito no se retrotraen automáticamente. No atribuir al contrato completo una disponibilidad temporal que el archivo no acredita.

## Diseño de validación

### Cortes y uso de etiquetas

La primera ronda seguirá este calendario, idéntico para todas las familias:

| Identificador | Entrenamiento de la base | Evaluación o uso de datos posteriores |
| --- | --- | --- |
| V22 | 2021 | 2022 para ajuste interno inicial y diagnóstico |
| V23 | 2021–2022 | 2023 para comparación de desarrollo, con ajuste de transformaciones y modelo solo en el entrenamiento |
| V24 | 2021–2023 | 2024 como evaluación externa de la primera ronda, tras congelar candidatos, variantes del objetivo y política de calibración |
| Producción | 2021–2024 | Predicción de 2025 después de la revisión de V24; sin etiquetas ocultas |

Las etiquetas de todos estos cortes están valoradas al cierre de 2024. V22/V23/V24 serán pruebas temporales sobre la referencia observable, no reconstrucciones exactas del estado de información de una aseguradora en cada año. Los predictores sí respetarán el corte hasta donde pueda acreditarse. Esta distinción evita confundir madurez posterior de la etiqueta con información admisible para entrenar en un backtest histórico estricto.

Una vez consultado V24 para modificar el modelo, deja de ser una evaluación intacta. Registrar cada apertura y el cambio que motivó. Los sucesivos resultados seguirán siendo útiles, con condición de evaluación reutilizada; no se presentarán como una nueva prueba independiente. La puntuación pública de Kaggle será contraste adicional de 2025, conforme a la política D29.

### Calibración y selección interna

Comparar siempre una salida sin calibrar. Para evaluar calibración durante el desarrollo, dividir las predicciones V23 por un hash estable de cliente en dos mitades: una para ajustar factores o isotónica y otra para seleccionar la variante. Regla inicial: SHA-256 del texto UTF-8 `cal_v1|customer_id`, primeros 16 caracteres hexadecimales convertidos a entero; resto módulo 2 igual a cero para calibración y uno para selección. Conservar todas las filas de un cliente en la misma mitad y registrar la regla antes de ver sus resultados. La dependencia por dirección compartida se medirá y, si es material, se usará agrupación conjunta compatible con el tamaño de los grupos y una nueva versión de particiones.

Después de seleccionar la forma de calibración, se puede reajustar en todo V23 y evaluar V24 con la base entrenada hasta 2023. Ese cambio de base exige comprobar la transferencia del calibrador; no se da por estable. Un calibrador ajustado en V23 no se evalúa como prueba independiente sobre esas mismas etiquetas. En producción, el reajuste y uso de predicciones fuera de muestra deberá quedar definido antes del entrenamiento final.

Cada transformación aprendida, codificación por objetivo, prior de credibilidad o selección de variables se ajustará dentro de su partición. Para mezclas y stacking se necesitan predicciones de bases que no hayan visto las etiquetas de las filas usadas para entrenar el combinador y una evaluación externa conservada. No usar resultados in-sample de una base completa como si fueran predicciones fuera de muestra.

### Entidades conocidas y nuevas

La renovación de un cliente o póliza entre pasado y futuro es parte del problema y no se elimina de la comparación temporal. Para V23, V24 y 2025, medir proporciones de filas con póliza, cliente y dirección observados previamente y reportar errores por esos grupos. La auditoría debe usar claves limpiadas y distinguir coincidencia por ramo de coincidencia en toda la cartera.

El diagnóstico actual encuentra una mezcla semejante en los cortes históricos y en 2025. La proporción de filas de 2025 con cliente ya observado en el mismo ramo es 84,75% en autos, 84,85% en edificios y 84,84% en contenidos. Para dirección conocida es 84,08%, 81,51% y 81,69%, respectivamente. Son proporciones de filas, no de clientes únicos. Respaldan una validación temporal con renovaciones y un diagnóstico secundario de nuevas entidades. [Evidencia y archivos identificados](diagnosticos/objetivo_20261016T181306Z/evidencia.json).

Una partición por clientes/direcciones no vistos será una prueba secundaria. Si se agrupan componentes conectadas, medir antes el tamaño de las componentes y la cobertura de cada ramo. No imponer cinco particiones cuando una componente dominante haga inviable una separación útil. Esa evaluación responde a generalización a riesgos nuevos, no sustituye la predicción del año siguiente con renovaciones.

## Métrica, calibración y diagnósticos

Puntuar el vector concatenado de costes de periodo con `d2_tweedie_score(..., power=1.5)`, inicialmente sin pesos adicionales, y declarar que la ponderación completa del scorer oficial no está publicada. El D² de los ramos no se promedia para obtener el global. Mantener también desviación media y suma de desviaciones para comparar errores y contribuciones.

La desviación cumple `d_p(e*r,e*q)=e**(2-p)*d_p(r,q)`. Con potencia 1,5, el entrenamiento sobre tasas ponderadas por `sqrt(e)` alinea su suma de pérdidas con los importes sin pesos. Usar peso `e` es otra formulación actuarial que merece una sensibilidad. Los valores D² de ambas escalas pueden diferir por la referencia constante y sus normalizadores. Es una derivación de la pérdida, no una confirmación del servidor del concurso. [Desviación Tweedie](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_tweedie_deviance.html), [D²](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.d2_tweedie_score.html).

Comparar dos referencias: tasa anual de cartera `sum(Y)/sum(e)` por ramo y tasa constante que minimiza la desviación de importes. Para potencia 1,5 esta última es `sum(Y/sqrt(e))/sum(sqrt(e))`. No confundirlas con la constante por fila usada en el denominador de D². La identidad matemática se comprobará al implementar la métrica.

La razón agregado predicho/observado mide balance; no demuestra precisión individual ni balance futuro. Para una calibración `c*m` de predicciones positivas, el factor que minimiza desviación Tweedie con potencia 1,5 y pesos unitarios es `sum(Y/sqrt(m))/sum(sqrt(m))`, diferente en general de `sum(Y)/sum(m)`. Estimar ambos en el bloque de calibración y comparar fuera de él. La isotónica solo avanza si mejora de forma estable sin concentrar escalones injustificados.

Mantener las predicciones finitas y positivas. Para la primera implementación se propone un piso numérico fijo de `1e-8 CU/año * exposición`, documentado como protección de dominio y no como prima mínima económica. Valores no finitos o exposición no positiva son errores de flujo, no casos que se resuelvan con ese piso. No se ajustará el piso con el leaderboard en la primera ronda.

Los diagnósticos incluirán, por ramo, producto y corte, coste total, desviación, frecuencia y severidad cuando correspondan, calibración por bandas y comportamiento de extremos. Los segmentos con pocas observaciones o siniestros se muestran con su soporte, sin convertirlos en conclusiones firmes. Un gráfico de doble lift compara desacuerdos de dos modelos con observaciones retenidas; no tiene curvas objetivo predeterminadas.

No comparar un D² sobre T0 con otro sobre T1 como si la diferencia midiera mejora del algoritmo. Para cada comparación, mantener fija la etiqueta de evaluación. Al estudiar desarrollo, producir una matriz de candidatos entrenados con T0/T1/T2 y evaluados contra cada referencia declarada; los ajustes aprendidos se estiman solo con el entrenamiento del corte. La estabilidad de selección entre escenarios aporta evidencia de robustez. Un modelo que se adapta mejor a una proxy inmadura no demuestra por ese hecho mejor predicción del último.

La incertidumbre se examinará con remuestreo por cliente, sensibilidad a dirección/región y escenarios de desarrollo, reconociendo dependencia por eventos comunes. Con pocos años y regiones, un intervalo estrecho bajo independencia por fila no representa toda la incertidumbre futura. Las bandas de sensibilidad de reservas no son intervalos probabilísticos.

La selección comparará diferencias de desviación sobre las mismas filas y grupos, no solo dos scores aislados. Ante resultados similares y sensibles al corte o al escenario, preferir el candidato más estable y fácil de revisar, o conservar la diversidad para una mezcla validada. La complejidad se justifica por su aportación observada, sin un umbral de mejora inventado antes de conocer la variabilidad.

## Comparaciones que priorizamos

| Comparación | Pregunta que resuelve |
| --- | --- |
| Referencia por ramo frente a GLM Tweedie | ¿Hay señal tarifaria estable más allá de nivel y duración? |
| GLM frente a GAM | ¿Las curvas suaves aportan sin perder estabilidad de relatividades? |
| GLM/GAM frente a LightGBM, CatBoost y XGBoost | ¿Las interacciones mejoran el resultado sobre la misma etiqueta y partición? |
| Coste directo frente a frecuencia–severidad | ¿La descomposición aporta precisión, explicación o control de maduración? |
| Total de ramo frente a componentes por peligro | ¿Separar lesiones o hundimiento mejora la estimación y sus supuestos? |
| Separado frente a conjunto multirramo | ¿Compartir información mejora sin ocultar deterioro de un producto? |
| Base contractual frente a bloques de historia, clima y tarifario | ¿Qué información explica la mejora y era admisible al predecir? |
| Sin calibración frente a balance, Tweedie e isotónica | ¿La corrección aprendida se sostiene en el siguiente año? |
| T0 frente a escenarios T1/T2 | ¿La selección depende de una hipótesis de reservas o de reporte no identificada? |

Los híbridos GLM con residuos de árboles o redes, credibilidad, CANN, modelos locales y Transformers son extensiones posteriores. Avanzarán cuando una comparación concreta justifique su aportación o diversidad y exista un protocolo reproducible. La especialización por ramo se basa en mecanismos y evidencia; no predetermina qué familia ganará.

## Entregables para comenzar los pilotos

1. Tabla de asignación de siniestros con categorías excluyentes y reconciliación de conteos e importes.
2. Tabla T0 por `row_id`, con sus componentes monetarios y diagnóstico de dominio. Las variantes del último tendrán nombre y configuración distintos.
3. Matriz F0 y contrato de disponibilidad de cada predictor. Los bloques adicionales conservarán su versión y fecha de información.
4. Particiones persistentes con `split_id`, `row_id`, rol, corte de predictores, fecha de valoración y versión del objetivo, además del hash de cliente para calibración.
5. Referencias por ramo y GLM Tweedie, con predicciones retenidas, puntuaciones en CU de periodo y registro de configuración, código y entorno.

La primera comparación local puede empezar una vez verificados estos entregables, sin esperar una estimación perfecta del último. Su conclusión quedará acotada a T0 y los cortes disponibles. La elección del candidato para 2025 deberá incorporar después sensibilidad a reporte, reservas, recuperaciones y tendencia. Conservar la política de hasta cinco envíos diarios como máximo provisional, sin obligación de agotarlos, y documentar qué hipótesis contrasta cada envío.

## Evidencia, responsabilidad y continuidad

La evidencia base está en la [auditoría actuarial](../Analisis/README.md), la [limpieza verificable](../Limpieza/README.md) y el [diagnóstico de soporte](diagnosticos/actual.json). Este último resume estados, retrasos observados, productos y solapamiento temporal de entidades sobre archivos identificados por hash; no entrena ni certifica etiquetas últimas.

El diagnóstico histórico D35, anterior a DUP01, encontró que en siniestros aceptados ocurridos en 2024 y reportados al corte seguían abiertos 940 de 1.178 expedientes de lesiones de autos (79,8%) y 200 de 291 de hundimiento de edificios (68,7%). En robo de contenidos son 253 de 1.976 (12,8%). Para la cohorte reportada de 2021, el percentil 95 observado del retraso es aproximadamente 544, 332 y 17 días en esos componentes, respectivamente. Estas cifras describen el archivo disponible, todavía truncado, y no son tiempos de liquidación ni factores de desarrollo. La diferencia justifica separar sus diagnósticos, sin inventar curvas últimas. Esas cifras conservan su procedencia histórica; el diagnóstico vigente recalcula los agregados desde claims DUP01, sin reutilizar proxies monetarias de D30.

El proyecto seguirá las prácticas IAA priorizadas de propósito y límites, documentación de datos/modelos, revisión de salidas y distinción entre validación propia e independiente. Documentar las decisiones humanas reales y el trabajo asistido por IA; no inventar aprobaciones. Las referencias educativas no son una certificación del flujo. [Matriz IAA del proyecto](../../../Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md).

Al llegar la Parte 2 se revisarán definición del objetivo, cobertura, unidades, mezcla, faltantes y disponibilidad temporal antes de transferir parámetros. Comparar reuso, recalibración y reentrenamiento permitido con evidencia nueva. El cambio de mercado es una prueba de adaptación, no una garantía de que una arquitectura extrapole correctamente.

Fuentes principales: [enunciado](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1), [contrato operativo archivado](../../REGLAS_2026.md), [ejemplo de prima pura y frecuencia–severidad de scikit-learn](https://scikit-learn.org/stable/auto_examples/linear_model/plot_tweedie_regression_insurance_claims.html) y las referencias específicas citadas en el texto. La propuesta es propia del proyecto; los resultados de literatura no se presentan como rendimiento de nuestras carteras.

La [investigación D37 de técnicas por ramo](Investigacion_tecnicas/INFORME.md) complementa la metodología con evidencia descriptiva anterior a DUP01 de la capa CAP01/CAT01/AGE01 y fuentes primarias. Propone contrastar coste directo frente a componentes por peligro, y proporcionalidad de exposición frente a una función adicional de duración. Añade TabM, ANAM, Credibility Transformer, TabPFN de severidad y zero-inflated Tweedie al catálogo, bajo sus condiciones. Estos ejes no cambian T0/T1/T2, las particiones ni el estado de preparación: faltan su implementación y los resultados retenidos.


La integración DUP01 conserva las corridas descriptivas anteriores. El lector activo recalcula asignación y agregados desde los siniestros del catálogo vigente; las proxies D30 no se mezclan con claims depurado. La tabla T0 operativa y las particiones continúan pendientes. Las bitácoras y alias son evidencia de preparación, nunca observaciones adicionales ni predictores.


## REN00 y exclusión operativa de decisiones y auditoría

D45: se añade audit_ren00 a las seis tablas derivadas. True identifica pertenencia a las 2.742 pólizas de la cohorte congelada D44 en cualquiera de sus 12.041 periodos; no afirma rechazo en cada fila. False significa fuera de esa lista. La pertenencia usa el resultado 2024 y la continuidad 2025, por lo que también es información futura respecto de los periodos históricos y está prohibida como predictor. Los roles de los dos extremos y el resto del historial quedan en la bitácora. Todas las celdas previas, los 162.546 siniestros DUP01 y las fechas permanecen iguales.

El selector real iaa_lab.data.feature_frames excluye renewal_decision y cualquier nombre que contenga ese texto, junto a audit_*. El guard permite rechazar solicitudes explícitas de columnas prohibidas y roles audit_only. Se validó sobre esquemas de las seis tablas y muestras reales con marcas positivas/negativas, perturbando decisiones y marcas sin alterar la matriz seleccionada. Esto impone la exclusión solicitada; no completa la matriz F0, sus cortes de disponibilidad, el objetivo T0 ni la adaptación del runner a Tweedie D². No hubo entrenamiento.

[Informe REN00](../Limpieza/runs/renaudit_20261016T203904Z_657dd741/informe.html). La semántica de declined_by_insurer y las fechas de CAL00 siguen pendientes. El rechazo de póliza no debe confundirse con el estado repudiated de un expediente.
