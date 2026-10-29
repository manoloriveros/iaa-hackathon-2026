# Modelo propio G4 y CSV para Kaggle

El CSV propio está preparado: 209.063 predicciones de 2025, con dos columnas (`row_id`, `prediction`), IDs únicos y orden idéntico a la plantilla emergente. Se ajustaron tres GLM estándar con las 50.094 filas de 2023. El replay desde disco reprodujo exactamente todas las predicciones sin ajustar nada. 2024 permanece cerrado para políticas, precios, validación, scores y ledger; B00 y las alternativas se conservan.

Codex, 2026-10-25T01:29:03.607646+00:00. Preinscripción COD-S2-20261024-069; reparación focal G4-FINAL-GUARD1; resultado COD-S2-20261024-070. La instrucción del participante de continuar automáticamente hasta finalizar permitió completar capital, C0 y modelos de 2023 y la inferencia de 2025. El resultado es un archivo local listo para cargar; no se ha enviado a Kaggle ni seleccionado una entrega final oficial.

| Ramo | Filas de ajuste2023 | Siniestros2023 | Predicciones2025 |
| --- | ---: | ---: | ---: |
| motor | 21680 | 3557 | 90521 |
| buildings | 12580 | 519 | 52295 |
| contents | 15834 | 491 | 66247 |

## Receta y ámbito

Se mantuvo la receta estándar de efectos principales ya especificada en B20: Tweedie1,5 con enlace log y alpha1, siete variables por ramo, mediana y escala numéricas y codificación categórica aprendidas solo del ajuste. No se añadió calibración de nivel/pendiente, tendencia, clima, credibilidad o mezcla con otras predicciones. No hubo otra búsqueda de hiperparámetros o entrenamiento repetido de los cinco folds.

El ámbito final comprende toda la cohorte elegible de 2023 y tiene identidad propia. Sus parámetros de capital, curvas C0, preprocesadores y GLM se aprendieron en ese ámbito, sin renombrar un objeto exterior como final. Para edificios y contenidos se conservó CAPS2-01 con sus umbrales anteriores de diez millones y un millón. La prima se emplea solo en la regla auditada de calidad de capital, fuera de los predictores. En el ajuste se corrigieron 26 capitales de edificios y 30 de contenidos; en2025 se aplicó la regla congelada a 104 y 135respectivamente. No se aprendieron referencias de las cotizaciones.

C0 conserva rho1 y masa de cola no observada0. Se ajustaron quince curvas de reporte (5 autos,6 edificios,4 contenidos), quince frecuencias y sus marcas medias usando ocurrencias de2023 y seguimiento hasta el corte histórico2024-12-31. Eso no abre la cohorte de pólizas2024. La respuesta del GLM es T0/C0 y el peso sqrt(C0). Para cotizar2025 se multiplica la tasa anual por la exposición nominal reconciliada; no se aplica a una cotización futura la completitud observada de una póliza2023.

Las tres tablas oficiales de test2025, el maestro estático de direcciones y la plantilla de IDs solo se decodificaron después de terminar los tres modelos. Las fuentes de ajuste son copias ya estrictas2023, con SHA histórico, columnas explícitas y prueba de fechas/año en el footer. No se ejecutó un productor histórico que materialice todos los años. Las cotizaciones conservaron su exposición tras comprobar la regla de días inclusivos/365 redondeada a cuatro decimales.

## Comprobaciones y reparación

La nueva prueba focal sintética recorrió los tres ramos, con tres GLM y quince curvas de reporte aparte de los cómputos reales. Pasaron ocho controles de flujo y ámbito. En datos reales, T0 concilió con los siniestros heredados en centavos; los tres GLM convergieron y sus gradientes penalizados quedaron por debajo del criterio previo1e-4. La predicción manual exp(Xbeta+intercepto) y la identidad de pesos Tweedie cumplieron rtol1e-12/atol1e-9. C0 coincidió con integración diaria directa en 120 casos, con error máximo 2.73e-14, bajo el límite1e-12.

