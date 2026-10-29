

## HET: enlace por riesgo, resultados y separación de forma última, 26 de octubre de 2026

Codex, 2026-10-26T09:14:59.179896+00:00. Se completó el contraste de exposición, conservando T0, modelos fuente, C0, reglas y folds. H2 fue el primario preinscrito (perfil exterior con kappas guardadas); H1 fue la ablation fuente sola. No se intercambian después del resultado.

H1: D² 0.13801903, diferencia frente a G3 +0.00091910, IC95 [+0.00049162, +0.00136048]. Gana en cinco folds y ambos años. Tras retirar los 31 grupos más favorables: +0.00038046; sensibilidad ponderada de cartera 2025: +0.00200432, con ESS insuficiente. Fallos: delta_ge_002.

H2: D² 0.13795613, diferencia frente a G3 +0.00085620, IC95 [+0.00041594, +0.00134089]. Gana en cinco folds y ambos años. Tras retirar los 31 grupos más favorables: +0.00026947; sensibilidad ponderada de cartera 2025: +0.00038314, con ESS insuficiente. Fallos: delta_ge_002, cell_min_ge_minus001.

Ninguno cumple todos los criterios. H1 solo falla la magnitud mínima; eso no lo convierte en ganador confirmado ni habilita envío. H2 también falla una celda de ramo/año/negocio. No se baja el umbral +0,002 ni se ocultan celdas. Las dos direcciones positivas aportan evidencia exploratoria para revisar la observación antes de más capacidad.

Los 30 flujos pasaron alteración de T0/reservas retenidos, replay exacto con todo el aprendizaje bloqueado, momento/derivada de nivel y aritmética de exposición independientes. El mismo perfil exterior se aplicó a entrenamiento y retenido en su ámbito; no se reutilizaron perfiles de otros folds para aprender. Las pruebas sintéticas incluyeron el adaptador de último de 2025 con enlaces observados cero y exposición calendario una sola vez. Coste: 710 constantes cerradas únicas; controles y normalizadores aparte. Cero ajustes iterativos, curvas, kappas, inferencias fuente, precios finales o envíos.

La siguiente pregunta separa la forma última FSp de la observación. Algebraicamente, la razón RFS antigua incorpora la razón de completitudes además de la forma última. Se preparan PUL1 (forma última pura sobre G3) y PUL2 primario (misma forma sobre H1), con los mismos pesos REN .25/.25/.5, conservando NB exactamente. Es una nueva composición adaptativa propuesta, no adopción retrospectiva de H1; requiere otra receta y comentario antes de producir/puntuar precios. No hay parámetros, árboles o curvas adicionales previstos. El comparador completo F3c histórico sigue sin reproducirse; una ganancia local frente a G3 no prueba mejora del público.

2024 abierto y adaptativo; B00, F3c 0,16914, H2 y todas las alternativas/fallos conservados. Ningún cupo consumido; objetivo 0,17 activo. Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/enlace_HET_20261026_v1/report.json; propuesta: Hackaton/Repositorio_IAA2026/registro/semana2_forma_ultima_observacion_propuesta_v0.json.
