"""Adversos focales de selección tardía, entrada temporal y predicción congelada."""
from pathlib import Path
import importlib.util,sys,json
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('mechanism_fixtures',REPO/'src/semana2/sensibilidad_c0_reservas2023.py');m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
def main():
    run=Path(sys.argv[1]).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023');p=m.u.read(run/'plan_snapshot.json');claims=m.pq.read_table(run/'inputs_2023/claims_2023.parquet').to_pandas();checks=[]
    def check(n,v):checks.append({'name':n,'pass':bool(v)})
    def reject(n,f):
        try:f()
        except (ValueError,AssertionError):check(n,True)
        else:check(n,False)
    def forbidden(*a,**k):raise AssertionError('Ningún fit en adversos congelados')
    m.obs.fit_reporting=forbidden
    for cls in [m.u.TweedieRegressor,m.u.SimpleImputer,m.u.StandardScaler,m.u.OneHotEncoder,m.u.ColumnTransformer,m.u.Pipeline]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
    parent=ROOT/p['input_run']
    for fold in range(5):
        for line in ['motor','buildings','contents']:
            expected=m.choose_late_group(claims,fold,line);poison=claims.copy();heldout=poison.fold.eq(fold);poison.loc[heldout,'T0_cents']=10**16;poison.loc[heldout,'delay']=700
            check('Heldout huge costs do not change selector '+line+str(fold),m.choose_late_group(poison,fold,line)==expected)
            shuffled=claims.sample(frac=1.,random_state=20261024)
            check('Input row order irrelevant '+line+str(fold),m.choose_late_group(shuffled,fold,line)==expected)
    toy=m.pd.DataFrame({'line':['motor']*4,'fold':[1,1,1,0],'group_id':['a','b','c','heldout'],'delay':[366,366,365,700],'T0_cents':[100,100,10**8,10**10]})
    check('Strict365day boundary and deterministic tie',m.choose_late_group(toy,0,'motor')=='a')
    early=toy.copy();early['delay']=365;check('No eligible late costs identity branch',m.choose_late_group(early,0,'motor') is None)
    zero=toy.copy();zero['T0_cents']=0;check('No positive late costs identity branch',m.choose_late_group(zero,0,'motor') is None)
    for line in ['motor','buildings','contents']:
        frame=m.u.load_2023(parent/f'variant_inputs/{line}_fold0.parquet');dates=m.pq.read_table(parent/f'inputs_2023/raw_{line}.parquet',columns=['row_id','period_start','period_end']).to_pandas();no_late=claims.copy();no_late['delay']=365
        e,rec,models=m.late_link(frame,dates,no_late,0,line)
        check('No late branch invokes no curve fit '+line,m.np.array_equal(e,frame['e_cost_mix_1.0']) and rec['identity'] and rec['new_reporting_fits']==0 and models=={})
        for label,column,value in [('2024','year',2024),('test','is_test',True)]:
            bad=frame.head(2).copy();bad[column]=value;reject('Late-link rejects '+label+line,lambda bad=bad:m.late_link(bad,dates,claims,0,line))
        reject('Late-link rejects duplicate keys '+line,lambda:m.late_link(m.pd.concat([frame.head(2),frame.head(1)]),dates,claims,0,line))
        bundle=m.u.joblib.load(run/f'models/R125_W2-B14_{line}_fold0/bundle.joblib');valid=frame[frame.fold.eq(0)].head(20).copy();poison=valid.copy();poison['T0']=1e13;poison['reserve']=-1e13;poison['row_id']=['poison'+str(i) for i in range(len(poison))]
        check('No outcome/id enters price '+line,m.np.array_equal(m.v.predict(bundle,valid),m.v.predict(bundle,poison)))
    result={'author':'Codex','scope':'Changed selector/consumer adversaries only; fit blocked including report curves','passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'professional_independent_validation':False}
    m.u.dump(run/'fixture_checks.json',result);print(json.dumps(result));return bool(result['failed'])
if __name__=='__main__':raise SystemExit(main())
