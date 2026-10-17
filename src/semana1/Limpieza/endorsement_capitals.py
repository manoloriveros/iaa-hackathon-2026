"""CAP06R: dos excepciones manuales autorizadas; preparar, verificar y activar."""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from html.parser import HTMLParser
import argparse
import json
import re
import shutil
import subprocess
import sys
import uuid
import clean_data as c
import correct_capitals as cap
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT, BASE = c.ROOT, c.BASE
INDEX = BASE/'current_retrospective_dataset.json'
OP_INDEX = BASE/'current_endorsement_capital_correction.json'
REVIEW = ROOT/'Hackaton/Semana 1/Revision_ampliaciones_capital/runs/endorsements_20261017T005807Z_7f43caaa'
RULE = 'CAP06R'
IDS = {'C00502745': (27200000.0,27200.0), 'C00399729': (25700000.0,25700.0)}
COHORT_SHA = '950fa3bd010d477961f82e739952c1076b3c1c447330b3440f35af9863321896'
REQUEST = 'Aplica la división por mil a C00502745 y C00399729 en una nueva capa retrospectiva. Conserva originales, ampliaciones, renovaciones y los otros 419 pendientes; documenta y valida cada cambio.'
SCRIPTS = ['endorsement_capitals.py','clean_data.py','correct_capitals.py']


def readj(path):
    return json.loads(path.read_text('utf-8'))


def save(frame,path):
    frame.to_parquet(path.with_suffix('.parquet'),index=False)
    frame.to_csv(path.with_suffix('.csv'),index=False)


def protected_ok(protected,except_path=None):
    return all(c.digest(ROOT/path)==sha for path,sha in protected.items() if path!=except_path)


