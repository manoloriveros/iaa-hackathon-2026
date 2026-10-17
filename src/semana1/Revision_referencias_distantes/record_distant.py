"""Cierre de revisión48 y propuesta46; no activa la regla ni modifica datos."""
from datetime import datetime,timezone
from pathlib import Path
from html.parser import HTMLParser
import json,re,shutil,sys
import review_distant as a
import clean_data as c
def main(out):
    assert '--figures-inspected' in sys.argv and not (out/'manifest.json').exists()
    v=json.loads((out/'verification.json').read_text('utf-8'));ui=json.loads((out/'interface_verification.json').read_text('utf-8'));s=json.loads((out/'summary.json').read_text('utf-8'))
    protected=json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    assert v['failed']==ui['failed']==0 and ui['all_48_rows_exercised'] and ui['all_12_cases_exercised']
    assert all(c.digest(c.ROOT/p)==sha for p,sha in protected.items())
    for name in ['review_distant.py','render_distant.py','verify_distant.py','verify_report.js','record_distant.py']:
        source=a.BASE/name;dest=out/'source_snapshot'/name
        if dest.exists():assert c.digest(dest)==c.digest(source)
        else:shutil.copy2(source,dest)
    for name in ['clean_data.py','correct_capitals.py']:shutil.copy2(c.BASE/name,out/'source_snapshot'/name)
    for name in ['README.md','PRACTICAS_PRIORITARIAS.md']:shutil.copy2(c.ROOT/'Preparación/Antecedentes/IAA_IA'/name,out/'evidence'/('IAA_'+name))
    c.dump(out/'figure_inspection.json',{'status':'visually_inspected_by_Codex','method':'view_image of both actual saved final PNG files',
        'figures':{name:c.digest(out/name) for name in ['figures/distant_evidence.png','figures/histories.png']},
        'finding':'Labels and counts legible; all hypothetical values distinct; first-complete anchors highlighted, including the two nearer numeric conflicts. Logarithmic axes explicit.',
        'real_browser_rendering_verified':False,'independent_validation':False})
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.refs=[]
        def handle_starttag(self,tag,attrs):self.refs += [v for k,v in attrs if k in ['href','src']]
    report=(out/'informe.html').read_text('utf-8');parser=Links();parser.feed(report)
    assert all(ref=='manifest.json' or (out/ref).is_file() for ref in parser.refs)
    assert json.loads(re.search(r'<script id="reviewData" type="application/json">([\s\S]*?)</script>',report).group(1))==json.loads((out/'explorer_data.json').read_text('utf-8'))
    c.dump(out/'final_artifact_checks.json',{'passed':3,'failed':0,'local_links_resolve_with_manifest_at_closure':True,
        'embedded_payload_matches_stored_verified_payload':True,'protected_files_unchanged':True,'report_sha256':c.digest(out/'informe.html')})
    paths={name:c.ROOT/'Preparación'/name for name in ['ESTADO_PROYECTO.json','MEMORIA_PROYECTO.md','DECISIONES.md']};paths['RUTAS_PROYECTO.json']=c.ROOT/'RUTAS_PROYECTO.json'
    state=json.loads(paths['ESTADO_PROYECTO.json'].read_text('utf-8'));routes=json.loads(paths['RUTAS_PROYECTO.json'].read_text('utf-8'));memory=paths['MEMORIA_PROYECTO.md'].read_text('utf-8');decisions=paths['DECISIONES.md'].read_text('utf-8')
    decision='D'+str(max(map(int,re.findall(r'\bD(\d+)\b',decisions)))+1);now=datetime.now(timezone.utc).isoformat();rel=out.relative_to(c.ROOT).as_posix()
    close=a.BASE/'closures'/datetime.now(timezone.utc).strftime('closure_%Y%m%dT%H%M%SZ');close.mkdir(parents=True,exist_ok=False)
    for name,p in paths.items():shutil.copy2(p,close/('before_'+name))
    record={'decision_id':decision,'workspace_relative_run':rel,'created_utc':now,'status':'verified_review_only_no_data_changes',
        'report_workspace_relative':rel+'/informe.html','cohort_rows':48,'policies':48,'by_line':s['by_line'],
        'history_rows':210,'original_reference_pairs':162,'proposed_candidate_rows_NOT_APPLIED':46,'candidate_by_line':s['candidate_by_line'],
        'held_numeric_conflict_rows':2,'held_policies':['C50633171','C56600576'],'candidate_gap_min_days':427,'candidate_gap_max_days':731,
        'candidate_prior_anchors':21,'candidate_future_anchors':25,'candidate_test2025_anchors':7,'candidate_test2025_anchor_by_line':s['test2025_candidate_anchor_by_line'],
        'focus_test2025_rows':13,'candidate_rule':'DIST01-R proposal v1','proposed_window_calendar_years':2,'live_400day_rule_changed':False,
        'selected_candidate_edges':92,'selected_candidate_edges_without_gap':72,'selected_candidate_edges_with_CAL00_gap':20,
        'claims':7,'claims_in_focus_periods':0,'capital_changes':0,'correction_authorized':False,
        'retrospective_pending_unchanged':467,'base_pending_unchanged':1454,'other_pending_not_adjudicated':419,
        'keep_108_pending_unchanged':True,'models_trained':False,'independent_validation':False,'real_browser_rendering_verified':False,
        'own_source_checks':v['passed'],'minimal_DOM_checks':ui['passed'],'final_artifact_checks':3,
        'proposal_workspace_relative':rel+'/tables/proposed_scale_changes_NOT_APPLIED.parquet',
        'proposal_sha256':c.digest(out/'tables/proposed_scale_changes_NOT_APPLIED.parquet'),
        'closure_workspace_relative':close.relative_to(c.ROOT).as_posix()}
    c.dump(out/'closure_record.json',record)
    c.dump(out/'manifest.json',{'created_utc':now,'type':'immutable_48_distant_original_capital_review','files':[
        {'path':p.relative_to(out).as_posix(),'sha256':c.digest(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()]})
    index=a.BASE/'current_run.json';c.dump(index,record)
    state['distant_capital_review']=record
    state['incomplete_capital_review']['followup_distant_review_decision']=decision
    state['incomplete_capital_review']['followup_candidate_rows_NOT_APPLIED']=46
    state['memory_as_of']=now;routes['week_1_distant_capital_review_index']='Hackaton/Semana 1/Revision_referencias_distantes/current_run.json'
    c.dump(paths['ESTADO_PROYECTO.json'],state);c.dump(paths['RUTAS_PROYECTO.json'],routes)
    text=f'''\n\n### {decision}, 48 referencias distantes: propuesta de 46 y dos ampliaciones pendientes, 16 de octubre de 2026, America/Bogota

El participante pidió revisar en detalle las 48 filas completas con referencias a más de 400 días, comparar historias y proponer cuándo corregir escala, sin modificar datos. La corrida ../{rel} congela exactamente el subgrupo de D56: 48 pólizas, 18 edificios y 30 contenidos, 210 periodos completos y 162 referencias originales. Los capitales de toda su historia siguen iguales a los originales. El criterio operativo de 400 días y protocolo 1.8 permanecen sin cambios; no se activa regla o capa de datos.

Se propone DIST01-R v1, limitada a esta cohorte: elegir en cada sentido la referencia original habitual más próxima con todos los campos D34 informados, antes de comprobar contexto o capital. Debe tener contexto completo igual al de la fila, distancia mayor de 400 días y como máximo dos años calendario, una sola fila original intermedia de escala habitual con faltantes pero sin cambios conocidos, razón entre hipótesis /1000 y ancla entre 0,90–1,10 y cada paso monetario dentro de esa banda. Conservar fechas sin solapes o huecos nuevos, admitiendo solo la omisión CAL00 ya conocida del 31-12-2024 como pendiente. Nunca imputar la fila intermedia, usar reparaciones como referencias originales o saltar una referencia completa contradictoria. Dos años calendario pueden ser 731 días; el criterio no es 730 días fijos.

Con ese criterio se proponen 46 filas para una eventual operación retrospectiva /1000 separada: 18 edificios y 28 contenidos. Sus anclas están a 427–731 días, 21 anteriores y 25 posteriores; siete posteriores son test 2025 (un edificio, seis contenidos). Son distintos de las 13 filas de la cohorte que pertenecen a test 2025. Los 92 pasos monetarios crecen entre 1,59% y 3,30%; 72 enlaces son contiguos y 20 conservan el día CAL00 omitido. No se afirma cobertura completa ni una ley de inflación. La propuesta se aprende y examina retrospectivamente: las fechas anteriores de algunas anclas no aprueban disponibilidad F0 o un backtest causal. La nueva regla no se valida globalmente para otras cohortes.

B02977304: 187.000.000 CU en 2021 con contexto completo, 193.000 con alarmas ausentes en 2022 y 198.000 completo en 2023; se propone 187.000 con ancla a 730 días, conservando el nulo. B05543458 tiene 385.000 completo en enero 2023, 397.000 incompleto en 2024 y 409.000.000 completo en 2025; propuesta 409.000 con ancla anterior de 707 días. B55826538 propone 211.000 desde 211.000.000 con 217.000 intermedios y ancla test 2025 de 224.000, señalada como futura. C62678958 propone 34.100 desde 34.100.000 con 32.800 completos en 2023 y 33.400 intermedios con seguridad/bienes de valor ausentes; se mantienen ambos nulos. Igualdad de extremos registrados no prueba toda circunstancia intermedia: days_unoccupied cambia en los 18 pares de edificios, y los demás factores tarifarios no se declaran constantes.

C50633171/C00502745 queda pendiente: 27.200.000 en 2021, 27.700 incompleto al iniciar 2022, ampliación completa de 39.400 en mayo 2022 y 28.300 en 2023. La primera referencia completa está a 488 días; 27.200 hipotéticos quedan 30,96% por debajo de 39.400. C56600576/C00399729 registra 25.700.000, después 26.200 incompleto, ampliación completa a 37.700 en septiembre 2022 y 26.700 en 2023. Su primera referencia completa está a 619 días y la hipótesis 25.700 queda 31,83% por debajo. Elegir solo 2023 ocultaría esos niveles. El patrón puede coexistir con un error de escala, pero requiere revisión específica de la ampliación/reversión; no se confirma que los importes altos sean correctos ni se cambia el capital ampliado.

La lista propuesta de 46 queda materializada, con ancla, dirección, distancia, señal 2025 y falsos de aplicación/autorización. Los dos conflictos tienen inventario propio. Todos los 467 pendientes siguen pendientes, incluidos los 108 conservados por el participante, los dos aquí retenidos y las otras 154 filas de contexto incompleto. Los otros 419 ajenos a esta cohorte no reciben adjudicación nueva. La base conserva 1.454 pendientes y las 3.060 correcciones heredadas de la rama retrospectiva no cambian.

Se conservan siete siniestros, ninguno ocurrido en los 48 periodos pendientes. CL74020899 tiene incurrido de 47.174,97 CU en la fila intermedia original de B05390516; no decide la escala ni reconstruye el atributo desconocido. No se modifican siniestros, importes, etiquetas, fechas o exposición. El maestro de direcciones no aporta una valoración contractual histórica.

Pasaron {v['passed']} controles propios de fuentes y {ui['passed']} de lógica sobre las 48 vistas y doce casos, más tres controles finales de artefactos. Se releen todos los campos de historias/direcciones, todas las referencias, primera referencia completa, pasos de capital/calendario, 467 pendientes y los dos controles negativos reales. Ambos PNG se inspeccionaron realmente; sin navegador renderizado o revisión independiente acreditados. Un primer intento del verificador accedió a row_id como columna después de indexarlo; se conserva ese código/error y se corrigió la comprobación antes de pasar la suite, sin efecto sobre análisis o datos. Los originales, archivos del catálogo, ambos índices de datos, protocolo 1.8, guard y manifiestos previos mantienen sus hashes. Solo se actualizan evidencia, memoria, estado y rutas. Sin entrenamiento, proveedor externo, publicación, contacto a terceros o delegación. La IA preparó análisis, propuesta y controles propios; no se atribuye autorización de aplicar. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad, límites y responsabilidad. Ver distant_capital_review.
'''
    paths['DECISIONES.md'].write_text(decisions.rstrip()+text,encoding='utf-8')
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip()+f'''\n\n48 referencias distantes revisadas, {decision}: [informe con doce casos y explorador](../{rel}/informe.html), [46 propuestas sin aplicar](../{rel}/tables/proposed_scale_changes_NOT_APPLIED.csv). Son 210 periodos y 162 referencias originales, sin reparaciones previas en estas historias. DIST01-R candidata propone /1000 para 46 filas (18 edificios, 28 contenidos): extremos D34 completos/iguales, primera referencia completa elegida antes del importe, más de 400 días y hasta dos años calendario, una fila intermedia incompleta sin cambios conocidos y todos los pasos de importe compatibles. Hay 21 anclas anteriores y 25 posteriores, siete test 2025 (1/6), distancias 427–731 días. Los 20 huecos CAL00 de los 92 enlaces se conservan. C50633171 y C56600576 quedan pendientes por ampliaciones completas intermedias a 39.400/37.700 que contradicen la hipótesis de 27.200/25.700 frente a la referencia completa más próxima. No saltarlas para usar solo 2023. Se conservan nulos, otros atributos y siete siniestros sin incidencia en los 48 periodos. Pasaron {v['passed']} controles propios y {ui['passed']} de lógica, dos figuras inspeccionadas, sin revisión independiente. Ningún dato o índice operativo cambia: siguen 467 pendientes retrospectivos y 1.454 en la base, incluidos los 108 ya conservados. El límite operativo de 400 días y protocolo 1.8 siguen iguales; la propuesta no se activa ni generaliza a otras cohortes. Sin entrenamiento o contactos. Ver distant_capital_review y {decision}.\n''',encoding='utf-8')
    after=close/'after';after.mkdir()
    for name,p in paths.items():shutil.copy2(p,after/name)
    assert all(c.digest(c.ROOT/p)==sha for p,sha in protected.items()) and a.cap.manifest_ok(out)
    c.dump(close/'closure.json',{'created_utc':now,'decision_id':decision,'review':record,'manifest_sha256':c.digest(out/'manifest.json'),
        'all_protected_files_unchanged':True,'documents':{p.relative_to(c.ROOT).as_posix():c.digest(p) for p in list(paths.values())+[index]}})
    print(json.dumps({'decision':decision,'run':str(out),'closure':str(close),'status':'verified_review_only_no_data_changes'},ensure_ascii=False))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
