# Técnicas por ramo a la luz de los datos: diagnóstico independiente y búsqueda de fuentes

Investigación de Claude a solicitud del participante, 16 de octubre de 2026 (America/Bogota). Complementa, y en varios puntos contrasta, la [investigación D37 de Codex](../Investigacion_tecnicas/INFORME.md) y la [metodología vigente](../METODOLOGIA_ACTUARIAL.md) (versión 1.3 con DUP01 cuando se ejecutó la corrida; al cerrar esta investigación el protocolo iba por la 1.5 con REN00 y PRE00, ver la sección 7). Todo lo cuantitativo sale de una corrida nueva de diagnósticos descriptivos sobre la capa preparada vigente; no se entrenó ningún modelo, no se materializó T0 operativo y no se modificó ningún dato. Las propuestas son hipótesis ordenadas por la evidencia, pendientes de la primera ronda de comparación y de revisión humana.

Evidencia: [runs/diag_20261016T210304Z_df57908a/evidencia.json](runs/diag_20261016T210304Z_df57908a/evidencia.json), con tablas CSV y figuras en la misma carpeta y el script [diagnosticos_tecnicas.py](diagnosticos_tecnicas.py) copiado dentro de la corrida. Fuentes nuevas: [fuentes.json](fuentes.json), 28 referencias verificadas contra Crossref, arXiv o la documentación oficial. Las referencias S01–S23 citadas abajo son las de D37.

## Lo que cambia respecto a lo ya documentado

La primera ola propuesta por D37 (tasa de referencia, GLM Tweedie y boosting Tweedie por ramo, después frecuencia–severidad y componentes por peligro) sigue siendo la correcta. Lo que esta revisión añade es evidencia de la propia cartera que decide varias dudas que D37 dejó abiertas y detecta un riesgo que ninguna decisión previa había cuantificado:

1. `customer_service_contacts` es, en la práctica, un indicador del siniestro del propio periodo. En autos, las filas con cero contactos tienen frecuencia 0,0003 por año-exposición y las de tres o más contactos 1,08, con el 85 % de esas filas siniestradas. Su D² one-way en muestra es 0,43 frente a un máximo de 0,04 para cualquier otra variable. Además su distribución en el test de 2025 es distinta: tres o más contactos aparecen en el 7,2 % de las filas de entrenamiento de autos y solo en el 0,8 % de las de test. Usarla como predictor es fuga en entrenamiento y cambio de distribución en inferencia. Debe quedar fuera de cualquier modelo de tarifa y documentarse como hallazgo de calidad y disponibilidad.
2. Los conteos de siniestros por periodo son casi Poisson una vez se tiene en cuenta la exposición: dispersión de Pearson con tasa constante 1,14 en autos, 1,05 en edificios y 1,03 en contenidos, y proporción de ceros observada apenas por encima de la que implica una Poisson de tasa constante (89,99 % frente a 89,42 % en autos). No hay inflación estructural de ceros que justifique un modelo zero-inflated o hurdle como primera opción; la heterogeneidad restante es pequeña y debería absorberla la especificación de tasas.
3. Dentro de cada peligro la severidad se parece a una gamma de forma cercana a uno (coeficiente de variación entre 1,0 y 1,3) con cola moderada (índice de Hill entre 2,8 y 4,5); la potencia Tweedie que implica una severidad gamma está entre 1,50 y 1,63. La excepción es lesiones corporales de autos: CV 6,5, índice de Hill 2,0 y un expediente de 11,9 millones CU. Al mezclar peligros, la cartera de cada ramo se comporta como si p fuese 1,85–1,99, y la ley de potencia varianza–media entre celdas da pendientes 2,06 (autos), 2,12 (edificios) y 1,89 (contenidos). Conviene comparar la potencia de ajuste 1,5 con otra más alta (1,8–1,9) manteniendo la evaluación en 1,5; y modelar lesiones aparte o con tratamiento de grandes siniestros.
4. No hay eventos catastróficos en los datos: los diez días con más siniestros de tormenta concentran el 2,1 % de los siniestros de tormenta y el máximo diario es de 20 expedientes; en inundación de edificios, el 2,6 % y un máximo de 9. La dependencia entre filas por eventos comunes es despreciable, lo que simplifica la validación y descarta modelos de catástrofe o de shock común.
5. El clima rezagado tiene tanta señal como el contemporáneo. La frecuencia de inundación en edificios se multiplica por 5,2 entre el decil más seco y el más lluvioso del año anterior, frente a 3,8 con la lluvia del mismo año; el viento rezagado ordena la tormenta (1,8 frente a 2,2 veces) y las heladas rezagadas el escape de agua (2,2 frente a 2,3), con correlaciones de Spearman entre decil y frecuencia de 0,87 a 1,00. El bloque F2 con años estrictamente anteriores al corte es legítimo y casi tan informativo como el clima realizado, que no estaría disponible al tarificar.
6. La historia propia conocida al inicio del periodo (siniestros de la misma póliza reportados antes de `period_start`) multiplica la frecuencia por 1,5 y 2,6 en autos, por 1,6 y 2,7 en edificios y por 1,6 y 2,3 en contenidos. La historia del cliente en otros ramos no aporta nada (D² one-way 0,0001 en autos, 0,0000 en edificios). Credibilidad o historia causal por póliza entran en la segunda ola; un modelo multirramo conjunto aporta poco.
7. La frecuencia es prácticamente plana entre 2021 y 2024 cuando se controla el truncamiento (ocurrencias de enero a septiembre reportadas en 60 días): 0,132, 0,135, 0,128 y 0,128 en autos. La caída de 2024 en la frecuencia bruta de autos (0,1295 frente a 0,1402 en 2023) es sobre todo IBNR de lesiones corporales y de los siniestros de diciembre. La severidad de hogar sí sube: la media de cerrados en edificios pasa de 8.686 a 9.001 CU entre 2021 y 2023 y la mediana de 2.835 a 3.103, entre 2 % y 5 % anuales según se mire la media o la mediana. Para 2025 hace falta una hipótesis explícita de tendencia con sensibilidades.
8. Todos los peligros salvo lesiones corporales y hundimiento se reportan en menos de 90 días en más del 98,6 % de los casos. El desarrollo pendiente (reserva de caso y no reportados) se concentra en esos dos componentes: en la cohorte 2024 siguen abiertos el 79,8 % de los expedientes de lesiones y el 68,7 % de hundimiento, frente a 17,1 % en daños propios. El tratamiento T1/T2 puede acotarse a esos dos peligros y a los siniestros de diciembre, sin un factor global por ramo.
9. La señal univariante es baja en toda la cartera: ninguna variable legítima supera 0,04 de D² one-way en muestra. Las que más explican son zona de inundación, elevación, distancia al río y capital en hogar, y bonificación, edad y antigüedad de licencia en autos. Es el perfil típico de una cartera de tarificación: los modelos aditivos regularizados compiten bien, el boosting aporta por interacciones y la diferencia entre familias será pequeña y sensible a los siniestros grandes.

