"""Combinador por peligro de dos motores de frecuencia (CatBoost CFS y aditivo FSAP) con la misma severidad GLM y el
mismo nivel anual de severidad, en lugar de mezclar sus totales por ramo con un solo peso.

Para cada peligro, el peso del motor CatBoost w_p se elige en V23 selección minimizando la devianza Tweedie del coste del
peligro (y_p) en una rejilla de 0 a 1 en pasos de 0,1 y se confirma en V24 (se informa el peso que V24 habría elegido,
sin usarlo). Los peligros con menos de MIN_SIN siniestros en V23 selección usan el peso global del ramo (el que minimiza
la devianza del total). Escribe WORK/<salida>/ con el formato de las demás corridas (sel, v24, prediccion_2025,
resumen con pesos por peligro) para usarlo en mezcla3 como un componente.
Uso: python3 combinar_peligros_b.py <ramo> <salida> --cfs_v23=.. --cfs_v24=c1[,c2] --cfs_prod=c1[,c2] --fsa_v23=.. --fsa_v24=.. --fsa_prod=.. [--regla=pooled|ultimo|tendencia|mixto] [--peso_fijo=0.5]
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
from comun import PERILS, WORK, d2, deviance  # noqa: E402
from partes_b import marco, mascaras, partes_por_peligro  # noqa: E402

MIN_SIN = 300
GRID = np.round(np.arange(0.0, 1.0001, 0.1), 2)


def main():
    line, name = sys.argv[1:3]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[3:] if a.startswith("--"))
    regla = opts.get("regla", "pooled")
    df = marco(line)
    cfs, info_c = partes_por_peligro(df, line, opts["cfs_v23"], opts["cfs_v24"].split(","), opts["cfs_prod"].split(","), regla)
    fsa, info_f = partes_por_peligro(df, line, opts["fsa_v23"], opts["fsa_v24"].split(","), opts["fsa_prod"].split(","), regla)
    masks = mascaras(df)
    t0 = df["T0"].fillna(0).values
    rep = {"line": line, "regla": regla, "opts": opts, "perils": {}}
    # peso global del ramo en V23 (total)
    evm = masks["V23"][1]
    y = t0[evm]
    totc = sum(cfs["V23"].values()); totf = sum(fsa["V23"].values())
    dev_g = {float(w): deviance(y, w * totc + (1 - w) * totf).sum() for w in GRID}
    w_global = min(dev_g, key=dev_g.get)
    rep["peso_global_v23"] = w_global
    pesos = {}
    for p in PERILS[line]:
        yp = df[f"y_{p}"].fillna(0).values
        res = {}
        for fold in ("V23", "V24"):
            m = masks[fold][1]
            d = {float(w): deviance(yp[m], w * cfs[fold][p] + (1 - w) * fsa[fold][p]).sum() for w in GRID}
            null = deviance(yp[m], np.full(m.sum(), yp[m].mean())).sum()
            res[fold] = {"mejor": min(d, key=d.get), "d2_por_peso": {str(w): round(1 - v / null, 5) for w, v in d.items()}}
        n_sel = int((df[f"n_{p}"].fillna(0).values[masks["V23"][1]] > 0).sum())
        w = res["V23"]["mejor"] if n_sel >= MIN_SIN else w_global
        if "peso_fijo" in opts:
            w = float(opts["peso_fijo"])
        pesos[p] = w
        rep["perils"][p] = {"peso_cfs": w, "siniestros_sel": n_sel, "mejor_v23": res["V23"]["mejor"], "mejor_v24": res["V24"]["mejor"],
                            "d2_v23_por_peso": res["V23"]["d2_por_peso"], "d2_v24_por_peso": res["V24"]["d2_por_peso"],
                            "nivel_cfs": info_c[p], "nivel_fsa": info_f[p]}
        print(line, p, "peso CFS", w, "(V23", res["V23"]["mejor"], "V24", res["V24"]["mejor"], "n_sel", n_sel, ")", flush=True)
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    for fold, (trm, evm) in masks.items():
        mu = sum(pesos[p] * cfs[fold][p] + (1 - pesos[p]) * fsa[fold][p] for p in PERILS[line])
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
    # referencias: cada motor solo, con la misma severidad y nivel
    for tag, src in (("cfs_solo", cfs), ("fsa_solo", fsa)):
        rep[tag] = {fold: round(d2(t0[masks[fold][1]], sum(src[fold].values())), 5) for fold in ("V23", "V24")}
    (out / "resumen.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in rep.items() if k not in ("perils", "opts")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
