"""Integra atribución descriptiva, sin adoptar sus niveles oráculo."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
OUT = R/'privado/semana2/mision017_fase2/P13_atribucion_GLM_20261026'
sp = importlib.util.spec_from_file_location('p13_close_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not (OUT/'completion_receipt.json').exists()
    d = w.read(OUT/'report.json'); replay = w.read(OUT/'replay_report.json')
    assert len(d['loss_decompositions']) == 20 and replay['aggregate_models_checked'] == 40
    assert replay['report_sha256'] == w.sha(OUT/'report.json')
    assert d['new_model_fits'] == d['new_inference'] == d['new_submissions'] == 0
    assert (OUT/'bounded_missing_indicator_review.json').exists()
    stamp = datetime.now(timezone.utc); cut = R/'privado'/('corte_P13_'+stamp.strftime('%Y%m%dT%H%M%S%fZ')); cut.mkdir()
    next_unit = ('P14: preregister a fixed-penalty source GLM main-effects recipe adding only standardized missingness '
                 'indicators for numeric predictors with nonconstant missingness in source training. Keep source2021-2024 '
                 'data/T0/e_cost, feature values, median/clip/scale, alpha1 and all target contracts unchanged. '
                 'First prove old median/missing collision and new distinction with a synthetic full fit/predict/JSONreplay. '
                 'At most3new sourceGLMs, no masks, hypersearch, interactions, C0or futureinference. Then separately '
                 'preregister complete pooled/year-transfer validation versus original A1S/S2/H1primary and plainP12GLMsecondary, '
                 'all gates/stresses retained, no line selection or oracle rescaling. P13missing gap is evidence of '
                 'a representation limitation, not a proven causal explanation or permission to claim private improvement.')
    note = '\n\n## Privada P13: nivel, asignación y ausencia de datos del GLM, 26 de octubre de 2026\n\n'
    note += f'Codex, {stamp.isoformat()}. Se completaron las veinte descomposiciones nominales preinscritas, sin volver a ajustar, inferir, remuestrear o crear precios.\n\n'
    note += '| Ámbito global | Δ total | Δ asignación perfilada | Δ penalización de nivel | Máxima Δ con nivel oráculo nuevo frente a referencia fija |\n|---|---:|---:|---:|---:|\n'
    for a in d['loss_decompositions']:
        if a['scope'] == 'GLOBAL':
            note += f'| {a["cohort"]} | {a["delta_total"]:.7f} | {a["delta_profiled_allocation"]:.7f} | {a["delta_level_penalty"]:.7f} | {a["best_possible_new_scalar_vs_fixed_old_delta"]:.7f} |\n'
    note += ('\nEl deterioro global de transferencia se atribuye principalmente al nivel: la asignación '
             'perfilada mejora ligeramente. No corresponde afirmar que todo deterioro venga de la forma '
             'de riesgo. El nivel oráculo podría mejorar una referencia sin perfilar, pero usa respuestas '
             'retenidas y no es un factor admisible. No se ha estimado una corrección de nivel.\n\n'
             'En contenidos2023, tanto nuevos como renovaciones, aun el mejor escalar del GLM queda '
             'por debajo de la referencia fija (−0,0098682 y −0,0044354 de Δ de celda respectivamente). '
             'Edificios nuevos2023 también queda por debajo (−0,0003851). En edificios nuevos2024 hay '
             'pérdidas tanto de asignación perfilada como de nivel; su mínimo oráculo sí podría superar '
             'una referencia fija sin perfilar. La pérdida perfilada no es una métrica pura de ranking '
             'ni una atribución causal. Se verificaron las identidades por sumas escalares, desviación '
             'directa, sklearn, derivada y la invariancia de escala sobre agregados, sin crear precios reescalados.\n\n'
             'El censo de covariables produjo78banderas: trece pares ramo/variable repetidos en los seis '
             'ámbitos destino año/negocio. Todas se deben al aumento de ausentes, no a nuevas categorías '
             'o recortes numéricos grandes. En2025los campos señalados tienen entre11,37%y12,29%ausentes; '
             'las referencias fuente comparables están entre2,40%y2,54%. La máxima brecha de recorte '
             'numérico es0,65puntos porcentuales y no se observaron valores categóricos ausentes del '
             'conjunto de valores fuente en estas matrices. Esto no acredita soporte conjunto, '
             'transportabilidad o disponibilidad temporal de los maestros. El ESS2025fallido permanece.\n\n')
    note += '| Ramo | Variables con brecha de ausentes |\n|---|---|\n'
    note += '| Autos | household_size, years_at_address, distance_to_river_km, vehicle_age, engine_size_cc |\n'
    note += '| Edificios | household_size, years_at_address, distance_to_river_km, days_unoccupied |\n'
    note += '| Contenidos | household_size, years_at_address, distance_to_river_km, high_value_items |\n'
    note += ('\nP11imputa la mediana numérica sin indicador, de modo que un ausente y un valor observado '
             'igual a la mediana tienen la misma representación. La revisión acotada de cinco productores '
             'GLM fuente anteriores tampoco encontró add_indicator; no se afirma ausencia en todas las '
             'familias históricas. El mayor porcentaje de ausentes era una carencia conocida de los '
             'mercados: este censo comprueba su persistencia en el contrato actual de cuatro años, '
             'sin presentarlo como un descubrimiento causal. No se repitieron los ajustes de las '
             'recetas enmascaradas de2023.\n\n'
             'Decisión: probar primero una corrección estándar y concreta de representación, indicadores '
             'de ausencia numérica con penalización fija, antes de añadir no linealidad o interacciones. '
             'Los indicadores se decidirán por presencia no constante en fuente, nunca por su relación '
             'con respuestas destino. La hipótesis necesita nueva preinscripción y comparación completa; '
             'no se adopta una receta ni se explica todavía el fallo por los ausentes.\n\n'
             'Se guardaron40escalares oráculo solo para diagnóstico, separados de ajustes y constantes '
             'de precio. Cero fits, C0, inferencias nuevas, vectores predictivos o envíos. B00/F3c/P6y '
             'todos los adversos permanecen;2024abierto adaptativo, prioridad privada activa.\n\n')
    note += 'Evidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'; '+w.rel(OUT/'bounded_missing_indicator_review.json')+'.\n'
    doc = R/'docs/semana2/PRIVADA_P13_NIVEL_ASIGNACION_AUSENTES.md'; assert not doc.exists(); doc.write_text(note, encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, cut)
    body = OUT/'forum_resultados.md'; body.write_text(note, encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P13-ATRIBUCION-RESULTADO', '--asunto',
                             'P13: nivel y asignación distinguidos; representación de ausentes como siguiente prueba estándar',
                             '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {k: v for k, v in d.items() if k != 'loss_decompositions'}
    receipt.update(utc=stamp.isoformat(), report=w.rel(OUT/'report.json'), report_sha256=w.sha(OUT/'report.json'),
                   replay=w.rel(OUT/'replay_report.json'), document=w.rel(doc), forum=json.loads(result.stdout), next_unit=next_unit)
    cp = R/'registro/semana2_contadores_propios_actual.json'; counters = w.read(cp)
    assert 'phase2_private_P13_attribution' not in counters
    w.update(cp, {'as_of_utc': stamp.isoformat(), 'phase2_private_P13_attribution':
                  {'diagnostic_oracle_scalars_inadmissible_separate': 40, 'loss_decompositions': 20,
                   'new_model_fits': 0, 'new_price_constants': 0, 'new_inference': 0,
                   'report': receipt['report'], 'report_sha256': receipt['report_sha256']}}, cut)
    w.update(INDEX := R/'registro/semana2_atribucion_GLM_privada_actual.json', receipt, cut)
    priority = R/'registro/semana2_mision_privada_actual.json'
    w.update(priority, {'last_progress_utc': stamp.isoformat(), 'P13': receipt, 'next_unit': next_unit}, cut)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; assert not w.read(phase).get('active_jobs')
    w.update(phase, {'utc': stamp.isoformat(), 'private_P13': receipt, 'mission_private_priority': w.read(priority),
                     'next_unit': next_unit, 'last_goal_turn_classification':
                     'progress: nominal GLM allocation/level attribution and current marginal-support census complete; next standard missingness representation justified without causal claim'}, cut)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P13=receipt, mission_private_priority=w.read(priority), next_unit=next_unit, goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, cut)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_GLM_attribution_index': w.rel(INDEX), 'week_2_private_GLM_attribution_report': w.rel(doc)}, cut)
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'forum': receipt['forum'], 'new_fits': 0, 'new_submissions': 0}))


if __name__ == '__main__': main()
