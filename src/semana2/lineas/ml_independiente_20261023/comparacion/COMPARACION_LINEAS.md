# MLind frente a las otras líneas: ¿vale la pena enviarlo a Kaggle?

Pregunta del participante, 24 de octubre de 2026: comparar la línea ML independiente con los resultados de los otros modelos para decidir si vale la pena enviarla. Corte: 15:55 UTC. Fuentes: los archivos de la validación nocturna (SHA comprobados: designada f786deb3…224c53aa, A1 4a9f7fc0…15f9, R0 928865e5…cb3e, predicciones de 2024 e4f55f69…7eb7) y los D² del catálogo de Codex que cita CLA-S2-20261024-013. Código: `codigo/comparar_lineas.py`, `comparar_lineas_2.py`, `mezcla_designada.py`.

![Comparación](f10_comparacion_lineas.png)

## 1. En 2023 (desarrollo, mismas 50.094 filas y mismo T0)

| Modelo | D² 2023 |
| --- | --- |
| Tasa por ramo (B00 de Codex / R0 de MLind sin calibrar) | 0,0686 / 0,0683 |
| Mejor del catálogo de Codex, solo emergente (B10) | 0,0942 |
| A1 de la validación nocturna (B10 + 0,0270) | 0,1212 |
| MLind T2b, sin calibrar / con la calibración final | 0,1291 / 0,1233 |

Los pliegues y la exposición efectiva difieren entre líneas (entre la validación nocturna y Codex, la exposición difiere un 0,4 % en total), así que la comparación vale para el orden grueso. La transferencia desde el desarrollado gana al catálogo en las dos líneas que la usan.

## 2. En 2024 (mismas 59.202 filas, mismo T0, remuestreo por componente cliente-dirección)

Las dos líneas ya habían visto 2024 cuando eligieron sus últimas versiones, así que esto es exploratorio.

| Modelo | Todas | Nuevo negocio | Renovación | Ponderado a la cartera 2025 |
| --- | --- | --- | --- | --- |
| R0 tasa por ramo | 0,0728 | 0,1093 | 0,0626 | 0,0617 |
| A1 (base de la designada) | 0,1214 | 0,1223 | 0,1165 | 0,1095 |
| A1fixF1b3n, designada (cifra de su línea) | 0,1244 | | | |
| MLind T2b | 0,1253 | 0,1176 | 0,1216 | 0,1109 |
| Mezcla 50/50 T2b + A1 | 0,1247 | 0,1211 | 0,1205 | 0,1111 |

- **MLind frente a A1:** +0,0038 (IC95 [−0,0004; +0,0081]). Sale de renovación (+0,0051, [+0,0011; +0,0097]). En nuevo negocio pierde −0,0048 ([−0,0193; +0,0068]), con solo 447 siniestros. Ponderado a 2025 queda en +0,0013 ([−0,0037; +0,0062]).
- **MLind frente a la designada:** +0,0009 de punto, sin intervalo, porque las predicciones de 2024 de la designada no quedaron guardadas.
- **Mezcla 50/50:** supera a A1 en +0,0033 ([+0,0011; +0,0057]) y empata con T2b.
- **Ruido del tablero:** en una submuestra del 33 % de las filas, como la del tablero público, la diferencia MLind − A1 tiene una desviación típica de 0,0030.

## 3. Producción 2025

| Archivo | Total (M CU) | Autos | Edificios | Contenidos |
| --- | --- | --- | --- | --- |
| R0 | 61,20 | 456,3 | 418,8 | 90,0 |
| Designada A1fixF1b3n | 67,17 | 519,5 | 434,6 | 93,8 |
| Mezcla 50/50 designada + MLind (preparada, sin enviar) | 69,00 | | | |
| MLind final | 70,82 | 546,8 | 467,5 | 92,7 |
| Designada con tendencia TEN-N2 (A1fixF1nTc) | 71,34 | 545,9 | 472,2 | 98,8 |
| MLind con ajuste de nuevo negocio (C2) | 82,66 | 697,3 | 460,4 | 97,6 |

Las columnas por ramo son tasas en CU por año de exposición. Fila a fila, MLind y la designada correlacionan 0,987 en logaritmo; el cociente entre las dos va de 0,60 a 1,55 entre los percentiles 1 y 99. Si una de las dos fuera la verdad, la otra perdería unos 0,005 de D² en esperanza. Casi toda esa distancia viene de diferencias fila a fila y no del nivel: con el nivel de la designada por ramo, MLind seguiría a 0,0050. En total, MLind está un 5,4 % por encima: autos +5,3 %, edificios +7,6 % y contenidos −1,1 %.

## 4. Lectura

MLind y la designada empatan dentro del ruido. En 2024 MLind va algo por delante en el total, por renovación, pero la cartera de 2025 es un 77 % nueva y en ese segmento la familia A1 va por delante de punto. Cambiar la entrega final por MLind no está justificado.

Comparar los dos archivos en el tablero público tampoco resolvería la duda: el ruido de esa comparación (0,003) es del tamaño de la diferencia esperada. Elegir por ella repetiría el riesgo que D103 corrigió en la semana 1.

Lo que sí tiene respaldo es combinar las dos implementaciones. La mezcla 50/50 mejora a A1 en 2024 y no pierde frente a ninguno. Queda preparada en `Repositorio_IAA2026/privado/semana2/claude_ml_independiente_20261023/mezcla50_designada_mlind_2025.csv` (SHA 12831ef4…db4a, 69,00 M CU), sin enviar.

El mayor valor de un envío está en otra parte. El nivel 2025 es la mayor incertidumbre de todas las líneas, sobre todo el del nuevo negocio de autos, y el tablero público es la única evidencia sobre la cartera del corredor. Además, el primer envío comprobaría si Kaggle ya acepta las 209.063 filas: el anfitrión anunció el arreglo a las 02:57 UTC del 24, pero nadie lo ha verificado. Los envíos los hace Codex con autorización expresa del participante.