El resto del documento desarrolla cada punto con sus cifras, conecta cada decisión con fuentes primarias y termina con una propuesta operativa por ramo y un orden de pruebas.

## 1. Datos, alcance y método

La corrida lee [current_dataset.json](../../Limpieza/current_dataset.json), que apunta al catálogo DUP01 (`dupfix_20261016T195843Z_fc0bb423`), comprueba el SHA-256 de las once tablas contra el catálogo y exige `verification.json` con `passed: true`. Se usan las seis tablas de pólizas y test con ID01, EXP01, CAP01, CAT01 y AGE01, los siniestros con DUP01 (162.546 registros) y los originales de clientes, direcciones, clima y plantilla. La comprobación de duplicados de D40 ya no encuentra ningún par idéntico salvo `claim_id`.

La asignación de siniestros a periodos usa la condición conjunta `policy_id`, ramo y `period_start <= loss_date <= period_end`. Resultado: 110.496 siniestros aceptados asignados de forma única en autos, 26.266 en edificios y 23.670 en contenidos (160.432 en total, igual que la conciliación de D42); no hay ninguno ambiguo ni sin póliza; 409 aceptados y 4 rechazados son anteriores al primer periodo observado de su póliza (293, 67 y 49 aceptados por ramo) y se dejan fuera del coste, como fija el protocolo. El coste neto que queda fuera por esa razón es 1,13 millones CU en autos, 0,43 en edificios y 0,16 en contenidos.

La proxy de coste por periodo es la del protocolo: `incurred_to_date - recoveries` de los aceptados asignados, cero cuando no hay siniestro. Se calcula en memoria para diagnosticar; no se escribe una tabla T0 operativa. Todas las relatividades y los D² one-way son estadísticas en muestra sobre el entrenamiento 2021–2024: miden señal, no rendimiento validado, y no sustituyen a V22/V23/V24.

| Ramo | Periodos | Años-exposición | Coste neto observado, CU | Prima de riesgo observada, CU por año | Frecuencia de aceptados por año | Periodos con coste cero |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Autos | 979.968 | 787.158 | 428.762.847 | 544,70 | 0,1404 | 89,99 % |
| Edificios | 707.726 | 590.560 | 246.656.437 | 417,67 | 0,0445 | 96,42 % |
| Contenidos | 721.617 | 590.859 | 65.737.585 | 111,26 | 0,0401 | 96,82 % |

Las cifras monetarias son incurridos netos al 31 de diciembre de 2024 e incluyen reservas de caso (14,0 % del incurrido en autos, 9,7 % en edificios, 4,0 % en contenidos). No son costes últimos.

## 2. Diagnósticos que condicionan la elección de técnicas

### 2.1 Estructura de los conteos: Poisson con exposición basta como punto de partida

| Ramo | Periodos con 1 siniestro | Con 2 | Con 3 o más | Ceros observados | Ceros que implica una Poisson de tasa constante | Dispersión de Pearson |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Autos | 8,92 % | 0,95 % | 0,14 % | 89,99 % | 89,42 % | 1,14 |
| Edificios | 3,46 % | 0,12 % | 0,01 % | 96,42 % | 96,36 % | 1,05 |
| Contenidos | 3,07 % | 0,10 % | 0,003 % | 96,82 % | 96,78 % | 1,03 |

La dispersión de Pearson compara la varianza de los conteos con la que tendría una Poisson de tasa constante por ramo; un valor de 1,14 con una sola tasa para toda la cartera de autos deja muy poco margen a una binomial negativa una vez que entren las covariables. Esto responde a la pregunta que D37 dejó condicionada: el modelo zero-inflated Tweedie (S15) o un hurdle no tienen apoyo descriptivo aquí; Tweedie compuesto o Poisson–gamma reproducen la masa de ceros por sí solos.

En autos, el producto cambia la frecuencia pero no el coste medio de forma monótona: `comprehensive` tiene frecuencia 0,156 y prima de riesgo 540 CU, `third_party_fire_theft` 0,074 y 494 CU, y `third_party_only` 0,066 y 635 CU. La prima más alta de terceros se explica por la mezcla de peligros: el cruce cobertura–peligro de los aceptados asignados muestra 0 cristales y 0 robos en `third_party_only`, 0 cristales en `third_party_fire_theft` y solo 4 daños propios fuera de `comprehensive` (los que D40 registró). La cobertura debe entrar como estructura contractual e interactuar con el peligro; un modelo por componentes de peligro con matriz de elegibilidad es más natural que un Tweedie único con `cover_type` como categoría más.

### 2.2 Severidad y colas por peligro

Severidades netas positivas de aceptados con ocurrencia 2021–2024, en CU:

