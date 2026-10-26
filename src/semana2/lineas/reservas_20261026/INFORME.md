# Reservas del mercado emergente y el modelo actual (F3c)

Claude (Cowork, línea principal), 26 de octubre de 2026. Responde a la petición del participante en esta sesión: «Actualiza y recalcula la acreditación de reserva (y los adicionales que sean necesarios), al trabajo, el modelo y la información de la segunda semana, el modelo actual». Es trabajo de IA, sin revisión humana, y no es una valoración actuarial independiente. No cambia F3c ni ningún archivo de su cadena, no envía nada y no toca la selección.

El plan se escribió antes de calcular: [`PREINSCRIPCION.md`](PREINSCRIPCION.md) (SHA-256 67abc8e2…00c6), guardado en el equipo a las 13:49:39 UTC; la primera etapa de cálculo empezó a las 13:53:19 UTC ([`resultados/datos.json`](resultados/datos.json)). Lo que se calculó fuera del plan está marcado como no preinscrito. Cada cifra de este informe sale de los JSON de [`resultados/`](resultados/), y [`verificar_informe.py`](verificar_informe.py) la recalcula y comprueba que está escrita tal cual.

![Semáforo de reservas para F3c por ramo](figuras/fig0_resumen.png)

## En una página

F3c fija su nivel de 2025 con sondas del marcador público, y el marcador no depende de nuestras reservas. Por eso un error en las reservas del emergente llega muy amortiguado al nivel de 2025. De cada punto de error en el nivel base de la mezcla, a F3c le llega una fracción que va de 0,141 a 0,505 según la celda, y 0,146 si el error fuera igual en los tres ramos. Sin sondas llegaría el punto entero.

La suficiencia de la reserva de caso sigue sin poder acreditarse. Con la regla de la semana 1 y la materialidad del 1 % del nivel 2025 de cada ramo, queda como incertidumbre material en autos, edificios y contenidos, porque los intervalos de β del emergente son anchos y cruzan el umbral. En autos, por poco: el intervalo al 90 % baja hasta 0,647 y F3c se movería un 1 % con b = 0,697. Con la β puntual, el nivel de F3c cambiaría −0,66 % en autos, −0,10 % en edificios y +0,47 % en contenidos.

El IBNR queda acotado en los tres ramos. El backtest de la cohorte 2023, que es lo nuevo que permiten estos datos, da un resultado adverso en lesiones corporales: el coste que llegó tarde fue un 42,7 % mayor de lo que prevé la curva del desarrollado (IC90 1,021 a 2,021). Aun así, en F3c ese desvío sube el nivel de autos solo un 0,36 %, porque la sonda lo absorbe casi entero.

La estructura apenas se mueve. Con los escenarios de reserva, el exponente que inclina las relatividades cambia como mucho 0,021, y los factores de F2 y F3c, con la credibilidad que usan, menos de 0,026 en logaritmo (esta última, lectura no preinscrita).

Como lectura no preinscrita, con β y k_e en sus valores puntuales a la vez F3c se movería −0,36 % en autos, −0,11 % en edificios y +0,27 % en contenidos, todo dentro del 1 %.

Propongo al participante, que es quien decide, extender a la entrega de la semana 2 (F3c y, si se envía, F3d) la limitación declarada que decidió el 20 de octubre y mantuvo el 23 para S41, sin cambiar T0, la receta ni el modelo.

## 1. Cómo puede llegar un error de reservas a F3c

Las etiquetas de entrenamiento del emergente son T0: para cada póliza y periodo de 2023 y 2024, el incurrido menos los recobros de sus siniestros aceptados, valorado al 31 de diciembre de 2024. En un siniestro cerrado, el incurrido es lo pagado. En uno abierto incluye la reserva de caso, la previsión del tramitador de lo que falta por pagar. Los siniestros ocurridos que aún no se han comunicado (el IBNR) no están en T0: el modelo los tiene en cuenta reduciendo la exposición de cada fila por su completitud de reporte, la fracción del coste que la curva del desarrollado espera ya reportada a esa fecha.

