"""Replay real de P4 con todos los puntos de ajuste bloqueados, sin nuevos scores."""
from pathlib import Path
import importlib.util
import json
from datetime import datetime, timezone
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
sp = importlib.util.spec_from_file_location('P4_committed_replay', R/'herramientas/validar_transferencia_anual_H1.py')
m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
np = m.np; pd = m.pd; OUT = m.OUT; w = m.w


def main():
    sys.stdout.reconfigure(encoding='utf8')
    assert (OUT/'report.json').exists() and not (OUT/'replay_report.json').exists()
    report = w.read(OUT/'report.json'); assert report['committed_scopes'] == 90
    plan = w.read(m.PLAN)
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    extra = w.read(OUT/'transitive_source_cut_before.json')
    assert all(w.sha(ROOT/p) == z for p, z in extra['sources'].items())
    frames = m.input_frames(); claims = m.n.attach_claim_year(pd.read_parquet(m.CLAIMS), frames)
    guard = []
    def reject(*args, **kwargs):
        raise AssertionError('No fitting allowed in actual P4saved replay')
    for module, name in [(m.h, 'learn'), (m.b, 'reporting_scope'), (m.b, 'factor'), (m.v, 'fit_reporting'),
                         (m.g, 'fit_stage'), (m.complete, 'learn'), (m.complete, 'fit_component'),
                         (m.complete.b, 'factor'), (m.complete.g, 'fit_stage')]:
        guard.append((module, name, getattr(module, name))); setattr(module, name, reject)
    checked = []; normalizers = 0
    event_before = w.sha(OUT/'events.jsonl')
    try:
        for scope in w.read(OUT/'preflight.json')['scopes']:
            line, outer, member = scope['line'], scope['outer'], scope['member']
            folder = OUT/f'scope_{line}_outer{outer}_member{member}'
            commit = w.read(folder/'committed.json')
            assert all(w.sha(ROOT/p) == z for p, z in commit['outputs'].items())
            f = m.make_scope(frames[line], outer, member)
            bad, cc = m.corrupt(f, claims)
            # Reuse primary artifacts, with poisoned future responses. Every
            # numerical fitting entrypoint is forbidden, so cache checks alone
            # cannot silently produce new learned objects.
            replay = m.learn_scope(bad, cc, line, folder/'primary', OUT,
                                   f'replay|{line}|{outer}|{member}', 'replay', member == -1)
            saved = pd.read_parquet(folder/'ultimate.parquet').set_index('row_id').loc[replay['held_row_ids']]
            assert all(np.array_equal(saved['U_'+k].to_numpy(), val) for k, val in replay['ultimate'].items())
            assert m.b.digest(replay['C0']) == m.b.digest(w.read(folder/'primary/C0.json'))
            normalizers += replay['ultimate_normalizers']
            checked.append({'line': line, 'outer': outer, 'member': member,
                            'real_yearfiltered_flow_fits_blocked_and_poisoned_replay_exact': True})
        assert w.sha(OUT/'events.jsonl') == event_before
        assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
        assert all(w.sha(ROOT/p) == z for p, z in extra['sources'].items())
    finally:
        for module, name, original in reversed(guard):
            setattr(module, name, original)
    receipt = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
               'status': 'P4actual_yearfiltered_flow_replay_exact_without_learning', 'scopes': checked,
               'blocked_fit_entrypoints': 9, 'all90_exact': len(checked) == 90,
               'recomputed_covariate_only_ultimate_normalizers_separate': normalizers,
               'fit_events_unchanged': True, 'new_fits': 0, 'new_C0_fits': 0, 'new_scores': 0,
               'new_source_inference': 0, 'new_final_test_prices': 0, 'new_submissions': 0,
               'main_registered_sources_unchanged': True, 'transitive_sources_cut_during_execution_unchanged': True,
               'report_sha256': w.sha(OUT/'report.json'), 'code_sha256': w.sha(Path(__file__))}
    m.dump(OUT/'replay_report.json', receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k not in ['scopes']}))


if __name__ == '__main__':
    with m.threadpool_limits(limits=2):
        main()
