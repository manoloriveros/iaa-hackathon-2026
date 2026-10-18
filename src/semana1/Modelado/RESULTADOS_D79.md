# Desarrollo diario y severidad por peligro frente a S08

Se implementó y probó el desarrollo diario por peligro, con frecuencia y severidad separadas. La receta elegida en 2023 obtiene 0.13261433 en 2024 frente a 0.13247471 de S08, una diferencia de +0.00013963. No cumple los criterios declarados para una mejora clara y consistente. Se conserva S08 y no se gasta ningún envío. Su mejor score público registrado sigue en 0.12532; los resultados siguientes son locales.

## Resultado de la receta fijada

| line | S08 | D79 | delta |
| --- | --- | --- | --- |
| all | 0.13247471 | 0.13261433 | 0.00013963 |
| buildings | 0.11342890 | 0.11331712 | -0.00011178 |
| contents | 0.08841663 | 0.08940258 | 0.00098596 |
| motor | 0.08444106 | 0.08444106 | 0.00000000 |

Se puntúan las 626.190 filas de 2024 con todos los costes, incluidas pérdidas extremas, y Tweedie D² de potencia 1,5. La implementación propia coincide con scikit-learn. La receta se fijó el 2026-10-18T03:07:36+00:00 antes de los seis conjuntos principales de 2024 y sus controles; no se reajusta con su resultado. Los pesos usan únicamente la mitad de clientes de selección 2023 de esta ronda, normalizando cada canal al total predicho por S08 en el ramo completo, sin usar el total observado ni añadir otra calibración.

| ramo | variante | peso |
| --- | --- | --- |
| buildings | F0124__daily_delay | 0.25000000 |
| contents | F0124__nominal_control | 1.00000000 |
| motor | F012__monthly_freq | 0.00000000 |

El peso cero de autos conserva S08. Contenidos retiene un control nominal con tarifario: cualquier aporte suyo corresponde a la combinación de variables y learner, y no acredita un beneficio del desarrollo. En edificios sí se seleccionó severidad condicionada por retraso. Se conserva el conjunto completo de comparaciones, incluidos resultados adversos; no se buscan nuevos pesos al observar 2024.

Los intervalos condicionales aproximados del cambio global, con 400 remuestreos por agrupación, son [-0.00010596; 0.00038683] por cliente y [-0.00011697; 0.00044498] por dirección. Las claves de ambas agrupaciones están completas. Estos intervalos condicionan a modelos y receta ya elegidos; no incluyen incertidumbre de selección ni dependencia regional de eventos.

Al excluir el 0,1 % más costoso, S08 obtiene 0.09723330 y D79 0.09743125. Esta es una sensibilidad; la métrica principal conserva todos los costes.

## Implementación actuarial y de aprendizaje

