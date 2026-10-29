# Sensibilidad y robustez de S30 y S22

Claude (Cowork), 19 de octubre de 2026, a pedido del participante. Trabajo asistido por IA: no es revisión humana ni reproducción por otra persona. No cambia la receta, los modelos entregados, los envíos ni la selección en Kaggle.

S30 es el candidato principal y S22 el respaldo. La pregunta de estos experimentos es cuánto de lo que sostiene esa elección resiste cuando se mueven los supuestos: las reservas, el IBNR, el nivel de 2025, los capitales corregidos, los pesos y la forma de la mezcla, y la propia reproducción de los modelos. Antes de calcular se fijaron por escrito once experimentos con hipótesis y criterio de aceptación, y después, por instrucción del participante, un backtesting del IBNR. Los resultados adversos se registran igual que los favorables.

Lo que se puede sostener es que S30 y S22 están empatados en la práctica. La ventaja de S30 en 2024 desaparece al quitar 6 clientes de 373.831, su pieza principal se valida en un solo corte y una parte es un efecto colateral de la regla de nivel. Ninguna alternativa probada mejora a S30 en todos los criterios, así que no hay razón para cambiar la receta. Sí hay sensibilidades materiales que el informe debe declarar: el nivel de edificios, los capitales sin confirmación y el nivel de autos, que el IBNR de lesiones corporales y las recuperaciones no anticipadas empujan hacia abajo.

## Cómo se diseñó y se controló la batería

Cada experimento tiene su hipótesis y su criterio escritos antes de ver resultados, en un plan con huella SHA-256 registrado en `registro/experimentos_nuevos.json`. Todas las comparaciones usan la etiqueta T0, la mitad de selección de 2023 (V23) y el año 2024 completo (V24), con D² Tweedie de potencia 1,5 en dos versiones: completa y de cuerpo (sin el 0,1 % de mayores costes y con el nivel reajustado, como en las pruebas de robustez del proyecto).

El piso de ruido viene de mediciones existentes. Cambiar semillas mueve la mezcla como mucho 0,00003 en el D² completo de V24 y 0,00005 sin el 0,1 % superior. El remuestreo por cliente es mucho más ancho: el intervalo del 95 % para S30 menos S22 va de −0,000087 a +0,000381. Una diferencia por debajo del piso de semillas se trata como empate.

En una sesión paralela, y también antes de ver resultados, el participante fijó la materialidad en el 1 % del nivel 2025 de cada ramo (`registro/autorizacion_reproduccion_reservas_20261019.json`). Mis criterios ya estaban fijados en el plan; donde los dos difieren, se informan ambos.

Ningún recálculo se usó sin un control previo que reprodujera la referencia. La mezcla de S30 y S22 sale con el SHA-256 entregado; el arnés reproduce los D² de V24 (0,13787963 y 0,13774159); la reimplementación del chain-ladder reproduce la tabla de D67 en los 15 peligros; los componentes con tendencia y las severidades GLM salen idénticos bit a bit; y los dos LightGBM de hogar reentrenados también (sección de reproducción).

| Experimento | Pregunta | Frente al criterio fijado |
| --- | --- | --- |
| Influencia de clientes | ¿Depende la ventaja de pocos clientes? | Sí: 6 clientes la invierten. Hipótesis rechazada |
| Nivel por ramo | ¿Es estable el nivel de 2025? | No en edificios. Rechazada en ese ramo |
| Reservas y recuperaciones | ¿Resiste el orden y el nivel? | El orden resiste; recuperaciones materiales en autos por el criterio del plan, no por el del 1 % |
| Meseta de pesos | ¿Hay pesos vecinos mejores? | No. Confirmada |
| Capitales sin confirmación | ¿Es inmaterial la división entre mil? | No a nivel de fila. Rechazada |
| Cohortes y segmentos | ¿Es homogénea la ventaja? | No es estable entre cortes. Rechazada en parte |
| Piso de ruido | ¿Es el piso de semillas menor que 0,0001? | Sí. Confirmada |
| Tendencia de severidad | ¿Resiste S30 a escenarios de tendencia? | Sí, con matices de atribución. Confirmada |
| Forma y elasticidad | ¿Están en una meseta? | No hay meseta, pero nada domina al vigente |
| Reproducción de componentes | ¿Se reproducen al reentrenar? | Sí, bit a bit. Confirmada |
| Semilla nueva | ¿Cuánto mueve una semilla nueva? | No ejecutado: cubierto por S33 de la línea B y la reproducción |
| Backtesting del IBNR | ¿Predice el método los reportes posteriores? | No en varios peligros. Rechazada; impacto acotado |

