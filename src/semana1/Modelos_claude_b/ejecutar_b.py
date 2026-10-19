"""Ejecuta un script de la línea principal (robustez, publico_simulado, bootstrap_codex, influencia_reservas,
exportar_predicciones, comparar_codex, semestres) con la regla de nivel s17 extendida a las corridas B_ (nivel_b).
Uso: python3 ejecutar_b.py <modulo> <argumentos del script...>
Los argumentos con <spec>@... se inspeccionan para clasificar las corridas nuevas antes de parchear."""
import json
import os as _os
import runpy
import sys
from pathlib import Path as _Path

_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
sys.path.insert(0, str(_Path(__file__).resolve().parent))
import nivel_b  # noqa: E402

mod = sys.argv[1]
args = sys.argv[2:]
for a in args:
    cand = a.split("=", 1)[-1].split("@")[0]
    if cand.endswith(".json") and _Path(cand).exists():
        try:
            spec = json.loads(_Path(cand).read_text())
            if isinstance(spec, dict) and all(isinstance(v, list) for v in spec.values()):
                nivel_b.clasificar({line: [c[0] for c in comps] for line, comps in spec.items()})
        except Exception:
            pass
extra = nivel_b.aplicar()
import robustez  # noqa: E402
robustez.sin_referencia = nivel_b.mezcla3.sin_referencia
print("fuera de la referencia de nivel (corridas B):", sorted(extra), flush=True)
sys.argv = [mod + ".py"] + args
runpy.run_path(str(_Path(_MC) / f"{mod}.py"), run_name="__main__")
