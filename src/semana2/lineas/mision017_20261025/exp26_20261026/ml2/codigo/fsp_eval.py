import sys, json
import numpy as np, pandas as pd
T = "/home/claude/ml2/trabajo"; P = "/home/claude/m017/oof/pred"
lab = pd.read_parquet("/home/claude/m017/base_etiquetas.parquet").set_index("row_id")
def dev(y, m): m = np.maximum(m, 1e-12); return 4 * y / np.sqrt(m) + 4 * np.sqrt(m) - 8 * np.sqrt(y)
def kopt(y, m): return np.sum(y / np.sqrt(m)) / np.sum(np.sqrt(m))
def d2(y, m): return 1 - dev(y, m).sum() / dev(y, np.full(len(y), y.mean())).sum()
def lev(y, m, nb):
    m = m.copy()
    for v in (False, True):
        i = nb == v
        if i.any(): m[i] *= kopt(y[i], m[i])
    return m
KP = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0
res = {}
for l in sys.argv[1].split(","):
    f = pd.read_parquet(f"{T}/pred/fsp/{l}.parquet").set_index("row_id")
    per = [c[2:] for c in f.columns if c.startswith("f_")]
    cn = pd.read_parquet(f"{T}/conteos_emerging_{l}.parquet").set_index("row_id")
    be = pd.read_parquet(f"{T}/base_emerging_{l}.parquet", columns=["row_id"] + [f"y_{p}" for p in per]).set_index("row_id")
    t2 = pd.concat([pd.read_parquet(f"{P}/dev/T2b_{l}.parquet"), pd.read_parquet(f"{P}/hold/T2b_{l}.parquet")]).set_index("row_id").mu
    idx = t2.index; L = lab.loc[idx]; y = L.y.values; nb = L.new_business.values.astype(bool); yr = L.year.values.astype(int)
    mT = t2.values * L.c_fila.values
    F_ = f.loc[idx]; N = cn.loc[idx]; Y = be.loc[idx]
    ef = {p: F_[f"f_{p}"].values * F_[f"cp_{p}"].values for p in per}   # siniestros esperados observados
    es = {p: F_[f"s_{p}"].values for p in per}
    single = sum(ef[p] * es[p] for p in per)
    r = {}
    for tr, te in ((2023, 2024), (2024, 2023)):
        a = yr == tr; b = yr == te
        # κ por peligro con credibilidad hacia el κ global del ramo
        kg = y[a].sum() / single[a].sum()
        kap = {}
        for p in per:
            n = N[f"n_{p}"].values[a].sum(); kf = n / ef[p][a].sum()
            ks = Y[f"y_{p}"].values[a].sum() / max((N[f"n_{p}"].values[a] * es[p][a]).sum(), 1e-9) if n > 0 else 1.0
            raw = kf * ks / kg; z = n / (n + KP); kap[p] = float(np.exp(z * np.log(max(raw, 1e-3))))
        rec = sum(kap[p] * ef[p] * es[p] for p in per)
        corr = rec / single
        out = {"kappa_rel": {p: round(v, 3) for p, v in kap.items()}}
        base = d2(y[b], lev(y[b], mT[b], nb[b]))
        for nm, m in (("FSp_single", single), ("FSp_recal", rec), ("T2b_x_corr", mT * corr), ("geo_T2b_recal", np.sqrt(mT * rec * (mT.sum() / rec.sum())))):
            out[nm] = round(d2(y[b], lev(y[b], m[b], nb[b])) - base, 5)
            for seg, s in (("REN", ~nb), ("NB", nb)):
                j = b & s; out[nm + "_" + seg] = round(d2(y[j], lev(y[j], m[j], nb[j])) - d2(y[j], lev(y[j], mT[j], nb[j])), 5)
        out["D2_T2b"] = round(base, 5)
        out["corr_sd_log"] = round(float(np.std(np.log(corr[b]))), 4)
        r[f"{tr}->{te}"] = out
    res[l] = r
    print(l, json.dumps(r, indent=1), flush=True)
json.dump(res, open(f"{T}/pred/fsp/eval_K{int(KP)}.json", "w"), indent=1)
