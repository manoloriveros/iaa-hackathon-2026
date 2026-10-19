# Documentación de los datos de la primera semana

Versión documental 1.0. Corte de datos D61, 2026-10-16 20: 31 America/Bogota. Rama retrospectiva CAP06R y protocolo metodológico 1.10. Las fechas UTC de las carpetas pueden ser del día siguiente al día local.

Los once Parquet originales se conservan. La preparación tiene dos ramas: la base mantiene 1.454 capitales pendientes; la rama retrospectiva incorpora 1.035 correcciones adicionales y conserva 419 pendientes. Las reglas aplicadas tienen listas de cambios y evidencia de verificación, pero ninguna rama está aprobada todavía como conjunto final para entrenar o entregar predicciones.

Este dossier permite seguir cada dato desde el archivo recibido hasta la versión que lo consume, comprender las decisiones actuariales y localizar lo que falta resolver. Los resultados de revisiones anteriores conservan su fecha y su catálogo; sus cifras no se presentan automáticamente como cifras de CAP06R.

## Estado de los datos al cierre


| Elemento | Estado al corte | Referencia |
| --- | --- | --- |
| Originales | 11 archivos Parquet intactos; 105 nombres de campo y 242 ocurrencias de columna. | [Mapa de rutas](../../../../../RUTAS_PROYECTO.json) |
| Periodos de póliza | 2.409.311 train y 626.639 test. | [Diccionario oficial archivado](../../../../../Preparaci%C3%B3n/artifacts/verification/iaa_launch_20261016/pages/data-description.md) |
| Siniestros | 163.150 originales; 162.546 después de DUP01; 413 marcados PRE00. | [PRE00](../../../Limpieza/runs/preaudit_20261016T211816Z_817285a5/informe.html) |
| Base preparada | ID01, EXP01, CAP01, CAT01, AGE01, DUP01, REN00 y PRE00; 1.454 capitales pendientes. | [Índice base](../../../Limpieza/current_dataset.json) |
| Rama retrospectiva | CAP06R; 3.108 correcciones de capital totales y 419 pendientes. | [Índice retrospectivo](../../../Limpieza/current_retrospective_dataset.json) |
| Auditoría | audit_ren00 y audit_pre00; 107 nombres de campo en el catálogo derivado. | dictionary_107.json |
| Preparación para modelos | T0/F0 y particiones operativas pendientes; sin entrenamiento en este trabajo. | [Protocolo 1.10](../../../Modelado/protocolo_metodologico.json) |



El índice base apunta al catálogo `Hackaton/Semana 1/Limpieza/runs/preaudit_20261016T211816Z_817285a5/dataset_catalog.json`. El retrospectivo apunta a `Hackaton/Semana 1/Limpieza/runs/capendorse_20261017T010844Z_fbf8cc20/dataset_catalog.json`. Los archivos current_run.json de otras carpetas identifican una operación o revisión concreta. No son intercambiables con esos dos índices de entrada.

## Archivos recibidos y unidades de observación

Los datos activos originales están en `Hackaton/Semana 1/Datos`. La descarga y el ZIP permanecen en `Preparación/data/raw/iaa_2026_part1_20261016`. El mapa central resuelve las rutas relativas desde `C:/dev/Hakaton`; las rutas antiguas archivadas no se reescriben.


| Tabla original | Filas | Columnas | Unidad de observación |
| --- | --- | --- | --- |
| addresses | 575.983 | 16 | Un inmueble/dirección; atributos físicos y geográficos. |
| claims | 163.150 | 12 | Un expediente reportado, valorado al 31-12-2024. |
| customers | 545.240 | 18 | Un cliente; maestro compartido y sin versión histórica por año. |
| policies_buildings | 707.726 | 27 | Un periodo de póliza de 2021 a 2024. |
| policies_contents | 721.617 | 28 | Un periodo de póliza de 2021 a 2024. |
| policies_motor | 979.968 | 39 | Un periodo de póliza de 2021 a 2024. |
| sample_submission | 626.639 | 2 | Una salida por fila test; no contiene costes reales. |
| test_buildings | 184.155 | 26 | Un periodo de póliza de 2025. |
| test_contents | 187.498 | 27 | Un periodo de póliza de 2025. |
| test_motor | 254.986 | 38 | Un periodo de póliza de 2025. |
| weather | 2.879.915 | 9 | Dirección y año; no implica disponibilidad ex ante de todo el clima anual. |



Las filas de póliza representan años naturales completos o fracciones de año. Una modificación durante el año puede generar varios periodos de la misma póliza. No deben contarse como asegurados distintos ni sumarse sus capitales como si fueran bienes diferentes. Los periodos terminan antes si hay cancelación o baja. El test corresponde a 2025 y sus 626.639 filas deben conservar su identidad al preparar la salida.

