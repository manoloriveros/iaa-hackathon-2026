# Comparación de hogar preparada, pendiente por cuota

Codex, 25 de octubre de 2026, 16:41 UTC. Los dos archivos están preparados y comprobados, pero no se han enviado. La consulta autenticada de Kaggle a las 16:32:31 UTC informó diez envíos usados hoy y cero cupos disponibles. El límite total no está agotado. Es una restricción de cuota; no hubo rechazo del CSV ni un nuevo fallo de scoring. Esa respuesta no acredita una hora exacta de reapertura.

Se prepararon dos salidas ya fijadas del mismo GLM regional de hogar, con un solo ajuste final sobre 28.414 periodos de 2023. Una usa la salida completa de hogar y otra mantiene la mezcla anterior de raíces, 50/50 con B20. Las 90.521 predicciones de autos se copiaron exactamente de R36, incluido su texto decimal. No se ajustaron fuentes ni C0 nuevos, y no se leyeron costes de 2025 o cohortes y métricas de 2024.

| Salida de investigación | Filas | Cambio de nivel en edificios frente a R36 | Cambio en contenido |
| --- | ---: | ---: | ---: |
| Hogar completo, autos R36 | 209.063 | +1,94% | +7,94% |
| Hogar mezclado 50/50 con B20, autos R36 | 209.063 | -0,43% | +0,25% |

El aumento de contenido de la primera salida supera el umbral de atribución del 5%. Unos 7,12 puntos porcentuales proceden del cambio, ya definido, de peso 50% a 100% del profesor; los restantes 0,83 puntos corresponden a la corrección regional conjunta. Esta identidad numérica no valida la superioridad, la maduración o el nivel futuro. Los fallos de incertidumbre e influencia de 2023 siguen vigentes. Los archivos sirven para una comparación exploratoria y no constituyen una promoción formal, una selección final o un modelo declarado robusto. Incluso un público de al menos 0,17 acreditaría solo ese subobjetivo mientras falte robustez local.

Ambos CSV conservan todos los identificadores y el orden de la plantilla oficial. Sus predicciones son positivas y finitas en todas las filas. Se cotejó una fórmula densa independiente en las 118.542 cotizaciones de hogar. Otro proceso, con todos los ajustes y optimizadores bloqueados, reprodujo ambos archivos bit a bit. Cada archivo pasó las cinco comprobaciones del dry-run del skill.

El primer dry-run falló al limpiar temporales del sandbox y se conserva. La segunda versión ubicó los temporales dentro del espacio de trabajo y completó las comprobaciones, sin cambiar los CSV o la cuenta. La reanudación exige recibos válidos vinculados al SHA de cada archivo y no acepta aquel intento fallido como evidencia.

Se enviará, como máximo, el prefijo disponible de dos salidas, en el orden ya fijado: hogar completo y después mezcla. Primero se volverá a consultar la cuota. Se completará la tanda elegida antes de leer cualquiera de sus nuevos scores y solo se consultarán recibos propios. No se reajustarán pesos o nivel con esos resultados. Sin cupos no se intentará un canal alterno ni un cambio de cuenta. B00 y todas las alternativas permanecen; 2024 sigue cerrado.

La receta vigente es registro/semana2_comparacion_publica_hogar_plan_v2.json. Los CSV, el modelo, fuentes por SHA, atribución, replay, dry-runs y recibo de cuota están en privado/semana2/robustez2023/comparacion_publica_hogar_20261025_v1. Su queue_ready.json fija los archivos pendientes. El ejecutor vigente es herramientas/enviar_comparacion_hogar2023_v2.py; su preflight no consulta scores y conserva cada lectura de cuota. A este corte no existe un recibo de envío o un score nuevo de esta comparación.

Consulta posterior: a las 17:02:22 UTC Kaggle volvió a informar diez envíos usados hoy y cero disponibles. Los archivos permanecen iguales y no se intentó POST. La cola posterior queue_followup4.json conserva el nuevo recibo y una espera de sesenta minutos, sin afirmar una hora de reapertura. El ejecutor vigente se probó con seis escenarios sintéticos aislados; esos resultados no equivalen a aceptación o scoring real.

Corte posterior de las18:02:24UTC:la lectura única terminó con diez envíos usados hoy y cero cupos;no se intentóPOST ni hay score nuevo. El proceso de espera está cerrado. Anexo de ejecución vigente:registro/semana2_comparacion_publica_hogar_ejecucion_v3.json,con nueve escenarios sintéticos de conciliación probados;CSV,prioridad y fallos locales permanecen iguales. Objetivo bloqueado por cuota,pendiente y sin hora de reapertura certificada.
