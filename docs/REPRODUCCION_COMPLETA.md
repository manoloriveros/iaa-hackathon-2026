# Reproducción completa de la entrega final, S41, desde los datos originales

Claude (línea principal), 19 a 23 de octubre de 2026. La entrega final de la parte 1 es S41, que el participante marcó en Kaggle el 23 de octubre (CIE-D103-20261023, [registro](../registro/decision_marca_final_S41_20261023.json)). Este documento explica en qué consiste, con qué hipótesis se construyó y por qué es adecuada. También muestra que se puede rehacer desde los once Parquet originales de dos maneras: reajustando todo y repitiendo la predicción sin ajustar nada. La reproducción la hizo Claude en el entorno de referencia ([autorización](../registro/autorizacion_reproduccion_reservas_20261019.json)). La independencia exigiría que otra persona la repitiera en su propio entorno, y el participante decidió no hacerlo (sección «Qué decidió el participante y qué queda abierto»).

S41 se obtiene en dos pasos. El primero es la receta de 36 nodos que produce la Mezcla por peligro (S30 en el código): datos, variables, diez componentes y la mezcla. El reajuste completo, de los originales al CSV, devolvió el SHA-256 registrado. De las 181 huellas que la receta verifica nodo a nodo coinciden 162; las otras 19 difieren en los últimos bits, como mucho 3,9e-15 relativo, por una elección interna de LightGBM que explica la sección «El reajuste completo». La réplica desde los 436 estimadores guardados, con un centinela que hace fallar cualquier entrenamiento, no ajustó nada y repitió bit a bit todas sus salidas en 34 minutos. El segundo paso multiplica las predicciones de cada ramo por un factor fijo. Repetido con el script registrado sobre los productos de las dos corridas, da S41 con su SHA-256 y las notas de sus parámetros iguales salvo en el último bit.

## Qué es S41, con qué hipótesis y por qué es adecuada

### En qué consiste

S41 es la Mezcla por peligro con el nivel de 2025 de cada ramo ajustado por un factor fijo: 0,9962 en autos, 1,0260 en edificios y 1,0126 en contenidos. En total prevé 213,7 millones de CU para los 626.639 periodos de 2025: 118,5 millones en autos, 76,3 en edificios y 18,9 en contenidos.

La Mezcla por peligro predice el coste último de cada periodo. En cada ramo combina modelos del coste total con distribución Tweedie (LightGBM y CatBoost) con modelos de frecuencia por peligro multiplicada por la severidad. Aprende del coste observado al cierre de 2024 con una exposición efectiva que descuenta lo que aún falta por reportar, de modo que el IBNR entra una sola vez. Fija el nivel de 2025 con el factor de año siguiente, f = Σ(y/√μ)/Σ√μ, promediado entre los cortes de 2023 y 2024. La cadena completa, de los datos a la predicción, está en [`MODELO_FINAL_S41.md`](MODELO_FINAL_S41.md); los componentes, los pesos y su evaluación, en el informe (`docs/entrega/`) y en [`GUIA_TECNICA.md`](GUIA_TECNICA.md).

El factor de nivel sale de una regla escrita el 22 de octubre, antes de mirar ningún resultado (D100, [preinscripción](../registro/sonda_nivel_D100_preinscripcion.json)). Tiene dos partes:

1. Seis envíos de sonda permiten despejar en cada ramo el factor que prefiere el tablero público, c*. Cada sonda es la mezcla con un solo ramo multiplicado por 0,90 o por 1,10. Para la desviación Tweedie de potencia 1,5, el D² del público en función de un factor c aplicado a un ramo tiene forma cerrada, con dos incógnitas por ramo: D²(c) − D²(1) = −4·[S₁·(c^−½ − 1) + S₂·(c^½ − 1)]/N, con S₁ = Σ y/√μ y S₂ = Σ √μ sobre las filas públicas del ramo y N la desviación nula del público. Las dos sondas de un ramo y la puntuación de la mezcla bastan para despejar S₁/N y S₂/N, y el óptimo es c* = S₁/S₂. Las sondas eran diagnósticas y la regla las excluía de la selección.
2. El factor c* lleva el ruido de un tercio de las filas, así que solo se aplica su parte creíble: c = 1 + Z·(c* − 1), con Z = τ²/(τ² + σ²). La τ es cuánto se esperaba, sin mirar el tablero, que el nivel de 2025 se apartara del de la mezcla: 1,5 % en autos y en contenidos y 3,5 % en edificios. En edificios es la mitad de la distancia entre los factores de 2023 y 2024; en los otros dos ramos esa media distancia se amplió con lo que D95 encontró sobre el IBNR y las recuperaciones. La σ es el ruido del óptimo de una submuestra del 33 %, medido con 300 submuestras de 2024.

| Ramo | Público con ×0,90 / ×1,10 | c*, óptimo del público | σ | τ | Z | Factor de S41 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Autos | 0,12954 / 0,12906 | 0,9774 | 3,37 % | 1,5 % | 0,166 | 0,9962 |
| Edificios | 0,12873 / 0,13018 | 1,0751 | 4,81 % | 3,5 % | 0,346 | 1,0260 |
| Contenidos | 0,12929 / 0,13011 | 1,0840 | 3,57 % | 1,5 % | 0,150 | 1,0126 |

Con la mezcla en 0,12996, la forma cerrada predijo para S41 un público de 0,13015759, y Kaggle devolvió 0,13016 (envío 57531719; [resolución](../registro/sonda_nivel_D100_resolucion.json)).

Dentro de cada ramo S41 es la mezcla multiplicada por su factor. El orden de los riesgos, las relatividades entre pólizas y la forma de la tasa son los de la mezcla. Por eso lo que miden 2023 y 2024 sobre el orden y las relatividades vale igual para S41: el factor solo actúa sobre el nivel de 2025.

