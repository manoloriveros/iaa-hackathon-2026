"""Coteja gasto fijo por póliza con la lectura anterior prorrateada."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, localcontext
from pathlib import Path
import pandas as pd
from cerrar_pendientes_F3c import ROOT, DATA, read, save, sha, rel


def main(run):
    prior = run / 'veinte_primas_privadas.json'
    source = ROOT / 'Hackaton/Semana 2/Codex/fuentes/pages_response.json'
    references = pd.read_parquet(DATA / 'reference_policies.parquet').set_index('row_id')
    assert len(references) == references.policy_id.nunique() == 20
    expenses = pd.read_parquet(DATA / 'expenses.parquet').set_index('item').emerging
    save(run / 'gasto_fijo_criterio_previo.json', {
        'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Control mecánico de supuestos de las veinte primas; hallazgo posterior a las otras pruebas, sin selección de modelos.',
        'source': rel(source), 'source_sha256': sha(source), 'prior_sha256': sha(prior),
        'expense_parquet_sha256': sha(DATA / 'expenses.parquet'),
        'official_description': 'Items: fixed expense per policy; unit CU. No explicit annual-proration instruction in archived data-description.',
        'criterion': 'Interpretación literal principal:85CUpor póliza de referencia. Preservar85*exposure como sensibilidad de la hipótesis anual previa. Cada referencia es una póliza distinta. No volver a multiplicar Rpor exposición.',
        'checks': 'Dos fórmulas Decimal porfila, identidad de cargas y cotejo float; mismo riesgo/comisiones/impuestos/cat/profit de antes.'})
    out = []
    D = lambda x: Decimal(str(x))
    E = lambda x: D(expenses[x])
    with localcontext() as ctx:
        ctx.prec = 45
        for row in read(prior):
            r = references.loc[row['row_id']]
            risk, old = D(row['risk_period']), D(row['commercial_unrounded'])
            commission = E('commission_' + r.channel)
            cat = E('cat_reinsurance') if r.line in ('buildings', 'contents') else D(0)
            den = 1 - E('variable_expense') - commission - E('premium_tax') - E('target_profit_margin')
            fixed = E('fixed_expense_per_policy')
            price = (risk * (1 + cat) + fixed) / den
            other = old + fixed * (1 - D(row['exposure'])) / den
            identity = risk * (1 + cat) + fixed + price * (1 - den)
            assert abs(other - price) < D('1e-30') and abs(identity - price) < D('1e-30')
            assert abs((float(risk) * (1 + float(cat)) + float(fixed)) / float(den) - float(price)) < 1e-8
            out.append({**row, 'commercial_prorated': row['commercial'],
                'commercial_prorated_unrounded': row['commercial_unrounded'],
                'commercial_unrounded': str(price), 'commercial': str(price.quantize(D('.01'), rounding=ROUND_HALF_UP)),
                'fixed_expense': str(fixed), 'fixed_expense_basis': 'per_policy',
                'increase_over_proration': str(price - old), 'increase_over_proration_pct': float(price / old - 1)})
    save(run / 'veinte_primas_gasto_por_poliza.json', out)
    pd.DataFrame(out).to_csv(run / 'veinte_primas_gasto_por_poliza.csv', index=False)
    summary = []
    baseline = {x['row_id']: D(x['commercial_unrounded']) for x in out if x['model'] == 'F3c' and x['scenario'] == 'nominal'}
    nominal = {}
    for x in out:
        if x['scenario'] == 'nominal':
            nominal[(x['model'], x['row_id'])] = D(x['commercial_unrounded'])
    for (model, scenario), group in pd.DataFrame(out).groupby(['model', 'scenario']):
        vals = [D(v) for v in group.commercial_unrounded]
        diffs = [v / baseline[idx] - 1 for v, idx in zip(vals, group.row_id)]
        own = [v / nominal[(model, idx)] - 1 for v, idx in zip(vals, group.row_id)]
        summary.append({'model': model, 'scenario': scenario, 'records': len(group),
            'total': str(sum((D(v) for v in group.commercial), D(0))), 'unrounded_total': str(sum(vals)),
            'prior_total': str(sum((D(v) for v in group.commercial_prorated), D(0))),
            'references_material_vs_F3c': sum(abs(x) >= D('.1') for x in diffs),
            'max_individual_increase_expense_pct': float(group.increase_over_proration_pct.max()),
            'min_change_vs_F3c': float(min(diffs)), 'max_change_vs_F3c': float(max(diffs)),
            'max_change_vs_own_nominal': float(max(abs(x) for x in own))})
    save(run / 'gasto_por_poliza_resumen.json', summary)
    save(run / 'gasto_por_poliza_verificacion.json', {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'rows': len(out), 'references': 20, 'distinct_policies': 20, 'decimal_two_formulas': True,
        'loading_identity': True, 'float_check': True, 'R_period_not_reannualized': True,
        'new_fits_predictions_or_scores': 0, 'output_sha256': sha(run / 'veinte_primas_gasto_por_poliza.json')})
    print([x for x in summary if x['scenario'] == 'nominal'])


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--run', type=Path, required=True)
    main(p.parse_args().run.resolve())
