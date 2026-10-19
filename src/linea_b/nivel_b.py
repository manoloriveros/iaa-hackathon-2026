"""Regla de nivel s17 aplicada a corridas nuevas de la línea B, sin tocar mezcla3.py.

mezcla3.sin_referencia excluye de la referencia de nivel un conjunto fijo de corridas (NIVEL_INESTABLE_S17). Para las
corridas nuevas de esta línea, la misma regla (sin etiquetas) se calcula aquí: el total 2025 entre el total V24 de la
corrida, comparado con el del ancla del ramo (CAT_motor_4s, S12h_edif_md1000, S08h_hogar_F3s2); si se aparta más de un
1,5 %, la corrida queda fuera de la referencia de nivel. El resultado se guarda en WORK/nivel_inestable_b.json y se
añade al conjunto fijo. Importar `aplicar()` antes de usar mezcla3/robustez/publico_simulado.
"""
from __future__ import annotations

import json
import sys

import pandas as pd

import os as _os
from pathlib import Path as _Path
# código de la línea principal de Claude: carpeta hermana Modelos_claude en el repositorio, o la copia de la nube
_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
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
    """{ramo: [corridas]} -> {corrida: {"desvio": x, "fuera": bool}}; actualiza la caché."""
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
    """Parchea mezcla3.sin_referencia (y robustez si está importado) con las corridas inestables de la caché."""
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
