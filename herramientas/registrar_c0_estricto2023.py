"""Registra una prueba sintética terminada; no carga datos o modelos del concurso."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
RUN = REPO / 'privado/semana2/desarrollo2023/c0_adapter_sintetico_20261024_v1'
INDEX = REPO / 'registro/semana2_b20_c0_adaptador_sintetico_actual.json'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def prepend_json(path, key, value):
    previous = path.read_text(encoding='utf-8-sig')
    assert key not in json.loads(previous), 'Registro ya existente: ' + key
    entry = json.dumps({key: value}, ensure_ascii=False, indent=2)[1:-1].strip('\n')
    result = '{\n' + entry + ',\n' + previous[previous.index('{') + 1:].lstrip('\r\n')
    json.loads(result)
    assert path.read_text(encoding='utf-8-sig') == previous, 'Cambio concurrente; reintentar registro.'
    path.write_text(result, encoding='utf-8')


def main():
    assert not INDEX.exists(), 'Ya registrado; no duplicar memoria o foro.'
    plan = read(RUN / 'plan.json')
    verified = read(RUN / 'verification.json')
    assert verified['success'] and verified['ordered_poison_cases'] == 20
    assert verified['competition_rows_read'] == verified['competition_C0_fits'] == 0
    for item in plan['frozen_sources']:
        assert sha(ROOT / item['path']) == item['sha256'], 'Cambió una fuente congelada.'
        assert sha(ROOT / item['snapshot']) == item['sha256']
    sources = []
    for name in ['src/semana2/c0_estricto2023.py', 'herramientas/probar_c0_estricto2023.py',
                 'herramientas/registrar_c0_estricto2023.py', 'docs/semana2/ADAPTADOR_C0_ESTRICTO_2023.md']:
        path = REPO / name
        snapshot = RUN / ('final_' + path.name)
        snapshot.write_bytes(path.read_bytes())
        sources.append({'path': rel(path), 'sha256': sha(path), 'snapshot': rel(snapshot)})
    utc = datetime.now(timezone.utc).isoformat()
    record = {'id': plan['id'], 'author': 'Codex', 'utc': utc, 'path_base': 'workspace_root',
        'authorization_literal': plan['authorization_literal'],
        'status': 'C0_numeric_stage_synthetic_verified_only_support_failed_no_competition_execution',
        'run': rel(RUN), 'documentation': rel(REPO / 'docs/semana2/ADAPTADOR_C0_ESTRICTO_2023.md'),
        'plan': rel(REPO / 'registro/semana2_b20_c0_adaptador_sintetico_plan_v1.json'),
        'verification': {'path': rel(RUN / 'verification.json'), 'sha256': sha(RUN / 'verification.json')},
        'tests': verified['tests'], 'ordered_poison_cases': verified['ordered_poison_cases'],
        'synthetic_C0_fit_calls': verified['synthetic_C0_fit_calls'],
        'competition_rows_read': 0, 'competition_C0_fits': 0, 'new_pricing_fits': 0,
        'new_predictions': 0, 'new_scores': 0, 'new_bootstrap': 0,
        'source_and_snapshot_hashes': sources, 'historical_sources_unchanged': True,
        'support_gate': 'FAILED unchanged', 'G1_closed': False, 'G2_closed': False,
        'G4_C0_software_stage': 'implemented_and_synthetic_verified', 'G4_full_flow_closed': False,
        '2024_test_read': False, 'selection_or_reference_changed': False,
        'remote_training': False, 'submission': False, 'automation_changed': False, 'delegation': False,
        'first_attempt': {'receipt': rel(RUN / 'attempt1_verification.json'), 'errors': 3,
            'reason': 'Adverse fixture assignment rejected by pandas3 before adapter; failures preserved.'},
        'future_C0_budget': {'unique_internal_scopes': 10, 'reporting_fits': 60,
            'frequency_constants': 60, 'cost_means_from_reporting': 60, 'mixtures': 10,
            'executed_on_competition_data': False},
        'limits': 'Own C0-stage software verification with synthetic data; no GLM/calibrator whole-flow or professional independence claim.'}
    write(INDEX, record)
    prepend_json(ROOT / 'Preparación/ESTADO_PROYECTO.json', 'semana2_b20_c0_adaptador_sintetico_20261024',
        {k: record[k] for k in ['id', 'utc', 'author', 'path_base', 'status', 'documentation', 'tests',
             'ordered_poison_cases', 'competition_rows_read', 'competition_C0_fits', 'new_pricing_fits',
             'support_gate', 'G4_full_flow_closed', '2024_test_read']})
    routes_path = ROOT / 'RUTAS_PROYECTO.json'
    prepend_json(routes_path, 'week_2_b20_C0_adapter_index', rel(INDEX))
    prepend_json(routes_path, 'week_2_b20_C0_adapter_report', record['documentation'])
    note = f'''\n\n## S2-B20-C0-ADAPTADOR-SINTETICO, continuación técnica sin entrenar el contraste

Codex, UTC {utc}. Instrucción directa «continua con esto». Plan previo y foro COD-S2-20261024-B20-C0-ADAPTADOR-PRE. Se implementó src/semana2/c0_estricto2023.py: API sin lectores, emerging2023, claves compuestas, aislamiento exterior/interior de curvas/marcas/pesos/frecuencias/mezcla y caché, rho1 y valoración histórica fijos. Rechaza datos2024/test, pertenencias ajenas y objetos de otro ámbito. No tiene ejecutor de datos reales o autorización de soporte incorporada.

13 pruebas propias pasaron y20/20pares ordenados fueron invariantes a etiquetas/fechas/perils/exposición de ambos folds protegidos, con control positivo de entrenamiento que cambia el objeto y compatibilidad con la receta base histórica en fixtures.79invocaciones sintéticas, incluidas las rechazadas; cero filas, C0, precios, modelos o scores del concurso. Primer intento conservado:3errores al insertar datos adversos en columnas enteras de pandas3, corregidos sin relajar el contrato. Fuentes históricas fijadas por SHA permanecen iguales.

Índice {rel(INDEX)}; informe {record['documentation']}; recibos {rel(RUN)}. G4tiene la etapa C0 numérica implementada y comprobada en sintético; preprocesado/GLM/calibrador y ejecución interna real siguen pendientes. G1/G2y soporteFAILED sin cambios: el código no resuelve concentración o mecanismo ni habilita el contraste B20. B00/alternativas, T0/C0/folds/catálogo y contadores preservados. Sin2024/test/SEL01/actas/ledger, remoto, envíos, automatizaciones o delegación. Exposición previa en otros contextos a narrativas2024 y al público del envío declarada, sin usarla en el código o elegir modelos; no se afirma ceguera completa. Revisión propia de Codex, no profesional independiente.
'''
    for path in [ROOT / 'Preparación/MEMORIA_PROYECTO.md', ROOT / 'Preparación/DECISIONES.md']:
        with path.open('a', encoding='utf-8') as handle:
            handle.write(note)
    (RUN / 'aporte_resultado.md').write_text(note, encoding='utf-8')
    print(json.dumps({k: record[k] for k in ['status', 'tests', 'ordered_poison_cases',
                     'competition_rows_read', 'new_pricing_fits', 'support_gate']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
