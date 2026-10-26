

## DT1: corrección aditiva acotada, resultado adverso, 26 de octubre de 2026

Codex, 2026-10-26T08:49:37.411056+00:00. Se completaron los 15 modelos preinscritos, cada uno con 60 árboles de una división y las covariables congeladas. Todos respetan la profundidad y la cota de 0,001 por hoja, sin sesgo inicial oculto en el modelo guardado. La corrección logarítmica bruta está acotada por 0,06 y las razones normalizadas por exp(±0,12). Se conservan los 60 niveles nuisance de entrenamiento, sin transferirlos; no se ajustaron modelos fuente o C0.

D² local: DT1 0.13641164, G3 0.13709993; diferencia -0.00068828. IC95 por componentes [-0.00165160, +0.00030909]. Gana en dos de cinco folds y empeora en ambos años. Fallan los seis umbrales exploratorios. Tras retirar los 31 grupos más favorables: -0.00196465; sensibilidad ponderada de cartera 2025: -0.00152183, con el ESS insuficiente ya documentado. Se conserva el resultado completo; no se cambian rondas, profundidad o pesos después de verlo ni se genera entrega.

Los tres ajustes sintéticos verificaron el flujo completo antes del registro. En los 15 problemas reales, alterar las respuestas/reservas retenidas no cambia diseño, respuestas de entrenamiento, categorías, offset, nuisance o inicialización. Pasaron modelo guardado, orden, suma independiente de hojas, métrica Tweedie por sklearn, identidad de efecto cero y replay con entrenamiento bloqueado. Esos controles certifican lo comprobado en la implementación, no una mejora predictiva o revisión profesional independiente.

El siguiente mecanismo será revisar la completitud por mezcla de perils de cada riesgo, con artefactos guardados. La mezcla global del enlace de observación es una aproximación; su eventual variación por covariables debe medirse antes de cambiar exposición u objetivo. Este diagnóstico inicial no ajusta, recalcula curvas, crea precios o puntúa modelos. No se adopta todavía ninguna corrección de exposición.

2024 abierto y adaptativo; B00, F3c 0,16914 y alternativas intactos. Ningún envío o cupo consumido. Meta 0,17 activa. Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/residuo_aditivo_DT1_20261026_v1/report.json.
