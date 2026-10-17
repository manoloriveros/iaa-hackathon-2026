"""Congela fuentes y concilia cifras para el dossier; no transforma datos del concurso."""
from datetime import datetime, timezone
from pathlib import Path
from decimal import Decimal
import json
import re
import shutil
import sys
import uuid
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'Hackaton/Semana 1/Limpieza'))
sys.path.insert(0,str(ROOT/'Preparación/src'))
import clean_data as c
import correct_capitals as cap
from iaa_lab import predictor_guard
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
BASE=Path(__file__).parent
WEEK=ROOT/'Hackaton/Semana 1'


def readj(path):return json.loads(path.read_text('utf-8'))
def save(frame,out,name):
    frame.to_parquet(out/'tables'/(name+'.parquet'),index=False)
    frame.to_csv(out/'tables'/(name+'.csv'),index=False)


def main():
    routes=readj(ROOT/'RUTAS_PROYECTO.json');state=readj(ROOT/'Preparación/ESTADO_PROYECTO.json')
    now=datetime.now(timezone.utc);out=BASE/'runs'/(now.strftime('dossier_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8])
    for name in ['evidence','tables','figures','source_snapshot']:(out/name).mkdir(parents=True,exist_ok=False)
    sources={};counter=0
    def source(key,path,snapshot=False):
        nonlocal counter
        path=path.resolve();assert path.is_file(),str(path)
        if key in sources:assert sources[key]['workspace_relative_path']==path.relative_to(ROOT).as_posix();return path
        counter+=1
        item={'source_id':f'S{counter:03d}','workspace_relative_path':path.relative_to(ROOT).as_posix(),'sha256':c.digest(path),'bytes':path.stat().st_size}
        if snapshot:
            dest=out/'evidence'/(key+path.suffix);shutil.copy2(path,dest);item['snapshot']=dest.relative_to(out).as_posix()
        sources[key]=item;return path
    for key,path in {'routes':ROOT/'RUTAS_PROYECTO.json','state':ROOT/'Preparación/ESTADO_PROYECTO.json',
        'memory':ROOT/'Preparación/MEMORIA_PROYECTO.md','decisions':ROOT/'Preparación/DECISIONES.md',
        'rules':ROOT/'Hackaton/REGLAS_2026.md','IAA_priorities':ROOT/'Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md',
        'IAA_references':ROOT/'Preparación/Antecedentes/IAA_IA/README.md',
        'official_dictionary':ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md',
        'methodological_protocol':WEEK/'Modelado/protocolo_metodologico.json','methodology':WEEK/'Modelado/METODOLOGIA_ACTUARIAL.md',
        'predictor_guard':ROOT/'Preparación/src/iaa_lab/predictor_guard.py','target_scope':WEEK/'Modelado/target_scope.py'}.items():source(key,path,True)
    indices={}
    for key,rel in routes.items():
        if key.endswith('_index'):
            p=source(key,ROOT/rel,True);indices[key]=readj(p)
    baseidx=indices['week_1_prepared_data_index'];retro=indices['week_1_retrospective_prepared_data_index']
    assert retro['capital_rule']=='CAP06R' and retro['pending_capitals']==419
    basecat=readj(source('base_catalog',ROOT/baseidx['catalog_workspace_relative'],True));retrocat=readj(source('retrospective_catalog',ROOT/retro['catalog_workspace_relative'],True))
    protected={}
    raw_metadata=[];current_metadata=[]
    for name in sorted(basecat):
        path=source('raw_'+name,c.RAW/(name+'.parquet'));q=pq.ParquetFile(path)
        raw_metadata.append({'table':name,'rows':q.metadata.num_rows,'columns':len(q.schema_arrow),'bytes':path.stat().st_size,'sha256':c.digest(path),
            'column_names':q.schema_arrow.names,'column_types':{field.name:str(field.type) for field in q.schema_arrow}})
        protected[path.relative_to(ROOT).as_posix()]=c.digest(path)
        for layer,catalog in [('base',basecat),('retrospective',retrocat)]:
            p=ROOT/catalog[name]['workspace_relative_path'];assert c.digest(p)==catalog[name]['sha256'];protected[p.relative_to(ROOT).as_posix()]=c.digest(p)
            m=pq.ParquetFile(p);current_metadata.append({'layer':layer,'table':name,'rows':m.metadata.num_rows,'columns':len(m.schema_arrow),
                'workspace_relative_path':p.relative_to(ROOT).as_posix(),'sha256':c.digest(p),'column_names':m.schema_arrow.names})
    for key in indices:protected[routes[key]]=sources[key]['sha256']
    for key in ['base_catalog','retrospective_catalog','methodological_protocol','predictor_guard','target_scope']:
        protected[sources[key]['workspace_relative_path']]=sources[key]['sha256']
    # Every change and every residual capital is read from the active immutable ledgers.
    retropath=ROOT/retro['workspace_relative_run'];basepath=ROOT/baseidx['workspace_relative_run']
    pending=pd.read_parquet(source('current_pending',retropath/'tables/pending_capitals.parquet'))
    cumulative=pd.read_parquet(source('retrospective_ledger',retropath/'ledger/cumulative_retrospective_changes.parquet'))
    cap01=pd.read_parquet(source('CAP01_ledger',retropath/'evidence/CAP01_ledger.parquet'))
    cap01pending=ROOT/indices['week_1_capital_correction_index']['workspace_relative_run']/'tables/pending_capitals.parquet'
    # CAP01 records pending under a different historical file name on some layers.
    if not cap01pending.exists():cap01pending=ROOT/indices['week_1_retrospective_capital_application_index']['workspace_relative_run']/'evidence/frozen_1454_pending.parquet'
    save(pending,out,'pending_419_snapshot');save(cumulative,out,'retrospective_1035_snapshot')
    groups=pending.groupby(['review_group','group_label'],dropna=False).size().rename('rows').reset_index()
    save(groups,out,'current_pending_groups')
    by_table=pending.groupby(['source_table','line']).size().rename('rows').reset_index();save(by_table,out,'current_pending_by_table')
    raw_extreme=set();base_extreme=set();retro_extreme=set()
    for name in ['policies_buildings','test_buildings','policies_contents','test_contents']:
        cutoff=10000000 if name.endswith('buildings') else 1000000
        for layer,path,ids in [('original',c.RAW/(name+'.parquet'),raw_extreme),('base',ROOT/basecat[name]['workspace_relative_path'],base_extreme),('retrospective',ROOT/retrocat[name]['workspace_relative_path'],retro_extreme)]:
            d=pq.read_table(path,columns=['row_id','sum_insured']).to_pandas();ids.update(d.loc[d.sum_insured.gt(cutoff),'row_id'])
    assert len(raw_extreme)==3527 and len(base_extreme)==1454 and len(retro_extreme)==419
    assert set(pending.row_id)==retro_extreme==raw_extreme-set(cap01.row_id)-set(cumulative.row_id)
    assert len(cap01)==cap01.row_id.nunique()==2073 and len(cumulative)==cumulative.row_id.nunique()==1035 and not set(cap01.row_id)&set(cumulative.row_id)
    stages=[{'rule':'CAP01','decision':'D36','rows':len(cap01),'new_test2025_anchors':0,'test_rows_changed':int(cap01.source_table.str.startswith('test_').sum()),'cumulative_corrected':len(cap01),'remaining':1454}]
    running=2073
    stage_rules=[('CAP02R','D49','week_1_retrospective_capital_application_index'),('CAP03R','D52','week_1_numeric_capital_application_index'),('CAP04R','D54','week_1_context_capital_application_index'),('CAP05R','D58','week_1_distant_capital_application_index'),('CAP06R','D61','week_1_endorsement_capital_application_index')]
    for rule,decision,key in stage_rules:
        frame=cumulative.loc[cumulative.rule.eq(rule)];running+=len(frame)
        stages.append({'rule':rule,'decision':decision,'rows':len(frame),'new_test2025_anchors':int(frame.audit_ref_test2025.sum()),
            'test_rows_changed':int(frame.source_table.str.startswith('test_').sum()),'cumulative_corrected':running,'remaining':3527-running})
        run=ROOT/indices[key]['workspace_relative_run']
        for suffix in ['summary.json','verification.json','rules.json','authorization.json','lineage.json']:
            if (run/suffix).is_file():source(rule+'_'+suffix.split('.')[0],run/suffix)
    save(pd.DataFrame(stages),out,'capital_stages')
    # Historic evidence remains attached to its exact cut.
    eda=ROOT/state['data_validation']['run'].removeprefix('../')
    notes=pd.read_csv(source('column_notes_D30',eda/'column_notes.tsv'),sep='\t')
    d40=ROOT/indices['week_1_validation_gap_review_index']['workspace_relative_run']
    inventory=readj(source('field_inventory_D40',d40/'field_inventory.json'))
    d56=ROOT/indices['week_1_incomplete_capital_review_index']['workspace_relative_run']
    backlog=readj(source('backlog_D56',d56/'validation_backlog_58.json',True));assert len(backlog)==58
    source('workstreams_D56',d56/'tables/validation_workstreams.csv')
    d59=ROOT/indices['week_1_adjustment_validation_claude_index']['workspace_relative_run']
    claude=readj(source('D59_evidence',d59/'evidencia.json'))
    agekeys=['discrepancies','explained_by_age_at_quote_date','explained_by_birthday_on_period_start_exclusive','plus_one_explained_by_age_at_period_end','unexplained']
    age={key:sum(v[key] for v in claude['rules']['AGE01']['tables'].values()) for key in agekeys}
    assert age['discrepancies']==2936 and age['unexplained']==2 and sum(age[k] for k in agekeys[1:])==2936
    source('D59_report',WEEK/'Validacion_ajustes_claude/INFORME.md');source('D59_delivery_verification',WEEK/'Validacion_ajustes_claude/verification.json')
    for key in ['data_cleaning','data_refinement','capital_correction','duplicate_application','renewal_audit_application','prehistory_audit_application']:
        value=state[key];run=ROOT/value['run'].removeprefix('../')
        for suffix in ['summary.json','verification.json','rules.json']:
            if (run/suffix).is_file():source(key+'_'+suffix.split('.')[0],run/suffix)
    clean=readj(ROOT/sources['data_cleaning_summary']['workspace_relative_path']);refine=readj(ROOT/sources['data_refinement_summary']['workspace_relative_path'])
    for key,val in state.items():
        if isinstance(val,dict) and (val.get('report') or val.get('report_workspace_relative')):
            rp=(val.get('report') or val['report_workspace_relative']).split('#')[0]
            p=((ROOT/'Preparación'/rp) if val.get('report') else (ROOT/rp)).resolve()
            if p.is_file() and p.is_relative_to(ROOT):source('report_'+key,p)
    for key,val in indices.items():
        if val.get('workspace_relative_run'):
            run=ROOT/val['workspace_relative_run']
            for suffix in ['summary.json','verification.json']:
                if (run/suffix).is_file():source(key+'_'+suffix.split('.')[0],run/suffix)
    # Snapshot source text for all mutable project context; immutable run evidence stays linked by hash.
    overrides={
        'VD09':'D59 conserva cuatro casos de daño propio fuera de comprehensive tras DUP01; evidencia al corte CAP05R, sin adjudicación nueva.',
        'VD10':'D59 registra 502 edificios y1.087 contenidos tras DUP01; no506/1.090 originales. Conteo histórico; revisar semántica y cobertura sin eliminar siniestros.',
        'VD11':'D59 registró8/3 superiores al capital; no es recálculo sobre CAP06R. Queda revisión vigente por asignación, cobertura y límite.',
        'VD30':'CAP06R:419 pendientes en rama retrospectiva y1.454 en base;3.108 correcciones totales,1.035 retrospectivas. No se aprueba disponibilidad causal.',
        'VD32':'AGE01 fija edad al inicio. D59 explica2.934 de2.936 diferencias por otras convenciones y conserva2 sin explicar; no todos son errores de captura.',
        'VD41':'D56 revisó202 contextos incompletos. Tras CAP05R/CAP06R quedan154 del grupo F; los nulos siguen sin imputar.',
        'VD53':'Los índices vigentes son base PRE00 y rama CAP06R. Los demás current_* identifican operaciones o revisiones históricas, no la última capa.',
        'VD54':'D59 es segunda implementación asistida por IA hasta CAP05R, no revisión humana independiente. CAP06R tiene279 controles propios; revisión independiente sigue pendiente.'}
    current_backlog=[]
    for row in backlog:
        current_backlog.append({**row,'documentation_update_at_CAP06R':overrides.get(row['id'],'Sin adjudicación nueva. Mantener el alcance y pendiente registrados en D56; no se reejecutó este control.'),
            'status_at_documentation_cut':'parcial_419_pendientes_retrospectivos' if row['id']=='VD30' else row['current_status'],
            'fresh_rule_reexecution':False})
    c.dump(out/'validation_register_58.json',current_backlog)
    save(pd.DataFrame([{k:row[k] for k in ['id','area','priority','title','current_status','status_at_documentation_cut','remaining_work_current','closure_criterion','documentation_update_at_CAP06R','fresh_rule_reexecution']} for row in current_backlog]),out,'validation_register_58')
    probe={name:predictor_guard.exclusion_reason(name) for name in ['renewal_decision','audit_ren00','audit_pre00','customer_service_contacts']}
    assert probe['renewal_decision'] and probe['audit_ren00'] and probe['audit_pre00'] and probe['customer_service_contacts'] is None
    probe['selection_example']=predictor_guard.select_predictor_columns(['sum_insured','exposure','renewal_decision','audit_ren00','customer_service_contacts'])
    c.dump(out/'guard_probe.json',probe)
    original_columns=set().union(*(set(x['column_names']) for x in raw_metadata));derived_columns=set().union(*(set(x['column_names']) for x in current_metadata if x['layer']=='retrospective'))
    assert len(original_columns)==len(notes)==105 and len(derived_columns)==107
    dictionary=[]
    field_updates={
        'customer_id':'ID01 en autos; texto de ocho dígitos. Clave para joins/historia, no efecto tarifario del código arbitrario.',
        'exposure':'EXP01: días cubiertos inclusivos/365, cuatro decimales. No cambia fechas; no usar como capital ni dividir otra vez la predicción por exposición.',
        'sum_insured':'CAP01 en base; CAP02R a CAP06R solo en rama retrospectiva. Base conserva1.454 extremos, rama419. No imputar, anualizar, copiar límites o corregir otros IDs por inferencia.',
        'construction_type':'CAT01 solo alias de caja y espacios según mapa. t y w separados; CON01 candidata fuera del catálogo activo.',
        'policyholder_age':'AGE01: años cumplidos al inicio de cobertura desde nacimiento. Cambio de definición de referencia, no certificación de error original; alcance hogar.',
        'driver_age':'Se conserva; conductor principal puede diferir del tomador. No aplicar AGE01.',
        'renewal_decision':'Uso diagnóstico de desenlace. Exclusión de predictores implementada por guard1.0; REN00 no cambia etiquetas.',
        'customer_service_contacts':'D50 recomienda excluir por señal contemporánea de siniestro y deriva. Brecha comprobada: guard1.0 aún la acepta. Bloquear antes de entrenar; no se modificó aquí.',
        'written_premium':'Valor comercial observado; convención anual/prorrateada y disponibilidad ex ante pendientes. No prueba la unidad del capital ni se anualiza para decidir reparaciones.',
        'discount_applied':'Descuento comercial, requiere contrato de disponibilidad y justificación; sin cambio de valores.',
        'incurred_to_date':'Pagado más estimación de caso al31-12-2024. Diagnóstico del objetivo; no predictor contemporáneo. No equivale a último observado.',
        'paid_to_date':'Pagado neto de franquicia según diccionario; no restar automáticamente otra vez los excesos.',
        'recoveries':'Recuperación observada al corte; componentes netos diagnósticos, sin reparación o desarrollo futuro.',
        'claim_id':'DUP01 conserva CL+ocho dígitos y alias de604 copias excluidas. No usar como predictor.',
        'prediction':'Salida requerida por row_id, CU por periodo, no negativa. Plantilla no es una etiqueta ni resultado entrenado.'}
    for row in notes.to_dict('records'):
        col=row['column'];tables=[x['table'] for x in raw_metadata if col in x['column_names']]
        dictionary.append({**row,'tables':tables,'definition_source':'D30 column_notes.tsv + official dictionary',
            'treatment_at_cut':field_updates.get(col,'Se conserva. La propuesta inicial D30 que sigue no implica aprobación F0, imputación o inclusión en modelos.'),
            'original_proposed_treatment_D30':row['proposed_treatment'],'operational_F0_contract_complete':False})
    for col,meaning,scoped in [('audit_ren00','Marca de auditoría de periodos de2742 pólizas con rechazo y continuidad.',list(name for name in retrocat if name.startswith(('policies_','test_')))),
        ('audit_pre00','Marca de413 siniestros anteriores al primer periodo de póliza observado.',['claims'])]:
        dictionary.append({'column':col,'meaning':meaning,'insurance_and_tariff':'Auditoría de datos, sin efecto de tarifa; nunca predictor.',
            'availability':'Membresía retrospectiva; fuera de F0.','proposed_treatment':'Excluir siempre del selector de predictores.',
            'tables':scoped,'definition_source':'D45 REN00 / D47 PRE00',
            'treatment_at_cut':'Marca aplicada, campos de fuente conservados y exclusión de predictores implementada.',
            'original_proposed_treatment_D30':'Campo añadido después de D30.','operational_F0_contract_complete':False})
    dictionary=sorted(dictionary,key=lambda x:x['column']);c.dump(out/'dictionary_107.json',dictionary)
    save(pd.DataFrame([{**row,'tables':' | '.join(row['tables'])} for row in dictionary]),out,'dictionary_107')
    decision_lines=[]
    for line in (ROOT/'Preparación/DECISIONES.md').read_text('utf-8').splitlines():
        match=re.match(r'### D(\d+), (.*)',line)
        if match and 28<=int(match[1])<=61:decision_lines.append({'decision':'D'+match[1],'number':int(match[1]),'title':match[2]})
    save(pd.DataFrame(sorted(decision_lines,key=lambda x:x['number'])),out,'decision_timeline')
    facts={'cut_created_utc':now.isoformat(),'source_data_cut_decision':'D61','scope':'Documentation and source reconciliation only; not fresh re-execution of every historical validation.',
        'base_index':baseidx,'retrospective_index':retro,'raw_tables':raw_metadata,'current_tables':current_metadata,
        'original_unique_columns':len(original_columns),'original_column_occurrences':sum(x['columns'] for x in raw_metadata),
        'derived_unique_columns':len(derived_columns),'derived_column_occurrences':sum(x['columns'] for x in current_metadata if x['layer']=='retrospective'),
        'original_extreme_capitals':len(raw_extreme),'base_pending_extremes':len(base_extreme),'retrospective_pending_extremes':len(retro_extreme),
        'capital_stages':stages,'pending_groups':groups.to_dict('records'),'pending_by_table':by_table.to_dict('records'),
        'new_retrospective_test_anchors_total':int(cumulative.audit_ref_test2025.sum()),'retrospective_test_rows_corrected':int(cumulative.source_table.str.startswith('test_').sum()),
        'cleaning_summary':clean,'refinement_summary':refine,'AGE01_D59_explanation':age,
        'D59_summary':claude['summary'],'D59_actual_retrospective_run':claude['lineage']['active_retrospective'],
        'D59_open_issues_historical':claude['open_issues'],'D59_rules':{rule:{k:v for k,v in value.items() if k!='tables'} for rule,value in claude['rules'].items()},
        'audit_counts':{k:state[k] for k in ['duplicate_application','renewal_audit_application','prehistory_audit_application']},
        'Jev':state['ai_validation_tool_assessment'],'predictor_guard_probe':probe,'protocol_version':readj(ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json')['version'],
        'base_catalog_workspace_relative':baseidx['catalog_workspace_relative'],'retrospective_catalog_workspace_relative':retro['catalog_workspace_relative'],
        'models_trained_by_this_task':False,'data_modified':False,'independent_validation':False}
    c.dump(out/'facts.json',facts);c.dump(out/'source_register.json',sources);c.dump(out/'protected_data_hashes.json',protected)
    for name in ['collect_documentation.py','clean_data.py','correct_capitals.py']:
        src=BASE/name if name=='collect_documentation.py' else c.BASE/name;shutil.copy2(src,out/'source_snapshot'/name)
    assert all(c.digest(ROOT/path)==sha for path,sha in protected.items())
    print(json.dumps({'run':str(out),'sources':len(sources),'columns':len(dictionary),'pending':len(pending),'age_explanation':age},ensure_ascii=False))


if __name__=='__main__':main()
