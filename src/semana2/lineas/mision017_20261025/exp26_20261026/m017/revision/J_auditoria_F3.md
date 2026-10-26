# Auditoría de F3 (revisor J)

F3 está bien construido: mi implementación propia lo reproduce byte a byte y no encontré errores de código ni doble conteo de nivel. Sin la parte de factores, su D² público previsto es 0,1650–0,1651, casi el mismo que el de `final_creible` (0,1651–0,1652). Toda la diferencia de F3 depende de los factores residuales, que no tienen ninguna medición pública: mi previsión central es 0,1665, con un intervalo del 80 % de 0,1643 a 0,1688. El riesgo está concentrado en autos de nuevo negocio, donde la evidencia histórica es casi solo ruido.

Código y cifras en `revision/J_*.py` y `J_*.json` (resumen en `J_resumen.json`). No uso código del autor; sí leo sus tablas para compararlas.

## 1. Reconstrucción y formato

Reimplementé cada paso en `J_lib.py`: factores NCB y previos de F2, forma 0,9 en motor_0, forma de motor_1 con Σμ fijo, cinco factores Tweedie con credibilidad n/(n+300) en log, R3 como media de las cuatro series y resolutor de nivel (`J_reconstruir_F3.py`).

- Mi F3 tiene el mismo SHA que `exp26/F3_2025.csv`: b9139703…a6d765. La diferencia relativa máxima entre filas es 4,7·10⁻⁶ y viene del redondeo a seis decimales de los valores más pequeños.
- Formato: 209.063 filas, el mismo orden de `row_id` que F, cabecera `row_id,prediction`, finales de línea LF sin CR, valores finitos y positivos (mínimo 0,1007, máximo 5.569,38) y total 85.829.230,52.
- Los factores recalculados coinciden con los de `F3_info.json` hasta 4,9·10⁻⁵, que es el redondeo a cuatro decimales; lo mismo pasa con los de F2. R3 coincide hasta 5·10⁻⁵.
- `F3_sinfac` no existía. Lo construí con los mismos pasos y sin factores, con su propio R3: `J_F3_sinfac_2025.csv`, SHA 05b9a2f6…, total 86.269.677,57.
- También reconstruí `final_creible_2025.csv`, que no estaba en disco: `J_final_creible_2025.csv` reproduce el SHA 1a003d86… de `final_salida.txt`.

## 2. Álgebra de nivel

Uso una parametrización exacta. Para cada celda s y cada archivo X defino s_s = Σ√X_s / Σ√F_s (sobre las filas 2025 de la celda; el público es un tercio al azar) y llamo G_s a la ganancia de orden de X medida con el Σ√μ de F. Entonces

D²(X) = D²(F) + Σ_s [A_s(F)(1 − 1/s_s) + B_s(F)(1 − s_s)] + Σ_s G_s/s_s,

con A_s(F) = a_s/√g y B_s(F) = b_s·√g. El primer sumatorio es el nivel y es exacto con los recibos. El segundo es el orden. Esta identidad no supone que la razón Tweedie histórica (la que usan R y R3) ni el Σ√μ fijo sean «neutros»; solo hace falta estimar G.

(a) El resolutor reproduce exactamente los c\*_s de `final_salida.txt`: motor_1 1,38407; motor_0 1,19189; buildings_1 1,20083; contents_1 1,07521; contents_0 0,91859; buildings_0 0,77342. También reproduce cred/g (motor_1 1,11301) y el D² previsto con el nivel creíble sobre F (0,162121).

(b) No hay doble conteo. En cada celda, Σμ(F3) = Σμ(F) × R3 × cred/g exactamente; por ejemplo, en motor_1 1,0358 × 1,1130 = 1,1529, que es la razón observada. La razón de nivel propia de F2 no se aplica en F3 porque R3 la sustituye, y c\*_s entra una sola vez. Lo que sí existe es una interacción. El nivel creíble se calculó para el orden de F, y con un orden mejor el óptimo a Σ√μ fijo baja en G/A, entre un 1,0 % y un 2,7 % en motor_1 según la ganancia de factores que se suponga. Sumar sin más «ganancia de nivel sobre F + ganancias de orden» sobrestima el resultado en 0,00014; en mis previsiones esa interacción ya está incluida. Aun así, F3 queda entre un 2,2 % y un 4,0 % por debajo del óptimo público de su propio orden en motor_1, como pretende la credibilidad, y eso cuesta entre 0,00003 y 0,0001 en el público.

