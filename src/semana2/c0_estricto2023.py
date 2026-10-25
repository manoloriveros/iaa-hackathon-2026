"""C0 base por ámbito, sin lectores de datos ni punto de entrada de entrenamiento.

No evalúa soporte estadístico ni autoriza usar datos reales. El llamador debe
resolver esas puertas antes de conectar este núcleo a un ensayo del concurso.
"""
from __future__ import annotations

import hashlib
import json
from numbers import Integral
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from .ambitos_c0_b20_2023 import KEY, membership_digest, select_scope

RECIPE = 'C0-B20-2023-rho1-v1'
VALUATION = '2024-12-31'
PERILS = ('accidental_damage', 'escape_of_water', 'fire', 'flood', 'storm', 'subsidence')
META = [*KEY, 'year', 'is_test', 'fold', 'group_id', 'customer_id', 'address_id']


def _require(condition, message):
    if not bool(condition):
        raise ValueError(message)


def _digest(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False,
                     separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _exclusions(folds):
    folds = tuple(folds)
    _require(len(folds) in (1, 2) and len(set(folds)) == len(folds)
             and all(isinstance(x, Integral) and not isinstance(x, bool)
                     and 0 <= x <= 4 for x in folds), 'Excluir uno o dos folds enteros distintos.')
    return tuple(sorted(int(x) for x in folds))


def _metadata(periods):
    _require(set(META).issubset(periods.columns), 'Faltan metadatos de periodos.')
    meta = periods[META].copy()
    _require(meta.notna().all().all(), 'Metadatos ausentes.')
    for field in [*KEY, 'group_id', 'customer_id', 'address_id']:
        _require(meta[field].map(lambda x: isinstance(x, str) and bool(x.strip())).all(),
                 'Identificador no textual o vacío: ' + field)
    _require(meta.market.eq('emerging').all(), 'Solo mercado emerging.')
    _require(meta.year.eq(2023).all(), 'Solo cohorte2023;2024 permanece cerrado.')
    _require(meta.is_test.map(lambda x: isinstance(x, (bool, np.bool_)) and not x).all(),
             'Test prohibido o indicador no booleano.')
    _require(meta.fold.map(lambda x: isinstance(x, Integral) and not isinstance(x, bool)
                          and x in range(5)).all(), 'Fold inválido.')
    # El selector existente comprueba también cruces globales de componentes,
    # clientes y direcciones, antes de seleccionar el ramo.
    return meta


def _dates(values, name):
    result = pd.to_datetime(values, errors='raise')
    _require(result.notna().all() and result.dt.tz is None, 'Fecha inválida: ' + name)
    _require(result.eq(result.dt.normalize()).all(), 'Se requieren fechas sin hora: ' + name)
    return result


def _period_features(periods):
    frame = periods[[*KEY, 'period_start', 'period_end', 'exposure']].copy()
    frame['period_start'] = _dates(frame.period_start, 'period_start')
    frame['period_end'] = _dates(frame.period_end, 'period_end')
    _require(frame.period_start.dt.year.eq(2023).all()
             and frame.period_end.dt.year.eq(2023).all()
             and frame.period_end.ge(frame.period_start).all(), 'Fechas fuera de2023 o invertidas.')
    frame['exposure'] = pd.to_numeric(frame.exposure, errors='raise')
    _require(np.isfinite(frame.exposure).all() and frame.exposure.gt(0).all(),
             'Exposición no positiva o no finita.')
    return frame


def _reporting_base(delay, age, marks):
    """Misma receta histórica de reporte; exclusivamente la marca base rho=1."""
    delay = np.asarray(delay, dtype=int)
    age = np.asarray(age, dtype=int)
    marks = np.asarray(marks, dtype=float)
    _require(len(delay) >= 5, 'Menos de cinco notificaciones; sin fallback protegido.')
    _require((delay >= 0).all() and (age >= delay).all(), 'Retraso/truncamiento imposible.')
    _require(np.isfinite(marks).all() and (marks >= 0).all() and marks.sum() > 0,
             'Marca T0 base inválida.')
    values, events = np.unique(delay, return_counts=True)
    risk = np.array([np.count_nonzero((delay <= value) & (age >= value)) for value in values])
    _require((risk >= events).all(), 'Conjunto de riesgo incoherente.')
    cdf = np.empty(len(values))
    survival = 1.
    for j in range(len(values) - 1, -1, -1):
        cdf[j] = survival
        survival *= 1 - events[j] / risk[j]
    mass = np.maximum(np.diff(np.r_[0., cdf]), 0.)
    _require(abs(mass.sum() - 1) < 1e-10, 'Masa de reporte no normalizada.')
    probability = mass[np.searchsorted(values, delay)] / events[np.searchsorted(values, delay)]
    _require(abs(probability.sum() - 1) < 1e-10, 'Pesos de notificación incoherentes.')
    cost_mass = np.array([mass[j] * marks[delay == value].mean()
                          for j, value in enumerate(values)])
    mean_mark = float(cost_mass.sum())
    return {
        'delay_days': values.tolist(), 'events': events.tolist(), 'risk_set': risk.tolist(),
        'count_cdf': cdf.tolist(), 'count_mass': mass.tolist(),
        'cost_cdf': (np.cumsum(cost_mass) / mean_mark).tolist(),
        'mean_net_mark': mean_mark, 'n': len(delay),
        'max_delay': int(values.max()), 'max_followup': int(age.max()),
        'max_individual_cost_share': float(np.max(probability * marks / mean_mark)),
    }, probability * len(delay)


def _completion(periods, model, kind):
    first_age = (pd.Timestamp(VALUATION) - periods.period_start).dt.days.to_numpy()
    last_age = (pd.Timestamp(VALUATION) - periods.period_end).dt.days.to_numpy()
    support = np.asarray(model['delay_days'])
    curve = np.asarray(model[kind + '_cdf'])
    positions = np.searchsorted(support, np.arange(int(first_age.max()) + 1), side='right') - 1
    daily = np.where(positions >= 0, curve[np.maximum(positions, 0)], 0.)
    integrated = np.r_[0., np.cumsum(daily)]
    q = (integrated[first_age + 1] - integrated[last_age]) / (first_age - last_age + 1)
    _require(np.isfinite(q).all() and (q >= -1e-10).all() and (q <= 1 + 1e-10).all(),
             'Completitud fuera de rango.')
    return np.clip(q, 0, 1)


def fit_c0_2023(periods: pd.DataFrame, claims: pd.DataFrame, *,
                excluded_folds: Sequence[int], source_versions: Mapping[str, str]) -> dict:
    """Aprende curvas, marcas, frecuencias y mezcla solo del ámbito permitido.

    Recibe únicamente una cohorte2023 ya preparada en memoria. Las columnas
    de fechas/costes/exposición protegidas no se leen para ajustar o identificar
    la caché. year/is_test y pertenencias se comprueban en toda la entrada.
    No recibe pendientes de calibración ni factores de reserva: rho queda en1.
    """
    excluded = _exclusions(excluded_folds)
    meta = _metadata(periods)
    fit_rows, _ = select_scope(meta.to_dict('records'), excluded)
    _require(bool(source_versions) and all(isinstance(k, str) and isinstance(v, str)
             and len(v) == 64 and all(c in '0123456789abcdef' for c in v)
             for k, v in source_versions.items()), 'Versiones fuente SHA256 requeridas.')
    fit_keys = pd.MultiIndex.from_tuples([tuple(row[k] for k in KEY) for row in fit_rows])
    period_mask = pd.MultiIndex.from_frame(periods[list(KEY)]).isin(fit_keys)
    fit_periods = _period_features(periods.loc[period_mask]).sort_values(list(KEY)).reset_index(drop=True)
    required = [*KEY, 'claim_id', 'year', 'is_test', 'fold', 'included_in_T0',
                'loss_date', 'report_date', 'T0_cents', 'peril']
    _require(set(required).issubset(claims.columns), 'Faltan columnas de notificaciones.')
    claim_meta = claims[[*KEY, 'claim_id', 'year', 'is_test', 'fold', 'included_in_T0']]
    _require(claim_meta.notna().all().all() and claim_meta.year.eq(2023).all()
             and claim_meta.is_test.map(lambda x: isinstance(x, (bool, np.bool_)) and not x).all()
             and claim_meta.fold.map(lambda x: isinstance(x, Integral) and not isinstance(x, bool)
                                     and x in range(5)).all()
             and claim_meta.included_in_T0.map(lambda x: isinstance(x, (bool, np.bool_)) and x).all(),
             'Notificaciones ajenas a2023, test o no incluidas en T0.')
    _require(claim_meta.claim_id.map(lambda x: isinstance(x, str) and bool(x.strip())).all()
             and not claims.duplicated(['market', 'line', 'claim_id']).any(), 'claim_id inválido/repetido.')
    joined = claim_meta.merge(meta[[*KEY, 'fold']], on=list(KEY), how='left',
                              validate='many_to_one', suffixes=('', '_period'), indicator=True)
    _require(joined['_merge'].eq('both').all() and joined.fold.eq(joined.fold_period).all(),
             'Notificación sin periodo compuesto o fold discrepante.')
    claim_mask = pd.MultiIndex.from_frame(claims[list(KEY)]).isin(fit_keys)
    # La selección precede a toda interpretación de etiquetas, perils o fechas.
    fitted = claims.loc[claim_mask, required].copy().sort_values([*KEY, 'claim_id']).reset_index(drop=True)
    _require(fitted.peril.isin(PERILS).all() and set(fitted.peril) == set(PERILS),
             'Se requieren los seis perils de edificios, sin fallback de otros folds.')
    fitted['loss_date'] = _dates(fitted.loss_date, 'loss_date')
    fitted['report_date'] = _dates(fitted.report_date, 'report_date')
    fitted['T0_cents'] = pd.to_numeric(fitted.T0_cents, errors='raise')
    _require(np.isfinite(fitted.T0_cents).all() and fitted.T0_cents.ge(0).all()
             and fitted.T0_cents.eq(np.floor(fitted.T0_cents)).all(), 'T0 debe estar en centavos enteros no negativos.')
    bounds = fitted.merge(fit_periods[[*KEY, 'period_start', 'period_end']], on=list(KEY), validate='many_to_one')
    _require(bounds.loss_date.ge(bounds.period_start).all() and bounds.loss_date.le(bounds.period_end).all()
             and bounds.report_date.ge(bounds.loss_date).all()
             and bounds.report_date.le(pd.Timestamp(VALUATION)).all(), 'Fecha de siniestro fuera de periodo/corte.')
    curves, weighted_claims, frequencies, levels = {}, [], {}, {}
    for peril in PERILS:
        rows = fitted.loc[fitted.peril.eq(peril)]
        delay = (rows.report_date - rows.loss_date).dt.days.to_numpy()
        age = (pd.Timestamp(VALUATION) - rows.loss_date).dt.days.to_numpy()
        model, weights = _reporting_base(delay, age, rows.T0_cents.to_numpy() / 100)
        denominator = float(np.sum(fit_periods.exposure.to_numpy() * _completion(fit_periods, model, 'count')))
        _require(np.isfinite(denominator) and denominator > 0, 'Denominador C0 nulo/no finito.')
        frequency = len(rows) / denominator
        curves[peril] = model
        frequencies[peril] = {'notifications': len(rows), 'effective_count_exposure': denominator,
                              'frequency': frequency}
        levels[peril] = frequency * model['mean_net_mark']
        for metadata, weight in zip(rows[[*KEY, 'claim_id', 'year', 'fold']].to_dict('records'), weights):
            weighted_claims.append({**metadata, 'peril': peril, 'weight': float(weight)})
    shares = {peril: levels[peril] / sum(levels.values()) for peril in PERILS}
    # Fechas ISO y centavos enteros: identidad estable ante orden y tipos pandas.
    period_payload = [[*[str(row[k]) for k in KEY], row.period_start.isoformat(),
                       row.period_end.isoformat(), float(row.exposure)] for _, row in fit_periods.iterrows()]
    claim_payload = [[*[str(row[k]) for k in KEY], row.claim_id, row.peril,
                      row.loss_date.isoformat(), row.report_date.isoformat(), int(row.T0_cents)]
                     for _, row in fitted.iterrows()]
    cohort = meta.loc[meta.line.eq('buildings')].sort_values(list(KEY)).to_dict('records')
    contract = {'recipe': RECIPE, 'valuation': VALUATION, 'reserve_factor': 1., 'tail_mass': 0.,
                'market': 'emerging', 'line': 'buildings', 'year': 2023,
                'excluded_folds': list(excluded), 'source_versions': dict(sorted(source_versions.items())),
                'fit_membership_sha256': membership_digest(fit_rows),
                'cohort_metadata_sha256': _digest(cohort),
                'training_content_sha256': _digest({'periods': period_payload, 'claims': claim_payload})}
    artifact = {'contract': contract, 'cache_key': _digest(contract), 'cohort_metadata': cohort,
                'curves': curves, 'weighted_claims': weighted_claims, 'frequencies': frequencies,
                'cost_shares': shares,
                'work': {'reporting_fits': 6, 'frequency_constants': 6, 'cost_means_from_reporting': 6,
                         'normalized_mixtures': 1, 'pricing_models': 0, 'calibrators': 0},
                'support_gate_assessed': False,
                'tail_assumption': 'F(max observed delay)=1; ultimate/tail mass not identified.'}
    artifact['artifact_sha256'] = _digest(artifact)
    return artifact


def apply_c0_2023(periods: pd.DataFrame, artifact: dict, *, excluded_folds: Sequence[int]) -> pd.DataFrame:
    """Aplica el objeto congelado y rechaza cachés de otro ámbito o modificadas."""
    excluded = _exclusions(excluded_folds)
    _require(artifact.get('artifact_sha256') == _digest({k: v for k, v in artifact.items()
                                                       if k != 'artifact_sha256'}), 'Objeto C0 modificado.')
    contract = artifact['contract']
    _require(contract['recipe'] == RECIPE and contract['valuation'] == VALUATION
             and contract['reserve_factor'] == 1. and contract['tail_mass'] == 0.
             and contract['excluded_folds'] == list(excluded)
             and artifact['cache_key'] == _digest(contract), 'Caché C0 incompatible con el ámbito solicitado.')
    meta = _metadata(periods)
    _require(meta.line.eq('buildings').all(), 'Aplicación solo edificios.')
    cohort = {tuple(row[k] for k in KEY): row for row in artifact['cohort_metadata']}
    _require(not meta.duplicated(list(KEY)).any()
             and all(cohort.get(tuple(row[k] for k in KEY)) == row for row in meta.to_dict('records')),
             'Pertenencia no registrada en el objeto C0.')
    frame = _period_features(periods)
    result = periods[[*KEY, 'fold']].copy()
    qmix = np.zeros(len(frame))
    for peril in PERILS:
        curve = artifact['curves'][peril]
        result['qN_' + peril] = _completion(frame, curve, 'count')
        result['qC_' + peril] = _completion(frame, curve, 'cost')
        qmix += artifact['cost_shares'][peril] * result['qC_' + peril].to_numpy()
    result['q_cost_mix'] = qmix
    result['C0'] = frame.exposure.to_numpy() * qmix
    _require(np.isfinite(result.C0).all() and result.C0.gt(0).all(), 'C0 no positivo o no finito.')
    return result
