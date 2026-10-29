# Archivo documental

Conservo aquí los 246 Markdown retirados de las carpetas principales el 29 de octubre de 2026. Consulto la documentación vigente desde mi [guía principal](../README.md). En `versiones_previas_20261029/` conservo las guías anteriores a la revisión de escritura y entrega.

| Carpeta | Procedencia |
| --- | --- |
| [semana1](semana1/) | 23 documentos que estaban directamente en `docs/`, principalmente de semana 1 y notas transversales |
| [semana2](semana2/) | 223 propuestas, cortes de trabajo y revisiones anteriores que estaban en `docs/semana2/` |

Los resultados adversos y la autoría permanecen en cada documento. Se ajustaron rutas y enlaces para leerlos desde su nueva ubicación. Las versiones exactas anteriores se conservaron en el expediente privado de organización, junto con su SHA-256; no se modificaron corridas, recetas ni notebooks.

El [mapa de traslados](../../registro/archivo_documental_actual.json) relaciona cada ruta anterior con la nueva y con su versión original. Las referencias activas se actualizaron. Las rutas citadas en registros históricos inmutables se interpretan con ese mapa, sin cambiar lo que quedó registrado en su fecha.

Para localizar una cita antigua desde la raíz del repositorio:

```powershell
python herramientas/archivar_markdown.py resolver docs/PROPUESTA_MODELO_20261022.md
```

Si un manifiesto histórico exige una huella concreta, añade `--sha256` y esa huella. El resolutor devuelve el original exacto cuando los enlaces del documento archivado han cambiado. Para comprobar los 246 traslados y sus originales:

```powershell
python herramientas/archivar_markdown.py verificar
```

El [índice con búsqueda](../INDICE_DOCUMENTAL.html) permite consultar el archivo por título, ruta y categoría. El expediente privado conserva además el plan, los respaldos de las referencias ajustadas y el registro de cada movimiento.
