"""Cierra la revisión y actualiza memoria; el catálogo preparado queda intacto."""
from datetime import datetime,timezone
from pathlib import Path
import json
import re
import shutil
import sys

import review_pending as r
import clean_data as c


def main(out):
    assert '--figures-inspected' in sys.argv,'Inspeccionar realmente las dos figuras antes del cierre.'
    assert not (out/'manifest.json').exists(),'Corrida cerrada; no sobrescribir.'
    s=json.loads((out/'summary.json').read_text('utf-8'));v=json.loads((out/'verification.json').read_text('utf-8'))
    ui=json.loads((out/'interface_verification.json').read_text('utf-8'))
    protected=json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    assert v['failed']==ui['failed']==0 and ui['all_1454_rows_exercised']
    assert all(c.digest(c.ROOT/p)==sha for p,sha in protected.items())
    assert s['pending_rows_after_review']==1454 and s['original_values_changed']==0 and not s['active_dataset_changed']
    for name in ['review_pending.py','interpret_pending.py','render_pending.py','verify_pending.py','verify_report.js','record_pending.py']:
        source=r.BASE/name;dest=out/'source_snapshot'/name
        if dest.exists():assert c.digest(dest)==c.digest(source)
        else:shutil.copy2(source,dest)
    shutil.copy2(c.BASE/'clean_data.py',out/'source_snapshot/clean_data.py')
    for name in ['README.md','PRACTICAS_PRIORITARIAS.md']:
        shutil.copy2(c.ROOT/'Preparación/Antecedentes/IAA_IA'/name,out/'evidence'/('IAA_'+name))
    c.dump(out/'figure_inspection.json',{'status':'visually_inspected_by_Codex','figures':[
        {'file':'figures/cohort.png','sha256':c.digest(out/'figures/cohort.png'),'finding':'Seven exclusive groups and year counts are legible; labels/totals fit.'},
        {'file':'figures/histories.png','sha256':c.digest(out/'figures/histories.png'),'finding':'Six real histories show original, current and hypothetical values; log axes and legend are legible.'}],
        'method':'view_image of both actual saved PNG files','real_browser_rendering':False,'independent_validation':False})
    now=datetime.now(timezone.utc).isoformat();rel=out.relative_to(c.ROOT).as_posix()
    paths={name:c.ROOT/'Preparación'/name for name in ['ESTADO_PROYECTO.json','MEMORIA_PROYECTO.md','DECISIONES.md']}
    paths.update({'RUTAS_PROYECTO.json':c.ROOT/'RUTAS_PROYECTO.json',
                  'capital_review_README.md':c.ROOT/'Hackaton/Semana 1/Revision_capitales/README.md'})
    close=r.BASE/'closures'/datetime.now(timezone.utc).strftime('closure_%Y%m%dT%H%M%SZ')
    close.mkdir(parents=True,exist_ok=False)
    for name,p in paths.items():shutil.copy2(p,close/('before_'+name))
    state=json.loads(paths['ESTADO_PROYECTO.json'].read_text('utf-8'))
    decisions=paths['DECISIONES.md'].read_text('utf-8');memory=paths['MEMORIA_PROYECTO.md'].read_text('utf-8')
    routes=json.loads(paths['RUTAS_PROYECTO.json'].read_text('utf-8'))
    decision='D'+str(max(map(int,re.findall(r'\bD(\d+)\b',decisions)))+1)
    record={'decision_id':decision,'status':'verified_review_only_no_data_changes','run':'../'+rel,
        'report':'../'+rel+'/informe.html','proposal':'../'+rel+'/proposal.json',
        'assessment':'../'+rel+'/tables/pending_assessment.parquet','assessment_csv':'../'+rel+'/tables/pending_assessment.csv',
        'proposed_retrospective_scenario_NOT_APPLIED':'../'+rel+'/tables/proposed_retrospective_scenario_NOT_APPLIED.parquet',
        'verification':'../'+rel+'/verification.json','index':'../Hackaton/Semana 1/Revision_capitales_pendientes/current_run.json',
        'frozen_pending_rows':1454,'policies':1452,'buildings_rows':691,'contents_rows':763,
        'policy_history_rows':5587,'claim_history_rows':128,'original_reference_pairs':4130,'example_policies':14,
        'review_groups':s['review_groups'],'nearest_original_prior_support':0,'nearest_original_later_support':988,
        'CAP01_dependent_prior_support':3,'older_prior_reference_conflict_cases':20,
        'D34_retrospective_rows':879,'D34_retrospective_prior_numeric_conflicts':12,
        'retrospective_scenario_candidates_NOT_APPLIED':867,'retrospective_candidates_2025_reference':111,
        'technical_checks':v['passed'],'interface_logic_checks':ui['passed'],'all_1454_rows_interaction_checked':True,
        'figures_visually_inspected':True,'browser_rendering_verified':False,'independent_validation':False,
        'source_values_modified':False,'active_dataset_changed':False,'capital_changes':0,'pending_after_review':1454,
        'CAP01_inherited_changes':2073,'CON01_activated':False,'calendar_dates_pending':True,
        'claims_modified':False,'dates_modified':False,'new_audit_columns':0,'models_trained':False,
        'application_authorized':False,'source_units_confirmed':False,'closure':'../'+close.relative_to(c.ROOT).as_posix()}
    c.dump(out/'closure_reference.json',{'decision_id':decision,'closure_workspace_relative':close.relative_to(c.ROOT).as_posix(),
        'data_catalog_activation':False,'verification_origin':'Own AI-assisted checks, no independent review.'})
    manifest={'created_utc':now,'type':'immutable_pending_capital_review_no_data_changes','files':[
        {'path':p.relative_to(out).as_posix(),'sha256':c.digest(p),'bytes':p.stat().st_size}
        for p in sorted(out.rglob('*')) if p.is_file()]}
    c.dump(out/'manifest.json',manifest)
    index=r.BASE/'current_run.json'
    c.dump(index,{'workspace_relative_run':rel,'decision_id':decision,'status':'verified_review_only_no_data_changes',
        'report_workspace_relative':rel+'/informe.html','pending_rows':1454,'corrections_applied':0})
    state['pending_capital_review']=record;state['memory_as_of']=now
    routes['week_1_pending_capital_review_index']='Hackaton/Semana 1/Revision_capitales_pendientes/current_run.json'
    c.dump(paths['ESTADO_PROYECTO.json'],state);c.dump(paths['RUTAS_PROYECTO.json'],routes)
    text=f'''\n\n### {decision}, revisión detallada de los 1.454 capitales pendientes, 16 de octubre de 2026, America/Bogota\n\nEl participante pidió comparar historiales, casos y tratamiento sin modificar datos. Se conserva la lista exacta pendiente de CAP01 D36 y se revisa contra el catálogo PRE00/REN00 activo: 1.454 filas, 1.452 pólizas, 691 edificios y 763 contenidos; 1.264 train y 190 test. La corrida ../{rel} archiva 5.587 periodos completos, 128 siniestros, contexto de dirección y 4.130 pares con todas las referencias originales habituales, incluidas las desfavorables. Hay catorce casos y un explorador para cada una de las 1.454 filas. Capital original y derivado se presentan juntos para reconocer CAP01.\n\nNinguna fila tiene apoyo anterior próximo en la referencia habitual original más reciente bajo los campos, completitud, no solapamiento, distancia de 1–400 días y cociente /1000 en 0,90–1,10. Existen 988 apoyos posteriores: 879 ya eran retrospectivos D34 y 109 tienen diferencias conocidas de contexto anterior. De los 988, 129 usan una referencia posterior 2025; 112 pertenecen al grupo de 879. Las rutas D34 permanecen congeladas, sin reescribir su criterio de cociente inverso para el apoyo posterior. Tres apoyos anteriores nuevos dependen de usar una cifra ya corregida CAP01 (B40325888, B51302846 y C67134620); no son evidencia original independiente ni autorizan una cascada.\n\nLa partición de revisión por prioridad tiene 879 retrospectivos D34, 109 con apoyo posterior y discrepancia previa, 108 sin cifra original habitual en la misma póliza, 2 residuales con dependencia CAP01, 16 residuales con dependencia T/W, 202 residuales con contexto incompleto y 138 con otras diferencias de riesgo/capital/distancia. Hay solapamientos de bloqueos y se conservan indicadores separados. La cifra de dos dependencias CAP01 en la partición no oculta la tercera, ya incluida entre los retrospectivos.\n\nDentro de los 879 retrospectivos, doce tienen además un capital original anterior próximo conocido e igual en contexto, pero la hipótesis /1000 se aparta más de ±10% de su cifra. Se propone separar esos doce y preparar como primer escenario retrospectivo 867 filas (111 con ancla test 2025), sin aplicarlo. La lista está en tables/proposed_retrospective_scenario_NOT_APPLIED con old/hipótesis/ancla y autorización false. Todos los 1.454 importes siguen pendientes. En veinte filas una referencia anterior más antigua resulta favorable mientras la cifra más reciente no lo es; no elegir solo el ancla conveniente. C02948658 muestra 39.600→62.800 CU durante 2024 y 40.400.000 en 2025: /1000 daría 40.400, pero queda 35,7% por debajo del último capital normal.\n\nC00131038 tiene 17.300.000 CU en 2021 y 17.600 en 2022: indicio de escala con evidencia posterior, no disponibilidad al cotizar 2021. B00723804 pasa de T/230.000 en 2022 a W/237.000.000 en 2023 y W/244.000 en 2024, sin unificar T/W. B19256617 muda dirección en julio 2022, luego tiene dos periodos altos y 400.000 CU en 2024; no copiar el capital del inmueble anterior ni ignorar la distancia temporal. B40325888 tiene 232.000 en 2024 procedentes de CAP01 y mantiene 239.000.000 en 2025. B00774853 solo muestra 2025 con 209.000.000; /1000 parece plausible marginalmente, pero carece de soporte independiente de esa póliza. B01207490 mantiene faltante smoke_alarms; no imputarlo para acreditar igualdad.\n\nLa hipótesis /1000 solo se calcula en tablas diagnósticas. Los 1.454 límites suman 192.855.500.000 CU frente a 192.855.500 hipotéticos, sin representar prima, pérdida o valor único de bienes: hay periodos/pólizas repetidos. No se dividen primas, costes, exposición, etiquetas o predicciones. La prima registrada no tiene base de prorrateo confirmada; B51302846 muestra la cautela en un tramo corto. De 128 siniestros, 24 se asignan a 23 periodos pendientes y uno conserva PRE00 antes del historial; ninguno aceptado asignado excede individualmente el capital hipotético por incurrido observado. Eso no confirma una unidad ni el alcance contractual del límite. Los siniestros no seleccionan las propuestas de capital.\n\nAntes de cualquier aplicación se requiere autorización nueva por cohorte y operación, preservación/reversión y una separación entre reconstrucción retrospectiva y preparación por corte temporal. No usar información de 2025 o resultados de validación como si fueran conocidos años antes. Si se modela con incidencias abiertas, los tratamientos de capital se compararán dentro de folds: importe reportado con transformación documentada, variable no disponible con imputación ajustada en entrenamiento, o reparación autorizada. Esta revisión no adopta ninguno ni añade metadatos de auditoría a los predictores. Se conservan los 2.073 CAP01, 1.454 pendientes, CON01 sin activar, fechas pendientes, DUP01 y REN00/PRE00.\n\nPasaron {v['passed']} controles propios y {ui['passed']} de lógica del explorador que recorre las 1.454 filas. Las dos figuras PNG fueron inspeccionadas con view_image. Se verifican valores completos de los historiales y claims frente a fuentes, todas las referencias por algoritmo de comprobación separado, la asignación por ocurrencia y hashes de originales, derivados e índice activo. La propuesta inicial conservada en iterations se afinó al detectar las doce contradicciones numéricas del grupo de 879. No se acredita renderizado real de navegador ni revisión independiente. Protocolo operativo 1.5 y catálogo preparado permanecen intactos; sin entrenamiento, proveedor externo, contacto a terceros, publicación o corrección de datos. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad y responsabilidad. Consultar pending_capital_review.\n'''
    paths['DECISIONES.md'].write_text(decisions.rstrip()+text,encoding='utf-8')
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip()+f'\n\nCapitales pendientes revisados, {decision}: [informe y explorador](../{rel}/informe.html), [propuesta sin aplicar](../{rel}/proposal.json). Lista CAP01 intacta: 1.454 filas/1.452 pólizas, 691 edificios y 763 contenidos; 5.587 periodos y 128 siniestros. Ningún respaldo anterior próximo original más reciente pasa el criterio. Hay 879 retrospectivos D34 y 109 apoyos posteriores con cambio de contexto previo; 108 sin referencia original habitual. Dependencias, T/W, faltantes y otras contradicciones quedan separadas. Dentro de los 879 hay 12 discrepancias numéricas anteriores adicionales: primer escenario retrospectivo propuesto de 867 filas, 111 con ancla 2025, sin aplicar ni autorizar. Tres apoyos anteriores dependen de CAP01; veinte referencias antiguas favorables contradicen el capital más reciente. No ampliar CAP01 ni elegir solo anclas convenientes. Pasaron {v["passed"]} controles de datos y {ui["passed"]} de lógica; dos figuras inspeccionadas, sin revisión independiente. Catálogo PRE00/REN00, importes, fechas y todos los pendientes permanecen iguales; protocolo 1.5 sin cambios. Ver pending_capital_review y {decision}.\n',encoding='utf-8')
    paths['capital_review_README.md'].write_text(paths['capital_review_README.md'].read_text('utf-8').rstrip()+f'\n\nLa revisión posterior de los 1.454 pendientes está separada de D34 en [Revision_capitales_pendientes](../Revision_capitales_pendientes/current_run.json), {decision}. [Informe con catorce casos y explorador](../Revision_capitales_pendientes/{out.relative_to(r.BASE).as_posix()}/informe.html). No aplica correcciones, no reescribe D34 ni amplía CAP01. El primer escenario retrospectivo propuesto contiene 867 filas después de separar doce discrepancias numéricas de los 879 originales; sigue sin aplicar.\n',encoding='utf-8')
    after=close/'after';after.mkdir()
    for name,p in paths.items():shutil.copy2(p,after/name)
    assert all(c.digest(c.ROOT/p)==sha for p,sha in protected.items())
    assert all(c.digest(out/e['path'])==e['sha256'] for e in manifest['files'])
    c.dump(close/'closure.json',{'created_utc':now,'decision_id':decision,'review':record,
        'manifest_sha256':c.digest(out/'manifest.json'),'original_and_active_dataset_hashes_unchanged':True,
        'documents':{p.relative_to(c.ROOT).as_posix():c.digest(p) for p in list(paths.values())+[index]}})
    print(json.dumps({'decision':decision,'run':str(out),'report':str(out/'informe.html'),'closure':str(close),
                      'status':'verified_review_only_no_data_changes'},ensure_ascii=False))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
