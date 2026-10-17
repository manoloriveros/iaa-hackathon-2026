# Los otros 265 capitales pendientes: qué les falta, qué dicen sus historias y cómo tratarlos

Revisión de Claude a solicitud del participante, 16 de octubre de 2026 (America/Bogota). Corrida `runs/rest_20261017T021239Z_929ce606` (`evidencia.json`, nueve tablas CSV, copia del script y `manifest.json` con SHA-256); explorador interactivo en [informe.html](informe.html). Cubre los cinco grupos de D48 que siguen pendientes en la rama retrospectiva fuera del grupo F revisado en D63: otros conflictos de capital, riesgo o distancia temporal (138), sin referencia original habitual (108), dependientes de interpretar T/W (16), apoyo dependiente de correcciones CAP01 (2) y la discrepancia C48613718 (1). No se modificó ningún dato, índice ni corrida de Codex; las listas de candidatas que propone este informe no están aplicadas y necesitan autorización expresa. Es verificación propia asistida por IA, no una revisión independiente ni humana.

## 1. Qué se revisó

La rama activa al correr era `capendorse_20261017T010844Z_fbf8cc20` (CAP06R, D61) con 419 capitales pendientes: 154 del grupo F, ya revisados en D63, y los 265 de este informe (control K02). Son 264 pólizas (una del grupo C tiene dos periodos pendientes) y 844 periodos leídos desde los Parquet originales, con el capital de la base y de la rama al lado para ver qué correcciones previas hay en cada historia: en estas pólizas hay 269 periodos extremos, los 265 pendientes y cuatro ya corregidos por CAP01 o por la rama (control H02). Hash SHA-256 de los 265 `row_id` ordenados: `8530dc3ce2afefd4fd27749746749953c44600fd474d9261f873d22a2fc9192f`.

El método es el de D63. Para cada fila se evalúan todas las demás filas de su póliza como referencias con las condiciones de D34 (capital normal, sin solape, inicio a 1–400 días, razón entre el capital dividido por mil y la referencia dentro de 0,90–1,10, campos de contexto conocidos iguales; un nulo se registra como desconocido y no se imputa), y se anota, por referencia, el motivo exacto por el que no sirve: otra dirección, otro campo distinto, solo el código t/w, más de 400 días, solape o razón fuera de banda. Sobre esa clasificación se formulan criterios explícitos, cada uno apoyado en un comportamiento medido en todo el archivo original de hogar (891.881 periodos de edificios y 909.115 de contenidos). Los 23 controles de la corrida pasan (`tables/controles.csv`).

## 2. Tres comportamientos del archivo que permiten leer estos grupos

Mudanza. Entre periodos consecutivos de la misma póliza con cambio de dirección, el capital de edificios se recalcula: la razón capital(t)/capital(t−1) queda dentro de 0,90–1,10 en solo el 13,9 % de 34.315 pares, con percentiles 10 y 90 en 0,47 y 2,18 (control G02). El de contenidos se conserva: razón exactamente igual a 1 en el 99,78 % de 34.548 pares y dentro de la banda en el 100 % (control G03). Para la pregunta de escala esto significa que, en contenidos, un periodo de otra dirección de la misma póliza sirve de referencia; en edificios, no.

Ampliación a mitad de año. En contenidos, el periodo que sigue a un `mid_term_change` en la misma dirección sube el capital entre 1,20 y 1,60 veces (percentiles 1 y 99: 1,203 y 1,596; mediana 1,399) en 13.055 casos, nunca lo baja (control G04), y en la renovación siguiente el capital vuelve al nivel base indexado: siguiente/base entre 1,016 y 1,024 en 11.490 casos, el 100 % dentro de la banda (control G05). La etiqueta `mid_term_change` equivale a una firma estructural, periodo contiguo (sin hueco), misma dirección y mismo contador de renovaciones: coincide en el 100 % de los casos en un sentido y el 99,8 % en el otro (control G06), lo que permite reconocer ampliaciones en test 2025, donde la etiqueta no existe.

Alias t/w. En edificios, 18.202 pares consecutivos en la misma dirección cambian el código de construcción de t a w, el 99,8 % el 1 de enero de 2023; su razón de capital está dentro de la banda en el 100 % (mediana 1,030, igual que sin cambio) y no hay ningún otro cambio de código de construcción en la misma dirección en todo el archivo (control G01). Es lo que D39 llamó alias temporal; para la escala del capital no es un cambio.

