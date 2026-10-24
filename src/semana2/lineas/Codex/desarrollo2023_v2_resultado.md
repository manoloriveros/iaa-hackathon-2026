Codex. Cierro la tanda preinscrita en COD-S2-20261023-010 por la petición del participante. El [informe](../../Repositorio_IAA2026/docs/semana2/DESARROLLO_2023_TANDA2.md) y el [índice activo](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json) conservan la revisión, recetas y evidencia; v1 mantiene su snapshot y todas sus corridas.

| Receta | D² OOF 2023 | Predicho, millones CU | A/E |
| --- | ---: | ---: | ---: |
| W2-B00: Referencia | 0.06858 | 15.614 | 0.980 |
| W2-B01: GLM inicial | 0.06666 | 14.552 | 1.051 |
| W2-B02: LightGBM inicial, 300 árboles | -0.27353 | 7.559 | 2.024 |
| W2-B03: GLM, alpha=10 en edificios | 0.08672 | 14.320 | 1.068 |
| W2-B04: Prefijo LightGBM, 25 árboles | 0.07342 | 12.634 | 1.211 |
| W2-B05: Boosting simple, 80 árboles | 0.07986 | 14.113 | 1.084 |

Se completaron veinte ajustes nuevos solo en 2023, diez reutilizaciones GLM y quince exportaciones de prefijo, sin fallos. Son cinco folds y 50.094 filas OOF por receta. Los tres comparadores de v1, incluido B00, quedaron exactamente iguales. No hubo calibración posterior, búsqueda de otra ronda o nueva mezcla.

En edificios, alpha=10 mejora D² de -0.04147 a 0.01777, aún por debajo de la referencia del ramo (0.02085). Reduce la brecha de ajuste y variación de coeficientes, pero empeora A/E de 1.091 a 1.140. No se presenta la menor devianza como cierre de nivel o reservas. Autos/contenidos de B03 son idénticos a B01.

La brecha global de B02 (ajuste menos OOF), 0,80982, baja a 0.13260 con los primeros 25 árboles y a 0.06991 con árboles simples. Cumplen la dirección descriptiva previa, sin demostrar una causa única del error ni resolver los adversos de la receta original. DEV2023-B02-GENERALIZATION y S2-VAL-MOD-007 no se cierran aquí.

| Nueva receta frente a B00 | Diferencia D² | Intervalo exploratorio 95 % | Diferencia retirando 31 grupos favorables |
| --- | ---: | --- | ---: |
| W2-B03 | 0.01814 | [-0.00230, 0.03745] | -0.00791 |
| W2-B04 | 0.00483 | [-0.01202, 0.02017] | -0.00665 |
| W2-B05 | 0.01128 | [-0.00304, 0.02280] | -0.00358 |

Los tres intervalos cruzan cero y los tres diagnósticos de influencia invierten la ventaja. Se conserva la referencia y B01–B05, sin promoción, retiro o equivalencia declarada. Los intervalos de 2.000 sorteos comunes son exploratorios, sin corregir búsqueda adaptativa o las quince parejas. Las sensibilidades publicadas son a tasas fijas y no sustituyen escenarios reentrenados de confirmación.

Pasaron 21 controles focales y 1279 del comprobador separado; se solapan. Replay exacto con fit bloqueado, parámetros/encoders por fold, 25 árboles exactos y oráculo de suma de hojas, objetivos/exposiciones, métricas, intervalos e influencia contrastados. Es revisión propia de Codex. T0, folds, F0, vínculos y artefactos v1 no cambiaron.

2024 sigue cerrado por instrucción expresa del participante, aunque avance la reparación separada del selector. No hay ajuste, predicción o score de precios de 2024 o test, apertura del ledger o lista final congelada. Sin envíos, remoto o delegación. La referencia conserva su papel previo y las incertidumbres del último permanecen.
