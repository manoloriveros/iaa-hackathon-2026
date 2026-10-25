# Evolución de MLind: troncos nuevos y mezcla v2

Pedido del participante, 24 de octubre de 2026 a las 16:40 UTC: seguir mejorando la precisión del modelo sin sondas del tablero. Cada experimento quedó declarado en `experimentos.jsonl` antes de correrlo (E14 a E24). Una revisión independiente (A05, 18:10 UTC) encontró cinco defectos, y este documento ya los incorpora. No se envió nada a Kaggle.

![Troncos frente a T2b](f12_troncos.png)

## Un criterio nuevo: DES24

Las comparaciones en el emergente tienen poca potencia. En 2023 hay unos 3.000 siniestros y en edificios mandan unos pocos incendios. Por eso añadí DES24: cada tronco se entrena en el desarrollado 2021-2023 y se mide en el desarrollado 2024, fuera de tiempo, con 184.000 a 255.000 filas por ramo y el nivel reajustado en el propio año. Mide la estructura, no el nivel. Ninguna decisión anterior lo había usado.

## Qué se probó

DES24 se da como diferencia frente a T2b, que tiene 0,0751, 0,1099 y 0,0884 en autos, edificios y contenidos. Las columnas de 2023 y 2024 son D² con calibración C1, igual que en el informe principal; la sección de la mezcla explica por qué las cifras de 2023 están algo por debajo de su valor anidado.

| Tronco | Idea | DES24 autos / edificios / contenidos | 2023 (DEV) | 2024 (HOLD) |
| --- | --- | --- | --- | --- |
| T2b | referencia (MLind v1) | | 0,1233 | 0,1253 |
| FS | Poisson para el número de siniestros × Gamma para el coste medio | +0,0069 / +0,0017 / +0,0008 | 0,1173 | 0,1281 |
| T2h | T2c más una etapa de historia centrada, con multiplicador 1 donde la ventana no se observa | +0,0007 / −0,0002 / −0,0018 | 0,1214 | 0,1277 |
| T2o | T2b sin `occupation` | +0,0013 / +0,0008 / +0,0008 | 0,1226 | 0,1242 |
| T2c | T2b sin historia (A04) | −0,0007 / −0,0005 / −0,0021 | 0,1214 | 0,1272 |
| CB | CatBoost Tweedie con las variables de T2b | +0,0034 / +0,0010 / −0,0022 | 0,1122 | 0,1218 |
| FSp | frecuencia y severidad por peligro, un solo nivel emergente | +0,0039 / +0,0003 / −0,0377 | 0,1112 | 0,1212 |
| T2x | T2b + `make_model` + tenencia multirramo | −0,0093 / −0,0005 / −0,0001 | 0,1100 | 0,1226 |
| F0 | diagnóstico: frecuencia de FS × coste medio fijo | +0,0007 / −0,0206 / −0,0283 | 0,1025 | 0,1216 |

Fuentes: `e14_individuales.json`, `e14_fs.json`, `e15_cb.json`, `e21_fsp.json` y los `*_meta.json` de cada tronco. Código: `transfer2.py` y `e14_eval.py`.

## Lo que enseñan

El hallazgo más claro es la frecuencia × severidad. El diagnóstico F0 muestra de dónde sale la ganancia: con un coste medio fijo, edificios cae −0,021 y contenidos −0,028. Modelar la severidad aporta casi todo. Al pasar al emergente la ganancia se atenúa: en autos, los +0,0069 del desarrollado quedan en +0,0005 en 2023 y +0,0014 en 2024 (estructura con el nivel reajustado en cada muestra).

La pérdida de FS en 2023 viene de edificios: 0,0656 frente a 0,0848 de T2b con C1. Diez siniestros grandes de incendio e inundación explican 0,019 de esa diferencia. Solo un incendio de 261.192 CU, para el que T2b esperaba 1.077 y FS 546, aporta 0,007. En 2024, con incendios por debajo de lo habitual, FS gana en edificios por +0,0036 con C1.

La historia de siniestros funciona cuando se trata con coherencia. T2h corrige el problema de A04, los NaN que delataban el primer año de datos. En DEV coincide con T2c, porque en 2023 no hay ventana observada. En 2024 gana +0,0024 (IC95 [−0,0005; +0,0051]).

