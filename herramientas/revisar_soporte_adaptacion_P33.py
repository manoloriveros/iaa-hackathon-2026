"""Viabilidad de una adaptación NB/broker en destino, solo grupos de entrenamiento."""
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'
OUT = BASE/'P33_soporte_adaptacion_destino_20261026'
PLAN = R/'registro/semana2_soporte_adaptacion_destino_privada_plan.json'
INDEX = R/'registro/semana2_soporte_adaptacion_destino_privada_actual.json'
DOC = R/'docs/archivo/semana2/PRIVADA_P33_SOPORTE_ADAPTACION_DESTINO.md'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
sp = importlib.util.spec_from_file_location('p33_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def dump(path, value):
    with path.open('x', encoding='utf8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False,
            default=lambda x: x.item() if isinstance(x, np.generic) else str(x))


def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), default=float).encode()).hexdigest()


def paths():
    return [Path(__file__), R/'registro/semana2_canal_privada_plan.json',
        R/'registro/semana2_calibracion_conjunta_privada_plan.json',
        R/'registro/semana2_frecuencia_marca_validacion_privada_plan.json',
        BASE/'P32_adecuacion_condicional_fuente_20261026/report_recovered.json',
        BASE/'P19_cohortes_broker_20261026/covariates.parquet',
        *[BASE/f'preflight_anidado_H1_20261026_v1/canonical_{line}.parquet' for line in ['motor', 'buildings', 'contents']]]


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    OUT.mkdir()
    plan = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'question': 'Before considering one target newbusiness-by-broker residual effect on original S2/H1, is the effect distinct from prior P23/P18and supported in every affected training scope?',
        'candidate_not_fitted': 'Original incumbent, one NB-by-broker term; no rescue of P30source, favorable line subset or source capacity change.',
        'known_prior': {'P23': 'Broker main effect shared across businesses within each line; already adverse.',
            'P18': 'Joint ridge with line/business main effects, different GAMbase; no shared broker-by-business interaction.'},
        'scope': 'Only canonical emerging training rows: fold!=outer; additionally year2023for conditional transfer. Apply filters before loading/interpreting T0. No held outcome diagnostics.',
        'cells': ['NB_BROKER', 'NB_OTHER'], 'screen': {'minimum_positive_cost_groups_each_affected_line_cell': 30,
            'minimum_pooled_target_positive_groups_each_cell': 100,
            'all30scopes_required': True, 'no_threshold_or_fold_changes': True,
            'meaning': 'Existing per-level feasibility minimum retained; not credibility, approval to fit or new emerging support from pooling.'},
        'pooling': 'Count unique connected groups across target lines, not sums of line counts. Pooling requires an explicit exchangeability assumption; it cannot erase a failed per-line requirement or borrow developed-market events.',
        'sources': {w.rel(p): w.sha(p) for p in paths()},
        'budget': {'new_fits': 0, 'new_C0_fits': 0, 'new_model_inference': 0, 'new_prices': 0, 'new_scores': 0, 'new_submissions': 0},
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text('Codex. P33solo revisa novedad y soporte de una posible adaptación NB/broker en el mercado emergente, sobre la referencia original. P23ya probó broker compartido entre negocios y fue adverso; P18una calibración distinta por ramo/negocio. Antes de otro ajuste se conservará el mínimo de30grupos positivos por celda afectada y ramo en cada ámbito guardado. La suma entre ramos no creará soporte específico ni sustituirá ese requisito. Se filtrarán primero los grupos de entrenamiento; transferencia solo2023. No se ajusta, predice, puntúa, agrupa folds o reestima C0. B00/F3c y alternativas conservados,2024abierto. Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN),encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P33-SOPORTE-PREVIO', '--asunto', 'P33: soporte destino antes de una adaptación NB/broker, sin ajustes',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': plan['utc'], 'status': 'P33registered_support_only', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(posted.stdout)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt)
    print(json.dumps({'registered': True, 'new_fits': 0, 'forum': receipt['forum']}))


def run():
    assert not (OUT/'report.json').exists(); plan = w.read(PLAN)
    assert plan['sources'] == {w.rel(p): w.sha(p) for p in paths()}
    cov = pd.read_parquet(BASE/'P19_cohortes_broker_20261026/covariates.parquet',
        columns=['row_id', 'line', 'year', 'new_business', 'channel'], filters=[('year', 'in', [2023, 2024])]).set_index('row_id')
    template = w.read(R/'registro/semana2_frecuencia_marca_validacion_privada_plan.json')
    checks = []; pooled = []
    for evaluation in ['POOLED', 'TRANSFER']:
        for outer in range(5):
            pieces = []
            for line in ['motor', 'buildings', 'contents']:
                filters = [('fold', '!=', outer)]
                if evaluation == 'TRANSFER': filters.append(('year', '==', 2023))
                f = pd.read_parquet(BASE/f'preflight_anidado_H1_20261026_v1/canonical_{line}.parquet',
                    columns=['row_id', 'line', 'year', 'fold', 'group_id', 'new_business', 'T0'], filters=filters)
                expected = next(x for x in template['scopes'] if x['cohort'] == evaluation and x['outer'] == outer and x['line'] == line)
                assert digest(sorted(f.row_id)) == expected['training_row_digest']
                assert digest(sorted(set(f.group_id))) == expected['training_groups_digest']
                extra = cov.loc[f.row_id]; assert np.array_equal(extra.year, f.year) and np.array_equal(extra.new_business, f.new_business)
                assert extra.channel.isin(['broker', 'direct', 'comparison_site']).all()
                f = f.copy(); f['broker'] = extra.channel.eq('broker').to_numpy(); pieces.append(f)
                cells = []
                for broker, name in [(True, 'NB_BROKER'), (False, 'NB_OTHER')]:
                    z = f.loc[f.new_business.astype(bool)&f.broker.eq(broker)]
                    n = int(z.loc[z.T0.gt(0), 'group_id'].nunique())
                    cells.append({'cell': name, 'rows': len(z), 'groups': int(z.group_id.nunique()),
                        'positive_cost_periods': int(z.T0.gt(0).sum()), 'positive_cost_groups': n, 'minimum30_pass': n >= 30})
                checks.append({'evaluation': evaluation, 'outer': outer, 'line': line, 'cells': cells, 'support_pass': all(x['minimum30_pass'] for x in cells)})
            all_lines = pd.concat(pieces, ignore_index=True); cells = []
            for broker, name in [(True, 'NB_BROKER'), (False, 'NB_OTHER')]:
                z = all_lines.loc[all_lines.new_business.astype(bool)&all_lines.broker.eq(broker)]
                n = int(z.loc[z.T0.gt(0), 'group_id'].nunique())
                cells.append({'cell': name, 'positive_cost_periods': int(z.T0.gt(0).sum()),
                    'unique_target_positive_groups_across_lines': n, 'minimum100_pass': n >= 100})
            pooled.append({'evaluation': evaluation, 'outer': outer, 'cells': cells})
    per_line_ok = all(x['support_pass'] for x in checks); pooled_ok = all(c['minimum100_pass'] for a in pooled for c in a['cells'])
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'status': 'P33support_review_complete', 'per_line_scopes': checks, 'pooled_target_scopes': pooled,
        'all_line_scopes_pass': per_line_ok, 'all_pooled_scopes_pass': pooled_ok,
        'full_scope_viable': per_line_ok and pooled_ok, 'failed_line_scopes': sum(not x['support_pass'] for x in checks),
        'fit_authorized_by_support_report': False, 'plan_sha256': w.sha(PLAN),
        'new_fits': 0, 'new_C0_fits': 0, 'new_model_inference': 0, 'new_prices': 0, 'new_scores': 0, 'new_submissions': 0,
        '2024_open': True, 'B00_all_alternatives_preserved': True, 'goal_achieved': False}
    dump(OUT/'report.json', report)
    next_unit = ('P34: bounded review of source-only coarse newbusiness/renewal training reweighting under the known official2025business mix, before any fitting. '
        'First inspect prior source-weighting recipes to avoid repeats. Use covariates only and market-specific source/target row metadata; no response or model objects. '
        'Quantify line/business overlap and both row and connected-source-group ESS under one declared business-only ratio, not failed fine-grained2025propensity weights. '
        'A coarse overlap pass cannot overturn failed detailed support or prove covariate-shift assumptions; it would justify only a preregistered same-capacity training-relevance test. '
        'Keep pricing target/exposure and all target validation criteria, no source/target pooled support, target-fit cell rescue,2025prices or upload.' if not report['full_scope_viable'] else
        'Review exchangeability and full protected numerical flow before preregistering any common target NB/broker effect. Source and per-line counts alone do not justify pooling or admission; keep original minimum/gates and no new fitting until the recipe is concrete.')
    text = '# P33: soporte de la posible adaptación NB/broker\n\nCodex, '+report['utc']+'. '
    text += 'Se revisaron solo los grupos de entrenamiento de los30ámbitos guardados. Se aplicaron filtros de fold y año antes de interpretar T0. Ninguna etiqueta retenida se usó como diagnóstico.\n\n'
    text += '| Esquema | Ramo | Ámbitos con soporte mínimo | Ámbitos revisados |\n|---|---|---:|---:|\n'
    for evaluation in ['POOLED', 'TRANSFER']:
        for line in ['motor', 'buildings', 'contents']:
            aa = [a for a in checks if a['evaluation'] == evaluation and a['line'] == line]
            text += '| '+evaluation+' | '+line+' | '+str(sum(a['support_pass'] for a in aa))+' | '+str(len(aa))+' |\n'
    text += '\n'+('La receta completa no cumple el requisito retenido de soporte por ramo/celda. No se fuerza mediante un coeficiente común ni se rescatan ramos con números favorables.' if not report['full_scope_viable'] else 'Los mínimos numéricos pasan, pero no establecen la hipótesis de efecto común o credibilidad suficiente.')
    text += (' La agrupación de ramos del mismo mercado se informa con grupos únicos; no crea eventos específicos de edificios/contenidos ni borra los fallos individuales. '
        'No se mezcló soporte del mercado desarrollado. P23fue un efecto broker compartido entre negocios; P18usó otro modelo de calibración. La interacción propuesta sería distinta, pero no basta que sea distinta para ajustarla.\n\n'
        'Se conservan los mínimos de30grupos positivos por celda afectada, folds y referencias. Cero ajustes, C0, inferencias, precios, scores o envíos. '
        'B00/F3c y todas las alternativas siguen guardados,2024abierto adaptativo.\n\nPróximo trabajo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'.\n')
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P33-SOPORTE-RESULTADO', '--asunto', 'P33: soporte por ramo antes de adaptar NB/broker; sin forzar agrupaciones',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': report['utc'], 'status': report['status'], 'report': w.rel(OUT/'report.json'),
        'report_sha256': w.sha(OUT/'report.json'), 'document': w.rel(DOC), 'full_scope_viable': report['full_scope_viable'],
        'failed_line_scopes': report['failed_line_scopes'], 'forum': json.loads(posted.stdout), 'next_unit': next_unit,
        'new_fits': 0, 'new_scores': 0, 'new_submissions': 0, 'goal_achieved': False, '2024_open': True, 'B00_all_alternatives_preserved': True}
    archive = R/'privado'/('corte_P33_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P33': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P33': receipt, 'next_unit': next_unit}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']; own.update(private_P33=receipt, next_unit=next_unit)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P33: soporte destino sin ajustes, 26 de octubre de2026\n\nCodex, '+report['utc']+'. Viabilidad del alcance completo NB/broker='+str(report['full_scope_viable'])+'; ámbitos por ramo insuficientes='+str(report['failed_line_scopes'])+'. No se fuerza agrupación de ramos o soporte fuente. Cero ajustes/inferencias/scores/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_target_adaptation_support_index': w.rel(INDEX), 'week_2_private_target_adaptation_support_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt)
    print(json.dumps({'closed': True, 'full_scope_viable': report['full_scope_viable'], 'failed_line_scopes': report['failed_line_scopes'], 'new_fits': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'run']); args = parser.parse_args()
    {'prepare': prepare, 'run': run}[args.mode]()
