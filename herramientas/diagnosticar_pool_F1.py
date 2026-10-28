"""Diferencia nueva y concreta entre pools de reportes F1, sin precios."""
from pathlib import Path
import importlib.util,json,sys
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1];sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pandas as pd
import numpy as np
s=importlib.util.spec_from_file_location('pool_f1',R/'herramientas/validar_F3c_completo.py');f=importlib.util.module_from_spec(s);s.loader.exec_module(f)

def main():
    rows=[]
    for market,mk in [('developed','s1'),('emerging','s2')]:
        oldpath=f.LEGACY/'noche/salidas'/mk/'asignacion.parquet';newpath=f.ACTIVE/'prepared'/f'{market}_claims.parquet'
        old=pd.read_parquet(oldpath,columns=['claim_id','policy_id','line','report_date','accepted','category']);old=old[old.accepted].copy();old['report_date']=pd.to_datetime(old.report_date)
        new=pd.read_parquet(newpath,columns=['claim_id','policy_id','line','report_date','accepted']);new=new[new.accepted].copy();new['report_date']=pd.to_datetime(new.report_date)
        keys=['claim_id','policy_id','line','report_date'];missing=old.merge(new[keys].drop_duplicates(),on=keys,how='left',indicator=True);missing=missing[missing._merge.eq('left_only')].drop(columns='_merge')
        extra=new.merge(old[keys].drop_duplicates(),on=keys,how='left',indicator=True);extra=extra[extra._merge.eq('left_only')].drop(columns='_merge')
        missing.to_parquet(f.OUT/(market+'_original_F1_reports_missing_in_prepared.parquet'),index=False);extra.to_parquet(f.OUT/(market+'_prepared_F1_reports_extra.parquet'),index=False)
        rows.append({'market':market,'original_accepted':len(old),'prepared_accepted':len(new),'missing_from_prepared':len(missing),'extra_in_prepared':len(extra),'missing_by_category':missing.category.value_counts(dropna=False).to_dict(),'missing_by_line':missing.line.value_counts().to_dict(),'duplicate_original_event_keys':int(old.duplicated(keys).sum()),'original_sha256':f.sha(oldpath),'prepared_sha256':f.sha(newpath)})
    attempts={line:[json.loads(z) for z in (f.OUT/('fit_attempts_'+line+'.jsonl')).read_text().splitlines()] for line in ['motor','buildings']}
    counts={'total_started_native':sum(len(z) for z in attempts.values()),'F1_wrong_pool_started':sum(x['family']=='F1' for z in attempts.values() for x in z),'N0_started':sum(x['family']=='N0' for z in attempts.values() for x in z)}
    result={'author':'Codex','utc':f.utc(),'records':rows,'counts_before_correction':counts,'new_price_fits':0,'new_scores':0,'target_started':(f.OUT/'target_started.json').exists(),'interruption':'Own buildings producer16212stopped after F1seed13fullcheckpoint; N0poisonseed12inner subsequently started and was interrupted, no completed inner checkpoint. Queue14903terminated on unclassified childexit; no contents or target fit started.'}
    f.dump(f.OUT/'F1_pool_diagnosis.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':sys.stdout.reconfigure(encoding='utf8');main()
