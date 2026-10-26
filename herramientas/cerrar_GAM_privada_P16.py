"""Cierra el paquete GAM combinado y el fallo original sin duplicar fits."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; OUT = BASE/'P16_GAM_bedrooms_lineal_20261026'
PREVIOUS = BASE/'P16_GAM_fuente_20261026'
sp = importlib.util.spec_from_file_location('p16_close_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not (OUT/'completion_receipt.json').exists()
    d = w.read(OUT/'report.json'); replay = w.read(OUT/'amendment_replay_context.json'); plan = w.read(R/'registro/semana2_GAM_bedrooms_lineal_plan.json')
    assert d['combined_source_GAMfits'] == 3 and d['new_source_GAMfits_in_amendment'] == 1 and d['reused_models'] == 2
    assert not (PREVIOUS/'contents/model.json').exists() and replay['new_fits'] == 0
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    parameters = {line: len(w.read(OUT/line/'model.json')['coef'])+1 for line in ['motor', 'buildings', 'contents']}
    assert parameters == {'motor': 157, 'buildings': 129, 'contents': 125}
    stamp = datetime.now(timezone.utc); cut = R/'privado'/('corte_P16_'+stamp.strftime('%Y%m%dT%H%M%S%fZ')); cut.mkdir()
    next_unit = ('P17: implement and preregister complete comparison of GAM4_MI_bedrooms_linear from '
                 'P16_GAM_bedrooms_lineal_20261026 versus original A1S/S2/H1primary and P15linear-MIsecondary. '
                 'Source packet complete; do not refit any of its3models or resume failed original P16run. '
                 'Bind current3historical caches with same scopes/offsets/C0/N3/H1ratios;30primaryS2closedlearners '
                 'plus30full-held-poisoncontrols, no new C0/sourcefits/futureinference. Reuse frozen P12/P15 '
                 'complete numerical engine and source keys; keep .002minimum, fold/year/Post31/cell floors '
                 'and4scenarios. Paired secondary bootstrap can subtract existing P15draws with identical '
                 'groups/outcomes/order/seeds/null denominators, no second resampling. Declare current family '
                 'GAM5/4/3curves, bedrooms linear and one source model perline despite legacy cache filename. '
                 'Freeze wrapper/source hashes/criterion/cost/forum before new calibration or scoring; no '
                 'oraclelevels, line-selection or publicscore tuning. All outcomes remain exploratory with '
                 'source2024and adaptive target years; no uploads or private-performance claim from source-only completion.')
    note = '\n\n## Privada P16: paquete GAM completo tras enmienda de dormitorios, 26 de octubre de 2026\n\n'
    note += (f'Codex, {stamp.isoformat()}. Quedaron guardados los tres modelos fuente aditivos, con '
             'indicadores de ausencia y penalización1fija. Autos conserva cinco curvas y edificios '
             'cuatro; contenidos conserva tres curvas y el efecto lineal de bedrooms. Los parámetros '
             'totales son157,129y125respectivamente. No hay interacciones o búsqueda de nudos.\n\n'
             'El intento original se detuvo en el preprocesamiento de contenidos porque los cuantiles '
             'fuente de bedroomsfueron[1,3,3,6]. Se había definido un guardia que exigía nudos distintos, '
             'pero el fixture original solo ejerció las curvas de edificios y no detectó el caso de '
             'contenidos. El fallo ocurrió antes de estimator.fit: dos modelos reales quedaron completos '
             'y el tercero no llegó a ajustarse. Código, plan, marcadores y fallo originales permanecen.\n\n'
             'La enmienda se registró antes de continuar. Se retuvo el efecto lineal de dormitorios '
             'de la receta previa, sin probar otros nudos ni mirar un score destino de esta familia. '
             'El preflight de origen comprobó cuantiles estrictos en las otras tres variables de '
             'contenidos. Un nuevo fixture con dormitorios discretos repetidos pasó ajuste,JSONyorden. '
             'Autos y edificios se copiaron byte a byte con sus hashes y sus funciones/listas sin cambios. '
             'Solo se ajustó contenidos una vez, con llamada real a estimator.fitregistrada.\n\n'
             'Contabilidad: cuatro invocaciones de pipeline en total, una fallida antes de ajustar, '
             'tres llamadas reales de ajuste GAM(2originales+1enmienda), dos fits sintéticos separados. '
             'No se repitieron los modelos ya terminados. El replay conjunto desde JSONfue exacto '
             'con fitbloqueado y recuperó las109.296relatividades históricas. La repetición histórica '
             'del replay se cuenta aparte; no consulta2025. El nombre de caché three_seedes una '
             'interfaz heredada, con un único modelo GAMpor ramo.\n\n'
             'No se calcularon scores destino de esta familia, C0, calibraciones destino, inferencias2025, '
             'precios finales o envíos. La siguiente unidad registrará la comparación completa frente '
             'a A1Sy frente al GLMlineal con indicadores. Las conclusiones seguirán condicionadas por '
             'fuente2021–2024y ambos años destino adaptativos. No se acredita mejora privada o promoción. '
             'B00/F3c/P6y todos los fallos/alternativas se mantienen.\n\n')
    note += 'Evidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'amendment_replay_context.json')+'; intento original '+w.rel(PREVIOUS)+'.\n'
    doc = R/'docs/semana2/PRIVADA_P16_GAM_FUENTE_Y_ENMIENDA.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, cut)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P16-GAM-RESULTADO', '--asunto',
                             'P16: tres GAM fuente listos, dos reutilizados y dormitorios lineales; validación pendiente',
                             '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = dict(d); receipt.update(utc=stamp.isoformat(), report=w.rel(OUT/'report.json'), report_sha256=w.sha(OUT/'report.json'),
                   replay=w.rel(OUT/'amendment_replay_context.json'), document=w.rel(doc), forum=json.loads(result.stdout),
                   parameters=parameters, next_unit=next_unit)
    cp = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(cp)
    assert 'phase2_private_P16_source_GAM' not in counters
    w.update(cp, {'as_of_utc': stamp.isoformat(), 'cumulative_price_base_fits': counters['cumulative_price_base_fits']+3,
                  'phase2_private_P16_source_GAM': {'actual_source_estimator_fits': 3, 'pipeline_invocations': 4,
                    'preprocessing_failures_before_estimator_fit': 1, 'reused_completed_models_not_additional_fits': 2,
                    'synthetic_source_GAMfits_separate': 2, 'parameters_not_closedform_constants': sum(parameters.values()),
                    'historical_replay_inference_rows_separate': 109296, 'report': receipt['report'], 'report_sha256': receipt['report_sha256']}}, cut)
    initial_index = R/'registro/semana2_GAM_fuente_privada_actual.json'
    w.update(initial_index, {'status': 'partial_terminal_two_models_and_prefit_contents_failure',
                            'continuation_index': w.rel(R/'registro/semana2_GAM_bedrooms_lineal_actual.json'),
                            'own_actual_source_fits': 2, 'prefit_failure_scopes': 1, 'do_not_resume_original_run': True}, cut)
    w.update(INDEX := R/'registro/semana2_GAM_bedrooms_lineal_actual.json', receipt, cut)
    priority = R/'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P16': receipt, 'next_unit': next_unit}, cut)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; current = w.read(phase); assert not current.get('active_jobs')
    w.update(phase, {'utc': stamp.isoformat(), 'private_P16': receipt, 'new_price_fits': current['new_price_fits']+3,
                     'mission_private_priority': w.read(priority), 'next_unit': next_unit,
                     'last_goal_turn_classification': 'progress: missing-indicator recipe fully evaluated/adverse retained, fixed additive source packet completed with pre-fit amendment/reuse; complete target comparison next'}, cut)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P16=receipt, new_price_fits=current['new_price_fits']+3, mission_private_priority=w.read(priority), next_unit=next_unit, goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, cut)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_additive_source_initial_index': w.rel(initial_index),
                                        'week_2_private_additive_source_index': w.rel(INDEX),
                                        'week_2_private_additive_source_report': w.rel(doc)}, cut)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'actual_source_GAMfits': 3, 'new_submissions': 0, 'forum': receipt['forum']}))


if __name__ == '__main__': main()
