"""Continúa únicamente la producción fuente registrada, sin scoring ni envíos."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys
import time

R = Path(__file__).resolve().parents[1]
OUT = R / 'privado/semana2/F3c_regularizado_20261028/source_scoped'
PLAN = R / 'registro/semana2_F3c_regularizado_fuente_plan.json'


def now(): return datetime.now(timezone.utc).isoformat()


def status(state, **kwargs):
    record = {'author': 'Codex', 'utc': now(), 'pid': os.getpid(), 'state': state,
        'queue_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'plan_sha256': hashlib.sha256(PLAN.read_bytes()).hexdigest(), **kwargs}
    tmp = OUT / 'queue_status.tmp'; dest = OUT / 'queue_status.json'
    tmp.write_text(json.dumps(record, indent=2), encoding='utf-8'); os.replace(tmp, dest)
    print(json.dumps(record), flush=True)


def main():
    lease = OUT / 'queue_lease.json'
    owner = {'pid': os.getpid(), 'utc': now()}
    with lease.open('x', encoding='utf-8') as h: json.dump(owner, h)
    try:
        status('WAITING_CURVES', already_completed_scopes=[])
        start = time.monotonic()
        while not (OUT / 'curves_complete.json').exists():
            if time.monotonic() - start > 3600:
                raise TimeoutError('No terminó admisión de curvas en60min; conservar checkpoints, revisar productor antes de continuar')
            time.sleep(15)
        curves = json.loads((OUT / 'curves_complete.json').read_text(encoding='utf-8'))
        assert curves['all_passed'] and len(curves['scopes']) == 26
        plan = json.loads(PLAN.read_text(encoding='utf-8'))
        completed = []
        for item in plan['scopes']:
            scope = item['scope']; status('SOURCE_SCOPE_RUNNING', scope=scope, already_completed_scopes=completed)
            with (OUT / (scope + '_worker.log')).open('ab') as logfile:
                result = subprocess.run([sys.executable, str(R / 'herramientas/producir_fuente_F3c_regularizado.py'),
                    'run', '--scope', scope], cwd=R, stdout=logfile, stderr=subprocess.STDOUT)
            if result.returncode:
                raise RuntimeError(f'Productor {scope} terminó con código{result.returncode}; no iniciar siguientes ámbitos')
            completed.append(scope)
        journal = OUT / 'native_attempts.jsonl'
        attempts = len(journal.read_text().splitlines()) if journal.exists() else 0
        status('SOURCE_COMPLETE_TARGET_ADAPTER_PENDING', already_completed_scopes=completed,
               native_attempts=attempts, new_scores=0, new_submissions=0,
               next_action='Assemble own-scope target bases/C1/F2/own and cross-fit calibrator inputs; freeze exact downstream budget before fitting/scoring. Source completion alone is not candidate validation.')
    except Exception as exc:
        status('STOPPED_REQUIRES_RECONCILIATION', error_type=type(exc).__name__, error=str(exc),
               new_scores=0, new_submissions=0)
        raise
    finally:
        if json.loads(lease.read_text(encoding='utf-8')) == owner: lease.unlink()


if __name__ == '__main__': main()
