"""Diagnóstico acotado de199discrepancias; no cambia candidato ni precios."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'; PROTO = BASE / 'F3c_FSp_REN_prototipo_20261026_v1'
OUT = BASE / 'FSp_historia_compatibilidad_20261026_v1'
RAW = ROOT / 'Hackaton/Semana 2/Datos/emerging'
PLAN = R / 'registro/semana2_mision017_FSp_historia_compatibilidad_plan_v1.json'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import lightgbm as lgb


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


prototype = load('prototype_history_wrapper', R / 'herramientas/preparar_prototipo_F3c_FSp_REN.py')
w = prototype.w


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')


def main():
    assert not OUT.exists() and not PLAN.exists(); OUT.mkdir()
    proto = w.read(PROTO / 'report.json'); pre = w.read(PROTO / 'preflight.json')
    rates = pd.read_parquet(PROTO / 'annual_T2b_REN_2025.parquet').set_index('row_id')
    oldcsv = ROOT / pre['published_T2b_CSV']; old = pd.read_csv(oldcsv, dtype={'row_id': str}).set_index('row_id')
    claimpath = RAW / 'claims.parquet'
    claims = pd.read_parquet(claimpath, columns=['policy_id', 'line', 'report_date'])
    claims['report_date'] = pd.to_datetime(claims.report_date); assert claims.report_date.le('2024-12-31').all()
    paths = [Path(__file__), Path(prototype.__file__), PROTO / 'report.json', PROTO / 'annual_T2b_REN_2025.parquet', oldcsv, claimpath]
    maps = []
    for line in ['motor', 'buildings', 'contents']:
        for prefix in ['policies', 'test']:
            path = RAW / f'{prefix}_{line}.parquet'; paths.append(path)
            f = pd.read_parquet(path, columns=['policy_id', 'customer_id']); f['line'] = line; maps.append(f)
    mapping = pd.concat(maps, ignore_index=True).drop_duplicates(); assert not mapping.duplicated(['policy_id', 'line']).any()
    client_claims = claims.merge(mapping, on=['policy_id', 'line'], how='inner', validate='many_to_one')
    batches = []; caseframes = []
    for comparison in proto['historical_T2b_replay_and_future_shuffle']:
        line = comparison['line']; rate = rates.loc[rates.line.eq(line)]
        predicted = comparison['legacy_T2b_level_for_comparison_only'] * rate.annual_T2b.to_numpy() * rate.exposure_original.to_numpy()
        err = old.loc[rate.index, 'prediction'].to_numpy() - predicted
        ids = rate.index[np.abs(err) > 1e-6]
        matrixpath, rowpath, _ = prototype.locations(line); modelpath = BASE / f'linaje_T2b_v1/modelos/prod/T2b_{line}.txt'
        paths += [matrixpath, rowpath, modelpath]
        rows = pd.read_parquet(rowpath); indexed = rows.set_index('row_id'); positions = pd.Series(rows.index, index=rows.row_id).loc[ids].to_numpy()
        frame = pd.read_parquet(matrixpath).iloc[positions].copy().reset_index(drop=True)
        metadata = indexed.loc[ids].reset_index(); assert metadata.year.eq(2025).all() and metadata.new_business.eq(0).all()
        original = frame.copy(deep=True)
        for i in range(len(metadata)):
            end1 = pd.Timestamp(metadata.period_start.iloc[i]); end2 = min(end1, pd.Timestamp('2024-12-31'))
            for field, events, key in [('hist_pol_12m', claims.loc[claims.line.eq(line)], 'policy_id'),
                                        ('hist_cli_12m', client_claims, 'customer_id')]:
                g = events.loc[events[key].eq(metadata[key].iloc[i]), 'report_date']
                h2 = int((g.lt(end2) & g.ge(end2 - pd.Timedelta(days=365))).sum())
                h1 = int((g.lt(end1) & g.ge(end1 - pd.Timedelta(days=365))).sum())
                assert h2 == original[field].iloc[i]
                frame.loc[i, field] = h1
                metadata.loc[i, field + '_H2'] = h2; metadata.loc[i, field + '_H1'] = h1
        history_cols = ['hist_pol_12m', 'hist_cli_12m']
        assert frame.drop(columns=history_cols).equals(original.drop(columns=history_cols))
        metadata['line'] = line; metadata['old_component_price'] = old.loc[ids, 'prediction'].to_numpy()
        metadata['H2_component_price_compatibility_only'] = predicted[np.abs(err) > 1e-6]
        metadata['history_input_changed'] = (frame[history_cols].to_numpy() != original[history_cols].to_numpy()).any(axis=1)
        caseframes.append(metadata)
        batches.append({'line': line, 'frame': frame, 'metadata': metadata, 'model': modelpath,
                        'legacy_level': comparison['legacy_T2b_level_for_comparison_only']})
    cases = pd.concat(caseframes, ignore_index=True); assert len(cases) == 199
    cases.to_parquet(OUT / 'cases_before_inference.parquet', index=False)
    plan = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'hypothesis': 'Legacy T2b compatibility differences may be explained by unbounded-inception history versus the explicit observed-cut historia2. Test only these199rows and keep the prototype unchanged.',
        'configuration': {'rows': 199, 'fields_changed': ['hist_pol_12m', 'hist_cli_12m'],
                          'counterfactual': 'Legacy [period_start-365days,period_start) using only supplied report dates',
                          'retained_prototype': 'Explicit observed-cut [min(period_start,V)-365days,min(period_start,V)), V=2024-12-31',
                          'level_for_comparison': 'Already stored median ratio from prototype diagnostic, not learned again or deployed'},
        'criterion': 'Explain original CSV within1microCU after substituting only history fields. Record unexplained rows; do not change recipe to force a match.',
        'observed_dates': {'max_report_date': str(claims.report_date.max()), 'reports2024_12_31': int(claims.report_date.eq('2024-12-31').sum()),
                           'reports2024_01_01': int(claims.report_date.eq('2024-01-01').sum()),
                           'do_not_infer_an_unobserved_day_is_a_known_zero_or_extend_cutoff': True},
        'budget': {'diagnostic_T2b_inference_rows': 199, 'new_model_fits': 0, 'new_C0_fits': 0,
                   'new_candidate_prices': 0, 'new_candidate_CSVs': 0, 'new_submissions': 0},
        'sources': {w.rel(path): w.sha(path) for path in paths}, 'prototype_not_modified': True, '2024_open': True}
    dump(PLAN, plan)
    body = OUT / 'forum_previo.md'
    body.write_text('Codex. El prototipo conserva199REN cuya relatividad T2b no reproduce el CSV legado tras un único nivel por ramo. '
        'Registro antes de inferir una prueba acotada: solo esas199filas, cambiar únicamente los dos historiales al modo legado que termina '
        'en el inicio de2025, y comprobar si explica el archivo original dentro de1microCU. Se mantienen modelo y demás campos exactos. '
        'La comparación usa el nivel ya guardado para diagnóstico, sin estimarlo otra vez o desplegarlo. '
        'No se modificará el prototipo o el corte conocido para forzar la reproducción. Las fechas aportadas llegan al30/12/2024; '
        'no se presume conocido como cero el tramo posterior al corte ni se amplía su fecha. '
        'Cero ajustes, C0, nuevos CSV/precios candidatos o envíos. Plan: ' + w.rel(PLAN) + '.', encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-MISION017-FSP-HISTORIA-COMPATIBILIDAD-PREVIO',
        '--asunto', 'Compatibilidad del historial legado: prueba acotada de199REN', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': w.sha(PLAN), 'forum': json.loads(response.stdout)})
    results = []
    for batch in batches:
        model = lgb.Booster(model_file=str(batch['model']))
        annual = np.exp(model.predict(prototype.align_matrix(batch['frame'], model), raw_score=True, num_threads=2))
        m = batch['metadata'].copy()
        reconstruction = annual * m.exposure.to_numpy() * batch['legacy_level']
        error = reconstruction - m.old_component_price.to_numpy()
        m['H1_component_price_compatibility_only'] = reconstruction; m['legacy_error_H1'] = error
        m.to_parquet(OUT / f'compatibility_{batch["line"]}.parquet', index=False)
        results.append({'line': batch['line'], 'rows': len(m), 'history_input_changed_rows': int(m.history_input_changed.sum()),
                        'explained_within_1microCU': int((np.abs(error) <= 1e-6).sum()),
                        'max_abs_error_H1': float(np.max(np.abs(error))),
                        'max_abs_error_H2': float(np.max(np.abs(m.H2_component_price_compatibility_only - m.old_component_price)))})
    assert all(w.sha(ROOT / p) == sha for p, sha in plan['sources'].items())
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'results': results,
        'all199explained': sum(x['explained_within_1microCU'] for x in results) == 199,
        'supports_history_window_attribution_not_original_runtime_proof': True,
        'new_model_fits': 0, 'new_C0_fits': 0, 'diagnostic_inference_rows': 199,
        'diagnostic_component_price_reconstructions': 199, 'new_candidate_prices': 0, 'new_CSVs': 0, 'new_submissions': 0,
        'prototype_unchanged_SHA': w.sha(PROTO / 'F3c_FSp_REN_prototipo_2025.csv'), 'plan_sha256': w.sha(PLAN),
        'no_history_mode_selected_by_score_or_legacy_fit': True, '2024_open': True}
    dump(OUT / 'report.json', result)
    print(json.dumps(result, ensure_ascii=True))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); main()
