"""Severidad por peligro con nivel por año (tendencia) sobre las partes guardadas de frecuencia por peligro.

Las corridas CFS (CatBoost Poisson por peligro) y FSAP (frecuencia aditiva por peligro) guardan, por peligro, la frecuencia
esperada multiplicada por la severidad media de los años de entrenamiento del corte (v23_<p>.npz con lam, v24_<p>.npy y
prod_<p>.npy). severidad_cfs.py (línea principal de Claude) les aplica una relatividad GLM gamma por capital o por valor y
antigüedad del vehículo, normalizada a media 1, y conserva el nivel de la severidad media agrupada de 2021 al último año de
entrenamiento. Este script añade una pieza: el nivel de severidad de cada peligro en el año a predecir sale de la serie
anual de severidades de entrenamiento (media recortada por año para que un siniestro aislado, como el de 11,9 millones de
lesiones de 2023, no fije el nivel), con una de estas reglas:
  pooled     : media agrupada de los años de entrenamiento (lo que hacen CFSS y FSAS; sirve de control)
  ultimo     : la severidad del último año de entrenamiento
  tendencia  : regresión log-lineal de la severidad anual sobre el año (con al menos tres años; si hay dos, el último)
               extrapolada un año, con el crecimiento anual acotado a [-15 %, +15 %]
  mixto      : media geométrica de ultimo y tendencia
  ruptura    : tendencia con detección de cambio de régimen: si algún cambio interanual de la serie supera en valor
               absoluto el tope de crecimiento (15 %), la tendencia se ajusta solo sobre el tramo posterior a la última
               ruptura (con dos puntos, el último); si no hay ruptura, igual que tendencia. Pensada para lesiones de
               autos, donde la severidad cae un 20 % en 2023 y se mantiene en 2024: extrapolar la recta de cuatro años
               prolonga una caída que ya no existe.
La relatividad por fila (capital, sótano, valor y antigüedad) es la misma de severidad_cfs.py y se ajusta igual.
Escribe WORK/<salida>/ con sel_<salida>.parquet, v24.parquet, prediccion_2025.parquet y resumen.json (formato de las
demás corridas, utilizable por mezcla3.py), más el detalle por peligro y corte de los niveles usados.
Con --frec=<json>[:<familia>] multiplica además la parte de cada peligro y corte por el factor de deriva de frecuencia
fuera de muestra calculado por factores_frec_b.py (clave "factores" del JSON, o "factores_<familia>"): V23 <- r22,
V24 <- media geométrica de r22 y r23, 2025 <- media de r23 y r24, acotados a ±15 %.
Uso: python3 severidad_tendencia.py <ramo> <salida> --regla=<pooled|ultimo|tendencia|mixto> --v23=<corrida> --v24=<c1[,c2]> --prod=<c1[,c2]> [--frec=<json>[:<familia>]]
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

import os as _os
from pathlib import Path as _Path
# código de la línea principal de Claude: carpeta hermana Modelos_claude en el repositorio, o la copia de la nube
_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
from comun import F0DIR, PERILS, WORK, d2  # noqa: E402
from severidad_cfs import glm_gamma  # noqa: E402

TRIM_Q = 0.999
CAP_GROWTH = 0.15


def nivel_anual(df, p, years):
    """Severidad media por año del peligro, con los siniestros individuales acotados al cuantil TRIM_Q de todos los años
    de entrenamiento; devuelve la serie recortada y el cociente media completa / media recortada (agrupado)."""
    n = df[f"n_{p}"].fillna(0).values.astype(float)
    yp = df[f"y_{p}"].fillna(0).values
    yr = df.year.values
    m = np.isin(yr, years) & (n > 0)
    sev_fila = yp[m] / n[m]          # coste medio por siniestro en la fila (aproximación: filas con varios siniestros se promedian)
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
        # tendencia anclada en el ajuste, no en el último punto: valor ajustado del último año por el crecimiento
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
            # la parte guardada lleva la severidad agrupada completa de los años de entrenamiento; el factor lleva el nivel
            # al objetivo manteniendo el cociente completo/recortado del agrupado
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
