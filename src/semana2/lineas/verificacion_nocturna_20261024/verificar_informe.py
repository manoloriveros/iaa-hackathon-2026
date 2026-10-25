"""Comprueba que cada cifra de INFORME.md y de los aportes CLA-S2-20261024-007, 008, 011 y 021 sale de evidencia_nocturna.json y aparece tal cual.

Lee cifras_informe.json (misma carpeta). Para cada entrada calcula el valor desde la evidencia (o la huella de un archivo
de la carpeta cuando la entrada trae `archivo`), lo formatea como se escribe en el texto y exige que coincida con `valor`
y que `contexto` aparezca literalmente en el documento indicado (`en`: informe o aporte). Las entradas con `igual`, `menor` o
`prefijo` comprueban un valor exacto, una cota o el inicio de una versión. Los aportes ya publicados conservan sus cifras de entonces (por ejemplo, 21 controles en 008): se comprueban con los recuentos hasta el control que existía al publicarlos. Las entradas con `calculo` usan una de las funciones de CALCULOS, que
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
    if f.startswith('M'):  # millones
        return num(v / 1e6, int(f[1:]))
    if f == 'absint':
        return num(abs(round(v)), 0)
    if f.startswith('sdec'):
        return ('+' if v > 0 else '−') + num(abs(v), int(f[4:]))
    if f == 'raw':
        return str(v)
    raise ValueError(f)


def _hallazgos(ev):
    return ev['resumen']['hallazgos']


CALCULOS = {
    'suma': lambda ev, *paths: sum(get(ev, p) for p in paths),
    'razon': lambda ev, a, b: get(ev, a) / get(ev, b),
    'razon_menos_uno': lambda ev, a, b: get(ev, a) / get(ev, b) - 1,
    'resta': lambda ev, a, b: get(ev, a) - get(ev, b),
    'maximo': lambda ev, *paths: max(get(ev, p) for p in paths),
    'minimo': lambda ev, *paths: min(get(ev, p) for p in paths),
    'maximo_lista': lambda ev, p: max(get(ev, p)),
    'minimo_lista': lambda ev, p: min(get(ev, p)),
    'longitud': lambda ev, p: len(get(ev, p)),
    'controles_por_resultado': lambda ev, r: ev['resumen']['por_resultado'].get(r, 0),
    'hallazgos': lambda ev: len(ev['resumen']['hallazgos']),
    'max_dif_informe_pares': lambda ev: max(v['coincide_informe'][k] for run in ['dev5', 'dev6', 'dev7'] for v in ev['detalle']['VN10'][run]['pares'].values() for k in ['delta_dif', 'inferior_dif', 'superior_dif', 'retirar_dif']),
    'max_dif_replay': lambda ev: max(ev['detalle']['VN13'][l][v]['max_dif_rel'] for l in LINES for v in ['W2-B13', 'W2-B14']),
    'max_dif_D2_informe': lambda ev: max(ev['detalle']['VN04'][run][m]['frente_al_informe']['D2_dif'] for run in ['dev5', 'dev6', 'dev7'] for m in ev['detalle']['VN04'][run] if ev['detalle']['VN04'][run][m].get('frente_al_informe')),
    'intervalos_cruzan_cero': lambda ev: sum(v['recalculado']['inferior95'] < 0 < v['recalculado']['superior95'] for run in ['dev5', 'dev6', 'dev7'] for v in ev['detalle']['VN10'][run]['pares'].values()),
    'pares_total': lambda ev: sum(len(ev['detalle']['VN10'][run]['pares']) for run in ['dev5', 'dev6', 'dev7']),
    'entorno': lambda ev, k: str(ev['entorno'][k]),
    'pares_mezcla_cruzan_cero': lambda ev: sum(v['recalculado']['inferior95'] < 0 < v['recalculado']['superior95'] for v in ev['detalle']['VN18']['pares'].values()),
    'pares_mezcla_total': lambda ev: len(ev['detalle']['VN18']['pares']),
    'max_dif_rangos': lambda ev, a, b: max(abs(x[i] - y[i]) for k, x in get(ev, a).items() for i in (0, 1) for y in [get(ev, b)[k]]),
    'min_valor': lambda ev, p: min(get(ev, p).values()),
    'max_valor': lambda ev, p: max(get(ev, p).values()),
    'min_sub': lambda ev, p, k: min(v[k] for v in get(ev, p).values()),
    'max_sub': lambda ev, p, k: max(v[k] for v in get(ev, p).values()),
    'min_sub_filtro': lambda ev, p, k, suf: min(v[k] for kk, v in get(ev, p).items() if kk.endswith(suf)),
    'max_sub_filtro': lambda ev, p, k, suf: max(v[k] for kk, v in get(ev, p).items() if kk.endswith(suf)),
    'controles_hasta': lambda ev, ultimo: sum(1 for c in ev['controles'] if c['id'] <= ultimo),
    'controles_hasta_por_resultado': lambda ev, ultimo, r: sum(1 for c in ev['controles'] if c['id'] <= ultimo and c['resultado'] == r),
    'cifras_ampliacion_b19': lambda ev: sum(ev['detalle'][k][key] for k, key in [('VN23', 'comparaciones'), ('VN24', 'comparaciones_publicadas'), ('VN25', 'comparaciones_publicadas'), ('VN26', 'comparaciones_publicadas'), ('VN27', 'comparaciones_publicadas')]),
    'fallos_ampliacion_b19': lambda ev: sum(ev['detalle'][k][key] for k, key in [('VN23', 'fallos_frente_al_foro'), ('VN24', 'fallos_publicados'), ('VN25', 'fallos_publicados'), ('VN26', 'fallos_publicados'), ('VN27', 'fallos_publicados')]),
    'cifras_ampliacion_b20': lambda ev: sum(ev['detalle'][k]['comparaciones_publicadas'] for k in ['VN31', 'VN32', 'VN33', 'VN34', 'VN35']),
    'fallos_ampliacion_b20': lambda ev: sum(ev['detalle'][k]['fallos_publicados'] for k in ['VN31', 'VN32', 'VN33', 'VN34', 'VN35']),
    'archivos_sintesis': lambda ev: ev['detalle']['VN30']['sintesis']['entradas_manifiesto'] + ev['detalle']['VN30']['sintesis']['salidas_manifiesto'],
    'archivos_sintesis_no_copiados': lambda ev: ev['detalle']['VN30']['sintesis']['entradas_manifiesto'] + ev['detalle']['VN30']['sintesis']['salidas_manifiesto'] - ev['detalle']['VN30']['sintesis']['iguales'],
    'coeficientes_b19_comparados': lambda ev: sum(ev['detalle']['VN25']['ramos'][l]['B19']['coeficientes_comparados_con_codex'] for l in LINES),
    'max_dif_coeficientes_b19': lambda ev: max(ev['detalle']['VN25']['ramos'][l]['B19']['max_dif_coeficientes'] for l in LINES),
    'max_dif_ajuste_b19_b20': lambda ev: max(ev['detalle']['VN25']['ramos'][l]['max_dif_D2_ajuste_frente_a_train_validation'] for l in LINES),
    'min_lista_sub': lambda ev, p, k: min(get(ev, p)[k]),
    'max_lista_sub': lambda ev, p, k: max(get(ev, p)[k]),
    'suma_sub_lista': lambda ev, p, k: sum(x[k] for x in get(ev, p)),
    'cuenta_menores_que_uno': lambda ev, p: sum(x < 1 for x in get(ev, p)),
    'cuenta_mayores_que_uno': lambda ev, p: sum(x > 1 for x in get(ev, p)),
    'posicion_en_orden': lambda ev, p, m: [x[0] for x in get(ev, p)].index(m) + 1,
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
