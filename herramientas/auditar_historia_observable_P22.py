"""Distingue historia de siniestros y presencia de pólizas, sin etiquetas ni modelos."""
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
OUT = BASE/'P22_historia_observable_20261026'
PLAN = R/'registro/semana2_historia_observable_privada_plan.json'
INDEX = R/'registro/semana2_historia_observable_privada_actual.json'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
spec = importlib.util.spec_from_file_location('p22_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
LINES = ['motor', 'buildings', 'contents']; HISTORY = ['hist_pol_12m', 'hist_cli_12m']
KEYS = ['row_id', 'policy_id', 'customer_id', 'address_id', 'year', 'period_start', 'period_end', 'new_business', 'is_test']


def dump(path, value):
    with path.open('x', encoding='utf8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def locations(line, market):
    if line == 'buildings':
        directory = BASE/'FSp_edificios_matrices_20261026_v1'
        return directory/f'matrix_{market}_prod.parquet', directory/f'rows_{market}_prod.parquet'
    directory = BASE/'FSp_MC_recuperacion_20261026_v1/matrices'
    return directory/f'matrix_{line}_{market}_prod.parquet', directory/f'rows_{line}_{market}_prod.parquet'


def paths():
    result = [Path(__file__)]
    for line in LINES:
        result.append(BASE/f'linaje_T2b_v1/features_{line}.parquet')
        for market, label in [('source', 's1'), ('target', 's2')]:
            result += list(locations(line, market))
            result += [HOME/f'rows_{label}_{line}.parquet', HOME/f'matrix_{label}_{line}.parquet']
    return result


def check_sources(plan):
    expected = dict(plan['sources']); code = w.rel(Path(__file__))
    if expected[code] != w.sha(Path(__file__)):
        correction = w.read(OUT/'implementation_correction.json')
        assert correction['frozen_plan_sha256'] == w.sha(PLAN)
        assert correction['previous_code_sha256'] == expected[code]
        assert correction['new_code_sha256'] == w.sha(Path(__file__))
        assert correction['forum']['id'] == 'COD-S2-20261026-PRIVADA-P22-ENMIENDA-CLAVES'
        assert all(w.sha(ROOT/p) == h for p, h in correction['additional_sources'].items())
        expected[code] = correction['new_code_sha256']
    assert expected == {w.rel(p): w.sha(p) for p in paths()}


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists(); OUT.mkdir()
    plan = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'hypothesis': 'Una ventana calendario completa y un historial de siniestros cero pueden coexistir con ninguna póliza previa observada. Antes de modificar el modelo, medir si esa representación cambia entre fuente, destino histórico y adquisición2025.',
        'scope': 'Solo covariables: historiales12m restaurados, fechas/IDs de pólizas y años observados A1S; mercados separados, nunca unidos por IDs entre países.',
        'binding': 'Primero comprobar igualdad exacta de los dos historiales destino2023/2024 frente al cache T2b. Si falla, detenerse antes de interpretar2025.',
        'definitions': {
            'policy_no_prior_record': 'f1_anios_observados ==0; cotejar con la primera fecha de póliza observada y known_end=min(period_start,2024-12-31).',
            'client_no_prior_record': 'Ninguna fecha inicial de póliza de ese cliente, en cualquier ramo de este mercado, anterior a known_end. Es presencia histórica en esta base, no prueba de carencia de seguro anterior.',
            'calendar_window': 'known_end-365days >=2021-01-01para fuente, >=2023-01-01para destino; esta condición no prueba cobertura personal completa durante esos365días.',
            'claim_history_states': 'Ausente, cero o positivo; preservar positivos sin póliza anterior visible, sin borrar ni imputar.',
        },
        'tables': 'Por mercado/ramo/año/negocio, y negocio nuevo por broker. Conteos y cruces de presencia observada con historiales12m, sin riesgos, precios o scores nuevos.',
        'decision_rule': 'No enmascarar o añadir variables por defecto. Solo proponer una receta posterior si la procedencia y un fallo concreto lo justifican; distinguir observabilidad de siniestralidad real y del corte de reportes.',
        'limits': ['Las matrices fuente restauradas no son por sí solas el archivo exacto de entrenamiento original T2b.',
            'Primera póliza observada no equivale a exposición continua durante todo el lookback ni a toda experiencia asegurada.',
            'Los maestros sin fecha conservan sus límites de disponibilidad temporal; no se leen resultados2025.',
            'No se repite la compatibilidad de199REN entre historia H1/H2 ni los diagnósticos predictivos anteriores.'],
        'columns': {'restored_matrix': HISTORY, 'row_metadata': KEYS,
            'A1S_matrix': ['channel', 'new_business', 'f1_anios_observados'],
            'legacy_history': ['row_id']+HISTORY},
        'cost': {'model_fits': 0, 'C0_fits': 0, 'model_loading': 0, 'inference': 0, 'scores': 0, 'resampling': 0, 'submissions': 0},
        'sources': {w.rel(p): w.sha(p) for p in paths()},
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    text = ('Codex. Preinscripción P22, solo covariables: cotejar los dos historiales12m restaurados '
        'con el cache T2bhistórico y, si coinciden, cruzar ausente/cero/positivo con presencia '
        'previa observada de póliza/cliente, por mercado, ramo, año y negocio. Revisar también '
        'nuevo/broker2025. Un cero de siniestros no demuestra exposición previa conocida; una '
        'póliza observada tampoco prueba365días continuos. No se imputará ni enmascarará por '
        'defecto y se preservarán casos positivos sin periodo anterior visible. Cero etiquetas '
        'financieras, modelos/C0, inferencias, scores, remuestreos o envíos. No es la prueba '
        'de199REN por fecha de corte, ya cerrada. B00/F3c/alternativas conservados,2024abierto '
        'adaptativo. Plan: '+w.rel(PLAN)+'; SHA '+w.sha(PLAN)+'.\n')
    body = OUT/'forum_previo.md'; body.write_text(text, encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P22-HISTORIA-PREVIO',
        '--asunto', 'P22: distinguir cero siniestros y experiencia observada con covariables',
        '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    dump(INDEX, {'author': 'Codex', 'utc': plan['utc'], 'status': 'P22registered_covariate_audit',
        'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(posted.stdout)})
    print(json.dumps({'prepared': True, 'forum': w.read(INDEX)['forum'], 'new_fits': 0}))


def run():
    assert not (OUT/'report.json').exists()
    plan = w.read(PLAN)
    check_sources(plan)
    io = []
    def read(path, columns):
        f = pd.read_parquet(path, columns=columns)
        io.append({'path': w.rel(path), 'columns': columns, 'rows': len(f)})
        return f
    frames = {}; bindings = []
    for market, label in [('source', 's1'), ('target', 's2')]:
        frames[market] = []
        for line in LINES:
            xp, rp = locations(line, market)
            x = read(xp, HISTORY); rows = read(rp, KEYS)
            hr = read(HOME/f'rows_{label}_{line}.parquet', KEYS)
            hx = read(HOME/f'matrix_{label}_{line}.parquet', ['channel', 'new_business', 'f1_anios_observados'])
            assert len(rows) == len(x) and len(hr) == len(hx)
            assert rows.row_id.is_unique and hr.row_id.is_unique and set(rows.row_id) == set(hr.row_id)
            assert np.array_equal(hr.new_business.astype(bool), hx.new_business.astype(bool))
            for name in ['channel', 'f1_anios_observados']: hr[name] = hx[name].to_numpy()
            hr = hr.set_index('row_id', drop=False).loc[rows.row_id].reset_index(drop=True)
            if market == 'source' and line == 'motor':
                adapter = w.read(OUT/'source_motor_key_preflight.json')
                assert adapter['exact_zfill8_match'] and adapter['all_digit_keys']
                assert adapter['collision_groups'] == 0 and adapter['master_membership_complete']
                # ID01/D32 already applies this same normalization inside source feature joins.
                # Adapt only the temporary audit metadata; no source or model input is edited.
                hr['customer_id'] = hr.customer_id.astype(str).str.zfill(8)
            for key in KEYS:
                assert np.array_equal(hr[key], rows[key]), (market, line, key)
            f = hr.copy(); f['line'] = line
            for name in HISTORY:
                values = x[name].to_numpy(float)
                assert np.isfinite(values[~np.isnan(values)]).all()
                assert (values[~np.isnan(values)] >= 0).all()
                assert np.array_equal(values[~np.isnan(values)], np.round(values[~np.isnan(values)]))
                f[name] = values
            first = f.groupby('policy_id').period_start.min()
            known = pd.to_datetime(f.period_start).clip(upper=pd.Timestamp('2024-12-31'))
            observed_years = ((known-pd.to_datetime(f.policy_id.map(first))).dt.days/365.25).clip(lower=0)
            assert np.array_equal(observed_years.to_numpy(float), f.f1_anios_observados.to_numpy(float))
            f['policy_no_prior'] = f.f1_anios_observados.eq(0)
            f['known_end'] = known
            f['complete_calendar'] = (known-pd.Timedelta(days=365)).ge(pd.Timestamp('2021-01-01' if market == 'source' else '2023-01-01'))
            bindings.append({'market': market, 'line': line, 'rows': len(f),
                'keys_periods_business_exact': True, 'observed_years_reconstructed_exact': True})
            frames[market].append(f)
    # This check precedes all interpretations of future encodings.
    for f in frames['target']:
        line = f.line.iloc[0]
        old = read(BASE/f'linaje_T2b_v1/features_{line}.parquet', ['row_id']+HISTORY).set_index('row_id')
        h = f.loc[f.year.isin([2023, 2024])]
        for name in HISTORY:
            assert np.array_equal(h[name].to_numpy(float), old.loc[h.row_id, name].to_numpy(float), equal_nan=True), (line, name)
    tables = []; cases = []
    for market in ['source', 'target']:
        f = pd.concat(frames[market], ignore_index=True)
        assert f.row_id.is_unique
        first_client = f.groupby('customer_id').period_start.min()
        f['client_no_prior'] = pd.to_datetime(f.customer_id.map(first_client)).ge(f.known_end)
        for (line, year, business), z in f.groupby(['line', 'year', 'new_business'], sort=True):
            selections = [('ALL', z)]
            if bool(business): selections.append(('BROKER', z.loc[z.channel.astype(str).eq('broker')]))
            for channel, g in selections:
                entry = {'market': market, 'line': line, 'year': int(year), 'new_business': bool(business),
                    'channel_scope': channel, 'rows': len(g), 'policy_no_prior': int(g.policy_no_prior.sum()),
                    'client_no_prior': int(g.client_no_prior.sum()), 'calendar_incomplete': int((~g.complete_calendar).sum())}
                for variable, condition in [('hist_pol_12m', 'policy_no_prior'), ('hist_cli_12m', 'client_no_prior')]:
                    value = g[variable]; unknown = g[condition]
                    entry[variable] = {
                        'missing': int(value.isna().sum()), 'zero': int(value.eq(0).sum()), 'positive': int(value.gt(0).sum()),
                        'zero_without_prior_period_record': int((value.eq(0) & unknown).sum()),
                        'positive_without_prior_period_record': int((value.gt(0) & unknown).sum()),
                        'missing_with_prior_period_record': int((value.isna() & ~unknown).sum()),
                        'missing_despite_complete_calendar': int((value.isna() & g.complete_calendar).sum()),
                    }
                    assert entry[variable]['missing']+entry[variable]['zero']+entry[variable]['positive'] == len(g)
                tables.append(entry)
        for line, g in f.groupby('line'):
            cases.append({'market': market, 'line': line,
                'positive_policy_history_without_prior_period_rows': int((g.hist_pol_12m.gt(0) & g.policy_no_prior).sum()),
                'positive_client_history_without_prior_period_rows': int((g.hist_cli_12m.gt(0) & g.client_no_prior).sum()),
                'note': 'Counts preserved; positive known reports need not be erased because an earlier period row is absent.'})
    check_sources(plan)
    dump(OUT/'tables.json', tables); dump(OUT/'bindings.json', bindings)
    dump(OUT/'read_receipt.json', io); dump(OUT/'positive_history_without_period.json', cases)
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'status': 'P22covariate_history_observability_audit_complete',
        'plan_sha256': w.sha(PLAN), 'historical_target_histories_equal_T2b_cache': True,
        'markets_separately_bound': True, 'financial_label_columns_read': [],
        'source_training_original_T2b_identity_proven': False,
        'rows': {market: sum(len(f) for f in frames[market]) for market in frames},
        'new_model_fits': 0, 'new_C0_fits': 0, 'new_inference': 0, 'new_scores': 0,
        'new_resampling': 0, 'new_submissions': 0, 'fields_automatically_changed': [],
        'artifacts': {w.rel(OUT/name): w.sha(OUT/name) for name in [
            'tables.json', 'bindings.json', 'read_receipt.json', 'positive_history_without_period.json']},
        'limits': plan['limits'], 'private_improvement_established': False, 'goal_achieved': False,
        'B00_all_alternatives_preserved': True, '2024_open': True}
    dump(OUT/'report.json', report)
    print(json.dumps({'status': report['status'], 'rows': report['rows'], 'new_fits': 0, 'new_scores': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('mode', choices=['prepare', 'run'])
    args = parser.parse_args(); {'prepare': prepare, 'run': run}[args.mode]()