Las cifras anteriores se leen de los metadatos de los originales en esta conciliación. El historial de EDA, D30, usa los originales previos a DUP01. [Consultar EDA y gráficos históricos](../../../Analisis/runs/eda_20261016T165629Z_ab2a8365/informe.html). Los ficheros son sintéticos para el concurso; su procesamiento en servicios de IA se rige por el contrato archivado y no constituye permiso general de redistribución. [Reglas archivadas del proyecto](../../../../REGLAS_2026.md).

## Relaciones entre tablas y definición temporal


| Clave | Relación | Cardinalidad exigida | Cuidado al construir datos |
| --- | --- | --- | --- |
| customer_id | policies → customers | many_to_one | Maestro único; no sumar varias filas de cliente. |
| address_id | policies → addresses | many_to_one | Compartir dirección no implica mismo tomador ni mismos bienes. |
| address_id + year | policies → weather | many_to_one | Separar año de exposición de fecha de publicación del clima. |
| policy_id + line + loss_date | claims → periodo | Una asignación o excepción explícita | La fecha de ocurrencia debe caer entre period_start y period_end inclusivos. |
| row_id | test → sample_submission | one_to_one | Una predicción por fila, sin pérdidas ni duplicaciones. |



Una póliza mantiene policy_id entre años. El cliente puede tener varios ramos y varias personas pueden compartir una dirección. La clave de siniestro no debe unirlo indiscriminadamente a todos los años de su póliza: la asignación usa su ramo y fecha de ocurrencia. report_date indica cuándo se conoció, no el periodo de riesgo al que pertenece.

Las cardinalidades deben comprobarse en el ensamblado real: un join no debe multiplicar filas, exposición o coste de forma inadvertida. La revisión de claves y los diagnósticos existentes no sustituyen esos contratos dentro del futuro constructor de X y del objetivo. También falta fijar qué versión temporal de cada maestro podría conocerse en cada corte.

## Diccionario actuarial de las variables

El [diccionario consultable](diccionario.html) reúne los 105 nombres originales y las dos marcas derivadas. Cada entrada indica tablas, significado para el seguro y la tarifa, observaciones de disponibilidad, propuesta inicial D30 y tratamiento actual. También está en [CSV](tables/dictionary_107.csv) y [JSON](dictionary_107.json). La inclusión de una columna en el diccionario no la aprueba como predictor.

sum_insured es el límite de edificios o de contenidos, según el ramo. Es un importe por riesgo y periodo; no es prima ni pérdida observada, y no se anualiza con exposure. Un límite mayor puede cambiar la pérdida cubierta, pero no determina una variación proporcional de la prima o del coste esperado. vehicle_value_group en autos es una categoría de valor, no un importe monetario comparable al capital de hogar.

exposure mide tiempo cubierto. voluntary_excess y compulsory_excess son franquicias; el diccionario ya describe paid_to_date neto de franquicia, por lo que no se deben restar automáticamente otra vez del coste observado. incurred_to_date incluye pagado y estimación de caso, y recoveries son recuperaciones observadas. Los abiertos y los siniestros aún no reportados impiden equiparar ese incurrido con coste último conocido.

renewal_decision es un desenlace de fila y falta en test. audit_ren00 y audit_pre00 son metadatos de auditoría. customer_service_contacts tiene un problema distinto: la investigación D50 recomendó excluirlo por relación contemporánea con los siniestros y deriva, pero el guard vigente aún lo deja pasar. Esta brecha permanece abierta.

## Cómo se conserva el linaje

La unidad de preservación es el archivo original. Cada aplicación crea otra carpeta de corrida, un catálogo y bitácoras; no reemplaza el Parquet recibido. Cada catálogo declara rutas desde la raíz y SHA256. Las tablas sin cambios pueden seguir referenciando un archivo de una corrida anterior. No es necesario copiar las once tablas en cada operación.

El recorrido de pólizas es originales → ID01/EXP01 → CAP01 → CAT01/AGE01 → REN00. El de siniestros es original → DUP01 → PRE00. El catálogo base reúne ambas rutas. La rama retrospectiva parte de esa preparación y añade CAP02R → CAP03R → CAP04R → CAP05R → CAP06R sobre los capitales, heredando todos los demás datos.

Para identificar un padre no basta mirar parent_sha256: las operaciones añaden claves específicas como audit_parent_sha256 o endorsement_capital_parent_sha256. Se deben leer el índice, el catálogo completo, lineage.json y los hashes de la operación. Los códigos y los punteros se conservan por separado para poder distinguir qué versión se consumió.

