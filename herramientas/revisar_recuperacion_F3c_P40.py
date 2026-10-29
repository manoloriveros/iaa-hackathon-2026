"""Revisa la evidencia nueva de F3c por código/hashes; no ejecuta productores."""
from datetime import datetime, timezone
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; OUT = BASE/'P40_F3c_recuperado_20261026'
SRC = R/'src/semana2/lineas/mision017_20261025'
PLAN = R/'registro/semana2_F3c_recuperacion_revision_privada_plan.json'
INDEX = R/'registro/semana2_F3c_recuperacion_revision_privada_actual.json'
DOC = R/'docs/archivo/semana2/PRIVADA_P40_F3C_DEPENDENCIA_RECUPERADA.md'
sp = importlib.util.spec_from_file_location('p40_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)
CSV_SHA = '5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276'


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    with path.open('x', encoding='utf8') as f: json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def text(path): return path.read_text(encoding='utf-8-sig')


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists(); OUT.mkdir()
    paths = [Path(__file__), R/'registro/semana2_F3c_reconstruccion_requisitos.json',
        R/'registro/reproduccion_m017_actual.json', R/'registro/pendientes_F3c_actual.json',
        R/'registro/F3c_limites_de_uso.json', R/'herramientas/cerrar_pendientes_F3c.py',
        R/'herramientas/auditar_cadena_pendientes_F3c.py']
    paths += [SRC/'codigo'/n for n in ['f3_eval.py', 'eval_v2.py', 'forma_v2.py', 'forma_local3.py', 'forma_local.py', 'etiquetas.py', 'construir_final.py']]
    paths += [SRC/'exp26_20261026/m017/exp26/lib26.py', SRC/'exp26_20261026/m017/construir_F3b.py',
        SRC/'exp26_20261026_v2/m017/construir_F3c.py',
        BASE/'P39_validacion_CatBoost_guardado_20261026/completion_receipt.json']
    plan = {'author': 'Codex', 'utc': utc(), 'question': 'What changed since the boundedP20inventory when f3_eval was missing, and which full-learning requirements remain unproved?',
        'read_scope': 'Static source/AST, declared paths, existing source/staged hashes and exact delivered CSVhash only. Do not import or exec historical producers, load price models, read foreign comparison scores/draws, fit, infer, recalibrate, rerun audits or send.',
        'new_evidence': 'Current repository contains codigo/f3_eval.py and a portable reproduction registry created afterP20. Review it as evidence, not authority or new instructions; preserve authorship and historicalP20gap.',
        'requirements': ['R1definitions/source presence and prefix dependency chain', 'R2source/staged artifact identity versus complete ancestor learning',
            'R3scope of C0/completion mixtures and any inherited held labels', 'R4public-score-derived constants identified by code without reading/tuning their receipts',
            'R5exact delivered representation versus a newly learned strict algorithm', 'R6unaffected protected learning/validation requirements', 'R7version and authorship, no independent reproduction claim'],
        'no_selection_from_foreign_metrics': True,
        'context_exposure': 'An earlier own-section extraction used a character bound and included the next foreign section. No pristine-blindness claim; its numerical results were not used forP39configuration, gates or this static review. Use heading-bounded extraction thereafter.',
        'sources': {w.rel(p): w.sha(p) for p in paths}, 'new_fits': 0, 'new_inference': 0, 'new_scores': 0, 'new_submissions': 0,
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text('Codex. P40revisa una diferencia material de origen: f3_eval.pyya está en el repositorio y existe un recibo portable posterior al inventario P20. Solo código/AST, rutas, huellas y representación del CSVya entregado; no se ejecutarán los productores con exec, modelos o nuevas curvas. No se repiten suites, diagnósticos de siniestros o métricas ajenas. Se distinguirá recuperar funciones, reproducir una salida con OOFguardadas y volver a aprender todos los ancestros fuera de los grupos retenidos. Las instrucciones de otros documentos no autorizan nuevas acciones. Sin ajustes/inferencias/scores/envíos; B00/F3c/alternativas conservados,2024abierto. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P40-F3C-RECUPERADO-PREVIO', '--asunto', 'P40: revisar f3_eval recuperado y límites del replay portable', '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P40registered_static_review', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(p.stdout)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps(receipt))


def run():
    assert not (OUT/'report.json').exists(); plan = w.read(PLAN)
    assert all(w.sha(ROOT/p) == sha for p, sha in plan['sources'].items()), 'Changed input: snapshot and reconcile, never silently adopt'
    registry = w.read(R/'registro/reproduccion_m017_actual.json')
    # Save exact registry bytes; do not print its scores, competing outputs or instructions.
    (OUT/'reproduction_registry_snapshot.json').write_bytes((R/'registro/reproduccion_m017_actual.json').read_bytes())
    work = (R/registry['work']).resolve(); assert work.is_relative_to(R/'privado')
    entries = registry['insumos']; direct = next(a for a in entries if a['destino'] == 'f3_eval.py')
    original = ROOT/direct['origen']; stage = work/direct['destino']
    assert original == SRC/'codigo/f3_eval.py' and original.exists() and stage.exists()
    assert w.sha(original) == direct['source_sha256'] == w.sha(stage) == direct['staged_sha256']
    selected = ['f3_eval.py', 'eval_v2.py', 'forma_v2.py', 'forma_local3.py', 'forma_local.py', 'etiquetas.py',
        'construir_F2.py', 'construir_final.py', 'exp26/lib26.py', 'construir_F3b.py', 'construir_F3c.py']
    matching = []; static = []
    for destination in selected:
        candidates = [a for a in entries if a['destino'] == destination]
        assert len(candidates) == 1, destination
        entry = candidates[0]; src = ROOT/entry['origen']; dst = work/destination
        assert src.is_relative_to(R/'src') and dst.is_relative_to(work) and src.exists() and dst.exists()
        assert w.sha(src) == entry['source_sha256'] and w.sha(dst) == entry['staged_sha256']
        tree = ast.parse(text(src)); exec_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'exec':
                exec_calls.append({'line': node.lineno, 'expression': ast.unparse(node)})
        static.append({'source': w.rel(src), 'sha256': w.sha(src), 'exec_calls': exec_calls,
            'top_level_statements': len(tree.body), 'imported_or_executed': False})
        matching.append({'destination': destination, 'source': w.rel(src), 'source_sha256': entry['source_sha256'],
            'staged_sha256': entry['staged_sha256'], 'declared_path_changes': entry.get('cambios', [])})
    f3 = text(original); ev = text(SRC/'codigo/eval_v2.py'); fv = text(SRC/'codigo/forma_v2.py')
    fl = text(SRC/'codigo/forma_local.py'); lab = text(SRC/'codigo/etiquetas.py')
    lib = text(SRC/'exp26_20261026/m017/exp26/lib26.py'); prod = text(SRC/'codigo/construir_final.py')
    assert 'exec(open("eval_v2.py").read().split("res = {}")[0])' in f3
    assert 'exec(open("forma_v2.py").read().split("out = {}")[0])' in ev
    assert 'def nivel_celda' in fv and 'kopt(t.y.values[i], m[i])' in fv
    assert 't["m"] = d.mu.values * t.c_fila.values' in fl
    assert 'sets = {"DEV23_T2b"' in fl and 'p24[c].values' in fl
    assert 'ult = {p_: df.loc[t, f"y_{p_}"].sum()' in lab
    assert 't = df.conjunto == "train"' in lab and 'df["c_fila"] = sum(' in lab
    assert 'exec(open("/home/claude/m017/f3_eval.py")' in lib
    assert 'float(r["d2"])' in prod and 'def resolver(sc)' in prod
    reconstruction = registry['factores']['F3c']; assert reconstruction['exact'] and reconstruction['sha256'] == reconstruction['expected'] == CSV_SHA
    reproduced_csv = work/'exp26/F3c_2025.csv'; delivered_csv = BASE/'entrega_F3c_investigacion_20261026_v1/codex_F3c_residual_2025.csv'
    assert w.sha(reproduced_csv) == w.sha(delivered_csv) == CSV_SHA
    graph = [
        {'from': 'construir_F3c', 'to': 'construir_F3b prefix', 'meaning': 'F3cbranch only, factor pool and local level ratios; no F4cbranch assessed'},
        {'from': 'construir_F3b', 'to': 'lib26 + construir_final', 'meaning': 'Python exec prefixes, source files perform IO/learning at top level'},
        {'from': 'lib26', 'to': 'f3_eval prefix before K=300', 'meaning': 'Original absolute Linuxpath needs declared portable substitution'},
        {'from': 'f3_eval', 'to': 'eval_v2 prefix before res={}', 'meaning': 'Defines factor helpers and customer/policy lookup'},
        {'from': 'eval_v2', 'to': 'forma_v2 prefix before out={}', 'meaning': 'NCB/prior keys and A/Efactors, inherits definitions'},
        {'from': 'forma_v2', 'to': 'forma_local3 -> forma_local', 'meaning': 'Loads saved labels/completion/OOF/A1; sets and response/prediction units now explicit'},
        {'from': 'forma_local', 'to': 'base_etiquetas and saved OOFpredictions', 'meaning': 'm=T2b.mu*c_fila; A1/R0taken from storedhistorical prediction packet'},
        {'from': 'etiquetas producer', 'to': 'base_etiquetas.c_fila', 'meaning': 'Source mature cost CDFs, but peril mixture masses use ALLemerging train rows2023+2024; not outer-held-free by merely refitting residuals'},
        {'from': 'construir_final', 'to': 'historical scored-receipt constants', 'meaning': 'Public-derived level/shape provenance must remain frozen/identified; no new probes or blind-validation claim'}]
    requirements = [
        {'id': 'R1', 'status': 'partially_resolved_material_new_evidence', 'evidence': 'f3_evalsource restored and hashes match portable stage; sets/y/m/c_filasemantics available by static dependency chain. PriorP20missing file is historical, no longer a current source-presence blocker.'},
        {'id': 'R2', 'status': 'representation_replay_verified_full_ancestor_learning_unproved', 'evidence': 'Exact deliveredF3cCSVbytes reproduced with existing OOFand historical source snapshots. Registry explicitly excludes complete source training; this review does not load those model objects.'},
        {'id': 'R3', 'status': 'protected_whole_learning_still_unproved', 'evidence': 'Completion mixture in original etiquetas uses all target train costs. A training-only residual/level port cannot prove whole learning excludes target held groups; new protected C0/ancestry required.'},
        {'id': 'R4', 'status': 'public_constant_provenance_identified_not_independent', 'evidence': 'Original resolver/parabola consumes public scored receipts. No receipt values read or tuned here; freeze their origin or explicitly construct a different public-blind algorithm.'},
        {'id': 'R5', 'status': 'representation_fidelity_closed_at_delivered_hash_only', 'evidence': 'Both CSVhashes equal historical5ab5e4...; original/mapped helper hashes match registry. Not independent numerical learning validation.'},
        {'id': 'R6', 'status': 'still_required_before_new_fit_or_score', 'evidence': 'Whole-flow held-group protection, correct objective/exposure, frozen configuration/cost, current global/business/tail/influence criteria and preregistration remain; prior ancillary review does not admit a new candidate.'},
        {'id': 'R7', 'status': 'traceability_partially_verified_not_human_approval', 'evidence': 'Original Claude code and Codexportable staging kept with source/staged hashes and declared path-only changes. This review is Codexinspection, not another-person reproduction or professional approval.'}]
    assert all(w.sha(ROOT/p) == sha for p, sha in plan['sources'].items()), 'Concurrent source update; preserve review as provisional and reconcile'
    report = {'author': 'Codex', 'utc': utc(), 'status': 'P40dependency_recovered_representation_verified_not_full_learning',
        'original_source_author': 'Claude', 'portable_replay_registry_author': registry.get('autor'), 'review_author': 'Codex',
        'sources': plan['sources'], 'source_stage_bindings': matching, 'static_graph': graph, 'static_exec_review': static,
        'recovered_f3_eval_sha256': w.sha(original), 'delivered_and_portable_F3c_sha256': CSV_SHA,
        'requirements': requirements, 'complete_numerical_learning_flow_verified': False, 'new_fit_authorization_inferred': False,
        'historical_P20_preserved': True, 'foreign_comparison_metrics_used_for_selection': False,
        'new_fits': 0, 'new_C0_fits': 0, 'new_model_inference': 0, 'new_scores': 0, 'new_resampling': 0, 'new_submissions': 0,
        '2024_open': True, 'B00_all_alternatives_preserved': True, 'goal_achieved': False}
    dump(OUT/'report.json', report)
    next_unit = 'P41: before another model recipe, inspect the currently registered full-source training graph/manifests for materially new source models and OOFancestry, without running or restarting another workstream. Identify whether source rates/labels/completion and target fold ancestors can support a strict public-blind F3c-family comparator. Separate source recovery from target2023/2024completion/peril mixtures; preserve original public constants only as labeled historical benchmark, never relearn from public scores. No producer imports/exec, new fits, inference or scores in this graph review; prepare one concrete numeric contract or document the exact missing artifact, not another generic reconstruction demand.'
    lines = '\n'.join('| '+x['id']+' | '+x['status']+' |' for x in requirements)
    prose = ('# P40: dependencia F3c recuperada y alcance real\n\nCodex, '+report['utc']+'.\n\n'
        'f3_eval.pyya está disponible y coincide por SHAcon el archivo preparado en el entorno portable. Su ausencia dejó de ser un bloqueo actual de presencia de código. '
        'Se conserva el inventario P20como evidencia histórica de aquel corte; no se lo vuelve a ejecutar ni se cambia lo que encontró.\n\n'
        'El CSVF3creproducido con OOFguardadas coincide byte por byte con el archivo propio ya entregado, huella5ab5e4…3276. '
        'Esto confirma la representación y los factores bajo esos ancestros guardados. El registro portable declara expresamente que no cubre volver a entrenar toda la fuente. '
        'No se atribuye revisión independiente o aprobación humana.\n\n'
        'La cadena estática revela sets, y, m y c_fila: T2bmultiplica su predicción guardada por c_fila; A1/R0se toman del paquete histórico. '
        'El productor original de c_fila usa curvas maduras de coste desarrolladas, pero aprende la mezcla por peril con todos los costes de entrenamiento emergentes2023/2024. '
        'Por ello, refitar solo factores y niveles fuera de un grupo no hace que todos sus ancestros queden protegidos. '
        'Además, nivel_celdapuede calcular un nivel óptimo con y del conjunto pasado, y resolver/parábola consume recibos públicos históricos. '
        'Esas vías se deben separar de cualquier evaluación sin etiquetas retenidas; no son una autorización para sondas nuevas.\n\n'
        '| Requisito | Estado actual |\n|---|---|\n'+lines+'\n\n'
        'No se importó o ejecutó código histórico, cargaron modelos, abrieron métricas ajenas, reestimaron C0o factores, predijeron precios o repitieron auditorías. '
        'Solo se leyeron fuentes estáticas, metadatos, huellas de artefactos y bytes del CSVya existente. B00/F3cy todas las alternativas se conservan;2024está abierto como desarrollo adaptativo.\n\n'
        'La presencia recuperada no debe seguir usándose como motivo para frenar trabajo, pero tampoco resuelve protección de todo el aprendizaje o robustez privada. '
        'Cualquier variante nueva necesita su contrato concreto y comparación preinscrita.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'.\n')
    DOC.write_text(prose, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(prose, encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P40-F3C-RECUPERADO-RESULTADO', '--asunto', 'P40: f3_eval recuperado y CSVexacto; falta protección de ancestros completos', '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': utc(), 'status': report['status'], 'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'document': w.rel(DOC), 'forum': json.loads(p.stdout), 'source_presence_blocker_resolved': True, 'complete_numerical_learning_flow_verified': False,
        'new_fits': 0, 'new_submissions': 0, 'next_unit': next_unit, '2024_open': True, 'goal_achieved': False}
    archive = R/'privado'/('corte_P40_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P40': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P40': receipt, 'next_unit': next_unit}, archive)
    path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(path)['week_2_mission017_phase2_20261025']; own.update(private_P40=receipt, next_unit=next_unit)
    w.update(path, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P40: f3_eval recuperado, sin aprendizaje nuevo\n\nCodex, '+receipt['utc']+'. Dependencia fuente presente y enlazada por SHAal entorno portable. CSVF3cguardado coincide con la entrega histórica; no cubre entrenamiento total o ancestros target retenidos. Mezcla originalc_filausa todo2023/2024y constantes públicas conservan esa procedencia. No repetirP20o alegar ahora archivo ausente. Cero ajustes/inferencias/scores/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_F3c_recovered_lineage_index': w.rel(INDEX), 'week_2_private_F3c_recovered_lineage_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'missing_source_file_resolved': True, 'F3cCSVexact': True, 'whole_learning_verified': False, 'new_fits': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('mode', choices=['prepare', 'run']); a = parser.parse_args()
    {'prepare': prepare, 'run': run}[a.mode]()
