# Resultado del ensayo de severidad compartida

El modelo se pudo entrenar, pero no aporta una mejora con la regla de combinación acordada. Las seis cabezas Gamma están guardadas. El peso elegido exclusivamente con la mitad de calibración de 2023 fue cero, por lo que el candidato resultante conserva exactamente las predicciones de S30. El ensayo queda retenido y no sustituye el modelo actual.

El participante autorizó comprobar los insumos, entrenar si era viable y comparar con los criterios definidos, conservando S30 y sin enviar a Kaggle hasta revisar los resultados. No se prepararon nuevas predicciones de 2025 ni se hizo un envío.

## Corrección del diseño antes de entrenar

La propuesta inicial incluía una cabeza binaria para la probabilidad de coste positivo. La auditoría encontró que `n_p` de F0 ya cuenta siniestros positivos y que las frecuencias guardadas modelan ese conteo. Multiplicar otra probabilidad de positividad duplicaría el ajuste. Antes de ajustar las cabezas nuevas se registró una enmienda: conservar la frecuencia positiva y estimar únicamente la severidad positiva compartida entre los peligros de cada ramo.

Se conciliaron los siniestros aceptados asignados de forma única con los conteos y costes por fila de F0. Pasaron 39 controles: 160.432 siniestros aceptados, de los que 160.431 tienen coste positivo. El coste es incurrido menos recuperaciones. No se restaron franquicias de nuevo ni se añadió IBNR. Esto comprueba las etiquetas del ensayo; no acredita el coste último o la suficiencia de las reservas.

## Modelo ajustado

Se entrenó una cabeza Gamma por ramo y corte, con todos sus peligros agrupados y el peligro como variable categórica. El objetivo es el coste positivo individual dividido por la media positiva del peligro, calculada solo en entrenamiento. Cada siniestro pesa uno. La credibilidad conserva la regla fijada: N positivo / (N positivo + 1.000).

| Ramo | Siniestros positivos hasta 2022 | Siniestros positivos hasta 2023 |
| --- | ---: | ---: |
| Autos | 56.642 | 84.631 |
| Edificios | 12.878 | 19.695 |
| Contenidos | 11.524 | 17.682 |

Cada cabeza tiene 500 rondas, hasta siete hojas y profundidad tres, con los demás parámetros fijados antes del ajuste. No hubo búsqueda de parámetros, semillas o peligros favorables. Las categorías se aprenden solo en los siniestros de entrenamiento del corte. Las variables nuevas de severidad excluyen identificadores, primas, F3, clima y datos de tramitación del siniestro. Los campos físicos y contractuales conservan sus limitaciones de disponibilidad y confirmación económica previamente declaradas.

Las frecuencias existentes se recuperaron sin volver a ajustarlas. La falta de predicciones de calibración en los archivos de S30 se resolvió por inferencia de sus estimadores guardados. Diez componentes recuperados coincidieron con sus selectores archivados dentro de la tolerancia previa; también coincidieron las anclas históricas completas de V23 y V24. La calibración usa 312.840 filas de la mitad original de 2023. Esa mitad ya se usó para parada temprana de modelos de base, por lo que no es validación independiente.

## Comparación con S30

Se ajustó un único peso global entre cero y 25 %, usando solo calibración de 2023. El componente nuevo se normaliza al total predicho por S30 de cada ramo y corte. El mínimo elegido fue cero. La comprobación numérica independiente confirmó que darle un peso de 25 %, el extremo ya evaluado por el ajuste, aumenta un 0,2315 % la pérdida Tweedie en esa calibración. No se eligió otro peso después de mirar 2024.

| Escenario de reserva, cartera V24 | D² S30 | D² combinación elegida | Ganancia |
| --- | ---: | ---: | ---: |
| 75 % | 0,13723585 | 0,13723585 | 0 |
| 100 % | 0,13787963 | 0,13787963 | 0 |
| 125 % | 0,13720766 | 0,13720766 | 0 |

Se comprobaron los 72 ámbitos previstos, por ramo, cartera, semestre, corte y escenario. No hay retrocesos porque los dos vectores son idénticos. Tampoco se alcanza la mejora global mínima de 0,0002. Los límites inferiores por cliente y dirección son cero y no cumplen la exigencia de ser positivos. Sus intervalos [0, 0] se obtienen por identidad algebraica: no se simularon mil réplicas idénticas. La enumeración regional exacta no procede al fallar los filtros anteriores.

Estos resultados describen la combinación seleccionada, cuyo peso nuevo es cero. No demuestran equivalencia estadística entre la severidad aislada y S30, ni rendimiento futuro en la parte privada de la competencia. No se rescata un ramo, otra intensidad o una semilla de este ensayo.

## Evidencia y límites técnicos

El expediente está en [la corrida privada](../privado/corridas/sevcomp_20261022T155621Z/). Incluye el [plan previo](../privado/corridas/sevcomp_20261022T155621Z/plan_previo.json), la [auditoría de etiquetas](../privado/corridas/sevcomp_20261022T155621Z/auditoria_etiquetas.json), los [campos y parámetros](../privado/corridas/sevcomp_20261022T155621Z/campos_y_parametros_previos.json), la [barrera anterior al ajuste](../privado/corridas/sevcomp_20261022T155621Z/barrera_insumos_pre_fit.json), los [seis modelos y codificadores](../privado/corridas/sevcomp_20261022T155621Z/modelos/), el [resultado íntegro](../privado/corridas/sevcomp_20261022T155621Z/resultado.json) y el [cierre con huellas](../privado/corridas/sevcomp_20261022T155621Z/cierre.json).

Se conservaron las incidencias anteriores al ajuste: rechazo de enlaces duros, rechazo de la carga histórica estricta por huellas diferentes, preparación explícita de `cfg_total.json` y fichas Gamma históricas sin número de filas ni columnas después de liberar los datos de LightGBM. La captura original y la receta no se modificaron. El adaptador separado para inferencia nueva identifica un estimador único por sus metadatos, exige el SHA del modelo y contrasta las predicciones archivadas antes de entrenar. No se presenta como prueba de identidad binaria de todas las entradas del ajuste histórico.

Las seis cabezas nuevas verificaron sus predicciones al guardarse y cargarse. Las huellas protegidas de S30, su especificación y la receta se conservaron. El trabajo fue local: seis ajustes nuevos, cero ajustes de frecuencias, cero producción nueva de 2025 y cero envíos a Kaggle.
