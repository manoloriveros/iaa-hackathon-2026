# P71: boosting residual estándar, preflight

Codex, 2026-10-27T04:59:32.522599+00:00. Los GLMactuales no superaron las guardas, incluida la forma con respuesta acotada. Se prepara un boosting final estándar restringido sobre los mismos offsetsOOFycampos, para probar una respuesta por tramos; no se ha demostrado que esa estructura resuelva la falta de generalización.

64rondas fijas, profundidad3/7hojas, min_data1000yL2=10, sin earlystopping o búsqueda. La cota por hoja y la suma de64árboles se comprueban en el modelo real, sin capar predicciones después. La documentación de [LightGBM4.6.0](https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html#max_delta_step) describe esa restricción; el preflight contrasta la implementación instalada.

Tres ajustes sintéticos primarios/3adversos ejercitaron splits, offset nativo real comprobado por métrica escalar, suma de hojas por otro método, límites de árbol, precisiónfloat32de etiquetas y replayJSONnativo exacto. El último no lee q/coste/offsetobservado retenidos. Se enlazaron15entradas reales sin ajustarlas. No se repitieron bases/curvas, ni hubo scoring/2025/envíos. La cuenta mínima de filas por hoja es aproximada en el algoritmo y no acredita credibilidad.

Se mantienen todas las guardas predictivas y la necesidad de transferencia propia; la integridad del algoritmo finito sustituye el control de estacionariedad exclusivo delGLM. B00/F3cyalternativas conservados,2024abierto adaptativo. Persisten supuestos de reporte/fuente/cola/mercado/maestros y selección adaptativa; sin mejora privada acreditada o revisión independiente.

Próximo: P72: register/commit fixed64round restricted native-offset residual GBDT,15primary/15adverse fits on exact P67inputs. No base/report/source fits or field/hyperparameter search. Every old predictive/cohort/scenario/family16gate plus actual tree/offset math; transfer OWN2023required after pooled pass, no automatic CSV.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P71_boosting_residual_preflight_20261027/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P71_boosting_residual_preflight_20261027/synthetic.json.
