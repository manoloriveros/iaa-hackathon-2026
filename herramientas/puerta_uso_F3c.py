"""Aplica las consecuencias del cierre sin modificar una selección en Kaggle."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def decide(purpose):
    index = read(REPO / 'registro/pendientes_F3c_actual.json')
    ledger_path = ROOT / index['ledger']
    assert sha(ledger_path) == index['ledger_sha256']
    ledger = read(ledger_path)
    for source in ledger['sources']:
        assert sha(ROOT / source['path']) == source['sha256'], source['path']
    assert sha(ROOT / index['report']) == index['report_sha256']
    allowed = purpose == 'research_review'
    fallback = REPO / 'privado/semana2/mision017_fase2/calibracion_F2_creible_20261025_v1/final_creible_2025.csv'
    assert sha(fallback) == '1a003d8682f1fcd71ad4a44f59f785d394488fc1cc95e60722f418b04c30ef29'
    return {'purpose': purpose, 'allowed': allowed,
        'decision': 'research_only_preserve_simpler_comparator' if allowed else 'blocked_evidence_requirements_not_satisfied',
        'formal_incumbent_policy_v2_unchanged': True,
        'reasons': index['hard_limits'],
        'preserved_without_own_factors': str(fallback),
        'not_a_professional_approval': True,
        'release': 'Nuevo recibo de admisión con evidencia que cierre los requisitos; no basta reconocer la limitación o mejorar público.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('purpose', choices=('research_review', 'promote', 'professional_quote', 'claim_full_reproduction', 'new_submission'))
    a = p.parse_args()
    result = decide(a.purpose)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['allowed'] else 3)
