"""CAT01 y AGE01: refinamiento reversible sobre CAP01, sin ampliar la corrección de capitales."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import uuid

import clean_data as c
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT, BASE = c.ROOT, c.BASE
PARENT = BASE / 'runs/capfix_20261016T184904Z_099a22b1'
CAT_MAP = {'Brick':'brick','BRICK':'brick','NON_STANDARD':'non_standard','STONE':'stone','T':'t','W':'w'}
CAT_EXPECTED = {'policies_buildings':555824,'test_buildings':144386}
AGE_EXPECTED = {'policies_buildings':1122,'test_buildings':300,'policies_contents':1209,'test_contents':305}
REQUEST = 'COntinua con el analisis y ajuste de la data'


def full_age(starts, births):
    s, b = pd.to_datetime(starts), pd.to_datetime(births)
    if s.isna().any() or b.isna().any() or (s < b).any():
        raise ValueError('Missing or future birth date; do not invent an age.')
    ambiguous = b.dt.month.eq(2) & b.dt.day.eq(29) & ~s.dt.is_leap_year & s.dt.month.eq(2) & s.dt.day.eq(28)
    if ambiguous.any():
        raise ValueError('Leap-birthday convention needs review; no implicit assumption on 28 February.')
    return s.dt.year-b.dt.year-((s.dt.month<b.dt.month)|((s.dt.month==b.dt.month)&(s.dt.day<b.dt.day))).astype('int64')


def main():
    manifest=json.loads((PARENT/'manifest.json').read_text(encoding='utf-8'))
    assert all(c.digest(PARENT/e['path'])==e['sha256'] for e in manifest['files'])
    assert json.loads((PARENT/'verification.json').read_text(encoding='utf-8'))['passed']
    ident=datetime.now(timezone.utc).strftime('refine_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8]
    out=BASE/'runs'/ident
    for name in ['data','ledger','tables','source_snapshot','evidence','figures']:(out/name).mkdir(parents=True,exist_ok=False)
    for name in ['refine_data.py','audit_quality.py','verify_refinement.py','REFINAMIENTO.md','clean_data.py']:
        shutil.copy2(BASE/name,out/'source_snapshot'/name)
    catalog=json.loads((PARENT/'dataset_catalog.json').read_text(encoding='utf-8'))
    protected={p.relative_to(ROOT).as_posix():c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({v['workspace_relative_path']:c.digest(ROOT/v['workspace_relative_path']) for v in catalog.values()})
    c.dump(out/'protected_hashes_before.json',protected)
    shutil.copy2(PARENT/'manifest.json',out/'evidence/parent_manifest.json')
    shutil.copy2(PARENT/'verification.json',out/'evidence/parent_verification.json')
    dictionary=ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md'
    shutil.copy2(dictionary,out/'evidence/official_data_description.md')
    c.dump(out/'rules.json',{
        'CAT01':{'field':'construction_type','map':CAT_MAP,'meaning':'Case aliases only. t and w stay separate unresolved codes; neither mapped to timber.',
                 'expected_changes':CAT_EXPECTED},
        'AGE01':{'field':'policyholder_age','formula':'Completed calendar years from customers.date_of_birth at period_start',
                 'source_priority':'Birth date in unique customer master is the project reference for this derived age; reported source age retained in ledger.',
                 'gates':'Same customer key; complete nonfuture dates; observed discrepancy at most one year; ambiguous leap-birthday convention rejected.',
                 'expected_changes':AGE_EXPECTED,'driver_age':'Unchanged: main driver may differ from policyholder.'},
        'inherited':['ID01','EXP01','CAP01 frozen cohort'],
        'capital_scope':'No additional capital corrections; all 1454 pending values remain unchanged.',
        'missing_values':'Preserved; no arbitrary zero, median or forward-fill imputation.',
        'human_instruction':REQUEST,'source_dictionary_sha256':c.digest(dictionary),
        'review_scope':'Own AI-assisted verification; no independent validation or complete modeling approval.'})
    c.dump(out/'task_origin.json',{'messages':[{'role':'user','content':REQUEST}],
        'implementation_choices':'Reversible case normalization and calendar-age recalculation under supplied dictionary; no expansion of CAP01.',
        'ai_contribution':'Codex generated code, diagnostics and report; no external provider call.'})
    customers=pq.read_table(ROOT/catalog['customers']['workspace_relative_path'],columns=['customer_id','date_of_birth']).to_pandas()
    assert customers.customer_id.is_unique and customers.date_of_birth.notna().all()
    birth_lookup=customers.set_index('customer_id').date_of_birth
    new_catalog,summary,all_logs={},[],[]
    for name,entry in catalog.items():
        source=ROOT/entry['workspace_relative_path'];assert c.digest(source)==entry['sha256']
        if name not in c.TABLES:
            new_catalog[name]=dict(entry);continue
        dest=out/'data'/f'{name}.parquet'
        cat_count=age_count=0
        if name not in AGE_EXPECTED:
            shutil.copy2(source,dest)
        else:
            table=pq.read_table(source);original=table
            columns=['row_id','customer_id','period_start','policyholder_age']+(['construction_type'] if name in CAT_EXPECTED else [])
            f=table.select(columns).to_pandas()
            birth=f.customer_id.map(birth_lookup)
            age=full_age(f.period_start,birth)
            assert (age-f.policyholder_age).abs().le(1).all()
            age_mask=age.ne(f.policyholder_age);age_count=int(age_mask.sum());assert age_count==AGE_EXPECTED[name]
            log=pd.DataFrame({'source_table':name,'source_row':f.index[age_mask],'row_id':f.loc[age_mask,'row_id'],
                'customer_id':f.loc[age_mask,'customer_id'],'date_of_birth':birth[age_mask],
                'period_start':f.loc[age_mask,'period_start'],'old':f.loc[age_mask,'policyholder_age'],
                'new':age[age_mask],'rule':'AGE01','field':'policyholder_age'})
            log.to_parquet(out/'ledger'/f'{name}_policyholder_age.parquet',index=False)
            all_logs.append(log[['source_table','source_row','row_id','field','old','new','rule']].assign(
                old=log.old.astype('string'),new=log.new.astype('string'),value_type='int64'))
            table=table.set_column(table.schema.get_field_index('policyholder_age'),table.schema.field('policyholder_age'),
                pa.array(age,type=table.schema.field('policyholder_age').type))
            if name in CAT_EXPECTED:
                cat=f.construction_type.replace(CAT_MAP)
                mask=cat.ne(f.construction_type);cat_count=int(mask.sum());assert cat_count==CAT_EXPECTED[name]
                log=pd.DataFrame({'source_table':name,'source_row':f.index[mask],'row_id':f.loc[mask,'row_id'],
                    'old':f.loc[mask,'construction_type'],'new':cat[mask],'rule':'CAT01','field':'construction_type'})
                log.to_parquet(out/'ledger'/f'{name}_construction_type.parquet',index=False)
                all_logs.append(log[['source_table','source_row','row_id','field','old','new','rule']].assign(value_type='string'))
                table=table.set_column(table.schema.get_field_index('construction_type'),table.schema.field('construction_type'),
                    pa.array(cat,type=table.schema.field('construction_type').type))
            pq.write_table(table,dest,compression='zstd')
            summary.append({'table':name,'rows':table.num_rows,'category_changes':cat_count,'age_changes':age_count,
                            'capital_changes':0})
            print(json.dumps(summary[-1]),flush=True)
        new_catalog[name]={'workspace_relative_path':dest.relative_to(ROOT).as_posix(),'layer':'derived',
            'sha256':c.digest(dest),'parent_workspace_relative_path':entry['workspace_relative_path'],
            'parent_sha256':entry['sha256'],'category_changes':cat_count,'age_changes':age_count,'capital_changes':0}
    combined=pd.concat(all_logs,ignore_index=True)
    combined.to_parquet(out/'ledger/all_changes.parquet',index=False)
    combined.to_csv(out/'ledger/all_changes.csv',index=False)
    pd.DataFrame(summary).to_csv(out/'tables/change_summary.csv',index=False)
    c.dump(out/'summary.json',summary);c.dump(out/'dataset_catalog.json',new_catalog)
    c.dump(out/'lineage.json',{'parent_run':PARENT.relative_to(ROOT).as_posix(),
        'inherited_rules':['ID01','EXP01','CAP01'],'parent_lineage':(PARENT/'lineage.json').relative_to(ROOT).as_posix(),
        'inherited_pending_capitals':(PARENT/'tables/pending_capitals.parquet').relative_to(ROOT).as_posix(),
        'active_index_published_after_verification':True})
    from audit_quality import audit
    audit(new_catalog,out)
    after={p:c.digest(ROOT/p) for p in protected};assert protected==after
    c.dump(out/'protected_hashes_after.json',after)
    c.dump(out/'run.json',{'run_id':ident,'utc':datetime.now(timezone.utc).isoformat(),
        'category_changes':sum(x['category_changes'] for x in summary),'age_changes':sum(x['age_changes'] for x in summary),
        'changed_cells':len(combined),'additional_capital_changes':0,'originals_modified':False,
        'old_versions_modified':False,'models_trained':False,'external_AI_calls':False,'independent_validation':False,
        'source_master_birth_date_assumption':'Explicit project reference; not independent confirmation of birth dates.',
        'python':__import__('sys').version,'pandas':pd.__version__,'pyarrow':pa.__version__})
    c.dump(BASE/'current_refinement.json',{'workspace_relative_run':out.relative_to(ROOT).as_posix(),'status':'pending_verification'})
    print('RUN='+str(out),flush=True)


if __name__=='__main__':main()
