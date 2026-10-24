Codex. Cierro la primera tanda preinscrita en COD-S2-20261023-008, por autorización directa del participante. Se completaron los cinco folds persistidos de 2023 para tres ramos y tres recetas: quince constantes y treinta estimadores, sin fallos de ajuste. Hay una predicción OOF por cada una de las 50.094 filas y cada receta. El [informe](../../Repositorio_IAA2026/docs/semana2/DESARROLLO_2023.md) y el [índice activo](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_actual.json) identifican todos los artefactos.

| Receta | D² OOF 2023 | Predicho, millones CU | A/E |
| --- | ---: | ---: | ---: |
| Referencia constante (W2-B00) | 0.06858 | 15.614 | 0.980 |
| GLM regularizado (W2-B01) | 0.06666 | 14.552 | 1.051 |
| LightGBM limitado (W2-B02) | -0.27353 | 7.559 | 2.024 |

El observado es 15,297 millones CU. Se evaluó T0 con el mismo vínculo C0, sin pesos extra de evaluación, calibración posterior o mezcla. No son resultados de último real ni de Kaggle.

GLM−referencia: -0.00192, con intervalo exploratorio del 95 % [-0.03811, 0.02869], 2.000 remuestreos de componentes pareados. No acredita mejora global ni equivalencia. El GLM mejora el punto en autos/contenidos y empeora en edificios y nuevo negocio. Al retirar los 31 grupos más favorables a la diferencia, esta queda en -0.03415. La referencia se mantiene; las otras recetas se conservan.

LightGBM queda por debajo en los cinco folds y los tres ramos. D² dentro de ajuste 0.53629 frente a -0.27353 OOF y A/E OOF 2.024. Es compatible con sobreajuste y deterioro de nivel, sin aislar causalmente un parámetro. No se reescaló, eligió otra ronda ni retocó la receta. DEV2023-B02-GENERALIZATION impide avanzar esta receta como aspirante validado sin nueva evidencia de desarrollo. No se retira la familia ni se borran resultados adversos.

Los quince casos conocidos y 937 controles del comprobador separado pasaron; los recuentos se solapan. Se reprodujeron las predicciones desde los modelos guardados con fit bloqueado y se cotejaron pérdida, constantes, transformaciones dentro del fold, parámetros, gradientes GLM, intervalos e influencia. Es revisión propia de Codex. Las sensibilidades de reserva/cola usaron tasas base fijas: ambas alternativas siguen por debajo, pero esto no sustituye reentrenamientos o pruebas completas de confirmación.

Solo se materializó 2023 para el consumidor de precios. No hay ajuste, predicción o score de 2024 o test, envíos, remoto, promoción o lista final congelada. El ledger sigue sin abrir. S2-AUD-METRIC-BINDING continúa abierto; el trabajo de cierre coordinado en COD-S2-IA-20261023-CIERRE-ENCARGO conserva su alcance y responsable. Mantengo 2024 cerrado hasta que se corrija y contraste el selector y se congelen recetas, lista y evidencias requeridas. No atribuyo cierre a ese trabajo por este resultado.
