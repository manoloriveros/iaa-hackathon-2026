# Validación exhaustiva de los datos de la semana 2 (mercado emergente)

Claude (Cowork), 23 de octubre de 2026. Evidencia del aporte [CLA-S2-20261023-004](../../Foro/FORO.md). El participante pidió continuar con las validaciones de datos de forma exhaustiva, sin pasar nada por alto.

Este documento explica qué se comprobó, qué salió y qué significa para el trabajo que viene. Las cifras salen de `evidencia_validacion.json`, que escribe `validar_datos_s2.py` desde los trece Parquet emergentes, siete del desarrollado y las capas que Codex ha construido esta semana, siempre después de comprobar sus huellas SHA-256. La tabla `tablas/controles.csv` tiene una fila por control y los casos por fila están en `Hackaton/Repositorio_IAA2026/privado/semana2/validacion_datos_claude_20261023/`, fuera de Git. Nada de esto cambia datos ni archivos de Codex, y es revisión de IA, no revisión profesional independiente.

## 1. Cómo leer el catálogo

Son 74 controles, numerados VE01 a VE75 (el VE74 cierra la lista, el VE75 se añadió al encontrar lo de `make_model` y el número VE71 quedó sin usar porque la tendencia anual y la inflación se trataron juntas en VE70), agrupados en diez familias: integridad, relaciones, calendario y exposición, clientes, direcciones y clima, pólizas por ramo, siniestros, test frente a entrenamiento, capas derivadas y límites. Cada control dice de dónde viene en la semana 1 (la columna `vd_semana1` apunta al control VD01–VD58 que lo inspira), así que la auditoría de la semana 1 queda recorrida entera sobre el mercado nuevo, y se añaden los controles propios de esta semana: referencias y gastos, bandas de edad, códigos locales, la cartera de broker, el clima de 2025 y las capas de Codex.

Cada control termina en uno de cuatro resultados:

| Resultado | Qué significa | Cuántos |
| --- | --- | ---: |
| Pasa | La propiedad esperada se cumple en todas las filas | 41 |
| Hallazgo | Algo que condiciona el modelo, la base o la entrega; lleva severidad P0, P1 o P2 | 12 |
| Límite | Algo que estos archivos no permiten resolver y hay que declarar | 5 |
| Informativo | Una descripción útil que no exige acción | 16 |

Las severidades siguen el criterio de la semana 1: P0 afecta al objetivo, a la exposición o a la fuga de información; P1 afecta a predictores o a la entrega; P2 es una incoherencia menor que conviene documentar.

![Resumen de los controles](fig1_controles.png)

## 2. Los doce hallazgos, uno a uno

Cuatro ya estaban en la mesa y la base de Codex los trata o los conoce; ocho aportan algo nuevo o lo precisan.

### Que condicionan el objetivo o la exposición (P0)

VE16, la exposición. 609 filas de entrenamiento no están en días / 365: 495 guardadas como días / 360 y 114 como número de días (207 y 47 en autos, 122 y 33 en edificios, 166 y 34 en contenidos). Ninguna fila queda sin explicar y todo el test está en días / 365. Son exactamente las filas que Codex corrigió en la base (VE54 lo comprueba fila a fila), así que el hallazgo está resuelto en la capa derivada y queda documentado aquí como control permanente: si llegara una capa nueva, el control avisa.

VE38, los contactos de servicio. `customer_service_contacts` mide el siniestro del propio periodo: en autos la frecuencia es 0,0002 con cero contactos y 1,125 con tres o más, y el 9,5 % del entrenamiento tiene tres o más frente al 0,8 % del test. F0 ya lo excluye. Se conserva como P0 porque cualquier variante que lo recupere se contaminaría.

### Que condicionan predictores o la entrega (P1)

VE75, `make_model`. Es un código de 300 niveles que no describe el vehículo: los 300 códigos mezclan varias carrocerías, combustibles y plazas, en los dos mercados, con entre 386 y 542 filas por código en el emergente. La frecuencia por código tiene más dispersión que Poisson (razón 1,595, p 2,6e-10) y también en el desarrollado (1,654), pero las frecuencias por código de los dos mercados no se correlacionan: 0,028 sobre los 300 códigos comunes. Es decir, lo que un modelo aprenda de ese código no se traslada de un mercado a otro, y dentro del emergente, con 450 filas por código, lo que aprende es en buena parte ruido. Esto encaja con el deterioro de W2-B02 que midió Codex (COD-S2-VAL02-20261023-SINTESIS: `x_make_model` acumula el 68,74 % de la ganancia de partición de entrenamiento en autos). Propuesta: tratarlo como factor de alta cardinalidad con contracción fuerte o dejarlo fuera del bloque base, y nunca trasladar su efecto desde el desarrollado.

