"""Resolve official notebook inputs and validate them without training models."""
from pathlib import Path
import hashlib
import json
import os

LINES = ('motor', 'buildings', 'contents')
BASE_FILES = ['addresses.parquet', 'claims.parquet', 'customers.parquet',
              'weather.parquet', 'sample_submission.parquet'] + [
    f'{prefix}_{line}.parquet' for prefix in ('policies', 'test') for line in LINES]
INPUT_CONTRACT = {}
NOTEBOOK_WEEK = None
_RESOLVED_INPUTS = {}
_VERIFIED_INPUTS = {}
_VERIFIED_TEMPLATES = {}
_VARIABLES = {'public': 'IAA_W1_DATA', 'developed': 'IAA_W2_DEVELOPED',
              'emerging': 'IAA_W2_EMERGING'}
_ROUTE_KEYS = {'public': 'week_1_data', 'developed': 'week_2_developed_reference',
               'emerging': 'week_2_emerging_data'}


def _directory(value):
    return Path(value).expanduser().resolve()


def _missing(folder, required):
    return [name for name in required if not (folder / name).is_file()]


def _discover(root, required, market):
    """Search only an explicitly chosen data tree or the Kaggle input mount."""
    candidates = set()
    if not root.is_dir():
        return []
    for current, directories, filenames in os.walk(root, followlinks=False):
        folder = Path(current)
        if len(folder.relative_to(root).parts) >= 6:
            directories[:] = []
        else:
            directories[:] = [d for d in directories if not d.startswith('.')]
        if 'sample_submission.parquet' not in filenames or _missing(folder, required):
            continue
        # The emerging folder also contains the eleven base filenames.
        if market != 'emerging' and (folder / 'reference_policies.parquet').is_file():
            continue
        candidates.add(folder.resolve())
    return sorted(candidates, key=str)


def _project_folder(market):
    explicit = os.environ.get('IAA_PROJECT_ROOT', '')
    if explicit:
        configs = [_directory(explicit) / 'RUTAS_PROYECTO.json']
        if not configs[0].is_file():
            raise RuntimeError(f'IAA_PROJECT_ROOT has no RUTAS_PROYECTO.json: {configs[0]}')
    else:
        start = Path.cwd().resolve()
        configs = [p / 'RUTAS_PROYECTO.json' for p in (start, *start.parents)
                   if (p / 'RUTAS_PROYECTO.json').is_file()][:1]
    if not configs:
        return None
    config = configs[0]
    routes = json.loads(config.read_text(encoding='utf-8-sig'))
    value = routes.get(_ROUTE_KEYS[market])
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f'{config.name} lacks the data route {_ROUTE_KEYS[market]}')
    return (config.parent / value).resolve()


def find_market(market, required, override):
    """Resolve one market, never silently select between multiple candidates."""
    if market not in INPUT_CONTRACT or market not in _VARIABLES:
        raise RuntimeError(f'No frozen input contract for {market!r}')
    origin = _VARIABLES[market]
    if override:
        candidates = [_directory(override)]
    elif os.environ.get('IAA_DATA_ROOT'):
        origin = 'IAA_DATA_ROOT'
        candidates = _discover(_directory(os.environ['IAA_DATA_ROOT']), required, market)
    else:
        project = _project_folder(market)
        origin = 'RUTAS_PROYECTO.json' if project is not None else '/kaggle/input'
        candidates = [project] if project is not None else _discover(Path('/kaggle/input'), required, market)
    if len(candidates) != 1:
        raise RuntimeError(f'Expected one {market} directory via {origin}; found '
                           f'{[str(p) for p in candidates]}. Set {_VARIABLES[market]} '
                           'to the directory containing the required Parquet files.')
    folder = candidates[0]
    missing = _missing(folder, required)
    if missing:
        raise RuntimeError(f'Missing {market} files in {folder}: {", ".join(missing)}. '
                           f'Check {_VARIABLES[market]}. No fallback was selected.')
    if market != 'emerging' and (folder / 'reference_policies.parquet').is_file():
        raise RuntimeError(f'{folder} contains emerging-market reference policies; '
                           f'check {_VARIABLES[market]} instead of mixing markets.')
    _RESOLVED_INPUTS[str(folder)] = {'market': market, 'origin': origin}
    _VERIFIED_INPUTS.pop(market, None)
    _VERIFIED_TEMPLATES.pop(market, None)
    return folder


