"""Rejilla de pesos por ramo con un objetivo de cuerpo: D² sin el 0,5 % superior renivelado (rt0.995) y D² completo.

Recorre el símplex de pesos (paso 0,1) de los componentes de la especificación y, para cada combinación y cada forma
propuesta, calcula en V23 selección y V24: D² completo y rt0.995 (y rt0.99). Informa la frontera de Pareto entre la peor
de las dos mejoras de cuerpo (rt0.995, frente a la referencia) y la peor de las dos mejoras del D² completo, para elegir
una combinación que gane cuerpo sin ceder más de lo tolerable en el completo. El nivel sigue la regla s17.
Uso: python3 rejilla_cuerpo_b.py <ramo> <spec_json> <salida.json> [--ref_forma=a:b] [--formas=1:1,1.03:1,...] [--paso=0.1] [--tol=0.0003]
"""
from __future__ import annotations

import itertools
import json
import sys

import numpy as np
import pandas as pd

import os as _os
from pathlib import Path as _Path
# código de la línea principal de Claude: carpeta hermana Modelos_claude en el repositorio, o la copia de la nube
_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
import nivel_b  # noqa: E402
from comun import WORK, d2  # noqa: E402
from mezcla3 import component, ftw, labels, shape_rate  # noqa: E402


def rt(y, v, q):
    keep = y <= np.quantile(y, q)
    return d2(y[keep], v[keep] * ftw(y[keep], v[keep]))


def main():
    line, spec_path, out = sys.argv[1:4]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[4:] if a.startswith("--"))
    paso = float(opts.get("paso", 0.1)); tol = float(opts.get("tol", 0.0003))
    formas = [tuple(float(x) for x in f.split(":")) for f in opts.get("formas", "1:1").split(",")]
    spec = json.load(open(spec_path))
    nivel_b.clasificar({line: [c[0] for c in spec[line]]})
    nivel_b.aplicar()
    excl = nivel_b.mezcla3.sin_referencia({"nivel": "s17"})
    ysel, y24, idx25 = labels(line)
    fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "e_ef_coste", "exposure"])
    fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
    esel, e24 = fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values
    raw = []
    for run, sel_name, w in spec[line]:
        s, v, p = component(run, sel_name, line)
        raw.append((run, w, s.reindex(ysel.index).values, v.reindex(y24.index).values, p.reindex(idx25).values))
    names = [r[0] for r in raw]
    own = [r for r in raw if r[0] not in excl]
    wo = sum(r[1] for r in own)
    ref_tot = [sum(r[1] * r[j].sum() for r in own) / wo for j in (2, 3, 4)]
    S = np.column_stack([r[2] * ref_tot[0] / r[2].sum() for r in raw]); V = np.column_stack([r[3] * ref_tot[1] / r[3].sum() for r in raw])
    y1, y2 = ysel.values, y24.values
    k = len(raw)
    steps = int(round(1 / paso))
    grid = [np.array(c) / steps for c in itertools.product(range(steps + 1), repeat=k) if sum(c) == steps]
    rows = []
    for w in grid:
        bsel = S @ w; b24 = V @ w
        for a, b in formas:
            fs, f4 = shape_rate(bsel, esel, a, b), shape_rate(b24, e24, a, b)
            f23 = ftw(y1, fs)
            rows.append({"pesos": tuple(np.round(w, 2)), "forma": (a, b), "d2_v23": d2(y1, fs), "d2_v24": d2(y2, f4 * f23),
                         "rt995_v23": rt(y1, fs, 0.995), "rt995_v24": rt(y2, f4, 0.995), "rt99_v23": rt(y1, fs, 0.99), "rt99_v24": rt(y2, f4, 0.99)})
    df = pd.DataFrame(rows)
    # referencia: los pesos de la especificación con la forma de referencia
    w0 = tuple(np.round(np.array([r[1] for r in raw]) / sum(r[1] for r in raw), 2))
    ref_forma = tuple(float(x) for x in opts.get("ref_forma", "1:1").split(":"))
    ref = df[(df.pesos == w0) & (df.forma == ref_forma)]
    if ref.empty:
        bsel = S @ np.array(w0); b24 = V @ np.array(w0)
        fs, f4 = shape_rate(bsel, esel, *ref_forma), shape_rate(b24, e24, *ref_forma)
        ref = pd.DataFrame([{"d2_v23": d2(y1, fs), "d2_v24": d2(y2, f4 * ftw(y1, fs)), "rt995_v23": rt(y1, fs, 0.995), "rt995_v24": rt(y2, f4, 0.995),
                             "rt99_v23": rt(y1, fs, 0.99), "rt99_v24": rt(y2, f4, 0.99)}])
    ref = ref.iloc[0]
    for c in ("d2", "rt995", "rt99"):
        df[f"d{c}_v23"] = df[f"{c}_v23"] - ref[f"{c}_v23"]; df[f"d{c}_v24"] = df[f"{c}_v24"] - ref[f"{c}_v24"]
        df[f"peor_{c}"] = df[[f"d{c}_v23", f"d{c}_v24"]].min(axis=1)
    df["admisible"] = df.peor_d2 >= -tol
    pd.set_option("display.width", 250); pd.set_option("display.float_format", lambda x: f"{x:+.5f}")
    print("componentes:", names, "| referencia pesos", w0, "forma", ref_forma, "| fuera de nivel:", sorted(set(names) & excl))
    print("referencia:", {k: round(float(ref[k]), 5) for k in ("d2_v23", "d2_v24", "rt995_v23", "rt995_v24")})
    adm = df[df.admisible].sort_values("peor_rt995", ascending=False)
    print(f"\nmejores por cuerpo (rt0.995) con D² completo >= ref - {tol} en los dos cortes:")
    print(adm.head(12)[["pesos", "forma", "dd2_v23", "dd2_v24", "drt995_v23", "drt995_v24", "drt99_v23", "drt99_v24"]].to_string(index=False))
    print("\nmejores por D² completo (peor de los dos cortes):")
    print(df.sort_values("peor_d2", ascending=False).head(8)[["pesos", "forma", "dd2_v23", "dd2_v24", "drt995_v23", "drt995_v24"]].to_string(index=False))
    # frontera de Pareto (peor_d2, peor_rt995)
    pts = df[["peor_d2", "peor_rt995"]].values
    pareto = [i for i in range(len(df)) if not ((pts[:, 0] >= pts[i, 0]) & (pts[:, 1] >= pts[i, 1]) & ((pts[:, 0] > pts[i, 0]) | (pts[:, 1] > pts[i, 1]))).any()]
    print("\nfrontera de Pareto (peor mejora completa, peor mejora cuerpo):")
    print(df.iloc[pareto].sort_values("peor_d2")[["pesos", "forma", "peor_d2", "peor_rt995", "dd2_v23", "dd2_v24", "drt995_v23", "drt995_v24"]].to_string(index=False))
    df.to_json(WORK / out, orient="records")


if __name__ == "__main__":
    main()