VE36, el capital. 349 filas de hogar (157 de edificios y 192 de contenidos) están mil veces por encima de la nube normal, con huecos de 67 y 27 veces entre nubes y una prima por mil que vuelve al rango normal al dividir. El participante ya decidió dividirlas (CAPS2-01); el control queda para la siguiente capa.

VE42, peligro frente a cobertura. 23 siniestros aceptados de daño accidental en edificios (de 122) y 47 en contenidos (de 335) están en filas sin la cobertura opcional. Además, 3 siniestros de incendio en edificios y 1 de inundación en contenidos superan el capital asegurado de su fila: los tres incendios están cerrados y se pasan por poco (304.128 CU frente a 304.000, 286.093 frente a 286.000 y 181.064 frente a 181.000, como si el capital se hubiera agotado y quedaran gastos), y la inundación sigue abierta (50.885 frente a 47.400). En autos no hay ningún siniestro fuera de su cobertura. Es la misma clase de rasgo que VD09–VD11 en la semana 1: se conserva el coste y se documenta, sin recortar ni borrar.

### Incoherencias que conviene documentar (P2)

VE05 y VE21, la ocupación. Es la única columna de texto con variantes: 80 valores crudos, 40 al normalizar espacios y mayúsculas y 20 al quitar el prefijo «self-employed», que llevan 11.975 clientes, incluidos 1.819 «self-employed retired». Los 20 coinciden con el vocabulario del desarrollado. Si entra en un bloque condicional, normalizar y probar la marca aparte.

VE30, autos. 2.465 eléctricos con cilindrada informada (327 sin ella), como en la semana 1. La edad mínima del vehículo es 3 años (en el desarrollado, 0): el emergente no asegura vehículos nuevos, y un modelo trasladado no debería extrapolar a edades que allí sí existen. `compulsory_excess` es constante dentro de cada ramo (250 en autos, 350 en edificios y en contenidos) y también en los autos del desarrollado (250): no tiene información.

VE31, carnet y bonificación. 27.807 filas de autos tienen más años de bonificación que de carnet (el 20,2 % de las filas; en los autos del desarrollado, el 13,0 %). Ninguna banda de edad implica un carnet antes de los 16 años. Como en VD33, se conserva y no se recorta.

VE46, la decisión de renovación. `declined_by_insurer` tiene un periodo posterior en el 97,3 % de los casos de autos (95,6 % en edificios), mientras `lapsed_by_customer` y `cancelled` no lo tienen nunca. La etiqueta no describe una no renovación efectiva, como ya pasaba con REN00. No entra en los predictores.

VE52, los gastos. La comisión de `comparison_site` está vacía en la tabla de gastos del emergente, aunque ese canal tiene el 5,0 % de las filas de entrenamiento y el 5,0 % del test. No afecta a las veinte referencias (17 broker y 3 directas). Se declara como incoherencia de la fuente.

VE59, F0. Las matrices reproducen sus columnas de origen sin ninguna discrepancia de valores (ver sección 4), pero llevan un predictor constante, `x_compulsory_excess`, en los tres ramos, y `x_renewal_count` es idéntico a `x_customer_tenure_years` en el 100 % de las filas. Conviene retirar el constante y uno de los dos duplicados antes de la siguiente tanda.

## 3. Lo que pasa, área por área

Integridad (VE01–VE07). Los trece archivos coinciden con el manifiesto de descarga de Codex y con los tamaños del listado de Kaggle; las columnas de cada tabla son exactamente las del diccionario de la página, con las de un solo mercado bien separadas; los tipos de las columnas comunes son los mismos que en el desarrollado; no hay duplicados exactos y todas las claves son únicas; ninguna clave, fecha ni exposición es nula; y todos los numéricos están dentro de los rangos que da el diccionario (viento 0–10, sequía e incendio 0–1, días 0–366, capitales y primas positivos).

