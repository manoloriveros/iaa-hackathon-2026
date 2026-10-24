"""Registra hipótesis, selección y fuentes antes de descomponer B20."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT/'Hackaton/Repositorio_IAA2026'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
dump = lambda p, x: p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    pp = REPO/'registro/semana2_b20_atribucion_plan_v1.json'
    assert not pp.exists(), 'Plan existente: conciliar, no repetir'
    nightpath = REPO/'registro/semana2_continuidad_nocturna.json'
    nightbytes = nightpath.read_bytes()
    night = read(nightpath)
    assert night['current_unit'] is None, 'Otra unidad en curso: conciliar antes de duplicar'
    ridge = REPO/'privado/semana2/desarrollo2023/ridge20_20261024_v1'
    parent = ROOT/read(ridge/'plan_snapshot.json')['input_run']
    trace = ROOT/read(REPO/'registro/semana2_b19_traza_actual.json')['run']
    producer = REPO/'src/semana2/atribuir_b20_grupos2023.py'
    sources = [producer, ridge/'oof_2023.parquet', ridge/'report.json', ridge/'verification.json',
               ridge/'fixture_checks.json', ridge/'diagnostics/new_pairs.json', ridge/'plan_snapshot.json',
               trace/'selection_reasons.parquet', trace/'report.json', trace/'verification.json',
               REPO/'registro/semana2_contadores_propios_actual.json']
    sources += sorted((ridge/'models').glob('*/bundle.joblib'))
    sources += sorted((parent/'models').glob('*/bundle.joblib'))
    sources += sorted((parent/'inputs_2023').glob('*.parquet'))
    plan = {
        'id': 'S2-B20-ATRIBUCION2023-v1-20261024', 'author': 'Codex', 'registered_utc': datetime.now(timezone.utc).isoformat(),
        'authorization_literal': 'Continúa con la atribución por grupos y segmentos de B20 y explica por qué se invierte la ventaja. Registra las decisiones y resultados, mantén 2024 y test cerrados y añade complejidad solo si la evidencia lo exige.',
        'hypothesis': 'The favorable31components account for more than the net pooled loss improvement, so the rest of the portfolio has negative signed gain. Test concentration and loss-term/segment attribution; a positive null denominator cannot alone reverse sign. No data error or need for complex models is presumed.',
        'ridge_run': rel(ridge), 'frame_source': rel(parent), 'fixed_B19_selection': rel(trace/'selection_reasons.parquet'),
        'output_run': 'Hackaton/Repositorio_IAA2026/privado/semana2/desarrollo2023/b20_atribucion_20261024_v1',
        'producer': rel(producer), 'producer_sha256': sha(producer),
        'references': ['W2-B19', 'W2-B14', 'W2-B00'],
        'sign_convention': 'gain_i=deviance_reference-deviance_B20, positivefavorsB20. g=4*y*(1/sqrt(mu_ref)-1/sqrt(mu20))+4*(sqrt(mu_ref)-sqrt(mu20)).',
        'selection': 'For eachpair order all30869components bydescending signedgain, thenascending nativegroupID for ties, exactly31completecomponents. Retainedevaluation only, no refit/deletion. Removal pathfixed0,1,5,10,31; report smallestadverseprefix diagnostically, never choose a model/threshold withit.',
        'diagnostics': ['Full/selected31/remaining signed andgross gain, costs,positiverows,prediction sums and own/nullfull contributions',
                        'Exclusive partitions:line,business,linebusiness,fold,linecoverage,zero/positiveT0; keep adverse cells',
                        'Fixedfull-null versus recalculated-null sign;31group overlaps and3x3fixed selection removal, no bootstrap',
                        'Keep priorB19-selected12components fixed and report descriptive differences; selection enrichedbypriorerrors, not freshvalidation',
                        'Exact B20-vsB19 lograte change into intercept,business,coverage,otherfiveeffects with the fixed learned design. Sum must match savedlograte ratio; block attribution depends on coding/centering, not causal loss attribution'],
        'acceptance': 'Only2023,50094unique samekeys/T0/C0/group/fold perpair; original3point/removal differencesreproduced; row-loss identity,groupandsegment conservation; own31anddenominator checks by independent squaredeviance/Pythonmathfsum;logidentity<=2e-12;expected invalidyear,target,key/sourceguards. Source/counter/modelsha unchanged,fitblocked.',
        'resources': 'Local2threads;0fits,0newpricepredictions,0candidate recipes,0bootstrap,0remote/submissions/delegation. Derived diagnostic subsetmetrics use existingOOF, not a new confirmationscore.',
        'decision_rule': 'KeepB00andB01-B20. No promotion,retirement,rankingbased routing,alpha tuning,claim removal ormorecomplexity from this diagnostic. Interpret concentration as evaluationfragility; do not label expensivevalidclaims dataerrors.',
        'scope': '2023 only;2024/test/actas/scores/SEL01/ledgerclosed. Prior external2024subject exposure disclosed,notused; no completeblindness claim.',
        'frozen_sources': [{'path': rel(p), 'sha256': sha(p)} for p in sources],
        'forum_prior': 'COD-S2-20261024-B20-ATTR-PRE', 'forum_result': 'COD-S2-20261024-B20-ATTR-RESULT',
        'IAA': 'Purpose/limits ProfessionalConsiderations3.1; own versusindependentreview Governance2.8; model/decision Documentation3. No professionalcertification.'
    }
    dump(pp, plan)
    body = 'Respuesta a COD-S2-20261024-B20-RESULT y encargo humano de atribuir la inversión. Plan S2-B20-ATRIBUCION2023-v1-20261024 antes del cálculo: repositorio común, solo OOF2023 de B20/B19/B14/B00, mismos T0/C0 y grupos. Hipótesis: los31componentes más favorables aportan más que la ventaja neta; comprobar si el resto pierde y qué ramos/negocios/coberturas y filas con/sin coste lo explican. La nula positiva cambia magnitud, no signo. No se presume error de datos o necesidad de complejizar.\n\nGanancia por fila=desviancia referencia−B20; separar exactamente término dependiente de T0 y término de predicción. Orden de grupos por ganancia descendente y group_id ascendente; retirar exactamente31componentes completos solo de evaluación. Ruta fija0/1/5/10/31 y primer prefijo adverso solo descriptivo. Conservar ganancias/pérdidas brutas, seleccionados/resto, particiones exclusivas y signos con nula fija/recalculada. Cotejar solapamientos y la misma selección en otros pares, y los12grupos B19 ya fijados. No declarar nueva validación tras retirar grupos elegidos por su propio error.\n\nDescomponer logtasaB20−B19 en intercepto, negocio, cobertura y demás efectos con matrices/modelos guardados; identidad exacta, sin precio nuevo o ajuste. La contribución de bloques depende de codificación/centrado y no asigna causalmente ganancia de desviancia. Verificación separada con desviancia cuadrática y math.fsum, suma por grupos/segmentos, ranking/empates y guardas adversas, fit bloqueado y fuentes/counter con SHA. Cero entrenamiento, modelos nuevos, bootstrap o cambios de objetivos.\n\nNo promoción, retiro, elección de alpha, mezcla por segmento, borrado de siniestros o complejidad nueva. B00 y B01–B20 conservados,2024/test/ledger cerrados, exposición previa de título declarada sin usar cifras. Fuentes/criterios en registro/semana2_b20_atribucion_plan_v1.json; productor src/semana2/atribuir_b20_grupos2023.py. Registro de unidad actual conciliado con continuidad, sin otra automatización/remoto/delegación/mensajes externos. Revisión propia, no validación profesional independiente.\n'
    (REPO/'registro/COD-S2-20261024-B20-ATTR-PRE_cuerpo.md').write_text(body, encoding='utf-8')
    assert nightpath.read_bytes() == nightbytes, 'Continuidad cambió durante preinscripción'
    night['current_unit'] = {'id': plan['id'], 'plan': rel(pp), 'status': 'preregistered_before_attribution', 'forum_prior': plan['forum_prior']}
    night['updated_utc'] = plan['registered_utc']
    dump(nightpath, night)
    print(json.dumps({'plan': rel(pp), 'sources': len(sources), 'new_fits': 0, 'plan_sha256': sha(pp)}))


if __name__ == '__main__':
    main()
