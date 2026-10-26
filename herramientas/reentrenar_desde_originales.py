"""Reentrenamiento local, trazable y reanudable desde los Parquet originales.

Los originales de Claude se extraen del commit congelado; no se copian modelos
ni predicciones anteriores al espacio de cálculo. Sin red en los procesos hijo.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
COMMIT = '40b3100ba1fe59eb35faf5b3af84aa55b5ee6159'
ML = 'src/semana2/lineas/ml_independiente_20261023/codigo'
LINES = ('motor', 'buildings', 'contents')


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args])


def steps():
    out = [('ml_preparar', ['preparar_datos.py']), ('ml_historia', ['historia.py'])]
    # Cada modelo fuente se ajusta solo en la primera fase de su ámbito;
    # hold/prod reutilizan exclusivamente el modelo recién creado en esta corrida.
    for phase in ('dev', 'hold', 'pcv', 'prod'):
        for line in LINES:
            out.append((f't2b_{phase}_{line}', ['gbm.py', phase, 'ninguno', line]))
    return out


BOOTSTRAP = r'''
import os,sys,runpy,json
from pathlib import Path
work=Path(sys.argv[1]).resolve()
code=work/'ml/codigo'
script=code/sys.argv[2]
sys.path.insert(0,str(code))
allowed=[work,Path(sys.prefix).resolve(),Path(sys.base_prefix).resolve()]
def inside(p,root):return p==root or root in p.parents
def audit(event,args):
    if event in ('socket.connect','socket.bind','socket.sendto','subprocess.Popen'):
        raise PermissionError('Etapa sin red ni subprocesos: '+event)
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        path=Path(os.fsdecode(args[0])).resolve()
        if not any(inside(path,root) for root in allowed):
            raise PermissionError('Lectura externa al entorno limpio: '+str(path))
        mode=args[1] or ''
        flags=args[2] or 0
        writing=any(c in str(mode) for c in 'wax+') or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
        if writing and (not inside(path,work) or inside(path,work/'ml/datos')):
            raise PermissionError('Escritura fuera de salidas permitidas: '+str(path))
sys.addaudithook(audit)
sys.argv=[str(script),*sys.argv[3:]]
runpy.run_path(str(script),run_name='__main__')
'''


def prepare(work):
    if work.exists():
        raise RuntimeError('La carpeta de cálculo debe ser nueva; no se borra una corrida previa.')
    versions = {name: importlib.metadata.version(name) for name in
                ('numpy', 'pandas', 'pyarrow', 'lightgbm', 'scipy', 'scikit-learn')}
    work.mkdir(parents=True)
    files = []
    source_names = git('ls-tree', '-r', '--name-only', COMMIT, ML).decode('utf-8').splitlines()
    for source in source_names:
        if not source.endswith('.py'):
            continue
        data = git('show', f'{COMMIT}:{source}')
        target = work / 'ml/codigo' / Path(source).name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        compile(data, str(target), 'exec')
        files.append({'path': target.relative_to(work).as_posix(), 'source': source,
                      'commit': COMMIT, 'sha256': sha(target), 'kind': 'code_original_Claude'})
    for market, original in (
        ('developed', ROOT / 'Hackaton/Semana 1/Datos'),
        ('emerging', ROOT / 'Hackaton/Semana 2/Datos/emerging'),
    ):
        for source in sorted(original.glob('*.parquet')):
            target = work / 'ml/datos' / market / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            assert sha(target) == sha(source)
            files.append({'path': target.relative_to(work).as_posix(),
                          'source': source.relative_to(ROOT).as_posix(), 'sha256': sha(target), 'kind': 'original_data'})
    for relative in ('tmp', 'logs', 'receipts', 'ml/trabajo/modelos/dev', 'ml/trabajo/modelos/prod', 'ml/entrega', 'ml/privado'):
        (work / relative).mkdir(parents=True, exist_ok=True)
    (work / 'ejecutar_etapa.py').write_text(BOOTSTRAP, encoding='utf-8')
    cfg = (Path(sys.prefix) / 'pyvenv.cfg').read_text(encoding='utf-8')
    assert 'include-system-site-packages = false' in cfg
    save(work / 'manifest.json', {'utc': now(), 'source_commit': COMMIT, 'author_original': 'Claude',
         'orquestador': 'Codex', 'files': files, 'python': sys.version, 'python_executable': sys.executable,
         'venv': cfg, 'packages': versions, 'platform': platform.platform(),
         'historical_models_or_predictions_as_inputs': False,
         'bootstrap_sha256': sha(work / 'ejecutar_etapa.py'),
         'source_model_scope': 'T2b dev2021-2023 y prod2021-2024, tres ramos',
         'steps': [{'id': name, 'argv': args} for name, args in steps()]})
    print(json.dumps({'prepared': len(files), 'work': str(work), 'packages': versions}))


def run(work, until):
    manifest = json.loads((work / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['python_executable'] == sys.executable, 'Usar el mismo entorno limpio'
    assert sha(work / 'ejecutar_etapa.py') == manifest['bootstrap_sha256']
    for item in manifest['files']:
        if sha(work / item['path']) != item['sha256']:
            raise RuntimeError('Insumo alterado: ' + item['path'])
    lock = work / 'runner.lock'
    with lock.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps({'pid': os.getpid(), 'utc': now()}))
    env = {key: value for key, value in os.environ.items() if key.upper() in
           ('SYSTEMROOT', 'WINDIR', 'PATH', 'COMSPEC', 'PATHEXT', 'NUMBER_OF_PROCESSORS')}
    env.update(MLIND_RAIZ=str(work / 'ml'), MLIND_BACKBONE='T2b', PYTHONUTF8='1',
               PYTHONDONTWRITEBYTECODE='1', TEMP=str(work / 'tmp'), TMP=str(work / 'tmp'),
               OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2',
               KAGGLE_SKILL_READ_ONLY='1')
    try:
        for name, args in steps():
            receipt = work / 'receipts' / f'{name}.json'
            if receipt.exists():
                previous = json.loads(receipt.read_text(encoding='utf-8'))
                if previous['exit_code'] == 0:
                    # Una reanudación verifica las huellas antes de reutilizar salidas.
                    for item in previous['outputs']:
                        assert sha(work / item['path']) == item['sha256']
                    if name == until:
                        break
                    continue
                raise RuntimeError(f'Etapa fallida {name}; conservar evidencia y corregir antes de reanudar.')
            # Ningún modelo histórico debe aparecer antes de su primer entrenamiento.
            if name == 't2b_dev_motor' and list((work / 'ml/trabajo/modelos').rglob('*.txt')):
                raise RuntimeError('Había modelos antes del primer ajuste fuente')
            before = {p: (p.stat().st_size, p.stat().st_mtime_ns) for p in (work / 'ml/trabajo').rglob('*') if p.is_file()}
            save(work / 'live.json', {'utc': now(), 'runner_pid': os.getpid(), 'stage': name, 'state': 'running'})
            start = time.monotonic()
            print(f'{now()} start {name}', flush=True)
            with (work / 'logs' / f'{name}.log').open('wb') as log:
                child = subprocess.Popen([sys.executable, '-I', '-X', 'utf8', '-u', str(work / 'ejecutar_etapa.py'),
                                          str(work), *args], cwd=work / 'ml/codigo', env=env, stdout=log, stderr=subprocess.STDOUT)
                save(work / 'live.json', {'utc': now(), 'runner_pid': os.getpid(), 'child_pid': child.pid, 'stage': name, 'state': 'running'})
                code = child.wait()
            outputs = []
            for p in (work / 'ml/trabajo').rglob('*'):
                if p.is_file() and before.get(p) != (p.stat().st_size, p.stat().st_mtime_ns):
                    outputs.append({'path': p.relative_to(work).as_posix(), 'sha256': sha(p)})
            result = {'stage': name, 'utc': now(), 'exit_code': code, 'seconds': time.monotonic() - start,
                      'tool_sha256': sha(__file__), 'log_sha256': sha(work / 'logs' / f'{name}.log'), 'outputs': outputs}
            save(receipt, result)
            print(json.dumps({k: result[k] for k in ('stage', 'exit_code', 'seconds')}), flush=True)
            if code:
                save(work / 'live.json', dict(result, state='failed'))
                return 1
            if name == until:
                break
        save(work / 'live.json', {'utc': now(), 'state': 'stages_complete', 'until': until})
        return 0
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('preparar', 'correr'))
    parser.add_argument('--trabajo', type=Path, required=True)
    parser.add_argument('--hasta', choices=[name for name, _ in steps()], default=steps()[-1][0])
    args = parser.parse_args()
    work = args.trabajo.resolve()
    if REPO / 'privado' not in work.parents:
        parser.error('La corrida debe quedar dentro de privado/')
    if args.mode == 'preparar':
        prepare(work)
        return 0
    return run(work, args.hasta)


if __name__ == '__main__':
    raise SystemExit(main())
