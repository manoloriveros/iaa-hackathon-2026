# Contraste exploratorio B20: mejora media frágil, rechazo por influencia

Codex, cierre UTC 2026-10-24T17:39:48.353301+00:00. El contraste se entrenó y se evaluó una sola vez con la [enmienda autorizada](ENMIENDA_CONTRASTE_B20_2023_V2.md). Cumple 17 de 19 condiciones predictivas y falla los dos controles de influencia. Se conserva B20 original y todas las alternativas. No se promueve un modelo ni se envía a Kaggle.

## Resultado sobre 2023

| Brazo | D² global | A/E global | Coste observado predicho, millones CU |
| --- | ---: | ---: | ---: |
| B20 original | 0.089382 | 1.0113 | 15.126 |
| L, solo nivel | 0.089985 | 0.9487 | 16.124 |
| S, compresión y nivel | 0.093747 | 1.0002 | 15.294 |

Son las mismas 50.094 filas y 30.869 componentes, con T0 observado y C0 condicionado; no es validación del coste último de 2025. La ganancia global de S es +0.003762 frente a L y +0.004365 frente al B20 original. La hipótesis de compresión resulta compatible con estos puntos, pero la influencia impide aceptar la mejora como estable.

| Fold exterior | Pendiente S | ΔD² S−L | ΔD² S−B20 |
| --- | ---: | ---: | ---: |
| 0 | 0.3963 | +0.000258 | -0.000248 |
| 1 | 0.4250 | +0.006558 | -0.000234 |
| 2 | 0.5441 | +0.006323 | +0.005684 |
| 3 | 0.4483 | +0.000889 | +0.003091 |
| 4 | 0.4601 | +0.005437 | +0.013052 |

Las cinco pendientes son interiores, entre 0.396 y 0.544. S mejora frente a L en los cinco folds, pero pierde ligeramente frente al B20 original en dos. Ese rango no es un intervalo de confianza: los conjuntos de ajuste se solapan y 2023 ya se usó repetidamente para investigar.

## Por qué se rechaza

La regla previa elimina únicamente de la evaluación los 31 componentes más favorables de cada comparación. No se borran del ajuste, no se corrigen sus costes y no se reentrena.

| Comparación | ΔD² completo | ΔD² sin los 31 componentes más favorables | Regla previa |
| --- | ---: | ---: | --- |
| S−L | +0.003762 | -0.006440 | Debía seguir≥0; falla |
| S−B20 | +0.004365 | -0.014059 | Debía seguir≥0; falla |

Pasaron los demás criterios: magnitud global, acuerdo por fold, pendientes no degeneradas, segmentos, invariancia de autos/contenidos y nivel. La brecha logarítmica entre las bandas extremas originales baja de 1.0153 con L a 0.0304 con S. Los A/E extremos pasan de 1,68 / 0,61 a 1,06 / 1,03. El total nominal condicionado de edificios cambia +2.96%, dentro del máximo previo de 5 %. Esas mejoras no compensan los dos incumplimientos de influencia.

El soporte original sigue fallido. Se pudo medir además el soporte de las diez colas interiores de calibración, antes desconocido: solo una cumple las reglas originales. No se agrupan bandas o relajan umbrales para convertir ese resultado en aprobado. El entrenamiento exploratorio estaba autorizado precisamente conservando esta carencia, no dando por resuelto su soporte.

## Integridad y recursos

Las seis pruebas sintéticas previas comprobaron C0, imputación, escala, categorías, GLM e intercepto/pendiente en conjunto: alterar las etiquetas del fold exterior no cambió ningún objeto aprendido. Hubo 32 invocaciones sintéticas del flujo, incluidas las rechazadas; no se suman a los ajustes del concurso.

La comprobación posterior pasa 219 controles: fuentes y criterios congelados, pertenencias exactas de los diez ámbitos internos, pesos de notificaciones, ausencia de cruces por componente/cliente/dirección, replay exacto de tasas/C0, identidades del intercepto y condiciones de primer orden. La métrica se coteja con scikit-learn. Se bloquearon las rutinas de ajuste durante esta comprobación: cero reentrenamientos.

Se hicieron diez GLM interiores, sesenta ajustes de reporte, sesenta constantes de frecuencia, diez mezclas y cinco calibraciones de pendiente con diez interceptos finales. Cinco B20 exteriores se reutilizaron y sus predicciones originales se reprodujeron exactamente. Los contadores propios de precios pasan de 195 a 205 y de constantes de 285 a 295; pendientes y auxiliares se contabilizan aparte. Los 519 siniestros de edificios y los 12.580 periodos usados por la etapa interna pertenecen a 2023. No se materializaron etiquetas de pólizas de 2024 o test ni se ejecutaron sus productores.

El fallo de escritura Parquet se produjo antes del primer ajuste real, se conservó y se reparó sin cambiar criterios. Se guardan las diez parejas C0/GLM, predicciones internas, cinco calibradores, anclas exteriores, tres OOF completos y resultados adversos en privado. No hay un CSV de 2025 nuevo, modelo promovido, cambio de política común o envío a Kaggle. Este resultado no dispara otra pendiente, alpha, banda, semilla o receta.

[Contrato previo](../../../registro/semana2_b20_enmienda_exploratoria_v2_20261024.json), [índice del resultado](../../../registro/semana2_b20_contraste_exploratorio_actual.json) y evidencia completa en `privado/semana2/desarrollo2023/b20_contraste_exploratorio_20261024_v2`. El informe conserva precisión resumida; `evaluation.json` contiene valores completos y las 19 condiciones, y `verification.json` sus recibos técnicos. Revisión propia de Codex, sin revisión profesional humana o confirmación independiente. Propósito y límites, procedencia y cambios se documentan conforme a las prácticas IAA adoptadas por el proyecto.
