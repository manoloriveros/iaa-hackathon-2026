# P87: calibrar niveles antes de la mezcla y del GLM

Codex, 2026-10-27T07:34:26.233305+00:00. Se prepara el mismo GLM P82, cambiando su prior: cada fuente recibe niveles generales y por tipo de negocio aprendidos en el entrenamiento propio, con la regla Tweedie y credibilidad K400 ya usada. Luego se mezclan 50/50. No se estiman formas de precio ni se copian niveles de otra receta.

Pasaron tres GLM primarios y tres adversos sintéticos con sus18+18 niveles guardados. El payload retenido completo se alteró antes del selector, la calibración y el preproceso; modelos y niveles coincidieron. Momentos/credibilidad por suma escalar, objetivo y gradiente condicional por otro cálculo, replay JSON exacto y proyección por subconjuntos/permutación. El prior conserva unidades al reexpresar la fuente relativa; un negocio sin positivos fue rechazado antes de ajustar el GLM. Se enlazaron15entradas reales, sin estimar sus nuevos niveles.

La calibración y el GLM aprenden del mismo entrenamiento como algoritmo por etapas. No es un offset puramente fuente, stacking independiente ni un óptimo conjunto. El nuevo prior también cambia la normalización de la verosimilitud frente a alpha1 en el objetivo relativo. La prueba futura evalúa el algoritmo completo, sin atribuir una eventual diferencia solo a pesos fuente. Cero ajustes reales/CDF/scores/2025/envíos. B00/F3c/adversos preservados,2024abierto adaptativo; persisten información fuente/observación/valoración y búsqueda adaptativa, sin revisión independiente.

Próximo: P88: register/commit EXACTP87same-bandGLMwith own-training unshaped percomponent line/business calibratedhalfprior.15primary/15adverseGLMfits,90primary/90adverse closedlevels, no source/shapepricebase/CDFfits. ALLexisting outerguards and conditionaltransfer requirement; no copiedP65levels, alpha/grid/field/line rescue.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P87_prior_calibrado_preflight_20261027/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P87_prior_calibrado_preflight_20261027/synthetic.json.
