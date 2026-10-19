"""Convierte las predicciones del GAM por peligro de Codex (carpeta nocturna N01, solo lectura) en un componente de mezcla.

Codex entrena, por ramo, frecuencias Poisson por peligro con estructura aditiva y severidades gamma (columna gamma_1.0),
con modelos temporales: V23 entrena 2021-2022, V24 entrena 2021-2023 y producción 2021-2024 con exposición nominal.
Este script copia esas predicciones al formato de Claude (sel_GAMC_<ramo>.parquet, GAMC_<ramo>/v24.parquet y
GAMC_<ramo>/prediccion_2025.parquet), comprueba que las filas y el T0 coinciden con los cortes de Claude, guarda el
SHA-256 de cada fuente en GAMC_<ramo>/resumen.json e informa el D² del componente solo.
Uso: python3 importar_gam_codex.py <ramo> <ruta_V23> <ruta_V24> <ruta_PROD>
"""
from __future__ import annotations

import hashlib
import json
import sys

import numpy as np
import pandas as pd

from comun import WORK, d2
from mezcla3 import labels


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    line, p23, p24, p25 = sys.argv[1:5]
    col = "gamma_1.0"
    ysel, y24, idx25 = labels(line)
    a = pd.read_parquet(p23).set_index("row_id"); b = pd.read_parquet(p24).set_index("row_id"); c = pd.read_parquet(p25).set_index("row_id")
    s = a.reindex(ysel.index); v = b.reindex(y24.index); p = c[col].reindex(idx25)
    assert s[col].notna().all() and v[col].notna().all() and p.notna().all()
    assert np.allclose(s.T0.values, ysel.values, atol=0.01) and np.allclose(v.T0.values, y24.values, atol=0.01)
    if "V23" in s.columns:
        assert (s.V23 == "eval_seleccion").all()
    name = f"GAMC_{line}"
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"row_id": ysel.index, "line": line, "y": ysel.values, "mu": s[col].values}).to_parquet(WORK / f"sel_{name}.parquet", index=False)
    pd.DataFrame({"row_id": y24.index, "line": line, "y": y24.values, "mu": v[col].values}).to_parquet(out / "v24.parquet", index=False)
    pd.DataFrame({"row_id": idx25, "line": line, "prediction": p.values}).to_parquet(out / "prediccion_2025.parquet", index=False)
    rep = {"origen": "Codex, Modelado_codex/nocturna_20261017_N01 (solo lectura)", "columna": col,
           "fuentes": {"V23": {"ruta": p23, "sha256": sha(p23)}, "V24": {"ruta": p24, "sha256": sha(p24)}, "PROD": {"ruta": p25, "sha256": sha(p25)}},
           "d2_sel": round(d2(ysel.values, s[col].values), 5), "d2_v24": round(d2(y24.values, v[col].values), 5),
           "nivel_sel": round(float(s[col].sum() / ysel.sum()), 4), "nivel_v24": round(float(v[col].sum() / y24.sum()), 4),
           "pred_2025_total_CU": round(float(p.sum()), 2)}
    (out / "resumen.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps(rep, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
