# Doce pendientes de F3c: resultados, límites y decisiones

Codex, 26 de octubre de 2026, Bogotá. Revisión propia con código y cálculos locales. Las recetas originales y sus factores son de Claude; la nueva comparación, auditoría y verificación son de Codex. No es validación profesional independiente.

La revisión de los doce puntos terminó, pero los doce requisitos no quedaron aprobados. Hay una ganancia global condicional de los factores y resultados adversos que impiden promover F3c o acreditar su uso profesional. Se conserva final_creible sin factores como comparador sencillo, junto con todas las alternativas. La política humana v2 mantiene a A1 como titular común; este trabajo no revierte esa decisión ni cambia una selección en Kaggle.

## Alcance y criterio congelado

Se guardó el plan antes del cálculo nuevo y se comentó en el foro. Ya se habían leído las sensibilidades de Claude y los contrastes P19/P20/P26/P30/P32. Por ello congelar esta tanda no devuelve independencia a 2024. La comparación evalúa una receta residual trasladada entre años, sobre las mismas filas, costes T0 y bases guardadas; no llama OOF al F3c de producción aprendido con ambos años.

El margen global es 0,0005, con 10.000 bootstrap emparejados por componente conexa cliente-dirección y banda de familia 6. Los intervalos fijan precios/modelos y condicionan los ancestros guardados: no incluyen incertidumbre de reentrenamiento fuente, selección adaptativa o suficiencia de reservas. Las sensibilidades no reciben una garantía simultánea sobre toda la búsqueda histórica. Se usan niveles aprendidos en entrenamiento. Los exponentes heredados de final_creible fueron elegidos con público 2025 y se declaran; también se calcula una vista sin ellos.

| N.º | Prueba | Resultado del cierre | Consecuencia |
| --- | --- | --- | --- |
| 01 | Comparar F3c y sin factores | Ganancia condicional; promoción no acreditada | Mantener final_creible como referencia de esta comparación. Conservar el titular A1 de la política v2, B00 y las alternativas; no promover F3c por este informe. |
| 02 | Protección de negocio nuevo | Salvaguarda original fallida; incertidumbre abierta | No presentar falta de potencia o enmienda como aprobación estadística. Revisión de cohortes largas y datos adicionales antes de uso profesional. |
| 03 | Modelo frente a sondas | Identificación parcial | No atribuir a estructura toda la ganancia pública ni inferir privada a partir de la misma señal. No producir sondas nuevas para cerrar documentalmente. |
| 04 | Estabilidad de factores | Falla estabilidad de contribución en autos NB | No acreditar factores propios estables para autos NB; no escoger retrospectivamente solo los pasos favorables. |
| 05 | Concentración | Fragilidad identificada, veto nominal pasa por poco | Mantener referencia y mostrar concentración. No afirmar fragilidad mayor/menor que otra receta no comparada con los mismos escenarios. |
| 06 | Conteos, coste y tardíos | Curvas separadas; último real sin identificar | No usar una curva de coste como si acreditara frecuencia. Escenarios no establecen suficiencia ni absorción real de nuevas sondas. |
| 07 | Reservas por componentes | Sensibilidad medida; suficiencia abierta | Conservar tensiones por peligro y compensaciones; bloquear acreditación de reservas y uso comercial profesional sin revisión. |
| 08 | Particiones de la cadena | No acredita cadena integral protegida | No etiquetar resultados como prueba temporal íntegra. Nueva receta con limpieza/desarrollo/categorías/calibración dentro de cada ámbito antes de sostener esa afirmación. |
| 09 | Exploración y confirmación | Clasificación e inventario cerrados por alcance | Todos estos resultados siguen exploratorios y adaptativos. La corrección familia 6 no borra selección previa. |
| 10 | Disponibilidad y soporte | Disponibilidad no acreditada y soporte escaso | Neutralizar factores propios si falta disponibilidad/admisibilidad; para riesgo base sin soporte, revisión con constante. No aprobar uso real con esta evidencia. |
| 11 | Reproducción desde originales | Parcial, criterio integral incumplido | Prohibir la afirmación de reproducción integral o independiente. Resolver grafo portable A1/T2b y ancestros FSp para F4c; acta real pendiente. |
| 12 | Veinte primas | Cálculo y sensibilidad verificados; uso limitado | Revisión individual antes de publicar/usar. Escenarios no son IC; beneficio 8% no se presume margen de incertidumbre suficiente. |

