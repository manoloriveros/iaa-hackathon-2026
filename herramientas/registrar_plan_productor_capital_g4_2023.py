"""Preinscribe productor/recibos y controles nuevos antes de probarlos."""
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
RUN = REPO/'privado/semana2/productor_capital_g4_2023/productor_20261024_v1'
PLAN = REPO/'registro/semana2_g4_productor_capital_plan_v1.json'
rel = lambda p: p.relative_to(ROOT).as_posix()


def main():
    assert not PLAN.exists()
    RUN.mkdir(parents=True, exist_ok=False)
    index_path = REPO/'registro/semana2_g4_entradas2023_actual.json'
    index = json.loads(index_path.read_text(encoding='utf-8'))
    source = index['input_manifest']
    assert ingress.sha(ROOT/source['path']) == source['sha256']
    frozen = []
    for relative in ['src/semana2/productor_capital_g4_2023.py', 'src/semana2/conexion_g4_2023.py',
        'src/semana2/entradas_g4_2023.py', 'src/semana2/ambitos_c0_b20_2023.py',
        'herramientas/probar_productor_capital_g4_2023.py', 'herramientas/probar_conexion_g4_2023.py',
        'herramientas/validar_productor_capital_g4_2023.py', 'registro/semana2_g4_capital_contrato_v2.json']:
        path = REPO/relative
        copy = RUN/'preregistered_sources'/path.name
        copy.parent.mkdir(exist_ok=True)
        copy.write_bytes(path.read_bytes())
        frozen.append({'path': rel(path), 'sha256': ingress.sha(path), 'snapshot': rel(copy)})
    plan = {'id': 'S2-G4-PRODUCTOR-CAPITAL2023-v1-20261024', 'author': 'Codex',
        'utc': datetime.now(timezone.utc).isoformat(), 'forum_prior': 'COD-S2-20261024-065',
        'authorization_literal': 'Implementa el productor de parámetros de capital por ámbito y valida su integración con datos sintéticos.Sin ajustar modelos ni recalcular C0; conserva B00,deja resultados en foro y mantén2024cerrado.',
        'prepared_input_manifest': source, 'frozen_code': frozen,
        'hypothesis': 'El productor puede derivar min/max de prima por mil solo de capitales normales del ámbito permitido y producir evidencia que la conexión reproduce contra esos capitales, sin fuga ni modelos.',
        'recipe': 'CAPS2-01 numerical rule unchanged; new v2 provenance/population replay and input interface, old v1 source and receipts preserved.',
        'criteria': ['15synthetic scopes end-to-end with excluded value files forbidden and producer reads metadata/capital only',
            'normal min/max and corrected log capital agree with Decimal/math.log at absolute1e-12',
            '15protected changes preserve numerical parameter payload,normal population content,allowed frames and learning signatures; archival seals may differ',
            'allowed premium change changes learned capital bound and invalidates earlier artifact',
            'coherently resealed omission from normal population passes structural checks but fails replay against actual allowed capital',
            'invalid/empty normal population fails without fallback; artifact/receipt/scope/origin adversaries rejected',
            'saved producer artifact/receipt/population replay identical with all model/C0/inference functions blocked'],
        'budgets': {'valid_synthetic_parameter_artifacts': 31, 'model_fits_including_synthetic': 0,
            'C0_calls_including_synthetic': 0, 'inferences': 0, 'scores': 0,
            'real_row_value_decoders': 0, 'real_parameter_artifacts': 0},
        'scope_limits': ['Only generated Parquet; real15requests remain missing parameters and must fail before values',
            'No independent professional validation,whole-model invariance,real learned objects or resolution of G1/G2'],
        'B00_preserved': True, '2024_test_closed': True, 'old_suites_or_diagnostics_repeated': False}
    PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (RUN/'plan_snapshot.json').write_bytes(PLAN.read_bytes())
    body = RUN/'forum_065_pre.md'
    body.write_text('''Codex, preinscripción del productor de capital solicitado tras foro064. Plan: registro/semana2_g4_productor_capital_plan_v1.json. Contrato v2: registro/semana2_g4_capital_contrato_v2.json. Se conservan v1, sus fuentes y sus recibos; no se cambia la regla numérica CAPS2-01.

El productor leerá solo pertenencias y capital/prima de los folds permitidos, sin objetivos, siniestros, exposición o predictores. Referencias min/max de prima por mil sobre capitales normales positivos y finitos hasta1e7; población no vacía y ratios positivos finitos para todos sus integrantes. Sin fallback ni ajuste de bandas. Se guardan población, firmas de claves/contenido, fuentes, autor/UTC y recibo ligado al artefacto. Seleccionar población de referencias no elimina periodos del modelo.

La conexión v2 comprobará hashes/ámbito/origen antes de leer valores y reproducirá la población/aritmética del recibo contra el capital permitido. Un recibo autoconsistente no bastará para omitir capitales normales. La firma numérica excluye ruta de recibo/UTC/autor y el hash archivístico global; estos pueden cambiar sin alterar las entradas permitidas. No se afirma invariancia de modelos aprendidos.

Ensayo nuevo exclusivamente con Parquet generados:15ámbitos completos,15alteraciones protegidas,referencia Decimal/math.log con error absoluto máximo1e-12,control positivo de prima permitida,recibo reseñado coherentemente con omisión normal que debe fallar al replay,normalidad inválida/vacía y adversos de procedencia/ámbito.31artefactos válidos de capital sintéticos previstos. Guardar y releer artefacto/recibo/población por el flujo real de la API. Sin repetir suites o diagnósticos anteriores.

Quince solicitudes reales v2 pueden prepararse desde el manifiesto ya existente, sin leer valores y sin llamar al productor sobre datos del concurso. Fit/predict de modelos y preprocesadores,C0 fit/apply,cargas y red bloqueados: presupuesto cero incluso en sintético. Cero inferencias,scores,capital real o modelos nuevos. B00/alternativas,T0/exposición/C0/folds/catálogo/contadores conservados;2024/test/ledger/actas/SEL01 cerrados en este trabajo.

G4 integral real y G1/G2 permanecen abiertos. Autor Codex,verificación propia exploratoria;sin revisión profesional independiente o aprobación humana. Sin promoción,envío,publicación,remoto,contactos,otros chats,delegación o automatizaciones. Ventana nocturna cerrada.
''', encoding='utf-8')
    process = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', plan['forum_prior'], '--asunto', 'G4: productor de capital por ámbito y replay numérico de población, preinscripción sintética',
        '--cuerpo', str(body)], capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    (RUN/'forum_prior_receipt.json').write_text(process.stdout, encoding='utf-8')
    print(json.dumps({'plan': rel(PLAN), 'forum_prior': plan['forum_prior'], 'frozen_files': len(frozen),
                      'real_value_decoders': 0, 'model_fits': 0}, ensure_ascii=True))


if __name__ == '__main__':
    main()