(c) Hay una incoherencia de normalización, pero su efecto es pequeño. El vértice se corrigió con Σ√μ fijo, mientras que el nivel final de F3 usa Σμ fijo y la razón Tweedie histórica. En motor_1, los pasos medidos en Σ√μ y llevados a nivel dan:

- F2: −1,7 % (s = 0,9913).
- Forma con R: +2,75 %. Es la misma fuga que H quitó del vértice, que vuelve a entrar en el nivel final.
- Paso de factores con R3: −1,3 %.

El neto queda en s/objetivo = 0,99828, es decir, un nivel un 0,34 % por debajo de √(cred/g). Eso cuesta 0,000014 en el público, y −0,000012 sumando todas las celdas (`J_prediccion.json`). La cercanía al objetivo sale de efectos que se compensan. R3 de motor_1 es frágil: por serie va de 0,967 (2023) a 1,062 (2024), y tres de las cuatro series comparten los siniestros de 2024. Si se pesan los dos años por igual, R3 baja a 1,0128 y el nivel cae un 2,2 %, con un coste público de unas 0,00013.

Sobre la forma, el vértice exacto con esta parametrización es 1,329. La aproximación lineal de H daba 1,3212, y el redondeo de los recibos solo mueve el vértice con una desviación típica de 0,0027. También probé un modelo de potencia sin ruido, μ ∝ e·r^a0 sobre F2: con a0 = 1,345 y una escala de 1,0016 reproduce los dos puntos de sonda (`J_forma_modelo.py`), así que las sondas de celda y las de forma son coherentes entre sí. Entre a = 1,298, 1,32 y 1,37 hay como mucho 3·10⁻⁵ de D². La sonda a = 1,4 no enviada daría 0,16285 si la curva es cuadrática y 0,16298 si es de potencia; casi coincide con el 0,16296 de la parábola original, de modo que no sirve para comprobar la fuga.

## 3. Previsión del D² público

| Parte | F3 | F3 sin factores | final_creible | Fuente |
|---|---|---|---|---|
| D²(F) | 0,15948 | 0,15948 | 0,15948 | recibo |
| Nivel (exacto) | +0,00261 | +0,00269 | +0,00273 | Σ√ por celda y a_s, b_s |
| Orden de F2 (medido) | +0,00115 | +0,00114 | +0,00114 | 0,00119 con el Σ√ de F, dividido por s |
| Forma | +0,00177 / +0,00185 | +0,00176 / +0,00183 | +0,00177 / +0,00188 | parábola exacta / modelo de potencia |
| Factores | +0,0015 (desconocida) | 0 | 0 | evidencia local |
| Total | 0,1665 (80 %: 0,1643–0,1688) | 0,16507–0,16515 | 0,16511–0,16522 | |

Con una ganancia de factores nula, F3 daría 0,16501–0,16509. Queda 0,00006 por debajo de F3 sin factores porque la parte de R3 que corresponde a los factores baja los niveles.

Para la parte de factores uso G_s ≈ 2·ρ_s·A_s(F), donde ρ_s es la reducción relativa de la desvianza óptima de la celda con pesos de banda de exposición 2025 (`J_local.py`, `J_local2.py`). Los escenarios son estos (en D² con el Σ√μ de F):

- Fuera de tiempo 23→24: −0,0046.
- Fuera de tiempo 24→23: +0,0140.
- Validación cruzada agrupada por cliente: +0,0058.
- Efecto de renovación trasladado al nuevo negocio: +0,0025.
- El mismo traslado calibrado con F2: +0,0006. En el público, la ganancia de orden de F2 fue un 24 % de lo que predecía la evidencia local, que iba de 0,0030 a 0,0073 frente a 0,00119 medidos.

Los extremos vienen de motor_1, cuyo tamaño efectivo histórico es de 821 filas: allí ρ cambia de signo entre direcciones (−112 y +239 puntos básicos). Tomo como centro +0,0015, el punto medio de los dos últimos escenarios. El ruido de muestreo de esta parte es de 0,0014 en el público y 0,0010 en el privado (desviación típica con tamaño efectivo). La cifra de 0,0039 que aparece en `J_prediccion.json` escala sin tamaño efectivo y lo sobrestima.