## Comparación directa sobre la misma base

| Vista | Δ D² global | Banda condicional familia 6 | Δ NB | Δ autos NB |
| --- | --- | --- | --- | --- |
| DEV23_T2b → HOLD24_T2b | 0,002392 | [0,000526; 0,004436] | 0,000478 | -0,001004 |
| DEV23_T2b → HOLD24_A1 | 0,002606 | [0,000711; 0,004630] | 0,000773 | -0,000427 |
| DEV23_T2b → HOLD24_mezcla | 0,002473 | [0,000636; 0,004489] | 0,000825 | -0,000316 |
| HOLD24_T2b → DEV23_T2b | 0,002020 | [-0,000420; 0,005109] | 0,009291 | 0,017630 |

Las tres primeras vistas comparten resultados 2024 y no son tres pruebas independientes. El traslado 2024 a 2023 estudia estabilidad inversa y no es un pronóstico. El primario mejora 0,002392 y su límite inferior 0,000526 supera por poco 0,0005. Esa condición aislada pasa, con sus límites. La comparación reponderada por ramo, negocio y banda de exposición 2025 da 0,001208, con IC95 [-0,002884; 0,005163]: sigue siendo incierta para la composición futura.

| Segmento 2024 | Sin factores | Con factores | Diferencia | IC95 condicional |
| --- | --- | --- | --- | --- |
| motor | 0,074110 | 0,077284 | 0,003173 | [0,000787; 0,005725] |
| buildings | 0,076274 | 0,076274 | 0,000000 | [0,000000; 0,000000] |
| contents | 0,089320 | 0,094022 | 0,004702 | [0,000689; 0,008675] |
| new_business | 0,093210 | 0,093689 | 0,000478 | [-0,003696; 0,004681] |
| renewal | 0,120607 | 0,123287 | 0,002680 | [0,001214; 0,004245] |

En la celda autos/negocio nuevo la diferencia es -0,001003611, apenas 0,000003611 por debajo del piso adicional predeclarado de −0,001. Ese cruce es frágil por proximidad al umbral y no prueba daño poblacional; se conserva. El intervalo de negocio nuevo es compatible con pérdidas materiales. Las carencias de la cadena y la inestabilidad de su contribución impiden convertir la ganancia global en promoción.

## Protección original y representatividad del negocio nuevo

El control original A1 contra R0 dio +0,013062 en la población nueva y límite 95−0,010535, inferior al mínimo −0,001. Falló. La enmienda humana v2 del 24 de octubre retiró el veto del intervalo y promovió A1 sin reabrir 2024; se conserva esa decisión y su autoría. La potencia insuficiente describe incertidumbre, no aprobación de no inferioridad. Fuente: política v2 y rev5_resultados.json, t4_politica, paso1_A1_vs_R0. No confundir aquel contraste con el incremento F3c contra final_creible de esta tanda, ni la marca new_business con un cliente totalmente nuevo para todos los ramos.

| Año | Periodos | Nuevo negocio | % filas NB | % exposición NB |
| --- | --- | --- | --- | --- |
| 2023 | 50.094 | 5.974 | 11,93 | 6,31 |
| 2024 | 59.202 | 9.063 | 15,31 | 9,08 |
| 2025 | 209.063 | 158.980 | 76,04 | 76,88 |

El soporte grueso por ramo/negocio 2024 pasa el filtro descriptivo de 100 grupos efectivos y 30 grupos positivos; ese resultado no cubre la banda que domina 2025. Los periodos con exposición≥0,9 muestran otra escala:

