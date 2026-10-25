# Preinscripción E27: nivel 2025 por ramo y segmento con evidencia actuarial, sin tablero

Escrita el 24 de octubre de 2026, antes de calcular ninguno de los cocientes de abajo. Pedido del participante: «aplica el punto 3 y preparemos una entrega». El punto 3 era estudiar el nivel de 2025, sobre todo el del nuevo negocio de autos, solo con evidencia actuarial y con una regla fijada antes de calcular. El participante prefirió no usar sondas del tablero (CLA-S2-20261024-020).

## Qué se ajusta

La base es la mezcla 50/50 ya enviada, `mezcla50_designada_mlind_2025.csv` (SHA-256 12831ef4a05c1773824abe5fa139d9503dd2989b4874e7d93cfc000406cfdb4a, público 0,15390). La entrega nueva conserva sus relatividades fila a fila y solo multiplica cada uno de seis segmentos (tres ramos por nuevo negocio y renovación) por un factor f_s.

## La evidencia: siniestralidad esperada sobre la prima escrita

Este es el método de siniestralidad esperada (*expected loss ratio*): el coste esperado de un bloque es la siniestralidad histórica de la aseguradora multiplicada por la prima de ese bloque. La prima escrita es la tarifa que la propia aseguradora puso a cada póliza de 2025, así que es independiente del tablero y de nuestros modelos. Ya está comprobado sin calcular cocientes que la prima escrita es anual: la mediana es la misma en tramos parciales y en años completos, en los tres ramos y en los tres años.

1. Para cada fila emergente de 2023-2024 se calculan la prima devengada, P = prima escrita × exposición, y el coste último estimado, U = y / c_fila (la completitud de reporte de la línea).
2. La siniestralidad del segmento es LR_s = ΣU / ΣP, con 2023 y 2024 juntos. Se le aplica credibilidad hacia la del ramo, LR*_s = Z_n·LR_s + (1 − Z_n)·LR_ramo, con Z_n = n / (n + 200), donde n es el número de siniestros del segmento. Es la misma K que la calibración C2.
3. El coste que implica la tarifa en 2025 es E_s = LR*_s × P25_s, con P25 la prima devengada de 2025.
4. El cociente frente a la base es g_s = E_s / B_s, donde B_s es el total de la mezcla enviada en el segmento.

## La combinación con credibilidad

5. La incertidumbre de la evidencia es σ_s² = var_boot + var_año:
   - var_boot es la varianza de log LR*_s en 1.000 remuestreos por cliente (pesos de Poisson, semilla 20261024);
   - var_año es ½·(log LR_s,2024 − log LR_s,2023)², la discrepancia entre años, que captura cambios de tarifa o de cartera.
6. La credibilidad es Z_s = τ² / (τ² + σ_s²), con τ = 0,07 fijada ahora: es la media cuadrática de los desvíos de nivel del modelo en la parte 1 (nivel implícito del público frente al de S30: −2,3 %, +7,5 % y +8,4 %, sección 19 de la memoria).
7. El factor es f_s = exp(Z_s · log g_s), recortado a [0,85; 1,15].
8. Cada fila del segmento s se multiplica por f_s. Se escribe el CSV con el contrato habitual: 209.063 filas, orden de la plantilla, `row_id,prediction`, seis decimales, LF y valores positivos.

## Diagnósticos que se informan y no cambian la regla

- La siniestralidad por año y segmento (estabilidad 2023 frente a 2024).
- Un backtest de un año: la misma regla con 2023 solo, aplicada a T2b en 2024, y el D² de 2024 con y sin factor. 2024 ya está abierto, así que es exploratorio.
- Si la tarifa 2025 del bloque del bróker ordena el riesgo como la de 2023-2024. Se mide con la correlación de rangos entre la prima por exposición y la predicción base por exposición, en nuevo negocio de 2025 frente a nuevo negocio de 2023-2024.
- La sensibilidad a τ (0,05 y 0,10) y a K (100 y 400).
- El efecto esperado en D²: la divergencia de Bregman entre la base y la entrega nueva, en dos escenarios (que la verdad esté en el nivel de la base o en el nivel de la tarifa).

## Qué se entrega y quién decide

Se prepara el archivo y una nota para Codex. No se envía. Si se envía, lo hace Codex con autorización expresa del participante, y la marca final en Kaggle la decide el participante. No hay regla que impida preparar la entrega: el participante pidió prepararla. La recomendación de enviarla o no se dará con los diagnósticos a la vista.
