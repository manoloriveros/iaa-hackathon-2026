"""Qué estadístico local de 2024 acompaña al orden del marcador público: candidatos puntuados con predicciones de 2024.

Para cada candidato puntuado del que hay predicción de 2024 (S04, S08, S09b, A_G, H, S21) calcula sobre las mismas filas:
D² completo, sin el 0,1 % y el 0,5 % superior de la pérdida, renivelado (factor Tweedie óptimo), por ramo y global,
concentración de las predicciones (desviación típica del log de la tasa) y nivel 2025 / nivel 2024, y los cruza con el
público. Son seis puntos: sirve para ver patrones, no para ajustar nada al marcador.
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

import os as _os
from pathlib import Path as _Path
# código de la línea principal de Claude: carpeta hermana Modelos_claude en el repositorio, o la copia de la nube
_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
from comun import LINES, WORK, d2  # noqa: E402
from mezcla3 import ftw, labels  # noqa: E402
from robustez import blend  # noqa: E402

C = "/mnt/user-data/uploads/Hakaton/Hackaton/Semana 1/Modelado_codex/nocturna_20261017_N01"
D76 = "/mnt/user-data/uploads/Hakaton/Preparación/artifacts/verification/improvement_D76"
PUB = {"S04": 0.12435, "S08": 0.12532, "S09b": 0.12889, "A_G": 0.12908, "H": 0.12886, "S21": 0.12874}
FORMA = {"motor": (1.09, 0.95), "buildings": (1.08, 1.14), "contents": (1.07, 1.0), "_nivel": "s17"}


def main():
    ag = pd.read_parquet(f"{C}/crossfit_meta_gam_guard/predictions_V24_crossfit.parquet", columns=["row_id", "T0", "meta_gam", "S09b"]).set_index("row_id")
    hh = pd.read_parquet(f"{C}/geometric_meta_nested/V24.parquet", columns=["row_id", "candidate"]).set_index("row_id")
    s8 = pd.read_parquet(f"{D76}/learned_predictions_V24.parquet", columns=["row_id", "stack"]).set_index("row_id")
    spec = json.load(open(WORK / "spec_s21.json"))
    rows = []
    allv = {}
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "e_ef_coste", "exposure"])
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        _, _, b24, _ = blend(spec, FORMA, line, ysel, y24, idx25, expos)
        s4 = pd.read_parquet(WORK / "S04b_lgbm_F0124_F3autos" / "v24.parquet"); s4 = s4[s4.line == line].set_index("row_id")["mu"]
        idx = y24.index
        y = y24.values
        assert np.allclose(ag.T0.reindex(idx).values, y, atol=0.01)
        e = expos[1]
        P = {"S04": s4.reindex(idx).values, "S08": s8["stack"].reindex(idx).values, "S09b": ag.S09b.reindex(idx).values,
             "A_G": ag.meta_gam.reindex(idx).values, "H": hh.candidate.reindex(idx).values, "S21": b24}
        for k, v in P.items():
            assert np.isfinite(v).all(), (line, k)
            allv.setdefault(k, []).append(v)
        allv.setdefault("y", []).append(y)
        for k, v in P.items():
            r = {"ramo": line, "cand": k, "publico": PUB[k], "d2": d2(y, v), "d2_reniv": d2(y, v * ftw(y, v)), "nivel": v.sum() / y.sum(), "sd_log_tasa": float(np.log(v / e).std())}
            for q in (0.999, 0.995, 0.99):
                keep = y <= np.quantile(y, q)
                r[f"d2_sin_{q}"] = d2(y[keep], v[keep]); r[f"d2_sin_{q}_reniv"] = d2(y[keep], v[keep] * ftw(y[keep], v[keep]))
            rows.append(r)
    y = np.concatenate(allv.pop("y"))
    for k, parts in allv.items():
        v = np.concatenate(parts)
        r = {"ramo": "global", "cand": k, "publico": PUB[k], "d2": d2(y, v), "d2_reniv": d2(y, v * ftw(y, v)), "nivel": v.sum() / y.sum(), "sd_log_tasa": np.nan}
        for q in (0.999, 0.995, 0.99):
            keep = y <= np.quantile(y, q)
            r[f"d2_sin_{q}"] = d2(y[keep], v[keep]); r[f"d2_sin_{q}_reniv"] = d2(y[keep], v[keep] * ftw(y[keep], v[keep]))
        rows.append(r)
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 250); pd.set_option("display.float_format", lambda x: f"{x:.5f}")
    for ramo, g in df.groupby("ramo", sort=False):
        print("\n==", ramo); print(g.drop(columns=["ramo"]).to_string(index=False))
    g = df[df.ramo == "global"].set_index("cand")
    print("\ncorrelaciones de rango (Spearman) con el público, global:")
    for c in [c for c in g.columns if c.startswith("d2")]:
        print(f"  {c:22s} {g[c].corr(g['publico'], method='spearman'):+.3f}   pearson {g[c].corr(g['publico']):+.3f}")
    df.to_csv(WORK / "publico_vs_local_b.csv", index=False)


if __name__ == "__main__":
    main()