| Ramo | NB largo 2024 | Periodos positivos | NB largo 2025 |
| --- | --- | --- | --- |
| motor | 343 | 54 | 56508 |
| buildings | 203 | 3 | 35021 |
| contents | 246 | 11 | 43113 |

Edificios y contenidos solo aportan 3 y 11 periodos positivos en la banda larga de 2024. Las proporciones futuras multiplican esa información escasa. Se conservan por año, ramo y negocio las exposiciones, tamaños efectivos de filas y componentes y grupos positivos en results.json/support. No se altera la partición para mejorar soporte. El corte por componentes estrictamente nuevos deja 8972 filas, frente a las 9.063 con marca contractual NB.

## Cuánto aporta la estructura y cuánto la lectura pública

| Cálculo 2024 | Constante | Sin factores | Con factores |
| --- | --- | --- | --- |
| Nivel histórico, formas públicas fijas | 0,070391 | 0,121354 | 0,123746 |
| Mismo nivel + overlay público recibido | 0,071990 | 0,123943 | 0,126365 |
| Sin exponentes adicionales del público | 0,070391 | 0,122722 | 0,125131 |

La constante usa una tasa por ramo y negocio con la misma optimización Tweedie histórica y exposición efectiva. En la fila del overlay se aplica a los tres modelos el mismo multiplicador público guardado. Esto compara un procedimiento común de aplicación; no estima una calibración pública propia de la constante. Los momentos extraídos del tablero dependen de la predicción sondeada, por lo que no se transfieren como si identificaran el óptimo de otro vector. Esa parte del pendiente queda sin identificar y no se inventan sondas.

La lectura pública histórica real sigue separada: final_creible0,16519 y F3c 0,16914, diferencia +0,00395. Comparte selección adaptativa y feedback del tablero; no es un privado observado. Reoptimizar en las etiquetas del mismo año prueba forma con nivel oráculo: en la vista ponderada 2025 del primario el incremento pasa a -0,000930. Ese diagnóstico explica la tensión con B05 de Claude; no se mezcla con el pronóstico de nivel aprendido en entrenamiento.

## Estabilidad de género, teletrabajo y marketing

| Paso | Autos NB 2024 | Contenidos NB 2024 | Autos NB traslado inverso |
| --- | --- | --- | --- |
| gender | -0,002891 | 0,003734 | 0,015272 |
| works_from_home | 0,000000 | -0,003000 | 0,000000 |
| marketing_segment | 0,000000 | 0,003844 | 0,000000 |

Los incrementos de la tabla mantienen el nivel de la base fijo y aplican la secuencia completa, sin seleccionar pasos después. Género perjudica autos NB en 2024 y ayuda en el traslado inverso; teletrabajo perjudica contenidos NB 2024. Los factores de género mantienen su dirección agregada, pero su contribución fuera del año cambia. Varios niveles de marketing cruzan 1. No corresponde afirmar estabilidad por una ganancia global ni retirar retrospectivamente un nivel para hacer pasar la prueba.

| Variable | Ramo | Nivel | Factor 2023 | Factor 2024 | Cruza 1 |
| --- | --- | --- | --- | --- | --- |
| gender | motor | F | 0,9161 | 0,8884 | no |
| gender | motor | M | 1,0856 | 1,1126 | no |
| gender | contents | F | 1,0592 | 1,0577 | no |
| gender | contents | M | 0,9376 | 0,9407 | no |
| works_from_home | contents | False | 0,9449 | 0,9514 | no |
| works_from_home | contents | True | 1,0893 | 1,0692 | no |
| marketing_segment | contents | mature_affluent | 0,9681 | 0,9963 | no |
| marketing_segment | contents | mature_budget | 1,0115 | 1,0056 | no |
| marketing_segment | contents | mature_mainstream | 1,0496 | 0,9883 | sí |
| marketing_segment | contents | midlife_affluent | 0,9775 | 0,9454 | no |
| marketing_segment | contents | midlife_budget | 1,0164 | 1,0011 | no |
| marketing_segment | contents | midlife_mainstream | 1,0177 | 0,9777 | sí |
| marketing_segment | contents | senior_affluent | 0,9629 | 1,0248 | sí |
| marketing_segment | contents | senior_budget | 0,9771 | 1,0133 | sí |
| marketing_segment | contents | senior_mainstream | 0,9611 | 0,9389 | no |
| marketing_segment | contents | young_affluent | 0,9665 | 0,9910 | no |
| marketing_segment | contents | young_budget | 1,0733 | 1,0341 | no |
| marketing_segment | contents | young_mainstream | 1,0424 | 1,0835 | no |

