# Línea ML independiente de la semana 2: transferencia del mercado desarrollado al emergente

Autor: Claude, sesión «ML independiente» abierta por el participante el 23 de octubre de 2026 a las 21:30 de Bogotá. Corte de este informe: 24 de octubre de 2026, 15:30 UTC. Todo el código, las etiquetas y los modelos se escribieron desde los Parquet originales; no se usó ninguna predicción, factor ni código de otras líneas. Nada se envió a Kaggle.

![Flujo de la receta final](figuras/f00_flujo_receta.png)

## 1. Qué se entrega y por qué

El encargo fue montar modelos de aprendizaje automático para el mercado emergente con lo aprendido en las dos semanas, hasta tener uno completo, validado y calibrado, con libertad para probar transformers y ajuste fino. Se probaron catorce modelos (más sus variantes) y tres mezclas bajo un protocolo escrito antes de ajustar nada (`PREINSCRIPCION.md`, SHA-256 cf3e5d97…ff7e, en el equipo desde las 02:45 UTC del 24 de octubre).

El modelo elegido es T2b: un LightGBM Tweedie con potencia 1,5 entrenado en el mercado desarrollado con las variables que existen en los dos mercados, llevado al emergente sin reentrenar, con el nivel de cada ramo estimado en el emergente 2023-2024. Es la versión más sencilla de lo que en redes se llama aprendizaje por transferencia: el mercado grande aporta la forma del riesgo (quién es más caro que quién) y el mercado pequeño aporta el nivel (cuánto cuesta el promedio).

| Pieza | Valor |
| --- | --- |
| Archivo | `prediccion_2025_mlind.csv`, 209.063 filas en el orden de la plantilla, todas positivas |
| SHA-256 | d261388c7e4d5dcc… (completo en `produccion_2025.json`) |
| Total 2025 | 70.822.703 CU: autos 43.202.961, edificios 22.147.741, contenidos 5.472.001 |
| Tasa por año de exposición | autos 546,8; edificios 467,5; contenidos 92,7 |
| D² en 2023 (validación cruzada por cliente) | 0,1233 con la calibración final |
| D² en 2024 (abierto una vez) | 0,1253 |
| Referencia: tasa por ramo | 0,0631 en 2023 y 0,0732 en 2024 |

La ventaja frente a la tasa por ramo es +0,0602 en 2023 (IC95 por cliente [+0,0436; +0,0765]) y +0,0521 en 2024 ([+0,0348; +0,0729]). Frente al mejor modelo entrenado solo con datos emergentes (LightGBM T1wp) la ventaja es +0,0336 en 2023 ([+0,0200; +0,0474]) y +0,0264 en 2024 ([+0,0128; +0,0404]). Las cifras salen de `bootstrap_final.json`, con 1.000 remuestreos de clientes.

## 2. Datos y etiquetas

### 2.1 Qué se limpió

Las reglas son las ya conocidas en el proyecto, comprobadas otra vez con código propio (`preparar_datos.py`): exposición recalculada como días inclusivos entre 365 en todas las filas, `customer_id` de autos del desarrollado rellenado a ocho dígitos, los 604 duplicados del desarrollado retirados (los `claim_id` de once caracteres), capital de hogar dividido entre mil cuando supera 5 millones (edificios) o 2 millones (contenidos), lo que afecta a 53 y 57 filas de entrenamiento emergente y a 104 y 135 de test, y construcción armonizada (t y w del desarrollado son madera, como WOD del emergente). `customer_service_contacts` y `renewal_decision` quedan fuera de los predictores.

La etiqueta observada T0 suma `incurred_to_date − recoveries` de los siniestros no rechazados con ocurrencia dentro del periodo, por póliza y ramo. En el emergente suma 27.997.991,57 CU en 109.296 periodos de entrenamiento; quedan 36 siniestros sin periodo, todos anteriores a la primera fila de su póliza. Una revisión independiente (subagente, sección 9) recalculó T0 desde los originales y obtuvo diferencia cero.

### 2.2 Completitud de reporte

