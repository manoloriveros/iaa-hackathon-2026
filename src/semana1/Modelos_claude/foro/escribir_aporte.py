"""Añade un aporte de Claude a foros/FORO.md con el mismo formato que foros/comentar.py, sin archivo de bloqueo.

La máquina virtual desde la que escribe Claude no puede borrar archivos en la carpeta conectada, así que comentar.py
dejaría su .escritura.lock sin retirar y bloquearía a Codex. Este script no crea bloqueo: espera si hay un bloqueo de
otro escritor, comprueba que el ID no existe, compone el aporte, vuelve a leer el foro justo antes de escribir y aborta si
cambió, y escribe con un archivo temporal que os.replace consume (no deja restos).
Uso: python3 escribir_aporte.py <ruta FORO.md> <ID> <asunto> <cuerpo.md>
"""
import datetime
import hashlib
import json
import os
import sys
import time
from pathlib import Path

forum, ident, subject, body_path = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4])
lock = forum.parent / ".escritura.lock"
body = body_path.read_text(encoding="utf-8-sig")
marker = f"<!-- aporte:{ident} -->"
assert all(c.isascii() and (c.isalnum() or c in "-_") for c in ident) and "\n" not in subject and body.strip()
t0 = time.monotonic()
while lock.exists():
    if time.monotonic() - t0 > 60:
        raise SystemExit("Otro escritor conserva el bloqueo; no se escribe.")
    time.sleep(0.5)
before = forum.read_bytes()
if marker in before.decode("utf-8"):
    raise SystemExit(f"ID ya registrado: {ident}")
now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
addition = f"\n\n## Claude | {ident} | {now} | {subject}\n\n{marker}\n\n{body.strip()}\n"
after = before + addition.encode("utf-8")
if lock.exists() or forum.read_bytes() != before:
    raise SystemExit("El foro cambió o apareció un bloqueo mientras se componía el aporte; volver a leer.")
stage = forum.parent / f".aporte-{ident}.tmp"
with stage.open("xb") as f:
    f.write(after)
    f.flush()
    os.fsync(f.fileno())
os.replace(stage, forum)
print(json.dumps({"author": "Claude", "id": ident, "utc": now, "previous_sha256": hashlib.sha256(before).hexdigest(),
                  "sha256": hashlib.sha256(after).hexdigest()}))
