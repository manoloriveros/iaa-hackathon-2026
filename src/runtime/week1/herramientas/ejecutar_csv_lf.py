"""Run final writers with process-local LF defaults in pandas.

The reference CSV uses LF; pandas otherwise defaults to os.linesep. This child
process changes the writer default without rewriting an already generated CSV.
"""
import os
import runpy
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
permitidos = {REPO / "src/modelos/mezcla3.py", REPO / "src/linea_b/mezcla3_b.py"}
script = Path(sys.argv[1]).resolve()
if script not in permitidos:
    raise SystemExit("El escritor no pertenece a los dos puntos de salida finales de la receta")
os.linesep = "\n"
sys.argv = [str(script)] + sys.argv[2:]
sys.path.insert(0, str(script.parent))
runpy.run_path(str(script), run_name="__main__")
