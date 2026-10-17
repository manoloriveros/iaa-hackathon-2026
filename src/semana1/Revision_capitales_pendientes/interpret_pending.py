"""Interpreta evidencia congelada, propone rutas y prepara casos; no aplica correcciones."""
from pathlib import Path
import json
import sys
from decimal import Decimal

import review_pending as r
import clean_data as c
import pandas as pd
import numpy as np
import pyarrow.parquet as pq

LABELS={
 'A_retrospective_D34':'Continuidad posterior ya identificada en D34',
 'B_later_with_prior_conflict':'Apoyo posterior con discrepancia anterior',
 'C_no_original_normal_reference':'Sin capital habitual original en la póliza',
 'D_CAP01_dependency_only':'Apoyo nuevo dependiente de CAP01',
 'E_TW_dependency':'Compatibilidad condicionada a interpretar T/W',
 'F_incomplete_context':'Contexto incompleto, sin diferencia conocida en el par',
 'G_other_conflicts':'Otras diferencias de riesgo, capital o distancia temporal'}
ACTIONS={
 'A_retrospective_D34':'Candidato a escenario retrospectivo /1000, separado de la preparación causal por corte; requiere autorización expresa para cualquier aplicación.',
 'B_later_with_prior_conflict':'Revisar el cambio de riesgo y la cadena completa; no trasladar automáticamente el criterio de un extremo al otro.',
 'C_no_original_normal_reference':'Conservar pendiente. Comparar distribución/dirección solo como indicios; solicitar unidad o soporte contractual antes de reparar.',
 'D_CAP01_dependency_only':'Mantener pendiente y registrar dependencia. No ampliar CAP01 en cascada; evaluar propuesta independiente con origen y alcance propios.',
 'E_TW_dependency':'Mantener pendiente. Resolver significado de T/W o aprobar expresamente una hipótesis separada; no activar CON01 por este análisis.',
 'F_incomplete_context':'Conservar los nulos. Verificar campo y riesgo; la ausencia no equivale a igualdad ni autoriza imputación para pasar la regla.',
 'G_other_conflicts':'Revisión individual; conservar capital y todas las referencias contradictorias. No elegir solo el ancla favorable.'}


def truth(f,col):return f[col].fillna(False).astype(bool)