Las etiquetas de los organizadores para 2025 no dependen de nuestras reservas. Lo que sí depende de ellas es cómo aprende F3c, y la figura 2 sigue ese camino con un ejemplo. Si la reserva de caso de los abiertos de autos se equivoca por un factor b = 0,75, T0 de autos baja un 5,52 % y el nivel base de la mezcla otro tanto (−5,55 %). Las sondas del público corrigen ese nivel hacia el óptimo que mide el marcador en nivel absoluto, con una credibilidad Z: la global con Z_g = 0,854 y las de cada celda (ramo por nuevo negocio o renovación) con Z_s entre 0,36 y 0,866. Al final el nivel 2025 de F3c en autos cambia −0,82 %. Una sonda con Z = 1 copiaría el óptimo del público y borraría cualquier error de nivel base; con Z = 0 no corregiría nada.

![Cadena de nivel de F3c y cuánto de un error de nivel base llega al final](figuras/fig2_cadena.png)

Con una sola valoración no se puede saber si una reserva es exacta. Sí se puede medir cuánto tendría que equivocarse para mover el nivel 2025 de F3c más de un 1 %, y comparar ese umbral con lo que sugieren los datos. Para eso se usan dos multiplicadores:

- b multiplica la reserva de caso de los abiertos: b = 0,75 quiere decir que de verdad faltaba por pagar un 25 % menos de lo reservado. β es la estimación de b que dan los datos bajo un supuesto escrito (sección 3).
- k multiplica el coste aún no reportado: con k = 1,25 hay un 25 % más de IBNR del que prevé la curva. k_e es su estimación con el backtest de la cohorte 2023 (sección 4).

La clasificación es la de la semana 1: «acotado» si el intervalo al 90 % de β (o de k_e) queda dentro del intervalo de b (o de k) que mueve F3c menos de un 1 %; «indicio de desvío material» si queda entero fuera; «incertidumbre material» si lo cruza.

## 2. Cuánto de T0 es todavía estimación (parte A)

T0 suma 27.997.991,57 CU, la misma cifra que obtuvieron Codex y la validación de datos: el control coincidió al céntimo y la regla de parada no hizo falta. De ese total, 4.995.797,64 CU (17,8 %) es reserva de caso de 1.055 siniestros abiertos (5 de ellos sin reserva). El peso cambia mucho con el año: 9,3 % en 2023 y 28,1 % en 2024. Las cifras de 2023 coinciden al céntimo con las de Codex en `docs/semana2/NIVEL_C0_REPORTES_Y_RESERVAS_2023.md`.

| Ramo y año | T0 (CU) | Reserva de caso (CU) | Reserva / T0 | Abiertos | Completitud media de coste | IBNR implícito (CU) |
|---|---:|---:|---:|---:|---:|---:|
| Autos 2023 | 8.162.761 | 1.137.404 | 13,9 % | 130 | 0,975 | 213.475 |
| Autos 2024 | 7.693.127 | 2.363.988 | 30,7 % | 709 | 0,803 | 1.891.350 |
| Edificios 2023 | 5.848.688 | 290.511 | 5,0 % | 21 | 0,996 | 23.393 |
| Edificios 2024 | 3.710.061 | 1.010.188 | 27,2 % | 136 | 0,942 | 227.313 |
| Contenidos 2023 | 1.285.655 | 0 | 0,0 % | 0 | 0,996 | 4.980 |
| Contenidos 2024 | 1.297.700 | 193.707 | 14,9 % | 59 | 0,964 | 48.963 |

El IBNR implícito es T0 dividido por la completitud media menos T0; solo sirve para dar escala, porque el modelo aplica la completitud fila a fila.

![Composición de T0 por ramo y año, y reserva por peligro](figuras/fig1_reservas.png)

La reserva se concentra en pocos peligros. Lesiones corporales de autos tiene 2.447.771 CU en 260 abiertos: el 69,9 % de la reserva de autos y el 49,0 % de toda la reserva. 125 de esos abiertos son de 2023 y llevan más de un año sin cerrarse. En edificios pesan inundación (39,7 %), hundimiento (21,4 %, con 28 abiertos) e incendio (18,8 %); en contenidos, inundación (60,9 %).

