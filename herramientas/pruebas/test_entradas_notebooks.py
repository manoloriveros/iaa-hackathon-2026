"""Behavioral checks for input selection, integrity and read-only inputs."""
from pathlib import Path
from unittest.mock import patch
import hashlib
import json
import os
import runpy
import sys
import tempfile
import unittest

import pyarrow as pa
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
RUNTIME = (REPO / 'herramientas/entradas_notebooks.py').read_text(encoding='utf-8').split('# END_NOTEBOOK_RUNTIME')[0]


class InputContractTests(unittest.TestCase):
    def setUp(self):
        parent = REPO / 'privado/entradas_notebooks_20261029/pruebas'
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.root = Path(self.temp.name).resolve()
        self.allowed_root = parent.resolve()
        self.ns = {}
        exec(compile(RUNTIME, '<test notebook runtime>', 'exec'), self.ns)
        self.data = self.root / 'official'
        self.data.mkdir()
        for name in self.ns['BASE_FILES']:
            ids = ['motor', 'buildings', 'contents'] if name == 'sample_submission.parquet' else [
                name.removeprefix('test_').removesuffix('.parquet') if name.startswith('test_') else 'fixture']
            pq.write_table(pa.table({'row_id': ids}), self.data / name)
        self._refresh_contract()
        self.ns['NOTEBOOK_WEEK'] = 1
        self.env = patch.dict(os.environ, {k: '' for k in [
            'IAA_DATA_ROOT', 'IAA_PROJECT_ROOT', 'IAA_NOTEBOOK_WORK', 'IAA_NOTEBOOK_EXPORT',
            'IAA_W1_DATA', 'IAA_W2_DEVELOPED', 'IAA_W2_EMERGING']})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        assert self.allowed_root in self.root.parents
        self.temp.cleanup()

    def _refresh_contract(self):
        files = {p.name: {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in self.data.glob('*.parquet')}
        self.ns['INPUT_CONTRACT'] = {'public': files, 'developed': files, 'emerging': files}

    def _resolve(self):
        return self.ns['find_market']('public', self.ns['BASE_FILES'], str(self.data))

    def _verify(self):
        folder = self._resolve()
        self.ns['inventory'](folder, self.ns['BASE_FILES'])
        self.ns['check_template'](folder)

    def test_explicit_folder_has_priority_over_project_config(self):
        os.environ['IAA_PROJECT_ROOT'] = str(self.root / 'nonexistent')
        self.assertEqual(self._resolve(), self.data)

    def test_invalid_explicit_path_does_not_fall_back(self):
        with self.assertRaisesRegex(RuntimeError, 'Missing public files'):
            self.ns['find_market']('public', self.ns['BASE_FILES'], str(self.root / 'missing'))

    def test_missing_file_is_named(self):
        (self.data / 'claims.parquet').unlink()
        with self.assertRaisesRegex(RuntimeError, 'claims.parquet'):
            self._resolve()

    def test_multiple_data_folders_are_rejected(self):
        other = self.root / 'other'
        other.mkdir()
        for p in self.data.iterdir():
            (other / p.name).write_bytes(p.read_bytes())
        os.environ['IAA_DATA_ROOT'] = str(self.root)
        with self.assertRaisesRegex(RuntimeError, 'Expected one public directory'):
            self.ns['find_market']('public', self.ns['BASE_FILES'], '')

    def test_project_routes_work_from_a_nested_directory(self):
        (self.root / 'RUTAS_PROYECTO.json').write_text(json.dumps({'week_1_data': 'official'}), encoding='utf-8')
        cwd = self.root / 'repository/notebooks'
        cwd.mkdir(parents=True)
        with patch.object(Path, 'cwd', return_value=cwd):
            self.assertEqual(self.ns['find_market']('public', self.ns['BASE_FILES'], ''), self.data)

    def test_emerging_folder_cannot_be_used_as_developed(self):
        (self.data / 'reference_policies.parquet').write_bytes(b'fixture')
        with self.assertRaisesRegex(RuntimeError, 'mixing markets'):
            self.ns['find_market']('developed', self.ns['BASE_FILES'], str(self.data))

    def test_a_changed_input_is_rejected_before_training(self):
        folder = self._resolve()
        with (folder / 'claims.parquet').open('ab') as stream:
            stream.write(b'changed')
        with self.assertRaisesRegex(RuntimeError, 'fingerprint mismatch'):
            self.ns['inventory'](folder, self.ns['BASE_FILES'])

    def test_wrong_template_order_is_rejected(self):
        pq.write_table(pa.table({'row_id': ['contents', 'motor', 'buildings']}), self.data / 'sample_submission.parquet')
        self._refresh_contract()
        folder = self._resolve()
        self.ns['inventory'](folder, self.ns['BASE_FILES'])
        with self.assertRaisesRegex(RuntimeError, 'identifiers/order'):
            self.ns['check_template'](folder)

    def test_workspace_requires_successful_preflight(self):
        with self.assertRaisesRegex(RuntimeError, 'Run the input inventory'):
            self.ns['prepare_workspace'](1)

    def test_output_cannot_be_inside_inputs(self):
        self._verify()
        os.environ['IAA_NOTEBOOK_WORK'] = str(self.data / 'forbidden')
        with self.assertRaisesRegex(RuntimeError, 'read-only input data'):
            self.ns['prepare_workspace'](1)
        self.assertFalse((self.data / 'forbidden').exists())

    def test_changed_inputs_after_preflight_are_rejected(self):
        self._verify()
        with (self.data / 'claims.parquet').open('ab') as stream:
            stream.write(b'changed after validation')
        with self.assertRaisesRegex(RuntimeError, 'changed after validation'):
            self.ns['prepare_workspace'](1)

    def test_successful_preflight_writes_a_receipt_without_changing_inputs(self):
        self._verify()
        before = {p.name: p.read_bytes() for p in self.data.iterdir()}
        os.environ['IAA_NOTEBOOK_WORK'] = str(self.root / 'runs')
        os.environ['IAA_NOTEBOOK_EXPORT'] = str(self.root / 'exports')
        run, export = self.ns['prepare_workspace'](1)
        self.assertTrue(export.is_dir())
        receipt = json.loads((run / 'input_manifest.json').read_text(encoding='utf-8'))
        self.assertFalse(receipt['training_started'])
        self.assertEqual(receipt['template_rows']['public'], 3)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.data.iterdir()})


if __name__ == '__main__':
    unittest.main()
