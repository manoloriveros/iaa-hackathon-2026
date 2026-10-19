"""Cociente real/esperado de la mezcla S18 sin forma por tramo de exposición nominal y trimestre de inicio del periodo.

Por ramo y corte (V23 selección y V24), con el nivel ajustado en cada corte (factor Tweedie). Muestra también cuántas filas
de 2025 caen en cada celda. Sirve para leer la elasticidad b de la forma: los periodos se parten por año natural y por
cambios de póliza, así que los tramos cortos son principios o finales de año o de póliza.
Uso: python3 ae_exposicion_trimestre.py (lee las corridas de ../Modelos_claude a través de mezcla3.py)
"""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd
MC = Path(os.environ.get("MODELOS_CLAUDE", Path(__file__).resolve().parent.parent / "Modelos_claude"))
if not MC.exists():
    MC = Path("/home/claude/modelos_claude")  # espacio de trabajo en la nube
sys.path.insert(0, str(MC))
from comun import WORK, d2
from mezcla3 import component, labels, sin_referencia, ftw
spec_path = MC / "experimentos" / "spec_s18_propio.json"
spec = json.load(open(spec_path if spec_path.exists() else WORK / "spec_s18_propio.json"))
for line in ("contents", "buildings", "motor"):
    ysel, y24, idx25 = labels(line)
    raw = []
    for run, sel_name, w in spec[line]:
        s, v, p = component(run, sel_name, line)
        raw.append((run, w, s.reindex(ysel.index).values, v.reindex(y24.index).values, p.reindex(idx25).values))
    own = [(w, s, v, p) for run, w, s, v, p in raw if run not in sin_referencia({'nivel': 's17'})]
    wo = sum(o[0] for o in own); ref = [sum(o[0] * o[j].sum() for o in own) / wo for j in (1, 2, 3)]
    comps = [(s * ref[0] / s.sum(), v * ref[1] / v.sum(), p * ref[2] / p.sum()) for run, w, s, v, p in raw]
    ws = np.array([c[2] for c in spec[line]], float); ws /= ws.sum()
    cols = ["row_id", "e_ef_coste", "exposure", "mes_inicio", "period_start"]
    fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=cols)
    fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
    bsel = sum(w * c[0] for w, c in zip(ws, comps)); b24 = sum(w * c[1] for w, c in zip(ws, comps))
    print("=====", line)
    for nm, idx, y, b in (("V23", ysel.index, ysel.values, bsel), ("V24", y24.index, y24.values, b24)):
        f = fe.reindex(idx)
        ex = f.exposure.values; mi = f.mes_inicio.values
        mu = b * ftw(y, b)
        eb = np.digitize(ex, [0.25, 0.5, 0.75, 0.999])
        q = ((mi - 1) // 3).astype(int)
        tab = pd.DataFrame({"eb": eb, "q": q, "y": y, "mu": mu}).groupby(["eb", "q"]).agg(n=("y", "size"), y=("y", "sum"), mu=("mu", "sum"))
        tab["AE"] = (tab.y / tab.mu).round(3)
        piv = tab.AE.unstack("q"); pn = tab.n.unstack("q")
        print(nm, "A/E por tramo de exposición (filas: <0,25, 0,25-0,5, 0,5-0,75, 0,75-1, =1) y trimestre de inicio (columnas)")
        print(piv.to_string()); print("filas"); print(pn.to_string())
    f25 = fe.reindex(idx25)
    print("2025 filas por tramo y trimestre"); print(pd.crosstab(np.digitize(f25.exposure.values, [0.25, 0.5, 0.75, 0.999]), ((f25.mes_inicio.values - 1)//3).astype(int)).to_string())