Los parámetros privados guardan para cada nivel las filas, exposición y grupos positivos porNB/REN. Un factor cercano a 1 puede reflejar credibilidad escasa y no ausencia del efecto. La fórmula de n/(n +300) cuenta periodos con coste positivo, no todos los siniestros; se mantiene esa definición histórica y no se presenta como una estimación de frecuencia por siniestro.

## Concentración y perturbaciones comunes

| Exclusión común | Constante | Sin factores | Con factores | Δ factores |
| --- | --- | --- | --- | --- |
| remove_top_31 | 0,076248 | 0,127650 | 0,127864 | 0,000214 |
| remove_top_37 | 0,077498 | 0,129266 | 0,129270 | 0,000004 |
| remove_top1pct_positive_cost_periods | 0,047073 | 0,080987 | 0,082906 | 0,001919 |

Las tres recetas reciben exactamente las mismas exclusiones. Retirar los 37 grupos favorables deja una ganancia de 0,000004471: pasa el veto puntual≥0 por un margen mínimo y pierde casi toda la mejora. Retirar grupos elegidos después del resultado es diagnóstico, no validación. En cambio, las 100 retiradas aleatorias predeclaradas de 1% de componentes mantienen la diferencia positiva, entre 0,002146 y 0,002611. La fragilidad depende del mecanismo de perturbación y se informa en ambos sentidos.

## Conteo, severidad tardía y objetivo de coste

etiquetas.py construye curvas ponderadas por incurrido neto, no curvas de conteos. No hay que reinterpretar esa curva como completitud de frecuencia. Se separaron ambas y se conservaron los ceros de los siniestros aceptados. La siguiente tabla compara los ocurridos en 2023 reportados hasta la valoración 2024; tardío significa reportado después del 31 de diciembre 2023.

| Ramo | Peligro | Aceptados 2023 | Tardíos | Sev. tardía/temprana | Completitud conteo | Completitud coste |
| --- | --- | --- | --- | --- | --- | --- |
| buildings | accidental_damage | 55 | 0 | sin tardíos | 1,000 | 1,000 |
| buildings | escape_of_water | 131 | 12 | 1,11 | 0,908 | 0,899 |
| buildings | fire | 49 | 1 | 0,63 | 0,980 | 0,987 |
| buildings | flood | 42 | 0 | sin tardíos | 1,000 | 1,000 |
| buildings | storm | 210 | 17 | 1,83 | 0,919 | 0,861 |
| buildings | subsidence | 32 | 10 | 1,05 | 0,688 | 0,678 |
| contents | accidental_damage | 166 | 5 | 0,48 | 0,970 | 0,985 |
| contents | escape_of_water | 86 | 9 | 0,36 | 0,895 | 0,960 |
| contents | flood | 51 | 1 | 1,44 | 0,980 | 0,972 |
| contents | theft | 188 | 6 | 0,67 | 0,968 | 0,978 |
| motor | bodily_injury | 266 | 105 | 1,65 | 0,605 | 0,482 |
| motor | glass_hail | 601 | 15 | 0,98 | 0,975 | 0,976 |
| motor | own_damage | 1378 | 52 | 0,80 | 0,962 | 0,970 |
| motor | theft | 194 | 3 | 1,24 | 0,985 | 0,981 |
| motor | third_party_prop | 1120 | 61 | 0,86 | 0,946 | 0,953 |

