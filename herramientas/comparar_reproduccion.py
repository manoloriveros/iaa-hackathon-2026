"""Compara numéricamente dos carpetas work/ de la receta, o una carpeta work/ con las corridas guardadas del equipo.

reproducir.py exige igualdad exacta de contenido, que es lo correcto en el entorno de referencia. En otro entorno (otro
sistema, otras versiones de numpy, LightGBM o CatBoost) los ajustes pueden diferir en los últimos bits y propagarse por la
parada temprana. Esta herramienta mide cuánto: para cada artefacto de la receta presente en las dos carpetas informa si es
idéntico, y si no, la diferencia absoluta y relativa máxima de cada columna numérica, la diferencia de totales y, cuando hay
etiqueta y predicción (sel_*, v24.parquet), el cambio de D² Tweedie 1,5. Para los CSV finales informa además el SHA-256.
No ajusta, no mezcla ni corrige nada; no decide si una diferencia es aceptable: eso lo fija quien revisa.

Uso: python herramientas/comparar_reproduccion.py <work_a> <work_b> [--salida=<json>] [--nodos=n1,n2]
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
P = 1.5


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def d2(y, mu):
    y = np.asarray(y, float); mu = np.asarray(mu, float)

    def dev(y, mu):
        return 2.0 * (np.power(y, 2 - P) / ((1 - P) * (2 - P)) - y * np.power(mu, 1 - P) / (1 - P) + np.power(mu, 2 - P) / (2 - P))
    return float(1.0 - dev(y, mu).sum() / dev(y, np.full_like(y, y.mean())).sum())


def cargar(p: Path):
    if p.suffix == ".parquet":
        import pandas as pd
        return pd.read_parquet(p)
    if p.suffix == ".npy":
        return np.load(p)
    if p.suffix == ".npz":
        z = np.load(p)
        return {k: z[k] for k in z.files}
    if p.suffix == ".csv":
        import pandas as pd
        return pd.read_csv(p, dtype={"row_id": str})
    return None


def comparar_arrays(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    if a.shape != b.shape:
        return {"forma_distinta": [list(a.shape), list(b.shape)]}
    dif = np.abs(a - b)
    den = np.maximum(np.abs(a), 1e-300)
    return {"iguales": int((a == b).sum()), "n": int(a.size), "max_abs": float(dif.max()) if a.size else 0.0,
            "max_rel": float((dif / den).max()) if a.size else 0.0, "total_a": float(a.sum()), "total_b": float(b.sum()),
            "rel_total": float(b.sum() / a.sum() - 1.0) if a.sum() else None}


def comparar(pa: Path, pb: Path):
    r = {"sha_igual": sha(pa) == sha(pb)}
    if r["sha_igual"]:
        return r
    A, B = cargar(pa), cargar(pb)
    if A is None:
        r["nota"] = "formato sin comparación numérica"
        return r
    if isinstance(A, dict):
        r["miembros"] = {k: comparar_arrays(A[k], B[k]) for k in A if k in B}
        return r
    if isinstance(A, np.ndarray):
        r["valores"] = comparar_arrays(A, B)
        return r
    cols = [c for c in A.columns if c in B.columns]
    if "row_id" in cols and not (A["row_id"].astype(str).values == B["row_id"].astype(str).values).all():
        B = B.set_index(B["row_id"].astype(str)).loc[A["row_id"].astype(str)].reset_index(drop=True)
        r["filas_reordenadas"] = True
    r["columnas"] = {}
    for c in cols:
        if A[c].dtype.kind in "fiu" and B[c].dtype.kind in "fiu":
            r["columnas"][c] = comparar_arrays(A[c].values, B[c].values)
        else:
            r["columnas"][c] = {"iguales": bool((A[c].astype(str).values == B[c].astype(str).values).all())}
    if "y" in cols and "mu" in cols:
        r["d2_a"], r["d2_b"] = d2(A["y"], A["mu"]), d2(B["y"], B["mu"])
        r["d2_dif"] = r["d2_b"] - r["d2_a"]
    return r


def main():
    wa, wb = Path(sys.argv[1]), Path(sys.argv[2])
    o = dict(a[2:].split("=", 1) for a in sys.argv[3:] if a.startswith("--") and "=" in a)
    receta = json.loads((REPO / "receta" / "receta.json").read_text(encoding="utf-8"))
    solo = set(o["nodos"].split(",")) if o.get("nodos") else None
    out = {"a": str(wa), "b": str(wb), "nodos": {}}
    for n in receta["nodos"]:
        if solo and n["id"] not in solo:
            continue
        res = {}
        for rel in n["salidas"]:
            pa, pb = wa / rel, wb / rel
            if pa.is_file() and pb.is_file():
                res[rel] = comparar(pa, pb)
            else:
                res[rel] = {"presente_a": pa.is_file(), "presente_b": pb.is_file()}
        out["nodos"][n["id"]] = res
    resumen = {"artefactos": 0, "identicos": 0, "max_rel": 0.0, "max_abs_d2": 0.0}
    for res in out["nodos"].values():
        for v in res.values():
            if "sha_igual" not in v:
                continue
            resumen["artefactos"] += 1
            resumen["identicos"] += int(v["sha_igual"])
            for grupo in ("columnas", "miembros"):
                for c in (v.get(grupo) or {}).values():
                    resumen["max_rel"] = max(resumen["max_rel"], float(c.get("max_rel") or 0.0))
            if "valores" in v:
                resumen["max_rel"] = max(resumen["max_rel"], float(v["valores"].get("max_rel") or 0.0))
            if v.get("d2_dif") is not None:
                resumen["max_abs_d2"] = max(resumen["max_abs_d2"], abs(v["d2_dif"]))
    out["resumen"] = resumen
    texto = json.dumps(out, ensure_ascii=False, indent=1, default=float)
    if o.get("salida"):
        Path(o["salida"]).write_text(texto, encoding="utf-8")
    print(json.dumps(resumen, ensure_ascii=False))


if __name__ == "__main__":
    main()
