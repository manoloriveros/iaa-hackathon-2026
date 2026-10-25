"""Reproduce solo el artefacto sintético generado en esta revisión, sin fit."""
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
import hashlib,json,sys,io
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
RUN=REPO/'privado/semana2/desarrollo2023/g4_flujo_sintetico_20261024_v1'
sys.path.insert(0,str(REPO/'src'));sys.path.insert(0,str(REPO/'herramientas'))
import numpy as np
import joblib
from threadpoolctl import threadpool_limits
from semana2 import flujo_g4_sintetico2023 as flow
from probar_flujo_g4_sintetico2023 import data_guard,BLOCKED

def main():
    out=RUN/'disk_replay_receipt.json';assert not out.exists(),'Replay already saved; no reason to repeat unchanged sources'
    planpath=REPO/'registro/semana2_g4_flujo_sintetico_plan_v2_reparacion.json'
    planbytes=planpath.read_bytes();plan=json.loads(planbytes.decode('utf-8'));planhash=hashlib.sha256(planbytes).hexdigest()
    for x in plan['frozen_sources']:assert hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest()==x['sha256']
    verification=json.loads((RUN/'verification.json').read_text(encoding='utf-8'));assert verification['success']
    manifest=json.loads((RUN/'synthetic_outer0_manifest.json').read_text(encoding='utf-8'))
    assert manifest['synthetic_only'] and manifest['fixture']==flow.FIXTURE
    raw=(RUN/'synthetic_outer0.joblib').read_bytes();assert hashlib.sha256(raw).hexdigest()==manifest['sha256']
    flow.reset_work();before=flow.WORK.copy()
    with threadpool_limits(limits=2),data_guard(),patch.object(flow,'fit_scope',side_effect=AssertionError('No fit in replay')),patch.object(flow,'fit_outer',side_effect=AssertionError('No fit in replay')),patch.object(flow,'fit_calibrator',side_effect=AssertionError('No calibration in replay')),patch.object(flow.c0,'fit_c0_2023',side_effect=AssertionError('No C0 fit in replay')),patch.object(flow.TweedieRegressor,'fit',side_effect=AssertionError('No GLM fit in replay')):
        bundle=joblib.load(io.BytesIO(raw));assert bundle['artifact_sha256']==manifest['artifact_sha256']
        assert bundle['base']['contract']['source_versions']['frozen_plan']==planhash
        p,_=flow.fixture();query=p[p.fold.eq(0)]
        prediction=flow.apply_outer(query,bundle)
        buildings=query[query.line.eq('buildings')].sort_values(flow.KEY)
        q=flow.predict_scope(buildings,bundle['base'],[0]);X=bundle['base']['transformer'].transform(buildings[flow.FEATURES])
        manual=np.exp(np.asarray(X@bundle['base']['model'].coef_).ravel()+bundle['base']['model'].intercept_)
        np.testing.assert_allclose(manual,q.rate,rtol=1e-10,atol=1e-10)
        observed=prediction[prediction.line.eq('buildings')].sort_values(flow.KEY)
        for mode in ['L','S']:
            c=bundle['calibrators'][mode]
            expected=q.C0*np.exp(c['a']+c['m']+c['b']*(np.log(manual)-c['m']))
            np.testing.assert_allclose(observed[mode],expected,rtol=1e-10,atol=1e-10)
    assert before==flow.WORK and not BLOCKED
    receipt={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'fixture':flow.FIXTURE,'source_model_sha256':manifest['sha256'],
        'synthetic_rows':len(prediction),'manual_rate_max_abs_difference':float(np.max(np.abs(manual-q.rate))),
        'prediction_sha256':flow.digest(prediction.to_dict('records')),'fit_calls':flow.WORK,
        'competition_rows_read':0,'unexpected_opens':len(BLOCKED),'success':True,
        'scope':'On-disk synthetic artifact loaded through verified bytes and replayed with all fit entrypoints blocked.'}
    out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'success':True,'synthetic_rows':len(prediction),'fit_calls':flow.WORK,'competition_rows':0},ensure_ascii=True))

if __name__=='__main__':main()