Lesiones corporales tiene severidad tardía 1,645 veces la temprana y completitud de coste 0,482 frente a 0,605 de conteo. La misma fracción de avisos no implica la misma fracción de coste. Estas severidades son incurridas a una sola valoración; los abiertos aún pueden cambiar y los todavía no reportados no se observan.

| Escenario | Completitud media 2024 | D² con factores antes | Después overlay fijo | Δ frente sin factores antes |
| --- | --- | --- | --- | --- |
| count_curve | 0,8853 | 0,123533 | 0,126248 | 0,002388 |
| cost_curve_train_peril_mix | 0,8804 | 0,123655 | 0,126287 | 0,002392 |
| unreported_severity_x0.5 | 0,9155 | 0,122980 | 0,125891 | 0,002400 |
| unreported_severity_x1.5 | 0,8559 | 0,123813 | 0,126213 | 0,002387 |
| unreported_severity_x2.0 | 0,8367 | 0,123802 | 0,125998 | 0,002383 |

Las mezclas por peligro de estos escenarios se calculan solo en entrenamiento 2023; se conservan los árboles y la estructura de los precios. Se cambia la severidad de la porción no reportada a 0,5,1,5 y 2 veces y se compara conteo/coste, con y sin overlay público congelado. El overlay fijo no simula una nueva recalibración del marcador, de modo que su diferencia no mide cuánto absorberían realmente nuevas sondas.

La acotación anterior de Claude (src/semana2/lineas/reservas_20261026/INFORME.md) mantiene un resultado adverso de lesiones:1,427 veces el coste tardío previsto, IC90 [1,021;2,021]. Su estimador extrapola desde el coste temprano mediante completitudes integradas por exposición; el de reporting_count_cost condiciona en cada siniestro/coste observado hasta 2024. Los denominadores difieren. No se reemplaza aquella alarma con este contraste ni se lee uno como réplica del otro. FSp usa una exposición de frecuencia que debe revisarse por separado si su completitud procede de coste; F3c no incorpora FSp y F4c conserva ese requisito.

## Reservas por ramo y peligro, orden y compensaciones

Se calcularon 45 escenarios de respuesta con reservas 0,75/1,25 agregadas, por cada ramo y cada uno de 15 peligros, dos tensiones opuestas de lesiones/resto, severidad de tardíos observados y colas de lesiones/hundimiento. Se añaden 5 escenarios de completitud. Los tres modelos reciben el mismo escenario. Se miden precios congelados con objetivo estresado y niveles reaprendidos solo en 2023, además del overlay público fijo. No es un refit de todos los árboles o factores de forma bajo cada valoración.

| Escenario | Δ D² | Correlación rangos | Total 20 CU | Cambio individual % |
| --- | --- | --- | --- | --- |
| reserve 075 | 0,002291 | 0,999933 | 20205.51 | -4,42 a 0,00 |
| reserve 125 | 0,002486 | 0,999940 | 21394.51 | 0,00 a 4,42 |
| opposed_BI125_rest075 | 0,002401 | 0,999708 | 21104.91 | -2,02 a 4,41 |
| opposed_BI075_rest125 | 0,002379 | 0,999697 | 20495.12 | -4,41 a 2,02 |
| reserve_motor_bodily_injury_1.25 | 0,002444 | 0,999855 | 21249.73 | 0,00 a 4,42 |

Lesiones concentra 2.447.770,73 CU de reserva en los periodos enlazados. Los cambios opuestos producen compensaciones entre componentes que no se ven en un único total. Las correlaciones de rangos son altas porque aquí cambia el nivel por celda, no las relatividades dentro de ella; no acreditan estabilidad de un reentrenamiento completo. Los veinte precios con reserva±25% cambian hasta 4,43% individualmente. Los escenarios de severidad son más amplios y están identificados como tensiones, sin probabilidad asignada. La suficiencia real permanece abierta con una valoración.

## Auditoría de la cadena y dependencias

