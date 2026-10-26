"""Reproducción P6 en otro proceso: solo artefactos guardados, sin aprendizaje."""
from datetime import datetime, timezone
from pathlib import Path
import csv
import hashlib
import importlib.util
import io
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
sp = importlib.util.spec_from_file_location('P6_fresh_process_producer', R/'herramientas/producir_S2_H1_nominal.py')
p = importlib.util.module_from_spec(sp); sp.loader.exec_module(p)
OUT = p.OUT; w = p.w


def main():
    sys.stdout.reconfigure(encoding='utf8')
    assert (OUT/'report.json').exists() and not (OUT/'independent_process_replay.json').exists()
    report = w.read(OUT/'report.json'); plan = w.read(p.PLAN)
    assert all(w.sha(ROOT/path) == expected for path, expected in plan['sources'].items())
    assert w.sha(ROOT/report['CSV']['path']) == report['CSV']['sha256']
    files = [OUT/'report.json', ROOT/report['CSV']['path']]
    for line in p.h.LINES:
        files += list((OUT/f'parameters_{line}').glob('*.json'))
        files += [OUT/f'forecast_{line}.parquet', OUT/f'future_{line}.parquet', OUT/f'components_{line}.parquet']
    hashes = {w.rel(path): w.sha(path) for path in files}
    p.dump(OUT/'production_artifacts_manifest.json', {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
                                                   'scope': 'Post-production immutable model, input and forecast snapshot before separate-process replay',
                                                   'artifacts': hashes, 'plan_sha256': w.sha(p.PLAN)})
    saved_events = w.sha(OUT/'events.jsonl'); guards = []
    def reject(*args, **kwargs):
        raise AssertionError('No estimation in separate-process P6replay')
    for module, name in [(p, 'fit_base'), (p, 'learn_n3'), (p.v, 'fit_reporting'), (p.b, 'reporting_scope'),
                         (p.b, 'shape_fit'), (p.b, 'factor'), (p.h, 'learn'), (p.g, 'fit_stage'),
                         (p.core, 'learn'), (p.core, 'fit_component'), (p.core.b, 'shape_fit'),
                         (p.core.b, 'factor'), (p.core.g, 'fit_stage')]:
        guards.append((module, name, getattr(module, name))); setattr(module, name, reject)
    outputs = []; normalizers = 0
    try:
        for item in plan['scopes']:
            line = item['line']; future = p.pd.read_parquet(ROOT/item['future_metadata'])
            expected_ids = future.row_id.tolist()
            future['T0'] = -1e30; future['reserve'] = 1e30
            components = p.pd.read_parquet(ROOT/item['future_components'])
            artifact = {'N3': w.read(OUT/f'parameters_{line}/N3.json'), 'S2': w.read(OUT/f'parameters_{line}/S2.json')}
            prices, norms = p.forecast(future, components, artifact, expected_ids)
            saved = p.pd.read_parquet(OUT/f'forecast_{line}.parquet')
            assert prices.equals(saved)
            outputs.append(prices); normalizers += sum(len(x) for x in norms.values())
        sample = p.pd.read_csv(p.SAMPLE, dtype=str)
        output = p.pd.concat(outputs, ignore_index=True).set_index('row_id').loc[sample.row_id].reset_index()
        ticks = p.round_ticks(output.candidate_S2_H1.to_numpy())
        text = io.StringIO(newline=''); writer = csv.writer(text, lineterminator='\n'); writer.writerow(['row_id', 'prediction'])
        for rowid, tick in zip(output.row_id, ticks):
            writer.writerow([rowid, f'{int(tick)//1_000_000}.{int(tick)%1_000_000:06d}'])
        sha = hashlib.sha256(text.getvalue().encode('utf8')).hexdigest()
        assert sha == report['CSV']['sha256'] and len(output) == 209063
        assert w.sha(OUT/'events.jsonl') == saved_events
        assert all(w.sha(ROOT/path) == expected for path, expected in hashes.items())
        assert all(w.sha(ROOT/path) == expected for path, expected in plan['sources'].items())
    finally:
        for module, name, value in reversed(guards): setattr(module, name, value)
    receipt = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
               'status': 'P6separate_process_saved_model_replay_exact', 'rows': 209063,
               'CSV_sha256': sha, 'CSV_bytes_exact': True, 'full_saved_forecasts_exact_all_lines': True,
               'blocked_estimation_entrypoints': 13, 'ultimate_prediction_normalizers_separate': normalizers,
               'arbitrary_future_response_payload_ignored': True, 'registered_sources_unchanged': True,
               'production_artifacts_unchanged': True, 'fit_events_unchanged': True,
               'new_model_fits': 0, 'new_C0_fits': 0, 'new_source_inference': 0,
               'new_predictive_price_families': 0, 'new_scores': 0, 'new_submissions': 0,
               'reproduced_primary_rows': 209063, 'reproduced_diagnostic_base_rows': 209063,
               'report_sha256': w.sha(OUT/'report.json'), 'replay_code_sha256': w.sha(Path(__file__))}
    p.dump(OUT/'independent_process_replay.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    with p.threadpool_limits(limits=2): main()
