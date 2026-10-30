"""Fit R0, emerging-only T1, transferred T2 and boosting-fine-tuned T3 trees.
DEV uses five-customer-fold 2023 OOF and developed 2021-2023 pretraining.
HOLD trains emerging 2023 for 2024 with the same developed window. Production
trains emerging 2023-2024 for 2025 with developed 2021-2024 pretraining.
Usage: python gbm.py <dev|hold|prod>
"""
from __future__ import annotations
import sys, time, hashlib, os
import numpy as np, pandas as pd, lightgbm as lgb
from comun import *
from variables import *

FASE = sys.argv[1] if len(sys.argv) > 1 else "dev"
SOLO = sys.argv[2].split(",") if len(sys.argv) > 2 else None
CONF = {"dev": dict(clima="hasta2023", dev_years=[2021, 2022, 2023], em_train=[2023], em_eval=None),
        "hold": dict(clima="hasta2023", dev_years=[2021, 2022, 2023], em_train=[2023], em_eval=2024),
        "prod": dict(clima="hasta2024", dev_years=[2021, 2022, 2023, 2024], em_train=[2023, 2024], em_eval=2025),
        "pcv": dict(clima="hasta2024", dev_years=[2021, 2022, 2023, 2024], em_train=[2023, 2024], em_eval=None)}[FASE]
OUT = TRABAJO / "pred" / FASE
OUT.mkdir(parents=True, exist_ok=True)
MOD = TRABAJO / "modelos" / {"pcv": "prod", "hold": "dev"}.get(FASE, FASE)  # Share the developed pretraining fit.
MOD.mkdir(parents=True, exist_ok=True)

P_DEV = dict(objective="tweedie", tweedie_variance_power=1.5, learning_rate=0.05, num_leaves=63,
             min_data_in_leaf=1000, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0,
             max_cat_to_onehot=8, cat_smooth=50, verbose=-1, num_threads=2, seed=20261024)
P_EM = dict(objective="tweedie", tweedie_variance_power=1.5, learning_rate=0.02, num_leaves=15,
            min_data_in_leaf=100, feature_fraction=0.7, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0,
            max_cat_to_onehot=8, cat_smooth=50, verbose=-1, num_threads=2, seed=20261024)
P_FT = dict(P_EM, learning_rate=0.01, num_leaves=7, min_data_in_leaf=200, lambda_l2=20.0)
# E07 chooses line hyperparameters using developed-market internal validation.
P_DEVB = {"motor": dict(P_DEV, learning_rate=0.03, lambda_l2=0.0, min_data_in_leaf=300),
          "buildings": dict(P_DEV, learning_rate=0.03, lambda_l2=0.0, min_data_in_leaf=3000),
          "contents": dict(P_DEV, learning_rate=0.03, lambda_l2=10.0, min_data_in_leaf=3000)}
BACKBONE = os.environ.get("MLIND_BACKBONE", "T2")


def interno(cids):
    return np.array([int(hashlib.sha256(("mlind_inner|" + c).encode()).hexdigest()[:8], 16) % 5 == 0 for c in cids])


def ajustar(X, y, off, params, max_rounds, es=200, val=None):
    """Fit with an internal customer validation mask or fixed boosting rounds."""
    if val is not None:
        dtr = lgb.Dataset(X[~val], y[~val], init_score=off[~val], free_raw_data=False)
        dva = lgb.Dataset(X[val], y[val], init_score=off[val], reference=dtr)
        b = lgb.train(params, dtr, max_rounds, valid_sets=[dva], callbacks=[lgb.early_stopping(es, verbose=False)])
        n = max(b.best_iteration, 1)
        # Refit on the full training partition using n fixed rounds.
        b = lgb.train(params, lgb.Dataset(X, y, init_score=off), n)
        return b, n
    b = lgb.train(params, lgb.Dataset(X, y, init_score=off), max_rounds)
    return b, max_rounds


def preentrenar(linea):
    """T2: fit developed-market LightGBM Tweedie using the shared feature schema."""
    f = MOD / f"T2_{linea}.txt"
    d = cargar("developed", linea, CONF["clima"])
    d = d[d.year.isin(CONF["dev_years"])]
    cols = comunes(linea)
    return d, cols, f