La bitácora de un cambio de valor guarda identidad, tabla, posición, valor anterior y nuevo, regla, y referencias de revisión cuando proceden. Las operaciones recientes añaden hashes de cohorte, solicitud, origen y derivado. La reversión reconstruye los valores y la tabla Arrow del padre; no implica que el archivo Parquet recomprimido deba tener los mismos bytes. SHA256 comprueba la preservación de los archivos originales; la igualdad Arrow comprueba filas, valores, tipos y metadatos.

## Reglas aplicadas en la base


| Regla | Decisión | Alcance | Qué hace | Límite |
| --- | --- | --- | --- | --- |
| ID01 | D32 | 123.664 celdas customer_id | Ceros iniciales hasta ocho dígitos; maestro único y referencia existente. | Solo autos; no fusionar claves distintas del maestro. |
| EXP01 | D32 | 14.229 celdas exposure | Días cubiertos inclusivos/365; cuatro decimales. | No cambiar fechas ni recortar exposición a 1. |
| CAP01 | D36 | 2.073 celdas sum_insured | División por mil en lista autorizada con respaldo anterior original. | Base; no cascadas ni corrección de los 1.454 restantes. |
| CAT01 | D38 | 700.210 celdas construction_type | Mapa explícito de alias de caja. | t y w permanecen separados. |
| AGE01 | D38 | 2.936 celdas policyholder_age | Años cumplidos al inicio desde nacimiento del maestro. | Cambio de definición; no cambia driver_age. |
| DUP01 | D42 | 604 copias excluidas de claims | Igualdad total salvo ID; conserva CL+ocho dígitos. | Alias y filas excluidas conservados; 57 grupos no idénticos intactos. |
| REN00 | D45 | 12.041 periodos marcados | audit_ren00 en todas las filas de 2.742 pólizas congeladas. | No retirar pólizas ni siniestros, ni alterar fechas/etiquetas. |
| PRE00 | D47 | 413 siniestros marcados | audit_pre00; coste fuera del objetivo de periodos actuales. | No borrar siniestros ni modificar importes/estados/fechas. |



Los alcances cuentan celdas, filas o pólizas según la regla. No se suman para obtener un número de observaciones distintas: una misma fila puede recibir varios ajustes o una marca posterior. Los 12.041 REN00 son periodos de 2.742 pólizas; los 413 PRE00 son expedientes de siniestro.

## Identificadores de clientes y exposición

ID01 recuperó 123.664 celdas de customer_id: 98.110 en train de autos y 25.554 en test de autos. El código se trata como texto de ocho dígitos ASCII. La preparación rechaza claves inválidas, exige unicidad del maestro y pertenencia a él. No se fusionaron dos claves diferentes del maestro. El recálculo de Claude encontró una proporción de IDs cortos coherente con la pérdida de ceros iniciales.

EXP01 cambió 14.229 exposiciones de train, repartidas así:


| Tabla | Cambios de exposición | Antes en años registrados | Después con días inclusivos /365 |
| --- | --- | --- | --- |
| policies_motor | 5.736 | 1.058.509,6812 | 787.157,5563 |
| policies_buildings | 4.182 | 789.403,9271 | 590.560,1951 |
| policies_contents | 4.311 | 810.722,5688 | 590.859,3077 |



La exposición total de train pasa de 2.658.636,1771 a 1.968.577,0591 años. El test no necesitó correcciones de exposición. La regla es round((period_end − period_start + 1)/365,4). Las fechas no cambian. Un periodo inclusivo de 366 días daría 1,0027; ese ejemplo explica la convención, no afirma que haya tal periodo en los datos. D59 registró que los periodos 2024 terminan como máximo el 30 de diciembre.

La convención dominante respalda ACT/365, pero no equivale a confirmación del organizador. Sin uniformar unidades, una tasa por año podría tener un denominador artificialmente grande. No debe dividirse ciegamente toda exposición entre 365 ni reconstruirse un capital a partir de la exposición. [Limpieza ID01 y EXP01](../../../Limpieza/runs/clean_20261016T175335Z_a6412ce0/informe.html).

## Categorías de construcción y edad

CAT01 unifica las variantes explícitas de construction_type: Brick/BRICK→brick, STONE→stone, NON_STANDARD→non_standard, T→t y W→w, según el mapa archivado. Cambió 555.824 celdas de train de edificios y 144.386 de test, total 700.210. La normalización de caja no unifica t y w.

La revisión longitudinal de T/W encontró evidencia de recodificación alrededor de 2023 y preparó una candidata CON01. Esa candidata continúa fuera de los catálogos activos; el material físico que significan los códigos no se confirmó. Los 16 pendientes que dependen de T/W no quedan resueltos por CAT01. [Revisión de construcción y candidata no activa](../../../Revision_construccion/editions/clarified_20261016T192928Z/informe.html).

