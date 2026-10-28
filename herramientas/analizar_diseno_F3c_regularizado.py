"""Verifica solo la formulación propuesta con números sintéticos; no contiene fit ni lector del concurso."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import numpy as np


def objective(beta, X, y, base, cell, lam):
    if not (np.isfinite(base).all() and (base > 0).all() and
            np.isfinite(y).all() and (y >= 0).all()):
        raise ValueError('Objetivo u offset inválido')
    scale = np.sqrt(base).mean()
    # Igual peso de penalización para las seis celdas; pérdida por fila.
    # Así una celda pequeña no reduce automáticamente su penalización.
    diag = np.array([np.mean(np.sqrt(base[cell == j % 6]) *
                     X[cell == j % 6, j] ** 2) / (6 * scale)
                     for j in range(X.shape[1])])
    mu = base * np.exp(X @ beta)
    root = np.sqrt(mu)
    dev = 4 * (y / root + root - 2 * np.sqrt(y))
    loss = dev.mean() / (2 * scale) + lam * np.dot(diag, beta ** 2) / 2
    grad = X.T @ (root - y / root) / (len(y) * scale) + lam * diag * beta
    hess = (X.T * ((root + y / root) / (2 * len(y) * scale))) @ X + lam * np.diag(diag)
    return loss, grad, hess, mu, diag


def main():
    repo = Path(__file__).resolve().parents[1]
    out = repo / 'privado/semana2/F3c_regularizado_20261028'
    plan = repo / 'registro/semana2_F3c_regularizado_plan.json'
    assert (out / 'forum_previo.json').exists(), 'Registrar antes del cálculo'
    p = json.loads(plan.read_text(encoding='utf-8'))
    assert p['status'] == 'proposal_and_synthetic_analysis_only'
    rng = np.random.default_rng(20261028)
    cell = np.repeat(np.arange(6), [240, 90, 60, 40, 20, 10])
    base = np.exp(rng.normal(3, 1, len(cell)))
    signal = rng.normal(0, .2, len(cell))
    signal[np.isin(cell, [1, 4])] = 0  # edificios: bloque propio identidad
    X = np.zeros((len(cell), 12))
    X[np.arange(len(cell)), cell] = 1
    X[np.arange(len(cell)), 6 + cell] = signal
    beta = np.r_[np.linspace(-.15, .15, 6), [.2, 0, .4, .6, 0, .8]]
    y = np.where(rng.random(len(cell)) < .14, rng.gamma(2, 60, len(cell)), 0.)
    lam = .1
    loss, grad, hess, mu, diag = objective(beta, X, y, base, cell, lam)
    eps = 1e-5
    fdg, fdh = [], []
    for j in range(12):
        e = np.eye(12)[j] * eps
        plus = objective(beta + e, X, y, base, cell, lam)
        minus = objective(beta - e, X, y, base, cell, lam)
        fdg.append((plus[0] - minus[0]) / (2 * eps))
        fdh.append((plus[1] - minus[1]) / (2 * eps))
    scalar_mu = np.array([float(b) * math.exp(sum(float(xx) * float(bb)
                       for xx, bb in zip(row, beta))) for b, row in zip(base, X)])
    scalar_loss = sum(2 * (float(a) / math.sqrt(float(b)) + math.sqrt(float(b)) -
                         2 * math.sqrt(float(a))) for a, b in zip(y, scalar_mu))
    scalar_loss /= len(y) * sum(math.sqrt(float(b)) for b in base) / len(base)
    scalar_loss += lam * sum(float(d) * float(b) ** 2 for d, b in zip(diag, beta)) / 2
    scale_test = objective(beta, X, 100 * y, 100 * base, cell, lam)
    nonzero = np.flatnonzero(diag > 0)
    tests = {
        'scalar_formula': abs(loss - scalar_loss) < 1e-12,
        'scalar_prediction': np.allclose(mu, scalar_mu, rtol=1e-14, atol=0),
        'gradient': np.allclose(grad, fdg, rtol=1e-6, atol=1e-8),
        'hessian': np.allclose(hess, np.array(fdh).T, rtol=1e-6, atol=1e-8),
        'positive_definite_active_columns': np.linalg.eigvalsh(hess[np.ix_(nonzero, nonzero)]).min() > 0,
        'zero_columns_removed': set(np.flatnonzero(diag == 0)) == {7, 10},
        'identity_at_zero': np.array_equal(objective(np.zeros(12), X, y, base, cell, lam)[3], base),
        'currency_invariance_loss': np.isclose(scale_test[0], loss, rtol=1e-13),
        'currency_invariance_gradient': np.allclose(scale_test[1], grad, rtol=1e-13, atol=1e-13),
        'currency_invariance_hessian': np.allclose(scale_test[2], hess, rtol=1e-13, atol=1e-13),
        'positive_prices': bool((mu > 0).all()),
        'rowwise_calibration_given_fixed_inputs': np.allclose(scalar_mu[::3], base[::3] * np.exp(X[::3] @ beta), rtol=1e-14),
    }
    for gamma in (0., .25, .5, .75, 1.):
        correction = np.exp(gamma * signal)
        tests['attenuation_envelope_' + str(gamma)] = bool(np.all(correction >= np.minimum(1., np.exp(signal)) - 1e-14)
            and np.all(correction <= np.maximum(1., np.exp(signal)) + 1e-14))
    # Es un límite del factor, no del precio después del intercepto.
    receipt = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'status': 'mathematical_prototype_only', 'checks': {k: bool(v) for k, v in tests.items()},
        'all_passed': all(tests.values()), 'synthetic_rows': len(y), 'active_coefficients': len(nonzero),
        'new_real_fits': 0, 'synthetic_fits': 0, 'new_scores': 0, 'new_submissions': 0,
        'max_gradient_error': float(np.max(np.abs(grad - fdg))),
        'max_hessian_error': float(np.max(np.abs(hess - np.array(fdh).T))),
        'minimum_active_eigenvalue': float(np.linalg.eigvalsh(hess[np.ix_(nonzero, nonzero)]).min()),
        'plan_sha256': hashlib.sha256(plan.read_bytes()).hexdigest(),
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'not_verified': ['optimizer/constrained KKT', 'real input lineage/nested learning',
                        'whole trunk batch invariance', 'predictive improvement/private score']}
    with (out / 'synthetic_math.json').open('x', encoding='utf-8') as f:
        json.dump(receipt, f, indent=2)
    print(json.dumps(receipt))
    assert receipt['all_passed']


if __name__ == '__main__':
    main()