def correr(linea):
    t0 = time.time()
    em = cargar("emerging", linea, CONF["clima"])
    dv = cargar("developed", linea, CONF["clima"])
    dv = dv[dv.year.isin(CONF["dev_years"])].reset_index(drop=True)
    colsC = comunes(linea)
    if BACKBONE == "T2c":  # A04 excludes history features whose missingness reveals the first observed year.
        colsC = [c for c in colsC if c not in ("hist_pol_12m", "hist_cli_12m")]
    colsE = colsC + SOLO_EMERGENTE
    todas = colsE + MARKETING + TARIFA + MAKE
    cats = categorias_union([dv, em], todas)
    # T2: developed-market pretraining.
    Xd = matriz(dv, colsC, cats); yd = dv.y.values; offd = np.log(dv.exposure.values * dv.c_fila.values)
    vald = dv.fold.values == 0
    f2 = MOD / f"{BACKBONE}_{linea}.txt"
    pdev = P_DEV if BACKBONE == "T2" else P_DEVB[linea]  # T2b and T2c share E07 settings.
    if f2.exists():
        b2 = lgb.Booster(model_file=str(f2)); n2 = b2.current_iteration()
    else:
        b2, n2 = ajustar(Xd, yd, offd, pdev, 5000, es=150, val=vald)
        b2.save_model(str(f2))
    # Developed releveling is diagnostic; k2 determines the emerging-market level.
    kdev = factor_tweedie(yd, np.exp(b2.predict(Xd, raw_score=True) + offd))
    print(linea, "T2 rondas", n2, "s", round(time.time() - t0))
    imp = pd.Series(b2.feature_importance("gain"), index=colsC).sort_values(ascending=False)
    imp.to_csv(MOD / f"{BACKBONE}_{linea}_importancia.csv")
    pd.DataFrame({"row_id": em.row_id.values, "raw": b2.predict(matriz(em, colsC, cats), raw_score=True)}).to_parquet(
        OUT / f"{BACKBONE}raw_{linea}.parquet", index=False)
    # Emerging-market fits.
    tr = em[(em.conjunto == "train") & em.year.isin(CONF["em_train"])].reset_index(drop=True)
    if CONF["em_eval"] is None:
        ev_sets = [(tr[tr.fold != k], tr[tr.fold == k]) for k in range(5)]
    else:
        ev = em[em.year == CONF["em_eval"]].reset_index(drop=True)
        ev_sets = [(tr, ev)]
    variantes = {
        "T1": colsE, "T1mk": colsE + MARKETING, "T1wp": colsE + TARIFA, "T1mm": colsE + MAKE,
        "T3": colsE, "T3wp": colsE + TARIFA, "T3mk": colsE + MARKETING,
    }
    if SOLO:
        variantes = {k: v for k, v in variantes.items() if k in SOLO}
    if BACKBONE != "T2":
        variantes = {k.replace("T3", "T3b"): v for k, v in variantes.items() if k.startswith("T3")}
    res = {k: [] for k in ["R0", BACKBONE] + list(variantes)}
    rondas = {k: [] for k in variantes}
    for a, b in ev_sets:
        offa = np.log(a.exposure.values * a.c_fila.values)
        ya = a.y.values
        # R0: line ultimate rate, using a Tweedie factor over effective exposure.
        k0 = factor_tweedie(ya, np.exp(offa))
        res["R0"].append(pd.DataFrame({"row_id": b.row_id.values, "mu": k0 * b.exposure.values}))
        # T2: developed-market relativities times the emerging-market level.
        ra = b2.predict(matriz(a, colsC, cats), raw_score=True)
        rb = b2.predict(matriz(b, colsC, cats), raw_score=True)
        k2 = factor_tweedie(ya, np.exp(ra + offa))
        res[BACKBONE].append(pd.DataFrame({"row_id": b.row_id.values, "mu": k2 * np.exp(rb) * b.exposure.values}))
        val = interno(a.customer_id.values)
        for nom, cols in variantes.items():
            Xa = matriz(a, cols, cats); Xb = matriz(b, cols, cats)
            if nom.startswith("T1"):  # Only with BACKBONE T2.
                base_a = np.full(len(a), np.log(k0)); base_b = np.full(len(b), np.log(k0))
                bm, n = ajustar(Xa, ya, offa + base_a, P_EM, 3000, es=200, val=val)
            else:
                base_a = ra + np.log(k2); base_b = rb + np.log(k2)
                bm, n = ajustar(Xa, ya, offa + base_a, P_FT, 2000, es=200, val=val)
            # E02: relevel within the training fold using its Tweedie factor.
            kin = factor_tweedie(ya, np.exp(bm.predict(Xa, raw_score=True) + base_a + offa))
            mu = kin * np.exp(bm.predict(Xb, raw_score=True) + base_b) * b.exposure.values
            rondas[nom].append(n)
            res[nom].append(pd.DataFrame({"row_id": b.row_id.values, "mu": mu}))
            if CONF["em_eval"] is not None:
                (TRABAJO / "modelos" / FASE).mkdir(parents=True, exist_ok=True)
                bm.save_model(str(TRABAJO / "modelos" / FASE / f"{nom}_{linea}.txt"))
    for k, v in res.items():
        out = pd.concat(v, ignore_index=True)
        out.to_parquet(OUT / f"{k}_{linea}.parquet", index=False)
    guardar_json({"rondas": rondas, f"{BACKBONE}_rondas": n2, "k_desarrollado": kdev, "segundos": round(time.time() - t0)},
                 OUT / f"gbm_{BACKBONE}_{linea}_meta.json")
    print(linea, "listo", rondas, round(time.time() - t0), "s")


if __name__ == "__main__":
    lineas = [x for x in LINEAS if (len(sys.argv) <= 3 or x in sys.argv[3].split(","))]
    for l in lineas:
        correr(l)