AGE01 define policyholder_age de hogar como años cumplidos desde customers.date_of_birth hasta period_start. Cambió 1.122/300 filas de train/test de edificios y 1.209/305 de contenidos, total 2.936. La edad de conductor de autos se conserva, porque puede corresponder a otra persona.

El recálculo D59 explica 2.432 diferencias por edad a la fecha de cotización, 457 por cumpleaños en el propio día de inicio y 45 por edad al final del periodo. Son 2.934 explicadas y dos sin explicar en esa revisión. Por tanto, AGE01 establece una definición común; no demuestra 2.936 errores de captura. La memoria inicial que resumía los tres grupos como explicación de todas las diferencias queda matizada por este corte. Los valores anteriores siguen en bitácora. [Refinamiento CAT01 y AGE01](../../../Limpieza/runs/refine_20261016T190025Z_6751bba4/informe.html) · [Evidencia D59 de las convenciones](../../../Validacion_ajustes_claude/runs/val_20261017T004949Z_62ad2cac/evidencia.json).

## Capitales y criterios de corrección

La revisión inicial separó 3.527 capitales extremos para estudiar: más de 10 millones CU en edificios o más de 1 millón en contenidos. Esos umbrales son filtros de revisión, no límites contractuales. Una cifra alta o una coincidencia de dirección por sí sola no autorizó una reparación.

CAP01 dividió por mil 2.073 filas con una referencia anterior original de la misma póliza, contexto exigido conocido e igual, ausencia de solape, distancia entre inicios de 1 a 400 días y razón entre capital hipotético y referencia dentro de 0,90–1,10. Se conservaron 1.454 pendientes y no se generaron cascadas a partir de reparaciones recién hechas. [Revisión de capitales](../../../Revision_capitales/runs/capital_20261016T180903Z_bceb990c/informe.html) · [Aplicación CAP01](../../../Limpieza/runs/capfix_20261016T184904Z_099a22b1/informe.html).

Los campos comparados en edificios fueron customer_id, address_id, construction_type, occupancy, accidental_damage_cover, voluntary_excess, compulsory_excess, smoke_alarms y mortgage. En contenidos fueron customer_id, address_id, tenure, security_level, high_value_items, accidental_damage_cover, works_from_home, lodgers, bicycle_cover y ambas franquicias. Igualdad en esos campos es un criterio parcial; no prueba que todos los factores tarifarios o el riesgo físico permanezcan constantes.

La segunda implementación D59 añade evidencia global compatible con la hipótesis×1000: separación de las nubes y coincidencia aproximada de medianas tras dividir. No confirma la unidad por el sistema de origen. No se usan importes de siniestro o prima para elegir el capital que conviene ni se copian límites de otra fecha.

## La rama retrospectiva de capitales


| Regla | Decisión | Cambios nuevos | Corregidos acumulados | Pendientes | Anclas posteriores test 2025 nuevas | Filas test corregidas |
| --- | --- | --- | --- | --- | --- | --- |
| CAP01 | D36 | 2.073 | 2.073 | 1.454 | 0 | 540 |
| CAP02R | D49 | 867 | 2.940 | 587 | 111 | 0 |
| CAP03R | D52 | 11 | 2.951 | 576 | 1 | 0 |
| CAP04R | D54 | 109 | 3.060 | 467 | 17 | 0 |
| CAP05R | D58 | 46 | 3.106 | 421 | 7 | 13 |
| CAP06R | D61 | 2 | 3.108 | 419 | 0 | 0 |



La columna de anclas cuenta respaldos posteriores de test 2025 para una corrección retrospectiva; la última columna cuenta filas corregidas que pertenecen a test. Son cosas diferentes. CAP01 utiliza respaldo anterior, por lo que la columna de anclas posteriores es cero; corrigió 540 filas test. La rama retrospectiva corrige otras 13 filas test, todas en CAP05R, y usa 136 anclas posteriores test acumuladas.

CAP02R aplicó las 867 propuestas de D48, 430 edificios y 437 contenidos; todas tenían respaldo posterior, 111 de test 2025. CAP03R añadió once de las doce discrepancias revisadas en D51 y mantuvo [identificador sintético omitido] pendiente, con un respaldo test nuevo. CAP04R corrigió 109 filas con contexto anterior distinto pero respaldo posterior completo compatible, 75 edificios y 34 contenidos, con 17 apoyos test. Cada lista quedó congelada antes de aplicar. [CAP02R](../../../Limpieza/runs/capretro_20261016T213644Z_9b52ecc4/rules.json) · [CAP03R](../../../Limpieza/runs/capnumeric_20261016T215017Z_75a1fda5/rules.json) · [CAP04R](../../../Limpieza/runs/capcontext_20261016T220924Z_4b397220/rules.json).

