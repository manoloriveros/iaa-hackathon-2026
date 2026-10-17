"""Diagnóstico descriptivo para elegir técnicas; no estima ni entrena modelos."""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "Preparación/.cache/parquet-reader"))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    index_path = ROOT / "Hackaton/Semana 1/Limpieza/current_dataset.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    catalog_path = ROOT / index["catalog_workspace_relative"]
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    verification = json.loads((catalog_path.parent / "verification.json").read_text(encoding="utf-8"))
    assert verification["passed"]
    run = Path(__file__).parent / "runs" / datetime.now(timezone.utc).strftime("soporte_%Y%m%dT%H%M%SZ")
    run.mkdir(parents=True, exist_ok=False)
    provenance = {}

    def read(name, columns=None):
        entry = catalog[name]
        path = ROOT / entry["workspace_relative_path"]
        actual = sha(path)
        assert actual == entry["sha256"], name
        provenance[name] = {"path": entry["workspace_relative_path"], "sha256": actual,
                            "columns_read": columns or "all"}
        return pq.read_table(path, columns=columns, use_threads=False).to_pandas(use_threads=False)

    print("Resumiendo siniestros aceptados 2021–2024", flush=True)
    claims = read("claims")
    claims["loss_year"] = pd.to_datetime(claims.loss_date).dt.year
    claims["lag_days"] = (pd.to_datetime(claims.report_date) - pd.to_datetime(claims.loss_date)).dt.days
    accepted = claims[claims.status.isin(["open", "closed"]) & claims.loss_year.between(2021, 2024)].copy()
    accepted["net"] = accepted.incurred_to_date - accepted.recoveries
    accepted["reserve"] = accepted.incurred_to_date - accepted.paid_to_date
    assert accepted.net.ge(0).all()
    assert accepted.reserve.ge(0).all()

    def describe(part):
        positive = part.loc[part.net.gt(0), "net"]
        count_top = max(1, math.ceil(len(positive) * .01))
        total = float(part.net.sum())
        return {"reported_accepted_claims": len(part), "positive_cost_claims": len(positive),
                "zero_cost_claims": int(part.net.eq(0).sum()),
                "net_incurred_CU": total, "case_reserve_CU": float(part.reserve.sum()),
                "case_reserve_share_net_incurred": float(part.reserve.sum() / total),
                "open_claim_fraction": float(part.status.eq("open").mean()),
                "positive_severity_mean_CU": float(positive.mean()),
                "positive_severity_median_CU": float(positive.median()),
                "positive_severity_p95_CU": float(positive.quantile(.95)),
                "positive_severity_p99_CU": float(positive.quantile(.99)),
                "positive_severity_max_CU": float(positive.max()),
                "top_1pct_positive_claim_count_ceil": count_top,
                "top_1pct_positive_claim_cost_share": float(positive.nlargest(count_top).sum() / total),
                "observed_report_delay_p95_days": float(part.lag_days.quantile(.95))}

    line_stats, peril_stats, cohort_stats = [], [], []
    for line, part in accepted.groupby("line"):
        line_stats.append({"line": line, **describe(part)})
        line_total = part.net.sum()
        for peril, sub in part.groupby("peril"):
            peril_stats.append({"line": line, "peril": peril, **describe(sub),
                                "peril_share_line_net_incurred": float(sub.net.sum() / line_total)})
        for (peril, year), sub in part.groupby(["peril", "loss_year"]):
            cohort_stats.append({"line": line, "peril": peril, "year": int(year), **describe(sub)})

    eda = ROOT / "Hackaton/Semana 1/Analisis/runs/eda_20261016T165629Z_ab2a8365"
    proxy_stats = []
    for line in ("motor", "buildings", "contents"):
        print(f"Revisando masa de ceros de {line} en proxy histórico", flush=True)
        path = eda / f"tables/observed_proxy_{line}.parquet"
        provenance[f"historical_proxy_{line}"] = {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path),
                "reused_fields": ["year", "observed_net_incurred", "accepted_claims"],
                "excluded_fields": ["customer_id", "exposure"],
                "scope": "D30 descriptive claim assignment only, not newly materialized T0"}
        proxy = pq.read_table(path, columns=["year", "observed_net_incurred", "accepted_claims"], use_threads=False).to_pandas(use_threads=False)
        cost = proxy.observed_net_incurred
        positive = cost[cost.gt(0)]
        n_top = max(1, math.ceil(len(cost) * .01))
        proxy_stats.append({"line": line, "rows": len(proxy), "accepted_claims_assigned": int(proxy.accepted_claims.sum()),
                "net_incurred_assigned_CU": float(cost.sum()), "zero_cost_row_fraction": float(cost.eq(0).mean()),
                "positive_cost_rows": len(positive), "top_1pct_all_rows_count_ceil": n_top,
                "top_1pct_all_rows_cost_share": float(cost.nlargest(n_top).sum() / cost.sum()),
                "positive_period_cost_p99_CU": float(positive.quantile(.99))})

    portfolio = []
    for line in ("motor", "buildings", "contents"):
        for test in (False, True):
            name = f"{'test' if test else 'policies'}_{line}"
            cols = ["exposure"] + (["sum_insured"] if line != "motor" else ["cover_type"])
            frame = read(name, cols)
            item = {"line": line, "partition": "test_2025" if test else "train_2021_2024", "rows": len(frame),
                    "exposure_years": float(frame.exposure.sum()),
                    "exposure_p05": float(frame.exposure.quantile(.05)),
                    "exposure_median": float(frame.exposure.median()),
                    "share_exposure_below_quarter_year": float(frame.exposure.lt(.25).mean()),
                    "share_exposure_below_half_year": float(frame.exposure.lt(.5).mean()),
                    "nonpositive_exposure_rows": int(frame.exposure.le(0).sum()),
                    "share_exposure_above_one": float(frame.exposure.gt(1).mean())}
            if line != "motor":
                v = frame.sum_insured
                item["sum_insured_active_CAP01"] = {"missing": int(v.isna().sum()), "p01": float(v.quantile(.01)),
                    "median": float(v.median()), "p99": float(v.quantile(.99)), "maximum": float(v.max()),
                    "extreme_diagnostic_rows": int(v.gt(1e7 if line == "buildings" else 1e6).sum()),
                    "extreme_threshold_is_contractual_limit": False}
            else:
                item["cover_type_rows"] = {str(k): int(v) for k, v in frame.cover_type.value_counts().items()}
            portfolio.append(item)

    profile_path = eda / "tables/column_profile.csv"
    profile = pd.read_csv(profile_path)
    # Exclude fields changed by ID01, EXP01, CAP01, CAT01 and AGE01.
    excluded_profile_fields = ["customer_id", "exposure", "sum_insured", "construction_type", "policyholder_age"]
    profile = profile[~profile.column.isin(excluded_profile_fields)]
    provenance["original_profile_restricted"] = {"path": profile_path.relative_to(ROOT).as_posix(),
                "sha256": sha(profile_path), "excluded_columns": excluded_profile_fields}
    profile.to_csv(run / "perfil_campos_sin_cambios.csv", index=False)
    for filename, rows in (("ramos.csv", line_stats), ("riesgos.csv", peril_stats),
                           ("cohortes.csv", cohort_stats), ("proxy_periodos.csv", proxy_stats)):
        pd.DataFrame(rows).to_csv(run / filename, index=False)
    assert json.loads(index_path.read_text(encoding="utf-8")) == index, "El índice cambió durante la inspección"
    result = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "valuation": "2024-12-31",
              "scope": "Descriptive observed accepted claims, occurrence 2021–2024, reported by valuation. Claim-level sums include claims not assigned by old EDA.",
              "active_input_index": index, "active_input_catalog_sha256": sha(catalog_path),
              "provenance": provenance, "claims_by_line": line_stats, "claims_by_peril": peril_stats,
              "proxy_periods": proxy_stats, "active_portfolio": portfolio,
              "capital_extremes_reconcile_to_pending": sum(x.get("sum_insured_active_CAP01", {}).get("extreme_diagnostic_rows", 0) for x in portfolio) == index["pending_capitals"],
              "models_trained": 0, "labels_created_for_training": False, "human_review": "pending",
              "independent_validation": False}
    assert result["capital_extremes_reconcile_to_pending"]
    (run / "evidencia.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    shutil.copy2(__file__, run / Path(__file__).name)
    print(json.dumps({"run": run.relative_to(ROOT).as_posix(), "lines": line_stats, "proxy": proxy_stats}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
