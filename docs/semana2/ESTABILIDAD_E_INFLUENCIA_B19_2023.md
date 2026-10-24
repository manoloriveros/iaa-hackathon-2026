# Estabilidad de coeficientes e influencia de grupos en B19

Codex, corte UTC 2026-10-24T01:55:38.449816+00:00. Solo artefactos de 2023: modelos B19 y B14 guardados, OOF y siniestros canónicos. Cero entrenamientos, recetas nuevas o remuestreos. B00 y todas las alternativas permanecen. La receta diagnóstica se publicó en el comentario 036 antes del cálculo.

## Dos formas distintas de influencia

La pérdida relativa de autos nuevos depende mucho de un componente con lesiones corporales. En edificios la influencia se reparte entre varios componentes, especialmente incendios. La dispersión de coeficientes se mantiene al compararlos en su escala original; no es un artefacto de comparar coeficientes estandarizados con escalas diferentes.

La contribución OOF de un componente mide cómo cambia la desviancia B19 frente a B14 en sus filas retenidas. La influencia local de ajuste aproxima cómo cambiarían los coeficientes si se redujera el peso de ese componente en otros modelos donde sí participó. Cada componente está fuera del ajuste que produjo su propia predicción OOF. No se confunden esos dos mecanismos.

## Coeficientes comparables

Las pendientes numéricas se recuperan como beta_estandarizado/escala, con la corrección del intercepto por centrado. Se comprueban las mismas referencias categóricas; no se fabrica una comparación para categorías ausentes o agrupadas. Los cinco folds comparten datos y no son cinco observaciones independientes para construir un intervalo.

| Ramo | Razón condicional de tasa | Rango entre folds | Coeficiente negativo | Positivo |
| --- | --- | ---: | ---: | ---: |
| buildings | AD sí / AD no | 0.795–1.388 | 1 | 4 |
| buildings | Nuevo / renovación | 0.856–1.217 | 3 | 2 |
| contents | AD sí / AD no | 0.865–1.020 | 2 | 3 |
| contents | Nuevo / renovación | 0.671–1.028 | 4 | 1 |
| motor | third_party_fire_theft / comprehensive | 0.587–0.611 | 5 | 0 |
| motor | third_party_only / comprehensive | 0.567–0.857 | 5 | 0 |
| motor | Nuevo / renovación | 1.978–2.481 | 0 | 5 |

En edificios, AD sí / AD no va de 0,795 a 1,388 y cambia dirección: el fold 3 es inferior a uno. En autos, third_party_only/comprehensive va de 0,567 a 0,857; third_party_fire_theft/comprehensive es más estable, aproximadamente 0,587–0,611. Nuevo negocio de autos conserva una razón próxima a la de B14; no se atribuye toda la inestabilidad al campo añadido. Estas son asociaciones condicionales del GLM para coste total, no efectos causales de una cobertura o confirmación del clausulado.

## Pérdida OOF por componente

Se define A_g como la suma de desviancia B19 menos B14. Valores positivos son adversos para B19. La selección de grupos se fijó por signo y rango, con empates por ID y tamaños 1, 5, 10 y 31. No se ajustó el número de grupos para elegir un modelo. Se recalcula la nula común al retirar filas únicamente de la evaluación.

En edificios hay 12.107 componentes y delta D² B19−B14 de −0,012743. Todos los retiros individuales mantienen el signo negativo; retirar el más adverso deja −0,009127. Los cinco componentes más adversos son incendios y reúnen 1.237.635,60 CU de T0, aproximadamente el 31.5% de las pérdidas brutas de desviancia adversa. Su compensación con grupos favorables se conserva, sin presentar solo una cola de la distribución.

Autos nuevos tiene 2.427 componentes y delta D² −0,021777. Un componente con una fila, third_party_only y lesiones corporales concentra el 56.1% de la pérdida bruta adversa. Su T0 es 136.767,16 CU; los costes esperados OOF ya guardados son 90,25 CU en B19 y 132,77 CU en B14. Son costes esperados por periodo: su distancia a un siniestro grande no significa que el precio deba igualar ese importe. Al retirar solo ese componente de la evaluación del segmento, el contraste cambia a +0,009766. El contraste global del portafolio continúa negativo, −0,002430, al retirar su componente completo.

| Ámbito | Grupos retirados de evaluación | Delta D² al retirar adversos | Delta D² al retirar favorables |
| --- | ---: | ---: | ---: |
| Edificios | 1 | -0.009127 | -0.013562 |
| Edificios | 5 | -0.002984 | -0.015222 |
| Edificios | 10 | +0.000851 | -0.016611 |
| Edificios | 31 | +0.006178 | -0.019760 |
| Autos nuevos | 1 | +0.009766 | -0.025682 |
| Autos nuevos | 5 | +0.016059 | -0.034901 |
| Autos nuevos | 10 | +0.017917 | -0.039254 |
| Autos nuevos | 31 | +0.020558 | -0.045867 |