Se reconstruyó T0 con los siniestros originales y se cotejaron todas las 109.296 filas históricas con la base recibida, con error inferior a `1e-8` CU; suma 27.997.991,57 CU. Test conserva y nulo. Los 36 siniestros sin periodo se preservan aparte: 34 anteriores a 2023 y dos de 2023; 92.267,26 CU netos en conjunto. No se reasignaron claves ni se alteró la base para este contraste.

| Año | Componentes | Componentes partidos | Direcciones partidas | Filas afectadas |
| --- | --- | --- | --- | --- |
| 2023 | 30869 | 205 | 205 | 595 |
| 2024 | 36398 | 256 | 249 | 728 |

Los folds originales usan hash de cliente. Construir componentes cliente-dirección para el bootstrap no repara que el aprendizaje previo separase direcciones compartidas. El inventario estático también muestra: pesos de peligro de c_fila calculados con ambos años destino; diccionario de categorías construido con covariables fuente y destino completas; factores F2/F3c de producción aprendidos con 2023+2024; y razones de nivel evaluadas sobre pools usados para aprenderlos. La unión de categorías no usa etiquetas, pero es transductiva y no cumple una exigencia estricta de transformación aprendida solo en entrenamiento.

La nueva capa de factores y nivel sí pasó el control adverso: alterar completamente y retenido deja exactamente iguales parámetros aprendidos y precios, en los dos sentidos de traslado. Se reprodujeron también las primeras multiplicidades archivadas por otro cálculo fila a fila para los tres modelos y seis segmentos. Son comprobaciones propias. No cubren el reaprendizaje de ancestros T2b/A1, limpieza, completitud o selección de variables. El replay fuente de producción hasta 2024 no certifica automáticamente los objetos dev/hold cuyo código declara cortes hasta 2023.

## Exploración, disponibilidad y soporte futuro

El inventario congelado de recuperación contiene 500 documentos de registro y semana 2 con menciones a 2024. Guarda rutas, número de menciones y SHA; no pretende reconstruir cada lectura o decisión no registrada. La política v1, su fallo, la enmienda v2 y la autorización de desarrollo 2024 del 25 de octubre se conservan. Todas las cifras nuevas siguen siendo exploratorias. Bonferroni de esta familia no corrige retrospectivamente el proceso que eligió sus variables o el uso del público.

Se revisaron 142 perfiles de covariables. Las mayores alertas de PSI corresponden a exposición (2,43 autos, 2,15 edificios, 2,69 contenidos), coherentes con la sustitución de cartera corta por negocio nuevo de año completo. Son indicadores descriptivos sensibles a las bandas, no umbrales de validez actuarial.

| Ramo | Filas combinaciones nuevas | % exposición nueva | % exposición con <30 filas históricas |
| --- | --- | --- | --- |
| motor | 2019 | 2,49 | 71,31 |
| buildings | 236 | 0,48 | 29,24 |
| contents | 1291 | 2,13 | 62,12 |

Las combinaciones fijadas usan negocio, canal, año completo y dos campos del ramo. Con cinco campos se dispersan los históricos; estos porcentajes no prueban por sí solos que cada riesgo carezca de información. Sí identifican dónde falta evidencia cercana. Los maestros de cliente y dirección no tienen vigencia histórica por atributo; que género o marketing existan en la tabla no prueba que fueran conocidos al cotizar. El archivo de clima 2025 tampoco acredita conocimiento prospectivo.

La regla de contingencia queda escrita en el registro de uso: clave propia no vista recibe factor 1; si no se acredita disponibilidad/admisibilidad de los atributos propios, se neutraliza el bloque entero y su razón de nivel, recuperando final_creible. Si el riesgo base está fuera de soporte, se compara con constante por ramo/negocio y se exige revisión; no hay tarifa real aprobada automáticamente. La disponibilidad de variables de la base también sigue pendiente. El permiso del mercado sintético no se traslada como dictamen jurídico a una jurisdicción real.

## Reproducción: lo realizado y lo que sigue abierto

