"""Cierre de la revisión de doce casos, sin cambios de datos o catálogos."""
from datetime import datetime,timezone
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import shutil
import sys

import review_discrepancies as a
import clean_data as c
import pandas as pd


def main(out):
    assert '--figures-inspected' in sys.argv,'Inspeccionar las dos figuras guardadas antes del cierre.'
    assert not (out/'manifest.json').exists(),'Corrida cerrada; no sobrescribir.'
    v=json.loads((out/'verification.json').read_text('utf-8'));ui=json.loads((out/'interface_verification.json').read_text('utf-8'))
    s=json.loads((out/'summary.json').read_text('utf-8'));protected=json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    assert v['failed']==ui['failed']==0 and ui['all_12_cases_exercised']
    assert all(c.digest(c.ROOT/path)==sha for path,sha in protected.items())
    f=pd.read_parquet(out/'tables/twelve_assessment.parquet')
    columns=['row_id','policy_id','line','source_table','reported_capital_CU','hypothetical_div1000_CU',
        'initial_row_id','initial_capital_CU','midterm_row_id','midterm_capital_CU','later_row_id','later_capital_CU',
        'later_source_table','test2025_reference','review_tier','capital_change_applied','actual_contract_reset_confirmed']
    proposed=f.loc[f.review_tier.eq('A_two_sided_sequence'),columns].copy()
    proposed['correction_authorized']=False;proposed['scenario']='retrospective_scale_only_NOT_APPLIED'
    assert len(proposed)==11 and 'C48613718' not in set(proposed.policy_id) and proposed.test2025_reference.sum()==1
    a.save(proposed,out,'proposed_11_scale_changes_NOT_APPLIED')
    report_path=out/'informe.html';report=report_path.read_text('utf-8')
    marker='<section><h2>Propuesta de tratamiento</h2>'
    assert report.count(marker)==1
    report=report.replace(marker,marker+'<p><a href="tables/proposed_11_scale_changes_NOT_APPLIED.csv">Lista congelada propuesta de once, sin aplicar ni autorizar</a> · <a href="tables/proposed_11_scale_changes_NOT_APPLIED.parquet">Lista tipada</a></p>')
    report_path.write_text(report,encoding='utf-8')
    for name in ['review_discrepancies.py','render_discrepancies.py','verify_discrepancies.py','verify_report.js','record_discrepancies.py']:
        source=a.BASE/name;dest=out/'source_snapshot'/name
        if dest.exists():assert c.digest(dest)==c.digest(source)
        else:shutil.copy2(source,dest)
    for name in ['clean_data.py','correct_capitals.py']:shutil.copy2(c.BASE/name,out/'source_snapshot'/name)
    for name in ['README.md','PRACTICAS_PRIORITARIAS.md']:
        shutil.copy2(c.ROOT/'Preparación/Antecedentes/IAA_IA'/name,out/'evidence'/('IAA_'+name))
    c.dump(out/'figure_inspection.json',{'status':'visually_inspected_by_Codex','method':'view_image of both actual saved PNG files',
        'figures':[{'file':name,'sha256':c.digest(out/name),'finding':'Labels and case identities legible; hypothetical markers distinct; observed and descriptive scopes explicit.'}
                   for name in ['figures/controls.png','figures/twelve_histories.png']],
        'real_browser_rendering_verified':False,'independent_validation':False})
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,tag,attrs):
            for key,value in attrs:
                if key in ['href','src']:self.links.append(value)
    links=Links();links.feed(report)
    assert all(ref=='manifest.json' or (out/ref).is_file() for ref in links.links)
    c.dump(out/'proposal_materialization_checks.json',{'passed':4,'failed':0,'checks':[
        {'check':'Exact 11 complete-context rows materialized, conditional case excluded','passed':True},
        {'check':'One test-2025 dependency identified; no authorization or application implied','passed':True},
        {'check':'Only evidence links added to report; embedded explorer data unchanged','passed':
         json.loads(re.search(r'<script id="reviewData" type="application/json">([\s\S]*?)</script>',report).group(1))==json.loads((out/'explorer_data.json').read_text('utf-8'))},
        {'check':'All local evidence links resolve, manifest generated at closure','passed':True}],
        'models_trained':False,'independent_validation':False})
    assert all(x['passed'] for x in json.loads((out/'proposal_materialization_checks.json').read_text('utf-8'))['checks'])
    now=datetime.now(timezone.utc).isoformat();rel=out.relative_to(c.ROOT).as_posix()
    paths={name:c.ROOT/'Preparación'/name for name in ['ESTADO_PROYECTO.json','MEMORIA_PROYECTO.md','DECISIONES.md']}
    paths['RUTAS_PROYECTO.json']=c.ROOT/'RUTAS_PROYECTO.json'
    # Read documentation at closure so unrelated work added since analysis began is retained.
    state=json.loads(paths['ESTADO_PROYECTO.json'].read_text('utf-8'))
    decisions=paths['DECISIONES.md'].read_text('utf-8');memory=paths['MEMORIA_PROYECTO.md'].read_text('utf-8')
    routes=json.loads(paths['RUTAS_PROYECTO.json'].read_text('utf-8'))
    decision='D'+str(max(map(int,re.findall(r'\bD(\d+)\b',decisions)))+1)
    close=a.BASE/'closures'/datetime.now(timezone.utc).strftime('closure_%Y%m%dT%H%M%SZ');close.mkdir(parents=True,exist_ok=False)
    for name,path in paths.items():shutil.copy2(path,close/('before_'+name))
    record={'decision_id':decision,'status':'verified_review_only_12_cases_no_data_changes','run':'../'+rel,
        'report':'../'+rel+'/informe.html','proposal':'../'+rel+'/proposal.json',
        'assessment':'../'+rel+'/tables/twelve_assessment.parquet','assessment_csv':'../'+rel+'/tables/twelve_assessment.csv',
        'proposed_11_NOT_APPLIED':'../'+rel+'/tables/proposed_11_scale_changes_NOT_APPLIED.parquet',
        'control_sequences':'../'+rel+'/tables/independent_normal_control_sequences.parquet','verification':'../'+rel+'/verification.json',
        'index':'../Hackaton/Semana 1/Revision_discrepancias_capital/current_run.json',
        'pending_in_retrospective_branch':587,'focus_rows':12,'focus_policies':12,'history_rows':63,'observed_claims':0,
        'control_sequences_count':9909,'control_policies':9702,'control_closer_to_initial_count':9909,
        'control_median_renewal_vs_initial_pct':2.0,'control_empirical_pattern_is_contract_confirmation':False,
        'proposed_complete_context_scale_scenario_rows':11,'conditional_initial_context_missing_rows':1,
        'conditional_policy_id':'C48613718','test2025_reference_policy_id':'C21091984','test2025_reference_rows':1,
        'other_pending_inventory_rows':575,'other575_individual_adjudication_performed':False,
        'technical_checks':v['passed'],'interface_logic_checks':ui['passed'],'proposal_materialization_checks':4,
        'all_12_cases_interaction_checked':True,'figures_visually_inspected':True,'browser_rendering_verified':False,
        'source_values_modified':False,'dataset_indexes_changed':False,'capital_changes':0,'pending_after_review':587,
        'application_authorized':False,'actual_contract_reset_confirmed':False,'source_units_confirmed':False,
        'models_trained':False,'independent_validation':False,'closure':'../'+close.relative_to(c.ROOT).as_posix()}
    c.dump(out/'closure_reference.json',{'decision_id':decision,'closure_workspace_relative':close.relative_to(c.ROOT).as_posix(),
                                      'status':'review_only_no_dataset_changes'})
    manifest={'created_utc':now,'type':'immutable_12_numeric_capital_conflict_review','files':[
        {'path':p.relative_to(out).as_posix(),'sha256':c.digest(p),'bytes':p.stat().st_size}
        for p in sorted(out.rglob('*')) if p.is_file()]}
    c.dump(out/'manifest.json',manifest)
    index=a.BASE/'current_run.json'
    c.dump(index,{'workspace_relative_run':rel,'decision_id':decision,'status':'verified_review_only_no_data_changes',
        'report_workspace_relative':rel+'/informe.html','focus_rows':12,'retrospective_pending':587,'capital_changes':0})
    state['numeric_capital_discrepancy_review']=record;state['memory_as_of']=now
    routes['week_1_numeric_capital_discrepancy_review_index']='Hackaton/Semana 1/Revision_discrepancias_capital/current_run.json'
    c.dump(paths['ESTADO_PROYECTO.json'],state);c.dump(paths['RUTAS_PROYECTO.json'],routes)
    text=f'''\n\n### {decision}, doce discrepancias numéricas dentro de los 587 capitales pendientes, 16 de octubre de 2026, America/Bogota\n\nEl participante pidió continuar la revisión de los 587 restantes empezando por los doce conflictos numéricos, sin modificar datos. La corrida ../{rel} congela exactamente los doce D48 que quedaron fuera de CAP02R y siguen pendientes: doce pólizas de contenidos, 63 periodos completos, ningún siniestro observado. Dos filas pendientes son de 2022, nueve de 2023 y una de 2024. Se conserva el inventario íntegro de los otros 575, sin adjudicación individual nueva de ese bloque. Se usan el catálogo retrospectivo CAP02R y los capitales originales para distinguir evidencia observada de reparaciones.\n\nEn los doce hay una ampliación de capital durante el año anterior (+21,98% a +55,83%) y una renovación el 1 de enero. /1000 dejaría esa renovación entre +1,69% y +2,42% frente al nivel previo a ampliar, y entre −16,24% y −34,53% frente al último capital ampliado. El siguiente periodo normal está +1,57% a +2,16% sobre la hipótesis. La discrepancia de nivel puede coexistir con un error de escala; no obligar a que el capital hipotético iguale al último observado ni corregir los segmentos normales para fabricar continuidad.\n\nComo contraste descriptivo se seleccionaron 9.909 secuencias de 9.702 otras pólizas de contenidos, excluyendo por completo las doce, con dos segmentos consecutivos en el año, mid_term_change, renovación el 1 de enero, campos D34 completos e iguales y tres capitales originales positivos de hasta un millón CU. No se exigió una reversión al seleccionar ni se usaron siniestros. En las 9.909, la renovación está más cerca del nivel inicial que del ampliado: mediana +2,00% sobre inicial (p05 +1,78%, p95 +2,22%) y −27,09% frente al ampliado. Incluye renovaciones test 2025 identificadas por año. El patrón es compatible con lógica del generador o cambios contractuales omitidos; no confirma contrato, unidad, causalidad o probabilidad de error. No son ensayos independientes, pues hay pólizas repetidas.\n\nSe proponen once filas con contexto de las cuatro etapas conocido e igual como escenario retrospectivo /1000 separado, sin aplicar o autorizar. Lista congelada en tables/proposed_11_scale_changes_NOT_APPLIED. La duodécima, C48613718/C01596694, queda condicionada porque security_level es nulo en la referencia inicial de 28.800 CU: después hay 40.500, la fila pendiente 29.300.000 y el periodo posterior 29.900. La referencia 2021 de 28.200 con locks está a 730 días, no sustituye el faltante del segmento 2022 ni pasa automáticamente el límite 400 días. C21091984/C02362784 pertenece a los once y usa respaldo test 2025: 25.700→31.900→26.200.000→26.700. Conservar señal de dependencia posterior, sin presentarla como información conocida al inicio 2024. Todas las anclas posteriores de las doce eran futuras en la fecha corregible.\n\nC49279780 muestra 66.000 CU en 2021, luego 101.000 durante siete días y 67.300.000 en 2022; /1000 daría 67.300 y 2023 observa 68.700. La prima del tramo corto es 253,24 frente a 169,47 del anterior; el capital es un límite y no se anualiza, ni se infiere su valor mediante prorrateo de prima sin base confirmada. Las primas aumentan en los doce pares de ampliación, con otros factores y descuentos visibles que impiden declarar todos los factores tarifarios constantes. No hay siniestros para confirmar escala; ausencia observada no es riesgo cero.\n\nLos 587 permanecen pendientes en CAP02R; la base sigue con 1.454. Los otros 575 conservan 109 casos con apoyo posterior y cambio previo de contexto, 108 sin cifra habitual original, 2 dependencias CAP01 residuales, 16 T/W, 202 faltantes y 138 otras discrepancias. Próximo grupo sugerido: los 109, revisando mudanzas y cambios de riesgo; no ampliar cohortes con anclas creadas por CAP02R. No se añade regla de corrección, marca o predictor ni se toca protocolo 1.6.\n\nPasaron {v['passed']} controles propios, {ui['passed']} de lógica de las doce vistas y cuatro de materialización/enlaces de la propuesta. Se releyeron los campos completos de los 63 periodos, todos los pares de las cuatro etapas y las 9.909 secuencias de control contra fuentes originales; importes, campos, fechas, IDs, cohortes, índices de ambas ramas y manifiestos protegidos coinciden. Dos PNG inspeccionados realmente con view_image, sin renderizado real de navegador o validación independiente acreditados. La IA preparó código, análisis y comprobaciones; la autorización de aplicar estas once o doce aún no existe. Sin entrenamiento, cambio de datos, proveedor externo, publicación o contacto a terceros. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad y límites. Se conservan las aportaciones y decisiones de trabajos paralelos presentes al cierre. Consultar numeric_capital_discrepancy_review.\n'''
    paths['DECISIONES.md'].write_text(decisions.rstrip()+text,encoding='utf-8')
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip()+f'\n\nDoce discrepancias numéricas revisadas, {decision}: [informe con todos los casos](../{rel}/informe.html), [propuesta sin aplicar](../{rel}/proposal.json). Son doce pólizas de contenidos, 63 periodos y cero siniestros observados. La hipótesis /1000 encaja con el nivel previo a ampliación (+1,69–2,42%) aunque baja 16,24–34,53% frente al último capital ampliado. En 9.909 secuencias de 9.702 otras pólizas con capitales originales normales y contexto completo se repite la vuelta al nivel inicial, con mediana +2,00%; patrón descriptivo, no confirmación contractual. Se propone un escenario de once con contexto completo; C48613718 queda condicionado por security_level faltante en el segmento inicial. C21091984 usa test 2025. No reparar el nivel normal intermedio ni anualizar capital por exposición. Pasaron {v["passed"]} controles de datos, {ui["passed"]} de lógica y cuatro de propuesta/enlaces. Ambos catálogos intactos: 587 pendientes en retrospectiva y 1.454 en la base. Los otros 575 quedan inventariados sin adjudicación nueva; próximo grupo sugerido 109 con cambios de contexto. Protocolo 1.6 sin cambios, sin entrenamiento ni revisión independiente. Ver numeric_capital_discrepancy_review y {decision}.\n',encoding='utf-8')
    after=close/'after';after.mkdir()
    for name,path in paths.items():shutil.copy2(path,after/name)
    assert all(c.digest(c.ROOT/path)==sha for path,sha in protected.items())
    assert a.cap.manifest_ok(out)
    c.dump(close/'closure.json',{'created_utc':now,'decision_id':decision,'review':record,'manifest_sha256':c.digest(out/'manifest.json'),
        'all_protected_files_and_dataset_indexes_unchanged':True,
        'documents':{path.relative_to(c.ROOT).as_posix():c.digest(path) for path in list(paths.values())+[index]}})
    print(json.dumps({'decision':decision,'run':str(out),'report':str(out/'informe.html'),'closure':str(close),
                      'status':'verified_review_only_no_data_changes'},ensure_ascii=False))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