| Ramo y peligro | Positivos | Media | Mediana | p99 | Máximo | CV | p Tweedie implícita por gamma | Hill, 5 % superior | Coste del 1 % mayor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Autos, lesiones corporales | 7.522 | 21.583 | 11.530 | 134.476 | 11.894.277 | 6,52 | 1,98 | 2,02 | 18,4 % |
| Autos, daños propios | 48.302 | 1.857 | 970 | 11.227 | 62.697 | 1,30 | 1,63 | 3,01 | 7,8 % |
| Autos, daños a terceros | 32.992 | 3.683 | 2.554 | 17.159 | 44.546 | 1,01 | 1,50 | 3,63 | 5,8 % |
| Autos, robo | 6.122 | 6.300 | 4.291 | 31.286 | 74.682 | 1,06 | 1,53 | 3,28 | 6,5 % |
| Autos, cristales/granizo | 15.655 | 1.087 | 746 | 5.084 | 9.736 | 1,02 | 1,51 | 3,69 | 5,8 % |
| Edificios, incendio | 1.107 | 51.773 | 28.604 | 315.594 | 631.246 | 1,31 | 1,63 | 3,85 | 8,3 % |
| Edificios, inundación | 2.221 | 31.328 | 20.749 | 162.123 | 352.282 | 1,11 | 1,55 | 2,85 | 7,3 % |
| Edificios, hundimiento | 1.290 | 23.802 | 16.600 | 115.309 | 207.875 | 1,04 | 1,52 | 3,88 | 6,1 % |
| Edificios, escape de agua | 10.075 | 5.734 | 3.743 | 29.592 | 66.585 | 1,09 | 1,54 | 3,26 | 6,6 % |
| Edificios, tormenta | 7.765 | 3.454 | 2.302 | 16.405 | 41.283 | 1,06 | 1,53 | 3,68 | 6,3 % |
| Edificios, daño accidental | 3.829 | 1.217 | 842 | 5.693 | 11.003 | 1,02 | 1,51 | 3,66 | 5,9 % |
| Contenidos, robo | 7.633 | 3.650 | 2.331 | 19.592 | 72.189 | 1,14 | 1,57 | 3,02 | 6,9 % |
| Contenidos, inundación | 1.615 | 9.979 | 6.242 | 47.549 | 111.900 | 1,11 | 1,55 | 3,55 | 7,0 % |
| Contenidos, escape de agua | 5.373 | 2.741 | 1.734 | 14.730 | 35.553 | 1,13 | 1,56 | 3,37 | 6,8 % |
| Contenidos, daño accidental | 9.069 | 782 | 512 | 4.469 | 9.851 | 1,09 | 1,54 | 3,08 | 6,5 % |
| Autos, todos los peligros | 110.593 | 3.880 | 1.531 | 35.667 | 11.894.277 | 9,58 | 1,99 | 1,63 | 20,9 % |
| Edificios, todos | 26.287 | 9.391 | 3.130 | 98.892 | 631.246 | 2,38 | 1,85 | 1,68 | 18,4 % |
| Contenidos, todos | 23.690 | 2.777 | 1.190 | 22.051 | 111.900 | 1,68 | 1,74 | 2,21 | 11,8 % |

Tres lecturas. Primera, dentro de cada peligro la severidad es casi exponencial-gamma: CV cercano a uno, y una lognormal ajustada por momentos del logaritmo sobreestima el p99 empírico entre 1,8 y 2,7 veces en todos los peligros (columna `lognormal_p99_over_empirical_p99` de la tabla CSV). Una severidad gamma con enlace log, o la Tweedie directa, es la especificación coherente; no hace falta una cola Pareto salvo en lesiones. Segunda, lesiones corporales es el único componente de cola pesada: índice de Hill 2,0 significa que la varianza apenas existe y que un solo expediente mueve el agregado; el máximo de 11,9 millones CU equivale al 2,8 % del coste total de autos. Esto afecta directamente a la métrica: la desviación Tweedie con p=1,5 no acota la influencia de un siniestro grande, así que el ranking del leaderboard público de 2025 tendrá un componente de azar ligado a pocas filas, y la selección debe apoyarse en V23/V24 y en la estabilidad por semillas y cortes, como fija la política D29. Tercera, la mezcla de peligros dentro de un ramo eleva la potencia implícita a 1,85–1,99: un Tweedie único por ramo con p=1,5 está mal especificado en varianza aunque siga siendo un estimador consistente de la media (C03). La solución más natural es modelar por componentes de peligro o, al menos, comparar potencias de ajuste.

La ley de potencia varianza–media entre celdas (periodos de año completo agrupados por año, región, producto o tipo de inmueble, bandas de edad o de capital; 619, 539 y 687 celdas con al menos 300 periodos) da pendientes 2,06, 2,12 y 1,89 con R² ponderado 0,69, 0,88 y 0,89 ([figura](runs/diag_20261016T210304Z_df57908a/figuras/fig_taylor_potencia.png)). La pendiente mezcla la función de varianza con la heterogeneidad no modelada, por lo que no es una estimación de máxima verosimilitud de p (C06); pero apunta en la misma dirección que la lectura por peligros. Propuesta concreta: en la primera ronda, ajustar cada familia con p=1,5 y con p=1,8 o 1,9 y evaluar siempre con D² a 1,5; en boosting, `tweedie_variance_power` es un hiperparámetro barato de recorrer (S20, S22).

### 2.3 Reporte, madurez y qué peligros necesitan desarrollo

| Peligro | Reportados en 90 días (cohorte 2021) | p90 del retraso, cohorte 2021, días | p90 del retraso, cohorte 2024 | Abiertos en la cohorte 2024 | Reserva de caso / incurrido, cohorte 2024 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Autos, lesiones corporales | 38,1 % | 426 | 198 | 79,8 % | 67,2 % |
| Autos, daños propios | 99,5 % | 24 | 23 | 17,1 % | 14,0 % |
| Autos, robo | 99,3 % | 12 | 12 | 16,1 % | 13,6 % |
| Edificios, hundimiento | 50,9 % | 260 | 159 | 68,7 % | 56,7 % |
| Edificios, incendio | 99,6 % | 11 | 13 | 42,1 % | 25,5 % |
| Edificios, inundación | 99,6 % | 22 | 24 | 36,6 % | 29,7 % |
| Edificios, escape de agua | 99,3 % | 36 | 32 | 26,5 % | 22,7 % |
| Edificios, tormenta | 99,6 % | 25 | 21 | 18,2 % | 14,7 % |
| Contenidos, robo | 99,6 % | 13 | 12 | 12,8 % | 10,3 % |
| Contenidos, escape de agua | 98,6 % | 34 | 34 | 17,0 % | 14,2 % |