## La ventaja de S30 sobre S22 es un empate práctico

En V24, S30 supera a S22 por +0,000138 de D² y en V23 por +0,000162. Al calcular el aporte exacto de cada cliente, los diez más favorables suman 0,000173, más que toda la ventaja, y basta quitar 6 de 373.831 clientes para invertir el signo en V24; en V23 basta uno. Solo el 46,6 % de los clientes favorece a S30 en V24 (68,1 % en V23).

La ventaja no se reparte de forma estable. En 2024 la región R03 (9,7 % de las filas) sale en contra de S30 con un intervalo del 90 % que excluye cero (−0,000662), pero en 2023 esa misma región es neutra (−0,000010) y son otras dos, R08 y R09, las que salen en contra. El segundo semestre de 2024 también es negativo (−0,000304) con intervalo que incluye cero, y el decil superior de predicción cambia de signo entre cortes. Con doce regiones y dos cortes, tres resultados adversos aislados son compatibles con el azar de comparar muchas veces. Lo mismo vale para la calibración regional de edificios: en 2024 seis regiones que suman la mitad de las pólizas del ramo se apartan más de un 10 % del A/E global, pero la correlación de esas desviaciones entre 2023 y 2024 es de 0,22 y solo cinco de doce regiones repiten el signo. Solo R07 y R08 quedan subestimadas en ambos años, y R02 y R05 sobrestimadas; son las candidatas a revisar en la parte 2.

Las reservas no cambian el orden. Con la reserva de caso multiplicada por 0,75, 1 y 1,25, la ventaja en V24 es +0,000105, +0,000138 y +0,000169, y en V23 +0,000188, +0,000162 y +0,000135.

## De dónde sale la ventaja

S30 difiere de S22 en dos cosas: los pesos y la elasticidad de contenidos, y la severidad con tendencia en autos y edificios. Al recalcular la mezcla con la severidad sin tendencia aparece un tercer efecto que no estaba descrito: con esa severidad, un componente de edificios entra en la referencia de nivel de la regla s17 y cambia qué modelo fija el nivel del ramo. Separando los tres:

| Criterio | Contenidos | Composición de la referencia de nivel | Tendencia de severidad | Total S30 menos S22 |
| --- | ---: | ---: | ---: | ---: |
| V23 completo | +0,000230 | −0,000084 | +0,000016 | +0,000162 |
| V24 completo | +0,000006 | +0,000047 | +0,000086 | +0,000138 |
| V23 cuerpo | +0,000249 | +0,000396 | +0,000006 | +0,000651 |
| V24 cuerpo | +0,000141 | −0,000177 | +0,000219 | +0,000183 |

De la ventaja en V24, cerca del 62 % es la tendencia de severidad, el 34 % es el efecto colateral de la regla de nivel y el 4 % el cambio de contenidos. El efecto de la regla de nivel cambia de signo según el criterio, lo que indica una discontinuidad del procedimiento más que una mejora del modelo.

La tendencia solo puede evaluarse en V24. Con dos años de entrenamiento (V23) la regla no ajusta recta y usa el último año, así que su validación descansa en un único corte, el mismo con el que se eligió. El cambio de contenidos es la pieza más robusta: positivo en los cuatro criterios.

## Escenarios de tendencia de severidad

| Escenario | V24 frente a S30 | V24 frente a S22 |
| --- | ---: | ---: |
| Sin tendencia (nivel medio de los años, como S22) | −0,000133 | +0,000005 |
| Nivel del último año ajustado, sin crecimiento | −0,000034 | +0,000104 |
| Mitad del crecimiento estimado | −0,000015 | +0,000123 |
| Tope de crecimiento de ±10 % en vez de ±15 % | 0 | +0,000138 |

S30 sigue por encima de S22 en todos los escenarios con tendencia y los totales de 2025 se mueven menos del 1 %. El tope de ±10 % no cambia nada porque ninguna pendiente lo alcanza. Un supuesto merece mención explícita: la recta de cuatro años lleva la severidad de lesiones corporales de 2025 a unas 16.200 CU, por debajo de los dos últimos años observados (unas 17.700), porque prolonga la caída de 2023. Como ese componente está fuera de la referencia de nivel, el supuesto mueve el reparto entre pólizas de autos y no el total del ramo.

