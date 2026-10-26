"""Control de consistencia: el mismo productor prod alimenta CV y despliegue."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'
PREVIOUS = BASE / 'FSp_REN_G3_contraste_20261026_v2'
OUT = BASE / 'FSp_REN_G3_prod_contraste_20261026_v1'
PLAN = R / 'registro/semana2_mision017_FSp_REN_G3_prod_plan_v1.json'
ENGINE = R / 'herramientas/contrastar_FSp_REN_contra_G3_v2.py'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


engine = load('RFS1_unmodified_math_engine', ENGINE)
w = engine.w
import numpy as np
import pandas as pd


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')


def prepare():
    assert not OUT.exists(); OUT.mkdir()
    previous = w.read(PREVIOUS / 'preflight.json')
    paths = [Path(__file__), ENGINE, PREVIOUS / 'report.json', PREVIOUS / 'preflight.json',
             R / 'registro/semana2_mision017_FSp_REN_G3_plan_v2.json']
    # Exact already-verified inputs, not another integration/feature suite.
    assert all(w.sha(ROOT / path) == sha for path, sha in previous['sources'].items())
    scopes = []; cache = {}; changes = []
    for scope in previous['scopes']:
        line = scope['line']; held = scope['held']
        if line not in cache:
            home = BASE / 'FSp_edificios_productor_20261026_v1' if line == 'buildings' else BASE / 'FSp_MC_recuperacion_20261026_v1/productor'
            path = home / ('components_prod.parquet' if line == 'buildings' else f'components_{line}_prod.parquet')
            report = home / 'report.json'; paths += [path, report]
            assert w.sha(path) == w.read(report)['outputs'][path.name]['sha256']
            prod = pd.read_parquet(path, filters=[('year', '<=', 2024)]).set_index('row_id')
            assert prod.index.is_unique and prod.year.isin([2023, 2024]).all()
            cache[line] = prod
        prod = cache[line]
        previous_path = ROOT / scope['input']; paths.append(previous_path)
        assert w.sha(previous_path) == scope['sha256']
        f = pd.read_parquet(previous_path); original = f.copy(deep=True)
        keyed = prod.loc[f.row_id]; scale = f.exposure.to_numpy() / keyed.exposure.to_numpy()
        replacing = []
        for p in previous['perils'][line]:
            f['f_' + p] = keyed['f_' + p].to_numpy() * scale
            f['s_' + p] = keyed['s_' + p].to_numpy()
            replacing += ['f_' + p, 's_' + p]
        assert f.drop(columns=replacing).equals(original.drop(columns=replacing))
        mask24 = f.year.eq(2024).to_numpy(); mask23 = f.year.eq(2023).to_numpy()
        assert np.array_equal(f.loc[mask24, replacing], original.loc[mask24, replacing])
        changed = np.any(f[replacing].to_numpy() != original[replacing].to_numpy(), axis=1)
        assert changed[mask23].any() and not changed[mask24].any()
        outpath = OUT / f'inputs_{line}_fold{held}.parquet'; f.to_parquet(outpath, index=False)
        scopes.append({**scope, 'input': w.rel(outpath), 'sha256': w.sha(outpath)})
        changes.append({'line': line, 'held': held, 'changed_rows2023': int(changed[mask23].sum()),
                        'changed_rows2024': 0, 'all_other_columns_exact': True, 'replaced_columns': replacing})
    report = {**previous, 'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'scopes': scopes,
              'production_alignment_changes': changes, 'no_new_model_inference': True,
              'sources': {**previous['sources'], **{w.rel(p): w.sha(p) for p in paths}},
              'purpose': 'Replace only2023f/s with cached production-window components; everything else bit exact. Later calibration may also change2024predictions because training pools both years.',
              'new_parameter_estimates': 0, 'new_C0_fits': 0, 'new_scores': 0, 'new_test_prices': 0}
    dump(OUT / 'preflight.json', report)
    print(json.dumps({'preflight': 'passed', 'scopes': len(scopes), '2024_f_s_exact': True,
                      'all_other_columns_exact': True, 'new_estimates': 0, 'new_scores': 0}))


def register():
    assert not PLAN.exists() and not (OUT / 'registration.json').exists()
    pre = w.read(OUT / 'preflight.json')
    original = w.read(R / 'registro/semana2_mision017_FSp_REN_G3_plan_v2.json')
    plan = json.loads(json.dumps(original))
    plan.pop('repair', None)
    plan.update(author='Codex', utc=datetime.now(timezone.utc).isoformat(), candidate_id='RFS1P',
        hypothesis='The actual deployment uses source2021–2024 and target climate2023–24. Check the same producer on both historical target years, matching the T2b/G3 information set, rather than assuming a two-phase development result transfers to production.',
        need_for_distinct_trial='Earlier RFS1 used dev components in2023 and prod in2024. This is a fixed deployment-consistency control, not a window search or a retry with changed K/weights. Preserve the earlier result.',
        source_phase={'target2023': 'cached prod source2021–2024, target climate2023–24',
                      'target2024': 'cached prod source2021–2024, target climate2023–24',
                      'target2025_future_deployment': 'same prod source2021–2024, target climate2023–24',
                      'limits': 'All are conditional on the supplied end2024snapshot. This is group validation for a2025deployment, not a prospective forecast of2023/24.'},
        numerical_engine={'path': w.rel(ENGINE), 'sha256': w.sha(ENGINE), 'learn_apply_functions_unchanged': True,
                          'globals_set': {'OUT': w.rel(OUT), 'PLAN': w.rel(PLAN), 'PREVIOUS': 'nonexistent path: no old calibration reuse'},
                          'report_metadata_adapter_only': 'Remove v1repair counters; identify RFS1P. No change to numeric estimator, score, normalization or bootstrap.'},
        preflight={'path': w.rel(OUT / 'preflight.json'), 'sha256': w.sha(OUT / 'preflight.json')},
        sources={**pre['sources'], **{s['input']: s['sha256'] for s in pre['scopes']},
                 w.rel(OUT / 'preflight.json'): w.sha(OUT / 'preflight.json')})
    plan['budget']['new_moment_constants_this_control'] = 165
    plan['budget']['old_calibration_reused'] = 0
    assert plan['configuration'] == original['configuration'] and plan['criterion'] == original['criterion']
    assert plan['bootstrap'] == original['bootstrap']
    dump(PLAN, plan)
    body = OUT / 'forum_previo.md'
    body.write_text('Codex. Antes de estimar o puntuar registro RFS1P, control de consistencia del despliegue. '
        'La producción2025 usa modelos fuente2021–2024 y clima emergente2023–2024; se comprobará ese mismo productor en ambos años históricos, '
        'igualando el conjunto de información del padre T2b/G3. RFS1 anterior conservaba el productor dev2021–2023/clima2023 al evaluar2023. '
        'Solo cambian sus entradas f/s de2023: las de2024 y todas las demás columnas son idénticas. Las constantes nuevas pueden cambiar también la aplicación2024 '
        'porque su aprendizaje agrupa ambos años. No se elige una ventana por el mejor score ni se reescribe RFS1. '
        'Se mantienen G3, grupos, C0, pesos .25/.25/.5 solo REN, KP100, normalización y criterios. '
        'Se reutilizan los 60 modelos guardados; cero ajustes de árboles, C0, inferencias nuevas, precios de test o envíos. '
        'Se estiman165momentos en15ámbitos y30normalizadores, sin reutilizar calibraciones de la configuración anterior. '
        'El motor matemático y el bootstrap son iguales; solo se adaptan sus rutas y metadatos. '
        'La validación es condicional al corte de diciembre2024 y no acredita un pronóstico prospectivo de2023. '
        'Plan: ' + w.rel(PLAN) + '.', encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-MISION017-FSP-REN-G3-PROD-CONSISTENCIA-PREVIO',
        '--asunto', 'Consistencia del despliegue FSp: mismo productor fuente2024 en ambos años', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': w.sha(PLAN), 'forum': json.loads(response.stdout)})
    print(json.dumps({'registered': True, 'candidate': 'RFS1P', 'new_moment_constants': 165, 'new_models': 0, 'forum': json.loads(response.stdout)}))


def run():
    plan = w.read(PLAN)
    assert w.sha(ENGINE) == plan['numerical_engine']['sha256']
    assert engine.WEIGHTS == plan['configuration']['weights_REN'] and engine.KP == plan['configuration']['KP']
    engine.OUT = OUT; engine.PLAN = PLAN; engine.PREVIOUS = OUT / '_no_previous_calibration_reuse'
    assert not engine.PREVIOUS.exists()
    original_dump = engine.dump
    def adapted_dump(path, value):
        if path == OUT / 'report.json':
            value = dict(value)
            value.pop('reused_v1_calibration_constants', None); value.pop('new_v2_calibration_constants', None)
            value.update(candidate_id='RFS1P', new_real_moment_constants=165, old_calibration_reused=0,
                         production_consistency_control=True,
                         oof_RFS1_column_denotes='RFS1P in this output only; earlier RFS1 remains separate',
                         source_phase=plan['source_phase'])
        original_dump(path, value)
    engine.dump = adapted_dump
    engine.run()
    result = w.read(OUT / 'report.json')
    assert result['old_calibration_reused'] == 0 and len(list(OUT.glob('learning_*.json'))) == 15
    print(json.dumps({'candidate': 'RFS1P', 'new_moment_constants': 165, 'new_models': 0,
                      'new_C0_fits': 0, 'new_submissions': 0, 'delta': result['delta_vs_G3']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'register', 'run'])
    args = parser.parse_args(); {'prepare': prepare, 'register': register, 'run': run}[args.mode]()
