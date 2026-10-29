# P89: árbol estándar sobre el prior calibrado

Codex, 2026-10-27T07:47:15.758780+00:00. P88 no resolvió las pérdidas del GLM pese a calibración simple y convergencia. Se prepara el mismo prior/campos con el boosting restringido ya registrado:64rondas, profundidad3,7hojas y paso máximo0,003, sin aumentar capacidad o buscar parámetros. No se demostró que interacciones causaran la pérdida.

P72 usaba precios/bases OOF P67 y un campo de riesgo derivado de esa base. Esta receta usa las fuentes y bandas originales P88, más sus niveles generales y por negocio; ningún modelo de formas/precio por fila o feature de precio ajustado. Las columnas internas baseline son únicamente offsets para el motor nativo y no entran al diseño.

Pasaron3árboles primarios/3adversos sintéticos y18+18niveles. Hubo splits reales, métrica nativa con offset contrastada por suma escalar, precisión float32de etiquetas declarada, límites/suma de hojas y serialización/proyección exactas. Alterar el payload retenido completo antes de nivelar/preprocesar no cambió modelos o niveles.15entradas reales enlazadas sin ajustar; cero nuevos modelos fuente/CDF/scoring/2025/envíos.

La integridad del algoritmo finito sustituye solo la estacionariedad específica del GLM; las guardas predictivas y transferencia propia siguen intactas. Los pasos cortos no garantizan credibilidad o mejora privada. B00/F3c/adversos preservados,2024abierto adaptativo y límites de información/observación/valoración y selección adaptativa persistentes; sin revisión independiente.

Próximo: P90: register/commit EXACTP89restricted native tree on SAMEP88raw features/owntrain scalar calibratedprior.15primary/15adverse treefits,90+90closedlevels, no source/shapepricebase/CDFfits, all unchanged predictive/cohort/scenario/family16/level/influence gates and native integrity. Ownconditionaltransfer required beforeCSV; no depth/round/step/field/line rescue.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P89_boosting_prior_preflight_20261027/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P89_boosting_prior_preflight_20261027/synthetic.json.
