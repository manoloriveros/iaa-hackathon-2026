"""Métrica, sensibilidad a grupos y replay de CatBoost/mezclas sin ajustes nuevos."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
spec=importlib.util.spec_from_file_location('b3',R/'herramientas/mision017_fase2_tanda3_v3.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
import numpy as np
import pandas as pd
import catboost as cb
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits
OUT=b.OUT/'validation_v1'


def null(y):return float(8*(np.sqrt(np.sum(y)*len(y))-np.sqrt(y).sum()))


def evaluate(p,plan):
    y=p.T0.to_numpy(float);den=null(y);names=['Q1','Q2','Q3'];base=b.unit(y,p.N0.to_numpy(float))
    for name in ['N0',*names]:
        assert abs(b.unit(y,p[name].to_numpy(float)).mean()-mean_tweedie_deviance(y,p[name],power=1.5))<1e-7
    gi,groups=pd.factorize(p.group_id,sort=True);G=len(groups)
    counts=np.bincount(gi);total=np.bincount(gi,weights=y);sqrt_y=np.bincount(gi,weights=np.sqrt(y))
    d=np.column_stack([np.bincount(gi,weights=base-b.unit(y,p[n].to_numpy(float))) for n in names])
    rng=np.random.default_rng(plan['bootstrap']['seed']);draws=[]
    for _ in range(80):
        w=rng.multinomial(G,np.full(G,1/G),size=25);nn=8*(np.sqrt((w@total)*(w@counts))-w@sqrt_y)
        assert (nn>0).all();draws.append((w@d)/nn[:,None])
    draws=np.vstack(draws);comparisons={};segments=[];folds=[];years=[]
    for j,name in enumerate(names):
        rowdelta=base-b.unit(y,p[name].to_numpy(float));delta=float(rowdelta.sum()/den)
        ci=np.quantile(draws[:,j],[.025,.975]);sim=np.quantile(draws[:,j],[.025/3,1-.025/3])
        bycell=[];byfold=[];byyear=[]
        for (line,nb),s in p.groupby(['line','new_business'],observed=True):
            gain=float(rowdelta[s.index].sum()/den);bycell.append(gain)
            segments.append({'model':name,'line':line,'new_business':int(nb),'rows':len(s),'positive':int(s.T0.gt(0).sum()),
                'delta_full_null':gain,'A_over_E':float(s.T0.sum()/s[name].sum()),'base_A_over_E':float(s.T0.sum()/s.N0.sum())})
        for fold,s in p.groupby('fold',observed=True):
            gain=float(rowdelta[s.index].sum()/den);byfold.append(gain)
            folds.append({'model':name,'fold':int(fold),'delta_full_null':gain})
        for year,s in p.groupby('year',observed=True):
            gain=float(rowdelta[s.index].sum()/null(s.T0.to_numpy(float)));byyear.append(gain)
            years.append({'model':name,'year':int(year),'rows':len(s),'delta':gain})
        best=np.argsort(d[:,j])[::-1][:31];after=float((d[:,j].sum()-d[best,j].sum())/den)
        gates={'delta_ge_002':delta>=.002,'lower95_positive':bool(ci[0]>0),
            'positive_folds_ge4':sum(x>0 for x in byfold)>=4,'all_cells_ge_minus001':min(bycell)>=-.001,
            'post31_nonnegative':after>=0,'both_years_nonnegative':min(byyear)>=0}
        comparisons[name]={'delta':delta,'bootstrap95':ci.tolist(),'simultaneous95_3':sim.tolist(),
            'positive_folds':sum(x>0 for x in byfold),'min_cell_delta':min(bycell),'after_remove31_delta':after,
            'gates':gates,'exploratory_pass':all(gates.values())}
        pd.DataFrame({'group_id':groups,'delta_deviance':d[:,j]}).to_parquet(OUT/f'influence_{name}.parquet',index=False)
    np.save(OUT/'bootstrap_deltas.npy',draws)
    pd.DataFrame(segments).to_csv(OUT/'segments.csv',index=False);pd.DataFrame(folds).to_csv(OUT/'folds.csv',index=False)
    pd.DataFrame(years).to_csv(OUT/'years.csv',index=False)
    return comparisons


def validate():
    assert not OUT.exists();plan=b.read(b.PLAN);report=b.read(b.OUT/'price_report.json')
    assert b.read(b.OUT/'registration.json')['plan_sha256']==b.sha(b.PLAN)
    for path,h in plan['sources'].items():assert b.sha(ROOT/path)==h
    assert report['price_estimator_fits']==3 and report['target_reporting_refits']==0
    p=pd.read_parquet(b.OUT/'oof_2023_2024.parquet');assert p.row_id.is_unique and len(p)==109296
    OUT.mkdir();comparisons=evaluate(p,plan)
    oldfit=cb.CatBoostRegressor.fit;oldcurve=b.v.fit_reporting
    def reject(*a,**kw):raise AssertionError('No fitting during replay')
    cb.CatBoostRegressor.fit=reject;b.v.fit_reporting=reject
    replay=[];optimality=[]
    try:
        with threadpool_limits(limits=2):
            target=pd.read_parquet(b.BASE/'target_T0_and_stresses.parquet',filters=[('is_test','=',False)])
            parts=pd.read_parquet(b.BASE/'partitions.parquet',filters=[('is_test','=',False)])
            for line in b.source.LINES:
                meta=b.read(b.OUT/f'CB_{line}_metadata.json');assert b.sha(b.OUT/f'CB_{line}.cbm')==meta['model_sha256']
                model=cb.CatBoostRegressor();model.load_model(str(b.OUT/f'CB_{line}.cbm'))
                f=pd.read_parquet(b.PARENT/f'features_{line}.parquet')
                X=b.matrix(f,meta['columns'])
                annual=meta['initial_source_rate']*np.exp(model.predict(cb.Pool(X,cat_features=meta['catcols']),prediction_type='RawFormulaVal'))
                raw=pd.read_parquet(b.OUT/f'raw_CB_{line}.parquet').set_index('row_id').annual_CB.reindex(f.row_id).to_numpy(float)
                assert np.array_equal(annual,raw)
                f['annual_CB']=annual
                f=f.merge(pd.read_parquet(b.PARENT/f'raw_rates_{line}.parquet')[['row_id','annual_raw_T2b']],on='row_id',validate='one_to_one')
                f=f.merge(parts.loc[parts.line.eq(line),['row_id','fold']],on='row_id',validate='one_to_one')
                f=f.merge(target.loc[target.line.eq(line),['row_id','T0']],on='row_id',validate='one_to_one')
                f['exposure']=target.loc[target.line.eq(line)].set_index('row_id').exposure.reindex(f.row_id).to_numpy(float);f['is_test']=False
                for held in range(5):
                    levels=b.read(b.OUT/f'levels_{line}_fold{held}.json')
                    assert b.sha(ROOT/levels['C0_parent'])==levels['C0_parent_sha256']
                    a=b.read(ROOT/levels['C0_parent'])['artifact']['C0'];mask=f.fold.ne(held).to_numpy()
                    assert sorted(f.loc[mask,'row_id'])==levels['fit_row_ids']==a['fit_row_ids']
                    q=sum(w*b.v.average_completion(f,a['curves'][peril],'cost',1.) for peril,w in a['mixture'].items())
                    e=f.exposure.to_numpy(float)*q
                    t0=f.annual_raw_T2b.to_numpy(float)*levels['T2b_k'];r1=f.annual_CB.to_numpy(float)*levels['CB_k']
                    rates=[t0,r1,((1-.25)*t0+.25*r1)*levels['mixture_k']['Q2'],(.5*t0+.5*r1)*levels['mixture_k']['Q3']]
                    expected=p.set_index('row_id').loc[f.loc[~mask,'row_id'],['N0','Q1','Q2','Q3']].to_numpy(float)
                    observed=np.column_stack([rate[~mask]*e[~mask] for rate in rates])
                    observed[:,0]=(f.annual_raw_T2b.to_numpy(float)[~mask]*e[~mask])*levels['T2b_k']
                    assert np.array_equal(expected,observed)
                    y=f.loc[mask,'T0'].to_numpy(float)
                    for name,rate in zip(['Q1','Q2','Q3'],rates[1:]):
                        mu=rate[mask]*e[mask]
                        score=float(np.sum(y/np.sqrt(mu))-np.sum(np.sqrt(mu)))
                        relative=abs(score)/np.sum(np.sqrt(mu));assert relative<1e-12
                        optimality.append({'line':line,'fold':held,'model':name,'relative_level_score':relative})
                    poison=f.assign(T0=-1e30,reserve=-1e30,T0_cents=-1e30)
                    X2=b.matrix(poison,meta['columns'])
                    alt=meta['initial_source_rate']*np.exp(model.predict(cb.Pool(X2,cat_features=meta['catcols']),prediction_type='RawFormulaVal'))
                    assert np.array_equal(annual,alt)
                    replay.append({'line':line,'fold':held,'rows':int((~mask).sum()),'exact_predictions':True,
                        'held_label_poison_source_invariant':True,'exact_scope_membership':True,'new_fit_calls':0})
    finally:cb.CatBoostRegressor.fit=oldfit;b.v.fit_reporting=oldcurve
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scores':report['scores'],
        'comparisons':comparisons,'replays':replay,'level_optimality_checks':optimality,'metric_second_method':True,
        'new_fits':0,'source_author':'Codex','parent_reference_author':'Claude','source_years':[2021,2022,2023,2024],
        'emerging_C0_reused':True,'source_snapshot_scope':'start of2025,notprospective2024',
        '2024_is_adaptive_development':True,'new_submissions':0,'B00_preserved':True,'goal_achieved':False}
    b.dump(OUT/'report.json',result)
    print(json.dumps({'scores':report['scores'],'comparisons':comparisons,'replays':len(replay),'all_replays_pass':True}))


if __name__=='__main__':validate()
