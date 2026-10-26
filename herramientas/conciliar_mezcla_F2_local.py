"""Concilia componentes y parámetros publicados de F2 sin ajuste ni scoring."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd

BASE = R / 'privado/semana2'; OUT = BASE / 'mision017_fase2/conciliacion_mezcla_F2_v3'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
rel = lambda p: p.relative_to(ROOT).as_posix()

def main():
    assert not OUT.exists()
    files = {
        'A1_corrected': BASE / 'claude_validacion_nocturna_20261023/A1fixF1b3n_2025.csv',
        'T2b_v1': BASE / 'claude_ml_independiente_20261023/prediccion_2025_mlind.csv',
        'mixture_v1': BASE / 'claude_ml_independiente_20261023/mezcla50_designada_mlind_2025.csv',
        'F2': BASE / 'claude_mision017_20261025/F2_ncb_previos_2025.csv',
        'F2_rounded_parameters': ROOT / 'Hackaton/Semana 2/Claude/mision017_20261025/F2_info.json',
        'global_level_receipt': BASE / 'claude_validacion_nocturna_20261023/sonda_global/resultado.json',
        'original_A1_2024': BASE / 'claude_validacion_nocturna_20261023/predicciones_2024.parquet',
        'recipe_corrected_A1': ROOT / 'Hackaton/Semana 2/Claude/validacion_nocturna_20261023/codigo/evaluar_final.py',
        'original_F2_denominator_code': ROOT / 'Hackaton/Semana 2/Claude/mision017_20261025/codigo/etiquetas.py',
        'previous_denominator_diagnostic': BASE / 'mision017_fase2/conciliacion_mezcla_F2_v2/report.json',
    }
    frames = {name: pd.read_csv(files[name], dtype={'row_id': str}) for name in ['A1_corrected', 'T2b_v1', 'mixture_v1', 'F2']}
    ref = frames['mixture_v1']
    for f in frames.values():
        assert list(f) == ['row_id', 'prediction'] and len(f) == 209063 and f.row_id.is_unique
        assert np.array_equal(f.row_id, ref.row_id) and np.isfinite(f.prediction).all() and f.prediction.gt(0).all()
    assert sha(files['mixture_v1']) == '12831ef4a05c1773824abe5fa139d9503dd2989b4874e7d93cfc000406cfdb4a'
    info = read(files['F2_rounded_parameters']); assert sha(files['F2']) == info['sha256']
    expected = .5 * frames['A1_corrected'].prediction.to_numpy() + .5 * frames['T2b_v1'].prediction.to_numpy()
    difference = expected - ref.prediction.to_numpy()
    assert np.abs(difference).max() < 5.00001e-7
    # Independent decimal check against the six-decimal CSV quantization.
    samples = []
    for index in [0, 1, 13, 99, 1000, 10000, 99999, 150000, 209062]:
        a = Decimal(str(frames['A1_corrected'].prediction.iloc[index]))
        t = Decimal(str(frames['T2b_v1'].prediction.iloc[index]))
        m = Decimal(str(ref.prediction.iloc[index]))
        error = abs((a + t) / 2 - m)
        assert error <= Decimal('0.000000500001')
        samples.append({'row_id': ref.row_id.iloc[index], 'decimal_abs_error': str(error)})
    raw = ROOT / 'Hackaton/Semana 2/Datos/emerging'
    portfolio = []
    for line in ['motor', 'buildings', 'contents']:
        path = raw / f'test_{line}.parquet'; files[f'portfolio_{line}'] = path
        cols = ['row_id', 'customer_id', 'new_business', 'exposure', 'period_start', 'period_end']
        if line == 'motor': cols += ['ncb_years']
        f = pd.read_parquet(path, columns=cols); f['line'] = line
        portfolio.append(f)
    files['customer_covariates'] = raw / 'customers.parquet'
    customers = pd.read_parquet(files['customer_covariates'], columns=['customer_id', 'prior_claims_5y'])
    f = ref[['row_id']].merge(pd.concat(portfolio, ignore_index=True), on='row_id', validate='one_to_one')
    f = f.merge(customers, on='customer_id', validate='many_to_one')
    assert len(f) == len(ref) and np.array_equal(f.row_id, ref.row_id)
    cells = (f.line + '_' + f.new_business.astype(int).astype(str)).to_numpy()
    ncb = pd.cut(f.ncb_years.fillna(0), [-1, 0, 2, 5, 9, 99], labels=['0', '1-2', '3-5', '6-9', '10+']).astype(str)
    prior = np.minimum(f.prior_claims_5y.fillna(0).to_numpy(), 2).astype(int).astype(str)
    g = read(files['global_level_receipt'])['c_final_exacto']
    base = ref.prediction.to_numpy() * g
    assert abs(base.sum() - info['total_F']) < .02
    observations = []
    for exposure_name, exposure in [
        ('provided', f.exposure.to_numpy(float)),
        ('calendar_inclusive_rounded4', (((pd.to_datetime(f.period_end) - pd.to_datetime(f.period_start)).dt.days + 1) / 365).round(4).to_numpy()),
        ('original_F2_calendar_inclusive_full_precision', (((pd.to_datetime(f.period_end) - pd.to_datetime(f.period_start)).dt.days + 1) / 365).to_numpy())]:
        pred = base.copy()
        for factors, keys in [(info['factores_ncb'], ncb), (info['factores_previos'], prior)]:
            factor = np.array([factors.get(c + '|' + key, 1.) for c, key in zip(cells, keys)])
            prev = pred.copy(); pred *= factor
            for c in np.unique(cells):
                mask = cells == c; pred[mask] *= prev[mask].sum() / pred[mask].sum()
        for cell, power in info['forma'].items():
            mask = cells == cell; e = exposure[mask]; assert (e > 0).all()
            rate = pred[mask] / e; mean = pred[mask].sum() / e.sum()
            shape = e * mean * (rate / mean) ** power
            pred[mask] = shape * pred[mask].sum() / shape.sum()
        pred *= np.array([info['razon_nivel'][c] for c in cells])
        actual = frames['F2'].prediction.to_numpy(); error = np.abs(pred - actual)
        # Published effects/level ratios are rounded to four decimals. This is
        # a deliberately approximate check, not a bit-exact parameter replay.
        within = error <= .0007 * actual + 5e-6
        observations.append({'exposure_definition': exposure_name, 'rows_within_published_rounding_envelope': int(within.sum()),
            'max_abs_error': float(error.max()), 'max_relative_error': float(np.max(error / actual)),
            'median_relative_error': float(np.median(error / actual)), 'total': float(pred.sum()),
            'approximate_only': True, 'bit_exact_replay': False})
    old = pd.read_parquet(files['original_A1_2024'])
    needed = [f'lg_A1fixF1b3_{line}_em.parquet' for line in ['motor', 'buildings', 'contents']]
    # Inventory only within this workspace. Absence here says nothing about
    # historical cloud sessions or another person's live environment.
    hits = read(files['previous_denominator_diagnostic'])['bounded_workspace_inventory']
    assert sorted(hits) == sorted(needed)
    assert not any(hits.values())
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'purpose': 'Component lineage and artifact reproducibility; no new predictive comparison',
        'rows': len(ref), 'sources': {name: {'path': rel(path), 'sha256': sha(path)} for name, path in files.items()},
        'mixture': {'formula': '0.5*A1fixF1b3n + 0.5*T2b_v1', 'max_abs_CSV_rounding_error': float(np.abs(difference).max()),
            'decimal_checks': samples, 'author_components': 'Claude', 'review_author': 'Codex'},
        'F2_published_rounded_parameter_reconstruction': observations,
        'F2_exact_historical_replay_established': False,
        'failed_prior_control': {'path': rel(BASE / 'mision017_fase2/conciliacion_mezcla_F2_v1_fallida/failure.json'),
            'explanation': 'The prior version assumed both exposure definitions would meet the rounded-parameter envelope. That assertion failed. This revision records the discrepancy; it does not certify a failed reconstruction or relax a model admission gate.'},
        'missing_exact_F2_replay_evidence': ['Unrounded NCB/prior effects and per-cell level ratios, or exact historical input frame to reproduce them',
            'Corrected A1 three-seed historical raw relativities or saved source models for 2023 and 2024, with matching matrices and provenance'],
        'original_A1_2024_columns': list(old), 'original_A1_2024_is_not_corrected_A1': True,
        'bounded_workspace_inventory': hits, '2024_open': True, '2024_is_adaptive_development': True,
        'new_price_fits': 0, 'new_C0_fits': 0, 'new_model_inferences': 0, 'new_scores': 0, 'new_submission_CSV_written': False,
        'new_submissions': 0, 'B00_preserved': True, 'all_alternatives_preserved': True,
        'goal_achieved': False, 'code_sha256': sha(Path(__file__))}
    OUT.mkdir(parents=True); (OUT / 'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'mixture_max_abs_error': result['mixture']['max_abs_CSV_rounding_error'],
        'approximate_F2_reconstruction': observations, 'exact_F2_historical_replay_established': False,
        'new_fits': 0, 'new_scores': 0, 'new_submissions': 0}))

if __name__ == '__main__':
    main()
