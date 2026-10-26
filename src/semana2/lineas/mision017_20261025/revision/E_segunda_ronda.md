# Segunda ronda de sondas: segmentación dentro de ramo × nuevo negocio

Ninguna segmentación compensa. La mejor, partir autos de nuevo negocio (motor_1) en dos por valor del vehículo, forma de pago o tasa predicha, rinde entre 0 y +0,0001 de D² privado por envío con la dispersión que dan los datos. Con información perfecta y una dispersión real del 10 % por segmento, el techo sería +0,0004. Para mañana recomiendo cero envíos en segmentos nuevos.

## Método

τ: en 15 segmentaciones × 6 celdas comparé el escalar Tweedie óptimo de cada segmento con el de su celda, en 2023 (T2b) y 2024 (mezcla), con NCB y previos de F2 estimados con el otro año. Resté el ruido con 400 réplicas bootstrap por cliente y siniestros topados en el percentil 99 (`E_tau.py`).

σ y ganancia: remuestreo por cliente de cada segmento a su tamaño 2025, público de 1/3, puntuaciones a 5 decimales, b_j por cuota de Σ√μ y último segmento deducido de la a de la celda; 300 réplicas por fuente y 20 sorteos de la desviación real. Nivel aplicado: celda × (c_j/c_celda)^Z, Z = τ²/(τ² + σ²) (`E_sim.py`).

## Resultados

La historia no distingue unas segmentaciones de otras: en cada celda, la varianza de τ² entre segmentaciones queda bajo su ruido de estimación (autos nuevos: 0,0014 frente a 0,031; edificios nuevos: 0,093 frente a 0,218). Lo defendible es una τ² común por celda: 0,0048 por segmento en autos nuevos (τ ≈ 7 %), 0,0011 en autos de renovación, 0,0034 en edificios de renovación y casi cero en contenidos. El 0,07 de edificios nuevos sale de 35 a 40 siniestros por año y cambia de signo entre años (forma de pago: −64 % y +77 % en 2024; +44 % y −52 % en 2023).

Además, entre el 82 y el 88 % del nuevo negocio de 2025 es de año completo, frente al 8-9 % de 2023-2024, y en 2024 esa banda tuvo pocos siniestros (54 en autos, 3 en edificios, 11 en contenidos). La tabla da σ emparejando bandas de exposición y sin emparejar (casi el doble).

Ganancia esperada en el privado, en diezmilésimas de D² (todas en `E_resumen.csv`):

| Segmentación (celda) | Envíos | σ por segmento | τ² histórica (± ee) | Con τ² común | Si τ = 10 % | Techo sin ruido, τ = 10 % |
|---|---|---|---|---|---|---|
| Valor del vehículo, 2 grupos (motor_1) | 1 | 0,045–0,088 | 0,000 ± 0,037 | 0,5–1,1 | 2,0–2,8 | 3,9 |
| Forma de pago (motor_1) | 1 | 0,052–0,107 | 0,053 ± 0,058 | 0,3–1,1 | 1,5–2,8 | 4,1 |
| Tasa predicha, 2 grupos (motor_1) | 1 | 0,052–0,098 | 0,037 ± 0,064 | 0,0–1,0 | 1,1–2,8 | 4,1 |
| Tasa predicha, quintiles (motor_1) | 4 | 0,090–0,150 | 0,033 ± 0,078 | 0,8–1,4 | 2,4–3,8 | 7,1 |
| Región (motor_1) | 5 | 0,096–0,181 | 0,000 ± 0,078 | 0,7–1,2 | 2,1–3,5 | 7,5 |
| Forma de pago (buildings_1) | 1 | 0,16 | 0,65 ± 0,28 | 6,2–6,4 con τ² = 0,07, indistinguible de 0 | 0,4 | 2,3 |

Por envío mandan las particiones binarias de motor_1; en total, región y quintiles. Si se cree la τ² histórica y la real es cero, la sonda pierde de 0,0001 a 0,0003 (forma de pago, tasa predicha). En renovación no hay nada: σ de 0,1 a 0,7 por segmento frente a τ de 3 a 6 %.

## Qué hacer mañana

Cero envíos en segmentaciones. La única estructura dentro de celda con evidencia fuera de tiempo es la tasa predicha en autos nuevos: el factor por quintil de 2023 gana +0,0041 en 2024, y +0,0044 al revés (`E_gratis.csv`). Eso es la forma, que ya tiene sondas preparadas (`sonda_F2_motor_1_a06.csv` y `_a08.csv`): dos envíos para un parámetro continuo en vez de cuatro por quintiles. Si sobran envíos, una partición binaria de motor_1 (valor del vehículo o forma de pago, Z entre 0,3 y 0,7) es una apuesta de esperanza casi nula.

Límites: τ medida con modelos de 2023-2024, no con F2; supone público aleatorio por filas.