La caída del p90 en 2024 es truncamiento al 30 de diciembre de 2024, no liquidación más rápida ([figura](runs/diag_20261016T210304Z_df57908a/figuras/fig_retraso_por_anio.png)). Fuera de lesiones y hundimiento, la distribución del retraso es corta y estable entre cohortes, así que los siniestros no reportados de 2024 se concentran en ocurrencias de noviembre y diciembre; un modelo de retraso truncado (C07, S17) es necesario solo para esos dos componentes, y para el resto basta una corrección de reporte por mes de ocurrencia estimada con las cohortes 2021–2023.

En las cohortes maduras de 2021–2022, el coste medio no depende del retraso de reporte en daños propios, terceros, escape de agua, inundación ni robo (las medias por banda de retraso se mueven menos del 10 %). En lesiones, los reportados después de 365 días cuestan 25.677 CU de media frente a 20.300–23.000 en las bandas cortas y tienen más abiertos. Completar conteos equivale aproximadamente a completar coste en los peligros cortos; en lesiones no, y hay que modelar la severidad de los tardíos o aplicar un factor específico. Esto delimita T2 con precisión.

Las reservas de caso de 2024 pesan en incendio (25,5 % del incurrido), inundación (29,7 %) y hundimiento (56,7 %) además de lesiones (67,2 %). La sensibilidad T1 con factores 0,75/1/1,25 debería aplicarse a esos cuatro componentes y no a toda la cartera.

### 2.4 Tendencia: frecuencia plana, severidad de hogar al alza

| Ramo | Frecuencia bruta 2021/22/23/24 | Frecuencia controlada por truncamiento (ene–sep, reportados en 60 días) | Media de cerrados 2021/22/23/24, CU | Mediana de cerrados, CU |
| --- | --- | --- | --- | --- |
| Autos | 0,1455 / 0,1467 / 0,1402 / 0,1295 | 0,1322 / 0,1346 / 0,1281 / 0,1276 | 3.670 / 3.574 / 3.259 / 2.813 | 1.403 / 1.462 / 1.487 / 1.399 |
| Edificios | 0,0440 / 0,0446 / 0,0455 / 0,0438 | 0,0421 / 0,0415 / 0,0411 / 0,0437 | 8.686 / 8.874 / 9.001 / 8.769 | 2.835 / 2.964 / 3.103 / 3.034 |
| Contenidos | 0,0396 / 0,0396 / 0,0411 / 0,0399 | 0,0392 / 0,0385 / 0,0406 / 0,0410 | 2.662 / 2.663 / 2.816 / 2.750 | 1.115 / 1.169 / 1.221 / 1.188 |

En autos hay una caída de frecuencia de alrededor de 5 % entre 2022 y 2023–2024 que sobrevive al control de truncamiento; en hogar no hay tendencia de frecuencia. La media de cerrados de autos cae en 2024 porque los cerrados recientes son los pequeños y rápidos (selección por madurez), no porque bajen los costes. En edificios y contenidos las medianas de cerrados suben entre 2 % y 5 % anual hasta 2023 y la media de todos los aceptados pasa de 8.725 a 10.250 CU entre 2021 y 2024 en edificios, cifra que mezcla inflación con reservas inmaduras. Para predecir 2025 hace falta un efecto de año o una tendencia declarada: la recomendación es estimar el nivel con 2021–2024, extrapolar 2025 bajo tres escenarios (sin tendencia, +3 % y +5 % en severidad de hogar) y elegir con V24 y balance, nunca con el leaderboard.

### 2.5 Eventos comunes y estacionalidad

Los diez días con más siniestros concentran el 2,1 % de los expedientes de tormenta de edificios (máximo 20 en un día, mediana 5), el 2,6 % de inundación de edificios (máximo 9), el 3,3 % de inundación de contenidos (máximo 7) y el 1,3 % de cristales/granizo de autos (máximo 21, mediana 11). El generador no produce tormentas que afecten a muchas pólizas a la vez; la dependencia entre filas por eventos es despreciable y, en el día de mayor frecuencia de cada peligro, ninguna región concentra más del 29 % de esos expedientes. Consecuencias: el remuestreo por cliente basta para medir incertidumbre, no hace falta modelo de shock común (C12 cubre el caso en que sí hubiera dependencia) y la validación por año no está distorsionada por un año catastrófico.

Sí hay estacionalidad en dos peligros de hogar: escape de agua y tormenta concentran 11–13 % de los siniestros en cada uno de diciembre, enero y febrero frente a 7 % en los meses restantes ([figura](runs/diag_20261016T210304Z_df57908a/figuras/fig_estacionalidad.png)); los demás peligros son planos. Para 2025, el 80–83 % de los periodos de test empiezan en enero, pero el 10–12 % dura un trimestre o menos; en periodos cortos de invierno la exposición efectiva a esos dos peligros es mayor que la exposición calendario. Una función de duración o un offset estacional es un experimento barato y justificado (S04, C15).

### 2.6 Señal de las variables por bloque

El D² one-way es la fracción de desviación Tweedie (p=1,5) que explica una tabla de una sola variable frente a la tasa constante por ramo, calculada en muestra; sirve para ordenar señales, no para predecir rendimiento ([figura](runs/diag_20261016T210304Z_df57908a/figuras/fig_oneway_d2_f0.png), [tabla completa](runs/diag_20261016T210304Z_df57908a/tables/oneway_d2_univariante.csv), [bandas](runs/diag_20261016T210304Z_df57908a/tables/oneway_bandas.csv)).

