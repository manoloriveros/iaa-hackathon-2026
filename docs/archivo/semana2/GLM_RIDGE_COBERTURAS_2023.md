# GLM ridge con coberturas: ensayo estándar de estabilidad

Codex, corte UTC 2026-10-24T01:44:14.234707+00:00. Se completó una sola receta preinscrita con quince ajustes locales sobre los cinco folds de 2023. La motivación fue concreta: B19 mejoró el ajuste en todas las celdas, pero empeoró fuera de muestra frente a B14. Se probó contracción antes de añadir variables, interacciones u otra familia.

La receta pasa la revisión técnica. Su punto global mejora, pero no hay respaldo suficiente para promoverla: el intervalo frente a B14 incluye cero y todas las ventajas se invierten en el diagnóstico de grupos favorables. B00 y las veinte alternativas se conservan.

## Resultado fuera de muestra

| Modelo | D² global 2023 | A/E | Total observado predicho, CU |
| --- | ---: | ---: | ---: |
| W2-B00 | 0.068582 | 0.9797 | 15,614,394.39 |
| W2-B14 | 0.086710 | 0.9914 | 15,429,695.38 |
| W2-B19 | 0.082470 | 0.9909 | 15,436,941.83 |
| W2-B20 | 0.089382 | 1.0113 | 15,126,408.70 |

Las 50.094 filas y los 30.869 componentes son los mismos para todos los modelos. La métrica global usa su propia desviancia nula; no promedia los scores por ramo. Son resultados exploratorios sobre datos de 2023 usados repetidamente para investigar, con T0 observado y C0 condicionados.

| Contraste nuevo | Cambio D² | Intervalo exploratorio 95% | Tras retirar 31 grupos favorables |
| --- | ---: | --- | ---: |
| B20 / W2-B19 | +0.006912 | [+0.001420; +0.013511] | -0.003869 |
| B20 / W2-B14 | +0.002672 | [-0.003673; +0.008683] | -0.006513 |
| B20 / W2-B00 | +0.020800 | [+0.000346; +0.041688] | -0.006580 |

Se calcularon solo las tres parejas nuevas, con 2.000 remuestreos pareados por componente y sorteos comunes. Los intervalos no ajustan la búsqueda adaptativa ni la incertidumbre de volver a ajustar modelos y primera etapa. El intervalo positivo frente a B19 no supera esas limitaciones. El análisis de influencia cambia únicamente la evaluación: no se borran siniestros o grupos ni se vuelve a entrenar.

## Deterioros que conserva la decisión

| Segmento | D² B20 | Cambio frente a B14 |
| --- | ---: | ---: |
| buildings_new_business | 0.069497 | +0.019334 |
| buildings_renewal | 0.012680 | +0.001216 |
| contents_new_business | 0.147164 | -0.006415 |
| contents_renewal | 0.029850 | +0.008887 |
| motor_new_business | -0.019444 | -0.009399 |
| motor_renewal | 0.042435 | +0.002641 |

Los tres ramos mejoran su punto agregado frente a B19 y B14, pero autos nuevos y contenidos nuevos pierden frente a B14. No se elige una receta por ramo o segmento después de observarlos. En hogar el A/E agregado de B20 supera uno; una mejor desviancia no acredita suficiencia del nivel.

El nominal condicionado de los mismos periodos de 2023 cambia -2.008% frente a B19. Es exposición nominal por tasa bajo el vínculo declarado, no una estimación validada del nivel último de 2025.

## Qué cambió en la receta

Tweedie de potencia 1,5 y enlace log, con las mismas siete variables por ramo, T0, C0, capital y folds de B19. El único cambio de hiperparámetros es alpha de cero a uno. La penalización actúa sobre todos los coeficientes numéricos estandarizados y categóricos codificados; el intercepto queda libre. No es una intervención exclusiva sobre cobertura. Alpha uno procede de la primera receta B01 y se fijó antes del ensayo, sin buscar otras intensidades.

Medianas, escalas y categorías se aprenden solo con las filas de ajuste. Se conserva OHE con primera categoría omitida, frecuencia mínima 50 y máximo 40 categorías; el efecto de ridge depende de esa codificación, que queda explícita y fija. La respuesta es T0/e, el peso es raíz(e) y la predicción observada aplica e una vez. No se añaden máscaras estructurales, clima, credibilidad o calibración de nivel.

La norma cuadrada de coeficientes baja en los quince ajustes y el objetivo penalizado mejora respecto al coeficiente sin penalizar evaluado en el mismo diseño. Eso comprueba el mecanismo de contracción. En edificios, la razón condicional de cobertura accidental activa frente a inactiva todavía recorre aproximadamente 0,801 a 1,375 entre folds y cambia de dirección. Los folds se solapan; ese rango no es un intervalo ni una relación causal o contractual.

## Comprobaciones y siguiente decisión

Pasaron 542 comprobaciones separadas con fit bloqueado y 48 adversos focales, con solapamiento entre controles. La revisión reconstruye medianas, escalas e indicadores, predicción manual, objetivo general, gradiente penalizado y su derivada por diferencias finitas. Reproduce métricas con sklearn y el remuestreo con multiplicidades. Tres comandos nativos rechazan repetición, código cambiado o fuente cambiada antes de ajustar. No se repitió el entrenamiento para comprobarlos.

Se mantienen B00 y B01–B20. No se promueve, retira una alternativa ni congela una lista final. El siguiente diagnóstico útil atribuye la ganancia a grupos y segmentos con los artefactos guardados, sin ajustar alpha o añadir complejidad. La verificación propia de Codex no es validación profesional independiente.

2024 y test permanecen cerrados para precios, predicciones y scores de este trabajo; no se leyó el ledger. Sigue declarada la exposición previa a métricas externas en un asunto del foro, sin usar esa información o afirmar ceguera completa. Permanecen las limitaciones de capital, último, reservas y reporte. La incidencia de Kaggle no autoriza enviar una prueba.

Se hicieron quince ajustes nuevos: el contador propio pasa de 180 a 195 ajustes de precio y conserva 285 constantes. El linaje del catálogo principal tiene 120 ajustes y 60 constantes; las otras sensibilidades, auxiliares y curvas se cuentan aparte. Se reutilizan exactamente las veinte recetas anteriores.

[Plan previo](../../../registro/semana2_glm_ridge_coberturas_plan_v1.json), [índice](../../../registro/semana2_glm_ridge_actual.json), [productor](../../../src/semana2/entrenar_glm_ridge_coberturas2023.py), [comprobador](../../../herramientas/verificar_glm_ridge_coberturas2023.py) y [adversos](../../../herramientas/probar_glm_ridge_coberturas2023.py). La corrida, modelos y decisiones por fila permanecen en `privado/semana2/desarrollo2023/ridge20_20261024_v1`, fuera de Git. Se aplican las prácticas IAA de propósito y límites, validación y control de cambios y ficha del modelo, sin certificación.
