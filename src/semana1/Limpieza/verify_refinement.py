"""Verifica CAT01/AGE01, conserva pendientes y publica la versión preparada."""
from datetime import date
import base64
import json

import refine_data as a
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def calendar_age(start,birth):
    try:anniversary=birth.replace(year=start.year)
    except ValueError:anniversary=date(start.year,3,1)
    return start.year-birth.year-int(start<anniversary)


def main():
    out=a.ROOT/json.loads((a.BASE/'current_refinement.json').read_text(encoding='utf-8'))['workspace_relative_run']
    checks=[]
    def check(name,passed):
        checks.append({'check':name,'passed':bool(passed)})
        if not passed:
            a.c.dump(out/'verification.json',{'passed':False,'checks':checks});raise AssertionError(name)
    parent=json.loads((a.PARENT/'dataset_catalog.json').read_text(encoding='utf-8'))
    cat=json.loads((out/'dataset_catalog.json').read_text(encoding='utf-8'))
    protected=json.loads((out/'protected_hashes_before.json').read_text(encoding='utf-8'))
    check('all_17_original_and_prior_data_files_unchanged',len(protected)==17 and all(a.c.digest(a.ROOT/p)==h for p,h in protected.items()))
    manifest=json.loads((a.PARENT/'manifest.json').read_text(encoding='utf-8'))
    check('every_CAP01_manifest_entry_unchanged',all(a.c.digest(a.PARENT/e['path'])==e['sha256'] for e in manifest['files']))
    check('catalog_exact_11_tables_hashes_valid',set(cat)==set(parent) and len(cat)==11 and all(a.c.digest(a.ROOT/e['workspace_relative_path'])==e['sha256'] for e in cat.values()))
    birth_frame=pq.read_table(a.ROOT/parent['customers']['workspace_relative_path'],columns=['customer_id','date_of_birth']).to_pandas()
    birth_lookup=birth_frame.set_index('customer_id').date_of_birth
    logs=pq.read_table(out/'ledger/all_changes.parquet').to_pandas()
    check('combined_ledger_703146_cells_unique',len(logs)==703146 and not logs.duplicated(['source_table','row_id','field']).any())
    test_ids=[]
    for name in a.c.TABLES:
        before=pq.read_table(a.ROOT/parent[name]['workspace_relative_path'])
        after=pq.read_table(a.ROOT/cat[name]['workspace_relative_path'])
        check(name+':schema_metadata_rows',before.schema.equals(after.schema,check_metadata=True) and before.num_rows==after.num_rows)
        allowed=['policyholder_age'] if name in a.AGE_EXPECTED else []
        if name in a.CAT_EXPECTED:allowed.append('construction_type')
        check(name+':all_other_values_identical_including_capital_ids_exposure',all(before[col].equals(after[col]) for col in before.column_names if col not in allowed))
        if not allowed:check(name+':motor_byte_identical',parent[name]['sha256']==cat[name]['sha256'])
        row_ids=after['row_id'].to_pylist();check(name+':row_ids_unique',len(set(row_ids))==len(row_ids))
        for col in allowed:
            ledger=pq.read_table(out/'ledger'/f'{name}_{col}.parquet').to_pandas()
            old,new=before[col].to_pandas(),after[col].to_pandas()
            idx=ledger.source_row.to_numpy(dtype=int)
            check(name+':'+col+':complete_change_positions',np.array_equal(np.flatnonzero(old.ne(new)),idx)
                  and ledger.row_id.tolist()==[row_ids[i] for i in idx])
            check(name+':'+col+':typed_ledger_matches_values',ledger.old.tolist()==old.iloc[idx].tolist() and ledger.new.tolist()==new.iloc[idx].tolist())
            consolidated=logs[(logs.source_table==name)&(logs.field==col)]
            check(name+':'+col+':consolidated_ledger_complete',consolidated.source_row.tolist()==ledger.source_row.tolist()
                and consolidated.old.tolist()==ledger.old.astype('string').tolist() and consolidated.new.tolist()==ledger.new.astype('string').tolist())
            restored=new.copy();restored.iloc[idx]=ledger.old.to_numpy()
            check(name+':'+col+':exact_reversal',restored.equals(old))
            if col=='construction_type':
                expected=old.replace(a.CAT_MAP)
                check(name+':case_map_idempotent_no_semantic_merge',new.equals(expected) and new.replace(a.CAT_MAP).equals(new)
                    and old.str.casefold().eq(new).all())
                check(name+':expected_category_changes',len(ledger)==a.CAT_EXPECTED[name])
            else:
                starts=after['period_start'].to_pylist()
                births=after['customer_id'].to_pandas().map(birth_lookup).tolist()
                expected=[calendar_age(s,b) for s,b in zip(starts,births)]
                check(name+':all_ages_independent_calendar_arithmetic',new.tolist()==expected)
                check(name+':expected_age_changes',len(ledger)==a.AGE_EXPECTED[name] and (ledger.new-ledger.old).abs().eq(1).all())
        if name.startswith('test_'):test_ids.extend(row_ids)
    sample=pq.read_table(a.ROOT/cat['sample_submission']['workspace_relative_path'],columns=['row_id']).column(0).to_pylist()
    check('test_626639_ids_match_sample_once',len(test_ids)==len(set(test_ids))==len(sample)==626639 and set(test_ids)==set(sample))
    for name in set(cat)-set(a.c.TABLES):check(name+':original_reference_unchanged',cat[name]==parent[name])
    quality=json.loads((out/'quality_summary.json').read_text(encoding='utf-8'))
    check('quality_pass_profiles_all_7826877_rows',quality['rows_profiled']==7826877 and quality['tables']==11 and not quality['strict_failures'])
    check('undefined_construction_codes_preserved',quality['unresolved_construction_rows']==107817)
    check('NCB_cases_preserved_for_review',quality['NCB_review_rows']==161822)
    check('claims_414_pre_history_dates_not_forced',quality['claims_before_observed_history']==414)
    pending=pq.read_table(a.PARENT/'tables/pending_capitals.parquet').to_pandas()
    for name,group in pending.groupby('source_table'):
        f=pq.read_table(a.ROOT/cat[name]['workspace_relative_path'],columns=['row_id','sum_insured']).to_pandas().set_index('row_id')
        check(name+':pending_capitals_exactly_preserved',np.array_equal(f.loc[group.row_id,'sum_insured'].to_numpy(),group.sum_insured.to_numpy()))
    check('calendar_age_birthday_and_day_before',calendar_age(date(2021,11,5),date(1978,11,5))==43 and calendar_age(date(2021,11,4),date(1978,11,5))==42)
    rejected=False
    try:a.full_age(pd.Series([date(2025,2,28)]),pd.Series([date(2000,2,29)]))
    except ValueError:rejected=True
    check('ambiguous_leap_birthday_rejected',rejected)
    result={'passed':True,'checks_count':len(checks),'checks':checks,'category_changes':700210,'age_changes':2936,
        'additional_capital_changes':0,'pending_capitals_unchanged':1454,'independent_validation':False,'approved_for_modeling':False}
    a.c.dump(out/'verification.json',result)
    report(out,result,quality)
    entries=[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':a.c.digest(p)}
             for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json']
    a.c.dump(out/'manifest.json',{'count':len(entries),'files':entries})
    pointer={'workspace_relative_run':out.relative_to(a.ROOT).as_posix(),'status':'verified_CAT01_AGE01_CAP01_inherited',
        'catalog_workspace_relative':(out/'dataset_catalog.json').relative_to(a.ROOT).as_posix(),
        'capital_changes_inherited':2073,'pending_capitals':1454,'category_changes':700210,'age_changes':2936,'approved_for_modeling':False}
    a.c.dump(a.BASE/'current_refinement.json',pointer)
    temporary=a.BASE/'current_dataset.pending.json';a.c.dump(temporary,pointer);temporary.replace(a.BASE/'current_dataset.json')
    print(json.dumps({'passed':True,'checks':len(checks),'quality_checks':quality['checks'],'category_changes':700210,'age_changes':2936,'run':str(out)}))


def report(out,result,q):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    years=pd.read_csv(out/'tables/construction_by_year.csv')
    p=years.pivot(index='year',columns='construction_type',values='rows').fillna(0)
    share=p.div(p.sum(axis=1),axis=0)*100
    missing=pd.read_csv(out/'tables/missingness.csv').nlargest(10,'fraction')
    fig,axes=plt.subplots(1,2,figsize=(12,4.5))
    axes[0].plot(share.index,share['t'],'o-',label='Código t, significado pendiente')
    axes[0].plot(share.index,share['w'],'o-',label='Código w, significado pendiente')
    axes[0].set_xticks(share.index);axes[0].set_ylabel('% de filas de edificios');axes[0].set_title('Cambio de codificación en 2023');axes[0].legend(fontsize=8)
    labels=missing.table.str.replace('policies_','train_',regex=False)+': '+missing.column
    axes[1].barh(labels[::-1],(100*missing.fraction)[::-1]);axes[1].set_xlabel('% de valores ausentes');axes[1].set_title('Faltantes conservados, sin imputación')
    fig.tight_layout();fig.savefig(out/'figures/quality.png',dpi=140);plt.close(fig)
    image=base64.b64encode((out/'figures/quality.png').read_bytes()).decode()
    summary=pd.read_csv(out/'tables/change_summary.csv')
    age_logs=pd.concat([pq.read_table(out/'ledger'/f'{name}_policyholder_age.parquet').to_pandas().head(3) for name in a.AGE_EXPECTED],ignore_index=True)
    open_issues=[
      {'issue':'construction_material_codes','rows':107817,'action':'Keep t and w separate; meaning and any cross-code equivalence unresolved.'},
      {'issue':'construction_temporal_code_break','rows':q['same_address_t_to_w_transitions'],'action':'Observed same-policy/same-address t→w transitions. Investigate source recoding; no semantic mapping applied.'},
      {'issue':'NCB_gt_license_tenure','rows':161822,'action':'Preserve; clarify definition and carry-over before capping.'},
      {'issue':'remaining_extreme_capitals','rows':1454,'action':'Preserve CAP01 pending set; no cascading or additional correction.'},
      {'issue':'claims_before_observed_policy_history','rows':414,'action':'Keep original event dates; separate from covered-period target.'},
      {'issue':'missing_numeric_and_categorical','rows':None,'action':'Preserve nulls; model-specific imputers, if chosen, fit inside temporal training folds.'},
      {'issue':'availability_and_ultimate','rows':None,'action':'Annual future weather, unversioned masters, contacts/telematics timing and development/IBNR remain unresolved.'}]
    a.c.dump(out/'open_issues.json',open_issues)
    t=lambda f:f.to_html(index=False,na_rep='Sin dato')
    sections=['<!doctype html><html lang="es"><meta charset="utf-8"><title>Refinamiento de datos</title>',
      '<style>body{font:16px/1.6 system-ui;max-width:1200px;margin:40px auto;padding:0 24px;color:#182b3c}table{border-collapse:collapse;display:block;overflow:auto;font-size:13px}td,th{padding:9px;border-bottom:1px solid #ddd;text-align:right}th{background:#edf3f8}img{max-width:100%}a{color:#075b9b}</style>',
      '<h1>Refinamiento CAT01/AGE01 y revisión multitabla</h1>',
      '<p>Se normalizaron 700.210 etiquetas de construcción y recalcularon 2.936 edades de tomadores de hogar. Se conservaron los originales, versiones previas, 2.073 capitales CAP01 y los 1.454 capitales pendientes. No se imputaron nulos ni se cambió driver_age.</p>',
      '<h2>Ajustes por tabla</h2>',t(summary),
      '<p>CAT01 agrupa únicamente variantes de mayúscula/minúscula. AGE01 usa años cumplidos desde el nacimiento del tomador hasta el inicio de cobertura. Se adopta el maestro de nacimiento como referencia del proyecto; el dato anterior queda en bitácora. No se encontró el caso ambiguo de nacimiento 29 de febrero con inicio 28 de febrero en año no bisiesto; el código lo rechazaría para revisar la convención.</p>',
      '<h2>Ejemplos de edad</h2>',t(age_logs[['source_table','row_id','customer_id','date_of_birth','period_start','old','new']]),
      '<h2>Qué sigue requiriendo interpretación</h2>',
      f'<img alt="Cambio temporal de códigos y valores ausentes" src="data:image/png;base64,{image}">',
      f'<p>t aparece en 2021–2022 y w en 2023–2025. Hay {q["same_address_t_to_w_transitions"]:,} transiciones t→w en la misma póliza y dirección. Apunta a investigar una recodificación, pero no confirma que el material sea timber o que ambas etiquetas sean equivalentes. Se conservan ambas. Los códigos no se fusionan ni se tratan como un nuevo tipo físico probado.</p>',
      '<p>La ausencia de telemática coincide exactamente con no haber optado por ella, sin contradicciones. No significa puntuación cero. El 2,5% aproximado de faltantes en varios campos no basta para afirmar que sean aleatorios. campaign_code puede faltar cuando no hubo campaña o no se registró; no se sustituye por una interpretación inventada.</p>',
      t(pd.DataFrame(q['review_findings'])),
      '<p>Los 161.822 casos NCB mayor que antigüedad de licencia se conservan; no se fija NCB=min(NCB,licencia). Los 414 siniestros anteriores al primer periodo observado quedaron separados en el diagnóstico, con estado before_first_observed_period: no se alteraron fechas ni se forzó cobertura. No se construyó aquí una etiqueta última.</p>',
      '<h2>Verificación y continuidad</h2>',
      f'<p>Se recorrieron las once tablas y sus {q["rows_profiled"]:,} filas; {q["checks"]} controles de calidad, sin fallos estrictos. Las incidencias semánticas permanecen abiertas. Pasaron {result["checks_count"]} controles técnicos específicos de la transformación, incluidos reversión, calendario independiente, idempotencia de categorías, capitales pendientes, catálogo y cobertura de test. La revisión es propia asistida por IA, no validación independiente ni aprobación general para modelar.</p>',
      '<p>Las reglas de imputación y disponibilidad de predictores se decidirán dentro del protocolo temporal de modelado. La limpieza no sustituye la definición de T0, desarrollo/IBNR, variables disponibles al cotizar o validación por corte. Referencias: diccionario oficial archivado; IAA Documentación §2, Gobernanza §2.8 y Consideraciones profesionales §§3.2 y 3.5–3.6.</p>',
      '<p><a href="ledger/all_changes.csv">Bitácora CSV</a> · <a href="verification.json">Verificación</a> · <a href="quality_summary.json">Resumen de calidad</a> · <a href="tables/quality_checks.csv">Controles completos CSV</a> · <a href="tables/missingness.csv">Faltantes CSV</a> · <a href="open_issues.json">Decisiones pendientes</a> · <a href="dataset_catalog.json">Catálogo activo</a> · <a href="rules.json">Reglas</a></p></html>']
    (out/'informe.html').write_text('\n'.join(sections),encoding='utf-8')


if __name__=='__main__':main()
