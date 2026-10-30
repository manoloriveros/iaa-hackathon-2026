"""Fit alternative developed-market transfer components under the common schema.

Variants include CatBoost Tweedie, frequency-severity, make/model and multiline
tenure, occupation exclusion, and a centered history stage. E23 variants start
boosting at the mean rate. MLIND_HISTORIA=2 ends 2025 history at min(start,V).
devhold trains developed 2021-2023 for DEV-2023 OOF, HOLD-2024 and DES24;
prodpcv trains developed 2021-2024 for PCV-2023/2024 and production-2025.
Estimate the emerging line level only on each fold's training rows.
Usage: python transfer2.py <variant> <devhold|prodpcv> [<lines>]
"""
from __future__ import annotations
import sys, time, hashlib
import numpy as np, pandas as pd, lightgbm as lgb
from comun import *
from variables import *

VAR = sys.argv[1]
FASE = sys.argv[2]
CONF = {"devhold": dict(clima="hasta2023", dev_years=[2021, 2022, 2023], mod="dev", oof=("dev", [2023]),
                        ev=("hold", [2023], 2024), des=2024),
        "prodpcv": dict(clima="hasta2024", dev_years=[2021, 2022, 2023, 2024], mod="prod", oof=("pcv", [2023, 2024]),
                        ev=("prod", [2023, 2024], 2025), des=None)}[FASE]
MOD = TRABAJO / "modelos" / CONF["mod"]
HIST = ["hist_pol_12m", "hist_cli_12m"]
TEN = ["n_lineas", "tiene_motor", "tiene_buildings", "tiene_contents"]
SEMILLA = 20261024
INICIO0 = VAR in ("T2bi", "T2ci", "T2oi", "FSi", "T2hi")  # E23 starts boosting at the mean rate.
BASE = VAR[:-1] if INICIO0 else VAR
import os
SUF = os.environ.get("MLIND_SUFIJO", "")  # E24 output suffix; saved model names remain fixed.
P_DEV = dict(objective="tweedie", tweedie_variance_power=1.5, learning_rate=0.05, num_leaves=63,
             min_data_in_leaf=1000, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0,
             max_cat_to_onehot=8, cat_smooth=50, verbose=-1, num_threads=2, seed=SEMILLA)
P_DEVB = {"motor": dict(P_DEV, learning_rate=0.03, lambda_l2=0.0, min_data_in_leaf=300),
          "buildings": dict(P_DEV, learning_rate=0.03, lambda_l2=0.0, min_data_in_leaf=3000),
          "contents": dict(P_DEV, learning_rate=0.03, lambda_l2=10.0, min_data_in_leaf=3000)}


def ajustar(X, y, off, params, max_rounds, es=150, val=None, w=None):
    """Stop on the internal validation fold, then refit on the entire training partition."""
    wt = None if w is None else w[~val]
    dtr = lgb.Dataset(X[~val], y[~val], init_score=off[~val], weight=wt, free_raw_data=False)
    dva = lgb.Dataset(X[val], y[val], init_score=off[val], weight=None if w is None else w[val], reference=dtr)
    b = lgb.train(params, dtr, max_rounds, valid_sets=[dva], callbacks=[lgb.early_stopping(es, verbose=False)])
    n = max(b.best_iteration, 1)
    b = lgb.train(params, lgb.Dataset(X, y, init_score=off, weight=w), n)
    return b, n


def ajustar0(X, y, off, params, max_rounds, es=150, val=None, w=None):
    """E23: include the log mean rate in init_score; return the fit, rounds and raw-score constant."""
    ww = np.ones(len(y)) if w is None else w
    b0 = float(np.log(np.sum(ww * y) / np.sum(ww * np.exp(off))))
    b, n = ajustar(X, y, off + b0, params, max_rounds, es=es, val=val, w=w)
    return b, n, b0


def _guardar_base(f, b0):
    guardar_json({"base": b0}, str(f) + ".base.json")


def _leer_base(f):
    import json
    return json.load(open(str(f) + ".base.json"))["base"]