## 3. Grupo G: 138 filas de otros conflictos

La etiqueta de D48 agrupaba lo que no encajaba en los demás grupos. Separados por motivo, los 138 son tres cosas distintas.

Mudanzas, 88 filas (47 de contenidos y 41 de edificios): el periodo extremo es el único de su dirección y todas las referencias normales están en otra. En las 47 de contenidos, el capital del periodo de la otra dirección coincide exactamente con el capital dividido por mil: razón 1,0000 en todas (control R04), con el resto del contexto igual y a menos de 400 días. Es el comportamiento de las 34.548 mudanzas del archivo. En las 41 de edificios, la otra casa tiene otro capital (razones entre 0,40 y 3,6) y la póliza no ofrece nada comparable; se tratan con el grupo C en la sección 4. Otras dos filas con mudanza tienen además una referencia en la misma dirección que resuelve el caso: una por el alias t/w y otra por una cadena de dos periodos extremos (sección 6).

Ampliación con error de escala, 32 filas, todas de contenidos: el periodo extremo sigue sin hueco a un periodo normal de la misma dirección con el mismo contador de renovaciones (un `mid_term_change` en entrenamiento; la misma firma en las 5 filas de test 2025) y, dividido por mil, queda entre 1,207 y 1,594 veces el nivel previo (mediana 1,370), exactamente donde caen las 13.055 ampliaciones del archivo. En 24 de ellas existe la renovación siguiente y vuelve al nivel base: siguiente/previo entre 1,019 y 1,022. En las otras 8 la póliza termina en ese periodo (`lapsed_by_customer`, `cancelled`) o la fila es de test 2025 y no hay periodo posterior. Son un cambio real de cobertura, la ampliación, y además un error de escala; por eso la banda de ±10 % de D34 las rechazaba al compararlas con el nivel previo. La razón de un periodo ampliado frente a su base no es una cifra libre: el archivo la acota.

Nivel base con ampliación adyacente, 16 filas, todas de contenidos: el periodo extremo es el nivel base y la referencia que contradice (razón entre 0,625 y 0,815) es un tramo ampliado contiguo, mientras las demás renovaciones encajan (0,979 a 1,021). Es el patrón de las dos pólizas de D60 que CAP06R corrigió a mano; aquí la condición queda escrita: hay referencia compatible y toda referencia contradictoria es un periodo ampliado reconocible por la firma estructural, con subida dentro de 1,15–1,65.

## 4. Grupo C y mudanzas de edificios: 149 filas sin nada con qué compararse

Las 108 del grupo C son pólizas de un solo periodo (106) o de dos periodos ambos extremos (una póliza, dos filas); 107 están en test 2025 y 62 son de edificios. Junto con las 41 mudanzas de edificios del grupo G suman 149 filas sin ninguna referencia en su póliza, 123 de ellas en test 2025 (control R02 para el grupo C). Ninguna regla de la familia D34 puede certificar su escala fila a fila, y D48 ya rechazó dividir por umbral de forma automática. Lo que sí se puede medir es si el capital dividido por mil es verosímil, con tres señales que no deciden ninguna corrección pero sí informan el modelado.

Primera, la posición en la distribución: dividido por mil, el capital de estas filas cae en cualquier punto de la distribución de capitales normales de su ramo, del percentil 4 al 99,5 en edificios (93.000 a 556.000 CU, frente a un máximo normal de 1.061.000) y del 1 al 99,5 en contenidos (10.700 a 126.200 CU, máximo normal 346.700). No se concentran en un extremo, como ocurriría si fueran capitales genuinos de otra magnitud. Segunda, la póliza vecina: 101 de las 149 filas tienen, en la misma dirección y fechas, una póliza del otro ramo de hogar del mismo cliente, ninguna extrema. La razón contenidos/edificios calculada con el capital dividido por mil cae dentro del 90 % central de la población (633.693 pares normales de la misma combinación cliente, dirección y solape; mediana 0,213) en el 90,1 % de los casos (control R12); con el capital registrado, esa razón sería mil veces mayor o menor. Tercera, la prima: en los 18 periodos pendientes de año completo de toda la cohorte, la prima por mil de capital calculada con el capital dividido por mil tiene medianas de 0,828 en edificios y 3,371 en contenidos, frente a 0,973 y 3,304 en las filas normales de año completo; en periodos cortos la prima escrita no está prorrateada de forma documentada y no se compara.

