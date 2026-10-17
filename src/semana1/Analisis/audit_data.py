"""EDA actuarial reproducible. No modifica originales ni ajusta modelos predictivos."""
from __future__ import annotations

import hashlib
import json
import platform
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PREP = ROOT / "Preparación"
sys.path.insert(0, str(PREP / ".cache/parquet-reader"))
import numpy as np
import pandas as pd
import pyarrow
import pyarrow.parquet as pq

DATA = ROOT / "Hackaton/Semana 1/Datos"
BASE = Path(__file__).parent
LINES = ["motor", "buildings", "contents"]
DATES = {"period_start", "period_end", "date_of_birth", "loss_date", "report_date"}
CHECKS = []


def scalar(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if pd.isna(value):
        return None
    return str(value)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=scalar,
                               allow_nan=False) + "\n", encoding="utf-8")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(name):
    frame = pq.read_table(DATA / f"{name}.parquet").to_pandas()
    for col in frame:
        if col in DATES:
            frame[col] = pd.to_datetime(frame[col], errors="coerce")
        elif pd.api.types.is_string_dtype(frame[col]) or frame[col].dtype == object:
            if col.endswith("_id"):
                frame[col] = frame[col].astype("string[pyarrow]")
            elif col not in DATES and frame[col].nunique(dropna=True) < 2000:
                frame[col] = frame[col].astype("category")
    return frame


def check(table, rule, count, total, severity="revisar", detail=""):
    CHECKS.append({"table": table, "rule": rule, "affected": int(count),
                   "denominator": int(total), "fraction": float(count / total) if total else 0,
                   "severity": severity if count else "pasa", "detail": detail})


def profile(frame, name):
    result = {"name": name, "rows": len(frame), "columns": [],
              "memory_mb": float(frame.memory_usage(deep=True).sum() / 1e6)}
    for col in frame:
        s = frame[col]
        valid = s.dropna()
        record = {"name": col, "dtype": str(s.dtype), "missing": int(s.isna().sum()),
                  "missing_pct": float(s.isna().mean() * 100), "unique": int(s.nunique()),
                  "kind": "category"}
        if col in DATES:
            record.update(kind="date", min=str(s.min()), max=str(s.max()))
            values = s.dt.year.value_counts().sort_index()
            record["counts"] = [{"value": str(k), "n": int(v)} for k, v in values.items()]
        elif pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            a = valid.to_numpy(dtype=float)
            finite = a[np.isfinite(a)]
            record.update(kind="numeric", nonfinite=int(len(a)-len(finite)))
            if len(finite):
                qs = np.quantile(finite, [0, .01, .05, .25, .5, .75, .95, .99, 1])
                record["quantiles"] = dict(zip(["min", "p01", "p05", "p25", "p50", "p75", "p95", "p99", "max"], map(float, qs)))
                record.update(mean=float(np.mean(finite)), std=float(np.std(finite)),
                              zeros=int(np.sum(finite == 0)), negative=int(np.sum(finite < 0)))
                lo, hi = np.quantile(finite, [.005, .995])
                hist, edges = np.histogram(finite, bins=30, range=(lo, hi) if hi > lo else None)
                record["histogram"] = {"counts": hist.tolist(), "edges": edges.tolist(),
                                       "below": int(np.sum(finite < lo)), "above": int(np.sum(finite > hi))}
        if record["kind"] == "category" or record["unique"] <= 25:
            counts = s.value_counts(dropna=False).head(30)
            record["counts"] = [{"value": "(faltante)" if pd.isna(k) else str(k), "n": int(v)} for k, v in counts.items()]
            if len(valid) and not pd.api.types.is_numeric_dtype(s):
                raw = valid.astype("string")
                canonical = raw.str.strip().str.casefold().str.replace(r"[ -]+", "_", regex=True)
                variants = pd.DataFrame({"raw": raw, "canonical": canonical}).drop_duplicates()
                aliases = variants.groupby("canonical", observed=True)["raw"].agg(list)
                record["case_space_aliases"] = {str(k): v for k, v in aliases.items() if len(v) > 1}
                record["blank_strings"] = int((raw.str.strip() == "").sum())
        result["columns"].append(record)
    return result


