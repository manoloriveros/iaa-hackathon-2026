"""A1R fuente por outerfold:90fits registrados, puntos finitos por ámbito."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import gc
import importlib.util
import json
import math
import os
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'; BASE = R/'privado/semana2/mision017_fase2'
HOME = BASE/'A1S_nucleo_20261026_v1'; INPUT = BASE/'P50_reporte_agrupado_20261027'
OUT = BASE/'P51_fuente_agrupada_20261027'
PLAN = R/'registro/semana2_fuente_agrupada_privada_plan.json'; INDEX = R/'registro/semana2_fuente_agrupada_privada_actual.json'
DOC = R/'docs/archivo/semana2/PRIVADA_P51_FUENTE_AGRUPADA.md'
sp = importlib.util.spec_from_file_location('p51_existing_source_price_kernel', R/'herramientas/entrenar_nucleo_A1S.py')
old = importlib.util.module_from_spec(sp); sp.loader.exec_module(old)
pp = importlib.util.spec_from_file_location('p51_scoped_reporting_inputs', R/'herramientas/preparar_reporte_agrupado_P50.py')
prep = importlib.util.module_from_spec(pp); pp.loader.exec_module(prep)
w = old.w; np = old.np; pd = old.pd; lgb = old.lgb; ACTIVE_OUTER = None
old.OUT = OUT; old.PLAN = PLAN


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value): return prep.dump(path, value)


def sources():
    d = w.read(INPUT/'report.json'); parent = w.read(prep.PLAN)
    paths = [Path(__file__), Path(old.__file__), Path(prep.__file__), prep.PLAN, INPUT/'report.json', INPUT/'completion_receipt.json',
        INPUT/'synthetic.json', HOME/'partition_source/report.json']
    result = dict(parent['sources']); result.update(d['outputs']); result.update({w.rel(k): w.sha(k) for k in paths})
    return result


def completed_outer(): return sorted(int(x.parent.name.removeprefix('outer')) for x in OUT.glob('outer*/completed.json'))


def state(status, execution):
    archive = R/'privado'/('p51_state_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    attempts = sorted(x.parent.relative_to(OUT).as_posix() for x in OUT.glob('outer*/*/fit_invoked.json'))
    done = sorted(x.parent.relative_to(OUT).as_posix() for x in OUT.glob('outer*/*/fit_record.json'))
    if execution is not None: execution = {**execution, 'author': 'Codex', 'script': w.rel(Path(__file__)), 'kind': 'P51scoped_source_price', 'outer': ACTIVE_OUTER, 'output': w.rel(OUT)}
    current = {'author': 'Codex', 'utc': utc(), 'status': status, 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN),
        'attempted_source_fits': len(attempts), 'completed_source_fits': len(done), 'completed_outer_scopes': completed_outer(),
        'execution': execution, 'new_C0_fits': 0, 'new_target_scores': 0, 'new2025inference': 0, 'new_submissions': 0,
        'next_unit': 'Finish remaining P51outer source checkpoints only; no replay of completed fits or curves. Then separately register complete target comparison and OWNconditional-transfer source/reporting, not copying pooled source objects. No source-pass admission or2025prices.'}
    counts_path = R/'registro/semana2_contadores_propios_actual.json'; counts = w.read(counts_path)
    previous = counts.get('phase2_private_P51_scoped_source', {}).get('counted_fit_keys', []); assert set(previous).issubset(attempts)
    added = len(set(attempts)-set(previous))
    w.update(counts_path, {'as_of_utc': utc(), 'cumulative_price_base_fits': counts['cumulative_price_base_fits']+added,
        'phase2_private_P51_scoped_source': {'counted_fit_keys': attempts, 'attempted': len(attempts), 'completed': len(done), 'new_C0_fits': 0}}, archive)
    w.update(INDEX, current, archive)
    phase_path = R/'registro/semana2_mision017_fase2_actual.json'; phase = w.read(phase_path)
    jobs = [] if execution is None else [execution]
    w.update(phase_path, {'private_P51': current, 'active_jobs': jobs, 'active_execution': execution, 'new_price_fits': phase['new_price_fits']+added, 'next_unit': current['next_unit']}, archive)
    state_path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state_path)['week_2_mission017_phase2_20261025']; own.update(private_P51=current, active_jobs=jobs, next_unit=current['next_unit'])
    w.update(state_path, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': execution}, archive)


old.update_state = state


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase = w.read(R/'registro/semana2_mision017_fase2_actual.json'); assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent = w.read(INPUT/'report.json'); assert parent['primary_cost_CDF_estimators'] == 55 and parent['adverse_cost_CDF_estimators_separate'] == 55
    assert w.read(INPUT/'completion_receipt.json')['report_sha256'] == w.sha(INPUT/'report.json')
    expected = sources(); assert all(w.sha(ROOT/k) == v for k, v in expected.items())
    OUT.mkdir()
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'A1R_scoped_pooled_cost_reporting_source',
        'hypothesis': 'Repair the recovered A1source reporting ancestry within each outer training fold, with unchanged source-safe features/GBMcapacity, so the complete target learner can later be evaluated without a source object already inheriting the held target reports.',
        'source_recipe': 'Exact current A1Ssource feature matrices, source-safe notification history and source-connected groups. Same3seeds11/12/13, original31leafTweedie1.5params. Only monetary observation e_cost is replaced by current own outerP50scoped pooled cost reporting. No extra capacity or new feature/search.',
        'parameters': old.PARAMS, 'seeds': old.SEEDS, 'outer_scopes': list(range(5)),
        'inner_selection': 'Original saved source internal_validation groups. Base log(sum(source_trainingT0)/sum(source_traininge_cost)) excludes inner-held source labels. max4000,patience400, Tweedie metric. Source observation itself includes all source claims: conditional source score, not independent full-source validation.',
        'full_refit': 'All source2021-2024with selected rounds and own full-source init_base. Save model before controls; each actual invocation counted. Model selected with target-training-scoped reporting may never be shared into another outerfold.',
        'application': 'Each full model predicts historical emerging2023/2024only and is centered on sourceexposure_model. All3centered source logrisks averaged geometrically perline; source means/rounds and output hashes retained. No2025inference, target calibration or score.',
        'budget_this_stage': {'pooled_outer_scopes': 5, 'inner_source_fits': 45, 'full_source_refits': 45, 'max_actual_source_fit_calls': 90,
            'source_center_normalizers_separate': 45, 'new_C0_fits': 0, 'new_target_fits': 0, 'new_target_scores': 0, 'new2025inference': 0, 'new_submissions': 0},
        'complete_future_cost_not_hidden': '90fits is ONLY this pooled source stage. Conditional-transfer training requires its OWN5source/reporting scopes, potentially another90sourcefits; final all-trainingproduction would require18more if separately admitted. P50future90wording is stage-local, not a claim that the whole research/delivery chain costs90fits.',
        'finite_work': 'Run one declared outer at a time with run --outer k. Completing18fits is a checkpoint, not whole-stage completion. Resume only saved completed objects; an invoked unsaved fit is a failure needing reconciliation, never automatic refit.',
        'controls': ['P50all-five held-target cost/peril/date poison curves identical, current offset SHA bound to own outer and source row order; no raw held target labels enter this fitting entry point.',
            'Source rows/labels/offsets/group keys and feature blobs fixed; target-training-only effect is through audited own scoped reporting. Save fit payload digests and all source model records.',
            'Real internal-held Tweedie loss by LightGBM, scalar formula and sklearn; source metric cannot promote a candidate.',
            'Full model saved/reloaded/reordered prediction exact; independent tree-leaf sum and source-weighted relative mean1; exposure once in observed source cost.',
            'Each outer complete receipt keeps all9fullmodel centers,3historical aggregate vectors and all18fit checkpoints; no seed/line selection or row removal.'],
        'sources': expected, 'limits': w.read(prep.PLAN)['limits']+['This is a new scoped source approximation, not exact historical F3cidentity or a new source benchmark winner.',
            'No target C0/level/factor learning or public/private improvement established in source stage; complete original gates and conditional-transfer prerequisite remain.'],
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan); body = OUT/'forum_previo.md'
    body.write_text('Codex. P51preinscribe la fuente A1Rpor los cinco ámbitos P50: mismas matrices/historia segura, grupos fuente, tres semillas y parámetros31hojas. Solo cambia la observación monetaria agrupada dentro del entrenamiento exterior.45ajustes internos y45refits completos,90máximo para esta etapa combinada; fuente2023→2024condicional exigiría otros ámbitos propios y potencialmente90fits, más18de producción si se admite después. No se oculta ese coste ni se declara completa la etapa al terminar un fold. Cada invocación se guarda y cuenta; un intento sin modelo detiene la reanudación. La validación interna fuente es condicional porque sus curvas incluyen toda la fuente. Se verifican pérdidas por tres métodos, recarga/orden, hojas, normalización y exposición. Perfiles históricos solamente; cero C0nuevo, calibración o score destino, inferencias2025 o envíos. B00/F3c/adversos conservados;2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P51registered_before_source_fits', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN),
        'forum': prep.post(body, 'COD-S2-20261027-PRIVADA-P51-FUENTE-PREVIO', 'P51: fuente A1Rpor ámbito,90fits explícitos y continuidad por checkpoint')}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps(receipt))


def model_for(folder, params, data, rounds, valid=None, initial_base=None):
    if (folder/'fit_record.json').exists():
        rec = w.read(folder/'fit_record.json'); assert w.sha(folder/'model.txt') == rec['model_sha256']
        return lgb.Booster(model_file=str(folder/'model.txt'))
    assert not (folder/'fit_invoked.json').exists(), 'Invoked unsaved fit: reconcile, do not retry'
    return old.fit_once(folder, params, data, rounds, valid, initial_base)


def apply_full(folder, model, x, rows, target_x, target_rows):
    if (folder/'application.json').exists():
        a = w.read(folder/'application.json'); assert w.sha(folder/'target_components.parquet') == a['target_components_sha256']; return
    raw = model.predict(x, raw_score=True, num_threads=2); exposure = rows.exposure_model.to_numpy(float)
    center = float(old.logsumexp(raw, b=exposure)-np.log(exposure.sum()))
    assert math.isclose(center, math.log(math.fsum((np.exp(raw)*exposure).tolist())/math.fsum(exposure.tolist())), rel_tol=1e-12, abs_tol=1e-12)
    assert abs(np.average(np.exp(raw-center), weights=exposure)-1) < 2e-12
    target_raw = model.predict(target_x, raw_score=True, num_threads=2)
    loaded = lgb.Booster(model_file=str(folder/'model.txt')); take = np.unique(np.linspace(0, len(target_x)-1, 32, dtype=int))
    assert np.array_equal(target_raw[take], loaded.predict(target_x.iloc[take], raw_score=True, num_threads=2))
    assert np.array_equal(target_raw[take[::-1]], loaded.predict(target_x.iloc[take[::-1]], raw_score=True, num_threads=2))
    leaf_error = float(np.max(np.abs(old.leaf_sum(loaded, target_x.iloc[take[:6]])-target_raw[take[:6]]))); assert leaf_error < 1e-10
    rec = w.read(folder/'fit_record.json'); mu = np.exp(raw+np.log(rows.e_cost.to_numpy(float))+rec['initial_base'])
    assert np.isfinite(mu).all() and (mu > 0).all()
    assert np.isfinite(target_raw).all() and np.isfinite(np.exp(target_raw-center)).all()
    f = target_rows[['row_id', 'year', 'is_test']].copy(); f['log_relative_A1R'] = target_raw-center
    assert not f.is_test.any() and f.year.isin([2023, 2024]).all()
    f.to_parquet(folder/'target_components.parquet', index=False)
    dump(folder/'application.json', {'author': 'Codex', 'utc': utc(), 'center': center, 'source_weighted_relative_mean': float(np.average(np.exp(raw-center), weights=exposure)),
        'source_prediction_rows': len(rows), 'historical_target_rows': len(f), 'independent_leaf_sum_max_error': leaf_error,
        'reload_and_order_exact': True, 'target_components_sha256': w.sha(folder/'target_components.parquet'), 'new2025inference': 0})


def run(outer):
    global ACTIVE_OUTER
    ACTIVE_OUTER = outer; plan = w.read(PLAN); assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    assert all(w.sha(ROOT/k) == v for k, v in plan['sources'].items())
    phase = w.read(R/'registro/semana2_mision017_fase2_actual.json'); assert not phase.get('active_jobs') and not phase.get('active_execution')
    folder = OUT/f'outer{outer}'; assert not (folder/'completed.json').exists(), 'Completed outer; do not repeat'
    folder.mkdir(exist_ok=True)
    if not (OUT/'started.json').exists(): dump(OUT/'started.json', {'author': 'Codex', 'utc': utc(), 'pid': os.getpid(), 'script': w.rel(Path(__file__))})
    # Partial previous invocations are not presumed dead/retryable merely from a state file.
    partial = [x for x in folder.glob('*/fit_invoked.json') if not (x.parent/'fit_record.json').exists()]
    assert not partial, 'Reconcile unsaved invoked fits before continuation'
    dump(folder/('execution_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'), {'author': 'Codex', 'utc': utc(), 'pid': os.getpid(), 'outer': outer})
    state('P51source_outer_running', {'pid': os.getpid(), 'outer': outer})
    try:
        for line in old.LINES:
            rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet'); x = pd.read_parquet(HOME/f'matrix_s1_{line}.parquet')
            scope = pd.read_parquet(INPUT/f'outer{outer}/source_{line}.parquet'); part = pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet')
            assert np.array_equal(rows.row_id, scope.row_id) and np.array_equal(rows.row_id, part.row_id) and len(x) == len(rows)
            rows['e_cost'] = scope.e_cost_A1R.to_numpy(); assert rows.e_cost.gt(0).all() and rows.T0.ge(0).all()
            held = part.internal_validation.to_numpy(bool); train = ~held; assert set(part.loc[train, 'source_group']).isdisjoint(set(part.loc[held, 'source_group']))
            target = pd.read_parquet(HOME/f'rows_s2_{line}.parquet', columns=['row_id', 'year', 'is_test'])
            keep = (~target.is_test&target.year.isin([2023, 2024])).to_numpy(); target = target.loc[keep].reset_index(drop=True)
            tx = pd.read_parquet(HOME/f'matrix_s2_{line}.parquet').iloc[np.flatnonzero(keep)].reset_index(drop=True)
            base_inner = float(np.log(rows.loc[train, 'T0'].sum()/rows.loc[train, 'e_cost'].sum())); base_full = float(np.log(rows.T0.sum()/rows.e_cost.sum()))
            components = []
            for seed in old.SEEDS:
                params = {**old.PARAMS, 'seed': seed}; inner = folder/f'{line}_seed{seed}_inner'; full = folder/f'{line}_seed{seed}_full'
                inner.mkdir(exist_ok=True); full.mkdir(exist_ok=True)
                payload = {'outer': outer, 'line': line, 'seed': seed, 'feature_blob_sha256': w.sha(HOME/f'matrix_s1_{line}.parquet'),
                    'source_rows_sha256': w.sha(HOME/f'rows_s1_{line}.parquet'), 'own_scoped_offset_sha256': w.sha(INPUT/f'outer{outer}/source_{line}.parquet'),
                    'outer_curve_sha256': w.sha(INPUT/f'outer{outer}/cost_curves.json'), 'source_partition_sha256': w.sha(HOME/f'partition_source/folds_{line}.parquet'),
                    'no_raw_target_labels_read_in_price_fit_entry': True, 'invariance_source': w.rel(INPUT/f'outer{outer}/scope.json')}
                if not (inner/'payload.json').exists(): dump(inner/'payload.json', payload)
                else: assert w.read(inner/'payload.json') == payload
                dtr = lgb.Dataset(x.loc[train], rows.T0.to_numpy()[train], init_score=np.log(rows.e_cost.to_numpy()[train])+base_inner, free_raw_data=False)
                dva = lgb.Dataset(x.loc[held], rows.T0.to_numpy()[held], init_score=np.log(rows.e_cost.to_numpy()[held])+base_inner, reference=dtr, free_raw_data=False)
                model = model_for(inner, params, dtr, 4000, dva, base_inner)
                old.validate_inner(inner, model, x, rows, held)
                rounds = w.read(inner/'fit_record.json')['best_iteration']; assert 0 < rounds <= 4000
                dfull = lgb.Dataset(x, rows.T0, init_score=np.log(rows.e_cost.to_numpy())+base_full, free_raw_data=False)
                fitted = model_for(full, params, dfull, rounds, None, base_full)
                apply_full(full, fitted, x, rows, tx, target)
                components.append(pd.read_parquet(full/'target_components.parquet'))
                del dtr, dva, dfull, model, fitted; gc.collect()
            for comp in components: assert np.array_equal(comp.row_id, target.row_id)
            result = target.copy(); result['log_relative_A1R'] = np.column_stack([comp.log_relative_A1R.to_numpy() for comp in components]).mean(axis=1)
            result.to_parquet(folder/f'historical_{line}.parquet', index=False)
            print(json.dumps({'outer': outer, 'line': line, 'source_seeds_complete': 3, 'historical_rows': len(result)}), flush=True)
            del rows, x, scope, part, target, tx, components; gc.collect()
        assert all(w.sha(ROOT/k) == v for k, v in plan['sources'].items())
        model_records = list(folder.glob('*/fit_record.json')); assert len(model_records) == 18
        output = {w.rel(k): w.sha(k) for k in folder.glob('historical_*.parquet')}
        dump(folder/'completed.json', {'author': 'Codex', 'utc': utc(), 'outer': outer, 'source_fits': 18,
            'source_fit_records': {w.rel(k): w.sha(k) for k in model_records}, 'outputs': output, 'new_target_scores': 0, 'new2025inference': 0})
        state('P51source_all5_complete_target_validation_pending' if len(completed_outer()) == 5 else 'P51source_partial_checkpoint_target_validation_pending', None)
        print(json.dumps({'outer_complete': outer, 'completed_outer_scopes': completed_outer(), 'actual_fits_this_outer': 18, 'new_target_scores': 0}))
    except BaseException as exc:
        dump(folder/('failure_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'), {'author': 'Codex', 'utc': utc(),
            'exception': type(exc).__name__, 'message': str(exc), 'do_not_auto_refit': True})
        state('P51source_interrupted_reconcile_invocations', None); raise


def checkpoint():
    finished = completed_outer(); assert finished
    current = w.read(INDEX); assert current.get('execution') is None
    text = '# P51: fuente A1Rpor ámbito, avance parcial\n\nCodex, '+utc()+'. Ámbitos completos: '+str(finished)+'. Ajustes reales invocados: '+str(current['attempted_source_fits'])+'; modelos guardados: '+str(current['completed_source_fits'])+'. El contrato mantiene cinco ámbitos y90fits máximos; este checkpoint no reduce ese alcance ni declara validación destino.\n\n'
    text += 'Cada árbol usa su propio reporte P50, matrices e historia segura, grupos fuente y parámetros fijados. Se guardaron modelos antes de controles, métricas internas por tres métodos, recarga/orden/hojas y centros fuente. Solo se aplicaron a histórico2023/2024. La fuente interna es condicional al reporte de toda la fuente; el grupo targetretenido está excluido antes de estimarlo.\n\n'
    text += 'Faltan los ámbitos fuente restantes, calibración/comparación destino completa y la transferencia condicional con sus propias curvas y árboles. Los90fits declarados aquí son solo esta etapa; la transferencia podría requerir90más y producción18si se admite. No se mezcla un componente de otro fold por comodidad, ni se adoptan precios o se gastan envíos. B00/F3c/adversos conservados,2024abierto adaptativo.\n\nPróximo: '+current['next_unit']+'\n'
    DOC.write_text(text, encoding='utf8'); body = OUT/('forum_checkpoint_'+str(len(finished))+'.md'); body.write_text(text, encoding='utf8')
    forum = prep.post(body, 'COD-S2-20261027-PRIVADA-P51-FUENTE-CORTE'+str(len(finished)), 'P51: checkpoint fuente por ámbito, alcance y validación restante explícitos')
    archive = R/'privado'/('corte_P51_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    receipt = {**current, 'document': w.rel(DOC), 'forum': forum, 'goal_achieved': False, 'B00_all_alternatives_preserved': True, '2024_open': True}
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P51': receipt, 'next_unit': current['next_unit']}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P51': receipt}, archive)
    state_path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state_path)['week_2_mission017_phase2_20261025']; own.update(private_P51=receipt)
    w.update(state_path, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P51: fuente A1Rpor ámbito, checkpoint\n\nCodex, '+utc()+'. Ámbitos completos='+str(finished)+'; intentos='+str(current['attempted_source_fits'])+', modelos='+str(current['completed_source_fits'])+'. Sin nuevos C0, scores destino, inferencias2025o envíos. Faltan fuente restante y evaluación completa, no mejora privada acreditada. Informe: '+w.rel(DOC)+'.\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_scoped_A1R_source_index': w.rel(INDEX), 'week_2_private_scoped_A1R_source_report': w.rel(DOC)}, archive)
    dump(OUT/('checkpoint_'+str(len(finished))+'.json'), receipt); print(json.dumps({'checkpoint': finished, 'source_models': current['completed_source_fits'], 'forum': forum}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); a = argparse.ArgumentParser(description=__doc__); a.add_argument('mode', choices=['prepare', 'run', 'checkpoint']); a.add_argument('--outer', type=int, choices=range(5)); args = a.parse_args()
    with old.threadpool_limits(limits=2):
        if args.mode == 'run': assert args.outer is not None; run(args.outer)
        else: {'prepare': prepare, 'checkpoint': checkpoint}[args.mode]()
