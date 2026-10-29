"""Cierre de PUL sin repetir precios, remuestreo o entrenamiento."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
OUT=R/'privado/semana2/mision017_fase2/forma_ultima_PUL_20261026_v1'
sp=importlib.util.spec_from_file_location('PUL_closure_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w);sys.stdout.reconfigure(encoding='utf8')


def main():
    assert not (OUT/'completion_receipt.json').exists()
    report=w.read(OUT/'report.json');assert report['primary']=='PUL2' and len(report['numeric_controls'])==15
    stamp=datetime.now(timezone.utc);archive=OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ');archive.mkdir(parents=True)
    next_unit='First inspect age-wise changes in the NEW H1NBobservation exposure and price offset using saved artifacts only, without outcome scoring. If material, register exact old standard ageNBGLM (same5bands,K300,optimizer) under H1, retaining PUL2renewals;15newfits maximum,no tree/source/C0/kappa changes. This is a changed observation-link assay, not repeating the old G3offset age experiment or tuning age bands. Preserve old NBaddition guard so RENgains cannot mask NBdamage. Do not weaken PUL2post31criterion or tune RENweights.2024open;B00/F3c0.16914and slots preserved.'
    receipt={'author':'Codex','utc':stamp.isoformat(),'status':'complete_exploratory_post31_gate_failed','primary':'PUL2',
        'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
        'results':{name:{k:r[k] for k in ['scores','delta_vs_G3','bootstrap95','gates','weighted2025_sensitivity_delta']} for name,r in report['results'].items()},
        'incremental_vs_H1':report['incremental_vs_H1'],'new_price_estimator_fits':0,'new_C0_fits':0,'new_kappa_fits':0,
        'new_source_inference':0,'new_prediction_normalizers':60,'new_final_test_prices':0,'new_submissions':0,
        'formal_admission':False,'submission_allowed':False,'2024_open':True,'B00_all_alternatives_preserved':True,
        'goal_achieved':False,'next_unit':next_unit}
    phase=R/'registro/semana2_mision017_fase2_actual.json'
    w.update(phase,{'utc':stamp.isoformat(),'PUL':receipt,'next_unit':next_unit,'active_execution':None,'active_jobs':[]},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(PUL=receipt,next_unit=next_unit,active_jobs=[],goal_achieved=False)
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    index=R/'registro/semana2_forma_ultima_PUL_actual.json';assert not index.exists();index.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    note='\n\n## PUL: forma última separada de observación, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. Se verificó la identidad: razón RFS antigua = razón de forma última pura × completitud por mezcla exterior/completitud global. '
    note+='PUL1 aplica forma última sobre G3; PUL2 primario la aplica sobre H1. Los pesos REN .25/.25/.5 se mantienen; NB es exactamente su respectivo padre. '
    note+='No se ajustó ningún modelo, curva, kappa o parámetro de precio; hubo 60 normalizadores de predicciones, sin etiquetas retenidas.\n\n'
    for name,r in report['results'].items():
        note+=f'{name}: D² {r["scores"][name]:.8f}, diferencia frente a G3 {r["delta_vs_G3"]:+.8f}, IC95 [{r["bootstrap95"][0]:+.8f}, {r["bootstrap95"][1]:+.8f}]. '
        note+='Gana en cinco folds y ambos años. '
        note+=f'Tras retirar los 31 grupos más favorables: {r["post31_delta"]:+.8f}; sensibilidad ponderada de cartera 2025: {r["weighted2025_sensitivity_delta"]:+.8f}, con ESS insuficiente. '
        note+='Fallos: '+', '.join(k for k,v in r['gates'].items() if not v)+'.\n\n'
    inc=report['incremental_vs_H1']
    note+=f'Incremento PUL2 frente a H1: {inc["delta"]:+.8f}, IC95 pareado [{inc["paired_bootstrap95"][0]:+.8f}, {inc["paired_bootstrap95"][1]:+.8f}]. '
    note+='Se usaron las mismas unidades, orden de grupos/respuestas y semilla que HET; se restaron réplicas pareadas guardadas, sin un tercer remuestreo. '
    note+='La igualdad de NB, la independencia de la forma última respecto de campos observados y la matemática logarítmica pasaron.\n\n'
    note+='PUL2 supera magnitud, intervalo, folds, años y peor celda, pero falla concentración tras 31 grupos. No se relaja ese control ni se afinan pesos o eliminan grupos. '
    note+='No se prepara envío de este candidato. La señal es exploratoria tras búsqueda adaptativa; no hay un comparador histórico completo F3c ni prueba de que la diferencia local se traslade al público.\n\n'
    note+='La siguiente revisión será la edad en NB bajo el nuevo enlace H1, primero solo con sus exposiciones y offsets guardados. '
    note+='La antigua prueba de edad usó G3 con mezcla global; no se repetirá con fuentes iguales. Solo si el cambio de observación/offset resulta material se registrará la misma receta GLM estándar, con bandas y K intactos, y guardas NB para impedir que REN oculte daño. '
    note+='No se añade profundidad o arquitectura.\n\n'
    note+='2024 abierto y adaptativo. B00, F3c 0,16914, H1/H2 y todos los adversos permanecen. Cero precios finales de 2025 o envíos; meta pública 0,17 activa. '
    note+='Evidencia: '+w.rel(OUT/'report.json')+'.\n'
    doc=R/'docs/archivo/semana2/MISION017_PUL_RESULTADO.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    body=OUT/'forum_resultados.md';body.write_text(note,encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-PUL-RESULTADO','--asunto','PUL2 mejora +0,00259 local; persiste concentración y no se envía',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt.update(document=w.rel(doc),forum=json.loads(response.stdout))
    w.update(index,receipt,archive/'post_forum');w.update(phase,{'PUL':receipt},archive/'post_forum')
    own=w.read(state)['week_2_mission017_phase2_20261025'];own['PUL']=receipt
    w.update(state,{'week_2_mission017_phase2_20261025':own},archive/'post_forum')
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_mission017_PUL_index':w.rel(index),'week_2_mission017_PUL_report':w.rel(doc)},archive/'post_forum')
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'status':receipt['status'],'results':receipt['results'],'incremental_vs_H1':inc,'forum':receipt['forum']},ensure_ascii=True))


if __name__=='__main__':main()
