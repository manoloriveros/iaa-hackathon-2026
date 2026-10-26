"""Preservar lector fallido y seleccionar columnas físicas antes de derivar logaritmos."""
from pathlib import Path
R=Path('C:/dev/Hakaton/Hackaton/Repositorio_IAA2026');p=R/'herramientas/auditar_solapamiento_numerico2023.py';s=p.read_text(encoding='utf-8')
old=" cols=list(dict.fromkeys(cols));assert not set(['T0','T0_cents','reserve','prediction','annual_rate']).intersection(cols)"
new=" cols=list(dict.fromkeys(cols));derived={'x_log_voluntary_excess':'x_voluntary_excess','x_log_compulsory_excess':'x_compulsory_excess','x_log_distance_to_river_km':'x_distance_to_river_km'};missing=set(cols)-set(names);assert all(c in derived and derived[c] in names for c in missing),missing;cols=[c for c in cols if c in names];assert not set(['T0','T0_cents','reserve','prediction','annual_rate']).intersection(cols)"
assert s.count(old)==1;s=s.replace(old,new).replace("'new_fits':0,'new_scores':0", "'reader_version':2,'previous_reader_failed_before_output_missing_derived_columns':True,'new_fits':0,'new_scores':0")
out=R/'herramientas/auditar_solapamiento_numerico2023_v2.py';assert not out.exists();out.write_text(s,encoding='utf-8');print('Reader v1 preserved;v2 reads raw covariates only and derives logs in memory.')
