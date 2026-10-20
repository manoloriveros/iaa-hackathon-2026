"""Preflight documental para otro entorno. No instala, ajusta, infiere o mezcla.

Un recibo de esta herramienta no satisface por sí solo GOV-003. El operador y su
identidad son declaraciones; la independencia y la reproducción completa siguen
requiriendo evidencia adicional.
"""
import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operador", required=True)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    if not args.operador.strip():
        parser.error("Identifique al operador real; no se infiere una persona.")
    repo = Path(__file__).resolve().parents[1]
    manifest = json.loads((repo / "receta/codigo.json").read_bytes())
    entries = dict(manifest["archivos"])
    package = manifest.get("paquete", {})
    # El manifiesto recibido guarda el runtime separado de los scripts históricos.
    runtime = package.get("archivos", {})
    entries.update(runtime)
    checks = []
    for rel, meta in entries.items():
        path = (repo / rel).resolve()
        if not path.is_relative_to(repo.resolve()):
            raise ValueError("Una ruta del manifiesto sale del repositorio")
        expected = meta["sha256"] if isinstance(meta, dict) else meta
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        checks.append({"ruta": rel, "esperado": expected, "actual": actual, "coincide": actual == expected})
    versions = {}
    for name in ["numpy", "pandas", "pyarrow", "scipy", "scikit-learn", "lightgbm", "catboost", "torch"]:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    result = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "operador_declarado": args.operador,
              "identidad_verificada_por_herramienta": False,
              "entorno": {"python": sys.version, "ejecutable": sys.executable, "plataforma": platform.platform(), "paquetes": versions},
              "manifest_sha256": hashlib.sha256((repo/"receta/codigo.json").read_bytes()).hexdigest(),
              "receta_sha256": hashlib.sha256((repo/"receta/receta.json").read_bytes()).hexdigest(),
              "alcance": "preflight de código y entorno, sin ejecución de modelos o datos",
              "controles": checks, "conforme_codigo": bool(checks) and all(c["coincide"] for c in checks),
              "reproduccion_completa": False, "independencia_acreditada": False,
              "impedimento": "CLA004 informa modelos no persistidos: el recorrido completo requiere nuevos ajustes, fuera de la restricción vigente."}
    with args.salida.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"conforme_codigo": result["conforme_codigo"], "archivos": len(checks), "reproduccion_completa": False}))
    return 0 if result["conforme_codigo"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
