# P18: la calibración conjunta no mejora la robustez

Codex, 2026-10-26T18:42:18.965452+00:00. Se completó la receta preinscrita: tasas anuales absolutas del GAMfuente con calibración Tweedie conjunta regularizada, sin mezcla N3 ni corrección H1 o normalizadores de cartera al predecir.

| Frente a A1S/S2/H1, nominal | Δ D² | IC95 por grupos | Post31 | Peor celda |
|---|---:|---|---:|---:|
| POOLED | -0.0014624 | [-0.0060474, 0.0028618] | -0.0074248 | -0.0259973 |
| TRANSFER | 0.0026877 | [-0.0021080, 0.0079275] | -0.0052940 | -0.0238447 |

La transferencia es positiva en punto; su intervalo incluye cero. El combinado pierde, y fallan los controles de folds, años, concentración y pisos por celda. La receta no se adopta ni se envía. Compartir escala entre ramos pudo contraer diferencias reales entre mercados, pero esta receta cambió varios componentes a la vez y no identifica una causa única.

| Frente al GAM/S2/H1 de P17 | Δ D² | IC95 emparejado | Post31 | Peor celda |
|---|---:|---|---:|---:|
| POOLED | -0.0027874 | [-0.0055668, -0.0002416] | -0.0057467 | -0.0188274 |
| TRANSFER | 0.0011615 | [-0.0017092, 0.0040678] | -0.0028136 | -0.0222109 |

El intervalo marginal del combinado secundario es negativo; el simultáneo de la familia de diez comparaciones incluye cero. No se interpreta como confirmación independiente tras la búsqueda adaptativa. Se reutilizaron diferencias de draws con idénticos grupos, outcomes, semillas y denominadores, sin otro remuestreo.

| Escenario | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |
|---|---:|---:|---:|---:|
| RESERVE075 | -0.0017236 | -0.0261552 | 0.0015918 | -0.0329587 |
| RESERVE125 | -0.0012164 | -0.0293895 | 0.0036981 | -0.0157594 |
| TAIL005 | -0.0013816 | -0.0259838 | 0.0028447 | -0.0229666 |
| TAIL010 | -0.0012990 | -0.0259696 | 0.0030042 | -0.0220776 |

Se conservaron todos los adversos. Estas sensibilidades usan precios congelados; no representan la reestimación completa de cada valoración de reservas o cola.

Los diez ajustes primarios y diez controles adversos separados terminaron con 29 parámetros por ámbito. Alterar todos los T0/reservas retenidos dejó iguales los objetos aprendidos y precios últimos. Se verificaron el puente de observación, la equivalencia matemática del objetivo de cocientes con la desviación de costes, los gradientes y el flujo completo por filas, lotes y orden cambiado. Los diez replays con fit bloqueado fueron exactos. No hubo nuevos modelos fuente, C0, inferencias2025, precios finales ni envíos. Los coeficientes de estos GLM no se cuentan como constantes cerradas de precio.

Corrección editorial del registro congelado: donde la evaluación dice “PureGammaalgorithm” corresponde GAM, modelo aditivo generalizado. La implementación y las tasas guardadas proceden del GAM de P16; la calibración es Tweedie1,5, no una regresión Gamma de severidad. Se conserva el texto original y su SHA.

El siguiente paso revisará la representación del negocio adquirido por broker con covariables y predicciones ya guardadas. La distribución2025tiene mucho negocio nuevo y el soporte de la ponderación anterior sigue insuficiente. Antes de otra familia de modelos conviene delimitar dónde puede transferirse la evidencia histórica. Las cohortes serán proxies descriptivos; no se ajustarán pesos para favorecer una receta.

Se mantienen B00, F3c y todas las alternativas.2024está abierto como desarrollo adaptativo; la fuente y las marcas incluyen2024y la evaluación anual sigue siendo condicional. No se acredita mejora privada ni revisión profesional independiente.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P18_calibracion_conjunta_20261026/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P18_calibracion_conjunta_20261026/secondary_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P18_calibracion_conjunta_20261026/replay_report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P18_calibracion_conjunta_20261026/secondary_replay_receipt.json.