Se reutiliza la evidencia ya verificada del entorno limpio Python 3.12.14: etiquetas desde originales y factores F3c/F3d reaprendidos sobre OOF guardadas, ambos CSV idénticos por SHA. Esta tanda agrega cotejo por fila de las etiquetas. No se repitió aquel ensayo por una corrección documental ni se llamó reproducción integral a reconstruir desde OOF.

La auditoría guarda un grafo de nueve nodos. Se localizaron las fases T2b dev/hold/pcv/prod y sus semillas, preparación, historia y variables. A1 de contraste y A1fixF1b3n de producción tienen recetas distintas; el segundo requiere sus promedios de semillas 11/12/13, historia neutral, modelos y ensamblado exactos. El grafo portable de todos esos ancestros no está cerrado ni ejecutado desde cero. F4c necesita además sus tablas FSp originales exactas. No corresponde iniciar un entrenamiento parecido y llamarlo reproducción fiel.

La reproducción por otra persona tampoco se realizó. La plantilla de acta disponible no es una firma. La consecuencia es impedir las afirmaciones de reproducción integral e independiente hasta disponer del grafo ejecutable cerrado, entorno y versiones fuente exactas, semillas, comandos, salidas cotejadas y un operador real distinto cuando proceda. Es un requisito no cumplido, no una tarea declarada terminada por acumulación de comprobaciones parciales.

## Las veinte primas comerciales

| Candidato guardado | 85 CU por póliza | 85 × exposición previo | Referencias con cambio ≥10% vs F3c |
| --- | --- | --- | --- |
| F2 | 18.845,43 | 18.349,63 | 6 |
| F3c | 20.800,02 | 20.304,23 | 0 |
| F3d_no_admitido | 20.817,06 | 20.321,27 | 0 |
| F4c_no_reproducido | 20.766,16 | 20.270,38 | 0 |
| sin_factores_final_creible | 19.977,40 | 19.481,61 | 1 |

Se verificaron 2.100 registros para cada lectura de gasto, 4.200 en total, con veinte referencias en cada combinación de candidato y escenario. La revisión directa de la descripción oficial detectó una diferencia respecto al informe anterior: el concepto se denomina «fixed expense per policy», unidad CU. No consta que sea un gasto anual. La lectura principal de esta revisión cobra 85 CU por póliza de referencia y conserva el prorrateo 85×exposición como hipótesis alternativa. Las veinte referencias tienen policy_id distintos; no se está cobrando dos veces a una póliza repetida dentro de esta lista.

Con la lectura por póliza, F3c suma 20.800,02 CU de comerciales redondeadas y 20.800,018538 CU sin redondear; redondear esa suma da 20.800,02 CU. La lectura prorrateada anterior suma 20.304,23 CU. La diferencia agregada no revela el impacto en los periodos cortos: 3 referencias suben al menos 10% por esta sola interpretación de gasto y el máximo es 825,75%. No cambia su prima de riesgo, exposición, comisión o modelo.

La referencia sin factores suma 19.977,40 CU y una comercial cambia al menos 10% frente a F3c. Bajo el prorrateo previo eran dos. Se conservan ambas lecturas para que la convención de gasto no oculte incertidumbre del modelo. F3d y F4c siguen siendo sensibilidades guardadas, sin admisión; un total parecido no demuestra equivalencia.

La fórmula principal es `P = (R × (1 + cat) + 85) / (1 − 0,15 − comisión − 0,08 − 0,08)`. Catástrofes añade 0,12 de la prima de riesgo solo en hogar; la comisión es 0 para directo y 0,20 para broker. R ya corresponde al periodo y no se vuelve a multiplicar por exposición. Para comparar tasas anuales se divide R por exposición por separado. La comisión comparison_site está vacía para el emergente; ninguna de las veinte referencias usa ese canal y no se inventó una tasa.

Ambas lecturas pasan dos fórmulas Decimal, identidad de cargas y cotejo float. El cambio exacto de prima por corregir el gasto es `85 × (1 − exposición) / denominador`; se comprobó en las 2.100 filas. El supuesto de gasto debe declararse en la entrega: el archivo oficial no identifica cómo repartir un gasto de adquisición entre varios subperiodos de una misma póliza fuera de estas veinte referencias. La frase anterior que atribuía el prorrateo al contrato queda corregida por esta consulta directa.

