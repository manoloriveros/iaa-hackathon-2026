"""Replay de P5 con respuestas retenidas corruptas y puntos de ajuste bloqueados."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
sp = importlib.util.spec_from_file_location('P5_committed_replay', R/'herramientas/recalibrar_valoracion_H1.py')
m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
w = m.w; OUT = m.OUT


def main():
    sys.stdout.reconfigure(encoding='utf8')
    assert (OUT/'report.json').exists() and not (OUT/'replay_report.json').exists()
    report = w.read(OUT/'report.json'); assert report['committed_scopes'] == 180
    plan = w.read(m.PLAN); assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    frames = m.input_frames(); original = []
    def reject(*args, **kwargs):
        raise AssertionError('No fitting permitted during actual P5replay')
    for module, name in [(m.h, 'learn'), (m.b, 'reporting_scope'), (m.b, 'factor'), (m.v, 'fit_reporting'),
                         (m.g, 'fit_stage'), (m.complete, 'learn'), (m.complete, 'fit_component'),
                         (m.complete.b, 'factor'), (m.complete.g, 'fit_stage')]:
        original.append((module, name, getattr(module, name))); setattr(module, name, reject)
    events_before = w.sha(OUT/'events.jsonl'); checks = []; normalizers = 0
    try:
        for name, branch in m.BRANCHES:
            for item in plan['scopes']:
                line, outer, member = item['line'], item['outer'], item['member']
                folder = OUT/name/f'scope_{line}_outer{outer}_member{member}'
                commit = w.read(folder/'committed.json')
                assert all(w.sha(ROOT/p) == z for p, z in commit['outputs'].items())
                f = m.corrupt(m.scope(frames[line], outer, member)); c0 = m.learned_c0(line, outer, member)
                a = m.learner(f, c0, branch, line, folder/'primary', 'replay', 'replay', member == -1, True)
                saved = m.pd.read_parquet(folder/'ultimate.parquet').set_index('row_id').loc[a['held_row_ids']]
                assert all(m.np.array_equal(saved['U_'+k].to_numpy(), val) for k, val in a['ultimate'].items())
                normalizers += a['ultimate_normalizers']
                checks.append({'line': line, 'outer': outer, 'member': member, 'branch': branch, 'poisoned_actual_replay_exact': True})
        assert len(checks) == 180 and w.sha(OUT/'events.jsonl') == events_before
        assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    finally:
        for module, name, value in reversed(original):
            setattr(module, name, value)
    receipt = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'status': 'P5actual_poisoned_replay_exact_without_learning',
               'all180_exact': True, 'scopes': checks, 'blocked_fit_entrypoints': 9, 'fit_events_unchanged': True,
               'ultimate_normalizers_recomputed_separate': normalizers, 'new_model_fits': 0, 'new_C0_fits': 0,
               'new_scores': 0, 'new_source_inference': 0, 'new_final_test_prices': 0, 'new_submissions': 0,
               'report_sha256': w.sha(OUT/'report.json'), 'replay_code_sha256': w.sha(Path(__file__))}
    m.dump(OUT/'replay_report.json', receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != 'scopes'}))


if __name__ == '__main__':
    with m.threadpool_limits(limits=2):
        main()