## El nivel de 2025: edificios es el punto débil

El nivel de cada ramo para 2025 es la media de dos factores de calibración, uno estimado en V23 (f23) y otro en V24 (f24). Cuanto más se separan, más incierto es el nivel.

| Ramo | f23 | f24 | Mitad de la distancia | Pérdida de D² si el nivel se equivoca en esa magnitud |
| --- | ---: | ---: | ---: | ---: |
| Autos | 0,986 | 1,005 | 0,92 % | 0,000013 |
| Edificios | 1,059 | 1,134 | 3,44 % | 0,000150 |
| Contenidos | 1,078 | 1,092 | 0,68 % | 0,000006 |

En edificios los dos cortes discrepan casi un 7 % en el nivel y un error de la mitad de esa distancia cuesta 0,000150 de D², cinco veces el piso y del mismo tamaño que toda la ventaja de S30 sobre S22. En autos y contenidos el costo queda bajo el piso. Con el umbral del participante el veredicto es el mismo: edificios supera el 1 % y autos (0,92 %) y contenidos (0,68 %) quedan por debajo. La banda en la que el D² no cae más que el piso mide cerca de ±1,25 % a ±1,5 % del nivel en los tres ramos, así que el umbral del 1 % fijado por el participante queda dentro de lo que la métrica apenas distingue: es un criterio prudente.

Una primera versión de este cálculo comparaba niveles en bases distintas (las predicciones de V24 ya llevan f23) y señalaba por error a contenidos; quedó archivada como superada junto a la evidencia.

## Backtesting del IBNR

Se reestimó el chain-ladder de conteos de D67 con la información disponible al 31 de diciembre de 2022, al 31 de diciembre de 2023 y al 30 de junio de 2024, y se comparó lo que el método proyectaba reportar después de cada corte con lo que realmente se reportó hasta diciembre de 2024. El criterio fijado exigía un error de hasta el 10 % en peligros de cola corta y del 20 % en lesiones corporales y hundimiento.

Con ese criterio el método falla en 6 o 7 de los 15 peligros en cada corte. Muchos fallos están en peligros con muy pocos reportes en la ventana (incendio de edificios: 7 proyectados frente a 5 reales), donde el ruido de Poisson por sí solo supera el 10 %. Daños propios y daños a terceros en autos, los dos peligros de mayor volumen, quedan dentro del 10 % en los tres cortes; escape de agua lo cumple en los cierres de año y se sale en el corte de junio de 2024. El criterio no se relaja por esto; se informa como contexto.

La señal que supera el ruido está en los dos peligros largos. Al cierre de cada año, el IBNR del año recién terminado resultó así frente a su reestimación con todos los datos:

| Peligro | Al cierre de 2022 | Al cierre de 2023 |
| --- | ---: | ---: |
| Lesiones corporales (autos) | +20,1 % | +7,9 % |
| Hundimiento (edificios) | −12,7 % | +24,6 % |

En lesiones corporales el método sobrestimó las dos veces, con un sesgo que baja a medida que el triángulo madura. En el corte de junio de 2024 el error fue de signo contrario (−7,5 %), así que el sesgo parece propio de los cierres de año y no del método en general. En hundimiento el signo cambia, lo que apunta a inestabilidad más que a sesgo. Lesiones corporales es el 90 % del coste IBNR de autos en 2024, así que si su sesgo se repitiera, el nivel de autos para 2025 estaría alto entre 0,80 % y 1,75 %. El costo en D² de ese error es de 0,000010 a 0,000048, en el entorno del piso. En edificios y contenidos el efecto en nivel queda en ±0,3 %.

## Reservas y recuperaciones de autos

Ninguno de los 7.422 siniestros abiertos aceptados de autos tiene recuperaciones registradas, mientras que los cerrados recuperan el 23,6 % del incurrido en daños propios y el 4,0 % en robo. Si las reservas de caso no anticipan esas recuperaciones, el T0 de autos de 2024 está sobrestimado en 1.356.940 CU, el 1,50 % del ramo. Recalculado siniestro a siniestro sobre el universo exacto de T0 (que el control reproduce fila a fila), f24 de autos se movería −1,49 % y f23 apenas −0,006 %, de modo que el nivel de autos para 2025 se movería −0,75 %, unas 895.473 CU menos.

