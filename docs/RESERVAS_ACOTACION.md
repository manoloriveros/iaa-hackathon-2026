# Reservas con una sola valoración: qué se puede acotar y qué queda abierto

Claude (línea principal), 19 de octubre de 2026. Encargo del participante en esta sesión, con la materialidad fijada en el 1 % del nivel 2025 de cada ramo antes de calcular nada ([autorización](../registro/autorizacion_reproduccion_reservas_20261019.json); plan pre-registrado en la corrida privada `reservas_20261019T225357Z_99b45271`). No se cambió T0, la receta ni ninguna predicción, y nada de esto es revisión humana.

## Por qué ningún cálculo con estos archivos demuestra la suficiencia

Una reserva de caso es una previsión de lo que falta por pagar en un siniestro abierto. Para saber si era suficiente hay que ver esos pagos, y eso exige una valoración posterior de los mismos siniestros. El archivo `claims` es una sola fotografía al 31 de diciembre de 2024, con una fila por siniestro y sin movimientos, así que la suficiencia no se puede demostrar con él. Codex lo dejó dicho en COD-20261019-114 y el protocolo de evidencia nueva lo mantiene.

Lo que sí se puede hacer es más modesto y útil para decidir. Primero, medir cuánto sesgo de reservas haría falta para que el resultado cambie de verdad: mover el nivel 2025 de un ramo más del 1 % o cambiar el orden entre S30 y S22. Segundo, estimar el sesgo bajo un supuesto escrito y comprobar las consecuencias de ese supuesto que sí se ven en los datos. Si el sesgo plausible queda por debajo del umbral de quiebre, la incertidumbre de reservas no es material; si lo cruza, hay que declararla y decidirla.

## Cuánto sesgo haría falta para que importe

Un sesgo en la reserva de caso cambia las etiquetas T0 de los años recientes, donde se concentran los abiertos, y llega al nivel 2025 por dos vías. La más fuerte es el factor de año siguiente: f23 compara las etiquetas de 2023 con un modelo entrenado en 2021-2022 y f24 las de 2024 con uno entrenado en 2021-2023, y el nivel de 2025 usa su media. La otra es el nivel de entrenamiento de los componentes, que aprende de las etiquetas de 2021 a 2024. La primera vía se recalculó exactamente sobre las predicciones guardadas de S30; la segunda se aproxima por el cambio relativo del coste último supuesto de los años de entrenamiento. Como control, los factores recalculados sin sesgo coinciden con los de `resumen.json` de S30 en las cinco cifras publicadas.

El multiplicador b se aplica a la reserva de caso de los abiertos: b = 1,10 significa que lo que falta por pagar es un 10 % más de lo reservado. El multiplicador k se aplica al coste IBNR que D67 estimó para los siniestros aún no reportados.

| Ramo | Reserva sobre último supuesto, 2023 y 2024 | b que mueve el nivel 2025 un 1 % | Nivel 2025 con b = 0,75 y 1,25 | k del IBNR que lo mueve un 1 % |
| --- | --- | --- | --- | --- |
| Autos | 20,1 % y 22,7 % | 0,963 a 1,037 | −6,7 % y +6,8 % | 0,946 a 1,054 |
| Edificios | 5,6 % y 26,0 % | 0,960 a 1,040 | −6,2 % y +6,4 % | 0,836 a 1,163 |
| Contenidos | 1,0 % y 13,7 % | 0,910 a 1,090 | −2,8 % y +2,8 % | 0,595 a 1,403 |

La lectura es exigente: con una materialidad del 1 %, un error de reservas de unos cuatro puntos en autos o edificios ya es material. En autos la reserva de lesiones corporales es el 80 % de la reserva del ramo y por sí sola mueve el nivel un 1 % con b fuera de 0,942 a 1,058. En edificios el hundimiento pesa un 33 % y necesita un error de unos trece puntos.

## Lo que dicen los abiertos frente a los cerrados

El supuesto S1 dice que, dentro de un mismo ramo, peligro y trimestre de reporte, lo que acaba costando un siniestro no depende de cuánto tarde en cerrarse. Si S1 se cumple y las reservas son insesgadas, los abiertos de una celda deberían acabar costando lo mismo, en media, que los cerrados de esa celda. De ahí sale un estimador directo, β: la reserva que haría falta para que los abiertos cuesten como los cerrados de su celda, dividida por la reserva contabilizada. β por encima de 1 indicaría reservas cortas y por debajo, holgadas. Solo cuentan las celdas con al menos 20 cerrados y el intervalo al 90 % sale de 400 réplicas de bootstrap por siniestro.