### Con qué hipótesis

- El tablero calcula el D² Tweedie de potencia 1,5 fila a fila y suma los ramos sin interacción. Esto es lo que permite despejar c* con dos sondas por ramo. El acierto al quinto decimal lo respalda, aunque no identifica el evaluador de forma única (COD-IA-20261022T172751Z).
- El público es una submuestra de un tercio de las filas sin relación con el riesgo, y el ruido de su óptimo se parece al que se mide en 2024. La batería de sensibilidad posterior (L03 de [`SENSIBILIDAD_S43.md`](SENSIBILIDAD_S43.md)) mostró que, frente al 67 % que no se ve, la varianza de ese ruido es 1/0,67 veces la que usó la regla. Con el ruido corregido, σ/√0,67, Z habría sido 0,117, 0,262 y 0,106, y los factores 0,9973, 1,0197 y 1,0089, más cerca aún de la mezcla.
- El error de nivel de 2025 es común a todas las pólizas de un ramo. El orden y las relatividades aprendidos en 2021-2024 siguen valiendo en 2025.
- La previa τ es razonable. Es una elección de juicio, fijada antes de mirar.
- Valen las hipótesis de la propia mezcla: el coste observado al 31 de diciembre de 2024 como base, con el IBNR estimado por chain-ladder; las reservas de caso a su valor contable; y la disponibilidad de las variables al cotizar. Su sensibilidad a las reservas está en [`RESERVAS_ACOTACION.md`](RESERVAS_ACOTACION.md).

### Por qué es adecuada

Sale sin cambios de la regla escrita antes de mirar: los tres factores no se retocaron después de ver ninguna puntuación. Del tablero toma lo mínimo, tres parámetros de nivel y solo una fracción de su óptimo (Z de 0,15 a 0,35). Lo demás es la mezcla, evaluada en los cortes temporales de 2023 y 2024; esos cortes también sirvieron para elegir sus pesos y su forma, así que no son una validación independiente.

La batería de sensibilidad posterior ([`SENSIBILIDAD_S43.md`](SENSIBILIDAD_S43.md), N05) estimó, con el ruido corregido, la ganancia esperada de S41 en el privado frente a la mezcla. Es positiva bajo los tres pares de previas que probó: +0,000019 con la previa de la propia regla de D100, +0,000062 con Bayes empírico corregido y +0,000083 con previas que no usan el tablero. Con la previa de D100, su desviación típica es 0,000118.

Fuera del tablero hay tres señales sobre hacia dónde debería moverse el nivel de 2025: el factor del último año, los efectos de etiqueta que midió D95 y la siniestralidad de 2024 (L05 de la misma batería). En hogar, S41 sube el nivel en el sentido de al menos dos de ellas y sin pasarse de su tamaño: con la regla de L05, aplicada a S41 sin preinscribir, edificios y contenidos quedan apoyados. En autos solo la señal de D95 acompaña la bajada de S41 (−0,38 %) y el ramo queda parcial; la bajada es pequeña porque la regla confía poco en el marcador. La señal de siniestralidad usa la prima escrita, cuya periodicidad el diccionario no confirma (DATA-006); sin ella, edificios quedaría parcial.

Por último, se reproduce desde los datos originales por dos caminos, como muestra este documento.

### Con qué límites

- La ventaja esperada es pequeña frente al ruido, y nada garantiza el resultado en el privado.
- S41 toma de la mezcla la mayor parte de su nivel, así que hereda su sensibilidad a las reservas. La reserva de caso es una incertidumbre material en los tres ramos. Bajo el supuesto S3 sobre el IBNR de lesiones, el nivel de autos quedaría alto en torno a un 1,9 % ([`RESERVAS_ACOTACION.md`](RESERVAS_ACOTACION.md), «Qué cambia con S41»).
- El tablero público, calculado con un tercio de las etiquetas de 2025, entra en tres parámetros a través de siete puntuaciones. Por eso el público de S41 es optimista por construcción.
- Ninguna persona ha revisado todavía la reproducción ni la batería de sensibilidad; las dos son trabajo de IA.

## Qué faltaba

Hasta el 19 de octubre la cadena tenía dos huecos. La reconstrucción lanzada la noche del 18 se perdió con su contenedor sin dejar recibos por nodo, y ningún script de la receta guardaba el modelo que ajustaba, así que no había forma de predecir sin volver a ajustar ([CLA-20261019-004](RESPUESTA_CLAUDE_REPRODUCCION_RESERVAS.md), COD-20261019-114). Con los archivos de ese momento solo se podía repetir la mezcla final a partir de los componentes guardados.

Este encargo cubre las dos cosas con dos recorridos. El primero va de los once Parquet originales a los dos CSV de la receta, reajustando todo, con recibo por nodo y con cada estimador guardado al terminar de ajustarse. El segundo repite el mismo camino sin ajustar nada: cada ajuste se sustituye por la carga del estimador guardado, y si alguno falta o sus entradas no son las mismas, se detiene.

## Cómo se guardan los estimadores sin tocar la receta

Los scripts de `src/` y `reproducir.py` 1.2 no cambian; sus SHA-256 siguen siendo los de `receta/codigo.json`. La captura vive en una capa aparte, [`herramientas/captura_modelos/`](../herramientas/captura_modelos/captura.py), que Python carga al arrancar solo cuando la carpeta va primera en `PYTHONPATH` y la variable `CAPTURA_MODO` vale `guardar` o `reproducir`. La capa envuelve los puntos donde se ajusta algo: `lightgbm.train`, `CatBoostRegressor.fit`, los dos GLM gamma por IRLS (`glm_gamma` y `glm_gamma_ridge`) y, en la red Tweedie, su entrenamiento y la preparación de sus variables.

