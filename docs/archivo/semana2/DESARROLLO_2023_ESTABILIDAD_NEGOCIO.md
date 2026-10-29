# Estabilidad de B08 y nivel de nuevo negocio

Codex, 23 de octubre de 2026. B08 mejora frente a B00 en los cinco folds, pero su nivel es sensible a pocos siniestros grandes del ajuste. Las dos correcciones de nivel preinscritas mejoran sus puntos globales; la ventaja sobre sus propios padres sigue incierta y ambas empeoran la devianza de edificios nuevos. Se conserva B00 y todas las alternativas. 2024 permanece cerrado.

El [plan v4](../../../registro/semana2_desarrollo2023_plan_v4.json) quedó en COD-S2-20261023-014 antes de calcular factores o reentrenar. El resultado es COD-S2-20261023-015 del [foro](<../../../../Semana%202/Foro/FORO.md>). El [índice activo](../../../registro/semana2_desarrollo2023_actual.json) mantiene las cuatro tandas y sus snapshots. Los cálculos se refieren a 50.094 periodos de 2023, 30.869 componentes cliente-dirección y cinco folds guardados. D² usa Tweedie 1,5 en importes observados T0, con nulo global; no es un promedio de D² por ramo ni una medición del último real.

## Diagnóstico antes de probar

La [revisión del OOF congelado](../../../privado/semana2/desarrollo2023/revision_estabilidad_20261023T204359Z_e4efa1cd/report.json) no calculó factores o nuevas predicciones. B08 mejora entre 0,01291 y 0,03360 puntos D² frente a B00 en cada fold; su A/E varía entre 0,779 y 1,133. Sus 31 componentes de evaluación más favorables concentran 78,0 % de la ventaja neta, y los de B09 90,8 %. Harían falta 68/40 grupos favorables para invertir sus ventajas con modelos fijos. Los folds comparten ajuste y estos retiros no comprueban estabilidad con reentrenamiento.

B09 pierde en autos nuevos (delta D² frente a B00 −0,01722, A/E 1,910) y edificios nuevos (−0,00843), mientras mejora en contenidos nuevos (+0,02782). Autos nuevos aporta 1,088 millones CU observados y solo 0,570 predichos; el propio B00 predice 0,543 millones. B08 mejora el agregado nuevo, pero pierde en edificios nuevos (−0,03269). Los tamaños positivos de nuevo negocio son 265 en autos, 40 en edificios y 36 en contenidos: unas pocas severidades pueden mover mucho las conclusiones por ramo.

## Recetas congeladas y frontera de información

B10 parte de B08 y B11 de B09. Para cada ramo/fold y negocio nuevo o renovación se calcula únicamente en ajuste:

`mu = exposición_efectiva_C0 × tasa_padre`

`q = sum(T0 / sqrt(mu)) / sum(sqrt(mu))`

`tasa_nueva = q × tasa_padre`

Es el mínimo escalar positivo de la devianza Tweedie 1,5 para esa forma de riesgo. Usa predicciones dentro del ajuste y no constituye calibración independiente o interna fuera de muestra. Cambia explícitamente el ancla de nivel en las dos variantes; no fuerza totales de ajuste/validación o A/E igual a uno. Conserva orden de tasas solo dentro de ramo, fold y tipo de negocio. Se aprendieron 60 factores y se guardaron 30 adaptadores, sin nuevos GLM/árboles para B10/B11. No hubo búsqueda de pesos, suavizado, cap o elección por score retenido.

Una sensibilidad separada, S08, retira los 25 componentes con mayor T0 de cada conjunto de ajuste (0,1 % redondeado hacia arriba). El orden usa solo costes de ajuste y desempata por ID; se retiran todas sus filas en los tres ramos. Reaprende transformaciones, GLM B03 (alpha 10 en edificios, 1 en los otros ramos), constante S00, ancla y mezcla fija del 50 %. Son quince GLM y quince constantes; cada fold conserva todas las filas de validación. S00/S08 son resultados de estrés, fuera de las doce alternativas candidatas. No se eliminó ninguna fila del ajuste principal de B10/B11, del objetivo completo o de los datos originales.

El estrés conserva C0 del fold. Sus curvas excluyen validación pero aún reflejan los grupos retirados; por eso mide sensibilidad del modelo de riesgo y sus transformaciones, condicional al vínculo de observación. No es reestimación integral de reporting, jackknife completo o validación temporal. La retirada deliberada de siniestros grandes tampoco es una regla admisible de limpieza o propuesta de producción.

