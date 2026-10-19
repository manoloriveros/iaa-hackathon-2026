"""Build the frozen eight-rule preaudit base using only eleven raw Parquet inputs.

No legacy run, target catalog, cohort list, model, network or project import is used.
Approved cohort fingerprints are guards, not row selections.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys,os,shutil,gc
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

LINES=['motor','buildings','contents']
POLICIES=[p+'_'+l for p in ['policies','test'] for l in LINES]
def utc():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def fp(v):return hashlib.sha256(json.dumps(sorted(v),ensure_ascii=True,separators=(',',':')).encode()).hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def replace(t,name,v):
 field=t.schema.field(name)
 return t.set_column(t.schema.get_field_index(name),field,pa.array(v,type=field.type))

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--raw',required=True,type=Path);ap.add_argument('--rules',required=True,type=Path);ap.add_argument('--out',required=True,type=Path)
 a=ap.parse_args();raw=a.raw.resolve();rulesfile=a.rules.resolve();out=a.out.resolve()
 assert raw.is_dir() and not out.exists() and raw!=out and not raw.is_relative_to(out) and not out.is_relative_to(raw)
 out.mkdir(parents=True,exist_ok=False);(out/'data').mkdir();(out/'evidence').mkdir()
 reads=[]
 def audit(event,args):
  if event!='open' or not isinstance(args[0],(str,bytes,os.PathLike)):return
  p=Path(os.fsdecode(args[0])).resolve()
  if p.suffix.lower() not in ['.json','.parquet','.csv']:return
  mode=args[1];flags=args[2] if len(args)>2 else 0
  writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT)))
  if not writing:
   if not (p.parent==raw or p==rulesfile or p.is_relative_to(out)):raise RuntimeError('Unexpected data read: '+str(p))
   reads.append(str(p))
 sys.addaudithook(audit)
 rules=json.loads(rulesfile.read_text(encoding='utf-8'))
 expected=rules['originals_sha256']
 assert len(expected)==11 and set(expected)=={p.name for p in raw.glob('*.parquet')}
 before={name:sha(raw/name) for name in sorted(expected)};assert before==expected,'Raw input version changed'
 dump(out/'RUNNING.json',{'utc':utc(),'pid':os.getpid(),'source_sha256':sha(Path(__file__)),'rules_sha256':sha(rulesfile)})
 def load(name,columns=None):
  p=raw/(name+'.parquet');assert p.name in expected
  with p.open('rb') as f:return pq.read_table(f,columns=columns)
 def frame(name,columns=None):return load(name,columns).to_pandas()
 def check_set(v,c,key):
  values=list(v);assert len(values)==len(set(values))==c['count'] and fp(values)==c[key],'Approved cohort fingerprint mismatch'
 stats={};caps={};ren={};first={}
 # CAP01 selection from original, uncorrected household data; no cascading.
 for line in ['buildings','contents']:
  fields=rules['CAP01']['context_fields'][line]
  cols=['row_id','policy_id','period_start','period_end','sum_insured']+fields
  parts=[]
  for p in ['policies','test']:
   f=frame(p+'_'+line,cols);f['source_table']=p+'_'+line;parts.append(f)
  f=pd.concat(parts,ignore_index=True).sort_values(['policy_id','period_start','period_end','row_id']).reset_index(drop=True)
  f['period_start']=pd.to_datetime(f.period_start);f['period_end']=pd.to_datetime(f.period_end)
  extreme=f.sum_insured.gt(rules['CAP01']['thresholds'][line])
  positions=pd.Series(np.where(~extreme,np.arange(len(f)),np.nan),index=f.index)
  previous=positions.groupby(f.policy_id).ffill().groupby(f.policy_id).shift()
  exists=previous.notna();anchor=f.reindex(previous.fillna(-1).astype(int)).reset_index(drop=True)
  known=pd.Series(True,index=f.index);same=pd.Series(True,index=f.index)
  for name in fields:
   x,y=f[name],anchor[name]
   if name=='construction_type':x=x.astype('string').str.casefold().str.strip();y=y.astype('string').str.casefold().str.strip()
   known &= x.notna()&y.notna()&exists;same &= x.eq(y).fillna(False)
  selected=extreme&exists&known&same&(anchor.period_end<f.period_start)&(f.period_start-anchor.period_start).dt.days.between(1,400)&((f.sum_insured/1000)/anchor.sum_insured).between(.9,1.1)
  for name,g in f.loc[selected].groupby('source_table'):
   ids=g.row_id.tolist();check_set(ids,rules['CAP01']['approved_sets'][name],'row_ids_sha256');caps[name]=set(ids)
  print(json.dumps({'rule':'CAP01','line':line,'selected':int(selected.sum()),'cohort_guard':'exact'}),flush=True)
  del parts,f,anchor,positions,previous;gc.collect()
 assert set(caps)==set(rules['CAP01']['approved_sets'])
 # REN00 membership and earliest train start, separately by line to bound RAM.
 for line in LINES:
  tr=frame('policies_'+line,['row_id','policy_id','period_start','period_end','renewal_decision'])
  first[line]=pd.to_datetime(tr.period_start).groupby(tr.policy_id).min()
  te=frame('test_'+line,['row_id','policy_id','period_start','period_end']);te['renewal_decision']=pd.NA
  f=pd.concat([tr,te],ignore_index=True);f['period_start']=pd.to_datetime(f.period_start);f['period_end']=pd.to_datetime(f.period_end)
  f=f.sort_values(['policy_id','period_start','period_end']).reset_index(drop=True)
  year=f.period_start.dt.year;ny=year.groupby(f.policy_id).shift(-1)
  ids=sorted(f.loc[f.renewal_decision.eq('declined_by_insurer')&year.eq(2024)&ny.eq(2025),'policy_id'].unique().tolist())
  check_set(ids,rules['REN00']['approved_sets'][line],'policy_ids_sha256');ren[line]=set(ids)
  print(json.dumps({'rule':'REN00','line':line,'policies':len(ids),'cohort_guard':'exact'}),flush=True)
  del tr,te,f;gc.collect()
 customers=frame('customers',['customer_id','date_of_birth'])
 master=customers.customer_id.astype('string')
 assert master.is_unique and master.str.fullmatch('[0-9]{8}').all()
 births=customers.set_index('customer_id').date_of_birth
 renfield=pa.field('audit_ren00',pa.bool_(),nullable=False,metadata={
  b'role':b'audit_only',b'rule':b'REN00',b'excluded_from_predictors':b'true',
  b'cohort_sha256':rules['REN00']['cohort_source_file_sha256'].encode(),
  b'meaning':b'Policy membership in frozen 2024-declined/2025-successor cohort; not a row-level decision.'})
 for name in POLICIES:
  t=load(name);line=name.split('_',1)[1]
  f=t.select(['row_id','customer_id','period_start','period_end','exposure','policy_id']).to_pandas()
  ids=f.customer_id.astype('string')
  assert ids.str.fullmatch('[0-9]{1,8}').fillna(False).all()
  ids=ids.str.zfill(8);assert ids.isin(master).all()
  start=pd.to_datetime(f.period_start);end=pd.to_datetime(f.period_end)
  assert start.notna().all() and end.notna().all() and end.ge(start).all()
  exp=((end-start).dt.days.add(1)/rules['EXP01']['denominator']).round(rules['EXP01']['decimals'])
  q={'rows':t.num_rows,'ID01':int(ids.ne(f.customer_id).sum()),'EXP01':int(exp.ne(f.exposure).sum()),'CAP01':0,'CAT01':0,'AGE01':0}
  t=replace(t,'customer_id',ids);t=replace(t,'exposure',exp)
  if name in caps:
   values=t.column('sum_insured').to_pandas().to_numpy(copy=True);mask=f.row_id.isin(caps[name]).to_numpy()
   q['CAP01']=int(mask.sum());values[mask]=values[mask]/rules['CAP01']['scale'];t=replace(t,'sum_insured',values)
  if line!='motor':
   b=pd.to_datetime(ids.map(births));assert b.notna().all() and start.ge(b).all()
   ambiguous=b.dt.month.eq(2)&b.dt.day.eq(29)&~start.dt.is_leap_year&start.dt.month.eq(2)&start.dt.day.eq(28)
   assert not ambiguous.any(),'Leap birthday convention requires review'
   age=start.dt.year-b.dt.year-((start.dt.month<b.dt.month)|((start.dt.month==b.dt.month)&(start.dt.day<b.dt.day))).astype('int64')
   prior=t.column('policyholder_age').to_pandas();assert (age-prior).abs().le(1).all()
   q['AGE01']=int(age.ne(prior).sum());t=replace(t,'policyholder_age',age)
   if line=='buildings':
    prior=t.column('construction_type').to_pandas();cat=prior.replace(rules['CAT01']['map'])
    q['CAT01']=int(cat.ne(prior).sum());t=replace(t,'construction_type',cat)
  mark=pc.is_in(t['policy_id'],value_set=pa.array(sorted(ren[line]),type=t.schema.field('policy_id').type))
  q['REN00']=int(pc.sum(mark).as_py());t=t.append_column(renfield,mark)
  with (out/'data'/f'{name}.parquet').open('wb') as dest:pq.write_table(t,dest,compression='zstd')
  stats[name]=q;print(json.dumps({'table':name,**q}),flush=True);del t,f;gc.collect()
 # DUP01: complete-payload identical pairs; retain short reviewed representative.
 original=load('claims');c=original.to_pandas();assert c.claim_id.is_unique
 payload=[x for x in c.columns if x!='claim_id']
 duplicates=c.loc[c.duplicated(payload,keep=False)]
 pairs=[];excluded=[]
 for values in duplicates.groupby(payload,dropna=False,sort=False,observed=True).claim_id.agg(list):
  assert len(values)==2
  short=[x for x in values if pd.Series([x]).str.fullmatch('CL[0-9]{8}').iloc[0]]
  long=[x for x in values if pd.Series([x]).str.fullmatch('CL[0-9]{9}').iloc[0]]
  assert len(short)==len(long)==1;pairs.append((short[0],long[0]));excluded.append(long[0])
 assert len(pairs)==rules['DUP01']['count'] and fp(pairs)==rules['DUP01']['pairs_sha256']
 assert len(excluded)==len(set(excluded))
 keep=pc.invert(pc.is_in(original['claim_id'],value_set=pa.array(excluded,type=original.schema.field('claim_id').type)))
 t=original.filter(keep);c=t.to_pandas();preids=[]
 for line in LINES:
  z=c.loc[c.line.eq(line)];starts=z.policy_id.map(first[line]);assert starts.notna().all()
  preids+=z.loc[pd.to_datetime(z.loss_date).lt(starts),'claim_id'].tolist()
 check_set(preids,rules['PRE00'],'claim_ids_sha256')
 prefield=pa.field('audit_pre00',pa.bool_(),nullable=False,metadata={
  b'role':b'audit_only',b'rule':b'PRE00',b'excluded_from_predictors':b'true',
  b'excluded_from_current_period_target':b'true',b'cohort_sha256':rules['PRE00']['cohort_source_file_sha256'].encode(),
  b'meaning':b'Frozen pre-first-observed-period claim list; not a coverage or repudiation decision.'})
 marks=pc.is_in(t['claim_id'],value_set=pa.array(sorted(preids),type=t.schema.field('claim_id').type))
 t=t.append_column(prefield,marks)
 with (out/'data/claims.parquet').open('wb') as dest:pq.write_table(t,dest,compression='zstd')
 stats['claims']={'rows_before':original.num_rows,'rows':t.num_rows,'DUP01':len(excluded),'PRE00':int(pc.sum(marks).as_py())}
 del original,t,c;gc.collect()
 for name in sorted(expected):
  stem=Path(name).stem
  if stem not in POLICIES and stem!='claims':
   shutil.copyfile(raw/name,out/'data'/name);stats[stem]={'operation':'byte-copy unchanged original'}
 after={name:sha(raw/name) for name in sorted(expected)};assert before==after
 raw_reads=sorted({p for p in reads if Path(p).parent==raw})
 assert {Path(p).name for p in raw_reads}==set(expected)
 outputs={p.name:sha(p) for p in sorted((out/'data').glob('*.parquet'))};assert set(outputs)==set(expected)
 result={'utc':utc(),'all_builder_guards_passed':True,'tables':stats,'input_sha256':before,'inputs_unchanged':True,
  'output_sha256':outputs,'rules_sha256':sha(rulesfile),'source_sha256':sha(Path(__file__)),
  'raw_read_paths':raw_reads,'data_read_paths':sorted(set(reads)),'reference_data_reads':0,
  'environment':{'python':sys.version,'pandas':pd.__version__,'numpy':np.__version__,'pyarrow':pa.__version__},
  'new_models':0,'Kaggle_calls':0}
 dump(out/'build_receipt.json',result)
 dump(out/'COMPLETE.json',{'utc':utc(),'build_receipt_sha256':sha(out/'build_receipt.json'),'tables':11})
 print('RAW_ONLY_BASE_BUILD_COMPLETE',flush=True)
if __name__=='__main__':main()