La tabla se limita al segmento indicado. El anexo conserva además la retirada del componente completo en todos los ramos para la métrica global, y todos los retiros individuales. Los IDs están en artefactos restringidos. Los grupos se ordenan después de observar las pérdidas de 2023; estas sensibilidades son exploratorias, no nuevos conjuntos de validación o intervalos. No se eliminan registros de datos o modelos y no se declara superioridad del modelo sobre el subconjunto elegido.

## Influencia local sobre el ajuste, sin reentrenar

Para diez modelos guardados de autos/edificios se usa el Hessiano observado del GLM con su diseño completo y el gradiente de cada componente. La aproximación de retirada es delta_beta ≈ H⁻¹G_g, convirtiendo después a escala original. Se mantiene H completo y C0 fijo: no es un ajuste sin el grupo, no vuelve a estimar transformaciones o curvas y no sustituye coeficientes para producir precios. El gradiente residual del ajuste y la traza de leverage quedan registrados.

El componente de lesiones corporales anterior aparece en los ajustes 1, 2, 3 y 4, pero no en el 0 que lo predijo. Es el de mayor influencia local absoluta sobre third_party_only entre los componentes de ajuste con negocio nuevo en esos cuatro modelos. Su retirada local aproxima cambios de −0,223 a −0,245 en el logcoeficiente de cobertura y de −0,195 a −0,213 en el de nuevo negocio. El modelo 0, donde falta todo ese fold, tiene la razón third_party_only más baja. Esa coincidencia no aísla el efecto exacto del componente: también faltan los demás grupos de su fold.

En edificios, un incendio de 286.093 CU es el componente con mayor influencia local sobre AD en cuatro ajustes. Sus cambios aproximados del logcoeficiente van de −0,100 a −0,156. No explica por sí solo toda la inversión de signo entre folds. Los cinco mayores grupos adversos OOF también son incendios; una bandera de daño accidental está asociándose a diferencias de coste total, que incluye otros perils. No se infiere una exclusión contractual o una limpieza de incendios caros.

Los Hessianos tienen condiciones de aproximadamente 80.9 a 165.1, lejos del límite técnico previo de 1e12, sin pseudoinversa o ridge. Esto respalda la solución numérica, no la precisión de una retirada completa. Las trazas máximas de leverage de grupos llegan aproximadamente a 0,461 en edificios y 0,293 en autos; ante grupos influyentes, cambios grandes y el Hessiano de grupo omitido limitan la aproximación local. No se usa como prueba causal ni se calcula un precio corregido con ella.

## Verificación, decisiones y continuidad

Pasaron 24 controles del productor, 629 comprobaciones separadas y 112 conciliaciones de lectura, con solapamiento. Fit está bloqueado. La segunda implementación contrasta coeficientes originales, cuentas de grupos por otra fórmula de desviancia y métricas por filas con sklearn, selección de signos/empates, derivadas direccionales del Hessiano y soluciones duales por Cholesky. El error relativo máximo de derivadas es 1e-09. El flujo real rechaza un cambio de T0 entre modelos antes de calcular Hessianos; el fallo esperado queda marcado. Una guarda inicial de continuidad detuvo el intento previo al completarse otra unidad concurrente; no hubo cálculo o ajuste, y se preservó su trabajo al registrar este diagnóstico.

Se conservan los modelos, T0, C0, OOF y grupos. La revisión documenta sensibilidad a siniestros grandes y a composición de folds, sin promover o retirar alternativas. El siguiente paso es cotejar la traza de los componentes destacados (pagado, reservas, recuperaciones, estado y fechas), manteniendo importes y cohortes; cualquier nuevo ensayo requiere su propia receta y autorización aplicable. No se repite el remuestreo anterior ni se salta a otra familia de modelos.

El contador al corte de entrada era 195 ajustes de precio y 285 constantes. Esta revisión añade cero; no modifica el contador o el catálogo activo de otras continuaciones. Sus cortes y cambios concurrentes se conservan. Revisión técnica propia de Codex, no validación profesional independiente o aprobación humana.

2024 permanece cerrado para este trabajo, también test, actas, predicciones, scores y ledger. Se mantiene la exposición previa de un título ajeno con métricas externas, sin repetirlas o usarlas ni afirmar ceguera completa. Solo se muestran autor, ID y UTC del foro. Sin remoto, envíos, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones.

[Plan congelado](../../registro/semana2_b19_estabilidad2023_plan_v1.json), [índice de esta revisión](../../registro/semana2_b19_estabilidad_actual.json), [productor](../../src/semana2/diagnosticar_estabilidad_b19_2023.py), [comprobador](../../herramientas/verificar_estabilidad_b19_2023.py), [ensayo B19 original](GLM_COBERTURAS_2023.md). Evidencia y hashes restringidos: `Hackaton/Repositorio_IAA2026/privado/semana2/desarrollo2023/estabilidad_b19_20261024T014815Z_9b2b1803`. El [balance nocturno](BALANCE_NOCTURNO_PARCIAL_20261024.md) sigue siendo parcial hasta las 07:00 Bogotá.
