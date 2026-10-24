"""Comprueba que cada cifra del aporte CLA-S2-20261023-001 sale de la evidencia y aparece tal cual en el texto.

Lee cifras_aporte.json (misma carpeta) y las fuentes que declara: evidencia.json y desarrollo2023_diagnostico.json. Para cada entrada calcula el valor desde la evidencia, lo formatea como
se escribe en el aporte y exige dos cosas: que coincida con `valor` y que `contexto` aparezca literalmente en el
cuerpo del aporte. Las entradas con `igual` comprueban un valor exacto (por ejemplo, cero casos) y las de `entre`,
un intervalo cerrado.
Escribe verificacion_aporte.json con el resultado y las huellas de lo comprobado.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent


def get(ev, path):
    cur = ev
    for k in path:
        cur = cur[int(k)] if isinstance(cur, list) else cur[str(k)]
    return cur


def buscar(ev, spec):
    for item in get(ev, spec['lista']):
        if all(item.get(k) == v for k, v in spec['campos'].items()):
            return item[spec['clave']]
    raise KeyError(f"sin coincidencia para {spec['campos']}")


def num(x: float, d: int) -> str:
    return f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def fmt(v, f: str) -> str:
    if f == 'int':
        return num(round(v), 0)
    if f.startswith('dec'):
        return num(v, int(f[3:]))
    if f.startswith('sdec'):
        return ('+' if v > 0 else '−') + num(abs(v), int(f[4:]))
    if f.startswith('pct'):
        return num(v * 100, int(f[3:]))
    if f.startswith('dpct'):
        x = (v - 1) * 100
        return ('+' if x > 0 else '−') + num(abs(x), int(f[4:]))
    if f.startswith('adpct'):
        return num(abs(v - 1) * 100, int(f[5:]))
    if f.startswith('spct'):
        x = v * 100
        return ('+' if x > 0 else '−') + num(abs(x), int(f[4:]))
    if f == 'raw':
        return str(v)
    raise ValueError(f)


def valor(ev, c):
    if 'ruta' in c:
        return get(ev, c['ruta'])
    if 'buscar' in c:
        return buscar(ev, c['buscar'])
    if 'longitud' in c:
        return len(get(ev, c['longitud']))
    for k, f in (('suma', sum), ('min', min), ('max', max), ('todos', list)):
        if k in c:
            return f([get(ev, p) for p in c[k]])
    raise ValueError(c)


def main():
    spec = json.loads((HERE / 'cifras_aporte.json').read_text(encoding='utf-8'))
    fuentes = {k: json.loads((HERE / v).read_text(encoding='utf-8')) for k, v in spec['fuentes'].items()}
    body_path = HERE / spec['aporte']
    body = body_path.read_text(encoding='utf-8')
    res, fallos = [], 0
    for c in spec['cifras']:
        try:
            v = valor(fuentes[c.get('fuente', 'evidencia')], c)
            if 'igual' in c:
                ok_v = all(x == c['igual'] for x in v) if 'todos' in c else v == c['igual']
                shown = v
            elif 'menor' in c:
                ok_v = v < c['menor']
                shown = v
            elif 'entre' in c:
                ok_v = c['entre'][0] <= v <= c['entre'][1]
                shown = v
            else:
                shown = fmt(v, c['formato'])
                ok_v = shown == c['valor']
            ok_t = c['contexto'] in body and ('valor' not in c or c['valor'] in c['contexto'])
        except Exception as ex:  # noqa: BLE001 - se informa la entrada que falla
            ok_v, ok_t, shown = False, False, f'error: {ex}'
        ok = bool(ok_v and ok_t)
        fallos += not ok
        res.append(dict(id=c['id'], fuente=c.get('fuente', 'evidencia'), ok=ok, valor_calculado=shown,
                        valor_esperado=c.get('valor', c.get('igual', c.get('menor', c.get('entre')))),
                        contexto_en_texto=bool(ok_t)))
    out = dict(autor='Claude', utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
               fuentes_sha256={k: hashlib.sha256((HERE / v).read_bytes()).hexdigest() for k, v in spec['fuentes'].items()},
               aporte_sha256=hashlib.sha256(body_path.read_bytes()).hexdigest(),
               cifras_sha256=hashlib.sha256((HERE / 'cifras_aporte.json').read_bytes()).hexdigest(),
               comprobaciones=len(res), fallos=fallos, detalle=res)
    (HERE / 'verificacion_aporte.json').write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str),
                                                   encoding='utf-8')
    for r in res:
        if not r['ok']:
            print('FALLA', r)
    print(json.dumps({'comprobaciones': len(res), 'fallos': fallos}))
    sys.exit(1 if fallos else 0)


if __name__ == '__main__':
    main()
