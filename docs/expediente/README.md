# Working record · Expediente de trabajo

This folder keeps a readable copy of the two records that show how the work was done: the shared forum where the AI work lines posted hypotheses, results and critiques, and the project's decision log. Both are exported by `herramientas/exportar_expediente.py` from the originals, which stay outside the repository and are never modified.

Esta carpeta conserva una copia legible de los dos registros que muestran cómo se hizo el trabajo: el foro común donde las líneas de IA publicaron hipótesis, resultados y críticas, y el registro de decisiones del proyecto. Ambos se exportan con `herramientas/exportar_expediente.py` desde los originales, que siguen fuera del repositorio y nunca se modifican.

| File | Contents | Contenido |
| --- | --- | --- |
| [`foro/FORO.md`](foro/FORO.md) | The full forum, each post with its real author, UTC time and identifier | El foro completo, cada aporte con su autor real, hora UTC e identificador |
| [`foro/indice.csv`](foro/indice.csv) | One row per post: author, identifier, time and subject | Una fila por aporte |
| [`decisiones/DECISIONES.md`](decisiones/DECISIONES.md) | The decision log, from the preparation stage to the final model | El registro de decisiones, desde la preparación hasta el modelo final |
| [`decisiones/indice.csv`](decisiones/indice.csv) | One row per heading | Una fila por encabezado |
| [`MANIFIESTO.json`](MANIFIESTO.json) | SHA-256 of sources and copies, masking rule and counts | Huellas, regla de enmascarado y recuentos |

The competition data are synthetic. Even so, identifiers of policies, customers, claims and addresses quoted in these records are replaced by their prefix and six characters of their SHA-256, so repeated mentions of the same case stay linked without showing the value. Private conversations are not included. Los datos del concurso son sintéticos; aun así, los identificadores citados se sustituyen por su prefijo y seis caracteres de su SHA-256, y no se incluyen conversaciones privadas.

These records are working material, written in Spanish by the participant and the AI work lines as the work happened. They are evidence of process, not part of the graded report.
