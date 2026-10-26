"""Recupera el readout P32 sin repetir las2000réplicas ni ajustar modelos."""
from datetime import datetime, timezone
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('p32_saved_draw_recovery', R/'herramientas/revisar_residuo_fuente_P32.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
w = m.w; np = m.np; pd = m.pd; OUT = m.OUT
DOC = R/'docs/semana2/PRIVADA_P32_ADECUACION_CONDICIONAL_FUENTE.md'


def scalar(value):
    if isinstance(value, np.generic): return value.item()
    raise TypeError('Unsupported result type: '+str(type(value)))


def dump(path, value):
    with path.open('x', encoding='utf8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False, default=scalar)


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not (OUT/'completion_receipt.json').exists()
    assert not (OUT/'report_recovered.json').exists() and not DOC.exists()
    plan = w.read(m.PLAN); assert plan['sources'] == {w.rel(p): w.sha(p) for p in m.paths()}
    assert (OUT/'started.json').exists() and (OUT/'report.json').exists()
    try: w.read(OUT/'report.json')
    except json.JSONDecodeError: pass
    else: raise AssertionError('Do not replace a completed valid original report')
    hashes = {line: w.sha(OUT/(line+'_group_draws.npy')) for line in m.LINES}
    dump(OUT/'serialization_failure_receipt.json', {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'original_partial_report': w.rel(OUT/'report.json'), 'original_partial_report_sha256': w.sha(OUT/'report.json'),
        'original_producer_sha256': w.sha(Path(m.__file__)),
        'observed_error': 'TypeError: Object of type bool is not JSON serializable; result contains NumPy scalar boolean.',
        'all3source_readouts_and_draw_files_saved_before_error': True, 'draw_hashes': hashes,
        'recovery': 'Reconstruct deterministic metadata and quantiles from immutable source inputs and saved2000draws. Regenerate only first4identical seed weights as a replay; no new statistical replicates or refits.'})
    results = []; control = []
    for line in m.LINES:
        rows = pd.read_parquet(m.HOME/f'rows_s1_{line}.parquet', columns=['row_id', 'year', 'new_business', 'T0'])
        part = pd.read_parquet(m.HOME/f'partition_source/folds_{line}.parquet', columns=['row_id', 'source_group', 'internal_validation'])
        x = pd.read_parquet(m.HOME/f'matrix_s1_{line}.parquet', columns=['channel', 'new_business'])
        held = part.internal_validation.to_numpy(bool)
        assert np.array_equal(part.row_id, rows.row_id) and np.array_equal(rows.new_business.astype(float), x.new_business.astype(float))
        z = rows.loc[held].reset_index(drop=True); z['source_group'] = part.loc[held, 'source_group'].to_numpy()
        channel = x.loc[held, 'channel'].astype('string').reset_index(drop=True)
        z['cell'], known = m.classify(z.new_business, channel)
        saved = pd.read_parquet(m.SOURCE/line/'held_predictions.parquet')
        assert np.array_equal(z.row_id, saved.row_id) and np.array_equal(z.year, saved.year)
        for col in ['candidate', 'original_tree']: z[col] = saved[col].to_numpy(float)
        totals, groups = m.aggregate(z); point = m.interaction(totals.sum(axis=0))[0]
        draws = np.load(OUT/(line+'_group_draws.npy'), allow_pickle=False)
        assert draws.shape == (2000, 3) and w.sha(OUT/(line+'_group_draws.npy')) == hashes[line]
        rng = np.random.default_rng(plan['bootstrap']['seed_'+line])
        first4 = rng.multinomial(len(groups), np.full(len(groups), 1/len(groups)), size=4)
        assert np.allclose(m.interaction(first4@totals), draws[:4], rtol=2e-10, atol=2e-13, equal_nan=True)
        np.save(OUT/(line+'_first4_replayed_weights.npy'), first4)
        finite = np.isfinite(draws).all(axis=1); invalid = int((~finite).sum())
        band = np.quantile(draws[:, 2], plan['bootstrap']['quantiles']).tolist() if invalid == 0 else None
        cells = m.cell_readout(z)
        top = z.groupby('source_group').T0.sum().reset_index().sort_values(['T0', 'source_group'], ascending=[False, True]).head(31).source_group
        trimmed = z.loc[~z.source_group.isin(top)]; trim_sums, _ = m.aggregate(trimmed)
        trim = m.interaction(trim_sums.sum(axis=0))[0]; trim_cells = m.cell_readout(trimmed)
        years = []
        for year, frame in z.groupby('year'):
            sums, _ = m.aggregate(frame); pp = m.interaction(sums.sum(axis=0))[0]; cc = m.cell_readout(frame)
            years.append({'year': int(year), 'D': float(pp[2]) if np.isfinite(pp[2]) else None,
                'support_pass': min(c['positive_groups'] for c in cc) >= 30})
        gates = {'pooled_cell_support': min(c['positive_groups'] for c in cells) >= 100,
            'primary_D_material': bool(np.isfinite(point[2]) and abs(point[2]) >= math.log(1.10)),
            'family3_band_excludes_zero': band is not None and (band[0] > 0 or band[1] < 0),
            'GLM_anomaly_larger_than_tree': bool(abs(point[0]) > abs(point[1])),
            'GLM_anomaly_same_D_direction': bool(point[0]*point[2] > 0),
            'at_least3source_years_same_direction': bool(sum(a['support_pass'] and a['D'] is not None and a['D']*point[2] > 0 for a in years) >= 3),
            'after31_cell_support': min(c['positive_groups'] for c in trim_cells) >= 30,
            'after31_D_same_direction_material': bool(np.isfinite(trim[2]) and trim[2]*point[2] > 0 and abs(trim[2]) >= math.log(1.05)),
            'no_invalid_bootstrap_draws': invalid == 0}
        result = {'line': line, 'rows': len(z), 'groups': len(groups), 'cells': cells,
            'unknown_channel_rows': int((~known).sum()), 'unknown_channel_cost': float(z.loc[~known, 'T0'].sum()),
            'logR_GLM': float(point[0]), 'logR_tree': float(point[1]), 'primary_D': float(point[2]),
            'family3_band95_D': band, 'invalid_draws': invalid, 'source_years': years,
            'after31_primary_D': float(trim[2]) if np.isfinite(trim[2]) else None,
            'removed_groups': len(top), 'removed_rows': len(z)-len(trimmed), 'after31_cells': trim_cells,
            'gates': gates, 'mechanism_screen_pass': all(gates.values()), 'draws_sha256': hashes[line]}
        results.append(result); control.append({'line': line, 'first4saved_statistic_draws_replayed': True,
            'all_original2000draws_unchanged': True, 'new_bootstrap_replicates': 0})
    assert plan['sources'] == {w.rel(p): w.sha(p) for p in m.paths()}
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'status': 'P32conditional_source_review_recovered_no_interaction_evidence', 'results': results,
        'source_lines_with_screen': [x['line'] for x in results if x['mechanism_screen_pass']],
        'recovery_controls': control, 'plan_sha256': w.sha(m.PLAN),
        'producer_serialization_failure_preserved': w.rel(OUT/'serialization_failure_receipt.json'),
        'new_model_fits': 0, 'new_C0_fits': 0, 'new_model_inference': 0, 'new_prices': 0,
        'new_target_scores': 0, 'new_bootstrap_replicates_in_recovery': 0,
        'original_source_bootstrap_contrasts': 3, 'original_replicates_each': 2000,
        'new_submissions': 0, 'limits': plan['limits'], '2024_open': True,
        'B00_all_alternatives_preserved': True, 'goal_achieved': False}
    assert not report['source_lines_with_screen']; dump(OUT/'report_recovered.json', report)
    next_unit = ('P33: bounded novelty/support review for a standard target-market newbusiness-by-broker residual interaction, on the original incumbent S2/H1, before any fitting or new held scoring. '
        'P32does not support adding that interaction to source GLMs; do not refit source or reinterpret its nonsignificant tiny contrast as a pass. '
        'Inspect prior P23shared-broker stage, business/credibility recipes and existing target-only cell support by stored outer/transfer training groups. '
        'Distinguish a business-specific adaptation from P23main broker effect; inspect whether pooled-within-target-lines coefficient is justifiable and document its exchangeability assumptions and per-line support separately. '
        'Do not borrow developed-market support, pool perils, regroup folds or relax cell floors. No new target prediction/score or fit in the support review. '
        'If no distinct feasible standard correction is supported, keep the reference and identify another concrete evidence need; do not rescue favorable P30cells. '
        'Any later recipe must freeze objective,comparators,regularization,cost and complete protected flow/forum; B00/F3c/all alternatives and adaptive2024open remain.')
    table = '\n'.join('| '+x['line']+' | '+f'{x["primary_D"]:+.5f}'+' | ['+f'{x["family3_band95_D"][0]:+.5f}; {x["family3_band95_D"][1]:+.5f}'+'] | '+str(x['mechanism_screen_pass'])+' |' for x in results)
    text = '# P32: no hay evidencia para otra interacción en la fuente\n\nCodex, '+report['utc']+'. '
    text += ('Se revisó la adecuación condicional de las predicciones fuente retenidas ya guardadas. El contraste primario compara la interacción residual de negocio/canal del GLM con la del árbol original. '
        'Ningún ramo supera el filtro fijado antes del readout. Los intervalos incluyen cero y las diferencias quedan muy por debajo del umbral descriptivo del10%. '
        'Esto no certifica toda la calibración fuente ni identifica la causa del fallo de transporte.\n\n'
        '| Ramo | Diferencia log-interacción GLM menos árbol | Banda95 de familia3 | Filtro completo |\n|---|---:|---|---|\n'+table+'\n\n'
        'Se conservaron las cuatro celdas y los años fuente, la revisión de soporte, los canales desconocidos y la sensibilidad al retirar31grupos de mayor coste. '
        'No se usó ningún A/E como factor de precio. Las réplicas mantienen juntas las filas del mismo grupo fuente y las dos predicciones en cada contraste. '
        'La fuente y su enlace de observación siguen siendo condicionales; el readout es adaptativo después del adverso de destino.\n\n'
        'Las2000réplicas de cada ramo terminaron, pero el productor falló al exportar un booleano NumPy a JSON. Se conserva el informe parcial y su error. '
        'La recuperación reconstruyó solo metadatos y cuantiles desde las mismas fuentes y arrays guardadas; no repitió remuestreo ni ajustes. '
        'Los hashes de las6000réplicas no cambiaron y se reprodujeron las cuatro primeras multiplicidades de cada semilla como control. '
        'El informe válido se guarda aparte como report_recovered.json; el original parcial no se reescribe.\n\n'
        'Cero ajustes, C0, inferencias, precios, scores destino o envíos nuevos. La revisión no justifica más capacidad o una nueva interacción en fuente. '
        'B00/F3c y todos los modelos se conservan,2024abierto adaptativo; no se acredita mejora privada ni revisión profesional independiente.\n\n'
        'Próximo trabajo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report_recovered.json')+'; '+w.rel(OUT/'serialization_failure_receipt.json')+'.\n')
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P32-RESIDUO-FUENTE-RESULTADO',
        '--asunto', 'P32: no añadir interacción fuente; readout recuperado sin repetir réplicas',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': report['utc'], 'status': report['status'],
        'report': w.rel(OUT/'report_recovered.json'), 'report_sha256': w.sha(OUT/'report_recovered.json'),
        'failure_receipt': w.rel(OUT/'serialization_failure_receipt.json'), 'document': w.rel(DOC),
        'forum': json.loads(posted.stdout), 'next_unit': next_unit,
        'new_model_fits': 0, 'new_C0_fits': 0, 'new_model_inference': 0, 'new_target_scores': 0,
        'new_submissions': 0, 'original_source_bootstrap_contrasts': 3, 'new_bootstrap_replicates_in_recovery': 0,
        'source_interaction_evidence_established': False, 'goal_achieved': False,
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    archive = R/'privado'/('corte_P32_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(m.INDEX, receipt, archive)
    w.update(R/'registro/semana2_mision_privada_actual.json', {'P32': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P32': receipt, 'next_unit': next_unit,
        'last_goal_turn_classification': 'progress: P31bridge compatibility clarified; P32new source conditional-adequacy uncertainty resolved, all source interaction screens failed; serialization repaired using saved draws, no refits/resampling or unsupported submission'}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']; own.update(private_P32=receipt, next_unit=next_unit)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P32: interacción fuente no respaldada, 26 de octubre de2026\n\nCodex, '+report['utc']+'. Contrastes GLM menos árbol pequeños y bandas de familia3incluyen cero; los tres filtros fallan. No más capacidad fuente por este mecanismo. Se conserva el fallo de exportación NumPy; informe recuperado con6000draws ya guardados, sin remuestrear o ajustar. Cero inferencias/precios/scores destino/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_source_conditional_adequacy_index': w.rel(m.INDEX), 'week_2_private_source_conditional_adequacy_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt)
    print(json.dumps({'closed': True, 'source_lines_with_interaction_evidence': [],
        'new_fits': 0, 'new_bootstrap_replicates_in_recovery': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    with m.threadpool_limits(limits=2): main()