| Ramo | Variables contractuales y físicas (F0) con mayor D² one-way | Relatividad extrema |
| --- | --- | --- |
| Autos | `ncb_years` 0,027; `driver_age` 0,025; `years_licensed` 0,023; `annual_mileage` 0,008; `urban_density` 0,003; `renewal_count` 0,003; `region` 0,003; `vehicle_use` 0,003; `voluntary_excess` 0,002; `vehicle_value_group` 0,001 | NCB 0–1 años 1,89; 13–15 años 0,65 |
| Edificios | `flood_zone` 0,038; `elevation_m` 0,030; `distance_to_river_km` 0,023; `sum_insured` 0,014; `bedrooms` 0,008; `energy_rating` 0,005; `year_built` 0,005; `property_type` 0,004; `construction_type` 0,002 | Zonas 3–5 de inundación 3,56; elevación ≤ 1,8 m 2,52; capital decil superior 1,59 |
| Contenidos | `flood_zone` 0,029; `elevation_m` 0,023; `distance_to_river_km` 0,018; `sum_insured` 0,018; `tenure` 0,005; `region` 0,003; `policyholder_age` 0,003 | Zonas 3–5 de inundación 3,20; elevación ≤ 1,8 m 2,33; capital decil superior 1,69 |

Las variables de inundación son las más potentes de la cartera de hogar y se componen: la frecuencia de inundación en edificios por zona es 0,0004, 0,0017, 0,0069, 0,0251 y 0,0750 de la zona 1 a la 5, con prima de riesgo de inundación de 12 a 2.271 CU por año. La zona faltante (2,9 % de las filas) tiene frecuencia 0,0151, entre las zonas 3 y 4: la ausencia es informativa y debe entrar como categoría propia, nunca imputarse a la moda.

Los demás bloques:

| Bloque | Hallazgo | Decisión propuesta |
| --- | --- | --- |
| F1 historia propia de la póliza conocida al inicio | Frecuencia 0,129 / 0,195 / 0,338 con 0, 1 y 2+ siniestros previos en autos; 0,043 / 0,068 / 0,116 en edificios; 0,039 / 0,063 / 0,089 en contenidos. D² one-way 0,006, 0,004 y 0,003 | Entra en la segunda ola como conteo con contracción (credibilidad, C13, S03) o como variable del boosting; construir solo con `report_date < period_start` |
| F1 historia del cliente en otros ramos | D² 0,0001 o menor en los tres ramos; relatividades entre 0,89 y 1,48 con muy poca exposición | No priorizar; el cruce entre ramos no aporta |
| F2 clima del año anterior | D² sobre el coste total 0,001–0,002 porque los peligros climáticos pesan poco en el total, pero entre el decil más bajo y el más alto del clima del año anterior la frecuencia de inundación se multiplica por 5,2 (lluvia), la de tormenta por 1,8 (viento), la de escape de agua por 2,2 (heladas) y la de cristales/granizo de autos por 1,7 (días de granizo), con relaciones monótonas (Spearman 0,87 a 1,00) ([figura](runs/diag_20261016T210304Z_df57908a/figuras/fig_clima_rezago.png)) | Incluir el clima de años anteriores al corte como atributo climatológico de la dirección; el clima realizado del mismo año apenas añade |
| F3 operativos y de maestro | `customer_service_contacts` es post-siniestro (sección 2.7). `marketing_segment` 0,019 y `occupation` 0,009 en autos, `years_at_address` 0,003; `credit_band` 0,001; `prior_claims_5y` 0,001–0,002; `telematics_score` ordena la frecuencia de 0,195 a 0,128 entre los que optaron (12 % de la exposición) | `marketing_segment` necesita decidirse como proxy comercial (C18): es fuerte y probablemente derivado de siniestralidad; probarlo en ablación aparte. Telemática como bloque condicional con indicador de adhesión |
| F4 tarifario existente | `written_premium` explica 0,027 en autos, 0,049 en edificios y 0,022 en contenidos; sus deciles extremos van de 0,36 a 3,02 en edificios | La prima vigente ya incorpora inundación y capital. Usarla como predictor sería tarificar sobre la tarifa; una ablación con y sin F4 medirá cuánto de la señal ya la captura el tarifario actual |

### 2.7 Un predictor que no debe usarse: contactos con el servicio al cliente

| Contactos en el periodo | Autos: frecuencia por año | Autos: filas con siniestro | Autos: % de filas en entrenamiento | Autos: % en test 2025 | Edificios: % entrenamiento | Edificios: % test |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0,0003 | 0,02 % | 61,2 % | 67,0 % | 64,4 % | 66,9 % |
| 1 | 0,059 | 5,3 % | 23,8 % | 26,7 % | 25,7 % | 26,9 % |
| 2 | 0,379 | 33,5 % | 7,7 % | 5,4 % | 6,8 % | 5,4 % |
| 3 o más | 1,081 | 84,7 % | 7,2 % | 0,8 % | 3,2 % | 0,8 % |

Un periodo sin contactos prácticamente nunca tiene siniestro; cada siniestro genera contactos. En el test de 2025 la distribución se desplaza hacia pocos contactos, coherente con que los contactos de 2025 se generaron sin los siniestros de 2025 o con una ventana distinta. Un modelo que aprenda de esta variable predecirá costes casi nulos para la mayoría del test. Es un ejemplo claro de disponibilidad temporal (Consideraciones profesionales IAA §3.1 y Documentación §2): la variable existe en ambos ficheros, pero no describe lo mismo. Se recomienda excluirla de F0–F4, conservar el hallazgo en la ficha de datos y usarlo en el informe al jurado como evidencia de controles sobre la calidad de los datos. `missed_payments_12m` y `days_unoccupied` no muestran ni desplazamiento ni señal.

### 2.8 Duración, endosos y nuevo negocio