def domain_checks(frame, name):
    ranges = {"exposure": (0, 1), "driver_age": (16, 110), "policyholder_age": (16, 110),
              "vehicle_age": (0, 80), "years_licensed": (0, 95), "ncb_years": (0, 80),
              "vehicle_value_group": (1, 20), "telematics_score": (1, 100),
              "flood_zone": (1, 5), "wind_exposure_index": (0, 10),
              "dry_summer_index": (0, 1), "wildfire_index": (0, 1),
              "hail_days": (0, 366), "freezing_days": (0, 366), "days_unoccupied": (0, 366),
              "household_size": (1, 30), "bedrooms": (0, 30), "energy_rating": None,
              "discount_applied": (0, 1), "sum_insured": (0, 1e9),
              "annual_mileage": (0, 500000), "engine_size_cc": (0, 10000),
              "written_premium": (0, 1e8), "voluntary_excess": (0, 1e6),
              "compulsory_excess": (0, 1e6), "prior_claims_5y": (0, 100),
              "rainfall_mm": (0, 20000), "years_at_address": (0, 110)}
    for col, bounds in ranges.items():
        if col in frame and bounds:
            s = frame[col]
            count = ((s < bounds[0]) | (s > bounds[1])).sum()
            check(name, f"rango_{col}", count, len(frame), detail=f"Rango de cribado {bounds}; no es umbral regulatorio ni regla universal.")
    if "years_licensed" in frame:
        check(name, "licencia_supera_edad", (frame.years_licensed > frame.driver_age).sum(), len(frame))
        check(name, "ncb_supera_licencia", (frame.ncb_years > frame.years_licensed).sum(), len(frame))
        check(name, "telematica_sin_consentimiento", ((~frame.telematics_opt_in) & frame.telematics_score.notna()).sum(), len(frame))
        check(name, "telematica_opt_in_sin_score", (frame.telematics_opt_in & frame.telematics_score.isna()).sum(), len(frame), "informativo")
    if "period_start" in frame:
        days = (frame.period_end - frame.period_start).dt.days + 1
        check(name, "periodo_invertido", (days <= 0).sum(), len(frame), "error")
        check(name, "exposicion_no_positiva", (frame.exposure <= 0).sum(), len(frame), "error")
        year = frame.period_start.dt.year
        denom = np.where(frame.period_start.dt.is_leap_year, 366, 365)
        err = np.minimum(np.abs(frame.exposure-days/365), np.abs(frame.exposure-days/denom))
        check(name, "exposicion_no_coincide_dias", (err > .000051).sum(), len(frame), detail="Comparacion inclusiva, base 365 o dias del año, tolerancia por redondeo 4 decimales.")
        check(name, "periodo_cruza_año", (year != frame.period_end.dt.year).sum(), len(frame))
        sorted_rows = frame.sort_values(["policy_id", "period_start", "period_end"])
        prev_max = sorted_rows.groupby("policy_id", observed=True).period_end.cummax().groupby(sorted_rows.policy_id, observed=True).shift()
        check(name, "periodos_superpuestos", (sorted_rows.period_start <= prev_max).sum(), len(frame), "error")