El nuevo negocio lleva proporcionalmente más reserva que la renovación: en autos, 30,6 % de su T0 frente a 20,9 %; en edificios, 27,5 % frente a 12,7 %; en contenidos, 16,2 % frente a 6,6 %. Importa para 2025, donde el 76,0 % de las filas son de nuevo negocio, frente al 13,8 % de 2023-2024. El nuevo negocio pesa el 84,8 % del total de F3c en autos, el 79,6 % en edificios y el 78,5 % en contenidos, así que domina el nivel de cada ramo.

Los recobros solo aparecen en autos y solo en siniestros cerrados: daños propios recupera el 24,0 % de su incurrido y robo el 3,9 %. Los abiertos no llevan ningún recobro. Si acabaran recuperando como los cerrados de su peligro, T0 de autos estaría sobrestimado en 97.361 CU (0,61 %).

Hay 107 siniestros rechazados en autos y 13 en contenidos, todos con importes a cero. Si cada uno se pagara al coste medio de un cerrado aceptado de su peligro, T0 subiría un 1,64 % en autos y un 1,06 % en contenidos. Otros 36 siniestros no caen en ningún periodo de su póliza (1 abierto, 92.267 CU netos) y quedan fuera de T0, como en `etiquetas.py`.

## 3. ¿Acierta la reserva de caso? (parte B)

Sin una valoración posterior, la reserva solo se puede juzgar comparándola con algo. El supuesto S1 de la semana 1 dice que, dentro de un ramo, un peligro y un trimestre de reporte, lo que acaba costando un siniestro no depende de cuánto tarde en cerrarse. Si S1 vale, los abiertos de una celda deberían costar en media lo mismo que sus cerrados, y β es la reserva que haría falta para conseguirlo dividida por la reserva contabilizada. Con β = 1 la reserva acierta en media; con β = 0,8 sobra un 20 %.

El código y las definiciones son los de la semana 1: celdas con al menos 20 cerrados, intervalo al 90 % con 400 réplicas Poisson por siniestro (semilla 20261026) y la prueba A2 de S1, la pendiente del logaritmo del cociente abiertos/cerrados frente al logit de la fracción cerrada (contradice S1 si |t| > 2).

| Grupo | β emergente | IC90 | Reserva en celdas con 20 cerrados | t de A2 | β desarrollado | Emergente − desarrollado, IC90 |
|---|---:|---:|---:|---:|---:|---:|
| Autos | 0,797 | 0,647 a 0,997 | 65,5 % | 1,56 | 0,850 | −0,381 a 0,258 |
| Autos: lesiones corporales | 0,758 | 0,512 a 1,077 | 55,1 % | 0,07 | 0,823 | −0,485 a 0,342 |
| Autos: resto de peligros | 0,852 | 0,729 a 1,012 | 89,6 % | 2,80 | 0,962 | −0,256 a 0,068 |
| Edificios | 0,974 | 0,500 a 1,333 | 9,9 % | 2 celdas | 0,985 | −0,514 a 0,354 |
| Edificios: hundimiento | sin celdas | | 0 % | | 0,996 | |
| Edificios: resto de peligros | 0,974 | 0,487 a 1,335 | 12,6 % | 2 celdas | 0,980 | −0,487 a 0,354 |
| Contenidos | 1,222 | 0,740 a 2,078 | 33,9 % | 2 celdas | 0,983 | −0,236 a 1,139 |

«2 celdas» quiere decir que A2 no se puede calcular. La β del desarrollado se recalculó con el mismo código; la de la semana 1 era 0,851 en autos, 0,985 en edificios y 0,982 en contenidos.

![β del emergente y del desarrollado frente a los umbrales de F3c](figuras/fig4_beta.png)