La propuesta para estas 149 filas es una decisión de modelado, no una corrección de datos: una transformación documentada en la construcción de F0, aplicada a cualquier capital que siga pendiente al entrenar o al predecir, que use `sum_insured/1000` como valor del predictor cuando el capital supera el umbral del ramo y añada una marca `capital_scale_suspect` que queda fuera de los predictores como las columnas `audit_*`. La tabla de datos no cambia. La alternativa que D48 dejó anotada, tratar el capital como no disponible con un imputador entrenado solo en entrenamiento, sigue abierta y conviene compararla dentro de las particiones temporales. Las 123 filas de test pesan más que las 26 de entrenamiento en esta decisión: en test el modelo predice con el capital que se le dé.

## 5. Grupo E: 16 filas dependientes de T/W

Las 16 son de edificios y de entrenamiento. Cada una tiene en la misma dirección, a entre 39 y 365 días, un periodo normal con todo el contexto igual salvo el código de construcción: t en el periodo extremo (2021–2022) y w en la referencia (2023 en adelante), o al revés; razones entre 0,9669 y 1,0357 (control R07). En nueve la referencia es anterior, en siete posterior, y en nueve pólizas hay además una mudanza cuyas referencias de otra dirección no cuentan. El criterio TW01-R trata t y w como el mismo código solo para la comparación de escala, con los demás campos iguales y las condiciones numéricas y temporales de D34; no unifica los códigos en los datos ni activa CON01, como pidió D39. Una fila más del grupo G entra por el mismo criterio: 17 candidatas en total.

## 6. Grupo D y la cadena de la póliza B19256617: 3 filas

Las dos del grupo D son filas de test 2025 (B02718543 y B02755900) cuya referencia próxima es la fila de 2024 ya corregida por CAP01, y la referencia original normal más cercana está a 731 días. Usar la fila corregida como ancla sería circular; el criterio CHAIN01-R exige un ancla original normal en la misma dirección a más de 400 días y hasta dos años calendario, como DIST01-R, con una fila intermedia corregida en lugar de una fila intermedia con faltantes, y razón en banda en cada paso: ancla → fila corregida (1,031 y 1,030), fila corregida → fila pendiente dividida por mil (1,030 y 1,033) y fila pendiente → ancla (1,062 y 1,064). En B40325888 la cadena es 225.000 (2023) → 232.000.000 corregido a 232.000 (2024) → 239.000.000 (2025); en B51302846, 267.000 → 275.000.000 → 284.000.000. La dependencia de CAP01 se registra en la bitácora; el ancla sigue siendo un capital original.

La tercera fila es B00962235 (grupo G): tras una mudanza en julio de 2022, la póliza B19256617 tiene dos periodos extremos consecutivos en la nueva dirección, 377.000.000 (2022) y 388.000.000 (2023); la rama corrigió el segundo con apoyo posterior (CAP02R, 388.000 frente a 400.000 en 2024) y el primero encaja con esa corrección (0,972) y con el ancla original de 2024 a 542 días (0,9425). Depende de una corrección de la rama; se registra igual.

## 7. Grupo A: C48613718

La fila C01596694 (29.300.000 CU, 2023) quedó pendiente en D51 porque su referencia anterior más próxima con contexto igual, el tramo de septiembre a diciembre de 2022 con 40.500 CU, da una razón de 0,723. La historia completa lo explica: 28.200 en 2021; 28.800 de enero a septiembre de 2022, con `security_level` nulo; el tramo ampliado de 40.500 hasta diciembre; 29.300.000 en 2023; 29.900 en 2024 y 30.500 en 2025. El tramo de 40.500 es una ampliación (1,406 sobre 28.800) y la renovación de 2024 (0,980) y la base de 2022 (1,017) encajan con 29.300. Entra en END02-R como las pólizas de D60; el nulo de la referencia inicial se registra como desconocido, con la misma lógica que NUL01-R en D63.

## 8. Casos concretos