def segment(frame, feature, line):
    s = frame[feature]
    if feature.endswith("_id") or feature in DATES or feature in {"surname", "prediction", "line", "year"}:
        return None
    if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s) and s.nunique() > 12:
        try:
            levels = pd.qcut(s, 8, duplicates="drop").astype("string").fillna("(faltante)")
        except ValueError:
            return None
    else:
        top = s.value_counts().head(15).index
        levels = s.astype("string").fillna("(faltante)")
        levels = levels.where(s.isin(top) | s.isna(), "(otros)")
    work = pd.DataFrame({"level": levels, "exposure": frame.exposure,
                         "cost": frame.observed_net_incurred, "paid": frame.observed_net_paid,
                         "nclaims": frame.accepted_claims, "year": frame.year})
    grouped = work.groupby("level", observed=True, dropna=False).agg(
        rows=("exposure", "size"), exposure=("exposure", "sum"), cost=("cost", "sum"),
        paid=("paid", "sum"), claims=("nclaims", "sum"))
    grouped["observed_cost_per_exposure"] = grouped.cost / grouped.exposure
    grouped["reported_frequency"] = grouped.claims / grouped.exposure
    grouped["observed_severity"] = grouped.cost / grouped.claims.replace(0, np.nan)
    grouped["line"] = line
    grouped["feature"] = feature
    return grouped.reset_index()