Ninguna diferencia con el desarrollado excluye el cero, como preveía H1: el generador parece el mismo en los dos mercados. Las estimaciones puntuales del emergente sugieren reservas holgadas en autos y algo cortas en contenidos, pero los intervalos son anchos. Hay pocos cerrados comparables: las celdas con 20 cerrados cubren el 65,5 % de la reserva de autos, el 33,9 % de la de contenidos y solo el 9,9 % de la de edificios. Hundimiento y el nuevo negocio de edificios y de contenidos no tienen ninguna celda. En lesiones corporales, que concentra la reserva, hay 189 cerrados para 260 abiertos.

La prueba A2 contradice S1 en el resto de peligros de autos (t = 2,80) y, al separar por negocio, en la renovación de autos (t = 2,18) y en el nuevo negocio con el signo contrario (t = −2,72). En lesiones no la contradice (t = 0,07). β depende de S1, y en esos subconjuntos S1 falla; es una razón más para no leerla como una medida de la reserva.

Como ninguna diferencia excluye el cero, el plan permite una lectura secundaria con β agrupado de los dos mercados, mucho más estrecha: autos 0,849 (0,617 a 1,085), edificios 0,984 (0,874 a 1,113) y contenidos 0,988 (0,819 a 1,136).

## 4. ¿Llega tarde el coste que se espera? (parte C)

La completitud de reporte sale de una curva del desarrollado: por ramo y peligro, qué fracción del coste se ha comunicado a cada edad, con los siniestros aceptados de al menos 1.095 días de desarrollo. Estos datos permiten algo que la semana 1 no podía hacer, que es comprobar esa curva en el propio emergente. Los siniestros ocurridos en 2023 tienen, a 31 de diciembre de 2024, un año entero de reporte posterior. La curva dice qué parte de su coste debía llegar en 2024 dado lo que llegó en 2023, y k_e compara lo que llegó de verdad con esa previsión. Con k_e = 1 la curva acierta; por encima de 1 llega más coste tarde del previsto, y el IBNR que usa el modelo para 2024 se quedaría corto.

| Grupo | Siniestros de 2023 | Reportados en 2024 | k_e (coste) | IC90 | k en número | IC90 |
|---|---:|---:|---:|---:|---:|---:|
| Autos | 3.557 | 234 | 1,267 | 0,912 a 1,718 | 0,873 | 0,774 a 0,987 |
| Autos: lesiones corporales | 266 | 105 | 1,427 | 1,021 a 2,021 | 0,916 | 0,739 a 1,140 |
| Autos: resto de peligros | 3.291 | 129 | 0,694 | 0,541 a 0,886 | 0,840 | 0,721 a 0,971 |
| Edificios | 519 | 40 | 0,991 | 0,551 a 1,686 | 1,351 | 0,967 a 1,794 |
| Edificios: hundimiento | 32 | 10 | 0,946 | 0,282 a 2,135 | 0,967 | 0,451 a 1,679 |
| Edificios: resto de peligros | 487 | 30 | 1,041 | 0,566 a 1,675 | 1,557 | 1,105 a 2,051 |
| Contenidos | 491 | 21 | 0,674 | 0,230 a 1,271 | 1,235 | 0,786 a 1,674 |

![Backtest del IBNR en la cohorte 2023](figuras/fig5_ibnr.png)

En lesiones corporales llegó tarde un 42,7 % más de coste del previsto (1.444.498 CU frente a 1.012.492), y el intervalo excluye el 1 por poco. El número de siniestros tardíos sí es el previsto (k en número 0,916): llegan los que se esperaban, pero más caros. 65 de esos 105 tardíos siguen abiertos, así que parte de su coste es reserva de caso; si esa reserva se escala por la β de lesiones, k_e baja a 1,365 (lectura no preinscrita, sección 8). En el resto de peligros de autos pasa lo contrario, con k_e 0,694, y los dos efectos se compensan en el ramo.

