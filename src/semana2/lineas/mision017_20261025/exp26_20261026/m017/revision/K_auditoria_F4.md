# Auditoría de F4 (revisor K, 25-10-2026)

F4 está bien construido. Mi implementación propia reproduce `exp26/F4_2025.csv` byte a byte (SHA a6bbdb14…), y con pesos 0 reproduce también F3b (SHA 5755513e…). La FSp no tiene fuga: al reentrenarla con mi código salen exactamente las mismas predicciones emergentes, así que solo usa el desarrollado. El problema está en la evidencia. La ganancia que se presenta para la FSp incluye la de los factores. El mecanismo que la motiva, la recalibración por peligro, no aporta nada medible. Y en nuevo negocio, que es el 76 % de 2025, la evidencia local se reparte entre ruido, compresión del orden y signos contrarios según la dirección.

Mi previsión para el paso FSp en el público (F4 − F3b) es +0,0003, con un intervalo del 80 % de −0,0024 a +0,0029 y una probabilidad de empeorar de 0,45 (entre 0,19 y 0,56 según el método de traslado). En edificios de nuevo negocio la probabilidad de empeorar sube a 0,72. Recomiendo no enviar F4 tal cual. La variante que aplica la FSp solo en renovación (`revision/K_F4_soloREN_2025.csv`, SHA 3ffd2b65…) conserva la parte robusta: se espera entre +0,0003 y +0,0006 sobre F3b, con una probabilidad de empeorar de 0,05 a 0,19.

Todo el código es propio (`revision/K_*.py`). Del autor solo uso como datos sus salidas (parquet de la FSp, OOF, archivos 2025, recibos) y, para leer variables y completitud del desarrollado, las utilidades `cargar`, `matriz` y `por_peligro` de la línea ML. Las ganancias están en unidades de D² (1 pb = 0,0001); los pb relativos de la sección 5 son reducciones relativas de Σy/√m.

## 1. La FSp: fuga y corrección

Reentrené las 15 parejas frecuencia-severidad con el desarrollado 2021-2023 y los hiperparámetros del autor (`K_t1c_fsp_reentreno.py`). En los 15 peligros, la correlación del log y la razón de totales frente a los parquet del autor valen 1,0000 para f y para s. La base de entrenamiento solo contiene `market = developed`. El desplazamiento inicial lleva el log de la tasa media: Σf·cp/Σn en el entrenamiento queda entre 0,984 y 0,9998.

Ningún modelo de frecuencia se detuvo en una ronda: el mínimo es 23 (incendio de edificios, dev) y 53 en prod (`K_t1_fsp.json`). Las severidades son débiles. Daños accidentales de edificios se paró en 1 ronda en dev y en 8 en prod, de modo que su severidad es prácticamente constante (sd del log 0,009). Lunas (10 rondas), lesiones (20 y 10) y robo de autos (12) también son casi planas. Eso no rompe nada, porque el nivel de cada peligro lo fija κ.

La completitud es coherente. Conteos y offset usan la misma completitud de reporte ponderada por coste, y el producto κ_f·κ_s coincide con la razón directa de costes con diferencias de 0,03 o menos, salvo en incendio de edificios 2023 (1,86 frente a 2,01, con 49 siniestros) e inundación de contenidos 2023 (1,17 frente a 1,26). Hay una trampa: en los parquet, las filas 2025 tienen cp = 0 en todos los peligros, no 1. La construcción de F4 usa f·s sin cp, así que está bien, pero cualquier reutilización de `fsp_pred` sin `ultimate=True` sobre 2025 daría ceros.

La motivación por mezcla de peligros solo se sostiene en parte (`K_t1b_mezcla.json`, frecuencia y severidad emergente/desarrollado con completitud por peligro):

| Peligro | 2023 | 2024 |
|---|---|---|
| Incendio edificios, frecuencia | ×2,32 (49 siniestros) | ×0,84 (21 siniestros) |
| Incendio, cuota del coste emergente (desarrollado 0,22) | 0,55 | 0,29 |
| Escape de agua edificios, frecuencia | ×0,69 | ×0,66 |
| Lesiones en autos, severidad | ×0,45 | ×0,62 |
| Escape de agua contenidos, frecuencia | ×0,67 | ×0,63 |

