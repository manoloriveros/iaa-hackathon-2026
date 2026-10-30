"""Extend the main blend's s17 level rule to B_ runs through nivel_b.
Usage: python mezcla3_b.py <name> <spec_json> [--forma=...] [--nivel=s17] [--escribir]
"""
import json
import os as _os
import sys
from pathlib import Path as _Path

_MC = _os.environ.get("MODELOS_BASE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_base", _Path("/home/participant/mc")) if p.exists()), "/home/participant/mc")
sys.path.insert(0, _MC)
sys.path.insert(0, str(_Path(__file__).resolve().parent))
import nivel_b  # noqa: E402

spec = json.loads(open(sys.argv[2]).read())
nivel_b.clasificar({line: [c[0] for c in comps] for line, comps in spec.items()})
extra = nivel_b.aplicar()
print("fuera de la referencia de nivel (corridas B):", sorted(extra), flush=True)
nivel_b.mezcla3.main()
