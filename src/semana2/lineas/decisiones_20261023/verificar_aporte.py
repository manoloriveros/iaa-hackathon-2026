"""Comprueba que cada cifra del aporte CLA-S2-20261023-003 y del README sale de evidencia_decisiones.json y aparece tal cual.

Lee cifras_aporte.json (misma carpeta). Para cada entrada calcula el valor desde la evidencia, lo formatea como se
escribe en el texto y exige que coincida con `valor` y que `contexto` aparezca literalmente en el documento indicado
(`en`: aporte o readme). Las entradas con `igual` o `menor` comprueban un valor exacto o una cota. Las entradas con
`calculo` usan una de las funciones de CALCULOS, que recalculan resúmenes del diagnóstico y del gasto fijo.
Escribe verificacion_aporte.json con el resultado y las huellas de lo comprobado.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TRES = ['C00314425', 'B00250679', 'M00129413']


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
    if f.startswith('spct'):
        x = v * 100
        return ('+' if x > 0 else '−') + num(abs(x), int(f[4:]))
    if f.startswith('dpct'):
        x = (v - 1) * 100
        return ('+' if x > 0 else '−') + num(abs(x), int(f[4:]))
    if f.startswith('apct'):
        return num(abs(v) * 100, int(f[4:]))
    if f.startswith('pct'):
        return num(v * 100, int(f[3:]))
    if f == 'sha':
        return f'{v[:8]}…{v[-4:]}'
    if f == 'hora':
        return v[11:16]
    if f == 'raw':
        return str(v)
    raise ValueError(f)


def _diag(ev):
    return ev['diagnostico_oof']['recetas']


def _mejor(o, clave):
    vs = ['guardada', 'emergente', 'credibilidad', 'desarrollado']
    return max(vs, key=lambda v: o[v][clave])


CALCULOS = {
    'recetas': lambda ev: len(_diag(ev)),
    'creible_mejor_todas': lambda ev: sum(_mejor(o, 'D2_mezcla_2025') == 'credibilidad' for o in _diag(ev).values()),
    'mejor_todas_guardada_o_emergente': lambda ev: sum(_mejor(o, 'D2_mezcla_2025') in ('guardada', 'emergente')
                                                       for o in _diag(ev).values()),
    'creible_supera_emergente_cuerpo': lambda ev: sum(o['credibilidad']['D2_mezcla_2025_sin_01'] > o['emergente']['D2_mezcla_2025_sin_01']
                                                      for o in _diag(ev).values()),
    'guardada_mejor_cuerpo': lambda ev: sum(_mejor(o, 'D2_mezcla_2025_sin_01') == 'guardada' for o in _diag(ev).values()),
    'gasto_referencias_resto': lambda ev: sum(r['row_id'] not in TRES for r in ev['gasto_fijo']['referencias']),
    'gasto_max_diferencia_resto': lambda ev: max(r['F_entero_por_fila_termino_F'] - r['F_por_exposicion_termino_F']
                                                 for r in ev['gasto_fijo']['referencias'] if r['row_id'] not in TRES),
    'subida_poliza_anio_M00129413': lambda ev: _sube(ev, 'M00129413'),
    'subida_poliza_anio_B00250679': lambda ev: _sube(ev, 'B00250679'),
    'confirmadas_total': lambda ev: ev['capital']['buildings']['confirmadas_por_historia'] + ev['capital']['contents']['confirmadas_por_historia'],
}


def _sube(ev, rid):
    r = [x for x in ev['gasto_fijo']['referencias'] if x['row_id'] == rid][0]
    return r['F_por_poliza_y_anio_P'] - r['F_por_exposicion_P']


def valor(ev, c):
    if 'calculo' in c:
        return CALCULOS[c['calculo']](ev)
    if 'ruta' in c:
        return get(ev, c['ruta'])
    if 'buscar' in c:
        return buscar(ev, c['buscar'])
    if 'inverso' in c:
        return 1 / get(ev, c['inverso'])
    for k, f in (('suma', sum), ('min', min), ('max', max), ('todos', list)):
        if k in c:
            return f([get(ev, p) for p in c[k]])
    raise ValueError(c)


def main():
    spec = json.loads((HERE / 'cifras_aporte.json').read_text(encoding='utf-8'))
    ev = json.loads((HERE / spec['fuente']).read_text(encoding='utf-8'))
    docs = {k: (HERE / v).read_text(encoding='utf-8') for k, v in spec['documentos'].items()}
    res, fallos = [], 0
    for c in spec['cifras']:
        try:
            v = valor(ev, c)
            if 'igual' in c:
                ok_v = all(x == c['igual'] for x in v) if 'todos' in c else v == c['igual']
                shown = v
            elif 'menor' in c:
                ok_v = v < c['menor']
                shown = v
            else:
                shown = fmt(v, c['formato'])
                ok_v = shown == c['valor']
            ok_t = c['contexto'] in docs[c.get('en', 'aporte')] and ('valor' not in c or c['valor'] in c['contexto'])
        except Exception as ex:  # noqa: BLE001 - se informa la entrada que falla
            ok_v, ok_t, shown = False, False, f'error: {ex}'
        ok = bool(ok_v and ok_t)
        fallos += not ok
        res.append(dict(id=c['id'], en=c.get('en', 'aporte'), ok=ok, valor_calculado=shown,
                        valor_esperado=c.get('valor', c.get('igual', c.get('menor'))), contexto_en_texto=bool(ok_t)))
    out = dict(autor='Claude', utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
               fuente_sha256=hashlib.sha256((HERE / spec['fuente']).read_bytes()).hexdigest(),
               documentos_sha256={k: hashlib.sha256((HERE / v).read_bytes()).hexdigest() for k, v in spec['documentos'].items()},
               cifras_sha256=hashlib.sha256((HERE / 'cifras_aporte.json').read_bytes()).hexdigest(),
               comprobaciones=len(res), fallos=fallos, por_documento={k: sum(r['en'] == k for r in res) for k in docs},
               detalle=res)
    (HERE / 'verificacion_aporte.json').write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    for r in res:
        if not r['ok']:
            print('FALLA', r)
    print(json.dumps({'comprobaciones': len(res), 'fallos': fallos, 'por_documento': out['por_documento']}))
    sys.exit(1 if fallos else 0)


if __name__ == '__main__':
    main()
