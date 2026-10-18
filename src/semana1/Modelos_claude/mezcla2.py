"""Ensamble por ramo de varias corridas con pesos fijos y calibración al año siguiente.

Cada componente aporta v24.parquet y prediccion_2025.parquet (WORK/<corrida>/) y, si existe, sus predicciones de la
mitad de selección de V23 (WORK/sel_<nombre>.parquet). El factor de calibración se estima sobre la mezcla en V23 y en
V24 (media de los dos; solo V24 si falta V23) y se aplica a 2025. Informa el D² de V24 de cada componente, de la mezcla
y de la mezcla con el factor de V23, y el público esperado con la escala ajustada sobre los envíos.
Uso: python3 mezcla2.py <nombre> <spec_json>
spec: {"motor": [["S04b_lgbm_F0124_F3autos", "total_F01234", 0.3], ["FS_frecsev", "fs1", 0.4], ...], "buildings": [...], ...}
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import BASE, LINES, WORK, d2, digest


def ftw(y, mu):
    return float((y / np.sqrt(mu)).sum() / np.sqrt(mu).sum())


def main():
    name, spec_path = sys.argv[1], sys.argv[2]
    spec = json.loads(open(spec_path).read())
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    rep = {"spec": spec, "lines": {}}
    y24s, m24s, m24c, preds = [], [], [], []
    for line in LINES:
        comps = spec[line]
        wsum = sum(c[2] for c in comps)
        ref24 = None
        m24 = m25 = msel = None
        ysel = ysel_ids = None
        comp_rep = {}
        have_sel = True
        for run, sel_name, w in comps:
            w = w / wsum
            v = pd.read_parquet(WORK / run / "v24.parquet"); v = v[v.line == line]
            p = pd.read_parquet(WORK / run / "prediccion_2025.parquet"); p = p[p.line == line]
            if ref24 is None:
                ref24 = v[["row_id", "y"]].reset_index(drop=True); ref25 = p[["row_id"]].reset_index(drop=True)
                m24 = np.zeros(len(ref24)); m25 = np.zeros(len(ref25))
            v = v.set_index("row_id").loc[ref24.row_id]; p = p.set_index("row_id").loc[ref25.row_id]
            m24 += w * v.mu.values; m25 += w * p.prediction.values
            comp_rep[run] = {"w": round(w, 4), "d2_v24": round(d2(ref24.y, v.mu.values), 5)}
            sp = WORK / f"sel_{sel_name}.parquet" if sel_name else None
            if sp is not None and sp.exists():
                s = pd.read_parquet(sp); s = s[s.line == line] if "line" in s.columns else s
                if ysel is None:
                    ysel_ids = s.row_id.values; ysel = s.y.values; msel = np.zeros(len(s))
                s = s.set_index("row_id").loc[ysel_ids]
                msel += w * s.mu.values
            else:
                have_sel = False
        f24 = ftw(ref24.y.values, m24)
        f23 = ftw(ysel, msel) if (have_sel and msel is not None) else None
        f = (f23 + f24) / 2 if f23 is not None else f24
        rep["lines"][line] = {"componentes": comp_rep, "d2_v24_mezcla": round(d2(ref24.y, m24), 5),
                              "d2_v24_mezcla_con_f_v23": round(d2(ref24.y, m24 * f23), 5) if f23 else None,
                              "d2_sel_v23_mezcla": round(d2(ysel, msel), 5) if (have_sel and msel is not None) else None,
                              "f_v23": round(f23, 4) if f23 else None, "f_v24": round(f24, 4), "f_aplicado": round(f, 4),
                              "pred_2025_tasa_CU": None}
        y24s.append(ref24.y.values); m24s.append(m24); m24c.append(m24 * (f23 if f23 else 1.0))
        preds.append(pd.DataFrame({"row_id": ref25.row_id.values, "line": line, "prediction": m25 * f}))
        print(line, json.dumps(rep["lines"][line], ensure_ascii=False), flush=True)
    y24 = np.concatenate(y24s)
    rep["d2_v24_global_mezcla"] = round(d2(y24, np.concatenate(m24s)), 5)
    rep["d2_v24_global_mezcla_con_f_v23"] = round(d2(y24, np.concatenate(m24c)), 5)
    rep["publico_esperado"] = round(0.0099 + 0.8644 * rep["d2_v24_global_mezcla_con_f_v23"], 5)
    pred = pd.concat(preds, ignore_index=True)
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
    (out / "resumen.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in rep.items() if k not in ("lines", "spec")}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
