"""Conserva el diagnóstico de transferencia y las carencias; no crea precios."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
OUT=R/'privado/semana2/mision017_fase2/transferencia_PUL2_20261026_v1'
sp=importlib.util.spec_from_file_location('PUL2_transfer_closure',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w);sys.stdout.reconfigure(encoding='utf8')


def main():
    assert not (OUT/'completion_receipt.json').exists()
    report=w.read(OUT/'report.json');assert len(report['numeric_controls'])==15
    stamp=datetime.now(timezone.utc);archive=OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ');archive.mkdir(parents=True)
    next_unit='Prepare a finite PUL2reserve/reporting observation-stress audit with frozen prices/rates and saved outerC0curves only. Inspect available075/100/125reserve and late-cost scenario contracts first; do not refit or claim full-pipeline revaluation. Define transformed observed predictions/exposure per risk/global consistently, freeze sources/hypothesis/criteria/forum before scoring new scenarios. Preserve failedpost31, S0uncertainty, F3chistory and ensemblelimits. Then review concrete research readiness and actualquota; no automatic POSTfrom prototype.2024open;B00/F3c0.16914and alternatives retained.'
    receipt={'author':'Codex','utc':stamp.isoformat(),'status':report['status'],'report':w.rel(OUT/'report.json'),
        'report_sha256':w.sha(OUT/'report.json'),'new_fits':0,'new_C0_fits':0,'new_source_inference':0,
        'new_prediction_normalizers':105,'G3_identity_control_normalizers_separate':30,'new_CSVs':0,'new_submissions':0,
        'not_full_F3c_validation':True,'post31_failure_unchanged':True,'submission_allowed':False,
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,'next_unit':next_unit}
    phase=R/'registro/semana2_mision017_fase2_actual.json'
    w.update(phase,{'utc':stamp.isoformat(),'PUL2_transfer_audit':receipt,'next_unit':next_unit,'active_execution':None,'active_jobs':[]},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(PUL2_transfer_audit=receipt,next_unit=next_unit,active_jobs=[],goal_achieved=False)
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    index=R/'registro/semana2_transferencia_PUL2_actual.json';assert not index.exists();index.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    note='\n\n## PUL2: transferencia del operador de producción, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. Se aplicó el operador exacto del prototipo, incluyendo normalización REN sobre cada base ya corregida H1/G3. '
    note+='Se reportan todas las bases preinscritas, sin escoger la mejor o cambiar niveles. G3 reprodujo PUL2 dentro del error numérico y su informe previo se reutilizó. '
    note+='Ningún ajuste, C0, inferencia fuente, CSV nuevo o envío.\n\n'
    for name,r in report['source_safe_bases'].items():
        note+=f'{name}: diferencia {r["delta"]:+.8f}, IC95 [{r["bootstrap95"][0]:+.8f}, {r["bootstrap95"][1]:+.8f}], '
        note+=f'intervalo simultáneo exploratorio de familia [{r["simultaneous95_family"][0]:+.8f}, {r["simultaneous95_family"][1]:+.8f}]. '
        note+=f'Tras quitar los 31 grupos más favorables: {r["post31_delta"]:+.8f}; tras el peor grupo individual: {r["worst_single_group_removed_delta"]:+.8f}. '
        note+='La dirección puntual es positiva en ambos años y al menos cuatro folds; el intervalo de S0 incluye cero.\n\n'
    a=report['conditional_A1_2024']['A1']
    note+=f'Proxy A1 original de 2024: diferencia {a["delta"]:+.8f}, IC95 [{a["bootstrap95"][0]:+.8f}, {a["bootstrap95"][1]:+.8f}], post31 {a["post31_delta"]:+.8f}. '
    note+='Su linaje de observación original no acredita confirmación independiente por grupo; este resultado es condicional y no sustituye F3c completo. '
    note+='Las sensibilidades de nivel ±5% mantienen diferencias puntuales positivas, sin elegir un nivel para el CSV a partir de esos scores.\n\n'
    note+='En el futuro, el cociente máximo/mínimo de los cinco miembros llega a 1,05955 en contenidos REN, 1,01981 en edificios REN y 1,01469 en autos REN; '
    note+='en NB los máximos son 1,00888 en autos, 1,00288 en edificios y 1,00152 en contenidos. Ninguna fila supera 1,10. '
    note+='Es estabilidad entre modelos correlacionados, no un intervalo predictivo ni validación anidada del ensemble.\n\n'
    note+='La transferencia de dirección está respaldada en varias bases, pero no queda demostrado el efecto sobre el F3c real de validación. '
    note+='Todos los diagnósticos post31 siguen negativos y S0 conserva incertidumbre que incluye cero. No se modifica esa evidencia o los criterios, no se habilita upload. '
    note+='El siguiente control será de reservas/reportes bajo tasas y curvas guardadas, con hipótesis y transformación de observación fijadas antes de nuevos scores. '
    note+='Debe distinguirse sensibilidad de observación de revaloración completa del modelo; no se estimarán curvas para rellenar una cadencia.\n\n'
    note+='B00, F3c 0,16914, el prototipo preparado y todas las alternativas se conservan.2024 abierto y adaptativo. Cero cupos consumidos; objetivo público 0,17 activo. '
    note+='Evidencia: '+w.rel(OUT/'report.json')+'.\n'
    doc=R/'docs/archivo/semana2/MISION017_PUL2_TRANSFERENCIA.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    body=OUT/'forum_resultados.md';body.write_text(note,encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-PUL2-TRANSFERENCIA-RESULTADO','--asunto','Transferencia PUL2 positiva en varias bases; persisten concentración e incertidumbre',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt.update(document=w.rel(doc),forum=json.loads(response.stdout))
    w.update(index,receipt,archive/'post_forum');w.update(phase,{'PUL2_transfer_audit':receipt},archive/'post_forum')
    own=w.read(state)['week_2_mission017_phase2_20261025'];own['PUL2_transfer_audit']=receipt
    w.update(state,{'week_2_mission017_phase2_20261025':own},archive/'post_forum')
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_mission017_PUL2_transfer_index':w.rel(index),
        'week_2_mission017_PUL2_transfer_report':w.rel(doc)},archive/'post_forum')
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'status':receipt['status'],'new_fits':0,'new_submissions':0,'submission_allowed':False,'forum':receipt['forum']},ensure_ascii=True))


if __name__=='__main__':main()
