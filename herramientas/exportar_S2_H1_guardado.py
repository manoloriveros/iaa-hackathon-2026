"""Regenera el CSV de la cartera congelada desde parámetros y entradas guardados.

Este comando nunca ajusta modelos, infiere nuevos componentes fuente o envía a
Kaggle. Su resultado es un artefacto técnico, no una admisión predictiva.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import csv
import importlib.util
import json
import os
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
sp = importlib.util.spec_from_file_location('P6_saved_export_producer', R/'herramientas/producir_S2_H1_nominal.py')
p = importlib.util.module_from_spec(sp); sp.loader.exec_module(p)


def main(output):
    sys.stdout.reconfigure(encoding='utf8')
    output = Path(output).resolve()
    assert output.is_relative_to(ROOT), 'Use an output inside the project workspace'
    report = p.w.read(p.OUT/'report.json'); plan = p.w.read(p.PLAN)
    manifest = p.w.read(p.OUT/'production_artifacts_manifest.json')
    assert all(p.w.sha(ROOT/name) == value for name, value in manifest['artifacts'].items())
    assert all(p.w.sha(ROOT/name) == value for name, value in plan['sources'].items())
    assert output != ROOT/report['CSV']['path'], 'Preserve the original CSV'
    assert output.suffix.lower() == '.csv' and output.parent.is_dir()
    assert not output.exists(), 'Choose a new output path; no artifact is overwritten'
    guards = []
    def reject(*args, **kwargs):
        raise AssertionError('Fitting is forbidden in the saved-model export command')
    for module, name in [(p, 'fit_base'), (p, 'learn_n3'), (p.v, 'fit_reporting'), (p.b, 'reporting_scope'),
                         (p.b, 'shape_fit'), (p.b, 'factor'), (p.h, 'learn'), (p.g, 'fit_stage'),
                         (p.core, 'learn'), (p.core, 'fit_component'), (p.core.b, 'shape_fit'),
                         (p.core.b, 'factor'), (p.core.g, 'fit_stage')]:
        guards.append((module, name, getattr(module, name))); setattr(module, name, reject)
    prices = []; normalizers = 0
    try:
        for item in plan['scopes']:
            line = item['line']; future = p.pd.read_parquet(ROOT/item['future_metadata'])
            components = p.pd.read_parquet(ROOT/item['future_components'])
            artifact = {'N3': p.w.read(p.OUT/f'parameters_{line}/N3.json'), 'S2': p.w.read(p.OUT/f'parameters_{line}/S2.json')}
            forecast, norm = p.forecast(future, components, artifact, future.row_id.tolist())
            prices.append(forecast); normalizers += sum(len(x) for x in norm.values())
        sample = p.pd.read_csv(p.SAMPLE, dtype=str)
        values = p.pd.concat(prices, ignore_index=True).set_index('row_id').loc[sample.row_id]
        ticks = p.round_ticks(values.candidate_S2_H1.to_numpy())
        tmp = output.with_name(output.name+'.tmp')
        assert not tmp.exists()
        with tmp.open('x', encoding='utf8', newline='') as stream:
            writer = csv.writer(stream, lineterminator='\n'); writer.writerow(['row_id', 'prediction'])
            for rowid, tick in zip(sample.row_id, ticks):
                writer.writerow([rowid, f'{int(tick)//1_000_000}.{int(tick)%1_000_000:06d}'])
            stream.flush(); os.fsync(stream.fileno())
        assert p.w.sha(tmp) == report['CSV']['sha256'], 'Regenerated CSV must match the registered artifact'
        assert not output.exists(); os.replace(tmp, output)
    finally:
        for module, name, value in reversed(guards): setattr(module, name, value)
    receipt = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'status': 'saved_nominal_model_CSV_regenerated_exact',
               'output': p.w.rel(output), 'sha256': p.w.sha(output), 'rows': 209063,
               'code_sha256': p.w.sha(Path(__file__)), 'production_report_sha256': p.w.sha(p.OUT/'report.json'),
               'blocked_fit_entrypoints': 13, 'recomputed_prediction_normalizers_separate': normalizers,
               'new_model_fits': 0, 'new_C0_fits': 0, 'new_source_inference': 0, 'new_predictive_price_families': 0,
               'new_submissions': 0, 'submission_allowed': False}
    p.dump(output.with_suffix('.receipt.json'), receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', required=True); args = parser.parse_args()
    with p.threadpool_limits(limits=2): main(args.output)
