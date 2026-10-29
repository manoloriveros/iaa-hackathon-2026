"""Registra resultados nuevos A1S sin repetir ajustes, inferencias o estadística."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';HOME=BASE/'A1S_nucleo_20261026_v1'
SOURCE=HOME/'source_models';TARGET=HOME/'target_complete_core'
PHASE=R/'registro/semana2_mision017_fase2_actual.json'
INDEX=R/'registro/semana2_mision017_A1S_actual.json'
COUNTER=R/'registro/semana2_contadores_propios_actual.json'
spec=importlib.util.spec_from_file_location('close_A1S_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
sys.stdout.reconfigure(encoding='utf8')


def main():
    assert not (HOME/'completion_receipt.json').exists()
    sr=w.read(SOURCE/'report.json');tr=w.read(TARGET/'report.json')
    assert sr['new_source_model_fits']==18 and len(sr['records'])==18
    assert tr['new_iterative_fits']==0 and tr['new_C0_fits']==0
    assert len(tr['numeric_controls'])==15
    stamp=datetime.now(timezone.utc);archive=HOME/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ')
    archive.mkdir(parents=True)
    score=tr['scores']; delta=tr['primary_delta_vs_G3'];ci=tr['primary_bootstrap95']
    gates=tr['gates'];passed=all(gates.values())
    next_unit=('Review the full-core S2 scope evidence and remaining deployment differences before a separately registered2025refit/delivery. '
               'No automatic upload or formal promotion; retain actual F3c0.16914and quota.') if passed else (
               'Use this completed adverse full-core result to identify a concrete unresolved failure before another recipe. '
               'Do not repeat A1Sfits/calibration/bootstrap or tune seeds, weights, bands or rules to held losses; retain F3c0.16914and quota.')
    receipt={'author':'Codex','utc':stamp.isoformat(),
             'status':'source_and_complete_target_comparison_finished_exploratory',
             'source_report':w.rel(SOURCE/'report.json'),'source_report_sha256':w.sha(SOURCE/'report.json'),
             'target_report':w.rel(TARGET/'report.json'),'target_report_sha256':w.sha(TARGET/'report.json'),
             'new_model_fits':18,'source_internal_fits':9,'source_full_refits':9,'new_scores':3,'new_target_scores':3,
             'new_C0_fits':0,'new_final_test_prices':0,'new_submissions':0,
             'scores':score,'delta_vs_G3':delta,'bootstrap95':ci,'gates':gates,
             'exploratory_gates_pass':passed,'formal_admission':False,'submission_allowed':False,
             '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,
             'unique_primary_learning_constants':tr['unique_primary_learning_constants'],
             'next_unit':next_unit}
    constants=tr['unique_primary_learning_constants']
    learned=sum(constants[k] for k in ['shape_factors','component_levels','residual_factors','residual_nuisance_levels'])
    counter=w.read(COUNTER)
    assert 'phase2_A1S_complete_target' not in counter
    assert counter['phase2_A1S_source']['attempts']==18 and counter['phase2_A1S_source']['completed']==18
    w.update(COUNTER,{'as_of_utc':stamp.isoformat(),
        'cumulative_closed_form_constants':counter['cumulative_closed_form_constants']+learned,
        'phase2_A1S_complete_target':{'unique_learned_price_constants':learned,
            'breakdown':constants,'control_recomputation_same_constants_separate':constants,
            'new_iterative_fits':0,'new_C0_fits':0,'report':w.rel(TARGET/'report.json'),
            'report_sha256':w.sha(TARGET/'report.json')}},archive)
    phase=w.read(PHASE)
    w.update(PHASE,{'utc':stamp.isoformat(),'A1S_core':receipt,'active_execution':None,'active_jobs':[],
                    'next_unit':next_unit,'2024_open':True,'2024_closed':False},archive)
    w.update(INDEX,receipt,archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json'
    own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(utc=stamp.isoformat(),A1S_core=receipt,next_unit=next_unit,active_jobs=[],goal_achieved=False)
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    note='\n\n## A1S: núcleo guardado y contraste completo por grupos, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. Se completaron los 18 ajustes fuente previstos (9 internos y 9 refits) con tres semillas fijas por ramo. '
    note+='Partición fuente por 476.444 componentes cliente/dirección, máximo 37 filas; modelos y componentes guardados. '
    note+='Las rondas se eligieron solo en fuente. No hubo curvas/C0 nuevos, entrenamiento emergente iterativo, precios finales de 2025 o envíos. '
    note+='A1S es alternativa nueva explícita con enlace aprendido solo en fuente e historia limitada al corte, no reproducción exacta ni certificación del A1 legado.\n\n'
    note+='La calibración y aplicación completas excluyen los grupos emergentes retenidos; los 15 ámbitos pasaron alteración de T0/reservas retenidos y replay exacto con aprendizaje bloqueado. '
    note+='C0 exterior se reutilizó con membresía cotejada. La pérdida se cotejó con sklearn; los niveles, por momento y derivada independientes. '
    note+='La etapa fuente pasó reproducción desde archivo, orden y suma de hojas independiente.\n\n'
    note+='D² local de desarrollo 2023–2024: '+', '.join(f'{name} {value:.8f}' for name,value in score.items())+'. '
    note+=f'El primario S2 frente a G3 cambia {delta:+.8f}; IC95 por componentes [{ci[0]:+.8f}, {ci[1]:+.8f}]. '
    note+='S0 es A1S calibrado; S1 su mezcla aritmética fija 50/50 con N3/T2b; S2 añade las correcciones residuales estándar. '
    note+='S0/S1 son ablaciones declaradas antes de puntuar, sin selección posterior de ganador.\n\n'
    note+='Contribuciones por fold: '+json.dumps(tr['fold_contributions'],ensure_ascii=False)+'. '
    note+='Por año: '+json.dumps(tr['year_contributions'],ensure_ascii=False)+'. '
    note+=f'Tras quitar los 31 grupos más favorables, diferencia {tr["post31_delta"]:+.8f}. '
    note+=f'Sensibilidad ponderada a cartera 2025: {tr["weighted2025_sensitivity_delta"]:+.8f}; el ESS previamente fallido sigue impidiendo interpretarla como confirmación fiable. '
    note+='Criterios cumplidos: '+', '.join(k for k,v in gates.items() if v)+'. '
    note+='Fallos: '+(', '.join(k for k,v in gates.items() if not v) or 'ninguno de los umbrales exploratorios de este contraste')+'.\n\n'
    note+='No se compara directamente con F3c completo porque faltan los artefactos A1 corregidos históricos; una ganancia frente a G3 no equivale a mejora pública. '
    note+='2024 está abierto y es desarrollo adaptativo; los maestros sin fecha, el corte único, cola y reservas siguen condicionando la interpretación. '
    note+='La selección interna fuente condiciona el enlace de observación ya aprendido con toda la fuente. Revisión propia exploratoria tras búsqueda adaptativa, sin aprobación humana o validación profesional independiente. '
    note+='B00, F3c (0,16914) y todas las alternativas/adversos intactos. Meta pública 0,17 activa.\n\n'
    note+='Contabilidad nueva de esta unidad: 18 ajustes fuente ya anotados por invocación; '+str(learned)+' constantes de precio cerradas únicas, con normalizadores y recomputaciones adversas separados en el informe. '
    note+='Evidencia: '+w.rel(SOURCE/'report.json')+'; '+w.rel(TARGET/'report.json')+'.\n\nSiguiente unidad: '+next_unit+'\n'
    doc=R/'docs/archivo/semana2/MISION017_A1S_NUCLEO_COMPLETO_RESULTADO.md'
    assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
        w.append(ROOT/'Preparación'/name,note,archive)
    body=HOME/'forum_resultados.md';body.write_text(note,encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor','Codex','--id','COD-S2-20261026-MISION017-A1S-COMPLETO-RESULTADO',
        '--asunto','A1S: resultados del núcleo completo y límites de validación',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt.update(document=w.rel(doc),document_sha256=w.sha(doc),forum=json.loads(response.stdout))
    # Preserve all fields already written and add the forum receipt, without re-counting.
    for path,key in [(INDEX,None),(PHASE,'A1S_core')]:
        if key is None:w.update(path,receipt,archive/'post_forum')
        else:w.update(path,{key:receipt},archive/'post_forum')
    state_own=w.read(state)['week_2_mission017_phase2_20261025'];state_own['A1S_core']=receipt
    w.update(state,{'week_2_mission017_phase2_20261025':state_own},archive/'post_forum')
    (HOME/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:receipt[k] for k in ['status','scores','delta_vs_G3','bootstrap95','gates','forum','next_unit']},ensure_ascii=True))


if __name__=='__main__':main()
