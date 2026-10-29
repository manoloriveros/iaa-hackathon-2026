"""Cierre de DT1 y contabilidad; no reproduce entrenamiento ni estadísticas."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
OUT=R/'privado/semana2/mision017_fase2/residuo_aditivo_DT1_20261026_v1'
sp=importlib.util.spec_from_file_location('DT1_closure_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w)
sys.stdout.reconfigure(encoding='utf8')


def main():
    assert not (OUT/'completion_receipt.json').exists()
    report=w.read(OUT/'report.json')
    assert len(list(OUT.glob('model_*/record.json')))==15
    assert len(report['numeric_controls'])==15
    stamp=datetime.now(timezone.utc);archive=OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ');archive.mkdir(parents=True)
    next_unit='Investigate risk-dependent peril reporting completion as a distinct observation-link uncertainty using saved outer C0 and existing FSp source components/outer calibration artifacts only. First measure its variation/availability without new fits, curves, prices, scores or inference; no automatic recipe or adoption. Do not repeat DT1/A1S/GLM or tune depth/rounds/weights.2024open;B00/F3c0.16914and quota preserved.'
    receipt={'author':'Codex','utc':stamp.isoformat(),'status':'complete_exploratory_no_admission',
        'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
        'new_real_target_price_fits':15,'new_training_nuisance_levels':60,'synthetic_fits_separate':3,
        'new_source_fits':0,'new_C0_fits':0,'new_final_test_prices':0,'new_submissions':0,
        'scores':report['scores'],'delta_vs_G3':report['delta_vs_G3'],'bootstrap95':report['bootstrap95'],
        'gates':report['gates'],'formal_admission':False,'submission_allowed':False,
        '2024_open':True,'goal_achieved':False,'B00_all_alternatives_preserved':True,'next_unit':next_unit}
    cp=R/'registro/semana2_contadores_propios_actual.json';counter=w.read(cp)
    assert 'phase2_DT1' not in counter
    w.update(cp,{'as_of_utc':stamp.isoformat(),'cumulative_price_base_fits':counter['cumulative_price_base_fits']+15,
                 'cumulative_closed_form_constants':counter['cumulative_closed_form_constants']+60,
                 'phase2_DT1':receipt},archive)
    phase=R/'registro/semana2_mision017_fase2_actual.json';p=w.read(phase)
    w.update(phase,{'utc':stamp.isoformat(),'DT1':receipt,'new_price_fits':p['new_price_fits']+15,
                    'active_execution':None,'active_jobs':[],'next_unit':next_unit,'2024_open':True,'2024_closed':False},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(DT1=receipt,next_unit=next_unit,active_jobs=[],goal_achieved=False)
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    note='\n\n## DT1: corrección aditiva acotada, resultado adverso, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. Se completaron los 15 modelos preinscritos, cada uno con 60 árboles de una división y las covariables congeladas. '
    note+='Todos respetan la profundidad y la cota de 0,001 por hoja, sin sesgo inicial oculto en el modelo guardado. '
    note+='La corrección logarítmica bruta está acotada por 0,06 y las razones normalizadas por exp(±0,12). '
    note+='Se conservan los 60 niveles nuisance de entrenamiento, sin transferirlos; no se ajustaron modelos fuente o C0.\n\n'
    note+=f'D² local: DT1 {report["scores"]["DT1"]:.8f}, G3 {report["scores"]["G3"]:.8f}; diferencia {report["delta_vs_G3"]:+.8f}. '
    note+=f'IC95 por componentes [{report["bootstrap95"][0]:+.8f}, {report["bootstrap95"][1]:+.8f}]. '
    note+='Gana en dos de cinco folds y empeora en ambos años. Fallan los seis umbrales exploratorios. '
    note+=f'Tras retirar los 31 grupos más favorables: {report["post31_delta"]:+.8f}; sensibilidad ponderada de cartera 2025: {report["weighted2025_sensitivity_delta"]:+.8f}, con el ESS insuficiente ya documentado. '
    note+='Se conserva el resultado completo; no se cambian rondas, profundidad o pesos después de verlo ni se genera entrega.\n\n'
    note+='Los tres ajustes sintéticos verificaron el flujo completo antes del registro. En los 15 problemas reales, alterar las respuestas/reservas retenidas no cambia diseño, respuestas de entrenamiento, categorías, offset, nuisance o inicialización. '
    note+='Pasaron modelo guardado, orden, suma independiente de hojas, métrica Tweedie por sklearn, identidad de efecto cero y replay con entrenamiento bloqueado. '
    note+='Esos controles certifican lo comprobado en la implementación, no una mejora predictiva o revisión profesional independiente.\n\n'
    note+='El siguiente mecanismo será revisar la completitud por mezcla de perils de cada riesgo, con artefactos guardados. '
    note+='La mezcla global del enlace de observación es una aproximación; su eventual variación por covariables debe medirse antes de cambiar exposición u objetivo. '
    note+='Este diagnóstico inicial no ajusta, recalcula curvas, crea precios o puntúa modelos. No se adopta todavía ninguna corrección de exposición.\n\n'
    note+='2024 abierto y adaptativo; B00, F3c 0,16914 y alternativas intactos. Ningún envío o cupo consumido. Meta 0,17 activa. '
    note+='Evidencia: '+w.rel(OUT/'report.json')+'.\n'
    doc=R/'docs/archivo/semana2/MISION017_DT1_RESULTADO.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    body=OUT/'forum_resultados.md';body.write_text(note,encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-DT1-RESULTADO','--asunto','DT1 cumple cotas pero empeora; se revisará el enlace de observación',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt.update(document=w.rel(doc),forum=json.loads(response.stdout))
    w.update(phase,{'DT1':receipt},archive/'post_forum')
    own=w.read(state)['week_2_mission017_phase2_20261025'];own['DT1']=receipt
    w.update(state,{'week_2_mission017_phase2_20261025':own},archive/'post_forum')
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_mission017_DT1_report':w.rel(doc)},archive/'post_forum')
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:receipt[k] for k in ['status','scores','delta_vs_G3','bootstrap95','forum']},ensure_ascii=True))


if __name__=='__main__':main()