Frecuencia de aceptados por año-exposición según duración del periodo: en autos 0,158 para periodos de hasta un cuarto de año, 0,157, 0,155 y 0,155 para las bandas intermedias y 0,136 en periodos de año completo; en edificios 0,054 frente a 0,044; en contenidos 0,044 frente a 0,040 ([figura](runs/diag_20261016T210304Z_df57908a/figuras/fig_duracion.png)). Los periodos cortos no son neutrales: parte del efecto es nuevo negocio (frecuencia 0,189 frente a 0,136 en autos, prima de riesgo 721 frente a 529 CU) y parte puede ser una no proporcionalidad real. Los periodos con cambio a mitad de año no difieren de los demás (0,1396 frente a 0,1404). Es exactamente la situación que S04 y C15 estudian: comparar el offset puro `log(exposure)` con el offset más una función regularizada de duración, y mantener `new_business` y `renewal_count` en F0. En el test, el 59–64 % de los periodos son de año completo y el 10–12 % duran un cuarto o menos, así que la decisión importa.

### 2.9 Capital asegurado y ratio de daño

El coste medio de un siniestro positivo como fracción del capital (filas con capital por debajo de los umbrales de cribado) es, en edificios, 13,3 % en incendio (p90 55 %, p99 cercano al 100 %), 9,2 % en inundación (p90 32 %), 7,4 % en hundimiento, 1,7 % en escape de agua y 1,0 % en tormenta; en contenidos, 16,7 % en inundación (p90 59 %) y 4,5 % en escape de agua. La severidad escala con el capital en los peligros de pérdida total y mucho menos en los de daño parcial. Modelar la severidad de incendio e inundación como fracción del capital, o con `log(sum_insured)` y pendiente cercana a uno, es más estable que un término libre. Los 593 periodos de edificios y 671 de contenidos con capital por encima del umbral (98 y 92 en test) siguen siendo los 1.454 pendientes de D36: cualquier especificación con `log(sum_insured)` debe acotarse o evaluarse con y sin ellos.

### 2.10 Categorías, faltantes y perfil del test

No hay ningún nivel de variable categórica en el test que no exista en entrenamiento. `make_model` tiene 300 niveles con participación máxima del 0,37 %: es la única categoría de alta cardinalidad y pide codificación regularizada (target encoding dentro del fold, efectos aleatorios o el tratamiento ordenado de CatBoost) en lugar de 300 indicadores libres. Los faltantes están alrededor del 2,5 % en `smoke_alarms`, `security_level` y `overnight_parking`, y del 2,9 % en `flood_zone`, donde la ausencia es informativa. El test de 2025 tiene un 15,2 % de nuevo negocio y un 84,8 % de pólizas ya observadas, coincide con la mezcla de los cortes históricos y empieza en enero en el 80–83 % de las filas.

## 3. Qué dice la literatura y cómo encaja con esta cartera

### 3.1 GLM y GAM Tweedie, balance y recalibración

El GLM Tweedie con enlace log y `log(exposure)` como offset sigue siendo la referencia profesional (C24, C22, C23, S01). Con una señal univariante máxima de 0,04 y relaciones monótonas suaves (capital, elevación, NCB, edad), un GAM con splines penalizados o un GLM con bandas e interacciones seleccionadas debería quedar cerca del boosting; la diferencia la marcarán las interacciones cobertura–peligro en autos y zona–elevación–capital en hogar. En Python el proyecto no tiene una librería GAM instalada: `glum` (C25) ofrece GLM Tweedie con offsets, pesos y regularización L1/L2 con validación cruzada del camino; `TweedieRegressor` de scikit-learn (C26) admite `power` en (1, 2) y `sample_weight` pero no offset, por lo que el ajuste con exposición requiere modelar tasas con peso `sqrt(e)` para reproducir la desviación en importes (identidad de homogeneidad de la metodología) o peso `e` como sensibilidad; la EBM de InterpretML (C27) es un GAM por boosting con interacciones por pares y `objective="tweedie_deviance:variance_power=1.5"`, útil como modelo interpretable intermedio aunque no documenta offset.

Los modelos ajustados por desviación Tweedie no garantizan balance por segmento; Denuit, Charpentier y Trufin (C01) proponen la autocalibración como paso local posterior y el orden convexo para comparar modelos, y Wüthrich y Ziegel (C02) muestran que la recalibración isotónica produce tarifas simples cuando la señal es baja, como aquí. Lindholm, Lindskog y Palmquist (C15) ajustan el sesgo local de modelos flexibles y construyen celdas tarifarias automáticamente. Para redes, el balance se pierde y hay que restaurarlo (C16). Todo esto se aplica en la mitad de calibración de V23 y se evalúa en la de selección, como ya fija el protocolo.

Para comparar modelos, la desviación Tweedie de cualquier potencia es una función de puntuación consistente para la media (C03): elegir p=1,9 para ajustar no cambia el objetivo, solo la ponderación de los residuos; y las curvas de concentración y el Gini (C17) complementan al D² para medir ordenación.

### 3.2 Frecuencia–severidad frente a Tweedie directo

Delong, Lindholm y Wüthrich (C05) muestran cómo el Tweedie compuesto se relaciona con una frecuencia Poisson y una severidad gamma con parámetros separados, y cómo estimar la potencia; Smyth y Jørgensen (C06) estiman p y la dispersión por máxima verosimilitud. Nuestros diagnósticos (CV ≈ 1 dentro de peligro, p implícita 1,50–1,63) indican que el Tweedie por peligro y la Poisson–gamma por peligro serán casi equivalentes; la descomposición gana valor en lesiones corporales, donde frecuencia y severidad tienen dinámicas distintas, y en los componentes con reservas. La dependencia entre frecuencia y severidad (C11, C12) puede comprobarse en la primera ronda comparando la severidad media de periodos con uno y con dos siniestros.

### 3.3 Boosting Tweedie, offsets y restricciones

