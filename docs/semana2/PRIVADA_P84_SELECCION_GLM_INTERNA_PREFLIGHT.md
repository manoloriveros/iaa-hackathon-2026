# P84: selección interna finita de regularización

Codex, 2026-10-27T07:04:19.753759+00:00. Se prepara un algoritmo que elige unalpha común para todos los ramos entre1/0,1/0,01usando exclusivamente los cincofolds internos del entrenamiento. Minimiza la suma de devianceTweedie sobre todos los retenidos internos; empates numéricos favorecen mayor penalización. Luego ajusta un GLMpor ramo con todo ese entrenamiento. Se mantienen campos, bandas por negocio, prior fuente, objetivo y calendario; no elección por resultados exteriores o públicos.

Pasaron48ajustes sintéticos primarios/48adversos,45internos y3finales porbundle. Alterar TODOel payload exterior antes del selector no cambió selección o modelos; JSONreprodujo los45objetivos internos, el selector y predicciones finales con aprendizaje nativo bloqueado. Cada preproceso se aprende en su propio entrenamiento. Los q sintéticos son fixtures fijos, no curvas RPLreestimadas.

Se prepararon75tablas de q internas desde25objetosP67pinnados, cotejando los grupos exactos de aprendizaje del reporte y el enlace numérico completo con los retenidos internos guardados. Nunca se reutilizó qexterior para elegiralpha; no se cargaron bases de precio P67o modelos nuevos de fuente. La prueba de aprendizaje del reporte es evidencia histórica porSHA, no una nueva auditoría completa. Cero ajustes reales/CDF/scores exteriores/2025/envíos.

La futura evaluación cuesta240GLMprimarios/240adversos y conserva todas las guardas, incluida convergencia de cada candidato interno y transferencia propia si pasa combinado. No hay mejoralpha real, mejora privada o CSVadmitido. B00/F3cyalternativas preservados,2024abierto adaptativo; fuente/snapshots/cola/reservas y búsqueda adaptativa limitan la interpretación, sin revisión independiente.

Próximo: P85: register/commit EXACTP84inner-selected common-alpha whole algorithm,225inner+15finalGLMprimary and sameadverse, no new source/base/CDFfits. All existing outerguards plus inner/final convergence, exact whole selector/model replay. Pooledpass still needs own2023-only conditionaltransfer before CSV. No grid refinement or perline alpha/field/band rescue.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P84_seleccion_GLM_preflight_20261027/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P84_seleccion_GLM_preflight_20261027/synthetic.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P84_seleccion_GLM_preflight_20261027/bindings.json.
