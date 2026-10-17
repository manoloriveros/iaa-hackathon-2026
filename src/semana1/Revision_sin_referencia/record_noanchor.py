"""Cierra revisión de los108 sin referencia; no modifica capas o protocolo."""
from datetime import datetime,timezone
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import shutil
import sys
import review_noanchor as a
import clean_data as c

def main(out):
    assert '--figures-inspected' in sys.argv
    assert not (out/'manifest.json').exists(),'Corrida cerrada: no sobrescribir.'
    v=json.loads((out/'verification.json').read_text('utf-8'));ui=json.loads((out/'interface_verification.json').read_text('utf-8'))
    s=json.loads((out/'summary.json').read_text('utf-8'));protected=json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    assert v['failed']==ui['failed']==0 and ui['all_108_rows_exercised'] and ui['all_12_cases_exercised']
    assert all(c.digest(c.ROOT/p)==sha for p,sha in protected.items())
    for name in ['review_noanchor.py','render_noanchor.py','verify_noanchor.py','verify_report.js','record_noanchor.py']:
        source=a.BASE/name;dest=out/'source_snapshot'/name
        if dest.exists():assert c.digest(source)==c.digest(dest)
        else:shutil.copy2(source,dest)
    for name in ['clean_data.py','correct_capitals.py']:shutil.copy2(c.BASE/name,out/'source_snapshot'/name)
    for name in ['README.md','PRACTICAS_PRIORITARIAS.md']:
        shutil.copy2(c.ROOT/'Preparación/Antecedentes/IAA_IA'/name,out/'evidence'/('IAA_'+name))
    c.dump(out/'figure_inspection.json',{'status':'visually_inspected_by_Codex','method':'view_image of both actual saved PNG files; final capital_ranges version inspected after label refinement.',
        'figures':{name:c.digest(out/name) for name in ['figures/evidence_map.png','figures/capital_ranges.png']},
        'finding':'Group counts and labels legible, all hypotheses distinguished from current capital, log axes and other coverage explicitly marked; boxplot limits explained in report.',
        'real_browser_rendering_verified':False,'independent_validation':False})
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.refs=[]
        def handle_starttag(self,tag,attrs):self.refs += [v for k,v in attrs if k in ['href','src']]
    report=(out/'informe.html').read_text('utf-8');parser=Links();parser.feed(report)
    assert all(ref=='manifest.json' or (out/ref).is_file() for ref in parser.refs)
    assert json.loads(re.search(r'<script id="reviewData" type="application/json">([\s\S]*?)</script>',report).group(1))==json.loads((out/'explorer_data.json').read_text('utf-8'))
    c.dump(out/'final_artifact_checks.json',{'passed':3,'failed':0,'all_local_links_resolve_except_manifest_created_at_closure':True,
        'final_embedded_payload_equals_verified_stored_payload':True,'protected_files_unchanged':True,
        'report_sha256':c.digest(out/'informe.html'),'own_verification_sha256':c.digest(out/'verification.json'),
        'interface_verification_sha256':c.digest(out/'interface_verification.json'),'real_browser_rendering_verified':False})
    paths={name:c.ROOT/'Preparación'/name for name in ['ESTADO_PROYECTO.json','MEMORIA_PROYECTO.md','DECISIONES.md']}
    paths['RUTAS_PROYECTO.json']=c.ROOT/'RUTAS_PROYECTO.json'
    # Read at closure, retaining the current CAP04R and any unrelated documented work.
    state=json.loads(paths['ESTADO_PROYECTO.json'].read_text('utf-8'));routes=json.loads(paths['RUTAS_PROYECTO.json'].read_text('utf-8'))
    decisions=paths['DECISIONES.md'].read_text('utf-8');memory=paths['MEMORIA_PROYECTO.md'].read_text('utf-8')
    decision='D'+str(max(map(int,re.findall(r'\bD(\d+)\b',decisions)))+1)
    now=datetime.now(timezone.utc).isoformat();rel=out.relative_to(c.ROOT).as_posix()
    close=a.BASE/'closures'/datetime.now(timezone.utc).strftime('closure_%Y%m%dT%H%M%SZ');close.mkdir(parents=True,exist_ok=False)
    for name,p in paths.items():shutil.copy2(p,close/('before_'+name))
    record={'decision_id':decision,'workspace_relative_run':rel,'created_utc':now,'status':'verified_review_only_no_data_changes',
        'report_workspace_relative':rel+'/informe.html','cohort_rows':108,'policies':107,'by_line':s['by_line'],
        'history_rows':108,'singleton_policies':106,'two_period_policy':'B67263929','test2025_focus_rows':107,'train2024_focus_rows':1,
        'group_rows':s['group_rows'],'original_normal_own_policy_references':0,'same_line_same_customer_address_references':0,
        'rows_with_other_coverage_same_customer_address_interval':71,'other_linked_policies':72,'other_linked_history_rows':79,
        'linked_comparison_rows':81,'own_claims':0,'linked_claims':0,'context_missing_rows':5,
        'descriptive_peer_period_rows':240141,'hypothetical_inside_matched_peer_range_rows':108,
        'proposed_action':'KEEP_ALL_108_PENDING_NO_AUTOMATIC_REPAIR','automatic_repair_candidates':0,
        'correction_authorized':False,'capital_changes':0,'retrospective_pending_unchanged':467,'base_pending_unchanged':1454,
        'other_pending_not_adjudicated':359,'dataset_indexes_changed':False,'protocol_1_8_changed':False,
        'models_trained':False,'independent_validation':False,'real_browser_rendering_verified':False,
        'own_source_checks':v['passed'],'minimal_DOM_checks':ui['passed'],'final_artifact_checks':3,
        'closure_workspace_relative':close.relative_to(c.ROOT).as_posix()}
    c.dump(out/'closure_record.json',record)
    c.dump(out/'manifest.json',{'created_utc':now,'type':'immutable_108_capital_no_original_anchor_review','files':[
        {'path':p.relative_to(out).as_posix(),'sha256':c.digest(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()]})
    index=a.BASE/'current_run.json';c.dump(index,record)
    state['no_original_capital_review']=record;state['memory_as_of']=now
    routes['week_1_no_original_capital_review_index']='Hackaton/Semana 1/Revision_sin_referencia/current_run.json'
    c.dump(paths['ESTADO_PROYECTO.json'],state);c.dump(paths['RUTAS_PROYECTO.json'],routes)
    text=f'''\n\n### {decision}, revisión de 108 capitales sin referencia original habitual, 16 de octubre de 2026, America/Bogota

El participante pidió comparar historiales, casos y tratamiento sin modificar datos. La corrida ../{rel} congela exactamente el grupo C de D48 que sigue pendiente en CAP04R: 108 filas de 107 pólizas, 62 edificios y 46 contenidos. Hay 107 filas test 2025 (61/46) y una de edificios train 2024. 106 pólizas tienen solo un periodo publicado y B67263929 tiene dos, ambos altos. Los 108 periodos completos conservan sus capitales originales, sin reparaciones heredadas en su historia. 107 son altas con renewal_count=0; una es renovación con contador 1. No hay ancla habitual original en ninguna póliza.

Se retienen los 79 periodos completos de 72 otras pólizas de hogar vinculadas y 81 comparaciones. Para 71 filas existe otra cobertura del mismo cliente, dirección e intervalo, siempre de distinto ramo. No hay referencia de otra póliza que coincida en ramo/cliente/dirección. El desglose excluyente es dos filas con dos periodos altos (una póliza), 69 filas únicas con otra cobertura del mismo cliente, una con solo dirección compartida por otro cliente y 36 sin otra póliza de hogar vinculada.

B67263929 registra 435.000.000 CU desde 21-09-2024 y 448.000.000 al renovar en 2025; /1000 daría 435.000 y 448.000. El crecimiento de 2,99% es idéntico bajo ambas escalas y no identifica unidad absoluta. Contenidos C07190342 registra 43.100 y 43.900, otro objeto y contrato. No corregir uno por supuesto para justificar el otro. B00774853 registra 209.000.000 y su otra cobertura C75353570, 37.800; no copiar el límite de bienes al edificio ni imponer una razón fija. C52311091 registra 53.600.000; C88435910 en A6437358 tiene 36.300/37.000/37.800 pero otro cliente, sin equivalencia de bienes o contrato.

Se comparan 240.141 periodos de otras pólizas con capital original positivo igual al vigente y bajo los umbrales históricos de cribado (10.000.000 edificios, 1.000.000 contenidos), por tabla/año/alta-renovación. Se seleccionan sin pérdidas, prima o parecido favorable a /1000. Hay pólizas repetidas; no son ensayos independientes. Los 108 hipotéticos quedan dentro del rango de su cohorte: 128.000–556.000 CU edificios y 10.700–126.200 contenidos. Los valores vigentes superan el máximo comparable. Es evidencia de plausibilidad de escala, no confirmación de 108 límites contractuales. No recortar a percentiles, invertir la tarifa, anualizar capital por exposición o usar un umbral como máximo contractual.

Cinco filas tienen además faltantes de contexto: smoke_alarms en dos edificios, security_level en dos contenidos y high_value_items en otro. Se mantienen nulos; los problemas se solapan con falta de ancla. No hay expedientes observados en las 107 pólizas o 72 vinculadas; gran parte es test 2025 sin resultados publicados. No convertir ausencia de observaciones en riesgo cero, ni crear objetivos, descartar filas de test o alterar sus identificadores. El maestro de direcciones no ofrece valoración de reconstrucción/bienes ni fechas de vigencia.

Se propone conservar los 108 pendientes, con cero candidatos a corrección automática bajo la evidencia actual. Haría falta confirmar unidad/serialización o documentos contractuales para las filas exactas. Una eventual sensibilidad /1000 o capital desconocido para el modelo requiere una instrucción posterior; este informe no crea esa capa ni predictor. Los otros 359 quedan inventariados sin nueva adjudicación. Continúan 467 pendientes en retrospectiva y 1.454 en la base; las 3.060 correcciones anteriores no se tocan.

Pasaron {v['passed']} controles propios de fuente y {ui['passed']} de lógica, recorriendo 108 vistas y doce casos. Se reconstruyen por otro algoritmo los vínculos y toda la población comparable; se releen todos los campos publicados de historias/direcciones y consultas vacías de siniestros. Ambos PNG se inspeccionaron; sin renderizado real de navegador o revisión independiente acreditados. Tres controles finales comprueban enlaces, payload y hashes. Originales, archivos del catálogo, ambos índices de datos, protocolo 1.8, CAP04R y D48 conservan sus hashes. Se actualizan solo evidencia, memoria, estado y rutas. Sin entrenamiento, T0/F0 nuevo, proveedor externo, publicación, contacto a terceros o delegación. La IA preparó análisis/código/controles propios; no se atribuye autorización humana de corregir estos 108. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad, límites y responsabilidad. Consultar no_original_capital_review.
'''
    paths['DECISIONES.md'].write_text(decisions.rstrip()+text,encoding='utf-8')
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip()+f'''\n\n108 capitales sin referencia original revisados, {decision}: [informe con doce casos y explorador](../{rel}/informe.html), [tratamiento por fila sin aplicar](../{rel}/tables/proposed_treatment_NOT_APPLIED.csv). Son 107 pólizas (106 con una fila, B67263929 con dos periodos), 62 filas edificios y 46 contenidos; 107 test 2025 y una train 2024. No hay ancla habitual original en sus propias historias. Se comparan 79 periodos de 72 otras pólizas: 71 filas tienen otro ramo del mismo cliente/dirección/intervalo; ninguna tiene referencia del mismo ramo/cliente/dirección. C52311091 comparte dirección con otro cliente, sin equivalencia de bienes. B67263929 tiene 435.000.000→448.000.000; /1000 conserva el aumento de 2,99% y no identifica unidad absoluta. Los 108 hipotéticos quedan dentro del rango de 240.141 periodos comparables por tabla/año/alta-renovación, evidencia descriptiva insuficiente para corregir contratos. Cinco faltantes de contexto conservados; cero expedientes observados no significa riesgo cero. Se recomienda mantener los 108 pendientes, sin escenario nuevo ni cambio de datos o protocolo 1.8. Los otros 359 quedan inventariados sin adjudicación nueva. Pasaron {v['passed']} controles de fuente, {ui['passed']} de lógica y tres finales; dos figuras inspeccionadas, sin revisión independiente. Siguen 467 pendientes retrospectivos y 1.454 en la base, con todos los originales/derivados/índices intactos. Sin entrenamiento o contactos. Ver no_original_capital_review y {decision}.\n''',encoding='utf-8')
    after=close/'after';after.mkdir()
    for name,p in paths.items():shutil.copy2(p,after/name)
    assert all(c.digest(c.ROOT/p)==sha for p,sha in protected.items()) and a.cap.manifest_ok(out)
    c.dump(close/'closure.json',{'created_utc':now,'decision_id':decision,'review':record,'manifest_sha256':c.digest(out/'manifest.json'),
        'all_protected_data_and_dataset_indexes_unchanged':True,'documents':{p.relative_to(c.ROOT).as_posix():c.digest(p) for p in list(paths.values())+[index]}})
    print(json.dumps({'decision':decision,'run':str(out),'closure':str(close),'status':'verified_review_only_no_data_changes'},ensure_ascii=False))

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
