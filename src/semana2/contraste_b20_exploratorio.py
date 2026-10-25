"""Una sola calibración anidada S/L, sin lectores ni búsqueda de recetas."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import logsumexp

from . import c0_estricto2023 as c0

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('exploratory_b20_frozen_recipe',
                                             REPO / 'src/semana2/entrenar_glm_ridge_coberturas2023.py')
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)
KEY = list(c0.KEY)


def require(ok, message):
    if not bool(ok):
        raise ValueError(message)


def fit_inner(frame, claims, excluded, recipe, source_versions):
    """Todos los objetos aprendidos excluyen los dos folds, también C0."""
    excluded = tuple(sorted(excluded))
    require(len(excluded) == 2 and len(set(excluded)) == 2, 'Dos folds distintos requeridos.')
    metadata = c0._metadata(frame)
    c0.select_scope(metadata.to_dict('records'), excluded)
    report = c0.fit_c0_2023(frame, claims, excluded_folds=excluded, source_versions=source_versions)
    training = frame.loc[~frame.fold.isin(excluded)].copy()
    observed = c0.apply_c0_2023(training, report, excluded_folds=excluded)
    training = training.drop(columns=['e_cost_mix_1.0'], errors='ignore').merge(
        observed[KEY + ['C0']], on=KEY, validate='one_to_one').rename(columns={'C0': 'e_cost_mix_1.0'})
    require(not training.fold.isin(excluded).any(), 'Fold protegido en GLM.')
    with base.u.threadpool_limits(limits=2):
        bundle, receipt = base.fit_ridge(training, 'buildings', excluded[0], recipe)
    signature = {'C0': report['artifact_sha256'], 'transformer_and_GLM': joblib.hash(bundle)}
    receipt.update(excluded_folds=list(excluded), source_versions=source_versions,
                   fit_membership_sha256=report['contract']['fit_membership_sha256'],
                   whole_learned_signature=signature)
    return {'C0': report, 'bundle': bundle, 'receipt': receipt}


def predict_inner(node, periods, excluded):
    require(not periods.empty and periods.fold.isin(excluded).all(), 'Predicción interior fuera de retenidos.')
    require(node['receipt']['excluded_folds'] == sorted(excluded), 'Objeto de otro ámbito.')
    observed = c0.apply_c0_2023(periods, node['C0'], excluded_folds=excluded)
    with base.u.threadpool_limits(limits=2):
        rate = node['bundle']['estimator'].predict(
            node['bundle']['transformer'].transform(periods[node['bundle']['columns']]))
    require(np.isfinite(rate).all() and (rate > 0).all(), 'Tasa interior inválida.')
    result = periods[KEY + ['year', 'fold', 'group_id']].copy()
    result['annual_rate'] = rate
    result = result.merge(observed[KEY + ['C0']], on=KEY, validate='one_to_one')
    return result


def calibrate(y, rate, exposure, settings):
    y, rate, exposure = [np.asarray(x, dtype=float) for x in (y, rate, exposure)]
    require(len(y) > 0 and np.isfinite(y).all() and (y >= 0).all() and y.sum() > 0,
            'Objetivo de calibración inválido.')
    require(np.isfinite(rate).all() and (rate > 0).all()
            and np.isfinite(exposure).all() and (exposure > 0).all(), 'Tasa/C0 inválidos.')
    log_rate = np.log(rate)
    spread = float(np.quantile(log_rate, .8) - np.quantile(log_rate, .2))
    require(spread >= settings['minimum_inner_log_P80_P20'], 'Rango interior insuficiente para identificar pendiente.')
    center = float(np.average(log_rate, weights=exposure))
    z = log_rate - center
    log_y = np.full(len(y), -np.inf)
    log_y[y > 0] = np.log(y[y > 0])
    profile_calls = 0

    def profile(b):
        nonlocal profile_calls
        profile_calls += 1
        log_h = np.log(exposure) + center + b * z
        a = float(logsumexp(log_y - .5 * log_h) - logsumexp(.5 * log_h))
        prediction = np.exp(a + log_h)
        loss = float(base.u.unit_deviance(y, prediction).sum())
        return loss, a

    optimization = minimize_scalar(lambda b: profile(float(b))[0], bounds=(0., 1.), method='bounded',
        options={'xatol': settings['xatol'], 'maxiter': settings['maxiter']})
    require(optimization.success, 'No convergió el ajuste de pendiente.')
    choices = {b: profile(b) for b in [0., 1., float(optimization.x)]}
    best = min(choices, key=lambda b: choices[b][0])
    tolerance = settings['objective_tie_relative'] * max(1., abs(choices[best][0]))
    for boundary in [1., 0.]:
        if choices[boundary][0] <= choices[best][0] + tolerance:
            best = boundary
            break
    loss_L, a_L = choices[1.]
    loss_S, a_S = choices[best]
    require(loss_S <= loss_L + tolerance, 'S no domina su control anidado en ajuste.')
    hL = np.exp(np.log(exposure) + center + z)
    score_L = np.sum(y / np.sqrt(np.exp(a_L) * hL) - np.sqrt(np.exp(a_L) * hL))
    return {'m': center, 'a_L': a_L, 'a_S': a_S, 'b_S': float(best),
            'fit_loss_L': loss_L, 'fit_loss_S': loss_S, 'log_rate_P80_P20': spread,
            'intercept_score_L': float(score_L), 'profile_calls': profile_calls,
            'optimizer_evaluations': int(optimization.nfev)}


def calibration_for_outer(frame, predictions, outer, settings):
    pieces = []
    for inner in range(5):
        if inner == outer:
            continue
        pair = tuple(sorted([outer, inner]))
        rows = predictions[pair].loc[predictions[pair].fold.eq(inner)].copy()
        require(not rows.empty and not rows.fold.eq(outer).any(), 'Ancestro protegido en calibración.')
        pieces.append(rows)
    predicted = pd.concat(pieces, ignore_index=True)
    labels = frame.loc[frame.fold.ne(outer), KEY + ['T0']]
    data = predicted.merge(labels, on=KEY, validate='one_to_one').sort_values(KEY).reset_index(drop=True)
    require(len(data) == len(labels) and not data.fold.eq(outer).any(), 'Calibración exterior incompleta.')
    fit = calibrate(data.T0, data.annual_rate, data.C0, settings)
    fit.update(outer_fold=outer, calibration_rows=len(data), calibration_groups=data.group_id.nunique(),
               calibration_folds=sorted(data.fold.unique().tolist()))
    return fit, data


def apply_calibration(rate, exposure, parameters, arm):
    rate, exposure = np.asarray(rate, float), np.asarray(exposure, float)
    require(arm in ['L', 'S'], 'Brazo desconocido.')
    b = 1. if arm == 'L' else parameters['b_S']
    a = parameters['a_L'] if arm == 'L' else parameters['a_S']
    result = np.exp(a + np.log(exposure) + parameters['m'] + b * (np.log(rate) - parameters['m']))
    require(np.isfinite(result).all() and (result > 0).all(), 'Predicción calibrada inválida.')
    return result
