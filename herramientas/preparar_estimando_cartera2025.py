"""Pesos de composición fijados solo con covariables, antes de nuevos resultados."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd

OUT = R / 'privado/semana2/mision017_fase2/estimando_cartera2025_v3'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()

def duration(exposure):
    return np.where(exposure < .5, 'short', np.where(exposure < .9, 'medium', 'long'))

def main():
    assert not OUT.exists(); OUT.mkdir(parents=True)
    path = R / 'privado/semana2/mision017_fase2/tanda2_20261025_v1/oof_2023_2024.parquet'
    sources = [Path(__file__), path]
    # Deliberately do not load historical outcomes or prices to define weights.
    h = pd.read_parquet(path, columns=['row_id', 'line', 'year', 'new_business', 'exposure', 'fold', 'group_id'])
    h['duration'] = duration(h.exposure.to_numpy(float)); h['new_business'] = h.new_business.astype(int)
    future = []
    for line in ['motor', 'buildings', 'contents']:
        p = ROOT / f'Hackaton/Semana 2/Datos/emerging/test_{line}.parquet'; sources.append(p)
        f = pd.read_parquet(p, columns=['row_id', 'new_business', 'period_start', 'period_end'])
        exposure = ((pd.to_datetime(f.period_end) - pd.to_datetime(f.period_start)).dt.days + 1) / 365
        f['line'] = line; f['duration'] = duration(exposure.to_numpy(float)); f['new_business'] = f.new_business.astype(int)
        future.append(f[['row_id', 'line', 'new_business', 'duration']])
    t = pd.concat(future, ignore_index=True); assert len(t) == 209063 and t.row_id.is_unique
    columns = ['line', 'new_business', 'duration']
    counts = t.groupby(columns, observed=True).size().rename('target_rows').reset_index(); counts['target_share'] = counts.target_rows / len(t)
    parts = []; support = []
    for year in [2023, 2024]:
        f = h.loc[h.year.eq(year)].copy(); n = f.groupby(columns, observed=True).size().rename('history_rows').reset_index()
        table = counts.merge(n, on=columns, how='left', validate='one_to_one')
        assert table.history_rows.notna().all() and table.history_rows.gt(0).all(), 'No regrouping or invented support for a missing stratum'
        table['year'] = year; table['weight'] = len(h) * .5 * table.target_share / table.history_rows
        f = f.merge(table[columns + ['weight']], on=columns, validate='many_to_one')
        assert f.weight.notna().all() and f.weight.gt(0).all()
        assert np.isclose(f.weight.sum(), len(h) / 2, rtol=1e-12)
        achieved = f.groupby(columns, observed=True).weight.sum() / f.weight.sum()
        assert np.allclose(achieved.sort_index(), counts.set_index(columns).target_share.sort_index(), rtol=1e-12)
        parts.append(f); support.append(table)
    p = pd.concat(parts, ignore_index=True); assert len(p) == len(h) and p.row_id.is_unique
    grouped = p.groupby('group_id', observed=True).weight.sum().to_numpy(float)
    weight = p.weight.to_numpy(float)
    row_ess = weight.sum() ** 2 / np.sum(weight ** 2); group_ess = grouped.sum() ** 2 / np.sum(grouped ** 2)
    # One check by a different formula: normalized weights and inverse sum squares.
    assert abs(row_ess - 1 / np.sum((weight / weight.sum()) ** 2)) < 1e-8
    eligible = bool(row_ess / len(p) >= .1 and group_ess / len(grouped) >= .1)
    target = OUT / 'weights.parquet'; p.to_parquet(target, index=False)
    tables = pd.concat(support, ignore_index=True); tables.to_csv(OUT / 'support.csv', index=False)
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'purpose': 'A new conditional target2025 estimand for subsequent preregistered recipes, not retroactive admission of failed batches',
        'strata': 'line × new_business × duration, fixed breaks .5 and .9 used in existing project analyses',
        'year_mixture': 'Equal2023/2024, each exactly matched to the known2025target composition',
        'weights_defined_without_labels_or_prices': True, 'history_rows': len(p), 'target_rows': len(t),
        'target_strata': len(counts), 'all_target_strata_supported_in_both_years': True,
        'row_ESS': row_ess, 'row_ESS_fraction': row_ess / len(p),
        'group_ESS': group_ess, 'group_ESS_fraction': group_ess / len(grouped),
        'min_weight': float(weight.min()), 'max_weight': float(weight.max()),
        'proposed_weighted_primary_estimand_eligibility': eligible,
        'unchanged_preflight_gate': 'row_ESS/n>=.1 and group_ESS/groups>=.1',
        'diagnostic_weights_not_a_primary_validation_approval': True,
        'weighted_null_formula_power1_5': '8*(sqrt(sum(w*y)*sum(w))-sum(w*sqrt(y)))',
        'not_established': 'Conditional covariate-shift assumptions, outcome stationarity and fine-grained overlap beyond these strata',
        'sources': {rel(p): sha(p) for p in sources}, 'weights': {'path': rel(target), 'sha256': sha(target)},
        'new_fits': 0, 'new_price_scores': 0, 'new_submissions': 0}
    with (OUT / 'report.json').open('x', encoding='utf8') as f: json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: report[k] for k in ['target_strata', 'row_ESS', 'row_ESS_fraction', 'group_ESS', 'group_ESS_fraction', 'min_weight', 'max_weight', 'proposed_weighted_primary_estimand_eligibility', 'new_fits', 'new_price_scores']}))
    assert eligible, 'Proposed weighted-primary gate still fails; diagnostics preserved, no model or score produced'

if __name__ == '__main__':
    main()
