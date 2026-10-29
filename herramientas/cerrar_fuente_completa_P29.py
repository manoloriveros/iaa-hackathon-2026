"""Cierra la exportación fuente P29 sin ajustar ni volver a predecir."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P29_fuente_frecuencia_completa_20261026'
INDEX = R/'registro/semana2_fuente_frecuencia_completa_privada_actual.json'
DOC = R/'docs/archivo/semana2/PRIVADA_P29_FUENTE_COMPLETA_NUMERO_MARCA.md'
sp = importlib.util.spec_from_file_location('p29_close_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not (OUT/'completion_receipt.json').exists()
    report = w.read(OUT/'report.json'); plan = w.read(R/'registro/semana2_fuente_frecuencia_completa_privada_plan.json')
    assert report['plan_sha256'] == w.sha(R/'registro/semana2_fuente_frecuencia_completa_privada_plan.json')
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    assert all(w.sha(ROOT/p) == z for p, z in report['outputs'].items())
    assert len(list(OUT.glob('*/*/controls.json'))) == len(list(OUT.glob('*/*/fit_invoked.json'))) == 30
    model_hashes = {}; gradients = []
    for path in OUT.glob('*/*/fit_record.json'):
        saved = w.read(path); assert saved['model_sha256'] == w.sha(path.parent/'model.json')
        assert saved['plan_sha256'] == report['plan_sha256']
        controls = w.read(path.parent/'controls.json'); assert controls['max_abs_gradient'] <= 1e-4
        model_hashes[w.rel(path.parent/'model.json')] = saved['model_sha256']; gradients.append(controls['max_abs_gradient'])
    applications = [w.read(OUT/line/'application.json') for line in ['motor', 'buildings', 'contents']]
    assert sum(x['historical_rows'] for x in applications) == 109296
    assert all(x['new_future_inference'] == 0 and x['JSONhistorical_pipeline_sample_exact'] and x['source_relative_mean_one'] for x in applications)
    now = datetime.now(timezone.utc).isoformat()
    next_unit = ('P30: preregister complete current50/50S2/H1comparison using P29single fixed peril-sum source caches against original A1Ssource. '
        'Reuse unchanged P26strict source-key adapter and complete learning/forward engine by hash; validate new30source scope bindings, no repeat unchanged fixtures. '
        '30primary whole closedS2learners plus30held-poison controls, source/C0/N3/H1frozen. All original global/NB/broker/cohort/stress gates unchanged. '
        'No line/seed/peril selection or reinterpretation of source gate as target/private admission. No new2025inference, prices or upload before target assessment.')
    text = '# P29: fuente completa preparada para el contraste de transporte\n\nCodex, '+now+'. '
    text += ('Se completaron30refits GLM con la receta P28congelada y tres normalizadores relativos. '
        'Son15pares por peril, sumados por ramo; no hay tres semillas aunque el nombre de caché conserve esa compatibilidad. '
        'Los109.296componentes históricos2023/2024quedaron guardados, sin calibrar ni puntuar sus etiquetas.\n\n'
        'Preprocesamiento, respuestas, pesos y reescala de penalización se calcularon en toda la fuente, con el mismo contrato ya probado. '
        'Cada JSONse guardó antes de los controles y se consumió desde disco para construir las tasas anuales. '
        'Convergencia, gradiente máximo, carga/orden y predictor escalar pasaron. La suma anual por peril y el centro por exposición se cotejaron por otro método; '
        'la media relativa ponderada fuente es uno y la aplicación histórica desde JSONcoincidió en las muestras comprobadas. '
        'El nuevo fixture de composición anual no ajustó ningún modelo; los fixtures de familias que no cambiaron se reutilizaron.\n\n'
        'Los datos2025se filtraron antes de transformar o predecir. Cero inferencias2025, precios finales, C0nuevo, calibraciones o scores destino y envíos. '
        'No se vuelve a contar el aprendizaje interno de P28ni se interpreta el ajuste con toda la fuente como otra validación. '
        'Los vínculos de observación tienen ancestros comunes; cola y suficiencia de reservas siguen sin identificarse. '
        'B00/F3c y todas las alternativas se conservan,2024abierto adaptativo. No hay mejora privada acreditada.\n\nPróximo: '+next_unit
        +'\n\nEvidencia: '+w.rel(OUT/'report.json')+'. Código previo a los refits:9deafed3.\n')
    assert not DOC.exists(); DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P29-FRECUENCIA-RESULTADO',
        '--asunto', 'P29: GLM completos y componentes históricos listos; falta contraste de transporte',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': now, 'status': report['status'], 'report': w.rel(OUT/'report.json'),
        'report_sha256': w.sha(OUT/'report.json'), 'document': w.rel(DOC), 'forum': json.loads(posted.stdout),
        'new_source_GLM_fits': 30, 'new_source_normalizers': 3, 'historical_components': 109296,
        'model_hashes': model_hashes, 'maximum_gradient': max(gradients),
        'new_C0_fits': 0, 'new_target_scores': 0, 'new_future_inference': 0, 'new_submissions': 0,
        'next_unit': next_unit, 'goal_achieved': False, '2024_open': True, 'B00_all_alternatives_preserved': True}
    archive = R/'privado'/('corte_P29_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    cp = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(cp); entry = counters['phase2_private_P29_full_pairs']
    assert entry['attempts'] == entry['completed'] == 30 and not entry.get('source_normalizers_counted')
    entry.update(source_normalizers_counted=3, report=receipt['report'], report_sha256=receipt['report_sha256'])
    w.update(cp, {'phase2_private_P29_full_pairs': entry, 'cumulative_closed_form_constants': counters['cumulative_closed_form_constants']+3}, archive)
    w.update(INDEX, receipt, archive)
    w.update(R/'registro/semana2_mision_privada_actual.json', {'P29': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P29_source': receipt, 'next_unit': next_unit}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']; own.update(private_P29_source=receipt, next_unit=next_unit)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P29: fuente completa sin score destino, 26 de octubre de2026\n\nCodex, '+now+'.30refits GLM por peril y3normalizadores;109.296componentes históricos listos. JSON/gradiente/suma/centro y muestras históricas verificados. No tres semillas, no mejora privada acreditada. Cero C0/inferencia2025/score destino/envíos; B00/F3cy2024abierto adaptativo conservados. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_count_mark_full_source_index': w.rel(INDEX), 'week_2_private_count_mark_full_source_report': w.rel(DOC)}, archive)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'closed': True, 'new_source_fits': 30, 'source_normalizers': 3, 'new_target_scores': 0, 'forum': receipt['forum']}))


if __name__ == '__main__': main()
