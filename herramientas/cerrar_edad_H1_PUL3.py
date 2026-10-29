"""Guarda el ensayo adverso y prepara un prototipo distinto, sin enviarlo."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
OUT=R/'privado/semana2/mision017_fase2/edad_H1_PUL3_20261026_v1'
sp=importlib.util.spec_from_file_location('AGEH1_closure_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w);sys.stdout.reconfigure(encoding='utf8')


def main():
    assert not (OUT/'completion_receipt.json').exists()
    result=w.read(OUT/'report.json');assert len(list(OUT.glob('model_*.json')))==15
    assert len(result['numeric_controls'])==15
    stamp=datetime.now(timezone.utc);archive=OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ');archive.mkdir(parents=True)
    next_unit='Prepare concrete2025PUL2correction prototype relative to actualF3c, with all five frozen outer calibrations and sameRENweights; no age or newfit. First inventory/cache2025T2bREN/NBrates and needed covariates, define source/target lineage and ensemble/normalization before inference. ProductionQAand actual price/level/cohort shifts, not a claim failed post31passed. Freeze recipe/cost/forum before predictions. No upload: separate admission/research decision still unestablished;2024open,B00/F3c/alternatives preserved.'
    receipt={'author':'Codex','utc':stamp.isoformat(),'status':'complete_adverse_NB_rejected','report':w.rel(OUT/'report.json'),
        'report_sha256':w.sha(OUT/'report.json'),'new_real_GLM_fits':15,'synthetic_optimizer_fits':0,
        'new_C0_fits':0,'new_source_fits':0,'new_kappa_fits':0,'new_final_test_prices':0,'new_submissions':0,
        'combined':{k:result['combined'][k] for k in ['scores','delta_vs_G3','bootstrap95','gates','weighted2025_sensitivity_delta']},
        'NB_delta':result['NB_increment']['delta'],'NB_bootstrap95':result['NB_increment']['paired_bootstrap95'],
        'NB_guards':result['NB_increment']['guards'],'weighted_NB_increment':result['weighted_NB_increment'],
        'additional_vetoes':result['additional_vetoes'],'formal_admission':False,'submission_allowed':False,
        '2024_open':True,'goal_achieved':False,'B00_all_alternatives_preserved':True,'next_unit':next_unit}
    cp=R/'registro/semana2_contadores_propios_actual.json';counter=w.read(cp);assert 'phase2_AGEH1_PUL3' not in counter
    w.update(cp,{'as_of_utc':stamp.isoformat(),'cumulative_price_base_fits':counter['cumulative_price_base_fits']+15,
                 'phase2_AGEH1_PUL3':receipt},archive)
    phase=R/'registro/semana2_mision017_fase2_actual.json';p=w.read(phase)
    w.update(phase,{'utc':stamp.isoformat(),'AGEH1_PUL3':receipt,'new_price_fits':p['new_price_fits']+15,
                    'next_unit':next_unit,'active_execution':None,'active_jobs':[],'2024_open':True,'2024_closed':False},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(AGEH1_PUL3=receipt,next_unit=next_unit,active_jobs=[],goal_achieved=False)
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    note='\n\n## AGEH1/PUL3: la edad NB vuelve a fallar, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. Se completaron los 15 GLM preinscritos con el motor de edad sin cambios, cinco bandas y K300, ahora sobre H1. '
    note+='La conexión nueva cotejó ámbitos, ancestros y replay H1 separado en entrenamiento/retenido; no se mezclaron precios OOF de otros folds. '
    note+='No se repitió la suite del optimizador sin cambios: su código/fixture se comprobaron por hash; se probaron las rutas nuevas sin ajustar.\n\n'
    nb=result['NB_increment'];full=result['combined']
    note+=f'Incremento NB frente a H1/PUL2: {nb["delta"]:+.8f}; IC95 pareado [{nb["paired_bootstrap95"][0]:+.8f}, {nb["paired_bootstrap95"][1]:+.8f}]. '
    note+='Empeora en los cinco folds y los dos años; fallan todas las guardas NB. '
    note+=f'Sensibilidad ponderada del incremento NB: {result["weighted_NB_increment"]:+.8f}. '
    note+=f'Proxy A1 original de 2024 para edad NB sola: {result["A1_original_2024_age_only_NB_proxy"]:+.8f}; el proxy de razón completa es {result["A1_original_2024_full_ratio_proxy"]:+.8f}. '
    note+='El segundo es positivo por otros componentes y no rescata el daño NB. Los proxies no son F3c corregido completo y el ESS sigue siendo insuficiente.\n\n'
    note+=f'PUL3 combinado: D² {full["scores"]["PUL3"]:.8f}, diferencia frente a G3 {full["delta_vs_G3"]:+.8f}; conserva la concentración y empeora una celda. '
    note+='REN permaneció exactamente PUL2. Ninguna ganancia REN se usa para aprobar la edad. Se conserva PUL3 como adverso, sin elegir nuevas bandas o K.\n\n'
    note+='Los 15 ajustes pasaron objetivo/onehot/gradiente/Hessiano independientes, problema numérico idéntico bajo etiquetas retenidas alteradas y replay exacto con optimizador bloqueado. '
    note+='Coste real: 15 GLM nuevos, cero modelos fuente, C0, kappas, inferencias fuente, precios finales o envíos. '
    note+='Los coeficientes y dos interceptos de cada GLM son parámetros dentro de esos modelos, no nuevas constantes cerradas independientes para sumarlas otra vez.\n\n'
    note+='La siguiente unidad preparará un prototipo concreto PUL2 de 2025 respecto de F3c, sin edad ni más ajuste, para verificar el flujo real y medir cambios de nivel/cartera. '
    note+='No implica superar post31, admisión estadística o permiso nuevo de envío. Se distinguirá la media de cinco miembros de la validación OOF de un solo ámbito y la transferencia a F3c del comparador local G3. '
    note+='Antes de inferir se registrarán fórmula, normalización, fuentes y coste; el productor no tendrá una vía de upload.\n\n'
    note+='B00, F3c 0,16914, PUL2 y todos los adversos conservados.2024 abierto y adaptativo. Ningún cupo consumido; meta pública 0,17 activa. '
    note+='Evidencia: '+w.rel(OUT/'report.json')+'.\n'
    doc=R/'docs/archivo/semana2/MISION017_AGEH1_PUL3_RESULTADO.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    body=OUT/'forum_resultados.md';body.write_text(note,encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-AGEH1-PUL3-RESULTADO','--asunto','AGEH1 deteriora NB en cinco folds; se prepara producción PUL2 sin edad',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt.update(document=w.rel(doc),forum=json.loads(response.stdout))
    w.update(phase,{'AGEH1_PUL3':receipt},archive/'post_forum')
    own=w.read(state)['week_2_mission017_phase2_20261025'];own['AGEH1_PUL3']=receipt
    w.update(state,{'week_2_mission017_phase2_20261025':own},archive/'post_forum')
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_mission017_AGEH1_PUL3_report':w.rel(doc)},archive/'post_forum')
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'status':receipt['status'],'NB_delta':receipt['NB_delta'],'NB_bootstrap95':receipt['NB_bootstrap95'],'forum':receipt['forum']},ensure_ascii=True))


if __name__=='__main__':main()
