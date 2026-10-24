# Calibración de B20 en bandas definidas con el ajuste

Codex, corte UTC 2026-10-24T02:47:09.026808+00:00. Se revisaron los mismos 50.094 periodos OOF de 2023. El A/E global de B20 es 1,011, pero el equilibrio agregado oculta diferencias por banda. La regularización modera varios extremos de B19 sin producir una mejora uniforme de calibración. No se ha reentrenado, recalibrado o promovido un modelo.

## Cómo se fijaron las bandas

Se reproduce la tasa anual nominal con cada uno de los quince estimadores B20 guardados, exclusivamente en las filas que lo ajustaron. Para cada ramo y fold se fijan los quintiles 20, 40, 60 y 80 de esa tasa, con la inversa empírica sin interpolación. El objetivo T0 y las etiquetas retenidas no eligen cortes. Las filas OOF se asignan después por su tasa B20 ya guardada.

La banda inferior incluye su límite superior; las siguientes son abiertas por abajo y cerradas por arriba. Se conservan cortes repetidos, empates y bandas vacías, sin desempatar por ID ni alterar el número de bandas. En este cálculo los quince conjuntos tienen cuatro cortes distintos. Las bandas representan posición relativa dentro del ajuste de cada ramo/fold; no son intervalos absolutos comunes de precio.

B19 se resume sobre las mismas filas y bandas definidas por B20. Así se comparan poblaciones iguales. El A/E es suma de T0 observado dividida por suma de predicción observada con C0, no media de cocientes por póliza ni coste dividido por tasa anual sin exposición. Valores superiores a uno indican más T0 observado que esperado bajo ese vínculo; no prueban insuficiencia de último.

## Calibración fuera de muestra

| Ramo | Banda 1, menor tasa | Banda 2 | Banda 3 | Banda 4 | Banda 5, mayor tasa |
| --- | ---: | ---: | ---: | ---: | ---: |
| Autos | 1,082 | 0,861 | 1,038 | 1,019 | 0,981 |
| Edificios | 1,966 | 1,563 | 0,856 | 1,198 | 0,714 |
| Contenidos | 1,226 | 1,175 | 0,759 | 1,444 | 0,789 |

El global es 1,011 para B20 y 0,991 para B19. Su proximidad a uno no implica que las bandas estén calibradas. En edificios, B19 pasa de A/E 2,232 a 1,966 con B20 en la banda inferior y de 0,644 a 0,714 en la superior: se moderan esos dos extremos. En las bandas intermedias 3 y 4 las desviaciones respecto a uno empeoran. En autos, la banda 5 se acerca de 0,840 a 0,981, mientras la banda 2 se aleja de 0,905 a 0,861.

Contenidos mantiene una forma irregular: las bandas 3 y 5 quedan por debajo de uno, y la 4 por encima. Son diagnósticos de forma y nivel sobre 2023 ya usado adaptativamente. No se transforma este perfil en una curva de calibración, prueba de monotonía o justificación de una familia más compleja.

## Soporte y concentración del coste

| Ramo y banda | Periodos OOF | Periodos con T0 positivo | Mayor componente, % del T0 | Grupos equivalentes por concentración |
| --- | ---: | ---: | ---: | ---: |
| Edificios, 1 | 2525 | 69 | 31,65 | 6,09 |
| Edificios, 5 | 2530 | 124 | 19,02 | 14,16 |
| Contenidos, 1 | 3179 | 97 | 7,67 | 34,40 |
| Contenidos, 5 | 3155 | 110 | 8,25 | 38,59 |
| Autos, 1 | 4365 | 410 | 5,37 | 80,57 |
| Autos, 5 | 4329 | 766 | 5,74 | 110,78 |

Los grupos equivalentes se calculan como (suma de coste por grupo)²/suma de costes de grupo². Describen cuánto se concentra el importe; no son tamaño muestral efectivo para un intervalo de confianza. Los conteos de grupos tampoco se suman entre bandas o ramos, pues un componente puede tener varios periodos.

En autos nuevos, la banda 1 no contiene filas y su A/E queda indefinido. La banda 2 contiene trece periodos y dos positivos, con A/E 11,991; la banda 3 tiene 104 periodos y seis positivos, con A/E 6,786. Un componente reúne el 93,91% del coste de esta última celda. El grueso del nuevo negocio de autos queda en la banda 5: 2.145 periodos, 232 positivos y A/E 0,823. Las bandas se fijaron por ramo, no se vuelven a dividir dentro de nuevo negocio para llenar celdas.

