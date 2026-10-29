"""Registra el CSV numérico, conservando las carencias predictivas y sin upload."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
OUT=R/'privado/semana2/mision017_fase2/F3c_PUL2_prototipo_20261026_v1'
sp=importlib.util.spec_from_file_location('prototype_PUL2_closure',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w);sys.stdout.reconfigure(encoding='utf8')


def main():
    assert not (OUT/'completion_receipt.json').exists()
    report=w.read(OUT/'report.json');csv=ROOT/report['CSV']['path']
    assert w.sha(csv)==report['CSV']['sha256'] and report['CSV']['rows']==209063
    assert len(report['inferences'])==3 and not report['submission_allowed']
    stamp=datetime.now(timezone.utc);archive=OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ');archive.mkdir(parents=True)
    next_unit='Before any admission/upload, register and run an exact-production transfer diagnostic on saved held S0/S1/S2and originalA1_2024proxies: apply H1/G3then pureFSpRENnormalized on each corrected base, sameweights, no newfits/sourceinference. Report all bases, years/folds/cells, post31and fixed+-5percentlevel sensitivity; no winner selection or retrospective gate changes. G3identity reuses PUL2receipt. Preserve ensemble/F3c-history/ESSlimits and failedpost31.2024open;B00/F3c0.16914preserved; no automatic POST.'
    receipt={'author':'Codex','utc':stamp.isoformat(),'status':report['status'],'report':w.rel(OUT/'report.json'),
        'report_sha256':w.sha(OUT/'report.json'),'CSV':report['CSV'],'submission_allowed':False,'submission_ready':False,
        'predictive_admission':False,'formal_promotion':False,'post31_failure_preserved':True,
        'new_model_fits':0,'new_C0_fits':0,'new_kappa_fits':0,'new_submissions':0,
        'new_primary_NB_T2b_rows':158980,'new_order_check_rows':96,'cached_REN_rows':50083,
        'prediction_only_normalizers':110,'control_identity_normalizers_separate':15,
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,'next_unit':next_unit}
    phase=R/'registro/semana2_mision017_fase2_actual.json'
    w.update(phase,{'utc':stamp.isoformat(),'F3c_PUL2_prototype':receipt,'next_unit':next_unit,'active_execution':None,'active_jobs':[]},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(F3c_PUL2_prototype=receipt,next_unit=next_unit,active_jobs=[],goal_achieved=False)
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    index=R/'registro/semana2_F3c_PUL2_prototipo_actual.json';assert not index.exists();index.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    oldtotal=87269136.42047201;newtotal=report['CSV']['total_CU']
    note='\n\n## F3c/PUL2: prototipo 2025 reproducible, sin admisión de envío, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. Se generó el CSV de 209.063 filas, en el orden oficial, con importes positivos y seis decimales. '
    note+=f'Total: {newtotal:,.6f} CU, frente a {oldtotal:,.6f} de F3c (+{100*(newtotal/oldtotal-1):.3f}%). '
    note+='En autos NB el total sube aproximadamente 2,394%; en edificios NB 0,959% y contenidos NB 0,092%. '
    note+='NB recibe solo H1/G3, sin edad ni FSp. La forma FSp de REN conserva el total ya corregido por observación, no el antiguo total F3c.\n\n'
    note+='Se reutilizaron 50.083 tasas REN verificadas por hash previo y los kernels FSp, cotejados con su álgebra fuente exacta. '
    note+='Hubo tres inferencias T2b nuevas para 158.980 NB y 96 filas de control de orden. No hubo ajuste, C0, kappa o parámetro de calibración nuevo. '
    note+='Se calcularon 110 normalizadores: 80 en G3/H1, 15 en la composición y 15 en el componente propio de contraste; las identidades de control se cuentan aparte. '
    note+='Las versiones de preflight/código previas al fortalecimiento QA y la precisión editorial del contador quedaron archivadas antes del registro, sin predicciones entonces.\n\n'
    note+='Pasaron claves/orden, categorías explícitas, bandas históricas, ancestros y representación bool de teletrabajo; usar su 0/1 transformado habría dejado factores desconocidos. '
    note+='El flujo real ignoró los marcadores observados cero de 2025 y usó calendario una sola vez para último. Se cotejaron G3/H1 y precios por otro cálculo escalar logarítmico, invariancia de claves y rechazos de tasas inválidas. '
    note+='Redondeo racional IEEE a microCU, comprobación Decimal independiente y readback fueron exactos. F3c original permanece intacto.\n\n'
    note+='Este resultado es preparación numérica, no mejora pública verificada. PUL2 conserva el fallo post31, la media de cinco miembros no tiene validación anidada y no se reprodujo el F3c histórico completo. '
    note+='El ESS ponderado insuficiente y los límites de reservas/cola/vintage siguen vigentes. El productor no tiene vía de upload; submission_allowed y submission_ready permanecen false. '
    note+='La entrega vigente continúa siendo F3c 0,16914.\n\n'
    note+='Antes de cualquier decisión de admisión se revisará la transferencia con el operador exacto de producción sobre las bases guardadas S0/S1/S2 y A1 original de 2024. '
    note+='Se registrará antes de crear o puntuar esas predicciones, sin entrenar ni escoger el mejor proxy después. Se informarán concentración y sensibilidad de nivel, sin convertirlos en validación del F3c real.\n\n'
    note+='CSV: '+w.rel(csv)+'; SHA256 '+report['CSV']['sha256']+'. Evidencia: '+w.rel(OUT/'report.json')+'. '
    note+='B00 y alternativas preservados; 2024 abierto y adaptativo, cero cupos consumidos, meta pública 0,17 activa.\n'
    doc=R/'docs/archivo/semana2/MISION017_F3C_PUL2_PROTOTIPO_2025.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    body=OUT/'forum_resultados.md';body.write_text(note,encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-F3C-PUL2-PROTO-RESULTADO','--asunto','F3c/PUL2 2025 preparado y cotejado; sin upload ni admisión predictiva',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt.update(document=w.rel(doc),forum=json.loads(response.stdout))
    w.update(index,receipt,archive/'post_forum');w.update(phase,{'F3c_PUL2_prototype':receipt},archive/'post_forum')
    own=w.read(state)['week_2_mission017_phase2_20261025'];own['F3c_PUL2_prototype']=receipt
    w.update(state,{'week_2_mission017_phase2_20261025':own},archive/'post_forum')
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_mission017_F3c_PUL2_prototype_index':w.rel(index),
        'week_2_mission017_F3c_PUL2_prototype_report':w.rel(doc),'week_2_mission017_F3c_PUL2_unadmitted_CSV':w.rel(csv)},archive/'post_forum')
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'status':receipt['status'],'CSV':receipt['CSV'],'submission_allowed':False,'forum':receipt['forum']},ensure_ascii=True))


if __name__=='__main__':main()