Relaciones (VE08–VE13). Todas las claves de pólizas y test encuentran su cliente y su dirección, y no hay clientes ni direcciones sin uso. El clima tiene cada una de las 136.914 direcciones exactamente una vez en 2023, 2024 y 2025. Los identificadores tienen formato fijo (prefijo del ramo y ocho dígitos; `claim_id` es «CL» y ocho dígitos; 13.490 clientes conservan sus ceros iniciales, así que no hace falta nada como ID01). Ningún `policy_id` aparece en dos ramos. Los 752 clientes y 8.046 direcciones que comparten identificador con el desarrollado son entidades distintas: el apellido coincide en el 0,5 % y el tipo de vivienda en el 25,6 %, lo que cabe esperar por azar. Las claves de fila y de póliza también se repiten entre mercados: los 47.283 `row_id` del entrenamiento de autos emergente existen en el desarrollado (ninguno del test ni de los ramos de hogar), y coinciden 298, 129 y 194 `policy_id` por ramo y 19 `claim_id`. Es el mismo rasgo que señala VAL04 de Codex; esta validación nunca cruza mercados por esas claves, y cualquier capa que una los dos mercados debe llevar el mercado dentro de la clave. En los 56.915 hogares con edificios y contenidos el mismo año, canal e inicio coinciden salvo en 991 inicios, y las 31 bandas de edad distintas se explican todas por un cumpleaños entre dos inicios distintos; ningún inquilino tiene póliza de edificios.

Calendario (VE14–VE19). Ningún periodo cruza el año natural ni supera los 365 días; 2024 termina el 30 de diciembre en todas las pólizas y ningún periodo ni siniestro cubre el 31-12-2024, el mismo día que faltaba en la semana 1; no hay solapes dentro de una póliza y los únicos huecos son los de un día en la transición a 2025 (20.097, 12.103 y 14.922; 47.122 en total, la misma cifra que DAT-008 de Codex). `new_business` equivale a `renewal_count = 0` sin excepción, `renewal_count` es exactamente el año menos `customer_since_year` en el 100 % de las filas, y el nuevo negocio solo aparece en el primer año de cada póliza (también en el segundo tramo de ese año cuando hay un cambio a mitad). Los días entre cotización e inicio van de 0 a 30, con mediana 13 en todos los segmentos.

![Calendario y exposición](fig2_calendario.png)

Clientes (VE20–VE24). Los dominios son los del diccionario. `customer_since_year` va de 2008 a 2025 con unos 1.800 clientes por año hasta 2022, 3.727 en 2023, 5.608 en 2024 y 99.088 en 2025: 27.433 clientes de entrenamiento ingresaron antes de que la aseguradora entrara al mercado, según cuenta la página de datos, y son exactamente los 27.433 sin `campaign_code`. El código de campaña existe para todo el que ingresó desde 2023 y falta para los anteriores, así que es un rasgo de la fecha de ingreso, no una campaña. Los años en la dirección nunca superan la edad máxima de la banda. `prior_claims_5y`, declarado al ingresar, ordena la frecuencia de forma plausible (en autos, 0,93 veces la media con cero y 1,76 con cuatro), sin un salto que delate que mida el propio periodo.

Direcciones y clima (VE25–VE29). Dominios del diccionario; la distancia al río baja con la zona de inundación; sin elevaciones ni distancias negativas; ninguna vivienda construida después de su primer periodo (año de construcción entre 1862 y 2021); la cuota de edificios protegidos es la misma en todos los tramos de construcción (3 %). El clima de 2025 no copia el de 2024 en ninguna dirección, las heladas y la temperatura van en sentidos opuestos (correlación −0,886) y la sequía estival apenas se relaciona con la lluvia anual (0,277), lo que cabe anotar. Sobre la persistencia que usa CLIMA-S2-01: con el umbral 0,80 medido solo entre 2023 y 2024 pasarían cuatro variables (exposición al viento, índice forestal, lluvia y temperatura media); exigirlo también entre 2024 y 2025, como hizo la variante, deja tres y usa 2025 para elegirlas, que es la dependencia que señaló COD-S2-VAL04-20261023-CLIMA-AVISO. Frente al desarrollado, el emergente es otro clima: 15,5 días de granizo frente a 6,5, índice forestal 0,53 frente a 0,14, 1.378 mm de lluvia frente a 1.009, y 57.237 direcciones-año con un índice forestal fuera del rango que el desarrollado llegó a observar.

