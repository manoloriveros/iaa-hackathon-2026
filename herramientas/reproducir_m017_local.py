"""Reconstrucción local de F3c/F3d, con etiquetas originales y OOF guardadas.

No reentrena los árboles fuente. Conserva los originales de Claude y adapta
únicamente dos rutas de lib26 en una carpeta privada nueva. No consulta scores.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
SRC = REPO / 'src/semana2/lineas/mision017_20261025'
PRIVATE = REPO / 'privado/semana2'
LINES = ('motor', 'buildings', 'contents')
EXPECTED = {
    'F3c': '5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276',
    'F3d': '5103f6fd9cf2c46bbb82a5ead586b4eaa0f7b34ecff6efdc99a2a0662e76706b',
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1 << 20), b''):
            h.update(part)
    return h.hexdigest()


def save(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def bindings():
    files = {}
    for name in ('etiquetas', 'forma_local', 'forma_local3', 'forma_v2', 'eval_v2',
                 'f3_eval', 'construir_F2', 'construir_final'):
        files[f'{name}.py'] = SRC / f'codigo/{name}.py'
    files.update({
        'exp26/lib26.py': SRC / 'exp26_20261026/m017/exp26/lib26.py',
        'exp26/fuga_celdas.json': SRC / 'exp26_20261026/m017/exp26/fuga_celdas.json',
        'construir_F3b.py': SRC / 'exp26_20261026/m017/construir_F3b.py',
        'construir_F3c.py': SRC / 'exp26_20261026_v2/m017/construir_F3c.py',
        'construir_F3d.py': SRC / 'exp26_20261026_v3/m017/construir_F3d.py',
        'in/preinscripcion.json': PRIVATE / 'claude_validacion_nocturna_20261023/sonda_segmento/preinscripcion.json',
        'sigma_forma.json': SRC / 'sigma_forma.json',
        'sondas_F2_info.json': SRC / 'sondas_F2_info.json',
        'in/predicciones_2024.parquet': PRIVATE / 'claude_validacion_nocturna_20261023/predicciones_2024.parquet',
        'in/final_sonda_global_2025.csv': PRIVATE / 'claude_validacion_nocturna_20261023/sonda_global/final_sonda_global_2025.csv',
        'F2_ncb_previos_2025.csv': PRIVATE / 'claude_mision017_20261025/F2_ncb_previos_2025.csv',
        'revision/J_final_creible_2025.csv': PRIVATE / 'mision017_fase2/calibracion_F2_creible_20261025_v1/final_creible_2025.csv',
        'datos/developed/claims.parquet': ROOT / 'Hackaton/Semana 1/Datos/claims.parquet',
    })
    for name in ('claims', 'customers', 'addresses', 'weather',
                 *(f'policies_{l}' for l in LINES), *(f'test_{l}' for l in LINES)):
        files[f'datos/emerging/{name}.parquet'] = ROOT / f'Hackaton/Semana 2/Datos/emerging/{name}.parquet'
    for scope in ('dev', 'hold'):
        for line in LINES:
            files[f'oof/pred/{scope}/T2b_{line}.parquet'] = PRIVATE / f'mision017_fase2/linaje_T2b_v1/pred/{scope}/T2b_{line}.parquet'
    return files


def prepare(work):
    # Resolve all bindings before creating anything. No guesses by basename.
    packages = {x: importlib.metadata.version(x) for x in ('numpy', 'pandas', 'pyarrow')}
    sources = bindings()
    missing = [str(p) for p in sources.values() if not p.is_file()]
    if missing:
        raise RuntimeError('Faltan insumos explícitos: ' + json.dumps(missing, ensure_ascii=False))
    if work.exists():
        raise RuntimeError('La carpeta de trabajo debe ser nueva; se conservan los intentos previos.')
    work.mkdir(parents=True)
    manifest = []
    for name, source in sources.items():
        target = work / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        source_hash = sha(source)
        changes = []
        if name == 'exp26/lib26.py':
            text = target.read_text(encoding='utf-8')
            for old, new in (
                ('/home/claude/m017/f3_eval.py', 'f3_eval.py'),
                ('/home/claude/ml2/datos/emerging/weather.parquet', 'datos/emerging/weather.parquet'),
            ):
                if text.count(old) != 1:
                    raise RuntimeError(f'La fuente cambió; se esperaba una aparición de {old}')
                text = text.replace(old, new)
                changes.append({'antes': old, 'despues': new})
            target.write_text(text, encoding='utf-8', newline='\n')
        if name.endswith('.py'):
            text = target.read_text(encoding='utf-8-sig')
            compile(text, str(target), 'exec')
            if '/home/claude/' in text:
                raise RuntimeError(f'Ruta absoluta no resuelta en {name}')
        manifest.append({'destino': name, 'origen': source.relative_to(ROOT).as_posix(),
                         'source_sha256': source_hash, 'staged_sha256': sha(target), 'cambios': changes})
    save(work / 'manifest.json', {
        'utc': datetime.now(timezone.utc).isoformat(), 'autor_original': 'Claude', 'adaptacion': 'Codex',
        'alcance': 'etiquetas desde originales y aprendizaje de factores con OOF guardadas; no árboles fuente',
        'archivos': manifest, 'python': sys.version, 'platform': platform.platform(),
        'packages': packages, 'python_prefix': sys.prefix,
        'venv_configuration': (Path(sys.prefix) / 'pyvenv.cfg').read_text(encoding='utf-8'),
        'reproduccion_independiente': False,
    })
    print(json.dumps({'prepared': len(manifest), 'work': str(work)}, ensure_ascii=False))


def run(work, mode):
    manifest = json.loads((work / 'manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['archivos']:
        if sha(work / entry['destino']) != entry['staged_sha256']:
            raise RuntimeError(f"Insumo alterado: {entry['destino']}")
    commands = [('etiquetas', ['etiquetas.py'])] if mode == 'etiquetas' else [
        ('F3c', ['construir_F3c.py', 'F3c']), ('F3d', ['construir_F3d.py']),
    ]
    if mode == 'factores' and not (work / 'base_etiquetas.parquet').is_file():
        raise RuntimeError('Primero reconstruya las etiquetas desde originales.')
    results = []
    for name, args in commands:
        receipt = work / f'receipt_{name}.json'
        if receipt.exists():
            raise RuntimeError(f'Ya existe {receipt.name}; no se repite un aprendizaje terminado.')
        with (work / f'{name}.log').open('wb') as log:
            r = subprocess.run([sys.executable, '-I', *args], cwd=work, stdout=log, stderr=subprocess.STDOUT)
        result = {'stage': name, 'exit_code': r.returncode, 'utc': datetime.now(timezone.utc).isoformat(),
                  'log_sha256': sha(work / f'{name}.log')}
        if name in EXPECTED and r.returncode == 0:
            result.update({'sha256': sha(work / f'exp26/{name}_2025.csv'), 'expected': EXPECTED[name]})
            result['exact'] = result['sha256'] == result['expected']
        save(receipt, result)
        results.append(result)
        if r.returncode or result.get('exact') is False:
            print(json.dumps(result, ensure_ascii=False))
            return 1
    print(json.dumps(results, ensure_ascii=False))
    return 0


def candidates(work):
    import numpy as np
    import pandas as pd
    rule_path = REPO / 'registro/semana2_lectura_F3d_F4c_v4_claude_20261026.json'
    rule = json.loads(rule_path.read_text(encoding='utf-8'))
    data = ROOT / 'Hackaton/Semana 2/Datos/emerging'
    sample = pd.read_parquet(data / 'sample_submission.parquet').row_id.astype(str)
    ids = pd.concat([pd.read_parquet(data / f'test_{line}.parquet', columns=['row_id']).assign(line=line)
                     for line in LINES], ignore_index=True)
    tests = ids.set_index('row_id').line.reindex(sample)
    result = {'autor': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
              'regla_sha256': sha(rule_path), 'sample_sha256': sha(data / 'sample_submission.parquet'),
              'decision_participante': 'Solo revisar y preparar por ahora', 'envios': 0,
              'aprobacion_informe_es': False, 'ingles': 'Diferido hasta versión española definitiva',
              'limite': 'Preflight del archivo, sin admisión estadística, scores nuevos o selección final.',
              'candidatos': {}}
    for name in ('F3c', 'F3d', 'F4c'):
        path = PRIVATE / f'claude_mision017_20261025/{name}_2025.csv'
        df = pd.read_csv(path, dtype={'row_id': str})
        values = df.prediction.to_numpy()
        expected = rule['referencia']['sha256'] if name == 'F3c' else rule['candidatos'][name]['sha256']
        checks = {'sha_historico': sha(path) == expected,
                  'columnas': list(df.columns) == ['row_id', 'prediction'],
                  'filas': len(df) == len(sample), 'orden': df.row_id.tolist() == sample.tolist(),
                  'unicos': not df.row_id.duplicated().any(), 'finitos': bool(np.isfinite(values).all()),
                  'no_negativos': bool((values >= 0).all()), 'test_tres_ramos': not tests.isna().any()}
        result['candidatos'][name] = {'sha256': sha(path), 'checks': {k: bool(v) for k, v in checks.items()},
                                     'filas': len(df), 'preflight': all(checks.values())}
    destination = work / 'revision_candidatos.json'
    if destination.exists():
        raise RuntimeError('Ya existe la revisión de candidatos; se conserva.')
    save(destination, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if all(c['preflight'] for c in result['candidatos'].values()) else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('modo', choices=('preparar', 'etiquetas', 'factores', 'candidatos'))
    p.add_argument('--trabajo', type=Path, required=True)
    args = p.parse_args()
    work = args.trabajo.resolve()
    if REPO / 'privado' not in work.parents:
        p.error('El trabajo debe estar dentro de privado/, fuera de Git.')
    try:
        if args.modo == 'candidatos':
            return candidates(work)
        return (prepare(work) or 0) if args.modo == 'preparar' else run(work, args.modo)
    except (OSError, RuntimeError, importlib.metadata.PackageNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
