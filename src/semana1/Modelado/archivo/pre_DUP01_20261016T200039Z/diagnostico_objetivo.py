"""Resume evidencia del objetivo y los cortes temporales, sin entrenar modelos."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "Preparación/.cache/parquet-reader"))

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    print("Leyendo catálogo verificado", flush=True)
    index = ROOT / "Hackaton/Semana 1/Limpieza/current_dataset.json"
    run = ROOT / json.loads(index.read_text(encoding="utf-8"))["workspace_relative_run"]
    verification = json.loads((run / "verification.json").read_text(encoding="utf-8"))
    if not verification["passed"]:
        raise ValueError("La corrida de limpieza no tiene verificación satisfactoria")
    catalog = json.loads((run / "dataset_catalog.json").read_text(encoding="utf-8"))
    provenance: dict[str, dict] = {}

    def read(name: str, columns: list[str] | None = None) -> pd.DataFrame:
        entry = catalog[name]
        path = ROOT / entry["workspace_relative_path"]
        actual = digest(path)
        if actual != entry["sha256"]:
            raise ValueError(f"Hash distinto del catálogo: {name}")
        provenance[name] = {"path": entry["workspace_relative_path"], "sha256": actual}
        return pq.read_table(path, columns=columns).to_pandas()

    claims = read("claims")
    print("Siniestros leídos; resumiendo desarrollo observado", flush=True)
    for col in ("loss_date", "report_date"):
        claims[col] = pd.to_datetime(claims[col])
    claims["loss_year"] = claims.loss_date.dt.year
    claims["lag"] = (claims.report_date - claims.loss_date).dt.days
    claims["net"] = claims.incurred_to_date - claims.recoveries
    claims["reserve"] = claims.incurred_to_date - claims.paid_to_date
    accepted = claims.status.isin(["open", "closed"])
    observed: list[dict] = []
    for (line, peril, year), part in claims[accepted].groupby(["line", "peril", "loss_year"]):
        opened = part.status.eq("open")
        observed.append({
            "line": line, "peril": peril, "loss_year": int(year),
            "reported_accepted_claims": len(part), "open_claims": int(opened.sum()),
            "open_fraction": float(opened.mean()), "net_incurred": float(part.net.sum()),
            "case_reserve": float(part.reserve.sum()),
            "observed_lag_median_days": float(part.lag.median()),
            "observed_lag_p95_days": float(part.lag.quantile(.95)),
            "observed_lag_p99_days": float(part.lag.quantile(.99)),
            "scope": "Reported at 2024-12-31; observed delay distribution is truncated",
        })

    policies: dict[str, pd.DataFrame] = {}
    temporal: list[dict] = []
    products: list[dict] = []
    for line in ("motor", "buildings", "contents"):
        print(f"Revisando periodos de {line}", flush=True)
        cols = ["row_id", "policy_id", "customer_id", "address_id", "period_start", "exposure"]
        if line == "motor":
            cols.append("cover_type")
        train = read(f"policies_{line}", cols)
        train["year"] = pd.to_datetime(train.period_start).dt.year
        test = read(f"test_{line}", cols)
        test["year"] = pd.to_datetime(test.period_start).dt.year
        policies[line] = train
        for year in (2022, 2023, 2024, 2025):
            history = train[train.year.lt(year)]
            future = test if year == 2025 else train[train.year.eq(year)]
            temporal.append({
                "line": line, "prediction_year": year, "rows": len(future),
                "exposure_years_cleaned": float(future.exposure.sum()),
                "known_policy_row_fraction": float(future.policy_id.isin(history.policy_id).mean()),
                "known_customer_row_fraction": float(future.customer_id.isin(history.customer_id).mean()),
                "known_address_row_fraction": float(future.address_id.isin(history.address_id).mean()),
                "scope": "Same-line prior policy records only; no historical claim amounts used",
            })
        if line == "motor":
            for (partition, frame) in (("train", train), ("test", test)):
                for product, part in frame.groupby("cover_type", dropna=False):
                    products.append({"line": line, "partition": partition,
                                     "cover_type": str(product), "rows": len(part),
                                     "exposure_years_cleaned": float(part.exposure.sum())})

    prior_eda = ROOT / "Hackaton/Semana 1/Analisis/runs/eda_20261016T165629Z_ab2a8365"
    proxy_summary: list[dict] = []
    for line, frame in policies.items():
        print(f"Contrastando proxy de {line}", flush=True)
        path = prior_eda / f"tables/observed_proxy_{line}.parquet"
        proxy = pq.read_table(path, columns=["row_id", "accepted_claims", "observed_net_incurred", "open_claims"]).to_pandas()
        provenance[f"eda_proxy_{line}"] = {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path)}
        merged = frame.merge(proxy, on="row_id", how="left", validate="one_to_one")
        if merged.accepted_claims.isna().any():
            raise ValueError("Falta una fila de proxy descriptiva")
        for year, part in merged.groupby("year"):
            proxy_summary.append({
                "line": line, "year": int(year), "rows": len(part),
                "exposure_years_cleaned": float(part.exposure.sum()),
                "reported_accepted_claims": int(part.accepted_claims.sum()),
                "open_claims": int(part.open_claims.sum()),
                "observed_net_incurred": float(part.observed_net_incurred.sum()),
                "zero_observed_cost_row_fraction": float(part.observed_net_incurred.eq(0).mean()),
                "scope": "EDA assignment reused; exposure from verified cleaning; not an ultimate target",
            })

    controls = {
        "unique_claim_ids": bool(claims.claim_id.is_unique),
        "unknown_statuses": sorted(set(claims.status) - {"closed", "open", "repudiated"}),
        "accepted_nonfinite_net_cost": int((~np.isfinite(claims.loc[accepted, "net"])).sum()),
        "accepted_negative_net_cost": int(claims.loc[accepted, "net"].lt(0).sum()),
        "accepted_zero_net_cost": int(claims.loc[accepted, "net"].eq(0).sum()),
        "negative_case_reserve": int(claims.reserve.lt(-.005).sum()),
        "closed_paid_incurred_mismatch": int((claims.status.eq("closed") & claims.reserve.abs().gt(.005)).sum()),
        "negative_report_delay": int(claims.lag.lt(0).sum()),
        "reported_after_valuation": int(claims.report_date.gt("2024-12-31").sum()),
        "rejected_nonzero_incurred": int((claims.status.eq("repudiated") & claims.incurred_to_date.ne(0)).sum()),
    }
    now = datetime.now(timezone.utc)
    output = Path(__file__).parent / "diagnosticos" / now.strftime("objetivo_%Y%m%dT%H%M%SZ")
    output.mkdir(parents=True, exist_ok=False)
    result = {"created_at_utc": now.isoformat(), "scope": "Descriptive target and temporal-design evidence; no training or label correction",
              "valuation_date": "2024-12-31", "cleaning_run": run.relative_to(ROOT).as_posix(),
              "provenance": provenance, "controls": controls, "claims_by_peril_year": observed,
              "temporal_entity_overlap": temporal, "motor_products": products,
              "observed_proxy_with_cleaned_exposure": proxy_summary,
              "human_review": "pending", "independent_validation": False,
              "models_trained": 0, "source_files_modified": False}
    (output / "evidencia.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    shutil.copy2(__file__, output / "diagnostico_objetivo.py")
    print(json.dumps({"run": output.relative_to(ROOT).as_posix(), "controls": controls,
                      "temporal_2025": [x for x in temporal if x["prediction_year"] == 2025]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
