"""Comprueba la escala Tweedie y las importaciones, sin ajustar estimadores."""
from pathlib import Path
from datetime import datetime, timezone
import importlib
import hashlib
import json
import sys

REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np

checks=[]
def check(name,ok):checks.append({'name':name,'pass':bool(ok)});assert ok,name

y=np.array([0.,.5,10.,100000.])
exposure=np.array([.0027,.5,1.,.3147])
rate=np.array([2.,10.,100.,30000.])
deviance=lambda a,b:4*(a/np.sqrt(b)+np.sqrt(b)-2*np.sqrt(a))
total=deviance(y,exposure*rate)
scaled=np.sqrt(exposure)*deviance(y/exposure,rate)
check('Unit Tweedie1.5 total loss equals sqrt exposure weighted rate loss',np.allclose(total,scaled,rtol=1e-12,atol=1e-10))
check('Zero target allowed with strictly positive predicted total',np.isfinite(total).all() and (exposure*rate>0).all())
modules={}
for name in ['numpy','pandas','pyarrow','scipy','sklearn','lightgbm','catboost']:
    module=importlib.import_module(name)
    modules[name]={'version':module.__version__,'path':module.__file__}
    check('Import '+name,True)
result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'executable':sys.executable,
    'modules':modules,'checks':checks,'passed':len(checks),'failed':0,'pricing_models_trained':0,
    'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'loss_contract':'Observed response / effective exposure, weight effective exposure**(2-power), power1.5 for unweighted total-unit deviance proxy; raw-T0 baseline uses nominal exposure; conditional branch uses scoped effective cost exposure.'}
path=REPO/'registro/semana2_contrato_entrenamiento_comprobacion.json'
with path.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'passed':len(checks),'modules':{k:v['version'] for k,v in modules.items()},'pricing_models_trained':0},ensure_ascii=True))