def tenencia(mercado):
    b = {l: pd.read_parquet(TRABAJO / f"base_{mercado}_{l}.parquet", columns=["customer_id", "year"]) for l in LINEAS}
    cl = pd.concat([d.assign(line=l) for l, d in b.items()]).drop_duplicates()
    t = cl.assign(v=1).pivot_table(index=["customer_id", "year"], columns="line", values="v", fill_value=0)
    t.columns = [f"tiene_{c}" for c in t.columns]
    t["n_lineas"] = t.sum(axis=1)
    return t.reset_index()


def columnas(linea):
    c = comunes(linea)
    if BASE in ("T2c", "T2h"):
        c = [x for x in c if x not in HIST]
    if BASE == "T2o":
        c = [x for x in c if x != "occupation"]
    if VAR == "T2x":
        c = c + (["make_model"] if linea == "motor" else []) + TEN
    return c


# Developed-market backbone models.
def tronco_lgb(dv, cols, cats, linea, nombre):
    f = MOD / f"{nombre}_{linea}.txt"
    Xd = matriz(dv, cols, cats); offd = np.log(dv.exposure.values * dv.c_fila.values)
    if f.exists():
        b = lgb.Booster(model_file=str(f)); n = b.current_iteration()
        b0 = _leer_base(f) if INICIO0 else 0.0
    elif INICIO0:
        b, n, b0 = ajustar0(Xd, dv.y.values, offd, P_DEVB[linea], 5000, val=dv.fold.values == 0)
        b.save_model(str(f)); _guardar_base(f, b0)
    else:
        b, n = ajustar(Xd, dv.y.values, offd, P_DEVB[linea], 5000, val=dv.fold.values == 0); b0 = 0.0
        b.save_model(str(f))
    return (lambda df: b.predict(matriz(df, cols, cats), raw_score=True) + b0), {"rondas": n, "base": b0}


def tronco_cb(dv, cols, cats, linea):
    from catboost import CatBoostRegressor, Pool
    catc = [c for c in cols if c in CATEGORICAS]

    def X(df):
        o = pd.DataFrame(index=df.index)
        for c in cols:
            if c in CATEGORICAS:
                o[c] = df[c].astype(str).where(df[c].notna(), "NA")
            else:
                o[c] = pd.to_numeric(df[c], errors="coerce").astype(float)
        return o
    f = MOD / f"CB_{linea}.cbm"
    m = CatBoostRegressor()
    if f.exists():
        m.load_model(str(f)); n = m.tree_count_
    else:
        offd = np.log(dv.exposure.values * dv.c_fila.values); val = dv.fold.values == 0
        Xd = X(dv)
        prm = dict(loss_function="Tweedie:variance_power=1.5", learning_rate=0.08, depth=6, l2_leaf_reg=3.0,
                   one_hot_max_size=8, thread_count=2, random_seed=SEMILLA, verbose=0, allow_writing_files=False)
        m1 = CatBoostRegressor(iterations=3000, od_type="Iter", od_wait=100, **prm)
        m1.fit(Pool(Xd[~val], dv.y.values[~val], baseline=offd[~val], cat_features=catc),
               eval_set=Pool(Xd[val], dv.y.values[val], baseline=offd[val], cat_features=catc), use_best_model=True)
        n = max(m1.get_best_iteration() + 1, 1)
        m = CatBoostRegressor(iterations=n, **prm)
        m.fit(Pool(Xd, dv.y.values, baseline=offd, cat_features=catc))
        m.save_model(str(f))
    return (lambda df: m.predict(Pool(X(df), cat_features=catc), prediction_type="RawFormulaVal")), {"rondas": int(n)}