Cada estimador se identifica con una clave calculada sobre todo lo que entra en el ajuste: parámetros, valores de la matriz de predictores fila a fila (con las categorías y su orden), etiquetas, offsets, pesos y conjuntos de validación. En modo guardar se ajusta como siempre y después se escribe el estimador completo: LightGBM en texto con todas sus iteraciones, CatBoost en `.cbm`, los coeficientes GLM en `.npy` a precisión completa y la red con su `state_dict` y sus codificadores (medianas, columnas de faltantes, QuantileTransformer y categorías raras). Guardar no consume números aleatorios ni cambia el modelo. En modo reproducir, la misma clave localiza el estimador; si no existe, o si su archivo no coincide con el SHA-256 de su ficha, el proceso se detiene.

La capa pasó por cuatro versiones durante el encargo, todas conservadas con su SHA en la carpeta de la corrida:

| Versión | Autor | Qué cambió | Por qué |
| --- | --- | --- | --- |
| 1.0 | Claude | Primera versión: la clave resumía los marcos de datos por forma, columnas y tipos | |
| 1.1 | Claude | La clave incluye los valores de la matriz, las categorías con su orden y los pesos y demás argumentos de cada Pool | Codex mostró en COD-20261019-117 que con la 1.0 un predictor cambiado en dos filas conservaba la clave |
| 1.1.1 | Codex | En modo reproducir rechaza un Pool sin huella completa antes de buscar el estimador | COD-20261019-121 |
| 1.1.2 | Claude | La clave incluye argumentos posicionales y opciones extra solo cuando existen, así que las llamadas de la receta conservan su clave | GOV-008 (COD-VAL-20261020T0049-GOB): un `sample_weight` por posición no cambiaba la clave |

La batería [`herramientas/probar_captura.py`](../herramientas/probar_captura.py), con datos sintéticos, comprueba que guardar no cambia ningún resultado, que reproducir da vectores idénticos sin ajustar y que reproducir se detiene cuando cambia cualquier entrada o falta o se altera un estimador. La 1.0 pasaba 11 de 15 casos; la 1.1 y la 1.1.1, 15 de 16 (fallaba el peso posicional); la 1.1.2 pasa 18 de 18, incluida la carga con 1.1.2 de estimadores guardados con 1.1. La batería de Codex para el Pool sin huella da 14 de 14 con la 1.1.2.

La captura sustituye los ajustes que conoce, pero un entrenamiento que no pasara por sus envoltorios correría en silencio en modo reproducir. Para cerrar ese hueco la réplica se lanza con un segundo módulo, [`herramientas/centinela_ajustes/usercustomize.py`](../herramientas/centinela_ajustes/usercustomize.py), que Python carga después de la captura y que hace fallar las funciones con las que entrenan las cuatro bibliotecas de la receta: `Booster.update` de LightGBM, que corre en cada iteración; `_CatBoostBase._train` de CatBoost; `backward` de PyTorch, sin el cual la red no aprende; y `QuantileTransformer.fit` de scikit-learn. Cargar un modelo y predecir no pasa por ninguna de ellas. Los GLM por IRLS son numpy puro y no se pueden bloquear así; su control es que la réplica cargue exactamente los estimadores que guardó la corrida, ni uno más ni uno menos. Cada proceso que la captura identifica como nodo deja constancia del centinela en los eventos de ese nodo, de modo que se puede comprobar que estuvo activo. La batería [`herramientas/probar_centinela.py`](../herramientas/probar_centinela.py) pasa 21 de 21 casos: con el centinela, la réplica da los vectores guardados sin ningún bloqueo; fuera del modo reproducir no actúa; y cinco maneras de entrenar que esquivan la captura (la interfaz scikit-learn de LightGBM, `lightgbm.engine.train` llamado directamente, `CatBoostClassifier`, un bucle de PyTorch con `backward` y un `QuantileTransformer` ajustado aparte) corren en silencio con la captura sola y se detienen con el centinela.

## El reajuste completo

La corrida `repro_20261019T223638Z_d00a39dd` ejecutó `reproducir.py` 1.2 sin cambios, primero en modo `datos` desde los once originales y las tres decisiones congeladas y después en modo `componentes` con `--continuar-si-difiere`, con la captura en modo guardar. La etapa de datos (capa preparada, bases actuariales y F0) terminó conforme en dos minutos y dieciséis segundos. Los 36 nodos sumaron 10,6 horas de cómputo registrado entre las 22:48 UTC del 19 y las 11:06 UTC del 20. El entorno fue el de referencia (Ubuntu 24.04, Python 3.13.16, las versiones de [`entorno/entorno_referencia.json`](../entorno/entorno_referencia.json), dos núcleos), aunque en otra instancia de la nube: la de esta sesión es un Xeon a 2,80 GHz y los componentes se entrenaron en su día en uno de 2,10 GHz.

Los dos CSV de la receta salieron con el SHA-256 registrado: el de la mezcla, S30 `fd9528e0…3bc5`, y el de S22, `c21a02e1…41b0`. S22 es una mezcla anterior que la receta conserva como registro histórico: no forma parte de la entrega y se reproduce porque sale de la misma cadena. Por tipo de nodo, las 181 huellas verificadas quedaron así:

| Tipo | Nodos | Huellas verificadas | Iguales en contenido |
| --- | ---: | ---: | ---: |
| Variables | 1 | 3 | 3 |
| LightGBM | 15 | 83 | 71 |
| CatBoost | 8 | 64 | 64 |
| GLM gamma | 7 | 21 | 16 |
| Red Tweedie | 1 | 3 | 3 |
| Promedio de semillas | 2 | 3 | 3 |
| Mezclas S22 y S30 | 2 | 4 | 2 |
| Total | 36 | 181 | 162 |

