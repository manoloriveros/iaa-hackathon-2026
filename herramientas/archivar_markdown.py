"""Traslado reversible de documentación y resolución de referencias históricas.

Planifica por adelantado los movimientos y las ediciones de enlaces. Guarda
los bytes originales antes de tocar un documento; no modifica corridas,
recetas, notebooks ni manifiestos históricos. No importa código del modelo.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from urllib.parse import quote, unquote, urlsplit, urlunsplit


REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
DOCS = REPO / 'docs'
ARCHIVE = DOCS / 'archivo'
MAP = REPO / 'registro/archivo_documental_actual.json'
KEEP_ROOT = {
    'README.md', 'CONTROL_DE_VERSIONES.md', 'VERSION_CONTROL.md',
    'DECISION_FINAL_S41.md', 'MODELO_FINAL_S41.md',
    'REENTRENAMIENTO_ORIGINALES.md', 'REPRODUCCION_COMPLETA.md',
    'REPRODUCCION_DOS_SEMANAS.md', 'REVISION_PENDIENTE_PARTICIPANTE.md',
}
KEEP_WEEK2 = {
    'PROTOCOLO_SELECCION.md', 'F3C_REVISION_FINAL_20261028.md',
    'F3C_REGULARIZADO_CIERRE_20261028.md', 'F3C_VALIDACION_COMPLETA_20261027.md',
    'F3C_A1_MEZCLA_PROTEGIDAS_Y_ESCENARIOS.md', 'F3C_CADENA_PROTEGIDA_REEVALUACION.md',
}
LINK = re.compile(r'(?P<prefix>\]\()(?P<target><[^>]*>|[^\s)]+)')
HTML_LINK = re.compile(r'(?P<prefix>\b(?:href|src)\s*=\s*["\x27])(?P<target>[^"\x27]+)', re.I)
REFERENCE = re.compile(r'(?m)^(?P<prefix>\s*\[[^\]\n]+\]:\s*)(?P<target><[^>]*>|[^\s]+)')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def checked(path):
    absolute = path.resolve()
    if not absolute.is_relative_to(ROOT.resolve()):
        raise ValueError('Ruta fuera del espacio de trabajo: ' + str(path))
    return absolute


def moves():
    rows = []
    for folder, keep, group in [(DOCS, KEEP_ROOT, 'semana1'), (DOCS / 'semana2', KEEP_WEEK2, 'semana2')]:
        for path in sorted(folder.glob('*.md')):
            if path.name not in keep:
                destination = checked(ARCHIVE / group / path.name)
                assert not destination.exists(), 'El destino ya existe'
                checked(path)
                rows.append({'old': relative(path), 'new': relative(destination), 'before_sha256': digest(path)})
    return rows


def replacement_table(rows):
    table = {}
    for row in rows:
        old = (ROOT / row['old']).relative_to(REPO).as_posix()
        new = (ROOT / row['new']).relative_to(REPO).as_posix()
        table[old] = new
        table[old.replace('/', '\\')] = new.replace('/', '\\')
        table[old.replace('/', '\\\\')] = new.replace('/', '\\\\')
    return table


def replace_paths(text, table):
    pattern = re.compile('|'.join(re.escape(k) for k in sorted(table, key=len, reverse=True)))
    return pattern.sub(lambda match: table[match.group()], text)


def rebase_target(value, source, destination, mapping):
    angle = value.startswith('<') and value.endswith('>')
    raw = value[1:-1] if angle else value
    url = urlsplit(raw)
    if url.scheme or url.netloc or not url.path or raw.startswith('#'):
        return value
    target = (source.parent / unquote(url.path)).resolve()
    # Algunas fuentes copiadas conservan una ruta explícita desde la raíz.
    if not target.exists():
        decoded = unquote(url.path)
        alternatives = []
        if decoded.startswith('docs/'):
            alternatives.append(REPO / decoded)
        if 'Hackaton/' in decoded:
            alternatives.append(ROOT / decoded[decoded.index('Hackaton/'):])
        alternatives = [p.resolve() for p in alternatives if p.exists()]
        if len(set(alternatives)) == 1:
            target = alternatives[0]
    new_target = mapping.get(str(target).casefold(), target)
    if source == destination and target == new_target:
        return value
    path = Path(os.path.relpath(new_target, destination.parent)).as_posix()
    path = quote(path, safe='/@:+-._~')
    result = urlunsplit(('', '', path, url.query, url.fragment))
    return '<' + result + '>' if angle else result


def rewrite_links(text, source, destination, mapping):
    def change(match):
        return match['prefix'] + rebase_target(match['target'], source, destination, mapping)
    for pattern in [LINK, HTML_LINK, REFERENCE]:
        text = pattern.sub(change, text)
    return text


def candidates():
    paths = {ROOT / 'README.md', ROOT / 'Hackaton/README.md', ROOT / 'Hackaton/Entrega_final/README.md', ROOT / 'RUTAS_PROYECTO.json',
             REPO / 'README.md', REPO / 'README.es.md', REPO / 'AGENTS.md', REPO / 'notebooks/README.md'}
    for p in DOCS.rglob('*'):
        local = p.relative_to(DOCS).parts
        if p.is_file() and p.suffix in {'.md', '.html'} and not set(local).intersection({'archivo', 'fuentes', 'evidencia'}):
            paths.add(p)
    for p in (REPO / 'herramientas').iterdir():
        if p.is_file() and p.suffix in {'.py', '.cjs', '.js', '.ps1', '.sh'} and p.name != Path(__file__).name:
            paths.add(p)
    for p in (REPO / 'registro').glob('*_actual.json'):
        if p.name not in {'organizacion_actual.json', MAP.name}:
            paths.add(p)
    return sorted(p for p in paths if p.exists())


def skeleton(tree):
    """Verifica que los cambios Python se limitan a constantes de texto."""
    class Mask(ast.NodeTransformer):
        def visit_Constant(self, node):
            if isinstance(node.value, str):
                node.value = '<texto>'
            return node
    return ast.dump(Mask().visit(tree), include_attributes=False)


def plan():
    assert not MAP.exists(), 'Ya existe un archivo documental; no se repite el traslado'
    rows = moves()
    run = REPO / 'privado/organizacion' / ('archivo_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    run.mkdir(parents=True, exist_ok=False)
    mapping = {str((ROOT / row['old']).resolve()).casefold(): ROOT / row['new'] for row in rows}
    table = replacement_table(rows)
    edits = []
    for source in candidates():
        raw = source.read_bytes()
        text = raw.decode('utf-8')
        destination = mapping.get(str(source.resolve()).casefold(), source)
        if source.suffix in {'.md', '.html'}:
            text = rewrite_links(text, source, destination, mapping)
        # Los expedientes exportados conservan la narración y sus rutas citadas;
        # se ajustan únicamente los hipervínculos que se siguen al leerlos.
        if not source.is_relative_to(DOCS / 'expediente'):
            text = replace_paths(text, table)
        if source.suffix == '.py':
            constants = {node.value for node in ast.walk(ast.parse(raw))
                         if isinstance(node, ast.Constant) and isinstance(node.value, str)}
            moved_names = {Path(row['old']).name for row in rows}
            # Cinco productores forman la ruta con un directorio y un nombre
            # separados. Cambiar también esa base evita omitir esas lecturas.
            if constants.intersection(moved_names) and 'docs/semana2' in constants:
                text = re.sub(r'(["\x27])docs/semana2\1', lambda m: m[1] + 'docs/archivo/semana2' + m[1], text)
        updated = text.encode('utf-8')
        if updated == raw and source == destination:
            continue
        if source.suffix == '.py':
            assert skeleton(ast.parse(raw)) == skeleton(ast.parse(updated)), relative(source)
        before = checked(run / 'antes' / source.relative_to(ROOT))
        after = checked(run / 'despues' / destination.relative_to(ROOT))
        before.parent.mkdir(parents=True, exist_ok=True)
        after.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, before)
        after.write_bytes(updated)
        edits.append({'source': relative(source), 'destination': relative(destination),
                      'before_sha256': hashlib.sha256(raw).hexdigest(), 'after_sha256': hashlib.sha256(updated).hexdigest(),
                      'original': relative(before), 'staged': relative(after)})
    by_source = {row['source']: row for row in edits}
    for row in rows:
        edit = by_source[row['old']]
        row.update(after_sha256=edit['after_sha256'], original=edit['original'])
    value = {'schema_version': 1, 'utc': datetime.now(timezone.utc).isoformat(), 'autor': 'Codex',
             'base': 'workspace_root', 'status': 'planificado', 'run': relative(run), 'moves': rows, 'edits': edits,
             'preserved': {'root': sorted(KEEP_ROOT), 'week2': sorted(KEEP_WEEK2)},
             'immutable_scope': 'Corridas, src, receta, notebooks y registros históricos no se reescriben. Las citas antiguas se resuelven con este mapa.'}
    save(run / 'plan.json', value)
    print(json.dumps({'plan': relative(run / 'plan.json'), 'movimientos': len(rows), 'archivos_con_referencias_o_ubicacion_actualizados': len(edits)}, ensure_ascii=False))


def apply(plan_path):
    value = load(plan_path)
    assert value['status'] == 'planificado' and not MAP.exists()
    # Preflight completo antes del primer traslado.
    for row in value['edits']:
        source, staged = checked(ROOT / row['source']), checked(ROOT / row['staged'])
        assert digest(source) == row['before_sha256'], 'Cambio concurrente: ' + row['source']
        assert digest(staged) == row['after_sha256']
        assert digest(ROOT / row['original']) == row['before_sha256']
        if row['source'] != row['destination']:
            assert not checked(ROOT / row['destination']).exists()
    run = ROOT / value['run']
    with (run / 'operaciones.jsonl').open('a', encoding='utf-8') as journal:
        for row in value['edits']:
            source, destination = checked(ROOT / row['source']), checked(ROOT / row['destination'])
            assert digest(source) == row['before_sha256'], 'Cambio concurrente: ' + row['source']
            if source != destination:
                destination.parent.mkdir(parents=True, exist_ok=True)
                source.rename(destination)
            destination.write_bytes((ROOT / row['staged']).read_bytes())
            assert digest(destination) == row['after_sha256']
            journal.write(json.dumps({'source': row['source'], 'destination': row['destination'], 'ok': True}) + '\n')
            journal.flush()
    value['status'] = 'trasladado'
    value['completed_utc'] = datetime.now(timezone.utc).isoformat()
    save(MAP, value)
    result = verify()
    save(run / 'verificacion_traslados.json', result)
    print(json.dumps({'movidos': len(value['moves']), 'ok': result['ok'], 'mapa': relative(MAP)}, ensure_ascii=False))


@lru_cache(maxsize=2)
def reference_lookup(map_mtime_ns):
    del map_mtime_ns  # La fecha invalida la caché al cambiar el mapa.
    result = {}
    for row in load(MAP)['edits']:
        for key in ['source', 'destination']:
            absolute = os.path.normcase(os.path.abspath(ROOT / row[key]))
            result[absolute] = row
    return result


def resolve(path, expected_sha256=None):
    """Ruta antigua -> documento actual; con hash antiguo -> original exacto."""
    supplied = Path(path)
    if not supplied.is_absolute():
        supplied = (REPO if str(path).replace('\\', '/').startswith('docs/') else ROOT) / supplied
    absolute = os.path.normcase(os.path.abspath(supplied))
    # Una revisión editorial posterior conserva sus propias versiones, sin
    # modificar el mapa ni los recibos del traslado del 29 de octubre.
    editorial = REPO / 'registro/revision_entrega_actual.json'
    if expected_sha256 and editorial.exists():
        for row in load(editorial).get('editorial_files', []):
            if absolute == os.path.normcase(os.path.abspath(ROOT / row['path'])):
                if expected_sha256 == row['before_sha256']:
                    original = ROOT / row['original']
                    if digest(original) != expected_sha256:
                        raise ValueError('La versión editorial original no coincide')
                    return original
    if MAP.exists():
        row = reference_lookup(MAP.stat().st_mtime_ns).get(absolute)
        if row:
            if expected_sha256 == row['before_sha256']:
                target = ROOT / row['original']
            elif expected_sha256 == row['after_sha256']:
                target = ROOT / row['staged']
            else:
                target = ROOT / row['destination']
            if expected_sha256 and digest(target) != expected_sha256:
                raise ValueError('La huella no coincide con la referencia solicitada')
            return target
    if not supplied.exists():
        raise FileNotFoundError(path)
    if expected_sha256 and digest(supplied) != expected_sha256:
        raise ValueError('La huella no coincide')
    return supplied


def verify():
    value = load(MAP)
    rows = []
    for row in value['moves']:
        old, new, original = ROOT / row['old'], ROOT / row['new'], ROOT / row['original']
        rows.append({'old': row['old'], 'new': row['new'], 'original_integro': original.is_file() and digest(original) == row['before_sha256'],
                     'archivo_integro': new.is_file() and digest(new) == row['after_sha256'], 'retirado_de_origen': not old.exists(),
                     'resolucion_historica': resolve(row['old'], row['before_sha256']).is_file()})
    return {'utc': datetime.now(timezone.utc).isoformat(), 'ok': all(all(v for k, v in row.items() if isinstance(v, bool)) for row in rows), 'moves': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('plan')
    command = sub.add_parser('aplicar')
    command.add_argument('plan')
    sub.add_parser('verificar')
    command = sub.add_parser('resolver')
    command.add_argument('ruta')
    command.add_argument('--sha256')
    args = parser.parse_args()
    if args.action == 'plan':
        plan()
    elif args.action == 'aplicar':
        apply(checked(ROOT / args.plan))
    elif args.action == 'verificar':
        result = verify()
        print(json.dumps({'ok': result['ok'], 'movimientos': len(result['moves'])}))
        return 0 if result['ok'] else 1
    else:
        print(resolve(args.ruta, args.sha256))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
