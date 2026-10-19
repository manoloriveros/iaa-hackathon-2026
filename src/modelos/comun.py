"""Utilidades comunes de Modelos_claude: rutas, métrica, carga de matrices con variables adicionales y bloques.

Las variables adicionales respetan el corte de información del 1 de enero del año del periodo (mismo corte en
entrenamiento y test) y solo usan datos ya verificados por hash (matrices F0 D68, asignación D67, clima original).
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(os.environ.get("HAKATON_SEMANA1", "/mnt/user-data/uploads/Hakaton/Hackaton/Semana 1"))
F0RUN = "f0_20261017T141732Z_65df7fca"
F0DIR = BASE / "Matriz_F0_claude" / "runs" / F0RUN
BASESRUN = "bases_20261017T120251Z_45443ff0"
BASESDIR = BASE / "Bases_actuariales_claude" / "runs" / BASESRUN
WORK = Path(os.environ.get("MODELOS_WORK", "/home/claude/work"))
LINES = ["motor", "buildings", "contents"]
PERILS = {"motor": ["own_damage", "third_party_prop", "bodily_injury", "theft", "glass_hail"],
          "buildings": ["storm", "flood", "escape_of_water", "subsidence", "fire", "accidental_damage"],
          "contents": ["theft", "escape_of_water", "accidental_damage", "flood"]}
WEATHER_VARS = ["hail_days", "wind_exposure_index", "freezing_days", "dry_summer_index", "wildfire_index", "rainfall_mm", "mean_temperature_c"]
POWER = 1.5
NEVER = {"row_id", "policy_id", "customer_id", "address_id", "period_start", "period_end", "is_test", "year"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def deviance(y, mu, p=POWER):
    y = np.asarray(y, float)
    mu = np.asarray(mu, float)
    return 2.0 * (np.power(y, 2 - p) / ((1 - p) * (2 - p)) - y * np.power(mu, 1 - p) / (1 - p) + np.power(mu, 2 - p) / (2 - p))


def d2(y, mu, p=POWER) -> float:
    y = np.asarray(y, float)
    return float(1.0 - deviance(y, mu, p).sum() / deviance(y, np.full_like(y, y.mean()), p).sum())


def contract() -> dict:
    return json.loads((F0DIR / "contrato_disponibilidad.json").read_text(encoding="utf-8"))["columnas"]


def build_extra(line: str) -> pd.DataFrame:
    """Matriz F0 del ramo más variables adicionales F1, F2 y F4 con el corte del 1 de enero del año del periodo."""
    df = pd.read_parquet(F0DIR / "tables" / f"f0_{line}.parquet")
    a = pd.read_parquet(BASESDIR / "tables" / "asignacion_por_siniestro.parquet")
    a["report_year"] = a.report_date.dt.year.astype(int)

    # F1 por póliza y peligro: notificaciones reportadas antes del 1 de enero del año del periodo
    ap = a[a.line == line]
    parts = []
    for y in range(2021, 2026):
        prev = ap[ap.report_year < y]
        if len(prev):
            w = prev.groupby(["policy_id", "peril"]).size().unstack(fill_value=0)
            w.columns = [f"f1x_notif_{c}" for c in w.columns]
            w = w.reset_index()
            w["year"] = y
            parts.append(w)
    hist = pd.concat(parts, ignore_index=True)
    df = df.merge(hist, on=["policy_id", "year"], how="left")
    for p in PERILS[line]:
        col = f"f1x_notif_{p}"
        if col not in df.columns:
            df[col] = 0
        df[col] = df[col].fillna(0).astype("int32")

    # exposición previa observada de la póliza y tasa de notificación previa
    tr = df.loc[~df.is_test, ["policy_id", "year", "exposure"]]
    pe = tr.groupby(["policy_id", "year"])["exposure"].sum().unstack(fill_value=0.0)
    cum = pe.cumsum(axis=1).shift(1, axis=1).fillna(0.0)
    cum[2025] = pe.sum(axis=1)
    cum = cum.stack().rename("f1x_exposicion_previa").reset_index().rename(columns={"level_1": "year"})
    cum["year"] = cum["year"].astype(int)
    df = df.merge(cum, on=["policy_id", "year"], how="left")
    df["f1x_exposicion_previa"] = df["f1x_exposicion_previa"].fillna(0.0)
    df["f1x_tasa_notif_previa"] = np.where(df.f1x_exposicion_previa > 0, df.f1_notificaciones_previas / df.f1x_exposicion_previa.clip(lower=0.25), np.nan)

    # F1 por dirección (hogar): notificaciones de edificios y contenidos en la misma dirección antes del 1 de enero
    if line in ("buildings", "contents"):
        rows = pd.concat([pd.read_parquet(F0DIR / "tables" / f"f0_{l}.parquet", columns=["row_id", "address_id"]).assign(src=l) for l in ("buildings", "contents")], ignore_index=True)
        ah = a[a.line.isin(["buildings", "contents"]) & a.row_id.notna()].merge(rows[["row_id", "address_id"]], on="row_id", how="inner")
        other = "contents" if line == "buildings" else "buildings"
        parts = []
        for y in range(2021, 2026):
            prev = ah[ah.report_year < y]
            g = prev.groupby("address_id").agg(addr_notif_hogar=("claim_id", "size")).reset_index()
            o = prev[prev.line == other].groupby("address_id").agg(addr_notif_otro_ramo=("claim_id", "size")).reset_index()
            fl = prev[prev.peril.isin(["flood", "subsidence", "storm", "escape_of_water"])].groupby(["address_id", "peril"]).size().unstack(fill_value=0)
            fl.columns = [f"addr_notif_{c}" for c in fl.columns]
            g = g.merge(o, on="address_id", how="outer").merge(fl.reset_index(), on="address_id", how="outer")
            g["year"] = y
            parts.append(g)
        ad = pd.concat(parts, ignore_index=True)
        df = df.merge(ad, on=["address_id", "year"], how="left")
        for c in [c for c in df.columns if c.startswith("addr_notif_")]:
            df[c] = df[c].fillna(0).astype("int32")

    # F2: media del clima de todos los años anteriores al del periodo en la dirección
    w = pd.read_parquet(BASE / "Datos" / "weather.parquet").sort_values(["address_id", "year"])
    g = w.groupby("address_id")
    n_prev = g.cumcount()
    for v in WEATHER_VARS:
        s = g[v].cumsum() - w[v]
        w[f"{v}_mprev"] = np.where(n_prev > 0, s / n_prev.replace(0, np.nan), np.nan)
    w = w[["address_id", "year"] + [f"{v}_mprev" for v in WEATHER_VARS]]
    df = df.merge(w, on=["address_id", "year"], how="left")

    # F4: prima escrita anualizada relativa a la media del ramo en su año (sin tendencia del tarifario)
    rate = df.written_premium / df.exposure
    ymean = df.groupby("year")["written_premium"].sum() / df.groupby("year")["exposure"].sum()
    df["prem_rel"] = rate / df.year.map(ymean)
    df["log_prem_rel"] = np.log(df.prem_rel.clip(lower=1e-6))
    return df


def blocks_for(line: str, df: pd.DataFrame) -> dict:
    """Asigna cada columna candidata a un bloque; las nuevas siguen las reglas del contrato D68."""
    c = contract()[line]
    out = {}
    for col in df.columns:
        if col in NEVER or col.startswith("e_ef_"):
            continue
        if col in c:
            b = c[col]["bloque"]
        elif col.startswith("f1x_") or col.startswith("addr_notif"):
            b = "F1"
        elif col.endswith("_mprev"):
            b = "F2"
        elif col in ("prem_rel", "log_prem_rel"):
            b = "F4"
        else:
            b = "revisar"
        if b in ("F0", "F1", "F2", "F3", "F4"):
            out[col] = b
    return out


def to_model_frame(df: pd.DataFrame, feats: list[str]) -> pd.DataFrame:
    """Convierte a tipos de LightGBM sobre todas las filas del ramo a la vez, para compartir categorías entre cortes."""
    X = df[feats].copy()
    for col in X.columns:
        s = X[col]
        if isinstance(s.dtype, pd.CategoricalDtype):
            continue
        if pd.api.types.is_bool_dtype(s.dtype):
            X[col] = s.astype("float32")
        elif pd.api.types.is_numeric_dtype(s.dtype):
            if str(s.dtype).startswith(("Int", "Float")):
                X[col] = s.astype("float64")
        else:
            if pd.api.types.infer_dtype(s, skipna=True) == "boolean":
                X[col] = s.map({True: 1.0, False: 0.0}).astype("float32")
            else:
                X[col] = s.astype("category")
    return X