La revisión posterior detectó una falta de guarda en la función de capital: admitía por sí sola un artefacto válido del otro ramo. La ejecución real había pasado el artefacto correcto a cada ramo. Se archivó la sonda adversa y se preinscribió la reparación antes de cambiar el código. Solo se añadieron rechazos de ramo/umbral y año admisible. No se alteraron parámetros, operaciones numéricas, modelos o CSV y no se reentrenó. Pasaron ocho controles focales, incluidos artefactos reseñalados de ámbito incorrecto; las características recalculadas desde los raw2025 y las 209.063 predicciones siguieron idénticas.

Se conservan el código anterior de ajuste y el código posterior con guardas. Los recibos originales certifican su versión original; la versión de consumo posterior tiene su propio replay. Hubo replay dentro del proceso y en otro proceso desde los tres modelos guardados, con todos los fit y los productores de capital/C0 bloqueados. Se verificaron columnas, orden, cobertura exacta de209.063IDs, valores positivos/finitos y roundtripCSVsin pérdida. No se rellenaron filas, recortaron precios o mezclaron mercados.

## Evidencia de rendimiento y límites

La receta B20 tenía D² OOF2023 de 0,08938 frente a0,06858de B00 en la corrida histórica. Se reutiliza esa evidencia; no se ejecutó otra validación o bootstrap sobre las mismas etiquetas. Es exploratoria tras búsqueda adaptativa y conserva sus advertencias por segmentos y concentración. El modelo ajustado con todo2023 no tiene un nuevo score de validación. Ningún diagnóstico de ajuste se presenta como prueba de generalización.

La estimación de último sigue condicionada al tratamiento heredado de reservas y a cola no observada nula. No se ha identificado independientemente la masa fuera de soporte ni se ha efectuado una revisión actuarial profesional. Las carencias del ensayo de calibración de B20 siguen registradas. El CSV utiliza el GLM estándar sin esa calibración. No hay promoción formal, retirada de B00 o selección final manual. La exposición previa ajena de información2024 permanece declarada; no se consultó o usó en este trabajo.

## Archivos y reproducción

CSV: `Hackaton/Repositorio_IAA2026/privado/semana2/modelo_final_g4_2023/final_20261024_v1/attempt1/submission_g4_glm_2023_2025.csv`. SHA256: `e5e30c5921c0494b7c0bebe76fbf33725f45ab392f7bed5ab7f6927a89f394ab`. Los modelos, capitales, C0, vistas de cotización, plan, entorno y recibos están en `Hackaton/Repositorio_IAA2026/privado/semana2/modelo_final_g4_2023/final_20261024_v1`. Índice: `Hackaton/Repositorio_IAA2026/registro/semana2_g4_entrega_final_actual.json`. El paquete privado de revisión incluye los objetos y las entradas derivadas necesarias para replay, código actual y fuentes archivadas anteriores. No incluye el foro, memoria compartida, credenciales o predicciones de otros modelos. Es local; no se ha publicado o enviado.

El comando de replay usa los modelos congelados y no entrena:

```powershell
& 'C:/dev/Hakaton/Preparación/.venv/Scripts/python.exe' 'C:/dev/Hakaton/Hackaton/Repositorio_IAA2026/herramientas/reproducir_csv_final_g4_sin_ajuste.py' --manifest 'C:/dev/Hakaton/Hackaton/Repositorio_IAA2026/privado/semana2/modelo_final_g4_2023/final_20261024_v1/replay_manifest_guard1.json' --receipt 'C:/dev/Hakaton/Hackaton/Repositorio_IAA2026/privado/semana2/modelo_final_g4_2023/final_20261024_v1/replay_revision_nueva.json'
```

El recibo solicitado debe ser nuevo. El entrenamiento original y sus fuentes están archivados para revisión; no reejecutar su consumidor con las mismas fuentes para confirmar un cambio editorial. El paquete no se presenta como reproducción profesional independiente o ejecución verificada en Kaggle/Linux. La comprobación en proceso separado sigue siendo verificación propia de Codex.

Decisiones G4FNL-01 a G4FNL-07. Tres nuevos GLM reales y quince ajustes de reporte; tres GLM y quince ajustes de reporte sintéticos se cuentan aparte. Sin política2024, scores2024, ledger, actas o SEL01 abiertos; sin nuevos chats, delegación, cómputo remoto o automatizaciones. La ventana nocturna anterior sigue cerrada. La intervención humana es la autorización de alcance, no una aprobación técnica inventada del modelo. Referencias del proyecto: IAA Documentación§2 y Gobernanza§2.8.
