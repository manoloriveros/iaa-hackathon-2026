"""Cierre documental de un ensayo GLM, sin repetir aprendizaje o diagnósticos."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
OUT=R/'privado/semana2/mision017_fase2/GLM_discrepancia_A1S_20261026_v1'
sp=importlib.util.spec_from_file_location('close_disagreement_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w)
sys.stdout.reconfigure(encoding='utf8')


def main():
    assert not (OUT/'completion_receipt.json').exists()
    result=w.read(OUT/'report.json');assert result['new_real_GLM_fits']==15
    models=sorted(OUT.glob('model_*.json'));assert len(models)==15
    stamp=datetime.now(timezone.utc);archive=OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ')
    archive.mkdir(parents=True)
    next_unit=('Keep this completed result without repeating source A1S fits, mixture calibration, GLM, bootstrap or tuning K/weights on held losses. '
               'Review a distinct, documented uncertainty or new legitimate source before registering another finite standard-model trial. '
               'Preserve F3c0.16914/B00;2024open; no slot consumed and public0.17goal remains active.')
    receipt={'author':'Codex','utc':stamp.isoformat(),'status':'complete_exploratory_no_admission',
             'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
             'new_real_GLM_fits':15,'new_C0_fits':0,'new_source_fits':0,'synthetic_fits_separate':3,
             'slopes':30,'nuisance_intercepts':60,'new_final_test_prices':0,'new_submissions':0,
             'scores':result['scores'],'delta_vs_G3':result['delta_vs_G3'],'bootstrap95':result['bootstrap95'],
             'gates':result['gates'],'formal_admission':False,'submission_allowed':False,
             '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,'next_unit':next_unit}
    cp=R/'registro/semana2_contadores_propios_actual.json';counter=w.read(cp)
    assert 'phase2_GLM_discrepancy_A1S' not in counter
    w.update(cp,{'as_of_utc':stamp.isoformat(),
                 'cumulative_price_base_fits':counter['cumulative_price_base_fits']+15,
                 'phase2_GLM_discrepancy_A1S':receipt},archive)
    phase=R/'registro/semana2_mision017_fase2_actual.json';p=w.read(phase)
    w.update(phase,{'utc':stamp.isoformat(),'GLM_discrepancy_A1S':receipt,
                     'new_price_fits':p['new_price_fits']+15,'active_execution':None,'active_jobs':[],
                     'next_unit':next_unit,'2024_open':True,'2024_closed':False},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(GLM_discrepancy_A1S=receipt,next_unit=next_unit,active_jobs=[],goal_achieved=False)
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    slopes={line:[{'fold':j,'REN':w.read(OUT/f'model_{line}_fold{j}.json')['coef'][0],
                    'NB':w.read(OUT/f'model_{line}_fold{j}.json')['coef'][1]} for j in range(5)]
            for line in ['motor','buildings','contents']}
    (OUT/'coefficient_summary.json').write_text(json.dumps(slopes,ensure_ascii=False,indent=2),encoding='utf8')
    note='\n\n## GLM de discrepancia A1S/T2b: resultado adverso, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. Se completaron los 15 GLM Tweedie estándar preinscritos, con dos pendientes de discrepancia fuente por negocio y cuatro interceptos de año/negocio no transferidos. '
    note+='K=300 fijo, offset G3 guardado, sin modelos fuente, inferencias fuente o C0 nuevos. Se preservan B00, los 18 modelos A1S y todas las alternativas.\n\n'
    note+=f'D² de desarrollo 2023–2024: D1 {result["scores"]["D1"]:.8f}, frente a G3 {result["scores"]["G3"]:.8f}. '
    note+=f'Diferencia {result["delta_vs_G3"]:+.8f}; IC95 por componentes [{result["bootstrap95"][0]:+.8f}, {result["bootstrap95"][1]:+.8f}]. '
    note+='Los cinco folds y los dos años empeoran. Fallan los seis umbrales exploratorios; no se adopta ni se prepara entrega de este cambio. '
    note+=f'Tras quitar los 31 grupos más favorables: {result["post31_delta"]:+.8f}; sensibilidad ponderada de cartera 2025: {result["weighted2025_sensitivity_delta"]:+.8f}, condicionada por el ESS previamente insuficiente.\n\n'
    note+='El problema numérico completo (diseño, respuestas, offset, regularización e inicialización) fue idéntico tras alterar T0/reservas retenidos en los 15 ámbitos. '
    note+='Pasaron la función objetivo por sklearn, diferencias finitas de gradiente/Hessiano y replay exacto con el optimizador bloqueado. Los tres ajustes sintéticos están contados aparte. '
    note+='La corrección de autos cambia de signo entre folds para ambos negocios; la de renovaciones de edificios también. Contenidos muestra signo positivo estable, insuficiente para justificar recortar después los demás ramos. '
    note+='Coeficientes guardados, sin nuevo ajuste: '+w.rel(OUT/'coefficient_summary.json')+'.\n\n'
    note+='No se afina K ni se elige un subconjunto por este resultado. La familia de mezcla A1S queda documentada y conservada; se cambia de mecanismo de investigación. '
    note+='2024 permanece abierto y adaptativo. Falta el comparador histórico completo F3c; se mantienen las limitaciones de maestros sin fecha, reporte tardío, cola y reservas. '
    note+='Sin precios finales de 2025, envíos o cupos consumidos. Mejor público procesado 0,16914; meta 0,17 activa, sin promesa de éxito ni aprobación independiente.\n\n'
    note+='Evidencia: '+w.rel(OUT/'report.json')+'. Siguiente unidad: '+next_unit+'\n'
    doc=R/'docs/semana2/MISION017_GLM_DISCREPANCIA_A1S_RESULTADO.md'
    assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    body=OUT/'forum_resultados.md';body.write_text(note,encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-GLM-DISCREPANCIA-A1S-RESULTADO',
        '--asunto','GLM A1S/T2b: deterioro en cinco folds, se conserva la referencia',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt.update(document=w.rel(doc),document_sha256=w.sha(doc),forum=json.loads(response.stdout))
    w.update(phase,{'GLM_discrepancy_A1S':receipt},archive/'post_forum')
    own=w.read(state)['week_2_mission017_phase2_20261025'];own['GLM_discrepancy_A1S']=receipt
    w.update(state,{'week_2_mission017_phase2_20261025':own},archive/'post_forum')
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:receipt[k] for k in ['status','scores','delta_vs_G3','bootstrap95','forum']},ensure_ascii=True))


if __name__=='__main__':main()