Pólizas (VE30–VE38, VE46, VE75). Dominios del diccionario en los tres ramos; los códigos de construcción son BRK, STN, WOD y MIX y F0 los traduce a brick, stone, timber y mixed_or_nonstandard. De un año al siguiente la póliza evoluciona como debe: el carnet sube un año en los 40.181 pares de autos, la banda de edad nunca retrocede, el cliente no cambia, y el capital de hogar se indexa un 3,0 % en edificios y un 2,0 % en contenidos (razones año a año con percentiles 10 y 90 entre 1,027 y 1,033 y entre 1,018 y 1,022), salvo los 96 saltos ×1000 y 93 caídas que son el ruido de escala del capital. La prima escrita es anual: su mediana apenas cambia con la exposición de la fila (en autos, entre 513 y 546 CU en todos los tramos) y sube de un año al siguiente (498, 505 y 540 CU en autos). El descuento toma tres valores: 0, 5 % y 10 %.

Siniestros (VE39–VE45). Fechas y dominios limpios: ocurrencias del 27-10-2021 al 29-12-2024, reportes del 02-01-2023 al 30-12-2024, ninguno después del corte ni antes de la ocurrencia; `third_party_id` solo en peligros de terceros y `repairer_id` solo en daños propios y daños a terceros. Importes coherentes: pagado ≤ incurrido, recuperaciones entre 0 y el incurrido, netos no negativos, cerrados sin reserva, rechazados sin pago; las recuperaciones solo aparecen en siniestros cerrados (el 24 % del incurrido de daños propios y el 2,3 % de robo), como en la semana 1. La asignación por póliza y fecha da 9.222 únicos y 36 sin periodo, todos anteriores al primer inicio de su póliza (entre 14 y 431 días) y 35 de ellos reportados dentro de un periodo observado; no hay ambiguos ni siniestros en los huecos de un día. No hay duplicados de ninguna clase (ni iguales salvo `claim_id`, ni misma póliza-peligro-fecha). El retraso de reporte tiene mediana de 9 días en autos y 99 en lesiones corporales, con 31 siniestros de autos reportados después de un año (316.442 CU). La concentración es muy distinta por ramo: los diez mayores siniestros son el 5,7 % del coste en autos y el 25,6 % en edificios.

![Siniestros](fig6_siniestros.png)

Test (VE47–VE52, VE73). El test tiene las mismas columnas que el entrenamiento salvo `renewal_decision`, sin categorías nuevas; los numéricos fuera del soporte son pocos y explicables (993 filas con `renewal_count` 17, una renovación más; 116 vehículos de 27 años; 49 carnets de 74 años). El 76 % de las filas de 2025 son nuevo negocio, el 88–91 % de él empieza en enero, y ninguna renovación del test carece de fila en 2024. El canal del nuevo negocio de 2025 es el mismo del orgánico (70 % broker, 25 % directo, 5 % comparador); la mezcla por región, densidad y zona de inundación no cambia (PSI menor que 0,001). La plantilla tiene las 209.063 filas en el orden de los tres test concatenados y todas sus predicciones son cero. Las veinte referencias son filas del test con exactamente los mismos valores en todas las columnas; 19 cubren menos de un año y 15 menos de 0,99, y dos son tramos de pólizas con otra fila en 2025.

![Qué cambia en 2025](fig5_test.png)