Las 19 que difieren son estas, medidas contra los archivos históricos de `Modelos_claude` y `Modelos_claude_b`, cuyas huellas coinciden con las de la receta ([medida](../privado/corridas/repro_20261019T223638Z_d00a39dd/diferencias/medida_diferencias.json)):

| Nodo | Artefactos que difieren | Valores distintos | Diferencia relativa máxima |
| --- | --- | ---: | ---: |
| FSA_contents | v24 y predicción 2025 | 95.490 y 96.115 de unos 187.500 | 7,4e-16 |
| FSAP_buildings | parte V24 de accidental_damage y v24 | 217 y 18 de 184.001 | 1,0e-15 |
| FSAP2_buildings | partes V24 y 2025 de flood, v24 y predicción 2025 | entre 146 y 8.230 | 2,1e-15 |
| FSAP_contents | parte 2025 de flood y predicción 2025 | 187.075 y 88.291 de 187.498 | 3,9e-15 |
| FSAP2_contents | parte 2025 de accidental_damage y predicción 2025 | 828 y 155 de 187.498 | 1,1e-15 |
| FSAXc4_contents | predicción 2025 | 65.923 de 187.498 | 1,4e-15 |
| FSAS4_buildings | v24 y predicción 2025 | 90 y 1.434 | 5,9e-16 |
| B_FSAST_buildings_tendencia | v24 y predicción 2025 | 93 y 1.470 | 5,8e-16 |
| S22_claude_propio | predicción 2025 en Parquet | 92.763 de 626.639 | 8,4e-16 |
| S30_claude_b | predicción 2025 en Parquet | 69.225 de 626.639 | 9,5e-16 |

Un 1e-15 relativo son unas pocas unidades del último bit de un número en doble precisión, cuya resolución relativa es 2,2e-16. La suma de ningún artefacto cambia más de 1,7e-15 en términos relativos, y al escribir el CSV con seis decimales la diferencia desaparece. Las etiquetas y los identificadores de fila son idénticos en todos.

