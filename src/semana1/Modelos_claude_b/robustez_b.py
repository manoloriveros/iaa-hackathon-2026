"""robustez.py de la línea principal con la regla de nivel s17 extendida a las corridas nuevas (nivel_b.aplicar).

Uso: python3 robustez_b.py <salida.json> <ref>=<spec>[@<forma>[@s17]] <cand>=<spec>[@<forma>[@s17]] ...
"""
import json
import sys

import os as _os
from pathlib import Path as _Path
# código de la línea principal de Claude: carpeta hermana Modelos_claude en el repositorio, o la copia de la nube
_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
import nivel_b  # noqa: E402
import robustez  # noqa: E402

specs = [json.loads(open(a.split("=", 1)[1].split("@")[0]).read()) for a in sys.argv[2:]]
for s in specs:
    nivel_b.clasificar({line: [c[0] for c in comps] for line, comps in s.items()})
extra = nivel_b.aplicar()
print("fuera de la referencia de nivel (nuevas):", sorted(extra), flush=True)
robustez.main()
