"""Frecuencia por peligro con CatBoost Poisson por severidad media del peligro (versión CatBoost de FS_frecsev).

mu = sum_p lambda_p(x) x s_p, con lambda_p de CatBoost Poisson (baseline log e_ef_p + base) y s_p = coste del peligro /
número de siniestros del peligro en el entrenamiento de cada corte (sin tope). Mismo contrato que cat_experimento.py:
F3 solo en autos (y las siete variables de cliente D80 en hogar con --f3s2). V23: parada temprana por peligro en la mitad
de calibración y comparación en la de selección (guarda sel_<nombre>.parquet). Con --prod: V24 (iteraciones V23 x 1,15)
y 2025 (x 1,3, exposición nominal), con las semillas indicadas. Escribe WORK/<nombre>/ con el formato de produccion.py.
Reanudable: cada peligro guarda su resultado al terminar (v23_<p>.npz, v24_<p>.npy, prod_<p>.npy) y al relanzar la misma
orden se salta lo ya hecho. Las columnas numéricas pasan a float32 para ahorrar memoria (desde CFS_buildings; CFS_motor se
corrió con float64 salvo en su 2025).
Con --desde=<corrida> --semilla_inicial=k toma las mejores iteraciones de V23 de otra corrida y entrena solo V24 y 2025
con semillas nuevas, para promediarlas después con combinar_semillas.py.
Uso: python3 cat_frecsev.py <nombre> <ramo> [--prod] [--solo_prod] [--semillas=2] [--depth=6] [--lr=0.05] [--f3s2] [--desde=<corrida>] [--semilla_inicial=0]
"""
from __future__ import annotations

import gc
import json
import sys
import time

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool

from cat_experimento import frame
from comun import PERILS, WORK, d2
from experimentos import features, load

F3S2 = ["prior_claims_5y", "credit_band", "missed_payments_12m", "household_size", "years_at_address", "marital_status", "licence_points"]


