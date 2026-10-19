"""Factores de deriva de frecuencia por peligro y corte, por familia de partes, con la lógica del nivel (f23, f24).

Fuentes: r22 de experimentos/frec_v22_<ramo>.json (v22_frecuencia_b.py, familias "cat" y "aditivo") y r23, r24 de las
partes guardadas de las corridas indicadas (observado / esperado del peligro en la mitad de selección de 2023 y en 2024,
calculados aquí). Factores: V23 <- r22; V24 <- media geométrica de r22 y r23; PROD <- media geométrica de r23 y r24.
Cada media se contrae hacia 1 con credibilidad de fluctuación limitada, z = min(1, sqrt(n / 1082)) con n los siniestros
observados del peligro en los periodos medidos (1082 siniestros para credibilidad completa, 90 % dentro de ±5 %), y se
acota a [1/1,15; 1,15].
Escribe experimentos/frec_factores_<ramo>.json con "factores_cat" y "factores_aditivo" (y el detalle de los cocientes).
Uso: python3 factores_frec_b.py <ramo> --cat=<corrida CFS> --aditivo=<corrida FSAP> [--sin_v22]
"""
from __future__ import annotations

import json
import os as _os
import sys
from pathlib import Path as _Path

import numpy as np

_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
sys.path.insert(0, str(_Path(__file__).resolve().parent))
from comun import PERILS  # noqa: E402
from experimentos import load  # noqa: E402
from frecuencia_tendencia_b import cocientes_guardados  # noqa: E402

EXP = _Path(__file__).resolve().parent / "experimentos"
CAP = 0.15
N_PLENA = 1082


def main():
    line = sys.argv[1]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[2:] if a.startswith("--"))
    df = load(line)
    yr = df.year.values; ch = df.cal_half.values
    v22 = json.loads((EXP / f"frec_v22_{line}.json").read_text()) if (EXP / f"frec_v22_{line}.json").exists() and "sin_v22" not in opts else {}
    rep = {"line": line, "cap": CAP, "siniestros_credibilidad_plena": N_PLENA, "detalle": {}}
    for familia in ("cat", "aditivo"):
        if familia not in opts:
            continue
        run = opts[familia]
        g = cocientes_guardados(df, line, [run])[run]
        det, fac = {}, {"V23": {}, "V24": {}, "PROD": {}}
        for p in PERILS[line]:
            n = df[f"n_{p}"].fillna(0).values
            cnt = {"V23": int(n[(yr == 2023) & (ch == 1)].sum()), "V24": int(n[yr == 2024].sum())}
            r = {}
            if familia in v22 and p in v22[familia]:
                r["V22"] = (v22[familia][p]["cociente"], v22[familia][p]["observados"])
            for k in ("V23", "V24"):
                if k in g[p]:
                    r[k] = (g[p][k], cnt[k])
            det[p] = {k: {"cociente": v[0], "siniestros": v[1]} for k, v in r.items()}

            def media(claves):
                vals = [np.log(r[k][0]) for k in claves if k in r]
                n_obs = sum(r[k][1] for k in claves if k in r)
                if not vals:
                    return 1.0
                z = min(1.0, np.sqrt(n_obs / N_PLENA))
                return round(float(np.clip(np.exp(z * np.mean(vals)), 1 / (1 + CAP), 1 + CAP)), 4)
            fac["V23"][p] = media(["V22"]); fac["V24"][p] = media(["V22", "V23"]); fac["PROD"][p] = media(["V23", "V24"])
        rep["detalle"][familia] = {"corrida": run, "cocientes": det}
        rep[f"factores_{familia}"] = fac
        print(familia, run, json.dumps(fac), flush=True)
    (EXP / f"frec_factores_{line}.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