Los cinco nodos de origen son los frecsev2: frecuencia por peligro con LightGBM Poisson de árboles de una sola división, multiplicada por una severidad gamma del mismo tipo o constante. En los cuatro que guardan partes por peligro la diferencia está en un solo peligro, en FSAP2_buildings en sus dos etapas (FSA_contents no guarda partes), y FSAXc4, FSAS4, B_FSAST, S22 y S30 la heredan porque leen esas partes. La explicación está en la documentación de LightGBM: cuando no se fija `force_col_wise` ni `force_row_wise`, la biblioteca prueba las dos maneras de construir los histogramas y se queda con la más rápida ([parámetros de LightGBM](https://lightgbm.readthedocs.io/en/latest/Parameters.html)). Las dos suman los mismos gradientes en distinto orden, y con aritmética de coma flotante eso cambia el último bit de algunas hojas. La receta no fija ninguno de los dos, así que el modo depende de un cronómetro.

Lo comprobé con el modelo que difiere en FSAP_buildings, la frecuencia V24 de accidental_damage: dos semillas de 702 rondas sobre 523.725 filas, repetidas fuera de la receta y sin la captura. Con `force_row_wise` el vector sale idéntico bit a bit al histórico, con `force_col_wise` idéntico al de esta corrida, y en automático, con la máquina en reposo, eligió row-wise. Después repetí 18 veces la prueba de elección sobre el mismo conjunto, en tres variantes de seis: sin nada previo, calculando antes la clave de la captura y consolidando antes el marco de pandas. LightGBM eligió col-wise dos veces, en la primera y en la tercera variante, y las dos coinciden con una prueba anormalmente lenta (0,40 y 0,41 segundos frente a 0,11 a 0,17). Con la clave calculada antes eligió row-wise las seis veces ([diagnóstico](../privado/corridas/repro_20261019T223638Z_d00a39dd/diagnostico_lightgbm/diagnostico_lightgbm_fsap_buildings_ad.json)). Guardar los estimadores y el cambio de procesador quedan descartados como causa, porque en esta misma máquina y sin captura salen los dos resultados según el modo. Basta el ruido del cronómetro, y cualquier repetición de la receta puede encontrárselo en un nodo LightGBM cuyas dos pruebas tarden casi lo mismo.

Con el criterio fijado antes de correr, igualdad de contenido en las 181 huellas y SHA exacto de los dos CSV, el resultado es parcial: los CSV cumplen y 19 intermedios no. `reproducir.py` lo clasifica como `csv_iguales_con_diferencias_intermedias` y termina con código 3, que su propia documentación llama reconstrucción documentada, no acreditada. La causa explicada no convierte esas diferencias en igualdad. Lo que sí se puede afirmar es que el reajuste completo desde los originales reproduce los dos CSV byte a byte y todos los intermedios dentro de 3,9e-15 relativo. La causa está demostrada en el modelo de FSAP_buildings, y las demás diferencias tienen el mismo patrón: un peligro por nodo y el mismo orden de magnitud.

Las tres salidas que la receta excluye del cotejo quedaron así: `sel_CFS_motor.parquet` es idéntica al histórico incluso en bytes; `CFS_motor/v24.parquet` difiere en 127.252 de 254.698 valores con un máximo relativo de 7,7e-16, la misma medida que dio Codex en COD-IA-20261020T053207Z; y `CFS_motor_4s/v24.parquet`, que se calcula a partir de la anterior, difiere en 68.908 valores con un máximo de 4,4e-16. Las diez partes por peligro de CFS_motor que nunca tuvieron huella histórica solo se pueden comparar entre esta corrida y su réplica.

Durante la corrida pasaron cuatro cosas que deben constar. El contenedor de la nube se reinició a las 01:14 y a las 02:18 UTC del 20, las dos veces con CFS_motor en marcha. La primera relancé el orquestador con `--relanzar-parciales`, que apartó las salidas incompletas con sufijo; la segunda terminé el nodo con un segmento manual de 7.862 segundos (misma orden, mismo entorno, captura activa) usando la reanudación por peligro de `cat_frecsev.py`, y después `reproducir.py` lo verificó por huella. Al reajustar peligros tras el reinicio, CatBoost escribió siete `.cbm` con otros bytes para claves ya guardadas; la diferencia está solo en `model_guid` y `train_finish_time`, la exportación JSON sin esos campos es idéntica y la réplica carga el primero. Por último, `frecsev2.py` lee `cfg_total.json` de la carpeta de trabajo y `reproducir.py` 1.2 no lo coloca, así que copié el de `receta/especificaciones/` con su SHA (`aca601c6…643d`); `reproducir_capturado.py` hace hoy esa copia y la comprueba.

## La recaptura de los nodos guardados con la 1.0

Los doce nodos con ajuste que corrieron antes de la versión 1.1 (las seis selecciones, S03, S04b, S06c, S08h, S12h y CAT_motor, con 65 estimadores) quedaron guardados con claves de la 1.0, que la réplica no puede usar. Los volví a correr en una carpeta aparte con la captura 1.1.2, junto con el nodo de variables que los alimenta. Nueve nodos salieron iguales a sus huellas y cuatro difieren: S04b en la predicción 2025 de autos, S06c en V24 y 2025 de autos, y S08h y S12h solo porque reutilizan la parte de autos de S04b (182 filas, máximo relativo 8,0e-16). Es el mismo fenómeno de LightGBM en otros modelos, ahora en la misma máquina y pocas horas después: en la corrida principal esos nodos habían salido iguales. `reproducir.py` terminó la recaptura con código 3; la línea `rc=0` del guion que la encadenó es un error de ese guion, que leía el código después de llamar a `date`.

Como la recaptura no repite bit a bit, la réplica no usa sus estimadores. Usa los de la corrida principal, reindexados con la clave 1.1.2 que la recaptura calculó sobre las mismas entradas. Dentro de cada nodo los ajustes ocurren en el mismo orden en las dos corridas, así que el i-ésimo estimador de una se empareja con el i-ésimo de la otra exigiendo el mismo tipo, y las fichas de los 65 pares coinciden en rondas, filas, parámetros y mejor iteración. De los 65, 60 son además idénticos en contenido y 5 difieren por la elección de LightGBM: uno de S04b, tres de S06c y uno de S12h que no cambia ninguna salida ([informe](../privado/corridas/repro_20261019T223638Z_d00a39dd/reindexado/reindexado_informe.json)). Cada ficha reindexada conserva el archivo y el SHA de la 1.0, la clave y el SHA del recapturado y si son iguales. La réplica es la prueba de que el emparejamiento es correcto: con una pareja equivocada la clave no aparecería o la predicción saldría distinta.

## La réplica sin ajustes

La réplica corrió `reproducir_capturado.py reproducir` desde los once originales, en una carpeta nueva, con el centinela en `PYTHONPATH` y los estimadores montados con [`montar_paquetes.py`](../herramientas/montar_paquetes.py) desde los paquetes de la corrida y los reindexados ([recibo](../privado/corridas/repro_20261019T223638Z_d00a39dd/replica/recibo_reproducir_capturado.json)). Tardó 34 minutos: 3 minutos y 37 segundos la etapa de datos y 30 minutos los 36 nodos, frente a las 10,6 horas del reajuste. CFS_motor y CFS_motor_s23, que necesitaron 2,2 y 3 horas para ajustarse, se repitieron en 64 y 56 segundos.

[`comprobar_replay.py`](../herramientas/comprobar_replay.py), con la corrida principal como referencia, da conformes los 36 nodos ([resultado](../privado/corridas/repro_20261019T223638Z_d00a39dd/replica/comprobar_replay.json)):

- Hay 436 estimadores guardados (209 LightGBM, 113 CatBoost, 102 GLM, 9 redes y 3 codificadores de la red) y 436 cargas; cada nodo cargó exactamente las claves que tenía guardadas, ni una más.
- En modo reproducir no hubo ningún evento distinto de una carga: ningún guardado, duplicado, estimador ausente, Pool sin huella ni bloqueo del centinela.
- Los 34 procesos que la captura identifica como nodo tuvieron el centinela activo. Los dos de mezcla, S22 y S30, corren a través de `herramientas/ejecutar_csv_lf.py`, que la captura no reconoce como nodo, y por eso no dejan eventos; no tienen estimadores ni importan bibliotecas de aprendizaje, y el centinela se instala igual en un proceso sin nodo, como comprobé aparte.
- Las 194 salidas que declara la receta, incluidas las diez partes de CFS_motor sin huella histórica y las tres excluidas del cotejo, son idénticas en contenido y en bytes a las de la corrida principal.
- Los dos CSV tienen el SHA entregado.

Frente a las huellas históricas la réplica da lo mismo que el reajuste, 26 nodos iguales y los mismos 10 con las mismas 19 diferencias, como corresponde a estimadores que son los de esa corrida; `reproducir.py` vuelve a terminar con código 3 por ellas. Los paquetes guardados en el equipo del participante montan exactamente lo mismo: en la máquina virtual local salen los mismos 443 archivos de estimador (los 436 y los 7 duplicados que no se cargan) y los mismos 886 archivos, fuera de los registros de eventos, que en el montaje de la nube ([verificación](../privado/corridas/repro_20261019T223638Z_d00a39dd/replica/verificacion_montaje_dispositivo.json)).

## S41: el paso de nivel desde el reajuste

Reproducir el paso de nivel exige tres insumos:

- el CSV de la mezcla, que el reajuste ya devolvió con su SHA registrado;
- las seis puntuaciones públicas de las sondas, que son hechos de Kaggle con recibo ([recibos](../registro/sonda_nivel_D100_recibos.json)) y se usan tal como se registraron;
- las predicciones de 2024 de la mezcla, `predicciones_v23_v24_s30.parquet`, de donde sale el ruido σ.

Ese archivo no es salida de la receta y había que regenerarlo. Lo hizo la corrida `repro_s42_20261022T170245Z_c9ea2fc3`, preinscrita el 22 de octubre, que repitió todo el paso de nivel ([plan](../privado/corridas/repro_s42_20261022T170245Z_c9ea2fc3/PLAN_PREREGISTRO.md)).

Las predicciones de 2024 se regeneraron con `exportar_predicciones.py`, lanzado como en la línea B (`ejecutar_b.py`, con la regla de nivel s17 extendida), en dos carpetas de trabajo: la del reajuste completo y la de la réplica congelada. Los dos archivos salen idénticos byte a byte. Frente al histórico tienen las mismas 939.705 filas en el mismo orden y la etiqueta T0 y la reserva de caso idénticas. Hay 22.944 predicciones con diferencias en el último bit (22.912 de contenidos y 32 de edificios, en 2024; como máximo 7,9e-16 relativo), herencia de las 19 diferencias de LightGBM descritas arriba.

Después `sonda_nivel.py`, sin cambios, corrió en tres raíces mínimas con las puntuaciones registradas: con el archivo histórico como control, con el regenerado del reajuste y con el de la réplica. Lo que corresponde a S41 se extrajo en la corrida `repro_s41_20261023T145808Z_c8055dfc`, sin correr nada nuevo ([plan](../privado/corridas/repro_s41_20261023T145808Z_c8055dfc/PLAN_PREREGISTRO.md), [resultado](../privado/corridas/repro_s41_20261023T145808Z_c8055dfc/resultados/parte1_s41.json)).

| Corrida | Predicciones de 2024 | S41 con su SHA | Campos numéricos idénticos en las dos notas de D100 | Diferencia relativa máxima |
| --- | --- | --- | ---: | ---: |
| Control | históricas | sí | 125 de 142 | 2,1e-13 |
| Reajuste | regeneradas | sí | 118 de 142 | 6,3e-13 |
| Réplica congelada | regeneradas | sí | 118 de 142 | 6,3e-13 |

En el control los tres factores de S41 coinciden bit a bit. Con las predicciones regeneradas, el de contenidos difiere en la última cifra binaria (2,2e-16 relativo), sin que cambie ningún valor del CSV. Lo demás que difiere son cantidades que salen del bootstrap y de la forma cerrada (σ, Z, el público esperado y las ganancias esperadas); las mayores diferencias relativas están en las ganancias, que son restas entre números muy próximos. Con el criterio preinscrito, las tres corridas quedan como «reproducido con diferencias de último bit». Una hipótesis no se cumplió: con el archivo histórico, el control tampoco repite σ y Z bit a bit. Eso apunta al entorno numérico, es decir, a la versión o al procesador por el orden de las sumas, y no a los datos.

También se comprobó la herencia:

- Dentro de cada ramo, S41 es la mezcla por su factor, con una diferencia máxima de 5e-7 CU por fila, que es el redondeo a seis decimales del CSV.
- El orden de los periodos por coste predicho es idéntico y no aparecen empates nuevos.
- Por tasa por año expuesto solo se invierten pares cuyas tasas en la mezcla difieren menos que una unidad de redondeo.
- Los totales por ramo coinciden con los de la resolución.

## Qué decidió el participante y qué queda abierto

El 23 de octubre, antes del cierre, el participante marcó S41 en Kaggle como entrega final (CIE-D103-20261023, [registro](../registro/decision_marca_final_S41_20261023.json)). Lo hizo después del aviso de la batería de sensibilidad, cuya regla de alarma, fijada antes de calcular, se cumplió a favor de S41 ([`SENSIBILIDAD_S43.md`](SENSIBILIDAD_S43.md), N05). Las decisiones del 20 de octubre sobre esta reproducción no cambian.

El 20 de octubre a las 15:21 UTC el participante resolvió los cuatro puntos que esta reproducción dejaba en sus manos ([registro](../registro/decisiones_participante_20261020.json)).

La independencia no se va a acreditar: no habrá una repetición por otro operador con el kit de la sección siguiente. La reproducción queda como hecha por Claude en la nube de Claude, y así se declara; corresponde al hallazgo GOV-003 del enjambre. El kit se conserva por si esa decisión cambia.

Tampoco se exige que un reajuste futuro coincida bit a bit. La receta no tiene un error: LightGBM elige un modo de cálculo según un cronómetro y la receta no lo fija. Fijar `force_row_wise=True` quitaría esa dependencia, pero en la parte 1 sería un cambio de receta posterior a la entrega: habría que regenerar huellas y volver a correr unas once horas, y la receta dejaría de ser el código que produjo la mezcla de la que sale S41. Como las diferencias no pasan de 3,9e-15 relativo y desaparecen en el CSV, coincido con el participante en que no compensa. Para la parte 2, donde no hay huellas históricas que conservar, propongo fijar el modo desde el primer modelo LightGBM; está pendiente de que el participante lo confirme.

La suficiencia de reservas queda como limitación del ejercicio, que es el hallazgo MOD-002: sigue valiendo la acotación de [`RESERVAS_ACOTACION.md`](RESERVAS_ACOTACION.md), con incertidumbre material en los tres ramos y el supuesto S3 sin adoptar. El 23 de octubre, después de que Codex pidiera una valoración expresa para S41 (COD-VAL-20261023T1523-S41-RESERVAS), el participante mantuvo esa decisión para la entrega final ([registro](../registro/decision_reservas_S41_20261023.json)).

GOV-008 quedó aceptado en el alcance de la corrección técnica de la captura 1.1.2, que Codex había comprobado en COD-VAL-20261020T0642-GOB. El recorrido afectado es la réplica de este documento, con sus 436 cargas por clave exacta ([decisión](../registro/decision_GOV008_20261020.json)).

Sigue abierta la revisión humana general del proyecto.

La réplica vuelve a calcular, con fórmulas cerradas y los mismos datos, tres estimaciones que no son estimadores de la capa: los factores de nivel de las mezclas, f23 y f24, que son la razón `sum(y/sqrt(mu))/sum(sqrt(mu))` sobre V23 y V24; la pendiente log-lineal de la severidad media anual en la línea B (`numpy.polyfit`); y la cola de los factores de desarrollo en la etapa de datos (`numpy.polyfit`). Ninguna tiene iteraciones ni aleatoriedad, y sus resultados entran en las huellas de los nodos que los contienen.

Las matrices de variables (`feat_*.parquet`, unos 0,3 GB) no van en los paquetes por tamaño; se regeneran con el nodo de variables, que es determinista y coincide con sus huellas en las tres corridas.

## Cómo repetirlo en otro equipo

Esta parte queda para quien quiera hacer la reproducción independiente, si la decisión del participante cambia. Hacen falta Python 3.13 con las versiones de [`entorno/entorno_referencia.json`](../entorno/entorno_referencia.json) (LightGBM 4.7.0, CatBoost 1.2.10, scikit-learn 1.9.1 y PyTorch 2.14.1; la red corre en CPU), dos núcleos y 8 GB de memoria. Los once Parquet del concurso los descarga cada operador de Kaggle, porque las reglas no permiten redistribuirlos, y la carpeta `Hackaton/Semana 1` del proyecto aporta las tres listas congeladas que lee la etapa de datos. Todas las órdenes se lanzan desde la raíz del repositorio. En PowerShell, `PYTHONPATH=...` se escribe `$env:PYTHONPATH="..."` en una línea previa.

El recorrido que cuenta como reproducción independiente es el reajuste completo, de los originales a los dos CSV, en carpetas nuevas:

```
python herramientas/reproducir_capturado.py guardar --originales=<Semana 1>/Datos --decisiones=<Semana 1> --trabajo=<carpeta nueva> --capturas=<otra carpeta nueva> --continuar-si-difiere
```

Con dos núcleos tarda unas once horas. Si el proceso muere a mitad, la misma orden con `--relanzar-parciales` aparta lo incompleto y sigue; los nodos ya terminados se saltan después de comprobar sus huellas. El código 0 significa que las 181 huellas y los dos SHA coinciden; el 3, que los CSV coinciden y algún intermedio no, y entonces `registro.jsonl` dice cuál. Por lo visto aquí, lo esperable es un 3 con diferencias del orden de 1e-15 en algún nodo LightGBM, y lo que procede es medirlas, no darlas por buenas.

La réplica desde los estimadores congelados es más corta y responde a otra pregunta: si con estos estimadores y este código salen exactamente los mismos CSV sin ajustar nada. Primero se montan los estimadores desde los paquetes de la corrida, que están en `privado/corridas/repro_20261019T223638Z_d00a39dd/` dentro de la carpeta común; los reindexados van detrás para que sustituyan, nodo a nodo, a lo guardado con la 1.0:

```
python herramientas/montar_paquetes.py --paquetes=<corrida>/nodos,<corrida>/reindexado --destino=<capturas montadas>
PYTHONPATH=herramientas/centinela_ajustes python herramientas/reproducir_capturado.py reproducir --originales=<Semana 1>/Datos --decisiones=<Semana 1> --trabajo=<carpeta nueva> --capturas=<capturas montadas> --continuar-si-difiere
python herramientas/comprobar_replay.py --trabajo=<carpeta de la réplica> --capturas=<capturas montadas> --salida=<json>
```

`montar_paquetes.py` comprueba cada parte, cada paquete y cada archivo contra su manifiesto antes de escribirlo, y [`inventario_estimadores.py`](../herramientas/inventario_estimadores.py) lista después los 436 estimadores con su tipo, formato, SHA y versión de captura. `comprobar_replay.py` exige que en modo reproducir no haya más eventos que cargas, que cada nodo cargue exactamente los estimadores guardados para él, que el centinela haya estado activo en todos los procesos y que los dos CSV tengan el SHA entregado. Sin `--referencia`, además, que cada nodo coincida con sus huellas históricas; en esta réplica eso no se cumple por diseño en los diez nodos que heredan las diferencias de LightGBM, porque los estimadores congelados son los de esta corrida. Con `--referencia` apuntando a una carpeta de trabajo de la corrida guardar (por ejemplo, la que `montar_paquetes.py --solo=todo` reconstruye desde los paquetes, acompañada de `--registro-referencia=<corrida>/registro_corrida_principal.jsonl`), compara cada salida declarada con la de esa corrida, y los nodos que difieren de la historia pasan si difieren igual que la corrida que guardó sus estimadores. Si Python corre en un entorno virtual sin paquetes del sistema, no carga `usercustomize` y el centinela no se activa; el comprobador lo detecta y marca esos procesos como no conformes.

Para que cuente como independiente, quien la haga debería devolver `recibo_reproducir_capturado.json`, `registro.jsonl` y, en la réplica, la salida de `comprobar_replay.py`, con su sistema operativo, procesador y versiones.

El paso de nivel de S41 se repite después de cualquiera de los dos recorridos, con la carpeta de trabajo que dejó. Primero las predicciones de 2024, en una copia de esa carpeta porque la orden escribe en `work/` (en la nube se usaron enlaces y una copia de `nivel_inestable_b.json`):

```
HAKATON_SEMANA1="<trabajo>/proyecto/Hackaton/Semana 1" MODELOS_WORK=<copia>/work MODELOS_CLAUDE=src/modelos PYTHONHASHSEED=0 python "<Semana 1>/Modelos_claude_b/ejecutar_b.py" exportar_predicciones s30 "S30=receta/especificaciones/spec_s30.json@motor:1.09:0.95,contents:1:0.95@s17"
```

Después se arma una raíz mínima con `RUTAS_PROYECTO.json`, una copia de `herramientas/sonda_nivel.py` en `Hackaton/Repositorio_IAA2026/herramientas/`, los tres `test_*.parquet` en `Hackaton/Semana 1/Datos/`, el CSV de S30 en `Hackaton/Semana 1/Envios/archivos/` y el parquet regenerado en `Hackaton/Semana 1/Modelos_claude_b/experimentos/`. El script se copia y no se enlaza, porque localiza la raíz subiendo desde su propia ruta:

```
python <raíz>/Hackaton/Repositorio_IAA2026/herramientas/sonda_nivel.py generar
python <raíz>/Hackaton/Repositorio_IAA2026/herramientas/sonda_nivel.py resolver --s30 0.12996 --motor 0.12954 0.12906 --buildings 0.12873 0.13018 --contents 0.12929 0.13011
```

`resolver` escribe `S41_nivel_credibilidad.csv` en `Hackaton/Semana 1/Envios/archivos/` de la raíz mínima, y su nota en `Hackaton/Semana 1/Envios/`. Los comparadores con el registro (`comparar_parquet.py` y `comparar_notas.py`) y las órdenes usadas en la nube (`regenerar.sh` y `montar_y_correr_sondas.sh`, cuya última orden, `revisar`, no interviene en S41) están en `scripts/` de la corrida `privado/corridas/repro_s42_20261022T170245Z_c9ea2fc3/`. La extracción de lo que corresponde a S41 (`parte1_s41.py`) está en `scripts/` de `privado/corridas/repro_s41_20261023T145808Z_c8055dfc/`.

## Archivos y huellas

| Archivo | SHA-256 |
| --- | --- |
| `reproducir.py` 1.2 (sin cambios) | `a346d125…5de17` |
| `herramientas/captura_modelos/captura.py` 1.1.2 | `3ae39d78…32f0` |
| `herramientas/centinela_ajustes/usercustomize.py` 1.0 | `5e67930f…e20b` |
| `herramientas/reproducir_capturado.py` (con las guardas de Codex) | `7bdf635b…aa37` |
| `herramientas/montar_paquetes.py` | `40959976…7f76` |
| `herramientas/comprobar_replay.py` | `2a9fcfdd…cfa0` |
| `herramientas/inventario_estimadores.py` | `8b525789…2f2d` |
| `herramientas/probar_centinela.py` | `de58f0be…49a9` |
| `privado/corridas/repro_20261019T223638Z_d00a39dd/evidencia_20261020.tar.gz` (198 archivos, con manifiesto) | `05b2f22f…e663` |
| `herramientas/sonda_nivel.py` (sin cambios) | `d6cfe805…a7a7` |
| `Semana 1/Modelos_claude_b/ejecutar_b.py` (sin cambios) | `e70f5a08…c893` |
| `src/modelos/exportar_predicciones.py` (sin cambios) | `3f758d6d…262d` |
| `privado/corridas/repro_s42_20261022T170245Z_c9ea2fc3/PLAN_PREREGISTRO.md` | `c9ea2fc3…13ff` |
| `…/regenerado/predicciones_v23_v24_s30.parquet` (reajuste y réplica) | `4e80bde3…3d80` |
| `…/corrida_s42_c9ea2fc3.tar.gz` (41 archivos, con manifiesto) | `b7721c7d…30e8` |
| `privado/corridas/repro_s41_20261023T145808Z_c8055dfc/PLAN_PREREGISTRO.md` | `c8055dfc…81e3` |
| `…/corrida_s41_c8055dfc.tar.gz` (6 archivos, con manifiesto) | `73397bc9…547d` |
| `registro/sonda_nivel_D100_preinscripcion.json` | `a4c0e504…e9c7` |
| `registro/sonda_nivel_D100_resolucion.json` | `aa9c438b…81a7` |

En la carpeta de la corrida, fuera de Git, están además los 36 paquetes por nodo con sus manifiestos (`nodos/`), los 12 de estimadores reindexados con su informe (`reindexado/`), la réplica (`replica/`), la medida de las diferencias (`diferencias/`), el diagnóstico de LightGBM (`diagnostico_lightgbm/`), las pruebas de la captura y del centinela (`pruebas_captura/`), el registro completo de la corrida principal y su resumen por nodo. El recibo con todas las huellas es [`registro/recibo_reproduccion_completa_20261020.json`](../registro/recibo_reproduccion_completa_20261020.json); se refiere a la versión de este documento anterior a las decisiones del participante (SHA `fa0c2a8a…cc11`). Las decisiones están en [`registro/decisiones_participante_20261020.json`](../registro/decisiones_participante_20261020.json) y [`registro/decision_GOV008_20261020.json`](../registro/decision_GOV008_20261020.json), con el evento original en `privado/decisiones_participante_20261020/`. La reproducción del paso de nivel de S41 tiene su recibo, [`registro/recibo_reproduccion_s41_20261023.json`](../registro/recibo_reproduccion_s41_20261023.json). Este documento se reescribió el 23 de octubre en torno a la entrega final. Sus versiones anteriores, que también trataban candidatos que no se eligieron, se conservan: la del 20 de octubre en Git (commit `0ade351`), la del 22 en `privado/trazabilidad/reproduccion_s43_20261023/` y la de la mañana del 23 en `privado/trazabilidad/reproduccion_s41_20261023/`. Los recibos `registro/recibo_reproduccion_s42_20261022.json` y `registro/recibo_reproduccion_s43_20261023.json` registran sus huellas.
