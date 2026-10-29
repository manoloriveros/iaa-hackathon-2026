# P68: GLM actual guardado, coeficientes y contribuciones

Codex, 2026-10-27T04:41:43.832622+00:00. P67mejora su propio entrenamiento con offsetsOOFen15de15ámbitos y supera aP65en6de15retenidos. Diferencia global P67menosP65=-0.0021505; frente aP60=+0.0009609. Puntos sin nuevo intervalo.

Se guardan TODOSlos coeficientes/contrastes en unidades originales y las pérdidas de todas las celdas, sin seleccionar variables.15aplicaciones nuevas al entrenamiento, no ajustes. Las basesOOFusan64%frente a80%enretenido y normalizadores propios; esta brecha no identifica causalmente sobreajuste. Las contribuciones por norma del gradiente y coste se agregan por grupo, sin borrar siniestros ni simular precios capados.

| Ramo | Fold | Δ entrenamiento | Δ retenido | Elasticidad riesgo | Coste top1 grupo | Gradiente top1 grupo | Coste sobrep995 |
|---|---|---|---|---|---|---|---|
| motor | 0 | +0.00187 | +0.00060 | 1.0058 | 0.013 | 0.010 | 0.108 |
| motor | 1 | +0.00243 | -0.00123 | 1.0077 | 0.011 | 0.013 | 0.106 |
| motor | 2 | +0.00239 | -0.00069 | 1.0080 | 0.012 | 0.013 | 0.108 |
| motor | 3 | +0.00176 | +0.00029 | 0.9967 | 0.012 | 0.013 | 0.106 |
| motor | 4 | +0.00251 | -0.00241 | 0.9977 | 0.012 | 0.013 | 0.107 |
| buildings | 0 | +0.00952 | -0.00125 | 1.0385 | 0.046 | 0.022 | 0.199 |
| buildings | 1 | +0.00729 | +0.00165 | 1.0180 | 0.043 | 0.018 | 0.182 |
| buildings | 2 | +0.01384 | -0.01192 | 0.9795 | 0.046 | 0.021 | 0.188 |
| buildings | 3 | +0.00442 | +0.00333 | 0.9607 | 0.050 | 0.024 | 0.164 |
| buildings | 4 | +0.01398 | -0.01784 | 1.0721 | 0.048 | 0.024 | 0.162 |
| contents | 0 | +0.00384 | +0.00015 | 1.0754 | 0.025 | 0.010 | 0.083 |
| contents | 1 | +0.00429 | -0.00353 | 1.0046 | 0.025 | 0.010 | 0.078 |
| contents | 2 | +0.00312 | -0.00042 | 1.0411 | 0.025 | 0.010 | 0.074 |
| contents | 3 | +0.00527 | -0.00327 | 1.0855 | 0.021 | 0.007 | 0.069 |
| contents | 4 | +0.00351 | +0.00068 | 1.0738 | 0.024 | 0.009 | 0.074 |

No se repitieron soportes de categoríaP58, suites o remuestreos. No hay campos/alphaelegidos ni receta posterior admitida. Se mantiene el rechazoP67ycuota;B00/F3cyalternativas conservados,2024abierto adaptativo, reservas/cola/mercado/fuente2024condicional sin certificar. No mejora privada acreditada o revisión profesional independiente.

Próximo: Review NEWP68training gradient/cost concentration and fixed-coefficient contrasts before choosing a standard bounded-influence SHAPE estimator plus exact uncapped Tweedie level, or another concrete mechanism. This is NOTa registered recipe: freeze objective/threshold/config/cost/criteria and synthetic full flow before any real fit. Do not tune alpha/fields, delete claims, alter T0evaluation or submit a probe.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P68_GLM_actual_guardado_20261027/report.json.
