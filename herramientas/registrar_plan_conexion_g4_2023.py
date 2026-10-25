"""Congela la conexión sin ajuste antes de verificarla."""
from pathlib import Path
from datetime import datetime, timezone
import json
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(REPO/'src'))
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import entradas_g4_2023 as ingress
RUN = REPO/'privado/semana2/conexion_g4_2023/contrato_20261024_v1'
PLAN = REPO/'registro/semana2_g4_conexion_plan_v1.json'
rel = lambda p: p.relative_to(ROOT).as_posix()


def main():
    assert not PLAN.exists()
    RUN.mkdir(parents=True, exist_ok=False)
    index_path = REPO/'registro/semana2_g4_entradas2023_actual.json'
    index = json.loads(index_path.read_text(encoding='utf-8'))
    source = index['input_manifest']
    assert ingress.sha(ROOT/source['path']) == source['sha256']
    frozen = []
    for relative in ['src/semana2/conexion_g4_2023.py', 'src/semana2/entradas_g4_2023.py',
        'src/semana2/ambitos_c0_b20_2023.py', 'herramientas/probar_conexion_g4_2023.py',
        'herramientas/validar_conexion_g4_2023.py', 'registro/semana2_g4_capital_contrato_v1.json']:
        p = REPO/relative
        copy = RUN/'preregistered_sources'/p.name
        copy.parent.mkdir(exist_ok=True)
        copy.write_bytes(p.read_bytes())
        frozen.append({'path': rel(p), 'sha256': ingress.sha(p), 'snapshot': rel(copy)})
    plan = {'id': 'S2-G4-CAPITAL-CONEXION2023-v1-20261024', 'author': 'Codex',
        'utc': datetime.now(timezone.utc).isoformat(), 'forum_prior': 'COD-S2-20261024-063',
        'authorization_literal': 'Prepara el contrato de capital por ámbito y conecta las entradas de2023 a G4. Valídalo con datos sintéticos,sin ajustar modelos ni recalcular C0; conserva B00,deja resultados en foro y mantén2024cerrado.',
        'prepared_input_index': {'path': rel(index_path), 'sha256': ingress.sha(index_path)},
        'prepared_input_manifest': source, 'frozen_code': frozen,
        'hypothesis': 'La frontera lector estricto->capital congelado->siete predictores puede aislar ámbitos y preservar T0 sin ajuste; las entradas reales fallan antes de decodificar valores cuando falta capital del ámbito.',
        'scope': 'Real15request wiring and pending templates from existing manifest metadata; integration on generated Parquet fixtures and fixed fictitious parameters only. Not real parameter estimation or model execution.',
        'criteria': ['all15synthetic scope connections preserve keys,targets and excluded values stay unopened',
            'capital math agrees with Decimal/math.log to absolute1e-12 including threshold/missing/rejection cases',
            'invalid parameter/source/scope/hash/target/finite/provenance contracts rejected before values',
            'protected-fold payload changes leave allowed frames and learning signature identical; allowed change invalidates old capital',
            'disk contract roundtrip identical without fit or C0',
            'all15real requests block before values when parameters absent; fixed synthetic parameters do not unlock real data'],
        'budgets': {'model_fits_including_synthetic': 0, 'C0_calls_including_synthetic': 0,
            'inferences': 0, 'scores': 0, 'real_value_decoders': 0, 'real_parameter_estimates': 0},
        'limits': ['Real parameter producer/estimation and positive real receipt flow absent',
            'Input invariance is not invariance of learned objects', 'No synthetic learner marker added to real rows',
            'G1/G2 remain unchanged; G4 real full flow remains open'],
        'B00_preserved': True, '2024_test_closed': True, 'old_diagnostics_or_suites_repeated': False}
    PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (RUN/'plan_snapshot.json').write_bytes(PLAN.read_bytes())
    body = RUN/'forum_063_pre.md'
    body.write_text('''Codex, preinscripción de la conexión solicitada tras foro062. Plan: registro/semana2_g4_conexion_plan_v1.json. Contrato: registro/semana2_g4_capital_contrato_v1.json.

Se implementa una frontera propia de entrada a G4: solicitud ligada al manifiesto preparado2023, lector por folds, capital con parámetros externos congelados del ámbito exacto y siete predictores con objetivos/notificaciones heredados. No se llama al aprendiz sintético ni se añade su marcador a datos reales. Quince solicitudes reales y sus plantillas pendientes se producen solo desde el manifiesto, sin decodificar nuevamente filas reales.

CAPS2-01 exige parámetros finitos/positivos, umbral1e7, intervalo ordenado, firmas del ajuste/pertenencias y fuentes de capital permitidas. Se fija la regla de la futura estimación, sin estimarla aquí. Recibo de productor y autor/UTC requeridos para parámetros reales; constantes ficticias de origen distinto no los sustituyen. La ausencia detiene antes de abrir valores, sin fallback o recálculo.

Prueba nueva solo con Parquet generados y constantes ficticias: quince ámbitos por el flujo lector-capital-predictores, referencia Decimal/math.log con tolerancia absoluta1e-12, casos adversos de contrato, invariancia de entradas ante alteración protegida, control positivo de cambio permitido y lectura de contratos desde disco. Se distinguen la firma de aprendizaje y el recibo archivístico, que sí puede cambiar al cambiar fuentes protegidas. No se afirma invariancia de modelos aprendidos.

Todos los fit, incluso sintéticos, C0 fit/apply, predicción, cargas de estimadores y red estarán bloqueados. Cero ajustes, estimaciones de capital, inferencias o scores. La parte real se prueba solo por su bloqueo temprano sin parámetros; productor de parámetros y objetos C0/preprocesado/GLM/calibrador reales siguen pendientes. Sin repetir diagnósticos o suites anteriores.

B00 y alternativas conservados.2024/test/ledger/actas/SEL01 cerrados en este trabajo. G1/G2 no cambian, G4 integral real no cerrado. Sin envío, publicación, remoto, contactos, otros chats, delegación o automatizaciones. Ventana nocturna cerrada. Autor Codex, verificación propia exploratoria, sin aprobación humana o validación profesional independiente.
''', encoding='utf-8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor', 'Codex', '--id', plan['forum_prior'], '--asunto', 'G4: contrato de capital por ámbito y conexión sin aprendizaje, prueba sintética preinscrita',
        '--cuerpo', str(body)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    (RUN/'forum_prior_receipt.json').write_text(p.stdout, encoding='utf-8')
    print(json.dumps({'plan': rel(PLAN), 'forum_prior': plan['forum_prior'], 'frozen_files': len(frozen),
                      'real_row_values_decoded': 0, 'fits': 0}, ensure_ascii=True))


if __name__ == '__main__':
    main()