def shifts(train, test, line):
    records = []
    for col in train.columns.intersection(test.columns):
        if col.endswith("_id") or col in DATES:
            continue
        a, b = train[col], test[col]
        rec = {"line": line, "column": col, "train_missing": float(a.isna().mean()),
               "test_missing": float(b.isna().mean()), "train_unique": int(a.nunique()), "test_unique": int(b.nunique())}
        if pd.api.types.is_numeric_dtype(a) and not pd.api.types.is_bool_dtype(a):
            rec.update(kind="numeric", train_mean=float(a.mean()), test_mean=float(b.mean()),
                       train_median=float(a.median()), test_median=float(b.median()))
            scale = a.std()
            rec["standardized_mean_difference"] = float((b.mean()-a.mean())/scale) if scale else 0
        else:
            pa, pb = a.value_counts(normalize=True), b.value_counts(normalize=True)
            ix = pa.index.union(pb.index)
            rec.update(kind="category", total_variation=float((pa.reindex(ix, fill_value=0)-pb.reindex(ix, fill_value=0)).abs().sum()/2),
                       new_level_fraction=float((b.notna() & ~b.isin(a.dropna().unique())).mean()))
        records.append(rec)
    return records


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = BASE / "runs" / f"eda_{stamp}_{uuid.uuid4().hex[:8]}"
    out.mkdir(parents=True, exist_ok=False)
    (out / "tables").mkdir()
    save(BASE / "current_run.json", {"run": out.relative_to(ROOT).as_posix()})
    print(f"OUT={out}", flush=True)
    shutil.copy2(__file__, out / "audit_data.py")
    profiles = []
    hashes = {}
    for path in sorted(DATA.glob("*.parquet")):
        name = path.stem
        frame = read(name)
        profiles.append(profile(frame, name))
        key = {"customers": ["customer_id"], "addresses": ["address_id"], "weather": ["address_id", "year"], "claims": ["claim_id"]}.get(name, ["row_id"])
        check(name, "clave_duplicada", frame.duplicated(key).sum(), len(frame), "error")
        for col in key:
            check(name, f"clave_nula_{col}", frame[col].isna().sum(), len(frame), "error")
        domain_checks(frame, name)
        hashes[path.name] = sha(path)
        print(f"perfil {name}: {len(frame):,}", flush=True)
    save(out / "profiles.json", profiles)
    save(out / "input_hashes.json", hashes)
    customers, addresses, weather, claims = map(read, ["customers", "addresses", "weather", "claims"])
    claims["loss_year"] = claims.loss_date.dt.year
    claims["report_lag_days"] = (claims.report_date-claims.loss_date).dt.days
    claims["observed_net_incurred"] = claims.incurred_to_date-claims.recoveries
    claims["observed_net_paid"] = claims.paid_to_date-claims.recoveries
    claims["case_outstanding"] = claims.incurred_to_date-claims.paid_to_date
    for label, mask in {
        "reporte_antes_siniestro": claims.report_lag_days < 0,
        "reporte_despues_corte": claims.report_date > pd.Timestamp("2024-12-31"),
        "ocurrencia_despues_corte": claims.loss_date > pd.Timestamp("2024-12-31"),
        "incurrido_menor_pagado": claims.incurred_to_date < claims.paid_to_date,
        "neto_incurrido_negativo": claims.observed_net_incurred < 0,
    }.items():
        check("claims", label, mask.sum(), len(claims))
    claims.groupby(["line", "peril", "status", "loss_year"], observed=True).agg(
        claims=("claim_id", "size"), paid=("paid_to_date", "sum"), incurred=("incurred_to_date", "sum"),
        recoveries=("recoveries", "sum"), lag_median=("report_lag_days", "median"),
        lag_p95=("report_lag_days", lambda x:x.quantile(.95))).reset_index().to_csv(out / "tables/claims_by_peril.csv", index=False)
    claims.drop(columns=["repairer_id", "third_party_id"]).to_parquet(out / "tables/claims_diagnostic.parquet", index=False)
    summaries, associations, drift, links, join_results = [], [], [], [], []
    for line in LINES:
        tr, te = read(f"policies_{line}"), read(f"test_{line}")
        tr["year"], te["year"] = tr.period_start.dt.year, te.period_start.dt.year
        for partition, frame in [("train", tr), ("test", te)]:
            for col, master in [("customer_id", customers.customer_id), ("address_id", addresses.address_id)]:
                check(f"{partition}_{line}", f"sin_maestro_{col}", (~frame[col].isin(master)).sum(), len(frame), "error")
            links.append({"line": line, "partition": partition, "rows": len(frame),
                          "policies": int(frame.policy_id.nunique()), "customers": int(frame.customer_id.nunique()),
                          "addresses": int(frame.address_id.nunique()), "exposure": float(frame.exposure.sum()),
                          "exposure_mean": float(frame.exposure.mean()), "years": sorted(map(int, frame.year.unique()))})
        drift.extend(shifts(tr.drop(columns="year"), te.drop(columns="year"), line))
        for key in ["policy_id", "customer_id", "address_id"]:
            check(f"test_{line}", f"entidad_nueva_{key}", (~te[key].isin(tr[key])).sum(), len(te), "informativo", "Es cambio de composición, no error.")
        candidates = claims.loc[claims.line == line].merge(
            tr[["policy_id", "row_id", "period_start", "period_end"]], on="policy_id", how="left", validate="many_to_many")
        valid = candidates.loss_date.between(candidates.period_start, candidates.period_end, inclusive="both")
        matched = candidates.loc[valid].copy()
        multiplicity = matched.groupby("claim_id", observed=True).size()
        selected = claims.loc[claims.line == line, "claim_id"]
        check(line, "siniestros_sin_periodo", (~selected.isin(multiplicity.index)).sum(), len(selected), "error")
        check(line, "siniestros_con_multiples_periodos", (multiplicity > 1).sum(), len(selected), "error")
        matched = matched.loc[matched.claim_id.isin(multiplicity[multiplicity == 1].index)]
        matched["accepted"] = matched.status != "repudiated"
        for col in ["observed_net_incurred", "observed_net_paid", "case_outstanding"]:
            matched[col] = matched[col].where(matched.accepted, 0)
        matched["open_claim"] = matched.accepted & (matched.status == "open")
        agg = matched.groupby("row_id", observed=True).agg(
            accepted_claims=("accepted", "sum"), reported_claims=("claim_id", "size"),
            observed_net_incurred=("observed_net_incurred", "sum"), observed_net_paid=("observed_net_paid", "sum"),
            case_outstanding=("case_outstanding", "sum"), open_claims=("open_claim", "sum"))
        tr = tr.merge(agg, on="row_id", how="left", validate="one_to_one")
        tr[agg.columns] = tr[agg.columns].fillna(0)
        check(line, "conservacion_coste_cruce", int(not np.isclose(tr.observed_net_incurred.sum(), matched.observed_net_incurred.sum())), 1, "error")
        join_results.append({"line": line, "candidate_rows_naive_policy_join": len(candidates),
                             "unique_claims": len(selected), "matched_unique_claims": int(matched.claim_id.nunique()),
                             "naive_inflation_factor": float(len(candidates)/len(selected))})
        for year, group in tr.groupby("year", observed=True):
            exposure = group.exposure.sum(); count = group.accepted_claims.sum(); cost = group.observed_net_incurred.sum()
            summaries.append({"line": line, "year": int(year), "rows": len(group), "exposure": exposure,
                              "reported_accepted_claims": count, "net_incurred": cost,
                              "net_paid": group.observed_net_paid.sum(), "outstanding": group.case_outstanding.sum(),
                              "reported_frequency": count/exposure, "observed_severity": cost/count if count else 0,
                              "observed_cost_per_exposure": cost/exposure,
                              "zero_claim_rows_fraction": float((group.accepted_claims == 0).mean()),
                              "open_claims": group.open_claims.sum(), "written_premium": group.written_premium.sum()})
        expanded = tr.merge(customers, on="customer_id", how="left", validate="many_to_one").merge(
            addresses, on="address_id", how="left", validate="many_to_one").merge(
            weather, on=["address_id", "year"], how="left", validate="many_to_one", indicator="weather_join")
        check(line, "sin_clima_direccion_año", (expanded.weather_join != "both").sum(), len(expanded), "error")
        expanded["customer_age_from_dob"] = np.floor((expanded.period_start-expanded.date_of_birth).dt.days/365.2425)
        expanded["property_age"] = expanded.year-expanded.year_built
        check(line, "edificio_futuro", (expanded.property_age < 0).sum(), len(expanded))
        check(line, "alta_cliente_futura", (expanded.customer_since_year > expanded.year).sum(), len(expanded))
        if "policyholder_age" in expanded:
            delta = expanded.policyholder_age-expanded.customer_age_from_dob
            check(line, "edad_titular_difiere_mas_1", (delta.abs()>1).sum(), len(expanded), detail="Comparacion DOB vs edad; aproximacion de años bisiestos tolera 1 año.")
        ignored = set(agg.columns) | {"weather_join", "observed_net_incurred", "observed_net_paid", "case_outstanding", "accepted_claims", "reported_claims", "open_claims"}
        for feature in expanded.columns:
            if feature not in ignored:
                table = segment(expanded, feature, line)
                if table is not None:
                    associations.append(table)
        cols = ["row_id", "policy_id", "customer_id", "address_id", "year", "exposure", *agg.columns]
        tr[cols].to_parquet(out / f"tables/observed_proxy_{line}.parquet", index=False)
        print(f"cruces y diagnosticos {line}: {len(expanded):,} filas", flush=True)
    pd.DataFrame(summaries).to_csv(out / "tables/annual_summary.csv", index=False)
    pd.concat(associations, ignore_index=True).to_csv(out / "tables/segments.csv", index=False)
    pd.DataFrame(drift).to_csv(out / "tables/train_test_shift.csv", index=False)
    save(out / "portfolio_links.json", links)
    save(out / "claim_join_diagnostics.json", join_results)
    save(out / "checks.json", CHECKS)
    save(out / "run.json", {"finished_at_utc": datetime.now(timezone.utc).isoformat(),
         "source_sha256": sha(Path(__file__)), "python": sys.version, "platform": platform.platform(),
         "versions": {"pandas": pd.__version__, "numpy": np.__version__, "pyarrow": pyarrow.__version__},
         "data_rows_profiled": sum(p["rows"] for p in profiles), "training_performed": False,
         "observed_proxy_is_ultimate": False, "notes": "Asociaciones descriptivas sin ajuste multivariado; no son causalidad ni relatividades de tarifa."})
    print(json.dumps({"run": str(out), "checks": len(CHECKS), "nonzero_checks": sum(c["affected"]>0 for c in CHECKS)}, ensure_ascii=True), flush=True)


if __name__ == "__main__":
    main()
