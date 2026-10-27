"""Diagnóstico algebraico nuevo de PS1: nivel y asignación, sin alterar precios."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import math
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'; BASE = R/'privado/semana2/mision017_fase2'
PARENT = BASE/'P48_validacion_pareada_20261026'; OUT = BASE/'P49_atribucion_pareada_20261027'
PLAN = R/'registro/semana2_atribucion_pareada_privada_plan.json'; INDEX = R/'registro/semana2_atribucion_pareada_privada_actual.json'
DOC = R/'docs/semana2/PRIVADA_P49_NIVEL_Y_ASIGNACION_PAREADA.md'
sp = importlib.util.spec_from_file_location('p49_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    with path.open('x', encoding='utf8') as f: json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def post(body, identifier, subject):
    a = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', identifier,
        '--asunto', subject, '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    return json.loads(a.stdout)


def profile(y, price):
    assert np.isfinite(y).all() and (y >= 0).all() and np.isfinite(price).all() and (price > 0).all()
    aa = math.fsum(float(v)/math.sqrt(float(p)) for v, p in zip(y, price)); bb = math.fsum(math.sqrt(float(p)) for p in price)
    cc = math.fsum(math.sqrt(float(v)) for v in y)
    assert aa > 0 and bb > 0
    actual = math.fsum(4*float(v)/math.sqrt(float(p))+4*math.sqrt(float(p))-8*math.sqrt(float(v)) for v, p in zip(y, price))
    minimum = 8*math.sqrt(aa*bb)-8*cc; level_penalty = 4*(math.sqrt(aa)-math.sqrt(bb))**2
    assert math.isclose(actual, minimum+level_penalty, rel_tol=3e-12, abs_tol=1e-8)
    return {'actual_loss': actual, 'profiled_minimum_loss': minimum, 'level_penalty': level_penalty,
        'oracle_scale_diagnostic_not_price_parameter': aa/bb, 'A': aa, 'B': bb, 'C': cc}


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists(); OUT.mkdir()
    parent = w.read(PARENT/'completion_receipt.json'); assert parent['report_sha256'] == w.sha(PARENT/'report.json') and not parent['all_exploratory_gates_pass']
    replay = w.read(PARENT/'replay_report.json'); assert replay['report_sha256'] == w.sha(PARENT/'report.json') and replay['learning_and_source_inference_blocked']
    paths = [Path(__file__), PARENT/'report.json', PARENT/'completion_receipt.json', PARENT/'replay_report.json',
        BASE/'P47_preflight_pareado_20261026/report.json', BASE/'P13_atribucion_GLM_20261026/report.json']
    paths += [PARENT/(c+'_prices.parquet') for c in ['POOLED', 'TRANSFER']]
    plan = {'author': 'Codex', 'utc': utc(), 'question': 'Does the NEW complete PS1loss arise from aggregate level penalty or remaining risk allocation even after an oracle scalar?',
        'novelty': 'Apply the previously verified P13algebra only to new P48whole-algorithm predictions. Do not rerun P13or score old models, fit, bootstrap, apply models or create scaled price arrays.',
        'scopes': 'Exactly20nominal decompositions: pooled global plus12line/year/business cells; transfer global plus6line/year/business cells. Include every adverse cell. No choosing scopes after outcomes.',
        'mathematics': 'A=sum(y/sqrt(mu)), B=sum(sqrt(mu)), C=sum(sqrt(y)); D=4(A+B-2C), D_min=8sqrt(AB)-8C, penalty=4(sqrt(A)-sqrt(B))^2. k_oracle=A/Bdiagnostic only. Delta_total=delta_profiled_minimum+delta_level_penalty under each fixed scope null.',
        'diagnostic_consequence': 'If even min-lossPS1is worse than fixed reference, no scalar correction can solve that scope. Otherwise this is only room for a training-only mechanism, not permission to use retained-label oracle scales or claim a deployable improvement.',
        'support': 'Reuse P47saved training-positive-period counts as context, explicitly not independent group support or new uncertainty validation. No new C0/support audit on unchanged inputs.',
        'budget': {'decompositions': 20, 'oracle_diagnostic_scalars_separate': 40, 'new_fits': 0, 'new_C0_fits': 0, 'new_source_inference': 0,
            'new_predictive_vectors': 0, 'new_bootstraps': 0, 'new2025inference': 0, 'new_submissions': 0},
        'sources': {w.rel(k): w.sha(k) for k in paths},
        'limits': ['Profiled loss is not pure ranking or causal attribution; new model changed several linked components.',
            'Adaptive2023/2024, conditional source2024, masters/tail/reserve/support limits unchanged. No admission from oracle diagnostics.'],
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan); body = OUT/'forum_previo.md'
    body.write_text('Codex. P49registra veinte descomposiciones nominales del PS1 recién validado: ambos globales y todas las celdas ramo/año/negocio. Se reutiliza la identidad matemática ya comprobada en P13 sobre estas predicciones nuevas, sin repetir el diagnóstico antiguo. Se separan pérdida mínima perfilada y penalización de nivel; cuarenta escalares oráculo solo como diagnóstico, nunca factores o vectores de precio. Se comprobará por sumas independientes la identidad del contraste y sus nulas. Se conserva el soporte positivo P47 como contexto, sin convertir periodos en grupos independientes. Cero ajustes, C0, inferencias, precios nuevos, remuestreo o envíos. B00/F3c/adversos conservados;2024abierto. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P49registered_before_new_algebra', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN),
        'forum': post(body, 'COD-S2-20261027-PRIVADA-P49-PAREADO-PREVIO', 'P49: nivel y asignación del PS1 nuevo, sin reescalar o ajustar')}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps(receipt))


def run():
    assert not (OUT/'report.json').exists(); plan = w.read(PLAN); assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    assert all(w.sha(ROOT/k) == v for k, v in plan['sources'].items()); results = []
    for evaluation in ['POOLED', 'TRANSFER']:
        f = pd.read_parquet(PARENT/(evaluation+'_prices.parquet')); scopes = [('GLOBAL', f)]
        scopes += [(f'{line}|{year}|NB{int(nb)}', f.loc[ix]) for (line, year, nb), ix in f.groupby(['line', 'year', 'new_business']).groups.items()]
        for label, z in scopes:
            y = z.T0.to_numpy(float); old = profile(y, z.old_nominal.to_numpy(float)); new = profile(y, z.new_nominal.to_numpy(float))
            null = 8*(math.sqrt(len(y)*math.fsum(y.tolist()))-math.fsum(math.sqrt(float(v)) for v in y)); assert null > 0
            allocation = (old['profiled_minimum_loss']-new['profiled_minimum_loss'])/null
            level = (old['level_penalty']-new['level_penalty'])/null; total = (old['actual_loss']-new['actual_loss'])/null
            assert math.isclose(total, allocation+level, rel_tol=2e-10, abs_tol=1e-12)
            # Independent vectorized unit deviance on the unchanged saved forecasts, no oracle-rescaled prices.
            direct = (np.sum(4*y/np.sqrt(z.old_nominal)+4*np.sqrt(z.old_nominal)-8*np.sqrt(y))-
                np.sum(4*y/np.sqrt(z.new_nominal)+4*np.sqrt(z.new_nominal)-8*np.sqrt(y)))/null
            assert math.isclose(total, direct, rel_tol=2e-10, abs_tol=1e-12)
            result = {'evaluation': evaluation, 'scope': label, 'rows': len(z), 'groups': int(z.group_id.nunique()), 'delta_total': total,
                'delta_profiled_allocation': allocation, 'delta_level_penalty': level,
                'new_oracle_vs_fixed_reference': (old['actual_loss']-new['profiled_minimum_loss'])/null,
                'old': old, 'new': new}
            if label == 'GLOBAL': assert math.isclose(total, w.read(PARENT/'report.json')['results'][evaluation]['NOMINAL']['delta'], rel_tol=2e-10, abs_tol=1e-12)
            results.append(result)
    assert len(results) == 20
    assert all(w.sha(ROOT/k) == v for k, v in plan['sources'].items())
    support = w.read(BASE/'P47_preflight_pareado_20261026/report.json')['bindings']
    report = {'author': 'Codex', 'utc': utc(), 'status': 'P49new_PS1algebra_complete', 'plan_sha256': w.sha(PLAN), 'results': results,
        'minimum_training_positive_periods_per_business_reused': min(min(x['positive_train_by_business'].values()) for x in support),
        'cell_scopes_no_scalar_can_beat_fixed_reference': sum(x['new_oracle_vs_fixed_reference'] < 0 for x in results if x['scope'] != 'GLOBAL'),
        'new_fits': 0, 'new_C0_fits': 0, 'new_predictive_vectors': 0, 'new_resampling': 0, 'oracle_diagnostic_scalars_separate': 40,
        'new_submissions': 0, 'adopted': False, '2024_open': True, 'private_improvement_established': False, 'goal_achieved': False}
    dump(OUT/'report.json', report); print(json.dumps({'complete': True, 'global': [{k:v for k, v in x.items() if k not in ['old', 'new']} for x in results if x['scope']=='GLOBAL'], 'cell_scopes_no_scalar_can_rescue': report['cell_scopes_no_scalar_can_beat_fixed_reference'], 'new_fits': 0}))


def close():
    assert not (OUT/'completion_receipt.json').exists(); d = w.read(OUT/'report.json'); assert d['plan_sha256'] == w.sha(PLAN)
    next_unit = 'P50: use P49new global/cell decomposition to choose one documented standard mechanism, not another generic source-family search. If allocation remains worse after profiling, do not fit a scalar to oracle levels. Review an exact transferable production comparator now recoverable from the P40/P41source graph, separating pooled-source reporting and target-peril-mixture ancestors; identify the smallest genuine numerical dependency needed for protected validation. No repeat bounded missing-file search, old57stage hash audit, public receipt fitting or hidden-private claims. Commit/preregister a concrete corrected complete-flow recipe before any later fit/score; no automatic CSVor upload.'
    text = '# P49: nivel y asignación del algoritmo pareado\n\nCodex, '+utc()+'. Se completaron las veinte descomposiciones preinscritas, sin ajustar ni modificar un vector de precios. Los cuarenta escalares oráculo se guardan solo como diagnóstico.\n\n| Global | Δ total | Δ asignación perfilada | Δ penalización de nivel | Mejor escalar nuevo frente a referencia fija |\n|---|---:|---:|---:|---:|\n'
    global_results = {}
    for x in d['results']:
        if x['scope'] == 'GLOBAL':
            global_results[x['evaluation']] = {k:x[k] for k in ['delta_total', 'delta_profiled_allocation', 'delta_level_penalty', 'new_oracle_vs_fixed_reference']}
            text += f"| {x['evaluation']} | {x['delta_total']:+.7f} | {x['delta_profiled_allocation']:+.7f} | {x['delta_level_penalty']:+.7f} | {x['new_oracle_vs_fixed_reference']:+.7f} |\n"
    text += f"\nEn {d['cell_scopes_no_scalar_can_beat_fixed_reference']}de las18celdas ramo/año/negocio, ni el mejor escalar del PS1superaría a la referencia fija. Se conservan todas las celdas y signos, sin elegir niveles oráculo o crear precios reescalados. La pérdida perfilada no es una métrica pura de ranking ni una explicación causal. Las identidades se comprobaron por sumas escalares independientes y desviación vectorizada de las predicciones guardadas; no se repitió la suite matemática de P13 o su diagnóstico sobre otros modelos.\n\n"
    text += f"El mínimo de soporte de entrenamiento P47es{d['minimum_training_positive_periods_per_business_reused']}periodos positivos por negocio, reutilizado como contexto y sin equipararlo a grupos independientes. Persiste la incertidumbre de reservas/cola y la fuente2024condicional. Cero ajustes fuente/destino/C0, inferencias, precios nuevos, bootstrap o envíos.2024abierto adaptativo, B00/F3c/adversos conservados; no mejora privada acreditada.\n\nPróximo: "+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'.\n'
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': d['status'], 'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'document': w.rel(DOC), 'global_results': global_results, 'new_fits': 0, 'new_predictive_vectors': 0, 'new_resampling': 0, 'new_submissions': 0,
        'next_unit': next_unit, 'goal_achieved': False, '2024_open': True,
        'forum': post(body, 'COD-S2-20261027-PRIVADA-P49-PAREADO-RESULTADO', 'P49: descomposición de la pérdida nueva, sin adoptar escalares oráculo')}
    archive = R/'privado'/('corte_P49_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P49': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P49': receipt, 'next_unit': next_unit}, archive)
    path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(path)['week_2_mission017_phase2_20261025']; own.update(private_P49=receipt, next_unit=next_unit)
    w.update(path, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P49: nivel y asignación del PS1 nuevo\n\nCodex, '+receipt['utc']+'.20descomposiciones nuevas,40escalares oráculo diagnósticos, cero ajustes/precios nuevos/remuestreo/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_paired_attribution_index': w.rel(INDEX), 'week_2_private_paired_attribution_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'new_fits': 0, 'new_submissions': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); a = argparse.ArgumentParser(description=__doc__); a.add_argument('mode', choices=['prepare', 'run', 'close']); mode = a.parse_args().mode
    {'prepare': prepare, 'run': run, 'close': close}[mode]()
