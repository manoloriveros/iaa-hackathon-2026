"""Revisión de los 1454 capitales congelados pendientes; no escribe datos preparados."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import sys
import uuid

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'Hackaton/Semana 1/Limpieza'))
import clean_data as c
import correct_capitals as cap
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

BASE=Path(__file__).parent
CAP=ROOT/'Hackaton/Semana 1/Limpieza/runs/capfix_20261016T184904Z_099a22b1'
ORIGINAL_REVIEW=cap.REVIEW
THRESHOLDS={'buildings':10_000_000,'contents':1_000_000}
REQUEST='Ahora revisemos los 1.454 capitales que siguen pendientes. Compara los historiales de las pólizas, muestra casos concretos y propón cómo tratarlos sin modificar los datos todavía.'


def save_frame(frame,out,name):
    frame.to_parquet(out/'tables'/(name+'.parquet'),index=False)
    frame.to_csv(out/'tables'/(name+'.csv'),index=False)


def comparison(row,anchor,line,direction):
    if anchor is None:return {'exists':False}
    missing=[];changed=[];differences={}
    for col in cap.FIELDS[line]:
        x,y=row[col],anchor[col]
        if pd.isna(x) or pd.isna(y):missing.append(col);continue
        if col=='construction_type':x,y=str(x).strip().casefold(),str(y).strip().casefold()
        if x!=y:
            changed.append(col);differences[col]={'pending':x,'reference':y}
    delta=(row.period_start-anchor.period_start).days if direction=='prior' else (anchor.period_start-row.period_start).days
    temporal=anchor.period_end<row.period_start if direction=='prior' else row.period_end<anchor.period_start
    ratio=(row.sum_insured/1000)/anchor.sum_insured
    base={'exists':True,'row_id':anchor.row_id,'source_table':anchor.source_table,'sum_insured_CU':float(anchor.sum_insured),
          'period_start':str(anchor.period_start.date()),'period_end':str(anchor.period_end.date()),
          'CAP01_reference':bool(anchor.cap01_applied),'start_gap_days':int(delta),'nonoverlap':bool(temporal),
          'context_complete':not missing,'context_same':not changed and not missing,
          'missing_fields':'|'.join(missing),'changed_fields':'|'.join(changed),
          'field_differences_json':json.dumps(differences,ensure_ascii=False,default=lambda x:x.item()),
          'what_if_div1000_over_reference':float(ratio),
          'strict_support_10pct':not changed and not missing and temporal and 1<=delta<=400 and .9<=ratio<=1.1,
          't_w_only_change':line=='buildings' and changed==['construction_type'] and not missing and
                            {str(row.construction_type).casefold(),str(anchor.construction_type).casefold()}=={'t','w'},
          'premium_ratio_pending_over_reference':float(row.written_premium/anchor.written_premium) if anchor.written_premium>0 else None,
          'premium_periods_comparable':row.covered_days>=300 and anchor.covered_days>=300 and .95<=row.covered_days/anchor.covered_days<=1.05,
          'reference_is_future_at_pending_start':direction=='later',
          'reference_is_test_2025':anchor.source_table.startswith('test_')}
    return base


def main():
    active=ROOT/'Hackaton/Semana 1/Limpieza/current_dataset.json'
    pointer=json.loads(active.read_text('utf-8'));catalog_path=ROOT/pointer['catalog_workspace_relative']
    catalog=json.loads(catalog_path.read_text('utf-8'));active_run=ROOT/pointer['workspace_relative_run']
    assert cap.manifest_ok(active_run) and cap.manifest_ok(CAP) and cap.manifest_ok(ORIGINAL_REVIEW)
    pending_path=CAP/'tables/pending_capitals.parquet'
    frozen=pd.read_parquet(pending_path);assert len(frozen)==frozen.row_id.nunique()==1454
    fixed=pd.read_parquet(CAP/'ledger/all_capital_changes.parquet').set_index('row_id')
    out=BASE/'runs'/(datetime.now(timezone.utc).strftime('pending_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8])
    for name in ['tables','evidence','source_snapshot','figures']:(out/name).mkdir(parents=True,exist_ok=False)
    protected={p.relative_to(ROOT).as_posix():c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({v['workspace_relative_path']:v['sha256'] for v in catalog.values()})
    for p in [active,catalog_path,active_run/'manifest.json',CAP/'manifest.json',ORIGINAL_REVIEW/'manifest.json',pending_path]:
        protected[p.relative_to(ROOT).as_posix()]=c.digest(p)
    assert all(c.digest(ROOT/p)==sha for p,sha in protected.items())
    c.dump(out/'protected_hashes_before.json',protected)
    for name,p in {'active_index.json':active,'dataset_catalog.json':catalog_path,'active_manifest.json':active_run/'manifest.json',
        'frozen_pending_capitals.parquet':pending_path,'CAP01_manifest.json':CAP/'manifest.json',
        'CAP01_ledger.parquet':CAP/'ledger/all_capital_changes.parquet','D34_manifest.json':ORIGINAL_REVIEW/'manifest.json',
        'D34_protocol.json':ORIGINAL_REVIEW/'protocol.json',
        'data-description.md':ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md'}.items():
        shutil.copy2(p,out/'evidence'/name)
    shutil.copy2(__file__,out/'source_snapshot'/Path(__file__).name)
    shutil.copy2(ROOT/'Hackaton/Semana 1/Limpieza/correct_capitals.py',out/'source_snapshot/correct_capitals.py')
    c.dump(out/'request.json',{'messages':[{'role':'user','content':REQUEST}],'scope':'Review only; all proposed values are arithmetic diagnostics. No active dataset/index, claim amount or capital changes.'})
    histories=[];all_reviews=[];all_refs=[];peers=[]
    for line,threshold in THRESHOLDS.items():
        selected=frozen.loc[frozen.line.eq(line)];wanted=set(selected.policy_id);pending_ids=set(selected.row_id)
        parts=[]
        for prefix in ['policies','test']:
            name=prefix+'_'+line;path=ROOT/catalog[name]['workspace_relative_path']
            frame=pq.read_table(path).to_pandas();frame['source_table']=name;frame['line']=line
            for col in ['period_start','period_end']:frame[col]=pd.to_datetime(frame[col])
            frame['year']=frame.period_start.dt.year
            for year,g in frame.groupby('year'):
                normal=g.loc[g.sum_insured.le(threshold),'sum_insured']
                peers.append({'line':line,'table':name,'year':int(year),'rows':len(g),'screened_high':int(g.sum_insured.gt(threshold).sum()),
                              'normal_p01_CU':float(normal.quantile(.01)),'normal_p50_CU':float(normal.median()),
                              'normal_p99_CU':float(normal.quantile(.99)),'normal_max_CU':float(normal.max())})
            small=frame.loc[frame.policy_id.isin(wanted)].copy()
            raw=pq.read_table(c.RAW/(name+'.parquet'),columns=['row_id','sum_insured']).to_pandas().set_index('row_id')
            small['original_sum_insured_CU']=small.row_id.map(raw.sum_insured)
            parts.append(small)
            del frame,raw
        hist=pd.concat(parts,ignore_index=True).sort_values(['policy_id','period_start','row_id']).reset_index(drop=True)
        hist['pending_frozen']=hist.row_id.isin(pending_ids)
        hist['cap01_applied']=hist.row_id.isin(fixed.index)
        hist['covered_days']=(hist.period_end-hist.period_start).dt.days+1
        hist['extreme_screen']=hist.sum_insured.gt(threshold)
        hist['what_if_div1000_CU']=np.where(hist.pending_frozen,hist.sum_insured/1000,np.nan)
        assert hist.loc[hist.pending_frozen].set_index('row_id').sum_insured.sort_index().equals(selected.set_index('row_id').sum_insured.sort_index())
        grouped={pid:g for pid,g in hist.groupby('policy_id',sort=False)}
        rows=[];refs=[]
        for _,row in hist.loc[hist.pending_frozen].iterrows():
            g=grouped[row.policy_id]
            rec=row.to_dict()
            rec['original_review_route']=selected.set_index('row_id').loc[row.row_id,'review_route']
            for origin,normal in [('original',g.loc[~g.extreme_screen&~g.cap01_applied]),('prepared',g.loc[~g.extreme_screen])]:
                for direction in ['prior','later']:
                    options=normal.loc[normal.period_start.lt(row.period_start)] if direction=='prior' else normal.loc[normal.period_start.gt(row.period_start)]
                    anchor=None if options.empty else options.iloc[-1 if direction=='prior' else 0]
                    info=comparison(row,anchor,line,direction)
                    for key,value in info.items():rec[f'{origin}_{direction}_{key}']=value
                    if origin=='original' and anchor is not None:
                        # Keep every normal reference, not just the nearest, for exhaustive inspection.
                        for _,reference in options.iterrows():
                            refs.append({'pending_row_id':row.row_id,'policy_id':row.policy_id,'line':line,'direction':direction,
                                         **comparison(row,reference,line,direction)})
            rec['prior_extreme_rows']=int((g.period_start.lt(row.period_start)&g.extreme_screen).sum())
            rec['later_extreme_rows']=int((g.period_start.gt(row.period_start)&g.extreme_screen).sum())
            rec['policy_history_rows']=len(g)
            rec['first_observed_row']=row.row_id==g.iloc[0].row_id
            rec['strict_prior_support']=bool(rec.get('original_prior_strict_support_10pct',False))
            rec['strict_later_support']=bool(rec.get('original_later_strict_support_10pct',False))
            rec['prepared_prior_support']=bool(rec.get('prepared_prior_strict_support_10pct',False))
            rec['prepared_later_support']=bool(rec.get('prepared_later_strict_support_10pct',False))
            rows.append(rec)
        review=pd.DataFrame(rows)
        print(json.dumps({'line':line,'pending':len(review),'policies':len(grouped),'history_rows':len(hist),
                          'strict_prior':int(review.strict_prior_support.sum()),'strict_later':int(review.strict_later_support.sum()),
                          'prepared_prior':int(review.prepared_prior_support.sum()),'prepared_later':int(review.prepared_later_support.sum())}),flush=True)
        histories.append(hist);all_reviews.append(review);all_refs.extend(refs)
    review=pd.concat(all_reviews,ignore_index=True);history=pd.concat(histories,ignore_index=True)
    references=pd.DataFrame(all_refs)
    save_frame(review,out,'pending_review');save_frame(history,out,'all_affected_policy_histories')
    save_frame(references,out,'all_original_normal_references');save_frame(pd.DataFrame(peers),out,'peer_capital_bands')
    addresses=pq.read_table(ROOT/catalog['addresses']['workspace_relative_path']).to_pandas()
    save_frame(addresses.loc[addresses.address_id.isin(history.address_id)],out,'affected_address_context')
    claims=pq.read_table(ROOT/catalog['claims']['workspace_relative_path']).to_pandas()
    claims=claims.loc[claims.policy_id.isin(set(history.policy_id))&claims.line.isin(THRESHOLDS)].copy()
    for col in ['loss_date','report_date']:claims[col]=pd.to_datetime(claims[col])
    save_frame(claims,out,'all_affected_claim_histories')
    c.dump(out/'initial_profile.json',{'pending_rows':len(review),'policies':review.policy_id.nunique(),
        'history_rows':len(history),'claims':len(claims),'by_original_route':review.original_review_route.value_counts().to_dict(),
        'by_line':review.line.value_counts().to_dict(),'pending_values_changed':0,'active_dataset_changed':False,
        'models_trained':False,'independent_validation':False})
    assert all(c.digest(ROOT/p)==sha for p,sha in protected.items())
    print('RUN='+str(out),flush=True)


if __name__=='__main__':main()