LightGBM, XGBoost y CatBoost admiten pérdidas Tweedie (S20–S22); `HistGradientBoostingRegressor` de scikit-learn no (C26), aunque sí Poisson y gamma con `monotonic_cst` y `categorical_features`, lo que permite una variante frecuencia–severidad nativa en el entorno ya instalado. El offset de exposición entra como `init_score` en LightGBM (C28) o `base_margin` en XGBoost (S21), en escala del enlace, y debe sumarse manualmente al predecir. Henckaerts y colaboradores (C04) comparan GLM y GBM en frecuencia–severidad de autos y usan modelos sustitutos para traducir el GBM a una tarifa; Lee y Lin (C14) diseñan un boosting específico para pérdidas actuariales. Las restricciones monótonas tienen sentido en NCB, años de licencia, zona de inundación y elevación; la EBM recomienda aplicarlas después del ajuste con `monotonize` porque el boosting puede compensar una restricción con una variable correlacionada (C27).

### 3.4 Credibilidad, GLMM y categorías de alta cardinalidad

La historia propia de la póliza y `make_model` son los dos lugares donde la contracción aporta: GLMM o Bühlmann–Straub (C13, S03) como referencia actuarial, y target encoding dentro del fold o efectos ordenados de CatBoost como equivalentes prácticos en boosting. La ausencia de señal de la historia de otros ramos y la débil dependencia entre ramos (lift 1,12–1,17) aconsejan modelos separados por ramo con variables compartidas, no un modelo multirramo conjunto.

### 3.5 Grandes siniestros y colas

Solo lesiones corporales (y, en menor medida, incendio) justifican un tratamiento de cola: el splicing con cuerpo Erlang mixto y cola de valores extremos (C10) permite estimar la media de la severidad con una cola paramétrica estable y evaluar la sensibilidad a un umbral. Para la primera ronda basta con dos sensibilidades: incluir todo y acotar los siniestros de lesiones por encima de un umbral alto (por ejemplo p99,9) redistribuyendo el exceso como carga uniforme sobre el componente; ambas se evalúan con la etiqueta completa.

### 3.6 Reporte, IBNR y reservas

Verbelen, Antonio, Claeskens y Crevecoeur (C07) modelan ocurrencias con retraso truncado mediante EM; Bücher y Rosenstock (C08) predicen conteos pendientes a nivel micro con covariables; Crevecoeur, Robben y Antonio (C09) organizan las reservas de reportados por capas. Aquí la aplicación es acotada: un modelo de retraso para lesiones y hundimiento, una corrección de reporte por mes de ocurrencia para el resto y una sensibilidad de reserva en lesiones, hundimiento, incendio e inundación. Sin trayectorias de pagos no hay triángulo que ajustar (S16, S17 y la metodología ya lo advierten).

### 3.7 Redes e híbridos

CANN, LocalGLMnet, ANAM, Credibility Transformer, TabM y DRN (S05–S12) siguen en la tercera ola. Con la señal observada y sin dependencia espacial ni eventos, la ganancia esperable frente a GLM más boosting es pequeña y deberá demostrarse en V24 con varias semillas; ICEnet (C19) y la EBM ofrecen restricciones de forma y curvas explicables que encajan con la rúbrica de confianza y documentación. SHAP (C20, C21) sirve para explicar la salida real, con la cautela de que explica predicción y no causalidad.

### 3.8 Proxies y práctica profesional

`marketing_segment`, `occupation`, `marital_status`, `credit_band` y `previous_insurer` tienen señal y son proxies comerciales o sociodemográficos. Lindholm, Richman, Tsanakas y Wüthrich (C18) formalizan la tarificación libre de discriminación indirecta; aunque el territorio es ficticio y no hay jurisdicción, la decisión de usarlos o no debe ser explícita, con ablación, y explicada al jurado como consideración profesional (IAA Consideraciones profesionales §3.3).

## 4. Propuesta por ramo

### Autos

Primera ronda con tres especificaciones sobre F0 (cobertura, franquicias, exposición, conductor, vehículo, uso, kilometraje, estacionamiento, región y densidad), más `new_business` y `renewal_count`: tasa constante por producto; GLM Tweedie con `cover_type` interactuando con las curvas de edad, licencia, NCB y valor; LightGBM y CatBoost Tweedie con offset de exposición. Segunda ronda: componentes por peligro con matriz de elegibilidad (cristales y robo solo donde el producto los cubre), Poisson–gamma por componente y lesiones separadas con sensibilidad de cola y de reservas; historia propia de la póliza con contracción; función de duración; potencia de ajuste 1,9. `telematics_score` y `marketing_segment` entran solo en ablaciones etiquetadas. `customer_service_contacts` queda fuera.

### Edificios

Primera ronda sobre F0 ampliado con las variables físicas de la dirección (zona de inundación con categoría de ausencia, elevación, distancia al río, suelo, antigüedad, tipo, habitaciones, eficiencia) y el clima rezagado: GLM Tweedie con `log(sum_insured)` suave, zona–elevación como interacción explícita y estacionalidad de invierno; boosting Tweedie con las mismas entradas. Segunda ronda: componentes por peligro (agua, tormenta, inundación, incendio, hundimiento, accidental) con severidad de incendio e inundación como fracción del capital, hundimiento con reserva y retraso propios, y sensibilidad con y sin los 593 capitales pendientes. El tarifario vigente solo en ablación.

### Contenidos

Es el ramo más limpio para comparar algoritmos: reservas del 4 %, retrasos cortos, sin cola pesada, señal concentrada en inundación, elevación, capital y tenencia. Primera ronda: GLM Tweedie con `log(sum_insured)`, zona–elevación e indicadores de seguridad, frente a boosting. Segunda: robo, agua, inundación y accidental por separado con información de edificios de la misma dirección solo como atributo físico (no como siniestros del mismo periodo). Es el candidato natural para probar primero la recalibración isotónica y la EBM, porque sus resultados serán menos ruidosos.

## 5. Orden de pruebas y criterios de decisión

