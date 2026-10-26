"""Vista de medición con faltantes fijos, sin tocar etiquetas ni inflar muestra."""
import hashlib
import numpy as np,pandas as pd
KEY=['market','line','row_id'];SEED='2026102526';PROBABILITY=.10
FIELDS={'motor':{'x_vehicle_age':'policy','x_engine_size_cc':'policy'},'buildings':{'x_smoke_alarms':'policy','x_distance_to_river_km':'address'},'contents':{'x_high_value_items':'policy','x_distance_to_river_km':'address'}}

def apply(frame,line):
 assert frame.year.eq(2023).all() and frame.market.eq('developed').all() and frame.line.eq(line).all() and not frame.duplicated(KEY).any()
 out=frame.copy();changed=set();receipts=[]
 for column,entity in FIELDS[line].items():
  key='address_id' if entity=='address' else 'policy_id';assert frame[key].notna().all() and column in frame
  # Distance is a shared address attribute. Contractual answers use policy and line.
  identities=frame[key].astype(str).map(lambda v:entity+':'+('' if entity=='address' else line+':')+v)
  unique=identities.unique();selected={v:int.from_bytes(hashlib.sha256((SEED+'|'+column+'|'+v).encode()).digest()[:8],'big')/2**64<PROBABILITY for v in unique}
  mask=identities.map(selected).to_numpy(bool);before=pd.to_numeric(frame[column],errors='raise');out[column]=before.astype(float).mask(mask);changed.add(column)
  derived='x_log_'+column[2:]
  if derived in frame:out[derived]=pd.to_numeric(frame[derived],errors='raise').astype(float).mask(mask);changed.add(derived)
  assert np.array_equal(before[~mask].to_numpy(float),out.loc[~mask,column].to_numpy(float),equal_nan=True)
  receipts.append({'column':column,'entity':key,'probability_additional':PROBABILITY,'rows':len(frame),'entities':len(unique),'masked_entities':sum(selected.values()),'original_missing':int(before.isna().sum()),'additional_observed_to_missing':int((mask&before.notna().to_numpy()).sum()),'final_missing':int(out[column].isna().sum())})
 for column in frame:
  if column not in changed:assert out[column].equals(frame[column]),column
 assert len(out)==len(frame) and out[KEY].equals(frame[KEY])
 return out,{'line':line,'rows':len(out),'seed':SEED,'probability':PROBABILITY,'fields':receipts,'all_costs_and_exposures_unchanged':True,'no_new_rows':True,'unmodified_columns':len(frame.columns)-len(changed),'changed_covariate_columns':sorted(changed),'label_independent_entity_stable':True}
