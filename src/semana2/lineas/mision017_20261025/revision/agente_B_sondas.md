# Revisión B: sondas por celda y de forma

Scripts y salidas en `revision/scripts_B/`.

## 1. Identidad

Con p = 1,5, d(y, μ) = 4y/√μ + 4√μ − 8√y. Escalar la celda s de g a gK cambia la desviación en 4[(gK)^−½ − g^−½]Σy/√μ + 4[(gK)^½ − g^½]Σ√μ. Al dividir por D₀ salen a_s y b_s, cuya suma da βA y βB. F es exactamente mezcla × g. Signos, base y despeje son correctos, y a_deducida = βA − Σa_s también. Reproduzco βA = 0,62133, βB = 0,50800 y D²(g) = 0,159480; la identidad se cumple con error 4e‑16.

## 2. Público aleatorio

2024 remuestreado al tamaño de 2025, predicción A1 llevada a c*_g = 1,223, 1/3 público al azar, redondeo a 5 decimales, 1.000 réplicas. Error de log c*_s:

| celda | RMS | p95 | σ_s |
|---|---|---|---|
| contents_0 | 0,34 % | 0,70 % | 18,7 % |
| buildings_0 | 1,13 % | 2,32 % | 26,7 % |
| motor_0 | 0,12 % | 0,25 % | 9,7 % |
| contents_1 | 0,16 % | 0,34 % | 12,0 % |
| buildings_1 | 0,75 % | 1,56 % | 12,4 % |
| motor_1 | 0,12 % | 0,23 % | 7,9 % |

El sesgo queda bajo 0,06 %. El error viene sobre todo de la cuota (desvío de 0,5 a 1,3 %, atenuado por el factor 1,301/c* − 1). El redondeo aporta como mucho 0,2 %. El supuesto se tolera bien. Lo que el método no detecta es un público que no sea aleatorio.

## 3. Sondas observadas

| celda | a_s | c*_s (redondeo) | log c*_s/c*_g | límite |
|---|---|---|---|---|
| contents_0 | 0,01803 | 0,919 (0,911–0,926) | −0,286 | 0,70 |
| buildings_0 | 0,02640 | 0,773 (0,768–0,779) | −0,458 | 0,80 |
| motor_0 | 0,06831 | 1,192 (1,189–1,194) | −0,026 | 0,70 |
| contents_1 | 0,07028 | 1,075 (1,073–1,078) | −0,129 | 0,70 |

Ninguna a_s ≤ 0 ni ninguna parada. Para la celda deducida, c*_m1 = (0,43831 − a_b1)/0,21920. Si D²(buildings_1) vale 0,1575, 0,1585 o 0,1592, sale c*_m1 = 1,45, 1,39 o 1,35. Solo hay parada si D²_b1 < 0,15325.

## 4. Resolutor

Con recibos generados a partir de c* conocidos (0,92; 0,77; 1,19; 1,08; 1,15; 1,4096) recupera 0,9186; 0,7698; 1,1897; 1,0809; 1,1496; 1,4097. Con `recibos_prueba.json` coincide con mi cálculo. Los CSV tienen 209.063 filas, orden idéntico, valores positivos, SHA correcto y factor f_s/g constante por celda.

Desviación: ante la parada |log| escribe los archivos, contra la preinscripción. Borré los sintéticos.

## 5. Sondas de forma

Las seis cambian exactamente las filas de su celda y ninguna fuera (comparación de texto). SHA y orden correctos.

## 6. Error lógico: `kopt` eleva al cuadrado

`kopt` (forma_local.py) devuelve (Σy/√m ÷ Σ√m)², pero el óptimo es la razón sin cuadrado. Por eso todas las razones de nivel salen al cuadrado:

| razón | publicada | correcta |
|---|---|---|
| F1 motor_1 / motor_0 | 0,8464 / 0,9341 | 0,9200 / 0,9665 |
| motor_1 a = 0,3 / 0,7 | 0,8335 / 0,8787 | 0,9130 / 0,9374 |
| buildings_1 a = 0,7 / 1,3 | 0,8353 / 1,3553 | 0,9138 / 1,1639 |
| contents_1 a = 0,7 / 1,3 | 0,9069 / 1,2011 | 0,9523 / 1,0959 |

La ganancia de forma se mantiene: NCB más forma aporta entre 0,0042 y 0,0059 en 2024.

Aplicar f_s/g sobre F1 no cuenta nada dos veces. R corrige el cambio de nivel óptimo que trae la forma, y f_s/g el nivel de la celda medido con la mezcla. Pero eso exige que R sea neutral. Con el error, motor_1 queda un 8,0 % baja y motor_0 un 3,4 %. Si c*_m1 ≈ 1,4, F1_celda_credible pierde ≈ 0,0009 de D² público.

Corrección: reconstruir F1 con la razón correcta, o multiplicar motor_1 por 1,0870 y motor_0 por 1,0347.

En las sondas de forma el error desnivela los puntos de la parábola. Solo por nivel, motor_1 a = 0,7 gana entre 0,0004 y 0,0006 y buildings_1 a = 1,3 pierde hasta 0,0024. Con la razón correcta el efecto queda bajo 0,0001. Hay que regenerarlas antes de enviarlas.
