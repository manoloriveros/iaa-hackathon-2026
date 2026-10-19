"""Arranca los escritores finales sin cambiar sus fuentes, con LF en pandas.

Pandas toma os.linesep como terminador por defecto; el CSV de referencia es LF.
El cambio vive solo en este proceso hijo. No se modifica un CSV ya producido.
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
