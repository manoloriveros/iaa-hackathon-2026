"""Configuración, contrato de datos y particiones preservadas."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import GroupKFold, KFold, TimeSeriesSplit

SUPPORTED_METRICS = {"rmsle", "rmse", "mae"}
SUPPORTED_MODELS = {"dummy", "ridge", "hist_gradient_boosting", "catboost", "lightgbm", "xgboost"}


def find_root(start: Path | None = None) -> Path:
    configured = os.environ.get("IAA_PROJECT_ROOT")
    if configured:
        root = Path(configured).resolve()
        if (root / "configs" / "demo.yaml").is_file():
            return root
        raise ValueError("IAA_PROJECT_ROOT no apunta a este proyecto.")
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "configs" / "demo.yaml").is_file():
            return candidate
    raise FileNotFoundError("Abre el notebook dentro del proyecto o define IAA_PROJECT_ROOT.")


def load_config(path: Path) -> dict:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("La configuración YAML debe contener un objeto.")
    if config.get("mode") not in {"demo", "competition"}:
        raise ValueError("mode debe ser demo o competition.")
    if config["mode"] == "competition" and config.get("rules_confirmed") is not True:
        raise ValueError(
            "Confirma las reglas de 2026 con rules_confirmed antes de usar datos reales."
        )
    required = [
        "train_path",
        "test_path",
        "sample_submission_path",
        "id_column",
        "target_column",
        "metric",
    ]
    for key in required:
        if not config.get(key) or str(config[key]).upper() == "TODO":
            raise ValueError(f"Completa {key} en la configuración.")
    if config["metric"] not in SUPPORTED_METRICS:
        raise ValueError(
            f"Métrica no implementada: {config['metric']}. Disponibles: {sorted(SUPPORTED_METRICS)}"
        )
    models = config.get("models", [])
    if not models or len(models) != len(set(models)) or set(models) - SUPPORTED_MODELS:
        raise ValueError("models debe contener nombres implementados, sin duplicados.")
    if config.get("selection_model") not in {*models, "best_cv"}:
        raise ValueError("selection_model debe ser best_cv o uno de los modelos configurados.")
    split = config.get("split", {})
    if split.get("strategy") not in {"kfold", "group", "time"}:
        raise ValueError("split.strategy debe ser kfold, group o time.")
    if not isinstance(split.get("n_splits"), int) or split["n_splits"] < 2:
        raise ValueError("Se necesitan al menos dos folds.")
    hypothesis = config.get("experiment", {}).get("hypothesis", "")
    if not hypothesis or str(hypothesis).upper() == "TODO":
        raise ValueError("Escribe la hipótesis antes de correr el experimento.")
    return config


def input_paths(root: Path, config: dict) -> dict[str, Path]:
    return {
        key: (root / config[key]).resolve()
        for key in ("train_path", "test_path", "sample_submission_path")
    }


def validate_frames(
    train: pd.DataFrame, test: pd.DataFrame, sample: pd.DataFrame, config: dict
) -> None:
    id_col, target = config["id_column"], config["target_column"]
    if id_col == target:
        raise ValueError("El identificador y el objetivo deben ser columnas distintas.")
    for name, frame in [("train", train), ("test", test), ("sample_submission", sample)]:
        if frame.empty or id_col not in frame:
            raise ValueError(f"{name} está vacío o no contiene {id_col}.")
        if frame[id_col].isna().any() or frame[id_col].duplicated().any():
            raise ValueError(f"{name} contiene identificadores nulos o duplicados.")
    if target not in train or target not in sample:
        raise ValueError("El objetivo debe existir en train y sample_submission.")
    if target in test:
        raise ValueError("El test no debe contener el objetivo. Revisa la procedencia del archivo.")
    if set(train.columns) - {target} != set(test.columns):
        raise ValueError("Las columnas predictoras de train y test no coinciden.")
    if list(sample.columns) != [id_col, target]:
        raise ValueError(
            "Esta plantilla de regresión espera sample_submission con ID y objetivo, en ese orden."
        )
    if len(sample) != len(test) or set(sample[id_col]) != set(test[id_col]):
        raise ValueError("Los identificadores de sample_submission y test no coinciden.")
    if set(train[id_col]) & set(test[id_col]):
        raise ValueError("Hay identificadores de observación repetidos entre train y test.")
    y = pd.to_numeric(train[target], errors="raise").to_numpy(dtype=float)
    if not np.isfinite(y).all():
        raise ValueError("El objetivo contiene valores nulos o no finitos.")
    if config["metric"] == "rmsle" and (y < 0).any():
        raise ValueError("RMSLE exige objetivos no negativos.")
    for key in ("group_column", "time_column"):
        column = config["split"].get(key)
        if column and (column not in train or train[column].isna().any()):
            raise ValueError(f"{key} debe existir y no contener nulos.")


def read_data(root: Path, config: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    paths = input_paths(root, config)
    frames = [pd.read_csv(path) for path in paths.values()]
    validate_frames(*frames, config)
    return tuple(frames)


def feature_frames(
    train: pd.DataFrame, test: pd.DataFrame, config: dict
) -> tuple[pd.DataFrame, pd.DataFrame]:
    excluded = {
        config["id_column"],
        config["target_column"],
        config["split"].get("group_column"),
        config["split"].get("time_column"),
    }
    columns = [column for column in train if column not in excluded]
    if not columns:
        raise ValueError("No quedan variables predictoras.")
    prepared = []
    for frame in (train[columns], test[columns]):
        frame = frame.copy()
        for column in frame:
            if pd.api.types.is_numeric_dtype(frame[column]):
                if np.isinf(frame[column].to_numpy(dtype=float)).any():
                    raise ValueError(f"{column} contiene infinito.")
            else:
                # Conversión fija de tipos. No calcula estadísticas ni usa el objetivo.
                frame[column] = frame[column].astype(object).where(frame[column].notna(), np.nan)
        prepared.append(frame)
    return tuple(prepared)


def make_splits(train: pd.DataFrame, config: dict) -> list[tuple[np.ndarray, np.ndarray]]:
    split = config["split"]
    n_splits = split["n_splits"]
    strategy = split["strategy"]
    if strategy == "kfold":
        iterator = KFold(n_splits=n_splits, shuffle=True, random_state=split["seed"])
        folds = list(iterator.split(train))
    elif strategy == "group":
        group_col = split.get("group_column")
        if not group_col:
            raise ValueError("La validación por grupo necesita group_column.")
        folds = list(GroupKFold(n_splits=n_splits).split(train, groups=train[group_col]))
    else:
        time_col = split.get("time_column")
        if not time_col:
            raise ValueError("La validación temporal necesita time_column.")
        dates = pd.to_datetime(train[time_col], errors="raise", utc=True)
        periods = np.sort(dates.unique())
        iterator = TimeSeriesSplit(n_splits=n_splits, gap=split.get("gap_periods", 0))
        folds = [
            (np.flatnonzero(dates.isin(periods[a])), np.flatnonzero(dates.isin(periods[b])))
            for a, b in iterator.split(periods)
        ]
    for a, b in folds:
        if not len(a) or not len(b) or set(a) & set(b):
            raise ValueError("Una partición está vacía o mezcla entrenamiento y validación.")
    return folds


def make_submission(
    sample: pd.DataFrame, test: pd.DataFrame, predictions: np.ndarray, config: dict
) -> pd.DataFrame:
    predictions = np.asarray(predictions, dtype=float)
    if len(predictions) != len(test) or not np.isfinite(predictions).all():
        raise ValueError("Las predicciones tienen longitud incorrecta o valores no finitos.")
    if config["metric"] == "rmsle" and (predictions < 0).any():
        raise ValueError("No se pueden entregar predicciones negativas para RMSLE.")
    id_col, target = config["id_column"], config["target_column"]
    by_id = pd.Series(predictions, index=test[id_col].to_numpy())
    result = sample.copy()
    result[target] = result[id_col].map(by_id)
    if result[target].isna().any():
        raise ValueError("No se pudo alinear la salida con sample_submission.")
    return result