def inventory(folder, filenames):
    import pandas as pd
    import pyarrow.parquet as pq
    folder = _directory(folder)
    binding = _RESOLVED_INPUTS.get(str(folder))
    if binding is None:
        raise RuntimeError('Resolve this input with find_market before inventory.')
    market = binding['market']
    _VERIFIED_INPUTS.pop(market, None)
    _VERIFIED_TEMPLATES.pop(market, None)
    expected = INPUT_CONTRACT[market]
    if set(filenames) != set(expected):
        raise RuntimeError(f'File list does not match the frozen {market} contract')
    rows = []
    for name in filenames:
        path = folder / name
        before = path.stat()
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        actual = digest.hexdigest()
        if before.st_size != expected[name]['bytes'] or actual != expected[name]['sha256']:
            raise RuntimeError(f'Official-download fingerprint mismatch: {market}/{name}. '
                               'Check the input version; training has not started.')
        parquet = pq.ParquetFile(path)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError(f'Input changed while being checked: {path}')
        rows.append({'file': name, 'rows': parquet.metadata.num_rows,
                     'columns': len(parquet.schema_arrow), 'bytes': after.st_size,
                     'sha256': actual, 'matches_download': True,
                     'mtime_ns': after.st_mtime_ns})
    _VERIFIED_INPUTS[market] = {'directory': str(folder), 'origin': binding['origin'], 'files': rows}
    return pd.DataFrame([{k: v for k, v in row.items() if k != 'mtime_ns'} for row in rows])


def check_template(folder):
    import pandas as pd
    folder = _directory(folder)
    market = _RESOLVED_INPUTS[str(folder)]['market']
    _VERIFIED_TEMPLATES.pop(market, None)
    if market not in _VERIFIED_INPUTS:
        raise RuntimeError('Verify input fingerprints before checking the template.')
    sample = pd.read_parquet(folder / 'sample_submission.parquet')
    test = pd.concat([pd.read_parquet(folder / f'test_{line}.parquet', columns=['row_id'])
                      for line in LINES], ignore_index=True)
    if ('row_id' not in sample or not sample.row_id.notna().all()
            or not test.row_id.notna().all() or not test.row_id.is_unique
            or not sample.row_id.is_unique or not sample.row_id.equals(test.row_id)):
        raise RuntimeError(f'{market}: template and test identifiers/order do not agree')
    _VERIFIED_TEMPLATES[market] = len(sample)
    print(f'{market}: template matches test identifiers in order ({len(sample):,} rows)')
    return sample


def _safe_output_root(root):
    root = _directory(root)
    for binding in _RESOLVED_INPUTS:
        source = Path(binding)
        if root == source or source in root.parents:
            raise RuntimeError(f'Output directory is inside read-only input data: {root}')
    return root


