# Contracción de niveles de negocio nuevo hacia su ramo

Codex, 27 de octubre de 2026. La receta se registró antes de ajustar sus constantes y evaluar. Mejora el resultado global local, pero **no supera los controles previstos para adoptarla**. Se conserva como evidencia, sin modificar R1 o F3c ni hacer otro envío.

## Receta y alcance

Se mantuvieron fijos el tronco T2b, la exposición, las curvas de desarrollo, F2, la forma común, los normalizadores y todos los precios de renovación. La comparación usa las versiones de la misma familia aprendidas con 2023 y aplicadas a 2024. No evalúa los archivos publicados como si sus parámetros, que incorporan ambos años, hubieran estado disponibles antes de 2024.

Sobre el precio OOF de 2023 después de F2 y forma, antes del nivel terminal, se estimó un único óptimo Tweedie por ramo. El nivel original de negocio nuevo se contrajo geométricamente hacia él:

\[
Z=\frac{n_{NB,+}}{n_{NB,+}+300},\qquad
\lambda_{NB,cred}=\exp\{Z\log\lambda_{NB}+(1-Z)\log\lambda_{ramo}\}.
\]

K=300 quedó fijo. Es una regla de regularización heredada, no una estimación de credibilidad actuarial plena. El recuento corresponde a periodos con coste positivo, sin eliminar o truncar siniestros. Los niveles originales se reutilizaron; solo se ajustaron tres constantes de ramo y se derivaron tres niveles. Los controles adversos y numéricos se contabilizan aparte. No se ajustaron árboles ni curvas ni se calcularon predicciones de 2025.

| Negocio nuevo | Periodos positivos de entrenamiento | Z | Nivel original | Nivel del ramo | Nivel contraído | Cambio del precio |
|---|---:|---:|---:|---:|---:|---:|
| Autos | 265 | 0,4690 | 1,9386 | 0,9826 | 1,3514 | −30,29 % |
| Edificios | 40 | 0,1176 | 0,9273 | 1,0022 | 0,9931 | +7,09 % |
| Contenidos | 36 | 0,1071 | 0,9274 | 1,0055 | 0,9968 | +7,49 % |

Estos niveles se aprendieron con 2023 para la prueba temporal. No son los niveles de producción de R1 aprendidos con 2023–2024. La valoración de siniestros sigue siendo la fotografía de diciembre de 2024: una separación de aprendizaje correcta no reconstruye snapshots históricos inexistentes.

## Resultado local retenido de 2024

Se evaluaron 59.202 periodos con D² Tweedie de potencia 1,5 y T0 observado. Se mantuvieron los folds guardados; sus cinco resultados son cortes del mismo año de evaluación, no cinco entrenamientos independientes. El remuestreo por 36.408 componentes cliente-dirección reutiliza las mismas 10.000 multiplicidades originales.

| Comparación global | D² local | Diferencia del candidato |
|---|---:|---:|
| Base de la familia, sin bloque propio | 0,123325 | +0,004566 |
| R1 de la misma familia | 0,125642 | +0,002248 |
| Bloque propio completo de la misma familia | 0,125657 | +0,002234 |
| Contracción NB propuesta | 0,127890 | 0 |

Frente a R1, el intervalo ordinario del 95 % es **[+0,000729; +0,003580]**. La banda condicional de la familia de quince contrastes es **[−0,000233; +0,004121]**, por lo que falla el criterio previo de mejora respaldada por esa banda. La familia contabiliza los doce contrastes anteriores y los tres nuevos; no cubre toda la búsqueda adaptativa del proyecto.

| Segmento | Diferencia D² frente a R1 |
|---|---:|
| Todo negocio nuevo | +0,018024 |
| Autos nuevos | +0,039093 |
| Edificios nuevos | **−0,009828** |
| Contenidos nuevos | +0,006525 |
| Renovación de los tres ramos | 0 exacto |

Edificios nuevos incumple el piso registrado de −0,001. El ramo de edificios completo pierde 0,001052, por debajo del mismo piso de segmentos amplios. La mejora es positiva en cuatro de los cinco cortes guardados; el tercero pierde 0,000517.

## Concentración, cola y sensibilidad

Al retirar los 37 grupos más favorables, la diferencia frente a R1 sigue en **+0,001419**. Por tanto, la mejora global no desaparece con ese control de influencia. No obstante, los 41 periodos del 1 % superior entre los de coste positivo reúnen el 21,23 % del T0 retenido y registran un deterioro de devianza frente a R1. El beneficio fuera de esa cola compensa ese deterioro; se conserva la evidencia, sin borrar esos periodos.

En los cincuenta escenarios existentes, aplicados a **precios fijos**, 46 incumplen el piso de algún segmento amplio frente a R1. El peor cambio es −0,001305. El recuento no es una probabilidad de fracaso: son escenarios deterministas de reservas, reportes y desarrollo, con el tronco y los precios fijos. Los recibos anteriores de reaprendizaje del destino no certifican la nueva regla. Como ya falla el contraste nominal, no se inicia una tanda de reaprendizaje para rescatarla.

Con los pesos descriptivos de composición de 2025, la diferencia global frente a R1 es +0,017895, pero su banda de familia vuelve a incluir cero. Esta sensibilidad no introduce etiquetas futuras, no corrige la falta de soporte ni predice el score privado.

## Comprobaciones y decisión

Los controles de implementación pasan. Alterar los costes retenidos de 2024 no cambia los parámetros de la capa nueva; alterar los costes de entrenamiento sí los cambia. Se rechazaron años incorrectos, duplicados y objetivos inválidos. Renovación permanece idéntica, y el replay con parámetros guardados reproduce todos los precios.

Un optimizador escalar con la función de sklearn confirmó los tres óptimos de ramo. La fórmula geométrica se cotejó por potencias ponderadas. Los puntos, veinte sorteos guardados y las métricas de los cincuenta escenarios coinciden con sklearn a precisión numérica. Las identidades de los contrastes originales se comprobaron en las 10.000 réplicas, sin nuevos sorteos ni reajustes. Ambos archivos enviados conservan sus hashes.

La receta queda **sin adoptar y sin admisión de envío**. No se modifican K, el prior o los ramos después de observar estos resultados. En particular, la mejora en autos no autoriza convertir retrospectivamente este ensayo en una receta solo para autos.

El siguiente diagnóstico debe revisar si el nivel de ramo es un prior transportable para edificios nuevos: soporte de 2023, composición de las cohortes, exposición, madurez y contribución de los siniestros grandes. Esto ayudará a distinguir falta de soporte, diferencias de negocio y supuestos de coste último antes de registrar otra receta estándar. R1 y F3c se conservan; no se ha establecido un ganador para el privado.

Índice: `registro/semana2_NB_nivel_credibilidad_actual.json`. Plan previo: `registro/semana2_NB_nivel_credibilidad_plan.json`. Código y verificación: `herramientas/probar_contraccion_nivel_NB.py` y `herramientas/verificar_contraccion_nivel_NB.py`. Los datos y resultados por fila permanecen privados. La revisión es propia y exploratoria, no una revisión profesional independiente.
