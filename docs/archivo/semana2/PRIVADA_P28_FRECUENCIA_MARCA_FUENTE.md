# P28: GLM número/marca, control fuente completado

Codex, 2026-10-26T21:02:27.970317+00:00. Los30GLM internos terminaron y los tres ramos pasan el veto frente a la referencia constante por peril, bajo el mismo contrato de observación. No se ha calibrado ni puntuado destino.

| Ramo | Desviación GLM | Constante por peril | Cambio relativo | Árbol original, contexto |
|---|---:|---:|---:|---:|
| motor | 125.05349 | 128.45690 | -2.649% | 125.12919 |
| buildings | 116.98671 | 124.65610 | -6.152% | 117.36135 |
| contents | 57.11787 | 60.65083 | -5.825% | 57.02909 |

La comparación con árboles se informa completa: autos y edificios mejoran ligeramente en fuente, mientras contenidos empeora. El criterio preinscrito era la referencia constante bajo el nuevo estimando; no se transforma el contexto de árboles en otra regla posterior ni se rescata solo un ramo. El éxito fuente no acredita mejora privada ni sustituye los criterios completos de destino.

Poisson de número y Tweedie1,5de marca usan efectos principales con el preprocesamiento P14aprendido solo en grupos fuente de entrenamiento. Las respuestas/pesos y la escala de alpha siguen el contrato P27; se retiene la marca cero y no se recortan importes o siniestros. Se guardó cada JSON antes de controles. Los gradientes, la carga JSON, el orden y el predictor por suma escalar pasaron. El replay adicional bloqueó aprendizaje y reconstruyó todas las predicciones fuente retenidas, las sumas por peril y la desviación por otro método; verificó también las entradas efectivas y grupos de cada ajuste.

La protección nueva se refiere al preprocesamiento y coeficientes GLM. Los objetos de observación fuente congelados tienen ancestros comunes que incluyen grupos ahora retenidos; por ello el control es condicional y adaptativo, no una evaluación de todo el aprendizaje de observación sin esos grupos. El control de alteración retenida fue del límite de argumentos, sin duplicar30ajustes reales; no se presenta como un replay de aprendizaje numérico independiente. Los ajustes sintéticos sí ejercieron ambas familias, gradientes por diferencias finitas y las nuevas transformaciones.

Coste nuevo:30ajustes fuente internos,30constantes de referencia por peril, dos ajustes sintéticos separados. Cero C0nuevo, refits fuente completos, calibraciones o scores destino, inferencias2025, precios finales o envíos. Los GLM por peril y FS/FSpanteriores se conservan; esta diferencia de contrato no invalida automáticamente sus productos de coste. Cola última, suficiencia de reservas, fuente2024y maestros sin fecha conservan sus límites. B00/F3c y todas las alternativas permanecen,2024abierto adaptativo. Revisión propia conforme a la distinción de Gobernanza IAA§2.8y Documentación§3; sin aprobación profesional independiente.

Próximo trabajo: P29: preregister30full-source GLM refits with exact P28features,families,nominal penalties and paired offset formulas, no source hyperparameter/seed/line search. Fit preprocessing on all source only; scale penalties by the full-source training weights according to frozen P27formula. Do not refit source C0. Export summed annual frequency*mark rates and original exposure-weighted relative normalization, historical2023/2024only, sourceJSON/gradient/scalar/source-calendar checks. Legacy three_seed cache name would denote one fixed15peril sum, never3seeds. No target calibration/score,2025inference, finalprice or upload in that unit. Only later separately preregister whole original50/50S2/H1comparison with all global/NB/cohort/stress gates; no private improvement from source pass.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P28_fuente_frecuencia_marca_20261026/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P28_fuente_frecuencia_marca_20261026/numerical_replay.json. Código previo a los ajustes:6c3ef39a.