`make_model` empeora incluso dentro del desarrollado (−0,0093 en autos en DES24): como categórica de 300 niveles, LightGBM sobreajusta. CatBoost no transfiere bien solo (−0,0110 en 2023). FSp no mejora a FS, y en contenidos dos de sus frecuencias por peligro no llegaron a aprender (E21).

La revisión señaló que, al recibir `init_score`, LightGBM no parte de la tasa media: los troncos gastan rondas en alcanzar el nivel. Lo corregí en E23 (arranque en la tasa media) y el resultado fue peor. La parada temprana se adelanta (T2b pasa de 249/194/169 rondas a 128/57/77) y edificios cae en DES24 entre 0,0037 y 0,0062 en los troncos Tweedie (0,0009 en FS). Autos mejora entre +0,0007 y +0,0019. Arrancar desde cero actuaba como regularización, así que se conservan los troncos originales.

`customer_service_contacts` sigue fuera, como fijó el proyecto. En 2023-2024 las filas sin contactos casi no tienen siniestros, lo que delata información posterior al periodo. En el test, la media de contactos es la mitad que en entrenamiento (0,40 frente a 0,77-0,86 en autos). No sirve para cerrar el hueco con el líder.

## Mezcla v2 (E22)

Entran T2b y todo tronco que no pierda más de 0,002 frente a T2b en DES24 (en ningún ramo) ni en 2024. Cumplen T2h, FS y T2o. Los pesos por ramo se encogen a la mitad hacia pesos iguales, el nivel es C1 y no hay tendencia.

Esa regla se escribió a las 17:25 UTC, cuando ya conocía DES24 y 2024 de seis de los siete troncos; solo FSp estaba sin ver. Por eso la ganancia en 2024 y en el OOF 2023-2024 de la tabla siguiente no es una confirmación independiente. La única evidencia limpia para todos es DES24, que mide los troncos y no la mezcla.

| Evaluación (anidada salvo HOLD) | T2b (v1) | Mezcla v2 | Diferencia (IC95 por cliente) |
| --- | --- | --- | --- |
| 2023, DEV (troncos 2021-2023) | 0,1292 | 0,1286 | −0,0006 [−0,0038; +0,0023] |
| 2024, HOLD (troncos 2021-2023) | 0,1253 | 0,1281 | +0,0028 [+0,0009; +0,0045] |
| OOF 2023-2024 con los troncos de producción (2021-2024) | 0,1326 | 0,1359 | +0,0033 [+0,0004; +0,0065] |
| … solo renovación | | | +0,0039 [+0,0010; +0,0075] |
| … solo nuevo negocio | | | −0,0009 [−0,0077; +0,0057] |

Fuentes: `anidado_dev.json`, `anidado_pcv.json` y `e22_mezcla.json`; código `anidado.py`.

"Anidada" quiere decir que, para cada pliegue evaluado, el nivel de cada tronco, los pesos y C1 se estiman sin ese pliegue, también en las predicciones internas. La revisión detectó que la evaluación anterior no lo hacía: el efecto iba contra el pliegue y dejaba las cifras con C1 de DEV y PCV entre 0,004 y 0,006 por debajo de su valor. Eso alcanza también a la tabla del informe principal (T2b C1 en DEV: 0,1233 antes, 0,1292 anidado). Las diferencias entre candidatos casi no cambian. Con la evaluación anidada, C1 equivale a no calibrar. C2 queda +0,003 por encima en 2023 y +0,001 en 2023-2024, y en 2024 sigue perdiendo, como ya se había visto.

Por la regla de E18, la mezcla no sustituye a MLind v1, porque pedía al menos +0,001 en 2023. Queda como candidata alternativa documentada. T2b, por su parte, se eligió en DEV entre unos quince candidatos, y su cifra de 2023 tiene un sesgo de selección a su favor.

Mi lectura es que la mejora existe en renovación. En nuevo negocio no hay evidencia de ganancia, y el 76 % de la cartera 2025 es nuevo negocio. Ponderado a esa cartera, el cambio en 2023 es +0,0006 (IC95 [−0,0066; +0,0076], `pcv_v2_frente_v1.json`). La ganancia esperada en el tablero ronda +0,001. Corrección posterior (CLA-S2-20261024-024 de la otra sesión de Claude): el ruido de 0,003 de `COMPARACION_LINEAS.md` era el de la diferencia entre MLind y A1, que correlacionan 0,987, y no sirve para dos mezclas casi iguales. Medido en 2024 con submuestras del 33 %, la diferencia pareada entre la mezcla 50/50 con v2 y la mezcla con v1 (A1 en lugar de la designada) tiene una desviación típica de 0,0007 alrededor de +0,0011 (`ruido_pareado_v2.json`). El tablero podría distinguir una mejora así si se trasladara a 2025, pero la mezcla robusta muestra que una ganancia local de ese tamaño puede no trasladarse.