Capas derivadas (VE53–VE61). Es la parte de la validación que más tranquiliza, porque recalcula las capas de Codex con código propio. Las seis tablas de periodos de la base son idénticas a los originales salvo la exposición, y sus 609 cambios son exactamente mis filas fuera de días / 365. T0 coincide en las 109.296 filas al centavo (27.997.991,57 CU; 8.071 filas con coste positivo), con los componentes, los conteos de aceptados, positivos y abiertos, las fórmulas de T1 y el test sin etiquetas. Los 36 siniestros anteriores a la cobertura son los míos y los 9.102 incluidos en T0 caen en el mismo periodo. Los 36.398 grupos de las particiones son exactamente los componentes conexos de cliente y dirección que yo recalculo con union-find, ningún cliente ni dirección aparece en dos folds, el test no tiene fold, y las banderas de entidad vista coinciden al 100 % con la lectura «vista en cualquier año anterior» (con la lectura estricta «vista el año inmediatamente anterior» fallan 12 direcciones de 318.359). En los cinco folds de desarrollo y de población nueva, la evaluación es el fold k, el ajuste no lo contiene, no comparten clientes ni direcciones, y cada fila de 2023 y de 2024 se evalúa exactamente una vez. Las matrices F0 reproducen cada predictor desde su columna de origen (pólizas y direcciones), los derivados son correctos (antigüedad, mes de inicio, edad de la vivienda, logaritmo del capital nulo exactamente sobre el filtro), no contienen columnas excluidas y el contrato coincide con las columnas. El OOF de la tercera tanda (dev3) tiene las mismas filas, folds, T0, exposición y nuevo negocio que la base, `prediction = tasa × C0` en el 100 % de las filas y C0/e entre 0,932 y 1. Las tablas de las decisiones del participante (349 capitales, que son los mismos de la auditoría de Codex, y el bloque de clima) son coherentes con los originales.

## 4. Los cinco límites

Son cosas que estos archivos no permiten resolver y que el informe final debe declarar: los maestros de clientes y direcciones no tienen fecha de versión y se asumen estables (todo el nuevo negocio del test tiene `customer_since_year` 2025); el clima de 2025 está en el archivo aunque la página anuncia 2023–2024 y no es información conocida al cotizar; contactos, impagos y desocupación no tienen anclaje temporal (los impagos ordenan la frecuencia, 0,044 con cero y 0,123 con tres en edificios, pero no se sabe cuándo se registran); hay una sola valoración al 31-12-2024, con 1.055 abiertos dentro de T0 y una reserva de caso del 17,8 % de T0, sin triángulo; y todo esto es revisión de IA.

## 5. Hechos descriptivos que conviene tener presentes al modelar

- Los nulos del 12 %. Varias columnas de pólizas y de direcciones tienen entre el 11 % y el 12 % de ausencias (tipo de suelo, tejado, energía, distancia al río, aparcamiento, cilindrada, edad del vehículo, alarmas, desocupación, seguridad, objetos de valor), y el 41,7 % de las direcciones tiene algún nulo. La cuota es la misma en 2023, en 2024, en las renovaciones y en el nuevo negocio de 2025 (la mayor diferencia entre la cartera nueva y 2024 es 0,005), igual en las seis regiones, y las ausencias no se correlacionan entre columnas (todas por debajo de 0,005). Se comportan como aleatorias; una categoría «ausente» aprendida en el entrenamiento tendrá el mismo soporte en el test.
- Los cambios a mitad de año son cambios de objeto: en autos, 10.062 de los 10.091 cambios de vehículo (`make_model`); en edificios, los 3.036 son mudanzas (cambia la dirección) con nuevo capital; en contenidos, 3.717 mudanzas y 1.799 cambios de capital.
- La estructura de los hogares: 81.089 clientes con un ramo, 39.959 con dos y 14.808 con tres; 2.235 direcciones con más de un cliente, hasta 8.
- El historial propio sí informa: en las pólizas con los dos años, la frecuencia de 2024 es 0,148 sin siniestro en 2023 y 0,310 con él en autos (0,044 frente a 0,085 en edificios).
- Las siniestralidades observadas sobre la prima escrita prorrateada son 0,71 y 0,63 en autos, 1,49 y 0,83 en edificios y 0,73 y 0,66 en contenidos (2023 y 2024, con 2024 truncado por reporte y desarrollo). La prima escrita no sirve de ancla de suficiencia.

![Los nulos del 12 %](fig3_nulos.png)

![make_model](fig4_make_model.png)

## 6. Concordancia con la auditoría de datos de Codex (S2-VAL04)

Mientras se preparaba este informe, Codex cerró su propia auditoría de datos de las dos semanas (COD-S2-VAL04-20261023-SINTESIS y COD-S2-VAL04-20261023-CLIMA-AVISO). Las dos revisiones se hicieron por separado y con código distinto, así que donde coinciden en la cifra exacta la lectura gana fuerza:

| Codex (VAL04) | Este informe | Coincide |
| --- | --- | --- |
| DAT-007: 27.807 filas con NCB mayor que licencia | VE31: 27.807 | Sí, cifra exacta |
| DAT-008: 47.122 huecos del 31-12-2024 | VE15: 20.097 + 12.103 + 14.922 = 47.122 | Sí; la primera corrida de VE15 decía 20.110 en autos por un error de alineación de índices que se corrigió al cotejar |
| DAT-009: 348 periodos posteriores a `declined_by_insurer` | VE46: 213, 108 y 27 (el 97,3 %, 95,6 % y 90,0 % de 219, 113 y 30) | Sí, suma 348 |
| Colisiones de identificadores entre mercados, incluidos los 47.283 `row_id` de autos | VE12: 47.283 `row_id` de autos, 0 en test y hogar, 298 + 129 + 194 `policy_id`, 19 `claim_id` | Sí |
| DAT-003 (alta): la selección de variables de CLIMA-S2-01 depende de 2025 | VE28: con 2023–2024 solo pasarían cuatro variables; con los dos pares, tres | Sí; el aviso es correcto y la variante queda como escenario declarado, no como información al cotizar |
| DAT-004: CAPS2-01 reproduce las 349 filas con el rango normal de 2023 | VE61: las 349 son el mismo conjunto que la auditoría de capital de Codex | Sí |

Lo que esta validación añade a la de Codex está en la sección 2: `make_model`, los predictores constante y duplicado de F0, los daños accidentales sin cobertura y los cuatro netos sobre el capital, la ocupación y el `campaign_code` como rasgo de la fecha de ingreso.

## 7. Qué no cubre esta validación

No valida los modelos ni sus métricas (eso es lo que Codex llama el selector y la confirmación de 2024), no estima el último ni la cola de reporte (VARIABLES_Y_ULTIMO.md de Codex y la revisión CLA-S2-20261023-001), y no sustituye la revisión humana. Los casos por fila existen para que esa revisión pueda mirar cualquier control sin volver a correr nada.

## 8. Qué contiene y cómo repetirlo

| Archivo | Contenido |
| --- | --- |
| `validar_datos_s2.py` | Los 74 controles desde los originales y las capas de Codex, con comprobación de huellas |
| `figuras_validacion.py` | Las seis figuras |
| `evidencia_validacion.json` | Resumen, tabla de controles y el detalle de cada uno |
| `tablas/controles.csv` | Una fila por control: área, título, resultado, severidad, observado, esperado, control de semana 1 y archivo de casos |
| `cifras_informe.json`, `verificar_informe.py`, `verificacion_informe.json` | Cada cifra de este informe y del aporte con su ruta en la evidencia, y el resultado del verificador |
| `tablero.html`, `construir_tablero.py` | Tablero sin conexión con los controles filtrables, el detalle de cada uno y las figuras, y el script que lo genera desde la evidencia; se queda en el repositorio |
| `aporte_CLA-S2-20261023-004.md` | El texto publicado en el foro |
| `parche_20261024.py` | Constancia de la corrección de VE15 y de las seis claves añadidas al cotejar con VAL04, ya aplicada al script |
| `manifiesto.json` | SHA-256 de entradas, scripts, salidas, documentos y casos privados |

Desde `C:/dev/Hakaton`, con un Python que tenga pandas, pyarrow, scipy y matplotlib (el `.venv` del laboratorio con `PYTHONPATH` apuntando a `Preparación/.cache/parquet-reader`):

```powershell
$py = 'C:/dev/Hakaton/Preparación/.venv/Scripts/python.exe'
$env:PYTHONPATH = 'C:/dev/Hakaton/Preparación/.cache/parquet-reader'
$dir = 'Hackaton/Semana 2/Claude/validacion_datos_20261023'
& $py "$dir/validar_datos_s2.py" --out "$dir/repeticion" --privado "$dir/repeticion/privado"
& $py "$dir/verificar_informe.py"
```

Sin argumentos lee `Hackaton/Semana 2/Datos/emerging`, `Hackaton/Semana 1/Datos`, la corrida base, la F0, el OOF de dev3 y las tablas de las decisiones del participante, y se detiene si alguna huella no coincide. La corrida original se hizo en la nube de Claude (Python 3.13, pandas 3.0, numpy 2.5, pyarrow 26, scipy 1.18) en unos dos minutos; repetida dio la misma evidencia salvo la hora, y la corrección posterior del conteo de VE15 y las seis claves añadidas al cotejar con VAL04 no cambiaron ningún otro valor ni las figuras.
