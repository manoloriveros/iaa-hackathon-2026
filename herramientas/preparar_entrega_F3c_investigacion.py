"""Revisión concreta de F3c recibido: excepción de investigación, nunca promoción formal."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import argparse
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
spec = importlib.util.spec_from_file_location('writer_F3_delivery', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
import numpy as np
import pandas as pd

BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'entrega_F3c_investigacion_20261026_v1'
SOURCE = R / 'privado/semana2/claude_mision017_20261025/F3c_2025.csv'
CSV = OUT / 'codex_F3c_residual_2025.csv'
SHA = '5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276'
POLICY = R / 'registro/semana2_mision017_F3c_revision_entrega_v1.json'
MESSAGE = 'Codex F3c residual factors | source Claude; reviewed Codex | 5ab5e4e34290cf6e | research, no formal promotion'
now = lambda: datetime.now(timezone.utc).isoformat()

def register():
    assert not OUT.exists() and not POLICY.exists(); OUT.mkdir(parents=True)
    received = BASE / 'aportes_F3c_F4c_20261026_v2/report.json'; rec = w.read(received)
    assert w.sha(SOURCE) == SHA == rec['candidates']['F3c']['sha256']
    status_path = BASE / 'estado_publico_20261026_v2/receipt.json'; status = w.read(status_path)
    assert status['limits']['num_allowed_now'] == 1 and status['best_processed_public']['public_score'] == .16519
    v10path = BASE / 'tanda10_factores_20261026_v1/validation_v1/report.json'; v10 = w.read(v10path)
    v11path = BASE / 'tanda11_conjunto_20261026_v1/validation_v1/report.json'; v11 = w.read(v11path)
    scope_policy = R / 'registro/semana2_politica_desarrollo2024_v2.json'
    sources = [Path(__file__), SOURCE, received, status_path, v10path, v11path, scope_policy,
        BASE / 'calibracion_F2_creible_20261025_v1/public_receipt.json',
        BASE / 'calibracion_F2_creible_20261025_v1/final_creible_2025.csv',
        BASE / 'aportes_F3c_F4c_20261026_v2/F3c_multiplier_intervals.csv']
    policy = {'id': 'S2-MISION017-F3c-RESEARCH-REVIEW-v1', 'author_decision': 'Codex', 'utc': now(),
        'status': 'research_review_registered_before_replay_and_any_submission',
        'human_authorization_in_thread': ['Dale, envía el CSV propio a Kaggle, verifica que se procese y deja el resultado en el foro.',
            'continua de manera automática hasta que finalices, no me preguntes más y tomas todas las decisiones que consideres necesarias',
            '2024 no tiene que estar bloqueado, usa todo lo que tenemos y necesites que nos lleve a mejorar significativamente el modelo'],
        'no_new_human_approval_inferred_from_AI_documents': True,
        'scope': 'A single research delivery under existing human authority; excludes formal candidate promotion or manual final selection',
        'candidate_source_author': 'Claude', 'review_and_transport_author': 'Codex',
        'CSV_source': w.rel(SOURCE), 'CSV_sha256': SHA, 'copy_bytes_unchanged': True,
        'hypothesis': 'The simple residual gender/telework/marketing signal can improve the measured C1 in2025, without uncertain FSp or changing its base risk recipe.',
        'support': {'own_G3_delta': v10['comparisons']['G3']['delta'], 'own_G3_simultaneous95': v10['comparisons']['G3']['simultaneous95_3'],
            'own_G3_both_years_positive': v10['comparisons']['G3']['gates']['both_years_nonnegative'],
            'own_G3_all_six_segments_nonnegative': v10['comparisons']['G3']['min_cell_delta'] >= 0,
            'own_G3_post31_delta': v10['comparisons']['G3']['after_remove31_delta'],
            'received_motor_gender_frequency_mechanism': 'Received I report, stable across years and business; not independently professionally validated',
            'joint_solver_not_a_material_improvement': v11['matched_sequential_delta']},
        'failed_gates_preserved': {'own_G3_delta_below002': True, 'own_G3_positive_folds': 3,
            'own_G3_A1_original_proxy_delta': v10['original_A1_2024_proxy']['G3']['weighted2024_delta'],
            'full_C1_or_F3c_learning_historical_replay_available': False,
            'weighted2025_primary_ESS_gate_pass': False},
        'why_a_research_exception': 'Positive mean evidence in both years and simultaneous component interval, no adverse six-cell point contribution, a nonnegative though fragile post31G3result and a received homogeneous frequency mechanism justify one measured full-model step. This explicitly does not pass the original promotion criteria; last-slot use is a Codex research decision, not new human approval or a threshold change.',
        'limits': ['F3c is a received trained artifact; own G3 is a distinct protected N3 scope and does not reproduce full C1/F3c learning',
            'CSV multiplier decoding/replay is an artifact representation check derived from outputs, not independent model training reproduction',
            'Adaptive variable/model/public calibration search; public receipt will not be independent confirmation or formal promotion',
            'NB support and undated master availability unresolved; telework NB severity sparse, marketing weaker',
            'Last known available slot1; no F4c, probes, fallback upload or resubmit on uncertain receipt'],
        'received_forecast_only': {'central': .1666, 'interval80': [.1647, .1682], 'source': 'Claude preinscription v2; not own validated prediction',
            'expected_below_goal': True},
        'required_before_upload': ['unchanged source/copy SHA and source hashes', 'artifact-only multiplier replay with bounded rounding',
            'official skill dryrun all5pass', 'current own quota and exact duplicate check', 'exclusive start marker and at most1APIupload'],
        'budget': {'max_new_submissions': 1, 'new_fits': 0, 'new_C0_fits': 0, 'new_model_inferences': 0,
            'replay_rows': 209063, 'quota_available_must_be_at_least': 1},
        'manual_final_selection': False, 'formal_promotion': False, 'B00_preserved': True,
        '2024_open': True, 'goal_achieved': False, 'message': MESSAGE,
        'sources': {w.rel(p): w.sha(p) for p in sources}}
    POLICY.write_text(json.dumps(policy, ensure_ascii=False, indent=2), encoding='utf8')
    body = OUT / 'forum_previo.md'
    body.write_text('Se registra una revisión de entrega de investigación de F3c, receta de Claude sobre el C1 ya medido. '
        'Codex decide preparar un único envío bajo las instrucciones humanas vigentes de enviar, continuar automáticamente y decidir sin volver a preguntar. '
        'No se infiere permiso de una ficha de IA. Se emplearía el último cupo conocido. No se modifica la selección final.\n\n'
        'La justificación es la señal sencilla: G3 propio gana en ambos años, tiene intervalo simultáneo positivo, no pierde en ninguno de los seis segmentos '
        'y conserva diferencia apenas positiva tras31grupos, junto al mecanismo de frecuencia de género recibido. '
        'Se conservan expresamente sus fallos: menos de+0,002, solo3folds positivos y A1 original2024 ligeramente negativo. '
        'El ajuste conjunto no resolvió esos límites. Esto es una excepción para investigación, no una promoción ni una relajación retrospectiva de los criterios.\n\n'
        'Se revisará la aplicación de los multiplicadores de F3c sobre C1 y la copia será byte idéntica al archivo recibido. '
        'La reproducción de esos multiplicadores se deriva del propio CSV, por lo que no certifica su aprendizaje histórico o el C1 completo. '
        'La previsión recibida0,1666 no es un score y queda por debajo de0,17. '
        'Antes de cualquier carga faltan replay acotado, dryrun oficial, cuota y control de duplicados. '
        'Máximo un envío; cero entrenamientos/C0, F4c o sondas. B00, C1/F2 y alternativas se conservan;2024 abierto. '
        'Decisión y límites: ' + w.rel(POLICY) + '.\n', encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-MISION017-F3c-INVESTIGACION-PREVIO', '--asunto',
        'F3c: excepción explícita para un envío de investigación, sin promoción ni cambio de criterios', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    (OUT / 'registration.json').write_text(json.dumps({'policy_sha256': w.sha(POLICY), 'forum': json.loads(response.stdout)}, indent=2), encoding='utf8')
    print(json.dumps({'registered': w.rel(POLICY), 'max_new_submissions': 1, 'last_known_slots': 1, 'new_fits': 0,
        'promotion_gates_passed': False, 'research_exception_only': True}))

def replay():
    assert not (OUT / 'replay_report.json').exists()
    policy = w.read(POLICY); assert w.read(OUT / 'registration.json')['policy_sha256'] == w.sha(POLICY)
    for path, value in policy['sources'].items(): assert w.sha(ROOT / path) == value, path
    CSV.write_bytes(SOURCE.read_bytes()); assert w.sha(CSV) == SHA
    base_path = BASE / 'calibracion_F2_creible_20261025_v1/final_creible_2025.csv'
    base = pd.read_csv(base_path, dtype={'row_id': str}); received = pd.read_csv(CSV, dtype={'row_id': str})
    registry = pd.read_csv(BASE / 'aportes_F3c_F4c_20261026_v2/F3c_multiplier_intervals.csv')
    registry['multiplier'] = .5 * (registry.constant_multiplier_interval_lower + registry.constant_multiplier_interval_upper)
    raw = ROOT / 'Hackaton/Semana 2/Datos/emerging'; customers = pd.read_parquet(raw / 'customers.parquet', columns=['customer_id', 'gender', 'marketing_segment'])
    frames = []
    for line in ['motor', 'buildings', 'contents']:
        cols = ['row_id', 'customer_id', 'new_business'] + (['works_from_home'] if line == 'contents' else [])
        f = pd.read_parquet(raw / f'test_{line}.parquet', columns=cols).merge(customers, on='customer_id', validate='many_to_one')
        f['line'] = line
        if line != 'contents': f['works_from_home'] = 'not_used'; f['marketing_segment'] = 'not_used'
        if line == 'buildings': f['gender'] = 'not_used'
        f['works_from_home'] = f.works_from_home.astype(str); frames.append(f)
    cov = pd.concat(frames, ignore_index=True).set_index('row_id').loc[base.row_id].reset_index()
    keys = ['line', 'new_business', 'gender', 'works_from_home', 'marketing_segment']
    cov = cov.merge(registry[keys + ['multiplier']], on=keys, validate='many_to_one', how='left')
    assert np.array_equal(cov.row_id, base.row_id) and cov.multiplier.notna().all()
    prediction = base.prediction.to_numpy(float) * cov.multiplier.to_numpy(float)
    difference = np.abs(prediction - received.prediction.to_numpy(float)); assert difference.max() <= .5001e-6
    replayed = base[['row_id']].copy(); replayed['prediction'] = prediction
    replay_path = OUT / 'artifact_replay_2025.csv'; replayed.to_csv(replay_path, index=False, float_format='%.6f', lineterminator='\n')
    formatted = pd.read_csv(replay_path, dtype={'row_id': str})
    max_written = float(np.max(abs(formatted.prediction.to_numpy(float) - received.prediction.to_numpy(float))))
    assert max_written <= 1.0001e-6
    # Decimal is an arithmetic check only; parameters were decoded from the
    # output artifact and are never presented as independent training evidence.
    base_text = pd.read_csv(base_path, dtype=str)
    chosen = sorted(set([0, len(base) - 1, *np.argsort(prediction)[:5], *np.argsort(prediction)[-5:]]))
    decimal_errors = []
    with localcontext() as ctx:
        ctx.prec = 60
        for i in chosen:
            value = Decimal(base_text.prediction.iloc[i]) * Decimal(str(cov.multiplier.iloc[i]))
            err = abs(float(value) - prediction[i]); assert err < 1e-9
            decimal_errors.append({'row_number': int(i), 'absolute_float_vs_Decimal_error': err})
    registry.to_csv(OUT / 'decoded_artifact_multiplier_registry.csv', index=False)
    result = {'author': 'Codex', 'utc': now(), 'source_author': 'Claude', 'review_author': 'Codex',
        'kind': 'Artifact representation/replay only, output-derived registry, NOT independent training reproduction',
        'source_sha256': SHA, 'CSV_copy_sha256': w.sha(CSV), 'CSV_copy_byte_identical': CSV.read_bytes() == SOURCE.read_bytes(),
        'rows': len(base), 'decoded_patterns': len(registry), 'max_absolute_before_rounding': float(difference.max()),
        'max_absolute_after_rounding': max_written, 'replay_byte_identical': replay_path.read_bytes() == CSV.read_bytes(),
        'replay_sha256': w.sha(replay_path), 'Decimal_sample': decimal_errors, 'no_labels_used': True,
        'new_fits': 0, 'new_C0_fits': 0, 'new_model_inferences': 0, 'new_submissions': 0,
        'policy_sha256': w.sha(POLICY), 'code_sha256': w.sha(Path(__file__))}
    (OUT / 'replay_report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    spec = {'path': w.rel(CSV), 'sha256': w.sha(CSV), 'rows': len(received), 'bytes': CSV.stat().st_size,
        'total': float(received.prediction.sum())}
    (OUT / 'CSV_spec.json').write_text(json.dumps(spec, indent=2), encoding='utf8')
    print(json.dumps({'CSV': spec, 'artifact_replay_only': True, 'replay_byte_identical': result['replay_byte_identical'],
        'max_rounding_error': max_written, 'new_fits': 0, 'new_submissions': 0}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['register', 'replay']); args = parser.parse_args()
    register() if args.mode == 'register' else replay()
