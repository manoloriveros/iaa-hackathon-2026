"""Autos híbrido: el exceso sobre el tope se reparte según la frecuencia predicha de lesiones corporales (BI).

En 2021-2023 el 25 % del coste de autos está por encima de 15.000 por fila y el 83 % del coste de esas filas es BI.
El recargo uniforme reparte ese exceso en proporción al Tweedie acotado, que crece con los daños propios (valor del
vehículo) aunque el exceso dependa de la frecuencia de BI. Componentes, todos con la configuración vigente de autos (F3):

  T  Tweedie acotado por fila (tope 15.000 o el indicado), offset e_ef_coste; se guarda sin recargo.
  B  Poisson del número de BI con offset e_ef_bodily_injury.
  N  Tweedie del coste sin BI (tope 25.000), offset e_ef de la mezcla de peligros sin BI.

Combinaciones (constantes estimadas solo con el entrenamiento de cada pliegue):
  H1(a): mu = T x (1 + a (L - 1)) + (1 - a) x k x B, con L = suma y / suma y acotada y k = exceso / número de BI.
  H2:    mu = N x L_N + s_BI x B, con s_BI = coste BI / número de BI del entrenamiento.
V23: parada temprana en la mitad de calibración, comparación en la de selección; V24: rondas V23 x 1,15; --prod entrena
2021-2024 (x 1,3) y predice 2025 con la exposición nominal. Guarda las predicciones de cada componente.
Uso: python3 hibrido_autos.py <nombre> [--cap=15000] [--prod]
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd

from comun import PERILS, WORK, d2, to_model_frame
from experimentos import features, fit, load, predict

CFG = json.load(open(WORK / "cfg_total.json"))["motor"]["params"]
NOBI = [p for p in PERILS["motor"] if p != "bodily_injury"]


def ftw(y, mu):
    return float((y / np.sqrt(mu)).sum() / np.sqrt(mu).sum())


def main():
    name = sys.argv[1]
    opts = dict((a[2:].split("=") + ["1"])[:2] for a in sys.argv[2:] if a.startswith("--"))
    cap = float(opts.get("cap", 15000))
    t0 = time.time()
    df = load("motor")
    feats = features("motor", df, "F01234")
    X = to_model_frame(df, feats)
    y = df["T0"].fillna(0).values
    ybi = df["y_bodily_injury"].fillna(0).values
    nbi = df["n_bodily_injury"].fillna(0).values.astype(float)
    ynb = y - ybi
    off = df["e_ef_coste"].values
    offbi = df["e_ef_bodily_injury"].values
    mature = df.year.isin([2021, 2022]).values
    w = {p: df[f"y_{p}"].fillna(0).values[mature].sum() for p in NOBI}
    offnb = sum(w[p] * df[f"e_ef_{p}"].values for p in NOBI) / sum(w.values())
    expo = df["exposure"].values
    yr = df.year.values
    folds = {
        "V23": ((yr <= 2022), ((yr == 2023) & (df.cal_half == 0)).values, ((yr == 2023) & (df.cal_half == 1)).values),
        "V24": ((yr <= 2023), None, (yr == 2024)),
        "PROD": ((yr <= 2024), None, (yr == 2025)),
    }
    pT = dict(CFG); pT["cap"] = cap
    pN = dict(CFG); pN["cap"] = 25000.0
    pB = dict(CFG); pB.pop("cap", None); pB["objective"] = "poisson"; pB.pop("tweedie_variance_power", None)
    best = {}
    rep = {"cap": cap, "folds": {}}
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    for fold in (["V23", "V24", "PROD"] if "prod" in opts else ["V23", "V24"]):
        tr, cal, ev = folds[fold]
        mult = {"V23": None, "V24": 1.15, "PROD": 1.3}[fold]
        o_ev, obi_ev, onb_ev = (off[ev], offbi[ev], offnb[ev]) if fold != "PROD" else (expo[ev], expo[ev], expo[ev])
        comp = {}
        for key, target, o, o_e, params in (("T", y, off, o_ev, pT), ("B", nbi, offbi, obi_ev, pB), ("N", ynb, offnb, onb_ev, pN)):
            if fold == "V23":
                b, base = fit(X[tr], target[tr], o[tr], X[cal], target[cal], o[cal], rounds=6000, early=200, params=dict(params))
                best[key] = b.best_iteration or b.current_iteration()
                it = best[key]
            else:
                b, base = fit(X[tr], target[tr], o[tr], rounds=int(round(best[key] * mult)), early=None, params=dict(params))
                it = None
            b.loading = 1.0
            comp[key] = predict(b, base, X[ev], o_e, it)
            print(fold, key, "best", best[key], round(time.time() - t0), flush=True)
        yc = np.minimum(y[tr], cap)
        L = y[tr].sum() / yc.sum()
        k = (y[tr].sum() - yc.sum()) / nbi[tr].sum()
        ync = np.minimum(ynb[tr], 25000.0)
        LN = ynb[tr].sum() / ync.sum()
        sbi = ybi[tr].sum() / nbi[tr].sum()
        consts = {"L": round(L, 4), "k": round(k, 1), "LN": round(LN, 4), "s_bi": round(sbi, 1)}
        variants = {f"H1_a{a:.2f}": comp["T"] * (1 + a * (L - 1)) + (1 - a) * k * comp["B"] for a in (1.0, 0.75, 0.5, 0.25, 0.0)}
        variants["H2"] = comp["N"] * LN + sbi * comp["B"]
        frame = pd.DataFrame({"row_id": df.row_id[ev].astype(str).values, "line": "motor", "T": comp["T"], "B": comp["B"], "N": comp["N"]})
        if fold != "PROD":
            yev = y[ev]
            frame["y"] = yev
            res = {k2: {"d2": round(d2(yev, m), 5), "d2_f_optimo": round(d2(yev, m * ftw(yev, m)), 5), "f": round(ftw(yev, m), 4)} for k2, m in variants.items()}
            res["consts"] = consts
            res["best"] = dict(best)
            rep["folds"][fold] = res
            print(fold, json.dumps(res), flush=True)
        else:
            rep["folds"][fold] = {"consts": consts, "totales": {k2: round(float(m.sum()), 2) for k2, m in variants.items()}}
        frame.to_parquet(out / f"componentes_{fold}.parquet", index=False)
        (out / "resumen.json").write_text(json.dumps(rep, indent=1))
    print("fin", round(time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