H4 preveía k_e compatible con 1, porque los retrasos no difieren entre mercados (prueba de Kolmogórov-Smirnov de CLA-S2-20261023-001). Falla en lesiones corporales y en el resto de peligros de autos, en direcciones opuestas. En número salen del 1 autos (0,873), el resto de peligros de autos (0,840) y el resto de edificios (1,557). Son 14 intervalos al 90 % sobre grupos que se solapan: por azar cabría esperar uno o dos fuera del 1, y hay 5. Esta cuenta no estaba en el plan.

En la semana 1, el supuesto S3, que no se adoptó, daba para lesiones del desarrollado un k de 0,867, es decir, un IBNR sobrevalorado. El backtest del emergente apunta en la dirección contraria, así que tampoco aquí hay base para adoptar S3.

## 5. Del dato al nivel de F3c (parte D)

Para cada ramo se calcula cómo cambia el nivel base de la mezcla con las etiquetas de cada escenario y cómo pasa ese cambio por las sondas hasta el nivel 2025 de F3c. La reconstrucción de los factores de nivel por celda reproduce los de la cadena con una diferencia relativa máxima de 4,9 × 10⁻⁷. Los pasos de F2 y de los factores conservan el nivel de cada celda con un cociente de escalares Tweedie sobre las mismas etiquetas; no se recalcularon por escenario y el plan lo declaró como supuesto (la sección 6 lo acota).

Con un error que afecte a un solo ramo, la fracción que llega a cada celda es (1 − Z_s) + (Z_s − Z_g) · w_r, con w_r el peso del ramo en la sonda global: 0,571 en autos, 0,274 en edificios y 0,155 en contenidos. Las celdas de los otros ramos se mueven un poco en sentido contrario, porque la sonda global reparte la corrección.

| Celda | Z_s de su sonda | Fracción del error que llega a F3c | Peso en el total 2025 de F3c del ramo |
|---|---:|---:|---:|
| Autos, renovación | 0,810 | 0,165 | 15,2 % |
| Autos, nuevo negocio | 0,866 | 0,141 | 84,8 % |
| Edificios, renovación | 0,360 | 0,505 | 20,4 % |
| Edificios, nuevo negocio | 0,724 | 0,240 | 79,6 % |
| Contenidos, renovación | 0,534 | 0,416 | 21,5 % |
| Contenidos, nuevo negocio | 0,736 | 0,246 | 78,5 % |

La figura 3 muestra la respuesta completa para la reserva de caso; las curvas son una ilustración no preinscrita de los umbrales, que sí lo son. La línea gris es el nivel base de la mezcla, que sin sondas se saldría de la banda del 1 % con errores de reserva de pocos puntos; la azul es F3c, mucho más plana.

![Respuesta del nivel 2025 a la reserva de caso](figuras/fig3_respuesta_b.png)

La tabla reúne los umbrales y la clase de cada escenario. «Hasta» quiere decir que por abajo ningún valor de la rejilla mueve F3c un 1 %, y «cualquiera», que no lo mueve ninguno entre 0 y 20.

| Escenario | b o k que mueven la mezcla menos del 1 % | b o k que mueven F3c menos del 1 % | Estimación (IC90) | Clase para F3c | F3c en la estimación puntual |
|---|---:|---:|---:|---|---:|
| Autos, reserva de caso | 0,955 a 1,045 | 0,697 a 1,321 | β 0,647 a 0,997 | incertidumbre material | −0,66 % |
| Autos, solo lesiones | 0,934 a 1,066 | 0,558 a 1,469 | β 0,512 a 1,077 | incertidumbre material | −0,54 % |
| Autos, resto de peligros | 0,857 a 1,143 | 0,041 a 2,018 | β 0,729 a 1,012 | acotado | −0,15 % |
| Edificios, reserva de caso | 0,926 a 1,074 | 0,751 a 1,255 | β 0,500 a 1,333 | incertidumbre material | −0,10 % |
| Edificios, solo hundimiento | 0,673 a 1,327 | hasta 2,123 | sin β | sin estimación | |
| Edificios, resto de peligros | 0,904 a 1,096 | 0,677 a 1,330 | β 0,487 a 1,335 | incertidumbre material | −0,08 % |
| Contenidos, reserva de caso | 0,866 a 1,134 | 0,533 a 1,479 | β 0,740 a 2,078 | incertidumbre material | +0,47 % |
| Autos, IBNR | 0,885 a 1,121 | 0,341 a 2,001 | k_e 0,912 a 1,718 | acotado | +0,31 % |
| Autos, IBNR de lesiones | 0,855 a 1,160 | 0,243 a 2,572 | k_e 1,021 a 2,021 | acotado | +0,36 % |
| Edificios, IBNR | 0,633 a 1,402 | hasta 2,501 | k_e 0,551 a 1,686 | acotado | −0,01 % |
| Edificios, IBNR de hundimiento | 0,231 a 2,506 | cualquiera de 0 a 20 | k_e 0,282 a 2,135 | acotado | −0,02 % |
| Contenidos, IBNR | 0,522 a 1,489 | hasta 2,800 | k_e 0,230 a 1,271 | acotado | −0,19 % |

