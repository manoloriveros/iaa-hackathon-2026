"""Vetos pendientes del candidato nuevo; reutiliza pesos y modelos guardados."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'FSp_REN_G3_prod_contraste_20261026_v1'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


engine = load('RFS_proxy_veto_math', R / 'herramientas/contrastar_FSp_REN_contra_G3_v2.py')
w = engine.w; unit = engine.unit


def null(y, weight):
    value = float(8 * (np.sqrt(np.dot(weight, y) * weight.sum()) - np.dot(weight, np.sqrt(y))))
    other = float(np.sum(weight * unit(y, np.full(len(y), np.average(y, weights=weight)))))
    assert abs(value - other) < 1e-6
    return value


def G3_proxy(f, stages):
    result = f.A1.to_numpy(float).copy()
    for stage in stages:
        labels = f[stage['variable']].astype('string').fillna('__MISSING__').astype(str)
        factor = labels.map(stage['factors']).fillna(1.).to_numpy(float)
        previous = result.copy()
        for nb in [0, 1]:
            mask = f.new_business.eq(nb).to_numpy(); assert mask.any()
            norm = np.sum(previous[mask] * factor[mask]) / np.sum(previous[mask])
            result[mask] = previous[mask] * factor[mask] / norm
    return result


def main():
    resultpath = OUT / 'additional_veto_points.json'; assert not resultpath.exists()
    planpath = R / 'registro/semana2_mision017_FSp_REN_G3_prod_plan_v1.json'
    plan = w.read(planpath); pre = w.read(OUT / 'preflight.json')
    assert 'additional_veto' in plan['criterion']
    weightpath = BASE / 'estimando_cartera2025_v3/weights.parquet'
    a1path = BASE.parent / 'claude_validacion_nocturna_20261023/predicciones_2024.parquet'
    sources = [Path(__file__), planpath, OUT / 'report.json', OUT / 'oof_2023_2024.parquet', weightpath, a1path]
    p = pd.read_parquet(OUT / 'oof_2023_2024.parquet')
    p = p.merge(pd.read_parquet(weightpath, columns=['row_id', 'weight']), on='row_id', validate='one_to_one')
    assert len(p) == 109296 and p.weight.gt(0).all()
    y = p.T0.to_numpy(float); weights = p.weight.to_numpy(float); dd = null(y, weights)
    weighted = float(np.dot(weights, unit(y, p.G3.to_numpy()) - unit(y, p.RFS1.to_numpy())) / dd)
    for col in ['G3', 'RFS1']:
        assert abs(np.average(unit(y, p[col]), weights=weights) - mean_tweedie_deviance(y, p[col], power=1.5, sample_weight=weights)) < 1e-7
    proxy = p.loc[p.year.eq(2024)].merge(pd.read_parquet(a1path, columns=['row_id', 'A1']), on='row_id', validate='one_to_one')
    assert len(proxy) == 59202
    proxy['A1_G3'] = proxy.A1; proxy['A1_G3_RFS1P'] = proxy.A1
    for scope in pre['scopes']:
        line, held = scope['line'], scope['held']
        idx = proxy.index[proxy.line.eq(line) & proxy.fold.eq(held)]
        t = proxy.loc[idx].copy()
        f = pd.read_parquet(ROOT / scope['input']).set_index('row_id')
        for col in f:
            if col not in t: t[col] = f.loc[t.row_id, col].to_numpy()
        if line != 'buildings':
            stagepath = BASE / f'tanda10_factores_20261026_v1/learning_{line}_fold{held}.json'
            covpath = BASE / f'tanda10_factores_20261026_v1/covariates_{line}.parquet'
            sources += [stagepath, covpath]
            cov = pd.read_parquet(covpath).set_index('row_id')
            for col in cov: t[col] = cov.loc[t.row_id, col].to_numpy()
            t['baseline_G3'] = G3_proxy(t, w.read(stagepath)['stages'])
        else:
            t['baseline_G3'] = t.A1
        # The shared application expects both years. Its 2024 operation is
        # reproduced directly here, without fabricating2023rows or estimating.
        learned = OUT / f'learning_{line}_fold{held}.json'; sources += [learned, ROOT / scope['input']]
        a = w.read(learned); perils = pre['perils'][line]
        risk = sum(a['perils'][q]['kappa'] * t['f_' + q].to_numpy() * t['s_' + q].to_numpy() * t['q_' + q].to_numpy() for q in perils)
        m = t.baseline_G3.to_numpy().copy(); mask = t.new_business.eq(0).to_numpy()
        factor = (risk[mask] / t.unshaped_T2b.to_numpy()[mask]) ** engine.WEIGHTS[line]
        m[mask] *= factor * m[mask].sum() / np.dot(m[mask], factor)
        assert np.array_equal(m[~mask], t.baseline_G3.to_numpy()[~mask])
        proxy.loc[idx, 'A1_G3'] = t.baseline_G3.to_numpy(); proxy.loc[idx, 'A1_G3_RFS1P'] = m
    yy = proxy.T0.to_numpy(); ww = proxy.weight.to_numpy(); nn = null(yy, ww)
    original = unit(yy, proxy.A1.to_numpy())
    values = {col: float(np.dot(ww, original - unit(yy, proxy[col].to_numpy())) / nn) for col in ['A1_G3', 'A1_G3_RFS1P']}
    for col in ['A1', 'A1_G3', 'A1_G3_RFS1P']:
        assert abs(np.average(unit(yy, proxy[col]), weights=ww) - mean_tweedie_deviance(yy, proxy[col], power=1.5, sample_weight=ww)) < 1e-7
    cohort = pd.read_parquet(BASE / 'renovacion_fsp_recepcion_20261026_v1/cohort_2025.parquet')
    composition = {'historical_rows': len(p), 'historical_REN_rows': int(p.new_business.eq(0).sum()),
                   'test_rows': len(cohort), 'test_REN_rows': int(cohort.new_business.eq(0).sum()),
                   'test_NB_fraction': float(cohort.new_business.mean())}
    before = {w.rel(path): w.sha(path) for path in sources}
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
              'weighted2025_incremental_delta_vs_G3': weighted,
              'A1_original2024_weighted_deltas': values,
              'incremental_RFS1P_on_G3_A1_proxy': values['A1_G3_RFS1P'] - values['A1_G3'],
              'additional_veto_points': {'weighted2025_point_positive': weighted > 0,
                                          'original_A1_2024_proxy_not_negative': values['A1_G3_RFS1P'] >= 0},
              'composition': composition, 'weighted_primary_ESS_previously_failed_remains_failed': True,
              'points_only_no_new_bootstrap_or_domain_classifier': True,
              'original_A1_proxy_not_corrected_A1_or_complete_F3c': True,
              'new_model_fits': 0, 'new_C0_fits': 0, 'new_parameter_estimates': 0,
              'replayed_G3_prediction_only_normalizers': 40, 'new_FSp_proxy_prediction_only_normalizers': 30,
              'new_test_prices': 0, 'new_submissions': 0, 'sources': before,
              'no_promotion_or_criterion_change': True}
    resultpath.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    proxy[['row_id', 'A1', 'A1_G3', 'A1_G3_RFS1P']].to_parquet(OUT / 'A1_original2024_proxy_prices.parquet', index=False)
    print(json.dumps({k:v for k,v in report.items() if k not in ['sources']}, ensure_ascii=True))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); main()
