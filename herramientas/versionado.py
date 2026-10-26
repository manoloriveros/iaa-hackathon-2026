"""Control de versiones del repositorio: auditoría, vigía, guardia antes de cada commit, sello, plan y entrega.

Solo usa la biblioteca estándar y el ejecutable git. Las órdenes de git que lanza son de lectura (con
--no-optional-locks y sin refrescar el índice), salvo `empaquetar`, que escribe el paquete fuera de Git.
La herramienta nunca hace commits ni push: los hace un operador en Windows con el plan que deja `plan`.

Órdenes:
  auditar     Estado del historial, cambios pendientes por área, código fuera de Git y del repositorio,
              guardia sobre lo pendiente y sobre la historia completa y etiquetas citadas que no existen.
              Escribe registro/versionado/auditoria_<utc>.json y .md.
  vigia       Decide si hay cambios importantes sin registrar (código pendiente de varias horas, recibos de
              envío o decisiones sin commit, demasiados archivos pendientes, commits sin subir). Código 0 si
              no hace falta nada, 3 si conviene registrar, 1 si la guardia encuentra algo prohibido.
  guardia     Revisa lo preparado para el próximo commit (git add); termina con 1 si algo debe quedarse fuera.
              La usa el hook herramientas/git_hooks/pre-commit.
  sello       Identifica en JSON la versión del código que produjo un resultado (commit, etiqueta, estado).
              Con --exigir-limpio termina con 1 si alguna ruta no está en Git o tiene cambios sin commit.
  plan        Propone commits temáticos para lo pendiente. Con --cronologico los ordena por la fecha de
              última modificación de cada archivo (un commit por día y tema) y deja aplicar_plan.ps1, que
              registra cada commit con esa fecha como fecha de autor y la fecha real como fecha de commit.
  incorporar  Copia sin cambios, con su fecha de modificación, el código y la documentación de una carpeta
              externa a una carpeta nueva del repositorio, con ORIGEN.json; omite datos y lo que ya está en el
              repositorio con otro nombre. Sin --actualizar nunca sobrescribe; con --actualizar trae los archivos
              nuevos o cambiados de un origen ya incorporado y anota la actualización en ORIGEN.json;
              --actualizar-todo lo hace con todas las incorporaciones registradas bajo src/.
  empaquetar  Para una etiqueta o commit: bundle con la historia completa, ZIP del árbol y manifiesto SHA-256.

Códigos de salida: 0 correcto, 1 bloqueo o comprobación fallida, 2 uso incorrecto, 3 registro recomendado.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path

VERSION = '1.1'
REPO = Path(__file__).resolve().parents[1]
BOGOTA = dt.timezone(dt.timedelta(hours=-5))

# ---------------------------------------------------------------- reglas de contenido
# §2.5.b de las reglas específicas prohíbe redistribuir los datos del concurso. Por política del proyecto
# (AGENTS.md del repositorio) tampoco se versionan predicciones por fila ni modelos entrenados.
EXT_BLOQUEO = {
    '.parquet', '.feather', '.arrow', '.npy', '.npz', '.pkl', '.pickle', '.joblib', '.cbm', '.pt', '.pth',
    '.onnx', '.h5', '.hdf5', '.zip', '.7z', '.gz', '.tgz', '.tar', '.bz2', '.xz', '.bundle', '.db', '.sqlite',
    '.xlsx', '.xls', '.csv', '.tsv', '.dat', '.ubj', '.bin', '.model', '.lgb', '.xgb', '.safetensors', '.ckpt',
    '.rds', '.rda', '.sav', '.dta', '.bak', '.orc', '.avro',
}
PERMITIDOS = [re.compile(p) for p in (r'^receta/.+\.csv$', r'^docs/expediente/[^/]+/indice\.csv$')]
BINARIOS_PERMITIDOS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.pdf', '.woff', '.woff2', '.ttf', '.otf'}
TAM_AVISO = 2 * 1024 * 1024
TAM_BLOQUEO = 10 * 1024 * 1024
SECRETOS = [
    ('token Kaggle', re.compile(rb'KGAT_[A-Za-z0-9]{16,}')),
    ('kaggle.json', re.compile(rb'"key"\s*:\s*"[0-9a-f]{32}"')),
    ('clave privada', re.compile(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('token GitHub', re.compile(rb'\bgh[pousr]_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{30,}\b')),
    ('clave de API', re.compile(rb'\bsk-(?:ant-)?[A-Za-z0-9_-]{30,}\b|\bAIza[0-9A-Za-z_-]{35}\b|\bhf_[A-Za-z0-9]{30,}\b')),
    ('clave AWS', re.compile(rb'\bAKIA[0-9A-Z]{16}\b')),
    ('token Slack', re.compile(rb'\bxox[abprs]-[A-Za-z0-9-]{10,}\b')),
    ('cabecera Bearer', re.compile(rb'(?i)authorization:\s*bearer\s+[A-Za-z0-9._~+/-]{20,}')),
]
MODELOS = re.compile(rb'(?:\Atree\r?\nversion=v\d|"gradient_booster"\s*:|"oblivious_trees"\s*:)')
# Identificadores con la forma de los del concurso: row_id y policy_id (letra y 7 a 9 dígitos) y
# customer_id o claim_id (8 dígitos). Muchos distintos en un archivo indican una tabla por fila.
IDS = [('alfanuméricos', re.compile(rb'\b[A-Z]{1,2}[0-9]{7,9}\b')),
       ('numéricos', re.compile(rb'(?<![\d.,])\b[0-9]{8}\b(?![.,]\d)'))]
IDS_AVISO, IDS_BLOQUEO = 50, 200
RUTA_PERSONAL = re.compile(rb'(?i)\b[A-Z]:[\\/]{1,2}Users[\\/]{1,2}[^\\/\s"\']+')
EXT_CODIGO = {'.py', '.ipynb', '.ps1', '.r', '.sql', '.sh', '.mjs', '.js'}
OMITIR_DIRS = {'__pycache__', '.venv', '.venv-kaggle', '.git', 'runs', 'privado', 'node_modules',
               'catboost_info', '.cache', '.pytest_cache', '.ruff_cache', 'Datos', 'data'}
# Carpetas de trabajo con código propio. Se omite Hackaton/Semana 1/Modelado_codex/nocturna_20261017_N01, que
# guarda miles de copias instantáneas de código por corrida; la receta final de la parte 1 está en src/ y receta/.
EXTERNOS = ['Hackaton/Semana 2/Claude', 'Hackaton/Semana 2/Codex', 'Hackaton/Semana 2/Foro',
            'Hackaton/Semana 1/Modelos_claude', 'Hackaton/Semana 1/Modelos_claude_b', 'Hackaton/Semana 1/Envios',
            'Hackaton/Semana 1/Bases_actuariales_claude', 'Hackaton/Semana 1/Matriz_F0_claude',
            'Hackaton/Semana 1/Limpieza', 'Hackaton/Semana 1/Modelado', 'Preparación/src', 'Preparación/scripts']
VERSIONADO_EN_NOMBRE = re.compile(r'_v\d+(?:_[^/]*)?\.[A-Za-z0-9]+$')
EVIDENCIA_CLAVE = re.compile(r'(?i)^registro/.*(envio|recibo|decision|acta|seleccion|marca|autoriz)')

# Temas de los commits propuestos, en orden; gana la primera regla que coincide (sin distinguir mayúsculas).
P1 = (r'(s4[0-3]|sonda_(nivel|forma)|reservas_s4|regenerar_s4|d10[0-3]|marca_final|seleccion_final|'
      r'decision_(final|reservas|marca)_s4|reproduccion_s4|sensibilidad_s4|modelo_final_s41|semana1|'
      r'severidad_compartida|propuesta_modelo|envios_privados|s22_s30|prima_escrita)')
P2 = (r'(semana2|s2_|_s2|2023|2024|2025|mision017|emerg|privada|752144|nocturn|robustez|g4|b19|b20|fsp|a1s|'
      r'h1|h3b|pul\d?|f3c|f2_|f0[1-5]|t2b|rfs1p|fase2|_nb|completitud|dt1|het|ciclo\d|hogar|parquet_oficiales|'
      r'alias24|continuidad_2026|captura_equipo|kaggle_existente|estado_publico)')
GRUPOS = [
    ('gobierno', 'Gobernar el control de versiones con guardia, sello, vigía y auditoría',
     [r'^\.git(ignore|attributes)$', r'^AGENTS\.md$', r'^(LICENSE|NOTICE\.md)$', r'^herramientas/versionado\.py$', r'^herramientas/git_hooks/',
      r'^docs/(CONTROL_DE_VERSIONES|VERSION_CONTROL)\.md$', r'^registro/versionado/']),
    ('parte1_entregables', 'Actualizar los entregables de la parte 1: informe, panel, láminas, guion y guías de IA',
     [r'^docs/entrega/', r'^README(\.es)?\.md$', r'^docs/GUIA_TECNICA\.md$', r'^docs/expediente/',
      r'^herramientas/(cifras_entregables|construir_entrega|verificar_entregables|exportar_expediente|'
      r'actualizar_revision|panel_template)']),
    ('parte1_cierre', 'Registrar el cierre de la parte 1: sondas, sensibilidad, reservas, reproducción y selección final',
     [r'^(docs|herramientas|registro)/.*' + P1, r'^docs/(REPRODUCCION_COMPLETA|RESERVAS_ACOTACION)\.md$']),
    ('semana1_codigo', 'Registrar el código de trabajo de la semana 1 que no estaba en el repositorio',
     [r'^src/semana1/', r'^src/preparacion/']),
    ('semana2_codigo', 'Registrar el código de la semana 2: datos, modelos, validación y selección',
     [r'^src/semana2/', r'^herramientas/.*' + P2, r'^herramientas/[^/]*(seleccionar|metric_binding|'
      r'leer_foro|buscar_aclaraciones|revision_formulario)']),
    ('semana2_docs', 'Documentar los experimentos de la semana 2 y su protocolo de selección',
     [r'^docs/semana2/', r'^docs/.*' + P2]),
    ('semana2_registro', 'Registrar planes preinscritos, actas, recibos y decisiones de la semana 2',
     [r'^registro/.*' + P2]),
    ('registro_general', 'Actualizar el registro común: estado, requisitos, revisiones y recibos', [r'^registro/']),
    ('resto', 'Registrar documentos y herramientas restantes', [r'.*']),
]
REGLAS_GRUPOS = [(g, m, [re.compile(r, re.IGNORECASE) for r in rs]) for g, m, rs in GRUPOS]


def utc_ahora() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def git(*args: str, entrada: bytes | None = None, ok: tuple[int, ...] = (0,)) -> bytes:
    cmd = ['git', '--no-optional-locks', '-c', 'core.quotepath=off', '-C', str(REPO), *args]
    try:
        r = subprocess.run(cmd, input=entrada, capture_output=True)
    except FileNotFoundError:
        sys.stderr.write('git no está instalado o no está en el PATH.\n')
        raise SystemExit(2)
    if r.returncode not in ok:
        raise RuntimeError(f'git {" ".join(args[:3])} -> {r.returncode}: {r.stderr.decode("utf-8", "replace").strip()}')
    return r.stdout


def git_txt(*args: str, ok: tuple[int, ...] = (0,)) -> str:
    return git(*args, ok=ok).decode('utf-8', 'replace').strip()


def lista_z(salida: bytes) -> list[str]:
    return [p.decode('utf-8', 'replace') for p in salida.split(b'\0') if p]


def sha256(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def sha_normalizado(datos: bytes) -> str:
    """Huella que ignora finales de línea CRLF/LF, para reconocer copias del mismo script."""
    return sha256(datos.replace(b'\r\n', b'\n'))


def como_texto(datos: bytes) -> bytes | None:
    """Devuelve el contenido en UTF-8 si es texto (UTF-8 o UTF-16 con BOM, como el que deja PowerShell 5.1)."""
    if datos[:2] in (b'\xff\xfe', b'\xfe\xff'):
        try:
            return datos.decode('utf-16').encode('utf-8')
        except UnicodeDecodeError:
            return None
    return None if b'\0' in datos[:8192] else datos


def revisar_contenido(ruta: str, tam: int, datos: bytes | None) -> list[dict]:
    """Hallazgos para una ruta relativa al repositorio. datos=None si no se pudo o no se quiso leer."""
    h = []
    ext = Path(ruta).suffix.lower()
    if ruta.startswith('privado/') or '/privado/' in ruta:
        h.append({'nivel': 'bloqueo', 'regla': 'carpeta privado/', 'detalle': 'privado/ está excluida de Git'})
    if ext in EXT_BLOQUEO and not any(p.match(ruta) for p in PERMITIDOS):
        h.append({'nivel': 'bloqueo', 'regla': 'extensión de datos o artefacto',
                  'detalle': f'{ext}: datos, predicciones por fila, modelos o archivos comprimidos no se versionan'})
    if tam > TAM_BLOQUEO:
        h.append({'nivel': 'bloqueo', 'regla': 'tamaño', 'detalle': f'{tam / 1e6:.1f} MB > {TAM_BLOQUEO / 1e6:.0f} MB'})
    elif tam > TAM_AVISO:
        h.append({'nivel': 'aviso', 'regla': 'tamaño', 'detalle': f'{tam / 1e6:.1f} MB > {TAM_AVISO / 1e6:.0f} MB'})
    if datos is None:
        return h
    texto = como_texto(datos)
    if texto is None:
        if ext not in BINARIOS_PERMITIDOS:
            h.append({'nivel': 'bloqueo', 'regla': 'binario no reconocido',
                      'detalle': f'contenido binario con extensión {ext or "(sin)"}; solo se admiten imágenes, PDF y fuentes'})
        return h
    for nombre, rx in SECRETOS:
        if rx.search(texto):
            h.append({'nivel': 'bloqueo', 'regla': 'secreto', 'detalle': nombre})
    if MODELOS.search(texto):
        h.append({'nivel': 'bloqueo', 'regla': 'modelo entrenado', 'detalle': 'formato de modelo LightGBM, XGBoost o CatBoost'})
    for nombre, rx in IDS:
        n_ids = len(set(rx.findall(texto)))
        if n_ids >= IDS_BLOQUEO:
            h.append({'nivel': 'bloqueo', 'regla': 'identificadores por fila',
                      'detalle': f'{n_ids} identificadores {nombre} distintos con forma de los del concurso: parece una tabla por fila'})
        elif n_ids >= IDS_AVISO:
            h.append({'nivel': 'aviso', 'regla': 'identificadores por fila',
                      'detalle': f'{n_ids} identificadores {nombre} distintos con forma de los del concurso'})
    if RUTA_PERSONAL.search(texto):
        h.append({'nivel': 'info', 'regla': 'ruta personal', 'detalle': 'cita una ruta de la carpeta de usuario de Windows'})
    return h


# ---------------------------------------------------------------- estado del repositorio

def estado_pendiente() -> list[dict]:
    """Cambios del árbol de trabajo frente a HEAD."""
    partes = git('status', '--porcelain=v1', '-z', '-uall').split(b'\0')
    res, i = [], 0
    while i < len(partes):
        e = partes[i]
        i += 1
        if len(e) < 4:
            continue
        xy, ruta = e[:2].decode(), e[3:].decode('utf-8', 'replace')
        if 'R' in xy or 'C' in xy:
            i += 1  # la entrada siguiente es la ruta de origen del renombre o la copia
        tipo = ('sin_versionar' if xy == '??' else 'borrado' if 'D' in xy else
                'preparado' if xy[0] not in ' ?' else 'modificado')
        res.append({'xy': xy, 'ruta': ruta, 'tipo': tipo})
    return res


def area(ruta: str) -> str:
    p = ruta.split('/')
    return '/'.join(p[:2]) if p[0] in ('docs', 'src') and len(p) > 2 else p[0] if len(p) > 1 else '(raíz)'


def tema(ruta: str) -> tuple[str, str]:
    for g, m, rs in REGLAS_GRUPOS:
        if any(r.search(ruta) for r in rs):
            return g, m
    return 'resto', REGLAS_GRUPOS[-1][1]


def info_historial() -> dict:
    info: dict = {}
    try:
        info['head'] = git_txt('rev-parse', 'HEAD')
    except RuntimeError:
        return {'head': None, 'commits': 0, 'etiquetas': [], 'remoto': None}
    info['rama'] = git_txt('rev-parse', '--abbrev-ref', 'HEAD')
    info['commits'] = int(git_txt('rev-list', '--count', 'HEAD'))
    ult = git_txt('log', '-1', '--format=%H%x1f%cI%x1f%an%x1f%s').split('\x1f')
    info['ultimo_commit'] = {'sha': ult[0], 'fecha': ult[1], 'autor': ult[2], 'mensaje': ult[3]}
    fechas = git_txt('log', '--format=%cs').split('\n')
    info['commits_por_dia'] = {d: fechas.count(d) for d in sorted(set(fechas))}
    try:
        ultimo = dt.datetime.fromisoformat(ult[1])
        info['dias_desde_ultimo_commit'] = round((dt.datetime.now(dt.timezone.utc) - ultimo).total_seconds() / 86400, 2)
    except ValueError:
        pass
    up = git_txt('rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}', ok=(0, 128))
    if up and 'fatal' not in up and not up.startswith('@'):
        a, b = git_txt('rev-list', '--left-right', '--count', f'HEAD...{up}').split()
        info['remoto'] = {'rama': up, 'commits_sin_subir': int(a), 'commits_sin_bajar': int(b),
                          'nota': 'según la copia local del remoto; esta herramienta no consulta GitHub'}
    else:
        info['remoto'] = None
    etq = git_txt('for-each-ref', 'refs/tags', '--format=%(refname:short)%1f%(objectname:short)%1f%(creatordate:iso-strict)%1f%(contents:subject)')
    info['etiquetas'] = [dict(zip(('nombre', 'objeto', 'fecha', 'asunto'), l.split('\x1f'))) for l in etq.split('\n') if l]
    return info


def archivos_repo() -> tuple[list[str], list[str]]:
    return lista_z(git('ls-files', '-z')), lista_z(git('ls-files', '-z', '--others', '--exclude-standard'))


def leer(ruta: str) -> tuple[int, bytes | None]:
    p = REPO / ruta
    try:
        tam = p.stat().st_size
        return tam, (p.read_bytes() if tam <= TAM_BLOQUEO else None)
    except OSError:
        return -1, None


def leer_blobs(shas: list[str]) -> tuple[dict[str, int], dict[str, bytes]]:
    """Tamaño y contenido (hasta TAM_BLOQUEO) de una lista de blobs, con dos llamadas a git cat-file."""
    if not shas:
        return {}, {}
    tam: dict[str, int] = {}
    for l in git('cat-file', '--batch-check', entrada=('\n'.join(shas) + '\n').encode()).decode().split('\n'):
        p = l.split()
        if len(p) == 3 and p[1] == 'blob':
            tam[p[0]] = int(p[2])
    leer_sha = [s for s, t in tam.items() if t <= TAM_BLOQUEO]
    cont = git('cat-file', '--batch', entrada=('\n'.join(leer_sha) + '\n').encode()) if leer_sha else b''
    datos, pos = {}, 0
    while pos < len(cont):
        fin = cont.index(b'\n', pos)
        cab = cont[pos:fin].decode().split()
        if len(cab) != 3:  # objeto ausente (clon parcial)
            pos = fin + 1
            continue
        t = int(cab[2])
        datos[cab[0]] = cont[fin + 1: fin + 1 + t]
        pos = fin + 1 + t + 1
    return tam, datos


def revisar_historia() -> dict:
    """Revisa todos los blobs alcanzables desde cualquier referencia: nombre, tamaño y contenido."""
    rutas: dict[str, str] = {}
    for l in git('rev-list', '--objects', '--all').decode('utf-8', 'replace').split('\n'):
        if ' ' in l:
            s, r = l.split(' ', 1)
            rutas.setdefault(s, r)
    tam, datos = leer_blobs(list(rutas))
    hallazgos = []
    for s, t in tam.items():
        for h in revisar_contenido(rutas[s], t, datos.get(s)):
            if h['nivel'] in ('bloqueo', 'aviso'):
                hallazgos.append({'ruta': rutas[s], 'blob': s[:12], **h})
    return {'blobs': len(tam), 'bytes': sum(tam.values()),
            'bloqueos': [x for x in hallazgos if x['nivel'] == 'bloqueo'],
            'avisos': [x for x in hallazgos if x['nivel'] == 'aviso']}


def codigo_externo(raiz: Path, carpetas: list[str], presupuesto: float) -> dict:
    """Código del proyecto que vive fuera del repositorio y no tiene copia idéntica dentro."""
    seguidos, nuevos = archivos_repo()
    en_repo: dict[str, str] = {}
    for ruta, estado in [(r, 'versionado') for r in seguidos] + [(r, 'sin_versionar') for r in nuevos]:
        if Path(ruta).suffix.lower() in EXT_CODIGO:
            try:
                en_repo.setdefault(sha_normalizado((REPO / ruta).read_bytes()), estado)
            except OSError:
                pass
    inicio, res, completo = time.monotonic(), [], True
    for c in carpetas:
        base = raiz / c
        fila = {'carpeta': c, 'existe': base.is_dir(), 'archivos': 0, 'distintos': 0, 'copia_versionada': 0,
                'copia_sin_versionar': 0, 'sin_copia': 0, 'nombres_con_vN': 0, 'ejemplos_sin_copia': []}
        vistos: set[str] = set()
        if base.is_dir():
            for d, subd, fich in os.walk(base):
                subd[:] = [s for s in subd if s not in OMITIR_DIRS and not s.startswith('.')]
                rd = Path(d).resolve()
                if rd == REPO or REPO in rd.parents:
                    subd[:] = []
                    continue
                for f in fich:
                    if Path(f).suffix.lower() not in EXT_CODIGO:
                        continue
                    p = Path(d) / f
                    try:
                        h = sha_normalizado(p.read_bytes())
                    except OSError:
                        continue
                    fila['archivos'] += 1
                    if h not in vistos:
                        vistos.add(h)
                        fila['distintos'] += 1
                    fila['nombres_con_vN'] += bool(VERSIONADO_EN_NOMBRE.search(f))
                    e = en_repo.get(h)
                    if e == 'versionado':
                        fila['copia_versionada'] += 1
                    elif e == 'sin_versionar':
                        fila['copia_sin_versionar'] += 1
                    else:
                        fila['sin_copia'] += 1
                        if len(fila['ejemplos_sin_copia']) < 5:
                            fila['ejemplos_sin_copia'].append(str(p.relative_to(raiz)).replace('\\', '/'))
                if time.monotonic() - inicio > presupuesto:
                    completo = False
                    break
        res.append(fila)
        if not completo:
            break
    return {'raiz': raiz.name, 'completo': completo, 'segundos': round(time.monotonic() - inicio, 1), 'carpetas': res}


def proponer_plan(pend: list[dict], cronologico: bool = False) -> list[dict]:
    grupos: dict[tuple, dict] = {}
    for e in pend:
        g, m = tema(e['ruta'])
        try:
            mt = (REPO / e['ruta']).stat().st_mtime if e['tipo'] != 'borrado' else time.time()
        except OSError:
            mt = time.time()
        dia = dt.datetime.fromtimestamp(mt, BOGOTA).date().isoformat() if cronologico else ''
        x = grupos.setdefault((dia, g), {'grupo': g, 'dia': dia or None, 'mensaje': m, 'rutas': [], 'mtime_max': 0.0})
        x['rutas'].append(e['ruta'])
        x['mtime_max'] = max(x['mtime_max'], mt)
    orden_tema = {g: i for i, (g, _, _) in enumerate(GRUPOS)}
    clave = (lambda x: (x['mtime_max'], orden_tema[x['grupo']])) if cronologico else (lambda x: orden_tema[x['grupo']])
    lista = sorted(grupos.values(), key=clave)
    for x in lista:
        x['fecha_autor'] = dt.datetime.fromtimestamp(x['mtime_max'], BOGOTA).isoformat(timespec='seconds')
    return lista


def sha_herramienta() -> str:
    return sha256(Path(__file__).read_bytes())


# ---------------------------------------------------------------- órdenes

def cmd_auditar(a) -> int:
    t0 = time.monotonic()
    hist = info_historial()
    pend = estado_pendiente()
    seguidos, nuevos = archivos_repo()
    codigo = [r for r in seguidos + nuevos if Path(r).suffix.lower() in EXT_CODIGO]
    codigo_seguido = [r for r in seguidos if Path(r).suffix.lower() in EXT_CODIGO]
    por_area: dict[str, dict] = {}
    for e in pend:
        d = por_area.setdefault(area(e['ruta']), {'modificado': 0, 'sin_versionar': 0, 'borrado': 0, 'preparado': 0})
        d[e['tipo']] += 1
    candidatos = []
    for e in pend:
        if e['tipo'] != 'borrado':
            tam, datos = leer(e['ruta'])
            candidatos += [{'ruta': e['ruta'], **h} for h in revisar_contenido(e['ruta'], tam, datos)]
    rep = {
        'herramienta': 'herramientas/versionado.py', 'version': VERSION, 'sha256_herramienta': sha_herramienta(),
        'orden': 'auditar', 'utc': utc_ahora(), 'repositorio': REPO.name, 'git': git_txt('--version'), 'historial': hist,
        'pendiente': {'total': len(pend), 'por_tipo': {t: sum(e['tipo'] == t for e in pend)
                      for t in ('modificado', 'sin_versionar', 'borrado', 'preparado')}, 'por_area': por_area},
        'codigo': {'archivos_en_repositorio': len(codigo), 'versionados': len(codigo_seguido),
                   'sin_versionar': len(codigo) - len(codigo_seguido),
                   'nombres_con_vN': sum(bool(VERSIONADO_EN_NOMBRE.search(r)) for r in codigo)},
        'guardia_pendiente': {n: [c for c in candidatos if c['nivel'] == k]
                              for n, k in (('bloqueos', 'bloqueo'), ('avisos', 'aviso'), ('info', 'info'))},
        'gitignore_cubre': {r: bool(git_txt('check-ignore', '--no-index', r, ok=(0, 1)))
                            for r in ('privado/x.csv', 'a.parquet', 'b.csv', 'c.joblib')},
    }
    if not a.sin_historia:
        rep['historia'] = revisar_historia()
    if not a.sin_externos:
        raiz = Path(a.raiz_proyecto).resolve() if a.raiz_proyecto else REPO.parents[1]
        rep['codigo_externo'] = codigo_externo(raiz, a.externos or EXTERNOS, a.presupuesto)
    doc = REPO / 'docs' / 'VERSION_CONTROL.md'
    if doc.exists():
        documentadas = sorted(set(re.findall(r'`((?:parte|semana|entrega)[A-Za-z0-9._-]*)`', doc.read_text(encoding='utf-8'))))
        existentes = {e['nombre'] for e in hist.get('etiquetas', [])}
        rep['etiquetas_documentadas'] = {'documento': 'docs/VERSION_CONTROL.md', 'documentadas': documentadas,
                                         'ausentes': [t for t in documentadas if t not in existentes]}
    rep['plan_commits'] = [{'grupo': g['grupo'], 'mensaje': g['mensaje'], 'archivos': len(g['rutas'])}
                           for g in proponer_plan(pend)]
    rep['plan_cronologico'] = [{'dia': g['dia'], 'grupo': g['grupo'], 'archivos': len(g['rutas']), 'fecha_autor': g['fecha_autor']}
                               for g in proponer_plan(pend, cronologico=True)]
    rep['segundos'] = round(time.monotonic() - t0, 1)
    bloqueos = len(rep['guardia_pendiente']['bloqueos']) + len(rep.get('historia', {}).get('bloqueos', []))
    rep['veredicto'] = 'bloqueo' if bloqueos else 'sin_bloqueos'
    if a.salida != '-':
        out = (REPO / a.salida) if not Path(a.salida).is_absolute() else Path(a.salida)
        out.mkdir(parents=True, exist_ok=True)
        marca = rep['utc'].replace('-', '').replace(':', '')
        pj, pm = out / f'auditoria_{marca}.json', out / f'auditoria_{marca}.md'
        pj.write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        pm.write_text(resumen_md(rep), encoding='utf-8')
        print(f'Auditoría escrita en {pj.name} y {pm.name} ({out})')
    print(resumen_md(rep))
    return 1 if bloqueos else 0


def resumen_md(r: dict) -> str:
    h = r['historial']
    L = [f"# Auditoría del control de versiones, {r['utc']}", '',
         f"Repositorio `{r['repositorio']}`, {r['git']}. Herramienta `{r['herramienta']}` {r['version']} "
         f"(SHA-256 {r['sha256_herramienta'][:12]}…).", '']
    if h.get('head'):
        u, rem = h['ultimo_commit'], h.get('remoto')
        L += ['## Historial', '', '| Indicador | Valor |', '| --- | --- |',
              f"| Rama y commits | {h['rama']}, {h['commits']} commits |",
              f"| Último commit | {u['sha'][:7]} del {u['fecha']}: {u['mensaje']} |",
              f"| Días desde el último commit | {h.get('dias_desde_ultimo_commit', 'n/d')} |",
              f"| Commits sin subir, según la copia local del remoto | {rem['commits_sin_subir'] if rem else 'sin rama remota'} |",
              f"| Etiquetas | {', '.join(e['nombre'] for e in h['etiquetas']) or 'ninguna'} |",
              f"| Días con commits | {', '.join(f'{d} ({n})' for d, n in h['commits_por_dia'].items())} |", '']
    p, c = r['pendiente'], r['codigo']
    L += ['## Cambios sin registrar', '', f"{p['total']} archivos: " +
          ', '.join(f'{v} {k.replace("_", " ")}' for k, v in p['por_tipo'].items() if v) + '.', '',
          '| Área | Modificados | Sin versionar | Borrados |', '| --- | ---: | ---: | ---: |']
    for k, v in sorted(p['por_area'].items(), key=lambda kv: -sum(kv[1].values())):
        L.append(f"| {k} | {v['modificado'] + v['preparado']} | {v['sin_versionar']} | {v['borrado']} |")
    L += ['', f"Código dentro del repositorio: {c['archivos_en_repositorio']} archivos, {c['versionados']} en Git y "
          f"{c['sin_versionar']} sin versionar. Archivos de código con la versión en el nombre (_v2, _v3...): {c['nombres_con_vN']}.", '']
    if 'codigo_externo' in r:
        ce = r['codigo_externo']
        L += ['## Código del proyecto fuera del repositorio', '',
              '| Carpeta | Scripts | Distintos | Copia en Git | Copia sin versionar | Sin copia |',
              '| --- | ---: | ---: | ---: | ---: | ---: |']
        for f in ce['carpetas']:
            if f['existe']:
                L.append(f"| {f['carpeta']} | {f['archivos']} | {f['distintos']} | {f['copia_versionada']} | "
                         f"{f['copia_sin_versionar']} | {f['sin_copia']} |")
        if not ce['completo']:
            L.append(f"\nRecorrido parcial: se agotó el presupuesto de {ce['segundos']} s.")
        L.append('')
    g = r['guardia_pendiente']
    L += ['## Guardia', '', f"Sobre lo pendiente: {len(g['bloqueos'])} bloqueos, {len(g['avisos'])} avisos y "
          f"{len(g['info'])} notas informativas."]
    for x in (g['bloqueos'] + g['avisos'])[:30]:
        L.append(f"- {x['nivel']}: `{x['ruta']}` ({x['regla']}: {x['detalle']})")
    if 'historia' in r:
        hh = r['historia']
        L += ['', f"Historia completa: {hh['blobs']} blobs revisados, {len(hh['bloqueos'])} bloqueos y {len(hh['avisos'])} avisos."]
        for x in (hh['bloqueos'] + hh['avisos'])[:20]:
            L.append(f"- {x['nivel']}: `{x['ruta']}` ({x['regla']}: {x['detalle']})")
    if 'etiquetas_documentadas' in r:
        ed = r['etiquetas_documentadas']
        L += ['', f"Etiquetas citadas en {ed['documento']}: {len(ed['documentadas'])}; ausentes en el repositorio: "
              f"{', '.join(ed['ausentes']) or 'ninguna'}."]
    L += ['', '## Commits temáticos propuestos', '', '| Tema | Archivos | Mensaje |', '| --- | ---: | --- |']
    for x in r['plan_commits']:
        L.append(f"| {x['grupo']} | {x['archivos']} | {x['mensaje']} |")
    if r.get('plan_cronologico'):
        dias: dict[str, list] = {}
        for x in r['plan_cronologico']:
            dias.setdefault(x['dia'], []).append(x)
        L += ['', f"En orden cronológico serían {len(r['plan_cronologico'])} commits:", '',
              '| Día (Bogotá) | Commits | Archivos | Temas |', '| --- | ---: | ---: | --- |']
        for d, xs in dias.items():
            L.append(f"| {d} | {len(xs)} | {sum(x['archivos'] for x in xs)} | {', '.join(x['grupo'] for x in xs)} |")
    L += ['', f"Veredicto: {r['veredicto'].replace('_', ' ')}. Duración {r['segundos']} s.", '']
    return '\n'.join(L)


def cmd_guardia(a) -> int:
    resultados = []
    if a.pendiente:
        rutas = [e['ruta'] for e in estado_pendiente() if e['tipo'] != 'borrado']
        fuente = 'árbol de trabajo'
        for ruta in rutas:
            tam, datos = leer(ruta)
            resultados += [(ruta, h) for h in revisar_contenido(ruta, tam, datos)]
    else:
        fuente = 'preparado (git add)'
        rutas = lista_z(git('diff', '--cached', '--name-only', '-z', '--diff-filter=ACMRT'))
        indice = {}
        for e in lista_z(git('ls-files', '-s', '-z')):
            meta, ruta = e.split('\t', 1)
            modo, sha, _ = meta.split()
            indice[ruta] = (modo, sha)
        shas = [indice[r][1] for r in rutas if r in indice and indice[r][0] != '160000']
        tam, datos = leer_blobs(shas)
        for ruta in rutas:
            modo, sha = indice.get(ruta, ('', ''))
            if modo == '160000':
                resultados.append((ruta, {'nivel': 'bloqueo', 'regla': 'submódulo', 'detalle': 'el repositorio no usa submódulos'}))
            elif sha not in tam:
                resultados.append((ruta, {'nivel': 'bloqueo', 'regla': 'no legible', 'detalle': 'no se pudo leer el contenido preparado'}))
            else:
                resultados += [(ruta, h) for h in revisar_contenido(ruta, tam[sha], datos.get(sha))]
    bloqueos = [(r, h) for r, h in resultados if h['nivel'] == 'bloqueo']
    avisos = [(r, h) for r, h in resultados if h['nivel'] == 'aviso']
    for ruta, h in avisos:
        print(f'aviso   {ruta}: {h["regla"]} ({h["detalle"]})')
    for ruta, h in bloqueos:
        print(f'BLOQUEO {ruta}: {h["regla"]} ({h["detalle"]})')
    print(f'Guardia {VERSION} sobre {len(rutas)} archivos del {fuente}: {len(bloqueos)} bloqueos, {len(avisos)} avisos.')
    if bloqueos:
        print('Quita esos archivos del commit (git restore --staged <ruta>) o corrige .gitignore. '
              'Las reglas del concurso prohíben redistribuir los datos.')
    return 1 if bloqueos else 0


def sello_version(rutas: list[str] | None = None) -> dict:
    """Identifica la versión del código que produjo un resultado. Para copiar en recibos.

    Las rutas se interpretan desde la carpeta actual. Una ruta está limpia si existe, no está ignorada,
    tiene al menos un archivo en Git y no tiene cambios ni archivos nuevos sin commit. Solo lee: no
    refresca el índice, de modo que puede correr en una máquina que no puede borrar los bloqueos de Git."""
    try:
        head = git_txt('rev-parse', 'HEAD')
    except RuntimeError:
        head = None
    problemas, rels = [], []
    for r in rutas or []:
        p = Path(r).resolve()
        if p != REPO and REPO not in p.parents:
            problemas.append(f'{r}: fuera del repositorio')
            continue
        rel = p.relative_to(REPO).as_posix() if p != REPO else '.'
        rels.append(rel)
        if not p.exists():
            problemas.append(f'{rel}: no existe')
        elif rel != '.' and git_txt('check-ignore', '--no-index', rel, ok=(0, 1)):
            problemas.append(f'{rel}: está ignorada por .gitignore, no puede estar en Git')
        elif not git('ls-files', '-z', '--', rel):
            problemas.append(f'{rel}: ningún archivo en Git')
    estado = git_txt('status', '--porcelain=v1', '-uall', *(['--', *rels] if rels else []))
    lineas = [l for l in estado.split('\n') if l]
    limpio = not problemas and not lineas and head is not None
    return {
        'repositorio': 'iaa-hackathon-2026', 'commit': head,
        'rama': git_txt('rev-parse', '--abbrev-ref', 'HEAD') if head else None,
        'etiqueta_cercana': git_txt('describe', '--tags', '--always', ok=(0, 128)) if head else None,
        'limpio': limpio, 'cambios_sin_commit': len(lineas), 'problemas': problemas,
        'rutas_comprobadas': rels or 'todo el repositorio', 'ejemplos': lineas[:5], 'utc': utc_ahora(),
        'herramienta': f'versionado.py {VERSION}',
    }


def cmd_sello(a) -> int:
    s = sello_version(a.rutas or None)
    print(json.dumps(s, ensure_ascii=False, indent=1))
    if a.exigir_limpio and not s['limpio']:
        sys.stderr.write('El código de esas rutas no está registrado tal cual en Git: haz el commit antes de producir resultados.\n')
        return 1
    return 0


def cmd_vigia(a) -> int:
    ahora = time.time()
    pend = estado_pendiente()
    motivos, viejos = [], []
    for e in pend:
        if e['tipo'] == 'borrado' or Path(e['ruta']).suffix.lower() not in EXT_CODIGO:
            continue
        try:
            horas = (ahora - (REPO / e['ruta']).stat().st_mtime) / 3600
        except OSError:
            continue
        if horas >= a.horas_codigo:
            viejos.append((e['ruta'], round(horas, 1)))
    if viejos:
        motivos.append({'motivo': 'código sin registrar',
                        'detalle': f'{len(viejos)} archivos de código con más de {a.horas_codigo:g} h sin commit',
                        'ejemplos': [r for r, _ in sorted(viejos, key=lambda x: -x[1])[:5]]})
    evid = [e['ruta'] for e in pend if EVIDENCIA_CLAVE.search(e['ruta'])]
    if evid:
        motivos.append({'motivo': 'evidencia de envío o decisión sin registrar', 'detalle': f'{len(evid)} archivos', 'ejemplos': evid[:5]})
    if len(pend) > a.max_pendientes:
        motivos.append({'motivo': 'muchos archivos pendientes', 'detalle': f'{len(pend)} > {a.max_pendientes}', 'ejemplos': []})
    hist = info_historial()
    rem = hist.get('remoto')
    if rem and rem['commits_sin_subir'] and hist.get('dias_desde_ultimo_commit', 0) * 24 >= a.horas_push:
        motivos.append({'motivo': 'commits sin subir',
                        'detalle': f"{rem['commits_sin_subir']} commits; el último tiene más de {a.horas_push:g} h", 'ejemplos': []})
    bloqueos = []
    for e in pend:
        if e['tipo'] != 'borrado':
            tam, datos = leer(e['ruta'])
            bloqueos += [{'ruta': e['ruta'], **h} for h in revisar_contenido(e['ruta'], tam, datos) if h['nivel'] == 'bloqueo']
    codigo = 1 if bloqueos else 3 if motivos else 0
    res = {'herramienta': f'versionado.py {VERSION}', 'orden': 'vigia', 'utc': utc_ahora(), 'pendientes': len(pend),
           'motivos': motivos, 'bloqueos_guardia': bloqueos[:20],
           'veredicto': {0: 'sin cambios importantes', 3: 'registrar ahora', 1: 'bloqueo de la guardia'}[codigo],
           'umbrales': {'horas_codigo': a.horas_codigo, 'max_pendientes': a.max_pendientes, 'horas_push': a.horas_push}}
    if a.registrar:
        out = REPO / 'registro' / 'versionado' / 'vigia'
        out.mkdir(parents=True, exist_ok=True)
        (out / f"vigia_{res['utc'].replace('-', '').replace(':', '')}.json").write_text(
            json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return codigo


PS1 = '''\
# Aplica el plan de commits que genero herramientas/versionado.py {version} el {utc}.
# Cada commit lleva como fecha de autor la ultima modificacion del archivo mas reciente del grupo y como
# fecha de commit la real del momento en que se aplica. No reescribe ni borra commits existentes.
# Uso:  powershell -ExecutionPolicy Bypass -File "<esta carpeta>\\aplicar_plan.ps1" [-Simular] [-Subir]
param([switch]$Simular, [switch]$Subir)
$ErrorActionPreference = 'Stop'
$plan = $PSScriptRoot
$repo = (git -C $plan rev-parse --show-toplevel).Trim()
Set-Location $repo
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {{ throw 'Hay cambios ya preparados en el indice. Vacialo con: git restore --staged .' }}
$hook = (git config core.hooksPath)
if ($hook -ne 'herramientas/git_hooks') {{ Write-Warning 'El hook de la guardia no esta activo: git config core.hooksPath herramientas/git_hooks' }}
$grupos = @(
{grupos}
)
$hechos = @()
foreach ($g in $grupos) {{
  $rutas = Join-Path $plan ($g.n + '.rutas')
  $msg = Join-Path $plan ($g.n + '.msg')
  Write-Host ("== {{0}}  fecha de autor {{1}}  archivos {{2}}" -f $g.n, $g.fecha, $g.archivos)
  if ($Simular) {{ continue }}
  git --literal-pathspecs add --pathspec-from-file="$rutas" --pathspec-file-nul
  if ($LASTEXITCODE -ne 0) {{ throw ("git add fallo en " + $g.n) }}
  if (Select-String -Path $rutas -SimpleMatch 'herramientas/git_hooks/pre-commit' -Quiet) {{
    git update-index --chmod=+x herramientas/git_hooks/pre-commit
  }}
  if ($g.fecha) {{ $env:GIT_AUTHOR_DATE = $g.fecha }}
  try {{ git commit -F "$msg" }} finally {{ Remove-Item Env:GIT_AUTHOR_DATE -ErrorAction SilentlyContinue }}
  if ($LASTEXITCODE -ne 0) {{ throw ("git commit fallo en " + $g.n + "; revisa la guardia y el indice (git status)") }}
  $hechos += [pscustomobject]@{{ grupo = $g.n; tema = $g.tema; fecha_autor = $g.fecha; commit = (git rev-parse HEAD).Trim() }}
}}
if ($Simular) {{ return }}
$hechos | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $plan 'aplicado.json')
{etiquetas}git log --format='%h  autor %ad  commit %cd  %s' --date=short -n ($hechos.Count + 1)
if ($Subir) {{
  git fetch origin
  git push origin HEAD --follow-tags
}} else {{
  Write-Host 'Revisa el historial y sube con: git fetch origin; git push origin HEAD --follow-tags'
}}
'''


def cmd_plan(a) -> int:
    plan = proponer_plan(estado_pendiente(), cronologico=a.cronologico)
    hoy = dt.datetime.now(BOGOTA).date().isoformat()
    tipo = 'cronológico (un commit por día y tema)' if a.cronologico else 'temático'
    print(f'Plan {tipo} con {len(plan)} commits. Revisar cada grupo con git status y git diff antes de aplicarlo.\n')
    for i, g in enumerate(plan, 1):
        cab = f'{i:02d}. {g["dia"]} {g["grupo"]}' if g['dia'] else f'{i:02d}. {g["grupo"]}'
        print(f'{cab} ({len(g["rutas"])} archivos, última modificación {g["fecha_autor"]})\n    {g["mensaje"]}')
        for r in g['rutas'][: a.max_rutas]:
            print(f'      {r}')
        if len(g['rutas']) > a.max_rutas:
            print(f'      ... y {len(g["rutas"]) - a.max_rutas} más')
    if a.json:
        Path(a.json).write_text(json.dumps({'utc': utc_ahora(), 'cronologico': a.cronologico, 'plan': plan},
                                           ensure_ascii=False, indent=1), encoding='utf-8')
    if not a.carpeta:
        return 0
    out = (REPO / a.carpeta) if not Path(a.carpeta).is_absolute() else Path(a.carpeta)
    if out.exists() and any(out.iterdir()):
        sys.stderr.write(f'{out} ya tiene archivos; elige una carpeta nueva (no se sobrescribe).\n')
        return 2
    out.mkdir(parents=True, exist_ok=True)
    filas = []
    for i, g in enumerate(plan, 1):
        n = f'{i:02d}_{g["dia"] + "_" if g["dia"] else ""}{g["grupo"]}'
        (out / f'{n}.rutas').write_bytes(b'\0'.join(r.encode('utf-8') for r in g['rutas']) + b'\0')
        titulo = f'{g["mensaje"]} ({g["dia"]})' if g['dia'] else g['mensaje']
        if a.cronologico:
            cuantos = 'el archivo' if len(g['rutas']) == 1 else f'los {len(g["rutas"])} archivos'
            detalle = (f'Reconstrucción del historial hecha el {hoy}: este commit reúne {cuantos} '
                       f'del tema cuya última modificación es del {g["dia"]} (hora de Bogotá), en su versión final. '
                       'La fecha de autor es la de la modificación más reciente del grupo; la fecha de commit es la '
                       'real de la reconstrucción. Cada recibo de registro/ conserva su hora UTC y sus SHA-256.')
        else:
            detalle = (f'{len(g["rutas"])} archivos registrados en la puesta al día del historial; '
                       'cada recibo de registro/ conserva su hora UTC y sus SHA-256 originales.')
        cuerpo = (f'{titulo}\n\n{detalle}\n\nRefs: {a.refs or "docs/CONTROL_DE_VERSIONES.md"}\n'
                  f'Asistido-por: Codex | Claude\nRevision-humana: {a.revision}\n'
                  + (f'Reconstruido: {hoy}\n' if a.cronologico else ''))
        (out / f'{n}.msg').write_text(cuerpo, encoding='utf-8')
        fecha = g['fecha_autor'] if a.cronologico else ''
        filas.append(f"  @{{ n = '{n}'; tema = '{g['grupo']}'; fecha = '{fecha}'; archivos = {len(g['rutas'])} }}")
    etiquetas = ''
    if a.cronologico:
        p1 = [f"{i:02d}_{g['dia']}_{g['grupo']}" for i, g in enumerate(plan, 1) if g['grupo'].startswith('parte1')]
        if p1:
            etiquetas += (f"$s41 = ($hechos | Where-Object {{ $_.grupo -eq '{p1[-1]}' }}).commit\n"
                          f"git tag -a parte1-entrega-final-S41 $s41 -m \"Entrega final de la parte 1 (S41, CIE-D103). "
                          f"Etiquetada el {hoy} en la reconstruccion del historial, sobre el ultimo commit con archivos de la parte 1.\"\n")
        if git('rev-parse', '-q', '--verify', '0ade351^{commit}', ok=(0, 1)).strip():
            etiquetas += (f"git tag -a parte1-mezcla-por-peligro 0ade351 -m \"Mezcla por peligro (S30) declarada modelo "
                          f"definitivo, D99, 20 de octubre. Etiquetada el {hoy}.\"\n")
    ps1 = PS1.format(version=VERSION, utc=utc_ahora(), grupos=',\n'.join(filas), etiquetas=etiquetas)
    # PowerShell 5.1 lee como ANSI los scripts sin BOM: se escribe con BOM y finales CRLF.
    (out / 'aplicar_plan.ps1').write_bytes(b'\xef\xbb\xbf' + ps1.replace('\n', '\r\n').encode('utf-8'))
    (out / 'plan.json').write_text(json.dumps({'herramienta': f'versionado.py {VERSION}', 'utc': utc_ahora(),
                                               'cronologico': a.cronologico, 'grupos': plan}, ensure_ascii=False, indent=1),
                                   encoding='utf-8')
    print(f'\nPlan escrito en {out}: {len(plan)} pares .rutas/.msg, plan.json y aplicar_plan.ps1.')
    print('Probar primero:  powershell -ExecutionPolicy Bypass -File "<carpeta>\\aplicar_plan.ps1" -Simular')
    return 0


def cmd_empaquetar(a) -> int:
    commit = git_txt('rev-parse', f'{a.ref}^{{commit}}')
    nombre = re.sub(r'[^A-Za-z0-9._-]', '_', a.ref)
    out = (REPO / a.salida) if not Path(a.salida).is_absolute() else Path(a.salida)
    out.mkdir(parents=True, exist_ok=True)
    bundle, zipf = out / f'iaa-hackathon-2026_{nombre}.bundle', out / f'iaa-hackathon-2026_{nombre}_codigo.zip'
    for f in (bundle, zipf):
        if f.exists():
            sys.stderr.write(f'Ya existe {f}; elige otra --salida (no se sobrescribe).\n')
            return 2
    git('bundle', 'create', str(bundle), '--all')
    verif = subprocess.run(['git', '-C', str(REPO), 'bundle', 'verify', str(bundle)], capture_output=True)
    git('archive', '--format=zip', '--prefix=iaa-hackathon-2026/', '-o', str(zipf), commit)
    hallazgos = []
    with zipfile.ZipFile(zipf) as z:
        nombres = [i for i in z.infolist() if not i.is_dir()]
        for i in nombres:
            ruta = i.filename.split('/', 1)[1]
            datos = z.read(i) if i.file_size <= TAM_BLOQUEO else None
            hallazgos += [{'ruta': ruta, **h} for h in revisar_contenido(ruta, i.file_size, datos) if h['nivel'] == 'bloqueo']
    man = {
        'herramienta': f'versionado.py {VERSION}', 'sha256_herramienta': sha_herramienta(), 'utc': utc_ahora(),
        'ref': a.ref, 'commit': commit, 'commits_en_historia': int(git_txt('rev-list', '--count', '--all')),
        'etiquetas': [t for t in git_txt('tag', '-l').split('\n') if t],
        'bundle': {'archivo': bundle.name, 'bytes': bundle.stat().st_size, 'sha256': sha256(bundle.read_bytes()),
                   'verificado': verif.returncode == 0,
                   'salida_verify': (verif.stdout + verif.stderr).decode('utf-8', 'replace').strip().split('\n')[-1]
                   .replace(str(bundle), bundle.name)},
        'zip': {'archivo': zipf.name, 'bytes': zipf.stat().st_size, 'sha256': sha256(zipf.read_bytes()),
                'archivos': len(nombres), 'bloqueos': hallazgos},
        'como_usar': [f'git clone {bundle.name} iaa-hackathon-2026   # historia completa',
                      'git -C iaa-hackathon-2026 log --oneline --decorate',
                      'el ZIP contiene el árbol del commit indicado, sin historia, para leerlo sin Git'],
    }
    (out / f'MANIFIESTO_{nombre}.json').write_text(json.dumps(man, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(man, ensure_ascii=False, indent=1))
    return 0 if man['bundle']['verificado'] and not hallazgos else 1


EXT_INCORPORAR = EXT_CODIGO | {'.md', '.json', '.txt', '.yaml', '.yml', '.toml', '.cfg', '.ini'}
MAX_INCORPORAR = 1024 * 1024


def cmd_incorporar(a) -> int:
    if a.actualizar_todo:
        raiz, codigo = REPO.parents[1], 0
        for man in sorted((REPO / 'src').rglob('ORIGEN.json')):
            m = json.loads(man.read_text(encoding='utf-8'))
            sub = argparse.Namespace(origen=str(raiz / m['origen']), destino=man.parent.relative_to(REPO).as_posix(),
                                     simular=a.simular, actualizar=True, actualizar_todo=False, detalle=False)
            print(f"== {sub.destino} <- {m['origen']}")
            codigo = max(codigo, cmd_incorporar(sub))
        return codigo
    if not (a.origen and a.destino):
        sys.stderr.write('incorporar necesita --origen y --destino, o --actualizar-todo.\n')
        return 2
    origen = Path(a.origen).resolve()
    destino = (REPO / a.destino).resolve()
    if REPO not in destino.parents:
        sys.stderr.write('El destino debe estar dentro del repositorio.\n')
        return 2
    if not origen.is_dir():
        sys.stderr.write(f'No existe la carpeta de origen {origen}.\n')
        return 2
    raiz = REPO.parents[1]
    origen_txt = origen.relative_to(raiz).as_posix() if raiz in origen.parents else str(origen)
    destino_txt = destino.relative_to(REPO).as_posix()
    man_previo = None
    if (destino / 'ORIGEN.json').exists():
        if not a.actualizar:
            sys.stderr.write(f'{a.destino} ya tiene ORIGEN.json; para traer los cambios de la misma carpeta usa --actualizar.\n')
            return 2
        man_previo = json.loads((destino / 'ORIGEN.json').read_text(encoding='utf-8'))
        if man_previo.get('origen') != origen_txt:
            sys.stderr.write(f"ORIGEN.json de {a.destino} apunta a {man_previo.get('origen')}, no a {origen_txt}.\n")
            return 2
    elif a.actualizar:
        sys.stderr.write(f'{a.destino} no tiene ORIGEN.json: la primera incorporación se hace sin --actualizar.\n')
        return 2
    copiar, omitidos, vistos = [], [], {}
    en_repo: dict[str, str] = {}
    seguidos, nuevos = archivos_repo()
    for r in seguidos + nuevos:
        if Path(r).suffix.lower() in EXT_INCORPORAR and not r.startswith(destino_txt + '/'):
            try:
                en_repo.setdefault(sha_normalizado((REPO / r).read_bytes()), r)
            except OSError:
                pass
    for d, subd, fich in os.walk(origen):
        subd[:] = sorted(x for x in subd if x not in OMITIR_DIRS and not x.startswith('.'))
        for f in sorted(fich):
            p = Path(d) / f
            rel = p.relative_to(origen).as_posix()
            ext = p.suffix.lower()
            if rel == 'ORIGEN.json':
                omitidos.append({'ruta': rel, 'motivo': 'nombre reservado para el manifiesto de la incorporación'})
                continue
            if ext not in EXT_INCORPORAR:
                omitidos.append({'ruta': rel, 'motivo': f'extensión {ext or "(sin)"} fuera de código y documentación'})
                continue
            st = p.stat()
            if st.st_size > MAX_INCORPORAR:
                omitidos.append({'ruta': rel, 'motivo': f'{st.st_size / 1e6:.1f} MB > {MAX_INCORPORAR / 1e6:.0f} MB'})
                continue
            datos = p.read_bytes()
            if sha_normalizado(datos) in en_repo:
                omitidos.append({'ruta': rel, 'motivo': f'ya está en el repositorio como {en_repo[sha_normalizado(datos)]}'})
                continue
            if sha_normalizado(datos) in vistos:
                omitidos.append({'ruta': rel, 'motivo': f'copia idéntica de {vistos[sha_normalizado(datos)]} en el mismo origen'})
                continue
            ruta_repo = (destino / rel).relative_to(REPO).as_posix()
            bloq = [h for h in revisar_contenido(ruta_repo, st.st_size, datos) if h['nivel'] in ('bloqueo', 'aviso')]
            if bloq:
                omitidos.append({'ruta': rel, 'motivo': '; '.join(f"{h['regla']}: {h['detalle']}" for h in bloq)})
                continue
            q = REPO / ruta_repo
            estado = 'nuevo' if not q.exists() else 'sin_cambios' if sha256(q.read_bytes()) == sha256(datos) else 'actualizado'
            copiar.append({'origen': rel, 'destino': ruta_repo, 'bytes': st.st_size, 'sha256': sha256(datos), 'estado': estado,
                           'modificado_utc': dt.datetime.fromtimestamp(st.st_mtime, dt.timezone.utc).isoformat(timespec='seconds'),
                           'duplicado_de': vistos.get(sha_normalizado(datos))})
            vistos.setdefault(sha_normalizado(datos), rel)
    cuenta = {k: sum(c['estado'] == k for c in copiar) for k in ('nuevo', 'actualizado', 'sin_cambios')}
    resumen = {'herramienta': f'versionado.py {VERSION}', 'orden': 'incorporar', 'utc': utc_ahora(),
               'origen': origen_txt, 'destino': destino_txt, 'simulado': a.simular, 'actualizacion': bool(man_previo),
               'copiados': len(copiar), 'bytes': sum(c['bytes'] for c in copiar), **cuenta,
               'duplicados_internos': sum(bool(c['duplicado_de']) for c in copiar),
               'omitidos': len(omitidos), 'por_extension': {}}
    for c in copiar:
        e = Path(c['destino']).suffix.lower()
        resumen['por_extension'][e] = resumen['por_extension'].get(e, 0) + 1
    if not man_previo:
        existentes = [c['destino'] for c in copiar if c['estado'] != 'nuevo']
        if existentes:
            resumen['conflictos'] = existentes[:20]
            print(json.dumps(resumen, ensure_ascii=False, indent=1))
            sys.stderr.write(f'{len(existentes)} archivos ya existen en el destino; no se sobrescribe nada.\n')
            return 2
    if not a.simular:
        for c in copiar:
            if c['estado'] == 'sin_cambios':
                continue
            q, src = REPO / c['destino'], origen / c['origen']
            q.parent.mkdir(parents=True, exist_ok=True)
            q.write_bytes(src.read_bytes())
            st = src.stat()
            os.utime(q, (st.st_atime, st.st_mtime))  # conserva la fecha para el plan cronológico
            if sha256(q.read_bytes()) != c['sha256']:
                raise RuntimeError(f"La copia de {c['origen']} no coincide con su origen.")
        nota = ('Copia sin cambios del código tal como se ejecutó, con su fecha de modificación; '
                'la carpeta de origen sigue siendo la de trabajo. Las versiones anteriores de un archivo actualizado '
                'quedan en los commits anteriores.')
        if man_previo:
            man = dict(man_previo)
            prev = {x['destino']: x for x in man_previo.get('archivos', [])}
            prev.update({c['destino']: c for c in copiar})
            man['archivos'] = sorted(prev.values(), key=lambda x: x['destino'])
            man['omitidos_detalle'] = omitidos
            man.setdefault('actualizaciones', []).append({k: resumen[k] for k in ('utc', 'nuevo', 'actualizado', 'sin_cambios', 'omitidos')})
            man['nota'] = nota
        else:
            man = dict(resumen, archivos=copiar, omitidos_detalle=omitidos, nota=nota)
        destino.mkdir(parents=True, exist_ok=True)
        (destino / 'ORIGEN.json').write_text(json.dumps(man, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(resumen, ensure_ascii=False, indent=1))
    if a.detalle:
        for o in omitidos[:60]:
            print(f"omitido  {o['ruta']}: {o['motivo']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest='orden', required=True)
    x = s.add_parser('auditar')
    x.add_argument('--salida', default='registro/versionado', help="carpeta del informe, o '-' para solo imprimir")
    x.add_argument('--raiz-proyecto', help='raíz del espacio de trabajo (por defecto, dos niveles sobre el repositorio)')
    x.add_argument('--externos', nargs='*', help='carpetas, relativas a la raíz, donde buscar código fuera del repositorio')
    x.add_argument('--presupuesto', type=float, default=90, help='segundos máximos para recorrer carpetas externas')
    x.add_argument('--sin-externos', action='store_true')
    x.add_argument('--sin-historia', action='store_true')
    x = s.add_parser('vigia')
    x.add_argument('--horas-codigo', type=float, default=3, help='horas que puede estar un archivo de código sin commit')
    x.add_argument('--max-pendientes', type=int, default=40, help='archivos pendientes a partir de los que conviene registrar')
    x.add_argument('--horas-push', type=float, default=24, help='horas que pueden estar commits sin subir')
    x.add_argument('--registrar', action='store_true', help='guarda el resultado en registro/versionado/vigia/')
    x = s.add_parser('guardia')
    x.add_argument('--pendiente', action='store_true', help='revisar todo lo pendiente, no solo lo preparado')
    x = s.add_parser('sello')
    x.add_argument('rutas', nargs='*', help='rutas del código que produjo el resultado, desde la carpeta actual')
    x.add_argument('--exigir-limpio', action='store_true')
    x = s.add_parser('plan')
    x.add_argument('--cronologico', action='store_true', help='un commit por día y tema, con la fecha de autor real')
    x.add_argument('--max-rutas', type=int, default=8)
    x.add_argument('--json')
    x.add_argument('--carpeta', help='carpeta nueva donde dejar .rutas, .msg, plan.json y aplicar_plan.ps1')
    x.add_argument('--refs', help='identificadores del foro o decisiones para la línea Refs: del mensaje')
    x.add_argument('--revision', default='pendiente', help='quién revisó el contenido (por defecto, pendiente)')
    x = s.add_parser('empaquetar')
    x.add_argument('--ref', required=True, help='etiqueta o commit que se entrega')
    x.add_argument('--salida', default='privado/entrega_codigo')
    x = s.add_parser('incorporar')
    x.add_argument('--origen', help='carpeta de trabajo fuera del repositorio')
    x.add_argument('--destino', help='carpeta nueva del repositorio, por ejemplo src/semana2/lineas/<carpeta>')
    x.add_argument('--actualizar-todo', action='store_true', help='actualiza todas las incorporaciones con ORIGEN.json bajo src/')
    x.add_argument('--simular', action='store_true')
    x.add_argument('--actualizar', action='store_true', help='trae los archivos nuevos o cambiados de un origen ya incorporado')
    x.add_argument('--detalle', action='store_true')
    a = p.parse_args(argv)
    if not (REPO / '.git').exists():
        sys.stderr.write(f'{REPO} no es un repositorio Git.\n')
        return 2
    try:
        return {'auditar': cmd_auditar, 'vigia': cmd_vigia, 'guardia': cmd_guardia, 'sello': cmd_sello,
                'plan': cmd_plan, 'empaquetar': cmd_empaquetar, 'incorporar': cmd_incorporar}[a.orden](a)
    except RuntimeError as e:
        sys.stderr.write(f'versionado.py {a.orden}: {e}\n')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
