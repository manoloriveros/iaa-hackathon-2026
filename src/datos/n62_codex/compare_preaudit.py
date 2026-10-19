"""Compare a completed raw-only rebuild with frozen preaudit; never alter either input."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib,sys
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
def utc():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
def load(p):
 with Path(p).open('rb') as f:return pq.read_table(f)
def main():
 p=argparse.ArgumentParser();p.add_argument('--rebuild',required=True,type=Path);p.add_argument('--catalog',required=True,type=Path);p.add_argument('--project-root',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
 a=p.parse_args();build=a.rebuild.resolve();root=a.project_root.resolve();out=a.out.resolve()
 receipt=read(build/'build_receipt.json')
 assert read(build/'COMPLETE.json')['build_receipt_sha256']==sha(build/'build_receipt.json')
 assert receipt['all_builder_guards_passed'] and receipt['reference_data_reads']==0
 catalog=read(a.catalog);assert len(catalog)==11
 assert not out.exists();out.mkdir(parents=True)
 references={name:(root/e['workspace_relative_path']).resolve() for name,e in catalog.items()}
 assert all(p.is_relative_to(root) for p in references.values())
 before={name:sha(p) for name,p in references.items()}
 assert before=={name:e['sha256'] for name,e in catalog.items()},'Reference has changed since frozen contract'
 summaries=[]
 for name,e in sorted(catalog.items()):
  made=build/'data'/f'{name}.parquet';assert sha(made)==receipt['output_sha256'][made.name]
  x=load(made);y=load(references[name])
  rows=x.num_rows==y.num_rows;columns=x.column_names==y.column_names
  schema_types=columns and all(x.schema.field(c).type==y.schema.field(c).type for c in x.column_names)
  q={'table':name,'rows_rebuilt':x.num_rows,'rows_reference':y.num_rows,'columns':len(y.column_names),'row_count_equal':rows,'column_order_equal':columns,'types_equal':schema_types,
   'schema_metadata_equal':x.schema.equals(y.schema,check_metadata=True),'file_byte_identical':sha(made)==before[name],'column_checks':[]}
  for col in sorted(set(x.column_names)&set(y.column_names)):
   b=x[col].combine_chunks();c=y[col].combine_chunks()
   same_nulls=rows and pc.is_null(b).equals(pc.is_null(c))
   if not rows or b.type!=c.type:
    n=max(len(b),len(c));samples=[]
   elif b.equals(c):n=0;samples=[]
   else:
    bx=pd.Series(b.to_pandas());cy=pd.Series(c.to_pandas())
    eq=(bx.eq(cy)|(bx.isna()&cy.isna())).fillna(False)
    bad=np.flatnonzero(~eq.to_numpy(dtype=bool));n=len(bad)
    samples=[{'position':int(i),'rebuilt':str(bx.iloc[i]),'reference':str(cy.iloc[i])} for i in bad[:5]]
   q['column_checks'].append({'column':col,'null_positions_equal':bool(same_nulls),'value_differences':int(n),'examples':samples})
  q['value_differences']=sum(z['value_differences'] for z in q['column_checks'])
  q['all_null_positions_equal']=all(z['null_positions_equal'] for z in q['column_checks'])
  q['all_values_rows_types_equal']=rows and columns and schema_types and q['all_null_positions_equal'] and q['value_differences']==0
  q['all_columns_compared_in_original_row_order']=rows and columns
  summaries.append(q)
  print(json.dumps({k:v for k,v in q.items() if k!='column_checks'},ensure_ascii=False),flush=True)
  del x,y
 after={name:sha(p) for name,p in references.items()};assert before==after
 assert all(sha(build/'data'/filename)==h for filename,h in receipt['output_sha256'].items())
 result={'utc':utc(),'all_values_rows_types_equal':all(z['all_values_rows_types_equal'] for z in summaries),
 'all_arrow_metadata_equal':all(z['schema_metadata_equal'] for z in summaries),
 'tables_compared':len(summaries),'total_rows_rebuilt':sum(z['rows_rebuilt'] for z in summaries),
 'total_cells_compared':sum(z['rows_reference']*z['columns'] for z in summaries),
 'value_differences':sum(z['value_differences'] for z in summaries),
 'byte_identical_tables':sum(z['file_byte_identical'] for z in summaries),'tables':summaries,
 'reference_files_unchanged':before==after,'rebuild_files_unchanged':True,
 'build_receipt_sha256':sha(build/'build_receipt.json'),'reference_catalog_sha256':sha(a.catalog),
 'reference_sha256':before,'source_sha256':sha(Path(__file__)),'new_models':0,'Kaggle_calls':0,
 'scope':'All row positions, columns, logical types, null masks and values; metadata/file bytes reported separately. This does not validate appropriateness or prospective availability of historical decisions.'}
 dump(out/'result.json',result);dump(out/'COMPLETE.json',{'utc':utc(),'result_sha256':sha(out/'result.json'),'passed':result['all_values_rows_types_equal']})
 print(json.dumps({'comparison_complete':True,**{k:result[k] for k in ['all_values_rows_types_equal','all_arrow_metadata_equal','tables_compared','total_rows_rebuilt','total_cells_compared','value_differences','byte_identical_tables']}}),flush=True)
 if not result['all_values_rows_types_equal']:raise SystemExit(2)
if __name__=='__main__':main()

