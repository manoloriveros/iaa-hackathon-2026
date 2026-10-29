# P32: no hay evidencia para otra interacción en la fuente

Codex, 2026-10-26T21:49:52.784671+00:00. Se revisó la adecuación condicional de las predicciones fuente retenidas ya guardadas. El contraste primario compara la interacción residual de negocio/canal del GLM con la del árbol original. Ningún ramo supera el filtro fijado antes del readout. Los intervalos incluyen cero y las diferencias quedan muy por debajo del umbral descriptivo del10%. Esto no certifica toda la calibración fuente ni identifica la causa del fallo de transporte.

| Ramo | Diferencia log-interacción GLM menos árbol | Banda95 de familia3 | Filtro completo |
|---|---:|---|---|
| motor | +0.00572 | [-0.00379; +0.01539] | False |
| buildings | +0.00208 | [-0.01800; +0.02173] | False |
| contents | -0.00276 | [-0.02181; +0.01690] | False |

Se conservaron las cuatro celdas y los años fuente, la revisión de soporte, los canales desconocidos y la sensibilidad al retirar31grupos de mayor coste. No se usó ningún A/E como factor de precio. Las réplicas mantienen juntas las filas del mismo grupo fuente y las dos predicciones en cada contraste. La fuente y su enlace de observación siguen siendo condicionales; el readout es adaptativo después del adverso de destino.

Las2000réplicas de cada ramo terminaron, pero el productor falló al exportar un booleano NumPy a JSON. Se conserva el informe parcial y su error. La recuperación reconstruyó solo metadatos y cuantiles desde las mismas fuentes y arrays guardadas; no repitió remuestreo ni ajustes. Los hashes de las6000réplicas no cambiaron y se reprodujeron las cuatro primeras multiplicidades de cada semilla como control. El informe válido se guarda aparte como report_recovered.json; el original parcial no se reescribe.

Cero ajustes, C0, inferencias, precios, scores destino o envíos nuevos. La revisión no justifica más capacidad o una nueva interacción en fuente. B00/F3c y todos los modelos se conservan,2024abierto adaptativo; no se acredita mejora privada ni revisión profesional independiente.

Próximo trabajo: P33: bounded novelty/support review for a standard target-market newbusiness-by-broker residual interaction, on the original incumbent S2/H1, before any fitting or new held scoring. P32does not support adding that interaction to source GLMs; do not refit source or reinterpret its nonsignificant tiny contrast as a pass. Inspect prior P23shared-broker stage, business/credibility recipes and existing target-only cell support by stored outer/transfer training groups. Distinguish a business-specific adaptation from P23main broker effect; inspect whether pooled-within-target-lines coefficient is justifiable and document its exchangeability assumptions and per-line support separately. Do not borrow developed-market support, pool perils, regroup folds or relax cell floors. No new target prediction/score or fit in the support review. If no distinct feasible standard correction is supported, keep the reference and identify another concrete evidence need; do not rescue favorable P30cells. Any later recipe must freeze objective,comparators,regularization,cost and complete protected flow/forum; B00/F3c/all alternatives and adaptive2024open remain.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P32_adecuacion_condicional_fuente_20261026/report_recovered.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/P32_adecuacion_condicional_fuente_20261026/serialization_failure_receipt.json.
