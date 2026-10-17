"""Comprueba la evidencia y referencias de la investigación, sin entrenar."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    checks = []

    def check(name, result, detail=None):
        checks.append({"name": name, "passed": bool(result), "detail": detail})

    index = read_json(HERE / "actual.json")
    evidence_path = HERE / index["evidence"]
    evidence = read_json(evidence_path)
    active_index = read_json(ROOT / "Hackaton/Semana 1/Limpieza/current_dataset.json")
    catalog_path = ROOT / active_index["catalog_workspace_relative"]
    catalog = read_json(catalog_path)
    check("evidence_active_input_index", evidence["active_input_index"] == active_index)
    check("active_catalog_hash", digest(catalog_path) == evidence["active_input_catalog_sha256"])
    for name, entry in catalog.items():
        check(f"catalog_input_unchanged:{name}", digest(ROOT / entry["workspace_relative_path"]) == entry["sha256"])
    for name, entry in evidence["provenance"].items():
        check(f"analysis_input_unchanged:{name}", digest(ROOT / entry["path"]) == entry["sha256"])
    check("script_matches_snapshot", digest(HERE / "analizar_soporte.py") == digest(HERE / index["script_snapshot"]))
    ast.parse((HERE / "analizar_soporte.py").read_text(encoding="utf-8"))
    check("analysis_script_parses", True)

    lines = {x["line"]: x for x in evidence["claims_by_line"]}
    for line, row in lines.items():
        perils = [x for x in evidence["claims_by_peril"] if x["line"] == line]
        check(f"perils_reconcile_count:{line}", sum(x["reported_accepted_claims"] for x in perils) == row["reported_accepted_claims"])
        for field in ("net_incurred_CU", "case_reserve_CU"):
            check(f"perils_reconcile:{line}:{field}", math.isclose(sum(x[field] for x in perils), row[field], abs_tol=.01))
        check(f"peril_shares_sum_one:{line}", math.isclose(sum(x["peril_share_line_net_incurred"] for x in perils), 1.0, abs_tol=1e-12))
    with (evidence_path.parent / "ramos.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            check(f"csv_matches_json:{row['line']}", math.isclose(float(row["net_incurred_CU"]), lines[row["line"]]["net_incurred_CU"], abs_tol=.01))
    check("test_rows_626639", sum(x["rows"] for x in evidence["active_portfolio"] if x["partition"] == "test_2025") == 626639)
    pending = sum(x.get("sum_insured_active_CAP01", {}).get("extreme_diagnostic_rows", 0) for x in evidence["active_portfolio"])
    check("pending_capitals_reconciled", pending == active_index["pending_capitals"] == 1454)
    check("no_nonpositive_exposures", all(x["nonpositive_exposure_rows"] == 0 for x in evidence["active_portfolio"]))

    sources = read_json(HERE / "fuentes.json")
    source_ids = [x["id"] for x in sources["sources"]]
    check("23_unique_sources", len(source_ids) == len(set(source_ids)) == 23)
    check("source_inspection_and_limits", all(x.get("inspection") and x.get("project_limit") and x.get("url", "").startswith("https://") for x in sources["sources"]))
    experiments = read_json(HERE.parent / "experimentos.json")
    ids = [x["id"] for x in experiments["candidates"]]
    check("22_unique_planned_candidates", len(ids) == len(set(ids)) == 22 and set(ids) == {f"M{i:02d}" for i in range(22)})
    check("candidate_dependencies_exist", all(set(x["depends_on"]).issubset(ids) for x in experiments["candidates"]))
    check("not_trained", experiments["models_trained"] == evidence["models_trained"] == index["models_trained"] == 0)
    check("no_operational_labels_created", evidence["labels_created_for_training"] is False)

    report = (HERE / "INFORME.md").read_text(encoding="utf-8")
    check("report_current_source_independent", "gemini" not in report.lower())
    for left, right in re.findall(r"\]\((?:<([^>]+)>|([^\)]+))\)", report):
        target = left or right
        if target.startswith(("https://", "http://", "#")):
            continue
        check(f"report_link:{target}", (HERE / target.split("#")[0]).exists())
    for key in ("report", "sources", "evidence", "script_snapshot"):
        check(f"index_link:{key}", (HERE / index[key]).exists())
    state = read_json(ROOT / "Preparación/ESTADO_PROYECTO.json")
    check("state_research_catalog_consistent", state["technique_research"]["planned_candidates_total"] == len(ids) and state["technique_research"]["primary_sources"] == len(source_ids))
    check("methodology_version_matches_current_state", read_json(HERE.parent / "protocolo_metodologico.json")["version"] == state["methodological_plan"]["version"] == "1.2")
    previous = read_json(HERE / index["initial_evidence_preserved"])
    for field in ("claims_by_line", "claims_by_peril", "proxy_periods", "active_portfolio"):
        check(f"D38_refresh_preserves_aggregates:{field}", previous[field] == evidence[field])
    check("restricted_profile_excludes_D38_changes", {"construction_type", "policyholder_age"}.issubset(evidence["provenance"]["original_profile_restricted"]["excluded_columns"]))
    decisions = (ROOT / "Preparación/DECISIONES.md").read_text(encoding="utf-8")
    check("unique_D37", len(re.findall(r"^### D37,", decisions, flags=re.M)) == 1)
    result = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "passed": all(x["passed"] for x in checks),
              "checks": checks, "check_count": len(checks), "verification_kind": "own_assisted_by_AI",
              "human_review": "pending", "independent_validation": False,
              "scope": "Integrity, descriptive reconciliation, source/catalog/links consistency. No model-performance or ultimate-target validation."}
    (HERE / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "check_count": len(checks), "failed": [x for x in checks if not x["passed"]]}, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
