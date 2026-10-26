"""Cinco bloques de componentes fuente2023, sin cambiar folds emergentes."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/bloques_fuente2023_v1';S=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
import pandas as pd
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
class Components:
 def __init__(self):self.parent={}
 def find(self,x):
  if x not in self.parent:self.parent[x]=x
  while self.parent[x]!=x:self.parent[x]=self.parent[self.parent[x]];x=self.parent[x]
  return x
 def union(self,a,b):
  a=self.find(a);b=self.find(b)
  if a!=b:self.parent[max(a,b)]=min(a,b)
def main():
 assert not OUT.exists();OUT.mkdir(parents=True);parts=[];paths=[]
 for line in ['motor','buildings','contents']:
  p=S/f'{line}_2023.parquet';paths.append(p);f=pq.read_table(p,columns=['market','line','row_id','year','customer_id','address_id'],filters=[('year','=',2023)]).to_pandas();assert f.year.eq(2023).all() and f.market.eq('developed').all();parts.append(f)
 f=pd.concat(parts,ignore_index=True);assert len(f)==626355 and not f.duplicated(['market','line','row_id']).any()
 u=Components()
 for c,a in f[['customer_id','address_id']].itertuples(index=False,name=None):u.union('c:'+c,'a:'+a)
 roots={c:u.find('c:'+c) for c in f.customer_id.unique()};ids={root:'DSG_'+hashlib.sha256(root.encode()).hexdigest()[:20] for root in set(roots.values())};f['source_group_id']=f.customer_id.map(lambda c:ids[roots[c]])
 groups=sorted(f.source_group_id.unique());folds={g:int(hashlib.sha256(('C17-source2023:'+g).encode()).hexdigest()[:8],16)%5 for g in groups};f['source_fold']=f.source_group_id.map(folds)
 assert f.groupby('customer_id').source_fold.nunique().max()==1 and f.groupby('address_id').source_fold.nunique().max()==1
 for line in ['motor','buildings','contents']:f[f.line.eq(line)].to_parquet(OUT/f'{line}.parquet',index=False)
 report={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','rows':len(f),'groups':len(groups),'fold_counts':f.groupby(['line','source_fold']).size().to_dict().__str__(),'customer_address_components_exact':True,'no_outcomes_read':True,'emerging_folds_changed':False,'price_fits':0,'each_source_row_training_multiplicity_in_five_bags':4,
 'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths],'outputs':[{'path':rel(p),'sha256':sha(p)} for p in OUT.glob('*.parquet')]}
 with (OUT/'report.json').open('x',encoding='utf-8') as h:json.dump(report,h,ensure_ascii=False,indent=2)
 print(json.dumps({k:v for k,v in report.items() if k not in ['sources','outputs']}))
if __name__=='__main__':main()