def prepare_workspace(week):
    """Create a run only after all input contracts and templates have passed."""
    import tempfile
    import uuid
    from datetime import datetime, timezone
    if week not in (1, 2) or week != NOTEBOOK_WEEK:
        raise RuntimeError('Workspace week does not match the notebook input contract')
    required = {'public'} if week == 1 else {'developed', 'emerging'}
    if not required.issubset(_VERIFIED_INPUTS) or not required.issubset(_VERIFIED_TEMPLATES):
        raise RuntimeError('Run the input inventory and template cells before creating the workspace.')
    for market in required:
        for row in _VERIFIED_INPUTS[market]['files']:
            path = Path(_VERIFIED_INPUTS[market]['directory']) / row['file']
            stat = path.stat()
            if (stat.st_size, stat.st_mtime_ns) != (row['bytes'], row['mtime_ns']):
                raise RuntimeError(f'Input changed after validation: {market}/{row["file"]}')
    work_root = _safe_output_root(os.environ.get('IAA_NOTEBOOK_WORK') or tempfile.gettempdir())
    export_value = os.environ.get('IAA_NOTEBOOK_EXPORT', '')
    export_root = _safe_output_root(export_value) if export_value else (
        Path('/kaggle/working') if Path('/kaggle/working').is_dir() else None)
    run = work_root / ('iaa_week' + str(week) + '_' + uuid.uuid4().hex[:12])
    run.mkdir(parents=True, exist_ok=False)
    export = (export_root if export_root is not None else run) / (run.name + '_exports')
    export.mkdir(parents=True, exist_ok=False)
    receipt = {'utc': datetime.now(timezone.utc).isoformat(), 'week': week,
               'inputs': {m: _VERIFIED_INPUTS[m] for m in sorted(required)},
               'template_rows': {m: _VERIFIED_TEMPLATES[m] for m in sorted(required)},
               'training_started': False}
    (run / 'input_manifest.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('New run:', run)
    print('Final outputs:', export)
    return run, export


# END_NOTEBOOK_RUNTIME

def notebook_input_source(week):
    """Embed the runtime and only this week's aggregate input fingerprints."""
    root = Path(__file__).resolve().parents[1]
    contract = json.loads((root / 'registro/contrato_entradas_notebooks.json').read_text(encoding='utf-8'))
    roles = ['public'] if week == 1 else ['developed', 'emerging']
    if week not in (1, 2):
        raise ValueError('week must be 1 or 2')
    selected = {role: contract['markets'][role]['files'] for role in roles}
    source = Path(__file__).read_text(encoding='utf-8').split('# END_NOTEBOOK_RUNTIME')[0]
    return source + '\nNOTEBOOK_WEEK = ' + repr(week) + '\nINPUT_CONTRACT = ' + repr(selected) + '\n'


def apply_input_contract(notebook, week):
    """Update only startup cells; model and embedded source cells stay intact."""
    found = set()
    for cell in notebook['cells']:
        if cell['cell_type'] == 'markdown' and ''.join(cell['source']).startswith('## Attach the competition data'):
            variables = '`IAA_W1_DATA`' if week == 1 else '`IAA_W2_DEVELOPED` and `IAA_W2_EMERGING`'
            inputs = ('the eleven developed-market Parquet files from Part 1' if week == 1 else
                      'the eleven developed-market files and thirteen emerging-market files from Part 2')
            cell['source'] = (f'''## Attach the competition data

I use {inputs}. I resolve the folders in this order: explicit market variables ({variables}), an optional `IAA_DATA_ROOT`, the local workspace's `RUTAS_PROYECTO.json`, then attached data under `/kaggle/input`.

In my local project, I can open this notebook from the workspace without entering machine-specific paths. `IAA_PROJECT_ROOT` identifies that workspace when the kernel starts elsewhere. For another local checkout I set the market variables to the actual Parquet directories, or point `IAA_DATA_ROOT` to their common parent. In Kaggle I attach the corresponding competition; folder discovery stops if multiple candidates are possible.

Before training, I check every required file against the frozen sizes and SHA-256 fingerprints of my archived official downloads, then check the template's identifiers and order against the test files. Week 2 validates both markets. An incorrect path, missing file, mixed market or different fingerprint stops execution. These hashes identify the downloaded bytes; they are not represented as hashes published by Kaggle.

Only after these checks pass do I create the run folder. Its `input_manifest.json` records the resolved paths, input fingerprints and template counts. I keep inputs read-only and prevent output directories inside them.
''').splitlines(True)
            found.add('documentation')
        if cell['cell_type'] != 'code':
            continue
        text = ''.join(cell['source'])
        if text.startswith(('SOURCES[', 'DATAFILES[')):
            continue
        if 'def find_market(' in text:
            text = notebook_input_source(week)
            found.add('inputs')
        elif week == 2 and text.startswith('emerging_files = '):
            if 'developed_sample = check_template(developed)' not in text:
                text = text.replace('sample = check_template(emerging)',
                                    'developed_sample = check_template(developed)\nsample = check_template(emerging)')
            found.add('developed_template')
        elif 'REFERENCE = ' in text and ('import tempfile\n' in text or 'prepare_workspace(' in text):
            start = text.index('import tempfile\n') if 'import tempfile\n' in text else text.index('RUN, EXPORT = prepare_workspace(')
            end = text.index('SOURCES = {}', start) + len('SOURCES = {}')
            middle = 'RUN, EXPORT = prepare_workspace(' + str(week) + ')\n'
            if week == 1:
                middle += 'PACKAGE = RUN / "embedded_code"\nPACKAGE.mkdir()\n'
            text = text[:start] + middle + 'SOURCES = {}' + text[end:]
            text = text.replace('\nprint("New run:", RUN)', '')
            found.add('workspace')
        cell['source'] = text.splitlines(True)
    expected = {'inputs', 'workspace', 'documentation'} | ({'developed_template'} if week == 2 else set())
    if found != expected:
        raise RuntimeError(f'Notebook startup cells not found: {expected - found}')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Verify notebook data inputs without training.')
    parser.add_argument('--week', choices=('1', '2', 'both'), default='both')
    parser.add_argument('--project-root', help='Workspace containing RUTAS_PROYECTO.json')
    parser.add_argument('--data-root', help='Alternative root containing the official data directories')
    parser.add_argument('--receipt', help='Optional JSON receipt; keep it outside the input directories')
    args = parser.parse_args()
    if args.project_root:
        os.environ['IAA_PROJECT_ROOT'] = args.project_root
    if args.data_root:
        os.environ['IAA_DATA_ROOT'] = args.data_root
    summaries = []
    for week in ((1, 2) if args.week == 'both' else (int(args.week),)):
        namespace = {}
        exec(compile(notebook_input_source(week), '<notebook input runtime>', 'exec'), namespace)
        roles = ('public',) if week == 1 else ('developed', 'emerging')
        for market in roles:
            required = BASE_FILES + (['expenses.parquet', 'reference_policies.parquet']
                                     if market == 'emerging' else [])
            folder = namespace['find_market'](market, required, os.environ.get(_VARIABLES[market], ''))
            namespace['inventory'](folder, required)
            namespace['check_template'](folder)
            summary = {'week': week, 'market': market, 'directory': str(folder),
                       'files_verified': len(required), 'template_rows': namespace['_VERIFIED_TEMPLATES'][market],
                       'all_fingerprints_match': True, 'training_started': False}
            summaries.append(summary)
            print(f'Week {week}, {market}: {len(required)} input files verified')
        if args.receipt:
            namespace['_safe_output_root'](Path(args.receipt).parent)
    result = {'ok': True, 'checks': summaries, 'training_started': False}
    if args.receipt:
        path = _directory(args.receipt)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
