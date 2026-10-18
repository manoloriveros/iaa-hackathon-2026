# Resultado D76: aprendizaje de modelos y combinaciones

S08 mejora el mejor público previo: público0.12532, diferencia+0.00097 frente a0.12435. Kaggle confirmó COMPLETE con ID57331887. El mejor público vigente es0.12532 (envío57331887).

| Comprobación | D² |
| --- | ---: |
| S07,2024 completo | 0.131729414 |
| S08,2024 completo | 0.132474706 |
| S08,público Kaggle | 0.12532 |
| Mejor público antes de S08 | 0.12435 |

Se añadió CatBoost con categorías nativas e historia ampliada F0124. Profundidad 4, 700 árboles en V23, 805 en V24 y 910 en producción; tasa 0,04, L2=20, complejidad máxima CTR=1, semilla 2026, cuatro hilos CPU. Autos conserva desarrollo estimado solo en train y tope de ajuste 15.000 CU con exceso devuelto; scoring sobre todos los costes. Hogar usa exposición nominal y nivel último al combinar. Se guardan parámetros, escala de etiqueta, pesos, modelos y predicciones por fila.

Un stacking restringido aprende cuánto peso dar a S07 y CatBoost usando predicciones de 2023 de bases entrenadas hasta 2022. Penalización 0,01 respecto de S07 y suelo 25 % para S07. CatBoost pesa 37,67 % en autos, 8,94 % en edificios y 2,03 % en contenidos. La calibración de nivel usa la mitad de la diferencia entre 1 y el factor Tweedie óptimo aprendido en OOF 2023. Se normaliza cada componente a la referencia última S02, se combina y se aplica ese factor estadístico una vez. Los totales ya no se fuerzan a ser exactamente S02. Esta es una hipótesis de calibración declarada; el desarrollo de siniestros se aplica una vez.

El score del combinador sobre 2023 es de ajuste y no se presenta como validación. La receta quedó congelada antes de los ajustes V24. El corte 2024 ya había sido inspeccionado en rondas anteriores y continúa siendo desarrollo, sin validación independiente. La ganancia completa es pequeña y depende de pérdidas grandes: al excluir el 0,1 % mayor, S08 da 0.097233 frente a 0.098520 de S07. El bootstrap por cliente no incluye incertidumbre de selección ni toda la dependencia por evento o dirección. La combinación cambia tanto el reparto del riesgo como el nivel; el resultado público no identifica el efecto aislado de cada cambio.

El primer stacking, con GLM/GBT/FS y solo media muestra de 2023 para ajustar, se descartó: selección 0,135218 y V24 0,124503, peores que S07. También se conservaron los contrastes CatBoost de profundidad 6 y LightGBM con tres declaraciones anteriores a la incorporación. Su disponibilidad por columna se comprobó con diccionario, año de incorporación y coincidencia del origen; no se extiende a todo F3. El candidato final da peso prácticamente cero a ese LightGBM y no usa F3. Se conservan los 14 modelos de boosting nuevos y 9 optimizaciones de pesos; tres pruebas funcionales nuevas pasan.

Reproducción: train_cat.py por ramo, corte y profundidad; audit_prejoin.py y train_prejoin.py para el contraste de incorporación; learn_stack.py para el contraste inicial rechazado; assemble_learned.py freeze/V24/PROD para la receta final; verify_gain.py; prepare_submission.py. Los comandos de auditoría que cambian autorizaciones, registro y cierre son de una sola vez, no se deben repetir sobre los documentos vigentes. plan.json, plan_after_screen.json, learned_recipe.json y los manifiestos conservan elecciones y hashes. Se usó Windows local con Python 3.12.14, CatBoost 1.2.8, LightGBM 4.6.0 y scikit-learn 1.7.2.

Archivo:Hackaton/Semana 1/Envios/archivos/S08_D76_CatBoost_stacking_calibrado_ultimo.csv; SHA-256f6c11e366fa3663fed7187c9c45db30f5542155e864bdfef25857277b33363e6; filas626,639. El [recibo](../../../Preparación/artifacts/verification/improvement_D76/submission_receipt.json), la [comprobación de ganancia](../../../Preparación/artifacts/verification/improvement_D76/gain_verification.json) y la [auditoría de producción](../../../Preparación/artifacts/verification/improvement_D76/S08_audit.json) conservan el resultado exacto. Competición:[iaa-ai-assisted-hackathon-2026-part-1](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1).

Fuentes técnicas: [Tweedie en CatBoost](https://catboost.ai/docs/en/concepts/loss-functions-regression) y [stacking con predicciones cruzadas](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.StackingRegressor.html). La implementación usa un optimizador no negativo propio para el combinador. Las matrices base de ajuste son OOF temporales y conservan la separación del entrenamiento de sus modelos base.

IAA: Documentación §§2–6, Gobernanza §2.8 y Consideraciones profesionales §§3.5–3.6. Codex propuso, implementó, entrenó y comprobó; el participante pidió continuar y autorizó el envío condicional. La responsabilidad y revisión humana permanecen abiertas; no hay certificación profesional ni validación independiente. No se publicaron datos o código ni se inició cómputo remoto.
