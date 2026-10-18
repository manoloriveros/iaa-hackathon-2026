# LightGBM y nivel último de cartera, S06, D73

17 de octubre de 2026. Preparación local por Codex a solicitud del participante. Los scores públicos confirmados siguen siendo S01 0,07118 y S02 0,07211. S06 está preparado y su simulación pasó; no se ha enviado.

La ola 1 se entrenó en Windows, con los bloques del contrato T04 y los Parquet verificados. Se conservan 54 ajustes principales, predicciones y snapshots; el detalle de selección está en [RESULTADOS_MODELOS_D72.md](RESULTADOS_MODELOS_D72.md). LightGBM F0 de tres semillas superó al GLM y M00 en los dos cortes. Las variantes con historia, clima, CatBoost y XGBoost quedan como investigación documentada; no se incorporan por prometer más sin comprobar su estabilidad.

La revisión de producción detectó que el balance sobre train no conserva necesariamente el nivel medio deseado en la cartera de 2025. S04 estima una tasa anual media de autos de 496,98 CU frente a 583,32 CU de S02. En edificios da 451,54 frente a 427,15; en contenidos 118,84 frente a 112,24. El año como predictor y el menor desarrollo del T0 reciente son una explicación plausible, pero no se ha aislado causalmente. También puede haber diferencias de composición. Mantener el nivel medio S02 por ramo es un supuesto explícito y puede sacrificar información de composición o tendencia.

Se prepara S06 con las mismas relatividades LightGBM de S04, normalizadas por ramo a la suma última de S02 en la misma cartera:

`predicción_i = predicción_S04_i / suma_S04_ramo * suma_S02_ramo`.

El factor de desarrollo ya aplicado a S04 se cancela algebraicamente en el cociente. No se vuelve a multiplicar IBNR. El cálculo no usa etiquetas de test. Esta es la aplicación operativa de la preferencia última D70 con un balance final de cartera. El runner conserva el balance de entrenamiento en los modelos guardados; el paso final reproducible está en `../Envios/preparar_s06_nivel_ultimo.py` y debe acompañar la preparación de candidatos posteriores bajo esta política.

| Diagnóstico local sobre T0 | V23 selección | V24, 2024 |
| --- | ---: | ---: |
| M00 por ramo | 0,083108 | 0,070937 |
| GLM F0 | 0,126128 | 0,110789 |
| LightGBM F0 tres semillas, crudo | 0,127678 | 0,125347 |
| LightGBM con balance de cartera | 0,132099 | 0,124037 |

En los cortes locales el nivel se fija a M00 estimado solo en train, multiplicado por las exposiciones de evaluación conocidas. Se evalúa con T0 observado y D² Tweedie p=1,5; el traslado al nivel último en producción no tiene etiquetas locales últimas con las que verificarse. V23 usa las exposiciones y predicciones sin etiqueta de ambas mitades para la normalización y puntúa solo selección. No se ajustan factores usando T0 de evaluación.

Los modelos e hiperparámetros quedaron congelados antes de V24. La regla final de balance S06 se añadió después de revisar V24 y el nivel de producción. Por ello, los scores S06 son una comprobación reutilizando esos cortes, no una evaluación final nueva ni una validación independiente. El descenso de 0,125347 a 0,124037 frente a LightGBM crudo se conserva: no se elige S06 por maximizar V24, sino por separar estructura de riesgo y el supuesto de nivel último S02. Su eficacia pública sigue pendiente.

S06 supera a M00 en V24 por 0.053100 de D² y reduce su desviación un 5.72 %. El bootstrap por cliente (373.831 clientes, 300 réplicas, denominador nulo fijo) da una banda aproximada [0.047642, 0.058214] para la diferencia. No incluye toda la dependencia por dirección o evento ni la incertidumbre de selección. Sin el 0,1 % de costes mayores conserva D² 0,088580 frente a M00 0,048025. La sensibilidad de reserva +/-25 % da 0.120980 / 0.124037 / 0.125599; las predicciones se mantienen fijas. No se elimina ni recorta ninguna etiqueta.

