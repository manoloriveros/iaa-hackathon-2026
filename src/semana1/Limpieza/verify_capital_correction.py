"""Verificación íntegra de CAP01; activa el catálogo solo si todos los controles pasan."""
from decimal import Decimal
from pathlib import Path
import html
import json

import correct_capitals as a
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def main():
    out = a.ROOT / json.loads((a.BASE / 'current_capital_correction.json').read_text(encoding='utf-8'))['workspace_relative_run']
    checks = []

    def check(name, passed):
        checks.append({'check': name, 'passed': bool(passed)})
        if not passed:
            a.c.dump(out / 'verification.json', {'passed': False, 'checks': checks})
            raise AssertionError(name)

    protected = json.loads((out / 'protected_hashes_before.json').read_text(encoding='utf-8'))
    check('11_originals_and_6_parent_derivatives_unchanged', len(protected) == 17 and all(
        a.c.digest(a.ROOT / path) == value for path, value in protected.items()))
    check('D32_and_D34_all_manifest_entries_preserved', a.manifest_ok(a.PARENT) and a.manifest_ok(a.REVIEW))
    catalog = json.loads((out / 'dataset_catalog.json').read_text(encoding='utf-8'))
    parent_catalog = json.loads((a.PARENT / 'dataset_catalog.json').read_text(encoding='utf-8'))
    allowlist = pq.read_table(out / 'evidence/approved_cohort.parquet').to_pandas()
    ledger = pq.read_table(out / 'ledger/all_capital_changes.parquet').to_pandas()
    pending = pq.read_table(out / 'tables/pending_capitals.parquet').to_pandas()
    check('catalog_has_exact_original_11_tables', set(catalog) == set(parent_catalog) and len(catalog) == 11)
    check('catalog_all_file_hashes_valid', all(a.c.digest(a.ROOT / e['workspace_relative_path']) == e['sha256'] for e in catalog.values()))
    check('authorized_counts_frozen_and_unique', len(allowlist) == len(ledger) == 2073
        and allowlist.row_id.is_unique and ledger.row_id.is_unique
        and allowlist.groupby('source_table').size().to_dict() == a.EXPECTED
        and set(ledger.row_id) == set(allowlist.row_id))
    selected_ids, deferred_ids = set(), set()
    source_by_line = {}
    for line in ['buildings', 'contents']:
        review = pq.read_table(a.REVIEW / 'tables' / f'extreme_review_{line}.parquet').to_pandas()
        selected_ids.update(review.loc[review.review_route.eq('prior_supported'), 'row_id'])
        deferred_ids.update(review.loc[~review.review_route.eq('prior_supported'), 'row_id'])
        fields = list(dict.fromkeys(['row_id','policy_id','period_start','period_end','sum_insured'] + a.FIELDS[line]))
        source_by_line[line] = pd.concat([pq.read_table(
            a.ROOT / parent_catalog[f'{prefix}_{line}']['workspace_relative_path'], columns=fields).to_pandas()
            for prefix in ['policies', 'test']], ignore_index=True).set_index('row_id')
    check('allowlist_is_exact_D34_prior_supported_set', set(allowlist.row_id) == selected_ids)
    check('1454_other_extreme_rows_stay_pending', len(pending) == 1454 and pending.row_id.is_unique
        and set(pending.row_id) == deferred_ids and not selected_ids.intersection(deferred_ids)
        and pending.status.eq('pending_no_capital_change').all())
    check('consolidated_ledger_uses_only_CAP01', ledger.rule.eq('CAP01').all() and ledger.divisor.eq(1000).all())
    test_ids, actual_changed = [], set()
    for name in a.c.TABLES:
        original_path = a.ROOT / parent_catalog[name]['workspace_relative_path']
        path = a.ROOT / catalog[name]['workspace_relative_path']
        old = pq.read_table(original_path)
        new = pq.read_table(path)
        check(name + ':schema_rows_and_metadata', old.num_rows == new.num_rows and old.schema.equals(new.schema, check_metadata=True))
        if name not in a.EXPECTED:
            check(name + ':motor_byte_identical', a.c.digest(original_path) == a.c.digest(path))
        else:
            untouched = [col for col in old.column_names if col != 'sum_insured']
            check(name + ':every_other_column_identical_including_ID_exposure_premium', all(old[col].equals(new[col]) for col in untouched))
            log = pq.read_table(out / 'ledger' / f'{name}_sum_insured.parquet').to_pandas()
            subset = ledger[ledger.source_table.eq(name)].reset_index(drop=True)
            check(name + ':per_table_and_consolidated_ledger_agree', log.equals(subset))
            before, after = old['sum_insured'].to_numpy(), new['sum_insured'].to_numpy()
            changed = np.flatnonzero(before != after)
            positions = log.source_row.to_numpy(dtype=int)
            row_ids = new['row_id'].to_pylist()
            actual_changed.update(row_ids[i] for i in changed)
            check(name + ':exact_authorized_change_positions', np.array_equal(changed, positions)
                and len(changed) == a.EXPECTED[name] and log.row_id.tolist() == [row_ids[i] for i in changed])
            check(name + ':every_old_value_and_new_value_logged', np.array_equal(before[positions], log.old)
                and np.array_equal(after[positions], log.new))
            check(name + ':every_amount_divided_exactly_by_1000', all(
                Decimal(str(before[i])) / Decimal(1000) == Decimal(str(after[i])) for i in positions))
            restored = after.copy(); restored[positions] = log.old.to_numpy()
            check(name + ':exact_reversal_to_D32', np.array_equal(restored, before))
            second, count = a.apply_frozen(after, positions, log.old.to_numpy(), log.new.to_numpy())
            check(name + ':idempotence_no_second_division', count == 0 and np.array_equal(second, after))
            line = name.split('_',1)[1]
            source = source_by_line[line]
            evidence_ok = True
            for row in log.itertuples(index=False):
                current, ref = source.loc[row.row_id], source.loc[row.prior_row_id]
                evidence_ok &= current.policy_id == ref.policy_id == row.policy_id
                evidence_ok &= ref.sum_insured == row.prior_sum_insured
                evidence_ok &= ref.sum_insured <= (10_000_000 if line == 'buildings' else 1_000_000)
                evidence_ok &= ref.period_end < current.period_start
                evidence_ok &= 1 <= (current.period_start-ref.period_start).days <= 400
                evidence_ok &= .9 <= row.new/ref.sum_insured <= 1.1
                for col in a.FIELDS[line]:
                    x, y = current[col], ref[col]
                    evidence_ok &= pd.notna(x) and pd.notna(y)
                    if pd.isna(x) or pd.isna(y):
                        continue
                    if col == 'construction_type':
                        x, y = str(x).casefold().strip(), str(y).casefold().strip()
                    evidence_ok &= x == y
            check(name + ':every_prior_reference_and_risk_context_rechecked', evidence_ok)
            p = pending[pending.source_table.eq(name)]
            lookup = pd.Series(after, index=row_ids)
            check(name + ':all_unapproved_extremes_unchanged', np.array_equal(lookup.loc[p.row_id].to_numpy(), p.sum_insured.to_numpy()))
        if name.startswith('test_'):
            test_ids.extend(new['row_id'].to_pylist())
    check('total_changed_set_exactly_2073_no_cascading', len(actual_changed) == 2073 and actual_changed == selected_ids)
    check('ledger_2073_positive_finite_new_values', np.isfinite(ledger.new).all() and ledger.new.gt(0).all())
    check('division_function_rejects_conflicting_amount', rejects_conflict())
    for name in set(catalog) - set(a.c.TABLES):
        check(name + ':original_reference_unchanged', catalog[name] == parent_catalog[name])
    sample_ids = pq.read_table(a.ROOT / catalog['sample_submission']['workspace_relative_path'], columns=['row_id']).column(0).to_pylist()
    check('all_626639_test_ids_match_sample_once', len(test_ids) == len(set(test_ids)) == len(sample_ids) == 626639 and set(test_ids) == set(sample_ids))
    summary = pd.read_csv(out / 'tables/change_summary.csv')
    check('summary_reconciles_changes_and_pending', int(summary.changed_rows.sum()) == 2073 and int(summary.other_extreme_pending.sum()) == 1454)
    authorization = json.loads((out / 'authorization.json').read_text(encoding='utf-8'))
    check('explicit_request_preserved', authorization['messages'] == [{'role':'user','content':a.REQUEST}])
    result = {'passed': True, 'checks_count': len(checks), 'checks': checks, 'capital_changes':2073,
        'pending_unchanged':1454, 'originals_modified':False, 'prior_runs_modified':False,
        'scope':'Own technical verification, assisted by AI; operation explicitly authorized by participant; source-unit inference and overall modeling readiness remain separate.'}
    a.c.dump(out / 'verification.json', result)
    render_report(out, summary, ledger, pending, result)
    entries = [{'path': p.relative_to(out).as_posix(), 'bytes': p.stat().st_size, 'sha256': a.c.digest(p)}
               for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    a.c.dump(out / 'manifest.json', {'count':len(entries),'files':entries})
    pointer = {'workspace_relative_run':out.relative_to(a.ROOT).as_posix(), 'status':'verified_CAP01_frozen_cohort',
               'catalog_workspace_relative':(out/'dataset_catalog.json').relative_to(a.ROOT).as_posix(),
               'capital_changes':2073,'pending_capitals':1454,'approved_for_modeling':False}
    a.c.dump(a.BASE / 'current_capital_correction.json', pointer)
    temporary = a.BASE / 'current_dataset.pending.json'
    a.c.dump(temporary, pointer)
    temporary.replace(a.BASE / 'current_dataset.json')
    print(json.dumps({'passed':True,'checks':len(checks),'capital_changes':2073,'pending':1454,'run':str(out)}))


def rejects_conflict():
    try:
        a.apply_frozen(np.array([200.]),np.array([0]),np.array([1000.]),np.array([1.]))
    except ValueError:
        return True
    return False


def render_report(out, summary, ledger, pending, result):
    counts = pending.groupby('review_route').size().rename('pending_rows').reset_index()
    examples = ledger[ledger.row_id.isin(['B02068654','B02774400','C02314938','C01614150'])]
    sections = ['<!doctype html><html lang="es"><meta charset="utf-8"><title>CAP01: corrección de capitales</title>',
      '<style>body{font:16px/1.6 system-ui;max-width:1200px;margin:40px auto;padding:0 24px;color:#182b3c}table{border-collapse:collapse;display:block;overflow:auto;font-size:14px}td,th{padding:10px;border-bottom:1px solid #ddd;text-align:right;white-space:nowrap}th{background:#edf3f8}a{color:#075b9b}</style>',
      '<h1>Corrección CAP01 autorizada: 2.073 capitales /1000</h1>',
      '<p>Se creó una capa nueva sobre D32. La lista prior_supported de D34 quedó congelada: 1.533 filas de entrenamiento y 540 de test. Solo cambia sum_insured en esas filas. Los once originales, D32, D34 y las demás columnas conservan sus valores. Las copias de autos son idénticas byte a byte.</p>',
      '<p>La autorización del participante aprueba la transformación de esta cohorte. La unidad continúa siendo una inferencia del proyecto, sin confirmación del sistema generador ni validación independiente.</p>',
      '<h2>Cambios por tabla</h2>',summary.to_html(index=False),
      '<h2>Ejemplos reales</h2>',examples[['source_table','row_id','policy_id','old','new','prior_row_id','prior_sum_insured']].to_html(index=False),
      '<h2>Capitales pendientes</h2>',counts.to_html(index=False),
      '<p>Se conservaron los 1.454 capitales extremos restantes. No se amplió la lista mediante referencias nuevas creadas por esta corrección. Por ejemplo, C67134620 cambia en su fila C01614150 de 43.500.000 a 43.500 CU; C02237105 conserva 44.400.000 CU y continúa pendiente. Los capitales de B19256617 y el primer capital de C00131038 permanecen sin corregir.</p>',
      '<h2>Bitácora y validación</h2>',
      f'<p>Pasaron {result["checks_count"]} controles técnicos completos: lista exacta, división verificada con aritmética decimal, evidencia anterior, contexto de riesgo, reversión, idempotencia, conservación de todas las demás columnas, pendientes, hashes y cobertura de test.</p>',
      '<p>Cada cambio conserva old/new, posición, fila, póliza, referencia anterior, contexto identificativo, divisor, regla, hash de revisión y autorización. Las bitácoras de identificadores y exposición se heredan de D32 mediante lineage.json. No se cambiaron primas, siniestros o etiquetas; no se entrenó ningún modelo.</p>',
      '<p>current_dataset.json identifica esta versión preparada verificada. No equivale a aprobación completa para modelar: las demás carencias de datos, objetivo y disponibilidad temporal siguen abiertas. Los cortes temporales deben respetar su información disponible, sin expandir la corrección usando periodos posteriores.</p>',
      '<p><a href="ledger/all_capital_changes.csv">Bitácora de los 2.073 cambios CSV</a> · <a href="tables/pending_capitals.csv">Los 1.454 pendientes CSV</a> · <a href="dataset_catalog.json">Catálogo de las once tablas</a> · <a href="verification.json">Verificación</a> · <a href="rules.json">Regla CAP01</a> · <a href="authorization.json">Autorización</a> · <a href="lineage.json">Linaje</a></p></html>']
    (out/'informe.html').write_text('\n'.join(sections),encoding='utf-8')


if __name__ == '__main__':
    main()
