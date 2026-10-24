"""Controles nuevos: rutas de reutilización, prefijo y guardas; cero ajustes."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,json,sys,tempfile
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
path=REPO/'src/semana2/entrenar_desarrollo2023_v2.py'
spec=importlib.util.spec_from_file_location('tested_dev2',path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
checks=[]
def check(name,result):checks.append({'name':name,'pass':bool(result)})
def rejects(name,fn):
    try:fn()
    except ValueError:check(name,True)
    else:check(name,False)
for line in m.LINES:
    check('B03 route '+line,m.route('W2-B03',line)==('new_fit' if line=='buildings' else 'reuse_W2-B01'))
    check('B04 route '+line,m.route('W2-B04',line)=='prefix_W2-B02')
    check('B05 route '+line,m.route('W2-B05',line)=='new_fit')
rejects('Unknown model rejected',lambda:m.route('unknown','motor'))
rejects('Unknown line rejected',lambda:m.route('W2-B03','unknown'))
parent=REPO/'privado/semana2/desarrollo2023/dev_20261023T173828Z_7efe46fc'
bundle=m.joblib.load(parent/'models/W2-B02_motor_fold0/bundle.joblib')
for value in [0,-1,301,1.5]:rejects('Invalid prefix '+str(value),lambda value=value:m.prefix_bundle(bundle,value))
prefix=m.prefix_bundle(bundle,25);check('Exactly 25 exported trees',prefix['booster'].num_trees()==25)
frame=m.v1.load_2023(parent/'inputs_2023/motor.parquet').iloc[:8].copy()
with m.v1.threadpool_limits(limits=2):
    expected=bundle['estimator'].predict(m.v1.prepare_lgb(frame,bundle['columns'],bundle['categories']),num_iteration=25)
    actual=m.predict(prefix,frame)
check('Saved prefix equals parent prefix',m.np.array_equal(expected,actual))
rejects('Prefix 2024 prediction rejected',lambda:m.predict(prefix,frame.assign(year=2024)))
rejects('Prefix test prediction rejected',lambda:m.predict(prefix,frame.assign(is_test=True)))
with tempfile.TemporaryDirectory(prefix='prefix_fixture_',dir=parent.parent) as tmp:
    artifact=Path(tmp)/'bundle.joblib';m.joblib.dump(prefix,artifact)
    with m.v1.threadpool_limits(limits=2):restored=m.predict(m.joblib.load(artifact),frame)
    check('Prefix serialization exact',m.np.array_equal(actual,restored))
check('Parent still has 300 trees',bundle['estimator'].booster_.num_trees()==300)
result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'source_sha256':m.v1.sha(path),'checks':checks,
        'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),
        'fit_calls':0,'real_model_scores_computed':0,'note':'Uses eight 2023 feature rows for native-prefix equivalence only, no outcome metric'}
with (REPO/'registro/semana2_desarrollo2023_pruebas_v2.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=True));assert result['failed']==0
