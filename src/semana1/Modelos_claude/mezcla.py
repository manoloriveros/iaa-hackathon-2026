"""Mezcla por ramo de dos estructuras (Tweedie acotado y frecuencia por peligro x severidad) y calibración al año siguiente.

Pesos por ramo fijados en la mitad de selección de V23. La mezcla se evalúa en V24 con las predicciones de cada
estructura entrenada en 2021-2023, y el factor de calibración al año siguiente se estima sobre la mezcla en los dos
pliegues (V23 selección y V24) y se aplica, con su media, a la predicción de 2025.
Uso: python3 mezcla.py <nombre> <pesos_json>
pesos_json: {"motor": 0.5, "buildings": 0.0, "contents": 0.2}  (peso de frecuencia-severidad)
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import BASE, LINES, WORK, d2, digest

TW_RUN = "S04b_lgbm_F0124_F3autos"     # Tweedie: autos con F3, hogar F0124 (reutilizado de S03)
FS_RUN = "FS_frecsev"                  # frecuencia-severidad: autos con F3, contenidos F0124
SEL_TW = {"motor": "total_F01234", "buildings": "total_F0124", "contents": "total_F0124"}
SEL_FS = "fs1"


def ftw(y, mu):
    return float((y / np.sqrt(mu)).sum() / np.sqrt(mu).sum())


def align(a, b):
    b = b.set_index("row_id").loc[a.row_id].reset_index()
    assert (a.row_id.values == b.row_id.values).all()
    return b


def main():
    name, wpath = sys.argv[1], sys.argv[2]
    w = json.loads(open(wpath).read()) if wpath.endswith(".json") else json.loads(wpath)
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    rep = {"weights_frecsev": w, "tweedie_run": TW_RUN, "frecsev_run": FS_RUN, "lines": {}}
    tw24 = pd.read_parquet(WORK / TW_RUN / "v24.parquet"); tw25 = pd.read_parquet(WORK / TW_RUN / "prediccion_2025.parquet")
    fs24 = pd.read_parquet(WORK / FS_RUN / "v24.parquet"); fs25 = pd.read_parquet(WORK / FS_RUN / "prediccion_2025.parquet")
    fssel = pd.read_parquet(WORK / f"sel_{SEL_FS}.parquet")
    y24_all, m24_raw, m24_cal, sel_y, sel_m = [], [], [], [], []
    pred_parts = []
    for line in LINES:
        wl = float(w.get(line, 0.0))
        a24 = tw24[tw24.line == line].reset_index(drop=True); a25 = tw25[tw25.line == line].reset_index(drop=True)
        asel = pd.read_parquet(WORK / f"sel_{SEL_TW[line]}.parquet"); asel = asel[asel.line == line].reset_index(drop=True)
        if wl > 0:
            b24 = align(a24, fs24[fs24.line == line]); b25 = align(a25, fs25[fs25.line == line]); bsel = align(asel, fssel[fssel.line == line])
            m24 = (1 - wl) * a24.mu.values + wl * b24.mu.values
            m25 = (1 - wl) * a25.prediction.values + wl * b25.prediction.values
            msel = (1 - wl) * asel.mu.values + wl * bsel.mu.values
        else:
            m24, m25, msel = a24.mu.values, a25.prediction.values, asel.mu.values
        f23, f24 = ftw(asel.y.values, msel), ftw(a24.y.values, m24)
        f = (f23 + f24) / 2
        rep["lines"][line] = {"w_frecsev": wl, "d2_sel_v23": round(d2(asel.y, msel), 5), "d2_v24_tweedie": round(d2(a24.y, a24.mu), 5),
                              "d2_v24_mezcla": round(d2(a24.y, m24), 5), "d2_v24_mezcla_con_f_v23": round(d2(a24.y, m24 * f23), 5),
                              "f_v23": round(f23, 4), "f_v24": round(f24, 4), "f_aplicado": round(f, 4),
                              "pred_2025_total_CU": round(float((m25 * f).sum()), 2)}
        print(line, rep["lines"][line], flush=True)
        y24_all.append(a24.y.values); m24_raw.append(m24); m24_cal.append(m24 * f23); sel_y.append(asel.y.values); sel_m.append(msel)
        pred_parts.append(pd.DataFrame({"row_id": a25.row_id.values, "line": line, "prediction": m25 * f}))
    y24 = np.concatenate(y24_all)
    rep["d2_v24_global_tweedie"] = round(d2(tw24.y, tw24.mu), 5)
    rep["d2_v24_global_mezcla"] = round(d2(y24, np.concatenate(m24_raw)), 5)
    rep["d2_v24_global_mezcla_con_f_v23"] = round(d2(y24, np.concatenate(m24_cal)), 5)
    rep["d2_sel_v23_global_mezcla"] = round(d2(np.concatenate(sel_y), np.concatenate(sel_m)), 5)
    rep["publico_esperado"] = {"formula": "0,0099 + 0,8644 x V24 (ajuste sobre S01, S03 y S04)",
                               "mezcla_con_calibracion": round(0.0099 + 0.8644 * rep["d2_v24_global_mezcla_con_f_v23"], 5)}
    pred = pd.concat(pred_parts, ignore_index=True)
    sample = pd.read_parquet(BASE / "Datos" / "sample_submission.parquet", columns=["row_id"])
    sub = sample.merge(pred[["row_id", "prediction"]], on="row_id", how="left", validate="one_to_one")
    assert len(sub) == 626639 and np.isfinite(sub.prediction).all() and (sub.prediction > 0).all()
    csv = out / f"{name}.csv"
    sub.to_csv(csv, index=False, float_format="%.6f")
    back = pd.read_csv(csv, dtype={"row_id": str})
    assert (back.row_id.values == sample.row_id.values).all()
    rep["file"] = {"path": str(csv), "sha256": digest(csv), "rows": 626639, "total_CU": round(float(back.prediction.sum()), 2),
                   "by_line_CU": {l: round(float(pred[pred.line == l].prediction.sum()), 2) for l in LINES}}
    pred.to_parquet(out / "prediccion_2025.parquet", index=False)
    (out / "resumen.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: v for k, v in rep.items() if k != "lines"}, indent=1))


if __name__ == "__main__":
    main()
