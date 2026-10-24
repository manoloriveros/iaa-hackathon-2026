"""Adversos de mezcla y consumidor, sin nuevos modelos de precio."""
from pathlib import Path
import importlib.util,sys,json
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('mix_fixtures',REPO/'src/semana2/sensibilidad_mezcla_negocio2023.py');m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
def main():
    run=Path(sys.argv[1]).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023');p=m.u.read(run/'plan_snapshot.json');source=ROOT/p['input_run'];linkroot=ROOT/p['observation_run'];checks=[]
    def check(n,v):checks.append({'name':n,'pass':bool(v)})
    def reject(n,f):
        try:f()
        except (ValueError,AssertionError):check(n,True)
        else:check(n,False)
    def forbidden(*a,**k):raise AssertionError('Fit de precio prohibido en adversos')
    for cls in [m.u.TweedieRegressor,m.u.SimpleImputer,m.u.StandardScaler,m.u.OneHotEncoder,m.u.ColumnTransformer,m.u.Pipeline]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
    for name,values in [('empty',{}),('allzero',{'a':0.,'b':0.}),('negative',{'a':2.,'b':-1.}),('nonfinite',{'a':float('nan'),'b':1.})]:reject('Normalize rejects '+name,lambda values=values:m.normalize(values))
    a=m.normalize({'a':2.,'b':3.});b=m.normalize({'a':200.,'b':300.});check('Total scale is not extra price multiplier',a==b and sum(a.values())==1.)
    all_models=m.u.read(linkroot/'exclude_fold0/reporting_models.json')
    for line in ['motor','buildings','contents']:
        frame=m.u.load_2023(source/f'variant_inputs/{line}_fold0.parquet');claims=m.pq.read_table(run/f'inputs_2023/{line}_fold0_fitclaims.parquet').to_pandas();perils=sorted(key.split('|',1)[1] for key in all_models if key.startswith(line+'|'));models={peril:all_models[line+'|'+peril] for peril in perils}
        columns=m.KEY+['qN_'+x for x in perils]+['qC_1.0_'+x for x in perils];curves=m.pq.read_table(linkroot/f'exclude_fold0/observation_link_{line}.parquet',filters=[('year','=',2023),('is_test','=',False)],columns=columns).to_pandas();curves=frame[m.KEY].merge(curves,on=m.KEY,validate='one_to_one')
        base,detail=m.estimate_mixtures(frame,curves,claims,models,0,line)
        poisoned=frame.copy();poisoned.loc[poisoned.fold.eq(0),'T0']=1e15;other,otherdetail=m.estimate_mixtures(poisoned,curves,claims,models,0,line)
        check('Heldout outcome cannot change mixtures '+line,detail['business_shares']==otherdetail['business_shares'] and all(m.np.array_equal(base[k],other[k]) for k in base))
        scaled=claims.copy();scaled['severity_probability_weight']*=10.;changed,changedetail=m.estimate_mixtures(frame,curves,scaled,models,0,line)
        check('Gamma means invariant to weight scale '+line,all(m.np.allclose(base[k],changed[k],rtol=1e-12,atol=1e-12) for k in base))
        shuffled,shuffdetail=m.estimate_mixtures(frame,curves,claims.sample(frac=1.,random_state=20261024),models,0,line)
        check('Claim row order irrelevant '+line,all(m.np.allclose(base[k],shuffled[k],rtol=1e-12,atol=1e-12) for k in base))
        for name,column,value in [('year2024','year',2024),('test','is_test',True),('business','x_new_business',2.)]:
            bad=frame.copy();bad[column]=value;reject('Frame rejects '+name+line,lambda bad=bad:m.estimate_mixtures(bad,curves,claims,models,0,line))
        bad=claims.copy();bad.iloc[0,bad.columns.get_loc('fold')]=0;reject('Heldout claim rejected '+line,lambda bad=bad:m.estimate_mixtures(frame,curves,bad,models,0,line))
        bad=claims.copy();bad.iloc[0,bad.columns.get_loc('year')]=2024;reject('Non2023 claim rejected '+line,lambda bad=bad:m.estimate_mixtures(frame,curves,bad,models,0,line))
        reject('Duplicate claims rejected '+line,lambda:m.estimate_mixtures(frame,curves,m.pd.concat([claims,claims.head(1)]),models,0,line))
        reject('Misordered curves rejected '+line,lambda:m.estimate_mixtures(frame,curves.iloc[::-1],claims,models,0,line))
        bad=claims.copy();bad['severity_probability_weight']=0.;reject('Positive cell without weight mass rejected '+line,lambda bad=bad:m.estimate_mixtures(frame,curves,bad,models,0,line))
        valid=frame[frame.fold.eq(0)].head(20).copy();bundle=m.u.joblib.load(run/f'models/MIXFS_W2-B14_{line}_fold0/bundle.joblib');poison=valid.copy();poison['T0']=1e15;poison['row_id']=['poison'+str(i) for i in range(len(poison))]
        check('Outcome/id do not enter native price '+line,m.np.array_equal(m.v.predict(bundle,valid),m.v.predict(bundle,poison)))
    zero=0
    for path in (run/'mixtures').glob('*.json'):
        detail=m.u.read(path)
        for cell in detail['cell_estimates']:
            if cell['claims']==0:
                zero+=1;check('Observed zero cell has no fabricated severity '+path.stem+cell['peril']+str(cell['business']),cell['business_severity'] is None and all(detail['business_shares'][variant][str(cell['business'])][cell['peril']]==0. for variant in ['MIXF','MIXFS']))
    check('Zero cells recorded rather than hidden',zero==5)
    result={'author':'Codex','scope':'Focal mixtures/consumer adversaries; repeated arithmetic only to test invariance, no new price fits','passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'professional_independent_validation':False}
    m.u.dump(run/'fixture_checks.json',result);print(json.dumps(result));return bool(result['failed'])
if __name__=='__main__':raise SystemExit(main())
