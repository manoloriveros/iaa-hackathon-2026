"""Prepara los archivos de envío S01 y S02 del plan D67 (referencia M00: tasa constante por ramo x exposición) y los
anota en registro_envios.json con los campos de D29. No envía nada: el envío lo hace o lo autoriza el participante.

S01: tasa por ramo = suma de T0 2021-2024 / suma de exposición 2021-2024 (balance), multiplicada por la exposición de
     cada fila de test. Hipótesis: la escala local (V24) y la pública coinciden.
S02: tasa por ramo = (T0 + IBNR de coste 2021-2024) / exposición 2021-2024, con el IBNR del chain-ladder D67.
     Hipótesis: la etiqueta de 2025 está valorada a nivel último; si S02 puntúa más que S01, los modelos deben predecir
     a nivel último.

Lee la capa vigente (current_dataset.json) y la corrida vigente de Bases_actuariales_claude, comprueba hashes, escribe
archivos/<ID>_<nombre>.csv con columnas row_id,prediction en el orden de sample_submission y actualiza el registro.
Uso: python3 'Hackaton/Semana 1/Envios/preparar_envio_m00.py'
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "RUTAS_PROYECTO.json").is_file():
            return candidate
    raise FileNotFoundError("No se encontró RUTAS_PROYECTO.json hacia arriba.")


ROOT = find_root(HERE)
try:
    import pyarrow  # noqa: F401
except ImportError:  # pragma: no cover
    sys.path.insert(0, str(ROOT / "Preparación" / ".cache" / "parquet-reader"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

LINES = ["motor", "buildings", "contents"]
POWER = 1.5


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def deviance(y, mu, p=POWER):
    y = np.asarray(y, float)
    mu = np.asarray(mu, float)
    return 2.0 * (np.power(y, 2 - p) / ((1 - p) * (2 - p)) - y * np.power(mu, 1 - p) / (1 - p) + np.power(mu, 2 - p) / (2 - p))


def d2(y, mu, p=POWER):
    y = np.asarray(y, float)
    return float(1 - deviance(y, mu, p).sum() / deviance(y, np.full_like(y, y.mean()), p).sum())


def main() -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    current = json.loads((ROOT / "Hackaton/Semana 1/Limpieza/current_dataset.json").read_text(encoding="utf-8"))
    catalog_path = ROOT / current["catalog_workspace_relative"]
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    bad = [t for t in ["test_motor", "test_buildings", "test_contents", "sample_submission"] if digest(ROOT / catalog[t]["workspace_relative_path"]) != catalog[t]["sha256"]]
    if bad:
        raise SystemExit(f"Hash distinto del catálogo: {bad}")
    bases_index = json.loads((ROOT / "Hackaton/Semana 1/Bases_actuariales_claude/current_run.json").read_text(encoding="utf-8"))
    bases_run = ROOT / bases_index["workspace_relative_run"]
    manifest = json.loads((bases_run / "manifest.json").read_text(encoding="utf-8"))
    for name in ["tables/t0_por_row_id.parquet", "tables/ibnr_por_peligro_anio.csv"]:
        if digest(bases_run / name) != manifest[name]:
            raise SystemExit(f"Hash distinto del manifiesto de bases: {name}")
    evidence = json.loads((bases_run / "evidencia.json").read_text(encoding="utf-8"))
    if evidence["provenance"]["active_run"] != current["workspace_relative_run"]:
        raise SystemExit("La corrida de bases no corresponde a la capa activa; repetir bases_actuariales.py")

    t0 = pd.read_parquet(bases_run / "tables/t0_por_row_id.parquet", columns=["row_id", "line", "year", "exposure", "T0"])
    ibnr = pd.read_csv(bases_run / "tables/ibnr_por_peligro_anio.csv")
    ibnr_line_year = ibnr.groupby(["line", "year"])["ibnr_coste_CU"].sum()

    def rates(years, ultimate: bool) -> dict:
        sub = t0[t0.year.isin(years)]
        out = {}
        for line in LINES:
            s = sub[sub.line == line]
            num = float(s.T0.sum()) + (float(sum(ibnr_line_year[(line, y)] for y in years)) if ultimate else 0.0)
            out[line] = num / float(s.exposure.sum())
        return out

    variants = {
        "S01": {"name": "m00_tasa_ramo_T0", "ultimate": False,
                "hypothesis": "La escala local V24 y la pública coinciden: una tasa constante por ramo a nivel T0 debería puntuar cerca de 0,07 (V24 local 0,07094; referencia pública de coste medio 0,07169 en la captura D64)",
                "changes": "Primera predicción del proyecto: tasa constante por ramo = suma de T0 2021-2024 / suma de exposición 2021-2024, por la exposición de la fila"},
        "S02": {"name": "m00_tasa_ramo_ultimo", "ultimate": True,
                "hypothesis": "La etiqueta de 2025 está valorada a nivel último: añadir el IBNR de coste 2021-2024 del chain-ladder D67 a la tasa por ramo debería mejorar el D² público frente a S01",
                "changes": "Respecto de S01, solo cambia el nivel: tasa = (T0 + IBNR de coste 2021-2024) / exposición 2021-2024"},
    }
    sample = pd.read_parquet(ROOT / catalog["sample_submission"]["workspace_relative_path"], columns=["row_id"])
    test = pd.concat([pd.read_parquet(ROOT / catalog[f"test_{l}"]["workspace_relative_path"], columns=["row_id", "exposure"]).assign(line=l) for l in LINES], ignore_index=True)
    test = sample.merge(test, on="row_id", how="left", validate="one_to_one")
    if test.exposure.isna().any() or len(test) != 626639 or not test.row_id.is_unique:
        raise SystemExit("La plantilla y los test no coinciden en 626.639 row_id únicos")

    out_dir = HERE / "archivos"
    out_dir.mkdir(exist_ok=True)
    registry_path = HERE / "registro_envios.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.is_file() else {
        "schema": "D29: hypothesis, changes, code_version, data_version, parameters, validation_scheme, exact_submission_file, local_score, public_score",
        "note": "Cada envío requiere autorización expresa del participante; submitted y public_score los completa quien envía.", "candidates": []}
    v24_eval = t0[t0.year == 2024]
    for sid, spec in variants.items():
        q = rates([2021, 2022, 2023, 2024], spec["ultimate"])
        q_v24 = rates([2021, 2022, 2023], spec["ultimate"])
        pred = test.exposure * test.line.map(q)
        if not (np.isfinite(pred).all() and (pred > 0).all()):
            raise SystemExit(f"{sid}: predicciones no finitas o no positivas")
        mu_v24 = v24_eval.exposure * v24_eval.line.map(q_v24)
        local = {"V24_d2_global_sobre_T0": round(d2(v24_eval.T0, mu_v24), 5),
                 **{f"V24_d2_{l}_sobre_T0": round(d2(v24_eval.T0[v24_eval.line == l], mu_v24[v24_eval.line == l]), 5) for l in LINES},
                 **{f"V24_balance_{l}_pred_sobre_T0": round(float(mu_v24[v24_eval.line == l].sum() / v24_eval.T0[v24_eval.line == l].sum()), 4) for l in LINES},
                 "nota": "V24 se puntúa con T0 de 2024, que está incompleto (D67); para S02 el D² local no puede mostrar la ganancia de nivel que se contrasta en público"}
        path = out_dir / f"{sid}_{spec['name']}.csv"
        pd.DataFrame({"row_id": test.row_id, "prediction": pred.round(6)}).to_csv(path, index=False, float_format="%.6f")
        back = pd.read_csv(path, dtype={"row_id": str})
        ok = len(back) == 626639 and list(back.columns) == ["row_id", "prediction"] and (back.row_id.values == sample.row_id.values).all() and (back.prediction > 0).all()
        if not ok:
            raise SystemExit(f"{sid}: el archivo releído no cumple el formato")
        entry = {
            "id": sid, "prepared_utc": now, "plan": "D67 PLAN_PRUEBAS.md sección 6.2", "candidate": "M00", "hypothesis": spec["hypothesis"], "changes": spec["changes"],
            "code_version": {"script": "Hackaton/Semana 1/Envios/preparar_envio_m00.py", "sha256": digest(Path(__file__))},
            "data_version": {"active_run": current["workspace_relative_run"], "catalog_sha256": digest(catalog_path), "bases_run": bases_index["workspace_relative_run"]},
            "parameters": {"rate_per_exposed_year_CU": {l: round(q[l], 4) for l in LINES}, "rate_V24_2021_2023_CU": {l: round(q_v24[l], 4) for l in LINES},
                           "level": "ultimo (T0 + IBNR D67)" if spec["ultimate"] else "T0 observado", "power_eval": POWER},
            "validation_scheme": "V24: tasa estimada con 2021-2023 y evaluada sobre T0 de 2024 con D² Tweedie p=1,5 sin pesos",
            "exact_submission_file": {"path": f"Hackaton/Semana 1/Envios/archivos/{path.name}", "sha256": digest(path), "rows": 626639,
                                      "prediction_total_CU": round(float(pred.sum()), 2), "prediction_total_by_line_CU": {l: round(float(pred[test.line == l].sum()), 2) for l in LINES},
                                      "prediction_min": round(float(pred.min()), 6), "prediction_max": round(float(pred.max()), 6)},
            "local_score": local, "public_score": None, "submitted": False, "submitted_utc": None, "authorized_by_participant": False,
        }
        registry["candidates"] = [c for c in registry["candidates"] if c["id"] != sid] + [entry]
        print(f"{sid}: {path.name} sha256 {entry['exact_submission_file']['sha256'][:16]}… tasas {entry['parameters']['rate_per_exposed_year_CU']} V24 {local['V24_d2_global_sobre_T0']}")
    registry["candidates"].sort(key=lambda c: c["id"])
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
