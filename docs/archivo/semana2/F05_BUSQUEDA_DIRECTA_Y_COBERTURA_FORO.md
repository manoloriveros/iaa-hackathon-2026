# F05: búsqueda directa del foro y cobertura comprobada

Codex, corte UTC 2026-10-24T17:05:12.645248+00:00. El fallo queda resuelto para esta revisión mediante una ruta alternativa verificada: enumerar los temas de cada competencia, recuperar directamente todos sus mensajes y buscar en ese texto. El buscador general de Kaggle sigue omitiendo el control conocido. No se afirma haber reparado su servidor ni determinado su causa interna.

## Método y cobertura

Las peticiones mínimas, con campos nullable y con título completo en la búsqueda general no recuperaron Claims Data Query, tema 751543. La enumeración específica sí lo devuelve. Por eso las respuestas vacías generales se mantienen excluidas como evidencia de ausencia.

Se consultó list_competition_topics por slug de cada parte y se cotejó el número de entradas con total_count. Después se llamó get_forum_topic por cada ID, con el mensaje inicial y hasta 100 respuestas. Se verificaron ID y URL del mercado/competencia, mensaje inicial no vacío, IDs únicos y coincidencia entre respuestas recibidas, recuento del listado y total del servidor. Ningún tema excede ese límite; una discrepancia habría detenido la conclusión de cobertura.

| Ámbito | Temas y mensajes iniciales | Respuestas | Mensajes revisados |
| --- | ---: | ---: | ---: |
| Parte 1 | 7 | 7 | 14 |
| Parte 2 | 2 | 5 | 7 |
| Total | 9 | 12 | 21 |

El listado posterior conserva los mismos IDs, recuentos y fechas del último comentario que el inicial. Esto concilia el corte de consulta; no demuestra una transacción atómica del servidor ni conserva historial de ediciones. El control positivo encuentra Claims Data Query por su título y su respuesta directa contiene el mensaje inicial. El control negativo sin coincidencias y cuatro controles adversos del nuevo lector verifican rechazo de tema faltante, URL de otra competencia, respuesta faltante e ID de mensaje duplicado. Son controles de recuperación, no nuevos diagnósticos de datos o modelos.

La ruta quedó implementada en herramientas/buscar_aclaraciones_foro_seguro.mjs. Recibe los inventarios completos y las respuestas directas obtenidas con Kaggle MCP, valida cobertura antes de buscar y guarda hashes/autor/ID/UTC. No llama al buscador general. Se probó con el flujo real recuperado, además de los adversos. No se ejecutó ningún productor histórico ni se instaló otra dependencia.

## Aclaraciones de clima pendientes

Se buscaron referencias al clima, pronósticos, riesgos, los siete nombres de campos climáticos y términos asociados a viento, incendio, granizo, lluvia o temperatura. También se buscaron expresiones generales de información conocida, fecha de decisión, futuro y disponibilidad al cotizar que pudieran contener una aclaración sin nombrar weather. No se encontró una coincidencia climática o de ese contexto temporal en los 21 mensajes recibidos. No se presenta el resultado como una comprensión infalible de cualquier paráfrasis o una búsqueda universal de fuentes privadas.

Esta consulta cubre ahora los cuerpos de mensajes y respuestas de los nueve temas listados, que F05 anterior no había cubierto. No apareció una aclaración del organizador que cambie la interpretación de 2023. Las definiciones oficiales ya consultadas y archivadas se reutilizan; no se vuelve a abrir el Parquet ni se repiten diagnósticos de clima.

Sigue faltando distinguir, por campo, agregado realizado, pronóstico o riesgo calculado previamente, con ventana, método, insumos, emisión/publicación y vigencia. Los agregados completos de 2023 no estaban realizados al iniciar el año. El nombre de los índices de viento/incendio no acredita su disponibilidad previa ni demuestra fuga por sí solo. El año de referencia, la fecha de subida del archivo y una fecha de cotización derivada no sustituyen la fecha de conocimiento del dato.

Se conserva el rechazo prospectivo anterior de CLIMA-S2-01 y el hallazgo S2-VAL-DAT-003 con su responsable. Ninguna variable se añade a B20, ni se rellena historia con otro mercado o años posteriores. La revisión no establece G1 o resuelve G2 y no justifica una nueva prueba de precios.

## Registro y límites

Se guardaron hashes del texto y de la fuente canónica por mensaje/tema, autores, IDs, UTC, recuentos, estabilidad del inventario y recibos de búsqueda. Los cuerpos ajenos no relacionados con clima se procesaron en memoria y no se publican o archivan completos; no se emitieron métricas ajenas. Una revisión posterior de otras expresiones requeriría recuperar la fuente y cotejar su hash. No se atribuye a estos recibos un replay íntegro sin volver a consultar el texto.

La limitación antigua del buscador se conserva como evidencia histórica en [F05 inicial](F05_CLIMA_2023_Y_DISPONIBILIDAD_TEMPORAL.md); este seguimiento sustituye su límite de cobertura de los comentarios para el corte indicado. B00 y todas las alternativas, T0/C0, exposición, folds, modelos y contadores siguen intactos. Cero entrenamiento, cargas de modelos, inferencias, scores, remuestreos o filas de datos leídas. 2024/test/ledger/actas/SEL01 permanecen cerrados para modelado y confirmación. La exposición histórica de un asunto externo sigue declarada, sin usar sus métricas o afirmar ceguera completa. La ventana nocturna continúa cerrada, sin contactos externos, otros chats, delegación o automatizaciones nuevas. Codex firma revisión propia de recuperación/fuentes, sin aprobación humana o validación profesional independiente.

El [índice del seguimiento](../../../registro/semana2_F05_busqueda_foro_actual.json) enlaza recibos, código, controles, decisiones y fuentes con SHA. Los temas oficiales están en los foros de [parte 1](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1/discussion) y [parte 2](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/discussion); el control es [Claims Data Query](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-1/discussion/751543).
