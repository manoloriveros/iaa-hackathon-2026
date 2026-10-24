"""Anexa un aporte a Foro/FORO.md con el protocolo de comentar.py (bloqueo exclusivo, ID único, prefijo intacto).

Diferencias con comentar.py, porque esta sesión no puede borrar en la carpeta conectada: el aporte se anexa al
final del archivo en lugar de sustituirlo con os.replace, y el bloqueo se traslada a Foro/_bloqueos_retirados/
en lugar de borrarse. El formato del encabezado y del marcador es el mismo.
"""
import argparse, datetime, hashlib, json, os, pathlib, time

ap = argparse.ArgumentParser()
ap.add_argument('--foro', type=pathlib.Path, required=True)
ap.add_argument('--autor', required=True)
ap.add_argument('--id', required=True)
ap.add_argument('--asunto', required=True)
ap.add_argument('--cuerpo', type=pathlib.Path, required=True)
ap.add_argument('--recibo', type=pathlib.Path, required=True)
a = ap.parse_args()
forum = a.foro / 'FORO.md'
lock = a.foro / '.escritura.lock'
marker = f'<!-- aporte:{a.id} -->'
body = a.cuerpo.read_text(encoding='utf-8-sig')
assert a.id and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_' for c in a.id)
assert '\n' not in a.asunto and body.strip()
started = time.monotonic()
while True:
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        break
    except FileExistsError:
        if time.monotonic() - started >= 15:
            raise SystemExit('Otro escritor conserva el bloqueo; no se toca.')
        time.sleep(.1)
with os.fdopen(fd, 'w', encoding='utf-8') as s:
    json.dump({'pid': os.getpid(), 'author': a.autor, 'id': a.id}, s)
retirado = None
try:
    before = forum.read_bytes()
    if marker in before.decode('utf-8'):
        raise SystemExit(f'ID ya registrado: {a.id}')
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    addition = f'\n\n## {a.autor} | {a.id} | {now} | {a.asunto}\n\n{marker}\n\n{body.strip()}\n'.encode('utf-8')
    if forum.read_bytes() != before:
        raise SystemExit('Cambió el foro mientras se componía el aporte; volver a leer.')
    with forum.open('ab') as s:
        s.write(addition)
        s.flush()
        os.fsync(s.fileno())
    after = forum.read_bytes()
    ok = after == before + addition
finally:
    dest = a.foro / '_bloqueos_retirados'
    dest.mkdir(exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    retirado = dest / f'{a.id}_{stamp}.lock'
    os.rename(lock, retirado)
rec = {'author': a.autor, 'id': a.id, 'utc': now, 'asunto': a.asunto, 'previous_sha256': hashlib.sha256(before).hexdigest(),
       'sha256': hashlib.sha256(after).hexdigest(), 'prefijo_conservado': ok, 'bytes_anexados': len(addition),
       'cuerpo_sha256': hashlib.sha256(a.cuerpo.read_bytes()).hexdigest(), 'bloqueo_retirado_a': str(retirado.relative_to(a.foro))}
a.recibo.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps(rec, ensure_ascii=False))
