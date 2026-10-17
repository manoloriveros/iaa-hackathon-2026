"""Cierre documental de revisión202 y pendientes, sin alterar datos o contrato operativo."""
from datetime import datetime,timezone
from pathlib import Path
from html.parser import HTMLParser
import json,re,shutil,sys
import review_incomplete as a
import clean_data as c
def main(out):
    assert '--figures-inspected' in sys.argv and not (out/'manifest.json').exists()
    v=json.loads((out/'verification.json').read_text('utf-8'));ui=json.loads((out/'interface_verification.json').read_text('utf-8'))
    s=json.loads((out/'summary.json').read_text('utf-8'));protected=json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    assert v['failed']==ui['failed']==0 and ui['all_202_rows_exercised'] and ui['all_12_cases_exercised']
    assert all(c.digest(c.ROOT/p)==sha for p,sha in protected.items())
    for name in ['review_incomplete.py','update_backlog.py','render_incomplete.py','verify_incomplete.py','verify_report.js','record_incomplete.py']:
        dest=out/'source_snapshot'/name
        if dest.exists():assert c.digest(dest)==c.digest(a.BASE/name)
        else:shutil.copy2(a.BASE/name,dest)
    for name in ['clean_data.py','correct_capitals.py']:shutil.copy2(c.BASE/name,out/'source_snapshot'/name)
    for name in ['README.md','PRACTICAS_PRIORITARIAS.md']:shutil.copy2(c.ROOT/'Preparación/Antecedentes/IAA_IA'/name,out/'evidence'/('IAA_'+name))
    c.dump(out/'figure_inspection.json',{'status':'visually_inspected_by_Codex','method':'view_image of both actual final saved PNG files',
        'figures':{name:c.digest(out/name) for name in ['figures/missing_context.png','figures/histories.png']},
        'finding':'Labels and counts legible;132 fields distinguished from131 rows; original and hypothetical capital separate on explicitly logarithmic axes.',
        'real_browser_rendering_verified':False,'independent_validation':False})
    c.dump(out/'implementation_notes.json',{'scope':'No data mutation during analysis or report preparation.',
        'report_preparation_fix':'An editorial replacement briefly changed a Python attribute name and produced a SyntaxError before execution. Corrected before final rendering and verification; no data effect.',
        'initial_readonly_probe_fixes':'A stale script filename and terminal Unicode encoding were corrected for read-only inspection. No protected file changed.',
        'verification':'The final data and UI verification suites passed without assertion failures.'})
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.refs=[]
        def handle_starttag(self,tag,attrs):self.refs += [val for key,val in attrs if key in ['href','src']]
    report=(out/'informe.html').read_text('utf-8');parser=Links();parser.feed(report)
    assert all(ref=='manifest.json' or (out/ref).is_file() for ref in parser.refs)
    assert json.loads(re.search(r'<script id="reviewData" type="application/json">([\s\S]*?)</script>',report).group(1))==json.loads((out/'explorer_data.json').read_text('utf-8'))
    paths={name:c.ROOT/'Preparación'/name for name in ['ESTADO_PROYECTO.json','MEMORIA_PROYECTO.md','DECISIONES.md']};paths['RUTAS_PROYECTO.json']=c.ROOT/'RUTAS_PROYECTO.json'
    state=json.loads(paths['ESTADO_PROYECTO.json'].read_text('utf-8'));routes=json.loads(paths['RUTAS_PROYECTO.json'].read_text('utf-8'))
    decisions=paths['DECISIONES.md'].read_text('utf-8');memory=paths['MEMORIA_PROYECTO.md'].read_text('utf-8')
    decision='D'+str(max(map(int,re.findall(r'\bD(\d+)\b',decisions)))+1);now=datetime.now(timezone.utc).isoformat();rel=out.relative_to(c.ROOT).as_posix()
    close=a.BASE/'closures'/datetime.now(timezone.utc).strftime('closure_%Y%m%dT%H%M%SZ');close.mkdir(parents=True,exist_ok=False)
    for name,p in paths.items():shutil.copy2(p,close/('before_'+name))
    record={'decision_id':decision,'workspace_relative_run':rel,'created_utc':now,'status':'verified_review_only_no_data_changes',
        'report_workspace_relative':rel+'/informe.html','cohort_rows':202,'policies':202,'by_line':s['by_line'],'history_rows':844,
        'original_reference_pairs':642,'strict_original_support_pairs':0,'focus_complete_rows':71,'focus_missing_rows':131,
        'focus_complete_distant_compatible_rows':48,'focus_complete_no_distant_compatible_rows':23,
        'missing_field_bridge_records':132,'bridge_statuses':s['bridge_statuses'],'claims':24,'claims_in_focus_periods':4,
        'test2025_focus_rows':40,'test2025_later_incomplete_reference_rows':34,
        'proposed_action':'KEEP_ALL_202_PENDING_NO_IMPUTATION_NO_WINDOW_EXTENSION','automatic_repair_candidates':0,
        'participant_confirmed_108_keep_pending':True,'other_pending_rows':265,'other_pending_not_newly_adjudicated_excluding108':157,
        'capital_changes':0,'correction_authorized':False,'retrospective_pending_unchanged':467,'base_pending_unchanged':1454,
        'protocol_1_8_unchanged':True,'predictor_guard_unchanged':True,'models_trained':False,'independent_validation':False,
        'own_source_checks':v['passed'],'minimal_DOM_checks':ui['passed'],'real_browser_rendering_verified':False,
        'validation_backlog_controls_reconciled':58,'validation_workstreams':16,'contacts_exclusion_operational_gap':True,
        'closure_workspace_relative':close.relative_to(c.ROOT).as_posix()}
    backlog_record={'decision_id':decision,'workspace_relative_run':rel,'report_workspace_relative':rel+'/informe.html#pendientes',
        'controls_workspace_relative':rel+'/validation_backlog_58.json','workstreams_workspace_relative':rel+'/tables/validation_workstreams.csv',
        'controls_reconciled':58,'workstreams':16,'scope':'Documentary reconciliation plus actual guard probe; not a full fresh execution of all58 controls.',
        'source_D40_index_preserved':True,'contacts_guard_gap':True,'all_data_approved_for_modeling':False}
    c.dump(out/'closure_record.json',{'review':record,'validation_backlog':backlog_record})
    c.dump(out/'manifest.json',{'created_utc':now,'type':'immutable_202_incomplete_capital_review_and_validation_backlog','files':[
        {'path':p.relative_to(out).as_posix(),'sha256':c.digest(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()]})
    index=a.BASE/'current_run.json';c.dump(index,record)
    state['incomplete_capital_review']=record;state['validation_backlog_update']=backlog_record
    state['no_original_capital_review']['participant_confirmed_keep_pending_decision']=decision;state['no_original_capital_review']['participant_confirmed_keep_108_pending']=True
    state['memory_as_of']=now
    routes['week_1_incomplete_capital_review_index']='Hackaton/Semana 1/Revision_contexto_incompleto/current_run.json'
    routes['week_1_validation_backlog_index']='Hackaton/Semana 1/Revision_contexto_incompleto/current_run.json'
    c.dump(paths['ESTADO_PROYECTO.json'],state);c.dump(paths['RUTAS_PROYECTO.json'],routes)
    text=f'''\n\n### {decision}, 202 capitales con contexto incompleto y validaciones pendientes, 16 de octubre de 2026, America/Bogota

El participante confirmó conservar los 108 sin ancla de D55 y pidió revisar los 202 del grupo F de D48, comparar historias/casos, proponer tratamiento sin modificar datos y listar validaciones pendientes. La corrida ../{rel} congela exactamente las 202 filas/pólizas que siguen pendientes en CAP04R: 63 edificios y 139 contenidos, 844 periodos completos y 642 referencias originales habituales. Todos los capitales de estas historias siguen iguales a los originales, sin reparaciones usadas como anclas nuevas. No hay ninguna referencia completa/equivalente que además cumpla no solape, inicio a 1–400 días y razón (capital/1000)/referencia de 0,90–1,10. Se conservan todas las referencias contradictorias o distantes, sin elegir solo las favorables.

En 131 filas falta un atributo propio: 36 solo smoke_alarms, 36 solo security_level, 58 solo high_value_items y una ambos campos de contenidos. Son 132 campos, no 132 pólizas. Las otras 71 filas están completas y los faltantes pertenecen a referencias; 48 tienen respaldo original completo compatible a más de 400 días y 23 no. Hay 259 comparaciones próximas incompletas compatibles en tiempo/importe; 57 filas las tienen a ambos lados. De los 132 campos propios ausentes, 50 tienen vecinos iguales bajo los demás campos registrados compatibles, 12 valores iguales con otro contexto o faltante, 69 solo un lado conocido y uno vecinos diferentes. La igualdad observada a ambos extremos no prueba el valor desconocido intermedio ni continuidad física completa.

B01207490: 332.000 CU y alarmas=true en 2023, 342.000.000 con alarmas ausentes en 2024; no rellenar el nulo para justificar 342.000. B02977304 tiene 187.000.000 con true en 2021, 193.000 con alarmas ausentes en 2022 y 198.000 con true en 2023: la referencia completa está a 730 días, fuera del criterio. B12840475 tiene 243.000 y false en 2024, 250.000.000 con alarmas ausentes en 2025 y después 289.000 con true en otro inmueble/construcción; no trasladar el dato posterior al riesgo anterior. C23894587 tiene 54.400.000 en 2023 con seguridad y bienes de valor ausentes, rodeado de standard y un bien en 2022/2024; se conservan ambos nulos. Desconocido no equivale a false, locks o cero.

Se proponen conservar los 202 pendientes y priorizar una revisión metodológica separada de las 48 filas completas con referencia distante, sin ampliar aquí 400 días. Los 23 completos restantes requieren aclarar referencias; los 131 incompletos mantienen incertidumbre. Cualquier imputación de modelo se aprendería dentro del corte, separada de una reparación de fuente. No hay lista autorizada de /1000, imputación o recodificación. Los 108 D55 permanecen pendientes por decisión humana expresa; los otros 157 no reciben adjudicación nueva. Total: 467 pendientes retrospectivos y 1.454 en la base, con las 3.060 correcciones anteriores preservadas.

Hay 24 siniestros observados, todos asignados de forma única; cuatro en periodos del grupo. CL96646113 tiene incurrido 28.258,63 CU frente a hipótesis 64.900. Ninguno supera individualmente su capital hipotético, sin que esto confirme unidades. No se usan pérdidas o primas para seleccionar reglas, ni se modifican costes, fechas, coberturas o etiquetas. Hay 40 filas pendientes de test 2025 y, por separado, 34 con referencia posterior cercana test 2025 incompleta: no son 34 reparaciones confirmadas. El carácter futuro de la evidencia se conserva.

Se reconcilian documentalmente los 58 controles de D40 con las aplicaciones posteriores, agrupados en 16 bloques. No se reejecutan los 58 ni se presenta la auditoría histórica como nueva. DUP01/REN00/PRE00 y CAP01–CAP04R están aplicados en sus cohortes; persisten límites semánticos e integración. Prioridad para piloto: T0 materializado con conciliación y ceros legítimos; F0 por disponibilidad; exclusión real de fuga; particiones V22/V23/V24 y preparación dentro de corte; uniones controladas; métrica Tweedie D² p=1,5 por importe de periodo. También faltan tratamiento del último/reporte/IBNR/recuperaciones, calendario, capitales restantes, T/W, cobertura frente a peligro/capital, coherencia autos/hogar/clima, faltantes/deriva/soporte, concentración/inflación, maestros/proxies/comercial, entrega/segunda semana y reproducción/revisión humana.

Pendiente P0 comprobado: D50 pide excluir customer_service_contacts, pero el guard actual devuelve None para esa columna y la conserva en una selección diagnóstica. renewal_decision y audit_* sí se bloquean. Se documenta la brecha sin cambiar el guard, el protocolo o un modelo. La exclusión debe trasladarse al contrato/selector y probarse antes de entrenar. Los conteos D40 de coberturas, autos y deriva quedan explícitamente históricos y requieren actualización en cada análisis, no se reciclan como resultado vigente de CAP04R.

Pasaron {v['passed']} controles propios de fuentes y {ui['passed']} de lógica, recorriendo las 202 vistas y doce casos. Se reconstruyen todas las comparaciones y vecinos, se releen historias/direcciones y claims, se comprueban los 467 pendientes incluidos los 108, la conciliación de 58 controles y la sonda de guard. Ambos PNG fueron inspeccionados realmente; no se acredita renderizado de navegador o revisión independiente. Originales, archivos del catálogo, ambos índices de datos, protocolo 1.8, guard y manifiestos anteriores mantienen hashes. Solo cambian evidencia de revisión, memoria, estado y rutas. Se conservan los índices históricos D40/D55. Sin entrenamiento, T0/F0 nuevo, proveedor externo, publicación, contacto a terceros o delegación. La IA preparó análisis/código/controles propios; la autorización humana de hoy se limita a conservar los 108 y revisar los 202. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad y límites. Ver incomplete_capital_review y validation_backlog_update.
'''
    paths['DECISIONES.md'].write_text(decisions.rstrip()+text,encoding='utf-8')
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip()+f'''\n\n202 contextos incompletos revisados, {decision}: [informe con doce casos, gráficos y pendientes](../{rel}/informe.html), [58 controles reconciliados](../{rel}/validation_backlog_58.json). Se confirma por instrucción humana mantener los 108 D55 pendientes. El grupo F tiene 202 pólizas (63 edificios, 139 contenidos), 844 periodos y 642 referencias originales; ninguna cumple todo el criterio D34 de contexto conocido/igual y 400 días. Hay 131 filas con 132 campos ausentes y 71 filas completas; 48 de estas tienen respaldo completo compatible más allá de 400 días, otras 23 no. Se propone mantener los 202 y sus nulos, priorizando revisión separada de las 48 sin ampliar el criterio ahora. Los 50 campos con vecinos iguales bajo contexto registrado compatible siguen sin valor intermedio demostrado. Se conservan 24 siniestros, cuatro en periodos del grupo. 40 filas test 2025 y 34 referencias posteriores test incompletas son conteos distintos. Siguen 467 pendientes en retrospectiva y 1.454 en la base; los otros 157 ajenos a 202/108 no reciben adjudicación. Los 58 controles se agrupan en 16 bloques pendientes, sin reauditar todo. Brecha P0: customer_service_contacts recomendado fuera en D50 aún pasa el guard vigente; falta aplicar/probar esa exclusión antes de entrenar. T0/F0, cortes, joins y métrica operativos siguen pendientes, además de límites actuariales/datos documentados. {v['passed']} controles propios y {ui['passed']} de lógica pasaron; dos figuras inspeccionadas, sin revisión independiente. Datos, índices, protocolo 1.8 y guard intactos. Sin entrenamiento o contactos. Ver incomplete_capital_review, validation_backlog_update y {decision}.\n''',encoding='utf-8')
    after=close/'after';after.mkdir()
    for name,p in paths.items():shutil.copy2(p,after/name)
    assert all(c.digest(c.ROOT/p)==sha for p,sha in protected.items()) and a.cap.manifest_ok(out)
    c.dump(close/'closure.json',{'created_utc':now,'decision_id':decision,'review':record,'validation_backlog':backlog_record,
        'manifest_sha256':c.digest(out/'manifest.json'),'all_protected_files_unchanged':True,
        'documents':{p.relative_to(c.ROOT).as_posix():c.digest(p) for p in list(paths.values())+[index]}})
    print(json.dumps({'decision':decision,'run':str(out),'closure':str(close),'status':'verified_review_only_no_data_changes'},ensure_ascii=False))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
