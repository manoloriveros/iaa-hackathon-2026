

## Privada P16: paquete GAM completo tras enmienda de dormitorios, 26 de octubre de 2026

Codex, 2026-10-26T17:50:17.874662+00:00. Quedaron guardados los tres modelos fuente aditivos, con indicadores de ausencia y penalización1fija. Autos conserva cinco curvas y edificios cuatro; contenidos conserva tres curvas y el efecto lineal de bedrooms. Los parámetros totales son157,129y125respectivamente. No hay interacciones o búsqueda de nudos.

El intento original se detuvo en el preprocesamiento de contenidos porque los cuantiles fuente de bedroomsfueron[1,3,3,6]. Se había definido un guardia que exigía nudos distintos, pero el fixture original solo ejerció las curvas de edificios y no detectó el caso de contenidos. El fallo ocurrió antes de estimator.fit: dos modelos reales quedaron completos y el tercero no llegó a ajustarse. Código, plan, marcadores y fallo originales permanecen.

La enmienda se registró antes de continuar. Se retuvo el efecto lineal de dormitorios de la receta previa, sin probar otros nudos ni mirar un score destino de esta familia. El preflight de origen comprobó cuantiles estrictos en las otras tres variables de contenidos. Un nuevo fixture con dormitorios discretos repetidos pasó ajuste,JSONyorden. Autos y edificios se copiaron byte a byte con sus hashes y sus funciones/listas sin cambios. Solo se ajustó contenidos una vez, con llamada real a estimator.fitregistrada.

Contabilidad: cuatro invocaciones de pipeline en total, una fallida antes de ajustar, tres llamadas reales de ajuste GAM(2originales+1enmienda), dos fits sintéticos separados. No se repitieron los modelos ya terminados. El replay conjunto desde JSONfue exacto con fitbloqueado y recuperó las109.296relatividades históricas. La repetición histórica del replay se cuenta aparte; no consulta2025. El nombre de caché three_seedes una interfaz heredada, con un único modelo GAMpor ramo.

No se calcularon scores destino de esta familia, C0, calibraciones destino, inferencias2025, precios finales o envíos. La siguiente unidad registrará la comparación completa frente a A1Sy frente al GLMlineal con indicadores. Las conclusiones seguirán condicionadas por fuente2021–2024y ambos años destino adaptativos. No se acredita mejora privada o promoción. B00/F3c/P6y todos los fallos/alternativas se mantienen.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P16_GAM_bedrooms_lineal_20261026/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P16_GAM_bedrooms_lineal_20261026/amendment_replay_context.json; intento original Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P16_GAM_fuente_20261026.
