"""S06: relatividades LightGBM y balance de cartera al nivel último S02, sin doble IBNR."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "Preparación/.cache/parquet-reader"))
sys.path.insert(0, str(ROOT / "Preparación/src"))
import numpy as np
import pandas as pd
from iaa_lab.models import score_predictions


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    registry_path = ROOT / "Hackaton/Semana 1/Envios/registro_envios.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if any(c["id"] == "S06" for c in registry["candidates"]):
        raise ValueError("S06 ya existe; no sobrescribir.")
    evidence = ROOT / "Preparación/artifacts/verification/improvement_20261017_D71"
    sources = {name: next(c for c in registry["candidates"] if c["id"] == name) for name in ["S02", "S04"]}
    frames = {}
    for name, candidate in sources.items():
        path = ROOT / candidate["exact_submission_file"]["path"]
        assert sha(path) == candidate["exact_submission_file"]["sha256"]
        frames[name] = pd.read_csv(path, dtype={"row_id": str})
    if frames["S02"].row_id.tolist() != frames["S04"].row_id.tolist():
        raise ValueError("Los orígenes no están alineados.")
    labels = []
    matrices = ROOT / "Hackaton/Semana 1/Matriz_F0_claude/runs/f0_20261017T141732Z_65df7fca/tables"
    for line in ["motor", "buildings", "contents"]:
        t = pd.read_parquet(matrices / f"f0_{line}.parquet", columns=["row_id", "year"])
        labels.append(t.loc[t.year.eq(2025), ["row_id"]].assign(line=line))
    frame = frames["S04"].merge(pd.concat(labels), on="row_id", validate="one_to_one", how="left")
    frame["S02"] = frames["S02"].prediction.to_numpy(float)
    factors = {}
    for line, group in frame.groupby("line"):
        target = float(group.S02.sum())
        factor = float(target / group.prediction.sum())
        factors[line] = {"target_total_ultimate_CU": target, "relative_normalization": factor}
        frame.loc[group.index, "prediction"] *= factor
    path = ROOT / "Hackaton/Semana 1/Envios/archivos/S06_lightgbm_3semillas_F0_nivel_S02.csv"
    frame[["row_id", "prediction"]].to_csv(path, index=False, float_format="%.6f")
    restored = pd.read_csv(path, dtype={"row_id": str})
    assert restored.row_id.tolist() == frames["S02"].row_id.tolist()
    assert np.isfinite(restored.prediction).all() and restored.prediction.min() > 0
    metrics = []
    for split in ["V23", "V24"]:
        local = pd.read_parquet(evidence / f"frozen_{split}_predictions.parquet")
        # El objetivo local de nivel procede solo de los años de train.
        for line, group in local.groupby("line"):
            factor = float(group.M00.sum() / group.GBT3_raw.sum())
            local.loc[group.index, "anchored"] = group.GBT3_raw * factor
        selected = local.loc[local.V23.eq("eval_seleccion")] if split == "V23" else local
        for line, group in [("ALL", selected), *list(selected.groupby("line"))]:
            ordinary = group.T0 < group.T0.quantile(.999)
            metrics.append({"split": split, "line": line,
                            "D2_anchored": score_predictions(group.T0, group.anchored, "d2_tweedie"),
                            "D2_without_top_0_1pct": score_predictions(group.loc[ordinary, "T0"], group.loc[ordinary, "anchored"], "d2_tweedie")})
        local.to_parquet(evidence / f"anchored_{split}_predictions.parquet", index=False)
    pd.DataFrame(metrics).to_csv(evidence / "anchored_level_metrics.csv", index=False)
    local_scores = {r["split"]: r["D2_anchored"] for r in metrics if r["line"] == "ALL"}
    candidate = {
        "id": "S06", "prepared_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "plan": "D73: separar estructura y nivel, conservando el nivel de cartera S02 aprobado D70",
        "candidate": "M04_three_seeds_portfolio_balance",
        "hypothesis": "LightGBM aporta relatividades de riesgo; conservar por ramo el mismo total último de S02 evita trasladar a 2025 el descenso aparente de T0 reciente por falta de desarrollo",
        "changes": "Normalizar por ramo la forma de S04 contra el total S02 de esa cartera; el factor anterior se cancela algebraicamente, sin aplicar de nuevo IBNR",
        "code_version": {"script": Path(__file__).relative_to(ROOT).as_posix(), "sha256": sha(Path(__file__))},
        "data_version": sources["S04"]["data_version"],
        "parameters": {"underlying_candidate": "S04", "power_fit": 1.5, "seeds": [2026, 42, 137],
                       "blocks": ["F0"], "level": "ultimate_portfolio_S02", "normalization": factors,
                       "development_applied_once": True, "test_labels_used": False,
                       "assumption": "Conservar el nivel medio último por ramo S02; no trasladar cambios globales de nivel aprendidos del T0 incompleto",
                       "formula": "prediction_i = relative_risk_i / sum(relative_risk_line) * ultimate_S02_total_line"},
        "validation_scheme": "Misma forma LightGBM congelada; en V23/V24, normalización al total M00 por ramo estimado solo en train y exposiciones de evaluación sin etiquetas; evaluación con T0 y D2 p=1.5. Producción cambia solo ese nivel a S02 último D70.",
        "exact_submission_file": {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path),
                                  "rows": len(restored), "prediction_total_CU": float(restored.prediction.sum()),
                                  "prediction_min": float(restored.prediction.min()), "prediction_max": float(restored.prediction.max())},
        "local_score": local_scores, "public_score": None, "submitted": False, "submitted_utc": None,
        "authorized_by_participant": False,
        "source_candidates": {name: c["exact_submission_file"]["sha256"] for name, c in sources.items()},
        "evidence": evidence.relative_to(ROOT).as_posix(),
    }
    registry["candidates"].append(candidate)
    registry["recommended_next_submission"] = {"id": "S06", "reason": "Preserva nivel último S02 por ramo y usa las relatividades LightGBM validadas; corrige deriva de nivel por T0 reciente inmaduro", "requires_participant_confirmation_after_dry_run": True}
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (evidence / "S06_preparation.json").write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"S06": candidate["exact_submission_file"], "local_scores": local_scores, "normalization": factors}, ensure_ascii=False))


if __name__ == "__main__":
    main()
