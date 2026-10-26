"""Solapamiento numérico de covariables 2023, sin leer etiquetas o producir precios."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2.modelos_robustos2023 import FEATURES,KEY,features
import numpy as np,pandas as pd,pyarrow.parquet as pq
OUT=R/'privado/semana2/robustez2023/mision017_20261025_v1/numeric_overlap2023.json';assert not OUT.exists();SOURCE=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1';BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();paths=[Path(__file__)];findings=[]
def load(path,line):
 names=pq.ParquetFile(path).schema_arrow.names;cols=KEY+['year','exposure']+FEATURES[line]['numeric']+FEATURES[line]['categorical']
 for c in ['x_voluntary_excess','x_compulsory_excess','x_distance_to_river_km']:
  if c in names:cols.append(c)
 cols=list(dict.fromkeys(cols));assert not set(['T0','T0_cents','reserve','prediction','annual_rate']).intersection(cols)
 f=pq.read_table(path,columns=cols,filters=[('year','=',2023)]).to_pandas();assert f.year.eq(2023).all() and not f.duplicated(KEY).any();return features(f,line)
def stats(s,w):
 x=s.to_numpy(float);good=np.isfinite(x);assert good.any();x=x[good];w=w[good];w=w/w.sum();mean=float(w@x);return {'missing_fraction':float(1-good.mean()),'minimum':float(x.min()),'maximum':float(x.max()),'weighted_mean':mean,'weighted_sd':float(np.sqrt(w@((x-mean)**2))),'quantiles':np.quantile(x,[.005,.05,.25,.5,.75,.95,.995]).tolist()}
for line in FEATURES:
 p=SOURCE/f'{line}_2023.parquet';q=BASE/f'{line}_fold0.parquet';paths +=[p,q];s=load(p,line);t=load(q,line);assert s.market.eq('developed').all() and t.market.eq('emerging').all()
 for col in FEATURES[line]['numeric']:
  a=stats(s[col],s.exposure.to_numpy(float));b=stats(t[col],t.exposure.to_numpy(float));x=t[col].to_numpy(float);valid=np.isfinite(x);den=np.sqrt((a['weighted_sd']**2+b['weighted_sd']**2)/2);standard=(b['weighted_mean']-a['weighted_mean'])/den if den>0 else 0.;findings.append({'line':line,'column':col,'source':a,'target':b,'standardized_mean_shift':standard,'target_finite_rows_outside_source_range':int(((x<a['minimum'])|(x>a['maximum']))[valid].sum()),'target_finite_fraction_beyond_source_clip':float(((x<a['quantiles'][0])|(x>a['quantiles'][-1]))[valid].mean())})
report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scope':'numeric covariates and nominal exposure only,2023;no costlabels,predictions,fits or2024rows','interpretation':'descriptive marginal overlap,not jointsupport,causality,transportability,temporalavailability or permission tocorrectfeatures;repeatedperiodsnot independent','findings':findings,'prior_categorical_levels_receipt_reused':rel(R/'privado/semana2/robustez2023/categorical_domains2023.json'),'prior_categorical_sha256':sha(R/'privado/semana2/robustez2023/categorical_domains2023.json'),'new_fits':0,'new_scores':0,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
with OUT.open('x',encoding='utf-8') as h:json.dump(report,h,ensure_ascii=False,indent=2)
print(json.dumps({'scope':report['scope'],'largest_shifts':[{'line':x['line'],'column':x['column'],'standardized_mean_shift':x['standardized_mean_shift'],'target_fraction_beyond_source_clip':x['target_finite_fraction_beyond_source_clip'],'target_rows_outside_source_range':x['target_finite_rows_outside_source_range']} for x in sorted(findings,key=lambda r:-abs(r['standardized_mean_shift']))[:12]]}))