| Ramo y peligro | Abiertos | Reserva (M CU) | Peso en la reserva del ramo | β | Intervalo al 90 % | Prueba de S1 (t) |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Autos, total | 7.422 | 63,70 | 100 % | 0,851 | 0,613 a 1,106 | 0,36 |
| Autos, lesiones corporales | 2.867 | 51,13 | 80 % | 0,824 | 0,550 a 1,154 | 0,44 |
| Autos, daños a terceros | 2.094 | 6,82 | 11 % | 0,963 | 0,902 a 1,039 | 0,55 |
| Autos, daños propios | 1.990 | 4,13 | 6 % | 0,951 | 0,881 a 1,028 | −0,77 |
| Edificios, total | 1.889 | 23,82 | 100 % | 0,985 | 0,873 a 1,109 | −0,22 |
| Edificios, hundimiento | 389 | 7,76 | 33 % | 0,997 | 0,829 a 1,202 | 1,15 |
| Edificios, inundación | 236 | 6,53 | 27 % | 0,942 | 0,739 a 1,242 | 0,61 |
| Edificios, incendio | 149 | 4,52 | 19 % | 1,193 | 0,840 a 1,701 | −0,72 |
| Contenidos, total | 809 | 2,65 | 100 % | 0,982 | 0,787 a 1,156 | 0,81 |
| Contenidos, inundación | 129 | 1,16 | 44 % | 1,017 | 0,590 a 1,432 | 2,86 |

Ninguna estimación apunta a reservas cortas: en los tres ramos β queda en 0,85 a 0,99, y en autos la cifra puntual sugiere que lesiones corporales está reservada con holgura. Pero los intervalos son anchos, sobre todo en lesiones, donde un solo siniestro de 11,9 millones de CU pesa mucho, y en los tres ramos cruzan los umbrales de quiebre. Con el criterio fijado antes de calcular, la reserva de caso queda como incertidumbre material en autos, edificios y contenidos.

La columna de la prueba de S1 mira una consecuencia observable del supuesto. Si los siniestros grandes tardaran más en cerrarse, el cociente entre abiertos y cerrados de una celda cambiaría con la fracción ya cerrada de esa celda. Esa relación no aparece en ningún peligro con reserva importante salvo inundación de contenidos (t = 2,86 con cinco celdas), donde β no debe leerse como sesgo. En edificios, las celdas con al menos 20 cerrados cubren el 69 % de la reserva de hundimiento y el 58 % de la de incendio; en autos y contenidos, toda.

## El IBNR de lesiones corporales parece valorado con una severidad alta

Los siniestros de 2024 que aún no se habían reportado al 31 de diciembre forman el IBNR. D67 contó cuántos faltan con un chain-ladder y les dio una severidad: la media de 2021-2022 en los peligros cortos y, en lesiones corporales y hundimiento, la media de los reportados más de 365 días después del siniestro. El supuesto S3 propone otro análogo, que reproduce la misma selección por demora: los siniestros de 2021 y 2022 que se reportaron después del 31 de diciembre de su año de ocurrencia. El cociente k entre su severidad media y la usada por D67 dice cuánto se aparta el coste por aviso tardío.

| Peligro | Severidad usada por D67 (CU) | Avisos tardíos 2021-2022 | Severidad de los tardíos (CU) | k | Intervalo al 90 % | Umbral de k | Nivel 2025 con ese k |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| Autos, lesiones corporales | 25.774 | 1.893 | 22.354 | 0,867 | 0,813 a 0,922 | 0,940 a 1,059 | −2,2 % |
| Edificios, hundimiento | 18.691 | 205 | 21.097 | 1,129 | 1,002 a 1,260 | 0,736 a 1,263 | +0,5 % |