Los siniestros de 2024 todavía se están reportando. En lugar de inflar la etiqueta, cada fila lleva un factor c que dice qué fracción de su coste último ya debería estar reportada al 31-12-2024. Se calcula con la distribución del retraso de reporte ponderada por coste, por ramo y peligro, estimada en los siniestros del desarrollado ocurridos en 2021 (más de tres años de observación), y con el peso de cada peligro en el coste emergente. El modelo se ajusta con desplazamiento log(exposición × c) y predice el coste último; para comparar con lo observado se multiplica por c.

![Completitud](figuras/f01_completitud_reporte.png)

La completitud media de 2024 en el emergente es 0,8027 en autos, 0,9423 en edificios y 0,9636 en contenidos; la de 2023, 0,9745, 0,9960 y 0,9961. Las lesiones corporales mandan en autos (solo el 37 % de su coste se reporta en 90 días y el 83 % en un año). El retraso emergente de 2023, comparado con el del desarrollado a 30, 90 y 180 días, coincide en los quince peligros dentro de unos puntos (`preparacion.json`, clave `contraste_reporte_emergente_2023`). La revisión independiente encontró que en autos el patrón podría quedarse un 3 % corto para 2024; se declara como límite.

### 2.3 Qué cambia de 2024 a 2025

La cartera de 2025 es casi toda nueva: el nuevo negocio pasa del 6-9 % de la exposición en 2023-2024 al 77 % en 2025, y entre el 88 % y el 91 % de ese negocio empieza en enero. Un clasificador que distingue filas de 2023 de filas de test separa con AUC 0,94 en autos y 0,92 en hogar; las variables que más lo delatan son `new_business`, `renewal_count` y el mes de inicio. El canal no cambia (70 % corredor en los dos periodos).

![Desplazamiento](figuras/f02_desplazamiento_cartera.png)

Ese clasificador da además los pesos de un segundo criterio de validación (D² ponderado a la mezcla de 2025). La mezcla de peligros también cambia entre mercados: incendio pesa el 44,8 % del coste de edificios emergente frente al 23,0 % del desarrollado (`preparacion.json`, pesos por peligro).

## 3. Protocolo

| Fase | Entrenamiento emergente | Desarrollado | Evaluación |
| --- | --- | --- | --- |
| DEV | 2023, cinco pliegues por cliente | 2021-2023 | fuera de pliegue en 2023 |
| HOLD | 2023 completo | 2021-2023 | 2024, abierto una sola vez a las 14:36 UTC con la lista congelada a las 14:19 |
| PCV | 2023-2024, cinco pliegues por cliente | 2021-2024 | fuera de pliegue, solo para fijar la calibración de producción |
| PROD | 2023-2024 | 2021-2024 | test 2025, sin enviar |

La métrica es D² Tweedie 1,5 sobre los tres ramos concatenados, siempre con la observación frente a μ × c. Cada diferencia lleva un intervalo por remuestreo de clientes. La regla de selección, fijada antes de empezar: gana el mejor D² de DEV, pero un candidato más complejo solo desplaza a uno más simple si mejora al menos 0,001, y el elegido debe superar al mejor modelo solo emergente también en el cuerpo de la distribución y en la mezcla de 2025. Cada experimento quedó declarado antes de correrlo en `experimentos.jsonl` (diecinueve entradas), también los adversos y las desviaciones.

## 4. Los modelos probados

Las familias, en orden de complejidad:

- Sin transferencia: R0 tasa por ramo; G1 GLM Tweedie con variables categorizadas y ridge; T1 LightGBM solo emergente (con variantes de marketing, prima escrita y `make_model`).
- Árboles con transferencia: T2 y T2b (LightGBM del desarrollado; T2b con hiperparámetros elegidos en una rejilla validada solo en el desarrollado), T3 (T2b más ajuste fino por boosting residual en el emergente), T4 (modelo conjunto de los dos mercados con indicador), T5 (GLM ridge de adaptación sobre T2), T6 (un modelo por peligro con nivel emergente por peligro).
- Redes: un FT-Transformer (Gorishniy et al., 2021) con tokens por variable, dos bloques de atención y pérdida Tweedie 1,5 con desplazamiento. N1 se entrena desde cero en el emergente; N2a y N2b se preentrenan en el desarrollado y se ajustan en el emergente (completo con penalización L2-SP hacia los pesos preentrenados, o solo la cabeza y los tokens nuevos de región, género y autónomo); N3 es una red residual tipo CANN que aprende correcciones sobre el logaritmo de T2b, con la cabeza inicializada en cero.
- Mezclas convexas por ramo (E1 a E3), con pesos cruzados por pliegue.

