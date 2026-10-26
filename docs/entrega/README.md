# Final deliverables · Entregables finales

El informe conjunto actual está en [`privado/entrega_final/informe_dos_semanas.pdf`](../../privado/entrega_final/informe_dos_semanas.pdf), con cinco páginas totales y las veinte referencias comerciales. El PDF se conserva fuera de Git porque contiene sus primas por fila. Su [texto editable](informe_final/INFORME_ES.md), [figuras](informe_final/figuras/) y [trazabilidad](informe_final/README.md) están aquí. El [dashboard](panel_analisis.html) compara ambas semanas simultáneamente.

The Week 1 model deliverables use [`datos/cifras_entregables.json`](datos/cifras_entregables.json); the joint data analysis uses [`analisis/datos_panel.json`](analisis/datos_panel.json). The joint five-page report has its own [source manifest](informe_final/datos_informe.json). Versioned deliverables contain aggregates; the PDF with the twenty reference prices stays private. Las fuentes conservan sus rutas y SHA-256.

| File | What it is | Archivo |
| --- | --- | --- |
| [`../../privado/entrega_final/informe_dos_semanas.pdf`](../../privado/entrega_final/informe_dos_semanas.pdf) | Current joint report, five total pages, Spanish; local private file | Informe conjunto actual |
| [`report_en.pdf`](report_en.pdf) | Preserved Week 1 report with appendix | Informe previo de semana 1 en inglés |
| [`informe_es.pdf`](informe_es.pdf) | Preserved Spanish Week 1 report | Informe previo de semana 1 en español |
| [`informe/`](informe/) | Markdown sources of both reports | Fuentes Markdown del informe |
| [`panel_modelo.html`](panel_modelo.html) | Offline model dashboard, English or Spanish, light or dark; every chart has a table view | Panel del modelo sin conexión |
| [`panel_analisis.html`](panel_analisis.html) | Simultaneous comparison of both weeks: common years, paired bars, differences and export | Comparación conjunta de datos |
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

Los productores de datos y clima leen fuentes locales por fila y guardan la auditoría en privado. El constructor de figuras del anexo lee agregados. La verificación UI vigente se delega desde `verificar_panel_analisis.cjs` a `verificar_comparacion.cjs`, con Playwright y Chrome. Los recibos y capturas quedan en el corte privado del informe actual. Python para los datos requiere pandas, NumPy y PyArrow; figuras, Matplotlib; PDF, ReportLab, Pillow, pypdf, pdfplumber y pypdfium2. La [validación del agregado base](analisis/VALIDACION_PANEL.md) conserva su corte; la [edición comparativa](informe_final/README.md) registra los controles nuevos.

Para preparar el informe conjunto:

```text
python herramientas/informe_comparativo.py datos
python herramientas/informe_comparativo.py figuras
python herramientas/informe_comparativo.py pdf
python herramientas/compilar_paneles_analisis.py
node herramientas/verificar_panel_analisis.cjs
```

`datos` crea una corrida y coteja las veinte referencias con el CSV F3c ya guardado; no predice. Para una corrección de presentación se repiten solo figuras/PDF/compilación o UI según lo afectado. Las veinte referencias no se escriben en el manifiesto público ni en el dashboard. No se entrena, envía o selecciona una entrega mediante estos comandos.

Two sources of the 2025 level calibration come from their own tools, which read the original files and write aggregates only. Dos fuentes de la calibración del nivel de 2025 salen de herramientas propias, que leen los originales y solo escriben agregados:

```text
python herramientas/regenerar_s41.py --raiz <workspace>          # final submission S41: byte-identical rebuild and ten delivery checks
python herramientas/prima_escrita_por_anio.py --raiz <workspace>  # written premium per exposure year, 2021-2025
```
