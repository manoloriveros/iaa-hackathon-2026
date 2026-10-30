"""Extend saved frequency contributions with prespecified physical severity covariates.

Fit positive-claim, count-weighted gamma GLMs by peril/cut. Apply ridge LAMBDA
only to additional covariates; leave the intercept and base insured-value,
basement, vehicle-value and vehicle-age terms unpenalized. Normalize relativities
to weighted training mean 1 before applying them to saved contributions.
Prespecified buildings features cover roof, dwelling type, urban density, flood
zone, river distance, vacancy, occupancy, soil, nearby trees, construction and
listed status as appropriate to each peril. Contents uses security, valuables,
urban density and dwelling/flood attributes. Motor uses body/fuel/engine type,
driver age, young-driver status, use, assistance and overnight parking by peril.
Categorical levels come from training; the most common is the base, missing is
explicit, and levels below MIN_NIVEL claims merge with the base. --tope=q caps
severity for slope estimation without changing the original mean-severity level.
Usage: python severidad_cfs3.py <V23_run> <line> <output_run> [--v24=c1,c2]
       [--prod=c1,c2] [--lambda=20] [--tope=q]
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import PERILS, WORK, d2
from experimentos import load

LAMBDA = 20.0
MIN_NIVEL = 30
# (type, column): num is transformed in preparar(); cat is categorical.
COV = {
    "buildings": {
        "storm": [("num", "zsi"), ("cat", "roof_type"), ("cat", "property_type"), ("cat", "urban_density")],
        "flood": [("num", "zsi"), ("num", "basement"), ("cat", "flood_zone"), ("num", "log_dist_rio"), ("cat", "property_type")],
        "escape_of_water": [("num", "zsi"), ("cat", "property_type"), ("num", "antiguedad"), ("num", "log_desocupada"), ("cat", "occupancy")],
        "subsidence": [("num", "zsi"), ("cat", "soil_type"), ("num", "arboles"), ("num", "antiguedad"), ("cat", "property_type")],
        "fire": [("num", "zsi"), ("cat", "construction_type_harmonized"), ("cat", "property_type"), ("num", "protegido"), ("num", "antiguedad")],
        "accidental_damage": [("num", "zsi"), ("cat", "property_type")],
    },
    "contents": {
        "theft": [("num", "zsi"), ("cat", "security_level"), ("num", "objetos_valor"), ("cat", "urban_density")],
        "escape_of_water": [("num", "zsi"), ("cat", "property_type"), ("num", "antiguedad")],
        "accidental_damage": [("num", "zsi"), ("num", "objetos_valor")],
        "flood": [("num", "zsi"), ("num", "basement"), ("cat", "flood_zone")],
    },
    "motor": {
        "own_damage": [("num", "zv"), ("num", "vage"), ("cat", "body_type"), ("cat", "fuel_type"), ("num", "asistencia")],
        "third_party_prop": [("num", "zv"), ("cat", "urban_density"), ("cat", "body_type"), ("num", "log_cc")],
        "bodily_injury": [("num", "edad"), ("num", "joven"), ("cat", "urban_density"), ("cat", "vehicle_use")],
        "theft": [("num", "zv"), ("num", "vage"), ("cat", "overnight_parking")],
        "glass_hail": [("num", "zv"), ("num", "vage"), ("cat", "body_type")],
    },
}


# Leave base-severity terms unpenalized so the extended model contains the base model.
LIBRES = {"buildings": {p: ("zsi",) for p in COV["buildings"]} | {"flood": ("zsi", "basement")},
          "contents": {p: ("zsi",) for p in COV["contents"]} | {"flood": ("zsi", "basement")},
          "motor": {"own_damage": ("zv", "vage"), "theft": ("zv", "vage"), "glass_hail": ("zv", "vage")}}


def glm_gamma_ridge(X, y, w, lam=LAMBDA, iters=60, libres=None):
    """Fit log-link gamma IRLS with ridge except on the intercept and free base-severity columns."""
    beta = np.zeros(X.shape[1]); beta[0] = np.log(np.average(y, weights=w))
    P = np.eye(X.shape[1]) * lam; P[0, 0] = 0.0
    for j in (libres or []):
        P[j, j] = 0.0
    for _ in range(iters):
        eta = X @ beta; mu = np.exp(eta)
        z = eta + (y - mu) / mu
        XtW = (X * w[:, None]).T
        new = np.linalg.solve(XtW @ X + P, XtW @ z)
        if np.max(np.abs(new - beta)) < 1e-9:
            return new
        beta = new
    return beta


def preparar(df, line, trm):
    """Transform numeric columns and impute missing values with cut-specific training medians."""
    out = {}
    yr = df.year.values.astype(float)

    def med(v):
        return np.nanmedian(v[trm])
    if line != "motor":
        si = df.sum_insured.astype(float).values; si = np.where(np.isfinite(si) & (si > 0), si, np.nan)
        m = med(si); out["zsi"] = np.log(np.where(np.isnan(si), m, si) / m)
        out["basement"] = df.basement.astype(float).fillna(0).values
        ant = np.clip(yr - df.year_built.astype(float).values, 0, 150); ant = np.where(np.isnan(ant), med(ant), ant)
        out["antiguedad"] = ant / 50.0
        if line == "buildings":
            d = np.log1p(df.distance_to_river_km.astype(float).values); out["log_dist_rio"] = np.where(np.isnan(d), med(d), d)
            u = np.log1p(df.days_unoccupied.astype(float).values); out["log_desocupada"] = np.where(np.isnan(u), med(u), u)
            out["arboles"] = df.trees_within_5m.astype(float).fillna(0).values
            out["protegido"] = df.listed_building.astype(float).fillna(0).values
        else:
            h = df.high_value_items.astype(float).values; out["objetos_valor"] = np.where(np.isnan(h), med(h), h)
    else:
        v = df.vehicle_value_group.astype(float).values; m = med(v); out["zv"] = np.log(np.where(np.isnan(v), m, v) / m)
        va = df.vehicle_age.astype(float).values; out["vage"] = np.clip(np.where(np.isnan(va), med(va), va), 0, 30) / 10.0
        out["asistencia"] = df.driver_assist.astype(float).fillna(0).values
        cc = np.log(df.engine_size_cc.astype(float).values / 2000.0); out["log_cc"] = np.where(np.isnan(cc), med(cc), cc)
        age = df.driver_age.astype(float).values
        out["edad"] = (age - 45.0) / 20.0
        out["joven"] = (age < 25).astype(float)
    return out


def disenio(df, nums, spec, pos, n, libres_cols=()):
    """Build a peril design matrix from training levels; return the unpenalized base-column indices too."""
    cols = [np.ones(len(df))]
    libres = []
    for kind, c in spec:
        if kind == "num":
            if c in libres_cols:
                libres.append(len(cols))
            cols.append(nums[c])
            continue
        v = df[c].astype("string").fillna("NA").values.astype(str)
        cnt = pd.Series(n[pos]).groupby(v[pos]).sum().sort_values(ascending=False)
        base = cnt.index[0]
        for lev in cnt.index[1:]:
            if cnt[lev] >= MIN_NIVEL:
                cols.append((v == lev).astype(float))
    return np.column_stack(cols), libres


def main():
    src, line, name = sys.argv[1:4]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[4:] if a.startswith("--"))
    runs_v24 = opts.get("v24", src).split(","); runs_prod = opts.get("prod", src).split(","); run_v23 = opts.get("v23", src)
    global LAMBDA
    LAMBDA = float(opts.get("lambda", LAMBDA))
    tope = float(opts["tope"]) if "tope" in opts else None
    df = load(line)
    yr = df.year.values
    folds = {"V23": (yr <= 2022, (yr == 2023) & (df.cal_half.values == 1)), "V24": (yr <= 2023, yr == 2024), "PROD": (yr <= 2024, yr == 2025)}
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    rep = {"origen": {"v23": run_v23, "v24": runs_v24, "prod": runs_prod}, "line": line, "lambda": LAMBDA, "tope": tope, "perils": {}}
    parts = {}
    for fold, (trm, evm) in folds.items():
        nums = preparar(df, line, trm)
        tot = np.zeros(evm.sum())
        for p in PERILS[line]:
            n = df[f"n_{p}"].fillna(0).values.astype(float); yp = df[f"y_{p}"].fillna(0).values
            pos = trm & (n > 0) & (yp > 0)
            X, libres = disenio(df, nums, COV[line][p], pos, n, LIBRES[line].get(p, ()))
            ys = yp[pos] / n[pos]
            if tope is not None:
                ys = np.minimum(ys, np.quantile(ys, tope))
            beta = glm_gamma_ridge(X[pos], ys, n[pos], lam=LAMBDA, libres=libres)
            rel = np.exp(X @ beta - beta[0])
            rel = rel / np.average(rel[pos], weights=n[pos])
            if fold == "V23":
                lam = np.load(WORK / run_v23 / f"v23_{p}.npz")["lam"]
                part = lam * (yp[trm].sum() / max(n[trm].sum(), 1.0))
            else:
                rr = runs_v24 if fold == "V24" else runs_prod
                part = sum(np.load(WORK / r / f"{'v24' if fold == 'V24' else 'prod'}_{p}.npy") for r in rr) / len(rr)
            assert len(part) == evm.sum()
            tot += part * rel[evm]
            rep["perils"].setdefault(p, {})[fold] = {"parametros": int(X.shape[1] - 1), "siniestros": int(n[pos].sum()),
                                                     "rel_p5_p95": [round(float(np.quantile(rel[evm], 0.05)), 3), round(float(np.quantile(rel[evm], 0.95)), 3)]}
        parts[fold] = (evm, tot)
    t0 = df["T0"].fillna(0).values; row_ids = df.row_id.astype(str).values
    evm, mu = parts["V23"]; rep["d2_sel"] = round(d2(t0[evm], mu), 5)
    pd.DataFrame({"row_id": row_ids[evm], "line": line, "y": t0[evm], "mu": mu}).to_parquet(WORK / f"sel_{name}.parquet", index=False)
    evm, mu = parts["V24"]; rep["d2_v24"] = round(d2(t0[evm], mu), 5)
    pd.DataFrame({"row_id": row_ids[evm], "line": line, "y": t0[evm], "mu": mu}).to_parquet(out / "v24.parquet", index=False)
    evm, mu = parts["PROD"]; rep["pred_2025_total_CU"] = round(float(mu.sum()), 2)
    pd.DataFrame({"row_id": row_ids[evm], "line": line, "prediction": mu}).to_parquet(out / "prediccion_2025.parquet", index=False)
    (out / "resumen.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in rep.items() if k != "perils"}, ensure_ascii=False), flush=True)
    for p, v in rep["perils"].items():
        print("  ", p, v, flush=True)


if __name__ == "__main__":
    main()
