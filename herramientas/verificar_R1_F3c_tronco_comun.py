"""Verifica la comparación congelada y separa cambios de nivel y de precios individuales."""
from pathlib import Path
from decimal import Decimal,localcontext
import importlib.util,json,sys
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
s=importlib.util.spec_from_file_location('common',R/'herramientas/comparar_R1_F3c_tronco_comun.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def main():
    m.guard();t=pd.read_parquet(m.OUT/'paired_prices_and_bridge.parquet');r=m.w.read(m.OUT/'results.json')
    checks={};effects=[]
    for (line,nb),g in t.groupby(['line','new_business']):
        row={'line':line,'new_business':int(nb),'rows':len(g)}
        for name,numerator,denominator in [('NB_rule_F3c','F3c_trunk_NBfallback','F3c'),('NB_rule_R1','R1','R1_trunk_fullown')]:
            change=(g[numerator]/g[denominator]-1).to_numpy()
            row[name]={'total_change_fraction':float(g[numerator].sum()/g[denominator].sum()-1),'mean_absolute_relative_change':float(np.abs(change).mean()),
                'p95_absolute_relative_change':float(np.quantile(np.abs(change),.95)),'fraction_abs_change_over_10pct':float(np.mean(np.abs(change)>.10)),
                'min_relative_change':float(change.min()),'max_relative_change':float(change.max())}
        row['C1_over_F2_cell_total']=float(g.C1.sum()/g.F2.sum())
        row['R1base_over_F2_cell_total']=float(g.R1base.sum()/g.F2.sum())
        effects.append(row)
    checks['all_renewal_policy_identity']=all(row['NB_rule_F3c']['mean_absolute_relative_change']==0 and row['NB_rule_R1']['mean_absolute_relative_change']<3e-14 for row in effects if row['new_business']==0)
    # Decimal: independent scalar price-bridge, 3factor subsets and own-fallback.
    i=np.unique(np.r_[0,len(t)-1,np.argmax(t.R1),np.argmin(t.R1),np.arange(0,len(t),3049)])
    maxerr=0.;maxadd=0.
    with localcontext() as context:
        context.prec=65
        for k in i:
            row=t.iloc[int(k)];start=Decimal(str(row.F3c));end=Decimal(str(row.R1));prod=start
            for name in m.NAMES:prod*=Decimal(str(row['factor_'+name]))
            maxerr=max(maxerr,float(abs(prod-end)/end))
            add=start+sum(Decimal(str(row['shapley_'+name])) for name in m.NAMES)
            maxadd=max(maxadd,float(abs(add-end)/end))
    checks['Decimal_product_bridge']=maxerr<3e-13;checks['Decimal_additive_bridge']=maxadd<3e-13
    # Independently sum all rows; no rescoring or hidden labels used.
    row_delta=t.R1.to_numpy()-t.F3c.to_numpy();shap=t[['shapley_'+n for n in m.NAMES]].to_numpy()
    checks['all_row_additive_identity']=np.allclose(shap.sum(axis=1),row_delta,rtol=1e-12,atol=1e-10)
    checks['global_and_six_cells_reconcile']=all(abs(sum(x[n+'_total'] for x in r['six_cells'])-r['global'][n+'_total'])<1e-6 for n in ['R1','F3c','C1','F2'])
    checks['global_ShAP_reconciles']=abs(sum(r['global']['shapley_CU'].values())-r['global']['R1_minus_F3c_total'])<1e-6
    checks['saved_model_and_production_sources_unchanged']=True # guard() already checked every frozen SHA.
    checks['both_original_CSV_hashes_preserved']=m.w.sha(m.F3)==m.SHA_F3 and m.w.sha(m.R1/'R1_T2b_2025.csv')==m.SHA_R1
    checks['no_upload_csv_created']=not list(m.OUT.glob('*.csv'))
    checks['all_passed']=all(checks.values())
    result={'author':'Codex','utc':m.utc(),'checks':checks,'Decimal_samples':len(i),'max_Decimal_product_relative_error':maxerr,
        'max_Decimal_additive_relative_error':maxadd,'matched_policy_individual_effects':effects,
        'new_native_or_closed_fits':0,'new_Booster_inference':0,'new_bootstrap_draws':0,'new_submissions':0,
        'individual_changes_may_matter_despite_small_total':True,'no_metric_attribution_without2025labels':True,
        'verifier_sha256':m.w.sha(Path(__file__))}
    m.dump(m.OUT/'verification.json',result);assert checks['all_passed'],checks
    print(json.dumps({'all_passed':True,'Decimal_samples':len(i),'matched_policy_individual_effects':effects}),flush=True)
if __name__=='__main__':main()
