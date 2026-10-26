"""Replay numérico fuente y cierre P28, sin ajuste o inferencia destino."""
from datetime import datetime, timezone
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('p28_close_numeric', R/'herramientas/fuente_frecuencia_marca_P28.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
OUT = m.OUT; w = m.w; np = m.np; pd = m.pd
INDEX = m.INDEX; DOC = R/'docs/semana2/PRIVADA_P28_FRECUENCIA_MARCA_FUENTE.md'


def reject(*args, **kwargs): raise AssertionError('Learning blocked in P28saved numerical replay')


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not (OUT/'completion_receipt.json').exists()
    raw = w.read(OUT/'report.json'); plan = w.read(m.PLAN)
    assert raw['plan_sha256'] == w.sha(m.PLAN)
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    assert len(list(OUT.glob('*/*/fit_invoked.json'))) == len(list(OUT.glob('*/*/controls.json'))) == 30
    m.coefficients = reject; m.fit = reject; m.p14.fit_preprocessor = reject
    m.PoissonRegressor.fit = reject; m.TweedieRegressor.fit = reject
    checks = []; input_hashes = {}
    for line in m.LINES:
        folder = OUT/line; summary = w.read(folder/'summary.json')
        assert summary['held_predictions_sha256'] == w.sha(folder/'held_predictions.parquet')
        x = pd.read_parquet(m.HOME/f'matrix_s1_{line}.parquet')
        rows = pd.read_parquet(m.HOME/f'rows_s1_{line}.parquet', columns=['row_id', 'T0'])
        part = pd.read_parquet(m.HOME/f'partition_source/folds_{line}.parquet', columns=['row_id', 'source_group', 'internal_validation'])
        count = pd.read_parquet(m.COUNTS/f'counts_{line}.parquet'); link = pd.read_parquet(m.LINKS/f'rkm_links_{line}.parquet')
        held = part.internal_validation.to_numpy(bool); train = ~held
        matrix, names = m.p14.transform(x.loc[held], w.read(folder/'preprocessor.json'))
        new = np.zeros(held.sum()); old = np.zeros(held.sum()); terms = []
        for peril in [z['peril'] for z in w.read(m.P27/'report.json')['by_line_peril'] if z['line'] == line]:
            n = count['N_'+peril].to_numpy(float); cost = count['T0_cents_'+peril].to_numpy(float)/100
            en = link['E_count_rkm_'+peril].to_numpy(float); ec = count['E_cost_'+peril].to_numpy(float)
            sel, ratio, yy, ww = m.p27.transformed_mark(n, cost, en, ec)
            mu = {}
            for family in ['frequency', 'mark']:
                target = folder/f'{line}_{peril}_{family}'
                record = w.read(target/'fit_record.json'); invoked = w.read(target/'fit_invoked.json')
                assert record['model_sha256'] == w.sha(target/'model.json')
                assert record['plan_sha256'] == w.sha(m.PLAN) and names == record['columns']
                assert record['preprocessor_sha256'] == w.sha(folder/'preprocessor.json')
                idx = (en > 0)&train if family == 'frequency' else sel&train
                y = n[idx]/en[idx] if family == 'frequency' else yy[train[sel]]
                weight = en[idx] if family == 'frequency' else ww[train[sel]]
                assert invoked['y_sha256'] == m.array_digest(y) and invoked['weight_sha256'] == m.array_digest(weight)
                assert record['fit_row_digest'] == m.digest(rows.loc[idx, 'row_id'])
                assert record['fit_group_digest'] == m.digest(part.loc[idx, 'source_group'].unique())
                model = w.read(target/'model.json'); mu[family] = m.predict(matrix, model)
                sample = np.unique(np.linspace(0, matrix.shape[0]-1, 32, dtype=int))
                assert np.array_equal(m.predict(matrix[sample[::-1]], model), mu[family][sample[::-1]])
                for name in ['model.json', 'fit_record.json', 'controls.json']:
                    path = target/name; input_hashes[w.rel(path)] = w.sha(path)
            value = ec[held]*mu['frequency']*mu['mark']; terms.append(value); new += value
            constant = w.read(folder/(peril+'_constant.json'))
            rr = ec[sel&train]/en[sel&train]
            lambda0 = math.fsum(n[train].tolist())/math.fsum(en[train].tolist())
            mark0 = math.fsum((cost[sel&train]/np.sqrt(rr)).tolist())/math.fsum((n[sel&train]*np.sqrt(rr)).tolist())
            assert math.isclose(constant['frequency'], lambda0, rel_tol=3e-14)
            assert math.isclose(constant['mark'], mark0, rel_tol=3e-14)
            old += ec[held]*constant['frequency']*constant['mark']
        saved = pd.read_parquet(folder/'held_predictions.parquet')
        assert np.array_equal(saved.row_id, rows.loc[held, 'row_id'])
        assert np.allclose(new, saved.candidate, rtol=3e-15, atol=1e-10)
        assert np.array_equal(old, saved.constant)
        sample = np.unique(np.linspace(0, len(new)-1, 32, dtype=int))
        independent = np.array([math.fsum(z[i] for z in terms) for i in sample])
        assert np.allclose(independent, saved.candidate.to_numpy()[sample], rtol=3e-15, atol=1e-10)
        y = rows.T0.to_numpy(float)[held]
        scalar_losses = {}
        for name, value in [('candidate', new), ('constant', old)]:
            scalar = math.fsum(4*a/math.sqrt(b)-8*math.sqrt(a)+4*math.sqrt(b) for a, b in zip(y, value))/len(y)
            expected = summary[name+'_deviance']; assert math.isclose(scalar, expected, rel_tol=3e-13)
            scalar_losses[name] = scalar
        checks.append({'line': line, 'all_held_rows_saved_JSON_pipeline_replayed': True,
            'scalar_peril_sum_and_deviance_verified': True, 'source_fit_arguments_and_memberships_match': True,
            'max_relative_error': float(np.max(np.abs(new/saved.candidate.to_numpy()-1))),
            'scalar_losses': scalar_losses})
    replay = {'author': 'Codex', 'utc': m.utc(), 'checks': checks, 'input_hashes': input_hashes,
        'learning_blocked': True, 'new_fits': 0, 'new_C0_fits': 0, 'new_target_inference': 0,
        'report_sha256': w.sha(OUT/'report.json'), 'code_sha256': w.sha(Path(__file__))}
    m.dump(OUT/'numerical_replay.json', replay)
    passed = raw['source_gate_all_pass']; now = m.utc()
    next_unit = ('P29: preregister30full-source GLM refits with exact P28features,families,nominal penalties and paired offset formulas, no source hyperparameter/seed/line search. '
        'Fit preprocessing on all source only; scale penalties by the full-source training weights according to frozen P27formula. '
        'Do not refit source C0. Export summed annual frequency*mark rates and original exposure-weighted relative normalization, historical2023/2024only, sourceJSON/gradient/scalar/source-calendar checks. '
        'Legacy three_seed cache name would denote one fixed15peril sum, never3seeds. No target calibration/score,2025inference, finalprice or upload in that unit. '
        'Only later separately preregister whole original50/50S2/H1comparison with all global/NB/cohort/stress gates; no private improvement from source pass.' if passed else
        'Do not refit source full or score target. Review only saved source failure and count-versus-mark attribution under the paired contract before any distinct recipe; no threshold relaxation, perils dropped or opportunistic reweighting.')
    table = '\n'.join(f'| {x["line"]} | {x["candidate_deviance"]:.5f} | {x["constant_deviance"]:.5f} | {100*x["relative_loss_vs_constant"]:+.3f}% | {x["original_tree_deviance_context"]:.5f} |' for x in raw['results'])
    text = '# P28: GLM número/marca, control fuente completado\n\nCodex, '+now+'. '
    text += ('Los30GLM internos terminaron y los tres ramos pasan el veto frente a la referencia constante por peril, bajo el mismo contrato de observación. '
        'No se ha calibrado ni puntuado destino.\n\n' if passed else 'El veto fuente incumple alguna celda; no se permite el refit completo o la evaluación destino.\n\n')
    text += '| Ramo | Desviación GLM | Constante por peril | Cambio relativo | Árbol original, contexto |\n|---|---:|---:|---:|---:|\n'+table+'\n\n'
    text += ('La comparación con árboles se informa completa: autos y edificios mejoran ligeramente en fuente, mientras contenidos empeora. '
        'El criterio preinscrito era la referencia constante bajo el nuevo estimando; no se transforma el contexto de árboles en otra regla posterior ni se rescata solo un ramo. '
        'El éxito fuente no acredita mejora privada ni sustituye los criterios completos de destino.\n\n'
        'Poisson de número y Tweedie1,5de marca usan efectos principales con el preprocesamiento P14aprendido solo en grupos fuente de entrenamiento. '
        'Las respuestas/pesos y la escala de alpha siguen el contrato P27; se retiene la marca cero y no se recortan importes o siniestros. '
        'Se guardó cada JSON antes de controles. Los gradientes, la carga JSON, el orden y el predictor por suma escalar pasaron. '
        'El replay adicional bloqueó aprendizaje y reconstruyó todas las predicciones fuente retenidas, las sumas por peril y la desviación por otro método; verificó también las entradas efectivas y grupos de cada ajuste.\n\n'
        'La protección nueva se refiere al preprocesamiento y coeficientes GLM. Los objetos de observación fuente congelados tienen ancestros comunes que incluyen grupos ahora retenidos; '
        'por ello el control es condicional y adaptativo, no una evaluación de todo el aprendizaje de observación sin esos grupos. '
        'El control de alteración retenida fue del límite de argumentos, sin duplicar30ajustes reales; no se presenta como un replay de aprendizaje numérico independiente. '
        'Los ajustes sintéticos sí ejercieron ambas familias, gradientes por diferencias finitas y las nuevas transformaciones.\n\n'
        'Coste nuevo:30ajustes fuente internos,30constantes de referencia por peril, dos ajustes sintéticos separados. Cero C0nuevo, refits fuente completos, calibraciones o scores destino, inferencias2025, precios finales o envíos. '
        'Los GLM por peril y FS/FSpanteriores se conservan; esta diferencia de contrato no invalida automáticamente sus productos de coste. '
        'Cola última, suficiencia de reservas, fuente2024y maestros sin fecha conservan sus límites. B00/F3c y todas las alternativas permanecen,2024abierto adaptativo. '
        'Revisión propia conforme a la distinción de Gobernanza IAA§2.8y Documentación§3; sin aprobación profesional independiente.\n\n'
        'Próximo trabajo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'numerical_replay.json')+'. Código previo a los ajustes:6c3ef39a.\n')
    assert not DOC.exists(); DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P28-FRECUENCIA-RESULTADO',
        '--asunto', 'P28: GLM fuente supera su referencia constante; replay y límites, sin admisión destino',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': now, 'status': 'P28source_inner_verified_target_pending',
        'source_gate_all_pass': passed, 'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'replay': w.rel(OUT/'numerical_replay.json'), 'replay_sha256': w.sha(OUT/'numerical_replay.json'),
        'document': w.rel(DOC), 'forum': json.loads(posted.stdout), 'new_source_GLM_fits': 30,
        'new_source_baseline_constants': 30, 'new_C0_fits': 0, 'new_target_scores': 0,
        'new_future_inference': 0, 'new_submissions': 0, 'next_unit': next_unit,
        'goal_achieved': False, '2024_open': True, 'B00_all_alternatives_preserved': True}
    archive = R/'privado'/('corte_P28_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    cp = R/'registro/semana2_contadores_propios_actual.json'; counter = w.read(cp); entry = counter['phase2_private_P28_source_pairs']
    assert entry['attempts'] == entry['completed'] == 30 and not entry.get('baseline_constants_counted')
    entry.update(baseline_constants_counted=30, synthetic_GLM_fits_separate=2, replay=receipt['replay'])
    w.update(cp, {'phase2_private_P28_source_pairs': entry, 'cumulative_closed_form_constants': counter['cumulative_closed_form_constants']+30}, archive)
    w.update(INDEX, receipt, archive)
    w.update(R/'registro/semana2_mision_privada_actual.json', {'P28': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P28_source': receipt, 'next_unit': next_unit}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P28_source=receipt, next_unit=next_unit); w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P28: GLM fuente por peril, 26 de octubre de2026\n\nCodex, '+now+'.30GLM internos y30constantes de referencia; veto fuente tres ramos='+str(passed)+'. Replay JSONde todo el flujo retenido y desviación escalar sin ajustes. Cero C0/refits completos/scoredestino/inferencia2025/envíos; ancestros comunes de observación fuente hacen el control condicional. No mejora privada acreditada. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_count_mark_source_index': w.rel(INDEX), 'week_2_private_count_mark_source_report': w.rel(DOC)}, archive)
    m.dump(OUT/'completion_receipt.json', receipt)
    print(json.dumps({'closed': True, 'source_gate_all_pass': passed, 'new_fits_in_replay': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    with m.threadpool_limits(limits=2): main()
