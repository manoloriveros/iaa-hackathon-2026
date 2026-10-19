"""Deriva de la frecuencia por peligro fuera de muestra: factor por peligro para el año siguiente, con la lógica del nivel.

Los modelos de frecuencia por peligro (CFS, FSAP) se entrenan agrupando los años sin variable de año; su nivel por
peligro es el promedio de la ventana de entrenamiento. El nivel global lo corrige el ancla de la mezcla (factor
f = (f23 + f24) / 2 de la línea principal), pero la mezcla de peligros no: en 2024 los modelos de edificios predicen un
10-15 % menos de siniestros de hundimiento de los observados (y en 2023 un 10 %), con inundación y tormenta sin deriva
estable. Dentro de muestra la deriva no se ve (las variables ligadas al calendario, renovaciones y antigüedad como
cliente, la absorben), así que la medida útil es la de los cortes anteriores fuera de muestra, igual que f23 y f24:
  r22_p = siniestros observados / esperados del peligro en 2022 con un modelo entrenado en 2021,
  r23_p = ídem en 2023 con 2021-2022, r24_p = ídem en 2024 con 2021-2023,
con un modelo sustituto LightGBM Poisson por peligro (variables y offset de CFS; parada temprana en un 15 % aleatorio de
las filas de entrenamiento). Factores por corte: V23 <- r22; V24 <- media(r22, r23); PROD <- media(r23, r24), acotados a
[1/1,15; 1,15] y a 1 cuando el peligro tiene menos de MIN_SIN siniestros en el año medido. También se calculan los
cocientes de las partes guardadas de las corridas CFS y FSAP en V23 y V24, para comprobar que el sustituto las sigue.
Resultado en experimentos/frec_tendencia_<ramo>.json; se aplica con severidad_tendencia.py --frec=<json>[:fuente].
Uso: python3 frecuencia_tendencia_b.py <ramo> [--cortes=V22,V23,V24] [--peligros=p1,p2] [--corridas=CFS_x,FSAP_x]
"""
from __future__ import annotations

import json
import os as _os
import sys
import time
from pathlib import Path as _Path

import lightgbm as lgb
import numpy as np
import pandas as pd

_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
sys.path.insert(0, str(_Path(__file__).resolve().parent))
from cat_frecsev import F3S2  # noqa: E402
from comun import PERILS, WORK  # noqa: E402
from experimentos import features, load  # noqa: E402

EXP = _Path(__file__).resolve().parent / "experimentos"
# corte: (último año de entrenamiento, año medido)
FOLDS = {"V22": (2021, 2022), "V23": (2022, 2023), "V24": (2023, 2024)}
APLICA = {"V23": ["V22"], "V24": ["V22", "V23"], "PROD": ["V23", "V24"]}
CAP = 0.15
MIN_SIN = 200
PARAMS = dict(objective="poisson", learning_rate=0.05, num_leaves=31, min_data_in_leaf=500, feature_fraction=0.8, bagging_fraction=0.8,
              bagging_freq=1, lambda_l2=10.0, max_bin=255, num_threads=2, verbose=-1, boost_from_average=False, cat_smooth=50,
              min_data_per_group=200, max_cat_to_onehot=8, seed=20261018)
CORRIDAS = {"motor": ["CFS_motor_v23", "CFS_motor_s23"], "buildings": ["CFS_buildings", "FSAP_buildings"], "contents": ["CFS_contents", "FSAP_contents"]}


def cocientes_guardados(df, line, runs):
    """Observado / esperado por peligro en V23 (mitad de selección de 2023) y V24 (2024) de las partes guardadas."""
    yr = df.year.values; ch = df.cal_half.values
    out = {}
    for r in runs:
        out[r] = {}
        for p in PERILS[line]:
            n = df[f"n_{p}"].fillna(0).values.astype(float); yp = df[f"y_{p}"].fillna(0).values
            res = {}
            f = WORK / r / f"v23_{p}.npz"
            if f.exists():
                sel = (yr == 2023) & (ch == 1)
                res["V23"] = round(float(n[sel].sum() / np.load(f)["lam"].sum()), 4)
            f = WORK / r / f"v24_{p}.npy"
            if f.exists():
                tr = yr <= 2023; m24 = yr == 2024
                sev = yp[tr].sum() / max(n[tr].sum(), 1.0)
                res["V24"] = round(float(n[m24].sum() / (np.load(f).sum() / sev)), 4)
            out[r][p] = res
    return out