| Ramo | Total S02 y S06, CU | Factor sobre S04 |
| --- | ---: | ---: |
| Autos | 116.654.870,15 | 1,17372469 |
| Edificios | 64.176.493,47 | 0,94597169 |
| Contenidos | 16.850.595,90 | 0,94447791 |

La diferencia por redondeo es inferior a 0,001 CU en cada ramo. S06 conserva las 626.639 filas y orden del sample oficial, predicciones positivas y finitas. Total 197.681.959,52 CU. Archivo `../Envios/archivos/S06_lightgbm_3semillas_F0_nivel_S02.csv`, SHA-256 `3eef3d811dcc786bc9894efaff2bbbe172625247e21bce158656b42ace132ca1`. Los registros y archivos S01/S02 están intactos; S03/S04/S05 también se conservan.

El dry run comprueba columnas, filas, todos los IDs, ausencia de vacíos y números finitos. La consulta Kaggle de 19:26:56 UTC registra dos envíos hoy, ambos completos y sin pendientes. La plataforma informa diez como máximo; mantenemos el límite provisional del proyecto de cinco. S06 consumiría un cupo, quedarían dos del límite provisional hasta el reinicio a las 19:00 de Bogotá. Se subiría el CSV de predicciones a la competición; su puntuación aparecería en el leaderboard público. No hay nueva publicación de dataset ni entrenamiento remoto. Falta la confirmación de este archivo después de la simulación, exigida por `.agents/skills/kaggle/SKILL.md`: “After the user says yes, run it again with --yes”.

Evidencia en `Preparación/artifacts/verification/improvement_20261017_D71`: preparación, auditoría del CSV, resultados locales, sensibilidades, dry run, consulta de cupo y snapshots. Pasaron las 27 pruebas del flujo afectado; los últimos cambios al código son solo saltos de línea para Ruff y no requieren repetir entrenamiento. Ruff pasa para week1.py y predictor_guard.py. Sigue pendiente la revisión humana profesional. Se aplican IAA Documentación §§2–6, Gobernanza §2.8 y Consideraciones profesionales §§3.2 y 3.5–3.6, con las limitaciones de valoración única e IBNR D67 conservadas.

La comprobación paralela del archivo aportado `S03_lgbm_F0124.csv` tiene su propio hash y registro S03-PREFLIGHT-20261017T1922Z. No corresponde al S03 GLM de esta ola; su nombre no acredita bloques, entrenamiento o calibración y no se usa como origen de S06.


## Conciliación posterior de S03 y S06, 17 de octubre de 2026

Una actualización paralela autorizada incorporó S03_lgbm_F0124.csv, envío 57323464, COMPLETE y D² público 0,12321, por encima de S02 0,07211. La consulta propia Kaggle de 19:30:13 UTC confirma puesto 5 de 9 y tres envíos hoy. El resultado público corresponde a ese CSV por hash, con procedencia de entrenamiento aún pendiente; no se atribuye a S06 o al S03 GLM D72.

S06 sigue preparado sin envío ni score público, con D² local diagnóstico V24 0,124037. El dry run se renovó sin consumir cupo. Quedan dos cupos del límite provisional cinco; enviar S06 dejaría uno hasta las 19:00 Bogotá. La plataforma indica siete de diez disponibles. La recomendación S06 y la confirmación pendiente se mantienen. No se repite ningún envío.

Los hashes de memoria, estado, decisiones y registro del cierre D73 cambiaron por la incorporación paralela de ese recibo. Se verificaron intactos los otros 92 archivos incluidos en dicho manifiesto; se conserva el cierre original y se añade reconciliation_S03_S06.json con la transición y snapshots actuales. Los registros S01/S02 y el archivo S06 permanecen intactos.
