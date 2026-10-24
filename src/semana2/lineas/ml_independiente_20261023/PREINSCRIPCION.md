# Preinscripción de la línea ML independiente (semana 2)

Escrita el 24 de octubre de 2026 a las 02:45 UTC (23 de octubre, 21:45 de Bogotá), antes de construir etiquetas, ajustar modelos o mirar cualquier comparación entre candidatos. Autor: Claude, sesión «ML independiente» abierta por el participante con la instrucción de analizar los datos de las dos semanas y montar modelos de aprendizaje automático completos, validados y calibrados, con libertad para probar transformers y ajuste fino, sin afectar a las demás sesiones.

## 1. Independencia y lo que ya se sabe

Esta línea escribe todo su código desde los Parquet originales (13 emergentes y 7 desarrollados, SHA-256 comprobados contra el equipo). No lee predicciones, factores, matrices ni código de otras líneas (Codex, las otras sesiones de Claude). Sí usa hechos de calidad de datos documentados en el proyecto, que vuelve a comprobar con código propio: exposición en días/365, capitales con escala ×1000 en hogar, duplicados de siniestros del desarrollado, `customer_service_contacts` como indicador del siniestro del propio periodo, `renewal_decision` solo en entrenamiento. Se declara que el autor conoce dos cifras agregadas de otra sesión (D² 2023 de 0,1213 de su modelo de transferencia A1 y 0,1214 en 2024); no se usan para elegir nada.

## 2. Objetivo y escala

Para cada fila de test 2025 del mercado emergente, coste último esperado del periodo, neto de franquicia y recuperaciones, sin rechazados. Métrica: D² Tweedie con potencia 1,5 sobre el vector concatenado de los tres ramos.

Etiqueta observada T0: suma de `incurred_to_date − recoveries` de los siniestros no rechazados con `loss_date` dentro del periodo (misma póliza y ramo). Se modela la tasa última y se compara con lo observado multiplicando por la completitud de reporte de la fila: E[T0] = μ_último × c_fila. La completitud c_fila se calcula con la distribución de retraso de reporte ponderada por coste, por ramo y peligro, estimada en cohortes maduras del desarrollado y contrastada en el emergente; las reservas de caso se toman sin sesgo (supuesto declarado). En los ajustes, el desplazamiento es log(exposición × c_fila).

## 3. Particiones

| Fase | Entrenamiento emergente | Desarrollado para preentrenar | Evaluación |
| --- | --- | --- | --- |
| DEV | 2023, cinco pliegues por cliente | 2021–2023 | OOF de 2023 |
| HOLD | 2023 completo | 2021–2023 | 2024, se abre una sola vez con la lista congelada |
| PROD | 2023–2024 | 2021–2024 | test 2025 (sin enviar) |

Pliegue = entero de los primeros 16 hex de SHA-256(`mlind_v1|` + customer_id) módulo 5.

## 4. Candidatos (orden de complejidad)

- R0: tasa última por ramo.
- G1: GLM Tweedie (log, p = 1,5) solo emergente, variables categorizadas.
- T1: LightGBM Tweedie solo emergente.
- T2: LightGBM Tweedie preentrenado en el desarrollado con el esquema común, transferido sin reentrenar (solo nivel por ramo).
- T3: T2 más ajuste fino por boosting residual en el emergente (puntuación inicial = log de la predicción de T2 más desplazamiento; tasa de aprendizaje baja; rondas por parada temprana interna).
- T4: modelo conjunto desarrollado + emergente con indicador de mercado y peso mayor del emergente.
- N1: FT-Transformer (Gorishniy et al., 2021) solo emergente, pérdida Tweedie 1,5 con desplazamiento.
- N2: FT-Transformer preentrenado en el desarrollado y ajustado fino en el emergente.
- N3: red residual tipo CANN sobre el mejor árbol (salida inicializada en cero).
- E: mezcla convexa por ramo de las predicciones OOF, con pesos ajustados por validación cruzada cruzada (pesos de cuatro pliegues aplicados al quinto).

Las variantes de cada familia (bloques de variables, hiperparámetros) se declaran en el registro de experimentos antes de correrlas y todas se informan, también las adversas.

## 5. Criterio de selección (solo DEV)

Primario: D² OOF de 2023 con todas las filas. Robustez, obligatoria para el elegido: (a) D² del cuerpo (sin las filas del 0,5 % de pérdidas positivas mayores por ramo, cada candidato renivelado por ramo al total observado del cuerpo) y (b) D² ponderado a la mezcla de 2025 (pesos de razón de densidad de un clasificador adversarial DEV frente a test 2025, recortados a [0,1; 10]) no inferiores a los de T1. Un candidato más complejo sustituye a uno más simple solo si mejora el primario en al menos 0,001. Intervalos por remuestreo de clientes (1.000 réplicas) para toda diferencia que se informe.

## 6. Calibración (reglas fijadas ahora)

1. Nivel por ramo: k = Σ y/√(μc) / Σ √(μc) sobre OOF (factor que minimiza la desviación Tweedie 1,5), calculado en DEV para HOLD y en OOF de 2023–2024 para PROD.
2. Tendencia a 2025: factor por ramo τ^Δt, con τ la pendiente log-lineal anual del cociente observado/esperado del desarrollado (modelo sin año, etiquetas ajustadas por completitud) en 2021–2023 para HOLD y 2021–2024 para PROD; Δt = fecha media de cobertura objetivo − fecha media de cobertura de entrenamiento, ponderadas por exposición.
3. Diagnóstico de calibración: descomposición de Murphy de la desviación (incertidumbre, discriminación, descalibración) con recalibración isotónica, A/E por deciles y por segmentos (nuevo negocio, canal, región, ramo). La recalibración isotónica no se aplica a la entrega; solo diagnostica.
4. Nada se recalibra con el test ni con el tablero.

## 7. HOLD

Tras congelar la lista y el elegido de DEV, se reajusta cada candidato congelado con 2023 y se puntúa 2024 una sola vez: D² completo, cuerpo y ponderado, por ramo, diferencias con remuestreo, y prueba de la regla de tendencia (Δt ≈ 1). El elegido no cambia por el resultado de HOLD; si HOLD contradice a DEV, se informa como hallazgo.

## 8. Fuera de alcance

Sin envíos a Kaggle, sin cómputo remoto, sin escribir en carpetas de otras líneas ni en sus índices. Las salidas por fila van a `Repositorio_IAA2026/privado/semana2/claude_ml_independiente_20261023/`; el resto a `Hackaton/Semana 2/Claude/ml_independiente_20261023/`.