## Archivos 2025

La revisión encontró también que la historia de 12 meses de las pólizas 2025 que empiezan de febrero a diciembre contaba como cero un tramo sin observar, porque los siniestros llegan hasta el 30 de diciembre de 2024. `historia2.py` corta la ventana en el 31 de diciembre de 2024. Solo cambia el 0,1 % de las filas de 2025 y el total sube un 0,02 %. DEV, HOLD y PCV no cambian. La v2 que se entrega ya lleva la corrección. En v1 el mismo arreglo movería el total un +0,014 %, así que el archivo enviado no queda afectado de forma apreciable.

| Archivo | Total (CU) | Autos | Edificios | Contenidos | SHA-256 |
| --- | --- | --- | --- | --- | --- |
| MLind v1 (T2b, C1) | 70.822.703 | 546,8 | 467,5 | 92,7 | d261388c… |
| MLind v2 (mezcla e50, historia corregida) | 70.488.759 | 553,2 | 449,9 | 92,6 | 4fe490fe… |
| Mezcla 50/50 designada + v1 (la enviada, público 0,15390) | 68.995.571 | | | | 12831ef4… |
| Mezcla 50/50 designada + v2 | 68.828.599 | | | | 77a18749… |

Las columnas por ramo son tasas en CU por año de exposición. Los archivos `prediccion_2025_mlind_v2.csv` y `mezcla50_designada_mlind_v2_2025.csv` están en `Repositorio_IAA2026/privado/semana2/claude_ml_independiente_20261023/`. Tienen 209.063 filas en el orden de la plantilla, sin nulos y todas positivas. Las huellas completas están en `produccion_mlind_v2.json`. La revisión reconstruyó desde las predicciones la v2 anterior a la corrección de la historia y obtuvo su misma huella. Con solo T2b, `produccion2.py` reproduce v1 bit a bit (d261388c).

V2 se parece mucho a v1: la correlación de los logaritmos es 0,995. Autos sube un 1,2 %, con el nuevo negocio de 581,8 a 590,0 y la renovación de 430,8 a 431,2. Edificios baja un 3,8 %. Con pesos sin encoger (e0) el total sería 70,31 M, y con pesos iguales (e100) 70,83 M.

## Qué decide el participante

- Si la mezcla 50/50 con v2 sustituye a la mezcla con v1 como candidata de envío. Es la misma regla de combinación con un miembro que mejora en renovación. El efecto esperado en el tablero es pequeño (+0,001), con un ruido pareado de unas 0,0007, y la experiencia de la mezcla robusta aconseja no contar con él.
- Si se envía. Los envíos los hace Codex, con autorización expresa.

## Hacia dónde seguir

La severidad es donde el desarrollado tiene estructura que el Tweedie directo no aprende. El paso siguiente sería ajustar la severidad de FS con validación interna del desarrollado, como E07 hizo con T2b, y medirla con DES24. E23 deja otra pista: arrancar en la tasa media ayuda en autos y perjudica en edificios. Merece un ajuste por ramo de la tasa de aprendizaje y la parada temprana, juzgado también con DES24.

Seguir sumando troncos rinde poco: los mejores cambios valen unas milésimas. La incertidumbre grande sigue siendo el nivel del nuevo negocio de autos en 2025. Con 2023-2024 no se puede resolver, porque esos dos años se contradicen: bajo T2b, el cociente entre el real/esperado del nuevo negocio y el de renovación fue 1,39 en 2023 y 1,02 en 2024.

## Adenda: severidad ajustada y pesos estimados en el desarrollado (E25 y E26)

Corte del 24 de octubre a las 19:57 UTC, a pedido del participante («continua»). Las dos pruebas siguen la pista que dejó la sección anterior: la severidad es donde el desarrollado tiene estructura propia. Ambas se declararon antes de correr (19:42 UTC).