def prepare():
    assert cap.manifest_ok(REVIEW)
    proposal=REVIEW/'tables/proposed_manual_scale_changes_NOT_APPLIED.parquet'
    frozen=pd.read_parquet(proposal)
    assert c.digest(proposal)==COHORT_SHA and set(frozen.row_id)==set(IDS) and len(frozen)==2
    pointer=readj(INDEX);parent=ROOT/pointer['workspace_relative_run'];catpath=ROOT/pointer['catalog_workspace_relative'];cat=readj(catpath)
    assert cap.manifest_ok(parent) and all(c.digest(ROOT/e['workspace_relative_path'])==e['sha256'] for e in cat.values())
    if pointer.get('capital_rule')==RULE:
        values=pq.read_table(ROOT/cat['policies_contents']['workspace_relative_path'],columns=['row_id','sum_insured'],filters=[('row_id','in',list(IDS))]).to_pandas().set_index('row_id').sum_insured
        assert pointer['cohort_sha256']==COHORT_SHA and pointer['pending_capitals']==419 and pointer['capital_changes_this_layer']==2
        assert all(values.loc[rid]==new for rid,(old,new) in IDS.items())
        assert c.digest(BASE/'current_dataset.json')==pointer['base_catalog_index_sha256']
        assert readj(OP_INDEX)['workspace_relative_run']==pointer['workspace_relative_run']
        print(json.dumps({'status':'already_applied_verified_noop','new_changes':0,'run':str(parent)}));return
    assert pointer['capital_rule']=='CAP05R' and c.digest(INDEX)==c.digest(REVIEW/'evidence/retrospective_index.json')
    assert cat==readj(REVIEW/'evidence/dataset_catalog.json')
    pending=pd.read_parquet(parent/'tables/pending_capitals.parquet')
    assert len(pending)==421 and set(IDS).issubset(set(pending.row_id))
    out=BASE/'runs'/(datetime.now(timezone.utc).strftime('capendorse_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8])
    for name in ['data','ledger','tables','evidence','source_snapshot']:(out/name).mkdir(parents=True,exist_ok=False)
    protected={p.relative_to(ROOT).as_posix():c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']:e['sha256'] for e in cat.values()})
    for path in [*BASE.glob('current*.json'),catpath,parent/'manifest.json',parent/'tables/pending_capitals.parquet',REVIEW/'manifest.json',proposal,
        REVIEW.parent.parent/'current_run.json',ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json',
        ROOT/'Preparación/src/iaa_lab/predictor_guard.py',ROOT/'Hackaton/Semana 1/Modelado/target_scope.py',
        ROOT/'Hackaton/Semana 1/Validacion_ajustes_claude/current_run.json']:
        protected[path.relative_to(ROOT).as_posix()]=c.digest(path)
    c.dump(out/'protected_hashes_before.json',protected)
    copies={'parent_index.json':INDEX,'base_index.json':BASE/'current_dataset.json','parent_catalog.json':catpath,
        'parent_manifest.json':parent/'manifest.json','review_manifest.json':REVIEW/'manifest.json',
        'frozen_2_proposal.parquet':proposal,'frozen_421_pending.parquet':parent/'tables/pending_capitals.parquet',
        'policy_histories.parquet':REVIEW/'tables/all_policy_histories.parquet','original_histories.parquet':REVIEW/'tables/all_original_policy_histories.parquet',
        'review_proposal.json':REVIEW/'proposal.json','review_protocol.json':REVIEW/'protocol.json','review_verification.json':REVIEW/'verification.json',
        'CAP01_ledger.parquet':parent/'evidence/CAP01_ledger.parquet','prior_retrospective_ledger.parquet':parent/'ledger/cumulative_retrospective_changes.parquet',
        'protocol_before_CAP06R.json':ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json'}
    for name,path in copies.items():shutil.copy2(path,out/'evidence'/name)
    for name in SCRIPTS:shutil.copy2(BASE/name,out/'source_snapshot'/name)
    c.dump(out/'authorization.json',{'status':'explicit_participant_authorization','messages':[{'role':'user','content':REQUEST}],
        'rule':RULE,'criterion':'MANUAL_ENDORSE01-R, exact two D60 rows only','cohort_sha256':COHORT_SHA,
        'scope':'sum_insured /1000 at C00502745 and C00399729 only, new retrospective layer on CAP05R.',
        'preserve':'Originals, all other cells, six2022/2023 historical rows including endorsements and renewals, every null/date,419 pending, all prior repairs and test tables.',
        'historical_flags':'D60 false authorization/application flags remain unchanged in the frozen proposal; this later request authorizes CAP06R.',
        'not_approved':'Cohort expansion, passing DIST01-R, changing general400-day rule, smoothing, imputation, causal backtests or training.'})
    entry=cat['policies_contents'];before=pq.read_table(ROOT/entry['workspace_relative_path'])
    ledger=frozen.copy().rename(columns={'review_status':'D60_review_status','new_proposal':'D60_new_proposal'})
    positions=pd.Series(range(before.num_rows),index=before['row_id'].to_pylist())
    ledger['source_position']=positions.loc[ledger.row_id].to_numpy();ledger=ledger.sort_values('source_position').reset_index(drop=True)
    old=ledger.sum_insured.to_numpy();new=ledger.hypothetical_div1000_CU.to_numpy();pos=ledger.source_position.to_numpy(dtype=int)
    assert all((row.sum_insured,row.hypothetical_div1000_CU)==IDS[row.row_id] for row in ledger.itertuples(index=False))
    assert np.array_equal(before['sum_insured'].to_numpy()[pos],old)
    result,count=cap.apply_frozen(before['sum_insured'].to_numpy(),pos,old,new);assert count==2
    after=before.set_column(before.schema.get_field_index('sum_insured'),before.schema.field('sum_insured'),pa.array(result,type=before.schema.field('sum_insured').type))
    dest=out/'data/policies_contents.parquet';pq.write_table(after,dest,compression='zstd')
    ledger['old']=old;ledger['new']=new;ledger['divisor']=1000;ledger['rule']=RULE
    ledger['audit_ref_test2025']=False;ledger['reference_is_future_at_focus_start']=True
    ledger['evidence_available_at_period_start']=False;ledger['retrospective_only']=True
    ledger['operation_authorized']=True;ledger['correction_authorized']=True;ledger['capital_change_applied']=True
    ledger['reference_row_id']=ledger.endorsed_2022_row_id
    ledger['reference_source_table']='policies_contents'
    history=pd.read_parquet(out/'evidence/policy_histories.parquet').set_index('row_id')
    ledger['reference_period_start']=pd.to_datetime(history.loc[ledger.reference_row_id,'period_start'].to_numpy()).strftime('%Y-%m-%d')
    ledger['reference_role']='Nearest complete2022 endorsement retained explicitly; DIST01-R fails; manual decision reviews both annual baselines and endorsement.'
    ledger['source_sha256']=entry['sha256'];ledger['derived_sha256']=c.digest(dest)
    ledger['cohort_sha256']=COHORT_SHA;ledger['authorization_sha256']=c.digest(out/'authorization.json')
    save(ledger,out/'ledger/all_capital_changes')
    save(ledger,out/'ledger/policies_contents_sum_insured')
    remaining=pending.loc[~pending.row_id.isin(IDS)].copy();assert len(remaining)==419
    save(remaining,out/'tables/pending_capitals')
    canonical=['row_id','policy_id','line','source_table','old','new','rule','audit_ref_test2025','reference_row_id','reference_source_table','reference_period_start']
    cumulative=pd.concat([pd.read_parquet(out/'evidence/prior_retrospective_ledger.parquet'),ledger[canonical]],ignore_index=True)
    save(cumulative,out/'ledger/cumulative_retrospective_changes')
    save(cumulative.loc[cumulative.audit_ref_test2025],out/'ledger/cumulative_test2025_supported_changes')
    hist=after.filter(pc.is_in(after['policy_id'],value_set=pa.array(ledger.policy_id.tolist()))).to_pandas()
    for col in ['period_start','period_end']:hist[col]=pd.to_datetime(hist[col]).dt.as_unit('ns')
    hist['source_table']='policies_contents';hist=hist.sort_values(['policy_id','period_start']).reset_index(drop=True)
    save(hist,out/'tables/policy_histories_after')
    save(hist.loc[~hist.row_id.isin(IDS)].reset_index(drop=True),out/'tables/preserved_2022_2023_periods')
    newcat={k:dict(v) for k,v in cat.items()}
    newcat['policies_contents']={**entry,'workspace_relative_path':dest.relative_to(ROOT).as_posix(),'sha256':c.digest(dest),
        'endorsement_capital_parent_workspace_relative_path':entry['workspace_relative_path'],'endorsement_capital_parent_sha256':entry['sha256'],
        'endorsement_capital_rule':RULE,'endorsement_capital_changes':2,'endorsement_capital_ledger_workspace_relative_path':(out/'ledger/all_capital_changes.parquet').relative_to(ROOT).as_posix()}
    c.dump(out/'dataset_catalog.json',newcat)
    summary={'rule':RULE,'capital_changes':2,'changes_by_table':{'policies_contents':2},'pending_before':421,'pending_after':419,
        'CAP01_inherited':2073,'CAP02R_inherited':867,'CAP03R_inherited':11,'CAP04R_inherited':109,'CAP05R_inherited':46,
        'total_corrected_capitals':3108,'cumulative_retrospective_changes':1035,'new_test2025_supported_rows':0,'cumulative_test2025_supported_rows':136,
        'test_rows_changed':0,'base_pending_unchanged':1454,'preserved_history_rows':6,'originals_modified':False,'other_fields_changed':0,
        'new_columns':0,'dates_changed':False,'claims_changed':False,'models_trained':False,'approved_for_modeling':False,'retrospective_only':True,'independent_validation':False}
    c.dump(out/'summary.json',summary)
    c.dump(out/'lineage.json',{'parent_rule':'CAP05R','new_rule':RULE,'parent_run':parent.relative_to(ROOT).as_posix(),'review_run':REVIEW.relative_to(ROOT).as_posix(),'summary':summary})
    c.dump(out/'rules.json',{'rule':RULE,'version':'1.0','criterion':'MANUAL_ENDORSE01-R, exact two-row participant-authorized exception from D60.',
        'operation':'sum_insured /1000','row_ids':list(IDS),'cohort_sha256':COHORT_SHA,
        'reason':'Annual baseline comparisons distinguish a possible2021 scale error from the observed2022 endorsement and2023 renewal. Full nearest complete2022 references are retained, not skipped.',
        'DIST01_R_passed':False,'general_400day_rule_changed':False,'automatic_expansion':False,'missing_fields_imputed':False,
        'preserved_endorsements':{'C01153989':39400,'C01147928':37700},'preserved_renewals':{'C01702744':28300,'C01618408':26700},
        'retrospective_only':True,'evidence':'Future train2022/2023; no new test2025 support. D60 peer cohort exploratory, not contractual proof.',
        'reversal':'Restore old at source_position; exact parent Arrow table including schema metadata recovered.',
        'source_units_confirmed':False,'approved_for_cutoff_specific_backtesting':False,
        'IAA':['Documentation §2 and §§4–6','Governance §2.8','Professional considerations §3.2 and §§3.5–3.6']})
    assert protected_ok(protected)
    print(json.dumps({'run':str(out),'status':'prepared_not_activated','capital_changes':2,'pending':419},ensure_ascii=False))


def verify(out):
    if (out/'manifest.json').exists():
        assert cap.manifest_ok(out);print(json.dumps({'status':'closed_manifest_intact_no_rewrite'}));return
    checks=[]
    def check(name,ok):
        checks.append({'check':name,'passed':bool(ok)})
        if not ok:
            c.dump(out/'verification_failure.json',{'status':'failed_not_activated','checks':checks});raise AssertionError(name)
    read=lambda path:pd.read_parquet(out/path)
    parent,newcat=readj(out/'evidence/parent_catalog.json'),readj(out/'dataset_catalog.json')
    frozen,ledger=read('evidence/frozen_2_proposal.parquet'),read('ledger/all_capital_changes.parquet')
    before=pq.read_table(ROOT/parent['policies_contents']['workspace_relative_path']);after=pq.read_table(ROOT/newcat['policies_contents']['workspace_relative_path'])
    old,new=before['sum_insured'].to_numpy(),after['sum_insured'].to_numpy();pos=ledger.source_position.to_numpy(dtype=int)
    check('Exact two authorized row IDs, frozen hash and preserved review false flags',len(ledger)==ledger.row_id.nunique()==2 and set(ledger.row_id)==set(IDS)==set(frozen.row_id) and c.digest(out/'evidence/frozen_2_proposal.parquet')==COHORT_SHA and not frozen.correction_authorized.any() and not frozen.capital_change_applied.any())
    check('Actual source row IDs agree with positions',before.take(pa.array(pos))['row_id'].to_pylist()==ledger.row_id.tolist())
    check('Full schema, metadata, column and row order preserved',before.schema.equals(after.schema,check_metadata=True) and before.num_rows==after.num_rows and before.column_names==after.column_names)
    check('Every noncapital cell and null unchanged',before.drop(['sum_insured']).equals(after.drop(['sum_insured']),check_metadata=True))
    check('Only two authorized capital positions differ',np.array_equal(np.flatnonzero(~np.isclose(old,new,rtol=0,atol=0,equal_nan=True)),pos))
    check('Actual old and new values match ledger exactly',np.array_equal(old[pos],ledger.old.to_numpy()) and np.array_equal(new[pos],ledger.new.to_numpy()))
    check('Positive finite capitals, no changed null count or added policy column',np.isfinite(new[pos]).all() and (new[pos]>0).all() and before['sum_insured'].null_count==after['sum_insured'].null_count)
    auth=readj(out/'authorization.json')
    check('Exact participant request and per-row authorization hashes',auth['messages']==[{'role':'user','content':REQUEST}] and auth['cohort_sha256']==COHORT_SHA and ledger.authorization_sha256.eq(c.digest(out/'authorization.json')).all() and ledger.cohort_sha256.eq(COHORT_SHA).all())
    check('Authorized rule, divisor and application flags',ledger.rule.eq(RULE).all() and ledger.divisor.eq(1000).all() and ledger.operation_authorized.all() and ledger.correction_authorized.all() and ledger.capital_change_applied.all())
    check('Correct source/derived hashes and inherited catalog metadata',ledger.source_sha256.eq(parent['policies_contents']['sha256']).all() and ledger.derived_sha256.eq(c.digest(ROOT/newcat['policies_contents']['workspace_relative_path'])).all() and all(newcat['policies_contents'][k]==val for k,val in parent['policies_contents'].items() if k not in ['workspace_relative_path','sha256']))
    restored=new.copy();restored[pos]=ledger.old.to_numpy()
    reverse=after.set_column(after.schema.get_field_index('sum_insured'),after.schema.field('sum_insured'),pa.array(restored,type=after.schema.field('sum_insured').type))
    check('Reversal recovers complete CAP05R Arrow table and metadata',reverse.equals(before,check_metadata=True))
    again,count=cap.apply_frozen(new,pos,ledger.old.to_numpy(),ledger.new.to_numpy())
    check('Second transformation is a no-op',count==0 and np.array_equal(again,new,equal_nan=True))
    bad=new.copy();bad[pos[0]]+=.5
    try:cap.apply_frozen(bad,pos,ledger.old.to_numpy(),ledger.new.to_numpy())
    except ValueError:rejected=True
    else:rejected=False
    check('Unexpected capital rejected',rejected)
    for name in set(parent)-{'policies_contents'}:
        check(name+': complete catalog reference and file unchanged',newcat[name]==parent[name] and c.digest(ROOT/newcat[name]['workspace_relative_path'])==parent[name]['sha256'])
    check('Exactly one new derived data file',{p.name for p in (out/'data').iterdir()}=={'policies_contents.parquet'})
    pending,prior=read('tables/pending_capitals.parquet'),read('evidence/frozen_421_pending.parquet')
    check('Exact419 remaining pending IDs',len(pending)==pending.row_id.nunique()==419 and set(pending.row_id)==set(prior.row_id)-set(IDS))
    pd.testing.assert_frame_equal(pending,prior.loc[~prior.row_id.isin(IDS)].reset_index(drop=True),check_exact=True)
    check('All419 inventory fields, nulls and order unchanged',True)
    for name,part in pending.groupby('source_table'):
        values=pq.read_table(ROOT/newcat[name]['workspace_relative_path'],columns=['row_id','sum_insured']).to_pandas().set_index('row_id').sum_insured
        check(name+': every actual pending capital preserved',np.array_equal(values.loc[part.row_id],part.sum_insured))
    check('All108 no-original-anchor cases still pending',len(pending.loc[pending.review_group.eq('C_no_original_normal_reference')])==108)
    histories=read('evidence/policy_histories.parquet').set_index('row_id');published=read('tables/policy_histories_after.parquet').set_index('row_id')
    source=after.filter(pc.is_in(after['row_id'],value_set=pa.array(histories.index.tolist()))).to_pandas().set_index('row_id')
    for col in ['period_start','period_end']:source[col]=pd.to_datetime(source[col]).dt.as_unit('ns')
    check('All eight history IDs preserved',set(histories.index)==set(source.index)==set(published.index) and len(histories)==8)
    for rid,row in histories.iterrows():
        expected=row.copy()
        if rid in IDS:expected['sum_insured']=IDS[rid][1]
        for col in source.columns:
            x,y=source.loc[rid,col],expected[col]
            ok=(pd.isna(x) and pd.isna(y)) or (pd.notna(x) and pd.notna(y) and x==y)
            check(rid+': preserved published history field '+col,ok)
        check(rid+': saved after-history matches current source',all((pd.isna(source.loc[rid,col]) and pd.isna(published.loc[rid,col])) or (pd.notna(source.loc[rid,col]) and pd.notna(published.loc[rid,col]) and source.loc[rid,col]==published.loc[rid,col]) for col in source.columns))
    preserved=read('tables/preserved_2022_2023_periods.parquet')
    check('Six2022/2023 periods exported intact',len(preserved)==6 and set(preserved.row_id)==set(histories.index)-set(IDS))
    check('Endorsements39400/37700 and renewals28300/26700 preserved',all(source.loc[rid,'sum_insured']==amount for rid,amount in {'C01153989':39400,'C01147928':37700,'C01702744':28300,'C01618408':26700}.items()))
    check('Both intermediate unknown context values remain null',pd.isna(source.loc['C01100142','high_value_items']) and pd.isna(source.loc['C00997126','security_level']))
    for row in ledger.itertuples(index=False):
        check(row.row_id+': exact Decimal division',Decimal(str(row.old))/Decimal(1000)==Decimal(str(row.new)) and (row.old,row.new)==IDS[row.row_id])
        ref=source.loc[row.reference_row_id]
        check(row.row_id+': nearest complete endorsement retained despite DIST01-R conflict',row.reference_row_id==row.endorsed_2022_row_id and row.reference_source_table=='policies_contents' and ref.sum_insured==row.endorsed_2022_CU and not .9<=row.new/ref.sum_insured<=1.1 and (ref.period_start-source.loc[row.row_id,'period_start']).days==row.nearest_complete_reference_gap_days and row.reference_period_start==ref.period_start.strftime('%Y-%m-%d'))
        check(row.row_id+': future train evidence, no test signal or causal availability claim',row.reference_is_future_at_focus_start and row.retrospective_only and not row.audit_ref_test2025 and not row.evidence_available_at_period_start)
    cap01=read('evidence/CAP01_ledger.parquet');inherited=read('evidence/prior_retrospective_ledger.parquet')
    for name,frame,expected in [('CAP01',cap01,2073),('CAP02R_CAP03R_CAP04R_CAP05R',inherited,1033)]:
        valid=True
        for table,part in frame.groupby('source_table'):
            values=pq.read_table(ROOT/newcat[table]['workspace_relative_path'],columns=['row_id','sum_insured']).to_pandas().set_index('row_id').sum_insured
            valid &= np.array_equal(values.loc[part.row_id],part.new)
        check('Every inherited '+name+' value preserved without redivision',len(frame)==expected and not set(frame.row_id)&set(IDS) and valid)
    cumulative=read('ledger/cumulative_retrospective_changes.parquet');signal=read('ledger/cumulative_test2025_supported_changes.parquet')
    check('1035 unique retrospective corrections and3108 including CAP01',len(cumulative)==cumulative.row_id.nunique()==1035 and len(set(cumulative.row_id)|set(cap01.row_id))==3108 and cumulative.rule.value_counts().to_dict()=={'CAP02R':867,'CAP04R':109,'CAP05R':46,'CAP03R':11,'CAP06R':2})
    pd.testing.assert_frame_equal(cumulative.iloc[:1033].reset_index(drop=True),inherited,check_exact=True)
    check('All prior cumulative ledger records preserved',True)
    check('136 cumulative test2025 signals unchanged, no new test support',len(signal)==136 and set(signal.row_id)==set(inherited.loc[inherited.audit_ref_test2025,'row_id']))
    check('All protected hashes and manifests intact before activation',protected_ok(readj(out/'protected_hashes_before.json')) and cap.manifest_ok(REVIEW) and cap.manifest_ok(ROOT/readj(out/'evidence/parent_index.json')['workspace_relative_run']))
    files=[p for p in out.rglob('*') if p.is_file() and p.name not in ['verification.json','verification_failure.json']]
    result={'status':'passed_own_technical_verification','passed':len(checks),'failed':0,'checks':checks,'capital_changes':2,'pending_after':419,
        'reversal_verified':True,'idempotence_verified':True,'unexpected_value_rejected':True,'independent_validation':False,
        'verified_files':{p.relative_to(out).as_posix():c.digest(p) for p in files}}
    c.dump(out/'verification.json',result)
    print(json.dumps({k:val for k,val in result.items() if k not in ['checks','verified_files']}))


class ReportCheck(HTMLParser):
    def __init__(self):
        super().__init__();self.refs=[];self.rows=0;self.table_rows=[]
    def handle_starttag(self,tag,attrs):
        self.refs += [val for key,val in attrs if key in ['href','src']]
        if tag=='table':self.rows=0
        if tag=='tr':self.rows+=1
    def handle_endtag(self,tag):
        if tag=='table':self.table_rows.append(self.rows-1)


def finalize(out):
    assert not (out/'manifest.json').exists(),'Corrida cerrada; no sobrescribir.'
    v=readj(out/'verification.json');protected=readj(out/'protected_hashes_before.json')
    assert v['failed']==0 and v['capital_changes']==2 and v['pending_after']==419
    assert all(c.digest(out/path)==sha for path,sha in v['verified_files'].items()) and protected_ok(protected)
    assert all(c.digest(BASE/name)==c.digest(out/'source_snapshot'/name) for name in SCRIPTS)
    assert not OP_INDEX.exists()
    parent=readj(out/'evidence/parent_index.json');cat=readj(out/'dataset_catalog.json')
    assert all(c.digest(ROOT/e['workspace_relative_path'])==e['sha256'] for e in cat.values())
    paths={name:ROOT/'Preparación'/name for name in ['ESTADO_PROYECTO.json','MEMORIA_PROYECTO.md','DECISIONES.md']}
    paths.update({'RUTAS_PROYECTO.json':ROOT/'RUTAS_PROYECTO.json','protocol.json':ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json',
        'methodology.md':ROOT/'Hackaton/Semana 1/Modelado/METODOLOGIA_ACTUARIAL.md','model_README.md':ROOT/'Hackaton/Semana 1/Modelado/README.md',
        'cleaning_README.md':BASE/'README.md','capital_rules.md':BASE/'CAPITALES.md'})
    state,routes,protocol=readj(paths['ESTADO_PROYECTO.json']),readj(paths['RUTAS_PROYECTO.json']),readj(paths['protocol.json'])
    memory,decisions=paths['MEMORIA_PROYECTO.md'].read_text('utf-8'),paths['DECISIONES.md'].read_text('utf-8')
    methodology=paths['methodology.md'].read_text('utf-8')
    old_header='Versión 1.9, con capas retrospectivas CAP02R/CAP03R/CAP04R/CAP05R y PRE00/REN00 sobre la base DUP01/CAP01/CAT01/AGE01.'
    assert protocol['version']=='1.9' and methodology.count(old_header)==1
    now=datetime.now(timezone.utc);rel=out.relative_to(ROOT).as_posix();short=out.relative_to(BASE).as_posix()
    decision='D'+str(max(map(int,re.findall(r'\bD(\d+)\b',decisions)))+1)
    close=BASE/'closures'/now.strftime('CAP06R_closure_%Y%m%dT%H%M%SZ');close.mkdir(parents=True,exist_ok=False)
    for name,path in paths.items():shutil.copy2(path,close/('before_'+name))
    record={'decision_id':decision,'rule':RULE,'criterion':'MANUAL_ENDORSE01-R, exact two D60 rows only',
        'status':'applied_verified_retrospective_only','run':'../'+rel,'report':'../'+rel+'/informe.html','catalog':'../'+rel+'/dataset_catalog.json',
        'index':'../Hackaton/Semana 1/Limpieza/current_endorsement_capital_correction.json',
        'ledger':'../'+rel+'/ledger/all_capital_changes.parquet','ledger_csv':'../'+rel+'/ledger/all_capital_changes.csv',
        'preserved_history':'../'+rel+'/tables/preserved_2022_2023_periods.csv','pending':'../'+rel+'/tables/pending_capitals.parquet',
        'verification':'../'+rel+'/verification.json','capital_changes':2,'row_ids':list(IDS),'changes_by_table':{'policies_contents':2},
        'new_capitals_CU':{rid:new for rid,(old,new) in IDS.items()},'pending_in_retrospective_layer':419,'baseline_pending_unchanged':1454,
        'total_corrected_capitals':3108,'retrospective_changes_total':1035,'new_test2025_supported_rows':0,'test2025_supported_cumulative_rows':136,
        'CAP01_inherited_changes':2073,'CAP02R_inherited_changes':867,'CAP03R_inherited_changes':11,'CAP04R_inherited_changes':109,'CAP05R_inherited_changes':46,
        'preserved_endorsements_CU':{'C01153989':39400,'C01147928':37700},'preserved_renewals_CU':{'C01702744':28300,'C01618408':26700},
        'missing_context_preserved':True,'preserved_history_rows':6,'originals_modified':False,'other_fields_changed':0,'test_tables_modified':False,
        'claims_modified':False,'dates_modified':False,'new_columns':0,'retrospective_only':True,'source_units_confirmed':False,
        'automatic_expansion':False,'general_400day_rule_changed':False,'DIST01_R_passed':False,'technical_checks':v['passed'],
        'independent_validation':False,'models_trained':False,'approved_for_modeling':False,'operational_T0_materialized':False,'CON01_activated':False,
        'D59_revalidation_of_this_layer':'Not performed; D59 remains historical evidence, no new third-party validation claimed.',
        'closure':'../'+close.relative_to(ROOT).as_posix()}
    ledger=pd.read_parquet(out/'ledger/all_capital_changes.parquet');preserved=pd.read_parquet(out/'tables/preserved_2022_2023_periods.parquet')
    money=lambda x:f'{float(x):,.2f}'.replace(',','_').replace('.',',').replace('_','.')
    changes=ledger[['row_id','policy_id','old','new','endorsed_2022_row_id','endorsed_2022_CU','renewal_2023_row_id','renewal_2023_CU']].to_html(index=False,border=0,float_format=money)
    view=preserved[['row_id','policy_id','period_start','period_end','sum_insured','exposure','renewal_count','renewal_decision','security_level','high_value_items']].copy()
    for col in ['period_start','period_end']:view[col]=pd.to_datetime(view[col]).dt.strftime('%Y-%m-%d')
    history=view.to_html(index=False,border=0,na_rep='Sin dato',float_format=money)
    report=f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CAP06R: dos capitales corregidos</title><style>body{{font:16px/1.65 system-ui,sans-serif;background:#eef3f6;color:#193245;margin:0}}main{{max-width:1350px;margin:auto;padding:24px}}header,section{{background:white;border-radius:12px;padding:24px;margin-bottom:18px}}header{{background:#17394d;color:white}}h1{{font-size:30px;line-height:1.3}}h2{{font-size:23px}}table{{border-collapse:collapse;font-size:13px;width:100%}}th,td{{padding:9px;border-bottom:1px solid #dce5ea;white-space:nowrap;text-align:left}}th{{background:#edf3f6}}.scroll{{overflow:auto}}.note{{border-left:4px solid #b47725;background:#fff5e2;padding:12px 18px}}a{{color:#007d72}}</style></head><body><main>
<header><h1>CAP06R: dos capitales de 2021 divididos por mil</h1><p>{decision} · Capa retrospectiva sobre CAP05R · Autorización explícita para C00502745 y C00399729</p><p>Dos cambios en contenidos · 419 pendientes preservados · Originales intactos</p></header>
<section><h2>Los dos cambios autorizados</h2><p>Solo cambia sum_insured en C00502745 (27.200.000→27.200 CU) y C00399729 (25.700.000→25.700 CU). Se crea una nueva tabla derivada de policies_contents, conservando todos los demás valores, orden, nulos, tipos y metadatos. Las otras diez referencias completas del catálogo permanecen iguales.</p><div class="scroll">{changes}</div><p><a href="ledger/all_capital_changes.csv">Bitácora de los dos cambios, CSV</a> · <a href="ledger/all_capital_changes.parquet">Bitácora tipada</a> · <a href="authorization.json">Solicitud íntegra</a> · <a href="dataset_catalog.json">Nuevo catálogo</a></p></section>
<section><h2>Ampliaciones, renovaciones y nulos conservados</h2><p>Los seis periodos de 2022/2023 se conservan íntegros. C01153989/C01147928 mantienen 39.400/37.700 CU; C01702744/C01618408 mantienen 28.300/26.700. C01100142 conserva high_value_items desconocido y C00997126 conserva security_level desconocido. Se preservan fechas, exposición, primas, contadores y decisiones de renovación.</p><div class="scroll">{history}</div><p><a href="tables/preserved_2022_2023_periods.csv">Los seis periodos preservados</a> · <a href="tables/policy_histories_after.csv">Las ocho filas después de CAP06R</a> · <a href="evidence/policy_histories.parquet">Las ocho filas anteriores</a></p></section>
<section><h2>Alcance de la excepción manual</h2><p>CAP06R aplica MANUAL_ENDORSE01-R únicamente a los dos IDs autorizados. La revisión D60 separó la hipótesis de unidad de 2021 de los cambios de nivel de 2022/2023. Dividir solo 2021 da un aumento al inicio de 2022 de 1,84%/1,95%, conservando las ampliaciones de 42,24%/43,89% y los descensos al renovar de 28,17%/29,18%.</p><p>Las primeras referencias completas de 2022 permanecen explícitas en bitácora y en el registro acumulado: son las ampliaciones, con sus fechas y capitales. Las razones 27.200/39.400 y 25.700/37.700 siguen fuera de 0,90–1,10. No se declara superada DIST01-R ni se amplía la regla general de 400 días; no se copia, interpola o suaviza el capital. El grupo comparativo de D60 era exploratorio, no prueba contractual.</p><div class="note">El respaldo es posterior de train 2022/2023. No hay nuevo respaldo de test 2025 ni cambios en tablas test. La capa es retrospectiva y no aprueba backtests causales, entrenamiento o confirmación de unidad por la fuente.</div><p><a href="rules.json">Regla aplicada y límites</a> · <a href="evidence/review_proposal.json">Propuesta histórica D60</a></p></section>
<section><h2>419 pendientes y correcciones anteriores</h2><p>El inventario conserva exactamente el complemento de los 421 anteriores, con todos sus campos, nulos y orden. Los 108 sin ancla original, C48613718 y B19256617/B00962235 siguen pendientes; no hay cascadas. La base current_dataset.json mantiene su hash y 1.454 pendientes.</p><p>Se conservan 2.073 CAP01, 867 CAP02R, once CAP03R, 109 CAP04R y 46 CAP05R. Con los dos CAP06R son 3.108 capitales corregidos, de los cuales 1.035 retrospectivos. Los 136 respaldos test 2025 acumulados permanecen iguales, sin nuevos casos. Siniestros, componentes del objetivo y marcas REN00/PRE00 se conservan.</p><p><a href="tables/pending_capitals.csv">Los 419 pendientes</a> · <a href="ledger/cumulative_retrospective_changes.csv">Las 1.035 correcciones retrospectivas</a> · <a href="ledger/cumulative_test2025_supported_changes.csv">Los 136 respaldos test heredados</a></p></section>
<section><h2>Validación y reproducción</h2><p>Pasaron {v['passed']} controles propios. La comparación completa de policies_contents contra CAP05R solo detecta las dos celdas autorizadas. Se comprobaron divisiones con Decimal, posiciones, todo campo de las ocho filas históricas, seis periodos preservados, todos los pendientes y reparaciones heredadas. Restaurar old recupera exactamente la tabla padre Arrow y sus metadatos. Una segunda transformación no cambia valores y un importe inesperado se rechaza.</p><p>La bitácora guarda old/new, posición, identidad, las tres referencias históricas de cada póliza, contexto ausente, primera referencia completa, regla/divisor y hashes de fuente, derivado, cohorte y autorización. Los falsos de la propuesta congelada D60 permanecen como evidencia histórica; la solicitud posterior autoriza esta operación.</p><p>Desde C:/dev/Hakaton, usar Preparación/.venv/Scripts/python.exe con Hackaton/Semana 1/Limpieza/endorsement_capitals.py prepare. Pasar verify y finalize con la carpeta generada. Repetir prepare sobre la capa activa verifica que ya esté aplicada y termina sin cambios. El cierre comprueba esa segunda invocación real del CLI. Se archivan los tres scripts.</p><p><a href="verification.json">Controles completos</a> · <a href="lineage.json">Linaje</a> · <a href="manifest.json">Manifiesto SHA256</a></p><p>current_retrospective_dataset.json avanza a CAP06R y current_endorsement_capital_correction.json identifica esta operación. Los índices de operación anteriores permanecen intactos. Protocolo y metodología 1.10, documentos antes/después archivados. La validación D59 de Claude permanece histórica y no acredita esta nueva capa; no se atribuye una reproducción nueva.</p><p>La IA preparó código y verificaciones propias; el participante autorizó las dos filas. Sin validación independiente ni renderizado de navegador acreditados. No se materializa T0/F0, entrena, publica, contacta a terceros o llama a un proveedor externo. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad y responsabilidad, sin constituir certificación.</p></section></main></body></html>'''
    (out/'informe.html').write_text(report,encoding='utf-8');parser=ReportCheck();parser.feed(report)
    assert parser.table_rows==[2,6] and all(ref=='manifest.json' or (out/ref).is_file() for ref in parser.refs)
    c.dump(out/'report_verification.json',{'passed':3,'failed':0,'tables_actual_rows':parser.table_rows,'all_links_present_except_manifest_at_closure':True,'real_browser_rendering_verified':False})
    for name in ['README.md','PRACTICAS_PRIORITARIAS.md']:shutil.copy2(ROOT/'Preparación/Antecedentes/IAA_IA'/name,out/'evidence'/('IAA_'+name))
    c.dump(out/'manifest.json',{'created_utc':now.isoformat(),'type':'immutable_CAP06R_manual_endorsement_capital_correction','files':[
        {'path':p.relative_to(out).as_posix(),'sha256':c.digest(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()]})
    pointer={**parent,'workspace_relative_run':rel,'catalog_workspace_relative':rel+'/dataset_catalog.json','status':'verified_retrospective_CAP06R',
        'capital_rule':RULE,'capital_changes_this_layer':2,'capital_changes_inherited':3106,'CAP05R_inherited_changes':46,
        'total_capital_changes':3108,'retrospective_capital_changes_total':1035,'pending_capitals':419,
        'later_test2025_supported_rows':136,'this_layer_test2025_supported_rows':0,'corrected_test2025_rows_this_layer':0,
        'cohort_sha256':COHORT_SHA,'parent_catalog_index_sha256':c.digest(out/'evidence/parent_index.json'),
        'application_index_workspace_relative':OP_INDEX.relative_to(ROOT).as_posix(),'retrospective_only':True,
        'not_approved_for_cutoff_specific_backtesting':True,'approved_for_modeling':False}
    assert protected_ok(protected)
    temp=BASE/('endorsement_index_'+uuid.uuid4().hex+'.json');c.dump(temp,pointer);temp.replace(INDEX)
    c.dump(OP_INDEX,{'workspace_relative_run':rel,'report_workspace_relative':rel+'/informe.html','decision_id':decision,
        'status':'applied_verified_retrospective_only','capital_changes':2,'new_test2025_supported_rows':0,'pending':419})
    protocol['version']='1.10';protocol['inputs'].setdefault('retrospective_capital_history',[]).append(protocol['inputs']['retrospective_capital_layer'])
    protocol['inputs']['retrospective_capital_layer']={'latest_rule':RULE,'criterion':'MANUAL_ENDORSE01-R, exact two D60 rows only',
        'rows_this_layer':2,'operation':'sum_insured /1000','row_ids':list(IDS),'catalog_index':'../Limpieza/current_retrospective_dataset.json',
        'default_catalog_index_unchanged':'../Limpieza/current_dataset.json','retrospective_only':True,
        'CAP01_inherited':2073,'CAP02R_inherited':867,'CAP03R_inherited':11,'CAP04R_inherited':109,'CAP05R_inherited':46,
        'total_corrected_capitals':3108,'retrospective_corrections_total':1035,'test2025_supported_new':0,'test2025_supported_cumulative':136,
        'pending_in_this_layer':419,'pending_in_default_layer':1454,'test_rows_changed':0,'all_other_fields_preserved':True,
        'general_400day_rule_changed':False,'DIST01_R_passed':False,'automatic_expansion':False,'source_unit_confirmation':False,'T_W_semantic_merge':False,
        'use_in_cutoff_specific_backtests':'Not approved; future train2022/2023 evidence and retrospective manual decision.',
        'reference_role':'Nearest complete2022 endorsement retained in ledger; annual baselines reviewed separately, without smoothing.',
        'report':'../Limpieza/'+short+'/informe.html'}
    c.dump(paths['protocol.json'],protocol)
    note=f'''\n\n{decision}, CAP06R autorizado: C00502745 pasa de 27.200.000 a 27.200 CU y C00399729 de 25.700.000 a 25.700 en una nueva capa retrospectiva sobre CAP05R. Se conservan las ampliaciones de 39.400/37.700, renovaciones de 28.300/26.700, ambos nulos y todos los demás campos. Los otros 419 pendientes permanecen íntegros, incluidos 108 sin ancla; la base sigue con 1.454. Total 3.108 correcciones, de las cuales 1.035 retrospectivas; 136 respaldos test acumulados sin nuevos casos o cambios de test. Excepción manual limitada a los dos IDs, sin ampliar 400 días ni declarar superada DIST01-R. Protocolo 1.10; sin aprobación causal por corte. '''
    new_header='Versión 1.10, con capas retrospectivas CAP02R/CAP03R/CAP04R/CAP05R/CAP06R y PRE00/REN00 sobre la base DUP01/CAP01/CAT01/AGE01.'
    paths['methodology.md'].write_text(methodology.replace(old_header,new_header).rstrip()+note+f'[Informe y bitácora](../Limpieza/{short}/informe.html).\n',encoding='utf-8')
    for key,prefix in [('model_README.md','../Limpieza/'),('cleaning_README.md',''),('capital_rules.md','')]:
        paths[key].write_text(paths[key].read_text('utf-8').rstrip()+note+f'[Informe y bitácora]({prefix}{short}/informe.html). CLI endorsement_capitals.py con prepare, verify y finalize; índice current_endorsement_capital_correction.json. D59 conserva alcance histórico y no acredita la nueva capa.\n',encoding='utf-8')
    state['endorsement_capital_application']=record
    state['endorsement_capital_review']['followup_application_decision']=decision;state['endorsement_capital_review']['two_row_operation_authorized_later']=True
    state['methodological_plan']['version']='1.10';state['memory_as_of']=now.isoformat()
    routes['week_1_endorsement_capital_application_index']='Hackaton/Semana 1/Limpieza/current_endorsement_capital_correction.json'
    c.dump(paths['ESTADO_PROYECTO.json'],state);c.dump(paths['RUTAS_PROYECTO.json'],routes)
    localdate=now.astimezone(timezone(timedelta(hours=-5))).strftime('%Y-%m-%d')
    text=f'''\n\n### {decision}, CAP06R autorizado: dos capitales de 2021 /1000 y 419 pendientes conservados, {localdate}, America/Bogota

El participante autorizó dividir por mil C00502745 y C00399729 en una nueva capa retrospectiva, conservar originales, ampliaciones, renovaciones y otros 419 pendientes, y documentar/validar cada cambio. La solicitud íntegra está en ../{rel}/authorization.json. CAP06R aplica MANUAL_ENDORSE01-R sobre CAP05R exclusivamente a esas dos filas de policies_contents: 27.200.000→27.200 y 25.700.000→25.700 CU. Propuesta D60 congelada por SHA256 {COHORT_SHA}; sin selección nueva o cascada. Los falsos históricos de autorización/aplicación se conservan en la evidencia; la bitácora registra la autorización posterior.

Se conserva exactamente toda celda ajena a esos dos capitales, filas, orden, nulos, tipos y metadatos. Las otras diez referencias completas del catálogo permanecen iguales, incluidas todas las tablas test y siniestros. C01153989/C01147928 mantienen las ampliaciones de 39.400/37.700; C01702744/C01618408 mantienen renovaciones de 28.300/26.700. C01100142 conserva high_value_items nulo y C00997126, security_level nulo. Se archivan las ocho historias posteriores y los seis periodos intactos de 2022/2023. No se modifican fechas, exposición, primas, decisiones de renovación, REN00/PRE00 u objetivo.

La excepción manual reconoce la variación observada de capital durante 2022 y al renovar; no declara superada DIST01-R ni amplía el límite general de 400 días. Las primeras referencias completas de 2022 se retienen como referencias principales en la bitácora y registro acumulado, con sus fechas y capitales, aunque no pasan la banda monetaria 0,90–1,10. No se ocultan para elegir solo 2023. Se usa la revisión conjunta de bases anuales y ampliación, sin copiar o suavizar valores. El respaldo es futuro de train 2022/2023, sin nuevos respaldos de test 2025; no confirma unidades por la fuente ni aprueba backtest causal o entrenamiento.

Los 419 pendientes son el complemento exacto de los 421 anteriores, preservando todos sus campos y orden. Se mantienen los 108 sin referencia original habitual, C48613718 y B19256617/B00962235. Se conservan las 3.106 correcciones heredadas sin redivisión. El total es 3.108 (2.073 CAP01 + 867 CAP02R + 11 CAP03R + 109 CAP04R + 46 CAP05R + 2 CAP06R); las retrospectivas suman 1.035. Los 136 respaldos test acumulados se conservan íntegros; ningún cambio nuevo es de test. La base conserva su hash y 1.454 pendientes.

Pasaron {v['passed']} controles propios: comparación completa de la tabla contra CAP05R con solo dos diferencias autorizadas, Decimal por fila, todas las celdas de las ocho historias, ampliaciones/renovaciones/nulos, pendientes y reparaciones heredadas; reversión exacta Arrow con metadatos, segunda transformación sin cambios y rechazo de importe inesperado. El cierre comprueba además una segunda invocación real del CLI sin cambios. La bitácora incluye posiciones, valores, referencias, regla/divisor y hashes de fuente, derivado, cohorte y autorización. El informe estático muestra dos cambios y seis periodos preservados, con enlaces comprobados; sin renderizado de navegador o validación independiente acreditados.

current_retrospective_dataset.json avanza atómicamente a CAP06R tras verificar capa y padre; current_endorsement_capital_correction.json identifica la operación. Los anteriores índices de operación y la corrida D60 permanecen intactos. Protocolo y metodología 1.10, documentos antes/después archivados. La revisión D59 de Claude se conserva como evidencia histórica, sin atribuirle verificación de CAP06R. La IA preparó código y controles propios; el participante autorizó los dos IDs. Sin proveedor externo, entrenamiento, publicación, contacto a terceros o delegación. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad y responsabilidad. Ver endorsement_capital_application.
'''
    paths['DECISIONES.md'].write_text(decisions.rstrip()+text,encoding='utf-8')
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip()+note+f'[Informe](../{rel}/informe.html), [dos cambios](../{rel}/ledger/all_capital_changes.csv), [seis periodos preservados](../{rel}/tables/preserved_2022_2023_periods.csv). {v["passed"]} controles propios, reversión e idempotencia verificadas. current_retrospective_dataset.json avanza a CAP06R. D59 mantiene alcance histórico; sin entrenamiento o validación independiente de esta capa. Ver endorsement_capital_application y {decision}.\n',encoding='utf-8')
    afterdocs=close/'after';afterdocs.mkdir()
    for name,path in paths.items():shutil.copy2(path,afterdocs/name)
    pointersha,opsha=c.digest(INDEX),c.digest(OP_INDEX)
    replay=subprocess.run([sys.executable,str(BASE/'endorsement_capitals.py'),'prepare'],cwd=ROOT,capture_output=True,text=True,check=True);replayresult=json.loads(replay.stdout)
    allowed={INDEX.relative_to(ROOT).as_posix(),paths['protocol.json'].relative_to(ROOT).as_posix()}
    post=[{'check':'Actual second CLI prepare is a verified no-op','passed':replayresult['status']=='already_applied_verified_noop' and replayresult['new_changes']==0},
        {'check':'No-op preserves both active indexes','passed':c.digest(INDEX)==pointersha and c.digest(OP_INDEX)==opsha},
        {'check':'All protected originals, parent files and prior indexes unchanged','passed':all(c.digest(ROOT/path)==sha for path,sha in protected.items() if path not in allowed)},
        {'check':'New, CAP05R and D60 manifests intact','passed':cap.manifest_ok(out) and cap.manifest_ok(ROOT/parent['workspace_relative_run']) and cap.manifest_ok(REVIEW)},
        {'check':'Correct419/3108/1035/136 counters and zero new test support','passed':pointer['pending_capitals']==419 and pointer['total_capital_changes']==3108 and pointer['retrospective_capital_changes_total']==1035 and pointer['later_test2025_supported_rows']==136 and pointer['this_layer_test2025_supported_rows']==pointer['corrected_test2025_rows_this_layer']==0},
        {'check':'Default catalog unchanged and no modeling approval','passed':protocol['inputs']['catalog_index']=='../Limpieza/current_dataset.json' and not pointer['approved_for_modeling'] and pointer['not_approved_for_cutoff_specific_backtesting']},
        {'check':'Every report link present after sealing','passed':all((out/ref).is_file() for ref in parser.refs)}]
    assert all(row['passed'] for row in post)
    c.dump(close/'post_activation_verification.json',{'passed':len(post),'failed':0,'checks':post,'actual_second_cli':replayresult,'stderr':replay.stderr,'independent_validation':False})
    c.dump(close/'closure.json',{'created_utc':now.isoformat(),'decision_id':decision,'application':record,'manifest_sha256':c.digest(out/'manifest.json'),
        'documents':{path.relative_to(ROOT).as_posix():c.digest(path) for path in [*paths.values(),INDEX,OP_INDEX]}})
    print(json.dumps({'status':'applied_verified_retrospective_only','decision':decision,'run':str(out),'report':str(out/'informe.html'),'closure':str(close),'post_activation_checks':len(post)},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','verify','finalize']);parser.add_argument('run',nargs='?');args=parser.parse_args()
    if args.command=='prepare':prepare()
    else:
        if args.run is None:parser.error('verify y finalize requieren la carpeta de corrida')
        {'verify':verify,'finalize':finalize}[args.command](Path(args.run).resolve())
