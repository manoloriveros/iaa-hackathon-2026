"""Añade a WORK/feat_<ramo>.parquet el clima del propio año del periodo en la dirección, separado en dos piezas:
wx_<v>_media (media de la dirección en 2021-2025, el "clima" de la dirección) y wx_<v>_dev (desviación del año frente a
esa media, la "meteorología" del año). El archivo de clima trae 2025 completo, así que las dos piezas existen también
para las filas de 2025. La F2 vigente (media de años anteriores) no se toca.
Uso: python3 clima_anual.py [ramo ...]
"""
import sys

import pandas as pd

import os as _os
from pathlib import Path as _Path
# código de la línea principal de Claude: carpeta hermana Modelos_claude en el repositorio, o la copia de la nube
_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
from comun import BASE, LINES, WEATHER_VARS, WORK  # noqa: E402

w = pd.read_parquet(BASE / "Datos" / "weather.parquet")
m = w.groupby("address_id")[WEATHER_VARS].mean()
m.columns = [f"wx_{v}_media" for v in WEATHER_VARS]
w = w.merge(m.reset_index(), on="address_id")
for v in WEATHER_VARS:
    w[f"wx_{v}_dev"] = w[v] - w[f"wx_{v}_media"]
w = w[["address_id", "year"] + [c for c in w.columns if c.startswith("wx_")]]
for line in (sys.argv[1:] or LINES):
    df = pd.read_parquet(WORK / f"feat_{line}.parquet")
    df = df.drop(columns=[c for c in df.columns if c.startswith("wx_")])
    df = df.merge(w, on=["address_id", "year"], how="left", validate="many_to_one")
    df.to_parquet(WORK / f"feat_{line}.parquet", index=False)
    print(line, df.shape, df[[f"wx_{v}_dev" for v in WEATHER_VARS]].isna().mean().round(4).to_dict(), flush=True)