El desplazamiento de f24 supera la banda de ±1,25 % de autos, así que por mi criterio fijado es material; con el umbral del 1 % del nivel del participante, −0,75 % no lo es. Además reduce la ventaja de S30 sobre S22 en autos de +0,000075 a +0,000031. En edificios y contenidos los cerrados no tienen recuperaciones y el efecto es nulo.

Este resultado y el del IBNR apuntan en la misma dirección: el nivel de autos para 2025 podría estar algo alto. Sumados como escenario, entre 1,5 % y 2,5 %, por encima del umbral del 1 %. La acotación de reservas de la sesión paralela llega a la misma conclusión por otro camino: si la severidad de los avisos tardíos de lesiones sigue su hipótesis S3, el nivel de autos baja un 2,2 % (`docs/archivo/semana1/RESERVAS_ACOTACION.md`). Ninguno de estos ajustes se aplica a S30 sin decisión del participante.

## Capitales sin confirmación: una decisión que pesa en 123 filas

De los capitales divididos entre mil, 149 no tienen confirmación por la historia de su póliza (103 de edificios y 46 de contenidos) y 123 están en el test de 2025. En S30 esas filas suman 24.667,97 CU, el 0,012 % del total, y quitar de la evaluación las que caen en 2023 y 2024 casi no mueve el D².

Para medir cuánto depende S30 de esa decisión se rehicieron sus componentes de hogar con el capital sin dividir en esas filas. Los árboles quedan acotados (cada fila sube entre ×1,04 y ×1,92 en el LightGBM de edificios), pero las severidades GLM extrapolan en el logaritmo del capital y multiplican la severidad entre ×5 y ×277 según el peligro. En la mezcla final:

| Ramo | Suma de las filas afectadas en S30 | Con capital sin dividir | Cambio por fila | Resto de filas del ramo | Total del ramo |
| --- | ---: | ---: | --- | --- | ---: |
| Edificios | 21.923 CU | 1.349.139 CU | ×46,9 a ×89,0 (mediana ×65,8) | ×0,974 a ×0,991 | +0,009 % |
| Contenidos | 2.745 CU | 141.161 CU | ×34,8 a ×75,1 (mediana ×49,1) | ×0,988 a ×0,997 | +0,018 % |

Todas las filas afectadas cambian más de diez veces, el umbral material fijado. El total del ramo casi no se mueve porque lo fija la referencia de nivel, y ese mismo mecanismo hace que el resto de las pólizas bajen para compensar: entre 0,9 % y 2,6 % en edificios y entre 0,3 % y 1,2 % en contenidos. La decisión D66 sobre estos capitales es, por tanto, determinante para esas filas y se transmite al resto vía el reescalado. La prueba de prima de D66 sigue siendo la evidencia que respalda la división; estos números muestran cuánto depende el resultado de ella.

## Reproducción y estabilidad de los modelos

Los dos LightGBM de hogar de S30 (S08h y S12h) se reentrenaron con la receta en el entorno de referencia y reproducen bit a bit las predicciones guardadas de 2025 y de V24: ninguna de las 184.155 y 187.498 filas difiere. La copia instrumentada solo añade guardar los modelos, de modo que estos dos nodos ya tienen modelo persistido, en la carpeta privada.

El mismo ejercicio muestra la sensibilidad del boosting a cambios mínimos en los datos. Al reentrenar el LightGBM de edificios cambiando solo el capital de 26 filas de entrenamiento sin siniestros, de unas 700.000, cambian las predicciones de todas las demás: mediana 0,5 %, percentil 99 de 2,7 %, y el 22 % de las filas se mueve más de un 1 %, mientras el total del componente apenas varía. Para una cartera es irrelevante; para cotizar una póliza aislada es un límite a declarar.

## Pesos y forma de la mezcla

Se movió cada uno de los diez pesos de S30 en ±0,05 y ±0,10: de 40 vecinos, ninguno mejora a la vez los dos cortes y los dos criterios por encima del piso. Los pesos están en una meseta.

