"""Crea y verifica un complemento de código de captura 1.1.1. No extrae ni ejecuta código del ZIP.

Uso: python herramientas/kit_captura.py crear --salida=<carpeta nueva> --base=<codigo.tar.gz histórico>
     python herramientas/kit_captura.py verificar --kit=<carpeta del complemento>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from identidad_captura import identidad_captura, version_fuente

CAPTURA_VERSION = "1.1.1"
CAPTURA_SHA = "07776e60e5f266a4f7c547ce92bcf7b3394a64a12d6a22a2db8060f141da31a0"
ARCHIVOS = (
    "herramientas/captura_modelos/captura.py", "herramientas/captura_modelos/sitecustomize.py",
    "herramientas/identidad_captura.py", "herramientas/reproducir_capturado.py", "herramientas/kit_captura.py",
    "herramientas/probar_pool_sin_huella.py", "herramientas/probar_kit_captura.py", "docs/controles/kit_captura_1_1_1.md",
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def escribir(path: Path, data: dict):
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def verificar(kit: Path) -> dict:
    manifest = json.loads((kit / "manifiesto.json").read_bytes())
    archive = kit / "captura_1_1_1.zip"
    if sha(archive.read_bytes()) != manifest["zip_sha256"]:
        raise ValueError("El ZIP no coincide con su SHA-256")
    if set(manifest["archivos"]) != set(ARCHIVOS):
        raise ValueError("El manifiesto no tiene la lista exacta de código permitida")
    with zipfile.ZipFile(archive) as z:
        if len(z.infolist()) != len(ARCHIVOS) or set(z.namelist()) != set(ARCHIVOS):
            raise ValueError("Miembros ausentes, adicionales o duplicados en el ZIP")
        for name, entry in manifest["archivos"].items():
            raw = z.read(name)
            if sha(raw) != entry["sha256"] or len(raw) != entry["bytes"]:
                raise ValueError(f"Contenido distinto: {name}")
        capture = z.read("herramientas/captura_modelos/captura.py")
        version, digest = version_fuente(capture), sha(capture)
        if version != CAPTURA_VERSION or digest != CAPTURA_SHA:
            raise ValueError("El complemento no contiene la captura 1.1.1 autorizada")
        if version != manifest["captura_version"] or digest != manifest["captura_sha256"]:
            raise ValueError("Versión o SHA declarados no coinciden con captura.py del ZIP")
    result = {"autor": "Codex", "utc": datetime.now(timezone.utc).isoformat(), "modo": "verificacion_estatica_kit",
              "estado": "conforme", "captura_version": version, "captura_sha256": digest,
              "zip_sha256": manifest["zip_sha256"], "base_codigo_sha256": manifest["base_codigo_sha256"],
              "archivos_conformes": len(ARCHIVOS), "entrenamiento": False, "ejecucion_modelos": False,
              "alcance": "Integridad y metadatos del complemento local; no instalación externa ni reproducción de predicciones."}
    receipt = kit / "recibo_kit.json"
    if receipt.exists():
        old = json.loads(receipt.read_bytes())
        for key in ("captura_version", "captura_sha256", "zip_sha256", "base_codigo_sha256"):
            if old[key] != result[key]:
                raise ValueError(f"El recibo del kit difiere en {key}")
    return result


def crear(repo: Path, salida: Path, base: Path) -> dict:
    identity = identidad_captura(repo)
    if identity["version"] != CAPTURA_VERSION or identity["sha256"] != CAPTURA_SHA:
        raise ValueError("La captura vigente no corresponde a la versión 1.1.1 autorizada")
    blobs = {name: (repo / name).read_bytes() for name in ARCHIVOS}
    if sha(blobs["herramientas/captura_modelos/captura.py"]) != CAPTURA_SHA:
        raise ValueError("La captura cambió mientras se preparaba el complemento")
    base_sha = sha(base.read_bytes())
    salida.mkdir(parents=True, exist_ok=False)
    archive = salida / "captura_1_1_1.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for name, raw in blobs.items():
            z.writestr(name, raw)
    manifest = {"autor": "Codex", "utc": datetime.now(timezone.utc).isoformat(), "tipo": "complemento_codigo_sin_datos_modelos",
                "captura_version": identity["version"], "captura_sha256": identity["sha256"],
                "base_codigo_nombre": base.name, "base_codigo_sha256": base_sha,
                "zip": archive.name, "zip_sha256": sha(archive.read_bytes()),
                "archivos": {name: {"sha256": sha(raw), "bytes": len(raw)} for name, raw in blobs.items()},
                "instalacion": "Solo sobre una copia del kit base identificado. No sustituir corridas o recibos históricos; conservar este manifiesto y emitir recibo de instalación sin ejecutar modelos."}
    escribir(salida / "manifiesto.json", manifest)
    result = verificar(salida)
    escribir(salida / "recibo_kit.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="modo", required=True)
    create = sub.add_parser("crear")
    create.add_argument("--salida", required=True, type=Path)
    create.add_argument("--base", required=True, type=Path)
    verify = sub.add_parser("verificar")
    verify.add_argument("--kit", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = crear(Path(__file__).resolve().parent.parent, args.salida, args.base) if args.modo == "crear" else verificar(args.kit)
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as exc:
        parser.exit(1, f"NO CONFORME: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