El incendio de edificios ×2,3 y su 55 % del coste son de 2023; en 2024 desaparecen. Los κ de edificios cambian mucho de un año a otro: incendio 1,86 / 1,13, tormenta 0,82 / 1,66, escape de agua 0,51 / 0,80. En autos y contenidos son más estables (lunas 1,61 / 1,75). Los κ de producción coinciden con `F4_info.json`. En 2025, tras κ, el incendio pesa el 33 % del coste FSp de edificios y lesiones el 36 % del de autos, cifras compatibles con la experiencia. Los totales 2025 de la FSp no importan, porque la mezcla se reescala al total de ramo y de celda.

## 2. Ganancia fuera de tiempo reproducida

Mi código reproduce la tabla `exp26/fsp_blend_eval.csv` sin diferencias a cinco decimales en las 192 entradas que comparo. Las cifras de cabecera del autor (+0,0045 en 23→24 y +0,0035 en 24→23; ponderado 2025, +0,0011 a +0,0033) comparan «mezcla + factores» con F2 sin factores. Los factores solos ya aportan +0,0021 / +0,0016 sin ponderar, y +0,0093 ponderado en 24→23. El incremento propio de la FSp, con los factores ya puestos y los pesos elegidos, es este (`K_t2_oot.json`):

| Serie | Todas, sin ponderar | Composición 2025 | NB | Renovación |
|---|---|---|---|---|
| 23→24 T2b | +0,0027 | +0,0018 | +0,0021 | +0,0028 |
| 23→24 mezcla | +0,0023 | +0,0015 | +0,0007 | +0,0025 |
| 23→24 A1 | +0,0032 | +0,0022 | +0,0006 | +0,0035 |
| 24→23 T2b | +0,0019 | −0,0060 | −0,0009 | +0,0023 |

En 24→23, con la composición 2025, la FSp se come 0,0060 de los 0,0093 que ganan los factores. Por ramo (T2b, 23→24 / 24→23): autos renovación +0,0014 / +0,0017, autos NB +0,0063 / −0,0028, edificios renovación +0,0024 / +0,0020, edificios NB −0,0013 / −0,0012, contenidos renovación +0,0071 / +0,0051, contenidos NB −0,0028 / +0,0057.

El bootstrap por cliente (1.000 réplicas, los mismos clientes remuestreados en las dos direcciones; media de 23→24 T2b y 24→23) da +0,0022 en el total sin ponderar (IC90 +0,0010 a +0,0035) y +0,0025 en renovación (IC90 +0,0011 a +0,0038), ambos con P(<0) de 0,001 o menos. En NB da +0,0006 (IC90 −0,0022 a +0,0035; P(<0) = 0,37). Con la composición 2025 da −0,0017 en el total (P(<0) = 0,71) y −0,0027 en NB (P(<0) = 0,77). La composición 2025 pesa mucho el NB de año completo, y en local solo hay entre 160 y 500 filas efectivas por celda NB, así que ese bootstrap es muy ancho.

Los pesos están poco sobreajustados en el total sin ponderar. Con las contribuciones por ramo dados los factores (media de las dos direcciones), los pesos elegidos dan +0,0023, la regla fija de 0,25 da +0,0020 y el mejor a posteriori (0,75 / 0,5 / 0,75) da +0,0032. La diferencia con la regla fija viene de contenidos 0,5, que gana en renovación y pierde en NB. La selección cruzada entre direcciones sí es inestable. Si se eligen los pesos en 23→24 con la composición 2025 (0,5 / 0,6 / 0,75), en 24→23 dan −0,0123. Si se eligen en NB, la otra dirección pierde entre 0,0013 y 0,0054.

## 3. Placebos: de dónde sale la ganancia

Sustituí la FSp por alternativas sin información nueva o sin κ (`K_t3_placebo.json`; pesos elegidos, sin factores):

| Variante | 23→24 T2b (total / NB) | 23→24 A1 (total / NB) | 24→23 (total / NB) |
|---|---|---|---|
| V0 FSp con κ (F4) | +0,0027 / +0,0021 | +0,0032 / +0,0007 | +0,0020 / −0,0011 |
| V1 FSp con κ = 1 | +0,0028 / +0,0020 | +0,0034 / +0,0007 | +0,0019 / −0,0007 |
| V3 otro árbol transferido (T2c) | +0,0011 / −0,0001 | +0,0022 / −0,0008 | +0,0007 / −0,0002 |
| V4 compresión pura (F2^a_eff) | −0,0003 / +0,0024 | −0,0001 / +0,0010 | −0,0001 / +0,0002 |
| V5 solo canal κ sobre F2 | −0,0001 / +0,0001 | −0,0001 / +0,0000 | +0,0001 / −0,0004 |