def main():
    name, line = sys.argv[1], sys.argv[2]
    opts = dict((a[2:].split("=") + ["1"])[:2] for a in sys.argv[3:] if a.startswith("--"))
    seeds, depth, lr = int(opts.get("semillas", 2)), int(opts.get("depth", 6)), float(opts.get("lr", 0.05))
    s0 = int(opts.get("semilla_inicial", 0))  # para añadir semillas nuevas a una corrida previa sin repetir las usadas
    t0 = time.time()
    df = load(line)
    feats = features(line, df, "F01234" if line == "motor" else "F0124")
    if line != "motor" and "f3s2" in opts:
        feats += [c for c in F3S2 if c in df.columns and c not in feats]
    X, cats = frame(df, feats)
    for c in X.columns:
        if c in cats:
            X[c] = X[c].astype("category")
        elif X[c].dtype == "float64":
            X[c] = X[c].astype("float32")
    y = df["T0"].fillna(0).values
    yr = df.year.values
    expo = df["exposure"].values
    row_ids = df.row_id.astype(str).values
    cal_half = df.cal_half.values
    per = {p: (df[f"n_{p}"].fillna(0).values.astype(float), df[f"y_{p}"].fillna(0).values, df[f"e_ef_{p}"].values) for p in PERILS[line]}
    del df
    gc.collect()
    tr = yr <= 2022; cal = (yr == 2023) & (cal_half == 0); sel = (yr == 2023) & (cal_half == 1)
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    if "solo_prod" in opts:
        # solo 2025, con las mejores iteraciones guardadas de V23; guarda cada peligro al terminar para poder reanudar
        rep = json.loads((out / "resumen.json").read_text())
        te, trm = yr == 2025, yr <= 2024
        # memoria: copias compactas de entrenamiento y test, sin el marco completo
        Xtr, Xte = X.loc[trm].copy(), X.loc[te].copy()
        del X
        for Z in (Xtr, Xte):
            for c in Z.columns:
                if Z[c].dtype == "float64":
                    Z[c] = Z[c].astype("float32")
        gc.collect()
        mu = np.zeros(te.sum())
        for p, (n, yp, off) in per.items():
            fp = out / f"prod_{p}.npy"
            if fp.exists():
                mu += np.load(fp)
                print(name, "2025", p, "reanudado", flush=True)
                continue
            sev = yp[trm].sum() / max(n[trm].sum(), 1.0)
            base = float(np.log(n[trm].sum() / off[trm].sum()))
            ptr = Pool(Xtr, n[trm], cat_features=cats, baseline=np.log(off[trm]) + base)
            pev = Pool(Xte, cat_features=cats)
            part = np.zeros(te.sum())
            for s in range(seeds):
                m = CatBoostRegressor(loss_function="Poisson", iterations=int(round(max(rep["perils"][p]["best"], 20) * 1.3)), learning_rate=lr, depth=depth,
                                      l2_leaf_reg=10, thread_count=2, random_seed=20261017 + 101 * (s0 + s), verbose=0, boost_from_average=False, one_hot_max_size=8)
                m.fit(ptr)
                part += np.exp(m.predict(pev, prediction_type="RawFormulaVal") + np.log(expo[te]) + base) * sev / seeds
            np.save(fp, part)
            del ptr, pev, m
            gc.collect()
            mu += part
            print(name, "2025", p, round(time.time() - t0), flush=True)
        rep["pred_2025_total_CU"] = round(float(mu.sum()), 2)
        pd.DataFrame({"row_id": row_ids[te], "line": line, "prediction": mu}).to_parquet(out / "prediccion_2025.parquet", index=False)
        (out / "resumen.json").write_text(json.dumps(rep, indent=1))
        print(name, "2025 total", rep["pred_2025_total_CU"], flush=True)
        return
    rep = {"line": line, "depth": depth, "lr": lr, "seeds": seeds, "f3s2": "f3s2" in opts, "perils": {}}
    mu_sel = np.zeros(sel.sum())
    best = {}
    if "desde" in opts:
        # semillas nuevas de una corrida previa: toma sus mejores iteraciones de V23 y pasa directo a V24 y 2025
        src = json.loads((WORK / opts["desde"] / "resumen.json").read_text())
        best = {p: int(src["perils"][p]["best"]) for p in per}
        rep.update({"desde": opts["desde"], "semilla_inicial": s0, "perils": {p: {"best": best[p]} for p in per}})
        (out / "resumen.json").write_text(json.dumps(rep, indent=1))
    for p, (n, yp, off) in ([] if "desde" in opts else per.items()):
        sev = yp[tr].sum() / max(n[tr].sum(), 1.0)
        base = float(np.log(n[tr].sum() / off[tr].sum()))
        fv = out / f"v23_{p}.npz"
        if fv.exists():
            z = np.load(fv)
            best[p], lam = int(z["best"]), z["lam"]
            print(name, "V23", p, "reanudado", flush=True)
        else:
            m = CatBoostRegressor(loss_function="Poisson", iterations=3000, learning_rate=lr, depth=depth, l2_leaf_reg=10, od_type="Iter", od_wait=150,
                                  thread_count=2, random_seed=20261017, verbose=0, boost_from_average=False, one_hot_max_size=8, use_best_model=True)
            m.fit(Pool(X[tr], n[tr], cat_features=cats, baseline=np.log(off[tr]) + base),
                  eval_set=Pool(X[cal], n[cal], cat_features=cats, baseline=np.log(off[cal]) + base))
            best[p] = max(int(m.get_best_iteration()) + 1, 20)
            lam = np.exp(m.predict(Pool(X[sel], cat_features=cats), prediction_type="RawFormulaVal") + np.log(off[sel]) + base)
            np.savez(fv, best=best[p], lam=lam)
            del m
            gc.collect()
        mu_sel += lam * sev
        rep["perils"][p] = {"best": best[p], "sev": round(float(sev), 2), "d2_coste_peligro_sel": round(d2(yp[sel], lam * sev), 5)}
        print(name, p, rep["perils"][p], round(time.time() - t0), flush=True)
    if "desde" not in opts:
        rep["d2_sel"] = round(d2(y[sel], mu_sel), 5)
        print(name, "V23 selección", rep["d2_sel"], flush=True)
        pd.DataFrame({"row_id": row_ids[sel], "line": line, "y": y[sel], "mu": mu_sel}).to_parquet(WORK / f"sel_{name}.parquet", index=False)
        (out / "resumen.json").write_text(json.dumps(rep, indent=1))
    if "prod" not in opts:
        return
    for tag, trm, evm, mult in (("v24", yr <= 2023, yr == 2024, 1.15), ("2025", yr <= 2024, yr == 2025, 1.3)):
        mu = np.zeros(evm.sum())
        for p, (n, yp, off) in per.items():
            fp = out / (f"v24_{p}.npy" if tag == "v24" else f"prod_{p}.npy")
            if fp.exists():
                mu += np.load(fp)
                print(name, tag, p, "reanudado", flush=True)
                continue
            sev = yp[trm].sum() / max(n[trm].sum(), 1.0)
            base = float(np.log(n[trm].sum() / off[trm].sum()))
            ptr = Pool(X[trm], n[trm], cat_features=cats, baseline=np.log(off[trm]) + base)
            pev = Pool(X[evm], cat_features=cats)
            offe = off[evm] if tag == "v24" else expo[evm]
            part = np.zeros(evm.sum())
            for s in range(seeds):
                m = CatBoostRegressor(loss_function="Poisson", iterations=int(round(best[p] * mult)), learning_rate=lr, depth=depth, l2_leaf_reg=10,
                                      thread_count=2, random_seed=20261017 + 101 * (s0 + s), verbose=0, boost_from_average=False, one_hot_max_size=8)
                m.fit(ptr)
                part += np.exp(m.predict(pev, prediction_type="RawFormulaVal") + np.log(offe) + base) * sev / seeds
                del m
            np.save(fp, part)
            mu += part
            del ptr, pev
            gc.collect()
            print(name, tag, p, round(time.time() - t0), flush=True)
        if tag == "v24":
            rep["d2_v24"] = round(d2(y[evm], mu), 5)
            pd.DataFrame({"row_id": row_ids[evm], "line": line, "y": y[evm], "mu": mu}).to_parquet(out / "v24.parquet", index=False)
            print(name, "V24", rep["d2_v24"], flush=True)
        else:
            rep["pred_2025_total_CU"] = round(float(mu.sum()), 2)
            pd.DataFrame({"row_id": row_ids[evm], "line": line, "prediction": mu}).to_parquet(out / "prediccion_2025.parquet", index=False)
        (out / "resumen.json").write_text(json.dumps(rep, indent=1))
    rep["secs"] = round(time.time() - t0)
    (out / "resumen.json").write_text(json.dumps(rep, indent=1))
    print(name, json.dumps(rep), flush=True)


if __name__ == "__main__":
    main()
