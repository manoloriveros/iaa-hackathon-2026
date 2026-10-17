"""Comprueba identidades contables, cobertura documental y artefactos del análisis."""
import csv
import hashlib
import json
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from PIL import Image

BASE=Path(__file__).parent
OUT=ROOT/json.loads((BASE/'current_run.json').read_text(encoding='utf-8'))['run']
profiles=json.loads((OUT/'profiles.json').read_text(encoding='utf-8'))
hashes=json.loads((OUT/'input_hashes.json').read_text(encoding='utf-8'))
reference=json.loads((ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/data_manifest.json').read_text(encoding='utf-8'))
expected={Path(v['path']).name:v['sha256'] for v in reference['files']}
annual=pd.read_csv(OUT/'tables/annual_summary.csv')
calendar=pd.read_csv(OUT/'tables/annual_summary_date365.csv')
segments=pd.read_csv(OUT/'tables/segments_date365.csv')
claims=pd.read_parquet(OUT/'tables/claims_diagnostic.parquet')
unmatched=pd.DataFrame(json.loads((OUT/'unmatched_claims_diagnosis.json').read_text(encoding='utf-8')))
dictionary=pd.read_csv(OUT/'tables/dictionary_interpreted.csv')
source_columns={(p['name'],c['name']) for p in profiles for c in p['columns']}
documented=set(zip(dictionary.table,dictionary.column))
checks={
    'input_hashes_match_original_archive_manifest':hashes==expected,
    'all_11_tables_profiled':len(profiles)==11,
    'every_physical_column_documented':documented==source_columns,
    'all_105_column_names_interpreted':dictionary.column.nunique()==105,
    'calendar_sensitivity_preserves_claim_costs':bool(np.allclose(annual.net_incurred,calendar.net_incurred)),
    'calendar_sensitivity_preserves_claim_counts':bool(np.array_equal(annual.reported_accepted_claims,calendar.reported_accepted_claims)),
}
accepted=claims.loc[claims.status!='repudiated'].groupby('line').observed_net_incurred.sum()
reconciled=annual.groupby('line').net_incurred.sum().add(unmatched.set_index('line').net_incurred_excl_declined)
checks['assigned_plus_pre_window_claims_reconcile_all_accepted_costs']=bool(np.allclose(accepted.sort_index(),reconciled.sort_index(),atol=.00001))
totals=calendar.groupby('line').agg(exposure=('exposure','sum'),cost=('net_incurred','sum'),claims=('reported_accepted_claims','sum'))
for (line,feature),group in segments.groupby(['line','feature']):
    for col,reference_col in [('exposure','exposure'),('cost','cost'),('claims','claims')]:
        assert np.isclose(group[col].sum(),totals.loc[line,reference_col],rtol=1e-10,atol=1e-5),(line,feature,col)
checks['all_segment_groups_reconcile_exposure_claims_cost']=True
nonnull=segments.observed_severity.notna()
checks['frequency_times_severity_equals_observed_cost_rate']=bool(np.allclose(
    segments.loc[nonnull,'reported_frequency']*segments.loc[nonnull,'observed_severity'],
    segments.loc[nonnull,'observed_cost_per_exposure'],rtol=1e-10))

class Structure(HTMLParser):
    def __init__(self):
        super().__init__();self.cards=0;self.images=0;self.ids=set()
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='article' and attrs.get('class')=='column-card':self.cards+=1
        if tag=='img':self.images+=1
        if 'id' in attrs:self.ids.add(attrs['id'])

parsed=Structure();parsed.feed((OUT/'informe.html').read_text(encoding='utf-8'))
checks['html_contains_105_column_cards']=parsed.cards==105
checks['html_navigation_and_search_targets_exist']=set(['modelo','calidad','experiencia','tiempo','diccionario','acciones','search','counter','expand']).issubset(parsed.ids)
for image in (OUT/'graficos').glob('*.png'):
    with Image.open(image) as im:im.verify()
checks['all_generated_png_files_decode']=True
checks['each_embedded_figure_has_exported_png']=parsed.images==len(list((OUT/'graficos').glob('*.png')))
result={'checks':checks,'technical_artifact_checks_passed':all(checks.values()),
        'dataset_approved_for_modeling':False,'independent_validation':False,
        'human_review':'pending','training_performed':False,
        'browser_interaction_verified':False,
        'browser_limitation':'Browser URL policy disallowed file protocol; no workaround attempted. HTML checked statically; selected PNGs visually inspected.',
        'profiled_rows':sum(p['rows'] for p in profiles),'column_names':105,'physical_columns':len(source_columns),
        'figures':parsed.images,'conclusions':'Technical consistency of derived evidence verified; material source-data findings and actuarial assumptions remain open.'}
(OUT/'analysis_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True))
assert all(checks.values())
