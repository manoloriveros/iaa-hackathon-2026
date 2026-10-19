"""Frecuencia LightGBM Poisson por peligro (aditiva o de profundidad intermedia) con variables adicionales opcionales,
para medir qué aporta una familia de variables en los peligros donde debería actuar (por ejemplo, la meteorología del
propio año en lunas, tormenta, escape de agua y hundimiento).

Para cada peligro pedido entrena dos modelos con la misma configuración, uno sin y otro con las variables adicionales:
V23 (2021-2022, parada temprana en la mitad de calibración de 2023, medida en la de selección) y V24 (2021-2023 con las
rondas de V23 x 1,15, medida en 2024). Informa el D² Poisson de los conteos y el D² Tweedie del coste del peligro con la
severidad media del entrenamiento (como frecsev2.py). Con --partes guarda las partes (formato cat_frecsev.py) de la
variante con variables, para poder sustituir ese peligro en una corrida de frecuencia existente.
Uso: python3 frec_peligro_b.py <nombre> <ramo> --peligros=p1,p2 --extra=col1,col2 [--aditivo] [--partes] [--semillas=2] [--prod]
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd

import os as _os
from pathlib import Path as _Path
# código de la línea principal de Claude: carpeta hermana Modelos_claude en el repositorio, o la copia de la nube
_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
from comun import PERILS, WORK, d2, deviance, to_model_frame  # noqa: E402
from experimentos import features, fit, load, predict  # noqa: E402

F3S2 = ["prior_claims_5y", "credit_band", "missed_payments_12m", "household_size", "years_at_address", "marital_status", "licence_points"]


def d2_poisson(n, lam):
    dev = 2 * (np.where(n > 0, n * np.log(np.where(n > 0, n, 1) / lam), 0) - (n - lam))
    null = 2 * (np.where(n > 0, n * np.log(np.where(n > 0, n, 1) / n.mean()), 0) - (n - n.mean()))
    return float(1 - dev.sum() / null.sum())


def main():
    name, line = sys.argv[1], sys.argv[2]
    opts = dict((a[2:].split("=") + ["1"])[:2] for a in sys.argv[3:] if a.startswith("--"))
    perils = opts["peligros"].split(",")
    extra = [c for c in opts.get("extra", "").split(",") if c]
    seeds = int(opts.get("semillas", 2))
    t0 = time.time()
    cfg = json.load(open(WORK / "cfg_total.json"))[line]["params"]
    df = load(line)
    base_feats = features(line, df, "F01234" if line == "motor" else "F0124")
    if line != "motor":
        base_feats += [c for c in F3S2 if c in df.columns and c not in base_feats]
    missing = [c for c in extra if c not in df.columns]
    assert not missing, missing
    X = to_model_frame(df, base_feats + extra)
    yr = df.year.values
    expo = df["exposure"].values
    tr = yr <= 2022; cal = (yr == 2023) & (df.cal_half.values == 0); sel = (yr == 2023) & (df.cal_half.values == 1)
    tr24 = yr <= 2023; ev24 = yr == 2024; trp = yr <= 2024; te = yr == 2025
    pf = dict(cfg); pf.pop("cap", None); pf["objective"] = "poisson"; pf.pop("tweedie_variance_power", None)
    if "aditivo" in opts:
        pf.update({"num_leaves": 2, "learning_rate": 0.05, "min_data_in_leaf": 2000})
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    rep = {"line": line, "extra": extra, "aditivo": "aditivo" in opts, "perils": {}}
    for p in perils:
        n = df[f"n_{p}"].fillna(0).values.astype(float)
        yp = df[f"y_{p}"].fillna(0).values
        off = df[f"e_ef_{p}"].values
        r = {}
        for tag, feats in (("sin", base_feats), ("con", base_feats + extra)):
            Xf = X[feats]
            b, base = fit(Xf[tr], n[tr], off[tr], Xf[cal], n[cal], off[cal], rounds=6000, early=200, params=dict(pf))
            bf = b.best_iteration or b.current_iteration()
            lam = predict(b, base, Xf[sel], off[sel], bf)
            sev = yp[tr].sum() / max(n[tr].sum(), 1.0)
            r[tag] = {"best": int(bf), "d2n_sel": round(d2_poisson(n[sel], lam), 5), "d2c_sel": round(d2(yp[sel], lam * sev), 5)}
            lam24 = np.zeros(ev24.sum())
            for s in range(seeds):
                b24, base24 = fit(Xf[tr24], n[tr24], off[tr24], rounds=int(round(bf * 1.15)), early=None, params=dict(pf, seed=20261017 + 101 * s))
                lam24 += predict(b24, base24, Xf[ev24], off[ev24]) / seeds
            sev24 = yp[tr24].sum() / max(n[tr24].sum(), 1.0)
            r[tag].update({"d2n_v24": round(d2_poisson(n[ev24], lam24), 5), "d2c_v24": round(d2(yp[ev24], lam24 * sev24), 5)})
            if tag == "con" and "partes" in opts:
                np.savez(out / f"v23_{p}.npz", best=bf, lam=lam)
                np.save(out / f"v24_{p}.npy", lam24 * sev24)
                if "prod" in opts:
                    lamp = np.zeros(te.sum())
                    for s in range(seeds):
                        bp, basep = fit(Xf[trp], n[trp], off[trp], rounds=int(round(bf * 1.3)), early=None, params=dict(pf, seed=20261017 + 101 * s))
                        lamp += predict(bp, basep, Xf[te], expo[te]) / seeds
                    np.save(out / f"prod_{p}.npy", lamp * (yp[trp].sum() / max(n[trp].sum(), 1.0)))
            if tag == "con":
                imp = pd.Series(b.feature_importance("gain"), index=feats)
                r["gain_extra"] = {c: round(float(imp[c] / imp.sum()), 4) for c in extra}
            print(name, p, tag, r[tag], round(time.time() - t0), flush=True)
        r["dif_sel"] = round(r["con"]["d2c_sel"] - r["sin"]["d2c_sel"], 5)
        r["dif_v24"] = round(r["con"]["d2c_v24"] - r["sin"]["d2c_v24"], 5)
        rep["perils"][p] = r
        (out / "resumen.json").write_text(json.dumps(rep, indent=1))
        print(name, p, "dif coste sel", r["dif_sel"], "v24", r["dif_v24"], "gain extra", r.get("gain_extra"), flush=True)


if __name__ == "__main__":
    main()