Dos calibraciones de nivel acompañan a cada uno: C1, un factor por ramo, y C2, un factor por ramo y nuevo negocio con credibilidad (Z = n/(n + 200) siniestros). Ambas se estiman en los pliegues que no se evalúan.

## 5. Resultados en 2023 (DEV)

![Candidatos DEV](figuras/f03_dev_candidatos.png)

| Modelo | D² C1 | D² C2 | Cuerpo (C2) | Mezcla 2025 (C2) |
| --- | --- | --- | --- | --- |
| R0 tasa por ramo | 0,0631 | 0,0687 | 0,0734 | 0,0865 |
| G1 GLM solo emergente | 0,0776 | 0,0771 | 0,0820 | 0,0994 |
| T1wp LightGBM solo emergente | 0,0896 | 0,0923 | 0,0969 | 0,1133 |
| T2b transferido | 0,1233 | 0,1264 | 0,1219 | 0,1514 |
| T3bwp T2b + ajuste fino por boosting | 0,1248 | 0,1274 | 0,1235 | 0,1520 |
| N1 transformer desde cero | 0,0757 | 0,0771 | 0,0813 | 0,0984 |
| N2a transformer preentrenado y ajustado | 0,1093 | 0,1106 | 0,1094 | 0,1333 |
| N3 transformer residual sobre T2b | 0,1221 | 0,1251 | 0,1213 | 0,1530 |
| E1 mezcla T2b + T3bwp + N3 | 0,1206 | 0,1236 | 0,1191 | 0,1521 |

La tabla completa, con los 17 candidatos y sus intervalos frente a T2b, está en `tabla_dev.csv`. Tres lecturas:

1. La transferencia es la palanca grande. Todo lo que parte del desarrollado supera a todo lo que parte de cero, en árboles y en redes.
2. El preentrenamiento funciona también para el transformer: N2a supera a N1 en +0,0335 (IC95 [+0,0166; +0,0505]). Aun así, la red preentrenada queda por debajo del LightGBM transferido, como suele pasar en datos tabulares.
3. Afinar sobre T2b casi no añade. T3bwp gana +0,0009 con C2 (IC95 [−0,0024; +0,0041]), por debajo del umbral de 0,001, y la red residual N3 pierde −0,0013 ([−0,0044; +0,0018]). Por la regla, el elegido de DEV fue T2b con C2 (C2 ganaba a C1 por +0,0031).

Los resultados adversos también se conservan: el modelo conjunto T4 se desnivela en edificios (D² 0,0991 con C2), el modelo por peligro T6 pierde en edificios porque el nivel de incendio emergente descansa en 49 siniestros (0,1023), y la adaptación GLM T5 no mejora a su base (0,1181).

## 6. Resultados en 2024 (HOLD)

![DEV frente a HOLD](figuras/f04_dev_frente_hold.png)

En 2024 el orden grueso se repite: los árboles con transferencia y la red residual quedan entre 0,1223 y 0,1253, la red preentrenada en 0,1085 y los modelos que parten de cero entre 0,0697 y 0,0989. El preentrenamiento del transformer vuelve a valer +0,0387 ([+0,0234; +0,0594]). Dentro del grupo de arriba las diferencias son ruido.

HOLD sirvió además para probar dos reglas, y las dos fallaron:

