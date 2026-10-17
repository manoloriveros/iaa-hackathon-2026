"""PRE00: analiza siniestros anteriores a la primera fila observada, sin alterar datos."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
import json
import shutil
import sys
import uuid

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).parent
sys.path.insert(0,str(ROOT/'Hackaton/Semana 1/Limpieza'))
import clean_data as c
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REQUEST = ('Ahora revisemos los 413 siniestros anteriores al primer periodo de póliza observado. '
           'Compara sus historiales, muestra casos concretos y propón cómo tratarlos sin modificar los datos todavía.')


def rec(f):
    return json.loads(f.to_json(orient='records',date_format='iso'))


def save(f,out,name,csv=True):
    f.to_parquet(out/'tables'/(name+'.parquet'),index=False)
    if csv:
        f.to_csv(out/'tables'/(name+'.csv'),index=False)


def money(f,col):
    return sum((Decimal(str(x)) for x in f[col]),Decimal('0')).quantize(Decimal('.01'))


def financial(f):
    accepted=f.loc[f.status.isin(['closed','open'])]
    paid=money(accepted,'paid_to_date');inc=money(accepted,'incurred_to_date');recover=money(accepted,'recoveries')
    return {'records':len(f),'accepted':len(accepted),'closed':int(f.status.eq('closed').sum()),
        'open':int(f.status.eq('open').sum()),'repudiated':int(f.status.eq('repudiated').sum()),
        'paid_accepted_CU':str(paid),'incurred_accepted_CU':str(inc),'recoveries_accepted_CU':str(recover),
        'case_reserve_accepted_CU':str(inc-paid),'net_accepted_CU':str(inc-recover)}


def main():
    active=ROOT/'Hackaton/Semana 1/Limpieza/current_dataset.json'
    pointer=json.loads(active.read_text('utf-8'));catpath=ROOT/pointer['catalog_workspace_relative']
    cat=json.loads(catpath.read_text('utf-8'));parent=ROOT/pointer['workspace_relative_run']
    claim_run=(ROOT/cat['claims']['workspace_relative_path']).parents[1]
    for directory in [parent,claim_run]:
        m=json.loads((directory/'manifest.json').read_text('utf-8'))
        assert all(c.digest(directory/e['path'])==e['sha256'] for e in m['files'])
    out=BASE/'runs'/(datetime.now(timezone.utc).strftime('prehistory_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8])
    for name in ['tables','evidence','source_snapshot','figures']:
        (out/name).mkdir(parents=True,exist_ok=False)
    for name in ['review_history.py','render_history.py','verify_history.py','verify_report.js','record_history.py']:
        shutil.copy2(BASE/name,out/'source_snapshot'/name)
    shutil.copy2(Path(c.__file__),out/'source_snapshot/clean_data.py')
    protected={p.relative_to(ROOT).as_posix():c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']:c.digest(ROOT/e['workspace_relative_path']) for e in cat.values()})
    assignment_path=claim_run/'tables/claim_period_assignment.parquet'
    for p in [active,catpath,parent/'manifest.json',claim_run/'manifest.json',assignment_path]:
        protected[p.relative_to(ROOT).as_posix()]=c.digest(p)
    for p in [ROOT/'Preparación/src/iaa_lab/data.py',ROOT/'Preparación/src/iaa_lab/predictor_guard.py',ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json']:
        protected[p.relative_to(ROOT).as_posix()]=c.digest(p)
    assert all(c.digest(ROOT/e['workspace_relative_path'])==e['sha256'] for e in cat.values())
    c.dump(out/'protected_hashes_before.json',protected)
    for name,p in {'active_index.json':active,'dataset_catalog.json':catpath,'parent_manifest.json':parent/'manifest.json',
        'DUP01_manifest.json':claim_run/'manifest.json','DUP01_assignment.parquet':assignment_path,
        'DUP01_aliases.parquet':ROOT/cat['claims']['aliases_workspace_relative_path'],
        'official_data_description.md':ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md',
        'IAA_priorities.md':ROOT/'Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md',
        'protocol_1_4.json':ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json'}.items():
        shutil.copy2(p,out/'evidence'/name)
    for name in ['MEMORIA_PROYECTO.md','ESTADO_PROYECTO.json','DECISIONES.md']:
        shutil.copy2(ROOT/'Preparación'/name,out/'evidence'/('before_'+name))
    c.dump(out/'request.json',{'messages':[{'role':'user','content':REQUEST}],'scope':'Review only. No data or assignment changes.',
        'ai_role':'Codex reconstructs histories, tests hypotheses and proposes treatment.','independent_validation':False,'external_ai_provider_used':False})
    frames=[]
    for line in ['motor','buildings','contents']:
        for prefix in ['policies','test']:
            name=prefix+'_'+line
            fields=['row_id','policy_id','customer_id','address_id','period_start','period_end','exposure','new_business','renewal_count','audit_ren00']
            x=pq.read_table(ROOT/cat[name]['workspace_relative_path'],columns=fields).to_pandas()
            x['line'],x['source_table']=line,name
            for col in ['period_start','period_end']:
                x[col]=pd.to_datetime(x[col])
            x['year']=x.period_start.dt.year;frames.append(x)
    periods=pd.concat(frames,ignore_index=True).sort_values(['line','policy_id','period_start','period_end','row_id'])
    first=periods.drop_duplicates(['line','policy_id']).copy()
    first=first.rename(columns={col:'first_'+col for col in first.columns if col not in ['line','policy_id']})
    claims=pq.read_table(ROOT/cat['claims']['workspace_relative_path']).to_pandas()
    for col in ['loss_date','report_date']:
        claims[col]=pd.to_datetime(claims[col])
    original_claim_fields=claims.columns.tolist()
    claims['accepted']=claims.status.isin(['closed','open'])
    claims['observed_net_CU']=np.where(claims.accepted,claims.incurred_to_date-claims.recoveries,0.)
    claims['loss_year']=claims.loss_date.dt.year
    j=claims[['claim_id','line','policy_id','loss_date']].merge(periods[['row_id','line','policy_id','period_start','period_end']],on=['line','policy_id'],how='left')
    hits=j.loc[j.loss_date.between(j.period_start,j.period_end)]
    assert not hits.claim_id.duplicated().any()
    claims=claims.merge(hits[['claim_id','row_id']],on='claim_id',how='left',validate='one_to_one').merge(first,on=['line','policy_id'],how='left',validate='many_to_one')
    claims['assignment_status']=np.where(claims.row_id.notna(),'unique_period',np.where(claims.loss_date.lt(claims.first_period_start),'before_first_observed_period','unresolved_other'))
    prior=pd.read_parquet(out/'evidence/DUP01_assignment.parquet').set_index('claim_id')
    actual=claims.set_index('claim_id')
    assert actual.row_id.fillna('NONE').equals(prior.row_id.reindex(actual.index).fillna('NONE'))
    assert actual.assignment_status.equals(prior.assignment_status.reindex(actual.index))
    assert not claims.assignment_status.eq('unresolved_other').any()
    save(claims[['claim_id','line','policy_id','loss_date','row_id','assignment_status']],out,'fresh_assignment',False)
    q=claims.loc[claims.assignment_status.eq('before_first_observed_period')].copy()
    assert len(q)==q.policy_id.nunique()==413
    customers=pq.read_table(ROOT/cat['customers']['workspace_relative_path'],columns=['customer_id','customer_since_year','prior_claims_5y']).to_pandas()
    q=q.merge(customers,left_on='first_customer_id',right_on='customer_id',validate='many_to_one')
    q['days_before_first_observed']=(q.first_period_start-q.loss_date).dt.days
    q['report_delay_days']=(q.report_date-q.loss_date).dt.days
    q['days_report_after_first_start']=(q.report_date-q.first_period_start).dt.days
    q['reported_strictly_before_first_start']=q.report_date.lt(q.first_period_start)
    legacy=q.first_period_start.eq(pd.Timestamp('2021-01-01')) & q.first_new_business.eq(False) & q.first_renewal_count.gt(0)
    newbiz=q.first_new_business.eq(True) & q.first_renewal_count.eq(0)
    q['review_class']=np.select([legacy,newbiz],['legacy_at_dataset_boundary','before_recorded_new_business'],default='other_unresolved')
    assert legacy.sum()==244 and newbiz.sum()==169 and (legacy|newbiz).all()
    q['classification_is_coverage_confirmation']=False
    q['loss_before_customer_since_year']=q.loss_year.lt(q.customer_since_year)
    q['loss_in_customer_since_year']=q.loss_year.eq(q.customer_since_year)
    # Other policies of a customer provide context, never substitute coverage in this policy/line.
    customer_first=periods.groupby('customer_id').period_start.min()
    q['earliest_observed_customer_period']=q.first_customer_id.map(customer_first)
    context=periods.loc[periods.customer_id.isin(q.first_customer_id)].copy()
    links=q[['claim_id','policy_id','line','loss_date','first_customer_id']].merge(context,
        left_on='first_customer_id',right_on='customer_id',suffixes=('_claim','_context'))
    other_hit=links.loc[links.loss_date.between(links.period_start,links.period_end) &
        (links.policy_id_claim.ne(links.policy_id_context)|links.line_claim.ne(links.line_context))]
    q['other_customer_policy_covers_loss_date']=q.claim_id.isin(other_hit.claim_id)
    save(other_hit,out,'other_policy_date_context')
    # Explore the tempting report-date join without applying it to claims.
    report_join=q[['claim_id','policy_id','line','report_date']].merge(periods[['row_id','policy_id','line','period_start','period_end']],on=['policy_id','line'])
    report_hit=report_join.loc[report_join.report_date.between(report_join.period_start,report_join.period_end)]
    assert not report_hit.claim_id.duplicated().any()
    q['report_date_matching_row_id']=q.claim_id.map(report_hit.set_index('claim_id').row_id)
    q['report_after_first_period_end']=q.report_date.gt(q.first_period_end)
    save(q,out,'frozen_prehistory_cohort')
    cohort_ids=set(q.policy_id); customer_ids=set(q.first_customer_id)
    own_history=periods.loc[periods.policy_id.isin(cohort_ids)]
    own_claims=claims.loc[claims.policy_id.isin(cohort_ids)].copy()
    save(own_claims,out,'all_affected_claim_histories')
    save(context,out,'all_customer_policy_context')
    selected_first=first.loc[first.policy_id.isin(cohort_ids)]
    save(selected_first,out,'affected_first_periods')
    alias=pd.read_parquet(out/'evidence/DUP01_aliases.parquet')
    alias=alias.loc[alias.retained_claim_id.isin(q.claim_id)]
    save(alias,out,'previous_duplicate_alias_context')
    # Financial reconciliation keeps the full economic total, but outside-window cost has no current row.
    books=[]
    for scope,part in [('all',claims),('assigned',claims.loc[claims.assignment_status.eq('unique_period')]),('prehistory',q)]:
        books.append({'scope':scope,**financial(part)})
    for line in ['motor','buildings','contents']:
        books.append({'scope':'prehistory_'+line,**financial(q.loc[q.line.eq(line)])})
    for label,part in q.groupby('review_class'):
        books.append({'scope':label,**financial(part)})
    c.dump(out/'financial_reconciliation.json',books)
    pd.DataFrame(books).to_csv(out/'tables/financial_reconciliation.csv',index=False)
    profile=q.groupby(['line','review_class','first_year'],dropna=False).agg(records=('claim_id','size'),
        net_observed_CU=('observed_net_CU','sum'),first_new_business=('first_new_business','first'),
        before_days_min=('days_before_first_observed','min'),before_days_max=('days_before_first_observed','max')).reset_index()
    save(profile,out,'cohort_profile')
    save(q.groupby(['line','loss_year','first_year',q.report_date.dt.year.rename('report_year')]).size().reset_index(name='records'),out,'year_alignment')
    save(q.groupby('loss_date').size().reset_index(name='records'),out,'loss_date_concentration')
    save(q.groupby(['review_class','prior_claims_5y']).size().reset_index(name='records'),out,'declared_prior_claims_context')
    save(q.groupby(['review_class','loss_before_customer_since_year','loss_in_customer_since_year']).size().reset_index(name='records'),out,'customer_entry_context')
    # A future history-count candidate would need reporting availability; these are diagnostic probes only.
    availability=own_history.merge(q[['policy_id','claim_id','report_date','loss_date','review_class']],on='policy_id',validate='many_to_one')
    availability['reported_before_period_start']=availability.report_date.lt(availability.period_start)
    availability['same_day_report_uncertain']=availability.report_date.eq(availability.period_start)
    availability['use_approved_as_predictor']=False
    save(availability,out,'report_availability_diagnostic')
    av=availability.groupby(['line','year']).agg(periods=('row_id','size'),reported_before_start=('reported_before_period_start','sum'),
        same_day=('same_day_report_uncertain','sum')).reset_index()
    save(av,out,'availability_by_year')
    # Hypothetical forced-first assignment: wrong temporal target; no corrected claim table is written.
    assigned=claims.loc[claims.row_id.notna() & claims.accepted]
    hypothetical=[]
    for year,part in q.groupby('first_year'):
        scope_periods=periods.loc[periods.row_id.isin(part.first_row_id)]
        scope_claims=claims.loc[claims.row_id.isin(part.first_row_id)]
        net_add=Decimal(financial(part)['net_accepted_CU'])
        before=Decimal(financial(scope_claims)['net_accepted_CU'])
        hypothetical.append({'first_period_year':int(year),'first_rows':len(part),'accepted_claims_forced':int(part.accepted.sum()),
            'net_CU_added_wrong_period':str(net_add),'existing_net_CU_in_first_rows':str(before),
            'hypothetical_net_CU_in_first_rows':str(before+net_add),'observed_exposure_unchanged':float(scope_periods.exposure.sum()),
            'applied':False,'reason_not_applied':'No source interval covers loss_date; adding cost without supported exposure misstates the period target.'})
    save(pd.DataFrame(hypothetical),out,'forced_first_period_sensitivity_NOT_APPLIED')
    # Select cases by questions, not by a predictive score.
    cases=[];used=set()
    def choose(label,why,pool,sort=None,ascending=True):
        pool=pool.loc[~pool.policy_id.isin(used)]
        pool=pool.sort_values(sort or ['line','policy_id'],ascending=ascending)
        assert len(pool),label
        r=pool.iloc[0];used.add(r.policy_id)
        cases.append({'case':len(cases)+1,'policy_id':r.policy_id,'line':r.line,'focus_claim_id':r.claim_id,
            'label':label,'interpretation':why,'cohort_member':True})
    choose('La copia DUP01 ya depurada','El alias excluido no vuelve a ser un siniestro. Conservar el representante y su prehistoria, sin reintroducir la copia para cuadrar conteos.',q.loc[q.claim_id.isin(alias.retained_claim_id)])
    choose('Mayor neto en una póliza ya renovada','La primera fila disponible es una renovación en 2021 y el cliente es anterior. Es compatible con cobertura histórica no incluida; no acredita un intervalo 2020 o sus condiciones.',q.loc[q.review_class.eq('legacy_at_dataset_boundary')],['observed_net_CU','policy_id'],False)
    choose('Nuevo negocio posterior a una pérdida importante','La ocurrencia precede a un alta registrada con cero renovaciones. Solicitar vínculo/contrato/fecha fuente; no asumir cobertura del asegurador ni mover la pérdida al alta.',q.loc[q.review_class.eq('before_recorded_new_business') & q.line.eq('buildings')],['observed_net_CU','policy_id'],False)
    choose('Ocurrencia 2020, alta 2021 y reporte 2022','Tres momentos distintos: ocurrencia, primera fila y reporte. El reporte posterior no convierte el evento en pérdida del periodo de reporte.',q.loc[q.policy_id.eq('M10432603')])
    choose('Contenidos: mayor neto prehistórico','El mismo criterio temporal se aplica a contenidos. La cobertura, capital y dirección anteriores al primer periodo no se reconstruyen desde los valores actuales.',q.loc[q.line.eq('contents')],['observed_net_CU','policy_id'],False)
    choose('Siniestro abierto anterior a la historia','Mantener pagado, reserva, recuperación y estado. La antigüedad del evento no basta para cerrarlo o igualar incurrido a pagado; la valoración única limita la reconstrucción histórica.',q.loc[q.status.eq('open')],['observed_net_CU','policy_id'],False)
    choose('Expediente repudiated','Preservar el expediente y su clasificación temporal. Su exclusión del coste aceptado sigue el estado del siniestro, no una corrección de fecha ni de cobertura.',q.loc[q.status.eq('repudiated')])
    choose('Separación temporal más corta','Incluso pocos días antes quedan fuera del intervalo inclusivo publicado. No hay tolerancia automática para desplazar fechas o ampliar el inicio.',q,['days_before_first_observed','policy_id'])
    choose('Separación temporal más larga','Una ampliación de centenares de días inventaría exposición, riesgo y condiciones de cobertura. La antigüedad del cliente no sustituye el contrato específico.',q,['days_before_first_observed','policy_id'],False)
    choose('Reporte después del primer periodo completo','El reporte cae en un año observado posterior, mientras la ocurrencia sigue fuera de los intervalos disponibles. Asignar por report_date ocultaría el problema y contaminaría ese año.',q.loc[q.policy_id.eq('B99888204')])
    choose('Cero siniestros declarados antes del ingreso','prior_claims_5y es una declaración de cinco años antes de ingresar. Su ventana y definición difieren del registro de siniestros del asegurador; no sumarlos ni corregirlo por esta diferencia.',q.loc[q.prior_claims_5y.eq(0) & q.review_class.eq('legacy_at_dataset_boundary')])
    control='B01979656'
    assert control not in cohort_ids
    control_claim=claims.loc[claims.policy_id.eq(control) & claims.loss_date.eq(pd.Timestamp('2023-12-31'))].iloc[0]
    cases.append({'case':len(cases)+1,'policy_id':control,'line':'buildings','focus_claim_id':control_claim.claim_id,
        'label':'Control: reporte tardío con ocurrencia cubierta',
        'interpretation':'Ocurrió el 31-12-2023 y se reportó el 04-01-2024. Tiene un intervalo 2023 que sí cubre la ocurrencia: se mantiene allí. Reporte tardío y ausencia de historia son conceptos distintos.','cohort_member':False})
    save(pd.DataFrame(cases),out,'case_index')
    selected=cohort_ids|{control};wide=[]
    for line in ['motor','buildings','contents']:
        for prefix in ['policies','test']:
            name=prefix+'_'+line
            x=pq.read_table(ROOT/cat[name]['workspace_relative_path']).to_pandas()
            x=x.loc[x.policy_id.isin(selected)].copy();x['line'],x['source_table']=line,name
            for col in ['period_start','period_end']:
                x[col]=pd.to_datetime(x[col])
            x['year']=x.period_start.dt.year;wide.append(x)
    wide=pd.concat(wide,ignore_index=True).sort_values(['line','policy_id','period_start','period_end','row_id'])
    selected_claims=claims.loc[claims.policy_id.isin(selected)].copy()
    save(wide,out,'all_affected_policy_histories')
    save(selected_claims,out,'cohort_and_control_claim_histories')
    case_ids={x['policy_id'] for x in cases}
    save(wide.loc[wide.policy_id.isin(case_ids)],out,'case_policy_histories')
    save(selected_claims.loc[selected_claims.policy_id.isin(case_ids)],out,'case_claim_histories')
    ph={pid:rec(h) for pid,h in wide.groupby('policy_id',sort=False)}
    ch={pid:rec(h) for pid,h in selected_claims.groupby('policy_id',sort=False)}
    histories={pid:{'policies':ph[pid],'claims':ch.get(pid,[])} for pid in ph}
    c.dump(out/'explorer_data.json',{'cases':cases,'index':rec(q),'histories':histories})
    legacybook=financial(q.loc[legacy.to_numpy()]);newbook=financial(q.loc[newbiz.to_numpy()])
    summary={'run':out.relative_to(ROOT).as_posix(),'created_utc':datetime.now(timezone.utc).isoformat(),'rule':'PRE00',
        'status':'review_only_no_data_or_assignment_changes','prehistory_records':413,'policies':int(q.policy_id.nunique()),
        'customers':int(q.first_customer_id.nunique()),'by_line':q.line.value_counts().to_dict(),'by_status':q.status.value_counts().to_dict(),
        'legacy_boundary_records':int(legacy.sum()),'new_business_records':int(newbiz.sum()),'legacy_financial':legacybook,'new_business_financial':newbook,
        'prehistory_financial':financial(q),'all_claim_financial':financial(claims),'assigned_claim_financial':financial(claims.loc[claims.row_id.notna()]),
        'before_days_min':int(q.days_before_first_observed.min()),'before_days_max':int(q.days_before_first_observed.max()),
        'before_days_median':float(q.days_before_first_observed.median()),'loss_on_minimum_date':int(q.loss_date.eq(pd.Timestamp('2020-12-01')).sum()),
        'minimum_loss_date':'2020-12-01','reported_before_first_start':int(q.reported_strictly_before_first_start.sum()),
        'reported_equal_first_start':int(q.report_date.eq(q.first_period_start).sum()),'reported_after_first_start':int(q.report_date.gt(q.first_period_start).sum()),
        'report_after_first_period_end':int(q.report_after_first_period_end.sum()),'report_date_would_match_a_row':int(q.report_date_matching_row_id.notna().sum()),
        'other_policy_customer_date_matches':int(q.other_customer_policy_covers_loss_date.sum()),
        'cohort_policy_history_rows':len(own_history),'cohort_all_claim_history_rows':len(own_claims),
        'cohort_2025_period_rows':int(own_history.year.eq(2025).sum()),'cohort_REN00_overlap_policies':int(q.first_audit_ren00.sum()),
        'previous_duplicate_aliases':len(alias),'case_count':len(cases),'control_policies':1,
        'data_modified':False,'dates_modified':False,'claims_reassigned':False,'active_dataset_changed':False,
        'operational_T0_materialized':False,'predictors_added':False,'models_trained':False,'independent_validation':False,'source_coverage_confirmed':False}
    c.dump(out/'summary.json',summary)
    c.dump(out/'proposal.json',{'rule':'PRE00','status':'review_only_no_application_authorized',
        'recommended':'Keep all 413 source claims unchanged as before_first_observed_period in reconciliation, outside the target of currently provided policy intervals.',
        'legacy_group':'244 renewed policies at 2021 boundary are compatible with left-truncated coverage history, not proof of 2020 contract conditions.',
        'new_business_group':'169 losses before recorded new business need contract/link/date/source clarification. Do not infer the insurer was on risk or zero out recorded accepted amounts.',
        'target':'Assign cost to a period only when its published interval covers loss_date. Report_date is not the occurrence target date. No forced first-row attachment.',
        'history_features':'Potential prior-report history only after report_date strictly before each prediction cutoff and after source attribution/meaning review. At first observed inception no record passes that reporting condition. Final 2024 status and amounts are not historical snapshots.',
        'prior_claims_5y':'Declared five years before customer entry, not a rolling count. Do not add or overwrite using these records without overlap and window evidence.',
        'no_fabrication':['No backdated policy start','No synthetic exposure or 2020 policy row','No loss/report date shift','No transfer to another line/customer policy','No alias reinstatement','No current paid/incurred/status treated as known in earlier years'],
        'future_audit_if_authorized':'Separate audit_pre00 on a frozen claim list, preserving original dates, payload and assignment; exclude audit metadata from predictors. Not applied in this review.',
        'source_questions':['Are pre-window claims deliberate run-off/migrated history?','Can new_business follow coverage under the same policy_id?','Were dates floored at 2020-12-01? What do minimum-date concentrations mean?',
            'Can prior contract periods, inception dates, change history and claim linkage be supplied?','What prior claims had been reported and available at each underwriting cutoff?'],
        'uncertainty':'Before first observed row is not equivalent to before true contract inception or an uncovered claim. Incomplete histories and date-generation artifacts cannot be distinguished without source evidence.',
        'IAA':['Documentation §2 and §§4–6','Governance §2.8','Professional considerations §3.2, §3.3 and §§3.5–3.6']})
    assert all(c.digest(ROOT/p)==sha for p,sha in protected.items())
    print(json.dumps({'run':str(out),'summary':summary,'cases':cases},ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
