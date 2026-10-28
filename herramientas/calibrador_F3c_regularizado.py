"""Calibrador de baja dimensión. No carga datos ni ejecuta trabajo al importar."""
import json
import numpy as np
from scipy.optimize import minimize

LAMBDAS = [1., .1, .01]


def design(base, signal, cell):
    b = np.asarray(base, dtype=float)
    z = np.asarray(signal, dtype=float)
    c = np.asarray(cell)
    if b.ndim != 1 or z.shape != b.shape or c.shape != b.shape or not len(b):
        raise ValueError('Dimensiones incorrectas')
    if not (np.isfinite(b).all() and (b > 0).all() and np.isfinite(z).all()):
        raise ValueError('Offset o señal inválidos')
    if not np.isin(c, np.arange(6)).all():
        raise ValueError('Celda desconocida')
    c = c.astype(int)
    if np.any(z[np.isin(c, [1, 4])] != 0):
        raise ValueError('Edificios debe conservar bloque identidad')
    X = np.zeros((len(b), 12))
    X[np.arange(len(b)), c] = 1
    X[np.arange(len(b)), 6 + c] = z
    return b, X, c


def setup(base, signal, cell, y):
    b, X, c = design(base, signal, cell)
    y = np.asarray(y, dtype=float)
    if y.shape != b.shape or not np.isfinite(y).all() or (y < 0).any():
        raise ValueError('Costes inválidos')
    scale = np.sqrt(b).mean()
    diag = np.zeros(12)
    for j in range(12):
        m = c == j % 6
        if m.any():
            diag[j] = np.mean(np.sqrt(b[m]) * X[m, j] ** 2) / (6 * scale)
    return b, X, y, scale, diag


def loss_grad(beta, b, X, y, scale, diag, lam):
    eta = X @ beta
    # No clipping silencioso del predictor: un paso no finito es un fallo del optimizador.
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        root = np.sqrt(b) * np.exp(eta / 2)
        loss = np.mean(2 * (y / root + root - 2 * np.sqrt(y))) / scale
        loss += lam * np.dot(diag, beta ** 2) / 2
        grad = X.T @ (root - y / root) / (len(y) * scale) + lam * diag * beta
    return float(loss), grad


def projected_gradient(beta, grad, active):
    pg = grad.copy()
    for j in range(6, 12):
        if beta[j] <= 1e-9 and grad[j] >= 0:
            pg[j] = 0
        if beta[j] >= 1 - 1e-9 and grad[j] <= 0:
            pg[j] = 0
    pg[~active] = 0
    return float(np.abs(pg).max())


def fit(base, signal, cell, y, lam, independent=False):
    if lam not in LAMBDAS:
        raise ValueError('Lambda fuera de receta')
    b, X, y, scale, diag = setup(base, signal, cell, y)
    active = diag > 0
    bounds = [(None, None) if j < 6 else (0., 1.) for j in np.flatnonzero(active)]
    def obj(t):
        beta = np.zeros(12)
        beta[active] = t
        value, grad = loss_grad(beta, b, X, y, scale, diag, lam)
        return value, grad[active]
    method = 'SLSQP' if independent else 'L-BFGS-B'
    options = {'maxiter': 5000, 'ftol': 1e-14}
    if not independent:
        options.update(gtol=1e-9, maxls=50, maxcor=20)
    result = minimize(obj, np.zeros(int(active.sum())), method=method, jac=True,
                      bounds=bounds, options=options)
    beta = np.zeros(12)
    beta[active] = result.x
    value, grad = loss_grad(beta, b, X, y, scale, diag, lam)
    pg = projected_gradient(beta, grad, active)
    if not result.success or pg >= 1e-6:
        raise RuntimeError(f'Convergencia no admitida: {result.message}; KKT={pg}')
    return {'beta': beta.tolist(), 'lambda': lam, 'scale': float(scale), 'diag': diag.tolist(),
            'active': active.tolist(), 'loss': value, 'projected_gradient_inf': pg,
            'solver': method, 'iterations': int(result.nit)}


def predict(base, signal, cell, artifact):
    b, X, _ = design(base, signal, cell)
    beta = np.asarray(artifact['beta'], float)
    if beta.shape != (12,) or not np.isfinite(beta).all() or (beta[6:] < 0).any() or (beta[6:] > 1).any():
        raise ValueError('Parámetros inválidos')
    mu = b * np.exp(X @ beta)
    if not np.isfinite(mu).all() or (mu <= 0).any():
        raise ValueError('Predicción inválida')
    return mu


def select(losses):
    a = np.asarray(losses, float)
    if a.shape != (3,) or not np.isfinite(a).all():
        raise ValueError('Pérdidas del selector inválidas')
    tolerance = 1e-10 * max(1., abs(a.min()))
    j = int(np.flatnonzero(a <= a.min() + tolerance)[0])
    return {'lambda': LAMBDAS[j], 'losses': a.tolist(), 'tie_tolerance': float(tolerance)}


def synthetic_bundle(frame, held_frame):
    # Esta función recibe entradas ya formadas: no certifica productores del tronco real.
    train = frame.loc[~frame.is_held].copy()
    if set(train.group_id) & set(held_frame.group_id):
        raise ValueError('Grupos retenidos en entrenamiento')
    if train.row_id.duplicated().any():
        raise ValueError('Claves duplicadas')
    totals = np.zeros(3)
    members = []
    for f in range(5):
        tr = train.loc[train.fold != f]
        va = train.loc[train.fold == f]
        for k, lam in enumerate(LAMBDAS):
            model = fit(tr.base, tr.signal, tr.cell, tr.y, lam)
            mu = predict(va.base, va.signal, va.cell, model)
            totals[k] += np.sum(4 * (va.y.to_numpy() / np.sqrt(mu) + np.sqrt(mu) - 2 * np.sqrt(va.y.to_numpy())))
            members.append(model)
    selection = select(totals)
    final = fit(train.base, train.signal, train.cell, train.y, selection['lambda'])
    return {'selection': selection, 'members': members, 'final': final,
            'training_rows': sorted(train.row_id.tolist())}
