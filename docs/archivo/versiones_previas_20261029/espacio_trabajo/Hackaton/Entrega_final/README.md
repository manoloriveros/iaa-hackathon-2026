# Entrega final IAA 2026

Selección local organizada el 29 de octubre de 2026. El participante confirmó S41 para la semana 1 y F3c para la semana 2. Las once copias reunidas aquí coinciden por SHA-256 con sus fuentes; [MANIFIESTO.json](../../../../../../../Entrega_final/MANIFIESTO.json) identifica su procedencia. No se modificaron las predicciones ni los documentos originales.

| Carpeta | Contenido |
| --- | --- |
| [01_Para_entregar](../../../../../../../Entrega_final/01_Para_entregar) | [Informe final en español](../../../../../../../Entrega_final/01_Para_entregar/Informe_final_ES.pdf), [predicciones de semana 1](../../../../../../../Entrega_final/01_Para_entregar/Predicciones_semana_1_S41.csv) y [predicciones de semana 2](../../../../../../../Entrega_final/01_Para_entregar/Predicciones_semana_2_F3c.csv) |
| [02_Reproduccion](../../../../../../../Entrega_final/02_Reproduccion) | [Notebook semana 1](../../../../../../../Entrega_final/02_Reproduccion/week1_developed_market.ipynb), [notebook semana 2](../../../../../../../Entrega_final/02_Reproduccion/week2_emerging_market.ipynb), [guía](../../../../../../../Entrega_final/02_Reproduccion/README.md) y dependencias |
| [03_Textos_video](../../../../../../../Entrega_final/03_Textos_video) | [Narración española](../../../../../../../Entrega_final/03_Textos_video/Narracion_ES.txt), [narración inglesa](../../../../../../../Entrega_final/03_Textos_video/Narracion_EN.txt) y [guion español](../../../../../../../Entrega_final/03_Textos_video/Guion_ES.md) |
| [04_Video](../../../../../../../Entrega_final/04_Video) | [Video final en inglés, solo voz](../../../../../../../Entrega_final/04_Video/Video_final_EN.mp4), de 4:59, elegido expresamente por el participante |

El informe vigente tiene diez páginas; las primeras cinco son calificables. Su fuente y huella están en el [registro editorial](../../../../../../registro/informe_final_editorial_actual.json). El video elegido coincide con `IAA2026_video_EN_solo_voz.mp4`; se comprobó su identidad, duración y la presencia de imagen y audio. Esta tarea no revisó íntegramente su contenido audiovisual.

## Versiones conservadas e informe inglés pendiente

La [carpeta de producción audiovisual](<../../../../../../../../Claude%20outputs/video_concurso_20261028>) conserva la versión alternativa y los fragmentos de transferencia. La elección expresa del participante del 29 de octubre identifica la versión de solo voz como definitiva; no hace falta cargar los fragmentos `.part`.

El [PDF inglés recibido](<../../../../../../../../Claude%20outputs/report_en.pdf>) no tiene en el registro editorial una confirmación de concordancia con el PDF español vigente. El inglés de la narración sí tiene una huella registrada. Los informes y las láminas anteriores en `docs/entrega/` conservan su corte histórico.

La [guía del formulario](../../../../../entrega/FORMULARIO_FINAL.md) contiene los requisitos de carga y enlaces. Esta carpeta no acredita envío, marca final en plataforma, acceso público al video o revisión profesional independiente. Las limitaciones de reproducción de los notebooks se conservan en su guía.

## Código y archivo de trabajo

El [repositorio común](../../../../../../README.es.md) conserva el código completo y su historial. La [guía documental](../../../../../README.md) permite consultar métodos y evidencia; el [índice con búsqueda](../../../../../INDICE_DOCUMENTAL.html) recoge los Markdown de soporte. Los documentos anteriores están en [archivo/](../../../../README.md), con sus referencias activas ajustadas y un [mapa de equivalencias](../../../../../../registro/archivo_documental_actual.json) para las citas históricas.

Los CSV y el informe con primas por póliza son restringidos. Esta carpeta es local y está excluida de Git; no debe publicarse como paquete. Para comprobar que sus copias siguen iguales a las fuentes:

```powershell
& 'C:/dev/Hakaton/Preparación/.venv/Scripts/python.exe' 'C:/dev/Hakaton/Hackaton/Repositorio_IAA2026/herramientas/organizar_archivos.py' verificar
```

Si una fuente cambia, el verificador lo señala. No actualiza ni sustituye esta selección automáticamente.
