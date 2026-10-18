"""Mezcla entre la línea de Claude (ensamble por ramo, spec de mezcla2) y el S08 de Codex (stack D76).

Las dos líneas se construyeron por separado (variables, tratamiento de desarrollo y modelos distintos), así que su
promedio puede reducir la varianza de la predicción. Para no deformar las relatividades, antes de mezclar se iguala el
total de la predicción de Codex al de Claude en las mismas filas (solo predicciones, sin usar la etiqueta). Luego
mu = w x Claude + (1 - w) x Codex y el factor de calibración se estima como en mezcla2 (V23 selección y V24, media
para 2025). Informa D² por ramo y global en V23 selección y en V24 (con el factor de V23) para una rejilla de w.
Uso: python3 mezcla_codex.py <nombre> <spec_json> [w_motor,w_buildings,w_contents]
Con w explícitos escribe el CSV de envío en WORK/<nombre>/.
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import BASE, LINES, WORK, d2, digest

CODEX = BASE.parent.parent / "Preparación" / "artifacts" / "verification" / "improvement_D76"
GRID = [1.0, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.0]


def ftw(y, mu):
    return float((y / np.sqrt(mu)).sum() / np.sqrt(mu).sum())


def claude_blend(spec, line):
    comps = spec[line]
    wsum = sum(c[2] for c in comps)
    m24 = m25 = msel = None
    for run, sel_name, w in comps:
        w = w / wsum
        v = pd.read_parquet(WORK / run / "v24.parquet"); v = v[v.line == line].set_index("row_id")
        p = pd.read_parquet(WORK / run / "prediccion_2025.parquet"); p = p[p.line == line].set_index("row_id")
        s = pd.read_parquet(WORK / f"sel_{sel_name}.parquet"); s = s[s.line == line].set_index("row_id")
        if m24 is None:
            m24 = v[["y"]].assign(mu=0.0); m25 = p[[]].assign(prediction=0.0); msel = s[["y"]].assign(mu=0.0)
        m24["mu"] += w * v.mu.reindex(m24.index).values
        m25["prediction"] += w * p.prediction.reindex(m25.index).values
        msel["mu"] += w * s.mu.reindex(msel.index).values
    return m24, msel, m25


def main():
    name, spec_path = sys.argv[1], sys.argv[2]
    wfix = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None
    spec = json.loads(open(spec_path).read())
    root = Path_codex()
    c24 = pd.read_parquet(root / "learned_predictions_V24.parquet", columns=["row_id", "line", "T0", "stack"]).set_index("row_id")
    c23 = pd.read_parquet(root / "learned_fit_V23.parquet", columns=["row_id", "line", "V23", "T0", "stack"]).set_index("row_id")
    c25 = pd.read_parquet(root / "learned_predictions_PROD.parquet", columns=["row_id", "line", "stack"]).set_index("row_id")
    rep = {"spec": spec, "lines": {}, "grid": {}}
    store = {}
    for line in LINES:
        m24, msel, m25 = claude_blend(spec, line)
        a24 = c24["stack"].reindex(m24.index).values
        asel = c23["stack"].reindex(msel.index).values
        a25 = c25["stack"].reindex(m25.index).values
        assert np.isfinite(a24).all() and np.isfinite(asel).all() and np.isfinite(a25).all(), line
        assert np.allclose(c24.T0.reindex(m24.index).fillna(0).values, m24.y.values), "T0 distinto en V24"
        flag = c23.V23.reindex(msel.index)
        rep["lines"][line] = {"filas_sel_en_codex_seleccion": round(float((flag == "eval_seleccion").mean()), 4),
                              "nivel_codex_sobre_claude_v24": round(float(a24.sum() / m24.mu.sum()), 4),
                              "nivel_codex_sobre_claude_2025": round(float(a25.sum() / m25.prediction.sum()), 4),
                              "corr_log_v24": round(float(np.corrcoef(np.log(a24), np.log(m24.mu.values))[0, 1]), 4)}
        # igualar niveles con predicciones solamente
        a24 = a24 * m24.mu.sum() / a24.sum(); asel = asel * msel.mu.sum() / asel.sum(); a25n = a25 * m25.prediction.sum() / a25.sum()
        store[line] = (m24, msel, m25, a24, asel, a25n)
        res = {}
        for w in GRID:
            b24 = w * m24.mu.values + (1 - w) * a24
            bsel = w * msel.mu.values + (1 - w) * asel
            f23 = ftw(msel.y.values, bsel)
            res[w] = {"d2_sel": round(d2(msel.y.values, bsel), 5), "d2_v24_f23": round(d2(m24.y.values, b24 * f23), 5), "f23": round(f23, 4),
                      "f24": round(ftw(m24.y.values, b24), 4)}
        rep["grid"][line] = res
        print(line, json.dumps(rep["lines"][line]), flush=True)
        for w, r in res.items():
            print("  w_claude", w, r, flush=True)
    # global por w común
    for w in GRID:
        ys24, mus24, yssel, mussel = [], [], [], []
        for line in LINES:
            m24, msel, m25, a24, asel, a25n = store[line]
            b24 = w * m24.mu.values + (1 - w) * a24; bsel = w * msel.mu.values + (1 - w) * asel
            f23 = ftw(msel.y.values, bsel)
            ys24.append(m24.y.values); mus24.append(b24 * f23); yssel.append(msel.y.values); mussel.append(bsel)
        g24 = d2(np.concatenate(ys24), np.concatenate(mus24)); gsel = d2(np.concatenate(yssel), np.concatenate(mussel))
        rep.setdefault("global", {})[w] = {"d2_sel": round(gsel, 5), "d2_v24_f23": round(g24, 5), "publico_esperado": round(0.0099 + 0.8644 * g24, 5)}
        print("global w_claude", w, rep["global"][w], flush=True)
    if wfix:
        preds, ys24, mus24 = [], [], []
        rep["final"] = {}
        for line, w in zip(LINES, wfix):
            m24, msel, m25, a24, asel, a25n = store[line]
            b24 = w * m24.mu.values + (1 - w) * a24; bsel = w * msel.mu.values + (1 - w) * asel
            f23 = ftw(msel.y.values, bsel); f24 = ftw(m24.y.values, b24); f = (f23 + f24) / 2
            # las predicciones 2025 de los componentes de Claude son brutas (sin factor); el factor de la mezcla se aplica aquí,
            # y el de Claude solo se informa como referencia
            fc = (ftw(msel.y.values, msel.mu.values) + ftw(m24.y.values, m24.mu.values)) / 2
            b25 = (w * m25.prediction.values + (1 - w) * a25n) * f
            preds.append(pd.DataFrame({"row_id": m25.index.values, "line": line, "prediction": b25}))
            ys24.append(m24.y.values); mus24.append(b24 * f23)
            rep["final"][line] = {"w_claude": w, "f_mezcla": round(f, 4), "f_claude": round(fc, 4), "total_2025": round(float(b25.sum()), 2),
                                  "d2_v24_f23": round(d2(m24.y.values, b24 * f23), 5), "d2_sel": round(d2(msel.y.values, bsel), 5)}
        rep["final"]["global_v24_f23"] = round(d2(np.concatenate(ys24), np.concatenate(mus24)), 5)
        rep["final"]["publico_esperado"] = round(0.0099 + 0.8644 * rep["final"]["global_v24_f23"], 5)
        pred = pd.concat(preds, ignore_index=True)
        sample = pd.read_parquet(BASE / "Datos" / "sample_submission.parquet", columns=["row_id"])
        sub = sample.merge(pred[["row_id", "prediction"]], on="row_id", how="left", validate="one_to_one")
        assert len(sub) == 626639 and np.isfinite(sub.prediction).all() and (sub.prediction > 0).all()
        out = WORK / name
        out.mkdir(parents=True, exist_ok=True)
        csv = out / f"{name}.csv"
        sub.to_csv(csv, index=False, float_format="%.6f")
        back = pd.read_csv(csv, dtype={"row_id": str})
        assert (back.row_id.values == sample.row_id.values).all()
        rep["file"] = {"path": str(csv), "sha256": digest(csv), "rows": 626639, "total_CU": round(float(back.prediction.sum()), 2),
                       "by_line_CU": {l: round(float(pred[pred.line == l].prediction.sum()), 2) for l in LINES}}
        pred.to_parquet(out / "prediccion_2025.parquet", index=False)
        print(json.dumps(rep["final"], indent=1), json.dumps(rep["file"], indent=1), flush=True)
        (out / "resumen.json").write_text(json.dumps(rep, indent=1, default=str))
    else:
        (WORK / f"mezcla_codex_{name}.json").write_text(json.dumps(rep, indent=1, default=str))


def Path_codex():
    from pathlib import Path
    p = Path("/mnt/user-data/uploads/Hakaton/Preparación/artifacts/verification/improvement_D76")
    return p if p.exists() else CODEX


if __name__ == "__main__":
    main()
