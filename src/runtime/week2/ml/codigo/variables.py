"""Shared transfer-model feature schema and phase-specific matrix loading."""
from __future__ import annotations
import numpy as np, pandas as pd
from comun import *

POLIZA = ["voluntary_excess", "channel", "payment_method", "missed_payments_12m", "new_business", "renewal_count",
          "log_days_quote", "discount_applied", "start_month", "full_year", "hist_pol_12m", "hist_cli_12m"]
CLIENTE = ["marital_status", "household_size", "prior_claims_5y", "licence_points", "years_at_address",
           "tenure_years", "age_band", "occupation"]
MARKETING = ["email_domain", "marketing_consent", "document_preference", "previous_insurer", "campaign_code",
             "branch_id", "marketing_segment"]
DIRECCION = ["urban_density", "flood_zone", "distance_to_river_km", "elevation_m", "soil_type", "property_age",
             "property_type", "roof_type", "basement", "trees_within_5m", "listed_building", "bedrooms",
             "energy_rating", "solar_panels", "clima_wind_exposure_index", "clima_wildfire_index",
             "clima_rainfall_mm", "clima_mean_temperature_c"]
RAMO = {
    "motor": ["years_licensed", "ncb_years", "vehicle_value_group", "vehicle_age", "engine_size_cc", "body_type",
              "transmission", "seats", "fuel_type", "driver_assist", "cover_type", "overnight_parking",
              "vehicle_use", "named_young_driver"],
    "buildings": ["log_si", "construction", "occupancy", "days_unoccupied", "smoke_alarms",
                  "accidental_damage_cover", "mortgage"],
    "contents": ["log_si", "tenure", "security_level", "high_value_items", "accidental_damage_cover",
                 "works_from_home", "lodgers", "bicycle_cover"],
}
SOLO_EMERGENTE = ["gender", "self_employed", "region"]
TARIFA = ["log_wp_rel"]
MAKE = ["make_model"]

CATEGORICAS = {"channel", "payment_method", "marital_status", "age_band", "occupation", "email_domain",
               "document_preference", "previous_insurer", "campaign_code", "marketing_segment", "urban_density",
               "soil_type", "property_type", "roof_type", "energy_rating", "body_type", "transmission", "fuel_type",
               "cover_type", "overnight_parking", "vehicle_use", "construction", "occupancy", "tenure",
               "security_level", "gender", "region", "make_model", "branch_id"}


def comunes(linea, marketing=False):
    return POLIZA + CLIENTE + (MARKETING if marketing else []) + DIRECCION + RAMO[linea]


def _historia(df, claims, inicio_datos):
    """Count all-status policy/customer notifications in the preceding 365 days; use NaN when the full window is unobserved."""
    lo = df.period_start - pd.Timedelta(days=365)
    ok = lo >= pd.Timestamp(inicio_datos)
    hp = claims[["policy_id", "line", "report_date"]].merge(
        df[["row_id", "policy_id", "line", "period_start"]], on=["policy_id", "line"])
    hp = hp[(hp.report_date < hp.period_start) & (hp.report_date >= hp.period_start - pd.Timedelta(days=365))]
    pol = df.row_id.map(hp.groupby("row_id").size()).fillna(0)
    return pol.where(ok, np.nan)


_cache = {}


def cargar(mercado, linea, ventana_clima):
    """Load derived features using the hasta2023 or hasta2024 weather window."""
    key = (mercado, linea, ventana_clima)
    if key in _cache:
        return _cache[key].copy()
    df = pd.read_parquet(TRABAJO / f"base_{mercado}_{linea}.parquet")
    cl = pd.read_parquet(TRABAJO / f"clima_{mercado}_{ventana_clima}.parquet")
    df = df.merge(cl, on="address_id", how="left")
    if "occupation" in df:
        df["occupation"] = df.occupation.str.lower().str.strip()
    import os  # A05 history mode 2 ends at min(start,V), affecting only 2025 rows.
    pref = "historia2" if os.environ.get("MLIND_HISTORIA") == "2" else "historia"
    hist = pd.read_parquet(TRABAJO / f"{pref}_{mercado}_{linea}.parquet")
    df = df.merge(hist, on="row_id", how="left")
    _cache[key] = df
    return df.copy()


def matriz(df, cols, categorias):
    X = pd.DataFrame(index=df.index)
    for c in cols:
        if c in CATEGORICAS:
            v = df[c].astype(str).where(df[c].notna(), None) if c in df else pd.Series(None, index=df.index)
            X[c] = pd.Categorical(v, categories=categorias[c])
        else:
            X[c] = pd.to_numeric(df[c], errors="coerce").astype(float) if c in df else np.nan
    return X


def categorias_union(frames, cols):
    out = {}
    for c in cols:
        if c in CATEGORICAS:
            vals = set()
            for f in frames:
                if c in f:
                    vals |= set(f[c].dropna().astype(str).unique())
            out[c] = sorted(vals)
    return out