CAP05R aplicó 46 de las 48 referencias distantes revisadas: 18 edificios y 28 contenidos, con 21 anclas anteriores y 25 posteriores; siete apoyos test y 13 filas test corregidas. La excepción DIST01-R exige primera referencia original completa elegida antes del contexto/importe, extremos completos e iguales, más de 400 días y hasta dos años calendario, una sola fila intermedia incompleta sin cambios conocidos y pasos monetarios compatibles. Los 20 huecos CAL00 de sus 92 enlaces se conservaron. No se amplió el criterio general de 400 días. [Regla DIST01-R aplicada a la lista de 46](../../../Limpieza/runs/capdistant_20261017T004534Z_6e8f8e18/rules.json).

CAP06R añadió solo [identificador sintético omitido] y [identificador sintético omitido], como excepción manual por revisión de ampliaciones y renovaciones. Estas dos filas siguen sin cumplir DIST01-R; no se declara que una regla anterior haya pasado por reinterpretación. [Excepción manual CAP06R](../../../Limpieza/runs/capendorse_20261017T010844Z_fbf8cc20/rules.json).

![Evolución de capitales corregidos y grupos pendientes](figures/capitales_y_pendientes.png)

La suma se concilia en cada paso: corregidos acumulados + pendientes =3.527. Al corte son 3.108 + 419. Las 1.035 correcciones retrospectivas son 867+ 11+ 109+ 46+ 2. La base no incorpora estas 1.035. Las fechas anteriores de algunas anclas no convierten la selección retrospectiva de la regla en un procedimiento causal disponible en aquel momento.

## Dos casos completos de ampliaciones y renovaciones


| Periodo | [identificador sintético omitido] | [identificador sintético omitido] |
| --- | --- | --- |
| 2021 original | [identificador sintético omitido]: 27.200.000 CU | [identificador sintético omitido]: 25.700.000 CU |
| 2021 después de CAP06R | 27.200 CU | 25.700 CU |
| 2022 antes de ampliación | [identificador sintético omitido]: 27.700 hasta 03-05 | [identificador sintético omitido]: 26.200 hasta 11-09 |
| 2022 ampliado | [identificador sintético omitido]: 39.400 desde 04-05 | [identificador sintético omitido]: 37.700 desde 12-09 |
| 2023 al renovar | [identificador sintético omitido]: 28.300 hasta 15-05 | [identificador sintético omitido]: 26.700 hasta 03-02 |



Los contadores de renovación son 7→8→8→9 y 15→16→16→17. Las ampliaciones observadas de 2022 son 42,24% y 43,89%; al renovar bajan 28,17% y 29,18%. Dividir únicamente 2021 por mil conserva esa variación y da aumentos hacia la base inicial 2022 de 1,84% y 1,95%. No hay siniestros observados para estas pólizas. Los nulos high_value_items de [identificador sintético omitido] y security_level de [identificador sintético omitido] siguen sin imputar.

D60 comparó el patrón con otras 2.305 pólizas originales, excluyendo las dos focales de sus estadísticas. La selección fue exploratoria, después de observar los casos; no constituye una validación independiente o una prueba contractual. La autorización posterior D61 se limita a los dos IDs y conserva las primeras referencias completas de 2022 aunque contradigan una trayectoria suave. [Revisión de ocho periodos](../../../Revision_ampliaciones_capital/runs/endorsements_20261017T005807Z_7f43caaa/informe.html) · [Aplicación y seis periodos preservados](../../../Limpieza/runs/capendorse_20261017T010844Z_fbf8cc20/informe.html).

## Siniestros duplicados y coste observado

DUP01 identifica 604 pares con igualdad de los once campos distintos de claim_id; 1.208 registros implicados. Se conserva el representante CL seguido de ocho dígitos y se excluye su copia de nueve dígitos. El identificador completo retenido tiene diez caracteres por incluir CL. La selección se congela y guarda alias, exclusiones, originales de las filas y reversión.

claims pasa de 163.150 a 162.546 registros. Los 600 pares de 2022, tres de 2021 y uno de 2020 no representan 604 nuevos siniestros tras depurar. La reducción de incurrido neto aceptado registrada es 3.174.167,49 CU, de los cuales 358,88 corresponden a prehistoria y 3.173.808,61 a periodos observados. Es un efecto sobre el agregado diagnóstico de ese corte, no ahorro económico producido por la IA ni estimación de pérdida última evitada.