## Resultados fuera de muestra en 2023

Observado total: 15,297 millones CU, de los cuales 1,528 son de nuevo negocio. A/E es observado dividido por predicho.

| Receta | D² global | Predicho, millones CU | A/E global | D² nuevo negocio | A/E nuevo negocio |
| --- | ---: | ---: | ---: | ---: | ---: |
| W2-B00 | 0.06858 | 15.614 | 0.980 | 0.04783 | 1.550 |
| W2-B08 | 0.09318 | 15.599 | 0.981 | 0.07297 | 1.182 |
| W2-B09 | 0.08077 | 15.618 | 0.979 | 0.04065 | 1.502 |
| W2-B10 | 0.09424 | 14.161 | 1.080 | 0.08037 | 1.019 |
| W2-B11 | 0.08659 | 14.319 | 1.068 | 0.08304 | 1.043 |

B10 mejora 0,00106 puntos globales frente a B08 y B11 0,00582 frente a B09. Sus intervalos exploratorios incluyen cero. B11 acerca el nivel nuevo (A/E 1,043 frente a 1,502 de B09) y sube su D² nuevo a 0,08304; esto no corrige automáticamente la forma del riesgo. B10 deja un A/E global 1,080 frente a 0,981 de B08: mejorar la devianza no equivale a cuadrar el agregado.

| Comparación | Delta D² | Intervalo exploratorio 95 % | Delta tras retirar sus 31 grupos favorables |
| --- | ---: | --- | ---: |
| W2-B10 / W2-B00 | 0.02566 | [0.01358; 0.03766] | 0.00691 |
| W2-B11 / W2-B00 | 0.01801 | [0.00955; 0.02745] | 0.00346 |
| W2-B10 / W2-B08 | 0.00106 | [-0.00349; 0.00648] | -0.00336 |
| W2-B11 / W2-B09 | 0.00582 | [-0.00158; 0.01619] | -0.00506 |

Las 66 parejas usan 2.000 sorteos comunes por componente, con semilla 2026102302. No corrigen búsqueda adaptativa ni comparaciones múltiples; no son el acta de confirmación 2024. Con las listas previamente congeladas de grupos favorables B08/B09, las diferencias B10/B11 frente a B00 son +0,00701/+0,00835. Las ventajas sobre sus propios padres se invierten al retirar sus respectivos 31 grupos favorables. Se conservan todos los resultados adversos.

| Nuevo negocio por ramo, D² | B00 | B08 | B09 | B10 | B11 |
| --- | ---: | ---: | ---: | ---: | ---: |
| motor_new_business | -0.13013 | -0.08418 | -0.14736 | -0.05602 | -0.04508 |
| buildings_new_business | 0.06523 | 0.03253 | 0.05680 | 0.01111 | 0.02595 |
| contents_new_business | 0.11912 | 0.18781 | 0.14695 | 0.17587 | 0.12741 |

En edificios nuevos, B10 logra A/E 1,003 pero su D² baja de 0,03253 a 0,01111; B11 llega a A/E 1,020 mientras su D² baja de 0,05680 a 0,02595. El nivel agregado oculta una pérdida de calidad dentro del segmento. En autos nuevos ambas correcciones mejoran, aunque sus D² siguen negativos frente al nulo específico del segmento.

| Factor q, rango entre folds | Renovación | Nuevo negocio |
| --- | ---: | ---: |
| W2-B10, motor | 0.869–0.899 | 1.265–1.317 |
| W2-B10, buildings | 0.883–0.916 | 0.803–1.020 |
| W2-B10, contents | 0.860–0.907 | 0.767–0.965 |
| W2-B11, motor | 0.832–0.876 | 1.703–1.889 |
| W2-B11, buildings | 0.911–0.937 | 0.782–1.102 |
| W2-B11, contents | 0.880–0.940 | 0.737–1.074 |

La corrección B11 en autos nuevos exige multiplicadores entre 1,703 y 1,889. Los rangos mayores de edificios/contenidos nuevos deben leerse junto con sus pocos positivos. No se extrae de esto una causa única del deterioro de B09 ni se cierra la advertencia de su receta original.

## Sensibilidad de B08 al reentrenar

Cada fold pierde 46–53 filas de ajuste, que suman entre 2,715 y 3,408 millones CU. Son conjuntos solapados de 25 componentes por fold, no 125 observaciones independientes. La validación y C0 quedan fijos.