- La tendencia preinscrita (pendiente anual del desarrollado, +8,2 % en autos y +4,2 % en hogar para HOLD) baja el D² de 2024: −0,0013 con C2 (IC95 [−0,0026; +0,0001]) y −0,0016 con C1 ([−0,0029; −0,0002]). La pérdida viene sobre todo de edificios, cuyo 2024 quedó muy por debajo de 2023.
- C2, el ajuste del nuevo negocio, pasa de ganar 0,0031 en 2023 a perder 0,0017 en 2024 ([−0,0039; +0,0009]). El motivo se ve en la figura: el exceso de coste del nuevo negocio de autos frente al modelo transferido fue 1,55 en 2023 y 1,00 en 2024, con unos 300 siniestros cada año y un coste por siniestro con coeficiente de variación cercano a 4. Una K de 200 siniestros era demasiado optimista para cocientes de coste tan ruidosos. Una prueba cruzada entre años (factor estimado en un año y aplicado al otro) da credibilidad óptima de 0,1 en autos y 0 en contenidos; en edificios sale 1, con un efecto despreciable (`credibilidad_entre_anios.json`).

![Nuevo negocio por año](figuras/f06_nuevo_negocio_por_anio.png)

Por eso la receta de producción usa C1 y no aplica tendencia. La decisión se tomó después de abrir 2024 y está declarada como desviación (A03 en `experimentos.jsonl`); el D² de 2024 de la receta final, 0,1253, ya no es una estimación ciega y se informa como tal.

## 7. Calibración

La calibración se revisa con las predicciones fuera de pliegue de 2023-2024 (fase PCV), que es lo más parecido a la producción.

![Calibración por deciles](figuras/f05_calibracion_deciles_pcv.png)

La descomposición de Murphy separa la desviación media en incertidumbre, discriminación y descalibración, usando como recalibración la regresión isotónica con pesos e^0,5 (la que corresponde a Tweedie 1,5). La descalibración es el 0,9 % de la desviación en autos, el 2,3 % en edificios y el 1,2 % en contenidos. Como la isotónica se ajusta en la misma muestra, esas cifras son una cota superior. Los cocientes observado/esperado por decil no muestran pendiente: en autos van de 0,82 a 1,26 y en edificios de 0,75 a 1,46, con el vaivén que se espera de unos pocos cientos de siniestros por decil.

Dos diagnósticos más, sin efecto en la entrega:

- Forma: comprimir las relatividades transferidas con un exponente 0,90 mejoraría el D² en la muestra en 0,0007 (autos) y 0,0012 (edificios). Es poco y la lección de la semana 1 fue no trasladar parámetros de forma afinados en los cortes, así que se deja en 1.
- Nivel frente a balance: el factor Tweedie que maximiza la métrica no cuadra totales. En el fuera de pliegue 2023-2024 lo observado es el 95,8 % de lo predicho en autos, el 96,8 % en edificios y el 100,8 % en contenidos. La entrega a Kaggle usa el factor de la métrica; la prima comercial usa el nivel de balance (sección 8).

## 8. Producción 2025 y su sensibilidad

![Sensibilidad](figuras/f07_sensibilidad_2025.png)

| Variante | Total 2025 (CU) | Autos | Edificios | Contenidos |
| --- | --- | --- | --- | --- |
| Final: T2b + C1, sin tendencia | 70.822.703 | 43.202.961 | 22.147.741 | 5.472.001 |
| C2 (nuevo negocio con credibilidad) | 82.664.944 | 55.094.318 | 21.811.421 | 5.759.205 |
| C1 con tendencia | 76.849.247 | 46.810.394 | 24.216.656 | 5.822.197 |
| Preinscrita (C2 + tendencia) | 89.671.375 | 59.694.675 | 23.848.919 | 6.127.781 |
| T2c (sin variables de historia) + C1 | 70.130.508 | 43.029.463 | 21.622.114 | 5.478.931 |

La tasa de autos de 2025 (546,8) queda por encima de la observada en 2023 y 2024 (444,0 y 476,7). No es un nivel distinto: el modelo del desarrollado ve más riesgo en la cartera nueva (la relatividad media de autos sube un 12,6 % de 2024 a 2025, casi todo por el nuevo negocio). En edificios la tasa prevista (467,5) cae entre un 2023 alto y un 2024 bajo (516,3 y 325,5). Contenidos es estable (92,7 frente a 91,5 y 90,1).

La mayor incertidumbre es el nivel del nuevo negocio de autos: con C2 el total sube un 16,7 %. Con el 77 % de la cartera nueva, un envío de prueba al tablero público mediría ese nivel mejor que cualquier dato de entrenamiento; esta línea no envía y deja la decisión al participante.