El informe HTML muestra quince casos elegidos por una condición explícita, con la historia completa, todas las referencias, los siniestros y la póliza vecina. Resumidos:

R01, póliza C53818446 (contenidos): 17.100 y 17.400 en la dirección antigua; 17.400.000 en la nueva desde enero de 2022. Razón 1,0000 con el periodo anterior de la otra dirección; MOV01-R.

R02, póliza C66015840 (contenidos): 49.100.000 en la primera dirección durante 2021; 49.100 y 50.100 en la siguiente. Razón 1,0000 con el periodo posterior; MOV01-R con apoyo posterior.

R03, póliza C59751087 (contenidos): 33.600 hasta febrero de 2021 (`mid_term_change`), 53.300.000 hasta diciembre, 34.300 en 2022 y renovaciones hasta 36.400. Dividido por mil, 53.300 es 1,586 veces el nivel previo; la renovación de 2022 vuelve al nivel base (1,021). END01-R con reversión observada.

R04, póliza C04869917 (contenidos): 38.300, 39.100 hasta mayo de 2022 y 52.800.000 hasta julio, cuando el cliente deja la póliza. Razón 1,350 sobre el nivel previo; sin periodo posterior. END01-R.

R04b, póliza C27269421 (contenidos): seis periodos normales de 2021 a mayo de 2025 (51.500 a 55.700, con una mudanza en 2023 que conserva el capital) y 87.800.000 de junio a diciembre de 2025 en test. Sin etiqueta, la firma estructural identifica la ampliación: razón 1,576. END01-R en test 2025.

R05, póliza C48613718 (contenidos): la del grupo A, descrita en la sección 7. END02-R.

R06, póliza C58208578 (contenidos): 26.400.000 de enero a marzo de 2021 (`mid_term_change`), 32.800 el resto del año (ampliación de 1,242 sobre 26.400), 26.900 en 2022 y renovaciones hasta 28.600 en 2025. El tramo ampliado contradice (0,805); las renovaciones encajan (0,981). END02-R.

R07, póliza B59578424 (edificios): 117.000.000 con código t de mayo a diciembre de 2022; 121.000 con w en 2023 y 125.000 en 2024. Razón 0,967; TW01-R.

R08, póliza B37813572 (edificios): 315.000.000 (t) en 2022 y 325.000 (w) en 2023 en la misma dirección; después una mudanza con 168.000 a 178.000, que no cuentan. Razón 0,969; TW01-R.

R09, póliza B40325888 (edificios, grupo D): la cadena de la sección 6, con ancla original en 2023. CHAIN01-R.

R09b, póliza B19256617 (edificios): la cadena con intermedia corregida por la rama, sección 6. CHAIN01-R.

R10, póliza B85008304 (edificios): 294.000.000 en 2021 en una dirección; 181.000 a 204.000 en otra desde 2022. La otra casa no dice nada sobre la primera; sin referencia.

R11, póliza B18081301 (edificios, test 2025): un solo periodo, 2025, sin historia. Sin referencia.

R12, póliza C89102435 (contenidos, test 2025): un solo periodo desde junio de 2025. Sin referencia.

R13, póliza B67263929 (edificios): dos periodos y los dos extremos, 435.000.000 desde septiembre de 2024 y 448.000.000 en 2025; ningún capital normal en la historia. Sin referencia.

## 9. Propuestas, sin aplicar

Cinco criterios con lista congelada, todos con las condiciones numéricas y temporales de D34 y un solo cambio cada uno, medido en el archivo. Si una fila cumple varios, el orden es END02-R, MOV01-R, END01-R, TW01-R, CHAIN01-R.

| Criterio | Qué exige | Filas | Grupos | Apoyo anterior | Solo posterior | Test 2025 |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| MOV01-R | Contenidos: referencia original normal de la misma póliza y cliente en otra dirección, demás campos conocidos iguales, 1–400 días, razón 0,90–1,10 | 47 | G | 19 | 28 | 15 |
| END01-R | Contenidos: periodo que sigue sin hueco y con el mismo contador a un periodo normal de la misma dirección, contexto conocido igual, (÷1000)/previo dentro de 1,15–1,65; subnivel con reversión observada (24) | 32 | G | 32 | 0 | 5 |
| END02-R | Referencia compatible (nulos como desconocidos) y toda referencia contradictoria es un periodo ampliado; la ampliación se conserva | 17 | G, A | 11 | 6 | 5 |
| TW01-R | Edificios: referencia en la misma dirección que solo difiere en t/w, 1–400 días, razón 0,90–1,10 | 17 | E, G | 9 | 8 | 0 |
| CHAIN01-R | Ancla original normal a más de 400 días y hasta dos años en la misma dirección, intermedia corregida por CAP01 o la rama, razón en banda en cada paso | 3 | D, G | 2 | 1 | 2 |
| Total | | 116 | | 73 | 43 | 27 |

