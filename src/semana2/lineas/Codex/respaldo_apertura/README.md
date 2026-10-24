# AI Hackathon IAA 2026

La carpeta conserva el trabajo preparatorio y separa los archivos activos del concurso por semana. [RUTAS_PROYECTO.json](RUTAS_PROYECTO.json) es el mapa de rutas relativo a esta raíz.

Desde el 19 de octubre de 2026 el trabajo nuevo de la primera semana se concentra en [Hackaton/Repositorio_IAA2026](Hackaton/Repositorio_IAA2026/README.md). Allí están el [panel de revisión](Hackaton/Repositorio_IAA2026/docs/panel_revision.html), el [informe de cinco páginas](Hackaton/Repositorio_IAA2026/docs/informe_semana1.pdf), el código, la receta S30/S22 y el seguimiento. Git y [GitHub privado](https://github.com/manoloriveros/iaa-hackathon-2026) ya están configurados. Los originales y corridas previas conservan sus rutas como evidencia; no se crean nuevas carpetas de trabajo separadas por asistente para esta semana.

| Ruta | Contenido y función |
| --- | --- |
| [Preparación](Preparación/README.md) | Entornos Python, código de ensayo, antecedentes y evidencia histórica |
| [Memoria general](Preparación/MEMORIA_PROYECTO.md) | Estado vigente, método de trabajo y cortes anteriores identificados |
| [Estado](Preparación/ESTADO_PROYECTO.json) y [decisiones](Preparación/DECISIONES.md) | Pendientes y decisiones persistentes |
| [Reglas operativas](Hackaton/REGLAS_2026.md) | Contrato del reto, rúbrica y ambigüedades conservadas |
| [Semana 1](<Hackaton/Semana 1/README.md>) | Acceso a los once Parquet originales de Datos |
| .agents/skills | Skills compartidos; permanecen en la raíz |

Desde PowerShell en C:/dev/Hakaton, para comprobar estructura, hashes y lectura completa de los datos:

```powershell
& '.\Preparación\.venv\Scripts\python.exe' '.\Preparación\scripts\validate_workspace_layout.py'
```

El validador usa PyArrow 26.0.0 instalado de forma aislada en Preparación/.cache/parquet-reader. Conserva un informe nuevo en Preparación/artifacts/verification. No entrena ni modifica los Parquet. El informe incluye la cobertura de la plantilla respecto de los tres test; no acredita calidad actuarial, etiquetas últimas o corrección de los cruces temporales.

Para usar los comandos del ensayo, entrar primero en Preparación:

```powershell
Set-Location -LiteralPath 'C:\dev\Hakaton\Preparación'
& '.\.venv\Scripts\python.exe' scripts/check_environment.py
```

El runner de ensayo de Preparación conserva su alcance histórico. Para el reto ya hay modelos y envíos puntuados: S30 es candidato principal (público 0,12996), S22 respaldo (0,12988). La reproducción completa y la revisión humana siguen pendientes; consultar el estado de entrega de la carpeta común. Las afirmaciones del corte inicial sobre ausencia de modelos o envíos describen el 16 de octubre.

El [análisis detallado de datos](<Hackaton/Semana 1/Analisis/README.md>) contiene el diccionario actuarial, gráficos y hallazgos de calidad de D30. La revisión encontró incidencias materiales; no equivale a aprobación para modelar.
