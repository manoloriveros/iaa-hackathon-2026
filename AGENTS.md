# Carpeta común de entrega y trabajo de la semana 1

Desde el 19 de octubre de 2026 el participante pide trabajar aquí, sin abrir nuevas carpetas por asistente. Esta instrucción sustituye para trabajo nuevo la separación Codex/Claude del 18 de octubre. Conservar el autor real, el linaje y todos los resultados adversos. No renombrar ni reescribir corridas históricas.

Leer `README.md`, `registro/estado_entrega.json`, `registro/requisitos.json` y `docs/archivo/semana1/INFORME_SEMANA1.md`. Usar `herramientas/actualizar_revision.py` para recoger evidencia existente, verificar los CSV y regenerar el panel, sin entrenar. El panel es una fotografía fechada; sus anotaciones personales no equivalen a aprobación registrada.

Código en `src/`, receta congelada en `receta/`, documentación en `docs/`, seguimiento en `registro/`, cálculos nuevos y archivos restringidos en `privado/` (fuera de Git). Cada experimento nuevo requiere hipótesis y criterio de aceptación previo, configuración, origen de datos, resultados, entorno y autor. No cambiar la receta S30 al documentarla ni mezclar linajes por conveniencia de nombres.

Los datos originales permanecen en `../Semana 1/Datos`; las corridas antiguas son fuentes externas locales identificadas por ruta y SHA. El repositorio GitHub es privado. No subir datos, predicciones por fila, modelos entrenados, credenciales ni historiales privados de conversación. Ninguna acción de esta reorganización autoriza entrenamiento remoto, mensajes a terceros, nuevas automatizaciones o selección final manual en Kaggle.

Conservar la memoria común en `../../Preparación/` y los aportes reales del foro en `../../foros/`. Las revisiones de IA se distinguen de revisión humana y de reproducción por otra persona.

Preferencia editorial del participante, 19 de octubre: explicar el problema, el enfoque y el resultado con párrafos breves y títulos descriptivos, sin numeración innecesaria. Concentrar las cifras útiles en tablas. Dejar hashes, identificadores de envíos, nombres internos y precisión completa en anexos o registros; el texto principal conserva los límites que afectan la interpretación. Consultar `registro/criterio_editorial.json` y mantener esta forma de escribir en el informe, el guion y las explicaciones del panel.

## Selección común obligatoria de semana 2, 23 de octubre

El participante pide aplicar el protocolo antes de comparar modelos y dar consecuencias a las advertencias. Consultar `docs/semana2/PROTOCOLO_SELECCION.md`, `registro/semana2_politica_seleccion_v1.json` y el índice `registro/semana2_seleccion_actual.json`. Hay una sola política y un ledger común para todas las líneas, no un filtro por asistente. No consultar scores de modelos en 2024 sin lista/recetas congeladas y apertura registrada por `herramientas/seleccionar_semana2.py`. No promover o retirar una alternativa por un mejor público, reproducción o ganancia incierta. Toda promoción necesita el acta del evaluador y los recibos estadísticos cotejados; los fallos conservan la referencia y los artefactos alternativos. Una excepción para investigar/enviar no cambia los criterios ni reabre confirmación. Las fuentes y autorizaciones anteriores conservan su alcance; esta decisión no entrena ni autoriza envíos.

## Control de versiones, 26 de octubre

El concurso califica el repositorio y su historial (página Submissions y criterio 4 de Evaluation). La guía es `docs/CONTROL_DE_VERSIONES.md` y la herramienta `herramientas/versionado.py`. Rige para todas las líneas:

- Ningún archivo se envía a Kaggle si el código que lo produjo no está en un commit. El recibo del envío copia la salida de `versionado.py sello <rutas del código> --exigir-limpio`.
- El código que corre fuera de este repositorio se incorpora con `versionado.py incorporar` antes de proponer un candidato. No se crean nombres nuevos con `_v2`, `_v3`: una versión nueva es un commit nuevo del mismo archivo.
- Commits temáticos con mensaje en imperativo y tres líneas finales: `Refs:`, `Asistido-por:` y `Revision-humana:`. No se reescribe la historia (`rebase`, `push --force`) ni se ponen fechas de commit falsas; en una reconstrucción, la fecha de autor es la última modificación del archivo y la de commit, la real, y el mensaje lo dice.
- Commits y push los hace un solo operador desde Windows, con autorización del participante. Las sesiones que trabajan desde la máquina virtual no hacen commits: Git no puede borrar allí sus bloqueos.
- Codex corre `versionado.py incorporar --actualizar-todo` y `versionado.py vigia` en su automatización horaria (decisión del participante, 26 de octubre). Con código 3 registra lo pendiente en commits temáticos el mismo día; con código 1 lo corrige antes de cualquier commit. Push al menos una vez al día.
- Nada de datos del concurso, predicciones por fila, modelos o credenciales en Git; el hook se activa con `git config core.hooksPath herramientas/git_hooks`.
- El repositorio sigue privado hasta el cierre de la parte 2 (31 de octubre, 03:59:59 UTC). Después se hace público con la licencia MIT de `LICENSE` (decisión del participante, 26 de octubre); `NOTICE.md` aclara lo que la licencia no cubre.


## Archivo documental del 29 de octubre de 2026

Por instrucción expresa del participante, 246 Markdown anteriores se trasladaron a `Hackaton/Repositorio_IAA2026/docs/archivo/`. Consultar `RUTAS_PROYECTO.json`, la guía `docs/README.md` y `registro/archivo_documental_actual.json` para las rutas actuales. Las referencias activas se ajustaron; las corridas, recetas, notebooks y registros históricos permanecen en su ubicación.

Para una cita o un pin histórico, resolver la ruta con `herramientas/archivar_markdown.py resolver RUTA`. Cuando se exige una huella guardada, pasar `--sha256 HUELLA`: devuelve el original exacto o la copia de esa versión conservada durante el traslado. Desde Python puede usarse `runpy.run_path` sobre esa herramienta y llamar `resolve(ruta, expected_sha256)`. No comparar una copia con enlaces ajustados contra una huella anterior como si fueran la misma versión, ni reescribir los manifiestos históricos. El mapa conserva también los originales de los archivos activos cuyas rutas se ajustaron. Los límites de lectura y autorización previos siguen vigentes.


## Voz de la documentación vigente, 29 de octubre de 2026

Por petición del participante, redactar las guías y la presentación vigentes en su primera persona, con una voz natural y concreta. Conservar la declaración del uso de IA y la autoría real de revisiones, código, fuentes y registros. No transformar una comprobación de un asistente en una revisión humana atribuida a Manuel. Las instrucciones operativas y el histórico firmado conservan su función y autoría. Consultar registro/revision_entrega_actual.json para requisitos, situación de cierre y versiones anteriores de esta edición.