| Paso | Qué se compara | Qué decide |
| --- | --- | --- |
| 0 | Asignación, T0 con componentes, F0 con contrato de disponibilidad que excluya `customer_service_contacts`, particiones V22/V23/V24 persistentes | Requisito previo; nada de lo anterior es un resultado |
| 1 | M00 tasa constante, M01 GLM Tweedie, M04–M06 boosting Tweedie, con p=1,5 y p=1,9 | Cuánto aportan las no linealidades y si la potencia de ajuste importa |
| 2 | Componentes por peligro frente a ramo completo; Poisson–gamma frente a Tweedie; duración; historia propia con contracción | Qué estructura mejora de forma estable en V23 selección y V24 |
| 3 | Calibración: sin ajustar, balance, factor Tweedie, isotónica (C02) y autocalibración local (C01); sensibilidad T1 en lesiones, hundimiento, incendio e inundación; corrección de reporte de noviembre–diciembre; tendencia 0/+3/+5 % en hogar | Elección del candidato para 2025 y de sus supuestos declarados |
| 4 | EBM o GAM interpretable como sustituto; SHAP del candidato; ablaciones F3 y F4 | Explicación y decisiones de proxies para el informe |
| 5 | Mezcla convexa de los dos mejores por ramo | Solo si hay complementariedad de errores en V24 |

Criterio de mejora: diferencias de desviación sobre las mismas filas, con remuestreo por cliente y al menos tres semillas en boosting; una ganancia que desaparece al retirar el 0,1 % de periodos más costosos no es una ganancia. La selección final sigue D29.

Candidatos nuevos que convendría añadir al catálogo cuando el participante lo decida: EBM con interacciones por pares como GAM interpretable (C27); Poisson y gamma nativos de `HistGradientBoostingRegressor` como frecuencia–severidad sin dependencias nuevas (C26); recalibración isotónica (C02) y autocalibración local (C01) como etapas de calibración; splicing de severidad para lesiones (C10); corrección de reporte por mes de ocurrencia como alternativa simple a T2 completa.

## 6. Riesgos y controles

| Riesgo | Evidencia | Control |
| --- | --- | --- |
| Fuga por `customer_service_contacts` y cambio de distribución en test | Sección 2.7 | Exclusión por contrato de disponibilidad aplicado por código; prueba automática que falle si la variable entra en X |
| Un siniestro de lesiones domina el score | Máximo 11,9 millones CU, Hill 2,0 | Sensibilidad con y sin extremos; selección por V24 y no por el leaderboard público |
| IBNR y reservas inmaduras de 2024 en V24 | 79,8 % de lesiones y 68,7 % de hundimiento abiertos | Evaluar V24 con y sin esos componentes; declarar la valoración posterior |
| Capitales extremos pendientes | 593 y 671 periodos | Variante con `log(sum_insured)` acotado; sensibilidad con y sin ellos |
| Proxies comerciales | `marketing_segment` D² 0,019 en autos | Decisión explícita y ablación documentada |
| Día omitido del 31-12-2024 y exposición | D43 | Usar EXP01 como base; sensibilidad CAL00 si se confirma |

## 7. Reproducción, verificación y límites

Desde `C:\dev\Hakaton`, con el entorno de Preparación:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Modelado\Investigacion_tecnicas_claude\diagnosticos_tecnicas.py'
& '.\Preparación\.venv\Scripts\python.exe' '.\Hackaton\Semana 1\Modelado\Investigacion_tecnicas_claude\verificar_entrega.py'
```

Cada ejecución crea una carpeta nueva en `runs/` con el script copiado, `evidencia.json`, tablas, figuras y `manifest.json` con hashes; `current_run.json` identifica la corrida revisada y no cambia al repetir el comando. La corrida de este informe se ejecutó en el espacio de trabajo en la nube de Claude con Python 3.13, pandas 3.0.5 y PyArrow 26.0.0 sobre copias de los Parquet verificadas por SHA-256 contra el catálogo DUP01; repetirla en Windows con pandas 3.0.1 debería dar las mismas cifras salvo diferencias de redondeo en la última cifra decimal. `verificar_entrega.py` comprueba los hashes del catálogo, el manifiesto de la corrida, que las cifras citadas en este informe coincidan con `evidencia.json` y que los enlaces locales existan; es verificación propia asistida por IA, no revisión independiente.

Durante la redacción, D45 y D47 publicaron las capas REN00 y PRE00 y el catálogo activo pasó a `preaudit_20261016T211816Z_817285a5`. Esas capas solo añaden las columnas de auditoría `audit_ren00` (seis tablas de pólizas y test) y `audit_pre00` (siniestros) y no cambian ningún valor previo, así que las cifras de esta corrida siguen describiendo la capa vigente; `verificar_entrega.py` acepta ese linaje (hash igual, o `parent_sha256`/`audit_parent_sha256` igual con cero cambios de valores) y pasó 11 de 11 controles con el catálogo PRE00 activo. Los 413 expedientes anteriores al primer periodo que aquí quedan fuera del coste (296 de autos, 67 de edificios y 50 de contenidos, con 1.721.459,84 CU de neto aceptado) son los mismos que PRE00 marca y concilia en el [informe de D47](../../Limpieza/runs/preaudit_20261016T211816Z_817285a5/informe.html). Las columnas `audit_*` y `renewal_decision` ya quedan fuera de los predictores por `iaa_lab.predictor_guard` (D45); la propuesta de esta revisión es tratar `customer_service_contacts` de la misma forma, con razón explícita y prueba automática, cuando el participante lo decida.

Límites: no se entrenó ningún modelo, por lo que ningún orden entre familias está medido; los D² one-way son en muestra; la asignación y la proxy de coste se calcularon en memoria y no sustituyen a la tabla T0 operativa; los índices de Hill con pocos excesos (hundimiento, incendio al 2 %) no se calcularon; no se consultaron notebooks ni discusiones de la competición porque la sesión no tenía acceso a buscadores ni a Kaggle. La aplicación de métodos, los supuestos de último y la elección final siguen sujetos a revisión humana. Los datos originales permanecen intactos; no hubo proveedores externos, envíos, publicación ni delegación.