def main(out):
    assert not (out/'manifest.json').exists()
    f=pd.read_parquet(out/'tables/pending_review.parquet')
    h=pd.read_parquet(out/'tables/all_affected_policy_histories.parquet')
    refs=pd.read_parquet(out/'tables/all_original_normal_references.parquet')
    for direction in ['prior','later']:
        prefix='original_'+direction+'_'
        context_known_difference=f[prefix+'changed_fields'].fillna('').ne('')
        incomplete=f[prefix+'missing_fields'].fillna('').ne('')
        times=truth(f,prefix+'nonoverlap')&f[prefix+'start_gap_days'].between(1,400)
        ratio=f[prefix+'what_if_div1000_over_reference'].between(.9,1.1)
        f[direction+'_missing_only_compatible']=times&ratio&incomplete&~context_known_difference
        f[direction+'_TW_only_compatible']=times&ratio&truth(f,prefix+'t_w_only_change')
        for tolerance in [.05,.1,.2]:
            f[direction+'_strict_'+str(int(tolerance*100))+'pct']=times&truth(f,prefix+'context_same')&f[prefix+'what_if_div1000_over_reference'].between(1-tolerance,1+tolerance)
    older_prior=refs.loc[refs.direction.eq('prior')&refs.strict_support_10pct]
    older_later=refs.loc[refs.direction.eq('later')&refs.strict_support_10pct]
    f['any_original_prior_support']=f.row_id.isin(older_prior.pending_row_id)
    f['any_original_later_support']=f.row_id.isin(older_later.pending_row_id)
    f['older_prior_cherry_pick_risk']=f.any_original_prior_support&~f.strict_prior_support
    f['later_reference_2025_only_evidence']=f.strict_later_support&truth(f,'original_later_reference_is_test_2025')
    f['CAP01_prior_dependency']=f.prepared_prior_support&~f.strict_prior_support
    f['nearest_prior_numeric_conflict']=(f.original_prior_exists&truth(f,'original_prior_context_same')&
        truth(f,'original_prior_nonoverlap')&f.original_prior_start_gap_days.between(1,400)&
        ~f.original_prior_what_if_div1000_over_reference.between(.9,1.1))
    f['review_group']=np.select([
        f.original_review_route.eq('retrospective_support_only'),f.strict_later_support,
        ~f.original_prior_exists&~f.original_later_exists,
        f.CAP01_prior_dependency,f.prior_TW_only_compatible|f.later_TW_only_compatible,
        f.prior_missing_only_compatible|f.later_missing_only_compatible],list(LABELS)[:-1],default='G_other_conflicts')
    f['group_label']=f.review_group.map(LABELS);f['proposed_treatment']=f.review_group.map(ACTIONS)
    f['retrospective_scenario_candidate_NOT_APPLIED']=f.review_group.eq('A_retrospective_D34')&~f.nearest_prior_numeric_conflict
    f['capital_change_applied']=False;f['correction_authorized']=False
    # Do not use a claim result to select a capital correction. Claim comparisons are a separate diagnostic.
    claims=pd.read_parquet(out/'tables/all_affected_claim_histories.parquet')
    periods=h[['row_id','policy_id','line','period_start','period_end','sum_insured','pending_frozen']]
    links=claims[['claim_id','policy_id','line','loss_date']].merge(periods,on=['policy_id','line'],how='left',validate='many_to_many')
    hit=links.loc[links.loss_date.between(links.period_start,links.period_end)].copy()
    assert hit.claim_id.is_unique
    cl=claims.merge(hit[['claim_id','row_id','sum_insured','pending_frozen']],on='claim_id',how='left',validate='one_to_one')
    cl['accepted']=cl.status.isin(['open','closed'])
    cl['observed_net_accepted_CU']=np.where(cl.accepted,cl.incurred_to_date-cl.recoveries,0.)
    cl['hypothetical_capital_CU']=np.where(cl.pending_frozen.fillna(False),cl.sum_insured/1000,np.nan)
    cl['accepted_incurred_gt_hypothetical_capital']=cl.accepted&cl.incurred_to_date.gt(cl.hypothetical_capital_CU)
    cl['diagnostic_only_not_used_for_correction_selection']=True
    current_ref=pq.read_table(c.ROOT/'Hackaton/Semana 1/Limpieza/runs/preaudit_20261016T211816Z_817285a5/tables/claim_period_assignment.parquet').to_pandas()
    assert cl.set_index('claim_id').row_id.sort_index().fillna('').equals(current_ref.set_index('claim_id').loc[sorted(cl.claim_id),'row_id'].fillna(''))
    r.save_frame(cl,out,'claim_assignment_and_capital_diagnostic')
    claim_stats=cl.groupby('row_id').agg(observed_claims=('claim_id','size'),accepted_claims=('accepted','sum'),
        observed_net_accepted_CU=('observed_net_accepted_CU','sum'),accepted_claim_incurred_above_hypothetical_cap=('accepted_incurred_gt_hypothetical_capital','sum'))
    f=f.merge(claim_stats,on='row_id',how='left',validate='one_to_one')
    for col in claim_stats.columns:f[col]=f[col].fillna(0)
    r.save_frame(f,out,'pending_assessment')
    r.save_frame(f.loc[f.retrospective_scenario_candidate_NOT_APPLIED,
        ['row_id','policy_id','line','source_table','sum_insured','what_if_div1000_CU','original_later_row_id',
         'original_later_source_table','original_later_period_start','later_reference_2025_only_evidence',
         'nearest_prior_numeric_conflict','capital_change_applied','correction_authorized']],out,'proposed_retrospective_scenario_NOT_APPLIED')
    groups=f.groupby(['review_group','group_label','line','source_table'],sort=True).agg(rows=('row_id','size'),
        policies=('policy_id','nunique'),pending_capital_CU=('sum_insured','sum'),hypothetical_capital_CU=('what_if_div1000_CU','sum'),
        accepted_claims=('accepted_claims','sum'),observed_net_accepted_CU=('observed_net_accepted_CU','sum')).reset_index()
    r.save_frame(groups,out,'group_summary')
    sensitivity=[]
    for line in ['buildings','contents']:
        part=f.loc[f.line.eq(line)]
        for tol in [5,10,20]:
            sensitivity.append({'line':line,'tolerance_pct':tol,'nearest_prior_original':int(part['prior_strict_'+str(tol)+'pct'].sum()),
                                'nearest_later_original':int(part['later_strict_'+str(tol)+'pct'].sum()),'diagnostic_only':True})
    r.save_frame(pd.DataFrame(sensitivity),out,'sensitivity')
    premium=[]
    for direction in ['prior','later']:
        p=f.loc[truth(f,'original_'+direction+'_premium_periods_comparable')&f['original_'+direction+'_exists']]
        ratio=p['original_'+direction+'_premium_ratio_pending_over_reference'].dropna()
        premium.append({'reference':direction,'comparable_pairs':len(p),'ratio_n':len(ratio),
                        'p05':float(ratio.quantile(.05)),'median':float(ratio.median()),'p95':float(ratio.quantile(.95)),
                        'basis':'Recorded quote premium, long periods within 5% duration; no linearity or annualization assumed.'})
    c.dump(out/'premium_context.json',premium)
    examples=[]
    def case(pid,title,interpretation,focus=None):
        q=f.loc[f.policy_id.eq(pid)].sort_values('period_start')
        assert len(q),pid
        examples.append({'policy_id':pid,'focus_row_id':focus or q.iloc[0].row_id,'title':title,'interpretation':interpretation})
    case('C00131038','El primer capital necesita un dato del año siguiente',
         'En 2021 figuran 17.300.000 CU; 2022 registra 17.600 CU. Dividir el primero daría 17.300 CU, compatible con esa secuencia. Ese respaldo es posterior y no estaba disponible al inicio de 2021.')
    case('B00382678','Continuidad posterior en edificios',
         'El primer capital alto de esta póliza tiene una referencia posterior de escala habitual con los campos exigidos conocidos e iguales. Revisar fechas y primas en la tabla: es evidencia retrospectiva, no un ancla anterior.')
    q=f.loc[f.review_group.eq('A_retrospective_D34')&f.later_reference_2025_only_evidence].sort_values(['line','row_id']).iloc[0]
    case(q.policy_id,'Una reparación de 2024 apoyada en test 2025',
         'El respaldo más próximo es una póliza de test 2025. Puede informar una auditoría retrospectiva de la unidad; no debe presentarse como información conocida al cotizar el periodo de 2024.',q.row_id)
    case('B00723804','T/W y un retorno posterior en el mismo inmueble',
         '2022 tiene 230.000 CU y T; 2023 registra 237.000.000 y W; 2024 vuelve a 244.000 con W. El respaldo posterior existe sin unificar T/W; la referencia anterior exige interpretar ese cambio, todavía pendiente.')
    case('B19256617','Dos capitales altos después de una mudanza',
         'La dirección cambia en julio de 2022: 196.000 CU en la anterior, 377.000.000 en la nueva y 388.000.000 en 2023. En 2024 aparecen 400.000 CU en la nueva. La mudanza puede justificar un cambio real de nivel; no copiar 196.000 ni encadenar reparaciones. La referencia posterior de 2024 queda a más de 400 días del primer segmento alto.')
    case('B01207490','Un nulo impide acreditar igualdad completa',
         'La continuidad numérica encaja con /1000, pero falta smoke_alarms en el par de comparación. Un campo desconocido no demuestra que el riesgo cambió ni que siguió igual. No rellenarlo para hacer pasar CAP01.')
    q=f.loc[f.review_group.eq('F_incomplete_context')&f.line.eq('contents')].sort_values('row_id').iloc[0]
    case(q.policy_id,'Faltantes en seguridad o bienes de valor',
         'La escala corregida sería compatible con una referencia próxima, pero faltan security_level o high_value_items. Esos campos describen el riesgo o la concentración de valor; se conserva el nulo y la duda.',q.row_id)
    case('B03631275','El único parecido anterior depende de T/W',
         'La división hipotética encaja con el capital anterior si se aceptara la equivalencia T/W. El periodo posterior cambia de dirección y construcción. Esta revisión no activa CON01 ni usa una mudanza como prueba de equivalencia.')
    case('B00774853','Alta 2025 sin capital habitual en su póliza',
         'Solo se observa el periodo 2025 con 209.000.000 CU. /1000 daría 209.000 y parece plausible frente a la distribución, pero no existe una cifra contractual independiente de esta póliza que lo confirme.')
    q=f.loc[f.review_group.eq('C_no_original_normal_reference')&f.policy_history_rows.gt(1)].sort_values(['policy_id','row_id']).iloc[0]
    case(q.policy_id,'Dos periodos altos no aportan una unidad independiente',
         'Ambos periodos publicados están en la banda alta. Dividirlos juntos haría una historia más plausible, pero repetir la misma escala no confirma su unidad.',q.row_id)
    case('B40325888','Una segunda reparación dependería de la primera',
         '2024 pasó de 232.000.000 a 232.000 CU por CAP01. 2025 conserva 239.000.000. Usar 232.000 como ancla abre una dependencia explícita de CAP01; no convierte 2024 en una referencia original ni autoriza una cascada.')
    case('C67134620','Dos años altos, una reparación y apoyo futuro',
         '2023 ya pasó de 43.500.000 a 43.500 CU por CAP01. 2024 mantiene 44.400.000 y 2025 registra 45.200. Hay apoyo retrospectivo y dependencia de la reparación previa; deben quedar identificados por separado.')
    case('C02948658','No elegir la referencia más conveniente',
         'En 2024 el capital cambia de 39.600 a 62.800 CU en septiembre. El registro 2025 de 40.400.000 daría 40.400 al dividir por mil: encaja con 39.600, pero queda 35,7% por debajo del capital más reciente. Saltar esa observación ocultaría un cambio real o una inconsistencia adicional.')
    case('B51302846','Una prima de un periodo corto no prueba la escala',
         'La referencia 2024 de 275.000 CU procede de CAP01. 2025 conserva 284.000.000 y una prima de 258,04 CU para un periodo que termina el 4 de marzo. La prima no viene acompañada de una base de prorrateo confirmada; no inferir el capital dividiendo prima por duración.')
    c.dump(out/'cases.json',examples)
    r.save_frame(pd.DataFrame(examples),out,'case_index')
    count_groups=f.review_group.value_counts().to_dict()
    summary={'scope':'Review only; no corrected dataset or audit feature is produced.','pending_rows':len(f),
        'unique_policies':int(f.policy_id.nunique()),'by_line':f.line.value_counts().to_dict(),
        'by_table':f.source_table.value_counts().to_dict(),'review_groups':count_groups,'group_labels':LABELS,
        'history_rows':len(h),'claim_history_rows':len(cl),'example_policies':len(examples),
        'strict_original_prior_nearest':int(f.strict_prior_support.sum()),'strict_original_later_nearest':int(f.strict_later_support.sum()),
        'later_supported_2025_references':int(f.later_reference_2025_only_evidence.sum()),
        'D34_retrospective_2025_references':int((f.review_group.eq('A_retrospective_D34')&f.later_reference_2025_only_evidence).sum()),
        'D34_retrospective_nearest_prior_numeric_conflicts':int((f.review_group.eq('A_retrospective_D34')&f.nearest_prior_numeric_conflict).sum()),
        'retrospective_scenario_candidates_NOT_APPLIED':int(f.retrospective_scenario_candidate_NOT_APPLIED.sum()),
        'retrospective_candidates_2025_reference':int((f.retrospective_scenario_candidate_NOT_APPLIED&f.later_reference_2025_only_evidence).sum()),
        'CAP01_dependent_prior_support':int(f.CAP01_prior_dependency.sum()),
        'older_prior_reference_conflict_cases':int(f.older_prior_cherry_pick_risk.sum()),
        'pending_rows_with_observed_claims':int(f.observed_claims.gt(0).sum()),
        'claims_assigned_to_pending_periods':int(f.observed_claims.sum()),
        'accepted_claims_incurred_above_hypothetical_cap':int(cl.accepted_incurred_gt_hypothetical_capital.sum()),
        'claims_before_observed_history':int(cl.row_id.isna().sum()),
        'marked_REN00_history_rows':int(h.audit_ren00.sum()),'marked_PRE00_claims':int(cl.audit_pre00.sum()),
        'all_pending_capital_CU':format(sum((Decimal(str(x)) for x in f.sum_insured),Decimal('0.00')),'.2f'),
        'hypothetical_div1000_capital_CU':format(sum((Decimal(str(x))/1000 for x in f.sum_insured),Decimal('0.00')),'.2f'),
        'hypothetical_sums_are_not_claim_cost_or_premium':True,
        'original_values_changed':0,'active_dataset_changed':False,'claims_changed':False,'dates_changed':False,
        'CAP01_applied_rows_unchanged':2073,'pending_rows_after_review':1454,'CON01_activated':False,
        'operational_T0_materialized':False,'models_trained':False,'independent_validation':False}
    c.dump(out/'summary.json',summary)
    c.dump(out/'proposal.json',{'status':'review_only_not_authorized_to_apply','rules':ACTIONS,'group_priority':list(LABELS),
        'recommendation':'Keep all 1454 source values pending. Do not expand CAP01 in bulk. If authorized later, freeze any new candidate row list and separate retrospective from cutoff-available evidence.',
        'first_separate_scenario':'867 of the 879 D34 retrospective-supported rows, excluding 12 with a nearest-prior known-equal-context capital discrepancy outside +/-10%. 111 of the 867 rely on a 2025 nearest normal reference. Arithmetic /1000 only; no operational correction approved.',
        'other_groups':'109 later-support rows with prior discrepancy, 108 no-reference rows, 2 new CAP01-dependent cases, 16 T/W-dependent residual cases, 202 incomplete-context residual cases, 138 other residual cases. Group priority prevents double counting.',
        'temporal_design':'A repair requiring later policy/test information is not contemporaneous evidence for the earlier tariff. Freeze separate cutoff-specific preparation; never inspect validation claim outcomes to choose a repair.',
        'modeling_if_unresolved':'Before fitting, compare explicit capital treatments inside temporal training folds: retain reported amount with documented transform, treat suspected values as unavailable with a train-only imputer, or an explicitly approved repair scenario. No option is applied here, and repair/audit routing metadata must remain outside predictors.',
        'claims':'Use claims only for separate reconciliation and plausibility diagnostics; do not scale, cap, zero or select repairs by realized loss. Reported/valuation cutoffs still apply.',
        'no_automatic_rules':['No divide every amount above a threshold','No T/W merge','No fill missing risk fields to satisfy equality','No copy another policy/customer capital','No use premium as a linear capital equation','No cascading CAP01','No selection of only the favorable older reference'],
        'source_questions':['Confirm monetary unit and any x1000 serialization issue by year/file/column.','Confirm whether capital is a per-event or aggregate maximum and any coverage sublimits.','Provide contract/endorsement capital changes and meaning of year-start resets after midterm changes.','Confirm T/W and missing risk field semantics.','Clarify the basis and proration of written_premium, including short periods.'],
        'IAA':['Documentation §2 and §§4–6','Governance §2.8','Professional considerations §3.2 and §§3.5–3.6']})
    c.dump(out/'protocol.json',{'frozen_cohort':'CAP01 pending_capitals.parquet, exactly 1454 row IDs, values unchanged.',
        'screening_thresholds_CU':r.THRESHOLDS,'thresholds_are_ground_truth':False,
        'comparison_fields':r.cap.FIELDS,'known_equal_means':'Known and equal only for the named fields; no statement that every unmeasured aspect of risk is unchanged.',
        'nearest_reference':'Earlier/later non-extreme original value in same policy. CAP01 references are separate, never independent.',
        'strict_context':'All named fields nonmissing and equal; only trim/casefold of construction labels. T and W stay distinct.',
        'temporal':'Non-overlapping original intervals and start dates 1–400 days apart.',
        'ratio':'Diagnostic (pending capital /1000) /reference capital between 0.90 and 1.10 for either direction. D34 uses inverse ratio for later support; frozen D34 routes are retained separately.',
        'multiple_references':'All original normal references retained; nearest contradiction may not be skipped to pass a rule.',
        'classification_priority':list(LABELS),'no_capital_changes':True,'no_funds_or_external_calls':True})
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