Toda la ganancia viene de mezclar con una estructura distinta. La recalibración por peligro aporta entre −0,00015 y +0,00007. Además, los κ reales quedan en los percentiles 36, 41 y 69 de 200 permutaciones de κ entre peligros, y en edificios en los percentiles 9, 12 y 39: peor que asignarlos al azar. Otro árbol transferido (T2c) consigue entre el 35 % y el 70 % de la ganancia de la FSp. En NB 23→24, la compresión pura del orden de F2 (exponente efectivo 0,94 en motor_1) gana tanto como la FSp. Los datos 2024 prefieren un NB de autos más plano, pero las sondas públicas piden lo contrario en 2025 (vértice 1,32 en motor_1).

Medido en dominio, en el desarrollado 2024 (reentreno propio, T2b guardado), la FSp sí aporta en todos los segmentos. En autos con peso 0,25 gana +0,0025 en renovación de año completo y +0,0033 en NB de año completo (IC90 +0,0016 a +0,0053); la FSp sola ya supera a T2b. En edificios gana +0,0015 y +0,0002 (IC90 −0,0030 a +0,0054). En contenidos, con peso 0,5, gana +0,0032 y +0,0017, este último con un intervalo muy ancho. El valor de la estructura FSp es real, y en NB de año completo es parecido al de renovación en autos, menor en contenidos y casi nulo en edificios.

## 4. Construcción de F4

- Formato: 209.063 filas, cabecera `row_id,prediction`, LF sin CR, el mismo orden de `row_id` que F2 y F3b, identificadores únicos e iguales a los del test, valores finitos y positivos (mínimo 0,0829, máximo 6.252,71), total 84.476.520,05.
- No hay doble conteo. La R de F2 ya está dentro de F2. R4 sustituye a la razón de factores de F3b sin multiplicarse con ella, y cred/g entra una sola vez. La mezcla conserva el total de ramo y luego el de celda, y la forma de motor_1 se aplica con Σ√μ fijo, igual que en F3b.
- F4 frente a F3b por celda, en Σμ: motor_0 0,999; motor_1 0,992; buildings_0 0,988; buildings_1 1,000; contents_0 0,986; contents_1 0,991. La desviación típica de log(F4/F3b) va de 0,04 a 0,10.
- R4 es razonable con pesos iguales por año, pero su parte de mezcla es ruido. En motor_1 la razón de la mezcla vale 1,002 en 2023 y 0,982 en 2024; en contents_1, 0,975 y 1,010. Con la identidad exacta de nivel, F4 queda −0,00006 por nivel frente a F3b. Usar la razón de F3b en lugar de R4 recupera +0,00003; R4 solo con 2023 cuesta −0,00006 y solo con 2024 gana +0,00004 (`K_t4b_checks.json`).
- Dilución de F2. La mezcla geométrica deshace en parte los factores NCB y de siniestros previos de F2, que la FSp no lleva. En 2025, en motor_1 con previos = 1 (factor F2 0,878), la mezcla sube la prima relativa un 5,4 %; en NCB 10+ (1,164) la baja un 2,8 %; en contents_1 con previos = 1 (1,059) la baja un 4,1 %. Si se multiplica la FSp por el multiplicador de F2 antes de mezclar, la estimación local mejora en +0,0009 (23→24) y +0,0026 (24→23), en unidades públicas (`K_t5_public.json`).
- En 2025 la compresión es pequeña: la pendiente de la FSp sobre F2 vale 0,94 en motor_1, 0,87 en buildings_1 y 0,98 en contents_1. El exponente efectivo de motor_1 pasa de 1,298 a 1,278, y según las parábolas de las sondas eso cuesta 0,00006 en el público.

## 5. Previsión pública de F4 frente a F3b

Uso la identidad de J: D²(X) = D²(F) + Σ_s [A_s(1 − 1/s_s) + B_s(1 − s_s)] + Σ_s G_s/s_s. El nivel sale exacto de los archivos. El orden por celda es ΔG_s = g_s·A_s/s_s, donde g_s es la reducción relativa de Σy/√m con Σ√m fijo en la tubería F2 → mezcla → forma → factores reestimados, fuera de tiempo. Separo la compresión, que tiene coste público conocido por las sondas, de la parte ortogonal (`K_t5c_ortogonal.json`, `K_t5d_variantes.json`, `K_t5e_escenarios.json`).

