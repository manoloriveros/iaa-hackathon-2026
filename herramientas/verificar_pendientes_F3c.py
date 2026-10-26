"""Oráculo de métrica por fila, replay de multiplicidades y aprendizaje protegido."""
from __future__ import annotations
import argparse
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from cerrar_pendientes_F3c import (SRC, NAMES, read, save, sha, rel, load, fit_recipe, cells, band)


def oracle(y, prediction, weights):
    p = 1.5
    mean = np.sum(y * weights) / np.sum(weights)
    def d(mu):
        return 2 * (np.power(y, 2 - p) / ((1 - p) * (2 - p))
                    - y * np.power(mu, 1 - p) / (1 - p)
                    + np.power(mu, 2 - p) / (2 - p))
    return 1 - np.sum(weights * d(prediction)) / np.sum(weights * d(np.full(len(y), mean)))


def main(run):
    result = read(run / 'results.json')
    b, pol, sets = load()
    future = b[b.conjunto == 'test']
    fk = pd.Series(cells(future) + '_' + band(future.exposure.to_numpy())).value_counts(normalize=True)
    checks = []
    for path in sorted(run.glob('*_to_*.parquet')):
        frame = pd.read_parquet(path)
        group, unique = pd.factorize(frame.group, sort=True)
        ng = len(unique)
        # Exactamente las dos primeras multiplicidades de la semilla archivada.
        multiplicities = np.random.default_rng(2026102607).multinomial(ng, np.full(ng, 1 / ng), size=2)
        for weighted in ([False, True] if path.stem == 'DEV23_T2b_to_HOLD24_T2b' else [False]):
            label = path.stem + ('_composition2025' if weighted else '')
            saved = np.load(run / ('bootstrap_' + label + '.npz'))
            segments = {s: np.ones(len(frame), bool) if s == 'all' else
                frame.new_business.to_numpy() if s == 'new_business' else
                ~frame.new_business.to_numpy() if s == 'renewal' else
                frame.line.to_numpy() == s for s in saved['segments']}
            weights = np.ones(len(frame))
            if weighted:
                k = cells(frame) + '_' + band(frame.exposure.to_numpy())
                freq = pd.Series(k).value_counts(normalize=True)
                weights = pd.Series(k).map(fk / freq).fillna(0).to_numpy()
            error = 0.
            for j, mult in enumerate(multiplicities):
                for si, mask in enumerate(segments.values()):
                    ww = weights[mask] * mult[group[mask]]
                    yy = frame.y.to_numpy()[mask]
                    for ni, n in enumerate(NAMES):
                        score = oracle(yy, frame[n].to_numpy()[mask], ww)
                        error = max(error, abs(score - saved['scores'][j, si, ni]))
            assert error < 2e-12
            checks.append({'label': label, 'rowwise_replayed_draws': 2, 'models': 3, 'segments': len(segments),
                           'max_error': error, 'new_draws_or_candidate_search': 0})
    powers = result['fixed_public_shape']
    for trname, tename in [('DEV23_T2b', 'HOLD24_T2b'), ('HOLD24_T2b', 'DEV23_T2b')]:
        label = trname + '_to_' + tename
        tr, te = sets[trname], sets[tename].copy()
        # El aprendizaje vuelve a correr solo como control adverso, no para elegir.
        te['y'] = 1e9 + np.arange(len(te))
        pred, params, _ = fit_recipe(tr, te, powers)
        saved = read(run / (label + '_parameters.json'))
        learned = lambda obj: {k: v for k, v in obj.items() if k != 'stage_contributions'}
        assert learned(saved) == learned(params)
        pp = pd.read_parquet(run / (label + '.parquet'))
        assert all(np.array_equal(pp[n].to_numpy(), pred[n]) for n in NAMES)
        checks.append({'label': label, 'held_target_poison_learning': 'parameters_and_prices_exact',
                       'adverse_scalar_recipe_refit': 1, 'source_or_C0_fits': 0})
    save(run / 'independent_math_and_poison.json', {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'code_sha256': sha(Path(__file__)), 'results_sha256': sha(run / 'results.json'),
        'checks': checks, 'professional_independent_review': False,
        'limit': 'Otro cálculo matemático propio; ancestros fuente y mezcla de completitud quedan fuera del control adverso.'})
    print({'verified': len(checks), 'receipt': rel(run / 'independent_math_and_poison.json')})


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--run', required=True, type=Path)
    main(p.parse_args().run.resolve())
