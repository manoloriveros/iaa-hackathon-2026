"""Conserva la edad declarada fuente2023 y los datos originales, sin corregirlos."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/edad2023_inputs_v1';AGE=R/'privado/semana2/robustez2023/edad2023_auditoria_v1';SRC=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
KEY=['market','line','row_id'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
assert not OUT.exists();OUT.mkdir(parents=True);sources=[AGE/'report.json',Path(__file__)];checks=[]
for line in ['motor','buildings','contents']:
 p=SRC/f'{line}_2023.parquet';a=AGE/f'{line}_source_age2023.parquet';t=AGE/f'{line}_target_band2023.parquet';sources +=[p,a,t]
 original=pq.read_table(p,filters=[('year','=',2023)]).to_pandas();extra=pq.read_table(a,columns=KEY+['source_raw_age','source_raw_band']).to_pandas().rename(columns={'source_raw_age':'x_exact_age','source_raw_band':'x_transport_band'});assert extra.row_id.is_unique
 f=original.merge(extra,on=KEY,validate='one_to_one',how='left');assert len(f)==len(original) and f.x_exact_age.notna().all() and f.x_transport_band.notna().all()
 before=original.sort_values(KEY).reset_index(drop=True);after=f.sort_values(KEY).reset_index(drop=True)
 for col in original:assert before[col].equals(after[col]),col
 f.to_parquet(OUT/f'{line}_2023.parquet',index=False)
 target=pq.read_table(t).to_pandas();c='x_driver_age_band' if line=='motor' else 'x_policyholder_age_band';target=target.rename(columns={c:'x_transport_band'});assert target.year.eq(2023).all() and target.market.eq('emerging').all() and target.x_transport_band.notna().all();target.to_parquet(OUT/f'{line}_emerging_bands.parquet',index=False)
 checks.append({'line':line,'source_rows':len(f),'target_band_rows':len(target),'all_original_columns_exact':True,'source_declared_age_preserved':True,'DOB_not_substituted':True,'no_target_exact_age':True})
report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'new_fits':0,'new_C0':0,'2024_rows_read':0,'source_age_rule':'raw inception-age as supplied;small home DOB discrepancies retained,not silently corrected;motor main driver never replaced with policyholderDOB','sources':[{'path':rel(p),'sha256':sha(p)} for p in dict.fromkeys(sources)],'outputs':[{'path':rel(p),'sha256':sha(p)} for p in OUT.glob('*.parquet')]}
with (OUT/'report.json').open('x',encoding='utf-8') as h:json.dump(report,h,ensure_ascii=False,indent=2)
print(json.dumps(checks))
