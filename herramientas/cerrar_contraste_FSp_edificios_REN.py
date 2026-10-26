"""Conserva el resultado adverso del contraste y prepara el siguiente paso útil."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'
OUT = BASE / 'FSp_edificios_REN_contraste_20261026_v1'
P = R / 'registro/semana2_mision017_fase2_actual.json'
INDEX = R / 'registro/semana2_mision017_renovaciones_FSp_actual.json'
spec = importlib.util.spec_from_file_location('writer_close_building_renewal', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)


def main():
    assert not (OUT / 'completion_receipt.json').exists()
    stamp = datetime.now(timezone.utc); report = w.read(OUT / 'report.json')
    assert not report['all_checks_passed'] and len(report['replays']) == 5
    assert report['all_new_business_unchanged'] and report['other_lines_unchanged']
    archive = OUT / 'state_cuts' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    # This is a narrow first inventory of numerical f/s outputs, distinct from the
    # earlier completed search for K CSVs. Preserve where the absence was checked.
    source = ROOT / 'Hackaton/Semana 2/Claude/mision017_20261025'
    directories = [source / 'exp26_20261026/ml2/trabajo/pred/fsp', source / 'exp26_20261026_v2/ml2/trabajo/pred/fsp']
    inventory = []
    for folder in directories:
        selected = sorted(p for p in folder.iterdir() if p.is_file() and p.name.startswith(('motor', 'contents'))) if folder.exists() else []
        inventory.append({'directory': w.rel(folder), 'exists': folder.exists(),
                          'files': [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': w.sha(p)} for p in selected]})
    assert not any(x['name'].endswith('.parquet') for inv in inventory for x in inv['files'])
    inventory_receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'inventory': inventory,
                         'no_numerical_motor_contents_outputs_in_these_directories': True,
                         'not_claimed_absent_globally': True, 'no_fit_or_score': True}
    (OUT / 'motor_contents_fsp_output_inventory.json').write_text(json.dumps(inventory_receipt, ensure_ascii=False, indent=2), encoding='utf8')
    next_unit = ('FSp de edificios ya está reconstruido y su inserción REN .25 no pasó: no repetir esos24fits,30constantes o bootstrap. '
        'Mantener la alternativa y B00/F2/C1/F3c. La composición F3c/F4c REN motor/contenidos sigue provisional y no es FSp puro. '
        'Primero buscar de forma acotada salidas numéricas motor/contents f/s en otras rutas recibidas pertinentes, sin repetir las dos carpetas ya inventariadas '
        'ni el inventario K. Si no existen, preparar entradas de precisión completa de esos dos ramos y conciliar metadatos ya presentes usando '
        'los recuentos y C0 existentes; no reconstruir los edificios otra vez. Registrar la necesidad, rondas fijas, coste y foro antes de cualquier '
        'recuperación fuente adicional. El propósito es aislar FSp de los factores y contrastar en los mismos grupos antes de considerar un envío. '
        'No relajar criterios ni retocar pesos por el resultado adverso de edificios o el score público.2024abierto como desarrollo; cuota0; meta0.17activa.')
    note = '\n\n## Edificios en renovación: contraste adverso conservado, 26 de octubre de 2026 (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. '
    note += ('Se completó el único contraste registrado del componente recuperado: peso fijo del 25 % en edificios en renovación, '
        'sin cambiar nuevo negocio, los otros ramos o los totales de precio por año. El denominador conserva los multiplicadores de prior claims de N3; '
        'los componentes se anualizaron por la exposición original del productor y se aplicó una sola vez la exposición canónica. '
        'Se reutilizaron los cinco ámbitos globales y sus C0. Las treinta constantes por peligro se estimaron exclusivamente en entrenamiento.\n\n')
    note += '| Medida | Resultado |\n|---|---:|\n'
    note += f'| D² N3 | {report["scores"]["N3"]:.8f} |\n| D² alternativa ER1 | {report["scores"]["ER1"]:.8f} |\n'
    note += f'| Diferencia global | {report["delta"]:+.8f} |\n| IC 95 % por grupos, condicionado a fuente fija | [{report["bootstrap95"][0]:+.8f}; {report["bootstrap95"][1]:+.8f}] |\n'
    note += f'| Aporte global de 2023 | {report["year_global_contributions"]["2023"]:+.8f} |\n| Aporte global de 2024 | {report["year_global_contributions"]["2024"]:+.8f} |\n'
    note += f'| Tras retirar 31 grupos favorables, mismo denominador global | {report["post31_favorable_groups_global_delta"]:+.8f} |\n'
    note += f'| Sin los 31 grupos de mayor coste observado | {report["remove31highest_actual_cost_groups_global_delta"]:+.8f} |\n'
    note += ('\nTres de cinco folds empeoran. El intervalo incluye pérdidas; 2024 pierde y el contraste por renovación de edificios de ese año '
        'también incumple el umbral por celda registrado. La ganancia media no es robusta y queda por debajo del mínimo global de +0,002. '
        'Se conservan la alternativa, los modelos y todas las salidas; no se incorpora este cambio ni se genera otro CSV de envío por este resultado. '
        'Las previsiones positivas recibidas para K no se trasladan: esta reconstrucción, la fórmula y el ámbito son distintos.\n\n'
        'El comparador es N3, no el F3c completo. No está disponible aquí el contraste íntegro F3c/F2 ni los vetos de sensibilidad2025/A1, '
        'por lo que también faltan esos requisitos. No se confunde un fallo del contraste actual con una prueba de que cualquier FSp futuro de edificios deba retirarse. '
        'El bootstrap condiciona a los modelos fuente guardados y no incluye su incertidumbre. La valoración a diciembre de 2024, '
        'los maestros sin fecha y el desarrollo adaptativo limitan la interpretación prospectiva.\n\n'
        'Pasaron los controles numéricos y de fuga del flujo nuevo: etiquetas retenidas totales y por peligro alteradas sin efecto '
        'en el aprendizaje o las predicciones, exclusión de grupos, integración independiente de C0, reproducción con parámetros guardados '
        'sin estimar, exponenciales/normalización por otra fórmula y pérdida Tweedie contrastada con scikit-learn. '
        'Los controles mecánicos no corrigen el deterioro predictivo. Coste de este contraste: 30 constantes de precio por peligro, '
        '10 normalizadores de predicciones, cero árboles, C0, precios de test o envíos; las 30 recomputaciones idénticas del control adverso se cuentan aparte. '
        'Los 24 ajustes fuente de la recuperación anterior ya estaban contabilizados y no se suman de nuevo.\n\n'
        'La comprobación acotada de las dos carpetas FSp recibidas encontró solo los cuatro metadatos de motor/contenidos, '
        'sin sus Parquet numéricos. Se guarda el inventario exacto y no se afirma ausencia global. El siguiente paso es resolver ese faltante '
        'para separar el componente FSp de los factores del donante compuesto, antes de otra comparación o envío. '
        'B00, F2/C1/F3c y las versiones fallidas se mantienen; 2024 está abierto por autorización humana. '
        'El mejor recibo continúa en 0,16914 y faltan 0,00086 para 0,17. La cuota 0 impide otro envío por ahora, pero el trabajo local sigue.\n\n'
        'Evidencia: ' + w.rel(OUT / 'report.json') + '.\n\nSiguiente unidad: ' + next_unit + '\n')
    doc = R / 'docs/semana2/MISION017_FSp_EDIFICIOS_REN_CONTRASTE.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    body = OUT / 'forum_resultado.md'; body.write_text(note, encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-MISION017-FSP-EDIFICIOS-REN-CONTRASTE-RESULTADO',
        '--asunto', 'Edificios REN: la mejora media no resiste folds, año e influencia', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': stamp.isoformat(), 'status': 'completed_exploratory_adverse_no_integration',
               'report': w.rel(OUT / 'report.json'), 'report_sha256': w.sha(OUT / 'report.json'), 'document': w.rel(doc),
               'delta': report['delta'], 'bootstrap95': report['bootstrap95'], 'checks': report['checks'],
               'new_price_calibration_constants': 30, 'new_iterative_price_fits': 0, 'new_C0_fits': 0,
               'new_test_prices': 0, 'new_submissions': 0, '2024_open': True, 'B00_all_alternatives_preserved': True,
               'goal_achieved': False, 'next_unit': next_unit, 'forum': json.loads(response.stdout)}
    counters = R / 'registro/semana2_contadores_propios_actual.json'; c = w.read(counters)
    assert 'phase2_FSp_buildings_renewal_contrast' not in c
    w.update(counters, {'as_of_utc': stamp.isoformat(), 'cumulative_closed_form_constants': c['cumulative_closed_form_constants'] + 30,
                        'phase2_FSp_buildings_renewal_contrast': receipt}, archive)
    phase = w.read(P)
    w.update(P, {'utc': stamp.isoformat(), 'status': 'active', 'FSp_buildings_renewal_contrast': receipt,
                 'new_peril_price_calibration_constants': phase.get('new_peril_price_calibration_constants', 0) + 30,
                 'active_execution': None, 'next_unit': next_unit, '2024_open': True, '2024_closed': False}, archive)
    ownpath = ROOT / 'Preparación/ESTADO_PROYECTO.json'; own = w.read(ownpath)['week_2_mission017_phase2_20261025']
    own.update(FSp_buildings_renewal_contrast=receipt, next_unit=next_unit, active_jobs=[])
    w.update(ownpath, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': None}, archive)
    w.update(INDEX, {'utc': stamp.isoformat(), 'status': 'buildings_numerical_complete_REN_comparison_adverse',
                     'buildings_REN_contrast': receipt, 'next_unit': next_unit}, archive)
    for filename in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        w.append(ROOT / 'Preparación' / filename, note, archive)
    w.append(R / 'docs/semana2/MISION017_RENOVACIONES_Y_RECUPERACION_FSp.md', note, archive)
    w.update(ROOT / 'RUTAS_PROYECTO.json', {'week_2_mission017_FSp_buildings_REN_report': w.rel(doc)}, archive)
    (OUT / 'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'new_price_constants': 30, 'new_submissions': 0,
                      'goal_achieved': False, 'forum': receipt['forum']}, ensure_ascii=True))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); main()
