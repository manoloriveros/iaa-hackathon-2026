Codex. Continúo COD-S2-20261023-009 por la nueva petición del participante. Antes de probar otra tanda revisé los modelos y OOF guardados, con fit bloqueado y solo 2023. La [revisión](../../Repositorio_IAA2026/privado/semana2/desarrollo2023/revision_20261023T175646Z_4924665e/report.json) conserva código y detalle.

En edificios, el GLM gana en las 12.083 filas sin coste y pierde en las 497 positivas; cinco grupos adversos bastan para cambiar el signo al retirarlos solo como diagnóstico. No se retiran de la pérdida o del entrenamiento. Los 26 capitales desconocidos no tienen siniestros y explican una contribución pequeña al deterioro; no justifican corregir capitales. Algunos coeficientes categóricos cambian de signo entre folds. En el árbol 300 de LightGBM hay hojas con pocos positivos, incluso ninguno en contenidos. Es evidencia de soporte débil, no prueba causal de un parámetro.

Precisión a la redacción anterior: min_child_samples=200 es el parámetro declarado, no una garantía de doscientas filas reales por hoja; LightGBM lo aproxima mediante Hessianos. La revisión encontró hojas más pequeñas, coherentes con la [documentación oficial](https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html#min_data_in_leaf). No se cambió la receta v1.

El [plan v2](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_plan_v2.json) fija tres recetas nuevas antes de sus resultados:

- W2-B03: el mismo GLM de edificios con alpha=10; autos y contenidos reutilizan exactamente B01. Cambia solo la penalización de edificios.
- W2-B04: exactamente los primeros 25 árboles de cada modelo B02 guardado. No se entrenan de nuevo ni se puntuó antes otro prefijo; 25 queda fijado ahora, sin elegir el mejor punto de una curva.
- W2-B05: LightGBM con 80 rondas, árboles de profundidad uno y dos hojas, min_child_samples=1000 y L2=100; el resto coincide con B02. Es una reducción conjunta de capacidad y no aísla cada parámetro.

Se mantienen F0, T0/C0, peso sqrt(e), particiones y semilla. No se cambia nivel ni se añaden mezclas. Habrá veinte ajustes nuevos, diez reutilizaciones GLM y quince extracciones de prefijo, con CPU local y dos hilos. Se comparan las seis recetas contando v1, con todos los puntos, segmentos, brechas, influencia y 2.000 remuestreos exploratorios comunes. La búsqueda ya informada por v1 se declara; los intervalos no corrigen esa selección ni las quince parejas.

La lectura previa exige comprobar si B03 mejora edificios y si B04/B05 reducen la brecha y el deterioro frente a B02; cada alternativa también se contrasta con B00 sin cambios. No se cambiará una receta después de ver esta tanda. Se conserva la referencia y toda alternativa, con resultados adversos. La aceptación técnica incluye replay, parámetros, encoders dentro de fold, prefijo exacto y comparadores inalterados.

2024 permanece cerrado por instrucción expresa del participante, aunque otro encargo avance la corrección del selector. No hay promoción ni lista final congelada, scores 2024, test, envíos o entrenamiento remoto en este plan. El bloqueo previo de B02 y su alias S2-VAL-MOD-007 no se dan por cerrados por registrar recetas diferentes.
