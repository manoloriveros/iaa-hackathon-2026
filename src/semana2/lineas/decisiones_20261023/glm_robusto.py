"""GLM Poisson y Gamma con enlace log por IRLS y errores típicos robustos agrupados (Claude, 23-10-2026).

Se usa solo para estimar relatividades del nuevo negocio (NB-CRED-01); no produce predicciones de precio.
Diseño denso en float32 con productos por bloques en float64, para que quepa el desarrollado de autos.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import sparse

BLOQUE = 200_000


def _xtwx(X, w):
    p = X.shape[1]
    A = np.zeros((p, p))
    for i in range(0, X.shape[0], BLOQUE):
        xb = X[i:i + BLOQUE].astype(np.float64)
        A += xb.T @ (xb * w[i:i + BLOQUE, None])
    return A


def _xtv(X, v):
    out = np.zeros(X.shape[1])
    for i in range(0, X.shape[0], BLOQUE):
        out += X[i:i + BLOQUE].astype(np.float64).T @ v[i:i + BLOQUE]
    return out


def _eta(X, beta):
    out = np.empty(X.shape[0])
    for i in range(0, X.shape[0], BLOQUE):
        out[i:i + BLOQUE] = X[i:i + BLOQUE].astype(np.float64) @ beta
    return out


def _devianza(y, mu, familia):
    if familia == 'poisson':
        t = np.where(y > 0, y * np.log(np.where(y > 0, y, 1) / mu), 0.0)
        return 2 * np.sum(t - (y - mu))
    return 2 * np.sum(-np.log(y / mu) + (y - mu) / mu)


def ajustar(X, y, offset, familia, cluster, ridge=1e-8, maxit=100, tol=1e-10):
    """Devuelve coeficientes, errores típicos robustos agrupados, iteraciones y convergencia."""
    y = np.asarray(y, float)
    offset = np.zeros(len(y)) if offset is None else np.asarray(offset, float)
    p = X.shape[1]
    beta = np.zeros(p)
    if familia == 'poisson':
        beta[0] = np.log(y.sum() / np.exp(offset).sum())
    else:
        beta[0] = np.log(y.mean())
    eta = _eta(X, beta) + offset
    mu = np.exp(eta)
    dev = _devianza(y, mu, familia)
    convergio = False
    for it in range(1, maxit + 1):
        w = mu if familia == 'poisson' else np.ones_like(mu)
        z = (eta - offset) + (y - mu) / mu
        A = _xtwx(X, w) + ridge * np.eye(p)
        b = _xtv(X, w * z)
        nuevo = np.linalg.solve(A, b)
        paso = 1.0
        for _ in range(30):
            cand = beta + paso * (nuevo - beta)
            eta_c = _eta(X, cand) + offset
            mu_c = np.exp(np.clip(eta_c, -50, 50))
            dev_c = _devianza(y, mu_c, familia)
            if np.isfinite(dev_c) and dev_c <= dev * (1 + 1e-12):
                break
            paso /= 2
        cambio = abs(dev - dev_c) / max(abs(dev_c), 1e-12)
        beta, eta, mu, dev = cand, eta_c, mu_c, dev_c
        if cambio < tol:
            convergio = True
            break
    w = mu if familia == 'poisson' else np.ones_like(mu)
    A = _xtwx(X, w) + ridge * np.eye(p)
    r = (y - mu) if familia == 'poisson' else (y - mu) / mu
    codes, uniq = pd.factorize(pd.Series(cluster).astype(str))
    G = len(uniq)
    M = sparse.csc_matrix((np.ones(len(codes)), (codes, np.arange(len(codes)))), shape=(G, len(codes)))
    S = np.zeros((G, p))
    for i in range(0, X.shape[0], BLOQUE):
        S += M[:, i:i + BLOQUE] @ (X[i:i + BLOQUE].astype(np.float64) * r[i:i + BLOQUE, None])
    B = S.T @ S * G / (G - 1)
    Ainv = np.linalg.inv(A)
    V = Ainv @ B @ Ainv
    se = np.sqrt(np.clip(np.diag(V), 0, None))
    return dict(beta=beta, se=se, iteraciones=it, convergio=convergio, devianza=float(dev), mu=mu, clusters=G)


def txt(s: pd.Series) -> np.ndarray:
    """Texto con 'NA' para los faltantes (pandas 3 conserva NaN al convertir a str)."""
    return s.astype(object).where(s.notna(), 'NA').map(str).to_numpy(dtype=object)


def disenar(df, categoricas, referencias, continuas=()):
    """Matriz densa float32: intercepto, indicadores (sin el nivel de referencia) y continuas."""
    cols, nombres = [np.ones(len(df), np.float32)], ['intercepto']
    for c in categoricas:
        v = txt(df[c])
        niveles = sorted(set(v) - {referencias[c]})
        for lv in niveles:
            ind = (v == lv)
            if ind.sum() == 0:
                continue
            cols.append(ind.astype(np.float32))
            nombres.append(f'{c}={lv}')
    for c in continuas:
        cols.append(df[c].values.astype(np.float32))
        nombres.append(c)
    return np.column_stack(cols), nombres
