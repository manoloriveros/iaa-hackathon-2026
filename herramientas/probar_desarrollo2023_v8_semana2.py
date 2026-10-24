"""Adversos de B19, sin entrenamiento adicional; fallos nativos conservados."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,subprocess
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('dev8_guarded_consumer',REPO/'src/semana2/entrenar_desarrollo2023_v8.py');m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)

def main():
    run=Path(sys.argv[1]).resolve();p=m.u.read(run/'plan_snapshot.json');checks=[]
    def check(n,x):checks.append({'name':n,'pass':bool(x)})
    def reject(n,fn):
        try:fn()
        except ValueError:check(n,True)
        else:check(n,False)
    def forbidden(*a,**k):raise AssertionError('Fit adicional prohibido en adversos')
    for cls in [m.u.TweedieRegressor,m.u.SimpleImputer,m.u.StandardScaler,m.u.OneHotEncoder,m.u.ColumnTransformer,m.u.Pipeline]:
        cls.fit=forbidden
        if hasattr(cls,'fit_transform'):cls.fit_transform=forbidden
    for line in ['motor','buildings','contents']:
        frame=m.pq.read_table(run/f'inputs_2023/{line}_fold0.parquet').to_pandas();valid=frame[frame.fold.eq(0)].head(25).copy();fit=frame[frame.fold.ne(0)].head(25).copy();bundle=m.u.joblib.load(run/f'models/W2-B19_{line}_fold0/bundle.joblib')
        field='x_cover_type' if line=='motor' else 'x_accidental_damage_cover'
        with m.u.threadpool_limits(limits=2):original=m.predict(bundle,valid,line)
        for label,col,value in [('year','year',2024),('test','is_test',True),('cover_missing',field,None),('cover_unknown',field,'unknown' if line=='motor' else 2.),('zeroC0','e_cost_mix_1.0',0.),('negativeT0','T0',-1.)]:
            bad=valid.copy();bad[col]=value;reject('Prediction guard '+label+line,lambda bad=bad:m.predict(bundle,bad,line))
        reject('Heldout cannot fit '+line,lambda:m.fit_glm7(valid,0,p['recipe'],line))
        reject('Duplicate keys '+line,lambda:m.predict(bundle,m.pd.concat([valid,valid.head(1)],ignore_index=True),line))
        poison=valid.copy();poison['T0']=1e15;poison['row_id']=['poison'+str(j) for j in range(len(poison))];poison['written_premium']=-1e15;poison['reserve']=1e15
        with m.u.threadpool_limits(limits=2):rp=m.predict(bundle,poison,line);shuffled=m.predict(bundle,valid.iloc[::-1],line)
        check('TargetIDsreservepremium not predictors '+line,m.np.array_equal(original,rp))
        check('Row order only reorders prediction '+line,m.np.array_equal(original,shuffled[::-1]))
        check('Positive rates without structural zeros '+line,m.np.isfinite(original).all() and (original>0).all())
        if line!='motor':
            flagoff=valid.copy();flagoff[field]=0.
            with m.u.threadpool_limits(limits=2):zero_flag_rate=m.predict(bundle,flagoff,line)
            check('Optional coverfalse does not zero price '+line,(zero_flag_rate>0).all())
    # Run the actual consumer on poisoned frozen fixture copies. These must fail
    # before fit_started; no new price estimator is trained in these subprocesses.
    ad=run/'adversaries';ad.mkdir(exist_ok=False);failures=[];source=m.pq.read_table(run/'inputs_2023/motor_fold0.parquet').to_pandas()
    for label,reason in [('year','Solo se permite materializar desarrollo 2023'),('cover','Cobertura ausente'),('T0','T0/partición cambió T0'),('C0','C0 retenido cambió e_cost_mix_1.0')]:
        folder=ad/label;(folder/'variant_inputs').mkdir(parents=True);bad=source.copy()
        if label=='year':bad['year']=2024
        elif label=='cover':bad['x_cover_type']=None
        elif label=='T0':bad.loc[bad.index[0],'T0']+=1.
        else:bad.loc[bad.fold.eq(0),'e_cost_mix_1.0']*=.9
        f=folder/'variant_inputs/motor_fold0.parquet';bad.to_parquet(f,index=False)
        negative=dict(p,input_run=m.u.relative(folder),frozen_sources=[{'path':m.u.relative(f),'sha256':m.u.sha(f)}]);pp=folder/'plan.json';m.u.dump(pp,negative)
        before=set(run.parent.glob('dev8_*'));proc=subprocess.run([sys.executable,str(ROOT/p['code']),str(pp)],capture_output=True,text=True)
        created=sorted(set(run.parent.glob('dev8_*'))-before);failures.extend(m.u.relative(x) for x in created)
        (folder/'stderr.txt').write_text(proc.stderr,encoding='utf-8');(folder/'stdout.txt').write_text(proc.stdout,encoding='utf-8')
        check('Native consumer rejects '+label+' before fit',proc.returncode!=0 and reason in proc.stderr and len(created)==1 and 'fit_started' not in proc.stdout and not (created[0]/'report.json').exists())
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,
        'expected_failure_runs':failures,'new_fits':0,'scope':'Focused guard/predictor adversaries, fit blocked in process;4native negative commands fail before fit. No repeated training or bootstrap. Own review, not professional independent validation.'}
    m.u.dump(run/'fixture_checks.json',result);print(json.dumps({'passed':result['passed'],'failed':result['failed'],'expected_failure_runs':len(failures)}))
    if result['failed']:print(json.dumps([x for x in checks if not x['pass']]));return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