En lesiones corporales el intervalo entero queda por debajo del umbral. D67 eligió el subconjunto de demoras más largas, que es más caro (25.774 CU con 582 siniestros), mientras que el análogo completo de los avisos posteriores al cierre del año cuesta 22.354 CU, con cifras casi iguales por año (k = 0,861 en 2021 y 0,874 en 2022). Si S3 se cumple, el IBNR de lesiones de 2024 (23,5 M CU) estaría sobrevalorado en torno a un 13 % y el nivel 2025 de autos quedaría alto en un 2,2 % (entre 1,3 % y 3,1 %), por encima de la materialidad. Dos cosas empujan en el mismo sentido y otra en contra. Entre los tardíos de 2021 y 2022 todavía están abiertos el 21 % y el 37 %, y la reserva de lesiones parece holgada; además, la severidad de lesiones bajó desde 2023 (los tardíos de 2023 ya observados dan k = 0,66, con la cohorte incompleta). En contra, los avisos de 2022 con demoras de más de dos años aún no se ven y podrían ser más caros. Ninguno de los demás peligros mueve el nivel más de un 0,5 %.

Es un indicio, no un cambio adoptado: la severidad de D67 es una elección conservadora y documentada, y cambiarla le toca al revisor humano. Si se aceptara S3, la corrección iría en la exposición efectiva de lesiones, sin tocar T0.

## La elección entre S30 y S22 no depende de las reservas

Con las etiquetas modificadas por cualquier b uniforme entre 0,25 y 2,5, y también con b aplicado solo a lesiones corporales, S30 sigue por delante de S22 en el agregado de los tres ramos, en V24 y en V23. La batería de sensibilidad de la otra sesión de Claude (E03) lo había medido con 0,75 y 1,25; aquí se extiende a toda la rejilla. Por ramo hay inversiones que no llegan al agregado: en autos, V24 cambia de signo si la reserva de lesiones fuera un 50 % corta o si la del resto de peligros fuera holgada en más de un 25 %; en contenidos, si la reserva fuera holgada en más de un 10 %.

## Lo que cuesta un punto de nivel en la métrica

| Ramo | D² V24 de S30 | Nivel −1 % | Nivel +1 % |
| --- | ---: | ---: | ---: |
| Autos | 0,09168 | −0,00007 | +0,00004 |
| Edificios | 0,11580 | −0,00019 | +0,00017 |
| Contenidos | 0,09665 | −0,00005 | +0,00002 |
| Agregado | 0,13788 | −0,00011 | +0,00008 |

Un 1 % de nivel vale en el agregado alrededor de una diezmilésima de D², del mismo orden que la ventaja de S30 sobre S22 en V24 (0,00014). Las cifras se miden contra T0, que no es el último, así que dicen cuánto pesa el nivel en la métrica y no qué nivel es el correcto.

## Abiertos sin reserva y rechazados

Hay 61 abiertos aceptados con reserva cero. Si cada uno se cerrara con la media de los cerrados de su celda, añadirían unos 0,21 M CU en autos repartidos en cuatro años y menos de 0,05 M en hogar, muy por debajo del 0,1 % del coste de cualquier año. Los 1.701 rechazados tienen todos los importes en cero (no hay ninguno en edificios). Si se pagaran todos con la severidad media de su peligro, el nivel 2025 subiría un 1,07 % en autos y un 1,24 % en contenidos; para llegar a la materialidad habría que reabrir y pagar el 93 % de los rechazados de autos o el 81 % de los de contenidos.

## Qué quedó para la revisión humana y cómo se decidió

La suficiencia de la reserva de caso sigue sin acreditarse y, con la materialidad del 1 %, es una incertidumbre material en los tres ramos. Los datos no muestran reservas cortas; muestran que no alcanzan para descartar errores de cuatro puntos. El IBNR de lesiones corporales tiene un indicio de sobrevaloración material bajo S3, que bajaría el nivel de autos en torno a un 2 %. La elección de S30 frente a S22 es robusta a cualquier sesgo de reservas razonable. Lo que resolvería la cuestión es una valoración posterior de los mismos siniestros con `claim_id` estable, o documentación del generador de los organizadores.

El participante lo decidió el 20 de octubre a las 15:21 UTC: «Suficiencia de reservas: Lo dejamos así como limitación del ejercicio» ([registro](../registro/decisiones_participante_20261020.json)). La incertidumbre material de la reserva de caso queda declarada como limitación (hallazgo MOD-002 del enjambre), el supuesto S3 no se adopta y no cambian T0, la receta ni S30.

