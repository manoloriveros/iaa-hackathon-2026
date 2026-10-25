"""Ejercita el flujo nuevo en memoria; bloquea datos/estimadores externos."""
from pathlib import Path
from datetime import datetime,timezone
from contextlib import contextmanager,ExitStack
from itertools import permutations
from copy import deepcopy
from unittest.mock import patch
import builtins,io,json,hashlib,os,sys,socket,time,unittest
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='2'
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
sys.path.insert(0,str(REPO/'src'))
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import scipy,sklearn,joblib
import pyarrow.parquet as pq
from scipy.optimize import minimize
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits
from semana2 import flujo_g4_sintetico2023 as flow

RUN=REPO/'privado/semana2/desarrollo2023/g4_flujo_sintetico_20261024_v1'
PLAN=REPO/'registro/semana2_g4_flujo_sintetico_plan_v2_reparacion.json'
SOURCES={};BASE={};CACHE={};DETAIL={};BLOCKED=[];EXPECTED_GUARD_PROBES=0

def serialized(obj):
    b=io.BytesIO();joblib.dump(obj,b,compress=0);return b.getvalue()

def poison(periods,claims,folds):
    p=periods.copy();c=claims.copy();pm=p.fold.isin(folds)&p.line.eq('buildings');cm=c.fold.isin(folds)
    for name in [*flow.NUM,*flow.CAT,'exposure','period_start','period_end']:
        p[name]=p[name].astype(object);p.loc[pm,name]='PROTECTED_PAYLOAD_MUST_NOT_BE_INTERPRETED'
    for name in ['T0_cents','peril','loss_date','report_date']:
        c[name]=c[name].astype(object);c.loc[cm,name]='PROTECTED_PAYLOAD_MUST_NOT_BE_INTERPRETED'
    return p,c

@contextmanager
def data_guard():
    original_open=builtins.open;original_io=io.open;original_os=os.open;original_load=joblib.load
    def checked(op):
        def wrapped(path,*args,**kwargs):
            if isinstance(path,(str,bytes,os.PathLike)):
                s=os.fsdecode(path).replace('\\','/').lower();suffix=Path(s).suffix
                workspace=s.startswith(str(ROOT).replace('\\','/').lower()+'/')
                if suffix in ['.csv','.parquet','.arrow','.feather','.pkl','.pickle','.joblib','.npy','.npz','.xlsx','.zip'] or (workspace and suffix not in ['.py','.pyc','.pyd','.dll']):
                    BLOCKED.append({'operation':'file_open','suffix':suffix});raise PermissionError('Synthetic run: external data/model I/O blocked')
            return op(path,*args,**kwargs)
        return wrapped
    def deny(*args,**kwargs):
        BLOCKED.append({'operation':'data_reader'});raise PermissionError('Synthetic run: reader blocked')
    def safe_load(value,*args,**kwargs):
        if not isinstance(value,io.BytesIO):return deny()
        return original_load(value,*args,**kwargs)
    def no_network(*args,**kwargs):
        BLOCKED.append({'operation':'network'});raise PermissionError('Synthetic run: network blocked')
    with ExitStack() as stack:
        stack.enter_context(patch('builtins.open',checked(original_open)))
        stack.enter_context(patch('io.open',checked(original_io)))
        stack.enter_context(patch('os.open',checked(original_os)))
        for name in ['read_csv','read_parquet','read_pickle','read_feather']:stack.enter_context(patch.object(pd,name,deny))
        stack.enter_context(patch.object(pq,'read_table',deny));stack.enter_context(patch.object(pq,'ParquetFile',deny))
        stack.enter_context(patch.object(joblib,'load',safe_load))
        stack.enter_context(patch.object(socket.socket,'connect',no_network))
        yield

class FullSyntheticFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p,cls.c=flow.fixture()
        for outer in range(5):BASE[outer]=flow.fit_outer(cls.p,cls.c,outer,SOURCES,CACHE)
        DETAIL['baseline_unique_scopes']=len(CACHE)
        DETAIL['baseline_digests']={str(k):v['artifact_sha256'] for k,v in BASE.items()}
        DETAIL['fixture']={'periods':len(cls.p),'claims':len(cls.c),'building_periods':int(cls.p.line.eq('buildings').sum()),'seed':20261024}

    def test_01_nested_membership_and_cache(self):
        self.assertEqual(len(CACHE),15)
        for outer,obj in BASE.items():
            self.assertEqual(obj['base']['contract']['excluded_folds'],[outer])
            for inner,ancestor in obj['inner'].items():
                omitted=sorted([outer,int(inner)])
                self.assertEqual(ancestor['contract']['excluded_folds'],omitted)
                keys={tuple(x[k] for k in flow.KEY) for x in ancestor['contract']['training_keys']}
                expected=self.p[self.p.line.eq('buildings')&~self.p.fold.isin(omitted)]
                self.assertEqual(keys,set(map(tuple,expected[flow.KEY].itertuples(index=False,name=None))))
                self.assertTrue(all(x['fold'] not in omitted for x in ancestor['C0']['weighted_claims']))
            self.assertTrue(all(x['row_id'] not in set(self.p[self.p.fold.eq(outer)].row_id) for x in obj['calibrators']['S']['training_keys']))
        DETAIL['unique_inner_scopes']=10;DETAIL['ordered_inner_uses']=20

    def test_02_outer_poison_all_learning(self):
        digests=[];byte_equal=[]
        for outer,clean in BASE.items():
            p,c=poison(self.p,self.c,[outer]);dirty=flow.fit_outer(p,c,outer,SOURCES,{})
            self.assertEqual(clean['artifact_sha256'],dirty['artifact_sha256'])
            self.assertEqual(flow.canonical(flow.live_outer_state(clean)),flow.canonical(flow.live_outer_state(dirty)))
            pd.testing.assert_frame_equal(flow.apply_outer(self.p[self.p.fold.eq(outer)],clean),flow.apply_outer(self.p[self.p.fold.eq(outer)],dirty),check_exact=True)
            same=serialized(clean)==serialized(dirty);self.assertTrue(same)
            digests.append(clean['artifact_sha256']);byte_equal.append(same)
        DETAIL['outer_poison_cases']=5;DETAIL['whole_object_serialization_equal']=byte_equal

    def test_03_twenty_inner_exclusions(self):
        for outer,inner in permutations(range(5),2):
            clean=BASE[outer]['inner'][str(inner)]
            p,c=poison(self.p,self.c,[outer,inner]);dirty=flow.fit_scope(p,c,[outer,inner],SOURCES)
            self.assertEqual(clean['artifact_sha256'],dirty['artifact_sha256'])
            self.assertEqual(flow.canonical(flow.live_state(clean)),flow.canonical(flow.live_state(dirty)))
            self.assertEqual(serialized(clean),serialized(dirty))
            query=self.p[self.p.line.eq('buildings')&self.p.fold.eq(inner)]
            pd.testing.assert_frame_equal(flow.predict_scope(query,clean,[outer,inner]),flow.predict_scope(query,dirty,[outer,inner]),check_exact=True)
        DETAIL['ordered_inner_poison_cases']=20

    def test_04_training_positive_controls(self):
        clean=BASE[4];c=self.c.copy();i=c.index[c.fold.eq(0)][0];c.loc[i,'T0_cents']*=7
        changed=flow.fit_outer(self.p,c,4,SOURCES,{})
        self.assertNotEqual(clean['base']['C0']['artifact_sha256'],changed['base']['C0']['artifact_sha256'])
        self.assertFalse(np.array_equal(clean['base']['model'].coef_,changed['base']['model'].coef_))
        self.assertNotEqual(clean['calibrators'],changed['calibrators'])
        p=self.p.copy();mask=p.line.eq('buildings')&p.fold.eq(0)
        p.loc[mask,'x_log_sum_insured']=p.loc[mask,'x_log_sum_insured']+5.
        changed=flow.fit_outer(p,self.c,4,SOURCES,{})
        self.assertNotEqual(flow.canonical(flow.preprocessor_state(clean['base']['transformer'])),flow.canonical(flow.preprocessor_state(changed['base']['transformer'])))
        self.assertFalse(np.array_equal(clean['base']['model'].coef_,changed['base']['model'].coef_))
        DETAIL['training_positive_controls']=2

    def test_05_reference_math_and_replay(self):
        b=BASE[0];q=self.p[self.p.line.eq('buildings')&self.p.fold.eq(0)].sort_values(flow.KEY)
        prediction=flow.predict_scope(q,b['base'],[0]);X=b['base']['transformer'].transform(q[flow.FEATURES])
        manual=np.exp(np.asarray(X@b['base']['model'].coef_).ravel()+b['base']['model'].intercept_)
        np.testing.assert_allclose(manual,prediction.rate,rtol=1e-10,atol=1e-10)
        restored=joblib.load(io.BytesIO(serialized(b)))
        before=flow.WORK.copy()
        with patch.object(flow,'fit_scope',side_effect=AssertionError('Replay called fit')):
            pd.testing.assert_frame_equal(flow.apply_outer(self.p[self.p.fold.eq(0)],b),flow.apply_outer(self.p[self.p.fold.eq(0)],restored),check_exact=True)
        self.assertEqual(before,flow.WORK)
        y=np.array([0.,1.,7.,23.]);e=np.array([.2,.5,.9,1.]);r=np.array([2.,4.,8.,12.]);mu=e*r
        own=float(flow.deviance(y,mu).sum());api=mean_tweedie_deviance(y,mu,power=1.5)*len(y)
        np.testing.assert_allclose(own,api,rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(own,np.sum(np.sqrt(e)*flow.deviance(y/e,r)),rtol=1e-12,atol=1e-12)
        DETAIL['replay_without_fit']=True;DETAIL['manual_rate_max_abs_error']=float(np.max(np.abs(manual-prediction.rate)))

    def test_06_calibration_profile_and_joint_reference(self):
        r=np.array([1.,2.,4.,8.,16.]);e=np.array([.2,.4,.6,.8,1.]);m=float(np.sum(e*np.log(r))/e.sum())
        errors=[]
        for expected in [0.,.4,1.]:
            y=e*np.exp(.2+m+expected*(np.log(r)-m))
            f=pd.DataFrame({'market':'emerging','line':'buildings','row_id':['SYN-G4-CAL-'+str(j) for j in range(5)],'T0':y,'C0':e,'rate':r})
            cal=flow.fit_calibrator(f,'S')
            self.assertAlmostEqual(cal['b'],expected,delta=1e-5)
            self.assertAlmostEqual(cal['a'],.2,delta=1e-5)
            def joint(v):
                mu=e*np.exp(v[0]+m+v[1]*(np.log(r)-m));g=np.sqrt(mu)-y/np.sqrt(mu)
                return float(flow.deviance(y,mu).sum()),2*np.array([g.sum(),g@(np.log(r)-m)])
            ref=minimize(joint,[0.,.5],jac=True,method='L-BFGS-B',bounds=[(None,None),(0.,1.)],options={'maxiter':500,'ftol':1e-14,'gtol':1e-9})
            self.assertTrue(ref.success);self.assertLessEqual(abs(ref.fun-cal['loss']),1e-8)
            errors.append(abs(ref.fun-cal['loss']))
        DETAIL['profile_joint_max_loss_difference']=max(errors);DETAIL['calibration_boundary_cases']=[0.,1.]
        tied=f.copy();tied['rate']=1.
        with self.assertRaises(ValueError):flow.fit_calibrator(tied,'S')
        zero=f.copy();zero['T0']=0.
        with self.assertRaises(ValueError):flow.fit_calibrator(zero,'S')

    def test_07_scope_and_corruption_adversaries(self):
        query=self.p[self.p.line.eq('buildings')&self.p.fold.eq(0)]
        with self.assertRaises(ValueError):flow.predict_scope(query,BASE[0]['base'],[0,1])
        corrupt=deepcopy(BASE[0]);corrupt['calibrators']['S']['a']+=1.
        with self.assertRaises(ValueError):flow.apply_outer(self.p[self.p.fold.eq(0)],corrupt)
        corrupt=deepcopy(BASE[0]['base']);corrupt['model'].coef_[0]+=1.
        with self.assertRaises(ValueError):flow.predict_scope(query,corrupt,[0])
        for field,value in [('year',2024),('is_test',True),('fixture_id','not_synthetic')]:
            p=self.p.copy();p.loc[0,field]=value
            with self.assertRaises(ValueError):flow.fit_scope(p,self.c,[0,1],SOURCES)
        p=pd.concat([self.p,self.p.iloc[[0]]],ignore_index=True)
        with self.assertRaises(ValueError):flow.fit_scope(p,self.c,[0,1],SOURCES)
        p=self.p.copy();p.loc[p.fold.eq(1),'group_id']=self.p.iloc[0].group_id
        with self.assertRaises(ValueError):flow.fit_scope(p,self.c,[0,1],SOURCES)
        DETAIL['scope_and_corruption_adversaries']=8

    def test_08_order_missing_and_passthrough(self):
        reordered=flow.fit_scope(self.p.iloc[::-1],self.c.iloc[::-1],[0,1],SOURCES)
        self.assertEqual(reordered['artifact_sha256'],BASE[0]['inner']['1']['artifact_sha256'])
        p=self.p.copy();p['x_property_age']=np.nan
        obj=flow.fit_scope(p,self.c,[0,1],SOURCES)
        self.assertTrue(np.isfinite(obj['model'].coef_).all())
        for outer,b in BASE.items():
            pred=flow.apply_outer(self.p[self.p.fold.eq(outer)],b)
            other=self.p[self.p.fold.eq(outer)&~self.p.line.eq('buildings')].sort_values(flow.KEY)
            actual=pred[pred.line.ne('buildings')].sort_values(flow.KEY)
            for mode in ['raw','L','S']:np.testing.assert_array_equal(actual[mode],other.synthetic_base_prediction)
        DETAIL['passthrough_motor_contents_exact']=True

    def test_09_ingress_guard(self):
        global EXPECTED_GUARD_PROBES
        with self.assertRaises(PermissionError):pd.read_parquet(RUN/'FAKE_DO_NOT_OPEN.parquet')
        EXPECTED_GUARD_PROBES+=1

def main():
    global SOURCES
    plan=json.loads(PLAN.read_text(encoding='utf-8'))
    forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes()
    assert forum.count(('<!-- aporte:'+plan['forum_prior']+' -->').encode())==1
    for item in plan['frozen_sources']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    SOURCES={'synthetic_generator':hashlib.sha256((REPO/'src/semana2/flujo_g4_sintetico2023.py').read_bytes()).hexdigest(),
             'frozen_plan':hashlib.sha256(PLAN.read_bytes()).hexdigest()}
    flow.reset_work();output=io.StringIO();start=time.monotonic()
    with threadpool_limits(limits=2),data_guard():
        result=unittest.TextTestRunner(stream=output,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(FullSyntheticFlow))
    elapsed=time.monotonic()-start
    unexpected=len(BLOCKED)-EXPECTED_GUARD_PROBES
    success=result.wasSuccessful() and unexpected==0 and elapsed<=600
    attempt=1
    while (RUN/f'attempt{attempt}_verification.json').exists():attempt+=1
    receipt={'id':plan['id'],'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'attempt':attempt,
        'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'success':success,
        'elapsed_seconds':elapsed,'synthetic_work':flow.WORK.copy(),'details':DETAIL,
        'blocked_opens':BLOCKED,'expected_guard_probes':EXPECTED_GUARD_PROBES,'unexpected_data_or_network_attempts':unexpected,
        'competition_rows_read':0,'competition_C0_fits':0,'competition_pricing_fits':0,'competition_predictions':0,
        'competition_scores':0,'old_diagnostics_repeated':False,'G1_G2_resolved':False,
        'environment':{'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__,'joblib':joblib.__version__},
        'scope':'Full newly integrated software flow, synthetic only; no real-data eligibility or actuarial validity claim.'}
    RUN.mkdir(parents=True,exist_ok=True)
    (RUN/f'attempt{attempt}_verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (RUN/f'attempt{attempt}_test_output.txt').write_text(output.getvalue(),encoding='utf-8')
    folder=RUN/f'attempt{attempt}_sources';folder.mkdir()
    for item in plan['frozen_sources']:
        p=ROOT/item['path'];(folder/p.name).write_bytes(p.read_bytes())
    if success:
        (RUN/'verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        b=serialized(BASE[0]);(RUN/'synthetic_outer0.joblib').write_bytes(b)
        (RUN/'synthetic_outer0_manifest.json').write_text(json.dumps({'fixture':flow.FIXTURE,'sha256':hashlib.sha256(b).hexdigest(),'artifact_sha256':BASE[0]['artifact_sha256'],'synthetic_only':True},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'attempt':attempt,'success':success,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'work':flow.WORK,'output':str(RUN/f'attempt{attempt}_test_output.txt')},ensure_ascii=True))
    return 0 if success else 1

if __name__=='__main__':raise SystemExit(main())
