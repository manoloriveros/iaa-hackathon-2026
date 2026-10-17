"""Cierre documental de revisión; no activa la propuesta ni cambia índices de datos."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import shutil
import sys
import review_endorsements as a
import clean_data as c


def main(out):
    assert not (out/'manifest.json').exists(), 'No sobrescribir una corrida cerrada.'
    v = json.loads((out/'verification.json').read_text('utf-8'))
    assert v['failed'] == 0 and v['passed'] == 522 and v['capital_changes'] == 0
    assert all(c.digest(out/path) == sha for path,sha in v['verified_files'].items())
    protected = json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    assert all(c.digest(c.ROOT/path) == sha for path,sha in protected.items())
    for name in ['review_endorsements.py','render_endorsements.py','verify_endorsements.py','record_endorsements.py']:
        dest = out/'source_snapshot'/name
        if dest.exists(): assert c.digest(dest) == c.digest(a.BASE/name)
        else: shutil.copy2(a.BASE/name,dest)
    for name in ['clean_data.py','correct_capitals.py']:
        shutil.copy2(c.BASE/name,out/'source_snapshot'/name)
    for name in ['README.md','PRACTICAS_PRIORITARIAS.md']:
        shutil.copy2(c.ROOT/'Preparación/Antecedentes/IAA_IA'/name,out/'evidence'/('IAA_'+name))
    c.dump(out/'figure_inspection.json',{'status':'inspected_by_Codex_in_view_image','images':{
        name:c.digest(out/name) for name in ['figures/histories.png','figures/peer_comparison.png']},
        'finding':'Both PNGs actually viewed. Amounts, log/linear axes and hypothetical2021 markers legible; all2022/2023 capitals preserved. Peer plots label2305 other policies, both focus lines and exploratory limitations.',
        'real_browser_rendering_verified':False,'human_or_independent_validation':False})
    c.dump(out/'tooling_notes.json',{'verification_attempt_1':{
        'source':'evidence/verify_attempt_1.py','result':'evidence/verification_attempt_1.json',
        'issue':'Initial link checker expected its own not-yet-written verification.json to exist. All data/cohort checks had passed before this artifact-order check.',
        'resolution':'Allow verification.json until the verifier writes it; check it exists again at closure. No change to analysis or data.'},
        'exploratory_probe_note':'An initial ad hoc original-cohort probe used boolean inversion on a shifted series with boundary NaN and raised TypeError. Main source uses explicit eq(False); no cohort or dataset output from that probe was used.'})
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.refs=[]
        def handle_starttag(self,tag,attrs):self.refs += [val for key,val in attrs if key in ['href','src']]
    parser=Links();parser.feed((out/'informe.html').read_text('utf-8'))
    assert all(ref == 'manifest.json' or (out/ref).is_file() for ref in parser.refs)
    c.dump(out/'final_artifact_checks.json',{'passed':3,'failed':0,'all_report_links_present_except_manifest_at_closure':True,
        'source_snapshots_match':True,'protected_files_unchanged':True,'report_sha256':c.digest(out/'informe.html')})
    paths={name:c.ROOT/'Preparación'/name for name in ['ESTADO_PROYECTO.json','MEMORIA_PROYECTO.md','DECISIONES.md']}
    paths['RUTAS_PROYECTO.json']=c.ROOT/'RUTAS_PROYECTO.json'
    state=json.loads(paths['ESTADO_PROYECTO.json'].read_text('utf-8'))
    routes=json.loads(paths['RUTAS_PROYECTO.json'].read_text('utf-8'))
    memory,decisions=paths['MEMORIA_PROYECTO.md'].read_text('utf-8'),paths['DECISIONES.md'].read_text('utf-8')
    decision='D'+str(max(map(int,re.findall(r'\bD(\d+)\b',decisions)))+1)
    now=datetime.now(timezone.utc);rel=out.relative_to(c.ROOT).as_posix()
    close=a.BASE/'closures'/now.strftime('closure_%Y%m%dT%H%M%SZ');close.mkdir(parents=True,exist_ok=False)
    for name,path in paths.items():shutil.copy2(path,close/('before_'+name))
    record={'decision_id':decision,'workspace_relative_run':rel,'created_utc':now.isoformat(),
        'status':'verified_review_only_no_data_changes','report_workspace_relative':rel+'/informe.html',
        'policy_ids':a.PIDS,'focus_row_ids':a.FOCUS,'history_rows':8,'training_rows':8,'test_rows':0,
        'original_claims':0,'prepared_claims':0,'other_customer_policies':0,
        'original_2022_2023_triads_including_focus':2307,'other_original_triads':2305,
        'other_complete_D34_triads':1991,'other_triads_increase20_drop10_return_within10pct':2300,
        'other_original_complete_normal_2021_predecessors':2193,'peer_criteria_exploratory':True,
        'proposed_manual_scale_changes_NOT_APPLIED':2,'proposed_rule':'MANUAL_ENDORSE01-R proposal v1, exact two rows only',
        'proposed_capitals_NOT_APPLIED':{'C00502745':27200,'C00399729':25700},
        'endorsements_preserved_CU':{'C01153989':39400,'C01147928':37700},
        'renewals_preserved_CU':{'C01702744':28300,'C01618408':26700},
        'missing_context_preserved':['C01100142/high_value_items','C00997126/security_level'],
        'correction_authorized':False,'capital_changes':0,'retrospective_pending_unchanged':421,
        'other_pending_not_adjudicated':419,'base_pending_unchanged':1454,'test2025_evidence_used':False,
        'methodology_version_unchanged':'1.9','dataset_indexes_changed':False,'models_trained':False,
        'independent_validation':False,'real_browser_rendering_verified':False,'own_source_checks':v['passed'],
        'final_artifact_checks':3,'proposal_workspace_relative':rel+'/tables/proposed_manual_scale_changes_NOT_APPLIED.parquet',
        'proposal_sha256':c.digest(out/'tables/proposed_manual_scale_changes_NOT_APPLIED.parquet'),
        'closure_workspace_relative':close.relative_to(c.ROOT).as_posix()}
    c.dump(out/'closure_record.json',record)
    c.dump(out/'manifest.json',{'created_utc':now.isoformat(),'type':'immutable_two_endorsement_capital_review','files':[
        {'path':p.relative_to(out).as_posix(),'sha256':c.digest(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()]})
    index=a.BASE/'current_run.json';assert not index.exists()
    c.dump(index,record)
    state['endorsement_capital_review']=record
    state['distant_capital_review']['followup_two_endorsement_review_decision']=decision
    state['memory_as_of']=now.isoformat()
    routes['week_1_endorsement_capital_review_index']='Hackaton/Semana 1/Revision_ampliaciones_capital/current_run.json'
    c.dump(paths['ESTADO_PROYECTO.json'],state);c.dump(paths['RUTAS_PROYECTO.json'],routes)
    date=now.astimezone(timezone(timedelta(hours=-5))).strftime('%Y-%m-%d')
    text=f'''\n\n### {decision}, C50633171 y C56600576: ampliaciones y renovaciones, propuesta manual sin aplicar, {date}, America/Bogota

El participante pidió comparar en detalle las ampliaciones y renovaciones de las dos pólizas, mostrar historias y proponer tratamiento, sin modificar datos. La corrida ../{rel} relee ocho periodos de train, cuatro por póliza, sus originales y todos los campos. No hay periodos de test2025, siniestros originales/derivados ni otra póliza de esos clientes en las seis tablas. No se interpreta esa ausencia como riesgo cero ni ausencia de seguro externo. CAP05R y sus 421 pendientes permanecen intactos; base con 1.454, protocolo1.9, guard y objetivo iguales.

C50633171: C00502745 tiene 27.200.000 CU en 2021; C01100142 registra 27.700 entre 01-01 y 03-05-2022 con high_value_items desconocido; C01153989 registra 39.400 desde 04-05 a 31-12-2022; C01702744 registra 28.300 entre 01-01 y 15-05-2023 y termina lapsed_by_customer. Renovaciones 7→8→8→9. El tramo inicial de 2022 termina mid_term_change y el siguiente es contiguo. Ampliación +42,2383%; renovación posterior −28,1726%. Si solo 2021 se dividiera por mil, su base de 27.200 pasaría a 27.700 (+1,8382%) y la base de 2023 a 28.300 (+2,1661% frente al inicio de 2022). La ampliación seguiría en 39.400.

C56600576: C00399729 tiene 25.700.000 en 2021; C00997126 registra 26.200 entre 01-01 y 11-09-2022 con security_level ausente; C01147928 registra 37.700 desde 12-09 a 31-12-2022; C01618408 registra 26.700 entre 01-01 y 03-02-2023 y termina lapsed_by_customer. Renovaciones 15→16→16→17. Ampliación +43,8931%; renovación −29,1777%. /1000 solo en 2021 daría 25.700, con +1,9455% hacia la base de 2022 y +1,9084% entre las bases 2022/2023. Se conserva 37.700.

Los contextos D34 informados coinciden; ambos nulos permanecen desconocidos. Los ocho periodos no tienen huecos o solapes. Las dos partes de 2022 suman exposición 1 por póliza, sin anualizar o prorratear capital. Las primas escritas son diagnósticas: la fuente describe prima cobrada sin detallar su convención anual/prorrateada. Duraciones y factores varían; no se usa prima, falta de siniestros o maestro de direcciones como prueba de la unidad. renewal_decision se consulta como desenlace de fila y sigue fuera de predictores. No se transforma el objetivo.

Se investiga una cohorte exploratoria definida después de ver los casos, seleccionada por cronología, contador, capital original habitual y contexto conocido compatible, sin filtrar por tamaño del aumento o retorno. Incluye 2.307 tríos originales de 2022/2023. Se excluyen las dos pólizas de las estadísticas: otras 2.305, de las que 1.991 tienen todos los D34 observados. En 2.300 hay aumento >20%, caída >10% y retorno a menos del 10% de la base inicial de 2022. Las 2.305 bajan al renovar y su base de 2023 queda entre 0% y 4% por encima de la base de 2022. Otras 2.193 tienen además un predecesor de 2021 original habitual y completo con contexto conocido compatible. La cohorte se reconstruye por joins de fechas en el verificador, de forma distinta del análisis por desplazamiento. Se conservan todos los IDs y seis ejemplos reales. Esta evidencia apoya coherencia interna del patrón; no prueba suplemento contractual, mecanismo generador, unidad o probabilidad estadística de error, ni es validación independiente.

Se propone MANUAL_ENDORSE01-R para revisión manual retrospectiva separada: dividir únicamente C00502745/C00399729 por mil, sin aplicar ahora. Mantener 39.400/37.700 ampliados y 28.300/26.700 al renovar, sin copiar, interpolar, suavizar o imputar contexto. Reconocer la ampliación como nivel observado evita tratar toda trayectoria como suave. DIST01-R sigue fallando: las referencias completas más próximas de 2022 están a 488/619 días y sus razones frente al hipotético 2021 son 0,6904/0,6817. No se omiten ni se declara superada esa regla; la propuesta es una excepción manual distinta para estos dos IDs. El respaldo es posterior de train 2022/2023, sin test 2025; no autoriza uso causal. Solo una operación posterior autorizada llevaría 421→419 pendientes. No se activa regla global ni capa, ni se añade marca a datos. La confirmación contractual necesita la fuente; la causa del retorno permanece desconocida.

Pasaron 522 controles propios y tres finales de artefactos; dos figuras se inspeccionaron realmente, sin renderizado de navegador o revisión independiente acreditados. Se concilian ocho periodos, todos los campos y transiciones, originales, valores/nulos, exposiciones/calendario, siniestros, cobertura de búsquedas y los 2.307 tríos mediante un método distinto. Un primer control de enlaces esperaba su propio verification.json antes de crearlo; se archivó código/error y se ajustó el orden, sin modificar análisis o datos. Las fuentes, todos los índices de datos y el protocolo 1.9 conservan hashes. La IA preparó análisis, código y controles propios; la solicitud humana autoriza revisión y propuesta, no aplicación. Sin entrenamiento, proveedor externo, publicación, contacto a terceros o delegación. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad y responsabilidad. Ver endorsement_capital_review.
'''
    paths['DECISIONES.md'].write_text(decisions.rstrip()+text,encoding='utf-8')
    note=f'''\n\nDos ampliaciones revisadas, {decision}: [informe y ocho periodos](../{rel}/informe.html), [dos propuestas manuales sin aplicar](../{rel}/tables/proposed_manual_scale_changes_NOT_APPLIED.csv). C50633171: 27.200.000→27.700→39.400→28.300; C56600576: 25.700.000→26.200→37.700→26.700. Ampliaciones de 2022 +42,24%/+43,89%; retornos al renovar −28,17%/−29,18%, contadores constantes dentro del año y +1 al renovar. Se compara con otras 2.305 pólizas originales (1.991 completas): el patrón de ampliación/retorno es descriptivamente común; cohorte exploratoria, no confirmación contractual o validación independiente. Se proponen solo dos divisiones /1000 manuales retrospectivas de 2021 (27.200/25.700), conservando ampliaciones, renovaciones y nulos. No superan DIST01-R ni activan regla: respaldo futuro de train 2022/2023, sin test 2025. Ningún cambio de datos, protocolos o índices operativos; siguen 421 pendientes y 1.454 en la base, incluidos 108 sin ancla. 522 controles propios, tres finales y dos figuras inspeccionadas. Memoria registra propuesta, no autorización de aplicar. Ver endorsement_capital_review y {decision}.\n'''
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip()+note,encoding='utf-8')
    after=close/'after';after.mkdir()
    for name,path in paths.items():shutil.copy2(path,after/name)
    post=[{'check':'Closed review manifest intact','passed':a.cap.manifest_ok(out)},
        {'check':'All protected original, derived and index files unchanged','passed':all(c.digest(c.ROOT/path) == sha for path,sha in protected.items())},
        {'check':'All report links present after sealing','passed':all((out/ref).is_file() for ref in parser.refs)},
        {'check':'Review index and state agree','passed':json.loads(index.read_text('utf-8')) == state['endorsement_capital_review']}]
    assert all(x['passed'] for x in post)
    c.dump(close/'post_closure_verification.json',{'passed':len(post),'failed':0,'checks':post,'independent_validation':False})
    c.dump(close/'closure.json',{'created_utc':now.isoformat(),'decision_id':decision,'review':record,
        'manifest_sha256':c.digest(out/'manifest.json'),'all_protected_files_unchanged':True,
        'documents':{path.relative_to(c.ROOT).as_posix():c.digest(path) for path in [*paths.values(),index]}})
    print(json.dumps({'decision':decision,'run':str(out),'report':str(out/'informe.html'),'closure':str(close),'status':'verified_review_only_no_data_changes'},ensure_ascii=False))


if __name__=='__main__':
    main(Path(sys.argv[1]).resolve())
