# F05: clima de 2023 y disponibilidad temporal

Codex, corte UTC 2026-10-24T16:55:23.806770+00:00. No se localizó una aclaración oficial nueva que acredite la disponibilidad prospectiva del clima de 2023 o defina sus índices como riesgos conocidos antes de cotizar. La búsqueda tiene límites: el buscador de palabras del foro falló un control positivo y no se revisaron todos los cuerpos de comentarios. Por tanto, no se afirma ausencia universal de aclaraciones.

## Fuentes comprobadas y límites de búsqueda

El [diccionario de la parte 2](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/data), releído por Kaggle MCP, coincide íntegramente con el archivado. La sección weather del [diccionario de la parte 1](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1/data) coincide con la actual de la parte 2. El texto define una fila por dirección/año, pero no fecha de publicación, captura, versión de pronóstico o entrenamiento del índice. No se abrió weather.parquet ni se contaron o compararon celdas.

Los listados específicos devuelven siete temas y total_count=7 en parte 1, y dos y total_count=2 en parte 2. No hay un título identificado como weather,climate,forecast o hazard. Los dos temas de parte 2 mantienen las fechas/recuentos de la búsqueda F04, referidos a descarga y formato de envío, sin releerlos como si fueran una novedad climática. La revisión de títulos no cubre aclaraciones enterradas en comentarios de otros temas.

La búsqueda general por categoría devolvió temas de otras competencias y se descartó. Tras obtener el forum_id oficial, las consultas weather/climate por foro devolvieron objetos vacíos. También devolvió vacío Claims, aunque el listado específico contiene el tema conocido 751543. Ese control impide convertir las respuestas vacías en evidencia de que no existe una aclaración. Las máscaras de metadatos no devolvieron el localizador; se obtuvo después de metadatos del tema, sin emitir o usar su cuerpo ajeno. Los recibos conservan estos fallos, sin presentar el buscador como verificado.

Como respaldo se consultó el índice web con las rutas de discusión de ambas competencias y términos climáticos. Los resultados visibles remitían a eventos ajenos, incluido el hackathon Ames 2025; se excluyeron. No se adoptaron reglas, definiciones o permisos de otros concursos. El índice público tampoco acredita cobertura completa. No se contactó al organizador o a terceros.

## Qué significa cada medida y qué falta fechar

| Campo | Definición documental | Límite temporal |
| --- | --- | --- |
| hail_days | Número de días con granizo del año | Recuento anual; no se describe como pronóstico emitido antes del año |
| freezing_days | Días bajo cero, dentro de tabla por año | Recuento del año de referencia; sin vintage de pronóstico/publicación |
| rainfall_mm | Precipitación anual | Agregado anual; no previsión fechada en el diccionario |
| mean_temperature_c | Temperatura media anual | Agregado anual; no previsión fechada en el diccionario |
| dry_summer_index | Sequedad estival, escala húmedo/seco | Índice de estación/año; no consta metodología,ventana exacta o naturaleza observada/pronosticada |
| wind_exposure_index | Exposición a viento dañino, escala0–10 | Podría representar una medida de riesgo; no consta si es estática,realizada o prospectiva ni vintage |
| wildfire_index | Riesgo de incendio forestal, escala0–1 | No consta si es hazard previo,pronóstico o índice actualizado con experiencia del año |

Los recuentos y agregados de todo 2023 no estaban realizados al iniciar ese año. Su presencia en una tabla entregada posteriormente no los convierte en información disponible entonces. Si algún campo fuera un pronóstico, se necesitarían su fecha de emisión y versión; el diccionario no lo establece. dry_summer_index necesita además ventana de referencia y aclarar si resume la estación realizada o una previsión.

wind_exposure_index y wildfire_index tienen lenguaje de riesgo, pero eso no prueba un mapa estático anterior al periodo. Tampoco basta para afirmar que sus valores incorporen siniestros futuros o sean fuga demostrada. Método, insumos, periodo de cálculo, publicación y vigencia no constan en las definiciones examinadas. Correlación o persistencia entre años no resolverían estas preguntas y no se vuelven a medir.

