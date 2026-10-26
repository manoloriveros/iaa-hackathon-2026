"""Diagnóstico finito de artefactos NUEVOS A1S; sin ajustar ni inferir modelos."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
HOME=R/'privado/semana2/mision017_fase2/A1S_nucleo_20261026_v1'
SOURCE=HOME/'source_models';OUT=HOME/'source_tail_seed_audit'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd

sp=importlib.util.spec_from_file_location('source_tail_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w)


def main():
    assert not OUT.exists(),'Existing audit must be reused, not repeated.'
    assert (HOME/'completion_receipt.json').exists()
    OUT.mkdir()
    paths=[Path(__file__),SOURCE/'report.json',HOME/'completion_receipt.json']
    results=[];bycell=[]
    for line in ['motor','buildings','contents']:
        rp=HOME/f'rows_s1_{line}.parquet';pp=HOME/f'partition_source/folds_{line}.parquet'
        paths+=[rp,pp]
        rows=pd.read_parquet(rp,columns=['row_id','year','new_business','T0'])
        groups=pd.read_parquet(pp,columns=['row_id','source_group','internal_validation'])
        assert np.array_equal(rows.row_id,groups.row_id)
        row_reports=[]
        for seed in [11,12,13]:
            path=SOURCE/f'{line}_seed{seed}_full/source_components.parquet';paths.append(path)
            comp=pd.read_parquet(path);assert np.array_equal(rows.row_id,comp.row_id)
            y=rows.T0.to_numpy(float);mu=comp.conditional_source_mu.to_numpy(float)
            assert (y>=0).all() and (mu>0).all()
            # y/sqrt(mu) is the observed sufficient-statistic contribution to
            # the Tweedie multiplicative-level score, not a causal influence.
            mass=y/np.sqrt(mu)
            group=pd.DataFrame({'group':groups.source_group,'T0':y,'observed_score_mass':mass,
                                'absolute_gradient':np.abs(np.sqrt(mu)-mass)}).groupby('group',sort=True).sum()
            largest=group.observed_score_mass.sort_values(ascending=False)
            top31=group.loc[largest.index[:31]].copy()
            top31.to_parquet(OUT/f'{line}_seed{seed}_top31_training_groups.parquet')
            entry={'line':line,'seed':seed,'source_rows':len(rows),'source_groups':len(group),
                   'positive_periods':int(np.count_nonzero(y>0)),
                   'top1_group_score_mass_share':float(largest.iloc[0]/largest.sum()),
                   'top31_group_score_mass_share':float(largest.iloc[:31].sum()/largest.sum()),
                   'top31_same_groups_T0_share':float(top31.T0.sum()/y.sum()),
                   'largest_period_T0':float(y.max()),'largest_period_T0_share':float(y.max()/y.sum()),
                   'top31_absolute_gradient_share':float(top31.absolute_gradient.sum()/group.absolute_gradient.sum()),
                   'training_in_sample_not_independent_influence':True}
            results.append(entry)
        for market in ['s1','s2']:
            rp=HOME/f'rows_{market}_{line}.parquet';paths.append(rp)
            meta=pd.read_parquet(rp,columns=['row_id','year','new_business'])
            logs=[]
            for seed in [11,12,13]:
                path=SOURCE/f'{line}_seed{seed}_full/{"source" if market=="s1" else "target"}_components.parquet'
                paths.append(path);frame=pd.read_parquet(path,columns=['row_id','log_relative'])
                assert np.array_equal(meta.row_id,frame.row_id)
                logs.append(frame.log_relative.to_numpy(float))
            logs=np.stack(logs);spread=np.exp(logs.max(axis=0)-logs.min(axis=0))
            sigma=logs.std(axis=0)
            assert np.isfinite(spread).all() and (spread>=1).all()
            for (year,nb),ix in meta.groupby(['year','new_business']).groups.items():
                ii=np.array(list(ix));bycell.append({'line':line,'market':market,'year':int(year),'new_business':int(nb),
                    'rows':len(ii),'max_min_seed_relative_ratio_quantiles':np.quantile(spread[ii],[.5,.9,.99,1]).tolist(),
                    'log_relative_seed_sd_quantiles':np.quantile(sigma[ii],[.5,.9,.99,1]).tolist()})
    sources={w.rel(p):w.sha(p) for p in paths}
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'saved_new_A1S_artifact_diagnostic_complete',
            'observed_score_mass_definition':'y/sqrt(mu), from saved full-source conditional incurred-cost predictions; source-row grouped sum',
            'top31_rule':'Descriptive top31source groups by score mass, fixed before reading the audit; not removed, trimmed or rescored',
            'source_tail':results,'seed_stability':bycell,'sources':sources,
            'new_model_fits':0,'new_C0_fits':0,'new_model_inference':0,'new_calibration_fits':0,'new_price_scores':0,
            'new_final_test_prices':0,'new_submissions':0,'2024_open':True,'B00_all_alternatives_preserved':True,
            'limits':['Source in-sample gradient concentration is not causal group influence or out-of-sample performance',
                      'Three fixed seeds are correlated perturbations, not independent samples or confidence intervals',
                      'No justified severity cap, row deletion, seed selection, recipe adoption or submission from this diagnostic alone']}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'source_tail':results,'target2025_seed_stability':[x for x in bycell if x['market']=='s2' and x['year']==2025]},ensure_ascii=True))


if __name__=='__main__':main()
