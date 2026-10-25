# Rechazo reportado por cantidad de filas en la parte 2

Codex, 23 de octubre de 2026, hora de Bogotá. El participante compartió la [discusión 752144](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/discussion/752144). Kaggle MCP permitió leer el mensaje original y sus tres respuestas. La [respuesta original](../fuentes/kaggle_discusion_752144_20261024.json) y el [cotejo local](../../registro/semana2_cotejo_filas_752144_20261024.json) conservan la evidencia.

El autor reporta que un archivo con una fila por ID de la plantilla emergente es rechazado porque la plataforma espera el tamaño de la parte 1. Otros dos participantes refieren el mismo problema. El comité, con rol HOST, respondió el 23 de octubre a las 18:33 de Bogotá que investigaría y resolvería la incidencia. En el corte consultado no anuncia una corrección. No hubo un intento de envío de esta tarea.

| Comprobación local desde los originales | Filas |
| --- | ---: |
| Test emergente, autos | 90.521 |
| Test emergente, edificios | 52.295 |
| Test emergente, contenidos | 66.247 |
| Total emergente y plantilla emergente | 209.063 |
| Plantilla desarrollada de la parte 1 | 626.639 |

Se leyeron solo metadatos y la columna `row_id`, sin importes, variables predictoras o resultados de confirmación. Pasaron diez comprobaciones: ausencia de nulos y duplicados, conjunto y orden exactos de IDs y coincidencia de los tamaños con el reporte público. Se conservaron las huellas de los cinco Parquet. El script no ajusta ni predice. La primera invocación de Python sin la ruta de dependencias no encontró PyArrow; el cotejo usa la caché existente `Preparación/.cache/parquet-reader`, sin instalar paquetes o modificar el entorno.

La coincidencia respalda el problema reportado. Que el evaluador esté enlazado a la solución de la parte 1 sigue siendo una hipótesis del autor: no se inspeccionó la configuración del servidor y la respuesta del comité no confirma esa causa.

## Consecuencia operativa

Se mantiene el contrato de 209.063 filas emergentes y `row_id,prediction`. No completar con filas desarrolladas, duplicar IDs ni alterar objetivos para satisfacer el rechazo. La incidencia puede impedir una futura entrega externa; no impide continuar el trabajo local autorizado de 2023, con modelos estándar y criterios previos. La evidencia no modifica la política de selección o las restricciones de 2024/test.

La continuidad nocturna existente incorpora la consulta de esta discusión cada hora hasta el 24 de octubre a las 07:00 de Bogotá. Se archivan novedades; si nada cambia, no se repite el cotejo ni se añade un aviso exclusivo. Un anuncio del comité se registraría como corrección anunciada. La aceptación y el scoring solo se acreditarían con un recibo de un envío autorizado posteriormente; no se envía una prueba para monitorizar la incidencia.

El registro separa evidencia externa, verificación propia y causa pendiente, conforme a Gobernanza IAA §§2.8–2.10 y Documentación §2, priorizadas por el proyecto. No constituye validación profesional independiente.


## Actualización UTC2026-10-24T03:14:17.620273+00:00: corrección anunciada

HOST3543798 anunció a las02:57:36.893UTC que la incidencia estaba resuelta. La [consulta nueva](../fuentes/kaggle_discusion_752144_20261024T0307Z.json) conserva la respuesta Kaggle MCP y el corte anterior permanece archivado. Se cotejaron mensaje nuevo, rol HOST, fecha y mensajes previos; no se repitió el cotejo de archivos. Estado actualizado: corrección anunciada, sin verificación propia de recepción/scoring ni causa interna. No hubo envío propio; el anuncio no autoriza uno. Se mantienen contrato emergente, selección y restricciones2024/test. Foro046 e [informe de conciliación](VIGENCIA_B20_E_INCIDENCIA_20261024.md).


## Recepción y scoring verificados, 24 de octubre de 2026

Por instrucción expresa del participante, Codex envió la mezcla 50/50 ya preparada por Claude. Kaggle procesó correctamente las 209.063 filas emergentes: envío 57599788, estado COMPLETE, D² público 0.15390. El [recibo](../../registro/semana2_envio_mezcla50_20261024.json) conserva archivo, hashes, preflight y respuesta. Esto verifica recepción y scoring para ese CSV, sin establecer la causa interna del fallo anterior. Se conserva el rechazo previo del contenedor gzip por extracción, distinto del problema histórico de cantidad de filas. No hubo padding, mezcla entre mercados, entrenamiento nuevo o selección manual final.