## Año de referencia, publicación y fecha de decisión

year es el año al que corresponde la medida, no la fecha en que se conoció. Para un agregado realizado haría falta que su ventana hubiera terminado y su publicación/captura ocurriera antes de la decisión. Terminar el calendario no prueba publicación inmediata. Para un índice de riesgo o pronóstico se necesitaría acreditar una versión emitida con los insumos entonces disponibles y su vigencia, sin usar resultados posteriores para construirlo o elegirlo.

La variante histórica existente deriva quote_date=period_start−days_quote_to_inception y selecciona el año natural anterior. Es una convención conservadora de calendario con disponibilidad al terminar el año asumida en la documentación; no una comprobación de la fecha real de publicación. Como ya señaló F02, esa resta tampoco crea una cotización o declaración versionada. Se cualifica aquí su interpretación, sin editar la función, el contrato o artefactos históricos.

La revisión previa dejó documentada ausencia de historia climática emergente anterior a 2023 para la prueba. Se reutiliza ese resultado y no se repite el inventario de valores. Los registros desarrollados no proporcionan una dirección emergente equivalente: los identificadores pueden colisionar y no existe correspondencia geográfica publicada entre regiones sintéticas. No se rellena con clima de otros mercados, del mismo año o posterior, ni se inventa un cruce a clima real.

## Decisión vigente y evidencia necesaria

La variante CLIMA-S2-01 ya quedó fuera del contrato prospectivo por sus fuentes y selección posteriores. Se conserva la revisión anterior y su hallazgo S2-VAL-DAT-003, con autoría y responsable; no se repiten permutaciones, guardas, replays o scores, ni se cierra el hallazgo. La búsqueda actual no aporta evidencia para cambiar esa decisión. No se entrena una copia con clima todo ausente ni una variante con información posterior.

Para reconsiderar F05 se necesitaría una aclaración oficial versionada por campo: observado/pronosticado/hazard estático, ventana de referencia, método e insumos, fecha de emisión o publicación y vigencia. Una fecha genérica de subida de Parquet no cumple esa función. También se necesitaría historia legítima para las direcciones emergentes y un instante de decisión verificable si se pretende uso prospectivo. Una autorización de uso en el concurso, si existiera, no fecharía por sí sola el conocimiento histórico de cada valor.

Esta ficha es una revisión documental de disponibilidad, no una nueva receta o admisión de predictores. Ninguno de los siete campos climáticos entra en B20. F05 queda buscada sin aclaración temporal nueva localizada, con clasificación de índices y fechas aún pendientes. No añade siniestros, exposición o componentes, ni establece G1 o resuelve G2.

B00 y todas las alternativas, T0/C0, exposición, folds, modelos y contadores se conservan. 2024/test/ledger/actas/SEL01 siguen cerrados para datos/resultados de modelado; no se cargaron sus artefactos. Cero entrenamiento,cargas de modelos,inferencias,scores,remuestreos o nuevos diagnósticos. Exposición histórica de un asunto externo declarada, sin repetir o usar sus métricas ni afirmar ceguera completa. Ventana/automatización nocturna cerradas, sin nuevas continuaciones, contactos o delegación. Codex firma revisión propia de fuentes, no aprobación humana o validación profesional independiente. Las prácticas IAA de documentación §2 y gobernanza §2.8 orientan separar disponibilidad,supuesto y verificación.

El [índice F05](../../../registro/semana2_F05_clima 2023_actual.json) enlaza matriz por campo, consultas y limitaciones, fuentes/SHA y decisiones. Se conserva la [revisión climática previa](CAPITAL_CLIMA_CREDIBILIDAD_2023.md), la [disponibilidad inicial](VARIABLES_Y_ULTIMO.md) y [F02](F02_SEMANTICA_Y_DISPONIBILIDAD_2023.md) sin reescribirlas.
