"""Huellas de archivos para comparar artefactos reconstruidos con los originales.

Dos huellas por archivo:
- `sha256`: SHA-256 de los bytes. Es la prueba fuerte y la que se exige al CSV de envío.
- `contenido`: SHA-256 de los valores, independiente del escritor. Parquet se lee con pyarrow columna a columna
  (diccionarios decodificados, cadenas largas como cadenas, marcas de tiempo en nanosegundos), .npy por su tipo,
  forma y bytes, .npz miembro a miembro (el zip guarda la hora de escritura, así que sus bytes nunca coinciden),
  CSV con finales de línea normalizados y JSON en forma canónica. Sirve cuando el archivo se reescribe con otra
  versión de pyarrow o pandas, o en otra máquina, y los valores son los mismos.

Uso: python huella.py <archivo> [...]
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np


def sha256_bytes(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _array_digest(h, arr: np.ndarray) -> None:
    arr = np.ascontiguousarray(arr)
    h.update(f"{arr.dtype.str}|{arr.shape}|".encode())
    if arr.dtype.kind == "O":
        h.update("\x1f".join("\x00" if v is None else str(v) for v in arr.ravel()).encode("utf-8"))
    else:
        h.update(arr.tobytes())


def _parquet_digest(path: Path) -> str:
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    t = pq.read_table(path)
    h = hashlib.sha256()
    h.update(f"filas={t.num_rows}|".encode())
    for name in t.column_names:
        if name.startswith("__index_level_"):
            continue
        col = t.column(name).combine_chunks()
        if pa.types.is_dictionary(col.type):
            col = col.dictionary_decode()
        typ = col.type
        es_vista = getattr(pa.types, "is_string_view", lambda _t: False)
        if pa.types.is_large_string(typ) or es_vista(typ):
            col = col.cast(pa.string()); typ = col.type
        if pa.types.is_timestamp(typ):
            col = pc.cast(col.cast(pa.timestamp("ns", tz=typ.tz)), pa.int64()); tag = "ts_ns"
        elif pa.types.is_date(typ):
            col = pc.cast(col.cast(pa.date32()), pa.int32()); tag = "date32"
        elif pa.types.is_string(typ):
            tag = "str"
        elif pa.types.is_boolean(typ):
            tag = "bool"
        elif pa.types.is_integer(typ):
            tag = "int"
        elif pa.types.is_floating(typ):
            tag = "float"
        else:
            tag = str(typ)
        h.update(f"{name}|{tag}|nulos={col.null_count}|".encode())
        if tag == "str":
            vals = col.to_pylist()
            h.update("\x1f".join("\x00" if v is None else v for v in vals).encode("utf-8"))
        elif tag == "bool":
            h.update(np.asarray(col.fill_null(False).to_numpy(zero_copy_only=False), dtype=np.uint8).tobytes())
            if col.null_count:
                h.update(np.asarray(col.is_null().to_numpy(zero_copy_only=False), dtype=np.uint8).tobytes())
        elif tag in ("int", "ts_ns", "date32"):
            v = col.fill_null(0).to_numpy(zero_copy_only=False).astype(np.int64)
            h.update(v.tobytes())
            if col.null_count:
                h.update(np.asarray(col.is_null().to_numpy(zero_copy_only=False), dtype=np.uint8).tobytes())
        elif tag == "float":
            v = col.to_numpy(zero_copy_only=False).astype(np.float64)
            h.update(v.tobytes())
        else:
            h.update(json.dumps(col.to_pylist(), default=str).encode("utf-8"))
    return h.hexdigest()


def huella_contenido(path: Path) -> str:
    path = Path(path)
    suf = path.suffix.lower()
    if suf == ".parquet":
        return _parquet_digest(path)
    h = hashlib.sha256()
    if suf == ".npy":
        _array_digest(h, np.load(path, allow_pickle=False))
    elif suf == ".npz":
        with np.load(path, allow_pickle=False) as z:
            for k in sorted(z.files):
                h.update(f"[{k}]".encode())
                _array_digest(h, z[k])
    elif suf == ".csv":
        h.update(path.read_bytes().replace(b"\r\n", b"\n"))
    elif suf == ".json":
        h.update(json.dumps(json.loads(path.read_text(encoding="utf-8-sig")), sort_keys=True, ensure_ascii=False).encode("utf-8"))
    else:
        h.update(path.read_bytes())
    return h.hexdigest()


def huellas(path: Path) -> dict:
    path = Path(path)
    return {"bytes": path.stat().st_size, "sha256": sha256_bytes(path), "contenido": huella_contenido(path)}


if __name__ == "__main__":
    for a in sys.argv[1:]:
        print(json.dumps({"archivo": a, **huellas(Path(a))}, ensure_ascii=False))
