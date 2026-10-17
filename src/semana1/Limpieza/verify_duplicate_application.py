"""Verificación integral y publicación de DUP01 solo tras comprobar todos sus efectos."""
from collections import defaultdict
from decimal import Decimal
from html.parser import HTMLParser
import json

import apply_duplicates as a
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def main():
    ptr=json.loads((a.BASE/'current_duplicate_application.json').read_text(encoding='utf-8'))
    out=a.ROOT/ptr['workspace_relative_run']
    parent=json.loads((out/'evidence/parent_catalog.json').read_text(encoding='utf-8'))
    catalog=json.loads((out/'dataset_catalog.json').read_text(encoding='utf-8'))
    before=pq.read_table(a.ROOT/parent['claims']['workspace_relative_path'])
    after=pq.read_table(a.ROOT/catalog['claims']['workspace_relative_path'])
    removed=pq.read_table(out/'ledger/excluded_rows.parquet')
    selection=pq.read_table(out/'evidence/approved_pair_actions.parquet').to_pandas()
    aliases=pq.read_table(out/'ledger/claim_id_aliases.parquet').to_pandas()
    ledger=pq.read_table(out/'ledger/exclusion_ledger.parquet').to_pandas()
    protected=json.loads((out/'protected_hashes_before.json').read_text(encoding='utf-8'))
    checks=[]
    def check(name,ok):
        checks.append({'name':name,'passed':bool(ok)})
        if not ok:
            a.c.dump(out/'verification_failed.json',{'passed':False,'checks':checks});raise AssertionError(name)
    for path,sha in protected.items():check('protected_hash:'+path,a.c.digest(a.ROOT/path)==sha)
    check('all_protected_hashes_before_after_equal',protected==json.loads((out/'protected_hashes_after.json').read_text(encoding='utf-8')))
    for label,folder in [('parent',a.ROOT/json.loads((out/'evidence/parent_index.json').read_text(encoding='utf-8'))['workspace_relative_run']),('review',a.REVIEW)]:
        m=json.loads((out/'evidence'/f'{label}_manifest.json').read_text(encoding='utf-8'))
        check(label+':all_historical_files_and_manifest_unchanged',a.c.digest(folder/'manifest.json')==a.c.digest(out/'evidence'/f'{label}_manifest.json')
              and all(a.c.digest(folder/item['path'])==item['sha256'] for item in m['files']))
    check('claims_schema_and_metadata_exactly_preserved',before.schema.equals(after.schema,check_metadata=True))
    check('exact_record_counts_163150_minus_604_equals_162546',before.num_rows==163150 and after.num_rows==162546 and removed.num_rows==604)
    ids_before=before['claim_id'].to_pylist();ids_after=after['claim_id'].to_pylist();position={claim:i for i,claim in enumerate(ids_before)}
    excluded=set(selection.proposed_exclude_claim_id);kept=set(selection.proposed_keep_claim_id)
    keep_positions=[i for i,claim in enumerate(ids_before) if claim not in excluded]
    removed_positions=[i for i,claim in enumerate(ids_before) if claim in excluded]
    check('exact_frozen_604_id_difference_no_other_exclusion',set(ids_before)-set(ids_after)==excluded and not(set(ids_after)-set(ids_before)))
    check('all_604_eight_digit_representatives_preserved',kept.issubset(set(ids_after)) and selection.proposed_keep_claim_id.str.fullmatch(r'CL[0-9]{8}').all())
    check('all_other_161942_claims_still_present',len(set(ids_before)-(excluded|kept))==161942 and (set(ids_before)-(excluded|kept)).issubset(set(ids_after)))
    check('every_retained_cell_and_row_order_identical',after.equals(before.take(pa.array(keep_positions,type=pa.int64())),check_metadata=True))
    check('typed_excluded_ledger_exact_source_rows_and_metadata',removed.equals(before.take(pa.array(removed_positions,type=pa.int64())),check_metadata=True))
    check('source_claim_ids_remain_text_and_unique',len(ids_after)==len(set(ids_after)) and all(isinstance(x,str) for x in ids_after))
    check('alias_map_exact_one_to_one_604_disjoint_ids',len(aliases)==604 and aliases.excluded_claim_id.is_unique and aliases.retained_claim_id.is_unique
          and set(aliases.excluded_claim_id)==excluded and set(aliases.retained_claim_id)==kept and not excluded&kept)
    alias_ref=selection.set_index('proposed_exclude_claim_id').proposed_keep_claim_id.to_dict()
    check('every_alias_resolves_to_its_frozen_twin',aliases.set_index('excluded_claim_id').retained_claim_id.to_dict()==alias_ref)
    source=before.to_pandas();filtered=after.to_pandas();payload=[col for col in source if col!='claim_id']
    for row in aliases.itertuples():
        first=before.slice(position[row.excluded_claim_id],1).select(payload)
        second=before.slice(position[row.retained_claim_id],1).select(payload)
        assert first.equals(second,check_metadata=True)
        assert ids_after[row.retained_derived_row]==row.retained_claim_id
        assert row.excluded_source_row==position[row.excluded_claim_id] and row.retained_source_row==position[row.retained_claim_id]
    check('all_alias_payloads_exact_and_old_new_positions_match',True)
    check('consolidated_exclusion_ledger_complete_source_positions',ledger.excluded_source_row.tolist()==removed_positions
          and ledger.claim_id.tolist()==removed['claim_id'].to_pylist() and ledger.operation_applied.all())
    check('ledger_full_source_values_identical',all(ledger[col].reset_index(drop=True).equals(removed[col].to_pandas().reset_index(drop=True)) for col in before.column_names))
    combined=pa.concat_tables([after,removed])
    combined_positions=keep_positions+removed_positions
    restore_order=np.argsort(np.array(combined_positions))
    restored=combined.take(pa.array(restore_order,type=pa.int64()))
    check('full_exact_reversal_from_retained_data_and_typed_exclusions',restored.equals(before,check_metadata=True))
    again,n=a.apply_frozen(after,selection)
    check('idempotent_second_application_removes_nothing',n==0 and again.equals(after,check_metadata=True))
    conflict=after.set_column(after.schema.get_field_index('incurred_to_date'),after.schema.field('incurred_to_date'),
        pa.array([value+(1. if claim==selection.proposed_keep_claim_id.iloc[0] else 0.) for value,claim in zip(after['incurred_to_date'].to_pylist(),ids_after)],type=after.schema.field('incurred_to_date').type))
    rejected=False
    try:a.apply_frozen(conflict,selection)
    except ValueError:rejected=True
    check('changed_representative_payload_rejected',rejected)
    partial=before.filter(pa.array([claim!=selection.proposed_exclude_claim_id.iloc[0] for claim in ids_before]))
    rejected=False
    try:a.apply_frozen(partial,selection)
    except ValueError:rejected=True
    check('partial_exclusion_state_rejected',rejected)
    # Independent exact-content grouping from raw tuples; after is compared without reusing the production filter.
    groups=defaultdict(list)
    for row in source.itertuples(index=False,name=None):
        record=dict(zip(source.columns,row));key=tuple(None if pd.isna(record[col]) else record[col] for col in payload)
        groups[key].append(record['claim_id'])
    twins=[members for members in groups.values() if len(members)>1]
    check('independent_full_payload_604_pair_cohort_matches_authorized_members',len(twins)==604 and all(len(members)==2 for members in twins)
          and {claim for members in twins for claim in members}==excluded|kept)
    check('no_exact_non_id_payload_duplicate_left',not filtered.duplicated(payload).any())
    controls=pq.read_table(out/'evidence/review_near_controls.parquet').to_pandas().drop_duplicates('claim_id')
    check('all_114_nonidentical_same_occurrence_control_records_preserved',len(controls)==114 and set(controls.claim_id).issubset(set(ids_after)))
    collision_counts=[]
    for keys in [['policy_id','line','peril','loss_date','report_date'],['policy_id','line','peril','loss_date'],['policy_id','line','loss_date']]:
        sizes=filtered.groupby(keys,dropna=False).size();collision_counts.append(int(sizes.gt(1).sum()))
    check('nonidentical_collision_groups_1_17_57_unchanged',collision_counts==[1,17,57])
    # Independent assignment result: the source classification filtered by ID must agree with the fresh date join.
    oldassign=pq.read_table(out/'evidence/parent_claim_assignment.parquet').to_pandas()
    newassign=pq.read_table(out/'tables/claim_period_assignment.parquet').to_pandas()
    expected=oldassign[~oldassign.claim_id.isin(excluded)].sort_values('claim_id').reset_index(drop=True)
    actual=newassign.sort_values('claim_id').reset_index(drop=True)
    # The previous diagnostic stored midnight timestamps; the new diagnostic keeps source date32.
    # Compare the same instants at a common resolution without changing either saved diagnostic.
    expected['loss_date']=pd.to_datetime(expected.loss_date).astype('datetime64[ns]')
    actual['loss_date']=pd.to_datetime(actual.loss_date).astype('datetime64[ns]')
    check('fresh_interval_assignment_identical_for_every_retained_claim',actual.equals(expected))
    check('prehistory_count_exact_414_to_413_without_date_change',int(oldassign.assignment_status.eq('before_first_observed_period').sum())==414
          and int(newassign.assignment_status.eq('before_first_observed_period').sum())==413)
    check('new_assignment_has_one_row_per_claim_no_ambiguity',newassign.claim_id.is_unique and set(newassign.claim_id)==set(ids_after)
          and set(newassign.assignment_status)=={'unique_period','before_first_observed_period'})
    books=json.loads((out/'reconciliation.json').read_text(encoding='utf-8'))
    for entry in books:
        for field in ['records','accepted','closed','open','repudiated']:
            assert entry['before_'+field]==entry['after_'+field]+entry['excluded_'+field]
        for field in ['paid_accepted_CU','incurred_accepted_CU','recoveries_accepted_CU','reserve_accepted_CU','net_accepted_CU']:
            assert Decimal(entry['before_'+field])==Decimal(entry['after_'+field])+Decimal(entry['excluded_'+field])
    check('all_counts_and_all_monetary_components_reconcile_exactly_with_Decimal',len(books)==6)
    check('net_reduction_all_3174167_49',books[0]['excluded_net_accepted_CU']=='3174167.49')
    check('net_reduction_assigned_3173808_61_and_prehistory_358_88',next(x for x in books if x['value']=='unique_period')['excluded_net_accepted_CU']=='3173808.61'
          and next(x for x in books if x['value']=='before_first_observed_period')['excluded_net_accepted_CU']=='358.88')
    check('new_ramo_counts_reconcile',filtered.line.value_counts().to_dict()=={'motor':112195,'buildings':26333,'contents':24018})
    check('new_status_counts_reconcile',filtered.status.value_counts().to_dict()=={'closed':150706,'open':10135,'repudiated':1705})
    for name,entry in catalog.items():
        check(name+':catalog_hash',a.c.digest(a.ROOT/entry['workspace_relative_path'])==entry['sha256'])
        if name!='claims':check(name+':entire_catalog_reference_unchanged',entry==parent[name])
    check('only_claims_catalog_entry_changed',set(catalog)==set(parent) and len(catalog)==11)
    check('no_capital_or_policy_transformation_or_CON01_activation',all(catalog[name]==parent[name] for name in a.c.TABLES)
          and not any('construction_type_harmonized' in pq.read_schema(a.ROOT/catalog[name]['workspace_relative_path']).names for name in ['policies_buildings','test_buildings']))
    authorization=json.loads((out/'authorization.json').read_text(encoding='utf-8'))
    check('explicit_user_authorization_and_hash_link_in_every_alias',authorization['messages']==[{'role':'user','content':a.REQUEST}]
          and aliases.authorization_sha256.eq(a.c.digest(out/'authorization.json')).all())
    check('overall_modeling_approval_not_inferred',not json.loads((out/'summary.json').read_text(encoding='utf-8'))['T0_operationally_materialized'])
    result={'passed':True,'checks_count':len(checks),'checks':checks,'excluded_records':604,'records_after':162546,
        'retained_values_changed':0,'exact_reversal_verified':True,'idempotence_verified':True,
        'originals_modified':False,'other_claims_modified':False,'independent_validation':False,'approved_for_modeling':False}
    a.c.dump(out/'verification.json',result)
    render_report(out,result,books,ledger,aliases)
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.paths=[]
        def handle_starttag(self,tag,attrs):self.paths.extend(v for k,v in attrs if k=='href' and v and not v.startswith(('#','data:','https:','http:')))
    parser=Links();parser.feed((out/'informe.html').read_text(encoding='utf-8'))
    check('all_report_links_exist',all((out/p).is_file() for p in parser.paths))
    result.update(checks=checks,checks_count=len(checks));a.c.dump(out/'verification.json',result)
    render_report(out,result,books,ledger,aliases)
    entries=[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':a.c.digest(p)}
        for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json']
    a.c.dump(out/'manifest.json',{'count':len(entries),'files':entries})
    # Publish last and only if nobody moved the prepared-data pointer while this run was being built.
    active=a.BASE/'current_dataset.json'
    if a.c.digest(active)!=a.c.digest(out/'evidence/parent_index.json'):raise ValueError('Active dataset changed concurrently; do not overwrite its catalog.')
    pointer={'workspace_relative_run':out.relative_to(a.ROOT).as_posix(),'status':'verified_DUP01_frozen_cohort',
        'catalog_workspace_relative':(out/'dataset_catalog.json').relative_to(a.ROOT).as_posix(),
        'inherited_rules':['ID01','EXP01','CAP01','CAT01','AGE01'],'claims_rule':'DUP01',
        'claims_records':162546,'claims_excluded':604,'capital_changes_inherited':2073,'pending_capitals':1454,
        'category_changes_inherited':700210,'age_changes_inherited':2936,'CON01_activated':False,'approved_for_modeling':False}
    temp=a.BASE/'current_dataset.pending.json';a.c.dump(temp,pointer);temp.replace(active)
    a.c.dump(a.BASE/'current_duplicate_application.json',pointer)
    print(json.dumps({'passed':True,'checks':len(checks),'claims_after':162546,'excluded':604,'active_run':str(out)}),flush=True)


def render_report(out,result,books,ledger,aliases):
    summary=pd.DataFrame([{'ramo':b['value'],'antes':b['before_records'],'después':b['after_records'],
        'excluidos':b['excluded_records'],'reducción_neto_aceptado_CU':b['excluded_net_accepted_CU']} for b in books if b['dimension']=='line'])
    examples=ledger[ledger.policy_id.isin(['M27706820','M71403075','M76932061','M37030249'])][
        ['claim_id','retained_claim_id','policy_id','status','paid_to_date','incurred_to_date','recoveries','net_accepted_excluded_CU']]
    html=['<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DUP01 aplicado</title>',
        '<style>body{font:16px/1.65 system-ui;max-width:1250px;margin:36px auto;padding:0 24px;color:#183344}table{display:block;overflow:auto;border-collapse:collapse;font-size:14px}th,td{padding:9px;border-bottom:1px solid #dce5ea;white-space:nowrap;text-align:left}th{background:#e9f1f4}a{color:#056391}.result{padding:15px 22px;background:#e8f4ef;border-left:5px solid #007c77}</style></head><body>',
        '<h1>DUP01 aplicado a los 604 pares autorizados</h1>',
        '<div class="result"><p>La nueva capa de claims contiene 162.546 registros, frente a 163.150 anteriores. Se excluyeron exactamente los 604 IDs de nueve dígitos de la cohorte revisada y se conservaron sus 604 representantes de ocho dígitos. Cada celda de los registros retenidos, su esquema y orden relativo permanecen iguales.</p></div>',
        '<p>La autorización explícita está conservada. Los once originales y los datos anteriores mantienen hashes. Las otras diez entradas del catálogo no cambian; incluye todas las pólizas y los capitales. CON01 no se activó y los 1.454 capitales pendientes siguen intactos.</p>',
        '<h2>Conciliación por ramo</h2>',summary.to_html(index=False,border=0),
        '<p>Se excluyeron 586 cerrados, 12 abiertos y seis rechazados. La reducción observada del neto aceptado es 3.174.167,49 CU en todo claims: 3.173.808,61 CU de periodos observados y 358,88 CU anteriores a la historia. No se estima pérdida última ni mejora predictiva. Se conservan pagos, reservas y recuperaciones de los expedientes retenidos sin ajustes.</p>',
        '<h2>Bitácora y alias</h2>',examples.to_html(index=False,border=0),
        '<p>Cada exclusión registra el claim_id original, representante, grupo, posiciones originales y derivadas, huella de contenido, todos los valores fuente, hashes, autorización y regla. excluded_rows.parquet conserva las 604 filas con el esquema y metadatos originales para una reversión exacta. El mapa de alias resuelve referencias antiguas; no se une como si añadiera siniestros nuevos.</p>',
        '<h2>Qué permanece</h2><p>Los otros 161.942 siniestros ajenos a los pares y los 604 representantes se conservan íntegros. Los 114 registros de los 57 grupos no idénticos con misma póliza/ocurrencia permanecen. Las diferencias de estado, importes, reparador o tercero no se fusionan. No se descubrió o amplió ninguna cohorte nueva durante la aplicación.</p>',
        '<p>La asignación por fechas se recalculó para validar el efecto: quedan 413 siniestros anteriores al primer periodo, frente a 414 en el snapshot histórico, porque se excluyó una copia de ese conjunto. Las fechas no cambian y esos siniestros no se fuerzan a un periodo. La tabla de asignación es evidencia diagnóstica; no se materializó una tabla operativa T0.</p>',
        '<h2>Verificación y uso</h2>',
        f'<p>Pasaron {result["checks_count"]} controles propios: diferencia exacta de IDs, igualdad de todos los valores retenidos y su orden, alias, bitácora, reversión completa, idempotencia y rechazo de conflictos, conciliación decimal de importes, controles no idénticos, catálogo, hashes y autorización. Se publicará la versión preparada únicamente tras estos controles y sin sobrescribir una actualización concurrente.</p>',
        '<p>El índice unificado current_dataset.json identifica esta capa. Los informes D38, D40 y D41 conservan sus versiones históricas; no certifican automáticamente estadísticas posteriores a DUP01. La validación propia asistida por IA y la autorización de esta operación no equivalen a confirmación del generador, validación independiente o aprobación general para modelar.</p>',
        '<p>Desde la raíz: ejecutar apply_duplicates.py y verify_duplicate_application.py con Preparación/.venv/Scripts/python.exe. La primera aplicación crea una versión nueva; una repetición sobre un catálogo DUP01 verificado es un no-op. Se rechazan fuentes cambiadas, selección parcial y representantes que difieren de la revisión congelada.</p>',
        '<p><a href="ledger/exclusion_ledger.csv">Bitácora CSV de 604 exclusiones</a> · <a href="ledger/exclusion_ledger.parquet">Bitácora Parquet</a> · <a href="ledger/claim_id_aliases.csv">Alias CSV</a> · <a href="ledger/claim_id_aliases.parquet">Alias Parquet</a> · <a href="ledger/excluded_rows.parquet">Filas excluidas tipadas</a> · <a href="data/claims.parquet">Claims derivado</a> · <a href="dataset_catalog.json">Catálogo preparado</a> · <a href="tables/financial_reconciliation.csv">Conciliación completa</a> · <a href="verification.json">Verificación</a> · <a href="authorization.json">Autorización</a> · <a href="lineage.json">Linaje y reversión</a></p>',
        '<p>IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §§3.5–3.6: datos trazables, alcance de revisión y decisión humana. No hubo entrenamiento, proveedor externo, envío o delegación.</p></body></html>']
    (out/'informe.html').write_text('\n'.join(html),encoding='utf-8')


if __name__=='__main__':main()
