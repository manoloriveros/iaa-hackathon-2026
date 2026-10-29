"""Registra un recibo COMPLETE de Kaggle sin modelos, inferencia o entrenamiento."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path('C:/dev/Hakaton')
REPO = ROOT / 'Hackaton/Repositorio_IAA2026'
OUT = REPO / 'privado/semana2/envios/g4_20261025_v1'
INDEX = REPO / 'registro/semana2_g4_envio_kaggle_actual.json'
DOC = REPO / 'docs/archivo/semana2/ENVIO_G4_KAGGLE_20261025.md'
FID = 'COD-S2-20261025-G4-ENVIO-RESULTADO'
IDENT = 'S2-G4-KAGGLE-SCORED-v1-20261025'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
now = lambda: datetime.now(timezone.utc).isoformat()


def dump(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def top(raw, key, value):
    encoded = json.dumps(value, ensure_ascii=False, indent=2).replace('\n', '\n  ')
    if key not in json.loads(raw):
        return raw[:raw.rfind('}')].rstrip() + ',\n  ' + json.dumps(key) + ': ' + encoded + '\n}\n'
    match = re.search(r'(?m)^  ' + re.escape(json.dumps(key)) + r':\s*', raw)
    assert match, key
    _, end = json.JSONDecoder().raw_decode(raw[match.end():])
    return raw[:match.end()] + encoded + raw[match.end() + end:]


def main():
    assert not INDEX.exists(), 'Conciliar registro parcial antes de repetir'
    evidence = read(OUT / 'scoring_check_02.json')
    response = read(OUT / 'submission_response.json')
    local = read(OUT / 'local_preflight.json')
    row = evidence['submission']
    assert row['status'] == 'COMPLETE' and row['ref'] == response['ref'] == 57628123
    assert row['error'] == '' and row['public_score'] == '0.13310'
    assert row['total_bytes'] == response['bytes'] == 6248900
    assert row['description'] == local['message'] == response['message']
    assert evidence['CSV_hash_unchanged'] and sha(Path(response['CSV'])) == local['sha256']
    assert evidence['new_fit_calls'] == 0 and not evidence['2024_policy_data_or_metrics_read']
    original_index = REPO / 'registro/semana2_g4_entrega_final_actual.json'
    original = read(original_index)
    assert original['CSV']['sha256'] == local['sha256'] and original['reference'] == 'W2-B00'
    preserved_paths = [ROOT / original['CSV']['path'], ROOT / original['packet']['path'],
        REPO / 'registro/semana2_contadores_propios_actual.json',
        REPO / 'registro/semana2_continuidad_nocturna.json',
        REPO / 'registro/semana2_g4_modelo_final_plan_v1.json',
        REPO / 'privado/semana2/desarrollo2023/ridge20_20261024_v1/report.json',
        REPO / 'privado/semana2/desarrollo2023/ridge20_20261024_v1/manifest.json']
    preserved_paths += [ROOT / original['run'] / 'attempt1/models' / (line + '.joblib')
                        for line in ('motor', 'buildings', 'contents')]
    preserved = {rel(p): sha(p) for p in preserved_paths}
    result = {'id': IDENT, 'author': 'Codex', 'utc': now(),
        'status': 'Kaggle_COMPLETE_public_score_recorded', 'competition': evidence['competition'],
        'competition_url': 'https://www.kaggle.com/competitions/' + evidence['competition'],
        'model_id': original['model_id'], 'submission_ref': row['ref'],
        'submitted_utc': row['date'] + 'Z', 'processing_verified_utc': evidence['utc'],
        'Kaggle_status': row['status'], 'public_score_text': row['public_score'],
        'public_score': float(row['public_score']), 'metric': 'D2 Tweedie Score, power 1.5',
        'CSV': original['CSV'], 'server_filename': row['file_name'], 'server_bytes': row['total_bytes'],
        'message': row['description'], 'submission_attempts': 1, 'submission_slots_used': 1,
        'submissions_left_at_check': evidence['limits']['num_allowed_now'],
        'forum_prior': 'COD-S2-20261025-G4-ENVIO-PREVIO', 'forum_result': FID,
        'documentation': rel(DOC), 'private_receipts': rel(OUT),
        'local_preflight': {'path': rel(OUT / 'local_preflight.json'), 'sha256': sha(OUT / 'local_preflight.json')},
        'server_receipt': {'path': rel(OUT / 'scoring_check_02.json'), 'sha256': sha(OUT / 'scoring_check_02.json')},
        'prior_2023_recipe_evidence': original['previous_2023_recipe_evidence'],
        'prior_replay': original['replay'], 'new_fit_calls': 0, 'new_predictions': 0,
        'C0_reestimated': False, '2024_policy_data_or_metrics_read': False,
        '2024_closed': True, 'reference': 'W2-B00', 'all_alternatives_preserved': True,
        'G1_G2_resolved': False, 'promotion': False, 'manual_final_selection': False,
        'professional_independent_validation': False, 'remote_training': False,
        'private_score_consulted': False, 'other_submission_scores_consulted': False}
    body = f'''# Envío propio G4 procesado en Kaggle

Kaggle procesó el CSV propio G4 y devolvió estado COMPLETE, sin error, con D² Tweedie público de **0,13310**. Se envió el archivo congelado de 209.063 predicciones de 2025, sin reentrenar, recalcular C0 o generar nuevas inferencias. B00 y las alternativas se conservan; 2024 sigue cerrado.

Codex, {result['utc']}. El participante autorizó expresamente enviar el CSV y verificar su procesamiento. La autorización se refiere a esta entrega; no equivale a aprobación técnica profesional ni a promoción formal. El envío se hizo el 25 de octubre de 2026 a las 06:26:10 Bogotá (11:26:10 UTC), en la competición [IAA AI Assisted Hackathon 2026, Part 2]({result['competition_url']}).

| Comprobación | Resultado |
| --- | --- |
| Identificador de Kaggle | {row['ref']} |
| Estado del servidor | COMPLETE |
| Score público D² Tweedie | 0,13310 |
| Filas | 209.063 |
| Archivo | {row['file_name']} |
| Tamaño cotejado en servidor | 6.248.900 bytes |
| Recepción y procesamiento | ID, competición, mensaje, nombre y tamaño coinciden |
| Cupos consumidos en esta entrega | 1 |
| Disponibles en la última consulta | 6 |
| Nuevos ajustes o predicciones | 0 |

## Evidencia y alcance

La revisión de salida confirmó la misma huella SHA256, IDs únicos y orden idéntico a la plantilla emergente, dos columnas correctas y valores positivos finitos. El dry-run del skill aprobó cinco comprobaciones de formato. La consulta previa autenticada no encontró otro envío de este archivo o mensaje. Se hizo una única carga; después se siguió exclusivamente el identificador devuelto por esa carga, primero PENDING y luego COMPLETE. No se leyó el score privado ni scores o mensajes de otros envíos.

La huella local se comprobó de nuevo tras el procesamiento: `e5e30c5921c0494b7c0bebe76fbf33725f45ab392f7bed5ab7f6927a89f394ab`. El cotejo remoto confirma identidad de registro y tamaño; Kaggle no devolvió una huella criptográfica del contenido. Se conserva el replay exacto anterior del archivo y no se repitió. El paquete de código/modelos permanece privado y no se subió: solo se envió el CSV a la competición.

La receta histórica B20 tiene D² OOF2023 de 0,08938 frente a 0,06858 de B00; esa evidencia exploratoria se conserva, sin nuevos ensayos. El público actual mide otro conjunto y no demuestra que las carencias de mecanismo, soporte o concentración hayan desaparecido. G1/G2 y el ensayo de calibración anidada original siguen pendientes. Este CSV usa los GLM estándar sin recalibración. No se retiró B00, se modificó una receta o se cambió la selección final manual en Kaggle.

Los modelos finales siguen ajustados solo con 2023; las predicciones corresponden a 2025. En esta operación no se abrieron pólizas, predicciones, métricas, ledger, actas o SEL01 de 2024. Tampoco hubo entrenamiento remoto, nuevos chats, delegación, publicaciones de código/modelos o cambios de automatizaciones. La verificación es propia de Codex, sin atribuir revisión actuarial profesional independiente.

## Recibos

Índice: `{rel(INDEX)}`. Recibos locales y autenticados: `{rel(OUT)}` (`local_preflight.json`, `remote_preflight.json`, `skill_dry_run.txt`, `submission_response.json`, `scoring_check_01.json`, `scoring_check_02.json`). Foro previo COD-S2-20261025-G4-ENVIO-PREVIO; resultado {FID}. CSV: `{original['CSV']['path']}`. El conjunto de recibos conserva las fuentes/SHA y los cambios documentales de esta entrega, sin alterar las corridas históricas.
'''
    DOC.parent.mkdir(parents=True, exist_ok=True)
    with DOC.open('x', encoding='utf-8') as f:
        f.write(body)
    result['documentation_sha256'] = sha(DOC)
    dump(INDEX, result)
    changes = []

    def change(path, transform, keys=None):
        before = path.read_bytes()
        raw = before.decode('utf-8-sig')
        transformed = transform(raw)
        if keys is not None:
            old, new = json.loads(raw), json.loads(transformed)
            assert {k: v for k, v in old.items() if k not in keys} == {k: v for k, v in new.items() if k not in keys}
        after = transformed.encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):
            after = b'\xef\xbb\xbf' + after
        for phase, payload in [('before', before), ('after', after)]:
            snapshot = OUT / 'registration_cuts' / phase / path.relative_to(ROOT)
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            with snapshot.open('xb') as f:
                f.write(payload)
        temporary = path.with_name(path.name + '.G4submission.tmp')
        with temporary.open('xb') as f:
            f.write(after)
            f.flush()
            os.fsync(f.fileno())
        assert path.read_bytes() == before, 'Concurrent edit: ' + rel(path)
        os.replace(temporary, path)
        changes.append({'path': rel(path), 'before_sha256': hashlib.sha256(before).hexdigest(), 'after_sha256': sha(path)})

    def updates(raw, values):
        for key, value in values.items():
            raw = top(raw, key, value)
        return raw

    link = {'index': rel(INDEX), 'documentation': rel(DOC), 'submission_ref': row['ref'],
            'utc': now(), 'status': 'COMPLETE', 'public_score': row['public_score'],
            'new_fit_calls': 0, '2024_closed': True}
    idx_updates = {'status': 'own_standard_model_CSV_Kaggle_COMPLETE_2023_only_2024_closed',
        'submission_sent': True, 'submission_processed': True, 'Kaggle_score': float(row['public_score']),
        'Kaggle_submission': link}
    change(original_index, lambda raw: updates(raw, idx_updates), set(idx_updates))

    state = ROOT / 'Preparación/ESTADO_PROYECTO.json'
    oldkey = 'week_2_G4_own_model_and_CSV2025_ready_v1_20261024'
    newkey = 'week_2_G4_own_CSV_Kaggle_processed_20261025'
    def state_update(raw):
        branch = deepcopy(json.loads(raw)[oldkey])
        branch.update(idx_updates)
        return updates(raw, {oldkey: branch, newkey: result})
    change(state, state_update, {oldkey, newkey})
    development = REPO / 'registro/semana2_desarrollo2023_actual.json'
    def development_update(raw):
        branch = deepcopy(json.loads(raw)['G4_final_standard_deployment'])
        branch.update(status='CSV_Kaggle_COMPLETE', submission_sent=True, Kaggle_submission=link)
        return top(raw, 'G4_final_standard_deployment', branch)
    change(development, development_update, {'G4_final_standard_deployment'})
    routes = {'week_2_G4_own_submission_index': rel(INDEX), 'week_2_G4_own_submission_report': rel(DOC)}
    change(ROOT / 'RUTAS_PROYECTO.json', lambda raw: updates(raw, routes), set(routes))
    note = f'''\n\n## G4: CSV propio procesado en Kaggle, 25 de octubre de 2026

Codex, UTC {now()}. Instrucción humana directa: enviar el CSV propio, verificar procesamiento y registrar resultado, sin entrenar; B00 conservado y 2024 cerrado. Previo COD-S2-20261025-G4-ENVIO-PREVIO; resultado {FID}. Índice {rel(INDEX)}, informe {rel(DOC)}, recibos {rel(OUT)}.

Envío único {row['ref']}, competición {evidence['competition']}, fecha UTC {row['date']}Z. CSV209063 filas, {row['total_bytes']}bytes, SHA256 {local['sha256']}; misma huella antes/después, IDs/orden/formato/valores comprobados. Recepción cotejada por ID, competición, nombre, mensaje y tamaño. Estado COMPLETE, D² Tweedie público {row['public_score']}, sin error. De7a6cupos disponibles; un cupo consumido. Kaggle no devolvió SHA remoto: cotejo de registro/tamaño, no certificación criptográfica del lado servidor.

0fits,0nuevasinferencias,0C0; sin diagnósticos repetidos. Replay anterior reutilizado. B00/modelos/alternativas/capital/C0 intactos; G1/G2 y calibración original siguen pendientes. Público distinto de OOF2023; sin promoción, ajuste por leaderboard o cambio manual final. No se accedió a score privado, scores/mensajes ajenos, pólizas/predicciones/métricas/ledger/actas/SEL012024. Paquete de código/modelos privado no publicado. Autorización humana de envío, no aprobación profesional inventada. Sin remoto, delegación, otroschats o automatizaciones.
'''
    for name in ('MEMORIA_PROYECTO.md', 'DECISIONES.md'):
        change(ROOT / 'Preparación' / name, lambda raw: raw.rstrip() + note)
    forum_body = OUT / 'forum_result.md'
    with forum_body.open('x', encoding='utf-8') as f:
        f.write(body.replace('# Envío propio G4 procesado en Kaggle\n', '', 1))
    proc = subprocess.run([str(ROOT / 'Preparación/.venv/Scripts/python.exe'),
        str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', FID,
        '--asunto', 'CSV propio G4 procesado por Kaggle, sin reentrenar', '--cuerpo', str(forum_body)],
        capture_output=True, text=True, encoding='utf-8', check=True)
    forum_receipt = json.loads(proc.stdout)
    dump(OUT / 'forum_result_receipt.json', forum_receipt)
    assert preserved == {rel(p): sha(p) for p in preserved_paths}
    dump(OUT / 'registration_receipt.json', {'utc': now(), 'id': IDENT, 'shared_changes': changes,
        'unrelated_top_level_keys_preserved': True, 'preserved_artifact_hashes': preserved,
        'CSV_hash_unchanged': True, 'new_fit_calls': 0, 'forum': forum_receipt,
        'readback': {'index': sha(INDEX), 'documentation': sha(DOC)}, '2024_closed': True})
    files = sorted(p for p in OUT.rglob('*') if p.is_file())
    dump(OUT / 'manifest.json', {'id': IDENT, 'utc': now(),
        'files': [{'path': rel(p), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in files]})
    print(json.dumps({'id': IDENT, 'status': row['status'], 'public_score': row['public_score'],
        'ref': row['ref'], 'index': rel(INDEX), 'documentation': rel(DOC),
        'forum': forum_receipt, 'shared_files_updated': len(changes),
        'preserved_hashes_verified': len(preserved), 'manifest_files': len(files)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