def tronco_fs(dv, cols, cats, linea):
    fF = MOD / f"{VAR}f_{linea}.txt"; fS = MOD / f"{VAR}s_{linea}.txt"
    if VAR == "FSt":  # E25 keeps FS frequency unchanged and uses the internally selected severity grid.
        fF = MOD / f"FSf_{linea}.txt"
    Xd = matriz(dv, cols, cats); offd = np.log(dv.exposure.values * dv.c_fila.values); val = dv.fold.values == 0
    s = (dv.n_sin.values > 0) & (dv.y.values > 0)
    msev = float(dv.y.values[s].sum() / dv.n_sin.values[s].sum())
    if VAR == "FSt":
        import json
        el = json.load(open(TRABAJO / "modelos" / "dev" / f"e25_rejilla_{linea}.json"))["elegida"]
        bf = lgb.Booster(model_file=str(fF)); nf = bf.current_iteration(); b0 = 0.0
        if fS.exists():
            bs = lgb.Booster(model_file=str(fS))
        else:
            ps = dict(objective="gamma", learning_rate=0.03, num_leaves=el["num_leaves"],
                      min_data_in_leaf=el["min_data_in_leaf"], lambda_l2=el["lambda_l2"], feature_fraction=0.8,
                      bagging_fraction=0.8, bagging_freq=1, max_cat_to_onehot=8, cat_smooth=50, verbose=-1,
                      num_threads=2, seed=SEMILLA)
            Xs = Xd[s].reset_index(drop=True); n_ = dv.n_sin.values[s].astype(float)
            bs, _ = ajustar(Xs, dv.y.values[s] / n_, np.full(s.sum(), np.log(msev)), ps, 3000, es=100, val=val[s], w=n_)
            bs.save_model(str(fS))
        ns = bs.current_iteration()
    elif fF.exists():
        bf = lgb.Booster(model_file=str(fF)); bs = lgb.Booster(model_file=str(fS))
        nf, ns = bf.current_iteration(), bs.current_iteration()
        b0 = _leer_base(fF) if INICIO0 else 0.0
    else:
        pf = {k: v for k, v in P_DEVB[linea].items() if k != "tweedie_variance_power"}
        pf["objective"] = "poisson"
        if INICIO0:
            bf, nf, b0 = ajustar0(Xd, dv.n_sin.values.astype(float), offd, pf, 5000, val=val)
            _guardar_base(fF, b0)
        else:
            bf, nf = ajustar(Xd, dv.n_sin.values, offd, pf, 5000, val=val); b0 = 0.0
        ps = dict(objective="gamma", learning_rate=0.03, num_leaves=31, min_data_in_leaf=200, feature_fraction=0.8,
                  bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, max_cat_to_onehot=8, cat_smooth=50,
                  verbose=-1, num_threads=2, seed=SEMILLA)
        Xs = Xd[s].reset_index(drop=True); n_ = dv.n_sin.values[s]
        bs, ns = ajustar(Xs, dv.y.values[s] / n_, np.full(s.sum(), np.log(msev)), ps, 5000, val=val[s], w=n_)
        bf.save_model(str(fF)); bs.save_model(str(fS))

    def raw(df):
        X = matriz(df, cols, cats)
        return bf.predict(X, raw_score=True) + b0 + bs.predict(X, raw_score=True) + np.log(msev)
    return raw, {"rondas_frec": nf, "rondas_sev": ns, "sev_media": msev, "base_frec": b0}


def tronco_fsp(dv, cols, cats, linea):
    """E21 FSp: developed-market peril Poisson frequency and gamma severity, with one emerging level per line."""
    from completitud import por_peligro
    Xd = matriz(dv, cols, cats); val = dv.fold.values == 0
    perils = sorted(c[2:] for c in dv.columns if c.startswith("n_") and c != "n_sin" and c != "n_lineas")
    modelos = {}; meta = {}
    pf = {k: v for k, v in P_DEVB[linea].items() if k != "tweedie_variance_power"}
    pf["objective"] = "poisson"
    ps = dict(objective="gamma", learning_rate=0.03, num_leaves=15, min_data_in_leaf=200, feature_fraction=0.8,
              bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, max_cat_to_onehot=8, cat_smooth=50,
              verbose=-1, num_threads=2, seed=SEMILLA)
    for p in perils:
        fF = MOD / f"FSpf_{linea}_{p}.txt"; fS = MOD / f"FSps_{linea}_{p}.txt"
        n = dv[f"n_{p}"].values; yp = dv[f"y_{p}"].values
        s = (n > 0) & (yp > 0)
        msev = float(yp[s].sum() / n[s].sum())
        if fF.exists():
            bf = lgb.Booster(model_file=str(fF)); bs = lgb.Booster(model_file=str(fS))
        else:
            cp = np.maximum(por_peligro(linea, p, dv.period_start, dv.period_end), 1e-4)
            bf, _ = ajustar(Xd, n.astype(float), np.log(dv.exposure.values * cp), pf, 5000, val=val)
            bs, _ = ajustar(Xd[s].reset_index(drop=True), yp[s] / n[s], np.full(s.sum(), np.log(msev)), ps, 3000,
                            val=val[s], w=n[s].astype(float))
            bf.save_model(str(fF)); bs.save_model(str(fS))
        modelos[p] = (bf, bs, msev)
        meta[p] = {"rondas_frec": bf.current_iteration(), "rondas_sev": bs.current_iteration(), "sev_media": msev,
                   "siniestros": int(n.sum())}
        print("  ", linea, p, meta[p], flush=True)

    def raw(df):
        X = matriz(df, cols, cats)
        tot = np.zeros(len(df))
        for p, (bf, bs, msev) in modelos.items():
            tot += np.exp(bf.predict(X, raw_score=True) + bs.predict(X, raw_score=True)) * msev
        return np.log(tot)
    return raw, {"peligros": meta}


