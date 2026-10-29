"""Inventario local y carpeta de entrega; nunca entrena, borra ni mueve fuentes.

Las rutas históricas son dependencias de recetas y manifiestos. La carpeta
Entrega_final es una selección verificable, no un cambio de esos contratos.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import html
import json
import os
from pathlib import Path
import shutil
import stat
from datetime import datetime, timezone


REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
FINAL = ROOT / 'Hackaton/Entrega_final'
PRIVATE = REPO / 'privado/organizacion'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def rel(path):
    return path.relative_to(ROOT).as_posix()


def extended(path):
    value = str(path.resolve())
    return '\\\\?\\' + value if os.name == 'nt' and not value.startswith('\\\\?\\') else value


def inventory(run):
    """Sólo metadatos. No sigue enlaces ni abre datos/modelos/credenciales."""
    groups = collections.defaultdict(lambda: {'files': 0, 'bytes': 0})
    extensions = collections.Counter()
    errors, skipped = [], []
    destination = run / 'inventario_workspace.csv'
    # Entornos instalados, .git y cachés se cuentan como infraestructura aparte.
    infrastructure = {'.git', '.venv', '.venv-kaggle', 'node_modules', '__pycache__',
                      '.cache', '.ruff_cache', '.pytest_cache', '.agents', '.kaggle-skill'}
    stack = [(extended(ROOT), ())]
    with destination.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['ruta', 'bytes', 'mtime_ns', 'categoria'])
        while stack:
            current, parts = stack.pop()
            try:
                entries = os.scandir(current)
                with entries:
                    for entry in entries:
                        subparts = (*parts, entry.name)
                        relative = '/'.join(subparts)
                        try:
                            info = entry.stat(follow_symlinks=False)
                            if getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                                skipped.append({'ruta': relative, 'motivo': 'enlace_no_seguido'})
                            elif entry.is_dir(follow_symlinks=False):
                                if entry.name in infrastructure or relative.startswith(rel(PRIVATE)) or relative == rel(FINAL):
                                    skipped.append({'ruta': relative, 'motivo': 'infraestructura_o_salida_propia'})
                                else:
                                    stack.append((entry.path, subparts))
                            elif entry.is_file(follow_symlinks=False):
                                if '/Datos/' in relative or relative.startswith('Preparación/data/raw/'):
                                    category = 'originales_restringidos'
                                elif '/privado/' in relative:
                                    category = 'evidencia_restringida'
                                elif '/docs/' in relative:
                                    category = 'documentacion_soporte'
                                elif '/src/' in relative or '/herramientas/' in relative or '/notebooks/' in relative:
                                    category = 'codigo_y_reproduccion'
                                else:
                                    category = 'trabajo_y_archivo'
                                writer.writerow([relative, info.st_size, info.st_mtime_ns, category])
                                key = '/'.join(subparts[:2]) if len(subparts) > 2 else subparts[0]
                                groups[key]['files'] += 1
                                groups[key]['bytes'] += info.st_size
                                extensions[Path(entry.name).suffix.lower()] += 1
                        except OSError as exc:
                            errors.append({'ruta': relative, 'error': str(exc)})
            except OSError as exc:
                errors.append({'ruta': '/'.join(parts), 'error': str(exc)})
    summary = {'files': sum(v['files'] for v in groups.values()),
               'bytes': sum(v['bytes'] for v in groups.values()),
               'groups': dict(sorted(groups.items())), 'extensions': dict(extensions.most_common()),
               'errors': errors, 'skipped': skipped,
               'scope': 'Metadatos de archivos regulares; infraestructura instalada y enlaces enumerados aparte. No valida contenido actuarial.'}
    write_json(run / 'inventario_resumen.json', summary)
    return summary


def catalog(run):
    docs = REPO / 'docs'
    rows, hashes = [], collections.defaultdict(list)
    for path in sorted(docs.rglob('*.md')):
        local = path.relative_to(docs).as_posix()
        if local.startswith('archivo/'):
            group = 'Archivo de trabajo y evidencia'
        elif local == 'README.md':
            group = 'Entrada vigente'
        elif local.startswith('entrega/video/') and path.name in {'GUION_VIDEO_ES.md', 'NARRACION_GEMINI_TTS_ES.md'}:
            group = 'Preparación audiovisual vigente'
        elif local.startswith('semana2/') and path.name in {'PROTOCOLO_SELECCION.md', 'F3C_REVISION_FINAL_20261028.md', 'F3C_REGULARIZADO_CIERRE_20261028.md', 'README.md'}:
            group = 'Decisión final y límites'
        elif path.name in {'CONTROL_DE_VERSIONES.md', 'VERSION_CONTROL.md', 'MODELO_FINAL_S41.md', 'DECISION_FINAL_S41.md', 'REENTRENAMIENTO_ORIGINALES.md', 'REPRODUCCION_COMPLETA.md', 'REPRODUCCION_DOS_SEMANAS.md', 'REVISION_PENDIENTE_PARTICIPANTE.md'}:
            group = 'Referencia técnica'
        else:
            group = 'Archivo de trabajo y evidencia'
        title = path.stem
        with path.open(encoding='utf-8-sig', errors='replace') as f:
            for i, line in enumerate(f):
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
                if i >= 25:
                    break
        digest = sha(path)
        rows.append({'path': rel(path), 'group': group, 'title': title, 'bytes': path.stat().st_size, 'sha256': digest})
        hashes[digest].append(rel(path))
    write_json(run / 'catalogo_documental.json', rows)
    write_json(run / 'duplicados_markdown_exactos.json', [v for v in hashes.values() if len(v) > 1])
    body = []
    for row in rows:
        href = Path(os.path.relpath(ROOT / row['path'], docs)).as_posix()
        body.append('<tr><td>' + html.escape(row['group']) + '</td><td><a href="' + html.escape(href, quote=True) + '">' + html.escape(row['title']) + '</a></td><td><code>' + html.escape(href) + '</code></td></tr>')
    page = '''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Índice documental IAA 2026</title>
<style>body{font:16px/1.5 system-ui;max-width:1400px;margin:40px auto;padding:0 24px;color:#17212b;background:#f7f8fa}h1{font-size:30px}input{font:inherit;width:96%;padding:12px;margin:16px 0}table{border-collapse:collapse;width:100%;background:white}td,th{padding:10px;text-align:left;border-bottom:1px solid #ddd}td:first-child{width:220px}code{font-size:12px;overflow-wrap:anywhere}a{color:#14579c}p{max-width:1000px}</style>
<h1>Documentación del hackathon</h1><p>Mi carpeta local Hackaton/Entrega_final reúne la selección vigente y los archivos restringidos que mantengo fuera de Git. Las propuestas y revisiones anteriores están en <a href="archivo/README.md">docs/archivo</a>. El <a href="../registro/archivo_documental_actual.json">mapa de traslados</a> identifica las ubicaciones anteriores y las versiones originales.</p><p>Las categorías son una organización documental; no acreditan validación profesional o cierre de pendientes. Autoría y resultados adversos se conservan.</p><label for="buscar">Filtrar por nombre, ruta o categoría</label><input id="buscar" type="search" placeholder="Por ejemplo: decisión final, reproducción o reservas"><table><thead><tr><th>Uso</th><th>Documento</th><th>Ruta actual</th></tr></thead><tbody>''' + '\n'.join(body) + '''</tbody></table><script>document.getElementById('buscar').addEventListener('input',function(){const q=this.value.toLocaleLowerCase();document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLocaleLowerCase().includes(q))})</script></html>'''
    (docs / 'INDICE_DOCUMENTAL.html').write_text(page, encoding='utf-8')
    return rows


def choose_files():
    """Lista cerrada, escogida por índices de decisión, nunca por mtime/score."""
    s1 = read_json(REPO / 'registro/decision_final_S41_20261023.json')
    s2 = read_json(REPO / 'registro/semana2_decision_final_F3c_20261028.json')
    report = read_json(REPO / 'registro/informe_final_editorial_actual.json')
    en = read_json(REPO / 'registro/narracion_gemini_tts_en_actual.json')
    notebooks = read_json(REPO / 'registro/notebooks_kaggle_actual.json')['archivos']
    es_hash = report['primary_narration_sha256']
    script = read_json(REPO / 'registro/guion_video_actual.json')
    specs = [
        (ROOT / report['pdf'], '01_Para_entregar/Informe_final_ES.pdf', report['pdf_sha256'], 'informe_final_editorial_actual.json'),
        (ROOT / s1['csv_copia_local'], '01_Para_entregar/Predicciones_semana_1_S41.csv', s1['sha256_csv'], 'decision_final_S41_20261023.json'),
        (ROOT / s2['predictions']['path'], '01_Para_entregar/Predicciones_semana_2_F3c.csv', s2['predictions']['sha256'], 'semana2_decision_final_F3c_20261028.json'),
        (REPO / 'notebooks/week1_developed_market.ipynb', '02_Reproduccion/week1_developed_market.ipynb', notebooks['notebooks/week1_developed_market.ipynb'], 'notebooks_kaggle_actual.json'),
        (REPO / 'notebooks/week2_emerging_market.ipynb', '02_Reproduccion/week2_emerging_market.ipynb', notebooks['notebooks/week2_emerging_market.ipynb'], 'notebooks_kaggle_actual.json'),
        (REPO / 'notebooks/README.md', '02_Reproduccion/README.md', None, 'notebooks/README.md'),
        (REPO / 'requirements.txt', '02_Reproduccion/requirements.txt', None, 'requirements.txt'),
        (REPO / 'docs/entrega/video/NARRACION_GEMINI_TTS_ES.txt', '03_Textos_video/Narracion_ES.txt', es_hash, 'informe_final_editorial_actual.json'),
        (REPO / en['text'], '03_Textos_video/Narracion_EN.txt', en['text_sha256'], 'narracion_gemini_tts_en_actual.json'),
        (REPO / script['source'], '03_Textos_video/Guion_ES.md', script['current_source_actual_sha256'], 'guion_video_actual.json'),
    ]
    organization = REPO / 'registro/organizacion_actual.json'
    if organization.exists():
        video = read_json(organization).get('video', {})
        if video.get('elegido_por_participante') is True:
            specs.append((ROOT / video['fuente'], '04_Video/Video_final_EN.mp4', video['sha256'], 'organizacion_actual.json'))
    return specs


def prepare(run):
    if FINAL.exists():
        raise RuntimeError('Entrega_final ya existe. Verificar su manifiesto antes de sustituirla; no se sobrescribe.')
    staged = []
    for source, target, expected, index in choose_files():
        digest = sha(source)
        if expected and digest != expected:
            raise RuntimeError(f'La fuente no coincide con su índice: {source.name}')
        staged.append((source, target, digest, index))
    FINAL.mkdir()
    (FINAL / '.gitignore').write_text('*\n!.gitignore\n', encoding='utf-8')
    files = []
    for source, target, digest, index in staged:
        output = FINAL / target
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, output)
        assert sha(output) == digest
        files.append({'archivo': target, 'fuente': rel(source), 'sha256': digest,
                      'bytes': output.stat().st_size, 'indice_origen': index})
    manifest = {'schema_version': 1, 'utc': datetime.now(timezone.utc).isoformat(), 'autor': 'Codex',
                'base_fuentes': 'C:/dev/Hakaton', 'modelo_semana_1': 'S41', 'modelo_semana_2': 'F3c',
                'alcance': 'Selección local verificada por identidad; no es recibo de entrega ni validación actuarial nueva.',
                'archivos': files, 'video_final_confirmado': any(row['archivo'].endswith('.mp4') for row in files), 'informe_final_EN_confirmado': False,
                'originales_modificados': False, 'evidencia': rel(run)}
    write_json(FINAL / 'MANIFIESTO.json', manifest)
    write_json(run / 'seleccion_final.json', manifest)
    return manifest


def verify():
    manifest = read_json(FINAL / 'MANIFIESTO.json')
    results = []
    for row in manifest['archivos']:
        source, output = ROOT / row['fuente'], FINAL / row['archivo']
        result = {'archivo': row['archivo'], 'copia_integra': output.is_file() and sha(output) == row['sha256'],
                  'fuente_sin_cambios': source.is_file() and sha(source) == row['sha256']}
        results.append(result)
    expected = {target: (rel(source), digest) for source, target, digest, _ in choose_files()}
    registered = {row['archivo']: row for row in manifest['archivos']}
    indices_match = all(target in registered and registered[target]['fuente'] == source and
                        (digest is None or registered[target]['sha256'] == digest)
                        for target, (source, digest) in expected.items())
    allowed = set(registered) | {'README.md', 'MANIFIESTO.json', '.gitignore'}
    extra = sorted(p.relative_to(FINAL).as_posix() for p in FINAL.rglob('*')
                   if p.is_file() and p.relative_to(FINAL).as_posix() not in allowed)
    return {'utc': datetime.now(timezone.utc).isoformat(),
            'ok': all(r['copia_integra'] and r['fuente_sin_cambios'] for r in results) and indices_match and not extra,
            'indices_vigentes_coinciden': indices_match, 'archivos_no_declarados': extra, 'archivos': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accion', choices=['inventario', 'preparar', 'verificar'])
    args = parser.parse_args()
    if args.accion == 'verificar':
        result = verify()
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result['ok'] else 1
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run = PRIVATE / stamp
    run.mkdir(parents=True, exist_ok=False)
    if args.accion == 'inventario':
        summary = inventory(run)
        rows = catalog(run)
        print(json.dumps({'evidencia': rel(run), 'archivos': summary['files'], 'bytes': summary['bytes'],
                          'errores': len(summary['errors']), 'documentos': len(rows)}, ensure_ascii=False))
    else:
        manifest = prepare(run)
        result = verify()
        write_json(run / 'verificacion.json', result)
        print(json.dumps({'evidencia': rel(run), 'copias': len(manifest['archivos']), 'verificacion': result['ok']}, ensure_ascii=False))
        return 0 if result['ok'] else 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