def main():
    line = sys.argv[1]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[2:] if a.startswith("--"))
    cortes = opts.get("cortes", "V22,V23,V24").split(",")
    perils = opts.get("peligros", ",".join(PERILS[line])).split(",")
    runs = opts.get("corridas", ",".join(CORRIDAS[line])).split(",")
    t0 = time.time()
    df = load(line)
    feats = features(line, df, "F01234" if line == "motor" else "F0124")
    if line != "motor":
        feats += [c for c in F3S2 if c in df.columns and c not in feats]
    X = df[feats].copy()
    for c in X.columns:
        if pd.api.types.is_bool_dtype(X[c].dtype):
            X[c] = X[c].astype("float32")
        elif pd.api.types.is_numeric_dtype(X[c].dtype):
            X[c] = X[c].astype("float32")
        else:
            X[c] = X[c].astype(str).fillna("nan").astype("category")
    yr = df.year.values
    rng = np.random.default_rng(20261018)
    hold = rng.random(len(df)) < 0.15
    out_path = EXP / f"frec_tendencia_{line}.json"
    rep = json.loads(out_path.read_text()) if out_path.exists() else {"line": line, "cortes": {}, "factores": {}}
    rep["guardadas"] = cocientes_guardados(df, line, [r for r in runs if (WORK / r).exists()])
    print("cocientes de las partes guardadas:", json.dumps(rep["guardadas"]), flush=True)
    for fold in cortes:
        ymax, yev = FOLDS[fold]
        trm, evm = yr <= ymax, yr == yev
        rep["cortes"].setdefault(fold, {})
        for p in perils:
            if p in rep["cortes"][fold] and "reanudar" in opts:
                continue
            n = df[f"n_{p}"].fillna(0).values.astype(float); off = df[f"e_ef_{p}"].values
            base = float(np.log(n[trm].sum() / off[trm].sum()))
            tr, va = trm & ~hold, trm & hold
            dtr = lgb.Dataset(X[tr], label=n[tr], init_score=np.log(off[tr]) + base, free_raw_data=False)
            dva = lgb.Dataset(X[va], label=n[va], init_score=np.log(off[va]) + base, reference=dtr)
            m = lgb.train(PARAMS, dtr, num_boost_round=3000, valid_sets=[dva], callbacks=[lgb.early_stopping(100, verbose=False)])
            lam = np.exp(m.predict(X[evm], raw_score=True) + np.log(off[evm]) + base)
            obs, esp = float(n[evm].sum()), float(lam.sum())
            # mismo cociente sin el año medido entero: por semestre de inicio, para ver si es estable dentro del año
            mes = df.mes_inicio.values[evm]
            rep["cortes"][fold][p] = {"iteraciones": int(m.best_iteration), "observados": int(obs), "esperados": round(esp, 1), "cociente": round(obs / esp, 4),
                                     "cociente_h1": round(float(n[evm][mes <= 6].sum() / lam[mes <= 6].sum()), 4), "cociente_h2": round(float(n[evm][mes > 6].sum() / lam[mes > 6].sum()), 4),
                                     "frecuencia_entrenamiento_x1000": round(1000 * float(n[trm].sum() / off[trm].sum()), 3), "frecuencia_medida_x1000": round(1000 * float(n[evm].sum() / off[evm].sum()), 3)}
            print(fold, p, json.dumps(rep["cortes"][fold][p]), round(time.time() - t0), flush=True)
            out_path.write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    # factores por corte de aplicación
    for dest, fuentes in APLICA.items():
        rep["factores"][dest] = {}
        for p in PERILS[line]:
            vals = [rep["cortes"][f][p] for f in fuentes if f in rep["cortes"] and p in rep["cortes"][f]]
            if not vals:
                continue
            fac = float(np.exp(np.mean([np.log(v["cociente"]) if v["observados"] >= MIN_SIN else 0.0 for v in vals])))
            rep["factores"][dest][p] = round(float(np.clip(fac, 1 / (1 + CAP), 1 + CAP)), 4)
    out_path.write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print("factores:", json.dumps(rep["factores"]), flush=True)


if __name__ == "__main__":
    main()
