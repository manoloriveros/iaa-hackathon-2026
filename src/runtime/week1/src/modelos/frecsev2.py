"""Fit peril frequency with LightGBM Poisson and positive severity with gamma boosting.

Frequency uses peril-specific effective exposure. Fit weighted positive row
severity y_p/n_p when at least MIN_SEV positive claims are available; otherwise
use constant mean severity. Multiply by the positive-cost claim proportion to
include zero-cost claims. Use the approved household customer features and motor
F01234. V23 stops on calibration and compares on selection; --prod adds V24
and 2025 with 1.15 and 1.3 times the selected rounds and the requested seeds.
--aditivo uses two-leaf trees at learning rate 0.05 for additive models without
interactions. --desde and --semilla_inicial add frequency seeds using earlier
V23 rounds; the gamma severity fit is deterministic. --partes also saves each
peril's frequency times training mean severity for severidad_cfs.py.
Usage: python frecsev2.py <name> <line> [--prod] [--semillas=2] [--aditivo]
       [--desde=<run>] [--semilla_inicial=0] [--partes]
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd

from comun import PERILS, WORK, d2, to_model_frame
from experimentos import features, fit, load, predict

MIN_SEV = 1500
F3S2 = ["prior_claims_5y", "credit_band", "missed_payments_12m", "household_size", "years_at_address", "marital_status", "licence_points"]
SEV_PARAMS = {"objective": "gamma", "learning_rate": 0.03, "num_leaves": 5, "min_data_in_leaf": 300, "feature_fraction": 0.7, "lambda_l2": 20.0,
              "cat_smooth": 100, "min_data_per_group": 300, "max_cat_threshold": 16}


def main():
    name, line = sys.argv[1], sys.argv[2]
    opts = dict((a[2:].split("=") + ["1"])[:2] for a in sys.argv[3:] if a.startswith("--"))
    seeds = int(opts.get("semillas", 2))
    s0 = int(opts.get("semilla_inicial", 0))  # Add new seeds for averaging with an existing run.
    t0 = time.time()
    cfg = json.load(open(WORK / "cfg_total.json"))[line]["params"]
    df = load(line)
    feats = features(line, df, "F01234" if line == "motor" else "F0124")
    if line != "motor":
        feats += [c for c in F3S2 if c in df.columns and c not in feats]
    X = to_model_frame(df, feats)
    y = df["T0"].fillna(0).values
    yr = df.year.values
    expo = df["exposure"].values
    tr = yr <= 2022; cal = (yr == 2023) & (df.cal_half.values == 0); sel = (yr == 2023) & (df.cal_half.values == 1)
    pf = dict(cfg); pf.pop("cap", None); pf["objective"] = "poisson"; pf.pop("tweedie_variance_power", None)
    sev_params = dict(SEV_PARAMS)
    if "aditivo" in opts:
        pf.update({"num_leaves": 2, "learning_rate": 0.05, "min_data_in_leaf": 2000})
        sev_params.update({"num_leaves": 2, "learning_rate": 0.05})
    rep = {"line": line, "aditivo": "aditivo" in opts, "perils": {}}
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    best = {}

    def sev_fit(p, n, yp, trm, valm=None, rounds=None):
        pos_tr = trm & (yp > 0) & (n > 0)
        share = float((yp[trm] > 0).sum() / max((n[trm] > 0).sum(), 1))  # Claim-bearing rows with positive observed cost.
        mean_pos = float(yp[pos_tr].sum() / n[pos_tr].sum())
        if pos_tr.sum() < MIN_SEV:
            return None, mean_pos, share, 0
        s_obs = yp / np.maximum(n, 1)
        params = dict(sev_params, num_threads=2, verbose=-1, seed=20261017)
        import lightgbm as lgb
        dtr = lgb.Dataset(X[pos_tr], label=s_obs[pos_tr], weight=n[pos_tr], init_score=np.full(pos_tr.sum(), np.log(mean_pos)))
        if valm is not None:
            pos_v = valm & (yp > 0) & (n > 0)
            dv = lgb.Dataset(X[pos_v], label=s_obs[pos_v], weight=n[pos_v], init_score=np.full(pos_v.sum(), np.log(mean_pos)), reference=dtr)
            b = lgb.train(params, dtr, num_boost_round=3000, valid_sets=[dv], callbacks=[lgb.early_stopping(150, verbose=False)])
            it = max(b.best_iteration, 10)
        else:
            b = lgb.train(params, dtr, num_boost_round=rounds)
            it = rounds
        return b, mean_pos, share, it

    def sev_pred(b, mean_pos, share, m, it):
        if b is None:
            return np.full(m.sum(), mean_pos * share)
        return np.exp(b.predict(X[m], raw_score=True, num_iteration=it) + np.log(mean_pos)) * share

    mu_sel = np.zeros(sel.sum())
    if "desde" in opts:
        src = json.loads((WORK / opts["desde"] / "resumen.json").read_text())
        best = {p: (int(src["perils"][p]["best_frec"]), int(src["perils"][p]["best_sev"])) for p in PERILS[line]}
        rep.update({"desde": opts["desde"], "semilla_inicial": s0, "perils": {p: {"best_frec": best[p][0], "best_sev": best[p][1]} for p in PERILS[line]}})
    for p in ([] if "desde" in opts else PERILS[line]):
        n = df[f"n_{p}"].fillna(0).values.astype(float)
        yp = df[f"y_{p}"].fillna(0).values
        off = df[f"e_ef_{p}"].values
        b, base = fit(X[tr], n[tr], off[tr], X[cal], n[cal], off[cal], rounds=6000, early=200, params=dict(pf))
        bf = b.best_iteration or b.current_iteration()
        lam = predict(b, base, X[sel], off[sel], bf)
        if "partes" in opts:
            np.savez(out / f"v23_{p}.npz", best=bf, lam=lam)
        sb, mean_pos, share, sit = sev_fit(p, n, yp, tr, cal)
        sv = sev_pred(sb, mean_pos, share, sel, sit if sb is not None else None)
        best[p] = (bf, sit)
        mu_sel += lam * sv
        sv_const = mean_pos * share
        rep["perils"][p] = {"best_frec": bf, "best_sev": sit, "sev_media": round(sv_const, 1),
                            "d2_peligro_sev_modelo": round(d2(yp[sel], lam * sv), 5), "d2_peligro_sev_constante": round(d2(yp[sel], lam * sv_const), 5)}
        print(name, p, rep["perils"][p], round(time.time() - t0), flush=True)
    if "desde" not in opts:
        rep["d2_sel"] = round(d2(y[sel], mu_sel), 5)
        print(name, "V23 selección", rep["d2_sel"], flush=True)
        pd.DataFrame({"row_id": df.row_id[sel].astype(str).values, "line": line, "y": y[sel], "mu": mu_sel}).to_parquet(WORK / f"sel_{name}.parquet", index=False)
    (out / "resumen.json").write_text(json.dumps(rep, indent=1))
    if "prod" not in opts:
        return
    for tag, trm, evm, mult in (("v24", yr <= 2023, yr == 2024, 1.15), ("2025", yr <= 2024, yr == 2025, 1.3)):
        mu = np.zeros(evm.sum())
        for p in PERILS[line]:
            n = df[f"n_{p}"].fillna(0).values.astype(float)
            yp = df[f"y_{p}"].fillna(0).values
            off = df[f"e_ef_{p}"].values
            offe = off[evm] if tag == "v24" else expo[evm]
            bf, sit = best[p]
            if sit:
                sb, mean_pos, share, _ = sev_fit(p, n, yp, trm, None, rounds=int(round(sit * mult)))
            else:
                pos = trm & (yp > 0) & (n > 0)
                sb, mean_pos, share = None, float(yp[pos].sum() / n[pos].sum()), float((yp[trm] > 0).sum() / max((n[trm] > 0).sum(), 1))
            sv = sev_pred(sb, mean_pos, share, evm, None)
            freq = np.zeros(evm.sum())
            for s in range(seeds):
                b, base = fit(X[trm], n[trm], off[trm], rounds=int(round(bf * mult)), early=None, params=dict(pf, seed=20261017 + 101 * (s0 + s)))
                freq += np.exp(b.predict(X[evm], raw_score=True) + base + np.log(offe)) / seeds
            mu += freq * sv
            if "partes" in opts:
                # cat_frecsev format: predicted frequency times training cost/claim count.
                np.save(out / f"{'v24' if tag == 'v24' else 'prod'}_{p}.npy", freq * (yp[trm].sum() / max(n[trm].sum(), 1.0)))
        if tag == "v24":
            rep["d2_v24"] = round(d2(y[evm], mu), 5)
            pd.DataFrame({"row_id": df.row_id[evm].astype(str).values, "line": line, "y": y[evm], "mu": mu}).to_parquet(out / "v24.parquet", index=False)
            print(name, "V24", rep["d2_v24"], round(time.time() - t0), flush=True)
        else:
            rep["pred_2025_total_CU"] = round(float(mu.sum()), 2)
            pd.DataFrame({"row_id": df.row_id[evm].astype(str).values, "line": line, "prediction": mu}).to_parquet(out / "prediccion_2025.parquet", index=False)
        (out / "resumen.json").write_text(json.dumps(rep, indent=1))
    print(name, json.dumps(rep), flush=True)


if __name__ == "__main__":
    main()