En nuevo negocio de edificios solo hay de seis a nueve periodos positivos por banda; en contenidos, de cuatro a diez. Los extremos observados no proporcionan una base estable para cinco factores comerciales o una regla distinta por banda. No se eliminan siniestros o componentes para suavizarlos.

## Variación entre folds y alcance del ajuste

| Ramo y banda | A/E mínimo entre folds | A/E máximo | Folds por encima / debajo de uno |
| --- | ---: | ---: | ---: |
| Autos, 1 | 0,710 | 1,897 | 2 / 3 |
| Autos, 5 | 0,750 | 1,354 | 2 / 3 |
| Edificios, 1 | 0,342 | 3,457 | 4 / 1 |
| Edificios, 5 | 0,285 | 1,153 | 2 / 3 |
| Contenidos, 1 | 0,653 | 1,646 | 4 / 1 |
| Contenidos, 5 | 0,545 | 1,134 | 2 / 3 |

Los ajustes comparten cuatro de cinco folds y las tablas comparten componentes; esos rangos no son intervalos de confianza ni cinco réplicas independientes. En edificios, incluso las bandas extremas cambian de lado respecto a uno entre folds. La banda 1 llega a tener un componente con 91,82% del coste dentro de un fold. Se conserva el diagnóstico, sin convertir su punto agrupado en una corrección cierta.

Se encontraron cuatro tasas OOF fuera del rango mínimo/máximo de sus filas de ajuste: dos de edificios, una de contenidos y una de autos. Se conservan marcadas; no se recortan las tasas ni cambian los cortes. Pertenecer a una banda extrema no garantiza soporte de entrenamiento para cualquier tasa.

El replay de las filas de ajuste suma 200.376 apariciones, porque cada periodo participa en cuatro modelos. Son 50.094 periodos originales, no cuatro muestras nuevas. La calibración de entrenamiento es descriptiva. El máximo score normalizado del intercepto es 0,00000187, y el A/E de ajuste por modelo recorre 0,9873 a 1,0417. El óptimo del intercepto Tweedie impone una suma ponderada de residuos, no igualdad exacta de sumas observada y esperada. No se normaliza el nivel para forzar uno.

## Verificación y decisión

Pasaron 2121 comprobaciones separadas y 21 adversos, con solapamiento entre controles. La revisión usa un predictor exp(Xβ) con indicadores manuales, estadísticas de orden de Python y bisect para los cortes, y math.fsum/diccionarios para importes, grupos y concentración. Contrasta la partición completa por banda, los originales T0/C0, las mismas filas de ambos modelos y el carácter exclusivo de las filas de ajuste. Las etiquetas e IDs alterados no cambian cortes; empates, celdas vacías y año/test inválidos se tratan según el contrato. Dos comandos nativos rechazan fuente alterada y repetición antes de producir trabajo nuevo. Fit estuvo bloqueado.

Se mantiene B00 como referencia y B01–B20 como alternativas. No hay factores por banda, isotónica, búsqueda de alpha, variables/interacciones nuevas o enrutamiento de modelos. El diagnóstico confirma que la calibración agregada oculta heterogeneidad y soporte escaso; no demuestra una corrección validada ni exige aumentar complejidad. Corresponde consolidar esta evidencia con contracción y atribución, manteniendo la incertidumbre de último, reservas, reporte y capital.

Cero ajustes nuevos, nuevas recetas, remuestreos o precios de 2024/test. Se hicieron quince inferencias sobre filas de ajuste con estimadores guardados, sin volver a estimar transformaciones o parámetros. El contador permanece en 195 ajustes de precio y 285 constantes. 2024, test, actas, scores y ledger siguen cerrados para este trabajo; la exposición previa del título ajeno queda declarada sin usar sus cifras o afirmar ceguera completa. Revisión propia de Codex, no profesional independiente. Sin remoto, envíos, delegación, publicación externa o cambios a otras automatizaciones.

[Plan previo](../../registro/semana2_b20_bandas_calibracion_plan_v1.json), [índice](../../registro/semana2_b20_bandas_calibracion_actual.json), [productor](../../src/semana2/revisar_calibracion_b20_bandas2023.py), [comprobador separado](../../herramientas/verificar_calibracion_b20_bandas2023.py) y [adversos](../../herramientas/probar_calibracion_b20_bandas2023.py). Cortes exactos, replay de ajuste, asignaciones OOF y todas las celdas quedan en `privado/semana2/desarrollo2023/b20_bandas_calibracion_20261024_v1`, fuera de Git. La ficha del modelo y la distinción de revisión propia siguen Documentación IAA §3 y Gobernanza §2.8.
