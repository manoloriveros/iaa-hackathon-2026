"""Partes por peligro de una corrida de frecuencia (CFS o FSAP) con la severidad GLM por fila y el nivel anual de
severidad por peligro (ver severidad_tendencia.py). Devuelve arrays por corte y peligro para combinarlos."""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

import os as _os
from pathlib import Path as _Path
# código de la línea principal de Claude: carpeta hermana Modelos_claude en el repositorio, o la copia de la nube
_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
from comun import F0DIR, PERILS, WORK  # noqa: E402
from severidad_cfs import glm_gamma  # noqa: E402
from severidad_tendencia import nivel_anual, nivel_objetivo  # noqa: E402

FOLDS = {"V23": [2021, 2022], "V24": [2021, 2022, 2023], "PROD": [2021, 2022, 2023, 2024]}


def marco(line):
    extra = ["sum_insured", "basement"] if line != "motor" else ["vehicle_value_group", "vehicle_age"]
    cols = ["row_id", "year", "T0", "customer_id", "exposure", "e_ef_coste"] + extra + [f"{k}_{p}" for p in PERILS[line] for k in ("n", "y")]
    df = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=cols)
    part = pd.read_parquet(F0DIR / "tables" / "particiones.parquet", columns=["row_id", "cal_half"])
    df = df.merge(part, on="row_id", how="left", validate="one_to_one")
    df["row_id"] = df.row_id.astype(str)
    return df


def mascaras(df):
    yr = df.year.values
    return {"V23": (yr <= 2022, (yr == 2023) & (df.cal_half.values == 1)), "V24": (yr <= 2023, yr == 2024), "PROD": (yr <= 2024, yr == 2025)}


def relatividades(df, line, p, trm):
    """Relatividad GLM gamma por fila (media 1 en los siniestros de entrenamiento), como severidad_cfs.py."""
    n = df[f"n_{p}"].fillna(0).values.astype(float); yp = df[f"y_{p}"].fillna(0).values
    pos = trm & (n > 0) & (yp > 0)
    if line != "motor":
        si = df.sum_insured.astype(float).values
        si = np.where(np.isfinite(si) & (si > 0), si, np.nan)
        med = np.nanmedian(si[trm])
        zsi = np.log(np.where(np.isnan(si), med, si) / med)
        covs = [zsi] + ([df.basement.astype(float).fillna(0).values] if p == "flood" else [])
    else:
        vvg = df.vehicle_value_group.astype(float).values
        vage = np.clip(df.vehicle_age.astype(float).fillna(df.vehicle_age.median()).values, 0, 30) / 10.0
        medv = np.nanmedian(vvg[trm])
        zv = np.log(np.where(np.isnan(vvg), medv, vvg) / medv)
        covs = [zv, vage] if p in ("own_damage", "theft", "glass_hail") else []
    if not covs:
        return np.ones(len(df)), []
    Z = np.column_stack(covs)
    beta = glm_gamma(Z[pos], yp[pos] / n[pos], n[pos])
    rel = np.exp(Z @ beta[1:])
    return rel / np.average(rel[pos], weights=n[pos]), [round(float(b), 4) for b in beta[1:]]


def partes_por_peligro(df, line, run_v23, runs_v24, runs_prod, regla="pooled", sustituir=None):
    """{fold: {peligro: coste esperado por fila del corte}} con relatividad GLM y nivel anual de severidad.
    sustituir: {peligro: (run_v23, [runs_v24], [runs_prod])} toma las partes de ese peligro de otra corrida."""
    out = {}
    info = {}
    sustituir = sustituir or {}
    for fold, (trm, evm) in mascaras(df).items():
        out[fold] = {}
        for p in PERILS[line]:
            rv23, rv24, rprod = sustituir.get(p, (run_v23, runs_v24, runs_prod))
            n = df[f"n_{p}"].fillna(0).values.astype(float); yp = df[f"y_{p}"].fillna(0).values
            rel, betas = relatividades(df, line, p, trm)
            serie, pooled_full, pooled_trim = nivel_anual(df, p, FOLDS[fold])
            objetivo = nivel_objetivo(serie, regla)
            factor = 1.0 if objetivo is None else float(objetivo * (pooled_full / pooled_trim) / pooled_full)
            def cargar(r23, r24, rpr):
                if fold == "V23":
                    lam = np.load(WORK / r23 / f"v23_{p}.npz")["lam"]
                    return lam * (yp[trm].sum() / max(n[trm].sum(), 1.0)), r23
                rr = r24 if fold == "V24" else rpr
                return sum(np.load(WORK / r / f"{'v24' if fold == 'V24' else 'prod'}_{p}.npy") for r in rr) / len(rr), rr
            base_part, rr = cargar(rv23, rv24, rprod)
            if p in sustituir:
                # la corrida sustituta aporta las relatividades dentro del peligro; el nivel del peligro (su total en el
                # corte) se conserva de la corrida base, para no mover la mezcla de peligros del componente
                orig, _ = cargar(run_v23, runs_v24, runs_prod)
                base_part = base_part * (orig.sum() / base_part.sum())
            assert len(base_part) == evm.sum(), (fold, p)
            out[fold][p] = base_part * rel[evm] * factor
            info.setdefault(p, {})[fold] = {"factor_nivel": round(factor, 4), "betas": betas, "origen": rr, "nivel_conservado_de_base": p in sustituir}
    return out, info
