"""Revisa recibos y ancestros de la nueva corrida completa, sin modelos o scores."""
from datetime import datetime, timezone
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; OUT = BASE/'P41_grafo_fuente_recuperada_20261026'
WORK = R/'privado/reentrenamiento_completo_20261026/corrida'
PLAN = R/'registro/semana2_grafo_fuente_recuperada_privada_plan.json'
INDEX = R/'registro/semana2_grafo_fuente_recuperada_privada_actual.json'
DOC = R/'docs/archivo/semana2/PRIVADA_P41_GRAFO_REENTRENADO_Y_ALCANCE.md'
sp = importlib.util.spec_from_file_location('p41_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    with path.open('x', encoding='utf8') as f: json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists(); OUT.mkdir()
    inputs = [Path(__file__), WORK/'manifest.json', WORK/'chain_manifest.json', WORK/'live.json', WORK/'chain_live.json',
        R/'herramientas/reentrenar_desde_originales.py', R/'herramientas/completar_reentrenamiento_cadena.py',
        WORK/'ml/codigo/preparar_datos.py', WORK/'ml/codigo/gbm.py', WORK/'noche/codigo/reporte.py',
        WORK/'noche/codigo/ultimo_mercado.py', WORK/'aux/reproduccion_cadena.py', BASE/'P40_F3c_recuperado_20261026/report.json']
    plan = {'author': 'Codex', 'utc': utc(), 'scope': 'Read current manifest/terminal stage receipts and final artifact hashes for the now completed57stage historical reconstruction. No producer import/exec, process restart, model load, predictions, scoring, bootstrap or edits to the other workstream.',
        'criterion': 'Distinguish execution and byte-integrity from target-held ancestry. Resolve repeated output paths by declared chronological stage order: verify only latest writer final hash and retain superseded earlier hashes, not false corruption from legitimate in-place stages.',
        'source_eligibility': 'Separate developed-only T2bpretraining from pooled both-market reporting ancestors in A1. Target training-only residuals cannot protect a source object that already used held target reporting data. Production on all known training years remains a different legitimate scope.',
        'sources': {w.rel(p): w.sha(p) for p in inputs}, 'new_fits': 0, 'new_inference': 0, 'new_scores': 0, 'new_submissions': 0,
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text('Codex. P41revisa metadatos nuevos: la cadena limpia declara etapas completas, mientras su índice anterior aún decía en ejecución. Se contrastarán recibos terminales y huellas del último escritor de cada salida, respetando las sustituciones entre etapas declaradas. No se reinicia, importa o ejecuta nada de esa línea, ni se leen sus scores. Se separará T2bfuente de los ancestros de reporte agrupados de A1antes de considerar un comparador con grupos protegidos. Cero entrenamiento/inferencias/envíos; B00/F3c/alternativas conservados,2024abierto. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P41-GRAFO-PREVIO', '--asunto', 'P41: recibos de la cadena completada y alcance de los ancestros', '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P41registered_manifest_review', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(p.stdout)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps(receipt))


def run():
    assert not (OUT/'report.json').exists(); plan = w.read(PLAN)
    assert all(w.sha(ROOT/p) == sha for p, sha in plan['sources'].items()), 'Concurrent update: reconcile first'
    main = w.read(WORK/'manifest.json'); chain = w.read(WORK/'chain_manifest.json')
    latest = {}; replaced = []; receipts = []; checks = []
    for name, manifest, key in [('receipts', main, 'steps'), ('chain_receipts', chain, 'plan')]:
        for stage in manifest[key]:
            path = WORK/name/(stage['id']+'.json'); receipt = w.read(path)
            assert receipt['stage'] == stage['id'] and receipt['exit_code'] == 0
            for output in receipt['outputs']:
                relative = output['path']; resolved = (WORK/relative).resolve(); assert resolved.is_relative_to(WORK)
                if relative in latest: replaced.append({'path': relative, 'prior_stage': latest[relative]['stage'], 'later_stage': stage['id']})
                latest[relative] = {'stage': stage['id'], 'sha256': output['sha256']}
            receipts.append({'stage': stage['id'], 'utc': receipt['utc'], 'exit_code': 0, 'receipt_sha256': w.sha(path), 'output_count': len(receipt['outputs'])})
    for relative, expected in latest.items():
        path = WORK/relative; actual = w.sha(path) if path.is_file() else None
        checks.append({'path': relative, 'last_writer': expected['stage'], 'expected_sha256': expected['sha256'], 'actual_sha256': actual, 'match': actual == expected['sha256']})
    immutable = {}
    for manifest in [main, chain]:
        for item in manifest['files']: immutable[item['path']] = item
    input_checks = []
    for relative, expected in immutable.items():
        path = (WORK/relative).resolve(); assert path.is_relative_to(WORK)
        actual = w.sha(path) if path.is_file() else None
        input_checks.append({'path': relative, 'kind': expected.get('kind'), 'declared_sha256': expected['sha256'], 'actual_sha256': actual, 'match': actual == expected['sha256']})
    ml = (WORK/'ml/codigo/preparar_datos.py').read_text(encoding='utf-8-sig')
    gbm = (WORK/'ml/codigo/gbm.py').read_text(encoding='utf-8-sig')
    global_curve = (WORK/'aux/reproduccion_cadena.py').read_text(encoding='utf-8-sig')
    assert 'for m in ["developed", "emerging"]' in ml
    assert 'c = cd if m == "developed" else ce' in ml and 'cost = {p_: df.loc[tr' in ml
    assert 'Xd = matriz(dv, colsC, cats); yd = dv.y.values' in gbm and 'cats = categorias_union([dv, em]' in gbm
    assert "pd.concat([RP.load('s1'), RP.load('s2')]" in global_curve
    whole_scope = [
        {'object': 'T2bsource GBM', 'current_evidence': 'Source response and cost-completion mixtures derived from developedrows only, bymarket loop. Whole-target category vocabulary is label-free transductive covariates. Completed stage/model hash is not a full independent end-to-end validation.', 'target_held_free_use': 'Potential fixed source component, after numerical/key/feature verification; never reuse stored target levels or c_filaas if they excluded outer held groups.'},
        {'object': 'A1source GBM with original global reporting', 'current_evidence': 'Restored REP-N2cost curve pools s1+s2accepted claim delays/costs with no outer held exclusion, then feeds source/target ultimate inputs. Source price coefficients can therefore inherit target reporting data.', 'target_held_free_use': 'Not eligible as a fixed target-held-independent source merely because price labels are developed. Requires outer-specific reporting/source fitting or an explicitly different source-only observation contract. All-known-training production is a separate scope.'},
        {'object': 'F3c/F3d/F4cproduction and factors', 'current_evidence': 'Full raw-input reconstruction can now be examined from completed stage receipts. These outputs still inherit public calibration, pooled target mixtures and historical feature choices.', 'target_held_free_use': 'Do not directly score full-training production prices on their historical ancestors or relabel archived output replay as protected validation.'}]
    assert all(w.sha(ROOT/p) == sha for p, sha in plan['sources'].items()), 'Source graph changed during read; preserve provisional evidence'
    report = {'author': 'Codex', 'utc': utc(), 'status': 'P41full_retraining_graph_reviewed_not_private_validation',
        'stage_receipts': receipts, 'stage_count': len(receipts), 'terminal_exit0_count': sum(a['exit_code'] == 0 for a in receipts),
        'latest_output_checks': checks, 'all_latest_outputs_match': all(a['match'] for a in checks),
        'superseded_output_hashes_preserved_not_false_failures': replaced, 'input_checks': input_checks,
        'all_declared_input_bytes_match_current_manifest': all(a['match'] for a in input_checks), 'ancestor_scope': whole_scope,
        'full_retraining_recipe_restorations_not_original_identity': chain.get('restorations_not_recovered_originals'),
        'other_workstream_not_started_or_modified': True, 'other_models_not_loaded': True, 'new_fits': 0, 'new_C0_fits': 0, 'new_inference': 0,
        'new_scores': 0, 'new_resampling': 0, 'new_submissions': 0, 'private_improvement_established': False, '2024_open': True,
        'B00_all_alternatives_preserved': True, 'goal_achieved': False}
    dump(OUT/'report.json', report)
    next_unit = ('P42: pre-register a simpler one-change source ablation of failed P30before increasing capacity: reuse the exact existing P28inner/P29full Poisson frequency GLMs, replace conditional severity GLMs by the same paired-offset constant mark per peril. Reuse saved inner constant marks; compute15full-source scalar marks only after an all-line source-held veto<=1.002originalA1Stree. Correct mark constant=sum(C/sqrt(E_C/E_N))/sum(N*sqrt(E_C/E_N)); no count-period proxy, extra exposure, C0or GLMfit. Fixed frequency-only hypothesis, not selecting perils/lines or trying the reciprocal ablation opportunistically. First register objective/formula/budget, verify saved models and source scopes, then current historical components and source veto. Whole-target evaluation separately preregistered only if all source vetoes pass. No2025prices or upload.')
    prose = '# P41: cadena reentrenada, recibos y alcance de uso\n\nCodex, '+report['utc']+'.\n\n'
    prose += ('Hay '+str(len(receipts))+'recibos terminales con salida0en la cadena registrada. Se cotejaron '+str(len(checks))+'salidas finales por el último escritor declarado; todas coinciden='+str(report['all_latest_outputs_match'])+'. '
        'Entradas declaradas concordantes='+str(report['all_declared_input_bytes_match_current_manifest'])+'. Las huellas intermedias sustituidas se conservan como tales, no como falsas corrupciones. '
        'No se reanudó, reinició o modificó el trabajo concurrente, ni se contó su entrenamiento como ajuste propio de este ciclo.\n\n'
        'Esto amplía la evidencia respecto del replay portable con OOFguardadas: ya existen recibos del reentrenamiento desde originales. '
        'Sin embargo, completitud de ejecución y fidelidad histórica son distintas de protección de validación. Las restauraciones declaradas siguen visibles.\n\n'
        'T2baprende respuestas y mezclas de coste del mercado desarrollado; sus categorías pueden mirar covariables emergentes, sin sus etiquetas. '
        'Puede revisarse como componente fuente fijo, pero sus niveles emergentes y c_filahistóricos necesitan su propio ámbito protegido. '
        'En A1, la curva REP-N2restaurada agrupa siniestros desarrollados y emergentes, antes de alimentar los offsets de fuente. '
        'Por ello, que el árbol de precio solo vea etiquetas desarrolladas no vuelve independiente del grupo target retenido a todo su aprendizaje. '
        'Usar todos los años conocidos para producción sigue siendo un ámbito distinto y legítimo; el problema es presentarlo como validación fuera del aprendizaje.\n\n'
        'No se adopta un CSVnuevo por haber terminado la cadena. No se cargaron modelos, calcularon predicciones/scores o leyeron las métricas de comparaciones ajenas. '
        'La revisión es estática y de integridad, no validación profesional independiente o mejora privada demostrada. B00/F3c/alternativas conservados;2024abierto adaptativo.\n\n'
        'La siguiente prueba simplifica una familia estándar ya disponible, sin repetir fuente o aumentar árboles. El fallo P30no se atribuye automáticamente a severidad; '
        'la ablación verificará esa incertidumbre con una sola intervención preinscrita y veto fuente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'.\n')
    DOC.write_text(prose, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(prose, encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P41-GRAFO-RESULTADO', '--asunto', 'P41: cadena completa cotejada; separar fuente T2b y reporte agrupado A1', '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': utc(), 'status': report['status'], 'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'document': w.rel(DOC), 'stage_count': len(receipts), 'all_latest_outputs_match': report['all_latest_outputs_match'],
        'all_manifest_inputs_match': report['all_declared_input_bytes_match_current_manifest'], 'forum': json.loads(p.stdout), 'next_unit': next_unit,
        'new_fits': 0, 'new_scores': 0, 'new_submissions': 0, 'goal_achieved': False, '2024_open': True}
    archive = R/'privado'/('corte_P41_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P41': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P41': receipt, 'next_unit': next_unit}, archive)
    path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(path)['week_2_mission017_phase2_20261025']; own.update(private_P41=receipt, next_unit=next_unit)
    w.update(path, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P41: grafo reentrenado y ámbitos\n\nCodex, '+receipt['utc']+'. '+str(len(receipts))+'etapas con recibo terminal; salidas finales concordantes='+str(report['all_latest_outputs_match'])+'. T2bfuente desarrollado distinto de A1con ancestros REP-N2agrupados s1/s2; no adoptar validación targetpor fuente solo nominalmente desarrollada. Cero ajustes/inferencias/scores/envíos propios. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_retrained_graph_review_index': w.rel(INDEX), 'week_2_private_retrained_graph_review_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'stages': len(receipts), 'outputs_match': report['all_latest_outputs_match'], 'manifest_inputs_match': report['all_declared_input_bytes_match_current_manifest'], 'new_fits': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); p = argparse.ArgumentParser(description=__doc__); p.add_argument('mode', choices=['prepare', 'run']); a = p.parse_args(); {'prepare': prepare, 'run': run}[a.mode]()
