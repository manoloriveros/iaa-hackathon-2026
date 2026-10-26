"""Completa A1, FSp y M017 con artefactos producidos en la corrida limpia.

No recibe predicciones/modelos históricos. Los SHA de los resultados anteriores
se comparan después, en otro proceso, sin condicionar parámetros de aprendizaje.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
COMMIT = '40b3100ba1fe59eb35faf5b3af84aa55b5ee6159'
NOCHE = 'src/semana2/lineas/validacion_nocturna_20261023/codigo'
M017 = 'src/semana2/lineas/mision017_20261025'
LINES = ('motor', 'buildings', 'contents')


def now(): return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''): h.update(block)
    return h.hexdigest()


def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def original(path):
    return subprocess.check_output(['git', '-C', str(REPO), 'show', f'{COMMIT}:{path}']).decode('utf-8')


def remove_output_hash_gates(text):
    # Solo las guardas de identidad del archivo histórico: los controles
    # estadísticos, de soporte, finitud y claves siguen activos.
    data = text.encode('utf-8')
    offsets = [0]
    for line in data.splitlines(keepends=True): offsets.append(offsets[-1] + len(line))
    spans = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Assert):
            condition = ast.get_source_segment(text, node.test)
            if 'hashlib' in condition or 'sha256' in condition:
                spans.append((offsets[node.lineno - 1] + node.col_offset,
                              offsets[node.end_lineno - 1] + node.end_col_offset))
    for start, end in sorted(spans, reverse=True): data = data[:start] + b'pass' + data[end:]
    return data.decode('utf-8'), len(spans)


def plan():
    rows = []
    def add(name, family, argv, **extra): rows.append(dict(id=name, family=family, argv=argv, **extra))
    add('ml_C1', 'ml', ['@aux', 'ml_c1'])
    add('noche_base_s1', 'noche', ['base_mercado.py', 's1'])
    add('noche_base_s2', 'noche', ['base_mercado.py', 's2'])
    add('noche_curva_global', 'noche', ['@aux', 'curve'])
    add('noche_ultimo_s1', 'noche', ['ultimo_mercado.py', 's1'])
    add('noche_ultimo_s2', 'noche', ['ultimo_mercado.py', 's2'])
    add('noche_conf_insumos', 'noche', ['conf_insumos.py'])
    # Solo se precisan modelos completos para el CSV designado, y tres
    # modelos del acta original para HOLD24_A1. No repetir los conf de F1.
    for history in (False, True):
        for seed in (11, 12, 13):
            for line in LINES:
                if history:
                    suffix = ('_v2fixf1' if line == 'motor' else '_v2f1') + (f's{seed}' if seed != 11 else '')
                else:
                    suffix = f'_v2fixs{seed}' if line == 'motor' else ('_m02' if seed == 11 else f'_v2s{seed}')
                argv = ['desarrollado_gbm.py', line, '--sufijo', suffix, '--lr', '.02', '--pat', '400', '--seed', str(seed)]
                if line == 'motor': argv += ['--sin', 'make_model']
                if history: argv += ['--f1']
                add(f'A1_full_{line}_{seed}_{"F1" if history else "base"}', 'noche', argv)
    for line in LINES:
        argv = ['desarrollado_gbm.py', line, '--años', '2021,2022,2023', '--sufijo', '_v2conf', '--lr', '.02', '--pat', '400', '--conf', '--seed', '11']
        if line == 'motor': argv += ['--sin', 'make_model']
        add(f'A1_conf_historico_{line}', 'noche', argv, legacy_id01=(line == 'motor'))
    add('A1_produccion_y_hold', 'noche', ['@aux', 'a1_post'])
    add('m017_insumos_generados', 'ml', ['@aux', 'm017_inputs'])
    add('m017_F2', 'm017', ['construir_F2.py'])
    add('m017_final_creible', 'm017', ['construir_final.py', 'recibos_reales_20261026.json'])
    add('m017_alias_J', 'm017', ['@aux', 'final_alias'])
    add('m017_F3c', 'm017', ['construir_F3c.py', 'F3c'])
    add('m017_F3d', 'm017', ['construir_F3d.py'])
    add('ml_conteos_peril', 'ml', ['conteos_peligro.py'])
    for scope, script in (('dev', 'fsp_light.py'), ('prod', 'fsp_light_prod.py')):
        for line in LINES: add(f'FSp_{scope}_{line}', 'ml', [script, line])
    add('m017_F4c', 'm017', ['construir_F3c.py', 'F4c'])
    return rows


BOOTSTRAP = r'''
import sys,os,runpy
from pathlib import Path
work=Path(sys.argv[1]).resolve();family=sys.argv[2]
code=work/'ml/codigo' if family=='ml' else work/family/'codigo' if family=='noche' else work/'m017'
sys.path.insert(0,str(code))
name=sys.argv[3];script=work/'aux/reproduccion_cadena.py' if name=='@aux' else code/name
allowed=[work,Path(sys.prefix).resolve(),Path(sys.base_prefix).resolve()]
def inside(p,r):return p==r or r in p.parents
def hook(event,args):
    if event in ('socket.connect','socket.bind','socket.sendto','subprocess.Popen'):raise PermissionError('Etapa sin red/subprocesos: '+event)
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        p=Path(os.fsdecode(args[0])).resolve()
        if not any(inside(p,r) for r in allowed):raise PermissionError('Lectura ajena a la corrida limpia: '+str(p))
        mode=args[1] or '';flags=args[2] or 0
        wr=any(c in str(mode) for c in 'wax+') or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
        if wr and (not inside(p,work) or inside(p,work/'ml/datos') or inside(p,work/'noche/datos')):raise PermissionError('Escritura no permitida: '+str(p))
sys.addaudithook(hook)
sys.argv=[str(script),*sys.argv[4:]]
runpy.run_path(str(script),run_name='__main__')
'''


def prepare(work):
    if (work / 'chain_manifest.json').exists(): raise RuntimeError('El suplemento ya existe; no se sobrescribe')
    base = json.loads((work / 'manifest.json').read_text(encoding='utf-8'))
    assert base['source_commit'] == COMMIT
    entries = []
    def stage(destination, source, *, local=False, m017=False):
        text = (REPO / source).read_text(encoding='utf-8') if local else original(source)
        original_sha = hashlib.sha256(text.encode('utf-8')).hexdigest()
        changes = []
        for old, new in (('/home/claude/noche', (work / 'noche').as_posix()),
                         ('/home/claude/m017', (work / 'm017').as_posix()),
                         ('/home/claude/ml2', (work / 'ml').as_posix())):
            if old in text:
                changes.append({'ruta': old, 'sustitucion': new, 'apariciones': text.count(old)})
                text = text.replace(old, new)
        if destination == 'noche/codigo/variables.py':
            old = 'key = base.customer_id.astype(str).str.zfill(8)'
            assert text.count(old) == 1
            text = text.replace(old, "key = base.customer_id.astype(str) if __import__('os').environ.get('A1_PRE_ID01') else base.customer_id.astype(str).str.zfill(8)")
            old = "assert df.customer_since_year.notna().all(), 'cruce de clientes incompleto'"
            assert text.count(old) == 1
            text = text.replace(old, "assert __import__('os').environ.get('A1_PRE_ID01') or df.customer_since_year.notna().all(), 'cruce de clientes incompleto'")
            changes.append({'restauracion': 'Solo A1_conf_historico_motor: no rellenar ceros y permitir clientes ausentes, defecto ID01 documentado. No es una fuente anterior recuperada.'})
        if m017:
            text, count = remove_output_hash_gates(text)
            if count: changes.append({'guardas_sha_historico_trasladadas_al_cotejo_externo': count})
        p = work / destination
        if p.exists(): raise RuntimeError('Destino ya existente: ' + destination)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8', newline='\n')
        compile(text, str(p), 'exec')
        entries.append({'path': destination, 'source': source, 'original_sha256': original_sha,
                        'sha256': sha(p), 'changes': changes, 'local_adapter': local})
    for name in ('base_mercado', 'reporte', 'exposicion_efectiva', 'ultimo_mercado', 'conf_insumos', 'desarrollado_gbm', 'variables', 'marco'):
        stage(f'noche/codigo/{name}.py', f'{NOCHE}/{name}.py')
    for name in ('fsp_light', 'fsp_light_prod'):
        stage(f'ml/codigo/{name}.py', f'{M017}/exp26_20261026/ml2/codigo/{name}.py')
    sources = {
      **{f'{name}.py': f'{M017}/codigo/{name}.py' for name in ('forma_local','forma_local3','forma_v2','eval_v2','f3_eval','construir_F2','construir_final')},
      'exp26/lib26.py': f'{M017}/exp26_20261026/m017/exp26/lib26.py',
      'exp26/fsp_blend_eval.py': f'{M017}/exp26_20261026/m017/exp26/fsp_blend_eval.py',
      'construir_F3b.py': f'{M017}/exp26_20261026/m017/construir_F3b.py',
      'construir_F4b.py': f'{M017}/exp26_20261026_v2/m017/construir_F4b.py',
      'construir_F3c.py': f'{M017}/exp26_20261026_v2/m017/construir_F3c.py',
      'construir_F3d.py': f'{M017}/exp26_20261026_v3/m017/construir_F3d.py',
    }
    # F4b v2 es idéntico al original incorporado, omitido por deduplicación.
    try: original(sources['construir_F4b.py'])
    except subprocess.CalledProcessError: sources['construir_F4b.py'] = f'{M017}/exp26_20261026/m017/construir_F4b.py'
    for destination, source in sources.items(): stage('m017/' + destination, source, m017=True)
    stage('aux/reproduccion_cadena.py', 'src/semana2/reproduccion_cadena.py', local=True)
    # Únicos insumos derivados externos: constantes públicas y registros congelados,
    # sin importes por fila ni modelos. Se conserva su procedencia por SHA.
    configs = {
       'm017/in/preinscripcion.json': REPO / 'privado/semana2/claude_validacion_nocturna_20261023/sonda_segmento/preinscripcion.json',
       'm017/sigma_forma.json': REPO / f'{M017}/sigma_forma.json',
       'm017/sondas_F2_info.json': REPO / f'{M017}/sondas_F2_info.json',
       'm017/recibos_reales_20261026.json': REPO / f'{M017}/recibos_reales_20261026.json',
       'm017/exp26/fuga_celdas.json': REPO / f'{M017}/exp26_20261026/m017/exp26/fuga_celdas.json',
    }
    for dest, source in configs.items():
        p = work / dest; p.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, p)
        entries.append({'path': dest, 'source': source.relative_to(ROOT).as_posix(), 'sha256': sha(p), 'kind': 'frozen_historical_metadata_not_row_predictions'})
    source = REPO / 'registro/semana2_envio_final_sonda_global_20261024.json'
    g = json.loads(source.read_text(encoding='utf-8'))['credibility_factor']
    save(work / 'm017/in/constantes_publicas.json', {'factor_global': g, 'source': source.relative_to(ROOT).as_posix(), 'source_sha256': sha(source)})
    entries.append({'path': 'm017/in/constantes_publicas.json', 'sha256': sha(work / 'm017/in/constantes_publicas.json')})
    for market, target in (('developed','s1'),('emerging','s2')):
        for source in sorted((work / f'ml/datos/{market}').glob('*.parquet')):
            p = work / f'noche/datos/{target}/{source.name}'; p.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source,p)
    for relative in ('noche/salidas/conf','noche/salidas/transfer','noche/salidas/correccion','m017/in','m017/revision','chain_logs','chain_receipts'):
        (work / relative).mkdir(parents=True, exist_ok=True)
    (work / 'ejecutar_bloque.py').write_text(BOOTSTRAP, encoding='utf-8')
    entries.append({'path': 'ejecutar_bloque.py', 'sha256': sha(work / 'ejecutar_bloque.py')})
    save(work / 'chain_manifest.json', {'utc': now(), 'source_commit': COMMIT, 'files': entries, 'plan': plan(),
         'historical_row_predictions_as_inputs': False, 'source_models_as_inputs': False,
         'restorations_not_recovered_originals': ['REP-N2 global curve from conf_insumos formula without year filter', 'pre-ID01 customer linkage for historical motor A1']})
    print(json.dumps({'supplement_files': len(entries), 'steps': len(plan())}))


def scan(work):
    out = {}
    for rel in ('ml/trabajo','ml/privado','noche/salidas','m017'):
        for p in (work / rel).rglob('*'):
            if p.is_file(): out[p] = (p.stat().st_size,p.stat().st_mtime_ns)
    return out


def run(work, until):
    assert not (work / 'runner.lock').exists(), 'La unidad T2b anterior sigue activa; no competir por modelos/cómputo'
    assert json.loads((work / 'receipts/t2b_prod_contents.json').read_text(encoding='utf-8'))['exit_code'] == 0
    manifest = json.loads((work / 'chain_manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['files']: assert sha(work / entry['path']) == entry['sha256'],entry['path']
    latest = {}
    for step in manifest['plan']:
        p = work / f'chain_receipts/{step["id"]}.json'
        if p.exists():
            receipt = json.loads(p.read_text(encoding='utf-8'))
            assert receipt['exit_code'] == 0, f'Fallo preservado en {p}'
            latest.update({x['path']:x['sha256'] for x in receipt['outputs']})
    for p,digest in latest.items(): assert sha(work / p) == digest,p
    lock = work / 'chain.lock'
    with lock.open('x',encoding='utf-8') as f:f.write(json.dumps({'pid':os.getpid(),'utc':now()}))
    env = {k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','PATH','COMSPEC','PATHEXT','NUMBER_OF_PROCESSORS')}
    env.update(RETRAIN_WORK=str(work), MLIND_RAIZ=str(work/'ml'), MLIND_BACKBONE='T2b',
       PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',TEMP=str(work/'tmp'),TMP=str(work/'tmp'),
       OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',KAGGLE_SKILL_READ_ONLY='1')
    try:
        for step in manifest['plan']:
            name=step['id']; receipt=work/f'chain_receipts/{name}.json'
            if receipt.exists():
                if name==until:break
                continue
            family=step['family']; cwd=work/'ml/codigo' if family=='ml' else work/'noche/codigo' if family=='noche' else work/'m017'
            childenv=dict(env)
            if step.get('legacy_id01'):childenv['A1_PRE_ID01']='1'
            before=scan(work);start=time.monotonic();logpath=work/f'chain_logs/{name}.log'
            print(f'{now()} start {name}',flush=True)
            with logpath.open('wb') as log:
                p=subprocess.Popen([sys.executable,'-I','-X','utf8','-u',str(work/'ejecutar_bloque.py'),str(work),family,*step['argv']],cwd=cwd,env=childenv,stdout=log,stderr=subprocess.STDOUT)
                save(work/'chain_live.json',{'utc':now(),'runner_pid':os.getpid(),'child_pid':p.pid,'stage':name,'state':'running'})
                code=p.wait()
            outputs=[{'path':p.relative_to(work).as_posix(),'sha256':sha(p)} for p,state in scan(work).items() if before.get(p)!=state]
            result={'utc':now(),'stage':name,'exit_code':code,'seconds':time.monotonic()-start,'outputs':outputs,'log_sha256':sha(logpath),'tool_sha256':sha(__file__)}
            save(receipt,result);print(json.dumps({k:result[k] for k in ('stage','exit_code','seconds')}),flush=True)
            if code:
                save(work/'chain_live.json',dict(result,state='failed'));return 1
            if name==until:break
        save(work/'chain_live.json',{'utc':now(),'state':'stages_complete','until':until});return 0
    finally:lock.unlink()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('preparar','correr'));p.add_argument('--trabajo',type=Path,required=True);p.add_argument('--hasta',choices=[s['id'] for s in plan()],default='m017_F4c')
    a=p.parse_args();w=a.trabajo.resolve()
    assert REPO/'privado' in w.parents
    if a.mode=='preparar':prepare(w)
    else:raise SystemExit(run(w,a.hasta))
