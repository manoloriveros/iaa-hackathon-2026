"""Vista de medición con faltantes fijos, sin tocar etiquetas ni inflar muestra."""
import hashlib
import numpy as np,pandas as pd
KEY=['market','line','row_id'];SEED='2026102526';PROBABILITY=.10
FIELDS={'motor':{'x_vehicle_age':'policy','x_engine_size_cc':'policy'},'buildings':{'x_smoke_alarms':'policy','x_distance_to_river_km':'address'},'contents':{'x_high_value_items':'policy','x_distance_to_river_km':'address'}}

def apply(frame,line):
 assert frame.year.eq(2023).all() and frame.market.eq('developed').all() and frame.line.eq(line).all() and not frame.duplicated(KEY).any()
 out=frame.copy();changed=set();receipts=[]
 for column,entity in FIELDS[line].items():
  key='address_id' if entity=='address' else 'policy_id';derived='x_log_'+column[2:];available=[c for c in [column,derived] if c in frame];assert frame[key].notna().all() and available
  # Distance is a shared address attribute. Contractual answers use policy and line.
  identities=frame[key].astype(str).map(lambda v:entity+':'+('' if entity=='address' else line+':')+v)
  unique=identities.unique();selected={v:int.from_bytes(hashlib.sha256((SEED+'|'+column+'|'+v).encode()).digest()[:8],'big')/2**64<PROBABILITY for v in unique}
  mask=identities.map(selected).to_numpy(bool);observed=available[0];before=pd.to_numeric(frame[observed],errors='raise')
  for actual in available:
   out[actual]=pd.to_numeric(frame[actual],errors='raise').astype(float).mask(mask);changed.add(actual);assert np.array_equal(pd.to_numeric(frame.loc[~mask,actual]).to_numpy(float),out.loc[~mask,actual].to_numpy(float),equal_nan=True)
  receipts.append({'column':column,'stored_columns':available,'entity':key,'probability_additional':PROBABILITY,'rows':len(frame),'entities':len(unique),'masked_entities':sum(selected.values()),'original_missing':int(before.isna().sum()),'additional_observed_to_missing':int((mask&before.notna().to_numpy()).sum()),'final_missing':int(out[observed].isna().sum())})
 for column in frame:
  if column not in changed:assert out[column].equals(frame[column]),column
 assert len(out)==len(frame) and out[KEY].equals(frame[KEY])
 return out,{'line':line,'rows':len(out),'seed':SEED,'probability':PROBABILITY,'fields':receipts,'all_costs_and_exposures_unchanged':True,'no_new_rows':True,'unmodified_columns':len(frame.columns)-len(changed),'changed_covariate_columns':sorted(changed),'label_independent_entity_stable':True}