Sin las sondas, la mezcla quedaría con incertidumbre material en todos los escenarios con estimación salvo el IBNR del hundimiento: con el k_e puntual de lesiones, por ejemplo, su nivel subiría un 2,48 %, frente al 0,36 % de F3c.

Las variantes del plan son lecturas secundarias y no cambian la clase principal, pero en autos darían otra. Con Z_g = 0,90 el umbral de F3c para la reserva de caso se abre a 0,633 a 1,396, y con el error solo en 2024, a 0,560 a 1,467; en los dos casos autos y lesiones quedarían acotados. Con solo la fórmula de la designada o solo la de la línea ML el umbral apenas cambia (0,696 y 0,699 por abajo). En edificios y contenidos ninguna variante cambia la clase. Con el β agrupado de los dos mercados, la lectura secundaria, quedarían acotados edificios, contenidos, lesiones y los dos «resto de peligros», y autos seguiría con incertidumbre material, porque el intervalo agrupado baja hasta 0,617.

Por celda, lo más expuesto es la renovación de edificios: F3c se mueve un 1 % en esa celda con b fuera de 0,854 a 1,148. Es la celda con la sonda menos creíble (Z_s = 0,36) y por eso con la fracción más alta (0,505). Le sigue la renovación de contenidos (umbral 0,681 a 1,323). Pesa poco en el nivel del ramo porque en 2025 domina el nuevo negocio.

Si el error fuera el mismo en los tres ramos a la vez, la sonda global lo absorbería casi entero. Con b = 0,75 en todo, autos bajaría un 0,83 %, edificios un 0,28 % y contenidos subiría un 0,14 %: al bajar autos, que pesa más en la sonda global, esta sube algo el nivel de los demás.

F3d solo cambia los factores de contenidos. Su umbral de b en contenidos es 0,532569 a 1,479203, frente a 0,532594 a 1,479177 de F3c, así que todo lo anterior vale igual para F3d.

## 6. La estructura: relatividades y factores (parte E)

Un error de reservas que no fuera proporcional en todas las pólizas podría inclinar las relatividades: si las pólizas de más riesgo llevaran más reserva, corregirla cambiaría la pendiente.

E1 lo mide en el emergente con la estructura de T2b. El exponente a que mejor ajusta T0 es 0,889 en autos, 0,959 en edificios y 0,981 en contenidos. Que salga por debajo de 1 ya pasa con T0 y no tiene que ver con las reservas. Con los escenarios de b (0,75, 1,25 y los extremos del intervalo de β), a cambia como mucho 0,021, en edificios con b = 0,5, y el coste en D² de 2023-2024 no pasa de 3,4 × 10⁻⁵.

E2 mira el desarrollado con las predicciones V24 de S30 de la semana 1. Ahí la reserva pesa el 29,2 % del T0 en autos, el 28,1 % en edificios y el 14,1 % en contenidos, y en autos se concentra en el decil de menor predicción (55,9 % de su T0). Un error del 25 % en esa reserva inclinaría el cociente real/esperado de autos con una pendiente de +0,021 (b = 0,75) o −0,017 (b = 1,25) por unidad de logaritmo de la predicción, y en hogar de cinco a seis milésimas. Es del orden de lo que mide E1 y mucho menor que la distancia de a a 1.