## 4. F3 frente a final_creible por celda

| Celda | Total F | Total final_creible | Total F3 | F3/FC en Σμ | F3/FC en nivel (Σ√)² | sd log(F3/FC) | a F3 | a FC |
|---|---|---|---|---|---|---|---|---|
| motor_0 | 9,10 M | 8,66 M | 8,57 M | 0,991 | 0,983 | 0,147 | 1 | 1 |
| motor_1 | 40,93 M | 48,47 M | 47,19 M | 0,974 | 0,979 | 0,150 | 1,298 | 1,372 |
| buildings_0 | 5,84 M | 4,95 M | 4,95 M | 1,000 | 1,000 | 0 | 1 | 1 |
| buildings_1 | 19,54 M | 19,31 M | 19,30 M | 0,999 | 1,000 | 0,001 | 1 | 1,002 |
| contents_0 | 1,49 M | 1,28 M | 1,27 M | 0,991 | 0,985 | 0,127 | 1 | 1 |
| contents_1 | 5,04 M | 4,63 M | 4,55 M | 0,983 | 0,989 | 0,132 | 1 | 1,055 |

Los totales son 81,94 M para F, 87,29 M para final_creible y 85,83 M para F3. Fuera de los factores, las dos versiones solo difieren en el nivel y en la forma.

En motor_1, F3 queda un 2,1 % más bajo que final_creible. Un 0,85 % viene de la forma: a = 1,298 tiene una R menor que a = 1,372, y con ella entra menos fuga de nivel. El otro 1,3 % viene del componente de factores de R3. En motor_0 y contents, F3 queda entre un 1,1 % y un 1,7 % más bajo, solo por ese mismo componente.

En el público, el nivel de final_creible da 0,00012 más (0,00273 frente a 0,00261), porque F3 y final_creible están por debajo del óptimo público. La forma deja a las dos versiones a menos de 3·10⁻⁵ una de otra. buildings y contents_1 cambian poco: la forma de contents_1 en final_creible aporta +0,00003.

## 5. Problemas, por impacto esperado en el privado

1. Los factores no tienen medición pública. Calculo una ganancia privada esperada de +0,0015, con un rango aproximado de −0,001 a +0,003 y un ruido de ±0,0010. Pesan en motor_1, que reúne el 76 % de las filas de autos en 2025, y se estiman casi solo con renovación. En renovación la evidencia es estable: género con correlación 0,99 entre años; teletrabajo con A/E de 1,31–1,36 frente a 0,87–0,91 en cada año; todos los pasos positivos en motor_0 y contents_0 en ambas direcciones. Aseguradora previa (40 niveles), ocupación y segmento son inestables, con correlaciones del log-factor entre años de 0,28, 0,40 y 0,48, aunque en renovación aportan algo positivo (+3 a +10 pb). F no codifica ninguna de estas variables, así que no hay doble conteo con F. Recomiendo medir F3 y F3 sin factores en el público antes de elegir: son dos envíos, y la diferencia esperada (+0,0015 ± 0,0014) se puede leer.
2. El nivel de motor_1 depende de cómo se construye R3, que pondera 2024 tres veces más que 2023 y varía del 0,967 al 1,062 entre años. Con pesos iguales por año, el público perdería 0,00013. Además, motor_1 es la celda deducida (βA menos las demás) y hereda los errores de β, con σ de 0,079 entre público y privado. No es un fallo, pero es la mayor sensibilidad de nivel.
3. El componente de factores de R3 se mide en parte dentro de muestra. En motor_0, la razón óptima del paso de factores vale 0,993 dentro de muestra y 0,996 o 1,002 fuera de tiempo. Por eso F3 baja el nivel en torno a un 0,9 % en motor_0 sin respaldo, y eso cuesta unas 0,00006 en el público. En contents_0 la bajada también aparece fuera de tiempo (0,994), así que allí sí tiene base.
4. La interacción entre nivel y orden (−0,00014) afecta a las previsiones que suman componentes, no a los archivos.
5. La forma es inmaterial, con diferencias de 3·10⁻⁵ o menos. No gastaría el envío de a = 1,4 para probar la fuga.

Fuera de la métrica, convendría confirmar que las reglas del concurso permiten tarificar por género.