Los 57 grupos de coincidencias no idénticas se conservaron; no se borran por compartir póliza y fecha. Los demás siniestros y las pólizas permanecen. El EDA previo y el diagnóstico previo a DUP01 se consultan como históricos; el diagnóstico posterior recalcula el agregado con la capa depurada. [Revisión de los 604 pares](../../../Revision_duplicados/editions/explorer_fix_20261016T195247Z/informe.html) · [DUP01 aplicado y alias](../../../Limpieza/runs/dupfix_20261016T195843Z_fc0bb423/informe.html).

## Prehistoria de siniestros y objetivo

PRE00 marca 413 siniestros anteriores al primer periodo observado de su póliza. Son 409 aceptados y cuatro repudiados; el incurrido neto aceptado observado es 1.721.459,84 CU. Se conservan los 162.546 expedientes completos, sus importes, fechas y estados. Los 413 no se trasladan al primer periodo observado ni se convierten en pérdidas de una cobertura no registrada.

La marca audit_pre00 y target_scope.py impiden cargar su coste al objetivo de los periodos actuales; una asignación contradictoria obliga a revisar, no se resuelve silenciosamente moviendo fechas o poniendo importes a cero. D59 observó que los 413 se reportaron dentro de alguna cobertura observada, hecho compatible con reporte tardío pero insuficiente para reconstruir la cobertura histórica de ocurrencia. [Revisión de prehistoria](../../../Revision_prehistoria/runs/prehistory_20261016T210357Z_13161fac/informe.html) · [PRE00 y conciliación financiera](../../../Limpieza/runs/preaudit_20261016T211816Z_817285a5/informe.html).

El contrato económico busca coste último esperado por periodo en CU. El primer objetivo operativo propuesto T0 es incurrido observado neto de recuperaciones, excluyendo repudiados y respetando la asignación por ocurrencia. Las tablas diagnósticas existentes no son el T0 final materializado para entrenar. Abiertos, reporte tardío y valoración única al 31-12-2024 limitan una validación histórica causal: usar importes valorados después del corte no los hace conocidos en ese corte. [Objetivo y validación metodológica](../../../Modelado/METODOLOGIA_ACTUARIAL.md).

La salida solicitada por el reto es una predicción no negativa de coste por cada periodo test, en CU; no una prima comercial ni una tasa anual aislada. El contrato archivado define Tweedie D² con potencia 1,5. El scorer efectivo y la transformación entre tasas y coste por periodo aún deben implementarse y probarse conforme al protocolo; la documentación del contrato no acredita esa implementación.

## Calendario y rechazos de renovación

La revisión CAL00 estudió 500.245 continuidades que dejan sin cubrir el 31-12-2024: 200.063 de autos, 150.111 de edificios y 150.071 de contenidos. Los periodos terminan el 30-12 y reaparecen el 01-01-2025. El usuario decidió mantener las fechas pendientes. EXP01 respeta los días registrados, sin añadir ese día. No se desplazan siniestros para acomodar la discontinuidad. [Revisión del calendario](../../../Revision_calendario/runs/calendar_20261016T201406Z_01c55c49/informe.html).

La revisión de rechazos identificó 2.742 pólizas con declined_by_insurer en 2024 que continúan en 2025. REN00 marca todas sus 12.041 filas, 9.110 train y 2.931 test. No cambia etiquetas, fechas o siniestros. La continuidad observada impide interpretar automáticamente ese código como ausencia de cobertura posterior; su significado de negocio permanece sin confirmar. La pertenencia retrospectiva a REN00 tampoco es información ex ante de tarifa. [Historias de rechazo](../../../Revision_rechazos/runs/renewals_20261016T202736Z_b0ddd9b5/informe.html) · [REN00 aplicado](../../../Limpieza/runs/renaudit_20261016T203904Z_657dd741/informe.html).

## Los 419 capitales pendientes actuales


| Grupo histórico conservado | Filas actuales | Tratamiento al corte |
| --- | --- | --- |
| A_retrospective_D34 | 1 | Una discrepancia numérica conservada, [identificador sintético omitido]. |
| C_no_original_normal_reference | 108 | Mantener 108 por instrucción humana; no demostrar escala absoluta por vecinos de otras pólizas. |
| D_CAP01_dependency_only | 2 | Dos dependencias de reparaciones anteriores; sin cascada. |
| E_TW_dependency | 16 | 16 pendientes; CON01 no activa. |
| F_incomplete_context | 154 | 154 residuales tras revisar 202 y corregir 48 en CAP05R/CAP06R; conservar nulos. |
| G_other_conflicts | 138 | 138 sin adjudicación nueva; revisar cada conflicto. |



