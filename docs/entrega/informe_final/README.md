# Informe conjunto de cinco páginas y dashboard comparativo

Este es el informe comparativo histórico del 26 de octubre. El documento vigente de entrega es el PDF identificado en el [índice editorial](../../../registro/informe_final_editorial_actual.json), con diez páginas y cinco calificables. El participante confirmó F3c como definitivo el 28 de octubre; véase la [decisión final](../../../registro/semana2_decision_final_F3c_20261028.json). Las referencias a selección pendiente en los artefactos de esta carpeta corresponden al corte histórico y no sustituyen esa decisión.

Edición de Codex, 26 de octubre de 2026, sobre el EDA común y el informe conjunto anterior de Claude. El original de Claude, sus anexos y los entregables de semana 1 se conservan.

El [PDF actual](../../../privado/entrega_final/informe_dos_semanas.pdf) contiene exactamente cinco páginas totales, sin portada o anexos adicionales. Está fuera de Git porque incluye los importes por fila de las veinte referencias oficiales. La plantilla [INFORME_ES.md](INFORME_ES.md) conserva el marcador de esa tabla; sus valores se leen de la corrida privada.

| Página | Comparación integrada |
| --- | --- |
| 1 | Historia, volúmenes, cambio de clientes entre 2024 y 2025 y adaptación por etapa |
| 2 | Coste, frecuencia y severidad de 2023-2024; calidad y variables con columnas paralelas |
| 3 | Modelos, métricas con año y muestra identificados, y cadena pública de semana 2 |
| 4 | Reserva de 2024 por ramo, selección, reproducción, uso de IA y límites |
| 5 | Supuestos de gastos de ambos mercados y primas de las veinte referencias emergentes |

Los colores se mantienen: azul para semana 1, naranja para semana 2. Las barras comparten escala dentro de cada indicador. Las tasas comparables usan solo 2023-2024; la reserva usa 2024. La primera cohorte del archivo no se trata como adquisición de clientes. El público de parte 2 y el privado de parte 1 se etiquetan por su muestra y no se dibujan como resultados de un mismo test.

El [dashboard](../panel_analisis.html) muestra ambos mercados a la vez. Los filtros de cohorte y ramo actúan sobre las dos columnas y las barras emparejadas. Se puede alternar coste por exposición, frecuencia, severidad, reservas, ceros y exposición. La exportación corresponde a la comparación visible y conserva nulos los resultados de test. Los conteos completos de exclusión y el contexto 2024-2025 se identifican como alcances fijos.

El informe superó el conteo de cinco páginas, la extracción de texto y la comprobación de que cada referencia aparece una sola vez. Las primas se calcularon desde el F3c guardado, cotejado por SHA-256, y los gastos originales, con identidad Decimal y comprobación alternativa en float. Los totales de la tabla suman sus filas ya redondeadas; el cálculo de cada prima usa la precisión guardada sin redondeos intermedios.

La UI pasó 508 comprobaciones sobre 96 combinaciones de cohorte, ramo e indicador, exportaciones, teclado, impresión, enlaces y anchos de 320, 390, 768 y 1440 px. Sin errores JavaScript o solicitudes HTTP(S). Las cinco páginas y las capturas se revisaron visualmente por Codex. Es revisión propia asistida por IA, sin validación profesional independiente o aprobación humana atribuida.

Se conserva un primer intento de seis páginas: una línea de la segunda pasó a una página huérfana. Se acortó esa explicación sin reducir el cuerpo tipográfico. La prueba inicial de navegación trató el fragmento `#limites` como parte del nombre de archivo; se corrigió la prueba. El informe y el dashboard pasaron después sus comprobaciones finales.

El índice es `registro/informe_comparativo_actual.json`. `datos_informe.json` recoge fuentes con autoría y SHA-256; la corrida conserva el PDF, sus cinco PNG, las veinte referencias y los recibos. Los comandos están en [el README de entrega](../README.md). No hubo entrenamiento, nuevas predicciones, envíos o modificación de la selección final. S41 permanece seleccionada en parte 1; F3c es la referencia pública medida al corte y la selección de parte 2 sigue abierta.

## Revisión posterior de los doce pendientes, 26 de octubre

El [cierre técnico de F3c](../../archivo/semana2/CIERRE_DOCE_PENDIENTES_F3C.md) limita las conclusiones que pueden trasladarse a la entrega: ganancia global condicional, incertidumbre de negocio nuevo, concentración y cadena completa pendiente de reproducción. No promueve F3c ni acredita uso profesional.

También corrige un supuesto de la página de primas: la descripción oficial dice gasto fijo por póliza, sin indicar prorrateo anual. La lectura principal nueva cobra 85 CU por referencia y suma 20.800,02 CU en F3c; la anterior, 85 × exposición, sumaba 20.304,23 CU y se conserva como sensibilidad. La nueva tabla por referencia está en privado, enlazada desde el cierre. El PDF de esta edición permanece como corte anterior y requiere integrar esa corrección antes de otra entrega. Sus controles de cálculo y maquetación no resolvían la interpretación del gasto.
