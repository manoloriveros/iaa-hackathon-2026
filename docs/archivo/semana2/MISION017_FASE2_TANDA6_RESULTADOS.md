

## Calibración de pendientes por ámbito, 25 de octubre de 2026 (Bogotá)

Codex, 2026-10-26T02:48:27.452778+00:00. La tanda 6 aprendió pendientes de riesgo dentro de cada fold de componentes en 2023–2024. El preflight reprodujo exactamente precios y completitud en los 15 ámbitos con C0/credibilidad ya guardados; no se reestimó ninguna curva. Se ajustaron 30 GLM Tweedie 1,5: pendiente común y pendientes por negocio, con penalización 1 y cuatro interceptos año/negocio de control. Solo se trasladaron pendientes; T3 aplicó la mitad de T2 sin otro ajuste. Se conservaron los totales de cada celda mediante predicciones y covariables.

| Variante | D² local | Diferencia frente a N3 | IC 95 % por componentes | Folds positivos |
|---|---:|---:|---|---:|
| T1 | 0.134370 | -0.000879 | [-0.001772; +0.000010] | 1/5 |
| T2 | 0.134193 | -0.001057 | [-0.002366; +0.000199] | 1/5 |
| T3 | 0.134834 | -0.000416 | [-0.001060; +0.000193] | 2/5 |

N3 = 0.135250 es referencia de investigación sobre T2b, no el envío F2 completo. Las tres variantes empeoran el resultado conjunto y fallan los criterios registrados. La pendiente separada tiene una diferencia de −0,002712 en 2023 y +0,000592 en 2024; esa mejora de un año no basta para admitirla. En nuevo negocio, las pendientes de autos van aproximadamente de 0,66 a 0,94 y las de edificios de 0,63 a 0,99 entre folds. El soporte no estabiliza esas correcciones. Se conservan todos los resultados adversos y no se envía la tanda.

Los 30 GLM pasaron la reconstrucción independiente de matriz, momentos, objetivo scikit-learn y derivadas por diferencias finitas. Se recorrió el flujo real de aprendizaje sustituyendo el optimizador por la solución congelada: selección, inicialización, momentos, objetivos y parámetros resultan idénticos al alterar las etiquetas retenidas, sin volver a ajustar. Las 15 reproducciones de precios fueron exactas y conservaron los totales por ramo/negocio. Coste: 30 estimadores GLM, cero modelos fuente nuevos, cero C0 y 90 normalizadores de cartera sin etiquetas. Los 120 interceptos son parámetros de esos GLM, no 120 estimadores adicionales.

La consulta oficial actual confirmó F2 procesado, referencia 57647413, score público 0,16033. Kaggle informa ocho envíos del día, 20 totales y dos disponibles; el límite activo no es un agotamiento total del concurso. La primera lectura falló por DNS del entorno restringido; la consulta autorizada de lectura funcionó después. No hubo envíos ni cambios de cuenta y no se leyó el score privado. Se conserva el recibo con fecha, sin presentar la consulta como nueva mejora predictiva.

2024 está abierto como desarrollo adaptativo. El ámbito de información de T2b incluye el desarrollado de 2024, conocido al inicio de 2025; no es validación prospectiva de 2024. Los intervalos condicionan en la fuente fijada y no identifican toda la incertidumbre de reservas, cola o maestros sin fecha. Es revisión propia exploratoria, no aprobación humana ni revisión profesional independiente. B00, F2, alternativas y autoría permanecen.

Evidencia: Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/tanda6_pendiente_20261025_v1/validation_v1/report.json; Hackaton/Repositorio_IAA2026/privado/semana2/mision017_fase2/estado_publico_20261026_v1/receipt.json.

Siguiente unidad: Auditar la composición de la cartera de 2025 por ramo, negocio y duración frente a 2023–2024, sin etiquetas nuevas ni ajustes. Revisar por separado la calibración creíble de F2 ya propuesta y sus recibos oficiales: reconstrucción exacta del CSV desde parámetros guardados, identidad/orden de filas, matemática, sensibilidad y límites de extrapolación de forma; no tratar su previsión de score como recibo ni como validación independiente. No lanzar otra familia ni otro ajuste de pendientes con las mismas fuentes. Si hay una mejora bien sustentada, fijar antes de enviar el único candidato, su SHA, criterio y coste; como máximo un envío inicial y conservar el otro cupo. No activar colas antiguas, sondas ajenas ni selección final manual. 2024 sigue abierto como desarrollo; B00, F2 y alternativas se conservan, y la misión 0,17 permanece activa.