### Prima comercial de las 20 pólizas de referencia

Con los supuestos de `expenses.parquet`, P = [R (1 + 0,12 en hogar) + 85 × exposición] / (1 − 0,15 − comisión − 0,08 − 0,08), con comisión 0,20 para corredor y 0 para directo, y R la predicción llevada al nivel de balance. Las veinte filas están en `prima_comercial_20.csv` con cada componente. La prima comercial media sale en 1.161,6 CU en autos, 985,5 en edificios y 260,2 en contenidos, frente a una prima escrita media de 682,3, 247,8 y 138,2. La distancia viene de la estructura de gastos (con corredor, el denominador es 0,49) y de que la prima de riesgo de edificios ya supera a la escrita en el agregado de 2025 (razón 1,10).

## 9. Revisión independiente

Un subagente sin acceso a las conclusiones revisó código, etiquetas y predicciones con código propio (informe completo resumido en el registro de la sesión). No encontró errores. Confirmó T0 con diferencia cero, la exposición, el corte del capital, la ausencia de fugas directas, el cruce por pliegues, la métrica (D² propio igual al del código) y el CSV. Dejó cinco avisos, todos recogidos:

- Los valores ausentes de la historia de 12 meses delatan el primer año de datos de cada mercado, y T2b aprendió ese nivel: en HOLD mete una tendencia implícita de unos +6 % en autos y en 2025 unos +3 %. Se probó T2c, sin esas variables, con una regla fijada antes (A04): pierde 0,0019 en DEV, así que T2b se queda; su total 2025 difiere un 1 % y figura en la tabla de sensibilidad.
- En DEV el clima persistente de 2023 se aplica a pólizas de 2023, lo que hace a DEV algo optimista; HOLD está limpio.
- Los márgenes de selección entre los modelos de arriba son del orden del ruido del nivel.
- La decisión de A03 es posterior a HOLD.
- El nivel 2025 depende del nuevo negocio, que pesa poco en el entrenamiento.

## 10. Límites

- Una sola valoración (31-12-2024): ni la suficiencia de las reservas de caso ni el desarrollo posterior al reporte se pueden medir; se asume reserva sin sesgo.
- El nivel de edificios depende de incendio: en el emergente pasó de 49 siniestros en 2023 a 21 en 2024 y el cociente observado/esperado del ramo fue 1,22 y 0,73. El nivel elegido es la media de los dos años.
- `occupation` es la variable con más ganancia de T2b en los tres ramos, pero su efecto univariante en hogar es débil en el desarrollado (frecuencia relativa entre 0,94 y 1,05 en edificios) y casi no se correlaciona entre mercados (0,25 en edificios, 0,17 en contenidos; 0,74 en autos). Parte de esa ganancia puede ser sobreajuste de la variable categórica; una ablación es el siguiente paso natural.
- La cartera del corredor puede no comportarse como el nuevo negocio orgánico. Ningún dato de entrenamiento lo identifica.
- Las redes se entrenaron en dos núcleos de CPU con unas 1.000 a 1.700 filas por segundo; con más cómputo se podría explorar arquitectura y búsqueda de hiperparámetros, que aquí quedaron fijas.

## 11. Cómo repetirlo

En `codigo/`, con Python 3.13, LightGBM 4.7, scikit-learn 1.9, pandas 3.0, PyTorch 2.14 y los Parquet en `datos/emerging` y `datos/developed` (huellas en `comun.py`, comprobadas al empezar):

```
python preparar_datos.py ; python historia.py
MLIND_BACKBONE=T2b python gbm.py dev ninguno      # y hold, pcv, prod
python glm.py dev ; python t4.py dev ; python peligros.py dev ; python adaptacion.py dev
python red.py pre dev motor ; python red.py fino dev motor N2b,N3,N2a,N1   # por ramo
python tabla_dev_final.py ; python abrir_hold.py ; python tendencia.py prod
python produccion.py ; python prima_comercial.py ; python calibracion.py pcv ../entrega/receta_final.json
python verificar_informe.py
```

Los Parquet por fila (bases, predicciones, modelos) quedan fuera de Git, en `Repositorio_IAA2026/privado/semana2/claude_ml_independiente_20261023/`.
