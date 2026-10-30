"""Inspect E14-E18 individually and in blends in DEV OOF and exploratory HOLD.
Apply C1 by line and C2 by line/new-business with K=200. Fit convex weights
out of fold in DEV and on all DEV for HOLD. Compare fitted weights (e0), 50%
shrinkage toward equal weights (e50), and equal weights (e100).
Usage: python e14_eval.py <output.json> <candidate> [...] [--mezclas A+B+C,...]
"""
from __future__ import annotations
import sys, json
import numpy as np, pandas as pd
from comun import *
from evaluar import mezcla_pesos, metricas, bootstrap_dif, calibrar_cruzado
from receta import tabla, componentes, K_NB


def pesos(t, P, comps, il, encoge):
    M = np.column_stack([P[c][il] * t.c_fila.values[il] for c in comps])
    w = mezcla_pesos(t.y.values[il], M) if len(comps) > 1 else np.ones(1)
    return (1 - encoge) * w + encoge / len(comps)


def dev_oof(t, P, comps, encoge):
    folds = pliegue(t.customer_id.values)
    if len(comps) == 1:
        return P[comps[0]], folds
    U = np.column_stack([P[c] for c in comps]); out = np.zeros(len(t))
    for k in np.unique(folds):
        te = folds == k
        for l in LINEAS:
            il = (t.line == l).values
            w = pesos(t[~te].reset_index(drop=True), {c: P[c][~te] for c in comps}, comps, il[~te], encoge)
            out[te & il] = U[te & il] @ w
    return out, folds


def hold_pred(td, Pd, th, Ph, comps, calib, encoge):
    mu = np.zeros(len(th)); info = {}
    for l in LINEAS:
        il = (td.line == l).values; ih = (th.line == l).values
        w = pesos(td, Pd, comps, il, encoge)
        m = np.column_stack([Pd[c][il] for c in comps]) @ w * td.c_fila.values[il]
        y = td.y.values[il]; kl = factor_tweedie(y, m)
        base = np.column_stack([Ph[c][ih] for c in comps]) @ w
        if calib == "ramo":
            f = np.full(ih.sum(), kl)
        else:
            f = np.zeros(ih.sum())
            for nb in (True, False):
                s = td.new_business.values[il] == nb
                ks = factor_tweedie(y[s], m[s] * kl); n = int((y[s] > 0).sum()); z = n / (n + K_NB)
                f[th.new_business.values[ih] == nb] = kl * (z * ks + 1 - z)
        mu[ih] = base * f
        info[l] = {"pesos": dict(zip(comps, np.round(w, 4).tolist())), "k_ramo": kl}
    return mu, info


def main():
    salida = sys.argv[1]
    args = sys.argv[2:]
    mezclas = []
    if "--mezclas" in args:
        i = args.index("--mezclas"); mezclas = [m.split("+") for m in args[i + 1].split(",")]; args = args[:i]
    cands = args if "T2b" in args else ["T2b"] + args
    td = tabla("dev").merge(pd.read_parquet(TRABAJO / "pesos_2025_dev.parquet"), on="row_id", how="left")
    th = tabla("hold")
    todos = sorted(set(cands) | {c for m in mezclas for c in m} | {"T2b"})
    Pd = componentes("dev", todos, td); Ph = componentes("hold", todos, th)
    recetas = [([c], 0.0) for c in cands] + [(m, e) for m in mezclas for e in (0.0, 0.5, 1.0)]
    res = {}; preds_dev = {}; preds_hold = {}
    for comps, enc in recetas:
        nom = "+".join(comps) + ("" if len(comps) == 1 else f"_e{int(enc * 100)}")
        base, folds = dev_oof(td, Pd, comps, enc)
        r = {"sin": metricas(td, base)} if len(comps) == 1 else {}
        for calib in ("ramo", "ramo_nb"):
            md = calibrar_cruzado(td, base, folds, por_nb=(calib == "ramo_nb"), K=K_NB)
            mh, info = hold_pred(td, Pd, th, Ph, comps, calib, enc)
            preds_dev[(nom, calib)] = md; preds_hold[(nom, calib)] = mh
            r[calib] = {"dev": metricas(td, md), "hold": metricas(th, mh), "pesos_hold": info}
        res[nom] = r
        print(nom, "DEV C1 %.4f C2 %.4f w25 %.4f | HOLD C1 %.4f C2 %.4f" % (
            r["ramo"]["dev"]["D2"], r["ramo_nb"]["dev"]["D2"], r["ramo"]["dev"]["D2_w2025"],
            r["ramo"]["hold"]["D2"], r["ramo_nb"]["hold"]["D2"]), flush=True)
    # Bootstrap against T2b under the same calibration.
    boot = {}
    for (nom, calib), md in preds_dev.items():
        if nom == "T2b":
            continue
        boot[f"{nom}|{calib}"] = {
            "dev": bootstrap_dif(td, md, preds_dev[("T2b", calib)], B=1000),
            "hold": bootstrap_dif(th, preds_hold[(nom, calib)], preds_hold[("T2b", calib)], B=1000)}
    # DES24 predictions from the meta-models.
    des = {}
    for c in todos:
        for l in LINEAS:
            f = TRABAJO / "pred" / "hold" / f"{c}_{l}_meta.json"
            if f.exists():
                m = json.load(open(f))
                if "DES24" in m:
                    des.setdefault(c, {})[l] = m["DES24"]["D2"]
    guardar_json({"resultados": res, "bootstrap_vs_T2b": boot, "DES24": des}, ENTREGA / salida)
    print(json.dumps({k: {kk: [round(v["dif"], 4), [round(x, 4) for x in v["ic95"]]] for kk, v in b.items()} for k, b in boot.items()}, indent=0))
    print("DES24", json.dumps({c: {l: round(v, 4) for l, v in d.items()} for c, d in des.items()}))


if __name__ == "__main__":
    main()
