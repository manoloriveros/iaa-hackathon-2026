"""Severidad híbrida (GLM gamma más boosting gamma encima) para la frecuencia CatBoost por peligro (CFS), sin reentrenar la frecuencia.

Extiende severidad_cfs.py. Por peligro y corte, primero ajusta el mismo GLM gamma con enlace log de CFSS (log del capital
relativo a la mediana y sótano en inundación en hogar; log del grupo de valor y antigüedad del vehículo en daños propios,
robo y lunas en autos; constante en el resto). Después, si el peligro tiene al menos MIN_SEV siniestros positivos en el
entrenamiento del corte, añade un LightGBM gamma que parte del GLM (init_score) y usa las variables autorizadas de la
línea (autos F01234 sin marketing_segment; hogar F0124 más las siete F3 de D80), con los parámetros de severidad de
frecsev2.py. Las rondas se eligen en V23 con parada temprana sobre los siniestros positivos de la mitad de calibración de
2023; V24 y producción usan esas rondas por 1,15 y 1,3, como el resto de la línea. Con menos de 5 rondas útiles el
peligro queda solo con el GLM. La relatividad se normaliza para que su media ponderada en los siniestros de entrenamiento
valga 1 y multiplica la contribución guardada de cada peligro (frecuencia x severidad constante).
Uso: python3 severidad_cfs2.py <corrida_cfs> <ramo> <corrida_salida> [--v23=..] [--v24=c1,c2] [--prod=c1,c2] [--hojas=5] [--min_sev=1500]
--hojas=2 usa árboles de una división con tasa 0,05 (aditivo); --hojas=5 los parámetros de FS2 (tasa 0,03).
"""
from __future__ import annotations

import json
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd

from comun import PERILS, WORK, d2, to_model_frame
from experimentos import features, load
from severidad_cfs import glm_gamma

F3S2 = ["prior_claims_5y", "credit_band", "missed_payments_12m", "household_size", "years_at_address", "marital_status", "licence_points"]
SEV_PARAMS = {"objective": "gamma", "learning_rate": 0.03, "num_leaves": 5, "min_data_in_leaf": 300, "feature_fraction": 0.7, "lambda_l2": 20.0,
              "cat_smooth": 100, "min_data_per_group": 300, "max_cat_threshold": 16, "num_threads": 2, "verbose": -1, "seed": 20261017}
MULT = {"V24": 1.15, "PROD": 1.3}


