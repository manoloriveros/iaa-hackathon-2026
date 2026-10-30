"""Apply annual peril-severity levels to saved frequency contributions.

CFS and additive FSAP runs save frequency times pooled training mean severity.
Retain the insured-value, basement and vehicle-value/age gamma relativities from
severidad_cfs.py, normalized to mean 1, and change only the target-year level.
Estimate annual severities from training data with trimming to limit single-claim
influence. Supported rules are pooled (all training years), ultimo (last year),
tendencia (log-linear annual trend, capped at +/-15%, requiring three years),
mixto (geometric mean of last-year and trend), and ruptura (fit after the latest
annual change exceeding 15%; with two points, use the last year).
Write selection, V24 and 2025 predictions, summary and peril-level diagnostics.
Optional --frec factors apply recorded out-of-sample frequency drift: V23 uses
r22, V24 the geometric mean of r22/r23, and 2025 the mean of r23/r24, capped at
15% in either direction.
Usage: python severidad_tendencia.py <line> <output> --regla=<rule>
       --v23=<run> --v24=<c1[,c2]> --prod=<c1[,c2]> [--frec=<json>[:<family>]]
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

import os as _os
from pathlib import Path as _Path
# Resolve main-model sources from the runtime binding or a sibling checkout.
_MC = _os.environ.get("MODELOS_BASE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_base", _Path("/home/participant/mc")) if p.exists()), "/home/participant/mc")
sys.path.insert(0, _MC)
from comun import F0DIR, PERILS, WORK, d2  # noqa: E402
from severidad_cfs import glm_gamma  # noqa: E402

TRIM_Q = 0.999
CAP_GROWTH = 0.15


def nivel_anual(df, p, years):
    """Return annual peril mean severity capped at training TRIM_Q, plus the pooled uncapped/capped ratio."""
    n = df[f"n_{p}"].fillna(0).values.astype(float)
    yp = df[f"y_{p}"].fillna(0).values
    yr = df.year.values
    m = np.isin(yr, years) & (n > 0)
    sev_fila = yp[m] / n[m]          # Row mean cost per claim approximates individual severity when a row has multiple claims.
    cap = np.quantile(np.repeat(sev_fila, n[m].astype(int)), TRIM_Q)
    sev_trim = np.minimum(sev_fila, cap)
    serie = {}
    for y in years:
        k = yr[m] == y
        serie[int(y)] = float(np.average(sev_trim[k], weights=n[m][k])) if n[m][k].sum() > 0 else np.nan
    pooled_full = float(yp[m].sum() / n[m].sum())
    pooled_trim = float(np.average(sev_trim, weights=n[m]))
    return serie, pooled_full, pooled_trim


def nivel_objetivo(serie, regla):
    ys = sorted(serie)
    vals = np.array([serie[y] for y in ys], float)
    if regla == "pooled":
        return None
    if regla == "ruptura":
        saltos = np.abs(np.diff(np.log(vals)))
        corte = int(np.where(saltos > np.log(1 + CAP_GROWTH))[0].max()) + 1 if (saltos > np.log(1 + CAP_GROWTH)).any() else 0
        return nivel_objetivo({y: serie[y] for y in ys[corte:]}, "tendencia")
    ultimo = vals[-1]
    if len(ys) >= 3:
        b = np.polyfit(np.array(ys, float), np.log(vals), 1)[0]
        b = float(np.clip(b, np.log(1 - CAP_GROWTH), np.log(1 + CAP_GROWTH)))
        # Anchor the trend to the fitted last-year value, then apply annual growth.
        fit = np.polyval(np.polyfit(np.array(ys, float), np.log(vals), 1), ys[-1])
        tend = float(np.exp(fit + b))
    else:
        tend = ultimo
    if regla == "ultimo":
        return ultimo
    if regla == "tendencia":
        return tend
    if regla == "mixto":
        return float(np.sqrt(ultimo * tend))
    raise SystemExit(regla)


def main():
    line, name = sys.argv[1:3]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[3:] if a.startswith("--"))
    regla = opts.get("regla", "tendencia")
    run_v23 = opts["v23"]; runs_v24 = opts["v24"].split(","); runs_prod = opts["prod"].split(",")
    frec = {}
    if "frec" in opts:
        ruta, _, familia = opts["frec"].partition(":")
        fj = json.load(open(ruta))
        frec = fj["factores_" + familia] if familia else fj["factores"]
    extra = ["sum_insured", "basement"] if line != "motor" else ["vehicle_value_group", "vehicle_age"]
    cols = ["row_id", "year", "T0"] + extra + [f"{k}_{p}" for p in PERILS[line] for k in ("n", "y")]
    df = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=cols)
    part = pd.read_parquet(F0DIR / "tables" / "particiones.parquet", columns=["row_id", "cal_half"])
    df = df.merge(part, on="row_id", how="left", validate="one_to_one")
    df["row_id"] = df.row_id.astype(str)
    yr = df.year.values
    if line != "motor":
        si = df.sum_insured.astype(float).values
        si = np.where(np.isfinite(si) & (si > 0), si, np.nan)
        bas = df.basement.astype(float).fillna(0).values
    else:
        vvg = df.vehicle_value_group.astype(float).values
        vage = np.clip(df.vehicle_age.astype(float).fillna(df.vehicle_age.median()).values, 0, 30) / 10.0
    folds = {"V23": (yr <= 2022, (yr == 2023) & (df.cal_half.values == 1), [2021, 2022]),
             "V24": (yr <= 2023, yr == 2024, [2021, 2022, 2023]),
             "PROD": (yr <= 2024, yr == 2025, [2021, 2022, 2023, 2024])}
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    rep = {"line": line, "regla": regla, "v23": run_v23, "v24": runs_v24, "prod": runs_prod, "frec": opts.get("frec"), "perils": {}}
    parts = {}
    for fold, (trm, evm, years) in folds.items():
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
            if line != "motor":
                covs = [zsi] + ([bas] if p == "flood" else [])
            else:
                covs = [zv, vage] if p in ("own_damage", "theft", "glass_hail") else []
            if covs:
                Z = np.column_stack(covs)
                beta = glm_gamma(Z[pos], yp[pos] / n[pos], n[pos])
                rel = np.exp(Z @ beta[1:])
                rel = rel / np.average(rel[pos], weights=n[pos])
            else:
                beta = np.zeros(1); rel = np.ones(len(df))
            serie, pooled_full, pooled_trim = nivel_anual(df, p, years)
            objetivo = nivel_objetivo(serie, regla)
            # Saved contributions contain uncapped pooled training severity; move their level
            # to the target while retaining the pooled uncapped/capped ratio.
            factor = 1.0 if objetivo is None else float(objetivo * (pooled_full / pooled_trim) / pooled_full)
            if fold == "V23":
                lam = np.load(WORK / run_v23 / f"v23_{p}.npz")["lam"]
                sev = yp[trm].sum() / max(n[trm].sum(), 1.0)
                base_part = lam * sev
            else:
                rr = runs_v24 if fold == "V24" else runs_prod
                base_part = sum(np.load(WORK / r / f"{'v24' if fold == 'V24' else 'prod'}_{p}.npy") for r in rr) / len(rr)
            assert len(base_part) == evm.sum(), (fold, p, len(base_part), evm.sum())
            ffrec = float(frec.get(fold, {}).get(p, 1.0))
            tot += base_part * rel[evm] * factor * ffrec
            rep["perils"].setdefault(p, {})[fold] = {"serie_recortada": {k: round(v, 1) for k, v in serie.items()}, "pooled": round(pooled_full, 1),
                                                     "objetivo_recortado": None if objetivo is None else round(objetivo, 1), "factor": round(factor, 4), "factor_frecuencia": round(ffrec, 4),
                                                     "betas": [round(float(b), 4) for b in beta[1:]], "siniestros": int(n[pos].sum())}
        parts[fold] = (evm, tot)
    t0 = df["T0"].fillna(0).values
    evm, mu = parts["V23"]
    rep["d2_sel"] = round(d2(t0[evm], mu), 5)
    pd.DataFrame({"row_id": df.row_id[evm].values, "line": line, "y": t0[evm], "mu": mu}).to_parquet(WORK / f"sel_{name}.parquet", index=False)
    evm, mu = parts["V24"]
    rep["d2_v24"] = round(d2(t0[evm], mu), 5)
    pd.DataFrame({"row_id": df.row_id[evm].values, "line": line, "y": t0[evm], "mu": mu}).to_parquet(out / "v24.parquet", index=False)
    evm, mu = parts["PROD"]
    rep["pred_2025_total_CU"] = round(float(mu.sum()), 2)
    pd.DataFrame({"row_id": df.row_id[evm].values, "line": line, "prediction": mu}).to_parquet(out / "prediccion_2025.parquet", index=False)
    (out / "resumen.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in rep.items() if k != "perils"}, ensure_ascii=False), flush=True)
    for p, v in rep["perils"].items():
        print("  ", p, {f: (w["serie_recortada"], w["objetivo_recortado"], w["factor"], w["factor_frecuencia"]) for f, w in v.items()}, flush=True)


if __name__ == "__main__":
    main()
