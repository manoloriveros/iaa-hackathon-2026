"""Diagnósticos descriptivos por ramo y peligro para orientar la selección de técnicas.

No entrena modelos ni modifica datos. Lee la capa preparada vigente a través de
current_dataset.json, comprueba los hashes del catálogo y crea una corrida nueva en runs/.
Las tablas one-way (relatividades y D² univariante) son descriptivas y en muestra: no son
resultados de validación ni de un modelo ajustado.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "RUTAS_PROYECTO.json").is_file():
            return candidate
    raise FileNotFoundError("No se encontró RUTAS_PROYECTO.json hacia arriba.")


HERE = Path(__file__).resolve()
ROOT = find_root(HERE.parent)
READER = ROOT / "Preparación/.cache/parquet-reader"
if READER.is_dir():
    sys.path.insert(0, str(READER))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pyarrow as pa  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

LINES = ["motor", "buildings", "contents"]
LINE_LABEL = {"motor": "Autos", "buildings": "Edificios", "contents": "Contenidos"}
PALETTE = {"motor": "#2a78d6", "buildings": "#eb6834", "contents": "#1baf7a"}
POWER = 1.5
EXTREME_CAPITAL = {"buildings": 10_000_000, "contents": 1_000_000}


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def jsonable(value):
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
            return None
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if value is pd.NaT:
        return None
    return value


def tweedie_deviance(y: np.ndarray, mu: np.ndarray, p: float = POWER) -> float:
    y = np.asarray(y, dtype=float)
    mu = np.asarray(mu, dtype=float)
    term = (
        np.power(y, 2 - p) / ((1 - p) * (2 - p))
        - y * np.power(mu, 1 - p) / (1 - p)
        + np.power(mu, 2 - p) / (2 - p)
    )
    return float(2 * term.sum())


def hill_estimator(values: np.ndarray, k: int) -> float | None:
    values = np.sort(np.asarray(values, dtype=float))[::-1]
    values = values[values > 0]
    if k < 30 or k >= len(values):
        return None
    top = values[: k + 1]
    logs = np.log(top[:-1]) - np.log(top[-1])
    return float(1.0 / logs.mean())


def band_numeric(series: pd.Series, q: int = 10) -> pd.Series:
    try:
        return pd.qcut(series, q=q, duplicates="drop").astype(str).fillna("<NA>")
    except ValueError:
        return series.astype(str).fillna("<NA>")


def band_categorical(series: pd.Series, top: int = 30) -> pd.Series:
    s = series.astype("string").fillna("<NA>")
    counts = s.value_counts()
    if len(counts) > top:
        keep = set(counts.index[:top])
        s = s.where(s.isin(keep), "<OTHER>")
    return s.astype(str)


def interval_left(label: str) -> float:
    """Borde izquierdo numérico de una etiqueta de intervalo de pandas; <NA> y texto van al final."""
    import re as _re

    match = _re.match(r"^[\(\[]\s*(-?[\d.]+)", str(label))
    return float(match.group(1)) if match else float("inf")


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"diag_{stamp}_{uuid.uuid4().hex[:8]}"
    out = HERE.parent / "runs" / run_id
    (out / "tables").mkdir(parents=True, exist_ok=False)
    (out / "figuras").mkdir()
    shutil.copy2(HERE, out / HERE.name)
    print("Corrida", run_id, flush=True)

    index_path = ROOT / "Hackaton/Semana 1/Limpieza/current_dataset.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    run_dir = ROOT / index["workspace_relative_run"]
    verification = json.loads((run_dir / "verification.json").read_text(encoding="utf-8"))
    if not verification.get("passed"):
        raise ValueError("La corrida de limpieza vigente no tiene verificación satisfactoria.")
    catalog_path = ROOT / index["catalog_workspace_relative"]
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    provenance = {"index": str(index_path.relative_to(ROOT)), "catalog": str(catalog_path.relative_to(ROOT)),
                  "catalog_sha256": digest(catalog_path), "files": {}}
    paths = {}
    for name, entry in catalog.items():
        path = ROOT / entry["workspace_relative_path"]
        checksum = digest(path)
        if checksum != entry["sha256"]:
            raise ValueError(f"Hash distinto al catálogo: {name}")
        provenance["files"][name] = {"path": entry["workspace_relative_path"], "sha256": checksum,
                                     "layer": entry["layer"]}
        paths[name] = path
    print("Hashes del catálogo comprobados", flush=True)

    def read(name: str, columns: list[str] | None = None) -> pd.DataFrame:
        return pq.read_table(paths[name], columns=columns).to_pandas(date_as_object=False)

    evidence: dict = {
        "run_id": run_id,
        "created_at_utc": utc_now(),
        "purpose": "Diagnósticos descriptivos para seleccionar técnicas por ramo; sin entrenamiento.",
        "valuation_date": "2024-12-31",
        "tweedie_power_reference": POWER,
        "environment": {"python": sys.version, "platform": platform.platform(), "pandas": pd.__version__,
                        "numpy": np.__version__, "pyarrow": pa.__version__,
                        "matplotlib": matplotlib.__version__},
        "provenance": provenance,
        "models_trained": False,
        "labels_materialized_for_training": False,
        "originals_modified": False,
        "human_review": "pending",
        "independent_validation": False,
    }

    # ------------------------------------------------------------------ datos
    claims = read("claims")
    claims["net"] = claims["incurred_to_date"] - claims["recoveries"]
    claims["reserve"] = claims["incurred_to_date"] - claims["paid_to_date"]
    claims["accepted"] = claims["status"] != "repudiated"
    claims["delay_days"] = (claims["report_date"] - claims["loss_date"]).dt.days
    claims["occ_year"] = claims["loss_date"].dt.year
    addresses = read("addresses")
    customers = read("customers")
    weather = read("weather")

    # Duplicados VD04: todos los campos iguales salvo claim_id
    dup_cols = [c for c in claims.columns if c not in {"claim_id", "net", "reserve", "accepted", "delay_days", "occ_year"}]
    dup_size = claims.groupby(dup_cols, dropna=False)["claim_id"].transform("size")
    dups = claims[dup_size > 1].copy()
    dups["dup_group_size"] = dup_size[dup_size > 1]
    first_in_group = ~dups.duplicated(subset=dup_cols, keep="first")
    evidence["claims_duplicates_vd04"] = {
        "definition": "Grupos de siniestros con todos los campos iguales salvo claim_id",
        "rows_involved": int(len(dups)),
        "groups": int(dups.drop_duplicates(subset=dup_cols).shape[0]),
        "extra_copies": int((~first_in_group).sum()),
        "extra_copies_accepted": int(dups.loc[~first_in_group, "accepted"].sum()),
        "extra_copies_net_cost": float(dups.loc[~first_in_group & dups["accepted"], "net"].sum()),
        "by_line_extra_copies": dups.loc[~first_in_group].groupby("line")["claim_id"].size().to_dict(),
        "by_status_extra_copies": dups.loc[~first_in_group].groupby("status")["claim_id"].size().to_dict(),
    }
    dups.sort_values(dup_cols).to_csv(out / "tables" / "siniestros_duplicados_vd04.csv", index=False)

    evidence["claims_status"] = claims.groupby(["line", "status"])["claim_id"].size().unstack(fill_value=0).to_dict("index")

    # ------------------------------------------------------- pólizas y asignación
    policies: dict[str, pd.DataFrame] = {}
    tests: dict[str, pd.DataFrame] = {}
    assignment_summary = {}
    row_cost: dict[str, pd.DataFrame] = {}
    assigned_claims: dict[str, pd.DataFrame] = {}
    for line in LINES:
        pol = read(f"policies_{line}")
        pol["year"] = pol["period_start"].dt.year
        tst = read(f"test_{line}")
        tst["year"] = tst["period_start"].dt.year
        policies[line] = pol
        tests[line] = tst
        cl = claims[claims["line"] == line].copy()
        keyed = cl[["claim_id", "policy_id", "loss_date"]].merge(
            pol[["row_id", "policy_id", "period_start", "period_end"]], on="policy_id", how="left")
        inside = (keyed["loss_date"] >= keyed["period_start"]) & (keyed["loss_date"] <= keyed["period_end"])
        hits = keyed[inside].groupby("claim_id")["row_id"].agg(["size", "first"])
        cl = cl.merge(hits.rename(columns={"size": "n_periods", "first": "row_id"}), left_on="claim_id",
                      right_index=True, how="left")
        cl["n_periods"] = cl["n_periods"].fillna(0).astype(int)
        first_start = pol.groupby("policy_id")["period_start"].min()
        cl["policy_known"] = cl["policy_id"].isin(first_start.index)
        cl["first_start"] = cl["policy_id"].map(first_start)
        cl["category"] = np.select(
            [cl["n_periods"] == 1, cl["n_periods"] > 1, ~cl["policy_known"], cl["loss_date"] < cl["first_start"]],
            ["unique", "ambiguous", "no_policy", "pre_history"], default="gap_or_after")
        cat = cl.groupby(["category", "accepted"])["claim_id"].size().unstack(fill_value=0)
        assignment_summary[line] = {
            "claims": int(len(cl)),
            "by_category": {k: {"accepted": int(v.get(True, 0)), "repudiated": int(v.get(False, 0))}
                            for k, v in cat.to_dict("index").items()},
            "net_cost_unique_accepted": float(cl.loc[(cl.category == "unique") & cl.accepted, "net"].sum()),
            "net_cost_outside_accepted": float(cl.loc[(cl.category != "unique") & cl.accepted, "net"].sum()),
        }
        assigned = cl[(cl["category"] == "unique") & cl["accepted"]].copy()
        assigned["is_pos"] = (assigned["net"] > 0).astype(int)
        assigned["is_open"] = (assigned["status"] == "open").astype(int)
        assigned_claims[line] = assigned
        agg = assigned.groupby("row_id").agg(
            n_acc=("claim_id", "size"), n_pos=("is_pos", "sum"), n_open=("is_open", "sum"), y=("net", "sum"),
            paid=("paid_to_date", "sum"), reserve=("reserve", "sum"), recov=("recoveries", "sum"))
        rc = pol.merge(agg, left_on="row_id", right_index=True, how="left")
        for c in ["n_acc", "n_pos", "n_open"]:
            rc[c] = rc[c].fillna(0).astype(int)
        for c in ["y", "paid", "reserve", "recov"]:
            rc[c] = rc[c].fillna(0.0)
        rc["pos_claims_net"] = rc["y"]
        row_cost[line] = rc
        print(line, "asignación lista", flush=True)
    evidence["claim_assignment"] = assignment_summary

    # --------------------------------------------------------- resumen por ramo
    line_summary = {}
    count_dist = {}
    for line in LINES:
        rc = row_cost[line]
        e = rc["exposure"].to_numpy(dtype=float)
        y = rc["y"].to_numpy(dtype=float)
        n = rc["n_acc"].to_numpy(dtype=float)
        lam = n.sum() / e.sum()
        expected = lam * e
        pearson = float(((n - expected) ** 2 / expected).sum() / (len(n) - 1))
        p0_obs = float((n == 0).mean())
        p0_poisson = float(np.exp(-expected).mean())
        line_summary[line] = {
            "rows": int(len(rc)), "exposure_years": float(e.sum()), "net_cost": float(y.sum()),
            "pure_premium_per_year": float(y.sum() / e.sum()),
            "claims_accepted_assigned": int(n.sum()), "frequency_accepted_per_year": float(lam),
            "frequency_positive_per_year": float(rc["n_pos"].sum() / e.sum()),
            "rows_with_zero_cost_share": float((y == 0).mean()),
            "rows_with_zero_accepted_share": p0_obs,
            "poisson_constant_rate_expected_zero_share": p0_poisson,
            "pearson_dispersion_constant_rate": pearson,
            "mean_y": float(y.mean()), "var_y": float(y.var(ddof=1)),
            "cost_share_top_1pct_rows": float(np.sort(y)[::-1][: math.ceil(0.01 * len(y))].sum() / y.sum()),
            "cost_share_top_0_1pct_rows": float(np.sort(y)[::-1][: math.ceil(0.001 * len(y))].sum() / y.sum()),
            "reserve_share_of_incurred": float(rc["reserve"].sum() / (rc["y"].sum() + rc["recov"].sum())),
            "open_claims_assigned": int(rc["n_open"].sum()),
        }
        vc = pd.Series(np.minimum(n, 3)).value_counts(normalize=True).sort_index()
        count_dist[line] = {str(int(k)) + ("+" if k == 3 else ""): float(v) for k, v in vc.items()}
    evidence["line_summary"] = line_summary
    evidence["claim_count_distribution"] = count_dist

    # cover_type en autos
    rc = row_cost["motor"]
    g = rc.groupby("cover_type").agg(rows=("row_id", "size"), exposure=("exposure", "sum"), cost=("y", "sum"),
                                     n_acc=("n_acc", "sum"), n_pos=("n_pos", "sum"))
    g["pure_premium"] = g["cost"] / g["exposure"]
    g["freq_acc"] = g["n_acc"] / g["exposure"]
    evidence["motor_by_cover_type"] = g.to_dict("index")
    # matriz cobertura x peligro (elegibilidad observada)
    mat = assigned_claims["motor"].merge(rc[["row_id", "cover_type"]], on="row_id")
    evidence["motor_cover_type_x_peril_accepted"] = mat.groupby(["cover_type", "peril"])["claim_id"].size().unstack(fill_value=0).to_dict("index")
    home_ad = {}
    for line in ["buildings", "contents"]:
        m = assigned_claims[line].merge(row_cost[line][["row_id", "accidental_damage_cover"]], on="row_id")
        home_ad[line] = m.groupby(["accidental_damage_cover", "peril"])["claim_id"].size().unstack(fill_value=0).to_dict("index")
    evidence["home_accidental_damage_cover_x_peril_accepted"] = home_ad

    # ------------------------------------------------- severidad y colas por peligro
    sev_rows = []
    acc = claims[claims["accepted"] & (claims["occ_year"].between(2021, 2024))]
    for (line, peril), grp in list(acc.groupby(["line", "peril"])) + [((line, "<todos>"), acc[acc.line == line]) for line in LINES]:
        pos = grp.loc[grp["net"] > 0, "net"].to_numpy(dtype=float)
        if len(pos) < 20:
            continue
        srt = np.sort(pos)[::-1]
        cv = pos.std(ddof=1) / pos.mean()
        alpha = 1 / cv**2
        logs = np.log(pos)
        ln_p99 = float(np.exp(logs.mean() + 2.326 * logs.std(ddof=1)))
        sev_rows.append({
            "line": line, "peril": peril, "n_positive": int(len(pos)), "net_cost": float(pos.sum()),
            "mean": float(pos.mean()), "median": float(np.median(pos)),
            "p90": float(np.quantile(pos, 0.9)), "p95": float(np.quantile(pos, 0.95)),
            "p99": float(np.quantile(pos, 0.99)), "p999": float(np.quantile(pos, 0.999)), "max": float(pos.max()),
            "cv": float(cv), "gamma_shape_from_cv": float(alpha),
            "tweedie_p_implied_by_gamma_severity": float((alpha + 2) / (alpha + 1)),
            "log_skew": float(pd.Series(logs).skew()), "log_sd": float(logs.std(ddof=1)),
            "lognormal_p99_over_empirical_p99": float(ln_p99 / np.quantile(pos, 0.99)),
            "share_top_1pct": float(srt[: math.ceil(0.01 * len(srt))].sum() / srt.sum()),
            "share_top_0_1pct": float(srt[: math.ceil(0.001 * len(srt))].sum() / srt.sum()),
            "hill_alpha_top5pct": hill_estimator(pos, int(0.05 * len(pos))),
            "hill_alpha_top2pct": hill_estimator(pos, int(0.02 * len(pos))),
            "share_open": float((grp["status"] == "open").mean()),
            "reserve_share": float(grp["reserve"].sum() / grp["incurred_to_date"].sum()),
            "claims_accepted": int(len(grp)), "zero_net_claims": int((grp["net"] <= 0).sum()),
        })
    severity = pd.DataFrame(sev_rows)
    severity.to_csv(out / "tables" / "severidad_por_peligro.csv", index=False)
    evidence["severity_by_peril"] = severity.to_dict("records")

    # ----------------------------------------- retraso de reporte y madurez por año
    delay_rows = []
    for (line, peril, year), grp in acc.groupby(["line", "peril", "occ_year"]):
        d = grp["delay_days"].to_numpy(dtype=float)
        delay_rows.append({
            "line": line, "peril": peril, "occ_year": int(year), "claims": int(len(grp)),
            "delay_median": float(np.median(d)), "delay_p90": float(np.quantile(d, 0.9)),
            "delay_p95": float(np.quantile(d, 0.95)), "delay_max": float(d.max()),
            "share_reported_within_90d": float((d <= 90).mean()),
            "share_open": float((grp["status"] == "open").mean()),
            "reserve_share": float(grp["reserve"].sum() / grp["incurred_to_date"].sum()) if grp["incurred_to_date"].sum() else None,
            "mean_net": float(grp["net"].mean()),
        })
    delays = pd.DataFrame(delay_rows)
    delays.to_csv(out / "tables" / "retraso_y_madurez_por_anio.csv", index=False)
    evidence["delay_by_peril_year"] = delays.to_dict("records")

    # severidad por banda de retraso en cohortes 2021-2022 (más maduras)
    mature = acc[acc["occ_year"] <= 2022].copy()
    mature["delay_band"] = pd.cut(mature["delay_days"], [-1, 7, 30, 90, 180, 365, 10_000],
                                  labels=["0-7", "8-30", "31-90", "91-180", "181-365", ">365"])
    sev_delay = mature.groupby(["line", "peril", "delay_band"], observed=True).agg(
        claims=("claim_id", "size"), mean_net=("net", "mean"), median_net=("net", "median"),
        share_open=("status", lambda s: float((s == "open").mean()))).reset_index()
    sev_delay.to_csv(out / "tables" / "severidad_por_banda_retraso_2021_2022.csv", index=False)
    evidence["severity_by_delay_band_2021_2022"] = sev_delay.astype({"delay_band": str}).to_dict("records")

    # ------------------------------------------- frecuencia por año de ocurrencia
    freq_year = []
    for line in LINES:
        rc = row_cost[line]
        exp_year = rc.groupby("year")["exposure"].sum()
        a = assigned_claims[line]
        for year, e in exp_year.items():
            sub = a[a["occ_year"] == year]
            freq_year.append({
                "line": line, "year": int(year), "exposure": float(e), "rows": int((rc["year"] == year).sum()),
                "claims_accepted": int(len(sub)), "freq_accepted": float(len(sub) / e),
                "freq_reported_within_90d": float((sub["delay_days"] <= 90).sum() / e),
                "pure_premium": float(sub["net"].sum() / e),
                "share_open": float((sub["status"] == "open").mean()) if len(sub) else None,
                "mean_net": float(sub["net"].mean()) if len(sub) else None,
            })
    freq_year = pd.DataFrame(freq_year)
    freq_year.to_csv(out / "tables" / "frecuencia_por_anio.csv", index=False)
    evidence["frequency_by_year"] = freq_year.to_dict("records")

    # ------------------------------------------ estacionalidad y eventos comunes
    season = acc.assign(month=acc["loss_date"].dt.month).groupby(["line", "peril", "month"])["claim_id"].size()
    season = season.groupby(level=[0, 1]).transform(lambda s: s / s.sum()).reset_index(name="share")
    season.to_csv(out / "tables" / "estacionalidad_mensual.csv", index=False)
    events = []
    addr_region = addresses.set_index("address_id")["region"]
    for line, peril in [("buildings", "storm"), ("buildings", "flood"), ("contents", "flood"), ("motor", "glass_hail")]:
        sub = assigned_claims[line][assigned_claims[line]["peril"] == peril].merge(
            row_cost[line][["row_id", "address_id"]], on="row_id")
        sub["region"] = sub["address_id"].map(addr_region)
        daily = sub.groupby("loss_date").agg(claims=("claim_id", "size"), net=("net", "sum"),
                                             top_region_share=("region", lambda s: float(s.value_counts(normalize=True).iloc[0])))
        daily = daily.sort_values("claims", ascending=False)
        top = daily.head(10)
        events.append({
            "line": line, "peril": peril, "days_with_claims": int(len(daily)), "claims": int(daily["claims"].sum()),
            "top10_days_share_of_claims": float(top["claims"].sum() / daily["claims"].sum()),
            "top10_days_share_of_cost": float(top["net"].sum() / daily["net"].sum()),
            "max_claims_single_day": int(daily["claims"].max()),
            "median_claims_per_day": float(daily["claims"].median()),
            "top10_days": [{"loss_date": str(idx.date()), "claims": int(r.claims), "net": float(r.net),
                            "top_region_share": float(r.top_region_share)} for idx, r in top.iterrows()],
        })
    evidence["event_clustering"] = events

    # ------------------------------------------------------------ duración
    dur_rows = []
    for line in LINES:
        rc = row_cost[line].copy()
        rc["exp_band"] = pd.cut(rc["exposure"], [0, 0.25, 0.5, 0.75, 0.99, 1.01], labels=["(0,0.25]", "(0.25,0.5]", "(0.5,0.75]", "(0.75,0.99]", "año completo"])
        rows_per_policy_year = rc.groupby(["policy_id", "year"])["row_id"].transform("size")
        rc["mid_term"] = rows_per_policy_year > 1
        for key, name in [("exp_band", "exposure_band"), ("mid_term", "mid_term_change"), ("new_business", "new_business")]:
            g = rc.groupby(key, observed=True).agg(rows=("row_id", "size"), exposure=("exposure", "sum"),
                                                   n_acc=("n_acc", "sum"), cost=("y", "sum"))
            for k, r in g.iterrows():
                dur_rows.append({"line": line, "dimension": name, "level": str(k), "rows": int(r.rows),
                                 "exposure": float(r.exposure), "freq_accepted": float(r.n_acc / r.exposure),
                                 "pure_premium": float(r.cost / r.exposure)})
        tst = tests[line]
        tst_band = pd.cut(tst["exposure"], [0, 0.25, 0.5, 0.75, 0.99, 1.01]).value_counts(normalize=True).sort_index()
        for k, v in tst_band.items():
            dur_rows.append({"line": line, "dimension": "test_exposure_band_share", "level": str(k), "rows": None,
                             "exposure": None, "freq_accepted": None, "pure_premium": float(v)})
    duration = pd.DataFrame(dur_rows)
    duration.to_csv(out / "tables" / "duracion_y_endosos.csv", index=False)
    evidence["duration"] = duration.to_dict("records")

    # ------------------------------------------------- Taylor / potencia Tweedie
    def taylor(line: str, keys: list[str], frame: pd.DataFrame, min_n: int) -> dict:
        full = frame[(frame["exposure"] >= 0.98) & (frame["exposure"] <= 1.03)]
        cells = full.groupby(keys, observed=True)["y"].agg(["size", "mean", "var"]).reset_index()
        cells = cells[(cells["size"] >= min_n) & (cells["mean"] > 0) & (cells["var"] > 0)]
        if len(cells) < 10:
            return {"cells": int(len(cells)), "slope_p": None}
        x = np.log(cells["mean"].to_numpy()); z = np.log(cells["var"].to_numpy()); w = cells["size"].to_numpy(dtype=float)
        X = np.column_stack([np.ones_like(x), x])
        W = np.sqrt(w)
        beta, *_ = np.linalg.lstsq(X * W[:, None], z * W, rcond=None)
        resid = z - X @ beta
        r2 = 1 - float((w * resid**2).sum() / (w * (z - np.average(z, weights=w)) ** 2).sum())
        return {"cells": int(len(cells)), "rows_full_year": int(full.shape[0]), "min_rows_per_cell": min_n,
                "slope_p": float(beta[1]), "intercept_log_phi": float(beta[0]), "weighted_r2": r2,
                "keys": keys, "cells_table": cells.assign(**{k: cells[k].astype(str) for k in keys}).to_dict("records")}

    taylor_out = {}
    mot = row_cost["motor"].merge(addresses[["address_id", "region"]], on="address_id", how="left")
    mot["age_band"] = pd.cut(mot["driver_age"], [16, 25, 35, 45, 55, 65, 120]).astype(str)
    mot["value_band"] = pd.cut(mot["vehicle_value_group"], [0, 5, 10, 15, 20]).astype(str)
    taylor_out["motor"] = taylor("motor", ["year", "region", "cover_type", "age_band", "value_band"], mot, 300)
    bld = row_cost["buildings"].merge(addresses[["address_id", "region", "property_type"]], on="address_id", how="left")
    bld["si_band"] = band_numeric(bld["sum_insured"], 5)
    bld["age_band"] = pd.cut(bld["policyholder_age"], [16, 30, 40, 50, 60, 70, 120]).astype(str)
    taylor_out["buildings"] = taylor("buildings", ["year", "region", "property_type", "construction_type", "si_band"], bld, 300)
    cnt = row_cost["contents"].merge(addresses[["address_id", "region"]], on="address_id", how="left")
    cnt["si_band"] = band_numeric(cnt["sum_insured"], 5)
    taylor_out["contents"] = taylor("contents", ["year", "region", "tenure", "security_level", "si_band"], cnt, 300)
    evidence["taylor_power_law"] = {k: {kk: vv for kk, vv in v.items() if kk != "cells_table"} for k, v in taylor_out.items()}
    for line, res in taylor_out.items():
        if res.get("cells_table"):
            pd.DataFrame(res["cells_table"]).to_csv(out / "tables" / f"taylor_celdas_{line}.csv", index=False)

    # -------------------------------------------- one-way: relatividades y D² univariante
    def one_way(frame: pd.DataFrame, col: str, kind: str) -> dict | None:
        s = frame[col]
        if s.isna().all():
            return None
        if kind == "numeric":
            band = band_numeric(s, 10)
        elif kind == "bool":
            band = s.astype("string").fillna("<NA>").astype(str).fillna("<NA>")
        else:
            band = band_categorical(s)
        e = frame["exposure"].to_numpy(dtype=float); y = frame["y"].to_numpy(dtype=float)
        n = frame["n_acc"].to_numpy(dtype=float)
        tmp = pd.DataFrame({"band": band.to_numpy(), "e": e, "y": y, "n": n})
        g = tmp.groupby("band").agg(rows=("e", "size"), e=("e", "sum"), y=("y", "sum"), n=("n", "sum"))
        g["rate"] = g["y"] / g["e"]; g["freq"] = g["n"] / g["e"]
        rate_total = y.sum() / e.sum()
        mu = e * tmp["band"].map(g["rate"]).to_numpy(dtype=float)
        mu0 = e * rate_total
        dev_model = tweedie_deviance(y, np.maximum(mu, 1e-12)); dev0 = tweedie_deviance(y, mu0)
        dev_mean = tweedie_deviance(y, np.full_like(y, y.mean()))
        g["relativity"] = g["rate"] / rate_total
        g["exposure_share"] = g["e"] / e.sum()
        if kind == "numeric":
            g = g.loc[sorted(g.index, key=interval_left)]
        return {"column": col, "kind": kind, "levels": int(len(g)),
                "d2_oneway_vs_constant_rate": 1 - dev_model / dev0,
                "d2_oneway_vs_constant_mean": 1 - dev_model / dev_mean,
                "relativity_min": float(g["relativity"].min()), "relativity_max": float(g["relativity"].max()),
                "exposure_weighted_abs_log_relativity": float((g["exposure_share"] * np.abs(np.log(g["relativity"].clip(lower=1e-9)))).sum()),
                "bands": g.reset_index().assign(band=lambda d: d["band"].astype(str)).to_dict("records")}

    skip = {"row_id", "policy_id", "customer_id", "address_id", "period_start", "period_end", "exposure", "year",
            "renewal_decision", "n_acc", "n_pos", "n_open", "y", "paid", "reserve", "recov", "pos_claims_net",
            "surname", "date_of_birth", "email_domain", "exp_band", "mid_term", "age_band", "value_band", "si_band",
            "region_x", "region_y"}
    blocks = {"F4": {"written_premium", "discount_applied"},
              "F3": {"customer_service_contacts", "missed_payments_12m", "telematics_score", "telematics_opt_in",
                     "days_unoccupied", "occupation", "marital_status", "household_size", "credit_band",
                     "licence_points", "years_at_address", "marketing_consent", "document_preference",
                     "previous_insurer", "campaign_code", "branch_id", "marketing_segment", "customer_since_year",
                     "prior_claims_5y"}}
    oneway_all = []
    for line in LINES:
        frame = row_cost[line].merge(addresses, on="address_id", how="left").merge(
            customers, on="customer_id", how="left", suffixes=("", "_cust"))
        wx = weather.rename(columns={c: f"wx_{c}" for c in weather.columns if c not in {"address_id", "year"}})
        frame = frame.merge(wx, on=["address_id", "year"], how="left")
        wx_lag = wx.copy(); wx_lag["year"] = wx_lag["year"] + 1
        wx_lag = wx_lag.rename(columns={c: c.replace("wx_", "wxlag1_") for c in wx_lag.columns if c.startswith("wx_")})
        frame = frame.merge(wx_lag, on=["address_id", "year"], how="left")
        for col in frame.columns:
            if col in skip or col.endswith("_cust"):
                continue
            s = frame[col]
            if pd.api.types.is_bool_dtype(s):
                kind = "bool"
            elif pd.api.types.is_numeric_dtype(s):
                kind = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(s):
                continue
            else:
                kind = "categorical"
            res = one_way(frame, col, kind)
            if res is None:
                continue
            block = "F2_same_year" if col.startswith("wx_") else "F2_lag1" if col.startswith("wxlag1_") else \
                "F4" if col in blocks["F4"] else "F3" if col in blocks["F3"] else "F0"
            res.update({"line": line, "block": block})
            oneway_all.append(res)
        print(line, "one-way listo", flush=True)
    oneway_df = pd.DataFrame([{k: v for k, v in r.items() if k != "bands"} for r in oneway_all])
    oneway_df.sort_values(["line", "d2_oneway_vs_constant_rate"], ascending=[True, False]).to_csv(
        out / "tables" / "oneway_d2_univariante.csv", index=False)
    pd.DataFrame([{**{"line": r["line"], "column": r["column"], "block": r["block"]}, **b}
                  for r in oneway_all for b in r["bands"]]).to_csv(out / "tables" / "oneway_bandas.csv", index=False)
    evidence["oneway_d2"] = oneway_df.to_dict("records")

    # ------------------------------------------------ cardinalidad y cobertura test
    card_rows = []
    for line in LINES:
        tr = policies[line]; te = tests[line]
        for col in tr.columns:
            if col in skip or col in {"renewal_decision"} or col not in te.columns:
                continue
            s = tr[col]
            if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
                continue
            lv_tr = set(s.dropna().astype(str)); lv_te = set(te[col].dropna().astype(str))
            unseen = lv_te - lv_tr
            share_unseen = float(te[col].astype(str).isin(unseen).mean()) if unseen else 0.0
            vc = s.astype(str).value_counts(normalize=True)
            card_rows.append({"line": line, "column": col, "levels_train": len(lv_tr), "levels_test": len(lv_te),
                              "unseen_levels_in_test": len(unseen), "test_rows_share_unseen": share_unseen,
                              "top_level_share": float(vc.iloc[0]), "null_share_train": float(s.isna().mean()),
                              "null_share_test": float(te[col].isna().mean())})
    card = pd.DataFrame(card_rows)
    card.to_csv(out / "tables" / "cardinalidad_categoricas.csv", index=False)
    evidence["categorical_cardinality"] = card.to_dict("records")

    # ------------------------------------------------------- clima: mismo año vs rezago
    wx_rows = []
    for line, peril in [("buildings", "flood"), ("buildings", "storm"), ("buildings", "escape_of_water"),
                        ("contents", "flood"), ("motor", "glass_hail")]:
        rc = row_cost[line]
        a = assigned_claims[line][assigned_claims[line]["peril"] == peril].groupby("row_id")["claim_id"].size()
        fr = rc[["row_id", "address_id", "year", "exposure"]].copy()
        fr["n_peril"] = fr["row_id"].map(a).fillna(0)
        for lag, label in [(0, "same_year"), (1, "lag1")]:
            w = weather.copy(); w["year"] = w["year"] + lag
            m = fr.merge(w, on=["address_id", "year"], how="left")
            for var in ["rainfall_mm", "wind_exposure_index", "hail_days", "freezing_days", "dry_summer_index"]:
                band = band_numeric(m[var], 10)
                g = m.assign(band=band).groupby("band").agg(e=("exposure", "sum"), n=("n_peril", "sum"))
                g["freq"] = g["n"] / g["e"]
                g = g.loc[sorted(g.index, key=interval_left)]
                known = g[g.index != "<NA>"]
                wx_rows.append({"line": line, "peril": peril, "weather": label, "variable": var,
                                "freq_min_decile": float(known["freq"].min()), "freq_max_decile": float(known["freq"].max()),
                                "ratio_max_min": float(known["freq"].max() / max(known["freq"].min(), 1e-12)),
                                "freq_lowest_decile": float(known["freq"].iloc[0]), "freq_highest_decile": float(known["freq"].iloc[-1]),
                                "ratio_highest_over_lowest": float(known["freq"].iloc[-1] / max(known["freq"].iloc[0], 1e-12)),
                                "spearman_decile_vs_freq": float(pd.Series(range(len(known))).corr(known["freq"].reset_index(drop=True), method="spearman")),
                                "deciles": g.reset_index().assign(band=lambda d: d["band"].astype(str)).to_dict("records")})
    wxdf = pd.DataFrame([{k: v for k, v in r.items() if k != "deciles"} for r in wx_rows])
    wxdf.to_csv(out / "tables" / "clima_mismo_anio_vs_rezago.csv", index=False)
    evidence["weather_lag_comparison"] = wx_rows
    fz = row_cost["buildings"].merge(addresses[["address_id", "flood_zone"]], on="address_id", how="left")
    fl = assigned_claims["buildings"][assigned_claims["buildings"]["peril"] == "flood"].groupby("row_id")["net"].agg(["size", "sum"])
    fz = fz.merge(fl, left_on="row_id", right_index=True, how="left").fillna({"size": 0, "sum": 0.0})
    g = fz.groupby("flood_zone", dropna=False).agg(e=("exposure", "sum"), n=("size", "sum"), cost=("sum", "sum"))
    g["freq"] = g["n"] / g["e"]; g["pure_premium"] = g["cost"] / g["e"]
    evidence["buildings_flood_by_flood_zone"] = g.reset_index().assign(flood_zone=lambda d: d["flood_zone"].astype(str)).to_dict("records")

    # ------------------------------------------------------ multirramo y dependencia
    cust_lines = pd.concat([policies[l][["customer_id"]].assign(line=l) for l in LINES]).drop_duplicates()
    per_cust = cust_lines.groupby("customer_id")["line"].size().value_counts().sort_index()
    addr_lines = pd.concat([policies[l][["address_id"]].assign(line=l) for l in LINES]).drop_duplicates()
    per_addr = addr_lines.groupby("address_id")["line"].size().value_counts().sort_index()
    bc = row_cost["buildings"][["address_id", "year", "n_acc"]].groupby(["address_id", "year"])["n_acc"].sum().rename("b")
    cc = row_cost["contents"][["address_id", "year", "n_acc"]].groupby(["address_id", "year"])["n_acc"].sum().rename("c")
    both = pd.concat([bc, cc], axis=1, join="inner")
    p_c = float((both["c"] > 0).mean()); p_c_given_b = float((both.loc[both["b"] > 0, "c"] > 0).mean())
    mb = row_cost["motor"][["customer_id", "year", "n_acc"]].groupby(["customer_id", "year"])["n_acc"].sum().rename("m")
    bb = row_cost["buildings"][["customer_id", "year", "n_acc"]].groupby(["customer_id", "year"])["n_acc"].sum().rename("b")
    both2 = pd.concat([mb, bb], axis=1, join="inner")
    evidence["multi_line"] = {
        "customers_by_number_of_lines": {str(k): int(v) for k, v in per_cust.items()},
        "addresses_by_number_of_lines": {str(k): int(v) for k, v in per_addr.items()},
        "address_years_with_buildings_and_contents": int(len(both)),
        "p_contents_claim": p_c, "p_contents_claim_given_buildings_claim": p_c_given_b,
        "lift_contents_given_buildings": p_c_given_b / p_c if p_c else None,
        "customer_years_with_motor_and_buildings": int(len(both2)),
        "p_buildings_claim": float((both2["b"] > 0).mean()),
        "p_buildings_claim_given_motor_claim": float((both2.loc[both2["m"] > 0, "b"] > 0).mean()),
    }

    # ------------------------------------------------ capital, ratio de daño y extremos
    cap = {}
    for line in ["buildings", "contents"]:
        rc = row_cost[line]
        thr = EXTREME_CAPITAL[line]
        ext_train = int((rc["sum_insured"] > thr).sum()); ext_test = int((tests[line]["sum_insured"] > thr).sum())
        a = assigned_claims[line].merge(rc[["row_id", "sum_insured"]], on="row_id")
        a = a[(a["sum_insured"] <= thr) & (a["net"] > 0)]
        a["damage_ratio"] = a["net"] / a["sum_insured"]
        dr = a.groupby("peril")["damage_ratio"].describe(percentiles=[0.5, 0.9, 0.99]).reset_index()
        cap[line] = {"extreme_rows_train_above_threshold": ext_train, "extreme_rows_test_above_threshold": ext_test,
                     "threshold": thr, "damage_ratio_by_peril": dr.to_dict("records"),
                     "claims_above_capital": int((a["damage_ratio"] > 1).sum())}
    evidence["capital"] = cap

    # ------------------------------------ variables operativas: train frente a test 2025
    operational = {}
    for line in LINES:
        tr = policies[line]; te = tests[line]
        cols = ["customer_service_contacts", "missed_payments_12m"] + (["telematics_opt_in", "telematics_score"] if line == "motor" else ["days_unoccupied"] if line == "buildings" else [])
        operational[line] = {}
        for col in cols:
            if col not in tr.columns:
                continue
            if col == "telematics_score":
                operational[line][col] = {"train_nonnull_share": float(tr[col].notna().mean()), "test_nonnull_share": float(te[col].notna().mean()),
                                          "train_mean": float(tr[col].mean()), "test_mean": float(te[col].mean())}
            else:
                vt = tr[col].astype(float).clip(upper=3).value_counts(normalize=True).sort_index()
                ve = te[col].astype(float).clip(upper=3).value_counts(normalize=True).sort_index()
                operational[line][col] = {"train_share_by_value_capped_3": {str(k): float(v) for k, v in vt.items()},
                                          "test_share_by_value_capped_3": {str(k): float(v) for k, v in ve.items()}}
        rc = row_cost[line]
        g = rc.assign(c=rc["customer_service_contacts"].clip(upper=3)).groupby("c").agg(rows=("row_id", "size"), e=("exposure", "sum"), n=("n_acc", "sum"), y=("y", "sum"))
        g["freq"] = g["n"] / g["e"]; g["share_rows_with_claim"] = rc.assign(c=rc["customer_service_contacts"].clip(upper=3), has=rc["n_acc"] > 0).groupby("c")["has"].mean()
        operational[line]["contacts_vs_claims_train"] = g.reset_index().to_dict("records")
    evidence["operational_variables_train_vs_test"] = operational

    # ------------------------------ frecuencia controlada por truncamiento y tendencia de severidad
    trend_rows = []
    for line in LINES:
        rc = row_cost[line]; a = assigned_claims[line]
        for year in [2021, 2022, 2023, 2024]:
            sub_rows = rc[(rc["year"] == year)]
            cutoff = pd.Timestamp(year=year, month=9, day=30)
            # exposición de los periodos del año hasta el 30 de septiembre (aproximación por días cubiertos)
            start = sub_rows["period_start"].clip(lower=pd.Timestamp(year=year, month=1, day=1))
            end = sub_rows["period_end"].clip(upper=cutoff)
            days = (end - start).dt.days + 1
            e_q = float(days.clip(lower=0).sum() / 365)
            cl = a[(a["occ_year"] == year) & (a["loss_date"] <= cutoff) & (a["delay_days"] <= 60)]
            closed = a[(a["occ_year"] == year) & (a["status"] == "closed")]
            trend_rows.append({"line": line, "year": year, "exposure_jan_sep": e_q,
                               "claims_jan_sep_reported_within_60d": int(len(cl)), "freq_jan_sep_reported_within_60d": float(len(cl) / e_q),
                               "closed_claims_mean_net": float(closed["net"].mean()), "closed_claims_median_net": float(closed["net"].median()),
                               "closed_claims": int(len(closed))})
    trend = pd.DataFrame(trend_rows)
    trend.to_csv(out / "tables" / "tendencia_frecuencia_severidad.csv", index=False)
    evidence["trend_truncation_controlled"] = trend.to_dict("records")

    # ------------------------------------------- historia previa conocida al inicio (F1 descriptivo)
    history = {}
    all_claims = pd.concat([assigned_claims[l].assign(line=l) for l in LINES])
    for line in LINES:
        rc = row_cost[line][["row_id", "policy_id", "customer_id", "period_start", "exposure", "n_acc", "y"]].copy()
        cl = assigned_claims[line][["policy_id", "loss_date", "report_date"]]
        m = rc[["row_id", "policy_id", "period_start"]].merge(cl, on="policy_id", how="inner")
        known = m[(m["report_date"] < m["period_start"])].groupby("row_id").size()
        rc["prior_known_claims_policy"] = rc["row_id"].map(known).fillna(0).clip(upper=2)
        cust_claims = all_claims.merge(pd.concat([policies[l][["policy_id", "customer_id"]] for l in LINES]).drop_duplicates(), on="policy_id", how="left")
        mc = rc[["row_id", "customer_id", "period_start"]].merge(cust_claims[["customer_id", "report_date", "line"]], on="customer_id", how="inner")
        known_c = mc[(mc["report_date"] < mc["period_start"]) & (mc["line"] != line)].groupby("row_id").size()
        rc["prior_known_claims_customer_other_lines"] = rc["row_id"].map(known_c).fillna(0).clip(upper=2)
        res = {}
        for col in ["prior_known_claims_policy", "prior_known_claims_customer_other_lines"]:
            g = rc.groupby(col).agg(rows=("row_id", "size"), e=("exposure", "sum"), n=("n_acc", "sum"), y=("y", "sum"))
            g["freq"] = g["n"] / g["e"]; g["rate"] = g["y"] / g["e"]
            e_ = rc["exposure"].to_numpy(dtype=float); y_ = rc["y"].to_numpy(dtype=float)
            mu = e_ * rc[col].map(g["rate"]).to_numpy(dtype=float); mu0 = e_ * y_.sum() / e_.sum()
            res[col] = {"d2_oneway_vs_constant_rate": 1 - tweedie_deviance(y_, np.maximum(mu, 1e-12)) / tweedie_deviance(y_, mu0),
                        "bands": g.reset_index().astype({col: str}).to_dict("records")}
        history[line] = res
    evidence["prior_history_oneway"] = history

    # ------------------------------------------------------------- test 2025
    test_info = {}
    for line in LINES:
        te = tests[line]
        test_info[line] = {"rows": int(len(te)), "exposure": float(te["exposure"].sum()),
                           "start_month_share": te["period_start"].dt.month.value_counts(normalize=True).sort_index().to_dict(),
                           "new_business_share": float(te["new_business"].mean()),
                           "policies_seen_in_train_share": float(te["policy_id"].isin(policies[line]["policy_id"]).mean()),
                           "customers_seen_in_train_any_line_share": float(te["customer_id"].isin(cust_lines["customer_id"]).mean())}
    evidence["test_2025"] = test_info

    # ------------------------------------------------------------------ figuras
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for line in LINES:
        pos = np.sort(acc.loc[(acc.line == line) & (acc.net > 0), "net"].to_numpy(dtype=float))
        surv = 1 - np.arange(1, len(pos) + 1) / len(pos)
        ax.loglog(pos, np.maximum(surv, 1 / len(pos)), color=PALETTE[line], lw=1.6, label=LINE_LABEL[line])
    ax.set_xlabel("Severidad neta positiva por siniestro, CU (log)"); ax.set_ylabel("P(X > x) (log)")
    ax.set_title("Cola de severidad por ramo (aceptados 2021–2024, valorados al 31-12-2024)")
    ax.legend(frameon=False); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(out / "figuras" / "fig_cola_severidad.png", dpi=150); plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
    for ax, line in zip(axes, LINES):
        res = taylor_out[line]
        if res.get("cells_table"):
            cells = pd.DataFrame(res["cells_table"])
            ax.scatter(np.log(cells["mean"]), np.log(cells["var"]), s=10, color=PALETTE[line], alpha=0.6)
            xs = np.linspace(np.log(cells["mean"]).min(), np.log(cells["mean"]).max(), 10)
            ax.plot(xs, res["intercept_log_phi"] + res["slope_p"] * xs, color="#0b0b0b", lw=1.4)
            ax.set_title(f"{LINE_LABEL[line]}: pendiente p = {res['slope_p']:.2f} ({res['cells']} celdas)")
        ax.set_xlabel("log media del coste por periodo (celda)"); ax.set_ylabel("log varianza")
        ax.grid(alpha=0.25)
    fig.suptitle("Ley de potencia varianza–media en periodos de año completo (diagnóstico de potencia Tweedie)")
    fig.tight_layout(); fig.savefig(out / "figuras" / "fig_taylor_potencia.png", dpi=150); plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=False)
    focus = {"motor": ["bodily_injury", "own_damage", "third_party_prop"], "buildings": ["subsidence", "flood", "escape_of_water"],
             "contents": ["theft", "escape_of_water", "flood"]}
    markers = ["o", "s", "^"]
    for ax, line in zip(axes, LINES):
        for peril, mk in zip(focus[line], markers):
            sub = delays[(delays.line == line) & (delays.peril == peril)].sort_values("occ_year")
            ax.plot(sub["occ_year"], sub["delay_p90"], marker=mk, color=PALETTE[line], lw=1.4, ms=5, label=peril)
        ax.set_title(f"{LINE_LABEL[line]}: p90 del retraso de reporte (días)"); ax.set_xlabel("Año de ocurrencia")
        ax.set_xticks([2021, 2022, 2023, 2024]); ax.legend(frameon=False, fontsize=8); ax.grid(alpha=0.25)
    fig.suptitle("El retraso observado cae en 2024 por truncamiento al 31-12-2024, no por liquidación más rápida")
    fig.tight_layout(); fig.savefig(out / "figuras" / "fig_retraso_por_anio.png", dpi=150); plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4))
    for ax, line in zip(axes, LINES):
        sub = oneway_df[(oneway_df.line == line) & (oneway_df.block == "F0")].nlargest(12, "d2_oneway_vs_constant_rate")
        ax.barh(sub["column"][::-1], sub["d2_oneway_vs_constant_rate"][::-1], color=PALETTE[line], height=0.6)
        ax.set_title(f"{LINE_LABEL[line]}: D² one-way F0 (en muestra)"); ax.set_xlabel("D² Tweedie p=1,5 frente a tasa constante")
        ax.grid(axis="x", alpha=0.25)
    fig.tight_layout(); fig.savefig(out / "figuras" / "fig_oneway_d2_f0.png", dpi=150); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for ax, (line, perils) in zip(axes, [("buildings", ["storm", "flood", "escape_of_water"]), ("motor", ["own_damage", "glass_hail", "theft"])]):
        for peril, mk in zip(perils, markers):
            sub = season[(season.line == line) & (season.peril == peril)].sort_values("month")
            ax.plot(sub["month"], sub["share"] * 100, marker=mk, ms=4, lw=1.4, color=PALETTE[line], label=peril, alpha=0.9)
        ax.set_title(f"{LINE_LABEL[line]}: % de siniestros por mes de ocurrencia"); ax.set_xlabel("Mes"); ax.set_xticks(range(1, 13))
        ax.legend(frameon=False, fontsize=8); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(out / "figuras" / "fig_estacionalidad.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 3.8))
    for r, ls, mk in [(x, "-", "o") for x in wx_rows if x["line"] == "buildings" and x["peril"] == "flood" and x["variable"] == "rainfall_mm"]:
        d = pd.DataFrame(r["deciles"])
        d = d[d["band"] != "<NA>"]
        ax.plot(range(1, len(d) + 1), d["freq"] * 100, marker=mk, lw=1.6, color=PALETTE["buildings"] if r["weather"] == "same_year" else "#52514e",
                label=f"lluvia del {'mismo año' if r['weather'] == 'same_year' else 'año anterior'}")
    ax.set_xticks(range(1, 11)); ax.set_xlabel("Decil de lluvia anual en la dirección (1 = más seco, 10 = más lluvioso)"); ax.set_ylabel("Siniestros de inundación por 100 años-exposición")
    ax.set_title("Edificios, inundación: señal del clima contemporáneo frente al clima rezagado")
    ax.legend(frameon=False); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(out / "figuras" / "fig_clima_rezago.png", dpi=150); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    dband = duration[duration.dimension == "exposure_band"]
    for line in LINES:
        sub = dband[dband.line == line]
        axes[0].plot(sub["level"], sub["freq_accepted"], marker="o", color=PALETTE[line], lw=1.4, label=LINE_LABEL[line])
        axes[1].plot(sub["level"], sub["pure_premium"], marker="o", color=PALETTE[line], lw=1.4, label=LINE_LABEL[line])
    axes[0].set_title("Frecuencia de aceptados por año-exposición según duración"); axes[1].set_title("Coste observado por año-exposición según duración")
    for ax in axes:
        ax.tick_params(axis="x", rotation=20); ax.legend(frameon=False, fontsize=8); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(out / "figuras" / "fig_duracion.png", dpi=150); plt.close(fig)

    figures = sorted(p.name for p in (out / "figuras").glob("*.png"))
    evidence["figures"] = figures
    evidence["tables"] = sorted(p.name for p in (out / "tables").glob("*.csv"))
    evidence["finished_at_utc"] = utc_now()
    (out / "evidencia.json").write_text(json.dumps(jsonable(evidence), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {p.relative_to(out).as_posix(): digest(p) for p in sorted(out.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run_id": run_id, "evidence": str((out / "evidencia.json").relative_to(ROOT))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
