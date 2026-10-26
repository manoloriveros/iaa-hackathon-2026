# P42: frecuencia Poisson con severidad constante

Codex, 2026-10-26T23:12:07.274720+00:00.

El veto conjunto fuente falla. No se estiman medias completas ni se infiere el histórico destino; se conserva el resultado sin elegir ramos favorables.

| Ramo | Cambio relativo de desviación fuente | Pasa |
|---|---:|---|
| motor | +0.0489% | True |
| buildings | +1.0092% | False |
| contents | +1.6897% | False |

Se conservaron los Poisson existentes y sus exposiciones de número. Las constantes de marca respetan la razón E_C/E_Ny el peso N*sqrt(r), incluidos costes cero con siniestros positivos. Las constantes internas ya calculadas se cotejaron y reutilizaron; no se contaron otra vez. Se comprobaron claves, ámbitos, JSON, predicción por suma lineal y exposición una sola vez. El cierre reproduce la desviación guardada por sumas escalares, sin aprendizaje, inferencias nuevas o remuestreo. No se atribuye automáticamente el fallo de P30a severidad ni se busca la ablación recíproca tras ver este resultado.

El holdout fuente ya fue inspeccionado adaptativamente y hereda curvas fuente comunes. No es validación independiente o evidencia privada. Nuevos GLM/C0=0/0; medias fuente completas=0. Cero ajustes/scores destino, inferencias2025o envíos. B00/F3c/alternativas conservados;2024abierto adaptativo.

Próximo: P43: review the remaining paired count/mark source observation assumptions and saved P30/P42source evidence before another model. Constant severity failed; do not pursue an opportunistic reciprocal ablation, relax the veto, rescue a line or increase capacity from this source result alone. Use current source-safe reference and materially new evidence, not the superseded f3_evalabsence, to choose the next concrete standard mechanism.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P42_frecuencia_marca_constante_20261026/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P42_frecuencia_marca_constante_20261026/scalar_replay.json.