Parte ortogonal por celda, en pb relativos (23→24, media de tres bases / 24→23): motor_0 +23 / +24; motor_1 +56 / −90; buildings_0 +98 / +42; buildings_1 −79 / −17; contents_0 +111 / +97; contents_1 −74 / +163. La renovación es estable. El NB tiene desviaciones bootstrap de 30 a 190 pb y signos que cambian.

| Escenario de traslado | F4 − F3b | P(empeora) |
|---|---|---|
| Emergente, parte ortogonal (media de direcciones) | −0,0003 | 0,56 |
| Emergente con la compresión local incluida | +0,0013 | 0,26 |
| Renovación + NB con el cociente NB/renovación del desarrollado | +0,0018 | 0,19 |
| El anterior trasladado al 24 % (precedente de F2 en J) | +0,0004 | 0,43 |
| Centro | +0,0003 (80 %: −0,0024 a +0,0029) | 0,45 |

La desviación típica de 0,0021 viene sobre todo de la estimación de motor_1 NB (±0,0020). El ruido del tercio público solo añade 0,0005. Con F3b anclado en el F2 medido (0,16033 + nivel + forma + factores +0,0014), F3b quedaría en 0,1663 y F4 en 0,1666. El margen de los factores (−0,001 a +0,003) se suma igual a los dos.

Por partes: la renovación aporta +0,0005 (sd 0,0003, robusta). Edificios NB aporta −0,0006 ± 0,0010 (P(empeora) = 0,72). En motor_1 y contents_1, NB es una moneda al aire con un sesgo leve a favor si se cree el desarrollado.

## 6. Recomendación y problemas por impacto

Recomiendo no enviar F4 tal cual. Como alternativa propongo F4 solo en renovación (`K_F4_soloREN_2025.csv`, construido con `K_t4_build.py --wc=0.25,0,0.25,0,0.5,0`): +0,0005 esperado sobre F3b (+0,0003 si el traslado se queda a la mitad), con P(empeora) de 0,05 en el público y 0,01 en el privado (0,19 con traslado a la mitad). Si se quiere probar la FSp en NB, hay que poner edificios a 0, mezclar FSp × multiplicador de F2 para no diluir NCB y previos, y medir F3b y la variante en el público. La diferencia esperada (±0,002) es cuatro veces el ruido público, así que una lectura decide.

Problemas, de más a menos impacto:

1. La evidencia de NB no sostiene la mezcla. El 76 % de 2025 es NB y la ganancia combinada ponderada a 2025 es −0,0017 (P(<0) = 0,71). La cabecera del autor suma la ganancia de los factores a la de la FSp.
2. Edificios NB es negativo en las cuatro series (parte ortogonal de −17 a −100 pb), y en el desarrollado su ganancia es casi nula. Con peso 0,25 cuesta unas 0,0006 esperadas.
3. El mecanismo declarado no actúa: κ = 1 rinde igual o mejor, los κ reales no se distinguen de permutaciones y el incendio ×2,3 es de un solo año.
4. La mezcla diluye los factores NCB y de previos de F2 (hasta un 5 % por nivel); en local eso cuesta entre 0,0009 y 0,0026.
5. La parte de mezcla de R4 es ruido con signos opuestos por año; cuesta unas 0,00003 en el público.
6. Menores: cp = 0 en las filas 2025 de los parquet (trampa para reutilizaciones), docstring de `fsp_light_prod.py` con años equivocados (dice 2021-2023 y entrena 2021-2024), y severidades casi constantes (daños accidentales de edificios con 1 ronda).

Archivos: `K_lib.py` (implementación), `K_t1*` (FSp), `K_t2_oot.*` (fuera de tiempo y bootstrap), `K_t3_placebo.*`, `K_t4_build.py` y `K_t4b_checks.*` (reconstrucción y comprobaciones), `K_t5*` (previsión), `K_resumen.json`, y los archivos `K_F4_mio`, `K_F3b_mio`, `K_F4_sinedif`, `K_F4_soloREN` y `K_F4_soloREN_sinedif` (`_2025.csv`).
