# Validación de F2 (revisor D)

Código propio en `revision/D_*.py` y `D_*.json`; k = Σ(y/√μ)/Σ√μ.

## 1. Reconstrucción

Mi F2 coincide: diferencia relativa máxima 3,3·10⁻⁶ (redondeo a seis decimales). 209.063 filas, mismo orden que F, positivas y finitas, SHA 119627d9…. En cada celda F2/F es exactamente la razón de nivel (motor_0 0,9719; motor_1 0,9757; hogar 0,996–1,0005), así que factores y forma conservan los totales. Estimar previos tras NCB (`construir_F2`) o a la vez (`eval_v2`) cambia ≤ 0,15 % por fila.

## 2. Fuera de tiempo

Composición 2025 por celda × exposición, nivel óptimo ponderado por celda, nulo con media ponderada:

| Ganancia D² | 23→24 T2b | 23→24 A1 | 23→24 mezcla | 24→23 |
|---|---|---|---|---|
| NCB | +0,0007 | +0,0007 | +0,0007 | +0,0054 |
| Previos | +0,0025 | +0,0023 | +0,0024 | +0,0031 |
| Ambos | +0,0032 | +0,0030 | +0,0031 | +0,0085 |
| F2 completo | +0,0033 | +0,0030 | +0,0031 | +0,0084 |

Con nivel sin ponderar (`eval_v2`) salen las cifras declaradas. Por celda (23→24 T2b): motor_1 +0,0026, contents_1 +0,0007, buildings_0 −0,0001, resto ≈ 0. En 24→23, motor_1 +0,0079.

Depende de pocas filas. En motor_1, la banda de exposición ≥ 0,9 (54 siniestros en 2024 con peso 47; 48 en 2023 con peso 64) aporta +0,0023 de +0,0033 y +0,0077 de +0,0084; en 2023 los cinco mayores de esa banda (el primero de 118.374) explican el 60 %. Quitando los 20 mayores por celda: evaluación 2024 +0,0023; estimación 2023 +0,0008 (previos cae a +0,0002); evaluación 2023 −0,0002. Bootstrap por cliente en 2024, percentiles 5–95: T2b [+0,0001; +0,0066], A1 [−0,0003; +0,0064].

## 3. Fallos buscados

- Fuga: ningún dato de 2025 entra en los factores.
- `prior_claims_5y` no recoge siniestros propios: P(previos ≥ 1) es 0,224 sin siniestros en 2023-24, 0,256 con siniestro solo en 2023 y 0,263 solo en 2024; el 69 % de quienes tuvieron 2+ siniestros tiene previos = 0. Razón de frecuencia previos ≥ 1/0: 1,21 y 1,25 en renovación (2023, 2024), 1,26 y 1,28 en nuevo negocio.
- Mecanismo de previos: en motor_1 la frecuencia sube con previos como predice T2b (1,15; 1,64–1,85) y la prima pura no (0,47 y 0,66 en 2023; 0,86 y 1,07 en 2024). El factor corrige severidad: 18 y 17 de los 20 mayores siniestros caen en previos = 0, donde se esperaban 14,6. Se repite en ambos años, pero son unos 35 siniestros. NCB tiene respaldo externo (relatividad 1,73 emergente frente a 2,56 desarrollada, memoria del proyecto).
- Credibilidad bien aplicada; juntar dos años equivale a k ≈ 150 en uno. Con k = 100 la ganancia sube (+0,0058; +0,0172) y con k = 1000 baja (+0,0013; +0,0031), pero el peor caso recortado empeora a −0,0011.
- Razón de nivel correcta, medida dentro de muestra; fuera de tiempo motor_1 pide 0,985–0,988. Coste ≤ 0,00001.

## 4. Recomendación

Enviar F2 tal cual (k = 300): todas las pruebas dan el mismo signo. No bajaría k, porque la ganancia extra sale de los mismos siniestros grandes. Si la banda larga rinde como las cortas, la prueba da +0,0032 (23→24) y +0,0021 (24→23): esperaría +0,002 a +0,003, con una cola pequeña de pérdida; el +0,0093 de 24→23 no es representativo.
