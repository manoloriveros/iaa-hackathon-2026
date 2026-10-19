"""Calibración por segmentos de una mezcla exportada (predicciones_v23_v24_<cand>.parquet de exportar_predicciones).

Para cada segmentación (obra nueva, periodo corto, canal, forma de pago, región, exposición, prima relativa,
antigüedad del cliente...) calcula el factor de renivelado ftw = Σ(y/√μ)/Σ√μ por segmento en V23 y en V24, y mide
en V24 el D² al aplicar los factores de V23 (normalizados para no cambiar el total del ramo). Un segmento con el
mismo signo en los dos cortes y ganancia en V24 es una miscalibración estable; lo demás es ruido.
Uso: python3 calibracion_segmentos_b.py <cand> [--q=0.999]
"""
from __future__ import annotations

import json
import os as _os
import sys
from pathlib import Path as _Path

import numpy as np
import pandas as pd

_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
from comun import WORK, d2  # noqa: E402
from mezcla3 import ftw  # noqa: E402

EXP = _Path(__file__).resolve().parent / "experimentos"
SEGS = {
    "motor": ["new_business", "periodo_corto", "channel", "payment_method", "region", "cover_type", "vehicle_use", "urban_density", "q_exposure", "q_prem_rel", "q_renewal", "q_vage", "q_driver_age", "semestre"],
    "buildings": ["new_business", "periodo_corto", "channel", "payment_method", "region", "property_type", "urban_density", "q_exposure", "q_prem_rel", "q_renewal", "q_sum_insured", "semestre"],
    "contents": ["new_business", "periodo_corto", "channel", "payment_method", "region", "property_type", "urban_density", "q_exposure", "q_prem_rel", "q_renewal", "q_sum_insured", "semestre"],
}


def segmentos(fe, line):
    out = pd.DataFrame(index=fe.index)
    for c in SEGS[line]:
        if c.startswith("q_"):
            base = {"q_exposure": "exposure", "q_prem_rel": "prem_rel", "q_renewal": "renewal_count", "q_vage": "vehicle_age", "q_driver_age": "driver_age", "q_sum_insured": "sum_insured"}[c]
            v = fe[base].astype(float)
            if base == "renewal_count":
                out[c] = pd.cut(v.fillna(0), [-1, 0, 1, 3, 6, 1e9], labels=["0", "1", "2-3", "4-6", "7+"]).astype("string").fillna("NA").astype(str)
            elif base == "exposure":
                out[c] = pd.cut(v, [0, 0.26, 0.51, 0.76, 0.999, 1.01], labels=["<=q1", "q2", "q3", "q4", "1"]).astype("string").fillna("NA").astype(str)
            else:
                out[c] = pd.qcut(v.rank(method="first"), 5, labels=["d1", "d2", "d3", "d4", "d5"]).astype("string").fillna("NA").astype(str)
        elif c == "semestre":
            out[c] = np.where(fe.mes_inicio.astype(float) <= 6, "H1", "H2")
        else:
            out[c] = fe[c].astype("string").fillna("NA").astype(str)
    return out


def main():
    cand = sys.argv[1]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[2:] if a.startswith("--"))
    q = float(opts.get("q", 0.999))
    src = next(p for p in (EXP / f"predicciones_v23_v24_{cand}.parquet", WORK / f"predicciones_v23_v24_{cand}.parquet") if p.exists())
    pr = pd.read_parquet(src)
    pr["row_id"] = pr.row_id.astype(str)
    res = {}
    for line in ("motor", "buildings", "contents"):
        cols = ["row_id", "exposure", "prem_rel", "renewal_count", "mes_inicio", "new_business", "periodo_corto", "channel", "payment_method", "region", "urban_density"]
        cols += {"motor": ["cover_type", "vehicle_use", "vehicle_age", "driver_age"], "buildings": ["property_type", "sum_insured"], "contents": ["property_type", "sum_insured"]}[line]
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=cols)
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        sg = segmentos(fe, line)
        d = {}
        for corte in ("V23", "V24"):
            p = pr[(pr.line == line) & (pr.corte == corte)]
            d[corte] = (p.y_T0.values, p.prediction.values, sg.reindex(p.row_id.values))
        res[line] = {}
        for c in SEGS[line]:
            y1, m1, s1 = d["V23"][0], d["V23"][1], d["V23"][2][c].values
            y2, m2, s2 = d["V24"][0], d["V24"][1], d["V24"][2][c].values
            f1 = {g: float(ftw(y1[s1 == g], m1[s1 == g])) for g in np.unique(s1)}
            f2 = {g: float(ftw(y2[s2 == g], m2[s2 == g])) for g in np.unique(s2)}
            # factores de V23 aplicados a V24, normalizados al total del ramo
            fac = np.array([f1.get(g, 1.0) for g in s2]); fac = fac * m2.sum() / (m2 * fac).sum()
            # robustez: factores de V23 sin el q superior de pérdidas
            k1 = y1 <= np.quantile(y1, q)
            f1t = {g: float(ftw(y1[k1 & (s1 == g)], m1[k1 & (s1 == g)])) for g in np.unique(s1)}
            fact = np.array([f1t.get(g, 1.0) for g in s2]); fact = fact * m2.sum() / (m2 * fact).sum()
            # mitad de la corrección (contracción 0,5)
            fach = np.sqrt(fac)
            fach = fach * m2.sum() / (m2 * fach).sum()
            base = d2(y2, m2)
            tam = {g: int((s2 == g).sum()) for g in np.unique(s2)}
            res[line][c] = {"n_seg": len(f2), "factores": {str(g): [round(f1.get(g, np.nan), 4), round(f2.get(g, np.nan), 4), tam.get(g, 0)] for g in sorted(set(f1) | set(f2), key=str) if tam.get(g, 0) >= 2000},
                            "d2_v24_base": round(base, 5), "gan_v24_fact_v23": round(d2(y2, m2 * fac) - base, 6),
                            "gan_v24_fact_v23_sin_top": round(d2(y2, m2 * fact) - base, 6), "gan_v24_mitad": round(d2(y2, m2 * fach) - base, 6),
                            "gan_v24_oraculo": round(d2(y2, m2 * np.array([f2[g] for g in s2]) * m2.sum() / (m2 * np.array([f2[g] for g in s2])).sum()) - base, 6)}
            print(line, c, json.dumps({k: v for k, v in res[line][c].items() if k != "factores"}), flush=True)
            for g, v in res[line][c]["factores"].items():
                print("    ", g, v, flush=True)
    (EXP / f"calibracion_segmentos_{cand}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
