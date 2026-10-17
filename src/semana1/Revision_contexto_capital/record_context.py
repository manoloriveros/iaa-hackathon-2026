"""Cierra evidencia de revisión y actualiza memoria; no modifica índices de datos."""
from datetime import datetime,timezone
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import shutil
import sys
import review_context as a
import clean_data as c


def main(out):
    assert '--figures-inspected' in sys.argv
    assert not (out/'manifest.json').exists(),'Corrida cerrada: no sobrescribir.'
    v=json.loads((out/'verification.json').read_text('utf-8'));ui=json.loads((out/'interface_verification.json').read_text('utf-8'))
    s=json.loads((out/'summary.json').read_text('utf-8'));protected=json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    assert v['failed']==ui['failed']==0 and ui['all_109_rows_exercised'] and ui['all_12_cases_exercised']
    assert all(c.digest(c.ROOT/path)==sha for path,sha in protected.items())
    inspected=json.loads((out/'evidence/figure_hashes_actually_inspected.json').read_text('utf-8'))
    assert all(c.digest(out/path)==sha for path,sha in inspected.items()),'Una figura cambió después de inspeccionarla.'
    c.dump(out/'figure_inspection.json',{'status':'visually_inspected_by_Codex','method':'view_image of both actual PNG files',
        'figures':inspected,'finding':'Labels and cases legible; hypothetical markers distinct; B192 earlier high value has no hypothetical marker.',
        'real_browser_rendering_verified':False,'independent_validation':False})
    for name in ['review_context.py','render_context.py','verify_context.py','verify_report.js','record_context.py']:
        source=a.BASE/name;dest=out/'source_snapshot'/name
        if dest.exists():assert c.digest(source)==c.digest(dest)
        else:shutil.copy2(source,dest)
    for name in ['clean_data.py','correct_capitals.py']:shutil.copy2(c.BASE/name,out/'source_snapshot'/name)
    for name in ['README.md','PRACTICAS_PRIORITARIAS.md']:
        shutil.copy2(c.ROOT/'Preparación/Antecedentes/IAA_IA'/name,out/'evidence'/('IAA_'+name))
    failed=a.BASE/'runs/context_20261016T215439Z_22d3064b'
    assert a.cap.manifest_ok(failed)
    shutil.copy2(failed/'failed_attempt.json',out/'evidence/failed_export_attempt.json')
    c.dump(out/'evidence/failed_export_reference.json',{'workspace_relative_run':failed.relative_to(c.ROOT).as_posix(),
        'manifest_sha256':c.digest(failed/'manifest.json'),'status':'closed_failed_attempt_preserved_no_data_changes'})
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,tag,attrs):
            self.links += [value for key,value in attrs if key in ['href','src']]
    report=(out/'informe.html').read_text('utf-8');links=Links();links.feed(report)
    assert all(ref=='manifest.json' or (out/ref).is_file() for ref in links.links)
    now=datetime.now(timezone.utc).isoformat();rel=out.relative_to(c.ROOT).as_posix()
    paths={name:c.ROOT/'Preparación'/name for name in ['ESTADO_PROYECTO.json','MEMORIA_PROYECTO.md','DECISIONES.md']}
    paths['RUTAS_PROYECTO.json']=c.ROOT/'RUTAS_PROYECTO.json'
    # Re-read at closure to preserve any unrelated project work.
    state=json.loads(paths['ESTADO_PROYECTO.json'].read_text('utf-8'));routes=json.loads(paths['RUTAS_PROYECTO.json'].read_text('utf-8'))
    decisions=paths['DECISIONES.md'].read_text('utf-8');memory=paths['MEMORIA_PROYECTO.md'].read_text('utf-8')
    decision='D'+str(max(map(int,re.findall(r'\bD(\d+)\b',decisions)))+1)
    close=a.BASE/'closures'/datetime.now(timezone.utc).strftime('closure_%Y%m%dT%H%M%SZ');close.mkdir(parents=True,exist_ok=False)
    for name,path in paths.items():shutil.copy2(path,close/('before_'+name))
    record={'decision_id':decision,'workspace_relative_run':rel,'status':'verified_review_only_no_data_changes',
        'created_utc':now,'report_workspace_relative':rel+'/informe.html','cohort_rows':109,'policy_ids':109,
        'by_line':s['by_line'],'history_period_rows':571,'claims':8,'claims_in_focus_periods':2,
        'TW_only_rows':31,'building_address_changes':44,'contents_address_changes':34,
        'original_immediate_later_references':109,'test2025_references':17,'test2025_by_line':{'buildings':6,'contents':11},
        'old_context_missing_smoke_alarm_rows':3,'noncriterion_days_unoccupied_changed_known_pairs':68,
        'noncriterion_days_unoccupied_missing_pairs':1,'proposed_scale_rows_NOT_APPLIED':109,'other_pending_not_adjudicated':467,
        'retrospective_pending_unchanged':576,'base_pending_unchanged':1454,'capital_changes':0,
        'correction_authorized':False,'CON01_activated':False,'models_trained':False,'independent_validation':False,
        'real_browser_rendering':False,'own_source_checks_passed':v['passed'],'minimal_DOM_checks_passed':ui['passed'],
        'proposal_workspace_relative':rel+'/tables/proposed_scale_changes_NOT_APPLIED.parquet',
        'closure_workspace_relative':close.relative_to(c.ROOT).as_posix()}
    c.dump(out/'closure_record.json',record)
    c.dump(out/'manifest.json',{'created_utc':now,'type':'immutable_109_capital_context_review','files':[
        {'path':p.relative_to(out).as_posix(),'sha256':c.digest(p),'bytes':p.stat().st_size}
        for p in sorted(out.rglob('*')) if p.is_file()]})
    index=a.BASE/'current_run.json';c.dump(index,record)
    state['context_capital_review']=record;state['memory_as_of']=now
    routes['week_1_context_capital_review_index']='Hackaton/Semana 1/Revision_contexto_capital/current_run.json'
    c.dump(paths['ESTADO_PROYECTO.json'],state);c.dump(paths['RUTAS_PROYECTO.json'],routes)
    text=f'''\n\n### {decision}, 109 capitales con apoyo posterior y cambio de contexto anterior, 16 de octubre de 2026, America/Bogota

El participante solicitó revisar sus historiales, casos y tratamiento sin modificar datos. La corrida ../{rel} congela exactamente los 109 del grupo B de D48 que siguen pendientes en CAP03R: 75 edificios y 34 contenidos, 109 pólizas, 571 periodos completos. Se conserva el inventario de los otros 467 sin nueva adjudicación individual. Son 31 edificios con solo T→W en los campos del criterio previo, 44 con cambio de dirección y 34 contenidos con mudanza. Entre los 44 edificios hay 16 solo dirección, 17 dirección/construcción, seis dirección/alarmas y cinco los tres. Todos conservan cliente. Los 31 T/W entran el 1 de enero de 2023; el contraste W→W posterior permite revisar escala sin activar CON01 ni confirmar material físico.

Los 109 tienen respaldo en el periodo inmediatamente posterior original, sin CAP01/CAP02R/CAP03R, con campos D34 completos e iguales y sin solape. Sus inicios están a 3–365 días; la banda (capital/1000)/referencia 0,90–1,10 se cumple. El capital posterior está +2,22–3,90% sobre /1000 en edificios y +1,63–2,48% en contenidos. Hay 17 referencias test 2025 (seis edificios y once contenidos), señaladas por fila; las otras 92 también eran futuras al inicio del periodo pendiente. Se propone exactamente la lista congelada de 109 como eventual operación retrospectiva separada, sin aplicación ni autorización nueva. No equivale a preparación causal aprobada o confirmación de la unidad por la fuente.

B13523069 pasa de 105.000 CU en un inmueble a 382.000.000 en otro y luego 393.000 bajo la dirección nueva; /1000 daría 382.000, sin copiar el límite anterior. B03817872 muestra el sentido contrario, 301.000→185.000.000→191.000. En los 34 contenidos /1000 coincide con el capital anterior pese a la mudanza, compatible con mantener el valor declarado de bienes, sin probar identidad física. C09729229 empieza con tres días de 51.600 CU, cambia de dirección con 51.600.000 y test 2025 muestra 52.600: el capital no se anualiza por exposición.

B18335664, B31552770 y B43866315 conservan smoke_alarms nulo del riesgo anterior. Su comparación posterior del riesgo nuevo está completa; no se imputa el antiguo ni se afirma equivalencia de inmuebles. B19256617 tiene otra fila pendiente de 377.000.000 CU en julio 2022: sigue fuera de esta propuesta, dentro de los 467. Solo la fila 2023 de 388.000.000 se propone con ancla original 2024 de 400.000. No usar reparaciones nuevas para cascadas. C48613718/C01596694 conserva 29.300.000 y su situación anterior no se reabre.

La igualdad de contexto se limita a los campos exactos del criterio D34, enumerados en el informe. Se inventarían por separado los demás campos: days_unoccupied cambia en 68 pares informados de edificios y un par tiene faltante; edad, exposición, primas y otras circunstancias también pueden variar. No inferir tarifa constante ni identidad completa del riesgo físico. El maestro de direcciones carece de fechas de vigencia, por lo que solo aporta contexto. Se conservan primas y todos los demás campos. Los ocho siniestros observados son de edificios y tienen asignación única; dos caen en periodos del grupo, CL83963478 (4.446,52 CU) y CL25718230 (29.100,65 CU). Ninguno supera individualmente su capital hipotético; no se usan pérdidas o primas para elegir reparaciones, ni se cambian siniestros u objetivo.

Pasaron {v['passed']} controles propios de fuente y {ui['passed']} de lógica del explorador, que recorren las 109 filas y doce casos explicados. Ambos PNG se inspeccionaron realmente y mantienen los mismos hashes; no se acredita renderizado real de navegador ni revisión independiente. Se conserva un primer intento fallido de exportación por row_id convertido en índice, corregido antes de generar una corrida nueva. Los ajustes de las comprobaciones y la separación de diferencias informadas/faltantes quedan documentados. Todos los originales, archivos del catálogo, ambos índices de datos y manifiestos anteriores mantienen sus hashes. No cambió capital alguno: siguen 576 pendientes en retrospectiva, 1.454 en la base y 2.951 correcciones heredadas. Protocolo 1.7, fechas, CON01 y demás pendientes permanecen iguales. Se actualizan solo evidencia de revisión, memoria, estado y rutas. Sin entrenamiento, proveedor externo, publicación, contacto a terceros o delegación. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad, límites y responsabilidad. Consultar context_capital_review.
'''
    text=text.replace('Se inventarían por separado','Quedan inventariados por separado')
    paths['DECISIONES.md'].write_text(decisions.rstrip()+text,encoding='utf-8')
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip()+f'''\n\nRevisión de 109 capitales con cambio de contexto, {decision}: [informe con doce casos y explorador completo](../{rel}/informe.html), [lista propuesta sin aplicar](../{rel}/tables/proposed_scale_changes_NOT_APPLIED.csv). Son 75 edificios y 34 contenidos, 571 periodos y ocho siniestros. 31 casos muestran solo T→W; otros 78 cambian de dirección. Los 109 tienen referencia inmediatamente posterior original, contexto D34 completo e igual y escala /1000 plausible. Se propone una operación retrospectiva separada para esos 109, sin autorización o aplicación. 17 usan test 2025 (6/11); los demás también tienen información posterior. Conservar los límites propios de cada inmueble/bienes y los nulos anteriores de tres casos. En B19256617, la fila 2023 de 388.000.000 tiene ancla 400.000; el otro capital de 377.000.000 sigue pendiente fuera del grupo, sin cascada. La igualdad se limita al criterio, no a todos los factores tarifarios: days_unoccupied cambia en 68 pares informados y otro tiene faltante. Pasaron {v['passed']} controles propios y {ui['passed']} de lógica, dos figuras inspeccionadas, sin revisión independiente o navegador acreditados. Ambos catálogos y todos sus datos intactos: 576 pendientes en retrospectiva y 1.454 en la base. Los otros 467 quedan inventariados sin nueva adjudicación. Protocolo 1.7, fechas y CON01 sin cambios, sin entrenamiento. Ver context_capital_review y {decision}.\n''',encoding='utf-8')
    after=close/'after';after.mkdir()
    for name,path in paths.items():shutil.copy2(path,after/name)
    assert all(c.digest(c.ROOT/path)==sha for path,sha in protected.items()) and a.cap.manifest_ok(out)
    c.dump(close/'closure.json',{'created_utc':now,'decision_id':decision,'review':record,'manifest_sha256':c.digest(out/'manifest.json'),
        'all_protected_files_and_dataset_indexes_unchanged':True,
        'documents':{path.relative_to(c.ROOT).as_posix():c.digest(path) for path in list(paths.values())+[index]}})
    print(json.dumps({'decision':decision,'run':str(out),'closure':str(close),'status':'verified_review_only_no_data_changes'},ensure_ascii=False))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
