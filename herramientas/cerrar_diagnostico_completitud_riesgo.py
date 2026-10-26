"""Documenta el diagnóstico de observación, sin nuevos cálculos predictivos."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
OUT=R/'privado/semana2/mision017_fase2/completitud_por_riesgo_diagnostico_20261026_v2'
sp=importlib.util.spec_from_file_location('completion_diagnostic_closure',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w);sys.stdout.reconfigure(encoding='utf8')


def main():
    assert not (OUT/'completion_receipt.json').exists()
    report=w.read(OUT/'report.json');assert len(report['numeric_controls'])==15
    stamp=datetime.now(timezone.utc);archive=OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ');archive.mkdir(parents=True)
    next_unit='Prepare HET standard observation-link comparison on2023/2024: primary saved-outer-kappa risk mix, source-only risk mix as fixed ablation. Apply SAMEouter profile to its training and held rows; never merge held q from otherfolds into training. Reuse C0curves and FSp models, same N3/G3closed shape/level/factor rules, no new capacity. Synthetic whole-flow/maturity/ancestry invariance; freeze recipe/budget/criterion and forum before any new calibration or score.2024open;B00/F3c0.16914and slots preserved.'
    receipt={'author':'Codex','utc':stamp.isoformat(),'status':'completion_profile_diagnostic_complete_no_adoption',
        'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'rows':109296,
        'material_fold_profile_cells':39,'total_fold_profile_cells':120,'new_model_fits':0,'new_C0_fits':0,
        'new_calibrations':0,'new_scores':0,'new_submissions':0,'reused_v1_scopes':8,'new_v2_scopes':7,
        '2024_open':True,'goal_achieved':False,'next_unit':next_unit}
    index=R/'registro/semana2_completitud_por_riesgo_actual.json';assert not index.exists()
    index.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    phase=R/'registro/semana2_mision017_fase2_actual.json'
    w.update(phase,{'utc':stamp.isoformat(),'risk_completion_diagnostic':receipt,'next_unit':next_unit,'active_execution':None,'active_jobs':[]},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(risk_completion_diagnostic=receipt,next_unit=next_unit,active_jobs=[],goal_achieved=False)
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    note='\n\n## Mezcla de perils y completitud por riesgo, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. Se revisaron los 109.296 periodos retenidos de 2023/2024, por los cinco folds guardados. '
    note+='Se comparó el enlace global con perfiles f*s de fuente y, aparte, kappa*f*s exterior ya guardado. Cero ajustes, C0, momentos, inferencias, precios o scores nuevos. '
    note+='39 de 120 celdas de fold/perfil/ramo/año/negocio superan el filtro descriptivo preinscrito. Esas celdas están relacionadas y no son 120 observaciones independientes.\n\n'
    note+='Al reunir los cinco folds de 2024, la fracción con diferencia multiplicativa de completitud mayor de 1,05 es 57,29% (fuente) y 62,20% (perfil exterior) en autos nuevos; '
    note+='38,17% y 27,60% en edificios nuevos. En renovaciones de autos es 32,92% y 34,79%. Contenidos muestra diferencias mucho menores; 2023 está casi completamente desarrollado bajo estas curvas. '
    note+='Esto documenta una posible limitación de la mezcla global; no demuestra que los perfiles FSp representen el verdadero coste de último ni que una exposición nueva mejore la predicción.\n\n'
    note+='La primera versión falló al exigir q>0 para cada peril: una fila retenida de subsidencia tiene q=0 legítimo. '
    note+='Se conservan el fallo, código y ocho ámbitos completos; v2 admite q=0 con log(0)=-infinito y solo completa siete ámbitos. No se ponen mínimos o se cambian curvas. '
    note+='Se comprobó membresía exterior exacta, independencia por grupo, mezcla global, log-sum-exp y las identidades de escala/completitud. '
    note+='La función de perfiles ignora costes, reservas y recuentos observados; los controles alterados lo comprobaron.\n\n'
    note+='El siguiente contraste mantendrá T0, árboles fuente y reglas de corrección estándar. Cambiará únicamente el enlace de observación: perfil exterior como primario y fuente sola como ablation declarada. '
    note+='Cada perfil exterior debe aplicarse a todas las filas de su propio ámbito. Usar para entrenamiento el vector OOF de otros folds introduciría ancestros protegidos; queda expresamente excluido. '
    note+='Antes de nuevas calibraciones o scores se preparará el flujo, se verificará con datos sintéticos y se congelará receta, coste y criterio en el foro. '
    note+='En la predicción de último de 2025, la completitud es 1 por definición del objetivo, no la completitud observada al corte de 2024. Esto se comprobará en el adaptador futuro, sin generar precios ahora.\n\n'
    note+='Persisten los límites de cola, reservas, maestros sin fecha y del proxy de coste f*s.2024 sigue abierto y adaptativo. '
    note+='B00, F3c 0,16914 y alternativas intactos; ningún cupo consumido y objetivo 0,17 activo. Evidencia: '+w.rel(OUT/'report.json')+'.\n'
    doc=R/'docs/semana2/MISION017_COMPLETITUD_POR_RIESGO_DIAGNOSTICO.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    body=OUT/'forum_resultados.md';body.write_text(note,encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-COMPLETITUD-RIESGO-RESULTADO','--asunto','Completitud por riesgo: variación relevante, sin prueba de mejora aún',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt.update(document=w.rel(doc),forum=json.loads(response.stdout))
    w.update(index,receipt,archive/'post_forum');w.update(phase,{'risk_completion_diagnostic':receipt},archive/'post_forum')
    own=w.read(state)['week_2_mission017_phase2_20261025'];own['risk_completion_diagnostic']=receipt
    w.update(state,{'week_2_mission017_phase2_20261025':own},archive/'post_forum')
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_mission017_risk_completion_diagnostic_index':w.rel(index),
        'week_2_mission017_risk_completion_diagnostic_report':w.rel(doc)},archive/'post_forum')
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(receipt,ensure_ascii=True))


if __name__=='__main__':main()