Hashes SHA-256 de las listas (row_id ordenados): MOV01-R `aa59644bdf93…`, END01-R `c185d8048391…`, END02-R `34b8792034ca…`, TW01-R `23da90bf3695…`, CHAIN01-R `193b2eabfca4…`; completos en `evidencia.json` y `tables/candidatas_NO_APLICADAS.csv`. La suma de capitales de las 116 pasaría de 9.116.400.000 a 9.116.400 CU. Quince referencias de MOV01-R y cinco de END01-R están en test 2025; esas filas quedarían marcadas como respaldo posterior, como las 136 ya existentes en la rama.

Qué asume cada criterio. MOV01-R, que el capital de contenidos se conserve al mudarse: lo hace exactamente en el 99,78 % de las mudanzas del archivo; en edificios no aplica y no se propone. END01-R, que el periodo sea una ampliación real además de un error de escala: la banda 1,15–1,65 cubre las 13.055 ampliaciones del archivo con margen, y en 24 de las 32 filas la renovación siguiente confirma la vuelta al nivel base; las 8 sin reversión observada son el subnivel más débil. END02-R generaliza MANUAL_ENDORSE01-R con la condición escrita. TW01-R asume que t y w son el mismo código para la escala, lo que 18.202 pares muestran sin excepción; no toca los datos ni CON01. CHAIN01-R depende de una corrección previa, que se registra; dos de sus tres filas son de test.

Qué no cambia en ninguna: solo cambiaría `sum_insured`, dividido por mil, en una capa retrospectiva separada de la base, con lista por hash y sin recalcular la selección tras reparar; ningún nulo se rellena, ningún código se unifica, ninguna ampliación se suaviza ni se copia; primas, siniestros y pólizas vecinas son diagnóstico; las referencias posteriores no son evidencia causal al corte; las 149 filas sin referencia no entran en ninguna lista de corrección. Cualquier aplicación necesita autorización expresa del participante y seguiría el flujo apply, verify y finalize de Limpieza.

Qué haría revisar las propuestas: una fila cuya razón quede fuera de banda; un siniestro aceptado por encima del capital hipotético (hoy ninguno: nueve siniestros en estas pólizas, ninguno en periodos pendientes); una definición del generador en la que la mudanza, la ampliación o el alias t/w signifiquen otra cosa; la confirmación de unidades por el organizador.

## 10. Límites

Las estadísticas describen el generador de datos del concurso, no una cartera real: que una mudanza conserve el capital de contenidos o que una ampliación suba siempre entre 1,20 y 1,60 veces dice cómo se generaron los datos. Las definiciones de D34 se tomaron de la documentación del proyecto. La firma estructural de la ampliación en test es una inferencia a partir del entrenamiento. No se consultó al organizador. No se entrenaron modelos ni se modificaron datos, índices ni corridas; la revisión humana e independiente está pendiente.

## 11. Reproducción y verificación

Desde `C:\dev\Hakaton`, con el Python de `Preparación\.venv`: `revisar_pendientes_restantes.py` crea una corrida nueva en `runs/` (resuelve la rama activa por `current_retrospective_dataset.json`; los controles K01 y K02 avisan si los grupos cambian); `construir_informe.py` reconstruye `informe.html`; `verificar_entrega.py`, sin pandas, comprueba el manifiesto de la corrida vigente, que el informe HTML de la raíz es el de esa corrida, que los 23 controles pasaron, que los once originales conservan su hash, que ninguna candidata está aplicada, que los enlaces de este informe existen y que las cifras citadas aquí (`cifras_informe.json`) coinciden con `evidencia.json`; escribe `verification.json`. `current_run.json` identifica la corrida revisada.
