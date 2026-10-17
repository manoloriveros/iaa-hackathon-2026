"""Comprueba la cola de capitales, enlaces y hashes; conserva la versión previa del manifiesto."""
from pathlib import Path
import hashlib
import json
import re
import shutil

import clean_data as c
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def main():
    out = c.ROOT / json.loads((c.BASE / 'current_run.json').read_text(encoding='utf-8'))['workspace_relative_run']
    checks = []

    def add(name, passed):
        checks.append({'check': name, 'passed': bool(passed)})
        assert passed, name

    for line, limit in [('buildings', 10_000_000), ('contents', 1_000_000)]:
        q = pq.read_table(out / 'tables' / f'capital_review_{line}.parquet').to_pandas()
        src = pd.concat([pq.read_table(c.RAW / f'{p}_{line}.parquet', columns=[
            'row_id', 'policy_id', 'period_start', 'period_end', 'sum_insured', 'address_id']).to_pandas()
            for p in ['policies', 'test']], ignore_index=True).set_index('row_id')
        add(line + ':queue_current_values_match_source', q.row_id.is_unique and np.array_equal(
            q.sum_insured, src.loc[q.row_id, 'sum_insured']))
        v = q.previous_row_id.notna()
        prev = src.loc[q.loc[v, 'previous_row_id']]
        add(line + ':previous_values_policy_dates_match_source',
            np.array_equal(q.loc[v, 'previous_sum_insured'], prev.sum_insured)
            and np.array_equal(q.loc[v, 'policy_id'], prev.policy_id)
            and np.array_equal(q.loc[v, 'previous_period_end'], prev.period_end))
        ratio = q.loc[v, 'sum_insured'].to_numpy() / prev.sum_insured.to_numpy()
        add(line + ':ratios_and_strictly_past_periods',
            np.allclose(q.loc[v, 'ratio_to_previous'], ratio, equal_nan=True)
            and (q.loc[v, 'previous_period_end'] < q.loc[v, 'period_start']).all())
        add(line + ':screening_flags_and_no_repairs',
            np.array_equal(q.high_amount_screen, q.sum_insured > limit)
            and (q.high_amount_screen | q.jump_up_1000_screen | q.jump_down_1000_screen).all()
            and q.decision.eq('pending_review_no_correction').all())
    jev = c.ROOT / 'Hackaton/Semana 1/Validacion_IA/jev_20261016'
    for report in [out / 'informe.html', jev / 'evaluacion.html']:
        links = re.findall(r'href="([^"]+)"', report.read_text(encoding='utf-8'))
        add(report.parent.name + ':local_links_exist', all((report.parent / link).exists()
            for link in links if not link.startswith('http')))
    for folder in [out, jev]:
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        add(folder.name + ':all_manifest_hashes_match', all(hashlib.sha256(
            (folder / e.get('path', e.get('file'))).read_bytes()).hexdigest() == e['sha256'] for e in manifest['files']))
    # This verifies the prior artifact state first. New evidence is added to a new manifest version.
    old_manifest = out / 'manifest.json'
    backup = out / 'manifest_initial.json'
    if not backup.exists():
        shutil.copy2(old_manifest, backup)
    shutil.copy2(__file__, out / 'source_snapshot' / Path(__file__).name)
    c.dump(out / 'artifact_qa.json', {'passed': True, 'checks_count': len(checks), 'checks': checks,
        'visual_qa': 'Chart and Chrome screenshot inspected separately in this Codex turn.',
        'scope': 'Own artifact checks; no independent actuarial validation.'})
    entries = [{'path': p.relative_to(out).as_posix(), 'bytes': p.stat().st_size, 'sha256': c.digest(p)}
               for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    c.dump(old_manifest, {'count': len(entries), 'files': entries})
    print(json.dumps({'passed': True, 'artifact_checks': len(checks), 'manifest_files': len(entries)}))


if __name__ == '__main__':
    main()