## Cómo repetirlo

Desde la carpeta común, con Python 3.10 o posterior, pandas y pyarrow:

```text
python herramientas/reservas_consistencia.py privado/corridas/<corrida> datos
python herramientas/reservas_consistencia.py privado/corridas/<corrida> a
python herramientas/reservas_consistencia.py privado/corridas/<corrida> b
python herramientas/reservas_consistencia.py privado/corridas/<corrida> resumen
```

La corrida debe contener `PLAN_PREREGISTRO.md`; los resultados quedan en `resultados/`. La parte a admite un ramo como tercer argumento para repartir el tiempo de cálculo.

## Anexo: archivos y huellas

| Archivo | SHA-256 |
| --- | --- |
| `registro/autorizacion_reproduccion_reservas_20261019.json` | `0d2001c4586393cb56d64290f20bf483345d4e8532fecc10bed9750a007cda5f` |
| `privado/corridas/reservas_20261019T225357Z_99b45271/PLAN_PREREGISTRO.md` | `52429a4f0069cac8ca6a73712ebdb3f0a65bec2153cbb9331dfd2b38db4409d4` |
| `herramientas/reservas_consistencia.py` | `e16680ec62e90bc8c4e49865010f7d088aaef967e479fed406bc6befa5be5d78` |
| `…/resultados/datos.json` | `9cc0647b034847f9c02540e3842af218c5a48fce3944f5f4313d2f589cda8a8a` |
| `…/resultados/parte_a.json` | `b65a7ca0f6f9788d5173f773052a031395910256d4ce26ff45dd093a3ab48b78` |
| `…/resultados/parte_b.json` | `6b266fda32082e38e3ee688c441556005d0cce27f15ae713a8c3e7d94fb0fb0e` |
| `…/resultados/resumen.json` | `5db16ea0950f93d13e1e45f8665a7b1a5f1ba41d7d2a0e1fdf3cd02d4ea0677a` |
| `Semana 1/Limpieza/runs/preaudit_20261016T211816Z_817285a5/data/claims.parquet` | `31b1d8007ca9ee3a6dd00e73f99e7a7fc0d1fb8b13087b687342c999bd7b8336` |
| `Semana 1/Bases_actuariales_claude/runs/bases_20261017T120251Z_45443ff0/tables/asignacion_por_siniestro.parquet` | `535327e1bbba95f171820d27e345988b3c2cbdeec6f86eefefaedefc52992ae5` |
| `…/tables/t0_por_row_id.parquet` | `caa8294e1d89dca5dfdc8b3de4db3f9a6fc2cba930506ec96a6abf5c31d3b340` |
| `…/tables/ibnr_por_peligro_anio.csv` | `4e1a723c0aa5691c64384fad32d6062b074a9794d72a4138a6f020f5ea572d71` |
| `…/tables/ibnr_2024_por_peligro.csv` | `bcf2a764c073a16dff77a9c55c3bbc2b269533fefa0b22d86d5eaba7953ae51c` |
| `Semana 1/Modelos_claude_b/experimentos/predicciones_v23_v24_s30.parquet` | `afd72dca917bf593202fb94cbee9382f5e9c35ea80c8aada81a68a2053d1131e` |
| `Semana 1/Modelos_claude/experimentos/predicciones_v23_v24_s22.parquet` | `22c816319a17e386b04d3901ac87615d3fd1e415a5b3431e55cd5bc093259d7c` |
| `Semana 1/Modelos_claude_b/runs/S30_claude_b/resumen.json` | `c3b2b0be4fd7c0e16638f1ebd83ada2b95faf991347f3a35fd648f56d9ff5992` |

Controles de la etapa de datos: 160.432 aceptados con asignación única, la reserva por fila coincide con la de T0 en todas las filas (diferencia máxima 0), ningún cerrado tiene reserva y los 1.701 rechazados únicos tienen todos los importes en cero. Entorno: máquina virtual del participante, Python 3.10.12, numpy 2.2.6, pandas 2.3.3 y pyarrow 25.0.1. Una comprobación se añadió después de ver la parte A y está marcada así en `resumen.json`: el k de lesiones y de hundimiento por año de ocurrencia.