def main():
    src, line, name = sys.argv[1:4]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[4:] if a.startswith("--"))
    run_v23 = opts.get("v23", src); runs_v24 = opts.get("v24", src).split(","); runs_prod = opts.get("prod", src).split(",")
    hojas = int(opts.get("hojas", 5)); min_sev = int(opts.get("min_sev", 1500))
    params = dict(SEV_PARAMS)
    if hojas == 2:
        params.update({"num_leaves": 2, "learning_rate": 0.05})
    df = load(line)
    feats = features(line, df, "F01234" if line == "motor" else "F0124")
    if line != "motor":
        feats += [c for c in F3S2 if c in df.columns and c not in feats]
    X = to_model_frame(df, feats)
    yr = df.year.values
    cal_half = df.cal_half.values
    if line != "motor":
        si = df.sum_insured.astype(float).values
        si = np.where(np.isfinite(si) & (si > 0), si, np.nan)
        bas = df.basement.astype(float).fillna(0).values
    else:
        vvg = df.vehicle_value_group.astype(float).values
        vage = np.clip(df.vehicle_age.astype(float).fillna(df.vehicle_age.median()).values, 0, 30) / 10.0
    folds = {"V23": (yr <= 2022, (yr == 2023) & (cal_half == 1)), "V24": (yr <= 2023, yr == 2024), "PROD": (yr <= 2024, yr == 2025)}
    cal = (yr == 2023) & (cal_half == 0)
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    rep = {"origen": src, "line": line, "hojas": hojas, "min_sev": min_sev, "features": len(feats), "perils": {}}
    rounds = {}
    parts = {}
    for fold, (trm, evm) in folds.items():
        if line != "motor":
            med = np.nanmedian(si[trm])
            zsi = np.log(np.where(np.isnan(si), med, si) / med)
        else:
            medv = np.nanmedian(vvg[trm])
            zv = np.log(np.where(np.isnan(vvg), medv, vvg) / medv)
        tot = np.zeros(evm.sum())
        for p in PERILS[line]:
            n = df[f"n_{p}"].fillna(0).values.astype(float); yp = df[f"y_{p}"].fillna(0).values
            pos = trm & (n > 0) & (yp > 0)
            s_obs = np.where(n > 0, yp / np.maximum(n, 1), 0.0)
            if line != "motor":
                covs = [zsi] + ([bas] if p == "flood" else [])
            else:
                covs = [zv, vage] if p in ("own_damage", "theft", "glass_hail") else []
            Z = np.column_stack([np.ones(len(df))] + covs)
            beta = glm_gamma(Z[pos, 1:], yp[pos] / n[pos], n[pos]) if covs else np.array([np.log(np.average(s_obs[pos], weights=n[pos]))])
            eta = Z @ beta
            info = {"betas": [round(float(b), 4) for b in beta[1:]], "siniestros": int(n[pos].sum()), "filas_pos": int(pos.sum())}
            raw = np.zeros(len(df))
            use_gbm = pos.sum() >= min_sev
            if use_gbm:
                dtr = lgb.Dataset(X[pos], label=s_obs[pos], weight=n[pos], init_score=eta[pos])
                if fold == "V23":
                    pv = cal & (n > 0) & (yp > 0)
                    dv = lgb.Dataset(X[pv], label=s_obs[pv], weight=n[pv], init_score=eta[pv], reference=dtr)
                    b = lgb.train(params, dtr, num_boost_round=3000, valid_sets=[dv], callbacks=[lgb.early_stopping(150, verbose=False)])
                    it = int(b.best_iteration or 0)
                    rounds[p] = it if it >= 5 else 0
                    if rounds[p]:
                        raw = b.predict(X, raw_score=True, num_iteration=rounds[p])
                else:
                    it = int(round(rounds.get(p, 0) * MULT[fold]))
                    if it:
                        b = lgb.train(params, dtr, num_boost_round=it)
                        raw = b.predict(X, raw_score=True)
                info["rondas"] = int(rounds.get(p, 0) if fold == "V23" else round(rounds.get(p, 0) * MULT[fold]))
            else:
                info["rondas"] = 0
            s_hat = np.exp(eta + raw)
            rel = s_hat / np.average(s_hat[pos], weights=n[pos])
            if fold == "V23":
                lam = np.load(WORK / run_v23 / f"v23_{p}.npz")["lam"]
                sev = yp[trm].sum() / max(n[trm].sum(), 1.0)
                part = lam * sev
            else:
                rr = runs_v24 if fold == "V24" else runs_prod
                part = sum(np.load(WORK / r / f"{'v24' if fold == 'V24' else 'prod'}_{p}.npy") for r in rr) / len(rr)
            assert len(part) == evm.sum()
            tot += part * rel[evm]
            if fold == "V23":
                t0 = df["T0"].fillna(0).values
                info["d2_peligro_sel"] = round(d2(yp[evm], part * rel[evm]), 5)
                info["d2_peligro_sel_constante"] = round(d2(yp[evm], part), 5)
            rep["perils"].setdefault(p, {})[fold] = info
            print(name, fold, p, info, flush=True)
        parts[fold] = (evm, tot)
    t0 = df["T0"].fillna(0).values
    row_ids = df.row_id.astype(str).values
    evm, mu = parts["V23"]
    rep["d2_sel"] = round(d2(t0[evm], mu), 5)
    pd.DataFrame({"row_id": row_ids[evm], "line": line, "y": t0[evm], "mu": mu}).to_parquet(WORK / f"sel_{name}.parquet", index=False)
    evm, mu = parts["V24"]
    rep["d2_v24"] = round(d2(t0[evm], mu), 5)
    pd.DataFrame({"row_id": row_ids[evm], "line": line, "y": t0[evm], "mu": mu}).to_parquet(out / "v24.parquet", index=False)
    evm, mu = parts["PROD"]
    rep["pred_2025_total_CU"] = round(float(mu.sum()), 2)
    pd.DataFrame({"row_id": row_ids[evm], "line": line, "prediction": mu}).to_parquet(out / "prediccion_2025.parquet", index=False)
    (out / "resumen.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in rep.items() if k != "perils"}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
