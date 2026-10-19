"""Componente de frecuencia por peligro con severidad GLM y nivel anual, montado desde partes guardadas, con la opción de
sustituir las partes de algunos peligros por las de otra corrida (por ejemplo, escape de agua con el clima del año).
Uso: python3 componente_partes_b.py <ramo> <salida> --v23=.. --v24=c1[,c2] --prod=c1[,c2] [--regla=pooled|tendencia] [--sustituir=p:run[,p:run]]
La corrida sustituta debe tener v23_<p>.npz, v24_<p>.npy y prod_<p>.npy (formato cat_frecsev.py / frec_peligro_b.py).
"""
import json
import sys

import pandas as pd

import os as _os
from pathlib import Path as _Path
# código de la línea principal de Claude: carpeta hermana Modelos_claude en el repositorio, o la copia de la nube
_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
from comun import PERILS, WORK, d2  # noqa: E402
from partes_b import marco, mascaras, partes_por_peligro  # noqa: E402

line, name = sys.argv[1:3]
opts = dict(a[2:].split("=", 1) for a in sys.argv[3:] if a.startswith("--"))
sust = {}
for kv in opts.get("sustituir", "").split(","):
    if kv:
        p, run = kv.split(":")
        sust[p] = (run, [run], [run])
df = marco(line)
parts, info = partes_por_peligro(df, line, opts["v23"], opts["v24"].split(","), opts["prod"].split(","), opts.get("regla", "pooled"), sust)
masks = mascaras(df)
t0 = df["T0"].fillna(0).values
out = WORK / name
out.mkdir(parents=True, exist_ok=True)
rep = {"line": line, "opts": opts, "perils": info}
for fold, (trm, evm) in masks.items():
    mu = sum(parts[fold].values())
    ids = df.row_id.values[evm]
    if fold == "V23":
        rep["d2_sel"] = round(d2(t0[evm], mu), 5)
        pd.DataFrame({"row_id": ids, "line": line, "y": t0[evm], "mu": mu}).to_parquet(WORK / f"sel_{name}.parquet", index=False)
    elif fold == "V24":
        rep["d2_v24"] = round(d2(t0[evm], mu), 5)
        pd.DataFrame({"row_id": ids, "line": line, "y": t0[evm], "mu": mu}).to_parquet(out / "v24.parquet", index=False)
    else:
        rep["pred_2025_total_CU"] = round(float(mu.sum()), 2)
        pd.DataFrame({"row_id": ids, "line": line, "prediction": mu}).to_parquet(out / "prediccion_2025.parquet", index=False)
    rep[f"d2_peligros_{fold}"] = {p: round(d2(df[f"y_{p}"].fillna(0).values[evm], parts[fold][p]), 5) for p in PERILS[line]} if fold != "PROD" else None
(out / "resumen.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
print(json.dumps({k: v for k, v in rep.items() if k not in ("perils", "opts")}, ensure_ascii=False), flush=True)