El archivo privado VEINTE_PRIMAS_GASTO_POR_POLIZA.md identifica cada referencia, diferencia nominal y rango de escenarios. VEINTE_PRIMAS_COMPARADAS.md conserva el cálculo prorrateado anterior. Las reservas/completitudes se propagan mediante razones de nivel histórico por celda a precios guardados; no son un refit integral ni intervalos individuales. Los escenarios y el margen de beneficio del 8% se mantienen separados: ese margen es una entrada del ejercicio, no prueba que cubra incertidumbre.

## Archivos, verificación y consecuencia operativa

El plan es registro/pendientes_F3c_plan.json. El cálculo, sus parámetros y precios por fila, los cinco archivos de bootstrap y las veinte comerciales están en `Hackaton/Repositorio_IAA2026/privado/pendientes_F3c/20261026_cierre12_recuperado`. La auditoría está en `Hackaton/Repositorio_IAA2026/privado/pendientes_F3c/20261026_cierre12_auditoria`. La matriz estructurada guarda criterio previo, resultado, limitación y consecuencia para cada punto; el registro público no incluye primas ni identificadores por fila.

Dos fallos de implementación se conservaron: exigencia incorrecta de enlace total y precisión de exposición demasiado estricta. El segundo ocurrió después de guardar precios/parámetros y los intervalos; la recuperación reutiliza esos archivos por SHA, sin nuevas remuestras ni elección de semilla. Recalcula los niveles escalares de escenarios perdidos antes de persistir, con las mismas reglas. El comprobador posterior pasa 16 controles y otro cálculo reproduce multiplicidades y controles adversos; sigue siendo verificación propia.

No se entrena un nuevo árbol fuente, C0, hace una sonda, envía, promueve, retira una alternativa o cambia una selección manual. Se registra un bloqueo de admisión para las afirmaciones/uso que no satisfacen los criterios, con su evidencia de liberación. El informe anterior de sensibilidad de Claude y sus conclusiones quedan como corte histórico; esta revisión limita lo que puede afirmarse hoy sin atribuirle aprobación de otra persona. Prácticas aplicadas: IAA Consideraciones profesionales §§3.1,3.3,3.5–3.8; Gobernanza§2.8 y §§3.4–3.6; Documentación§§2–6, como guías educativas del proyecto.

## Actualización de reproducción al cerrar esta revisión

El estado común posterior a la auditoría registra un reentrenamiento completo ya iniciado en otro chat del participante, «Revisar pendientes del proyecto IAA». No se duplica esa ejecución ni se le atribuye a esta batería. El grafo de T2b/A1/M017/FSp está implementado en `herramientas/completar_reentrenamiento_cadena.py`, con guía `docs/REENTRENAMIENTO_ORIGINALES.md`, entorno nuevo y controles de aislamiento. La consulta de cierre lo encuentra en ejecución local: T2b completado, A1 en progreso, sin recibo final de todos los CSV. Dos restauraciones de código histórico están declaradas y requieren cotejo. Esto supera el diagnóstico inicial de grafo portable sin cerrar, pero aún no demuestra igualdad final de toda la cadena ni reproducción por otra persona. Se conserva el snapshot fechado en privado y el requisito 11 no se da por aprobado.

La puerta `herramientas/puerta_uso_F3c.py` verifica las huellas de este expediente y solo permite `research_review`. Rechaza promoción, cotización profesional, afirmación de reproducción integral y nuevo envío con código de salida 3. Se conservan los recibos del ensayo de las cinco finalidades. Es una consecuencia operativa para esta línea; no reemplaza autorizaciones humanas históricas ni es una barrera contra un operador que reescriba el código. El informe conjunto anterior conserva su corte; sus cifras comerciales prorrateadas no se deben presentar como la lectura principal de esta revisión. Su integración editorial queda identificada antes de otra entrega.