def tronco_h(dv, cats, linea):
    """T2h: T2c plus centered history, with multiplier 1 where the history window is unobserved."""
    colsC = [x for x in comunes(linea) if x not in HIST]
    f1 = MOD / ("T2ci_%s.txt" % linea if INICIO0 else "T2c_%s.txt" % linea)
    b1 = lgb.Booster(model_file=str(f1)); base1 = _leer_base(f1) if INICIO0 else 0.0
    H = HIST + ["new_business", "renewal_count", "prior_claims_5y"]
    f = MOD / f"{VAR}_{linea}.txt"
    r1 = b1.predict(matriz(dv, colsC, cats), raw_score=True) + base1
    offd = np.log(dv.exposure.values * dv.c_fila.values)
    obs = dv.hist_pol_12m.notna().values
    XH = matriz(dv, H, cats)
    if f.exists():
        b2 = lgb.Booster(model_file=str(f)); n2 = b2.current_iteration()
    else:
        p2 = dict(objective="tweedie", tweedie_variance_power=1.5, learning_rate=0.03, num_leaves=7,
                  min_data_in_leaf=2000, lambda_l2=10.0, verbose=-1, num_threads=2, seed=SEMILLA)
        b2, n2 = ajustar(XH[obs].reset_index(drop=True), dv.y.values[obs], r1[obs] + offd[obs], p2, 3000,
                         val=(dv.fold.values == 0)[obs])
        b2.save_model(str(f))
    mu1 = np.exp(r1[obs] + offd[obs]); g = b2.predict(XH[obs], raw_score=True)
    cen = float(np.log(np.sum(mu1 * np.exp(g)) / np.sum(mu1)))

    def raw(df):
        r = b1.predict(matriz(df, colsC, cats), raw_score=True) + base1
        gg = b2.predict(matriz(df, H, cats), raw_score=True) - cen
        return r + np.where(df.hist_pol_12m.notna().values, gg, 0.0)
    return raw, {"rondas_etapa2": n2, "centrado": cen, "importancia": dict(zip(H, b2.feature_importance("gain").round(1).tolist()))}


# Phase predictions and outputs.
def nivel(a):
    return factor_tweedie(a.y.values, np.exp(a.raw.values) * a.exposure.values * a.c_fila.values)


def salidas(em, linea):
    meta = {}
    fo, anios = CONF["oof"]
    tr = em[(em.conjunto == "train") & em.year.isin(anios)]
    out, ks = [], []
    for k in range(5):
        a, b = tr[tr.fold != k], tr[tr.fold == k]
        kk = nivel(a); ks.append(kk)
        out.append(pd.DataFrame({"row_id": b.row_id.values, "mu": kk * np.exp(b.raw.values) * b.exposure.values}))
    (TRABAJO / "pred" / fo).mkdir(parents=True, exist_ok=True)
    pd.concat(out, ignore_index=True).to_parquet(TRABAJO / "pred" / fo / f"{VAR}{SUF}_{linea}.parquet", index=False)
    fe, anios_tr, anio_ev = CONF["ev"]
    a = em[(em.conjunto == "train") & em.year.isin(anios_tr)]; b = em[em.year == anio_ev]
    kk = nivel(a)
    (TRABAJO / "pred" / fe).mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"row_id": b.row_id.values, "mu": kk * np.exp(b.raw.values) * b.exposure.values}).to_parquet(
        TRABAJO / "pred" / fe / f"{VAR}{SUF}_{linea}.parquet", index=False)
    em[["row_id", "raw"]].to_parquet(TRABAJO / "pred" / fe / f"{VAR}{SUF}raw_{linea}.parquet", index=False)
    meta.update({"k_oof": ks, "k_eval": kk})
    return meta