| Resultado | D² | Predicho, millones CU | A/E |
| --- | ---: | ---: | ---: |
| B00 original | 0.06858 | 15.614 | 0.980 |
| B08 original | 0.09318 | 15.599 | 0.981 |
| S00 reestimada bajo estrés | 0.03932 | 11.636 | 1.315 |
| S08 reestimado bajo estrés | 0.06916 | 11.625 | 1.316 |

El total de S08 cae 25,48 % frente a B08 y el D² 0,02402 puntos. La mediana de cambio de tasa es −7,27 %; el percentil 1 es −67,34 % y el 99 +7,65 %. S08 supera a S00 en 0,02984 puntos bajo el mismo estrés. Esto sugiere que la forma conserva utilidad relativa frente a esa constante, mientras el nivel depende de grupos severos. No declara a B08 estable para 2025. El A/E 1,316 de S08 muestra el déficit de importe que esa perturbación puede introducir.

## Comprobaciones y decisiones

Pasaron 21 casos focales y 1178 controles del [comprobador separado](../../../privado/semana2/desarrollo2023/dev4_20261023T204811Z_4adcedec/verifications/20261023T205329Z_a8ab6abc.json), con solapamiento entre ellos; es revisión propia de Codex, no validación profesional independiente. Reconstruye factores con suma compensada y derivada, mínimo escalar, claves/ámbito, padres, imputación/escalado de estrés, constante/ancla, replay con fit bloqueado, segmentos, escenarios a tasas fijas, 66 parejas y retiros de grupos. El [manifiesto](../../../privado/semana2/desarrollo2023/dev4_20261023T204811Z_4adcedec/manifest.json), [informe íntegro](../../../privado/semana2/desarrollo2023/dev4_20261023T204811Z_4adcedec/report.json), [valoración](../../../privado/semana2/desarrollo2023/dev4_20261023T204811Z_4adcedec/assessment.json) y [casos focales](../../../privado/semana2/desarrollo2023/dev4_20261023T204811Z_4adcedec/fixture_checks.json) conservan precisión y trazabilidad.

El primer intento de corrida se detuvo antes de cualquier factor o entrenamiento: el cargador de una tabla por modelo rechazó las claves repetidas entre recetas del OOF. Se corrigió el contexto de unicidad a modelo/mercado/ramo/fila, sin cambiar la receta, y se preservó el intento. El primer comprobador se detuvo por una variable local que ocultaba el módulo de expresiones regulares; quedó registrado y se corrigió sin reentrenar. Hubo dos lecturas idénticas del OOF inicial al recuperar una sesión de herramienta, sin nuevas predicciones o ajustes; se conservan como lecturas, no evidencia independiente adicional.

Se mantienen B00 y B01–B11, sin promoción, retiro, equivalencia o lista final congelada. Quedan abiertas la sensibilidad del nivel de B08, el deterioro de edificios nuevos, la incertidumbre sobre la ventaja de los nuevos factores y los supuestos del último. Los escenarios de reservas/reporting mueven el vínculo y la respuesta a tasas fijas; no reentrenan ni acreditan suficiencia de reservas. La siguiente decisión metodológica tendría que tratar la dependencia del nivel y la forma por ramo sin ajustar a posteriori los folds vistos; no se inicia otra tanda en este encargo.

La aplicación de [prácticas IAA](../../../../../Preparaci%C3%B3n/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md) queda concreta en el contraste de segmentos (consideraciones profesionales §3.3), sensibilidad y separación de revisión propia/independiente (gobernanza §2.8 y §§3.3.2, 3.4–3.6), y linaje/recetas/resultados adversos (documentación §§2–3). La comparación comercial no acredita equidad profesional o competencia para uso real. No aplican despliegue o monitorización de una tarifa en esta prueba local.

2024 sigue cerrado por instrucción expresa, con cero precios, predicciones o scores; tampoco hay test, envíos, entrenamiento remoto, publicación externa o delegación. El avance técnico del selector no autoriza abrirlo. Las advertencias de otros encargos conservan sus autores y alcance. Persiste la revisión humana pendiente.


## Corte posterior: modelos estándar y continuidad nocturna

La [quinta prueba](DESARROLLO_2023_MODELOS_ESTANDAR.md) añade referencias estándar B12/B13 con receta previa, sin modificar esta tanda. Su [snapshot de índice v4](../../../registro/semana2_desarrollo2023_v4_snapshot.json) conserva exactamente este corte. La continuación nocturna tiene índice separado.
