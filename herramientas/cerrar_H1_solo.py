"""Registra la ablación H1, sus escenarios y el prototipo sin promoción."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton'); R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2'; OUT=BASE/'H1_solo_prototipo_20261026_v1'
TRANSFER=BASE/'transferencia_H1_solo_20261026_v1'
sp=importlib.util.spec_from_file_location('H1_own_state_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w);sys.stdout.reconfigure(encoding='utf8')


def main():
    assert not (OUT/'completion_receipt.json').exists() and not (TRANSFER/'completion_receipt.json').exists()
    a=w.read(TRANSFER/'report.json'); b=w.read(OUT/'report.json');csv=ROOT/b['CSV']['path']
    assert w.sha(csv)==b['CSV']['sha256'] and b['CSV']['rows']==209063
    assert a['new_model_fits']==b['new_model_fits']==0
    stamp=datetime.now(timezone.utc); archive=OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ');archive.mkdir(parents=True)
    next_unit=('Prepare an explicit finite research-delivery decision for the simpler F3c*H1/G3 prototype, not PUL2: '
               'copy by pinned SHA, official5check dryrun, idempotent submit/check transport and separately justified research exception if warranted. '
               'Keep formal gain.002 gate failed and reserve/tail NB adverse cases visible; no guarantee of.17 or invented human signoff. '
               'At most one public probe after a fresh actual quota response permits it; current26Oct10:32UTCquota=0, so no POSTnow. '
               'Do not repeat finished fits/audits or poll quota unchanged just to fill a turn. '
               '2024open adaptive, B00/F3c0.16914 and all alternatives retained; fullF3c held replay/nestedensemble/weightedESSlimits remain.')
    receipt={'author':'Codex','utc':stamp.isoformat(),'status':b['status'],'CSV':b['CSV'],
             'transfer_report':w.rel(TRANSFER/'report.json'),'transfer_report_sha256':w.sha(TRANSFER/'report.json'),
             'scenario_prototype_report':w.rel(OUT/'report.json'),'scenario_prototype_report_sha256':w.sha(OUT/'report.json'),
             'new_fits':0,'new_C0_fits':0,'new_source_inference':0,'new_prediction_normalizers':0,
             'new_CSVs':1,'new_submissions':0,'formal_promotion':False,'submission_allowed':False,
             'formal_minimum_gain002_passed_source_safe_bases':False,'NB_reserve_tail_adverses_preserved':True,
             'full_historic_F3c_replay_established':False,'future_ensemble_nested_validation_established':False,
             '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,'next_unit':next_unit}
    note='\n\n## H1 sola: mejora más estable y prototipo simple, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. Se aisló la corrección de exposición por peril H1/G3, sin forma FSp de renovaciones, pesos nuevos o normalizadores adicionales. '
    note+='La hipótesis surgió de un fallo concreto: PUL2 perdió la mejora al retirar grupos favorables y H1 original no. '
    note+='Se usaron exclusivamente predicciones y ámbitos guardados de 2023/2024, sin entrenar, recalibrar, inferir tasas fuente o reestimar C0.\n\n'
    note+='| Base guardada | Diferencia D² | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---:|---:|---:|\n'
    for name,row in a['source_safe_bases'].items():
        note+=f'| {name} | {row["delta"]:+.8f} | [{row["bootstrap95"][0]:+.8f}, {row["bootstrap95"][1]:+.8f}] | {row["post31_delta"]:+.8f} | {row["worst_cell_delta"]:+.8f} |\n'
    note+='\nS2 era la base principal preinscrita. Las tres mejoran en ambos años y los cinco folds, conservan dirección positiva bajo niveles fijos ±5%, '
    note+='y sus bandas simultáneas exploratorias de familia excluyen cero. Todas mantienen mejora post31 y pérdidas por celda menores que 0,001. '
    note+='Ninguna supera el mínimo formal de ganancia 0,002. No se modificó ese criterio.\n\n'
    aux=a['conditional_A1_2024']['A1']
    note+=f'El proxy A1 original2024 muestra diferencia {aux["delta"]:+.8f}, IC95[{aux["bootstrap95"][0]:+.8f},{aux["bootstrap95"][1]:+.8f}] y post31 {aux["post31_delta"]:+.8f}. '
    note+='Su linaje original de observación no acredita independencia por grupo. Es evidencia condicional, sin sustituir el F3c histórico completo ni asegurar la misma ganancia pública.\n\n'
    note+='| Escenario guardado, H1 frente a G3 | Diferencia D² | IC95 por grupos | Post31 |\n|---|---:|---:|---:|\n'
    for name,row in b['scenarios'].items():
        note+=f'| {name} | {row["delta"]:+.8f} | [{row["bootstrap95"][0]:+.8f}, {row["bootstrap95"][1]:+.8f}] | {row["post31_delta"]:+.8f} |\n'
    note+='\nSe reutilizaron los seis multiplicadores de observación ya calculados; no se repitió integración de CDF, estimación o controles de curvas. '
    note+='Las diferencias agrupadas y los límites inferiores marginales siguen positivos y post31 conserva signo positivo en todos. '
    note+='Nuevo negocio es exactamente igual al de PUL2 y conserva sus resultados adversos: autos nuevos2023 pierde -0,00490388 con revaloración75% y -0,00426495 con cola10%. '
    note+='La simplificación reduce concentración, pero no resuelve esas sensibilidades de reservas/reportes. Los escenarios no son verdad conocida de último.\n\n'
    note+='Se preparó un CSV de 209.063 filas con cinco miembros de precio F3c*H1/G3 y media aritmética, sin forma REN. '
    note+=f'Total redondeado {b["CSV"]["total_CU"]:,.6f} CU. Sus 158.980 filas NB son idénticas al prototipo PUL2 anterior. '
    note+='Las 50.083 REN cambian de distribución, conservando por miembro los totales sin redondear de PUL2; la diferencia global de 0,000098 CU tras redondear es aritmética. '
    note+='No se buscó un nivel nuevo en el leaderboard. El total continúa aproximadamente 1,758% por encima de F3c procesado.\n\n'
    note+='Pasaron las claves/orden oficiales, importes positivos, fórmula logarítmica independiente, redondeo racional y Decimal, readback y SHA de fuentes. '
    note+='La revisión de transferencia añadió invariancia ante perfiles desordenados por clave y recuperó H1 a partir de G3 sin repetir sus estadísticas. '
    note+='Estos controles certifican la aritmética revisada, no la calidad predictiva del futuro. Persisten el replay F3c completo ausente, la falta de validación anidada del ensemble '
    note+='y el ESS ponderado insuficiente. 2024 está abierto por instrucción directa y se trata como desarrollo adaptativo, sin confirmación intacta o revisión profesional independiente.\n\n'
    note+='La corrección H1 queda como alternativa de investigación más simple frente a PUL2. No hay promoción formal, nueva aprobación humana, envío o mejora pública verificada. '
    note+='Los indicadores de este diagnóstico conservan submission_allowed=false. El siguiente paso será una decisión separada y trazable de entrega de investigación: '
    note+='copia por SHA, dry run oficial y transporte idempotente con un máximo de un envío si los cupos reales lo permiten. '
    note+='La consulta vigente devolvió cero disponibles; no impide seguir preparando esa entrega. Se conservarán los fallos formales y las sensibilidades adversas en cualquier decisión.\n\n'
    note+='B00, F3c procesado0,16914, PUL2 y todas las alternativas se conservan; el objetivo público0,17 sigue activo. '
    note+='CSV: '+w.rel(csv)+'; SHA256 '+b['CSV']['sha256']+'. Evidencia: '+w.rel(TRANSFER/'report.json')+' y '+w.rel(OUT/'report.json')+'.\n'
    doc=R/'docs/semana2/MISION017_H1_SOLO_TRANSFERENCIA_Y_PROTOTIPO.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    body=OUT/'forum_resultados.md';body.write_text(note,encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
                             '--id','COD-S2-20261026-MISION017-H1-SOLO-RESULTADO',
                             '--asunto','H1 sola: transferencia y concentración más estables; persisten sensibilidad NB y límites de entrega',
                             '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt.update(document=w.rel(doc),forum=json.loads(response.stdout))
    for filename in ['semana2_transferencia_H1_solo_actual.json','semana2_H1_solo_prototipo_actual.json']:
        p=R/'registro'/filename;assert not p.exists();p.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    phase=R/'registro/semana2_mision017_fase2_actual.json'
    w.update(phase,{'utc':stamp.isoformat(),'H1_only_transfer_and_prototype':receipt,'next_unit':next_unit,'active_execution':None,'active_jobs':[]},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(H1_only_transfer_and_prototype=receipt,next_unit=next_unit,active_jobs=[],goal_achieved=False)
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_mission017_H1_only_transfer_index':w.rel(R/'registro/semana2_transferencia_H1_solo_actual.json'),
                                       'week_2_mission017_H1_only_prototype_index':w.rel(R/'registro/semana2_H1_solo_prototipo_actual.json'),
                                       'week_2_mission017_H1_only_report':w.rel(doc),'week_2_mission017_H1_only_unadmitted_CSV':w.rel(csv)},archive)
    for target in [OUT,TRANSFER]:(target/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'status':receipt['status'],'CSV':b['CSV'],'new_fits':0,'new_submissions':0,'2024_open':True,'forum':receipt['forum']}))


if __name__=='__main__':main()