El módulo Preparación/src/iaa_lab/development.py estima por peligro una CDF diaria del retraso de reporte mediante producto límite inverso con truncamiento derecho. Solo entran siniestros positivos, aceptados, asignados de forma única a filas de entrenamiento. Se conserva la probabilidad de cola D75 estimada en el mismo split; no se impone una cola nueva a partir de la validación. La [referencia de Korn, §2.2](https://variancejournal.org/article/115769-a-comprehensive-non-aggregated-stochastic-approach-to-loss-development), explica la estimación del retraso bajo truncamiento y sus supuestos. La distribución ponderada por coste y los Gamma de esta ronda son aproximaciones propias con una sola valoración de coste, sin identificar IBNER.

La exposición efectiva integra F(31-12-2024 menos fecha de ocurrencia) sobre cada día cubierto, incluidos los extremos, y la multiplica por la exposición suministrada. Se respeta el año bisiesto. El control mensual promedia exactamente la misma CDF sobre el mes calendario y la aplica a los días cubiertos de ese mes. De esta forma, el contraste diario/mensual aísla la granularidad del calendario y no un cambio simultáneo de curva. Las pólizas de mes completo coinciden; las intersecciones parciales pueden diferir.

Se ajusta un Poisson de 250 árboles por peligro con n/exposición efectiva y peso igual a esa exposición. La severidad base usa Gamma de 200 árboles sobre coste positivo/conteo positivo, con peso igual al conteo. El brazo daily_fs ajusta ese objetivo por el cociente de completitud de conteos e importes y predice con exposición efectiva de coste. La CDF de importes se acerca un 50 % a la de conteos para moderar la influencia de pérdidas grandes.

El brazo daily_delay ajusta otro Gamma a cada siniestro positivo, con covariables de póliza y una banda de retraso. Las bandas son 0–7, 8–30, 31–90, 91–180, 181–365, 366–730 y más de 730 días. Al predecir una póliza se integra la severidad de cada banda sobre su probabilidad reportada, sin consultar siniestros de esa póliza futura. La frecuencia, el calendario y la severidad quedan separados en los artefactos. Las bandas escasas y la severidad de la masa no observada mantienen incertidumbre; no se atribuye identificación de coste último a esta aproximación.

Se mantienen las reglas de elegibilidad y las excepciones positivas de entrenamiento. Por ejemplo, una excepción histórica impide imponer un cero automático al peligro correspondiente. T0 conserva coste incurrido neto de recuperaciones, sin restar de nuevo pagos o franquicia. Para el objetivo último 2025 se usaría exposición nominal y la masa completa de las bandas; esta ronda no entrena producción ni genera un envío porque la comprobación no supera el filtro. S08 conserva su nivel último y no se aplica otra vez IBNR ni exposición.

## Comparación pareada de mecanismos

Cada fila compara el mecanismo con su propio control FS nominal y las mismas variables, igualando el total predicho del ramo antes de calcular el cambio de D². F012 conserva las variables del FS anterior; F0124 añade exclusivamente el tarifario ya autorizado y sus primas anualizadas/relativas. Un Gamma base compartido evita confundir un nuevo ajuste de severidad con el offset de frecuencia. El control nominal F012 reutiliza los modelos históricos D74 verificados por hash; el control F0124 se ajusta explícitamente.

| line | feature_arm | method | V23 | V24 |
| --- | --- | --- | --- | --- |
| buildings | F012 | daily_delay | 0.00108958 | 0.00094551 |
| buildings | F012 | daily_freq | 0.00008201 | 0.00084281 |
| buildings | F012 | daily_fs | 0.00008218 | 0.00061024 |
| buildings | F012 | monthly_freq | 0.00008173 | 0.00072011 |
| buildings | F0124 | daily_delay | 0.00031804 | 0.00109570 |
| buildings | F0124 | daily_freq | -0.00007106 | 0.00038685 |
| buildings | F0124 | daily_fs | -0.00006680 | 0.00063701 |
| buildings | F0124 | monthly_freq | -0.00007131 | 0.00026606 |
| contents | F012 | daily_delay | -0.00102202 | 0.00112563 |
| contents | F012 | daily_freq | -0.00000688 | 0.00081341 |
| contents | F012 | daily_fs | -0.00000761 | 0.00071936 |
| contents | F012 | monthly_freq | -0.00000676 | 0.00066643 |
| contents | F0124 | daily_delay | -0.00064892 | 0.00074114 |
| contents | F0124 | daily_freq | -0.00000913 | 0.00083620 |
| contents | F0124 | daily_fs | -0.00000980 | 0.00078620 |
| contents | F0124 | monthly_freq | -0.00000901 | 0.00068383 |
| motor | F012 | daily_delay | -0.00018198 | 0.00437103 |
| motor | F012 | daily_freq | -0.00012217 | 0.00405505 |
| motor | F012 | daily_fs | 0.00016037 | 0.00421230 |
| motor | F012 | monthly_freq | -0.00011848 | 0.00392905 |
| motor | F0124 | daily_delay | 0.00041792 | 0.00385946 |
| motor | F0124 | daily_freq | 0.00017512 | 0.00382116 |
| motor | F0124 | daily_fs | -0.00047085 | 0.00406545 |
| motor | F0124 | monthly_freq | 0.00017914 | 0.00359875 |

Los valores de 2023 corresponden a la mitad de selección y los de 2024 al año completo. La tabla no representa diez experimentos independientes: los mecanismos comparten estimadores. El archivo peril_ablations.csv desglosa los cambios por peligro del brazo con tarifario, con total de cada peligro igualado al de su control nominal. Para ese diagnóstico se sustituye el cero predicho de coberturas excluidas por 1e-9; no cambia la métrica global ni las predicciones guardadas.

En 2024, pasar de mensual a diario con la misma curva mejora el D² pareado del FS con tarifario en 0,00022241 en autos, 0,00012080 en edificios y 0,00015237 en contenidos. En 2023 el efecto es mínimo, coherente con su mayor madurez al cierre común. La severidad por retraso también mejora el control nominal de edificios en ambos cortes (+0,00031804 y +0,00109570), pero su mezcla fijada no mejora S08 en ese ramo durante 2024. El FS de autos con desarrollo mejora claramente a su control nominal en 2024 y aun así queda por debajo del S08 de autos. Hay señal en el mecanismo actuarial; el reemplazo del combinador más fuerte requiere evidencia adicional.

## Completitud y severidad observadas

| line | peril | daily_count_completion | daily_cost_completion | relative_daily_minus_monthly_maxabs |
| --- | --- | --- | --- | --- |
| motor | bodily_injury | 0.56643933 | 0.55654557 | 7.67606397 |
| motor | glass_hail | 0.97636013 | 0.97591226 | 3.07766801 |
| motor | own_damage | 0.97082392 | 0.97088321 | 3.91466284 |
| motor | theft | 0.98396990 | 0.98429475 | 2.22135327 |
| motor | third_party_prop | 0.94237825 | 0.94210427 | 5.78274978 |
| buildings | accidental_damage | 0.97117905 | 0.97111911 | 3.98134624 |
| buildings | escape_of_water | 0.95654120 | 0.95699513 | 5.03182245 |
| buildings | fire | 0.98543701 | 0.98160881 | 2.08471510 |
| buildings | flood | 0.96977952 | 0.97035574 | 3.96646579 |
| buildings | storm | 0.96787564 | 0.96667464 | 3.91125989 |
| buildings | subsidence | 0.66492648 | 0.66417424 | 8.01542777 |
| contents | accidental_damage | 0.96902764 | 0.96904774 | 4.06094784 |
| contents | escape_of_water | 0.95571057 | 0.95651358 | 4.99965728 |
| contents | flood | 0.96486956 | 0.96426772 | 3.63999287 |
| contents | theft | 0.98431448 | 0.98401097 | 2.13566690 |

Las completitudes son medias ponderadas por exposición del año 2024 estimadas solo con 2021–2023. La última columna es la mayor diferencia relativa absoluta entre exposición diaria y mensual, dividida por la diaria: mide el caso más sensible, no el efecto promedio ni una mejora de score. calendar_diagnostics.csv añade distribución y períodos de hasta 30 días. delay_band_diagnostics.csv conserva por peligro y split tamaños de muestra, medias y totales de coste actual por banda; esas medias mezclan riesgo y retraso y no son efectos causales ni severidades últimas.

## Diseño, alcance y decisión

V23 entrena con 2021–2022 y evalúa 2023; V24 entrena con 2021–2023 y evalúa 2024. Todas las etiquetas se valoran al cierre común del 31 de diciembre de 2024. No se reconstruyen reservas históricas inexistentes. El comparador S08 ya ajustó su combinador con todo el OOF 2023, y 2024 fue consultado en rondas anteriores. Es desarrollo retrospectivo reutilizado y comprobación propia, sin validación independiente ni etiquetas últimas 2025.

Se declararon antes de 2024 una ganancia global mínima de 0,0005, límites inferiores positivos de ambos intervalos, caída máxima por ramo de 0,0005 y deterioro máximo de 0,0002 sin el 0,1 % superior, además de mejora positiva en esa sensibilidad. El resultado de cada criterio es:

| condicion | superada |
| --- | --- |
| global_gain | False |
| customer_bootstrap | False |
| address_bootstrap | False |
| per_line | True |
| tail_sensitivity | True |
| non_tail_gain | True |

La receta no supera el filtro conjunto. Las semillas adicionales 42 y 137 estaban condicionadas a superarlo y no se entrenan para buscar un resultado favorable. Se conservan modelos, predicciones, controles y curvas, pero no se promueve D79 a producción ni se reemplaza S08. El registro de envíos queda idéntico al inicio. No hubo entrenamiento remoto, publicaciones, mensajes, automatizaciones ni delegación.

## Evidencia y reproducción

Se entrenaron 12 conjuntos principales y seis controles nominales auxiliares, 330 estimadores en total, con semilla 2026 y cuatro hilos por learner en Windows local. Se comparan cuatro mecanismos y un control nominal en dos bloques de variables, tres ramos y dos cortes. Los pesos se buscan en 0/25/50/75/100 %. No se incorporan de nuevo las ventanas D78 ni se cambia el contrato F0 histórico.

Pasan siete pruebas funcionales: recuperación de una distribución conocida con truncamiento, ponderación por costes, días inclusivos y bisiestos, equivalencia de mes completo, suma de bandas y cola última, extremos de bandas e identidad de frecuencia/severidad con dos completitudes. Se recargan los 12 conjuntos principales y los seis controles nuevos, reproduciendo 1320 predicciones de póliza y sus componentes entre conjuntos, y comprobando sumas y objetivos en 2,505,090 filas de salida entre conjuntos. Las curvas se reconstruyen exactamente desde los siniestros originales de entrenamiento; diez períodos por peligro y conjunto se contrastan con una suma diaria directa. Son recomprobaciones propias del flujo, no revisión independiente.

Tres ajustes con tarifario de V23 terminaron de guardar modelos y predicciones pero fallaron después al anotar el hash del wrapper: se pasó una cadena donde sha256_file requería Path. Se preserva run_price_v1.py, se corrige el wrapper y se completan solo metadatos tras verificar los hashes de ambos archivos. metadata_repair.json documenta la reparación sin cambios de predicción ni repetición de entrenamiento. Los ajustes V24 terminan con el wrapper corregido.

La primera ejecución del diagnóstico por peligro reutilizaba el nombre de la tabla de predicciones para un subconjunto de siniestros y se detuvo antes de escribir resultados. Se conserva diagnostics_v1.py, se corrige ese nombre y se repite exclusivamente el diagnóstico. Ningún modelo, predicción, peso o métrica principal cambia por esa corrección.

La carpeta Preparación/artifacts/verification/improvement_D79 conserva plan.json, feature_arm_plan.json, recipe_V23.json, contract_D79.json, las métricas y ablaciones de ambos cortes, confirmation_V24_s2026.json, model_verification.json, environment.json y los modelos joblib. D79_source.zip archiva fuentes y dependencias propias relevantes; closure_D79.json identifica los archivos por SHA-256. La aportación de IA y las responsabilidades humanas se registran en request_and_AI_contribution.json. La documentación sigue las prácticas priorizadas de IAA, en particular Gobernanza §2.8 y §§3.4–3.6, y Documentación §§2–6. Esto no constituye certificación ni aprobación profesional.

Desde C:/dev/Hakaton se usa Preparación/.venv/Scripts/python.exe, con la caché parquet-reader y Preparación/src en sys.path. run.py train --line RAMO --split V23/V24 ajusta F012; run_price.py RAMO --split V23/V24 ajusta F0124; nominal_control.py RAMO --split V23/V24 crea su control. compare.py V23 congela la receta antes de los ajustes V24; compare.py V24 comprueba esa receta. verify_models.py reproduce artefactos y diagnostics.py calcula los diagnósticos. Una reproducción con nuevos ajustes debe usar una carpeta nueva, porque los scripts impiden sobrescribir los conjuntos existentes. No se modifican originales, datos activos, F0, D74, D75, D76 ni S08.
