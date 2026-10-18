"""Verifica S01 y S02 sin regenerar archivos ni enviar predicciones."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "Preparación" / ".cache" / "parquet-reader"))

import numpy as np
import pandas as pd


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    routes = json.loads((ROOT / "RUTAS_PROYECTO.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / routes["week_1_submissions_registry"]).read_text(encoding="utf-8"))
    active = json.loads((ROOT / routes["week_1_prepared_data_index"]).read_text(encoding="utf-8"))
    catalog_path = ROOT / active["catalog_workspace_relative"]
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    sample_path = ROOT / routes["week_1_data"] / "sample_submission.parquet"
    if digest(sample_path) != catalog["sample_submission"]["sha256"]:
        raise ValueError("La plantilla original cambió.")
    sample = pd.read_parquet(sample_path)
    if list(sample) != ["row_id", "prediction"] or sample.row_id.duplicated().any():
        raise ValueError("Plantilla inválida.")
    # Copia derivada para el skill, cuyo validador solo lee CSV.
    sample.to_csv(output / "sample_submission.csv", index=False)
    results = []
    for candidate in registry["candidates"]:
        if candidate["id"] not in {"S01", "S02"}:
            continue
        file = ROOT / candidate["exact_submission_file"]["path"]
        if digest(file) != candidate["exact_submission_file"]["sha256"]:
            raise ValueError(f"Archivo distinto del registro: {candidate['id']}")
        if digest(ROOT / candidate["code_version"]["script"]) != candidate["code_version"]["sha256"]:
            raise ValueError("El generador cambió respecto al registro.")
        if candidate["data_version"]["active_run"] != active["workspace_relative_run"]:
            raise ValueError("La capa activa cambió.")
        if digest(catalog_path) != candidate["data_version"]["catalog_sha256"]:
            raise ValueError("El catálogo activo cambió.")
        frame = pd.read_csv(file, dtype={"row_id": str})
        if list(frame) != list(sample) or frame.row_id.tolist() != sample.row_id.tolist():
            raise ValueError("Identificadores, orden o columnas distintos de la plantilla.")
        values = frame.prediction.to_numpy(float)
        if not np.isfinite(values).all() or (values <= 0).any():
            raise ValueError("Predicciones no positivas o no finitas.")
        if len(frame) != candidate["exact_submission_file"]["rows"]:
            raise ValueError("Número de filas distinto del registro.")
        results.append(dict(id=candidate["id"], sha256=digest(file), rows=len(frame),
                            prediction_total=float(values.sum()), status="verified_not_submitted"))
    report = dict(checked_utc=datetime.now(timezone.utc).isoformat(), candidates=results,
                  sample_parquet_sha256=digest(sample_path),
                  sample_csv_sha256=digest(output / "sample_submission.csv"), submissions_made=0)
    (output / "validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
