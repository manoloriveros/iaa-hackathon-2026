"""Diagnóstico y replay de precios temporales ya fijados; no ajusta modelos."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import sys
import warnings

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
P=R/'herramientas/mision017_fase2_tanda1_v2.py'
spec=importlib.util.spec_from_file_location('batch2',P);b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
import numpy as np
import pandas as pd
import lightgbm as lgb
import joblib
from threadpoolctl import threadpool_limits
OUT=b.OUT/'validation_v1'


def null_deviance(y):
    y=np.asarray(y,float)
    return float(8*(np.sqrt(y.sum()*len(y))-np.sqrt(y).sum()))


def validate():
    assert not OUT.exists(), 'Conservar diagnóstico existente; no repetir sin cambio.'
    plan=b.read(b.PLAN);report=b.read(b.OUT/'price_report.json')
    assert report['status']=='prices_scored_diagnostics_pending' and report['new_price_fits']==12
    assert b.read(b.OUT/'registration.json')['plan_sha256']==b.data.sha(b.PLAN)
    p=pd.read_parquet(b.OUT/'predictions_2024.parquet');OUT.mkdir()
    assert p.row_id.is_unique and p.group_id.notna().all()
    y=p.T0.to_numpy(float);null=null_deviance(y)
    assert abs(null-b.unit(y,np.full(len(y),y.mean())).sum())<1e-7
    names=['M1','M2','M3'];base=b.unit(y,p.M0.to_numpy(float));nulls=[]
    group_index,groups=pd.factorize(p.group_id,sort=True);n_groups=len(groups)
    ng=np.bincount(group_index);sy=np.bincount(group_index,weights=y);sqrt_y=np.bincount(group_index,weights=np.sqrt(y))
    dg=np.column_stack([np.bincount(group_index,weights=base-b.unit(y,p[name].to_numpy(float))) for name in names])
    rng=np.random.default_rng(plan['bootstrap']['seed']);draws=[]
    for start in range(0,2000,25):
        # Exact multinomial group bootstrap; one draw preserves all rows of each component.
        w=rng.multinomial(n_groups,np.full(n_groups,1/n_groups),size=min(25,2000-start))
        den=8*(np.sqrt((w@sy)*(w@ng))-w@sqrt_y)
        assert (den>0).all();draws.append((w@dg)/den[:,None])
    draws=np.vstack(draws)
    scores=report['scores'];checks={};segments=[];folds=[];stresses=[]
    for name in names:
        delta=base-b.unit(y,p[name].to_numpy(float))
        ci=np.quantile(draws[:,names.index(name)],[.025,.975]);sim=np.quantile(draws[:,names.index(name)],[.025/3,1-.025/3])
        cell_points=[];fold_points=[]
        for (line,nb),s in p.groupby(['line','x_new_business'],observed=True):
            ids=s.index.to_numpy();gain=float(delta[ids].sum()/null);cell_points.append(gain)
            segments.append({'model':name,'line':line,'new_business':int(nb),'rows':len(s),'positives':int(s.T0.gt(0).sum()),
                'delta_full_null':gain,'A_over_E':float(s.T0.sum()/s[name].sum()),'base_A_over_E':float(s.T0.sum()/s.M0.sum())})
        for k,s in p.groupby('fold',observed=True):
            gain=float(delta[s.index].sum()/null);fold_points.append(gain)
            folds.append({'model':name,'fold':int(k),'rows':len(s),'delta_full_null':gain,
                          'role':'segment of one temporal model, not an independently fitted fold'})
        gains=np.bincount(group_index,weights=delta)
        favorable=np.argsort(gains)[::-1][:31]
        after=float((gains.sum()-gains[favorable].sum())/null)
        stress_ok=True
        for label,response,e_col in [
            ('reserve075','T1_reserve075','e_cost_mix_0.75'),('reserve125','T1_reserve125','e_cost_mix_1.25'),
            ('tail005','T0','e_cost_mix_tail0.05'),('tail010','T0','e_cost_mix_tail0.1')]:
            yy=p[response].to_numpy(float);ratio=p[e_col].to_numpy(float)/p.e_cost.to_numpy(float)
            d0=b.unit(yy,p.M0.to_numpy(float)*ratio)
            d1=b.unit(yy,p[name].to_numpy(float)*ratio)
            gain=float((d0-d1).sum()/null_deviance(yy));stress_ok &= gain>=0
            stresses.append({'model':name,'scenario':label,'delta':gain,'rates_refitted':False,
                            'role':'fixed-rate observation/target sensitivity; not proof of ultimate adequacy'})
        gates={'point_delta_ge_002':scores[name]-scores['M0']>=.002,'paired_lower95_positive':ci[0]>0,
            'at_least_4_positive_group_fold_segments':sum(x>0 for x in fold_points)>=4,
            'no_line_business_contribution_below_minus001':min(cell_points)>=-.001,
            'after_31_favorable_groups_nonnegative':after>=0,'fixed_rate_stress_point_nonnegative':bool(stress_ok)}
        checks[name]={'delta':scores[name]-scores['M0'],'bootstrap95':ci.tolist(),'simultaneous95_3comparisons':sim.tolist(),
            'positive_fold_segments':sum(x>0 for x in fold_points),'min_cell_delta_full_null':min(cell_points),
            'after_remove_31_favorable_groups_delta':after,'gates':gates,'exploratory_pass':all(gates.values())}
        pd.DataFrame({'group_id':groups,'delta_deviance':gains}).to_parquet(OUT/f'group_influence_{name}.parquet',index=False)

    # Replay frozen real models, with fitting prohibited and protected held payload poisoned.
    replays=[]
    original_lgb_train=lgb.train;original_fit_glm=b.fit_glm
    def reject(*args,**kwargs): raise AssertionError('Fitting forbidden during replay')
    lgb.train=reject;b.fit_glm=reject
    try:
        with threadpool_limits(limits=2):
            for line in b.data.v.LINES:
                f=pd.read_parquet(b.data.OUT/f'emerging_{line}.parquet');f=f.loc[f.year.eq(2024)].copy()
                meta=b.read(b.OUT/f'{line}_metadata.json');source=lgb.Booster(model_file=str(b.OUT/f'source_{line}.txt'))
                small=lgb.Booster(model_file=str(b.OUT/f'M2_{line}.txt'))
                m1=joblib.load(b.OUT/f'M1_{line}.joblib');m3=joblib.load(b.OUT/f'M3_{line}.joblib')
                def predict(frame):
                    X,_=b.tree_frame(frame,meta['source_columns'],meta['source_categories'])
                    annual=source.predict(X,num_threads=2)*meta['source_level_k'];offset=annual*frame.e_cost.to_numpy(float)
                    Xa,_=b.tree_frame(frame,meta['adapter_columns'],meta['adapter_categories'])
                    return np.column_stack([offset,b.glm_predict(m1,frame,offset),
                        offset*np.exp(small.predict(Xa,raw_score=True,num_threads=2)),
                        b.glm_predict(m3,frame,frame.e_cost.to_numpy(float)*frame.written_premium.to_numpy(float))])
                expected=pd.read_parquet(b.OUT/f'predictions_2024_{line}.parquet').set_index('row_id').loc[f.row_id,['M0','M1','M2','M3']].to_numpy(float)
                a=predict(f);poison=f.copy()
                for c in ['T0','T0_cents','reserve','T1_reserve075','T1_reserve125']:poison[c]=1e20
                z=predict(poison)
                assert np.array_equal(a,expected) and np.array_equal(a,z)
                replays.append({'line':line,'rows':len(f),'bit_exact_saved_predictions':True,'protected_label_poison_invariant':True,'fit_calls':0})
    finally:
        lgb.train=original_lgb_train;b.fit_glm=original_fit_glm
    out={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scores':scores,'comparisons':checks,
        'replay':replays,'group_bootstrap_replicates':2000,'evaluation_rows':len(p),'groups':n_groups,
        'no_new_fit_calls':True,'not_formal_v1_confirmation':True,'2024_is_adaptive_development':True,
        'B00_preserved':True,'submissions':0,'goal_achieved':False,
        'limits':b.read(b.data.OUT/'report.json')['availability_limits']}
    b.dump(OUT/'report.json',out);pd.DataFrame(segments).to_csv(OUT/'segments.csv',index=False)
    pd.DataFrame(folds).to_csv(OUT/'fold_segments.csv',index=False);pd.DataFrame(stresses).to_csv(OUT/'sensitivities.csv',index=False)
    np.save(OUT/'bootstrap_deltas.npy',draws)
    print(json.dumps({'scores':scores,'comparisons':checks,'replay_pass':True,'new_fits':0},default=float))


if __name__=='__main__':
    validate()