def correr(linea):
    t0 = time.time()
    em = cargar("emerging", linea, CONF["clima"])
    dva = cargar("developed", linea, CONF["clima"])
    if VAR == "T2x":
        em = em.merge(tenencia("emerging"), on=["customer_id", "year"], how="left")
        dva = dva.merge(tenencia("developed"), on=["customer_id", "year"], how="left")
    if VAR == "FSp":
        dva = dva.merge(pd.read_parquet(TRABAJO / f"conteos_developed_{linea}.parquet"), on="row_id", how="left")
    dv = dva[dva.year.isin(CONF["dev_years"])].reset_index(drop=True)
    cols = columnas(linea)
    cats = categorias_union([dv, em], cols + HIST + ["new_business", "renewal_count", "prior_claims_5y"])
    if VAR in ("T2x", "T2o", "T2b", "T2c", "T2bi", "T2ci", "T2oi"):
        raw, meta = tronco_lgb(dv, cols, cats, linea, VAR)
    elif VAR == "CB":
        raw, meta = tronco_cb(dv, cols, cats, linea)
    elif VAR in ("FS", "FSi", "FSt"):
        raw, meta = tronco_fs(dv, cols, cats, linea)
    elif VAR == "FSp":
        raw, meta = tronco_fsp(dv, cols, cats, linea)
    elif VAR == "F0":  # Diagnostic: FS frequency times constant mean severity.
        bf = lgb.Booster(model_file=str(MOD / f"FSf_{linea}.txt"))
        s = (dv.n_sin.values > 0) & (dv.y.values > 0)
        lm = float(np.log(dv.y.values[s].sum() / dv.n_sin.values[s].sum()))
        raw, meta = (lambda df: bf.predict(matriz(df, cols, cats), raw_score=True) + lm), {"rondas_frec": bf.current_iteration()}
    elif VAR in ("T2h", "T2hi"):
        raw, meta = tronco_h(dv, cats, linea)
    else:
        raise ValueError(VAR)
    meta["s_tronco"] = round(time.time() - t0)
    # DES24: out-of-time developed structure, releveled within the evaluation year.
    if CONF["des"] is not None:
        d4 = dva[dva.year == CONF["des"]].reset_index(drop=True)
        mu = np.exp(raw(d4)) * d4.exposure.values * d4.c_fila.values
        k4 = factor_tweedie(d4.y.values, mu)
        meta["DES24"] = {"D2": d2(d4.y.values, k4 * mu), "k": k4, "n": len(d4)}
        if os.environ.get("MLIND_GUARDAR_DES24"):  # E26 saves developed-2024 raw predictions for blend-weight estimation.
            pd.DataFrame({"row_id": d4.row_id.values, "raw": np.log(mu / (d4.exposure.values * d4.c_fila.values)),
                          "y": d4.y.values, "exposure": d4.exposure.values, "c_fila": d4.c_fila.values}).to_parquet(
                TRABAJO / "pred" / "hold" / f"{VAR}{SUF}des24_{linea}.parquet", index=False)
    em = em.assign(raw=raw(em))
    if VAR not in ("T2b", "T2c") or SUF:
        meta.update(salidas(em, linea))
    meta["s"] = round(time.time() - t0)
    guardar_json(meta, TRABAJO / "pred" / CONF["ev"][0] / f"{VAR}{SUF}_{linea}_meta.json")
    print(VAR, FASE, linea, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in meta.items() if k != "importancia"}, flush=True)


if __name__ == "__main__":
    lineas = sys.argv[3].split(",") if len(sys.argv) > 3 else LINEAS
    for l in lineas:
        correr(l)
