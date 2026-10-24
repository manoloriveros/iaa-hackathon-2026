"""Comprueba que cada cifra de INFORME.md y del aporte CLA-S2-20261023-004 sale de evidencia_validacion.json y aparece tal cual.

Lee cifras_informe.json (misma carpeta). Para cada entrada calcula el valor desde la evidencia (o la huella de un archivo
de la carpeta cuando la entrada trae `archivo`), lo formatea como se escribe en el texto y exige que coincida con `valor`
y que `contexto` aparezca literalmente en el documento indicado (`en`: informe o aporte). Las entradas con `igual`, `menor` o
`prefijo` comprueban un valor exacto, una cota o el inicio de una versión. Las entradas con `calculo` usan una de las funciones de CALCULOS, que
recalculan sumas, cuotas y recuentos a partir de la evidencia. Escribe verificacion_informe.json con el resultado.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
LINES = ['motor', 'buildings', 'contents']


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
    if f.startswith('ipct'):
        return num((v - 1) * 100, int(f[4:]))
    if f.startswith('apct'):
        return num(abs(v) * 100, int(f[4:]))
    if f.startswith('pct'):
        return num(v * 100, int(f[3:]))
    if f.startswith('sci'):
        s = f'{v:.{int(f[3:])}e}'
        mant, exp = s.split('e')
        return mant.replace('.', ',') + 'e' + str(int(exp))
    if f == 'sha':
        return f'{v[:8]}…{v[-4:]}'
    if f == 'fecha':  # 2024-12-30 -> 30-12-2024
        return '-'.join(reversed(str(v)[:10].split('-')))
    if f == 'anio':
        return str(int(v))
    if f == 'raw':
        return str(v)
    raise ValueError(f)


def _hallazgos(ev):
    return ev['resumen']['hallazgos']


CALCULOS = {
    'suma': lambda ev, *paths: sum(get(ev, p) for p in paths),
    'razon': lambda ev, a, b: get(ev, a) / get(ev, b),
    'producto_redondeado': lambda ev, a, b: round(get(ev, a) * get(ev, b)),
    'uno_menos_por': lambda ev, a, n: round((1 - get(ev, a)) * n),
    'severidad': lambda ev, s: sum(h['severidad'] == s for h in _hallazgos(ev)),
    'hallazgos': lambda ev: len(_hallazgos(ev)),
    'controles_por_resultado': lambda ev, r: ev['resumen']['por_resultado'][r],
    'maximo_abs': lambda ev, *paths: max(abs(get(ev, p)) for p in paths),
    'maximo': lambda ev, *paths: max(get(ev, p) for p in paths),
    'minimo': lambda ev, *paths: min(get(ev, p) for p in paths),
    'longitud': lambda ev, p: len(get(ev, p)),
    'declined_sucesores': lambda ev: sum(round(get(ev, ['detalle', 'VE46', l, 'declined_by_insurer', 'filas']) * get(ev, ['detalle', 'VE46', l, 'declined_by_insurer', 'con_periodo_posterior'])) for l in LINES),
    'listed_todos_3pct': lambda ev: all(round(v * 100) == 3 for v in get(ev, ['detalle', 'VE26', 'listed_por_tramo_de_construccion']).values()),
    'nulos_max_corr_abs': lambda ev: max(abs(v) for v in get(ev, ['detalle', 'VE72', 'direcciones_nulos_independientes']).values()),
    'psi_geo_max': lambda ev: max(get(ev, ['detalle', 'VE73', l, k]) for l in LINES for k in ['psi_region', 'psi_densidad', 'psi_zona_inundacion']),
    'cambios_exposicion_total': lambda ev: sum(get(ev, ['detalle', 'VE54', f'{l}_train', 'cambios_de_exposicion']) for l in LINES),
    'mitad_anio_total_cambia_capital_cont': lambda ev: get(ev, ['detalle', 'VE19', 'contents', 'atributos_que_cambian', 'sum_insured']),
    'entorno': lambda ev, k: str(ev['entorno'][k]),
}


def valor(ev, c):
    if 'archivo' in c:
        return hashlib.sha256((HERE / c['archivo']).read_bytes()).hexdigest()
    if 'calculo' in c:
        return CALCULOS[c['calculo']](ev, *c.get('args', []))
    if 'ruta' in c:
        return get(ev, c['ruta'])
    if 'buscar' in c:
        return buscar(ev, c['buscar'])
    for k, f in (('suma', sum), ('min', min), ('max', max), ('todos', list)):
        if k in c:
            return f([get(ev, p) for p in c[k]])
    raise ValueError(c)


def main():
    spec = json.loads((HERE / 'cifras_informe.json').read_text(encoding='utf-8'))
    ev = json.loads((HERE / spec['fuente']).read_text(encoding='utf-8'))
    docs = {k: (HERE / v).read_text(encoding='utf-8') for k, v in spec['documentos'].items()}
    res, fallos = [], 0
    for c in spec['cifras']:
        try:
            v = valor(ev, c)
            if 'igual' in c:
                ok_v = all(x == c['igual'] for x in v) if 'todos' in c else v == c['igual']
                shown = v
            elif 'prefijo' in c:
                ok_v = str(v).startswith(c['prefijo'])
                shown = v
            elif 'menor' in c:
                ok_v = v < c['menor']
                shown = v
            else:
                shown = fmt(v, c['formato'])
                ok_v = shown == c['valor']
            ok_t = c['contexto'] in docs[c.get('en', 'informe')] and ('valor' not in c or c['valor'] in c['contexto'])
        except Exception as ex:  # noqa: BLE001 - se informa la entrada que falla
            ok_v, ok_t, shown = False, False, f'error: {ex}'
        ok = bool(ok_v and ok_t)
        fallos += not ok
        res.append(dict(id=c['id'], en=c.get('en', 'informe'), ok=ok, valor_calculado=shown,
                        valor_esperado=c.get('valor', c.get('igual', c.get('menor', c.get('prefijo')))), contexto_en_texto=bool(ok_t)))
    out = dict(autor='Claude', utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
               fuente_sha256=hashlib.sha256((HERE / spec['fuente']).read_bytes()).hexdigest(),
               documentos_sha256={k: hashlib.sha256((HERE / v).read_bytes()).hexdigest() for k, v in spec['documentos'].items()},
               cifras_sha256=hashlib.sha256((HERE / 'cifras_informe.json').read_bytes()).hexdigest(),
               comprobaciones=len(res), fallos=fallos, por_documento={k: sum(r['en'] == k for r in res) for k in docs},
               detalle=res)
    (HERE / 'verificacion_informe.json').write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    for r in res:
        if not r['ok']:
            print('FALLA', r)
    print(json.dumps({'comprobaciones': len(res), 'fallos': fallos, 'por_documento': out['por_documento']}))
    sys.exit(1 if fallos else 0)


if __name__ == '__main__':
    main()
