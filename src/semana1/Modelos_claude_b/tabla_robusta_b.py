"""Tabla de estadísticos "de cuerpo" (recortados y renivelados) para mezclas de la línea de Claude, en V23 y V24.

Para cada candidato <nombre>=<spec>[@<forma>[@s17]] calcula por ramo y global: D² completo, D² sin el 0,5 % y el 1 %
superior de la pérdida renivelado (factor Tweedie óptimo en el subconjunto), y la desviación típica del log de la tasa.
Uso: python3 tabla_robusta_b.py <salida.csv> <nombre>=<spec>[@forma[@s17]] ...
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import os as _os
from pathlib import Path as _Path
# código de la línea principal de Claude: carpeta hermana Modelos_claude en el repositorio, o la copia de la nube
_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
import nivel_b  # noqa: E402
from comun import LINES, WORK, d2  # noqa: E402
from mezcla3 import ftw, labels  # noqa: E402
from robustez import blend, parse  # noqa: E402


def stats(y, v, e=None):
    r = {"d2": d2(y, v), "nivel": v.sum() / y.sum()}
    for q in (0.999, 0.995, 0.99):
        keep = y <= np.quantile(y, q)
        r[f"rt{q}"] = d2(y[keep], v[keep] * ftw(y[keep], v[keep]))
    if e is not None:
        r["sd_log_tasa"] = float(np.log(v / e).std())
    return r


def main():
    out = sys.argv[1]
    cands = [parse(a) for a in sys.argv[2:]]
    for _, spec, _ in cands:
        nivel_b.clasificar({line: [c[0] for c in comps] for line, comps in spec.items()})
    nivel_b.aplicar()
    import robustez
    robustez.sin_referencia = nivel_b.mezcla3.sin_referencia

    def blend_fb(spec, forma, line, ysel, y24, idx25, expos):
        """Como robustez.blend, pero si ningún componente puede fijar el nivel (componente solo e inestable), lo fijan todos."""
        from mezcla3 import component, evaluate
        raw = []
        for run, sel_name, w in spec[line]:
            s, v, p = component(run, sel_name, line)
            raw.append((run, w, s.reindex(ysel.index).values, v.reindex(y24.index).values, p.reindex(idx25).values))
        own = [(w, s, v, p) for run, w, s, v, p in raw if run not in robustez.sin_referencia({"nivel": forma.get("_nivel")})]
        if not own:
            own = [(w, s, v, p) for run, w, s, v, p in raw]
        wo = sum(o[0] for o in own)
        ref = [sum(o[0] * o[j].sum() for o in own) / wo for j in (1, 2, 3)]
        comps = [(s * ref[0] / s.sum(), v * ref[1] / v.sum(), p * ref[2] / p.sum()) for run, w, s, v, p in raw]
        return evaluate(comps, [c[2] for c in spec[line]], ysel.values, y24.values, 1.0, forma.get(line), expos)
    rows = []
    acc = {}
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "e_ef_coste", "exposure"])
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        for name, spec, forma in cands:
            _, bsel, b24, b25 = blend_fb(spec, forma, line, ysel, y24, idx25, expos)
            for fold, y, v, e in (("V23", ysel.values, bsel, expos[0]), ("V24", y24.values, b24, expos[1])):
                rows.append({"ramo": line, "corte": fold, "cand": name, **stats(y, v, e)})
                acc.setdefault((name, fold), {"y": [], "v": []}); acc[(name, fold)]["y"].append(y); acc[(name, fold)]["v"].append(v)
            rows.append({"ramo": line, "corte": "2025", "cand": name, "total": float(b25.sum())})
    for (name, fold), d in acc.items():
        rows.append({"ramo": "global", "corte": fold, "cand": name, **stats(np.concatenate(d["y"]), np.concatenate(d["v"]))})
    df = pd.DataFrame(rows)
    df.to_csv(WORK / out, index=False)
    pd.set_option("display.width", 250); pd.set_option("display.float_format", lambda x: f"{x:.5f}")
    for (ramo, corte), g in df[df.corte != "2025"].groupby(["ramo", "corte"], sort=False):
        print(f"\n== {ramo} {corte}"); print(g.drop(columns=["ramo", "corte", "total"]).to_string(index=False))
    print("\n== totales 2025"); print(df[df.corte == "2025"].pivot(index="cand", columns="ramo", values="total").to_string())


if __name__ == "__main__":
    main()
