# F3c-R frente al modelo actual

Autor Codex. Corte 2026-10-29T02:06:50.361596+00:00. No cumple todos los criterios registrados. Se conserva F3c y no se prepara otro envio con esta evidencia.

Entrenamiento2023 con flujo anidado completo; evaluacion temporal2024 adaptativa. Los dos controles son trainlevel_full del mismo nuevo tronco y public_full de F3c original. Las cifras son locales, no calificaciones de Kaggle ni garantia privada.

| Segmento | F3c-R D2 | Control mismo tronco | F3c original | Delta vs control | Delta vs F3c |
|---|---:|---:|---:|---:|---:|
| global | 0.126662 | 0.126718 | 0.126806 | -0.000056 | -0.000144 |
| new_business | 0.114614 | 0.108412 | 0.109150 | +0.006202 | +0.005464 |
| renewal | 0.123638 | 0.124591 | 0.124586 | -0.000953 | -0.000948 |
| motor | 0.081469 | 0.080818 | 0.084739 | +0.000651 | -0.003270 |
| buildings | 0.076375 | 0.077471 | 0.070695 | -0.001096 | +0.005680 |
| contents | 0.098854 | 0.099035 | 0.100372 | -0.000182 | -0.001518 |
| motor_0 | 0.078696 | 0.080293 | 0.082307 | -0.001597 | -0.003611 |
| motor_1 | 0.072879 | 0.057397 | 0.073993 | +0.015483 | -0.001114 |
| buildings_0 | 0.068751 | 0.069423 | 0.066784 | -0.000672 | +0.001967 |
| buildings_1 | 0.047020 | 0.051723 | 0.010172 | -0.004702 | +0.036848 |
| contents_0 | 0.092348 | 0.092446 | 0.091690 | -0.000098 | +0.000658 |
| contents_1 | 0.133769 | 0.134461 | 0.148427 | -0.000692 | -0.014658 |

| Criterio | vs control mismo tronco | vs F3c original |
|---|---|---|
| global_family20_lower_above_margin | no pasa | no pasa |
| NB_nonnegative_and_lower95_floor | pasa | no pasa |
| broad_and_sixcell_floor | no pasa | no pasa |
| four_savedfolds_positive | no pasa | no pasa |
| top_favorable_group_removal_nonnegative | no pasa | no pasa |
| fixed_price_stress_broad_floor | no pasa | no pasa |
| whole_pipeline_fivefold_stability | no pasa | no pasa |

F3c_R_vs_matched_trainlevel_full: intervalo global familiar20 [-0.001357761705378029, 0.001145735784003588], intervalo95 de negocio nuevo [0.001603990262759503, 0.010823208672239175]. Al retirar 37 grupos favorables, delta -0.001269. Peor delta de los50escenarios en segmentos amplios: -0.001297. Estabilidad de las cinco omisiones de entrenamiento: False.

F3c_R_vs_public_full: intervalo global familiar20 [-0.006319636670807844, 0.005783056506717213], intervalo95 de negocio nuevo [-0.010009180228184896, 0.022905437143605326]. Al retirar 37 grupos favorables, delta -0.003676. Peor delta de los50escenarios en segmentos amplios: -0.007776. Estabilidad de las cinco omisiones de entrenamiento: False.

Los10000sorteos por grupos mantienen precios fijos; no repiten todo el aprendizaje. Familia20 es condicional y no cubre toda la busqueda adaptativa. Cinco omisiones completas de folds comprueban otra sensibilidad del entrenamiento, sin escoger al mejor miembro. Los escenarios no tienen probabilidades asignadas ni certifican reservas.

Permanecen la dependencia de normalizaciones por lote, la historia publica de A_M1 y el soporte escaso de edificios nuevos largos. La composicion2025 usa solo pesos ya archivados; no son etiquetas privadas. B00, R1, F3c y F3c-R quedan conservados, junto a fallos y parciales.

Trazabilidad: registro/semana2_F3c_regularizado_evaluacion_plan.json y privado/semana2/F3c_regularizado_20261028/assessment/{results.json,bootstrap.npz,fixed_price_stresses.json,whole_pipeline_stability.json}. Codigo y fuentes identificados por SHA en el plan. No nuevos ajustes desde el evaluador, precios2025 ni envios.
