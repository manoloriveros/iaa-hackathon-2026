"""Identidad de la fuente de captura, sin importarla ni activar ganchos de modelos."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path


def version_fuente(raw: bytes) -> str:
    values = [n.value for n in ast.parse(raw).body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == "VERSION" for t in n.targets)]
    if len(values) != 1 or not isinstance(values[0], ast.Constant) or not isinstance(values[0].value, str):
        raise ValueError("captura.py debe declarar un único VERSION literal de texto")
    return values[0].value


def identidad_captura(repo: Path) -> dict:
    raw = (repo / "herramientas/captura_modelos/captura.py").read_bytes()
    site = (repo / "herramientas/captura_modelos/sitecustomize.py").read_bytes()
    return {"version": version_fuente(raw), "sha256": hashlib.sha256(raw).hexdigest(),
            "ruta": "herramientas/captura_modelos/captura.py", "sitecustomize_sha256": hashlib.sha256(site).hexdigest()}
