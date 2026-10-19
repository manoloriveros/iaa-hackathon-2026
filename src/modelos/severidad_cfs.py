"""Severidad por capital asegurado para la frecuencia CatBoost por peligro (CFS), sin reentrenar la frecuencia.

La corrida CFS multiplica la frecuencia por peligro por una severidad media constante del peligro. En hogar la severidad
crece con el capital: en 2021-2023, del quintil inferior al superior de capital, inundación pasa de 20.136 a 40.027 CU por
siniestro, incendio de 29.765 a 70.601, hundimiento de 15.985 a 29.554, tormenta de 2.292 a 4.323 y escape de agua de 3.662
a 7.387; en inundación, el sótano la sube de 27.672 a 43.212. Este script ajusta por peligro y corte un GLM gamma con enlace
logarítmico sobre los siniestros positivos de los años de entrenamiento de ese corte (log del capital relativo a la mediana
y, en inundación, sótano), con peso igual al número de siniestros, y multiplica la contribución guardada de cada peligro
(frecuencia x severidad constante) por la relatividad, normalizada para que su media ponderada en los siniestros de
entrenamiento valga 1. Cortes: V23 (entrena 2021-2022, predice la mitad de selección de 2023), V24 (2021-2023, predice 2024)
y producción (2021-2024, predice 2025). Escribe una corrida nueva con el formato de las demás.
En autos la severidad crece con el grupo de valor del vehículo y baja con su antigüedad en daños propios, robo y lunas
(daños propios: de 1.417 a 2.231 CU por quintil de valor); terceros y lesiones quedan con severidad constante. En autos
se pueden combinar corridas de semillas distintas: --v23=<corrida>, --v24=<c1,c2> y --prod=<c1,c2> (promedio simple).
Con --tope=q (por ejemplo 0.995) las relatividades se estiman con la severidad por fila acotada al cuantil q de los siniestros
positivos del peligro en el entrenamiento del corte; la normalización a media 1 y la severidad media del peligro no cambian,
así que el nivel es el mismo y solo se reduce el peso de los siniestros extremos en las pendientes.
Uso: python3 severidad_cfs.py <corrida_cfs> <ramo> <corrida_salida> [--v23=..] [--v24=..] [--prod=..] [--tope=q]
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import F0DIR, PERILS, WORK, d2


def glm_gamma(Z, y, w, iters=50):
    """GLM gamma con enlace log por IRLS (con enlace log y varianza mu^2 el peso de trabajo es el peso previo)."""
    X = np.column_stack([np.ones(len(y)), Z])
    beta = np.zeros(X.shape[1]); beta[0] = np.log(np.average(y, weights=w))
    for _ in range(iters):
        eta = X @ beta; mu = np.exp(eta)
        z = eta + (y - mu) / mu
        new = np.linalg.solve((X * w[:, None]).T @ X, (X * w[:, None]).T @ z)
        if np.max(np.abs(new - beta)) < 1e-9:
            beta = new
            break
        beta = new
    return beta


def main():
    src, line, name = sys.argv[1:4]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[4:] if a.startswith("--"))
    run_v23 = opts.get("v23", src); runs_v24 = opts.get("v24", src).split(","); runs_prod = opts.get("prod", src).split(",")
    tope = float(opts["tope"]) if "tope" in opts else None
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
    folds = {"V23": (yr <= 2022, (yr == 2023) & (df.cal_half.values == 1)), "V24": (yr <= 2023, yr == 2024), "PROD": (yr <= 2024, yr == 2025)}
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    rep = {"origen": src, "line": line, "tope": tope, "perils": {}}
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
            if line != "motor":
                covs = [zsi] + ([bas] if p == "flood" else [])
            else:
                covs = [zv, vage] if p in ("own_damage", "theft", "glass_hail") else []
            if covs:
                Z = np.column_stack(covs)
                ys = yp[pos] / n[pos]
                if tope is not None:
                    ys = np.minimum(ys, np.quantile(ys, tope))
                beta = glm_gamma(Z[pos], ys, n[pos])
                rel = np.exp(Z @ beta[1:])
                rel = rel / np.average(rel[pos], weights=n[pos])
            else:
                beta = np.zeros(1); rel = np.ones(len(df))
            # contribución guardada del peligro (frecuencia x severidad constante) en el corte evaluado
            if fold == "V23":
                lam = np.load(WORK / run_v23 / f"v23_{p}.npz")["lam"]
                sev = yp[trm].sum() / max(n[trm].sum(), 1.0)
                part = lam * sev
            else:
                rr = runs_v24 if fold == "V24" else runs_prod
                part = sum(np.load(WORK / r / f"{'v24' if fold == 'V24' else 'prod'}_{p}.npy") for r in rr) / len(rr)
            assert len(part) == evm.sum()
            tot += part * rel[evm]
            rep["perils"].setdefault(p, {})[fold] = {"betas": [round(float(b), 4) for b in beta[1:]], "siniestros": int(n[pos].sum())}
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
    base = json.loads((WORK / src / "resumen.json").read_text())
    rep["referencia_cfs"] = {"d2_sel": base.get("d2_sel"), "d2_v24": base.get("d2_v24")}
    (out / "resumen.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in rep.items() if k != "perils"}, ensure_ascii=False), flush=True)
    for p, v in rep["perils"].items():
        print("  ", p, v, flush=True)


if __name__ == "__main__":
    main()
