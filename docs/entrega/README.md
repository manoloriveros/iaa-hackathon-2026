# Final deliverables · Entregables finales

Everything in this folder is generated from one data file, [`datos/cifras_entregables.json`](datos/cifras_entregables.json), which records the path and SHA-256 of each source it reads. No file here contains row-level data. Todo lo de esta carpeta sale de un único archivo de datos, que registra la ruta y el SHA-256 de cada fuente; ningún archivo contiene datos por fila.

| File | What it is | Archivo |
| --- | --- | --- |
| [`report_en.pdf`](report_en.pdf) | Report: five graded pages and an appendix | Informe en inglés |
| [`informe_es.pdf`](informe_es.pdf) | Spanish copy of the report | Informe en español |
| [`informe/`](informe/) | Markdown sources of both reports | Fuentes Markdown del informe |
| [`panel_modelo.html`](panel_modelo.html) | Offline model dashboard, English or Spanish, light or dark; every chart has a table view | Panel del modelo sin conexión |
| [`video/`](video/) | Slides (PDF and PNG, 1920 × 1080) and the video script in both languages | Láminas y guion del video |
| [`AI_WORKFLOW_EN.md`](AI_WORKFLOW_EN.md) | How AI was used and how it was checked | [`USO_DE_IA_ES.md`](USO_DE_IA_ES.md) |
| [`figuras/`](figuras/) | Every chart and diagram as PNG, per language | Gráficos y diagramas en PNG |
| [`web/`](web/) | Chart library, diagrams, styles and the embedded Inter font (SIL OFL) | Biblioteca de gráficos y estilos |
| [`datos/`](datos/) | The data file and the record of the last build | Archivo de datos y última construcción |

Rebuild and check · Regenerar y comprobar:

```text
python herramientas/cifras_entregables.py --raiz <workspace> --salida docs/entrega/datos/cifras_entregables.json
python herramientas/construir_entrega.py todo
python herramientas/verificar_entregables.py
```

The builder needs `markdown`, `pypdf` and Playwright with Chromium. It does not train, read row-level data or submit anything. El constructor no entrena, no lee datos por fila y no envía nada.