![Inclinación de las relatividades y cambio de los factores](figuras/fig6_estructura.png)

E3 mira los factores de F2 (bonificación por años sin siniestros y siniestros previos) y de F3c (género, teletrabajo y segmento). Si un nivel de una variable lleva más reserva que su grupo, un error de reserva cambia su factor. Sin la credibilidad, la cota preinscrita llega a 0,169 en logaritmo (0,01 equivale a un 1 %), en celdas casi vacías: contenidos de nuevo negocio con dos o más siniestros previos tiene 4 filas con coste. Con la credibilidad n/(n+300) que usan `construir_F2.py` y `construir_F3.py`, el mayor cambio baja a 0,026 (segmento mature_affluent de contenidos), 0,016 en autos y 0,007 en edificios. Esta segunda lectura no estaba en el plan. Usa además la ponderación de cada paso (balance en F2, Tweedie en F3c), y por eso en la renovación de contenidos con siniestros previos supera a la cota sin credibilidad.

## 7. Cuánto cuesta un 1 % de nivel en la métrica (parte F)

Con la forma cerrada de cada celda de la sonda, mover un 1 % el nivel de un solo ramo de F3c cambia el D² público como mucho 0,000029. Bajar los tres ramos un 1 % a la vez lo cambiaría +0,000028, y subirlos, −0,000056. Es una aproximación declarada: toma el nivel de F3c en cada celda como el cociente de totales F3c/mezcla y no modela la forma dentro de la celda. Que bajar edificios o contenidos mejore un poco el público viene de las sondas con Z < 1, que dejan esas celdas algo por encima del óptimo medido; las Z se fijaron antes de ver el público y este resultado no las cambia.

Dos resultados de Codex ayudan a leer la escala, sin recalcularlos aquí. En 2023-2024, la ventaja de PUL2 sobre G3 se mantiene entre +0,00251 y +0,00264 de D² con las reservas al 75 % y al 125 %, con colas más pesadas y con revaloración por peligro: esa comparación entre modelos resiste a las reservas, aunque el nivel no. Y con los modelos estándar de Codex, las reservas al 75 % y al 125 % mueven el nivel nominal de 2023 de B14 en −2,484 % y +2,483 %, del orden de lo que se mueve aquí la mezcla sin sondas.

## 8. Lecturas no preinscritas (parte G)

Se añadieron después de ver las partes B a F y no cambian ninguna clase.

- Si la reserva de los tardíos abiertos de lesiones se escala por su β (0,758), k_e de lesiones baja de 1,427 a 1,365: el exceso de coste tardío no se explica solo por reservas altas.
- Con β y k_e puntuales a la vez en cada ramo por separado, la mezcla cambiaría −2,46 % en autos, −0,37 % en edificios y +0,97 % en contenidos, y F3c −0,36 %, −0,11 % y +0,27 %. Con los tres ramos a la vez, F3c cambiaría −0,36 %, +0,15 % y +0,52 %.
- Con la aproximación de balance (el cambio relativo de T0 del ramo como cambio de nivel base), que los abiertos de autos recuperen como los cerrados movería F3c de autos −0,09 %, y pagar los rechazados lo movería +0,24 % en autos y +0,30 % en contenidos.

## 9. Hipótesis previas y desviaciones del plan

| Hipótesis | Qué decía | Resultado |
|---|---|---|
| H1 | β del emergente y del desarrollado no difieren de forma detectable | Se cumple: ninguna diferencia excluye el cero |
| H2 | La sonda global absorbe el 85 % de un error uniforme, autos queda acotado y lo más expuesto es la renovación de hogar | Se cumple en parte. La absorción y la exposición de la renovación de hogar, sí; autos no queda acotado en la reserva de caso (adverso) |
| H4 | k_e compatible con 1 | Adverso en lesiones corporales (por encima) y en el resto de peligros de autos (por debajo) |

Las desviaciones del plan fueron estas:

