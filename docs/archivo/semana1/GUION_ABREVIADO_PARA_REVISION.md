> Guion histórico. La versión española vigente de ambas semanas está en [GUION_VIDEO_ES.md](../../entrega/video/GUION_VIDEO_ES.md): nueve escenas, objetivo 4:45, F3c, gasto fijo de 85 CU por póliza y cierre técnico de reproducción del 26 de octubre.
# Guion abreviado del video para revisión

Este borrador reserva tres minutos y veinte segundos a la primera semana, un minuto y veinte segundos a la adaptación y quince segundos al cierre. El objetivo de duración es 4:55. Las láminas y el guion de entrega existentes se conservan; este borrador sirve para decidir el montaje antes de grabar. La adaptación se completa con resultados reales de la parte 2.

## Narración propuesta para la primera semana

La narración principal se prepara en inglés, con las figuras que ya existen. Los tiempos son un presupuesto de edición; deben comprobarse al leer y grabar.

| Tiempo | Imagen | Narración propuesta |
| --- | --- | --- |
| 0:00–0:20 | Portada y resultados | I am Manuel Rodríguez. My final Part 1 model, the Per-peril blend, predicts the expected ultimate claim cost of each 2025 policy period. Its public Tweedie D-squared score is 0.12996. On the reused 2024 validation cut it scores 0.138, compared with 0.071 for a constant rate per line. |
| 0:20–0:45 | Flujo de datos y siniestros | Eleven original files stay untouched. Reversible rules correct identifiers, exposure units and supported sums insured, and remove exact duplicate claims. A separate implementation rebuilt the prepared data. Each accepted claim is assigned once, by policy, line and occurrence date. The observed target is incurred cost less recoveries, with declined claims excluded. |
| 0:45–1:10 | Completitud y mezcla por peligro | Observed cost is incomplete. A count chain-ladder estimates reporting completeness by peril. Effective training exposure incorporates that adjustment once; production uses nominal exposure. The model blends total-cost Tweedie models with per-peril frequency times severity models. Level factors come from 2023 and 2024. Those cuts were reused for selection, so their results are not an untouched test. |
| 1:10–1:45 | Flujo de IA y dos correcciones concretas | Two AI assistants worked in modelling, creative alternatives and challenge. Hypotheses and acceptance criteria went to a shared forum, and adverse results stayed in the record. Cross-checks rejected an unsupported improvement claim and narrowed an overstatement about reserves. Validation agents also found that the reproduction package could report success with missing files. The controls were repaired and exercised with valid and deliberately invalid cases. These are cross-checks within the same project, not independent professional validation. |
| 1:45–2:15 | Diseño de validación y sensibilidad | We fit on earlier years and evaluate later periods. After selection, eleven pre-registered sensitivity experiments tested the result. Removing six customers reverses the small local lead over the previous submission. Reporting backtests fail their criterion for six or seven of fifteen perils. Reserve scenarios barely move the score but can materially change the 2025 level. These findings remain limitations of the final model. |
| 2:15–2:45 | Recibo de reproducción y panel | Rebuilding from the originals produced the exact submitted CSV. Nineteen intermediate fingerprints differ in the last bits, so the recorded exit code remains three. A replay from captured estimators matched its new reference according to the author's receipt. The same workflow performed both. The dashboard exposes the figures and their sources for human review; it does not approve them. |
| 2:45–3:20 | Límites y decisiones humanas | The participant confirmed this model as final. Reserve adequacy and the absence of independent reproduction were accepted as declared limitations. One claims valuation cannot establish ultimate losses, some feature availability dates remain unconfirmed, and 149 sums insured lack economic confirmation. The general human review is separate from those decisions. The frozen Part 1 model is our reference for assessing adaptation to the new market. |

La narración de esta parte evita convertir el D² en un porcentaje de aciertos, llamar independiente al contraste entre asistentes o presentar el IBNR como un último observado.

## Adaptación de la segunda semana

| Tiempo | Evidencia que debe existir | Narración que se completa después |
| --- | --- | --- |
| 3:20–3:50 | Comparación de contrato, unidades, exposición, peligros, reporte y variables | On the new market, the frozen reference scored [measured D²]. We found [observed differences]. Under our pre-registered protocol, these differences justified [specific adaptation]. |
| 3:50–4:40 | Referencia frente a adaptación, por ramo y con incertidumbre | The adapted model scored [measured D²], compared with [reference], with [calibration or stability result]. The public score was [observed score]. The most useful AI challenge was [authentic example and correction]. [Remaining uncertainty] still limits the result. |

Usar la misma métrica y un esquema de evaluación compatible en la comparación. Si falta una cifra o la adaptación no mejora, se comunica el resultado observado; no se completa el espacio con un efecto supuesto.

## Cierre y comprobación del montaje

Entre 4:40 y 4:55, mostrar dónde están el código, las decisiones y los límites. Una frase posible: “The repository records how the estimates were built, challenged and checked. The final report explains the adaptations and the limits a reviewing actuary must consider.”

Antes de grabar, cronometrar la lectura completa, sustituir los corchetes solo por resultados medidos y comprobar la versión final contra el informe. El corte del jurado está en los primeros cinco minutos. Si falta tiempo, acortar la historia de semana 1 antes de reducir la comparación del mercado nuevo.
