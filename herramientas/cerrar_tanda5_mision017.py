"""Conserva el resultado adverso de prima y registra continuidad sin cerrar la misión."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('statewriter', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'tanda5_prima_20261025_v1'
P = R / 'registro/semana2_mision017_fase2_actual.json'

def main():
    assert not (OUT / 'completion_receipt.json').exists()
    v = w.read(OUT / 'validation_v1/report.json')
    assert len(v['replays']) == 15 and len(v['source_mathematics']) == 6
    assert not any(x['exploratory_pass'] for x in v['comparisons'].values())
    stamp = datetime.now(timezone.utc); local = stamp.astimezone(timezone(timedelta(hours=-5)))
    archive = BASE / 'cortes_tanda5' / stamp.strftime('%Y%m%dT%H%M%SZ'); archive.mkdir(parents=True)
    next_unit = (
        'Conciliar los dos componentes de la mezcla que produjo F2 y su disponibilidad local, antes de otra familia. '
        'El replay anterior comprobó T2b, no la mezcla completa A1fixF1b3n/T2b. '
        'Cotejar por SHA y aritmética los CSV ya existentes de 2025 y el linaje de los factores, sin enviar ni ajustar. '
        'Separar el A1 original de 2024 de la versión corregida de tres semillas: no llamar al primero replay del segundo. '
        'El inventario acotado no ha encontrado los pesos ni las relatividades históricas de A1 corregido en las carpetas de intercambio; '
        'comprobar la disponibilidad real y registrar cualquier parte no reproducible. '
        'No repetir marketing, prima, CatBoost, replays o remuestreos cerrados con fuentes iguales. '
        '2024 permanece abierto como desarrollo. B00, F2 y alternativas se conservan; la misión 0,17 sigue activa y los cupos se reservan para evidencia suficiente.')
    note = f'\n\n## Prima anual como información residual, {local.date().isoformat()} (Bogotá)\n\n'
    note += f'Codex, {stamp.isoformat()}. La tanda 5 terminó y se conservan todos sus artefactos. '
    note += ('La comprobación de pares de tramos por póliza/año aporta evidencia empírica de que written_premium se comporta como prima anual en ambos mercados: '
        'la mediana de cambio logP/logE queda próxima a cero, seleccionando los pares por duración y sin leer siniestros. '
        'No demuestra una fórmula tarifaria exacta ni controla todos los cambios de cobertura. Esta receta no divide la prima por exposición.\n\n'
        'Se ajustaron seis GLM Tweedie sencillos en el mercado desarrollado 2021–2024: un efecto residual de prima y otro conjunto de prima/marketing por ramo. '
        'El objetivo sigue siendo el coste neto de siniestros y el offset es el riesgo del padre T2b. Región, canal y año actúan como controles en la fuente. '
        'Los efectos se trasladan sobre N3 con fuerzas fijadas y se conservan los totales por ramo/negocio mediante covariables y predicciones, sin etiquetas retenidas.\n\n')
    note += '| Variante | D² local | Diferencia frente a N3 | IC 95 % por componentes | Diferencia tras retirar 31 grupos favorables |\n|---|---:|---:|---|---:|\n'
    for name in ['S1', 'S2', 'S3']:
        z = v['comparisons'][name]; lo, hi = z['bootstrap95']
        note += f'| {name} | {v["scores"][name]:.6f} | {z["delta"]:+.6f} | [{lo:+.6f}; {hi:+.6f}] | {z["after_remove31_delta"]:+.6f} |\n'
    note += (f'\nN3 = {v["scores"]["N3"]:.6f} es una referencia de investigación, no la reproducción íntegra de F2 ni un candidato promovido. '
        'La prima sola empeora; añadir marketing produce una mejora pequeña, compatible con cero y dependiente de pocos grupos. Ninguna variante cumple los criterios registrados. '
        'Se conserva el resultado adverso y no se envía ninguna de ellas.\n\n'
        'La codificación dispersa y las medianas de prima se reconstruyeron por otro método. Los seis objetivos y sus derivadas se cotejaron con scikit-learn y diferencias finitas, sin ajustar. '
        'Los 15 ámbitos se reprodujeron exactamente con el optimizador bloqueado. Cambiar las etiquetas, la exposición o la unidad monetaria no altera la transformación más allá de precisión numérica; '
        'se conserva el total de cada celda. No se repitieron los ajustes de C0.\n\n'
        'Coste real: seis estimadores de precio fuente, cero curvas C0 nuevas, cero niveles aprendidos de nuevas etiquetas emergentes y 90 normalizadores de cartera sin etiquetas. '
        'Estos normalizadores y las medianas dependen de la cartera conocida; no acreditan un flujo prospectivo en línea. '
        '2024 se usa como desarrollo adaptativo autorizado. La incertidumbre de reservas, cola y fecha de los maestros permanece abierta; los intervalos condicionan en la fuente fijada. '
        'La revisión es exploratoria, realizada por Codex, y no constituye revisión profesional independiente.\n\n'
        'B00 y F2 se conservan. Cero envíos nuevos. La última marca pública conciliada del equipo sigue siendo 0,16033; no se ha alcanzado 0,17.\n\n'
        'Evidencia: ' + w.rel(OUT / 'validation_v1/report.json') + '.\n\nSiguiente unidad: ' + next_unit + '\n')
    doc = R / 'docs/archivo/semana2/MISION017_FASE2_TANDA5_RESULTADOS.md'; assert not doc.exists()
    doc.write_text(note, encoding='utf8'); body = OUT / 'forum_resultado.md'; body.write_text(note, encoding='utf8')
    receipt = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-FASE2-TANDA5-RESULTADO', '--asunto',
        'Prima residual: controles numéricos superados, mejora predictiva insuficiente; sin envío', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    summary = {'batch': 5, 'output': w.rel(OUT), 'status': 'completed_exploratory_no_admission',
        'price_report': w.rel(OUT / 'price_report.json'), 'price_report_sha256': w.sha(OUT / 'price_report.json'),
        'validation': w.rel(OUT / 'validation_v1/report.json'), 'validation_sha256': w.sha(OUT / 'validation_v1/report.json'),
        'reference': 'N3', 'scores': v['scores'], 'exploratory_pass': [], 'new_price_estimator_fits': 6,
        'new_source_reporting_reconstructions': 0, 'new_emerging_C0_fits': 0, 'new_covariate_only_normalizers': 90,
        'submissions': 0, 'forum': json.loads(receipt.stdout)}
    (OUT / 'closure_manifest.json').write_text(json.dumps({'utc': stamp.isoformat(), 'files': {
        p.relative_to(OUT).as_posix(): w.sha(p) for p in OUT.rglob('*') if p.is_file()}}, indent=2), encoding='utf8')
    (OUT / 'completion_receipt.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf8')
    counters = R / 'registro/semana2_contadores_propios_actual.json'; counter = w.read(counters)
    assert 'phase2_2024_tanda5' not in counter
    w.update(counters, {'as_of_utc': stamp.isoformat(), 'cumulative_price_base_fits': counter['cumulative_price_base_fits'] + 6,
        'phase2_2024_tanda5': {'source_GLM_fits': 6, 'new_C0_fits': 0, 'new_target_label_fitted_levels': 0,
            'covariate_only_portfolio_normalizers': 90, 'synthetic_fits_separate': 2,
            'source_year_initialization_values_not_independent_models': 24, 'receipt': summary}}, archive)
    phase = w.read(P)
    w.update(P, {'utc': stamp.isoformat(), 'status': 'active', 'previous_batch': phase['current_batch'], 'current_batch': summary,
        'completed_batches': phase['completed_batches'] + [summary], 'new_price_fits': phase['new_price_fits'] + 6,
        'new_covariate_only_portfolio_normalizers': phase['new_covariate_only_portfolio_normalizers'] + 90,
        'active_execution': None, 'active_jobs': [], 'next_unit': next_unit,
        'premium_unit_report': w.rel(BASE / 'unidad_prima_vigente_v1/report.json'),
        '2024_open': True, '2024_closed': False, 'goal_achieved': False}, archive)
    w.update(ROOT / 'Preparación/ESTADO_PROYECTO.json', {'week_2_mission017_phase2_20261025': {
        'status': 'active', 'phase': w.rel(P), 'current_batch': summary, '2024_open': True, '2024_closed': False,
        'active_jobs': [], 'goal_achieved': False, 'next_unit': next_unit}, 'week_2_mission017_phase2_execution': None}, archive)
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']:
        w.append(ROOT / 'Preparación' / name, note, archive)
    print(json.dumps({'goal_status': 'active', 'batch': 5, 'new_price_fits': 6, 'phase_price_fits': phase['new_price_fits'] + 6,
        'new_C0_fits': 0, 'new_submissions': 0, '2024_open': True, 'forum_id': summary['forum']['id']}))

if __name__ == '__main__':
    main()