E25 ajusta la severidad Gamma de FS con una rejilla de 36 combinaciones, elegida con el pliegue interno del desarrollado 2021-2023 sin mirar 2024 ni el emergente. En los tres ramos gana el árbol más pequeño (7 hojas, 50 filas por hoja), que además está en el borde de la rejilla. Con esa severidad, FSt mejora a FS en DES24 en edificios (+0,0018) y contenidos (+0,0012) y pierde en autos (−0,0011). La media es +0,0006, así que por la regla FSt sustituye a FS en la mezcla. El resultado es v2.1.

E26 prueba otra forma de elegir los pesos de la mezcla: estimarlos en el desarrollado 2024, con unas 200.000 filas por ramo, en lugar de en el emergente. Esos pesos cargan casi todo en FSt (0,87 en autos, 0,64 en edificios y 0,55 en contenidos). Dentro de 2024, con pesos cruzados, la mezcla no supera a FSt solo en autos ni en edificios.

| Evaluación (C1) | T2b (v1) | v2 | v2.1 (FSt, e50) | v3 (pesos DES24) | FSt solo |
| --- | --- | --- | --- | --- | --- |
| 2023, DEV anidado | 0,1292 | 0,1286 | 0,1287 | 0,1273 | 0,1242 |
| 2024, HOLD | 0,1253 | 0,1281 | 0,1284 | 0,1295 | 0,1298 |
| 2023-2024, PCV anidado | 0,1326 | 0,1359 | 0,1354 | 0,1358 | 0,1353 |

Fuentes: `e26_anidado_dev.json`, `e26_hold.json`, `e26_anidado_pcv.json` y `e26_pesos_des24.json`; código `e25_severidad.py`, `e26_pesos_des24.py`, `e26_hold.py` y `anidado.py`.

v3 pierde 0,0013 frente a v2 en 2023, más que el margen de 0,0005 que fijó E26, así que no sustituye a v2. v2.1 empata con v2: +0,0001 en 2023, +0,0003 en 2024 y −0,0005 en 2023-2024. Sus predicciones correlacionan 0,9996 en logaritmo con las de v2.

La tabla repite el patrón de toda la sección. Cuanto más peso tiene la frecuencia × severidad, mejor sale 2024 y peor 2023, y el vaivén lo deciden unos pocos incendios de edificios. Con unos 3.000 siniestros por año, ninguna de estas evaluaciones distingue diferencias de estructura de una milésima. El tablero tampoco: la mezcla robusta de la otra sesión de Claude ganaba +0,0009 en 2024 (IC95 [+0,0002; +0,0016]) y dio 0,15347 en el público, 0,0004 por debajo de la mezcla enviada (COD-S2-20261024-ENVIO-MEZCLA50-ROBUSTA).

Archivos de v2.1, sin enviar, en `Repositorio_IAA2026/privado/semana2/claude_ml_independiente_20261023/`:

| Archivo | Total (CU) | Autos | Edificios | Contenidos | SHA-256 |
| --- | --- | --- | --- | --- | --- |
| `prediccion_2025_mlind_v21.csv` | 70.706.999 | 551,7 | 457,1 | 92,6 | 481b679b… |
| `mezcla50_designada_mlind_v21_2025.csv` | 68.937.720 | | | | 666b7925… |

Por la regla, la candidata de esta línea pasa a ser v2.1. En la práctica es la misma que v2. Mi lectura es que la estructura de la línea está agotada con estos datos. Lo que queda abierto es el nivel de 2025, sobre todo el del nuevo negocio de autos. Según E09, llevado a la cartera 2025, un error del 15 % en el nivel de autos cuesta 0,002 de D², más que cualquiera de estas mejoras de estructura.

Ruido del tablero para estas mezclas. Para la mezcla 50/50 con v2.1 frente a la mezcla enviada, sobre 2024 (exploratorio, con A1 en lugar de la designada): diferencia +0,0013, +0,0008 ponderada a la cartera 2025, y desviación típica de 0,0007 en submuestras del 33 % (`ruido_pareado_v2.json`). La otra sesión de Claude midió para la mezcla robusta una desviación de 0,0004 alrededor de +0,0009, y el público dio −0,0004. Las dos mediciones apuntan a lo mismo: lo que 2023-2024 mide en este orden no basta para anticipar 2025.
