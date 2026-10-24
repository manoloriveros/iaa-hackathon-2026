"""Adversos focales del consumidor nuevo; no vuelve a ajustar modelos."""
from pathlib import Path
import importlib.util,sys,json,copy
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('v7_fixture_consumer',REPO/'src/semana2/desarrollo2023_v7_componentes.py')
m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
def main():
    plan=m.u.read(m.PLAN);parent=ROOT/plan['parent_run'];run=Path(sys.argv[1]).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023');checks=[]
    def check(n,v):checks.append({'name':n,'pass':bool(v)})
    def reject(n,f):
        try:f()
        except (ValueError,AssertionError):check(n,True)
        else:check(n,False)
    def forbidden(*a,**k):raise AssertionError('Fixture intentó fit')
    for cls in [m.u.TweedieRegressor,m.u.SimpleImputer,m.u.StandardScaler,m.u.OneHotEncoder,m.u.ColumnTransformer,m.u.Pipeline]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
    for fold in range(5):
        p=m.u.load_2023(parent/f'variant_inputs/motor_fold{fold}.parquet');v=p[p.fold.eq(fold)];v=m.pd.concat([v[v.x_new_business.eq(0)].head(2),v[v.x_new_business.eq(1)].head(2)]).copy()
        native=m.u.joblib.load(parent/f'models/W2-B14_motor_fold{fold}/bundle.joblib');cr=m.u.read(parent/f'auxiliary/credibility_fold{fold}.json')['ramos']['motor'];cs,theta=m.factors(cr,native)
        # A change of numeric standardization basis must not change a raw-scale business coefficient.
        changed=copy.deepcopy(native);block=list(changed['transformer'].transformers_[0][2]);j=block.index('x_new_business');changed['estimator'].coef_[j]*=2;changed['transformer'].named_transformers_['numeric'].named_steps['scale'].scale_[j]*=2
        alt,theta2=m.factors(cr,changed);check('Raw coefficient invariant to scale representation fold'+str(fold),theta==theta2 and cs==alt)
        b=m.u.joblib.load(run/f'models/W2-B18_motor_fold{fold}/bundle.joblib');r=m.predict(b,v);base=m.u.predict_bundle(native,v)
        check('Renewals exact mixed rows fold'+str(fold),m.np.array_equal(r[v.x_new_business.eq(0)],base[v.x_new_business.eq(0)]))
        poisoned=v.copy();poisoned['T0']=1e12;poisoned['reserve']=-1e9;poisoned['group_id']='diagnostic_poison';poisoned['row_id']=['poison'+str(k) for k in range(len(v))]
        check('Outcomes/identifiers cannot change price fold'+str(fold),m.np.array_equal(r,m.predict(b,poisoned)))
        shifted=copy.deepcopy(cr);shifted['theta_s_em']=float('nan');reject('Nonfinite factor rejected fold'+str(fold),lambda:m.factors(shifted,native))
        # An auxiliary model whose frequency and severity already equal the prior has identity component factors.
        equal=copy.deepcopy(cr);equal.update(theta_f_dev=cr['theta_f_em'],theta_s_dev=cr['theta_s_em']);identity,_=m.factors(equal,native)
        check('Identity component correction fold'+str(fold),identity['W2-B16']==identity['W2-B17']==1.)
        if fold==0:
            for name,column,value in [('Closed2024','year',2024),('Test','is_test',True),('Wrongfold','fold',1),('Wrongline','line','contents'),('Invalidbusiness','x_new_business',2.)]:
                bad=v.copy();bad[column]=value;reject(name+' rejected',lambda bad=bad:m.predict(b,bad))
            duplicated=m.pd.concat([v,v.iloc[[0]]]);reject('Duplicate keys rejected',lambda:m.predict(b,duplicated))
    result={'author':'Codex','scope':'Focal consumer adversaries with frozen standard GLM; no new fits','passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'professional_independent_validation':False}
    m.u.dump(run/'fixture_checks.json',result);print(json.dumps(result));return bool(result['failed'])
if __name__=='__main__':raise SystemExit(main())
