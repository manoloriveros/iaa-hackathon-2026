"""Cierra el corte de desarrollo 2023–2024 sin cerrar la misión 0,17."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
spec=importlib.util.spec_from_file_location('checkpoint',R/'herramientas/registrar_avance_mision017_fase2.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
OUT=R/'privado/semana2/mision017_fase2/tanda2_20261025_v1'
P=R/'registro/semana2_mision017_fase2_actual.json'
read=c.read;sha=c.sha;rel=c.rel


def main():
    report=OUT/'price_report.json';validation=OUT/'validation_v1/report.json';parent=OUT.parent/'linaje_T2b_v1/replay_report.json'
    a=read(report);v=read(validation);assert len(v['replays'])==15 and all(x['bit_exact'] for x in v['replays'])
    assert read(parent)['all_pass'] and not (OUT/'completion_receipt.json').exists()
    stamp=datetime.now(timezone.utc);archive=OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%SZ');archive.mkdir(parents=True)
    next_unit=('Preparar una comparación estándar de familia fuente sobre desarrollado 2021–2024, con CatBoost Tweedie y mezclas fijas frente a T2b. '
        'Primero revisar antecedentes CB y preparar variables comunes/fechas y unidades; 2024 está autorizado. '
        'Reutilizar las 15 curvas/mezclas C0 por ámbito de esta tanda para los grupos emergentes: no volver a ajustarlas ni remuestrear esta comparación. '
        'Congelar código/configuración/coste/criterio y foro antes del nuevo ajuste o score. '
        'No usar niveles derivados del leaderboard ni las sondas antiguas; conservar F2 y los cupos hasta una mejora local robusta. '
        'La fuente externa 2024 sirve para el ámbito de información al inicio de 2025, no para llamar prospectiva una validación de 2024.')
    current={'utc':stamp.isoformat(),'status':'completed_exploratory_batch','plan':rel(R/'registro/semana2_mision017_fase2_tanda2_plan_v1.json'),
        'output':rel(OUT),'price_report':rel(report),'price_report_sha256':sha(report),'validation':rel(validation),'validation_sha256':sha(validation),
        'scores':v['scores'],'exploratory_pass':[],'new_price_estimator_fits':0,'new_reporting_peril_fits':75,
        'closed_form_level_constants':105,'credibility_bucket_factors':140,'training_normalizers':40,'submissions':0,'execution':None}
    phase=read(P)
    c.update(P,{'utc':stamp.isoformat(),'status':'active','current_batch':current,'previous_batch':phase['current_batch'],
        'parent_F2_replay':{'report':rel(parent),'sha256':sha(parent),'source_author':'Claude','review_author':'Codex','passed':True},
        'new_price_fits':12,'new_C0_fits':90,'new_emerging_C0_fits':75,'new_source_C0_fits':15,
        'new_closed_form_levels':111,'new_bucket_factors':140,'new_bucket_normalizers':40,'new_submissions':0,
        'next_unit':next_unit,'2024_open':True,'2024_closed':False,'2024_is_development':True,'goal_achieved':False},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json'
    c.update(state,{'week_2_mission017_phase2_20261025':{'status':'active','phase':rel(P),'current_batch':current,
        '2024_open':True,'2024_closed':False,'goal_achieved':False,'next_unit':next_unit}},archive)
    counter=R/'registro/semana2_contadores_propios_actual.json';x=read(counter);assert 'phase2_2024_tanda2' not in x
    c.update(counter,{'as_of_utc':stamp.isoformat(),
        'cumulative_closed_form_constants':x['cumulative_closed_form_constants']+105,
        'supplementary_reporting_peril_fits_since_counter_start':x['supplementary_reporting_peril_fits_since_counter_start']+75,
        'mixture_frequency_constants_since_counter_start_separate':x['mixture_frequency_constants_since_counter_start_separate']+75,
        'mixture_positive_severity_means_since_counter_start_separate':x['mixture_positive_severity_means_since_counter_start_separate']+225,
        'phase2_2024_tanda2':{'price_estimator_fits':0,'reporting_peril_fits':75,'frequency_constants':75,
            'weighted_mark_means_3reserve_branches':225,'normalized_scope_mixtures':15,'closed_form_price_levels':105,
            'bucket_factors':140,'training_normalizers':40,'receipt':rel(validation),'sha256':sha(validation)}},archive)
    scores=v['scores'];z=v['comparisons']['N3']
    note=f'''\n\n## Dos años emergentes con C0 y credibilidad por componentes, 25 de octubre de 2026 (Bogotá)

Codex, {stamp.isoformat()}. 2024 permanece abierto por la instrucción humana más reciente. La misión 0,17 sigue activa y no depende del cierre antiguo que conserva el texto del tool de objetivos. B00, F2 y todas las alternativas siguen conservados; no se gastó ningún envío.

El padre T2b de F2, autor Claude, se reconstruyó con sus variables históricas: las 109.296 filas de 2023–2024 reproducen las predicciones guardadas salvo un factor constante por antiguo fold, con desviación relativa máxima 4,44e-16. No se entrenó ni puntuó en ese replay. La fuente incluye desarrollado hasta 2024; es información disponible al inicio de 2025, no una predicción prospectiva del año 2024.

La nueva comparación usa los folds guardados por componentes cliente-dirección de ambos años. Todos los objetos de reporte, marcas, mezcla, factores por bandas y niveles se aprenden excluyendo el componente retenido. D² local OOF: N0={scores['N0']:.6f}, N1={scores['N1']:.6f}, N2={scores['N2']:.6f}, N3={scores['N3']:.6f}. N1 añade la corrección relativa NCB/previos con credibilidad 300; N2 contrae el nivel por negocio con credibilidad 400; N3 combina ambas.

N3 mejora {z['delta']:+.6f} frente a N0 y gana en cinco folds y en ambos años. Su IC95 individual por componentes es [{z['bootstrap95'][0]:+.6f}, {z['bootstrap95'][1]:+.6f}], pero el intervalo simultáneo de las tres comparaciones incluye cero. La mejora no alcanza el mínimo preinscrito de 0,002 y pasa a {z['after_remove31_delta']:+.6f} al retirar los 31 grupos más favorables. Ninguna alternativa cumple todos los criterios. Se conserva el resultado adverso y no se promueve un modelo por esa cifra.

Los quince ámbitos reales se reprodujeron exactamente, con ajuste bloqueado, y alterar costes retenidos no cambió las predicciones. Se cotejó que cada ámbito contiene solo las filas y los siniestros de los componentes permitidos. Una prueba sintética anterior también verificó la invariancia de todo el aprendizaje frente a cambios de costes/perils protegidos. La métrica se contrastó con scikit-learn. Son verificaciones propias, no revisión profesional independiente.

Esta tanda añade 75 curvas de reporte, 105 constantes de nivel, 140 factores por bandas y 40 normalizadores aprendidos en entrenamiento; cero ajustes de nuevos estimadores de precio y cero envíos. No se vuelve a ajustar C0 para la próxima comparación si sus fuentes y ámbitos son los mismos. Continúan las limitaciones de la valoración única a diciembre de 2024, maestros sin fecha, cola no observada y suficiencia de reservas. La marca pública del equipo sigue en 0,16033, todavía por debajo de 0,17.

Próxima unidad: {next_unit}

Evidencia: {rel(validation)}. Plan congelado: {current['plan']}. Índice vigente: {rel(P)}.
'''
    for n in ['MEMORIA_PROYECTO.md','DECISIONES.md']:c.append(ROOT/'Preparación'/n,note,archive)
    doc=R/'docs/archivo/semana2/MISION017_FASE2_TANDA2_2023_2024.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
    body=OUT/'forum_resultado.md';body.write_text(note,encoding='utf8')
    p=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261025-MISION017-FASE2-TANDA2-RESULTADO','--asunto','Correcciones con dos años: mejora pequeña y aún concentrada; sin envíos','--cuerpo',str(body)],
        check=True,capture_output=True,text=True,encoding='utf8')
    receipt={'utc':stamp.isoformat(),'forum':json.loads(p.stdout),'current_batch':current,'next_unit':next_unit,'goal_status':'active','2024_open':True}
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'registered':True,'forum':receipt['forum'],'2024_open':True,'goal_status':'active','new_submissions':0,'all_candidates_failed_exploratory_admission':True}))


if __name__=='__main__':main()
