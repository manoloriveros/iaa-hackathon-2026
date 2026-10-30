"""Inventory frozen recipe artifacts from their original run directories.

For every recipe output, try <source>/<path>, <source>/runs/<path> and the recorded
selection-table locations. Inspect Week 1 inputs in the same way. Record file
size, byte SHA-256, content fingerprint and provenance in
receta/huellas_esperadas.json, and report missing files.

Usage: python herramientas/inventario.py --semana1=<directory> --origen=<directory>
Repeat --origen to search additional source directories.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from huella import huellas  # noqa: E402

REPO = AQUI.parent


def localizar(rel: str, origenes: list[Path]) -> Path | None:
    for o in origenes:
        cands = [o / rel, o / "runs" / rel]
        name = Path(rel).name
        if "/" not in rel and name.startswith("sel_"):
            corrida = name[4:-8]
            cands += [o / "runs" / corrida / name, o / "selecciones_v23" / name, o / corrida / name]
        for c in cands:
            if c.is_file():
                return c
    # Last selection-table fallback: a nested run such as runs/S08h_hogar_F3s2/sel_hS2.parquet.
    if "/" not in rel and Path(rel).name.startswith("sel_"):
        for o in origenes:
            hall = sorted((o / "runs").glob(f"*/{Path(rel).name}")) if (o / "runs").is_dir() else []
            if hall:
                return hall[0]
    return None


def main():
    opts = [a for a in sys.argv[1:] if a.startswith("--")]
    semana1 = Path(next(a.split("=", 1)[1] for a in opts if a.startswith("--semana1=")))
    origenes = [Path(a.split("=", 1)[1]) for a in opts if a.startswith("--origen=")]
    receta = json.loads((REPO / "receta" / "receta.json").read_text(encoding="utf-8"))
    out = {"creado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "origenes": [str(o) for o in origenes],
           "semana1": str(semana1), "entradas": {}, "salidas": {}, "faltan": []}
    for rel in receta["entradas"]["archivos"]:
        p = semana1 / rel
        if p.is_file():
            out["entradas"][rel] = huellas(p) | {"origen": str(p)}
        else:
            out["faltan"].append(rel)
    for n in receta["nodos"]:
        for rel in n["salidas"]:
            p = localizar(rel, origenes)
            if p is None:
                out["faltan"].append(rel)
                continue
            out["salidas"][rel] = huellas(p) | {"origen": str(p), "nodo": n["id"]}
            print(n["id"], rel, out["salidas"][rel]["sha256"][:12], flush=True)
    (REPO / "receta" / "huellas_esperadas.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("salidas:", len(out["salidas"]), "entradas:", len(out["entradas"]), "faltan:", out["faltan"])


if __name__ == "__main__":
    main()
