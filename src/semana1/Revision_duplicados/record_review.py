"""Cierre documental de DUP01 propuesto. Ningún dato se depura en este paso."""
from pathlib import Path
from datetime import datetime,timezone
from html.parser import HTMLParser
from urllib.parse import unquote
import json
import re
import shutil
import subprocess

import review_pairs as a


def main():
    root=a.ROOT;pointer=json.loads((a.BASE/'current_run.json').read_text(encoding='utf-8'))
    out=root/pointer['workspace_relative_run'];report_path=root/pointer['report_workspace_relative'];assert pointer['status']=='verified_proposal_only_no_data_changes'
    s=json.loads((out/'summary.json').read_text(encoding='utf-8'))
    verification=json.loads((out/'verification.json').read_text(encoding='utf-8'))
    manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'));manifest_hash=a.c.digest(out/'manifest.json')
    assert all(a.c.digest(out/e['path'])==e['sha256'] for e in manifest['files'])
    closure=a.BASE/'closures'/datetime.now(timezone.utc).strftime('closure_%Y%m%dT%H%M%SZ')
    (closure/'before').mkdir(parents=True,exist_ok=False);(closure/'after').mkdir()
    for name in ['record_review.py','verify_report.js']:shutil.copy2(a.BASE/name,closure/name)
    result=subprocess.run(['node',str(a.BASE/'verify_report.js'),str(report_path)],capture_output=True,text=True,encoding='utf-8',check=True)
    logic=json.loads(result.stdout);assert logic['passed'] and logic['all_604_groups_exercised']
    a.c.dump(closure/'report_logic_verification.json',logic)
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.paths=[]
        def handle_starttag(self,tag,attrs):
            self.paths.extend(v for k,v in attrs if k=='href' and v and not v.startswith(('data:','#','http:','https:')))
    links=Links();links.feed(report_path.read_text(encoding='utf-8'))
    assert all((report_path.parent/unquote(path)).is_file() for path in links.paths)
    docs=['Preparación/DECISIONES.md','Preparación/MEMORIA_PROYECTO.md','Preparación/ESTADO_PROYECTO.json','RUTAS_PROYECTO.json','Hackaton/Semana 1/README.md']
    for path in docs:
        dst=closure/'before'/path;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/path,dst)
    decisions=root/'Preparación/DECISIONES.md';before=decisions.read_text(encoding='utf-8')
    decision='D'+str(max(int(x) for x in re.findall(r'\bD(\d+)\b',before))+1)
    rel='../'+out.relative_to(root).as_posix();report_ref='../'+report_path.relative_to(root).as_posix()
    decisions.write_text(before+f'''

### {decision}, revisión de 604 pares de siniestros y regla DUP01 propuesta sin aplicar, 16 de octubre de 2026, America/Bogota

El participante pidió revisar historiales de los 604 pares, mostrar casos concretos y proponer una regla de depuración sin modificar datos. La corrida {rel} revisa toda la cohorte congelada D40 y las 601 pólizas afectadas, con 2.346 periodos y 1.678 registros de siniestro incluyendo dos pólizas de control. Las 601 pólizas afectadas tienen 462 otros registros de siniestro, que se conservan. No se usan datos de test para decidir la regla, ni se escribe un fichero de claims depurado o se cambia el catálogo activo D38. D39 sigue sin activar; los capitales CAP01 y pendientes no cambian.

Los 604 grupos tienen dos miembros e igualdad exacta de los once campos salvo claim_id: póliza, ramo, peligro, ocurrencia, reporte, estado, pagado, incurrido, recuperaciones, reparador y tercero. La detección independiente por tuplas reproduce la cohorte; no se redondean cifras ni aproximan fechas. Hay 411 pares motor, 109 edificios y 84 contenidos; 586 cerrados, 12 abiertos y seis rechazados. 296 pares tienen reparador informado, 159 tercero y 59 recuperaciones positivas, también iguales. Ambos ausentes cuentan como igualdad de registro, sin probar ausencia del objeto real.

Cada pareja contiene exactamente un ID CL+8 dígitos y otro CL+9. Los 604 IDs largos del fichero pertenecen exclusivamente a esas parejas; los otros 162.546 IDs son cortos. 600 ocurrencias son de 2022, tres de 2021 y una de 2020; 572 reportes son de 2022 y 32 de 2023. Es fuerte respaldo a una duplicación de registro en este snapshot, sin confirmar causa del generador o identidad física universal de eventos. No hay event_id, factura ni timestamp de creación/revisión. El orden no es cronología: el corto aparece primero en 303 parejas y el largo en 301.

DUP01 se propone solo para los 604 pares congelados, sin expansión automática y con hashes/esquema. Exige grupo de dos, igualdad de todos los valores salvo ID, IDs únicos distintos, misma fila cubierta o mismo estado anterior a historia y un miembro de cada formato revisado. Propuesta de representante: conservar CL+8 y excluir su gemelo CL+9 en una capa derivada futura, registrando alias largo→conservado y la bitácora completa. El formato dominante es una elección determinista de alias después de demostrar igualdad, no una prueba de fecha anterior; nunca borrar por longitud sola ni truncar un ID. Diferencias de estado/importes/fechas/recuperaciones/reparador/tercero, presente frente a ausente, grupos distintos de dos, ambigüedad o esquema nuevo permanecen en revisión. No hay autorización de aplicación ni se declara aplicada.

La conciliación por intervalos reconstruye de forma separada 1.206 miembros asignados, correspondientes a 603 parejas, y una pareja anterior al primer periodo. Son 600 periodos observados afectados; las 597 copias aceptadas asignables se concentran en 594 periodos. Tres pólizas tienen dos parejas de eventos distintos: conservar un evento por pareja, nunca un único siniestro por póliza. Los seis rechazados tendrían efecto en el conteo bruto de expedientes, no en el coste/frecuencia aceptados.

El efecto hipotético de excluir un miembro por pareja es 3.174.167,49 CU de incurrido neto aceptado observado: motor 1.833.024,44; edificios 1.112.148,78; contenidos 228.994,27. Dentro de periodos actuales son 3.173.808,61 CU; 358,88 corresponden a la pareja fuera de historia. El cálculo se verifica con Decimal sobre campos originales y concilia pagado+reserva−recuperación. Es una sensibilidad de preparación, no pérdida última, sobrecoste confirmado, corrección aplicada o mejora de score. No entrenar o escoger la cohorte por su efecto en una métrica.

Once casos ilustran toda la cohorte: M27706820, CL40310602/CL175619477, robo de 01-11-2022 y neto 1.418,65 CU; M54002274, CL26261382/CL187407319, lesión cerrada de 242.462,87 CU; B94219451, CL07800816/CL165324565, incendio de 186.636,16 CU; C53599376, CL93952805/CL177783271, inundación de 18.650,72 CU. En M71403075, CL74979157/CL179068823, ambos abiertos con pago 7.786,93 e incurrido 38.171,33: la reserva también se duplicaría. En M76932061, CL02983833/CL175421896, pago/incurrido 15.229,35 menos recuperación 12.183,48 deja neto 3.045,87. M37030249 ocurrió 04-12-2020 por 358,88, anterior a la cobertura observada; C09803918 es rechazado por cero; M77733416 tiene dos parejas distintas. Los demás casos son controles no idénticos.

Una vista diagnóstica que distingue gemelos exactos conserva 57 parejas no idénticas con misma póliza/ocurrencia; 17 comparten peligro y una además report_date. M83268515 tiene dos own_damage con iguales fechas 01-10-2024/22-10-2024, pero CL19172982 es abierto, pago 290,31, incurrido 1.503,24 y RP0051; CL75369456 cerrado, 3.177,35 y RP0487. DUP01 conserva ambos, sin inferir dos eventos o una evolución de versión. M63592395 tiene dos third_party_prop de 16-04-2022 con TP8386915/TP2577127, reportes e importes distintos; no se fusionan. Una clave abreviada incluiría 605, 621 o 661 grupos según campos, frente a los 604 exactos. Esos controles limitan el alcance de la regla.

Pasaron {verification['checks_count']} controles propios de fuentes, cohorte exacta, posiciones/IDs, asignación independiente, dinero, historias completas y controles de conservación. {logic['checks_count']} controles de lógica del explorador con DOM mínimo ejercitan once ejemplos y las 604 opciones; no equivalen a renderizado en navegador ni revisión independiente. La figura se inspeccionó visualmente. La primera prueba del explorador detectó que el sufijo _date incluía paid_to_date/incurred_to_date y provocaba TypeError; se conserva el fallo y se publica una edición nueva con una lista explícita de las cuatro fechas. El dataset y los cálculos no se repitieron por esa reparación de vista; se verifican todos los casos y las 604 opciones en la edición corregida. Los once originales, seis tablas preparadas y puntero activo conservan hashes; D38/D40 y sus manifiestos no se reescriben. No hubo depuración, objetivo T0 nuevo, correcciones, entrenamiento, proveedor externo, envío, publicación o delegación.

Aplican IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6. Codex trazó historiales, contrastó hipótesis y contraejemplos y preparó la regla y bitácora de propuesta; la decisión humana de aplicar queda pendiente. Antes de una aplicación autorizada, comprobar de nuevo el snapshot y usar la cohorte congelada, crear otra versión derivada y conservar alias/reversión. El conocimiento procede de la valoración de 2024, sin atribuir disponibilidad a un corte histórico anterior. Consultar duplicate_claim_review en el estado y Revision_duplicados/current_run.json.
''',encoding='utf-8')
    memory=root/'Preparación/MEMORIA_PROYECTO.md'
    memory.write_text(memory.read_text(encoding='utf-8')+f'''

## {decision}: DUP01 propuesto para 604 parejas, sin aplicar, 16 de octubre de 2026

La [revisión de historiales]({report_ref}) cubre 604 pares en 601 pólizas y once casos, con explorador para cualquier pareja. [Regla estructurada]({rel}/proposed_rule.json) y [propuesta por fila]({rel}/tables/proposed_pair_actions.csv). Se recomienda una copia por igualdad exacta de los once campos salvo claim_id, con mismo periodo o misma prehistoria. Cada pareja contiene CL+8 y CL+9 dígitos; todos los 604 IDs largos están en las parejas. Conservar el corto es una elección determinista de representante, no prueba de antigüedad. Nunca depurar por longitud sola o solo por póliza/fechas; no se aplicó ninguna exclusión.

Hay 411 pares motor, 109 edificios y 84 contenidos; 586 cerrados, 12 abiertos y seis rechazados. 600 ocurren en 2022, tres en 2021 y una en 2020. Los 603 pares asignables afectarían 600 periodos; 597 copias aceptadas asignables afectan 594 periodos. El efecto hipotético es 3.174.167,49 CU total observado y 3.173.808,61 CU dentro de periodos actuales; el resto, 358,88 CU, está antes de la historia. Mantener pago, reserva y recuperación conciliados; rechazados no reducen coste aceptado. No presentar esa sensibilidad como último o mejora predictiva.

Existen 57 parejas no idénticas con misma póliza/ocurrencia, 17 también con mismo peligro y una con ambas fechas. M83268515 muestra la necesidad de conservar dos expedientes con distintos importes/estado/reparador; M63592395 tiene terceros distintos. Las tres pólizas con dos pares mantienen dos eventos, no uno. Los 462 otros siniestros de las pólizas afectadas se conservan. La identificación no dispone de event_id/factura ni confirmación externa: evidencia fuerte para regla operativa, sin verdad física absoluta.

Pasaron {verification['checks_count']} comprobaciones propias y {logic['checks_count']} de lógica del informe que recorren las 604 parejas; figura inspeccionada, sin navegador ni revisor independiente acreditado. La capa D38, la candidata D39, los 1.454 capitales pendientes y todos los originales permanecen intactos. No hay claims depurado, activación o T0 nuevo. Consultar {decision} y duplicate_claim_review para una futura decisión humana de aplicación.
''',encoding='utf-8')
    statepath=root/'Preparación/ESTADO_PROYECTO.json';state=json.loads(statepath.read_text(encoding='utf-8'))
    state['duplicate_claim_review']={
        'decision_id':decision,'status':'histories_reviewed_DUP01_proposed_not_applied','run':rel,'report':report_ref,
        'rule':rel+'/proposed_rule.json','proposal':rel+'/tables/proposed_pair_actions.parquet',
        'index':'../Hackaton/Semana 1/Revision_duplicados/current_run.json','pairs':604,'members':1208,'affected_policies':601,
        'by_line':s['by_line'],'by_status':s['by_status'],'loss_years':s['loss_years'],
        'equality_fields':s['full_equality_fields'],'proposed_keep':'CL+8 digits after full equality and all gates',
        'proposed_exclude':'Its exact CL+9-digit twin only','identifier_length_alone_is_not_a_deletion_rule':True,
        'cohort_is_frozen':True,'cohort_auto_expansion':False,'assigned_groups':603,'prehistory_groups':1,
        'assigned_periods_affected':600,'accepted_assigned_copies':597,'accepted_assigned_periods':594,
        'hypothetical_net_reduction_total_CU':s['hypothetical_accepted_net_reduction_all_CU'],
        'hypothetical_net_reduction_assigned_CU':s['hypothetical_accepted_net_reduction_assigned_CU'],
        'same_occurrence_nonidentical_groups_preserved':57,'same_peril_nonidentical_groups_preserved':17,
        'same_report_date_nonidentical_groups_preserved':1,'other_claim_records_preserved_on_affected_policies':462,
        'technical_checks':verification['checks_count'],'report_logic_checks':logic['checks_count'],
        'case_histories':11,'all_groups_interaction_checked':True,'figure_visually_inspected':True,
        'data_modified':False,'active_dataset_changed':False,'operation_applied':False,'T0_materialized':False,
        'external_source_confirmation':False,'human_application_approval':'not provided; review-only request',
        'independent_validation':False,'browser_rendering_verified':False,'models_trained':False,
        'closure':'../'+closure.relative_to(root).as_posix()}
    state['data_validation_gap_review']['duplicate_followup_review_decision']=decision
    state['data_validation_gap_review']['duplicate_errors_not_confirmed']=True
    for p in state['pending_priorities']:
        if p['id']=='P05':
            p['action']=decision+': historiales revisados y DUP01 propuesto sin aplicar para 604 pares; falta decisión humana. Después conciliar/materializar T0, calendario/cobertura, F0 y particiones; mantener las demás incidencias.'
    a.c.dump(statepath,state)
    routespath=root/'RUTAS_PROYECTO.json';routes=json.loads(routespath.read_text(encoding='utf-8'))
    routes['week_1_duplicate_claim_review_index']='Hackaton/Semana 1/Revision_duplicados/current_run.json';a.c.dump(routespath,routes)
    week=root/'Hackaton/Semana 1/README.md'
    week.write_text(week.read_text(encoding='utf-8')+'\n\nLa revisión de los 604 pares de siniestros está en `Revision_duplicados/current_run.json`. Incluye las historias de las 601 pólizas, once casos y los controles que no deben colapsarse. DUP01 es una propuesta congelada con exclusiones y alias previstos; no modifica claims ni el catálogo activo.\n',encoding='utf-8')
    for path in docs:
        dst=closure/'after'/path;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/path,dst)
    integration=[]
    def check(name,value):integration.append({'name':name,'passed':bool(value)});assert value,name
    check('immutable_review_run_matches_manifest',a.c.digest(out/'manifest.json')==manifest_hash and all(a.c.digest(out/e['path'])==e['sha256'] for e in manifest['files']))
    check('all_report_local_links_resolve',all((report_path.parent/unquote(p)).is_file() for p in links.paths))
    check('all_604_groups_report_logic_checked',logic['passed'] and logic['all_604_groups_exercised'] and not logic['real_browser_rendering'])
    check('active_prepared_index_unchanged',a.c.digest(root/'Hackaton/Semana 1/Limpieza/current_dataset.json')==a.c.digest(out/'evidence/active_index.json'))
    check('documentation_paths_resolve',all((root/'Preparación'/state['duplicate_claim_review'][key]).exists() for key in ['run','report','rule','proposal','index','closure']))
    check('prior_state_sections_preserved',set(json.loads((closure/'before/Preparación/ESTADO_PROYECTO.json').read_text(encoding='utf-8'))).issubset(state))
    check('proposal_never_described_as_applied',not state['duplicate_claim_review']['operation_applied'] and not state['duplicate_claim_review']['data_modified'] and not pointer['operation_applied'])
    check('decision_unique_and_memory_linked',len(re.findall(r'^### '+decision+r',',decisions.read_text(encoding='utf-8'),flags=re.M))==1 and decision in memory.read_text(encoding='utf-8'))
    a.c.dump(closure/'integration_verification.json',{'passed':True,'checks_count':len(integration),'checks':integration,
        'decision_id':decision,'review_manifest_sha256':manifest_hash,'independent_validation':False})
    a.c.dump(closure/'manifest.json',{'files':[{'path':p.relative_to(closure).as_posix(),'sha256':a.c.digest(p),'bytes':p.stat().st_size}
        for p in sorted(closure.rglob('*')) if p.is_file()]})
    print(json.dumps({'decision':decision,'technical_checks':verification['checks_count'],'report_checks':logic['checks_count'],
        'integration_checks':len(integration),'closure':str(closure),'data_modified':False}),flush=True)


if __name__=='__main__':main()
