"""Shared Week 2 transfer-model utilities.
Resolve paths, read fingerprint-verified data, compute Tweedie metrics and assign folds.
"""
from __future__ import annotations
import hashlib, json, os
from pathlib import Path
import numpy as np

RAIZ = Path(os.environ.get("MLIND_RAIZ", "/home/participant/ml"))
DATOS = RAIZ / "datos"
TRABAJO = RAIZ / "trabajo"
ENTREGA = RAIZ / "entrega"
PRIVADO = RAIZ / "privado"
V = np.datetime64("2024-12-31")
LINEAS = ["motor", "buildings", "contents"]
P = 1.5

HUELLAS = {
    "emerging/addresses.parquet": "4e9bf9d2a1777896e84fd4ee471096ff075aaefefd544f91b731324b25425632",
    "emerging/claims.parquet": "1a2fce8a26cb1e05de1f53fe4e39bde772a1898e845755487625355fec4cc0e9",
    "emerging/customers.parquet": "c00a0095d5fb7b2b65cd9647216add49afb3703d863d5c358b1441f0fab1fb62",
    "emerging/expenses.parquet": "9033f666a5a45f0b44501d57e40ab1cc571c51c384f23a62942b75db323b1cdf",
    "emerging/policies_buildings.parquet": "ccc948fafc11e623d5cb010c2b494f6813f6048719eae7bcde28794467598319",
    "emerging/policies_contents.parquet": "84d7f48d03933b018bec8fdc2f4bbd96df184cca7ae1971c38d3acc955720f8e",
    "emerging/policies_motor.parquet": "7c5dbb5e5b46629ebf01a66c991183d20b8585393b589bc2644fcbd6653a3ec1",
    "emerging/reference_policies.parquet": "6d4c2839e87d092fccd4b3c3ddc16a2a4c4993c35e18481e322462cd382dd8f4",
    "emerging/sample_submission.parquet": "160fc59043f1012337605c8d8446c0efbf81458e046cf02df9186d6f909d59ef",
    "emerging/test_buildings.parquet": "21f91aaa66a1b9efd216ad0e04ff12a507dbeb721084330d9b9f06c99edd0ca6",
    "emerging/test_contents.parquet": "af5ef2553e35a2d563ca091b173500daac55acc4969d1d3a96fa6b4ec3c6a012",
    "emerging/test_motor.parquet": "108d5c68e9bab5ccd90ee5502bc3543aa515a5aa07fda44a3b227cf070a28aa5",
    "emerging/weather.parquet": "645067069f68de8c4746d1ba48a454ff00155e1aa6fbbf64cdee48ae7269cbbd",
    "developed/addresses.parquet": "2f1a9a157649a73ed1b0ee9b2caa3660b4c2a11766af3c64ab5131389079c0b1",
    "developed/claims.parquet": "323adf2e0f6c5975a026479d725d4cd04f51fce3aa069f897a99f664c6e392c0",
    "developed/customers.parquet": "065458a0b3aa9d3499e80b3b25b76baf0ef6245146477b6861f6ea35edf581eb",
    "developed/policies_buildings.parquet": "eb84372c23c16ed0619d89c8eb1396ab6916e5ec46a5907ce42c3dfce4a91cbe",
    "developed/policies_contents.parquet": "8c067cc80baed583100df999e1c3d5e389295702f7bac21d5331bbd639b83fcd",
    "developed/policies_motor.parquet": "4d2d7ae03971d5d6df3a71bbaf0ebc168250a6807b27d1561d38b638434dc95e",
    "developed/weather.parquet": "b8407f0f3c7279a49297c969a4ab2905641b232910e316fb806730065987cd49",
}


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def comprobar_huellas() -> dict:
    out = {}
    for rel, esperado in HUELLAS.items():
        obs = sha256(DATOS / rel)
        if obs != esperado:
            raise SystemExit(f"Huella distinta en {rel}: {obs}")
        out[rel] = obs
    return out


def pliegue(customer_ids) -> np.ndarray:
    return np.array([int(hashlib.sha256(("mlind_v1|" + c).encode()).hexdigest()[:16], 16) % 5
                     for c in customer_ids], dtype=np.int8)


def desviacion(y, mu, w=None, p=P):
    y = np.asarray(y, float); mu = np.asarray(mu, float)
    d = 2 * (np.power(np.maximum(y, 0), 2 - p) / ((1 - p) * (2 - p)) - y * np.power(mu, 1 - p) / (1 - p)
             + np.power(mu, 2 - p) / (2 - p))
    return d if w is None else d * w


def d2(y, mu, w=None, p=P) -> float:
    y = np.asarray(y, float); mu = np.asarray(mu, float)
    w = np.ones_like(y) if w is None else np.asarray(w, float)
    ybar = np.sum(w * y) / np.sum(w)
    return 1 - np.sum(desviacion(y, mu, w, p)) / np.sum(desviacion(y, np.full_like(y, ybar), w, p))


def factor_tweedie(y, mu, w=None):
    """Return k minimizing power-1.5 Tweedie deviance of k*mu."""
    w = np.ones_like(np.asarray(y, float)) if w is None else w
    return float(np.sum(w * y / np.sqrt(mu)) / np.sum(w * np.sqrt(mu)))


def guardar_json(obj, path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, default=float)
