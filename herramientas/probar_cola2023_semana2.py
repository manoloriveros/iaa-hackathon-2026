"""Adversos del álgebra de cola y del consumidor real sin nuevos ajustes."""
from pathlib import Path
from fractions import Fraction
import importlib.util,sys,copy,json
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('tail_fixtures',REPO/'src/semana2/sensibilidad_cola2023.py')
m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
def main():
    run=Path(sys.argv[1]).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023');p=m.u.read(run/'plan_amendment_snapshot.json');checks=[]
    def check(n,v):checks.append({'name':n,'pass':bool(v)})
    def reject(n,f):
        try:f()
        except (ValueError,AssertionError):check(n,True)
        else:check(n,False)
    def forbidden(*a,**k):raise AssertionError('Fit prohibido')
    for cls in [m.u.TweedieRegressor,m.u.SimpleImputer,m.u.StandardScaler,m.u.OneHotEncoder,m.u.ColumnTransformer,m.u.Pipeline]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
    check('No tail identity',m.factor_from_shares({'fire':1.})==1.)
    check('All tail closed form',abs(m.factor_from_shares({'bodily_injury':1.})-10/9)<1e-14)
    check('Permutation invariant',abs(m.factor_from_shares({'fire':.8,'bodily_injury':.2})-m.factor_from_shares({'bodily_injury':.2,'fire':.8}))<1e-14)
    ws=[Fraction(1,5),Fraction(4,5)];qs=[Fraction(3,5),Fraction(1)];t=[Fraction(1,10),Fraction(0)];z=sum(w/(1-a) for w,a in zip(ws,t));base=sum(w*q for w,q in zip(ws,qs))
    fixed=sum(w*(1-a)*q for w,a,q in zip(ws,t,qs));renorm=sum((w/(1-a)/z)*(1-a)*q for w,a,q in zip(ws,t,qs))
    check('Exact rational mixture identity',renorm==base/z and fixed!=renorm and abs(float(z)-m.factor_from_shares({'bodily_injury':.2,'fire':.8}))<1e-14)
    for name,shares in [('empty',{}),('negative',{'fire':1.1,'bodily_injury':-.1}),('notnormalized',{'fire':.5}),('nonfinite',{'fire':float('nan')})]:reject('Invalid shares '+name,lambda shares=shares:m.factor_from_shares(shares))
    parent=ROOT/p['input_run']
    for fold in range(5):
        for line in ['motor','buildings']:
            frame=m.u.load_2023(parent/f'variant_inputs/{line}_fold{fold}.parquet');valid=frame[frame.fold.eq(fold)].head(20).copy();bundle=m.u.joblib.load(run/f'models/T10R_W2-B14_{line}_fold{fold}/bundle.joblib');z=bundle['scale']
            rate=m.predict(bundle,valid);changed=copy.deepcopy(bundle['parent']);assert changed['estimator'].alpha==0;changed['estimator'].intercept_+=m.np.log(z)
            check('Equivalent native GLM intercept '+line+str(fold),m.np.allclose(rate,m.v.predict(changed,valid),rtol=1e-12))
            poison=valid.copy();poison['T0']=1e14;poison['group_id']='poison';poison['row_id']=['poison'+str(i) for i in range(len(poison))]
            check('Outcomes and ids cannot change price '+line+str(fold),m.np.array_equal(rate,m.predict(bundle,poison)))
            if line=='motor' and fold==0:
                for name,col,value in [('2024','year',2024),('test','is_test',True),('wrongfold','fold',1),('wrongline','line','contents')]:
                    bad=valid.copy();bad[col]=value;reject('Wrong scope '+name,lambda bad=bad:m.predict(bundle,bad))
                reject('Duplicate keys',lambda:m.predict(bundle,m.pd.concat([valid,valid.iloc[[0]]])))
                reject('Fit role contains heldout',lambda:m.scope(valid,0,True))
    result={'author':'Codex','scope':'Focal new tail-mechanism and consumer adversaries; zero fits','passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'professional_independent_validation':False}
    m.u.dump(run/'fixture_checks.json',result);print(json.dumps(result));return bool(result['failed'])
if __name__=='__main__':raise SystemExit(main())
