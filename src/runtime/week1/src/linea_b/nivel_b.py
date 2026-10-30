"""Apply the existing unlabeled s17 stability rule to additional line-B runs.

Compare each run's 2025/V24 total ratio with its frozen line anchor. Exclude
deviations above 1.5% from the level reference, cache the result in
WORK/nivel_inestable_b.json and extend the fixed exclusion set. Call aplicar()
before using mezcla3, robustez or publico_simulado.
"""
from __future__ import annotations

import json
import sys

import pandas as pd

import os as _os
from pathlib import Path as _Path
# Resolve the main model source directory from runtime bindings or a sibling checkout.
_MC = _os.environ.get("MODELOS_BASE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_base", _Path("/home/participant/mc")) if p.exists()), "/home/participant/mc")
sys.path.insert(0, _MC)
import mezcla3  # noqa: E402
from comun import WORK  # noqa: E402

ANCLA = {"motor": "CAT_motor_4s", "buildings": "S12h_edif_md1000", "contents": "S08h_hogar_F3s2"}
UMBRAL = 0.015
CACHE = WORK / "nivel_inestable_b.json"


def razon(run, line):
    v = pd.read_parquet(WORK / run / "v24.parquet"); v = v[v.line == line]["mu"].sum()
    p = pd.read_parquet(WORK / run / "prediccion_2025.parquet"); p = p[p.line == line]["prediction"].sum()
    return float(p / v)


def clasificar(runs_por_ramo: dict) -> dict:
    """Map {line: [runs]} to cached {run: {desvio: value, fuera: boolean}} decisions."""
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    for line, runs in runs_por_ramo.items():
        ra = razon(ANCLA[line], line)
        for run in runs:
            if run in cache or run in mezcla3.NIVEL_INESTABLE_S17 or run in mezcla3.EXTERNOS or run == ANCLA[line]:
                continue
            d = razon(run, line) / ra - 1.0
            cache[run] = {"ramo": line, "desvio_2025_v24_frente_ancla": round(d, 5), "fuera": bool(abs(d) > UMBRAL)}
    CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
    return cache


def aplicar(spec: dict | None = None):
    """Apply cached unstable-run exclusions to mezcla3 and, when imported, robustez."""
    if spec is not None:
        clasificar({line: [c[0] for c in comps] for line, comps in spec.items()})
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    extra = {run for run, v in cache.items() if v["fuera"]}
    base = mezcla3.sin_referencia

    def patched(opts):
        s = base(opts)
        return (s | extra) if opts.get("nivel") == "s17" else s

    mezcla3.sin_referencia = patched
    try:
        import robustez
        robustez.sin_referencia = patched
    except ImportError:
        pass
    return extra