Los nombres de grupo proceden del inventario histórico; no se reevalúan para convertirlos en etiquetas de modelo. [identificador sintético omitido]/[identificador sintético omitido] conserva 29.300.000 CU. [identificador sintético omitido]/[identificador sintético omitido] conserva 377.000.000, aunque otra fila de la misma póliza recibió corrección previa. [identificador sintético omitido] tiene dos de los 108 registros sin referencia original: 107 pólizas no equivalen a 108 registros. Las historias no justifican cascadas o imputación silenciosa.

Hay 177 filas pendientes en test 2025 en CAP06R, frente a 190 en la base. No se pueden presentar 419 como pendiente de todas las versiones ni 190 como pendiente del test retrospectivo. La tabla [pendientes actuales por origen](tables/current_pending_by_table.csv) y el [inventario de 419](tables/pending_419_snapshot.csv) identifican el conjunto de este corte. El tratamiento para modelar valores extremos aún requiere decisión explícita y preparación dentro de cada corte, no se considera resuelto por documentarlos.

## Validaciones realizadas y alcance de la evidencia

Cada operación conservó su propia verificación: listas congeladas, comparación con el padre, preservación de otros campos, bitácora y reversión. Las operaciones recientes prueban también segunda aplicación sin cambios y rechazo de un valor inesperado. Que un control técnico pase acredita su criterio, no el significado contractual de una variable o la idoneidad completa del conjunto para modelar.

D59 es una segunda implementación asistida por Claude, desde originales y definiciones del proyecto, con 41 comprobaciones satisfactorias. Recalculó la base y la rama hasta CAP05R, sin reutilizar el código de aplicación de Codex. Aporta contraste de implementación; comparte definiciones y supuestos del proyecto, y declara revisión humana pendiente. No se denomina auditoría humana o validación independiente profesional. Su informe y dashboard no se reescriben para aparentar cobertura de CAP06R. [Revisión crítica D59](../../../Validacion_ajustes_claude/INFORME.md).

CAP06R tiene 279 controles propios y siete comprobaciones posteriores de activación, con reversión e idempotencia acreditadas. No se suman las pruebas de todas las corridas como observaciones independientes o una puntuación de confianza. Este dossier concilia fuentes, catálogos, metadatos y conjuntos de capitales; no reejecuta los 58 controles completos ni todas las reglas históricas.

La comprobación actual del guard 1.0 bloquea renewal_decision, audit_ren00 y audit_pre00, pero customer_service_contacts sigue aceptada. El resultado exacto está en [guard_probe.json](guard_probe.json). La exclusión de contactos debe aplicarse y probarse antes de entrenar; la recomendación D50 no es todavía una garantía operativa. El diccionario F0 y los selectores reales deberán tener pruebas de esta y otras dependencias temporales.

## Trabajo pendiente antes de modelar

El [registro de 58 controles](validaciones.html) conserva prioridad, alcance, criterio de cierre y trabajo pendiente de D56, más actualizaciones documentales al corte D61. Es una conciliación de estados, no una nueva aprobación de cada control. El registro se ofrece también en [CSV](tables/validation_register_58.csv) y [JSON](validation_register_58.json).

Los bloqueos de preparación son construir y conciliar T0 con componentes; fijar F0 y excluir contactos/etiquetas posteriores; implementar joins con cardinalidades; congelar V22/V23/V24 y roles sin contaminación; preparar transformaciones dentro de cada entrenamiento; y probar scorer, unidades y cobertura final de filas. El calendario 2024, la semántica de rechazo, los 419/1.454 capitales y la información de origen siguen pendientes según el catálogo elegido.

Se mantienen abiertas las coherencias de autos, coberturas e importes de hogar, maestros sin versión, clima anual, telemática, primas y atributos comerciales. D59 registra 161.822 NCB superiores a años con licencia, 3.717 edades implícitas de licencia menores de 16 y 2.533 eléctricos sin cilindrada. Son sondeos de revisión, no autorización para recortar o imputar. Tras DUP01, su corte registra 502/1.087 siniestros de daño accidental sin opción en edificios/contenidos y cuatro de daño propio fuera de comprehensive. Los ocho/tres netos superiores al capital que allí figuran no se presentan como recálculo sobre CAP06R.

Para avanzar, cada incidencia necesita una decisión con motivo, alcance temporal y verificación reproducible. Aprobar una cohorte de reparación no aprueba automáticamente entrenamiento, una regla de imputación general o un envío. T/W, nulos y los 57 grupos de siniestros no idénticos permanecen sin depuración automática.

## Uso de IA y responsabilidad de las decisiones

