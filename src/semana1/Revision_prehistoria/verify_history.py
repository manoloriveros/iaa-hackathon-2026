"""Verificación propia desde fuentes: cohorte, historiales, dinero y cortes de reporte."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'Hackaton/Semana 1/Limpieza'))
import clean_data as c
import pandas as pd
import pyarrow.parquet as pq


def amount(f,col):
    return sum((Decimal(str(v)) for v in f[col]),Decimal('0')).quantize(Decimal('.01'))


def main(out):
    if (out/'manifest.json').exists():
        m=json.loads((out/'manifest.json').read_text('utf-8'));assert all(c.digest(out/e['path'])==e['sha256'] for e in m['files'])
        print(json.dumps({'status':'closed_verified_review_intact_no_rewrite'}));return
    checks=[]
    def check(name,condition):
        checks.append({'check':name,'passed':bool(condition)})
        if not condition:raise AssertionError(name)
    s=json.loads((out/'summary.json').read_text('utf-8'));cat=json.loads((out/'evidence/dataset_catalog.json').read_text('utf-8'))
    for p,sha in json.loads((out/'protected_hashes_before.json').read_text('utf-8')).items():
        check('Protected source/active/code unchanged: '+p,c.digest(ROOT/p)==sha)
    q=pd.read_parquet(out/'tables/frozen_prehistory_cohort.parquet')
    prior=pd.read_parquet(out/'evidence/DUP01_assignment.parquet')
    expected=set(prior.loc[prior.assignment_status.eq('before_first_observed_period'),'claim_id'])
    check('Exactly frozen 413 DUP01 claim IDs',set(q.claim_id)==expected and len(q)==413 and q.claim_id.is_unique)
    check('413 distinct policies and customers',q.policy_id.nunique()==q.first_customer_id.nunique()==413)
    check('296 motor, 67 buildings, 50 contents',q.line.value_counts().to_dict()=={'motor':296,'buildings':67,'contents':50})
    data=json.loads((out/'explorer_data.json').read_text('utf-8'))
    wide=pd.read_parquet(out/'tables/all_affected_policy_histories.parquet')
    selected=set(wide.policy_id);minimal=[]
    for line in ['motor','buildings','contents']:
        for prefix in ['policies','test']:
            name=prefix+'_'+line
            table=pq.read_table(ROOT/cat[name]['workspace_relative_path']);f=table.to_pandas()
            fields=table.column_names
            actual=f.loc[f.policy_id.isin(selected)].copy()
            for col in ['period_start','period_end']:actual[col]=pd.to_datetime(actual[col])
            recorded=wide.loc[wide.source_table.eq(name)].copy()
            check('Complete policy history IDs: '+name,set(actual.row_id)==set(recorded.row_id))
            cols=[x for x in fields if x!='row_id']
            pd.testing.assert_frame_equal(actual.set_index('row_id')[cols].sort_index(),recorded.set_index('row_id')[cols].sort_index(),check_dtype=False,check_exact=True)
            check('Every source policy value including REN00 equals recorded history: '+name,True)
            light=f[['row_id','policy_id','customer_id','period_start','period_end','new_business','renewal_count','exposure']].copy()
            light['line']=line
            for col in ['period_start','period_end']:light[col]=pd.to_datetime(light[col])
            minimal.append(light)
    periods=pd.concat(minimal,ignore_index=True).sort_values(['line','policy_id','period_start','period_end','row_id'])
    first=periods.drop_duplicates(['line','policy_id']).set_index('policy_id')
    ownfirst=first.loc[q.policy_id]
    check('First row IDs and dates independently reconstructed',ownfirst.row_id.tolist()==q.first_row_id.tolist() and ownfirst.period_start.tolist()==q.first_period_start.tolist())
    raw=pd.read_parquet(ROOT/cat['claims']['workspace_relative_path']);sourcefields=raw.columns.tolist()
    for col in ['loss_date','report_date']:raw[col]=pd.to_datetime(raw[col])
    claims=raw.merge(first[['period_start']].rename(columns={'period_start':'source_first_start'}),left_on='policy_id',right_index=True,how='left',validate='many_to_one')
    independent=set(claims.loc[claims.loss_date.lt(claims.source_first_start),'claim_id'])
    check('Fresh source criterion independently returns exactly the frozen cohort',independent==expected)
    check('All occurrences strictly before source first rows, range 4–499 days',q.loss_date.lt(q.first_period_start).all() and (q.first_period_start-q.loss_date).dt.days.min()==4 and (q.first_period_start-q.loss_date).dt.days.max()==499)
    fields=[x for x in sourcefields if x!='claim_id']
    pd.testing.assert_frame_equal(raw.loc[raw.claim_id.isin(expected)].set_index('claim_id')[fields].sort_index(),q.set_index('claim_id')[fields].sort_index(),check_dtype=False,check_exact=True)
    check('Every prehistory original claim payload remains identical',True)
    recordedclaims=pd.read_parquet(out/'tables/cohort_and_control_claim_histories.parquet')
    pd.testing.assert_frame_equal(raw.loc[raw.policy_id.isin(selected)].set_index('claim_id')[fields].sort_index(),recordedclaims.set_index('claim_id')[fields].sort_index(),check_dtype=False,check_exact=True)
    check('Complete source claims of every affected/control policy preserved',len(recordedclaims)==len(raw.loc[raw.policy_id.isin(selected)]))
    j=raw[['claim_id','policy_id','line','loss_date']].merge(periods[['row_id','policy_id','line','period_start','period_end']],on=['policy_id','line'])
    hit=j.loc[j.loss_date.between(j.period_start,j.period_end)]
    check('No prehistory occurrence has a source coverage interval',not hit.claim_id.isin(expected).any())
    check('All claim-date matches unique',hit.claim_id.is_unique)
    fresh=pd.read_parquet(out/'tables/fresh_assignment.parquet').set_index('claim_id')
    lookup=hit.set_index('claim_id').row_id
    check('Every fresh assignment matches independent source intervals',fresh.row_id.fillna('NONE').equals(lookup.reindex(fresh.index).fillna('NONE')))
    check('Current assignments equal DUP01 after REN00',fresh.row_id.fillna('NONE').equals(prior.set_index('claim_id').row_id.reindex(fresh.index).fillna('NONE')))
    legacy=q.first_period_start.eq(pd.Timestamp('2021-01-01')) & ~q.first_new_business & q.first_renewal_count.gt(0)
    newbiz=q.first_new_business & q.first_renewal_count.eq(0)
    check('244 legacy boundary and 169 new-business records',legacy.sum()==244 and newbiz.sum()==169 and (legacy|newbiz).all())
    check('Review groups use only these context conditions',q.loc[legacy,'review_class'].eq('legacy_at_dataset_boundary').all() and q.loc[newbiz,'review_class'].eq('before_recorded_new_business').all())
    master=pd.read_parquet(ROOT/cat['customers']['workspace_relative_path'],columns=['customer_id','customer_since_year','prior_claims_5y']).set_index('customer_id')
    check('Customer context equals unchanged master',master.loc[q.first_customer_id,'customer_since_year'].tolist()==q.customer_since_year.tolist() and master.loc[q.first_customer_id,'prior_claims_5y'].tolist()==q.prior_claims_5y.tolist())
    check('Legacy customer entry predates 2021; new business year equals entry year',q.loc[legacy,'customer_since_year'].lt(2021).all() and q.loc[newbiz,'customer_since_year'].eq(q.loc[newbiz,'first_year']).all())
    check('No record was reported strictly before first observed inception',not q.report_date.lt(q.first_period_start).any())
    av=pd.read_parquet(out/'tables/report_availability_diagnostic.parquet')
    check('Availability is strict report-date-before-start, never outcome-based',av.reported_before_period_start.equals(av.report_date.lt(av.period_start)) and not av.use_approved_as_predictor.any())
    reportjoin=q[['claim_id','policy_id','line','report_date']].merge(periods[['row_id','policy_id','line','period_start','period_end']],on=['policy_id','line'])
    rep=reportjoin.loc[reportjoin.report_date.between(reportjoin.period_start,reportjoin.period_end)].set_index('claim_id').row_id
    check('Tempting report-date matches documented without reassignment',q.set_index('claim_id').report_date_matching_row_id.fillna('NONE').equals(rep.reindex(q.claim_id).set_axis(q.claim_id).fillna('NONE')))
    books=json.loads((out/'financial_reconciliation.json').read_text('utf-8'))
    claims=raw.merge(prior[['claim_id','row_id']],on='claim_id',validate='one_to_one')
    for b in books:
        scope=b['scope']
        if scope=='all':z=claims
        elif scope=='assigned':z=claims.loc[claims.row_id.notna()]
        elif scope=='prehistory':z=q
        elif scope.startswith('prehistory_'):z=q.loc[q.line.eq(scope.split('_',1)[1])]
        else:z=q.loc[q.review_class.eq(scope)]
        acc=z.loc[z.status.isin(['closed','open'])]
        paid=amount(acc,'paid_to_date');inc=amount(acc,'incurred_to_date');rec=amount(acc,'recoveries')
        check('Independent Decimal financial book: '+scope,len(z)==b['records'] and len(acc)==b['accepted'] and paid==Decimal(b['paid_accepted_CU']) and inc==Decimal(b['incurred_accepted_CU']) and rec==Decimal(b['recoveries_accepted_CU']) and inc-rec==Decimal(b['net_accepted_CU']) and inc-paid==Decimal(b['case_reserve_accepted_CU']))
    book={b['scope']:b for b in books}
    for field in ['paid_accepted_CU','incurred_accepted_CU','recoveries_accepted_CU','case_reserve_accepted_CU','net_accepted_CU']:
        check('Assigned plus prehistory equals all: '+field,Decimal(book['assigned'][field])+Decimal(book['prehistory'][field])==Decimal(book['all'][field]))
    check('409 accepted, 15 open and four repudiated; exact net 1721459.84',book['prehistory']['accepted']==409 and book['prehistory']['open']==15 and book['prehistory']['repudiated']==4 and Decimal(book['prehistory']['net_accepted_CU'])==Decimal('1721459.84'))
    alias=pd.read_parquet(out/'tables/previous_duplicate_alias_context.parquet')
    check('Exactly one previous alias, excluded ID never reinstated',len(alias)==1 and set(alias.retained_claim_id)<=expected and not raw.claim_id.isin(alias.excluded_claim_id).any())
    sens=pd.read_parquet(out/'tables/forced_first_period_sensitivity_NOT_APPLIED.parquet')
    for r in sens.itertuples():
        z=q.loc[q.first_year.eq(r.first_period_year) & q.accepted]
        added=amount(z,'incurred_to_date')-amount(z,'recoveries')
        check('Forced-first scenario only, independently reconciled '+str(r.first_period_year),added==Decimal(r.net_CU_added_wrong_period) and not r.applied and Decimal(r.hypothetical_net_CU_in_first_rows)==Decimal(r.existing_net_CU_in_first_rows)+added)
    check('Twelve real cases and one assigned control',len(data['cases'])==12 and sum(not x['cohort_member'] for x in data['cases'])==1)
    check('Explorer includes exactly 413 cohort claims',set(x['claim_id'] for x in data['index'])==expected and len(data['index'])==413)
    for pid,h in data['histories'].items():
        assert set(p['row_id'] for p in h['policies'])==set(wide.loc[wide.policy_id.eq(pid),'row_id'])
        assert set(x['claim_id'] for x in h['claims'])==set(raw.loc[raw.policy_id.eq(pid),'claim_id'])
    check('Every explorer history is complete against sources',len(data['histories'])==414)
    report=(out/'informe.html').read_text('utf-8');embedded=re.search(r'<script id="reviewData" type="application/json">(.*?)</script>',report,re.S)
    check('Embedded explorer equals verified JSON',embedded is not None and json.loads(embedded.group(1))==data)
    for ref in re.findall(r'(?:href|src)="([^"]+)"',report):
        if ref.startswith(('#','http')) or ref in ['verification.json','interface_verification.json','manifest.json']:continue
        check('Local report link exists: '+ref,(out/ref).is_file())
    check('No incomplete template', '@@' not in report)
    check('No cleaned output, catalog activation, predictor or assignment changes',not (out/'data').exists() and not (out/'dataset_catalog.json').exists() and not any(s[k] for k in ['data_modified','dates_modified','claims_reassigned','active_dataset_changed','predictors_added','models_trained']))
    c.dump(out/'verification.json',{'status':'passed_own_verification','created_utc':datetime.now(timezone.utc).isoformat(),
        'passed':len(checks),'failed':0,'checks':checks,'independent_validation':False,'real_browser_rendering':False})
    print(json.dumps({'status':'passed_own_verification','passed':len(checks),'failed':0}))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
