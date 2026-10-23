"""Regenera la entrega final de la parte 1 (S42) a partir de S30, la compara con el archivo entregado y deja un recibo.

S42 es S30 con las predicciones de cada ramo multiplicadas por un factor de nivel 2025 (decisión D101): autos 0,9838,
edificios 1,0413 y contenidos 1,0579, con todos sus decimales en registro/sonda_nivel_D101_revision.json. La orden que
lo produjo, `herramientas/sonda_nivel.py revisar`, reescribe además el CSV entregado y sus notas; esta herramienta solo
lee, escribe la copia regenerada dentro de privado/ (fuera de Git) y un recibo sin datos por fila en
docs/evidencia/entrega_final_S42.json, con los diez controles de entrega que preflight.json aplica a S30.

    python herramientas/regenerar_s42.py --raiz C:/dev/Hakaton [--s30 S30.csv] [--salida copia.csv] [--sin-recibo]

S30 se obtiene con `python reproducir.py mezcla --objetivo=S30`. Necesita pandas y pyarrow (lee los test originales
para saber el ramo de cada fila y la plantilla para el orden). Código de salida: 0 si la copia regenerada tiene el
SHA-256 de la entrega final y los diez controles pasan, 1 si no, 2 si S30 no es el archivo entregado.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAMOS = ("motor", "buildings", "contents")
REVISION = REPO / "registro" / "sonda_nivel_D101_revision.json"
RECIBOS = REPO / "registro" / "envios_S41_S42_20261022_recibos.json"
RECIBO_SALIDA = REPO / "docs" / "evidencia" / "entrega_final_S42.json"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(p: Path, raiz: Path) -> str:
    try:
        return p.resolve().relative_to(raiz).as_posix()
    except ValueError:
        return str(p)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raiz", type=Path, default=REPO.parents[1], help="raíz del proyecto (contiene Hackaton/Semana 1)")
    ap.add_argument("--s30", type=Path, help="CSV de S30; por defecto, el archivo entregado en Envios/archivos")
    ap.add_argument("--salida", type=Path, default=REPO / "privado" / "regeneracion_S42" / "S42_regenerado.csv")
    ap.add_argument("--sin-recibo", action="store_true", help="no escribir docs/evidencia/entrega_final_S42.json")
    a = ap.parse_args()
    raiz = a.raiz.resolve()
    datos = raiz / "Hackaton" / "Semana 1" / "Datos"
    nota = json.loads(REVISION.read_text(encoding="utf-8"))
    s42, base = nota["revision"]["S42"], nota["base"]
    recibo_kaggle = next(x for x in json.loads(RECIBOS.read_text(encoding="utf-8"))["receipts"] if x["code"] == "S42")

    s30 = a.s30 or raiz / base["archivo"]
    if sha256(s30) != base["sha256"]:
        print(json.dumps({"estado": "S30 distinto del entregado", "s30": str(s30)}, ensure_ascii=False))
        return 2
    df = pd.read_csv(s30, dtype={"row_id": str, "prediction": float})
    lineas = pd.concat([pd.read_parquet(datos / f"test_{r}.parquet", columns=["row_id"]).assign(line=r) for r in RAMOS]).set_index("row_id")["line"]
    lin = lineas.reindex(df.row_id).values
    for r in RAMOS:
        df.loc[lin == r, "prediction"] = df.loc[lin == r, "prediction"] * s42["factores_aplicados"][r]
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.salida, index=False, float_format="%.6f", lineterminator="\n")
    h_reg = sha256(a.salida)

    # Controles de entrega sobre el archivo entregado, los mismos diez que preflight.json registra para S30.
    entregado = raiz / s42["archivo"]
    h_ent = sha256(entregado)
    e = pd.read_csv(entregado, dtype={"row_id": str, "prediction": float})
    plantilla = pd.read_parquet(datos / "sample_submission.parquet", columns=["row_id"]).row_id.astype(str)
    v = e.prediction.to_numpy()
    lin_e = lineas.reindex(e.row_id).values
    checks = {
        "columnas_exactas": list(e.columns) == ["row_id", "prediction"],
        "filas": len(e) == s42["filas"],
        "ids_unicos": bool(e.row_id.is_unique),
        "ids_y_orden_sample": len(e) == len(plantilla) and bool((e.row_id.values == plantilla.values).all()),
        "cobertura_tres_test": set(e.row_id) == set(lineas.index),
        "valores_finitos_no_negativos": bool(np.isfinite(v).all() and (v >= 0).all()),
        "predicciones_positivas": bool((v > 0).all()),
        "sha_entrega": h_ent == s42["sha256"],
        "sha_recibo": h_ent == recibo_kaggle["sha256"],
        "recibo_puntuado": recibo_kaggle.get("kaggle_status") == "COMPLETE" and recibo_kaggle.get("public_score") is not None,
    }
    pasa = all(checks.values()) and h_reg == h_ent
    salida = {
        "candidato": "S42", "id": nota["id"], "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "herramienta": "herramientas/regenerar_s42.py",
        "archivo_entregado": s42["archivo"], "sha256": h_ent, "filas": int(len(e)),
        "min": round(float(v.min()), 6), "max": round(float(v.max()), 6), "total_CU": round(float(v.sum()), 2),
        "por_ramo_CU": {r: round(float(v[lin_e == r].sum()), 2) for r in RAMOS},
        "base_S30": {"archivo": base["archivo"], "sha256": base["sha256"], "publico": base["publico"]},
        "factores_nivel": s42["factores_aplicados"],
        "regeneracion": {"copia": rel(a.salida, raiz), "sha256": h_reg, "igual_al_entregado": h_reg == h_ent},
        "checks": checks, "pasa": pasa,
        "submission_id": recibo_kaggle["kaggle_submission_id"], "public_score": recibo_kaggle["public_score"],
        "recibo_kaggle": "registro/envios_S41_S42_20261022_recibos.json", "decision": "D101 y CIE-D101 (selección final manual del participante, 22-10-2026)",
    }
    if not a.sin_recibo:
        RECIBO_SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: salida[k] for k in ("sha256", "total_CU", "regeneracion", "checks", "pasa")}, ensure_ascii=False))
    return 0 if pasa else 1


if __name__ == "__main__":
    sys.exit(main())