La forma y la elasticidad de exposición no lo están: en un entorno de ±0,02 alrededor de los valores vigentes el D² se mueve entre 0,0002 y 0,0015, más que toda la ventaja de S30 sobre S22. Pero los óptimos se contradicen entre criterios (el completo pide abrir la forma en hogar y el de cuerpo cerrarla) y entre cortes, y ningún punto de la rejilla mejora los cuatro criterios a la vez. Los valores vigentes son una elección razonable dentro de un conjunto de opciones que no se dominan entre sí.

## Qué cambia para la selección y el informe

| Asunto | Lectura de estos experimentos | Decisión pendiente del participante |
| --- | --- | --- |
| S30 frente a S22 | Empate práctico; S30 se sostiene por criterios secundarios, no por superioridad estadística | Describir la elección de S30 como pragmática |
| Variante S22 con contenidos de S30 | Mejora a S22 en los cuatro criterios, pero pierde frente a S30 en tres | Documentada, no propuesta |
| Nivel de edificios | Incertidumbre de ±3,4 %, sobre el umbral del 1 %, que cuesta tanto como la ventaja | Declararlo |
| IBNR y recuperaciones en autos | Cada uno sugiere nivel 2025 alto entre 0,75 % y 1,75 %; juntos superan el 1 %, como la acotación paralela | Decidir si se ajusta o se declara |
| Capitales sin confirmación | Determinantes para 123 filas, protegidos en el total | Mantener D66 y declarar el mecanismo |
| Tendencia de severidad | Validada en un solo corte; supone lesiones a la baja | Declarar el supuesto y su validación limitada |
| Regla de nivel s17 | Crea saltos según qué componente fija el nivel | Revisar para la parte 2 |
| Reproducción | Dos nodos reproducidos bit a bit con modelo guardado | Extender al resto de nodos si se decide |

## Límites de estos experimentos

V23 y V24 ya se usaron para construir S30 y S22, así que ninguna de estas pruebas es una validación independiente; sirven para medir estabilidad y sensibilidad. El backtesting del IBNR comprueba el patrón de reporte de conteos, no la suficiencia de las reservas ni la severidad de los siniestros tardíos. En el contrafactual de capitales no se recalcularon las frecuencias por peligro de los componentes GLM ni el componente FSA de contenidos, que son árboles y por tanto acotados; el efecto medido es el del canal que domina. Los escenarios combinados de nivel de autos suman efectos estimados por separado.

## Anexo: identificadores, evidencia y cómo repetir

| Elemento | Valor |
| --- | --- |
| Corrida | `sens_20261019T212700Z_b9e7aa92` |
| Plan previo | `privado/corridas/<corrida>/PLAN_PREREGISTRO.md`, SHA-256 `b9e7aa9281670109f12f9a939c241e36e36a9b43be5439ad140a680f88a145a8` |
| Adenda del IBNR | `ADENDA_E12_PREREGISTRO.md`, SHA-256 `7ab8fb145c17fedae194b07f781975b8a7a778c7a83c9e4ea2ca58d870075de1` |
| Evidencia | `privado/corridas/<corrida>/resultados/`: `e01.json` a `e12.json`, `e05_mezcla_cf.json`, `e05_cf_arboles_i.json`, `e05_cf_arboles_ii.json`, `e10_reproduccion.json`; versiones superadas de E02 y E03 conservadas con sufijo `SUPERADA` |
| Cifras ligadas | `cifras_sensibilidad.json`; `verificar_sensibilidad.py` recalcula cada cifra desde su JSON y comprueba que aparece en este texto |
| Modelos persistidos | `modelos_e10.tar.gz` (LightGBM S08h y S12h, producción y V24, tres semillas; y la variante con capital sin dividir) |
| Entorno | Nube de Claude, Python 3.13.16, numpy 2.5.3, pandas 3.0.5, pyarrow 26.0.0, scikit-learn 1.9.1, LightGBM 4.7.0, CatBoost 1.2.10 (las versiones de `requirements.txt`), dos núcleos |
| Insumos | Copias de los Parquet originales, F0 de D68, bases de D67 y corridas de componentes, verificadas por SHA-256 antes de usarse; la mezcla repetida dio los CSV con el SHA entregado |

Para repetir una pieza basta copiar esos insumos, fijar `HAKATON_SEMANA1`, `MODELOS_WORK` y `MODELOS_CLAUDE` como en los scripts y ejecutar el script del experimento; cada uno escribe su JSON y no toca la receta.