El participante definió prioridades, pidió revisiones de casos y autorizó explícitamente los conjuntos aplicados. Codex preparó análisis, código, propuestas y controles propios. Los informes enlazan las solicitudes y listas congeladas; una propuesta sin aplicar no se cuenta como transformación. Claude aportó investigación D50 y una segunda implementación D59 a solicitud del participante, con sus versiones y límites.

El informe D59 registra que los once originales y las capas analizadas se copiaron al espacio de trabajo en la nube de Claude y se contrastaron por SHA256 con los catálogos. Ese procesamiento previo forma parte de su procedencia, bajo el uso del concurso descrito en el contrato; no supone permiso de redistribución. Su resultado se cita con el catálogo CAP05R que realmente verificó.

Jev/TypeSafe se evaluó antes de financiarlo: saldo observado cero, un intento bloqueado por falta de fondos, cero decisiones de modelo recibidas, cero cargas de dataset y un piloto de 18 casos preparado sin ejecutar. No se añadieron fondos ni se usó Jev para decidir correcciones. No se acredita su precisión o calibración actuarial. [Evaluación Jev y propuesta de piloto](../../../Validacion_IA/jev_20261016/evaluacion.html).

Las referencias IAA priorizadas orientan ficha y linaje de datos (Documentación §2), reproducción/uso/riesgos (§§4–6), distinción de verificación propia y validación independiente (Gobernanza §2.8) y responsabilidad humana/comunicación de IA (Consideraciones profesionales §3.2 y §§3.5–3.6). Son documentos educativos; esta trazabilidad no acredita una certificación profesional. [Prácticas IAA aplicadas](../../../../../Preparaci%C3%B3n/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md).

## Cómo leer y reproducir la preparación

Se parte siempre de RUTAS_PROYECTO.json. Para análisis de base se abre current_dataset.json; para una reconstrucción retrospectiva explícita, current_retrospective_dataset.json. Antes de leer un archivo se verifica el SHA256 del catálogo. Un análisis guarda el hash del índice y del catálogo que consumió, ya que los punteros current pueden avanzar.

Los scripts de aplicación históricos exigen su padre congelado. No deben lanzarse contra CAP06R esperando reconstruir de nuevo una etapa anterior. Para reproducción integral hace falta un espacio aislado con la misma estructura, originales verificados, catálogos y padres de cada operación; restaurar el código archivado en su ubicación lógica y recorrer las instrucciones de esa operación. No se redirigen los índices de trabajo ni se ejecutan scripts dentro de source_snapshot asumiendo que sus rutas sigan siendo correctas allí. La reproducción integral aislada no se declara realizada por este dossier.

Los artefactos cerrados permiten una comprobación de integridad sin repetir transformaciones. Por ejemplo, el CLI de CAP06R devuelve una verificación de aplicación ya existente al repetir prepare, y verify sobre una corrida cerrada verifica el manifiesto. Eso no es por sí solo un recálculo independiente de la regla. Los comandos de la última operación son:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Limpieza\endorsement_capitals.py' prepare
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Limpieza\endorsement_capitals.py' verify 'C:\dev\Hakaton\Hackaton\Semana 1\Limpieza\runs\capendorse_20261017T010844Z_fbf8cc20'
```

D59 conserva validar_ajustes.py para un nuevo recálculo desde originales; su informe antiguo no actualiza su alcance sin una nueva ejecución y evidencia. Las bitácoras, hashes y solicitudes de cada operación están en sus carpetas. Los originales, carpetas cerradas y sus manifiestos se mantienen como evidencia; para corregir una presentación se crea una edición nueva.

## Registro de decisiones y fuentes

El [recorrido de decisiones](decisiones.html) recoge D28 a D61 e indica dónde se aplicó, revisó o dejó pendiente cada asunto. Los registros de modelos son contexto de preparación, sin atribuir entrenamiento. La decisión documental posterior no incorpora otra transformación de datos.

El [registro de fuentes](fuentes.html) enlaza los archivos que respaldan esta síntesis, con SHA256 y copia de los contextos mutables usados al comenzar. [facts.json](facts.json) contiene las cifras conciliadas; [source_register.json](source_register.json), la procedencia. Los índices base/retrospectivo y los archivos de datos se protegen por hash antes y después de la documentación. La evidencia de comprobación del dossier se guarda en [documentation_verification.json](documentation_verification.json).

Esta fotografía se actualiza mediante una nueva corrida cuando cambien datos o decisiones. El nombre CAP06R en una fuente, los 1.454 de la base, los 419 de la rama y el alcance CAP05R de D59 son parte del significado de sus resultados; deben viajar con ellos al citar cifras o preparar una entrega.