- E2 se midió con la cuota de reserva por decil de la predicción, porque el archivo de S30 de la semana 1 no trae exposición. El plan pedía el exponente a como en E1.
- La lectura de E3 con credibilidad y toda la parte G se añadieron después de ver los resultados.
- β del desarrollado se recalculó sin asignar los siniestros a su periodo, así que incluye los anteriores a 2023 y los no asignados que la semana 1 excluía. Las cifras apenas cambian (0,8503 frente a 0,8510 en autos).
- En la parte C se añadieron los grupos «resto de peligros», que el plan no nombraba, para ver dónde se compensa el desvío de lesiones.
- El plan pedía una revisión independiente por un subagente antes de publicar, y no se hizo: el participante detuvo su lanzamiento. En su lugar, `revision/recalculo_propio.py` recalcula con código escrito aparte, sin importar el del análisis, T0 por ramo y año, la reserva, β de autos y su cobertura, k_e de lesiones (con su propia curva de reporte), los factores de nivel por celda, la elasticidad de autos y el umbral inferior de b para autos en F3c. Coinciden las 18 comprobaciones. No es una revisión independiente, porque lo escribió la misma sesión de Claude que hizo el análisis.

## 10. Qué queda abierto y qué se propone

Lo que resolvería la reserva de caso es lo mismo que en la semana 1: una valoración posterior de los mismos siniestros con `claim_id` estable, o documentación del generador de los organizadores. Con estos datos:

- La suficiencia de la reserva de caso del emergente no se puede acreditar. Con la regla preinscrita es incertidumbre material en los tres ramos, para F3c y para F3d. El efecto estimado en el nivel 2025 es pequeño (entre −0,66 % y +0,47 % con la β puntual), pero el intervalo de β cruza el umbral. Es la misma clase que dejó la semana 1 para S41, ahora con umbrales mucho más anchos gracias a las sondas.
- El IBNR está acotado para F3c. El backtest de lesiones corporales indica que la curva del desarrollado se queda corta en el coste tardío de ese peligro en el emergente; en F3c eso sube el nivel de autos un 0,36 %.
- La estructura y los factores no se mueven de forma material.

Propongo al participante, que es quien decide, extender a la entrega de la semana 2 (F3c y, si se envía, F3d) la limitación que decidió el 20 de octubre («Suficiencia de reservas: Lo dejamos así como limitación del ejercicio») y mantuvo el 23 para S41, con estas cifras como respaldo, sin cambiar T0, la receta ni el modelo. Hasta que lo confirme, queda como propuesta.

## Archivos y reproducción

Todo está en esta carpeta salvo las tablas por siniestro y por fila, que quedan en `Repositorio_IAA2026/privado/semana2/claude_reservas_20261026/`.

- `PREINSCRIPCION.md`: el plan, escrito antes de calcular.
- `codigo/reservas_s2.py`: el cálculo, por etapas (`python3 reservas_s2.py <raíz> [datos|a|b|c|d|e|f|g]`). La raíz necesita los Parquet del emergente y `claims_desarrollado.parquet` en `datos/`, los CSV y JSON de la cadena de F3c en `cadena/`, las predicciones cruzadas de T2b en `oof/pred/pcv/` y los insumos de la semana 1 en `semana1/`; los SHA-256 de las fuentes están en `resultados/datos.json` y en `manifiesto.json`.
- `codigo/figuras_s2.py`: curvas, contexto y figuras (`python3 figuras_s2.py <raíz> [datos|figuras]`).
- `codigo/INFORME.plantilla.md` y `codigo/renderizar_informe.py`: generan este informe y `cifras_informe.json`.
- `resultados/`: evidencia agregada en JSON, una por parte.
- `verificar_informe.py`: recalcula cada cifra del informe desde `resultados/` y escribe `verificacion_informe.json`.
- `revision/recalculo_propio.py` y `revision/recalculo_propio.json`: el recálculo de cifras clave con código escrito aparte (sección 9).
- `manifiesto.json`: SHA-256 de todos los archivos.
