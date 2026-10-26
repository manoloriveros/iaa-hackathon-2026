# Final deliverables · Entregables finales

The Week 1 model deliverables use [`datos/cifras_entregables.json`](datos/cifras_entregables.json). The joint data analysis added on 26 October uses [`analisis/datos_panel.json`](analisis/datos_panel.json). Both record the source paths and SHA-256 hashes. No deliverable contains row-level data. Los entregables del modelo de semana 1 y el análisis conjunto tienen sus propios agregados y fuentes identificadas; ningún entregable contiene datos por fila.

| File | What it is | Archivo |
| --- | --- | --- |
| [`report_en.pdf`](report_en.pdf) | Report: five graded pages and an appendix | Informe en inglés |
| [`informe_es.pdf`](informe_es.pdf) | Spanish copy of the report | Informe en español |
| [`informe/`](informe/) | Markdown sources of both reports | Fuentes Markdown del informe |
| [`panel_modelo.html`](panel_modelo.html) | Offline model dashboard, English or Spanish, light or dark; every chart has a table view | Panel del modelo sin conexión |
| [`panel_analisis.html`](panel_analisis.html) | Offline data dashboard for both weeks, with market/year/line filters and aggregate export | Análisis conjunto de datos |
| [`analisis/anexo_datos_dos_semanas.pdf`](analisis/anexo_datos_dos_semanas.pdf) | Four-page data appendix, with source checks | Anexo listo para acompañar el informe |
| [`analisis/TEXTO_PARA_INFORME.md`](analisis/TEXTO_PARA_INFORME.md) | Short passage and table for the joint five-page report | Texto breve para incorporar al informe |
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

Joint data analysis / Análisis de ambas semanas:

```text
python herramientas/construir_panel_analisis.py --raiz <workspace>
python herramientas/verificar_panel_analisis.py
python herramientas/complementar_clima_panel.py
python herramientas/preparar_anexo_analisis.py figuras
python herramientas/preparar_anexo_analisis.py pdf
python herramientas/compilar_paneles_analisis.py
node herramientas/verificar_panel_analisis.cjs
```

The first two commands read local row-level sources and write audit rows only under `privado/panel_analisis/`. The other builders read aggregates. The browser checker needs Playwright and Chrome (or `PANEL_BROWSER_CHANNEL`); its receipts and screenshots remain private. Python for the data checks needs pandas, NumPy and PyArrow; figures use Matplotlib; the PDF builder uses ReportLab, Pillow, pypdf, pdfplumber and pypdfium2. See [`analisis/VALIDACION_PANEL.md`](analisis/VALIDACION_PANEL.md) for the actual environments and results. No command trains or submits predictions. El anexo acompaña al informe; no reemplaza sus cinco páginas ni la selección final de la semana 2.

Two sources of the 2025 level calibration come from their own tools, which read the original files and write aggregates only. Dos fuentes de la calibración del nivel de 2025 salen de herramientas propias, que leen los originales y solo escriben agregados:

```text
python herramientas/regenerar_s41.py --raiz <workspace>          # final submission S41: byte-identical rebuild and ten delivery checks
python herramientas/prima_escrita_por_anio.py --raiz <workspace>  # written premium per exposure year, 2021-2025
```
