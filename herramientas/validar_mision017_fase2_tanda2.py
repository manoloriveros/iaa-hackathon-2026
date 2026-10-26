"""Validación preinscrita y replay real sin reestimar curvas ni calibraciones."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
spec=importlib.util.spec_from_file_location('b2',R/'herramientas/mision017_fase2_tanda2.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance
OUT=b.OUT/'validation_v1'


def null(y):
    return float(8*(np.sqrt(np.sum(y)*len(y))-np.sqrt(y).sum()))


def validate():
    assert not OUT.exists()
    plan=b.read(b.PLAN);report=b.read(b.OUT/'price_report.json')
    assert b.read(b.OUT/'registration.json')['plan_sha256']==b.sha(b.PLAN)
    for p,h in plan['sources'].items():assert b.sha(ROOT/p)==h
    p=pd.read_parquet(b.OUT/'oof_2023_2024.parquet');OUT.mkdir()
    y=p.T0.to_numpy(float);den=null(y);base=b.unit(y,p.N0.to_numpy(float));names=['N1','N2','N3']
    for name in ['N0',*names]:
        assert abs(b.unit(y,p[name].to_numpy(float)).mean()-mean_tweedie_deviance(y,p[name],power=1.5))<1e-7
    gi,groups=pd.factorize(p.group_id,sort=True);G=len(groups)
    ng=np.bincount(gi);sy=np.bincount(gi,weights=y);sq=np.bincount(gi,weights=np.sqrt(y))
    dg=np.column_stack([np.bincount(gi,weights=base-b.unit(y,p[n].to_numpy(float))) for n in names])
    rng=np.random.default_rng(plan['bootstrap']['seed']);samples=[]
    for start in range(0,2000,25):
        w=rng.multinomial(G,np.full(G,1/G),size=25)
        d=8*(np.sqrt((w@sy)*(w@ng))-w@sq);assert (d>0).all();samples.append((w@dg)/d[:,None])
    samples=np.vstack(samples);comparisons={};segments=[];folds=[];years=[]
    for i,name in enumerate(names):
        diff=base-b.unit(y,p[name].to_numpy(float));point=float(diff.sum()/den)
        ci=np.quantile(samples[:,i],[.025,.975]);sim=np.quantile(samples[:,i],[.025/3,1-.025/3])
        cell=[];byfold=[];byyear=[]
        for (line,nb),s in p.groupby(['line','new_business'],observed=True):
            gain=float(diff[s.index].sum()/den);cell.append(gain)
            segments.append({'model':name,'line':line,'new_business':int(nb),'rows':len(s),'positive':int(s.T0.gt(0).sum()),
                'delta_full_null':gain,'A_over_E':float(s.T0.sum()/s[name].sum()),'base_A_over_E':float(s.T0.sum()/s.N0.sum())})
        for k,s in p.groupby('fold',observed=True):
            gain=float(diff[s.index].sum()/den);byfold.append(gain);folds.append({'model':name,'fold':int(k),'delta_full_null':gain})
        for year,s in p.groupby('year',observed=True):
            gain=float(diff[s.index].sum()/null(s.T0.to_numpy(float)));byyear.append(gain)
            years.append({'model':name,'year':int(year),'rows':len(s),'delta':gain})
        favorable=np.argsort(dg[:,i])[::-1][:31]
        after=float((dg[:,i].sum()-dg[favorable,i].sum())/den)
        gates={'delta_ge_002':bool(point>=.002),'lower95_positive':bool(ci[0]>0),
            'positive_folds_ge4':bool(sum(x>0 for x in byfold)>=4),'all_cells_ge_minus001':bool(min(cell)>=-.001),
            'post31_nonnegative':bool(after>=0),'both_years_nonnegative':bool(min(byyear)>=0)}
        comparisons[name]={'delta':point,'bootstrap95':ci.tolist(),'simultaneous95_3':sim.tolist(),
            'positive_folds':sum(x>0 for x in byfold),'after_remove31_delta':after,'min_cell_delta':min(cell),
            'gates':gates,'exploratory_pass':all(gates.values())}
    # Consume saved artifacts while any producer call is blocked.
    original=b.v.fit_reporting
    b.v.fit_reporting=lambda *a,**k: (_ for _ in ()).throw(AssertionError('No fit during replay'))
    replays=[];memberships=[]
    try:
        parts=pd.read_parquet(b.BASE/'partitions.parquet',filters=[('is_test','=',False)])
        target=pd.read_parquet(b.BASE/'target_T0_and_stresses.parquet',filters=[('is_test','=',False)])
        claims=pd.read_parquet(b.BASE/'claim_assignment_audit.parquet',columns=['claim_id','row_id','included_in_T0','line'])
        for line in b.v.LINES:
            f=pd.read_parquet(b.PARENT/f'features_{line}.parquet')
            raw=pd.read_parquet(b.PARENT/f'raw_rates_{line}.parquet')
            f=f.merge(raw[['row_id','annual_raw_T2b']],on='row_id',validate='one_to_one')
            f=f.merge(parts.loc[parts.line.eq(line),['row_id','fold']],on='row_id',validate='one_to_one')
            f['exposure']=target.loc[target.line.eq(line)].set_index('row_id').exposure.reindex(f.row_id).to_numpy(float)
            f['is_test']=False
            for held in range(5):
                row=b.read(b.OUT/f'learning_{line}_fold{held}.json');a=row['artifact']
                assert b.digest(a)==row['training_signature']
                keys=set(f.loc[f.fold.ne(held),'row_id']);assert sorted(keys)==a['C0']['fit_row_ids']
                claimids=claims.loc[claims.row_id.isin(keys)&claims.included_in_T0,'claim_id'].sort_values().tolist()
                assert claimids==a['C0']['fit_claim_ids']
                z=f.loc[f.fold.eq(held)].copy()
                def replay(frame):
                    q=sum(weight*b.v.average_completion(frame,a['C0']['curves'][peril],'cost',1.) for peril,weight in a['C0']['mixture'].items())
                    e=frame.exposure.to_numpy(float)*q;m=frame.annual_raw_T2b.to_numpy(float)*e
                    shaped=m.copy()
                    for artifact in a['shape']:shaped=b.shape_apply(frame,shaped,artifact)
                    nb=frame.new_business.to_numpy(dtype=int)
                    return np.column_stack([e*a['B00'],m*a['k'],shaped*a['kshape'],
                        m*np.array([a['cell'][str(n)] for n in nb]),shaped*np.array([a['cellshape'][str(n)] for n in nb])])
                result=replay(z);expected=p.set_index('row_id').loc[z.row_id,['B00_TEMP_CV2','N0','N1','N2','N3']].to_numpy(float)
                assert np.array_equal(result,expected)
                poison=z.assign(T0=1e30,reserve=-1e30,T0_cents=-1e30)
                assert np.array_equal(result,replay(poison))
                memberships.append({'line':line,'fold':held,'fit_rows':len(keys),'fit_claims':len(claimids),'exact_exclusion':True})
                replays.append({'line':line,'fold':held,'rows':len(z),'bit_exact':True,'protected_cost_poison_invariant':True,'fit_calls':0})
    finally:b.v.fit_reporting=original
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'scores':report['scores'],
        'comparisons':comparisons,'replays':replays,'memberships':memberships,'metric_second_method':True,
        'new_fits':0,'new_submissions':0,'2024_is_adaptive_development':True,'source_2024_available_for_2025_scope':True,
        'not_formal_promotion':True,'goal_achieved':False,'B00_preserved':True}
    b.dump(OUT/'report.json',result);np.save(OUT/'bootstrap_deltas.npy',samples)
    pd.DataFrame(segments).to_csv(OUT/'segments.csv',index=False);pd.DataFrame(folds).to_csv(OUT/'folds.csv',index=False)
    pd.DataFrame(years).to_csv(OUT/'years.csv',index=False)
    print(json.dumps({'scores':report['scores'],'comparisons':comparisons,'replays':len(replays),'all_replays_pass':True}))


if __name__=='__main__':validate()
