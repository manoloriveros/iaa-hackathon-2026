"""Preinscripción única antes de B20; no ajusta ni calcula nuevos scores."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT/'Hackaton/Repositorio_IAA2026'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()


def main():
    path = REPO/'registro/semana2_glm_ridge_coberturas_plan_v1.json'
    if path.exists():
        raise FileExistsError('Receta ya registrada; no reescribir o repetir')
    parent = REPO/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214'
    p = read(parent/'plan_snapshot.json')
    report = read(parent/'report.json')
    verified = read(parent/'verification.json')
    fixtures = read(parent/'fixture_checks.json')
    assert verified['failed'] == fixtures['failed'] == 0
    recipe = copy.deepcopy(p['recipe'])
    recipe['id'] = 'W2-B20'
    recipe['params']['alpha'] = 1.0
    producer = REPO/'src/semana2/entrenar_glm_ridge_coberturas2023.py'
    frozen = [parent/'oof_2023.parquet', parent/'report.json', parent/'verification.json', parent/'fixture_checks.json',
              parent/'plan_snapshot.json', REPO/'src/semana2/entrenar_desarrollo2023_v8.py',
              REPO/'src/semana2/entrenar_desarrollo2023.py', producer]
    frozen += sorted((parent/'inputs_2023').glob('*.parquet'))
    frozen += sorted((parent/'models').glob('*/bundle.joblib'))
    plan = {
        'id': 'S2-GLM-RIDGE-COBERTURAS2023-v1-20261024', 'model_id': 'W2-B20', 'author': 'Codex',
        'registered_utc': datetime.now(timezone.utc).isoformat(),
        'authorization_literal': 'Continúa con el siguiente modelo estándar y la validación local mientras corrigen Kaggle. Registra cada decisión y sus resultados, y añade complejidad solo si la evidencia lo exige.',
        'hypothesis': 'B19 reduces training deviance in all15 cells but worsens pooled OOF againstB14. Test one standard ridge GLM with identical seven main effects to examine coefficient variance and generalization. This pattern motivates but does not establish overfitting as the cause.',
        'previous_evidence': {'summary': report['summary'], 'pairs': report['pairs'],
                              'all15_training_deviance_deltas_negative': all(x['B19_minus_B14_fit_deviance'] < 0 for x in verified['nested_fit_diagnostics'])},
        'change': 'Only alpha0->1 on all standardized numeric and onehot coefficients, intercept unpenalized. Not a coverage-only penalty; no causal attribution to coverage coefficient alone.',
        'alpha_rationale': 'Reuse alpha1 fixed in the initial2023 B01 plan, not selected by scanning B20 scores. No tuning grid, retries, new seeds or alternate strengths.',
        'recipe': recipe, 'input_run': rel(parent),
        'output_run': 'Hackaton/Repositorio_IAA2026/privado/semana2/desarrollo2023/ridge20_20261024_v1',
        'code': rel(producer), 'code_sha256': sha(producer),
        'frozen_sources': [{'path': rel(x), 'sha256': sha(x)} for x in frozen],
        'objective': 'SameT0/e_cost_mix_1.0 response andsqrt(e) weights; half weighted rate deviance plus alpha/2||beta||2, weights normalized by sum. Heldout observed prediction=e*annualrate. Same per-fold C0, correctedcapital and persisted2023 partitions.',
        'scope': '2023 only,50094 rows/30869 groups,5folds. No2024/test fit/prediction/score, ledger access, remote, submission, third-party messaging or delegation.',
        'resources': {'local_threads': 2, 'new_price_fits': 15, 'new_constants': 0, 'new_reporting_fits': 0, 'new_auxiliary_fits': 0},
        'acceptance_before_fit': 'Exact sources/keys and training-only transforms, no convergence warning, n_iter<2000, maxabs penalized KKT gradient<=1e-4, finite positive rates, serialized replay exact, independent objective/gradient and metrics cross-check. Failures retained without refit.',
        'bootstrap': {'replicates': 2000, 'seed': 2026102302, 'new_pairs_only': ['B20/B19', 'B20/B14', 'B20/B00'],
                      'interpretation': 'Unadjusted exploratory95% fixedfit paired component intervals. Adaptive selection and parameter/refit uncertainty are not corrected; no promotion or equivalence.'},
        'decision_rule': 'RetainB00 and all20 prior recipes regardless of point/CI. Publish train/OOF and line/business/coverage harms, coefficient norms, objective, nominal2023 level and own31group influence. No final roster or2024 reopening. Complexity unchanged apart from standard shrinkage.',
        'known_limits': ['2023 adaptively reused; no fresh confirmation', 'Prior external2024 metric exposure in another forum subject disclosed; never used here',
                         'One-hot ridge penalty depends on reference coding; fixed and explicit', 'Ultimate scale, capital economic validity, reporting and reserve assumptions remain conditional'],
        'forum_prior': 'COD-S2-20261024-B20-PRE',
        'IAA': 'ProfessionalConsiderations3.1, Governance2.8/3.4-3.6, Documentation3; own technical verification, not independent professional review.'
    }
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    body = REPO/'registro/COD-S2-20261024-B20-PRE_cuerpo.md'
    body.write_text('Respuesta al resultado B19 de la continuidad y a instrucción directa de continuar modelos estándar. Se reservan W2-B20 y receta S2-GLM-RIDGE-COBERTURAS2023-v1-20261024, antes de cualquier ajuste o score nuevo.\n\nB19: D²0,082469696 frente a B14 0,086710078; el ajuste mejora en las15celdas y el OOFglobal empeora. Es indicio para probar contracción, no prueba causal de sobreajuste. Se conserva B19 y se reutilizan sus15modelos sin reentrenarlos. B20 mantiene exactamente sus siete efectos/ramo, transforms, T0,C0,capital yfolds, cambiando solo alpha0a1 para todos los coeficientes, con intercepto libre. Alpha1 procede de la receta inicialB01, sin nueva búsqueda. No es penalización exclusiva de cobertura.\n\nMercado emergente2023,50.094periodos/30.869grupos,cincofolds;15ajustes GLM CPU2hilos,0constantes/curvas/auxiliares. Configuración y fuentes conSHA en registro/semana2_glm_ridge_coberturas_plan_v1.json; productor src/semana2/entrenar_glm_ridge_coberturas2023.py. Salida exclusiva predeterminada impide repetir por accidente. Validación previa: convergencia ygradiente penalizado<=1e-4, transformsfit-only,replay nativo/manual sinfit, objetivo penalizado frente a B19, D²porotro método, tres parejas nuevas con2000remuestreos y31grupos favorables; segmentos y nivel nominal2023.\n\nCriterio: pasa controles técnicos o conserva fallos; ningún punto/intervalo2023 promueve, retira alternativas o congela lista. Mantener B00ytodas20recetas. Si ridge empeora, se publica sin reajustar alpha. No nuevas variables/interacciones/árboles. 2024/test/ledger cerrados; exposición previa de título2024 declarada, sin uso en decisiones. Sin envíos/remoto/delegación/mensajes externos; incidencia752144 no cambia contrato. Esta receta discurre en el repositorio común y complementa el cierre concurrente de B19, sin sobrescribir sus artefactos.\n', encoding='utf-8')
    print(json.dumps({'plan': rel(path), 'sha256': sha(path), 'model': 'W2-B20', 'frozen_sources': len(frozen), 'new_fits': 0}))


if __name__ == '__main__':
    main()
