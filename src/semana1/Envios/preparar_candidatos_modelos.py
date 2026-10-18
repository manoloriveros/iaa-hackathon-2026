"""Prepara candidatos S03-S05 desde modelos D71 completados; no envía a Kaggle."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "Preparación/.cache/parquet-reader"))
import numpy as np
import pandas as pd


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    run = ROOT / "Preparación/artifacts/runs/production_F0_D71"
    evidence = ROOT / "Preparación/artifacts/verification/improvement_20261017_D71"
    manifest = read(run / "manifest.json")
    if manifest["status"] != "completed" or manifest["production_level"] != "ultimate":
        raise ValueError("Producción incompleta o nivel distinto de D70.")
    for relative, expected in manifest["output_hashes"].items():
        if sha(run / relative) != expected:
            raise ValueError(f"Artefacto de producción alterado: {relative}")
    routes = read(ROOT / "RUTAS_PROYECTO.json")
    registry_path = ROOT / routes["week_1_submissions_registry"]
    registry = read(registry_path)
    if any(c["id"] in {"S03", "S04", "S05"} for c in registry["candidates"]):
        raise ValueError("Los IDs S03-S05 ya están registrados; no sobrescribir.")
    original = {c["id"]: json.dumps(c, sort_keys=True) for c in registry["candidates"]}
    sample = pd.read_parquet(ROOT / routes["week_1_data"] / "sample_submission.parquet")
    glm = pd.read_csv(run / "M01_p1.5_s2026_submission.csv", dtype={"row_id": str})
    gbms = [pd.read_csv(run / f"M04_p1.5_s{seed}_submission.csv", dtype={"row_id": str})
            for seed in [2026, 42, 137]]
    for frame in [glm, *gbms]:
        if frame.row_id.tolist() != sample.row_id.tolist():
            raise ValueError("Producción y plantilla no tienen el mismo orden.")
    gb = np.mean([f.prediction.to_numpy(float) for f in gbms], axis=0)
    definitions = [
        ("S03", "M01", "glm_F0_ultimo", glm.prediction.to_numpy(float),
         "Referencia GLM F0 con riesgo individual y nivel último D70; sustituye la tasa constante M00"),
        ("S04", "M04", "lightgbm_3semillas_F0_ultimo", gb,
         "Las interacciones de LightGBM F0 mejoran al GLM y M00 en V23/V24; promedio de tres semillas y nivel último"),
        ("S05", "M01+M04", "mezcla_glm_lightgbm_F0_ultimo", .5 * glm.prediction.to_numpy(float) + .5 * gb,
         "Mezcla convexa 50/50 GLM y LightGBM de tres semillas para reducir varianza; nivel último compartido"),
    ]
    v23 = pd.read_csv(evidence / "frozen_V23_metrics.csv")
    v24 = pd.read_csv(evidence / "frozen_V24_metrics.csv")
    columns = {"S03": "GLM_raw", "S04": "GBT3_raw", "S05": "blend_raw"}
    source_files = [run / "M01_p1.5_s2026_submission.csv", *[run / f"M04_p1.5_s{s}_submission.csv" for s in [2026, 42, 137]]]
    prepared = []
    for name, model, slug, predictions, hypothesis in definitions:
        path = ROOT / routes["week_1_submissions"] / "archivos" / f"{name}_{slug}.csv"
        if path.exists():
            raise ValueError(f"El archivo ya existe: {path}")
        frame = sample[["row_id"]].copy()
        frame["prediction"] = predictions
        frame.to_csv(path, index=False, float_format="%.6f")
        restored = pd.read_csv(path, dtype={"row_id": str})
        if (restored.row_id.tolist() != sample.row_id.tolist()
                or not np.isfinite(restored.prediction).all() or (restored.prediction <= 0).any()):
            raise ValueError(f"Archivo guardado inválido: {name}")
        scores = {}
        for label, table in [("V23_selection", v23), ("V24", v24)]:
            row = table.loc[table.line.eq("ALL") & table.model.eq(columns[name])].iloc[0]
            scores[label] = float(row.D2)
            scores[f"{label}_without_top_0_1pct"] = float(row.D2_without_top_0_1pct)
        candidate = {
            "id": name, "prepared_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "plan": "D67, D71/T18; S05 actualizado de prueba de potencia a mezcla convexa por resultados V23",
            "candidate": model, "hypothesis": hypothesis,
            "changes": "F0 contractual; e_ef_* y exposure fuera de predictores; tasas Tweedie p=1.5 con pesos sqrt(exposure), importe por exposición nominal; balance a último por ramo una sola vez",
            "code_version": {"script": Path(__file__).relative_to(ROOT).as_posix(), "sha256": sha(Path(__file__)),
                             "training_source_snapshot": manifest["code_snapshot"]["snapshot_id"]},
            "data_version": {"F0_run": "Hackaton/Semana 1/Matriz_F0_claude/runs/f0_20261017T141732Z_65df7fca",
                             "input_hashes": manifest["input_hashes"]},
            "parameters": {"fit_power": 1.5, "evaluation_power": 1.5, "blocks": ["F0"],
                           "boosting_seeds": [2026, 42, 137] if name != "S03" else [],
                           "blend_weights": {"GLM": .5, "LightGBM_3seeds": .5} if name == "S05" else None,
                           "level": "ultimate", "development_applied_once": True,
                           "training_config": manifest["config"]},
            "validation_scheme": "V23 train 2021-2022, calibracion/seleccion por cliente; V24 train 2021-2023, eval 2024 tras congelar parámetros; D2 p=1.5 sobre T0 sin pesos. Producción a último D70, no equivale a objetivo observado V24.",
            "exact_submission_file": {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path),
                                      "rows": len(restored), "prediction_total_CU": float(restored.prediction.sum()),
                                      "prediction_min": float(restored.prediction.min()), "prediction_max": float(restored.prediction.max())},
            "local_score": scores, "public_score": None, "submitted": False, "submitted_utc": None,
            "authorized_by_participant": False,
            "production_run": run.relative_to(ROOT).as_posix(),
            "source_prediction_hashes": {p.name: sha(p) for p in source_files},
            "evidence": evidence.relative_to(ROOT).as_posix(),
        }
        registry["candidates"].append(candidate)
        prepared.append({"id": name, "V24": scores["V24"], **candidate["exact_submission_file"]})
    assert all(json.dumps(next(c for c in registry["candidates"] if c["id"] == key), sort_keys=True) == value
               for key, value in original.items())
    registry["updated_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    registry["recommended_next_submission"] = {"id": "S04", "reason": "Mayor D2 en V24 entre candidatos congelados, mejora en V23 y estabilidad de tres semillas; mantener S03 como referencia interpretable y S05 como alternativa de mezcla", "requires_participant_confirmation_after_dry_run": True}
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (evidence / "prepared_candidates.json").write_text(json.dumps(prepared, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(prepared, ensure_ascii=False))


if __name__ == "__main__":
    main()
